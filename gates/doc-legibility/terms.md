# terms — the doc-legibility glossary

Persistent, hand-authored definitions for the acronyms and jargon-codes used in the scoped docs
(the obligations×formalisms survey + `docs/ARCHITECTURE.md`). This file is a **definition surface**
for [`gates/doc-legibility/check.py`](check.py): a token bolded `**LIKE-THIS**` on any line below
counts as *defined everywhere in scope*. One token, one line, `**TOKEN** — one-line definition.`

An entry here is a **claim that the term is real jargon and this is its correct meaning** — so the
definitions are checked, not guessed. A token that is genuinely common knowledge or a proper noun
(a tool, conference, journal, org, license) does **not** belong here; it goes in
[`allowlist.txt`](allowlist.txt). See [`README.md`](README.md) for the define-vs-allowlist rule.

> Sibling surfaces (also authoritative): the survey's **[KEY.md](../../research/obligations-formalisms-survey/KEY.md)**
> (obligation codes, tiers, tool index) and the root **[GLOSSARY.md](../../GLOSSARY.md)** (autoharn's coined vocabulary).

---

## Logic & formal methods — systems and operators

**LLM** — Large Language Model.
**MECE** — Mutually Exclusive, Collectively Exhaustive (a partition with no overlap and no gap).
**ASP** — Answer Set Programming (stable-model logic programming; clingo/gringo).
**ASPIC** — ASPIC+, a framework for structured argumentation with strict/defeasible rules.
**DeLP** — Defeasible Logic Programming.
**ABA** — Assumption-Based Argumentation.
**AF** — (abstract) Argumentation Framework, Dung's attack-graph semantics.
**AGM** — Alchourrón–Gärdenfors–Makinson, the standard rationality postulates for belief revision.
**DP** — Darwiche–Pearl, the postulates for *iterated* belief revision.
**AEL** — Autoepistemic Logic (nonmonotonic logic of self-belief).
**OCF** — Ordinal Conditional Function, Spohn's ranking function for graded belief/revision.
**DDL** — Dynamic Doxastic Logic (modal logic of belief change).
**SMT** — Satisfiability Modulo Theories (SAT plus theories like arithmetic; Z3/cvc5).
**SAT** — Boolean satisfiability: is there an assignment making a propositional formula true.
**UNSAT** — unsatisfiable: a SAT/SMT instance with no satisfying assignment (a refutation/proof).
**FOL** — First-Order Logic.
**HOL** — Higher-Order Logic (quantification over functions/predicates; Coq/Lean/Isabelle).
**CIC** — Calculus of Inductive Constructions, the type theory underlying Coq/Rocq.
**LTL** — Linear Temporal Logic (properties of a single linear execution; `□`, `◇`, `U`).
**CTL** — Computation Tree Logic (branching-time temporal logic; path quantifiers `A`/`E`).
**CTLK** — CTL extended with epistemic (Knowledge) operators.
**HyperLTL** — LTL over *sets* of traces, for hyperproperties (e.g. non-interference).
**TLA** — Temporal Logic of Actions (Lamport; the TLA+ specification language, model-checked by TLC).
**MTL** — Metric Temporal Logic (real-time temporal logic with timing bounds).
**STL** — Signal Temporal Logic (MTL over real-valued signals; robustness semantics).
**HS** — Halpern–Shoham logic of time intervals (the 13 Allen relations).
**DL** — Description Logic (the decidable fragments behind OWL; concepts, roles, individuals).
**ABox** — assertional box: the individual/instance assertions of a description-logic knowledge base.
**TBox** — terminological box: the concept/role axioms (the schema) of a DL knowledge base.
**EL** — the EL/EL++ family, a tractable (PTIME) description-logic profile.
**SROIQ** — the description logic underpinning OWL 2 DL.
**SROIQV** — SROIQ extended with extra constructs (here, the survey's temporal/extended variant).
**OWL** — Web Ontology Language (W3C ontology language built on description logic).
**KB** — Knowledge Base.
**KR** — Knowledge Representation (and reasoning).
**CWA** — Closed-World Assumption (unstated facts are false).
**OWA** — Open-World Assumption (unstated facts are unknown, not false).
**SDL** — Standard Deontic Logic (the modal logic KD of obligation/permission).
**KD** — the deontic-flavoured modal system K + axiom D (`□φ → ◇φ`).
**STIT** — "Sees To It That", the modal logic of agency / what an agent brings about.
**GL** — Gödel–Löb provability logic (the modal logic of formal provability; `□` = "is provable").
**G3KGL** — a G3-style (contraction-free) sequent calculus for the provability logic GL.
**PDL** — Propositional Dynamic Logic (modal logic of programs/actions).
**DEL** — Dynamic Epistemic Logic (knowledge change under announcements/actions).
**PAL** — Public Announcement Logic (the announcement fragment of DEL).
**JL** — Justification Logic (modal logic with explicit proof terms / evidence).
**LP** — Logic of Proofs (Artemov's core justification logic); also Priest's Logic of Paradox in the paraconsistent sections.
**FDE** — First-Degree Entailment, Belnap–Dunn four-valued (paraconsistent) logic.
**BL** — Hájek's Basic fuzzy Logic (the logic of continuous t-norms).
**BI** — the logic of Bunched Implications (the propositional basis of separation logic).
**ILP** — Inductive Logic Programming (learning logic programs from examples; Popper/Aleph).
**LFF** — Learning From Failures, the ILP paradigm behind the Popper system.
**CLP** — Constraint Logic Programming (e.g. CLP(FD), CLP(R)).
**CP** — Constraint Programming.
**CHR** — Constraint Handling Rules.
**FD** — finite domain (as in CLP(FD)); also functional dependence in dependence/team logic.
**SLD** — SLD resolution: Selective Linear resolution for Definite clauses (Prolog's strategy).
**SLG** — SLG resolution: the tabled, well-founded resolution used for Datalog/Prolog tabling.
**DRed** — Delete-and-Rederive, the standard algorithm for incremental Datalog view maintenance.
**EDB** — Extensional Database: the base (asserted) facts of a Datalog program.
**TMS** — Truth Maintenance System (records justifications so retractions propagate).
**JTMS** — Justification-based Truth Maintenance System.
**ST** — standard translation: the meaning-preserving map from modal logic into first-order logic / SMT.
**CTD** — Contrary-To-Duty: an obligation that only arises once another obligation has been violated.
**ESO** — Existential Second-Order logic (existential quantification over relations; captures NP).
**SRL** — Statistical Relational Learning (learning over relational + probabilistic structure).
**MLN** — Markov Logic Network (first-order formulas with weights → a Markov random field).
**PSL** — Probabilistic Soft Logic (continuous-truth relational logic; hinge-loss MRFs).
**HL-MRF** — Hinge-Loss Markov Random Field (the convex model PSL compiles to).
**MRF** — Markov Random Field (undirected graphical model).
**SCM** — Structural Causal Model (Pearl's equations + do-operator).
**HP** — Halpern–Pearl, the structural-model definition of *actual causation*.
**AC1**, **AC2**, **AC3** — the three conditions (occurrence, witness/but-for, minimality) of the (modified) Halpern–Pearl actual-causation definition.
**ATP** — Automated Theorem Prover.
**LTS** — Labelled Transition System.

## Complexity classes & solver internals

**NP** — nondeterministic polynomial time (the class of SAT and friends).
**coNP** — the complement class of NP (e.g. propositional validity / UNSAT).
**PTIME** — deterministic polynomial time.
**PSPACE** — problems solvable in polynomial space.
**NEXPTIME** — nondeterministic exponential time.
**EXPSPACE** — problems solvable in exponential space.
**BMC** — Bounded Model Checking (unroll the transition relation to depth k and hand it to SAT/SMT).
**CEGAR** — Counterexample-Guided Abstraction Refinement.
**IC3** / **PDR** — Property-Directed Reachability, an incremental SAT-based model-checking algorithm.
**CDCL** — Conflict-Driven Clause Learning (the modern SAT-solving core).
**DPLL** — Davis–Putnam–Logemann–Loveland (the backtracking-search ancestor of CDCL).
**VSIDS** — Variable State Independent Decaying Sum, the standard CDCL decision heuristic.
**CNF** — Conjunctive Normal Form.
**DRAT** — Deletion Resolution Asymmetric Tautology, the standard machine-checkable SAT proof format.
**MUS** — Minimal Unsatisfiable Subset (a minimal UNSAT core).
**WMC** — Weighted Model Counting (sum of weights of satisfying assignments).
**DNNF** — Decomposable Negation Normal Form (here d-DNNF), a tractable knowledge-compilation target.
**SDD** — Sentential Decision Diagram, another canonical knowledge-compilation form.
**BDD** — Binary Decision Diagram.
**LIA** — Linear Integer Arithmetic (SMT theory).
**LRA** — Linear Real Arithmetic (SMT theory).
**NRA** — Nonlinear Real Arithmetic (SMT theory).
**ATL** — Alternating-time Temporal Logic (strategic ability of agent coalitions).
**SL** — Strategy Logic (first-class quantification over strategies).
**GR** — GR(1), Generalized Reactivity(1), the tractable fragment used in reactive synthesis.
**MDP** — Markov Decision Process.
**PCTL** — Probabilistic Computation Tree Logic.
**CSL** — Continuous Stochastic Logic (PCTL-style logic over continuous-time Markov chains).
**RV** — Runtime Verification (monitoring a running system against a formal spec).
**RT** — real-time.
**VC** — verification condition (the proof obligation a verifier discharges); also Lewis's counterfactual logic VC.
**VW** — Lewis's counterfactual logic VW (variably-strict conditionals without uniqueness).
**PBES** — Parameterised Boolean Equation System (the μ-calculus model-checking target in mCRL2).
**LFSC** — Logical Framework with Side Conditions (a checkable proof format, e.g. from cvc5).
**UNDEC** — undecidable (table shorthand in the survey).

## Probabilistic & statistical methods

**MAP** — Maximum A Posteriori (the most-probable assignment / point estimate).
**HMC** — Hamiltonian Monte Carlo (gradient-based MCMC sampler).
**NUTS** — No-U-Turn Sampler (the self-tuning HMC variant in Stan/PyMC/NumPyro).
**ESS** — Effective Sample Size (autocorrelation-adjusted sample count from an MCMC chain).
**ECE** — Expected Calibration Error (gap between predicted probabilities and empirical frequencies).
**MH** — survey confidence-legend code, "medium-high" (defined inline in D-coverage-and-completeness.md; *not* Metropolis–Hastings in this corpus).

## Safety-critical standards & engineering

**MC-DC** — Modified Condition/Decision Coverage, the structural-coverage criterion mandated for the highest-criticality avionics software.
**MC** and **DC** — the Modified-Condition and Decision-Coverage components of **MC-DC** (flagged separately when the survey writes `structural/MC-DC`).
**WCET** — Worst-Case Execution Time.
**FTTI** — Fault-Tolerant Time Interval (the window within which a fault must be handled to stay safe).
**RMA** — Rate-Monotonic Analysis (schedulability analysis for fixed-priority real-time tasks).
**DO** — the RTCA DO-NNN family of avionics software standards (e.g. DO-178C, DO-330, DO-333).
**TQL** — Tool Qualification Level (the DO-178C criticality tier a verification tool must itself meet).
**GNC** — Guidance, Navigation, and Control.
**ODE** — Ordinary Differential Equation.

## Domain — finance & medical

**DvP** — Delivery versus Payment (securities settlement: asset transfer iff payment, atomically).
**MNPI** — Material Non-Public Information (the basis of insider-trading constraints).
**PHI** — Protected Health Information.
**eGFR** — estimated Glomerular Filtration Rate (a kidney-function measure).

## Project & tooling terms

**QUAL** — a qualification gate (QUAL-1 … QUAL-7), the discipline that makes an LLM-authored encoding trustworthy at life-critical stakes (see [C-encoding-qualification.md](../../research/obligations-formalisms-survey/C-encoding-qualification.md)).
**SSOT** — Single Source Of Truth: the one authoritative home for a fact (also in the root [GLOSSARY.md](../../GLOSSARY.md)).
**SMT-LIB** — the standard textual input/exchange format for SMT solvers.
**CTE** — Common Table Expression (a `WITH`-clause subquery in SQL; recursive CTEs ≈ Datalog).

## Known typo in the frozen survey text

**STIG** — a typo for **STIT** at `formal-systems/20-stit-agency.md:30`. The survey text is frozen
(supersession discipline), so it is recorded here rather than silently passed or edited away.
