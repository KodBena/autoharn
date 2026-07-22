<!-- doc-attest-exempt: consult deliverable, verbatim phase-3 record (ledger rows 1119-1122); removal condition: superseded by ratification into law. -->

# CONSULT — Elucidation RCA, Phase 3: Inoculation mechanism set

*Consult-authored (Fable, independent consult instance), 2026-07-22. Phase 3 of the
two-phase-plus-resurrection commission on the setup-TUI elucidation defects (phases 1–2:
the D1–D10 diagnosis and the causal apportionment across brief / provenance / implementer /
builder-cognition). Commissioned by the maintainer "in the spirit of ADR-0000 and ADR-0011."
Not committed by the consult; the orchestrator installs. Every mechanism below names its
consumer per the named-consumer test (ADR-0000, 2026-07-22 anecdote): a mechanism whose
consumer the maintainer cannot recognize gets deleted, and that is the correct outcome.*

---

## 0. Scope discipline — what is deliberately NOT proposed here

Named exclusions, so silence is a decision and not a gap (ADR-0000 Revisit #4 Clause 1,
applied to this document about itself):

- **Already adopted, not re-proposed:** synthetic-content-only worked examples in briefs;
  the cold-reading witness obligation for operator-facing artifacts (ledger rows 1120–1121).
  Mechanisms M3 and M4 below build a mechanical floor *under* those adoptions; they do not
  restate them.
