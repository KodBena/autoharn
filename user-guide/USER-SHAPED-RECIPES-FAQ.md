# Shaped recipes — mechanical patterns with a validated formal specimen

<!-- doc-attest-exempt: doc-tree relocation mechanical edit (work item doc-tree-reorg-user-guide, ledger row 1620, 2026-07-18) -- relative link path(s) repointed to a sibling file's new location after a git-mv relocation elsewhere in the tree; no prose rewrite, same disposition as the v1.1.2 release-cut's own markers (commit 543a389). Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->


This page is for the same operator [USER-RECIPES-FAQ.md](USER-RECIPES-FAQ.md) is written for —
someone who followed a link from a recipe's one-sentence stub there, or who wants to see, in
concrete terms, what one of that page's recipes looks like once its control flow is written down
formally rather than only in prose. It is the sibling `USER-RECIPES-FAQ.md` points at whenever a
recipe there turns out to have a **mechanical, gainfully shaped** control flow — enumerable phases
in a defined order, typed participant roles, and a stated termination or convergence condition —
that this project's v0 declared-pipeline grammar (`design/workflows/*.toml`, validated by
`tools/workflow_check.py`, documented in full at [design/workflows/README.md](../design/workflows/README.md))
can actually express. Selection is governed by
[design/FABLE-SHAPED-RECIPES-EXPLORATION-SPEC.md](../design/FABLE-SHAPED-RECIPES-EXPLORATION-SPEC.md)
section 2's three criteria — algorithmic shape, gainful (the schema can express the control flow
without dropping a load-bearing constraint), and not judgment-shaped (a recipe whose essence is
human/orchestrator judgment stays prose, never reduced to a boolean field) — applied to every
recipe in `USER-RECIPES-FAQ.md`; the builder's own enumeration and per-recipe verdict live in that
work item's closing report (ledger work item `shaped-recipes-factoring`), not repeated here.

**This page is not a language-design exercise.** v0's grammar already exists and is treated here
as authoritative; where a recipe's load-bearing constraint has no home in the four fields
(`phases`, `roles`, `convergence`, `landing_zones`), the recipe is NOT factored and the gap is
filed against `pipeline-dsl-exploration` instead of inventing a field on the spot. **Executing**
these TOML shapes is out of scope too — the DSL stays declarative-and-validated only at this
stage; nothing here runs a workflow, it only declares its shape well-formedly enough for
`tools/workflow_check.py` to check.

## Validation as witness

Every `design/workflows/<recipe>.toml` on this page passes `tools/workflow_check.py` — WITNESSED,
this build, run against all three files transcribed for this page in one invocation:

```sh
$ python3 tools/workflow_check.py design/workflows/faq-abc-fixpoint-loop.toml \
    design/workflows/faq-doc-then-fix-sequencing.toml \
    design/workflows/faq-bookkeeping-close-pairing.toml
```
```
design/workflows/faq-abc-fixpoint-loop.toml: OK -- 3 phase(s), well-formed v0 workflow declaration.
design/workflows/faq-doc-then-fix-sequencing.toml: OK -- 3 phase(s), well-formed v0 workflow declaration.
design/workflows/faq-bookkeeping-close-pairing.toml: OK -- 4 phase(s), well-formed v0 workflow declaration.
```
(exit 0). `tools/workflow_check.py` has no repo gate wiring yet (a separately-filed, already-known
gap — the exploration spec's section 3 names it explicitly and scopes building that wiring out of
this task); this manual run is the witness this page relies on.

## The A:B:C fresh-context fix-point loop

