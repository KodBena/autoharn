#!/usr/bin/env python3
"""run_fixtures.py — both-polarity proof for hooks/stamp_intercept.py's STAMP_SECRET fail-closed
fix (BACKLOG "Run-2 integrity finding", 2026-07-09).

Runs 1 and 2's actual defect: STAMP_SECRET was configured pointing at a file that no longer
existed (run 2: a moved project directory left a stale path baked into `.claude/settings.json`'s
hook command). The hook's SAFETY contract ("any error -> allow the command unchanged") meant a
matched ledger write (a `psql`/`led` call) passed through UNSTAMPED, silently -- twice witnessed.
The fix: an EXPLICITLY-configured STAMP_SECRET (the env var itself, never a not-yet-armed
deployment.json-derived default -- that stays fail-open by design, see bootstrap/templates/
HOOKS.md.tmpl's "one manual step remains" state) whose file is missing/unreadable/empty now DENIES
the matched command with teach-text quoting the real seed sequence, instead of passing through.

Each case subdirectory holds:
    stdin.json          — the hook-input JSON fed to the script's stdin
    env.json             — {"set": {VAR: value, ...}, "unset": [VAR, ...]} applied over os.environ
    expected_exit.txt     — the exit code the hook must produce
    expect.txt            — one assertion per line: "+substring" (must appear in combined stdout+
                             stderr) or "-substring" (must NOT appear); blank/absent file = no check
    setup.sh              — OPTIONAL: shell snippet run before the case (e.g. writing a scratch
                             secret file into this case's own directory)

Usage: python3 seen-red/stamp-intercept-secret/run_fixtures.py
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
HOOK = REPO / "hooks" / "stamp_intercept.py"


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
        env[var] = val.replace("__CASE__", str(case))
    return env


# fixture files a case dir carries in git; anything else `setup.sh` creates (e.g. a scratch
# secret file, generated fresh each run) is scratch and removed in the `finally` below so the
# repo tree stays clean between runs -- only these named files are ever staged/committed.
_TRACKED_NAMES = {"stdin.json", "env.json", "expected_exit.txt", "expect.txt", "setup.sh"}


def run_setup(case: Path) -> None:
    setup = case / "setup.sh"
    if setup.exists():
        subprocess.run(["bash", str(setup)], cwd=str(case), check=True,
                        capture_output=True, text=True)


def clean_scratch(case: Path) -> None:
    """Remove any file `setup.sh` generated in this case dir (scratch secrets, etc.) so re-running
    the fixture never leaves residue for git to notice."""
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
        lines.append(f"  ^^ FAIL exit code")
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
