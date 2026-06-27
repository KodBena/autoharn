# 09 — Linear & Resource-aware Logic — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 3 defect(s) noted · **not rewritten** (the hardening pass was a no-op).
>
> ⚠️ **Mechanical re-check flags this as a possible false-negative**: the auditor marked it `deflated=false`, yet 3 of its own defects cite reducible-only / concession tells.

## Linear & Resource-aware Logic — Fair Trial

The bet on trial: autoharn has facts that are *spent*, not eternal — a liveness token a refutation consumes, a measured `reading` a perf-claim discharges against, a `clean_tree` budget a promotion must pay. Modeling these as **linear resources** (CHR multiset rewriting; Petri/rewriting-logic reachability) should make "spent-but-still-counted" defects *structurally underivable* and let us prove a safety theorem over the whole concurrent lifecycle — not just spot-check rows.

## Maximal ambition

The frontier is not a better gate; it is a **safety theorem over the reachable resource-state space**. Encode supersession / promotion / refutation as multiset rewrite rules and ask a model-checker: *across every interleaving*, is any "bad marking" reachable — e.g. a state where a REFUTED capability token is simultaneously `live` and counted toward a green gate? This is coverability, and it quantifies over execution *orders* SQL never enumerates. With LLM authorship removing the tedium of writing the rules, two things become possible that the familiar tools cannot do:

1. **Proof-carrying gate decisions.** Every promotion/discharge emits its *consumed-resource trace* — the exact tokens spent to reach `confirmed`. That trace is a justification object the Provenance Ledger (P2) stores as a reading: the gate doesn't assert "promotable," it *exhibits the spend that earned it*.
2. **Deductive maintenance as re-proof.** When a maintainer adds a rule, re-run the coverability proof over the *new* transition system. A regression becomes a theorem that breaks, not a test that happens to be missing — the P3 meta-sweep ("every rule declares an enforcement surface") gains a machine-checked closure property.

## The expressiveness gap (precise, not hand-wavy)

Honest first: the **single-spend uniqueness** ("one reading discharges at most one claim") is *not* beyond SQL — a `UNIQUE(reading_id)` on the claims table enforces it trivially. I will not pretend otherwise. The CHR run below shows two perf-claims (`c_pr42`, `c_pr99`) against one reading `r1`; exactly one discharges and the other is *forced* to `unsubstantiated` — elegant, but Postgres does it with a constraint.

The genuine gap is **concurrent reachability/coverability over an unbounded multiset**. "Under all interleavings of {refute, supersede, promote, amend}, is a state with `live(C) ⊗ refuted(C) ⊗ counted(C)` reachable?" is not a query — a recursive CTE cannot quantify over rewrite-rule interleavings and won't terminate on an unbounded token marking. Petri-net coverability is EXPSPACE-complete: a *different complexity class*, not a slow `SELECT`. Second, **succinctness + auditability**: the entire consumption discipline is four rewrite rules whose trace is self-documenting, versus a thicket of triggers + `CHECK`s + `UPDATE`-ordering whose correctness depends on trigger firing order — invisible and unauditable. SQL keeps *current state*; linear logic keeps *the act of spending*, which is the thing P2 wants to audit.

## The falsifiable experiment (the trial)

**Setup.** Take N real provenance records (claims, readings, {commit,tree,session_id}, ADR amendments). Two stages, both runnable today on the installed SWI-Prolog 9.3.31 (verified) plus Maude.

**Stage A — CHR consumption gate (verified running):**
```prolog
:- use_module(library(chr)).
:- chr_constraint reading/2, claim/2, discharged/2, unsubstantiated/1.
claim(Tok,R), reading(R,V) <=> discharged(Tok,V).   % spend the reading
claim(Tok,_)               <=> unsubstantiated(Tok). % nothing left -> honest-NULL
```
```prolog
promote(B), benchof(B,T), clean(T) <=> confirmed(B). % spend clean-tree budget
promote(B), benchof(B,T), dirty(T) <=> suspect(B).   % dirty mints none -> stuck
```
I ran both: clean→`confirmed(bx)`, dirty→`suspect(by)`, and the double-claim→`discharged=[c_pr42] unsubstantiated=[c_pr99]`.

**Stage B — Maude coverability:** lift the same rules to `rl [promote] : ... => ...` and `search` for a marking containing `live(C) refuted(C) counted(C)`.

**Success criterion.** On the N records, the CHR gate flags *exactly* the violations a hand-audit finds, with a usable spent-token trace; AND Stage B either proves no bad marking is reachable or returns a concrete bad interleaving a `_violations` query was *not* watching.

**KILL CONDITION (non-negotiable).** Retire linear logic for autoharn if **either**: (a) every defect the CHR consumption catches is *also* caught by a single Postgres `UNIQUE`/`_violations` query AND the spend-trace changes no reviewer decision across the N records (then it is pure ceremony); **or** (b) the mutation suite below shows an LLM `!`↔⊗ mis-encoding that survives scaffolding and yields a green-but-wrong gate. Either outcome kills it.

## Neutralizing false authority (verification scaffolding)

Mis-encoding lives entirely in invisible operators (`!` vs plain, the `\` kept/removed marker) — so we make that the engineering target, not an excuse:

- **Mutation fixtures.** Programmatically flip each premise to reusable (`!reading` / change `<=>` to `\`) and *assert the gate goes red*. A mutation that leaves the gate green is a hole in the test, by construction. This is the experiment's decisive instrument.
- **Differential solvers.** Encode the same invariant three ways — CHR, Postgres `UNIQUE`/`_violations`, Z3 enum — and require unanimous votes; any disagreement halts the gate and files a P2 reading. SQL becomes a *cross-check*, never the fallback.
- **Back-translation.** Each rule is auto-rendered to English ("a promotion spends one clean-tree token; a dirty tree mints none") for maintainer sign-off, stored as a reading-with-provenance ({commit,tree,session_id}) — the encoding itself is audited like data.
- **Proof-carrying output.** Dump `chr_show_store`/consumed trace as the justification attached to every `confirmed`/`suspect`.
- **Bounded cross-check.** networkx (installed) or bounded Maude `search` confirms each CHR "stuck" state corresponds to a genuinely uncoverable marking.
- **Metamorphic locality.** Adding an unrelated `!`-fact must not change any gate outcome; if it does, linearity was mis-scoped.

## Verdict: phoenix or ash — and how we'll know

**Phoenix for the consumption discipline (CHR), undecided on the heavy frontier (Maude coverability).** CHR is installed, runs (shown), and turns supersession/discharge from a destructive `UPDATE` into an auditable derivation step with a trace P2 can store — a real auditability gain at near-zero install cost. The **single settling experiment is the mutation suite** of "Neutralizing false authority": it simultaneously tests whether the logic catches anything (Stage A) and whether LLM mis-encoding is *detectable* (kill-condition b). What flips me to **ash**: differential agreement is always perfect with the SQL `UNIQUE` cross-check (no unique decision) *and* a mis-encoding slips the mutation suite. What flips me harder to **phoenix**: Stage B's Maude `search` returns a real reachable bad-interleaving in the ADR-amendment lifecycle that no `_violations` query was watching — proof that the frontier (concurrent reachability), not the row-check, is where this logic earns its place.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
