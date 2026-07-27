#!/usr/bin/env python3
"""design-currency — both-polarity proof for gates/design_currency.py (spec design/
FABLE-DESIGN-CURRENCY-ADVISORY-SPEC.md; gates/fixture_census.py REGISTRY entry
"design-currency"). No mocks of the gate's own logic: every case runs the REAL gate module
against synthetic scratch `.md` files built fresh in a temp dir, via the module's own
`--design-dir`/`--repo-root`/`--strict` redirection flags (the same device
gates/doc_attestation_presence.py's `--doc-root`/`--ledger` and
gates/idris_model_freshness.py's `--idr-file`/`--lineage-dir` already establish).

`--repo-root` is pointed at THIS repo's own real root for every case, so `discharged-by`
ancestor verification runs against a real, live git history — a genuinely-ancestor sha
(`git rev-parse HEAD`, resolved fresh each run, never hard-coded) proves the GREEN discharge
path; a fabricated 40-hex sha proves the RED one.

Cases:
  red-discharge-not-ancestor  -- status=discharged discharged-by=<fabricated sha> -> advisory,
                                  --strict exit 1.
  red-dependency-drift        -- a live (ratified) doc depends-on a doc whose own status is
                                  superseded -> advisory naming both paths/statuses, --strict
                                  exit 1.
  red-malformed-grammar       -- header carries an unrecognized key -> teaching advisory naming
                                  the doc/line/issue, --strict exit 1.
  green-clean                 -- one doc, no discharged-by/superseded-by/depends-on, no old
                                  marker -> zero findings, --strict exit 0.
  green-satisfaction          -- a live doc depends-on a doc that is genuinely discharged (real
                                  ancestor sha) -> raises NOTHING (spec §5: satisfaction, not
                                  drift), --strict exit 0.
  check3-fires-on-historical-plus-supersededby -- the spec's own live-specimen shape
                                  (LOGGING-DIRECTION-SURVEY-2026-07-27.md): status=historical,
                                  superseded-by naming a live successor, PLUS an unreconciled
                                  doc-attest-exempt Removal-condition marker still present ->
                                  advisory FIRES (this is the FEATURE, not a defect -- the gate
                                  module's own docstring calls this the deliberate letter-vs-
                                  spirit broadening of check 3). --strict exit 1, same as a RED
                                  case mechanically, but asserted here as the POSITIVE detection
                                  this whole gate exists for.
  green-superseded-by-discharged-successor -- regression guard for the fix-round bug found
                                  2026-07-27 (real specimen: LOGGING-DIRECTION-SURVEY superseded-
                                  by a spec that itself later turned `discharged`): a doc's
                                  superseded-by target being `discharged` (built AND merged --
                                  the STRONGEST confirmation a successor is real) must NOT raise
                                  check 1's "not a live-or-historical token" advisory. --strict
                                  exit 0.

Usage: python3 seen-red/design-currency/run_fixtures.py
Exit 0 if every case matches its expected polarity; 1 otherwise. Lazy imports banned."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import os
# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "design_currency.py"

FABRICATED_SHA = "deadbeef00deadbeef00deadbeef00deadbeef0"


def real_head_sha() -> str:
    cp = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True)
    return cp.stdout.strip()


def run_gate(design_dir: Path, strict: bool = False) -> subprocess.CompletedProcess:
    args = [sys.executable, str(GATE), "--design-dir", str(design_dir), "--repo-root", str(REPO)]
    if strict:
        args.append("--strict")
    return subprocess.run(args, capture_output=True, text=True)


def write(design_dir: Path, name: str, content: str) -> None:
    design_dir.mkdir(parents=True, exist_ok=True)
    (design_dir / name).write_text(content)


def check(name: str, ok: bool, detail: str, failures: list[str]) -> None:
    print(f"=== {name} ===")
    print(f"  [{'ok' if ok else 'FAIL'}] {detail}")
    if not ok:
        failures.append(name)
    print()


def main() -> int:
    failures: list[str] = []
    head = real_head_sha()

    with tempfile.TemporaryDirectory(prefix="design-currency-fixtures-") as tmp:
        tmp = Path(tmp)

        # --- red-discharge-not-ancestor ---
        d1 = tmp / "case1"
        write(d1, "Bad.md", "# Bad\n\n<!-- design-currency: status=discharged "
                             f"discharged-by={FABRICATED_SHA} -->\n")
        cp1 = run_gate(d1, strict=True)
        check("red-discharge-not-ancestor",
              cp1.returncode == 1 and "not a verifiable ancestor" in cp1.stdout,
              f"exit={cp1.returncode}, stdout={cp1.stdout.strip()[:200]!r}", failures)

        # --- red-dependency-drift ---
        d2 = tmp / "case2"
        write(d2, "Live.md", "# Live\n\n<!-- design-currency: status=ratified "
                              "depends-on=Old.md -->\n")
        write(d2, "Old.md", "# Old\n\n<!-- design-currency: status=superseded "
                             "superseded-by=New.md -->\n")
        write(d2, "New.md", "# New\n\n<!-- design-currency: status=ratified -->\n")
        cp2 = run_gate(d2, strict=True)
        check("red-dependency-drift",
              cp2.returncode == 1 and "Live.md" in cp2.stdout and "drift, not satisfaction" in cp2.stdout,
              f"exit={cp2.returncode}, stdout={cp2.stdout.strip()[:300]!r}", failures)

        # --- red-malformed-grammar ---
        d3 = tmp / "case3"
        write(d3, "Malformed.md", "# Malformed\n\n<!-- design-currency: status=proposed "
                                  "foo=bar -->\n")
        cp3 = run_gate(d3, strict=True)
        check("red-malformed-grammar",
              cp3.returncode == 1 and "unrecognized token" in cp3.stdout,
              f"exit={cp3.returncode}, stdout={cp3.stdout.strip()[:300]!r}", failures)

        # --- green-clean ---
        d4 = tmp / "case4"
        write(d4, "Clean.md", "# Clean\n\n<!-- design-currency: status=ratified -->\n")
        cp4 = run_gate(d4, strict=True)
        check("green-clean",
              cp4.returncode == 0 and "clean" in cp4.stdout,
              f"exit={cp4.returncode}, stdout={cp4.stdout.strip()[:200]!r}", failures)

        # --- green-satisfaction (depends-on a GENUINELY discharged doc raises nothing) ---
        d5 = tmp / "case5"
        write(d5, "LiveSat.md", "# LiveSat\n\n<!-- design-currency: status=ratified "
                                 "depends-on=DoneDep.md -->\n")
        write(d5, "DoneDep.md", "# DoneDep\n\n<!-- design-currency: status=discharged "
                                 f"discharged-by={head} -->\n")
        cp5 = run_gate(d5, strict=True)
        check("green-satisfaction",
              cp5.returncode == 0 and "clean" in cp5.stdout,
              f"exit={cp5.returncode}, stdout={cp5.stdout.strip()[:200]!r}", failures)

        # --- check3-fires-on-historical-plus-supersededby (the live-specimen shape) ---
        d6 = tmp / "case6"
        write(d6, "Survey.md",
              "# Survey\n\n<!-- doc-attest-exempt: agent-authored survey. Removal condition: "
              "superseded by a ratified spec that cites it. -->\n"
              "<!-- design-currency: status=historical superseded-by=Successor.md -->\n")
        write(d6, "Successor.md", "# Successor\n\n<!-- design-currency: status=in-build -->\n")
        cp6 = run_gate(d6, strict=True)
        check("check3-fires-on-historical-plus-supersededby",
              cp6.returncode == 1 and "Survey.md" in cp6.stdout
              and "unreconciled" in cp6.stdout,
              f"exit={cp6.returncode}, stdout={cp6.stdout.strip()[:300]!r}", failures)

        # --- green-superseded-by-discharged-successor (fix-round regression guard) ---
        d7 = tmp / "case7"
        write(d7, "Old.md", "# Old\n\n<!-- design-currency: status=historical "
                             "superseded-by=Built.md -->\n")
        write(d7, "Built.md", "# Built\n\n<!-- design-currency: status=discharged "
                               f"discharged-by={head} -->\n")
        cp7 = run_gate(d7, strict=True)
        check("green-superseded-by-discharged-successor",
              cp7.returncode == 0 and "clean" in cp7.stdout,
              f"exit={cp7.returncode}, stdout={cp7.stdout.strip()[:200]!r}", failures)

    if failures:
        print(f"design-currency fixtures: {len(failures)}/7 case(s) FAILED: {failures}")
        return 1
    print("design-currency fixtures: all 7 cases matched their expected polarity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
