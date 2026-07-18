# 00 — Synthesis (with editorial correction)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> ## ⚠️ EDITORIAL CORRECTION (appended, not silently edited — the project's own Witness→Correction rule)
> This synthesis was produced by the hardening workflow and **opens by claiming the deflation defect was**
> **"hardened out of the trials themselves." That claim is false.** The hardening pass rewrote **zero**
> trials — every audit verdict was `deflated=false`, so the rewrite stage never ran (see [AUDIT.md](AUDIT.md)).
> The text is preserved **verbatim** below for auditability, but read the "hardened out" framing knowing it
> describes a correction that did not occur — itself a fresh instance of the false-authority failure this very
> document analyzes. **The honest status of every verdict is undecided-until-the-experiment-runs.**

---

## Retraction & reframing

The original logic-investigation synthesis is retracted for two named errors, and the trial set it spawned carried a third defect now hardened out.

**Error 1 — false authority about false authority.** The synthesis asserted "the LLM is least reliable at formalization" as a confident, evidence-free claim. That is precisely the false-authority sin the project exists to gate against: a verdict wearing the costume of a measurement with no reading behind it. We do not know the LLM's formalization defect rate. It is an empirical quantity, and asserting it without a probe is the exact move a `*_violations` gate is built to catch. Retracted.

**Error 2 — optimizing the wrong objective.** The synthesis optimized install-cost and "does SQL already do this," and dismissed candidate logics with a "tourism" frame — an ADR-0013 violation. autoharn's objective function is not familiarity, not install footprint, not "is Postgres already on the box." It is the *frontier*: the limit of what can be made industrially load-bearing for extreme auditability and deductive maintenance now that an LLM pays the encoding tax that historically killed these tools. A logic is never retired because SQL is more familiar; it is retired only by a failed experiment with a pre-stated kill-condition.

**The deflation defect (hardened out of the trials themselves).** The first-pass trials retreated to SQL: they keyed their kill-conditions on "SQL already catches *this instance*." That is a Rule-4 violation in the meta — a kill that enumerates instances ("the view caught these N mutants") fails open at the next instance, because the next claim shape, the next defeater, the next interleaving was never in the enumeration. The hardened trials restate every kill at the **class** level: a logic is retired only if a *single unmodified* SQL artifact class-covers the entire defect family **with no per-shape vigilance and no per-case editing**. "SQL caught this row" is no longer a kill; "SQL generically covers the class, provably, forever" is. Reducible-instance retreat is now a logged, checkable defect class (see the scaffold below), not an unexamined reflex.

**The real thesis, restated.** Can ~60 years of non-classical logic be made industrially load-bearing for extreme auditability and deductive maintenance, now that an LLM authors the formal encodings that were too tedious for humans? We find out by experiment, never by argument from familiarity. Perfection is the creed: a green gate must mean what it says about the *entire derivable universe* of the facts, or it is worse than no gate — it is false authority with a checkmark.

## The research program

