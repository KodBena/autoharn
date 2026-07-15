# 02 — Prolog & Constraint Logic Programming (SWI-Prolog, CLP(FD)) — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 2 defect(s) noted · **not rewritten** (the hardening pass was a no-op).
>
> ⚠️ **Mechanical re-check flags this as a possible false-negative**: the auditor marked it `deflated=false`, yet 1 of its own defects cite reducible-only / concession tells.

## Prolog & Constraint Logic Programming (SWI-Prolog, CLP(FD)) — Fair Trial

The bet: a single declarative Horn-clause engine can host BOTH autoharn's data model and its deductive gates, so that liveness, non-monotonic defaults, and paraconsistent status are *defined* by their rules rather than re-derived per query — and CLP(FD) adds in-process finite reasoning that emits a checkable trace.

## Maximal ambition

The frontier claim is **deductive maintenance with executable, queryable proof objects** — not just "did a gate pass" but "here is the SLD derivation that shows why this finding is live, and here is the counter-derivation if you retract one fact." Three things become possible that SQL/Z3-as-usual cannot do jointly:

1. **Negation-as-failure liveness as a first-class semantics.** The Pillar-2 ledger's "live head" is `live(F) :- finding(F), \+ supersedes(_,F).` — *liveness is the absence of a proof of supersession*. A new `supersedes/2` fact silently, correctly retracts a default conclusion. This is genuine non-monotonic reasoning: the SAME program returns a different, still-sound answer when you append to the ledger, with no schema change. SQL re-evaluates a `NOT EXISTS` join; Prolog *is* the closed-world semantics.

2. **One program for the closure AND the meta-closure.** Prolog can quantify over its own clauses (`clause/2`), so Pillar-3's meta-sweep ("every `discipline/2` rule declares an `enforcement/2` from the closed vocabulary") is a rule over rules in the same language — the gate and the thing it gates share one surface.

3. **Proof-carrying gates.** With a meta-interpreter, every gate violation can ship its derivation tree as data. That tree is the auditability artifact: stored under `{commit,tree,session_id}`, replayable, diff-able. SQL gives you a failing row; Prolog gives you *the inference path to that row*.

## The expressiveness gap (precise, not hand-wavy)

Honest boundary, stated as argument. For pure transitive closure over the supersession edges, SQL `WITH RECURSIVE` is equi-expressive and often faster — the prior section was right that the *closure* is not the gap. The real gap is **semantic, not relational**:

- **Stratified negation-as-failure over recursion.** `current(F,Base) :- supersedes(F,Base), live(F)` mixes recursive closure with negation of a recursive predicate. In SQL this is expressible only with awkward `NOT EXISTS` correlated against the same recursive CTE, and standard SQL forbids recursive references inside a subquery's `NOT EXISTS` — you hit a correctness cliff or must materialize and re-query. Prolog's stratified WFS gives this a defined, total semantics for free.
- **Succinctness of defaults.** A default-with-exceptions (`decision(X,allow) :- \+ override(X,_)`) is one clause; the SQL equivalent grows a join per exception class. Decidability is equal (both terminate on finite ground data); succinctness and *clarity-of-intent* are not.
- **Abduction.** `?- which facts would make gate G fail?` — running rules backward to enumerate minimal fact-sets — is native to Prolog (and to s(CASP), packable) and has NO SQL analogue. This is the one capability with no cheap substitute.

So: closure — no gap. Defaults, stratified NAF, abduction, proof-trace — real gap.

## The falsifiable experiment (the trial)

**Setup.** Export the live autoharn provenance ledger (the Witness→Correction supersession facts) and the perf-token table to ground Prolog facts. Build a gate suite under `janus-swi` driven from the existing Python CI harness.

**Encoding (real SWI syntax):**

