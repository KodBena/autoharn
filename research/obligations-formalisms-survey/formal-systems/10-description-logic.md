# 10 — Description Logic & OWL (+ temporal/probabilistic DL)

> Part of the autoharn **obligations×formalisms survey** (the obligation-organized pass). Abbreviations & tiers → **[KEY](../KEY.md)**; coined terms → root **[GLOSSARY.md](../../../GLOSSARY.md)**; index → [README](../README.md).

**Key for this document.** Full reference → [KEY.md](../KEY.md).  Guarantee-strength **5** deductive (kernel-checked) · **4** exhaustive-over-model · **3** bounded · **2** calibrated-CI · **1** defeasible.  Cost **T0** present locally · **T1** pip/jar · **T2** compile-from-source · **T3** encode into an existing host.

| code | meaning |
|---|---|
| [INV](../KEY.md#inv) | Safety-Invariant Maintenance — an "always"/barrier property holds in every reachable state; no silent excursion |
| [PROG](../KEY.md#prog) | Liveness & Real-Time Progress — required events eventually occur within deadline; no deadlock or correct-but-late action |
| [DEGRADE](../KEY.md#degrade) | Contrary-to-Duty Reparation — once already violated/faulted, enter a DEFINED safe regime — not undefined behaviour |
| [AUTH](../KEY.md#auth) | Action Authorization & Norm Precedence — every effect is gated by an explicit permission; closure + norm priority resolve deterministically |
| [COMMIT](../KEY.md#commit) | Directed Commitment & Handoff — an owed obligation has a tracked lifecycle; completes atomically or is unwound; no orphan/double handoff |
| [PROV](../KEY.md#prov) | Claim Provenance & Groundedness — every claim resolves via a finite replayable chain to primary evidence; no free-floating fact |
| [REVISE](../KEY.md#revise) | Belief Revision & Retraction — retracting a premise revisits every dependent conclusion; corrections append-only, AGM-rational |
| [CONSIST](../KEY.md#consist) | Consistency & Contradiction Containment — contradictions are quarantined; no ex-falso, no silent side-picking |
| [CALIB](../KEY.md#calib) | Substantiated & Calibrated Claims — each claim backed by a reproducible artifact at strength matched to its kind; honest confidence |
| [CLASS](../KEY.md#class) | Honest Sharp Classification — a value lands in exactly one cell of a MECE partition (or explicit "unknown"); misfit surfaced |
| [COHERE](../KEY.md#cohere) | Single-Authority / Single-Writer Coherence — one authoritative definition per fact; one owner per mutable state; references resolve to one correct target |

Description Logics are the decidable fragments of first-order logic underneath OWL: a formal vocabulary (TBox) plus assertions (ABox) over which a reasoner computes subsumption, consistency, and classification as guaranteed entailments. They are the native machinery for *honest sharp classification* and *single-authority coherence* — turning "which bucket, derived from the one shared definition" into a checkable theorem.

## Primer (becoming broadly expert)

A DL knowledge base splits into a **TBox** (concept/role axioms — `Sepsis ⊑ ∃hasOrder.Antibiotic`) and an **ABox** (individuals — `patient42 : Septic`). The decidability sweet spot OWL 2 DL targets is **SROIQ(D)** (Horrocks, Kutz, Sattler 2006): roles, nominals, inverses, qualified cardinality, datatypes. The reasoner's core services are **subsumption** (is A necessarily a B?), **consistency** (is the KB satisfiable?), **realization** (the most-specific types of an individual), and **classification** (the full subsumption lattice). The two ideas that carry the most weight for process management: (1) **open-world assumption (OWA)** — unstated facts are *unknown*, not false, the opposite of a database; and (2) **disjointness + covering axioms** — `DisjointClasses` and `EquivalentClasses(Acuity ObjectUnionOf(Tier1 … Tier5))` are what make a partition *total and mutually exclusive* so that a dual-class or a fall-through individual makes the whole KB **inconsistent** rather than silently mis-sorting. Canonical: Baader et al., *The Description Logic Handbook* (the field's spine) and the tableau-decidability results (Horrocks/Sattler). DL is built to discharge **[CLASS](../KEY.md#class)**: classification as a proved entailment, not a switch statement.

## Obligations it discharges

- **[CLASS](../KEY.md#class) — Honest Sharp Classification (primary home).** A closed vocabulary modeled with `DisjointClasses` (mutual exclusion) and an `EquivalentClasses … ObjectUnionOf` covering axiom (exhaustiveness) turns the triage failure mode into a refutation: an individual that satisfies two acuity tiers, or none, renders the ABox inconsistent and the reasoner *names the clash*. **Guarantee strength:** decidable, sound-and-complete entailment over SROIQ(D) — the misfit cannot be silently absorbed because absorbing it requires a model that provably does not exist.

- **[COHERE](../KEY.md#cohere) — Single-Authority / Single-Writer Coherence.** One TBox is the single authoritative definition every consumer *derives* from; cross-boundary drift becomes a subsumption mismatch. **Reference resolution to exactly one target** is exactly `hasKey` and `FunctionalProperty`: an `owl:hasKey(Patient (mrn ssn))` makes two records with a weak/partial key collapse or contradict, surfacing the "two patients merged on a weak key" failure as an inconsistency. **Guarantee:** strong for identity/closure under the modeled keys.

- **[PROV](../KEY.md#prov) — Claim Provenance & Groundedness (partial).** Every entailment has a **justification** (axiom pinpointing — Kalyanpur/Parsia/Sirin): a *minimal* subset of axioms that proves the conclusion, i.e., a finite inspectable derivation chain to its premises. **Guarantee:** the derived classification is replayable to admitted axioms; it does not vouch for the *primary evidence* behind those axioms.

- **[CONSIST](../KEY.md#consist) — Contradiction *detection*, not containment.** DL reasoners decide consistency exactly, so an antinomy is caught — but classical DL is **ex falso**: one clash poisons the entire ABox. It tells you *that* you are inconsistent (and, via pinpointing, *where*), but it does not keep reasoning usefully around the conflict. Quarantine is paraconsistent-DL territory (immature) — assign [CONSIST](../KEY.md#consist)'s *detection* here, its *containment* elsewhere.

**Does NOT serve:** [PROG](../KEY.md#prog), [INV](../KEY.md#inv), [DEGRADE](../KEY.md#degrade) (atemporal, non-deontic — base DL has no "always/eventually/obligation"); [COMMIT](../KEY.md#commit)/ATTR/AUTH-precedence (no directed deontic operators); [REVISE](../KEY.md#revise) (DL belief-revision exists but AGM/JTMS is a better home); [CALIB](../KEY.md#calib)/INDEP/RECORD. A frequent trap: OWA means a *missing* permission or a *missing* fact yields **no entailment** (silence), which is the wrong default for [AUTH](../KEY.md#auth) closure unless you explicitly close the world.

## A worked encoding

[CLASS](../KEY.md#class) obligation — triage acuity must be a total, exclusive partition; a novel presentation must fail loudly, not map to the nearest tier (OWL 2 functional syntax):

```
Declaration(Class(:Acuity))
EquivalentClasses(:Acuity ObjectUnionOf(:Tier1 :Tier2 :Tier3 :Tier4 :Tier5 :Unknown))  # covering: total
DisjointClasses(:Tier1 :Tier2 :Tier3 :Tier4 :Tier5 :Unknown)                            # mutually exclusive
SubClassOf(:Tier1 ObjectAllValuesFrom(:hasFinding :TimeCritical))
SubClassOf(ObjectIntersectionOf(:Presentation ObjectComplementOf(:Tier1) ... ) :Unknown) # forced fallthrough

ClassAssertion(:Presentation :case_novel)
ObjectPropertyAssertion(:hasFinding :case_novel :finding_unseen)   # matches no Tier rule
```

A reasoner realizes `case_novel : Unknown` (loud), *not* the nearest tier. Now inject the bug — assert `ClassAssertion(:Tier4 :case_novel)` while findings entail `:Tier1`: because the tiers are `DisjointClasses`, the ABox is **inconsistent**, and a justification returns the two conflicting axioms. The dual-class mis-sortation is a refuted model, not a closest-wrong bucket.

## Automation & tooling (git-clone-runnable)

**Dedicated tools exist and are mature** (WEB-VERIFIED June 2026):
- **owlready2 0.51** (LGPL-3.0-or-later, released 2026-06-22; `pip install owlready2`) — Python KB + **bundled HermiT and Pellet**; the fastest git-clone path. Not currently installed locally (`pip show owlready2` empty) but pip-installable, pure ecosystem.
- **Konclude** (LGPLv3; GitHub `konclude/Konclude`) — parallel tableau reasoner for SROIQV(D); the performance choice for large SROIQ ABoxes.
- **ELK** — OWL 2 **EL** profile, *polynomial-time* classification; use when the vocabulary fits EL (most biomedical ontologies do) for cheap CI gates.
- **ROBOT 1.9.10** (BSD-3-Clause; `ontodev/robot`, JVM — OpenJDK 25 is present locally) — the **CI harness**: `robot reason`, `robot verify` (SPARQL violation queries) give a non-zero exit on inconsistency. This is the autoharn gate.

**Encoding path where no mature solver exists — temporal/probabilistic DL.** Temporal DLs (LTL/CTL over DL, Lutz/Wolter/Zakharyaschev) and probabilistic DLs (P-SROIQ; Bayesian DL) have *no* production reasoner. Realistic plan: keep DL for the **atemporal vocabulary** and *bridge the modality to a host*. (a) **Temporal:** snapshot the ABox per tick and reason per-state with HermiT, then export the per-state classification predicates as input to **TLA+/TLC** or **clingo** to discharge the across-time [INV](../KEY.md#inv)/PROG envelope — DL supplies the state predicate, the model checker supplies "always/eventually." (b) **Probabilistic:** translate the DL T/ABox to **ProbLog or clingo+`#weight`/ASP** (the EL fragment maps cleanly to Datalog), or pair a Bayesian network (probabilities) with a DL consistency oracle (hard constraints) — Z3 can carry the datatype/cardinality side. No shrug: the DL stays the single source of vocabulary truth; the host pays for time and uncertainty.

## Honest leverage & kill-condition

**Load-bearing:** [CLASS](../KEY.md#class) and [COHERE](../KEY.md#cohere) gates, run as `robot reason && robot verify` in CI, with the teeth coming *entirely* from explicit `DisjointClasses` + covering + `hasKey` axioms. That is the real, falsifiable claim — and the trap: **without disjointness/covering, OWA gives you nothing** (the reasoner stays silent exactly where you needed a loud failure).

**Falsifiable experiment:** build golden fixtures of malformed individuals (dual-class, fall-through, weak-key collisions) plus a mutation campaign over the TBox; require that every fixture either (a) flips KB consistency or (b) changes a realized type, and that a justification localizes the cause.

**KILL CONDITION:** if, on that corpus, HermiT/Konclude produces **no observable signal beyond what a plain enum + `assert`** already yields — i.e., every catch traces to a disjointness/covering axiom a one-line code check encodes just as well, and the OWA reasoner is silent on the genuinely novel/ungrounded cases — then DL is **ash** for autoharn: pure encoding tax. It earns its keep only where the *derived* subsumption lattice (multi-axiom interactions no hand check anticipates) or `hasKey` identity closure produces a refutation a switch statement cannot. That, not classification per se, is the hypothesis on trial.

## References (edification)

- **Baader, Calvanese, McGuinness, Nardi, Patel-Schneider, *The Description Logic Handbook* (2nd ed.)** — the canonical spine; teaches TBox/ABox, tableau reasoning, and the complexity/decidability frontier.
- **Horrocks, Kutz, Sattler, "The Even More Irresistible SROIQ" (KR 2006)** — teaches exactly which constructs OWL 2 DL admits and why it stays decidable.
- **Kalyanpur, Parsia, Sirin, Hendler, "Debugging unsatisfiable classes / axiom pinpointing" (JWS 2007)** — teaches justifications: how to extract the minimal proving axiom set ([PROV](../KEY.md#prov)/groundedness).
- **owlready2 docs (Lamy)** + **ROBOT paper (Jackson et al., BMC Bioinformatics 2019)** — teach the runnable path: programmatic reasoning and CI-gated `reason`/`verify` workflows.


---
*Formal-system survey — verbatim output of the `autoharn-obligations-formalisms-survey` workflow (run `wf_2b657cd5-b06`, model claude-opus-4-8[1m]), 2026-06-27. Engine version/license claims are agent-reported (web-checked where noted) — confirm before install. Verdicts are agent-reasoned, not yet experimentally settled.*
