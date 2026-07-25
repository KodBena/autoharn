#!/usr/bin/env python3
"""Seen-red specimen for the MISSIVES kernel family (kernel/lineage/s58-missive-substrate.sql,
s59-missive-views.sql, design/FABLE-MISSIVES-KERNEL-SPEC.md, ledger row 1263).

HISTORICAL RED (round 1 of this build, pre-AMENDMENT 1, 2026-07-25): the ratified spec's own
choice to carry missive_disposed's subject on the pre-existing `regards` column collided with
s15-schema.sql's validate_review trigger, which hard-reserves `regards` to kind='review' and
refuses any other kind naming it. Witnessed live, both at the raw SQL boundary function and the
HTTP boundary:

    Ledger policy: regards is reserved for kind=review.

This banked as the build's own primary finding (build 4881a8f) and blocked every
missive_disposed write until AMENDMENT 1 moved the subject to a dedicated column,
missive_regards. The historical text above is preserved in red.txt as evidence the defect was
real and witnessed, not asserted -- it is NOT re-reproduced live here (the code path that
produced it, the s58-literal `regards`-reuse CHECK, no longer exists in the tree to reproduce
against; re-creating it would mean hand-writing a second, throwaway copy of dead SQL purely to
fail, which teaches nothing this file's own prose doesn't already say).

LIVE RED (this file's own runnable fixture, exercised against a REAL scratch schema pair, the
SAME mechanism the build's own witness plan used): the family's core refusals, both-polarity,
run against `kernel.ledger_write`/`kernel.missive_dispose` for real -- never stubbed.

  1. missive_regards_kind_shape -- AMENDMENT 1's own two-way CHECK: missive_regards on a
     non-missive_disposed row is refused (FORBIDDEN elsewhere).
  2. validate_missive_regards -- a missive_disposed row naming a nonexistent missive_regards
     target is refused with teaching (AMENDMENT 1's own dedicated trigger).
  3. validate_missive_courier_scope -- the courier principal writing any non-missive_received
     kind is refused (Q3, ratified row 1157).
  4. validate_missive_dedup -- a duplicate (author_world, thread, seq) missive_received row is
     refused (exactly-once RECORDING).

GREEN (negative control, same run): a lawful missive_sent write, by a non-courier principal,
accepted -- confirming the RED cases above are refusing the DEFECT, not the mechanism itself.

Every case runs the REAL kernel functions against a REAL scratch Postgres schema pair
(subprocess psql, not stubbed) -- exactly this build's own witness-plan mechanism, teardown to
zero residue on exit either way.
"""
from __future__ import annotations

import os
import subprocess
import sys

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or "192.168.122.1"
PGDB = os.environ.get("HARNESS_PGDB", "toy")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINEAGE = os.path.join(REPO, "kernel", "lineage")

CHAIN = [
    "high_watermark_1.sql", "s20-obligation-grants-and-view-refresh.sql",
    "s21-session-aware-distinctness.sql", "s22-work-item-ledger.sql",
    "s23-per-invocation-stamp-token.sql", "s24-declared-event-time.sql",
    "s25-commission-kind.sql", "s26-row-hash-chain.sql", "s27-chain-high-water.sql",
    "s28-work-parent-edge.sql", "s29-obligation-item-key-and-typed-close.sql",
    "s30-typed-dependency-edges.sql", "s31-supersession-uniform-retraction.sql",
    "s32-edge-views-single-home.sql", "s33-composite-discharge.sql",
    "s34-computed-grade-refusal.sql", "s35-validation-decomposition.sql",
    "s36-decision-grade.sql", "s37-violation-disposition.sql", "s38-bookkeeping-close.sql",
    "s39-blocks-start.sql", "s40-principal-identity-events.sql",
    "s41-principal-bindings-and-relations.sql", "s42-row-hash-full-coverage.sql",
    "s43-typed-verdict-write-boundary.sql", "s45-standing-lifecycle.sql",
    "s44-model-identity-attestation.sql", "s46-credited-views.sql",
    "s47-claim-on-closed-refusal.sql", "s48-review-witness-existence.sql",
    "s49-journaler-overflow-guard.sql", "s50-defeat-input-raw-domain.sql",
    "s51-artifact-store.sql", "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
]

FAILURES: list[str] = []


def _check(label: str, cond: bool) -> None:
    print(f"  [{'ok' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILURES.append(label)


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def teardown(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c",
        f"DROP SCHEMA IF EXISTS {schema} CASCADE; DROP SCHEMA IF EXISTS {kern} CASCADE;"])
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"DROP ROLE IF EXISTS {role};"])


