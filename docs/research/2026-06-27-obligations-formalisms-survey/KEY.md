# KEY — abbreviations, tiers & tools for the survey

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](README.md).

Every obligation code, guarantee/cost tier, and tool name used across this survey, defined in one place. Obligation codes are linked at every occurrence in the documents; this is the destination.

## Obligation codes

_The responsibilities the system must guarantee (the rows of the assignment). Full definition + failure mode + life-critical example for codes 1–17 in [01-obligation-taxonomy.md](01-obligation-taxonomy.md)._

<a id="inv"></a>**INV** — *Safety-Invariant Maintenance.* an "always"/barrier property holds in every reachable state; no silent excursion. ([full def](01-obligation-taxonomy.md#inv))

<a id="prog"></a>**PROG** — *Liveness & Real-Time Progress.* required events eventually occur within deadline; no deadlock or correct-but-late action. ([full def](01-obligation-taxonomy.md#prog))

<a id="trig"></a>**TRIG** — *Conditional Activation.* a triggered duty fires exactly when (and only when) its precondition holds. ([full def](01-obligation-taxonomy.md#trig))

<a id="degrade"></a>**DEGRADE** — *Contrary-to-Duty Reparation.* once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour. ([full def](01-obligation-taxonomy.md#degrade))

<a id="auth"></a>**AUTH** — *Action Authorization & Norm Precedence.* every effect is gated by an explicit permission; closure + norm priority resolve deterministically. ([full def](01-obligation-taxonomy.md#auth))

<a id="attr"></a>**ATTR** — *Agency Attribution.* every change bound to an identified agent who saw-to-it and could-have-done-otherwise. ([full def](01-obligation-taxonomy.md#attr))

<a id="commit"></a>**COMMIT** — *Directed Commitment & Handoff.* an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff. ([full def](01-obligation-taxonomy.md#commit))

<a id="prov"></a>**PROV** — *Claim Provenance & Groundedness.* every claim resolves via a finite replayable chain to primary evidence; no free-floating fact. ([full def](01-obligation-taxonomy.md#prov))

<a id="revise"></a>**REVISE** — *Belief Revision & Retraction.* retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational. ([full def](01-obligation-taxonomy.md#revise))

<a id="consist"></a>**CONSIST** — *Consistency & Contradiction Containment.* contradictions are quarantined; no ex-falso, no silent side-picking. ([full def](01-obligation-taxonomy.md#consist))

<a id="calib"></a>**CALIB** — *Substantiated & Calibrated Claims.* each claim backed by a reproducible artifact at strength matched to its kind; honest confidence. ([full def](01-obligation-taxonomy.md#calib))

<a id="class"></a>**CLASS** — *Honest Sharp Classification.* a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced. ([full def](01-obligation-taxonomy.md#class))

<a id="struct"></a>**STRUCT** — *Structural Soundness by Construction.* defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched. ([full def](01-obligation-taxonomy.md#struct))

<a id="cohere"></a>**COHERE** — *Single-Authority / Single-Writer Coherence.* one authoritative definition per fact; one owner per mutable state; references resolve to one correct target. ([full def](01-obligation-taxonomy.md#cohere))

<a id="trace"></a>**TRACE** — *Traceability, Coverage & Change-Impact.* hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact. ([full def](01-obligation-taxonomy.md#trace))

<a id="indep"></a>**INDEP** — *Independent Adjudication & Tool Qualification.* load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM). ([full def](01-obligation-taxonomy.md#indep))

<a id="record"></a>**RECORD** — *Auditable Decision Record & Ordering.* a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action. ([full def](01-obligation-taxonomy.md#record))

<a id="spec-adeq"></a>**SPEC-ADEQ** — *Specification Adequacy (added).* the requirement set itself is complete, non-vacuous, adequate — a wrong/vacuous spec must not be "proved correct". (added in the synthesis)

<a id="confid"></a>**CONFID** — *Confidentiality / Non-interference (added).* protected data (PHI/MNPI/positions) must not flow to lower clearance — a 2-safety hyperproperty over trace pairs. (added in the synthesis)

## Guarantee-strength tiers (how strong is the guarantee?)

**5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible

## Automation / cost tiers (how do we run it?)

**T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host

## Qualification gates (QUAL-1 … QUAL-7)

The discipline that makes an LLM-authored encoding trustworthy enough to gate at life-critical stakes (differential solvers, mutation/golden fixtures, vacuity & spec-mutation, requirement-completeness, back-translation, conformance via abstract interpretation + runtime verification). Full list and definitions: [C-encoding-qualification.md](C-encoding-qualification.md).

## Tool index

| tool | what it is | cost |
|---|---|---|
| **Z3** | SMT solver (Microsoft) — FOL + theories; the local default | T0 |
| **cvc5** | SMT solver — used as a differential cross-check against Z3 | T1 |
| **clingo / gringo** | Answer-Set Programming solver + grounder (Potassco) | T0 |
| **s(CASP)** | goal-directed ASP with justification trees (SWI-Prolog pack) | T1 |
| **SWI-Prolog** | Prolog system; CLP(FD), tabling, library(chr) | T0 |
| **OR-Tools CP-SAT** | constraint / SAT solver (Google) | T0 |
| **PostgreSQL (WITH RECURSIVE)** | relational DB; recursive queries ≈ Datalog | T0 |
| **TLC** | explicit-state model checker for TLA+ specifications | T1 |
| **NuSMV / nuXmv** | symbolic LTL/CTL model checkers (nuXmv adds infinite-state) | T2 |
| **mCRL2** | process-algebra toolset; modal μ-calculus model checking via parity games | T2 |
| **UPPAAL** | timed-automata model checker (real-time / WCET) | T2 |
| **RTAMT** | Python library for Signal Temporal Logic (STL) runtime monitoring | T1 |
| **SPINdle** | defeasible-logic reasoner (Java) | T1 |
| **HP2SAT** | Halpern–Pearl actual-causality checker via SAT (Java lib) | T1 |
| **VeriFast** | separation-logic verifier for C / Java | T2 |
| **Iris** | higher-order concurrent separation logic (mechanised in Coq) | T2 |
| **SMCDEL** | symbolic model checker for Dynamic Epistemic Logic | T2 |
| **Tweety** | Java libraries for logical AI (argumentation, AGM belief revision, …) | T1 |
| **µ-toksia** | abstract-argumentation (Dung AF) solver | T1 |
| **ProbLog** | probabilistic logic programming (Python; ≤3.12) | T1 |
| **NumPyro / Stan / PyMC** | probabilistic programming / Bayesian inference | T0/T1 |
| **ArviZ** | Bayesian diagnostics — calibration (SBC), LOO/WAIC | T1 |
| **HermiT / ELK / Pellet** | OWL description-logic reasoners | T1 |
| **ROBOT** | OWL ontology tooling / automation | T1 |
| **Coq / Lean / Isabelle** | interactive proof assistants (HOL / dependent types) | T2 |
| **Astrée** | sound abstract-interpretation static analyzer (commercial) | — |
| **LoTREC / MetTeL** | generic modal/tableau prover generators | T2 |

---
*Survey key — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*