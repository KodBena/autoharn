# 04 — SMT & Classical First-order Logic (Z3 / cvc5)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [STRUCT](../KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

SMT solvers decide quantifier-free (and, heuristically, quantified) formulas in classical first-order logic *modulo* background theories — arithmetic, fixed-width bitvectors, arrays, datatypes, strings — returning `unsat` (a machine-checkable proof of impossibility) or `sat` with a concrete countermodel. They are autoharn's mechanical oracle: the engine that turns "we believe X holds" into "no assignment violates X, here is the certificate."

## Primer (becoming broadly expert)

The core idea: lift a propositional SAT search (DPLL/CDCL) so that atoms are not booleans but constraints in a decided theory, and interleave the boolean search with theory-specific decision procedures (DPLL(T)) — Nelson–Oppen combination stitches several theories together over shared equalities. The two concepts that matter: (1) **satisfiability as the universal currency** — you prove a property P by asserting ¬P and getting `unsat`; validity is dual to unsatisfiability, so every "always" claim becomes a search for one counterexample; (2) **theories with complete, fast decision procedures** for the data your system actually manipulates — Presburger/linear arithmetic (decidable), bitvectors (bit-blasting, *exactly* models machine wraparound), arrays (extensionality), algebraic datatypes. Canonical lineage: Davis–Putnam–Logemann–Loveland; Nelson & Oppen (1979, theory combination); de Moura & Bjørner's Z3 (2008); Barrett et al.'s CVC line. The intuition for *which obligation*: SMT is built to discharge **invariants over rich state** — "in every state the machine can be in, this barrier is not crossed" — by certifying the absence of a violating assignment, not by sampling.

## Obligations it discharges

