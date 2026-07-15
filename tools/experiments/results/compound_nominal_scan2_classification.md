<!-- doc-attest-exempt: point-in-time measured-output / evidence record for the second
compound-nominal probe, cited by design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md. It is a results
bank full of deliberately-quoted defect specimens (ADR-0017 Exceptions: quoted defects + point-
in-time records), not maintainer-facing prose to run A:B:C over — same class as the sibling
.out.txt result files beside it. -->
# compound_nominal_scan2 — measured results and hand-classification

EXPERIMENT output, banked as the evidentiary basis for
`design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md`. Regenerate the raw numbers with
`python3 tools/experiments/compound_nominal_scan2.py` (runs saved beside this file as
`compound_nominal_scan2.*.out.txt`). This file adds the hand-classification the script
cannot do, plus the per-angle post-mortems.

## Run parameters (2026-07-13, second attempt)

- Corpus: 174 tracked `*.md` — all tracked markdown minus `vestigial_documentation/**`,
  `judgment/**` (frozen transcripts), the three definition surfaces, and two files carrying
  the `doc-attest-exempt` evidence-record marker (printed by the tool). Wider than attempt
  1's 115 (this run keeps `research/**` in scope).
- All lexicons EMBEDDED in the tool as data (never corpus-derived — the attempt-1 blindness).
- Definition-surface whitelist: 288 GLOSSARY/terms/KEY terms + 27 lexicalized compounds.
- One classifier-repair iteration happened between the first run and the measured run, and
  is disclosed: (a) CLASS 1 — three modifier misparses fixed (verb-s forms like "produces
  theater", superlatives, a handful of zero-derived adjectives); (b) CLASS 2 — five
  classifier bugs found by reading the first run's 11 flags (underscore-stripping glued
  `tlab_finding` into a fake gerund; gerund-modifier labels; single-word labels are
  form-underdetermined; leading parentheticals; header head extraction took the first
  content word, not the phrase head) plus the E-minority condition. The hand-classification
  below was performed ONCE, on the post-repair frozen output. No further tuning followed
  the classification.

## Pre-registered specimen set — recall (from `--specimens`, banked output beside this file)

Registered before building, from the tracker's incident row (ledger row 293) and the
maintainer's commission (row 306):

