#!/usr/bin/env python3
"""Seen-red specimen for the MISSIVES kernel family's TWO concurrency races (strengthened-tier
review, kernel axis, one severe -- reproduced live by the reviewer with two concurrent psql
sessions; kernel/lineage/s58-missive-substrate.sql ELEMENT 3B/4B/5/7B, ADR-0021 Rule B).

RACE 1 (dedup): validate_missive_dedup's own guard is a plain `EXISTS (...)` under READ
COMMITTED -- a duplicate (author_world, thread, seq) row on the SAME side (sent or received)
is invisible to a concurrent writer's own snapshot until the first writer COMMITS. TWO real
psycopg connections (real OS-level concurrency, real network sockets, not stubbed) reproduce
this: connection A opens an explicit transaction and calls kernel.ledger_write with a
missive_received payload, WITHOUT committing; connection B, on a SEPARATE thread, calls
kernel.ledger_write with the IDENTICAL (author_world, thread, seq) while A is still open.

  PRE-FIX (the reviewer's own reproduction, banked in red.txt): B's own EXISTS check runs
  before A ever commits, sees nothing, and B's write also proceeds -- BOTH accepted, a
  duplicate committed to the SAME (author_world, thread, seq) key. RED.

  POST-FIX (this repo's current tree, THIS fixture's own live run): B's INSERT (inside
  kernel.ledger_write's own trigger-fired write) contends with A's own UNCOMMITTED index entry
  at the missive_received_dedup_uq unique partial index -- real Postgres MVCC behavior (an
  INSERT into a b-tree unique index waits on a conflicting UNCOMMITTED entry via
  XactLockTableWait, not merely "checks after commit") -- B's call BLOCKS until A commits, then
  re-checks and raises SQLSTATE 23505, translated by kernel.missive_dedup_race_text() (ELEMENT
  4B) to the SAME teaching text validate_missive_dedup's own EXISTS-path produces. GREEN
  (refused, not a raw 23505).

RACE 2 (re-disposition): validate_missive_disposition's re-disposition guard is ALSO a plain
EXISTS under READ COMMITTED -- two concurrent dispositions of the SAME receipt both pass and
both commit, each minting its own acknowledgment (the reviewer's own reproduction). The SAME
two-connection technique: A calls kernel.missive_dispose(receipt=R, ...) inside an open
transaction, uncommitted; B calls kernel.missive_dispose(receipt=R, ...) concurrently.

  PRE-FIX: B's own EXISTS check (validate_missive_disposition) runs before A commits, sees no
  in-force disposition, and B ALSO commits -- two contradictory in-force missive_disposed rows
  for the SAME receipt, two acknowledgments. RED.

  POST-FIX: B's validate_missive_disposition trigger takes
  `pg_advisory_xact_lock(hashtext(schema || '.missive_disposed.' || receipt)::bigint)` BEFORE
  its own EXISTS check -- B blocks on the SAME lock key A already holds (A took it first,
  entering the trigger before B), so B's EXISTS check does not even RUN until A's transaction
  ends. Once A commits, B unblocks, re-checks, and NOW sees A's committed disposition -- the
  existing EXISTS-based refusal fires for B, exactly as the sequential case. GREEN.

Both races are run against a REAL scratch schema pair (teardown to zero residue on exit either
way) using psycopg (real, separate DB connections -- the concurrency is genuine OS-level
parallelism via Python threads blocked on real network sockets, not simulated).
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

import psycopg

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


def dosql(schema: str, kern: str, role: str, sql: str) -> None:
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"birth SQL failed:\n{cp.stdout}\n{cp.stderr}")


def birth(schema: str, kern: str, role: str, wname: str) -> None:
    genesis = sh(["openssl", "rand", "-hex", "32"]).stdout.strip()
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.chain_genesis (seed) VALUES ('{genesis}') "
        f"ON CONFLICT (only_one) DO NOTHING;"])
    login_role = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAc", "SELECT session_user;"]).stdout.strip()

    dosql(schema, kern, role, f"""
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind', 'principal_registered', 'statement', 'author self-attributed',
    'actor', (SELECT id FROM principal WHERE name = 'author'),
    'principal_subject', (SELECT id FROM principal WHERE name = 'author'),
    'principal_purpose', 'concurrent race fixture'));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION 'refused: %', v.message; END IF;
END $bw$;
""")
    for drole in (role, login_role):
        dosql(schema, kern, role, f"""
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
        dosql(schema, kern, role, f"""
SELECT set_config('birth.pname', '{pname}', false), set_config('birth.pclass', '{pclass}', false);
DO $bw$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.registration_write(jsonb_build_object(
    'name', current_setting('birth.pname'), 'agent_class', current_setting('birth.pclass'),
    'purpose', 'concurrent race fixture', 'statement', 'registered',
    'actor', (SELECT id FROM principal WHERE name = 'author')));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION '% registration refused: %', current_setting('birth.pname'), v.message; END IF;
END $bw$;
""")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.world_identity (world_name) VALUES ('{wname}') "
        f"ON CONFLICT (one_row) DO NOTHING;"])


def _conn(schema: str, kern: str, role: str) -> psycopg.Connection:
    conn = psycopg.connect(host=PGHOST, dbname=PGDB, autocommit=False)
    conn.execute(f"SET ROLE {role}")
    conn.execute(f"SET search_path = {schema}, {kern}")
    return conn


