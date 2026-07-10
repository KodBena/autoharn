#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T21:00:12Z
#   last-change: 2026-07-10T21:00:25Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for hooks/posttooluse_mutation_observer.py (Part 2,
maintainer mandate 2026-07-10: the bash-mutation OBSERVER that closes the epistemic half of the
gap hooks/pretooluse_change_gate.py's `bash_mutates_governed()` command-shape enumeration cannot
close -- a python-driven write, or any descendant process that writes bytes without spelling a
recognized shell redirection, evades that matcher; this hook DETECTS the mutation after the fact
instead of trying to predict it).

Real infra, no mocks: a throwaway scratch directory + a throwaway ledger schema in the toy db
(192.168.122.1), both torn down before AND after this file runs so re-running it never leaves
residue. Five cases, run as a fixed STATEFUL sequence (mirrors seen-red/stop-clean-exit/
run_fixtures.py's own bespoke-order convention, not the fully-independent-cases convention
seen-red/change-gate-subject-root/ uses -- the marker file's mtime-relative semantics make case
ORDER load-bearing here too):

  a-no-open-item     -- a python-driven write with NO open+claimed work item -> WARNING naming the
                        file and the command (the PreToolUse leg touches the marker, a real write
                        lands, the PostToolUse leg observes it).
  b-open-claimed     -- the identical shape write, but a work item is now open+claimed -> SILENT
                        (permit-to-work's own allow shape, reused here).
  c-pre-s22          -- against a SEPARATE scratch schema with NO s22 work-item layer at all -> a
                        real mutation with no possible permit concept produces NO warning (mirrors
                        permit-to-work's own pre-s22 NAMED CHOICE: nothing to compare against).
  d-mode-off         -- apparatus.json sets mutation_observer.mode="off" -> the PreToolUse leg
                        does not even touch the marker; a mutation with no open item produces NO
                        warning (genuinely zero cost, not merely zero output).
  e-exclusion        -- a write to an EXCLUDED path (.claude/logs/, a named hook state file) with
                        no open item -> NO warning (the exclusion list works, not just the
                        detection).

Usage: python3 seen-red/mutation-observer/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HOOK = REPO / "hooks" / "posttooluse_mutation_observer.py"

PROBE_DIR = Path("/tmp/.mutobsprobe")
PGHOST, PGDB = "192.168.122.1", "toy"
SCHEMA, KERN, ROLE = "mutobsprobe", "mutobsprobe_kernel", "mutobsprobe_rw"
SCHEMA2, KERN2, ROLE2 = "mutobsprobe2", "mutobsprobe2_kernel", "mutobsprobe2_rw"  # pre-s22, case c

LINEAGE = REPO / "kernel" / "lineage"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown() -> None:
    for schema, kern, role in ((SCHEMA, KERN, ROLE), (SCHEMA2, KERN2, ROLE2)):
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
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


def run_hook_leg(event: str, command: str, cwd: str, env_extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"hook_event_name": event, "tool_name": "Bash",
                           "tool_input": {"command": command}, "cwd": cwd})
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


def do_write(relpath: str, content: str) -> None:
    p = PROBE_DIR / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def touch_pre(command: str, env_extra: dict[str, str]) -> None:
    r = run_hook_leg("PreToolUse", command, str(PROBE_DIR), env_extra)
    if r.returncode != 0:
        print(f"  [!!] PreToolUse leg exited {r.returncode}: {r.stdout} {r.stderr}")


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
        print(f"  stdout: {result.stdout.strip()[:300]}")
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    print("-- teardown (pre, idempotent) --")
    teardown()

    print("-- setup: scratch schema WITH s22 (case a/b/d/e) --")
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
    write_apparatus({})  # default -- mutation_observer defaults to "observe"

    try:
        env = base_env(SCHEMA)

        # a) no open work item -> WARNING
        do_write("a_file.py", "content-a")
        touch_pre("python3 -c \"write a_file.py\"", env)
        time.sleep(1.1)
        do_write("a_file.py", "content-a-mutated")
        r = run_hook_leg("PostToolUse", "python3 -c \"write a_file.py\"", str(PROBE_DIR), env)
        check("a-no-open-item", r, True, ["a_file.py", "./led work open"], failures)

        # b) open+claim a work item, then mutate a DIFFERENT file -> SILENT
        led_sql(SCHEMA, KERN, ROLE,
                "INSERT INTO ledger(kind, work_slug, work_title, statement) VALUES "
                "('work_opened','mo-probe','mo probe item','work_opened: mo-probe -- item');"
                "INSERT INTO ledger(kind, work_slug, statement) VALUES "
                "('work_claimed','mo-probe','work_claimed: mo-probe by author');")
        touch_pre("python3 -c \"write b_file.py\"", env)
        time.sleep(1.1)
        do_write("b_file.py", "content-b")
        r = run_hook_leg("PostToolUse", "python3 -c \"write b_file.py\"", str(PROBE_DIR), env)
        check("b-open-claimed", r, False, [], failures)

        # c) pre-s22 schema (no work-item layer at all) -> a real mutation, no open item possible
        #    to check against -> NO warning (NAMED CHOICE, mirrors permit-to-work's own posture)
        env_c = base_env(SCHEMA2)
        touch_pre("python3 -c \"write c_file.py\"", env_c)
        time.sleep(1.1)
        do_write("c_file.py", "content-c")
        r = run_hook_leg("PostToolUse", "python3 -c \"write c_file.py\"", str(PROBE_DIR), env_c)
        check("c-pre-s22", r, False, [], failures)

        # d) mode="off" -> genuinely zero cost: the marker is not even touched, and a real
        #    mutation with no open item produces NO warning.
        write_apparatus({"mutation_observer": {"mode": "off"}})
        marker = PROBE_DIR / ".claude" / "mutation_observer_marker"
        marker.unlink(missing_ok=True)
        touch_pre("python3 -c \"write d_file.py\"", env)
        marker_untouched = not marker.exists()
        time.sleep(1.1)
        do_write("d_file.py", "content-d")
        r = run_hook_leg("PostToolUse", "python3 -c \"write d_file.py\"", str(PROBE_DIR), env)
        ok_d = marker_untouched and "additionalContext" not in (r.stdout + r.stderr) and r.returncode == 0
        print("=== d-mode-off ===")
        print(f"  [{'ok' if ok_d else 'FAIL'}] marker untouched={marker_untouched}, "
              f"no warning, exit={r.returncode}")
        print()
        if not ok_d:
            failures.append("d-mode-off")
        write_apparatus({})  # restore default (observe) for case e

        # e) EXCLUSIONS: a write under an excluded path with no open item -> NO warning
        touch_pre("python3 -c \"write .claude/logs/scratch.txt\"", env)
        time.sleep(1.1)
        do_write(".claude/logs/scratch.txt", "noise")
        r = run_hook_leg("PostToolUse", "python3 -c \"write .claude/logs/scratch.txt\"",
                         str(PROBE_DIR), env)
        check("e-exclusion", r, False, [], failures)
    finally:
        print("-- teardown (post) --")
        teardown()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print("run_fixtures: all 5 cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
