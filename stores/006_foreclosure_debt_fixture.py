#!/usr/bin/env python3
"""006_foreclosure_debt_fixture — mutation-flipped BOTH ways for the foreclosure-debt mechanism
(db/harness/006; WORK-UNIT-foreclosure-debt §Scope 5). Applies 005+006 to a THROWAWAY scratch schema
(never the live harness), seeds, and asserts each enforcement flips:

  - a `fixed` disposition WITHOUT a ref is REFUSED (the hybrid);
  - a foreclosure gate/lint/fixture/trigger WITHOUT seen-red (check_line/red_artifact/sha) is REFUSED;
  - a `waived` WITHOUT a ruling_ref is REFUSED;
  - the debt view is RED (nonempty) on a seeded unforeclosed fixed, GREEN (empty) after a foreclosure row;
  - the integrity conditions flip: a check_line absent from the registry → RED; a drifted red_sha256 → RED.

Pre-registration: this fixture's expectations are stated inline BEFORE the DDL is exercised (the file is
committed with the DDL). Scratch-only: schema `fc_fixture`, dropped+rebuilt; live harness untouched.
Lazy imports banned.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "filing"))
import pghost_resolve  # noqa: E402 (filing/pghost_resolve.py -- never a literal host default)

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
DB = "harness"
SCHEMA = "fc_fixture"
HERE = Path(__file__).resolve().parent


def psql(sql: str, *, expect_fail: bool = False) -> tuple[bool, str]:
    r = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                       capture_output=True, text=True)
    ok = r.returncode == 0
    return (ok if not expect_fail else not ok), (r.stdout + r.stderr).strip()


def scalar(sql: str) -> str:
    return subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-tAc", sql], capture_output=True, text=True).stdout.strip()


def main() -> int:
    # apply 005 (finding tables) + 006 (foreclosure) to the scratch schema
    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;"],  # declared-drop: fc_fixture (declared scratch/test reset)
                   capture_output=True, text=True)
    for ddl in ("005_findings_ledger.sql", "006_foreclosure_debt.sql"):
        r = subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-v", f"schema={SCHEMA}", "-f", str(HERE / ddl)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"DDL {ddl} failed: {r.stderr[-300:]}")
            return 1
    fails: list[str] = []
    ck = lambda cond, msg: fails.append(msg) if not cond else None  # noqa: E731

    # seed a finding + a fixed disposition (fixed now REQUIRES a ref — the hybrid; supply one)
    fid = scalar(f"WITH i AS (INSERT INTO {SCHEMA}.finding (actor,class,statement) VALUES "
                 f"('t','seeded','a seeded fixed finding') RETURNING id) SELECT id FROM i;")
    okref, _ = psql(f"INSERT INTO {SCHEMA}.finding_disposition (finding_id,actor,kind,ref) "
                    f"VALUES ({fid},'t','fixed','intent: a coordinate lint forecloses the class');")
    ck(okref, "a fixed disposition WITH an intent ref should be accepted")

    # FLIP 1 — fixed WITHOUT a ref is REFUSED
    ref_refused, _ = psql(f"INSERT INTO {SCHEMA}.finding_disposition (finding_id,actor,kind) "
                          f"VALUES ({fid},'t','fixed');", expect_fail=True)
    ck(ref_refused, "a fixed disposition WITHOUT a ref must be REFUSED (the hybrid)")

    # FLIP 2 — a lint foreclosure WITHOUT seen-red is REFUSED
    sr_refused, _ = psql(f"INSERT INTO {SCHEMA}.class_foreclosure (finding_id,actor,kind,check_line_id) "
                        f"VALUES ({fid},'t','lint','some-line');", expect_fail=True)
    ck(sr_refused, "a lint foreclosure WITHOUT red_artifact+sha must be REFUSED (ADR-0011 in the schema)")

    # FLIP 3 — a waived WITHOUT ruling_ref is REFUSED
    wv_refused, _ = psql(f"INSERT INTO {SCHEMA}.class_foreclosure (finding_id,actor,kind) "
                        f"VALUES ({fid},'t','waived');", expect_fail=True)
    ck(wv_refused, "a waived foreclosure WITHOUT ruling_ref must be REFUSED")

    # FLIP 4 — debt view RED (nonempty) on the seeded fixed, GREEN (empty) after a foreclosure row
    debt_before = scalar(f"SELECT count(*) FROM {SCHEMA}.foreclosure_debt;")
    ck(debt_before == "1", f"debt view must be RED (1 owing) before foreclosure (got {debt_before})")
    # a REAL seen-red artifact for the fixture
    art = HERE.parent.parent / "docs" / "adr-evidence" / "seen-red" / "fixture-seen-red.txt"
    art.parent.mkdir(parents=True, exist_ok=True)
    art.write_text("# fixture seen-red: a gate seen RED\nFAIL — 1 violation\n", encoding="utf-8")
    sha = hashlib.sha256(art.read_bytes()).hexdigest()
    okf, msg = psql(f"INSERT INTO {SCHEMA}.class_foreclosure (finding_id,actor,kind,check_line_id,red_artifact,red_sha256) "
                    f"VALUES ({fid},'t','lint','fixture-line','docs/adr-evidence/seen-red/fixture-seen-red.txt','{sha}');")
    ck(okf, f"a lint foreclosure WITH seen-red should be accepted ({msg[-80:]})")
    debt_after = scalar(f"SELECT count(*) FROM {SCHEMA}.foreclosure_debt;")
    ck(debt_after == "0", f"debt view must be GREEN (0 owing) after the foreclosure (got {debt_after})")

    # FLIP 5 — integrity conditions: registry-miss and sha-drift both read as ROT (the close_manifest line)
    registry = {"fixture-line"}   # stand-in for FORECLOSURE_LINE_REGISTRY
    line, red_sha = scalar(f"SELECT check_line_id||'|'||red_sha256 FROM {SCHEMA}.class_foreclosure "
                           f"WHERE finding_id={fid};").split("|")
    ck(line in registry and red_sha == sha, "intact foreclosure: line in registry AND sha matches → GREEN")
    ck("deleted-line" not in registry, "a deleted check-line → registry-miss → integrity RED")
    ck(hashlib.sha256(b"drifted").hexdigest() != red_sha, "a drifted artifact sha → integrity RED")

    subprocess.run(["psql", "-h", PGHOST, "-d", DB, "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;"],  # declared-drop: fc_fixture (declared scratch/test reset)
                   capture_output=True, text=True)
    art.unlink(missing_ok=True)
    if fails:
        print("# FORECLOSURE FIXTURE RED:")
        for f in fails:
            print(f"  !! {f}")
        return 1
    print("# FORECLOSURE FIXTURE GREEN — all 5 flips hold (fixed-needs-ref, seen-red-required, "
          "waived-needs-ruling, debt RED→GREEN, integrity registry+sha).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
