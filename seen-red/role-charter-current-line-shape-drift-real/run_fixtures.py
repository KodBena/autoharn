#!/usr/bin/env python3
"""run_fixtures.py -- REAL-INFRA sibling family (seen-red/role-charter-current-line-shape-
drift-real/, registered separately in gates/fixture_census.py since a registry entry names one
dir 1:1) of seen-red/role-charter-current-line-shape-drift/run_fixtures.py, for tools/
role_charter.py's
own row-1295 fix round (coordinator correction: the mock-only witness this fixture family
started with inherited a pgcrypto blocker that came from a throwaway LOCAL Postgres cluster;
this project's own house pattern is a scratch world scaffolded against the LAN host,
HARNESS_PGHOST -- see seen-red/review-witness-row-existence-check/run_fixtures.py and seen-red/
s51-artifact-store/run_fixtures.py for the same ADOPT-via-`bootstrap/new-project.sh --new-world`
pattern this file reuses). That blocker does not apply here: this file stands up a REAL scratch
world (full birth chain through s57) and drives the REAL served `led`.

TWO CASES, both against the SAME real scratch world/principal/charter registration:
  REAL-CLEAN     -- a genuine live charter registration (`role_charter.py register`, real served
                    `led`), then a second `register` attempt for the same role: correctly
                    REFUSED via JC4 (the existing registration is SEEN, not hidden) -- confirms
                    the fix's legitimate path end to end on real infra (run_fixtures.py's
                    mock-only R3, now witnessed for real).
  REAL-CORRUPTED -- the SAME registration row, but read through corrupt_led_proxy.py (this
                    directory's own proxy over the real served `led`, forwarding every command
                    unchanged except corrupting the ONE current-line naming this registration):
                    the fixed parser refuses loudly (CharterError, SHAPE DRIFT, names the line
                    and the producing command), exit 1, nothing is (re-)registered
                    (run_fixtures.py's mock-only R2, now witnessed for real).

NOT re-exercised here: run_fixtures.py's own R1 (the PRE-fix silent vacuous-pass, against git
417b200's checked-out tools/role_charter.py) -- the coordinator's correction scopes the
mandatory real leg to POST-fix behavior only; R1 stays a mock-only regression case, unchanged,
in run_fixtures.py.

Usage: python3 seen-red/role-charter-current-line-shape-drift-real/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned; stdlib only.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
ROLE_CHARTER = REPO / "tools" / "role_charter.py"
PROXY = HERE / "corrupt_led_proxy.py"

sys.path.insert(0, str(REPO / "seen-red"))  # for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402

_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = fixture_pghost(), "toy"
SCRATCH_NAME = "rcharterreal"
SCHEMA, KERN, ROLE = SCRATCH_NAME, f"{SCRATCH_NAME}_kernel", f"{SCRATCH_NAME}_rw"
ROLE_NAME = "editor"
SCAN_LIMIT = "200"

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str) -> None:
    tag = "ok" if cond else "FAIL"
    print(f"=== {label} ===\n  [{tag}] {detail}\n")
    if not cond:
        FAILURES.append(label)


def _psql(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["psql", "-h", PGHOST, "-d", PGDB, *args], capture_output=True, text=True)


def _drop_scratch() -> None:
    _psql("-v", "ON_ERROR_STOP=0", "-q",
          "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;",
          "-c", f"DROP SCHEMA IF EXISTS {KERN} CASCADE;",
          "-c", f"DROP ROLE IF EXISTS {ROLE};")


def _run_led(dest: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(dest / "led"), *args], cwd=str(dest), capture_output=True, text=True)


def main() -> int:
    _drop_scratch()
    tmpdir = Path(tempfile.mkdtemp(prefix="role-charter-current-line-shape-drift-real-"))
    dest = tmpdir / "project"

    r = subprocess.run([str(NEW_PROJECT), str(dest), "--new-world", SCRATCH_NAME,
                        "--db", PGDB, "--host", PGHOST], capture_output=True, text=True, cwd=str(REPO))
    ok = r.returncode == 0 and (dest / "deployment.json").exists()
    print(f"ADOPT: new-project.sh --new-world exit={r.returncode} "
          f"deployment.json={(dest / 'deployment.json').exists()} -- {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(f"ADOPT FAILED -- scratch left standing for inspection:\n  tempdir: {tmpdir}\n"
              f"STDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
        return 1

    proc = None
    crashed_with: BaseException | None = None
    try:
        proc = bs_fixtures.serve_existing_world(dest / "deployment.json", tmpdir)
        real_led = str(dest / "led")

        reg = _run_led(dest, "register-principal", ROLE_NAME, "human",
                        "--purpose", "role-charter-current-line-shape-drift-real fixture")
        assert reg.returncode == 0, f"register-principal failed: {reg.stdout!r} {reg.stderr!r}"

        charter_file = tmpdir / "CHARTER.md"
        charter_file.write_text("# editor charter\n\nfixture only -- binds nothing real.\n",
                                 encoding="utf-8")
        first = subprocess.run(
            [sys.executable, str(ROLE_CHARTER), "register", ROLE_NAME, str(charter_file),
             "--led", real_led, "--scan-limit", SCAN_LIMIT],
            capture_output=True, text=True)
        assert first.returncode == 0 and "registered -- role" in first.stdout, (
            f"initial real registration failed: {first.stdout!r} {first.stderr!r}")

        # REAL-CLEAN: a second `register` for the SAME role, real served `led`, no proxy --
        # must correctly REFUSE via JC4 because the existing row is SEEN, not hidden.
        second_file = tmpdir / "CHARTER-v2.md"
        second_file.write_text("# editor charter v2\n\nalso fixture only.\n", encoding="utf-8")
        r_clean = subprocess.run(
            [sys.executable, str(ROLE_CHARTER), "register", ROLE_NAME, str(second_file),
             "--led", real_led, "--scan-limit", SCAN_LIMIT],
            capture_output=True, text=True)
        clean_jc4 = "already carries an in-force charter registration" in r_clean.stderr
        clean_no_register = "role_charter: registered" not in r_clean.stdout
        check("REAL-CLEAN-existing-registration-correctly-refused-real-infra",
              r_clean.returncode == 1 and clean_jc4 and clean_no_register,
              f"exit={r_clean.returncode} names-existing-registration={clean_jc4} "
              f"no-registration-written={clean_no_register} (real scratch world, real served "
              f"led, no proxy)")

        # REAL-CORRUPTED: same world, read through corrupt_led_proxy.py, which corrupts the ONE
        # current-line naming this role's real charter registration.
        r_corrupt = subprocess.run(
            [sys.executable, str(ROLE_CHARTER), "register", ROLE_NAME, str(second_file),
             "--led", str(PROXY), "--scan-limit", SCAN_LIMIT],
            capture_output=True, text=True,
            env={**os.environ, "REAL_LED": real_led,
                 "CORRUPT_MATCH": f"role-charter registered: role={ROLE_NAME}"})
        corrupt_refused = ("REFUSED -- SHAPE DRIFT" in r_corrupt.stderr
                            and "does not match the expected `[id] kind: statement` shape"
                            in r_corrupt.stderr
                            and f"current {SCAN_LIMIT}" in r_corrupt.stderr
                            and "TRUNCATED ROW" in r_corrupt.stderr)
        corrupt_no_register = "role_charter: registered" not in r_corrupt.stdout
        check("REAL-CORRUPTED-refuses-loudly-real-infra",
              r_corrupt.returncode == 1 and corrupt_refused and corrupt_no_register,
              f"exit={r_corrupt.returncode} names-shape-drift={corrupt_refused} "
              f"no-registration-written={corrupt_no_register} (real scratch world, real served "
              f"led underneath, one current-line corrupted by the proxy on top of the real row)\n"
              f"  stderr={r_corrupt.stderr.strip()!r}")
    except BaseException as exc:  # noqa: BLE001 -- last-resort net, this fixture class's own
        # convention: an uncaught exception must not leak the boundary_service subprocess or the
        # scratch schema.
        crashed_with = exc
        FAILURES.append(f"UNCAUGHT EXCEPTION mid-fixture: {exc!r}")
        print(f"\n!! UNCAUGHT EXCEPTION mid-fixture -- {exc!r} -- reaping server and dropping "
              f"scratch before re-raising")
    finally:
        if proc is not None:
            bs_fixtures.stop_server(proc)

    if crashed_with is not None:
        _drop_scratch()
        shutil.rmtree(tmpdir, ignore_errors=True)
        print("role-charter-current-line-shape-drift-real: crashed -- server reaped, scratch "
              "dropped")
        raise crashed_with

    _drop_scratch()
    shutil.rmtree(tmpdir, ignore_errors=True)

    if FAILURES:
        print(f"role-charter-current-line-shape-drift-real: {len(FAILURES)} case(s) FAILED: "
              f"{FAILURES}")
        return 1
    print("all role-charter-current-line-shape-drift-real cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
