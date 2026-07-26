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

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own
# environment before any subprocess is spawned -- inherited by the whole process tree
# this fixture starts, so every repo-root verb invocation anywhere downstream carries it.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

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


def doquery(schema: str, kern: str, role: str, sql: str) -> str:
    """A bare scalar/tuple SELECT, tuples-only + unaligned (-tA) -- unambiguous stdout, no
    header/footer/formatting noise to mis-parse (unlike dowrite(), which is for DO blocks whose
    RAISE NOTICE output is the point)."""
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1"], input=script)
    return cp.stdout.strip()


def main() -> int:
    suffix = "mkf"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    peer_schema, peer_kern, peer_role = f"{suffix}_peer", f"{suffix}_peer_kernel", f"{suffix}_peer_rw"
    teardown(schema, kern, role)
    teardown(peer_schema, peer_kern, peer_role)
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

        # WITNESS-AXIS MODERATE (strengthened-tier review): the FULL dispose/acknowledge
        # lifecycle, the exact leg AMENDMENT 1 unblocked, had no GREEN case banked here. Added:
        # send -> receive -> dispose -> acknowledgment row verified -> re-disposition refused ->
        # supersession-based re-disposition accepted -- a GENUINE two-world pair (send happens
        # in a real peer schema, addressed to THIS world; a single-schema "send to yourself"
        # would never pass validate_missive_identity's own author/addressee split).
        apply_chain(peer_schema, peer_kern, peer_role)
        birth(peer_schema, peer_kern, peer_role, "peerworld")

        out = dowrite(peer_schema, peer_kern, peer_role, f"""
DO $$
DECLARE v {peer_kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {peer_kern}.ledger_write(jsonb_build_object(
    'kind','missive_sent','statement','full lifecycle: send',
    'actor',(SELECT id FROM principal WHERE name='author'),
    'missive_protocol',1,'missive_author_world','peerworld','missive_addressee_world','seenredworld',
    'missive_thread','peerworld/lifecycle','missive_seq',1,'missive_act','request'));
  RAISE NOTICE 'LIFECYCLE send: % / row=%', v.disposition, v.row_id;
END $$;
""")
        log_lines.append(out)
        _check("LIFECYCLE: send accepted (peer world)", "LIFECYCLE send: accepted" in out)

        prov_row = doquery(peer_schema, peer_kern, peer_role,
            "SELECT id || ':' || row_hash FROM ledger WHERE kind='missive_sent' "
            "AND missive_thread='peerworld/lifecycle' AND missive_seq=1;")
        prov_token = f"xrow:peerworld:{prov_row}" if prov_row else None
        _check("LIFECYCLE: sent row's provenance token resolved", prov_token is not None)

        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_received','statement','full lifecycle: send',
    'actor',(SELECT id FROM principal WHERE name='courier'),
    'missive_protocol',1,'missive_author_world','peerworld','missive_addressee_world','seenredworld',
    'missive_thread','peerworld/lifecycle','missive_seq',1,'missive_act','request',
    'missive_provenance','{prov_token}'));
  RAISE NOTICE 'LIFECYCLE receive: % / row=%', v.disposition, v.row_id;
END $$;
""")
        log_lines.append(out)
        _check("LIFECYCLE: receive (courier pull) accepted", "LIFECYCLE receive: accepted" in out)

        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
DECLARE rid bigint;
BEGIN
  SELECT id INTO rid FROM ledger_current WHERE kind='missive_received'
    AND missive_thread='peerworld/lifecycle' AND missive_seq=1;
  SELECT * INTO v FROM {kern}.missive_dispose(jsonb_build_object(
    'receipt', rid, 'disposition', 'consumed',
    'actor', (SELECT id FROM principal WHERE name='author')));
  RAISE NOTICE 'LIFECYCLE dispose: % / disp_row=%', v.disposition, v.row_id;
END $$;
""")
        log_lines.append(out)
        _check("LIFECYCLE: dispose accepted (the leg AMENDMENT 1 unblocked)",
               "LIFECYCLE dispose: accepted" in out)

        ack_row = doquery(schema, kern, role,
            "SELECT count(*) FROM missive_outbound WHERE missive_thread='peerworld/lifecycle' "
            "AND missive_act='acknowledgment' AND missive_disposition='consumed';")
        _check("LIFECYCLE: acknowledgment row verified on missive_outbound "
               "(act=acknowledgment, disposition=consumed)",
               ack_row == "1")

        # bare re-disposition (no supersedes) -- refused.
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
DECLARE rid bigint;
BEGIN
  SELECT id INTO rid FROM ledger_current WHERE kind='missive_received'
    AND missive_thread='peerworld/lifecycle' AND missive_seq=1;
  SELECT * INTO v FROM {kern}.missive_dispose(jsonb_build_object(
    'receipt', rid, 'disposition', 'declined',
    'actor', (SELECT id FROM principal WHERE name='author')));
  RAISE NOTICE 'LIFECYCLE re-dispose (bare): % / %', v.disposition, v.message;
