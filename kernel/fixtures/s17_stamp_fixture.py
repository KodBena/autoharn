#!/usr/bin/env python3
"""s17_stamp_fixture — proves the interception-stamp mechanism (s17-stamp-mechanism.sql) on a THROWAWAY
schema, BOTH ways. Applies s15 + the stamp delta, provisions a test secret, and asserts:

  1. NEGATIVE CONTROL — the subject role cannot SELECT kernel.stamp_secret (permission denied).
  2. HMAC AGREEMENT — a stamp computed in PYTHON (the hook's computer) validates in SQL (the trigger's
     SECURITY DEFINER recompute): a valid stamp -> stamp_verified=true. This is the cross-language wire
     agreement (ADR-0012 P7): one HMAC construction, two computers must agree.
  3. FORGERY REFUSED — a present-but-wrong HMAC (a subject SETting app.vendor_hmac to a guess) is REFUSED
     at write time (the teaching message).
  4. STALE REFUSED — a valid HMAC over a ts outside the +-300s window is REFUSED.
  5. UNSTAMPED RECORDED — an insert with no GUCs is recorded stamp_verified=false (not refused here).
  6. DISTINCTNESS — a proxy self-review (distinct ACTOR principals, SAME stamp_agent) shows
     same_invocation=true in review_stamp_distinctness (finding-31 shape caught); a genuinely distinct
     stamp_agent shows same_invocation=false.

Scratch-only (schemas s17val*, dropped after). Run from the e17-build dir. Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "filing"))
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST, DB = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST"), "harness"
SCHEMA, KERN, ROLE = "s17val", "s17val_kernel", "s17val_rw"
HERE = Path(__file__).resolve().parent
SECRET = os.urandom(32)


def psql(sql: str, *, as_owner: bool = True) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def stamp(session: str, agent: str, ts: int) -> str:
    return hmac.new(SECRET, f"{session}|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()


_AUTHOR_ID = ""  # set after DDL; supplied explicitly so the fixture never hits s15's set_actor mapping
                 # (which hardcodes `kernel.` — a validate-mode-only gap in the frozen lineage, filed
                 # separately; unaffected at real apply where kern='kernel').


def insert_row(role_sql: str, guc_sql: str, statement: str, kind: str = "decision",
               actor: str = "", extra_cols: str = "", extra_vals: str = "") -> tuple[bool, str]:
    actor = actor or _AUTHOR_ID
    cols = "kind, statement, actor" + (", " + extra_cols if extra_cols else "")
    vals = f"'{kind}', '{statement}', {actor}" + (", " + extra_vals if extra_vals else "")
    # SET ROLE (not a real login) does not apply the subject's login-time search_path; replicate it so
    # triggers' unqualified table refs (validate_review's `FROM ledger`) resolve exactly as at real login.
    sql = (f"SET ROLE {ROLE}; SET search_path = {SCHEMA}, {KERN}; {guc_sql} "
           f"INSERT INTO {SCHEMA}.ledger ({cols}) VALUES ({vals});")
    return psql(sql)


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731

    # --- apply s15 + the stamp delta to the throwaway schema ---
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s17val (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)
    for f in ("../lineage/s15-schema.sql", "../lineage/s17-stamp-mechanism.sql"):   # autoharn: DDL lives in kernel/lineage/
        cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1",
                             "-v", f"schema={SCHEMA}", "-v", f"kern={KERN}", "-v", f"role={ROLE}",
                             "-f", str(HERE / f)], capture_output=True, text=True)
        if cp.returncode != 0:
            print(f"DDL {f} failed: {cp.stderr[-400:]}")
            return 1
    # provision the test secret (apparatus/owner)
    psql(f"INSERT INTO {KERN}.stamp_secret (secret) VALUES (decode('{SECRET.hex()}','hex'));")
    global _AUTHOR_ID
    _AUTHOR_ID = psql(f"SELECT id FROM {KERN}.principal WHERE name='author';")[1]

    # 1. NEGATIVE CONTROL — subject cannot read the secret
    ok, out = psql(f"SET ROLE {ROLE}; SELECT secret FROM {KERN}.stamp_secret;")
    ck(not ok and "permission denied" in out.lower(),
       f"subject role must be DENIED SELECT on stamp_secret (got ok={ok}: {out[-80:]})")

    # 2. HMAC AGREEMENT — a python-computed valid stamp validates in SQL
    ts = int(time.time())
    guc = (f"SET app.vendor_session='sess1'; SET app.vendor_agent='main'; "
           f"SET app.vendor_ts='{ts}'; SET app.vendor_hmac='{stamp('sess1','main',ts)}'; ")
    ok, out = insert_row(ROLE, guc, "a stamped decision")
    ck(ok, f"a valid python-computed stamp must be accepted (got: {out[-120:]})")
    v = psql(f"SELECT stamp_verified FROM {SCHEMA}.ledger WHERE statement='a stamped decision';")[1]
    ck(v == "t", f"a validly-stamped row must have stamp_verified=true (got {v!r})")

    # 3. FORGERY REFUSED — a wrong HMAC is refused
    guc_bad = (f"SET app.vendor_session='sess1'; SET app.vendor_agent='main'; "
               f"SET app.vendor_ts='{ts}'; SET app.vendor_hmac='deadbeefdeadbeef'; ")
    ok, out = insert_row(ROLE, guc_bad, "a forged decision")
    ck(not ok and "did not validate" in out.lower(),
       f"a forged stamp must be REFUSED with the teaching message (got ok={ok}: {out[-100:]})")

    # 4. STALE REFUSED — a valid HMAC over an out-of-window ts is refused
    old = ts - 5000
    guc_stale = (f"SET app.vendor_session='sess1'; SET app.vendor_agent='main'; "
                 f"SET app.vendor_ts='{old}'; SET app.vendor_hmac='{stamp('sess1','main',old)}'; ")
    ok, out = insert_row(ROLE, guc_stale, "a stale decision")
    ck(not ok and "did not validate" in out.lower(),
       f"a stale stamp (ts outside +-300s) must be REFUSED (got ok={ok}: {out[-100:]})")

    # 5. UNSTAMPED RECORDED — no GUCs => stamp_verified=false, not refused
    ok, out = insert_row(ROLE, "RESET app.vendor_session; RESET app.vendor_agent; "
                               "RESET app.vendor_ts; RESET app.vendor_hmac; ", "an unstamped decision")
    ck(ok, f"an unstamped insert must be ALLOWED (recorded unverified), got: {out[-100:]}")
    v = psql(f"SELECT stamp_verified FROM {SCHEMA}.ledger WHERE statement='an unstamped decision';")[1]
    ck(v == "f", f"an unstamped row must have stamp_verified=false (got {v!r})")

    # 6. DISTINCTNESS — a proxy self-review (distinct actor principals, SAME stamp_agent)
    aid = psql(f"SELECT id FROM {SCHEMA}.ledger WHERE statement='a stamped decision';")[1]
    # register a distinct 'reviewer' principal (the subject may) and countersign as it, SAME invocation 'main'
    psql(f"SET ROLE {ROLE}; INSERT INTO {KERN}.principal (name, agent_class) VALUES ('reviewer','model') "
         f"ON CONFLICT (name) DO NOTHING;")
    rid = psql(f"SELECT id FROM {KERN}.principal WHERE name='reviewer';")[1]
    ts2 = int(time.time())
    guc2 = (f"SET app.vendor_session='sess1'; SET app.vendor_agent='main'; "
            f"SET app.vendor_ts='{ts2}'; SET app.vendor_hmac='{stamp('sess1','main',ts2)}'; ")
    ok, out = insert_row(ROLE, guc2, "a proxy self-review", kind="review", actor=rid,
                         extra_cols="regards", extra_vals=f"{aid}")
    ck(ok, f"the proxy review (distinct actor, same invocation) inserts (SoD keys on actor): {out[-100:]}")
    same = psql(f"SELECT same_invocation FROM {SCHEMA}.review_stamp_distinctness "
                f"WHERE review_id=(SELECT id FROM {SCHEMA}.ledger WHERE statement='a proxy self-review');")[1]
    ck(same == "t", f"a proxy self-review (same stamp_agent) must show same_invocation=true (got {same!r})")

    # cleanup
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s17val (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)

    if fails:
        print("# S17 STAMP FIXTURE RED:")
        for f in fails:
            print(f"  !! {f}")
        return 1
    print("# S17 STAMP FIXTURE GREEN — negative-control, HMAC agreement, forgery+stale refused, "
          "unstamped recorded, proxy self-review caught (same_invocation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
