# 14 — Inductive Logic Programming (Popper/Aleph)

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
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [TRACE](../KEY.md#trace) | Traceability, Coverage & Change-Impact — hazard→req→design→code→test links total & navigable; coverage measured; change-impact closed on the artifact |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

ILP synthesizes human-readable, first-order logic *programs* (definite clauses) from positive/negative examples plus background knowledge — making it autoharn's *specification-recovery* engine: it reconstructs the rule a corpus actually obeys, so you can diff de-facto behavior against the ratified mandate.

## Primer (becoming broadly expert)

ILP sits at the intersection of logic programming and machine learning: given background knowledge `B`, positive examples `E⁺`, negative examples `E⁻`, the task is to find a hypothesis `H` (a set of Horn clauses) such that `B ∧ H ⊨ E⁺` and `B ∧ H ⊭ E⁻`. Unlike statistical learners, the output is a *symbolic program* — every learned clause is inspectable, executable, and traces to the examples that forced it. Founded by Muggleton (1991); the two ideas that matter are the **hypothesis space defined by a language bias** (mode/type declarations bounding what clauses are admissible) and the **generality lattice** (θ-subsumption) the search navigates. Classical systems (Aleph, Progol) do bottom-clause-driven greedy cover-set search. The modern shift is **Learning From Failures** (Cropper & Morel, 2021): Popper encodes the *constraint* "do not generate hypotheses that generalize a failed one" as ASP constraints over a meta-program, pruning the space soundly and learning *recursive*, optimal (smallest) programs. ILP is built to discharge the obligation of *recovering a latent specification and grounding a general rule in the specific evidence that entails it* — induction made auditable, with the search certificate explaining why no smaller/other hypothesis fits.

## Obligations it discharges

**[TRACE](../KEY.md#trace) — Traceability & change-impact closure (primary).** ILP's semantics match [TRACE](../KEY.md#trace)'s failure mode of *silent scope-narrowing*: feed it the audit corpus (logged decisions, the test suite's input/output pairs, exercised branches) and it returns the *actual* rule the artifact implements. Diff that against the written requirement and an unimplemented requirement or an off-screen behavior surfaces mechanically — the de-facto spec is now an object, not a narration. Guarantee strength: **defeasible-but-explicit** — the recovered rule is exact over the corpus, conjectural beyond it.

**[PROV](../KEY.md#prov) — Claim provenance & groundedness.** Every learned clause resolves to a finite, replayable chain: the examples it covers and the negatives it excludes. Unlike a neural classifier, there is no free-floating fact — the hypothesis *is* the inspectable warrant. Matches [PROV](../KEY.md#prov)'s confabulation failure mode: a clause that covers no positive cannot be emitted.

**[CLASS](../KEY.md#class) — Honest sharp classification.** ILP yields a symbolic, MECE rule set *plus genuine abstention*: when no clause covers an instance, it is loudly "uncovered," not coerced into the nearest bucket. This is exactly [CLASS](../KEY.md#class)'s defense against silent mis-sortation.

**[INDEP](../KEY.md#indep) — Independent adjudication (conditional).** An ILP-recovered rule is a *differential oracle*: re-derived from data by a mechanism with no access to the developer's source. It catches the developer's blind spot **only if example provenance is independent of the artifact under test** (see kill-condition).

**Does NOT serve:** [INV](../KEY.md#inv), [PROG](../KEY.md#prog), [TRIG](../KEY.md#trig), [DEGRADE](../KEY.md#degrade), AUTH-enforcement, [ATTR](../KEY.md#attr), [COMMIT](../KEY.md#commit), [REVISE](../KEY.md#revise), [CONSIST](../KEY.md#consist), [COHERE](../KEY.md#cohere), [RECORD](../KEY.md#record). ILP is *offline hypothesis generation*, not a runtime or proof guarantee. Its output is always a **candidate** that must be discharged by a verifier (Z3/TLC/ASP) before it is load-bearing — induction is sound over the sample, conjectural over the domain.

## A worked encoding

Recover the sanctioned deploy-gate from an audit corpus (autoharn [AUTH](../KEY.md#auth)/TRACE): does the log obey "deploy permitted iff a human approved and we are not in a freeze window," and is any logged deploy *unexplainable* by that grammar?

`bias.pl`
```prolog
max_vars(2). max_body(3). max_clauses(1).
head_pred(deploy_ok,1).
body_pred(approved,1).
body_pred(human_actor,1).
body_pred(in_freeze,1).
type(deploy_ok,(event,)).  type(approved,(event,)).
type(human_actor,(event,)). type(in_freeze,(event,)).
direction(deploy_ok,(in,)). direction(approved,(in,)).
```
`bk.pl`
```prolog
approved(e1).  human_actor(e1).
approved(e2).  in_freeze(e2).
approved(e3).  human_actor(e3).
```
`exs.pl`
```prolog
pos(deploy_ok(e1)).  pos(deploy_ok(e3)).
neg(deploy_ok(e2)).
```
Run: `python popper.py corpus/` →
```prolog
deploy_ok(E):- approved(E), human_actor(E).
```
Popper learns the gate the corpus *actually* enforces. The [TRACE](../KEY.md#trace)/AUTH gate is the **unsatisfiable case**: add `pos(deploy_ok(e9))` with only `approved(e9)` in `bk.pl` (deployed without a human, no freeze info). No hypothesis in the bias covers all positives without covering the negative; Popper returns **"no solution."** That mechanical failure *is* the finding — a logged deployment that the sanctioned permission vocabulary cannot explain = authority leak. Aleph expresses the same with `:- modeh(1,deploy_ok(+event))`, `modeb(*,approved(+event))`, `induce/0`, and reports per-clause coverage statistics (a [CALIB](../KEY.md#calib) hook).

## Automation & tooling (git-clone-runnable)

**Two dedicated, mature, locally-runnable tools — no encoding gap.**

- **Popper** — `github.com/logic-and-learning-lab/Popper`, **MIT**, current release **v5.0.1 (2025)**. Host: Python over an **ASP/clingo** backend (clingo **5.8.0 present locally**; `swipl`/`python3` present). Install `pip install git+https://github.com/logic-and-learning-lab/Popper@main`. Learns recursive, optimal programs; supports predicate invention and (noisy/`maxn`) tolerance. This is the recommended default.
- **Aleph** — SWI-Prolog pack (`?- pack_install(aleph).`), port by F. Riguzzi of Srinivasan's Aleph v5; runs on the local **SWI-Prolog 9.3.31**. Mature, battle-tested, GPL-style academic license; best when you already live in Prolog and want coverage-scored single-clause induction.

Because Popper *compiles to ASP*, its verdicts are themselves re-checkable on the local clingo install — the learned program and the "no solution" certificate can be independently replayed, satisfying the qualification requirement for an LLM-orchestrated pipeline.

## Honest leverage & kill-condition

**Load-bearing:** as a *generator-of-candidates and differential-diff oracle* for [TRACE](../KEY.md#trace)/PROV/CLASS — recovering the latent rule from autoharn's own audit logs and test corpus, then diffing it against the ratified requirement to surface scope-narrowing and unexplainable behaviors a same-frame review ratifies. **Ash:** anywhere a *guarantee* is required ([INV](../KEY.md#inv)/PROG/AUTH-enforcement) — an induced rule is conjectural and must be handed to Z3/TLC, never trusted as a proof.

**Falsifiable experiment:** build a golden corpus with a known target gate-rule and seeded violations (deploys without approval, freeze-window breaches). Measure: (a) does Popper/Aleph recover the target rule from clean examples at realistic predicate arity (≤ minutes), and (b) does recovered-rule-plus-abstention/no-solution flag the injected anomalies **above a trivial frequency-count baseline**?

**KILL CONDITION:** if either (a) recovery fails or explodes combinatorially at the arities real autoharn obligations need, or (b) anomaly detection does not beat the frequency baseline — then ILP is ash here and the job reduces to a plain ASP integrity constraint. **Separately, [INDEP](../KEY.md#indep) is killed by common-cause:** if the examples are produced by the same artifact under test, the recovered rule inherits its bug and the "independent" oracle is theater — an explicit example-provenance audit (provenance ≠ artifact-under-test) is mandatory before any ILP verdict counts as independent.

## References (edification)

- **Cropper & Dumančić, "Inductive Logic Programming at 30: A New Introduction," JAIR 2022 (arXiv 2008.07912)** — the modern map of the field, systems, and biases; start here.
- **Cropper & Morel, "Learning Programs by Learning from Failures," MLJ 2021** — the Popper algorithm and the ASP-constraint LFF semantics that make search certificates auditable.
- **Srinivasan, *The Aleph Manual*** — operational mode/determination declarations and coverage-scored induction; the practitioner's reference for the Prolog host.
- **Muggleton, "Inductive Logic Programming," 1991** — the founding formulation (`B ∧ H ⊨ E`) and the generality lattice; the intuition everything else refines.

Sources: [Popper](https://github.com/logic-and-learning-lab/Popper), [Popper releases](https://github.com/logic-and-learning-lab/Popper/releases), [Aleph (SWI port)](https://github.com/friguzzi/aleph), [ILP at 30](https://arxiv.org/pdf/2008.07912)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
