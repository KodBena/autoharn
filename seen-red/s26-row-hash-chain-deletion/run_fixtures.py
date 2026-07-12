#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T12:42:33Z
#   last-change: 2026-07-12T12:42:33Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof that a FULL-ROW DELETION (not a content alteration --
seen-red/s26-row-hash-chain/run_fixtures.py already covers that) is caught by kernel/lineage/
s26-row-hash-chain.sql's row_hash chain, and an honest statement of the ONE case it structurally
cannot catch.

Why a separate seen-red directory (added alongside, not folded into
seen-red/s26-row-hash-chain/run_fixtures.py's own cases a-h): the financial-audit lens of the
2026-07-12 re-litigation panel (design/MAINT-RELITIGATION-SYNTHESIS.md, "Untested deletion
scenario") named DELETION -- an id disappearing from the chain entirely -- as a class the
existing fixtures never exercised; every existing case (d/e/h) tampers a row's CONTENT while the
row itself stays present. This file is that missing seen-red case, kept in its own directory per
this project's one-registry-entry-per-scenario-class convention (gates/fixture_census.py) so the
already-witnessed s26-row-hash-chain/red.txt is never touched by an unrelated addition
(ADR-0004 minimal-touch).

THE MECHANISM UNDER TEST: `./verify-chain`'s walk (bootstrap/templates/verify-chain.tmpl,
`walk_chain()`) recomputes each row's expected hash from `COALESCE(predecessor.row_hash,
genesis)`, where "predecessor" is looked up as `SELECT p.row_hash FROM ledger p WHERE p.id < l.id
ORDER BY p.id DESC LIMIT 1` -- the NEAREST SURVIVING row, not literally "id - 1". This is exactly
why a full-row DELETE is a structurally different attack from a content tamper: deleting a row
does not merely corrupt that row, it silently RE-POINTS every later row's predecessor lookup past
the gap.

Cases -- the closure statement this file proves (per ADR-0000's amendment):

  a-intact-baseline            -- a 4-row chain, untouched: `./verify-chain` reports INTACT. The
                                   "intact chain passes" polarity -- proves the fixture below does
                                   not just always report BROKEN regardless of what happened.
  b-interior-deletion-detected -- row 2 of 4 is DELETED OUTRIGHT (trigger bypassed, mirroring a
                                   schema-owner-level DELETE; s26's own header already states a
                                   superuser can disable the trigger). The "deletion detected"
                                   polarity: row 3's predecessor lookup now silently re-points past
                                   the gap to row 1, so row 3's STORED hash (computed at insert time
                                   against row 2's now-gone hash) no longer matches its RECOMPUTED
                                   expected hash. `./verify-chain` reports BROKEN with
                                   first_break_id == the row immediately AFTER the deleted one --
                                   never later, never silently absorbed -- confirming the panel's
                                   "plausibly caught structurally by chain dependency" hypothesis
                                   for the case that has a later row to reveal it.
  c-tail-deletion-not-detected -- the closure statement's honest negative half (ADR-0000's
                                   "name what is NOT covered, converting a silent gap into a filed
                                   deferral"): the LAST row (the highest surviving id, with no row
                                   after it) is deleted the same way. No later row's predecessor
                                   lookup depends on the deleted row's hash, so nothing in the
                                   row_hash chain changes: `./verify-chain` reports INTACT over the
                                   now-shorter chain, silently, with a lower head id and no
                                   diagnostic that a row ever existed past it. This is empirically
                                   verified here, not assumed, and reported plainly: chain-dependency
                                   detection covers every INTERIOR deletion and structurally cannot
                                   cover a TAIL deletion -- the row-hash chain alone has no notion
                                   of "the sequence should have reached id N", only "does what
                                   is here still agree with what is here". Disclosed as residue in
                                   this fixture's own report and the commissioning agent's final
                                   report, per CLAUDE.md's engineering-responsibility corollary --
                                   not fixed here (kernel/lineage is FROZEN; closing it would need a
                                   new mechanism -- e.g. a monotonic max-id witness recorded outside
                                   the table itself -- which is out of this S-sized fixture's scope)
                                   and not silently swept under "plausibly caught".

Usage: python3 seen-red/s26-row-hash-chain-deletion/run_fixtures.py
Exit 0 if every case matches its EXPECTED (not necessarily "detected") outcome; 1 otherwise --
case c's expected outcome is the honest INTACT-despite-deletion result, so this fixture's own exit
0 is not a claim that all deletion is caught, only that the file's stated closure holds.
Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
VERIFY_CHAIN_TMPL = REPO / "bootstrap" / "templates" / "verify-chain.tmpl"

PGHOST, PGDB = "192.168.122.1", "toy"
WORLD_INTERIOR = "s26delfxint"
WORLD_TAIL = "s26delfxtail"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown_all() -> None:
    for schema in (WORLD_INTERIOR, WORLD_TAIL):
        kern, role = f"{schema}_kernel", f"{schema}_rw"
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
            f"DROP OWNED BY {role};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def run_verify_chain(world_dir: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(world_dir / "deployment.json")
    return sh(["python3", str(VERIFY_CHAIN_TMPL), *extra], env=env)


def scaffold(world_dir: Path, world: str, n_rows: int) -> None:
    r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", world,
            "--db", PGDB, "--host", PGHOST])
    if r.returncode != 0:
        raise RuntimeError(f"SCAFFOLD FAILED for {world}: {r.stdout[-1500:]} {r.stderr[-1500:]}")
    for verb in ("led", "verify-chain"):
        (world_dir / verb).chmod(0o755)
    for i in range(1, n_rows + 1):
        rl = sh(["bash", str(world_dir / "led"), "decision", f"row {i} of {n_rows}, via led"],
                cwd=str(world_dir))
        if rl.returncode != 0:
            raise RuntimeError(f"led write FAILED ({world}, row {i}): {rl.stdout} {rl.stderr}")


def delete_row(schema: str, row_id: str) -> None:
    """Bypasses append_only_row exactly the way seen-red/s26-row-hash-chain/run_fixtures.py's own
    content-tamper cases (d/e/h) already do -- mirroring a schema-owner-level DELETE, the one
    adversary s26's own header names as out of the row_hash chain's protection (it adds
    DETECTABILITY, not prevention)."""
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"ALTER TABLE {schema}.ledger DISABLE TRIGGER append_only_row;"])
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"DELETE FROM {schema}.ledger WHERE id = {row_id};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"ALTER TABLE {schema}.ledger ENABLE TRIGGER append_only_row;"])
    if r.returncode != 0:
        raise RuntimeError(f"DELETE FAILED on {schema}.ledger id={row_id}: {r.stdout} {r.stderr}")


def first_and_last_ids(schema: str) -> tuple[str, str]:
    lo = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
             f"SELECT id FROM {schema}.ledger ORDER BY id LIMIT 1;"]).stdout.strip()
    hi = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
             f"SELECT id FROM {schema}.ledger ORDER BY id DESC LIMIT 1;"]).stdout.strip()
    return lo, hi


def nth_id(schema: str, n: int) -> str:
    """1-indexed, ordered by id ascending -- the n-th row currently in the table."""
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
               f"SELECT id FROM {schema}.ledger ORDER BY id LIMIT 1 OFFSET {n - 1};"]).stdout.strip()


def main() -> int:
    teardown_all()
    tmp = Path(tempfile.mkdtemp(prefix="s26del-seenred-"))
    failures: list[str] = []

    try:
        # --- world 1: interior deletion --------------------------------------------------------
        world_dir_i = tmp / WORLD_INTERIOR
        print(f"== scaffolding throwaway --new-world {WORLD_INTERIOR} (4 rows) ==")
        scaffold(world_dir_i, WORLD_INTERIOR, 4)

        # --- a: intact baseline, BEFORE any deletion --------------------------------------------
        ra = run_verify_chain(world_dir_i)
        ok_a = ra.returncode == 0 and ra.stdout.startswith("verify-chain: INTACT -- 4 row(s)")
        check("a-intact-baseline", ok_a, ra.stdout.strip(), failures)

        # --- b: delete row 2 of 4 (interior -- rows 1, 3, 4 survive) -----------------------------
        second_id = nth_id(WORLD_INTERIOR, 2)
        third_id = nth_id(WORLD_INTERIOR, 3)
        delete_row(WORLD_INTERIOR, second_id)
        rb = run_verify_chain(world_dir_i)
        # the deleted row (second_id) can never itself appear as a "break" (it no longer exists to
        # walk); the break must surface at the NEXT SURVIVING row, whose predecessor lookup now
        # silently re-points past the gap -- exactly the docstring's claim, checked literally.
        ok_b = (rb.returncode == 1
                and f"first break at row id {third_id}" in rb.stdout
                and f"row id {second_id}" not in rb.stdout)
        check("b-interior-deletion-detected", ok_b,
              f"deleted id={second_id}, expected break at next-surviving id={third_id}: "
              f"{rb.stdout.strip()}", failures)

        # --- world 2: tail deletion --------------------------------------------------------------
        world_dir_t = tmp / WORLD_TAIL
        print(f"== scaffolding throwaway --new-world {WORLD_TAIL} (3 rows) ==")
        scaffold(world_dir_t, WORLD_TAIL, 3)
        _, last_id = first_and_last_ids(WORLD_TAIL)
        delete_row(WORLD_TAIL, last_id)
        rc = run_verify_chain(world_dir_t)
        # EXPECTED (empirically, not assumed): INTACT over the now-2-row chain -- no later row
        # exists whose predecessor lookup depended on the deleted tail row's hash, so nothing in
        # the row_hash chain detects its absence. This is the closure statement's honest negative
        # half: PASS here means "the residual limit is confirmed and named", not "no gap exists".
        ok_c = rc.returncode == 0 and rc.stdout.startswith("verify-chain: INTACT -- 2 row(s)")
        check("c-tail-deletion-not-detected", ok_c,
              f"deleted the tail row id={last_id}; verify-chain over the now-shorter chain: "
              f"{rc.stdout.strip()} -- row_hash-chain-alone structurally cannot see a tail "
              f"deletion (no surviving row's predecessor hash depends on it); this is a NAMED, "
              f"disclosed limit, not a defect this fixture papers over", failures)

    finally:
        teardown_all()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s26 row_hash chain full-row-deletion proof (intact baseline / interior "
          "deletion detected one row downstream of the gap / tail deletion structurally "
          "undetected by the chain alone, confirmed and named), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
