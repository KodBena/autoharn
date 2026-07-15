#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T20:20:42Z
#   last-change: 2026-07-15T20:20:42Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""Both-polarity proof for gates/kind_shape_manifest_gate.py (ledger item
`kind-shape-manifest-gate`, gates/fixture_census.py REGISTRY entry "kind-shape-manifest-gate").
Real infra, no mocks: a throwaway scratch schema in the toy db, on a live full-chain apply
(high_watermark_1.sql through s30-typed-dependency-edges.sql), torn down after this file runs.

Cases:
  green-real-chain          -- the plain gate invocation (no injection) on the current, real
                                birth chain exits 0: every catalog kind-shape CHECK matches its
                                MANIFEST row, every trigger-mechanism row's column carries no
                                competing CHECK, no non-core column is unmanifested.
  red-unlicensed-column     -- `--inject-column` adds a synthetic scratch column (no CHECK, no
                                MANIFEST entry) to the SAME real chain; the gate must REFUSE it
                                by name as an unlicensed payload column (exit 1).
  red-shape-drift           -- a live mutation (dropping `work_title_kind_shape`'s real two-way
                                CHECK and replacing it with a one-way one) is caught by
                                assert_manifest() directly as a shape-drift violation naming the
                                column -- proves the classifier is reading the catalog, not just
                                echoing MANIFEST.

Usage: python3 seen-red/kind-shape-manifest-gate/run_fixtures.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "kind_shape_manifest_gate.py"
sys.path.insert(0, str(REPO / "gates"))
import kind_shape_manifest_gate as kbmg  # noqa: E402

PGHOST, PGDB = kbmg.PGHOST, kbmg.PGDB


def sh(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kw)


def run_gate(*args: str) -> subprocess.CompletedProcess:
    return sh([sys.executable, str(GATE), *args])


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []

    # --- green: real chain, no injection ---
    cp = run_gate()
    ok = cp.returncode == 0 and "clean" in cp.stdout
    check("green-real-chain", ok,
          f"exit={cp.returncode} stdout_tail={cp.stdout.strip()[-200:]!r}", failures)

    # --- red: unlicensed synthetic column ---
    cp = run_gate("--inject-column", "work_bogus_scratch_field")
    ok = (cp.returncode == 1
          and "UNLICENSED PAYLOAD COLUMN 'work_bogus_scratch_field'" in cp.stdout)
    check("red-unlicensed-column", ok,
          f"exit={cp.returncode} stdout_tail={cp.stdout.strip()[-400:]!r}", failures)

    # --- red: live shape-drift mutation, checked via assert_manifest() directly ---
    schema, kern, role = "kbmgfx_scratch", "kbmgfx_scratch_kernel", "kbmgfx_scratch_rw"
    kbmg.teardown(schema, kern, role)
    try:
        kbmg.apply_chain(schema, kern, role)
        mut = sh(["psql", "-h", PGHOST, "-d", PGDB, "-v", "ON_ERROR_STOP=1", "-c",
                  f"ALTER TABLE {schema}.ledger DROP CONSTRAINT work_title_kind_shape; "
                  f"ALTER TABLE {schema}.ledger ADD CONSTRAINT work_title_kind_shape "
                  f"CHECK (work_title IS NULL OR kind = 'work_opened');"])
        mut_ok = mut.returncode == 0
        violations = kbmg.assert_manifest(schema) if mut_ok else ["mutation itself failed"]
        drift_ok = mut_ok and any("work_title" in v and "shape drifted" in v for v in violations)
        check("red-shape-drift", drift_ok,
              f"mutation_exit={mut.returncode} violations={violations}", failures)
    finally:
        kbmg.teardown(schema, kern, role)

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL CASES OK -- kind-shape-manifest-gate both-polarity proof (real chain clean, "
          "unlicensed synthetic column refused by name, live shape-drift caught by the "
          "classifier reading the real catalog), zero residue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
