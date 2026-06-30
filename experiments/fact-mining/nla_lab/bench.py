#!/usr/bin/env python
"""bench — the auto-benchmark RUNNER (host orchestration; ADR-0012 P3 one-owner).

Ports control_lab's good core (uniform interface + registry + auto-bench + metrics +
config-driven runs) and LEAVES its lapses: this lives next to jax_deberta.py (not
buried under a misleading parent, B1); the registry value type is the real factory,
not `Any` (B2); the contract is a typed ABC + the exact-reference round-trip, not a
runtime_checkable + frozen-by-comment (B3); the runner / scorer / report are split
(B6); the bench runs against a FIXED seeded corpus, not a live external stream (B9);
latency and throughput are distinct comparables (B10); a fidelity lane vs the exact
reference exists (B11); device math is confined to lab_measure (B12).

AUTO-BENCH SHAPE (A6/A7). For each registered variant over the sweep of
`(batch ∈ ENCODE_BATCH_BUCKETS, seq_bucket ∈ ENCODE_LEN_BUCKETS)`: check the variant's
a-priori `fit` (record fit_retired if it declines), else compile-once + warm-time the
RUN-ONLY forward in both lanes and compute P6 fidelity vs the exact reference. A
malformed/throwing/NaN variant is CAUGHT, flagged as a FAILURE, and the sweep
CONTINUES — the warm params fixture is loaded once and never torn down (A10).

HOST-XOR-DEVICE. This file imports NO numpy and NO device lib. It holds the device
`params`/`cfg` as opaque handles (from the boundary loader or the synthetic fixture)
and routes every jax op through `lab_measure` — exactly as coref_decode_server (host)
delegates to coref_host_shell (device). `jax_deberta`/`deberta_weights` are
neutral-named, so the import-XOR gate stays green.
"""

from __future__ import annotations

import argparse
import sys
from typing import cast

import shape_buckets
from nla_lab.contract import EncodeBucket
from nla_lab.lab_report import (STATUS_FAILED_ERROR, STATUS_FAILED_NONFINITE,
                                STATUS_FAILED_SHAPE, STATUS_FIT_RETIRED,
                                STATUS_NOT_IMPLEMENTED, STATUS_OK, BenchRecord, agg,
                                format_table, record_span, status_legend, write_jsonl)
from nla_lab.registry import load_all, make, portfolio_names

from nla_lab import lab_corpus
from nla_lab import lab_measure

REFERENCE_NAME = "exact_reference"   # the baseline every fidelity is measured against

# default self-test geometry: the two cheapest length rungs × batch {1,2} — the fast
# CPU self-test geometry, exercising the LATENCY lane in milliseconds. NOTE (regime
# coverage): this default does NOT reach the throughput (large-batch, compute-bound)
# regime, and it is below the S>=512 crossover where the linear-attention variants
# (nystrom/performer) stop being fit_retired — so under the default those two are
# ALWAYS fit_retired BY DESIGN (an a-priori portfolio decision, not a broken impl).
# To exercise the throughput lane + that fit window, pass a larger sweep, e.g.
# `--batches 16 32 --seq-buckets 512 1024` (both on the shape_buckets ladders).
_DEFAULT_BATCHES = (1, 2)
_DEFAULT_SEQ_BUCKETS = (64, 128)


def _real_rows(mask_rows: list[list[int]]) -> int:
    """Number of non-empty (real) rows in a batch — the throughput denominator (dummy
    rows would never appear here since the corpus emits only real rows)."""
    return sum(1 for r in mask_rows if any(r))


