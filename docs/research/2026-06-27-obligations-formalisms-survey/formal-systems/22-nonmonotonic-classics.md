# 22 — Default Logic, Circumscription & Autoepistemic Logic

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

Three formalisms for **nonmonotonic** reasoning — concluding by default and *retracting* when the world objects. They are the native logic of "permitted unless forbidden," "normal unless flagged abnormal," and "duty detaches unless an exception is known." For autoharn they discharge the *closure* and *defeasible-detachment* obligations: what is true of the **unmentioned**, and how a conclusion dies when its ground is withdrawn.

## Primer (becoming broadly expert)

Classical logic is monotone: adding premises never destroys a theorem. Real governance is not — "the agent may act" survives only until an override appears. Three answers, all c. 1980:

- **Default Logic (Reiter, 1980).** Inference rules with *justifications*: `α : β / γ` reads "if α holds and β is consistent to assume, conclude γ." A **normal default** `α : γ / γ` is "α normally gives γ." Fixed points are **extensions** — maximal coherent belief sets. Theorem (Reiter): every default theory's extensions are exactly the groundedly-supported closures; normal theories always have one.
- **Circumscription (McCarthy, 1980).** A *second-order* sentence minimizing the extension of an **abnormality predicate** `Ab`: among models, prefer those where as little as possible is abnormal. This is closed-world-assumption done semantically — "nothing is exceptional unless forced."
- **Autoepistemic Logic (Moore, 1985).** A modal operator **L** ("I believe"); **stable expansions** model an agent introspecting its *own* belief set. Konolige's translation ties it to default logic.

The crisp invariant all three share — and the one that matters most for audit — is **groundedness**: a conclusion must be *supported*, never self-justifying. This is exactly the failure these logics are built to prevent.

## Obligations it discharges

- **AUTH — Action Authorization, Permission Closure & Norm Precedence** (primary). The *closure rule for the unmentioned* is literally circumscription: minimize `permitted`, and an act unnamed by any grant is forbidden — closed-world by construction, killing "permitted because no rule named it." Norm precedence (durable standing norm vs transient override) is **prioritized defaults**: the override is a higher-priority default that derogates the standing one *only while its justification holds*, so a bypass that outlives its window silently reverts to forbidden. **Guarantee strength:** for a finite, stratified rule base, the answer set is *unique and decidable* — the permission verdict is a total function of the logged state, mechanically recomputable.

- **TRIG — Conditional Activation** (primary). A triggered duty is a normal default `trigger : duty / duty` whose justification encodes "no defeater known." Degraded sensing is modeled as the justification failing *open* (duty still detaches under uncertainty) rather than failing silent. This is the deontic-detachment locus done as defeasible detachment. **Strength:** skeptical (in-every-extension) entailment gives a conservative "fire unless proven safe to suppress."

- **CLASS — Honest Sharp Classification** (primary). Default classification into a closed vocabulary with an explicit **`Ab`** escape: minimize abnormality, and any entity not minimally classifiable lands in a *loud* `unknown` rather than the nearest-wrong bucket. Order-dependent dispatch is exposed as **multiple extensions** — if two rules both match, the theory yields two stable models, and a non-unique answer set is the alarm.

- **REVISE — Belief Revision & Retraction Propagation** (strong secondary). Nonmonotonicity *is* retraction propagation: withdraw a premise and every default that leaned on it loses its justification; recomputation withdraws the dependent conclusions automatically. This is the classical Reiter-default ↔ justification-based truth-maintenance correspondence — the "spillway safe" verdict cannot outlive the reading it stood on.

- **PROV — Claim Provenance & Groundedness** (secondary). Stable-model semantics *requires* well-founded support: no fact floats without a grounded derivation, and self-supporting loops are excluded by definition — directly the failure mode (an assertion true in the store but unexplainable).

**Does NOT serve:** **PROG** (no time/deadlines — needs temporal logic), **INV** over execution traces (needs model checking), **CALIB** (no numeric confidence), **COMMIT** (no directed-obligation lifecycle). And — importantly — it does **not** discharge **CONSIST**: nonmonotonic ≠ paraconsistent. A flatly contradictory default theory has *no* extension (or detonates classically inside an extension); contradiction *containment* belongs to paraconsistent logic, not here. Use defaults for *exceptions*, not for *conflict quarantine*.

## A worked encoding

AUTH for the dam spillway: the optimizer agent may always *propose* but may *deploy* only inside a logged, time-boxed override window; anything unnamed is blocked (closed-world). Real clingo, run locally (clingo 5.8.0):

```prolog
agent(optimizer). agent(operator).
action(propose_change). action(deploy_spillway).

permitted(A, propose_change) :- agent(A).        % durable standing grant

{ window_open }.                                  % is the maintenance window open?
authorized_by(operator).                          % logged authorizer
granted(optimizer, deploy_spillway) :- window_open, authorized_by(operator).

% DEFAULT (closed-world): deploy forbidden unless an in-window grant exists
forbidden(A, deploy_spillway) :- agent(A), not granted(A, deploy_spillway).
permitted(A, deploy_spillway) :- granted(A, deploy_spillway), not forbidden(A, deploy_spillway).

% Permission closure: no positive permission ⇒ BLOCKED (no authority leakage)
blocked(A, Act) :- agent(A), action(Act), not permitted(A, Act).
#show permitted/2. #show blocked/2.
```

