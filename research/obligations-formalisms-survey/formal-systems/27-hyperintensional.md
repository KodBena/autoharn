# 27 — Hyperintensional Frontier: Truthmaker Semantics, Grounding, Dependence Logic, Free Logic (flag the speculative ones)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [STRUCT](../KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

These are the tools for when *which possible worlds a claim holds in* is too coarse — when you must audit **why** a claim is true, **what exactly** makes it so, **what it functionally depends on**, and **what happens when a term denotes nothing**. Maturity varies sharply: free logic and dependence logic are automation-ready; truthmaker semantics and metaphysical grounding are genuine frontier (flagged speculative below).

## Primer (becoming broadly expert)

Possible-worlds semantics is *intensional*: two claims true in the same worlds are identified, so any tautology is "verified" by everything and irrelevant facts count as truthmakers. **Hyperintensional** logics break this. **Truthmaker semantics** (Kit Fine) replaces worlds with *states* (parts of worlds) and defines *exact* verification: a state verifies φ only if it is *wholly relevant* to φ — no idle conjuncts. Conjunction is *fusion* of verifiers, disjunction is *union*; this gives a content algebra finer than logical equivalence. **Grounding** (Fine, *Guide to Ground*; Schaffer) is the "in virtue of" relation — explanatory, hyperintensional, non-monotonic, and *well-founded* (chains bottom out). **Dependence logic** (Väänänen) reads formulas over *teams* (sets of assignments) rather than single points; the **dependence atom** `=(x⃗, y)` asserts that across the whole team, `y` is functionally determined by `x⃗`. First-order dependence/independence logic captures exactly ESO/NP; inclusion logic captures PTIME. **Free logic** (Lambert, Scott) admits singular terms that *fail to denote*, with an explicit existence predicate `E!`, so `f(a)` of a non-existent `a` has principled (not garbage) semantics. Together they discharge obligations about *grounding*, *coherent dependence*, and *honest absence*.

## Obligations it discharges

