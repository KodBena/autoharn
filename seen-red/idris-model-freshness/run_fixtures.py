#!/usr/bin/env python3
"""Both-polarity proof for gates/idris_model_freshness.py (ledger item
`idris-model-freshness-gate`, gates/fixture_census.py REGISTRY entry "idris-model-freshness").
No mocks of the gate's own logic: every case runs the REAL gate module against synthetic scratch
files built fresh in a temp dir each run, via the module's own `--idr-file`/`--lineage-dir`/
`--idris2-bin` redirection flags (the same device gates/doc_attestation_presence.py's --doc-root/
--ledger already establishes as this codebase's precedent for redirecting a gate's file targets
without monkeypatching its internals).

Cases:
  red-stale-no-lagging   -- synthetic AS-OF s3, synthetic lineage head s5, no LAGGING marker ->
                             exit 1, RED finding naming both discharge paths.
  red-broken-syntax      -- a syntactically invalid .idr file (module/content mismatch aside,
                             this is a straight parse error) -> exit 1, elaboration RED,
                             independent of AS-OF currency (AS-OF here is even current/ahead).
  warn-lagging-downgrade -- synthetic AS-OF s3 (declared) < synthetic lineage head s5 (actual),
                             but the AS-OF line carries an explicit LAGGING marker -> exit 0
                             (WARN, not a failure) — proves the honest-lag escape hatch works.
  green-clean             -- REAL file content (design/Autoharn.idr, current bytes) copied
                             verbatim, paired with a synthetic lineage dir whose head is
                             DELIBERATELY set to match the real file's own declared s32 -- proves
                             the gate's clean path (declared == actual, real elaboration passes)
                             independent of this repo's own s33 lag (which the gate's own report
                             documents separately as the deliberate, honest RED disposition of
                             the real invocation).

Usage: python3 seen-red/idris-model-freshness/run_fixtures.py
Exit 0 if every case matches its expected polarity; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "idris_model_freshness.py"
REAL_IDR = REPO / "design" / "Autoharn.idr"


def run_gate(idr_file: Path, lineage_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), "--idr-file", str(idr_file), "--lineage-dir", str(lineage_dir)],
        capture_output=True, text=True,
    )


def mk_lineage(dir_: Path, heads: list[int]) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    for n in heads:
        (dir_ / f"s{n}-fixture-delta.sql").write_text("-- synthetic\n")
    # a sibling probe file at a HIGHER number, to prove it is correctly excluded from the head
    # derivation (dot-count filter) rather than accidentally raising the actual head.
    (dir_ / f"s{max(heads) + 7}-fixture-delta.detect.sql").write_text("-- synthetic sibling, must not count\n")


MINIMAL_VALID_IDR = """module Autoharn

x : Nat
x = 1
"""

BROKEN_IDR = """module Autoharn

x : Nat
x = this is not valid idris syntax ((((
"""


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="idris-freshness-fixtures-") as tmp:
        tmp = Path(tmp)

        # --- red-stale-no-lagging ---
        d1 = tmp / "case1"
        lineage1 = d1 / "lineage"
        mk_lineage(lineage1, [1, 2, 3, 4, 5])
        idr1 = d1 / "Autoharn.idr"
        idr1.parent.mkdir(parents=True, exist_ok=True)
        idr1.write_text("||| AS-OF: kernel chain through s3 (no lag note)\n" + MINIMAL_VALID_IDR)
        cp1 = run_gate(idr1, lineage1)
        check("red-stale-no-lagging",
              cp1.returncode == 1 and "RED" in cp1.stdout and "s3" in cp1.stdout and "s5" in cp1.stdout,
              f"exit={cp1.returncode}, stdout={cp1.stdout.strip()[:200]!r}", failures)

        # --- red-broken-syntax ---
        d2 = tmp / "case2"
        lineage2 = d2 / "lineage"
        mk_lineage(lineage2, [1])
        idr2 = d2 / "Autoharn.idr"
        idr2.parent.mkdir(parents=True, exist_ok=True)
        idr2.write_text("||| AS-OF: kernel chain through s1\n" + BROKEN_IDR)
        cp2 = run_gate(idr2, lineage2)
        check("red-broken-syntax",
              cp2.returncode == 1 and "elaboration" in cp2.stdout and "FAILED" in cp2.stdout,
              f"exit={cp2.returncode}, stdout={cp2.stdout.strip()[:300]!r}", failures)

        # --- warn-lagging-downgrade ---
        d3 = tmp / "case3"
        lineage3 = d3 / "lineage"
        mk_lineage(lineage3, [1, 2, 3, 4, 5])
        idr3 = d3 / "Autoharn.idr"
        idr3.parent.mkdir(parents=True, exist_ok=True)
        idr3.write_text(
            "||| AS-OF: kernel chain through s3 (LAGGING: fixture-only synthetic lag, real "
            "refresh not yet done)\n" + MINIMAL_VALID_IDR)
        cp3 = run_gate(idr3, lineage3)
        check("warn-lagging-downgrade",
              cp3.returncode == 0 and "WARN" in cp3.stdout and "s3" in cp3.stdout and "s5" in cp3.stdout,
              f"exit={cp3.returncode}, stdout={cp3.stdout.strip()[:200]!r}", failures)

        # --- green-clean (real file content, synthetic lineage head matched to its own s32) ---
        d4 = tmp / "case4"
        lineage4 = d4 / "lineage"
        mk_lineage(lineage4, list(range(1, 33)))  # head = 32, matching the real file's own AS-OF
        idr4 = d4 / "Autoharn.idr"
        idr4.parent.mkdir(parents=True, exist_ok=True)
        idr4.write_bytes(REAL_IDR.read_bytes())
        cp4 = run_gate(idr4, lineage4)
        check("green-clean",
              cp4.returncode == 0 and "clean" in cp4.stdout,
              f"exit={cp4.returncode}, stdout={cp4.stdout.strip()[:200]!r}", failures)

    if failures:
        print(f"idris-model-freshness fixtures: {len(failures)}/4 case(s) FAILED: {failures}")
        return 1
    print("idris-model-freshness fixtures: all 4 cases matched their expected polarity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
