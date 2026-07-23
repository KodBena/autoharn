# ADR-0005: Documentation Discipline

*Refactored for cross-project portability on 2026-07-13 under
[`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md) (tracker
`adr-portability-refactor`, maintainer-ratified 2026-07-13, WP-4). The pre-refactor text stands
verbatim at commit `ff691bb`; extracted records live in
[`history/0005-audit-substrate.md`](history/0005-audit-substrate.md) and are
not retro-edited. This ADR carries no dated Amendment sections as of this refactor, so nothing
in that category is affected; the two dated notes added below (Rule 5's citation fix and
Revisit-when #2's discharge) are new, in-situ dated corrections under Rule 8, not retro-edits
of prior text.*

- **Status:** Accepted
- **Genre:** Tenet (cross-cutting authoring discipline) — the third tenet,
  after ADR-0002 (fail loudly) and ADR-0004 (minimal-touch).
- **Date:** 2026-06-15
- **Provenance:** Transferred from the LengYue ADR corpus. The tenet and its
  rules are universal and transfer wholesale. LengYue's instance list named
  monorepo/dispatch-ledger/work-status-store machinery [chocofarm](../../GLOSSARY.md#omega-and-chocofarm) does not
  have; the rules are re-derived against chocofarm's real documentation
  corpus — the design notes under `docs/design/`, the consult records under
  `docs/consults/`, the agent commission/report pairs under `docs/agents/`,
  the results under `docs/results/`, and the architectural-audit corpus under
  `docs/notes/audit/`. Rules that presuppose infrastructure chocofarm lacks
  (a Postgres work-status store, a cross-team dispatch ledger) are re-stated
  in the form chocofarm actually uses or marked as not-applicable.
- **Scope:** All authoring of documentation in this repository — ADRs, design
  notes, consult records, agent commission/report pairs, results write-ups,
  STATUS / handoff documents, and the audit corpus.

## Context

A fast-moving software project accumulates an extensive documentation corpus, and — in the
project that first authored this tenet — an architectural audit surfaced documentation rot and
drift patterns sharing a common root: **documentation written reactively, after-the-fact, or
without an explicit lifecycle decays into low-trust artifacts faster than the code decays
around it.**

**Extracted record — the audit's four instances**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md))*:
a live task queue narrated in "finished" prose that was stale within 24 seconds of being
written; a binding convention cited sixteen times whose promised registry did not exist; a
load-bearing cross-reference filed in the wrong directory, with an anchor that resolved
nowhere; and load-bearing specifics offloaded to a design document that was itself marked
stale in the very code implementing its successor. Four different failure shapes, one root:
the gap between when work happens and when its documentation is written is where drift lives.

A working contributor's experience of these patterns: orientation takes longer than it should
because the documentation graph has to be reconstructed from the code rather than read from
the documents. The cost compounds — the longer the gap between work and its documentation, the
more reconstruction the next reader does, and reconstruction degrades into guessing. The
underlying principle: *documentation is cheaper to write while you remember why, not when you
reconstruct why later.*

## Decision

We adopt **Documentation Discipline** as a codebase-wide tenet. Every
documentation artifact is authored under the following rules.

### Rule 1: Single source of truth per nominal handle

Anything that names a piece of work or a fact — an ADR number, a consult id,
a reference rate, a derived layout, a named threshold — has exactly one
owning home. Parallel records of the same handle drift silently, and the
drift is often invisible until two copies disagree. The structural fix is one
computed owner per fact, with everything else deriving from it — the
discipline ADR-0008 (classification) generalizes.

**Extracted record — the SSOT drift instance**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md#rule-1))*:
a reference rate hand-copied across roughly ten files had already drifted between two
copies; a belief-mechanics computation was duplicated at the exact site that certifies
against it; a feature layout was written out independently in three places. Each was
resolved by naming one computed owner per fact and deriving everything else from it —
the concrete form Rule 1 forecloses this class in.

### Rule 2: Records live where the convention says, and the convention is a declared, per-deployment table

Records have a predictable home, not an author's-convenience one: every record
**kind** this discipline recognizes (design notes, consult/decision records, agent
commission/report pairs, results write-ups, audit records, and any further kind a
deployment adds) has exactly one declared home in the hosting deployment's
filing-homes table, stated once in the "Instance bindings" section below — not
chosen ad hoc per author, per session, or per convenience. The load-bearing
commitment is **one place, known to the next reader**; *which* directory serves
which kind is not this rule's content — that is the per-deployment half — but the
fact that some directory does, unambiguously, is.

**Extracted record — the misfiling instance and the original docs/ table**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md#rule-2))*:
the rule was first authored against a directory table (`docs/design/`, `docs/consults/`,
`docs/agents/`, `docs/results/`, `docs/notes/audit/`) naming that project's real homes at
the time; a consult record filed under the wrong one of these (the agent-report home
instead of the consult home) was the concrete violation that motivated the rule, fixed by
relocating the file. That table is retired as portable law — the tree it names does not
exist in every adopting project — and survives only as the dated record of the rule's
origin; the present, binding table for this deployment is the "Instance bindings" section
below.

### Rule 3: Descriptions describe relations, not content snapshots

A reference's description should describe how the referenced document RELATES
to the referencing one, not what the referenced document SAYS. The latter
goes stale when the target evolves; the former survives most realistic
evolutions. This governs section anchors too: a citation that points at a
section must point at a section that *actually exists* under that name, never
a dangling one the target never carried. Apply this in every "see also,"
every Related section, every cross-document link.

**Extracted record — the anchor-repointing instance**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md#rule-3))*:
a relocated record's citation was repointed to its new path, and its section anchor was
corrected from a dangling numeral to the target's real, named heading — the concrete case
this rule's anchor requirement forecloses.

### Rule 4: Document bodies don't bare-name their siblings where a rename would break them

Prefer generic descriptors ("the companion report," "the audit appendix")
over bare filenames in running prose where the reference would self-break on
a rename. Exception: filenames in code blocks, in shell commands, and in
load-bearing path citations (where the path *is* the resolvable handle) are
fine — the rule applies to incidental running prose.

### Rule 5: File location reflects content, not authoring history

If a file's content has drifted from its directory's intent, move it before
someone trusts the directory. When relocating, repoint the live referrers (a
moved file's links are broken links until repointed — see Rule 3); leave
point-in-time records that *describe* the old location alone (Rule 8).

*(Dated fix, 2026-07-13, per Rule 8: the pre-refactor text cited "(Rule 8 / Rule 11)" here —
this ADR has no Rule 11 and never has. Corrected to the single, correct citation rather than
carried forward as a dangling reference into the portable edition; this is a live-prose
citation fix, not a retro-edit of a point-in-time record.)*

**Extracted record — the misfiled-consult relocation instance**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md#rule-5))*:
a consult record filed under the wrong directory (the agent-report home, not the consult
home) was relocated once its content was recognized as a consult — the concrete
location-misleads-content trap this rule forecloses.

### Rule 6: Documentation lifecycle — author as you decide

Write the record while you remember why. Status updates, deviation notes, and
the context for a decision are captured in the moment, not reconstructed at
the close. The corollary: **status documents record slowly-aging decisions
and rationale, never a live task queue** — the queue belongs in version
control / the commit log, not in immutable prose that can go stale within
minutes of being written.

**Extracted record — the 24-seconds-stale handoff**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md#rule-6))*:
a status document listed a fix as pending; version control showed that exact fix
committed 24 seconds later — the sharpest measured instance of a live task queue
narrated in prose instead of tracked where it belongs.

### Rule 7: Transitional documentation sunsets itself

Sections or documents introduced as transitional carry an explicit retirement
plan named at the moment they are added. Without it, transitional sections
ossify into permanent fixtures that misdescribe the current state. (STATUS /
handoff documents are a natural home for transitional orientation; each
transitional claim names what retires it.)

### Rule 8: Sibling revisions / dated corrections over silent edits of point-in-time records

When an authoritative record is found wrong in a load-bearing way, preserve
the original as the planning-time record and add a dated correction
(an Amendments-line entry for an ADR, a sibling note, or an in-situ dated
strike) — never silently rewrite a point-in-time artifact. A silent rewrite
of a point-in-time artifact destroys the traceability the record exists for.

**Extracted record — the audit's dated-correction convention, worked**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md#rule-8))*:
an architectural audit stood explicitly point-in-time and not retro-edited — where a
worker overstated, the original text stood verbatim and the correction landed in a
later, dated section instead of rewriting the original; frozen commission records that
referenced a file's old location were left intact rather than repointed, because they
are records of what an agent was told, not live links to chase.

### Rule 9: Commissioned-review artifacts are recorded verbatim, in-tree

When work leans on a commissioned review — a delegated audit, a consult, an
adversarial pass — whose verdict the citing session treats as evidence, the
commission prompt and the full report are recorded verbatim, in-tree. The
verdict label does not travel without the artifact's substance; **a verdict
whose artifact cannot be produced on demand is treated as no verdict.**
Verbatim appendices are reference records consumed by pointer-citation, not
read end to end on every consultation — but the digest that fans out over
them is read in full, reconciling this rule with the read-fully-before-citing
discipline (root `CLAUDE.md`).

**Extracted record — the architectural-audit's verbatim-appendix instance**
*(moved verbatim to [history/0005-audit-substrate.md](history/0005-audit-substrate.md#rule-9))*:
a 35-worker architectural audit reproduced every worker's raw output verbatim in a
dedicated appendix, and paired consult records carried both the commission prompt and
the full verbatim report — the scale instance that proves the rule at its largest
measured case.

## Instance bindings (autoharn, 2026-07-13) — the non-portable section

Everything above is project-neutral. This section is autoharn's declaration of Rule 2's
filing-homes table — the one part of Rule 2 that is deliberately NOT portable — and an
adopting project replaces it wholesale with its own (the same core/bindings split
[ADR-0017](0017-the-zero-context-reader.md) already models, applied here to ADR-0005 for
the first time). No `docs/` tree exists in this repository; the five homes below are the
complete, current declaration, each named for what it actually holds today:

- **Design notes and specs** — planning and design documents (this project's `ORCH-*`,
  `MAINT-*`, `USER-*` prefixes) — live under [`design/`](../../design/).
- **Consult / decision records** — an independent review or ruling commissioned and
  treated as evidence, and adjudicated judgment banked to disk — live under
  [`judgment/`](../../judgment/): the numbered `e-series` consults, `rulings/`, and the
  `engine/` panel records.
- **Commissioned research briefs** — a substantive standing research product, and its
  conformance mapping against the corpus — live under [`law/briefs/`](../briefs/).
- **Research write-ups and investigation reports** live under
  [`research/`](../../research/).
- **Fresh-context attestation records** ([ADR-0017](0017-the-zero-context-reader.md)'s
  A:B:C loop output) live under [`attestations/`](../../attestations/).

A record kind this table does not yet cover gets a new bullet here when it recurs
(ADR-0011 Rule 2), not a fabricated new top-level directory guessed under time pressure.

## Consequences

### Positive

- **Lower reconstruction cost.** A reader walking into the corpus cold spends
  less time guessing which docs are current, which references resolve, and
  which numbers mean what.
- **Friction-aligned with development.** The discipline operates at the
  moment of authoring; it doesn't impose a batched cleanup later.
- **Audit trail.** Each rule corresponds to a concrete pattern a real audit
  surfaced; future audits reference the rule rather than re-deriving the
  pattern.

### Negative

- **Per-write authoring overhead.** Each documentation event takes slightly
  longer. Small per write, real in aggregate.
- **Discipline is largely policy, not mechanism — but less than at authoring time.**
  Like ADR-0002 and ADR-0004, this tenet still lives mostly in review and authoring
  habit for Rules 1, 2, 4, 6, 7, 8, and 9 — none of those has a gate. Cross-reference
  *resolution*, however, is no longer purely review's:

  *(Dated correction, 2026-07-13, per Rule 8: at authoring time this bullet read
  "cross-reference resolution is review's, not a CI gate's — a declared review-only
  surface." That is now stale and is corrected here rather than left standing, per this
  tenet's own rule against narrating a known gap without disposing of it.
  [ADR-0017](0017-the-zero-context-reader.md) Rule 2(b)'s
  [`gates/link_integrity.py`](../../gates/link_integrity.py) mechanizes exactly the
  checker this ADR's own Revisit-when #2 called for — every relative markdown link
  target resolves on disk — and runs as a blocking pre-commit step. Rules 3 and 5's
  resolution half is therefore test/CI-gate-grade, not review-only; the rest of this
  tenet's rules remain as declared above.)*
- **Some rules require judgment.** Rule 4 (bare-naming) is nearly
  mechanical; Rule 3 (relation-vs-content) requires a small evaluation each
  time. Reasonable contributors will sometimes disagree.

### Neutral

- **No retroactive rewrite required.** ADR-0004's spirit applies: incremental
  retrofit when files are touched for other reasons; no blanket rewrite pass.
  The point-in-time records (a project's own audits, agent commissions, and
  any result explicitly marked point-in-time) are explicitly NOT retro-edited.

## Revisit when…

1. **A specific rule introduces its own failure mode.** Unlikely; flag as the
   revisit trigger.
2. **Documentation tooling matures enough to mechanize part of the
   discipline.** A cross-reference-resolution checker (does every cited path
   resolve?) is the easiest candidate and is *not* soft — a path either
   points at an existing doc or it doesn't. If one is built, it becomes the
   mechanization of Rule 3/5's resolution half. (ADR-0011 Rule 1 records this
   as the open mechanization.)

   *(Dated note, 2026-07-13, per Rule 8: DISCHARGED.
   [`gates/link_integrity.py`](../../gates/link_integrity.py), commissioned under
   [ADR-0017](0017-the-zero-context-reader.md) Rule 2(b), is exactly this checker —
   merged and wired as a blocking pre-commit step. Recorded here, struck rather than
   silently dropped, so a reader does not chase an already-fired trigger to a dead
   end; see the matching Negative-consequences correction above.)*
3. **A genuinely new failure pattern surfaces** not covered by the existing
   rules. Append the rule rather than starting a new tenet — this tenet is
   shaped to absorb additional disciplines.

## Related

- **ADR-0002 (fail loudly).** This tenet is fail-loudly applied to
  documentation: when a documentation gap exists, name it visibly rather than
  papering over it.
- **ADR-0004 (minimal-touch).** The incremental-retrofit posture for existing
  documentation directly applies ADR-0004: don't blanket-rewrite docs that
  aren't being touched.
- **ADR-0006 (source-file headers).** The companion tenet governing per-file
  header conventions — a specific instance of this discipline at the file
  level.
- **ADR-0017 (the zero-context reader).** The legibility register of the same
  documentation family, and the source of the core/instance-bindings split this ADR's
  own "Instance bindings" section now uses for Rule 2's filing-homes table, and of
  [`gates/link_integrity.py`](../../gates/link_integrity.py), the mechanism that
  discharges Revisit-when #2 above.
- **The extracted audit substrate**
  ([history/0005-audit-substrate.md](history/0005-audit-substrate.md)) —
  the dated architectural audit this tenet was first authored against; Rule 9 (verbatim
  records) and Rule 8 (point-in-time, not-retro-edited, dated corrections) point to it as
  their worked instance.

## What this tenet does NOT mean

- **Not "all documentation is created equal."** ADRs and a project's own audits are
  higher-stakes; commit messages are lower-stakes. The discipline applies to
  all but the formality scales.
- **Not "no documentation churn."** The goal is to reduce DRIFT
  (unintentional staleness), not to freeze documents.
- **Not "documentation must be exhaustive."** Brevity remains a virtue.
- **Not a contribution gate.** A change with imperfect documentation is not
  blocked by this tenet; reviewers flag specific rules proportionately.

## License

Public Domain (The Unlicense).

<!-- doc-attest-exempt: mechanical, content-preserving edit (usability review, ledger row 1180, 2026-07-23, finding 16) -- the single existing word "chocofarm" at its first plain-text mention in this file was wrapped in a markdown link to GLOSSARY.md#omega-and-chocofarm (the Stand-Alone Principle's own first-use-link requirement, GLOSSARY.md#stand-alone-principle, applied here for the first time). No other character in this file changed; the rule content this ADR states is untouched. This mechanical class of edit is authorized by the maintainer's vested-judgment commission for this round (ledger row 1180), not a semantic change to law/ requiring further ceremony. Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for its actual rule content, not just a link wrap. -->
