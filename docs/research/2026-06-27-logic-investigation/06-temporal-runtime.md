# 06 — Temporal Logic & Runtime Verification (LTL/CTL/MTL, TLA+)

> Part of the autoharn **logics & automated-deduction investigation** — see the [index](README.md); coined terms (Pillar, *_violations gate, supersession, …) are defined in the root **[GLOSSARY.md](../../../GLOSSARY.md)**.

Formalisms for stating and checking properties about how a system's state evolves *over time* — "always", "eventually", "until", "before" — either by exhaustively model-checking a spec (TLA+/TLC, NuSMV) or by monitoring an event stream against a temporal formula at runtime (Spot, MTL monitors).

## Primer

You know Z3 answers "is there *a* state satisfying φ?" Temporal logic answers a different question: "across *every reachable trajectory* of state, does the ordering invariant hold?" The two operators that matter are **□ (always / globally)** and **◇ (eventually)**, plus their pairwise cousin **U (until)** and the past-time **before**. LTL reasons over a single linear trace (one run of events); CTL branches over all possible futures; MTL adds real-time bounds ("◇≤5s"). The intuition for *when* it's the right tool: your invariant is not about one row's values but about a **relationship between events at different times** — X must be committed *before* Y, a belief once *refuted* must *never again* be read as live, a status may go provisional→confirmed but *never* confirmed→provisional silently. SQL checks the current snapshot; temporal logic checks the *shape of the history* that produced it. That ordering-over-time axis is exactly where autoharn's ledger lives.

## Applicability to autoharn

**Pre-registration (Pillar 2) — fit: HIGH.** "A criterion declared+committed BEFORE the result it judges" is a textbook past-time temporal property, not a value check. A finding event carries a timestamp/seq; the rule is: *whenever a result is promoted to `confirmed`, a matching criterion must already exist in the past.* In LTL with past operators (Spot/`ltlfilt` accepts these):

```
G (promote_confirmed -> O(criterion_registered))
```

(`O` = "once", past ◇). Plain SQL *can* express this as a `NOT EXISTS (... WHERE crit.seq < result.seq)`, but the temporal formula is the single SSOT statement of intent; the SQL is one brittle compilation of it. Beats Z3 because Z3 has no native notion of trace order — you'd hand-roll an index variable and lose the point.

**Liveness / refuted-belief supersession (Pillar 1) — fit: HIGH.** "A REFUTED resource belief must be superseded, not silently stale." This is the canonical *response/no-resurrection* pattern:

```
G (refuted(r) -> G !read_as_live(r))     # once refuted, never read live again
G (refuted(r) ->  F superseded(r))        # every refutation is eventually superseded
```

The first is a **safety** property (a Spot monitor flags the offending trace instantly when CI replays the event log); the second is **liveness**. SQL struggles to say "never again, for the rest of history" without a self-join over all later rows; the temporal monitor is O(trace) and declarative.

**Status lifecycle provisional/confirmed/retracted (cross-cutting) — fit: HIGH, and the killer app for TLA+.** Model the lifecycle as a TLA+ spec and let TLC prove no illegal transition exists across *all* interleavings:

```tla
Next == \/ status' = "confirmed"  /\ status = "provisional" /\ ~DirtyTree
        \/ status' = "retracted"  /\ status \in {"provisional","confirmed"}
Invariant == (status = "confirmed") => Committed /\ ~DirtyTree
```

That directly mechanizes "a benchmark on a DIRTY git tree must NOT be promoted to confirmed" — TLC enumerates every path and returns a *counterexample trace* if a dirty→confirmed edge is reachable. This is strictly more than a CHECK constraint: it reasons about the *protocol*, not a single insert.

**`<store>_violations` CI gates (Pillar 3) — fit: MED→HIGH.** The gates are "a query whose non-empty result fails CI." A Spot/`ltlcross`-style monitor compiled from a temporal property *is* such a gate over the event log: replay rows, monitor rejects → exit nonzero. It complements the Postgres `WITH RECURSIVE` prototype rather than replacing it; use Datalog for the supersedes-chain reachability, temporal monitors for the ordering invariants.

**Supersedes chain / non-monotonic override (Pillar 2) — fit: MED.** "Witness→Correction, prior never rewritten" is append-only-with-history. The *no-rewrite* part ("□ a finding's payload, once written, never changes") is a clean temporal safety invariant; the *chain reachability* part is better left to recursive SQL/Datalog. Honest: temporal logic is the wrong hammer for the graph walk, the right one for the immutability invariant.

