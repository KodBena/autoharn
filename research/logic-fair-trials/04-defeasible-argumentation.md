# 04 — Defeasible / Non-monotonic Reasoning & Formal Argumentation — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 0 defect(s) noted · **not rewritten** (the hardening pass was a no-op).

## Defeasible / Non-monotonic Reasoning & Formal Argumentation — Fair Trial
The bet on trial: that **retraction-under-new-evidence** — a conclusion that silently withdraws when a refuting fact arrives, with conflicts resolved by priority instead of detonating — is a *primitive* autoharn needs at the gate, and that an LLM authoring the rules + a justification trail makes it load-bearing rather than abandonware.

## Maximal ambition
The frontier claim: autoharn's three stores stop being passive tables and become a **self-revising belief base whose every live verdict carries a machine-checkable derivation and an explicit defeater**. The most ambitious thing this logic proves that the familiar tools cannot: a CI gate that is *correct in the presence of unresolved contradiction*. Two findings assert `pass` and `fail` about the same invariant; Z3 returns `unsat` and the gate is meaningless; a SQL view returns whichever row the `ORDER BY` happened to pick. Defeasible reasoning instead keeps a *usable* verdict (the confirmed one defeats the provisional one), retains both rows, and emits a third value `suspect(F)` — "uncorroborated conflict" — as first-class data that a `*_violations` gate keys on by **class** (Rule 4), not by enumerating instances. Pushed maximally: the Capability Registry becomes a default theory where `usable(C)` holds *until refuted*, supersession chains compute "what holds now" by deduction while never rewriting priors, and — via `s(CASP)` — each surviving conclusion ships a **justification tree** answering "*why* does `usable(z3)` hold, and exactly which future reading would kill it." That is deductive maintenance in the literal sense: the maintainer edits beliefs, and the consequences (which caps drop, which ADR wins, which gate flips) re-derive themselves, each with a proof.

## The expressiveness gap (precise, not hand-wavy)
The gap is **semantic**, not merely ergonomic. SQL/Datalog are monotone: adding a row never *removes* a previously-derivable answer. autoharn's core relations are non-monotone — `usable(C)` must *vanish* when `liveness(C,dead,_)` arrives. You can fake this in SQL with `NOT EXISTS` correlated subqueries, but every additional defeater (refuted OR superseded OR conflicted) compounds the negation nesting, and the *stratification* that guarantees a well-defined answer becomes the engineer's manual burden — exactly the property ASP's stratified semantics gives you for free and *checks*. The decisive, provable gap is **defeat under contradiction**: classical/SQL semantics cannot represent "P and ¬P coexist, yield a usable answer, and flag the pair" without ad-hoc tri-state columns the author must hand-maintain everywhere. ASP's answer-set semantics (and Dung/ASPIC+ above it) give this a *named, studied* meaning (skeptical vs credulous, grounded extension) with a kill-defeater that is part of the model, not bolted on. Honest boundary: for *hard* mutual-exclusion (Pillar 1 `lib xor solver`) and feasibility, this logic is the wrong tool — that is crisp SAT/SMT. The gap is real only where **belief is provisional**; there it is genuine and SQL cannot close it cheaply.

## The falsifiable experiment (the trial)
**Setup.** Export the live Capability Registry + supersession + findings stores to clingo facts (already installed, 5.8.0). Encode the Safety Net (verified runnable today):

```prolog
usable(C) :- declared(C), not refuted(C).
refuted(C) :- liveness(C,dead,_).
holds(D,V) :- decision(D,V,T), not overridden(D,T).
overridden(D,T) :- decision(D,_,T), decision(D,_,T2), T2 > T.
verdict(F,P) :- finding(F,P,confirmed).
verdict(F,P) :- finding(F,P,provisional), not finding(F,_,confirmed).
suspect(F) :- finding(F,P,_), finding(F,Q,_), P!=Q.
:- usable(C), not liveness(C,_,_).   % meta-sweep: every cap declares its enforcement surface
```

Running this on seeded data yields exactly `usable(z3) usable(ortools)` (cvxpy dead → dropped), `holds(adr7,"y")` (T=3 defeats T=1), `verdict(f1,pass)` + `suspect(f1)` — confirmed and reproduced (`clingo`, 0.001s).

**Success criterion:** on a 10k-fact dump of the real stores, clingo grounds+solves under 2s, and the derived `usable/holds/verdict/suspect` sets match the maintainer's hand-labeled oracle on ≥30 supersession/conflict cases, **including ≥5 cases SQL gets wrong or awkward** (multi-defeater retraction).

**KILL CONDITION (non-negotiable):** retire this logic if EITHER (a) grounding blows up — solve time superlinear past 5s on the 10k dump, making it CI-unviable — OR (b) for every case in the oracle, an equivalent stratified SQL `NOT EXISTS` view is hand-written in comparable LOC and is judged *as clear* by the maintainer (i.e. the semantic gap did not cash out in practice). Either outcome is a stated failed experiment, not a familiarity retreat.

## Neutralizing false authority (verification scaffolding)
The prior section's "an LLM writes `not refuted` where it meant `-refuted` and the green gate lies" is the **central research problem**, engineered here, not a reason to flee to SQL:

1. **Mutation fixtures (demonstrated).** Drop the `not refuted(C)` guard and the mutant resurrects `usable(cvxpy)` — a *dead* resource — which the golden rejects. The mutant test suite *requires* that each known mis-encoding (default→fact, classical-neg confusion, priority inversion `T2 > T`→`T2 < T`) produces a diff vs the golden answer set; a mutant that survives = the test suite, not the logic, is the defect.
2. **Differential semantics.** Run the same theory under clingo (answer-set) and `s(CASP)` (goal-directed, packable on the installed SWI 9.3.31); divergence flags grounding/semantic ambiguity (skeptical vs credulous) before it reaches CI.
3. **Justification-carrying output → back-translation.** `s(CASP)` emits the proof tree for each verdict; a second LLM back-translates it to English ("`usable(z3)` holds because z3 is declared and no `dead` reading refutes it") for maintainer sign-off. The verdict is `review-only = presumptively decaying` until that signature lands.
4. **Encoding as a reading-with-provenance.** The `.lp` file is itself a Pillar-2 ledger entry: `{commit, tree, session_id}`, criterion-before-result, so the *rule that produced the gate* is as auditable as the data — a DIRTY tree never yields a confirmed verdict.

## Verdict: phoenix or ash — and how we'll know
**Phoenix — leaning strong, undecided only on scale.** The semantic gap (defeat-under-contradiction, derived retraction) is real, the encoding runs *today* in 0.001s, and the false-authority risk is now an engineering pipeline (mutation + differential + justification) rather than a hand-wave. The single settling experiment is the 10k-fact dump: if it grounds under 2s and beats SQL on the ≥5 multi-defeater cases, this earns a permanent seat at the frontier. What flips me to ash: grounding blow-up on real store sizes (kill-condition a), since a gate that times out audits nothing — that, and only that, is the honest failure mode, and it is measurable, not assumed.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
