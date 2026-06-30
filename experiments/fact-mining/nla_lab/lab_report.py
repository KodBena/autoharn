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

from spans import DEFAULT_DSN, get_tracer

#: the closed status vocabulary for one (variant, bucket) trial. An out-of-vocab
#: status is unrepresentable.
STATUS_OK = "ok"
STATUS_FIT_RETIRED = "fit_retired"          # a-priori retired by the variant's fit()
STATUS_NOT_IMPLEMENTED = "not_implemented"  # a stub (NotImplementedError) — expected today
STATUS_FAILED_SHAPE = "failed_shape"        # wrong output shape (watchdog caught)
STATUS_FAILED_NONFINITE = "failed_nonfinite"  # NaN/Inf (watchdog caught)
STATUS_FAILED_ERROR = "failed_error"        # any other exception in the variant
STATUS_OOM = "oom"                          # device RESOURCE_EXHAUSTED at this (B,Sbkt): too big to fit
STATUS_E2E_SKIP = "e2e_skip"                # NOT RUN: the e2e coref pipeline could not run this
#                                             (B,Sbkt) — a recorded, queryable DECISION (the dense
#                                             encode+decode+retained envelope would OOM), distinct
#                                             from `oom` (which is a forward that WAS run and failed)


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
    #: the FOURTH dimension: the variant's DECLARED conservative upper bound on the forward's
    #: peak VARIABLE (non-weight) DEVICE bytes at this (batch, seq_bucket) — the contract estimate
    #: (`EncodeVariant.est_peak_device_bytes`), NOT a live measurement. It is an a-priori DECLARED
    #: quantity, so it is recorded even for non-ok (fit_retired/not_implemented/failed) trials.
    est_peak_device_bytes: int | None
    detail: str

    @classmethod
    def latency_throughput(cls, *, variant: str, regime: str, fidelity_tier: str,
                           batch: int, seq_bucket: int, stat: Stat, n_real_rows: int,
                           fidelity_max_abs: float | None, fidelity_mean_abs: float | None,
                           est_peak_device_bytes: int | None) -> "BenchRecord":
        """An OK record: derive rows/s from the warm median per-call time over the real
        (non-dummy) rows in the batch (throughput lane), keep p50/p95 (latency lane), carry the
        declared peak-device-bytes estimate (memory lane)."""
        med_s = stat.p50_ms / 1000.0
        rows_per_s = (n_real_rows / med_s) if med_s > 0 else None
        return cls(variant=variant, regime=regime, fidelity_tier=fidelity_tier,
                   batch=batch, seq_bucket=seq_bucket, status=STATUS_OK,
                   lat_p50_ms=stat.p50_ms, lat_p95_ms=stat.p95_ms, lat_min_ms=stat.min_ms,
                   lat_mean_ms=stat.mean_ms, lat_n=stat.n, rows_per_s=rows_per_s,
                   fidelity_max_abs=fidelity_max_abs, fidelity_mean_abs=fidelity_mean_abs,
                   est_peak_device_bytes=est_peak_device_bytes, detail="")

    @classmethod
    def non_ok(cls, *, variant: str, regime: str, fidelity_tier: str, batch: int,
               seq_bucket: int, status: str, detail: str,
               est_peak_device_bytes: int | None) -> "BenchRecord":
        return cls(variant=variant, regime=regime, fidelity_tier=fidelity_tier,
                   batch=batch, seq_bucket=seq_bucket, status=status,
                   lat_p50_ms=None, lat_p95_ms=None, lat_min_ms=None, lat_mean_ms=None,
                   lat_n=0, rows_per_s=None, fidelity_max_abs=None, fidelity_mean_abs=None,
                   est_peak_device_bytes=est_peak_device_bytes, detail=detail)


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


# --------------------------------------------------------------- the PSQL results sink
# ONE queryable home for assembled bench rows (ADR-0012 P1): the SAME harness DB the
# tracer writes spans to (spans.DEFAULT_DSN, HARNESS_DSN-overridable — never a re-typed
# literal). This is what lets the process-per-variant runner (run_portfolio_bench.py)
# have each isolated subprocess write its rows and EXIT — the maintainer queries the
# assembled `nla.bench_result` table from the guest, no JSONL hand-off. Rows are
# APPENDED (never deleted): each sweep is one `run_tag` group, so history is preserved.
#
# It is idempotent (CREATE SCHEMA / TABLE IF NOT EXISTS), so any subprocess can be the
# first to create the table — no separate migration step before a fresh portfolio run.
#: the bench_result schema/table — the run-grouped, append-only readings store.
_PSQL_SCHEMA_DDL = "CREATE SCHEMA IF NOT EXISTS nla"
_PSQL_TABLE_DDL = """\
CREATE TABLE IF NOT EXISTS nla.bench_result (
    id                    bigserial PRIMARY KEY,
    run_ts                timestamptz NOT NULL DEFAULT now(),
    run_tag               text,
    model                 text,
    variant               text,
    regime                text,
    fidelity_tier         text,
    batch                 int,
    seq_bucket            int,
    status                text,
    lat_p50_ms            float8,
    lat_p95_ms            float8,
    rows_per_s            float8,
    fidelity_max_abs      float8,
    fidelity_mean_abs     float8,
    est_peak_device_bytes bigint,
    detail                text
)"""

#: the INSERT column order — the SSOT both the DDL and `psql_row` mirror (one list, so a
#: column added in one place must be added here, never silently skewed).
_PSQL_COLUMNS = ("run_tag", "model", "variant", "regime", "fidelity_tier", "batch",
                 "seq_bucket", "status", "lat_p50_ms", "lat_p95_ms", "rows_per_s",
                 "fidelity_max_abs", "fidelity_mean_abs", "est_peak_device_bytes",
                 "detail")


