# 18 — Provability Logic (GL, Löb) — self-reference & the anti-self-certification guardrail

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

GL is the modal logic of "is provable," and its central theorem (Löb) is the exact mathematical statement of why a system cannot ground its own trustworthiness from the inside — making it the formal backbone of autoharn's rule that no producer may certify itself.

## Primer (becoming broadly expert)

Read `□A` as "A is provable in the system" (Solovay: the provability predicate of Peano Arithmetic). GL = modal **K** + the **Löb axiom** `□(□A → A) → □A`, which entails transitivity (axiom 4) and, crucially, the *failure* of reflection: `□A → A` is **not** a theorem unless `A` itself is. **Löb's theorem** (1955): if `⊢ □A → A` then `⊢ A`. Contrapositive bite: a system that could internally prove "whatever I prove is true" would thereby prove *everything* it claims — so a consistent system *cannot* hold the schema `□A → A`. Gödel's Second Incompleteness Theorem (`¬□⊥`, "I cannot prove my own consistency") is the instance `A = ⊥`. The Kripke semantics is the tell: GL is sound and complete for **finite, transitive, irreflexive (converse-well-founded)** frames — there are no infinite ascending chains and no self-loops. The intuition for *which obligation*: GL is built to discharge the meta-claim "this certification is real," and its theorem is a *prohibition* — self-referential trust is vacuous. Canonical: Boolos, *The Logic of Provability* (1993); Löb (1955); Solovay (1976); Verbrugge's SEP article.

## Obligations it discharges

