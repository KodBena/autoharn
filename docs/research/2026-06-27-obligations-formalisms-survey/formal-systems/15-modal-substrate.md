# 15 — Modal Logic — the substrate (K–S5, frames, tableaux) & general modal provers

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](../KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [COMMIT](../KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [STRUCT](../KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [TRACE](../KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

Modal logic is the shared mathematical chassis under almost every other formalism in this survey: it adds operators □ ("in all accessible worlds") and ◇ ("in some accessible world") to classical logic and interprets them over a graph of states, so "the property holds everywhere it must" becomes a decidable graph question rather than a slogan.

## Primer (becoming broadly expert)

The core idea (Kripke, ~1959–63): a **frame** is a set of worlds W with an **accessibility relation** R ⊆ W×W; a **model** adds a valuation. □φ is true at world w iff φ holds at *every* v with R(w,v); ◇φ iff at *some* such v. The single concept that matters most is **correspondence**: constraints on R *are* the modal axioms (Sahlqvist's theorem makes this mechanical). Reflexivity ↔ T (□φ→φ); transitivity ↔ 4 (□φ→□□φ); symmetry ↔ B; seriality ↔ D (□φ→◇φ, the deontic "ought implies can-attempt" frame). The base normal system **K** assumes nothing about R; stacking these axioms yields the lattice K ⊂ T ⊂ S4 ⊂ S5. So you do not "pick a logic" abstractly — you *state the failure mode as a frame condition* and read off the axioms. The second concept is **proof by tableau**: refuting □φ means building a world that violates φ; the systematic search either closes (theorem) or yields a finite countermodel (Fitting, Goré). Canonical: Kripke; Hughes & Cresswell; Blackburn–de Rijke–Venema (*Modal Logic*); Sahlqvist correspondence; Ladner's PSPACE-completeness. The substrate is built to discharge **"holds across all reachable states"** — i.e. [INV](../KEY.md#inv) — and its dual ◇ underwrites reachability/PROG.

## Obligations it discharges

- **[INV](../KEY.md#inv) (Safety-Invariant Maintenance)** — primary. □(invariant) over the reachability frame literally *is* "true in every reachable state across the interval it is in force." The semantics match the failure mode exactly: a single excursion at one tick is one world where φ fails, and □ is false there — the tableau exhibits that world as a countermodel rather than averaging it away. Guarantee strength: **exact** over the modeled state graph (decidable; K/T/S4 PSPACE, S5 coNP per Ladner), modulo faithfulness of the frame to the real system.
- **[PROG](../KEY.md#prog) (Liveness & Progress)** — partial/substrate. ◇(goal) expresses "a reachable state satisfies goal." Plain modal logic gives *reachability*, not fairness or deadlines; genuine "eventually/within-deadline" needs the **temporal** extension (LTL/CTL/MTL) built *on this substrate*. So modal logic supplies the operators and frame machinery; the temporal-logic section discharges [PROG](../KEY.md#prog) proper. Guarantee here: reachability/possibility only.
- **[AUTH](../KEY.md#auth), [TRIG](../KEY.md#trig), [DEGRADE](../KEY.md#degrade), [ATTR](../KEY.md#attr), [REVISE](../KEY.md#revise), [PROV](../KEY.md#prov)** — *substrate only*. Deontic (□=obligation over a seriality frame), epistemic (□=knowledge over S5), and stit (agency) logics are all modal logics with specialized accessibility relations; this section assigns them their *frame* and *proof machinery*, and the dedicated sections discharge them.

It does **not** by itself serve [CALIB](../KEY.md#calib), [CLASS](../KEY.md#class), [STRUCT](../KEY.md#struct), [COHERE](../KEY.md#cohere), [TRACE](../KEY.md#trace), [INDEP](../KEY.md#indep), [RECORD](../KEY.md#record), [COMMIT](../KEY.md#commit), [CONSIST](../KEY.md#consist) — those are about evidence/typing/process, not accessibility over worlds. ([CONSIST](../KEY.md#consist) in particular *needs the classical base weakened* — paraconsistency — which K does not provide.)

## A worked encoding

Autoharn obligation **[INV](../KEY.md#inv)**: the dam spillway controller must guarantee □¬(reservoir_above_crest ∧ ¬spillway_open) across every reachable hour. We do not hand-build a model; we discharge it by the **standard translation** ST(·,x) into first-order logic and let Z3 search for a violating reachable world (a countermodel). If Z3 returns `unsat`, no reachable state violates the invariant.

```smt2
; worlds are integers (hours); R is the hour-to-hour transition relation
(declare-fun R (Int Int) Bool)
(declare-fun above_crest (Int) Bool)
(declare-fun spillway_open (Int) Bool)
(declare-fun reach (Int) Bool)        ; reachable from initial world 0

; frame: reach is closed under R from the start world
(assert (reach 0))
(assert (forall ((w Int) (v Int)) (=> (and (reach w) (R w v)) (reach v))))

; controller rule under verification: crest detected => next state opens spillway
(assert (forall ((w Int) (v Int))
          (=> (and (reach w) (above_crest w) (R w v)) (spillway_open v))))

; NEGATED invariant: a reachable world violating  []¬(above_crest ∧ ¬open)
(declare-const bad Int)
(assert (reach bad))
(assert (above_crest bad))
(assert (not (spillway_open bad)))
(check-sat)   ; unsat  => invariant holds on all reachable worlds; sat => countermodel hour
```

`unsat` is the discharge; `sat` hands the maintainer the exact reachable hour that breaks the barrier. This same ST(·,x) skeleton is what every downstream modal section reuses.

## Automation & tooling (the git-clone-runnable question)

**Dedicated open-source tools exist and are real.**
- **MetTeL2** — a *tableau-prover generator*: you give it a logic's syntax and tableau rules, it emits a Java prover. Java, **GPL-3**, succeeds MetTeL1; distributed via mettel-prover.org. This is the highest-leverage dedicated tool for autoharn because it lets the maintainer mint a sound prover for a *bespoke* obligation-logic without writing a solver. (Verify before trusting the generated prover — see [INDEP](../KEY.md#indep).)
- **LoTREC** — generic tableau prover for modal/description logics with Kripke semantics; defines custom logics, checks SAT/validity, builds models; Java, open-source on GitHub (bilals/lotrec).
- **MSPASS / SPASS** — translates modal formulae to first-order logic with equality; modal features now folded into SPASS releases.
- **MleanCoP** — first-order modal connection prover (Prolog).

**Encoding path (no extra install needed; this is the autoharn default).** Use the **standard translation to FOL and discharge in Z3 4.16** (verified local), as above: □ becomes a bounded universal over R-successors, ◇ an existential. For the *finite/bounded* frames autoharn cares about (a fixed state graph), this is decidable and Z3 returns concrete countermodels. For S5 (epistemic), drop R and quantify over all worlds. For richer logics where quantifier search diverges, **bound the frame** (bounded model construction up to the logic's finite-model-property depth) and let Z3 or **clingo** (ASP) enumerate worlds — ASP's grounding is a natural fit when R is an explicit finite relation. So: dedicated generator (MetTeL2/LoTREC) *or* ST→Z3/clingo — two independent runnable channels, which is exactly the diversity [INDEP](../KEY.md#indep) wants.

## Honest leverage & kill-condition

**Load-bearing** for [INV](../KEY.md#inv): barrier/invariant obligations over a finite reachable state graph map onto □ with no impedance mismatch, and ST→Z3 gives exact verdicts plus countermodels today. **Ash** where the obligation is intrinsically about *deadlines, fairness, evidence, or contradiction-tolerance* — plain K/S5 gives reachability, not timing (→temporal), and its classical base explodes under contradiction (→paraconsistent [CONSIST](../KEY.md#consist)). Claiming modal logic alone "does [PROG](../KEY.md#prog)" would be the forced phoenix.

**Falsifiable experiment / KILL CONDITION.** Build a golden set of 50 dam-controller mutants (off-by-one transition, missing guard, swapped operator) with hand-labeled invariant status. Encode via ST→Z3 *and* independently via a MetTeL2-generated K-prover. **Kill condition:** if the two channels disagree on any mutant, or if either misses any seeded invariant violation (false `unsat`), the substrate-as-INV-oracle is unqualified for autoharn until the disagreement is root-caused. A second kill: if realistic spillway frames blow past Z3's time budget faster than bounded-depth enumeration can rescue, the ST→Z3 channel is demoted to MetTeL2-only.

## References (edification)

- Blackburn, de Rijke, Venema, *Modal Logic* (CUP, 2001) — the definitive modern treatment of frames, correspondence, and completeness; teaches *why* axioms = frame conditions.
- Fitting & Mendelsohn, *First-Order Modal Logic* — teaches tableaux and the standard translation you actually run in Z3.
- Tishkovsky & Schmidt, "The Tableau Prover Generator MetTeL2" (IJCAR/JELIA 2012) — teaches how to turn a custom tableau calculus into a runnable prover. [Springer](https://link.springer.com/chapter/10.1007/978-3-642-33353-8_41); platform [mettel-prover.org](http://www.mettel-prover.org/demo.php).
- Schmidt's AiML Tools page ([cs.man.ac.uk/~schmidt/tools](http://www.cs.man.ac.uk/~schmidt/tools/)) and [LoTREC on GitHub](https://github.com/bilals/lotrec) — teaches the live landscape of modal provers you can clone today.


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