**[INV](../KEY.md#inv) — Safety-Invariant Maintenance (primary).** A keep-it-true property is a verification condition: assert the transition relation and ¬(invariant′); `unsat` on the inductive step proves no single tick can cross the barrier. SMT's semantics *match* the failure mode (a transient excursion correct-on-average, lethal at one tick) because it quantifies over *all* assignments at once — it cannot miss the unsampled state. Guarantee strength: for the bounded/inductive fragment, **exact** (a proof object, replayable); for unbounded reachability via k-induction or IC3/PDR, exact up to the discovered inductive strengthening.

**[STRUCT](../KEY.md#struct) — Structural Soundness (primary).** The bitvector theory models overflow, saturation, and truncation *bit-accurately* — `bvadd` wraps exactly as the silicon does. Asserting "the sum exceeds the register" is decided, not estimated; the `-1`-as-magic-sentinel and torn-arithmetic classes become discharged lemmas. Strength: **exact** over fixed-width semantics.

**[CALIB](../KEY.md#calib) & [INDEP](../KEY.md#indep) — Substantiated Claims / Independent Adjudication (primary, and structural to autoharn).** This is where SMT earns its keep against the LLM-authored-encoding risk. An LLM may *write* the constraints, but the verdict is rendered by Z3's CDCL core and certified by an `unsat` proof an external checker can replay. The oracle does not share the producer's bias: a claim "wearing a proof's costume" (the 4× chemo lemma that looks like a Z3 certificate but was never submitted) is exactly what mechanical re-checking kills. Strength: **exact**, *conditioned on the encoding being faithful* (see kill-condition).

**[CLASS](../KEY.md#class) — Honest Sharp Classification.** Totality and mutual-exclusivity of a partition are first-order validities: `unsat` on "two cells both fire" and on "no cell fires" proves MECE. Strength: **exact**.

**[COHERE](../KEY.md#cohere) — Single-Authority Coherence.** Two sides re-deriving one wire layout/unit/key is an equivalence check: assert the two definitions differ, expect `unsat`. Strength: **exact** for the modeled fields.

**[AUTH](../KEY.md#auth) (partial).** Permission *closure* and norm-precedence over a fixed action set encode as constraints (deterministic priority resolution checkable for totality), but SMT has no native deontic operator — it models the *resolved* gate, not the obligation's normative force. Assign [DEGRADE](../KEY.md#degrade)/COMMIT/ATTR to deontic/STIT systems; SMT is the arithmetic substrate beneath them.

**Does NOT serve well:** **[PROG](../KEY.md#prog)/liveness** ("eventually" needs fairness and well-founded ranking — that is model checking / ranking-function synthesis, where SMT is a *subroutine*, not the decider); **[CONSIST](../KEY.md#consist)/REVISE** (SMT is classically explosive — `unsat` is global, ex falso is the engine's *premise*; paraconsistency and AGM revision are foreign to it); **[PROV](../KEY.md#prov)** chains beyond unsat-core granularity.

## A worked encoding

Inductive safety of a dam spillway controller ([INV](../KEY.md#inv)): the reservoir level must never exceed crest. We prove the *inductive step* — any legal transition from a safe state lands safe — in SMT-LIB 2, runnable in Z3 4.16.0.

```smt2
(set-logic QF_LIA)
(declare-const level Int)      ; current reservoir level
(declare-const inflow Int)     ; this tick's inflow
(declare-const gate Bool)      ; spillway open?
(define-fun CREST () Int 1000)
(define-fun RELEASE () Int 50)

; controller: open the gate once within 50 of crest
(define-fun ctrl () Bool (= gate (>= level (- CREST RELEASE))))
; next-state
(define-fun next () Int (ite gate (+ level inflow (- RELEASE)) (+ level inflow)))

(assert (<= 0 inflow)) (assert (<= inflow RELEASE))   ; bounded inflow assumption
(assert (<= level CREST))                              ; inductive hypothesis: start safe
(assert ctrl)
(assert (> next CREST))                                ; NEGATION of the invariant
(check-sat)                                            ; expect: unsat  => step preserved
(get-model)                                            ; on sat: the counterexample tick
```

`unsat` certifies the controller cannot cross the crest in one tick under the inflow bound; flip the bound to `(<= inflow 200)` and Z3 returns `sat` with the *exact* inflow/level that floods — the single lethal tick, surfaced at origin. The assumption (`inflow <= RELEASE`) is itself an obligation that must be discharged elsewhere ([RECORD](../KEY.md#record) it as a monitored premise).

## Automation & tooling (the git-clone-runnable question)

Dedicated, mature, **WEB-VERIFIED**: **Z3** — MIT license, latest **4.16.0** (released 2026-02-19); confirmed locally (`z3 --version` → `Z3 version 4.16.0`, `z3-solver` 4.16.0.0 on PyPI). **cvc5** — modified-BSD (3-clause) license, latest **1.3.4** (2026-05-07); not yet installed locally. Both speak SMT-LIB 2.6, emit proofs (Z3's `(get-proof)`, cvc5's LFSC/Alethe), and ship Python/C/OCaml APIs. Maturity: industrial — both anchor the annual SMT-COMP and back Dafny, F*, SPARK, Boogie. Autoharn's path is direct: emit SMT-LIB, shell to `z3 -smt2`, parse `sat/unsat/unknown`, and for every load-bearing `unsat` **persist the proof object** so an independent replay (cvc5 as a *diverse second checker* — different codebase, no common cause, satisfying [INDEP](../KEY.md#indep)) confirms it. The git-clone deliverable embeds Z3 4.16.0 as the default oracle and cvc5 as the dissimilar adjudicator.

## Honest leverage & kill-condition

Load-bearing: [INV](../KEY.md#inv), [STRUCT](../KEY.md#struct), [CLASS](../KEY.md#class), [COHERE](../KEY.md#cohere), and SMT-as-oracle for [CALIB](../KEY.md#calib)/INDEP — anywhere the property is a quantifier-free constraint over arithmetic/bitvectors/arrays. Ash: liveness, deontic force, paraconsistent conflict, and *unbounded* reachability without a found inductive invariant (k-induction may return `unknown`; quantified fragments are undecidable and Z3 may diverge — `unknown` must be treated as **fail-closed**, never green).

The real risk is not the solver — it is the **encoding tax**: a faithful-looking SMT model of an unfaithful abstraction. **Falsifiable experiment:** build a mutation/golden harness — inject N seeded faults into the *system under analysis* (off-by-one in `RELEASE`, sign flip, dropped bound) and require the encoding to flip `unsat`→`sat` on every one; inject M mutations into the *encoding itself* and require differential disagreement between Z3 and cvc5. **KILL CONDITION:** if the harness shows the encoding returns `unsat` (green) on any seeded *system* fault — i.e. the model proves a property the real system violates — then SMT is not discharging the obligation here; it is laundering false authority, and the obligation must be reassigned or the encoding qualified before trust. Honest result: SMT's guarantee is exact *over its model*, and the model is on trial alongside the LLM that wrote it.

## References (edification)

- **de Moura & Bjørner, "Z3: An Efficient SMT Solver" (TACAS 2008)** — the architecture paper; teaches DPLL(T) and theory combination as Z3 realizes them.
- **Barrett, Sebastiani, Seshia & Tinelli, "Satisfiability Modulo Theories" (Handbook of Satisfiability, 2nd ed., 2021)** — the canonical survey; teaches each theory's decision procedure and where decidability ends.
- **Kroening & Strichman, "Decision Procedures: An Algorithmic Point of View" (2nd ed., 2016)** — teaches you to *build* the procedures, so you can audit your own encodings.
- **SMT-LIB Standard 2.6 (smt-lib.org)** — the input language and theory definitions; teaches the exact semantics your `unsat` is certifying.

Sources: [Z3 releases](https://github.com/z3prover/z3/releases), [cvc5 releases](https://github.com/cvc5/cvc5/releases)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
