# 03 — Answer Set Programming (clingo)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |

A declarative paradigm where you state a problem as a logic program under the stable-model (answer-set) semantics and a solver enumerates the worlds that make it true; default negation and integrity constraints make it the native home for closed-world authorization, defaults-with-exceptions, and exhaustive case partition.

## Primer (becoming broadly expert)

ASP descends from the stable-model semantics of Gelfond and Lifschitz (1988) for normal logic programs, which fixed the meaning of *default negation* `not p` ("p is not derivable") via a fixpoint construction (the Gelfond–Lifschitz reduct). The core idea: a program's meaning is not one model but the *set* of its stable models (answer sets), each a minimal, self-supporting, closed-world interpretation. Two constructs do almost all the load-bearing work. **Default negation** gives you nonmonotonic defaults-and-exceptions: conclusions retract when contradicting evidence arrives, without rewriting rules. **Integrity constraints** (`:- body.`) are headless rules that *eliminate* any answer set satisfying the body — a direct "this must never hold" filter. Disjunction and choice rules (`{a;b}`) let you generate candidate worlds; constraints prune them — the "generate-and-test" methodology (Lifschitz; Marek–Truszczyński; Niemelä, who framed ASP as a constraint paradigm). Modern grounders (gringo) plus conflict-driven solvers (clasp, Gebser–Kaufmann–Schaub) make it industrially fast. Intuition for *which* obligation: ASP is built to answer "given everything I know and the closed-world assumption, what is permitted / which exactly-one bucket applies / does any forbidden configuration survive?" — it is a **closure and partition engine**, not a temporal or arithmetic prover.

## Obligations it discharges

