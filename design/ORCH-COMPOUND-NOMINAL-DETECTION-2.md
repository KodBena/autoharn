# Compound-nominal detection, second attempt: a measured, ranked detector — built

> **Status: design-space exploration, second attempt. No ratification attached, none
> required.** This note answers a maintainer commission (tracker item
> `compound-nominal-detection-2-fable-attempt`, opened 2026-07-13 night): he did not accept
> the first attempt's infeasibility verdict — one method failing is method-failure
> induction, not evidence about the task — and commissioned a fresh, best-effort build of a
> static-analysis tool for the same two defect classes, with a pre-registered specimen set
> that must be caught and precision measured on the live corpus. This note reports the
> build and its measurements. Its relation to the first note,
> [ORCH-COMPOUND-NOMINAL-DETECTION.md](ORCH-COMPOUND-NOMINAL-DETECTION.md) (the prior
> attempt this one was commissioned to outdo): **partly supersedes, partly confirms** —
> the split is stated precisely in the Verdict section, and the factual correction the
> first note now needs is proposed there too (per
> [ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 8, as a dated correction,
> not an edit of the point-in-time record).

## What this is about, in plain words

Two documentation defects, both caught by the maintainer on 2026-07-13 in a document two
fresh-context reviewers had blessed (the incident and its four-factor diagnosis are ledger
row 293 — "the ledger" throughout this note is the project's append-only decision tracker,
a local Postgres store read with `./led show <id>` on a deployed checkout):

1. **A coined noun-noun compound whose relation is unrecoverable** — the table row label
   "trust story": is it a story about trust, a property of being trusted, a capability to
   trust? Nothing in the document says.
2. **A table whose label column silently switches type** — a header declaring "capability
   for a Haiku-tier consumer" over five rows of which two ("trust story", "cost to stand
   up") are not capabilities: an ill-typed element in a structured product.

The first attempt measured one detection method (a corpus-derived noun-lexicon scan),
found it flooded at ~2.5% precision while missing the motivating specimen entirely, and
concluded a mechanical check was not feasible. This second attempt built a different
instrument — several genuinely different ones, compared — and the headline results are:

- **Recall on the pre-registered specimen set: 2/2.** "trust story" is emitted at
  **global rank 1 of 13,855** candidates; the original KR table is flagged with **exactly
  the two ill-typed rows named** and no others. The repaired versions of both (the live
  corpus) are correctly not flagged — the detector discriminates, it does not just fire.
- **Measured precision of the ranked compound detector on the live 174-doc corpus**
  (hand-classified, banked): top-10 **100%**, top-25 **92%**, top-50 **78%** for the
  actionable band (unrecoverable coinages + undefined Claude-idiom metaphor compounds);
  10% / 8% / 4% for the strict unrecoverable-only band, on a corpus whose known strict
  defects had already been repaired. Tail precision below rank 50 is unmeasured and
  presumed poor; the instrument is a top-K reviewer aid, and says so.
- **The table detector's false-positive load on the live corpus: zero** (no E/D flags;
  two sound empty-header lints), at the honest price that live incidence is also ~0.

The tool is `tools/experiments/compound_nominal_scan2.py` (EXPERIMENT-marked, stdlib-only,
report-only, runnable standalone); every measured number in this note is regenerable from
it and banked under
[tools/experiments/results/](../tools/experiments/results/compound_nominal_scan2_classification.md)
(the classification file is the evidence spine; four `.out.txt` runs sit beside it).

## The pre-registered specimen set

The specimen set below was fixed before the tool was built, drawn from the commission row
and the incident row (ledger rows 306, 293). The "defect class" column carries 1 or 2 per
the two-item list in the opening section; the detection angles named in the status column
(A-F) are defined in the next section, "What was built".

