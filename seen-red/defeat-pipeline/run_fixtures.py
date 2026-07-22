#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for design/FABLE-DEFEAT-PIPELINE-SPEC.md's minimal
model-defeat pipeline (the spec's §12 witness plan W1-W11; W12's live leg is UNEXERCISED by
construction -- no s44 delta exists in this repository, RD-2's evidence-trigger not yet
reached). Real infra, no mocks: CLASSIC scaffolds + manual chain applies in the TOY db (the
exact pattern seen-red/s41-principal-bindings-and-relations/run_fixtures.py already banks),
torn down before and after. Never touches kernel/, bootstrap/, or any live world -- scratch
schema pairs only.

WORLDS:
  WORLD PRE -- chain ends at s40 (no s41): W9, the pre-s41 capability refusal.
  WORLD DF  -- chain ends at s41: W1 (defeat fires), W2 (the SPINE -- implicit lapse on grant
               withdrawal), W3 (resurrection on attestation supersession), W4 (cascade depth
               >=2), W5 (discharge, both SoD polarities), W6 (absence never defeats), W7's
               version-skip leg, W8 (the target-domain guard).
  WORLD MAL -- chain ends at s41, used ONCE: W7's malformed-v1 loud-refusal leg (a malformed
               candidate row poisons every later defeat-layer read on the SAME target -- see
               ledger_edb.py's candidate query, which reads every row regardless of
               supersession -- so it is isolated on its own throwaway world, never mixed into
               WORLD DF's other checks).
  WORLD DFC -- chain ends at s41, used ONCE: review finding F1's mismatch_attest/3 CONTENT
               witness (adjudication ledger row 1506) -- asserts the Grade ATOM crosses
               correctly on BOTH attestation arms (v1 real; s44-shaped typed arm via a
               scratch-only ALTER, since no s44 delta exists yet), isolated because it mutates
               the world's ledger schema (see world_mismatch_content_check's own docstring).
W10 (the MANDATED stratification negative control) and W11 (registry red) need NO database --
pure clingo / pure Python, run directly against this repo's engine/ modules.

Usage: python3 seen-red/defeat-pipeline/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
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
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import ledger_differential  # noqa: E402
import ledger_edb  # noqa: E402
import lp_registry  # noqa: E402
import pghost_resolve  # noqa: E402

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_COMMON = [
    "s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
    "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql",
]
CHAIN_A = CHAIN_COMMON  # s40 head -- pre-s41 (W9)
CHAIN_B = CHAIN_COMMON + ["s41-principal-bindings-and-relations.sql"]  # s41 head


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
        f"DROP SCHEMA IF EXISTS {world} CASCADE; DROP SCHEMA IF EXISTS {world}_kernel CASCADE; "
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


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"], input=script)


def scaffold_classic(world: str, chain: list[str]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix=f"{world}-seenred-"))
    world_dir = tmp / world
    schema, kern, role = world, f"{world}_kernel", f"{world}_rw"
    r = sh(["bash", str(NEW_PROJECT), str(world_dir),
            "--db", PGDB, "--host", PGHOST,
            "--schema", schema, "--kern", kern, "--role", role])
    if r.returncode != 0:
        raise RuntimeError(f"CLASSIC SCAFFOLD FAILED ({world}): {r.stdout[-1500:]} {r.stderr[-1500:]}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for name in chain:
        args += ["-f", str(LINEAGE / name)]
    ra = sh(args)
    if ra.returncode != 0:
        raise RuntimeError(f"CLASSIC apply FAILED ({world}): {ra.stdout[-1500:]} {ra.stderr[-1500:]}")
    hexsecret = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"TRUNCATE {kern}.stamp_secret;",
        "-c", f"INSERT INTO {kern}.stamp_secret (secret) VALUES (decode('{hexsecret}','hex'));"])
    genesis_hex = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1",
        "-c", f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis_hex}') "
              f"ON CONFLICT (only_one) DO NOTHING;"])
    return world_dir


