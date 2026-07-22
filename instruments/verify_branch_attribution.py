#!/usr/bin/env python3
"""verify_branch_attribution — the reusable, end-to-end witness for vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md
3b: (a) a REAL invocation of hooks/stamp_intercept.py writes the additive `cwd` field into
`.claude/logs/invocations.jsonl`; (b) a REAL stamped ledger row lands carrying the matching
`stamp_invocation` token; (c) `tools/branch_attribution.py` joins the two and resolves that row to
its checkout. Not a gate (branch_attribution.py refuses nothing; there is no red/green polarity to
prove), so this is a plain capability verification in the `instruments/verify_*.py` register
(mirrors `instruments/verify_consumer_no_vacuous.py`'s own un-gated-capability shape) rather than a
`seen-red/`-registered fixture -- the same posture `engine/contemp_edb.py`/`engine/contemp_audit.py`
already have (neither is in `gates/fixture_census.py`'s REGISTRY; an observer/reporting tool with no
refusal to prove red on has nothing for that registry to hold).

WHAT THIS SCRIPT DOES, self-contained, zero residue:
  1. Scaffolds a throwaway world via `bootstrap/new-project.sh --new-world` (the one sanctioned,
     already-tested path that applies the full kernel lineage through s26 and provisions a real
     stamp secret -- reused here rather than hand-rolling a second copy of that ceremony,
     ADR-0012 P1).
  2. Drives `hooks/stamp_intercept.py` directly (a real subprocess invocation, real stdin/stdout,
     the same harness `seen-red/stamp-intercept-invocation-token/run_fixtures.py` already uses to
     witness the hook) with a `./led decision ...` command, and actually EXECUTES the hook's
     returned, stamped command against the throwaway world -- a real ledger write, not a mock.
  3. Runs `tools/branch_attribution.py` against that world and asserts the new row comes back
     ATTRIBUTED with `cwd` equal to the world's own directory.
  4. Tears down: DROP SCHEMA/ROLE, remove the throwaway directory.

Exit 0 on a clean pass, 1 on any assertion failure (with the mismatch printed), 2 on a setup error
(bootstrap/new-project.sh itself failing, e.g. no DB reachable -- distinguished from an assertion
failure so a CI-less environment fails honestly rather than reporting a false witness).

Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "instruments"))
from pghost_resolve import resolve_pghost  # noqa: E402

PGHOST = resolve_pghost("EPISTEMIC_PGHOST")
DB = "toy"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def scaffold_world(world_name: str, dest: Path) -> None:
    cp = sh(["bash", str(REPO_ROOT / "bootstrap" / "new-project.sh"), str(dest),
             "--new-world", world_name, "--db", DB, "--host", PGHOST, "--name", world_name])
    if cp.returncode != 0:
        print(cp.stdout[-4000:])
        print(cp.stderr[-4000:], file=sys.stderr)
        raise SystemExit(f"SETUP FAILED: bootstrap/new-project.sh exited {cp.returncode} "
                          f"-- is {PGHOST}/{DB} reachable? (exit 2, not an assertion failure)")


def drive_hook_and_execute(dest: Path, command: str, session_id: str, tool_use_id: str) -> str:
    """One real hooks/stamp_intercept.py invocation (subprocess, real stdin/stdout), then actually
    RUNS the hook's own returned (stamped) command against the throwaway world. Returns the minted
    invocation token (parsed back out of the injected PGOPTIONS) so the caller can verify the
    journal/ledger agree on it without re-deriving the injection regex here (ADR-0012 P1: this
    module reads the hook's OWN structured JSON output, never a second hand-parse of PGOPTIONS)."""
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(dest),
               "session_id": session_id, "tool_use_id": tool_use_id}
    env = dict(os.environ)
    for k in ("STAMP_SECRET", "LEDGER_DEPLOYMENT", "GATE_SUBJECT_ROOT"):
        env.pop(k, None)
    cp = sh([sys.executable, str(REPO_ROOT / "hooks" / "stamp_intercept.py")],
            input=json.dumps(payload), env=env)
    if cp.returncode != 0:
        raise SystemExit(f"SETUP FAILED: stamp_intercept.py exited {cp.returncode}: {cp.stderr}")
    out = json.loads(cp.stdout)
    updated = out.get("hookSpecificOutput", {}).get("updatedInput")
    if not updated:
        raise SystemExit(f"SETUP FAILED: hook did not inject a stamp (world not wired?): {cp.stdout}")
    injected_command = updated["command"]
    run = sh(["bash", "-c", injected_command], cwd=str(dest))
    if run.returncode != 0:
        raise SystemExit(f"SETUP FAILED: stamped command failed: {run.stdout} {run.stderr}")
    # Read the token back from the just-written journal line (the honest source -- the hook's own
    # record of what it minted -- rather than re-parsing PGOPTIONS a second time).
    journal = dest / ".claude" / "logs" / "invocations.jsonl"
    last = json.loads(journal.read_text().splitlines()[-1])
    return last["token"]


def teardown(dest: Path, schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=0", "-q", "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
        f"DROP OWNED BY {role};"])
    sh(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=0", "-q", "-c",
        f"DROP ROLE IF EXISTS {role};"])
    # dest lives one level inside the tempfile.mkdtemp() parent (main() made `dest = mkdtemp()/name`
    # so bootstrap/new-project.sh's own "refuse to overwrite" check has a not-yet-existing target) --
    # remove THAT parent, not just `dest`, or the empty mkdtemp shell is left behind (residue).
    shutil.rmtree(dest.parent, ignore_errors=True)


def main() -> int:
    world_name = f"vba{int(time.time())}"
    dest = Path(tempfile.mkdtemp(prefix="branch-attribution-witness-")) / world_name
    schema, kern, role = world_name, f"{world_name}_kernel", f"{world_name}_rw"
    errors: list[str] = []
    try:
        scaffold_world(world_name, dest)
        token = drive_hook_and_execute(
            dest, './led decision "verify_branch_attribution.py witness row"',
            session_id="vba-session", tool_use_id="toolu_vba")
        print(f"  minted+journaled+executed token={token}")

        cp = sh([sys.executable, str(REPO_ROOT / "tools" / "branch_attribution.py"),
                 world_name, str(dest), "--json"],
                env={**os.environ, "LEDGER_DEPLOYMENT": str(dest / "deployment.json")})
        if cp.returncode != 0:
            errors.append(f"branch_attribution.py exited {cp.returncode}: {cp.stderr}")
            print(cp.stdout, cp.stderr)
        else:
            rows = json.loads(cp.stdout)
            match = next((r for r in rows if r.get("stamp_invocation") == token), None)
            if match is None:
                errors.append(f"no row in branch_attribution's output carries token {token}: {rows}")
            else:
                print(f"  branch_attribution resolved: {match}")
                if match["attribution"] != "ATTRIBUTED":
                    errors.append(f"expected ATTRIBUTED, got {match['attribution']!r}: {match}")
                if match["cwd"] != str(dest):
                    errors.append(f"expected cwd={dest}, got {match['cwd']!r}")
    finally:
        teardown(dest, schema, kern, role)

    if errors:
        print("FAILURES:")
        for e in errors:
            print(f"  !! {e}")
        return 1
    print("ALL OK -- 3b end-to-end: hook wrote the cwd field into a real journal line, a real "
          "stamped ledger row landed with the matching stamp_invocation token, and "
          "tools/branch_attribution.py resolved that row to its checkout (ATTRIBUTED, correct cwd). "
          "Zero residue (schema/role dropped, throwaway dir removed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
