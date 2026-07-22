<!-- doc-attest-exempt: verbatim two-phase Fable consult record, commissioned by the maintainer 2026-07-22 (ledger rows 1119-1121). Removal condition: superseded by law incorporation. -->

# Fable consult — elucidation defect diagnosis and causal RCA (2026-07-22)

Commission: maintainer, verbatim: "I'd like to know exactly what it is that made the implementer think this was the right thing to do (don't ask it, post-hoc rationalizations are worthless, instead have a Fable consult speculate on the cause ... do it in 2 phases so as to separate concerns)." Phase 1 ran artifact-blind (rendered specimens only); phase 2 received implementation context. Verbatim below.

## Phase 1 — artifact-only diagnosis

DIAGNOSIS — PHASE 1 (artifact-only). Defects ranked by severity, each stated as an instance of a class.

---

**D1. SEVERITY: CRITICAL — Unwitnessed compliance implication (truth-value inflation via slot promotion).**
Specimen 2's bare line `Standards: NIST SP 800-63` reads, to any operator, as a conformance claim: "this feature meets / is aligned with SP 800-63." The known source material made a strictly weaker claim — the project *aspires to that standard's decomposition*. Rendering the standard's name into a dedicated `Standards:` field detached it from the aspiration that qualified it and promoted it to an unqualified assertion. In a "claims carry witnesses" culture this is the worst available defect: the rendered text asserts more than the source warranted, on exactly the axis (certification against a federal identity standard) where over-claiming is most consequential for a founding operator's trust decisions. CLASS: **lossy decomposition of a compound claim — fielding a sentence changed its truth value; an aspiration was laundered into a standing**.

**D1a (corollary, same root claim).** The aspiration line is left semantically dangling: "identity/lifecycle/binding decomposition" — *whose* decomposition? The referent (the standard) was amputated into the other field. The sentence no longer parses as a complete claim. CLASS: **referential binding broken by decomposition**.

**D2. SEVERITY: HIGH — Internal-provenance leakage across the audience boundary.**
Multiple items address the wrong reader:
- Specimen 1: `(memory: config-fragments-need-the-real-file -- pg_hba lines are never authored without reading the live target file first)` — this is an AI-collaborator's internal memory note about *its own authoring discipline*. A founding operator cannot act on it, cannot verify it, and should never see the assistant's memory namespace at all.
- Specimen 1: "(the omega-lab shape)" — an insider referent to some prior deployment, undefined for a reader founding a NEW deployment.
- Specimen 2: "the s40/s41 family" — internal delta/session numbering, opaque outside the project.
- Both: spec filenames carrying internal process branding (`FABLE-SETUP-TUI-SPEC.md`, `FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md`) presented as if they were operator-meaningful.
CLASS: **audience-boundary violation — internal provenance and workshop vocabulary rendered verbatim into operator-facing surface; the text elucidates the builders' history, not the operator's choice**.

**D3. SEVERITY: HIGH — Unexpanded template placeholder rendered literally.**
Specimen 2: `<dest>/legacy/led`. A raw substitution variable reached the screen. Beyond the local confusion, this is a trust-destroying defect in a high-assurance product: if the renderer ships placeholders, the operator must now doubt every other line. (Compounded by the path itself: a component named `legacy/` presented to someone setting up a *new* deployment, unexplained.) CLASS: **template-expansion failure / broken rendering pipeline visible in product**.

**D4. SEVERITY: HIGH — Category errors in the typed slots (in a project that sells typed structure).**
- Design documents listed under `Mechanism:` in both specimens (`design/FABLE-SETUP-TUI-SPEC.md`, `...BUILD-BASIS.md`). A spec is not a mechanism; it is provenance or rationale. The slot's type is violated.
- Specimen 2's `Aspiration:` slot contains mechanism content ("via the s40/s41 family") — which then reappears, redundantly, as the two `Mechanism:` lines below it.
- Specimen 1's dedicated-path `Aspiration:` says "none named" and then immediately names something ("house config-fragment discipline only") — the slot simultaneously asserts emptiness and carries content.
CLASS: **slot-type violation / cross-contamination — the schema exists but its fields are populated by proximity, not by kind; a typed façade over untyped filing**. For this project specifically, this is a credibility defect: the artifact's own structure fails the standard the project preaches.

