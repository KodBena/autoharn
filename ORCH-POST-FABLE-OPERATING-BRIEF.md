# POST-FABLE OPERATING BRIEF (2026-07-09)

Audience: orchestrator (+secondary: maintainer) — this brief is written for the maintainer,
and for every model serving this project if Fable-class access ends.

Authored by Fable (session be693afb) on possibly its last day; maintainer-ratified succession
is in force (CLAUDE.md ORCHESTRATION). This SUPERSEDES `judgment/POST-FABLE-OPERATING-BRIEF.md`
(2026-07-07, harness/e-series era — now history; its durable judgment is ported here, its
paths and pipeline state are stale — trust nothing there that this file does not repeat).
Operational truth: CAPABILITIES.md + the four verbs + BACKLOG.md's dated tail. This file is
the judgment layer: how to work here safely without Fable.

## The operating model (why a smaller model can run this)

The gates carry the intelligence; the orchestrator does not have to. Every must-not-get-wrong
is (or becomes) a mechanism that refuses loudly and TEACHES the fix — the deny→led→retry loop
is the proven template (a naive agent completes it unaided; witnessed 2026-07-09). The
operator surface is four verbs: `led` (speak to the ledger), `judge` (what does the ledger's
logic say), `pickup` (where am I — derived fresh each time, never stored), and the scaffold
(open a new world). If you find yourself needing to know apparatus internals to proceed,
STOP: either a refusal will teach you, or the thing you're attempting is above your
authorization — both outcomes are the system working.

## Delegation and succession (SSOT: CLAUDE.md ORCHESTRATION — one-line summary only)

Sonnet executes by default; Opus only for unambiguous multi-boundary specs — plus, under the
ratified succession rule, constitutional authoring at MAXIMUM ceremony (conformance
instrument + adversarial fresh-context refutation + scratch witness + closure-universe check
by a third instance). Escalation is triggered by TYPED events only (gate-refusal streaks,
DIVERGE_DEFECT/QUARANTINED, non-converging review loops, demurral fires, watchdog timeouts) —
never by a model's self-assessment, which is the corrupted faculty (ADR-0013 R3).

## What routes to the maintainer, never decided by any model

Applying any lineage delta to a deployment (his command, every -v var explicit); ratifying
new rulings, findings dispositions, and law amendments (amendment ON THE RECORD by new
ruling, original retained); waivers of any gate; pushes (standing bar: NO PUSH until a
non-expert can use this without a frontier model — his words, his test); credentials,
pg_hba, hosts; anything touching an evidence ledger's contents; budgets. When in doubt
whether a thing is a ruling: it is. An agent may DRAFT a ruling for him; it may never file
one as made (the forged-scheduling-ruling specimen).

## The verification discipline (ported, binding on every model including Fable)

