# ADR-0007: File Size and Information Density

> *Refactored for cross-project portability on 2026-07-13 under
> [`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md)
> (tracker `adr-portability-refactor`, maintainer-ratified 2026-07-13). The
> pre-refactor text stands verbatim at commit
> `ff691bb9bc430ad497d74ff82d580f758a969f99`; extracted records live in
> [`history/0007-oversized-file-queue.md`](history/0007-oversized-file-queue.md)
> and are not retro-edited. Dated amendments below (there are none in this ADR) are
> preserved verbatim from the original.*

This ADR states the project's file-size and information-density convention:
soft thresholds, a density heuristic, and content-aware formatting rules that
together keep a source file small enough, and dense enough with decisions
rather than boilerplate, that a reader or reviewer can hold it in working
memory.

- **Status:** Accepted
- **Genre:** Tenet (cross-cutting authoring discipline) — the fifth tenet,
  after [ADR-0002](0002-fail-loudly.md) (fail loudly),
  [ADR-0004](0004-minimal-touch-edits-to-partially-visible-files.md)
  (minimal-touch), [ADR-0005](0005-documentation-discipline.md)
  (documentation discipline), and [ADR-0006](0006-source-file-headers.md)
  (source-file headers). This ADR is a sibling of ADR-0004: same failure
  mode, different intervention point.
- **Date:** 2026-06-15
- **Provenance:** Transferred from the LengYue ADR corpus — LengYue and
  chocofarm are two prior software projects this ADR corpus passed through
  before autoharn adopted it, LengYue the earlier of the two (TypeScript/Vue)
  and chocofarm its successor (Python). The tenet (size + density together,
  soft thresholds, no logic golf, content-aware contraction) is universal;
  the specific numeric budgets and contraction table are re-derived per
  language and per project — chocofarm re-derived LengYue's
  TypeScript/Vue-specific numbers for Python, and its own oversized
  files were the instance list at the time (preserved as history below).
  **Instance binding (autoharn):** this project's numeric thresholds below are
  inherited unchanged from chocofarm's Python re-derivation (autoharn's own
  source is also primarily Python); no re-derivation or fresh oversized-file
  survey has been run for autoharn's own tree as of this refactor.
- **Scope:** This tenet's scope is source-code authoring in the hosting
  project's own package(s). Documentation is governed by
  [ADR-0005](0005-documentation-discipline.md).

## Context

ADR-0004 governs editing a partially-visible file: only touch the flagged
lines. This tenet is the prophylactic counterpart — keep files small enough
that partial visibility is rare, eliminating the condition under which
ADR-0004's reactive discipline applies.

Two metrics together do the work. **Size** caps the number of lines a tool
view has to fit. **Density** ensures those lines carry decisions, not
boilerplate. A bloated file (high size, low density) is the worst case: tool
truncations elide as much decision content as boilerplate, and reviewers wade
through noise to find the parts that matter.

> **Extracted record — the named oversized-file queue**
> *(moved verbatim to [`history/0007-oversized-file-queue.md`](history/0007-oversized-file-queue.md))*:
> a 2026-06-15 architectural audit named seven specific chocofarm files
> (360–715 lines each) as the refactoring queue this tenet's Neutral clause
> governs, including the density-heuristic and column-cap groundings quoted
> verbatim in the record. The lesson: length alone did not indict a file
> (the audit found the largest of the seven "not the god-object its length
> implies" — three honest layers), but length still made each one a
> partial-visibility hazard under ADR-0004, and each entered a refactoring
> queue addressed incrementally rather than by retroactive sweep.

## Decision

### Size — soft thresholds (Python)

- **Target ≤ 300 lines** for a typical module; **≤ 400 acceptable** for a
  single coherent unit (one solver family, one schema, one cohesive state
  machine) where splitting would fragment cross-line invariants.

When a file crosses the threshold, the contributor pauses and asks whether a
split is warranted before extending further. Typical refactor moves: split
presentation from analysis; lift a shared helper into the package's shared
base; separate a schema (the typed contract) from the thin layer over it —
each a generalization of a worked move recorded verbatim in
[`history/0007-oversized-file-queue.md`](history/0007-oversized-file-queue.md).

### Density — effective lines / total lines

"Effective" lines carry decisions specific to this file's purpose (function
bodies, non-trivial domain-logic expressions, the contracts a docstring
owns). "Boilerplate" lines do not (imports, trivial property accessors,
repeated scaffolding).

These thresholds are qualitative at review — a review heuristic rather than a
mechanically-measured metric, unless a project has built tooling to measure
the ratio:
- **healthy:** the file is mostly decisions.
- **yellow flag:** noticeable scaffolding-to-decision ratio — review for
  splitting next time the file is touched.
- **red flag:** the decisions are buried in scaffolding — refactor before
  further extension.

### Format — content-aware contraction

Format reflects edit cadence. Content rarely hand-edited may contract to
maximize the visible budget for content that is; decision logic does not.

| Content | Rule |
|---|---|
| **Data tables, constant arrays, fixture literals** | Contraction acceptable — pack multi-value rows, keep one logical row per line. |
| **Numerical / decision logic** | No contraction. Standard formatting; multi-line for clarity. |
| **Docstrings / contracts** | Contextual. Rich, decisions-about-the-file headers earn their length; pure boilerplate prose does not. |

**Soft column cap:** ~100 characters as this project's own instance (re-derive
against the adopting project's own code — [`history/0007-oversized-file-queue.md`](history/0007-oversized-file-queue.md)
records the source project's own grounding figure verbatim); beyond the cap,
even contracted content goes multi-line.

**The no-go.** Never contract numerical or decision logic to fit a size
budget. Code golf in a core numerical routine or decision path hides bugs
behind dense lines and inflates working-memory cost per line — and, given
ADR-0004, a dense line in a partially-visible file is exactly where a silent
numerical drift hides. If a logic file is over budget, the answer is
structural extraction, never cosmetic compression.

## Exceptions

- **Coherent units** (one solver family, one schema dataclass set) with high
  density may run to ~400 lines if splitting would fragment cross-line
  invariants.
- **Generated artifacts**, if added, are exempt; size is a property of the
  upstream contract.

## Consequences

**Positive.** Partial-visibility risk (ADR-0004) drops at the source. Review
fits in working memory. Single-purpose discipline is enforced by gravity.

**Negative.** Some refactors are mandatory work. Discipline is policy, not
mechanism — like the other tenets, it lives in review
([ADR-0011](0011-mechanization-discipline.md) Rule 1: a declared review-only
surface; no `max-lines` check exists). Over-fragmentation
is a real risk if the rules are read too literally — a large file whose length
comes from several honest, cohesive layers should not be shattered into a
dozen files just to hit a line count (the Exceptions coherent-unit carve-out
exists for exactly this).

**Neutral.** There is no retroactive sweep. Oversized files enter a refactoring queue
and are addressed when next touched substantively, composing with ADR-0004's
and ADR-0006's incremental-retrofit posture — see
[`history/0007-oversized-file-queue.md`](history/0007-oversized-file-queue.md)
for the source project's own worked queue and how several of its files were
slated to shrink naturally as unrelated content work landed.

## Revisit when…

1. A linter or pre-commit hook automates the size rule — soft thresholds can
   become enforced limits ([ADR-0011](0011-mechanization-discipline.md) Rule 1's
   mechanization trigger).
2. The information-density heuristic proves too judgmental in practice —
   replace with a more mechanical proxy.
3. A specific exception's classification turns out wrong in practice — the
   exception narrows.

## Related

- **[ADR-0004](0004-minimal-touch-edits-to-partially-visible-files.md)** — the
  reactive sibling; this prevents the situation ADR-0004 mitigates. The
  oversized files here are ADR-0004's partial-visibility hazards.
- **[ADR-0005](0005-documentation-discipline.md)** — the documentation
  analog; both compose when a refactor relocates and resizes simultaneously.
- **[ADR-0006](0006-source-file-headers.md)** — file-level companion; smaller
  files multiplied by per-file headers keep overhead bounded.
- **[ADR-0001](0001-immutability-and-copy-on-write.md) /
  [ADR-0003](0003-domain-coupling-bands.md)** — file structure should match
  actual responsibility and domain band, no aspirational cohabitation.

## What this tenet does NOT mean

- Not a hard line-count limit; the threshold flags, not ceilings.
- Not a mandate to split immediately; existing files retrofit incrementally.
- Not a directory-organization decision.
- Not enforced by tooling today.

## License

Public Domain (The Unlicense).
