#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s27-chain-high-water.sql +
bootstrap/templates/verify-chain.tmpl's tail-deletion-witness comparison (tracker item
`s26-tail-deletion-witness`, decision row 192). Real infra, no mocks.

WHY this fixture exists, separately from seen-red/s26-row-hash-chain/ and
seen-red/s26-row-hash-chain-deletion/: those two prove the row_hash chain's own guarantees
(interior tamper detected; tail deletion structurally invisible to the chain ALONE, named as
residue). This fixture proves the residue s27 was built to close: an out-of-band, kernel-side
witness that DOES see a tail deletion, cannot itself be lowered by the subject role, and degrades
honestly (never a false SUSPECT, never a crash) on a world born before s27 existed.

Cases:
  a-intact-witness-agrees        -- a real --new-world scaffold (s27 in its birth chain), 4 rows
                                     written via `led`. `./verify-chain` reports INTACT AND
                                     TAIL-COVERAGE-CONFIRMED (witness max_id == walked max_id),
                                     exit 0. The "clean world passes" polarity.
  b-tail-deletion-suspect        -- the tail row (highest surviving id) is DELETED OUTRIGHT
                                     (trigger bypassed, mirroring a schema-owner-level DELETE --
                                     the exact attack seen-red/s26-row-hash-chain-deletion/'s case
                                     c proved invisible to the row_hash chain alone).
                                     `./verify-chain` now reports TAIL-DELETION-SUSPECT (witness
                                     AHEAD of the walked max), exit 3 -- distinct from BROKEN's
                                     exit 1, so a caller can tell "interior tamper" from "tail
                                     truncation" without parsing prose.
  c-head-refuses-on-suspect      -- `./verify-chain --head` against the tail-deleted world from
                                     case b refuses (exit 1, EMPTY stdout) rather than signing a
                                     head over a chain the witness itself flags -- the same
                                     posture the BROKEN row_hash case already has, extended to the
                                     gap that case never covered.
  d-role-cannot-lower-witness    -- connected AS THE GRANTED SUBJECT ROLE (`:role`), a direct
                                     `UPDATE kern.chain_high_water SET max_id = 0` is REFUSED
                                     (`permission denied`) -- the commission's own named hazard,
                                     witnessed live, not merely argued from the GRANT statements.
  e-role-cannot-delete-witness   -- same role, a direct `DELETE FROM kern.chain_high_water` is
                                     likewise REFUSED -- the witness cannot be erased either, only
                                     read.
  f-rollback-does-not-bump       -- an INSERT immediately ROLLED BACK leaves the witness
                                     UNCHANGED -- proving the trigger's bump is genuinely
                                     transactional (the PRIMARY reason this delta's ratified shape
                                     is a table bumped in-transaction rather than a bare sequence
                                     comparison, whose `nextval()` is NOT transactional and would
                                     have advanced anyway, per this delta's own header).
  g-pre-s27-degrades-honestly    -- a schema carrying s15..s26 but NOT s27 (the lineage as it
                                     existed before this commission): `./verify-chain` reports
                                     WITNESS-UNAVAILABLE, exit 0 -- never a false SUSPECT, never a
                                     crash, on a world this delta was never applied to.
  h-differential-agree           -- the EXISTING SQL/ASP marriage differential
                                     (`engine/ledger_differential.py`) still verdicts AGREE against
                                     the s27 scaffold world from case a, proving s27 does not
                                     perturb the existing T_now facts.

Usage: python3 seen-red/s27-chain-high-water/run_fixtures.py
Exit 0 if every case matches its EXPECTED outcome; 1 otherwise. Lazy imports banned.
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
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
VERIFY_CHAIN_TMPL = REPO / "bootstrap" / "templates" / "verify-chain.tmpl"
LINEAGE = REPO / "kernel" / "lineage"

PGHOST, PGDB = fixture_pghost(), "toy"
WORLD = "s27fxprobe"
PRE27_SCHEMA, PRE27_KERN, PRE27_ROLE = "s27fxpre27", "s27fxpre27_kernel", "s27fxpre27_rw"

CHAIN_TO_S26 = ["s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
                "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
                "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
                "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
                "s25-commission-kind.sql", "s26-row-hash-chain.sql"]


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
                                (PRE27_SCHEMA, PRE27_KERN, PRE27_ROLE)):
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
            f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE; "
            f"DROP OWNED BY {role};"])
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def run_verify_chain(world_dir: Path, *extra: str, dep_override: Path | None = None
                      ) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PICKUP_DEPLOYMENT"] = str(dep_override or (world_dir / "deployment.json"))
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
    """Bypasses append_only_row exactly as seen-red/s26-row-hash-chain-deletion/'s own
    delete_row() does -- mirroring a schema-owner-level DELETE."""
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"ALTER TABLE {schema}.ledger DISABLE TRIGGER append_only_row;"])
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"DELETE FROM {schema}.ledger WHERE id = {row_id};"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"ALTER TABLE {schema}.ledger ENABLE TRIGGER append_only_row;"])
    if r.returncode != 0:
        raise RuntimeError(f"DELETE FAILED on {schema}.ledger id={row_id}: {r.stdout} {r.stderr}")


