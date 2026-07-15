# Sweep: Functional safety standards — IEC 61508 (generic) and ISO 26262 (automotive): safety case composition, V&V records, tool qualification, competence records, and formal-methods evidence within the safety lifecycle

## Standards cited

### IEC 61508-1 through -7 (Functional Safety of E/E/PE Safety-related Systems)
- **Clause/locus:** Part 1 Clause 6 (safety management, functional safety assessment), Part 1 Annex A/B (documentation requirements), Part 3 Clause 7 (software safety lifecycle, incl. 7.4 design/development, 7.9 verification), Part 3 Annex A/B (technique tables by SIL, incl. formal methods as 'HR'/'R' at SIL3/4)
- **Requires recorded:** A full safety-lifecycle document set traceable across every phase: hazard/risk analysis results, the safety requirements specification (SRS) with allocated SIL per function, the safety plan, the validation plan and its results, design documentation showing bidirectional traceability from SRS down to code/hardware and back up through V&V evidence, verification reports at each lifecycle phase (not only final test), a functional safety assessment record (independent, with assessor competence noted), and modification/impact-analysis records for any post-release change. Where formal methods are used (semi-formal or formal specification/design per Table A.1/A.2, model checking, formal proof), the standard requires the formal notation/method used, the model, and the proof or verification result to be recorded as part of the design/verification evidence — not merely 'we used formal methods' but the artifact and its outcome.
- **Confidence:** high

### IEC 61508-3 Annex C / Table B — Software Quality: FMEDA and diagnostic coverage records
- **Clause/locus:** Part 2 Annex C (hardware), cross-referenced quantitative failure records feeding SIL claim
- **Requires recorded:** A Failure Modes, Effects and Diagnostic Analysis (FMEDA) report identifying each component's failure modes, classifying safe vs. dangerous failures, and the resulting Safe Failure Fraction (SFF) and diagnostic coverage numbers underpinning the claimed SIL — recorded as quantitative evidence, not asserted.
- **Confidence:** medium

### ISO 26262:2018 Part 2 (Management), Part 8 Clause 6 (Confirmation Reviews / measures)
- **Clause/locus:** Part 2 Clause 6 (safety management), Part 8 Clause 6 (confirmation measures: confirmation review, functional safety audit, functional safety assessment)
- **Requires recorded:** Confirmation review reports for each safety-relevant work product (safety plan, safety case, HARA, safety concepts, verification reports) stating reviewer independence level appropriate to the ASIL, the review checklist/criteria applied, findings, and disposition — recorded per work product, not as a single end-of-project sign-off. A functional safety assessment record independent of the development team, scaled to ASIL, is required before release.
- **Confidence:** high

### ISO 26262:2018 Part 3 (Concept phase — HARA) and Part 10 (Guideline)
- **Clause/locus:** Part 3 Clause 6 (Hazard Analysis and Risk Assessment), Part 3 Clause 8 (item safety goals)
- **Requires recorded:** The HARA work product: enumerated hazardous events, exposure/controllability/severity ratings and their derivation, the resulting ASIL per hazard, and the safety goals derived from each — recorded with the rationale for each rating, since ASIL assignment is later relied upon throughout the safety case as an unaudited premise if the derivation isn't captured.
- **Confidence:** high

### ISO 26262:2018 Part 8 Clause 11 (Confidence in the use of software tools) — TCL
- **Clause/locus:** Part 8 Clause 11.4 (tool classification), 11.4.6 (qualification methods 1a–1d)
- **Requires recorded:** For every software tool whose malfunction could inject or fail to detect an error in a safety-relevant work product: the Tool Impact (TI) and Tool error Detection (TD) classification with rationale, the resulting Tool Confidence Level (TCL1–3), and — for TCL2/3 — the qualification evidence per the chosen method: 1a increased-confidence-from-use (documented usage history/version and absence of safety-relevant malfunctions), 1b evaluation of the tool's development process (vendor process compliance evidence), 1c validation of the tool outputs, or 1d certification. This applies directly to any solver/prover/model-checker/compiler in a formal-methods toolchain — its qualification record is itself a required safety-case artifact, not incidental tooling.
- **Confidence:** high

