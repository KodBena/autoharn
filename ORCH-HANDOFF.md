# HANDOFF (rewritten 2026-07-13, session 3c50e030 — fresh-context entry point)

Audience: orchestrator

This file orients the next orchestrating session. It condenses and points; it does not
duplicate. The [SSOTs](GLOSSARY.md#ssot) (single sources of truth) it names outrank any
summary in it, and every claim below is re-observable — cite nothing from here without
re-checking at the source it names. It supersedes the prior HANDOFF wholesale (that
revision survives in git as commit 0704a4e). It was written because context length, not
open work, ended the prior session: the fresh-session + pickup path is this project's own
resumption doctrine, exercised on itself.

## Read in this order

0. `./pickup` — at this repository's ROOT. The repo tracks its own work in a standing
   Postgres ledger; the live open set, each item's full statement, the RESOURCES,
   ESTIMATES, TAXONOMIES, and MAINTAINER-REVIEW-QUEUE sections all come from there,
   never from this file.
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

## Where the project stands (2026-07-13)

The readiness-probe program CLOSED: probe 2 (frozen at stamp 0704a4e) replicated the
first probe's results cleanly, and probe 3 (stamp d4aac05) scored 17/19 with both
residual misses traced to documentation defects and fixed the same day (the
mandated-tier reconciliation in design/ORCH-SPEC-RESOURCE-ACCOUNTING.md §4.1; a stale
capability item repaired in 9c86d20). The instrument stays outside the repo on purpose (a greppable key contaminates
the probe); its hashes and protocol are ledgered under tracker item
`opus-readiness-probe`.

A SECOND LIVE DEPLOYMENT runs at the maintainer's `~/ent`: a code-health audit of the
picom compositor (C/GLSL), seeded with structural rows only (taxonomy, interface, and
environment-constraint declarations — no findings, no interpretive prose) and a
verbatim commission, orchestrated by the maintainer with Sonnet. Two standing consequences:

- **Merge-gate while ent runs:** nothing merges to `next` that touches
  bootstrap/templates/, hooks/, or gates imported by live verbs. proposals/ (registered,
  transitional) stages template patches until a session gap.
- **Observatory:** observatory/ent/ holds recurring read-only evaluation cycles
  (001–003 so far, on the maintainer's word each time). From cycle 003 the reports carry
  a METHOD CANDIDATES section — the maintainer's method-harvesting posture, ledgered:
  observatory cycles and merge-seam reviews (a "seam" here and throughout is the
  independent re-witnessing every builder branch receives at merge time, before it
  lands on `next`) watch for durably-shaped workflows worth serving
  into the recipes corpus, and we may not know in advance what we're looking for, so
  odd-but-recurring shapes get flagged even when they can't yet be classified.

Both auxiliary ledgers are applied and live (each by the maintainer's own
typed-confirmation act, witnessed): the research ledger (stores/001) and the harness-failure ledger
(stores/008, schema `harness_failure`, collection default-on; 12 records at handoff —
see design/ORCH-HARNESS-FAILURE-LEDGER.md). The executive review queue is live: the
`review:`/`review-done:` grammars feed a ranked MAINTAINER-REVIEW-QUEUE section in
`./pickup`, so only load-bearing judgment questions reach the maintainer.

pgAudit is at the provision-inert stage (design/ORCH-PGAUDIT-EXPLORATION.md): the
package install, preload entry, and one restart are the maintainer's acts; every
configuration decision is deferred until he is present for it. Do not advance this
without him.

Exploration/design records landed this session, all attested, none carrying a mandate:
knowledge-representation titration (design/ORCH-KR-TITRATION-EXPLORATION.md),
compound-nominal detection round-trip (design/ORCH-COMPOUND-NOMINAL-DETECTION.md and
-2.md — an Opus infeasibility verdict constructively rebutted with a working detector),
the typed-table constructor experiment (design/ORCH-TYPED-TABLE-EXPERIMENT.md), and the
registry completeness audit (design/ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md, a 20-family
matrix with proposals P1–P7 queued for the maintainer).

The ADR-portability refactor stands at end of Phase 1
(design/MAINT-ADR-PORTABILITY-SPEC.md): contradictions adjudicated (defaults stand plus
three overrides), with one provenance correction on record — the §7a "Metz disagreement"
statement was Opus-authored and only lazily approved at the time; it was never the
maintainer's own position. Final ratification and the Phase-2 go (dedicated
`adr-portability` branch, ~14 Sonnet work packages) sit in the maintainer's queue.

## Immediately actionable (fresh session, in this order)

1. **Re-dispatch two claimed items whose builders never ran** (the prior session hit
   its context ceiling between claim and dispatch; an orchestrator note (`./led show
   492`) records this): `served-workflow-gotchas` (statement at row 483,
   verbatim — a Workflow-script gotchas recipe entry; three independent witnesses of the
   args-parsing class) and `cosign-convention-crosscheck` (row 486 — adjudicate ent
   cycle-003's iterate-to-approval co-sign convention against ADR-0014 and the A:B:C
   recipe: already-covered, genuinely-new, or divergent — and if divergent, surface the
   divergence for the maintainer, never silently harmonize). Both are
   Sonnet-executable from their ledgered statements alone.
2. **Four parked branches await one merge pass at an ent session gap** (each gets a
   fresh seam review first; builders' worktree bases are stale by default — verify the
   base before trusting any corpus claim): `3305a5c` (three trivial doc/comment
   corrections), `a84d69c` (pickup CANNOT-HYDRATE, exit 5), `0cd0a6f` (stop-breaker
   strict-subset inherits instead of resetting), `f382b63` (watchdog liveness harness —
   a safety feature by the maintainer's explicit framing, never cost-policing; all
   thresholds end-user configurable).
3. proposals/ template patches apply at the same gap, behind the same seam discipline.

Everything else waits on the maintainer's queue: ADR-portability ratification (§7a
provenance question included), registry P1–P7, detector adoption (blocks the
detector-firing-telemetry item), typed-table adoption, the trust-domain wording
findings (three, disclosed at the README legibility sweep's merge, commit ae3eeb6), and
the pgAudit package step.

## Standing cautions (paid for; each was witnessed, not theorized)

- **Commissions verbatim, never paraphrased** — a compressed brief narrowed a
  deployment's scope, and the deployment session went straight at the headline defect
  single-handedly instead of executing the commissioned full audit (censure on record).
  State the scope before showing specimens. Never offer a free, narrow path alongside a
  gated, broad one — that pairing is what invited the narrowing.
- **Reviewer briefing is two agents, never one** — fusing "verify these fixes" with
  "sweep fresh" front-loads the reviewer and blinds the sweep (maintainer-caught, served
  to deployments the same day). Fresh fork per round; never resume a reviewer instance.
  Run B synchronously, always; give B the absolute path under the builder's worktree.
- **Delegation lane:** Sonnet executes by default; Opus only for unambiguous
  multi-boundary specs, never where its overconfidence can hurt. The orchestrator's own
  data-plane surface is the operator verbs, full stop — anything that reaches a database
  directly, reads included, is delegated whole, with intent-only prompts: state WHAT to
  record and point at the schema's own docs; the data design is wholly the subagent's.
- **Workflow scripts:** args arrive as JSON values, not strings; pin the model on every
  agent() call; no wall-clock/randomness calls (breaks resume); a stall and a crash
  present identically from outside — check for the failure notification before
  diagnosing. (These are the served-workflow-gotchas item's content; serving them is
  actionable item 1.)
- **Merge from the MAIN checkout** — a shell cwd left inside a worktree yields "Already
  up to date" against the branch itself (a recurring class, witnessed again this
  session). Never `git add -A` while agent worktrees exist.
