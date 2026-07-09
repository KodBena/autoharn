#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T13:52:33Z
#   last-change: 2026-07-09T13:57:12Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py — both-polarity proof for hooks/pretooluse_change_gate.py's SUBJECT_ROOT
fail-closed fix (BACKLOG "Run-2 integrity finding", 2026-07-09).

Run 2's actual defect: `.claude/settings.json` baked an absolute GATE_SUBJECT_ROOT/E13_SUBJECT_ROOT
env var that pointed at the project's PRE-MOVE path. Every Write/Edit/NotebookEdit call for that
session's entire life hit `is_governed()`, which can only ever match a real path under SUBJECT_ROOT
-- so a dangling SUBJECT_ROOT made it return False for EVERY edit, silently governing nothing. The
fix: detect "SUBJECT_ROOT was explicitly configured via env but does not exist on disk" and DENY
those tool calls with teach-text, instead of falling through to the silent `is_governed() -> False`
path.

Each case subdirectory holds:
    stdin.json          — the hook-input JSON fed to the script's stdin
    env.json             — {"set": {VAR: value, ...}, "unset": [VAR, ...]} applied over os.environ
    expected_exit.txt     — the exit code the hook must produce
    expect.txt            — one assertion per line: "+substring" (must appear in combined stdout+
                             stderr) or "-substring" (must NOT appear); blank/absent file = no check

Usage: python3 seen-red/change-gate-subject-root/run_fixtures.py
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
HOOK = REPO / "hooks" / "pretooluse_change_gate.py"


def case_dirs() -> list[Path]:
    # Only real fixture dirs (identified by carrying stdin.json) -- never an incidental
    # __pycache__/etc. that tooling (py_compile, an editor) might drop alongside them.
    return sorted(p for p in HERE.iterdir() if p.is_dir() and (p / "stdin.json").exists())


def build_env(case: Path) -> dict[str, str]:
    env = dict(os.environ)
    spec_path = case / "env.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {}
    for var in spec.get("unset", []):
        env.pop(var, None)
    for var, val in spec.get("set", {}).items():
        env[var] = val
    return env


def run_case(case: Path) -> tuple[bool, str]:
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
        lines.append(f"  ^^ FAIL exit code")
    for a in assertions:
        a = a.strip()
        if not a:
            continue
        polarity, substr = a[0], a[1:]
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
