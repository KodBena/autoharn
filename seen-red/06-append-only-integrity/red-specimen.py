#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T01:47:54Z
#   last-change: 2026-07-07T01:48:15Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for the append-only-integrity gate (forecloses findings 6 + 15, the append-only
trigger class). Builds a THROWAWAY scratch schema with an audit-spine-shaped table that is MISSING its
append-only guard — exactly the finding-6/15 shape — and runs the gate's own check against it. The gate
must flag it. The captured FAIL output is banked as red.txt (the proof the gate sees the class red).
Scratch-only (schema ao_redspec), dropped after. Run from the harness repo root."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
from append_only_integrity import missing_guards  # noqa: E402

HOST, DB, SCHEMA = "192.168.122.1", "harness", "ao_redspec"


def main() -> int:
    subprocess.run(["psql", "-h", HOST, "-d", DB, "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;"],  # declared-drop: ao_redspec (declared scratch/test reset)
                   capture_output=True, text=True)
    # a review_detail-shaped attestation table with NO append-only trigger — the finding-6/15 defect
    subprocess.run(["psql", "-h", HOST, "-d", DB, "-c",
                    f"CREATE SCHEMA {SCHEMA}; "
                    f"CREATE TABLE {SCHEMA}.review_detail (id serial primary key, verdict text);"],
                   capture_output=True, text=True, check=True)
    bad = missing_guards(HOST, DB, [(SCHEMA, "review_detail")], [])
    subprocess.run(["psql", "-h", HOST, "-d", DB, "-c", f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE;"],  # declared-drop: ao_redspec (declared scratch/test reset)
                   capture_output=True, text=True)
    if not bad:
        print("SPECIMEN INERT — the gate did NOT flag an unguarded attestation table (gate is broken).")
        return 1
    for b in bad:
        print(f"UNGUARDED APPEND-ONLY TABLE: {b}")
    print(f"# append-only-integrity FAIL — {len(bad)} audit-spine table(s) lack their append-only "
          f"guard. The ledger's tamper-evidence is not intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
