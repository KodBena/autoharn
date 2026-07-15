# Sweep: Nuclear instrumentation & control (I&C) software — IEC 60880 / IEC 61513 / IAEA SSG-39 / NRC digital I&C V&V regime

## Standards cited

### IEC 60880:2006 (Ed. 2.0) — Software aspects for computer-based systems performing category A functions
- **Clause/locus:** Whole-standard structure: requirements specification, design, coding, verification, validation, integration, operation & maintenance phases; each phase gated by documented output
- **Requires recorded:** A complete, auditable document set per lifecycle phase: software requirements specification (traceable to system/plant requirements), software design specification, source code plus coding-standard conformance evidence, a verification record for EVERY phase (not just final V&V) showing the phase output was checked against the phase input, a validation test record demonstrating the built software meets the SRS, and configuration/change records tying any modification back through re-verification. Documents must be structured so an independent auditor — not just the original team — can reconstruct why each design/implementation decision satisfies the upstream requirement.
- **Confidence:** high

### IEC 61513:2011 (Ed. 2.0) — General requirements for I&C systems important to safety (the umbrella standard under which IEC 60880 sits)
- **Clause/locus:** Safety life-cycle framework for overall I&C architecture and individual systems; category A/B/C classification per IEC 61226
- **Requires recorded:** The safety classification rationale for every I&C function (why it is category A vs B vs C, since that classification determines which downstream standard — IEC 60880 for A, IEC 62138 for B/C — and which rigor of proof applies), the system-level architecture and its allocation of safety functions to hardware/software, and the traceability chain from plant safety requirements down through system requirements to the category-specific software standard invoked. This classification record is itself an audit artifact: a later reviewer must be able to see the classification decision, not just its consequence.
- **Confidence:** high

### IEC 62138:2018 — Software for computer-based systems performing category B or C functions
- **Clause/locus:** Lifecycle activities and software quality assurance requirements scaled to categories B/C
- **Requires recorded:** A lifecycle and QA record set proportionate to category B/C (lighter than category A/IEC 60880 but still auditable) that must support safety-case development and maintenance — i.e., the record must remain usable as safety-case evidence, not just development-team paperwork, for the life of the plant.
- **Confidence:** medium

### IAEA Safety Standards Series — SSG-39, Design of Instrumentation and Control Systems for Nuclear Power Plants (and NS-G-1.1/NS-G-1.3 predecessors it consolidates)
- **Clause/locus:** I&C design guidance; V&V planning and independence provisions
- **Requires recorded:** A verification-and-validation plan naming the team(s) performing V&V, an explicit allocation of V&V tasks across teams, and — the load-bearing requirement — a demonstration that the team(s) performing V&V are independent of the development team. Records must show traceability of every V&V activity back to the specific source document (requirement, design element, or code unit) it verifies, so independence and coverage are both auditable after the fact, not asserted.
- **Confidence:** medium

### IAEA Safety Standards Series — Software for Computer Based Systems Important to Safety (Pub1095 lineage; successor to NS-G-1.1 software guidance)
- **Clause/locus:** Software lifecycle guidance for category A/B/C systems, qualification of pre-developed/COTS software
- **Requires recorded:** For any pre-developed, COTS, or previously-qualified software item reused in a new design, a qualification record establishing that its original development process, operating history, and any modifications are adequate for the new safety application — this is the nuclear-domain analogue of provenance/pedigree tracking and must be recorded per reused component, not assumed from vendor reputation.
- **Confidence:** medium

### US NRC Regulatory Guide 1.168, Rev. 2 — endorsing IEEE Std 1012-2004/2016 (Software V&V) and IEEE Std 1028-2008 (Software Reviews and Audits)
- **Clause/locus:** V&V planning, independence, and reporting requirements; tied to 10 CFR Part 50 Appendix A (GDC 1, GDC 21) and Appendix B (Criteria II, III, XI, XVIII)
- **Requires recorded:** An IV&V plan (per IEEE 1012) recording: the V&V tasks required for the software's integrity level, the specific independence attributes achieved (technical independence, managerial independence, and — for the highest integrity levels — financial independence of the V&V organization from the developer), task-by-task results and anomaly reports, and a final V&V summary report. Every anomaly found during V&V must be logged with its disposition (fixed, deferred with justification, accepted as-is with rationale) — an anomaly log is not optional paperwork, it is the evidence that independent review actually happened rather than being asserted.
- **Confidence:** high

### IEEE Std 7-4.3.2 (endorsed by NRC RG 1.152) — Criteria for digital computers in safety systems of nuclear power generating stations
- **Clause/locus:** Software quality, V&V, and configuration management provisions specific to safety-system digital computers
- **Requires recorded:** Design-basis documentation for the digital computer/software: the design requirements, design constraints, and the record of how the design was verified against those requirements, plus configuration management records that make every deployed software version traceable to its verified/validated baseline.
- **Confidence:** medium

### NRC Regulatory Guide 1.170, Rev. 1 — Software Test Documentation for digital computer software
- **Clause/locus:** Test documentation content and structure for safety-system software
- **Requires recorded:** Test plans, test design specifications, test case specifications, test procedures, and test reports as distinct, retained artifacts — the standard requires the test record to reconstruct not just pass/fail outcomes but the rationale for test coverage (why these cases exercise the requirement set).
- **Confidence:** medium

