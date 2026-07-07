# Sweep: Assurance cases (GSN) & software hazard analysis: safety-case argument structure, hazard logs, requirements traceability, MISRA process/deviation governance

## Standards cited

### GSN Community Standard v3 (SCSC Assurance Case Working Group, May 2021), plus Argevide/ACWG Assurance Case Guide
- **Clause/locus:** Core notation: Goal, Strategy, Solution, Context, Assumption, Justification, plus 'Away' elements and pattern/module extensions
- **Requires recorded:** Every node in the argument graph must be individually recorded and identifiable: (1) each Goal = an exact claim text (safety/reliability property, scoped); (2) each Strategy = the explicit inference rule used to decompose a goal into sub-goals, so the decomposition itself is auditable, not just its leaves; (3) each Solution = a pointer to a concrete, retrievable evidence artifact (test report, proof script, review record) with id/version/location; (4) each Context node = the scoping statement bounding a goal/strategy; (5) each Assumption = a first-class node distinct from context, carrying its own truth-status so a later falsification can be traced to every goal it undermined; (6) each Justification = the rationale for why a strategy or solution is believed sufficient. GSN also requires recording open/'undeveloped' goals explicitly rather than letting an incomplete branch look finished.
- **Confidence:** high

### ISO/IEC/IEEE 15026-2:2011 (updated 2022) — Systems and software assurance, Part 2: Assurance case
- **Clause/locus:** Minimum structural/content requirements for an assurance case
- **Requires recorded:** A top-level claim (or claim set) about a system property; the systematic argumentation connecting that claim through subordinate claims down to evidence; and explicit assumptions stated rather than left implicit. Requires enough recorded scope/applicability-condition/claimant information that a third-party assessor can judge sufficiency without reconstructing missing context. As a minimum-requirements standard it is the right locus for logging that an assurance case exists per safety-relevant work-product and meets these content tests, independent of which notation (GSN/CAE) instantiates it.
- **Confidence:** high