def race_1_dedup(schema: str, kern: str, role: str) -> None:
    print("\n=== RACE 1: dedup (missive_received), two real concurrent connections ===")
    conn_a = _conn(schema, kern, role)
    conn_b = _conn(schema, kern, role)
    results: dict[str, tuple] = {}

    def call(conn: psycopg.Connection, tag: str) -> None:
        try:
            row = conn.execute(f"""
              SELECT (v).disposition, (v).message FROM (
                SELECT {kern}.ledger_write(jsonb_build_object(
                  'kind','missive_received','statement','race 1',
                  'actor',(SELECT id FROM principal WHERE name='courier'),
                  'missive_protocol',1,'missive_author_world','raceauthor',
                  'missive_addressee_world','raceworld',
                  'missive_thread','raceauthor/race-1','missive_seq',1,'missive_act','request',
                  'missive_provenance','xrow:raceauthor:1:{'a'*64}')) AS v
              ) t;
            """).fetchone()
            results[tag] = row
        except Exception as e:  # noqa: BLE001 -- banking the raw exception class is the point
            results[tag] = ("EXCEPTION", str(e))

    # A starts and is held open (no commit yet) -- B starts concurrently on its own thread/conn.
    t_a = threading.Thread(target=call, args=(conn_a, "A"))
    t_a.start()
    t_a.join()  # A's own ledger_write call completes (accepted), but conn_a has NOT committed.

    t_b = threading.Thread(target=call, args=(conn_b, "B"))
    t_b.start()
    time.sleep(0.5)  # give B's blocked INSERT (post-fix) a moment to actually be waiting
    conn_a.commit()  # release A -- B (post-fix) unblocks HERE and re-checks
    t_b.join(timeout=15)

    print(f"  A: {results.get('A')}")
    print(f"  B: {results.get('B')}")
    conn_b.rollback()
    conn_a.close()
    conn_b.close()

    a_disp = results.get("A", (None,))[0]
    b_disp = results.get("B", (None,))[0]
    _check("RACE 1: A accepted", a_disp == "accepted")
    _check("RACE 1: B refused (post-fix concurrency backstop, not a raw exception)",
           b_disp == "refused")
    if b_disp == "refused":
        _check("RACE 1: B's refusal carries the SAME teaching text as the sequential case "
               "(exactly-once RECORDING), not a raw 23505/constraint name",
               "exactly-once RECORDING" in (results["B"][1] or ""))


def race_2_redisposition(schema: str, kern: str, role: str) -> None:
    print("\n=== RACE 2: re-disposition, two real concurrent connections ===")
    # Seed one missive_received row to dispose, via a throwaway admin connection.
    seed = _conn(schema, kern, role)
    row = seed.execute(f"""
      SELECT (v).row_id FROM (
        SELECT {kern}.ledger_write(jsonb_build_object(
          'kind','missive_received','statement','race 2 target',
          'actor',(SELECT id FROM principal WHERE name='courier'),
          'missive_protocol',1,'missive_author_world','raceauthor',
          'missive_addressee_world','raceworld',
          'missive_thread','raceauthor/race-2','missive_seq',1,'missive_act','request',
          'missive_provenance','xrow:raceauthor:2:{'b'*64}')) AS v
      ) t;
    """).fetchone()
    seed.commit()
    receipt_id = row[0]
    seed.close()
    _check("RACE 2 setup: seed receipt written", receipt_id is not None)

    conn_a = _conn(schema, kern, role)
    conn_b = _conn(schema, kern, role)
    results: dict[str, tuple] = {}

    def dispose(conn: psycopg.Connection, tag: str) -> None:
        try:
            row = conn.execute(f"""
              SELECT (v).disposition, (v).message FROM (
                SELECT {kern}.missive_dispose(jsonb_build_object(
                  'receipt', {receipt_id}, 'disposition', 'consumed',
                  'actor', (SELECT id FROM principal WHERE name='author'))) AS v
              ) t;
            """).fetchone()
            results[tag] = row
        except Exception as e:  # noqa: BLE001
            results[tag] = ("EXCEPTION", str(e))

    t_a = threading.Thread(target=dispose, args=(conn_a, "A"))
    t_a.start()
    t_a.join()  # A's own transaction is open (holding the advisory lock post-fix), uncommitted.

    t_b = threading.Thread(target=dispose, args=(conn_b, "B"))
    t_b.start()
    time.sleep(0.5)
    conn_a.commit()
    t_b.join(timeout=15)

    print(f"  A: {results.get('A')}")
    print(f"  B: {results.get('B')}")
    conn_b.rollback()
    conn_a.close()
    conn_b.close()

    a_disp = results.get("A", (None,))[0]
    b_disp = results.get("B", (None,))[0]
    _check("RACE 2: A accepted", a_disp == "accepted")
    _check("RACE 2: B refused (advisory-lock serialization, not a raw exception)",
           b_disp == "refused")
    if b_disp == "refused":
        _check("RACE 2: B's refusal carries the SAME in-force-disposition teaching text",
               "already carries an in-force disposition" in (results["B"][1] or ""))


def main() -> int:
    suffix = "mkfrace"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"
    teardown(schema, kern, role)
    try:
        apply_chain(schema, kern, role)
        birth(schema, kern, role, "raceworld")
        race_1_dedup(schema, kern, role)
        race_2_redisposition(schema, kern, role)
    finally:
        teardown(schema, kern, role)

    if FAILURES:
        print(f"\nmissives-kernel-family concurrent races: {len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("\nmissives-kernel-family concurrent races: both races closed, post-fix. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