```prolog
:- use_module(library(clpfd)).
% --- Pillar 2: liveness + supersession ---
live(F)            :- finding(F), \+ supersedes(_, F).
current(F, Base)   :- supersedes(F, Base), live(F).
% --- Pillar 3: perf substantiation gate (fires if any solution) ---
violation(perf_unsubstantiated, Tok) :-
    perf_token(Tok), \+ reading_of(Tok, _), \+ marked_unsubstantiated(Tok).
% --- Pillar 2: dirty tree can never be confirmed (paraconsistent) ---
status(R, confirmed) :- result(R), tree(R, clean), corroborated(R).
violation(dirty_confirmed, R) :- result(R), tree(R, dirty), status(R, confirmed).
% --- proof-carrying meta-interpreter ---
prove(true, true) :- !.
prove((A,B),(PA,PB)) :- !, prove(A,PA), prove(B,PB).
prove(G, G-Body) :- clause(G, B), prove(B, Body).
```

**Success criterion.** (a) On the real ledger, `current/2` reproduces the maintainer's hand-computed live set with ZERO discrepancy; (b) every `violation/2` clause is non-empty exactly when a planted defect is present and empty on the clean tree; (c) each fired gate emits a `prove/2` derivation that back-translates to the English the maintainer accepts; (d) wall-clock under 2s on the full store.

**KILL CONDITION (non-negotiable).** Retire Prolog if EITHER: (1) the live-set computation diverges from SQL `WITH RECURSIVE` on the SAME data AND the divergence is traced to Prolog's procedural semantics (cut/ordering/non-stratified NAF) rather than a data bug — i.e. the declarative reading lied; OR (2) producing a trustworthy gate requires so much defensive scaffolding (mode declarations, occurs-check, termination guards) that the encoding is *less* auditable than the SQL it replaces, measured by maintainer review time per gate exceeding the SQL baseline by 2×. Either outcome means the semantic gap doesn't pay for its risk here.

## Neutralizing false authority (verification scaffolding)

The mis-encoding risk (a fumbled `\+` or `!` yielding a confident wrong proof) is the central research problem, engineered down to a measured residual:

- **Mutation fixtures.** For every gate, a stored `should_fire/2` and `should_not_fire/2` corpus; CI asserts a known violation and confirms the gate FIRES (a green gate on a planted defect is itself a defect).
- **Differential solver.** Run liveness BOTH in Prolog and in Postgres `WITH RECURSIVE`; the two must agree on every store, every commit. Disagreement halts CI and is logged as a reading, not silently reconciled.
- **Back-translation.** Each clause carries an English gloss; the `prove/2` derivation renders to that gloss for maintainer sign-off — encoding→English→review is a Pillar-1 capability declaration.
- **Bounded cross-check.** Re-encode the same invariant in Z3/clingo and check small-model agreement (metamorphic: permuting fact order must not change the answer set — directly catches cut/ordering bugs).
- **Provenance.** The `.pl` source is stored as a reading under `{commit,tree,session_id}`; `:- set_prolog_flag(occurs_check, true)` and explicit mode/termination checks (via `library(mode)`) are part of the gate, not optional.

## Verdict: phoenix or ash — and how we'll know

**Phoenix — narrowly, where the semantic gap is real.** My current bet: Prolog earns a frontier slot for **negation-as-failure liveness, default-with-exception reasoning, and abductive "what fact would break this" queries** — none of which SQL expresses cleanly — and especially for **proof-carrying gates**, which raise the auditability ceiling rather than match it. It is ash for plain transitive closure (SQL ties and is faster). The settling experiment is the differential-solver liveness run above: if Prolog and `WITH RECURSIVE` agree on every real store while Prolog ALSO emits a maintainer-validated derivation trace, it's phoenix. What flips me to ash: the live-set divergence kill-condition firing on real data, proving the declarative reading is procedurally unsound in practice — at that point the logic costume hides exactly the error Pillar 2 exists to catch, and abduction alone (better served by s(CASP)) would not justify the engine.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
