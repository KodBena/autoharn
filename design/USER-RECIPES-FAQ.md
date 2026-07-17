# Can I do that? — recipes FAQ for operators

This page is written for an operator of a scaffolded project who wants to know whether the
harness supports a thing they have in mind, and what to actually type if it does. Every
entry below began life as a real operator question ("can we use X for end users?", "can I
track Y?") asked of this project's orchestrator during 2026-07; the answers were built,
witnessed, and then condensed here. This page deliberately restates NO grammar and NO
ceremony in full — each recipe names the intent, the one-line shape, the honest limit, and
the ONE page where the full truth lives (this project's single-source-of-truth discipline:
a grammar documented twice drifts). The dense per-mechanism inventory this page complements
is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md); the front door for first-time setup is
[USER-GUIDE.md](../USER-GUIDE.md).

## Planning and retrospectives

**Can agents estimate a task's cost before doing it, and can I see how the estimates did?**
Yes — ledger an `estimate:` row per task at decomposition time; `./pickup` prints all of
them under its ESTIMATES section, and the retrospective recipe has an estimate-vs-actual
section for reading them against what happened. The standing invariant, enforced by
design rather than by accident: a missed estimate is retrospective data, never a
violation — nothing gates, audits, or refuses on estimate accuracy, and nothing will.
Grammar and comparison recipe: [USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md) §6.

**Can I get cost/usage figures I can rely on?**
Partly, and the line matters: raw hook-witnessed event counts are evidentiary; anything
priced or derived from them (token totals, money) is diagnostic-grade permanently — useful
for a sanity check, never sound enough to bill against. Headline statement:
[USER-GUIDE.md](../USER-GUIDE.md) §5; the design boundary:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md) §6.

**Can work form a deep task tree without deep subagent nesting?**
Yes — the tree lives in ledger rows, not process nesting: an interior task's children are
OPENED as work items citing the parent, dispatched flat, each closeable with its own
witness. Execution stays one or two levels deep; the logical tree is unbounded and every
interior node is auditable. The work verbs' home is
[ORCH-OPERATING-CARD.md](../ORCH-OPERATING-CARD.md). Per-node estimate-vs-actual rollups
are a designed follow-up, not yet built — the design lives on the deployment's own tracker
as work item `work-tree-rollup` (a ledger row, not a committed page: read it with
`./led show work-tree-rollup` at the repository root, the same live-lookup convention the sibling
specs use for tracker items).

## Workflow patterns

**I want a workflow to iterate until clean — can an agent spawn sub-agents and loop on its
own output until a defect list comes up empty?**
Yes, natively, and both halves of that question have a plain answer. The looping half: a
"fix-point" here means a script keeps calling an agent, feeding it the artifact or defect
list as it currently stands, until a round finds nothing new to fix — and that loop lives in
the workflow **script's own deterministic control flow** (an ordinary `while` loop wrapping
repeated agent invocations — whether that is the `Agent` tool from an orchestrating session
or a standalone driver script built on the Claude Agent SDK), never in any one agent's own
sense that it is "done." Terminate on **loop-until-dry**: keep looping until K *consecutive*
rounds each report zero new findings, not just one empty round — a defect population of
unknown size can have a long tail a single-round counter misses. (This project uses the
identical criterion in its own fix-point loops:
[design/ORCH-AGENTIC-PATTERNS.md](ORCH-AGENTIC-PATTERNS.md) §3's "adversary files zero new
rows for K consecutive rounds", and the two-role audit loop below.) The spawning half: yes,
an agent your workflow dispatches can itself dispatch further sub-agents — nesting is not
disabled — with a fuller, more capable agent type (e.g. `general-purpose`) available to use
where the workflow's own default agent type is a leaner, narrower one.

The load-bearing caveat, stated because it was caught failing in practice: **each round of
the loop must spawn a genuinely fresh agent, never resume one long-lived agent across
rounds.** An agent that carries its own prior round's context into the next round is not
actually re-examining the current state with open eyes — it already committed to a verdict
in an earlier turn, and tends to re-assert that verdict even when the bytes in front of it
have since changed underneath it. This is not a hypothetical risk: on 2026-07-13, in this
project's own two-role fix-point loop (the A:B:C fresh-context documentation-review loop,
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md)'s round-2 discipline), a
reviewer agent resumed via a follow-up message — rather than spawned fresh — repeated its
first round's verdict *verbatim* against on-disk content that directly contradicted it. Spawn
round N+1 as a brand-new agent invocation with no memory of round N, every round, no
exceptions.

