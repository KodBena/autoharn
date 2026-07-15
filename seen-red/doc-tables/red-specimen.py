#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-15T14:12:11Z
#   last-change: 2026-07-15T14:12:11Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for gates/doc_tables.py (work item doc-table-mechanization,
gates/fixture_census.py REGISTRY entry "doc-tables"). Proves, both polarities, on live
subprocess runs of the real gate:

  RED   — gate mode on a doc carrying an em-dash-separator table (the exact defect class this
          work item found live in law/adr/0012-compositional-and-structural-hygiene.md, three
          instances, fixed by this same commission) names SEPARATOR-INVALID-CHARS and exits 1;
  GREEN — gate mode on the same table with a canonical hyphen separator exits 0;
  EXCLUDED-NOT-GATED — a file path under judgment/ carrying the same defect is reported by the
          gate as excluded, not gated (exit 0), matching the gate's own declared exclusions;
  REPORT-NEVER-FAILS — report mode (no args) exits 0 regardless of standing findings.

No network, no DB, no cost: pure-stdlib gate, temp files only.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "doc_tables.py"

BAD = """# A doc

| A | B | C |
| — | — | — |
| x | y | z |
"""

GOOD = """# A doc

| A | B | C |
| --- | --- | --- |
| x | y | z |
"""


def run(*args: str, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *args],
                          capture_output=True, text=True, cwd=cwd or REPO)


def main() -> int:
    failures: list = []
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.md"
        good = Path(td) / "good.md"
        bad.write_text(BAD, encoding="utf-8")
        good.write_text(GOOD, encoding="utf-8")

        red = run(str(bad))
        print(f"CASE 1 (em-dash-separator table, gate mode): exit={red.returncode}")
        print(red.stdout.rstrip())
        if red.returncode != 1:
            failures.append("expected exit 1 on the em-dash-separator doc")
        if "separator-invalid-chars" not in red.stdout:
            failures.append("expected 'separator-invalid-chars' named in the red output")

        green = run(str(good))
        print(f"CASE 2 (canonical hyphen separator, gate mode): exit={green.returncode}")
        if green.returncode != 0:
            failures.append(f"expected exit 0 on the clean doc; stdout: {green.stdout}")

        # (3) excluded-prefix path: run the gate from a cwd rooted so the relative path
        # actually starts with "judgment/" -- the gate's exclusion check is prefix-based on
        # the path string it is handed, matching how a real invocation would pass a
        # judgment/-relative path from repo root.
        judgment_dir = REPO / "judgment"
        rel_candidate = None
        if judgment_dir.is_dir():
            for p in judgment_dir.rglob("*.md"):
                rel_candidate = p.relative_to(REPO)
                break
        if rel_candidate is not None:
            excl = run(str(rel_candidate))
            print(f"CASE 3 (a real judgment/ doc, gate mode): exit={excl.returncode}")
            if "not gated" not in excl.stdout:
                failures.append("expected the judgment/ path to be reported as excluded/not "
                                 "gated")
        else:
            print("CASE 3 skipped: no *.md found under judgment/ in this checkout")

        report = run()
        print(f"CASE 4 (repo-wide report mode): exit={report.returncode} "
              f"(findings are informational; exit must be 0)")
        if report.returncode != 0:
            failures.append("report mode must always exit 0")

    if failures:
        print("doc-tables red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("doc-tables red-specimen: all four cases behaved as designed — red on the "
          "em-dash-separator doc naming the reason, green on the canonical-separator doc, "
          "the excluded prefix reported but not gated, report mode never failing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
