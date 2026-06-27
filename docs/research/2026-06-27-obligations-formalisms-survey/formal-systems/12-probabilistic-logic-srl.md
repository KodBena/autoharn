# 12 — Probabilistic Logic & Statistical-relational AI (ProbLog/PSL/MLN)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

Logics that attach calibrated numbers — probabilities or soft truth-degrees — to relational facts and rules, so that uncertainty is *carried through deduction* with a stated guarantee strength rather than thresholded away at the input boundary. Their job in autoharn is the obligation where the quantity being asserted is itself irreducibly statistical.

## Primer (becoming broadly expert)

Three lineages share one move: lift logic from {true,false} to [0,1] over a relational vocabulary. **ProbLog** (De Raedt, Kimmig, Toivonen, IJCAI 2007; KU Leuven) is a probabilistic Prolog under Sato's **distribution semantics**: each probabilistic fact is an independent Bernoulli switch, and the probability of a query is the weighted-model-count over all worlds that prove it — exact inference via knowledge compilation to d-DNNF/SDD. **Markov Logic Networks** (Richardson & Domingos, *Machine Learning* 2006) attach a real *weight* to each first-order formula; the ground network is a Markov random field where a world's probability rises with the weight-sum of satisfied formulas — a violated rule costs but does not annihilate. **Probabilistic Soft Logic** (Bach, Broecheler, Huang, Getoor, JMLR 2017; LINQS) relaxes truth to continuous [0,1] with Łukasiewicz connectives, turning MAP inference into a *convex* optimization (a HL-MRF) that scales.

The concept that matters: a probabilistic rule does not detach a conclusion — it detaches a *distribution*, and distributions compose by the calculus rather than by a programmer's ad-hoc multiply. The intuition for obligation-fit: when the honest claim is "84% ± 3%, here is the model," a logic that can only say true/false either lies or aborts. These systems are built so that **confidence is a first-class, composable, auditable derivation**, not a comment.

## Obligations it discharges

**CALIB (home obligation).** CALIB demands a "calibrated confidence that composes correctly and is matched against the obligation's required strength." This is exactly the distribution semantics' deliverable: ProbLog returns a number with a *defined* probabilistic meaning (weighted model count), and the composition of sub-claim confidences is the inference calculus, not a hand-rolled `p1*p2`. The guarantee strength bought is precise but *conditional*: **exact** propagation of uncertainty *given* the input probabilities and independence structure. It does not manufacture calibration — it preserves it. That is the right bar for a "float-sensitive / stated-CI" claim, and it makes the required-strength comparison mechanical: gate on `P(unsafe) < ε`.

**PROV — groundedness with weighted pedigree.** A ProbLog proof is a finite, replayable AND/OR chain to probabilistic facts (the primary evidence). The marginal is reconstructible and the derivation edges carry warrants — a confabulated chain scores its own low probability instead of passing as certain.

**CLASS — honest sharp classification under uncertainty.** A probabilistic classifier yields a *posterior over the closed vocabulary*; "no slot fits" surfaces as a flat/low-max posterior that a threshold routes loudly to `unknown`, rather than silent nearest-wrong sortation. MLN/PSL collective classification additionally enforces relational mutual-exclusion as soft constraints.

**CONSIST — contradiction containment without ex falso.** This is MLN/PSL's structural gift: contradictory soft evidence does not detonate the store (no ex falso), nor is it silently averaged — conflicting weighted formulas produce a *quantified tension* localized to the disputed atoms, leaving the rest of the model usable. Two redundant sensors disagreeing yields a hung/degraded posterior, not vacuous clearance.

**TRIG (partial).** For *degraded sensing*, probabilistic detachment computes `P(trigger)` from noisy inputs, separating "duty should fire" from "I am sure" — but the firing *decision* must still be a hard, logged threshold.

**Does NOT serve:** **INV, PROG, DEGRADE, AUTH, ATTR, COMMIT, COHERE, STRUCT, TRACE, RECORD, INDEP.** A safety invariant is not "P=0.9999"; a real-time deadline, an authorization gate, an agency record, and a happens-before order are *exact* deontic/temporal facts whose failure mode is categorical. Using a probability where an invariant is owed is a category error — assign INV to model checking / SMT, not here.

## A worked encoding

Redundant cabin-altitude sensors; the mask-deploy duty (TRIG) must reason about disagreement (CONSIST) and emit a calibrated trigger probability (CALIB). ProbLog syntax:

