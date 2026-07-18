# FABLE-PIPELINE-DSL-EXPLORATION — a declared form for reusable orchestration workflows

This document explores whether the recurring orchestration workflows the maintainer
currently authors as per-turn prose should become a small declared form (a "DSL" —
domain-specific language — in a plain data syntax such as TOML) that the harness can
check and reuse. It is written for the maintainer (who ruled the exploration should
happen) and for whoever later authors the build spec. It answers one question: what
would this DSL be, and — just as deliberately — what would it not be?

Status: AUTHORED 2026-07-16 by [Fable](../../GLOSSARY.md#post-fable-law) (the
maintainer's primary AI-collaborator authoring model), exploration-grade. It proposes a direction and a
method, not a buildable surface; a separate build spec, ratified on its own, must
precede any code. Provenance: the maintainer's ruling on question Q3 of
[MAINT-DECISION-QUEUE-2026-07-16](MAINT-DECISION-QUEUE-2026-07-16.md) ("Reusable
orchestration-pipeline primitive: pursue or park?"), recorded 2026-07-16 as row
1202 of this project's ledger (the external Postgres record `./led` reads, not a
file in this git tree), quoting the maintainer verbatim: "it probably
warrants a very easy DSL; I'm competent enough to declare the shape in prose as you
saw, and can translate it to toml/json/...something else; we can harvest the shapes
and compile into useful shapes!").

## The problem

The maintainer — a non-programmer operator — repeatedly authors orchestration policy
as natural-language paragraphs, one conversation turn at a time: which model drafts,
which reviews, which implements; how phases order topologically; what happens when a
review does not converge. Three witnessed specimens live in the panel's ledger (the
panel is the `autoharn-panel` deployment at `~/w/vdc/1/experience/autoharn-panel`, a
downstream adoption of this harness): rows 33, 42, and 57 — each a compound
orchestration pipeline declared in prose and decomposed live by the session's
orchestrator. The cost is twofold: the same shapes are re-declared from scratch each
time, and nothing checks them. The panel's orchestrator eventually hand-built its own
reusable template (`scripts/cycle-workflow-template.mjs` in the panel repo, committed
there precisely so it would survive the session) — a deployment inventing, from
scratch, the primitive the harness lacks.

## What the DSL would be

The DSL would be a declaration, in one small file per workflow, of exactly four
things:

1. **Phases** — named stages with their topological ordering (which the harness can
   check for cycles, the same acyclicity discipline this project's own ledger
   already carries on its dependency edges).
2. **Roles** — which model tier authors, which reviews, which implements, per phase
   (the standing delegation contract in [CLAUDE.md](../../CLAUDE.md) stays the outer
   bound; a declaration can be stricter than the contract, never looser).
3. **Convergence rules** — what "done" means per phase, and the typed escalation
   event (for example a non-converging review loop) that routes to the maintainer
   when it is not reached. Escalation on typed events only, never on self-assessment
   — the same rule the delegation contract already states.
4. **Landing zones** — where each phase's deliverable lands so it outlives the
   session. This field mechanically discharges the lesson of ledger item
   `dispatch-deliverable-landing-zone` (a deployment lost a full audit cycle's
   evidence to an ephemeral scratchpad because no dispatch surface asked the
   question).

A declared workflow is then a typed artifact in the sense of
[ADR-0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md): the
harness can refuse a malformed plan (a cycle, a phase with no role, a deliverable
with no landing zone) before any agent is dispatched, instead of discovering the gap
mid-run.

## What it deliberately is NOT

- **Not a workflow engine.** No conditionals, no loops, no expressions — the only
  branch a declaration may contain is the typed escalation event of a convergence
  rule. Anything Turing-shaped is the orchestrator's job, on the record, per turn.
- **Not a scheduler.** Time and resource assignment stay with
  `tools/makespan-scheduler/` (a sibling scheduling tool, vendored as a submodule)
  and the seam work ruled under question Q4 of the same
  [decision queue](MAINT-DECISION-QUEUE-2026-07-16.md) (ledger item
  `makespan-precedence-export`); the DSL declares order, never dates.
- **Not speculative.** The vocabulary grows ONLY from harvested specimens — a field
  enters the grammar when a real deployment's real shape needed it. (This is the
  maintainer's standing posture of harvesting durably-shaped methods from live
  deployments before designing for them; the same Q3 ruling cited above chose
  "pursue AND keep harvesting" over designing from one specimen.) No field ships
  because it might someday be wanted.

## Method: harvest, then compile

The maintainer's own sketch is the method. Concretely: collect declared-in-prose
shapes from deployments (the three panel rows above; the panel's hand-built template;
this repository's own builder-wave pattern of 2026-07-16 — parallel worktree builders,
per-item witnesses, orchestrator merges); transcribe each into a candidate TOML
declaration; where the specimens disagree, that disagreement IS the design question,
brought to the maintainer as a prepared fork. When at least three specimens
transcribe cleanly into one grammar, that grammar becomes the build spec's input.

## Next steps

1. Transcribe the three panel specimens plus this repository's builder-wave shape
   into candidate declarations (an orchestrator task, no new code).
2. Bring transcription disagreements to the maintainer as prepared forks.
3. Author the build spec (grammar, validation verb, refusal texts) for ratification.
   Until then, nothing in the operator surface changes.
