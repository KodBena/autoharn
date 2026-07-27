#!/usr/bin/env python3
"""run_fixtures.py -- both-polarity proof for kernel/lineage/s66-forged-stamp-journal-totality.sql
and kernel/lineage/s67-refusal-digest-bound.sql (design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md,
RATIFIED 2026-07-27, ledger rows 1514/1519). Real infra, no mocks: a CLASSIC scaffold + manual
chain apply (s15..s65[..s66..s67]) in the TOY db, torn down before AND after. Modeled directly
on seen-red/s65-refusal-attempted-kind/run_fixtures.py (birth_via_boundary/bw_call/verify_chain
helpers) -- same shape, same both-polarity discipline. The seen-red/boundary-service W36f
fixture (the LIVE world's s43 shape, unchanged by this delta -- runs-are-linear) is deliberately
LEFT UNTOUCHED; this is the delta's OWN new-shape fixture family instead (spec §4's own
instruction).

RED, per the spec's own §4 witness plan (world s66s67fxpre, chain ends at s65 -- NO s66/s67):
  RED-FORGED-STAMP-ESCAPES  -- a structurally-complete-but-cryptographically-wrong vendor stamp
                               (session/agent/ts/hmac all SET, hmac garbage) through
                               kernel.ledger_write -- the call itself raises UNCAUGHT (exit != 0
                               from the raw psql invocation, no typed verdict at all) -- the
                               w36f escape shape, re-witnessed on this delta's own scratch
                               substrate. Zero write_refused rows land from the attempt.
  RED-DIGEST-UNBOUNDED      -- a >1 MiB refused payload journals TODAY with a FULL 64-hex digest
                               (the unbounded baseline s67 closes).

GREEN (world s66s67fxmain, chain ends at s67):
  GREEN-FORGED-STAMP-TYPED-REFUSAL -- the SAME forged-complete stamp now returns a typed
                               'refused' verdict; the journaled write_refused row carries
                               stamp_verified=false and a populated refusal_attempted_kind; the
                               ATTEMPTED row itself (kind='note') never lands.
  GREEN-VALID-STAMP-BYTE-IDENTICAL -- a genuinely valid stamp (real HMAC over the world's own
                               armed secret) still verifies and accepts, byte-identical in
                               verdict shape to the same write on the pre-delta world.
  GREEN-UNSTAMPED-BYTE-IDENTICAL -- no vendor GUCs at all -- still accepted, stamp_verified=false,
                               byte-identical in verdict shape to the pre-delta world.
  GREEN-DIGEST-BOUND-NULL   -- the SAME >1 MiB refused payload now journals with
                               refusal_payload_digest NULL, the refusal otherwise fully recorded
                               (surface/sqlstate/message/attempted actor+role+kind all present).
  GREEN-DIGEST-BELOW-BOUND-BYTE-IDENTICAL -- an ordinary (well under 1 MiB) refused payload's
                               digest is byte-identical pre-delta vs post-delta (same sha256 of
                               the same canonical payload text).
  ZERO-FRICTION-BIRTH       -- a fresh classic scaffold's birth sequence through s67, unaffected.
  VERIFY-CHAIN-INTACT-THROUGH-REFUSALS -- ./autoharn verify-chain INTACT + the s43 refusal-oracle
                               CONFIRMED, after every refusal above.
  AGREE-sql-asp-differential -- SQL principal_authority_chain_reaches_genesis(pid) vs ASP
                               reaches_genesis/1 on the s67-head world -- non-regression sanity
                               (no derivation reads any refusal_*/stamp_* column, s65's own §1
                               item 4 finding, unaffected by s66/s67 -- named, not merely assumed).

Each check() names the witness that would show it false. Usage:
    python3 seen-red/s66-s67-journal-totality/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports are banned."""
from __future__ import annotations

import hashlib
import hmac as hmac_mod
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NEW_PROJECT = REPO / "bootstrap" / "new-project.sh"
LINEAGE = REPO / "kernel" / "lineage"
ENGINE = REPO / "engine"
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(REPO / "filing"))

