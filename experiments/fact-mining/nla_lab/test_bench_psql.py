#!/usr/bin/env python
"""nla_lab psql-sink + weight-source conformance gate (the queryable results store and
the real-maverick-weights precedence, proven — not asserted in a docstring).

Two tiers, by reachability:
  * OFFLINE (always runs, no DB, no fixture): the BenchRecord -> row mapping
    (`lab_report.psql_row`) — None stays None, every column present in order; the
    weight-source `model_tag` precedence (npz > HF > synthetic); the bench CLI
    mutual-exclusion of --model vs --weights-npz; and that load_fixture's npz branch is
    reached FIRST (precedence) rather than silently falling through to synthetic.
  * LIVE (only if the harness DB at spans.DEFAULT_DSN is reachable from this guest):
    write_psql round-trips synthetic records under a UNIQUE throwaway run_tag, reads them
    back asserting the field mapping (incl. None->SQL NULL and the four bench dimensions),
    then DELETEs the throwaway rows. If the DB is NOT reachable here, it SKIPS cleanly
    (the real run is on the host) — the offline mapping test still covers the row shape.

Run:  python -m pytest -q nla_lab/test_bench_psql.py   (from fact-mining/)
"""

from __future__ import annotations

import uuid

import pytest

from nla_lab import bench
from nla_lab.lab_report import (STATUS_FAILED_SHAPE, STATUS_OK, BenchRecord,
                                _PSQL_COLUMNS, psql_row, write_psql)
from spans import DEFAULT_DSN as _DEFAULT_DSN

#: the harness DSN, re-typed `str` at this module boundary (spans is follow_imports=skip
#: under nla_lab/mypy.ini, so its DEFAULT_DSN is `Any` here — one named cast, ADR-0012 P1).
DEFAULT_DSN: str = str(_DEFAULT_DSN)


def _ok_record() -> BenchRecord:
    """A fully-populated OK reading (every numeric field present)."""
    return BenchRecord(
        variant="exact_reference", regime="both", fidelity_tier="exact",
        batch=2, seq_bucket=128, status=STATUS_OK,
        lat_p50_ms=1.5, lat_p95_ms=1.9, lat_min_ms=1.4, lat_mean_ms=1.6, lat_n=10,
        rows_per_s=1057.7, fidelity_max_abs=0.0, fidelity_mean_abs=0.0,
        est_peak_device_bytes=2684354, detail="")


def _non_ok_record() -> BenchRecord:
    """A non-ok reading: lat/rows/fidelity are None (must survive as SQL NULL)."""
    return BenchRecord.non_ok(
        variant="flash_attention", regime="both", fidelity_tier="exact",
        batch=1, seq_bucket=64, status=STATUS_FAILED_SHAPE, detail="bad shape",
        est_peak_device_bytes=None)


# ============================================================== OFFLINE (no DB needed)
def test_psql_row_maps_fields_and_preserves_none() -> None:
    """The row mapping is by-column-order and None-preserving (the offline coverage that
    holds even when no DB is reachable). The four bench dimensions — latency
    (lat_p50/p95), throughput (rows_per_s), fidelity (fidelity_max/mean_abs), memory
    (est_peak_device_bytes) — are all present, and a None field stays None (-> SQL NULL)."""
    rec = _ok_record()
    row = psql_row(rec, run_tag="t", model="synthetic")
    assert len(row) == len(_PSQL_COLUMNS)
    d = dict(zip(_PSQL_COLUMNS, row))
    assert d["run_tag"] == "t" and d["model"] == "synthetic"
    assert d["variant"] == "exact_reference" and d["regime"] == "both"
    assert d["fidelity_tier"] == "exact" and d["status"] == STATUS_OK
    assert d["batch"] == 2 and d["seq_bucket"] == 128
    # the four dimensions present (latency / throughput / fidelity / memory)
    assert d["lat_p50_ms"] == 1.5 and d["lat_p95_ms"] == 1.9
    assert d["rows_per_s"] == 1057.7
    assert d["fidelity_max_abs"] == 0.0 and d["fidelity_mean_abs"] == 0.0
    assert d["est_peak_device_bytes"] == 2684354

    # a non-ok row: the absent measurements stay None (psycopg binds None as SQL NULL)
    nrow = dict(zip(_PSQL_COLUMNS, psql_row(_non_ok_record(), run_tag="t", model=None)))
    assert nrow["model"] is None
    assert nrow["lat_p50_ms"] is None and nrow["lat_p95_ms"] is None
    assert nrow["rows_per_s"] is None
    assert nrow["fidelity_max_abs"] is None and nrow["fidelity_mean_abs"] is None
    assert nrow["est_peak_device_bytes"] is None
    assert nrow["status"] == STATUS_FAILED_SHAPE and nrow["detail"] == "bad shape"


