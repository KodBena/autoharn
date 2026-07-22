#!/usr/bin/env python3
"""Seen-red fixture for gates/typed_table_drift.py (work item typed-table-ssot-integration,
gates/fixture_census.py REGISTRY entry "typed-table-drift"). Proves, both polarities, against a
fully SCRATCH registry+doc (never the live corpus — this fixture must be safe to run any number
of times without ever touching a real tracked doc):

  RED   — a doc region hand-edited to diverge from its registered builder's current output
          reports DRIFT and the gate exits 1;
  GREEN — the same doc immediately after `tools.doc_table_generation.write()` exits 0;
  MISSING-ANCHOR — a doc with no BEGIN/END anchor pair for a registered id is refused (not
          silently skipped) and the gate exits 1;
  CLEAN-REPORT — the real, live registry (untouched, not scratch) is also exercised once via a
          real subprocess call to the actual gate, to prove the fixture is not merely testing a
          mock — this call is READ-ONLY (gate mode never writes) so it is safe against the live
          corpus.

No network, no DB, no cost: pure-stdlib gate plus the two tools/ modules it imports.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "gates"))
sys.path.insert(0, str(REPO / "tools" / "experiments"))

import doc_table_generation as dtg  # noqa: E402
import typed_table_drift as gate  # noqa: E402
from typed_table import Table  # noqa: E402 — lazy imports are banned (CLAUDE.md 2026-07-02);
# hoisted here rather than inside _scratch_builder()/main(), same fix as gates/doc_tables.py's
# own module-top sys.path-then-import shape.

SCRATCH_DOC_TEMPLATE = """# Scratch doc

Some prose above the table.

<!-- typed-table:BEGIN id=scratch-fixture -->
{region}
<!-- typed-table:END id=scratch-fixture -->

Some prose below the table.
"""

NO_ANCHOR_DOC = """# Scratch doc with no anchors

| kind | example |
| --- | --- |
| alpha | a specimen |
"""


def _scratch_builder():
    t = Table(type_former="kind", columns=["kind", "example"])
    t.row("alpha", "a specimen", inhabits="'alpha' is a kind, given as an example row.")
    return t


def main() -> int:
    failures: list = []
    real_registry = dtg.REGISTRY
    real_repo_root = dtg.REPO_ROOT
    try:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            scratch_doc = tdp / "scratch.md"
            no_anchor_doc = tdp / "no_anchor.md"
            # Region built from the builder's OWN render output, not hand-typed — the fixture
            # must start genuinely in sync (a hand-typed table could silently mismatch the
            # constructor's exact byte format, e.g. the provenance comment line) and this is
            # itself the same one-home discipline the gate enforces.
            initial_region = _scratch_builder().render().rstrip("\n")
            scratch_doc.write_text(SCRATCH_DOC_TEMPLATE.format(region=initial_region),
                                    encoding="utf-8")
            no_anchor_doc.write_text(NO_ANCHOR_DOC, encoding="utf-8")

            # Point the module at the scratch tree so `entry["doc"]` (repo-root-relative)
            # resolves inside td, never inside the real repo.
            dtg.REPO_ROOT = tdp
            dtg.REGISTRY = {
                "scratch-fixture": {"doc": "scratch.md", "builder": _scratch_builder},
            }

            # CASE 1: GREEN — doc freshly written to match the builder exactly.
            findings = gate.doc_table_generation.check()
            print(f"CASE 1 (in-sync scratch doc): findings={findings}")
            if findings:
                failures.append(f"expected clean, got: {findings}")

            code = gate.main()
            print(f"CASE 1b (gate.main() on in-sync scratch registry): exit={code}")
            if code != 0:
                failures.append("expected gate.main() exit 0 on in-sync registry")

            # CASE 2: RED — hand-edit the region so it diverges from the builder.
            text = scratch_doc.read_text(encoding="utf-8")
            drifted = text.replace("| alpha | a specimen |", "| alpha | HAND-EDITED specimen |")
            assert drifted != text
            scratch_doc.write_text(drifted, encoding="utf-8")
            findings = gate.doc_table_generation.check()
            print(f"CASE 2 (hand-drifted scratch doc): findings={findings}")
            if not findings or not any("DRIFT" in f for f in findings):
                failures.append(f"expected a DRIFT finding, got: {findings}")
            code = gate.main()
            print(f"CASE 2b (gate.main() on drifted registry): exit={code}")
            if code != 1:
                failures.append("expected gate.main() exit 1 on drifted registry")

            # CASE 3: restore via write() -> GREEN again, proving --write is the sanctioned fix.
            touched = dtg.write()
            print(f"CASE 3 (dtg.write() restores sync): touched={touched}")
            findings = gate.doc_table_generation.check()
            if findings:
                failures.append(f"expected clean after write(), got: {findings}")
            if touched != ["scratch.md"]:
                failures.append(f"expected write() to report scratch.md touched, got {touched}")

            # CASE 4: MISSING-ANCHOR — a registered doc with no anchor pair at all.
            dtg.REGISTRY = {
                "scratch-fixture": {"doc": "no_anchor.md", "builder": _scratch_builder},
            }
            findings = gate.doc_table_generation.check()
            print(f"CASE 4 (no anchor pair in doc): findings={findings}")
            if not findings or not any("no BEGIN anchor" in f for f in findings):
                failures.append(f"expected a 'no BEGIN anchor' finding, got: {findings}")
    finally:
        dtg.REGISTRY = real_registry
        dtg.REPO_ROOT = real_repo_root

    # CASE 5: the real gate, as a real subprocess, against the real (live, untouched) registry
    # — read-only, so safe to run unconditionally.
    real = subprocess.run([sys.executable, str(REPO / "gates" / "typed_table_drift.py")],
                          capture_output=True, text=True, cwd=REPO)
    print(f"CASE 5 (real gate, real registry, subprocess): exit={real.returncode}")
    print(real.stdout.rstrip())
    if real.returncode != 0:
        failures.append(f"expected the LIVE registry to be clean (in-sync); gate said: "
                         f"{real.stdout}")

    if failures:
        print("typed-table-drift red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("typed-table-drift red-specimen: all five cases behaved as designed — red on a "
          "hand-drifted scratch doc naming DRIFT, green once dtg.write() resyncs it, red (not "
          "silently skipped) on a registered doc missing its anchor pair, and the real gate "
          "clean against the real, live, in-sync registry.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
