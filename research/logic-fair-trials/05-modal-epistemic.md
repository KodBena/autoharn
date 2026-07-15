# 05 — Modal & Epistemic Logic — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 3 defect(s) noted · **not rewritten** (the hardening pass was a no-op).
>
> ⚠️ **Mechanical re-check flags this as a possible false-negative**: the auditor marked it `deflated=false`, yet 2 of its own defects cite reducible-only / concession tells.

## Modal & Epistemic Logic — Fair Trial

The bet: autoharn's hardest invariants are not about facts but about *knowledge-status and temporal commitment* — "confirmed entails true," "a DIRTY reading may be believed but never known," "no result was judged before its criterion was known." Modal/epistemic logic makes these *kinds of truth* with their own inference rules, machine-checkable as a `*_violations` gate, where SQL's `status` enum is only a label.

## Maximal ambition

The frontier claim: turn the provenance ledger from a store of *current rows* into a **model whose entire reachable state-space is provably knowledge-sound**. Today `work_status_violations` checks the present extension — the rows that exist now. The modal ambition is to check the *transition system of the write-API itself*: prove that **no sequence of appends a session could perform** can ever produce a state where `status=confirmed` holds for a claim that is not true-in-all-epistemically-accessible-worlds. That is a statement about all possible futures and all possible epistemic alternatives — a quantifier SQL does not have.

Concretely, three things become provable that the familiar tools cannot state:

1. **Factivity as an enforced bridge, not a comment.** `K_session φ → φ`. "Confirmed" stops being a string and becomes an entailment: confirming a benchmark *obligates* the reading to be true in every world the session considers possible. A DIRTY tree introduces an accessible world where the number differs, so `K` is *underivable* there — the promotion is blocked by the logic, not by a reviewer remembering ADR policy.

2. **Pre-registration as a temporal-epistemic invariant.** `AG(result_emitted → Y K_engine criterion_registered)` — "whenever a result is emitted, yesterday the engine already *knew* the criterion." This binds the *measurement ⊥ interpretation* ordering into one falsifiable formula over the whole ledger's evolution, not a timestamp `WHERE` clause that only inspects rows that happen to exist.

3. **Distributed vs. common knowledge across sessions.** Two Claude Code sessions may each `B`-believe contradictory perf claims (`B_a φ`, `B_b ¬φ`) without the gate exploding; `suspect = ¬K_a φ ∧ ¬K_a ¬φ` makes ignorance first-class; and `C_{a,b} φ` (common knowledge) is the right model for "a fact every session is entitled to rely on without re-deriving." No relational store expresses "every agent knows that every agent knows."

## The expressiveness gap (precise, not hand-wavy)

Honest answer: for the *present-extension* checks, SQL is not beaten. "Is any row confirmed on a DIRTY tree?" is `SELECT ... WHERE status='confirmed' AND tree='DIRTY'`. The factivity gate I ran below is *more readable* in Prolog but not more *expressive* than that SQL — and the investigation's prior section was right that a two-table schema already separates reading from interpretation.

The gap is real only along two axes, and they are genuine:

- **Quantification over reachable states (decidability/semantics).** The prereg invariant is `AG(p → past q)` over the *transition system*, not the current table. SQL evaluates against the rows that exist; a CTL/CTLK model checker evaluates against *all reachable states of the write-API* and returns a **counterexample trace** — a specific append-sequence that would violate prereg — which no `SELECT` can produce because the violating rows do not exist yet. This is model checking, categorically outside SQL.
- **Succinctness of nested epistemic depth.** `K_a(value=12x)` vs `value=12x`, and `C_{a,b}` over n sessions, encode a 2^n indistinguishability structure that a relational encoding can only flatten by materializing the join blow-up. Modal succinctness here is the standard PSPACE-vs-explicit result.

Everything else autoharn does (classification, class-keyed nets, cycle detection) is *not* modal, and forcing Kripke frames on it is pure overhead.

## The falsifiable experiment (the trial)