def test_model_tag_precedence() -> None:
    """The `model` column value follows the weight-source precedence npz > HF > synthetic
    (mirrors load_fixture), so a query tells real-weight runs apart."""
    assert bench.model_tag(None, None) == "synthetic"
    assert bench.model_tag("microsoft/deberta-v3-large", None) == "microsoft/deberta-v3-large"
    assert bench.model_tag(None, "/p/fixtures/deberta_maverick.npz") == \
        "maverick-npz:deberta_maverick.npz"
    # npz WINS over model (precedence), matching load_fixture's branch order
    assert bench.model_tag("microsoft/deberta-v3-large", "/p/deberta_maverick.npz") == \
        "maverick-npz:deberta_maverick.npz"


def test_cli_model_and_weights_npz_are_mutually_exclusive() -> None:
    """A run has exactly ONE weight source: passing both --model and --weights-npz fails
    loud (argparse error -> SystemExit), never silently picks one."""
    with pytest.raises(SystemExit):
        bench.main(["--model", "x", "--weights-npz", "y"])


def test_load_fixture_npz_branch_has_precedence() -> None:
    """load_fixture's npz branch is reached FIRST (precedence over synthetic): a
    weights_npz path is honored even when model is None, so a MISSING npz raises (it tried
    to load it) rather than silently falling through to the synthetic fixture. If the REAL
    maverick export happens to be present on this guest, additionally assert it resolves
    params/cfg/vocab; otherwise the missing-path raise is the precedence proof (the real
    run is on the host)."""
    import os
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    real = os.path.join(here, "fixtures", "deberta_maverick.npz")
    if os.path.exists(real):
        params, cfg, vocab = bench.load_fixture(None, real, seed=0)
        assert vocab > 0 and "embeddings.word_embeddings.weight" in params
        assert cfg is not None
    else:
        # precedence proof without the fixture: the npz branch is taken (it tries to open
        # the path and raises), it does NOT silently return the synthetic fixture.
        with pytest.raises((FileNotFoundError, OSError, ValueError)):
            bench.load_fixture(None, os.path.join(here, "fixtures", "_no_such.npz"), seed=0)


# =================================================================== LIVE (DB round-trip)
def _reachable_dsn() -> str | None:
    """The harness DB DSN if reachable from this guest within a short timeout, else None
    (so the live test SKIPS cleanly rather than hanging/failing)."""
    try:
        import psycopg
        with psycopg.connect(DEFAULT_DSN, connect_timeout=4) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return DEFAULT_DSN
    except Exception:
        return None


def test_write_psql_round_trips_against_the_harness_db() -> None:
    """write_psql APPENDS rows to nla.bench_result and they read back with the fields
    mapped correctly (None->NULL, the four dimensions present), under a UNIQUE throwaway
    run_tag that is DELETEd afterward (history of real runs untouched). SKIPS cleanly if
    the harness DB is not reachable from this guest."""
    dsn = _reachable_dsn()
    if dsn is None:
        pytest.skip("harness DB (spans.DEFAULT_DSN) not reachable from this guest")
    import psycopg

    tag = f"_pytest_throwaway_{uuid.uuid4().hex}"
    recs = [_ok_record(), _non_ok_record()]
    try:
        n = write_psql(recs, dsn, run_tag=tag, model="synthetic")
        assert n == 2
        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT variant, model, batch, seq_bucket, status, lat_p50_ms, "
                "rows_per_s, fidelity_max_abs, est_peak_device_bytes, detail "
                "FROM nla.bench_result WHERE run_tag=%s ORDER BY variant", (tag,))
            got = cur.fetchall()
        assert len(got) == 2
        by = {r[0]: r for r in got}
        # the OK row: every dimension present and exact
        ok = by["exact_reference"]
        assert ok[1] == "synthetic" and ok[2] == 2 and ok[3] == 128
        assert ok[4] == STATUS_OK
        assert ok[5] == pytest.approx(1.5) and ok[6] == pytest.approx(1057.7)
        assert ok[7] == pytest.approx(0.0) and ok[8] == 2684354
        # the non-ok row: the absent measurements are SQL NULL (None back out)
        bad = by["flash_attention"]
        assert bad[4] == STATUS_FAILED_SHAPE
        assert bad[5] is None and bad[6] is None and bad[7] is None and bad[8] is None
        assert bad[9] == "bad shape"
    finally:
        # ALWAYS clean up the throwaway group, even on assert failure (history preserved).
        with psycopg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM nla.bench_result WHERE run_tag=%s", (tag,))
            conn.commit()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
