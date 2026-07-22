#!/usr/bin/env python3
"""Seen-red specimen for gates/doc_shapes.py (the zero-context-reader discipline's
deterministic core, design/ADR-DRAFT-documentation-discipline.md Rule 3;
gates/fixture_census.py REGISTRY entry "doc-shapes"). Proves, both polarities, on live
subprocess runs of the real gate:

  RED   — gate mode on a defective document flags BOTH checks (a standalone fragment
          paragraph, and a bare positional reference into HANDOFF) and exits 1;
  GREEN — gate mode on a clean document (full sentences; the sanctioned quoted-handle
          HANDOFF form from commit 48dce0c; a waived deliberate fragment; the exempt
          license line) exits 0;
  REPORT-NEVER-FAILS — report mode (no args) exits 0 regardless of standing findings,
          because the back-catalog binds on touch (ADR draft Rule 4), never by sweep.

No network, no DB, no cost: pure-stdlib gate, temp files only.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "doc_shapes.py"

BAD = """# A doc

The core deliverable.

Drafted per HANDOFF open-work item 2 from the two witnessed episodes.
"""

GOOD = """# A doc

This document records the deliverable in a full sentence, grounded for a cold reader.

Queued as item (a) of the maintainer's batch in HANDOFF "Open work" item 1.

A deliberate fragment. <!-- doc-shapes-allow: fixture exercising the waiver -->

Public Domain (The Unlicense).
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *args],
                          capture_output=True, text=True, cwd=REPO)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.md"
        good = Path(td) / "good.md"
        bad.write_text(BAD, encoding="utf-8")
        good.write_text(GOOD, encoding="utf-8")

        red = run(str(bad))
        print(f"CASE 1 (defective doc, gate mode): exit={red.returncode}")
        print(red.stdout.rstrip())
        if red.returncode != 1:
            failures.append("expected exit 1 on the defective doc")
        if "FRAGMENT" not in red.stdout or "HANDOFF-POSITIONAL" not in red.stdout:
            failures.append("expected BOTH checks named in the red output")

        green = run(str(good))
        print(f"CASE 2 (clean doc incl. quoted-handle form + waiver, gate mode): "
              f"exit={green.returncode}")
        if green.returncode != 0:
            failures.append(f"expected exit 0 on the clean doc; stdout: {green.stdout}")

        report = run()
        print(f"CASE 3 (repo-wide report mode): exit={report.returncode} "
              f"(findings are informational; exit must be 0)")
        if report.returncode != 0:
            failures.append("report mode must always exit 0")

    if failures:
        print("doc-shapes red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("doc-shapes red-specimen: all three cases behaved as designed — red on the "
          "defective doc naming both checks, green on the clean doc, report mode "
          "never failing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
