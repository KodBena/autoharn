# HANDOFF (rewritten 2026-07-12 evening, session e4410ef6 — fresh-context entry point)

Audience: orchestrator

This file orients the next orchestrating session. It condenses and points; it does not
duplicate. The [SSOTs](GLOSSARY.md#ssot) (single sources of truth) it names outrank any
summary in it, and every claim below is re-observable — cite nothing from here without
re-checking at the source it names. It supersedes the prior HANDOFF wholesale (that
revision survives in git as commit 22895f0). It was written because context length, not
open work, ended the prior session: the fresh-session + pickup path is this project's own
resumption doctrine, exercised on itself.

## Read in this order

0. `./pickup` — at this repository's ROOT. The repo tracks its own work in a standing
   Postgres ledger; the live open set, each item's full statement, the RESOURCES,
   ESTIMATES, and TAXONOMIES sections all come from there, never from this file.
1. ORCH-OPERATING-CARD.md — orientation in one page: the two-cwd model, vocabulary, the
   verbs, start/resume including the signed-commission start, the delta decision tree,
   the hooks map, the verification checklist.
2. CLAUDE.md — law pointers (five ADRs incl. 0017, all binding) + ORCHESTRATION. Read
   the named ADRs IN FULL before work that invokes them.
3. ORCH-CAPABILITIES.md — the operational truth: 35 witnessed capability items, each
   carrying real output or an honest UNWITNESSED mark.
4. The work tracker itself — `./led --recent` for the latest rows, `./led show <id>`
   for any one in full. BACKLOG.md is a retired pointer stub (maintainer ruling, tracker
   row 137); the frozen dated record every historical "BACKLOG entry" citation points
   into is read with `git show d6f64ee:BACKLOG.md`.
5. USER-GUIDE.md — the adopter's narrative spine; it orders the USER- shelf.
   design/USER-RECIPES-FAQ.md is the intent-keyed index over that shelf ("can I do X?"
   → the one page where the truth lives), attested against the live ledger.

## Where the project stands (2026-07-12 evening)

Run 12 completed as the first fully-ceremonied run: a SIGNED commission verified live
(first VERIFIED on record), a live resource declaration, six reviewer dispatches, ended
review-clean. Its defects became permanent mechanisms the same day: malformed
`resource:` intake now refuses loudly at the boundary; content-free review discharge is
audited (`./audit --review-gap`, FLAGGED-never-VIOLATED); decomposition review is a
write-time blocker (`decomposition_review` mechanism, observe default).

The maintainer's re-litigation commission ("re-judge adoption modulo the dearth of
adoption evidence") ran as a five-lens panel and is synthesized in
design/MAINT-RELITIGATION-SYNTHESIS.md (attested): 3–2 adoptable-in-principle, his bias
suspicion substantially confirmed, FAA's dissent recorded, one decision-shaped wall
standing (single trust domain — his, at leisure). Five Fable-authored specs shipped and
were attested the same day: resource accounting, decomposition policy, task taxonomy
(his boundary-discipline ask, polymorphic in taxonomy), the A:B:C offering, and the
scope-semantics ruling that closed Q1.

Two build waves then landed, every item claimed → estimated → built by a Sonnet
worktree builder → independently re-witnessed at the merge seam → closed with witness:

- **panel-cheap-fixes** — FAQ register fix ("is consistent with", CONTESTED→SIGNED
  rule), money-figures-diagnostic disclosure in USER docs, commit-hash-in-PROVENANCE at
  scaffold (DIRTY/UNAVAILABLE honesty), and the s26 deletion fixture, which FOUND a real
  limit: tail-row deletion is invisible to the chain alone (interior deletion breaks it;
  witnessed both ways twice). Tracker item `s26-tail-deletion-witness` holds the
  designed always-on fix.
- **apparatus-flip-witnessing** — every apparatus.json mutation journals a typed event
  (watcher deliberately outside its own switchboard); `verify-chain --head` carries
  `apparatus_hash` (manual two-head comparison, named precisely). CAPABILITIES item 32.
- **cost-estimation-retro** — the `estimate:` grammar is LIVE in the tracker verbs
  (six fields, refuse-before-write), `./pickup` renders ESTIMATES, the retrospective
  recipe gained estimate-vs-actual with the grade split stated (witnessed counts
  evidentiary once accounting stages B/D ship; tokens diagnostic-grade permanently).
  NEVER for policing costs — the maintainer's invariant is in the refusal text itself.
- **taxonomy-stage-a** — `taxon:`/`interface:` declarations live, TAXONOMIES in pickup,
  the omega licensing specimen worked in design/USER-TAXONOMY-DECLARATION.md.
  Stages B–D (audit, gate, task-policy wiring) are spec'd, unbuilt. Item 33.
- **accounting-stage-a** — the `forbidden:` TIER (MUST-NOT completing the deontic
  register); declaration + display only, enforcement is Stage C, unbuilt. Item 34.
- **abc-loop-offering** — the A:B:C loop offered to deployments: `./attest-doc` (the
  sixth in-project shim; the scaffold remains the seventh verb per
  ORCH-OPERATING-CARD.md/USER-GUIDE.md), deployment-local attestations ledger,
  distance-to-clean DOC-ATTESTATION section
  behind the `doc_attestation` apparatus switch (default off), adopter walkthrough
  design/USER-DOC-AUDIT-LOOP.md. Item 35.

Estimates were ledgered for wave 2 before dispatch and reconciled at close — first
calibration lesson, on the ledger: the 1M token-OOM denomination overshot all three
times; estimate 100K–1M boundary cases as 100K.

## The succession posture (what happens when Fable is gone)

- The succession drill PASSED, graded and ledgered (2026-07-12 morning): Opus authored
  design/ORCH-SPEC-DOC-ATTESTATION-2.md under the CLAUDE.md succession rule's maximum
  ceremony; that format is in routine service. Opus needs firm rails (evidence-pointer
  duties, scope bounds, named failure modes in the commission).
- A readiness PROBE is armed, awaiting the maintainer: a questionnaire of questions the
  maintainer actually asked Fable (capabilities / use-guidance / refusal-traps), graded
  as a repo-legibility audit — each wrong answer becomes a tracker item against the doc
  that should have carried it. The instrument lives OUTSIDE the repo (deliberately: a
  greppable key contaminates the probe) at ~/opus-readiness-questionnaire.md; its sha256
  and protocol amendments are ledgered (tracker item `opus-readiness-probe`). The
  maintainer chose to reference the evaluation to a git commit stamp; the stamp is the
  commit this file lands in, ledgered at close.
- Every open engineering item is Sonnet-executable from an attested spec — the open set
  lives in `./pickup`, not here; its current flavor: the tail-deletion witness,
  work-tree estimate rollups, a deliberate glossary sweep, registry stage 2, and the
  spec'd stages (accounting B–D, taxonomy B–D, decomposition-policy stages). Nothing
  open requires Fable-class authoring.
- The maintainer's own acts, tracked as items: key generation (hardware token; unlocks
  signed tags, SIGNED commissions, chain-head sign-off), the research-ledger apply (one
  line, armed), running the readiness probe, and the standing trust-domain decision
  (second key-holder or written acceptance — Tier-3, at leisure, now confirmed by five
  independent lenses as THE wall).