**[INDEP](../KEY.md#indep) — Independent Adjudication (primary).** The mission's own wound — "the deflation-detector that deflated," an LLM judging LLM output — is *literally* the move `□A → A`: "I derived it, therefore it holds." Löb's theorem says this inference is sound only when `A` is *independently* provable; the self-certifying step adds nothing. GL's converse-well-founded frames are the semantic image of [INDEP](../KEY.md#indep)'s requirement: every chain of justification must terminate at a source the producer did not author. **Guarantee strength:** a *structural impossibility* result — not "we tried to keep the verifier independent" but "a verdict whose support resolves to itself is provably worthless." This is the strongest kind of guarantee: it forbids an entire class of assurance topologies.

**[CALIB](../KEY.md#calib) — Substantiated & Calibrated Claims.** A claim "wearing a proof's costume but never discharged by an independent oracle" (a fake Z3 certificate) is exactly `□A` asserted while `A` is ungrounded. GL formalizes why the costume is not the proof: internal `□A` does not license `A`. **Strength:** detection of the failure topology, not the numeric content.

**[CONSIST](../KEY.md#consist) / [RECORD](../KEY.md#record) (secondary).** `¬□⊥` underwrites consistency-self-doubt ([CONSIST](../KEY.md#consist)): a sound store must not certify its own freedom from contradiction. For [RECORD](../KEY.md#record), the converse-well-foundedness condition forbids an assurance argument that closes a gap by citing its own conclusion.

**Does NOT serve:** GL is silent on *first-order* safety content — it does not check [INV](../KEY.md#inv) barriers, [PROG](../KEY.md#prog) deadlines, [TRIG](../KEY.md#trig) detachment, or [DEGRADE](../KEY.md#degrade) reparation. It governs the *shape of the trust graph over* those checks, never their substance. Assigning GL to discharge an invariant is a category error; assign it to govern *who is allowed to vouch for* the invariant's discharge.

## A worked encoding

The operational kernel is converse-well-foundedness of the *justified-by* relation in autoharn's assurance graph: a claim is grounded only via a finite descent to an external oracle; any claim resting on itself (or a mutual-admiration cycle) is a Löb violation. In clingo:

```prolog
% --- autoharn assurance graph (INDEP) ---
% support(C,S): claim C rests on source S      external(S): independent oracle
claim(dose_safe). claim(bound_proven). claim(llm_lemma).
external(z3_cert). external(signed_egfr).

support(dose_safe, bound_proven).
support(bound_proven, llm_lemma).     % "proven" by an LLM-authored lemma...
support(llm_lemma,  bound_proven).    % ...whose only warrant is the claim it backs

% --- Löb guardrail: grounded = finite descent to an external oracle ---
grounded(C) :- external(C).
grounded(C) :- support(C,S), grounded(S).
self_certifying(C) :- claim(C), not grounded(C).

#show self_certifying/1.
```

Running it (`clingo loeb.lp`) yields `self_certifying(dose_safe) self_certifying(bound_proven) self_certifying(llm_lemma)` — the 4× overdose ships *green by topology*: its support relation has a cycle, no descent to `z3_cert`/`signed_egfr`. Re-point `support(bound_proven, z3_cert)` and the set empties. The negation-as-failure here is faithful to GL: stable-model groundedness *is* the converse-well-founded fixpoint.

## Automation & tooling (the git-clone-runnable question)

**Two layers, both runnable today.**

(1) *Guardrail as graph property* (the load-bearing one, above): pure ASP in **clingo 5.8.0** (MIT-style, verified local: `clingo version 5.8.0`) or Prolog/Datalog. Self-certification = a non-well-founded support cycle; ASP's well-founded/stable semantics computes exactly the GL frame condition. Zero new dependencies.

(2) *Checking GL-validity of a modal assurance formula* (e.g., "is `□safe → safe` a theorem here?" — it must **not** be). No single dominant standalone GL solver, but real options: **LoTREC** (generic tableau prover, Java 8+, GPL-ish academic, GitHub `bilals/lotrec`) lets you *define* GL by declaring transitive + converse-well-founded Kripke rules and run satisfiability/validity; **MetTeL2** (Tishkovsky, `mettel-prover.org`) generates a tableau prover from a GL rule specification; **HOL Light** carries a *machine-checked* GL metatheory plus a decision-procedure tactic via the labelled sequent calculus **G3KGL** (Maggesi–Brogi, *JAR* 2023). For a self-contained autoharn dependency, encode GL's finite-model property directly into **Z3 4.16** (verified local): GL is decidable/PSPACE; a formula is GL-valid iff it has no countermodel on a finite transitive irreflexive frame, so bounded countermodel search over `worlds : Int`, an `R : world→world→Bool` constrained transitive + acyclic, with `box(A,w) := ∀v. R(w,v)→holds(A,v)`, gives a sound validity check (complete up to the model-size bound). **Encoding plan, not a shrug:** clingo for the graph guardrail (ship now); Z3 finite-frame search for modal-formula adjudication; LoTREC/HOL Light as the qualifying oracle when a GL verdict is itself load-bearing.

## Honest leverage & kill-condition

**Load-bearing:** GL is the *only* tool in the suite that speaks about the assurance graph's own topology, and the mission already paid in blood for the lesson it formalizes. The clingo guardrail is cheap, runnable, and catches the precise failure (self/mutual certification) that defeats LLM-on-LLM review. This is genuine phoenix, not cheerleading: the leverage is *structural detection*, which no first-order check provides.

**Ash boundary:** GL contributes *nothing* to whether a given check is correct — it cannot tell a real Z3 certificate from a forged one; it only insists *some* external oracle terminate the chain. If autoharn's "external" tagging is itself gameable, GL's guarantee is hollow. It is meta-discipline, not content verification.

**Falsifiable experiment + KILL CONDITION:** Build a corpus of 200 assurance graphs, half seeded with self-certifying cycles (direct, length-2 mutual, and length-5 laundered). Run the clingo guardrail. **KILL** the GL-guardrail claim if it fails to flag any seeded cycle, OR if its `external` predicate can be satisfied by a node the producer authored (i.e., the independence tag is not mechanically enforced upstream) — in that case GL is decorative and [INDEP](../KEY.md#indep) must be discharged by provenance ([PROV](../KEY.md#prov)), not by topology. **Survive** only if every laundered cycle is caught and `external` is bound to a cryptographically independent source.

## References (edification)

- **Boolos, *The Logic of Provability* (CUP, 1993).** The canonical text — GL, Löb, Solovay's arithmetical completeness; teaches why "provable" behaves modally.
- **Löb, "Solution of a problem of Leon Henkin," *JSL* 20 (1955).** The original theorem; teaches the exact form of the self-certification collapse.
- **Verbrugge, "Provability Logic," *Stanford Encyclopedia of Philosophy*.** Best modern primer; teaches semantics (converse-well-founded frames) and the incompleteness connection.
- **Maggesi & Brogi, "Mechanising Gödel–Löb Provability Logic in HOL Light," *JAR* (2023), arXiv:2205.03659.** Teaches a *machine-checked* GL decision procedure (G3KGL) — the qualification path for a trusted GL oracle.


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
