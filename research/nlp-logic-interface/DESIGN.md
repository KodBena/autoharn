# DESIGN — the NLP↔logic interface, purpose-first (2026-07-02)

**Status:** commissioned synthesis (Fable-tier, one commissioning), delivered against
`SYNTHESIS-INPUTS.md`. Companion documents: `INTERFACE.md` (the typed contracts),
`KB-CODESIGN.md` (the durable store), `BUILD-PLAN.md` (the phased increments and the
experiments ledger). This document is the executive map: the purpose, the functions the
purpose demands, and the formalism assigned to each function with its justification,
encoding path, and qualification gates.

**Frame (binding, maintainer-ruled 2026-07-02).** Two rulings govern everything below:

1. **Purpose-first, functions-not-obligations.** The purpose: *keep LLM collaborators
   doing the right thing proactively — interrogate their epistemic state and in-progress
   work against a knowledge base; proactively supply the information they need.*
   Formalisms are assigned to the **functions** this purpose demands. Whether a given
   function's output constitutes an obligation-violation is a **finding** — a classification
   the system emits — never the ontology it is organized by. Deontic-as-primary is
   rejected; nothing below assigns a formalism *to an obligation*.
2. **Inventory-first.** This design extends a real, measured seam — the typed spine
   `FactBundle` → `Claim` → `Finding`/`LogicFinding`, the `LogicBackend` Protocol
   (`analyze(claims) -> list[LogicFinding]`), two live engines (clingo/ASP via
   `contra_asp.AspBackend`, all three rules + defeasible R-FUNC + minimal repair; Z3 via
   `fde_z3.FdeZ3Backend`, the R-NEG paraconsistent glut), the mechanical cross-engine
   differential, coupling by `contra.finding` rows, and **no confidence scores anywhere by
   design** (honesty = rule-id + grounding, type-enforced at the adjudicate boundary).
   Every extension below is named against those artifacts, not a blank page.

**Coined terms, legible on first use** (project senses; the root `GLOSSARY.md` holds the
standing vocabulary):
- **claim** — one extracted assertion with provenance (`contra_detect.Claim`, frozen).
- **finding** — a candidate deduction over a claim pair, carrying rule-id + grounding,
  never a verdict (`contra_detect.Finding` / `logic_backend.LogicFinding`).
- **supersedes-chain** — an append-only link from a later claim/finding to the earlier one
  it corrects; the current belief on a scope is the one nothing supersedes (the house
  idiom from `tlab_finding`, ADR-0011's 2026-06-24 amendment).
- **glut** — a proposition told-true *and* told-false, contained as the value `both` in
  Belnap–Dunn **FDE** (first-degree entailment, the four-valued paraconsistent logic the
  Z3 lane implements) rather than exploding.
- **differential gate** — mechanical set-equality between two independent producers'
  findings on the same claim substrate; empty-empty = pass. An encoding-trust check,
  never a model's judgment (the fair-trials lesson).
- **WHY-ledger** — the durable record that a design decision carries its recorded WHY,
  with every subsequent means-change carrying an explicit disposition of that WHY.
- **mood** — the speech-act type of a claim's source sentence (assertion, interrogative,
  quoted mention, action-report, closure-claim), carried as a closed vocabulary, not a score.

---

## 1. What the measurements established (the inputs this design is bound by)

The 2026-07-02 trial series (three trials + GLiNER enrichment; evidence in
`experiments/fact-mining/docs/hook-trial/`) is the requirements writer. Its end state:

- Enrichment cut the joint noise floor **483 → 54** findings across both corpora
  (12×/7×), produced **0 novel findings** (enriched arms strict subsets — enrichment
  cannot create recall), and **0 of the 54 survivors are adjudicable candidates**.