Verified output — two stable models: window **closed** ⇒ `blocked(optimizer,deploy_spillway)`; window **open** ⇒ `permitted(optimizer,deploy_spillway)`. The operator is *never* granted deploy (no rule), so the closure blocks it in **both** worlds — the unmentioned act is denied, not leaked. Drop `window_open` and the permission evaporates: the bypass cannot outlive its window.

## Automation & tooling (the git-clone-runnable question)

**Default & autoepistemic logic: solved, via a dedicated mature host.** Their fixed-point/stable-expansion semantics is the **stable-model (answer-set) semantics**; normal default theories translate directly into normal logic programs (Gelfond–Lifschitz; Marek–Truszczyński), and autoepistemic stable expansions correspond to answer sets. The runnable engine is **clingo** (Potassco; **MIT license**; **v5.8.0**, the build present on this machine; highly mature, ICLP-grade, actively maintained). The git-clone deliverable ships these as `.lp` files — no extension needed.

**Circumscription: no everyday solver, but a concrete, published encoding path.** Two routes, both open-source:
1. **`circ2dlp`** (GPL) compiles a circumscriptive theory into a **disjunctive** logic program whose stable models are exactly the R-minimal models — then run clingo (which subsumes the old `dlv`/`gringo+clasp` pipeline). This is the standard route and is git-clone-runnable on the installed stack.
2. **Native in clingo** for the common case: minimize an `Ab` predicate with `#minimize { 1,X : ab(X) }` plus the optimality-by-inclusion idiom, or hand-roll the metasp "subset-minimal model" saturation encoding. For parity-minimal-model SAT, **Z3 4.16** (`(minimize ...)` / Pareto, present locally) handles the propositional fragment.

So: defaults/autoepistemic = clingo directly; circumscription = `circ2dlp`→clingo, or `Ab`-minimization in clingo/Z3. No shrug required.

**Qualification (INDEP).** The LLM-authored encoding is on trial: gate it with **golden fixtures** (the closed/open-window models above as a pinned oracle), **mutation tests** (delete the closure rule → an unnamed act must flip from `blocked` to leaked; flip a justification → retraction must propagate), and a **differential** `circ2dlp`-vs-`Ab`-minimization cross-check so the two routes must agree.

## Honest leverage & kill-condition

**Load-bearing** where the obligation is *what holds of the unmentioned* and *how a duty detaches and dies*: AUTH permission closure, TRIG detachment, CLASS default-with-`unknown`, REVISE retraction. Here the unique answer set is a decidable, replayable verdict — genuine industrial leverage.

**Ash** where stakes demand *temporal* or *conflict* guarantees: do not stretch defaults to cover INV-over-traces, PROG deadlines, or CONSIST. The seductive failure is encoding a true contradiction as a "default exception" and getting a vacuous or empty extension that *looks* like a clean answer.

**Falsifiable experiment / KILL CONDITION.** Take 50 real AUTH/CLASS policies with hand-labeled correct verdicts (including adversarial unmentioned acts and order-ambiguous classifications). Encode each; require clingo to (a) block every unnamed act, (b) emit *multiple* answer sets exactly when the policy is genuinely ambiguous, and (c) propagate every premise retraction. **Kill if** the encoded theory grants an unmentioned act, *or* silently returns one model where the policy is ambiguous (masking the conflict), in ≥1 case — that is the closed-world/groundedness guarantee failing, and the assignment is refuted for this obligation class.

## References (edification)

- **Reiter, "A Logic for Default Reasoning," *Artificial Intelligence* 13 (1980).** The source: defaults, justifications, extensions, and the existence theorem for normal theories.
- **Brewka, Niemelä & Truszczyński, "Nonmonotonic Reasoning" (Handbook of KR, 2008).** Best modern map tying default/circumscription/autoepistemic to answer-set semantics — the bridge to clingo.
- **Gebser, Kaminski, Kaufmann & Schaub, *Answer Set Solving in Practice* (2012) + Potassco clingo docs.** Teaches the runnable host: how defaults/closure become `.lp` and how minimization encodes circumscription.
- **Lifschitz, "Circumscription" (Handbook of Logic in AI, 1994).** The definitive treatment of `Ab`-minimization and closed-world reasoning, with the minimal-model semantics the tooling computes.

Sources: [circ2dlp / aspino model enumeration](https://arxiv.org/pdf/1707.01423), [ASP and default logic (Gelfond/Lifschitz, Reiter)](https://www.cs.utexas.edu/~vl/teaching/378/ASP.pdf), [minimal-reduct circumscription solving](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12727910/)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
