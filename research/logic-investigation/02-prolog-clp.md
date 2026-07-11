# 02 — Prolog & Constraint Logic Programming (SWI-Prolog, CLP(FD))

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)**.

A logic-programming engine: you state facts and Horn-clause rules, and the engine answers queries by SLD-resolution + backtracking. `library(clpfd)` bolts a finite-domain constraint solver onto that, so unification is replaced by constraint propagation over integer ranges.

## Primer

Think of Prolog as a *recursive, backtracking* relative of SQL: a `Datalog`-plus where rules can call themselves and bind *variables* rather than just filter rows. You write `parent(X,Y)` facts and an `ancestor/2` rule; the query `?- ancestor(a, Who).` enumerates every proof. The two ideas that matter: (1) **unification** — pattern-matching that binds variables both ways — and (2) **backtracking search** — the engine tries alternatives until a goal succeeds or the space is exhausted. CLP(FD) adds *constraint propagation*: `X #> Y, X in 1..9` narrows domains before search, like Z3 but with the relational query model wrapped around it. WHEN is it the right tool? When your problem is naturally **rules + recursive reachability over a small/medium symbolic store**, and you want one language for *both* the data and the deductive closure — not "solve one formula" (Z3) but "walk a chain, accumulate, explain, enumerate." Closer to Postgres `WITH RECURSIVE` than to an SMT one-shot.

## Applicability to autoharn

**SUPERSEDES chains (Pillar 2, high).** The append-only Witness→Correction ledger is a transitive-closure-over-edges problem — exactly Prolog's home turf, and more naturally *queryable* than `WITH RECURSIVE` because the "live head" emerges from negation-as-failure:

```prolog
supersedes(c2, w1).  supersedes(c5, c2).
live(F)   :- finding(F), \+ supersedes(_, F).
current(F, Base) :- supersedes(F, Base), live(F).   % ?- current(F, w1).
```

This beats SQL because the `\+ supersedes(_,F)` ("nothing overrides me") is the *definition* of liveness, not a NOT EXISTS subquery you re-derive each store.

**Non-monotonic DEFAULTS / ADR amendments (cross-cutting, high).** Defaults-later-overridden IS negation-as-failure. `decision(X, default) :- \+ override(X, _).` A new `override/2` fact silently retracts the default — non-monotonic reasoning is a *native* semantics here, whereas in Z3 you'd re-encode the whole frame.

**Paraconsistent suspect/DIRTY value (cross-cutting, med-high).** A 3-valued status is just a rule layer: a benchmark on a dirty tree must never reach `confirmed`:

```prolog
status(R, suspect)   :- result(R), tree(R, dirty).
status(R, confirmed) :- result(R), tree(R, clean), corroborated(R).
```

Conflicting advisories coexist as plain facts; the gate only fires on `status(R, confirmed)` derivations, so contradictions don't explode.

**CLP(FD) for finite enumeration (Pillar 1, med).** The task-shape→tool map blesses CP-SAT for finite enumeration; CLP(FD) is the *lightweight in-process* alternative for small scheduling/allocation checks, no external solver process:

```prolog
:- use_module(library(clpfd)).
slots(Xs) :- Xs = [A,B,C], Xs ins 1..3, all_distinct(Xs), label(Xs).
```

Honest: for real CP-SAT-scale enumeration, OR-Tools wins on power; CLP(FD)'s fit is "fast, embeddable, good enough for a CI gate," not "replaces the blessed solver."

**`<store>_violations` gates (Pillar 3, med).** A violation query ("a `confirmed` row whose tree is dirty," "a finding referenced by a perf-token with no stored reading") is a one-line clause that, if it has *any* solution, fails CI:

```prolog
violation(perf_unsubstantiated, Tok) :- perf_token(Tok), \+ reading_of(Tok, _), \+ unsubstantiated(Tok).
```

This is *the same engine* as the ledger queries — the appeal over a Python script is that the gate and the data model share one declarative surface.