| id | specimen | defect class | status |
|---|---|---|---|
| S1 | "trust story" (row label in the pre-repair KR — Knowledge Representation — exploration, [ORCH-KR-TITRATION-EXPLORATION.md](ORCH-KR-TITRATION-EXPLORATION.md); the pre-repair bytes are `git b96a8c8:design/ORCH-KR-TITRATION-EXPLORATION.md`) | 1 | must catch — **CAUGHT, rank 1** |
| S2 | the original §5 table of the same KR document (header "capability for a Haiku-tier consumer"; 3 verb-initial rows, 2 noun-initial) | 2 | must catch — **CAUGHT, both ill-typed rows, angles E and D** |
| S3 | "artifacts spec proof" (the first attempt's single hand-classified weak DEFECT) | 1 | **VOID on inspection** — see below |
| excluded | ABox/TBox, TOKEN-OOM | acronym class | owned by the existing `gates/doc-legibility/` gate, per the commission |
| excluded | "cancer B" missing pointer (a coined [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) taxonomy label — the second-hand-authored-copy defect class — cited in the KR doc without a pointer to that definition); unpointered citations | citation/link class | owned by `gates/link_integrity.py` and ADR-0017 Rule 2(a); not compound defects |

The S3 dissolution is a finding about the first attempt's evidence, found while
pre-registering: its "weak true positive" is the text **"the formal artifacts (spec +
proof)"** (`law/briefs/safety-critical-logging/intermediate/sweep-assurance-cases-gsn.md`)
— the first scanner tokenized across parentheses and manufactured a three-noun compound
that does not exist. The first attempt's true measured DEFECT precision was therefore
**0/40, not 1/40**. The second scanner segments at punctuation, so the artifact class
cannot recur.

## What was built — five angles, each with a soundness story

The commission demanded at least three genuinely different attack shapes, each stating
what it can and cannot conclude. The tool's docstring carries the full soundness stories;
the summary, with each angle's measured fate:

**CLASS 1 (compounds).**