**Stage A — doxastic factivity gate, runnable TODAY on installed SWI-Prolog 9.3.31.** Image a ledger slice (`reading/3`, `confirmed_status/1`, `holds/2`) and encode the T-axiom bridge. I ran exactly this:

```prolog
knows(C,V)         :- confirmed_status(C), reading(C,V,clean), holds(C,V).  % K factive
false_authority(C) :- confirmed_status(C), reading(C,V,_), \+ knows(C,V).   % gate
```

On a seed where `r2` is `confirmed` but on a `dirty` tree, the gate emitted `VIOLATION confirmed-but-not-known: r2`. **Success:** the gate flags exactly the confirmed-on-DIRTY rows that the policy forbids, with zero false positives on the clean fixture.

**Stage B — temporal-epistemic prereg, runnable via `pip install pynusmv` (NuSMV bundled; MCMAS for true CTLK).** Encode the write-API as a transition system with a `criterion_known` boolean and `result_emitted` boolean, and check:

```
CTLSPEC AG (result_emitted -> Y criterion_known)   -- model checker returns a counterexample trace if refutable
```

**Success:** the checker *certifies* the invariant on the faithful model and produces a concrete violating trace when I inject a "judge-before-prereg" write path.

**KILL CONDITION (non-negotiable).** Retire modal/epistemic for autoharn if **either**: (a) every invariant the trial encodes is reproduced by a `work_status_violations` SQL arm of comparable line-count *and* the SQL version also catches the mutation fixtures below — i.e. the model-checking quantifier-over-futures buys no defect the present-extension query misses on real ledger data; **or** (b) the LLM-authored accessibility relation cannot be made trustworthy: the mutation suite (next section) shows frame errors slipping through at a rate that makes the green gate *less* reliable than the SQL it replaces. Either outcome is ash.

## Neutralizing false authority (verification scaffolding)

The central research problem is that a modal proof is only as sound as the accessibility relation the LLM wrote (drop reflexivity and `K` silently stops being factive). This is an *engineering* problem, and I demonstrated the core mechanism:

- **Mutation fixtures (shown working).** I weakened the frame — dropped the `clean`-tree conjunct from `knows/2` — and the gate flipped to **GREEN on the known-bad ledger** (`r2` escaped). A mutation fixture asserting "this seed must stay RED" *catches that exact frame error*. Every axiom (T, D, 4, 5) gets a paired mutant whose escape fails CI.
- **Pinned axioms as provenance readings.** The frame is not inferred — each axiom is an explicit clause with a one-line justification stored as a *reading-with-provenance* (commit, tree, session_id) in the ledger, so "we assumed S5/perfect introspection" is an auditable, supersedable record, not a buried default.
- **Back-translation.** Encoding → English ("confirmed obligates the reading true in every world; DIRTY admits a divergent world") → maintainer review, stored alongside the clause.
- **Differential / bounded cross-check.** Run the *same* invariant as the SQL present-extension query and as the model check; on the shared finite fixture they must agree — disagreement is a bug in one encoding, surfaced rather than trusted.
- **Justification-carrying output.** The model checker's counterexample trace *is* the proof object; a passing gate ships the trace-free certificate, a failing one ships the witnessing append-sequence.

## Verdict: phoenix or ash — and how we'll know

**Undecided-until-trial, leaning phoenix-but-narrow.** The doxastic factivity gate is a phoenix *as readability/inference-hygiene* but not as expressiveness — it ties Stage A's kill-condition (a). The whole bet rides on **Stage B**: does model-checking the write-API's reachable states catch a prereg/false-authority defect on real `audit_log` data that the present-extension SQL provably cannot? Run the single settling experiment — encode the work-status write-API in NuSMV/MCMAS and feed it a replayed session trace. **Flips to phoenix** if it returns a counterexample append-sequence for an invariant no `SELECT` over current rows can refute. **Flips to ash** if every counterexample corresponds to a row that, once it exists, an SQL arm would already have flagged — then modal logic was elegant narration over a query, and SQL wins the frontier here.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
