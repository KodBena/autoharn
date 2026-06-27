# 06 — Linear & Branching Temporal Logic + Model Checking (LTL/CTL, NuSMV/Spot)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

The discipline of stating *when*-properties — "always," "eventually," "until," "on every/some path" — over the unbounded execution of a reactive system, and then *deciding them mechanically* by exhaustively exploring the reachable state space rather than testing samples of it.

## Primer (becoming broadly expert)

Pnueli's 1977 insight (Turing Award) was that program correctness for non-terminating reactive systems is naturally expressed in **temporal logic** over infinite traces. Two dialects matter. **LTL** adds to propositional logic the operators `G φ` (always/globally), `F φ` (eventually), `X φ` (next), and `φ U ψ` (until); it speaks about a *single* linear future, so it captures trace properties and is the home of fairness and "within deadline." **CTL** (Clarke & Emerson, also Turing Award) quantifies over the *branching* tree of futures with path quantifiers `A` (all paths) and `E` (some path): `AG safe`, `EF reach`, `AF respond`. The two are incomparable in expressiveness; CTL\* unifies them.

The load-bearing theorem is **decidability via automata** (Vardi–Wolper): an LTL formula compiles to a Büchi automaton, and model checking reduces to checking language emptiness of the product with the system — a graph search. CTL admits a fixpoint algorithm linear in states × formula. The intuition for *which obligation*: these logics were *built* to express "this invariant holds in every reachable state forever" (`G`/`AG`) and "this required event always eventually happens, in bounded time" (`F`/`AF` with a step counter) — and to **prove it over all interleavings**, surfacing the one adversarial schedule a test would miss as a concrete counterexample trace.

## Obligations it discharges

- **INV — Safety-Invariant Maintenance (primary).** `AG ¬bad` / `G(level ≤ crest)` is the *canonical* form of an always-property, and bounded model checking plus inductive invariants give an **exhaustive** guarantee over every reachable state and every interleaving — exactly the failure mode where a single undetected tick is lethal and a sampled test never visits it. Guarantee strength: total over the modeled state space; a green result is a proof *relative to the model*, and a red result is a replayable witness trace.

- **PROG — Liveness & Real-Time Progress (primary).** `G(request → F response)` and, with an explicit cycle/tick counter, `G(trigger → F[≤k] done)` capture "the event eventually arrives" and "within its deadline." Model checking detects deadlock, livelock, and starvation as *cycles with no progress* under stated fairness constraints — the hang that is wrong at no single state. Guarantee: existence-and-bound over all fair paths.

- **COHERE / RECORD (partial).** Happens-before and single-writer coherence are temporal ordering claims (`G(write → X coherent)`, `¬(approve S action)` via `A[¬action U approved]`) and model-check cleanly when the protocol is finite-state.

It does **not** serve the deontic obligations natively: **TRIG, AUTH, DEGRADE, ATTR, COMMIT** require permission/obligation/agency modalities (deontic, STIT, commitment logics) — temporal logic has no `O`/`P`/`sees-to-it`. A contrary-to-duty reparation (**DEGRADE**) can be *encoded* as reachability of a defined safe-state, but the norm-violation semantics live elsewhere. It also does not address **PROV/REVISE** (justification structure) or **CALIB** (numeric confidence).

## A worked encoding

INV + PROG for the dam spillway (obligations INV, PROG). Real NuSMV:

```smv
MODULE main
VAR
  level   : 0..100;          -- reservoir level, crest = 90
  gate    : {closed, opening, open};
  inflow  : 0..5;
ASSIGN
  init(gate) := closed;
  next(gate) := case
    level >= 85 & gate = closed  : opening;
    gate = opening               : open;
    level < 70  & gate = open    : closed;
    TRUE                         : gate;
  esac;
  next(level) := case
    gate = open  & level > 0   : level - 1;
    gate != open & level < 100 : min(level + inflow, 100);
    TRUE                       : level;
  esac;
-- INV: crest is never exceeded on any reachable path
LTLSPEC G (level <= 90)
-- PROG: once above 85, the gate is eventually fully open
LTLSPEC G (level >= 85 -> F gate = open)
```

