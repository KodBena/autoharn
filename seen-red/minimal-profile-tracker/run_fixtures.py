#!/usr/bin/env python3
"""run_fixtures — both-polarity live proof for `bootstrap/new-project.sh --profile tracker`
(the modern equivalent of the retired `bootstrap/track-work.sh`; ledger row 1271,
user-guide/TRACK-WORK-RETIREMENT-HERITAGE.md; gates/fixture_census.py REGISTRY entry
"minimal-profile-tracker"). Mirrors seen-red/track-work/run_fixtures.py's own scratch-and-drop
pattern (that fixture's own main(), retired but left in place, is this fixture's direct
ancestor) — a throwaway project directory plus a throwaway schema pair in the TOY db, torn down
after unless a case fails (left standing as evidence).

CASES (both polarities, all live subprocess runs of the real scaffold — never a mock):

  RED-USAGE           -- `--profile tracker` with no `--name` exits 2 (usage), no DB touched.
  RED-BAD-NAME        -- `--profile tracker --name Has_Bad_Chars` (fails the `[a-z0-9]{1,64}`
                        intersection this profile's own --name must satisfy — see
                        bootstrap/new-project.sh's own comment on the boundary-deployment /
                        SQL-identifier allowlist conflict) exits 1, no DB touched.
  RED-NEWWORLD-BAD-NAME -- `--new-world ScratchUP` (uppercase, work item
                        new-world-name-unchecked, row 1324/1335 arc: this same `[a-z0-9]{1,64}`
                        intersection is now ALSO enforced on `--new-world`'s own world name, not
                        just `--profile tracker --name` above) exits 1 citing the intersection,
                        no DB touched. Housed HERE, not in seen-red/setup-tui-worldname-boundary-
                        allowlist/ (that family is TUI/idtypes.py/steps_boundary.py-scoped,
                        Python-only, pinning a git commit for its RED leg -- a different
                        mechanism entirely from a live `bootstrap/new-project.sh` subprocess
                        invocation), because this family already owns the live-subprocess harness
                        (`_run_scaffold`-shaped calls, real toy@192.168.122.1) `new-project.sh`'s
                        OWN character-allowlist refusals are proven against, and the new
                        `--new-world` check lives in the exact same source file, right next to
                        the `--profile tracker` check this family already exercises.
  RED-NEWWORLD-TOO-LONG -- `--new-world` with a 65-character all-lowercase name (same work item;
                        the length half of the intersection, untested by RED-NEWWORLD-BAD-NAME's
                        charclass-only specimen) exits 1 citing the same intersection, no DB
                        touched.
  GREEN-ADOPT         -- a fresh `new-project.sh <dir> --profile tracker --name <name> --db toy
                        --host <host>` on an empty dir exits 0; writes deployment.json (carrying
                        boundary_url/boundary_deployment), boundary-multiplex.toml, keys/,
                        attestations/, roles/, the ten SHIM_VERBS_ALL verbs, legacy/, orchlog —
                        and writes NO `.claude/settings.json`, NO root `CLAUDE.md` (the "standing
                        project is not a governed world" contract, checked directly, not just
                        asserted by the scaffold's own stdout).
  GREEN-BOUNDARY-AUTOSPAWN -- no boundary daemon is running after GREEN-ADOPT (no
                        `.autoharn-service.pid`); the FIRST `./led work open` call spawns one
                        automatically (ensure-running) and the write succeeds.
  GREEN-ROUNDTRIP     -- `./led work open` -> `./led work list` (shows it, open) -> `./led work
                        claim` -> `./led work close ... --review-deferred --witness ...` -> a
                        second `./led work list` (closed item no longer listed, matching the
                        default state filter) -- all live subprocess calls against the real
                        served shim.
  GREEN-DOCTOR        -- `./doctor` reports `0 FAIL` against this deployment.
  RED-EXISTING        -- re-running the SAME command against the SAME dir with no `--force` is
                        REFUSED (exit 1), the ledger row count unchanged.
  GREEN-FORCE         -- the SAME command WITH `--force` succeeds again (exit 0), idempotent on
                        the kernel DDL, the existing ledger rows read back unchanged.

Scratch-only: `--name` (and hence schema/kern/role, and the boundary_deployment segment) is a
throwaway, lowercase-alnum-only name (compliant with BOTH the SQL-identifier allowlist and the
boundary service's own stricter `[a-z0-9-]{1,64}` contract simultaneously — no hyphen, no
underscore, so one name satisfies both at once) chosen not to collide with engine/targets.py's
curated registry or scratch-naming conventions, in the TOY db (192.168.122.1) plus a throwaway
tempdir — both dropped/removed after, UNLESS a case FAILS (left standing as evidence, matching
seen-red/track-work/run_fixtures.py's own convention) — and the spawned boundary service, if any,
is killed before teardown either way (never left as an orphaned background process).

Usage: python3 seen-red/minimal-profile-tracker/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402


REPO = Path(__file__).resolve().parents[2]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
PGHOST, DB = fixture_pghost(), "toy"
SCRATCH_NAME = "mptfixture"  # lowercase-alnum-only: valid SQL identifier AND valid boundary label
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, *args],
                          capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP OWNED BY {ROLE} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _ledger_row_count() -> int | None:
    """None if the schema/table does not exist yet (a case that must not have touched the DB)."""
    r = _psql("-tAc", f"SELECT to_regclass('{SCHEMA}.ledger') IS NOT NULL;")
    if r.stdout.strip() != "t":
        return None
    r = _psql("-tAc", f"SELECT count(*) FROM {SCHEMA}.ledger;")
    return int(r.stdout.strip())


def _run_scaffold(dest: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(NEW_PROJECT), str(dest), "--profile", "tracker",
         "--db", DB, "--host", PGHOST, *extra],
        capture_output=True, text=True, cwd=str(REPO))


def _kill_boundary(dest: Path) -> None:
    pidfile = dest / ".autoharn-service.pid"
    if not pidfile.is_file():
        return
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.3)
    except OSError:
        pass


def main() -> int:
    failures: list[str] = []
    _drop_scratch()  # start from a known-clean scratch substrate
    tmpdir = Path(tempfile.mkdtemp(prefix="minimal-profile-tracker-fixture-"))
    dest = tmpdir / "project"

    # ---------------------------------------------------------------- RED-USAGE (no DB touched)
    r = subprocess.run(["bash", str(NEW_PROJECT), str(dest), "--profile", "tracker",
                        "--db", DB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    if r.returncode != 2:
        failures.append(f"RED-USAGE: expected exit 2 (missing --name), got {r.returncode}\n{r.stderr}")
    if _ledger_row_count() is not None:
        failures.append("RED-USAGE: a schema was created despite the usage refusal (DB touched)")
    print(f"RED-USAGE: exit={r.returncode} (expect 2, no DB touch) -- "
          f"{'PASS' if r.returncode == 2 else 'FAIL'}")

    # ---------------------------------------------------------------- RED-BAD-NAME (no DB touched)
    r = _run_scaffold(dest, "--name", "Has_Bad_Chars")
    bad_name_refused = r.returncode == 1 and "[a-z0-9]{1,64}" in r.stderr
    if not bad_name_refused:
        failures.append(f"RED-BAD-NAME: expected exit 1 citing [a-z0-9]{{1,64}}, got {r.returncode}\n{r.stderr}")
    if _ledger_row_count() is not None:
        failures.append("RED-BAD-NAME: a schema was created despite the name-allowlist refusal (DB touched)")
    print(f"RED-BAD-NAME: exit={r.returncode} (expect 1, '[a-z0-9]{{1,64}}') no DB touch -- "
          f"{'PASS' if bad_name_refused else 'FAIL'}")

    # ---------------------------------------------------------- RED-NEWWORLD-BAD-NAME (no DB touch)
    r = subprocess.run(["bash", str(NEW_PROJECT), str(dest), "--new-world", "ScratchUP",
                        "--db", DB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    newworld_bad_name_refused = r.returncode == 1 and "[a-z0-9]{1,64}" in r.stderr
    if not newworld_bad_name_refused:
        failures.append(f"RED-NEWWORLD-BAD-NAME: expected exit 1 citing [a-z0-9]{{1,64}}, "
                        f"got {r.returncode}\n{r.stderr}")
    if _ledger_row_count() is not None:
        failures.append("RED-NEWWORLD-BAD-NAME: a schema was created despite the refusal (DB touched)")
    print(f"RED-NEWWORLD-BAD-NAME: exit={r.returncode} (expect 1, '[a-z0-9]{{1,64}}') no DB touch -- "
          f"{'PASS' if newworld_bad_name_refused else 'FAIL'}")

    # ---------------------------------------------------------- RED-NEWWORLD-TOO-LONG (no DB touch)
    long_name = "a" * 65
    r = subprocess.run(["bash", str(NEW_PROJECT), str(dest), "--new-world", long_name,
                        "--db", DB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    newworld_too_long_refused = r.returncode == 1 and "[a-z0-9]{1,64}" in r.stderr
    if not newworld_too_long_refused:
        failures.append(f"RED-NEWWORLD-TOO-LONG: expected exit 1 citing [a-z0-9]{{1,64}}, "
                        f"got {r.returncode}\n{r.stderr}")
    if _ledger_row_count() is not None:
        failures.append("RED-NEWWORLD-TOO-LONG: a schema was created despite the refusal (DB touched)")
    print(f"RED-NEWWORLD-TOO-LONG: exit={r.returncode} (expect 1, '[a-z0-9]{{1,64}}') no DB touch -- "
          f"{'PASS' if newworld_too_long_refused else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-ADOPT
    r = _run_scaffold(dest, "--name", SCRATCH_NAME, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE)
    ok = r.returncode == 0
    dep_path = dest / "deployment.json"
    scaffold_verbs = ("led", "judge", "pickup", "audit", "distance-to-clean",
                      "verify-commission", "verify-chain", "attest-doc", "asof-export", "doctor")
    verbs_present = all((dest / v).exists() and (dest / v).stat().st_mode & 0o111 for v in scaffold_verbs)
    boundary_toml = (dest / "boundary-multiplex.toml").is_file()
    no_hooks = not (dest / ".claude" / "settings.json").exists() and not (dest / "CLAUDE.md").exists()
    dep = json.loads(dep_path.read_text(encoding="utf-8")) if dep_path.exists() else {}
    boundary_keys_present = bool(dep.get("boundary_url")) and bool(dep.get("boundary_deployment"))
    if not (ok and dep_path.exists() and verbs_present and boundary_toml and no_hooks and boundary_keys_present):
        failures.append(
            f"GREEN-ADOPT: exit={r.returncode} dep_exists={dep_path.exists()} "
            f"verbs_present={verbs_present} boundary_toml={boundary_toml} no_hooks={no_hooks} "
            f"boundary_keys_present={boundary_keys_present}\nSTDOUT:\n{r.stdout[-2000:]}\nSTDERR:\n{r.stderr[-1000:]}")
    print(f"GREEN-ADOPT: exit={r.returncode} deployment.json={dep_path.exists()} "
          f"ten verbs present+executable={verbs_present} boundary-multiplex.toml={boundary_toml} "
          f"NO hooks/CLAUDE.md={no_hooks} boundary_url+boundary_deployment in deployment.json="
          f"{boundary_keys_present} -- "
          f"{'PASS' if ok and dep_path.exists() and verbs_present and boundary_toml and no_hooks and boundary_keys_present else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-BOUNDARY-AUTOSPAWN
    pidfile_before = (dest / ".autoharn-service.pid").exists()
    r_open = subprocess.run([str(dest / "led"), "work", "open", "smoke", "fixture smoke item"],
                            capture_output=True, text=True, cwd=str(dest))
    autospawned = "spawned it" in r_open.stderr or "unreachable" in r_open.stderr.lower() and r_open.returncode == 0
    pidfile_after = (dest / ".autoharn-service.pid").exists()
    autospawn_ok = (not pidfile_before) and r_open.returncode == 0 and pidfile_after
    if not autospawn_ok:
        failures.append(f"GREEN-BOUNDARY-AUTOSPAWN: pidfile_before={pidfile_before} "
                        f"open_exit={r_open.returncode} pidfile_after={pidfile_after}\n"
                        f"STDOUT:\n{r_open.stdout}\nSTDERR:\n{r_open.stderr}")
    print(f"GREEN-BOUNDARY-AUTOSPAWN: no daemon before ({not pidfile_before}), "
          f"first led call exit={r_open.returncode}, daemon running after ({pidfile_after}) -- "
          f"{'PASS' if autospawn_ok else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-ROUNDTRIP
    r_list1 = subprocess.run([str(dest / "led"), "work", "list"], capture_output=True, text=True, cwd=str(dest))
    list1_ok = r_list1.returncode == 0 and '"slug": "smoke"' in r_list1.stdout
    r_claim = subprocess.run([str(dest / "led"), "work", "claim", "smoke"], capture_output=True, text=True, cwd=str(dest))
    r_close = subprocess.run([str(dest / "led"), "work", "close", "smoke", "shipped",
                              "--review-deferred", "--witness", "test:fixture"],
                             capture_output=True, text=True, cwd=str(dest))
    r_list2 = subprocess.run([str(dest / "led"), "work", "list"], capture_output=True, text=True, cwd=str(dest))
    list2_ok = r_list2.returncode == 0 and '"slug": "smoke"' not in r_list2.stdout
    roundtrip_ok = (list1_ok and r_claim.returncode == 0 and r_close.returncode == 0 and list2_ok)
    if not roundtrip_ok:
        failures.append(f"GREEN-ROUNDTRIP: list1_ok={list1_ok} claim_exit={r_claim.returncode} "
                        f"close_exit={r_close.returncode} list2_ok={list2_ok}\n"
                        f"list1:\n{r_list1.stdout}\nclaim:\n{r_claim.stderr}\n"
                        f"close:\n{r_close.stdout}\n{r_close.stderr}\nlist2:\n{r_list2.stdout}")
    print(f"GREEN-ROUNDTRIP: open(already)->list(shows open)->claim->close(--review-deferred)->"
          f"list(excludes closed) -- {'PASS' if roundtrip_ok else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-DOCTOR
    r_doctor = subprocess.run([str(dest / "doctor")], capture_output=True, text=True, cwd=str(dest))
    doctor_ok = r_doctor.returncode == 0 and "0 FAIL" in r_doctor.stdout
    if not doctor_ok:
        failures.append(f"GREEN-DOCTOR: exit={r_doctor.returncode}\n{r_doctor.stdout}")
    print(f"GREEN-DOCTOR: exit={r_doctor.returncode} (expect 0 FAIL) -- {'PASS' if doctor_ok else 'FAIL'}")

    baseline_rows = _ledger_row_count()

    # ---------------------------------------------------------------- RED-EXISTING
    r = _run_scaffold(dest, "--name", SCRATCH_NAME, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE)
    refused = r.returncode == 1 and "already exists" in r.stderr
    rows_after_refusal = _ledger_row_count()
    untouched = rows_after_refusal == baseline_rows
    if not refused or not untouched:
        failures.append(f"RED-EXISTING: exit={r.returncode} refused={refused} "
                        f"rows_before={baseline_rows} rows_after={rows_after_refusal}\n{r.stderr}")
    print(f"RED-EXISTING: exit={r.returncode} (expect 1, 'already exists') rows unchanged "
          f"({baseline_rows}->{rows_after_refusal}) -- {'PASS' if refused and untouched else 'FAIL'}")

    # ---------------------------------------------------------------- GREEN-FORCE (idempotent re-apply)
    r = _run_scaffold(dest, "--name", SCRATCH_NAME, "--schema", SCHEMA, "--kern", KERN, "--role", ROLE, "--force")
    rows_after_force = _ledger_row_count()
    force_ok = r.returncode == 0 and rows_after_force == baseline_rows
    if not force_ok:
        failures.append(f"GREEN-FORCE: exit={r.returncode} rows_after_force={rows_after_force} "
                        f"(expected {baseline_rows}, unchanged)\n{r.stdout[-1000:]}\n{r.stderr[-1000:]}")
    print(f"GREEN-FORCE: exit={r.returncode} ledger rows unchanged ({baseline_rows}->{rows_after_force}) "
          f"-- {'PASS' if force_ok else 'FAIL'}")

    _kill_boundary(dest)

    if failures:
        print(f"\nminimal-profile-tracker fixture: {len(failures)} FAILURE(S) -- scratch substrate "
              f"left standing as evidence:\n  tempdir: {tmpdir}\n  schema:  {SCHEMA} / {KERN} / {ROLE} "
              f"(db {DB}@{PGHOST})")
        for f in failures:
            print(f"\n!! {f}")
        return 1

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nminimal-profile-tracker fixture: all cases PASS, scratch substrate torn down to zero "
          f"residue (tempdir removed, schema {SCHEMA}/{KERN}/role {ROLE} dropped, boundary killed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
