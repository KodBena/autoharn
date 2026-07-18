# 01 — Datalog & Deductive Databases

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

A deductive database stores explicit facts and **Horn-clause rules** (`head :- body`) and computes the least fixpoint — every consequence the rules force — automatically and to termination. It is SQL's recursion done right: declarative, set-at-a-time, with transitive closure as a first-class citizen.

## Primer

You know SQL `JOIN` and you know Z3's "is there a model?". Datalog sits between them. Like SQL it's relational and bottom-up; unlike SQL, **recursion is native and total** — a rule may call itself, and the engine iterates `rule → new facts → rule` until nothing new appears (the least fixpoint). Like Z3 it's logic, but it does *deduction* (derive all entailed facts) not *search* (find one satisfying assignment). That's the intuition for *when*: reach for Datalog whenever the question is "given these base facts and these closure rules, what is *everything* that follows?" — transitive chains, reachability, "does any bad pattern exist?" The two concepts that matter: **fixpoint** (rules apply until saturation) and **stratified negation** (`not p` is allowed only when `p` is fully computed first, so negation stays well-defined). A `violations` relation that is empty iff the database is healthy is the canonical Datalog idiom — and exactly autoharn's gate shape.

## Applicability to autoharn

**SUPERSEDES chains / ADR-amendment supersession (Pillar 2) — fit: HIGH.** The append-only ledger with `Witness→Correction` is a graph; "what is the *live* finding?" is transitive closure with negation — a query SQL expresses only as awkward `WITH RECURSIVE`, and which Datalog states in two lines:

```prolog
live(F)      :- finding(F), not superseded(F).
superseded(F):- supersedes(_, F).
superseded(F):- supersedes(G, F), superseded_chain... % closure
chain(A,C)   :- supersedes(A,C).
chain(A,C)   :- supersedes(A,B), chain(B,C).
```

Beats Z3 (no search needed) and beats a Python script (the closure + non-monotonic "latest wins" is declarative, not a hand-rolled graph walk that drifts).

**Per-store `<store>_violations` CI gates (Pillar 3) — fit: HIGH, the flagship.** Each gate is literally a Datalog relation that must be empty. The brief prototypes these in Postgres `WITH RECURSIVE`; Datalog is the same semantics with far less ceremony, and *the same source* can prototype in Postgres and compile to a fast Soufflé checker. Pre-registration (temporal: criterion committed before result):

```prolog
preg_violation(R) :- result(R, Crit, T_res),
                     criterion(Crit, T_decl),
                     T_decl >= T_res.        % judged-by post-hoc criterion
```

Dirty-tree promotion ban:

```prolog
dirty_promotion(R) :- result(R), tree(R, dirty), status(R, confirmed).
```

CI fails iff `dirty_promotion` is non-empty. Beats plain SQL on the *uniformity* — every gate is one relation, mechanically swept — and beats a script because emptiness-of-a-derived-relation *is* the contract.

**Rule 4: keys on the CLASS of a defect, never instances (Pillar 3) — fit: HIGH.** This is Datalog's whole nature. A rule head matches a *structural shape* (a slot, a name-pattern, a derived-from-one-source join), quantifying over all rows, so the net can never degrade into an enumeration of known-bad instances:

```prolog
% derived-from-one-source: a "reading-of" stored as data
conflation(X) :- measurement(X, V), interpretation(X, V).
```

That one clause forbids the entire class "measurement kept together with interpretation" (Pillar 2) without listing a single instance.

**META-SWEEP: every rule declares an enforcement surface; every named mechanism resolves on disk (Pillar 3) — fit: MED-HIGH.** Datalog can reason over *its own* rule catalog as facts:

```prolog
unenforced(Rule) :- discipline_rule(Rule), not declares_surface(Rule).
dangling(M)      :- mechanism(M, Path), not exists_on_disk(Path).
```

`exists_on_disk` is supplied as an extensional fact from a filesystem scan — clean separation of EDB (facts you load) from IDB (facts you derive). Beats SQL only marginally here; the win is co-locating meta-rules with the rules they sweep.

**Capability classification: lib xor solver xor service xor venv xor script (Pillar 1) — fit: MED.** Datalog can *flag* violations of the exclusive partition, but cannot *enforce* exclusivity at write time (no constraints):

```prolog
class_violation(C) :- kind(C, K1), kind(C, K2), K1 != K2.
```

