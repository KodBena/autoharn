#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T13:34:51Z
#   last-change: 2026-07-09T13:34:51Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py — executes instruments/conformance_check.py on every fixture
pair under this directory and asserts the expected exit code.

Each case is a subdirectory containing:
    commission.json     — the ratified scope
    report.json          — the executor's claim
    expected_exit.txt    — the single digit exit code the checker must produce
        (0 CONFORMANT / 1 CONFORMANT_WITH_DEFERRALS / 2 NONCONFORMANT)

Covers design/CONFORMANCE-INSTRUMENT.md's acceptance cases (a)-(e) plus one
EXTRA (f) demonstrating the OPERATOR-CHECK-never-silent-pass boundary for a
witness_type this checker cannot reach mechanically.

Usage: python3 seen-red/conformance_check/run_fixtures.py
Exit 0 if every case matches its expected exit code; 1 otherwise.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CHECKER = REPO / "instruments" / "conformance_check.py"


def case_dirs() -> list[Path]:
    return sorted(p for p in HERE.iterdir() if p.is_dir())


def main() -> int:
    failures: list[str] = []
    for case in case_dirs():
        commission = case / "commission.json"
        report = case / "report.json"
        expected_file = case / "expected_exit.txt"
        if not (commission.exists() and report.exists() and expected_file.exists()):
            failures.append(f"{case.name}: missing commission.json/report.json/expected_exit.txt")
            continue
        expected = int(expected_file.read_text(encoding="utf-8").strip())
        result = subprocess.run(
            [sys.executable, str(CHECKER), str(commission), str(report), "--repo", str(REPO)],
            capture_output=True, text=True,
        )
        print(f"=== {case.name} (expect exit {expected}) ===")
        print(result.stdout.rstrip())
        if result.returncode != expected:
            failures.append(
                f"{case.name}: expected exit {expected}, got {result.returncode}"
            )
            print(f"  ^^ FAIL (got exit {result.returncode})")
        else:
            print(f"  ^^ PASS (exit {result.returncode})")
        print()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S):")
        for f in failures:
            print(f"  !! {f}")
        return 1
    print(f"run_fixtures: all {len(case_dirs())} fixture(s) matched their expected exit code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
