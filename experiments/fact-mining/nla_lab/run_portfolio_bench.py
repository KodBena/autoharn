#!/usr/bin/env python
"""run_portfolio_bench — the PROCESS-PER-VARIANT portfolio sweep (host orchestration).

WHY A SUBPROCESS PER VARIANT (the crux — do NOT collapse this to an in-process loop).
`nla_lab.bench` runs ALL variants in ONE Python process. That is fine on the synthetic
CPU fixture, but it OOMs on a REAL-weight sweep for two compounding reasons:

  1. ~5 GB / variant of real deberta-v3-large weights. Loading the warm fixture ONCE and
     keeping every variant's prepped/packed params live in one process stacks those
     footprints — eight variants ≈ tens of GB resident at once.
  2. The XLA compiled-executable cache is PROCESS-GLOBAL and UNBOUNDED. Every distinct
     (variant, batch, seq_bucket) compiles its own executable and they ACCUMULATE for the
     process lifetime — the exact unbounded-cache accumulation we already had to fix by
     BUCKETING in coref_host_shell. Across a real portfolio × the (batch × seq_bucket)
     sweep, the retained executables alone exhaust device memory.

The fix is OS-level isolation: run each variant in a FRESH subprocess so that on exit the
OS reclaims EVERYTHING — the GPU arena, the XLA executable cache, and the host RSS — fully
and unconditionally, before the next variant starts. No in-process teardown is trusted to
be complete; process exit IS the teardown. The psql sink (nla.bench_result) is what makes
this clean: each subprocess writes its rows under the SHARED run_tag and exits; the
assembled run is one queryable table group, no JSONL hand-off between processes.

THE SHARED run_tag. It is generated ONCE here in the parent and passed identically to every
child (never re-derived per subprocess — a per-process timestamp would split one sweep into
N ungroupable singletons). All variants of one sweep therefore land under one run_tag.

RESILIENCE. A variant whose subprocess exits nonzero (e.g. it alone OOMs at a huge bucket)
does NOT abort the sweep — it simply contributes no rows, a clear line is printed, and the
runner continues to the next variant (the same per-variant safety envelope the in-process
bench gives each trial, lifted to the process boundary).

HOST-XOR-DEVICE. This is pure host orchestration (subprocess + stdlib). It authors no
device op; the device work happens inside each child `nla_lab.bench` process.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

# Run-form robustness: support BOTH `python nla_lab/run_portfolio_bench.py ...` (script
# form — sys.path[0] is nla_lab/, so the repo root is NOT importable) AND
# `python -m nla_lab.run_portfolio_bench`. REPO_ROOT (fact-mining/) is the dir that holds
# shape_buckets.py / spans.py and the `nla_lab` package; ensure it is importable here and
# is the child subprocess cwd so `python -m nla_lab.bench` always resolves.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import shape_buckets
from nla_lab.bench import model_tag
from nla_lab.registry import load_all, portfolio_names


def _shared_run_tag(model: str | None, weights_npz: str | None, label: str | None) -> str:
    """ONE run_tag for the whole sweep, generated in the parent (NOT per child). Combines
    the weight-source model tag, an optional caller label, and a single parent-side
    timestamp so distinct sweeps are distinct queryable groups."""
    parts = [model_tag(model, weights_npz)]
    if label:
        parts.append(label)
    parts.append(time.strftime("%Y%m%dT%H%M%S"))
    return ":".join(parts)


def _child_cmd(variant: str, run_tag: str, args: argparse.Namespace) -> list[str]:
    """The exact `python -m nla_lab.bench` argv for ONE variant's FRESH subprocess: just
    this one variant, --psql, the SHARED --run-tag, the --dsn, and the weight source +
    sweep knobs threaded through unchanged."""
    cmd = [sys.executable, "-m", "nla_lab.bench",
           "--variants", variant,
           "--psql", "--run-tag", run_tag, "--dsn", args.dsn,
           "--batches", *[str(b) for b in args.batches],
           "--seq-buckets", *[str(s) for s in args.seq_buckets],
           "--repeats", str(args.repeats),
           "--warmup", str(args.warmup),
           "--seed", str(args.seed)]
    if args.weights_npz is not None:
        cmd += ["--weights-npz", args.weights_npz]
    elif args.model is not None:
        cmd += ["--model", args.model]
    return cmd


def _child_env(mem_fraction: float | None) -> dict[str, str]:
    """The subprocess env with the XLA arena sized to USE the free VRAM. jax PREALLOCATES only
    0.75 of TOTAL device memory by default, so a large shape can OOM (RESOURCE_EXHAUSTED) while
    VRAM is physically free — the arena, not the card, is the limit. By default we turn
    preallocation OFF so the bench grows on demand into whatever is free; --mem-fraction sets a
    fixed preallocated arena instead (e.g. 0.3 to share the card with a running daemon)."""
    env = dict(os.environ)
    if mem_fraction is None:
        env["XLA_PYTHON_CLIENT_PREALLOCATE"] = "false"
        env.pop("XLA_PYTHON_CLIENT_MEM_FRACTION", None)
    else:
        env["XLA_PYTHON_CLIENT_PREALLOCATE"] = "true"
        env["XLA_PYTHON_CLIENT_MEM_FRACTION"] = repr(float(mem_fraction))
    return env


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="process-per-variant portfolio sweep (real-weight safe; psql sink)")
    ap.add_argument("--variants", nargs="*", default=None,
                    help="variant names (default: the full portfolio)")
    ap.add_argument("--model", default=None,
                    help="HF model id for REAL weights; mutually exclusive with --weights-npz")
    ap.add_argument("--weights-npz", default=None,
                    help="path to the REAL maverick deberta encoder export "
                         "(fixtures/deberta_maverick.npz) — the real-weight target. "
                         "Threaded to EVERY variant subprocess.")
    ap.add_argument("--batches", type=int, nargs="*", default=[1, 2],
                    help=f"batch rungs from {shape_buckets.ENCODE_BATCH_BUCKETS}")
    ap.add_argument("--seq-buckets", type=int, nargs="*", default=[64, 128],
                    help=f"seq rungs from {shape_buckets.ENCODE_LEN_BUCKETS}")
    ap.add_argument("--repeats", type=int, default=10, help="warm timed forwards per cell")
    ap.add_argument("--warmup", type=int, default=2, help="compile+warmup forwards (discarded)")
    ap.add_argument("--seed", type=int, default=0, help="corpus/fixture seed (reproducible)")
    ap.add_argument("--dsn", default=None,
                    help="harness DB DSN (default: spans.DEFAULT_DSN, HARNESS_DSN-overridable)")
    ap.add_argument("--label", default=None,
                    help="optional sweep label folded into the shared run_tag")
    ap.add_argument("--mem-fraction", type=float, default=None,
                    help="XLA_PYTHON_CLIENT_MEM_FRACTION per bench subprocess (fraction of "
                         "TOTAL device memory to PREALLOCATE). DEFAULT (unset): preallocation "
                         "OFF (XLA_PYTHON_CLIENT_PREALLOCATE=false) so the bench grows into the "
                         "FREE VRAM on demand — uses all that's free, not jax's 0.75-of-total "
                         "default arena (which OOMs a large shape while VRAM is physically "
                         "free). Set e.g. 0.3 to cap the arena and share the card with a daemon.")
    args = ap.parse_args(argv)

    if args.model is not None and args.weights_npz is not None:
        ap.error("--model and --weights-npz are mutually exclusive (a run has ONE weight "
                 "source). Pass only one.")
    # default the DSN to the ONE home here, so the child argv carries an explicit value.
    if args.dsn is None:
        from spans import DEFAULT_DSN
        args.dsn = DEFAULT_DSN

    if args.variants:
        variants = list(args.variants)
    else:
        load_all()
        variants = portfolio_names()

    run_tag = _shared_run_tag(args.model, args.weights_npz, args.label)
    mtag = model_tag(args.model, args.weights_npz)
    print(f"=== portfolio sweep: {len(variants)} variant(s), one FRESH subprocess each "
          f"(OS reclaims GPU arena + XLA cache + RSS between variants) ===")
    arena = ("preallocate=OFF (grow into free VRAM)" if args.mem_fraction is None
             else f"mem_fraction={args.mem_fraction} (fixed preallocated arena)")
    print(f"=== model={mtag!r} | run_tag={run_tag!r} | dsn={args.dsn!r} | arena: {arena} ===")
    print(f"=== variants: {', '.join(variants)} ===\n")

    failed: list[str] = []
    for i, variant in enumerate(variants, 1):
        cmd = _child_cmd(variant, run_tag, args)
        print(f"--- [{i}/{len(variants)}] variant {variant}: {' '.join(cmd)} ---",
              flush=True)
        # FRESH SUBPROCESS per variant: the OS reclaims ALL of this variant's device +
        # host memory on exit, before the next variant starts. stdout/stderr INHERIT the
        # parent's streams so the child's progress streams live to the maintainer. We do
        # NOT check=True: a nonzero child must NOT abort the sweep.
        proc = subprocess.run(cmd, cwd=REPO_ROOT, env=_child_env(args.mem_fraction))  # noqa: S603 — fixed argv, no shell
        if proc.returncode != 0:
            failed.append(variant)
            print(f"!!! variant {variant} exited nonzero (code {proc.returncode}) — it "
                  f"contributes no rows; continuing to the next variant.\n", flush=True)
        else:
            print(f"--- variant {variant} done ---\n", flush=True)

    print(f"=== sweep complete: {len(variants) - len(failed)}/{len(variants)} variant(s) "
          f"wrote rows under run_tag={run_tag!r}"
          + (f"; FAILED (no rows): {', '.join(failed)}" if failed else "") + " ===")
    print("\nRead the assembled run:\n")
    print(
        'psql -h 192.168.122.1 -d harness -c "'
        "SELECT variant,batch,seq_bucket,status,"
        "round(lat_p50_ms::numeric,2) ms,round(rows_per_s::numeric,1) rps,"
        "fidelity_max_abs,round(est_peak_device_bytes/1048576.0,2) devmib "
        "FROM nla.bench_result "
        f"WHERE run_tag='{run_tag}' "
        'ORDER BY variant,seq_bucket,batch;"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
