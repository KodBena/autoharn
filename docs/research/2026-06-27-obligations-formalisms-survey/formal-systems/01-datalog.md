# 01 — Datalog & Deductive Databases

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Coined terms → root **[GLOSSARY.md](../../../../GLOSSARY.md)**. See the [index](../README.md).

Datalog is the function-free, fixpoint-evaluated Horn-clause core of logic programming: a database that does not merely *store* facts but *derives* their full deductive closure, with guaranteed termination and a unique least model. It is the engine that turns "what is provable from these facts and rules" into a finite, replayable artifact.

## Primer (becoming broadly expert)

Datalog is the fragment of Prolog with no function symbols and no implicit search order: every program is a set of rules `head :- body`, evaluated bottom-up to a **least fixpoint** (the minimal Herbrand model). The two concepts that matter: (1) **the least model is unique, total, and computable in polynomial time in the data** — there is exactly one set of derivable facts, independent of rule/clause order, so "what does the system believe" is a well-defined object, not an execution artifact; (2) **stratified negation and recursion** let you express transitive closure (reachability, ancestry, dependency) — the thing SQL historically could not — while keeping a declarative semantics (Apt-Blair-Walker / Van Gelder's stratification; the well-founded and stable-model semantics of Gelfond-Lifschitz extend it when strata collapse). Canonical lineage: Ullman's *Principles of Database and Knowledge-Base Systems*; Ceri-Gottlob-Tanca; Abiteboul-Hull-Vianu's *Foundations of Databases*. The intuition for *which* obligation it serves: Datalog is built for **groundedness** — every derived fact carries an implicit, finite proof tree back to base facts. It is a machine for "nothing is true unless something made it true," which is exactly PROV's failure mode.

## Obligations it discharges

- **PROV (primary).** A Datalog fact is in the model *iff* a finite derivation grounds it in EDB (base) facts. Magic-set or provenance-annotated evaluation (semiring provenance, Green-Karvounarakis-Tannen) emits the actual proof tree. This directly kills the "free-floating fact" failure mode: an ungrounded assertion is simply *not in the least model*. Guarantee strength: **exact** over the closed program — no fact survives without a replayable chain to primary evidence.
- **TRACE (primary).** Hazard→requirement→design→code→test links are a graph; coverage and change-impact closure are **transitive-closure queries**. "Is there an untraced requirement / orphan code" is a single recursive rule; "what verification must re-run after this change" is reachability over the dependency graph. Guarantee: exact graph-reachability, total and bidirectional.
- **REVISE (strong fit).** Because the model is a deterministic function of the EDB, retracting a base fact and recomputing yields the new justified set automatically — every conclusion depending on the retracted premise vanishes. Incremental/differential evaluation (DRed, differential dataflow) makes retraction-propagation *the* native operation. Guarantee: conclusions are re-derived, not stale — though Datalog gives you the recomputation, not AGM minimality or append-only history (you layer those on).
- **AUTH (closed-world fit).** Datalog's default closed-world negation makes "permitted only if a rule names it" expressible and decidable; permission closure becomes a query. Guarantee: exact under an explicitly declared closure.
- **STRUCT/COHERE (secondary).** Single-authority and reference-resolution invariants ("every reference resolves to exactly one current target") are checkable as constraints with recursive joins.

**Does NOT serve well:** PROG/INV temporal "always/eventually" over execution traces (Datalog has no native temporal modality — use TLA+/model-checking; though Datalog-over-trace-events can encode bounded checks), CONSIST contradiction-tolerance (classical Datalog has no paraconsistency — a contradiction is just two facts, and stratified negation can make conflicting rules ill-defined; ASP/well-founded semantics is the right neighbor), and DEGRADE contrary-to-duty (needs defeasible/deontic layering).

## A worked encoding

PROV obligation: *the oncology system must not recommend a dose reduction unless a supporting creatinine value grounds it.* In Soufflé syntax:

```
.decl creatinine(patient:symbol, value:float, encounter:symbol)
.decl active_encounter(patient:symbol, encounter:symbol)
.decl renal_impaired(patient:symbol)
.decl dose_reduction(patient:symbol)
.decl ungrounded_reduction(patient:symbol)   // the alarm relation

// a flag is grounded only by a current measured value
renal_impaired(p) :- creatinine(p, v, e), active_encounter(p, e), v > 1.5.
dose_reduction(p) :- renal_impaired(p).

// kill the "inherited from a superseded encounter" failure mode:
ungrounded_reduction(p) :- dose_reduction(p), !renal_impaired(p).
.output ungrounded_reduction
```

If a `dose_reduction` flag exists with no *current-encounter* creatinine grounding it (the superseded-encounter bug), it appears in `ungrounded_reduction` — a loud, mechanical PROV violation. Swap `.output` for provenance mode (`souffle --provenance=explain`) and the tool prints the derivation tree for any grounded fact, satisfying RECORD's "reconstruct the rationale."

## Automation & tooling (git-clone-runnable)

**Dedicated tool: Soufflé** — variant of Datalog that synthesizes native parallel C++. License **Universal Permissive License v1.0** (permissive, OSI-approved). Latest **2.5.0** (released March 2025); mature, industrially used (it underpins the DOOP/Gigahorse static analyzers and EVM bytecode auditing). Provides stratified negation, `--provenance` (proof-tree explanation, *exactly* the PROV/RECORD primitive), aggregates, and components. **Not installed locally** (`which souffle` → not found); installable from the UPL source/Debian package — but the survey constraint forbids installing now.

**Git-clone path without Soufflé, using what is installed:** Datalog embeds losslessly into both local engines.
- **clingo 5.8.0 (installed):** ASP is a strict superset of stratified Datalog. The worked rules run essentially verbatim as ASP; the `ungrounded_reduction` integrity check becomes a constraint `:- dose_reduction(P), not renal_impaired(P).` and clingo's stable-model semantics gives you well-founded negation *and* the CONSIST/AUTH neighbors Datalog alone lacks. This is the recommended default host for autoharn — one engine spans PROV, TRACE, AUTH.
- **SWI-Prolog 9.3.31 (installed) with `library(tabling)`:** tabled (SLG) resolution gives terminating bottom-up-equivalent Datalog with the **same least-model guarantee**, plus `library(clpfd)` and direct proof-term capture. Best when you want the derivation as a first-class Prolog term for RECORD.
- **Postgres recursive CTEs (installed):** non-recursive + linearly-recursive Datalog (the TRACE reachability queries) maps to `WITH RECURSIVE`; good when the EDB already lives in the audit database, weaker on mutual recursion and provenance.

For incremental REVISE at scale, **differential-datalog (DDlog)** is the reference design but the VMware repo is **archived**; **Nemo** (Rust, open source, existential rules) is the maintained successor for large/streaming closures. Encoding plan if you outgrow clingo: emit DDlog/Nemo rules from the same source-of-truth rule set, keeping clingo as the differential oracle (INDEP).

## Honest leverage & kill-condition

**Load-bearing:** PROV and TRACE. These are *definitionally* least-fixpoint reachability/groundedness problems; Datalog is not "a logic that can do them," it is their normal form, and the polynomial-time, order-independent, provenance-emitting evaluation is exactly the auditable-deterministic property autoharn needs. REVISE leverage is real but partial — Datalog recomputes the justified set; it does not by itself give you append-only history or AGM minimality.

**Where it is ash:** anything genuinely temporal-over-execution (INV/PROG "across the interval it is in force") or contradiction-tolerant (CONSIST). Forcing trace-temporal properties into Datalog buys you a bounded, unrolled approximation that *looks* like an "always" guarantee and is not — that is a CALIB false-authority trap.

**Falsifiable experiment / KILL CONDITION:** Build the PROV/TRACE check as Datalog in clingo *and* independently in Soufflé from one rule source; run a mutation suite that injects (a) an inherited superseded-encounter flag and (b) an orphaned requirement. **Kill condition:** if there exists a load-bearing PROV/TRACE obligation in the autoharn corpus whose violation is *not* expressible as a (stratified-negation, recursion-allowed) Datalog query — i.e., it intrinsically needs counting-to-threshold over time, real arithmetic tolerance, or contradiction-tolerance — then Datalog is mis-assigned for that obligation and the work belongs to ASP, SMT, or a temporal checker. If the two engines ever disagree on the mutated fixtures, the encoding (not the obligation) is disqualified until reconciled.

## References (edification)

- **Abiteboul, Hull, Vianu, *Foundations of Databases* (1995), ch. 12-15** — the rigorous treatment of Datalog, fixpoint semantics, and stratified negation; teaches *why* the least model is unique and tractable.
- **Soufflé documentation & "Soufflé: On Synthesis of Program Analyzers" (CAV 2016), souffle-lang.github.io** — teaches the industrial engine, components, and the `--provenance` proof-tree mechanism that is your PROV/RECORD primitive.
- **Green, Karvounarakis, Tannen, "Provenance Semirings" (PODS 2007)** — teaches how to annotate every derived fact with its grounded justification, turning Datalog evaluation into an auditable provenance ledger.
- **Ceri, Gottlob, Tanca, "What You Always Wanted to Know About Datalog (And Never Dared to Ask)" (IEEE TKDE 1989)** — the canonical accessible primer; teaches the bottom-up/magic-set evaluation intuition fast.

Sources: [souffle-lang.github.io](https://souffle-lang.github.io/), [Soufflé 2.5 release](https://souffle-lang.github.io/release-2.5.0.html), [differential-datalog (archived)](https://github.com/vmware-archive/differential-datalog), [Nemo](https://ceur-ws.org/Vol-3801/short3.pdf)


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
