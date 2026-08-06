#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity witness for kernel/lineage/s73-typed-annulment-disposition.sql
(design/FABLE-TYPED-ANNULMENT-DISPOSITION-SPEC.md, ledger row 1087). Real infra, no mocks: scratch
schema pairs in the toy db, torn down before and after. Never touches kernel/, bootstrap/, or any
live world. Modeled on seen-red/s48-review-witness-existence/run_fixtures.py's simpler shape (a
direct SQL `birth()` sequence, no CLASSIC scaffold) plus seen-red/s72-stamp-binding-conjunct/
run_fixtures.py's vendor-stamp injection technique (a python-computed HMAC against a python-random
stamp_secret this fixture provisions itself, GUC-injected via `SET app.vendor_*` ahead of the write
-- never invoking hooks/stamp_intercept.py, the same "bypass the hook, forge the same HMAC the hook
would have produced" idiom every prior seen-red fixture in this lineage already relies on).

WORLDS:
  WORLD PRE  -- chain ends at s72 (no s73): the .detect.sql negative polarity, ordinary write
                unaffected.
  WORLD MAIN -- chain ends at s73 (on top of s72): the .detect.sql positive polarity, plus every
                live leg below, each cross-checked against `./judge --layer work` for row-for-row
                AGREE (the spec's own §2 ENGINE clause: verified, not asserted).

CASES on WORLD MAIN:
  ANNUL-ACCEPTED                 -- valid, in-force, distinct-actor-and-stamp authority -> accepted.
  ANNUL-EXCLUDED-FROM-GAP        -- the accepted annulled close never appears in work_review_gap.
  ANNUL-AUDIT-VIEW-RENDERS       -- work_review_annulled surfaces it, authority_in_force=true.
  ANNUL-MISSING-REF-REFUSED      -- work_review_ref NULL -> refused (CHECK).
  ANNUL-RETRACTED-REF-REFUSED    -- work_review_ref cites a row that EXISTS but is no longer
                                     in force (superseded before the annulment write) -> refused.
  ANNUL-SELF-SAME-ACTOR-REFUSED  -- authority row's actor equals the obligor's actor -> refused.
  ANNUL-SELF-SAME-STAMP-REFUSED  -- a DIFFERENT actor id, but the SAME (session,agent) invocation
                                     as the obligor -> refused (the s21 composition this delta's
                                     own header defends: a different principal id cannot manufacture
                                     the distinction from one invocation).
  ANNUL-STRICT-REFUSED           -- annulled disposition cannot satisfy a --strict close (the
                                     "legal only where deferred would have been legal" refusal).
  ANNUL-VIOLATION-DISPOSITION-KIND-REFUSED -- annulled is refused on a work_violation_disposition
                                     row (scoped to kind=work_closed alone).
  DEFENSE-IN-DEPTH-SURFACED      -- a SEPARATE accepted annulment whose authority row is retracted
                                     AFTER the annulment was written surfaces as
                                     annulled_authority_retracted in both work_item_violations and
                                     work_violation_history.

Usage: python3 seen-red/s73-typed-annulment-disposition/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import hashlib
import hmac as hmac_lib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LINEAGE = REPO / "kernel" / "lineage"
sys.path.insert(0, str(REPO / "filing"))
sys.path.insert(0, str(REPO / "engine"))
from pghost_resolve import resolve_pghost  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S72 = [
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
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
    "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql",
    "s62-delegation-lifecycle-gating.sql", "s63-supersession-body-restoration.sql",
    "s64-principal-stamps-delegation-conditions.sql", "s65-refusal-attempted-kind.sql",
    "s66-forged-stamp-journal-totality.sql", "s67-refusal-digest-bound.sql",
    "s68-typed-absence-dispositions.sql", "s69-role-coherence-refusals.sql",
    "s70-scope-binding.sql", "s71-row-level-scope-policies.sql",
    "s72-stamp-binding-conjunct.sql",
]
CHAIN_S73 = CHAIN_S72 + ["s73-typed-annulment-disposition.sql"]


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    # PGOPTIONS stripped -- the s70/s71/s72 fixtures' own identical note: hooks/stamp_intercept.py
    # injects app.vendor_* into PGOPTIONS ahead of every Bash-tool command; a fresh scratch
    # world's own kernel.stamp_secret is unrelated random, so an inherited GUC would be
    # present-but-invalid and get refused rather than accepted-unstamped.
    env = dict(kw.pop("env", os.environ))
    env.pop("PGOPTIONS", None)
    return subprocess.run(args, capture_output=True, text=True, env=env, **kw)


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


def sql1(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"sql1 failed: {sql}\n{cp.stderr}")
    return cp.stdout.strip()


def provision_stamp_secret(world: str) -> str:
    """A python-random 32-byte secret, written to the scratch world's own kern.stamp_secret --
    known to this fixture so it can compute matching HMACs, mirroring s72's own fixture technique
    (never touching hooks/stamp_intercept.py or any real apparatus secret)."""
    secret_hex = secrets.token_hex(32)
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-v", f"hex={secret_hex}"],
            input=f'TRUNCATE "{world}_kernel".stamp_secret;\n'
                  f'INSERT INTO "{world}_kernel".stamp_secret (secret) VALUES (decode(:\'hex\',\'hex\'));\n')
    if cp.returncode != 0:
        raise RuntimeError(f"stamp_secret provisioning failed: {cp.stdout} {cp.stderr}")
    return secret_hex


