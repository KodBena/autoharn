# ADR-0019 — Genre convention is the default spec (UIs are not a novelty surface)

<!-- doc-attest-exempt: constitutional text authored by Fable and maintainer-ratified
2026-07-22 (commission: "Can we document UI type shit-patterns into ADR-0019 so I never
again have to point it out?"). Removal condition: a fresh-context A:B:C attestation pass
over the law/ corpus. -->

Ratified 2026-07-22. Provenance: one day — 2026-07-22 — produced four independent UI
builds of the same configuration surface, each inventing a fresh anti-pattern no
mainstream configuration application exhibits, each caught only by the maintainer's
eyes at real cost (ledger rows 1100, 1109, and the day's session record; ~$340 of
spend measured by the maintainer). The maintainer's observation, preserved because it
is the diagnosis: LLM builders are supposed to be statistical pattern completers, yet
each attempt produced task-shaped novelty instead of the genre's convergent shape.

## Rule 1 — In an established genre, the convergent design IS the default spec

A configuration editor, a file picker, a log viewer, a form, a table browser — these
are SOLVED genres: decades of convergent evolution across thousands of applications
have produced a dominant idiom per genre (for configuration: a hierarchical tree of
the whole space, always visible; a form pane whose fields are a LIVE view of the
model; statuses derived, not declared; one real action, not per-node ceremony —
Qt settings, SAP IMG, every mature settings surface). A spec or build for a UI in
such a genre inherits the dominant idiom as its default in full. The spec's job is
to name the genre, name two or three reference exemplars, and specify only the
domain content and the DELTAS — and every delta from the genre idiom is a named,
justified decision that survives the named-consumer test (ADR-0000's tail: who
consumes this deviation?). An unjustified deviation is a defect on the same footing
as a failing gate, however locally clever it looks.

## Rule 2 — Novelty is the anti-pattern (the enumeration is open, the class is closed)

The anti-pattern catalog is infinite — a teletype emulated inside a widget toolkit;
a product type rendered as a sequential wizard; a per-section save button splitting
form state from model state; a bespoke navigation key protocol; a binding on another
tool's prefix key — and enumerating it is a losing race (each of those five was
invented fresh, in this repo, within days, four of them within hours). Therefore the
rule quantifies over the class, not the instances: **any UI structure the genre's
reference exemplars do not exhibit is presumptively wrong**, and the burden of proof
sits on the deviation, never on the convention. "I have not seen this shape in the
references" is sufficient grounds for a reviewer or the maintainer to reject without
further argument. The specimens above are preserved as evidence that the class is
real, not as the boundary of it.

## Consequences

- A UI spec that names no genre and no reference exemplars is incomplete and may not
  be frozen (composes with the read-back mechanism of ledger row 1102: the read-back
  is stated in operator terms against the named references).
- Builders receive the reference idiom in the brief; a builder that cannot match a
  structure it is building to the references must stop and say so rather than invent
  (ADR-0014 posture, applied to design instead of debugging).
- Review of a UI change checks the diff against the named exemplars before it checks
  the code: structure first, correctness second — a correct implementation of a
  deviant structure is still a defect (2026-07-22's four builds were all "correct").
- This ADR deliberately mints no anti-pattern list to maintain. The genre references
  are the living catalog; the world maintains them for us.

*Enforcement surface: spec-time (the genre/reference clause is a required part of any
UI build basis) and review-only for the structural check — no mechanical gate reads
screenshots today. If a recurrence survives spec-time and review, that recurrence is
ADR-0011 Rule 2 grounds for minting the strongest feasible mechanism then available.*

## 2026-07-22 — Rule 3 appended: one home per fact extends to the screen (unique placement)

*(Dated append per ADR-0005 Rule 8, same day as ratification. Provenance: the shared-field
rounds of the setup-TUI rebuild — a configuration value rendered editable under two
sub-headings, then proposed as a read-only mirror; the maintainer adjudicated both away,
verbatim: "ADR-0002 -- a duplicated mirror/projection of a value is a type error and
refused on TUI start" — ledger rows 1112 and this append's own commit.)*

**Rule 3 — The navigation hierarchy is a claim of unique placement, and the claim is
typed.** A section tree asserts a partition of the configuration space: every fact has
exactly one address. Rendering one value under two headings — editable or as a
"convenience" mirror — falsifies that claim and mints a hidden dependency the operator
can only discover empirically (touch one widget, watch another twitch). This is not a
taste question; it is ADR-0012 P1 (one home per fact) applied to the presentation
layer, because the screen is storage for the operator's mental model, and a duplicated
widget is a denormalized projection owing a synchronization story no one was ever told.
The named external pedigree, recorded so no future reader mistakes this for one
maintainer's idiosyncrasy: unique placement / polyhierarchy-as-hazard (information
architecture), hidden dependencies (Green & Petre's cognitive dimensions), 1:1
control-to-variable mapping and the gulf of evaluation (Norman). Enforcement is NOT
review-only: a duplicated projection of one fact is a TYPE ERROR, refused loudly at UI
start, naming the fact and every section claiming it. The same defect appeared at the
model layer (flat-keyspace aliasing) and the presentation layer (mirrored fields) in
one build, one day: they are one class — two views bound to what should be one slot,
or one slot masquerading as two facts — and the class is closed at construction, at
both layers, not policed by eyes.
