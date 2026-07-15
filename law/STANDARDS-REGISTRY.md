# STANDARDS-REGISTRY — the external standards this project holds itself against

Audience: everyone (orchestrator, builders, auditors, the maintainer)

This file is the authoritative, maintainer-approved list of external standards and
frameworks this project measures itself against. It exists because of a witnessed failure
(2026-07-12, the "what-did-we-miss" RCA, recorded on the project tracker): a standard the
maintainer held the project to — NIST SP 800-53 — appeared in the project only as a word,
never as a cited source document, and five independent audit layers each inherited that
silent omission. The rule this file enforces is
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
   is exempt from documentation-decay and vestigial sweeps; the shelf the project measures
   itself against stays stable while the documentation landscape re-orients around it.

## Entries

| Standard | Entered | Basis | Operationalization status (honest, dated) |
|---|---|---|---|
| NIST SP 800-53 (Security and Privacy Controls) | 2026-07-12 | Maintainer-stated bar; the RCA's motivating omission (the AU — "Audit and Accountability" — control family, NIST's own family-letter naming, including audit-of-reads, was never enumerated by any project instrument) | NOT YET OPERATIONALIZED (2026-07-12): no brief walks its control families; first registry-rooted completeness audit pending |

## Historical source set (context, not registry entries)

The founding brief (law/briefs/safety-critical-logging/BRIEF.md) grounds in roughly 25
standards across nine domain clusters (DO-178C and its supplements, IEC 61508/62304,
ISO 26262, IEC 60880/61513, IAEA/NRC regulatory guides, 21 CFR Part 11, SEC 17a-4/FINRA,
GSN/15026-2, and others — see its §1.1–1.8). Those citations remain what they always were:
the brief's own source set. They become registry entries only when the maintainer lists
them above; until then, completeness exercises treat the brief per ADR-0000 Revisit #4
Clause 1 — as a standards-synthesizing document whose scope disclaimer, not its
bibliography, bounds what it covers.
