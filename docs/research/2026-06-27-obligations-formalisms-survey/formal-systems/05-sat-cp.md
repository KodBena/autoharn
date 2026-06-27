# 05 — SAT, CP & Finite-domain Constraint Solving

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

Decision procedures that search for a total assignment to finite-domain variables satisfying a conjunction of constraints — or prove, with a machine-checkable certificate, that none exists. The "none exists" half is the load-bearing one for autoharn: a refutation is an exhaustiveness proof over a combinatorial space too large to enumerate by hand.

## Primer (becoming broadly expert)

A SAT problem asks whether a Boolean formula in CNF has a satisfying assignment; **Cook–Levin (1971)** made it the canonical NP-complete problem, and the irony of modern practice is that industrial CDCL solvers (conflict-driven clause learning — **Marques-Silva & Sakallah's GRASP, 1996**; Chaff's VSIDS, 2001) routinely close instances with millions of variables. Constraint Programming (CP) generalizes the *language*: variables range over finite integer/set domains, constraints are high-level *global* relations (`all_different`, `cumulative`, `table`), and a **propagator** for each constraint prunes domains to a consistency level (arc/bounds consistency — **Mackworth, 1977**) before branching. CP-SAT (lazy clause generation — **Ohrimenko, Stuckey, Codish, 2009**) fuses both: CP modeling with a learning SAT core underneath.

The intuition for *which* obligation this discharges: SAT/CP is the tool of **finite total enumeration with a certificate**. Its native question is not "find me a plan" but "does *any* point in this closed combinatorial space violate the property?" When the answer is UNSAT, you have proven a universally-quantified statement over a finite domain — exactly the shape of "exactly one bucket," "no two writers disagree," "no input falls through a gap." It does not reason about time, justification, or agency; it reasons about *whether a configuration can exist*.

## Obligations it discharges

- **CLASS — Honest Sharp Classification (primary).** The MECE partition is *literally* a constraint: at-least-one (∨ of the bucket guards) and at-most-one (pairwise ¬(gᵢ∧gⱼ)) over the full input domain. Searching for a counterexample to `exactly_one(g₁…gₙ) ∨ unknown` and getting UNSAT proves the vocabulary is total and exclusive — no silent nearest-wrong sortation, no order-dependent dual dispatch. Guarantee strength: **exact and exhaustive** over the finite domain, with a refutation proof.
- **CONSIST — Consistency & Contradiction Containment.** A requirement set is consistent iff its conjunction is SAT. UNSAT means antinomy; the **Minimal Unsatisfiable Subset / unsat core** *localizes* the contradiction to the smallest conflicting clause set — quarantine by construction, rather than ex-falso laundering. Strength: exact for the propositional/finite-domain fragment.
- **STRUCT — Structural Soundness by Construction.** Finite-domain propagation proves range/overflow/saturation safety: bound every variable to its declared domain, assert the negation of the saturation guard, check UNSAT. The "no representable out-of-range value" claim becomes a discharged lemma. Strength: exact within the bounded integer model.
- **COHERE — Single-Authority Coherence.** "All writers derive one truth" is an equality/`all_equal` constraint across writer-views; "every reference resolves to exactly one current target" is a functional-dependency constraint. A satisfiable *disagreement* is a found drift. Strength: exact for the modeled wire/config facts.
- **TRACE — Coverage (test generation).** SAT is the classical engine for generating MC-DC and boundary test vectors: assert the path/condition predicate, solve for an input that exercises it; UNSAT proves a branch *infeasible* (justifying its non-coverage). Strength: exact feasibility per condition.
- **AUTH — Permission Closure (closed-world fragment).** Encode the permission set; search for a world-affecting action satisfiable *outside* it. UNSAT proves no authority leakage under the declared closure. (Norm *precedence* with defeasible override belongs to deontic/ASP layers; CP handles the static closure check.)
- **INV — Safety-Invariant (bounded).** Bounded Model Checking unrolls the transition relation to depth *k* and SAT-checks whether the invariant is violated within *k* steps. This is its honest reach and its limit — see kill-condition.

**Does NOT serve:** **PROG** (liveness/"eventually," WCET over infinite traces — needs temporal/real-time logics; SAT sees only bounded prefixes), **REVISE/PROV/RECORD/ATTR/COMMIT** (justification chains, agency, temporal ordering, lifecycle — not constraint satisfiability), **DEGRADE/TRIG** (contrary-to-duty and detachment are deontic). Forcing these into CP is encoding malpractice.

## A worked encoding

CLASS obligation: prove a triage partition is total and mutually exclusive over the *whole* input domain (not just sampled rows). Real OR-Tools CP-SAT (Python), runs on the installed 9.15:

