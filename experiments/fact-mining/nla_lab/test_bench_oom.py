"""test_bench_oom — a device OOM at a (B, Sbkt) cell is a RECORDED capacity outcome, not a
crash, and not a silent pass. A shape too big for the arena (e.g. dense at large B×S) must:
  * in build_reference_cache: cache None for that shape (reference unavailable) and continue;
  * in run_one: record status 'oom' (distinct from failed_error) and keep sweeping —
    so a variant that FITS where the dense reference OOMs is still measured.
A NON-OOM failure is a real bug and must still propagate (fail-loud, P5)."""
from __future__ import annotations

import pytest

from nla_lab import bench, lab_measure
from nla_lab.lab_report import STATUS_OOM
from nla_lab.registry import load_all


def _oom(*_a: object, **_k: object) -> object:
    raise RuntimeError(
        "RESOURCE_EXHAUSTED: Out of memory while trying to allocate 9.00GiB. "
        "[executable_name='jit_forward']")


def test_reference_oom_caches_none_and_continues(monkeypatch: pytest.MonkeyPatch) -> None:
    load_all()
    params, cfg, vocab = bench.load_fixture(None, None, 0)
    monkeypatch.setattr(lab_measure, "run_lhs", _oom)
    cache = bench.build_reference_cache(params, cfg, vocab, (1,), (64,), 0)
    assert cache[(1, 64)] is None          # too big -> None, NOT a crash


def test_variant_oom_is_recorded_distinctly_and_sweep_continues(
        monkeypatch: pytest.MonkeyPatch) -> None:
    load_all()
    params, cfg, vocab = bench.load_fixture(None, None, 0)
    monkeypatch.setattr(lab_measure, "run_lhs", _oom)
    recs = bench.run_one("exact_reference", params, cfg, vocab,
                         (1, 2), (64,), repeats=2, warmup=1, seed=0, ref_cache={})
    assert recs, "the sweep must still produce records (one per cell), not abort"
    assert all(r.status == STATUS_OOM for r in recs), [r.status for r in recs]
    # est is still reported on an oom row (the predicted peak that did not fit)
    assert all(r.est_peak_device_bytes is not None for r in recs)


def test_non_oom_reference_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    load_all()
    params, cfg, vocab = bench.load_fixture(None, None, 0)

    def _boom(*_a: object, **_k: object) -> object:
        raise RuntimeError("a real bug, not a capacity limit")

    monkeypatch.setattr(lab_measure, "run_lhs", _boom)
    with pytest.raises(RuntimeError, match="real bug"):
        bench.build_reference_cache(params, cfg, vocab, (1,), (64,), 0)
