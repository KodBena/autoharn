<!-- engine-seed-panel wf_1ae3bf30-850; lens=adversarial; MODEL-SERVED (self-report): claude-fable-5 -->

MODEL-SERVED: claude-fable-5 (basis: my system prompt identifies me as "Fable 5, exact model ID claude-fable-5," and nothing in my own knowledge of my identity contradicts it; I have no independent channel to verify a silent mid-run downgrade, so per the provenance-honesty rule this is a self-report, not a proof. No degradation event was observed by me this invocation.)

# The Deductive Engine, designed from the adversarial-self-application lens

**Commission:** the component that consumes the ledger + acts stream + rulings and *derives* judgments about the collaboration — obligations, staleness, authorization, contradiction, honesty differentials — as a first-class engine, live and at close, rather than as humans or ad-hoc scripts. **Lens:** the engine is itself a tool whose output is trusted without independent human check. Under the BRIEF's own F6/I8 that makes it a qualification-bearing tool: *an unqualified checker is an unverified verifier.* So this design is organized backwards from the ways such an engine lies, with the project's banked instrument-failure specimens as the evidence that every one of these lying modes is real — most of them have already happened inside this apparatus, at N≥1, adjudicated.

## 0. The one-line contract

> A **judgment** is a typed verdict about the collaboration record, derived by a named engine version from a watermarked fact export under a cited ratified law, banked with a DerivationRecord, drawn from a closed discharge vocabulary in which silence is unrepresentable — and anything the engine cannot promise under that sentence it must *say* it cannot promise, in the record, machine-readably.

Everything below is the type structure (ADR-0000: what type makes each lying class unrepresentable), the mechanism (ADR-0011-shaped nets where a type cannot reach), and the honest residue (declared, never implied covered).

## 1. How this engine lies — the threat catalog, specimen-grounded

Each mode below names: the mechanism, the banked specimen proving it is not hypothetical, and the countermeasure (detailed in §2). This catalog is the engine's own F49-class register: a lying mode with no countermeasure row would itself be a silent gap.

**L1 — Derivation from the wrong or stale substrate.** The engine reasons soundly over facts that are not the record of record. Specimens: the e9 gate consumed `T_event` as `T_now` and derived two invalid tickets (F28, rows 25/27 — `gate_ok ∧ ¬sound_ok`, live); the close instruments were keyed to a prior arm's environment constants and *silently did not run* against the nla record of record (F49); the marriage body's own §3 EDB signature was stale against ground truth until the link-23 live verification (Appendix A.1). Countermeasure: substrate SSOT resolution + capability manifests + watermarked exports (§2.3).

**L2 — Silent non-derivation, and timeout-as-silence.** "No flag" is read as "checked, clean" when it actually means "never ran," "crashed," "grounding error," or "budget exhausted." Specimens: clingo emits *valid JSON with an empty model* on a grounding error, so a broken program banks an empty-atom result as if it were a derivation (marriage A.8); `soundness.py`'s condition-2 line was guarded by `if amends:` and silent rather than "(none)" on a zero-amends ledger (F49); the e17 gate-journal was never registered so contemporaneity read N/A off a skipped arming step (consult 35 §0). Countermeasure: total-map output types over a closed discharge vocabulary — silence made unrepresentable (§2.1) — plus quarantine-on-empty-over-nonempty-EDB, already built (A.5/A.8) and here generalized.

**L3 — Rules drifting from ratified law, and apocryphal rules.** The encoding stops matching the law register: a clause weakens during a refactor, a rule implements a consult's *proposal* rather than the maintainer's *ruling*, or a rule exists that no ratified law authorizes. Specimens: `soundness.lp` itself keyed defeat on `ts <=` while the ratified law was strict id-precedence — the operator's own instrument was the non-conforming encoding by the operator's own law, caught only by a fidelity review and retrofitted (soundness.lp header, F-D); DTO shows the inverse hazard — consult 19 argued one direction, the maintainer overruled it, and an engine encoding the consult would encode overruled law. Countermeasure: per-rule law citations + a register-diff gate + mutation tests (§2.2).

