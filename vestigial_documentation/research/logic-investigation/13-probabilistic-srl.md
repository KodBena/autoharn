# 13 — Probabilistic Logic & Statistical-relational AI (ProbLog / PSL / MLN)

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

A family of logics that attach **degrees of belief** to logical rules/facts, so deduction returns a *probability* (or a soft truth in [0,1]) instead of a hard yes/no — the formal home for autoharn's "statistical hunch vs provable truth" axis.

## Primer

You know Z3: facts are true/false and a model either exists or doesn't. Probabilistic logic relaxes that. In **ProbLog** you write Prolog rules, but each fact can carry a weight: `0.8::flaky(T)` means "T is flaky with probability 0.8." A query like `regression(R)` returns `P(regression)=0.34`, computed by summing over all possible worlds consistent with the rules (via weighted model counting under the *distribution semantics*). Two concepts matter: (1) **possible-worlds marginalization** — the engine enumerates which probabilistic facts hold and weights each world; (2) **soft truth** (in PSL/MLN) — rules can be *partially* satisfied, so contradictory evidence degrades a conclusion smoothly instead of making the theory `UNSAT`. Reach for this exactly when your inputs are *noisy or corroborative* — many weak signals that should *combine* into a calibrated confidence — and a crisp SAT/Datalog gate would either explode on contradiction or force you to fake a threshold.

## Applicability to autoharn

**1. "statistical hunch vs provable truth" bridge (cross-cutting) — strength: HIGH.** This is the one need that *only* a probabilistic logic serves. The maintainer's hunch ("this benchmark looks like a regression") is a marginal, not a theorem. ProbLog lets a hunch and hard provenance share one program:

```prolog
0.7::noisy_machine.
slowdown(B) :- reading(B,T), baseline(B,T0), T > 1.2*T0.
0.9::real_regression(B) :- slowdown(B), \+ noisy_machine.
query(real_regression(bench_solve)).
```

