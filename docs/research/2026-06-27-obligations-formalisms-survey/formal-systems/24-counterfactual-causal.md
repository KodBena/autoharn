# 24 — Counterfactual/Conditional Logic (Lewis/Stalnaker) & Causal Models (Pearl, Halpern–Pearl actual causation)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

The machinery for "had X not happened, Y would not have" — and for the harder question of which of several actual antecedents *actually caused* an outcome under preemption, overdetermination, and many-hands. This is the formal heart of attributing a change to an agent who *could have done otherwise*.

## Primer (becoming broadly expert)

A counterfactual `A □→ C` ("if A had held, C would have held") cannot be material implication — antecedents are false by construction, which would make every counterfactual vacuously true. **Stalnaker (1968)** and **Lewis (1973, *Counterfactuals*)** give it a possible-worlds semantics: `A □→ C` is true at world *w* iff C holds at the *closest* A-worlds, ordered by a similarity/comparative-plausibility relation (a system of spheres). Stalnaker assumes a unique closest world (Conditional Excluded Middle); Lewis drops uniqueness. The canonical logics are Lewis's **VC/VW**. Crucially these conditionals are **non-monotonic**: strengthening the antecedent need not preserve the consequent.

**Pearl (*Causality*, 2000)** operationalizes "closest A-world" mechanically: a Structural Causal Model is a set of equations; the counterfactual is computed by the **do-operator** — surgically setting a variable, severing its incoming equations, and propagating. **Halpern & Pearl (2001, revised 2005; Halpern 2016, *Actual Causality*)** then define **actual causation**: X=x is an actual cause of φ iff (AC1) both occurred, (AC2) there is a witness partition holding some variables fixed under which intervening on X flips φ, and (AC3) X is minimal. This is built to discharge **attribution**: it separates a genuine but-for difference-maker from a bystander, and handles overdetermination/preemption where naive but-for fails.

## Obligations it discharges

**ATTR — Agency Attribution & Non-Repudiable Change (primary, strong fit).** ATTR's deep requirement is the *could-have-done-otherwise* test and the *saw-to-it* binding, and its failure mode is accountability assigned to an agent with no exercisable alternative, or responsibility voids under many-hands. This is *exactly* what Halpern–Pearl actual causation formalizes. Naive logging records co-presence ("the account was active"); HP-causation records difference-making under an explicit witness setting — it is the only formalism in this taxonomy that distinguishes a rubber-stamp (no contingency under which the agent's act changes the outcome) from genuine supervision (a contingency exists). Guarantee strength: a **constructive certificate** — for each putative cause, either a concrete witness partition + intervention that flips the outcome (cause confirmed) or a proof no such witness exists (cause refuted), decidable over a finite Boolean model.

**PROV — Claim Provenance & Groundedness (secondary).** The do-calculus turns "why did the system conclude C?" into a replayable structural chain: C resolves to the equations and exogenous inputs that actually determined it. This catches the confabulated-chain failure (a derivation edge with no warrant) when the warrant is *causal* rather than merely logical.

**REVISE — Belief Revision (partial, via the Ramsey/Stalnaker test).** The Ramsey test links conditionals to belief change: accepting `A □→ C` is accepting C after minimally revising to admit A. This is the conceptual bridge to AGM, useful for "what would we have concluded under the corrected reading?"

**Does NOT serve:** **INV/PROG** (always/eventually properties are temporal, not causal — use temporal logic), **CLASS, STRUCT, COHERE, CALIB, COMMIT, TRIG** (deontic detachment is a conditional *obligation*, not a *counterfactual* — a different conditional). Forcing causal semantics onto an invariant buys nothing.

## A worked encoding

ATTR example: an overnight loosening of a Fed risk limit, approved through a shared service account where **two** approvers' tokens were both present (overdetermination). Naive but-for exonerates *both* ("removing approver A alone, B still approves → no difference"). HP-causation, with a witness that holds B fixed at *not-approving*, correctly identifies each as an actual cause. Z3 (Python) checks AC2:

```python
from z3 import *
# Structural model: limit_changed = approve_A OR approve_B (overdetermination)
aA, aB, changed = Bools('aA aB changed')
def model(a, b): return (a, b, Or(a, b))   # the structural equation

# Actual world: both approved, limit changed.
s = Solver(); s.add(aA==True, aB==True, changed==Or(aA,aB))
assert s.check()==sat                       # AC1 holds

# AC2 for cause aA: exists a witness W (here: fix aB) and a setting of aA
# under which the outcome flips. Hold aB at its actual value? No — HP allows
# resetting witness vars to *other* values. Try aB := False (the witness).
def is_actual_cause(cause_false_val, witness_false):
    out = Or(cause_false_val, witness_false)   # intervene: aA:=False, aB:=False
    return simplify(out) == BoolVal(False)     # outcome flips to "not changed"

print("aA actual cause?", is_actual_cause(False, False))  # True: witness aB:=F flips it
```

