#!/usr/bin/env python3
"""verify_contemporaneity_degrade — the standing fixture for contemporaneity's degrade contract
(forecloses finding 12: a MANDATORY gate that could-not-test a target once exited 0-WITH-OUTPUT, so a
downstream manifest read "could not test" as "tested clean" — the ADR-0015 R4 violation, the finding-3/
F49 shape). The fix gave the degrade path a DISTINCT exit code (3) so a manifest renders it N/A, never
OK. This pins that: an UNREGISTERED target must exit 3 (declared N/A), not 0 (clean) and not crash.

Registered close/lint line id: `contemporaneity-degrade`. Lazy imports banned.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CONTEMP = Path(__file__).resolve().parent / "contemporaneity.py"


def run(target: str) -> tuple[int, str]:
    cp = subprocess.run([sys.executable, str(CONTEMP), target], capture_output=True, text=True, timeout=60)
    return cp.returncode, cp.stdout + cp.stderr


def main() -> int:
    code, out = run("__unregistered_synthetic_target__")
    bad = []
    if code != 3:
        bad.append(f"an unregistered (N/A) target exited {code}, expected 3 (N/A distinct from clean/error)")
    if "N/A" not in out:
        bad.append("the N/A declaration is not VISIBLE in the output")
    for b in bad:
        print(f"CONTEMPORANEITY DEGRADE WRONG: {b}")
    if bad:
        print(f"# contemporaneity-degrade FAIL — {len(bad)} defect(s): could-not-test is not distinct "
              f"from tested-clean.")
        return 1
    print("# contemporaneity-degrade PASS — an unregistered target exits 3 (N/A), declared and visible; "
          "a manifest renders N/A, never OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