- The A:B:C attestation loop's two-round cap escalates
  (design/ORCH-ABC-AUDIT-LOOP-RECIPE.md); apply B's round-2 repairs verbatim with an honest
  adjudication record — UNLESS a repair would encode a falsehood; then fix the
  underlying truth and disclose the divergence.
- Verify artifacts, never reports — including agents' summaries and your own prior
  claims; the seam re-runs every load-bearing fixture before merging.
- The maintainer reads refusals, not source; his decision queue takes ONLY load-bearing
  judgment questions — trivia is fixed autonomously, never queued. Auditability outranks
  agent ergonomics; the hooks-recorded action stream is the evidentiary basis
  (harness-internal files are diagnostics only); token/cost figures are
  diagnostic-grade permanently and estimates exist for hazard detection, never
  economizing.
- Key generation and everything downstream of it (signed tags, chain-head sign-off) is
  DEFERRED by standing maintainer ruling until every other concern is banked — never
  re-raise it as a recommendation. The trust-domain decision
  ([README.md § Trust domain](README.md#trust-domain)) is likewise his, at leisure.
- The contemporaneity fact exporter refuses ledger windows over ~24.8 days; this
  repository's own tracker crosses that bound around 2026-08-05 — per-window anchoring
  is the documented follow-up in engine/contemp_edb.py's hazard docstring.
