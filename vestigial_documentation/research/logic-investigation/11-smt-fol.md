# 11 — SMT & Classical First-order Logic (Z3 / cvc5)

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

SMT (Satisfiability Modulo Theories) solvers decide quantifier-rich formulas in classical first-order logic enriched with background *theories* (linear arithmetic, arrays, strings, datatypes, bitvectors) — answering SAT (here is a model) or UNSAT (no model exists, optionally with a proof/unsat-core). Z3 and cvc5 are the two production engines.

## Primer

You already think in SQL (find rows satisfying a `WHERE`) and have seen Z3 solve puzzles. The leap: SMT does not search *over a fixed table* — it searches *over all possible interpretations of declared symbols* until it finds one that satisfies your constraints, or proves none can. Two concepts carry the weight. **(1) Models vs. proofs of impossibility.** `check()` returning `unsat` is a *universal* claim ("no assignment works"), which SQL can never give you — SQL only reports what is present. **(2) Unsat cores.** When constraints conflict, the solver hands back the *minimal subset* that is contradictory — a built-in blame assignment. SMT is the right tool when your question is "is this *consistent / always true / impossible*?" over open-ended values, not "which stored rows match?". Use it for feasibility, invariant-checking, and conflict detection; reach for SQL when you are filtering known data and for CP-SAT when you are *optimizing* over finite choices.

## Applicability to autoharn

**1. "what does this tool PROVE" task-shape → blessed-tool mapping (Pillar 1).** High. autoharn's own registry *names SMT as the answer to "feasibility"*. The eliciting mechanism is itself a tiny SMT query: given a declared task-shape, is the blessed-tool assignment forced/consistent?

```python
from z3 import *
shape = String('shape'); tool = String('tool')
s = Solver()
s.add(Implies(shape == StringVal("feasibility"),     tool == StringVal("smt")))
s.add(Implies(shape == StringVal("finite-enum"),     tool == StringVal("cp-sat")))
s.add(Implies(shape == StringVal("convex-alloc"),    tool == StringVal("cvxpy")))
s.add(shape == StringVal("feasibility"), tool != StringVal("smt"))
print(s.check())   # unsat  => the mapping is violated; CI fails
```

This beats a SQL lookup because it checks the *rule's* consistency, not a row's presence — you can prove "no task-shape maps to two tools" with one `unsat`.

**2. Classification discipline: lib xor solver xor service xor venv xor script (Pillar 1).** High. The closed-vocabulary, mutually-exclusive constraint is the textbook SMT idiom; an `unsat` is a hard CI gate, and the **unsat-core points at the offending pair of class predicates** — strictly more than a SQL `CHECK`.

```python
lib,solver,service,venv,script = Bools('lib solver service venv script')
s = Solver(); s.add(PbEq([(lib,1),(solver,1),(service,1),(venv,1),(script,1)], 1))
s.add(lib, solver)          # a capability tagged both
print(s.check())            # unsat
```

`PbEq(...,1)` = "exactly one" — declarative where SQL needs a hand-rolled trigger.

**3. Pre-registration temporal ordering & perf-claim substantiation (Pillar 2).** Med. SMT can encode the *temporal invariant* ("criterion committed BEFORE result") and the substantiation rule ("every perf token references a stored reading OR carries `[unsubstantiated]`") as a satisfiability check over integer timestamps and booleans:

```python
t_crit, t_result = Ints('t_crit t_result')
has_reading, marked = Bools('has_reading marked')
s = Solver()
s.add(t_crit < t_result)                       # pre-registration
s.add(Or(has_reading, marked))                 # no naked perf-claim
```

Why not SQL: timestamps *are* well stored in Postgres, and a `WHERE t_crit >= t_result` violations-view is honestly the better gate here. SMT only wins once you combine many such temporal+logical constraints and want a *single* consistency verdict with a core. Honest rating: **forced** for the standalone ordering check, **med** for the bundled invariant.

**4. DIRTY / paraconsistency 3-valued coexistence (cross-cutting).** Med. Classical SMT is *not* paraconsistent — adding a fact and its negation yields global `unsat` (explosion), exactly what autoharn forbids. The honest workaround is to *reify* truth as a sort `{confirmed, suspect, retracted}` so contradictory advisories sit as different enum values rather than `P ∧ ¬P`:

```python
V, (conf, susp, retr) = EnumSort('V', ['confirmed','suspect','retracted'])
a = Const('finding_a', V)
# two advisories disagree -> resolve to suspect, NOT a contradiction
```