*(First factored specimen, per the exploration spec's own mandate — the canonical member of this
page's selection criteria.)*

**Plain words.** When you want an agent-driven loop to keep improving something (a document, a
diff, a defect list) until nothing new is found, three roles compose: an author drafts or updates
the artifact, a genuinely fresh reviewer agent — never one resumed across rounds — checks it each
round, and a driving script adjudicates whether the loop has converged (K consecutive dry rounds)
or must escalate because a hard round cap was hit first. Reach for this whenever you are tempted
to let one long-lived agent "just keep going until it's happy" — the shape below is why that
temptation is a known failure mode, not a shortcut.

**The shape** (`design/workflows/faq-abc-fixpoint-loop.toml`):

```toml
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T15:27:25Z
#   last-change: 2026-07-18T15:54:24Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

# Transcribed from design/USER-RECIPES-FAQ.md, "Workflow patterns" section, first entry
# ("I want a workflow to iterate until clean -- can an agent spawn sub-agents and loop on its own
# output until a defect list comes up empty?"), the FAQ's own generalized description of this
# project's two-role fresh-context fix-point loop (A:B:C -- author, fresh-context reviewer,
# adjudicator/countersign; the same shape ORCH-ABC-AUDIT-LOOP-RECIPE.md governs in full and this
# very build task's own STEP 3 exercises). Selected as the FIRST factored specimen per
# design/FABLE-SHAPED-RECIPES-EXPLORATION-SPEC.md section 2 ("the A:B:C loop is the canonical
# member and MUST be the first factored specimen").
#
# THIS SPECIMEN DOES NOT FIT v0'S GRAMMAR CLEANLY, same class of gap Specimen C already recorded
# (design/workflows/panel-consult-cycle-template.toml, design/workflows/README.md "Known misfits",
# the entry headed "Specimen C's compliance-review/countersign phase is a bounded retry LOOP,
# which v0 cannot express as a mechanism."). The loop's own retry mechanics -- keep dispatching
# fresh-context rounds until K consecutive
# rounds report zero new findings ("loop-until-dry"), backstopped by a hard round cap (this
# project's own two-round cap) -- are a real loop construct the exploration document's "Not a
# workflow engine" clause rules out of v0 ("No conditionals, no loops, no expressions"). What is
# transcribed below is only the phase/role/convergence/landing-zone SHAPE the loop converges
# toward or escalates from -- never the loop's own dry-count arithmetic or round-cap bookkeeping,
# which stay ordinary deterministic driving-script code, exactly as Specimen C's own header
# documents for its structurally identical compliance-review/countersign loop.

[[phases]]
name = "author-draft"
depends_on = []

[[phases]]
name = "fresh-context-review"
depends_on = ["author-draft"]

[[phases]]
name = "adjudicate"
depends_on = ["fresh-context-review"]

[roles.author-draft]
authors = "the author role for whatever artifact the loop is converging (a document, a diff, a defect list) -- model tier is not fixed by the FAQ's own generalized description, unlike the panel's Specimen C, which names sonnet for every role"
implements = "same as authors -- the author phase is a single dispatch producing or updating the artifact under iteration"

[roles.fresh-context-review]
implements = "a genuinely fresh agent invocation every round, never one long-lived agent resumed across rounds -- the FAQ's own load-bearing caveat, caught failing in practice on 2026-07-13 in this project's own A:B:C loop (ORCH-ABC-AUDIT-LOOP-RECIPE.md's round-2 discipline): a resumed reviewer repeated its first round's verdict verbatim against on-disk content that had since changed underneath it"
reviews = "same agent invocation examines the current artifact or defect-list state and reports what remains to fix, or that nothing new was found this round"

[roles.adjudicate]
authors = "the driving workflow script's own deterministic control flow (an ordinary while loop wrapping repeated agent invocations, per the FAQ's own words) -- explicitly NOT itself a DSL-declared phase's mechanics, only the fact that adjudication happens is declared here"
implements = "same -- the script decides, each round, whether to re-dispatch author-draft/fresh-context-review for another round or to stop"

[convergence.author-draft]
done = "the artifact is drafted or updated for this round, ready for fresh-context review"
escalation_event = "none typed for this phase alone -- an author-draft failure is an ordinary dispatch failure, not a loop-specific escalation; the loop's own escalation is declared on the adjudicate phase below"

[convergence.fresh-context-review]
done = "the round's fresh-context review reports either zero new findings (a 'dry' round, per the FAQ's loop-until-dry criterion) or a concrete list of what still needs fixing"
escalation_event = "none typed for this phase alone -- convergence across rounds is judged by the adjudicate phase below, which is where the loop's own hard-cap escalation is declared; a single round's review output is never itself an escalation"

[convergence.adjudicate]
done = "K consecutive dry rounds are observed (loop-until-dry, the same criterion design/ORCH-AGENTIC-PATTERNS.md section 3 and this project's own A:B:C loop both use), reached strictly before the hard round-cap guard fires"
escalation_event = "non-converging-review-loop -- the hard budget guard (a round cap, alongside the dry-count guard) is reached without K consecutive dry rounds; this is CLAUDE.md's own named escalation trigger ('gate-refusal streaks, DIVERGE_DEFECT/QUARANTINED... non-converging review loops, never on self-assessment'), routed to the orchestrator to adjudicate rather than looping further"

[landing_zones.author-draft]
zone = "the artifact under iteration itself (a repo file, a worktree diff, a ledger row's own content) -- the FAQ names no single fixed location, since this loop shape is generalized across many concrete artifacts; the concrete workflow instantiating this shape must name its own landing zone per artifact"

[landing_zones.fresh-context-review]
zone = "each round's findings, recorded in that round's own report/transcript to the driving script -- the FAQ's own worked instance of this shape, ORCH-ABC-AUDIT-LOOP-RECIPE.md's B-round reviews, lands these in attestations/doc-legibility-attestations.jsonl when the artifact under review is a document; other instantiations of this general shape may land findings elsewhere, which is why this field stays this general rather than naming one fixed path"

[landing_zones.adjudicate]
zone = "the ledger -- the loop's final disposition (converged clean, or escalated to the orchestrator) is the kind of act this project records as an ordinary ledger row (a decision row, or a review row where the artifact is itself ledger-governed)"
```

**The prose recipe** (moved from `USER-RECIPES-FAQ.md`'s "Workflow patterns" section, content
preserving — only this lead-in sentence and the cross-reference below are new):

> **I want a workflow to iterate until clean — can an agent spawn sub-agents and loop on its own
> output until a defect list comes up empty?**
> Yes, natively, and both halves of that question have a plain answer. The looping half: a
> "fix-point" here means a script keeps calling an agent, feeding it the artifact or defect
> list as it currently stands, until a round finds nothing new to fix — and that loop lives in
> the workflow **script's own deterministic control flow** (an ordinary `while` loop wrapping
> repeated agent invocations — whether that is the `Agent` tool from an orchestrating session
> or a standalone driver script built on the Claude Agent SDK), never in any one agent's own
> sense that it is "done." Terminate on **loop-until-dry**: keep looping until K *consecutive*
> rounds each report zero new findings, not just one empty round — a defect population of
> unknown size can have a long tail a single-round counter misses. (This project uses the
> identical criterion in its own fix-point loops:
> [design/ORCH-AGENTIC-PATTERNS.md](../vestigial_documentation/design/ORCH-AGENTIC-PATTERNS.md) §3's "adversary files zero new
> rows for K consecutive rounds", and the two-role audit loop below.) The spawning half: yes,
> an agent your workflow dispatches can itself dispatch further sub-agents — nesting is not
> disabled — with a fuller, more capable agent type (e.g. `general-purpose`) available to use
> where the workflow's own default agent type is a leaner, narrower one.
>
> The load-bearing caveat, stated because it was caught failing in practice: **each round of
> the loop must spawn a genuinely fresh agent, never resume one long-lived agent across
> rounds.** An agent that carries its own prior round's context into the next round is not
> actually re-examining the current state with open eyes — it already committed to a verdict
> in an earlier turn, and tends to re-assert that verdict even when the bytes in front of it
> have since changed underneath it. This is not a hypothetical risk: on 2026-07-13, in this
> project's own two-role fix-point loop (the A:B:C fresh-context documentation-review loop,
> [ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)'s round-2 discipline), a
> reviewer agent resumed via a follow-up message — rather than spawned fresh — repeated its
> first round's verdict *verbatim* against on-disk content that directly contradicted it. Spawn
> round N+1 as a brand-new agent invocation with no memory of round N, every round, no
> exceptions.
>
> Termination discipline is the other half worth naming up front, not discovering by billing
> surprise: a dry-count guard (K consecutive empty rounds) belongs alongside a hard budget
> guard (a round cap, a cost or token ceiling) — a workflow script is ordinary deterministic
> code, so a fix-point loop with a broken or too-loose termination condition runs to whatever
> cap you built in, burning real, billed tokens the whole way there; nothing backstops a
> runaway loop before that cap except the cap itself. No single page owns this pattern end to
> end yet; [design/ORCH-AGENTIC-PATTERNS.md](../vestigial_documentation/design/ORCH-AGENTIC-PATTERNS.md) works out the
> loop-until-dry criterion in more depth, and
> [ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) is a complete worked example of
> exactly this shape — two agent roles, fresh-fork-per-round, a two-round cap, and a named
> escalation path for when the loop does not converge.

**The contrast note.** The TOML makes the loop's three-role skeleton (author, fresh-context
reviewer, adjudicator) and its escalation destination checkable well-formedness at a glance — a
reader who has never seen this project's own two-role loop can see the shape without reading
paragraphs of prose. What it cannot capture, by v0's own explicit design ("no conditionals, no
loops, no expressions"), is the loop's own retry arithmetic: the loop-until-dry K-consecutive-dry
criterion, the hard round-cap number, and the fresh-context-per-round discipline's own dated
failure specimen (the resumed reviewer that repeated a stale verdict) all stay prose-only, because
declaring them as fields would either be a fifth speculative field (banned) or a lie dressed as a
schema (a boolean `converged` field could never honestly carry "K consecutive"). The prose is also
the only place the *reason* fresh-context-per-round matters lives — the TOML states the rule, the
prose carries the incident that taught it.

