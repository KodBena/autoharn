#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof that `pickup` fails LOUDLY and TYPED against a served
boundary that is down or refusing, never silent-empty (tracker item
`pickup-connection-failure-silent-empty`, originally 2026-07-13; RETARGETED 2026-07-27 at the
LIVE surface per ledger row 1471 ruling 4a).

RETARGET, HONESTLY NAMED (ledger rows 1464/1471): this file used to test `bootstrap/templates/
pickup.tmpl` as it stood BEFORE the served-boundary CLI rebase (design/FABLE-BOUNDARY-MULTIPLEX-
AND-CLI-REBASE-SPEC.md §5 / design/FABLE-BOUNDARY-READ-SURFACE-SPEC.md) -- a direct-psql script
with its own `check_connectivity(dep) -> (ok, err)` probe. That rebase renamed the direct-psql
original to `legacy-pickup.tmpl` and gave `bootstrap/templates/pickup.tmpl` (the name every
`--new-world` scaffold's `./autoharn pickup` now actually reaches) a completely different shape:
an HTTP client against `serving/boundary_service.py` via `serving/boundary_cli_client.py`. Row
1464 found this fixture's OWN scaffold had ALSO gone stale independently (its `--new-world` call
never stood up a served boundary at all, so even the setup step -- a `led decision` write to seed
case b's control row -- failed with `capability_absent` before any case ran). Row 1471 ruling 4a:
"current pickup against a down/refusing served boundary must fail loudly and typed, never
silent-empty; legacy-pickup.tmpl is not guarded" -- so this file now tests the CURRENT
`bootstrap/templates/pickup.tmpl` (the one every real world actually runs) end to end, real infra,
never mocked, and explicitly does NOT touch `legacy-pickup.tmpl` at all (out of ruling 4a's own
scope).

THE FINDING, READ FROM SOURCE BEFORE WRITING THIS FIXTURE (not assumed): the current
`bootstrap/templates/pickup.tmpl` is ALREADY loud and typed on every "cannot even talk to the
boundary" shape -- this is confirmed empirically below, not a defect this file exists to catch.
Its `_load_config()` calls `serving/boundary_cli_client.py`'s `check_protocol_version()` before
issuing ANY real read; a boundary that is down raises `BoundaryUnreachable` (exit code 4, per
that module's own documented EXIT-CODE CONVENTION), a boundary that answers but refuses (a typed
HTTP 4xx/408/413/422/429/503/409 shape) raises `BoundaryRefusal` (exit code 3); `main()`'s own
`/health` check (the FIRST live call after config load) maps a `BoundaryRefusal` there to a
`CANNOT-HYDRATE` stderr banner + exit 3, matching the ORIGINAL pre-rebase fix's own vocabulary
one level up the stack. Both paths write to stderr and exit nonzero BEFORE any section is ever
printed -- there is no code path that prints a per-section "ERROR:" banner while still exiting 0
the way the original 2026-07-13 defect did. `serving/boundary_cli_client.py`'s own module
docstring names this a RATIFIED CLI contract (never exit 2, that range is reserved for the
legacy psql tools specifically so a caller can never confuse the two tools' failure codes) --
this fixture's job is to WITNESS that contract holds for pickup specifically, not to re-derive
it.

Cases:
  a-boundary-down-is-loud-typed  -- `./autoharn pickup` (via the SAME `deployment.json` a real
                                 `--new-world` scaffold writes, boundary_url REPOINTED at a
                                 closed local port -- genuine ECONNREFUSED, no server there at
                                 all) -> exit 4, stdout EMPTY, stderr names BOUNDARY UNREACHABLE
                                 (`report_boundary_exception`'s own text) and the bad port.
  b-good-boundary-control        -- the SAME world, boundary_url pointed at the REAL served
                                 boundary this fixture stood up -> exit 0, real section content
                                 (the IN-FORCE-DECISIONS row this fixture wrote via a real
                                 `led decision` through the same served boundary), proving case
                                 a's failure is genuinely caused by the down boundary, not an
                                 unrelated defect.
  c-boundary-refusing-is-loud-typed -- the SAME real, UP boundary, but `boundary_deployment`
                                 (the `/d/{name}` segment) repointed at a deployment name the
                                 boundary has never heard of -> a typed HTTP refusal
                                 (`unknown_deployment`), `BoundaryRefusal`, main()'s own /health
                                 check maps this to exit 3, CANNOT-HYDRATE, stdout EMPTY -- the
                                 SECOND polarity of "loud, never silent": a boundary that IS
                                 reachable but refuses is not conflated with one that is down
                                 (distinct exit codes, both loud).
  d-function-level-proof         -- direct, in-process proof that `serving/boundary_cli_client.
                                 py`'s own `check_protocol_version()` raises `BoundaryUnreachable`
                                 against the closed port and returns cleanly against the real
                                 served boundary -- the function-level fix, not just the whole-
                                 script exit code (mirrors this family's ORIGINAL case c, ported
                                 onto the current API -- `check_connectivity()` no longer exists
                                 in the rebased `pickup.tmpl`; this is its honest successor).
  e-genuine-section-absence-not-conflated -- the OTHER polarity, ported from the original file's
                                 case d: a scratch world whose kernel PREDATES
                                 kernel/lineage/s36-decision-grade.sql (no standing-decisions
                                 capability yet) but whose BOUNDARY is fully up and healthy ->
                                 `./autoharn pickup` still exits 0 (the boundary itself answered
                                 fine), STANDING-DECISIONS reports its own honest
                                 capability-absent note (pickup.tmpl's own `standing_decisions()`
                                 catches exactly this 409 locally and returns, per source read
                                 above), and NO CANNOT-HYDRATE banner appears anywhere -- proving
                                 a genuine per-VIEW capability absence is still never conflated
                                 with a down/refusing BOUNDARY, the same non-conflation guarantee
                                 the original 2026-07-13 fix proved for a per-SECTION SQL-level
                                 absence.

NOT FIXED HERE, BY DESIGN (ruling 4a, verbatim): `legacy-pickup.tmpl` is not guarded by this
file -- it is the SAME direct-psql tool the original 2026-07-13 fix (commit-era, `check_
connectivity()`) already hardened, and ledger row 1464 explicitly named it out of THIS
retarget's scope ("legacy-pickup.tmpl is not guarded").

Usage: python3 seen-red/pickup-connection-failure-silent-empty/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Real infra throughout: one throwaway `--new-world`
scaffold, a REAL `serving.boundary_service` stood up over it (reusing `seen-red/boundary-service/
run_fixtures.py`'s own `serve_existing_world`/`stop_server`/`free_port`, never re-derived), and a
second throwaway classic-scaffold-plus-manual-chain world capped before s36 for case e -- both
torn down (in `finally`) before and after. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # seen-red/, for _fixture_env
from _fixture_env import fixture_pghost  # noqa: E402 (filing/pghost_resolve.py via seen-red/_fixture_env.py -- never a literal host default)

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
PICKUP_TMPL = REPO / "bootstrap" / "templates" / "pickup.tmpl"
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "serving"))
sys.path.insert(0, str(REPO / "filing"))
import boundary_cli_client as bcc  # noqa: E402
import deployment_record  # noqa: E402

# REUSE (ADR-0012 P1), the corpus's own shared idiom (seen-red/s26-row-hash-chain-deletion/
# run_fixtures.py's own precedent for importing this sibling family by path).
_BS_SPEC = importlib.util.spec_from_file_location(
    "boundary_service_fixtures", REPO / "seen-red" / "boundary-service" / "run_fixtures.py")
assert _BS_SPEC is not None and _BS_SPEC.loader is not None
bs_fixtures = importlib.util.module_from_spec(_BS_SPEC)
sys.modules["boundary_service_fixtures"] = bs_fixtures
_BS_SPEC.loader.exec_module(bs_fixtures)

PGHOST, PGDB = fixture_pghost(), "toy"
WORLD = "pcfsxprobe"
PRES36_SCHEMA, PRES36_KERN, PRES36_ROLE = "pcfsxpres36", "pcfsxpres36_kernel", "pcfsxpres36_rw"

# The full current lineage up to (but not including) s36-decision-grade.sql -- case e's own
# deliberately-capped era witness (proving a genuine per-view capability absence, NOT a down
# boundary). This list is NOT the s43 cascade gap this commission migrates every OTHER family
# away from: case e's whole POINT is to be missing a capability, on purpose, so it must stay
# capped -- but the served BOUNDARY itself only needs the schema/kern/role to exist and be
# readable, not any particular generation, so this scratch world's `led`/write path is never
# exercised (case e only ever GETs from it) and s43's write-boundary/INSERT-revoke concerns do
# not apply here at all.
PRE_S36_CHAIN = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown_all() -> None:
    for schema, kern, role in ((WORLD, f"{WORLD}_kernel", f"{WORLD}_rw"),
                                (PRES36_SCHEMA, PRES36_KERN, PRES36_ROLE)):
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
            f"DROP OWNED BY {role};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def closed_port() -> int:
    """A port number guaranteed to have NOTHING listening: bind, read back the OS-assigned free
    port, then close immediately -- the same technique `seen-red/boundary-service/run_fixtures.
    py`'s own `free_port()` uses, but here the point is the port stays CLOSED afterward (a
    subsequent connect gets a fast, genuine ECONNREFUSED), not that it gets served."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_pickup(deployment_path: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(deployment_path)
    return sh(["python3", str(PICKUP_TMPL)], env=env, cwd=str(REPO))


def main() -> int:
    teardown_all()
    tmp = Path(tempfile.mkdtemp(prefix="pcfs-seenred-"))
    world_dir = tmp / WORLD
    failures: list[str] = []
    proc = None

    try:
        # --- scaffold the real --new-world (full chain) + stand a REAL served boundary --------
        print(f"== scaffolding throwaway --new-world {WORLD} ==")
        r = sh(["bash", str(NEW_PROJECT), str(world_dir), "--new-world", WORLD,
                "--db", PGDB, "--host", PGHOST])
        if r.returncode != 0:
            print("SCAFFOLD FAILED:", r.stdout[-1500:], r.stderr[-1500:])
            return 1
        for verb in ("autoharn",):
            p = world_dir / verb
            if p.exists():
                p.chmod(0o755)
        proc = bs_fixtures.serve_existing_world(world_dir / "deployment.json", tmp)
        # From here on, any raise must not leak `proc` (closed review finding on the s26-deletion
        # family's own commit -- replicated here rather than re-derived).
        try:
            rl = sh(["bash", str(world_dir / "autoharn"), "led", "decision", "row one, via led"],
                    cwd=str(world_dir))
            if rl.returncode != 0:
                raise RuntimeError(f"led write FAILED: {rl.stdout} {rl.stderr}")

            good_dep = deployment_record.load_deployment(world_dir / "deployment.json")
            bad_port = closed_port()

            # --- a: boundary DOWN (closed port, genuine ECONNREFUSED) -> exit 4, loud, empty ---
            down_deployment = tmp / "deployment-boundary-down.json"
            deployment_record.write_deployment(down_deployment, deployment_record.DeploymentRecord(
                db=good_dep.db, host=good_dep.host, schema=good_dep.schema, kern=good_dep.kern,
                role=good_dep.role, name=good_dep.name,
                boundary_url=f"http://127.0.0.1:{bad_port}",
                boundary_deployment=good_dep.boundary_deployment))
            ra = run_pickup(down_deployment)
            ok_a = (ra.returncode == 4 and ra.stdout.strip() == ""
                    and "could not be reached" in ra.stderr
                    and "Connection refused" in ra.stderr)
            check("a-boundary-down-is-loud-typed", ok_a,
                  f"exit={ra.returncode} stdout={ra.stdout!r} stderr_excerpt={ra.stderr.strip()[:300]!r}",
                  failures)

            # --- b: control -- the SAME world, the REAL served boundary, hydrates fully --------
            rb = run_pickup(world_dir / "deployment.json")
            ok_b = (rb.returncode == 0 and "### SECTION: IN-FORCE-DECISIONS" in rb.stdout
                    and "row one, via led" in rb.stdout and "CANNOT-HYDRATE" not in rb.stdout
                    and rb.stderr.strip() == "")
            check("b-good-boundary-control", ok_b,
                  f"exit={rb.returncode} has_row={'row one, via led' in rb.stdout} "
                  f"stderr={rb.stderr.strip()[:200]!r}", failures)

            # --- c: boundary UP but REFUSES (unknown /d/{name} segment) -> exit 3, loud, empty -
            unknown_deployment = tmp / "deployment-boundary-refuses.json"
            deployment_record.write_deployment(unknown_deployment, deployment_record.DeploymentRecord(
                db=good_dep.db, host=good_dep.host, schema=good_dep.schema, kern=good_dep.kern,
                role=good_dep.role, name=good_dep.name, boundary_url=good_dep.boundary_url,
                boundary_deployment="pcfsx-nonexistent-deployment-name"))
            rc = run_pickup(unknown_deployment)
            # This refusal fires inside `_load_config()`'s own `check_protocol_version()` call --
            # BEFORE main()'s own explicit `/health` check ever runs -- so it surfaces through the
            # top-level `report_boundary_exception()` path ("REFUSED by the boundary SERVICE
            # itself"), not main()'s own "CANNOT-HYDRATE" banner text. Both are loud, typed,
            # distinct-from-exit-4 refusals; this case asserts on the ACTUAL text, not a guess.
            ok_c = (rc.returncode == 3 and rc.stdout.strip() == ""
                    and "REFUSED by the boundary SERVICE itself" in rc.stderr
                    and "unknown_deployment" in rc.stderr)
            check("c-boundary-refusing-is-loud-typed", ok_c,
                  f"exit={rc.returncode} stdout={rc.stdout!r} stderr_excerpt={rc.stderr.strip()[:300]!r}",
                  failures)

            # --- d: function-level proof, check_protocol_version() itself ---------------------
            good_base = f"{good_dep.boundary_url}/d/{good_dep.boundary_deployment}"
            raised_bad = False
            try:
                bcc.check_protocol_version(f"http://127.0.0.1:{bad_port}/d/{good_dep.boundary_deployment}",
                                           f"http://127.0.0.1:{bad_port}")
            except bcc.BoundaryUnreachable:
                raised_bad = True
            raised_good = False
            try:
                bcc.check_protocol_version(good_base, good_dep.boundary_url)
            except bcc.BoundaryUnreachable:
                raised_good = True
            ok_d = raised_bad and not raised_good
            check("d-function-level-proof", ok_d,
                  f"raised on closed port={raised_bad} (expected True), "
                  f"raised on real boundary={raised_good} (expected False)", failures)

        finally:
            bs_fixtures.stop_server(proc)
            proc = None

        # --- e: genuine per-view capability absence, boundary itself fully up -----------------
        print(f"== applying s15..s35 (NOT s36) to {PRES36_SCHEMA}, standing a REAL boundary ==")
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"CREATE ROLE {PRES36_ROLE} LOGIN;"])
        args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
                "-v", f"schema={PRES36_SCHEMA}", "-v", f"kern={PRES36_KERN}", "-v", f"role={PRES36_ROLE}"]
        for f in PRE_S36_CHAIN:
            args += ["-f", str(LINEAGE / f)]
        rap = sh(args)
        if rap.returncode != 0:
            print("PRE-S36 APPLY FAILED:", rap.stdout[-1500:], rap.stderr[-1500:])
            return 1
        pres36_dep_path = tmp / f"{PRES36_SCHEMA}-deployment.json"
        deployment_record.write_deployment(pres36_dep_path, deployment_record.DeploymentRecord(
            db=PGDB, host=PGHOST, schema=PRES36_SCHEMA, kern=PRES36_KERN, role=PRES36_ROLE,
            name=PRES36_SCHEMA))
        proc_e = bs_fixtures.serve_existing_world(pres36_dep_path, tmp)
        try:
            re_ = run_pickup(pres36_dep_path)
            ok_e = (re_.returncode == 0 and "CANNOT-HYDRATE" not in re_.stdout
                    and "CANNOT-HYDRATE" not in re_.stderr
                    and "no standing decisions to show" in re_.stdout
                    and "kernel/lineage/s36-decision-grade.sql" in re_.stdout)
            check("e-genuine-section-absence-not-conflated", ok_e,
                  f"exit={re_.returncode} stdout_excerpt={re_.stdout[:400]!r} "
                  f"stderr={re_.stderr.strip()[:200]!r}", failures)
        finally:
            bs_fixtures.stop_server(proc_e)

    finally:
        if proc is not None:
            bs_fixtures.stop_server(proc)
        teardown_all()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- pickup-connection-failure-silent-empty RETARGETED at the live served-"
          "boundary surface (ledger row 1471 ruling 4a): boundary-down is loud+typed (exit 4, "
          "empty stdout) / good-boundary control still hydrates fully / boundary-up-but-refusing "
          "is loud+typed too (exit 3, empty stdout, distinct from exit 4) / check_protocol_"
          "version() itself proven at the function level / a genuine per-view capability absence "
          "on a fully-healthy boundary is never conflated with a down/refusing boundary -- "
          "current pickup.tmpl was ALREADY loud on every one of these shapes (confirmed by "
          "running it, not assumed), so nothing in pickup.tmpl itself needed fixing; "
          "legacy-pickup.tmpl is explicitly out of this retarget's scope (ruling 4a), untouched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
