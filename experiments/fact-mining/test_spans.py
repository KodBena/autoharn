#!/usr/bin/env python
"""Unit proofs for the SSOT tracer (spans.py) — everything provable WITHOUT the
3-process host pipeline:

  * span() is a near-zero-cost no-op when the tracer is DISABLED (default);
  * inject()/extract() round-trip the (run_id, trace_id, span_id) context through a
    plain dict, and a receiver parents its spans under the injected remote span;
  * the buffer BATCH-flushes immutable readings to the real `trace` schema, with the
    parent/child links and a monotonic dur_ms intact (skipped if the DB is unreachable).

The host run is what confirms the END-TO-END cross-process stitch (three live
processes, two ZMQ wires); these prove the mechanism in isolation.
"""

from __future__ import annotations

import os

import pytest

from spans import _TRACE_KEY, DEFAULT_DSN, Tracer, get_tracer

DSN = os.environ.get("HARNESS_DSN", DEFAULT_DSN)


def _db_up() -> bool:
    try:
        import psycopg
        with psycopg.connect(DSN, connect_timeout=3) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


# ============================================================ disabled = no-op
def test_span_is_noop_when_disabled():
    """A fresh tracer is OFF: span() yields the shared nullcontext singleton, buffers
    nothing, and writing under it cannot raise."""
    t = Tracer()
    assert t.enabled is False
    from spans import _NULL
    assert t.span("x") is _NULL, "disabled span() returns the shared nullcontext singleton"
    with t.span("anything", k=1):
        with t.span("nested"):
            pass
    assert t._buffer == [], "disabled span() must buffer nothing"
    # the SAME object is returned every time (no per-call allocation)
    assert t.span("a") is t.span("b")


def test_inject_is_noop_when_disabled():
    t = Tracer()
    meta = {"op": "decode"}
    assert t.inject(meta) is meta
    assert _TRACE_KEY not in meta, "a disabled tracer must not stamp the wire"


# ============================================================ enabled buffering
def test_enabled_span_buffers_a_reading_with_monotonic_duration():
    t = Tracer()
    t.configure(process="unit")
    t.enable(run_id=1, trace_id="tid")
    with t.span("outer", a=1):
        with t.span("inner"):
            pass
    assert len(t._buffer) == 2
    inner, outer = t._buffer  # inner exits first
    assert inner.name == "inner" and outer.name == "outer"
    assert inner.parent_span_id == outer.span_id, "nesting parents inner under outer"
    assert outer.parent_span_id is None, "outer is the root (no remote parent)"
    assert outer.attrs == {"a": 1}
    assert inner.dur_ms >= 0.0 and outer.dur_ms >= inner.dur_ms
    assert outer.t_end >= outer.t_start  # wall pair coherent within one process


# ============================================================ inject/extract round-trip
def test_inject_extract_roundtrips_and_parents_remote():
    sender = Tracer(); sender.configure(process="client")
    sender.enable(run_id=42, trace_id="trace-xyz")
    meta: dict = {"op": "parse", "texts": ["hi"]}
    with sender.span("client.zmq_wait.nlp_server"):
        sender.inject(meta)
        injected_span = meta[_TRACE_KEY]["span_id"]
    # the wire carries exactly the context
    ctx = meta[_TRACE_KEY]
    assert ctx["run_id"] == 42 and ctx["trace_id"] == "trace-xyz"
    assert injected_span is not None

    # a fresh receiver extracts -> enabled, same run/trace, remote parent adopted
    receiver = Tracer(); receiver.configure(process="nlp_server")
    assert receiver.enabled is False
    out = receiver.extract(meta)
    assert out == ctx
    assert receiver.enabled is True
    assert receiver.run_id == 42 and receiver.trace_id == "trace-xyz"
    with receiver.span("nlp_server.handle"):
        pass
    handle = receiver._buffer[0]
    assert handle.parent_span_id == injected_span, "remote span parents the receiver's root"
    assert handle.run_id == 42 and handle.trace_id == "trace-xyz"


def test_extract_without_context_disables():
    receiver = Tracer()
    receiver.enable(run_id=7)            # pretend a previous traced request
    receiver.extract({"op": "decode"})   # this request carries NO context
    assert receiver.enabled is False, "an untraced request must turn tracing OFF"


@pytest.mark.parametrize("bad_ctx", [
    {"trace_id": "t"},                   # missing run_id
    {"run_id": "not-a-number"},          # non-numeric run_id
    {"run_id": None},                    # null run_id
])
def test_extract_malformed_context_degrades_never_raises(bad_ctx):
    """ADR-0002: a MALFORMED telemetry context must NOT raise into handle() and
    destroy the pipeline reply — it disables tracing and proceeds, loud-but-safe."""
    receiver = Tracer()
    receiver.enable(run_id=7)            # pretend a previous traced request
    out = receiver.extract({"op": "decode", _TRACE_KEY: bad_ctx})  # must not raise
    assert out is None
    assert receiver.enabled is False, "a malformed context must turn tracing OFF, not crash"


# ============================================================ DB buffer+flush
@pytest.mark.skipif(not _db_up(), reason="harness DB unreachable")
def test_buffer_flushes_to_trace_schema():
    """End-to-end persistence against the REAL ephemeral `trace` schema: mint a run,
    record nested spans, flush, and read them back with links + dur_ms intact."""
    import psycopg

    t = Tracer()
    t.configure(process="unit", dsn=DSN)
    run_id = t.begin_run(config={"unit": True}, cmd="pytest test_spans.py",
                         process="unit", dsn=DSN)
    assert run_id is not None, "begin_run must create a code-stamped trace.run row"
    try:
        with t.span("parent", phase="x"):
            with t.span("child", cache_hit=True):
                pass
        assert len(t._buffer) == 2
        n = t.flush()
        assert n == 2
        assert t._buffer == [], "flush clears the buffer"

        with psycopg.connect(DSN) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT name, parent_span_id, span_id, dur_ms, attrs, process "
                "FROM trace.span WHERE run_id=%s ORDER BY name", (run_id,))
            rows = cur.fetchall()
            assert len(rows) == 2
            by_name = {r[0]: r for r in rows}
            child, parent = by_name["child"], by_name["parent"]
            assert child[1] == parent[2], "child.parent_span_id == parent.span_id in the DB"
            assert parent[1] is None
            assert child[3] >= 0.0 and parent[3] >= 0.0  # dur_ms persisted
            assert child[4] == {"cache_hit": True}        # attrs jsonb round-trips
            assert parent[5] == "unit"
            # code stamp landed on the run
            cur.execute("SELECT git_commit, git_tree, cmd, config FROM trace.run "
                        "WHERE run_id=%s", (run_id,))
            gc, gt, cmd, cfg = cur.fetchone()
            assert gc and gt and cmd == "pytest test_spans.py" and cfg == {"unit": True}
    finally:
        with psycopg.connect(DSN) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM trace.run WHERE run_id=%s", (run_id,))  # cascade spans
            conn.commit()


def test_flush_is_best_effort_on_bad_dsn():
    """ADR-0002 best-effort: a DB failure logs loud and drops the buffer, never raises."""
    t = Tracer()
    t.configure(process="unit", dsn="host=127.0.0.1 port=1 dbname=nope connect_timeout=1")
    t.enable(run_id=1)
    with t.span("x"):
        pass
    assert t.flush() == 0          # returned count is 0 (dropped), no exception
    assert t._buffer == []         # buffer cleared (bounded memory)


if __name__ == "__main__":
    import sys
    raise SystemExit(pytest.main([__file__, "-v", *sys.argv[1:]]))
