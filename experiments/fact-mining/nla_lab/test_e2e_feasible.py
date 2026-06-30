"""test_e2e_feasible — the bench sweeps ONLY (batch, seq_bucket) cells the END-TO-END coref
pipeline could actually run, REUSING the daemon's memory model (no second model).

Four properties (the maintainer's no-OOM-region rule + the no-silent-caps discipline):
  1. AGREEMENT (ADR-0012 P1). `shape_buckets.e2e_fits` must not disagree with the daemon's OWN
     feasibility on the same inputs — it IS the daemon's `max_batch_for_length` cap, and for a
     lone doc it agrees with whether `encode_batch_chunks` raises DocTooLargeError. They share
     the ONE `peak_variable_bytes` inequality; neither re-derives it.
  2. EXCLUSION/INCLUSION. An obviously-too-big cell (B=32, S=1024 on the dense deberta-v3-large
     footprint) is excluded; an obviously-fine one (B=1, S=64) is included.
  3. LOGGED, NOT SILENT. A skipped cell is LOUDLY logged AND recorded with a DISTINCT,
     queryable status `e2e_skip` (NOT `oom` — it was never run) carrying the declared est.
  4. OPT-OUT. `--no-e2e-feasible-only` (e2e_feasible_only=False) restores the full sweep: no
     skips, no skip log.
"""
from __future__ import annotations

import pytest

import shape_buckets
from nla_lab import bench
from nla_lab.lab_report import STATUS_E2E_SKIP, STATUS_OK
from nla_lab.registry import load_all

# the DENSE deployed encoder's architecture (deberta-v3-large: hidden 1024 = 16*64,
# disentangled position table width 2*256). This is what the daemon actually runs, so the
# e2e-feasible region is THIS footprint's (not a variant's).
_LARGE_MM = shape_buckets.dense_deberta_mem_model(num_heads=16, head_size=64, pos_ebd_size=256)


def test_e2e_fits_agrees_with_daemon_capacity() -> None:
    """e2e_fits == the daemon's own max_batch_for_length cap, for every (B, S, budget) — the
    daemon emits a [B,S] forward iff B is within that cap, so the bench must not disagree."""
    for avail in (1 << 30, 4 << 30, 8 << 30, 40 << 30):
        for s in (64, 256, 1024, 2048):
            cap = shape_buckets.max_batch_for_length(_LARGE_MM, s, avail)
            for b in (1, 2, 4, 8, 16, 32):
                assert shape_buckets.e2e_fits(_LARGE_MM, b, s, available_bytes=avail) == (b <= cap)


def test_e2e_fits_agrees_with_encode_batch_chunks_for_lone_doc() -> None:
    """For a LONE doc the daemon's `encode_batch_chunks` raises DocTooLargeError iff the doc
    cannot fit at B=1 — exactly when e2e_fits(...,1,S) is False. Reuse the daemon function on
    the same inputs; the verdicts must match (a fitting S and a non-fitting S)."""
    for s in (64, 512, 1024, 2048):
        for avail in (256 << 20, 2 << 30, 6 << 30, 80 << 30):
            fits = shape_buckets.e2e_fits(_LARGE_MM, 1, s, available_bytes=avail)
            raised = False
            try:
                shape_buckets.encode_batch_chunks([0], s, _LARGE_MM, avail, max_docs=64)
            except shape_buckets.DocTooLargeError:
                raised = True
            assert fits == (not raised), (s, avail, fits, raised)


def test_obviously_too_big_excluded_and_obviously_fine_included() -> None:
    budget = 6 << 30  # a realistic ~6 GiB card share
    assert shape_buckets.e2e_fits(_LARGE_MM, 1, 64, available_bytes=budget) is True
    assert shape_buckets.e2e_fits(_LARGE_MM, 32, 1024, available_bytes=budget) is False


# a budget (bytes) that, on the tiny SYNTHETIC fixture, admits S=64 cells but not S=128 —
# forces a real skip decision through the full bench wiring (computed from the synthetic mm
# below so the threshold is honest, not a magic constant).
_SYNTH_MM = shape_buckets.dense_deberta_mem_model(num_heads=2, head_size=8, pos_ebd_size=16)
_TINY_BUDGET = (shape_buckets.peak_variable_bytes(_SYNTH_MM, 2, 64)
                + shape_buckets.peak_variable_bytes(_SYNTH_MM, 1, 128)) // 2  # between S=64 and S=128


def test_skip_is_logged_and_recorded_distinctly(capsys: pytest.CaptureFixture[str]) -> None:
    """Run the full bench wiring on the synthetic fixture with a budget that makes S=128
    e2e-infeasible: the skipped cells must be LOUDLY LOGGED and recorded `e2e_skip` (with the
    est), while S=64 cells run normally — no silent truncation."""
    load_all()
    recs = bench.run_bench(["exact_reference"], model=None, batches=(1, 2),
                           seq_buckets=(64, 128), repeats=1, warmup=1, seed=0, jsonl=None,
                           e2e_feasible_only=True, budget_bytes=_TINY_BUDGET)
    out = capsys.readouterr().out
    # LOUD log: every skipped cell is visible, never silently dropped.
    assert "[e2e-skip]" in out
    assert "B=1,S=128" in out and "B=2,S=128" in out

    by = {(r.batch, r.seq_bucket): r for r in recs}
    # the infeasible S=128 cells are recorded e2e_skip (DISTINCT from oom), est kept, never run.
    for cell in ((1, 128), (2, 128)):
        assert by[cell].status == STATUS_E2E_SKIP, (cell, by[cell].status)
        assert by[cell].status != "oom"
        assert by[cell].est_peak_device_bytes is not None
        assert by[cell].lat_p50_ms is None       # never run -> no timing
    # the feasible S=64 cells run normally (the encoder IS measured where e2e can run).
    for cell in ((1, 64), (2, 64)):
        assert by[cell].status == STATUS_OK, (cell, by[cell].status)


def test_no_e2e_feasible_only_restores_full_sweep(capsys: pytest.CaptureFixture[str]) -> None:
    """--no-e2e-feasible-only: the gate is OFF, so even the same tiny budget produces NO skips
    and NO skip log (encode-isolation research path)."""
    load_all()
    recs = bench.run_bench(["exact_reference"], model=None, batches=(1, 2),
                           seq_buckets=(64, 128), repeats=1, warmup=1, seed=0, jsonl=None,
                           e2e_feasible_only=False, budget_bytes=_TINY_BUDGET)
    out = capsys.readouterr().out
    assert "[e2e-skip]" not in out
    assert not any(r.status == STATUS_E2E_SKIP for r in recs)
