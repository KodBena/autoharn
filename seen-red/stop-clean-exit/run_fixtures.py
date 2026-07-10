#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-10T19:43:05Z
#   last-change: 2026-07-10T19:43:05Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py — both-polarity proof for hooks/stop_clean_exit.py (the clean-exit Stop-hook
gate, BACKLOG "Run-5 forensics" family, 2026-07-10 -- CLAUDE.md point 5, "done means clean",
mechanized as a hook instead of left as advice).

Unlike seen-red/change-gate-subject-root/run_fixtures.py (whose five cases are each fully
independent -- any order, any subset), THREE of this gate's four named cases are a single
STATEFUL sequence against one throwaway probe world (the circuit breaker's whole point is state
across repeated Stop events), so this driver runs them in a fixed, documented order rather than
iterating case directories generically. Each case still keeps its inputs/expectations in its own
directory (stdin.json / env.json / expected_exit.txt / expect.txt), the same per-case-dir
convention every seen-red/ gate uses -- only the EXECUTION ORDER is bespoke here, not the case
shape.

Sequence (real infra, no mocks -- a throwaway probe world at /home/bork/w/vdc/1/.stopprobe, toy
db, torn down before AND after):
  1. a-unwired            -- no DB touched at all; proves zero interference for an un-opted-in
                             session (no env var, no deployment.json at cwd).
  2. [setup] bootstrap/new-project.sh --new-world stopprobe --db toy --host 192.168.122.1
             --name stopprobe  -> a fresh, CLEAN world (s22 applied automatically, per
             new-project.sh's own --new-world lineage chain).
  3. b-clean-world        -- the freshly-scaffolded world has open review_gap/question_status/
                             work_item_current/work_item_violations rows: none. Expect allow,
                             silently.
  4. [debt] ./led work open probe-item-1 "..."  -- an open, UNCLAIMED work item, never closed
             (the exact run-5 shape: a never-closed work item left in the ledger).
  5. c-dirty-world        -- call #1 against that debt: expect BLOCK (exit 2), the debt
             enumerated by slug with the closing command (./led work claim ...).
  6. [unasserted] a second identical call, run inline (not its own case directory) purely to
             advance the circuit-breaker's internal counter from 1 to 2 -- still a real
             assertion (checked inline below), just not one of the four NAMED fixture cases the
             build mandate lists by name.
  7. d-circuit-breaker-third-repeat -- call #3 against the SAME unchanged debt: the breaker
             fires -- expect ALLOW (exit 0) with the loud warning banner, not a block.
  8. [cleanup] ./led work claim + ./led work close the debt item; verify one more call returns a
             silent allow AND the state file is gone (progress resets the breaker / clean clears
             it) -- a fifth, bonus sanity check, reported but not one of the four named cases.
  9. [teardown] drop the probe schemas/role/directory.

Usage: python3 seen-red/stop-clean-exit/run_fixtures.py
Exit 0 if every case matches (including the unasserted/bonus inline checks); 1 otherwise.
Lazy imports banned.
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
HOOK = REPO / "hooks" / "stop_clean_exit.py"
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"

PROBE_DIR = Path("/home/bork/w/vdc/1/.stopprobe")
PGHOST, PGDB = "192.168.122.1", "toy"
SCHEMA, KERN, ROLE = "stopprobe", "stopprobe_kernel", "stopprobe_rw"
SLUG = "probe-item-1"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown_probe() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: stopprobe (declared scratch/test reset)
        f"DROP OWNED BY {ROLE};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {ROLE};"])
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def setup_probe() -> bool:
    r = sh([str(NEW_PROJECT), str(PROBE_DIR), "--new-world", SCHEMA,
            "--db", PGDB, "--host", PGHOST, "--name", SCHEMA])
    if r.returncode != 0:
        print("setup_probe FAILED:")
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        return False
    return True


def led(*args: str, actor: str | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if actor:
        env["LED_ACTOR"] = actor
    return sh([str(PROBE_DIR / "led"), *args], cwd=str(PROBE_DIR), env=env)


def build_env(case: Path) -> dict[str, str]:
    env = dict(os.environ)
    spec_path = case / "env.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8")) if spec_path.exists() else {}
    for var in spec.get("unset", []):
        env.pop(var, None)
    for var, val in spec.get("set", {}).items():
        env[var] = val
    return env


