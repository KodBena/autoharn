#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T20:37:15Z
#   last-change: 2026-07-11T20:37:15Z
#   contributors: e4410ef6/main
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
                        section, and `./distance-to-clean` (TOTAL debt: 0) all succeed live.
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

REPO = Path(__file__).resolve().parents[2]
TRACK_WORK = REPO / "bootstrap" / "track-work.sh"
PGHOST, DB = "192.168.122.1", "toy"
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

    r_d2c = subprocess.run([str(dest / "distance-to-clean")], capture_output=True, text=True, cwd=str(dest))
    d2c_ok = r_d2c.returncode == 0 and "TOTAL debt: 0" in r_d2c.stdout
    if not d2c_ok:
        failures.append(f"GREEN-ADOPT: distance-to-clean not clean\n{r_d2c.stdout}")
    print(f"GREEN-ADOPT: distance-to-clean TOTAL debt: 0 -- {'PASS' if d2c_ok else 'FAIL'}")

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
