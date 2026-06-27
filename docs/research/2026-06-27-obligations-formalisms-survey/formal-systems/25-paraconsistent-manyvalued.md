# 25 — Paraconsistent, Many-valued, Dialetheic & Fuzzy Logic (LP, FDE/Belnap, t-norm)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

Logics that admit truth-values beyond {true, false} — gaps, gluts, and degrees — so that reasoning survives *contradiction* and *partial evidence* without either exploding or silently picking a side. Their job in autoharn is to keep the engine **useful in the presence of conflict**.

## Primer (becoming broadly expert)

Classical logic obeys *ex contradictione quodlibet*: from `p ∧ ¬p` it derives everything, so one conflicting sensor pair makes every gate pass vacuously. **Paraconsistent** logics break that inference. The canonical move is to add truth-values. **Belnap–Dunn FDE** (Belnap 1977, Dunn 1976) uses four — **True, False, Both, Neither** — motivated explicitly by a database fed by multiple sources: *Both* = two sources conflict, *Neither* = no source spoke. Entailment is "designated-value preservation" over the *truth* lattice while conflict is tracked on a second *information* lattice (the bilattice; Ginsberg). **Priest's LP** (Logic of Paradox, 1979) is the three-valued fragment where *Both* (B) is **designated**: contradictions are *tolerated*, not catastrophic — the dialetheist reading that some contradictions are simply true-and-false. **Many-valued** logics (Łukasiewicz, Kleene K3) generalize the truth set; **fuzzy / t-norm** logics (Hájek, *Metamathematics of Fuzzy Logic* 2001) take `[0,1]` with a continuous **t-norm** (Łukasiewicz, Gödel, product) as graded conjunction, modeling *vagueness* — "elevated creatinine," "near crest." The key intuition: these logics are built to discharge **CONSIST** — localize and quarantine contradiction so the deductive machinery keeps working instead of laundering or detonating.

## Obligations it discharges

**CONSIST — Consistency & Contradiction Containment (primary assignment).** This is the obligation these logics were *designed for*. The failure mode — two conflicting facts let a classical engine prove everything, so all gates pass vacuously, or the conflict is silently averaged into apparent consensus — is exactly what paraconsistent entailment forbids. FDE/LP semantics make a contradiction a **first-class, inspectable value** (`Both`) carried on a specific atom, not a global solvent. **Guarantee strength:** strong and *exact* — non-triviality is a theorem of the consequence relation (the engine provably does not derive an arbitrary conclusion from a glut), and the contradiction's *location* is recoverable. This is the right home for redundant-sensor disagreement, conflicting requirement sets, and merge-time fact collisions that must route to **DEGRADE** rather than vanish.

**PROV — Claim Provenance & Groundedness (secondary).** FDE's fourth value, `Neither`, is precisely "no evidence spoke" — a typed marker for an *ungrounded* assertion, distinct from "asserted false." The bilattice's information ordering tracks how much evidence backs a claim. This buys a *medium* guarantee: it distinguishes grounded / refuted / conflicting / floating, but it does not by itself replay the evidence chain (that is RECORD/REVISE work) — it gives the value lattice those states need.

**CLASS — Honest Sharp Classification (secondary).** The taxonomy's own requirement — "or explicitly to *unknown*" — is a many-valued demand. K3's gap and FDE's `Neither`/`Both` supply the extra cells so a novel presentation lands in *unknown/conflicted* and surfaces loudly, instead of being forced into the nearest-wrong bucket. *Medium* guarantee.

**CALIB — Calibrated Claims (fuzzy, qualified).** t-norm logics give graded, *compositional* truth — useful for "guarantee strength matched to a quantity's kind" when the quantity is genuinely vague. The guarantee is *conditional* and carries a sharp **kill-condition** (below).

**Does NOT serve:** **INV, PROG, TRIG, DEGRADE, AUTH, ATTR, COMMIT, RECORD** as *primary* — temporal "always/eventually," deontic detachment, agency, ordering, and commitment lifecycles are the province of temporal/deontic/STIT/linear logics. Many-valued logic supplies the *value space* those logics quantify over; it is not the modality. Do not use fuzzy truth where an exact INV invariant is required — relaxing a logic invariant to a degree is itself a CALIB failure.

## A worked encoding

FDE four-valued conflict containment for the dam (CONSIST → routed to DEGRADE), encoded in **Z3 / SMT-LIB** by the standard *two-bit* trick: each atom carries `_t` ("told true") and `_f` ("told false"); the four assignments are T(1,0), F(0,1), Both(1,1), Neither(0,0). Verified runnable:

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
- **MULTLOG** (logic.at/multlog, v1.16a; academic/free) — a *prover generator*: input a finite truth-table specification, output a signed sequent/tableau calculus, including a published FDE/Belnap calculus. Use it to *generate and cross-check* the Z3 encoding (an INDEP second channel).
- **mNiBLoS** (CSIC; research code) — SMT-based solver for continuous t-norm logics (BL, Łukasiewicz, Gödel, product): 1-satisfiability, tautologicity, consequence. The reference if fuzzy reasoning becomes load-bearing.
- Sutcliffe et al., "Making Belnap's Useful Four-Valued Logic Useful" — maps FDE to classical ATP/TPTP, the same reduction strategy.

**Qualification (INDEP):** generate the n-valued truth tables programmatically, emit *both* a Z3 encoding and a MULTLOG calculus, and differential-test them against golden fixtures + mutation (flip a designated value; the contradiction-containment property must break). No LLM-judge in the loop — a mechanical gate.

## Honest leverage & kill-condition

**Load-bearing:** wherever conflicting-but-both-trustworthy inputs must *not* trigger ex falso and must route to a defined degraded mode — redundant sensors, merged records, contradictory requirement sets. Here the leverage is real and exact: non-triviality is provable and the encoding is tiny.

**Ash risk — fuzzy/CALIB.** t-norm conjunction is **truth-functional**; probability is not. Pushing graded fuzzy values through a long inference chain as if they were calibrated confidences yields numbers uncorrelated with evidence wearing a proof's costume.

**Falsifiable experiment + KILL CONDITION:** Build N glut/conflict fixtures with known correct degraded-mode verdicts. Run the FDE/Z3 encoding *and* a classical baseline. **KILL the FDE assignment for an obligation if** either (a) the classical baseline already contains every glut without vacuous passes on these fixtures (paraconsistency bought nothing there), or (b) for *fuzzy*, the propagated t-norm degree's ranking disagrees with a probabilistic/measured ground truth on >5% of fixtures — then fuzzy is not discharging CALIB and must be replaced by an explicit probabilistic channel.

## References (edification)

- **N. Belnap, "A Useful Four-Valued Logic" (1977)** — the founding intuition: why a multi-source database needs *Both* and *Neither*; reads directly onto sensor fusion.
- **G. Priest, *An Introduction to Non-Classical Logic* (2nd ed., 2008), ch. on LP/FDE** — cleanest primer on designated values and why explosion fails; the canonical teaching text.
- **P. Hájek, *Metamathematics of Fuzzy Logic* (2001)** — the rigorous foundation of t-norm logics; teaches exactly where graded truth is and isn't probability.
- **R. Hähnle, "Automated Deduction in Many-Valued Logics" (1993)** — the signed-formula reduction that makes the Z3/SMT encoding above mechanical and qualifiable.


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
