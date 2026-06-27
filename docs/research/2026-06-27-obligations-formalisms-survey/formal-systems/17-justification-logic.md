# 17 — Justification Logic / Logic of Proofs (Artemov) — proof-carrying belief

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

Justification Logic replaces the opaque modal "□F" ("F is known/provable") with an explicit witness term: `t:F`, read "`t` is a checkable justification for `F`." Belief stops being a bare bit in a store and becomes a structured, replayable object you can inspect, compose, and retract.

## Primer (becoming broadly expert)

The Logic of Proofs **LP** (Artemov, 1995) arose to solve a 60-year-old problem: give Gödel's provability reading of S4 an *arithmetically sound* semantics. Its move is to make justifications first-class terms. Formulas `t:F` say term `t` justifies `F`. Terms are built by three operations whose axioms are the whole theory: **application** `s·t` internalizes modus ponens (`s:(A→B) → (t:A → (s·t):B)` — combine a justification of an implication with a justification of its antecedent to get one for the consequent); **sum** `s+t` pools evidence monotonically (anything `s` or `t` justifies, `s+t` justifies); and **proof-checker** `!t`, giving `t:F → !t:(t:F)` (evidence that the evidence checks — positive introspection made explicit). Axioms enter only through a *constant specification* `c:A`, binding named constants to admitted axioms — your audited root warrants.

Two load-bearing results: the **Internalization Theorem** (every theorem `F` has a *ground* term `t` with `⊢ t:F` — provability always yields an explicit, constructible witness) and Artemov's **Realization Theorem** (every S4 theorem's `□`s can be replaced by LP terms, and back). Canonical authors: Artemov; Fitting (possible-world/Fitting models, tableaux); Kuznets & Studer (complexity, uniform realization). It is built to discharge **provenance**: not "is F true?" but "*what grounds F, and does that ground check?*"

## Obligations it discharges

**PROV — Claim Provenance & Groundedness (primary, exact fit).** PROV's failure mode is the ungrounded-but-true assertion and the confabulated-but-plausible chain. JL is the direct anti-pattern: a claim is not admissible as `F` alone but as `t:F`, where `t` *is* the finite, inspectable derivation down to constant-specification roots (signed inputs, cited authorities, admitted axioms). The application operator forces every detachment step to carry a sub-witness; you cannot assert `dose_reduce` without exhibiting the term that built it from a measurement and a guideline. Guarantee strength: a **checkable certificate** — `t:F` is decidably verifiable against the store independent of how it was produced, so a confabulated chain fails checking rather than passing inspection.

**RECORD — Auditable Decision Record (strong).** The witness term is exactly the "independently reconstructable rationale": replay `t` and you re-derive `F` or you don't. `!t:(t:F)` records *that the check was performed*, a tamper-evident "criterion-before-result" artifact.

**CALIB — Substantiated Claims (strong on the "proof costume" failure).** CALIB's lethal case is a claim "wearing a proof's costume but never discharged by an independent oracle." JL makes the costume *be* the proof: there is no `t:F` without a `t` that mechanically composes, so a bound that was never actually established has no constructible term.

**INDEP / ATTR (partial).** Sum lets you demand *distinct* terms from distinct channels (`s+t` where `s`, `t` trace to non-common-cause sources), and constants can name the *agent* who admitted an axiom, giving "who saw to it."

**Not its job:** temporal "always/eventually" (INV/PROG — JL has no time), deontic detachment and contrary-to-duty (TRIG/DEGRADE — JL justifies truth, not obligation), consistency containment (CONSIST), classification (CLASS), structural typing (STRUCT). Assign those elsewhere; JL owns the *evidence-for-a-claim* axis.

## A worked encoding

PROV obligation: an oncology recommender may emit `dose_reduce40` only carrying a witness resolving to a primary creatinine/eGFR value (the autoharn failure: a 40% reduction "for renal impairment" inherited from a superseded encounter with no supporting value). LP proof-checking is Horn-shaped, so SWI-Prolog hosts it directly:

```prolog
% justifies(Term, Claim) — an LP proof-checker over the current evidence store.

% Constant specification: audited roots (signed guideline, primary measurement).
justifies(cs(guideline_g7), impl(renal_impaired, dose_reduce40)).
justifies(meas(egfr_28, enc_4471), renal_impaired).   % this encounter only

% Application: internalized modus ponens  s:(A->B), t:A  =>  (s·t):B
justifies(app(S,T), B) :- justifies(S, impl(A,B)), justifies(T, A).

% Sum: monotone evidence pooling (independent corroboration).
justifies(plus(S,_), A) :- justifies(S, A).
justifies(plus(_,T), A) :- justifies(T, A).

% Proof-checker !t : (t:F)
justifies(check(T), just(T,F)) :- justifies(T, F).
```

