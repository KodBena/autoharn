# 03 — Answer Set Programming (clingo / DLV)

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)**.

ASP is a declarative logic-programming paradigm for combinatorial search and KR: you write rules over a finite domain, and the solver enumerates *answer sets* (stable models) — total assignments that justify themselves and satisfy every constraint. It is the natural engine for "find all worlds consistent with these defaults and exceptions."

## Primer

You know Z3 proves satisfiability over rich theories; you know SQL queries a fixed table. ASP sits between: like Datalog it computes a *minimal model* by least-fixpoint, but it adds **choice** (`{ p(X) } :- q(X).` — p *may* hold) and **stable-model semantics**, giving you genuine non-monotonic reasoning. Two concepts matter. (1) **Default negation `not`**: "conclude X unless there's evidence against it" — the textbook way to model defaults that later get overridden. (2) **Integrity constraints `:- body.`**: a headless rule that *kills* any model where `body` holds. So you generate candidate worlds with choice rules and prune them with constraints ("generate-and-test"), and the solver returns every surviving world — or `UNSATISFIABLE`. Reach for ASP when the question is "enumerate/optimize over the consistent configurations, with defaults and exceptions," not "is this one formula valid" (Z3) or "what rows match" (SQL).

## Applicability to autoharn

**Non-monotonic defaults & supersession (CROSS-CUTTING: "DEFAULTS later overridden", "supersession of ADR amendments") — fit: HIGH.** This is ASP's home turf and the single best reason autoharn would adopt it. A `SUPERSEDES` chain plus "the latest belief wins unless retracted" is exactly default negation. Postgres `WITH RECURSIVE` can *walk* a chain but cannot natively express "hold the default *unless* a superseding fact exists" without hand-rolled NOT-EXISTS scaffolding that breaks on cycles.
```prolog
holds(F) :- finding(F), not superseded(F).
superseded(F) :- supersedes(G,F), finding(G).
:- holds(F), retracted(F).   % a retracted belief can never be "live"
```
Add one fact `supersedes(corr1,witness1).` and `holds/1` recomputes — the prior is never rewritten, matching the append-only ledger.

**Logic-safety-net violation gates (PILLAR 3: `<store>_violations`) — fit: HIGH.** A violations gate is *precisely* an integrity constraint: a query whose non-empty result fails CI. ASP makes the gate a first-class object and, crucially, supports **Rule 4** (key on the *class* of defect, not instances) because constraints are universally quantified over variables:
```prolog
:- result(R), dirty(R), confirmed(R).   % dirty tree must NOT be promoted to confirmed
:- result(R), not has_commit(R), not honest_null(R).  % missing provenance => fail unless NULL-marked
```
These two lines enforce two pillar-2 invariants structurally; you cannot write them per-instance even if you wanted to. Why it beats SQL: the same source doubles as the *prover* of unsatisfiability and as a model-enumerator that hands you a counterexample world to debug. Why it beats Z3: closed-world finite enumeration is awkward to phrase as quantified SMT, and ASP grounds it for free.

**Classification discipline (PILLAR 1: lib xor solver xor service xor venv xor script) — fit: MED.** Mutual exclusion is a choice rule with cardinality:
```prolog
1 { class(C,lib); class(C,solver); class(C,service); class(C,venv); class(C,script) } 1 :- cap(C).
```
The `1 { … } 1` enforces *exactly one* — sharp classification, no fuzzy match. Honest caveat: a CHECK constraint / enum in Postgres does the same for stored rows more cheaply; ASP only wins here if classification is *derived* under defaults (e.g., infer class from features, overridable), otherwise it is forced.

**Abductive hypothesis generation for regressions (CROSS-CUTTING: abduction) — fit: MED-HIGH.** "What set of assumptions explains this regression?" is abduction, and ASP does it by making causes *choosable* and demanding the observation be entailed:
```prolog
{ cause(dirty_tree); cause(dep_bump); cause(config_drift) }.
explained :- cause(dirty_tree).      % (one rule per causal link)
:- not explained.                    % only models that explain the regression survive
#minimize { 1,C : cause(C) }.        % prefer the smallest explanation
```
Each answer set is a candidate diagnosis; `#minimize` gives parsimony. A Python script could brute-force this, but you'd reinvent minimality and consistency-checking that ASP gives natively.

