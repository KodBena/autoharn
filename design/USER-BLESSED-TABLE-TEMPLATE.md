# The blessed-table template — filling your project's Capability Registry

Audience: adopter

This page is a **template you fill in**, not a reference you merely read. Filling it gives an
agent working in your project a task-shape → blessed-tool table it can reach for by reflex,
instead of you re-explaining which tool to use every session — the piece
[Pillar 1](../GLOSSARY.md#pillar-1) (the Capability Registry) needs to exist before it can work.
("Task-shape" — the category of problem a tool solves, such
as "finite enumeration" or "convex allocation" — is the thread this whole page is organized
around; every row below names one.) If you are adopting autoharn — cloning it, or running
`bootstrap/new-project.sh` / `bootstrap/track-work.sh` against your own project directory — this
is the page you edit once at adoption, then again whenever you bless or mandate a new tool. It
assumes no prior context: not this repository's design history, not the session that produced
this template, nothing but what is written here and what it links to.

Two things this page is **not**: it is not the mechanism that *declares* a resource (that is
`./led decision "resource: ..."` — `./led` is this project's ledger CLI, a live ledger-writing
act — the conversion, [below](#the-conversion-a-filled-row-becomes-one-led-command), shows the
exact command a filled row converts to) and it is not this repository's own resource table
(autoharn declares nothing for you — see
"[the canonical residents](#the-canonical-residents-this-maintainers-stack-worked-examples)"
below on why the examples here are marked as such). It is the durable, human-edited *source* you
fill once and re-derive declarations from, the same relationship a spreadsheet has to the
database rows it seeds.

Coined terms below link to their definitions in [GLOSSARY.md](../GLOSSARY.md#pillar-1) on first
use, per this project's [Stand-Alone Principle](../GLOSSARY.md#project) — chase any link if a
word does not read as plain English.

## Background: what a resource declaration is, in one paragraph

[ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) (§2) specifies how your project
declares a resource — a tool, service, solver, or library — so a session hydrating with
`./pickup` — the scaffolded resume command an agent runs at the start of a session, this
project's other CLI verb alongside `./led` — sees it without you repeating yourself. Stage 1
(what is built today) uses your project's ordinary ledger rows of `kind` `decision` (every
ledger row carries a `kind` field naming what sort of act it records; `decision` is one of
several values that field takes) with a `resource:` statement-prefix convention — no kernel
schema change. A resource carries six fixed fields (NAME, CLASS, REACH,
WHAT-IT-PROVES, GUIDANCE, TIER) and a TIER of `available` (on record, no endorsement),
`blessed: <task-shape>` (the recommended reach for that task shape),
`mandated: <task-shape>` (required for that shape, and countersign-checked — see
["the mandated-tier review convention"](#the-mandated-tier-review-convention) below), or
`forbidden: <task-shape>` (this tool must NOT be reached for, for that shape —
[ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md) §3 added this fourth tier
to complete the MAY/SHOULD/MUST/MUST-NOT deontic register the first three already three-quarters
covered; it is checked by the `./audit --resources` audit surface once that surface ships — a
witnessed use against a forbidden entry is a violation — never by a write-time block, which that
spec's §7 names as deliberately out of scope for now). The table
in this page is organized around those same six fields, plus one more your project does not
declare to the ledger but that helps you *choose* a tool: where it sits on the ordering
[escalation ladder](#the-escalation-ladder-column) ORCH-SPEC-RESOURCE-REGISTRY.md §5 names.

## The table

Each row below is one candidate resource. The first seven rows are **EXAMPLES — this
maintainer's own stack** (autoharn's own maintainer, the "canonical residents" ORCH-SPEC-
RESOURCE-REGISTRY.md §2 enumerates from his own inventory), included as **worked examples of how
to fill a row correctly**, never as a claim that your project has, needs, or has declared any of
them. Delete them, or leave them as reference, and add your own rows in the blank template below.

### The canonical residents (this maintainer's stack — WORKED EXAMPLES)

| NAME | CLASS | REACH | WHAT-IT-PROVES | GUIDANCE | TIER | RUNG (ordering ladder) |
|---|---|---|---|---|---|---|
| MIP-SCIP | solver | `binary: scip` / `import: pyscipopt` | exact optimum or infeasibility proof for mixed-integer programs | reach for exact combinatorial optimization with linear/integer structure; not for convex-continuous-only problems (use cvxpy) or pure boolean satisfiability (use Z3) | available | rung 3 |
| cvxpy | library | `import: cvxpy` | global optimum proof for convex allocation problems | reach for convex, continuous resource-allocation problems; not for combinatorial/integer structure (use OR-Tools/MIP) | available | rung 3 |
| OR-Tools | library | `import: ortools.sat.python.cp_model` | finite-enumeration / exact constraint-satisfaction search proof | reach for finite enumeration and combinatorial constraint satisfaction — the maintainer's hyperparameter-enumeration precedent, generalized; not for continuous convex problems | available | rung 3 |
| Z3 | solver | `import: z3` (the `z3-solver` package) | satisfiability proof (SAT/SMT), or a concrete counterexample | reach for feasibility questions and logical/arithmetic constraint satisfaction; not for objective optimization at scale (use MIP/OR-Tools) | available | rung 3 |
| clingo | binary | `binary: clingo`; programs under `engine/lp/` | stable-model / answer-set proof — auditable enumeration of every model satisfying the declared rules | reach for non-monotonic reasoning, supersession, and auditable enumeration — already this project's house engine; ORCH-SPEC-RESOURCE-REGISTRY.md §5 stage 2's ordering-violations checker is built here | `mandated: ordering-violations-checking` (EXAMPLE — the tier stage 2 will actually declare) | rung 2 |
| tsort | binary | `binary: tsort` (POSIX coreutils) | a topological order over a DAG, or a cycle if none exists | reach for simple pairwise precedence with no arithmetic or resource dimension; escalate to clingo/Z3/OR-Tools the moment a constraint gains one | available | rung 2 |
| redis | service | `tcp://<host>:6379` (or your deployment's own connection string) | nothing provable — an ephemeral key/value cache or queue, not an audit-trail store | reach for ephemeral state or coordination only; never for durable ledger data, that is the ledger's own job | available | n/a |
| QEUBO (example per-project backend) | backend | `https://<this maintainer's QEUBO endpoint>` | preference-optimization result for this maintainer's own experiments | this maintainer's own project-specific backend — the living specimen ORCH-SPEC-RESOURCE-REGISTRY.md §1 names ("every recent commission hand-declares it because there is nowhere structured to declare it once"); **substitute your own project's backend here, this exact row is not yours to adopt** | available | n/a |

### Your project's rows (blank template — copy a row per resource you bless or mandate)

| NAME | CLASS | REACH | WHAT-IT-PROVES | GUIDANCE | TIER | RUNG (ordering ladder) |
|---|---|---|---|---|---|---|
| *(e.g. your-solver-name)* | *(solver \| service \| backend \| binary \| library)* | *(endpoint, binary path, venv, or import)* | *(one clause: "feasibility → this", "auditable enumeration → this")* | *(when to reach for it, when not to)* | *(available \| blessed: <task-shape> \| mandated: <task-shape> \| forbidden: <task-shape>)* | *(rung 1 trivial / rung 2 tsort-or-ASP / rung 3 Z3-or-OR-Tools / n/a)* |

### The escalation ladder column

ORCH-SPEC-RESOURCE-REGISTRY.md §5 names three rungs for **discharging an ordering constraint**
(a `work depends` edge, or the `constraint:` convention below) once it is declared and checked:
trivial orderings need no tool (**rung 1**); pure precedence at scale reaches for `tsort` or a
ten-line ASP enumeration (**rung 2**); arithmetic or resource-constrained orderings reach for
Z3 or OR-Tools, with their solver output committed as the auditable schedule artifact
(**rung 3**). The RUNG column above is not one of the six fields a `resource:` declaration
carries to the ledger (it is not part of the [conversion](#the-conversion-a-filled-row-becomes-one-led-command)
below) — it is a *choosing* aid: when your task is "put these things in order," read this column
to pick the cheapest tool that actually proves what you need, rather than reaching for Z3 out of
habit on a problem `tsort` already solves.

## The statement grammars

This section is the one documented home for both grammars below — the two parsers that
actually read them each point back here rather than restating a grammar a second time, but
they are NOT the same parser (corrected 2026-07-12, a hazard met in reach while building
[stage 2](ORCH-SPEC-RESOURCE-REGISTRY.md#8-implementation-routing-and-witness-plan): this
section previously claimed both grammars were parsed by `./pickup`'s RESOURCES section, which
was true only of `resource:`). `./pickup`'s RESOURCES section
(`bootstrap/templates/pickup.tmpl`) parses `resource:` rows only, for display at session
hydration. `constraint:` rows have no `./pickup` display surface — they are read by the
[stage 2](ORCH-SPEC-RESOURCE-REGISTRY.md#8-implementation-routing-and-witness-plan)
ordering-violations checker (`engine/ordering_edb.py` / `engine/ordering_floor.py`, wired into
`./audit --ordering`), which is a report an operator RUNS, not something `./pickup` shows
automatically. If a `./pickup` display surface for declared `constraint:` rows is ever wanted,
that is unbuilt, forward work — filed, not built.

### `resource:` — declaring one Capability Registry entry

```
resource: <NAME> | <CLASS> | <REACH> | <WHAT-IT-PROVES> | <GUIDANCE> | <TIER>
```

The six fields go in this exact order, separated by ` | ` (space-pipe-space) — the same order as
the table's first six columns above — so a filled row converts mechanically (next section). `CLASS`
is one of `solver | service | backend | binary | library`; `TIER` is one of
`available | blessed: <task-shape> | mandated: <task-shape> | forbidden: <task-shape>`. Copy-paste
example (the OR-Tools row above, promoted to `mandated` for a hyperparameter-enumeration task
shape):

```sh
./led decision "resource: OR-Tools-CP-SAT | library | import:ortools.sat.python.cp_model | finite enumeration -> exact hyperparameter search proof | use for hyperparameter enumeration over heuristic search; discharge evidence = committed declarative model file | mandated: hyperparameter-enumeration"
```

A `forbidden` example — declaring a tool this maintainer's project has decided must NOT be
reached for, for a named task shape (the MUST-NOT reads exactly like the two above, just with a
prohibition instead of an endorsement):

```sh
./led decision "resource: legacy-eval-script | binary | binary:legacy_eval.sh | nothing provable -- an unmaintained script with no test coverage | superseded by MIP-SCIP; do not reach for it even under time pressure | forbidden: hyperparameter-enumeration"
```

### `constraint:` — declaring an ordering constraint beyond a plain `work depends` edge

```
constraint: <RELATION> <slug-1> <slug-2> [<slug-n>...]
```

`RELATION` is `precedes` (conditional precedence — `slug-1` must close before `slug-2` closes,
a stronger or differently-scoped claim than the plain `work depends` edge) or `excludes` (mutual
exclusion — `slug-1` and `slug-2` may not both be open/claimed at once). This is the v1 vocabulary
ORCH-SPEC-RESOURCE-REGISTRY.md §5 opens ("conditional precedence, mutual exclusion" are its own
named examples); a third relation is added the same way — a new `RELATION` word in this same
convention, no schema change — the first time a real need is witnessed, per this project's
[Mechanization Discipline](../GLOSSARY.md#mechanization-discipline) (measure the recurrence,
then mechanize it, never speculatively). Stage 1 ships the convention and this documentation
only; the checker that actually flags a violated `constraint:` row is
[stage 2](ORCH-SPEC-RESOURCE-REGISTRY.md#8-implementation-routing-and-witness-plan), unbuilt as
of this page. Copy-paste examples:

```sh
./led decision "constraint: precedes decompose-schema implement-consumer"
./led decision "constraint: excludes migrate-live rollback-live"
```

## The conversion: a filled row becomes one `led` command

Fill one row of the table above, then join its six cells with ` | ` and prefix `resource: ` —
that string is the whole statement. Worked example, the OR-Tools row converted exactly as shown
in the grammar section above:

| NAME | CLASS | REACH | WHAT-IT-PROVES | GUIDANCE | TIER |
|---|---|---|---|---|---|
| OR-Tools-CP-SAT | library | `import:ortools.sat.python.cp_model` | finite enumeration -> exact hyperparameter search proof | use for hyperparameter enumeration over heuristic search; discharge evidence = committed declarative model file | mandated: hyperparameter-enumeration |

```sh
./led decision "resource: OR-Tools-CP-SAT | library | import:ortools.sat.python.cp_model | finite enumeration -> exact hyperparameter search proof | use for hyperparameter enumeration over heuristic search; discharge evidence = committed declarative model file | mandated: hyperparameter-enumeration"
```

Run that from your project's own root (the directory `./led` was scaffolded into), not from
autoharn's own checkout — per
[ORCH-SPEC-RESOURCE-REGISTRY.md §2](ORCH-SPEC-RESOURCE-REGISTRY.md#2-declaration--resource-rows-on-the-deployments-own-ledger)'s
boundary-hygiene rule, a resource is declared on **your** deployment's ledger, never in an
upstream autoharn file. A mandated-tier
declaration is commissioning-grade (it obliges a review discipline on whoever's work it governs
— next section), so signing it — FULL mode from your own terminal, or SIGNED mode with a
detached GPG signature — is apt; see
[USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) for both ceremonies. Once declared,
`./pickup`'s RESOURCES section shows it on the very next hydration, tier-sorted with `forbidden`
entries first, then `mandated`, then `blessed`
([ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md) §3: a prohibition outranks
a mandate for a reader's attention) — no separate "publish" step.

## The mandated-tier review convention

A `mandated: <task-shape>` declaration is a promise with teeth: work of that shape is not merely
encouraged to use the declared tool, it is **checked**. Stage 1 builds this checking with the
kernel machinery your project already has (the "kernel" is this project's write-time enforcement
layer — the schema, triggers, and checks the ledger itself runs on every write) — `countersign_obligation` / `review_gap`
(`bootstrap/templates/led.tmpl`'s own `led obligate` and `led review` documentation is the one
home of the underlying mechanism; this section composes it for the mandated-tier case, it does
not re-explain it) — never a new kernel column (that is deferred to
[stage 3](ORCH-SPEC-RESOURCE-REGISTRY.md#8-implementation-routing-and-witness-plan), on witnessed
need).

Three things a mandated declaration needs to actually be checked, not merely advertised:

1. **Name an EVIDENCE SHAPE in the GUIDANCE field** — the checkable artifact that proves the
   discipline was followed: a committed declarative model file, keys in a store matching a
   stated prefix, or a DerivationRecord (the solver-run provenance record this project's engine
   layer banks for every solver invocation). The OR-Tools example above names one: "discharge
   evidence = committed declarative model file."
2. **Obligate the principal who does mandated-shape work**, once, per your project:
   `./led obligate <scope> <assigned-by-principal> <obliged-actor-principal>` — see `led.tmpl`'s
   own comment for the full direction warning (getting `assigned-by`/`obliged-actor` backwards
   is the recurring mistake it exists to foreclose). Worked example: `./led obligate
   mandated-tool-review commissioner author` obliges every ledger row `author` writes from then
   on to carry a distinct-principal countersign or show up as debt.
3. **Countersign the mandated-shape work item's close, citing the evidence shape** — a distinct
   principal (never the author of the row under review — the kernel's segregation-of-duties
   check refuses same-actor countersigns unconditionally) runs `./led review <entry-id> <verdict>
   <independence> "<statement citing the evidence shape, present or absent>"`. **The reviewer
   verifies the ARTIFACT, never the narrative** — this project's blunt, maintainer-witnessed
   reason: implementers "take undue license and lie about what they have done"
   (ORCH-SPEC-RESOURCE-REGISTRY.md §4). Until reviewed, `./led review-gap` shows the row as
   outstanding debt — a mandated-shape close with no evidence-citing review is visible, never
   silent.

Read `led obligate`'s own comment before using it — in particular its documented **known
over-catch**: once a principal is obliged, `review_gap` counts *every* uncountersigned row that
principal writes from then on, of any kind, not only the mandated-shape ones. Scope your
obligation narrowly (a principal who does only mandated-shape work, or a project small enough
that the over-catch is cheap to clear) until a scoped `task_type` attachment column lands in
stage 3.

## Related

- [ORCH-SPEC-RESOURCE-REGISTRY.md](ORCH-SPEC-RESOURCE-REGISTRY.md) — the spec this template
  implements (§2 the statement fields, §4 the review convention, §5 the escalation ladder, §8 the
  stage plan and witness this template's own live proof follows).
- [ORCH-SPEC-RESOURCE-ACCOUNTING.md](ORCH-SPEC-RESOURCE-ACCOUNTING.md) — the companion spec that
  added the fourth TIER value, `forbidden` (§3), completing the MAY/SHOULD/MUST/MUST-NOT deontic
  register; §5/§7 name how and how far it is checked (audit-policed, no write-time block yet).
- [GLOSSARY.md](../GLOSSARY.md#pillar-1) — Pillar 1, `blessed`, `mandated (tier)`,
  `forbidden (tier)`, and `resource declaration` are all defined there; chase any of those terms
  there if this page's own use of them does not read as plain English (the Stand-Alone Principle
  two paragraphs above).
- [USER-GPG-TRUST-LAYER-FAQ.md](USER-GPG-TRUST-LAYER-FAQ.md) — the FULL/SIGNED commission-signing
  ceremonies a mandated declaration is apt to use.
- `bootstrap/templates/led.tmpl` — the `led obligate` / `led review` / `led review-gap`
  documentation this page's mandated-tier section composes rather than restates.
- `bootstrap/templates/pickup.tmpl` — the RESOURCES section that reads every `resource:`
  declaration this page's conversions produce.
