#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for hooks/pretooluse_read_observer.py (BACKLOG
"Five-item batch, maintainer-approved 2026-07-11 evening", item 3). No database is involved --
this hook's only side effect is a journal line -- so this fixture is pure filesystem, unlike
the delegation/mutation observer fixtures it otherwise mirrors in shape and stdin-payload
convention.

Real infra, no mocks: a throwaway scratch directory under /tmp, torn down before AND after this
file runs so re-running it never leaves residue. Six cases, run as an independent sequence
(order does not matter here -- unlike delegation_observer, this hook carries no cross-call
state):

  a-observe-default   -- no apparatus.json entry at all (missing-key default) -> mode resolves
                         to "observe" and a real Read of a file lands one journal line: ts (UTC-Z,
                         Z-suffixed), session_id, file_path.
  b-mode-off          -- apparatus.json sets read_observer.mode="off" -> genuinely zero cost: NO
                         journal line at all, even though a real Read just happened.
  c-mode-enforce-downgrade -- apparatus.json sets read_observer.mode="enforce" (NOT YET
                         SANCTIONED for this hook) -> the hook warns loudly on STDERR naming the
                         downgrade, then behaves exactly like "observe": one journal line lands.
  d-non-read-tool     -- tool_name="Write" (a different tool entirely) -> no journal line, no
                         output at all -- this hook only ever reacts to "Read".
  e-unwired           -- no GATE_SUBJECT_ROOT and no `cwd` resolving to a real directory -> the
                         hook exits clean with no journal write (nothing to journal INTO).
  f-multiple-reads-append -- two more real Reads of different files against the SAME wired,
                         observe-mode probe -> the journal now carries exactly 3 lines total
                         (this case's two plus case (a)'s one), each with the right file_path, in
                         append order -- proving the journal accumulates rather than overwrites.

Usage: python3 seen-red/read-observer/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "pretooluse_read_observer.py"

PROBE_DIR = Path("/tmp/.readobsprobe")
JOURNAL_PATH = PROBE_DIR / ".claude" / "logs" / "read_observer.journal.jsonl"


def teardown() -> None:
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def write_apparatus(mechanisms: dict) -> None:
    (PROBE_DIR / ".claude").mkdir(parents=True, exist_ok=True)
    (PROBE_DIR / ".claude" / "apparatus.json").write_text(
        json.dumps({"mechanisms": mechanisms}), encoding="utf-8")


def run_hook(tool_name: str, file_path: str, session_id: str,
             cwd: str | None, env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({
        "hook_event_name": "PreToolUse", "tool_name": tool_name,
        "tool_input": {"file_path": file_path},
        "session_id": session_id, "cwd": cwd or "",
    })
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True, env=env)


def journal_lines() -> list[dict]:
    if not JOURNAL_PATH.exists():
        return []
    return [json.loads(ln) for ln in JOURNAL_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    teardown()
    failures: list[str] = []

    # --- a-observe-default: no apparatus.json at all -----------------------------------------
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    r = run_hook("Read", "/etc/hostname", "sess-a",
                 str(PROBE_DIR), {"GATE_SUBJECT_ROOT": str(PROBE_DIR)})
    lines = journal_lines()
    ok = (r.returncode == 0 and len(lines) == 1
          and lines[0].get("session_id") == "sess-a"
          and lines[0].get("file_path") == "/etc/hostname"
          and isinstance(lines[0].get("ts"), str) and lines[0]["ts"].endswith("Z"))
    check("a-observe-default", ok,
          f"exit={r.returncode} journal_lines={len(lines)} rec={lines[-1] if lines else None}",
          failures)

    # --- b-mode-off: journal gains NO new line ------------------------------------------------
    write_apparatus({"read_observer": {"mode": "off"}})
    before = len(journal_lines())
    r = run_hook("Read", "/etc/hosts", "sess-b",
                 str(PROBE_DIR), {"GATE_SUBJECT_ROOT": str(PROBE_DIR)})
    after = len(journal_lines())
    ok = (r.returncode == 0 and after == before)
    check("b-mode-off", ok, f"exit={r.returncode} before={before} after={after} (expect equal)",
          failures)

    # --- c-mode-enforce-downgrade: warns on stderr, still journals like observe ---------------
    write_apparatus({"read_observer": {"mode": "enforce"}})
    before = len(journal_lines())
    r = run_hook("Read", "/etc/passwd", "sess-c",
                 str(PROBE_DIR), {"GATE_SUBJECT_ROOT": str(PROBE_DIR)})
    after = journal_lines()
    ok = (r.returncode == 0 and len(after) == before + 1
          and "NOT YET SANCTIONED" in r.stderr
          and after[-1].get("file_path") == "/etc/passwd")
    check("c-mode-enforce-downgrade", ok,
          f"exit={r.returncode} stderr_has_downgrade_warning={'NOT YET SANCTIONED' in r.stderr} "
          f"before={before} after={len(after)}", failures)

    # --- d-non-read-tool: a Write call produces nothing ----------------------------------------
    write_apparatus({"read_observer": {"mode": "observe"}})
    before = len(journal_lines())
    r = run_hook("Write", "/tmp/whatever.txt", "sess-d",
                 str(PROBE_DIR), {"GATE_SUBJECT_ROOT": str(PROBE_DIR)})
    after = len(journal_lines())
    ok = (r.returncode == 0 and after == before and r.stdout.strip() == "")
    check("d-non-read-tool", ok,
          f"exit={r.returncode} stdout={r.stdout.strip()!r} before={before} after={after}",
          failures)

    # --- e-unwired: no GATE_SUBJECT_ROOT, no real cwd directory --------------------------------
    before = len(journal_lines())
    r = run_hook("Read", "/etc/hostname", "sess-e", "/nonexistent/nowhere", {})
    after = len(journal_lines())
    ok = (r.returncode == 0 and after == before)
    check("e-unwired", ok, f"exit={r.returncode} before={before} after={after}", failures)

    # --- f-multiple-reads-append: two more real reads land two more lines, in order -----------
    write_apparatus({"read_observer": {"mode": "observe"}})
    before = journal_lines()
    r1 = run_hook("Read", "/tmp/file1.txt", "sess-f1",
                  str(PROBE_DIR), {"GATE_SUBJECT_ROOT": str(PROBE_DIR)})
    r2 = run_hook("Read", "/tmp/file2.txt", "sess-f2",
                  str(PROBE_DIR), {"GATE_SUBJECT_ROOT": str(PROBE_DIR)})
    after = journal_lines()
    ok = (r1.returncode == 0 and r2.returncode == 0
          and len(after) == len(before) + 2
          and after[-2]["file_path"] == "/tmp/file1.txt"
          and after[-1]["file_path"] == "/tmp/file2.txt")
    check("f-multiple-reads-append", ok,
          f"before={len(before)} after={len(after)} last_two="
          f"{[l['file_path'] for l in after[-2:]]}", failures)

    teardown()

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL CASES OK -- read_observer both-polarity proof clean, zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
