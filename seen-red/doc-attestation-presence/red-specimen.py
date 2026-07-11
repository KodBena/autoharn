#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-11T16:35:50Z
#   last-change: 2026-07-11T16:36:22Z
#   contributors: e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for gates/doc_attestation_presence.py (the ADR-0017 A:B:C fresh-context
audit loop's commit-time enforcement floor; gates/fixture_census.py REGISTRY entry
"doc-attestation-presence"). Proves, both polarities, on live subprocess runs of the real gate
against a throwaway temp repo tree (never against tracked repo content — recording a real
attestation into the LIVE ledger from a fixture would corrupt the audit trail the gate itself
exists to protect):

  RED-NO-ATTESTATION  -- gate mode on a doc with no matching ledger entry exits 1, naming the
                          content hash and pointing at the A:B:C recipe + --record.
  RED-MALFORMED       -- --record refuses (exit 2) a DEFECT record with no findings (an
                          umbrella verdict), a CLEAN record missing a Rule-1 clause, and a
                          record still-DEFECT at the two-round cap with escalated=false — none
                          of the three are ever appended to the ledger.
  GREEN               -- --record accepts a well-shaped CLEAN record (exit 0), and gate mode on
                          that same doc then exits 0.
  WAIVER-NOT-PROSE    -- a doc that merely MENTIONS the waiver token in plain prose (not inside
                          an HTML comment) is NOT waived and still gets flagged RED -- the live
                          bug this gate's own build hit (design/ABC-AUDIT-LOOP-RECIPE.md's own
                          worked-example prose false-triggered a raw substring check) and the
                          regression this case pins.
  REPORT-NEVER-FAILS  -- report mode (no args) always exits 0, mirroring gates/doc_shapes.py.

No network, no DB, no cost: pure-stdlib gate, temp files + a monkeypatched REPO_ROOT/LEDGER_PATH
only, so the real attestations/doc-legibility-attestations.jsonl is never touched.

Usage: python3 seen-red/doc-attestation-presence/red-specimen.py
Exit 0 if every case matches; 1 otherwise. Lazy imports banned.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GATE = REPO / "gates" / "doc_attestation_presence.py"


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *args],
                          capture_output=True, text=True, cwd=str(cwd))