- The 54-survivor residue decomposes: **35 subject-collapse** (28 strict same-sentence
  shreds), **8 mood/mention**, **3 temporal state-change**, **2 parse-polarity mis-scope**,
  **5 number-grab (gate-open side)**, **1 quantity-regime** — per the hand-read
  dispositions in `findings_gliner.json` / `findings_gliner_mainsession.json`.
  (The commissioning dossier's four-bucket summary — 35/8/3/1, summing to 47 — silently
  drops the 5 number-grab and 2 parse-polarity survivors; the six-bucket decomposition
  above, summing to 54, is the trial report's and is authoritative.)
- The one known-live positive (the 874 MB vs 2.9 GB memory-complaint pair, session
  `55eec152`) is at **zero recall in every arm**: the two statements' subjects never
  share any key, typed or bare.
- Conclusion of record (HOOK-DESIGN §4b): surface rules see neither the precision nor
  the recall side of the genre; **the logic layer is a prerequisite of useful L1**, and
  the specific missing capacities are exactly the functions in §2.

The residue is the design's target, not its excuse: each function below names which part
of the measured residue (or the measured recall miss) it exists to move.

## 2. The functions

Derivation: F1–F7 are the measured requirements of dossier §3 (non-negotiable inputs);
F8 is the already-built substrate function they refine; F9 is the purpose's third clause
(proactive supply, HOOK-DESIGN §1.3). The maintainer's concerns draft is assessed in §4
— its viable content lands inside these functions rather than beside them.

| # | Function | Measured warrant | Residue attacked |
|---|---|---|---|
| F1 | Temporal state-change / belief revision — model supersession, don't flag it | main-session R-NEG surplus (4.5× subagent density) dominated by "was X, now fixed" narratives | 3 temporal survivors + the R-NEG main-session mass |
| F2 | Assertion mood / use-vs-mention typing — hold apart action-report, defeasible inference, verified closure; exclude interrogatives and quotations from the assertion universe | the sharpest rule yields zero clean candidates because of exactly these; the "Cleaned [moving on]" specimen (BACKLOG) | 8 mood/mention survivors |
| F3 | Quantity commensurability — join and compare quantities by unit dimension and measurement regime, not by digit disequality | 98% of delta residue was digit-run grabbing; the 1 quantity-regime survivor; the known positive is a cross-unit (MB vs GB) pair no subject key joins | the R-NUM lane end to end; the recall miss |
| F4 | Predicate-standard indexing — gradable predicates carry a hidden standard; tolerate the glut at ingest, resolve when the index is recoverable, keep the unresolved form as calibration data | the maintainer's "not entirely / pretty much entirely out of my league" — true under two standards, a glut under none | the subject-collapse structure one level up (predicate axis) |
| F5 | Role-stratified universes — assistant-self / user-instruction / cross-role, with harness-injected and quoted content separated at ingress | 63% of baseline findings touched user-role prose; the L1 amendment (stratify, never exclude) is already ruled | ingress pollution across all rules |
| F6 | Goal-substitution detection (the WHY-ledger) — a decision carries its recorded WHY; a means-change without re-verification or explicit retirement is a flag | the impedance F-algebra→tagless-final arc: the fusion objective retired by conversational drift, no experiment | (KB-side; no trial residue — a recall class the trials could not see) |
| F7 | Ordering as dependency — precedence relations over reified work units, violation = work touched before its dependency discharged | concern 1; "ADRs before relevant work" as dependency, not sequence | (KB-side, as F6) |
| F8 | Consistency interrogation core — the existing R-NEG/R-FUNC/R-NUM lane | built, differential-gated, live | the substrate F1–F5 refine |
| F9 | Proactive supply — surface KB facts the collaborator's current claims touch, salience-gated | HOOK-DESIGN function 3; the impedance specimen's "tagless final bought no fusion" as a supplied fact | (deliberately last; needs F1–F5's ingest + the KB) |

**Where the deontic lives.** Under this frame a finding may carry an *obligation marker*
— e.g. an F6 `why_orphaned` finding against a standing mandate, or an F7 precedence
violation — as an output classification with its grounding. That is concern 4 discharged
as a finding-attribute, not as an organizing axis. No deontic logic is assigned an
engine here, because no measured function's failure mode is deontic-semantic: the
failure modes are non-monotonic retraction (F1, F6), vocabulary typing (F2, F5),
arithmetic under dimensions (F3), and parameterized truth (F4).

## 3. Formalism assignments — by failure mode, with encoding path and gates

The assignment rule (survives the primacy correction): **the formalism is chosen by the
failure mode of the thing being guaranteed** — assign, don't compete. Every assignment
names its encoding path into an engine that is live on this host (clingo 5.8 CLI, z3
4.16 in the generic venv, SWI-Prolog present; the Python `clingo` binding is *not* in
the venv — ASP is subprocess-only, a per-call process-spawn cost the time-budget design
must carry). Every assignment names its qualification gates — mechanical, never LLM
judgment. The house gate triple, used throughout, is the one already shipped in
`test_contra_asp.py` / `test_logic_backend.py`: **GOLDEN** (planted fixtures produce
exactly the expected findings, decoys stay silent), **MUTATION** (every load-bearing
encoding token flipped must change the verdict), **DIFFERENTIAL** (independent
implementations agree set-wise on the same substrate), plus ADR-0011's 2026-07-02 legs:
**negative control** (the gate seen red before its green is credited) and **shipped
binding** (the gate exercises the default path).

### F1 — Temporal state-change / belief revision → ASP (clingo), rule-id `R-SUP`

- **Failure mode:** a later claim *retracts* an earlier one ("was X, now fixed").
  Classical and SMT semantics are monotone — adding the later claim can only add
  conclusions; here it must *remove* one (the contradiction that isn't). Non-monotonic
  retraction under default negation is precisely stable-model semantics' lane, and the
  defeasible machinery is already live in `logic_layer.lp` (R-FUNC's
  `not exception(S,P)`).
- **Encoding path:** extend the EDB (`contra_asp.edb_from_claims`) with
  `at(Id, T)` — T = the claim's turn index from `ClaimContext` (INTERFACE §3), a total
  order per session, no wall-clock semantics claimed — and `supersedes(B, A)` facts
  (authored via adjudication, or derived by a rule: same atom key, opposite polarity,
  `T_b > T_a`, B carries a state-change marker). One default: a pair is an `R-NEG`
  finding *unless* superseded, in which case it is an `R-SUP` supersession record —
  routed to the KB's supersedes-chain (KB-CODESIGN §3), not injected as a contradiction.
  AGM-style belief revision (the Alchourrón–Gärdenfors–Makinson postulates) is the
  *reference theory*; the shipped mechanism is the two clauses above, and no AGM
  completeness is claimed.
- **Gates:** GOLDEN = the six genuinely temporal fixtures — the 3 temporal survivors
  plus the 3 `daemon/advertise` temporal duplicates the typed-keying arm removed
  (the other three of that arm's six R-NEG removals are interrogative/contrastive
  shapes and belong to F2's fixture set, not here — asking R-SUP to fire on them
  would credit a false positive) — R-SUP fires, R-NEG falls silent, decoy
  contradictions without ordering stay R-NEG. MUTATION on the new clauses. DIFFERENTIAL vs a Python oracle re-implementation of the same default (the
  oracle stays the hub, as today). Negative control: strip `at/2` facts, the fixture
  must regress to R-NEG.
- **The doxastic signal (concern 7, reduced).** Confidence escalating across a reversal
  ("must be this" → "nope, but *this* time I'm absolutely sure") becomes computable
  once claims carry a typed hedge (F2) and an order (F1): an `R-SUP` chain whose
  superseding claims carry non-decreasing `EMPHATIC` hedges is itself a reportable
  finding (`R-SUP-ESC`), grounded in the sequence. No reasoner taxonomy, no scores —
  a pattern over typed surface forms.

### F2 — Mood / use-vs-mention → a typed closed vocabulary + engine guards (no new engine)

- **Failure mode:** category error at the *vocabulary* level (ADR-0008): an
  interrogative, a quoted bug title, or a mention of a contradiction is not an
  assertion, and an action-report ("Cleaned") is not a verified closure. No deduction
  engine fixes a mis-typed premise; the fix is that the type system refuses the
  premise. The formalism here is the closed vocabulary itself — `Mood` and `Hedge`
  enums on the claim (INTERFACE §2) — plus one guard in every rule: only
  `Mood.ASSERTION` (and `ACTION_REPORT`, for its own lane) claims enter contradiction
  universes.
- **The closure-laundering discrimination** (the "Cleaned [moving on]" specimen): the
  three deduction types are held apart *by type* — (a) action-report
  (`Mood.ACTION_REPORT`: eventive, verifiable per se), (b) defeasible closure inference
  (an engine-derived default, retractable), (c) verified closure (a claim whose
  `ClosureWitness` field is present — invariant + universe + witness, ADR-0000's
  closure-statement shape as a typed record). An (a) claim can *ground* a (b)
  inference; nothing can promote (b) to (c) except a witness. This is a typed-contract
  rule, mechanically checkable, not an engine theorem.
- **Encoding path:** `ClaimContext.mood`/`hedge` populated at ingress. v0 classifier is
  parse-feature-mechanical (sentence-final `?` / aux-inversion → INTERROGATIVE;
  quotation-span coverage → MENTION; matrix-verb morphology + first-person eventive →
  ACTION_REPORT) — deliberately shallow, measurable, and wrong in knowable ways.
- **Gates:** GOLDEN = the 8 mood/mention survivors hand-labeled as fixtures (the three
  interrogative→resolution pairs, the quoted planted fixture, the use-vs-mention
  cases); the guard must silence them and must NOT silence the planted true fixtures.
  Negative control: guard off reproduces the control arm bit-identically (the
  default-unchanged idiom already pinned in `test_contra_detect.py`).
- **Honest uncertainty:** whether parse features reach useful mood precision on this
  genre is *not knowable from the armchair*. Deciding experiment (BUILD-PLAN E-1):
  hand-label ~200 prose units from the two corpora, measure the v0 classifier;
  kill condition — if INTERROGATIVE+MENTION precision < 0.9 on the labeled set, the
  v0 guard ships detection-only (stored, not gating) until a better classifier is
  measured. Mood typing is named NOT-yet-available in the capability envelope
  (dossier §4); this function is the reason to build it, and the guard design
  degrades to today's behavior when the field is `None`.

### F3 — Quantity commensurability → Z3 (linear real arithmetic over dimensioned quantities), rule-id `R-QTY`

- **Failure mode:** arithmetic incompatibility under units, scales, tolerance, and
  regime — `874 MB` vs `2.9 GB` is a factor-3.4 disagreement *only after* unit
  coercion; `36 %` vs `28 %` disagrees only within one measurement regime. Digit
  disequality (R-NUM today, honestly labeled disequality-only in `logic_layer.lp:65–68`)
  cannot express any of this. Arithmetic over reals with named constants is SMT's
  home turf; z3 is live and already the second engine.
- **Encoding path:** `parse_quantity` (INTERFACE §4) types the surface number into
  `Quantity(value, unit, dimension)` — a small, closed dimension table (bytes, seconds,
  percent, count, dimensionless), derived from **the unit token adjacent to the number
  in the sentence** (the surface forms are verified present in the known positive's
  transcript: "874 MB" / "874M" / "2.9 GB"), never guessed (`None` on no recognized
  unit, the `parse_number` posture). The GLiNER quantity-mention is a *corroborating*
  signal and the source of the mention head — deliberately not a gate on the parse,
  so a GLiNER quantity-miss cannot zero the recall lane (the recall exposure the
  GLiNER trial's audit named). `R-QTY` joins claim pairs on **(dimension, regime-key)**
  — not on subject key, which is what the known positive proves insufficient — and
  asserts incompatibility as a Z3 query:
  coerce to base units, `|a − b| > τ·max(a,b)` with τ a named, per-dimension constant
  (denominated in the quantity's own currency, ADR-0012's proxy-bound amendment; never
  a bare round literal). A Python oracle implements the same predicate for the
  differential. The regime-key (what measurement is this a reading *of*) starts as the
  typed subject where present, else the sentence's quantity-mention head; its
  recoverability rate is a measured unknown (experiment E-2).
- **Why not CLP(FD):** finite-domain constraint logic is integer-domain; these are
  reals with units and tolerances. FD would be a fuzzy vocabulary match (ADR-0008).
  CLP(FD)'s honest candidate lane is F7 (below), and only if numeric scheduling enters.
- **Gates:** GOLDEN = a *synthetic* planted cross-unit fixture (a deterministic
  MB-vs-GB contradiction the parser and join must always catch — the mechanism
  test); the quantity-regime survivor (`36 %` vs `28 %`) as the regime-separation
  fixture (joins only when regime keys collide); the id/constant number-grab
  survivors as decoys (never join — no dimension). The *live* known positive is
  deliberately not a golden: whether it joins is E-2's measured question (see the
  caveat below), and a golden that encodes an unmeasured hope is a gate that lies.
  MUTATION on the dimension table and τ. DIFFERENTIAL oracle-vs-Z3. Negative
  control: dimension lane off reproduces R-NUM's control arm exactly.
- **Caveat, stated plainly (the recall/precision tension is real and is not resolved
  here):** the known positive's two subjects share no key, so any regime-key derived
  from the subject re-inherits R-NUM's exact failure and misses the pair; a
  dimension-only join reaches the pair but with an unmeasured noise geometry. The
  same `regime_key` knob trades W1 (the pair joins) against W3 (noise stays low).
  This document therefore does **not** assert the pair will be recalled; it asserts
  the join *mechanism* and commissions the measurement — experiment E-2 runs both
  join configurations (subject-derived regime key vs dimension-only) with the known
  positive as the recall probe and the kill condition as the noise probe, and the
  configuration is decided by that data (BUILD-PLAN §Increment 1). The engine fit is
  certain; the join key is the experiment's output, not this document's claim.

### F4 — Predicate-standard indexing → the FDE/Z3 lane, extended atom key

- **Failure mode:** parameterized truth — a gradable predicate is true relative to a
  standard, and two claims under different standards are no contradiction at all.
  Flagging them classically is a false positive; discarding them loses the calibration
  signal. The dossier's architecture is adopted as ruled: **tolerate paraconsistently
  at ingest** (the FDE lane exists precisely to contain a glut without explosion),
  **resolve contextually** when the standard index is recoverable, **export the
  unresolved form as calibration data**, not noise.
- **Encoding path:** the FDE atom key `(subj_key, pred, obj_key)` gains an optional
  standard index: `(subj_key, pred@std, obj_key)`. Recoverable index (an explicit
  standard in the sentence — "for a dilettante", "by production standards"; a degree
  adverb regime) re-keys the atoms and the glut dissolves — mechanically, in
  `FdeZ3Backend`'s grouping, before any solve. An unresolved glut stays `value="both"`
  and is routed to `kb.calibration` (KB-CODESIGN §4) instead of the injection path.
  No new engine; one keying function + one routing rule. Said honestly: this
  assignment is *routing to an existing lane by ruling* more than a fresh
  failure-mode derivation — the new work is the keying function (which runs before
  any solve; the engine does nothing new for the resolved case), and the FDE lane's
  contribution is containment of what the keying cannot yet resolve. That is the
  dossier's ruled architecture, adopted as such.
- **Gates:** GOLDEN = the maintainer's own specimen as fixture ("not entirely out of
  my league" / "pretty much entirely out of my league" — glut when unindexed,
  dissolved when indexed with two standards). MUTATION on the keying function.
  Negative control: index extraction off must reproduce today's FDE outputs exactly.
- **Honest scope:** standard-index *recovery* is an NLP capability that mostly does
  not exist yet; v1 recovers only the explicit-marker cases and keeps everything else
  contained-and-exported. That is the design working as intended, not a gap: the
  calibration store is where the eventual classifier's training data accumulates.

### F5 — Role stratification → typed universe partition (no engine)

- **Failure mode:** ingress category error — user prose, harness-injected content, and
  quoted material entering one universe manufactures cross-role "self"-contradictions
  (63% of the baseline). The fix is a type: `Role` on `ClaimContext` (from the PROSE
  Port's `Provenance.role`, which already exists), plus a `ClaimUniverse` constructor
  that *refuses* mixed-role claim sets unless the universe is explicitly the cross-role
  one (INTERFACE §3). The three ruled universes — assistant-self, user-instruction,
  cross-role conduct-vs-mandate — are then three typed filters over one claim store,
  and the cross-role universe is gated on F2's mood work (as the L1 amendment already
  rules: it "needs the mood work before it is honest").
- **Gates:** construction-time refusal tests (illegal mixes unrepresentable, the
  adjudicate `schema.py` idiom); GOLDEN = the trial's catalogued cross-role false
  positives must vanish from the assistant-self universe and reappear, correctly
  labeled, in the cross-role one.

### F6 — Goal-substitution / the WHY-ledger → ASP defeasible over the KB ledger, rule-id `R-WHY`

- **Failure mode:** *absence as signal* — a mandate's recorded WHY was neither
  re-verified nor explicitly retired when the means changed; the flag must fire on
  silence. Closed-world absence with named defeaters is default negation's exact
  shape: `why_orphaned(M) :- mandate(M, W), means_change(M, E), not reverified(W, E),
  not retired(W)` — and `retired(W)` is itself constrained to carry an experiment
  witness (the frontier creed, "retire only via a failed experiment", as an EDB
  integrity constraint, not prose). The ledger rows are the KB's
  `kb.mandate` / `kb.why_event` (KB-CODESIGN §3).
- **Why ASP over SQL:** the detection *floor* is expressible as `NOT EXISTS` — and per
  the house idiom that floor is kept, as the differential baseline (a
  `kb.why_orphaned` view). ASP earns its keep exactly where R-FUNC did: the defeater
  set is open-ended and compositional (ratification-under-fatigue does not discharge;
  a retirement without a witness does not retire), and each new defeater is one EDB
  fact or one clause, not a rewritten view. This mirrors the shipped
  defeasible-retraction demonstration (`test_contra_asp.py:131`).
- **Gates:** GOLDEN = the impedance arc replayed as fixture rows (mandate: F-algebra
  for fusion; means-change: tagless-final substitution; no reverify, no witnessed
  retire ⇒ `why_orphaned` fires; add the retirement-with-witness row ⇒ retracts).
  DIFFERENTIAL vs the SQL view on the defeater-free floor. MUTATION on the clauses.
- **Scope honesty:** v1's mandate/means-change rows are *authored* (by the maintainer
  or an adjudication step), not NLP-extracted from transcripts — extraction of "this
  is a mandate with WHY = X" from prose is beyond the measured envelope. The function
  is real with authored rows (the impedance specimen shows the rows are few and
  load-bearing); the extraction path is a later experiment (E-4), not a claim.

### F7 — Ordering as dependency → ASP precedence over reified work units, rule-id `R-ORD`

- **Failure mode:** partial-order violation — work touched before its dependency
  discharged ("no variant surface before the port contract"; "ADRs read before
  relevant work" — which the maintainer glosses as prudence under imperfect memory,
  i.e. genuinely a dependency, not a ritual sequence). Transitive precedence over an
  event log with violation-on-absence is again Datalog/ASP shape:
  `violated(U) :- prereq(U, V), touched(U, T), not discharged_before(V, T)`.
- **Substrate:** the reified work-unit/discharge rows of KB-CODESIGN §5 — the
  maintainer's half-remembered idea, confirmed absent from the four research corpora
  (RESEARCH-SUMMARIES, final section) and therefore presented there as **his to ratify
  as new**, not re-found.
- **CLP(FD), placed honestly:** the maintainer's standing style ruling (a well-written
  CLP(FD) can beat SQL for elegance; intellectual stimulation is a primary motive) is
  honored with a real criterion rather than a token gesture: CLP(FD)/clingcon enters
  when the ordering function acquires *numeric* domains — durations, budgets, resource
  capacities — where propagation over integer intervals is the native semantics.
  Precedence-violation detection alone has no numeric domain, so assigning FD to it
  today would be engine-led design, the exact inversion this commissioning was killed
  for once already. Experiment E-5 (BUILD-PLAN) is the trigger: first real scheduling
  need gets encoded in both clingo and SWI CLP(FD), compared on encoding legibility
  and latency, and the winner recorded — a decision by experiment, per the creed.
