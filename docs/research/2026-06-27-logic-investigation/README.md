# Logics & automated deduction — applicability to autoharn

_Generated 2026-06-27 by a 13-family parallel investigation (13/13 families + a software
catalog, an adversarial fit-critic, and a synthesis), run `wf_6be06f87-68d`._

> **Vocabulary:** coined terms (Pillar, intent SSOT, *_violations gate, supersession, …) are defined in
> the root **[GLOSSARY.md](../../../GLOSSARY.md)** and linked on first use; never grep to learn a term.

Investigation into (1) the **applicability** of classical & non-classical logics + automated deduction
to autoharn, grounded in its concrete needs, and (2) the open-source **software** to leverage — each
family section carries a primer for the maintainer's edification.

## Read in this order

- **[00-synthesis.md](00-synthesis.md)** — thesis verdict, applicability matrix, **tiered recommended
  stack**, learning path, first experiment. **Start here.**
- **[B-autoharn-fit.md](B-autoharn-fit.md)** — adversarial critic: which logics earn their place vs.
  which are intellectual tourism for *this* project; coverage gaps.
- **[A-software-landscape.md](A-software-landscape.md)** — unified engine catalog + concrete install plan.

## Family deep-dives (applicability · software · primer · honest limits)

- [01-datalog.md](01-datalog.md) — Datalog & Deductive Databases
- [02-prolog-clp.md](02-prolog-clp.md) — Prolog & Constraint Logic Programming (SWI-Prolog, CLP(FD))
- [03-asp.md](03-asp.md) — Answer Set Programming (clingo / DLV)
- [04-defeasible-argumentation.md](04-defeasible-argumentation.md) — Defeasible / Non-monotonic Reasoning & Formal Argumentation
- [05-modal-epistemic.md](05-modal-epistemic.md) — Modal & Epistemic Logic
- [06-temporal-runtime.md](06-temporal-runtime.md) — Temporal Logic & Runtime Verification (LTL/CTL/MTL, TLA+)
- [07-paraconsistent.md](07-paraconsistent.md) — Paraconsistent & Many-valued Logic
- [08-description-logic.md](08-description-logic.md) — Description Logic & Ontologies (OWL)
- [09-linear-resource.md](09-linear-resource.md) — Linear & Resource-aware Logic
- [10-relevance-substructural.md](10-relevance-substructural.md) — Relevance & Substructural Logics
- [11-smt-fol.md](11-smt-fol.md) — SMT & Classical First-order Logic (Z3 / cvc5)
- [12-abductive-ilp.md](12-abductive-ilp.md) — Abductive Reasoning & Inductive Logic Programming
- [13-probabilistic-srl.md](13-probabilistic-srl.md) — Probabilistic Logic & Statistical-relational AI (ProbLog / PSL / MLN)
- [14-probabilistic-programming-bayesian.md](14-probabilistic-programming-bayesian.md) — Probabilistic Programming & Formal Bayesian Frameworks (complement to 13)

## Provenance & integrity

- All **13/13** logic families produced a section. Family sections + cross-cuts + synthesis are
  verbatim workflow output; engine version/license claims are agent-reported (web-checked where noted) —
  worth a confirm before install.
- Local engines already present and used by some examples: SWI-Prolog 9.3.31, clingo 5.8.0, Z3 4.16,
  OR-Tools CP-SAT 9.15 (`~/w/vdc/venvs/generic`). Not-installed engines are no objection — open-source,
  compile/`pip` as needed (ask the maintainer only for obscure or disk-heavy installs).
- **Report 14 (Probabilistic Programming & Bayesian)** is a hand-commissioned complement to report 13,
  authored in a separate single-agent run (`wf_6e4d1fb1-3ae`); its footer says so.