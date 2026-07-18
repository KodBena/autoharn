# ORCH-REGISTRY-COMPLETENESS-AUDIT-002 — maintainer-declared posture, recorded verbatim

<!-- doc-attest-exempt: point-in-time record (verbatim transcription of frozen ledger row 680,
checked byte-for-byte against `./led show 680`); this subagent invocation has no agent-forking
tool to run the ADR-0017 A:B:C loop -- see "Attestation posture" section below for the honest,
non-self-certifying reasoning and the named residual (a fresh-context B-read of this document's
own framing prose, not its quotes, is recommended and currently UNEXERCISED) -->

Audience: maintainer, orchestrator, and any future auditor picking up the NIST SP 800-53
registry thread.

**Status: point-in-time record, dated 2026-07-14. Never retro-edited; a later audit or a later
maintainer statement supersedes it by a new numbered document, exactly the rule
[ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md](ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md) states about
itself.** This document is 001's successor by that same rule, not an edit to it: 001 is dated
2026-07-13 and stays frozen as written. This document exists because the maintainer answered
001's family-by-family question and its seven follow-up proposals (P1–P7) in tracker row 680
(`./led show 680`, kind `commission`, 2026-07-14, "MAINTAINER EXECUTIVE RESPONSE 2026-07-14"),
and that answer needs a committed, citable home of its own — the same reasoning 001 gives for
why a registry-rooted posture matrix belongs in a document rather than only in conversation.

**What this document is not.** It is not a re-classification of the 20 families into 001's four
(now five, see below) formal classes. The maintainer's own words, read plainly, do not use that
vocabulary — he answers in his own terms, with explicit epistemic hedges, and this document's
job is to preserve those words exactly, not to translate them into IMPLEMENTED / PARTIAL /
NAMED-AS-EXCLUDED / ABSENT-AND-UNNAMED / ABSENT-AND-NAMED on his behalf. A future audit
(003+) that wants to perform that translation should do so as its own dated, attributed act —
translating a hedge into a formal class is itself a judgment call, and collapsing it here would
misattribute that judgment to the maintainer.

## Source, quoted in full context