### IEC 61508-1 Clause 6.2 / Annex — Competence of persons
- **Clause/locus:** Part 1 Clause 6.2 (competence of persons, organizations)
- **Requires recorded:** Documented competence records for every individual performing safety lifecycle activities (design, verification, assessment) — training, experience, and qualification appropriate to the SIL and the specific technique used (e.g., named competence in the formal method/prover employed), reviewed and kept current.
- **Confidence:** medium

### Goal Structuring Notation (GSN) — safety case argument structure (Kelly & Weaver; GSN Community Standard, Assurance Case Working Group)
- **Clause/locus:** GSN Community Standard v2/v3 — goal/strategy/evidence/context node semantics
- **Requires recorded:** The safety case itself as a structured argument: top claim (goal), the strategy decomposing it, context/assumptions attached at each node, and a Solution (evidence) node at each leaf pointing to a specific, retrievable artifact (test report, proof, review record, FMEDA, tool-qualification record). The traceable link from each leaf evidence node back to the underlying artifact is what auditors follow — an argument diagram without resolvable evidence links is not compliant evidence, it is an unsubstantiated claim graph.
- **Confidence:** medium

## Loggable items

- Record the HARA (hazard analysis and risk assessment) outcome per hazardous event — severity/exposure/controllability ratings, the derivation rationale, the resulting ASIL/SIL, and the safety goal — whenever a hazard is identified or re-assessed, not just the final number.
- Record a confirmation/independent review report against a defined checklist for every safety-relevant work product (safety plan, safety requirements spec, design, verification report, safety case) at the point that work product is baselined, capturing reviewer identity, independence level, and disposition of findings.
- When a formal method (proof assistant, model checker, B-machine/Event-B refinement, SMT solver) is used to discharge a safety requirement, record: the formal specification/model itself, the proof obligations generated, the verification/proof result (discharged/unproven/timeout), and — separately — the tool-qualification (TCL) record for the prover/solver/compiler used, since the proof's validity is conditioned on the tool's qualification.
- Record bidirectional traceability at the moment requirements, design elements, code, and test/verification evidence are linked — so 'no surplus untested code' and 'every requirement verified' can be checked mechanically rather than asserted.
- Record FMEDA-style quantitative failure data (failure mode, safe/dangerous classification, diagnostic coverage, SFF contribution) whenever a component/module's contribution to the claimed SIL is computed.
- Record competence evidence (training, experience, specific-technique qualification) for each individual performing or reviewing a safety lifecycle activity, refreshed when the activity or technique changes.
- Record every post-release/change-impact analysis — what changed, which safety case evidence nodes it invalidates, and the re-verification performed — at the moment a modification to a released safety-related item is made.
- Assemble the safety case as a GSN (or equivalent structured-argument) document with each evidence leaf resolving to a specific, retrievable artifact reference (not a narrative claim) — build/update this whenever a new evidence artifact is produced, so the argument and the evidence store never drift apart.
- Record the independent functional safety assessment (assessor identity/independence, scope, findings) as a discrete artifact prior to release at the SIL/ASIL levels where it is mandated.

## Formal-methods notes

Both standards treat formal methods as one technique within a graded 'technique and measure' framework rather than mandating a single proof style — IEC 61508-3 Annex B lists formal methods (formal specification, formal proof, model checking) as Highly Recommended (HR) or Recommended (R) depending on SIL, meaning the safety case must record which techniques were selected at each SIL, the rationale if a HR technique was NOT used (a documented deviation/compensation, per the standard's 'HR' semantics), and — where used — the actual formal model, the specification it models, the assumptions/environment model, the discharged proof obligations, and the verification result. Because these standards are technique-graded rather than proof-mandating, the auditable record must also capture the SIL/ASIL-to-technique mapping decision itself, not just the technique's output. Tool qualification (TCL under ISO 26262-8 Cl.11, or tool classification under IEC 61508-3 Cl.7.4.4 for T2/T3 tools) is a first-class, separate evidence requirement for any tool in the formal chain (prover, model checker, code generator) — a proof is not admissible safety-case evidence unless the tool that produced it has its own qualification record on file.
