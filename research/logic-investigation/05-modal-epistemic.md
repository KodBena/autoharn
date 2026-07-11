# 05 — Modal & Epistemic Logic

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../GLOSSARY.md)**.

Modal logic adds operators that qualify *the mode* of a truth — "necessarily", "possibly", "is known", "is believed", "after this happens" — interpreted over Kripke frames (worlds + accessibility relations). Epistemic logic is the agent-indexed instance: `K_a φ` ("agent *a* knows φ") and `B_a φ` ("believes"), with the doxastic/temporal variants autoharn actually needs.

## Primer

You already think relationally: a Kripke model is just a graph of *possible worlds* plus, per agent, an accessibility relation `R_a` over them. `K_a φ` holds at world *w* iff φ holds in **every** world *a* considers possible from *w* — knowledge = truth-in-all-epistemic-alternatives. Two axioms carry all the weight for autoharn. **T (factivity):** `K_a φ → φ` — what is *known* is *true* (reflexive `R`). Knowledge can't be wrong. **D:** `B_a φ → ¬B_a ¬φ` — belief is merely *consistent*, not truthful (serial `R`). That single gap — factive `K` vs defeasible `B` — is the whole reason to reach for this logic instead of a status enum: it makes "confirmed" and "provisional" *different kinds of truth* with different inference rules, and lets a benchmark on a dirty tree be *believed* but never *known*. Use it whenever your real subject is **who-is-entitled-to-assert-what, and when**, not the facts themselves.

## Applicability to autoharn

**Status lifecycle provisional/confirmed/retracted (high).** This is the canonical epistemic/doxastic split named in the cross-cutting shapes. Model `confirmed = K` (factive), `provisional = B` (defeasible), `retracted = ¬B`. The payoff over a plain SQL `status` column: factivity becomes an *enforced inference rule*, not a comment. A meta-interpreter in the **installed SWI-Prolog 9.3.31**:

```prolog
% T-axiom: knowledge is factive; belief is not.
knows(A,P)    :- confirmed(A,P), holds(P).      % K_a P -> P
believes(A,P) :- provisional(A,P).              % B_a P, defeasible
:- knows(_,P), \+ holds(P).                     % violation gate: "known" yet false
```

That last line is a `*_violations` gate (Pillar 3) expressed as a modal integrity constraint — it beats SQL because SQL has no notion that `confirmed` *entails* the fact.

**A benchmark on a DIRTY tree must not be promoted to "confirmed" (high).** Factivity gives the exact missing rule: promotion to `K` requires the supporting reading to be true *in every accessible world*, and a dirty tree introduces a world where the number differs. Encode the bridge:

```prolog
confirmable(Claim) :- reading(Claim, _N, clean_tree).
confirmable(Claim) :- reading(Claim, _N, dirty), fail.  % dirty -> only B, never K
```

This is the doxastic stop-gap autoharn wants mechanized rather than re-explained.

**Pre-registration: criterion committed BEFORE the result (high).** This is *temporal*-epistemic — the right engine is a temporal-epistemic model checker (MCMAS/CTLK). The property "no result is judged unless its criterion was already known" is one formula:

```
AG (result_emitted -> Y K_engine criterion_registered)   -- "Yesterday, knew the criterion"
```

A Python script can *check* timestamps; only the modal formula *states the invariant* declaratively so CI can refute it. Strength high because temporality + knowledge is exactly modal logic's home turf and SQL cannot express "in all futures".

**"A reading-of recorded as the data" is unrepresentable (med).** This is the de re/de dicto scope distinction. Epistemic logic keeps `K_a(value=12x)` (a belief *about* a measurement) type-distinct from `value=12x` (the measurement). Modeling reading and interpretation as different modal depths formalizes Pillar 2's "measurement separate from interpretation". Med, not high: a disciplined two-table schema also achieves separation; modal logic mainly adds the *inference hygiene* that you can't collapse `K_a φ` to `φ`.

**Conflicting advisories coexist; the DIRTY/suspect third value (med).** Standard epistemic logic is *not* paraconsistent — `K_a φ ∧ K_a ¬φ` explodes. The honest move is doxastic + a 3rd value: two agents may `B`-disagree without contradiction, and `suspect` = `¬K_a φ ∧ ¬K_a ¬φ` (ignorance is first-class). This serves the paraconsistency shape only when paired with belief, not knowledge — a forced fit if you demand it from `K` alone.