`NuSMV spillway.smv` either prints `is true` (exhaustive over all 101×3×6 states) or yields a counterexample trace — e.g. an inflow schedule where `opening→open` latency lets `level` reach 91 before the gate bites, falsifying `G(level<=90)` with the exact tick sequence. That trace *is* the autoharn audit artifact for the failure.

## Automation & tooling (the git-clone-runnable question — MANDATORY)

Dedicated, mature, open-source tools exist; this is a *solved* automation target.

- **NuSMV 2.7.1** (FBK) — **LGPL**, genuinely open source, BDD + SAT bounded model checking for LTL and CTL. The right default for the `git clone autoharn` deliverable precisely because LGPL permits commercial/industrial redistribution. Not in the listed local toolbox (`which nusmv` → not found) but a standard package; add to the harness manifest.
- **Spot 2.15.1** (released 2026-04-25, EPITA) — **GPLv3**, C++20 library with first-class **Python bindings** (`import spot`); `ltl2tgba` builds Büchi automata, `ltlcross`/`autcross` do *differential* equivalence checking across translators. Best fit for autoharn's INDEP/qualification needs — see below. Also not yet local (`which ltl2tgba` → not found); pip/conda installable.
- **nuXmv** (FBK) — stronger IC3/SMT infinite-state engines, but **binary-only, non-commercial/academic license**. *Kill it from the industrial deliverable*: a Federal-Reserve/NASA `git clone` cannot ship a non-commercial binary. Use it only as an offline cross-checker, never in the redistributed gate.

No encoding-into-host gymnastics are needed for the core; for the **INDEP/tool-qualification** obligation, Spot's `ltlcross` lets you cross-validate one engine's verdict against another (NuSMV vs. Spot-built automaton vs. a Z3 BMC unrolling) — three dissimilar channels, defeating the common-cause failure where one model checker's bug silently passes a bad spec.

## Honest leverage & kill-condition (life-critical seriousness)

**Load-bearing where the obligation is INV or PROG over a finite (or finitely-abstracted) control protocol**: interlocks, mode logic, handshake/settlement state machines, deadline-bounded alarms. Here a passing `G`/`AF` spec is the strongest guarantee in the whole survey short of a proof assistant — exhaustive, with free counterexamples.

**Ash where the system is genuinely infinite or data-rich.** Model checking guarantees the *model*, not the code. The lethal gap is **abstraction fidelity**: a 100-step `0..100` level model says nothing about the float arithmetic, the sensor noise, or the 700-line C that implements it. A green `AG(level≤90)` on a model that omitted the `opening` latency is *false authority* (CALIB failure) — the costume of a proof.

**Falsifiable experiment / KILL CONDITION.** Hypothesis: *for autoharn's INV/PROG obligations, an LLM-authored SMV/LTL model plus NuSMV catches injected timing/interleaving defects that a passing test suite misses.* Procedure: take a corpus of real reactive controllers; mutate each (drop a guard, off-by-one a deadline); require the LLM-built model to flag every mutant via a failing spec, AND require a **conformance/refinement check** (model ⊑ code, e.g. via runtime monitor synthesized from the LTL) tying model states to code execution. **Kill it if** either (a) the LLM-built model passes specs while the code is defective at a rate no better than the test suite (the model abstracts away the bug), or (b) ≥1 in N green verdicts corresponds to a model that does not refine the code under an independent conformance check. If the abstraction cannot be qualified to refine the artifact, the verdict is narration, not a guarantee — and autoharn must downgrade it to advisory.

## References (edification)

- Baier & Katoen, *Principles of Model Checking* (MIT Press, 2008) — the definitive textbook; teaches LTL/CTL semantics, Büchi automata, fairness, and the product construction end to end.
- Clarke, Henzinger, Veith, Bloem (eds.), *Handbook of Model Checking* (Springer, 2018) — teaches the modern engine landscape: BDD, BMC, IC3/PDR, abstraction refinement (CEGAR).
- Pnueli, "The Temporal Logic of Programs" (FOCS 1977) — teaches *why* reactive correctness needs temporal, not state, assertions.
- Spot documentation, spot-dev.lre.epita.fr — teaches the runnable API and `ltlcross` differential checking for tool qualification (INDEP).

Sources: [NuSMV 2.7.1](https://nusmv.fbk.eu/articles/271/), [Spot](https://spot-dev.lre.epita.fr/), [nuXmv](https://nuxmv.fbk.eu/)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
