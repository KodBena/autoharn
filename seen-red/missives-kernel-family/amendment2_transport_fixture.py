#!/usr/bin/env python3
"""Seen-red specimen for AMENDMENT 2 (design/FABLE-MISSIVES-KERNEL-SPEC.md, 2026-07-25,
maintainer-ratified "yes"): missive_outbound re-issued as APPEND-COMPLETE transport.

THE REVIEWER'S EXACT REPRODUCTION (strengthened-tier review, serving axis): two ORDINARY
SEQUENTIAL writes, no race -- send a request (seq=1), then send a withdrawal (seq=2)
superseding it, THEN read the outbound feed.

  PRE-A2 (the pre-amendment view body, `FROM ledger_current` -- current-truth-filtered):
  the superseded seq=1 row is INVISIBLE on missive_outbound -- only the withdrawal (seq=2)
  ever appears. A courier polling after both writes never sees the original at all: the
  addressee receives a withdrawal citing a provenance token for a message it never got and
  never will; missive_stale cannot correlate (the original never arrived). RED.

  POST-A2 (this repo's current tree, `FROM ledger` -- raw, append-complete): BOTH rows appear,
  in id order, delivery-monotonic. GREEN.

This fixture reproduces the RED leg against a DELIBERATELY REVERTED copy of
kernel/lineage/s59-missive-views.sql (missive_outbound's FROM clause reverted to
ledger_current) -- never committed to the tree, applied only to a throwaway scratch schema for
this one reproduction, then discarded -- and the GREEN leg against the real, current tree.
"""
from __future__ import annotations

import os
import subprocess
import sys

PGHOST = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST") or "192.168.122.1"
PGDB = os.environ.get("HARNESS_PGDB", "toy")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINEAGE = os.path.join(REPO, "kernel", "lineage")

CHAIN_BASE = [
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
    "s58-missive-substrate.sql",
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


def _reverted_s59(tmp_path: str) -> None:
    """A throwaway copy of s59-missive-views.sql with missive_outbound's FROM clause reverted
    to the PRE-AMENDMENT-2 body (`ledger_current`, current-truth-filtered) -- reproduces the
    reviewer's own witnessed defect. Never committed; written to `tmp_path`, applied once,
    discarded."""
    with open(os.path.join(LINEAGE, "s59-missive-views.sql")) as f:
        text = f.read()
    reverted = text.replace(
        "FROM   :\"schema\".ledger s\nWHERE  s.kind = 'missive_sent';",
        "FROM   :\"schema\".ledger_current s\nWHERE  s.kind = 'missive_sent';  "
        "-- [RED REPRO: reverted to pre-A2 ledger_current]",
    )
    if reverted == text:
        raise RuntimeError("RED REPRO SETUP FAILED: the expected missive_outbound FROM-clause "
                            "text was not found to revert -- s59's own body has changed shape; "
                            "update this fixture's own replace() target.")
    with open(tmp_path, "w") as f:
        f.write(reverted)


def apply_chain(schema: str, kern: str, role: str, *, s59_path: str) -> None:
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-c", f"CREATE ROLE {role} LOGIN;"])
    args = ["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1",
            "-v", f"schema={schema}", "-v", f"kern={kern}", "-v", f"role={role}"]
    for f in CHAIN_BASE:
        args += ["-f", os.path.join(LINEAGE, f)]
    args += ["-f", s59_path]
    cp = sh(args)
    if cp.returncode != 0:
        raise RuntimeError(f"chain apply FAILED:\n{cp.stdout[-2000:]}\n{cp.stderr[-2000:]}")


def dosql(schema: str, kern: str, role: str, sql: str) -> str:
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-q", "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"SQL failed:\n{cp.stdout}\n{cp.stderr}")
    return cp.stdout + cp.stderr


def doquery(schema: str, kern: str, role: str, sql: str) -> str:
    script = f"SET ROLE {role};\nSET search_path = {schema}, {kern};\n{sql}"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1"], input=script)
    return cp.stdout.strip()


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
    'principal_purpose', 'amendment2 fixture'));
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
    'purpose', 'amendment2 fixture', 'statement', 'registered',
    'actor', (SELECT id FROM principal WHERE name = 'author')));
  IF v.disposition <> 'accepted' THEN RAISE EXCEPTION '% registration refused: %', current_setting('birth.pname'), v.message; END IF;
