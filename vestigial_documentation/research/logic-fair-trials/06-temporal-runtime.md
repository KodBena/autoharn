# 06 — Temporal Logic & Runtime Verification (LTL/CTL/MTL, TLA+) — Fair Trial (first pass)

> Part of the autoharn **logic fair-trials** (the corrected, frontier-creed pass). Coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**. The honest status of every verdict here is **undecided-until-the-experiment-runs** — see [README](README.md) and [AUDIT.md](AUDIT.md).

> **Audit verdict:** `deflated = False` · 3 defect(s) noted · **not rewritten** (the hardening pass was a no-op).
>
> ⚠️ **Mechanical re-check flags this as a possible false-negative**: the auditor marked it `deflated=false`, yet 1 of its own defects cite reducible-only / concession tells.

## Temporal Logic & Runtime Verification (LTL/CTL/MTL, TLA+) — Fair Trial

The bet: autoharn's ledger is not a snapshot but a *trace* (`audit_log`, append-only, ordered by `at, audit_id`), and its hardest invariants are about the *shape of that history* — criterion-before-result, refuted-never-resurrected, no `dirty→confirmed` edge across *any* interleaving. The wager is that temporal logic lets us PROVE properties of trajectories the system has not yet run, not merely query the ones it did.

## Maximal ambition

The frontier prize is not a better runtime monitor — it is **exhaustive proof over un-run histories**. A SQL view inspects traces that *happened*; TLC inspects every trace the *protocol can produce*, including interleavings your test data never generated. Concretely: model autoharn's status lifecycle (`provisional → confirmed → retracted`, plus supersession and the dirty-tree guard) as a TLA+ state machine, and have TLC certify that across all reachable interleavings of concurrent writers (`coordinator`, ship-hooks, a second Claude session) *no* path reaches `confirmed` on a `DirtyTree`, and *no* `refuted` resource is ever re-read as live. That is a statement about the *design of the ledger protocol*, discharged before a single offending row exists. Stack MTL on top — `◇≤Δ` — and you get real-time obligations a snapshot cannot phrase at all: "a `perf-claim` row must be substantiated within the same session window" or "every `refuted` belief is superseded within N events, not left dangling." The maximal claim: autoharn ships a machine-checked *protocol contract* for the ledger, with TLC's counterexample trace as a justification-carrying proof object, alongside live Spot monitors that replay `audit_log` and reject the first offending event in O(trace).

## The expressiveness gap (precise, not hand-wavy)

Honesty first, because the creed demands argument not assumption. **Kamp's theorem** says LTL-with-past is expressively equal to first-order logic over a linear order. autoharn's `audit_log` is exactly a finite linear order (`audit_id`). Therefore every *safety* property over the *stored* log — pre-registration, no-rewrite, no-resurrection-so-far — is, in principle, expressible as a `NOT EXISTS` self-join. For the stored-trace gates, SQL is **not** expressively beaten. This must be stated plainly.

The genuine, non-redundant gaps are three:

1. **Quantification over un-run interleavings (TLA+/TLC).** SQL can only query histories that occurred. TLC enumerates the *reachable state space of the protocol*, catching an illegal transition reachable only under a writer interleaving your real data never exhibited. This is categorically beyond any view over `audit_log` — it is verification of the *generator*, not the *output*.

2. **Succinctness.** Nested temporal operators (e.g. "every `refute` is preceded by a `witness` that was itself never `retracted` between witness and refute" — a nested `Until`) compile to a self-join chain whose size blows up; the LTL formula is one line and is the SSOT of intent.

3. **Real-time (MTL).** `◇≤5s` / within-session bounds are clumsy-to-impossible as a snapshot CHECK and native to MTL monitors.

Liveness ("eventually superseded") is real but *design-time only*: over a finite log it degrades to "not yet," so it lives in TLA+, not the gate.

## The falsifiable experiment (the trial)

**Setup.** Dump the real `audit_log` (`/home/bork/w/omega/tools/work-status/schema.sql:159-201`) to an event trace, one atomic proposition per `op`/`state` transition keyed on `row_key`.

**Encoding A — runtime safety monitor (Spot, `ltlfilt`/`ltl2tgba`, past-time):**
```
# pre-registration: no confirm without a prior matching criterion
ltl2tgba -M 'G(promote_confirmed -> O(criterion_registered))'
# no resurrection: once refuted, never read live again
ltl2tgba -M 'G(refuted -> G !read_as_live)'
```
Run the monitor (`-M`, monitor mode) over the trace; nonempty rejection ⇒ gate exits nonzero.

