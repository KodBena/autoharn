# Sweep: Civil/Structural Engineering — Design Justification, Independent Checking, and Professional Sign-off Records

## Standards cited

### EN 1990 (Eurocode: Basis of Structural Design), Annex B — Management of Structural Reliability for Construction Works
- **Clause/locus:** Annex B, Tables B.1-B.3: Consequence Classes CC1-CC3, Design Supervision Levels DSL1-DSL3, Inspection Levels IL1-IL3
- **Requires recorded:** The consequence class assigned to the structure (linked to failure severity/exposure), the design supervision level applied (which sets who must check the design and to what depth), and the inspection level applied during execution. For CC3 (highest, e.g. large-span public structures, dams, major infrastructure) the record must show third-party/independent checking of design was performed, not merely self-check. Also requires a designer/checker competence classification.
- **Confidence:** high

### BS 5975 (Temporary Works) — Category 3 (Cat 3) Independent Check, and the analogous IStructE practice for permanent-works checking categories (Cat 1/2/3)
- **Clause/locus:** Cat 3 independent-design-review provisions
- **Requires recorded:** For high-consequence, complex, or novel designs: the identity and organisational independence of the checker (a different organisation from the designer, not just a different desk); the checker's own independently-derived load cases, calculations, and analyses (not a re-read of the designer's calc); a documented checker sign-off/certificate; and a record of which checking category (1/2/3) was assigned and why. This is the formal 'someone else redid the sums independently' evidence trail.
- **Confidence:** high

### Professional Engineer (PE) stamp/seal — US state licensing board statutes (e.g. NCEES Model Law, state Professional Engineering Acts), and equivalent chartered-engineer sign-off (UK IStructE/ICE, Eurocode 'competent person' provisions)
- **Clause/locus:** State PE Acts / NCEES Model Rules, 'responsible charge'
- **Requires recorded:** The name, license/registration number, and jurisdiction of the engineer of record who stamps/seals the calculation package; the scope of work the stamp covers (the PE is personally and legally liable only for what is under their 'responsible charge' — this scope boundary must be recorded, not assumed); date of seal; and, where a different engineer authored vs. stamped, the supervisory relationship establishing responsible charge. Stamping is a liability-transfer event and must be logged as such, distinct from mere completion of a calc.
- **Confidence:** medium

### CROSS-UK / CROSS-US (Collaborative Reporting for Safer Structures) and SCOSS (Standing Committee on Structural Safety) reporting norms
- **Clause/locus:** CROSS confidential safety-report process
- **Requires recorded:** When a hazard, near-miss, or design/checking failure is identified (including one incidentally discovered outside the scope of assigned work), the record should capture that a report was filed or a decision was made not to, and why — this is the profession's own mechanism for the 'hazard you can see, you flag loudly' obligation rather than routing around it.
- **Confidence:** medium

### Eurocodes generally (EN 1991 actions, EN 1992-1999 material codes) and AISC 360 / ASCE 7 (US equivalents) — code-compliance and design-basis documentation
- **Clause/locus:** Design-basis report conventions accompanying Eurocode/AISC submissions
- **Requires recorded:** Explicit statement of which code editions and National Annexes/amendments govern the design; the load combinations and characteristic/design values used (with source: site-specific data vs. code default); every deviation from a code default (e.g. a non-standard partial factor, an engineering-judgement override) recorded with its justification, since deviations are exactly where later failures cluster; material/component certification traceability (mill certs, product conformity) feeding the calc.
- **Confidence:** high

### Assumption Register / Design Basis Statement (standard UK/EU consulting-engineer practice, referenced in ISO 9001 §8.3 design-and-development controls as applied to engineering firms)
- **Clause/locus:** ISO 9001:2015 §8.3.3 (design inputs), §8.3.5 (design outputs), §8.3.4 (design review/verification/validation)
- **Requires recorded:** A standing, versioned assumption register separate from the calculation itself — ground conditions assumed pending site investigation, loads assumed pending final equipment specs, boundary conditions assumed for adjacent structures not yet designed — each with an owner, a closure/verification date, and the consequence if the assumption later proves false. ISO 9001 requires design review, verification, and validation be distinct recorded activities, not folded into one sign-off.
- **Confidence:** medium