END $bw$;
""")
    sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
        f"INSERT INTO {kern}.world_identity (world_name) VALUES ('{wname}') "
        f"ON CONFLICT (one_row) DO NOTHING;"])


def _reproduce(schema: str, kern: str, role: str) -> int:
    """Send seq=1, withdraw via seq=2 superseding it, then count rows on the outbound feed for
    that thread. Returns the row count (2 = delivered whole, 1 = the original silently lost)."""
    out = dosql(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_sent','statement','original',
    'actor',(SELECT id FROM principal WHERE name='author'),
    'missive_protocol',1,'missive_author_world','worlda','missive_addressee_world','worldb',
    'missive_thread','worlda/a2fixture','missive_seq',1,'missive_act','request'));
  RAISE NOTICE 'seq1: %', v.disposition;
END $$;
""")
    if "seq1: accepted" not in out:
        raise RuntimeError(f"setup failed (seq1): {out}")

    prov = doquery(schema, kern, role,
        "SELECT id || ':' || row_hash FROM ledger WHERE kind='missive_sent' "
        "AND missive_thread='worlda/a2fixture' AND missive_seq=1;")
    target_id = prov.split(":", 1)[0]
    token = f"xrow:worlda:{prov}"

    out = dosql(schema, kern, role, f"""
DO $$
DECLARE v {kern}.write_verdict;
BEGIN
  SELECT * INTO v FROM {kern}.ledger_write(jsonb_build_object(
    'kind','missive_sent','statement','withdrawing',
    'actor',(SELECT id FROM principal WHERE name='author'),
    'missive_protocol',1,'missive_author_world','worlda','missive_addressee_world','worldb',
    'missive_thread','worlda/a2fixture','missive_seq',2,'missive_act','withdrawal',
    'missive_responds_to','{token}','supersedes',{target_id}));
  RAISE NOTICE 'seq2: %', v.disposition;
END $$;
""")
    if "seq2: accepted" not in out:
        raise RuntimeError(f"setup failed (seq2): {out}")

    count = doquery(schema, kern, role,
        "SELECT count(*) FROM missive_outbound WHERE missive_thread='worlda/a2fixture';")
    return int(count)


def main() -> int:
    suffix = "mkfa2"
    schema, kern, role = f"{suffix}_scratch", f"{suffix}_scratch_kernel", f"{suffix}_scratch_rw"

    # RED leg: the reverted (pre-A2) view.
    reverted_path = "/tmp/mkfa2_s59_reverted.sql"
    _reverted_s59(reverted_path)
    teardown(schema, kern, role)
    try:
        apply_chain(schema, kern, role, s59_path=reverted_path)
        birth(schema, kern, role, "worlda")
        red_count = _reproduce(schema, kern, role)
        print(f"  RED (pre-A2, ledger_current-sourced): missive_outbound row count = {red_count}")
        _check("RED: pre-A2 view silently drops the superseded original (count == 1)",
               red_count == 1)
    finally:
        teardown(schema, kern, role)
        try:
            os.remove(reverted_path)
        except OSError:
            pass

    # GREEN leg: the real, current tree.
    teardown(schema, kern, role)
    try:
        apply_chain(schema, kern, role, s59_path=os.path.join(LINEAGE, "s59-missive-views.sql"))
        birth(schema, kern, role, "worlda")
        green_count = _reproduce(schema, kern, role)
        print(f"  GREEN (post-A2, append-complete): missive_outbound row count = {green_count}")
        _check("GREEN: post-A2 view delivers BOTH rows (count == 2)", green_count == 2)
    finally:
        teardown(schema, kern, role)

    if FAILURES:
        print(f"\namendment2_transport_fixture: {len(FAILURES)} FAILURE(S): {FAILURES}")
        return 1
    print("\namendment2_transport_fixture: red (pre-A2) and green (post-A2) both confirmed. ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
