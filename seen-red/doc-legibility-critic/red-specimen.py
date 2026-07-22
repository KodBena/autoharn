#!/usr/bin/env python3
"""Seen-red specimen for hooks/doc_legibility_critic.py (the zero-context-reader critic,
design/ADR-DRAFT-documentation-discipline.md instance bindings; gates/fixture_census.py
REGISTRY entry "doc-legibility-critic"). Proves, on live subprocess runs of the real hook:

  CASE 1 (RED)   — apparatus mode "observe": a Write of a known-defective .md passage (the
                   BRIEF's own staccato shape) fires a structured warning via
                   hookSpecificOutput.additionalContext, journals it, and STILL exits 0
                   (observer mode: the red is the warning, never a block).
  CASE 2 (GREEN) — same wiring, a clean grounded passage: silent, exit 0.
  CASE 3 (OFF)   — no apparatus.json at all (the default state of every world): the hook
                   exits 0 SILENTLY WITHOUT SPENDING A CLASSIFIER CALL — witnessed by
                   pointing classifier_command at a poison path via apparatus in cases 1-2
                   only; in case 3 there is no apparatus, and the hook must return before
                   any subprocess (asserted by wall-clock: an off-exit is near-instant).

This is a LIVE fixture: cases 1-2 shell out to the real `claude -p` haiku classifier (same
as the demurral-detector specimen — an acceptance-time cost, not a per-commit tax).
DOC_CRITIC_TIMEOUT_S is raised for a real verdict, per the demurral precedent's measured
~7-20s latency note.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "doc_legibility_critic.py"

DEFECTIVE_MD = (
    "## 3. The operationalizable log-register\n\n"
    "The core deliverable. Each row is an entry the AI collaborator MUST write. "
    "`Trigger` = the event that obliges the entry. `Integrity` = the invariant(s) from "
    "§2 it satisfies. Per the harness DB claim-ledger and the WHY-ledger / R-WHY / R-QTY "
    "work, all entries are append-only.\n"
)

CLEAN_MD = (
    "# WALKTHROUGH — a decision ledger for your own project\n\n"
    "Ten minutes: stand up an append-only decision ledger for a project of yours, file a "
    "decision, read it back, tear it down. What you get, concretely: decisions recorded as "
    "rows that cannot be edited or deleted (append-only, trigger-enforced), attributed to "
    "the connecting role (not self-declared), superseded by appending — never by "
    "rewriting.\n"
)


def payload(cwd: str, text: str) -> str:
    return json.dumps({
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "cwd": cwd,
        "tool_input": {"file_path": os.path.join(cwd, "probe.md"), "content": text},
    })


def run_hook(stdin: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("GATE_SUBJECT_ROOT", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, str(HOOK)], input=stdin,
                          capture_output=True, text=True, env=env, cwd=REPO)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        # Cases 1-2: a world with the mechanism switched to "observe".
        (Path(td) / ".claude").mkdir()
        (Path(td) / ".claude" / "apparatus.json").write_text(json.dumps({
            "mechanisms": {"doc_legibility_critic": {"mode": "observe", "timeout_s": 90}}
        }), encoding="utf-8")

        cp = run_hook(payload(td, DEFECTIVE_MD), {"DOC_CRITIC_TIMEOUT_S": "90"})
        warned = "doc-legibility-critic" in cp.stdout and "shape=" in cp.stdout
        journal = Path(td) / ".claude" / "logs" / "doc_legibility_critic.journal.jsonl"
        journaled = journal.exists() and "DEFECT" in journal.read_text(encoding="utf-8")
        print(f"CASE 1 (defective write, observe mode): exit={cp.returncode} "
              f"warned={warned} journaled_positive={journaled}")
        if cp.returncode != 0:
            failures.append("case 1: observer mode must exit 0 even on a red verdict")
        if not warned or not journaled:
            failures.append(f"case 1: expected a structured warning + journal entry; "
                            f"stdout was: {cp.stdout[:400]!r} stderr: {cp.stderr[:200]!r}")
        else:
            print("--- the emitted warning (the critic's red, verbatim) ---")
            print(cp.stdout.strip()[:900])
            print("--- end warning ---")

        cp2 = run_hook(payload(td, CLEAN_MD), {"DOC_CRITIC_TIMEOUT_S": "90"})
        print(f"CASE 2 (clean write, observe mode): exit={cp2.returncode} "
              f"silent={not cp2.stdout.strip()}")
        if cp2.returncode != 0:
            failures.append("case 2: expected exit 0")
        if cp2.stdout.strip():
            failures.append(f"case 2: expected silence on a clean passage; got "
                            f"{cp2.stdout[:300]!r}")

    with tempfile.TemporaryDirectory() as td_off:
        # Case 3: no apparatus.json anywhere -> default OFF, no subprocess, near-instant.
        t0 = time.monotonic()
        cp3 = run_hook(payload(td_off, DEFECTIVE_MD))
        dt = time.monotonic() - t0
        print(f"CASE 3 (no apparatus.json -> default OFF): exit={cp3.returncode} "
              f"silent={not cp3.stdout.strip()} elapsed={dt:.2f}s")
        if cp3.returncode != 0 or cp3.stdout.strip():
            failures.append("case 3: default-off must be silent exit 0")
        if dt > 3.0:
            failures.append(f"case 3: default-off took {dt:.2f}s — it must return before "
                            f"any classifier subprocess")

    if failures:
        print("doc-legibility-critic red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("doc-legibility-critic red-specimen: all three cases behaved as designed — a "
          "structured observer-grade warning on the defective write, silence on the clean "
          "write, and a no-cost instant exit when the switchboard is absent (default OFF).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
