#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T09:21:45Z
#   last-change: 2026-07-18T09:22:04Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for kernel/lineage/s46-credited-views.sql
(design/FABLE-DEFEAT-PIPELINE-SPEC.md §8, and its §12 W12 live leg -- UNEXERCISED at that
spec's own authoring, discharged here on scratch). Real infra, no mocks: scratch schema pairs
in the toy db, torn down before and after. Never touches kernel/, bootstrap/, or any live world.

WORLDS:
  WORLD PRE -- chain ends at s44 (no s46): the .detect.sql negative polarity.
  WORLD S46 -- chain ends at s46 (on top of s44): the .detect.sql positive polarity, a live
               model-identity mismatch defeating a row through model_defeated_rows/
               credited_current, cross-checked against the SQL floor
               (engine/ledger_floor.py::defeat_floor_atoms) and the ASP program
               (./judge --layer defeat) for row-for-row AGREE.

Usage: python3 seen-red/s46-credited-views/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "engine"))
from pghost_resolve import resolve_pghost  # noqa: E402

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S44 = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql",
    "s38-bookkeeping-close.sql", "s39-blocks-start.sql",
    "s40-principal-identity-events.sql", "s41-principal-bindings-and-relations.sql",
    "s42-row-hash-full-coverage.sql", "s43-typed-verdict-write-boundary.sql",
    "s45-standing-lifecycle.sql", "s44-model-identity-attestation.sql",
]
CHAIN_S46 = CHAIN_S44 + ["s46-credited-views.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
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


def apply_chain(world: str, chain: list[str]) -> None:
    teardown(world)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {world}_rw LOGIN PASSWORD 'x';"])
    if cp.returncode != 0:
        raise RuntimeError(f"role create failed: {cp.stderr}")
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw"]
    for f in chain:
        args += ["-f", str(LINEAGE / f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply failed for {world}: {cp.stdout[-2000:]} {cp.stderr[-2000:]}")


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def sql1(world: str, sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed ({world}): {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def kernel_write(world: str, payload: dict) -> dict:
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.ledger_write(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def main() -> int:
    failures: list[str] = []
    world_pre, world_s46 = "s46fx_pre", "s46fx_s46"
    try:
        print(f"== scaffolding WORLD PRE (chain ends {CHAIN_S44[-1]}) ==")
        apply_chain(world_pre, CHAIN_S44)
        check("detect-negative-pre-s46", detect(world_pre, "s46-credited-views.detect.sql") == "f",
              "s46 .detect.sql reads f on the pre-s46 (s44-head) chain", failures)

        print(f"== scaffolding WORLD S46 (chain ends {CHAIN_S46[-1]}) ==")
        apply_chain(world_s46, CHAIN_S46)
        check("detect-positive-s46", detect(world_s46, "s46-credited-views.detect.sql") == "t",
              "s46 .detect.sql reads t on the s46-applied chain", failures)

        # birth: genesis + stamp secret + author + a 'tool' sentry principal, same-transaction
        # anchor-coupling as s44's own fixture.
        birth = f"""
BEGIN;
INSERT INTO {world_s46}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world_s46}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world_s46}_kernel.principal (name, agent_class)
  VALUES ('author-fixture', 'model') RETURNING id \\gset author_
INSERT INTO {world_s46}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','author (fixture)', :author_id, :author_id, 'fixture author');
INSERT INTO {world_s46}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world_s46}_rw', true);
COMMIT;
BEGIN;
INSERT INTO {world_s46}_kernel.principal (name, agent_class)
  VALUES ('sentry-fixture', 'tool') RETURNING id \\gset sentry_
INSERT INTO {world_s46}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','sentry (fixture)', :author_id, :sentry_id, 'fixture sentry');
COMMIT;
"""
        cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=birth)
        if cp.returncode != 0:
            raise RuntimeError(f"birth sequence failed: {cp.stdout}\n{cp.stderr}")
        author_id = sql1(world_s46, f"SELECT id FROM {world_s46}_kernel.principal WHERE name='author-fixture';")
        sentry_id = sql1(world_s46, f"SELECT id FROM {world_s46}_kernel.principal WHERE name='sentry-fixture';")

        # a grant of model-identity-attestation competence to the sentry.
        grant = kernel_write(world_s46, {
            "kind": "principal_competence_granted", "statement": "fixture grant",
            "actor": int(author_id), "principal_subject": int(sentry_id),
            "principal_competence_activity": "model-identity-attestation",
            "principal_binding_active": True,
            "principal_competence_band": "high", "principal_competence_basis": "fixture",
        })
        check("grant-accepted", grant["disposition"] == "accepted", f"{grant}", failures)
        grant_id = grant["row_id"]

        # a target row, then W6: no attestation yet -- everything credited.
        target = kernel_write(world_s46, {"kind": "decision", "statement": "target row",
                                           "actor": int(author_id)})
        target_id = target["row_id"]
        credited_before = sql1(world_s46, f"SELECT id FROM {world_s46}.credited_current WHERE id={target_id};")
        check("W6-absence-never-defeats", credited_before == str(target_id),
              f"pre-attestation credited_current still shows row {target_id}: {credited_before!r}", failures)

        # W1: a typed mismatch attestation, actor = the sentry (matches the grant's subject).
        attest = kernel_write(world_s46, {
            "kind": "model_identity_attested", "statement": "typed mismatch attestation",
            "actor": int(sentry_id), "attest_row_id": target_id,
            "attest_model": "observed-model-x", "attest_grade": "exact-command",
            "attest_verdict": "mismatch", "attest_expected": "declared-model-y",
            "attest_session": "sess-w12", "attest_basis": "command,session",
        })
        check("attestation-accepted", attest["disposition"] == "accepted", f"{attest}", failures)
        attest_id = attest["row_id"]

        defeated_row = sql1(world_s46, f"SELECT row_id, attest_id, grant_id, model, grade "
                                        f"FROM {world_s46}.model_defeated_rows WHERE row_id={target_id};")
        check("W1-model-defeated-rows-with-cause",
              defeated_row == f"{target_id}|{attest_id}|{grant_id}|observed-model-x|exact-command",
              f"model_defeated_rows: {defeated_row!r}", failures)

        credited_after = sql1(world_s46, f"SELECT id FROM {world_s46}.credited_current WHERE id={target_id};")
        check("W1-credited-current-excludes-defeated-row", credited_after == "",
              f"credited_current for {target_id}: {credited_after!r} (expect empty)", failures)
        ledger_current_still_shows = sql1(world_s46, f"SELECT id FROM {world_s46}.ledger_current WHERE id={target_id};")
        check("W1-ledger-current-still-shows-row", ledger_current_still_shows == str(target_id),
              f"ledger_current for {target_id}: {ledger_current_still_shows!r}", failures)

        # cross-check against the independently-derived SQL floor (engine/ledger_floor.py).
        env = dict(os.environ)
        env["HARNESS_PGHOST"] = PGHOST
        env["EPISTEMIC_PGHOST"] = PGHOST
        env["LEDGER_DB"] = PGDB
        env["LEDGER_SCHEMA"] = world_s46
        env["LEDGER_KERN"] = f"{world_s46}_kernel"
        env["PYTHONPATH"] = f"{REPO / 'engine'}:{REPO / 'filing'}"
        cp = sh(["python3", "-c",
                 "import ledger_floor; "
                 "atoms = ledger_floor.defeat_floor_atoms('anyname'); "
                 "print('\\n'.join(sorted(atoms)))"],
                env=env, cwd=str(REPO))
        if cp.returncode != 0:
            raise RuntimeError(f"floor atoms failed: {cp.stderr}")
        floor_atoms = set(cp.stdout.strip().splitlines())
        check("floor-model-defeated-matches",
              f"model_defeated({target_id},{attest_id},{grant_id})" in floor_atoms,
              f"floor atoms: {sorted(floor_atoms)}", failures)
        check("floor-credited-excludes-target",
              f"credited({target_id})" not in floor_atoms,
              f"floor atoms: {sorted(floor_atoms)}", failures)

        # W2: withdraw the grant -- the defeat lapses implicitly, zero per-row cleanup.
        withdraw = kernel_write(world_s46, {
            "kind": "principal_competence_granted", "statement": "fixture withdrawal",
            "actor": int(author_id), "principal_subject": int(sentry_id),
            "principal_competence_activity": "model-identity-attestation",
            "principal_binding_active": False, "supersedes": grant_id,
        })
        check("W2-withdrawal-accepted", withdraw["disposition"] == "accepted", f"{withdraw}", failures)
        credited_after_withdraw = sql1(world_s46,
                                        f"SELECT id FROM {world_s46}.credited_current WHERE id={target_id};")
        check("W2-implicit-lapse-recredits", credited_after_withdraw == str(target_id),
              f"credited_current after grant withdrawal: {credited_after_withdraw!r}", failures)
        defeated_after_withdraw = sql1(world_s46,
                                        f"SELECT count(*) FROM {world_s46}.model_defeated_rows WHERE row_id={target_id};")
        check("W2-model-defeated-rows-empty-after-withdraw", defeated_after_withdraw == "0",
              f"model_defeated_rows count after withdrawal: {defeated_after_withdraw!r}", failures)

        # ./judge --layer defeat AGREE, both before and after the withdrawal leg above is
        # irrelevant to AGREE -- run it fresh, current state (grant withdrawn, zero defeats).
        cp = sh(["python3", "engine/ledger_differential.py", "--layer", "defeat"], env=env, cwd=str(REPO))
        # ledger_differential.py's own main() takes target names positionally; call the module API
        # directly instead for a clean programmatic verdict (mirrors seen-red/defeat-pipeline's
        # own pattern of importing engine modules rather than shelling out to a CLI wrapper).
        cp2 = sh(["python3", "-c",
                  "import ledger_differential as ld\n"
                  "r = ld.run_layer_differential('anyname', layer='defeat')\n"
                  "print(r.verdict())\n"
                  "print('asp', sorted(r.asp.atoms))\n"
                  "print('sql', sorted(r.sql.atoms))\n"],
                 env=env, cwd=str(REPO))
        if cp2.returncode != 0:
            raise RuntimeError(f"judge programmatic call failed: {cp2.stderr}")
        out = cp2.stdout.strip().splitlines()
        check("judge-defeat-AGREE-after-withdrawal", out and out[0] == "AGREE",
              f"judge output: {out}", failures)

    finally:
        teardown(world_pre)
        teardown(world_s46)

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s46-credited-views cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
