# 11 — SMT & Classical First-order Logic (Z3 / cvc5) — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 2 defect(s) noted · **not rewritten** (the hardening pass was a no-op).

## SMT & Classical First-order Logic (Z3 / cvc5) — Fair Trial

The bet on trial: that classical FOL-plus-theories is the right *substrate for autoharn's gates themselves* — that the invariants in the Capability Registry, Provenance Ledger, and Logic Safety Net can be expressed once, as quantified formulas over open-ended values, and discharged with a *universal* `unsat` verdict plus a minimal blame-core — something no `WHERE` clause can produce. LLM authorship is the unlock: the per-store axiomatization was always expressible, just too tedious to hand-write and keep in sync.

## Maximal ambition

The frontier ambition is a **single global consistency theory of the whole registry**, not a pile of independent row-checks. Today each store gets its own `*_violations` view; they cannot reason *across* each other. SMT lets autoharn assert the registry's full schema as axioms — classification exclusivity, task-shape→blessed-tool functionality, supersession acyclicity bounds, criterion-before-result temporality, perf-claim substantiation — and ask one question: *can any assignment of pending edits satisfy all invariants simultaneously?* If `unsat`, the **minimal unsat-core is a machine-generated, minimal repair target**: the smallest set of declared facts whose mutual presence is impossible. That is *deductive maintenance* in the literal sense — the gate doesn't just flag a bad row, it proves which combination of intentions cannot coexist and hands the maintainer the irreducible conflict.

The second ambition is **proving properties of rules, not data**. "No two task-shapes can ever map to the same tool" or "the classification predicate is total and injective over the closed vocabulary" are ∀-statements over all possible registries, present and future. SQL can confirm the *current* table obeys them; SMT proves the *constraint set itself* can never be violated by any admissible edit — a guarantee that survives data churn. With quantifiers over uninterpreted functions, autoharn can verify the *meta-sweep* invariant ("every rule declares an enforcement surface whose mechanism resolves") as a genuine theorem, closing the gap the prior section rated only "med."

## The expressiveness gap (precise, not hand-wavy)

Three things SQL provably cannot do, by semantics:

1. **Universal negative claims.** SQL is existential/closed-world: it reports present rows. `unsat` is a closed-form proof that *no* model exists over the *open* domain of declared symbols. "No assignment of these five class-bits ever yields a valid double-tag" is a statement about infinitely many hypothetical assignments; a view checks the finite current table. Different quantifier, not different speed.
2. **Minimal blame.** `unsat_core()` returns the *minimal* contradictory subset. A `CHECK` constraint that fails tells you a row is bad; it does not isolate the smallest conflicting set across multiple constraints. Computing that in SQL means hand-rolled set-cover — exponential and bespoke.
3. **Succinct exclusivity over quantified structure.** `PbEq(...,1)` ("exactly one") and ∀-functionality of a mapping are one line each; in SQL they are triggers plus anti-join views per pair, which grow combinatorially and drift out of sync with the schema.

Where the honest answer is "SQL suffices": pure **graph reachability** (supersedes-chain ancestry, dangling mechanism refs) is `WITH RECURSIVE` territory — cheaper and clearer than SMT. The gap is real but *bounded to the consistency/exclusivity/forced-mapping shape*, not universal.

## The falsifiable experiment (the trial)

**Setup.** Take the live Capability Registry. Encode every capability's class-tags and every task-shape→tool row as tracked assertions; add the exclusivity and functionality axioms. Run on real data plus a battery of 50 LLM-generated *mutant* registries (each injecting one known defect).

**Encoding (validated, runs on installed Z3 4.16.0):**

```python
s = Solver(); s.set(unsat_core=True)
b = {(c,k): Bool(f'{c}_{k}') for c in caps for k in classes}
for c in caps:
    s.assert_and_track(PbEq([(b[(c,k)],1) for k in classes], 1), f'exactly_one_{c}')
s.assert_and_track(b[('z3_solver','solver')], 'fact_z3_solver')
s.assert_and_track(b[('z3_solver','venv')],   'fact_z3_venv')
# -> unsat ; core = [exactly_one_z3_solver, fact_z3_solver, fact_z3_venv]
```

The core names exactly the offending pair plus the violated rule — *confirmed in this environment*.

**Success criterion:** on the clean registry, `sat`; on all 50 mutants, `unsat` with a core that is (a) minimal and (b) names the injected defect — and total wall-clock under a few seconds so it is a viable CI gate.

**Kill condition (non-negotiable):** if the registry invariants are all expressible as `WITH RECURSIVE` violations-views that catch the *same* 50 mutants at comparable clarity AND SMT adds no *universal* guarantee (every interesting invariant turns out to be existential/reachability-shaped), then SMT is redundant infrastructure — retire it to the two niche gates and use Postgres. Equally retiring: if realistic invariants require quantifiers that push Z3 *and* cvc5 to `unknown`/timeout on the real registry, the `unsat` verdict is unavailable when it matters → ash.

## Neutralizing false authority (verification scaffolding)

The central research problem: a green `unsat` is only as trustworthy as the encoding. Make it an engineering pipeline:

- **Negation cross-check (mechanized).** For every claim assert both `P` and `¬P`. `sat` on both ⇒ under-constrained encoding ⇒ gate *fails closed*. This catches dropped constraints automatically.
- **Mutation fixtures as the acceptance test.** The 50 mutants above are golden: a mutant that returns `sat` is a hole in the axiomatization, and the suite is the encoding's own `*_violations` gate.
- **Differential solvers.** Same SMT-LIB2 file through Z3 and cvc5; any verdict disagreement = encoding bug, never trusted. Both are standard-conformant, install is `pip`.
- **Back-translation reading.** LLM renders each axiom to English; maintainer signs off; the signed gloss is stored as a **reading-with-provenance** `{commit, tree, session_id}`, so the encoding's *meaning* is auditable, not just its output.
- **Justification-carrying output.** Store `unsat_core()`/`model()` as a measurement, separate from the interpretation (Pillar 2's measurement ⊥ interpretation), so the proof artifact is replayable.
- **Bounded-model cross-check.** Independently enumerate small registries (≤ k caps) by brute force and confirm SMT agrees — pins the encoding against a ground-truth oracle.

## Verdict: phoenix or ash — and how we'll know

**Phoenix, conditional** — leaning strongly phoenix for the *exclusivity / forced-mapping / global-consistency* gates, where the validated unsat-core blame is a capability SQL structurally lacks. The single settling experiment is the 50-mutant trial above: phoenix iff SMT catches every mutant with a minimal, defect-naming core in seconds *and* at least one invariant is a genuine ∀-theorem no view can express. Evidence that flips me to ash: the mutant set is fully caught by `WITH RECURSIVE` at equal clarity (gap collapses to reachability), or realistic quantified invariants drive both solvers to `unknown`. No retreat-to-SQL hedge: the question is whether the *universal verdict plus minimal core* earns its place at the frontier, and the env already shows the mechanism firing.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
