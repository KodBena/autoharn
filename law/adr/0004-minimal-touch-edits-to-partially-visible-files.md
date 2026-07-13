# ADR-0004: Minimal-Touch Edits to Partially-Visible Files

> *Refactored for cross-project portability on 2026-07-13 under
> [`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md)
> (tracker `adr-portability-refactor`, maintainer-ratified 2026-07-13). The pre-refactor
> text stands verbatim at commit `ff691bb9bc430ad497d74ff82d580f758a969f99`; extracted
> records live in [`history/0004-contract-examples.md`](history/0004-contract-examples.md)
> and are not retro-edited. Dated amendments below (there are none in this ADR) are
> preserved verbatim from the original.*

- **Status:** Accepted
- **Genre:** Tenet (cross-cutting authoring discipline) — the second tenet,
  after ADR-0002 (fail loudly).
- **Date:** 2026-06-15
- **Provenance:** Transferred from the LengYue ADR corpus — LengYue and chocofarm are
  two prior software projects this ADR corpus passed through before autoharn adopted
  it, LengYue the earlier of the two (a Vue/TypeScript project) and chocofarm its
  successor (a Python project) that re-derived LengYue's tenet for its own stack before
  autoharn inherited it from chocofarm in turn. The tenet is universal and transfers
  wholesale; a source project's own instance list (chocofarm's: numpy/JAX numerical
  contracts and a hand-synced feature layout; LengYue's: prop/emit/composable drift —
  Vue.js component-interface contracts specific to that project's frontend framework)
  is re-derived against each adopting project's real surfaces — whatever files carry
  contracts the test suite only partially polices. **Instance binding (autoharn):** this project's
  own source is Python/SQL/ASP over a Postgres-backed ledger and a clingo-based
  deductive engine, not chocofarm's numpy/JAX stack; no re-derivation of the instance
  list has been done for autoharn's own surfaces as of this refactor — a contributor
  applying this tenet here identifies autoharn's own partial-visibility hazards (its
  largest gates, stores, and workflow scripts) rather than reusing chocofarm's list,
  which is preserved as history below.
- **Scope:** All authoring work on the hosting codebase, especially during the kind
  of mechanical refactor where many files are touched in close succession.

## Context

A source file in the hosting project routinely carries multiple distinct
contracts that its test suite only partially polices — a numerical-equivalence
contract between backends, a positional layout contract sliced by offset in more
than one place, a duality contract where two code paths must certify against the
same underlying semantics, or a cross-site agreement contract (a value that must
match across several call sites) reintroduced as a bare literal if one site is
edited blind. In each case the failure mode is *silent at edit time and audible
only when a specific run or input surfaces it* — exactly the most dangerous tier
of [ADR-0002](0002-fail-loudly.md)'s loudness hierarchy (ADR-0002's own ranking
of failure modes from loud-and-immediate to silent-and-deferred; this failure
mode sits at the silent-and-deferred end, the one the loudness hierarchy treats
as worst).

> **Extracted record — the four chocofarm contract examples and the named
> oversized-file list**
> *(moved verbatim to [`history/0004-contract-examples.md`](history/0004-contract-examples.md))*:
> chocofarm's own worked instances of the four contract classes above — a
> numpy/JAX bit-equivalence contract, a feature-vector block order sliced by
> offset in three files, a belief-mechanics duality certified through
> `env.restrict`, and an episode-horizon literal owned in one place but
> repeatable in four — plus the specific oversized files (675, 715, 605, 510,
> 451, 360 lines) where partial visibility was the measured hazard, from a
> 2026-06-15 architectural audit. The lesson those specimens carry: the risk
> concentrates during large mechanical sweeps, where a tool view truncates a
> file and the temptation is to "tidy the rest while I'm in here" — that
> tidy-up, applied to parts the editor doesn't fully see, is where silent
> breakage gets introduced.

## Decision

**When editing a file under conditions where the full source is not in
immediate view, the only changes that go in are the specific lines the tool,
test, or task is about.** A "while I'm in here" full-file rewrite is not
permitted under these conditions.

The discipline has two cases:

- **Files visible in full.** Edit freely. The editor has the context to
  reason about the whole file's contracts — the numerical equivalence, the
  feature layout, the belief-mechanics duality, the horizon agreement.
- **Files visible only in part.** Edit only the specific lines the task or a
  failing test points at. If a broader rewrite seems warranted, read the full
  file first; do not produce one from inference. A large, multi-hundred-line
  file carrying one of the contracts above (see
  [`history/0004-contract-examples.md`](history/0004-contract-examples.md)
  for the worked instances preserved in
  [`history/0004-contract-examples.md`](history/0004-contract-examples.md))
  is exactly the file where an
  inferred rewrite drifts a numerical or layout contract the editor couldn't
  see.

## Consequences

### Positive

- **Silent numerical / layout / duality drift is structurally prevented,**
  not merely caught after the fact. A reorder of a feature sub-block, a
  reordered op in one forward backend, or a horizon literal reintroduced in
  one of four sites — none get introduced by an edit that touches only the
  flagged lines.
- **The cost of reading the full file is paid up-front,** in the cheaper
  currency (one read) rather than later in the more expensive currency (a
  silently-wrong research result that requires re-running to diagnose).
- **Bisection stays useful.** When a flagged issue gets fixed, the editor
  has confidence nothing else changed.

### Negative

- **Sweeps take more turns.** A consolidation that touches a file the editor
  hasn't seen in full requires reading it first — slower than a speculative
  rewrite.
- **The discipline is policy, not mechanism.** Like ADR-0002, it lives in
  review and authoring habit. There is no automated check that catches a
  violation. (ADR-0011 Rule 1: this is a declared review-only surface.)

### Neutral

- **No code change today.** This ADR documents a discipline for future
  authoring; it does not trigger any refactoring of existing code.

## Revisit when…

1. **A mechanical guard makes a drift class catchable.** An equivalence test
   already catches *some* numerical drift; a layout-sliced assertion naming its
   fields would catch positional drift (see chocofarm's own worked
   instance in [`history/0004-contract-examples.md`](history/0004-contract-examples.md)'s
   feature-layout contract). As each contract gains a mechanical guard, the
   policy can relax in proportion to the new guarantee — but only for the
   guarded class.
2. **The largest files are split below the partial-visibility threshold.**
   ADR-0007 (file size) is the prophylactic counterpart: if a codebase's
   oversized files are split so partial visibility becomes rare, this tenet's
   reactive discipline applies less often. The two compose.
3. **The discipline introduces its own unanticipated failure mode.**
   Unlikely, but worth flagging as the trigger for revisit.

## Related

- **[ADR-0002](0002-fail-loudly.md) (fail loudly).** The failure mode this
  tenet prevents — silent drift a later run is the first to discover — sits
  at the most dangerous tier of ADR-0002's loudness hierarchy. This tenet is
  ADR-0002's authoring-side counterpart: ADR-0002 says "when in doubt, fail
  audibly at runtime"; this one says "when in doubt about the file you're
  editing, don't introduce changes the run will be the first to discover."
- **[ADR-0007](0007-file-size-and-information-density.md) (file size and
  information density).** The prophylactic sibling: keep files small enough
  that partial visibility is rare, eliminating the condition under which this
  tenet's reactive discipline applies. The oversized files named in the
  extracted history record are ADR-0007's refactoring queue in the source
  project.
- **[ADR-0001](0001-immutability-and-copy-on-write.md) (immutability,
  copy-on-write, and rebind-not-mutate).** The same philosophy at the
  meta-level: don't write code that asserts a contract (a numerical
  equivalence, a layout) you haven't verified.

## Not goals (explicit)

- **Not a prohibition on full-file edits.** Files visible in full are edited
  freely; substantial rewrites are fine when the editor has the file in full
  and the rewrite is the point of the commit.
- **Not a requirement that every edit be tiny.** The tenet targets the
  *incidental* rewrite during a sweep focused on something else, not
  deliberate large refactors done with the file fully read.
- **Not a slowdown for trusted, well-known small files.** When a file is
  stable and small enough to edit blind safely, that's a per-file judgment
  call, not a relaxation of the general policy.

## License

Public Domain (The Unlicense).
