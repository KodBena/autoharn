# 23 — Defeasible Logic & Formal Argumentation (Dung AF, ASPIC+, DeLP)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [STRUCT](../KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

A discipline for reasoning that stays *useful in the presence of conflict*: claims are supported by defeasible arguments that attack and defend one another, and a semantics decides which survive — turning a contradiction from a catastrophe (ex falso) into a localized, inspectable adjudication.

## Primer (becoming broadly expert)

The pivot is Dung's 1995 *abstract argumentation framework* (AF): a directed graph `(Args, attacks)` whose nodes are arguments and whose edges are defeats. **Semantics** (Dung) select *extensions* — sets of arguments that are conflict-free and *admissible* (each defended against all attackers): the **grounded** extension is the unique, skeptical, least-committed verdict (everything you are forced to accept); **preferred/stable** are credulous alternatives. The deep result is that a conflicting knowledge base no longer explodes — acceptance is a fixpoint over the attack graph, not classical entailment. **ASPIC+** (Prakken, Modgil) and **DeLP** (García & Simari) put *structure* back in: arguments are built from strict and **defeasible rules** over a knowledge base; attacks are rebut (conflicting conclusions), undercut (attacking a rule's applicability), and undermine (attacking a premise); a **preference ordering** turns attacks into *defeats*, so priority between norms/sources is first-class. Rationality postulates (Caminada–Amgoud: closure, consistency) are theorems, not hopes. The intuition: this machinery exists to answer "given mutually inconsistent inputs and superseding evidence, *what may I still rationally hold, and exactly why* — without quarantining into either silence or arbitrary choice." It is built for **[CONSIST](../KEY.md#consist)**, **[REVISE](../KEY.md#revise)**, and **[PROV](../KEY.md#prov)**.

## Obligations it discharges

- **[CONSIST](../KEY.md#consist) — Consistency & Contradiction Containment (primary).** This is the home obligation. Conflicting inputs become mutually-attacking arguments; the grounded semantics refuses to accept either side of an undecided clash (labels it UNDEC) instead of deriving everything or laundering a consensus. The failure mode — classical ex falso making *all gates pass vacuously* — is structurally impossible: acceptance is non-explosive by construction. **Guarantee strength:** a proof that the contradiction is *isolated to its attack component* and that no unrelated claim inherits acceptance from it; the redundant-altimeter case yields a quarantined UNDEC, forcing degraded mode rather than vacuous clearance.

- **[REVISE](../KEY.md#revise) — Belief Revision & Retraction Propagation (primary).** Defeasibility *is* non-monotonicity: add an argument that the piezometer was recalibrated, and every conclusion resting on the old reading loses its defense and flips to OUT automatically — no forward reasoning from a knocked-out premise. Append-only fits natively: you add attackers, you don't overwrite. **Guarantee strength:** mechanical re-adjudication of the whole dependent sub-graph on every premise change; the *justification status* of each claim is recomputed, so a stale "spillway safe" cannot survive its own evidence.

- **[PROV](../KEY.md#prov) — Claim Provenance & Groundedness (primary).** An ASPIC+/DeLP argument *is* a finite chain from conclusion to premises/axioms; "accepted" means "has a surviving dialectical chain to admitted grounds." A confabulated chain is one whose links can be undercut. **Guarantee strength:** every accepted claim carries its replayable support tree and the set of attacks it defeats.

- **[AUTH](../KEY.md#auth) — Norm Precedence (secondary).** Preference orderings over rules give *deterministic derogation*: a standing safety norm outranks a transient override via an explicit, logged priority; defeat (not mere attack) resolves which norm is active. Strength: deterministic resolution *given* a stated order — it does not invent the order.

- **[RECORD](../KEY.md#record) (secondary):** the argument graph is itself the reconstructable rationale.

**Does NOT serve:** **[INV](../KEY.md#inv)/PROG** (no temporal "always"/deadline operators — use temporal logic / model checking), **[STRUCT](../KEY.md#struct)/COHERE/CALIB** (type-level and numeric-tolerance guarantees are out of scope), and **[TRIG](../KEY.md#trig)/COMMIT** lifecycle timing (deontic detachment can be *modeled* as defeasible rules but the temporal duty-window belongs elsewhere). Assign those obligations to their matched formalisms.

## A worked encoding

Obligation **[PROV](../KEY.md#prov)+[REVISE](../KEY.md#revise)**: the dam "spillway-safe" verdict must not outlive the evidence it rests on. Grounded extension in clingo (ASP):

```prolog
% args: s=spillway-safe, r=piezometer recalibrated => old reading void, c=cal cert valid
arg(s). arg(r). arg(c).
attacks(r,s).        % recalibration undercuts the safe verdict's premise
attacks(c,r).        % a valid prior cal-cert would defeat the recalibration claim
% --- grounded (well-founded) labelling ---
defeated(X) :- attacks(Y,X), accepted(Y).
accepted(X) :- arg(X), defeated(Y) : attacks(Y,X).   % in iff every attacker is out
#show accepted/1. #show defeated/1.
```

`clingo spillway.lp` ⇒ `accepted(c) accepted(s) defeated(r)`: the cert defends safety. Now add the kill fact — the cert was for a *superseded* encounter, so retract `c`:

```prolog
% comment out arg(c)/attacks(c,r), or add: attacks(x,c). arg(x).
```

⇒ `accepted(r) defeated(s)`: the safe verdict is automatically withdrawn. No state was overwritten; an attacker was added and the dependent verdict re-adjudicated. (For graphs with odd/even attack cycles the two-rule encoding's well-founded model *is* the grounded extension; credulous preferred/stable need the standard guess-and-check ASP encoding.)

## Automation & tooling (the git-clone-runnable question — MANDATORY)

**Dedicated tools exist and are mature — no encoding-from-scratch needed.**

- **µ-toksia** — state-of-the-art SAT-based abstract-AF reasoner (grounded/preferred/stable/complete, credulous & skeptical, ICCMA-winning). **License: MIT.** Best choice for *fast verdicts at scale* on the abstract AF you compile your arguments down to. (WEB-VERIFIED: ICCMA 2019/2023 participant; SAT-backed.)
- **PyArg** (DaphneOdekerken/PyArg, open-source Python) — supports **abstract AF, ASPIC+, and ABA**, with *explanation* generation. Ideal for autoharn because it produces the human-auditable "why accepted/rejected" trace, not just a yes/no.
- **py-aspic** (arg-tech) — focused ASPIC+ argumentation-theory builder (knowledge base + strict/defeasible rules + preferences). Good for the *structured* layer before flattening to an AF.
- **DeLP / Tweety** — the Tweety libraries (Java, **LGPL**) implement DeLP and many AF semantics; DeLP's `delp` engine gives dialectical-tree query answering directly.

**Recommended autoharn pipeline (all git-clone-runnable here):** author obligations as ASPIC+ rules in **py-aspic/PyArg** → flatten to an abstract AF → discharge acceptance with **clingo** (encoding above, already verified locally: clingo 5.8.0, swipl 9.3.31, z3 4.16 present) for the in-repo path, and cross-check with **µ-toksia** as an *independent channel* (**[INDEP](../KEY.md#indep)**: SAT-based vs ASP-based, no common solver). s(CASP) (SWI-Prolog packable) gives goal-directed, *self-justifying* defeasible answers when you want a Prolog-native trace. The clingo two-rule encoding above is the minimal qualifiable core; differential agreement clingo-vs-µ-toksia on golden AFs is the qualification gate.

## Honest leverage & kill-condition (life-critical seriousness)

**Load-bearing** wherever autoharn must hold conflicting evidence and re-adjudicate on retraction — the contradictory-sensor, superseded-encounter, and norm-override cases ([CONSIST](../KEY.md#consist)/REVISE/PROV/AUTH). The win is real: non-explosive verdicts + automatic withdrawal + a replayable support tree, with two independent solvers.

**Where it is ash:** it guarantees nothing temporal or numeric, and — critically — **garbage-in:** the verdict is only as sound as the hand-authored attack/preference graph. An LLM that *mis-encodes* an attack (omits an undercut, mis-orders a preference) yields a confidently-grounded *wrong* verdict that looks fully justified. The argument graph is exactly the artifact **[INDEP](../KEY.md#indep)** says cannot be trusted to its own author.

**Falsifiable experiment + KILL CONDITION.** Build a mutation suite: take N golden obligation→AF encodings with known correct extensions; have the LLM author the AFs; (a) require clingo and µ-toksia to agree (catches *solver* error), and (b) inject K seeded encoding mutations (dropped undercut, flipped preference, missing premise link) and measure detection by a *differential* check against the spec-derived expected extension. **KILL:** if seeded encoding-mutations survive (expected-vs-actual extension agree despite the mutation) at a rate above the residual-risk budget — i.e., the formalism cannot catch its own mis-encoding even with dual solvers — then argumentation is *not* discharging the obligation at life-critical strength and must be demoted to a non-load-bearing advisory layer behind an independently-authored oracle. Solver agreement alone does **not** clear this bar; only mutation-detection on the *encoding* does.

## References (edification)

- Dung (1995), *On the Acceptability of Arguments…*, AIJ 77 — teaches the abstract AF and the four semantics; the foundation everything else flattens to.
- Modgil & Prakken (2014), *The ASPIC+ framework for structured argumentation: a tutorial*, Argument & Computation — teaches how to build arguments from defeasible rules and turn attacks into defeats via preferences (the norm-precedence machinery).
- García & Simari (2004), *Defeasible Logic Programming*, TPLP — teaches a Prolog-native, query-driven dialectical-tree engine (the DeLP you can run today).
- Caminada & Amgoud (2007), *On the evaluation of argumentation formalisms*, AIJ — teaches the rationality postulates (closure/consistency) that separate a sound encoding from a plausible-looking broken one — directly your kill-condition's theory.

Sources: [µ-toksia (ICCMA)](https://iccma2023.github.io/solvers.html), [PyArg](https://daphneodekerken.github.io/PyArg/), [py-aspic](https://github.com/arg-tech/py-aspic)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
