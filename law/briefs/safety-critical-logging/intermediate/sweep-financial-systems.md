# Sweep: Financial-systems recordkeeping & change control (SEC Rule 17a-4 WORM/audit-trail, FINRA Rule 4511, Consolidated Audit Trail, SOX 404 ITGCs, ITIL change records)

## Standards cited

### SEC Rule 17a-4 (17 CFR 240.17a-4), as amended effective 2023-01-03
- **Clause/locus:** 17a-4(f) electronic storage media; audit-trail alternative to WORM
- **Requires recorded:** Broker-dealers must preserve required records either (a) in non-rewriteable, non-erasable WORM format, or (b) under the audit-trail alternative: an electronic recordkeeping system that can recreate the original record if modified/deleted, preserving for the full retention period a complete, time-stamped audit trail capturing (1) every modification and deletion of a record or any part of it, (2) date/time of each create/modify/delete action, (3) identity of the individual performing the action, and (4) 'any other information needed to maintain an audit trail of the record.' Retention periods: 3 years (most records, e.g. order tickets, trade confirms, correspondence) or 6 years (customer account records), first 2 years readily accessible. A designated third party (D3P) must have independent access authority to the records.
- **Confidence:** high

### FINRA Rule 4511 (General Requirements — Books and Records)
- **Clause/locus:** 4511(a)-(c)
- **Requires recorded:** Firms must make and preserve books/records per FINRA rules and Exchange Act rules, in a format/media meeting SEC Rule 17a-4 (so WORM or audit-trail-alternative compliant). Default 6-year retention applies to any FINRA-mandated record lacking its own specified period. Scope explicitly includes electronic communications (email, IM, social media) as records subject to the same immutable/auditable preservation, not just transactional data.
- **Confidence:** high

### Consolidated Audit Trail (CAT) — SEC Rule 613 (17 CFR 242.613) / FINRA CAT NMS Plan
- **Clause/locus:** Rule 613; CAT Reporting Technical Specifications
- **Requires recorded:** Every order, quote, cancellation, modification, routing instruction, and execution across the full order lifecycle for NMS stocks, OTC equities, and listed options must be reported with: side, quantity, price, order type/conditions; a unique linkage ID tying related events across the order's life; the identity of the customer/account and the firm; and event timestamps at millisecond granularity or finer (exchanges increasingly required to use microsecond timestamps). Firms must also retain the underlying internal books/records used to construct each CAT-reported event so the reported data can be reconciled/reconstructed, and must report any subsequent corrections to previously submitted data.
- **Confidence:** high

### Sarbanes-Oxley Act Section 404 (management assessment of internal controls) and Section 302, operationalized via IT General Controls (ITGCs)
- **Clause/locus:** SOX Section 404(a)/(b); COSO/COBIT-aligned ITGC framework auditors test against
- **Requires recorded:** For any change to a system that processes or reports financial data (code, configuration, or infrastructure change): a documented change request with business justification; evidence of independent review/approval prior to deployment; evidence of testing distinct from development; enforced segregation of duties so no single person can author, approve, and deploy/execute the same change (or record the resulting transaction); a log of who deployed the change, when, and to what environment; and periodic (typically quarterly) access reviews showing who held privileged/production access and why. Auditors require durable, dated evidentiary artifacts (tickets, approval sign-offs, test results, access-review reports) — verbal attestations are explicitly insufficient.
- **Confidence:** medium

### ITIL 4 Change Enablement practice
- **Clause/locus:** ITIL 4 Change Enablement practice guide
- **Requires recorded:** Every change (standard/normal/emergency) is logged as a discrete Change Record from request through closure, carrying: change type/classification, risk and impact assessment, backout/rollback plan, the approving authority (CAB or delegated authority) and approval timestamp, the implementation window, post-implementation review outcome, and linkage to the underlying incident/problem/service request that motivated it. The record is retained as the immutable evidence trail an internal-controls or regulatory audit (e.g., SOX ITGC testing) draws on to demonstrate the process was actually followed, not merely defined.
- **Confidence:** medium

### ALCOA+ data-integrity principles (originally FDA/pharma, adopted cross-domain as a data-integrity vocabulary)
- **Clause/locus:** Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring, Available
- **Requires recorded:** Not a financial-sector-specific rule, but a useful adjunct vocabulary: every record must be attributable to a specific actor/system, legible over its full retention life, captured contemporaneously with the event (not backfilled), preserved as the original or a verified true copy, accurate, complete (no silent gaps), internally consistent, durable for the mandated retention period, and available on demand to regulators/auditors. Flagged low-confidence in this domain since its home is FDA 21 CFR Part 11 / GxP, not securities law — cited as an analogy, not a controlling authority here.
- **Confidence:** low