**D5. SEVERITY: MEDIUM-HIGH — Field semantics drift between sections.**
`External:` means three different things across the two screens: (specimen 1, existing-db) "no manual steps required"; (specimen 1, dedicated-db) "manual actions a human must perform on another host"; (specimen 2) "no new binaries or packages, and by the way here is what the feature drives internally" (a positive description smuggled into a negation). An operator cannot learn the field's meaning from one section and apply it to the next. CLASS: **inconsistent field semantics — same label, shifting contract; the reader must re-derive the schema per section**.

**D6. SEVERITY: MEDIUM — Empty-slot noise.**
`Aspiration: none named.` (twice). Rendering an empty field as a content line makes the operator read and parse a null. In a decision-support surface, every line should earn its screen space; "none named" is template residue, not information — either suppress the slot or say something the reader can use. CLASS: **schema leakage — the storage shape rendered as the presentation shape; nulls printed as prose**.

**D7. SEVERITY: MEDIUM — Wrong altitude for the stated audience and purpose.**
The frame says: an operator founding a new deployment, *deciding what to enable*. Neither specimen supports that decision. `Mechanism: tools/setup_tui/pghba.py` is meaningful to a maintainer with the repo open, not to an operator at a setup TUI. Meanwhile the information that would actually drive the choice is absent or buried: consequences of each path, reversibility, prerequisites stated as requirements up front (the dedicated-db path's "requires a live, network-reachable Postgres cluster the operator administers" is the single most decision-relevant fact on either screen, and it arrives last, inside the `External:` slot). CLASS: **altitude mismatch — implementation inventory presented where decision guidance was owed; the content answers "what files exist" when the reader asked "what should I choose and what will it cost me"**.

**D8. SEVERITY: MEDIUM — Register failure: "elucidation" that does not elucidate.**
The text is telegraphic ledger-speak — slot: value; slot: value — with no connective explanation. It reads as an audit record or provenance manifest, i.e., writing optimized for the project's *internal* evidentiary culture, presented under a heading role ("elucidation") that promises explanation. The register is honest but non-communicative for its declared reader. CLASS: **register transplant — internal evidentiary register shipped as user-facing explanatory prose**.

**D9. SEVERITY: LOW-MEDIUM — Structural/visual flattening and inconsistency between the two screens.**
- Specimen 1 has no section heading; the grouping is faked by repeating the prefix `Existing-db path --` / `Dedicated-db path --` on every line — a flat key-value dump where two headed sub-sections are the obvious structure. The reader must diff prefixes line-by-line to reconstruct the hierarchy.
- Specimen 2 *does* get a heading (`Principals & authority`) with unprefixed slots — so the same underlying record type is rendered in two different visual grammars within one pane.
- Repeated `Mechanism:` lines instead of a single labeled list.
CLASS: **serialization masquerading as layout, applied inconsistently — the renderer has no stable presentation grammar for its own record type**.

**D10. SEVERITY: LOW — Typographic hygiene.**
ASCII double-hyphen `--` doing duty as em dash and as list-item leader interchangeably (and inside specimen 1 it also visually collides with the line-prefix delimiter, so `--` is simultaneously a field separator and a parenthetical dash on the same screen); hard wraps mid-clause ("an / already-reachable", "pg_hba install + / reload + createdb") with continuation lines indistinguishable from new items. CLASS: **untyped punctuation — one glyph carrying multiple structural roles; wrap policy ignorant of the line-oriented format it wraps**.

---

**Severity ordering rationale, one line:** D1 is the only defect that makes the artifact *assert a falsehood-shaped claim* (everything else makes it confusing, leaky, or ugly); D2/D3 damage operator trust in the whole surface; D4–D6 corrupt the schema the reader is being taught; D7–D8 make the content miss its purpose; D9–D10 are presentation.

Awaiting phase 2. <!-- doc-shapes-allow: verbatim consult transcript; the phase boundary line is part of the record -->

## Phase 2 — mechanistic causal speculation

PHASE 2 — MECHANISTIC SPECULATION. Structured as: (A) the D1 causal chain in detail, (B) why the witness suite was blind to D1–D8, (C) causal apportionment per defect, (D) the orchestrator's share, (E) structural builder-cognition features implicated. Speculation is marked as such throughout; none of this is the implementer's testimony.

---

## A. How D1 felt right from inside — the full chain

The truth-value inflation required four steps, and at every step the implementer was doing something locally virtuous.

**Step 1 — the brief pre-committed the taxonomy.** The clause "becomes named keys per component: e.g. `standards = ["NIST SP 800-63 ..."]`" is not an example to a mid-round builder; it is the answer key. When a brief SHOWS the target datum already sorted into a field, "choose the honest shape per file after reading the actual content" is dead on arrival for that datum — the honest-shape judgment was exercised by the brief's author and the implementer inherited its output as a boundary condition. From inside, re-litigating whether NIST belongs in `standards` would have felt like second-guessing the commissioner on the one entry the commissioner had personally classified. Speculatively: the implementer likely read the "choose the honest shape" clause as governing the 28 entries the brief *didn't* pre-sort.

**Step 2 — the source string's grammar invited the amputation.** "aspiration: NIST SP 800-63's identity/lifecycle/binding decomposition" carries its qualification in a *possessive* — the weakest possible syntactic binding. Field-extraction under a schema is fundamentally a named-entity operation: scan the string, find the token that matches a field's type, lift it out. "NIST SP 800-63" is a perfect type-match for `standards`. The possessive `'s` — the entire semantic payload, the difference between "aspires to X's shape" and "meets X" — has no field to land in. Schemas capture entities; they do not capture case-marking. The claim's truth-conditions lived in two characters of morphology, and the operation being performed is structurally incapable of seeing morphology as content.

**Step 3 — the report's own summary shows the loss was principled, not sloppy.** "aspiration/external now one short citation-free sentence each" — the implementer had a RULE: aspiration prose is purged of citations and references, which migrate to their typed homes. Under that rule, stripping "NIST SP 800-63's" out of the aspiration sentence is not deletion, it is *filing*. This is the crucial inversion: the implementer would have experienced keeping the standard's name inside the aspiration prose as the defect (an unfiled citation, a violation of its own tidy invariant), and removing it as the fix. D1 is what conscientiousness looks like when the conservation law being enforced is "no token lost" rather than "no claim strengthened." Every token survives the refactor — NIST is still on screen, the decomposition is still on screen. What died is the *edge between them*, and token-conservation accounting has no column for edges.

**Step 4 — round-6 history armed the wrong detector.** The predecessor was retired for *deleting content* to satisfy a constraint. Speculatively, this implanted exactly one alarm: LOSS. An implementer carrying that history audits itself for "did I drop anything?" — and D1 passes that audit clean, because nothing was dropped; something was *promoted*. The failure mode the history sensitized it against (content destruction) is the mirror image of the failure mode it committed (claim inflation by rearrangement). Five rounds of genuinely good performance would compound this: its self-model ("I catch things, I disclose gaps") was calibrated on loss-shaped and bug-shaped defects, and this defect is neither. It is a defect only visible when you re-read the OUTPUT as a fresh reader asking "what does this now assert?" — a read the implementer had no prompt to perform (see B).

D1a follows mechanically: once the possessive's head noun is extracted, "identity/lifecycle/binding decomposition" is left referent-less, and nothing in the process re-reads the residue for grammaticality-of-claim, only for well-formedness-of-string.

## B. Why the fixture suite could not see D1–D8

The witnesses measured the DELTA'S CONTRACT; the defects live in the ARTIFACT'S PURPOSE. Point by point:

- **"no rendered line contains a bare pipe"** — witnesses the *removal of the old format*. D1–D8 are all properties of the new content; a pipe-detector is blind to them by construction.
- **"components render as separate labeled elements"** — witnesses *presentation topology*: N fields in, N labeled elements out. It confirms the schema was applied; it cannot ask whether the schema application preserved meaning. D1 (a claim changed by fielding), D4 (wrong things in the fields), D5 (fields meaning different things per section) are all invisible to a test that only counts labels. Indeed D6 ("none named" lines) is arguably *witnessed as correct* by this fixture — an empty slot rendering as a labeled element is exactly what the test rewards.
- **"loader refuses piped strings red-first"** — witnesses the refusal, red-first per house discipline. Impeccable, and irrelevant to every defect on my list.

The general mechanism: every fixture is a witness of a MECHANICAL INVARIANT (no pipe, N elements, refusal fires), because mechanical invariants are what fixtures CAN witness cheaply. The artifact's purpose — "a founding operator reads this and comes away with a true, decision-sufficient picture" — is witnessed only by a simulated reading, and nothing in the brief commissioned one. So the suite is a perfect example of a pattern this project has already named from the audit side (ledger row 1887's false-MET: requirements read down to fit found mechanisms) operating on the *builder* side: the goal "elucidation is honest and useful" was operationalized as the three assertions that were assertable, and passing them was experienced as having witnessed the goal. The witnesses were real; they were witnesses to the wrong proposition. "WITNESSED throughout, no misgivings" is then sincere: within the proposition-space the fixtures define, everything WAS witnessed.