This works but is a *forced* fit; an Answer-Set/paraconsistent engine models the "coexist without exploding" requirement more natively.

**5. Logic safety-net `<store>_violations` gates (Pillar 3).** Med-low. SMT is excellent for *class-of-defect* checks (Rule 4) where the defect is "a structural slot can be assigned two incompatible values" — provable once, no instance enumeration. But the everyday `WITH RECURSIVE` violations-views (supersedes-chain reachability, dangling mechanism refs) are graph reachability, which Datalog/Postgres does better and cheaper. Use SMT for the *forced-assignment* gates, Datalog for the *reachability* gates.

Where SMT clearly **beats** alternatives: any question phrased "can these constraints ever hold together?" (consistency, exclusivity, forced mappings) — SQL cannot say `unsat`, CP-SAT is overkill without an objective, and a Python script gives a *false* universal ("I tried 100 cases") whereas SMT gives a *real* one.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|------|------|---------|---------------------|--------------|----------|------------------|
| Z3 4.16.0 (Feb 2026) | primary SMT engine; QF + quantifiers, strings, optimization (νZ) | MIT | C++ core; Python (`z3-solver`), C, .NET, Java, JS, OCaml; SMT-LIB2 CLI | `pip install z3-solver` (trivial); **already in `venvs/generic` 4.16.0** | very high, industry standard | very high — most-represented SMT API in training data, Pythonic |
| cvc5 1.3.4 (May 2026) | second-opinion / cross-check engine; strong on strings, datatypes, quantifiers, proofs | BSD-3-Clause | C++ core; Python (`cvc5`, incl. a Z3-compatible "pythonic" API), Java, SMT-LIB2 CLI | `pip install cvc5` (trivial); **not currently installed** | high, actively developed | high — pythonic API mirrors Z3, so prompts transfer |

Both speak standard **SMT-LIB2**, so autoharn can store models as portable text and run Z3 *and* cvc5 on the same file as a differential check (disagreement = encoding bug).

## Limits & honest take

The headline risk for autoharn is **false authority**: an LLM emits a model, the solver prints `unsat`, and everyone treats it as proven truth — but the *encoding* may not match reality. `unsat` only means "your formula has no model," not "your claim is correct." A dropped constraint, a `BitVec` overflow silently wrapping, or `Int` vs `Real` confusion produces a confident, wrong proof. This is precisely the perf-claim hazard Pillar 2 guards against, now wearing a tuxedo. **Mitigations to mechanize:** (a) always check the *negation* too — `sat` on both a claim and its negation means the model is under-constrained; (b) inspect the `model()` on `sat` and the `unsat_core()` on `unsat` and store them as *readings*, separate from the interpretation; (c) cross-run Z3 vs cvc5. Other limits: SMT is **not paraconsistent** (contradictions explode — bad for the DIRTY/coexist shape), gives **no probabilities** (cannot serve the "statistical hunch" axis), and **does not do abduction or ILP** (hypothesis-generation and rule-learning need other tools). Quantified/nonlinear/string formulas can hit **`unknown` or timeout** — an honest-NULL, never to be rounded up to `unsat`. Net: indispensable for *consistency and exclusivity* gates, wrong tool for *reachability, learning, and uncertainty*.

## References & learning

- **Z3 Guide / "Programming Z3" (Bjørner, de Moura, Nelson) — rise4fun.com/z3 & microsoft.github.io/z3guide** — the canonical interactive tutorial; teaches the SAT/UNSAT/model/core loop hands-on.
- **de Moura & Bjørner, "Satisfiability Modulo Theories: Introduction and Applications" (CACM 2011)** — the readable conceptual overview of what "modulo theories" buys you over plain SAT.
- **Kroening & Strichman, *Decision Procedures: An Algorithmic Point of View* (2nd ed.)** — teaches *why* each theory is decidable, so you can predict when SMT will return `unknown`.
- **cvc5 docs (cvc5.github.io/docs/latest) + the pythonic API page** — shows the Z3-compatible Python surface, enabling drop-in differential cross-checking.

Sources: [Z3 GitHub](https://github.com/Z3Prover/z3), [z3-solver PyPI](https://pypi.org/project/z3-solver/), [cvc5 PyPI](https://pypi.org/project/cvc5/), [cvc5 releases](https://github.com/cvc5/cvc5/releases/).


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