## Loggable items

- Record this when any electronic record (order, trade confirmation, correspondence, customer account record) is first created: capture creation timestamp, creating identity (person or system), and store it immutably (WORM medium or audit-trail-alternative system) per SEC 17a-4/FINRA 4511.
- Record this whenever an existing record is modified or deleted: the prior state (or enough to recreate it), the new state, date/time, and the identity of who/what performed the change — 17a-4's audit-trail alternative requires this to be reconstructible, not merely logged-and-forgotten.
- Record this for every order-lifecycle event (new order, cancel, modify, route, partial/full execution, allocation) in a live trading system: side, quantity, price, linkage ID across the order's life, and a millisecond-or-finer timestamp, per CAT/Rule 613 — and retain the internal books/records that back each reported event so it can be reconciled against what was actually reported.
- Record this when a CAT-reported event is later corrected: the correction, its timestamp, and traceability back to the original erroneous report — CAT requires visible correction history, not overwrite.
- Record this before any change is deployed to a system that processes or reports financial data: a change request with justification, independent reviewer/approver identity distinct from the author, evidence of testing performed by someone other than the deployer, and the approval timestamp — this is the segregation-of-duties evidence SOX 404 ITGC testing looks for.
- Record this at deployment time: who deployed, to which environment, when, and (for emergency changes) the retrospective approval and justification for bypassing the normal window.
- Record this on a recurring cadence (e.g., quarterly) independent of any single change: an access review listing everyone with privileged/production access and the business justification for each grant, per SOX ITGC access-control testing.
- Record this for every formal change record end-to-end (ITIL Change Enablement): classification, risk/impact assessment, backout plan, approving authority, implementation window, and post-implementation review outcome — kept as a closed, immutable record even after the change is superseded.
- Record this whenever retention-period metadata is set or changed for any record class: which rule drives the period (17a-4 default 3yr vs FINRA-4511 default 6yr vs a rule-specific period), so retention decisions are themselves auditable rather than implicit in code.
- Record this if a designated third party (D3P) or auditor is granted independent access to WORM/audit-trail records: who granted it, when, and under what authority, since 17a-4 requires this access channel to exist and be demonstrable.

## Integrity principles

- Append-only / non-destructive by construction: the system of record must make it structurally impossible (not merely policy-forbidden) to overwrite or silently delete history — this is the letter of 17a-4 WORM and the intent of its audit-trail alternative alike.
- Reconstructability over mere logging: FINRA/SEC do not just want a log line saying 'record changed' — they want enough captured (prior state + actor + timestamp) to recreate the original record on demand, which is a stronger bar than typical application audit logging.
- Segregation of duties is a structural property of the record, not a policy statement: the record must show a different identity requested, approved, tested, and deployed a change (or authorized, executed, and recorded a transaction) — a single-actor trail is itself a red flag under SOX ITGC testing.
- Correction is additive, not corrective-in-place: when CAT data or a financial record needs fixing, the fix is a new, linked event referencing the original, never an in-place edit that erases the erroneous state.
- Retention duration is a first-class, auditable fact: which rule (and its specific period) governs a given record class must itself be recorded, since 17a-4/4511 retention periods vary by record type (3yr vs 6yr vs rule-specific) and firms are expected to justify the period applied.

## Formal-methods notes

This domain's assurance model is evidentiary/procedural rather than proof-theoretic — SEC 17a-4, FINRA 4511, CAT, and SOX 404 do not ask for formal specifications or machine-checked proofs of a trading or ledger system's correctness; they ask for an immutable, reconstructible record of who-did-what-when to the system and its data. Where this project's formal-methods-first posture (type-driven design, proof obligations) intersects this domain, the natural fit is: (1) treating the WORM/audit-trail store itself as a component worth proving properties of (e.g., an Event-B or TLA+ model of the append-only log showing no update-in-place path exists, and no code path can delete without producing a linked correction event) — the proof obligation would be a safety property, 'no reachable state loses history,' amenable to model checking; (2) treating CAT/17a-4 field-completeness (every required data element present, correctly typed, correctly timestamped) as a type-driven-design opportunity — encode the CAT record schema as a type such that an incomplete or malformed report is not constructible, rather than validated after the fact; (3) SOX segregation-of-duties as a proof obligation over the authorization model (an SMT check that no principal's role permits author+approve+deploy simultaneously) rather than a manual access review. None of the four core standards researched here mandate formal proof; the formal-methods rigor would be this project's own addition on top of a domain whose baseline standard is procedural/evidentiary compliance, and that gap should be stated explicitly rather than implied as already covered by 17a-4/FINRA/SOX/CAT.