**Liveness as a refreshable fact (low).** Belief revision (AGM/dynamic epistemic logic, "public announcement" `[!φ]`) models a REFUTED resource belief being superseded. Real but low-leverage: autoharn's supersedes-chain is already an append-only ledger; DEL is heavier machinery than the need warrants.

**Where it's forced:** Rule-4 class-keyed nets and the capability *classification* (lib xor solver…) are plain typed constraints — not modal. Don't reach here for those.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **SWI-Prolog 9.3.31** | meta-interpreter for K/B axioms as Horn rules + violation gates | BSD-2 | Prolog; C/Python (`janus`) | **already installed** (`/usr/bin/swipl`) | very mature | high — readable clauses, but *you* hand-code the frame |
| **MCMAS 1.3.0** | temporal-epistemic (CTLK: `K`, `GK`, common/distributed knowledge) model checker; ISPL input | open-source (academic) | C++/OBDD; CLI | compile-from-source; **1.3.0 needs an old `bison`** — fiddly | mature, niche | med — ISPL is unusual; LLM training data thin |
| **nuXmv 2.1.0** (Nov 2024) | symbolic CTL/LTL temporal checker (pre-registration "before") | binary-only, **non-commercial** | C/CLI | apt-free binary download | mature | med — SMV widely documented |
| **NuSMV 2.7.1** | OSS CTL/LTL alternative to nuXmv | LGPL | C/CLI | compile or binary | mature | med |
| **SMCDEL** | symbolic *dynamic* epistemic logic (belief revision, announcements) via BDDs | GPL-2 | Haskell; CLI/web | compile (needs GHC/Stack) — heavy | research-grade | low — Haskell + DEL niche |

For autoharn today, **SWI-Prolog covers the high-value doxastic gates with zero install**; add **MCMAS or nuXmv** only when the *temporal* pre-registration invariant must be machine-checked.

## Limits & honest take

The headline risk is **false authority by mis-modeled frame**. A modal "proof" is only as sound as the accessibility relation an LLM wrote: forget reflexivity and `K` silently stops being factive; pick `S5` and you've assumed agents have *perfect introspection* they don't. The formula will still "verify" — confidently wrong, exactly the failure Pillar 2 fears. Mitigation: treat every generated frame as `provisional` and pin the axioms (T, D, 4, 5) explicitly with a one-line comment, never inferred. Second, classic epistemic logic suffers **logical omniscience** (`K_a φ` and `φ→ψ` forces `K_a ψ`) — autoharn's AI does *not* know all consequences of what it stores, so don't read `K` as "has surfaced". Third, much of autoharn (classification, class-keyed nets, SQL ledgers) is *not* modal; forcing it through Kripke frames is pure overhead. Use modal logic only where the subject is **knowledge-status and temporal commitment** — there it is uniquely right; everywhere else it is hype.

## References & learning

- **Fagin, Halpern, Moses, Vardi — *Reasoning About Knowledge* (MIT Press).** The standard text; teaches `K`, common/distributed knowledge, and the omniscience pitfall directly relevant to "what the AI knows vs stored".
- **van Ditmarsch, van der Hoek, Kooi — *Dynamic Epistemic Logic* (Springer).** Teaches public-announcement/belief-revision — the model for "REFUTED belief superseded".
- **MCMAS docs & ISPL tutorial** ([doc.ic.ac.uk/~alessio](https://www.doc.ic.ac.uk/~alessio/papers/06/tacas.pdf)). Teaches encoding agents + CTLK properties you'd run for pre-registration.
- **Gattinger, *New Directions in Model Checking DEL* / SMCDEL** ([malv.in/phdthesis](https://malv.in/phdthesis/), [github.com/jrclogic/SMCDEL](https://github.com/jrclogic/SMCDEL)). Teaches BDD-symbolic epistemic checking — how the theory becomes a fast tool.

Sources: [MCMAS](https://github.com/mattvonrocketstein/mcmas), [nuXmv](https://nuxmv.fbk.eu/), [NuSMV 2.7.0](https://nusmv.fbk.eu/articles/270/), [SMCDEL](https://github.com/jrclogic/SMCDEL)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