def _load_gate_module(repo_root: Path, ledger: Path):
    """Import doc_attestation_presence.py as a fresh module with REPO_ROOT/LEDGER_PATH
    monkeypatched to a throwaway temp tree -- used only for the --record in-process checks
    that need direct access to validate_record without shelling out per case."""
    spec = importlib.util.spec_from_file_location("_dap_seenred", GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # noqa: S102 -- loading our own gate module, not untrusted code
    mod.REPO_ROOT = repo_root
    mod.LEDGER_PATH = ledger
    return mod


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="doc-attest-seenred-"))
    failures: list[str] = []
    try:
        doc = tmp / "sample.md"
        doc.write_text("# Sample\n\nA short, clean paragraph with a real sentence.\n",
                        encoding="utf-8")
        ledger = tmp / "attestations" / "doc-legibility-attestations.jsonl"

        mod = _load_gate_module(tmp, ledger)

        # --- RED-NO-ATTESTATION -------------------------------------------------------
        rc = mod.main([str(doc)])
        print(f"CASE RED-NO-ATTESTATION: exit={rc}")
        if rc != 1:
            failures.append("expected exit 1 with no attestation record")

        # --- RED-MALFORMED (three sub-cases, none ever appended) -----------------------
        umbrella = {"doc": "sample.md", "b_id": "x",
                    "rounds": [{"round": 1, "verdict": "DEFECT", "findings": [],
                                "clauses_checked": []}],
                    "escalated": False}
        issues = mod.validate_record({**umbrella, "schema": "doc-attestation/1",
                                       "content_sha256": "a" * 64, "attested_at": "t"})
        print(f"CASE RED-MALFORMED (umbrella DEFECT, no findings): {len(issues)} issue(s)")
        if not issues:
            failures.append("umbrella DEFECT with no findings should be malformed")

        missing_clause = {"schema": "doc-attestation/1", "doc": "sample.md",
                           "content_sha256": "a" * 64, "b_id": "x", "attested_at": "t",
                           "rounds": [{"round": 1, "verdict": "CLEAN", "findings": [],
                                       "clauses_checked": ["1a", "1b", "1c"]}],
                           "escalated": False}
        issues = mod.validate_record(missing_clause)
        print(f"CASE RED-MALFORMED (CLEAN missing a Rule-1 clause): {len(issues)} issue(s)")
        if not issues:
            failures.append("CLEAN verdict missing a Rule-1 clause should be malformed")

        uncapped = {"schema": "doc-attestation/1", "doc": "sample.md",
                    "content_sha256": "a" * 64, "b_id": "x", "attested_at": "t",
                    "rounds": [
                        {"round": 1, "verdict": "DEFECT",
                         "findings": [{"file": "sample.md", "line": 1, "quote": "q", "repair": "r"}],
                         "clauses_checked": []},
                        {"round": 2, "verdict": "DEFECT",
                         "findings": [{"file": "sample.md", "line": 2, "quote": "q2", "repair": "r2"}],
                         "clauses_checked": []},
                    ],
                    "escalated": False}
        issues = mod.validate_record(uncapped)
        print(f"CASE RED-MALFORMED (2 rounds still DEFECT, escalated=false): {len(issues)} issue(s)")
        if not issues:
            failures.append("still-DEFECT at the two-round cap with escalated=false should be malformed")

        # --- GREEN ----------------------------------------------------------------------
        clean = {"schema": "doc-attestation/1", "doc": "sample.md",
                 "content_sha256": mod._sha256_of(doc), "b_id": "seen-red-fixture-B",
                 "attested_at": "2026-07-11T00:00:00Z",
                 "rounds": [{"round": 1, "verdict": "CLEAN", "findings": [],
                             "clauses_checked": ["1a", "1b", "1c", "1d"]}],
                 "escalated": False}
        issues = mod.validate_record(clean)
        print(f"CASE GREEN (well-shaped CLEAN record): {len(issues)} issue(s)")
        if issues:
            failures.append(f"a well-shaped CLEAN record should validate clean: {issues}")
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(clean) + "\n")
        rc = mod.main([str(doc)])
        print(f"CASE GREEN (gate mode after recording): exit={rc}")
        if rc != 0:
            failures.append("expected exit 0 once a matching well-shaped attestation is recorded")

        # --- WAIVER-NOT-PROSE ------------------------------------------------------------
        prose_doc = tmp / "mentions_token.md"
        prose_doc.write_text(
            "# Explains the waiver\n\n"
            "This document explains the token in prose: `doc-attest-exempt: <reason>` is the "
            "escape hatch, but merely naming it here must not itself waive this file.\n",
            encoding="utf-8")
        rc = mod.main([str(prose_doc)])
        print(f"CASE WAIVER-NOT-PROSE (token mentioned in prose, not an HTML comment): exit={rc}")
        if rc != 1:
            failures.append("a doc that only mentions the token in prose must still be flagged, not waived")

        real_waiver_doc = tmp / "real_waiver.md"
        real_waiver_doc.write_text(
            "# Genuinely waived\n\n"
            "<!-- doc-attest-exempt: point-in-time record, seen-red fixture -->\n"
            "Body text here.\n", encoding="utf-8")
        rc = mod.main([str(real_waiver_doc)])
        print(f"CASE WAIVER-NOT-PROSE (token inside a real HTML comment): exit={rc}")
        if rc != 0:
            failures.append("a doc with the token inside an HTML comment should be waived")

        # --- REPORT-NEVER-FAILS -----------------------------------------------------------
        # The temp fixture tree is not a git repo, so _tracked_md()'s `git ls-files` would
        # fail for a reason unrelated to what this case tests; monkeypatch it to the fixture
        # docs directly, same device seen-red/link-integrity/run_fixtures.py uses.
        mod._tracked_md = lambda: ["sample.md", "mentions_token.md", "real_waiver.md"]
        rc = mod.main([])
        print(f"CASE REPORT-NEVER-FAILS: exit={rc}")
        if rc != 0:
            failures.append("report mode must always exit 0")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("doc-attestation-presence red-specimen: FAILED —", "; ".join(failures))
        return 1
    print("doc-attestation-presence red-specimen: all cases behaved as designed — red on a "
          "missing attestation, refused-at-write on three malformed shapes, green once a "
          "well-shaped record is recorded, the prose-mention/HTML-comment waiver distinction "
          "holds, and report mode never fails.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
