#!/usr/bin/env python3
"""run_fixtures.py — both-polarity proof for hooks/stamp_intercept.py's SCRATCH-WORLD SCOPE
NARROWING fix (BACKLOG "stamp-intercept-scratch-world-leakage", ledger rows 1159/1162/1163,
2026-08-06).

THE DEFECT (row 1159, witnessed by three builders this session): the hook injects the CALLING
session's PGOPTIONS stamp into every Bash-tool command whenever cwd carries a deployment.json,
EXPORTED so the whole subprocess tree inherits it (module docstring, "export, not a prefix" --
needed so a psql call hidden inside a generated script or a wrapper still gets stamped). The same
mechanism means a fixture/scaffold that births/talks to a SCRATCH world from inside that command
inherits THIS session's stamp too -- computed against THIS session's own secret -- and the
kernel's set_stamp trigger (kernel/lineage/s17-stamp-mechanism.sql) REFUSES outright (all four
GUCs present, HMAC does not match), rather than degrading quietly the way an ABSENT stamp would.

THE FIX (module docstring, SCRATCH-WORLD SCOPE NARROWING): a narrow, disclosed, best-effort
recognizer (`_looks_like_scratch_fixture_invocation`) for the ONE self-contained shape actually
witnessed causing the leakage -- a Bash command that, in its ENTIRETY, does nothing but launch a
seen-red/ fixture script. A miss falls through to the unconditional injection (no regression); a
hit suppresses an injection that would have been wrong for that command anyway. This suite proves
BOTH polarities: the shapes that are now suppressed (a-d), and the shapes that correctly remain
UNCHANGED -- a mixed/chained command (e) and an ordinary own-world command (f) -- so the narrowing
can never be mistaken for a general "skip injection near seen-red/" rule.

Each case subdirectory holds the same shape as the sibling seen-red/stamp-intercept-secret/ suite
(stdin.json, env.json, expected_exit.txt, expect.txt, setup.sh) -- driven by the identical harness
below (deliberately NOT importing that suite's run_fixtures.py -- each seen-red/ suite is
self-contained per house convention, no cross-suite coupling).

Usage: python3 seen-red/stamp-intercept-scratch-scope/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "stamp_intercept.py"


def case_dirs() -> list[Path]:
    return sorted(p for p in HERE.iterdir() if p.is_dir() and (p / "stdin.json").exists())


def build_env(case: Path) -> dict[str, str]:
    env = dict(os.environ)
    spec_path = case / "env.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {}
    for var in spec.get("unset", []):
        env.pop(var, None)
    for var, val in spec.get("set", {}).items():
        env[var] = val.replace("__CASE__", str(case))
    return env


_TRACKED_NAMES = {"stdin.json", "env.json", "expected_exit.txt", "expect.txt", "setup.sh"}


def run_setup(case: Path) -> None:
    setup = case / "setup.sh"
    if setup.exists():
        subprocess.run(["bash", str(setup)], cwd=str(case), check=True,
                        capture_output=True, text=True)


def clean_scratch(case: Path) -> None:
    for p in case.iterdir():
        if p.is_file() and p.name not in _TRACKED_NAMES:
            p.unlink()


def run_case(case: Path) -> tuple[bool, str]:
    try:
        run_setup(case)
        return _run_case_inner(case)
    finally:
        clean_scratch(case)


def _run_case_inner(case: Path) -> tuple[bool, str]:
    stdin_text = (case / "stdin.json").read_text(encoding="utf-8")
    expected = int((case / "expected_exit.txt").read_text(encoding="utf-8").strip())
    expect_file = case / "expect.txt"
    assertions = expect_file.read_text(encoding="utf-8").splitlines() if expect_file.exists() else []

    result = subprocess.run(
        [sys.executable, str(HOOK)], input=stdin_text, capture_output=True, text=True,
        env=build_env(case),
    )
    combined = result.stdout + result.stderr
    lines = [f"exit={result.returncode} (expect {expected})"]
    ok = result.returncode == expected
    if not ok:
        lines.append("  ^^ FAIL exit code")
    for a in assertions:
        a = a.strip()
        if not a:
            continue
        polarity, substr = a[0], a[1:].replace("__CASE__", str(case))
        present = substr in combined
        good = present if polarity == "+" else not present
        lines.append(f"  [{'ok' if good else 'FAIL'}] {a}")
        ok = ok and good
    lines.append(f"  stdout: {result.stdout.strip()[:220]}")
    return ok, "\n".join(lines)


def main() -> int:
    failures: list[str] = []
    for case in case_dirs():
        print(f"=== {case.name} ===")
        ok, report = run_case(case)
        print(report)
        print()
        if not ok:
            failures.append(case.name)
    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print(f"run_fixtures: all {len(case_dirs())} case(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
