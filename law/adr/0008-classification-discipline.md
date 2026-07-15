# ADR-0008: Classification Discipline

> *Refactored for cross-project portability on 2026-07-13 under
> [`design/MAINT-ADR-PORTABILITY-SPEC.md`](../../design/MAINT-ADR-PORTABILITY-SPEC.md)
> (tracker `adr-portability-refactor`, maintainer-ratified 2026-07-13). The pre-refactor
> text stands verbatim at commit `ff691bb9bc430ad497d74ff82d580f758a969f99`; extracted
> records live under [`history/`](history/) (each Extraction Pointer below names its own
> destination file) and are not retro-edited. Dated amendments below are preserved
> verbatim from the original. The Scope field below is re-instanced generically at this
> same act (spec §4); the pre-refactor wording (which named this project's own package) is
> the git history at the commit above, not silently lost. The Provenance field, by
> contrast, is a preserved dated record the spec forbids rewording, so it keeps two
> source-project proper names; for the zero-context reader (the field is frozen,
> positional reference is safe): the first project it names is the ancestor whose ADR
> corpus this tenet was transferred from, and the instance substrate named beside it
> (a "Vue knob-domain enum", "chrome-neighborhood mounts") is that ancestor's UI
> machinery, which a reader here is not expected to know; the second project is the
> source project the re-derivation targeted — the same project whose worked instances
> this ADR's `history/` extractions describe. "The audit" throughout this document is
> that source project's 2026-06-15 architectural audit, an artifact of that project, not
> of this repository.*

- **Status:** Accepted
- **Genre:** Tenet (cross-cutting authoring discipline) — the sixth tenet,
  after ADR-0002 (fail loudly), ADR-0004 (minimal-touch), ADR-0005
  (documentation discipline), ADR-0006 (source-file headers), and ADR-0007
  (file size and information density). Sibling of ADR-0002: same shape of
  failure (a category error silently propagating), different intervention
  point — fail-loudly is the *reactive* register (surface a deviation after
  it occurs); classification discipline is the *proactive* register (refuse
  fuzzy matches and synthetic fabrications when a choice is being made
  against a vocabulary).
- **Date:** 2026-06-15
- **Provenance:** Transferred from the LengYue ADR corpus. The two-register
  principle (refuse fuzzy matches against an inadequate vocabulary; refuse to
  fabricate categories under ambiguity) is universal and transfers wholesale.
  LengYue's instance substrate (a Vue knob-domain enum, chrome-neighborhood
  mounts) is re-derived against chocofarm's real classification surfaces — the
  detector-model keying decision, the SSOT vocabulary, the audit's
  band/severity classifications, and the consult-record `kind` choice.
- **Scope:** All authoring work involving classification — picking values from
  closed vocabularies (enum-like choices, action keys, severity tags), placing
  files into the documentation tree, naming categories, and the symmetric act
  of creating new categories under ambiguity. Applies across the whole hosting
  codebase and its documentation corpus; the source project's own surfaces
  (a detector-model keying decision, an SSOT vocabulary, an audit's
  band/severity classifications, a consult-record `kind` choice) are the
  worked instances this ADR's extracted records carry.

## Context

A categorisation made by closest-fit when no true fit exists, or by
fabricated-fit when no honest category exists, silently propagates a wrong
vocabulary through every downstream consumer.

> **Extracted record — the detector-misspec and fossil-array substrates**
> *(moved verbatim to [history/0008-chocofarm-classification-substrate.md](history/0008-chocofarm-classification-substrate.md))*:
> the 2026-06-15 architectural audit that motivates this tenet surfaces both registers in
> its source project. Positive register: a detector model keyed sensing to the closest
> available encoding (a region) when the honest sensing unit was a different, finer thing
> (a face) — the mismatch propagated through six commits before being caught — contrasted
> with an action-key shape that was rightly *preserved* across the same re-keying because
> the vocabulary element still fit. Negative register: a data file kept two superseded
> fossil arrays a reader could not tell were dead, and the audit's own severity vocabulary
> is disciplined about calibrating to the worst case rather than the observed cost.

### Two registers, one principle

The positive register is about consuming a vocabulary; the negative register
is about extending one. Both rest on the same insight: **vocabularies and
taxonomies are honest only when they precisely fit the territory; bridging
gaps with fuzzy-fit or synthetic fabrication is the failure mode.** Both look
legitimate post-hoc and both propagate through every consumer that later reads
the classification as authoritative.

## Decision