def run_one(variant_name: str, params: dict[str, object], cfg: object, vocab: int,
            batches: tuple[int, ...], seq_buckets: tuple[int, ...],
            repeats: int, warmup: int, seed: int,
            ref_cache: dict[tuple[int, int], object]) -> list[BenchRecord]:
    """Bench ONE variant across the (batch × seq_bucket) sweep, returning its records.
    `ref_cache[(B,Sbkt)]` holds the exact-reference lhs for fidelity reuse."""
    variant = make(variant_name)
    hidden = cfg.num_heads * cfg.head_size   # type: ignore[attr-defined]
    records: list[BenchRecord] = []
    meta = dict(variant=variant_name, regime=variant.regime.value,
                fidelity_tier=variant.fidelity_tier.value)
    for s_bucket in seq_buckets:
        for batch in batches:
            bucket = EncodeBucket(batch=batch, seq_bucket=s_bucket)  # validates the ladder
            # the DECLARED memory dimension (contract estimate, not a live measurement) — an
            # a-priori quantity, derived once per (variant, bucket) and recorded on EVERY record
            # regardless of run outcome. A pure host-side int computation (shape_buckets, no
            # device op), computed OFF the device path. The memory lane is INDEPENDENT and
            # RESILIENT like the others (A10): a broken `est_peak_device_bytes` OVERRIDE blanks
            # ONLY this variant's devMiB cell (recorded None -> "—"), it does NOT tear down the
            # sweep — so one follow-on agent's bad memory override cannot red the bench for the
            # other seven (the same parallel-safety invariant as the per-variant IMPLEMENTED flag).
            try:
                est: int | None = variant.est_peak_device_bytes(bucket, cfg)
            except Exception:
                est = None
            verdict = variant.fit(bucket)
            if not verdict.ok:
                records.append(BenchRecord.non_ok(
                    **meta, batch=batch, seq_bucket=s_bucket,
                    status=STATUS_FIT_RETIRED, detail=verdict.reason,
                    est_peak_device_bytes=est))
                continue
            ids_rows, mask_rows = lab_corpus.make_batch(batch, s_bucket, vocab, seed)
            ids, mask = lab_measure.lift_batch(ids_rows, mask_rows)
            expected = (batch, s_bucket, hidden)
            ref_lhs = ref_cache.get((batch, s_bucket))
            try:
                lhs = lab_measure.run_lhs(variant, params, ids, mask, cfg)  # type: ignore[arg-type]
            except NotImplementedError as e:
                records.append(BenchRecord.non_ok(
                    **meta, batch=batch, seq_bucket=s_bucket,
                    status=STATUS_NOT_IMPLEMENTED, detail=str(e).split("\n")[0],
                    est_peak_device_bytes=est))
                continue
            except Exception as e:                       # any other variant failure
                records.append(BenchRecord.non_ok(
                    **meta, batch=batch, seq_bucket=s_bucket,
                    status=STATUS_FAILED_ERROR, detail=f"{type(e).__name__}: {e}",
                    est_peak_device_bytes=est))
                continue
            status, detail = lab_measure.guard_output(lhs, expected)
            if status == STATUS_FAILED_SHAPE or status == STATUS_FAILED_NONFINITE:
                records.append(BenchRecord.non_ok(
                    **meta, batch=batch, seq_bucket=s_bucket, status=status, detail=detail,
                    est_peak_device_bytes=est))
                continue
            # fidelity vs the exact reference (0.0 for the reference itself)
            if ref_lhs is None:
                fmax = fmean = None
            else:
                # ref_lhs is held opaquely by the host (device-array handle); the
                # device-side fidelity reads it as jax.Array (host↔device boundary).
                fmax, fmean = lab_measure.fidelity_delta(lhs, ref_lhs, mask)  # type: ignore[arg-type]
            stat = agg(lab_measure.warm_time_seconds(
                variant, params, ids, mask, cfg, repeats, warmup))  # type: ignore[arg-type]
            records.append(BenchRecord.latency_throughput(
                **meta, batch=batch, seq_bucket=s_bucket, stat=stat,
                n_real_rows=_real_rows(mask_rows), fidelity_max_abs=fmax,
                fidelity_mean_abs=fmean, est_peak_device_bytes=est))
    return records


