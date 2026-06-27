# 02 — Prolog, CLP & Prolog-as-Encoding-Host

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [STRUCT](../KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |

I have what I need. Writing the section.

## Prolog, CLP & Prolog-as-Encoding-Host

Prolog is the field's universal solvent: a Horn-clause resolution engine whose unification + backtracking + meta-interpretation make it the cheapest place to *encode* a non-classical logic that has no dedicated solver, and whose CLP and ASP descendants discharge real obligations directly. In autoharn it is both a first-class checker and the host of last resort.

## Primer (becoming broadly expert)

The core idea (Kowalski's *algorithm = logic + control*; Colmerauer's 1972 engine): write facts and rules as definite clauses `H :- B1,...,Bn`, and a query is answered by SLD-resolution — depth-first backward chaining with unification, the most-general-unifier doing structural pattern-matching for free. Two concepts matter most. First, **the closed-world assumption and negation-as-failure**: `\+ G` succeeds when `G` is not derivable. This is *exactly* a default/non-monotonic stance, which is what makes Prolog a natural home for closure rules and defeasible norms — and a trap if you forget it. Second, **Prolog as a meta-language**: clauses are terms, so a three-line meta-interpreter (`solve((A,B)):-solve(A),solve(B). solve(G):-clause(G,Body),solve(Body).`) becomes the skeleton you extend with labelled deductions, justifications, or modal accessibility — the standard route by which "merely philosophical" logics (defeasible, deontic, temporal) get *implemented*. Constraint Logic Programming (Jaffar & Lassez) replaces unification over a single domain with constraint solving over others — `clpfd` (finite domains, Triska), `clp(R/Q)` (reals/rationals), CHR (Frühwirth's committed-choice rewriting). Answer Set Programming (Gelfond–Lifschitz stable models) is the same declarative core with a *total*, grounded, multiple-model semantics. Built to discharge: groundable provenance, closure, and default reasoning.

## Obligations it discharges

- **[PROV](../KEY.md#prov) — Claim Provenance & Groundedness (primary).** SLD-resolution *is* a proof tree; capturing it gives a finite, replayable chain from query to ground facts/axioms. A meta-interpreter that threads a proof term turns every derived claim into an inspectable warrant. Guarantee: a syntactic certificate of derivability against the current store — strong for groundedness, only as strong as the asserted facts for soundness.
- **[AUTH](../KEY.md#auth) — Permission Closure (primary for the closure half).** CWA + negation-as-failure directly encode closed-world permission ("forbidden unless derivably permitted"); flipping a default clause encodes open-world. The closure *rule itself* becomes explicit and testable. Guarantee: decidable per-action gating over a finite policy.
- **[CLASS](../KEY.md#class) — Honest Sharp Classification.** Mutually-exclusive-and-exhaustive partitions are clauses; ASP's `:- ` integrity constraints and choice rules make dual-classing and gaps *unsatisfiable* rather than silently absorbed.
- **[TRIG](../KEY.md#trig) — Conditional Activation.** Antecedent→consequent detachment is the native operation; degraded-sensing variants want defeasible layering (encode, below).
- **[REVISE](../KEY.md#revise) — Belief Revision (with TMS).** Prolog hosts a justification-/assumption-based truth-maintenance system; assert/retract plus recorded justifications give retraction propagation. Guarantee: dependency-directed, *not* AGM-optimal unless you encode minimality.
- **[CONSIST](../KEY.md#consist) — Containment.** Plain Prolog does NOT serve this — it shares classical explosion under asserted contradiction via integrity violation, and CWA hides conflict. ASP detects unsatisfiability but reports no models rather than reasoning *through* conflict; paraconsistency must be encoded.

Does NOT serve well, assign elsewhere: **[INV](../KEY.md#inv)/PROG** real-time temporal invariants over infinite state (→ TLA+/model-checkers), **[CALIB](../KEY.md#calib)/INDEP** independent adjudication (Prolog is a *producer*; its own proof must be checked by a diverse oracle — see kill-condition), float-sensitive **[STRUCT](../KEY.md#struct)** numerics (→ Z3/interval).

## A worked encoding

[AUTH](../KEY.md#auth) permission closure + ATTR-adjacent gating, for the dam spillway branch (closed-world: deploy forbidden unless explicitly permitted *and* authorized).

```prolog
% facts: who may propose vs deploy, and standing > override precedence
role(ai_optimizer, propose).
role(duty_engineer, deploy).
norm(standing, forbid, deploy(spillway_ctrl)).
norm(override(T), permit, deploy(spillway_ctrl)) :- active_override(T).

permitted(Agent, Action) :-
    role(Agent, Action),
    \+ blocked(Action).               % negation-as-failure = closure rule
blocked(Action) :-
    norm(standing, forbid, Action),
    \+ ( norm(override(_), permit, Action) ).  % derogation order, logged

gate(Agent, Action, allow) :- permitted(Agent, Action), !.
gate(_,     _,      deny).            % total: no silent gap

% ?- gate(ai_optimizer, deploy(spillway_ctrl), R).  R = deny.
% ?- gate(duty_engineer, deploy(spillway_ctrl), R).  R = deny (standing forbid).
```

The `gate/3` last clause makes the partition *total* ([CLASS](../KEY.md#class)); the explicit `blocked` clause makes the closure rule auditable rather than emergent. To get a [PROV](../KEY.md#prov) certificate, run it under a proof-capturing meta-interpreter so each `deny`/`allow` carries the clause chain that produced it.

## Automation & tooling (the git-clone-runnable question)

Dedicated tools, all locally present and verified:

- **SWI-Prolog 9.3.31** (`/usr/bin/swipl`, confirmed). License: **BSD-2-Clause** (core; a few optional components LGPL). Bundles `library(clpfd)`, `clp(R/Q)`, and `library(chr)` — CHR loaded cleanly here. Mature, production-grade, actively released. (Note: web results conflated a future "10.0"; the installed development line 9.3.x is the standard current toolchain.)
- **clingo 5.8.0** (`/usr/bin/clingo`, confirmed) for the ASP obligations ([CLASS](../KEY.md#class), [AUTH](../KEY.md#auth) closed-world, REVISE-as-stable-models). License: **MIT**. Grounder+solver, industrial maturity.
- **s(CASP)** — goal-directed, *ungrounded* constraint ASP, with **built-in natural-language justification trees** (directly a [PROV](../KEY.md#prov)/RECORD artifact). License **CC BY 4.0**; SWI pack, needs SWI ≥ 8.5.6 (satisfied). NOT installed here (`library(scasp)` absent); install path is `?- pack_install(scasp).` — flag for the deliverable's bootstrap, do not install during survey.

Encoding path for logics with no solver (the host role): non-classical logics are implemented as **labelled meta-interpreters**. A defeasible/deontic layer for [TRIG](../KEY.md#trig)/DEGRADE: represent each rule as `rule(Id, Head, Body, strict|defeasible)`, add a priority relation, and write an interpreter that derives `+D Goal` (definitely) / `+d Goal` (defeasibly, no stronger contrary applies) — this is Governatori's Defeasible Deontic Logic, mechanically Prolog-encodable, and handles CTD reparation by chaining a violated primary to a secondary obligation. A TMS for [REVISE](../KEY.md#revise) is the same meta-interpreter threading `justification(Node, Antecedents)` and re-deriving on retract. CHR is the right host when the logic is naturally *rewriting* (constraint propagation, paraconsistent quarantine: CHR rules that consume a clashing pair into a `conflict/1` marker instead of letting both propagate — partial [CONSIST](../KEY.md#consist) recovery).

## Honest leverage & kill-condition

Load-bearing: [PROV](../KEY.md#prov), AUTH-closure, [CLASS](../KEY.md#class), and as the **encoding host** for the deontic/defeasible/TMS family that no off-the-shelf engine ships. The replayable proof tree is autoharn's cheapest groundedness gate, and CWA is the *correct* semantics for "permitted only if named."

Ash risk: the proof certificate is sound *for derivability in the asserted store*, not for truth — and an LLM authored both the clauses and the meta-interpreter ([INDEP](../KEY.md#indep)/CALIB exposure). Prolog's CWA can also silently launder a missing fact into a confident `deny`/`permit`.

**Falsifiable experiment:** build a mutation/golden corpus of 50 spillway-authorization scenarios with ground-truth allow/deny; run the encoding; then (a) differentially cross-check every verdict against an independent clingo re-encoding of the same policy, and (b) inject 200 mutants (drop a `blocked` clause, flip a default, perturb the cut). **KILL CONDITION:** if the Prolog and clingo encodings disagree on ≥1 ground-truth-correct scenario, OR if mutation score < 95% (mutants that change a verdict but are not caught by the golden set), Prolog is demoted from *adjudicator* to *untrusted producer* whose every output must be re-derived by the diverse ASP channel before any gate trusts it. Negation-as-failure masking a missing fact (a `deny` that should have been `unknown`) counts as a kill.

## References (edification)

- Kowalski, *Logic for Problem Solving* (1979) — teaches the logic-as-computation foundation and why clauses are both program and proof.
- Sterling & Shapiro, *The Art of Prolog* (2nd ed.) — teaches meta-interpreters: the exact technique for hosting a non-classical logic.
- Triska, *The Power of Prolog* (online) and `library(clpfd)` docs — teaches modern, sound constraint Prolog and the CWA pitfalls.
- Arias, Carro, Gupta et al., *Constraint Answer Set Programming without Grounding* / s(CASP) — teaches goal-directed ASP with machine-generated justifications, the [PROV](../KEY.md#prov)/RECORD payoff.

Sources: [SWI-Prolog/sCASP](https://github.com/SWI-Prolog/sCASP), [scasp pack](https://www.swi-prolog.org/pack/list?p=scasp), [SWI-Prolog license](https://www.swi-prolog.org/pldoc/man?section=license), [SWI-Prolog versions](https://www.swi-prolog.org/versions.md)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