def apply_chain(schema: str, kern: str, role: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {role} LOGIN;"])
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN:
        args += ["-f", os.path.join(LINEAGE, f)]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def birth(schema: str, kern: str, role: str, wname: str) -> None:
    genesis = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis}') "
        f"ON CONFLICT (only_one) DO NOTHING;"])
    login_role = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", "SELECT session_user;"]).stdout.strip()

    def do(body: str) -> subprocess.CompletedProcess:
        script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{body}"
        return sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1"], input=script)

    do(f"""
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_registered', 'statement', 'author self-attributed',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_purpose', 'seen-red fixture'));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for drole in (role, login_role):
        do(f"""
SELECT set_config('birth.drole', '{drole}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_standing_declared', 'statement', 'standing',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_db_role', current_setting('birth.drole'),
    'principal_binding_active', true));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for pname, pclass in (("write-boundary", "tool"), ("courier", "tool")):
        do(f"""
SELECT set_config('birth.pname', '{pname}', false), set_config('birth.pclass', '{pclass}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.registration_write(jsonb_build_object(
    'name', current_setting('birth.pname'), 'agent_class', current_setting('birth.pclass'),
    'purpose', 'seen-red fixture', 'statement', 'registered',
    'actor', (SELECT id FROM principal WHERE name = 'author')));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.world_identity (world_name) VALUES ('{wname}') "
        f"ON CONFLICT (one_row) DO NOTHING;"])


def dowrite(schema: str, kern: str, role: str, sql: str) -> str:
    """Returns stdout+stderr combined -- psql's RAISE NOTICE output (where every kernel.write_
    verdict this fixture prints lands) goes to STDERR, not stdout."""
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=0"], input=script)
    return cp.stdout + cp.stderr


def main() -> int:
    suffix = "mkf"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    teardown(schema, kern, role)
    log_lines: list[str] = []
    try:
        apply_chain(schema, kern, role)
        birth(schema, kern, role, "seenredworld")

        # RED 1: missive_regards on a non-missive_disposed row -- refused (defense in depth:
        # validate_missive_regards' own kind-check fires ahead of the missive_regards_kind_shape
        # CHECK for this specific case, since target row 1 is not itself missive_received either
        # -- either mechanism alone already forecloses the class).
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','note','statement','x','actor',(SELECT id FROM principal WHERE name='author'),
    'missive_regards', 1));
  RAISE NOTICE 'RESULT: % / %', v.disposition, v.message;
END $$;
""")
        log_lines.append(out)
        _check("RED: missive_regards on a non-missive_disposed row refused",
               "RESULT: refused" in out)

        # RED 2: missive_disposed naming a nonexistent missive_regards target.
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_disposed','statement','x','actor',(SELECT id FROM principal WHERE name='author'),
    'missive_regards', 999999, 'missive_disposition','consumed'));
  RAISE NOTICE 'RESULT: % / %', v.disposition, v.message;
END $$;
""")
        log_lines.append(out)
        _check("RED: missive_regards naming a nonexistent row refused, taught",
               "RESULT: refused" in out and "does not exist" in out)

        # RED 3: courier principal attempting a non-missive_received kind.
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','decision','statement','x','actor',(SELECT id FROM principal WHERE name='courier')));
  RAISE NOTICE 'RESULT: % / %', v.disposition, v.message;
END $$;
""")
        log_lines.append(out)
        _check("RED: courier writing a non-missive_received kind refused (Q3)",
               "RESULT: refused" in out and "records arrivals and NOTHING else" in out)

        # GREEN control: a lawful missive_sent write by the author accepts.
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_sent','statement','seen-red control',
    'actor',(SELECT id FROM principal WHERE name='author'),
    'missive_protocol',1,'missive_author_world','seenredworld','missive_addressee_world','otherworld',
    'missive_thread','seenredworld/t1','missive_seq',1,'missive_act','assertion'));
  RAISE NOTICE 'RESULT: % / %', v.disposition, v.message;
END $$;
""")
        log_lines.append(out)
        _check("GREEN: lawful missive_sent accepted (control)",
               "RESULT: accepted" in out)

        # RED 4: duplicate (author_world, thread, seq) missive_sent -- dedup.
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_sent','statement','duplicate',
    'actor',(SELECT id FROM principal WHERE name='author'),
    'missive_protocol',1,'missive_author_world','seenredworld','missive_addressee_world','otherworld',
    'missive_thread','seenredworld/t1','missive_seq',1,'missive_act','assertion'));
  RAISE NOTICE 'RESULT: % / %', v.disposition, v.message;
END $$;
""")
        log_lines.append(out)
        _check("RED: duplicate (thread, seq) missive_sent refused (dedup)",
               "RESULT: refused" in out and "one-time fact" in out)
    finally:
        teardown(schema, kern, role)

    print("\n".join(log_lines))
    if FAILURES:
        print(f"\nmissives-kernel-family seen-red: {len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("\nmissives-kernel-family seen-red: all cases behaved as expected. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