## The doc-then-fix ordering proof

**Plain words.** When you need to prove, to a reader who was never in the room, that documentation
genuinely landed *before* a fix that claims to follow it — rather than trusting either agent's
narrative about which came first — split the work into three separately-dispatched acts and let
the ledger's own append-only, monotonically-issued row ids do the proving. Reach for this whenever
"prove the order, not just assert it" matters more than the extra dispatch it costs.

**The shape** (`design/workflows/faq-doc-then-fix-sequencing.toml`):

```toml
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T15:27:43Z
#   last-change: 2026-07-18T15:27:43Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

# Transcribed from design/USER-RECIPES-FAQ.md, "Workflow patterns" section, entry "How do I
# prove two phases ran in the right order, instead of trusting an agent's say-so?" -- a real
# pattern this project's own record already carries (autoharn-panel ledger rows 401, 415, 1144,
# named there only as history; carried upstream via decision row 1295, this project's own record
# of the pattern). The pattern splits work into a document-only dispatch, an orchestrator-authored
# ledger row citing what that dispatch produced, and a fix-only dispatch created only after that
# citation row lands -- letting the ledger's append-only, monotonically-issued row ids do the
# proving instead of either agent's own narrative about which one went first.
#
# NO MISFIT recorded for this specimen -- unlike Specimens C and the sibling faq-abc-fixpoint-loop
# specimen, this pattern has no loop, no scheduling, and no field the v0 grammar lacks a home for;
# it is a strict three-phase depends_on chain, which is exactly the shape v0's four fields already
# express. The one thing that does NOT belong in the TOML is the recipe's own honest epistemic
# limit (order-proof is not content-proof) -- that caveat is not a control-flow constraint the
# grammar was ever meant to carry, so it stays prose-only; see the contrast note in
# design/USER-SHAPED-RECIPES-FAQ.md for where that limit is stated.

[[phases]]
name = "doc-authoring"
depends_on = []

[[phases]]
name = "ledger-citation"
depends_on = ["doc-authoring"]

[[phases]]
name = "fix-authoring"
depends_on = ["ledger-citation"]

[roles.doc-authoring]
authors = "the orchestrator, who dispatches a document-only agent whose sole output is the docs describing what changed and why"
implements = "the document-only agent -- by construction, it produces documentation and nothing else in this phase"

[roles.ledger-citation]
authors = "the orchestrator -- and only the orchestrator, once it has itself read the produced docs"
implements = "the orchestrator, writing an ordinary ledger row (e.g. a decision row) citing the docs produced in doc-authoring"

[roles.fix-authoring]
authors = "the orchestrator, who dispatches a fix-only agent in a wholly separate dispatch -- one that, by construction, did not exist yet at the moment the ledger-citation row landed"
implements = "the fix-only agent"

[convergence.doc-authoring]
done = "the docs describing what changed and why have landed (committed or otherwise durably recorded)"
escalation_event = "none typed for this phase alone -- a stalled or failed doc-authoring dispatch is an ordinary dispatch failure, not a sequencing-specific escalation"

[convergence.ledger-citation]
done = "the orchestrator's own ledger row citing the produced docs lands, written only once the orchestrator has actually read them"
escalation_event = "none typed for this phase alone -- whether the orchestrator genuinely read the docs before citing them is not mechanically checkable (see this recipe's own honest limit, carried in prose, not in this field); no automated escalation exists for a premature or ungrounded citation"

[convergence.fix-authoring]
done = "the fix-only agent's own ledger row(s) land, and by construction the agent's own dispatch postdates the ledger-citation row's id"
escalation_event = "none typed for this phase alone -- order is enforced structurally by the ledger's own append-only, monotonically-issued row ids, not by a runtime convergence check; a reader verifies the order after the fact by comparing row ids, which is the whole point of the pattern"

[landing_zones.doc-authoring]
zone = "the repository's tracked source tree (the docs themselves, committed)"

[landing_zones.ledger-citation]
zone = "the ledger -- an ordinary ledger row (this project's own worked instance used a decision row) citing the docs produced in doc-authoring"

[landing_zones.fix-authoring]
zone = "the repository's tracked source tree (the fix itself, committed) plus the ledger row(s) the fix-only agent's own dispatch and close produce"
```