def valid_vendor(secret_hex: str, session: str, agent: str, ts: int | None = None) -> dict[str, str]:
    ts = ts if ts is not None else int(time.time())
    secret = bytes.fromhex(secret_hex)
    data = f"{session}|{agent}|{ts}".encode()
    digest = hmac_lib.new(secret, data, hashlib.sha256).hexdigest()
    return {"session": session, "agent": agent, "ts": str(ts), "hmac": digest}


def bw_call(world: str, payload: dict, vendor: dict[str, str] | None = None) -> dict:
    """Same shape as seen-red/s48's kernel_write, with an OPTIONAL vendor preamble (s72's own
    technique): when given, SETs app.vendor_session/app.vendor_agent/app.vendor_ts/app.vendor_hmac
    in the SAME psql session ahead of the write-boundary call, so set_stamp() (s17) sees a
    genuine, verifiable interception stamp instead of the unstamped default."""
    pj = json.dumps(payload)
    preamble = ""
    if vendor:
        for k, v in vendor.items():
            preamble += f"SET app.vendor_{k} = '{v}';\n"
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-v", f"payload={pj}"],
            input=f"SET ROLE {world}_rw;\nSET search_path = {world}, {world}_kernel;\n"
                  f"{preamble}"
                  f"SELECT to_jsonb(v) FROM {world}_kernel.ledger_write(:'payload'::jsonb) v;\n")
    if cp.returncode != 0:
        raise RuntimeError(f"bw_call plumbing failed: {cp.stderr}")
    return json.loads(cp.stdout.strip())


def birth(world: str) -> tuple[int, int]:
    """Direct SQL genesis (the s48 fixture's own simpler shape, no CLASSIC scaffold): genesis seed,
    stamp_secret (provisioned separately, see provision_stamp_secret), a write-boundary recording
    identity, and TWO ordinary principals this fixture's cases use as distinct actors -- 'author'
    (the obligor/closer side) and 'authority' (the annulment-authority side). ORDER IS LOAD-
    BEARING (s60 Element 5/6, the entitlement-enforcement layer this fixture's chain now carries
    since s72): entitlement_genesis_principal() is the SUBJECT of the FIRST-EVER
    principal_registered row; author-fixture SELF-registers FIRST (actor=subject=author_id) so
    genesis becomes author_id -- every subsequent write by actor=author_id then trivially reaches
    genesis (the chain's own depth-0 row already equals genesis), sidestepping a chain-of-custody
    ceremony this fixture's own cases have no need to exercise. Returns (author_id, authority_id)."""
    script = f"""
BEGIN;
INSERT INTO {world}_kernel.chain_genesis (seed)
  VALUES (encode(gen_random_bytes(32),'hex')) ON CONFLICT (only_one) DO NOTHING;
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('author-fixture', 'model') RETURNING id \\gset author_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','author (fixture, self, establishes genesis)', :author_id, :author_id, 'fixture author/obligor');
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('write-boundary', 'tool') RETURNING id \\gset wb_
INSERT INTO {world}_kernel.principal (name, agent_class)
  VALUES ('authority-fixture', 'model') RETURNING id \\gset authority_
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','write-boundary (fixture)', :author_id, :wb_id, 'kernel write boundary recording identity');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_purpose)
  VALUES ('principal_registered','authority (fixture)', :author_id, :authority_id, 'fixture annulment authority');
INSERT INTO {world}.ledger (kind, statement, actor, principal_subject, principal_db_role, principal_binding_active)
  VALUES ('principal_standing_declared','standing (fixture)', :author_id, :author_id, '{world}_rw', true);
COMMIT;
SELECT :author_id, :authority_id;
"""
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1"], input=script)
    if cp.returncode != 0:
        raise RuntimeError(f"birth sequence failed: {cp.stdout}\n{cp.stderr}")
    author_id = int(sql1(f'SELECT id FROM "{world}_kernel".principal WHERE name=\'author-fixture\';'))
    authority_id = int(sql1(f'SELECT id FROM "{world}_kernel".principal WHERE name=\'authority-fixture\';'))
    return author_id, authority_id


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


