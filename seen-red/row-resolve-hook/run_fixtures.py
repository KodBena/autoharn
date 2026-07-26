#!/usr/bin/env python3
"""run_fixtures.py — both-polarity proof for hooks/userpromptsubmit_row_resolve.py (maintainer
commission 2026-07-26: a zero-LLM-cost `/row <id> [...]` ledger resolver, a UserPromptSubmit
hook that blocks the exact `/row 1325` shape with the row text via `decision: "block"`/`reason`
before it ever reaches the model, and passes every other prompt through untouched).

Each case subdirectory holds the same shape `seen-red/change-gate-subject-root/run_fixtures.py`
already establishes (house precedent, followed verbatim here): `stdin.json` (the hook-input
JSON fed to the script's stdin), an optional `env.json` (`{"set": {...}, "unset": [...]}`
layered over `os.environ`, with `__CASE__` substituted for this case dir's own absolute path),
`expected_exit.txt` (the exit code the hook must produce — always 0 here, since this hook's own
VERIFIED CONTRACT deliberately never uses exit 2, module docstring), and `expect.txt` (one
assertion per line: `+substring` must appear in combined stdout+stderr, `-substring` must NOT).

No `setup.sh`/`teardown.sh` here (unlike the change-gate fixture this file's shape is copied
from) — this hook never touches a real database or a served boundary; every case points
`ROW_RESOLVE_AUTOHARN_BIN` at `mock_row_cli.py` alongside this file (or, for the
CLI-unreachable case, at a path that does not exist at all) rather than the real
`./autoharn`, so this suite proves the hook's OWN regex/budget/formatting/failure-honesty logic
without a live deployment.json anywhere in the loop (design constraint 1's read-only-CLI-only
posture is a property of the SHIPPED hook, not something this fixture needs a live service to
also exercise).

Usage: python3 seen-red/row-resolve-hook/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "userpromptsubmit_row_resolve.py"


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


def run_case(case: Path) -> tuple[bool, str]:
    stdin_text = (case / "stdin.json").read_text(encoding="utf-8")
    expected = int((case / "expected_exit.txt").read_text(encoding="utf-8").strip())
    expect_file = case / "expect.txt"
    assertions = expect_file.read_text(encoding="utf-8").splitlines() if expect_file.exists() else []

    result = subprocess.run(
        [sys.executable, str(HOOK)], input=stdin_text, capture_output=True, text=True,
        env=build_env(case), timeout=30,
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
        polarity, substr = a[0], a[1:]
        present = substr in combined
        good = present if polarity == "+" else not present
        lines.append(f"  [{'ok' if good else 'FAIL'}] {a}")
        ok = ok and good
    lines.append(f"  stdout: {result.stdout.strip()[:300]}")
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
