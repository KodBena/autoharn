# 25 — Paraconsistent, Many-valued, Dialetheic & Fuzzy Logic (LP, FDE/Belnap, t-norm)

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
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

Logics that admit truth-values beyond {true, false} — gaps, gluts, and degrees — so that reasoning survives *contradiction* and *partial evidence* without either exploding or silently picking a side. Their job in autoharn is to keep the engine **useful in the presence of conflict**.

## Primer (becoming broadly expert)

Classical logic obeys *ex contradictione quodlibet*: from `p ∧ ¬p` it derives everything, so one conflicting sensor pair makes every gate pass vacuously. **Paraconsistent** logics break that inference. The canonical move is to add truth-values. **Belnap–Dunn FDE** (Belnap 1977, Dunn 1976) uses four — **True, False, Both, Neither** — motivated explicitly by a database fed by multiple sources: *Both* = two sources conflict, *Neither* = no source spoke. Entailment is "designated-value preservation" over the *truth* lattice while conflict is tracked on a second *information* lattice (the bilattice; Ginsberg). **Priest's LP** (Logic of Paradox, 1979) is the three-valued fragment where *Both* (B) is **designated**: contradictions are *tolerated*, not catastrophic — the dialetheist reading that some contradictions are simply true-and-false. **Many-valued** logics (Łukasiewicz, Kleene K3) generalize the truth set; **fuzzy / t-norm** logics (Hájek, *Metamathematics of Fuzzy Logic* 2001) take `[0,1]` with a continuous **t-norm** (Łukasiewicz, Gödel, product) as graded conjunction, modeling *vagueness* — "elevated creatinine," "near crest." The key intuition: these logics are built to discharge **[CONSIST](../KEY.md#consist)** — localize and quarantine contradiction so the deductive machinery keeps working instead of laundering or detonating.

## Obligations it discharges