def last_id(schema: str) -> str:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
               f"SELECT id FROM {schema}.ledger ORDER BY id DESC LIMIT 1;"]).stdout.strip()


def psql_as_role(role: str, schema: str, sql: str) -> subprocess.CompletedProcess[str]:
    prefix = f"SET ROLE {role};\nSET search_path = {schema};\n"
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-tA", "-q",
               "-c", prefix + sql])


def apply_lineage_no_s27(schema: str, kern: str, role: str) -> subprocess.CompletedProcess[str]:
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN_TO_S26:
        args += ["-f", str(LINEAGE / f)]
    return sh(args)


def main() -> int:
    teardown_all()
    tmp = Path(tempfile.mkdtemp(prefix="s27-seenred-"))
    failures: list[str] = []

    try:
        # --- scaffold the real --new-world (s27 in its birth chain automatically) ---------------
        world_dir = tmp / WORLD
        print(f"== scaffolding throwaway --new-world {WORLD} (4 rows; s27 applied automatically) ==")
        scaffold(world_dir, WORLD, 4)

        # --- a: intact chain, witness agrees -----------------------------------------------------
        ra = run_verify_chain(world_dir)
        ok_a = (ra.returncode == 0
                and ra.stdout.startswith("verify-chain: INTACT -- 4 row(s)")
                and "TAIL-COVERAGE-CONFIRMED" in ra.stdout
                and "witness max_id=4 agrees with walked max_id=4" in ra.stdout)
        check("a-intact-witness-agrees", ok_a, ra.stdout.strip(), failures)

        # --- f: rollback does not bump the witness (run BEFORE any tail deletion below, on the
        # same intact world, so the baseline for b/c is unaffected) ------------------------------
        before_witness = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                              f"SELECT max_id FROM {WORLD}_kernel.chain_high_water;"]).stdout.strip()
        rf_insert = psql_as_role(f"{WORLD}_rw", WORLD,
            "BEGIN; INSERT INTO ledger (kind, statement) VALUES "
            "('decision', 'row that will rollback'); ROLLBACK;")
        after_witness = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                             f"SELECT max_id FROM {WORLD}_kernel.chain_high_water;"]).stdout.strip()
        ok_f = (rf_insert.returncode == 0 and before_witness == "4" and after_witness == "4")
        check("f-rollback-does-not-bump", ok_f,
              f"witness before={before_witness!r} after-rolled-back-insert={after_witness!r} "
              f"(expect unchanged at 4 -- a rolled-back insert must not advance the witness, "
              f"the entire reason this delta's shape is a same-transaction trigger rather than a "
              f"bare sequence comparison)", failures)

        # --- d: role cannot lower the witness directly -------------------------------------------
        rd = psql_as_role(f"{WORLD}_rw", WORLD,
                           f"UPDATE {WORLD}_kernel.chain_high_water SET max_id = 0;")
        ok_d = rd.returncode != 0 and "permission denied" in (rd.stdout + rd.stderr)
        check("d-role-cannot-lower-witness", ok_d,
              f"exit={rd.returncode} stderr={(rd.stdout + rd.stderr).strip()[-160:]!r}", failures)

        # --- e: role cannot delete the witness row either -----------------------------------------
        re_ = psql_as_role(f"{WORLD}_rw", WORLD, f"DELETE FROM {WORLD}_kernel.chain_high_water;")
        ok_e = re_.returncode != 0 and "permission denied" in (re_.stdout + re_.stderr)
        check("e-role-cannot-delete-witness", ok_e,
              f"exit={re_.returncode} stderr={(re_.stdout + re_.stderr).strip()[-160:]!r}", failures)

        # --- confirm the witness is STILL 4 after d/e's refused attempts, before tampering below --
        post_de_witness = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc",
                               f"SELECT max_id FROM {WORLD}_kernel.chain_high_water;"]).stdout.strip()
        if post_de_witness != "4":
            check("d-e-witness-unchanged-after-refused-attempts", False,
                  f"witness={post_de_witness!r}, expected 4 -- a refused UPDATE/DELETE must not "
                  f"have partially applied", failures)

        # --- b: delete the tail row (id=4), verify-chain reports TAIL-DELETION-SUSPECT -----------
        tail_id = last_id(WORLD)
        delete_row(WORLD, tail_id)
        rb = run_verify_chain(world_dir)
        ok_b = (rb.returncode == 3
                and "TAIL-DELETION-SUSPECT" in rb.stdout
                and f"witness max_id={tail_id}" in rb.stdout
                and "walked max_id=3" in rb.stdout)
        check("b-tail-deletion-suspect", ok_b,
              f"deleted tail id={tail_id}: {rb.stdout.strip()}", failures)

        # --- c: --head refuses on the suspect chain, empty stdout ---------------------------------
        rc = run_verify_chain(world_dir, "--head")
        ok_c = (rc.returncode == 1 and rc.stdout.strip() == ""
                and "TAIL-DELETION-SUSPECT" in rc.stderr)
        check("c-head-refuses-on-suspect", ok_c,
              f"exit={rc.returncode} stdout={rc.stdout!r} stderr_excerpt={rc.stderr.strip()[:160]!r}",
              failures)

        # --- g: a pre-s27 world (s15..s26 only) degrades honestly to WITNESS-UNAVAILABLE ---------
        print(f"== applying s15..s26 (NOT s27) to {PRE27_SCHEMA} ==")
        rg_apply = apply_lineage_no_s27(PRE27_SCHEMA, PRE27_KERN, PRE27_ROLE)
        if rg_apply.returncode != 0:
            print("APPLY FAILED:", rg_apply.stdout[-1500:], rg_apply.stderr[-1500:])
            return 1
        genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
        sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
            f"INSERT INTO {PRE27_KERN}.chain_genesis (seed) VALUES ('{genesis_hex}') "
            f"ON CONFLICT (only_one) DO NOTHING;"])
        psql_as_role(f"{PRE27_ROLE}", PRE27_SCHEMA,
                     "INSERT INTO ledger (kind, statement) VALUES ('decision', 'only row, pre-s27');")
        pre27_dep = tmp / "pre27_deployment.json"
        pre27_dep.write_text(json.dumps({
            "name": PRE27_SCHEMA, "host": PGHOST, "db": PGDB,
            "schema": PRE27_SCHEMA, "kern": PRE27_KERN, "role": PRE27_ROLE}), encoding="utf-8")
        rg = run_verify_chain(world_dir, dep_override=pre27_dep)
        ok_g = (rg.returncode == 0
                and rg.stdout.startswith("verify-chain: INTACT -- 1 row(s)")
                and "witness UNAVAILABLE" in rg.stdout
                and "no chain_high_water witness" in rg.stdout)
        check("g-pre-s27-degrades-honestly", ok_g, rg.stdout.strip(), failures)

        # --- h: the EXISTING SQL/ASP marriage differential still AGREEs on the s27 world ---------
        rh = sh(["python3", "engine/ledger_differential.py", WORLD], cwd=str(REPO),
                 env={**os.environ, "LEDGER_DEPLOYMENT": str(world_dir / "deployment.json")})
        ok_h = rh.returncode == 0 and "DIFFERENTIAL GREEN" in rh.stdout
        check("h-differential-agree", ok_h, f"diff_ok={'DIFFERENTIAL GREEN' in rh.stdout}", failures)

    finally:
        teardown_all()
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s27 chain-high-water witness both-polarity proof (intact+agrees / "
          "rollback-does-not-bump / role-cannot-lower / role-cannot-delete / "
          "tail-deletion-suspect / head-refuses-on-suspect / pre-s27-degrades-honestly / "
          "differential-agree), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