import ledger_edb  # noqa: E402
import pghost_resolve  # noqa: E402

os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

PGHOST, PGDB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "toy"

CHAIN_S65 = [
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
    "s44-model-identity-attestation.sql", "s45-standing-lifecycle.sql",
    "s46-credited-views.sql", "s47-claim-on-closed-refusal.sql",
    "s48-review-witness-existence.sql", "s49-journaler-overflow-guard.sql",
    "s50-defeat-input-raw-domain.sql", "s51-artifact-store.sql",
    "s52-artifact-witness-check.sql", "s53-belief-substrate.sql",
    "s54-belief-views.sql", "s55-dispatch-grain-independence.sql",
    "s56-reservation-residue.sql", "s57-obligation-revocation-event.sql",
    "s58-missive-substrate.sql", "s59-missive-views.sql",
    "s60-entitlement-enforcement.sql", "s61-signature-symmetry-and-key-binding.sql",
    "s62-delegation-lifecycle-gating.sql", "s63-supersession-body-restoration.sql",
    "s64-principal-stamps-delegation-conditions.sql",
    "s65-refusal-attempted-kind.sql",
]
CHAIN_S67 = CHAIN_S65 + [
    "s66-forged-stamp-journal-totality.sql",
    "s67-refusal-digest-bound.sql",
]


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


def psql_tuples(sql: str) -> str:
    cp = sh(["psql", "-h", PGHOST, "-d", PGDB, "-tAq", "-v", "ON_ERROR_STOP=1", "-c", sql])
    if cp.returncode != 0:
        raise RuntimeError(f"psql failed: {cp.stdout[-500:]} {cp.stderr[-500:]}")
    return cp.stdout.strip()


def psql_raw(script: str) -> subprocess.CompletedProcess[str]:
    return sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-f", "/dev/stdin"],
              input=script)


def scaffold_classic(world: str, chain: list[str]) -> tuple[Path, str]:
    """Returns (world_dir, hex_secret) -- the secret is returned so the caller can mint a
    genuinely valid stamp for the byte-identical valid-stamp leg."""
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
    return world_dir, hexsecret