def run_hook(case: Path) -> subprocess.CompletedProcess[str]:
    stdin_text = (case / "stdin.json").read_text(encoding="utf-8")
    return subprocess.run([sys.executable, str(HOOK)], input=stdin_text,
                           capture_output=True, text=True, env=build_env(case))


def check(result: subprocess.CompletedProcess[str], case: Path) -> tuple[bool, str]:
    expected = int((case / "expected_exit.txt").read_text(encoding="utf-8").strip())
    expect_file = case / "expect.txt"
    assertions = expect_file.read_text(encoding="utf-8").splitlines() if expect_file.exists() else []
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
    lines.append(f"  stdout[:200]: {result.stdout.strip()[:200]!r}")
    lines.append(f"  stderr[:200]: {result.stderr.strip()[:200]!r}")
    return ok, "\n".join(lines)


def run_named_case(name: str, failures: list[str]) -> None:
    case = HERE / name
    print(f"=== {name} ===")
    result = run_hook(case)
    ok, report = check(result, case)
    print(report)
    print()
    if not ok:
        failures.append(name)


def main() -> int:
    failures: list[str] = []

    print("-- teardown (pre, idempotent) --")
    teardown_probe()

    # 1. unwired -- no DB dependency, runs standalone.
    run_named_case("a-unwired", failures)

    # 2. setup a fresh, clean probe world.
    print("-- setup probe world --")
    if not setup_probe():
        failures.append("setup_probe")
        print(f"run_fixtures: ABORTING -- setup failed. FAILURE(S): {', '.join(failures)}")
        return 1

    try:
        # 3. clean-world: freshly scaffolded, nothing open yet.
        run_named_case("b-clean-world", failures)

        # 4. create real debt: an open, unclaimed work item, never closed (the run-5 shape).
        print("-- creating debt: ./led work open probe-item-1 (never closed) --")
        r = led("work", "open", SLUG, "a test work item that is never closed")
        print(r.stdout.strip(), r.stderr.strip())
        if r.returncode != 0:
            failures.append("debt_setup")

        # 5. dirty-world: call #1 against that debt -- expect BLOCK, count -> 1.
        run_named_case("c-dirty-world", failures)

        # 6. unasserted call #2 -- same identical debt, advances the breaker counter to 2.
        print("=== (unasserted) second identical block, advancing breaker to 2/3 ===")
        case = HERE / "c-dirty-world"
        r2 = run_hook(case)
        ok2 = r2.returncode == 2 and "seen 2/3 times" in (r2.stdout + r2.stderr)
        print(f"  [{'ok' if ok2 else 'FAIL'}] exit={r2.returncode}, contains 'seen 2/3 times'")
        print()
        if not ok2:
            failures.append("unasserted-second-block")

        # 7. circuit-breaker third repeat: call #3, same debt -- expect ALLOW-with-warning.
        run_named_case("d-circuit-breaker-third-repeat", failures)

        # 8. cleanup + bonus sanity: close the debt, verify a clean allow and state-file reset.
        print("-- cleanup: claim + close the debt item --")
        led("work", "claim", SLUG)
        r = led("work", "close", SLUG, "dropped", actor="reviewer")
        print(r.stdout.strip(), r.stderr.strip())
        case = HERE / "b-clean-world"  # same stdin/env as the original clean case
        r3 = run_hook(case)
        state_file = PROBE_DIR / ".claude" / "stop_clean_exit_state.json"
        ok3 = r3.returncode == 0 and not r3.stdout.strip() and not r3.stderr.strip() and not state_file.exists()
        print(f"=== (bonus) post-cleanup clean allow + state file cleared ===")
        print(f"  [{'ok' if ok3 else 'FAIL'}] exit={r3.returncode}, no output, state file absent")
        print()
        if not ok3:
            failures.append("post-cleanup-clean-and-reset")
    finally:
        print("-- teardown (post) --")
        teardown_probe()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print("run_fixtures: all cases passed (4 named + 2 inline sanity checks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
