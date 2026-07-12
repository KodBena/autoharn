#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T07:54:37Z
#   last-change: 2026-07-12T02:31:38Z
#   contributors: 9bcc0113/main, be693afb/main, e4410ef6/main
# <<< PROVENANCE-STAMP <<<

"""layout_census — LAYOUT.md's designed tree as a MECHANICAL registry (manifest [C21]).

LAYOUT.md §3.4: "ls-legibility asserted once and never re-checked would rot exactly as the
old repos did." This gate keeps the conformance a CHECKED property, not a founding legend.
It enforces two of LAYOUT's claims mechanically and declares the third review-only:

  1. TOP-LEVEL ALLOWLIST (ADR-0008 default-to-flat): every top-level tracked entry is a
     registered single-currency directory or a registered root standing-document. An
     unregistered top-level entry is the synthetic-parent / misfit-absorption failure —
     RED.
  2. PER-DIRECTORY CURRENCY PATTERNS: for the directories whose currency is a strict file
     shape, every file matches the shape (stores/ = numbered DDL + fixtures; law/adr/ =
     NNNN-*.md; kernel/lineage/ = *.sql + README; seen-red/ = per-gate dirs only, no loose
     files; runs/ = run-id dirs + README). A pattern breach is RED.
  3. SINGLE-CURRENCY JUDGMENT (declared REVIEW-ONLY, ADR-0011 Rule 1): whether a NEW file
     inside a currency directory (design/, judgment/, instruments/, …) actually belongs to
     that directory's one currency is a human judgment no regex can make. This gate does not
     pretend to; it is named here as the honest residue, not silently omitted.

Exit 0 clean; exit 1 listing every breach. Run from repo root: python3 gates/layout_census.py
Lazy imports banned.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (1) the top-level allowlist — LAYOUT §1's designed tree, verbatim (the SSOT for this invariant).
ROOT_FILES = {
    "README.md", "CLAUDE.md", "GLOSSARY.md", "BACKLOG.md", "FINDINGS.md", ".gitignore",
    # organic additions since LAYOUT.md §1 was drafted (session 59c83ca6, 2026-07-09) —
    # LAYOUT.md's tree/table are not yet amended to match; flagged for maintainer review.
    # Renamed by the doc-audience-taxonomy sweep (2026-07-12): DIRCLASS/CAPABILITIES/HANDOFF ->
    # ORCH-*, WALKTHROUGH -> USER-*, POST-FABLE-OPERATING-BRIEF/OPERATING-CARD -> ORCH-*.
    "ORCH-DIRCLASS.md", "ORCH-CAPABILITIES.md", "ORCH-HANDOFF.md", "USER-WALKTHROUGH.md",
    "ORCH-POST-FABLE-OPERATING-BRIEF.md",  # succession handoff, root doc (2026-07-09)
    "ORCH-OPERATING-CARD.md",  # Opus-readiness operating-era quick reference, root doc (2026-07-11)
    # CONFIGURATION.md (pre-existing gap, unregistered before this edit too), renamed to
    # USER-CONFIGURATION.md by the doc-audience-taxonomy sweep; registered now while this exact
    # set is already being touched (CLAUDE.md hazard-flagging duty).
    "USER-CONFIGURATION.md",
    # bootstrap/track-work.sh's own STANDING deployment on autoharn itself (design/
    # USER-WORK-STATUS-OFFERING.md, deliverable 2, 2026-07-11): deployment.json + the five verb
    # shims (led/judge/pickup/audit/distance-to-clean), landing at the repo root because that
    # IS this deployment's project-dir. No hooks are wired for it (a standing project is not a
    # governed world — track-work.sh's own header comment) so these are inert outside a
    # deliberate `./led`/`./pickup`/etc invocation; registered here so an unregistered-top-level
    # breach does not fire on the offering's own first, self-hosted consumer.
    "deployment.json", "led", "judge", "pickup", "audit", "distance-to-clean",
    # .gitattributes — the merge-driver wiring for attestations/*.jsonl and BACKLOG.md's dated
    # sections (design/ORCH-WORKTREE-LEDGERING.md 3a; tools/merge_jsonl.py,
    # tools/merge_backlog_sections.py), a new top-level file this same commission created,
    # registered here rather than left an unregistered breach for the census gate to hit next
    # run (CLAUDE.md hazard-flagging duty, worktree-ledgering-implementation, 2026-07-12).
    ".gitattributes",
}
ROOT_DIRS = {
    ".claude", "bootstrap", "law", "judgment", "kernel", "stores", "instruments", "engine",
    "gates", "filing", "hooks", "drive", "seen-red", "design", "research", "runs", "ephemera",
    "provenance",
    # attestations/ — ADR-0017's A:B:C fresh-context audit-loop ledger
    # (attestations/doc-legibility-attestations.jsonl, gates/doc_attestation_presence.py),
    # landed 2026-07-11 but never added here; caught in passing while registering
    # design/USER-WORK-STATUS-OFFERING.md's own two attestations (CLAUDE.md hazard-flagging duty).
    "attestations",
    # tools/ — the doc-audience-taxonomy work item's per-document rename primitive
    # (tools/rename_doc.py); a new top-level directory this same sweep created, registered here
    # rather than left an unregistered breach for the census gate to hit next run (CLAUDE.md
    # hazard-flagging duty).
    "tools",
}

# (2) per-directory currency patterns: a directory -> the regex(es) its basenames MUST match.
#     A directory absent here is review-only (its single-currency claim is not regex-checkable).
DIR_PATTERNS: dict[str, list[str]] = {
    "stores":        [r"^\d{3}_.*\.sql$", r"^.*_fixture\.py$", r"^test_.*\.py$"],
    "law/adr":       [r"^\d{4}-.*\.md$"],
    "kernel/lineage": [r"^.*\.sql$", r"^README\.md$"],
    "runs":          [r"^README\.md$"],   # everything else under runs/ must live in a run-id subdir
}
# runs/ and seen-red/ additionally forbid LOOSE top-level files beyond an allowed set (evidence trees).
_RUNS_LOOSE_OK = {"README.md"}


def tracked() -> list[str]:
    out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True, check=True)
    return [l for l in out.stdout.splitlines() if l.strip()]


def main() -> int:
    files = tracked()
    breaches: list[str] = []

    # (1) top-level allowlist
    top = {f.split("/", 1)[0] for f in files}
    for entry in sorted(top):
        is_dir = any(f.startswith(entry + "/") for f in files)
        if is_dir:
            if entry not in ROOT_DIRS:
                breaches.append(f"UNREGISTERED top-level directory: {entry}/ "
                                f"(add to LAYOUT §1 + this registry, or it is a misfit-absorbing parent)")
        elif entry not in ROOT_FILES:
            breaches.append(f"UNREGISTERED top-level file: {entry} "
                            f"(a root standing-document must be registered in LAYOUT §1)")

    # (2) per-directory currency patterns
    for f in files:
        for d, pats in DIR_PATTERNS.items():
            prefix = d + "/"
            if not f.startswith(prefix):
                continue
            rest = f[len(prefix):]
            base = os.path.basename(f)
            if d in ("runs",):
                # runs/ : only README loose; everything else must be under a run-id subdir
                if "/" not in rest and base not in _RUNS_LOOSE_OK:
                    breaches.append(f"PATTERN BREACH {f}: runs/ holds only run-id subdirs + README")
                continue
            if "/" in rest:   # nested (e.g. a subdir) — pattern applies to the directory's own files
                continue
            if not any(re.match(p, base) for p in pats):
                breaches.append(f"PATTERN BREACH {f}: {base!r} does not match {d}/ currency "
                                f"({' | '.join(pats)})")

    # (2b) seen-red/ forbids loose top-level files (only per-gate subdirs)
    for f in files:
        if f.startswith("seen-red/") and "/" not in f[len("seen-red/"):]:
            breaches.append(f"PATTERN BREACH {f}: seen-red/ holds only per-gate subdirs, no loose files")

    if breaches:
        print(f"layout-census: {len(breaches)} breach(es) of the designed tree (LAYOUT §1):\n")
        for b in breaches:
            print(f"  !! {b}")
        return 1
    print(f"layout-census: clean ✓  ({len(ROOT_DIRS)} registered dirs, {len(ROOT_FILES)} root docs; "
          f"per-directory currency patterns hold). Single-currency judgment for new files is review-only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