**Paraconsistency / DIRTY 3rd value — fit: LOW (forced).** Temporal logics are classically two-valued; coexisting contradictory advisories without explosion is a *paraconsistent/3-valued* concern. There are multi-valued LTL variants, but reaching for them here is over-engineering versus a `suspect` enum column. Don't.

## Software to leverage

| tool | role | license | language / bindings | install cost | maturity | LLM-friendliness |
|------|------|---------|--------------------|--------------| ---------|------------------|
| **TLA+ / TLC** (tla2tools v1.8.0) | spec + exhaustive model-check of the status/ledger protocol | MIT (BSD-style) | Java jar; CLI; `tlaplus-cli` on PyPI wraps it | apt `default-jre` + one jar download | very mature (industrial: AWS, Azure) | med — verbose syntax, but lots of training data; LLMs write plausible TLA+ |
| **Spot** (v2.15.1, 2026-04) | LTL/PSL→automata, runtime **monitors**, past-time formulae | GPLv3 | C++ core, **first-class Python bindings** (Jupyter) | apt (`spot`) or pip-ish; compile if newest | mature, research-grade, actively released | high — `spot.formula`, `ltlfilt`/`ltl2tgba` CLI are scriptable from Python directly |
| **NuSMV** (v2.7.1) | symbolic CTL/LTL model checking of finite-state lifecycle | LGPL | C; CLI; no official Python (subprocess) | compile-from-source (mild) | mature/stable | med — clean SMV syntax, but driven via subprocess only |
| **nuXmv** | infinite-state (SMT) extension of NuSMV | **non-commercial binary only** | C binary; CLI | binary download | mature | low — licensing blocks CI use |
| **py-metric-temporal-logic** | MTL/real-time `◇≤Δ` monitoring of benchmark timing | MIT | pure Python | pip | small/niche | high — native Python AST |

Local check: `swipl` 9.3.31 present; none of TLC/Spot/NuSMV installed yet (`which` all miss). Cheapest path: TLA+ jar (JRE already implied) + `pip install py-metric-temporal-logic`; Spot is the heavier but highest-value add. **Avoid nuXmv** — its non-commercial license is incompatible with an open CI gate.

## Limits & honest take

The **false-authority risk is acute here**. A TLA+ spec is only as true as its `Next` relation; if an LLM mis-models the abstraction — forgets the dirty-tree guard, conflates `seq` with wall-clock — TLC will dutifully report "No error found" and hand you a *confidently wrong* proof of a property your real system violates. The model-checker verifies the model, never the system; the gap between them is unverified and invisible. **Mandate: every spec ships with at least one intentionally-broken variant that TLC must reject** — an executable sanity check the META-SWEEP can enforce. Second limit: **state explosion** — TLC is exhaustive, so a ledger spec with unbounded findings must be abstracted to a few symbolic rows or it won't terminate; this makes TLA+ a *design-time* discipline tool, not a live query over the real Postgres store. Third: temporal logic adds zero value for autoharn's *snapshot* invariants (classification discipline, "lib xor solver xor service") — that's a closed-vocabulary CHECK/Datalog job; forcing it into LTL is pure ceremony. Substance over hype: use it precisely for the *ordering* invariants (pre-registration, no-resurrection, lifecycle monotonicity) and nowhere else.

## References & learning

- **Lamport, *Specifying Systems*** (free PDF, MS Research) — the canonical TLA+ book; teaches state-machine specs + invariants from zero, exactly the status-lifecycle modeling style.
- **Hillel Wayne, *learntla.com*** — fast, practical TLA+/TLC tutorial for engineers; gets you to a running model-check in an afternoon (CLI section covers headless CI use).
- **Spot documentation, spot.lre.epita.fr** — `ltlfilt`/`ltl2tgba` and the Python API; teaches LTL-with-past and how to build a runtime monitor from a formula.
- **Baier & Katoen, *Principles of Model Checking*** — the rigorous reference for LTL vs CTL, safety vs liveness, and why the distinction matters when choosing a gate.

Sources: [tlaplus/tlaplus](https://github.com/tlaplus/tlaplus), [Spot](https://spot.lre.epita.fr/), [NuSMV 2.7.1](https://nusmv.fbk.eu/articles/271/), [nuXmv](https://nuxmv.fbk.eu/).


---
*Verbatim output of the `autoharn-logics-investigation` workflow (run `wf_6be06f87-68d`, model claude-opus-4-8[1m]), 2026-06-27 — one expert agent per logic family, grounded in autoharn. The maintainer should treat engine version/license claims as agent-reported (web-checked where noted), worth a confirm before install.*