**The prose recipe** (moved from `USER-RECIPES-FAQ.md`'s "Workflow patterns" section, content
preserving — only this lead-in sentence and the cross-reference below are new):

> **How do I prove two phases ran in the right order, instead of trusting an agent's
> say-so?**
> Split the work into two separately-dispatched agents and let the ledger's append-only row ids
> do the proving, rather than trusting either agent's narrative about which one went first. The
> pattern: dispatch a document-only agent whose sole output is the docs describing what changed
> and why; the orchestrator itself then writes a ledger row citing those produced docs, once it
> has read them; only after that row lands, in a wholly separate dispatch, is a fix-only agent
> created — an agent that, by construction, did not exist yet at the moment the documentation
> row landed. Because ledger rows are append-only and numbered in issuance order, a reader who
> was never in the room can verify the same three facts a live witness saw: the docs landed, the
> orchestrator's row citing them landed next, and the fix agent's own row landed only after
> that — order as a structural fact about row ids, never a self-report from either agent
> claiming it went first.
>
> Honest limit: this proves the ORDER in which the ledgered acts happened, not that the fix
> agent actually read the documents it was dispatched after — a fix-only agent created after a
> documentation row could still ignore it. Pair the sequencing with an ordinary review step that
> checks the fix's content against the docs it was supposed to follow; sequencing alone answers
> "did this happen in the right order", not "was the later act actually informed by the earlier
> one".
>
> Invented downstream, not here: this shape was invented by the autoharn-panel deployment's own
> orchestrator, in its own ledger (rows 401, 415, and 1144 there, named here only as history),
> and is carried upstream into this project's record via decision row 1295 (2026-07-17 "two-spy
> synthesis" — this project's own name for a maintainer-dispatched pair of independent, read-only
> observer sessions ["spies"] reporting separately on the same downstream deployment, whose two
> reports the orchestrator then reconciled into one record; every later mention of "two-spy
> synthesis" or "the spy" on this page is this same act, cited by its row number) — the underlying
> panel session transcripts remain local evidence per this project's auditability ruling; the
> ledger row is the citable record.

