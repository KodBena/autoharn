# HANDOFF (rewritten 2026-07-12 early morning, session e4410ef6 — fresh-context entry point)

Audience: orchestrator

This file orients the next orchestrating session. Fable — the maintainer's senior AI
authoring model, named throughout this project's law — retires within a day of this
revision; the succession posture below is therefore this document's most load-bearing
section. The file condenses and points; it does not duplicate. The
[SSOTs](GLOSSARY.md#ssot) (single sources of truth) it names outrank any summary in it,
and every claim below is re-observable — cite nothing from here without re-checking at
the source it names. It supersedes the prior HANDOFF wholesale (that revision survives
in git as commit f0718b8's ancestor state).

## Read in this order

0. `./pickup` — at this repository's ROOT. The repo tracks its own work in a standing
   Postgres ledger (closing the long-open question of how a project tracks its own work — the answer this repo's predecessor project omega prototyped; the closure record is design/USER-WORK-STATUS-OFFERING.md); the live open
   set, each item's full statement, and the RESOURCES section all come from there, never
   from this file.
1. ORCH-OPERATING-CARD.md — orientation in one page: the two-cwd model, vocabulary, the
   verbs, start/resume including the signed-commission start, the delta decision tree,
   the hooks map (reconciled against the 11-mechanism registry), the verification
   checklist.
2. CLAUDE.md — law pointers (five ADRs incl. 0017, all binding) + ORCHESTRATION. Read
   the named ADRs IN FULL before work that invokes them.
3. ORCH-CAPABILITIES.md — the operational truth: 30+ witnessed capability items.
4. BACKLOG.md, dated tail from "Two ratifications (maintainer, 2026-07-12 evening)"
   onward — the final Fable-era day's findings and dispositions.
5. USER-GUIDE.md — read once even as an orchestrator: it is the narrative spine an
   adopter follows, and it orders the USER- shelf.

## Where the project stands (2026-07-12, Fable's last day)

The documentation corpus is audience-split (MAINT-/ORCH-/USER- prefixes over design/ and
root, 46 documents; `tools/rename_doc.py` is the per-document rename primitive). The
maintainer's five decision-queue answers of 2026-07-11/12 are fully transcribed, each into its home artifact with the transcription acts in BACKLOG's dated entries of those days: both
ADR amendments are law with his proviso (the text binds, the mechanism assists);
ADR-0009 is re-instanced for autoharn; the research-ledger offering shipped — an "offering" is a one-command adoption any project can run, the genre USER-GUIDE.md's Adopt section orders — as `bootstrap/track-experiments.sh`, while applying the schema to his own standing research database remains his single pending command (`bootstrap/apply-research-ledger.sh`; tracker item research-ledger-apply);
perimeter/host-ops questions are permanently out of scope by his ruling; and his answer to the then-pending
review-gap scope-semantics ruling (a draft asking whether the kernel's second-pair-of-
eyes obligation binds a whole principal or one task; MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md)
rejected its framing outright and became the obligation-attachment vocabulary in
the registry spec.

The overnight yield (every item witnessed, attested, merged; BACKLOG's dated tail
carries each disposition):

- **Pillar 1 exists.** design/ORCH-SPEC-RESOURCE-REGISTRY.md (Fable-authored, attested)
  specifies the capability registry — three declaration tiers, the eliciting mechanism,
  mandated-tier countersigned evidence review, first-class ordering constraints, and
  planning as the explicitly-wrapped stretch appendix. STAGE 1 IS LIVE: `./pickup`
  shows a RESOURCES section, the preamble carries the eliciting line, and
  design/USER-BLESSED-TABLE-TEMPLATE.md holds the task-shape table and the
  `resource:`/`constraint:` grammars. Stage 2 (the ordering checker) is an open,
  Sonnet-executable tracker item; stages 3-4 wait on witnessed need and the
  maintainer's word respectively.
- **The preamble-ordering auditor is live and found real history.** Part 3 of
  design/ORCH-CONTEMPORANEITY-PART3-SPEC.md is implemented: an ASP program under
  engine/lp/ checking the twelve ordering obligations the governance preamble imposes
  (families F1-F12 in that spec's catalogue), marriage-grade — derived independently in
  ASP and SQL with the two required to agree — surfaced as `./audit --preamble` with
  exit 5 on any VIOLATED family. It ran retroactively over seven settled worlds and
  surfaced three genuine violations (run5 closed items before claims twice; run11's
  decomposition never cited its commission; run4's countersign preceded its window).
  The deductive-engine showcase is no longer prospective.
- **Worktree ledgering is mechanized.** Union merge drivers for the attestations jsonl
  and BACKLOG's dated sections are installed (one-time `git config` lines in
  bootstrap/QUICKSTART.md; bootstrap.sh installs them for fresh clones); the invocation
  journal (each world's `.claude/logs/invocations.jsonl`, hook-written per Bash call)
  carries the working directory for branch attribution; the `merge:` convention row and the
  merge-seam attestation rule live in ORCH-ABC-AUDIT-LOOP-RECIPE.md's integrator
  checklist. The drivers' first live merges resolved mechanically what two days of
  hand-regex kept fumbling.
- **The consumer shelf is complete for this era:** USER-GUIDE.md (walks install, adopt,
  operate, and audit in order; every command witnessed), USER-RETROSPECTIVE-RECIPE.md (the
  run-10/11 method with the ratchet codified and a reusable commission template),
  USER-CONFIGURATION.md, the offerings (track-work, track-experiments), and the GPG
  FAQ with deployment-local keyrings.

## The succession posture (what happens when Fable is gone)

- The succession drill PASSED, graded and ledgered (2026-07-12): Opus authored a real
  law-adjacent spec (design/ORCH-SPEC-DOC-ATTESTATION-2.md — version 2 of the
  attestation record format) under the CLAUDE.md succession rule's maximum
  ceremony, every ceremony component provably load-bearing. That format is now in
  routine service in the attestations ledger. Opus needs firm rails (evidence-pointer duties, scope bounds, named failure
  modes in the commission) and gets them from the standing prompt patterns in BACKLOG's
  commission records.
- Every remaining engineering item is Sonnet-executable from an attested spec: registry
  stage 2 (tracker item registry-stage2-ordering-checker); registry stage 3 — the
  `resource` ledger kind as kernel lineage step s27, the pre-ratified fail-safe class
  of change per CLAUDE.md's ORCHESTRATION — staged in
  design/ORCH-SPEC-RESOURCE-REGISTRY.md §8; the worktree memo's deferred first-class
  merge-event ledger kind (design/ORCH-WORKTREE-LEDGERING.md, on witnessed need); and
  the ordering auditor's residue (design/ORCH-CONTEMPORANEITY-PART3-SPEC.md's Status
  section). Nothing open requires Fable-class authoring.
- The maintainer's own acts, tracked as items: the research-ledger apply (one line) and
  key generation (USER-GPG-TRUST-LAYER-FAQ.md walks it; unlocks signed tags, SIGNED
  commissions, and the signed chain head that doubles as his session sign-off).

## Standing cautions (paid for; details in BACKLOG's tail)

- Synchronous B — the fresh-context reviewer role of ORCH-ABC-AUDIT-LOOP-RECIPE.md's
  audit loop — always, for attestation loops (the recipe now says so; orphaned
  background verdicts were twice-witnessed). The loop's two-round cap escalates to the
  orchestrator, who adjudicates by applying B's own repairs; the banked precedents are
  the escalated records in attestations/doc-legibility-attestations.jsonl.
- The freeze rule covers hooks/, bootstrap/templates/, and live-executed engine/ code
  while any wired session runs; worktree agents fast-forward their stale bases before
  working (three witnessed stale-base incidents; every agent self-corrected).
- Verify artifacts, never reports — including agents' summary messages (one witnessed
  says-clean-was-refused case) and your own prior claims.
- The maintainer reads refusals, not source; his decision queue takes ONLY load-bearing
  judgment questions (his calibration, on the record: trivia routed to him is a
  failure). Auditability outranks agent ergonomics; the action stream is the
  evidentiary basis and ~/.claude internals are diagnostics only.
- The contemporaneity audit's fact exporter (engine/contemp_edb.py) refuses ledger
  windows over ~24.8 days with a typed UnsafeWindowError; this repository's own
  standing work tracker crosses that bound around 2026-08-05 — per-window anchoring is
  the documented follow-up in that module's hazard docstring if the refusal starts
  firing.
