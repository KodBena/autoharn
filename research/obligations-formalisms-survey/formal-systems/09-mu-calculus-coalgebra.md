# 09 — Modal μ-calculus, Coinduction & Process Logics (maintenance over infinite behaviour)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](../KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [COMMIT](../KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [TRACE](../KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

The modal μ-calculus is the assembly language of temporal reasoning: a tiny modal logic plus least (μ) and greatest (ν) fixpoints that subsumes LTL, CTL, CTL\* and PDL, and lets you state and *machine-check* properties of systems that never terminate — the controllers, settlement engines and flight loops whose whole job is to run forever correctly.

## Primer (becoming broadly expert)

The core move (Kozen, 1983) is to add to ordinary modal logic — `<a>φ` "some `a`-step reaches φ", `[a]φ` "every `a`-step reaches φ" — two fixpoint binders over a recursion variable `X`. `νX.φ(X)` is the *greatest* fixpoint: the largest set of states invariant under unfolding — this is **safety/invariance/coinduction**, "this can be maintained forever." `μX.φ(X)` is the *least* fixpoint: reachable in finitely many unfoldings — this is **liveness/progress/induction**, "this is guaranteed to happen." Alternating μ and ν expresses fairness ("infinitely often"). The two facts that matter: (1) the **fixpoint duality** — ν is for "always/keep-true," μ is for "eventually/well-founded" — is exactly the safety/liveness split; (2) **bisimulation invariance** — the logic sees precisely what behaviour, not state encoding, can distinguish, so it is the right currency for *behavioural equivalence and refinement*. Canonical results: Kozen's axiomatization (completeness, Walukiewicz 2000); Emerson–Jutla's reduction of model-checking to **parity games**; Knaster–Tarski as the coinduction foundation. It is built to discharge maintenance of properties *over infinite runs of a reactive process* — [INV](../KEY.md#inv) and [PROG](../KEY.md#prog).

## Obligations it discharges

- **[INV](../KEY.md#inv) — Safety-Invariant Maintenance** (primary). The ν-fixpoint `νX.(safe ∧ [·]X)` *is* the formal meaning of "the invariant holds in every reachable state across the whole interval it is in force." A transient one-tick excursion that self-heals still falsifies the formula, because the greatest fixpoint quantifies over *all* successors at *every* depth. Guarantee strength: with a finite/finite-state model, model-checking is **exhaustive over all reachable states and all interleavings** — a decision procedure, not sampling. This is the strongest available channel for "keep-it-true across an unbounded interval."

- **[PROG](../KEY.md#prog) — Liveness & Real-Time Progress** (primary). `[true*]μY.(<·>true ∧ [¬event]Y)` says: from every reachable state, every path *inevitably* performs `event` in finitely many steps — the μ binds the well-founded "it actually arrives" obligation, ruling out the hang/livelock failure mode no single state exposes. With explicit clock/tick actions or a timed-automata front end you get bounded progress (within N ticks); μ alone gives unbounded-but-certain eventuality. Freedom from deadlock is the canonical `[true*]<true>true`.

- **[DEGRADE](../KEY.md#degrade)** (secondary/compositional). The trigger→reparation regime is naturally a ν over the sub-ideal region with a μ for "reaches safe-hold within the fault-tolerant interval" — μ-calculus expresses the *temporal shape* of reparation, though the *normative* contrary-to-duty content belongs to deontic/STIT logics; here μ-calculus is the timing/reachability spine they compose onto.

It does **not** serve: [ATTR](../KEY.md#attr), [AUTH](../KEY.md#auth), [COMMIT](../KEY.md#commit), [PROV](../KEY.md#prov), [REVISE](../KEY.md#revise), [CONSIST](../KEY.md#consist), [RECORD](../KEY.md#record) — these are normative, epistemic, or provenance obligations about *who/why/on-what-grounds*, not about the temporal structure of an infinite run. Assign those elsewhere (STIT, deontic, justification, paraconsistent logics). μ-calculus owns *temporal maintenance*, full stop.

## A worked encoding

Autoharn obligation: **[INV](../KEY.md#inv)** — "the dam spillway controller never spends a tick with the reservoir above crest while gates are commanded shut," plus **[PROG](../KEY.md#prog)** — "a detected over-crest condition inevitably reaches `open_gate`." In mCRL2's modal-formula syntax over a labelled transition system whose actions include `over_crest`, `gates_shut`, `open_gate`, `tick`:

```
% INV: no reachable state has over_crest sustained with gates shut (greatest fixpoint)
nu X . ( !(over_crest && gates_shut)
         && [true] X );

% PROG: from every reachable state, after over_crest, open_gate is inevitable
[true*] (
  [over_crest] mu Y . ( <true>true            % not deadlocked
                        && [!open_gate] Y )    % every continuation makes progress to open_gate
);
```

The pipeline is `mcrl22lps spillway.mcrl2 | lps2pbes -f inv.mcf` then `pbes2bool`, which compiles the model and formula into a **Parameterised Boolean Equation System** and solves the underlying parity game. `pbes2bool` returns `true`/`false` for the whole reachable state space; on `false` mCRL2 generates *evidence* — a concrete counterexample trace (e.g. the offending `over_crest . tick` interleaving) you attach to the autoharn audit record ([RECORD](../KEY.md#record)) as the falsifying witness.

## Automation & tooling (the git-clone-runnable question)

**Dedicated open-source tool: mCRL2, latest 202507.0, Boost Software License (permissive, OSI-approved).** This is the git-clone answer: mature (TU/e, 20+ years, TACAS'19 tool paper, active GitHub), industrial-grade, with `lps2pbes`/`pbes2bool`/`pbessolvesymbolic` for full μ-calculus-with-data model-checking and counterexample generation. Ships its own process language (mCRL2) and consumes LTSs. **CADP** (EVALUATOR 4.0, Mcl logic) is comparable but **academic-license, not open source** — usable in-house under agreement, not redistributable in a clone, so it is a secondary oracle (good for [INDEP](../KEY.md#indep) cross-checking), not the primary deliverable.

No *additional* solver is needed, but for parts already living in autoharn's installed stack there is a real **encoding path** that keeps μ-calculus checks inside engines we have: a μ-calculus model-checking instance reduces to a **parity game**, and a parity game over a finite arena is directly encodable in **clingo (ASP)** — states/moves as facts, the ν/μ priority assignment as a stratified/disjunctive winning-region computation — or solved as a fixpoint in recursive **Postgres** for the alternation-free fragment (safety/simple liveness), which covers most [INV](../KEY.md#inv)/PROG obligations. For invariants specifically, the ν-formula `νX.(safe ∧ [·]X)` is exactly "`safe` holds on the reachable set," discharged by a **Z3** k-induction / IC3 check on the same transition relation, giving an independent second channel ([INDEP](../KEY.md#indep)). So: primary = mCRL2; differential oracle = clingo parity-game encoding and Z3 invariant check on the same model — three engines, one verdict, qualifiable.

## Honest leverage & kill-condition (life-critical seriousness)

**Load-bearing** wherever the obligation is "this property is maintained / inevitably reached over an unbounded run of a *modelled* process" and the model is finite-state or finitely-abstractable: spillway interlocks, safe-hold reachability, deadlock-freedom, fairness of a settlement scheduler. Here the guarantee is a genuine *decision procedure over all interleavings* — categorically stronger than test sampling.

**Where it is ash:** the load-bearing artifact is the **model**, not the formula. If the LTS is hand-abstracted by the LLM from real code, a soundness gap in that abstraction makes a green μ-calculus verdict *false authority* ([CALIB](../KEY.md#calib) failure). And state-space explosion / data-heavy systems can make checking intractable, tempting silent scope-narrowing ([TRACE](../KEY.md#trace) failure).

**Falsifiable experiment + KILL CONDITION:** Take a corpus of real autoharn process specs with seeded [INV](../KEY.md#inv)/PROG defects (mutation: drop a guard, add a self-healing coercion, remove a progress edge). Require the mCRL2 pipeline to (a) flag every seeded defect with a valid counterexample trace, and (b) the model abstraction to be *mechanically* derived from the executable artifact (not LLM-narrated), checked by replaying the counterexample against the real system. **KILL CONDITION:** if mCRL2 passes a spec while the corresponding real system exhibits the seeded violation on the replayed trace — i.e. the abstraction laundered the bug — more than a negligible rate, then μ-calculus model-checking is *not* load-bearing for autoharn *as wired*, and the obligation must be re-discharged at the artifact level (runtime monitors / verified extraction), not at the model.

## References (edification)

- **Kozen, "Results on the Propositional μ-Calculus" (TCS, 1983)** — the source: syntax, fixpoint semantics, why ν=safety and μ=liveness.
- **Bradfield & Stirling, "Modal μ-calculus" (Handbook of Modal Logic, 2007)** — the best modern primer: games, expressiveness, the alternation hierarchy, intuition for fixpoint nesting.
- **Groote & Mousavi, *Modeling and Analysis of Communicating Systems* (MIT Press, 2014)** — the mCRL2 textbook; teaches the process algebra, the modal-formula language, and the PBES toolchain you actually run.
- **mCRL2 user manual, μ-calculus page (mcrl2.org, 202507.0)** — the runnable reference: exact `.mcf` syntax, `lps2pbes`/`pbes2bool`, evidence/counterexample generation.

Sources: [mcrl2.org μ-calculus](https://mcrl2.org/web/user_manual/language_reference/mucalc.html), [mCRL2 GitHub (Boost license)](https://github.com/mCRL2org/mCRL2), [CADP EVALUATOR](https://cadp.inria.fr/man/evaluator.html)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
