# 07 — Paraconsistent & Many-valued Logic

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)**.

Logics that admit more than two truth values (e.g. Kleene's *unknown*, Belnap's *both*) and that **tolerate contradiction without exploding** — from `A ∧ ¬A` a classical engine derives *everything*; a paraconsistent one derives nothing extra. It lets contradictory facts coexist as data.

## Primer

You already use a many-valued logic daily: SQL `NULL`. `WHERE promoted AND tree_clean` returns a row only when the predicate is **TRUE**; if `tree_clean IS NULL` (unknown), the row is silently withheld — that is Kleene's strong three-valued logic K3 (`true / false / unknown`). Belnap's **FOUR** adds a fourth value, **both**, for *contradiction*: when two sources assert opposite things, you tag the claim `both` instead of letting one win or letting the contradiction poison every other inference. The core move: replace classical negation-as-failure ("if I can't prove clean, it's dirty") with an **explicit value lattice** where `unknown` and `both` are first-class, queryable states. Reach for this exactly when you must **store a conflict you have not yet resolved** and keep reasoning around it — and when "absence of proof" must not silently become "proof of absence." It is the logic of *suspended judgment*.

## Applicability to autoharn

**1. Conflicting advisories / not-yet-corroborated findings COEXIST without the gate exploding (CROSS-CUTTING; high).** This is the textbook use. Two advisories disagree; classical CI logic that treats the store as a consistent theory would let `A ∧ ¬A` justify *any* gate result. Belnap's `both` contains it. In clingo (locally: **5.8.0**), model the value explicitly rather than via classical negation:

```prolog
truth(C, both) :- advises(A1,C,true), advises(A2,C,false), A1 != A2.
truth(C, true) :- advises(_,C,true),  not truth(C, both).
:- promoted(C), truth(C, both).      % CI gate: a 'both' claim cannot be promoted
```

The integrity constraint fails CI *only* for the conflicted claim; unrelated facts still derive cleanly. This beats a Python script because non-monotonic *containment* (the `not truth(C,both)` guard) is declarative, not a pile of `if` branches, and beats Z3 because you want the *model* (which claims are `both`), not UNSAT.

**2. The DIRTY tag / "a benchmark on a DIRTY git tree must NOT be promoted to confirmed" (PILLAR 2; high).** The third value *is* `dirty`. Native Postgres K3 already enforces it — no new engine:

```sql
-- truth ∈ {confirmed=TRUE, refuted=FALSE, suspect/dirty=NULL}
SELECT claim_id FROM findings
WHERE promoted AND tree_clean IS NOT TRUE;   -- dirty/unknown rows surface as violations
```
A `<store>_violations` gate is literally "this K3 query is non-empty." High fit, and it costs nothing — SQL's three-valued semantics is the mechanism. The teach: don't coerce `dirty` to `false`; keep it as the missing-third value so `honest-NULL` is representable.

**3. status lifecycle provisional/confirmed/retracted (CROSS-CUTTING; med–high).** Map the lifecycle onto a truth lattice (`retracted < provisional < confirmed`) and let supersession only move *up* the lattice. clingo expresses the monotone constraint directly; plain SQL can store the states but cannot cheaply enforce "no claim regresses without a SUPERSEDES row."

**4. statistical hunch vs provable truth (CROSS-CUTTING / probabilistic; med).** **PyReason**'s *generalized annotated logic* labels each atom with an interval `[lower, upper]`; `[1,1]` = proven, `[0.7,1]` = a hunch, and `lower > upper` *is* detected inconsistency (auto-reset to `[0,1]`, total uncertainty). This bridges the maintainer's axis without faking a single probability:

```python
pr.add_fact(Fact('regression(commit_abc) : [0.7, 1.0]'))   # a hunch, not a claim
pr.add_rule(Rule('confirmed(x) <-1 fast(x), clean_tree(x)', 'r1'))
```
Med, not high: it's a real fit, but the interval algebra is more machinery than most autoharn rows need, and PyReason's Python-version ceiling (below) hurts.

**Honest forced fit:** PILLAR 1 classification, the SUPERSEDES *chain*, and pre-registration *temporal* ordering are **not** paraconsistency problems — they are vocabulary/recursion/temporal problems better served by plain SQL `WITH RECURSIVE`, Datalog, or temporal logic. Many-valued logic only earns its keep where **conflict or unknown must persist as a value**.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **PostgreSQL** (18.3 local) | native K3 three-valued (`NULL`=suspect/dirty); the cheap win | PostgreSQL (BSD-like) | SQL; any client | **already installed** | very high | very high — every model knows SQL |
| **clingo / Potassco** (5.8.0 local) | encode Belnap `both`, gates as integrity constraints, non-monotonic defaults | MIT | C++; first-class Python (`pip install clingo`) | **already installed** | very high | high — small ASP programs; some idiom risk |
| **PyReason** (lab-v2, 0.x) | annotated `[l,u]` intervals, inconsistency-reset, temporal/graph | BSD-3 (repo) | Python (numba) | **pip, but Py 3.7–3.10 only** → separate venv; autoharn is **3.13** | research-grade, 0.x | medium — niche syntax, sparse examples |
| SWI-Prolog (9.3.31 local) | hand-roll a 4-valued meta-interpreter if you must | BSD-2 | Prolog/C | already installed | very high | medium |

The pragmatic stack: **Postgres for the dirty/suspect third value, clingo for the `both`/non-monotonic gate.** PyReason is worth a spike only for the probabilistic axis — and note its hard Python-3.10 ceiling means it cannot live in the `generic` 3.13 venv.

## Limits & honest take

Substance: the `suspect/dirty` third value and contained `both` are *exactly* what the brief asks for, and Postgres delivers them for free. Hype: "paraconsistent AI reasoning" is mostly marketing; you do not need exotic logic — you need to **stop coercing unknown to false**, which is a schema discipline, not a solver. PyReason's neuro-symbolic framing oversells; for autoharn it's an interval store with inconsistency detection.

The real danger is **false authority**: an LLM that mis-encodes the lattice — writes classical `not` where it meant `truth(C,both)`, or treats `[0,1]` "I have no idea" as `[1,1]` "proven" — produces a clingo model or a PyReason bound that *looks* like a proof and gates CI confidently wrong. Paraconsistency makes this worse in one way: it won't crash on the contradiction that would otherwise reveal the bug. Mitigation, on-brand for autoharn: treat every encoding as a finding needing a Witness, and unit-test the value lattice itself (assert `both` blocks promotion, assert `unknown ≠ false`) before trusting any gate built on it.

## References & learning

- **Belnap, "A Useful Four-Valued Logic" (1977)** — the founding `true/false/both/none` lattice; teaches *why* `both` belongs in a database of conflicting sources.
- **Priest, *An Introduction to Non-Classical Logic* (2nd ed.), ch. on LP/K3** — clean exposition of paraconsistency and many-valued semantics for an engineer.
- **Potassco clingo guide (potassco.org/clingo)** — how to write integrity constraints and non-monotonic defaults; the engine you'd actually run for the `both`-gate.
- **PyReason paper, CEUR Vol-3433 / github.com/lab-v2/pyreason** — annotated-interval semantics and inconsistency-reset, for the statistical-hunch-vs-truth spike.

Sources: [PyReason GitHub](https://github.com/lab-v2/pyreason), [PyReason paper](https://ceur-ws.org/Vol-3433/paper17.pdf), [clingo GitHub](https://github.com/potassco/clingo), [Potassco](https://potassco.org/clingo/)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
