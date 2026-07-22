#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s34-computed-grade-refusal.sql
(ledger item discharge-grade-refuse-if-supplied, claimed by the orchestrator; refinement-consult
finding, ledger row 1157). Real infra, no mocks: CLASSIC-mode scaffolds (explicit
--schema/--kern/--role, no automatic kernel apply -- s30/s31/s32/s33's own scaffold_classic
idiom) followed by a MANUAL lineage apply in the TOY db, torn down before AND after so re-running
leaves no residue.

TWO worlds, deliberately:
  WORLD A -- CHAIN ends at s33 (s34 NOT applied). This is the PRE-s34 kernel the finding names --
             its own `validate_independence()` silently OVERWRITES a writer-supplied
             discharge_grade with no error. Case `pre-s34-silent-overwrite` witnesses this LIVE,
             on this pass, before s34 is ever applied to anything -- not asserted from the SQL
             text alone.
  WORLD B -- CHAIN ends at s34 (s33 + s34 applied). The red/green polarities live here.

Cases:
  pre-s34-silent-overwrite  -- WORLD A: a writer-supplied discharge_grade ('distinct-deployment')
                               on a review_detail INSERT is accepted with NO error and silently
                               replaced by the kernel's own computation -- the bug this delta
                               closes, witnessed live on an s33-head scratch world.
  red-refused-with-teach    -- WORLD B: the SAME writer-supplied-grade INSERT is REFUSED; the
                               teach-text names the field as kernel-computed and cites the
                               pre-s34 silent-overwrite behavior (ledger finding 1157) as the WHY;
                               no row lands in review_detail.
  green-computed-unchanged  -- WORLD B: a normal review INSERT (discharge_grade left NULL, the
                               CLI's own shape) computes a grade; that computed value is BYTE-
                               IDENTICAL to the grade WORLD A computes on the same-shaped inputs
                               (same-principal, no interception stamp present in this fixture) --
                               the computed-default path is unchanged by this delta.
  allowlist-gate-unaffected -- gates/ledger_reader_allowlist.py stays green on WORLD B's chain
                               (validate_independence's existing ALLOWLIST entry covers the
                               re-issued function; no new raw-ledger reader is introduced).
  differential-agree-both-layers -- the STANDING `./judge` differential (engine/
                               ledger_differential.run_differential for 'tnow',
                               run_layer_differential for 'work') AGREEs on WORLD B, both layers
                               -- s34 introduces no ASP-modeled predicate (discharge_grade/
                               independence are not engine atoms), so this proves the refusal-only
                               change disturbs neither layer's parity.

Usage: python3 seen-red/s34-computed-grade-refusal/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
GATE = REPO / "gates" / "ledger_reader_allowlist.py"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import ledger_differential  # noqa: E402  (engine/ledger_differential.py)
import ledger_edb  # noqa: E402  (engine/ledger_edb.py -- export)
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_COMMON = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s28-work-parent-edge.sql",
    "s29-obligation-item-key-and-typed-close.sql", "s30-typed-dependency-edges.sql",
    "s31-supersession-uniform-retraction.sql", "s32-edge-views-single-home.sql",
    "s33-composite-discharge.sql",
]
CHAIN_A = CHAIN_COMMON  # WORLD A: pre-s34 (s33 head)
CHAIN_B = CHAIN_COMMON + ["s34-computed-grade-refusal.sql"]  # WORLD B: s34 applied


def sh(args: list[str], **kw) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def teardown(world: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "  # declared-drop: scratch reset
        f"DROP OWNED BY {world}_rw;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {world}_rw;"])


def led(world_dir: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    e = dict(os.environ)
    if env:
        e.update(env)
    return sh(["bash", str(world_dir / "led"), *args], cwd=str(world_dir), env=e)


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(sql: str) -> subprocess.CompletedProcess[str]:
    """A statement allowed to FAIL (the red-polarity probe) -- caller inspects returncode/stderr."""
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c", sql])


def scaffold_classic(world: str, chain: list[str]) -> Path:
    """CLASSIC MODE + manual apply of the given CHAIN (s30/s31/s32/s33's own scaffold_classic
    idiom). s34 is deliberately NOT in new-project.sh's LINEAGE_CHAIN (this commission's own
    instruction: "Do NOT wire LINEAGE_CHAIN"), so classic+manual is the honest wiring for both
    worlds this fixture builds."""
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    for verb in ("led", "judge", "pickup"):
        p = world_dir / verb
        if p.exists():
            p.chmod(0o755)
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}, chain ends {chain[-1]}): "
                           f"{ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    secret_dir = world_dir / ".claude" / "secrets"
    secret_dir.mkdir(parents=True, exist_ok=True)
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    (secret_dir / "stamp_secret.hex").write_text(hexsecret + "\n", encoding="utf-8")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def make_target_row(world_dir: Path, schema: str, tag: str) -> str:
    """A plain decision row (kind='decision') for a review to regard, distinct per case."""
    led(world_dir, "decision", f"target row for {tag} -- s34 fixture, not a real project decision")
    return psql_tuples(
        f"SELECT id FROM {schema}.ledger WHERE kind='decision' "
        f"AND statement LIKE 'target row for {tag}%' ORDER BY id DESC LIMIT 1;")


