# Makespan-scheduled dispatch — what can honestly be guaranteed, and what cannot

Audience: an orchestrator (human or LLM) deciding how to dispatch a batch of independent work
units across parallel agent capacity, and anyone assessing whether "the schedule was computed by
a formal planner" is a claim this project can stand behind. This note answers one question
precisely: given `tools/makespan-scheduler/` (vendored 2026-07-14; see
[`tools/makespan-scheduler/PROVENANCE.md`](../tools/makespan-scheduler/PROVENANCE.md)) and this
project's own ledger, what is actually guaranteed about a dispatch order the scheduler produces,
and what depends on a human/agent judgment the scheduler cannot check?

**Provenance.** Maintainer directive, 2026-07-14 (dictated pre-sleep, verbatim in substance;
ledger work item `makespan-scheduler-vendoring`, `./led show` at the repository root reads it in
full): the scheduler should be vendored and recommended as a standing practice for large-scale
agentic workflows, "since Claude Code is essentially an infinite-server model of work — however
the ADR-0013-violating default inclination of many models makes them default to sequential work
scheduling." The maintainer separately asked, in an earlier session, whether this could be
**formalized as a guarantee** by **typing work-splits** (his belief: partially already done) and
**mandating** that dispatch follow a formal planner's output, with the work-split itself
**correct by counter-signatured review** — and named, verbatim, the scheduler's own limitation:
"for this particular tool, the output of the work units produce no dependents to be used in later
ones (independent-tasks makespan model)." This note is the honest disposition of that ask: what
is a real guarantee today, what remains a designed-but-unbuilt recommendation, and why the
counter-signature step is not optional.

## 1. What "makespan" means here, in plain words

A batch of work units ("jobs") is dispatched to parallel agent capacity. Two jobs **conflict** if
they touch the same resource (a file, in the common case) — they must not run at overlapping
times, or their edits could interleave destructively. The **makespan** is the completion time of
the last-finishing job: the wall-clock (or abstract-unit) cost of running the whole batch to
completion under those conflict constraints and, optionally, a cap on how many jobs may run at
once. `tools/makespan-scheduler/` computes a dispatch order — grouped into "batches" (waves that
can launch together) — that minimizes this completion time, using a CP-SAT constraint solver
(OR-Tools). Full model detail:
[`tools/makespan-scheduler/README.md`](../tools/makespan-scheduler/README.md).

## 2. What the scheduler itself actually guarantees

Precisely, and no further: **given a job list whose declared `resources` are a complete and
accurate account of every real conflict among the jobs, and an accurate `duration` estimate per
job**, the scheduler returns a schedule that (a) never runs two resource-conflicting jobs
concurrently, (b) never exceeds a declared `max_parallel` cap, and (c) is either proven minimal
(`optimal: true`) or, if a time limit was given and expired first, the best schedule found so far
— still fully valid, just not proven minimal (`optimal: false`, never silently presented as
optimal). This is a real, checked guarantee: 73 tests, vendored verbatim and re-run in place
(`tools/makespan-scheduler/PROVENANCE.md`), cover exactly these properties, including adversarial
input shapes (duplicate ids, non-positive/non-finite durations, astronomically large values,
`max_parallel` beyond the solver's safe domain — each rejected with a clean, attributed error
rather than a silent wrong answer or a raw crash).

**What this guarantee is conditional on, stated because a conditional guarantee presented as
unconditional is worse than none:** the solver optimizes over the model it is GIVEN. It has no
way to know whether a `resources` list under-declares a real conflict, or whether a `duration`
estimate is honest. A job list that omits a genuine shared resource produces a schedule that
LOOKS authoritative (a CP-SAT-proven-optimal, machine-computed answer) while recommending two
jobs run concurrently that, in reality, must not. **The scheduler cannot audit its own input's
fidelity to the real world; nothing in this tool tries to.**

## 3. The named limitation, stated as sharply as the maintainer stated it: no dependents

