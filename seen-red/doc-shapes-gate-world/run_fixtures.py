#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for hooks/pretooluse_doc_shapes_gate.py (the
world-side, live-write-time transport of gates/doc_shapes.py; BACKLOG "ADR-0017 A:B:C
attestation loop" entry, orchestrator extension "leverage the mandatory documentation step for
run11"). Every case drives the REAL hook as a subprocess over stdin JSON, against a throwaway
scratch "world" directory (never against this repo's own tree, so a deliberately-defective
fixture document never trips this repo's own gates):

  ENFORCE-RED    -- mode=enforce, a defective Write: hook DENIES (permissionDecision=deny),
                     naming both doc_shapes.py checks, exit 2.
  ENFORCE-GREEN  -- mode=enforce, a clean Write: silent ALLOW (no stdout), exit 0.
  OBSERVE-WARN   -- mode=observe, the identical defective Write: ALLOWS but carries the same
                     message as a loud additionalContext warning, exit 0.
  OFF-SILENT     -- mode=off: silent ALLOW regardless of content, exit 0.
  DEFAULT-OBSERVE-- apparatus.json ABSENT entirely: behaves as observe (the documented default,
                     never off and never enforce) -- pins the "observer-first, not costed-off"
                     choice this hook's own module docstring commits to.
  EDIT-RECONSTRUCT-- an Edit (old_string/new_string) against a real on-disk file is
                     reconstructed to its full proposed content before checking -- proves the
                     context-sensitive FRAGMENT check sees the whole file, not an isolated
                     snippet, and that violations name the REAL target path, never the temp
                     file used internally.
  EXERCISED-LIVENESS-- small-follow-ups commission item 2 (BACKLOG "Run-11 first-shift
                     forensics", item 2's own change proposal): every evaluation above that
                     actually ran (ENFORCE-RED, ENFORCE-GREEN, OBSERVE-WARN, DEFAULT-OBSERVE,
                     EDIT-RECONSTRUCT -- five calls) appends one line to
                     doc_shapes_gate.exercised.jsonl with the right outcome
                     (denied/clean/observed_would_deny), while OFF-SILENT -- mode="off",
                     which returns before the check ever runs -- appends NOTHING: proving the
                     counter tracks real evaluations, not merely Write/Edit tool calls.

No network, no DB, no cost: pure-stdlib hook + pure-stdlib gate, throwaway temp world only.
Usage: python3 seen-red/doc-shapes-gate-world/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "pretooluse_doc_shapes_gate.py"

DEFECTIVE_CONTENT = "# A doc\n\nThe core deliverable.\n\nDrafted per HANDOFF open-work item 2.\n"
CLEAN_CONTENT = "# A doc\n\nThis is a full sentence, grounded for a cold reader.\n"


def _run(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True)


def _write_payload(world: Path, doc_name: str, content: str) -> dict:
    return {"tool_name": "Write",
            "tool_input": {"file_path": str(world / doc_name), "content": content},
            "cwd": str(world)}


def _exercised_lines(world: Path) -> list[dict]:
    path = world / ".claude" / "logs" / "doc_shapes_gate.exercised.jsonl"
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _set_mode(world: Path, mode: str | None) -> None:
    apparatus = world / ".claude" / "apparatus.json"
    if mode is None:
        apparatus.unlink(missing_ok=True)
        return
    apparatus.parent.mkdir(parents=True, exist_ok=True)
    apparatus.write_text(json.dumps({"mechanisms": {"doc_shapes_gate": {"mode": mode}}}),
                         encoding="utf-8")


def main() -> int:
    world = Path(tempfile.mkdtemp(prefix="doc-shapes-gate-world-seenred-"))
    failures: list[str] = []
    try:
        # --- ENFORCE-RED -----------------------------------------------------------------
        _set_mode(world, "enforce")
        r = _run(_write_payload(world, "bad.md", DEFECTIVE_CONTENT))
        print(f"CASE ENFORCE-RED: exit={r.returncode}")
        if r.returncode != 2:
            failures.append(f"expected exit 2 on a defective enforce-mode Write, got {r.returncode}")
        out = json.loads(r.stdout) if r.stdout.strip() else {}
        decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
        reason = out.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        if decision != "deny":
            failures.append(f"expected permissionDecision=deny, got {decision!r}")
        if "FRAGMENT" not in reason or "HANDOFF-POSITIONAL" not in reason:
            failures.append("expected both doc_shapes.py checks named in the deny reason")

        # --- ENFORCE-GREEN ----------------------------------------------------------------
        r = _run(_write_payload(world, "good.md", CLEAN_CONTENT))
        print(f"CASE ENFORCE-GREEN: exit={r.returncode}, stdout={r.stdout!r}")
        if r.returncode != 0 or r.stdout.strip():
            failures.append("expected silent exit 0 on a clean enforce-mode Write")

        # --- OBSERVE-WARN -------------------------------------------------------------------
        _set_mode(world, "observe")
        r = _run(_write_payload(world, "bad.md", DEFECTIVE_CONTENT))
        print(f"CASE OBSERVE-WARN: exit={r.returncode}")
        if r.returncode != 0:
            failures.append(f"expected exit 0 (allow) in observe mode, got {r.returncode}")
        out = json.loads(r.stdout) if r.stdout.strip() else {}
        hso = out.get("hookSpecificOutput", {})
        if hso.get("permissionDecision") != "allow":
            failures.append("expected permissionDecision=allow in observe mode")
        if "would DENY under enforce" not in hso.get("additionalContext", ""):
            failures.append("expected the observe-mode warning prefix in additionalContext")

        # --- OFF-SILENT ---------------------------------------------------------------------
        _set_mode(world, "off")
        r = _run(_write_payload(world, "bad.md", DEFECTIVE_CONTENT))
        print(f"CASE OFF-SILENT: exit={r.returncode}, stdout={r.stdout!r}")
        if r.returncode != 0 or r.stdout.strip():
            failures.append("expected silent exit 0 in off mode regardless of content")

        # --- DEFAULT-OBSERVE (apparatus.json absent) ------------------------------------------
        _set_mode(world, None)
        r = _run(_write_payload(world, "bad.md", DEFECTIVE_CONTENT))
        print(f"CASE DEFAULT-OBSERVE: exit={r.returncode}")
        out = json.loads(r.stdout) if r.stdout.strip() else {}
        if out.get("hookSpecificOutput", {}).get("permissionDecision") != "allow":
            failures.append("expected the missing-apparatus default to behave as observe (allow+warn), not off/enforce")

        # --- EDIT-RECONSTRUCT ------------------------------------------------------------------
        _set_mode(world, "enforce")
        target = world / "edit-target.md"
        target.write_text("# A doc\n\nOriginal sentence here.\n", encoding="utf-8")
        payload = {"tool_name": "Edit",
                  "tool_input": {"file_path": str(target),
                                  "old_string": "Original sentence here.",
                                  "new_string": "The core deliverable."},
                  "cwd": str(world)}
        r = _run(payload)
        print(f"CASE EDIT-RECONSTRUCT: exit={r.returncode}")
        if r.returncode != 2:
            failures.append("expected the reconstructed post-edit content to trip the FRAGMENT check")
        out = json.loads(r.stdout) if r.stdout.strip() else {}
        reason = out.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        if str(target) not in reason:
            failures.append("expected the deny reason to name the REAL target path, not a temp file")
        if "/tmp" in reason.replace(str(target), "") and "seenred" in reason:
            failures.append("deny reason leaked the internal temp file path")

        # --- EXERCISED-LIVENESS ------------------------------------------------------------
        # Five of the six calls above actually ran the check (ENFORCE-RED, ENFORCE-GREEN,
        # OBSERVE-WARN, DEFAULT-OBSERVE, EDIT-RECONSTRUCT); OFF-SILENT returned before the
        # check ever ran, so it must contribute NOTHING -- the discriminator this counter
        # exists to make visible (a Write/Edit count of 6 against an exercised count of 5).
        exercised = _exercised_lines(world)
        expected_outcomes = ["denied", "clean", "observed_would_deny", "observed_would_deny",
                             "denied"]
        got_outcomes = [ln.get("outcome") for ln in exercised]
        print(f"CASE EXERCISED-LIVENESS: {len(exercised)} exercised line(s), outcomes={got_outcomes}")
        if got_outcomes != expected_outcomes:
            failures.append(f"expected exercised outcomes {expected_outcomes} (5 lines, one per "
                            f"real evaluation, OFF-SILENT contributing none), got {got_outcomes}")
        if len(exercised) == 5 and exercised[4].get("file") != str(target):
            failures.append(f"expected the EDIT-RECONSTRUCT exercised line to name the real "
                            f"target path {str(target)!r}, got {exercised[4].get('file')!r}")

    finally:
        shutil.rmtree(world, ignore_errors=True)

    if failures:
        print("doc-shapes-gate-world red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("doc-shapes-gate-world red-specimen: all seven cases behaved as designed — enforce "
          "denies a defective write naming both checks, enforce allows a clean write silently, "
          "observe warns without blocking, off is silent regardless, a missing apparatus.json "
          "defaults to observe (never off, never enforce), an Edit is checked against its "
          "full reconstructed content with the real path named in the teach-text, and the "
          "exercised-liveness counter records exactly the five real evaluations (never "
          "OFF-SILENT's skipped one) in order, each naming the real target path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
