#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T12:46:47Z
#   last-change: 2026-07-09T12:46:47Z
#   contributors: be693afb/main
# <<< PROVENANCE-STAMP <<<

"""s21_session_aware_fixture — proves the (stamp_session, stamp_agent) PAIR distinctness fix
(s21-session-aware-distinctness.sql) AND the s19 residue fold-in, on a THROWAWAY schema pair in the
TOY db (design/S21-SESSION-AWARE-DISTINCTNESS.md's witness protocol, items 1-5, run exactly):

  1. SAME-SESSION, DISTINCT-AGENT technical review PASSES (the e17 shape, preserved unchanged).
  2. CROSS-SESSION MAIN-vs-MAIN technical review PASSES — the retired false refusal: two distinct
     sessions' main threads (agent='main' both sides) are DISTINCT invocations under the pair rule,
     where the pre-s21 agent-only rule would have wrongly refused this as same-invocation.
  3. SAME PAIR (session AND agent both equal the target's) technical claim REFUSED — the
     SoD-of-invocations negative control.
  4. UNVERIFIED-stamp technical claim REFUSED (4a); a NULL stamp-half on the TARGET row is treated as
     NOT distinct even when the reviewing row is itself verified and stamp-distinct in the ordinary
     sense (4b) — fail-safe, never fail-open.
  5. THE S19 RESIDUE, reproduced and cured: with only s20 applied (no s21), a linked-row (review) INSERT
     under `SET ROLE` with NO explicit `SET search_path` FAILS ("relation \"ledger\" does not exist" —
     the documented residue); with s21 applied on top (same schema, same session), the IDENTICAL insert
     SUCCEEDS with no session-level SET — the four validate_* functions now carry their own
     `SET search_path`, exactly the s19 idiom applied to the residue s19 itself named but did not cover.

Scratch-only (schema s21probe / s21probe_kernel, role s21probe_rw — dropped after). Run in the TOY db
(not `harness`, unlike the s17/s19 fixtures) per this delta's own scratch-witness instructions. Never
applied to toycolors or any live schema. Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import subprocess
import time
from pathlib import Path

PGHOST, DB = "192.168.122.1", "toy"
SCHEMA, KERN, ROLE = "s21probe", "s21probe_kernel", "s21probe_rw"
HERE = Path(__file__).resolve().parent
LINEAGE = HERE.parent / "lineage"
SECRET = os.urandom(32)


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def apply_ddl(fname: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
                         "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}",
                         "-f", str(LINEAGE / fname)], capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def stamp(session: str, agent: str, ts: int) -> str:
    return hmac.new(SECRET, f"{session}|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()


def guc(session: str, agent: str) -> str:
    ts = int(time.time())
    return (f"SET app.vendor_session='{session}'; SET app.vendor_agent='{agent}'; "
            f"SET app.vendor_ts='{ts}'; SET app.vendor_hmac='{stamp(session, agent, ts)}'; ")


def ins_ledger(guc_sql: str, kind: str, statement: str, actor: str, regards: str = "NULL",
              with_search_path: bool = True) -> tuple[bool, str]:
    sp = f"SET search_path={SCHEMA},{KERN}; " if with_search_path else ""
    return psql(f"SET ROLE {ROLE}; {sp}{guc_sql} "
                f"INSERT INTO {SCHEMA}.ledger(kind,statement,actor,regards) "
                f"VALUES('{kind}','{statement}',{actor},{regards});")


def ins_detail(ledger_id: str, independence: str) -> tuple[bool, str]:
    return psql(f"SET ROLE {ROLE}; SET search_path={SCHEMA},{KERN}; "
                f"INSERT INTO {SCHEMA}.review_detail(ledger_id,verdict,independence,basis) "
                f"VALUES({ledger_id},'attest','{independence}','fixture');")


def ledger_id(statement: str) -> str:
    return psql(f"SELECT id FROM {SCHEMA}.ledger WHERE statement='{statement}';")[1]


def same_invocation(review_id: str) -> str:
    return psql(f"SELECT same_invocation FROM {SCHEMA}.review_stamp_distinctness "
                f"WHERE review_id={review_id};")[1]


def teardown() -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s21probe (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731
    log: list[str] = []

    teardown()
    for f in ("s15-schema.sql", "s17-stamp-mechanism.sql", "s17-independence-vocabulary.sql",
             "s19-trigger-search-path.sql", "s20-obligation-grants-and-view-refresh.sql"):
        ok, out = apply_ddl(f)
        if not ok:
            print(f"# S21 FIXTURE SETUP FAILED ({f}): {out[-300:]}")
            return 1

    psql(f"INSERT INTO {KERN}.stamp_secret(secret) VALUES (decode('{SECRET.hex()}','hex'));")
    author = psql(f"SELECT id FROM {KERN}.principal WHERE name='author';")[1]
    psql(f"SET ROLE {ROLE}; INSERT INTO {KERN}.principal(name,agent_class) VALUES('reviewer','model') ON CONFLICT DO NOTHING;")
    reviewer = psql(f"SELECT id FROM {KERN}.principal WHERE name='reviewer';")[1]

    # row A: the work, authored session='s1' agent='main'
    ins_ledger(guc("s1", "main"), "decision", "row A (the work)", author)
    a_id = ledger_id("row A (the work)")

    # ---- ITEM 5, RED half: baseline (s15+s17+s19+s20, NO s21) -- a linked (review) insert under
    # SET ROLE with NO explicit SET search_path must FAIL (the s19 residue, reproduced) ----
    red_ok, red_out = ins_ledger(guc("s1", "sub-xyz"), "review", "item5 RED probe (no search_path)",
                                 reviewer, a_id, with_search_path=False)
    ck(not red_ok and 'relation "ledger" does not exist' in red_out,
       f"ITEM 5 RED expected: pre-s21 linked insert with no SET search_path must FAIL with "
       f"'relation \"ledger\" does not exist' (got ok={red_ok}: {red_out[-200:]})")
    log.append(f"ITEM 5 RED  (pre-s21, no SET search_path): ok={red_ok}\n    {red_out.splitlines()[-1] if red_out else ''}")

    # ---- apply s21 on top of the SAME schema ----
    ok, out = apply_ddl("s21-session-aware-distinctness.sql")
    if not ok:
        print(f"# S21 FIXTURE SETUP FAILED (s21 apply): {out[-300:]}")
        teardown()
        return 1

    # ---- ITEM 5, GREEN half: the IDENTICAL insert shape, no SET search_path, now SUCCEEDS ----
    green_ok, green_out = ins_ledger(guc("s1", "sub-xyz"), "review", "item5 GREEN probe (no search_path)",
                                     reviewer, a_id, with_search_path=False)
    ck(green_ok, f"ITEM 5 GREEN expected: post-s21 linked insert with no SET search_path must SUCCEED "
                f"(got ok={green_ok}: {green_out[-200:]})")
    log.append(f"ITEM 5 GREEN (post-s21, no SET search_path): ok={green_ok}\n    {green_out.splitlines()[-1] if green_out else ''}")

    # ---- ITEM 1: SAME-session, DISTINCT-agent technical review -- PASSES (e17 shape preserved) ----
    ins_ledger(guc("s1", "sub-xyz"), "review", "item1 same-session distinct-agent", reviewer, a_id)
    r1 = ledger_id("item1 same-session distinct-agent")
    ok, out = ins_detail(r1, "technical")
    ck(ok, f"ITEM 1: same-session distinct-agent technical claim must PASS: {out[-160:]}")
    si1 = same_invocation(r1)
    ck(si1 == "f", f"ITEM 1: same_invocation must be 'f' (got {si1!r})")
    log.append(f"ITEM 1 (same-session s1/main vs s1/sub-xyz): insert ok={ok}, same_invocation={si1!r}")

    # ---- ITEM 2: CROSS-session MAIN-vs-MAIN technical review -- PASSES (retired false refusal) ----
    ins_ledger(guc("s2", "main"), "review", "item2 cross-session main-main", reviewer, a_id)
    r2 = ledger_id("item2 cross-session main-main")
    ok, out = ins_detail(r2, "technical")
    ck(ok, f"ITEM 2: cross-session main-vs-main technical claim must PASS (the retired false refusal): {out[-160:]}")
    si2 = same_invocation(r2)
    ck(si2 == "f", f"ITEM 2: same_invocation must be 'f' even though agent='main' both sides (got {si2!r})")
    log.append(f"ITEM 2 (cross-session s1/main vs s2/main): insert ok={ok}, same_invocation={si2!r}")

    # ---- ITEM 3: SAME pair (session AND agent) -- REFUSED (SoD-of-invocations negative control) ----
    ins_ledger(guc("s1", "main"), "review", "item3 same-pair negative control", reviewer, a_id)
    r3 = ledger_id("item3 same-pair negative control")
    ok, out = ins_detail(r3, "technical")
    ck(not ok and "same invocation" in out.lower(),
       f"ITEM 3: same-pair (s1/main vs s1/main) technical claim must be REFUSED+taught: ok={ok} {out[-200:]}")
    log.append(f"ITEM 3 (same pair s1/main vs s1/main): insert ok={ok}\n    {out.splitlines()[-1] if out else ''}")

    # ---- ITEM 4a: UNVERIFIED (unstamped) review -- REFUSED ----
    ins_ledger("", "review", "item4a unstamped review", reviewer, a_id)  # no vendor_* GUCs -> unstamped
    r4a = ledger_id("item4a unstamped review")
    ok, out = ins_detail(r4a, "technical")
    ck(not ok and "verified interception stamp" in out.lower(),
       f"ITEM 4a: technical claim on an UNVERIFIED review must be REFUSED: ok={ok} {out[-200:]}")
    log.append(f"ITEM 4a (unstamped reviewing row): insert ok={ok}\n    {out.splitlines()[-1] if out else ''}")

    # ---- ITEM 4b: NULL-half on the TARGET (regarded row unstamped); reviewer IS verified+distinct ----
    ins_ledger("", "decision", "item4b unstamped target", author)  # unstamped target row
    t4b = ledger_id("item4b unstamped target")
    ins_ledger(guc("s3", "distinct-agent"), "review", "item4b review of unstamped target", reviewer, t4b)
    r4b = ledger_id("item4b review of unstamped target")
    ok, out = ins_detail(r4b, "technical")
    ck(not ok and "same invocation" in out.lower(),
       f"ITEM 4b: a technical claim on a NULL-stamp-half TARGET must be REFUSED (fail-safe, not "
       f"fail-open): ok={ok} {out[-220:]}")
    log.append(f"ITEM 4b (verified reviewer, NULL-stamp target): insert ok={ok}\n    {out.splitlines()[-1] if out else ''}")

    teardown()

    print("# S21 SESSION-AWARE DISTINCTNESS FIXTURE -- witness log:")
    for line in log:
        print(f"  {line}")
    if fails:
        print("# S21 FIXTURE RED:")
        for f in fails:
            print(f"  !! {f}")
        return 1
    print("# S21 FIXTURE GREEN -- (session,agent)-pair distinctness (items 1-4) and the s19 residue "
          "cure (item 5) all witnessed, both polarities where applicable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