**The contrast note.** The TOML makes the dependency chain — doc-authoring before ledger-citation
before fix-authoring — a structurally checkable fact (`workflow_check.py` would refuse a cycle or
a missing dependency here, the same way it refuses one anywhere else), which is exactly the
property the prose recipe is arguing FOR in words. What the TOML cannot carry is the recipe's own
honest epistemic limit: the shape proves *order*, never that the later act was actually informed
by the earlier one, and it says nothing about the provenance of the pattern itself (invented
downstream, carried upstream via a named ledger row) — both are exactly the kind of "what this
proves and what it doesn't" honesty a `done`/`escalation_event` string was never built to hold.

## The bookkeeping-close pairing convention

**Plain words.** When closing a work item necessarily changes the tracked source tree, and you
want a defeasible, queryable record that the promised commit actually landed — not just an
assertion — pair the item with a companion whose entire resolution IS that commit. Four phases,
in order: open both items together, claim both, close the judgment-bearing item with an ordinary
review, then close the companion with the purpose-built bookkeeping constructor, which the CLI
machine-checks against the world's own git history before it will construct.

**The shape** (`design/workflows/faq-bookkeeping-close-pairing.toml`):

```toml
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T15:28:00Z
#   last-change: 2026-07-18T15:28:00Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

# Transcribed from design/USER-RECIPES-FAQ.md, "Workflow patterns" section, entry "How do I
# record, defeasibly, that a close's promised commit actually landed in the tree?" -- the
# bookkeeping-close pairing convention (invented downstream by the autoharn-panel deployment's own
# orchestrator, its ledger rows 407/408, carried upstream via decision row 1295; the s38
# kernel-lineage delta, kernel/lineage/s38-bookkeeping-close.sql, is what made the convention's
# closes representable honestly). The FAQ's own WITNESSED transcript (a real, disposable
# --new-world scaffold run, torn down after) is the source this specimen transcribes: two work
# items opened together, both claimed, the judgment item closed first with an ordinary
# review-bearing constructor, then the companion closed with --review-bookkeeping and a
# commit-shaped --witness the CLI machine-checks (git cat-file) at construction time.
#
# NO MISFIT recorded for this specimen -- a strict four-phase depends_on chain, exactly the shape
# v0's four fields already express; the one thing the TOML does not, and should not, try to carry
# is the convention's own governance caveat (--review-bookkeeping is a deliberately closed
# category -- reaching for it on a close that carries any judgment at all is category creep, per
# the FAQ's own text), a policy/judgment statement, not a control-flow constraint -- it stays
# prose-only, named in the contrast note in design/USER-SHAPED-RECIPES-FAQ.md.

[[phases]]
name = "open-items"
depends_on = []

[[phases]]
name = "claim-items"
depends_on = ["open-items"]

[[phases]]
name = "close-judgment"
depends_on = ["claim-items"]

[[phases]]
name = "close-companion"
depends_on = ["close-judgment"]

[roles.open-items]
authors = "the operator/orchestrator opening both work items together: the judgment item, and a companion item citing it (--refs work:<slug>) whose entire resolution IS the promised commit"
implements = "the operator/orchestrator, via ./led work open (judgment item) and ./led work open ... --refs work:<slug> (companion item)"

[roles.claim-items]
implements = "the operator/orchestrator, via ./led work claim on both items"

[roles.close-judgment]
authors = "whichever principal's judgment the first item's close actually carries -- the FAQ's own text: 'the first item closes on its own merits... because it carries judgment'"
implements = "the operator/orchestrator, via ./led work close <slug> shipped with exactly one of the two ordinary review-disposition constructors, --review-witness or --review-deferred"
reviews = "the review disposition itself IS the judgment content of this phase -- whichever of the two ordinary constructors is used, per the FAQ's own worked example (--review-witness self-review, in the scratch-world transcript)"

[roles.close-companion]
implements = "the operator/orchestrator, via ./led work close <slug>-commit shipped --review-bookkeeping --witness commit:<sha>"
reviews = "explicitly none -- the FAQ's own text: '--review-bookkeeping claims ONLY this commit exists -- nothing about its content, correctness, or completeness'; the CLI machine-checks the claim structurally (COMMIT-EXISTENCE, s38 Element 3) rather than via a judgment review"

[convergence.open-items]
done = "both work_opened rows exist -- the judgment item and the companion item citing it"
escalation_event = "none typed for this phase alone -- an open refused for an ordinary reason (e.g. a duplicate slug) is an ordinary CLI refusal, not a pairing-specific escalation"

[convergence.claim-items]
done = "both work_claimed rows exist"
escalation_event = "none typed for this phase alone -- a claim refused because a slug is already claimed or closed is an ordinary CLI refusal, not a pairing-specific escalation"

[convergence.close-judgment]
done = "a work_closed row exists for the judgment item, resolution=shipped, carrying exactly one review-disposition constructor (--review-witness or --review-deferred)"
escalation_event = "REFUSED at construction if a second review-disposition flag is stacked in the same close act (s29/s38 Element 2: exactly one of --review-witness, --review-deferred, --review-bookkeeping, never more than one)"

[convergence.close-companion]
done = "a work_closed row exists for the companion item, resolution=shipped, --review-bookkeeping, with a --witness commit:<sha> the CLI has confirmed exists in this world's own repository"
escalation_event = "REFUSED at construction if the witness commit does not exist in this world's repository (the COMMIT-EXISTENCE check, s38 Element 3, git cat-file -e <sha>^{commit}), or if --review-bookkeeping is stacked with a second review-disposition flag (s38 Element 2, same rule close-judgment's escalation_event names)"

[landing_zones.open-items]
zone = "the ledger -- the two work_opened rows (judgment item, companion item)"

[landing_zones.claim-items]
zone = "the ledger -- the two work_claimed rows"

[landing_zones.close-judgment]
zone = "the ledger -- the judgment item's work_closed row, carrying its review disposition"

[landing_zones.close-companion]
zone = "the ledger -- the companion item's work_closed row, carrying work_review_disposition=bookkeeping and work_review_ref=commit:<sha>; the commit itself lands in the world's own git repository, which the close act's construction-time check confirms rather than merely asserts"
```

