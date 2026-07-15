# Synthesis-input dossier — everything the NLP↔logic interface design must ingest

**Status:** commissioning dossier, assembled 2026-07-02 at session end. The synthesis itself
is DEFERRED (Fable-tier, maintainer-gated on quota). This document exists so the commissioning
can fire the moment it is authorized, with nothing lost to memory decay. The frame corrections
below are RULINGS, not suggestions — a synthesis that violates them repeats a killed attempt.

## 1. The frame (two corrections, both maintainer-ruled 2026-07-02)

- **Purpose-first, functions-not-obligations.** Deontic-as-primary is REJECTED ("the lazy
  ADR-0013 violation"). The purpose: keep LLM collaborators doing the right thing proactively —
  interrogate their epistemic state and in-progress work against a knowledge base; proactively
  supply the information they need. Formalisms are ASSIGNED to the functions this demands;
  whether a function is an obligation is a finding, never the ontology. TRAP, tripped once
  (agent killed for it): any brief saying "assign formalisms to obligations" re-smuggles the
  rejected primacy regardless of a purpose-first preamble.
- **Sequencing: inventory-first.** The evidence base now exists (this directory: INVENTORY.md,
  RESEARCH-SUMMARIES.md). The synthesis extends a REAL seam, not a blank page: LogicBackend
  Protocol (analyze(claims) → findings), two engines (clingo ASP: 3 rules + defeasible R-FUNC +
  minimal repair; Z3 FDE: R-NEG glut), mechanical cross-engine differential, typed spine
  FactBundle → Claim → Finding, coupling by DB rows not imports, no confidence scores anywhere
  BY DESIGN (honesty = rule-id + grounding, type-enforced at the adjudicate boundary).

## 2. The maintainer's function draft

`docs/possibly-addressable-concerns.md` — 8 concerns (ordering; resources/underutilized tools;
min-unsat-core; deontic; alethic; defeasible; doxastic taxonomy; auditability), self-labeled
dilettante draft, some marked possibly-specious. Standing style rulings inside it: don't bend
everything into SQL (CLP(FD) can be more elegant; intellectual stimulation is a primary motive);
reach for tools even when the environment lacks them.

## 3. Requirements WRITTEN BY MEASUREMENT (the trial series, 3 trials + enrichment)

Evidence: experiments/fact-mining/docs/hook-trial/ (all findings JSONs reproducible from the
committed corpus). The series' conclusion (HOOK-DESIGN.md §4b): surface rules see neither the
precision nor the recall side of the real genre; the logic layer is a PREREQUISITE of useful
L1, not its L3 luxury. Specific requirements the engine inherits:

- **Temporal state-change / belief revision** — the main-session R-NEG surplus (4.5× subagent
  density) is dominated by "was X, now fixed" narratives: supersedes-chains to MODEL, not
  contradictions to flag. The maintainer's perf sessions ("must be this" → "nope, but *this*
  time I'm absolutely sure") are the canonical genre; confidence escalating across a reversal
  is itself a doxastic signal (concern 7 made measurable).
- **Assertion mood / use-vs-mention** — the reason the sharpest rule yields zero clean
  candidates: interrogatives, quoted bug titles, mentions of contradictions read as claims.
  Specimen: "Cleaned [moving on]" (BACKLOG) — action-report truth laundering a defeasible
  closure into a closure claim; the engine must hold (a) action-report, (b) defeasible
  inference, (c) verified closure apart when surface grammar does not.
- **Commensurability for quantities** — the 11.5% of number-grab residue that GLiNER's typing
  correctly admits but that only commensurability reasoning (same measurement regime?) can
  adjudicate.
- **Predicate-standard indexing** — gradable predicates carry a hidden standard; specimen: the
  maintainer's "not entirely out of my league / pretty much entirely out of my league" —
  perfectly true under two standards, a glut under none, subject-collapse's exact structure one
  level up (predicate axis, not entity axis). Architecture implied: tolerate paraconsistently at
  ingest (the FDE lane exists), resolve contextually when the index is recoverable, treat the
  unresolved form as calibration data, not noise.
- **Role-stratified universes** — assistant-self / user-instruction-consistency (contradictory
  maintainer mandates are a first-class diagnostic, surfaced TO the maintainer) / cross-role
  conduct-vs-mandate. Harness-injected/quoted content must be separated at ingress before the
  user stratum is honest.
- **Goal-substitution detection** — specimen: the impedance F-algebra→tagless-final arc
  (BACKLOG; sessions incl. e066e340): a design decision carries its recorded WHY; when means
  change, the WHY is re-verified or explicitly retired — silence is a flag. Fatigue-ratification
  does not discharge a standing mandate. This is the frontier creed ("retire only via a failed
  experiment") needing a mechanism, i.e. ADR-0011 at the knowledge level.
- **Ordering as dependency, not sequence** — "ADRs before relevant work" (maintainer: reading
  first is prudence under imperfect memory, not the mandate). Precedence relations over reified
  work units; concern 1.

## 4. What the NLP side can now deliver (measured capability envelope)

- Typed entity mentions: GLiNER service (:5601, standing, house-pattern) — WIRED AND MEASURED
  end-to-end (be71ce9): joint noise floor 483→54 findings across both corpora (12×/7× cuts,
  R-NUM suppression 93.5%/88.5%), 0 novel findings (enriched arms strict subsets — enrichment
  cannot create recall), 0 candidates of 54 hand-read; the known-live positive (874 MB/2.9 GB)
  still at zero recall. 57.8% clean subject discrimination; hard limits: 5.5% abstract subjects
  untypeable, 24–37% spelled numbers unlocatable (gate-open), ~105–110 ms/sentence enrichment
  cost. THE RESIDUE IS NOW ALMOST PURELY THE ENGINE'S LANE: of the 54 survivors — subject
  collapse 35, mood/mention 8, temporal state-change 3, quantity-regime 1 (correctly admitted;
  only commensurability reasoning can adjudicate it).
- PROSE Port (transcript_prose.py) with role provenance; per-doc isolation on every ingress;
  advertised limits + envelopes on all three daemons (ADR-0016's worked instances).
- NOT yet available: mood/hedge typing, temporal ordering of claims, canonical entity IDs
  across sessions (GLiNER types mentions; it does not resolve identity).

## 5. Candidate mechanizations the maintainer has floated (assess, don't inherit)

- Fact HANDLES (8-char claim ids) for token economy — strong for citation/dedup/audit; risky
  as content-substitute in active reasoning (a transformer can't dereference); handle+gloss
  the likely shape; measurable (inline vs handle+fetch A/B) — do not assert either way.
- MIN-UNSAT-CORE over new-requirement-vs-spec conflicts — first increment over already-TYPED
  substrates (dependency/version collisions, AdvertisedLimits axes, ordering mandates), NOT
  prose ADRs (LLM-authored encodings are on trial: fair-trials lesson; mechanical gates first).
- Reified work-unit/discharge boundaries — the maintainer half-remembers a research remark;
  CONFIRMED ABSENT from the four corpora (RESEARCH-SUMMARIES.md locates the nearest neighbors);
  the idea is his to ratify as new, not to re-find.

## 6. Constraints on the synthesis itself

- Fable-tier, ONE commissioning (the killed attempt is a sunk cost; its deliverable structure —
  executive map + interface design + KB co-design + phased plan — remains right).
- Sub-agent spawns opus/sonnet only; the standing brief-hygiene clauses apply.
- The KB co-design question is live on both ends: the mining/contra schemas exist and are
  narrow; the claim-ledger shape (harness DB) is the house idiom; storage of ~/.claude-derived
  claims is RULED durable-approved (scrub boundary stays).
- Engine assignment follows the failure mode of the thing being guaranteed (assign-don't-
  compete survives the primacy correction); every assignment must name its encoding path into
  an available engine (toolless ≠ unleverageable) and its qualification gates (mechanical,
  never LLM judgment).