Termination discipline is the other half worth naming up front, not discovering by billing
surprise: a dry-count guard (K consecutive empty rounds) belongs alongside a hard budget
guard (a round cap, a cost or token ceiling) — a workflow script is ordinary deterministic
code, so a fix-point loop with a broken or too-loose termination condition runs to whatever
cap you built in, burning real, billed tokens the whole way there; nothing backstops a
runaway loop before that cap except the cap itself. No single page owns this pattern end to
end yet; [design/ORCH-AGENTIC-PATTERNS.md](ORCH-AGENTIC-PATTERNS.md) works out the
loop-until-dry criterion in more depth, and
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md) is a complete worked example of
exactly this shape — two agent roles, fresh-fork-per-round, a two-round cap, and a named
escalation path for when the loop does not converge.

**My workflow script just crashed / hung / did something baffling — is this a known
shape?** Maybe — check first. Five gotchas have each bitten this project's own
workflow scripts more than once (args arriving as an already-parsed JSON value rather
than a string needing a parse, model-pinning on every dispatch call, the ban on
calling `Date.now()`/`Math.random()` inside a script a durable workflow runtime may
resume or replay from a checkpoint — either call can return a different value on
resume and silently steer the script down a different path than it took the first
time, stall-vs-crash as opposite-cause failure shapes needing opposite diagnoses, and
a workflow run's own journal (its append-only `.jsonl` log of what each round did)
carrying `result` fields that are repr-strings, not nested JSON) — four with a dated
incident on record, one (the Date.now()/Math.random() ban) stated as a general hazard
with no located incident yet — each with a stated fix regardless. Read
[ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md](ORCH-WORKFLOW-SCRIPT-GOTCHAS-RECIPE.md)
before writing a new workflow script, or when one fails in an unfamiliar way.

