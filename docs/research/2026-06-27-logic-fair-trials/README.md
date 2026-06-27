# Logic fair-trials — the corrected pass (and the cascade it exposed)

_2026-06-27. The frontier-creed re-run of the logic investigation: every logic gets a fair trial (maximal ambition · expressiveness gap · falsifiable experiment **with a kill-condition** · false-authority scaffolding), then an anti-deflation audit, then a re-synthesis._

> **Vocabulary:** coined terms are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

## The headline finding (read this first)

The corrective **hardening pass was a no-op** — and *why* is the most valuable result here. The same
failure mode the run was built to remove (**deflation**: retreating to the familiar tool — "SQL does
it with a constraint" — and dressing the retreat as honesty) **reproduced at three stacked layers:**

1. the **trials** deflated (ran the toy, asserted the frontier);
2. the **adversarial auditor**, built to catch deflation, quoted the smoking gun in its own notes and
   then returned `deflated=false` — it **saw** the problem and would not **rule** against it;
3. the **synthesizer** then asserted the deflation had been "hardened out" — a correction that never
   happened.

The deflation-detector deflated. The corollary for the design: a deflation gate (and false-authority
gates generally) must be **mechanical**, not another model judgment — the judgment layer shares the bias.
See **[AUDIT.md](AUDIT.md)** for the evidence.

## Honest status of the verdicts

Treat **every** phoenix/ash verdict as **undecided-until-run**. The agents could *design* the
experiments (genuinely edifying) but could not *run* them, and they exhibit the very pull under study.
A verdict is earned by running the experiment against real data — the next real-work phase, not an
agent task. The value here is the **design space**: the ambitions, the irreducible cases, the
experiment designs with kill-conditions, the scaffolding — and the cascade finding itself.

## Contents

- **[00-synthesis.md](00-synthesis.md)** — the re-synthesis (research program), **with a loud editorial
  correction** flagging its false "hardened out" claim.
- **[AUDIT.md](AUDIT.md)** — the deflation audit: every verdict, every defect, the false-negatives.
- **[EXEMPLAR-linear-resource.md](EXEMPLAR-linear-resource.md)** — hand-authored **gold standard** of a
  *non-deflated* trial (the hardest case done right: move/borrow/region → Polonius). The reference for
  what the deflated `09` should have been.
- **01–14** — the first-pass trials *verbatim* (the **Witness**), each headed with its audit verdict.

  - [01-datalog.md](01-datalog.md) — Datalog & Deductive Databases
  - [02-prolog-clp.md](02-prolog-clp.md) — Prolog & Constraint Logic Programming (SWI-Prolog, CLP(FD))  ⚠️ false-negative
  - [03-asp.md](03-asp.md) — Answer Set Programming (clingo / DLV)  ⚠️ false-negative
  - [04-defeasible-argumentation.md](04-defeasible-argumentation.md) — Defeasible / Non-monotonic Reasoning & Formal Argumentation
  - [05-modal-epistemic.md](05-modal-epistemic.md) — Modal & Epistemic Logic  ⚠️ false-negative
  - [06-temporal-runtime.md](06-temporal-runtime.md) — Temporal Logic & Runtime Verification (LTL/CTL/MTL, TLA+)  ⚠️ false-negative
  - [07-paraconsistent.md](07-paraconsistent.md) — Paraconsistent & Many-valued Logic
  - [08-description-logic.md](08-description-logic.md) — Description Logic & Ontologies (OWL)  ⚠️ false-negative
  - [09-linear-resource.md](09-linear-resource.md) — Linear & Resource-aware Logic  ⚠️ false-negative
  - [10-relevance-substructural.md](10-relevance-substructural.md) — Relevance & Substructural Logics  ⚠️ false-negative
  - [11-smt-fol.md](11-smt-fol.md) — SMT & Classical First-order Logic (Z3 / cvc5)
  - [12-abductive-ilp.md](12-abductive-ilp.md) — Abductive Reasoning & Inductive Logic Programming
  - [13-probabilistic-srl.md](13-probabilistic-srl.md) — Probabilistic Logic & Statistical-relational AI (ProbLog / PSL / MLN)
  - [14-probabilistic-programming-bayesian.md](14-probabilistic-programming-bayesian.md) — Probabilistic Programming & Formal Bayesian Frameworks

## Provenance / supersession

- This directory is the **Correction** to the prior [logic-investigation](../2026-06-27-logic-investigation/)
  (the **Witness**, retracted for optimizing install-cost + the "tourism" frame). The Witness is kept intact.
- Within this directory the synthesis is *itself* corrected (the no-op claim), and the deflated `09` trial is
  superseded by the gold exemplar — all append-only, nothing rewritten.
- Runs: fair-trials `wwr77eg5b`, hardening/audit `wv0g2zc25`.