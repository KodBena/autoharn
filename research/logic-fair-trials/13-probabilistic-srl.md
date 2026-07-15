# 13 — Probabilistic Logic & Statistical-relational AI (ProbLog / PSL / MLN) — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 3 defect(s) noted · **not rewritten** (the hardening pass was a no-op).

## Probabilistic Logic & Statistical-relational AI (ProbLog / PSL / MLN) — Fair Trial

The bet on trial: that distribution-semantics logic programming can make autoharn's *confidence* layer — the gap between a statistical hunch and a `confirmed` theorem — itself **provable and auditable**, by computing calibrated marginals over the same fact store the hard gates read, rather than burying that confidence in a hand-rolled Python threshold nobody can audit.

## Maximal ambition

The frontier claim: autoharn can carry a **second, quantified truth-channel that is itself a first-class auditable artifact**, not a vibe. Today `confirmed` is a Boolean wall; everything below it ("looks like a regression," "this machine is noisy," "this advisory probably applies") lives in prose, code comments, or a maintainer's head — *unauditable by construction*. ProbLog lets autoharn state the **promotion criterion as a program**: a reading is promoted from `suspect` to `confirmed` only when `P(real_regression | evidence) ≥ θ`, where θ, the rule weights, and the evidence are all stored, versioned, and replayable. Two things become possible that SQL/Z3-as-usual cannot:

1. **Marginalization over corroborating weak signals.** Five noisy indicators (slowdown ratio, dirty tree, solver-version bump, cold cache, prior flakiness) *combine* into one number with a sound semantics (weighted model counting), instead of an ad-hoc `score = 0.3*a + 0.2*b` that no auditor can defend.
2. **Abductive maintenance** — *deductive maintenance's missing half*. When a gate goes red, ProbLog ranks the probabilistic *causes* by posterior, turning "the benchmark regressed" into "P(dirty_tree)=0.69 ⊳ P(new_solver_ver)=0.42 ⊳ P(cold_cache)=0.28 — investigate the tree first." The ranked explanation is a maintenance artifact a script cannot produce declaratively from the shared store.

## The expressiveness gap (precise, not hand-wavy)

Be precise, because the prior section was right that most of autoharn is deliberately crisp. The gap is **#P / weighted model counting**, not NP. A regression's marginal `P(real_regression)` sums weighted satisfying worlds of a logic program with shared subgoals; that is `#P`-hard in general. SQL `GROUP BY ... SUM` computes a marginal *only* when you have pre-flattened every joint world into rows and the events are independent — the moment two rules share a latent fact (`noisy_machine` feeds both `slowdown_explained` and `flaky_history`), the naive SQL sum **double-counts** and silently returns the wrong probability. ProbLog's knowledge-compilation back-end handles the shared-variable correlation correctly; reproducing that in SQL means materializing the d-DNNF by hand — i.e., re-implementing the solver. *That* is the succinctness/semantics gap, and it is real. Where there is **genuinely no gap**: any single-rule, independent-event confidence (a lone TTL decay, a closed-vocabulary classification, an append-only supersession) is expressible as a SQL arithmetic view, and using ProbLog there is a forced fit that *loses* audit clarity — say so plainly.

## The falsifiable experiment (the trial)

**Setup.** Export the provenance ledger's last N benchmark readings to ProbLog facts (one query, deterministic). Encode the promotion criterion the maintainer would otherwise write in Python:

```prolog
% --- evidence emitted from the ledger (criterion-before-result) ---
slowdown(B) :- reading(B,T), baseline(B,T0), T > 1.2*T0.
0.85::machine_clean.                         % weight cited to reading r#4412
0.90::regression_if(B) :- slowdown(B), machine_clean.
0.20::regression_if(B) :- slowdown(B), \+ machine_clean.  % noisy-box path
real_regression(B) :- regression_if(B).
query(real_regression(bench_solve)).
```

Promotion rule: `suspect → confirmed` iff `P(real_regression) ≥ 0.80`.

**Success criterion.** On a labelled back-set of past incidents (true regressions vs known-noisy false alarms), the marginal-threshold gate must (a) reproduce the maintainer's eventual verdict on **≥ 90%** of cases, AND (b) on the held-out set be **calibrated** — Brier score materially better than the existing fixed-threshold heuristic, with the reliability curve inside ±0.1. The shared-fact case must beat a SQL `SUM` baseline on ≥1 incident where correlation matters (the double-count case above).

**KILL CONDITION (non-negotiable).** Retire ProbLog if EITHER: (1) on the back-set its calibration is **no better than** the fixed-threshold SQL heuristic (Brier within noise) AND no incident exercises shared-fact correlation — i.e., the #P expressiveness is never load-bearing on real data; OR (2) the weights cannot be sourced from cited readings and must be guessed, so every marginal carries an `[unsubstantiated]` token — meaning the number is decoration. Either outcome means the value is imaginary at autoharn's scale; ash.

## Neutralizing false authority (verification scaffolding)

False authority (the `0.9`-vs-`0.09` mis-encode, the silent independence assumption) is the central risk and an **engineering problem to solve**, not a retreat cue:

- **Mutation fixtures.** A golden corpus of `(program, query, expected_marginal±ε)` pinned in CI; the meta-sweep *mutates* each weight (`0.9→0.09`) and each evidence polarity and asserts the marginal **moves past a tripwire**. A mutation that leaves the answer unchanged is a dead rule — flagged. (Verified runnable: flipping `dirty_tree 0.5→0.05` shifts its posterior from 0.69 to ~0.16.)
- **Differential / bounded cross-check.** Re-encode the same program as an MLN (pracmln) or a Z3 weighted-model-count and require agreement to ε; divergence = encoding bug, not a verdict.
- **Back-translation gate.** Each rule auto-renders to English ("a clean machine makes a slowdown a regression with prob 0.90") for maintainer sign-off before the weight is admitted; the rendering is stored.
- **Reading-with-provenance for every weight.** No bare constant: `0.85::machine_clean` must carry `{cited_reading_id, commit, tree, session_id}`; a weight lacking provenance is `[unsubstantiated]` and the gate refuses to promote — exactly the perf-claim discipline (P2).
- **Justification-carrying output.** Use ProbLog's proof/explanation to emit *which worlds* drove the marginal, stored alongside the verdict so the green gate is inspectable, not oracular.

## Verdict: phoenix or ash — and how we'll know

**Undecided-until-trial, leaning cautious-phoenix in exactly one corner.** The honest position: ProbLog is a phoenix *iff* real autoharn incidents exhibit shared-latent-fact correlation (where SQL provably miscounts) AND weights are sourceable from cited readings; it is ash if every confidence reduces to an independent single-rule threshold. The **single settling experiment** is the calibration back-test above: run the marginal gate against the labelled incident history and compare Brier + correlation-handling to the SQL heuristic. Evidence that flips me to firm phoenix: ≥1 incident where the SQL sum double-counts a shared cause and ProbLog gets it right, plus better calibration. Evidence that flips me to ash: the kill condition — calibration parity and no correlation ever bites. No retreat to "use SQL instead": the experiment *decides* whether the #P channel earns its place, and it runs today on the installed 2.2.10.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
