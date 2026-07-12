<!-- doc-attest-exempt: point-in-time measured-output / evidence record for the
compound-nominal probe, cited by design/ORCH-COMPOUND-NOMINAL-DETECTION.md. It is a results
bank full of deliberately-quoted defect specimens (ADR-0017 Exceptions: quoted defects + point-
in-time records), not maintainer-facing prose to run A:B:C over — same class as the sibling
.out.txt result files beside it. -->
# compound_nominal_scan — measured results and hand-classification

EXPERIMENT output, banked as the evidentiary basis for
`design/ORCH-COMPOUND-NOMINAL-DETECTION.md`. Regenerate the raw numbers with
`python3 tools/experiments/compound_nominal_scan.py` (full run saved beside this file as
`compound_nominal_scan.out.txt`). This file adds the hand-classification the script cannot do.

## Run parameters (2026-07-13)

- Corpus: 115 tracked `*.md`, excluding `judgment/**`, `vestigial_documentation/**`,
  `research/**` (the frozen survey), and the three definition surfaces.
- Corpus-derived noun-lexicon: 6942 words (seen in a determiner/preposition slot).
- Whitelist: 113 multi-word terms (GLOSSARY.md `##`/`###` headings + terms.md bold leads +
  a small lexicalized-compound list).
- **TOTAL candidate hits: 15042 (11862 distinct compounds).**

For scale: the shipped acronym gate's own cautionary-tale number is "1619 undefined acronyms
across 206 docs" (ADR-0017 Context). This probe flags ~9x that. It is the cry-wolf failure
mode, reproduced.

## Does it catch the live specimen "trust story"? NO.

Probed directly (`scratchpad/probe.py`): `story` never occurs in a determiner/preposition
slot anywhere in the corpus, so it is absent from the corpus-derived noun-lexicon, so the
`trust story` bigram is never emitted. **The rarity that makes a coinage novel and jarring is
exactly what removes its head noun from a corpus-derived lexicon.** A frequency-based
poor-man's-POS is structurally blind to the defect class it was built for. (`row hash` — an
undefined-in-GLOSSARY house coinage — IS flagged; `birth chain` is correctly whitelisted;
`failure mode` — transparent and legible — is flagged as a false positive. So the probe misses
the one true defect and fires on the legible majority.)

## Hand-classified sample (40 distinct compounds, seed=42 random over the distinct set)

Categories: **DEFECT** = novel N+N whose inter-noun relation is genuinely unrecoverable to a
zero-context reader; **HOUSE** = a real N+N coinage that should be whitelisted (resolvable via
GLOSSARY/kernel, benign); **FP** = not the target at all (verb phrase, possessive, adj+noun,
clause fragment, or a transparent compound whose relation is plainly recoverable — Levi's
HAVE/IN/FOR classes).

| # | compound | verdict | why |
|---|---|---|---|
| 1 | correction-is-a-new-entry mechanism | FP | inline-glossed hyphenated descriptor, not a bare N+N |
| 2 | instrument's none | FP | possessive + "none"; not a compound |
| 3 | insert lag | FP | verb+noun; "lag on insert", relation recoverable |
| 4 | fixtures mutation | FP | transparent ("mutation of fixtures", Levi HAVE/OF) |
| 5 | kind review's attestation | FP | possessive chain |
| 6 | fuzzy task | FP | adj+noun ("fuzzy" adj missed by suffix rule) |
| 7 | changes git state | FP | verb clause |
| 8 | non-zero exit | FP | adj+noun |
| 9 | records test procedures | FP | verb + N+N |
| 10 | caller cannot ignore | FP | clause fragment |
| 11 | adoption switch | FP | transparent ("switch for adoption", Levi FOR) |
| 12 | first-person substrate | FP | adj+noun |
| 13 | time two | FP | "at time two" fragment |
| 14 | ledger hook | FP/HOUSE | transparent house term ("hook on the ledger") |
| 15 | used twice | FP | verb+adverb |
| 16 | taxonomy itself | FP | noun+pronoun |
| 17 | close registry already | FP | verb clause |
| 18 | sides ledger token | FP | "both sides' ledger token", recoverable in context |
| 19 | makes part | FP | verb+noun |
| 20 | gates conventions | FP | transparent ("conventions of gates/") |
| 21 | prose carry | FP | noun+verb |
| 22 | fix re-mints | FP | noun+verb |
| 23 | countersign obligation | HOUSE | kernel term (`countersign_obligation`, in GLOSSARY) |
| 24 | contradiction demo | FP | transparent ("demo of a contradiction") |
| 25 | artifacts spec proof | DEFECT? | N+N+N, relation genuinely murky — weak true positive |
| 26 | maintainer's verdict stands | FP | possessive + verb |
| 27 | error axis rule | FP/HOUSE | "error-axis rule" (ADR-0012), recoverable coinage |
| 28 | end user | HOUSE | lexicalized common compound (missed by whitelist) |
| 29 | edge result rows | FP | "edge-result rows", recoverable |
| 30 | future reader | FP | modifier+noun, transparent |
| 31 | letter says | FP | noun+verb |
| 32 | phase structure | FP | transparent ("structure of the phases") |
| 33 | ledger implements | FP | noun+verb |
| 34 | strategy fixtures use | FP | N+N+verb clause |
| 35 | service gates | FP/HOUSE | transparent house term |
| 36 | mechanism's mode | FP | possessive |
| 37 | machine checks | FP | noun+verb / transparent ("automated checks") |
| 38 | defeaters non-monotone defaults | FP | domain jargon run (logic-marriage doc) |
| 39 | properties none | FP | noun + "none" |
| 40 | didn't author | FP | verb clause |