We adopt **Classification Discipline** as a codebase-wide tenet. When a choice
involves classification, the choice is honest only if the vocabulary or
taxonomy precisely fits the case. Fuzzy matches and synthetic fabrications are
the failure mode the tenet forbids.

### Positive register — refuse fuzzy matches against an inadequate vocabulary

When choosing from a closed vocabulary and no element is a true match, the
honest move is **revise the vocabulary**, not pick the closest fit. If
vocabulary revision is out of scope for the current arc, the deviation is
filed visibly (a consult record, an inline comment naming the misfit, an ADR
amendment) so the next reader sees the gap rather than reading the
closest-match as a legitimate fit.

> **Extracted record — the detector re-keying instance**
> *(the same substrate the Context pointer above names, [history/0008-chocofarm-classification-substrate.md](history/0008-chocofarm-classification-substrate.md))*:
> the source project's detector model modeled a single-point sensor with the
> closest-fitting encoding available, which turned out to be the wrong vocabulary; the
> fix re-derived the vocabulary itself rather than keep the near-fit.

### Negative register — refuse to fabricate categories under ambiguity

When CREATING a classification and no existing category cleanly fits, the
honest move is **default to flat / leave it un-categorised and named as such**,
not invent a synthetic parent or force a "least-bad" home. A fabricated
category that descriptively fits nothing absorbs ambiguity into the taxonomy,
where the absorbed wrongness becomes the new baseline; a stale categorisation
left standing is as misleading as a fabricated one — the remedy is to strip
the fossil (mark it dead or remove it), not to leave the reader to guess.

### Severity calibration — the substitution test

The discipline is calibrated by what the failure shape would cost on a
critical surface, not by the observed instance's user-visible cost. The
exercise: name the failure shape in its most general form; list the surfaces
to which the same shape could apply; calibrate to the worst case on that list.

> **Extracted record — the reference-rate severity trace**
> *(moved verbatim to [history/0008-chocofarm-classification-substrate.md](history/0008-chocofarm-classification-substrate.md);
> the same underlying incident also grounds [ADR-0002](0002-fail-loudly.md) Rule 6)*:
> the source project's audit found one derived rate hardcoded as two literals that had
> already drifted from each other — one copy a harmless display-only value, the other a
> numerical input to a provable bound. The discipline that catches the harmless copy must
> be calibrated to the worst case the same failure shape could reach, not the one that
> happened to be observed first.

## Concrete rules

1. **Verify vocabulary fit before selecting.** Before picking a value from any
   closed vocabulary (an enum-like choice, a detector action key, a severity
   tag, a directory to file a doc in), check that some element is a true match
   for the case. If none is, name the gap.
2. **Default to flat / named-as-incomplete under ambiguity.** Before creating
   a new classification, ask whether an existing category descriptively fits.
   If yes, use it. If not, leave flat and name the incompleteness. Synthetic
   parents are last resort, not default.
3. **Surface the gap visibly.** When the right move (revise the vocabulary,
   strip the fossil, hold flat) is out of scope for the current arc, file the
   deviation visibly — a consult record (per
   [ADR-0005](0005-documentation-discipline.md) Rule 2; an adopting project
   substitutes its own filing convention, the obligation is the same), an ADR
   amendment, or at minimum an inline comment naming the misfit. Silent
   acceptance is the failure mode this tenet forbids.
4. **Apply the substitution test for severity.** When a category error
   surfaces, calibrate the remediation to what the failure shape would cost on
   the worst-case surface it could apply to, not the observed instance's cost.

## Exceptions

### Temporary, scheduled-for-revision misfit

When the right vocabulary revision is real but its blast radius is large
enough to defer, an inline `# TODO: misfit — see X` plus a follow-up record is
acceptable. The gap is filed visibly; the misfit is bounded; the revision has
a named trigger. This parallels ADR-0002's bounded-compat-shim exception.

### Deliberately-imprecise tag

A tag that *deliberately* admits the classification is incomplete (the
analyzer's "this quantity is detector-coupled and therefore suspect," a STALE
marker on a superseded design-doc specific, the audit's `cited-not-rerun`
evidence tag) is not a closest-match — it is an explicit refusal to classify
until the case firms up, which is the discipline applied to itself. Choosing
one of these is honest; reaching for them to *avoid* choosing an honest fit is
the discipline working as intended.

## Consequences

### Positive

- **Vocabulary integrity over time.** Each addition is forced through "does
  this fit, or does the vocabulary need revising?" — which is exactly the
  question the source project's detector re-keying fix answered (revise the
  vocabulary) and its fossil-array finding flags (strip the dead categories);
  both are carried in the extracted record the Context's Extraction Pointer
  above links.
