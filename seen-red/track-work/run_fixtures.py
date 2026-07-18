#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T20:37:15Z
#   last-change: 2026-07-18T07:46:42Z
#   contributors: e4410ef6/main, ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures — both-polarity live proof for bootstrap/track-work.sh (the standing
work-tracking offering; design/USER-WORK-STATUS-OFFERING.md; gates/fixture_census.py REGISTRY entry
"track-work"). Mirrors kernel/fixtures/s22_work_item_fixture.py's scratch-and-drop pattern: a
throwaway project directory plus a throwaway schema pair in the TOY db, torn down after unless a
case fails (left standing as evidence, matching the standing-probe convention).

CASES (both polarities, all live subprocess runs of the real script — never a mock):

  GREEN-ADOPT        -- a fresh `track-work.sh <dir> --name <name> --db toy --host <host>` on an
                        empty dir exits 0, writes deployment.json + the five verb shims, and the
                        shims actually work: `./led work open/claim`, `./pickup`'s IN-FLIGHT
                        section, and `./distance-to-clean` (TOTAL debt: 1, the `smoke` item this
                        very case deliberately leaves open+claimed -- see the DRIFT NOTE below)
                        all succeed live.

  DRIFT NOTE (ledger row 1368, diagnosed 2026-07-18): this fixture originally asserted
  `TOTAL debt: 0` here. Commit 0a3a204 ("distance-to-clean: mirror the stop-gate's five debt
  categories, not three", 2026-07-16 -- AFTER this fixture's own 2026-07-11 authoring date)
  deliberately widened `distance-to-clean` from three debt categories to the stop-gate hook's
  own five, explicitly so it would stop printing "TOTAL debt: 0" on a world the stop-gate hook
  would otherwise block on real, undischarged work-item debt (that commit's own message: "so it
  could print 'TOTAL debt: 0' on a world the stop-gate then blocked on real, undischarged
  work-item debt (witnessed live)"). GREEN-ADOPT below opens AND claims `smoke` but never closes
  it (deliberately, to prove `./pickup`'s IN-FLIGHT section renders a live open+claimed item) --
  so under the widened, INTENDED distance-to-clean behaviour that open+claimed item is exactly
  one unit of real debt, and the fixture's stale `debt: 0` expectation is what changed, not
  distance-to-clean. The assertion below is updated to `TOTAL debt: 1`, naming `smoke` as the
  expected debt item.
  RED-EXISTING        -- re-running the SAME command against the SAME dir with no --force is
                        REFUSED (exit 1), naming deployment.json and never touching the DB again
                        (verified by the row count in `ledger` staying exactly 2 — the two rows
                        GREEN-ADOPT wrote — across the refused re-run).
  RED-USAGE           -- omitting a required flag (--name) exits 2 with a usage message, no DB
                        touched at all (no schema created).
  GREEN-FORCE         -- the SAME command WITH --force on the existing dir succeeds again (exit
                        0) and is idempotent on the kernel DDL (every kernel/lineage file is
                        written `IF NOT EXISTS`/`CREATE OR REPLACE`, so a second apply is a no-op
                        on structure) — the two work-item rows from GREEN-ADOPT still read back
                        unchanged afterward.

Scratch-only: schema/kern/role derived from a throwaway name (`SCRATCH_NAME` below, chosen to
not collide with engine/targets.py's curated registry or scratch-naming conventions) in the TOY
db (192.168.122.1) plus a throwaway tempdir — both dropped/removed after, UNLESS a case FAILS
(left standing as evidence, kernel/fixtures/s22_work_item_fixture.py's own convention).

Usage: python3 seen-red/track-work/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)


REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "twfixture"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                          capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _ledger_row_count() -> int | None:
    """None if the schema/table does not exist yet (a case that must not have touched the DB)."""
    r = _psql("-tAc", f"SELECT to_regclass('{SCHEMA}.ledger') IS NOT NULL;")
    if r.stdout.strip() != "t":
        return None
    r = _psql("-tAc", f"SELECT count(*) FROM {SCHEMA}.ledger;")
    return int(r.stdout.strip())


def _run_track_work(dest: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(TRACK_WORK), str(dest), "--db", DB, "--host", PGHOST, *extra],
        capture_output=True, text=True, cwd=str(REPO))


def main() -> int:
    failures: list[str] = []
    _drop_scratch()  # start from a known-clean scratch substrate
    tmpdir = Path(tempfile.mkdtemp(prefix="track-work-fixture-"))
    dest = tmpdir / "project"

    # ---------------------------------------------------------------- RED-USAGE (no DB touched)
    r = subprocess.run([str(TRACK_WORK), str(dest), "--db", DB, "--host", PGHOST],
                       capture_output=True, text=True, cwd=str(REPO))
    if r.returncode != 2:
        failures.append(f"RED-USAGE: expected exit 2 (missing --name), got {r.returncode}\n{r.stderr}")
    if _ledger_row_count() is not None:
        failures.append("RED-USAGE: a schema was created despite the usage refusal (DB touched)")
    print(f"RED-USAGE: exit={r.returncode} (expect 2, no DB touch) -- "
          f"{'PASS' if r.returncode == 2 else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-ADOPT
    r = _run_track_work(dest, "--name", SCRATCH_NAME, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE)
    ok = r.returncode == 0
    dep = dest / "deployment.json"
    verbs_present = all((dest / v).exists() and (dest / v).stat().st_mode & 0o111 for v in
                        ("led", "judge", "pickup", "audit", "distance-to-clean"))
    if not ok or not dep.exists() or not verbs_present:
        failures.append(f"GREEN-ADOPT: exit={r.returncode} dep_exists={dep.exists()} "
                        f"verbs_present={verbs_present}\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    print(f"GREEN-ADOPT: exit={r.returncode} deployment.json={dep.exists()} "
          f"verb shims present+executable={verbs_present} -- {'PASS' if ok and dep.exists() and verbs_present else 'FAIL'}")

    # led work open/claim actually work (the verb shims are live, not just present)
    r_open = subprocess.run([str(dest / "led"), "work", "open", "smoke", "fixture smoke item"],
                            capture_output=True, text=True, cwd=str(dest))
    r_claim = subprocess.run([str(dest / "led"), "work", "claim", "smoke"],
                             capture_output=True, text=True, cwd=str(dest))
    if r_open.returncode != 0 or r_claim.returncode != 0:
        failures.append(f"GREEN-ADOPT: led work open/claim failed "
                        f"(open exit={r_open.returncode}, claim exit={r_claim.returncode})\n"
                        f"{r_open.stderr}\n{r_claim.stderr}")
    print(f"GREEN-ADOPT: led work open+claim exit={r_open.returncode}/{r_claim.returncode} -- "
          f"{'PASS' if r_open.returncode == 0 and r_claim.returncode == 0 else 'FAIL'}")

    r_pickup = subprocess.run([str(dest / "pickup")], capture_output=True, text=True, cwd=str(dest))
    pickup_ok = r_pickup.returncode == 0 and "smoke" in r_pickup.stdout and "SECTION: IN-FLIGHT" in r_pickup.stdout
    if not pickup_ok:
        failures.append(f"GREEN-ADOPT: pickup did not show the open work item\n{r_pickup.stdout}")
    print(f"GREEN-ADOPT: pickup shows IN-FLIGHT smoke item -- {'PASS' if pickup_ok else 'FAIL'}")

    # TOTAL debt: 1, not 0 -- `smoke` is deliberately left open+claimed (r_claim above, never
    # closed) to prove the IN-FLIGHT section renders it live, and distance-to-clean's five-
    # category widening (commit 0a3a204, 2026-07-16) correctly counts exactly that as one unit
    # of work-item debt. distance-to-clean itself is a gate-style verb (bootstrap/templates/
    # distance-to-clean.tmpl's own main(): `return 0 if total == 0 else 1`), so exit 1 is the
    # CORRECT, expected exit here, not a failure. See this file's own module-docstring DRIFT
    # NOTE (ledger row 1368).
    r_d2c = subprocess.run([str(dest / "distance-to-clean")], capture_output=True, text=True, cwd=str(dest))
    d2c_ok = (r_d2c.returncode == 1 and "TOTAL debt: 1" in r_d2c.stdout
              and "work-items        : 1 open+claimed item(s)" in r_d2c.stdout
              and "'smoke'" in r_d2c.stdout)
    if not d2c_ok:
        failures.append(f"GREEN-ADOPT: distance-to-clean did not report the expected smoke "
                        f"debt (TOTAL debt: 1, work-items: 1, slug 'smoke')\n{r_d2c.stdout}")
    print(f"GREEN-ADOPT: distance-to-clean TOTAL debt: 1 (smoke, open+claimed) -- "
          f"{'PASS' if d2c_ok else 'FAIL'}")

    baseline_rows = _ledger_row_count()
    if baseline_rows != 2:
        failures.append(f"GREEN-ADOPT: expected exactly 2 ledger rows (open+claim), got {baseline_rows}")

    # ---------------------------------------------------------------- RED-EXISTING
    r = _run_track_work(dest, "--name", SCRATCH_NAME, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE)
    refused = r.returncode == 1 and "already exists" in r.stderr
    rows_after_refusal = _ledger_row_count()
    untouched = rows_after_refusal == baseline_rows
    if not refused or not untouched:
        failures.append(f"RED-EXISTING: exit={r.returncode} refused={refused} "
                        f"rows_before={baseline_rows} rows_after={rows_after_refusal}\n{r.stderr}")
    print(f"RED-EXISTING: exit={r.returncode} (expect 1, 'already exists') rows unchanged "
          f"({baseline_rows}->{rows_after_refusal}) -- {'PASS' if refused and untouched else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-FORCE (idempotent re-apply)
    r = _run_track_work(dest, "--name", SCRATCH_NAME, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE, "--force")
    rows_after_force = _ledger_row_count()
    force_ok = r.returncode == 0 and rows_after_force == baseline_rows
    if not force_ok:
        failures.append(f"GREEN-FORCE: exit={r.returncode} rows_after_force={rows_after_force} "
                        f"(expected {baseline_rows}, unchanged -- --force re-applies DDL idempotently, "
                        f"it does not touch existing ledger rows)\n{r.stdout}\n{r.stderr}")
    print(f"GREEN-FORCE: exit={r.returncode} ledger rows unchanged ({baseline_rows}->{rows_after_force}) "
          f"-- {'PASS' if force_ok else 'FAIL'}")

    if failures:
        print(f"\ntrack-work fixture: {len(failures)} FAILURE(S) -- scratch substrate left standing "
              f"as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / {KERN} / {ROLE} (db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\ntrack-work fixture: all cases PASS, scratch substrate torn down to zero residue "
          f"(tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
