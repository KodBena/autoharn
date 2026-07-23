# ADR-0006: Source-File Headers

This ADR states the project's convention for what every source file's opening
header must say about itself: its own path, its purpose, and (where a project
makes this declaration at all) its license.

> *Refactored for cross-project portability on 2026-07-13 under
> [`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md)
> (tracker `adr-portability-refactor`, maintainer-ratified 2026-07-13). The
> pre-refactor text stands verbatim at commit
> `ff691bb9bc430ad497d74ff82d580f758a969f99`; extracted records live in
> [`history/0006-header-exemplars.md`](history/0006-header-exemplars.md)
> and are not retro-edited. Per the maintainer's C5 ruling (the fifth entry of
> this refactor's adjudicated contradictions register, `design/MAINT-ADR-PORTABILITY-SPEC.md`
> §7, `./led` decision-ledger row 369): the portable edition below drops the per-file
> license-header mandate as a universal requirement — file-headering license
> posture is a matter each project decides for itself — while autoharn's own
> instance binding (below) keeps its Unlicense-header posture locally,
> unchanged.*

- **Status:** Accepted
- **Genre:** Tenet (file-level authoring discipline) — the fourth tenet,
  after ADR-0002 (fail loudly), ADR-0004 (minimal-touch), and ADR-0005
  (documentation discipline).
- **Date:** 2026-06-15
- **Provenance:** Transferred from the LengYue ADR corpus — LengYue and
  [chocofarm](../../GLOSSARY.md#omega-and-chocofarm) are two prior software projects this ADR corpus passed through
  before autoharn adopted it, LengYue the earlier of the two. LengYue's tenet
  unified two divergent header conventions across a TypeScript frontend and a
  Python backend; chocofarm, LengYue's successor project, was a single Python
  package with one already-de-facto convention, so chocofarm's ADR *codified
  the existing convention* rather than reconciling two. **Instance binding
  (autoharn):** autoharn's own source is
  primarily Python plus SQL and ASP (clingo); no per-file header convention has
  been derived for autoharn's own tree as of this refactor — a contributor
  applying this tenet here derives autoharn's own exemplar set rather than
  reusing chocofarm's, which is preserved as history below.
- **Scope:** Source files in the hosting project's own package(s), scoped by the
  adopting project's own declaration (an adopter names its own source tree and
  its own exclusions, the way chocofarm named `chocofarm/`, `tests/`, `scripts/`,
  `probes/`). Data files following their own format conventions are excluded by
  the same declaration.

## Context

A project's source files converge, or should converge, on a header pattern: a
module docstring (or the hosting language's equivalent) whose first content
names the module's path/area and purpose. Naming the convention explicitly —
rather than leaving it an unwritten habit — gives the files that lack it a rule
to retrofit against.

> **Extracted record — the chocofarm exemplar file list and the Part A/B/C
> anecdote**
> *(moved verbatim to [`history/0006-header-exemplars.md`](history/0006-header-exemplars.md))*:
> six chocofarm files already converged on path+purpose+license headers at the
> time this rule was written, and a 2026-06-15 architectural audit found nine
> modules explaining their own behavior by reference to ephemeral session tags
> ("Part A/B/C") instead of by path — the *opposite* failure this convention
> forecloses. The lesson: a header naming path and purpose keeps a file
> readable standalone, including under ADR-0004's partial-visibility
> condition, where a session-tag reference resolves to nothing once the
> session that coined it is gone.

The convention earns its weight for two reasons:

1. **Self-locating files.** A file pasted into a review, a diff, or a search
   result identifies itself. This composes directly with ADR-0004
   (minimal-touch): a contributor working with partial visibility into a large
   file benefits from the file declaring where it lives.
2. **Per-file license clarity, where the project declares one.** A project that
   states its license per file keeps that signal attached to the file at the
   moment it is vendored, copied, or reposted — without it, only the project as
   a whole is identifiably licensed, and the signal is lost once a file leaves
   its repo context. Whether a project makes this declaration at all, and
   which license it names, is the project's own posture (Decision, below).

## Decision

**Every source file in the project's declared scope carries a header with two
mandatory parts and one optional part:**

1. **The module's path or area**, as the first content of the header
   (e.g. `<package>/eval/report.py — …`).
2. **A brief purpose statement** (one line minimum; multi-section commentary
   fine for a file whose header is itself a decision-bearing document, e.g. a
   rich contract or audit-reference section).
3. **A license declaration, if per-file declaration is the project's posture**
   — optional, per-deployment. A project that declares a license per file
   names it here (autoharn's own posture is below, under Instance bindings); a
   project that does not is not out of compliance with this rule for omitting
   it — the path and purpose slots are the mandatory core, the license slot is
   not.

### Form

The header takes this shape in Python (an adopting project in another
language restates the same three slots in its own comment/docstring idiom):

```python
#!/usr/bin/env python3
"""
<package>/<area>/<file>.py — <one-line purpose>.

[optional: design notes, the contracts this file owns, audit references]

[optional: the project's declared license, if per-file declaration is its posture]
"""
```

### Why path-first

A file that names its own path is the cheapest insurance against being moved
without its docstring updated, and the most useful thing to have when a
fragment is pasted out of context. Composes with ADR-0004.

### Composition with ADR-0004 — incremental retrofit

ADR-0004 enables incremental retrofit. When a file is touched with full
visibility, the header is added/corrected; when it's touched under partial
visibility, the header is left for next time. No special discipline is
required; headers accumulate as files cycle through normal editing.

### Exceptions

- **Package-init files** (e.g. Python's `__init__.py`): a header is fine but
  not required (often empty or re-exports only).
- **Data files**: follow their own format; no source-style header.
- **Generated artifacts**, if any are added, do not carry a hand-written
  header (a header would be lost on regeneration); the generator's config is
  the right home for that concern.

## Consequences

### Positive

- **Self-locating files.** This makes pasted code, diffs, and tooling/agent-
  report output easier to read and identify by file.
- **Per-file license clarity, where declared.** Vendored or extracted files
  retain the license signal, for a project that makes the declaration.
- **Consistency across the package.** One shape everywhere reduces friction.

### Negative

- **Per-file ceremony.** This ceremony is small but real, especially for
  short utilities.
- **Discipline is policy, not mechanism.** The tenet lives in authoring habit
  and review; there is no header-presence linter by default. (ADR-0011 Rule 1:
  a declared review-only surface; a path-presence check would be the
  mechanization trigger — a predecessor project's own header-checker script is
  a worked precedent that such a check is buildable; see Provenance.)

### Neutral

- **No retroactive sweep.** Per ADR-0004, existing files without a complete
  header are retrofitted incrementally as they're touched, not in a sweep.

## Revisit when…

1. **Tooling exists to auto-verify path headers.** A presence check would
   partially mechanize the discipline, at which point the rule could tighten
   from reviewed toward enforced.
2. **The project's license posture changes.** If a project that declares a
   per-file license changes that posture, the declaration's specifics need
   updating; the path/purpose discipline remains untouched either way.

## Related

- **ADR-0004 (minimal-touch).** Self-locating files reduce the cost of
  partial-visibility editing; the composition pattern is incremental retrofit.
- **ADR-0005 (documentation discipline).** The umbrella tenet of which file
  headers are a file-level instance. ADR-0005 Rule 5 (file location reflects
  content) is harder to violate when the file declares its own location.
- **ADR-0007 (file size and information density).** Smaller files multiplied
  by per-file headers keep header overhead bounded.

## What this tenet does NOT mean

- **Not a requirement for documentation files** (`.md`, the ADRs
  themselves). Markdown has its own conventions; ADR-0005 governs.
- **Not a requirement for data/blob files.** The tenet applies to files
  carrying source code intended for human reading.
- **Not a license mandate.** Whether a project declares a license per file, and
  which one, is the project's own posture (see Instance bindings); this rule
  mandates only the path and purpose slots universally.
- **Not a substitute for git-tracked metadata.** Authorship and change
  history live in git, not in headers.

## Instance bindings (autoharn) — the non-portable section

Everything above is project-neutral. This section is autoharn's binding of the
tenet to its own posture, and an adopting project replaces it with its own
declaration (or omits the license slot entirely).

- **autoharn's own license declaration:** Public Domain (The Unlicense), stated
  per file at the end of the header docstring — the same posture the
  extracted history record shows the source project holding. This is
  autoharn's own choice, not an inherited requirement — the C5 ruling (ledger
  row 369) is precisely that this posture does not bind an adopter.
- **autoharn's own scope declaration:** not yet re-derived against autoharn's
  actual source tree as of this refactor (flagged, not decided, per §8 of
  `design/MAINT-ADR-PORTABILITY-SPEC.md` — routing a scope re-derivation to the
  maintainer rather than improvising one here).

## License

Public Domain (The Unlicense).

<!-- doc-attest-exempt: mechanical, content-preserving edit (usability review, ledger row 1180, 2026-07-23, finding 16) -- the single existing word "chocofarm" at its first plain-text mention in this file was wrapped in a markdown link to GLOSSARY.md#omega-and-chocofarm (the Stand-Alone Principle's own first-use-link requirement, GLOSSARY.md#stand-alone-principle, applied here for the first time). No other character in this file changed; the rule content this ADR states is untouched. This mechanical class of edit is authorized by the maintainer's vested-judgment commission for this round (ledger row 1180), not a semantic change to law/ requiring further ceremony. Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for its actual rule content, not just a link wrap. -->
