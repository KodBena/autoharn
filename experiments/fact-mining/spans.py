#!/usr/bin/env python
"""SSOT distributed-span tracer for the 3-process coref pipeline (ADR-0009 / ADR-0012).

ONE home for span recording (ADR-0012 P1). Every process — the guest client
(load_facts), the host spaCy daemon (nlp_server), and the host JAX decode daemon
(coref_decode_server + coref_host_shell) — records spans through THIS module, and
propagates the trace context THROUGH the existing ZMQ JSON meta so the three
processes stitch into one trace (ADR-0012 P2: the receiver extract()s the context
and parents its spans under the sender's current span).

WHAT IT PROVIDES
  * span(name, **attrs)  — a context manager. When the tracer is ENABLED it buffers
    one immutable reading in memory (t_start/t_end WALL + dur_ms MONOTONIC), nesting
    parent/child via a context-local span stack. When DISABLED it returns a SHARED
    nullcontext singleton — a near-zero-cost no-op, so tracing never distorts the
    measurement it takes (OFF BY DEFAULT).
  * inject(meta) / extract(meta) — carry (run_id, trace_id, current span_id) over the
    wire IN the JSON meta. inject() stamps the dict before send; extract() reads it on
    receipt, ENABLES this process's tracer for that request, and parents subsequent
    spans under the remote span. A request WITHOUT a context disables tracing for that
    request (off by default across the wire).
  * begin_run(...) — client-side: code-stamps a trace.run row (git commit/tree, exact
    cmd, config jsonb), enables the tracer, returns run_id. This is what `--trace` on
    load_facts calls to mint the run and turn tracing on across the wire.
  * flush() — BATCH-inserts the buffered readings to Postgres (ADR-0012 P9: the pure
    span model is the functional core; the DB write is the imperative shell).

CLOCK / DURATION (ADR-0009 amendment). t_start/t_end are WALL-clock (timestamptz)
and exist ONLY for cross-process ORDERING — guest<->host wall clocks can be skewed,
which BOUNDS the ordering resolution. dur_ms is a per-span duration from a MONOTONIC
clock, computed entirely within one process, so it is SKEW-IMMUNE and is the
accurate duration. Never subtract monotonic readings across processes; use wall for
ordering, dur_ms for duration.

FAIL-LOUD vs BEST-EFFORT (ADR-0002). Tracing is ORTHOGONAL to pipeline correctness,
so a DB write failure is the genuinely-right silent fallback, STATED: it is logged
LOUDLY to stderr and the buffered readings are dropped (bounded memory), but it does
NOT break the pipeline. The pipeline's own correctness paths fail loud as before;
only the (orthogonal) telemetry degrades quietly-but-audibly.

HOST/DEVICE HYGIENE. This module imports NEITHER a host array lib (numpy) NOR a
device lib (jax/torch) — psycopg is the only heavy dependency and is lazy-imported
at flush/insert time. It is therefore host-XOR-device clean by the import-XOR gate
and authors no device op, so it is safe to import into the device-side host shell.
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

# The single key the trace context rides under, inside the existing ZMQ JSON meta.
_TRACE_KEY = "_trace"

# One owner of "which harness DB" (ADR-0012 P1). Both guest and host reach this DSN.
DEFAULT_DSN = os.environ.get("HARNESS_DSN", "host=192.168.122.1 dbname=harness")

# The shared near-zero-cost no-op returned by span() when tracing is OFF. One object,
# reused for every disabled span() call, so the disabled path allocates nothing.
_NULL = contextlib.nullcontext()


def _loud(msg: str) -> None:
    """Best-effort persistence failures are audible (ADR-0002), never silent."""
    print(f"[trace] {msg}", file=sys.stderr, flush=True)


def _git_stamp() -> tuple[str, str]:
    """(git_commit, git_tree) code stamp (ADR-0009: a measurement is code-addressable).

    git_tree is hashed from a THROWAWAY index seeded from HEAD then `add -A`, so it
    captures UNCOMMITTED edits without touching the real index/working tree — the
    honest content stamp for a tree with experimental, uncommitted instrumentation.
    Best-effort: a git failure falls back to HEAD's tree, then to 'unknown'.
    """
    import subprocess
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))

    def _git(*args: str, env: Optional[dict] = None) -> str:
        try:
            r = subprocess.run(["git", "-C", here, *args],
                               capture_output=True, text=True, env=env, timeout=10)
            return r.stdout.strip()
        except Exception:
            return ""

    commit = _git("rev-parse", "HEAD") or "unknown"
    try:
        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.close()
        env = dict(os.environ, GIT_INDEX_FILE=tf.name)
        _git("read-tree", "HEAD", env=env)   # seed the temp index from HEAD
        _git("add", "-A", env=env)           # stage all (temp index only)
        tree = _git("write-tree", env=env) or _git("rev-parse", "HEAD^{tree}") or "unknown"
        os.unlink(tf.name)
    except Exception:
        tree = _git("rev-parse", "HEAD^{tree}") or "unknown"
    return commit, tree


@dataclass
class _Reading:
    """One immutable span measurement (ADR-0009: the reading, never edited)."""
    run_id: int
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    process: str
    name: str
    t_start: datetime
    t_end: datetime
    dur_ms: float
    attrs: dict


class _SpanCtx:
    """An open span: pushes its id on the context-local stack on enter, buffers an
    immutable _Reading on exit. Returned by span() only when tracing is ENABLED."""

    __slots__ = ("_t", "name", "attrs", "span_id", "parent", "_token", "_mono0", "_wall0")

    def __init__(self, tracer: "Tracer", name: str, attrs: dict):
        self._t = tracer
        self.name = name
        self.attrs = attrs

    def __enter__(self) -> "_SpanCtx":
        t = self._t
        self.parent = t._current.get()           # current top-of-stack OR remote parent
        self.span_id = uuid.uuid4().hex
        self._token = t._current.set(self.span_id)
        self._wall0 = datetime.now(timezone.utc)  # WALL: cross-process ordering only
        self._mono0 = time.monotonic()            # MONOTONIC: skew-immune duration
        return self

    def __exit__(self, *exc: Any) -> bool:
        t = self._t
        dur_ms = (time.monotonic() - self._mono0) * 1000.0
        wall1 = datetime.now(timezone.utc)
        t._buffer.append(_Reading(
            run_id=t.run_id, trace_id=t.trace_id, span_id=self.span_id,
            parent_span_id=self.parent, process=t.process, name=self.name,
            t_start=self._wall0, t_end=wall1, dur_ms=dur_ms, attrs=dict(self.attrs)))
        t._current.reset(self._token)
        return False  # never swallow an exception — tracing is orthogonal


class Tracer:
    """The span recorder. One instance is the module singleton (get_tracer()); the
    class is public so tests can stand up isolated tracers (e.g. inject on A, extract
    on B). OFF by default — span() is a no-op until enable()/extract()/begin_run()."""

    def __init__(self) -> None:
        self._enabled = False
        self.process = "unknown"
        self.dsn = DEFAULT_DSN
        self.run_id: Optional[int] = None
        self.trace_id: Optional[str] = None
        self._buffer: list[_Reading] = []
        # context-local stack: holds the current span_id (or a remote parent).
        self._current: contextvars.ContextVar[Optional[str]] = \
            contextvars.ContextVar("trace_current_span", default=None)

    # --- configuration (no side effects; does NOT enable) --------------------
    def configure(self, process: Optional[str] = None, dsn: Optional[str] = None) -> None:
        """Set this process's label and/or DB DSN. Called once at process start; it
        never enables tracing (enabling is begin_run()/extract()'s job)."""
        if process is not None:
            self.process = process
        if dsn is not None:
            self.dsn = dsn

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self, run_id: int, trace_id: Optional[str] = None) -> None:
        self._enabled = True
        self.run_id = int(run_id)
        self.trace_id = trace_id or uuid.uuid4().hex

    def disable(self) -> None:
        self._enabled = False
        self._current.set(None)

    # --- the span context manager --------------------------------------------
    def span(self, name: str, **attrs: Any):
        """Open a span. ENABLED -> a real _SpanCtx that buffers a reading on exit.
        DISABLED -> the shared nullcontext singleton (near-zero cost, allocates
        nothing), so taking a measurement never perturbs it."""
        if not self._enabled:
            return _NULL
        return _SpanCtx(self, name, attrs)

    # --- wire propagation (ADR-0012 P2) --------------------------------------
    def inject(self, meta: dict) -> dict:
        """Stamp (run_id, trace_id, current span_id) into the ZMQ JSON meta before
        send. No-op when disabled, so a non-traced run leaves the wire untouched."""
        if self._enabled and isinstance(meta, dict):
            meta[_TRACE_KEY] = {
                "run_id": self.run_id,
                "trace_id": self.trace_id,
                "span_id": self._current.get(),
            }
        return meta

    def extract(self, meta: dict) -> Optional[dict]:
        """On receipt: read the trace context from the meta. Present -> ENABLE this
        process's tracer for the request and parent subsequent spans under the remote
        span (this is what stitches the processes). Absent -> disable for the request
        (off by default across the wire). Returns the context dict, or None."""
        ctx = meta.get(_TRACE_KEY) if isinstance(meta, dict) else None
        if not ctx:
            self.disable()
            return None
        # BEST-EFFORT (ADR-0002): a malformed telemetry context — missing/non-numeric
        # run_id, an inject<->extract shape skew — must NOT raise into handle() and
        # destroy the pipeline reply. Tracing is orthogonal: validate-and-degrade
        # (loud + disable + proceed un-traced), never validate-and-fail-the-payload.
        try:
            self.enable(ctx["run_id"], ctx.get("trace_id"))
        except (KeyError, ValueError, TypeError) as e:
            _loud(f"malformed trace context {ctx!r} ({e!r}) — tracing DISABLED for "
                  "this request (pipeline proceeds un-traced)")
            self.disable()
            return None
        self._current.set(ctx.get("span_id"))   # remote parent for this process's spans
        return ctx

    # --- client-side run minting (code-stamped, ADR-0009) --------------------
    def begin_run(self, *, config: Optional[dict] = None, cmd: Optional[str] = None,
                  host: Optional[str] = None, process: Optional[str] = None,
                  dsn: Optional[str] = None) -> Optional[int]:
        """Create the code-stamped trace.run row, enable the tracer, return run_id.
        Best-effort (ADR-0002): if the DB write fails, the tracer stays DISABLED and
        the pipeline runs un-traced rather than crashing — None is returned, loudly."""
        if dsn is not None:
            self.dsn = dsn
        if process is not None:
            self.process = process
        git_commit, git_tree = _git_stamp()
        cmd = cmd if cmd is not None else " ".join(sys.argv)
        host = host if host is not None else os.uname().nodename
        trace_id = uuid.uuid4().hex
        run_id = self._insert_run(trace_id, git_commit, git_tree, cmd, config or {}, host)
        if run_id is None:
            return None
        self.enable(run_id, trace_id)
        return run_id

    def _insert_run(self, trace_id: str, git_commit: str, git_tree: str,
                    cmd: str, config: dict, host: str) -> Optional[int]:
        try:
            import psycopg
            with psycopg.connect(self.dsn) as conn, conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO trace.run (trace_id, git_commit, git_tree, cmd, config, host) "
                    "VALUES (%s,%s,%s,%s,%s::jsonb,%s) RETURNING run_id",
                    (trace_id, git_commit, git_tree, cmd, json.dumps(config), host))
                run_id = cur.fetchone()[0]
                conn.commit()   # commit NOW: servers FK-reference this row before we finish
                return int(run_id)
        except Exception as e:
            _loud(f"trace.run insert failed ({e!r}) — tracing DISABLED for this run")
            return None

    # --- persistence (imperative shell, ADR-0012 P9) -------------------------
    def flush(self) -> int:
        """BATCH-insert the buffered readings to trace.span, returning the count
        written. Best-effort (ADR-0002): the buffer is cleared first (bounded memory),
        and a DB failure is logged LOUD with the count dropped — never raised."""
        if not self._buffer:
            return 0
        rows = self._buffer
        self._buffer = []
        try:
            import psycopg
            with psycopg.connect(self.dsn) as conn, conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO trace.span "
                    "(run_id, trace_id, span_id, parent_span_id, process, name, "
                    " t_start, t_end, dur_ms, attrs) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) "
                    "ON CONFLICT (run_id, span_id) DO NOTHING",
                    [(r.run_id, r.trace_id, r.span_id, r.parent_span_id, r.process,
                      r.name, r.t_start, r.t_end, r.dur_ms, json.dumps(r.attrs))
                     for r in rows])
                conn.commit()
            return len(rows)
        except Exception as e:
            _loud(f"trace.span flush dropped {len(rows)} span(s) ({e!r})")
            return 0


# The module singleton — every process records through this one home.
_TRACER = Tracer()


def get_tracer() -> Tracer:
    return _TRACER
