#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T07:54:37Z
#   last-change: 2026-07-14T22:12:50Z
#   contributors: 9bcc0113/main, be693afb/main, e4410ef6/main, 3c50e030/main, a857c93d/main
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

# (1) the top-level allowlist. THIS REGISTRY (ROOT_FILES/ROOT_DIRS below) is the LIVING SSOT
# for this invariant (corrected 2026-07-14, work item layout-census-teach-text-stale-ssot;
# ADR-0012 P1, one owner per fact) — LAYOUT.md §1 is the frozen, point-in-time founding DESIGN
# record (Status: DESIGN, provenance/LAYOUT.md; law/adr/0005 Rule 8 protected, never retro-
# edited to track the tree's organic growth) that this registry originally derived from and has
# since factually diverged from and superseded as the thing actually enforced. A new top-level
# entry is registered HERE, not in LAYOUT.md.
ROOT_FILES = {
    "README.md", "CLAUDE.md", "GLOSSARY.md", "BACKLOG.md", "FINDINGS.md", ".gitignore",
    # organic additions since LAYOUT.md §1 was drafted (session 59c83ca6, 2026-07-09) —
    # LAYOUT.md is a frozen point-in-time design record and is never amended to match; this
    # registry is the living SSOT that tracks them instead.
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
    # USER-GUIDE.md, attest-tags — pre-existing gap (landed by the doc-audience-taxonomy sweep
    # and an earlier commission respectively, neither of which registered here), hit while
    # panel-cheap-fixes was editing USER-GUIDE.md itself; fixed in passing rather than left an
    # unregistered breach for the next gate run (CLAUDE.md hazard-flagging duty, 2026-07-12).
    "USER-GUIDE.md", "attest-tags",
    # LICENSE (the Unlicense, added fca1100, maintainer's choice 2026-07-12) -- a root
    # standing-document like the others above, never registered when it landed; caught by
    # this gate's own next run (tracker item layout-census-license-unregistered, CLAUDE.md
    # hazard-flagging duty).
    "LICENSE",
    # VESTIGIAL-INDEX.md (merge d4aac05, the vestigial-doc-sweep's mandatory root index --
    # one paragraph per moved doc) -- landed with the sweep, never registered here; caught
    # at the same 2026-07-13 seam as the vestigial_documentation/ dir registration above.
    "VESTIGIAL-INDEX.md",
    # migrate — the sixth repo-root operator verb shim (bootstrap/migrate.sh), landed alongside
    # led/judge/pickup/audit/distance-to-clean but never registered here; caught by this gate's
    # own next run (CLAUDE.md hazard-flagging duty, root-shims-and-layout-census work item).
    "migrate",
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
    # vestigial_documentation/ — the 2026-07-12 vestigial-doc-sweep's declared-history archive
    # (47 moved docs, indexed by root VESTIGIAL-INDEX.md; merge d4aac05). The sweep registered
    # the dir in link_integrity/doc_attestation exclusions but missed this census; caught at a
    # 2026-07-13 merge seam when the LICENSE registration made the gate re-run (CLAUDE.md
    # hazard-flagging duty).
    "vestigial_documentation",
    # observatory/ — the ent-observatory commission's recurring read-only evaluation of the
    # live ~/ent deployment (autoharn tracker row 372, 2026-07-13): one dated cycle report per
    # run under observatory/ent/, each doc-attest-exempt (point-in-time evidence record) and
    # diffed against prior cycles. Registered on landing rather than left an unregistered
    # breach for this gate's next run (CLAUDE.md hazard-flagging duty).
    "observatory",
    # proposals/ — TRANSITIONAL (ADR-0005 Rule 7, retirement plan stated here): patch files for
    # merge-gated surfaces (live-exec'd templates/hooks), staged by builders whose commissions
    # forbid touching those surfaces while a deployment session is live (merge-gate policy,
    # 2026-07-13). Each patch retires when applied at a session gap; the directory empties and
    # may itself be retired when the gate policy has no standing holds. First entries:
    # scaffold-governed-set-language-default's two template patches (merge e54c1eb).
    "proposals",
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
                                f"(add to this registry's ROOT_DIRS — the living SSOT, see the "
                                f"module docstring and the ROOT_FILES comment above — or it is "
                                f"a misfit-absorbing parent)")
        elif entry not in ROOT_FILES:
            breaches.append(f"UNREGISTERED top-level file: {entry} "
                            f"(a root standing-document must be registered in this registry's "
                            f"ROOT_FILES — the living SSOT — not in the frozen LAYOUT.md §1 design)")

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
