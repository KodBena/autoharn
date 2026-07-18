# 07 — TLA+ / TLC — Specification & Refinement

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [ATTR](../KEY.md#attr) | Agency Attribution — every change bound to an identified agent who saw-to-it and could-have-done-otherwise |
| [COMMIT](../KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

TLA+ is Leslie Lamport's specification language for concurrent and reactive systems: you write the *whole* system — and the properties it must keep — as mathematics over behaviors (infinite sequences of states), then TLC mechanically checks that every reachable behavior satisfies them. It is autoharn's engine for "this invariant holds in *every* reachable state" and "this implementation refines that contract."

## Primer (becoming broadly expert)

The core idea: a system is a *set of behaviors*, and a specification is a temporal formula `Init ∧ □[Next]_vars ∧ Fairness` that is true of exactly the allowed behaviors. The two concepts that matter. First, the **stuttering-invariant action formula** `[Next]_vars`: every step either changes `vars` per `Next` or leaves them unchanged ("stutters"). Stuttering-insensitivity is the whole trick of **refinement**: a low-level spec implements a high-level one iff every low-level behavior, viewed through a *refinement mapping*, is a high-level behavior — and the extra fine-grained steps simply look like stutters above. Implication *is* implementation; `Impl => Spec` is a theorem TLC can check. Second, **liveness via weak/strong fairness** (`WF`/`SF`), expressed in raw linear temporal logic (`□`, `◇`, `↝`), letting you state "eventually" and "infinitely often" obligations classical invariants can't.

Canonical: Lamport, *The Temporal Logic of Actions* (TOPLAS 1994) and *Specifying Systems* (2002). Abadi–Lamport, "The Existence of Refinement Mappings" (1991), is the load-bearing theorem: when a refinement mapping is guaranteed to exist (adding history/prophecy variables). TLC is an explicit-state model checker; TLAPS is the companion proof system for unbounded proofs.

Built to discharge: **[INV](../KEY.md#inv)** (safety invariants over all reachable states) and **[PROG](../KEY.md#prog)** (liveness/progress under fairness), with **refinement** as its signature move.

## Obligations it discharges

- **[INV](../KEY.md#inv) — Safety-Invariant Maintenance** (primary). TLC's bread and butter: declare `Inv` and it enumerates *every reachable state* of the finite model, halting with a concrete shortest counterexample trace at the first violation. This *exactly* matches [INV](../KEY.md#inv)'s failure mode — the transient excursion at one tick that self-heals — because TLC does not sample or average; it checks the universally-quantified `□Inv`. Guarantee strength: **exhaustive proof over the bounded model** (sound and complete relative to the chosen finite instance; not a proof for all parameter sizes — see kill-condition).

- **[PROG](../KEY.md#prog) — Liveness & Real-Time Progress.** TLC checks temporal properties (`◇`, `↝`, `□◇`) under `WF`/`SF`, finding the lasso (cycle) where a required event is starved forever. This is the right tool for deadlock/livelock/starvation freedom. Caveat: TLA+ is *untimed* — it captures logical progress and ordering, not WCET. Real-time deadlines need an explicit clock variable (or hand off to a timed-automata tool); guarantee strength for the *eventually* part is exhaustive, for the *within-deadline* part only as good as your modeled clock.

- **[DEGRADE](../KEY.md#degrade)** and **[COHERE](../KEY.md#cohere)** (secondary, via refinement). A "defined safe-state reaction" is naturally a high-level spec the implementation must refine; multi-writer coherence invariants quantified over all writers are exactly `□[Next]_vars` invariants. TLC checks both as [INV](../KEY.md#inv)/refinement.

- **[RECORD](../KEY.md#record) — Temporal Ordering** (partial). "Approval-before-action / criterion-before-result" happens-before properties are temporal formulas TLC verifies on the *model*; it cannot, of course, audit your production logs — it proves the *design* admits no out-of-order behavior.

Does **not** serve: deontic/permission obligations (**[AUTH](../KEY.md#auth)**, **[ATTR](../KEY.md#attr)**, **[COMMIT](../KEY.md#commit)** — TLA+ has no native permission/agency operators), provenance/belief-revision (**[PROV](../KEY.md#prov)**, **[REVISE](../KEY.md#revise)**), paraconsistency (**[CONSIST](../KEY.md#consist)** — TLA+ is classical), numeric calibration (**[CALIB](../KEY.md#calib)**), or independent adjudication (**[INDEP](../KEY.md#indep)** — TLC *is* a producer-side check). Assign those elsewhere; TLA+ owns "always" and "eventually" over reachable states.

## A worked encoding

[INV](../KEY.md#inv) for the dam spillway (taxonomy #1): the reservoir must never sit above crest for an undetected hour. Real TLA+:

```tla
------------------------------ MODULE Spillway ------------------------------
EXTENDS Integers
CONSTANTS Crest, MaxInflow          \* e.g. Crest = 100
VARIABLES level, gateOpen, alarmHr  \* alarmHr = consecutive hrs over crest, undetected

Init == level = 90 /\ gateOpen = FALSE /\ alarmHr = 0

Tick ==
  /\ level' = IF gateOpen THEN level - 5 + (MaxInflow %% 4)   \* release vs inflow
              ELSE level + (MaxInflow %% 4)
  /\ gateOpen' = (level >= Crest)        \* control law: open when at/over crest
  /\ alarmHr' = IF (level >= Crest) /\ ~gateOpen THEN alarmHr + 1 ELSE 0

Next == Tick
Spec == Init /\ [][Next]_<<level, gateOpen, alarmHr>> /\ WF_<<level>>(Tick)

\* INV: never an undetected hour above crest
SafetyInv == alarmHr = 0
\* PROG: if over crest, the gate eventually opens (liveness)
GateLive  == (level >= Crest) ~> gateOpen
=============================================================================
```

Run: `java -cp tla2tools.jar tlc2.TLC -config Spillway.cfg Spillway.tla`. With `INVARIANT SafetyInv` in the `.cfg`, TLC enumerates the state space; if the one-tick control law has a lag bug, it prints the exact trace `level=98 → 102 (gate still closed) → alarmHr=1`, a violation, with the shortest path from `Init`. `GateLive` (a leads-to) is checked as a `PROPERTY` under fairness — catching the livelock where inflow forever cancels release.

## Automation & tooling (the git-clone-runnable question)

**Dedicated open-source tool: YES.** **TLC**, shipped in **tla2tools.jar** from `github.com/tlaplus/tlaplus`. **License: MIT.** **Latest stable: v1.8.0 ("Clarke", May 2023)**; active development continues on `master` with nightly builds at `nightly.tlapl.us`. Maturity: **high** — 25+ years, used at Amazon (S3/DynamoDB), Microsoft, Intel; the canonical industrial formal-methods success story. Companion: **TLAPS** (theorem prover, for unbounded proofs), **Apalache** (Informal Systems, symbolic/SMT-backed bounded model checker over Z3 — Apache-2.0, relevant because it sidesteps explicit-state blowup), and **CommunityModules**.

Local readiness: **OpenJDK 25 is installed** (`java -version` → 25.0.2); TLC needs only Java 11+. autoharn's `git clone` step must vendor `tla2tools.jar` (single ~10 MB jar, no build) — verified *not* yet present locally (`find / -iname 'tla2tools*'` empty). Drop-in: `wget` the release jar into `autoharn/vendor/`, invoke headless via `tlc2.TLC`; gate the harness on exit code (non-zero = invariant/property violated) and parse the counterexample trace. For state-space blowup, route the *same* `.tla` to **Apalache** (consumes Z3, already installed at 4.16) for symbolic checking to a bounded depth. No encoding-into-a-host needed: TLA+ is itself a first-class engine.

## Honest leverage & kill-condition

**Load-bearing where:** the obligation is a genuine *temporal/concurrency* property of a finite-control protocol — interlock sequencing, handoff state machines, redundancy/voting logic, safe-state transitions. Here TLC's exhaustive enumeration plus shortest-counterexample is decisive and matches [INV](../KEY.md#inv)/PROG failure modes precisely.

**Ash where:** the real risk lives in **data-domain size** (unbounded reservoir levels, real-valued continuous dynamics, large key spaces) or in **real-time WCET**. TLC checks a *finite instance*; a clean run proves nothing about the size that ships. This is the trap: green-on-the-model laundered into green-on-the-system (a **[CALIB](../KEY.md#calib)/TRACE** false-authority failure).

**Falsifiable experiment + KILL CONDITION.** Hypothesis: *for autoharn's target obligations, TLC over a tractable finite instance finds the defects that explicit-state checking should find, within the harness time budget.* Build a mutation battery: inject N seeded faults (off-by-one in the control law, a dropped fairness condition, a refinement-mapping gap) into golden specs and require TLC to flag ≥ a pre-registered fraction with a valid trace. **KILL TLC for an obligation if** either (a) the smallest instance that *exhibits* the real defect class exceeds the harness state/time budget (state explosion makes it non-runnable in CI), **or** (b) a seeded fault that is reachable only at parameter sizes beyond the model is silently passed — i.e., the finite model is *not representative* and small-model soundness fails. Then that obligation is reassigned to Apalache (symbolic, larger bounds) or to TLAPS (unbounded proof) — not patched by enlarging the model and hoping.

## References (edification)

- **Lamport, *Specifying Systems* (2002, free PDF).** The complete TLA+/TLC manual — teaches behaviors, `[Next]_vars`, fairness, and refinement from scratch.
- **Lamport, "The Temporal Logic of Actions" (TOPLAS 1994).** The foundational paper — teaches *why* stuttering-invariance makes implication equal implementation.
- **Abadi & Lamport, "The Existence of Refinement Mappings" (1991).** Teaches the theorem that makes refinement provable, and when you must add history/prophecy variables.
- **Newcombe et al., "How Amazon Web Services Uses Formal Methods" (CACM 2015).** Teaches the industrial reality: which bugs TLC catches, and the exact state-explosion limits that set the kill-condition above.

Sources: [tlaplus/tlaplus](https://github.com/tlaplus/tlaplus), [releases](https://github.com/tlaplus/tlaplus/releases)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