def open_claim(world: str, slug: str, author_id: int) -> None:
    o = bw_call(world, {"kind": "work_opened", "work_slug": slug, "work_title": slug,
                         "statement": f"open {slug}", "actor": author_id})
    assert o["disposition"] == "accepted", o
    c = bw_call(world, {"kind": "work_claimed", "work_slug": slug,
                         "statement": f"claim {slug}", "actor": author_id})
    assert c["disposition"] == "accepted", c


def main() -> int:
    failures: list[str] = []
    world_pre, world_main = "s73fx_pre", "s73fx_main"
    try:
        print(f"== scaffolding WORLD PRE (chain ends {CHAIN_S72[-1]}) ==")
        apply_chain(world_pre, CHAIN_S72)
        check("detect-negative-pre-s73", detect(world_pre, "s73-typed-annulment-disposition.detect.sql") == "f",
              "s73 .detect.sql reads f on the pre-s73 (s72-head) chain", failures)
        author_id_pre, _ = birth(world_pre)
        secret_pre = provision_stamp_secret(world_pre)
        ord_pre = bw_call(world_pre, {"kind": "note", "statement": "ordinary note, unaffected by s73's mere existence",
                                       "actor": author_id_pre})
        check("pre-s73-ordinary-write-unaffected", ord_pre["disposition"] == "accepted", f"{ord_pre}", failures)

        print(f"== scaffolding WORLD MAIN (chain ends {CHAIN_S73[-1]}) ==")
        apply_chain(world_main, CHAIN_S73)
        check("detect-positive-s73", detect(world_main, "s73-typed-annulment-disposition.detect.sql") == "t",
              "s73 .detect.sql reads t on the s73-applied chain", failures)

        author_id, authority_id = birth(world_main)
        secret = provision_stamp_secret(world_main)
        vendor_author = valid_vendor(secret, "sess-author", "agent-author")
        vendor_authority = valid_vendor(secret, "sess-authority", "agent-authority")

        # --- authority row: a decision written by the DISTINCT authority actor, stamped
        # distinctly -- the maintainer-ruling shape this delta's own header names (row 1087).
        auth_row = bw_call(world_main, {"kind": "decision",
                                         "statement": "authority ruling: this review debt is annulled (fixture)",
                                         "actor": authority_id}, vendor=vendor_authority)
        check("authority-row-accepted", auth_row["disposition"] == "accepted", f"{auth_row}", failures)
        auth_id = auth_row["row_id"]

        # --- ANNUL-ACCEPTED: valid, in-force, distinct-actor-and-stamp authority.
        open_claim(world_main, "annul-accept", author_id)
        acc = bw_call(world_main, {"kind": "work_closed", "work_slug": "annul-accept",
                                    "work_resolution": "dropped",
                                    "work_review_disposition": "annulled",
                                    "work_review_ref": f"row:{auth_id}",
                                    "statement": "close annul-accept, annulled by distinct authority",
                                    "actor": author_id}, vendor=vendor_author)
        check("annul-accepted", acc["disposition"] == "accepted", f"{acc}", failures)
        close_id = acc["row_id"]

        gap_rows = sql1(f'SET search_path = {world_main}; '
                         f"SELECT count(*) FROM work_review_gap WHERE close_id = {close_id};")
        check("annul-excluded-from-gap", gap_rows == "0", f"work_review_gap rows for the annulled close: {gap_rows!r}", failures)

        audit_row = sql1(f'SET search_path = {world_main}; '
                          f"SELECT authority_row_id || '|' || authority_in_force FROM work_review_annulled WHERE close_id = {close_id};")
        check("annul-audit-view-renders", audit_row == f"{auth_id}|true", f"work_review_annulled row: {audit_row!r}", failures)

        # --- ANNUL-MISSING-REF-REFUSED.
        open_claim(world_main, "annul-missing-ref", author_id)
        mr = bw_call(world_main, {"kind": "work_closed", "work_slug": "annul-missing-ref",
                                   "work_resolution": "dropped",
                                   "work_review_disposition": "annulled",
                                   "statement": "close with no ref at all",
                                   "actor": author_id}, vendor=vendor_author)
        check("annul-missing-ref-refused", mr["disposition"] == "refused", f"{mr}", failures)

        # --- ANNUL-RETRACTED-REF-REFUSED: an authority row that EXISTS but is superseded
        # (retracted) BEFORE the annulment write is attempted.
        stale_auth = bw_call(world_main, {"kind": "decision", "statement": "authority ruling, soon retracted (fixture)",
                                           "actor": authority_id}, vendor=vendor_authority)
        check("stale-authority-row-accepted", stale_auth["disposition"] == "accepted", f"{stale_auth}", failures)
        stale_auth_id = stale_auth["row_id"]
        retract = bw_call(world_main, {"kind": "decision", "statement": "retraction of the stale authority ruling",
                                        "supersedes": stale_auth_id, "actor": authority_id}, vendor=vendor_authority)
        check("stale-authority-retracted", retract["disposition"] == "accepted", f"{retract}", failures)
        open_claim(world_main, "annul-retracted-ref", author_id)
        rr = bw_call(world_main, {"kind": "work_closed", "work_slug": "annul-retracted-ref",
                                   "work_resolution": "dropped",
                                   "work_review_disposition": "annulled",
                                   "work_review_ref": f"row:{stale_auth_id}",
                                   "statement": "close citing an already-retracted authority row",
                                   "actor": author_id}, vendor=vendor_author)
        check("annul-retracted-ref-refused", rr["disposition"] == "refused", f"{rr}", failures)
        check("annul-retracted-ref-message-names-in-force",
              rr.get("message") is not None and "NOT IN FORCE" in rr["message"], f"message: {rr.get('message')!r}", failures)

        # --- ANNUL-SELF-SAME-ACTOR-REFUSED: the authority row is written by the SAME actor as
        # the obligor (the closer, since no --supersedes predecessor exists for this close).
        self_auth = bw_call(world_main, {"kind": "decision", "statement": "self-authored 'authority' (fixture)",
                                          "actor": author_id}, vendor=vendor_author)
        check("self-authority-row-accepted", self_auth["disposition"] == "accepted", f"{self_auth}", failures)
        self_auth_id = self_auth["row_id"]
        open_claim(world_main, "annul-self-same-actor", author_id)
        sa = bw_call(world_main, {"kind": "work_closed", "work_slug": "annul-self-same-actor",
                                   "work_resolution": "dropped",
                                   "work_review_disposition": "annulled",
                                   "work_review_ref": f"row:{self_auth_id}",
                                   "statement": "close citing an authority row I wrote myself",
                                   "actor": author_id}, vendor=vendor_author)
        check("annul-self-same-actor-refused", sa["disposition"] == "refused", f"{sa}", failures)
        check("annul-self-same-actor-message-names-no-self-annulment",
              sa.get("message") is not None and "no self-annulment" in sa["message"], f"message: {sa.get('message')!r}", failures)

        # --- ANNUL-SELF-SAME-STAMP-REFUSED: a DIFFERENT actor id (authority_id), but the SAME
        # (session,agent) invocation as the obligor's own close act -- the loophole this delta's
        # own header defends against composing s21 into the predicate.
        same_stamp_auth = bw_call(world_main, {"kind": "decision", "statement": "different actor, same invocation (fixture)",
                                                "actor": authority_id}, vendor=vendor_author)
        check("same-stamp-authority-row-accepted", same_stamp_auth["disposition"] == "accepted", f"{same_stamp_auth}", failures)
        same_stamp_auth_id = same_stamp_auth["row_id"]
        open_claim(world_main, "annul-self-same-stamp", author_id)
        ss = bw_call(world_main, {"kind": "work_closed", "work_slug": "annul-self-same-stamp",
                                   "work_resolution": "dropped",
                                   "work_review_disposition": "annulled",
                                   "work_review_ref": f"row:{same_stamp_auth_id}",
                                   "statement": "close citing an authority row from the SAME invocation, different actor id",
                                   "actor": author_id}, vendor=vendor_author)
        check("annul-self-same-stamp-refused", ss["disposition"] == "refused", f"{ss}", failures)
        check("annul-self-same-stamp-message-names-no-self-annulment",
              ss.get("message") is not None and "no self-annulment" in ss["message"], f"message: {ss.get('message')!r}", failures)

        # --- ANNUL-STRICT-REFUSED: annulled cannot satisfy a --strict close.
        open_claim(world_main, "annul-strict", author_id)
        strict_auth = bw_call(world_main, {"kind": "decision", "statement": "authority for the strict-close attempt (fixture)",
                                            "actor": authority_id}, vendor=vendor_authority)
        strict_auth_id = strict_auth["row_id"]
        st = bw_call(world_main, {"kind": "work_closed", "work_slug": "annul-strict",
                                   "work_resolution": "dropped",
                                   "work_review_disposition": "annulled",
                                   "work_review_ref": f"row:{strict_auth_id}",
                                   "work_strict_close": True,
                                   "statement": "strict close, annulled disposition",
                                   "actor": author_id}, vendor=vendor_author)
        check("annul-strict-refused", st["disposition"] == "refused", f"{st}", failures)
        check("annul-strict-message-names-strict",
              st.get("message") is not None and "strict close" in st["message"], f"message: {st.get('message')!r}", failures)

        # --- ANNUL-VIOLATION-DISPOSITION-KIND-REFUSED: annulled is scoped to kind=work_closed
        # alone -- refused on a work_violation_disposition row (a genuine in-force violation is
        # not required to exercise the KIND CHECK itself, which fires before any re-derivation).
        vd = bw_call(world_main, {"kind": "work_violation_disposition",
                                   "work_violation_class": "duplicate_open",
                                   "work_violation_target_id": auth_id,
                                   "work_resolution": "retired",
                                   "rationale": "fixture: exercising the kind-shape refusal only",
                                   "work_review_disposition": "annulled",
                                   "work_review_ref": f"row:{auth_id}",
                                   "statement": "attempt an annulled work_violation_disposition (refused by kind-shape)",
                                   "actor": author_id}, vendor=vendor_author)
        check("annul-violation-disposition-kind-refused", vd["disposition"] == "refused", f"{vd}", failures)

        # --- DEFENSE-IN-DEPTH-SURFACED: a separate accepted annulment whose authority is
        # retracted AFTER the annulment is on record.
        dep_auth = bw_call(world_main, {"kind": "decision", "statement": "authority, retracted AFTER the annulment (fixture)",
                                         "actor": authority_id}, vendor=vendor_authority)
        dep_auth_id = dep_auth["row_id"]
        open_claim(world_main, "annul-defense-in-depth", author_id)
        dep_close = bw_call(world_main, {"kind": "work_closed", "work_slug": "annul-defense-in-depth",
                                          "work_resolution": "dropped",
                                          "work_review_disposition": "annulled",
                                          "work_review_ref": f"row:{dep_auth_id}",
                                          "statement": "close, annulled, authority to be retracted after",
                                          "actor": author_id}, vendor=vendor_author)
        check("defense-in-depth-annul-accepted", dep_close["disposition"] == "accepted", f"{dep_close}", failures)
        dep_close_id = dep_close["row_id"]
        dep_retract = bw_call(world_main, {"kind": "decision", "statement": "retraction of the authority, after the fact",
                                            "supersedes": dep_auth_id, "actor": authority_id}, vendor=vendor_authority)
        check("defense-in-depth-authority-retracted", dep_retract["disposition"] == "accepted", f"{dep_retract}", failures)

        viol = sql1(f'SET search_path = {world_main}; '
                    f"SELECT violation FROM work_item_violations WHERE slug='annul-defense-in-depth';")
        check("defense-in-depth-surfaced-in-violations", viol == "annulled_authority_retracted",
              f"work_item_violations.violation for annul-defense-in-depth: {viol!r}", failures)
        hist = sql1(f'SET search_path = {world_main}; '
                    f"SELECT count(*) FROM work_violation_history WHERE slug='annul-defense-in-depth' "
                    f"AND violation='annulled_authority_retracted' AND target_id={dep_close_id};")
        check("defense-in-depth-surfaced-in-history", hist == "1",
              f"work_violation_history rows for annul-defense-in-depth: {hist!r}", failures)

        # ./judge --layer work AGREE on both polarities (the spec's own §2 ENGINE clause).
        judge_agree(world_pre, failures, "judge-work-AGREE-world-pre")
        judge_agree(world_main, failures, "judge-work-AGREE-world-main")

    finally:
        teardown(world_pre)
        teardown(world_main)

    if failures:
        print(f"FAIL: {len(failures)} case(s): {failures}")
        return 1
    print("all s73-typed-annulment-disposition cases WITNESSED clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
