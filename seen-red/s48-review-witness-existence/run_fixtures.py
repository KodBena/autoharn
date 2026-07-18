#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T15:54:43Z
#   last-change: 2026-07-18T15:54:43Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for kernel/lineage/s48-review-witness-existence.sql
(design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md Delta 1). Real infra, no mocks: scratch schema pairs in
the toy db, torn down before and after. Never touches kernel/, bootstrap/, or any live world.

WORLDS:
  WORLD PRE -- chain ends at s47 (no s48): the .detect.sql negative polarity.
  WORLD S48 -- chain ends at s48 (on top of s47): the .detect.sql positive polarity, plus every
               live leg below (WK1-a/b/c), each cross-checked against `./judge --layer work` for
               row-for-row AGREE.

Usage: python3 seen-red/s48-review-witness-existence/run_fixtures.py
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

CHAIN_S47 = [
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
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
]
CHAIN_S48 = CHAIN_S47 + ["s48-review-witness-existence.sql"]


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
-- s43 Element 6: the write-boundary's OWN recording identity.
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
    world_pre, world_s48 = "s48fx_pre", "s48fx_s48"
    try:
        print(f"== scaffolding WORLD PRE (chain ends {CHAIN_S47[-1]}) ==")
        apply_chain(world_pre, CHAIN_S47)
        check("detect-negative-pre-s48", detect(world_pre, "s48-review-witness-existence.detect.sql") == "f",
              "s48 .detect.sql reads f on the pre-s48 (s47-head) chain", failures)

        print(f"== scaffolding WORLD S48 (chain ends {CHAIN_S48[-1]}) ==")
        apply_chain(world_s48, CHAIN_S48)
        check("detect-positive-s48", detect(world_s48, "s48-review-witness-existence.detect.sql") == "t",
              "s48 .detect.sql reads t on the s48-applied chain", failures)

        birth(world_s48, "author-fixture")
        author_id = sql1(world_s48, f"SELECT id FROM {world_s48}_kernel.principal WHERE name='author-fixture';")

        # A pre-existing, citable row: a plain decision, to get a real ledger id WK1-a can cite.
        witness_row = kernel_write(world_s48, {"kind": "decision", "statement": "a decision to cite as review witness",
                                                "actor": int(author_id)})
        check("witness-row-decision-accepted", witness_row["disposition"] == "accepted", f"{witness_row}", failures)
        witness_id = witness_row["row_id"]

        # --- WK1-a: close citing an EXISTING row -> accepted, row lands (no regression).
        oa = kernel_write(world_s48, {"kind": "work_opened", "work_slug": "wk1a-item",
                                       "work_title": "wk1a item", "statement": "open wk1a-item",
                                       "actor": int(author_id)})
        check("wk1a-open-accepted", oa["disposition"] == "accepted", f"{oa}", failures)
        ca = kernel_write(world_s48, {"kind": "work_closed", "work_slug": "wk1a-item",
                                       "work_resolution": "dropped",
                                       "work_review_disposition": "witnessed",
                                       "work_review_ref": f"row:{witness_id}",
                                       "statement": "close wk1a-item, citing existing row",
                                       "actor": int(author_id)})
        check("wk1a-close-citing-existing-row-accepted", ca["disposition"] == "accepted", f"{ca}", failures)

        # --- WK1-b: close citing row:<absent id> -> refused, message names the id and the
        # teaching; nothing written; sequence-gap accounting unaffected (the write is journaled
        # by the write boundary as a write_refused row, not a raw abort -- s43's own posture).
        absent_id = 999999999
        ob = kernel_write(world_s48, {"kind": "work_opened", "work_slug": "wk1b-item",
                                       "work_title": "wk1b item", "statement": "open wk1b-item",
                                       "actor": int(author_id)})
        check("wk1b-open-accepted", ob["disposition"] == "accepted", f"{ob}", failures)
        cb = kernel_write(world_s48, {"kind": "work_closed", "work_slug": "wk1b-item",
                                       "work_resolution": "dropped",
                                       "work_review_disposition": "witnessed",
                                       "work_review_ref": f"row:{absent_id}",
                                       "statement": "close wk1b-item, citing absent row",
                                       "actor": int(author_id)})
        check("wk1b-close-citing-absent-row-refused", cb["disposition"] == "refused", f"{cb}", failures)
        check("wk1b-teach-text-names-id",
              cb.get("message") is not None
              and f"row {absent_id}" in cb["message"]
              and "dangling evidence pointer" in cb["message"],
              f"message: {cb.get('message')!r}", failures)
        wk1b_closed_rows = sql1(world_s48,
            f"SET search_path = {world_s48}; "
            f"SELECT count(*) FROM {world_s48}.ledger WHERE kind='work_closed' AND work_slug='wk1b-item';")
        check("wk1b-zero-work-closed-rows", wk1b_closed_rows == "0",
              f"work_closed row count for wk1b-item: {wk1b_closed_rows!r}", failures)

        # --- WK1-c: a plain decision citing an absent row via the GENERIC `refs` column
        # (NON-close kind, non-review-witness position) -> still accepted (scope check: prose
        # refs not captured by this refusal).
        cc = kernel_write(world_s48, {"kind": "decision", "statement": "prose citation of a future row",
                                       "refs": f"row:{absent_id}", "actor": int(author_id)})
        check("wk1c-decision-refs-absent-row-accepted", cc["disposition"] == "accepted", f"{cc}", failures)

        # ./judge --layer work AGREE on both polarities (spec's own Delta 1 witness list).
        judge_agree(world_pre, failures, "judge-work-AGREE-world-pre")
        judge_agree(world_s48, failures, "judge-work-AGREE-world-s48")

    finally:
        teardown(world_pre)
        teardown(world_s48)

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s48-review-witness-existence cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
