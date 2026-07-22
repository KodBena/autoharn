#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for kernel/lineage/s47-claim-on-closed-refusal.sql
(design/FABLE-CLAIM-ON-CLOSED-REFUSAL-SPEC.md §3). Real infra, no mocks: scratch schema pairs in
the toy db, torn down before and after. Never touches kernel/, bootstrap/, or any live world.

WORLDS:
  WORLD PRE -- chain ends at s46 (no s47): the .detect.sql negative polarity.
  WORLD S47 -- chain ends at s47 (on top of s46): the .detect.sql positive polarity, plus every
               live leg below (RED + three GREEN legs), each cross-checked against
               `./judge --layer work` for row-for-row AGREE.

Usage: python3 seen-red/s47-claim-on-closed-refusal/run_fixtures.py
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

CHAIN_S46 = [
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
    "s46-credited-views.sql",
]
CHAIN_S47 = CHAIN_S46 + ["s47-claim-on-closed-refusal.sql"]


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


def birth(world: str, author_name: str) -> None:
    script = f"""
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.stamp_secret (secret) VALUES (gen_random_bytes(32));
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('{author_name}', 'model') RETURNING id \\gset author_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','author (fixture)', :author_id, :author_id, 'fixture author');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world}_rw', true);
COMMIT;
BEGIN;
-- s43 Element 6: the write-boundary's OWN recording identity (bootstrap/new-project.sh's own
-- birth sequence registers this exact name/class for every new world; ledger_write's refusal
-- journaling refuses loudly, as witnessed above, without it).
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('write-boundary', 'tool') RETURNING id \\gset wb_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','write-boundary (fixture)', :author_id, :wb_id, 'the kernel write boundary''s own recording identity');
COMMIT;
"""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"birth sequence failed: {cp.stdout}\n{cp.stderr}")


def judge_agree(world: str, failures: list[str], label: str) -> None:
    env = dict(os.environ)
    env["HARNESS_PGHOST"] = PGHOST
    env["EPISTEMIC_PGHOST"] = PGHOST
    env["LEDGER_DB"] = PGDB
    env["LEDGER_SCHEMA"] = world
    env["LEDGER_KERN"] = f"{world}_kernel"
    env["PYTHONPATH"] = f"{REPO / 'engine'}:{REPO / 'filing'}"
    cp = sh(["python3", "-c",
             "import ledger_differential as ld\n"
             "r = ld.run_layer_differential('anyname', layer='work')\n"
             "print(r.verdict())\n"
             "print('asp', sorted(r.asp.atoms))\n"
             "print('sql', sorted(r.sql.atoms))\n"],
            env=env, cwd=str(REPO))
    if cp.returncode != 0:
        raise RuntimeError(f"judge programmatic call failed ({world}): {cp.stderr}")
    out = cp.stdout.strip().splitlines()
    check(label, out and out[0] == "AGREE", f"judge output ({world}): {out}", failures)