def birth_acts(world: str) -> None:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    script = (
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_purpose)\n"
        f"VALUES ('principal_registered', 'author registered (fixture genesis exception)',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), 'fixture connection principal');\n"
        f"INSERT INTO ledger (kind, statement, actor, principal_subject, principal_db_role)\n"
        f"VALUES ('principal_standing_declared', 'role {R} -> author',\n"
        f"        (SELECT id FROM principal WHERE name='author'),\n"
        f"        (SELECT id FROM principal WHERE name='author'), '{R}');\n")
    r = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"], input=script)
    if r.returncode != 0:
        raise RuntimeError(f"birth acts failed ({world}): {r.stderr[-600:]}")


def row_id_last(world: str, kind: str, statement: str) -> int:
    """The id of the row this fixture JUST wrote (statement text is unique per fixture call)."""
    out = psql_tuples(
        f"SELECT id FROM {world}.ledger WHERE kind='{kind}' AND statement = $stmt${statement}$stmt$ "
        f"ORDER BY id DESC LIMIT 1;")
    return int(out)


def principal_id(world: str, name: str) -> int:
    return int(psql_tuples(f"SELECT id FROM {world}_kernel.principal WHERE name='{name}';"))


def grant_row_id(world: str, subject_pid: int, activity: str) -> int:
    return int(psql_tuples(
        f"SELECT row_id FROM {world}.principal_competences WHERE subject={subject_pid} "
        f"AND activity='{activity}' ORDER BY row_id DESC LIMIT 1;"))


def set_target(name: str, schema: str, kern: str) -> None:
    os.environ["LEDGER_DB"], os.environ["LEDGER_SCHEMA"], os.environ["LEDGER_KERN"] = PGDB, schema, kern


def clear_target() -> None:
    for k in ("LEDGER_DB", "LEDGER_SCHEMA", "LEDGER_KERN"):
        os.environ.pop(k, None)


def run_defeat(name: str):
    set_target(name, name, f"{name}_kernel")
    try:
        return ledger_differential.run_layer_differential(name, "defeat")
    finally:
        clear_target()


def attest_stmt(row: int, verdict: str, grade: str, tag: str, version: str = "v1") -> str:
    return (f"model-attestation {version} | row={row} | model=claude-x | grade={grade} "
            f"| expected=claude-y | verdict={verdict} | session=sess-{tag} "
            f"| basis=commit-sha | rebuttals=design/FABLE-OTEL-SENTRY-SPEC.md#7-the-standing-rebuttals")


def world_pre_check(failures: list[str], tmps: list[Path]) -> None:
    world = "s40dfp"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_A[-1]}) ==")
    wdir = scaffold_classic(world, CHAIN_A)
    tmps.append(wdir.parent)
    birth_acts(world)
    res = run_defeat(world)
    check("W9-pre-s41-refusal",
          res.verdict() == ledger_differential.QUARANTINED
          and "trust_grant" in (res.asp.quarantine or "") and res.sql.quarantine is not None,
          f"verdict={res.verdict()}; asp.quarantine={res.asp.quarantine!r}; "
          f"sql.quarantine={res.sql.quarantine!r}",
          failures)
    teardown(world)