**I have a large batch of independent work units to dispatch — is there a standing
recommendation for how to parallelize them instead of just running them one after another?**
Yes — **standing recommendation** (maintainer directive, 2026-07-14): use
`tools/makespan-scheduler/` (vendored 2026-07-14, split into its own published repository and
converted to a git submodule 2026-07-15) for any large-scale batch of jobs that conflict only
over shared
resources (e.g. two edits touching the same file), rather than defaulting to a hand-picked
sequential order. Claude Code is, functionally, an infinite-server model of work — parallel
agent capacity is cheap to spin up — but the default LLM inclination is still to serialize
work that could safely overlap, which wastes exactly the capacity that is available. Feed the
batch's jobs (id + the resources each one touches + an optional duration) to the scheduler; it
returns a schedule computed by CP-SAT (a constraint-programming solver, OR-Tools' `cp_model`) —
either proven optimal or honestly labeled not — and a
`batches` field — ordered waves of job ids safe to dispatch together — and that dispatch order
is what you actually run, not a re-guess. **The guarantee is conditional, and the condition
matters more than the tool**: the scheduler can only be as correct as the job list it is given,
and it has NO notion of one job's output feeding another job as input (the vendored tool's own
"independent-tasks" scope) — a batch with a real, hidden data dependency fed into it as if it
were a mere resource conflict produces a schedule that looks authoritative and is wrong. Before
treating a batch as ready to schedule, therefore, an independent countersign of the job list
itself (not self-review) is the recommended discipline, not an optional nicety — full
treatment, including exactly how that countersign rides this project's own `led
review`/`led obligate` machinery and what remains unbuilt today: read
[ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md](ORCH-MAKESPAN-SCHEDULING-GUARANTEE.md) in full before
adopting this for anything you'd actually rely on. Tool docs and vendoring/split provenance:
[`tools/makespan-scheduler/README.md`](../tools/makespan-scheduler/README.md) /
[`tools/makespan-scheduler-PROVENANCE.md`](../tools/makespan-scheduler-PROVENANCE.md).

**How do I prove two phases ran in the right order, instead of trusting an agent's
say-so?**
Split the work into two separately-dispatched agents and let the ledger's append-only row ids
do the proving, rather than trusting either agent's narrative about which one went first. The
pattern: dispatch a document-only agent whose sole output is the docs describing what changed
and why; the orchestrator itself then writes a ledger row citing those produced docs, once it
has read them; only after that row lands, in a wholly separate dispatch, is a fix-only agent
created — an agent that, by construction, did not exist yet at the moment the documentation
row landed. Because ledger rows are append-only and numbered in issuance order, a reader who
was never in the room can verify the same three facts a live witness saw: the docs landed, the
orchestrator's row citing them landed next, and the fix agent's own row landed only after
that — order as a structural fact about row ids, never a self-report from either agent
claiming it went first.

Honest limit: this proves the ORDER in which the ledgered acts happened, not that the fix
agent actually read the documents it was dispatched after — a fix-only agent created after a
documentation row could still ignore it. Pair the sequencing with an ordinary review step that
checks the fix's content against the docs it was supposed to follow; sequencing alone answers
"did this happen in the right order", not "was the later act actually informed by the earlier
one".

Invented downstream, not here: this shape was invented by the autoharn-panel deployment's own
orchestrator, in its own ledger (rows 401, 415, and 1144 there, named here only as history),
and is carried upstream into this project's record via decision row 1295 (2026-07-17 two-spy
synthesis) — the underlying panel session transcripts remain local evidence per this project's
auditability ruling; the ledger row is the citable record.

## Declaring things on the ledger

**Can I declare which tools/services/agents this project may, should, must, or must not
use?**
Yes — one `resource:` row per resource, whose TIER field carries the deontic force:
`available` (MAY), `blessed:` (SHOULD), `mandated:` (MUST), `forbidden:` (MUST-NOT).
`./pickup` renders them tier-sorted, prohibitions first. Honest limit, tier by tier (not one
blanket answer — the two owning specs, [USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md)
and [ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md), drifted on exactly this
in mid-2026-07-12 and were
reconciled 2026-07-13, tracker row 223 — a ledger row, not a committed page: `./led show 223` at
the repository root reads it in full): `mandated`'s close-review convention already shipped and
surfaces an undischarged close as [`review_gap`](../GLOSSARY.md#review_gap) debt — never a
refusal of the close itself;
`forbidden` is declaration + display only today, with no mechanism yet refusing an invocation
that reaches it (that audit is spec'd, unbuilt — the spec's own §7 says so). The reconciled,
owning statement of what is and is not enforced per tier lives at
[ORCH-SPEC-RESOURCE-ACCOUNTING.md §4.1](ORCH-SPEC-RESOURCE-ACCOUNTING.md#41--the-mandated-tiers-enforcement-status-reconciled-dated-correction-2026-07-13-tracker-row-223).
Grammar home: [USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md); design:
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md).

**Can I declare an architectural or licensing boundary and split work along it?**
Yes, declare it today; enforcement is staged. `taxon:` rows assign path patterns to named
classes, `interface:` rows name the sanctioned crossing points; `./pickup` renders a
TAXONOMIES section. The worked example is a real one (an MIT-derivative package inside a
public-domain codebase). What does NOT exist yet: the audit family and the write-time gate
that would police cross-boundary writes (Stages B–D of the spec). Declaring no taxonomy
declares no obligation. Grammar home and example:
[USER-TAXONOMY-DECLARATION.md](USER-TAXONOMY-DECLARATION.md); design:
[ORCH-SPEC-TASK-TAXONOMY.md](ORCH-SPEC-TASK-TAXONOMY.md).

**Can I encode how tasks should be split, so I don't have to micromanage decomposition?**
Yes as declared policy: `task-policy:` rows carry splitting criteria (one acceptance
criterion per task, one boundary per task, estimate-before-execution, …) with MUST/SHOULD
force, and reviewer countersigns cite the criteria they checked. The policing column is
derived from what mechanisms actually exist — a criterion never claims more enforcement
than is built. Design and criteria table:
[ORCH-SPEC-DECOMPOSITION-POLICY.md](ORCH-SPEC-DECOMPOSITION-POLICY.md) §3.

## Trust ceremonies

**Can I prove a commission really came from me?** (a "commission" here is a ledgered
instruction attributed to a principal — the maintainer or an agent acting for them — and the
question is how strongly that attribution can be trusted). Full grammar and worked walkthrough:
[USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) §5–§7.
Yes, and it comes in three increasing strengths: **LAZY** (the row's stated actor is taken on
its word, no cryptographic or structural check), **FULL** (the right actor recorded on the row,
plus the absence of the interception stamp a hook adds only when an agent — not the maintainer
directly — wrote the row: a rebuttable presumption, not proof), and **SIGNED** (a detached GPG
signature over the row, checked against a known key — the only strength that survives a
dispute). The standing rule is that a **CONTESTED** commission (one whose attributed actor is
disputed after the fact) must be SIGNED to stand. You can rehearse every ceremony with a
throwaway key before any real key exists.

**Can I anchor the ledger so later tampering is provable?**
Yes — sign the chain head at run close (`verify-chain --head`, then a detached signature).
Any retroactive row alteration then breaks provably against a head your key vouches for;
the head also carries the apparatus-config hash, so a mechanism flipped off between two
signed heads is provable by comparing them. Known honest limits: the chain-hash mechanism proves
tampering with rows *between* two signed heads, but a deleted row at the very tail of the chain
(the newest end, appended after the last signature) is invisible to the chain alone — nothing
has signed over it yet (tracker item `s26-tail-deletion-witness` holds the designed fix — a
ledger row, not a committed page: `./led show s26-tail-deletion-witness` at the repository root
reads it), and the
apparatus comparison is manual, not auto-flagged.
Walkthrough: [USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) §6.

## Review discipline

**Is a review's content ever checked, or does any countersign discharge the obligation?**
Partly. [`review_gap`](../GLOSSARY.md#review_gap)'s own discharge test never looks at what a
review says — any unsuperseded, distinct-actor `attest` clears the obligation regardless of
content, by design. A separate, layered check DOES inspect the discharging review's own
statement: `./audit --review-gap` flags a discharge whose whitespace-normalized statement is
shorter than `CONTENT_FREE_STATEMENT_THRESHOLD` (40 chars,
[engine/review_gap_thresholds.py](../engine/review_gap_thresholds.py)) — the case this check
answers to was a real 4-char `"test"` review that silently discharged a genuine obligation.
Honest limit, in the check's own vocabulary: it is a length heuristic, so its verdict is
`FLAGGED`, never `VIOLATED` — a genuine terse review passes ("Confirmed, matches row 4's stated
criteria exactly." is 51 chars) and hollow-but-plausible prose of ordinary length ("Reviewed and
everything looks correct, no issues found, approved for merge.") is NOT caught; the check catches
the "test"-shaped instance, not the class, and never substitutes for a human reading the review.
This exit code (6) is reachable only through `--review-gap`, and only when nothing earlier
already raised the exit and at least one review is flagged. Witnessed both polarities:
[seen-red/content-free-review-audit/](../seen-red/content-free-review-audit/).

**How do I make an implementation step mechanically wait on a review step, instead of relying on
remembered discipline?** Arm `decomposition_review` — a third, independent PreToolUse mechanism in
[hooks/pretooluse_change_gate.py](../hooks/pretooluse_change_gate.py), alongside `change_gate`
(the ticket/window check) and `permit_to_work` (the open-claim check). It exists because a claimed,
open work item proves *permission* to work, never that the item's own decomposition — its plan, its
acceptance criteria — was ever looked at by anyone but its author: on this project's own record, a
claimed task's implementation began six seconds after claim, roughly 2.5 minutes ahead of the
countersign verdict that was supposed to gate it (the run12 specimen, named in the hook's own
docstring). A serious adopting organization should read that specimen as a *class*, not a one-off:
any harness that lets an agent dispatch straight from "plan accepted in principle" to "editing files"
carries the same race, and self-disclosed recurrences of exactly this shape are on record upstream
too, filed as [anthropics/claude-code#77900](https://github.com/anthropics/claude-code/issues/77900).
`decomposition_review` closes it by refusing a substantive `Write`/`Edit`/`NotebookEdit` — or a
governed-file-mutating `Bash` command — anywhere under the world's root while the claimed work
item's own opening act (`work_opened`) carries an undischarged
[`countersign_obligation`](../GLOSSARY.md#obligation): the same [`review_gap`](../GLOSSARY.md#review_gap)
discharge test every other obligated row already uses, not a second hand-rolled predicate.

Arming it is three steps, and none of them is optional-by-omission — a world that skips any one of
the three is unarmed, silently:

1. **Obligate the actor whose decompositions need outside eyes:**
   `./led obligate decomposition-review <reviewer-principal> <worker-principal>` (the worker is the
   *obliged* actor — get the direction backwards and you obligate the reviewer instead, a mistake
   this project's own `led obligate` usage text calls out by name because it has happened twice).
2. **Flip the mode to `enforce`** in `.claude/apparatus.json`:
   `"mechanisms": {"decomposition_review": {"mode": "enforce"}}` — see
   [bootstrap/templates/APPARATUS.md](../bootstrap/templates/APPARATUS.md) for the full switchboard.
3. **Verify it is actually armed before trusting it.** `led decomposition-review-status` is the
   purpose-built verb for this — it prints the resolved mode, the obligation-table row counts, and a
   one-line verdict (`ARMED-ENFORCING` / `ARMED-OBSERVING` / `VACUOUS` / `OFF`) — but as of this
   writing it exists only on the unmerged `build/effective-state-display` branch, not yet on this
   page's own base; check its own repository state before assuming it is present in yours. Until it
   lands, or if it has not landed in your checkout, read the same two raw facts by hand: (a) `cat
   .claude/apparatus.json` for `mechanisms.decomposition_review.mode` (missing entirely means the
   mechanism's own default, `observe`, applies — see below); (b) `./led review-gap`, cross-read
   against `./led work list` for which slug is currently open and claimed — if that slug's
   `work_opened` row appears in the `review-gap` output, the obligation is live and undischarged.

**The shipped default is `observe`, not `enforce` — deliberately, and unlike its two sibling
mechanisms.** `change_gate` and `permit_to_work` both default to `enforce` because they are free per
call and were already the project's steady state before per-mechanism modes existed.
`decomposition_review` is new machinery: an already-running, already-scaffolded world would find its
writes newly gated the moment `hooks/` is updated, with no operator opt-in — so this one mechanism
defaults to the weaker mode on purpose, and arming it to `enforce` is a one-line, per-world decision
an operator makes deliberately (see the module docstring's own "DECOMPOSITION-REVIEW BLOCKER"
section for the reasoning in full). A serious adopting organization should read this the same way:
the mechanism ships inert everywhere, and an unarmed world is not a bug, it is the honest starting
state — arming it is a policy choice belonging to whoever owns the world, not something a scaffold
should spring on a project mid-flight.

**What is, and is not, witnessed for this mechanism specifically.** PreToolUse hooks demonstrably
fire on a dispatched subagent's own tool calls — 24 specimens of `change_gate` (this same script,
this same invocation path) denying a subagent's edit are recorded in the upstream autoharn ledger,
decision row 1295 (2026-07-17 two-spy synthesis); the underlying session transcripts remain local
evidence per the project's auditability ruling — the ledger row is the citable record. What had
NOT been separately witnessed, because every previously-observed world carried zero
`countersign_obligation` rows under the shipped `observe` default, is `decomposition_review` itself
actually blocking anything. A scratch world (`decompprobe`, scaffolded via
`bootstrap/new-project.sh --new-world`, torn down completely afterward) closes that gap directly:
with a claimed work item's decomposition obligated and the mode flipped to `enforce`, invoking
`hooks/pretooluse_change_gate.py` with a real `PreToolUse` `Write` event on stdin produced

```
Ledger policy (decomposition-review-blocker): work item 'probe-task' (work_opened row 2) carries an
undischarged decomposition-review obligation — executing a claimed work item before its OWN
decomposition is countersigned makes every subtask a bet on an unreviewed plan (the run12 specimen:
task 1's implementation began 6 seconds after claim, ~2.5 minutes ahead of the countersign verdict
that was supposed to gate it). Discharge it, THEN retry the same edit: ...
```

(exit code 2, `permissionDecision: "deny"`). Discharging the obligation — a distinct-actor
`self-review` countersign, disclosed as such (the solo-world fallback this project's own scaffolded
`CLAUDE.md` documents) — and re-issuing the byte-identical event then produced exit code 0 with no
deny output at all: the same claimed item, the same edit, only the obligation's discharge state
changed. Flipping the mode back to `observe` and re-issuing the same event against a fresh
undischarged obligation produced `permissionDecision: "allow"` with an `additionalContext` field
opening `[apparatus observe-mode WARNING — would DENY under enforce] Ledger policy
(decomposition-review-blocker): ...` — the warn-not-block contrast, same check, same undischarged
state, only the mode differed. **What closes the crux is the composition of these two witnesses, not
either alone**: the ledger-recorded subagent specimens (decision row 1295) establish that this hook
script fires on a dispatched subagent's own tool calls at all; this scratch-world test establishes that
`decomposition_review`'s own deny path, once armed, actually fires for an undischarged obligation.
Neither witness alone would close it — the subagent specimens never exercised `decomposition_review`
armed, and this test never dispatched through a subagent.

**Should compliance review run per-commit or per-changeset?**
Per-changeset, at minimum — one reviewer reading the entire multi-commit changeset against the
LAW together, rather than one reviewer per commit checking each commit in isolation. The
reason is not caution for its own sake: a defect can live entirely in the INTERACTION of two
individually-correct commits, and no per-commit review ever sees that interaction, because
each commit, read alone, is fine.

The witnessed specimen (via decision row 1295's two-spy synthesis, citing the autoharn-panel
deployment's own row 590, named here only as history): a backend commit that validated
`limit=0` as a rejected input, and a frontend commit that messaged that same `limit=0` case to
the end user, landed about a minute apart as two separate commits. Each commit was correct in
isolation — the backend validation was sound on its own, the frontend messaging was sound on
its own — and the pairing was a regression, caught only because the review that found it
spanned both commits together, not because either commit's own review flagged anything.

Honest trade-off, stated plainly rather than left implicit: a whole-changeset review costs more
context per review round (the reviewer holds every commit in the set at once, not one at a
time) and arrives later than a per-commit review would (it waits for the changeset to close
rather than firing on each commit as it lands). The recipe is span-at-least-the-changeset for
LAW/compliance review — not never-review-early; a fast per-commit pass can still run as a first
filter, but it is not a substitute for the changeset-spanning pass, which is the only one
positioned to catch an interaction defect between two commits that are each correct alone.

## Classifying audit/diagnostic findings

**I have a batch of findings from a code audit or review, and sorting them into categories
keeps producing overlapping or incomplete buckets — is there a standard way to do this?** Yes —
split every narrative finding (one that bundles more than one bug or observation) into single-
actionable-unit atoms first, with a provenance link back to where each atom came from, THEN
classify; once every unit is atomic, "did we cover everything" and "does nothing overlap" become
a one-line mechanical check instead of a manual sweep. A second pass then re-clusters the atoms
into
[fix-authorship blocks](ORCH-FINDING-ATOMIZATION-RECIPE.md#stage-2--reconstitute-atoms-into-blocks-author-fixes-at-the-block-grain-not-the-atomic-grain)
by shared invariant, so one typed fix forecloses a whole class of bugs
rather than patching each atom instance-by-instance. Full method, its adjudication against this
corpus, and its relation to
[ADR-0000's typed-fix discipline](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md):
[ORCH-FINDING-ATOMIZATION-RECIPE.md](ORCH-FINDING-ATOMIZATION-RECIPE.md).

## Documentation quality

**Can my project use the fresh-context documentation review loop autoharn uses on itself?**
Yes — this was asked as "is there a reason we can't?", and the answer was no: the reviewer
is an ordinary fresh-context subagent. Scaffolded projects get `./attest-doc`
(`record`/`check`), a project-local attestations ledger, and an opt-in DOC-ATTESTATION
section in `distance-to-clean` (the scaffold's own operator-facing report that prints how far
the deployment sits from a clean governance state; apparatus switch `doc_attestation`, default
off).
Walkthrough: [USER-DOC-AUDIT-LOOP.md](USER-DOC-AUDIT-LOOP.md); the loop's rules:
[ORCH-ABC-AUDIT-LOOP-RECIPE.md](ORCH-ABC-AUDIT-LOOP-RECIPE.md).

**I have known findings to verify AND I want a fresh legibility sweep — can one reviewer do
both?**
No — and this was learned the hard way (a real, dated 2026-07-13 anchoring defect in a live
deployment, not a hypothetical). A reviewer briefed with a known findings list *and* asked to also
sweep fresh anchors on the list — the sweep silently degrades into a second verification pass. Run
two separate reviewers: a targeted verifier (front-loaded with the list — correct there) and a
genuinely blind B (artifact + commission only, no findings, no mention a correction pass
happened). The same rule governs a co-signer/countersign briefing. Full account, with the
witnessed 0-versus-4-and-7 findings gap between confirmation-mode and adversarial-fresh reviews:
[USER-DOC-AUDIT-LOOP.md](USER-DOC-AUDIT-LOOP.md)'s "Briefing your reviewer" section.

## Operating rhythm

**How do I pick up work after a break?**
Start a fresh session and run `./pickup` — never resume or continue an existing one. The brief is derived
at pickup time from live ledger state; a stored handoff decays and replayed context is
the quadratic cost the ledger exists to replace. Card:
[ORCH-OPERATING-CARD.md](../ORCH-OPERATING-CARD.md).

**Can I turn a safety mechanism off, or make it observe-only? Will that be visible?**
Yes and yes — every mechanism is independently `off`/`observe`/`enforce` in
`.claude/apparatus.json`, live on the next tool call; and since 2026-07-12 every mutation
of that file is itself journaled (hashes, which modes changed), so a flip is witnessed
rather than silent. Full switchboard, per-mechanism defaults and costs:
[bootstrap/templates/APPARATUS.md](../bootstrap/templates/APPARATUS.md).

**A finished run's world turns out to have a defect. Can I patch it?**
No — runs are strictly linear; a superseded world is settled, read-only evidence. The fix
enters the next world via the scaffold (it usually already has), and the finding goes on
the ledger. This is a ruling, not a limitation looking for a workaround. Ruling text:
[../CLAUDE.md](../CLAUDE.md), ORCHESTRATION section.

## Your review queue

**Can I keep a ranked "things I need to personally look at" queue, and tick items off as I go?**
Yes — a `review:`/`review-done:` ledger row pair does this; it renders at every `./pickup`
under a `MAINTAINER-REVIEW-QUEUE` section. Unlike the `resource:`/`estimate:` grammars
elsewhere on this page, the grammar is written out here **in full**, not merely pointed at —
this recipe is its one documented home
([ADR-0005 Rule 1](../law/adr/0005-documentation-discipline.md), single source of truth per
fact), and it deviates from this page's usual "point elsewhere" convention on purpose so an
executive queue has a self-contained page to hand a first-time reader.

A queue entry is a `decision`-kind ledger row (the same kind `resource:`/`estimate:` ride, run
via `./led decision "..."`), validated at write time by
[`bootstrap/templates/led.tmpl`](../bootstrap/templates/led.tmpl) and rendered at pickup time
by the `MAINTAINER-REVIEW-QUEUE` section of
[`bootstrap/templates/pickup.tmpl`](../bootstrap/templates/pickup.tmpl) — both cite this
subsection by name rather than restating the grammar a second time
([ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1).

**Opening or re-ranking an item:**

```
review: <SLUG> | <RANK> | <WHAT> | <POINTER>
```

The four fields, in order, separated by ` | ` (space-pipe-space):

- **SLUG** — a bare slug matching `^[a-z0-9][a-z0-9-]*$` (no spaces), the same shape
  `estimate:`'s TASK-SLUG field already uses. Identifies the item across its whole lifetime —
  opened, re-ranked, ticked off, and (if it recurs) re-opened.
- **RANK** — a positive integer (`1`, `2`, `3`, …), where `1` is the MOST important item —
  the queue's own sort key.
- **WHAT** — non-empty plain words: what you are reviewing, in a phrase a cold reader
  understands without opening the pointer.
- **POINTER** — non-empty: where to look. A repository path, a live-lookup command
  (`./led show 214`, run at the repository root), or a URL — whichever actually resolves for
  this item.

**Ticking an item off:**

```
review-done: <SLUG> | <DISPOSITION>
```

- **SLUG** — must match the same slug grammar `review:` uses (a `review-done:` for a
  slug-shaped-wrong SLUG is refused — there being nothing on record it could sensibly close).
- **DISPOSITION** — non-empty free text: what you decided, or what happened.

**Semantics — latest row per SLUG wins, append-only.** Nothing here is mutated or deleted; the
queue's state is *derived* from whichever row for a given SLUG has the highest ledger row id:

- The **latest `review:` row** for a SLUG is the one whose RANK/WHAT/POINTER render — so
  filing a new `review:` row with the same SLUG and a different RANK is how you re-rank an
  item (no supersedes flag needed; this is a simpler rule than `resource:`'s, deliberately,
  because a queue's whole point is a fast one-liner).
- A **`review-done:` row for a SLUG removes it** from the rendered queue — it is still on the
  ledger (append-only, nothing is ever deleted), just no longer printed as open.
- A **`review:` row filed AFTER a `review-done:` for the same SLUG re-opens it** — the same
  latest-row-wins rule applied uniformly, so reopening needs no special-cased verb.

Copy-paste examples:

```sh
./led decision "review: key-generation | 1 | decide the signing-key generation ceremony | design/MAINT-MAINTAINER-DECISION-BRIEF.md"
./led decision "review-done: key-generation | approved the brief's proposed ceremony as written"
```

`./pickup`'s `MAINTAINER-REVIEW-QUEUE` section prints every open entry rank-ascending, each with
the exact `./led decision "review-done: <slug> | <disposition>"` one-liner to tick it —
copy-paste, no grammar to recall. An empty queue prints a short, explicit line, never silence
(the same never-silent convention `resources()`/`estimates()` already keep). A malformed
`review:`/`review-done:` row is refused loudly at write time (see `led.tmpl`'s own teach-text);
nothing here is a gate on WHAT you decide, only on the shape of the row that records it.

## Correcting the record — supersession, and what to do about its fallout

**I encoded a row wrong (wrong flag, missing refs, bad wording) — how do I fix it?**
Supersede it: write the corrected row with `--supersedes <old-row-id>` (for work items,
`led work open <new-slug> ... --supersedes <old-open-row-id>`). The ledger is append-only,
so a correction is always a new, linked row — the old one leaves current truth but stays
in history, never obscured. This is the default answer to every "I wrote it wrong"
situation; nothing is ever edited in place, and raw SQL against the ledger is never the
answer to a missing verb. Honest limit: superseding a work item's OPEN row permanently
burns its slug (a deliberate, ratified choice) — the replacement needs a new slug, and
surviving claims/edges that named the old slug must be re-issued. Grammar:
`./led work open` usage; semantics:
[FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md](FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md).

**I superseded a parent item and `work violations` now shows orphan rows that nothing can
clear — did I break the world?**
No, and this exact situation happened in a real deployment (a composite parent superseded
while five children — three already closed — still hung under it; every child's parent-edge
became an `orphaned_by_retraction` violation with no discharge path, permanent blocking
debt). Nothing was lost: the children's own rows, closes, and reviews are all intact; the
violations are the record correctly describing dangling linkage. The gap was ours — a
violation an operator can legally cause must have an answering act, and orphans had none.
The fix is the s37 violation-disposition mechanism
([FABLE-ORPHAN-DISPOSITION-SPEC.md](FABLE-ORPHAN-DISPOSITION-SPEC.md)):
`led work resolve-violation <violating-act-id> <reissued|retired> "<basis>"` answers any
in-force violation with a reviewed, attributable row, and `led work supersede-cascade` handles the
live-descendants ripple in one witnessed pass. Until your world has s37: take no further
supersession, let the stop-gate (`hooks/stop_clean_exit.py`, the Stop hook that blocks a
session from ending while governance debt is open) handle stops via its loud fail-open
(that valve exists for exactly this — structurally unclosable debt), and migrate when the
delta reaches you.
**When do I reach for `resolve-violation`, and when for `supersede-cascade`?**
They are not alternatives at the same level: `resolve-violation` is the primitive and
`supersede-cascade` is a convenience built entirely out of it — nothing the cascade does
is impossible by hand, and the cascade writes no special rows. Reach for
`resolve-violation` when violations ALREADY EXIST (you are cleaning up after a
supersession, yours or an inherited one), and always for a superseded parent's
closed/settled children — their edges get `retired` dispositions and the children
themselves are never touched. Reach for `supersede-cascade` when you are ABOUT TO
supersede an item that still has live (open) descendants: it performs the whole ripple —
re-open each live child under a new slug citing its predecessor, re-issue claims and
edges, write each resulting orphan's `reissued` disposition — in one witnessed pass, in
dependency order. The order is the point: done by hand, each step of the ripple mints new
orphans one level down (by design — the mechanism is closed under that recursion), and a
mis-ordered hand-walk leaves you resolving violations you created two steps earlier.
Honest limit: the cascade only handles the subtree below the item you name; edges INTO
the subtree from elsewhere still surface as orphans afterward and are yours to
`resolve-violation` individually, because no tool can know whether an outside edge should
follow the successor or die with the predecessor.

**Why is the fix a disposition act, not "supersede the whole subtree"?**
A subtree is not closed under reference, and a settled review cannot be honestly
re-issued (a new review row in the reviewer's name would forge their agency) — the full
reasoning, with the witnessed evidence, is the ADR-0014 consultation record at
[ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md](ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md).

**Why does the harness insist closed and reviewed items stay correctable at all?**
Because the record model this project imports requires it, independent of anyone's
preference: [the safety-critical-logging BRIEF](../law/briefs/safety-critical-logging/BRIEF.md)'s
invariant I3 (a correction is a new, linked entry that never obscures the prior state),
I7 (every discharged obligation carries the conditions under which it ceases to hold),
and the nuclear/aviation clusters' change-through-re-verification linkage (IEC 60880,
DO-178C) all demand that a close — and the reviews that discharged it — can be superseded
or lapse when their basis is defeated, append-only, with the defeat linked. The kernel
already delivers the core of this (superseding a close re-opens the item and re-surfaces
its review debt, witnessed in the consult above); s37's validity-bounded dispositions
extend the same discipline to violation answers themselves.

## What this page is not

This page is not an inventory (that is [ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md), where every
mechanism carries witnessed output or an honest UNWITNESSED mark), it is not a setup guide
([USER-GUIDE.md](../USER-GUIDE.md)), and it is not a promise that a recipe listed here is
enforced — where an entry says "declaration only," the enforcement genuinely does not
exist yet, and the cited spec names the stage that would build it.
