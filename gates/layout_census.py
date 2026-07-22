#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-09T07:54:37Z
#   last-change: 2026-07-22T03:11:22Z
#   contributors: 9bcc0113/main, be693afb/main, e4410ef6/main, 3c50e030/main, a857c93d/main, ab5d5bab/main, 1fa3ab69/main, 431cddfa/main
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
    # user-guide/ORCH-HANDOFF.md, user-guide/USER-WALKTHROUGH.md, user-guide/ORCH-POST-FABLE-OPERATING-BRIEF.md,
    # user-guide/ORCH-OPERATING-CARD.md, user-guide/USER-CONFIGURATION.md, user-guide/USER-GUIDE.md moved OFF root into
    # user-guide/ by the doc-tree relocation (work item doc-tree-reorg-user-guide, ledger row
    # 1620, 2026-07-18); deregistered here, see the "user-guide" ROOT_DIRS entry below for
    # their new home. ORCH-CAPABILITIES.md stays root (maintainer's call, row 1625).
    "ORCH-DIRCLASS.md", "ORCH-CAPABILITIES.md",
    # bootstrap/track-work.sh's own STANDING deployment on autoharn itself (design/
    # USER-WORK-STATUS-OFFERING.md, deliverable 2, 2026-07-11): deployment.json + the five verb
    # shims (led/judge/pickup/audit/distance-to-clean), landing at the repo root because that
    # IS this deployment's project-dir. No hooks are wired for it (a standing project is not a
    # governed world — track-work.sh's own header comment) so these are inert outside a
    # deliberate `./led`/`./pickup`/etc invocation; registered here so an unregistered-top-level
    # breach does not fire on the offering's own first, self-hosted consumer.
    "deployment.json", "led", "judge", "pickup", "audit", "distance-to-clean",
    # deployment.json.example — the committed template deployment.json is generated from
    # (deployment.json itself is real/local and typically gitignored per-deployment; the
    # .example sibling is the tracked root standing-document). Pre-existing gap, never
    # registered here since deployment.json.example landed; caught in passing while this
    # exact registry was already being edited to add "orchlog" (CLAUDE.md hazard-flagging
    # duty: a hazard within reach of the touch gets fixed, not routed around).
    "deployment.json.example",
    # .gitattributes — the merge-driver wiring for attestations/*.jsonl and BACKLOG.md's dated
    # sections (vestigial_documentation/design/ORCH-WORKTREE-LEDGERING.md 3a; tools/merge_jsonl.py,
    # tools/merge_backlog_sections.py), a new top-level file this same commission created,
    # registered here rather than left an unregistered breach for the census gate to hit next
    # run (CLAUDE.md hazard-flagging duty, worktree-ledgering-implementation, 2026-07-12).
    ".gitattributes",
    # .gitmodules — landed with the tools/makespan-scheduler/ vendor-to-submodule conversion
    # (commit 5464937), never registered here at landing time; caught by this gate's own next
    # run while WP-4 (panel v2) was already editing this exact registry to add "panel" below
    # (CLAUDE.md hazard-flagging duty, same shape as the migrate/attestations/LICENSE entries
    # above -- a hazard within reach of the touch gets fixed, not routed around).
    ".gitmodules",
    # attest-tags — pre-existing gap (landed by an earlier commission, never registered here),
    # hit while panel-cheap-fixes was editing USER-GUIDE.md (root, at the time) itself; fixed
    # in passing rather than left an unregistered breach for the next gate run (CLAUDE.md
    # hazard-flagging duty, 2026-07-12). USER-GUIDE.md itself moved off root into user-guide/
    # 2026-07-18 (see above).
    "attest-tags",
    # extract-context — the mechanized world-context extraction verb (FABLE-WORLD-CONTEXT-
    # MIGRATION-CONSULT-2026-07-19.md; autoharn ledger row 1942 step 1). Repo-root style shim
    # like led/judge/pickup/audit/distance-to-clean/attest-tags above, but not scaffolded into
    # every world by new-project.sh -- both its `extract` and `ingest` subcommands take an
    # explicit --deployment path, so it lives once, here, and is pointed at whichever source/
    # target world the operator names.
    "extract-context",
    # verify-chain — the seventh repo-root operator verb shim, wired 2026-07-22 during the
    # autoharn1 succession (ledger row 1942): extract-context's provenance block quotes
    # ./verify-chain output verbatim (consult §2.3) and reported it UNAVAILABLE because this
    # legacy deployment had every sibling shim (led/judge/pickup/audit/distance-to-clean/
    # migrate) but never this one. Same PICKUP_DEPLOYMENT wrapper pattern; the template
    # itself (bootstrap/templates/verify-chain.tmpl) is the direct-psql original, so no
    # legacy- variant exists to point at.
    "verify-chain",
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
    # orchlog — the changelog-for-a-restarting-orchestrator verb (ledger item
    # orchlog-changelog-verb, 2026-07-15), a standalone Python executable like attest-tags
    # (no DB deployment needed). Its data directory is registered below as "orchlog.d" -- see
    # orchlog.d/README.md for why the directory could not be named "orchlog" too (a plain
    # filesystem cannot hold a file and a directory of the same name in one parent).
    "orchlog",
    # asof-export — the ledger-wide as-of read + §11.10(b) inspection-copy export verb (ledger
    # item asof-export-inspection-copy, 2026-07-18), the seventh member of the standing
    # track-work.sh shim set (bootstrap/track-work.sh's own shim loop, extended by this same
    # commission) -- registered on landing, not left an unregistered breach for the next run.
    "asof-export",
    # otel-attest — the OTel model-attestation verb (ledger item otel-model-attestation),
    # landed without registration here; one of three pre-existing breaches flagged loudly by
    # the asof-export builder (2026-07-18) and fixed at the merge seam rather than left for
    # the next run (CLAUDE.md hazard-flagging duty).
    "otel-attest",
    # otel-watch — the v0 OTel model-provenance sentry watchdog (design/FABLE-OTEL-SENTRY-SPEC.md
    # §3, work item otel-watch-v0-build), registered on landing rather than left an unregistered
    # breach for the next run.
    "otel-watch",
    # vestigial_documentation/ANTHROPIC-FEEDBACK-2026-07-17-security-recommendation-incident.md moved into
    # vestigial_documentation/ by the doc-tree relocation (row 1620, 2026-07-18) as
    # IMPLEMENTED-LEGACY (a self-declared point-in-time correspondence record); deregistered
    # here, see VESTIGIAL-INDEX.md.
}
ROOT_DIRS = {
    ".claude", "bootstrap", "law", "judgment", "kernel", "stores", "instruments", "engine",
    "gates", "filing", "hooks", "drive", "seen-red", "design", "research", "runs", "ephemera",
    "provenance",
    # serving/ — the FastAPI ledger boundary service (design/FABLE-LEDGER-BOUNDARY-SERVICE-SPEC.md,
    # first landed at merge 9942950), never registered here at landing; third of the three
    # pre-existing breaches flagged by the asof-export builder (2026-07-18), fixed at the same
    # merge seam (CLAUDE.md hazard-flagging duty).
    "serving",
    # attestations/ — ADR-0017's A:B:C fresh-context audit-loop ledger
    # (attestations/doc-legibility-attestations.jsonl, gates/doc_attestation_presence.py),
    # landed 2026-07-11 but never added here; caught in passing while registering
    # user-guide/USER-WORK-STATUS-OFFERING.md's own two attestations (CLAUDE.md hazard-flagging duty).
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
    # docs/ DEREGISTERED (2026-07-18, doc-tree relocation, row 1620): its sole tenant,
    # PROJECT-OVERVIEW.md, moved to user-guide/PROJECT-OVERVIEW.md; docs/ is now empty and
    # untracked (git does not track empty directories), so the top-level allowlist walk never
    # sees it — no entry needed, kept out per the same reasoning as the panel/ note below.
    #
    # user-guide/ — the single-homed adopter/operator "book" the doc-tree relocation created
    # (work item doc-tree-reorg-user-guide, ledger row 1620, maintainer ask 2026-07-18;
    # adjudication row 1625), collecting the USER-GUIDE-class docs (recipes, FAQs, the
    # walkthrough, the operating card/handoff, JUDGE-READING, PROJECT-OVERVIEW, ...) that were
    # previously scattered across root/design//bootstrap//docs//engine/docs/. Registered on
    # landing, same as serving/ above (CLAUDE.md hazard-flagging duty).
    "user-guide",
    # panel/ DEREGISTERED (2026-07-15, TASK C, commission item 3): the PoC SPA that lived here
    # (panel/backend, panel/frontend, panel/seed) moved to its own repo, KodBena/autoharn-panel,
    # and is adopted back in as a git submodule at tools/autoharn-panel — no new top-level
    # registration needed since tools/ is already a registered ROOT_DIR above and a submodule's
    # gitlink entry sorts under it. panel/ itself is untracked now (removed from the index; any
    # leftover files on disk are not git-tracked and this gate only walks `git ls-files`).
    # orchlog.d/ — the notes directory for the ./orchlog verb (ledger item
    # orchlog-changelog-verb, 2026-07-15): one markdown note per commit a restarting
    # orchestrator would want to know about, plus its policy README.md. Named "orchlog.d"
    # rather than "orchlog" because the verb itself is the root file "orchlog" -- a
    # filesystem cannot hold both a file and a directory of the same name in one parent (see
    # orchlog.d/README.md's "Why the directory is named orchlog.d/" section for the full
    # reasoning). Registered on landing rather than left for the next census run.
    "orchlog.d",
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
# _fixture_env.py — the shared host-resolution helper every seen-red/<case>/run_fixtures.py
# imports (its own docstring: "lives in seen-red/ itself, one directory above every driver that
# imports it"); a genuine cross-fixture shared module, not a per-gate evidence dir, so it is the
# one legitimate loose file under seen-red/ — caught here (panel v2, WP-4) while this exact
# registry was already being edited to add "panel" above (CLAUDE.md hazard-flagging duty: a
# hazard within reach of the touch gets fixed, not routed around).
_SEEN_RED_LOOSE_OK = {"_fixture_env.py"}


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

    # (2b) seen-red/ forbids loose top-level files (only per-gate subdirs + the allowed shared set)
    for f in files:
        rest = f[len("seen-red/"):] if f.startswith("seen-red/") else None
        if rest is not None and "/" not in rest and rest not in _SEEN_RED_LOOSE_OK:
            breaches.append(f"PATTERN BREACH {f}: seen-red/ holds only per-gate subdirs "
                            f"(+ {sorted(_SEEN_RED_LOOSE_OK)}), no other loose files")

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