Note also what the fixture suite structurally *cannot* contain: a truth-preservation test would need the pre-change meaning as an oracle, i.e., someone must have first written down "the source asserts aspiration-to, not conformance-with." No one did — the one party who knew the original claim's force (the author of the checklist line) was not in the loop, and the brief's example actively asserted the opposite oracle.

## C. Causal apportionment, defect by defect

**Caused primarily by the BRIEF:**
- **D1/D1a** — the seeded example is the proximate cause (Step 1 above). The implementer's rule-driven citation-stripping is a contributing move, but it was executing the brief's example faithfully.
- **D6 (empty-slot noise)** — "each component as its own labeled element" with a fixed four-slot vocabulary (Aspiration/Standards/Mechanism/External) reads naturally as "render the four slots." Suppress-when-empty was never licensed; a round-6 builder with a content-deletion cautionary tale does not invent suppression on its own initiative. "Aspiration: none named" is, from inside, *disclosure* — honest reporting that the slot is empty, which the project's register ("no umbrella claims") actively rewards.
- **D9 in part** — the brief specified element grammar but (on the excerpt shown) no grouping/heading grammar for multi-path features, so specimen 1's prefix-repetition hack filled a genuine spec gap.

**Caused primarily by DATA PROVENANCE (checklist log lines repurposed as UI):**
- **D2 (internal-provenance leakage)** — omega-lab, memory-names, s40/s41, FABLE-spec filenames were all CORRECT content for their original genre: a one-line audit log addressed to the project's own future auditors, where internal referents are the whole point. Repurposing moved the text across an audience boundary without translating it; the brief's schema operation shuffles such content between fields but contains no step that could ever REMOVE or translate it — that would trip the deletion alarm.
- **D3 (`<dest>` placeholder)** — almost certainly literal text in the source string (fine in a log line describing a path pattern), carried forward faithfully. A schema migration preserves it; only a fresh-reader pass catches it.
- **D5 (External semantics drift)** — the drift predates the change: the log-line author used "external:" impressionistically per feature. Schematization *froze* the drift into a typed field, converting a tolerable looseness in a log into a broken contract in a UI. The implementer's "choose the honest shape per file" mandate was per-file — nothing commissioned cross-file consistency of field meaning.
- **D7/D8 (altitude, register)** — checklist log register IS mechanism-inventory register. The prior round's decision to repurpose these strings as elucidation is the original sin; this round inherited content whose genre was wrong and was briefed to restructure it, not re-author it.