def raw_review_insert(schema: str, role: str, target_id: str, actor_name: str,
                      basis: str, discharge_grade: str | None) -> subprocess.CompletedProcess[str]:
    """A direct SQL writer against ledger+review_detail (the class the finding names: `GRANT
    INSERT` on review_detail has stood since s15; a writer with direct table access -- never the
    CLI, which never names discharge_grade in its own column list -- can supply the column). Runs
    as a single multi-statement script under ON_ERROR_STOP=1 so a REFUSAL on the review_detail
    INSERT aborts the whole script (including the ledger INSERT) -- exactly what a real
    transactional writer would experience."""
    grade_sql = "NULL" if discharge_grade is None else f"'{discharge_grade}'"
    script = f"""
SET ROLE {role};
SET search_path = {schema}, {schema}_kernel;
BEGIN;
INSERT INTO {schema}.ledger (kind, statement, regards, actor)
VALUES ('review', 'raw-writer review -- s34 fixture', {target_id},
        (SELECT id FROM principal WHERE name = '{actor_name}'))
RETURNING id \\gset r_
INSERT INTO {schema}.review_detail (ledger_id, verdict, independence, basis, discharge_grade)
VALUES (:r_id, 'attest', 'self-review', '{basis}', {grade_sql});
COMMIT;
"""
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


