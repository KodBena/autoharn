# 01 — Datalog & Deductive Databases — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 2 defect(s) noted · **not rewritten** (the hardening pass was a no-op).

## Datalog & Deductive Databases — Fair Trial

The bet: an LLM-authored set of Horn-clause rules over autoharn's ledger and registry can compute *every entailed consequence* of the project's invariants — `_violations` relations, live-finding closures, meta-sweep coverage — as a single least-fixpoint artifact whose **emptiness IS the contract**, more succinctly, more uniformly, and more auditably than recursive SQL, a script, or Z3-as-search ever could.

## Maximal ambition

The frontier: **one declarative deduction layer that is simultaneously the gate engine, the supersession resolver, and its own meta-auditor — and that emits a justification (proof) for every derived fact.** Push it all the way: autoharn does not just *check* invariants, it maintains a *closed-world certificate of health*. Because Datalog computes the least fixpoint to saturation, a green run is a statement about the **entire derivable universe** of the current facts, not a sampled assertion. With LLM authorship removing the tedium, every Pillar-3 discipline-rule becomes a clause, and the meta-sweep (`every rule declares a surface; every mechanism resolves on disk`) becomes *Datalog reasoning over Datalog's own rule catalog as EDB facts* — the harness audits its own audit, in the same language, in the same run. That reflexive self-application is the thing SQL/Z3/script can't do cheaply: the rules are data, the catalog is a relation, and "is any rule unenforced?" is just another `_violations` clause. The summit is **proof-carrying gates**: not "the violations set is empty," but "here is the derivation tree showing *why* this finding is live and *why* no pre-registration violation fires" — auditability as a provenance object, not a boolean.

## The expressiveness gap (precise, not hand-wavy)

Honest and precise: against *plain* SQL (no `WITH RECURSIVE`), the gap is decisive — transitive closure of `supersedes` is not first-order expressible, full stop. Against `WITH RECURSIVE` Postgres the gap is **not decidability but semantics + succinctness + safety**:

1. **Stratified negation is a guarantee SQL gives you only by hand.** `live(F) :- finding(F), not superseded(F)` where `superseded` is itself recursive requires negation over a recursive relation. Postgres *forbids* recursive references inside `NOT`/aggregates in a `WITH RECURSIVE` term — you must materialize the closure first, then a second query negates it, and *nothing in the SQL checks you stratified correctly*. Datalog's stratification check is a **mechanical, decidable property of the program** — the engine refuses an unstratifiable rule set. That is a correctness guarantee SQL structurally cannot offer.
2. **Succinctness / uniformity as an auditable invariant.** Every gate is *syntactically* `head_violation(X) :- body`. The meta-sweep can then quantify over rules because rules share one shape. In SQL each gate is a bespoke `WITH RECURSIVE … LEFT JOIN … WHERE NOT EXISTS`, and "is every gate of the right shape?" is no longer a machine-checkable property — you've lost the reflexive handle.
3. **Proof/justification output.** Soufflé `--provenance` and ASP justification emit the derivation tree for free; SQL gives you a result set with no "why."

So the gap is real but bounded: it is *not* "SQL can't decide this" (recursive SQL can), it is "SQL cannot give you stratification-as-a-checked-property, one-shape uniformity for meta-sweep, or derivation provenance — the three things that make the gate *trustworthy* rather than merely *correct-if-you-wrote-it-right*."

## The falsifiable experiment (the trial)

**Setup.** Export the real ledger + registry to CSV/facts: `result/3`, `criterion/2`, `supersedes/2`, `finding/1`, `discipline_rule/1`, `declares_surface/1`, `mechanism/2`, plus a filesystem scan `exists_on_disk/1`. Encode the three flagship invariants — pre-registration (temporal), supersession liveness (recursive+negation), meta-sweep (reflexive) — in a single program. Run on the **already-installed** clingo 5.8.0 (Datalog is the negation-stratified ground fragment of ASP; promote to Soufflé only if slow).