| id | specimen | class | source | result |
|---|---|---|---|---|
| S1 | "trust story" row label | 1 | pre-repair KR doc, `git b96a8c8:design/ORCH-KR-TITRATION-EXPLORATION.md` | **CAUGHT — global rank 1 of 13,855** (angle A 10.0) |
| S2 | KR §5 table: header "capability for a Haiku-tier consumer" over rows incl. "trust story", "cost to stand up" | 2 | same blob, line 443 | **CAUGHT by E and D** — exactly the two ill-typed rows named; no others |
| S3 | "artifacts spec proof" (attempt 1's only hand-classified weak DEFECT, its #25) | 1 | attempt-1 classification file | **VOID** — the source text is "the formal artifacts (spec + proof)"; attempt 1's tokenizer jammed across parentheses. Not a compound. Consequence: attempt 1's true measured DEFECT precision was 0/40, not 1/40. |
| — | ABox/TBox, TOKEN-OOM (same incident) | — | excluded: acronym class, owned by `gates/doc-legibility/` | n/a |
| — | "cancer B" missing pointer + unpointered citations (same incident) | — | excluded: citation/link-resolution class, owned by `gates/link_integrity.py` + ADR-0017 2(a) | n/a |

Recall on the pre-registered catchable set: **2/2**, both at the top of their rankings.
Negative control: the REPAIRED KR table (live corpus) is NOT flagged by D or E — witnessed
in the banked `--specimens` output.

## CLASS 1 — hand-classified top 50 (master ranking, frozen output in `*.c1.out.txt`)

Verdict scheme (stricter and better-separated than attempt 1's):

- **DEFECT** — inter-noun relation genuinely unrecoverable to a zero-context reader from
  the sentence, the document, or any definition surface (the commissioned class).
- **IDIOM** — Claude-idiom metaphor compound (story/posture/friction/spine/surface/... head),
  undefined anywhere, relation recoverable with effort via one dominant reading. Not
  strictly unrecoverable, but exactly the "consistent malady" register the maintainer
  named; actionable for style/glossary review. The incident's dialect-blindness diagnosis
  (ledger row 293) applies to this band: same-family readers auto-resolve these.
- **FP** — not the target: extraction artifact, adjective/participle+noun, verb misparse,
  established technical/lexicalized phrase, or fully transparent compound.

| # | compound | verdict | why |
|---|---|---|---|
| 1 | trust story | DEFECT (quoted) | the specimen itself; all 10 live sites are attempt 1's design note QUOTING it (exempt context, true shape) |
| 2 | assurance posture | IDIOM | posture-of-assurance recoverable; undefined |
| 3 | correctness story | IDIOM | "the substrate's correctness story" — framed by possessive, story-ABOUT reading dominant |
| 4 | integrity story | IDIOM | same shape, framed |
| 5 | relocation story | IDIOM (borderline DEFECT) | "no relocation story today" — story = procedure/support/plan, several glosses; bolded emphasis softens it |
| 6 | inference hygiene | IDIOM | hygiene = disciplined practice; recoverable |
| 7 | fix narrative | IDIOM | narrative-about-the-fix |
| 8 | probe hygiene | IDIOM | as 6 |
| 9 | documentation landscape | IDIOM | near-standard tech metaphor |
| 10 | software landscape | IDIOM | near-lexicalized |
| 11 | assertion mood | IDIOM | logic/linguistics near-term (assertoric mood), undefined here |
| 12 | apparatus friction | IDIOM | friction-from-the-apparatus |
| 13 | closure friction | IDIOM | |
| 14 | countersign friction | IDIOM | |
| 15 | dependency posture | IDIOM | |
| 16 | gap friction | FP | extraction: true text is "review_gap friction"; `_` split the identifier |
| 17 | granularity friction | IDIOM | |
| 18 | license posture | IDIOM | |
| 19 | recipe friction | IDIOM | |
| 20 | row skeleton | FP | extraction: true text is "2-row skeleton" (number-hyphen modifier) |
| 21 | redaction posture | IDIOM | |
| 22 | migration posture | IDIOM | used by ADR-0017 itself |
| 23 | authority surface | IDIOM (borderline DEFECT) | fragment context; which relation to "authority" is not framed |
| 24 | adoption reflex | IDIOM | |
| 25 | bias instinct | DEFECT (weak) | "the maintainer's bias instinct" — instinct FOR spotting bias vs instinct THAT IS biased: two live readings, opposite valence, nothing disambiguates |
| 26 | cabin altitude | FP | real aviation term (lexicalized) |
| 27 | complete footprint | FP | adjective+noun ("complete" missing from the embedded adjective list) |
| 28 | composition spine | IDIOM | |
| 29 | default reflex | FP | transparent (reflex-by-default) |
| 30 | detector geometry | FP | transparent domain compound (geometry OF the detector) |
| 31 | kernel surgery | IDIOM | single dominant reading (surgery ON the kernel) |
| 32 | lazy instinct | FP | adjective+noun |
| 33 | ledger spine | IDIOM | |
| 34 | reachability spine | IDIOM | |
| 35 | taught reflex | FP | participle+noun |
| 36 | citation currency | IDIOM | currency = being-current; standard sense, but money-metaphor reading interferes |
| 37 | detection geometry | FP | transparent domain compound |
| 38 | justification spine | IDIOM | |
| 39 | rulings spine | IDIOM | |
| 40 | reconstruction tax | IDIOM | tax = recurring cost; recoverable |
| 41 | squirrel tax | FP | resolves in-document (ADR-0017 quotes the maintainer's squirrel line it riffs on) |
| 42 | adjudication surface | IDIOM | |
| 43 | browser surface | IDIOM | |
| 44 | comparison surface | IDIOM | |
| 45 | confabulation surface | IDIOM | house "X surface" pattern; recoverable |
| 46 | consumer surface | IDIOM | |
| 47 | default surface | IDIOM | |
| 48 | error surface | IDIOM | |
| 49 | gaps surface | FP | verb misparse: "operational gaps surface from the findings journal" — "surface" is the verb |
| 50 | gate surface | IDIOM | |

### Tally and measured precision (the commissioned numbers)

| band | STRICT precision (DEFECT only) | ACTIONABLE precision (DEFECT + IDIOM) |
|---|---|---|
| top-10 | 1/10 = 10% (the quoted specimen) | 10/10 = **100%** |
| top-25 | 2/25 = 8% | 23/25 = **92%** |
| top-50 | 2/50 = 4% | 39/50 = **78%** |

Tail: unmeasured below rank 50; the master list has 13,860 candidates and the C-dominated
tail is presumed noise (see angle C post-mortem). Stated per the commission: top-K
precision measured, tail precision unknown and said so.

Reading the strict number honestly: the live corpus's strict-DEFECT incidence is near zero
BECAUSE tonight's known defects were already repaired (commit a4ef32d) — the corpus is
post-treatment. The specimen harness (S1: rank 1) is the evidence the tool finds the strict
class when it exists; the live ranking shows what the top of the list is made of meanwhile:
almost purely the Claude-idiom metaphor-compound register, at 100%/92%/78% actionable
precision. Attempt 1 measured ~2.5% (actually 0% after the S3 correction) with recall 0 on
the specimen; this ranking is not the same instrument class.

### Frame-sensitivity note (borderline calls)

"Correctness story" framed by a possessive in running prose is recoverable; "trust story"
bare in a table cell was not. Several IDIOM verdicts above would harden to DEFECT if the
same compound appeared as a bare label. The static tool cannot judge frames, but it can see
POSITION: a CLASS-1 hit inside a table label cell is strictly worse than the same bigram in
prose. (Cross-check wired: the CLASS-2 scanner independently walks table labels.)

## CLASS 2 — live-corpus results (frozen output in `*.tables.out.txt`)

- 120 markdown tables in the 174-doc corpus.
- Flagged label columns after the classifier repairs: **2**, both angle F (empty
  label-column header — a sound structural fact, zero judgment):
  `design/ORCH-COMPOUND-NOMINAL-DETECTION.md:396` (attempt 1's own comparison matrix — an
  empty corner cell, conventional for comparison matrices, benign) and
  `design/USER-WORK-STATUS-OFFERING.md:64` (the edge case attempt 1 also found).
- Angle E and D live flags: **0**. Combined with S2 caught and the repaired-table negative
  control clean, the measured false-positive load of E+D on this corpus is zero, at the
  honest price that their live true-positive count is also zero (incidence ~0 post-repair —
  the same finding as attempt 1, now with a detector that demonstrably fires on the
  archetype instead of a hand-run broadcast).
- The first, pre-repair run flagged 11 columns; all 9 E/D flags were classifier
  misparses (enumerated in Run parameters above), which is itself a measured result: the
  form classifier's error modes are identifier-shaped labels and single-word labels, and
  both are now handled structurally (underscores preserved; single words classified
  form-underdetermined).

## Per-angle post-mortems (dead angles get their paragraph)

- **A (metaphor-head x definition-surface): the load-bearing angle.** 184 candidates,
  precision above. Its stated incompleteness is real: a defect compound whose head is not
  in the curated lexicon is invisible. Its soundness story held: everything it flags IS a
  metaphor-headed undefined compound; whether that is a defect stays a human call, which is
  what report-only means.
- **B (borrowed-head statistic): DEAD standalone, alive as a feature.** Standalone top-25 is
  a flood of non-nominal second words ("act becomes", "answer lands", "alone today"):
  the ratio cannot distinguish "never determinered because it is not a noun" from "never
  determinered because it is a borrowed-sense noun". Fixing that requires knowing nounhood
  — i.e. the lexicon B was supposed to avoid. It survives as a +1 boost inside A's score,
  where the curated head lexicon already supplies nounhood. Banked: `*.angleB.out.txt`.
- **C (embedded-POS-lite novelty, the attempt-1-done-right control): flood confirmed, miss
  fixed.** 13,459 candidates; the top is an alphabetical tie of hapax bigrams. It DOES emit
  "trust story" (attempt 1's structural recall-0 is repaired — the blindness was the
  corpus-derived lexicon, exactly as attempt 1 diagnosed), but expected strict precision is
  ~2 in 13,000: Downing's wall, measured again from the other side. The verdict "N+N shape
  detection is not defect detection" is CONFIRMED for unranked shape detection — and
  overturned as a verdict on the whole task, because ranking by head-idiom (A) was
  available all along. Banked: `*.angleC.out.txt`.
- **D (unanchored form-parallelism): alive, narrow.** Caught S2 (3 VP vs 2 NOM). Zero live
  flags after repairs. Its one-sidedness is structural: uniform forms prove nothing (the
  form-parallelism proxy misses nominal-only cross-division entirely).
- **E (header-anchored form typing): the sharper CLASS-2 angle.** Caught S2 with the exact
  two rows. Fires only on its small header-head lexicon; the minority condition (≤50%
  mismatch) is what separates "an ill-typed element" from "my lexicon disagrees with this
  table's convention" — the pre-repair run measured why that condition is needed.
- **F (empty-header lint): sound, tiny, kept** — attempt 1's conclusion, unchanged.
