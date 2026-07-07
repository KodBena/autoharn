# 10 — Relevance & Substructural Logics

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

Logics obtained by *dropping structural rules* (weakening, contraction, exchange) from classical sequent calculus, so that premises must be genuinely *used* rather than merely *present*. The family runs from relevance logic (no weakening → no irrelevant premises, and crucially no explosion from contradiction) through linear logic (no weakening *or* contraction → facts are consumable resources used exactly once).

## Primer

In classical/Z3 logic, `A → B` can be proved by ignoring `A`, and one contradiction proves *everything* (ex falso). Substructural logics forbid both moves by deleting the bookkeeping rules that license them:

- **Drop weakening** ⇒ **relevance**: to assert `A ⊢ B`, `A` must actually be *used*. A side effect: `(A ∧ ¬A) ⊢ B` fails — contradictions stay *local* (paraconsistency).
- **Drop weakening + contraction** ⇒ **linear logic**: a hypothesis is a *token spent once*. `A ⊸ B` means "consume one `A`, produce one `B`." State that changes (a belief getting superseded) is modeled as tokens consumed and minted, never rewritten.

The intuition for *when* it's the right tool: whenever your domain is about **accounting** (this evidence was used / this resource was consumed / this contradiction must not infect everything) rather than timeless truth. Z3 assumes a *monotone, explosive* world; these logics assume a *resource-sensitive, paraconsistent* one — which is exactly the world of an append-only ledger with conflicting findings.

## Applicability to autoharn

**1. Paraconsistency — "conflicting advisories coexist without the gate exploding" (HIGH).** This is the single sharpest fit. Belnap's four-valued **FDE** (first-degree entailment) gives every fact one of {`true`, `false`, `both`, `neither`} — precisely autoharn's *provisional/confirmed/retracted* plus the **DIRTY/suspect** third value. Two findings that contradict yield `both`, and the violations-gate keeps evaluating instead of deriving `every_row_is_a_violation`. FDE is *truth-table evaluable*, so it lives directly in the store:

```sql
-- FDE meet on a finding asserted by two sources; 'both' = contradiction, not explosion
SELECT subject,
       CASE WHEN bool_or(v) AND bool_or(NOT v) THEN 'both'
            WHEN bool_or(v)                    THEN 'true'
            WHEN bool_or(NOT v)                THEN 'false'
            ELSE 'neither' END AS fde_status
FROM advisory GROUP BY subject;
```
Beats plain SQL/Z3 because Z3 would report `unsat` the moment two advisories clash and refuse to reason further; FDE *tags* the clash and lets CI proceed on the clean rows.

**2. Relevance (no weakening) — every perf-claim TOKEN references a stored reading (HIGH).** A relevant `⊢` refuses to derive a claim that doesn't *use* a premise. Model a claim as provable only if it **consumes** a reading token — there is no weakening rule to fabricate `"12x"` from nothing, so an unsubstantiated claim is *structurally* unprovable (or forced to carry `[unsubstantiated]`). Runnable in the already-installed SWI-Prolog with resources as a multiset:

```prolog
% relevance: claim/1 succeeds only by REMOVING a matching reading (premise must be used)
prove(claim(Tok), R0, R) :- select(reading(Tok), R0, R).
% there is deliberately NO clause deriving claim(_) without consuming a reading.
```
Beats a Python regex lint because the *logic itself* makes "claim without evidence" non-derivable, rather than pattern-matching after the fact.

**3. Linear logic (no contraction) — SUPERSEDES chains, liveness as a refreshable fact (HIGH/MED).** Linear `⊸` is consume-once state transition: it natively models "the prior is never rewritten — it is *spent* and a successor minted," and liveness as a token that must be re-minted (a **refuted** resource belief is consumed, not left stale):

```prolog
% supersession as a linear step: spend (provisional finding + correction), mint (retracted + confirmed)
step(supersede(S,S2), R0, [finding(S,retracted), finding(S2,confirmed)|R2]) :-
    select(finding(S,provisional), R0, R1),
    select(correction(S), R1, R2).
```
This *is* the append-only ledger semantics expressed as inference. Beats Z3 (which is non-linear: an asserted fact persists forever, so it cannot express "consumed"). MED not HIGH only because a Postgres state-machine on the ledger achieves the same effect with tooling the team already runs — linear logic is the *explanation*, SQL is the *enforcement*.

