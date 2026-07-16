# Declared pipeline workflows (v0) — what this grammar covers, and what it does not

This directory holds candidate TOML declarations of orchestration-pipeline shapes this project
and its downstream adopters have actually run, plus the grammar those candidates transcribe into
and the tool that checks a declaration for structural well-formedness. It exists to answer one
question for a reader who has not seen the exploration that produced it: **what does a v0
"pipeline DSL" file actually say, what will `tools/workflow_check.py` accept, and what will it
refuse?** This page is that answer, written to be readable with none of the authoring session's
context, per [law/adr/0017-the-zero-context-reader.md](../../law/adr/0017-the-zero-context-reader.md).

Two artifacts this page cites repeatedly are worth naming up front, since nothing below defines
them again: **"the ledger"** is this project's append-only Postgres record of decisions, reviews,
and work-item state, read and written through the `./led` command-line tool at the repository
root (a "ledger row," "ledger item," or "close record" below is one entry in that record,
addressable by its integer id via `./led show <id>`); **"blessed"** (as in "blessed resource" /
"blessed-tier") names a resource formally registered at a specific trust tier via a
`resource:`-prefixed ledger decision row plus a matching entry in a `CLAUDE.md` RESOURCES
section — the convention the autoharn-panel deployment (a separate downstream checkout of this
same tooling, at `~/w/vdc/1/experience/autoharn-panel`, referenced throughout this page by its
own ledger row numbers) establishes in its own ledger rows 16/36-40 (cited in Specimen A below)
for `makespan-scheduler`; this repository's own `CLAUDE.md` does not yet carry a RESOURCES
section of its own.

## Where this comes from

The governing document is `design/FABLE-PIPELINE-DSL-EXPLORATION.md` (authored by Fable — this
project's primary AI-collaborator authoring model, distinct from the Sonnet-tier models that
execute most of its work — 2026-07-16, exploration-grade; not itself committed to this
repository's main checkout at the
time this page was written, per its own status line; read it at that path in a checkout that has
it, or ask the maintainer). That document proposes a small declared form for the orchestration
pipelines the maintainer currently authors as per-turn prose, names exactly four fields it should
carry, and asks for at least three real, already-run specimens to be transcribed into candidate
declarations before any grammar or tool is built. This directory is that transcription plus the
resulting v0 grammar and checker — the exploration document's own "Next steps" §1–3 discharged.

## The four fields, and nothing else

A v0 workflow declaration is a TOML file with **exactly** these four top-level tables, matching
the exploration document's own four-item list verbatim:

