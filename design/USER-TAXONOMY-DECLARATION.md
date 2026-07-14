# USER-TAXONOMY-DECLARATION — declaring a boundary discipline on your own project

Audience: adopter

This document answers one question: **how do you tell this harness where a boundary sits in
your project — a licensing line, an architectural layer, a data-sensitivity zone — so an agent
workforce can be kept from coding across it, the same way a human team enforces it socially by
module ownership and review?**
[design/ORCH-SPEC-TASK-TAXONOMY.md](ORCH-SPEC-TASK-TAXONOMY.md) (§1) names the problem this
answers: *"a boundary discipline enforced by prose is enforced by hope … an agent workforce has
no social layer, so the discipline must be structural or it is absent."* This page is the
adopter-facing half of that spec's Stage A (§7) — the two statement grammars you write, and how
they render back to you at session hydration (the point where `./pickup` loads your project's
ledger into a fresh session, so an agent starting work sees them without you repeating yourself).
It assumes no prior context beyond what is written
here and what it links to; if a term below does not read as plain English, follow its link to
[GLOSSARY.md](../GLOSSARY.md).

Two things this page is **not**: it is not the mechanism that enforces a boundary once declared
(the write-time gate and the audit family are later stages, [§7](ORCH-SPEC-TASK-TAXONOMY.md#7-implementation-routing-all-stages-sonnet-executable-from-this-spec)
Stages B/C/D of the same spec, unbuilt as of this page — declaring a taxonomy today records it
on the ledger and shows it back to you at `./pickup`, and nothing more), and it is not this
repository's own boundary declaration (autoharn declares nothing for you — see
["the worked example"](#the-worked-example-one-maintainers-own-boundary) below on why the
example here is marked as such, following the same convention
[USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md) uses for its own worked rows).

## Background: what a taxonomy declaration is, in one paragraph

A **taxonomy** is a named classification scheme over your project's
artifacts (files) — `license`, `arch-layer`, `sensitivity` are the spec's own examples — under
which every artifact that matters falls into exactly one class (a **taxon**) of that scheme.
Declaring one is a ledger act, exactly like declaring a
[resource](USER-BLESSED-TABLE-TEMPLATE.md#background-what-a-resource-declaration-is-in-one-paragraph):
your project's ordinary ledger rows of `kind` `decision`, carrying a `taxon:` or `interface:`
statement-prefix convention — no ledger schema change, "version 1, no kernel change" in the
spec's own words (§3). A **taxon row** assigns one or more path globs (`PATTERNS`) to one class
(`TAXON`) of one scheme (`TAXONOMY`), with a human-readable `GLOSS`. An **interface row**
declares a sanctioned crossing point for a scheme — an artifact that code outside a taxon of
that scheme *may* reference even though it sits inside one, the "documented public API" the
spec's own worked specimen (§3) uses as its example. Together the two rows are the **declaration
half** of the discipline: the **policing half** (a write-time refusal when an agent's claimed
work item sits in one taxon and it edits an artifact in another; an audit report that flags an
artifact matching no declared taxon) is later spec stages, not built by this page.

## The worked example: one maintainer's own boundary

The rows below are **transcribed from [ORCH-SPEC-TASK-TAXONOMY.md §1](ORCH-SPEC-TASK-TAXONOMY.md#1-the-problem-and-the-worked-specimen-the-maintainer-already-owns)**,
which names them as "the maintainer's own omega project" — **one maintainer's own worked
example**, included here to show a real, filled-in declaration, never as a claim that your
project has, needs, or should copy this exact boundary. This is the same "EXAMPLES — this
maintainer's own stack" marking
[USER-BLESSED-TABLE-TEMPLATE.md's canonical-residents table](USER-BLESSED-TABLE-TEMPLATE.md#the-canonical-residents-this-maintainers-stack-worked-examples)
uses for its own rows: delete it, or keep it as reference, and declare your own project's
boundaries below it.

The specimen is a `backend/qeubo/` package that vendors an MIT-derivative dependency. The
project's own README already declared, in prose, that public-domain code MUST consume the
vendored package only through its documented API module and MUST NOT read its `vendor/`/
`runtime/` sources directly — a licensing boundary with one declared crossing interface, policed
today (in that project) only by the README paragraph a reader has to already know to look for.
The two statements below are that same boundary, declared structurally instead:

```sh
./led decision "taxon: license | mit-derivative | backend/qeubo/** | upstream qEUBO derivative"
./led decision "interface: license | backend/qeubo/__init__.py | the documented public surface"
```

Read as English: *under the `license` taxonomy, everything matching `backend/qeubo/**` is class
`mit-derivative` ("upstream qEUBO derivative"); and `backend/qeubo/__init__.py` is a sanctioned
crossing point for the `license` taxonomy ("the documented public surface")* — public-domain
code elsewhere in the project may reference that one file; it may reference nothing else under
`backend/qeubo/`.

## The statement grammars

This section is the one documented home for both grammars below — `bootstrap/templates/
led.tmpl`'s intake validators and `bootstrap/templates/pickup.tmpl`'s TAXONOMIES-section reader
both point back here rather than restating a grammar a second time
([ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1: a fact has one
home), the same relationship
[USER-BLESSED-TABLE-TEMPLATE.md's own grammar section](USER-BLESSED-TABLE-TEMPLATE.md#the-statement-grammars)
has to `resource:`/`constraint:`.

### `taxon:` — declaring one taxon within a taxonomy

The exact grammar, with angle brackets marking the four fields you fill in, is:

```
taxon: <TAXONOMY> | <TAXON> | <PATTERNS> | <GLOSS>
```

The four fields go in this exact order, separated by ` | ` (space-pipe-space). `TAXONOMY` and
`TAXON` are both **machine keys** — the predicates
[ORCH-SPEC-TASK-TAXONOMY.md §4](ORCH-SPEC-TASK-TAXONOMY.md#4-the-polymorphic-predicates-what-the-engine-checks-without-knowing-why)
quantify over (`single-taxon-task(T)`, `no-cross-taxon-write(T)`) match them by exact string, so
each must be a bare slug matching `^[a-z0-9][a-z0-9-]*$` — lowercase letters, digits, and
hyphens only, no spaces — the identical shape
[USER-RETROSPECTIVE-RECIPE.md's `TASK-SLUG` field](USER-RETROSPECTIVE-RECIPE.md#the-estimate-statement-grammar)
already uses for the same reason (a machine-matched key must not admit two differently-cased or
differently-punctuated spellings of the same thing). `PATTERNS` is one or more path globs (this
page's convention: comma-separate more than one, e.g. `src/vendor/**, third_party/**` — Stage A
validates only that the field is non-empty; the exact glob-matching semantics belong to
[Stage B](ORCH-SPEC-TASK-TAXONOMY.md#7-implementation-routing-all-stages-sonnet-executable-from-this-spec)'s
audit engine, unbuilt as of this page, so a `PATTERNS` field is accepted on shape alone today).
`GLOSS` is free text, non-empty, naming what the taxon means for a human reader. Copy-paste
example (a `arch-layer` taxonomy, distinguishing a domain layer from its adapters):

```sh
./led decision "taxon: arch-layer | domain | src/domain/** | pure business logic, no I/O and no framework imports"
```

### `interface:` — declaring a sanctioned crossing point

The exact grammar, with angle brackets marking the three fields you fill in, is:

```
interface: <TAXONOMY> | <ARTIFACT-PATTERN> | <GLOSS>
```

The three fields go in this exact order. `TAXONOMY` names the scheme the crossing point belongs
to — the same bare-slug shape as `taxon:`'s own `TAXONOMY` field, and ordinarily one for which
you have already declared at least one `taxon:` row, though this page's validator does not check
that cross-reference (Stage A validates each statement's own shape only; a `taxon:`/`interface:`
consistency check, if one is ever built, is a later-stage audit, not an intake refusal —
[ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)'s closure-statement
discipline names this an honest, deliberate absence rather than a silent gap). `ARTIFACT-PATTERN`
is the path or glob of the artifact that MAY be referenced from outside its own taxon — the ICD
(interface control document) analog
[ORCH-SPEC-TASK-TAXONOMY.md §3](ORCH-SPEC-TASK-TAXONOMY.md#3-declaring-a-taxonomy-rows-like-everything-else)
names. `GLOSS` is free text, non-empty, naming what the interface is for a human reader.
Copy-paste example (continuing the `arch-layer` taxonomy above):

```sh
./led decision "interface: arch-layer | src/domain/ports.py | the only module an adapter may import from the domain layer"
```

## Both grammars are validated at write time, before anything is stored

`./led decision "taxon: ..."` / `./led decision "interface: ..."` runs the exact grammar above
against a **whitespace-normalized copy** of your statement (every run of `\n`/`\r` plus its
following indentation collapsed to one space) — so a legitimate embedded newline, the kind a
terminal introduces by wrapping a long paste mid-word, is accepted rather than refused. A
statement that fails the check is **refused before any write happens** (nothing lands on the
ledger, exit non-zero, a message naming the exact field and grammar that failed and pointing
back at this section) — the same refuse-before-write atomicity
[USER-BLESSED-TABLE-TEMPLATE.md's `resource:` validator](USER-BLESSED-TABLE-TEMPLATE.md#resource-declaring-one-capability-registry-entry)
already gives you. A statement that passes is stored **byte-exact** — the row actually written
is what you typed, embedded newline included; the whitespace-normalized copy is validation-only
scratch, never persisted.

## Reading your declarations back: `./pickup`'s TAXONOMIES section

Once declared, `./pickup` shows every taxon and interface row on your ledger under one
`### SECTION: TAXONOMIES` header — taxa first (sorted by `TAXONOMY` then `TAXON`), then
interfaces (sorted by `TAXONOMY` then `ARTIFACT-PATTERN`) — no separate "publish" step, the same
pull-at-hydration convention `./pickup`'s RESOURCES and ESTIMATES sections already use. Running
`./pickup` after declaring this page's worked example prints:

```
### SECTION: TAXONOMIES

TAXON [license] mit-derivative  (ledger row id=41)
  patterns: backend/qeubo/**
  gloss:    upstream qEUBO derivative
INTERFACE [license] backend/qeubo/__init__.py  (ledger row id=42)
  gloss:    the documented public surface
```

A malformed row (one that predates this discipline, or was written by some other path that
skipped `led`'s own validator) prints flagged `MALFORMED` in place of a formatted block — a bad
declaration is a visible defect on your next `./pickup`, never a silently-dropped one — and an
empty registry prints its own explicit `(no taxon declarations on record)` /
`(no interface declarations on record)` line, never an omission you have to interpret.

## What this buys you today, and what it does not yet

Declaring a taxonomy today gives you a **structured, ledgered record** of where your project's
boundaries sit, and a **display surface** (`./pickup`'s TAXONOMIES section) so a session
hydrating into your project sees them without you repeating yourself in a prompt every time —
Stage A of [ORCH-SPEC-TASK-TAXONOMY.md](ORCH-SPEC-TASK-TAXONOMY.md), in full. It does **not**
yet enforce anything: no write-time gate refuses an agent's edit for crossing a declared
boundary (Stage C), no audit report flags an artifact matching no declared taxon or a reference
that skips a declared interface (Stage B), and no `task-policy:` criterion's policing column
moves because you declared one (Stage D) — those are named, routed, and left for later stages of
the same spec, not silently assumed to already work. Declaring a taxonomy with zero rows
declares zero obligation (the spec's own honest-limits section, §6): adoption is opt-in, and an
empty taxonomy registry is exactly as legitimate as one you have filled in.

## Related

- [ORCH-SPEC-TASK-TAXONOMY.md](ORCH-SPEC-TASK-TAXONOMY.md) — the spec this page implements
  Stage A of (§3 the statement grammars, §4 the predicates a future stage checks against, §5 the
  enforcement grades, §6 the honest limits, §7 the stage plan this page's own scope follows).
- [design/ORCH-SPEC-DECOMPOSITION-POLICY.md](ORCH-SPEC-DECOMPOSITION-POLICY.md) — the sibling
  spec whose `task-policy:` grammar a future stage attaches these taxonomies' predicates to.
- [USER-BLESSED-TABLE-TEMPLATE.md](USER-BLESSED-TABLE-TEMPLATE.md) — the sibling adopter page
  this one clones its worked-example marking and grammar-section conventions from, for the
  `resource:`/`constraint:` declarations.
- [USER-RETROSPECTIVE-RECIPE.md](USER-RETROSPECTIVE-RECIPE.md) — the sibling adopter page whose
  `estimate:` grammar this page's `TASK-SLUG`-shaped key fields borrow their shape from.
- `bootstrap/templates/led.tmpl` — the `taxon:`/`interface:` intake validators this page's
  grammar section is the documented source of.
- `bootstrap/templates/pickup.tmpl` — the TAXONOMIES section that reads every `taxon:`/
  `interface:` declaration this page's conversions produce.
