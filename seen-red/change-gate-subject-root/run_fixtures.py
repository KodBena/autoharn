#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T13:52:33Z
#   last-change: 2026-07-10T19:31:39Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py — both-polarity proof for hooks/pretooluse_change_gate.py's SUBJECT_ROOT
fail-closed fix (BACKLOG "Run-2 integrity finding", 2026-07-09) AND the permit-to-work fix
(BACKLOG "Run-5 forensics", 2026-07-10).

Run 2's actual defect: `.claude/settings.json` baked an absolute GATE_SUBJECT_ROOT/E13_SUBJECT_ROOT
env var that pointed at the project's PRE-MOVE path. Every Write/Edit/NotebookEdit call for that
session's entire life hit `is_governed()`, which can only ever match a real path under SUBJECT_ROOT
-- so a dangling SUBJECT_ROOT made it return False for EVERY edit, silently governing nothing. The
fix: detect "SUBJECT_ROOT was explicitly configured via env but does not exist on disk" and DENY
those tool calls with teach-text, instead of falling through to the silent `is_governed() -> False`
path.

Run 5's forensic pass found the ledger is a retroactive diary, not a permit log (8m23s of witnessed
work landed as 19 ledger rows 89.4s later). The fix: a Write/Edit under a WIRED subject root whose
ledger schema carries the s22 work-item layer is denied unless a work item is OPEN and CLAIMED. The
f/g/h cases below exercise this against a REAL throwaway schema in the toy db (192.168.122.1) --
setup.sh applies kernel/lineage DDL and seeds ledger rows; teardown.sh drops the scratch schema/
role after, so re-running this file never leaves DB residue (mirrors kernel/fixtures/
s22_work_item_fixture.py's own scratch-schema-per-probe convention).

Each case subdirectory holds:
    stdin.json          — the hook-input JSON fed to the script's stdin
    env.json             — {"set": {VAR: value, ...}, "unset": [VAR, ...]} applied over os.environ
    expected_exit.txt     — the exit code the hook must produce
    expect.txt            — one assertion per line: "+substring" (must appear in combined stdout+
                             stderr) or "-substring" (must NOT appear); blank/absent file = no check
    setup.sh              — OPTIONAL: shell snippet run before the case (e.g. applying lineage DDL
                             to a scratch schema, seeding ledger rows)
    teardown.sh           — OPTIONAL: shell snippet run after the case, success or failure (e.g.
                             dropping the scratch schema/role setup.sh created) -- so this file
                             stays re-runnable with zero DB residue between runs

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

# fixture files a case dir carries in git; anything else `setup.sh` creates (e.g. the hook's own
# scratch GATE_STATE/GATE_JOURNAL files, generated fresh each run) is scratch and removed in the
# `finally` below so the repo tree stays clean between runs -- only these named files are ever
# staged/committed (mirrors seen-red/stamp-intercept-secret/run_fixtures.py's own convention).
_TRACKED_NAMES = {"stdin.json", "env.json", "expected_exit.txt", "expect.txt", "setup.sh",
                  "teardown.sh"}


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


def run_setup(case: Path) -> None:
    setup = case / "setup.sh"
    if not setup.exists():
        return
    cp = subprocess.run(["bash", str(setup)], cwd=str(case), capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(f"setup.sh failed ({cp.returncode}): {(cp.stdout + cp.stderr)[-800:]}")


def run_teardown(case: Path) -> None:
    teardown = case / "teardown.sh"
    if teardown.exists():
        # Best-effort: a teardown failure must never mask the case's own pass/fail result, and
        # must never leave a later case unable to run (DB residue) -- log to stderr, don't raise.
        cp = subprocess.run(["bash", str(teardown)], cwd=str(case), capture_output=True, text=True)
        if cp.returncode != 0:
            print(f"  (teardown.sh for {case.name} exited {cp.returncode}: "
                  f"{(cp.stdout + cp.stderr).strip()[:300]})", file=sys.stderr)


def clean_scratch(case: Path) -> None:
    """Remove any file `setup.sh` (or the hook itself, e.g. GATE_STATE/GATE_JOURNAL) generated in
    this case dir, so re-running the fixture never leaves residue for git to notice."""
    for p in case.iterdir():
        if p.is_file() and p.name not in _TRACKED_NAMES:
            p.unlink()


def run_case(case: Path) -> tuple[bool, str]:
    try:
        try:
            run_setup(case)
        except Exception as e:  # noqa: BLE001 — a setup failure is a case FAILURE, not a crash
            return False, f"  ^^ FAIL setup.sh: {e}"
        return _run_case_inner(case)
    finally:
        # teardown.sh runs even on a setup.sh failure (partial schema/role left standing) — a
        # broken setup must never skip cleanup, or the NEXT run inherits its residue.
        run_teardown(case)
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