### Tally

- **DEFECT (genuine target): 1** (weak — #25, an N+N+N whose relation is arguably murky).
- **HOUSE (whitelist-worthy real coinage): 2–3** (#23, #28, and #14/#27/#35 borderline).
- **FALSE POSITIVE: ~36.**

### Precision estimate

- Precision for the DEFECT class: **1/40 = 2.5%** (and the one hit is a borderline call).
- Even counting HOUSE terms as "actionable true positives" (worth a whitelist entry):
  **~3/40 = 7.5%.**
- Recall on the one specimen the maintainer named: **0/1** ("trust story" not emitted).

A gate at 2.5% precision that misses the motivating specimen is the acronym-gate failure at
higher stakes. The measured verdict is NOT-FEASIBLE at the crude tier.

## What the false positives actually are (root cause)

The FPs are not tuning noise; they are three structural gaps a suffix/lexicon heuristic cannot
close without a real part-of-speech tagger:

1. **Verb/noun ambiguity** (`ledger implements`, `machine checks`, `letter says`, `prose
   carry`): most English content words are noun-or-verb; adjacency alone cannot tell which.
2. **Adjective/noun ambiguity** (`fuzzy task`, `non-zero exit`, `first-person substrate`):
   the suffix list catches `-al/-ive/-ing` but not zero-derived or irregular adjectives.
3. **Transparent-but-real compounds** (`failure mode`, `ledger row`, `audit trail`, `phase
   structure`): these ARE N+N, and a POS tagger would confirm it — but their relation is
   plainly recoverable (Levi's HAVE/IN/FOR), so they are legible and must not be flagged. This
   is the gap NO grammar analysis closes: defectiveness is relation-*recoverability*
   (semantics/pragmatics), not the N+N shape.

Gap 3 is the load-bearing one: even a perfect tagger flags every N+N, of which the
overwhelming majority in this corpus are legible. The whitelist covers *coined* house terms
but not the open-ended space of ad-hoc transparent compounds.

---

# Second defect class — table label-column TYPE INCOHERENCE (cross-division)

Run with `python3 tools/experiments/compound_nominal_scan.py --tables` (banked at
`table_broadcast.out.txt`). This mode does the MECHANICAL half only: enumerate every markdown
table, extract the label column's header + each row label, emit the maintainer's broadcast
concatenation `header : label`. The type-coherence JUDGMENT is semantic and stays with a
reader.

## Measured surface (2026-07-13)

- Markdown tables in corpus (115 docs, same exclusions): **64**.
- Tables with >=3 body rows (enumeration-shaped, broadcast-testable): **58**.

## Hand-checked sample (~20 tables read for type coherence)

Tables read: ORCH-DIRCLASS `Directory`; MAINT-REGULATOR-ADOPTION `Lens`; ORCH-DEPLOYMENT-ROADMAP
`Milestone`; ORCH-LEDGER-LOGIC-MARRIAGE `Judgment (consumer)`; ORCH-LOGIC-LAYER-ASP `mutation`;
ORCH-LOGIC-LAYER-SEAM `member`/`mutation`; ORCH-RETROSPECTIVE-RUN10/11 `Phase`;
ORCH-SPEC-DECOMPOSITION-POLICY `Criterion`; ORCH-SPEC-RESOURCE-ACCOUNTING `TIER`;
USER-BLESSED-TABLE-TEMPLATE `NAME`; USER-GPG-TRUST-LAYER-FAQ `You did`; USER-WORK-STATUS-OFFERING
`Omega capability` and one EMPTY header; gates/doc-legibility/README `surface`;
ADR-0007 `Content`; BRIEF-CONFORMANCE-MAP `Inv`/`Item`.

- **Type-incoherent (cross-division) in the current corpus: 0 of ~20 hand-checked.** All rows
  broadcast as well-formed instances of their header's declared type.
- **One edge case:** `USER-WORK-STATUS-OFFERING.md:64` has an EMPTY label-column header — the
  broadcast test cannot run (no genus declared). A label column with no header is its own minor
  legibility note, distinct from incoherence.

## The specimen the maintainer named — caught by the test, already fixed in the corpus

The live specimen was `design/ORCH-KR-TITRATION-EXPLORATION.md`'s table, header
**"capability for a Haiku-tier consumer"**, rows {look up one fact, enumerate current facts,
detect a contradiction, trust story, cost to stand up}. Applying the broadcast test to that
ORIGINAL (the row content is quoted in this note's design doc from git `e4f21bf`):

| broadcast | reads as the declared type ("a capability")? |
| --- | --- |
| capability … : look up one fact | yes |
| capability … : enumerate current facts | yes |
| capability … : detect a contradiction | yes |
| capability … : trust story | NO — a property, not a capability |
| capability … : cost to stand up | NO — a cost, not a capability |

Two of five rows silently switch type. The mechanical enumeration surfaces the exact five
concatenations a reviewer must read; the *judgment* that "cost to stand up" is not a capability
is semantic (a human/LLM call), not a regex. The table has since been restructured, so it does
not appear in the current `--tables` run.

## Reading

The table defect is **well-shaped for mechanical ENUMERATION** (finding the 58 testable label
columns is trivial and sound) but the **coherence decision is semantic** — same wall the
compound-nominal scan hit. The current-corpus incidence is ~0 (the one specimen was fixed),
which mirrors the compound finding: the defect is real but rare, and no static predicate
decides it. Value is therefore as a **report-only reviewer aid** (here are the label columns,
apply the broadcast test) and, better, as **prevention at construction** (typed table
constructor — see the design doc's Part 4).