Honest note: this is a detector, not a guarantee — for true mutual-exclusion-by-construction Z3/CP-SAT or a DB `CHECK` is better. Datalog earns its place only because the *same* `_violations` machinery already runs in CI.

**Liveness / refuted-belief supersession, status lifecycle provisional/confirmed/retracted (Pillar 1, cross-cutting) — fit: MED.** Non-monotonic "default unless overridden" maps to stratified negation (`live :- believed, not refuted`). Genuinely good fit, but plain Datalog has **no probabilities** and a thin notion of the 3rd "suspect/unknown" value.

**Honest non-fits:** abduction (hypothesis generation for a regression), ILP (learning rules from examples), and the "statistical hunch vs provable truth" probabilistic axis are **out of scope** for classical Datalog — those want ASP/abductive engines, an ILP system, or ProbLog. Paraconsistency (conflicting advisories coexisting without the gate exploding) is *forced* in pure Datalog: you must reify a `suspect` truth value yourself rather than get it from the logic.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **Postgres `WITH RECURSIVE`** | prototype gates, de-facto Datalog | PostgreSQL (BSD-ish) | SQL; psql/psycopg | already installed | very high | high — ubiquitous SQL |
| **Soufflé 2.5** | compile gates to fast native checkers | UPL-1.0 | `.dl` DSL; C++; CLI, CSV/SQLite I/O | compile-from-source / apt | high (Oracle Labs, static-analysis grade) | high — clean Horn syntax |
| **SWI-Prolog 9.3.31** | quick interactive Datalog/closure | BSD-2 | Prolog; `pyswip`, CLI | **already installed** (`/usr/bin/swipl`) | very high | med — needs cut/termination care |
| **clingo 5.8.0 (ASP)** | when you need search/negation/abduction | MIT | ASP; Python (`pip install clingo`) | **already installed** (`/usr/bin/clingo`) | very high | med — ASP idioms unfamiliar |

Local check confirmed: `swipl 9.3.31`, `clingo 5.8.0` both present; Soufflé absent (apt/source). Recommended path: **prototype every `_violations` gate in Postgres** (zero install, already the brief's plan), promote hot gates to **Soufflé** if CI gets slow.

## Limits & honest take

Datalog is a *deduction* engine, not a *search* or *learning* one: it will not generate the regression hypothesis (abduction), will not learn a rule from examples (ILP), and carries no probabilities — selling it for the "statistical hunch" axis is hype. It also cannot *enforce* a constraint at write time; it only *detects* a violation after the fact, so a green gate means "no violation found in current facts," not "impossible by construction." The sharpest danger for autoharn is **false authority**: an LLM that mis-encodes a rule — gets stratification wrong, fumbles a negation, models "superseded" backwards — produces a *confidently empty* `violations` relation and the gate passes while the invariant is broken. A Datalog "✓" is only as true as the encoding, and the encoding is exactly what's least reviewed. Mitigations that fit the Mechanization Discipline: **golden-test every gate** with known-bad fixtures that *must* light it up (a violation-of-the-violations-check), keep EDB/IDB separated so loaded facts are auditable apart from derived ones, and treat any rule with negation as presumptively decaying until its stratification is tested. Substance over enthusiasm: Datalog is genuinely excellent for the three *closure/gate/class-key* needs and merely adequate-or-forced for classification, paraconsistency, and anything probabilistic.

## References & learning

- **Abiteboul, Hull, Vianu, *Foundations of Databases* (free PDF, webdam.inria.fr)** — Ch. 12–15 teach Datalog semantics, the fixpoint, and stratified negation rigorously; the canonical reference for *why* the gate idiom is well-defined.
- **Soufflé tutorial (souffle-lang.github.io/tutorial)** — teaches the real `.dl` syntax you'd ship, including components and the CSV/SQLite I/O that lets gates read your Postgres stores.
- **"What You Always Wanted to Know About Datalog (And Never Dared to Ask)," Ceri/Gottlob/Tanca (1989)** — the friendliest deep intro to recursion, safety, and evaluation strategies; teaches the intuition behind termination.
- **Potassco clingo guide (potassco.org)** — teaches ASP for the moment a gate needs genuine negation/search or abductive hypothesis generation, where pure Datalog stops.

Sources: [souffle-lang GitHub](https://github.com/souffle-lang/souffle), [Soufflé 2.5 release](https://souffle-lang.github.io/release-2.5.0.html), [clingo PyPI](https://pypi.org/project/clingo/), [potassco clingo](https://potassco.org/clingo/)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