def read_discharge_grade(schema: str, basis_like: str) -> str:
    return psql_tuples(
        f"SELECT discharge_grade FROM {schema}.review_detail WHERE basis LIKE '{basis_like}%' "
        f"ORDER BY ledger_id DESC LIMIT 1;")


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    world_a, world_b = "s34fxa", "s34fxb"
    teardown(world_a)
    teardown(world_b)
    try:
        # =========================================================================================
        # WORLD A -- pre-s34 (s33 head). Witnesses the live silent-overwrite bug.
        # =========================================================================================
        print(f"== scaffolding classic world {world_a} (chain ends {CHAIN_A[-1]}, s34 NOT applied) ==")
        world_dir_a = scaffold_classic(world_a, CHAIN_A)
        tmps.append(world_dir_a.parent)
        print(f"  scaffold OK (schema={world_a}).\n")
        led(world_dir_a, "register-principal", "reviewer2", "model")

        target_a1 = make_target_row(world_dir_a, world_a, "pre-s34-bug")
        rp = raw_review_insert(world_a, f"{world_a}_rw", target_a1, "reviewer2",
                               "pre-s34 silent overwrite specimen", "distinct-deployment")
        stored_grade = read_discharge_grade(world_a, "pre-s34 silent overwrite specimen")
        ok_bug = (rp.returncode == 0 and stored_grade != "distinct-deployment"
                 and stored_grade == "same-principal")
        check("pre-s34-silent-overwrite", ok_bug,
              f"raw INSERT supplying discharge_grade='distinct-deployment' exit={rp.returncode} "
              f"(0 = accepted, no error) stored discharge_grade={stored_grade!r} -- the writer's "
              f"asserted value was silently discarded and replaced, no error surfaced anywhere "
              f"(ledger finding 1157, witnessed live on this s33-head world before s34 exists)",
              failures)

        # -- WORLD A's own normal (no-assertion) computed grade, for the green case's comparison --
        target_a2 = make_target_row(world_dir_a, world_a, "normal-a")
        rn_a = raw_review_insert(world_a, f"{world_a}_rw", target_a2, "reviewer2",
                                 "normal review basis A", None)
        grade_a = read_discharge_grade(world_a, "normal review basis A")
        if rn_a.returncode != 0:
            raise RuntimeError(f"WORLD A normal review insert unexpectedly failed: "
                               f"{rn_a.stdout[-500:]} {rn_a.stderr[-500:]}")

        # =========================================================================================
        # WORLD B -- s33 + s34. Red/green polarities.
        # =========================================================================================
        print(f"== scaffolding classic world {world_b} (chain ends {CHAIN_B[-1]}, s34 APPLIED) ==")
        world_dir_b = scaffold_classic(world_b, CHAIN_B)
        tmps.append(world_dir_b.parent)
        print(f"  scaffold OK (schema={world_b}).\n")
        led(world_dir_b, "register-principal", "reviewer2", "model")

        # --- red: writer-supplied grade REFUSED, teach-text witnessed --------------------------
        target_b1 = make_target_row(world_dir_b, world_b, "red-case")
        rr = raw_review_insert(world_b, f"{world_b}_rw", target_b1, "reviewer2",
                               "red case basis", "distinct-deployment")
        out_r = rr.stdout + rr.stderr
        no_row = psql_tuples(
            f"SELECT count(*) FROM {world_b}.review_detail WHERE basis = 'red case basis';")
        ok_red = (rr.returncode != 0 and "COMPUTED by the kernel" in out_r
                 and "ledger finding 1157" in out_r and "distinct-deployment" in out_r
                 and no_row == "0")
        check("red-refused-with-teach", ok_red,
              f"raw INSERT supplying discharge_grade='distinct-deployment' exit={rr.returncode} "
              f"(nonzero = refused) rows_landed={no_row} teach_names_computed="
              f"{'COMPUTED by the kernel' in out_r} teach_cites_finding="
              f"{'ledger finding 1157' in out_r} excerpt={out_r.strip()[-400:]!r}",
              failures)

        # --- green: normal review INSERT computes the grade exactly as before -------------------
        target_b2 = make_target_row(world_dir_b, world_b, "normal-b")
        rn_b = raw_review_insert(world_b, f"{world_b}_rw", target_b2, "reviewer2",
                                 "normal review basis A", None)
        grade_b = read_discharge_grade(world_b, "normal review basis A")
        ok_green = (rn_b.returncode == 0 and grade_a != "" and grade_b == grade_a)
        check("green-computed-unchanged", ok_green,
              f"WORLD A (pre-s34) computed discharge_grade={grade_a!r}; WORLD B (post-s34) "
              f"computed discharge_grade={grade_b!r} on the SAME-shaped input (no stamp present, "
              f"distinct actor, self-review) -- byte-identical: {grade_a == grade_b}", failures)

        # --- allowlist gate stays green on WORLD B's chain ---------------------------------------
        gg = sh([sys.executable, str(GATE)])
        ok_gate = gg.returncode == 0
        check("allowlist-gate-unaffected", ok_gate,
              f"gates/ledger_reader_allowlist.py exit={gg.returncode} on its own standing CHAIN "
              f"(validate_independence's existing ALLOWLIST entry covers the re-issued function; "
              f"s34 introduces no new raw-ledger reader, so no CHAIN change was needed)",
              failures)

        # --- STANDING differential AGREE, both layers, on WORLD B ---------------------------------
        os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = \
            PGDB, world_b, f"{world_b}_kernel"
        try:
            edb_text = ledger_edb.export(world_b).edb_text()
            res_tnow = ledger_differential.run_differential(world_b, edb_text=edb_text)
            res_work = ledger_differential.run_layer_differential(world_b, "work")
        finally:
            del os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"]
        v_tnow, v_work = res_tnow.verdict(), res_work.verdict()
        ok_diff = v_tnow == "AGREE" and v_work == "AGREE"
        check("differential-agree-both-layers", ok_diff,
              f"tnow verdict={v_tnow} work verdict={v_work} -- engine/ledger_differential's "
              f"run_differential (tnow) and run_layer_differential (work), the SAME code "
              f"`./judge` and `./judge --layer work` run, over WORLD B's real export (this "
              f"delta introduces no ASP-modeled predicate; discharge_grade/independence are not "
              f"engine atoms, so parity is expected and here witnessed, not merely asserted)",
              failures)

    finally:
        teardown(world_a)
        teardown(world_b)
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- s34 computed-grade-refusal both-polarity proof (pre-s34 silent "
          "overwrite witnessed live / post-s34 refusal with teach-text naming the WHY / "
          "computed-default path byte-identical pre vs post / allowlist gate unaffected / "
          "standing ./judge differential AGREE on both layers), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
