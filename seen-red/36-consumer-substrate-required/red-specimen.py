#!/usr/bin/env python3
"""Seen-red specimen for the consumer-substrate-required gate (forecloses finding 36). Reproduces the
PRE-FIX consumer: close_manifest.py resolved the acts `--fenced` dir and row_performed_by `--session-dir`
from HARDCODED e15-pinned module-globals (ACTS_FENCED=~/nk4-build, PERF_SESSION_DIR=<e15 subject dir>), so
a bare `close_manifest.py e16 --mode close` measured e15's substrate against e16's ledger and every acts/
perf consumer returned a VACUOUS 0/all-unbound reported as OK — a silent wrong-substrate pass (run B,
close-e16-post-disposition.txt). The naive consumers below reproduce that shape: OK regardless of whether
the target's substrate is registered. The gate's check() (which now requires REQUIRED-ABSENT at close on an
unregistered substrate) then flags it. Banked as red.txt. Run from anywhere."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path("/home/bork/w/vdc/1/epistemic-operator/instruments")))
import close_manifest as cm  # noqa: E402
from verify_substrate_required import check  # noqa: E402  (reads cm.run_*_consumers at CALL time)


def _naive_fixed_default_acts(target: str, mode: str):
    """The finding-36 defect: read a hardcoded module-global default (e15's fence) and report OK/vacuous
    regardless of the target — the silent wrong-substrate pass."""
    return [(c, "OK", "0 finding(s): (none) [vacuous — e15 default fence read against this target's ledger]")
            for c in cm.ACTS_CONSUMERS]


def _naive_fixed_default_perf(target: str, mode: str):
    return [(c, "OK", "0 finding(s): (none) [vacuous — e15 default session dir read against this run]")
            for c in cm.PERF_CONSUMERS]


def main() -> int:
    orig_acts = cm.run_acts_consumers
    orig_perf = cm.run_perf_consumers
    cm.run_acts_consumers = _naive_fixed_default_acts
    cm.run_perf_consumers = _naive_fixed_default_perf
    try:
        bad = check()
    finally:
        cm.run_acts_consumers = orig_acts
        cm.run_perf_consumers = orig_perf
    if not bad:
        print("SPECIMEN INERT — the hardcoded-default consumer did not trip the guard (unexpected).")
        return 1
    for b in bad:
        print(f"SUBSTRATE VACUOUS-PASS: {b}")
    print(f"# consumer-substrate-required FAIL — {len(bad)} defect(s): a consumer measured an unregistered "
          f"substrate instead of refusing it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
