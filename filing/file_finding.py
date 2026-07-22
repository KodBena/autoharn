#!/usr/bin/env python3
"""file_finding -- the filing path for the GENERAL FINDINGS LEDGER (db/harness/005_findings_ledger.sql;
docs/work-units/WORK-UNIT-findings-disposition.md). The sibling of tools/file_rationalization.py: that
store carries rationalization FIRES (detector-specific columns); THIS store carries ALL in-passing work
FINDINGS + their dispositions. Same trigger idiom, same filing-script shape.

THE GOVERNING MOVE (work-unit §0): provenance is separated from disposition. A finding is OPEN until a
recorded, actor-attributed disposition act closes it (F28) — prose ("NOTED", "predates this increment")
NEVER closes it; a provenance_claim is METADATA on an open finding. The honest case is cheap (one
`file` call); the only way to cheat is not filing, which concentrates dishonesty into one detectable act.

  python tools/file_finding.py file --actor "…" --class hazard --statement "…" \
      [--session …] [--increment e15-inc5] [--evidence-ref path/commit] \
      [--provenance-claim predates-increment] [--frame out-of-frame]
  python tools/file_finding.py dispose --finding 6 --actor "bork" --kind fixed [--ref <commit>]
  python tools/file_finding.py open [--increment e15-inc5]     # list OPEN findings (the close-gate query)

Store: the `harness` DB (psql -h 192.168.122.1 -d harness) — claims about WORK, never subject/evidence
records. Values cross into SQL as psql `:'var'` string-literal parameters (injection-safe). Every import
is top-of-file (lazy-import edict)."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pghost_resolve  # filing/pghost_resolve.py, the ONE home -- never a literal host default

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
DB = os.environ.get("HARNESS_DB", "harness")
DEFAULT_SCHEMA = os.environ.get("HARNESS_SCHEMA", "harness")
REPO_ROOT = Path(__file__).resolve().parent.parent
DDL = REPO_ROOT / "stores" / "005_findings_ledger.sql"   # autoharn: stores/ (was db/harness/)


def _psql(sql: str, *, params: dict[str, str] | None = None, schema: str = DEFAULT_SCHEMA) -> str:
    cmd = ["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-v", f"schema={schema}"]
    for k, v in (params or {}).items():
        cmd += ["-v", f"{k}={v}"]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"psql failed ({r.returncode}): {r.stderr.strip()}")
    return r.stdout.strip()


def ensure_schema(schema: str) -> None:
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", "ON_ERROR_STOP=1", "-v", f"schema={schema}",
                    "-f", str(DDL)], check=True, capture_output=True)
    print(f"findings ledger ensured in schema '{schema}' (db '{DB}')")


def cmd_file(a: argparse.Namespace) -> int:
    fid = _psql(
        "WITH ins AS (INSERT INTO :\"schema\".finding "
        "(actor, session, increment, class, statement, evidence_ref, provenance_claim, frame) VALUES "
        "(:'actor', NULLIF(:'session',''), NULLIF(:'increment',''), :'class', :'statement', "
        " NULLIF(:'evref',''), NULLIF(:'prov',''), :'frame') RETURNING id) SELECT id FROM ins;",
        params={"actor": a.actor, "session": a.session or "", "increment": a.increment or "",
                "class": a.klass, "statement": a.statement, "evref": a.evidence_ref or "",
                "prov": a.provenance_claim or "", "frame": a.frame}, schema=a.schema)
    print(f"filed finding id={fid} (class={a.klass}, frame={a.frame}) — OPEN until a disposition act closes it")
    return 0


def cmd_dispose(a: argparse.Namespace) -> int:
    did = _psql(
        "WITH ins AS (INSERT INTO :\"schema\".finding_disposition (finding_id, actor, kind, ref) VALUES "
        "(:finding, :'actor', :'kind', NULLIF(:'ref','')) RETURNING id) SELECT id FROM ins;",
        params={"finding": str(a.finding), "actor": a.actor, "kind": a.kind, "ref": a.ref or ""},
        schema=a.schema)
    print(f"disposed finding {a.finding} -> {a.kind} (disposition id={did}, ref={a.ref or '(none)'})")
    return 0


def cmd_open(a: argparse.Namespace) -> int:
    where = "WHERE increment = :'increment'" if a.increment else ""
    rows = _psql(
        f"SELECT id||' | '||class||' | '||frame||' | '||left(statement,80) "
        f"FROM :\"schema\".finding_open {where} ORDER BY id;",
        params=({"increment": a.increment} if a.increment else {}), schema=a.schema)
    scope = f" (increment {a.increment})" if a.increment else ""
    if rows:
        print(f"# OPEN findings{scope}:")
        for line in rows.splitlines():
            print(f"  {line}")
    else:
        print(f"# no OPEN findings{scope} — every finding carries a disposition act")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ensure-schema", help="apply the (idempotent) DDL")
    fp = sub.add_parser("file", help="record an in-passing finding (OPEN until disposed)")
    fp.add_argument("--actor", required=True)
    fp.add_argument("--class", dest="klass", required=True, help="descriptive kebab slug — NEVER a verdict")
    fp.add_argument("--statement", required=True)
    fp.add_argument("--session", default="")
    fp.add_argument("--increment", default="")
    fp.add_argument("--evidence-ref", default="")
    fp.add_argument("--provenance-claim", default="", help="METADATA (e.g. predates-increment) — NOT a disposition")
    fp.add_argument("--frame", default="in-frame", choices=("in-frame", "out-of-frame"))
    dp = sub.add_parser("dispose", help="append an actor-attributed disposition act (F28: append-only)")
    dp.add_argument("--finding", type=int, required=True)
    dp.add_argument("--actor", required=True)
    dp.add_argument("--kind", required=True, choices=("fixed", "filed", "explained", "waived", "duplicate-of"))
    dp.add_argument("--ref", default="", help="required for filed/explained/waived/duplicate-of")
    op = sub.add_parser("open", help="list OPEN findings (the close-gate query)")
    op.add_argument("--increment", default="")
    a = ap.parse_args(argv)
    if a.cmd == "ensure-schema":
        ensure_schema(a.schema); return 0
    if a.cmd == "file":
        return cmd_file(a)
    if a.cmd == "dispose":
        return cmd_dispose(a)
    if a.cmd == "open":
        return cmd_open(a)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