def build_reference_cache(params: dict[str, object], cfg: object, vocab: int,
                          batches: tuple[int, ...], seq_buckets: tuple[int, ...],
                          seed: int) -> dict[tuple[int, int], object]:
    """Run the exact reference once per (batch, seq_bucket) and cache its lhs, so every
    variant's fidelity is measured against the SAME reference array (and the reference's
    own fidelity-vs-itself is exactly 0)."""
    ref = make(REFERENCE_NAME)
    cache: dict[tuple[int, int], object] = {}
    for s_bucket in seq_buckets:
        for batch in batches:
            ids_rows, mask_rows = lab_corpus.make_batch(batch, s_bucket, vocab, seed)
            ids, mask = lab_measure.lift_batch(ids_rows, mask_rows)
            cache[(batch, s_bucket)] = lab_measure.run_lhs(ref, params, ids, mask, cfg)  # type: ignore[arg-type]
    return cache


def load_fixture(model: str | None, seed: int) -> tuple[dict[str, object], object, int]:
    """Return `(params, cfg, vocab)`. `model=None` -> the synthetic self-test fixture
    (no HF download; CPU jax). Otherwise the boundary loader `deberta_weights.load_jax_deberta`
    (imports torch+numpy+jax — the declared conversion seam, not scanned)."""
    if model is None:
        cfg = lab_measure.synthetic_cfg()
        vocab, intermediate = 100, 64
        params = lab_measure.synthetic_deberta(cfg, vocab, intermediate, seed)
        # the host holds device-array params OPAQUELY (it routes every jax op through
        # lab_measure); cast the typed fixture to the host's object-handle view.
        return cast("dict[str, object]", params), cfg, vocab
    import deberta_weights
    params, cfg, _hf = deberta_weights.load_jax_deberta(model)
    vocab = int(params["embeddings.word_embeddings.weight"].shape[0])
    return params, cfg, vocab


def run_bench(variant_names: list[str], model: str | None, batches: tuple[int, ...],
              seq_buckets: tuple[int, ...], repeats: int, warmup: int, seed: int,
              jsonl: str | None) -> list[BenchRecord]:
    """The full sweep: load the warm fixture ONCE, build the reference cache, bench each
    variant, emit table + spans + JSONL."""
    params, cfg, vocab = load_fixture(model, seed)
    ref_cache = build_reference_cache(params, cfg, vocab, batches, seq_buckets, seed)
    all_records: list[BenchRecord] = []
    for name in variant_names:
        all_records.extend(run_one(name, params, cfg, vocab, batches, seq_buckets,
                                   repeats, warmup, seed, ref_cache))
    for rec in all_records:
        record_span(rec)                       # one home: trace.span via the SSOT tracer
    if jsonl:
        write_jsonl(all_records, jsonl)
    return all_records


