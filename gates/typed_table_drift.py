#!/usr/bin/env python3
"""typed_table_drift — the mechanical GATE half of `tools/doc_table_generation.py` (work item
`typed-table-ssot-integration`, follow-up to the typed-table-constructor-experiment ADOPTION).
Wraps that module's `check()` as a gate, following `gates/doc_tables.py`'s own precedent (a
thin gate importing its `tools/` single-home engine rather than re-deriving the check).

CLOSURE STATEMENT (ADR-0000 Rule 2a):
  - INVARIANT: for every table id in `tools.doc_table_registry.REGISTRY`, the bytes between its
    doc's `<!-- typed-table:BEGIN id=... -->` / `... END ...` anchors equal, character for
    character, what that table's registered builder renders TODAY — no missing anchor pair, no
    duplicate anchor pair, no stale (hand-edited or un-regenerated) region.
  - QUANTIFICATION UNIVERSE: every table id in `REGISTRY` — a doc/table pair not registered is
    out of scope by construction (it never claimed the constructor as its home); the registry
    itself is the enumerated universe, exactly `gates/column_complete_gate.py`'s own precedent
    for a registry-scoped closure statement. A doc opts a table INTO this gate's scope solely by
    the table being added to `tools/doc_table_registry.REGISTRY` — never by this gate
    re-discovering anchor comments unregistered.
  - DENOMINATION: the resource is "a registered table id", not a proxy (not doc count, not line
    count) — one violation per drifted/malformed table, reported by id and doc path.

MODE: always runs over the FULL registry (unlike file-scanning gates such as `doc_tables.py`,
a registered table's doc is not necessarily among the files staged in a given commit — a
hand-edit to the doc region, with no other change to the builder file, would otherwise slip a
staged-files-only gate; the registry is small by construction, so scanning all of it every run
costs nothing).

Usage: `python3 gates/typed_table_drift.py` — exit 0 clean, exit 1 listing every drift finding.
Exit codes: 0 clean, 1 gate violations.
Lazy imports are banned (CLAUDE.md, 2026-07-02): everything below imports at module load.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))
import doc_table_generation  # noqa: E402


def main(argv=None) -> int:
    findings = doc_table_generation.check()
    n = len(doc_table_generation.REGISTRY)
    if findings:
        print(f"typed-table-drift: {len(findings)} finding(s) over {n} registered table(s):\n")
        for f in findings:
            print(f"  !! {f}")
        return 1
    print(f"typed-table-drift: clean ✓ ({n} registered table(s) match their builder's current "
          f"output)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