**[AUTH](../KEY.md#auth) (primary).** Permission closure is ASP's home turf. The choice between open- and closed-world is *the* design decision in the failure mode ("an act permitted because no rule named it"), and ASP makes that choice explicit and machine-checked: `blocked(A,Act) :- not permitted(A,Act).` is closed-world by construction. Norm precedence (standing norm vs. transient override) is exactly defaults-with-exceptions, and an integrity constraint `:- leak.` turns authority leakage into UNSAT. **Guarantee strength:** exhaustive over the grounded domain — if a leak is representable, the solver finds it or proves its absence. The bound is the grounding: guarantees hold only for the finite domain you ground.

**[CLASS](../KEY.md#class) (primary).** A total, mutually-exclusive-and-exhaustive partition with an explicit `unknown` cell is a count constraint plus a default. `:- #count{A: assign(P,A), A!=unknown} > 1` forbids dual-classing; the `unknown` default forces misfit to surface loudly rather than snap to the nearest-wrong tier. **Guarantee:** mechanical MECE over the closed vocabulary; order-independent (no rule-ordering dispatch bug).

**[CONSIST](../KEY.md#consist) (qualified).** ASP localizes conflict: contradictory hard requirements yield *no* answer set (UNSAT) rather than ex-falso explosion — the conflict is detected, not laundered. With weak constraints or assumption-tagging you can keep reasoning *around* a quarantined conflict. It does not give paraconsistent *graded* coexistence the way a dedicated LP-style logic does; assign [CONSIST](../KEY.md#consist)'s containment-while-still-useful core elsewhere and use ASP for detection.

**[REVISE](../KEY.md#revise) / [PROV](../KEY.md#prov) (secondary).** Nonmonotonicity means retracting a fact automatically withdraws unsupported conclusions on re-solve — a natural fit for retraction propagation, though ASP gives recomputation, not the AGM *minimal-change* audit trail [REVISE](../KEY.md#revise) demands. Stable-model groundedness (every atom must be *supported* by a rule) matches [PROV](../KEY.md#prov)'s "no free-floating fact," and clingo's justification/`clingo-explain` tooling can replay the support chain.

**Does NOT serve:** [PROG](../KEY.md#prog) (no native temporal/real-time deadline or fairness semantics — that is temporal logic / TLA+), [INV](../KEY.md#inv) over dense time, [CALIB](../KEY.md#calib)/numeric tolerance (use SMT/Z3), and unbounded data (grounding blows up). ASP is finite-domain and synchronous.

## A worked encoding

[AUTH](../KEY.md#auth) for the dam spillway gate (runs on clingo 5.8.0):

```prolog
agent(optimizer_ai). agent(release_eng).
action(propose_change). action(deploy_spillway).

% standing norm: only a human release engineer may deploy
permitted(A, propose_change) :- agent(A).
permitted(release_eng, deploy_spillway).

% transient override exists, but a standing safety norm outranks it
override(optimizer_ai, deploy_spillway, 11).
standing_forbid(optimizer_ai, deploy_spillway).

% closed-world: blocked unless explicitly permitted; derogation: standing forbid wins
blocked(A,Act) :- agent(A), action(Act), not permitted(A,Act).
blocked(A,Act) :- standing_forbid(A,Act).

request(optimizer_ai, deploy_spillway).
leak :- request(A,Act), not blocked(A,Act), standing_forbid(A,Act).
:- leak.          % authority leakage is UNSAT
#show blocked/2.
```

Output: `blocked(optimizer_ai,deploy_spillway)`, SATISFIABLE. Delete the `standing_forbid`-as-override-winner rule and the program still finds the leak via the constraint — the gate is *checked*, not narrated. The [CLASS](../KEY.md#class) triage variant (tested) maps a `novel_toxidrome` with no rule to `assign(p1,unknown), needs_review(p1)` instead of the nearest acuity tier.

## Automation & tooling (the git-clone-runnable question)

**Dedicated tool: clingo** (grounder gringo + solver clasp), the Potassco flagship. **License: MIT** (verified). **Latest: 6.0.0 / 5.8.1; locally installed 5.8.0** with Python 3.13 and Lua bindings (`clingo version 5.8.0`, confirmed via `which clingo`). Maturity: high — 20+ years, ASP-Competition–grade, used in NASA decision-support and product configuration. The Python API (`import clingo`) makes it a callable library inside autoharn's check harness, not just a CLI; on-the-fly grounding and multi-shot solving (`clingo.Control`) let you re-solve on premise retraction ([REVISE](../KEY.md#revise)). Companions, all open-source: **clingcon** (integer constraints), **clingo[DL]** (difference logic for light scheduling), and **s(CASP)** (goal-directed ASP, packable into the local SWI-Prolog 9.3.31) when you need a *justification tree* per query rather than whole-model enumeration — directly serving [PROV](../KEY.md#prov)/RECORD. No encoding gap to bridge here; the host *is* the tool. The qualification path ([INDEP](../KEY.md#indep)): ship golden answer-set fixtures and mutation tests over the rule base, and cross-check safety-critical UNSAT verdicts against an independent re-grounding or an s(CASP) justification, so the LLM-authored `.lp` is itself qualifiable.

## Honest leverage & kill-condition

**Load-bearing** for [AUTH](../KEY.md#auth) and [CLASS](../KEY.md#class): closed-world permission closure and MECE partition are *definitionally* what stable models compute, and the integrity constraint converts "should never happen" into a solver-decidable UNSAT — exactly the leak/dual-class failure modes. **Ash** where the obligation is temporal, real-time, numeric, or over unbounded data: forcing [PROG](../KEY.md#prog) or float-tolerance [CALIB](../KEY.md#calib) into ASP means encoding time as ground atoms, and grounding explodes.

**Falsifiable experiment:** take autoharn's authorization rule set with N agents × M actions × K norm sources; inject a leak (an over-permission or an override that should be outranked) via mutation. **KILL CONDITION:** if clingo cannot, within the grounded domain and a fixed time budget, flag every injected leak as UNSAT (or surface every uncovered [CLASS](../KEY.md#class) case as `unknown`) — i.e., if a mutant passes green — ASP is *not* load-bearing for that obligation and the assignment is wrong. A second kill condition: if realistic autoharn authorization domains do not ground in bounded memory/time, the guarantee is vacuous at scale and the obligation must move to a SAT/SMT lazy-grounding host.

## References (edification)

- **Gelfond & Lifschitz, "The Stable Model Semantics for Logic Programming" (1988)** — the founding paper; teaches what an answer set *is* and why default negation is nonmonotonic.
- **Gebser, Kaminski, Kaufmann, Schaub, *Answer Set Solving in Practice* (2012)** — the canonical primer; teaches generate-and-test modeling and the clingo language end to end.
- **Potassco clingo documentation / guide (potassco.org/clingo)** — teaches the actual syntax, the Python multi-shot API, and constraint extensions you will deploy.
- **Arias et al., "Constraint Answer Set Programming without Grounding" / s(CASP)** — teaches goal-directed ASP with per-query justifications, the [PROV](../KEY.md#prov)/RECORD bridge.

Sources: [clingo releases](https://github.com/potassco/clingo/releases/), [clingo LICENSE](https://github.com/potassco/clingo/blob/master/LICENSE.md), [PyPI clingo](https://pypi.org/project/clingo/)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