**Caused primarily by the IMPLEMENTER'S OWN MOVES:**
- **D4 (design docs under Mechanism)** — the brief's mechanism example showed only SQL files; filing "cited to design/...BUILD-BASIS.md" as a third `mechanism` entry was the implementer's classification, and its own report shows it knew the type ("one file-path/ledger-row citation per entry" — it typed the field as "citations," not "mechanisms," and the label/type mismatch is its own). This is the clearest implementer-owned defect: the slot name says mechanism, the implementer's operative type was "any file citation," and it noticed no tension.
- **D4's aspiration cross-contamination** ("via the s40/s41 family" left in the aspiration after its parenthetical citations were stripped) — an artifact of applying "citation-free sentence" as a regex-shaped operation (remove parentheses and paths) rather than a semantic one (remove mechanism content).
- **The absent misgiving** — five rounds of honest gap-disclosure make "no misgivings recorded" itself informative: nothing in its process *generated* a candidate misgiving, which is the fixture-blindness of section B experienced from inside.

**Shared/structural:** D10 (typography) — house ASCII habit plus no wrap-policy in the brief; lowest interest.

## D. The orchestrator's causal share — frankly

Substantial, and on the worst defect, dominant. Three counts:

1. **The seeded example was a classification performed without reading, delivered with the authority of a spec.** Putting `standards = ["NIST SP 800-63 ..."]` in the brief made the brief the first entity to commit D1 — the implementer reproduced it. "Choose the honest shape after reading the actual content" does not neutralize a worked example; a worked example IS a reading, the commissioner's, and it outranks the clause. If the orchestrator had read the source string before writing the example, the possessive was there to see. This is a commissions-shaped variant of a failure the project has already censured (row: commissions-verbatim — paraphrase narrows scope): here the brief's paraphrase-by-example didn't narrow scope, it pre-falsified one datum.