```python
from ortools.sat.python import cp_model
m = cp_model.CpModel()
# input domain: heart_rate 20..250, spo2 50..100
hr  = m.new_int_var(20, 250, "hr")
spo2= m.new_int_var(50, 100, "spo2")

# bucket guards (the deployed triage rules)
crit = m.new_bool_var("crit"); m.add(spo2 < 85).only_enforce_if(crit)
m.add(spo2 >= 85).only_enforce_if(crit.Not())
urg  = m.new_bool_var("urg");  m.add(hr > 130).only_enforce_if(urg)
m.add(hr <= 130).only_enforce_if(urg.Not())
# NOTE: no bucket covers hr<=130 and spo2>=85 -> a GAP

# look for a counterexample to "exactly one bucket fires"
n_fired = sum([crit, urg])
m.add(n_fired != 1)          # 0 (gap) or >=2 (dual-class)
solver = cp_model.CpSolver()
print(solver.status_name(solver.solve(m)))   # OPTIMAL/FEASIBLE = BUG
if solver.solve(m) == cp_model.OPTIMAL:
    print("uncovered:", solver.value(hr), solver.value(spo2))
```

This returns `OPTIMAL` with e.g. `hr=100, spo2=90` — a stable patient that matches **zero** tiers (the gap from obligation CLASS's failure mode). Fix the rules until this model is `INFEASIBLE`; that UNSAT is the exhaustiveness proof. The same skeleton with `n_fired >= 2` audits dual-classing. Crucially this is *qualifiable* (INDEP): CP-SAT can emit a checkable certificate, and the harness keeps golden SAT/UNSAT fixtures so an LLM-authored model is differentially tested, not trusted.

## Automation & tooling (git-clone-runnable)

Dedicated, mature, locally present:

- **OR-Tools CP-SAT** — Apache-2.0, **v9.15.6755 (2026-01-12)**, installed. State-of-the-art finite-domain solver, certificate-capable, Python/C++/Java/.NET. Production-grade.
- **clingo (Potassco)** — MIT, **v5.8.0**, installed. ASP grounder+solver; ideal when the CLASS/AUTH model wants closed-world negation and easy enumeration of *all* counterexamples.
- **Z3** — MIT, **v4.16.0**, installed. SMT superset: use when domains stop being finite (linear arithmetic, bitvectors for exact overflow, arrays) — the same UNSAT-as-proof discipline with richer theories.
- **MiniZinc** — MPL-2.0, **v2.9.7 (2026-04-30)**, *not* installed but `pip`/snap-trivial. Solver-independent modeling language; one `.mzn` retargets Chuffed, Gecode, CP-SAT, making it the natural **INDEP** diversity layer (solve the same model on two engines, diff verdicts).

No encoding gap exists: this is the one survey area where the dedicated tools *are* the deliverable. The recommendation is CP-SAT as primary engine, MiniZinc as the portable model + cross-solver oracle, Z3 when the domain escapes finiteness.

## Honest leverage & kill-condition

**Load-bearing** wherever the obligation reduces to "no configuration in a finite/boundable space violates property P": CLASS, CONSIST (with MUS localization), STRUCT range-safety, COHERE config drift, TRACE feasibility. Here the UNSAT certificate is a genuine ∀-proof — strictly stronger than any sampled test suite, and the green is not a costume.

**Ash** wherever the real property is temporal-unbounded or about justification. BMC's INV guarantee is **bounded to depth k**; calling a bounded check an invariant proof is precisely CALIB's "wrong bar" failure.

**Falsifiable experiment:** take an autoharn INV obligation (dam spillway level barrier) with a counterexample known to require depth d. Run BMC at the largest k feasible under the harness time budget. **KILL CONDITION:** if the shallowest real counterexample lies beyond feasible k — so SAT reports "no violation ≤ k" while the system *can* violate at k+1 — then SAT/CP is **disqualified as an invariant oracle for that obligation** and must be downgraded to a bug-*finder*, ceding the proof to an unbounded method (k-induction, IC3/PDR, or a temporal model checker). The kill is specific to unbounded INV/PROG; it does not touch the finite CLASS/CONSIST/COHERE assignments, where SAT remains decisive.

## References (edification)

- **Biere, Heule, van Maaren, Walsh, *Handbook of Satisfiability*, 2nd ed. (2021)** — the field's reference: CDCL, unsat cores/proofs (DRAT), and BMC; teaches why UNSAT-with-certificate is the real product.
- **Rossi, van Beek, Walsh, *Handbook of Constraint Programming* (2006)** — propagation, global constraints, consistency levels; the modeling discipline behind CLASS/COHERE encodings.
- **Krupke, *The CP-SAT Primer* (d-krupke.github.io/cpsat-primer, living)** — hands-on, idiomatic OR-Tools 9.x; the fastest path to a runnable autoharn check.
- **Biere et al., "Bounded Model Checking" (*Advances in Computers*, 2003)** — the canonical statement of BMC's reach *and* its depth bound; teaches exactly where the kill-condition bites.

Sources: [OR-Tools releases](https://github.com/google/or-tools/releases), [MiniZinc downloads](https://www.minizinc.org/downloads/), [MiniZinc license](https://www.minizinc.org/license/).


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
