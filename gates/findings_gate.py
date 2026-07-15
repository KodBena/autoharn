#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-06T18:52:55Z
#   last-change: 2026-07-14T23:19:51Z
#   contributors: 37017f46/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""findings_gate -- the CLOSE-GATE for the general findings ledger (db/harness/005; WORK-UNIT-
findings-disposition §2). A close_manifest-registered line (and a pre-commit hook where the increment
tag is known) that queries OPEN findings and goes RED if any exist: an increment cannot report complete
with undischarged findings, and a real hazard debt (e.g. the TRUNCATE-CASCADE hole) is SEEN RED before
anything disposes it.

A finding is OPEN iff it has no disposition act (F28) — prose ("NOTED", "predates this increment")
never closes it. This gate reads `harness.finding_open`.

  findings_gate.py                 # GLOBAL: red if ANY finding is open (the apparatus has open debt)
  findings_gate.py --increment X   # scoped: red if any finding tagged increment X is open

Exit vocabulary: 0 = no open findings (green); 1 = open findings exist (RED); 2 = could not query
(QUARANTINE — a gate that cannot run is NO RESULT, ADR-0015 R3, never a silent green). Read-only."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filing"))
import pghost_resolve  # noqa: E402  (filing/pghost_resolve.py, the ONE home -- never a literal host default)

PGHOST = pghost_resolve.resolve_pghost("HARNESS_PGHOST", "EPISTEMIC_PGHOST")
DB = os.environ.get("HARNESS_DB", "harness")
SCHEMA = os.environ.get("HARNESS_SCHEMA", "harness")


def open_findings(increment: str | None) -> list[str]:
    where = "WHERE increment = :'inc'" if increment else ""
    cmd = ["psql", "-h", PGHOST, "-d", DB, "-tA", "-v", "ON_ERROR_STOP=1"]
    if increment:
        cmd += ["-v", f"inc={increment}"]
    cmd += ["-c", f"SELECT id||' | '||class||' | '||frame||' | '||left(statement,90) "
            f"FROM {SCHEMA}.finding_open {where} ORDER BY id;"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Close-gate: RED if any finding is OPEN.")
    ap.add_argument("--increment", default=os.environ.get("FINDINGS_INCREMENT", ""),
                    help="scope to one increment tag (default: GLOBAL — every open finding)")
    args = ap.parse_args(argv)
    inc = args.increment or None
    scope = f"increment '{inc}'" if inc else "GLOBAL (every increment)"
    try:
        rows = open_findings(inc)
    except Exception as e:  # noqa: BLE001 — a gate that cannot query is NO RESULT, never a silent green
        print(f"# findings-gate QUARANTINED — could not query {SCHEMA}.finding_open: {e}")
        return 2
    if not rows:
        print(f"# findings-gate GREEN — no OPEN findings ({scope}); every finding carries a disposition act (F28).")
        return 0
    print(f"# findings-gate RED — {len(rows)} OPEN finding(s) ({scope}); an increment cannot report "
          f"complete with undischarged findings. Dispose (fix/file/explain/waive) each, then re-run:")
    for ln in rows:
        print(f"  OPEN: {ln}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