**META-SWEEP / Rule 4 class-keying (Pillar 3, med-low).** "Every rule declares an enforcement surface from a closed vocabulary" and "key on the CLASS of defect" is naturally a rule over rules. Prolog can quantify over its own clauses (`clause/2`), so a meta-rule "every `discipline/2` fact has an `enforcement/2` in the closed set" is expressible — but this is somewhat *forced*: ASP/clingo (also installed) or plain SQL constraints do it as cleanly without Prolog's procedural pitfalls.

**Where it's a stretch:** measurement-vs-interpretation separation, pre-registration *temporality*, probabilistic "hunch vs truth" — Prolog has no native temporal or probabilistic semantics (use ProbLog for the latter; timestamps + a guard rule for the former). Abduction/ILP are *real* Prolog strengths (Aleph/Popper) but are research-grade, not CI-grade.

## Software to leverage

Local check: `swipl 9.3.31` already installed; `clingo/gringo` also present.

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| SWI-Prolog | engine + `library(clpfd)` (bundled) | BSD-2-Clause | C; CLI `swipl`, `swipl script.pl` | apt / already installed (9.3.31; latest stable 10.0.2) | very mature, active | high — ubiquitous in training data, but subtle cut/negation semantics |
| janus-swi | bi-directional Python↔Prolog (bundled w/ SWI ≥9.1.12) | BSD-2-Clause | `pip install janus-swi`; needs SWI + C compiler | pip (compiles a small ext) | current, SWI-team maintained | high — clean `janus.query()` API for harness glue |
| PySwip | older ctypes Python→SWI bridge | MIT | `pip install pyswip` | pip | mature, community | med — more example code online, ~5x slower than Janus |
| Clingo (ASP) | alternative for meta-sweep / hard combinatorics | MIT | C++; `pip install clingo`, CLI | apt / already installed | very mature (Potassco) | med — distinct ASP semantics, easy to mis-encode |
| Aleph / Popper | ILP (learn rules from examples) | GPL / academic | Prolog / Python | source | research-grade | low — niche, sparse docs |

## Limits & honest take

The headline risk for autoharn is **false authority from mis-encoding**: a Prolog program *always returns an answer*, and an LLM that fumbles a `\+` (negation-as-failure ≠ logical negation), a misplaced `!` (cut), or an unsafe rule will produce a confident, wrong "proof" — exactly the failure Pillar 2 exists to prevent, now wearing a logic costume. Mitigations: keep clauses *ground and small*, treat every gate query as needing a *failing* witness test (assert a known violation, confirm the gate fires), and store the `.pl` source under `{commit, tree}` like any other artifact. Prolog is also a poor fit where autoharn genuinely needs *numeric optimization* (cvxpy), *SMT feasibility over rich theories* (Z3 — bitvectors, reals), or *probabilistic* judgement; forcing those into CLP(FD) is hype. And much of the ledger/violation work is honestly doable in Postgres `WITH RECURSIVE` already — Prolog earns its slot only where **non-monotonic defaults, negation-as-failure liveness, and abduction** appear, which SQL cannot express cleanly. Use it as a *focused* second engine, not a replacement for the SQL stores.

## References & learning

- *The Power of Prolog* (Markus Triska, free online, swi-prolog favored) — best modern intro; the CLP(FD) and "no cut, think relationally" chapters directly counter the mis-encoding risk.
- SWI-Prolog `library(clpfd)` manual — the authoritative reference for `ins/2`, `all_distinct/1`, `label/1` used in the gate encodings above.
- Janus docs (`swi-prolog.org/pldoc/man?section=janus`) — how to drive the engine from the Python harness, the integration path for autoharn's CI.
- *Programming in Prolog* (Clocksin & Mellish) — classic grounding in unification/backtracking, the mental model behind every rule above.

Sources: [SWI-Prolog downloads](https://www.swi-prolog.org/download/stable), [janus-swi PyPI](https://pypi.org/project/janus-swi/), [SWI-Prolog Python FAQ](https://www.swi-prolog.org/FAQ/Python.md), [PySwip](https://github.com/yuce/pyswip)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