END $$;
""")
        log_lines.append(out)
        _check("LIFECYCLE: bare re-disposition refused",
               "LIFECYCLE re-dispose (bare): refused" in out
               and "already carries an in-force disposition" in out)

        # supersession-based re-disposition -- accepted.
        out = dowrite(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
DECLARE rid bigint; prior_id bigint;
BEGIN
  SELECT id INTO rid FROM ledger_current WHERE kind='missive_received'
    AND missive_thread='peerworld/lifecycle' AND missive_seq=1;
  SELECT id INTO prior_id FROM ledger_current WHERE kind='missive_disposed' AND missive_regards = rid;
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_disposed','statement','full lifecycle: re-disposition via supersession',
    'actor',(SELECT id FROM principal WHERE name='author'),
    'missive_regards', rid, 'missive_disposition','escalated', 'supersedes', prior_id));
  RAISE NOTICE 'LIFECYCLE re-dispose (supersedes): % / row=%', v.disposition, v.row_id;
END $$;
""")
        log_lines.append(out)
        _check("LIFECYCLE: supersession-based re-disposition accepted",
               "LIFECYCLE re-dispose (supersedes): accepted" in out)
    finally:
        teardown(schema, kern, role)
        teardown(peer_schema, peer_kern, peer_role)

    print("\n".join(log_lines))

    # Same-family concurrency races (strengthened-tier review, kernel axis, one severe) --
    # a SEPARATE runnable module (real psycopg concurrency, threading), invoked here so this
    # ONE registered fixture (gates/fixture_census.py) exercises the whole family, per-dir.
    race_script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "concurrent_race_fixtures.py")
    race_cp = sh([sys.executable, race_script])
    print(race_cp.stdout)
    if race_cp.stderr:
        print(race_cp.stderr, file=sys.stderr)
    race_ok = race_cp.returncode == 0

    # AMENDMENT 2 (missive_outbound append-complete transport) -- same invocation, same
    # one-registered-fixture-per-dir census discipline.
    a2_script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "amendment2_transport_fixture.py")
    a2_cp = sh([sys.executable, a2_script])
    print(a2_cp.stdout)
    if a2_cp.stderr:
        print(a2_cp.stderr, file=sys.stderr)
    a2_ok = a2_cp.returncode == 0

    # courier findings (batch-witness accumulation, exit-code aggregation) -- SEVERE/SILENT,
    # strengthened-tier review: this file (gates/fixture_census.py's OWN registered entry point
    # for the whole family) invoked concurrent_race_fixtures.py and amendment2_transport_fixture.py
    # as subprocesses but had ZERO reference to courier_witness_fixtures.py, so the standing
    # workflow would never catch a regression in either courier fix -- fixture_census.py is
    # presence-only (a file existing on disk, tracked in git) and cannot see that the file it
    # never runs proves nothing on its own. Same invocation shape as the two siblings above, same
    # one-registered-fixture-per-dir discipline.
    courier_script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "courier_witness_fixtures.py")
    courier_cp = sh([sys.executable, courier_script])
    print(courier_cp.stdout)
    if courier_cp.stderr:
        print(courier_cp.stderr, file=sys.stderr)
    courier_ok = courier_cp.returncode == 0

    if FAILURES or not race_ok or not a2_ok or not courier_ok:
        if FAILURES:
            print(f"\nmissives-kernel-family seen-red: {len(FAILURES)} FAILURE(S): {FAILURES}")
        if not race_ok:
            print("\nmissives-kernel-family seen-red: concurrent_race_fixtures.py FAILED "
                  f"(exit {race_cp.returncode})")
        if not a2_ok:
            print("\nmissives-kernel-family seen-red: amendment2_transport_fixture.py FAILED "
                  f"(exit {a2_cp.returncode})")
        if not courier_ok:
            print("\nmissives-kernel-family seen-red: courier_witness_fixtures.py FAILED "
                  f"(exit {courier_cp.returncode})")
        return 1
    print("\nmissives-kernel-family seen-red: all cases behaved as expected. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