**[CONSIST](../KEY.md#consist) — Consistency & Contradiction Containment (primary assignment).** This is the obligation these logics were *designed for*. The failure mode — two conflicting facts let a classical engine prove everything, so all gates pass vacuously, or the conflict is silently averaged into apparent consensus — is exactly what paraconsistent entailment forbids. FDE/LP semantics make a contradiction a **first-class, inspectable value** (`Both`) carried on a specific atom, not a global solvent. **Guarantee strength:** strong and *exact* — non-triviality is a theorem of the consequence relation (the engine provably does not derive an arbitrary conclusion from a glut), and the contradiction's *location* is recoverable. This is the right home for redundant-sensor disagreement, conflicting requirement sets, and merge-time fact collisions that must route to **[DEGRADE](../KEY.md#degrade)** rather than vanish.

**[PROV](../KEY.md#prov) — Claim Provenance & Groundedness (secondary).** FDE's fourth value, `Neither`, is precisely "no evidence spoke" — a typed marker for an *ungrounded* assertion, distinct from "asserted false." The bilattice's information ordering tracks how much evidence backs a claim. This buys a *medium* guarantee: it distinguishes grounded / refuted / conflicting / floating, but it does not by itself replay the evidence chain (that is [RECORD](../KEY.md#record)/REVISE work) — it gives the value lattice those states need.

**[CLASS](../KEY.md#class) — Honest Sharp Classification (secondary).** The taxonomy's own requirement — "or explicitly to *unknown*" — is a many-valued demand. K3's gap and FDE's `Neither`/`Both` supply the extra cells so a novel presentation lands in *unknown/conflicted* and surfaces loudly, instead of being forced into the nearest-wrong bucket. *Medium* guarantee.

**[CALIB](../KEY.md#calib) — Calibrated Claims (fuzzy, qualified).** t-norm logics give graded, *compositional* truth — useful for "guarantee strength matched to a quantity's kind" when the quantity is genuinely vague. The guarantee is *conditional* and carries a sharp **kill-condition** (below).

**Does NOT serve:** **[INV](../KEY.md#inv), [PROG](../KEY.md#prog), [TRIG](../KEY.md#trig), [DEGRADE](../KEY.md#degrade), [AUTH](../KEY.md#auth), [ATTR](../KEY.md#attr), [COMMIT](../KEY.md#commit), [RECORD](../KEY.md#record)** as *primary* — temporal "always/eventually," deontic detachment, agency, ordering, and commitment lifecycles are the province of temporal/deontic/STIT/linear logics. Many-valued logic supplies the *value space* those logics quantify over; it is not the modality. Do not use fuzzy truth where an exact [INV](../KEY.md#inv) invariant is required — relaxing a logic invariant to a degree is itself a [CALIB](../KEY.md#calib) failure.

## A worked encoding

FDE four-valued conflict containment for the dam ([CONSIST](../KEY.md#consist) → routed to [DEGRADE](../KEY.md#degrade)), encoded in **Z3 / SMT-LIB** by the standard *two-bit* trick: each atom carries `_t` ("told true") and `_f` ("told false"); the four assignments are T(1,0), F(0,1), Both(1,1), Neither(0,0). Verified runnable:

```smt2
(declare-const A_t Bool)(declare-const A_f Bool)   ; sensor A: reservoir above crest?
(declare-const B_t Bool)(declare-const B_f Bool)   ; sensor B (redundant)
(define-fun above_t () Bool (or A_t B_t))          ; Belnap join of evidence
(define-fun above_f () Bool (or A_f B_f))
(define-fun above_designated () Bool (and above_t (not above_f))) ; classically-true
(define-fun conflict () Bool (and above_t above_f))              ; the "Both" cell
(assert A_t)(assert (not A_f))(assert (not B_t))(assert B_f)     ; A: above, B: not-above
(check-sat)
(get-value (above_designated conflict))
```

Output: `sat` / `above_designated false, conflict true`. The contradiction is **localized** to `above` and surfaced as a Boolean `conflict` flag (route to safe-hold), and the instance stays **satisfiable** — no explosion, no vacuous clearance. A classical encoding that asserted `above` and `(not above)` as one Bool would be `unsat`, and any downstream `(=> false anything)` would pass: the exact lethal failure FDE removes.

## Automation & tooling (the git-clone-runnable question)

**Best git-clone answer: encode into Z3 (4.16.0, MIT, present locally), via the two-bit / signed reduction above** — the standard, qualifiable route for FDE, LP, K3, and any *finitely*-valued logic (Hähnle's signed-formula method; every n-valued connective becomes a Boolean truth-table constraint, mechanically generable). For **infinitely-valued / t-norm fuzzy**, Łukasiewicz and Gödel embed in `QF_LRA`/`QF_NRA` (min/max/`1−x`/truncated sum) — again Z3, present. For **ASP**, conflict-tolerant reasoning is expressible in **clingo 5.8.0** (present) via explicit `conflict/1` atoms and weak constraints rather than integrity constraints.

**Dedicated tools (WEB-VERIFIED):**
- **MULTLOG** (logic.at/multlog, v1.16a; academic/free) — a *prover generator*: input a finite truth-table specification, output a signed sequent/tableau calculus, including a published FDE/Belnap calculus. Use it to *generate and cross-check* the Z3 encoding (an [INDEP](../KEY.md#indep) second channel).
- **mNiBLoS** (CSIC; research code) — SMT-based solver for continuous t-norm logics (BL, Łukasiewicz, Gödel, product): 1-satisfiability, tautologicity, consequence. The reference if fuzzy reasoning becomes load-bearing.
- Sutcliffe et al., "Making Belnap's Useful Four-Valued Logic Useful" — maps FDE to classical ATP/TPTP, the same reduction strategy.

**Qualification ([INDEP](../KEY.md#indep)):** generate the n-valued truth tables programmatically, emit *both* a Z3 encoding and a MULTLOG calculus, and differential-test them against golden fixtures + mutation (flip a designated value; the contradiction-containment property must break). No LLM-judge in the loop — a mechanical gate.

## Honest leverage & kill-condition

**Load-bearing:** wherever conflicting-but-both-trustworthy inputs must *not* trigger ex falso and must route to a defined degraded mode — redundant sensors, merged records, contradictory requirement sets. Here the leverage is real and exact: non-triviality is provable and the encoding is tiny.

**Ash risk — fuzzy/CALIB.** t-norm conjunction is **truth-functional**; probability is not. Pushing graded fuzzy values through a long inference chain as if they were calibrated confidences yields numbers uncorrelated with evidence wearing a proof's costume.

**Falsifiable experiment + KILL CONDITION:** Build N glut/conflict fixtures with known correct degraded-mode verdicts. Run the FDE/Z3 encoding *and* a classical baseline. **KILL the FDE assignment for an obligation if** either (a) the classical baseline already contains every glut without vacuous passes on these fixtures (paraconsistency bought nothing there), or (b) for *fuzzy*, the propagated t-norm degree's ranking disagrees with a probabilistic/measured ground truth on >5% of fixtures — then fuzzy is not discharging [CALIB](../KEY.md#calib) and must be replaced by an explicit probabilistic channel.

## References (edification)

- **N. Belnap, "A Useful Four-Valued Logic" (1977)** — the founding intuition: why a multi-source database needs *Both* and *Neither*; reads directly onto sensor fusion.
- **G. Priest, *An Introduction to Non-Classical Logic* (2nd ed., 2008), ch. on LP/FDE** — cleanest primer on designated values and why explosion fails; the canonical teaching text.
- **P. Hájek, *Metamathematics of Fuzzy Logic* (2001)** — the rigorous foundation of t-norm logics; teaches exactly where graded truth is and isn't probability.
- **R. Hähnle, "Automated Deduction in Many-Valued Logics" (1993)** — the signed-formula reduction that makes the Z3/SMT encoding above mechanical and qualifiable.


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
