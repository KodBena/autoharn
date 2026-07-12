# Detecting the "trust story" defect: compound-nominal ambiguity in LLM-authored prose

> **Status: design-space exploration. No ratification attached, none required.** This note
> answers a maintainer commission (tracker item `compound-nominal-defect-detection`, opened
> 2026-07-13) with a name for a documentation defect, a formal description of its detectable
> shape, and a **measured** feasibility verdict against this repository's own static-analysis
> assets. It recommends a process stopgap and files the mechanical version as not-yet-feasible
> with the numbers that would change that. It changes no gate and binds no one.

## What this is about, in plain words

On 2026-07-13 the maintainer read `design/ORCH-KR-TITRATION-EXPLORATION.md` (a
knowledge-representation titration exploration; "KR" = Knowledge Representation, and the "KR
document" below is this file) — a document that
had already passed a fresh-context (A:B:C) attestation as CLEAN — and caught a table row
labelled **"trust story"**. Two nouns jammed together with no stated relation between them: is
the claim that a Haiku-tier consumer *trusts a story*? that a capability *is* a trust story?
that there exists a *story about trust*? A reader who was not in the authoring session cannot
recover which. Under [ADR-0017](../law/adr/0017-the-zero-context-reader.md) clause 1(b) a table
row label is a **referent** the reader must be able to resolve, and this one does not resolve.

The maintainer made three claims about this defect and asked whether the repository's existing
static language tooling — the acronym gate at `gates/doc-legibility/` and the shape gate at
`gates/doc_shapes.py` — can be brought to bear on it. The claims:

1. the failure mode is **common** in LLM-authored prose across this repo;
2. it is **well-shaped** enough for static grammar analysis to detect;
3. a linguist could **name** the pattern.

This note evaluates all three. The short answers: claim 3 is correct (the pattern has a
settled name); claim 1 is **not** borne out as a distinct high-frequency class by the crude
scan (true novel-coinage defects are rare against a flood of legible compounds); claim 2 is
**half true** — the N+N *shape* is detectable with a real part-of-speech tagger, but shape
detection is not defect detection, and the gap between them is the whole problem.

**A second defect class, added mid-investigation (maintainer, 2026-07-13).** The same KR
document carried a second, related defect the maintainer named: **table label-column type
incoherence**. Its table header "capability for a Haiku-tier consumer" ran over five rows, of
which two ("trust story", "cost to stand up") silently switch type from *capability* to
*property-of-the-option* — and two independent fresh-context B reviewers blessed the table
anyway. The maintainer proposed a mechanical test: distribute (broadcast) the label-column
header over each row label ("header + ': ' + label") and require every concatenation to read as
a well-formed phrase of the type the header declares. This note treats it as the companion
class it is: Part 1 names it, Part 2 formalizes the broadcast test, Part 3 measures the table
surface, Part 4 relates the report-only detector to the maintainer's companion prevention idea
(a typed table constructor, filed separately). The two defects share a spine — both are a
declared or implied *type* that a coinage or a row silently violates — and the same wall:
enumerating the surface is mechanical, judging the violation is semantic.

## Part 1 — The name (linguistics and plain-language literature)

The defect sits at the intersection of two literatures, and the distinction between them
matters for what a checker could ever do.

**Noun-noun compound (complex-nominal) semantic-relation ambiguity.** The head term from
theoretical linguistics is the **complex nominal** (Levi, *The Syntax and Semantics of Complex
Nominals*, 1978). Levi's account is that an N+N compound is derived by **deleting a predicate**
that related the two nouns, leaving only the arguments — and that the deleted predicate is
drawn from a small set of **Recoverably Deletable Predicates (RDPs)**: CAUSE, HAVE, MAKE, USE,
BE, IN, FOR, FROM, ABOUT. "Apple pie" is `pie MAKE-FROM apple`; "night flight" is `flight IN
night`. The word *recoverably* is the load-bearing one: the compound is legible precisely when
the reader can recover which predicate was deleted. The known failure of Levi's own system —
that some compounds admit **more than one** deletable predicate — is not a flaw in the theory
here; it *is* the defect. "Trust story" offers the reader no way to choose among BE, ABOUT,
HAVE, or USE, so the deletion is not recoverable.

Downing (*On the Creation and Use of English Compound Nouns*, Language, 1977) is the empirical
counterweight and the reason no purely mechanical fix exists. Downing showed experimentally
that the relations holding novel N+N compounds together **cannot be captured by any finite
list**; appropriateness depends on use, context, and the interpreter's world knowledge. In
other words, whether a novel compound is legible is a **pragmatic** judgment, not a syntactic
property — which is exactly why a grammar-only checker cannot decide it.

**The plain-language "noun string" prohibition.** The applied-writing literature names the same
thing from the reader's side. The US Federal Plain Language Guidelines (the standard the
maintainer's "self-explanatory figure" instinct echoes) devote a section to **noun strings**.
Quoted verbatim (Federal Plain Language Guidelines, Revision 1, May 2011, "Avoid noun
strings"):

> "The bulk of government and technical writing uses too many noun strings – groups of nouns
> 'sandwiched' together. Readability suffers when three words that are ordinarily separate
> nouns follow in succession. Once you get past three, the string becomes unbearable.
> Technically, clustering nouns turns all but the last noun into adjectives. However, many
> users will think they've found the noun when they're still reading adjectives, and will
> become confused." … "open up the construction by using more prepositions and articles to
> clarify the relationships among the words."

The prescribed fix — **add the preposition back** — is the exact inverse of Levi's predicate
deletion: the reader's cure for an unrecoverable deletion is to restore the relation word. So
the defect has one name in theory (unrecoverable-predicate complex nominal) and one in practice
(a noun string / noun stack), and they describe the same object.

**The benign cases the name must exclude.** Not every N+N is a defect, and the literature is
clear on which are safe:

- **Lexicalized compounds** ("olive oil", "end user"): the relation is frozen by convention;
  no reader recovers it fresh because none needs to.
- **House terms of art with a definition surface** ("row hash", "birth chain", "kernel
  delta"): coined, but *resolvable* — [GLOSSARY.md](../GLOSSARY.md) or the kernel schema names
  the relation, so ADR-0017 clause 2(a) is satisfied.
- **Transparent ad-hoc compounds** ("failure mode", "audit trail", "ledger row"): novel to no
  one, relation recovered instantly via a single Levi RDP.

The defective case is the residue: **a novel coinage, relation not recoverable from a single
obvious RDP, and no definition surface anywhere.** "Trust story" is the whole of that residue
in one specimen.

### The second class also has a name — a stronger one

The table defect is *not* the same as compound-nominal ambiguity, and its name comes from
logic and taxonomy, not lexical semantics. Three converging labels:

- **Faulty parallelism** (the applied-writing name). Standard style guidance holds that every
  item in a series or list must share the same grammatical and logical category — "when items
  belong to the same category logically, they should belong to the same category grammatically"
  (parallel-structure guidance, e.g. university writing centers). This is the *weakest*
  framing: the KR rows are all grammatically noun phrases, so they pass a purely grammatical
  parallelism check while still failing on type. Faulty parallelism names the smell but
  under-describes the defect.
- **Violation of a single *fundamentum divisionis* / the cross-division fallacy** (the
  logic name, and the precise one). In the theory of logical division, a genus is divided into
  species along exactly one **basis of division** (the *fundamentum divisionis*); using two or
  more bases at once is the **cross-division** fallacy. The textbook example — dividing students
  into "tall, intelligent, fair, and backbenchers" — mixes four bases (height, intelligence,
  complexion, seating), and is structurally identical to mixing "capability", "property", and
  "cost" under one header. The table header **is** the declared *fundamentum divisionis*; every
  row label must be a species under that one basis.
- **Category mistake** (Ryle's ontological term) names the per-row form of the same failure: it
  predicates membership in one category ("a capability") of something that belongs to a
  different one ("a cost"), which is the individual-row version of the whole-table
  cross-division.

This repository already owns the engineering form of the same principle:
[ADR-0008 classification discipline](../law/adr/0008-classification-discipline.md) and the MECE
requirement (Mutually Exclusive, Collectively Exhaustive) are the constructive statement of
"one *fundamentum divisionis*, exhaustively partitioned". The table defect is a MECE violation
on the label axis — the maintainer's broadcast test is a lightweight MECE check a reviewer can
run by eye.

**The formal-side name, and a convergence worth stating plainly.** Put the same object in the
vocabulary of type theory rather than taxonomy and it has a one-line name: a table is a
**structured product type** — each row is a tuple typed by the column headers, and the label
column's header is a **type former** whose row labels must all be **inhabitants** of the type
it declares. The defect is then simply an **ill-typed element of a product (record) type**: a
row whose label does not inhabit the header's type, the exact analogue of putting a `str` where
the record field is typed `Capability`. The maintainer's broadcast test is a human-readable
**type-checking procedure** — one witness of ill-typing, not the definition of it. This is the
convergence the maintainer values and it is real: the **linguistics/plain-language** tradition
(parallelism, "coordination of likes", taxonomy category coherence) and the **type-theory**
tradition (well-typedness of a record's fields) are naming the *same shape* from two sides — a
homogeneity constraint on a set of items presented as members of one declared kind. This
project's own constitutional law is on the type-theory side: [ADR-0000, type-driven
design](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md), whose whole thesis is
"make illegal states unrepresentable" — which is precisely why the durable fix for this defect
is a constructor that refuses an ill-typed row (Part 4), not a checker that flags one after the
fact.

## Part 2 — The detectable shape, formally

State the target as a token pattern and the benign classes it must not swallow:

- **Target:** an adjacent run of two or three **common nouns**, all-lowercase (the defect
  profile; capitalized runs are proper nouns and house Titles), where the run resolves to **no**
  definition surface — not GLOSSARY.md, not `gates/doc-legibility/terms.md`, and not an inline
  gloss in the same document. This is deliberately the **same architecture** as the acronym gate
  (`gates/doc-legibility/check.py`): flag a token shape, subtract everything that resolves to a
  known definition, report the remainder. One abstraction up: the atom is a multi-word nominal
  rather than a `≥2-uppercase-letter` token.
- **Must not flag "row hash", "birth chain", "kernel delta":** covered by the GLOSSARY/terms
  whitelist (the definition-surface subtraction).
- **Must not flag "olive oil":** covered by a small lexicalized-compound list.
- **Must not flag "failure mode", "audit trail":** **not covered by anything** — these are
  transparent, undefined, and legible. This is the class no subtraction removes, flagged in
  Part 3 as the precision killer.

The pattern needs **part-of-speech (POS) tagging** to identify the "common noun" runs — specifically
to separate N+N ("trust story") from adjective+noun ("live session", "fresh context") and
verb+noun ("trust boundaries", "records procedures"). The prototype in Part 3 has **no**
tagger; it approximates one two ways, and measuring how far that approximation gets is the
point of the exercise:

- **A corpus-derived noun lexicon.** A word is treated as noun-capable if it was seen
  somewhere in the corpus in a determiner or preposition slot ("the *trust*", "of *trust*") —
  a slot that strongly selects nouns.
- **Adjective/participle suffix morphology.** A word ending `-al/-ive/-ous/-ing/-ed/-ly/…` is
  treated as a modifier, not a head — this is what catches deverbal heads like the `-tion`/
  `-ance` nominalizations and drops adjectives like "structural", "deductive".

The dependency posture forces this crudeness and is worth stating: every gate under `gates/`
is **Python-stdlib only**, and the no-lazy-imports law (CLAUDE.md, 2026-07-02) means a real
tagger (spaCy, NLTK) would be a top-of-file import paid by every importer. Adding a
natural-language-processing (NLP) dependency to the gate chain is therefore a **maintainer decision**, not something a gate
author may reach for unilaterally — so the honest feasibility question is first "how far does
stdlib-only crudeness get?", and only if that is promising does the dependency question arise.

### The broadcast test, formally (second class)

The table defect's shape is cleaner to state and its mechanical part is genuinely sound —
because the *enumeration* needs no POS tagging, only markdown parsing. State it in the general
form (the maintainer's 2026-07-13 refinement): a table is a **structured product type**, the
label-column header `H` is a **type former**, and every row label `L1…Ln` must be an
**inhabitant of the type `H` declares** — whatever that type is. The defect is an ill-typed
element. The **broadcast test** is one human-readable witness of ill-typing: for each `Li`, the
concatenation `H : Li` must read as a well-formed phrase of type `H`. (The header need not be a
question and the labels need not be answers — that "does the row answer the header?" reading was
a one-off approximation for the KR table, not the general rule; the general rule is
inhabitation of whatever type the header names, e.g. a `Directory` column whose rows are all
directories, a `Lens` column whose rows are all lenses.) The KR specimen, broadcast:

| broadcast `H : Li` | well-formed instance of `H` ("a capability")? |
| --- | --- |
| capability … : look up one fact | yes |
| capability … : enumerate current facts | yes |
| capability … : detect a contradiction | yes |
| capability … : trust story | NO — a property, not a capability |
| capability … : cost to stand up | NO — a cost, not a capability |

Two of five rows fail. What is **mechanical**: parsing the table, extracting `H` and each
`Li`, and emitting the `n` concatenations for review — this is a pure surface operation, done
soundly by the prototype's `--tables` mode over the whole corpus. What is **semantic**: the
yes/no in the right column. Deciding "cost to stand up" is not a capability requires knowing
what a capability is — a reader's or an LLM's judgment, not a regex's. So the shape splits
exactly where the compound-nominal shape did: enumeration is free and sound; the type-coherence
verdict is not statically computable. (One purely-mechanical sub-signal does exist and is worth
a report-only flag on its own: a label column with an **empty header** cannot be broadcast at
all — no genus is declared — which the prototype finds as an edge case.)

## Part 3 — Measured, not speculated

The prototype is `tools/experiments/compound_nominal_scan.py` (marked EXPERIMENT, not a wired
gate). Its full output is banked at `tools/experiments/results/compound_nominal_scan.out.txt`;
the hand-classification is at `tools/experiments/results/compound_nominal_classification.md`.
Run over 115 tracked `*.md` (excluding `judgment/**`, `vestigial_documentation/**`,
`research/**`, and the definition surfaces — the same exclusions the shipped gates use):

The headline numbers, each a count from the run, not an estimate:

| measured quantity | value |
| --- | --- |
| candidate hits flagged | **15042** (11862 distinct compounds) |
| for comparison — acronym gate's own cry-wolf number | 1619 across 206 docs (ADR-0017 Context) |
| DEFECT-class precision (hand-classified 40-sample) | **~2.5%** (1 weak true positive / 40) |
| precision counting whitelist-worthy house terms as actionable | ~7.5% (3 / 40) |
| recall on the motivating specimen "trust story" | **0** (never emitted) |

Two results decide the verdict.

**It floods.** 15042 hits is ~9x the acronym gate's already-unusable number. The
hand-classified 40-sample (random over the distinct set, seed 42, verdicts and reasoning in the
classification file) is ~36/40 false positives: verb phrases ("ledger implements", "machine
checks"), possessives ("mechanism's mode"), adjective+noun ("fuzzy task", "non-zero exit"), and
— the class that matters — **transparent real compounds whose relation is plainly recoverable**
("failure mode", "phase structure", "audit trail"). Genuine unrecoverable-coinage defects: one
weak instance in forty.

**It misses the specimen.** Probing the prototype directly (recorded in the classification
file): the word "story" never appears in a determiner/preposition slot anywhere in the corpus,
so it is absent from the corpus-derived noun lexicon, so "trust story" is **never emitted**.
The rarity that makes a coinage novel and jarring is exactly what removes its head noun from a
frequency-derived lexicon. A corpus-derived poor-man's-POS is structurally blind to the defect
class it was built to catch. (Meanwhile "row hash", an undefined-in-GLOSSARY house coinage, IS
flagged — a false positive of the whitelist-gap kind; "birth chain" is correctly suppressed by
the whitelist; "failure mode" is flagged, legibly wrong.)

**What would catch "trust story", and why it still would not help.** A real POS tagger would
tag `trust/NOUN story/NOUN` and emit the bigram — solving the miss. But the same tagger tags
`failure/NOUN mode/NOUN`, `ledger/NOUN row/NOUN`, `audit/NOUN trail/NOUN` identically, because
they *are* N+N. The tagger fixes the verb/adjective false positives (Part 3's gaps 1–2 in the
classification file) but not gap 3 — the transparent-compound flood — because that gap is
**semantic**: it is Downing's result that relation-recoverability is not a finite syntactic
property. No amount of grammar analysis computes it. So a perfect tagger moves precision from
~2.5% up to whatever fraction of all-N+N-compounds-in-the-repo are genuinely defective, and the
40-sample says that fraction is very small. The whitelist rescues *coined* house terms but
cannot enumerate the open-ended space of legible ad-hoc compounds.

### Table broadcast test — measured surface (second class)

The `--tables` mode enumerated the corpus's tables (banked at
`tools/experiments/results/table_broadcast.out.txt`):

| measured quantity | value |
| --- | --- |
| markdown tables in corpus | **64** |
| tables with ≥3 body rows (enumeration-shaped, broadcast-testable) | **58** |
| hand-checked for type coherence | ~20 |
| type-incoherent (cross-division) among those | **0** |
| edge case: label column with empty header (un-broadcastable) | 1 |

The enumeration is sound and cheap — finding the 58 testable label columns is trivial and had
zero parsing false positives on this corpus. But the current-corpus incidence of the actual
defect is **~0**: the one named specimen was already fixed (its table restructured, so it no
longer appears), and ~20 hand-checked tables all broadcast as type-coherent. This mirrors the
compound finding exactly: the defect is real but rare, the surface is mechanically enumerable,
and the violation is a semantic judgment no static predicate makes. The broadcast test's value
is therefore as a **reviewer aid** (emit the `H : Li` list, a human/LLM applies the test) and,
more durably, as **prevention at construction** (Part 4) — not as a deterministic red/green
gate, which would have nothing to fire on most of the time and could not judge the rare case
when it did.

## Verdict

**Not feasible as a deterministic gate at acceptable precision, at either the stdlib-crude tier
(measured 2.5%, misses the specimen) or the with-a-real-tagger tier (the flood is semantic, not
grammatical, so a tagger does not rescue precision).** Shipping either would rebuild the
acronym gate's cry-wolf failure that ADR-0017's Context and `gates/doc_shapes.py`'s
measure-first rule exist to prevent. The maintainer's claim 2 ("well-shaped enough for static
grammar analysis") is the near-miss: the *shape* is well-defined and detectable, but
*defectiveness* is relation-recoverability, which static analysis cannot decide.

Claim 1 ("common") is not confirmed as a distinct, separable high-frequency class: novel
unrecoverable coinages are real but rare against the legible-compound background, and no
mechanical predicate isolates them. Claim 3 ("a linguist could name it") is confirmed —
Part 1.

**The table class reaches the same verdict from the other side.** Its enumeration is
sound and cheap (unlike the compound scan, no flood — 58 clean testable columns), but the
type-coherence *judgment* is semantic, and the current-corpus incidence is ~0. So it is not a
deterministic red/green gate either: it would sit silent almost always and could not decide the
rare live case. Its right homes are the reviewer aid and the typed constructor (Part 4). One
purely-mechanical sub-check *is* gate-worthy on its own terms — an **empty label-column
header** (no genus to broadcast against), which is a sound, rare, zero-judgment signal — but
that is a narrow structural lint, not the type-coherence check the maintainer asked about.

What would change the verdict, stated concretely so the next pass does not re-litigate:

- A **measured** precision at or above the bar the shipped gates cleared (`gates/doc_shapes.py`
  shipped its two checks at 0 observed false positives; the acronym gate's disposition needed a
  54% FP cut just to reach KEEP-ADVISORY). A compound-nominal check would need a defect-class
  predicate demonstrated on this corpus at, minimally, the acronym gate's advisory grade — the
  40-sample says the crude tier is two orders of magnitude short.
- Evidence that the transparent-compound flood (gap 3) can be cut by something other than an
  unbounded whitelist — e.g. an LLM relation-recoverability judgment, which is not static
  analysis and belongs with the critic, not a gate.

## Part 4 — Staged path

Because the mechanical gate is not feasible now, the staged path is process-first, with the
mechanical door left open behind a measurement bar.

**Stage 0 (adopt now) — the B-reviewer prompt gains one clause.** The A:B:C fresh-context
audit loop ([ADR-0017](../law/adr/0017-the-zero-context-reader.md), "The fresh-context audit
loop") already runs a zero-context reader (B) over every attested document, and B's briefing
SSOT is the critic prompt at `hooks/doc_legibility_critic.py` (ADR-0017 instance bindings). The
"trust story" specimen proves B's current briefing under-weights one case: **table row and
column labels are referents** (clause 1(b)), and a two-noun label with no stated relation is
the noun-string defect Part 1 names. The stopgap is one sentence added to that briefing — in
substance: *"Treat every table row/column label as a referent under clause 1(b). Flag any
coined noun-noun (or noun-noun-noun) label whose relation between the nouns you cannot recover
from the document or a linked definition — the 'trust story' class. A legible compound resolves
via a single obvious relation (a story ABOUT trust) or a GLOSSARY link; a defective one admits
several and links nowhere."* This costs nothing beyond the loop already running and attacks the
defect where a human-grade reader can actually judge recoverability — which Part 3 shows a
machine cannot. It is a prompt edit to a live hook file, so it is **proposed here, not applied**
(the no-live-hooks-edits rule); the orchestrator wires it when the relevant freeze lifts.

A **second clause** covers the table class, and it is where B most clearly failed (two B
reviewers blessed the KR table): *"For every table, read its label-column header as a type and
check that each row label inhabits that type — broadcast the header over each label ('header :
label') and confirm each reads as a well-formed instance of the type the header names. Flag any
row that switches type (the 'capability … : cost to stand up' class — a cost is not a
capability), and flag any label column with no header at all (nothing to type against)."* This
is the report-only detector for hand-authored tables: the loop already renders the whole
document to B, so the marginal cost is one instruction, and B is exactly the human-grade judge
the type-coherence decision needs.

**Stage 1 (only if Stage 0 surfaces recurrence) — whitelist SSOT, no new surface.** If the
loop keeps catching real compound-nominal defects and they cluster, the whitelist mechanism is
already decided by ADR-0005 Rule 1 and ADR-0017 clause 2(a): **GLOSSARY.md is the single source
of truth** for house coinages, and the fix for a legitimate house compound is to define it
there (and link it on first use), not to grow a gate allowlist. No separate whitelist file
should be minted; that would be a second SSOT for the same fact.

**Stage 2 (deferred, gated on measurement) — a report-only mechanical check.** If and only if a
defect-class predicate is found that clears the measurement bar in the Verdict (which the crude
prototype does not, and a bare POS tagger does not), it would land the way `gates/doc_shapes.py`
landed its checks: **report-only first**, scoped to touched documents, false-positive load
printed in its own header, never blocking until the number earns it. It would extend the
doc-legibility family rather than mint a new gate genus (the acronym gate and the shape gate are
the siblings). Until that predicate exists, this stage stays UNBUILT with the numbers above as
the reason — the same honesty `gates/doc_shapes.py` records for its own declined heuristics. The
one sound, zero-judgment mechanical check that *could* land at this stage independently is the
**empty-label-column-header** lint from the table pass (a structural fact, not a semantic
judgment) — small, but it is the only piece of either class that survives the measurement bar as
a deterministic check.

**The companion — prevention at construction (typed table constructor), filed separately.** The
maintainer's companion idea, recorded here for how it relates rather than specified here:
**generate tables from a typed constructor** so row-type coherence is enforced at *construction*,
not at *review*. In the type-theory framing of Part 1, this is the ADR-0000 move — make the
ill-typed state unrepresentable: a constructor that takes `H` as a type former and accepts only
rows whose label the caller has declared to inhabit `H` cannot emit the "cost to stand up under
a capability header" table, the way a record constructor cannot accept a `str` for a
`Capability` field. The relationship between the two deliverables is clean and worth stating so
neither is mistaken for the other:

| | detector (this note, Stage 0/2) | typed constructor (companion, separate) |
| --- | --- | --- |
| when it acts | after authoring, at review/report | at construction, before the table exists |
| what it does | flags a suspected ill-typed row for a human/LLM to judge | refuses to build an ill-typed row at all |
| covers | hand-authored tables (the existing back-catalog + any prose table) | only tables built through the constructor |
| failure mode | false negatives (semantic judgment, rare defect) | none for its tables, but does not touch hand-authored ones |

They are complements, not alternatives: the constructor **prevents** the defect in generated
tables; the detector is the **report-only net** for the hand-authored tables the constructor
does not produce. Neither subsumes the other, and this note recommends the detector-as-B-clause
(Stage 0) now because it needs no new machinery, while the constructor is the maintainer's to
scope on its own track.

## Related

- **[ADR-0017 (the zero-context reader)](../law/adr/0017-the-zero-context-reader.md)** — the
  law this defect violates (clause 1(b), referents resolve; clause 2(a), coined terms link to a
  definition). Its Context is the direct precedent: the acronym gate's cry-wolf failure is the
  fate this note's Verdict declines to repeat, and its measure-first rule is the bar Part 3
  applies.
- **[ADR-0005 (documentation discipline)](../law/adr/0005-documentation-discipline.md)** — Rule
  1 (one source of truth per handle) fixes the Stage-1 whitelist question to GLOSSARY.md.
- **[ADR-0000 (type-driven design)](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)**
  — "make illegal states unrepresentable", the constitutional basis for the table class's
  type-theoretic framing and for preferring the typed constructor (prevention) over the detector.
- **[ADR-0008 (classification discipline)](../law/adr/0008-classification-discipline.md)** — the
  MECE requirement, this project's engineering form of the single-*fundamentum-divisionis* rule
  the table defect violates.
- **`gates/doc-legibility/check.py`** — the acronym gate; the architectural template (flag a
  token shape, subtract definition surfaces) this note's proposed check would follow one
  abstraction up, and the cautionary tale it must not become.
- **`gates/doc_shapes.py`** — the shape gate; the model for measure-first, report-only-until-
  earned mechanization, and the home a future check would extend.
- **`tools/experiments/compound_nominal_scan.py`** and its
  **`results/`** — the prototype and its banked measured output, the evidentiary basis for
  Part 3's numbers.
- **The literature (compound class):** Levi (1978), *The Syntax and Semantics of Complex
  Nominals* (the RDP account); Downing (1977), *On the Creation and Use of English Compound
  Nouns*, Language 53 (the finite-list-impossibility result); US Federal Plain Language
  Guidelines, "Avoid noun strings" (the reader-side prohibition and the restore-the-preposition
  cure).
- **The literature (table class):** faulty parallelism / "coordination of likes" (writing-style
  guidance); the theory of logical division — a single *fundamentum divisionis*, and the
  cross-division fallacy for mixing bases; Ryle's *category mistake* for the per-row form; and,
  on the formal side, the well-typedness of a record/product type — the convergence Part 1 names
  explicitly.