- **[PROV](../KEY.md#prov) (Claim Provenance & Groundedness)** — *primary fit, truthmaker + grounding.* [PROV](../KEY.md#prov)'s failure mode is the confabulated chain that *looks* grounded: a citation that does not support its claim, a derivation edge with no warrant. Possible-worlds entailment cannot see this — anything entails a tautology, irrelevant premises "verify" conclusions. **Exact truthmaking** is the matched semantics: the verifier must be *wholly relevant*, no idle conjuncts, so a claim's truthmaker-set *is* its inspectable warrant. Grounding's **well-foundedness** is exactly "resolves through a finite chain to primary evidence." Guarantee strength: structural — relevance and finite groundedness are properties of the derivation, not of statistical confidence.
- **[COHERE](../KEY.md#cohere) (Single-Writer Coherence)** — *primary fit, dependence logic.* [COHERE](../KEY.md#cohere) demands a coherence invariant *quantified over all writers*. A dependence atom `=(key, value)` is precisely a constraint over the *whole team* of observations/writers, not one state. It detects the "two sides re-author one truth and drift silently" failure as a team that violates the functional dependency. Guarantee strength: NP-checkable over finite teams (decidable, mechanical).
- **[STRUCT](../KEY.md#struct) (Structural Soundness)** — *primary fit, free logic.* The magic-`-1` / "no quote" sentinel and the lying signature are [STRUCT](../KEY.md#struct)'s failure mode. Free logic gives a *principled* semantics for non-denoting terms: `E!(t)` is a typed, must-handle existence guard rather than a sentinel silently flowing into arithmetic. Guarantee strength: matched to the type-discipline already in [STRUCT](../KEY.md#struct) (optional/expected).
- **[REVISE](../KEY.md#revise) / [RECORD](../KEY.md#record)** — *secondary, grounding.* Ground edges give the dependency graph along which retraction propagates ([REVISE](../KEY.md#revise)) and the reconstructable rationale ([RECORD](../KEY.md#record)).

**Does NOT serve:** [PROG](../KEY.md#prog)/real-time (no temporal/metric content), [DEGRADE](../KEY.md#degrade) (no contrary-to-duty operator — that is deontic), [AUTH](../KEY.md#auth) (no permission algebra), [INDEP](../KEY.md#indep) (an organizational, not semantic, property).

## A worked encoding

[COHERE](../KEY.md#cohere): a config key must have **one** authoritative value across all writers — a dependence atom `=(key, value)` over the team of observations. Real `clingo` (5.8.0, verified local):

```prolog
% team of observations of a safety config key from multiple writers/mirrors
obs(writer_a,  spillway_crest_m, 542).
obs(writer_b,  spillway_crest_m, 542).
obs(plc_mirror, spillway_crest_m, 540).   % a second writer re-authored the truth

% dependence atom =(K,V): V functionally determined by K across the whole team
drift(K) :- obs(_,K,V1), obs(_,K,V2), V1 != V2.
:- drift(K).                 % integrity constraint: no model if any key drifts
#show drift/1.
```

`clingo` returns **UNSATISFIABLE** because `drift(spillway_crest_m)` holds: the dependence atom is violated, surfacing the silent drift loudly instead of letting two internally-consistent sides diverge. Remove the mirror's `540` and the program is SAT — the team satisfies `=(key,value)`.

## Automation & tooling (the git-clone-runnable question)

**Free logic — dedicated, mature.** The Benzmüller–Scott *shallow semantic embedding of free logic in Isabelle/HOL* is a real, runnable artifact (`.thy` theories; Isabelle is BSD-3-licensed; current Isabelle2025). It lifts off-the-shelf higher-order automation (Sledgehammer/Nitpick) to free-logic reasoning about definedness/partiality. **Automation path: clone the embedding, model `E!` and non-denoting terms directly.** This is the most industrially ready of the four.

**Dependence logic — no general solver, but a clean encoding host.** Model-checking dependence/independence logic = ESO = NP, so the natural host is **ASP/clingo** (or SAT): represent the team as a relation, dependence atoms as integrity constraints (the worked example above runs *today*). Inclusion logic = PTIME → **Datalog / Postgres recursive**. No tool to install; the host *is* the implementation.

**Truthmaker semantics — no dedicated tool (speculative).** WEB-VERIFY: `truthmakersemantics.github.io` is a research hub, *not* a model checker; "very little technical work has been done … almost entirely [by] Fine." **Encoding path:** represent the state space as a finite join-semilattice (fusion = least upper bound) in **clingo** or **Z3**; define exact verification recursively — `verify(S,and(A,B))` iff `S` is the fusion of an `A`-verifier and a `B`-verifier; `verify(S,or(A,B))` iff `S` verifies `A` or `B`; check "S exactly verifies φ" with no idle parts via a minimality/`#minimize` constraint. Z3's lattice/partial-order axioms make fusion natural; the relevance (no-idle-part) condition is the subtle part and the qualification target.

**Grounding — no dedicated tool (speculative).** Encode the ground relation as a directed edge set; **well-foundedness = acyclicity**, checkable in ASP (`:- ground_path(X,X).`) or Datalog stratification; "bottoms out in primary evidence" = every source node is an admitted axiom/measurement. Runnable as a graph-integrity check today; the *semantics* of which edges are legitimate grounds is the open research question.

## Honest leverage & kill-condition

**Load-bearing:** free logic for [STRUCT](../KEY.md#struct) (definedness is a solved, automatable problem) and dependence logic for [COHERE](../KEY.md#cohere) (the clingo encoding above is a deployable drift gate *now*). **Frontier/at-risk:** truthmaker exactness for [PROV](../KEY.md#prov) is the genuinely novel claim — that "wholly relevant verifier" mechanically separates a real warrant from a confabulated-but-classically-valid one.

**Falsifiable experiment:** build a corpus of 50 claim→warrant pairs, half with *genuine* exact truthmakers, half where the cited warrant is classically entailing but *irrelevant* (idle-conjunct confabulations, of the kind an LLM emits). Encode exact verification in Z3 with the no-idle-part minimality condition. **KILL CONDITION:** if the truthmaker checker's relevance verdict does not separate the two classes at ≥0.9 precision/recall — i.e., it flags genuine warrants as irrelevant or passes confabulations as exact — then exact truthmaking buys [PROV](../KEY.md#prov) *nothing over* classical entailment + a citation check, and [PROV](../KEY.md#prov) should be discharged by provenance-graph tooling (Datalog lineage) instead. Honest ash is an acceptable result. For dependence/free logic the kill condition is weaker and likely unmet: the encodings already run.

## References (edification)

- **Fine, "Truthmaker Semantics" (2017, *Blackwell Companion to the Philosophy of Language*)** — teaches exact verification and the fusion/union content algebra; the canonical entry point. [PhilPapers](https://philpapers.org/rec/FINTSP-2)
- **Väänänen, *Dependence Logic* (2007)** — teaches team semantics and the dependence atom; establishes the ESO/NP correspondence that makes ASP the right host. [CORDIS/TEAMDEP](https://cordis.europa.eu/project/id/101020762)
- **Benzmüller & Scott, "Automating Free Logic in Isabelle/HOL"** — teaches the runnable shallow embedding for definedness/partiality; your git-clone path for [STRUCT](../KEY.md#struct). [PDF](http://page.mi.fu-berlin.de/cbenzmueller/papers/C57.pdf)
- **Fine, "Guide to Ground" (2012)** — teaches grounding as explanatory, hyperintensional, well-founded; the spec for [PROV](../KEY.md#prov)/RECORD chains.

Sources: [dependence logic / team semantics](https://cordis.europa.eu/project/id/101020762), [truthmaker semantics hub](https://truthmakersemantics.github.io/), [Benzmüller–Scott free logic in Isabelle/HOL](http://page.mi.fu-berlin.de/cbenzmueller/papers/C57.pdf).


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