The model is an **independent-tasks** makespan problem: every job's `resources` list says what it
must not overlap with, and that is the ENTIRE inter-job relationship the model represents. There
is no notion anywhere in `tools/makespan-scheduler/` of "job B consumes job A's output" — a true
data dependency (B cannot even *start* meaningfully until A's result exists, not merely "B must
not run concurrently with A"). If a real batch of work has such a dependency and it is fed into
this scheduler as if it were merely a resource conflict (or, worse, omitted from `resources`
entirely because the author only thought in terms of "which files do these two jobs touch"), the
computed schedule can be **actively wrong** — it may schedule B to start before A's output exists,
because the solver has no representation of "before" in the data-flow sense, only "not
overlapping in time" in the resource-contention sense.

**This tool's honest scope, therefore, is a single, checkable precondition**: a batch of jobs is
eligible for makespan-scheduling only if the batch, as a whole, has **no dependency edges between
any two jobs it contains** — every job's inputs are already fully available before the batch
starts, and every job's output is consumed by nothing else in the same batch. A batch containing
even one true dependency is not this tool's problem to solve; it needs a different model (a DAG
scheduler, out of scope here) or manual sequencing of the dependent sub-chain, with only the
remaining independent jobs handed to this scheduler.

## 4. "We already have this in part" — what the ledger's typed work-split actually types today