**Encoding B — protocol proof (TLA+/TLC, `java -jar tla2tools.jar`):**
```tla
Next == \/ /\ status = "provisional" /\ ~DirtyTree /\ Committed
           /\ status' = "confirmed"
        \/ /\ status \in {"provisional","confirmed"}
           /\ status' = "retracted"
        \/ /\ refuted /\ readLive' = FALSE          \* no-resurrection guard
Invariant == /\ (status = "confirmed") => (Committed /\ ~DirtyTree)
             /\ (refuted) => (readLive = FALSE)
```
Run with N concurrent writers modeled as interleaved `Next` steps.

**Success criterion.** (a) Monitor passes the clean real trace and rejects all injected mutations (below); (b) TLC returns "No error" on the guarded spec; (c) — the load-bearing one — TLC, on a stress model with ≥2 interleaved writers, produces a counterexample trace for an illegal transition that the existing `work_status_violations` snapshot view *does not flag*, OR the MTL monitor catches a within-window timing violation SQL cannot phrase.

**KILL CONDITION (non-negotiable).** If, on autoharn's *actual* single-writer-per-row append-only ledger, (i) every violation the Spot monitor catches is also caught by an equivalent ≤20-line SQL view, AND (ii) TLC's exhaustive check of the real lifecycle finds *zero* reachable illegal transition that a within-row CHECK constraint doesn't already block — i.e. no interleaving bug exists because the protocol is effectively sequential — then temporal logic delivers no incremental *provable* property here and is retired to design-time documentation only.

## Neutralizing false authority (verification scaffolding)

The 06 doc's "TLC proves the model, never the system" is the central research problem, made an engineering target:

- **Mutation fixtures (meta-sweep enforced).** Every spec ships ≥1 deliberately-broken variant (`Next` with the `~DirtyTree` guard deleted) that TLC *must* reject; the META-SWEEP fails CI if a spec lacks its negative twin. A green TLC with no failing mutant is treated as *unverified*.
- **Differential checkers.** Run the same `.tla` through **TLC** *and* **Apalache** (SMT-based); divergence fails. Compile the same LTL with **Spot** *and* an independent `py-metric-temporal-logic` monitor; disagreement on any trace fails.
- **Back-translation.** `spot.formula(...).to_str('utf8')` → LLM renders formula to English → maintainer diffs against the Capability-Registry (P1) statement of what the rule PROVES. The formula is not trusted until its English matches registered intent.
- **Encoding as reading-with-provenance.** The `.tla`/`.ltl` artifact is stored in the ledger with `{commit, tree, session_id}`, criterion-registered *before* its first verdict (P2).
- **Justification-carrying output.** TLC's counterexample trace is the proof object, persisted; a passing gate without a stored either-counterexample-or-coverage-report is suspect.
- **Metamorphic cross-check.** Randomly generate traces accepted by the TLA+ spec's bounded run; the Spot monitor must accept every one. Any trace TLC admits that the monitor rejects exposes an encoding mismatch, not a system bug.

## Verdict: phoenix or ash — and how we'll know

**Split, leaning phoenix-for-TLA+, undecided-for-runtime-LTL.** Kamp's theorem makes runtime LTL monitors *expressively* redundant with SQL over the stored single-writer log — their only edge there is succinctness/SSOT, which is real but modest. The phoenix case rests entirely on **un-run interleavings**: if autoharn's ledger ever has concurrent writers (two Claude sessions, ship-hook racing the coordinator), TLC proves protocol safety no view can. The single settling experiment is **Encoding B's criterion (c)**: does TLC, on the real lifecycle with ≥2 interleaved writers, surface a reachable `dirty→confirmed` or resurrection path that within-row CHECKs miss? **Yes → phoenix** (genuine non-SQL provable frontier). **No, because the protocol is provably sequential and CHECK-covered → ash for TLA+ too**, and runtime LTL collapses to "succinct SQL." What flips me to full phoenix: one MTL within-session timing obligation (perf-claim substantiation latency) that SQL cannot phrase becoming a live, mutation-tested gate.


---
*Verbatim first-pass output of the fair-trials workflow (run `wwr77eg5b`, claude-opus-4-8[1m]), 2026-06-27. The Witness — preserved un-corrected; read with the audit verdict above.*
