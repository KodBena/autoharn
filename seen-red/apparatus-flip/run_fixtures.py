#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T13:14:02Z
#   last-change: 2026-07-12T13:14:02Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for hooks/posttooluse_apparatus_flip.py (tracker item
`apparatus-flip-witnessing`, from the "Unwitnessed apparatus flips" finding of the NIST-lens
re-litigation panel, 2026-07-12: a governed agent could Write .claude/apparatus.json and flip a
mechanism to off mid-session with NO witnessed event -- no refusal, no journal line, no ledger
row).

No DB, no ledger: this hook watches exactly one file on disk, so the whole fixture is a throwaway
scratch directory + direct stdin-harness calls, no scratch schema needed. Cases a-g run as a fixed
stateful sequence against PROBE_DIR (mirrors seen-red/mutation-observer/run_fixtures.py's own
bespoke-order convention) since the hook's whole detection method is "compare to the persisted
baseline from the PREVIOUS call". Cases h/i are each a FRESH, never-before-run world of their own
(DAYZERO_DIR / DAYZERO_MATCH_DIR) because the day-zero comparison they test only fires on a
world's true first-ever observation:

  a-baseline-silent    -- the FIRST invocation in a fresh world, whose apparatus.json is BYTE-
                          IDENTICAL to the shipped scaffold default (bootstrap/templates/
                          apparatus.json) -- a genuine `--new-world` scaffold's actual starting
                          state -- establishes the baseline with NO event (nothing has changed
                          since scaffold).
  b-no-flip-silent     -- a second call with apparatus.json UNCHANGED -> still no event, no
                          journal line, no additionalContext (the no-flip polarity).
  c-flip-produces-event -- apparatus.json's mechanisms.change_gate.mode is edited "enforce" ->
                          "off" -> a typed apparatus_flip event lands in the journal, with correct
                          before/after hashes and mechanisms_changed naming exactly change_gate.
  d-malformed-fail-safe -- the file is then truncated into invalid JSON -> the hook still detects
                          the flip (hash changed), journals it with malformed=true and an empty
                          mechanisms_changed (the honest degrade), and -- the fail-safe claim --
                          never raises, never blocks (exit 0, no traceback on stderr).
  e-absent-fail-safe    -- the file is then deleted entirely -> the hook detects present:true ->
                          present:false, journals it, still exit 0, no crash.
  f-restore-flip-again  -- the file is written back with valid content -> detected as a flip from
                          absent, proving the detector recovers cleanly after the malformed/absent
                          detour (not just the happy path).
  g-unwired-silent      -- no GATE_SUBJECT_ROOT and no deployment.json anywhere findable -> the
                          hook is a complete no-op (exit 0, no journal, no state file even
                          created) -- an unwired session stays untouched, same posture as every
                          sibling hook.
  h-day-zero-divergence -- a FRESH world (never observed before) whose apparatus.json ALREADY
                          differs from the shipped scaffold default at the very first hook
                          invocation -- proving a flip that happened before this hook ever ran
                          once (the day-zero blind spot an out-of-frame hack-rationalization
                          audit caught, 2026-07-12) is now caught too: a
                          first_observation_vs_scaffold_default event lands in the journal, tool
                          honestly null, mechanisms_changed naming the real divergence.
  i-day-zero-match-silent -- a second FRESH world whose apparatus.json is byte-identical to the
                          scaffold default at first observation -> silent, same as case a, proven
                          independently on its own fresh world (not reusing case a's state).

Usage: python3 seen-red/apparatus-flip/run_fixtures.py
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
HOOK = REPO / "hooks" / "posttooluse_apparatus_flip.py"
SCAFFOLD_DEFAULT = REPO / "bootstrap" / "templates" / "apparatus.json"

PROBE_DIR = Path("/tmp/.apflipprobe")
UNWIRED_DIR = Path("/tmp/.apflipprobe-unwired")
DAYZERO_DIR = Path("/tmp/.apflipprobe-dayzero")
DAYZERO_MATCH_DIR = Path("/tmp/.apflipprobe-dayzero-match")
ALL_DIRS = (PROBE_DIR, UNWIRED_DIR, DAYZERO_DIR, DAYZERO_MATCH_DIR)


def teardown() -> None:
    for d in ALL_DIRS:
        shutil.rmtree(d, ignore_errors=True)


def write_apparatus_text(root: Path, text: str) -> None:
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "apparatus.json").write_text(text, encoding="utf-8")