Tracker row 680, `./led show 680`, session `main`, actor `author` (the maintainer, relayed
through the orchestrator's commission-recording convention), timestamp
2026-07-14 19:42:06.30199+02. The row's own opening line supplies its own provenance and its
own caveat about one truncated line, both preserved verbatim below rather than paraphrased:

> MAINTAINER EXECUTIVE RESPONSE 2026-07-14 (~/0714_exec_response, banked verbatim below; note
> his CA line ends mid-sentence at 'defer to orchestrator in' -- truncation preserved, not
> guessed at):

The row also carries the maintainer's own framing caveat for the whole family list, quoted
verbatim because it governs how every row below should be read — it is not this document's
editorializing, it is the source itself:

> My current posture on the enumerated control families (note: this is from my reading of the
> names, whether they're interpreted appropriately is not for me to say; I've been told family
> PL is not covered in the slightly by our makespan scheduling guarantee (or aspiration for
> said guarantee, anyway), so bear in mind that exactly every allocation/aspiration/
> classification below may be totally off):

("not covered in the slightly by" is reproduced exactly as it appears in the source row — an
apparent transcription artifact in the maintainer's own text, not corrected here per the
point-in-time rule quoting a defective passage as evidence is not itself a violation, ADR-0017
Rule 4.)

## The 20-family posture list, verbatim

One row per family, in the order the maintainer gave them (alphabetical by family code, which
matches 001's catalog order). The "Basis (001)" column is a bare pointer to 001's own family row
for a reader who wants the audit's independent classification and mechanism citations
side-by-side — it is not part of the maintainer's statement and carries no claim about how his
words map onto 001's four-class vocabulary.

| Family | Maintainer's posture (verbatim) | Basis (001) |
|---|---|---|
| AC — Access Control | `>= PARTIAL (reason: observed successful attempts by agents to circumvent access control; even if benign, it impugns the integrite of the harness)` | [001 row](ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md), classified PARTIAL |
| AT — Awareness and Training | `EPSILON (maintainer needs to be able to provision the system to it's own personal projects -- not yet achieved(!); nominally ABSENT)` | 001, classified ABSENT-AND-UNNAMED |
| AU — Audit and Accountability | `>= PARTIAL (core ("Pillar") feature of the project)` | 001, classified PARTIAL, and the full AU-1..AU-16 walk |
| CA — Assessment, Authorization, and Monitoring | `maintainer is not competent to judge; defer to orchestrator in` **(truncated in the source row at this exact word — the maintainer's sentence stops here; nothing after "in" was written. Recorded as truncated, not guessed at, per the source row's own header note quoted above.)** | 001, classified ABSENT-AND-UNNAMED |
| CM — Configuration Management | `>= PARTIAL (documented GxP with strictly positive outcome from other projects)` | 001, classified PARTIAL |
| CP — Contingency Planning | *(not given an individual family line by the maintainer — see P3/P7 below, which speak to this family's substance: backup/retention)* | 001, classified ABSENT-AND-NAMED (the class 001 proposed and P6 below accepts) |
| IA — Identification and Authentication | `>= PARTIAL (composes with AU and AC)` | 001, classified PARTIAL |
| IR — Incident Response | `>= PARTIAL (formalize the "spy" method; observability-driven development)` | 001, classified PARTIAL |
| MA — Maintenance | `my take: project is not at the level of maturity where this makes sense to address, but if it reaches maturity, could be.` | 001, classified ABSENT-AND-UNNAMED |
| MP — Media Protection | `not within scope, or perhaps better *not tractably within scope* and low ROI` | 001, classified ABSENT-AND-UNNAMED |
| PE — Physical and Environmental Protection | `same as MP` (i.e., not within scope / not tractably within scope and low ROI) | 001, classified ABSENT-AND-UNNAMED |
| PL — Planning | `apparently not applicable` | 001, classified ABSENT-AND-UNNAMED |
| PM — Program Management | `not competent to judge` | 001, classified ABSENT-AND-UNNAMED |
| PS — Personnel Security | `never applicable under any possible circumstances` | 001, classified ABSENT-AND-UNNAMED |
| PT — Personally Identifiable Information Processing and Transparency | `applicable but not within scope; aspiration explicitly rejected` | 001, classified ABSENT-AND-UNNAMED |
| RA — Risk Assessment | `may apply` | 001, classified PARTIAL |
| SA — System and Services Acquisition | `I've been told the makespan guarantee potentially falls under SA-3 (assuming it's patched up where it isn't airtight -- NOT a Fable task due to a high demotion-to-Opus likelihood)` | 001, classified PARTIAL |
| SC — System and Communications Protection | `maintainer not competent` | 001, classified PARTIAL |
| SI — System and Information Integrity | `possibly aspirational, but maintainer not competent to judge` | 001, classified PARTIAL |
| SR — Supply Chain Risk Management | `never applicable under any possible circumstances` | 001, classified ABSENT-AND-UNNAMED |

Note on CP: the maintainer's family-by-family list (AC through SR) does not include a
standalone CP line — his P3 and P7 answers (next section) speak directly to CP's substance
(backup/retention for the tracker database) without using the family code. This document does
not manufacture a CP line on his behalf; the P3/P7 quotes below are the honest record of what
he said about that territory.

## P1–P7, verbatim

These are the maintainer's answers to 001's own seven follow-up proposals (the "Follow-up
proposals from the ABSENT findings" section of 001), quoted exactly as row 680 gives them.

**A hazard flagged, not routed around:** the maintainer himself named, in this same commission
row (his "On B2" remark, quoted in
[MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md](MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md)
Part B and in row 680 itself), that bare `P<n>` labels are "pestilential" and "ripe for
confusion" across this project's documents — Part A1 of the decision brief has its own
sub-heading "A2" distinct from the brief's unrelated "Part A2", and this document's own P1–P7
list is a second instance of the identical hazard class he flagged: a reader skimming this
section without the surrounding prose could mistake these seven answers for a *different*
seven-item list elsewhere in the corpus. That confusion class is why he approved a bare-P-label
detector (`go-ahead: adr-bare-p-label-detector`, ledger row 680/683, B2) — this document does
not build that detector, but it does the cheap thing available to it now: every P-number below
is repeated with its full proposal title from 001, not left as a bare label, and the tracker
items opened in the next section carry human-readable slugs rather than "P3"/"P7" as their
names.

| # | 001's proposal title | Maintainer's answer (verbatim) |
|---|---|---|
| P1 | Scope-adjudication batch (the 10 ABSENT-AND-UNNAMED families, one sitting) | `maybe` |
| P2 | Dependency manifest (SR/SA-4/SI-2) | `we do have {python, clingo,psql (now possibly pgAudit), OR-Tools (load-bearing software)}, {Gentoo + OpenSUSE + libvirt/qemu + nvim + claude-code (development substrate)}` |
| P3 | Backup/retention decision for the tracker database (AU-11/CP) | `can upload sql-dumps to github if size permits (no pgAudit data I guess; hence, incomplete)` |
| P4 | Audit-of-reads posture decision (AU-2/AU-12 read slice, i.e. the pgAudit question) | `pgAudit provisioned, let's see where that takes us` |
| P5 | Commit the action-stream principle (PT/AU-13-adjacent) | `confirmed` |
| P6 | Registry taxonomy amendment — add ABSENT-AND-NAMED as a fifth class | `accept` |
| P7 | SSP-equivalent pointer document (PL) | `obviously needed (I thought we had this as a policy already; it's absence as a known and executed policy is organizational negligence.)` |

**A second hazard, surfaced by transcription rather than routed around:** P7's verbatim answer
("obviously needed... its absence as a known and executed policy is organizational negligence")
reads, in its own content, as an answer about **backup/retention policy** (P3's topic — "I
thought we had this as a policy already") rather than about the **SSP-equivalent pointer
document** 001's own P7 proposes. P3's verbatim answer, symmetrically, is squarely about backup
(sql-dumps to GitHub). This document does not silently resolve the mismatch by moving his words
to a different row — his words are recorded against the P-number he in fact used, per this
document's own no-editorializing rule — but it flags plainly, in the open, that P3 and P7's
*content* both land on backup/retention, and neither answer visibly addresses 001's actual P7
topic (the SSP pointer document). Read as evidence for, not against, his own point: this is a
second live specimen of the bare-P-label confusion class he named on B2, arising in the very
act of him answering the P-list. The tracker items opened below are titled by content
(`registry-audit-backup-retention-policy`, `registry-audit-sql-dumps-github-incomplete`), not by
P-number, specifically so this ambiguity cannot propagate into the tracker.

## Tracker items opened by this document

Per the commission: one item for the backup/retention policy the maintainer calls an
"organizational negligence" absence, and one for the sql-dumps-to-GitHub backup mechanism he
named as "honestly incomplete" without pgAudit data.

- `registry-audit-backup-retention-policy` — maintainer's words, verbatim: "obviously needed
  (I thought we had this as a policy already; it's absence as a known and executed policy is
  organizational negligence.)" A standing backup/retention policy for the tracker database
  (AU-11/CP territory) does not exist as a written, executed policy today; the maintainer
  judges its absence a negligence-grade gap, not a low-priority nice-to-have.
- `registry-audit-sql-dumps-github-incomplete` — maintainer's words, verbatim: "can upload
  sql-dumps to github if size permits (no pgAudit data I guess; hence, incomplete)." A concrete
  backup mechanism he is willing to use (periodic sql-dump upload to GitHub, size permitting),
  explicitly named by him as an incomplete answer because it would not carry pgAudit's read-log
  data — the audit trail's read-side would still be unbacked-up even after this mechanism
  existed.

```
$ ./led work open registry-audit-backup-retention-policy "Backup/retention policy for the tracker database (AU-11/CP) -- maintainer 2026-07-14 (ledger row 680, P7 answer): absence of a written, executed policy is organizational negligence, his word choice, not the orchestrator's"
$ ./led work open registry-audit-sql-dumps-github-incomplete "Sql-dump-to-GitHub backup mechanism (AU-11/CP, P3) -- maintainer 2026-07-14 (ledger row 680): approved if size permits, explicitly named by him as incomplete because it carries no pgAudit read-log data"
```

Witnessed output of both (this session, run against the project's own Postgres-backed tracker,
not simulated; `./led work open`'s own stdout is the psql session banner, `SET` / `SET` /
`INSERT 0 1` for each call — the human-readable `work_opened: ...` line is what the row reads
back as via `./led --recent`, reproduced below exactly as read back):

```
$ ./led work open registry-audit-backup-retention-policy "..."
SET
SET
INSERT 0 1
$ ./led work open registry-audit-sql-dumps-github-incomplete "..."
SET
SET
INSERT 0 1
$ ./led --recent 2
695|work_opened|work_opened: registry-audit-sql-dumps-github-incomplete -- Sql-dump-to-GitHub backup mechanism (AU-11/CP, P3) -- maintainer 2026-07-14 (ledger row 680): approved if size permits, explicitly named by him as incomplete because it carries no pgAudit read-log data|author||f|current
694|work_opened|work_opened: registry-audit-backup-retention-policy -- Backup/retention policy for the tracker database (AU-11/CP) -- maintainer 2026-07-14 (ledger row 680, P7 answer): absence of a written, executed policy is organizational negligence, his word choice, not the orchestrator's|author||f|current
```

Row IDs assigned: **694** (`registry-audit-backup-retention-policy`), **695**
(`registry-audit-sql-dumps-github-incomplete`).

## P6 — where the registry taxonomy amendment stands after "accept"

The maintainer's `accept` answers 001's P6 proposal directly, but P6 itself is explicit that
the registry (`law/STANDARDS-REGISTRY.md`) "changes only by maintainer amendment" and that 001
"proposes and does not edit." His `accept` is the maintainer-side half of that amendment
process — a real ratification of the *proposal* — but it is not, by itself, the edit to
`law/STANDARDS-REGISTRY.md`'s own property-1 text; that file sits under `law/`, and this
project's standing rule (CLAUDE.md: "Nobody edits kernel/lineage (frozen records), law/, or
engine/lp/ semantics without a Fable-authored, maintainer-ratified spec") means the mechanical
edit itself is not something this document performs, even with his `accept` in hand — a
Fable-authored spec carrying his ratification is the correct route for the literal text change,
consistent with how every other `law/` amendment in this project's history has landed. This
document therefore treats P6 as **accepted-in-principle, edit-to-`law/` pending its proper
route**, and uses the ABSENT-AND-NAMED label above (the CP row) as 001 already did before formal
acceptance — 001 itself used the label provisionally ("this audit marks such rows
ABSENT-AND-NAMED and proposes that refinement as a registry amendment") and his `accept` confirms
the label was the right call, without yet being the literal registry-file edit.

## Interactive follow-up still open

P1 (`maybe`) is the one answer in the P1–P7 set that is not a clean yes/no/data-point — 001's own
Part A2 write-up in the decision brief called P1 "interactive if appropriate", and the
commission row's own closing line repeats that framing: "modulo A2.P1 that is interactive if
appropriate, and I think it may be." This document does not treat `maybe` as either an approval
or a decline of the ten-family scope-adjudication sitting; it stays open, flagged here so a
future reader (or the maintainer himself) can pick the thread back up without re-deriving that
it was never closed.

## Witness summary

- WITNESSED: `./led show 680` read this session, full record reproduced above with no
  paraphrase of any quoted maintainer text; the CA-line truncation and the "not covered in the
  slightly by" transcription artifact are both reproduced exactly as the source row carries
  them, not corrected or smoothed.
- WITNESSED: [ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md](ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md)
  read in full this session for its posture-matrix structure, its P1–P7 proposal titles, and
  its own point-in-time/never-retro-edited rule, which is why this is document 002 rather than
  an edit to 001.
- WITNESSED: [law/adr/0017-the-zero-context-reader.md](../../law/adr/0017-the-zero-context-reader.md)
  read (Context through the fresh-context-audit-loop section) before authoring, to check this
  document against Rule 1's four clauses and to determine the attestation posture honestly
  (next section).
- WITNESSED: [MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md](MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md)
  read in full this session, cited above for the B2 bare-P-label context and to cross-check
  that this document's P1–P7 table titles match the same proposal titles the brief already used
  when it walked the maintainer through 001.
- WITNESSED: `./led work open` executed twice this session (rows 694, 695); both commands'
  stdout and the `./led --recent 2` read-back reproduced verbatim above, not summarized.

## Attestation posture (honest, not a rubber stamp)

This document is **doc-attest-exempt**, not because it is exempt from ADR-0017's test, but
because of two facts stated plainly rather than glossed:

1. **The subagent authoring this document has no agent-forking tool available in this
   invocation** — no Task/Agent-spawn capability was offered to this session, so the A:B:C
   fresh-context loop ADR-0017 describes as its primary transport cannot literally be run from
   inside this session. Claiming an A:B:C pass happened would be the umbrella-completion
   violation ADR-0013 and ADR-0017 both forbid; this document says instead, honestly, that it
   did not happen.
2. **The document's load-bearing content is a verbatim transcription of an already-frozen
   ledger row**, not new prose asserting new facts. The mechanical check that actually matters
   for a transcription — does the quoted text match the source byte-for-byte — was performed
   directly against `./led show 680`'s own output (reproduced inline above, not retyped from
   memory), which is a stronger check for *this specific failure mode* than a fresh-context
   prose read would be. What a fresh B-pass would still usefully check, and what this document
   cannot self-certify (ADR-0017 Rule 1's own point: the author cannot be the checker): whether
   the framing prose *around* the quotes — the hazard callouts, the P6 status paragraph, the CP
   note — reads cleanly to a reader with none of this session's context. That is recorded here
   as a residual, not hidden: **a fresh-context B read of this document's own prose (not its
   quoted material) is recommended before or alongside the next registry audit (003), and is
   currently UNEXERCISED.**

## Related

- [ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md](ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md) — the
  audit this document answers; frozen, never retro-edited.
- [MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md](MAINT-MAINTAINER-DECISION-BRIEF-2026-07-14.md)
  — the plain-words walkthrough that led to the maintainer's answer recorded here.
- [law/STANDARDS-REGISTRY.md](../../law/STANDARDS-REGISTRY.md) — the registry itself; P6's
  ABSENT-AND-NAMED class is accepted-in-principle here but not yet literally edited into this
  file (see the P6 section above).
- `./led show 680` — the source row this entire document transcribes from.

## License

Public Domain (The Unlicense).
