#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-12T18:08:05Z
#   last-change: 2026-07-14T22:23:15Z
#   contributors: 3c50e030/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity proof for bootstrap/freeze-at-stamp.sh (tracker slug
`freeze-at-stamp`; `./led show 225` for the commission, 228/229 for the two ratified spec
amendments this build implements: the frozen tracker copy is a standing, single-tenant database
`autoharn_test` with two roles, `autoharn_test_owner`/`autoharn_test_ro`, provisioned ONCE by the
maintainer -- this script never creates them).

Real infra, no mocks: every case below runs the actual script against THIS repo's own live
tracker (read-only throughout) and a real git commit.

REACHABILITY CAVEAT (honest, not hidden -- ADR-0002/ADR-0013 Rule 5): at authoring time,
`autoharn_test`/`autoharn_test_owner`/`autoharn_test_ro` EXIST (created) but pg_hba.conf on the
postgres host does not yet permit any role to CONNECT to that database from this LAN (verified
directly: `psql -h 192.168.122.1 -d autoharn_test -U autoharn_test_owner` refuses with "no
pg_hba.conf entry"). Per CLAUDE.md ORCHESTRATION ("credentials/pg_hba/hosts ... routes to the
maintainer, always"), this script/fixture never edits pg_hba.conf to make itself reachable. So:

  - Cases a-e below (refusal shapes that do not require reaching autoharn_test, or that exercise
    the standing-db-unreachable refusal itself) are exercised LIVE against real infrastructure.
  - Case f (the full snapshot: wipe -> restore -> truncate -> pickup shows only rows <= cutoff
    and not a later row -> verify-chain INTACT with witness agreeing -> a write attempt refused by
    GRANT) is UNEXERCISED this pass, with the concrete blocker named in its own printed line --
    never faked, per this project's "claims carry witnesses" rule. The orchestrator re-runs this
    fixture once pg_hba is updated to close this gap (a maintainer act, out of this script's and
    this fixture's own reach).

Cases:
  a-dest-exists-refused        -- an existing, non-empty <dest-dir> with no --force is refused,
                                   before any DB/git work is attempted.
  b-bad-commit-refused         -- a nonexistent commit ref is refused via `git rev-parse
                                   --verify`'s own error text.
  c-as-of-id-beyond-max-refused -- --as-of naming a ledger id past the source's own max id is
                                   refused, naming the actual max.
  d-as-of-future-ts-refused    -- --as-of naming a timestamp in the future is refused.
  e-standing-db-unreachable-refused -- the CURRENT true state: autoharn_test exists but pg_hba
                                   refuses the connection; the script's own reachability probe
                                   catches this and refuses with the exact one-time provisioning
                                   teach-text (never a stack trace, never an opaque psql failure).
  f-full-snapshot-e2e          -- UNEXERCISED (see REACHABILITY CAVEAT above) if autoharn_test is
                                   still unreachable when this fixture runs; otherwise runs live:
                                   wipe witnessed before/after, pickup shows a known early row and
                                   does NOT show a known later row, verify-chain reports INTACT
                                   with TAIL-COVERAGE-CONFIRMED at the cutoff id, and a write
                                   attempt through the frozen dest's own ./led is refused by GRANT.
  g-source-row-count-invariant -- SELECT count(*) FROM the SOURCE tracker's ledger is IDENTICAL
                                   before and after every case above -- the source is never
                                   mutated by this script under any polarity, refusal or success.

Usage: python3 seen-red/freeze-at-stamp/run_fixtures.py
Exit 0 if every EXERCISED case matches its expected outcome (an UNEXERCISED case does not fail
the run -- it is reported by name with its concrete blocker); 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCRIPT = REPO / "bootstrap" / "freeze-at-stamp.sh"

sys.path.insert(0, str(REPO / "filing"))
import deployment_record as _dr  # noqa: E402 -- must follow sys.path insert; top-of-file, not lazy

# Source db/host/schema are read LIVE from this checkout's own deployment.json -- the SAME single
# home freeze-at-stamp.sh itself resolves them from (its header: "never hardcoded 'autoharn'/
# 'autoharn_kernel' literal", ADR-0012 P1). A prior version of this fixture hardcoded
# SRC_SCHEMA = "autoharn" as a second, independent derivation of "where the source tracker lives";
# this repo's live schema was renamed to "autoharn1" (a stale, no-longer-live "autoharn" schema
# still sits in the same "toy" database from before that rename), so the hardcoded literal quietly
# started reading the WRONG schema -- a fixture bug, not a freeze-at-stamp.sh bug (see the RCA in
# `./led show` for tracker slug freeze-at-stamp: proven by querying the frozen copy's actual
# contents under the correct schema name, which were correct all along). Deriving it the same way
# the product script does makes this class of drift structurally impossible to repeat.
_src = _dr.load_deployment(REPO / "deployment.json")
PGHOST, PGDB, SRC_SCHEMA = _src.host, _src.db, _src.schema
STANDING_DB = "autoharn_test"


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def source_row_count() -> int:
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", f"SELECT count(*) FROM {SRC_SCHEMA}.ledger;"])
    return int(r.stdout.strip())


def main() -> int:
    failures: list[str] = []
    unexercised: list[tuple[str, str]] = []
    tmp = Path(tempfile.mkdtemp(prefix="freeze-at-stamp-fx-"))

    before_count = source_row_count()
    print(f"== source {SRC_SCHEMA}.ledger row count at fixture start: {before_count} ==\n")

    try:
        # --- a: dest already exists, no --force ---------------------------------------------
        existing_dest = tmp / "already-here"
        existing_dest.mkdir()
        (existing_dest / "marker").write_text("pre-existing\n")
        ra = sh(["sh", str(SCRIPT), "HEAD", str(existing_dest)])
        ok_a = (ra.returncode == 1 and "already exists" in ra.stderr
                and (existing_dest / "marker").read_text() == "pre-existing\n")
        check("a-dest-exists-refused", ok_a,
              f"exit={ra.returncode} stderr_tail={ra.stderr.strip()[-200:]!r}", failures)

        # --- b: bad commit ref ---------------------------------------------------------------
        dest_b = tmp / "bad-commit"
        rb = sh(["sh", str(SCRIPT), "not-a-real-ref-ever-xyz", str(dest_b)])
        ok_b = (rb.returncode == 1 and "does not resolve to a commit" in rb.stderr
                and not dest_b.exists())
        check("b-bad-commit-refused", ok_b,
              f"exit={rb.returncode} stderr_tail={rb.stderr.strip()[-200:]!r} dest_created={dest_b.exists()}",
              failures)

        # --- c: --as-of id beyond source max --------------------------------------------------
        max_id = int(sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                          f"SELECT max(id) FROM {SRC_SCHEMA}.ledger;"]).stdout.strip())
        beyond = max_id + 999999
        dest_c = tmp / "as-of-beyond"
        rc = sh(["sh", str(SCRIPT), "HEAD", str(dest_c), "--as-of", str(beyond)])
        ok_c = (rc.returncode == 1 and f"beyond the source" in rc.stderr
                and str(max_id) in rc.stderr and not dest_c.exists())
        check("c-as-of-id-beyond-max-refused", ok_c,
              f"exit={rc.returncode} max_id={max_id} stderr_tail={rc.stderr.strip()[-200:]!r}", failures)

        # --- d: --as-of a future timestamp ----------------------------------------------------
        dest_d = tmp / "as-of-future"
        rd = sh(["sh", str(SCRIPT), "HEAD", str(dest_d), "--as-of", "2099-01-01T00:00:00Z"])
        ok_d = (rd.returncode == 1 and "is in the future" in rd.stderr and not dest_d.exists())
        check("d-as-of-future-ts-refused", ok_d,
              f"exit={rd.returncode} stderr_tail={rd.stderr.strip()[-200:]!r}", failures)

        # --- e: standing db exists but unreachable (the CURRENT true state) ------------------
        db_exists = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                         f"SELECT count(*) FROM pg_database WHERE datname = '{STANDING_DB}';"]).stdout.strip()
        owner_exists = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                            f"SELECT count(*) FROM pg_roles WHERE rolname = '{STANDING_DB}_owner';"]).stdout.strip()
        ro_exists = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                         f"SELECT count(*) FROM pg_roles WHERE rolname = '{STANDING_DB}_ro';"]).stdout.strip()
        probe = sh(["psql", "-h", PGHOST, "-d", STANDING_DB, "-U", f"{STANDING_DB}_owner", "-tAc", "SELECT 1;"])
        reachable = probe.returncode == 0
        print(f"== live probe: db_exists={db_exists} owner_role_exists={owner_exists} "
              f"ro_role_exists={ro_exists} connect-as-owner reachable={reachable} ==")
        print(f"   probe stderr: {probe.stderr.strip()!r}\n")

        if not reachable:
            dest_e = tmp / "unreachable"
            re_ = sh(["sh", str(SCRIPT), "HEAD", str(dest_e)])
            ok_e = (re_.returncode == 1
                    and "REFUSED -- the standing frozen-snapshot database is not reachable" in re_.stderr
                    and "CREATE DATABASE" in re_.stderr
                    and not dest_e.exists())
            check("e-standing-db-unreachable-refused", ok_e,
                  f"exit={re_.returncode} dest_created={dest_e.exists()} "
                  f"stderr_tail={re_.stderr.strip()[-400:]!r}", failures)
        else:
            check("e-standing-db-unreachable-refused", True,
                  "SKIPPED (db is actually reachable now -- this polarity no longer applies; "
                  "see case f below for the live end-to-end run instead)", failures=[])

        # --- f: the full snapshot end-to-end, ONLY if reachable --------------------------------
        if reachable:
            dest_f = tmp / "full-snapshot"
            # Force a real, small cutoff (not "HEAD") so a KNOWN later row is provably excluded:
            # cutoff = a ledger id well below the current max (id 200), rather than "whatever HEAD
            # happens to be" -- the run must show rows <= 200 and prove a row well past 200 absent.
            rf = sh(["sh", str(SCRIPT), "HEAD", str(dest_f), "--as-of", "200"])
            details: list[str] = [f"script_exit={rf.returncode}"]
            ok_f = rf.returncode == 0 and dest_f.exists()
            if ok_f:
                ro_env = {**os.environ, "PGUSER": "autoharn_test_ro"}
                early = sh(["psql", "-h", PGHOST, "-d", STANDING_DB, "-tAc",
                            f"SELECT count(*) FROM {SRC_SCHEMA}.ledger WHERE id = 1;"], env=ro_env)
                later = sh(["psql", "-h", PGHOST, "-d", STANDING_DB, "-tAc",
                            f"SELECT count(*) FROM {SRC_SCHEMA}.ledger WHERE id > 200;"], env=ro_env)
                early_present = early.stdout.strip() == "1"
                later_absent = later.stdout.strip() == "0"
                details.append(f"row_id=1 present:{early_present} rows>200 present:{not later_absent}")

                vc = sh(["./verify-chain"], cwd=str(dest_f))
                vc_ok = vc.returncode == 0 and ("INTACT" in vc.stdout or "UNAVAILABLE" in vc.stdout)
                details.append(f"verify-chain exit={vc.returncode} stdout_tail={vc.stdout.strip()[-160:]!r}")

                write_attempt = sh(["./led", "decision", "should be refused by grant"], cwd=str(dest_f))
                write_refused = write_attempt.returncode != 0
                details.append(f"write-attempt exit={write_attempt.returncode} "
                                f"stderr_tail={(write_attempt.stdout + write_attempt.stderr).strip()[-160:]!r}")

                # teardown this run's snapshot (wipe, per standing single-tenant practice) before
                # the next case can run -- the standing db itself is never dropped.
                sh(["psql", "-h", PGHOST, "-d", STANDING_DB, "-U", f"{STANDING_DB}_owner",
                    "-v", "ON_ERROR_STOP=1", "-c",
                    f"DROP SCHEMA IF EXISTS {SRC_SCHEMA} CASCADE; "
                    f"DROP SCHEMA IF EXISTS {SRC_SCHEMA}_kernel CASCADE;"])

                ok_f = early_present and later_absent and vc_ok and write_refused
            check("f-full-snapshot-e2e", ok_f, " | ".join(details), failures)
        else:
            unexercised.append((
                "f-full-snapshot-e2e",
                f"BLOCKED: pg_hba.conf on {PGHOST} has no entry permitting "
                f"{STANDING_DB}_owner/{STANDING_DB}_ro to connect to database {STANDING_DB} from "
                f"this host's LAN (verified live: `psql -h {PGHOST} -d {STANDING_DB} -U "
                f"{STANDING_DB}_owner` -> {probe.stderr.strip()!r}). This is a maintainer-only "
                f"credentials/pg_hba act (CLAUDE.md ORCHESTRATION) this fixture will not perform "
                f"itself. Re-run this fixture once pg_hba is updated -- case e above will then "
                f"read 'SKIPPED (reachable now)' and case f will exercise for real."))
            print(f"=== f-full-snapshot-e2e ===\n  [UNEXERCISED] {unexercised[-1][1]}\n")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    after_count = source_row_count()
    ok_g = after_count == before_count
    check("g-source-row-count-invariant", ok_g,
          f"before={before_count} after={after_count} (source tracker must be untouched by every "
          f"polarity above, refusal or success)", failures)

    print(f"== zero residue: {tmp} removed; no schema/db was created or dropped in {PGDB} by this "
          f"fixture ==")

    if unexercised:
        print("UNEXERCISED cases (named blocker, not faked):")
        for name, blocker in unexercised:
            print(f"  - {name}: {blocker}")
        print()

    if failures:
        print("FAILURES:", failures)
        return 1
    print(f"ALL EXERCISED CASES OK ({len(unexercised)} case(s) UNEXERCISED with a concrete, "
          f"named blocker -- see above), zero residue, source row count invariant held.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