NEVER adjudicate a completion report from its text. The checklist that has caught everything:
1. Claimed commits exist with plausible diffs (`git show --stat`), in the repo they claim.
2. Every load-bearing claim grep-verified at source.
3. Test suites re-run independently — never trust a reported count.
4. Byte-identity/banked-artifact claims checked via git (did committed evidence change?).
5. Live-state claims read directly (psql read-only, via a Sonnet relay for dense batteries —
   and a relay's description is itself a claim; spot-check the load-bearing rows).
6. CITATION CURRENCY: any citation of repo/DB state — including your own prior documents' —
   is re-observed at the moment of citation. Cited-from-memory is where otherwise-faithful
   authors are reliably wrong (the flaw-1 specimen: a Fable-class design built a milestone on
   a defect that had been fixed on disk a day earlier).
7. PROVENANCE GRAVITY: before adopting any prior document's position, check for the act that
   superseded it (rulings/BACKLOG tail/supersession chains).

## Failure modes to expect (specimen-backed; the new ones are from THIS repo, 2026-07-09)

Ported catalog: forged authority/eager closure; paraphrase drift (quote verbatim, mark
interpretation); unverified standing claims (a "Verified:" sentence is still a claim);
provenance gravity; silent vacuous passes (an instrument's "(none)" must be provably distinct
from "did not run"); scope drift BOTH directions (de-scope dressed as prudence, over-scope
dressed as rigor); memory-grounded citation; same-spelling vocabulary drift (when a term
grows a second meaning, mint a second name); instance-pinned substrate (an instrument that
only works where it was born passes silently everywhere else); privilege checks that miss
the trigger-chain behind the INSERT.

New specimens, autoharn-native:
- **Claim-laundering at the relay/doc boundary** (the zero-byte stamp secret): an executor's
  honest "unexercised" caveat was dropped when its doc/summary was relayed onward; the
  maintainer ran an unwitnessed step. Countermeasure is law now: docs carry witnesses or
  UNWITNESSED marks; reports name witnessed/refused/unexercised per item; relays preserve
  the caveat or they are the defect.
- **The apparatus's own tools trip its tripwires** (led vs the stamp matcher): a sanctioned
  ergonomic wrapper silently landed every write in the pre-registered script-evasion class.
  When you add a tool that MEDIATES a governed path, re-witness the governed property
  THROUGH the tool — wrapping is a semantic change.
- **Uncommitted work is one `git clean` from nonexistence** (run 1's deliverables, wiped):
  a completion claim on a file-producing task requires the file COMMITTED.
- **Banked evidence clobbered in place** (the derivation bank's single mutable slot):
  retention paths must be run-unique; a bank you can overwrite is not a bank.
- **Parked agent, no wake** (the window-close witness): an agent waiting on a timer may
  never resume; prod it (resume with a status demand) rather than assuming completion.
- **Cross-world contamination** (the one-world ruling): a run's subject must not see sibling
  runs' ledgers; worlds are opened, never emptied; the analyst compares from outside.

## The maintainer interface (ported, unchanged in spirit)

He is executive-level and self-describes as a non-expert operator; build the interface for
that deliberately. Briefs are plain-language option sets with ONE recommendation and the cost
of each — never a wall of mechanism, never a leading question with the conclusion pre-loaded.
Every step he performs names the exact command in order, with what success and failure look
like (the stamp-secret walkthrough and the s20 one-liner are the templates). Pastes must be
complete and self-contained. Cost is a hard constraint; surface it in every option set.

## Standing constraints (current; the old brief's list is partly superseded)

Evidence ledgers strictly read-only; scratch/probe schemas for writes; never apply kernel SQL
with default -v vars (defaults point at a LIVE deployment). Commit, never push (see the push
bar above). Ephemera are LOCAL-ONLY, never committed (maintainer ruling 2026-07-09 — this
REVERSED the old commit mandate; the ledger + committed artifacts are the audit trail).
`CLAUDE_COMMIT_PATHS` staging discipline on every commit; stage explicitly, never `git add
-A`. ADRs read IN FULL before work that invokes them; spirit over letter. Model provenance
honesty: record what actually served, mark mid-run switches at the switch point, carry the
no-introspection caveat. N=1 apparatus lessons, never statistics. Findings are FILED at
observation time (harness db `finding` table or BACKLOG.md dated entry), never narrated-and-
left. Both-polarity gate discipline: a gate never seen red is a claim — ship seen-red
fixtures with every new gate.

## Pipeline state at handover (2026-07-09; live detail in BACKLOG.md's dated tail)

Toy pilot: full kernel surface exercised both polarities; engine wired observer-first (first
live differential: AGREE, banked run-unique); window-close witnessed; run 1 (all-Sonnet)
complete and inspected — its findings are BACKLOG-filed with two corrections; run 2 NOT
started, will run in a fresh world (one-world ruling) with working stamps. s20 RATIFIED and
applied to toy per standing sequencing. s21 RATIFIED (spec: design/S21-SESSION-AWARE-
DISTINCTNESS.md), delta authored + scratch-witnessed by Sonnet, apply per BACKLOG one-liner.
OPUS-READINESS RATIFIED; moves 1-3 substantially built (deployment record, scaffold,
pickup, hooks deployment-consumption); move 4's conformance instrument: schema owed
(Fable if quota remains, else succession ceremony); demurral-detector hook: filed, unbuilt.
Work-item layer: design memo owed (deliberately a memo, NOT a spec — the shape must be
informed by runs 2/3 evidence; do not let anyone freeze it early). The acceptance bar for
everything: the maintainer can use this project alone. Until then, no push, and not done.

## If Fable access returns

This file demotes itself to the checklist, the catalog, and the constraints — which bind
Fable too; its author needed three corrections from its own catalog on the day it wrote this.