### Defence Standard 00-56 Part 1 (Issue 7, 2017) — Safety Management Requirements for Defence Systems
- **Clause/locus:** Hazard Log requirements (safety risk management / hazard identification & analysis)
- **Requires recorded:** The Hazard Log as primary traceability mechanism for the whole safety risk-management process: every identified hazard (including ones outside the contractor's direct control, still logged and notified to the Duty Holder); every mitigation and residual risk; every risk not reducible to ALARP, recorded as an explicit unresolved action feeding the Safety Plan and Safety Case Report; and a living-document update trail as the system/environment/information changes, each revision agreed with the Duty Holder.
- **Confidence:** high

### EN 50126 / EN 50128 / EN 50129 (CENELEC railway RAMS / software / signalling safety-case triad)
- **Clause/locus:** EN 50129 Safety Case structure (Quality Management Report / Safety Management Report / Technical Safety Report); hazard log; Independent Safety Assessment
- **Requires recorded:** The Safety Case is assembled from three legs, each with its own evidence trail (process compliance, hazard/risk management activity, technical safety demonstration). The Hazard Log sits under the Safety Management leg, records every hazard plus its safety-integrity treatment, and must be explicitly re-triggered (not just re-dated) on every system modification. EN 50128 requires software safety requirements individually traced through design, coding and verification with SIL-appropriate technique usage recorded. Independent Safety Assessment sign-off is a loggable artifact distinct from the developer's own V&V evidence — who assessed, against what criteria, with what residual reservations.
- **Confidence:** high

### ISO 26262:2018, Part 8 Clause 6 (Supporting processes — configuration management) and the traceability principle spanning Parts 3-6/9
- **Clause/locus:** Bidirectional traceability from hazard to safety goal to functional safety requirement to technical safety requirement to implementation to verification
- **Requires recorded:** Every link of the hazard-to-verification chain recorded as a bidirectional trace: forward (does every hazard/requirement have a satisfying downstream artifact?) and backward (does every implementation/test element trace to an originating safety requirement, no orphan code, no unimplemented requirement?). Work products individually identified, versioned and configuration-controlled so a trace link names a specific version of each end, not just a document title that can rot underneath it.
- **Confidence:** medium

### MISRA Compliance:2020 (MISRA C/C++ compliance framework)
- **Clause/locus:** Deviation records and deviation permits; guideline categorization (Mandatory/Required/Advisory)
- **Requires recorded:** Every rule violation remaining in a compliant codebase captured as a formal deviation record: the specific guideline violated; the exact code location(s) where it applies (so compliance claims are falsifiable, not aggregate assertions); the justification for acceptability in this circumstance; the authorized scope/circumstances (a deviation is not a blanket waiver); and the authorizer. Recurring pre-agreed deviations may be pooled into a 'deviation permit' agreed between supplier and acquirer, but each permit must define its use-case boundary and the per-instance documentation obligations that still apply.
- **Confidence:** high

### Case-study grounding (not a standard, but domain evidence): Maeslantkering (Rotterdam storm-surge barrier) BOS/BESW control-system formal V&V
- **Clause/locus:** Z specification + PVS theorem-proving + model checking of the storm-surge closure decision system (1990s development; 2024/25 re-verification, arXiv:2504.08518)
- **Requires recorded:** Direct evidence that civil/flood-defense life-critical software is a first-class formal-methods domain, not an aerospace footnote: the record kept was the Z specification itself, a set of 'challenge theorems' used to validate the specification against intended design decisions (validating the spec against intent, not just code against spec), the mismatches found between specification and implementation, and a 2024/25 retrospective re-verification showing the original 1990s formal artifacts remained usable/re-checkable decades later — i.e. the specification/proof record had to survive as a re-verifiable artifact across a multi-decade system lifetime.
- **Confidence:** medium

## Loggable items

- Record the exact text of every Goal/claim node in the safety argument, including its scope qualifiers -- an unscoped claim ('the system is safe') is not auditable.
- Record the Strategy (inference rule) used at every decomposition point in the argument, not only the resulting sub-goals -- reviewers must be able to judge whether the decomposition itself is valid.
- Record every Solution (evidence) node as a retrievable pointer with id/version/location, sufficient to fetch the actual artifact independent of the argument diagram.
- Record every Assumption as a distinct, separately trackable node (not folded into Context) with its own truth-status, so that if it is later falsified, every claim it supported can be re-flagged.
- Record every Justification -- the stated rationale for why a piece of evidence or a strategy is believed sufficient -- so 'why we trusted this' survives independent of the author's memory.
- Record every 'undeveloped'/open goal in the argument explicitly, rather than presenting an incomplete branch as if it were closed.
- Record, per hazard, its full lifecycle in the Hazard Log: identification event, analysis, mitigation(s) applied, residual risk, ALARP judgement, and (if unresolved) the explicit unresolved-action entry feeding the Safety Plan/Safety Case Report.
- Record every Hazard Log update as a dated revision tied to the triggering system change or new information, with the responsible authority's agreement -- a hazard log is a living document, and its update history is itself evidence.
- Record hazards discovered outside the team's direct control scope, plus the notification of them to the responsible authority -- a hazard doesn't stop being loggable because it wasn't 'yours'.
- Record bidirectional trace links (hazard -> safety goal -> requirement -> design -> code -> test) with the specific versioned identity of each linked artifact, so trace integrity can be checked without ambiguity about which document revision it points at.
- Record any orphan (untraced) implementation element or any unimplemented safety requirement surfaced by a traceability sweep -- the absence-of-trace is itself a loggable finding, not silence.
- Record every MISRA (or equivalent coding-standard) rule deviation as a formal deviation record: guideline violated, exact code locations, justification, authorized scope, and authorizer identity.
- Record Independent Safety Assessment (or equivalent independent-reviewer) sign-off separately from the developer's own verification evidence, including any residual reservations the assessor flagged but did not block on.
- For formal-methods work: record the formal specification text/version, the properties proved against it, the proof obligations discharged and by what tool/technique, and any gap between what was proved and what the natural-language safety goal actually claims.
- For long-lived life-critical software (storm-surge, rail, dams), record a retention/legibility plan for specification and proof artifacts across the system's multi-decade service life -- the Maeslantkering case shows these must remain independently re-verifiable decades after original development, not just at commissioning.

## Integrity principles

- An assurance-case node (Goal/Strategy/Solution/Context/Assumption/Justification) is worthless if it cannot be independently retrieved and re-checked -- record pointers with enough identity (id/version/location) to survive the argument diagram being redrawn.
- Assumptions are load-bearing and must be tracked as first-class, falsifiable claims, not silently folded into context prose where their failure won't propagate to the goals that depended on them.
- A hazard log is a living document: its value is in the continuous update trail tied to triggering events, not a point-in-time snapshot at delivery.
- Absence of a trace link is itself a finding to be logged, not a gap to leave silent -- orphan code and unimplemented requirements are hazards in their own right.
- A deviation from a coding/process standard is only legitimate if it is falsifiable -- named guideline, named location, named justification, named authorizer -- a vague blanket waiver is not a deviation record.
- Independent assessment evidence must be recorded separately from developer self-verification -- collapsing the two into one evidence trail erases the independence the whole safety-case structure exists to provide.
- For long-lived civil infrastructure, the formal artifacts (spec + proof) must be recorded in a form re-verifiable decades later, not just archived as a delivery artifact nobody expects to reopen.

## Formal-methods notes

The GSN/assurance-case layer is where formal verification results get consumed as 'Solution' evidence nodes -- but the standards above (15026-2 especially) insist the assurance case record the argument connecting a proof to the claim, not just cite 'proved in Coq/PVS/Z3' as a talisman. Concretely this means logging: (a) the formal specification and its version, as an artifact distinct from the proof; (b) the exact theorem statements proved, phrased so a non-specialist reviewer can map them onto the natural-language safety goal (the Maeslantkering case shows teams additionally wrote 'challenge theorems' purely to validate that the formal spec meant what the engineers intended -- this challenge-theorem record is itself a loggable assurance artifact, separate from the main proof); (c) the assumptions/environment model the proof relies on, as explicit Assumption nodes -- an unstated assumption in a formal model is exactly the kind of silent hazard the mother's-life-bar standard asks you to flag, since a proof under a false assumption gives false confidence with a veneer of rigor; (d) tool qualification/trust basis for the prover or model checker used (is the tool itself validated, or is trust placed in an unqualified tool chain -- this gap must be recorded as a Justification node, explicit about the residual trust assumption); (e) any mismatch found between formal spec and actual code/implementation (per the Maeslantkering PVS study) must be logged as a hazard-log-worthy finding even if later fixed, since 'we found and fixed a spec/code divergence' is exactly the kind of near-miss record other domains in this study call the WHY-ledger.