**The prose recipe** (moved from `USER-RECIPES-FAQ.md`'s "Workflow patterns" section, content
preserving — only this lead-in sentence and the cross-reference below are new):

> **How do I record, defeasibly, that a close's promised commit actually landed in the tree?**
> Pair the work item with a second one. Whenever closing a work item necessarily modifies the
> tracked source tree, open a companion item at the same time whose entire resolution IS the
> git commit that captures the promised tree state. The first item closes on its own merits,
> with one of the two review-bearing constructors (`--review-witness` or `--review-deferred`),
> because it carries judgment. The companion closes only after the commit exists, with the
> third constructor built for exactly this shape — s38, the kernel-lineage delta that added it
> (`kernel/lineage/s38-bookkeeping-close.sql`):
>
>     ./led work close <slug>-commit shipped --review-bookkeeping --witness commit:<sha>
>
> The CLI machine-checks the claim at construction: the witness must be commit-shaped, and the
> commit must actually exist in this world's repository (`git cat-file` is run for you — a
> nonexistent or non-commit object refuses with a teach-text). The pairing gives you a
> defeasible, queryable record that the promised commit landed, without manufacturing a review
> obligation that has nothing in it to review.
>
> **Show me it actually working, not just the shape.** WITNESSED, on a disposable scratch
> [world](../GLOSSARY.md#world) scaffolded specifically for this walkthrough and torn down after
> (`bootstrap/new-project.sh <dir> --new-world faqwit0718 --db toy --host 192.168.122.1` — the
> live project's own ledger was never touched; s38 is authored but not applied to any pre-existing
> world under the runs-are-strictly-linear ruling, so a fresh `--new-world` scaffold, which carries
> s38 in its own birth chain, is the sanctioned way to exercise it live). Two work items, opened
> and claimed, then closed as the pairing convention prescribes — the judgment item first, with an
> ordinary review-bearing constructor:
> ```
> $ ./led work open faq-demo "demo work item for the pairing-convention FAQ transcript"
> led: row 7 written.
> $ ./led work open faq-demo-commit "companion bookkeeping item: resolution IS the landing commit for faq-demo" --refs work:faq-demo
> led: row 8 written.
> $ ./led work claim faq-demo && ./led work claim faq-demo-commit
> led: row 9 written.
> led: row 10 written.
> $ git init -q && git commit -q -m "faq-demo: the commit faq-demo-commit's bookkeeping close will witness" --allow-empty
> $ SHA=$(git rev-parse HEAD)   # 04de3a3589f0e7c65c7bd1346a28b794376cc5fb, this scratch world's own repo
> $ ./led work close faq-demo shipped --witness "note:DEMO.txt committed as $SHA" --review-witness "self:demo close for FAQ transcript"
> led: row 13 written.
> $ ./led work close faq-demo-commit shipped --review-bookkeeping --witness "commit:$SHA"
> led: row 14 written.
> ```
> `./led show 14` confirms the row landed exactly as the spec describes — `work_review_disposition`
> is `bookkeeping`, and `work_review_ref` carries the commit witness verbatim, not a paraphrase:
> ```
> work_slug                     | faq-demo-commit
> work_resolution               | shipped
> work_witness                  | commit:04de3a3589f0e7c65c7bd1346a28b794376cc5fb
> work_review_disposition       | bookkeeping
> work_review_ref               | commit:04de3a3589f0e7c65c7bd1346a28b794376cc5fb
> ```
> Both named refusal shapes fire exactly as documented, also WITNESSED live on the same scratch
> world: a witness citing a commit that does not exist in the world's own repository —
> ```
> $ ./led work close faq-demo2 shipped --review-bookkeeping --witness "commit:deadbeefdead"
> led work close: REFUSED -- --review-bookkeeping's --witness commit 'deadbeefdead'
>   failed the COMMIT-EXISTENCE check (s38 Element 3: 'git cat-file -e
>   deadbeefdead^{commit}' against <world-dir> did not resolve). Two honest
>   alternatives:
>     --review-witness <ref>   a review already exists; cite it
>     --review-deferred        this close act itself becomes the review obligation
> ```
> — and stacking `--review-bookkeeping` on top of a second review-disposition flag in the same
> close act:
> ```
> $ ./led work close faq-demo2 shipped --review-bookkeeping --review-witness "self:x" --witness "commit:$SHA"
> led work close: REFUSED -- --review-witness, --review-deferred, and
>   --review-bookkeeping are the THREE CONSTRUCTORS of a review disposition;
>   exactly ONE, never more than one, in one close act (s29 -- the earlier kernel-lineage
>   delta that first made a review disposition mandatory, `kernel/lineage/s29-obligation-item-
>   key-and-typed-close.sql` -- Element B, s38 Element 2).
> ```
> Both refuse at construction (exit 1), cleanly, with the teach-text this section already
> paraphrases above — nothing here was reasoned about without being run.
>
> Honest limits, stated so the pattern is not over-trusted: a bookkeeping close claims ONLY
> "this commit exists" — nothing about its content, correctness, or completeness; the paired
> JUDGMENT item's own review is where content is vouched for. And the constructor is
> deliberately a closed category: if you find yourself reaching for `--review-bookkeeping` on
> a close that carries any judgment at all, that is category creep — the exact drift the
> `work_bookkeeping_closes` view exists to make visible (every bookkeeping close, forever, one
> query; a growing view full of judgment-bearing closes is a finding to report upstream, never
> a local norm to settle into).
>
> Invented downstream, not here: the pairing convention comes from the autoharn-panel
> deployment's own orchestrator (its ledger rows 407 and 408, named here only as history),
> carried upstream via decision row 1295 (2026-07-17 two-spy synthesis); the s38 constructor
> (`design/FABLE-BOOKKEEPING-CLOSE-SPEC.md`, maintainer-ratified) is what made the convention's
> closes representable honestly instead of forcing rubber-stamp countersigns.

**The contrast note.** The TOML makes the pairing's own precondition structure a checkable
fact — four ordered phases, and the two REFUSED-at-construction escalation events (a stacked
review-disposition flag, a witness commit that does not exist) named as `escalation_event`
strings a reader can find without hunting through the CLI's teach-text. What it cannot carry is
the convention's own governance caveat: `--review-bookkeeping` is a *deliberately closed
category*, and reaching for it on a close that carries any judgment at all is category creep — a
policy statement about how the mechanism should and should not be used, not a control-flow fact,
so it has to stay prose. The witnessed live transcript (real row ids, real refusals, run on a
disposable scratch world) also has no TOML analogue at all — the shape declares what a run *would*
do, never a record that one actually happened.

## Schema gaps filed (not factored)

**The makespan-scheduler batch-dispatch recommendation** (`USER-RECIPES-FAQ.md`, "Workflow
patterns", "I have a large batch of independent work units to dispatch...") is NOT factored.
v0's own grammar explicitly disclaims scheduling as out of scope — quoting
`design/workflows/README.md` verbatim: *"Not a scheduler. Time and resource assignment stay with
`tools/makespan-scheduler/` … the DSL declares order, never dates."* This is not a missing field
the grammar could gain; it is a stated anti-goal of v0 itself, so nothing here invents a field on
spec. The load-bearing constraint that would need a schema home, quoted verbatim from the FAQ's
own text: *"the scheduler can only be as correct as the job list it is given, and it has NO
notion of one job's output feeding another job as input … a batch with a real, hidden data
dependency fed into it as if it were a mere resource conflict produces a schedule that looks
authoritative and is wrong. Before treating a batch as ready to schedule, therefore, an
independent countersign of the job list itself (not self-review) is the recommended discipline,
not an optional nicety."* Filed against `pipeline-dsl-exploration` for the maintainer's own
future scoping — the same gap `design/workflows/README.md`'s own "Known misfits" section already
names from the transcription side, under the entry headed "Same-file contention among sibling
phases has no field in this grammar" (same-file contention among sibling phases has no field
either).

## What this page is not

Like its sibling, this page is not an inventory, not a setup guide, and not a promise that every
mechanical-looking recipe in `USER-RECIPES-FAQ.md` has been factored — only the ones enumerated
in the `shaped-recipes-factoring` work item's closing report, against the three criteria in
[design/FABLE-SHAPED-RECIPES-EXPLORATION-SPEC.md](../design/FABLE-SHAPED-RECIPES-EXPLORATION-SPEC.md)
section 2. A recipe not listed here either failed one of those three criteria (most commonly:
it is a declarative grammar or a Q&A pointer with no enumerable phases at all, never an
algorithmic pipeline) or is itself a schema gap filed above, never both silently.
