#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T01:30:00Z
#   last-change: 2026-07-07T01:30:00Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""file_foreclosure — the filing path for the FORECLOSURE-DEBT LEDGER (db/harness/006_foreclosure_debt.sql;
docs/work-units/WORK-UNIT-foreclosure-debt.md). Sibling of file_finding.py. A `fixed` finding opens a
class debt (ADR-0000 never-again); this files the row that ANSWERS "what forecloses the class?" — a
registered gate/lint/fixture/trigger with a BANKED SEEN-RED artifact, OR a maintainer-ruled waiver.

The seen-red artifact (ADR-0011) is hashed here and pinned in the row; the DB trigger refuses a
non-waived foreclosure without check_line_id + red_artifact + red_sha256 — the never-again evidence
cannot be omitted. Seen-red lives at docs/adr-evidence/seen-red/<finding_id>-<slug>/, committed.

  file_foreclosure.py file --finding 24 --actor engineer:vicar --kind lint \
      --check-line destructive-ddl-guard --red docs/adr-evidence/seen-red/24-.../red.txt \
      --note "DROP ... CASCADE banned outside a migration path; reset scripts declare their targets"
  file_foreclosure.py waive --finding 25 --actor human:maintainer --ruling "acts.ruling id N / msg loc"
  file_foreclosure.py debt        # the open debt (the close-gate query)

Store: the `harness` DB. Values cross as psql :'var' string literals (injection-safe). Lazy imports banned.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

PGHOST = "192.168.122.1"
DB = "harness"


def _psql(sql: str, params: dict[str, str] | None = None) -> tuple[bool, str]:
    cmd = ["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1"]
    for k, v in (params or {}).items():
        cmd += ["-v", f"{k}={v}"]
    r = subprocess.run(cmd, input=sql, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def _file(a: argparse.Namespace) -> int:
    red = Path(a.red)
    if not red.exists():
        print(f"seen-red artifact not found: {red} (bank the RED run first — ADR-0011)", file=sys.stderr)
        return 1
    sha = hashlib.sha256(red.read_bytes()).hexdigest()
    ok, out = _psql(
        "WITH ins AS (INSERT INTO harness.class_foreclosure "
        "(finding_id, actor, kind, check_line_id, red_artifact, red_sha256, note) "
        "VALUES (:'fid'::bigint, :'actor', :'kind', :'cl', :'red', :'sha', :'note') RETURNING foreclosure_id) "
        "SELECT foreclosure_id FROM ins;",
        {"fid": a.finding, "actor": a.actor, "kind": a.kind, "cl": a.check_line,
         "red": a.red, "sha": sha, "note": a.note or ""})
    if not ok:
        print(f"REFUSED: {out.splitlines()[-1] if out else ''}", file=sys.stderr)
        return 1
    print(f"filed foreclosure id={out} for finding {a.finding} ({a.kind}, line={a.check_line}, "
          f"seen-red sha256={sha[:16]}…)")
    return 0


def _waive(a: argparse.Namespace) -> int:
    ok, out = _psql(
        "WITH ins AS (INSERT INTO harness.class_foreclosure (finding_id, actor, kind, ruling_ref, note) "
        "VALUES (:'fid'::bigint, :'actor', 'waived', :'ruling', :'note') RETURNING foreclosure_id) "
        "SELECT foreclosure_id FROM ins;",
        {"fid": a.finding, "actor": a.actor, "ruling": a.ruling, "note": a.note or ""})
    if not ok:
        print(f"REFUSED: {out.splitlines()[-1] if out else ''}", file=sys.stderr)
        return 1
    print(f"waived foreclosure id={out} for finding {a.finding} (ruling: {a.ruling})")
    return 0


def _debt(_a: argparse.Namespace) -> int:
    ok, out = _psql("SELECT finding_id||' | '||class FROM harness.foreclosure_debt ORDER BY finding_id;")
    if not ok:
        print(f"query failed: {out}", file=sys.stderr)
        return 2
    if not out:
        print("# no foreclosure debt — every fixed finding carries a class_foreclosure row")
        return 0
    print("# OPEN foreclosure debt (fixed findings with no class_foreclosure):")
    for line in out.splitlines():
        print(f"  {line}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("file")
    f.add_argument("--finding", required=True)
    f.add_argument("--actor", required=True)
    f.add_argument("--kind", required=True, choices=["gate", "lint", "fixture", "trigger"])
    f.add_argument("--check-line", required=True, help="id of a registered close-manifest / lint line")
    f.add_argument("--red", required=True, help="repo path of the banked seen-red artifact")
    f.add_argument("--note")
    f.set_defaults(fn=_file)
    w = sub.add_parser("waive")
    w.add_argument("--finding", required=True)
    w.add_argument("--actor", required=True)
    w.add_argument("--ruling", required=True, help="a maintainer ruling ref (acts.ruling id / message loc)")
    w.add_argument("--note")
    w.set_defaults(fn=_waive)
    d = sub.add_parser("debt")
    d.set_defaults(fn=_debt)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