Beats SQL (no marginalization) and Z3 (forces a Boolean it doesn't have). The hunch becomes a *number*, gating promotion to `confirmed`.

**2. Abduction / hypothesis generation for a regression (Pillar 3 shape) — strength: HIGH.** "Generate hypotheses to explain a regression" is literally abductive inference, ProbLog's home turf. Given an observed slowdown, ask which probabilistic causes (`new_z3_version`, `dirty_tree`, `cold_cache`) best explain it, ranked by posterior:

```prolog
0.3::new_solver_ver.  0.2::cold_cache.  0.5::dirty_tree.
slow :- new_solver_ver.   slow :- cold_cache.
evidence(slow,true).
query(new_solver_ver).   query(cold_cache).
```

Returns `P(cause | slow)` for each — a *ranked* hypothesis list. A Python script could do this with hand-rolled Bayes; ProbLog gives it declaratively with the same fact store the rest of autoharn uses.

**3. Paraconsistent coexistence of conflicting advisories (cross-cutting) — strength: MED.** The requirement that "conflicting advisories COEXIST without the gate exploding" is partly served here: **PSL/MLN never go UNSAT.** Two rules `advisory_A => prefer(cvxpy)` and `advisory_B => prefer(scs)` both partially satisfied yield a *soft* preference, not a contradiction. PSL syntax:

```
2.0: Advisory(A) & Recommends(A, T) -> Prefer(T) ^2
```

The `^2` makes it a hinge-loss the convex solver minimizes; conflict produces a blended weight rather than an explosion. Honest caveat: autoharn's DIRTY/suspect third value (Pillar 2) is better modeled by a *Kleene/3-valued Datalog gate* than by probabilities — using a continuous truth value to encode "unknown" is a forced fit and loses the audit clarity of a discrete tag.

**4. Liveness as a refreshable, decaying belief (Pillar 1) — strength: MED.** "A REFUTED resource belief must be superseded, not silently stale" has a probabilistic reading: belief in a capability's liveness *decays* with staleness. `0.95::alive(z3)` last verified 40 days ago could be down-weighted by a rule on `age`. But this is genuinely better done by the **provenance ledger's supersession chain + a TTL** (deterministic, auditable) than by a probability nobody calibrated — rate MED precisely because the deterministic mechanism is more honest.

**Forced / weak fits (stated for honesty):** sharp **classification discipline** (Pillar 1: lib xor solver xor service) is *anti*-probabilistic — its whole point is "NO fuzzy match," so soft logic is the wrong tool; use a closed-vocabulary CHECK constraint. **Pre-registration** and **append-only SUPERSEDES** are temporal/structural, not probabilistic. **Logic-safety-net `_violations` gates** want crisp non-empty results (Datalog/SQL), not marginals.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **ProbLog 2.2.10** (ML-KULeuven) | distribution-semantics PLP; marginals, abduction, MAP | Apache-2.0 | Python lib + CLI; pure-py core | `pip install problog` — **but PyPI lists ≤Py3.12**; venv is 3.13, so test/compile or pin a 3.12 venv | mature, actively released (Mar 2026) | High — Prolog-like, terse, scriptable from Python; easy to feed from SQL |
| **PSL 2.x** (linqs) | scalable soft logic via convex (hinge-loss) inference | Apache-2.0 | Java core (needs JRE 8+); Python `pslpython` wrapper + CLI | JVM dependency = medium/heavy; `pip install pslpython` for the wrapper | mature, research-grade, scales to large relational data | Medium — clean rule DSL, but JVM + data/predicate file setup is verbose |
| **pracmln** (danielnyga) | Markov Logic Networks (weighted FOL) | BSD-2 | pure Python + CLI/GUI | `pip` (pure-py) | **effectively unmaintained** (~50 dl/wk, last touched ~2018) | Low/Med — Python but stale; risky to depend on |
| **PyMC / pgmpy** (fallback) | plain Bayesian / factor-graph inference | Apache-2.0 / MIT | Python | `pip` | mature | High — but *not relational*; you lose the logic layer |

Local check: `problog` **not installed**; SWI-Prolog **9.3.31 present** (ProbLog's pure-Python core does not require it). No PSL/MLN installed.

## Limits & honest take

Most of autoharn is **deterministic by design** — the Mechanization Discipline wants crisp, auditable gates, and a probability is the enemy of "never seen twice." Probabilistic logic earns its place in exactly three corners: the hunch→confidence bridge, regression abduction, and softly-blended advisories. Everywhere else it is a forced fit that *trades auditability for a number nobody calibrated.*

The sharpest failure mode is **false authority**: an LLM that mis-encodes a weight (`0.9` vs `0.09`), inverts evidence, or forgets the independence assumption baked into the distribution semantics will get a *confidently precise wrong probability* — far more dangerous than a Z3 `UNSAT`, because there is no contradiction to trip the gate. Mitigation: store every weight with its *provenance* (which reading justified `0.7`?), pin queries to a known answer in CI, and treat any probability lacking a cited reading as `[unsubstantiated]` exactly like a perf-claim token. Calibration is unsolved here — the numbers are only as good as the maintainer's elicited priors. Hype check: PSL/MLN "scale to millions of facts" is real but irrelevant at autoharn's size; the value is *expressiveness*, not scale.

## References & learning

- **De Raedt, Kimmig & Toivonen, "ProbLog" (IJCAI 2007)** — the original distribution-semantics paper; teaches *why* weighted model counting gives sound marginals.
- **ProbLog docs & tutorial** (https://problog.readthedocs.io) — copy-pasteable Python-from-ProbLog examples; fastest path to a working abduction query.
- **Bach et al., "Hinge-Loss Markov Random Fields and Probabilistic Soft Logic" (JMLR 2017)** — the PSL foundations; teaches how soft truth becomes a *convex* (hence tractable) optimization, the reason PSL never goes UNSAT.
- **Richardson & Domingos, "Markov Logic Networks" (Machine Learning, 2006)** — the canonical MLN paper; teaches weighting *first-order* formulas and where the intractability lives.

Sources: [ProbLog PyPI](https://pypi.org/project/problog/), [ML-KULeuven/problog](https://github.com/ML-KULeuven/problog), [PSL linqs](https://psl.linqs.org/), [linqs/psl](https://github.com/linqs/psl), [pracmln PyPI](https://pypi.org/project/pracmln/)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