```prolog
% sensor reliabilities (calibrated from fleet data, the "primary evidence")
0.97::sensor_ok(a).
0.97::sensor_ok(b).
% degraded-sensor noise model: P(reads high | true state)
0.99::reads_high(a) :- truly_high, sensor_ok(a).
0.05::reads_high(a) :- \+ truly_high, sensor_ok(a).   % false positive
0.99::reads_high(b) :- truly_high, sensor_ok(b).
0.05::reads_high(b) :- \+ truly_high, sensor_ok(b).
0.5::truly_high.                                       % prior

% observed this tick: A says high, B says not-high (the conflict)
evidence(reads_high(a), true).
evidence(reads_high(b), false).

% the trigger duty's belief
query(truly_high).
```

`problog mask.pl` returns a single posterior `P(truly_high | a∧¬b)` — neither 1 (A wins) nor 0 (B wins) nor a silent average, but the exact weighted-model-count fusion. autoharn gates: deploy if `P > 0.90`, else declare `degraded-mode` and demand a third channel. The conflict is *quantified and contained*, and the number is auditable back to the fleet-calibrated facts.

## Automation & tooling (git-clone-runnable)

- **ProbLog 2** — DTAI/KU Leuven, **Apache-2.0**, PyPI **`problog`** (2.2.x current, 2.2.7 tagged Mar 2025; 2.2.10 on PyPI). Pure-Python core; exact inference via internal SDD/d-DNNF compilation. **`pip install problog`** is the git-clone path. *Not currently installed locally* (verified: `problog` absent; `clingo 5.8.0`, `swipl 9.3.31`, `z3 4.16` present) — add it to `requirements.txt`. **DeepProbLog** exists for neural fusion but is research-grade. **Recommended host for autoharn.**
- **PSL** — LINQS (UMD/UCSC), **Apache-2.0**, Java/Maven; convex MAP inference, scales to large relational data. Mature but JVM-heavy; pick it when soft collective classification over millions of atoms is the load.
- **MLN solvers** — **`pracmln`** (Python, BSD) and **Tuffy** (Java/Postgres) are **effectively unmaintained** (verified: pracmln flagged inactive; Tuffy v0.4 legacy). **Do not stand a life-critical pipeline on them.**

**Encoding path when you want the local stack:** MLN/LP^MLN semantics map cleanly onto **clingo** (installed). Encode weighted formulas as ASP weak constraints: `:~ body. [w@p]` makes the optimal stable model the MAP world, recovering MLN MAP inference on a maintained engine. For exact marginals, ProbLog's distribution semantics is also expressible as weighted model counting over a clingo/Prolog grounding handed to a WMC backend. So "MLN tools are dead" yields **encode-into-clingo/ProbLog**, not a shrug.

## Honest leverage & kill-condition

**Load-bearing:** CALIB and CONSIST where the quantity is genuinely statistical — sensor fusion, evidence-weighted PROV chains, posteriors that must compose and be compared to a required `ε`. ProbLog gives an *exact, replayable* uncertainty derivation: a mechanical gate, not an LLM's vibe.

**Ash:** anywhere it is used to *launder* a hard obligation — dressing an INV/AUTH/RECORD fact as a high probability. `P(safe)=0.9999` is decorative on a barrier that must *never* be crossed.

**Falsifiable experiment + KILL CONDITION:** the numbers are only load-bearing if they are *calibrated*. Take a held-out fixture set with ground truth; run ProbLog's posteriors through a reliability diagram and Brier/ECE check. **KILL CONDITION:** if expected calibration error exceeds the obligation's stated tolerance (predicted probabilities diverge from empirical frequencies beyond CI) on the qualification fixtures, then the distribution semantics is propagating mis-calibrated inputs faithfully but uselessly — the green `P` is a costume, CALIB is *not* discharged, and the obligation must fall back to an exact channel or a recalibrated model. The engine's exactness does not rescue garbage priors; that is the experiment that settles it.

## References (edification)

- De Raedt, Kimmig & Toivonen, *ProbLog: A Probabilistic Prolog and Its Application in Link Discovery* (IJCAI 2007) — the founding paper; teaches the distribution semantics and WMC inference.
- Richardson & Domingos, *Markov Logic Networks* (Mach. Learn. 2006) — teaches weighted first-order formulas and the violated-rule-costs-but-doesn't-kill intuition behind CONSIST.
- Bach, Broecheler, Huang & Getoor, *Hinge-Loss Markov Random Fields and Probabilistic Soft Logic* (JMLR 2017) — teaches the convex relaxation that makes relational probabilistic inference scale.
- ProbLog tutorial — [dtai.cs.kuleuven.be/problog](https://dtai.cs.kuleuven.be/problog/) — runnable examples; teaches the exact syntax/gating used above.

Sources: [problog PyPI](https://pypi.org/project/problog/) · [ML-KULeuven/problog](https://github.com/ML-KULeuven/problog) · [PSL / LINQS](https://psl.linqs.org/) · [linqs/psl](https://github.com/linqs/psl) · [pracmln](https://pypi.org/project/pracmln/) · [HazyResearch/tuffy](https://github.com/HazyResearch/tuffy)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