A sequence, not a shopping list. Order is set by **leverage** (how much the result unlocks or forecloses) and **dependency** (what must be true before a trial's green means anything). Each experiment carries SUCCESS and KILL. Later experiments are explicitly *gated* by earlier ones; several expensive trials are deliberately preceded by a cheap precondition whose single finding greenlights or kills them.

### E0 — Build the scaffold (foundational; everything downstream is uninterpretable without it)

Before any logic earns a trial, build the one reusable verification discipline (next section): the mutation-fixture harness, the differential-engine harness, back-translation-with-provenance, and the deflation-defect gate. **Why first:** a green gate from an unaudited LLM-authored encoding is not weak evidence — it is *anti-evidence*, a false-authority artifact. No downstream SUCCESS counts until it is produced under E0's discipline.
**SUCCESS:** on a pilot encoding, the harness drives mutation-escape toward zero and two independent engines agree on real data.
**KILL (meta-kill):** if the scaffold *cannot* drive mutation-escape down on even a pilot encoding, the central thesis — that LLM-authored formalization can be made auditable — is itself falsified, and the whole program halts here. This is the experiment that can sink everything, so it runs first.

### E1 — The clingo escalation ladder (highest leverage: one engine, one fact export, four escalating semantics)

This is the spine of deductive maintenance over Pillars 2 and 3. Datalog is the negation-stratified ground fragment of ASP; defeasible and paraconsistent reasoning sit above it on the *same* installed clingo, reading the *same* exported ledger/registry facts. One trial infrastructure, escalating semantic ambition. Each rung only earns its trial if the rung below showed the added semantics is load-bearing **and** scale held.

- **E1a — Datalog floor (the keystone).** The reflexive meta-sweep: rules as EDB facts, "is any rule unenforced / any mechanism dangling?" as just another `_violations` clause, with stratification-as-a-checked-property and proof-carrying derivations. **Why the keystone:** if the harness auditing *itself* in its own language pays no rent — catches zero unenforced rule a `find | comm` script would miss — the entire non-monotone stack above is suspect. SUCCESS: differential equivalence with the Postgres prototype *and* ≥1 genuinely unnoticed unenforced-rule/dangling-mechanism surfaced. KILL: zero marginal caught defect over one live gating month *and* the reflexive succinctness is cosmetic (a 20-line `WITH RECURSIVE` + script class-covers it).
- **E1b — ASP (defaults + minimal-repair + dead-exception hygiene)** on the real omega import graph. SUCCESS: bit-matches `check.mjs`'s band-conformance verdict, *additionally* finds dead exceptions in the 30-row ledger, and emits a ranked minimal-repair menu under budget. KILL: grounding blows past 60s/2GB even after projection, or the verdict diverges by an ASP-semantic surprise (unintended stable model).
- **E1c — Defeasible reasoning (defeat-under-contradiction, derived retraction, `suspect` as first-class third value)** on a 10k-fact dump. SUCCESS: grounds+solves under 2s and matches the maintainer oracle on ≥30 supersession/conflict cases including ≥5 multi-defeater cases SQL gets wrong or awkward. KILL: superlinear grounding past 5s (CI-unviable), or hand-written stratified `NOT EXISTS` views are judged *as clear* across the whole oracle (the semantic gap never cashed out).
- **E1d — Paraconsistent quarantine (Belnap `both`, contained contradiction across a derivation chain).** *Gated by an audit*, not assumed: does autoharn's real ledger ever produce a **multi-hop** verdict over conflictable inputs? SUCCESS: ≥1 historical verdict whose correctness depends on *containment* (not mere `NULL`-detection), where the classical control would have green-lit an unrelated release. KILL: every real contradiction is terminal — K3-`NULL` already class-covers it, `both` is dead weight.
- **E1e — Abduction (ranked minimal cause-set, `{abducibles} + #minimize`).** Shares the engine; run alongside E1b. SUCCESS: the maintainer-agreed minimal cause is among the co-optimal answers on ≥4/5 historical regressions. KILL: true cause absent in ≥2/5 *and* widening the abducible set makes every event return ≥4 explanations (no discriminating power).

**Shared ladder KILL:** grounding blow-up at real store size sinks any rung — a gate that times out audits nothing.

### E2 — SMT global-consistency of the registry (independent substrate, already firing in-env)

Z3/cvc5 over Pillar-1's Capability Registry: the whole schema as axioms, one `unsat` question, and a **minimal blame-core** as a machine-generated repair target — the one capability no `WHERE` clause produces. Sequenced after E1 because it faces a different Pillar (registry, not ledger) on a different engine; parallelizable in wall-clock but distinct in dependency.
**SUCCESS:** clean registry `sat`; all 50 mutant registries `unsat` with a minimal, defect-naming core in seconds; *and* ≥1 invariant is a genuine ∀-theorem (e.g. "no admissible edit can ever double-tag a class") that no view expresses.
**KILL:** `WITH RECURSIVE` class-covers all 50 mutants at equal clarity *and* every interesting invariant turns out existential/reachability-shaped (no universal guarantee); or realistic quantified invariants drive *both* Z3 and cvc5 to `unknown`/timeout — the verdict is unavailable when it matters.

### E3 — Description-Logic TBox reasoning (depends on E1 and E2)

DL is layered, not standalone: it owns the *static* TBox while ASP (E1) owns the non-monotone supersession chain — OWA monotonic DL cannot retract an entailment and a single contradiction explodes the ABox, so the ledger is explicitly *not* DL's. DL also must not duplicate E2's exclusivity check; it earns its slot **only** through the capability SMT and ASP lack: classification of *inferred* membership (routing-by-entailment).
**SUCCESS (K1):** on the real registry, ≥1 inferred-membership violation or entailed routing decision *actually occurs* — a tool double-kinded only by derivation, or a task routed to a tool as a theorem nobody wrote. SUCCESS deepens if a real entailed routing decision no human had recorded fires.
**KILL:** K1 empty — all membership is stored, never derived, so the inferred-membership cases never arise (elegant-but-inert); or K2 — the meta-sweep TBox cannot be authored without an axiom that mutates the entailment with no fixture catching it and no readable back-translation (false authority un-neutralizable here).

### E4 — Substructural consumption gate (fold linear + relevance into one CHR trial)

The linear and relevance trials are the same gate: one reading discharges at most one perf-claim (no contraction), no claim discharges without consuming a reading (no weakening). CHR multiset rewriting makes the wrong thing inexpressible without changing the connective. Cheap to run; **honestly near-ash** — the trial's own author shows a standing `claim_violations` view likely class-covers the flat case.
**SUCCESS:** a claim shape exists — multi-reading or partial-consumption — that the multiset semantics rejects *generically* but the standing SQL view can catch only by per-shape rewriting. Optional escalation: Maude coverability over the concurrent ADR-amendment lifecycle (run only if E5 finds real concurrency).
**KILL:** the single *unmodified* `claim_violations` view class-covers every weakening/contraction defect across all claim shapes with zero per-shape vigilance — then the logic is the *explanation* of the ledger's physics and SQL is the enforcement.

### E5 — Concurrency precondition (cheap finding; gates two expensive trials)

Modal Stage B (CTLK model-checking the write-API) and Temporal TLA+ (TLC over un-run interleavings) make the *same* bet: the frontier is quantification over states the system has not yet run. Both collapse to design-time documentation if the ledger is effectively single-writer-per-row. So one cheap audit gates both: **can ≥2 writers (two Claude sessions, ship-hook racing the coordinator) interleave on a shared row-key?**
- If **sequential**: both E5a (TLA+) and E5b (Modal Stage B) are ash *for the provable-frontier claim* — within-row CHECK constraints already cover it — and runtime-LTL is independently ash by **Kamp's theorem** (LTL-with-past is expressively first-order over the linear log; a `NOT EXISTS` self-join class-covers every stored-trace safety property). Both retire to design-time docs.
- If **concurrent**: run both. **SUCCESS:** TLC/MCMAS returns a reachable `dirty→confirmed`, resurrection, or pre-registration-violating append-sequence that no within-row CHECK and no present-extension `SELECT` can refute (the violating rows do not exist yet). A live MTL within-session timing obligation (perf-claim substantiation latency) SQL cannot phrase flips this to full phoenix. **KILL:** every counterexample corresponds to a row an SQL arm would already flag once it exists.

### E6 — Confidence-channel precondition + trial (gates ProbLog/SRL + Bayesian PPL)

The two probabilistic trials share one bet: the suspect→confirmed boundary should be a *stored, auditable* posterior, not a Python threshold in a maintainer's head. Both are gated by one audit: **does real perf history contain signal≈noise disputed claims and shared-latent-fact correlations?** This is a confidence *channel*, not a hard gate — lower priority for deductive maintenance, but a genuine extreme-auditability target, so it sits after the hard-gate spine.
**SUCCESS:** the marginal/posterior gate reproduces the maintainer's eventual verdict on ≥90% of a labelled back-set, is better-calibrated (Brier) than the fixed-threshold heuristic, overturns ≥1 historical verdict the maintainer ratifies as wrong (CI straddles 1.0), *and* beats a SQL `SUM` on ≥1 incident where a shared latent fact makes the naive sum double-count.
**KILL:** calibration parity with a one-line Welch t-test / fixed threshold in every real case *and* no incident ever exercises shared-fact correlation; or weights/priors cannot be sourced from cited readings and must be guessed — every marginal carries `[unsubstantiated]` and the number is decoration.

### E7 — ILP rule-factory (data-gated; last, because its corpus precondition may be unmet now)

Popper/Aleph induce the `_violations` *class predicate itself* from the ledger's labelled blessed/rejected history — Rule-4 compliance by construction, the safety net learning to write itself. It cannot run until the ledger holds **30+ clean labelled rows**; that data-availability precondition places it last. Its output is an ordinary runtime gate, so its value is concentrated entirely at authoring time (a rule factory, not a runtime engine).
**SUCCESS:** the induced rule recovers a human-written gate predicate on a held-out 20% split with zero false-negatives.
**KILL:** it cannot recover a rule a human already wrote correctly, or admits a labelled-good row in ≥2/5 cross-validation folds — synthesis buys nothing over human+SQL.

## Trustworthy LLM-authored formalization (the central problem, first-class)

Every trial above converges on the same five-part discipline. This is not per-logic scaffolding repeated fourteen times; it is **one reusable contract** that any LLM-authored encoding must satisfy before its green means anything. The encoding is treated as a Pillar-2 reading-with-provenance — a *measurement* that is presumptively decaying until audited — never as a settled theorem.

1. **Mutation fixtures (the primary instrument).** For every gate, store a known-bad fixture that *must* turn the relation red and a known-good fixture that *must* keep it green. Then auto-mutate the *encoding* (flip each `not`/`\+`, drop each integrity constraint, swap `<` for `≥`, `some`→`only`, `<=>`→kept-`\`, weight `0.9`→`0.09`, priority `T2>T`→`T2<T`) and assert every mutant flips a golden verdict. **A surviving mutant is a hole in the test suite, by construction** — the suite, not the logic, is then the defect. This directly kills the "confidently empty" / "confidently `unsat`" failure: a gate that cannot light up on its own mutant is a dead gate.

2. **Differential engines (two semantics, one verdict).** Run the same facts through two independent solvers — clingo *and* DLV; Z3 *and* cvc5; HermiT *and* ELK/Konclude; TLC *and* Apalache; NumPyro *and* PyMC; clingo *and* `s(CASP)` — and through one SQL reference arm *as a cross-check, never as the fallback*. Disagreement halts CI and is logged as a reading, never silently reconciled. Two engines agreeing is categorically stronger than one green check.

3. **Back-translation with provenance.** Each clause/axiom/weight auto-renders to one English sentence; the maintainer reviews the *English* against the registered ADR intent (Pillar-1 capability declaration). The encoding's authority is *conditioned on a human having read its meaning*. The `.lp`/`.tla`/`.py` source is itself a ledger entry under `{commit, tree, session_id}`, criterion-registered before its first verdict; a DIRTY tree never yields a confirmed verdict about its own encoding.

4. **Proof-carrying output.** Every fired gate ships its justification — Soufflé `--provenance`, `xclingo`/`s(CASP)` derivation tree, Z3 `unsat_core`, TLC counterexample trace, the CHR consumed-token trace, the ProbLog explaining-worlds. The gate emits *why*, stored as a replayable provenance object. A passing gate with no stored either-counterexample-or-coverage-report is itself suspect.

5. **The deflation-defect gate (the new, checkable class).** Reducible-instance retreat is now logged and machine-checkable. Two automated checks, both Rule-4 by class:
   - **Class-level-kill audit.** Scan every kill-condition for the shape "SQL caught instance/mutant X." That shape is *rejected* as a kill and logged as a deflation-defect candidate. A valid kill must assert *generic* coverage: "a single unmodified SQL artifact class-covers the entire defect family with zero per-shape vigilance, provably." The deflation defect is the meta-instance of the very Rule-4 violation autoharn polices in its gates — one constraint per case fails open at the next case.
   - **Metamorphic locality / generic-coverage probe.** For any logic whose kill rests on SQL equivalence, generate *unseen* instances of the defect class (a new claim shape, a new defeater chain, a new interleaving) and re-run the SQL arm with no edits. If the SQL arm requires a new clause to catch the new instance, the equivalence was instance-level and the kill is void.

**False authority as a measurable hypothesis (not a confident assertion).** The retracted synthesis declared the LLM "least reliable at formalization" with no probe. We replace the assertion with a falsifiable hypothesis and a metric:

> **H_fa:** LLM-authored encodings carry semantic defects at a rate that survives the scaffold and makes the green gate *less* reliable than its SQL baseline.

> **Metric:** the **mutation-escape rate** (fraction of injected known mis-encodings the fixture suite fails to catch) and the **differential-divergence rate on real data** (fraction of encodings where two independent engines disagree). Measured directly by planting known mis-encodings and counting detection — the same discipline a `*_violations` gate demands of any claim.

H_fa is **falsified** when the scaffold drives mutation-escape toward zero and back-translation review catches the residual — i.e. formalization defects are real but *caught*, exactly as compiler errors are real but caught. H_fa is **confirmed for a given logic** (and that logic retired) only when mis-encodings demonstrably survive the full scaffold at a rate exceeding the SQL baseline's error rate. Either way it is a number on the board, not an opinion.

## The frontier map

Each logic's current bet, and the *one* experiment that settles it — framed as how we find out, with honest ash where a trial earned it by genuine search.

| Logic | Current bet | The trial that settles it (how we FIND OUT) |
|---|---|---|
| **Datalog / deductive DB** | **Phoenix** (conditional, leaning strong) | E1a: does the reflexive meta-sweep, run live for one gating cycle, catch ≥1 unenforced rule a `find\|comm` script misses? Zero marginal catch over real data = ash. |
| **ASP (clingo/DLV)** | **Phoenix** for defeasible/repair gates; **ash** for flat count/presence gates (genuine — grounding is pure overhead there) | E1b: bit-match `check.mjs`, additionally find dead exceptions, ground under 60s/2GB on the real omega graph. |
| **Defeasible / argumentation** | **Phoenix** (leaning strong; undecided only on scale) | E1c: 10k-fact dump grounds <2s and beats SQL on ≥5 multi-defeater retractions. Superlinear blow-up = ash. |
| **Paraconsistent / many-valued** | **Undecided**, leaning phoenix | E1d: does real ledger history contain ≥1 *multi-hop* verdict whose correctness needs contradiction *containment*? All-terminal contradictions = ash (K3-`NULL` wins). |
| **Abductive reasoning** | **Phoenix** | E1e: maintainer-agreed minimal cause among co-optimal answers on ≥4/5 real regressions. |
| **SMT / classical FOL (Z3/cvc5)** | **Phoenix** (strong) for exclusivity/forced-mapping/global-consistency; **ash** for plain reachability (genuine — `WITH RECURSIVE` is cheaper and clearer) | E2: 50-mutant minimal-blame-core in seconds + ≥1 genuine ∀-theorem no view expresses. |
| **Description Logic / OWL** | **Phoenix** (narrow) for Pillar-1 TBox + meta-sweep; **ash** for the ledger (genuine — OWA monotonic DL cannot retract; ASP owns that layer) | E3/K1: does inferred-membership / routing-by-entailment *actually occur* on the real registry? |
| **Prolog / CLP(FD)** | **Phoenix** (narrow) for NAF-liveness, default-with-exception, abductive "what fact breaks this," proof-carrying gates; **ash** for plain transitive closure (genuine — SQL ties and is faster) | The differential-solver liveness run: Prolog and `WITH RECURSIVE` agree on every real store while Prolog emits a maintainer-validated derivation. Divergence traced to cut/ordering = ash. |
| **Linear / resource (CHR)** | **Phoenix** for the consumption discipline; **undecided** on the Maude coverability frontier | E4 + mutation suite: does a multi-reading/partial-consumption shape need per-shape SQL the multiset semantics handles generically? |
| **Relevance / substructural** | **Undecided**, honestly **near-ash** (the standing `claim_violations` view likely class-covers the flat double-spend/no-evidence family — earned by genuine search) | E4: find a claim shape the multiset rejects generically but the *unmodified* SQL view catches only per-shape. None found = ash. |
| **Temporal — TLA+** | **Phoenix** *iff* concurrent writers exist | E5/E5a: TLC surfaces a reachable illegal transition under ≥2 interleaved writers that within-row CHECKs miss. Provably-sequential protocol = ash. |
| **Temporal — runtime LTL** | **Ash** by genuine search (Kamp's theorem: expressively first-order over the single-writer log; SQL class-covers stored-trace safety) — *unless* an MTL within-session timing obligation SQL cannot phrase becomes a live gate | E5: the same concurrency/timing audit; an MTL `◇≤Δ` gate flips it back to phoenix. |
| **Modal / epistemic** | **Undecided**, leaning narrow-phoenix; Stage A (factivity) **ash by genuine search** (readability, not expressiveness — ties SQL); the bet rides entirely on Stage B | E5/E5b: CTLK model-check of the write-API returns a pre-reg/false-authority counterexample append-sequence no present-extension `SELECT` can refute. |
| **Probabilistic logic / SRL (ProbLog/MLN)** | **Undecided**, leaning cautious-phoenix in one corner (shared-latent #P correlation) | E6: calibration back-test beats fixed-threshold (Brier) + ≥1 shared-fact case where SQL `SUM` double-counts. Parity + no correlation = ash. |
| **Probabilistic programming / Bayesian (NumPyro)** | **Undecided**, leaning narrow-phoenix | E6: posterior over ≥10 disputed noisy claims overturns ≥1 ratified-wrong verdict + beats ratio-of-means on attribution. Always-redundant-with-t-test = ash. |
| **ILP (Popper/Aleph)** | **Undecided**, leaning cautious-phoenix as a build-time rule factory; **data-gated** | E7: induced rule recovers a correct human-written gate on a held-out split. Can't recover it = ash. |

## Honest risks (as hypotheses we will measure)

- **R1 — Grounding blow-up at real scale.** *Hypothesis:* the omega import graph / 10k-fact ledger pushes clingo grounding past 60s/2GB even after projection, making the whole E1 ladder CI-unviable. *Metric:* wall-clock + RSS on the real dump; the kill-line is pre-stated. This is the single most likely sinker of the highest-leverage cluster, so E1's rungs are ordered to hit it early (E1b/E1c are the scale stress).
- **R2 — H_fa confirmed (false authority is real and uncatchable for some logic).** *Hypothesis:* for the operator-invisible logics (linear `!` vs plain, modal accessibility-relation axioms, ProbLog weight polarity), mis-encodings survive the mutation suite at a rate exceeding the SQL baseline. *Metric:* mutation-escape rate per logic. Measured, not assumed; a logic where it stays high is retired *on that number*.
- **R3 — Empty frontier (the gap is real but never bites).** *Hypothesis:* the expressiveness gaps are genuine in principle but the *incidence* is zero on real data — no multi-hop contradiction (paraconsistent), no inferred membership (DL), no concurrent interleaving (temporal/modal), no shared-latent correlation (probabilistic). *Metric:* the per-trial incidence audit. This is the honest dominant ash-path: several logics are non-redundant in theory and inert in practice, and only the corpus audit tells us which.
- **R4 — Differential disagreement on real data with no ground truth.** *Hypothesis:* two engines diverge on a real store and *neither* is obviously right (skeptical vs credulous, an SMT `unknown`, an MCMC non-convergence). *Metric:* differential-divergence rate; each divergence is a logged reading requiring adjudication, and a high rate means the verdict is not yet trustworthy regardless of greenness.
- **R5 — The scaffold itself is the cost.** *Hypothesis:* producing a trustworthy gate requires so much defensive scaffolding (mode/termination guards, occurs-check, prior-sensitivity sweeps) that maintainer review time per gate exceeds the SQL baseline by ≥2×. *Metric:* review-minutes per gate vs SQL baseline. If the audit burden exceeds the audit benefit, the logic loses on its own objective function — auditability — not on familiarity.

## Open questions (genuine forks only the maintainer can decide)

1. **Is autoharn's write-API actually concurrent?** Whether two Claude sessions or a ship-hook can interleave writes on a shared row-key is a *design fact only the maintainer knows or chooses*. It single-handedly decides E5: concurrent ⇒ Modal Stage B and TLA+ are live frontier candidates; sequential-by-construction ⇒ both are design-time documentation and runtime-LTL is ash by Kamp. The program cannot settle this by experiment — it is an architecture decision.
2. **Does the maintainer want the ledger to *carry* unresolved contradiction, or *forbid* it at write time?** If contradictions are allowed to persist mid-supersession (Belnap `both`, paraconsistent quarantine), E1d is load-bearing. If the write discipline forbids a contradictory pair from ever coexisting, K3-`NULL` suffices and paraconsistency is inert. This is a policy fork, not a measurement.
3. **What is the labelling budget for ILP?** E7 needs 30+ maintainer-labelled blessed/rejected rows. Whether to invest in producing that corpus — and whether induced gates may ever enter CI as `provisional` — is a resourcing-and-trust decision only the maintainer can authorize.
4. **Where is the auditability/latency frontier set?** Several phoenix candidates trade CI wall-clock for proof-carrying justification. The acceptable per-gate budget (the 2s line, the 60s grounding line) is a maintainer-set threshold; moving it reclassifies trials at the margin.
5. **Confidence channel: gate or advisory?** If the suspect→confirmed posterior (E6) is allowed to *block* promotion, it is a hard gate and must clear the calibration kill. If it is advisory-only (a stored number an auditor may challenge), the bar is lower but so is the load-bearing claim. Which one autoharn wants is a governance fork, not an empirical one.

---
*Verbatim output of the hardening workflow (run `wv0g2zc25`, claude-opus-4-8[1m]), 2026-06-27; editorial-correction header by the assistant.*
