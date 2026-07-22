"""run_fixtures.py -- both-polarity proof for the apparatus.json MECHANISM SWITCHBOARD (Part 1,
maintainer mandate 2026-07-10): every hook in this project now reads its own mode
(`mechanisms.<name>.mode`) from `<world>/.claude/apparatus.json` at invocation time -- `"off"`
skips the mechanism entirely, `"observe"` runs the same checks but turns a would-have-denied
outcome into an allow-with-warning, `"enforce"` is byte-identical to the hook's original
behavior. This fixture drives the full three-way on `change_gate`
(hooks/pretooluse_change_gate.py) against a real scratch schema in the toy db, plus a spot-check
of the same three-way on `stamp_intercept` (hooks/stamp_intercept.py) -- the two-mechanism
minimum the maintainer's mandate asks for ("three-way witness on ONE mechanism suffices, plus
spot-check a second").

Real infra, no mocks: a throwaway scratch schema (192.168.122.1, toy db), torn down before AND
after this file runs. Four cases:

  a-off              -- change_gate mode="off": an edit to a file with NO ledger entry naming it
                        (a shape that is UNCONDITIONALLY denied under enforce) is ALLOWED,
                        untouched -- no journal, no warning.
  b-observe          -- the IDENTICAL edit, mode="observe": ALLOWED, but with a loud
                        `additionalContext` warning naming exactly what enforce would have denied,
                        plus a journal record.
  c-enforce          -- the IDENTICAL edit, mode="enforce" (the default): DENIED.
  d-stamp-intercept  -- spot-check on a SECOND mechanism: a broken (missing) STAMP_SECRET, off ->
                        passthrough untouched; observe -> allow-with-warning, unstamped; enforce
                        -> deny.

Usage: python3 seen-red/apparatus-config/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CHANGE_GATE_HOOK = REPO / "hooks" / "pretooluse_change_gate.py"
STAMP_HOOK = REPO / "hooks" / "stamp_intercept.py"

PGHOST, PGDB = fixture_pghost(), "toy"
SCHEMA, KERN, ROLE = "apparatusprobe", "apparatusprobe_kernel", "apparatusprobe_rw"

PROBE_DIR = Path(tempfile.gettempdir()) / ".apparatusprobe"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown() -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "
        f"DROP OWNED BY {ROLE};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {ROLE};"])
    shutil.rmtree(PROBE_DIR, ignore_errors=True)


def setup_schema() -> bool:
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}",
            "-f", str(REPO / "kernel" / "lineage" / "s15-schema.sql")])
    if r.returncode != 0:
        print("setup_schema FAILED:", r.stdout[-1000:], r.stderr[-1000:])
    return r.returncode == 0


def write_apparatus(mechanisms: dict) -> None:
    (PROBE_DIR / ".claude").mkdir(parents=True, exist_ok=True)
    (PROBE_DIR / ".claude" / "apparatus.json").write_text(
        json.dumps({"mechanisms": mechanisms}), encoding="utf-8")


def run_change_gate(target: str, tag: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": target},
                           "cwd": str(PROBE_DIR)})
    env = dict(os.environ)
    env.update({
        "GATE_SUBJECT_ROOT": str(PROBE_DIR), "GATE_LEDGER": f"{SCHEMA}.ledger",
        "LEDGER_DB": PGDB, "LEDGER_HOST": PGHOST,
        "GATE_STATE": str(PROBE_DIR / f"state-{tag}.json"),
        "GATE_JOURNAL": str(PROBE_DIR / f"journal-{tag}.jsonl"),
        # permit_to_work independently off for this fixture -- it exercises change_gate's own
        # mode in isolation, not the s22 layer (a pre-s22-shaped schema here has none anyway).
    })
    return subprocess.run([sys.executable, str(CHANGE_GATE_HOOK)], input=payload,
                          capture_output=True, text=True, env=env)


def run_stamp_intercept(secret_path: str) -> subprocess.CompletedProcess[str]:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo hi"},
                           "cwd": str(PROBE_DIR), "session_id": "apparatusprobe"})
    env = dict(os.environ)
    env.update({"GATE_SUBJECT_ROOT": str(PROBE_DIR), "STAMP_SECRET": secret_path})
    return subprocess.run([sys.executable, str(STAMP_HOOK)], input=payload,
                          capture_output=True, text=True, env=env)


def check(name: str, result: subprocess.CompletedProcess[str], expected_exit: int,
          must_contain: list[str], must_not_contain: list[str], failures: list[str]) -> None:
    combined = result.stdout + result.stderr
    ok = result.returncode == expected_exit
    for m in must_contain:
        ok = ok and (m in combined)
    for m in must_not_contain:
        ok = ok and (m not in combined)
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] exit={result.returncode} (expect {expected_exit})")
    if not ok:
        print(f"  stdout: {result.stdout.strip()[:300]}")
        print(f"  stderr: {result.stderr.strip()[:300]}")
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    print("-- teardown (pre, idempotent) --")
    teardown()

    print("-- setup: scratch schema (s15 only -- ticket/window logic needs nothing more) --")
    if not setup_schema():
        print("run_fixtures: ABORTING -- schema setup failed")
        teardown()
        return 1

    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    target = str(PROBE_DIR / "unticketed_target.py")
    Path(target).write_text("x", encoding="utf-8")

    try:
        # a) mode="off" -- a file with NO ledger entry naming it (unconditionally denied under
        # enforce) is allowed, untouched.
        write_apparatus({"change_gate": {"mode": "off"}})
        r = run_change_gate(target, "a")
        check("a-off", r, 0, [], ["deny", "additionalContext"], failures)

        # b) mode="observe" -- the identical edit: allow, with a warning naming the denial that
        # would have fired, plus a journal record.
        write_apparatus({"change_gate": {"mode": "observe"}})
        r = run_change_gate(target, "b")
        check("b-observe", r, 0,
              ["additionalContext", "would DENY under enforce", "ledger entry naming the file"],
              ["\"permissionDecision\": \"deny\""], failures)

        # c) mode="enforce" (the default) -- the identical edit: denied.
        write_apparatus({"change_gate": {"mode": "enforce"}})
        r = run_change_gate(target, "c")
        check("c-enforce", r, 2,
              ["\"permissionDecision\": \"deny\"", "a ledger entry naming the file"], [], failures)

        # d) spot-check a SECOND mechanism: stamp_intercept, broken (missing) secret.
        broken_secret = str(PROBE_DIR / "nope" / "stamp_secret.hex")
        write_apparatus({"stamp_intercept": {"mode": "off"}})
        r = run_stamp_intercept(broken_secret)
        check("d-stamp-off", r, 0, [], ["additionalContext", "deny"], failures)

        write_apparatus({"stamp_intercept": {"mode": "observe"}})
        r = run_stamp_intercept(broken_secret)
        check("d-stamp-observe", r, 0, ["additionalContext", "UNSTAMPED"], ["\"deny\""], failures)

        write_apparatus({"stamp_intercept": {"mode": "enforce"}})
        r = run_stamp_intercept(broken_secret)
        check("d-stamp-enforce", r, 2, ["\"permissionDecision\": \"deny\""], [], failures)
    finally:
        print("-- teardown (post) --")
        teardown()

    if failures:
        print(f"run_fixtures: {len(failures)} FAILURE(S): {', '.join(failures)}")
        return 1
    print("run_fixtures: all 6 cases passed (change_gate three-way + stamp_intercept spot-check three-way).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