### ALCOA+ data-integrity principles (originally GxP/pharma, increasingly applied to engineering QA records under ISO 9001-aligned QMS)
- **Clause/locus:** ALCOA+: Attributable, Legible, Contemporaneous, Original, Accurate, plus Complete, Consistent, Enduring, Available
- **Requires recorded:** Every calculation revision attributable to a named author and timestamped contemporaneously (not reconstructed later); original/native calc files retained (not just a PDF export) so the derivation is re-runnable; superseded calculation versions retained rather than overwritten, with the reason for revision stated. Applied here as the integrity backbone under the design-justification and checker trail, mirroring the same 'don't erase the derivation history' principle the AI-collaborator record must uphold.
- **Confidence:** low

## Loggable items

- Record the code edition and National Annex (or jurisdiction-equivalent) the design was performed to, at the moment the calculation is started — not reconstructed after the fact.
- Record the consequence/reliability class (e.g. Eurocode CC1-CC3) assigned to the structure and the design-supervision/checking level this triggers, before proceeding with the design so the required rigor is fixed up front rather than chosen retroactively to fit whatever was done.
- When a load case, material property, or boundary condition is assumed rather than measured or specified, log it to an assumption register with an owner and an explicit closure condition — do not let it live only inside a calculation's working notes where it will not be re-verified.
- When an independent check is required (per checking-category rules), record the checker's identity and organisational independence from the designer, and confirm the checker performed an independently-derived calculation rather than a review of the designer's numbers — log which of these two happened, since they are not interchangeable.
- At the point of professional sign-off (PE stamp / chartered-engineer certification), log the signer's identity, license number/jurisdiction, the explicit scope of what is being certified, and the date — because this is a liability-transfer event, not merely 'the calc is done.'
- When any code-default value, factor, or standard assumption is overridden by engineering judgement, log the override and its justification distinctly from the routine calculation — deviations from code defaults are the highest-value audit trail for later failure analysis.
- If, while doing assigned work, a hazard or defect outside the immediate task's scope is noticed (e.g. an adjacent unchecked assumption, a stale calc referenced by the current one), log that it was noticed and what was done about it (fixed, flagged, or filed as a formal safety report) — silence here is itself the failure mode this standard exists to prevent.
- Retain superseded calculation revisions rather than overwriting them, with a logged reason for each revision, so the derivation history remains reconstructible end to end.
- Record design review, verification, and validation as three distinct logged events (per ISO 9001 §8.3.4) rather than one combined 'approved' stamp, since they check different things and collapsing them hides which one was actually done.

## Formal-methods notes

Civil/structural assurance is traditionally calculation-and-independent-check based rather than machine-proof based, but the same shape maps onto formal methods directly: the calculation is the 'proof', the code clause invoked is the 'specification', the assumption register is the 'axioms/preconditions', and the independent checker's re-derivation is the 'second opinion / independent proof' (directly analogous to this project's own ADR-0014 executor-second-opinion). Where the domain now DOES use literal formal methods — e.g. finite-element model verification/validation (V&V) frameworks for major infrastructure (dams, storm-surge barriers), and increasingly rule-checking/parametric BIM compliance automation for code-compliance — the record must additionally capture: the FE model's mesh/convergence study and V&V evidence (analogous to tool-qualification evidence in DO-178C/IEC 61508), which numerical solver/version was used (tool provenance), and any model-form uncertainty carried forward as a safety factor. For fully formal civil-infrastructure control systems (e.g. storm-surge barrier closure logic, metro/railway interlocking logic embedded in a structure's operational envelope) the relevant formal-methods artifacts (B-method/Event-B models, proof obligations) belong to the adjacent software/systems-safety domain (IEC 61508/EN 50128) but the structural record must log the interface contract between the structural design-basis and that control logic (e.g. the design water level / load envelope the control system is assumed to enforce), since a mismatch there is a classic failure mode (structure over-designed for loads the control system was never proven to keep within).
