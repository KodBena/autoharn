#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T23:41:09Z
#   last-change: 2026-07-10T23:41:40Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for hooks/pretooluse_delegation_observer.py (Part 2,
BACKLOG "Run-8 mid-run forensics", 2026-07-11 finding 3: "investigation is ungoverned" -- a
subagent dispatch is a machine-observable tool event with zero ledger trace across every run to
date; preamble point 7 says dispatching a subagent is a `decision` row, but nothing enforced or
even OBSERVED that until this hook).

Real infra, no mocks: a throwaway scratch directory + TWO throwaway ledger schemas in the toy db
(192.168.122.1) -- one WITH the s22 work-item layer, one WITHOUT (pre-s22 NAMED CHOICE, mirrors
seen-red/mutation-observer/run_fixtures.py's own two-schema shape) -- both torn down before AND
after this file runs so re-running it never leaves residue. Six cases, run as a fixed STATEFUL
sequence (mirrors seen-red/mutation-observer/run_fixtures.py's own bespoke-order convention: the
work-item-open/closed state is load-bearing across cases, so case ORDER matters here too):

  a-no-open-item      -- dispatch tool_name="Agent" with NO open+claimed work item -> the journal
                         gets a real line (session id, description, prompt sha256+excerpt) AND a
                         loud, non-blocking additionalContext WARNING naming the delegation and
                         teaching `./led decision "..."` / `./led work open|claim`.
  b-open-claimed      -- a work item is now open+claimed; dispatch tool_name="Task" (the LEGACY
                         tool name -- proves BOTH names are matched, not just the current one) ->
                         journal gets a line, but SILENT (no warning; permit-to-work's own allow
                         shape, reused here).
  c-pre-s22           -- against a SEPARATE scratch schema with NO s22 work-item layer at all ->
                         journal STILL gets a line (journaling is unconditional -- module
                         docstring), but no warning is possible to compare against (mirrors
                         permit-to-work's own pre-s22 NAMED CHOICE).
  d-mode-off          -- apparatus.json sets delegation_observer.mode="off" -> genuinely zero
                         cost: NO journal line is written at all (not merely no warning), even
                         though a real dispatch with no open item just happened.
  e-mode-enforce-downgrade -- apparatus.json sets delegation_observer.mode="enforce" (NOT YET
                         SANCTIONED for this hook -- module docstring) -> the hook warns loudly on
                         STDERR naming the downgrade, then behaves EXACTLY like "observe": journal
                         line written, additionalContext warning fires (there is still no open
                         item at this point in the sequence).
  f-journal-unconditional (bonus, inline, not its own case dir) -- re-reads the journal file
                         end-to-end and confirms every ABOVE dispatch that should have journaled
                         (a, b, c, e -- not d) produced exactly one line each, in order, each
                         carrying the right session id and a prompt_sha256 that matches a fresh
                         local hash of the same prompt text (the wire-format cross-check).

Usage: python3 seen-red/delegation-observer/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "pretooluse_delegation_observer.py"

PROBE_DIR = Path("/tmp/.delegobsprobe")
PGHOST, PGDB = "192.168.122.1", "toy"
SCHEMA, KERN, ROLE = "delegprobe", "delegprobe_kernel", "delegprobe_rw"           # s22, cases a/b/d/e
SCHEMA2, KERN2, ROLE2 = "delegprobe2", "delegprobe2_kernel", "delegprobe2_rw"     # pre-s22, case c

LINEAGE = REPO / "kernel" / "lineage"
JOURNAL_PATH = PROBE_DIR / ".claude" / "logs" / "delegation_observer.journal.jsonl"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown() -> None:
    for schema, kern, role in ((SCHEMA, KERN, ROLE), (SCHEMA2, KERN2, ROLE2)):
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "  # declared-drop: delegprobe (declared scratch/test reset)
            f"DROP OWNED BY {role};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def apply_lineage(schema: str, kern: str, role: str, files: list[str]) -> bool:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in files:
        args += ["-f", str(LINEAGE / f)]
    r = sh(args)
    if r.returncode != 0:
        print("apply_lineage FAILED:", r.stdout[-1000:], r.stderr[-1000:])
    return r.returncode == 0


def led_sql(schema: str, kern: str, role: str, sql: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
               "-c", f"SET ROLE {role}; SET search_path = {schema}, {kern}; {sql}"])


def run_hook_leg(tool_name: str, description: str, prompt: str, session_id: str,
                  env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({
        "hook_event_name": "PreToolUse", "tool_name": tool_name,
        "tool_input": {"description": description, "prompt": prompt,
                       "subagent_type": "general-purpose"},
        "session_id": session_id, "cwd": str(PROBE_DIR),
    })
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True, env=env)


def base_env(schema: str) -> dict[str, str]:
    return {"GATE_SUBJECT_ROOT": str(PROBE_DIR), "GATE_LEDGER": f"{schema}.ledger",
            "LEDGER_DB": PGDB, "LEDGER_HOST": PGHOST}


def write_apparatus(mechanisms: dict) -> None:
    (PROBE_DIR / ".claude").mkdir(parents=True, exist_ok=True)
    (PROBE_DIR / ".claude" / "apparatus.json").write_text(
        json.dumps({"mechanisms": mechanisms}), encoding="utf-8")


def journal_lines() -> list[dict]:
    if not JOURNAL_PATH.exists():
        return []
    return [json.loads(ln) for ln in JOURNAL_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]


def check(name: str, result: subprocess.CompletedProcess[str], expect_warning: bool,
          must_contain: list[str], failures: list[str]) -> None:
    combined = result.stdout + result.stderr
    warned = "additionalContext" in combined
    ok = (warned == expect_warning) and result.returncode == 0
    for m in must_contain:
        ok = ok and (m in combined)
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] exit={result.returncode} warned={warned} "
          f"(expect warned={expect_warning})")
    if not ok:
        print(f"  stdout: {result.stdout.strip()[:400]}")
        print(f"  stderr: {result.stderr.strip()[:400]}")
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    print("-- teardown (pre, idempotent) --")
    teardown()

    print("-- setup: scratch schema WITH s22 (cases a/b/d/e) --")
    if not apply_lineage(SCHEMA, KERN, ROLE, [
        "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
        "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql"]):
        print("run_fixtures: ABORTING -- lineage apply failed")
        teardown()
        return 1

    print("-- setup: scratch schema WITHOUT s22 (case c, pre-s22) --")
    if not apply_lineage(SCHEMA2, KERN2, ROLE2, [
        "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
        "s21-session-aware-distinctness.sql"]):
        print("run_fixtures: ABORTING -- pre-s22 lineage apply failed")
        teardown()
        return 1

    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    write_apparatus({})  # default -- delegation_observer defaults to "observe"

    try:
        env = base_env(SCHEMA)

        # a) no open work item -> journal + WARNING (tool_name="Agent", the current name)
        r = run_hook_leg("Agent", "investigate the missing spec", "go read the transcript and "
                          "find phase 2's task text", "sess-a", env)
        check("a-no-open-item", r, True,
              ["investigate the missing spec", "./led decision", "./led work open"], failures)
        lines_after_a = journal_lines()
        ok_a_journal = (len(lines_after_a) == 1 and lines_after_a[0].get("session_id") == "sess-a"
                        and lines_after_a[0].get("tool") == "Agent"
                        and lines_after_a[0].get("description") == "investigate the missing spec")
        print(f"  [{'ok' if ok_a_journal else 'FAIL'}] journal line 1 matches case a's dispatch")
        if not ok_a_journal:
            failures.append("a-journal-content")
        print()

        # b) open+claim a work item, then dispatch tool_name="Task" (LEGACY name) -> journal + SILENT
        led_sql(SCHEMA, KERN, ROLE,
                "INSERT INTO ledger(kind, work_slug, work_title, statement) VALUES "
                "('work_opened','delegprobe-item','delegation probe item','work_opened: "
                "delegprobe-item -- item');"
                "INSERT INTO ledger(kind, work_slug, statement) VALUES "
                "('work_claimed','delegprobe-item','work_claimed: delegprobe-item by author');")
        r = run_hook_leg("Task", "run the tests", "run pytest and report results", "sess-b", env)
        check("b-open-claimed", r, False, [], failures)
        lines_after_b = journal_lines()
        ok_b_journal = (len(lines_after_b) == 2 and lines_after_b[1].get("session_id") == "sess-b"
                        and lines_after_b[1].get("tool") == "Task")
        print(f"  [{'ok' if ok_b_journal else 'FAIL'}] journal line 2 matches case b's dispatch "
              f"(tool_name='Task', the legacy name, recognized)")
        if not ok_b_journal:
            failures.append("b-journal-content")
        print()

        # restore "no open item" state for cases c/e below (close the item opened for case b) --
        # column names per bootstrap/templates/led.tmpl's own `led work close` INSERT: work_slug,
        # work_resolution, work_witness (NOT a bare "resolution" column).
        r_close = led_sql(SCHEMA, KERN, ROLE,
                "INSERT INTO ledger(kind, work_slug, work_resolution, statement) VALUES "
                "('work_closed','delegprobe-item','dropped','work_closed: delegprobe-item "
                "(dropped)');")
        if r_close.returncode != 0:
            print("  [!!] work_closed insert FAILED:", r_close.stdout[-500:], r_close.stderr[-500:])
            failures.append("work_closed_setup")

        # c) pre-s22 schema (no work-item layer at all) -> journal STILL written, no warning
        # possible to compare against (NAMED CHOICE, mirrors permit-to-work's own posture)
        env_c = base_env(SCHEMA2)
        r = run_hook_leg("Agent", "pre-s22 probe", "nothing to compare against here", "sess-c", env_c)
        check("c-pre-s22", r, False, [], failures)
        lines_after_c = journal_lines()
        ok_c_journal = (len(lines_after_c) == 3 and lines_after_c[2].get("session_id") == "sess-c")
        print(f"  [{'ok' if ok_c_journal else 'FAIL'}] journal line 3 matches case c's dispatch "
              f"(journaled even though this world has no work-item layer at all)")
        if not ok_c_journal:
            failures.append("c-journal-content")
        print()

        # d) mode="off" -> genuinely zero cost: NO journal line at all, even for a real dispatch
        # with no open item (schema A is back to "no open item" after the close above).
        write_apparatus({"delegation_observer": {"mode": "off"}})
        before_d = len(journal_lines())
        r = run_hook_leg("Agent", "should not be journaled", "mode is off", "sess-d", env)
        after_d = len(journal_lines())
        ok_d = (after_d == before_d and "additionalContext" not in (r.stdout + r.stderr)
                and r.returncode == 0)
        print("=== d-mode-off ===")
        print(f"  [{'ok' if ok_d else 'FAIL'}] journal unchanged ({before_d} -> {after_d}), "
              f"no warning, exit={r.returncode}")
        print()
        if not ok_d:
            failures.append("d-mode-off")

        # e) mode="enforce" -> NOT YET SANCTIONED for this hook: downgrades to "observe" with a
        # loud stderr warning naming the downgrade, THEN behaves exactly like observe (journal +
        # warning, since schema A still has no open item).
        write_apparatus({"delegation_observer": {"mode": "enforce"}})
        r = run_hook_leg("Agent", "enforce requested but not sanctioned", "prove the downgrade",
                          "sess-e", env)
        check("e-mode-enforce-downgrade", r, True,
              ["NOT YET SANCTIONED", "behaving as 'observe'", "./led decision"], failures)
        lines_after_e = journal_lines()
        ok_e_journal = (len(lines_after_e) == 4 and lines_after_e[3].get("session_id") == "sess-e")
        print(f"  [{'ok' if ok_e_journal else 'FAIL'}] journal line 4 matches case e's dispatch "
              f"(the downgrade still journals and warns, it only refuses to DENY)")
        if not ok_e_journal:
            failures.append("e-journal-content")
        print()
        write_apparatus({})  # restore default

        # f) bonus, inline: end-to-end journal wire-format cross-check (session ids in order,
        # prompt_sha256 matches a fresh local hash of the same prompt text).
        print("=== (bonus) f-journal-unconditional wire-format cross-check ===")
        all_lines = journal_lines()
        expected_sessions = ["sess-a", "sess-b", "sess-c", "sess-e"]  # NOT sess-d -- mode was off
        got_sessions = [ln.get("session_id") for ln in all_lines]
        prompt_a = "go read the transcript and find phase 2's task text"
        sha_a = hashlib.sha256(prompt_a.encode("utf-8")).hexdigest()
        ok_f = (got_sessions == expected_sessions and len(all_lines) == 4
                and all_lines[0].get("prompt_sha256") == sha_a
                and all_lines[0].get("prompt_excerpt") == prompt_a[:200])
        print(f"  [{'ok' if ok_f else 'FAIL'}] sessions in order = {got_sessions} "
              f"(expect {expected_sessions}); line 1's prompt_sha256 matches a fresh local hash")
        print()
        if not ok_f:
            failures.append("f-journal-unconditional")
    finally:
        print("-- teardown (post) --")
        teardown()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print("run_fixtures: all 5 named cases + 1 bonus cross-check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
