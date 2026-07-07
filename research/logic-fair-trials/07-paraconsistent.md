# 07 — Paraconsistent & Many-valued Logic — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 2 defect(s) noted · **not rewritten** (the hardening pass was a no-op).

## Paraconsistent & Many-valued Logic — Fair Trial

The bet: autoharn's Provenance Ledger (P2) will, over time, hold *mutually contradictory* findings — two scanners, two advisories, a superseded-but-not-yet-deleted claim. The wager is that paraconsistent + many-valued logic lets every CI gate stay *sound* over that inconsistent ledger — proving verdicts the familiar stack cannot, because classical logic over an inconsistent knowledge base proves *everything*.

## Maximal ambition

The frontier claim is a **quarantine theorem**: *a contradiction at claim X provably cannot alter the gate verdict at any claim Y not derivationally downstream of X.* This is the property that makes a green gate trustworthy on a knowledge base that is *known to contain conflicts you have chosen not to resolve yet*. Classical CI cannot offer it. I confirmed the failure mode concretely — a classical Z3 ledger asserting `clean_c1 ∧ ¬clean_c1` returns `entails release_c2 (unrelated)? True`: an inconsistent ledger **entails an unrelated release**. Every green gate built on a classically-inconsistent store wears total false authority. Paraconsistency is the only framing under which "the ledger contains a contradiction AND this unrelated gate is still meaningfully green" is a coherent, provable sentence. The maximal autoharn artifact: a ledger where conflicts are *first-class durable rows* (Belnap `both`), supersession moves verdicts only *up* a truth lattice (`retracted < provisional < confirmed`), and a meta-sweep proves no contradiction ever silently poisoned a downstream verdict — extreme auditability over an admittedly imperfect world, which is the real world.

## The expressiveness gap (precise, not hand-wavy)

SQL's three-valued `NULL` (Kleene K3) genuinely buys the `dirty/suspect` third value for free — the prior section is right that `WHERE promoted AND tree_clean IS NOT TRUE` is the correct, zero-cost dirty gate. That is **detection of unknown**, and SQL wins it.

The gap is **contained contradiction across a derivation chain** — Belnap's fourth value `both`, which SQL provably cannot express:

1. **Semantics.** SQL has no value for "asserted true *and* asserted false." You model it as two rows, but a join/aggregate then treats them as two independent facts; there is no `both` that *propagates as a single contained value*. SQL also has no notion of *explosion* to contain — so it cannot state, let alone enforce, the quarantine property.
2. **Soundness over inconsistency.** A recursive SQL view (`WITH RECURSIVE`) that derives a bundle verdict from conflicting inputs either silently propagates one side or needs a hand-coded guard at *every* hop. The paraconsistent consequence relation makes containment a property of the *semantics*, not of programmer vigilance — exactly the human-tedium barrier the LLM-authorship thesis targets.
3. **Succinctness/decidability.** "No `both` claim reaches a promoted bundle" is one ASP integrity constraint over the derivation graph; in SQL it is a manual materialization of the full paraconsistent closure plus per-hop guards.

Honest scope: if every contradiction autoharn meets is *terminal* (blocks one claim, never feeds a derived verdict), then K3-`NULL` suffices and `both` is dead weight. The gap is real **only** for *multi-hop* verdicts. That is the crux the experiment must settle.

## The falsifiable experiment (the trial)

**Setup.** Take the real P2 advisory→claim→bundle→release_gate chain. Seed one genuine conflict (two scanners disagree on `c1`) and one clean unrelated branch (`c2`). Encode in clingo 5.8.0 (installed; I ran this):

```prolog
advises(scanA,c1,true).  advises(scanB,c1,false).   % contradiction on c1
advises(scanA,c2,true).                              % unrelated clean branch
bundle(b1,c1). bundle(b2,c2). release_req(b1). release_req(b2).
val(C,both) :- advises(A1,C,true), advises(A2,C,false), A1 != A2.
val(C,true) :- advises(_,C,true), not val(C,both).
bundle_both(B) :- bundle(B,C), val(C,both).
release_ok(B) :- release_req(B), not bundle_both(B).
violation(B,blocked_by_contradiction) :- release_req(B), bundle_both(B).
```

Run output (verbatim): `release_ok(b2) violation(b1,blocked_by_contradiction)` — `b2` releases, `b1` is quarantined. The classical Z3 control on the same facts entails the unrelated release (explosion, shown above).

**Success criterion:** the paraconsistent gate (a) releases `b2`, (b) blocks `b1`, and (c) survives N injected real contradictions from ledger history where the classical control would have green-lit an unrelated release. Plus: across autoharn's actual invariant set, ≥1 verdict is genuinely *multi-hop* over conflictable inputs.

**KILL CONDITION (non-negotiable):** if an audit of real ledger history shows every contradiction autoharn actually faces is terminal — i.e. there exists **no** case where contradiction *containment* (not mere detection) changes a downstream gate verdict — then K3-`NULL` already does the job, `both` adds machinery with no provable payoff, and this logic is retired to ash. Equivalently: if the classical control *never* explodes into a wrong gate on real data, the quarantine theorem protects against nothing.

## Neutralizing false authority (verification scaffolding)

The prior section's fear — an LLM writes classical `not` where it meant `val(C,both)`, and paraconsistency *hides* the resulting bug by refusing to crash — is the central research problem, and it is engineerable:

1. **Mutation fixtures (primary).** Store golden fact-sets with known verdicts; auto-mutate the encoding (`val(C,both)` → classical `not`, `!=` → `==`) and assert each mutant *flips* a golden verdict. An encoding whose mutants all still pass is unfalsifiable and rejected. This directly kills the silent-miscoding failure.
2. **Lattice unit tests.** Assert the invariants of the value space itself: `both` blocks promotion, `unknown ≠ false`, supersession is monotone up the lattice — before any gate trusts the encoding.
3. **Differential solver.** Run the classical Z3 control beside clingo; *every* divergence (Z3 explodes, clingo contains) must trace to a logged, real contradiction. A divergence with no contradiction row is a miscoding alarm.
4. **Justification-carrying output.** Emit `violation(b1, blocked_by_contradiction)` *with* the witnessing `advises/3` rows; the gate ships its own proof object, stored as a P2 reading-with-provenance (`{commit, tree, session_id}`).
5. **Back-translation.** Template each rule to English ("a bundle inheriting a both-valued claim cannot release") for maintainer review — criterion-before-result.

## Verdict: phoenix or ash — and how we'll know

**Undecided-until-trial, leaning phoenix.** The logic is non-redundant *in principle* — I demonstrated explosion in the classical control and containment in clingo on the same ledger, so the capability is real and runnable today. What's unproven is **incidence**: does autoharn's real ledger actually produce *multi-hop verdicts over conflictable inputs*? The single settling experiment is the kill-condition audit: scan ledger history for one verdict whose correctness depends on contradiction containment rather than mere `NULL`-detection. One such case → phoenix (the quarantine theorem is load-bearing and SQL cannot state it). Zero across a representative history → ash, K3-`NULL` wins, and I retire it on a *failed experiment*, not a familiarity argument. Evidence that flips me toward ash early: the differential solver shows Z3 and clingo *never* diverge on real data.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