**Encoding (verified runnable — output below is real):**

```prolog
preg_violation(R) :- result(R,C,Tres), criterion(C,Tdecl), Tdecl >= Tres.
superseded(F)     :- supersedes(_,F).
live(F)           :- finding(F), not superseded(F).
unenforced(Rule)  :- discipline_rule(Rule), not declares_surface(Rule).
dangling(M)       :- mechanism(M,Path), not exists_on_disk(Path).
```

Ran on a fixture (`crit_b` declared at T=60 after its result at T=50; chain f3→f2→f1): clingo returned `live(f3) preg_violation(r2)` — correct: only the head of the chain is live, only the post-hoc criterion fires.

**Success criterion.** On real data, the program (a) reproduces every violation the existing Postgres prototype finds (differential equivalence), (b) computes the live-finding set whose closure SQL needs two passes for, in one stratified program, and (c) the meta-sweep flags at least one genuine unenforced-rule or dangling-mechanism that was not hand-noticed — i.e. the reflexive layer pays rent.

**KILL CONDITION (non-negotiable).** Retire Datalog if **either**: (1) on the real ledger the engine and the Postgres prototype disagree on *no* case AND the meta-sweep surfaces *nothing* a 20-line `WITH RECURSIVE` + a `find | comm` script wouldn't — i.e. the succinctness/reflexivity win produces **zero** marginal caught defect across the actual corpus after one month of live gating; **or** (2) the stratification/encoding burden generates a false-green that the mutation harness below catches *and* the same class of error is shown to be *less* likely in the SQL formulation. Either outcome = ash.

## Neutralizing false authority (verification scaffolding)

The "LLM mis-encodes, gate wears false authority" objection is the **central research problem**, made an engineering problem here:

- **Mutation fixtures (primary).** For each gate, store a *known-bad* fixture that MUST turn the relation non-empty, AND a *known-good* fixture that MUST keep it empty. CI runs the gate against both — a gate that can't light up on its own mutant is a dead gate. This directly kills the "confidently empty" failure: `preg_violation` is tested against a fixture engineered to violate pre-registration (the `crit_b@60` case above).
- **Differential solvers.** Run the SAME facts through clingo *and* the Postgres `WITH RECURSIVE` prototype; any disagreement is a P1 alarm. Two independent semantics agreeing is far stronger than one green check.
- **Back-translation as a reading-with-provenance.** Store each clause with an LLM-generated English gloss AND a maintainer-reviewable provenance record `{commit, tree, session_id, criterion-before-result}`. The gloss is reviewed; the clause+gloss is the audited artifact, not the clause alone.
- **Proof-carrying output.** Run with `clingo --output / justification` (or Soufflé `--provenance`) so every derived violation ships its derivation tree — the gate explains itself.
- **Stratification as a tested property.** Treat any negation-bearing rule as presumptively decaying: assert the program's stratification in CI (the engine rejects unstratifiable input — capture that as a passing test), so "negation modeled backwards" surfaces as a structural error, not a silent wrong answer.

## Verdict: phoenix or ash — and how we'll know

**Phoenix — conditional, leaning strong.** Not because it beats SQL on raw decidability (recursive SQL ties on closure), but because **stratification-as-a-checked-property + one-shape uniformity enabling the reflexive meta-sweep + proof-carrying justification** are three trust-amplifiers SQL structurally lacks — and trust is autoharn's actual objective function, not query power. The single settling experiment: run the unified clingo program above against the real ledger for one gating cycle, with the mutation+differential scaffold live. It flips to **ash** if the kill condition fires — specifically if the meta-sweep and live-closure produce *zero* marginal caught defect over real data that recursive SQL didn't already catch, meaning the succinctness is cosmetic. It stays **phoenix** the moment the reflexive layer catches one real unenforced rule, or the differential check exposes one SQL-prototype divergence the engine got right.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