**4. Pre-registration / temporal commitment (MED).** Linear consumption gives a clean "the criterion token must exist *before* the result can spend it" — a judgment step that `select`s a pre-committed criterion enforces the temporal order without a separate clock. Forced slightly: a `committed_at < measured_at` SQL check is simpler and is what you'd ship.

**5. Rule-4 / META-SWEEP class-keyed gates (LOW).** Substructural framing doesn't help here; this is plain Datalog over schema metadata. Honest non-fit.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|---|---|---|---|---|---|---|
| **FDE / Belnap eval** (hand-rolled) | paraconsistent 4-valued status of findings | n/a (you write it) | SQL `CASE` or ~30 lines Python | none | n/a | high — plain truth tables, hard to mis-encode |
| **SWI-Prolog** (multiset resources) | relevance/linear *encoding* as forward-chaining | BSD-2 | Prolog / CLI, C, Python (janus) | already installed (9.3.31) | very high | high — clauses are readable |
| **Celf** | native CLF/linear-logic framework (consume-once rules) | GPL-ish/BSD (research) | SML; CLI | compile-from-source (SML/NJ or MLton) | low, research-grade, ~dormant | low — niche syntax, scarce training data |
| **llprover** | sequent prover, first-order linear logic | research/free | SICStus Prolog | compile + needs SICStus (non-free) | abandonware (1990s) | low |
| **linTAP** | tableau prover, MELL fragment | research/free | Prolog | compile-from-source | abandonware (1990s) | low |
| **MaGIC** | matrix generator: *check* a relevance rule doesn't validate explosion | free (ANU) | C source via ftp | compile (release 2.1, **1995**) | dormant | low — interactive, dated |

Recommendation: do *not* adopt a dedicated prover. Encode FDE in the store and relevance/linear steps in the already-installed SWI-Prolog.

## Limits & honest take

The dedicated tooling is **weak-to-abandonware**: MaGIC dates to 1995, llprover needs non-free SICStus, linTAP covers only a fragment. There is no maintained, Python-driveable relevance/linear-logic prover you'd want in CI. So the value to autoharn is **conceptual/semantic** (FDE as the paraconsistency model; linear consumption as the ledger's *meaning*) far more than "run a prover." Pitching relevance logic as an automated gate is **forced** — its insight collapses into a 30-line FDE evaluator plus discipline.

The **false-authority risk is severe and specific here**: linear logic's power *is* its bookkeeping, and that is exactly what an LLM gets wrong — silently inserting a contraction (reusing a spent token) or weakening (asserting a claim it never consumed evidence for) reproduces the very explosion/fabrication the logic was meant to forbid, while the output still looks like "a proof." A confidently wrong linear-logic encoding is *harder* to spot than a wrong SQL query because the resource accounting is invisible. Mitigation: keep encodings tiny, runnable, and asserted against concrete ledger rows — never trust an unexecuted "proof."

## References & learning

- **Belnap, "A Useful Four-Valued Logic" (1977)** — the FDE truth tables; teaches *exactly* the both/neither values autoharn's DIRTY/suspect tag needs.
- **Restall, *An Introduction to Substructural Logics* (2000)** — the clearest map of which structural rule you drop and what you get; teaches the weakening↔relevance, contraction↔linearity dial.
- **Girard, "Linear Logic" (1987)** / Wadler's "A Taste of Linear Logic" — the consume-once resource reading that models supersession; Wadler is the engineer-friendly on-ramp.
- **[MaGIC page (Slaney, ANU)](https://users.cecs.anu.edu.au/~jks/magic.html)** and **[llprover](https://cspsat.gitlab.io/llprover/)** — what the actual (dated) tooling does and its limits, so you budget realistically.

Sources: [MaGIC](https://users.cecs.anu.edu.au/~jks/magic.html), [llprover](https://cspsat.gitlab.io/llprover/), [linTAP](https://link.springer.com/chapter/10.1007/3-540-48754-9_20), [Otten provers](https://jens-otten.de/provers.html)


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