1. **`[[phases]]`** — an array of named stages. Each entry has a `name` (string, unique within
   the file) and an optional `depends_on` (an array of other phases' names). The `depends_on`
   edges must form a DAG — no phase may (directly or transitively) depend on itself.
2. **`[roles.<phase-name>]`** — one table per phase, naming which model tier plays which of three
   verbs the exploration document names: `authors`, `reviews`, `implements`. A phase needs at
   least one of the three filled in; it does not need all three (a review-only phase, for
   example, may carry only `reviews`).
3. **`[convergence.<phase-name>]`** — one table per phase with two required strings: `done`
   (what "done" means for this phase) and `escalation_event` (the typed event that routes to the
   maintainer when the phase does not converge — named even when a given specimen never actually
   triggered it, because the field declares what WOULD happen, not a log of what did).
4. **`[landing_zones.<phase-name>]`** — one table per phase with a `zone` string naming where
   that phase's deliverable lives after the session ends. Every phase in this grammar is treated
   as deliverable-producing (phases are, by the exploration document's own definition, "named
   stages" that hand something to the next stage or to the record), so every phase needs one.

No other top-level key is legal. `tools/workflow_check.py` refuses one loudly and by name rather
than silently ignoring it — seeded by the same lesson this project already learned from
`led.tmpl` (this repository's template for the `led` ledger command's own flag parser)'s own
unknown-flag handling: an unenforced typo'd or speculative field is a silent scope leak, not a
convenience.

## What v0 deliberately does NOT cover

Quoting the governing exploration document's own "What it deliberately is NOT" section verbatim,
because the boundary is the point, not an afterthought:

> - **Not a workflow engine.** No conditionals, no loops, no expressions — the only branch a
>   declaration may contain is the typed escalation event of a convergence rule. Anything
>   Turing-shaped is the orchestrator's job, on the record, per turn.
> - **Not a scheduler.** Time and resource assignment stay with `tools/makespan-scheduler/` … the
>   DSL declares order, never dates.
> - **Not speculative.** The vocabulary grows ONLY from harvested specimens — a field enters the
>   grammar when a real deployment's real shape needed it. … No field ships because it might
>   someday be wanted.

Concretely, that means this grammar has **no** field for: retry loops or bounded round counts (a
`while` loop with a round cap, as Specimen C below actually runs, stays orchestrator/script code —
only the typed escalation event it eventually raises is declared); conditionals or branching logic
beyond the single escalation branch each convergence rule carries; scheduling (dates, worker
counts, concurrency caps — that is `tools/makespan-scheduler/`'s job, wired at the seam named by
ledger item `makespan-precedence-export`, not this DSL's); or any field not already demanded by a
real, already-run specimen.

## The validator

`tools/workflow_check.py <path.toml> [<path.toml> ...]` (stdlib only — `tomllib`, no third-party
dependency, no lazy imports per `CLAUDE.md`'s standing edict and `gates/no_lazy_imports.py`).
Exits 0 with a one-line `OK` summary per valid file; exits 1 and prints one `REFUSED` line per
defect, across every file given in one run, for four refusal classes plus a handful of narrower
shape checks in the same four fields (see the tool's own module docstring for the full list):

1. a dependency **cycle** among phases;
2. a phase with **no role**;
3. a phase (all phases are deliverable-producing in this grammar) with **no landing zone**;
4. an **unknown top-level key**.

Every one of these was exercised against a mutant fixture during this build; see the ledger work
item `pipeline-dsl-v0`'s close record for the witnessed output of all four refusals plus all four
specimen files below passing clean.

## The four transcribed specimens

The table below is this directory's index: each row names one transcribed TOML file, the
letter ("Specimen A/B/C/D") the "Known misfits" section below uses to refer back to it, what
real run it was harvested from, and how many phases it declares. Each file's own header comment
names its exact source rows/lines and any transcription judgment calls made along the way.

| Specimen | File | Source | Phases |
| --- | --- | --- | --- |
| A | `panel-msched-resource-provisioning.toml` | autoharn-panel ledger rows 14-47 (provisioning makespan-scheduler as a blessed resource) | 3 |
| B | `panel-ui-agentic-prereqs-decomposition.toml` | autoharn-panel ledger rows 48-85 (decomposing and implementing two UI prerequisites) | 5 |
| C | `panel-consult-cycle-template.toml` | autoharn-panel's hand-built `scripts/cycle-workflow-template.mjs` | 3 |
| D | `autoharn-builder-wave.toml` | this repository's own 2026-07-16 "builder-wave" shape — a wave of parallel Sonnet builder agents, each in its own isolated worktree (this very build is an instance of it) | 4 |

## Known misfits

The build task that produced this directory named a specific instruction: where a harvested shape
does not fit the four-field grammar cleanly, record the misfit verbatim rather than forcing it —
that is harvest data, not a defect in this page. Four are recorded here.

**1. The build task's own row-33 citation does not point at a compound pipeline.** The task (and,
apparently, the governing exploration document's "The problem" section, which names "rows 33, 42,
and 57 — each a compound orchestration pipeline") pointed at ledger row 33 of the panel deployment
as one of three pipeline specimens. Read directly (`./led show 33` in
`~/w/vdc/1/experience/autoharn-panel`), row 33 turns out to be a disclosure of an accidental
artifact (a stray `--help` argument that landed as row 24's statement text, filed under the
ledger's `snag` row-kind — the taxonomy value this project's ledger uses for exactly this class
of "something went wrong, disclosed rather than hidden" note) — not a pipeline decomposition of
any kind, compound or otherwise. Rows 42 and 57 DO sit inside real compound
pipelines (the msched-* three-item decomposition and the ui-agentic-prereqs five-item
decomposition, respectively), transcribed as Specimens A and B above — but row 33's neighborhood
(rows 14-47) is the SAME pipeline row 42 belongs to, not a distinct third specimen. This directory
therefore has four specimens transcribed from three distinct sources (A, B, C, D above) rather
than three from the three cited row numbers directly; the discrepancy between the exploration
document's row-33 description and the row's actual content is recorded here rather than quietly
worked around, since it may mean a different row was intended, or the description itself needs a
correction upstream.

**2. Specimen C's compliance-review/countersign phase is a bounded retry LOOP, which v0 cannot
express as a mechanism.** `scripts/cycle-workflow-template.mjs` runs `while (true) { ... if (round
>= MAX_COMPLIANCE_ROUNDS) break }`, re-prompting each round with every prior round's review and
countersign text serialized into the next prompt, capped at 2 rounds. This is exactly the shape
the exploration document's "Not a workflow engine" clause rules out ("no loops"). What v0 CAN and
does express is the shape the loop converges toward or escalates from — the `compliance-review`
and `compliance-countersign` phases, and the `non-converging-review-loop` escalation event the
loop raises on non-convergence — never the loop's own retry mechanics. Any future v0-consuming
orchestrator would still need to write that loop by hand, in code, exactly as the template already
does; the DSL declares what the loop is FOR, not how it iterates.

**3. Specimen C's `compliance-review` and `compliance-countersign` phases have no durable landing
zone.** The template holds both phases' output in an in-memory JavaScript object
(`complianceRounds`) and returns it to the caller at the end of the run; nothing in the template
writes it to a file or a ledger. This grammar requires every phase to declare a landing zone (all
phases are deliverable-producing by definition), so the specimen file fills the field honestly
with prose describing the in-memory-only reality rather than inventing a persistent location that
does not exist in the source — the field is satisfied, but by an honest declaration of absence,
not by forcing a fit. Contrast this with ADR-0017's own fresh-context audit loop (a close relative
of this same review/countersign shape), which DOES mandate a persistent landing zone
(`attestations/doc-legibility-attestations.jsonl`) — the template predates that discipline and
simply never gained one.

**4. Same-file contention among sibling phases has no field in this grammar.** Specimen B's source
rows (79-81) record findings that two dependency-free sibling work items nonetheless edit the same
file (`panel-profile-storage` and `panel-readonly-lock` both touch `backend/config.py`; several
other such pairs are named). This is real information a scheduler needs (the finding rows say so
explicitly: a scheduler reading only the `depends_on` graph would see the pair as safely
concurrent) — but it is not order, not a role, not a convergence rule, and not a landing zone, so
it does not fit any of v0's four fields. Per the exploration document's "Not speculative" rule,
this is not patched by inventing a fifth field on spec; it is recorded here as a real, witnessed
gap for the eventual `makespan-precedence-export` seam (which already owns resource-conflict
modeling, per `tools/makespan-scheduler/`'s own blessed-resource declaration in the panel's
`CLAUDE.md`) to pick up if and when a second specimen needs it too.
