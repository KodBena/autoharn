#!/usr/bin/env python
"""lab_report — the bench RECORD SCHEMA, the robust aggregation, and the report sinks
(host-side; one owner of "how a result is shaped and emitted", ADR-0012 P3).

THE RECORD IS A DOCUMENTED CROSS-BATCH CONTRACT (A7). One `BenchRecord` per
`(variant, batch, seq_bucket)` carries BOTH lanes — latency (p50/p95, compile-excluded,
warm) AND throughput (rows/s) — plus the P6 fidelity vs the exact reference and the
declared {regime, fidelity_tier} and the run status. Latency and throughput are
DISTINCT comparables and never collapsed into one number (B10): the regime axiom
requires both.

ROBUST STATS, NOT ONE EYEBALLED NUMBER (A7 / ADR-0009 robust-benchmark-statistics):
`agg` reduces the warm per-call sample to p50/p95/min/mean/n.

MEASUREMENT vs INTERPRETATION (ADR-0009 2026-06-24 amendment). Each `BenchRecord` is a
READING (immutable measured fact). It is recorded to the `trace.span` store via
`spans.get_tracer()` — the ONE bench/trace home (no second store, B2/ADR-0012 P1) —
and mirrored to a local JSONL belt-and-suspenders. A perf CLAIM about a record ("X is
faster") is a separate, supersedable finding, authored elsewhere, never minted here.

HOST-XOR-DEVICE: stdlib + `spans` (host-neutral). No numpy, no jax.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass

from spans import get_tracer

#: the closed status vocabulary for one (variant, bucket) trial. An out-of-vocab
#: status is unrepresentable.
STATUS_OK = "ok"
STATUS_FIT_RETIRED = "fit_retired"          # a-priori retired by the variant's fit()
STATUS_NOT_IMPLEMENTED = "not_implemented"  # a stub (NotImplementedError) — expected today
STATUS_FAILED_SHAPE = "failed_shape"        # wrong output shape (watchdog caught)
STATUS_FAILED_NONFINITE = "failed_nonfinite"  # NaN/Inf (watchdog caught)
STATUS_FAILED_ERROR = "failed_error"        # any other exception in the variant


@dataclass(frozen=True)
class Stat:
    """Robust reduction of a warm per-call timing sample (ms)."""
    p50_ms: float
    p95_ms: float
    min_ms: float
    mean_ms: float
    n: int


def agg(seconds: list[float]) -> Stat:
    """p50/p95/min/mean/n over warm per-call seconds -> milliseconds (A7)."""
    ms = sorted(s * 1000.0 for s in seconds)
    n = len(ms)

    def pct(p: float) -> float:
        if n == 1:
            return ms[0]
        k = min(n - 1, max(0, int(round(p * (n - 1)))))
        return ms[k]

    return Stat(p50_ms=pct(0.50), p95_ms=pct(0.95), min_ms=ms[0],
                mean_ms=statistics.fmean(ms), n=n)


@dataclass(frozen=True)
class BenchRecord:
    """One immutable measured reading for (variant, batch, seq_bucket) — the
    cross-batch schema. `lat_*` is the warm latency lane; `rows_per_s` the throughput
    lane; `fidelity_max_abs/mean_abs` the P6 distance vs exact_reference (0.0 for the
    reference itself; None when the trial did not produce output). `detail` carries the
    failure/retire reason."""
    variant: str
    regime: str
    fidelity_tier: str
    batch: int
    seq_bucket: int
    status: str
    lat_p50_ms: float | None
    lat_p95_ms: float | None
    lat_min_ms: float | None
    lat_mean_ms: float | None
    lat_n: int
    rows_per_s: float | None
    fidelity_max_abs: float | None
    fidelity_mean_abs: float | None
    detail: str

    @classmethod
    def latency_throughput(cls, *, variant: str, regime: str, fidelity_tier: str,
                           batch: int, seq_bucket: int, stat: Stat, n_real_rows: int,
                           fidelity_max_abs: float | None, fidelity_mean_abs: float | None
                           ) -> "BenchRecord":
        """An OK record: derive rows/s from the warm median per-call time over the real
        (non-dummy) rows in the batch (throughput lane), keep p50/p95 (latency lane)."""
        med_s = stat.p50_ms / 1000.0
        rows_per_s = (n_real_rows / med_s) if med_s > 0 else None
        return cls(variant=variant, regime=regime, fidelity_tier=fidelity_tier,
                   batch=batch, seq_bucket=seq_bucket, status=STATUS_OK,
                   lat_p50_ms=stat.p50_ms, lat_p95_ms=stat.p95_ms, lat_min_ms=stat.min_ms,
                   lat_mean_ms=stat.mean_ms, lat_n=stat.n, rows_per_s=rows_per_s,
                   fidelity_max_abs=fidelity_max_abs, fidelity_mean_abs=fidelity_mean_abs,
                   detail="")

    @classmethod
    def non_ok(cls, *, variant: str, regime: str, fidelity_tier: str, batch: int,
               seq_bucket: int, status: str, detail: str) -> "BenchRecord":
        return cls(variant=variant, regime=regime, fidelity_tier=fidelity_tier,
                   batch=batch, seq_bucket=seq_bucket, status=status,
                   lat_p50_ms=None, lat_p95_ms=None, lat_min_ms=None, lat_mean_ms=None,
                   lat_n=0, rows_per_s=None, fidelity_max_abs=None, fidelity_mean_abs=None,
                   detail=detail)


def record_span(rec: BenchRecord) -> None:
    """Mirror a record into the `trace.span` store via the SSOT tracer (one home).
    No-op unless a run is active (tracer enabled), so a `--no-trace` bench still emits
    the table + JSONL. Heavy I/O is OFF the timed path: this is called at the
    between-trial seam, never inside `warm_time_seconds` (A12)."""
    t = get_tracer()
    with t.span(f"nla_bench.{rec.variant}", **{k: v for k, v in asdict(rec).items()
                                               if v is not None}):
        pass


def write_jsonl(records: list[BenchRecord], path: str) -> None:
    """Belt-and-suspenders local sink (A12): one JSON object per record."""
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r)) + "\n")


def _fmt(x: float | None, spec: str) -> str:
    return "—".rjust(len(format(0.0, spec))) if x is None else format(x, spec)


def status_legend() -> str:
    """A legend disambiguating the status column — so a persistent `fit_retired` /
    `not_implemented` row is read as an EXPECTED portfolio/skeleton state, not a broken
    impl (the three-reviewer legibility note). Also states the regime-coverage caveat:
    the throughput (large-batch, compute-bound) regime — and the seq window where the
    linear-attention variants stop being `fit_retired` — is only reached with a larger
    sweep, e.g. `--batches 16 32 --seq-buckets 512 1024`; the default geometry is the
    fast CPU self-test geometry and exercises the latency lane only."""
    return (
        "status legend:\n"
        f"  {STATUS_OK:16} measured both lanes + P6 fidelity vs exact_reference.\n"
        f"  {STATUS_FIT_RETIRED:16} a-priori retired by the variant's fit() at this bucket — a "
        "RECORDED\n"
        f"  {'':16} portfolio decision (e.g. Nyström/Performer below the S>=512\n"
        f"  {'':16} crossover), NOT a broken impl. Raise --seq-buckets to exercise it.\n"
        f"  {STATUS_NOT_IMPLEMENTED:16} stub: encode() raises NotImplementedError — the EXPECTED\n"
        f"  {'':16} pre-fill state until the follow-on agent fills the math.\n"
        f"  {STATUS_FAILED_SHAPE:16} / {STATUS_FAILED_NONFINITE} / {STATUS_FAILED_ERROR}: a real failure the "
        "watchdog flagged (loud, never coerced).\n"
        "regime coverage: the default (batch 1-2 x seq 64-128) is the CPU self-test geometry\n"
        "  (latency lane). The THROUGHPUT lane (large-batch, compute-bound) and the S>=512\n"
        "  window where the linear-attention variants fit need a larger sweep, e.g.\n"
        "  --batches 16 32 --seq-buckets 512 1024.")


def format_table(records: list[BenchRecord]) -> str:
    """The comparison table: variant × bucket, both lanes + fidelity + status."""
    head = (f"{'variant':18} {'regime':10} {'B':>3} {'Sbkt':>5} {'p50ms':>9} "
            f"{'p95ms':>9} {'rows/s':>10} {'max|Δ|':>10} {'status':>16}")
    lines = [head, "-" * len(head)]
    for r in records:
        lines.append(
            f"{r.variant:18} {r.regime:10} {r.batch:>3} {r.seq_bucket:>5} "
            f"{_fmt(r.lat_p50_ms, '9.3f')} {_fmt(r.lat_p95_ms, '9.3f')} "
            f"{_fmt(r.rows_per_s, '10.1f')} {_fmt(r.fidelity_max_abs, '10.2e')} "
            f"{r.status:>16}")
    return "\n".join(lines)