def write_apparatus_json(root: Path, mechanisms: dict) -> None:
    write_apparatus_text(root, json.dumps({"mechanisms": mechanisms}))


def run_hook(cwd: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Write",
                           "tool_input": {"file_path": str(cwd / ".claude" / "apparatus.json")},
                           "cwd": str(cwd)})
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, str(HOOK)], input=payload,
                           capture_output=True, text=True, env=env)


def journal_lines(root: Path) -> list[dict]:
    p = root / ".claude" / "logs" / "apparatus_flip.journal.jsonl"
    if not p.is_file():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    print()
    if not ok:
        failures.append(name)


def main() -> int:
    failures: list[str] = []

    print("-- teardown (pre, idempotent) --")
    teardown()
    PROBE_DIR.mkdir(parents=True)

    env = {"GATE_SUBJECT_ROOT": str(PROBE_DIR)}

    try:
        # a) baseline establish -- first-ever call, apparatus.json BYTE-IDENTICAL to the shipped
        # scaffold default (a real --new-world's actual starting state) -> no event.
        (PROBE_DIR / ".claude").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SCAFFOLD_DEFAULT, PROBE_DIR / ".claude" / "apparatus.json")
        r = run_hook(PROBE_DIR, env)
        n_lines = len(journal_lines(PROBE_DIR))
        ok_a = (r.returncode == 0 and "additionalContext" not in (r.stdout + r.stderr)
                and n_lines == 0 and (PROBE_DIR / ".claude" / "apparatus_flip_state.json").is_file())
        check("a-baseline-silent", ok_a,
              f"exit={r.returncode} journal_lines={n_lines} state_file_written="
              f"{(PROBE_DIR / '.claude' / 'apparatus_flip_state.json').is_file()}", failures)

        # b) no change -- still silent
        r = run_hook(PROBE_DIR, env)
        n_lines = len(journal_lines(PROBE_DIR))
        ok_b = r.returncode == 0 and "additionalContext" not in (r.stdout + r.stderr) and n_lines == 0
        check("b-no-flip-silent", ok_b, f"exit={r.returncode} journal_lines={n_lines}", failures)

        # c) a real flip -- change_gate enforce -> off
        write_apparatus_json(PROBE_DIR, {"change_gate": {"mode": "off"}})
        r = run_hook(PROBE_DIR, env)
        lines = journal_lines(PROBE_DIR)
        warned = "additionalContext" in (r.stdout + r.stderr)
        ok_c = (r.returncode == 0 and warned and len(lines) == 1
                and lines[0]["event"] == "apparatus_flip"
                and lines[0]["baseline_kind"] == "prior_observation"
                and lines[0]["tool"] == "Write"
                and "change_gate" in lines[0]["mechanisms_changed"]
                and lines[0]["mechanisms_changed"]["change_gate"] == {"before": "enforce", "after": "off"}
                and lines[0]["before"]["hash"] != lines[0]["after"]["hash"]
                and lines[0]["before"]["malformed"] is False and lines[0]["after"]["malformed"] is False)
        check("c-flip-produces-event", ok_c,
              f"exit={r.returncode} warned={warned} lines={len(lines)} "
              f"mechanisms_changed={lines[0]['mechanisms_changed'] if lines else None!r}", failures)

        # d) malformed -- truncate mid-JSON. Still detected, still exit 0, no traceback.
        write_apparatus_text(PROBE_DIR, '{"mechanisms":{"change')
        r = run_hook(PROBE_DIR, env)
        lines = journal_lines(PROBE_DIR)
        new_line = lines[-1] if lines else {}
        no_traceback = "Traceback" not in r.stderr
        ok_d = (r.returncode == 0 and no_traceback and len(lines) == 2
                and new_line.get("after", {}).get("malformed") is True
                and new_line.get("mechanisms_changed") == {})
        check("d-malformed-fail-safe", ok_d,
              f"exit={r.returncode} no_traceback={no_traceback} lines={len(lines)} "
              f"after={new_line.get('after')}", failures)

        # e) absent -- delete the file entirely. Still detected, still exit 0, no crash.
        (PROBE_DIR / ".claude" / "apparatus.json").unlink()
        r = run_hook(PROBE_DIR, env)
        lines = journal_lines(PROBE_DIR)
        new_line = lines[-1] if lines else {}
        no_traceback = "Traceback" not in r.stderr
        ok_e = (r.returncode == 0 and no_traceback and len(lines) == 3
                and new_line.get("after", {}).get("present") is False
                and new_line.get("after", {}).get("hash") is None)
        check("e-absent-fail-safe", ok_e,
              f"exit={r.returncode} no_traceback={no_traceback} lines={len(lines)} "
              f"after={new_line.get('after')}", failures)

        # f) restore -- write a fresh valid file back, prove the detector recovers cleanly
        write_apparatus_json(PROBE_DIR, {"change_gate": {"mode": "enforce"},
                                          "permit_to_work": {"mode": "enforce"}})
        r = run_hook(PROBE_DIR, env)
        lines = journal_lines(PROBE_DIR)
        new_line = lines[-1] if lines else {}
        ok_f = (r.returncode == 0 and len(lines) == 4
                and new_line.get("before", {}).get("present") is False
                and new_line.get("after", {}).get("present") is True
                and new_line.get("after", {}).get("malformed") is False)
        check("f-restore-flip-again", ok_f,
              f"exit={r.returncode} lines={len(lines)} before={new_line.get('before')} "
              f"after={new_line.get('after')}", failures)

        # g) unwired -- no GATE_SUBJECT_ROOT, no deployment.json anywhere findable -> pure no-op
        UNWIRED_DIR.mkdir(parents=True, exist_ok=True)
        r = run_hook(UNWIRED_DIR, {"GATE_SUBJECT_ROOT": ""})
        state_created = (UNWIRED_DIR / ".claude" / "apparatus_flip_state.json").exists()
        ok_g = r.returncode == 0 and r.stdout.strip() == "" and not state_created
        check("g-unwired-silent", ok_g,
              f"exit={r.returncode} stdout={r.stdout.strip()!r} state_created={state_created}", failures)

        # h) day-zero divergence -- a FRESH world whose apparatus.json is ALREADY flipped relative
        # to the scaffold default, observed for the very first time. Proves the day-zero blind spot
        # (out-of-frame hack-rationalization audit, 2026-07-12) is closed: this is the world's
        # first-ever hook invocation, yet the divergence is still caught and journaled.
        write_apparatus_json(DAYZERO_DIR, {"change_gate": {"mode": "off"}})
        r = run_hook(DAYZERO_DIR, {"GATE_SUBJECT_ROOT": str(DAYZERO_DIR)})
        lines = journal_lines(DAYZERO_DIR)
        warned = "additionalContext" in (r.stdout + r.stderr)
        ok_h = (r.returncode == 0 and warned and len(lines) == 1
                and lines[0]["event"] == "apparatus_flip"
                and lines[0]["baseline_kind"] == "first_observation_vs_scaffold_default"
                and lines[0]["tool"] is None
                and "change_gate" in lines[0]["mechanisms_changed"]
                and lines[0]["mechanisms_changed"]["change_gate"]["after"] == "off")
        check("h-day-zero-divergence", ok_h,
              f"exit={r.returncode} warned={warned} lines={len(lines)} "
              f"baseline_kind={lines[0].get('baseline_kind') if lines else None!r} "
              f"tool={lines[0].get('tool') if lines else '<no line>'!r}", failures)

        # i) day-zero match -- a SEPARATE fresh world whose apparatus.json matches the scaffold
        # default byte-for-byte at first observation -> silent, proven independently of case a.
        (DAYZERO_MATCH_DIR / ".claude").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SCAFFOLD_DEFAULT, DAYZERO_MATCH_DIR / ".claude" / "apparatus.json")
        r = run_hook(DAYZERO_MATCH_DIR, {"GATE_SUBJECT_ROOT": str(DAYZERO_MATCH_DIR)})
        lines = journal_lines(DAYZERO_MATCH_DIR)
        ok_i = (r.returncode == 0 and "additionalContext" not in (r.stdout + r.stderr)
                and len(lines) == 0
                and (DAYZERO_MATCH_DIR / ".claude" / "apparatus_flip_state.json").is_file())
        check("i-day-zero-match-silent", ok_i,
              f"exit={r.returncode} journal_lines={len(lines)}", failures)
    finally:
        print("-- teardown (post) --")
        teardown()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print("run_fixtures: all 9 cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