# --------------------------------------------------------------- harness self-proof
def self_test() -> list[BenchRecord]:
    """THE END-TO-END PROOF the whole harness works (ADR-0013 "prove it with a working
    impl that round-trips"). On the synthetic fixture, assert:
      1. exact_reference resolves through the registry, runs through the bench, and its
         fidelity-vs-itself is EXACTLY 0.0 (the contract+registry+bench round-trip);
      2. the deliberately-broken `_smoke_broken` variant is CAUGHT and flagged a FAILURE
         (the watchdog fires; the sweep continues — A10/B8);
      3. each portfolio variant matches its OWN declared `IMPLEMENTED` flag (R3-F5): a stub
         (`IMPLEMENTED=False`) is not_implemented/fit_retired (never a silent ok); an
         `IMPLEMENTED=True` variant runs cleanly (ok/fit_retired at every bucket, never
         not_implemented and never a watchdog failure). This is DECOUPLED from the global
         "all stubs unimplemented" state, so one agent filling their math (flipping their
         own flag) cannot red this shared self-test for the other seven.
    Returns the records (for printing). Raises AssertionError on any violation."""
    load_all()
    names = portfolio_names() + ["_smoke_broken"]
    records = run_bench(names, model=None, batches=_DEFAULT_BATCHES,
                        seq_buckets=_DEFAULT_SEQ_BUCKETS, repeats=5, warmup=2,
                        seed=0, jsonl=None)
    by = {(r.variant, r.batch, r.seq_bucket): r for r in records}

    # 1. exact_reference round-trips: ok everywhere, fidelity-vs-itself == 0.0
    ref_recs = [r for r in records if r.variant == REFERENCE_NAME]
    assert ref_recs, "exact_reference produced no records"
    for r in ref_recs:
        assert r.status == "ok", f"exact_reference not ok: {r.status} {r.detail}"
        assert r.fidelity_max_abs == 0.0, (
            f"exact_reference fidelity-vs-itself != 0: {r.fidelity_max_abs}")
        assert r.lat_p50_ms is not None and r.rows_per_s is not None

    # 2. the broken smoke variant is flagged a failure (never silently substituted)
    broken = [r for r in records if r.variant == "_smoke_broken"]
    assert broken, "_smoke_broken produced no records"
    assert all(r.status in (STATUS_FAILED_SHAPE, STATUS_FAILED_NONFINITE) for r in broken), (
        f"watchdog did not flag _smoke_broken: {[(r.status, r.detail) for r in broken]}")

    # 3. each portfolio variant matches its OWN IMPLEMENTED flag (R3-F5 — decoupled from
    #    the global all-stub state; the flag is read from the variant's own class). A stub
    #    (IMPLEMENTED=False) must be not_implemented/fit_retired, never a silent ok; an
    #    IMPLEMENTED variant must run cleanly (ok/fit_retired), never not_implemented and
    #    never a watchdog FAILURE — so a variant that claims implemented but errors (NaN,
    #    wrong shape, an exception) is still caught here.
    for n in portfolio_names():
        if n == REFERENCE_NAME:
            continue
        recs = [r for r in records if r.variant == n]
        assert recs, f"variant {n} produced no records"
        if make(n).IMPLEMENTED:
            assert all(r.status in (STATUS_OK, STATUS_FIT_RETIRED) for r in recs), (
                f"variant {n} declares IMPLEMENTED=True but did not run cleanly "
                f"(expected ok/fit_retired at every bucket): "
                f"{[(r.status, r.detail) for r in recs]}")
        else:
            assert all(r.status in (STATUS_NOT_IMPLEMENTED, STATUS_FIT_RETIRED) for r in recs), (
                f"stub {n} (IMPLEMENTED=False) unexpectedly ran: "
                f"{[(r.status, r.detail) for r in recs]}")
    return records


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="nla_lab encode-variant auto-benchmark")
    ap.add_argument("--variants", nargs="*", default=None,
                    help="variant names (default: the full portfolio)")
    ap.add_argument("--model", default=None,
                    help="HF model id for REAL weights (e.g. microsoft/deberta-v3-large); "
                         "default: the synthetic self-test fixture (no download)")
    ap.add_argument("--batches", type=int, nargs="*", default=list(_DEFAULT_BATCHES),
                    help=f"batch rungs from {shape_buckets.ENCODE_BATCH_BUCKETS}")
    ap.add_argument("--seq-buckets", type=int, nargs="*", default=list(_DEFAULT_SEQ_BUCKETS),
                    help=f"seq rungs from {shape_buckets.ENCODE_LEN_BUCKETS}")
    ap.add_argument("--repeats", type=int, default=10, help="warm timed forwards per cell")
    ap.add_argument("--warmup", type=int, default=2, help="compile+warmup forwards (discarded)")
    ap.add_argument("--seed", type=int, default=0, help="corpus/fixture seed (reproducible)")
    ap.add_argument("--jsonl", default=None, help="optional local JSONL sink path")
    ap.add_argument("--self-test", action="store_true",
                    help="run the end-to-end harness self-proof and exit nonzero on failure")
    args = ap.parse_args(argv)

    if args.self_test:
        recs = self_test()
        print(format_table(recs))
        print("\n" + status_legend())
        print("\nSELF-TEST PASS: exact_reference round-trips (fidelity-vs-self==0), "
              "watchdog flags the broken variant, all stubs are not_implemented.")
        return 0

    load_all()
    names = args.variants if args.variants else portfolio_names()
    recs = run_bench(names, model=args.model, batches=tuple(args.batches),
                     seq_buckets=tuple(args.seq_buckets), repeats=args.repeats,
                     warmup=args.warmup, seed=args.seed, jsonl=args.jsonl)
    print(format_table(recs))
    print("\n" + status_legend())
    return 0


if __name__ == "__main__":
    sys.exit(main())
