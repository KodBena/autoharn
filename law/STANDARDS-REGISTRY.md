# STANDARDS-REGISTRY — the external standards this project holds itself against

Audience: everyone (orchestrator, builders, auditors, the maintainer)

This file is the authoritative, maintainer-approved list of external standards and
frameworks this project measures itself against. It exists because of a witnessed failure
(2026-07-12, the "what-did-we-miss" root-cause analysis (RCA), recorded on the project
tracker — this project's decision ledger, read via the `./led` command-line tool): a
standard the maintainer held the project to — NIST SP 800-53 — appeared in the project
only as a word, never as a cited source document, and five independent audit layers (the
founding brief, its conformance map, the mechanical conformance checker, two multi-lens
review panels, and a deliberately blind completeness audit) each inherited that silent
omission. (Each layer is a distinct instrument from that RCA: the founding brief is the
research document that first synthesized the ~25 external standards; its conformance map
is a companion document walking each of the brief's claims against project artifacts; the
mechanical conformance checker is an automated script comparing citations against code;
the two multi-lens review panels were independent human/agent review passes; the
deliberately blind completeness audit was a review run without sight of the others'
findings, to avoid inheriting their blind spots — all five are named, not linked, because
the RCA record recoverable from the project tracker is their one detailed home, and this
file's job is only to name the standard they all missed, not to re-litigate the RCA.) The
rule this file enforces is
[ADR-0000 Revisit #4](adr/0000-the-alpha-and-the-omega-type-driven-design.md):
every completeness or conformance exercise enumerates FROM the entries below (each
standard's own family/clause structure, read at its authoritative source) TOWARD the
project — never from the project's existing citations outward, because that direction can
only ever confirm what already exists.

Three properties of this registry, stated so a zero-context reader cannot misread it:

1. **An entry is a measuring stick, not a conformance claim.** Listing a standard here
   means the project has NAMED it as a bar; it does not mean the project meets it. What an
   entry forecloses is silent absence: the next completeness audit must produce a
   family-by-family posture matrix (implemented / partial / named-as-excluded /
   absent-and-unnamed) for every entry.
2. **Entries may predate operationalization indefinitely.** A standard belongs here the
   moment the maintainer decides the project answers to it, even if no document, brief, or
   mechanism cites it yet — that is precisely the case corpus-rooted discovery misses.
3. **This file changes only by maintainer amendment.** It lives in law/ deliberately: law/
   is exempt from documentation-decay (the periodic staleness/relevance review most other
   docs are subject to) and vestigial sweeps (the archival relocation pass recorded in
   [VESTIGIAL-INDEX.md](../VESTIGIAL-INDEX.md)); the shelf the project measures itself
   against stays stable while the documentation landscape re-orients around it.

## Entries

Each row below names one standard, the date it entered this registry, the basis for
entering it, and its current, honestly dated operationalization status (see the three
properties above for what an entry does and does not claim).

| Standard | Entered | Basis | Operationalization status (honest, dated) |
|---|---|---|---|
| NIST SP 800-53 (Security and Privacy Controls) | 2026-07-12 | Maintainer-stated bar; the RCA's motivating omission (the AU — "Audit and Accountability" — control family, NIST's own family-letter naming, including audit-of-reads, was never enumerated by any project instrument) | NOT YET OPERATIONALIZED (2026-07-12): no brief walks its control families; first registry-rooted completeness audit pending |
| NIST SP 800-63 (Digital Identity Guidelines) | 2026-07-26 | Maintainer ratification "D2 Yes" (2026-07-26; the [DEPTH consult](../design/FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22.md) §D2 option (a), recommendation confidence high): 800-63 is already the identity layer's de-facto design vocabulary (IAL/AAL — Identity Assurance Level / Authenticator Assurance Level — grades behind the s40/s41 honesty language, i.e. this project's principal-identity kernel-lineage deltas for registered identities and their role/key/competence bindings; the vendor-ceiling IA — Identity Assurance, argued excluded because it cannot exceed what the underlying LLM vendor's own API exposes, not a project gap — exclusions) and was sweep-proof (not caught by the documentation-decay/vestigial sweeps named above) — a stick the design speaks without naming | NOT YET OPERATIONALIZED (2026-07-26): no registry-rooted audit run; the AC/IA (Access Control / Identification-and-Authentication) posture audit ([design/AUDIT-AC-IA-POSTURE-2026-07-21.md](../design/AUDIT-AC-IA-POSTURE-2026-07-21.md)) predates this entry and enumerated from 800-53 alone |

**Staged entry, recorded by the same ratification (not yet an entry):** NIST SP 800-171
enters when a research-data or defense-class adopter is concrete (the [DEPTH
consult](../design/FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22.md) §D2 option (c),
ratified as staged); until then the taint (prompt-injection provenance tracking), DMZ
(network/trust-boundary zoning), and entitlement (permission-grant) mechanisms the same
consult elaborates accrue toward it without an audit obligation ahead of any consumer who
would read the result. 21 CFR Part 11 (the FDA's Electronic Records; Electronic Signatures
rule, option (b)) awaits the maintainer's market judgment on the commercial-regulated
class — explicitly not decided by the "D2 Yes."

## Historical source set (context, not registry entries)

The founding brief ([law/briefs/safety-critical-logging/BRIEF.md](briefs/safety-critical-logging/BRIEF.md)) grounds in roughly 25
standards across nine domain clusters (DO-178C and its supplements, IEC 61508/62304,
ISO 26262, IEC 60880/61513, IAEA/NRC regulatory guides, 21 CFR Part 11, SEC 17a-4/FINRA,
GSN/15026-2, and others — see its §1.1–1.8). Those citations remain what they always were:
the brief's own source set. They become registry entries only when the maintainer lists
them above; until then, completeness exercises treat the brief per ADR-0000 Revisit #4
Clause 1 — as a standards-synthesizing document whose scope disclaimer, not its
bibliography, bounds what it covers.
