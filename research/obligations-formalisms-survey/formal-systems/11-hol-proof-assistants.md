# 11 — Higher-order Logic, Dependent Types & Proof Assistants (Coq/Lean/Isabelle)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [STRUCT](../KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [TRACE](../KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

The strongest guarantee a machine can give: a property is not tested or model-checked but *proved*, with the proof itself a small inspectable object re-checkable by an independent kernel. This is the formalism you assign when "wrong once is catastrophic" and the cost of the full encoding tax is justified.

## Primer (becoming broadly expert)

Classical first-order logic quantifies only over individuals. **Higher-order logic (HOL)** quantifies over *functions and predicates* — you can state "for all properties P, …", which is exactly what an invariant over all reachable states or all writers needs. **Dependent type theory** (Martin-Löf; the Calculus of Inductive Constructions underlying Rocq/Coq; Lean's type theory) goes further: *types may depend on values*, so `Vector A n` (a list of statically-known length `n`) is a type, and a proof is literally a term whose type is the proposition (the **Curry-Howard correspondence**: propositions-as-types, proofs-as-programs). The load-bearing idea is the **trusted kernel / de Bruijn criterion**: however elaborate the proof search (tactics, automation, an LLM), the final certificate is rechecked by a tiny kernel you can audit line-by-line. Canonical landmarks: Gödel/Church's higher-order systems; de Bruijn's Automath; the four-color theorem (Gonthier, Coq); seL4 (Klein et al., Isabelle/HOL — a verified OS kernel); CompCert (Leroy, Coq — a verified C compiler whose output is provably faithful to its source). The intuition: this logic is built to discharge obligations where you must *guarantee a universally-quantified property over an unbounded space*, not sample it.

## Obligations it discharges

- **[INV](../KEY.md#inv) — Safety-Invariant Maintenance (primary).** A machine-checked theorem `∀ s, Reachable s → Invariant s` is a guarantee over *every* reachable state, not the finite frontier a model checker reaches before exhausting memory. This is the unique semantic match for "keep-it-true across the whole interval": the proof obligation literally *is* the universal quantifier, and the kernel refuses any state the proof skips. Guarantee strength: deductive certainty modulo the kernel and the axioms/specification (the strongest tier autoharn can buy).
- **[STRUCT](../KEY.md#struct) — Structural Soundness by Construction (primary).** Dependent types make defect classes *unrepresentable*: an out-of-bounds index, an unhandled `None`, or a unit mismatch becomes a term that *does not typecheck*. "Make illegal states unrepresentable" is the type-theoretic credo. Guarantee: compile-/check-time exclusion, not runtime catch.
- **[CALIB](../KEY.md#calib) — Substantiated & Calibrated Claims (primary).** A `Qed` is the gold standard of "a claim backed by an independently re-checkable artifact." Its proof term is precisely the certificate whose absence [CALIB](../KEY.md#calib)'s failure mode (a proof's costume with no oracle) names.
- **[INDEP](../KEY.md#indep) — Independent Adjudication (strong).** The kernel is the canonical bias-independent checker: proof *production* (untrusted tactics, LLM) is cleanly separated from proof *checking* (small kernel). An LLM may author the proof script; the kernel adjudicates without sharing its bias — exactly the structure autoharn demands for qualifying LLM-authored encodings.
- **[TRACE](../KEY.md#trace) / [RECORD](../KEY.md#record) (supporting).** A dependently-typed development links specification → theorem → proof term navigably; the proof object is a durable, replayable artifact. It does not by itself supply timestamps or happens-before; pair with [RECORD](../KEY.md#record)'s logging.
- **[PROV](../KEY.md#prov) / [REVISE](../KEY.md#revise) (partial).** A proof *is* a finite groundedness chain to admitted axioms ([PROV](../KEY.md#prov)), and `Qed` fails if any leaf is unjustified. But proof assistants are monotonic: they do not natively *retract* and re-justify ([REVISE](../KEY.md#revise)) — that is belief-revision/TMS territory, assigned elsewhere.

**Does NOT serve well:** [PROG](../KEY.md#prog)/real-time deadlines (HOL proves functional correctness, not WCET — assign to timed automata / RT model checking), [CONSIST](../KEY.md#consist) (the kernel rejects inconsistency rather than reasoning *within* it — assign to paraconsistent logic), and the deontic obligations [TRIG](../KEY.md#trig)/AUTH/DEGRADE/ATTR/COMMIT (no native normative operators — assign to deontic/STIT logics, though their *metatheory* can be formalized in HOL).

## A worked encoding

[INV](../KEY.md#inv) for the dam (taxonomy item 1): the reservoir level must never sit above crest while the spillway gate is commanded shut. In Lean 4:

```lean
structure St where
  level : Int      -- reservoir level, cm above datum
  crest : Int
  gateOpen : Bool

def Invariant (s : St) : Prop := s.level > s.crest → s.gateOpen

-- the controller: open the gate whenever level exceeds crest
def step (s : St) : St :=
  { s with gateOpen := decide (s.level > s.crest) || s.gateOpen }

-- THEOREM: every post-step state satisfies the barrier invariant
theorem step_preserves_inv (s : St) : Invariant (step s) := by
  unfold Invariant step
  intro h
  simp [decide_eq_true_eq] at *
  simp [h]
```

`step_preserves_inv` is universally quantified over *all* `s` — no input escapes it — and `decide`/`Int` give honest integer semantics rather than a float that silently saturates ([STRUCT](../KEY.md#struct)). Mutating the controller so it forgets the `|| s.gateOpen` or flips the comparison makes the proof fail to typecheck: the kernel is the mechanical gate. The same skeleton in Rocq (`Theorem … Qed.`) or Isabelle/HOL (`lemma … by auto`) is a line-for-line transliteration.

## Automation & tooling (the git-clone-runnable question)

Three production-grade, dedicated open-source tools, all WEB-VERIFIED current as of June 2026:

- **Rocq Prover (formerly Coq)** — LGPL-2.1, **9.2.0** (2026-03-30). Mature (30+ years; CompCert, four-color theorem). Dependent CIC.
- **Lean 4** — Apache-2.0, **4.31.0** stable (2026-06-13; 4.32-rc in flight). Mature and fast-moving; huge Mathlib; excellent metaprogramming for LLM-generated tactics.
- **Isabelle/HOL** — BSD-style, **Isabelle2025-2** (Jan 2026). Mature (seL4); **Sledgehammer** dispatches goals to external ATPs/SMT and is the best "push-button" experience.

Local check: none installed here, but **Z3 4.16.0 is present** — and Z3 *is* the backend Sledgehammer/`smt`/`coqhammer` call, so the autoharn deliverable can ship a `hammer`-first workflow. The git-clone path: vendor one assistant (Lean is the lightest single-binary install via `elan`), put the spec + theorems under `proofs/`, and gate CI on `lake build` / `rocq compile` / `isabelle build` — a red kernel is a failed build. For obligations needing decidable arithmetic, the assistant *discharges into Z3* and reflects the certificate back, so the heavy automation already on this machine is reused rather than duplicated. No tool is "missing"; the question is only *which* host, and the answer is a real, installable, kernel-checked binary.

## Honest leverage & kill-condition

**Load-bearing** for [INV](../KEY.md#inv)/STRUCT/CALIB/INDEP on the small, stable, catastrophic core — the barrier logic, the settlement-amount type, the authorization predicate. There the proof term is the single most trustworthy artifact in the repo, and the kernel is the independent adjudicator autoharn's [INDEP](../KEY.md#indep) obligation requires.

**Ash** if pointed at the whole system: the encoding tax is real, proofs are brittle under churn, and — the sharp risk — a proof guarantees only that *code meets spec*; a wrong spec is proved "correctly." The LLM that writes the proof can also write the comfortable spec.

**Falsifiable experiment.** Take 30 autoharn invariants. Have the LLM author Lean/Rocq specs *and* proofs. Independently mutate each implementation (golden/mutation fixtures); require the kernel to reject every mutant. Separately, have a *second, spec-blind* reviewer mutate the *specifications* and measure how many vacuous/wrong specs still `Qed`. **KILL CONDITION:** if the LLM-authored specifications admit ≥10% vacuous-but-passing proofs (e.g., a `True`-equivalent invariant, an unsatisfiable antecedent making [INV](../KEY.md#inv) trivially hold), then the proof's authority is an illusion at this stakes level and HOL must be demoted to "kernel-checks human-authored specs only" — automation of the *spec*, not just the proof, is off the table. Vacuity detection (does the antecedent ever hold? is the theorem non-trivial?) must itself be a mechanical gate, because an LLM judging spec-faithfulness shares the authoring bias.

## References (edification)

- **Pierce et al., *Software Foundations* (Vol. 1–3, Coq/Rocq), online.** Teaches Curry-Howard, dependent types, and proof tactics from zero — the canonical on-ramp.
- **Avigad, de Moura et al., *Theorem Proving in Lean 4* (online).** Teaches the modern dependent-type workflow and metaprogramming most amenable to LLM-driven proof authoring.
- **Klein et al., "seL4: Formal Verification of an OS Kernel" (SOSP 2009).** Teaches what an end-to-end HOL guarantee over a real safety-critical system actually costs and covers — and what it does *not*.
- **Leroy, "Formal Verification of a Realistic Compiler" (CACM 2009, CompCert).** Teaches the spec-is-the-real-trust-boundary lesson directly relevant to autoharn's kill-condition.

Sources: [Rocq releases](https://rocq-prover.org/releases), [Lean 4 releases](https://github.com/leanprover/lean4/releases), [Isabelle](https://isabelle.in.tum.de/).


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