### Formal-methods practice in the sector (B-method/Event-B, SCADE/Lustre, model-checking) as used on category-A nuclear and adjacent life-critical rail/transport systems — not a single named standard but the accepted evidentiary pattern IEC 60880 and IEC 61513 verification clauses are satisfied with when formal methods are chosen
- **Clause/locus:** IEC 60880 verification-phase requirement, discharged via formal proof instead of (or alongside) testing
- **Requires recorded:** When formal methods are the verification method for a category-A function: the formal specification itself (versioned, tied to the requirement it formalizes), the explicit list of assumptions/axioms the proof relies on (e.g., environment assumptions, hardware fault-model exclusions), the proof obligations generated by the toolchain, the discharge status of every obligation (proved / admitted-with-justification / not yet discharged), the tool-chain identity and version used to generate and check the proof (qualification of the prover itself, since an unqualified prover is an unverified verifier), and a mapping from each proof obligation back to the requirement or hazard it is meant to close. An admitted-but-undischarged obligation left silently in the record is exactly the class of hazard this domain cannot tolerate as an unflagged gap.
- **Confidence:** medium

### GSN (Goal Structuring Notation) safety cases, as used to assemble IEC 61513/IAEA evidence into an auditable argument — cross-domain practice, cited widely alongside nuclear and rail I&C assurance
- **Clause/locus:** Safety-case argument structure connecting top claim to evidence
- **Requires recorded:** The full argument tree: top-level safety claim, the strategy decomposing it into sub-claims, and for each leaf claim the specific piece of evidence (test record, proof obligation, IV&V report) that discharges it, plus any context/assumption nodes attached to a claim. Recording only the evidence artifacts without the argument that connects them to the claim is the classic partial-safety-case failure mode — the pieces exist but nobody recorded why they add up.
- **Confidence:** low

## Loggable items

- Record the safety category (A/B/C per IEC 61226) assigned to every function the code implements, and the rationale for that classification, before any design work proceeds under IEC 60880 vs IEC 62138.
- Record, for every lifecycle phase (requirements, design, code, integration, validation), a phase-verification artifact showing the output was checked against the phase's input — not just a final end-to-end V&V report.
- Record the V&V plan naming which team performs V&V and demonstrating that team's independence (technical, managerial, and where required financial) from the development team, per IAEA SSG-39 / IEEE 1012 / RG 1.168.
- Record every anomaly or discrepancy found during independent V&V with its disposition (fixed / deferred-with-justification / accepted-with-rationale) — never let an anomaly close silently without a disposition record.
- Record design-basis documentation: the explicit design requirements, design constraints, and assumptions (including environment and hardware fault-model assumptions) the software was built and verified against, per IEEE 7-4.3.2.
- Record a qualification dossier for any pre-developed, COTS, or reused software component establishing its development pedigree and operating history are adequate for this safety application (IAEA guidance on reused software).
- Record full test documentation per NRC RG 1.170: test plan, test design spec, test case spec, test procedure, and test report as separate retained artifacts, with rationale for why the case set covers the requirement set.
- When verification is discharged by formal methods rather than testing: record the formal specification (versioned, tied to its requirement), the explicit assumption/axiom list the proof depends on, every generated proof obligation and its discharge status, and the identity/version of the qualified prover tool that produced/checked the proof.
- Record configuration-management linkage from every deployed software baseline back to its verified/validated version, so no field-deployed artifact is untraceable to a completed V&V record.
- Where a safety case is assembled (GSN or equivalent), record the argument structure itself — claim, strategy, evidence mapping, and context/assumption nodes — not only the underlying evidence artifacts in isolation.

## Integrity principles

- Independence of verification from development is the load-bearing requirement, not a formality: the V&V/IV&V record must make independence demonstrable after the fact (who did the check, what organizational separation existed), not merely asserted in a plan.
- Every lifecycle phase gets its own verification record; a single end-of-project validation report is insufficient evidence under IEC 60880's phase-gated model.
- An undischarged or admitted proof obligation is a hazard, not paperwork — it must be flagged in the record with the same seriousness as a failed test, never left as a silent gap.
- Safety classification (category A/B/C) must be recorded with its rationale, since it determines which downstream standard's rigor applies — misclassification is an unrecorded, invisible failure mode.
- Reused/COTS/pre-developed software carries its own qualification burden; provenance cannot be assumed from vendor reputation and must be recorded per component.

## Formal-methods notes

This domain's formal-methods assurance (chiefly via B-method/Event-B and SCADE/Lustre-style model-based tooling, or model checking) is used to discharge IEC 60880's/IEC 61513's verification-phase requirements for category-A functions. The auditable record must go beyond "we used formal methods" and capture: (1) the versioned formal specification tied explicitly to the requirement it formalizes; (2) the complete assumption/axiom set the proof relies on (environment behavior, hardware fault-model exclusions, timing assumptions) — since an unstated assumption is an unverified gap dressed as a closed proof; (3) every proof obligation generated by the toolchain together with its discharge status (proved, admitted with explicit justification, or open); (4) tool qualification evidence for the prover/checker itself — an unqualified verification tool is an unverified verifier, and IEC 60880's spirit (auditable documents, verification of each phase) extends to the tool that did the verifying; and (5) an explicit map from proof obligations back to the requirements/hazards they close, ideally assembled into a GSN-style safety-case argument so a reviewer can trace top-level safety claims down to specific discharged obligations rather than being handed a pile of disconnected proof artifacts.