def psql_row(rec: BenchRecord, run_tag: str, model: str | None) -> tuple[object, ...]:
    """Map one BenchRecord -> the `nla.bench_result` value tuple (in `_PSQL_COLUMNS`
    order), stamped with the run's `run_tag` and `model`. A None field STAYS None ->
    psycopg binds it as SQL NULL (a non-ok row's lat/rows/fidelity, an underivable
    est_peak). PURE + DB-free, so the row mapping is unit-testable offline (no DB)."""
    return (run_tag, model, rec.variant, rec.regime, rec.fidelity_tier, rec.batch,
            rec.seq_bucket, rec.status, rec.lat_p50_ms, rec.lat_p95_ms, rec.rows_per_s,
            rec.fidelity_max_abs, rec.fidelity_mean_abs, rec.est_peak_device_bytes,
            rec.detail)


def write_psql(records: list[BenchRecord], dsn: str = DEFAULT_DSN, *,
               run_tag: str, model: str | None) -> int:
    """APPEND the records to `nla.bench_result` in the harness DB, returning the count
    written. Idempotently creates the schema+table first, then inserts every record
    tagged with `run_tag` (one queryable group) and `model` (so real-weight runs sort
    apart from synthetic). PRIOR runs are NOT touched — history is preserved.

    psycopg is the repo's existing host dependency (load_facts.py / spans.py show the
    pattern); it is neither numpy nor a device lib, so this stays host-XOR clean."""
    if not records:
        return 0
    import psycopg
    cols = ", ".join(_PSQL_COLUMNS)
    placeholders = ", ".join(["%s"] * len(_PSQL_COLUMNS))
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(_PSQL_SCHEMA_DDL)
        cur.execute(_PSQL_TABLE_DDL)
        cur.executemany(
            f"INSERT INTO nla.bench_result ({cols}) VALUES ({placeholders})",
            [psql_row(r, run_tag, model) for r in records])
        conn.commit()
    return len(records)


def _fmt(x: float | None, spec: str) -> str:
    return "—".rjust(len(format(0.0, spec))) if x is None else format(x, spec)


def _fmt_mib(nbytes: int | None, spec: str) -> str:
    """The declared peak DEVICE bytes -> MiB for the table (the memory lane). `None` only if a
    variant's estimate could not be derived (a contract bug — never expected on the dense
    default)."""
    return "—".rjust(len(format(0.0, spec))) if nbytes is None else format(nbytes / (1 << 20), spec)


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
        f"  {STATUS_OOM:16} the forward did NOT FIT the device arena at (B, Sbkt) "
        "(RESOURCE_EXHAUSTED) —\n"
        f"  {'':16} a recorded CAPACITY outcome, not a bug. A variant that fits where the\n"
        f"  {'':16} dense reference OOMs is exactly the win we want to see. (Raise the bench\n"
        f"  {'':16} arena — see run_portfolio_bench --mem-fraction / preallocate — if free VRAM allows.)\n"
        f"  {STATUS_E2E_SKIP:16} NOT RUN: the END-TO-END coref pipeline could not run this (B, Sbkt) —\n"
        f"  {'':16} the dense encode forward would not fit the daemon's own VRAM budget\n"
        f"  {'':16} (shape_buckets.e2e_fits == the daemon's max_batch_for_length cap). A\n"
        f"  {'':16} RECORDED, queryable DECISION (the est is kept), distinct from `oom`: this\n"
        f"  {'':16} cell was NEVER RUN (no point benchmarking the encoder where e2e can't run),\n"
        f"  {'':16} whereas `oom` is a forward that WAS run and RESOURCE_EXHAUSTED. Pass\n"
        f"  {'':16} --no-e2e-feasible-only to bench these anyway (encode-isolation research).\n"
        "devMiB: the variant's DECLARED conservative UPPER BOUND on the forward's peak VARIABLE\n"
        "  (non-weight) DEVICE bytes at (B, Sbkt), in MiB — the 4th dimension alongside\n"
        "  latency/throughput/fidelity (EncodeVariant.est_peak_device_bytes; DEVICE bytes only,\n"
        "  NOT host RSS). It is the dense-reference bound (shape_buckets.peak_variable_bytes)\n"
        "  unless a profile-changing variant overrides it; recorded even for non-ok rows.\n"
        "regime coverage: the default (batch 1-2 x seq 64-128) is the CPU self-test geometry\n"
        "  (latency lane). The THROUGHPUT lane (large-batch, compute-bound) and the S>=512\n"
        "  window where the linear-attention variants fit need a larger sweep, e.g.\n"
        "  --batches 16 32 --seq-buckets 512 1024.")


def format_table(records: list[BenchRecord]) -> str:
    """The comparison table: variant × bucket, both lanes + fidelity + status."""
    head = (f"{'variant':18} {'regime':10} {'B':>3} {'Sbkt':>5} {'p50ms':>9} "
            f"{'p95ms':>9} {'rows/s':>10} {'max|Δ|':>10} {'devMiB':>10} {'status':>16}")
    lines = [head, "-" * len(head)]
    for r in records:
        lines.append(
            f"{r.variant:18} {r.regime:10} {r.batch:>3} {r.seq_bucket:>5} "
            f"{_fmt(r.lat_p50_ms, '9.3f')} {_fmt(r.lat_p95_ms, '9.3f')} "
            f"{_fmt(r.rows_per_s, '10.1f')} {_fmt(r.fidelity_max_abs, '10.2e')} "
            f"{_fmt_mib(r.est_peak_device_bytes, '10.2f')} {r.status:>16}")
    return "\n".join(lines)
