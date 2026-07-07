#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T18:56:34Z
#   last-change: 2026-07-06T18:58:47Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""findings_gate_fixture -- the acceptance fixtures for the general findings ledger (db/harness/005,
tools/file_finding.py, tools/findings_gate.py; WORK-UNIT-findings-disposition §4). Runs in a THROWAWAY
schema (never the real `harness` store) so it is idempotent and never pollutes the standing findings.

Proves, all banked to a witness:
  1. DDL + triggers: UPDATE and DELETE each refused (append-only), seen loudly.
  2. Filing script round-trips file + dispose; per-kind ref requirement enforced (waived without ref REFUSED).
  3. Close-gate RED on an open finding, GREEN after a disposition act (both directions).
  4. provenance ≠ disposition: a finding with ONLY a provenance_claim stays OPEN (the governing move).
  5. F28: nothing auto-resolves — a disposition is an explicit act, never computed.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PGHOST = os.environ.get("HARNESS_PGHOST", os.environ.get("EPISTEMIC_PGHOST", "192.168.122.1"))
SCHEMA = "findings_fixture"
WITNESS = REPO / "docs" / "work-units" / "findings-ledger-fixture.witness.txt"
FF = [sys.executable, str(REPO / "tools" / "file_finding.py"), "--schema", SCHEMA]
GATE = [sys.executable, str(REPO / "tools" / "findings_gate.py")]


def psql(sql: str, *, want_fail: bool = False) -> tuple[int, str]:
    r = subprocess.run(["psql", "-h", PGHOST, "-d", "harness", "-tA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def ff(*args: str) -> tuple[int, str]:
    r = subprocess.run(FF + list(args), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def gate() -> tuple[int, str]:
    env = {**os.environ, "HARNESS_SCHEMA": SCHEMA}
    r = subprocess.run(GATE, capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()


def main() -> int:
    log: list[str] = ["# findings-ledger acceptance fixture (THROWAWAY schema; never the real store)\n"]
    ok = True

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        ok &= cond
        log.append(f"  [{'OK ' if cond else '!! '}] {name}{(' — ' + detail) if detail else ''}")

    # fresh throwaway schema
    psql(f"DROP TABLE IF EXISTS {SCHEMA}.finding_disposition CASCADE; DROP TABLE IF EXISTS {SCHEMA}.finding CASCADE; DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;")  # declared-drop: {SCHEMA} (declared scratch/test reset; blast radius = this schema only)
    subprocess.run(["psql", "-h", PGHOST, "-d", "harness", "-v", "ON_ERROR_STOP=1", "-v", f"schema={SCHEMA}",
                    "-f", str(REPO / "db" / "harness" / "005_findings_ledger.sql")], check=True, capture_output=True)

    # 4 + 5: file with ONLY a provenance_claim -> OPEN (provenance is not disposition)
    log.append("## provenance ≠ disposition (the governing move)")
    ff("file", "--actor", "fixture", "--class", "test-obs", "--statement", "prov-only stays open",
       "--provenance-claim", "predates-increment")
    rc, out = psql(f"SELECT count(*) FROM {SCHEMA}.finding_open;")
    check("a provenance_claim alone leaves the finding OPEN", out == "1", f"open={out}")

    # 3: close-gate RED on the open finding
    log.append("## close-gate direction")
    rc, out = gate()
    check("gate RED on an open finding (exit 1)", rc == 1, out.splitlines()[0] if out else "")

    # 2: per-kind ref requirement — filed WITHOUT ref refused; waived WITHOUT ref refused
    log.append("## per-kind ref requirement (a disposition without its witness is nothing)")
    rc, out = ff("dispose", "--finding", "1", "--actor", "fixture", "--kind", "filed")
    check("filed WITHOUT ref REFUSED", rc != 0, "refused")
    rc, out = ff("dispose", "--finding", "1", "--actor", "fixture", "--kind", "waived")
    check("waived WITHOUT ref REFUSED", rc != 0, "refused")

    # 3 (cont): dispose WITH ref -> gate GREEN
    ff("dispose", "--finding", "1", "--actor", "fixture", "--kind", "filed", "--ref", "BACKLOG.md")
    rc, out = psql(f"SELECT count(*) FROM {SCHEMA}.finding_open;")
    check("a disposition act closes the finding", out == "0", f"open={out}")
    rc, out = gate()
    check("gate GREEN after disposition (exit 0)", rc == 0, out.splitlines()[0] if out else "")

    # 1: append-only — UPDATE and DELETE each refused
    log.append("## append-only triggers (a finding/disposition is an audit fact)")
    rc, out = psql(f"UPDATE {SCHEMA}.finding SET class='x' WHERE id=1;")
    check("UPDATE on finding REFUSED", rc != 0, "refused")
    rc, out = psql(f"DELETE FROM {SCHEMA}.finding WHERE id=1;")
    check("DELETE on finding REFUSED", rc != 0, "refused")
    # target by finding_id, not a hardcoded disposition id: the two REFUSED disposes above advanced
    # the IDENTITY sequence (a failed INSERT still consumes nextval), so the real disposition is not
    # id=1 — an UPDATE WHERE id=1 would match zero rows and the per-row trigger would never fire (a
    # false green). The fixture caught exactly that (identity advances on failed insert).
    rc, out = psql(f"UPDATE {SCHEMA}.finding_disposition SET kind='x' WHERE finding_id=1;")
    check("UPDATE on finding_disposition REFUSED", rc != 0, "refused")
    rc, out = psql(f"DELETE FROM {SCHEMA}.finding_disposition WHERE finding_id=1;")
    check("DELETE on finding_disposition REFUSED", rc != 0, "refused")

    # duplicate-of requires an existing finding id
    log.append("## duplicate-of adjudication (identity is an ACT, never auto-computed — F28)")
    ff("file", "--actor", "fixture", "--class", "test-obs", "--statement", "second finding")
    rc, out = ff("dispose", "--finding", "2", "--actor", "fixture", "--kind", "duplicate-of", "--ref", "999")
    check("duplicate-of a NON-existent finding REFUSED", rc != 0, "refused")
    rc, out = ff("dispose", "--finding", "2", "--actor", "fixture", "--kind", "duplicate-of", "--ref", "1")
    check("duplicate-of an EXISTING finding accepted", rc == 0, "accepted")

    # clean up the throwaway schema
    psql(f"DROP TABLE IF EXISTS {SCHEMA}.finding_disposition CASCADE; DROP TABLE IF EXISTS {SCHEMA}.finding CASCADE; DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;")  # declared-drop: {SCHEMA} (declared scratch/test reset; blast radius = this schema only)

    WITNESS.parent.mkdir(parents=True, exist_ok=True)
    header = f"# findings-ledger fixture {'GREEN — all acceptance points pass' if ok else 'RED'}\n"
    WITNESS.write_text(header + "\n".join(log) + "\n", encoding="utf-8")
    print(header + "\n".join(log))
    print(f"# witness: {WITNESS}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