def main() -> int:
    failures: list[str] = []
    world_pre, world_s47 = "s47fx_pre", "s47fx_s47"
    try:
        print(f"== scaffolding WORLD PRE (chain ends {CHAIN_S46[-1]}) ==")
        apply_chain(world_pre, CHAIN_S46)
        check("detect-negative-pre-s47", detect(world_pre, "s47-claim-on-closed-refusal.detect.sql") == "f",
              "s47 .detect.sql reads f on the pre-s47 (s46-head) chain", failures)

        print(f"== scaffolding WORLD S47 (chain ends {CHAIN_S47[-1]}) ==")
        apply_chain(world_s47, CHAIN_S47)
        check("detect-positive-s47", detect(world_s47, "s47-claim-on-closed-refusal.detect.sql") == "t",
              "s47 .detect.sql reads t on the s47-applied chain", failures)

        birth(world_s47, "author-fixture")
        author_id = sql1(world_s47, f"SELECT id FROM {world_s47}_kernel.principal WHERE name='author-fixture';")

        # --- RED: open -> close -> claim the SAME slug -> refused, teach-text verbatim, zero
        # work_claimed row (spec sec-3 RED leg).
        o = kernel_write(world_s47, {"kind": "work_opened", "work_slug": "red-item",
                                      "work_title": "red item", "statement": "open red-item",
                                      "actor": int(author_id)})
        check("red-open-accepted", o["disposition"] == "accepted", f"{o}", failures)
        c = kernel_write(world_s47, {"kind": "work_closed", "work_slug": "red-item",
                                      "work_resolution": "dropped",
                                      "work_review_disposition": "deferred",
                                      "statement": "close red-item", "actor": int(author_id)})
        check("red-close-accepted", c["disposition"] == "accepted", f"{c}", failures)
        claim_red = kernel_write(world_s47, {"kind": "work_claimed", "work_slug": "red-item",
                                              "statement": "claim red-item", "actor": int(author_id)})
        check("red-claim-refused", claim_red["disposition"] == "refused", f"{claim_red}", failures)
        check("red-claim-teach-text-verbatim",
              claim_red.get("message") is not None and "is not claimable" in claim_red["message"]
              and "red-item" in claim_red["message"],
              f"message: {claim_red.get('message')!r}", failures)
        red_claim_rows = sql1(world_s47,
            f"SET search_path = {world_s47}; "
            f"SELECT count(*) FROM {world_s47}.ledger WHERE kind='work_claimed' AND work_slug='red-item';")
        check("red-zero-work-claimed-rows", red_claim_rows == "0",
              f"work_claimed row count for red-item: {red_claim_rows!r}", failures)

        # --- GREEN leg 1: claim an open item -> admitted, unchanged.
        o1 = kernel_write(world_s47, {"kind": "work_opened", "work_slug": "green-open",
                                       "work_title": "green open item", "statement": "open green-open",
                                       "actor": int(author_id)})
        check("green1-open-accepted", o1["disposition"] == "accepted", f"{o1}", failures)
        claim1 = kernel_write(world_s47, {"kind": "work_claimed", "work_slug": "green-open",
                                           "statement": "claim green-open", "actor": int(author_id)})
        check("green1-claim-admitted", claim1["disposition"] == "accepted", f"{claim1}", failures)

        # --- GREEN leg 2: open -> close -> supersede the close (s31 recipe) -> claim -> admitted
        # (the retracted close does not block).
        o2 = kernel_write(world_s47, {"kind": "work_opened", "work_slug": "green-retract",
                                       "work_title": "green retract item",
                                       "statement": "open green-retract", "actor": int(author_id)})
        check("green2-open-accepted", o2["disposition"] == "accepted", f"{o2}", failures)
        c2 = kernel_write(world_s47, {"kind": "work_closed", "work_slug": "green-retract",
                                       "work_resolution": "dropped",
                                       "work_review_disposition": "deferred",
                                       "statement": "close green-retract", "actor": int(author_id)})
        check("green2-close-accepted", c2["disposition"] == "accepted", f"{c2}", failures)
        c2_id = c2["row_id"]
        # supersede the close DIRECTLY (s31's own uniform retraction mechanics, witnessed for this
        # exact shape in vestigial_documentation/design/ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md: "the close
        # superseded -> item reads open in the same read"): ledger_current excludes row R iff SOME
        # row's own `supersedes` column names R, regardless of the superseding row's OWN kind (the
        # view's WHERE clause is `NOT EXISTS (SELECT 1 FROM ledger s WHERE s.supersedes = l.id)`,
        # no kind-match join at all). The retracting row here is an `informs` self-edge on the SAME
        # slug -- `informs` is exempt from every self-edge/dangling-antecedent check
        # (validate_work_item_depends' self-edge refusals are scoped to blocks-close/blocks-start
        # only, s30/s39) -- chosen because it is the lightest-weight kind whose own construction
        # carries no side effect of its own on this slug's close/claim state, purely a supersedes
        # carrier. NOT a second work_closed row: superseding WITH another close would only move
        # which close is in force, leaving the item still reading 'closed' under the successor.
        retract = kernel_write(world_s47, {"kind": "work_depends_on", "work_slug": "green-retract",
                                            "work_depends_on": "green-retract",
                                            "edge_type": "informs",
                                            "supersedes": int(c2_id),
                                            "statement": "retract close of green-retract (fixture, s31 recipe)",
                                            "actor": int(author_id)})
        check("green2-close-retracted-accepted", retract["disposition"] == "accepted", f"{retract}", failures)
        state2 = sql1(world_s47,
            f"SET search_path = {world_s47}; "
            f"SELECT state FROM {world_s47}.work_item_current WHERE slug='green-retract';")
        check("green2-item-reads-open-after-retraction", state2 == "open",
              f"work_item_current.state for green-retract: {state2!r}", failures)
        claim2 = kernel_write(world_s47, {"kind": "work_claimed", "work_slug": "green-retract",
                                           "statement": "claim green-retract", "actor": int(author_id)})
        check("green2-claim-admitted-after-retraction", claim2["disposition"] == "accepted",
              f"{claim2}", failures)

        # --- GREEN leg 3: blocks-start refusal (s39's own red leg) still fires unchanged.
        o3a = kernel_write(world_s47, {"kind": "work_opened", "work_slug": "green-bs-antecedent",
                                        "work_title": "bs antecedent",
                                        "statement": "open green-bs-antecedent", "actor": int(author_id)})
        check("green3-antecedent-open-accepted", o3a["disposition"] == "accepted", f"{o3a}", failures)
        o3b = kernel_write(world_s47, {"kind": "work_opened", "work_slug": "green-bs-dependent",
                                        "work_title": "bs dependent",
                                        "statement": "open green-bs-dependent", "actor": int(author_id)})
        check("green3-dependent-open-accepted", o3b["disposition"] == "accepted", f"{o3b}", failures)
        edge3 = kernel_write(world_s47, {"kind": "work_depends_on", "work_slug": "green-bs-dependent",
                                          "work_depends_on": "green-bs-antecedent",
                                          "edge_type": "blocks-start",
                                          "statement": "green-bs-dependent blocks-start on green-bs-antecedent",
                                          "actor": int(author_id)})
        check("green3-edge-accepted", edge3["disposition"] == "accepted", f"{edge3}", failures)
        claim3 = kernel_write(world_s47, {"kind": "work_claimed", "work_slug": "green-bs-dependent",
                                           "statement": "claim green-bs-dependent", "actor": int(author_id)})
        check("green3-claim-refused-blocks-start-unchanged", claim3["disposition"] == "refused",
              f"{claim3}", failures)
        check("green3-teach-text-is-s39-not-s47",
              claim3.get("message") is not None
              and "blocks-start antecedent(s) are not yet resolved" in claim3["message"]
              and "is not claimable" not in claim3["message"],
              f"message: {claim3.get('message')!r}", failures)

        # ./judge --layer work AGREE on both polarities (spec sec-3).
        judge_agree(world_pre, failures, "judge-work-AGREE-world-pre")
        judge_agree(world_s47, failures, "judge-work-AGREE-world-s47")

    finally:
        teardown(world_pre)
        teardown(world_s47)

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s47-claim-on-closed-refusal cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