- **Angle A — metaphor-head lexicon × definition-surface subtraction.** This is the
  load-bearing angle. It is a curated, weighted, in-file lexicon of Claude-idiom head nouns (story, posture,
  journey, friction, spine, hygiene, surface, ...; enumerated from the commission's seed
  list, a corpus sweep, and the authoring model's own knowledge of its idiom), intersected
  with "resolves to no definition surface" (GLOSSARY.md headings,
  `gates/doc-legibility/terms.md`, inline glosses, a small lexicalized-compound list), and
  boosted by abstract-attitude modifiers ("trust", "assurance"). It can conclude only
  membership in that measurable shape — never unrecoverability itself; that judgment stays
  with the reader the ranked list is FOR. Its stated incompleteness: heads outside the
  lexicon are invisible. 184 candidates on the live corpus; the precision table above is
  essentially this angle's.
- **Angle B — borrowed-head statistic.** This angle inverts the first attempt's blindness:
  a head noun that (nearly) never appears determinered ("the story") but repeatedly appears
  as a compound head is statistically a borrowed-sense import. Measured standalone it is
  **dead** — it floods with non-nominal second words ("act becomes", "alone today") because
  the statistic cannot tell "never determinered because not a noun" from "never determinered
  because borrowed" without knowing nounhood, which is the lexicon it was trying to avoid.
  It survives as a boost feature inside angle A, where the curated lexicon supplies
  nounhood. Its post-mortem is recorded in the classification file.
- **Angle C — the control: attempt 1's architecture with embedded (not corpus-derived)
  lexicons.** It now emits "trust story" — proving the first attempt's recall-0 was an
  artifact of deriving the noun lexicon from the corpus (rarity removed exactly the novel
  heads), not intrinsic to stdlib scanning. And it still floods (13,459 candidates,
  tied at the top by hapax bigrams — word pairs occurring exactly once, which a pure
  novelty ranking cannot order among themselves): this reproduces Downing (1977)'s result
  that novel-compound relations are not finitely enumerable, measured here a second time
  from the other side. Shape detection without idiom
  ranking is not defect detection — attempt 1's core semantic point, confirmed where it
  was actually scoped.

**CLASS 2 (tables).**

- **Angle D — unanchored form-parallelism.** Classify every label's surface form
  (verb-initial imperative / nominal / question / gerund, via embedded verb and determiner
  lists) and flag mixed columns at a stated majority/minority split. Catches S2 with no
  semantics at all (the commission's seed intuition, borne out). One-sided by
  construction: mixed forms ⇒ suspicion; uniform forms ⇒ nothing — a column of five
  nominals can still mix capabilities with costs, and this angle will never see it.
- **Angle E — header-anchored form typing.** The label column's header head-noun, when it
  falls in a small declared type lexicon (capability/operation/step... expect action-form
  labels; directory/file/term... expect nominals; question expects questions), type-checks
  each row's FORM against the header's declared kind. Sharper than D on S2 (names exactly
  the two bad rows). Two honesty conditions, both measured into it: it fires only on its
  lexicon (stated incompleteness), and only when mismatches are a minority — a column
  where every row "mismatches" means the lexicon disagrees with the table's convention,
  not that the table is wrong (the pre-repair run demonstrated why: capability columns
  legitimately written as noun phrases exist).
- **Angle F — empty-header lint.** Sound structural fact, kept from attempt 1; two live
  hits, both benign-by-convention corner cells, reported as facts not verdicts.

**Measured iteration, disclosed.** The first CLASS-2 run flagged 11 columns; reading them
found nine to be classifier misparses (identifier labels glued by underscore-stripping,
gerund modifiers, single-word labels, leading parentheticals, header-head extraction).
All five bugs were fixed structurally, the hand-classification was then performed once on
the frozen re-run, and no tuning followed the classification — the sequence is recorded in
the classification file so the measurement's provenance is checkable.

## Verdict — against the first note's

The first note concluded: *"Not feasible as a deterministic gate at acceptable precision,
at either the stdlib-crude tier (measured 2.5%, misses the specimen) or the
with-a-real-tagger tier."* This attempt's verdict is **constructive**, and it splits the
first note's conclusion into what survives and what does not:

**Confirmed (properly scoped).** The strict judgment "this compound's relation is
unrecoverable" is semantic and stays out of reach of any static predicate — angle C
re-measures Downing's wall, and angle A's soundness story explicitly leaves the final
judgment to a reader. Likewise the table type-coherence judgment proper: E and D check
form, not meaning, and say so. A blocking red/green gate on either class remains
unbuildable at this house's precision bar, on this evidence. The first note's Stage-0
recommendation (B-briefing clauses) and the typed-constructor complement (ADR-0000
prevention-over-detection) stand unchanged.

**Superseded.** The first note's implicit closure — from "my scan floods and misses the
specimen" to "no mechanical predicate isolates them" and a deferred UNBUILT — does not
survive contact with a different instrument, exactly as the maintainer suspected:

1. **The recall-0 was the lexicon, not the task.** An embedded lexicon catches the
   specimen at rank 1, stdlib-only. The first note's claim that "the rarity that makes a
   coinage novel is exactly what removes its head from a frequency-derived lexicon" was
   correct — and was an argument against corpus-derived lexicons, not against static
   analysis.
2. **A ranked report-only instrument at useful precision exists.** Top-10 100% / top-25
   92% / top-50 78% actionable, measured by hand on the live corpus, with the ranking
   function stated. That clears, for a reviewer-aid instrument, the bar the first note
   itself set for what "would change the verdict" (a measured predicate at or above
   advisory grade) — for the actionable band. For the strict band the live corpus is
   post-repair and near-empty; the specimen harness carries that half of the evidence.
3. **The first note's own measured number was wrong.** Its 1-in-40 weak true positive is
   a tokenization artifact (S3 above); its crude tier measured 0/40.

**No intractability argument is claimed.** The commission allowed a formalized
impossibility argument as an alternative deliverable. None is offered, deliberately: what
is actually impossible here (deciding semantic recoverability statically — Downing's
non-enumerability) does not entail what the first note concluded (that no useful static
instrument exists), and this attempt is a constructive counterexample to that entailment.
An impossibility proof of the narrow true statement would decorate the file without
deciding anything the measurements have not already decided.

**The dated correction the first note needs** (proposed here, not applied — the first note
is a point-in-time record and a concurrent-work no-touch item tonight): an Amendments-style
dated appendix stating (a) the 1/40 weak true positive is a tokenization artifact, so the
measured crude-tier DEFECT precision was 0/40; (b) the "misses the specimen" result is a
property of corpus-derived lexicons, not of the stdlib tier; (c) the feasibility verdict is
superseded for ranked report-only instruments by this note's measurements, and stands for
deterministic blocking gates. Any orchestrator-dispatched Sonnet can transcribe that from
this paragraph.

## What the instrument is for (and not)

- **A reviewer aid, today.** `--top 25` is a two-minute read for the maintainer or a B
  reviewer. The undefined-Claude-idiom slice of the actionable band (verdict "IDIOM" in
  the classification file's scheme), surfaced at 92-100% precision, is precisely the
  dialect-blindness class the incident diagnosis named: compounds a same-family reviewer
  auto-resolves and a different-priors reader trips on.
- **A B-briefing feeder.** The open tracker item `abc-recipe-b-prompt-amendment` plans a
  named defect catalogue handed to every B; this tool's ranked findings and the two
  specimen archetypes are the seed the commission for that item asked for.
- **Not a gate.** Report-only by design; exit code carries no verdict. The cry-wolf
  history ([gates/doc-legibility/README.md](../gates/doc-legibility/README.md)) is the
  standing reason, and nothing here re-litigates it. If it is ever wired anywhere, the
  wiring decision is the maintainer's, with these numbers on the table.
- **Dependency posture unchanged.** Stdlib-only throughout; a real POS tagger remains a
  maintainer dependency decision. The measured case for one is now WEAKER than the first
  note assumed: the embedded lexicons already catch the specimen and carry the precision,
  and a tagger would not move the semantic wall (attempt 1's own gap-3 argument, which
  this attempt confirms).

## Related

- [ORCH-COMPOUND-NOMINAL-DETECTION.md](ORCH-COMPOUND-NOMINAL-DETECTION.md) — the first
  attempt; this note partly supersedes and partly confirms its Verdict (the split above),
  and proposes the dated correction it needs. Its Part 1 naming (Levi's recoverably
  deletable predicates; Downing's non-enumerability; noun strings; the *fundamentum
  divisionis* / ill-typed-product-element family) is adopted here unchanged and not
  restated.
- [tools/experiments/compound_nominal_scan2.py](../tools/experiments/compound_nominal_scan2.py)
  — the instrument; its docstring is the SSOT of the per-angle soundness stories.
- [tools/experiments/results/compound_nominal_scan2_classification.md](../tools/experiments/results/compound_nominal_scan2_classification.md)
  — the hand-classification, precision arithmetic, specimen recall transcript pointers,
  and per-angle post-mortems; the four `.out.txt` files beside it are the frozen runs.
- [ADR-0017](../law/adr/0017-the-zero-context-reader.md) — the law both defect classes
  violate (clause 1(b): labels are referents; clause 2(a): coinages resolve); its
  measure-first mechanization rule is the bar this note's numbers answer to.
- [ADR-0011](../law/adr/0011-mechanization-discipline.md) — measured baselines before
  strength, negative controls (the specimen harness and the repaired-table control are
  this note's), and the class-not-instance rule the embedded lexicons deliberately trade
  against, with the trade stated.
- [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) — why the
  durable CLASS-2 fix remains a typed table constructor (prevention), with this detector
  as the report-only net for hand-authored tables; the first note's Part 4 table of that
  complementarity stands.
- Ledger rows 293 (the incident and four-factor diagnosis), 299 (the maintainer's
  structured-product-type clarification the CLASS-2 angles implement), 306 (this
  commission).