def world_malformed_check(failures: list[str], tmps: list[Path]) -> None:
    world = "s41dfm"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_B[-1]}) ==")
    wdir = scaffold_classic(world, CHAIN_B)
    tmps.append(wdir.parent)
    birth_acts(world)
    r = led(wdir, "register-principal", "sentry", "tool", "--purpose", "sentry fixture",
            env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    r = led(wdir, "principal", "grant-competence", "sentry", "--activity", "model-identity-attestation",
            "--band", "n/a", "--basis", "fixture", env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    stmt = "malformed target row"
    r = led(wdir, "decision", stmt, env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    target = row_id_last(world, "decision", stmt)
    bad = attest_stmt(target, "MISMATCH", grade="not-a-real-grade", tag="w7bad")
    r = led(wdir, "verification", bad, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr  # the KIND-SHAPE checks accept it; P-5 is a
                                                    # SEMANTIC (defeat-layer) refusal, not a kernel one
    res = run_defeat(world)
    check("W7-malformed-loud-BOTH-sides",
          res.verdict() == ledger_differential.QUARANTINED
          and res.asp.quarantine is not None and res.sql.quarantine is not None,
          f"verdict={res.verdict()}; asp.quarantine={res.asp.quarantine!r}; "
          f"sql.quarantine={res.sql.quarantine!r}",
          failures)
    teardown(world)


def world_df_check(failures: list[str], tmps: list[Path]) -> None:
    world = "s41dfw"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_B[-1]}) ==")
    wdir = scaffold_classic(world, CHAIN_B)
    tmps.append(wdir.parent)
    birth_acts(world)
    S, K = world, f"{world}_kernel"

    r = led(wdir, "register-principal", "sentry", "tool", "--purpose", "model-identity sentry fixture",
            env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    sentry_pid = principal_id(world, "sentry")

    r = led(wdir, "principal", "grant-competence", "sentry", "--activity", "model-identity-attestation",
            "--band", "n/a", "--basis", "fixture grant 1", env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    grant1 = grant_row_id(world, sentry_pid, "model-identity-attestation")

    target_stmt = "target row for the defeat-pipeline witness"
    r = led(wdir, "decision", target_stmt, env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    target = row_id_last(world, "decision", target_stmt)

    # ---- W6: absence never defeats (grant exists, zero attestations yet) ----
    res = run_defeat(world)
    check("W6-absence-never-defeats",
          res.verdict() == "AGREE"
          and not any(a.startswith("model_defeated(") for a in res.asp.atoms)
          and f"credited({target})" in res.asp.atoms,
          f"verdict={res.verdict()}; model_defeated atoms="
          f"{[a for a in res.asp.atoms if a.startswith('model_defeated(')]}; "
          f"target credited={f'credited({target})' in res.asp.atoms}",
          failures)

    # ---- W4 setup: F1 enacts target, F2 enacts F1 (depth-2 cascade substrate) ----
    f1_stmt = "F1 enacts target (cascade depth-1)"
    r = led(wdir, "-e", str(target), "decision", f1_stmt, env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    f1 = row_id_last(world, "decision", f1_stmt)
    f2_stmt = "F2 enacts F1 (cascade depth-2)"
    r = led(wdir, "-e", str(f1), "decision", f2_stmt, env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    f2 = row_id_last(world, "decision", f2_stmt)

    # ---- W7 (version-skip leg): a v2-headered candidate is skipped, harmless ----
    v2_stmt = attest_stmt(target, "MISMATCH", grade="exact-command", tag="w7skip", version="v2")
    r = led(wdir, "verification", v2_stmt, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    res = run_defeat(world)
    check("W7-version-skip-harmless",
          res.verdict() == "AGREE" and not any(a.startswith("model_defeated(") for a in res.asp.atoms),
          f"verdict={res.verdict()}; model_defeated atoms="
          f"{[a for a in res.asp.atoms if a.startswith('model_defeated(')]}",
          failures)

    # ---- W1: defeat fires; W4: cascade at depth >=2 ----
    attest1 = attest_stmt(target, "MISMATCH", grade="exact-command", tag="w1")
    r = led(wdir, "verification", attest1, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    attest1_id = row_id_last(world, "verification", attest1)
    res = run_defeat(world)
    model_defeated = {a for a in res.asp.atoms if a.startswith("model_defeated(")}
    credited = {a for a in res.asp.atoms if a.startswith("credited(")}
    exposure = {a for a in res.asp.atoms if a.startswith("exposure_model(")}
    check("W1-defeat-fires",
          res.verdict() == "AGREE"
          and f"model_defeated({target},{attest1_id},{grant1})" in model_defeated
          and f"credited({target})" not in credited,
          f"verdict={res.verdict()}; model_defeated={sorted(model_defeated)}; "
          f"target credited={f'credited({target})' in credited}",
          failures)
    check("W4-cascade-depth-2",
          f"exposure_model({f1},{target})" in exposure and f"exposure_model({f2},{target})" in exposure,
          f"exposure_model atoms={sorted(exposure)}",
          failures)

    # ---- W5: discharge, both SoD polarities ----
    schema_q = world
    psql_raw(f"CREATE TABLE {schema_q}.support_affirm "
             f"(r bigint NOT NULL, dependent bigint NOT NULL, antecedent bigint NOT NULL);")
    # SoD-distinct discharge on (F1,target): the affirming row r is authored by sentry, F1 by author.
    r_note_stmt = "SoD-distinct affirmation that F1 survives target's defeat"
    r = led(wdir, "note", r_note_stmt, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    r_note = row_id_last(world, "note", r_note_stmt)
    psql_raw(f"INSERT INTO {schema_q}.support_affirm (r,dependent,antecedent) VALUES ({r_note},{f1},{target});")
    # SELF-affirmation on (F2,target): the affirming row r2 is authored by author, same as F2.
    r2_note_stmt = "SELF affirmation that F2 survives target's defeat (SoD violation expected)"
    r = led(wdir, "note", r2_note_stmt, env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    r2_note = row_id_last(world, "note", r2_note_stmt)
    psql_raw(f"INSERT INTO {schema_q}.support_affirm (r,dependent,antecedent) VALUES ({r2_note},{f2},{target});")
    res = run_defeat(world)
    undischarged = {a for a in res.asp.atoms if a.startswith("exposure_model_undischarged(")}
    exposure = {a for a in res.asp.atoms if a.startswith("exposure_model(")}
    check("W5-discharge-distinct-actor",
          res.verdict() == "AGREE"
          and f"exposure_model({f1},{target})" in exposure
          and f"exposure_model_undischarged({f1},{target})" not in undischarged,
          f"verdict={res.verdict()}; exposure_model_undischarged={sorted(undischarged)}",
          failures)
    check("W5-self-affirm-does-not-discharge",
          f"exposure_model_undischarged({f2},{target})" in undischarged,
          f"exposure_model_undischarged={sorted(undischarged)}",
          failures)

    # ---- W8: the target-domain guard (attest/grant rows are never a defeat target) ----
    guard1 = attest_stmt(attest1_id, "MISMATCH", grade="exact-command", tag="w8-attest-target")
    r = led(wdir, "verification", guard1, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    guard2 = attest_stmt(grant1, "MISMATCH", grade="exact-command", tag="w8-grant-target")
    r = led(wdir, "verification", guard2, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    res = run_defeat(world)
    model_defeated = {a for a in res.asp.atoms if a.startswith("model_defeated(")}
    check("W8-target-domain-guard",
          res.verdict() == "AGREE"
          and not any(a.startswith(f"model_defeated({attest1_id},") for a in model_defeated)
          and not any(a.startswith(f"model_defeated({grant1},") for a in model_defeated),
          f"verdict={res.verdict()}; model_defeated={sorted(model_defeated)}",
          failures)

    # ---- W2: the implicit lapse (THE SPINE) ----
    r = led(wdir, "principal", "withdraw-competence", "sentry", "--activity", "model-identity-attestation",
            "--supersedes", str(grant1), env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    res = run_defeat(world)
    model_defeated = {a for a in res.asp.atoms if a.startswith("model_defeated(")}
    credited = {a for a in res.asp.atoms if a.startswith("credited(")}
    exposure = {a for a in res.asp.atoms if a.startswith("exposure_model(")}
    w2_ok = (res.verdict() == "AGREE" and not model_defeated
             and f"credited({target})" in credited and not exposure)
    check("W2-implicit-lapse-THE-SPINE",
          w2_ok,
          f"verdict={res.verdict()}; model_defeated={sorted(model_defeated)}; "
          f"target credited={f'credited({target})' in credited}; exposure_model={sorted(exposure)}; "
          f"asp_atom_count={len(res.asp.atoms)}; sql_atom_count={len(res.sql.atoms)}; "
          f"only_asp={sorted(res.only_asp)}; only_sql={sorted(res.only_sql)} "
          f"-- ZERO per-row cleanup performed: no row was written, deleted, or edited between "
          f"W1's defeat and this re-run; only the grant's own withdrawal row exists.",
          failures)
    print("W2 FULL QUOTE (the spine, verbatim):")
    print(f"  verdict={res.verdict()}")
    print(f"  asp.atoms ({len(res.asp.atoms)}) = {sorted(res.asp.atoms)}")
    print(f"  sql.atoms ({len(res.sql.atoms)}) = {sorted(res.sql.atoms)}")
    print()

    # ---- W3: resurrection on attestation supersession (fresh grant) ----
    # attest1 (W1's original mismatch attestation) is still unsuperseded and would independently
    # re-defeat `target` the moment a fresh grant exists for the same principal+activity (correct
    # per-attestation independence, W5.2's own multiplicity note) -- retract it here so W3
    # isolates the ONE attestation this leg is about, exactly as the spec's "(fresh grant)
    # supersede the attestation row" wording presumes a single live attestation.
    retract1 = "corrected: attestation w1 retracted ahead of the W3 resurrection leg"
    r = led(wdir, "--supersedes", str(attest1_id), "verification", retract1, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    r = led(wdir, "principal", "grant-competence", "sentry", "--activity", "model-identity-attestation",
            "--band", "n/a", "--basis", "fixture grant 2 (post-withdrawal)", env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    grant2 = grant_row_id(world, sentry_pid, "model-identity-attestation")
    attest3 = attest_stmt(target, "MISMATCH", grade="exact-command", tag="w3")
    r = led(wdir, "verification", attest3, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    attest3_id = row_id_last(world, "verification", attest3)
    res = run_defeat(world)
    check("W3-pre-supersede-defeat-fires-again",
          res.verdict() == "AGREE"
          and f"model_defeated({target},{attest3_id},{grant2})" in
              {a for a in res.asp.atoms if a.startswith("model_defeated(")},
          f"verdict={res.verdict()}; model_defeated="
          f"{sorted(a for a in res.asp.atoms if a.startswith('model_defeated('))}",
          failures)
    correction = "corrected: attestation w3 was itself a false positive, retracted"
    r = led(wdir, "--supersedes", str(attest3_id), "verification", correction, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    res = run_defeat(world)
    check("W3-resurrection-on-supersession",
          res.verdict() == "AGREE"
          and not any(a.startswith("model_defeated(") for a in res.asp.atoms)
          and f"credited({target})" in {a for a in res.asp.atoms if a.startswith("credited(")},
          f"verdict={res.verdict()}; model_defeated="
          f"{sorted(a for a in res.asp.atoms if a.startswith('model_defeated('))}",
          failures)

    teardown(world)


def w10_stratification_red(failures: list[str]) -> None:
    """The MANDATED stratification negative control (spec §10/§12 W10): a deliberately
    UNSTRATIFIED variant of the defeat rule (adds `not model_defeated_row(A)` to its own body)
    over a fixture with two mutually mismatch-attesting rows. Lives under seen-red/ ONLY."""
    prog = HERE / "unstratified_negative_control.lp"
    tnow = ENGINE / "lp" / "ledger_tnow.lp"
    support = ENGINE / "lp" / "ledger_support.lp"
    edb = """
entry(1,0,decision,none,none,none).
entry(2,0,verification,none,none,none).
entry(3,0,verification,none,none,none).
row_actor(2,100).
row_actor(3,100).
trust_grant(50,100,"model-identity-attestation").
% A1 (row 2) mismatch-attests A2 (row 3); A2 mismatch-attests A1 -- the guard removed, each
% attestation row is ALSO the other's defeat target (structurally forbidden by the LAWFUL
% program's defeat_input/1 guard; here that guard is exercised through the unstratified body).
mismatch_attest(2,3,none).
mismatch_attest(3,2,none).
"""
    edb_path = HERE / "_w10_scratch_edb.lp"
    edb_path.write_text(edb, encoding="utf-8")
    try:
        # -n 0: full model enumeration -- the ONLY way clingo's JSON reveals a genuine
        # multiple-stable-model shape; the default n=1 would silently report just the FIRST
        # model found and look identical to a lawful, uniquely-stratified program.
        cp = sh(["clingo", "--outf=2", "-n", "0", str(tnow), str(support), str(prog), str(edb_path)])
        # A genuinely unstratified program either yields != 1 stable model (clingo's own
        # multi-model / UNSAT signal on --outf=2 JSON) or clingo reports a grounding-time error.
        # Bank the raw output verbatim -- the failure surface IS the witness, not a paraphrase.
        (HERE / "w10_clingo_output.json").write_text(cp.stdout, encoding="utf-8")
        (HERE / "w10_clingo_stderr.txt").write_text(cp.stderr, encoding="utf-8")
        diverged = False
        detail = f"returncode={cp.returncode}"
        try:
            j = json.loads(cp.stdout)
            n_models = len(j.get("Call", [{}])[0].get("Witnesses", []))
            result = j.get("Result", "")
            diverged = (result != "SATISFIABLE") or (n_models != 1)
            detail = f"Result={result!r}, n_models={n_models}, Call={j.get('Call')}"
        except Exception as e:  # noqa: BLE001 -- a non-JSON/crash output is ITSELF the divergence
            diverged = True
            detail = f"non-JSON or crashed clingo output ({type(e).__name__}): {cp.stdout[:300]!r} {cp.stderr[:300]!r}"
        check("W10-unstratified-negative-control",
              diverged,
              f"the unstratified variant's clingo run diverged from the lawful single-stable-model "
              f"reading, as required: {detail} (full output banked at "
              f"seen-red/defeat-pipeline/w10_clingo_output.json)",
              failures)
    finally:
        edb_path.unlink(missing_ok=True)


def world_mismatch_content_check(failures: list[str], tmps: list[Path]) -> None:
    """Review finding F1 (adjudication ledger row 1506; spec §Amendments A1 clarification):
    the W1-W11 plan above never asserts on mismatch_attest/3 fact CONTENT -- every check reads
    only the #show'n atoms (model_defeated/credited/exposure_model*), and mismatch_attest is an
    EDB predicate the .lp program consumes anonymously (Grade unread there), so the first
    build's v1-arm defect (Grade hardcoded to the literal `none`, discarding the parsed value)
    shipped unseen. This fixture calls ledger_edb.export_defeat() directly and asserts on the
    Grade ATOM TEXT of the emitted mismatch_attest fact, on BOTH attestation arms:

      - the v1 convention arm: real, exercised through `led verification` exactly as W1 does.
      - the s44 typed arm: no s44 kernel delta exists in this repository yet (RD-2's
        evidence-trigger not reached, same disclosed limit as spec §12 W12's live leg) -- so
        the typed arm's SHAPE (attest_row_id/attest_verdict/attest_grade columns + a
        model_identity_attested-kind row) is exercised via a SCRATCH-ONLY ALTER on this
        fixture's own throwaway world, mirroring how W5 above adds a scratch-only
        `support_affirm` table: never a kernel/lineage file edit, never applied to any live or
        banked world, torn down with the rest of the scratch schema by this function's own
        teardown() call."""
    world = "s41dfc"
    teardown(world)
    print(f"== scaffolding classic world {world} (chain ends {CHAIN_B[-1]}) -- "
          f"mismatch_attest CONTENT witness (F1) ==")
    wdir = scaffold_classic(world, CHAIN_B)
    tmps.append(wdir.parent)
    birth_acts(world)

    r = led(wdir, "register-principal", "sentry", "tool", "--purpose", "F1 content-check sentry",
            env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    sentry_pid = principal_id(world, "sentry")

    r = led(wdir, "principal", "grant-competence", "sentry", "--activity", "model-identity-attestation",
            "--band", "n/a", "--basis", "F1 content-check grant", env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr

    target_stmt = "target row for the F1 mismatch_attest content witness"
    r = led(wdir, "decision", target_stmt, env={"LED_ACTOR": "author"})
    assert r.returncode == 0, r.stdout + r.stderr
    target = row_id_last(world, "decision", target_stmt)

    # ---- v1 arm: the PARSED grade must cross, never the literal `none` (F1) ----
    attest_v1 = attest_stmt(target, "MISMATCH", grade="exact-command", tag="f1content")
    r = led(wdir, "verification", attest_v1, env={"LED_ACTOR": "sentry"})
    assert r.returncode == 0, r.stdout + r.stderr
    attest_v1_id = row_id_last(world, "verification", attest_v1)

    set_target(world, world, f"{world}_kernel")
    try:
        exp = ledger_edb.export_defeat(world)
    finally:
        clear_target()
    expected_v1 = f"mismatch_attest({attest_v1_id},{target},\"exact-command\")."
    hardcoded_none = f"mismatch_attest({attest_v1_id},{target},none)."
    matching = [f for f in exp.facts if f.startswith(f"mismatch_attest({attest_v1_id},")]
    check("F1-mismatch-attest-content-v1-arm",
          expected_v1 in exp.facts and hardcoded_none not in exp.facts,
          f"expected {expected_v1!r} in facts (never the hardcoded {hardcoded_none!r}); "
          f"got matching facts={matching}",
          failures)

    # ---- typed arm (s44 shape, scratch-only -- see docstring): the parsed grade must cross
    # here too, exercising the SAME _atom() call site the typed arm has used since the first
    # build (never hardcoded -- this leg proves the typed arm was never the defect, and stays a
    # regression guard for it).
    S = world
    psql_raw(f"ALTER TABLE {S}.ledger DROP CONSTRAINT ledger_kind_check;\n"
             f"ALTER TABLE {S}.ledger ADD COLUMN attest_row_id bigint, "
             f"ADD COLUMN attest_verdict text, ADD COLUMN attest_grade text;\n")
    typed_stmt = "F1 typed-arm mismatch_attest content witness (scratch s44 shape)"
    typed_script = (
        f"SET ROLE {S}_rw;\nSET search_path = {S}, {S}_kernel;\n"
        f"INSERT INTO ledger (kind, statement, actor, attest_row_id, attest_verdict, attest_grade)\n"
        f"VALUES ('model_identity_attested', $stmt${typed_stmt}$stmt$, {sentry_pid}, {target}, "
        f"'mismatch', 'turn-bracketed');\n")
    rt = psql_raw(typed_script)
    assert rt.returncode == 0, rt.stdout + rt.stderr
    typed_id = row_id_last(world, "model_identity_attested", typed_stmt)

    set_target(world, world, f"{world}_kernel")
    try:
        exp2 = ledger_edb.export_defeat(world)
    finally:
        clear_target()
    expected_typed = f"mismatch_attest({typed_id},{target},\"turn-bracketed\")."
    matching2 = [f for f in exp2.facts if f.startswith(f"mismatch_attest({typed_id},")]
    check("F1-mismatch-attest-content-typed-arm",
          expected_typed in exp2.facts,
          f"expected {expected_typed!r} in facts; got matching facts={matching2}",
          failures)

    teardown(world)


def w11_registry_red(failures: list[str]) -> None:
    """W11: grounding the defeat layer with ledger_support.lp omitted from the program list ->
    RegistryError BEFORE any clingo run."""
    raised = False
    detail = ""
    try:
        lp_registry.require_layer_stack("defeat", ["ledger_tnow.lp", "ledger_defeat.lp"])
    except lp_registry.RegistryError as e:
        raised = True
        detail = str(e)
    check("W11-registry-red", raised, f"RegistryError raised: {detail[:200]}", failures)


def main() -> int:
    failures: list[str] = []
    tmps: list[Path] = []
    try:
        w11_registry_red(failures)
        w10_stratification_red(failures)
        world_pre_check(failures, tmps)
        world_df_check(failures, tmps)
        world_malformed_check(failures, tmps)
        world_mismatch_content_check(failures, tmps)
    finally:
        for t in tmps:
            shutil.rmtree(t, ignore_errors=True)

    if failures:
        print(f"FAILURES: {failures}")
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
