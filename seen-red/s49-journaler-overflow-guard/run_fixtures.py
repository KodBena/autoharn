#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T15:57:28Z
#   last-change: 2026-07-18T15:58:04Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""run_fixtures.py -- both-polarity witness for kernel/lineage/s49-journaler-overflow-guard.sql
(design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md Delta 2). Real infra, no mocks: ONE scratch schema pair
in the toy db, torn down before and after. Never touches kernel/, bootstrap/, or any live world.

WK2-c (the spec's own explicit requirement) is witnessed on the SAME schema pair the delta is
then applied to -- not two independently-scaffolded worlds: this fixture applies the chain
through s48 ONCE, reproduces the pre-fix crash (WK2-c), THEN applies s49 directly on top of that
SAME live schema (CREATE OR REPLACE is idempotent), and re-runs the identical payload to witness
the fix (WK2-a) plus the no-regression leg (WK2-b) -- one schema pair, two polarities in time.

Usage: python3 seen-red/s49-journaler-overflow-guard/run_fixtures.py
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

CHAIN_S48 = [
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
    "s48-review-witness-existence.sql",
]

OVERFLOW_ACTOR = 10 ** 29  # 30 digits -- well beyond bigint's 19-digit max magnitude.


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


def apply_one(world: str, filename: str) -> subprocess.CompletedProcess:
    """Apply ONE lineage file directly onto an already-scaffolded world (idempotent
    CREATE OR REPLACE) -- the in-place patch WK2-c's own same-schema-pair requirement needs."""
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
               "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-v", f"role={world}_rw",
               "-f", str(LINEAGE / filename)])


def detect(world: str, sibling: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1",
             "-v", f"schema={world}", "-v", f"kern={world}_kernel", "-f", str(LINEAGE / sibling)])
    if cp.returncode != 0:
        raise RuntimeError(f"detect failed: {cp.stderr}")
    return cp.stdout.strip()