The maintainer's belief that typed work-splits partially exist already is correct, precisely
scoped: `./led work open <slug> --parent <parent-slug>` and `led work depends <slug> <on-slug>`
([`kernel/lineage/s22-work-item-ledger.sql`](../kernel/lineage/s22-work-item-ledger.sql),
[`kernel/lineage/s28-work-parent-edge.sql`](../kernel/lineage/s28-work-parent-edge.sql)) give a work item a real,
kernel-typed position in a dependency/parent tree — `led work depends` is exactly a **declared
data-dependency edge** between two work items, and its presence is a machine-checkable fact, not
prose. But — stated as sharply as §3's limitation, because conflating the two would be the exact
mistake this note exists to prevent — **that edge types the DEPENDENCY topology; it does not type
the RESOURCE-CONFLICT topology the makespan scheduler needs.** `led work open`/`depends` has no
notion of "these two work items touch the same file"; `tools/makespan-scheduler/`'s `Job.
resources` has no notion of "this work item's *result* feeds that one." They are complementary,
not overlapping, typed facts about the same batch — and the missing mechanical link is named
honestly in §6 below, not glossed over.

**The one derivable, load-bearing consequence:** before a set of ledger work items is handed to
the scheduler as a batch, the sound precondition check is mechanical to STATE (whether it is
mechanical to RUN today is answered in §6): **no two items in the batch may have a `led work
depends` edge to each other.** An edge to something OUTSIDE the batch (an already-closed
prerequisite) is fine — the dependency is already discharged before the batch starts. An edge
WITHIN the batch means the batch violates §3's precondition and must not be scheduled as one
independent-tasks batch.

## 5. What "mandating dispatch follow the planner's output" means, and what it does not

The maintainer's ask was that a work-split, once declared correct, be **discharged according to
the scheduler's output** — the batches it computes, in the order it computes them — rather than
an orchestrating agent's own ad hoc sense of what to run next (the "default to sequential" lapse
named in the Provenance section above). This note adopts that as the **recommended discipline**:
once a job list clears §3's no-internal-dependents precondition and §6's counter-signature step,
the dispatch order is the scheduler's `batches` output, verbatim — not renegotiated by the
dispatching agent's own judgment about what "feels" parallelizable. If the declared resources or
durations change (a job is added, split, or a conflict is discovered late), the schedule is
**re-computed**, never hand-patched — the scheduler is cheap to re-run (§2's 73-test suite proves
it is sound to call repeatedly on a changed model) and a hand-patched schedule is exactly the
kind of unverified claim [ADR-0013 Rule 5](../law/adr/0013-execution-integrity.md#rule-5--verify-the-artifact-not-the-claim)
exists to forbid.

**What this is NOT:** a claim that every batch of work benefits from this. A small batch, a batch
with no real resource contention, or a batch where the dispatching agent's judgment and the
solver's output would coincide trivially gains little from the ceremony below — the discipline
earns its cost on a genuinely large, genuinely contention-heavy batch (the "large-scale
workflows" the maintainer named), not as a ritual applied to every three-file edit.

## 6. The counter-signature requirement — why the scheduler's guarantee needs an independent human step

§2's guarantee is conditional on the job list being an honest model of reality; §3 and §4 name
exactly the two ways it can be dishonest without anyone noticing (an under-declared resource
conflict; a true data dependency mistaken for, or hidden inside, a mere resource conflict). The
scheduler cannot check either — no code can verify that a `resources` list is COMPLETE, because
completeness is a claim about the real world the model does not have access to. This is the same
structural blindness [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
and [ADR-0014](../law/adr/0014-executor-second-opinion.md) name elsewhere in this corpus: **the
faculty that authored a decomposition is the faculty most likely to have missed what it
missed** — an agent that split a batch of work into jobs and declared each job's resources is
poorly positioned to notice, by re-reading its own list, the dependency or conflict it failed to
see the first time.

**The requirement, stated plainly:** before a job list is treated as ready for scheduling (§5),
an **independent** reviewer — not the agent that authored the decomposition — countersigns two
specific claims: (a) every real resource conflict among the batch's jobs is present in some
job's `resources` list (§2's precondition), and (b) the batch contains no internal dependency
(§3/§4's precondition — cross-checked, where the batch corresponds to ledger work items, against
`led work depends` edges). This project already has the exact machinery for an independent,
provably-distinct countersign: `led review <entry-id> <verdict> <independence> <statement>` with
`independence` at `technical` or stronger, which the kernel REFUSES unless the reviewing write
came from a stamp-distinct invocation from the one being reviewed (`led --recent`'s own
documentation, this repository's `led.tmpl` header) — the identical mechanism
[ORCH-CAPABILITIES.md](../ORCH-CAPABILITIES.md)'s "A second pair of eyes that has to be real —
and now session-aware, not just agent-aware" entry already describes as witnessed and enforced
for ordinary ledger rows, applied here to a job-list decomposition instead. `led
obligate <scope> <assigned-by> <obliged-actor>` additionally lets an orchestrator make this
countersign a standing, checkable OBLIGATION on whoever authors decompositions routinely
(`led review-gap` then surfaces an unreviewed decomposition as
[`review_gap`](../GLOSSARY.md#review_gap) debt), rather than a one-off request that is easy to
forget.

## 7. Honest status: designed discipline, not a built or wired mechanism

Per [ADR-0013](../law/adr/0013-execution-integrity.md)'s own Rule 1 (a claim of completion is
worth nothing until the artifact shows it) and
[ADR-0011](../law/adr/0011-mechanization-discipline.md)'s enforcement-surface honesty:
**nothing in this repository currently refuses a
dispatch that skips §6's countersign, or one that violates §3/§4's no-internal-dependents
precondition.** This note documents a RECOMMENDED practice, review-only and self-applied exactly
like the corpus's other execution disciplines
([ADR-0013](../law/adr/0013-execution-integrity.md), [ADR-0014](../law/adr/0014-executor-second-opinion.md))
— an orchestrator adopts it by choice and by discipline, not because a gate enforces it today. A
sound future mechanization, named here rather than silently deferred (this commission is
Sonnet-executable scope: vendor + recommend + honestly-scoped design note, not a new gate): a
pre-dispatch check that (1) rejects a job batch whose ledger work items carry a `led work
depends` edge to another item in the same batch (§4's mechanical precondition — checkable today
against the kernel, unbuilt), and (2) refuses to treat a job list as schedulable until a
`technical`-or-stronger `led review` row countersigning it exists (mirroring the existing
`review_gap` machinery §6 cites, applied to a new obligation scope rather than a new kernel
table). Both are ordinary `gates/` scripts and a new `led obligate` scope — not a kernel lineage
change, so CLAUDE.md's kernel/law/engine-authoring ceremony does not apply to building them —
filed here as the concrete next step, not built in this pass.

## What this note does NOT claim

- **Not that every LLM-dispatched batch of work is now provably safe to parallelize.** The
  guarantee in §2 is real but narrow — it is a guarantee about the SOLVER given an honest model,
  never a guarantee that any given model handed to it IS honest. §6's countersign is the only
  thing standing between "the schedule is provably optimal" and "the schedule is provably optimal
  for a batch that may not describe reality."
- **Not that the no-dependents limitation is a defect to be fixed.** It is the tool's honestly
  stated scope (README.md, "The problem, precisely"), inherited here unchanged — extending the
  model to a true DAG scheduler is a different, larger tool this note does not propose building.
- **Not a mandate on every task, however small.** §5's "not a ritual for every three-file edit"
  stands; this discipline is for the large-scale, contention-heavy batches the maintainer named.
- **Not yet enforced.** §7 is explicit: this is a recommended discipline with named, unbuilt
  mechanization candidates, not a live gate.