```
?- justifies(W, dose_reduce40).
W = app(cs(guideline_g7), meas(egfr_28, enc_4471)).   % the replayable witness
```

The claim ships *with* `W`. Now exercise the failure modes. Retract the measurement (superseded encounter): `?- justifies(_, dose_reduce40)` fails — the claim loses its witness the instant its ground does (this is the REVISE hook: no term, no conclusion). Try to forge a citation — assert the *string* `app(cs(guideline_g7), meas(egfr_28, enc_9999))` where `enc_9999` is not in the store: re-checking `justifies(app(...),dose_reduce40)` fails because the sub-term `meas(egfr_28,enc_9999)` has no justification. The term cannot lie; checking is the gate. A golden/mutation fixture set (drop each leaf; perturb each constant) qualifies the checker itself (INDEP).

## Automation & tooling (the git-clone-runnable question)

**Dedicated solver: none production-grade.** Web-verification confirms only academic prototypes and paper calculi — prefixed/analytic tableaux for JL (Goetschi & Kuznets; Finger), labeled sequent calculi with countermodel construction (Lurie/Studer), realization-algorithm prototypes (Brünnler–Goetschi–Kuznets) — none packaged with a license/version on a registry, none maintained as a tool. So the deliverable is an **encoding**, and it is cheap because LP's deductive core *is* Horn.

**Host: SWI-Prolog (9.3.31, local), optionally Datalog/ASP for the EDB.** The proof-checker above is the whole engine for ground LP — `justifies/2` is a definite-clause meta-interpreter over the term algebra; checking a supplied witness is linear-bottomed SLD resolution and decidable. Three extensions cover the rest: (a) the constant specification becomes the audited fact table (Postgres-backed for the real store); (b) **proof search** (synthesizing `t` rather than checking it) is bounded iterative-deepening over `app/+/!`, or delegated to clingo with the operations as choice rules and a term-size bound to keep it finite; (c) for the *realization* path — compiling a modal "□F = verified(F)" spec (TLA+/S4-style) into explicit witnesses — implement Fitting-realization as a pass over a cut-free modal proof, replacing each `□` with a fresh variable then solving the term-unification constraints (CHR in SWI handles the constraint propagation). Z3 is overkill for the core but useful when constants carry numeric side-conditions (the eGFR threshold) — emit `t:F` with an SMT obligation on the leaf. Nothing here needs an install beyond the locally-present SWI-Prolog.

## Honest leverage & kill-condition

**Load-bearing where evidence is a first-class object you branch over and retract:** multi-source corroboration (`s+t` with distinct provenance), nested verification (`!t` — "the auditor checked the producer's proof"), and witness survival under retraction. Here JL gives something a flat boolean store cannot: a claim that is true *and unexplainable* is unrepresentable.

**Where it is ash:** for plain flat provenance, ordinary Datalog **why-provenance** (the SLD proof tree, or semiring provenance) already yields a checkable, replayable derivation chain — the `app/cs` term above *is* essentially that proof tree. The `+`/`·`/`!` algebra and constant-specification discipline add nothing a provenance-annotated Datalog engine lacks.

**Falsifiable experiment / KILL CONDITION:** Take autoharn's real PROV corpus. Implement each claim's provenance twice — (i) the JL checker above, (ii) Datalog why-provenance (e.g., recursive Postgres or clingo with proof extraction). **JL is killed for autoharn if every PROV/RECORD/CALIB case is discharged by (ii) with equal forgery-resistance and equal retraction behavior, and no case requires reasoning *about* justification terms inside the logic** (evidence-of-evidence, justification quantification, or `+`-corroboration that Datalog cannot express). Survival requires exhibiting ≥1 production case where first-class, composable, introspectable witnesses are *necessary* — e.g., an INDEP cross-channel rule that must assert "two *distinct, separately-checking* justifications exist" as an object-level fact. Absent that case, assign PROV to Datalog provenance and retire JL to the realization-compiler role.

## References (edification)

- **Artemov & Fitting, *Justification Logic* (Stanford Encyclopedia of Philosophy; expanded Cambridge UP, 2019).** The canonical primer — terms, operations, Fitting models, internalization, realization; start here.
- **Artemov, "The Logic of Justification," *Review of Symbolic Logic* 1(4), 2008.** The motivating manifesto: why explicit witnesses solve the provability/knowledge gap.
- **Fitting, "The Logic of Proofs, Semantically," *APAL* 132 (2005).** Possible-world semantics and the tableau basis any prover encoding builds on.
- **Kuznets & Studer, *Logics of Proofs and Justifications* (College Publications, 2019).** Comprehensive reference for complexity, decidability, and uniform realization — the engineering substrate for an automation plan.


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
