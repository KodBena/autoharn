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
  red-duplicate-headers-both-valid -- two individually well-formed design-currency headers in one
                                  doc -> check-4 advisory naming the doc, the count, and both
                                  statuses; never silently takes the first. --strict exit 1.
  red-duplicate-headers-first-valid-second-garbled -- first header well-formed, second carries no
                                  `status` field at all -> same duplicate-header advisory, second
                                  status reported as `<missing>`. --strict exit 1.
  red-dangling-depends-on        -- a live doc's depends-on names a doc that does not exist under
                                  the design dir -> "depends-on target missing" advisory, distinct
                                  from the drift message. --strict exit 1.
  green-depends-on-headerless-target-silent -- a live doc depends-on a doc that EXISTS but carries
                                  no currency header -> raises NOTHING (the documented asymmetry:
                                  check 5's no-per-doc-noise rule applied to an edge). --strict
                                  exit 0.
  green-indented-example-not-duplicate -- regression guard for the false positive found live
                                  authoring this fix round: this spec's OWN §2 code block quotes
                                  the header grammar at 4-space indent, which an earlier
                                  `HEADER_RE` (no `^`/MULTILINE anchor) matched as a second real
                                  header on the spec's own doc. A doc with one flush-left header
                                  plus an indented illustrative line must NOT trip the duplicate-
                                  header check. --strict exit 0.

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

        # --- red-duplicate-headers-both-valid ---
        d8 = tmp / "case8"
        write(d8, "Dup.md",
              "# Dup\n\n<!-- design-currency: status=proposed -->\n\ntext in between\n\n"
              f"<!-- design-currency: status=discharged discharged-by={head} -->\n")
        cp8 = run_gate(d8, strict=True)
        check("red-duplicate-headers-both-valid",
              cp8.returncode == 1 and "multiple design-currency headers" in cp8.stdout
              and "'proposed'" in cp8.stdout and "'discharged'" in cp8.stdout,
              f"exit={cp8.returncode}, stdout={cp8.stdout.strip()[:300]!r}", failures)

        # --- red-duplicate-headers-first-valid-second-garbled ---
        d9 = tmp / "case9"
        write(d9, "DupGarbled.md",
              "# DupGarbled\n\n<!-- design-currency: status=proposed -->\n\ntext\n\n"
              "<!-- design-currency: depends-on=Nowhere.md -->\n")
        cp9 = run_gate(d9, strict=True)
        check("red-duplicate-headers-first-valid-second-garbled",
              cp9.returncode == 1 and "multiple design-currency headers" in cp9.stdout
              and "<missing>" in cp9.stdout,
              f"exit={cp9.returncode}, stdout={cp9.stdout.strip()[:300]!r}", failures)

        # --- red-dangling-depends-on ---
        d10 = tmp / "case10"
        write(d10, "Dangling.md", "# Dangling\n\n<!-- design-currency: status=ratified "
                                   "depends-on=NoSuchDoc.md -->\n")
        cp10 = run_gate(d10, strict=True)
        check("red-dangling-depends-on",
              cp10.returncode == 1 and "depends-on target missing" in cp10.stdout,
              f"exit={cp10.returncode}, stdout={cp10.stdout.strip()[:300]!r}", failures)

        # --- green-depends-on-headerless-target-silent (documented asymmetry) ---
        d11 = tmp / "case11"
        write(d11, "LiveHeaderless.md", "# LiveHeaderless\n\n<!-- design-currency: status=ratified "
                                         "depends-on=Headerless.md -->\n")
        write(d11, "Headerless.md", "# Headerless\n\nno currency header here at all.\n")
        cp11 = run_gate(d11, strict=True)
        check("green-depends-on-headerless-target-silent",
              cp11.returncode == 0 and "clean" in cp11.stdout,
              f"exit={cp11.returncode}, stdout={cp11.stdout.strip()[:200]!r}", failures)

        # --- green-indented-example-not-duplicate (false-positive regression guard) ---
        d12 = tmp / "case12"
        write(d12, "SpecLike.md",
              "# SpecLike\n\n<!-- design-currency: status=in-build -->\n\n"
              "Grammar, illustrated (indented, not a real second header):\n\n"
              "    <!-- design-currency: status=<token> [discharged-by=<sha>] -->\n")
        cp12 = run_gate(d12, strict=True)
        check("green-indented-example-not-duplicate",
              cp12.returncode == 0 and "clean" in cp12.stdout,
              f"exit={cp12.returncode}, stdout={cp12.stdout.strip()[:200]!r}", failures)

    if failures:
        print(f"design-currency fixtures: {len(failures)}/12 case(s) FAILED: {failures}")
        return 1
    print("design-currency fixtures: all 12 cases matched their expected polarity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
