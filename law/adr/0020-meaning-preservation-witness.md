# ADR-0020 — The meaning-preservation witness (no-content-lost never discharges no-meaning-changed)

<!-- doc-attest-exempt: constitutional text authored by Fable and maintainer-ratified
2026-07-23 ("I think small sibling ADR is right, it's an independent concern from
zero-context reader"). Removal condition: a fresh-context A:B:C attestation pass over
the law/ corpus. -->

Ratified 2026-07-23. Provenance: the 2026-07-22/23 setup-TUI arc witnessed one defect
class in five distinct habitats — a schema migration that turned "aspires to NIST SP
800-63's decomposition" into a bare conformance claim by filing the standard's name
into a `standards` field; a synopsis that re-promoted a demoted rule into flat law; a
plain-language edition whose first three review passes each found a distinct severe
meaning change (a swapped referent, six dropped consumer bindings, a reversed
recommendation); a checklist recording untouched defaults as "operator declined"; and
elucidation "fixed" for line length by deleting its content. Every instance passed its
mechanical checks, because every mechanical check attested token conservation or
format, and the defects lived in what the artifact ASSERTS. The causal RCA named the
mechanism the CONSERVATION PROXY: "no content lost" standing in for "no meaning
changed" — every token preserved, the claim strengthened, the edge between tokens
dead (law/adr/history/POSTMORTEM-SETUP-TUI-ARC-2026-07-23.md; the archived RCA record
in design/; ledger rows 1119–1121).

## The rule

**Any operation that migrates, schematizes, summarizes, or re-renders authored
content carries a cold-read meaning-preservation witness alongside its mechanical
invariants.** A fresh-context reader — one who did not perform the transformation —
reads the output against the source and attests: the output asserts no more and no
less than the source asserted (qualifiers, hedges, aspiration markers, speculation
markers, honest ceilings, named exclusions, consumer bindings, and recommendation
polarity all intact), and it serves its declared reader. The operations in scope,
enumerated by shape rather than instance: prose-to-schema and schema-to-prose,
document merges and splits, plain-language or audience-shifted editions, synopsis and
summary derivation, re-rendering content into a new presentation vocabulary, and any
"tidying" pass over authored claims. A transformation commissioned without this
witness clause is an incomplete commission.

Two subsidiary clauses, each a lesson paid for:

1. **Mechanical invariants cannot discharge this witness.** A check that counts
   tokens, elements, lines, or formats attests the delta's contract, not the
   artifact's meaning; passing every such check is compatible with a strengthened
   claim, a dropped hedge, or a reversed recommendation. Where a residue-disposition
   mechanism exists (every span of source text dispositioned as moved, dropped,
   duplicated, or relation-severed), it is a floor under this witness, never a
   substitute for the cold read.
2. **The witness iterates to a clean pass on severe findings.** A pass that finds a
   severe meaning change (truth value, coverage, referent, binding commitment, or
   recommendation direction) proves the class is present in the transformation
   process, not that it caught the last instance: after repair, a fresh reader —
   blind to the prior pass's findings — reads again, until a pass finds none. (The
   provenance arc needed four passes; the three severe-finding sets were pairwise
   disjoint.)

## Relation to neighbors

Independent of ADR-0017 (the zero-context reader), which governs whether a document
is LEGIBLE to a cold reader; this ADR governs whether a transformation PRESERVED what
its source asserted — an illegible document can be faithful and a beautifully legible
one can lie. Composes with ADR-0008 (two distinct facts are not fuzzy-matched into
one; a claim and its qualifier are two facts whose edge must survive) and with
ADR-0002 (the witness's findings are stated loudly, never repaired silently).

*Enforcement surface: spec-time (the witness clause is a required part of any
transformation commission) and the witness act itself; review-only for recognizing
that an operation IS a transformation in scope — that recognition is judgment, and
reading it down is the documented failure mode.*

## License

Public Domain (The Unlicense).