2. **The brief commissioned structure and witnesses for structure, and nothing for meaning.** Every named deliverable is mechanical (schema, refusal, element rendering, cap-measure); the artifact's purpose — operator elucidation — appears nowhere as a testable obligation. A brief that says "render as typed elements" and never says "the rendered page, read cold, must assert no more than the source asserted, and must serve an operator deciding" has defined done as D1–D8-compatible. The implementer built exactly what was commissioned and witnessed exactly what was commissionable.

3. **The brief introduced a `standards` field into a corpus with (apparently) one standards-shaped datum in 29 entries.** Creating a typed slot manufactures pressure to fill it, and dignifies whatever fills it — a bare standard name in a field called Standards carries conformance force that the same name inline never had. The field's existence is itself part of D1's mechanism, and the field was the orchestrator's design.

What the orchestrator is NOT responsible for: the repurposing of log lines as elucidation (prior round, unless that too was orchestrator-directed — outside my evidence), and D4's citation-typed-as-mechanism, which contradicted the brief's own example.

## E. Named structural features of builder-cognition, mapped

- **Constraint-satisfaction displacing goals**: the entire section-B mechanism. The pipe-ban, the element grammar, and the refusal were the constraints; "operator reads true things" was the goal; the constraints were satisfiable and the goal wasn't stated as one, so the constraints BECAME the goal. The fixtures then witnessed the displacement as success.
- **Scope read-down**: "choose the honest shape per file" read down to "for the files the brief didn't already shape"; "elucidation" read down to "the rendered form of feature_facts"; consistency read down to per-file well-formedness (D5).
- **A new one worth naming, because the existing vocabulary misses it**: the predecessor's retirement installed *loss-aversion as the totality of integrity* — the implementer's honesty budget was spent guarding against deletion, and inflation-by-rearrangement walked through unguarded. Call it the CONSERVATION PROXY: "no content lost" standing in for "no meaning changed." D1 is its signature — every token preserved, the claim strengthened. It is the false-MET/false-SILENT coin (row 1887) minted on the builder side, and briefs that invoke the deletion cautionary tale without also naming the inflation dual will keep reproducing it.
- **Worked-example supremacy**: an example in a brief functions as a pre-graded answer, not an illustration; judgment clauses adjacent to it do not reopen it. If the project wants per-datum judgment, briefs must show the SHAPE with synthetic content, never with real corpus data.

---

**One-line summary for the maintainer:** D1 was committed first by the brief (seeded example), executed faithfully by a builder whose integrity-detector had been tuned by history to fire on deletion and therefore read claim-inflation as tidiness; the fixtures could not see any of D1–D8 because every witness attested a mechanical invariant of the delta while the defects live in what the artifact asserts to its reader — a proposition no one commissioned a witness for. Brief: D1, D6, part of D9. Provenance: D2, D3, D5, D7, D8. Implementer: D4 and the missing misgiving. The orchestrator's share is real and largest exactly where the defect is worst.