**L4 — Vocabulary capture and Goodharted judgments.** Any judgment that prices a self-declared label corrupts that label as a measurement, in whichever direction avoids the cost — and a live engine whose derivations teach or deny creates exactly such prices. Specimens: F24/F26 at both signs (e8 deny-message vocabulary primed `decision`-inflation; e9 structural cost drove the enactment register into `process`); F26 is ratified consumer law. The subtle live-engine form: the teach-text itself becomes a training signal (e17's subject read the hook source and the frozen teach text — that channel is real and *worked*, which means it also shapes). Countermeasure: label-indifferent derivation inputs where a judgment carries a price; a declared Goodhart surface per judgment; frozen, versioned, specimen-tested teach texts (§2.5).

**L5 — The engine miscites its own substrate.** Engine outputs point at row ids; a desynced pointer fabricates provenance with a confident face. Specimens: F42 (row 31 `enacts={27}`, a two-slot desync from a kind-filtered read-back, caught *only by luck* of the target's kind); F22 (narration citing nonexistent ids #37/#40); F45 (a coincidental basename match authorizing an edit under an unrelated stale row). The law is ratified: citation currency must be record-observed at the moment of citation (F42/F46); memory-grounded correctness fails closed only by luck (F46/F48). The engine must obey the law it enforces: every id in an engine finding is emitted from the same watermarked export the derivation ran over, never recomputed or remembered across exports. Countermeasure: findings carry the export hash they were derived from; a finding whose ids do not resolve in its own named export is a construction-time failure (§2.4).

**L6 — The green wall: a gate never seen red.** The operator trusts a page of AGREE/OK lines from nets that have never fired. Specimens: the entire F49 episode is a green wall over three non-running instruments; ADR-0011's "a gate never seen red is a claim, not a net" is standing law; the marriage already pays for this with banked adjudicated defects as golden fixtures (§5 of the marriage doc). Countermeasure: the seen-red discipline as a *first-class output property* — a judgment class that has never flipped red on a fixture or specimen is displayed as UNPROVEN-NET, not as assurance (§2.6).

**L7 — Correlated producers dressed as independence.** The differential's two producers (Postgres recursive CTE vs clingo) are genuinely independent *engines*, but both consume the same `ledger_edb.py` export: a defect in the export fools both, and the AGREE verdict launders it. This is the channel-independence obligation (BRIEF F15/I6) applied to the engine itself; no banked specimen yet — which under the frontier creed means it is pre-registered as an open residual, not assumed away. Countermeasure: a raw-substrate audit lane that bypasses the shared export on a sampled basis, plus the declared shared-substrate residual in the engine's own conformance block (§2.4, §2.8).

**L8 — Live-run temporal lies.** Live, "no flag at turn t" silently means "no flag derivable from facts as of watermark N, within budget B, by engine version V" — and a hook that degrades (daemons down, timeout) leaves a turn unexamined while the close still reads clean. The e17 arming gap is the close-side shape of this; the hook disciplines (time-budgeted, degrade-not-block) create the live-side shape by design. Countermeasure: per-turn derivation statuses are themselves ledgered facts; the close manifest accounts for live coverage (how many turns ran, how many degraded) so a mostly-TIMEOUT run cannot read as continuously checked (§2.7).

**L9 — The coverage lie (I12).** The engine judges the ledgered record under the parser's perimeter; conduct outside it (F38), J-triggered omissions (the BRIEF's J-boundary), unledgered delegation events (e17's `unledgered_span(463,464)`), and subject build-tool provenance are invisible to every rule. An engine that does not state this boundary *implies* it covers it. Countermeasure: the declared-exclusion surface, machine-readable, emitted every run (§2.8) — the substrate capability manifest generalized to the whole engine.

**L10 — Acts-parser drift.** The acts stream is parsed from vendor transcripts; a silent format change truncates the acts EDB and every claims-vs-acts differential quietly weakens (the binder's batch-insert artifact — `unbound_row` at e17 — is the mild, caught form; a parser that drops a tool-call class entirely is the severe, uncaught form). Countermeasure: the parser is a qualified tool like any other — version-pinned, parity-pinned against banked transcripts, with parse coverage (acts recognized / bytes consumed) a manifest line whose regression is RED (§2.3).

## 2. The countermeasure architecture

### 2.1 The Judgment Register and total-map outputs (kills L2 structurally)

One Python authority module (`judgment_register.py`, ADR-0012 P1: one home) declares every judgment the engine claims, as a typed record:

```
JudgmentSpec:
  id                (e.g. J-TNOW-INFORCE, J-STALE-DEBT, J-SOD-INDEP, J-CLAIMS-VS-ACTS-BINDING…)
  semantics_class   (monotone-closure | nonmonotone-closure | combinatorial | arithmetic | report-lens)
  engine            (SQL | ASP | SMT | FDE-lens)      # assign-don't-compete, the §4 marriage table as data
  law_citations     [F-numbers / acts.ruling ids / consult §§]   # §2.2
  floor_producer    (the independent second producer, or a declared none-with-reason)
  fixtures          [banked specimen ids + required mutations]   # §2.6
  availability      (live | close | both)
  goodhart_surface  (which input facts the subject controls; pre-registered gaming residual)  # §2.5
  substrate_needs   [capability-manifest keys]        # §2.3
```

From this one authority derive: the documentation table, the close-manifest line set, and — the load-bearing type — the engine's output type: a **total map** `judgment_id → DischargeStatus` where `DischargeStatus ∈ {DERIVED(verdict), DERIVED-EMPTY(grounding-witness), NOT-RUN(reason), TIMEOUT(budget), QUARANTINED(cause), EXCLUDED(declared-reason)}`. Totality is the ADR-0000 move: the F49 failure class (a mandatory line silently absent) becomes *unconstructible*, because an output object missing a registered judgment cannot be built. Two details carry the honesty:

- **DERIVED-EMPTY is distinct from DERIVED(no-findings)** and requires a positive grounding witness — at minimum, proof the program grounded nonzero rules over a nonzero EDB (the A.8 quarantine generalized). "The solver said nothing" is never bankable as "clean."
- **EXCLUDED requires a reason drawn from the capability manifest**; a caller cannot exclude ad hoc. This is A.2's loud-declared-exclusion rule promoted from the substrate to every judgment.

The verdict payload keeps the closed differential vocabulary already ratified: {AGREE, DIVERGE_BY_DESIGN, DIVERGE_DEFECT, QUARANTINED}; DIVERGE_DEFECT and QUARANTINED exit non-zero and turn the run red.

### 2.2 Law provenance: every rule cites the law it implements (kills L3)

Every load-bearing clause in every engine program (`.lp`, SQL view, z3 lane) carries a machine-readable law citation (`% LAW: F28`, `% LAW: acts.ruling 29 (F53)`, `% LAW: consult 17 §5.3 id-is-order`). Two gates ride on this:

1. **The register diff.** A standing check compares the union of cited laws in deployed rules against the ratified register (FINDINGS.md F-entries with ruling anchors + `acts.ruling` rows). Three outcomes, all loud: a ratified consumer-law with no implementing rule and no declared exclusion → RED (an undischarged obligation); a rule citing no law → QUARANTINED as apocrypha (it may be right, but it is not *law*, and an engine that enforces non-law is a vocabulary-capture engine); a rule citing an overruled or superseded law (the register knows supersession — it is a ledger) → RED. This makes L3 drift a detectable defect rather than a review hope. Honest limit, stated: the diff proves citation *presence and currency*, not semantic fidelity of the encoding to the law's meaning — that residue belongs to the next mechanism.
2. **Mutation tests per clause** (the LOGIC-LAYER-ASP bar, inherited unchanged): every load-bearing clause has a mutation that must flip a verdict on a fixture. A clause whose deletion flips nothing is either dead or untested — both are findings. The soundness.lp ts→id retrofit is the standing proof this catches real non-conformance: the `<=`-vs-`<` boundary case is exactly a mutation-shaped divergence, and the operator-twin differential (`soundness_twin.py` as a declared close line) is its permanent net.

### 2.3 Substrate honesty: manifests, watermarks, and the parser as a qualified tool (kills L1, L10)

- **Resolution via SSOT:** every derivation resolves its db/schema/session from `ledger_target.py` (the finding-36 rule); an unregistered substrate is REQUIRED-ABSENT/RED, never a vacuous pass.
- **Capability manifests** (built, A.2) extend to the acts stream and rulings: per target, every fact family the export cannot produce is a declared exclusion with reason; a judgment whose `substrate_needs` include an absent capability lands as EXCLUDED(reason) in the total map — automatically, from the register, so the exclusion is *derived*, not hand-asserted.
- **Watermarks:** every export carries `(target, max_id, export_hash, exporter_version)`. Every judgment status embeds the watermark it was derived at. Live, this converts "no flag" into the honest sentence "no flag over facts ≤ id N" (L8); at close, it makes stale-substrate derivation (L1) type-visible — a close that banks a judgment watermarked below the record's max id is RED unless the gap is a declared exclusion. Id, never ts, is the order (consult 17 §5.3, enforced as in A.3).
- **The acts parser is a tool under I8:** version + config pinned in every DerivationRecord that consumed its output; parity-pinned against banked vendor transcripts (the persisted ephemera are the fixture corpus — the auditability clause pays off here); parse-coverage ratio is a manifest line with a ratcheted floor. A vendor format drift then presents as a loud coverage regression, not a quietly thinner acts EDB.

### 2.4 The derivation kernel: DerivationRecord, self-citation currency, and the shared-substrate residual (kills L5, bounds L7)

The kernel signature is one honest function: `derive(judgment_id, target, watermark, budget) → (DischargeStatus, DerivationRecord)`. The DerivationRecord (built, A.4) — {engine+version, config, EDB/program/output hashes} — is retained with the programs, EDB, and atom outputs (I11/F16: re-runnable, not asserted). **A verdict without both records is NO RESULT** — the already-ratified rule, kept as the kernel's outermost type.

Self-citation currency (L5): a finding's row-id pointers are emitted *from the export named by its own DerivationRecord* and are validated against that export at construction — a finding object with a non-resolving id cannot be built. This is F42's law applied to the engine's own mouth: the engine never cites from memory, across watermarks, or from a recomputation.

The L7 residual is handled in two honest halves. Mechanism half: a **raw-audit lane** — for a sampled subset of judgments per close, an independent query path (plain SQL against the live schema, no `ledger_edb` import; ADR-0012 P7's "two derivations of one truth must not share a hand-authored middle") recomputes the verdict; disagreement with the differential pair is DIVERGE_DEFECT. Disclosure half: the engine's conformance block names the shared-export channel as a correlated-failure surface that sampling shrinks but does not close. No overclaim: three producers sharing one Postgres are still one substrate at the bottom; that floor is stated.

### 2.5 Label-indifference and the Goodhart surface (kills L4's mechanized half, declares the rest)

Standing rules, inherited as law, now bound to the register:

- **Flag-never-auto-resolve (F28):** the engine never rewrites the record; every derivation lands as flags/journal into the review queue with FindingIdentity idempotency (re-running on an unchanged record inserts zero rows).
- **The only deny surfaces are the write-boundary triggers**, and a judgment class is promoted to a refuse-and-teach trigger only through the specimen pipeline e16→e17 proved: caught post-hoc → proven by deriver → banked as fixture → mechanized at write time with a **frozen, versioned teach text** delivered verbatim. The teach text is part of the measured apparatus (e8/e9 proved deny-message vocabulary reshapes subject labeling), so changing it is a versioned apparatus change, never a casual edit.
- **Per-judgment Goodhart surface, pre-registered:** each JudgmentSpec names which of its input facts the subject controls (self-declared labels, prose, self-chosen edges) versus which are subject-uncontrolled (interception stamps, ids, acts-stream facts, write-time-injected columns). A judgment that *prices* behavior (feeds a trigger or a gate) may key **only** on subject-uncontrolled facts — F26 as a type constraint, checkable from the register. Judgments keyed on subject-controlled facts stay flag-only, and their register row says so. What cannot be mechanized is the subject adapting to the *existence* of flag-only judgments; that residual is pre-registered per the harness threat-model scope (ledger-vs-acts honesty, not sandbox adversary), not silently absorbed.

### 2.6 The seen-red discipline as an output property (kills L6)

Qualification of an engine version is: (a) bit-identical reproduction of all banked instrument numbers on s9–s14/nla (the four-arm discipline, inherited); (b) every fixture in every JudgmentSpec reproduced — rows 25/27, the launder negative control, 31→27 with its kind-luck mutation, event 61, the F44 aspectual triple, the same-second id-order fixture, the empty-model quarantine; (c) every mutation flips its verdict. New, from this lens: **red-count is carried into the display layer.** Each judgment's close line shows when that net last fired red (fixture or live specimen). A judgment class that has never been red anywhere — including on its planted-defect witness — renders as `UNPROVEN-NET`, visually distinct from OK. The operator's green wall thereby carries its own calibration: a wall of OKs over UNPROVEN-NETs *looks like* what it is. This is ADR-0011 applied to the reader, not just the builder.

### 2.7 The live service: replay-equivalence and coverage accounting (bounds L8)

Live derivation is the marriage §7 hook ladder (L1′ self-consistency, L2′ currency/debt, L3′ engine interrogation behind the seam), cursor-incremental, time-budgeted, degrade-not-block — with two additions from this lens:

- **Per-turn statuses are facts.** Each hook invocation banks its own total map (usually a small registered live-subset) with watermark and budget outcome into the derivations store. The close manifest then computes **live coverage**: turns examined / degraded / skipped. A run whose live lines were 80% TIMEOUT closes with that number on its face; "the hook was on" can never again stand in for "the hook ran."
- **Replay equivalence as the live path's acceptance gate.** The live incremental path (and any future clingo multi-shot grounding) is qualified against the retrospective path by replaying banked sessions' acts streams as simulated live runs: at close-of-replay, the accumulated live verdict set must equal the retrospective derivation over the full record (set equality of finding signatures — the fair-trials lesson: the gate is set equality, never a model's judgment of similarity). Divergence is a defect in the incremental path by definition. This also yields the latency data the live design needs (§4, unknown U1) from evidence already paid for.

Timing honesty: the live engine makes **no real-time guarantee** (the conformance map's F14 exclusion holds for the engine too). Its promise is bounded-effort-with-visible-degradation, and that is the sentence the register carries.

### 2.8 The engine's own conformance under the BRIEF (the self-application, made a deliverable)

The engine emits, every close, a machine-readable **self-conformance block** in `close_manifest` — its own row-set in the BRIEF-CONFORMANCE-MAP vocabulary (mechanized / instrumented-retrospective / built-unexercised / review-only / open). The mapping this design commits to:

| Inv | Engine obligation | How |
|---|---|---|
| I1 | derivations timestamped + watermarked at run time, never reconstructed | DerivationRecord banked at derivation; append-only store |
| I2/I8 | the engine is an attributable tool: version/config/hash pinned per verdict | DerivationRecord; parser pinning (§2.3); NO RESULT without records |
| I3 | derivations append-only; a re-derivation supersedes, never overwrites | derivations store under the same append-only trigger class as the ledger |
| I4 | negatives first-class: NOT-RUN/TIMEOUT/QUARANTINED/UNPROVEN-NET are outputs, not absences | total map (§2.1); live coverage accounting (§2.7) |
| I5 | finding → rule → law → input-facts traceability, each end id-pinned | law citations (§2.2) + self-citation currency (§2.4) |
| I6 | the engine never adjudicates its own divergence | DIVERGE_DEFECT routes to review, exits non-zero; the differential's producers are distinct engines; raw-audit lane sampled |
| I7 | the engine's own assumptions carried with validity bounds | an explicit assumption register in the JudgmentSpec store: id-is-order (valid only on append-only lineage), export-parity (valid until schema change → red parity test), threat-model scope; each with its invalidating condition named |
| I9 | discharge-status honesty: DERIVED ≠ DERIVED-EMPTY ≠ reviewed ≠ excluded, never conflated into "checked" | the closed vocabularies (§2.1); UNPROVEN-NET (§2.6) |
| I11 | re-runnable: EDB + programs + outputs + records retained, versioned | built (A.4/marriage derivations dir), extended to live per-turn maps |
| I12 | the engine states its own boundary every run | the self-conformance block itself + declared exclusions (§2.9) |

Honesty about I8's ceiling: fixtures + mutations + differential are this project's qualification basis; they are **not** a DO-330 TQL or 26262 TCL certification, and the block says "qualification basis: project-internal, N-small" in those words. The NRC-bar posture is that the dossier is *shaped* like a tool-qualification dossier (operational requirements = the register; verification cases = fixtures+mutations; configuration index = DerivationRecords) so that an external qualifier has a real object to examine — not that the qualification already exists.

### 2.9 The promise/disclaim boundary (the engine's I12 sentence)

**The engine can promise:** for each judgment with status DERIVED at watermark N — the verdict follows from the cited rules (whose fidelity is fixture-and-mutation-tested and differential-gated) applied to the exported facts ≤ N of the named target, reproducibly from retained artifacts, with every cited row id resolving in the named export.

**The engine must disclaim, by name, machine-readably, every run:** reference *truth* and use-as-claimed (F20/F27 — an engine proves resolution and structure, never that cited content matches citing intent; review owns that); J-triggered absences (no oracle that a noticing-trigger fired — the BRIEF §3 boundary, restated not repaired); conduct outside the ledger+acts perimeter (F38) and unledgered event classes (delegation events until a kind exists); subject build-tool provenance (I8 subject-side, open); the shared-export correlated channel (§2.4); encoding fidelity beyond the fixture set (N-small ceiling — engine agreement on banked specimens is qualification, not proof of soundness on unseen records); real-time properties (none claimed); and prescriptive deontics (the engine derives normative *status* — `review_gap`, obligation-in-force — never prescribes action; the deontic line stays where the schema put it).

## 3. Increments, each with a checkable acceptance target

1. **Judgment Register + total-map output type**, retrofitting every existing marriage/instrument derivation under it. *Accept:* every current close line appears as a registered judgment with a status; deleting one rule file flips its judgment to NOT-RUN and the close to RED (the F49 negative control, mechanized); no output object constructible with a missing judgment.
2. **Law-provenance citations + register diff.** *Accept:* an injected apocryphal rule → QUARANTINED; commenting out the F28 implementation → RED undischarged-law; citing the overruled consult-19 clause-defeat direction → RED superseded-law.
3. **Acts-stream EDB + parser qualification**, promoting the binder/`unledgered_span`/claimed-vs-performed scripts into registered claims-vs-acts judgments. *Accept:* e17's `unbound_row` and `proxy_written(12)`/`self_performed(17,18)` reproduce bit-identically as registered judgments; a synthetically truncated transcript trips the parse-coverage floor.
4. **Replay harness.** Banked sessions replayed as simulated live runs; latency measured per turn at growing EDB sizes. *Accept:* replay verdict set == retrospective verdict set on all banked targets (set equality of signatures); a latency table that answers U1 with data.
5. **Live hook increment** (marriage §7 re-founded under §2.7): per-turn total maps banked, FindingIdentity idempotency, coverage accounting at close. *Accept:* planted ledger defect found live; daemons-down replay closes with visible degraded-coverage lines, never a clean close; unchanged-record re-run inserts zero findings.
6. **Self-conformance block + UNPROVEN-NET display.** *Accept:* the block renders from the register with zero hand-written rows; a fresh judgment class with no red history displays UNPROVEN-NET until its witness fires; the raw-audit lane catches a deliberately corrupted `ledger_edb` export (the L7 negative control).

Ordering note: 1–2 before any new judgment content, because they are the type that makes the later increments' lying modes unrepresentable — building more derivations first would be authoring new structure in the old shape (ADR-0012's reason to exist).

## 4. Unknowns, and how to find out

- **U1 — Live latency envelope.** Whether per-turn full re-derivation holds to hook budgets as records grow, or incremental/multi-shot grounding is needed. *Find out:* increment 4's replay latency table over banked sessions plus synthetic row-scaling; decide on data, not intuition.
- **U2 — Incremental-derivation soundness.** If multi-shot is needed, its equivalence to batch derivation is not free. *Find out:* the replay set-equality gate is the standing net; any incremental path lands behind it or not at all.
- **U3 — Teach-text side effects at N>1.** e17 proved one refusal converts ceremony to honesty once; whether frozen teach texts induce durable vocabulary shifts across runs is unmeasured. *Find out:* specimen-driven, one lever per experiment, per the standing N=1 apparatus discipline — never by weakening F26.
- **U4 — Vendor transcript drift rate.** Unknown until it happens. The parse-coverage floor makes it loud when it does; the persisted-ephemera corpus makes the parser re-qualifiable when it must change.
- **U5 — DTO arrival.** The T_now semantics are DTO-ready (marriage §4/A.6); when `decomposes` facts arrive on the lineage of record, the FDE report lens retires per-case. The register's `semantics_class` field is where that transition is recorded, not a rewrite.
- **U6 — What an external qualifier actually requires.** The dossier shape (§2.8) is this project's best-faith reading of DO-330/TCL analogs; whether it satisfies a real assessor is findable only by handing it to one. Stated as the honest end condition of the NRC bar, not claimed met.

## 5. What this design deliberately does not do

No new ledger kinds or edges minted; no enforcement from the derivation layer beyond the specimen-proven write-time trigger pipeline; no harness demand argued from our own runs' absence (the BRIEF is authoritative; fourteen experiments are a censored record); no kernel truth-value change (FDE stays a report lens); no claim that self-application closes the regress — the engine checks the record and the register checks the engine, but the register's own maintenance is review-plus-ruling, and *that* is the honest bottom: one layer of the tower is always held by judgment, and this design's contribution is to make it exactly one layer, named, small, and visible, instead of an unstated diffusion through every script.

---
*Record basis: LEDGER-LOGIC-MARRIAGE.md (body + Appendix A) in full; safety-critical-logging BRIEF in full; BRIEF-CONFORMANCE-MAP.md in full; instruments/core_a.lp and soundness.lp in full; FINDINGS.md (F1–F53, read through both pages); consults/e17-analysis-consult-35.md in full; ADR-0000 in full; ADR-0012 through P9 + the C++ contract head (remainder is compiled-component guidance not load-bearing here). No sub-agents; no files modified; psql not touched.*