**Paraconsistent coexistence of conflicting advisories (CROSS-CUTTING: 3rd "suspect" value) — fit: MED.** ASP is *not* paraconsistent by default (a hard contradiction yields no answer set — the gate "explodes"). The discipline is to model the third value explicitly as `suspect/1` rather than deriving `false`, so conflicting not-yet-corroborated findings coexist. Workable, but it's a modeling convention, not a free property — be honest that this is a forced-ish fit and a probabilistic/annotated logic may serve better.

**Weak fits:** pre-registration's *temporal* ordering (better as an append-only ledger + timestamp constraint), probabilistic "hunch vs proof" axis (needs LPMLN/ProbLog, not pure clingo), and ILP rule-learning (use ILASP/clingo's `xclingo` ecosystem, separate tool).

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **clingo 5.8.0** (Potassco; gringo+clasp) | grounder+solver, the default ASP engine | MIT | CLI; first-class Python `import clingo` (pip), C, Lua | **already on `/usr/bin/clingo`**; else `pip install clingo` (wheels) | very high, actively released (5.8.0 Apr 2025) | high — terse, well-documented syntax; abundant training data |
| **clorm** | Python ORM mapping clingo facts ↔ dataclasses | MIT | Python | `pip install clorm` | medium | high — bridges Postgres rows to ASP facts cleanly |
| **DLV2 / I-DLV** (UNICAL) | alt engine, strong SQL-ish front-end & external atoms | **free academic/non-profit only; commercial needs license** | CLI; Python via EmbASP | binary download; not pip | high | medium — smaller corpus, license friction |
| **ILASP / FastLAS** | inductive learning of ASP rules from examples (ILP) | academic/free | CLI, Python wrappers | download | medium | medium |
| **clingo[DL]/clingcon, LPMLN** | difference-logic & probabilistic extensions | MIT/academic | clingo plugins | with clingo | medium | lower — niche |

For autoharn: standardize on **clingo + clorm** (MIT, already installed, native Python — zero install cost, drives straight from Postgres). Avoid DLV2 unless its license clears, since autoharn is a public repo.

## Limits & honest take

ASP's reasoning is **closed-world and finite-domain**: it cannot do unbounded arithmetic feasibility (that's Z3) or continuous convex allocation (cvxpy) — don't force those. Grounding is the real failure mode: a careless rule over large domains causes a **grounding explosion** (combinatorial blow-up of instantiated rules) that hangs before solving — autoharn's stores must stay small or be filtered before they reach clingo. Pure clingo has **no native probability**, so the maintainer's "hunch vs provable truth" axis is not served without LPMLN/ProbLog; claiming otherwise is hype.

The sharpest danger for an *LLM-driven* workflow is **false authority**: ASP cheerfully returns `UNSATISFIABLE` or a crisp answer set for a model that is *subtly mis-encoded* — a flipped `not`, a missing constraint variable, a domain typo — and the result *looks* like a proof. A wrong choice rule silently enumerates phantom worlds; a too-strong constraint silently hides real ones, and there is no type system to catch it. Mitigation must be mechanized, not trusted: keep golden test programs with known answer sets, assert expected model *counts*, and treat any clingo verdict as a *witness to inspect*, never a verdict to quote. The "proof" is only as sound as the hand-written encoding — exactly the lapse-into-mechanism discipline autoharn exists to enforce.

## References & learning

- **Gebser, Kaminski, Kaufmann, Schaub — *Answer Set Solving in Practice* (Morgan & Claypool, 2012).** The canonical primer; teaches generate-and-test, choice rules, and constraints from scratch — read chapters 1-3 first.
- **Potassco clingo guide & Python API** (potassco.org/clingo, python-api/5.8). What you'll actually use day-to-day; teaches the real syntax and the embedding/control API for calling clingo from autoharn's Python.
- **Calimeri et al. — ASP-Core-2 standard** (the language spec). Teaches the portable subset so encodings survive an engine switch (clingo↔DLV2).
- **Kaminski et al. — "ASP-based Multi-shot Reasoning via DLV2 with Incremental Grounding" (TPLP, 2025).** Teaches incremental/multi-shot solving — directly relevant to re-running gates as the append-only ledger grows.

Sources: [potassco/clingo releases](https://github.com/potassco/clingo/releases/), [clingo on PyPI](https://pypi.org/project/clingo/), [clorm docs](https://clorm.readthedocs.io/en/latest/clorm/installation.html), [DLV homepage/license](https://dlv.demacs.unical.it/home), [DLV2 incremental TPLP 2025](https://www.cambridge.org/core/journals/theory-and-practice-of-logic-programming/article/aspbased-multishot-reasoning-via-dlv2-with-incremental-grounding/5CCCCCD550F3A544DE31B96EDE4F50DA).


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
