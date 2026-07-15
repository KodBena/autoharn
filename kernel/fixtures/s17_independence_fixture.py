#!/usr/bin/env python3
"""s17_independence_fixture — proves the independence vocabulary + stamp-distinctness gate
(s17-independence-vocabulary.sql) on a THROWAWAY schema. Applies s15 + stamp delta + independence delta,
provisions a secret, and asserts (finding 31 / the e17 refuse-and-teach lever):

  1. self-review ALWAYS allowed (an author reviewing own work, honest).
  2. an independence CLAIM (technical) by the SAME invocation as the reviewed row is REFUSED + taught
     (proxy_written — one context countersigning its own work as independent).
  3. an independence claim by a DISTINCT invocation (different stamp_agent) is ALLOWED (HONEST-DISTINCT).
  4. an independence claim on an UNVERIFIED (unstamped) review is REFUSED (cannot establish distinctness).

Scratch-only (schemas s17iv*, dropped). Lazy imports banned.
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
SCHEMA, KERN, ROLE = "s17iv", "s17iv_kernel", "s17iv_rw"
HERE = Path(__file__).resolve().parent
SECRET = os.urandom(32)


def psql(sql: str) -> tuple[bool, str]:
    cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                        capture_output=True, text=True)
    return cp.returncode == 0, (cp.stdout + cp.stderr).strip()


def stamp(agent: str, ts: int) -> str:
    return hmac.new(SECRET, f"sess|{agent}|{ts}".encode(), hashlib.sha256).hexdigest()


def guc(agent: str) -> str:
    ts = int(time.time())
    return (f"SET app.vendor_session='sess'; SET app.vendor_agent='{agent}'; "
            f"SET app.vendor_ts='{ts}'; SET app.vendor_hmac='{stamp(agent, ts)}'; ")


def ins_ledger(agent_guc: str, kind: str, statement: str, actor: str, regards: str = "NULL") -> tuple[bool, str]:
    return psql(f"SET ROLE {ROLE}; SET search_path={SCHEMA},{KERN}; {agent_guc} "
                f"INSERT INTO {SCHEMA}.ledger(kind,statement,actor,regards) "
                f"VALUES('{kind}','{statement}',{actor},{regards});")


def ins_detail(ledger_id: str, independence: str) -> tuple[bool, str]:
    return psql(f"SET ROLE {ROLE}; SET search_path={SCHEMA},{KERN}; "
                f"INSERT INTO {SCHEMA}.review_detail(ledger_id,verdict,independence,basis) "
                f"VALUES({ledger_id},'attest','{independence}','b');")


def main() -> int:
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s17iv (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)
    for f in ("../lineage/s15-schema.sql", "../lineage/s17-stamp-mechanism.sql", "../lineage/s17-independence-vocabulary.sql"):   # autoharn: DDL lives in kernel/lineage/
        cp = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-v", f"schema={SCHEMA}",
                             "-v", f"kern={KERN}", "-v", f"role={ROLE}", "-f", str(HERE / f)],
                            capture_output=True, text=True)
        if cp.returncode != 0:
            print(f"DDL {f} failed: {cp.stderr[-300:]}"); return 1
    psql(f"INSERT INTO {KERN}.stamp_secret(secret) VALUES (decode('{SECRET.hex()}','hex'));")
    author = psql(f"SELECT id FROM {KERN}.principal WHERE name='author';")[1]
    psql(f"SET ROLE {ROLE}; INSERT INTO {KERN}.principal(name,agent_class) VALUES('reviewer','model') ON CONFLICT DO NOTHING;")
    reviewer = psql(f"SELECT id FROM {KERN}.principal WHERE name='reviewer';")[1]

    # author a row as invocation 'main'
    ins_ledger(guc("main"), "decision", "the work", author)
    aid = psql(f"SELECT id FROM {SCHEMA}.ledger WHERE statement='the work';")[1]

    # 1. self-review by 'main' — always allowed. NOTE validate_review still requires a distinct actor
    #    PRINCIPAL (SoD keys on actor), so the honest self-review uses the reviewer principal but declares
    #    independence='self-review' truthfully (same INVOCATION 'main'); the gate allows it regardless of stamp.
    ins_ledger(guc("main"), "review", "self countersign", reviewer, aid)
    rid1 = psql(f"SELECT id FROM {SCHEMA}.ledger WHERE statement='self countersign';")[1]
    ok, out = ins_detail(rid1, "self-review")
    ck(ok, f"self-review must be allowed: {out[-90:]}")

    # 2. independence claim by the SAME invocation ('main') as the author — REFUSED + taught
    ins_ledger(guc("main"), "review", "proxy independent", reviewer, aid)
    rid2 = psql(f"SELECT id FROM {SCHEMA}.ledger WHERE statement='proxy independent';")[1]
    ok, out = ins_detail(rid2, "technical")
    ck(not ok and "same invocation" in out.lower(),
       f"a technical claim by the same invocation must be REFUSED+taught: ok={ok} {out[-120:]}")

    # 3. independence claim by a DISTINCT invocation (a subagent uuid) — allowed
    ins_ledger(guc("agent-uuid-xyz"), "review", "honest distinct", reviewer, aid)
    rid3 = psql(f"SELECT id FROM {SCHEMA}.ledger WHERE statement='honest distinct';")[1]
    ok, out = ins_detail(rid3, "technical")
    ck(ok, f"a technical claim by a distinct invocation must be ALLOWED (HONEST-DISTINCT): {out[-120:]}")

    # 4. independence claim on an UNSTAMPED review — REFUSED
    ins_ledger("RESET app.vendor_session; RESET app.vendor_agent; RESET app.vendor_ts; RESET app.vendor_hmac; ",
               "review", "unstamped claim", reviewer, aid)
    rid4 = psql(f"SELECT id FROM {SCHEMA}.ledger WHERE statement='unstamped claim';")[1]
    ok, out = ins_detail(rid4, "technical")
    ck(not ok and "verified interception stamp" in out.lower(),
       f"a technical claim on an unstamped review must be REFUSED: ok={ok} {out[-120:]}")

    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c",
                    f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE; DROP SCHEMA IF EXISTS {KERN} CASCADE; "  # declared-drop: s17iv (declared scratch/test reset)
                    f"DROP OWNED BY {ROLE}; DROP ROLE IF EXISTS {ROLE};"], capture_output=True, text=True)
    if fails:
        print("# S17 INDEPENDENCE FIXTURE RED:")
        for f in fails:
            print(f"  !! {f}")
        return 1
    print("# S17 INDEPENDENCE FIXTURE GREEN — self-review allowed; proxy-independence refused+taught; "
          "distinct-invocation independence allowed; unstamped-independence refused.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