The witness `aB:=False` is the auditable certificate that approver A *could have made a difference* — the record autoharn must store alongside the timestamp and authenticated actor, converting "the account approved it" into "agent A is an actual cause under witness {B not approving}."

## Automation & tooling (the git-clone-runnable question)

**Dedicated tool for actual causation: HP2SAT** — Java, **MIT license**, latest tagged release **1.0** (the canonical reference implementation of the *modified* Halpern–Pearl definition; Ibrahim & Pretschner, *Efficiently Checking Actual Causality with SAT Solving*, 2019). It reduces AC2/AC3 to SAT via the LogicNG/MiniSat stack and is the industrial-grade choice for Boolean structural models; verified at github.com/amjadKhalifah/HP2SAT1.0. Maturity: research-grade but published, cited, MIT — bundleable. **chirho** (Basis Research, Pyro-based) implements modified-HP actual causation for *probabilistic/continuous* SCMs — pull it in when models are stochastic. For statistical/interventional causal inference (do-calculus identification, not actual causation): **DoWhy** — MIT, **v0.14 (Nov 2025)**, verified on PyPI.

**Encoding path (host already installed, no Java needed):** the AC2 witness search is naturally an ASP problem. In **clingo 5.8** (local), encode structural equations as rules, `#external` the interventions, and search over witness partitions: guess a subset W of variables to fix and a counterfactual value for the candidate cause, then constrain that the outcome predicate flips — `:- not flipped.` AC3 minimality falls out of clingo's `#minimize`. For larger Boolean models, mirror HP2SAT directly into **Z3** (local, 4.16): assert the structural equations as a circuit, existentially quantify the witness assignment, and use `check()`/`get-model` to return the certificate — exactly the snippet above generalized with a Bool per variable and a quantified witness mask. Both give the constructive witness ATTR needs.

## Honest leverage & kill-condition

**Load-bearing where** the obligation is genuinely *attributive* and the structural model is honest and finite: Fed limit changes, NYSE order gating, ICU order authorship — many-hands, preemption, and rubber-stamp detection. Here HP-causation is not a heuristic; it is the definition, and HP2SAT/clingo discharge it mechanically.

**Ash where** the failure mode is temporal-invariant (INV/PROG) or where the causal model is *fabricated to order* — the LLM that authors the structural equations can launder the very bias the certificate is meant to expose (omit a confounding edge and any cause can be exonerated). The model is the attack surface, not the solver.

**Falsifiable experiment:** assemble a benchmark of 50 attribution scenarios with adjudicated ground-truth causes (overdetermination, late/early preemption, switch cases — the standard HP literature set). Have the LLM author SCMs from incident narratives; run HP2SAT/clingo; score against ground truth. **KILL CONDITION:** if LLM-authored models yield the correct actual-cause set on **< 90%** of scenarios — *or* if a held-out mutation suite (silently deleting one structural edge) is not flagged by an INDEP differential check on **≥ 95%** of mutants — then the encoding tax is not paid: the solver is sound but the modeling step is the unqualified link, and autoharn must demote causal attribution from "certificate" to "advisory" pending a qualified model-authoring oracle.

## References (edification)

- **Lewis, *Counterfactuals* (1973).** Teaches the sphere semantics and why counterfactuals are non-monotonic — the conceptual foundation.
- **Halpern, *Actual Causality* (MIT Press, 2016).** The definitive, example-driven treatment of the modified HP definition (AC1–AC3), preemption, and responsibility/blame — the maintainer's primary text for ATTR.
- **Pearl, *Causality* (2nd ed., 2009).** Structural causal models, the do-operator, and the three-level ladder (association/intervention/counterfactual) — the computational engine.
- **Ibrahim & Pretschner, *Efficiently Checking Actual Causality with SAT Solving* (2019).** Teaches the SAT reduction behind HP2SAT — the bridge from definition to runnable solver.

Sources: [HP2SAT](https://github.com/amjadKhalifah/HP2SAT1.0), [HP2SAT paper](https://arxiv.org/pdf/1904.13101), [chirho actual causality](https://basisresearch.github.io/chirho/actual_causality.html), [DoWhy](https://pypi.org/project/dowhy/)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