## Standing cautions (paid for today or before; each was witnessed, not theorized)

- Synchronous B, always, for attestation loops — background Bs' verdicts were misrouted
  to the orchestrator twice-witnessed (a type label is not an address), and one
  background-resumed B reviewed STALE content. Give B the absolute path under the
  builder's worktree, or it reads the main checkout while the builder edits the copy.
- The loop's two-round cap escalates; the ratified pattern is applying B's round-2
  repairs verbatim with an honest adjudication record — UNLESS a repair would encode a
  falsehood (twice-witnessed: a stale "pending merge" claim, a retired-BACKLOG link);
  then fix the underlying truth and disclose the divergence in the record.
- Merge from the MAIN checkout — a shell cwd left inside a worktree yields "Already up
  to date" against the branch itself (thrice-witnessed class). Never `git add -A` while
  agent worktrees exist (one witnessed embedded-gitlink commit, amended out;
  .claude/worktrees/ is now gitignored).
- One ORCH-CAPABILITIES.md writer per wave; sibling builders return proposed item text
  and the orchestrator lands the batch at the seam behind one scoped B.
- The freeze rule covers hooks/, bootstrap/templates/, and live-executed engine/ code
  while any wired session runs (check process cwds, not assumptions); worktree agents
  fast-forward their stale bases first (three witnessed incidents).
- Verify artifacts, never reports — including agents' summaries and your own prior
  claims; the seam re-runs every load-bearing fixture before merging.
- The maintainer reads refusals, not source; his decision queue takes ONLY load-bearing
  judgment questions. Auditability outranks agent ergonomics; the action stream is the
  evidentiary basis; token/cost figures are diagnostic-grade permanently.
- The contemporaneity fact exporter refuses ledger windows over ~24.8 days; this
  repository's own tracker crosses that bound around 2026-08-05 — per-window anchoring
  is the documented follow-up in engine/contemp_edb.py's hazard docstring.
