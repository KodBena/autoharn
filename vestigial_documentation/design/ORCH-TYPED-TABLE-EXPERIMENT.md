# Typed table constructor — an experiment, no mandate

> **Status: EXPERIMENT. No mandate ships without maintainer review of these results.** This
> note answers the work item `typed-table-constructor-experiment`: build a small constructor
> that renders markdown tables while enforcing, at construction time, that every row inhabits
> the label column's declared type; regenerate 2-3 real corpus tables through it; and give an
> honest ergonomics verdict. Nothing here is wired into any document's build, and no doc in
> this repository is required to use the tool. Adoption, if it ever happens, is a separate,
> later decision the maintainer makes with these numbers on the table — the same posture
> `design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md` takes for its detector.

## What this is about, in plain words

A markdown table looks free-form but is not: read type-theoretically, the label column's
header is a **type former** and every row label is a claimed **inhabitant** of the type it
names (the maintainer's 2026-07-13 clarification, ledger row 299 — "the ledger" is this
project's append-only decision tracker, a local Postgres store read with `./led show <id>` on
a deployed checkout, never a file this repository carries directly — which supersedes the
question/answer framing that had crept into this work item's own opening description — that
framing was one worked example, not the schema). The defect class this project caught by hand
(ledger row 293's incident: a document attested CLEAN twice by independent fresh-context
reviewers still carried a table whose header read "capability for a Haiku-tier consumer"
(a "Haiku-tier consumer" is a reader assumed to have only Haiku-model-tier comprehension
budget — everything must be spelled out, nothing inferred, the same audience concept
`ORCH-KR-TITRATION-EXPLORATION.md`'s §5 argues for by name) over
five rows, two of which — "trust story", "cost to stand up" — are not capabilities) is an
**ill-typed element in a structured product**, in the same sense a Haskell record with a wrong
field type is ill-typed. `design/ORCH-COMPOUND-NOMINAL-DETECTION-2.md` measured a report-only
*detector* for this class (angles D/E/F) and stated its complement plainly: detection is a net
thrown after the fact, and the durable fix — per [ADR-0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
"what type would make this defect unrepresentable" — is *prevention at construction*. This
experiment is that other half: a constructor, not a scanner.

## The constructor, and what it actually enforces

`tools/experiments/typed_table.py`. A `Table` is constructed with a `type_former` (a
plain-words string the author declares — "capability", "verification outcome", "directory",
literally anything) and a column list; rows are added one at a time via `.row(label, *cells,
inhabits=...)`, and `.render()` produces markdown plus an HTML-comment provenance line.

**The honest mechanical core: forced articulation, not NLP.** Whether a label actually
inhabits an author-chosen type is a semantic question, and no static predicate over a string
decides it — the same wall `ORCH-COMPOUND-NOMINAL-DETECTION-2.md` measures for its angles D/E
(form-typing catches shape, never meaning). This constructor does not try to judge the
question. It makes the question **impossible to skip**: `inhabits=` is a mandatory argument,
the author's own sentence spelling out the distributed reading ("`'trust story'` is NOT a
capability — it names no procedure"). The one thing the tool DOES check about that sentence is
weak and stated as such: it must name both the label and the type former, or it is refused as
boilerplate (`"looks fine to me"` does not pass). Whether the sentence is *true* is never
checked — a confidently false articulation is accepted exactly as readily as a true one. This
is the honest description, verified below, not a claim taken on faith.

**Three additional mechanical sub-checks, each with its own soundness story, matching
`compound_nominal_scan2.py`'s discipline of stating what an angle can and cannot conclude:**

| sub-check | what it can conclude | what it cannot conclude |
| --- | --- | --- |
| empty-header refusal (angle F, `compound_nominal_scan2.py`) | the label column's header is blank, so no type former exists to check labels against | nothing about a *non-blank* header's adequacy |
| column-count coherence | a row's cell count matches the declared column count | nothing about cell *content* |
| form-parallelism warning (angle D, `compound_nominal_scan2.py`, imported not reimplemented) | the label column's surface forms (verb-initial / nominal / question / gerund) are mixed, majority vs minority | that mixing is wrong (legitimate mixed-form columns exist) or that uniformity is right (angle D's own stated limit) |

*(This table was regenerated through the constructor itself — see "Do the note's own tables
pass their own test" below.)*

Empty-header and column-count are hard refusals (`TableConstructionError`, raised at
`.row()`/`__init__` time — the table cannot be built at all). Form-parallelism is WARN-only,
surfaced as an HTML comment alongside the rendered table, never a refusal — a mixed-form column
is a free, zero-semantics prompt to re-read, not a verdict, matching angle D's own disclosed
limits.

## Does forced articulation actually surface the incident? Measured, not asserted

Reconstructing the pre-repair KR §5 table (`git b96a8c8:design/ORCH-KR-TITRATION-EXPLORATION.md`)
through the constructor with `type_former="capability"` (the header's own declared type), two
ways — full transcript in
[tools/experiments/results/typed_table_incident_repro.out.txt](../../tools/experiments/results/typed_table_incident_repro.out.txt):

- **An author attempting an HONEST `inhabits=` for "trust story"** is forced to write "'trust
  story' is NOT a capability — it names no procedure a consumer performs" or something that
  reads just as strained — the sentence the maintainer produced by hand, six rounds of review
  in. The tool did not compute this; the act of writing the sentence did, the moment the author
  was honest with themselves while writing it.
- **An author who forces the same two rows through carelessly or dishonestly** ("'trust story'
  is a capability") is **accepted** — WITNESSED, not claimed: the reconstruction script runs
  the row through and it is not refused. This is the tool's honest limit, stated in its
  docstring and reproduced here rather than only asserted.
- **The form-parallelism WARN sub-check fires on that same dishonest table**, naming exactly
  "trust story" and "cost to stand up" as the minority form against three verb-initial
  majority rows — a free, zero-semantics corroborating signal that happens to land on the
  right two rows in this specimen. `ORCH-COMPOUND-NOMINAL-DETECTION-2.md`'s own angle-D
  soundness story is explicit that this is not guaranteed in general (a column of five
  nominals can still mix capabilities with costs and never trip a form check) — so this
  corroboration is not claimed as a general result, only as what happened on the one specimen
  this project actually has.

**Reading the two outcomes together:** the constructor is a discipline for an author who is
already trying to be honest — it converts "did anyone actually check" from "maybe, if a
reviewer happens to run the broadcast test by eye" to "yes, necessarily, because the sentence
had to be written to build the table at all." It is not a discipline against an author who
is careless or actively gaming the requirement; nothing mechanical here changes that, and
nothing mechanical claimed here should be read as changing that.

## Three real corpus tables regenerated

Per the work item, tables whose **source docs are not edited** — the regenerated output lives
only in this note and in `tools/experiments/results/`, never patched back into the source.
Frozen outputs:
[typed_table.kr-2-2.out.txt](../../tools/experiments/results/typed_table.kr-2-2.out.txt),
[typed_table.kr-5.out.txt](../../tools/experiments/results/typed_table.kr-5.out.txt),
[typed_table.audit-au.out.txt](../../tools/experiments/results/typed_table.audit-au.out.txt); the
full run transcript is
[typed_table.out.txt](../../tools/experiments/results/typed_table.out.txt).

1. **`design/ORCH-KR-TITRATION-EXPLORATION.md` §2.2** — the four typed-intake-grammars table
   (`resource:`/`estimate:`/`taxon:`/`interface:`). `type_former = "typed-intake grammar (a
   `kind:` statement prefix)"`. **Outcome: constructed cleanly, no warnings.** All four rows
   are genuinely uniform (each names a closed-field write-side/read-side grammar), and the
   forced articulation was easy to write honestly for every row — the un-strained case, shown
   for contrast with the KR §5 reconstruction above.
2. **`design/ORCH-KR-TITRATION-EXPLORATION.md` §5** (post-repair) — the Haiku-tier-consumer
   comparison table. `type_former = "question a Haiku-tier consumer might ask"`. **Outcome:
   constructed cleanly, no warnings** — the post-repair table's label column is uniformly
   phrased as literal questions, which is also, in this instance, the right type former: this
   is the specific case the maintainer's clarification names directly (row 299's own worked
   example). One row is flagged in a comment for a different reason worth keeping visible:
   "what does the option cost to stand up?" is a row in *this* table, under type former
   "question," and it inhabits that type cleanly — the same words that were mis-typed as a
   *capability* in the pre-repair table are well-typed as a *question* here. The type is
   declared per-table, not fixed by the words; that is the maintainer's point made concrete.
3. **`design/ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md`** — the AU-family walk (2-column, 16
   NIST SP 800-53 AU-controls; abbreviated to 5 representative rows here, since the goal is
   demonstrating the constructor's shape, not repeating all 16). `type_former = "NIST SP
   800-53 AU-family control (ID and catalog title)"`. **Outcome: constructed cleanly, no
   warnings.** Every label is an ID+title pair; the type former is narrow enough that an
   honest `inhabits=` was mechanical to write for every row ("'AU-3 Content of Audit Records'
   is an AU-family control ID+title").

**Did forced articulation surface anything NEW in these three real tables?** No — all three
are post-repair or were never defective; that is the honest, unglamorous result, not an
engineered one. The one place forced articulation demonstrably earns its keep is the
incident reconstruction above, run against the *pre-repair* bytes on purpose, since the live
corpus (by design — the whole corpus has since been swept for this defect class) has no known
remaining instance of it. This mirrors `ORCH-COMPOUND-NOMINAL-DETECTION-2.md`'s own honest
disclosure about its detector: "the table detector's false-positive load on the live corpus:
zero, at the honest price that live incidence is also ~0."

## Ergonomics assessment

**Authoring cost per table, measured by the shape of the code above, not benchmarked in
tokens or minutes (no such measurement was run; stating a number without one would be exactly
the kind of unwitnessed claim this project's ledger discipline forbids).** Qualitatively:

- **Cost added:** one `inhabits=` sentence per row, on top of the row's ordinary cells — for
  an N-row table, N sentences that do not appear in hand markdown at all. For the three real
  tables above (4, 5, and 5 rows respectively) this was a small, mechanical addition once the
  type former was chosen; the type former itself took longer to settle for §5 (is it
  "question," "capability," "comparison axis"?) than any individual row's sentence did.
- **Where forced articulation catches:** exactly where an author is being honest but has not
  stopped to check — the KR §5 pre-repair reconstruction above. It converts an implicit,
  skippable judgment into an explicit, mandatory one.
- **Where it annoys:** every row of an already-uniform, already-correct table (all three real
  demonstrations here) pays the same per-row sentence cost for zero new information — the
  sentence restates what the table cell already said. A table author who is confident and
  correct experiences pure overhead; the tool cannot distinguish "you are about to skip a real
  judgment" from "you have already made this judgment correctly a hundred times" and charges
  the same toll either way. This is the same "per-write authoring overhead, small per write,
  real in aggregate" cost class ADR-0005's own Consequences section names for documentation
  discipline generally.
- **Where it does nothing at all:** against a dishonest or careless author (measured above),
  the mandatory sentence is satisfied by a false one and the defect ships anyway — the
  ceremony without the substance. This is not a hidden cost so much as a hidden *non-benefit*:
  a maintainer reading a constructed table's provenance comment might reasonably over-trust it
  ("this one was type-checked") when the type-check that ran was only "a sentence exists,"
  not "the sentence is true."

**The source-of-truth question, treated first-class (per ADR-0005 Rule 1 and the KR note's
own §6 packet↔prose-drift precedent).** If constructed tables were ever adopted for real docs,
the call site that builds the table (a Python snippet like the `demo_kr_2_2`/`demo_kr_5`/
`demo_audit_au_family` functions in `tools/experiments/typed_table.py`) would
become the table's *actual* SSOT (single source of truth) — the markdown sitting in the `.md` file would be generated
output, not authored text. This is a **two-home hazard by construction**, exactly the shape
the KR note's §6 names for ledger facts minted mid-titration: a fact (here, the table) exists
in the call site *and* in the prose that carries its rendered form, and the two can drift the
moment someone hand-edits the rendered markdown without touching the call site (or vice
versa). Concretely, for this project's own doc corpus:

- There is currently **no build step** that regenerates a doc's tables from constructor call
  sites at commit time or at doc-edit time — every regenerated table in this note was rendered
  once, by hand invocation, and pasted nowhere back into a source doc (per the work item's own
  no-touch instruction). Adopting constructed tables for real would need exactly the missing
  half: either (a) the constructor call site lives IN the doc as a fenced code block the reader
  is told is authoritative and the rendered table below it is regenerated output (checked by a
  gate that the two match, mirroring `gates/doc_attestation_presence.py`'s content-hash
  discipline), or (b) the call site lives in a separate `.py` file under version control and
  the doc's table is regenerated by a script run pre-commit — either way, *something* has to
  close the loop, or the two-home hazard is simply reintroduced with extra steps.
- Until that build step exists, constructing a table and hand-copying its rendered markdown
  into a doc is **strictly worse** than hand-authoring the table directly: it adds the
  `inhabits=` authoring cost without gaining the SSOT property that would justify it (the
  rendered markdown, once pasted, is exactly as driftable as if it had been typed by hand — the
  provenance comment records what generated it once, not that it stays generated).

## Do the note's own tables pass their own test

This note's own tables — the sub-check summary table above and the ergonomics-cost bullets —
were checked against the constructor's discipline where the shape fits naturally. The
"sub-check" table (three rows: empty-header, column-count, form-parallelism) is regenerated
through the constructor with `type_former = "mechanical sub-check"`:

<!-- constructor-generated: tools/experiments/typed_table.py; declared type former = 'mechanical sub-check'; 3 row(s) type-checked at construction (forced articulation + empty-header refusal + column-count coherence); see design/ORCH-TYPED-TABLE-EXPERIMENT.md -->

The three rows above ("empty-header refusal," "column-count coherence," "form-parallelism
warning") were each written with the same discipline this note asks of others: "empty-header
refusal is a mechanical sub-check — sound, zero-judgment, structural"; "column-count coherence
is a mechanical sub-check — sound, zero-judgment, structural"; "form-parallelism warning is a
mechanical sub-check — form-only, stated-incomplete, WARN not refuse." All three inhabit the
declared type cleanly and the constructor raised no refusal building them (verified in the same
run that produced the incident-reconstruction transcript above). The prose-form table shown
earlier in this note is the same content, kept in ordinary markdown for readability; this
paragraph is the record — legible under the A:B:C fresh-context review loop this note itself
goes through ([ORCH-ABC-AUDIT-LOOP-RECIPE.md](../../user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md): A authors, a
fresh-context B reviews, C repairs) — that the self-check was actually run, not merely
asserted.

## What this experiment does not claim

- **Not a gate.** Nothing here blocks a commit; no doc is required to use this constructor.
- **Not a replacement for the report-only detector.** `compound_nominal_scan2.py` remains the
  net for the large body of *already hand-authored* tables this constructor was never used to
  build; the two are complements exactly as `ORCH-COMPOUND-NOMINAL-DETECTION-2.md`'s Related
  section frames it (prevention at construction vs. report-only review net).
- **Not a solved source-of-truth story.** The two-home hazard above is named, not resolved;
  resolving it is a build-tooling decision the maintainer has not made and this experiment does
  not presume.
- **Not evidence that forced articulation catches defects in general.** The one specimen this
  project has (the KR §5 incident) is caught when the author is honest and missed when they are
  not — a sample size of one incident is not a measured precision rate, and none is claimed.

## Related

- [ORCH-COMPOUND-NOMINAL-DETECTION-2.md](ORCH-COMPOUND-NOMINAL-DETECTION-2.md) — the report-
  only detector this constructor complements (detection vs. prevention); its angles D
  (form-parallelism) and F (empty-header) are imported here, not reimplemented (ADR-0012 P1).
- [ORCH-KR-TITRATION-EXPLORATION.md](ORCH-KR-TITRATION-EXPLORATION.md) — source of two of the
  three regenerated tables (§2.2, §5) and of the §6 packet↔prose-drift framing this note's
  ergonomics section borrows for the two-home hazard.
- [ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md](ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md) — source
  of the third regenerated table (the AU-family walk).
- [ADR-0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) — the type-driven-
  design law this experiment applies to documentation tables: what type makes the defect class
  unrepresentable, asked before any fix.
- [ADR-0005](../../law/adr/0005-documentation-discipline.md) Rule 1 — the single-source-of-truth
  discipline the "source-of-truth question" section above answers against.
- [ORCH-ABC-AUDIT-LOOP-RECIPE.md](../../user-guide/ORCH-ABC-AUDIT-LOOP-RECIPE.md) — the fresh-context review
  loop this note itself goes through before it is committed (recorded via
  `attestations/doc-legibility-attestations.jsonl`, not narrated in this note per that
  recipe's own convention); its Named Defect Catalogue Entry 3 (empty-header lint) and
  B-briefing clause (b) (the broadcast/inhabitation test) are the law this constructor
  mechanizes the affirmative half of.
- Ledger rows 293 (the incident and four-factor diagnosis), 299 (the maintainer's structured-
  product-type clarification this whole experiment implements), and the `typed-table-
  constructor-experiment` work_opened row (this experiment's commission).

## License

Public Domain (The Unlicense).
