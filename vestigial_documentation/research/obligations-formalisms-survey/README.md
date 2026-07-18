# Obligations × formalisms — the survey

_2026-06-27. A 27-formal-system survey at **life-critical seriousness**, organized by **obligation** (not by logic): each formal system is *assigned* to the responsibilities whose failure modes its semantics match, with a concrete **automation / encoding path**, produced by workflow run `wf_2b657cd5-b06` using 38 agents._

> **New here?** Read **[KEY.md](KEY.md)** first — it defines every obligation code (INV, DEGRADE, …), the guarantee/cost tiers (5–1, T0–T3), and every tool name. Codes are linked to it throughout. Coined terms are in the root **[GLOSSARY.md](../../../GLOSSARY.md)**. Stray acronyms (MC-DC, WCET, DvP, …) are defined in the doc-legibility glossary **[gates/doc-legibility/terms.md](../../../gates/doc-legibility/terms.md)**, mechanically enforced by its gate.

## Read in this order

- **[KEY.md](KEY.md)** — the abbreviations/tiers/tools legend. **Read first.**
- **[00-synthesis.md](00-synthesis.md)** — the obligation→formalism assignment, runnable tooling reality, composition sketch, learning path, honest verdicts.
- **[01-obligation-taxonomy.md](01-obligation-taxonomy.md)** — the responsibility classes, fully defined.
- **[A-automation-and-encoding.md](A-automation-and-encoding.md)** · dedicated tool vs encode-into-host per system.
- **[B-composition-architecture.md](B-composition-architecture.md)** · how the subsystems compose into one ledger.
- **[C-encoding-qualification.md](C-encoding-qualification.md)** · qualifying an LLM-authored encoding (the QUAL gates).
- **[D-coverage-and-completeness.md](D-coverage-and-completeness.md)** · coverage matrix + what the roster missed.

## The 27 formal systems  (in [formal-systems/](formal-systems))

- [Datalog & Deductive Databases](formal-systems/01-datalog.md)
- [Prolog, CLP & Prolog-as-Encoding-Host](formal-systems/02-prolog-clp.md)
- [Answer Set Programming (clingo)](formal-systems/03-asp.md)
- [SMT & Classical First-order Logic (Z3 / cvc5)](formal-systems/04-smt-fol.md)
- [SAT, CP & Finite-domain Constraint Solving](formal-systems/05-sat-cp.md)
- [Linear & Branching Temporal Logic + Model Checking (LTL/CTL, NuSMV/Spot)](formal-systems/06-ltl-ctl-modelchecking.md)
- [TLA+ / TLC — Specification & Refinement](formal-systems/07-tla-refinement.md)
- [Metric, Real-time & Interval Temporal Logic (MTL/STL, Allen/HS)](formal-systems/08-metric-interval-temporal.md)
- [Modal μ-calculus, Coinduction & Process Logics (maintenance over infinite behaviour)](formal-systems/09-mu-calculus-coalgebra.md)
- [Description Logic & OWL (+ temporal/probabilistic DL)](formal-systems/10-description-logic.md)
- [Higher-order Logic, Dependent Types & Proof Assistants (Coq/Lean/Isabelle)](formal-systems/11-hol-proof-assistants.md)
- [Probabilistic Logic & Statistical-relational AI (ProbLog/PSL/MLN)](formal-systems/12-probabilistic-logic-srl.md)
- [Probabilistic Programming & Bayesian Inference (PyMC/Stan/NumPyro)](formal-systems/13-probabilistic-programming.md)
- [Inductive Logic Programming (Popper/Aleph)](formal-systems/14-ilp.md)
- [Modal Logic — the substrate (K–S5, frames, tableaux) & general modal provers](formal-systems/15-modal-substrate.md)
- [Epistemic & Dynamic Epistemic Logic (S5n, common knowledge, DEL/PAL/action models)](formal-systems/16-epistemic-del.md)
- [Justification Logic / Logic of Proofs (Artemov) — proof-carrying belief](formal-systems/17-justification-logic.md)
- [Provability Logic (GL, Löb) — self-reference & the anti-self-certification guardrail](formal-systems/18-provability-logic.md)
- [Deontic & Normative Logic (SDL, dyadic, defeasible, I/O logic, norm-change)](formal-systems/19-deontic.md)
- [STIT & Logics of Agency / Responsibility attribution](formal-systems/20-stit-agency.md)
- [Belief Revision (AGM, contraction/revision/update, ranking/Spohn, DDL)](formal-systems/21-belief-revision.md)
- [Default Logic, Circumscription & Autoepistemic Logic](formal-systems/22-nonmonotonic-classics.md)
- [Defeasible Logic & Formal Argumentation (Dung AF, ASPIC+, DeLP)](formal-systems/23-argumentation.md)
- [Counterfactual/Conditional Logic (Lewis/Stalnaker) & Causal Models (Pearl, Halpern–Pearl actual causation)](formal-systems/24-counterfactual-causal.md)
- [Paraconsistent, Many-valued, Dialetheic & Fuzzy Logic (LP, FDE/Belnap, t-norm)](formal-systems/25-paraconsistent-manyvalued.md)
- [Substructural Logic: Linear, Affine, Relevant & BI/Separation (resource, the borrow-checker lineage)](formal-systems/26-substructural.md)
- [Hyperintensional Frontier: Truthmaker Semantics, Grounding, Dependence Logic, Free Logic (flag the speculative ones)](formal-systems/27-hyperintensional.md)

## Provenance, supersession & honest caveats

- This survey is the **obligation-organized Correction** to two earlier bake-off-framed passes, kept intact as **Witnesses**: [logic-investigation](../logic-investigation) and [logic-fair-trials](../logic-fair-trials).
- **Verdicts are agent-reasoned, not experimentally settled**; engine versions/licenses are agent-reported, web-checked where noted — confirm before install. Cross-cut **[C](C-encoding-qualification.md)** is the discipline that turns claims into qualified guarantees.
- All 27 of 27 planned formal-system sections were produced, using 38 agents across the four-stage pipeline: taxonomy → survey → cross-cut → synthesis.