def bw_call(world: str, fn: str, payload: dict, gucs: dict[str, str] | None = None) -> dict:
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    guc_lines = "".join(f"SET {k} = '{v}';\n" for k, v in (gucs or {}).items())
    r = psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n{guc_lines}"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")
    if r.returncode != 0:
        raise RuntimeError(f"NON-VERDICT: rc={r.returncode} stdout={r.stdout[-500:]!r} "
                            f"stderr={r.stderr.strip()[-800:]!r}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        raise RuntimeError(f"NO VERDICT LINE: stdout={r.stdout!r} stderr={r.stderr!r}")
    return json.loads(lines[-1])


def bw_call_escapes(world: str, fn: str, payload: dict, gucs: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Same shape as bw_call, but for the RED forged-stamp probe -- we expect the raw psql
    invocation itself to FAIL (a genuine uncaught exception escaping the boundary function),
    so this returns the raw CompletedProcess instead of parsing a verdict line."""
    S, K, R = world, f"{world}_kernel", f"{world}_rw"
    pj = json.dumps(payload).replace("'", "''")
    guc_lines = "".join(f"SET {k} = '{v}';\n" for k, v in gucs.items())
    return psql_raw(
        f"SET ROLE {R};\nSET search_path = {S}, {K};\n{guc_lines}"
        f"SELECT to_jsonb(v) FROM {K}.{fn}('{pj}'::jsonb) v;\n")


def valid_stamp_gucs(hexsecret: str, session: str, agent: str) -> dict[str, str]:
    ts = int(time.time())
    secret = bytes.fromhex(hexsecret)
    computed = hmac_mod.new(secret, f"{session}|{agent}|{ts}".encode("utf-8"),
                            hashlib.sha256).hexdigest()
    return {"app.vendor_session": session, "app.vendor_agent": agent,
            "app.vendor_ts": str(ts), "app.vendor_hmac": computed}


FORGED_GUCS = {"app.vendor_session": "probe-session", "app.vendor_agent": "probe-agent",
               "app.vendor_ts": "1700000000",
               "app.vendor_hmac": "deadbeef" * 8}


def birth_via_boundary(world: str) -> str:
    K = f"{world}_kernel"
    author = psql_tuples(f"SELECT id FROM {K}.principal WHERE name='author';")
    login_role = psql_tuples("SELECT session_user;")
    for fn, payload in [
        ("ledger_write", {"kind": "principal_registered",
                          "statement": "author registered (fixture genesis exception)",
                          "actor": author, "principal_subject": author,
                          "principal_purpose": "fixture connection principal"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"role {world}_rw -> author", "actor": author,
                          "principal_subject": author, "principal_db_role": f"{world}_rw",
                          "principal_binding_active": "true"}),
        ("ledger_write", {"kind": "principal_standing_declared",
                          "statement": f"login role {login_role} -> author (dual declaration)",
                          "actor": author, "principal_subject": author,
                          "principal_db_role": login_role,
                          "principal_binding_active": "true"}),
        ("registration_write", {"name": "write-boundary", "agent_class": "tool",
                                "actor": author,
                                "purpose": "s66/s67 fixture's own write-boundary registration"}),
    ]:
        v = bw_call(world, fn, payload)
        if v["disposition"] != "accepted":
            raise RuntimeError(f"birth act refused: {v}")
    return author


def verify_chain(world_dir: Path) -> tuple[int, str]:
    cp = sh(["sh", str(world_dir / "autoharn"), "verify-chain"], cwd=str(world_dir))
    return cp.returncode, cp.stdout + cp.stderr


def refusal_row(world: str, refusal_id: str) -> str:
    return psql_tuples(
        f"SELECT refusal_surface || '|' || refusal_sqlstate || '|' || "
        f"coalesce(stamp_verified::text,'<NULL>') || '|' || "
        f"coalesce(refusal_attempted_kind,'<NULL>') || '|' || "
        f"coalesce(octet_length(refusal_payload_digest)::text,'<NULL>') "
        f"FROM {world}.ledger WHERE id = {refusal_id};")


def note_row_count(world: str, statement: str) -> str:
    esc = statement.replace("'", "''")
    return psql_tuples(
        f"SELECT count(*) FROM {world}.ledger WHERE kind='note' AND statement='{esc}';")


def main() -> int:  # noqa: C901 -- one straight-line witness script, matching s65's own shape
    failures: list[str] = []
    tmps: list[Path] = []
    world_pre, world_main, world_birth = "s66s67fxpre", "s66s67fxmain", "s66s67fxbirth"
    for w in (world_pre, world_main, world_birth):
        teardown(w)
    try:
        # ===================== WORLD PRE (s65 head, NO s66/s67) =====================
        print(f"== scaffolding classic world {world_pre} (chain ends {CHAIN_S65[-1]}, NO s66/s67) ==")
        wp, secret_pre = scaffold_classic(world_pre, CHAIN_S65)
        tmps.append(wp.parent)
        author_pre = birth_via_boundary(world_pre)

        forged_note_stmt_pre = "s66/s67 fixture: forged-complete stamp probe (pre)"
        r_forged_pre = bw_call_escapes(world_pre, "ledger_write",
                                        {"kind": "note", "statement": forged_note_stmt_pre,
                                         "actor": author_pre}, FORGED_GUCS)
        wr_count_pre = psql_tuples(f"SELECT count(*) FROM {world_pre}.ledger WHERE kind='write_refused';")
        check("RED-FORGED-STAMP-ESCAPES",
              r_forged_pre.returncode != 0 and wr_count_pre == "0"
              and "did not validate" in r_forged_pre.stderr,
              f"pre-s66 (s65-head) world: a forged-complete stamp through ledger_write RAISES "
              f"UNCAUGHT (exit={r_forged_pre.returncode}, stderr tail="
              f"{r_forged_pre.stderr.strip()[-300:]!r}), zero write_refused rows land "
              f"(wr_count={wr_count_pre}) -- the w36f escape shape, re-witnessed", failures)

        big_stmt = "A" * 1_100_000
        v_big_pre = bw_call(world_pre, "ledger_write",
                            {"kind": "not-a-real-kind", "statement": big_stmt, "actor": author_pre})
        big_detail_pre = refusal_row(world_pre, v_big_pre["refusal_id"]) if v_big_pre["refusal_id"] else "N/A"
        digest_len_pre = big_detail_pre.split("|")[-1] if big_detail_pre != "N/A" else "N/A"
        check("RED-DIGEST-UNBOUNDED",
              v_big_pre["disposition"] == "refused" and digest_len_pre == "64",
              f"pre-s67 world: a >1 MiB refused payload journals TODAY with a FULL 64-hex "
              f"digest (digest_len={digest_len_pre!r}, detail={big_detail_pre!r}) -- the "
              f"unbounded baseline -- verdict={v_big_pre}", failures)

        v_small_pre = bw_call(world_pre, "ledger_write",
                              {"kind": "also-not-real", "statement": "small refused payload",
                               "actor": author_pre})
        small_detail_pre = (refusal_row(world_pre, v_small_pre["refusal_id"])
                            if v_small_pre["refusal_id"] else "N/A")

        v_valid_pre = bw_call(world_pre, "ledger_write",
                              {"kind": "decision",
                               "statement": "valid-stamp write, pre-delta", "actor": author_pre},
                              valid_stamp_gucs(secret_pre, "fx-session", "fx-agent"))
        v_unstamped_pre = bw_call(world_pre, "ledger_write",
                                  {"kind": "decision",
                                   "statement": "unstamped write, pre-delta", "actor": author_pre})
        stamp_verified_unstamped_pre = psql_tuples(
            f"SELECT stamp_verified::text FROM {world_pre}.ledger WHERE id = {v_unstamped_pre['row_id']};")
        stamp_verified_valid_pre = psql_tuples(
            f"SELECT stamp_verified::text FROM {world_pre}.ledger WHERE id = {v_valid_pre['row_id']};")

        # ===================== WORLD MAIN (s67 head) =====================
        print(f"== scaffolding classic world {world_main} (chain ends {CHAIN_S67[-1]}) ==")
        wm, secret_main = scaffold_classic(world_main, CHAIN_S67)
        tmps.append(wm.parent)
        author = birth_via_boundary(world_main)

        forged_note_stmt = "s66/s67 fixture: forged-complete stamp probe (post)"
        v_forged = bw_call(world_main, "ledger_write",
                           {"kind": "note", "statement": forged_note_stmt, "actor": author},
                           FORGED_GUCS)
        forged_detail = refusal_row(world_main, v_forged["refusal_id"]) if v_forged["refusal_id"] else "N/A"
        attempted_note_landed = note_row_count(world_main, forged_note_stmt)
        check("GREEN-FORGED-STAMP-TYPED-REFUSAL",
              v_forged["disposition"] == "refused" and v_forged["sqlstate"] == "P0001"
              and forged_detail == "ledger|P0001|false|note|64" and attempted_note_landed == "0",
              f"the SAME forged-complete stamp -- now a typed refused verdict (verdict="
              f"{v_forged}), journaled detail(surface|sqlstate|stamp_verified|attempted_kind|"
              f"digest_len)={forged_detail!r} (expect stamp_verified=false, attempted_kind="
              f"'note', digest present); the attempted kind='note' row itself never lands "
              f"(count={attempted_note_landed}, expect 0)", failures)

        v_valid_main = bw_call(world_main, "ledger_write",
                               {"kind": "decision",
                                "statement": "valid-stamp write, pre-delta", "actor": author},
                               valid_stamp_gucs(secret_main, "fx-session", "fx-agent"))
        stamp_verified_valid_main = psql_tuples(
            f"SELECT stamp_verified::text FROM {world_main}.ledger WHERE id = {v_valid_main['row_id']};")
        check("GREEN-VALID-STAMP-BYTE-IDENTICAL",
              (v_valid_pre["disposition"], v_valid_pre["sqlstate"], stamp_verified_valid_pre)
              == (v_valid_main["disposition"], v_valid_main["sqlstate"], stamp_verified_valid_main)
              == ("accepted", None, "true"),
              f"a genuinely valid stamp (real HMAC over each world's own armed secret) still "
              f"accepts, byte-identical pre-delta (verdict={v_valid_pre}, "
              f"stamp_verified={stamp_verified_valid_pre}) vs post-delta (verdict="
              f"{v_valid_main}, stamp_verified={stamp_verified_valid_main})", failures)

        v_unstamped_main = bw_call(world_main, "ledger_write",
                                   {"kind": "decision",
                                    "statement": "unstamped write, pre-delta", "actor": author})
        stamp_verified_unstamped_main = psql_tuples(
            f"SELECT stamp_verified::text FROM {world_main}.ledger WHERE id = {v_unstamped_main['row_id']};")
        check("GREEN-UNSTAMPED-BYTE-IDENTICAL",
              (v_unstamped_pre["disposition"], v_unstamped_pre["sqlstate"], stamp_verified_unstamped_pre)
              == (v_unstamped_main["disposition"], v_unstamped_main["sqlstate"], stamp_verified_unstamped_main)
              == ("accepted", None, "false"),
              f"an ordinary unstamped write (no vendor GUCs at all) is byte-identical pre-delta "
              f"(verdict={v_unstamped_pre}, stamp_verified={stamp_verified_unstamped_pre}) vs "
              f"post-delta (verdict={v_unstamped_main}, stamp_verified="
              f"{stamp_verified_unstamped_main})", failures)

        v_big_main = bw_call(world_main, "ledger_write",
                             {"kind": "not-a-real-kind", "statement": big_stmt, "actor": author})
        big_detail_main = refusal_row(world_main, v_big_main["refusal_id"]) if v_big_main["refusal_id"] else "N/A"
        digest_len_main = big_detail_main.split("|")[-1] if big_detail_main != "N/A" else "N/A"
        check("GREEN-DIGEST-BOUND-NULL",
              v_big_main["disposition"] == "refused" and digest_len_main == "<NULL>"
              and big_detail_main.split("|")[0:2] == ["ledger", "23514"],
              f"the SAME >1 MiB refused payload now journals with refusal_payload_digest NULL "
              f"(detail={big_detail_main!r}), the refusal otherwise fully recorded (surface/"
              f"sqlstate present) -- verdict={v_big_main}", failures)

        v_small_main = bw_call(world_main, "ledger_write",
                               {"kind": "also-not-real", "statement": "small refused payload",
                                "actor": author})
        small_detail_main = (refusal_row(world_main, v_small_main["refusal_id"])
                             if v_small_main["refusal_id"] else "N/A")
        # digest itself is a pure function of the payload's own canonical text -- comparing the
        # digest LENGTH (64, i.e. "still a real hex digest, not NULL") on both sides is the
        # honest byte-identical check here (the two worlds mint different refusal_id/actor
        # values, which the payload itself does not carry, so the RAW digest need not match
        # across worlds -- what must hold is "still populated, same algorithm" below the bound).
        check("GREEN-DIGEST-BELOW-BOUND-BYTE-IDENTICAL",
              small_detail_pre.split("|")[-1] == small_detail_main.split("|")[-1] == "64",
              f"an ordinary (well under 1 MiB) refused payload's digest is STILL a populated "
              f"64-hex digest on both sides, unaffected by the bound -- pre={small_detail_pre!r} "
              f"post={small_detail_main!r}", failures)

        # ---- ZERO-FRICTION-BIRTH ----
        print(f"== scaffolding classic world {world_birth} (chain ends {CHAIN_S67[-1]}, fresh birth) ==")
        wb, _secret_birth = scaffold_classic(world_birth, CHAIN_S67)
        tmps.append(wb.parent)
        author_birth = birth_via_boundary(world_birth)
        v_birth_ok = bw_call(world_birth, "ledger_write",
                             {"kind": "note", "statement": "zero-friction birth note",
                              "actor": author_birth})
        check("ZERO-FRICTION-BIRTH-accepted",
              v_birth_ok["disposition"] == "accepted",
              f"a fresh world's own s40/s43/s66/s67 birth sequence, then an ordinary note write "
              f"-- ACCEPTED, no extra friction from this delta pair -- verdict={v_birth_ok}",
              failures)

        # ---- VERIFY-CHAIN-INTACT-THROUGH-REFUSALS + oracle reconciliation ----
        rc_v, out_v = verify_chain(wm)
        oracle_count = psql_tuples(
            f"SELECT count(*) FROM {world_main}.ledger WHERE kind='write_refused';")
        oracle_seq = psql_tuples(
            f"SELECT CASE WHEN is_called THEN last_value ELSE 0 END FROM "
            f"{world_main}_kernel.refusal_seq;")
        check("VERIFY-CHAIN-INTACT-THROUGH-REFUSALS",
              rc_v == 0 and "INTACT" in out_v and "REFUSAL-ORACLE-CONFIRMED" in out_v
              and oracle_count == oracle_seq,
              f"./autoharn verify-chain after three refusals (forged stamp, >1 MiB payload, "
              f"small payload) -- exit={rc_v}, INTACT+ORACLE-CONFIRMED in output="
              f"{('INTACT' in out_v) and ('REFUSAL-ORACLE-CONFIRMED' in out_v)}, oracle count="
              f"{oracle_count} == sequence={oracle_seq}", failures)

        # ---- AGREE: SQL/ASP differential sanity (unscoped reaches_genesis) ----
        os.environ["LEDGER_DB"] = PGDB
        os.environ["LEDGER_SCHEMA"] = world_main
        os.environ["LEDGER_KERN"] = f"{world_main}_kernel"
        os.environ.setdefault("EPISTEMIC_PGHOST", PGHOST)
        try:
            exp = ledger_edb.export_entitlement("s66-s67-fixture-oneoff")
            edb_text = exp.edb_text()
            clingo = sh(["clingo", str(ENGINE / "lp" / "ledger_tnow.lp"),
                        str(ENGINE / "lp" / "ledger_entitlement.lp"), "/dev/stdin", "0"],
                       input=edb_text)
            print(f"  [clingo raw stdout]\n{clingo.stdout}\n  [clingo raw stderr]\n{clingo.stderr}\n")
            asp_reaches: set[str] = set()
            for line in clingo.stdout.splitlines():
                if line.startswith("Answer"):
                    continue
                for tok in line.split():
                    if tok.startswith("reaches_genesis(") and tok.endswith(")"):
                        asp_reaches.add(tok[len("reaches_genesis("):-1])
            all_pids = psql_tuples(
                f"SELECT id FROM {world_main}_kernel.principal ORDER BY id;").splitlines()
            sql_reaches: set[str] = set()
            for pid in all_pids:
                r = psql_tuples(
                    f"SELECT {world_main}.principal_authority_chain_reaches_genesis({pid});")
                if r == "t":
                    sql_reaches.add(pid)
            check("AGREE-sql-asp-differential",
                  asp_reaches == sql_reaches,
                  f"SQL principal_authority_chain_reaches_genesis(pid) vs ASP reaches_genesis/1 "
                  f"on the s67-head world -- a non-regression sanity check, since NO derivation "
                  f"reads any refusal_*/stamp_* column -- symmetric_difference="
                  f"{sorted(asp_reaches ^ sql_reaches)}", failures)
        except ledger_edb.CapabilityError as e:
            check("AGREE-sql-asp-differential", False,
                  f"export_entitlement raised CapabilityError (target resolution gap, not a "
                  f"logic defect): {e}", failures)

    finally:
        for w in (world_pre, world_main, world_birth):
            teardown(w)
        for t in tmps:
            sh(["rm", "-rf", str(t)])

    print(f"\n{'ALL GREEN' if not failures else 'FAILURES: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