- **Gates:** GOLDEN fixtures from the two concern-1 examples; MUTATION; the SQL
  transitive-closure view (`WITH RECURSIVE`) as differential floor.

### F8 — the consistency core → unchanged

The oracle + `AspBackend` + `FdeZ3Backend` triple stands as-is. F1–F5 compose with it
as guards (mood, role), keys (typed subject, standard index), an ordering relation
(turn index), and one new join lane (R-QTY). The `LogicBackend` Protocol is untouched;
new rules are new members of `rules: frozenset[str]`, and `cross_engine_differential`
runs on shared-rule intersections exactly as today. That the extension surface is
*this narrow* is the inventory-first ruling paying out.

### F9 — Proactive supply → retrieval + salience over the KB (engine assignment deferred, honestly)

Supply is a *relevance* problem before it is a deduction problem: given the session's
current claims, which KB facts are load-bearing here? v1 is typed-key retrieval
(entities, predicates, dimensions, mandate topics) + the salience gate the L1
amendment already specifies (novelty vs already-stored findings first;
embedding-similarity as the filed ranking lever — it ranks relevance, it cannot
substitute for the typing). The genuinely interesting deductive form — supply as
*abduction* (what missing fact would make the collaborator's plan sound?) — is the
research corpus's one specified-but-unrun experiment (abductive ASP); it is named as
experiment E-6, not designed here, because no measurement yet shapes it. Assigning it
an engine now would be exactly the formalism-led move this frame forbids.

## 4. The concerns draft, assessed (dilettante-labeled input, taken with its salt)

| Concern | Disposition |
|---|---|
| 1. ordering | **Accepted** as F7 (dependency, not sequence — the maintainer's own gloss). |
| 2. resources / underutilized tools | **Accepted, not as a logic function:** it is KB *content* (a capability registry the supply function draws on — the GLOSSARY's Pillar sense) plus a standing posture ("reach for tools even when the environment lacks them" — toolless ≠ unleverageable, already this project's creed). No formalism needed; F9 carries it. |
| 3. min-unsat-core | **Accepted with the dossier's own caveat intact:** first increment over already-TYPED substrates — dependency/version collisions, `AdvertisedLimits` axes, F7 ordering mandates — where Z3's native `unsat_core()` gives the minimal conflicting subset for free once the constraints are typed rows. NOT over prose ADRs: LLM-authored encodings of prose are on trial (fair-trials lesson), and a core over a mis-encoded constraint set is confidently-wrong blame. BUILD-PLAN increment 4. |
| 4. deontic | **Re-framed as ruled:** obligation-status is a finding attribute (§2 above), never the ontology. |
| 5. alethic | **Rejected** as a lane. The maintainer's own marking ("probably specious") is confirmed by the evidence: no measured requirement exhibits an alethic (necessity/possibility) failure mode. Its salvageable content — default reasoning under weak guidance to infer intent — is the defeasible machinery already assigned everywhere it earns keep (F1, F6, R-FUNC). A separate alethic modality would be a fabricated category (ADR-0008 negative register). |
| 6. defeasible | **Accepted as a property, not a function:** defeasibility is *how* F1/F6/F8 rules are written (default negation + named defeaters), demonstrated live since `logic_layer.lp`. The concern's "???" was the honest mark that it had no function of its own. |
| 7. doxastic taxonomy | **Rejected as a reasoner taxonomy** (Smullyan-style types are unmeasurable ontology here — the maintainer marked it "merely observational, probably specious"); **accepted in the reduced, measurable form** the dossier itself derives: hedge-trajectory-across-reversal (`R-SUP-ESC`, F1) — concern 7 made measurable. |
| 8. auditability | **Accepted structurally:** it *is* the KB co-design (append-only ledger, supersedes-chains, handles, verbatim grounding). Not a formalism; the shape of the store. |

**The floated mechanizations (dossier §5):**
- **Fact handles** — adopted for what they are strong for: citation, dedup, and audit
  (the claim handle and finding identity of INTERFACE §5 / KB-CODESIGN §2). NOT
  adopted as a content-substitute in active reasoning: a transformer cannot
  dereference a handle, so any injected context uses handle+gloss. The inline vs
  handle+fetch A/B (E-3) is the dossier's own named measurement; neither outcome is
  asserted here.
- **Reified work-unit/discharge boundaries** — presented in KB-CODESIGN §5 as a *new*
  idea for the maintainer to ratify (its absence from the research corpora is
  confirmed on record), shaped by the nearest neighbors the search did find (the
  COMMIT-lifecycle gap; the `audit_log` row-history pattern).

## 5. Engagement with the 2026-06-27 survey (departures argued, not strawmanned)

The obligations-formalisms survey is this design's strongest intellectual input, and
the departure from it must be precise:

- **Kept:** its central method — *match the formalism's semantics to the failure mode
  of the thing guaranteed* — survives wholesale as the assignment rule of §3; its
  qualification discipline (differential solving, mutation/golden fixtures) is the
  house gate triple this design mandates per function; its claim-ledger composition
  substrate agrees with the harness DB idiom and shapes KB-CODESIGN.
- **Departed — the organizing axis.** The survey organizes by obligation (17→19
  obligations, formalisms assigned to each). For *this* system that axis is rejected
  by ruling, and the ruling is right on the merits: the measured functions (mood
  typing, supersession modeling, commensurability) are not obligations and were
  invisible on an obligation map — the killed first attempt is the demonstration. The
  survey's frame remains apt for its own question (auditable software owing things);
  it was the wrong ontology for a support system whose purpose is proactive help.
- **Departed — the composition layer.** The justification-logic spine, the
  guarantee-strength meet, and the Gödel–Löb self-audit guardrail are *not* adopted.
  Grounds: the survey itself labels every verdict "agent-reasoned, not yet
  experimentally settled"; no measured requirement demands them; and the property
  they buy (self-certification structurally impossible) is already held at mechanical
  strength for everything shipped here by the differential gate + mutation tests +
  the adjudication boundary. If a future function's failure mode is genuinely
  "trusting an unqualified justification chain," the survey's design is the first
  candidate — that is a filed trigger, not a rejection of the idea's substance.
- **Departed — scope of "load-bearing core."** The logic-investigation corpus's
  reduced thesis ("most of it is a SQL job; exotic logic net-negative outside genuine
  non-classicality") is accepted as the *floor discipline* (every ASP assignment above
  keeps a SQL differential floor) but its deflationary default is not adopted as a
  design posture — per the maintainer's standing ruling (don't bend everything into
  SQL; elegance and intellectual yield count) and per the shipped evidence that ASP's
  non-monotonic increments (defeasible R-FUNC, minimal repair) already earn keep over
  the `mining.contradiction` view.

## 6. Honesty register — what is uncertain, and what decides it

Every uncertain assignment above carries a deciding experiment; they are collected as
the experiments ledger in BUILD-PLAN §4 (E-1 mood classifier precision; E-2
regime-key recoverability and R-QTY noise geometry; E-3 handle+gloss vs inline; E-4
mandate extraction from prose; E-5 CLP(FD) vs clingo on the first numeric scheduling
need; E-6 abductive supply). Per the frontier creed, each carries a kill condition;
none is retired or asserted by vibe here.

Hazards from the inventory that sit in this design's path, re-verified against the
artifacts on fresh read (not inherited from the inventory's snapshot — the ADR-0014
audit of this document caught exactly one stale inheritance, corrected here): the
`logic_backend.py:40` lazy-import docstring hazard the inventory flagged has since
been **remediated in the shipped file** (lines 44–48 now state the true posture and
endorse the ban) — no action remains. Two hazards stand: `fde_z3.py:111`'s bare
`assert` on the non-explosion invariant (elided under `python -O`; becomes a `raise`
in increment 2, INTERFACE §7), and `contra_app.py:41`'s `sys.path.insert`
cross-package reach, which contradicts the rows-not-imports coupling claim at its own
import line (BACKLOG holds the one-ruling fix; the ruling stays the maintainer's, as
filed).
