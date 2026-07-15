# 08 — Metric, Real-time & Interval Temporal Logic (MTL/STL, Allen/HS)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [TRIG](../KEY.md#trig) | Conditional Activation — a triggered duty fires exactly when (and only when) its precondition holds |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [COMMIT](../KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [STRUCT](../KEY.md#struct) | Structural Soundness by Construction — defect classes made unrepresentable (typed absence, honest signatures, fault isolation), not patched |
| [INDEP](../KEY.md#indep) | Independent Adjudication & Tool Qualification — load-bearing checks discharged by a mechanism that does NOT share the producer's bias (no LLM-judging-LLM) |
| [RECORD](../KEY.md#record) | Auditable Decision Record & Ordering — a tamper-evident trail authored at decision time; happens-before enforces criterion-before-result, approval-before-action |

Temporal logics that put numbers and intervals on "eventually": not just *that* an event follows, but *within how long*, *over which window*, and *in what ordering relation to other intervals*. This is the formal home of the deadline.

## Primer (becoming broadly expert)

Plain LTL says `□(request → ◇grant)` — grant *eventually* follows. At life-critical stakes "eventually" is a defect: a correct-but-late safety action is a failure. **Metric Temporal Logic (MTL)** (Koymans 1990) decorates modalities with real-time bounds: `□(request → ◇[0,60] grant)` — grant within 60 time units. **Signal Temporal Logic (STL)** (Maler & Ničković 2004) adds real-valued predicates over continuous signals (`level < crest`) and, crucially, a **quantitative robustness semantics** (Fainekos & Pappas 2009; Donzé & Maler 2010): a real number whose sign is the boolean verdict and whose magnitude is the *margin* — how many meters, how many seconds from violation. The headline complexity result: MTL satisfiability/model-checking is undecidable over dense time with punctual constraints (Alur–Henzinger), but the **bounded, future, non-punctual fragment** is eminently checkable, and *monitoring a concrete trace* is cheap (linear-ish). Separately, **interval logics** — Allen's 13 interval relations (1983) and the **Halpern–Shoham (HS)** modal logic of intervals (1991) — reason about *durations and their overlap* (an interlock window *during* a maintenance window; approval *meets* action) rather than instants. Full HS is undecidable; dozens of decidable fragments (NP to EXPSPACE) are mapped. Intuition: MTL/STL is built to discharge **timing**, where the failure is a missed or late deadline, not a wrong state.

## Obligations it discharges

- **[PROG](../KEY.md#prog) — Liveness & Real-Time Progress (primary, exact fit).** [PROG](../KEY.md#prog)'s failure mode is precisely "no state is wrong, but the required event never arrives or arrives too late." STL's bounded-eventually `◇[a,b]` *is* the deadline operator; robustness gives the temporal margin (seconds of slack). Guarantee strength: for a given trace, an **exact** boolean verdict plus a quantitative distance-to-violation; over a model (timed automaton), bounded-horizon **decidable** WCET/response-time guarantees. This is the one obligation the logic was invented for.
- **[TRIG](../KEY.md#trig) — Conditional Activation.** `□(trigger → ◇[0,Δ] duty)` is metric detachment with a window: the duty must activate *within* Δ of the trigger, and `□(duty → ◆[0,Δ] trigger)` (metric since) catches spurious firing. Strength: bounded-latency detachment with a robustness margin against sensor jitter.
- **[INV](../KEY.md#inv) — Safety-Invariant Maintenance, the *timed* part.** `□[t0,t1] (level < crest)` asserts the barrier holds across the whole interval it is in force, and robustness reports the worst-case approach distance. STL adds the metric "for how long / how close" that bare LTL `□` lacks. (Pure unbounded state invariants are equally well served by a model checker; STL earns its keep when the invariant has a *duration* or a *margin*.)
- **[DEGRADE](../KEY.md#degrade) — bounded fault-tolerant interval.** "Enter safe-hold within the fault-tolerant time interval" is `□(fault → ◇[0,FTTI] safe_state)` — a deadline on reparation. STL gives the FTTI a checkable, margin-bearing meaning.
- **[RECORD](../KEY.md#record) — temporal ordering (via Allen/HS).** "Approval *before* action," "criterion *before* result" are Allen `before`/`meets` constraints; metric versions bound the skew. This catches the NYSE clock-skew failure mechanically.
- **[COMMIT](../KEY.md#commit) — handoff intervals (Allen/HS, partial).** Commitment lifecycles are intervals; "no gap between two clinicians' coverage" is `meets`/`overlaps`, "no double-booking" is `disjoint`. HS expresses these natively.

**Does NOT serve:** [PROV](../KEY.md#prov), [REVISE](../KEY.md#revise), [CONSIST](../KEY.md#consist) (non-monotonic/paraconsistent territory), [AUTH](../KEY.md#auth)/ATTR (deontic/agency), [STRUCT](../KEY.md#struct), [CLASS](../KEY.md#class), [CALIB](../KEY.md#calib). Assign those elsewhere; do not stretch metric time over them.

## A worked encoding

[PROG](../KEY.md#prog) / autoharn sepsis example — antibiotic hung within 60 minutes of a sepsis flag — in **RTAMT** STL, evaluated against a trace with quantitative robustness:

```python
import rtamt
spec = rtamt.StlDiscreteTimeSpecification()
spec.declare_var('sepsis', 'float')   # >=0.5 means flag raised
spec.declare_var('abx', 'float')      # >=0.5 means antibiotic hung
# minutes; non-punctual bounded-future fragment -> decidable & monitorable
spec.spec = 'always ((sepsis >= 0.5) implies (eventually[0:60] (abx >= 0.5)))'
spec.parse()

# trace: flag at t=10, antibiotic at t=75 -> 65 min, LATE by 5
sepsis = [[t, 1.0 if t == 10 else 0.0] for t in range(0, 120)]
abx    = [[t, 1.0 if t == 75 else 0.0] for t in range(0, 120)]
rob = spec.evaluate(['sepsis', sepsis], ['abx', abx])
# rob[10] < 0  -> obligation VIOLATED at the flag instant; magnitude = minutes late
```

The negative robustness at `t=10` is the auditable artifact: not "a test failed" but "5 minutes past deadline at the sepsis instant." Move `abx` to `t=70` and robustness flips non-negative — the gate is a continuous margin, not a brittle boolean.

## Automation & tooling (the git-clone-runnable question)

**Dedicated tool exists — use it.** **RTAMT** (github.com/nickovic/rtamt) is a **BSD-licensed** Python library for offline/online STL monitoring with a C++ back-end for discrete time and dense-time support; actively maintained (RV-tool paper STTT 2020; arXiv 2501.18608, Jan 2025). It is `pip`-installable (PyPI `rtamt`); no GitHub "releases" are cut, so pin a commit SHA in autoharn's lockfile — a qualification requirement, not a nicety. **MoonLight** (github.com/MoonLightSuite/moonlight, Apache-2.0/CC-BY for docs) adds *spatio*-temporal (STREL) monitoring via Java/Python/Matlab — reach for it when geography matters (sensor mesh, dam telemetry grid). Trajectory/falsification engines **Breach** and **S-TaLiRo** are Matlab-bound; cite, don't ship.

**Monitoring vs. verification gap, and the encoding path.** RTAMT checks a *trace*; [INV](../KEY.md#inv)/PROG over *all* runs needs model checking. For bounded-horizon proof, **encode bounded MTL into SMT-Z3** (locally Z3 4.16): discretize the horizon, introduce a boolean/real per signal per tick, and unfold `◇[a,b]φ` at tick `t` into `⋁_{a≤k≤b} φ(t+k)` and `□` into a conjunction — standard bounded model checking, quantifier-free, directly dischargeable. For real-time *system* models use **timed automata** (UPPAAL, free-for-research, closed; or open `nuXmv` for RT-CTL) — but for a clean-license git-clone deliverable the **Z3 unfolding is the load-bearing path**: it stays inside an OSS engine autoharn already vendors. For **Allen/HS interval ordering** ([RECORD](../KEY.md#record)/COMMIT), encode the 13 relations as constraints over interval endpoint variables in **Z3** (linear arithmetic: `meets ≡ a.end = b.start`) or as ASP integrity constraints in **clingo 5.8** — both decidable and already installed; full-HS satisfiability is undecidable, so restrict to the endpoint-constraint (point-algebra) fragment, which is the part autoharn needs.

## Honest leverage & kill-condition

**Load-bearing:** any obligation whose failure is *a clock* — [PROG](../KEY.md#prog) deadlines, FTTI in [DEGRADE](../KEY.md#degrade), detachment latency in [TRIG](../KEY.md#trig), approval-before-action skew in [RECORD](../KEY.md#record). Robustness semantics is the rare gift here: it turns pass/fail into a *signed margin* the maintainer can threshold and trend. **Ash where:** the obligation is logical-not-temporal ([CONSIST](../KEY.md#consist), [PROV](../KEY.md#prov), [AUTH](../KEY.md#auth)); forcing time onto it produces vacuous specs. Also ash if your traces lack **trustworthy timestamps** — STL inherits clock quality, and a monitor over skewed clocks launders the very [RECORD](../KEY.md#record) failure it should catch (this couples to [INDEP](../KEY.md#indep): the timestamp source must be independent and qualified).

**Falsifiable experiment / KILL CONDITION.** Build a golden+mutant corpus of 50 timed traces for the sepsis spec (and a dam-FTTI spec), with deadline outcomes hand-labeled, plus **mutation** of the spec bounds (60→61, `[0,60]`→`[0,∞]`). Hypothesis: RTAMT robustness sign agrees with ground truth on 100% of traces, and every bound-mutant flips at least one verdict (the gate is sensitive to the number that matters). **KILL:** if any genuinely-late trace yields non-negative robustness, *or* a punctuality/bound mutation leaves all verdicts unchanged (the deadline isn't actually being checked), MTL/STL is not discharging [PROG](../KEY.md#prog) here and the assignment is withdrawn — do not paper over it with a passing aggregate.

## References (edification)

- Maler & Ničković, *Monitoring Temporal Properties of Continuous Signals* (FORMATS 2004) — the STL founding paper; teaches predicates-over-signals and the monitoring algorithm.
- Fainekos & Pappas, *Robustness of Temporal Logic Specifications* (TCS 2009) — teaches the quantitative robustness semantics that gives autoharn its *margins*.
- Ničković & Yamaguchi, *RTAMT* (ATVA/STTT 2020; arXiv [2501.18608](https://arxiv.org/html/2501.18608v1)) — teaches the runnable tool, online vs. offline, dense vs. discrete.
- Della Monica, Goranko, Montanari & Sciavicco, *Interval Temporal Logics: a Journey* (2011) — teaches the Allen/HS landscape and exactly which interval fragments stay decidable.

Sources: [RTAMT](https://github.com/nickovic/rtamt), [MoonLight](https://github.com/MoonLightSuite/MoonLight), [RTAMT arXiv 2025](https://arxiv.org/html/2501.18608v1), [HS decidable fragments](https://link.springer.com/chapter/10.1007/978-3-642-14162-1_29)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
