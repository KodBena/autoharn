# D — Coverage matrix & adversarial completeness critic

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](README.md).

**Key for this document.** Full reference → [KEY.md](KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [TRIG](KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [DEGRADE](KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [COMMIT](KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [PROV](KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [STRUCT](KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [COHERE](KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [TRACE](KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

## (1) Obligation × Formal-System Assignment Matrix

Confidence legend: **H** = high (semantics match the failure mode, tool runs today), **MH** = medium-high (good match, one fragility), **M** = medium (real but composed or input-fragile), **S** = speculative/frontier. Primary discharger(s) in **bold**; the assignment rule is *why this one for this obligation*, never "which logic wins."

| # | Obligation | Primary discharger(s) | Conf | Assignment rule (semantics→failure-mode) | Secondary / compositional |
|---|---|---|---|---|---|
| 1 | **[INV](KEY.md#inv)** | **HOL/proof assistants** (unbounded), **TLA+/TLC**, **LTL-CTL/NuSMV**, **μ-calculus/mCRL2**, **SMT/Z3** (inductive), **modal substrate** | H | "□ over all reachable states" = ν-fixpoint / inductive VC; one lethal tick is one falsifying world | SAT/CP (bounded BMC); MTL/STL (timed/margin part) |
| 2 | **[PROG](KEY.md#prog)** | **MTL/STL** (deadline+robustness), **LTL/TLA+/μ-calculus** (liveness/fairness) | MH | metric ◇[a,b] is the deadline operator; lasso-detection finds the hang | *WCET itself under-tooled — see gap* |
| 3 | **[TRIG](KEY.md#trig)** | **I/O & defeasible deontic logic**, **Default logic**, **MTL/STL** (metric detachment) | MH | conditional norm `O(act\|trigger)` = detachment locus; degraded-sensing = justification failing open | STIT (agentive detachment); Prolog |
| 4 | **[DEGRADE](KEY.md#degrade)** | **Dyadic/CTD deontic (Carmo-Jones)**, **STIT (Horty dominance)**, **MTL/STL** (FTTI) | MH | CTD logics are the *only* family giving "already non-compliant" a model-theoretic meaning | μ-calculus (reparation-timing spine) |
| 5 | **[AUTH](KEY.md#auth)** | **ASP/clingo** (closed-world), **Default/Circumscription**, **defeasible-deontic (s(CASP)/SPINdle)** (norm precedence) | H | permission closure = `Ab`-minimization / CWA; derogation = prioritized defaults | Prolog (CWA); argumentation (preference); SMT (resolved-gate totality) |
| 6 | **[ATTR](KEY.md#attr)** | **STIT (dstit)**, **Halpern-Pearl actual causation (HP2SAT)** | M | "saw-to-it AND could-have-done-otherwise" = guarantee-across-cell + avoidability witness | Epistemic (knew-at-time). *Input-fragile — see ash* |
| 7 | **[COMMIT](KEY.md#commit)** | **Substructural/linear (VeriFast)**, **DEL** (handoff knowledge), **directed deontic** | M | linear resource = create-once/discharge-once; lost token = type error | Allen/HS intervals. *Thinnest obligation — see gap* |
| 8 | **[PROV](KEY.md#prov)** | **Datalog** (least-fixpoint groundedness), **Justification Logic**, **ProbLog** (weighted), **argumentation** (support tree) | H | "in model iff finite derivation to EDB" = groundedness by construction | Prolog proof tree; Truthmaker (frontier) |
| 9 | **[REVISE](KEY.md#revise)** | **AGM belief revision (TweetyProject)**, **Default logic**, **argumentation** | H | contraction removes support so premise can't re-derive; non-monotonic re-adjudication | Datalog (recompute) |
| 10 | **[CONSIST](KEY.md#consist)** | **Paraconsistent FDE/LP**, **Dung/ASPIC+ argumentation** | H | designated-value / admissibility makes ex-falso structurally impossible; conflict localized | SAT-MUS (detect+localize); AGM (restore); ASP (detect) |
| 11 | **[CALIB](KEY.md#calib)** | **Probabilistic programming (NumPyro/Stan)**, **ProbLog** | H | posterior = calibrated interval; SBC is the mechanical calibration gate | SMT/HOL (exact-claim oracle); Provability Logic (anti-false-authority *topology* only) |
| 12 | **[CLASS](KEY.md#class)** | **Description Logic** (disjoint+covering), **ASP**, **SAT/CP**, **SMT** | H | MECE = at-least-one ∧ at-most-one over full domain; misfit→UNSAT/`unknown` | Many-valued (gap/glut cells) |
| 13 | **[STRUCT](KEY.md#struct)** | **Substructural/separation (VeriFast/Iris)**, **HOL/dependent types**, **SMT/bitvector** | H | make defect unrepresentable: move-once, exact wraparound, typed absence | Free logic (definedness `E!`) |
| 14 | **[COHERE](KEY.md#cohere)** | **SMT** (equivalence), **separation logic** (single-writer), **Dependence logic** (team functional-dep), **DL hasKey** | H | `x↦v * x↦w` disjointness-impossible; `=(key,val)` over all writers | SAT/CP; TLA+ |
| 15 | **[TRACE](KEY.md#trace)** | **Datalog** (reachability/coverage closure), **ILP** (latent-spec recovery + diff) | H | hazard→…→test links are transitive closure; orphan/untraced = one recursive rule | SAT (test-vector gen / infeasibility) |
| 16 | **[INDEP](KEY.md#indep)** | **HOL** (kernel⊥producer), **SMT** (cvc5 cross-check), **Provability Logic** (Löb anti-self-cert) | H | de Bruijn criterion: production untrusted, checking by small diverse kernel | differential tooling across all sections. *Partly organizational, not semantic* |
| 17 | **[RECORD](KEY.md#record)** | **Justification Logic** (replayable witness), **Allen/HS + MTL** (happens-before/skew), **TLA+** (design ordering) | MH | witness term = reconstructable rationale; `meets`/`before` = approval-before-action | s(CASP)/argumentation justification trees. *Cryptographic/distributed half missing — see gap* |

## (2) GAPS — obligations with no strong discharger

- **[COMMIT](KEY.md#commit) is the weakest-covered obligation in the taxonomy.** No surveyed system tracks the *full* commitment lifecycle (created→active→discharged→delegated→cancelled→violated, with *creditor entitlement*) as a first-class object. Linear logic nails single-discharge (no double-count, no leak); DEL nails the handoff knowledge transfer; directed deontic nails the owed-to relation — but the maintainer must *compose three formalisms by hand*, and that composition is untooled and unqualified. The matched dedicated formalism (**Singh's social-commitment protocols / Telang-Singh business-protocol logic** and **multiparty session types**) is entirely absent from the roster (see §4).

- **WCET / hard real-time resource bounds (the back half of [PROG](KEY.md#prog)).** STL *monitors* a trace's timing and reports margin; it does not *bound* worst-case execution time. The taxonomy explicitly demands "WCET and resource bounds established," and nothing in the 27 discharges it — that is timed-automata model checking (UPPAAL) and classical schedulability analysis (RMA/response-time), both missing.

- **The cryptographic/distributed half of [RECORD](KEY.md#record).** The logics give *design-level* happens-before (TLA+, Allen/HS). The actual obligation — a *tamper-evident, single-source-of-truth* trail with *provable* happens-before across async writes and clock skew (the literal NYSE example) — is a distributed-systems + cryptography problem (Lamport/vector clocks, hash-chains/Merkle, verifiable logs). No formal-logic family in the roster owns it.

- **[ATTR](KEY.md#attr) is covered but not *qualifiable*.** Both STIT and Halpern-Pearl require a modeled choice/causal structure that the LLM authors; if the available alternatives or the structural equations cannot be recovered from audit data without hand-authored fiction, the verdict is unfalsifiable theater. Coverage exists; trustworthy *inputs* do not. This is a residual-risk gap, not a coverage gap — but at these stakes it is load-bearing.

## (3) OVER-COVERAGE (healthy — assignment, not bake-off)

- **[INV](KEY.md#inv) (7 dischargers):** assign by guarantee strength and what is modeled — SAT-BMC (bounded bug-finder) < TLC/NuSMV (exhaustive over finite instance) < μ-calculus (infinite-behaviour fixpoint) < HOL (unbounded, all parameter sizes). SMT for inductive-step over rich arithmetic state; modal substrate as the shared ST→Z3 channel.
- **[AUTH](KEY.md#auth):** pure permission *closure* → ASP/circumscription; *norm precedence/derogation* → defeasible-deontic; both want the same `.lp`/rule source, differentially cross-checked.
- **[PROV](KEY.md#prov):** flat lineage → Datalog why-provenance; *composable/first-class* evidence (evidence-of-evidence, cross-channel corroboration) → Justification Logic; *weighted* → ProbLog; *defeasible* → argumentation.
- **[CLASS](KEY.md#class):** flat MECE → SAT/ASP/SMT (cheap, exhaustive); *multi-axiom subsumption interactions a switch-statement can't anticipate* + identity closure → Description Logic.
- **[CONSIST](KEY.md#consist):** want *containment while still reasoning* → paraconsistent/argumentation; want *minimal restoration, pick-a-side-and-log* → AGM; want *detection+localization only* → SAT-MUS/ASP.
None of these is a contest; each split is principled by the obligation's exact failure mode.

## (4) ADVERSARIAL — what the roster and taxonomy MISSED

### Formal SYSTEMS missing (blunt, ranked by load-bearing impact)

1. **Abstract interpretation / sound static analysis (Astrée, abstract domains).** This is the single most damaging omission. Every model-checking and TLA+ section confesses the same kill-condition — "green-on-the-model laundered into green-on-the-system." Abstract interpretation gives a *sound over-approximation guarantee on the actual source code* (Astrée proved absence-of-runtime-errors on Airbus A380 flight control). It directly discharges the artifact-fidelity gap the rest of the survey can only flag. Missing entirely.

2. **Runtime verification as a discipline (monitor synthesis, RV-LTL, monitorability).** RTAMT appears as one STL tool, but RV as the *bridge between verified-model and conforming-artifact* — synthesize a monitor from the spec, run it against the live system — is the methodological answer to nearly every section's "the model is on trial" ash. It deserves first-class treatment, not a passing mention.

3. **Differential dynamic logic (dL) / hybrid-systems verification (KeYmaera X).** The dam, the control loops, NASA GNC are *cyber-physical*: discrete control over *continuous* ODE dynamics. Platzer's dL is the matched formalism for an invariant over continuous reservoir dynamics — the survey models "level : 0..100" as an integer and then admits in the kill-condition that this says nothing about the real continuous process. dL closes exactly that gap and is absent.

4. **Probabilistic model checking (PCTL/CSL; PRISM, Storm).** "Probability of reaching an unsafe state within T < ε" over Markov/MDP models sits between qualitative temporal logic and Bayesian estimation, and is the matched tool for quantitative reliability/safety budgets ([DEGRADE](KEY.md#degrade)'s FTTI reliability, CALIB-over-temporal). Missing.

5. **Commitment protocols + session/behavioral types (Singh; multiparty session types, Honda-Yoshida).** The dedicated home for [COMMIT](KEY.md#commit) — the taxonomy's thinnest obligation. Session types make "a protocol with a tracked lifecycle and handoff" a *typing discipline* that rejects orphaned/dropped legs at compile time.

6. **Auto-active program verifiers as their own tier (Dafny, F*, SPARK/Ada, Why3).** The realistic industrial sweet spot between raw SMT and full HOL — SPARK is *actually deployed* in avionics/rail. The HOL section treats them only as Z3 clients; they are the most likely git-clone-runnable answer for [STRUCT](KEY.md#struct)/INV-on-real-code and deserve their own section.

7. **Reactive synthesis & strategy logic (ATL, SL, GR(1)).** Building a *correct-by-construction controller* rather than checking one — and multi-agent adversarial authorization. MCMAS is mentioned under epistemic; the synthesis dimension is absent.

### OBLIGATIONS the taxonomy missed (blunt)

1. **CONFIDENTIALITY / information-flow / non-interference.** The taxonomy is entirely safety/liveness/authorization/provenance — and has **no obligation for secrecy**: that PHI, material-non-public-information, or Fed position data does not flow to a lower clearance. [AUTH](KEY.md#auth) governs *may I act*; this governs *what may flow / who may come to know*. At Fed/NYSE/oncology stakes this is co-equal with safety and is glaringly absent. Formal home: security type systems, non-interference, epistemic logic of secrecy.

2. **HYPERPROPERTIES (relational / 2-safety) — the deeper structural miss.** Every obligation in the taxonomy is a *trace property* (a predicate on single executions). Non-interference, observational determinism, and "redundant channels given identical inputs produce identical safety outputs" are **hyperproperties** (Clarkson-Schneider) — relations over *sets* of traces, requiring HyperLTL/MCHyper. [INDEP](KEY.md#indep) gestures at channel diversity but never names that genuine diversity is a 2-safety property no single-trace checker can express.

3. **The SPECIFICATION-ADEQUACY meta-obligation.** This is the most important missing obligation given the mission's own obsession. Every section's kill-condition is some form of "a wrong/vacuous spec is proved correct." Yet no obligation names *the spec set itself being complete, non-vacuous, and adequate* — vacuity detection, spec-mutation, requirement-completeness. [TRACE](KEY.md#trace) covers requirement→artifact *linkage* and [INDEP](KEY.md#indep) covers verifier *independence*, but neither asks "is the ratified requirement set itself right and non-trivial?" The HOL section's "≥10% vacuous-but-passing proofs" kill belongs to an obligation that does not exist in the taxonomy.

4. **FAIRNESS / non-discrimination across protected groups.** At "hundreds of millions of lives," AI-assisted sortation (oncology triage, credit, Fed policy) carries an equity obligation distinct from [CLASS](KEY.md#class) (honest sortation of *one* entity): equitable sortation *across groups* (counterfactual fairness, statistical parity). The causal section has the machinery (Kusner counterfactual fairness); no obligation names it.

5. **REVERSIBILITY / compensability (distinct from [DEGRADE](KEY.md#degrade)).** [DEGRADE](KEY.md#degrade) enters a defined sub-ideal state; this is the separate duty that every committed effect has a defined *compensating/undo* action (saga compensation, transactional rollback). Herstatt is cited under [COMMIT](KEY.md#commit) but the general obligation is unnamed.

6. **BOUNDED RESOURCE CONSUMPTION / termination (distinct from [PROG](KEY.md#prog)/STRUCT).** Memory bounds, no unbounded allocation/recursion, cost/gas bounds, no slow resource leak — termination proofs and amortized resource analysis (RAML). Partially under [STRUCT](KEY.md#struct)/PROG; deserves naming.

(Lesser: numerical stability/conditioning as its own obligation; availability/partition-tolerance of the record-keeper itself.)

## (5) HONEST ASH FLAGS — genuinely non-leverageable for THIS purpose, by argument

- **Provability Logic (GL/Löb) as a logic.** The section concedes it: GL contributes *nothing* to whether any check is correct, and its one load-bearing payoff — anti-self-certification — reduces to an **acyclicity check on the assurance graph**, a one-line ASP/Datalog constraint. The *principle* (no producer certifies itself) is load-bearing; GL's modal axiomatics are pure edification. Ash as tooling.

- **Justification Logic (Artemov).** Its own kill-condition is likely met on the autoharn corpus: Datalog why-provenance delivers checkable, forgery-resistant, retraction-respecting provenance chains with equal strength. JL survives *only* if a production case requires object-level reasoning *about* justification terms (evidence-of-evidence as a first-class assertion, `s+t` cross-channel corroboration as an object). Absent a demonstrated such case, [PROV](KEY.md#prov) goes to Datalog and JL is ash.

- **Truthmaker semantics & metaphysical grounding (frontier).** Explicitly speculative, no tool, and the claimed leverage (exact relevance separating real warrant from confabulation) has a stated kill-condition that it buys nothing over classical-entailment + citation-check. Grounding-as-well-foundedness is just graph acyclicity (same collapse as GL). High ash risk; honest-ash is the likely result.

- **Fuzzy / t-norm logic for [CALIB](KEY.md#calib).** Truth-functional t-norm conjunction is *not* probability; propagating graded fuzzy degrees as calibrated confidences is [CALIB](KEY.md#calib)'s own failure mode reborn one level up. Ash for [CALIB](KEY.md#calib) (which belongs to probabilistic programming); fuzzy's only legitimate role is *vagueness representation*, not confidence propagation.

- **Dialetheism qua metaphysics.** FDE's four-valued *bookkeeping* (Both/Neither as typed conflict/gap markers) is the engineering leverage for [CONSIST](KEY.md#consist); the dialetheist commitment that some contradictions are *true* buys nothing operationally. The philosophy is ash; the value-lattice survives.

- **MLN/PSL dedicated tooling (pracmln, Tuffy).** Verified unmaintained — do not stand a life-critical pipeline on them. The *semantics* survives by encoding into clingo weak constraints; the tools are dead. Tooling ash, semantics re-homed.

- **ILP as a guarantee.** Sound over the sample, conjectural over the domain. Ash anywhere a *guarantee* is owed ([INV](KEY.md#inv)/PROG/AUTH-enforcement); leverageable only as candidate-generator and differential-diff oracle, with mandatory hand-off to Z3/TLC and a mandatory example-provenance≠artifact audit (else the "independent" oracle is common-cause theater).

- **Conditional/at-risk (not flat ash, but flag the residual):**
  - **Description Logic** *without* disjointness/covering/hasKey collapses to enum+assert — pure encoding tax; leverage is narrow (multi-axiom subsumption interactions + identity closure).
  - **DEL/epistemic** for any "handoff" that is really one source-of-truth read by one party is ceremony already covered by [COHERE](KEY.md#cohere)/RECORD; survives only for genuine information-asymmetric multi-agent structure.
  - **STIT / Halpern-Pearl [ATTR](KEY.md#attr)** is unfalsifiable theater wherever the choice cells or structural equations cannot be reconstructed from audit data without authored fiction — the LLM-authored model is the attack surface, and the mission's own discipline forbids trusting a producer's self-authored structure.

**Bottom line for the maintainer:** the survey is strongly covered on the temporal-safety spine ([INV](KEY.md#inv)/PROG), the closure-and-norm spine ([AUTH](KEY.md#auth)/TRIG/DEGRADE), and the evidence spine ([PROV](KEY.md#prov)/REVISE/CONSIST/CALIB). It is thin on [COMMIT](KEY.md#commit), fragile-by-input on [ATTR](KEY.md#attr), and structurally incomplete in three places that the mission's *own* stakes make non-negotiable: **information-flow confidentiality**, **the specification-adequacy meta-obligation**, and **the artifact-fidelity bridge (abstract interpretation + runtime verification)** that every section currently can only confess it lacks.


---
*Cross-cut — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