def sql1(world: str, sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed ({world}): {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def kernel_write(world: str, payload: dict) -> dict:
    """Normal-path helper: asserts the psql plumbing itself succeeded (a valid write_verdict
    came back, accepted OR refused). NOT used for WK2-c, which expects the plumbing itself to
    fail (an uncaught server-side exception, pre-fix)."""
    pj = json.dumps(payload)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.ledger_write(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"kernel_write plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def kernel_write_raw(world: str, payload: dict) -> subprocess.CompletedProcess:
    """WK2-c's own probe: does NOT assert success -- the pre-fix polarity is exactly an
    uncaught server-side exception (nonzero psql exit, SQLSTATE 22003 in stderr), which this
    returns for the caller to assert ON, rather than raising past it."""
    pj = json.dumps(payload)
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
              input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                    f"SELECT to_jsonb(v) FROM {world}_kernel.ledger_write(:'payload'::jsonb) v;\n")


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
    world = "s49fx"
    try:
        print(f"== scaffolding WORLD (chain ends {CHAIN_S48[-1]}, s49 NOT yet applied) ==")
        apply_chain(world, CHAIN_S48)
        check("detect-negative-pre-s49", detect(world, "s49-journaler-overflow-guard.detect.sql") == "f",
              "s49 .detect.sql reads f before s49 is applied to this schema pair", failures)

        birth(world, "author-fixture")
        author_id = int(sql1(world, f"SELECT id FROM {world}_kernel.principal WHERE name='author-fixture';"))

        judge_agree(world, failures, "judge-work-AGREE-world-pre")

        # --- WK2-c (spec's own explicit requirement): the pre-fix polarity, reproduced on THIS
        # schema pair BEFORE applying the delta -- a 30-digit actor crashes the journaler itself
        # (22003 propagates OUT of journal_write_refusal, uncaught), no write_refused row is
        # written, only the oracle's refusal_seq gap remains.
        seq_before = sql1(world, f"SELECT last_value || ':' || is_called FROM {world}_kernel.refusal_seq;")
        crash = kernel_write_raw(world, {"kind": "work_opened", "work_slug": "wk2-item",
                                          "work_title": "wk2 item", "statement": "open wk2-item",
                                          "actor": OVERFLOW_ACTOR})
        check("wk2c-prefix-journaler-crashes", crash.returncode != 0,
              f"psql exit={crash.returncode}; stderr tail: {crash.stderr[-500:]!r}", failures)
        check("wk2c-prefix-sqlstate-22003-surfaces",
              "22003" in crash.stderr or "out of range" in crash.stderr.lower(),
              f"stderr tail: {crash.stderr[-500:]!r}", failures)
        wk2c_refused_rows = sql1(world,
            f"SET search_path = {world}; "
            f"SELECT count(*) FROM {world}.ledger WHERE kind='write_refused';")
        check("wk2c-prefix-zero-write-refused-rows", wk2c_refused_rows == "0",
              f"write_refused row count pre-fix: {wk2c_refused_rows!r}", failures)
        seq_after_crash = sql1(world, f"SELECT last_value || ':' || is_called FROM {world}_kernel.refusal_seq;")
        check("wk2c-prefix-sequence-gap-recorded", seq_after_crash != seq_before,
              f"refusal_seq (last_value:is_called) before={seq_before!r} after-crash="
              f"{seq_after_crash!r} (bumped non-transactionally even though the journal row "
              f"never landed -- the s43 Element 5 oracle, doing exactly its job)", failures)

        # --- Apply s49 DIRECTLY onto this SAME live schema pair (idempotent CREATE OR REPLACE) --
        # the delta killing the exact defect just reproduced above, same schema, same data.
        print("== applying s49-journaler-overflow-guard.sql onto the SAME schema pair ==")
        patch = apply_one(world, "s49-journaler-overflow-guard.sql")
        check("s49-patch-applies-clean", patch.returncode == 0,
              f"psql exit={patch.returncode}; stderr tail: {patch.stderr[-500:]!r}", failures)

        check("detect-positive-post-s49", detect(world, "s49-journaler-overflow-guard.detect.sql") == "t",
              "s49 .detect.sql reads t after s49 is applied to this schema pair", failures)

        # --- WK2-a: retry the IDENTICAL payload that crashed the journaler above -> now the
        # refusal IS journaled: write_refused row present, refusal_attempted_actor NULL (the
        # cast still cannot resolve a 30-digit numeral to a real principal id -- it never
        # could -- but now that failure yields NULL instead of aborting), refusal_attempted_role
        # populated, sqlstate/message = the ORIGINAL refusal's (the jsonb_populate_record
        # overflow), not a new 22003 from the journaler's own internals.
        retry = kernel_write(world, {"kind": "work_opened", "work_slug": "wk2-item",
                                      "work_title": "wk2 item", "statement": "open wk2-item",
                                      "actor": OVERFLOW_ACTOR})
        check("wk2a-postfix-refused-not-crashed", retry["disposition"] == "refused", f"{retry}", failures)
        check("wk2a-postfix-sqlstate-is-22003",
              retry.get("sqlstate") == "22003", f"sqlstate: {retry.get('sqlstate')!r}", failures)
        refusal_id = retry.get("refusal_id")
        check("wk2a-postfix-refusal-row-id-present", refusal_id is not None, f"{retry}", failures)
        row = sql1(world,
            f"SET search_path = {world}; "
            f"SELECT refusal_attempted_actor IS NULL, refusal_attempted_role IS NOT NULL, "
            f"       refusal_sqlstate, refusal_message "
            f"FROM {world}.ledger WHERE id = {refusal_id};") if refusal_id else ""
        check("wk2a-postfix-write-refused-row-shape",
              row.startswith("t|t|22003|"),
              f"write_refused row (attempted_actor IS NULL | attempted_role IS NOT NULL | "
              f"sqlstate | message...): {row!r}", failures)

        # --- WK2-b: a refused write with a normal IN-RANGE actor (the author's own registered
        # id -- unambiguous, resolvable) refused for an UNRELATED reason (closing a slug that
        # was never opened) -> journaled with the attempted id RESOLVED (no regression on the
        # pre-existing resolving path -- the guard only wraps the ONE overflow-prone cast, it
        # does not touch the normal-range resolution at all).
        wk2b = kernel_write(world, {"kind": "work_closed", "work_slug": "wk2b-never-opened",
                                     "work_resolution": "dropped",
                                     "work_review_disposition": "deferred",
                                     "statement": "close a slug that was never opened",
                                     "actor": author_id})
        check("wk2b-refused", wk2b["disposition"] == "refused", f"{wk2b}", failures)
        wk2b_refusal_id = wk2b.get("refusal_id")
        wk2b_row = sql1(world,
            f"SET search_path = {world}; "
            f"SELECT refusal_attempted_actor FROM {world}.ledger WHERE id = {wk2b_refusal_id};"
            ) if wk2b_refusal_id else ""
        check("wk2b-attempted-actor-resolved", wk2b_row == str(author_id),
              f"refusal_attempted_actor: {wk2b_row!r} (expected the explicit, in-range, "
              f"registered actor {author_id})", failures)

        judge_agree(world, failures, "judge-work-AGREE-world-post-s49")

    finally:
        teardown(world)

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s49-journaler-overflow-guard cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