- **Composes with existing tenets.** ADR-0002's reactive register catches the
  silent symptom; this tenet catches the cause before the symptom forms.
  ADR-0005's documentation discipline (Rule 5, file location reflects content)
  is the documentation register of the negative register's file-placement
  case (the source project relocated a mis-filed consult record for exactly
  this reason).
- **Self-evident audit trail.** When the gap is filed visibly, future readers
  see the gap rather than reading the closest-match as authoritative.

### Negative

- **Per-classification authoring overhead.** Each classification choice now
  carries "does this vocabulary fit?". Small per choice, real in aggregate.
- **Refused fits can stall arcs.** When the honest answer is "revise the
  vocabulary" but the revision is itself substantial (the detector re-keying
  was a multi-file change), the arc may stall on the predecessor revision. The
  mitigation is the scheduled-for-revision exception and Rule 3's gap-filing.
- **Discipline is policy, not mechanism.** Like the other tenets, it lives in
  review and audit. There is no automated check (ADR-0011 Rule 1: a declared
  review-only surface; an enum-coverage or fabricated-parent check would be
  the mechanization trigger).

### Neutral

- **No code change today.** This ADR documents a discipline for future
  authoring; ADR-0004 / ADR-0006's incremental-retrofit posture applies — no
  batched rewrite of existing classifications.

## Revisit when…

1. **A specific rule introduces its own failure mode.** Flag as the revisit
   trigger.
2. **A genuinely new register surfaces** the positive/negative split doesn't
   cover. Append a third register here rather than starting a new tenet.
3. **The substitution test produces calibration that fights another tenet**
   (e.g. a worst-case calibration demanding more loudness than ADR-0002's
   exceptions allow). Reconcile then.
4. **Tooling makes part of the discipline mechanical** — an enum-coverage
   check, a fabricated-parent (single-occupant synthetic directory) detector,
   a fossil-field check on a canonical instance/config file. Tighten the
   corresponding rule toward enforcement as the mechanical surface grows.

## Related

- **[ADR-0002](0002-fail-loudly.md) (fail loudly).** The reactive sibling: its loudness
  hierarchy is where a classification failure that slips past this tenet's two registers
  ends up surfacing — a fuzzy classification that slips through becomes the silent
  symptom ADR-0002's hierarchy catches. This tenet's **positive register** (refuse a fuzzy
  vocabulary match) and **negative register** (refuse a fabricated category) are the
  proactive counterpart to ADR-0002's reactive rules; the two compose at different
  intervention points, neither restates the other.
- **[ADR-0003](0003-domain-coupling-bands.md) (domain-coupling bands).** The
  Band 1/2/3 vocabulary is one of the classifications this tenet protects against
  fuzzy-matching — a module drifting to depend on a fact that properly belongs to a
  different named surface is a band-misfit this discipline catches.
- **[ADR-0005](0005-documentation-discipline.md) (documentation discipline).**
  Rule 5 (file location reflects content) is the documentation-register instance of
  this tenet's negative register applied to file placement (the source project's
  relocation of a mis-filed consult record is the worked case).
- **[ADR-0009](0009-performance-investigation-discipline.md) (performance
  investigation discipline).** The per-domain instance for the perf-claim
  vocabulary — "faster"/"regression"/"no change" is a closed vocabulary;
  substantiation is the fit-verification this tenet implies.
- **The source project's 2026-06-15 architectural audit** — the detector-misspec
  substrate, the reference-rate severity calibration, and the fossil-array
  negative-register instance; all three are carried in this ADR's extracted record
  under `history/` (the Extraction Pointers above link it directly).

## What this tenet does NOT mean

- **Not "every category must be perfect on first pass."** Authoring is
  iterative; the tenet asks for honest "this vocabulary doesn't fit" surfacing
  when it doesn't.
- **Not "all classifications need ceremony."** Trivial one-off names are not
  what this tenet operates on; it applies to classifications that propagate to
  consumers — the detector model, the SSOT vocabulary, severity tags, the
  directory taxonomy.
- **Not a ban on synthetic parents in all cases.** A synthetic parent that
  genuinely captures a real distinction (e.g. an `hp/` package for the
  registry/schema that share a real characteristic) is honest. The tenet bans
  parents that exist *to absorb a misfit*.
- **Not a substitute for fail-loudly.** When the discipline fails in practice,
  ADR-0002's reactive register catches the resulting silent symptom.

## License

Public Domain (The Unlicense).