- **Already legislated, routed not re-minted:** phase-1 D9 (structural flattening,
  inconsistent rendering grammar) and D10 (typography) are ADR-0019 Rule 1 + companion
  C12/C13 territory; D6's *rendering* half (empty slots as content lines) is a C13-adjacent
  genre question. If those recur, the finding is an **enforcement gap in existing law**
  (ADR-0011 Rule 2 grounds against C12/C13's declared surfaces), not a law gap — no new rule
  is owed and none is written.
- **Out of reach and said so:** no mechanism below reads meaning. Where semantics is the
  question, the honest ceiling is review, and each such ceiling is named in place
  (ADR-0011 Rule 1).

Six mechanisms follow, ordered by the severity of the defect class each forecloses.

---

## M1 — Relation-typed external-authority references

*(Forecloses phase-1 D1/D1a: truth-value inflation of a standard citation via slot
promotion — the aspiration→Standards laundering.)*

**(a) Defect class and closure statement.**

The class, in its most general form: *a claim whose truth-conditions live in the RELATION
between two entities is stored in a schema that captures the entities and discards the
relation* — the possessive in "NIST SP 800-63's decomposition" carried the entire claim,
and entity-extraction is structurally blind to morphology. The type answer (ADR-0000 Rule
2(a)): an external-authority reference is not a string; it is a typed triple. A bare
standard name in a `standards` slot is made unrepresentable.

Closure statement:

1. **Invariant.** No rendered or stored datum references an external standard, framework,
   or certification regime except through a typed reference `{id, relation[, witness]}`
   drawn from the closed relation vocabulary `aspires-to | informed-by | named-only |
   conforms-to`, where `conforms-to` is unconstructable without a witness pointer. The
   renderer always renders the relation word; a relation-less standard name cannot reach
   the screen. (Composes with ADR-0000 Revisit #4 Clause 2's registry proviso — "named,
   not conformed" — by making that proviso a *type*, not a footnote.)
2. **Quantification universe.** Axes: prose fields AND list fields AND any future field
   kind of the typed data loaders (the net keys on the value, not the field). Sibling
   surfaces: `feature_facts` and its data-split siblings (`durable_decisions`,
   `principals_authority`), and any future elucidation/fact corpus the same loader family
   reads. The standard-identifier set is derived from `law/STANDARDS-REGISTRY.md`, so a
   registry addition extends the net with no second edit (ADR-0011 Rule 4:
   derive-from-one-source, never an enumerated ID list in the checker).
   **Named as NOT covered:** (i) free markdown under `design/` and `docs/` — the
   standards-scope-disclaimer clause (ADR-0000 Revisit #4 Clause 1) plus review govern
   there; (ii) conformance-flavored prose that names no registry entry ("complies with
   best practice") — no identifier, no mechanical hook; review-only, and the cold-reading
   witness is the named catcher.
3. **Denomination check.** No numeric bounds are minted; the check is vacuous and is named
   as such rather than faked.

**(b) Enforcement surface** (ADR-0011 Rule 1 vocabulary): **write-time data constraint**
(loader refusal, red-first) for the typed shape; **construction/import-time** at the
renderer for the relation word. Runnable sketch, loader side:

```python
RELATIONS = {"aspires-to", "informed-by", "named-only", "conforms-to"}

def check_standard_ref(ref: object, *, at: str) -> StandardRef:
    if isinstance(ref, str):
        refuse(f"{at}: bare standard name {ref!r} — a standard is cited as "
               f"{{id, relation}}; a bare name in a Standards slot asserts "
               f"conformance it cannot witness")
    missing = {"id", "relation"} - ref.keys()
    if missing:
        refuse(f"{at}: standard ref missing {sorted(missing)}")
    if ref["relation"] not in RELATIONS:
        refuse(f"{at}: relation {ref['relation']!r} not in {sorted(RELATIONS)}")
    if ref["relation"] == "conforms-to" and not ref.get("witness"):
        refuse(f"{at}: conforms-to without a witness pointer is unrepresentable")
    return StandardRef(**ref)

def check_prose_field(text: str, *, at: str, registry_ids: frozenset[str]) -> str:
    for sid in registry_ids:            # derived from law/STANDARDS-REGISTRY.md
        if sid in text:
            refuse(f"{at}: registry standard {sid!r} appears untyped in prose — "
                   f"move it to a typed standards ref with its honest relation")
    return text
```

Negative control per ADR-0011's 2026-07-02 amendment: the fixture feeds the gate exactly
the shipped defect — `standards = ["NIST SP 800-63"]` — and credits no green until that
red is banked.

**(c) Cost.** Per-citation authoring friction (choose a relation — which is the point: the
choice IS the honest claim). False positives: a registry ID appearing in prose *about* the
standard rather than *claiming* it (expected rare in fact corpora; the refusal teaches the
typed escape). **Consumer, named:** the founding operator reading the pane (protected
from a conformance lie), and the fact author at write time (the refusal that teaches).

---

## M2 — The migration meaning-ledger (the CONSERVATION PROXY net)

*(Forecloses the phase-2-named class: meaning changed while every token is conserved —
"no content lost" standing proxy for "no claim changed." Also nets D4's field
cross-contamination as a by-product.)*

**(a) Defect class and closure statement.**

The class: *a restructuring of existing prose into schema in which relocation severs a
semantic edge, and the only self-audit performed is loss-detection, which such a change
passes by construction.* Phase 2 showed the payload can live in two characters of
morphology (`'s`); therefore the net operates on the **character residue**, not word
tokens. No mechanism reads meaning — so the mechanism forces the *question* to be asked
per moved span, on the record, where review can check it.

Closure statement:

1. **Invariant.** Every commission that restructures existing prose into typed fields
   ships a **meaning ledger**: for each source record, every character span that (i) moved
   to a different field, (ii) was dropped, or (iii) was duplicated into a second field,
   carries exactly one disposition from the closed set `relocated-verbatim |
   relation-severed-and-retyped | dropped-with-reason | duplicated-with-reason`. A
   migration diff with undispositioned residue does not merge. `relation-severed-and-retyped`
   existing as a *required possible answer* is the inoculation: the question phase 2
   showed nobody asked becomes unaskippable.
2. **Quantification universe.** Axes: moved, dropped, duplicated spans (duplication is the
   D4 axis — "via the s40/s41 family" surviving in the aspiration AND as mechanism
   entries); punctuation/morphology included by the character-residue rule. Sibling
   surfaces: any prose→schema migration in the project, not only TOML — the trigger is
   the commission shape ("restructure existing content"), not the file type.
   **Named as NOT covered:** meaning changed by pure paraphrase with full token
   replacement (the ledger sees one big drop+add and the disposition degenerates to a
   free-text reason — review carries it); and migrations of content authored fresh in the
   same commission (no "before" exists). Both are the review tail, said plainly.
3. **Denomination check.** The gate's unit is character spans of the actual source — the
   resource in which the hazard detonates — never a "roughly reviewed" percentage or a
   sampled subset presented as the whole. No numeric threshold is minted (100% of residue
   is dispositioned; a sampling bound would be exactly the read-down this net exists to
   catch).

**(b) Enforcement surface: test/CI gate** on the migration commission's diff. Runnable
sketch of the residue computation:

```python
def residue(before: str, after_fields: dict[str, str]) -> list[Span]:
    """Character spans of `before` classified against the after-state."""
    out = []
    for span in unmatched_spans(before, after_fields):      # difflib per field
        homes = [f for f, v in after_fields.items() if span.text in v]
        kind = ("duplicated" if len(homes) > 1 else
                "moved" if homes and homes != [span.source_field] else
                "dropped")
        out.append(Span(span.text, span.source_field, homes, kind))
    return out

def gate(ledger: dict[str, str], spans: list[Span]) -> None:
    for s in spans:
        if s.key() not in ledger:
            fail(f"undispositioned {s.kind} span {s.text!r} "
                 f"({s.source_field} -> {s.homes}) — state its disposition")
```

Negative control: run the gate on the actual s40/s41 elucidation migration; it must go
red on the moved `NIST SP 800-63` span and the dropped `'s` before its green is credited
anywhere.

**(c) Cost.** Real per-migration friction, proportional to how much the migration
rearranges — which is proportional to the hazard, so the friction lands where the risk is.
Migrations are rare, high-attention events (the ADR-0011 self-application regime), so the
standing cost is near zero. False-positive surface: whitespace/punctuation normalization
noise — the residue matcher normalizes whitespace only, nothing else, and that choice is
stated in the gate. **Consumer, named:** the migration's reviewer, who today has no
artifact to check meaning-preservation against and therefore cannot check it; secondarily
the next RCA investigator, who gets dispositions instead of reconstruction.

---

## M3 — Audience-typed operator content: citation allowlist + placeholder refusal

*(Forecloses D2 internal-provenance leakage and D3 unexpanded placeholders. This is the
mechanical floor under the already-adopted cold-reading witness, not its replacement.)*

**(a) Defect class and closure statement.**

The class: *content stored for one audience rendered verbatim to another* — audience is a
type, and the corpus currently has no way to state or check it.

1. **Invariant.** A datum in an operator-facing corpus may cite paths only from the
   declared operator surface (the repo-root verbs and operator docs — an allowlist, so the
   net quantifies over "everything not operator-visible" rather than enumerating internal
   namespaces, per ADR-0011 Rule 4); and no rendered operator text contains an
   unsubstituted `<placeholder>`. An entry that must legitimately expose an internal
   referent carries an explicit `audience-exposed` marker with a one-line justification —
   which is itself named-consumer-testable at review.
2. **Quantification universe.** Axes: path-shaped citations; placeholder shapes
   (`<[a-z_]+>`); the internal-vocabulary tail (memory names, `sNN` numbering, ledger-row
   refs, workshop terms like "omega-lab"/"this world"). Sibling surfaces: all corpora of
   the same loader family (as M1). **Named as NOT covered:** the vocabulary tail beyond
   path/placeholder shapes is only pattern-nettable, and pattern nets under-quantify —
   an insider term with no syntactic signature passes the gate. That tail belongs to the
   cold-reading witness (rows 1120–1121), named here as the designated catcher; this
   mechanism is honest about being the floor, not the ceiling.
3. **Denomination check.** No bounds; vacuous, named as such.

**(b) Enforcement surface: write-time data constraint** (loader) for stored corpora plus
**construction-time** at the renderer for the placeholder check (catching substitution
failures that arise after load — the `<dest>` defect's actual site). Sketch:

```python
PLACEHOLDER = re.compile(r"<[a-z_]+>")
PATHLIKE    = re.compile(r"\b[\w./-]+/[\w./-]+\.(?:md|py|sql|toml)\b|\b\w+/\w+/")

def check_operator_text(text: str, *, at: str, operator_surface: tuple[str, ...],
                        audience_exposed: bool) -> str:
    if PLACEHOLDER.search(text):
        refuse(f"{at}: unexpanded placeholder {PLACEHOLDER.search(text).group()!r} "
               f"in operator-facing text")
    for m in PATHLIKE.finditer(text):
        if not m.group().startswith(operator_surface) and not audience_exposed:
            refuse(f"{at}: internal path {m.group()!r} cited to the operator — "
                   f"cite an operator surface, or mark audience-exposed with why")
    return text
```

Negative controls: the gate goes red on the shipped `<dest>/legacy/led` line and on
`design/FABLE-SETUP-TUI-SPEC.md` before green is credited.

**(c) Cost.** The main friction is legitimate teaching content that references internals —
the `audience-exposed` escape absorbs it at one justified line per entry. False positives
from the path regex on prose that merely resembles a path: expected low in this corpus;
each is a one-marker fix. Placeholder check: near-zero false positives (angle-bracket
literals in operator text are essentially always the defect). **Consumer, named:** the
founding operator (spared the workshop's interior); the fact author (taught by the
refusal); the cold-reading witness executor (whose scarce attention is reserved for the
tail only a reader can catch).

---

## M4 — Witness taxonomy: every WITNESSED claim states WHAT proposition it witnesses

*(Makes the fixture-blindness class — witnesses attest the delta's contract while the
artifact's purpose goes unwitnessed — detectable at review time.)*

**(a) Defect class and closure statement.**

The class: *a witness suite whose every member attests a mechanical invariant of the
change, presented (and sincerely experienced) as having witnessed the deliverable* — the
false-MET coin (ledger row 1887) minted on the builder side. No mechanism can judge
whether a witness reaches the purpose; a mechanism CAN make it loud that *none even
claims to*.

1. **Invariant.** Every WITNESSED item in a report (and every fixture in a commissioned
   suite) is tagged with the proposition class it attests: `delta-contract` (a mechanical
   invariant of the change: format bans, element counts, refusals firing) or
   `artifact-purpose` (an assertion stated in the deliverable's consumer's terms: what a
   cold reader of the output would take it to claim or be able to do). A commission whose
   deliverable is reader/operator-facing closes with **at least one** `artifact-purpose`
   witness, or an explicit UNEXERCISED with the concrete blocker — the same trichotomy
   CLAUDE.md already mandates, gaining one axis.
2. **Quantification universe.** Sibling surfaces: implementer reports; fixture suites;
   the conformance instrument's claim schema (where that instrument runs, the tag is a
   required field, not prose — ADR-0000 amendment's own move). **Named as NOT covered:**
   the *truthfulness* of a tag and the *adequacy* of a purpose-witness are review-only —
   a mechanical fixture relabeled `artifact-purpose` passes the count. The mechanism
   makes ABSENCE loud, never inadequacy; the reviewer's check is "read the purpose
   witnesses only, against the deliverable's stated consumer" — a minutes-scale read the
   tag makes possible at all.
3. **Denomination check.** The one bound ("at least one") is denominated in witnesses of
   the consumer's proposition — not in fixture count, which is the proxy unit this
   mechanism exists to stop crediting. Stated so the bound cannot be satisfied in the
   wrong currency by relabeling, except dishonestly, which is review's to catch.

**(b) Enforcement surface:** **test/CI gate** where the conformance instrument's claim
schema carries reports (required `attests:` field; instrument fails a reader-facing
commission with zero `artifact-purpose` entries); **review-only** for untyped reports and
for tag truthfulness — named as the ceiling it is. This is the ceiling the commission
asked me to be honest about: *review is structurally the final surface for
purpose-adequacy, because purpose lives in a reader and no gate reads.* What the
mechanism changes is that review-time blindness now requires ignoring an empty column,
not reconstructing an absence.

**(c) Cost.** One enum per claim — trivial authoring cost. The real cost is honest:
commissions will start reporting UNEXERCISED purpose witnesses with blockers, which is
friction shaped exactly like information. **Consumer, named:** the orchestrator reading
the report to decide acceptance — today that reader cannot distinguish "the deliverable
was witnessed" from "the delta was witnessed," and phase 2 showed the difference was the
whole event.

---

## M5 — The delegation-conflict stop (WORKED-EXAMPLE SUPREMACY, residual)

*(The synthetic-examples rule is adopted; this covers the residue: a brief's
authority-gradient can pre-resolve a delegated judgment through channels other than a
worked example — an enumeration, an aside, an attached prior artifact.)*

**(a) Defect class and closure statement.**

The class: *a brief that simultaneously delegates a judgment and carries a resolution of
an instance of that judgment; the resolution outranks the delegation in the implementer's
process, silently.* Phase 2's finding: an example is a pre-graded answer; the general
form is that ANY resolved instance is.

1. **Invariant.** A brief that delegates judgment carries a **JUDGMENTS DELEGATED**
   block naming each judgment the implementer owns. Standing rule, with ADR-0014's
   posture (and ADR-0019's "cannot match → stop" as the sibling precedent): an
   implementer that finds, anywhere in the brief or its attachments, a resolved instance
   of a listed judgment treats the conflict as a **typed stop** — surface it and ask,
   never silently obey either side. The stop is licensed and costs the implementer
   nothing; silence is the violation.
2. **Quantification universe.** Channels: worked examples (already closed by the adopted
   rule — synthetic content cannot resolve a real instance), enumerations, prose asides,
   attached prior-round artifacts, and fixture expectations shipped with the brief (a
   fixture asserting the answer is the strongest pre-resolution channel of all — named
   here because nobody has named it). **Named as NOT covered:** detection is semantic; no
   lint reads "this clause resolves that judgment." The reviewer's mechanical assist is
   only that the delegated-judgments list *exists* to diff the brief against.
3. **Denomination check.** No bounds; vacuous, named.

**(b) Enforcement surface:** **spec-time** (the block is a required brief section, same
standing as ADR-0019's genre/reference clause — a brief without it is incomplete and may
not dispatch) + **review-only** for the conflict-detection and the stop reflex, declared
plainly. Per ADR-0011 Rule 2's own register, this carries its mechanization trigger: if
a pre-resolved delegated judgment recurs *past* both the block and review, that
recurrence is grounds to mint the strongest then-feasible check (plausibly: the brief's
own conformance-instrument run gains a "delegations vs. resolutions" question).

**(c) Cost.** One section per brief; occasional stop-and-ask round-trips, some of which
will be false alarms — that is the decision-queue bar's price, and a false-alarm stop is
minutes where the phase-2 event was a ratified defect in law-adjacent content. **Consumer,
named:** the implementer (a licensed stop instead of a silent obedience choice) and the
orchestrator (whose own brief gets checked against its own delegation list — the
commissioner implicated by construction, as phase 2 found warranted).

---

## M6 — Field charters: a schema field declares its meaning once

*(Forecloses D5: the same field label meaning three things across sections — semantics
drift frozen into a typed field.)*

**(a) Defect class and closure statement.**

The class: *a typed field whose contract exists only in each author's head, so the type
system certifies the shape of values whose meaning diverges per site* — a lying signature
at schema scale, the same disease the lazy-imports edict names at module scale.

1. **Invariant.** Every field a typed data loader accepts carries a one-sentence
   **charter** in the schema definition (what the field asserts, to whom); the loader
   refuses a charterless field at import of the schema itself. The charter is the oracle
   the cold-reading witness and every future author/migrator reads a field's content
   against.
2. **Quantification universe.** All fields of all corpora in the loader family (as
   M1/M3). **Named as NOT covered:** cross-section *consistency with* the charter is
   semantic — review-only, discharged in practice by the cold-reading witness now having
   a stated contract to check against instead of inferring one per section (which is how
   D5 survived: every section was self-consistent with an unstated contract of its own).
3. **Denomination check.** No bounds; vacuous, named.

**(b) Enforcement surface: construction/import-time** for charter presence (a
`Field(charter=...)` required argument — omission is unconstructable, no lint needed);
**review-only** for adherence, named. Sketch is one line: the schema dataclass's `charter:
str` field with no default.

**(c) Cost.** One sentence per field, paid once at schema authoring. Near-zero standing
friction; the plausible failure is charters written as filler — caught, if at all, by the
same witness that consumes them, and an unused-filler charter is precisely what the
never-enforced-entries-get-culled condition should delete. **Consumer, named:** the
cold-reading witness executor (gains an oracle) and the next migration's implementer
(gains the contract phase 2's implementer had to invent per field).

---

## Roll-up

| # | Defect class foreclosed | Strongest honest surface | Ceiling named |
|---|---|---|---|
| M1 | Authority-relation severed by fielding (D1) | write-time typed refusal + renderer | prose without registry IDs → review |
| M2 | Meaning changed, tokens conserved (conservation proxy) | CI gate on migration residue | paraphrase; fresh content → review |
| M3 | Audience-boundary leakage; placeholder leak (D2/D3) | write-time + construction-time gates | vocabulary tail → cold-reading witness |
| M4 | Witnesses attest delta, not purpose (fixture blindness) | instrument-required claim field | tag truth & adequacy → review, permanently |
| M5 | Brief pre-resolves a delegated judgment (example-supremacy residual) | spec-time required block | detection & stop reflex → review, with mint trigger |
| M6 | Field label without a field contract (D5) | import-time required charter | adherence → review via witness |

Three of six reach a mechanized surface with a runnable core and a negative control
against the literal shipped defect (M1, M2, M3); one is mechanized where the instrument
runs and review elsewhere (M4); two are honestly spec-time/review with their
mechanization triggers pre-named (M5, M6's adherence half). Per ADR-0011's 2026-07-02
amendment, at this project's bar the M1–M3 gates ship WITH the corrective fix to the
current corpus, not after a second occurrence — the first fix's definition of done
includes its net.

If the maintainer culls, cull from the bottom of each mechanism's cost column, not from
the table: M4's enum and M6's charter are the cheapest and are load-bearing for the
review ceilings everything else honestly declares.
