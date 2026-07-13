# ORCH-REGISTRY-COMPLETENESS-AUDIT-001 — first registry-rooted completeness audit: NIST SP 800-53

Audience: maintainer (and the orchestrator relaying to him)

**Status: point-in-time audit record, dated 2026-07-13. Never retro-edited; a later audit
supersedes it by a new numbered document, which is why this one is numbered 001.**
Commissioned as tracker work item `registry-completeness-audit` (`./led show 249` prints the
commission; "the tracker" means autoharn's append-only Postgres decision ledger, read via the
`./led` verb). The rule this audit is the first exercise of is
[ADR-0000 Revisit #4](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
("Revisit #4 — 2026-07-12"), which requires every completeness exercise to enumerate FROM each
entry in [law/STANDARDS-REGISTRY.md](../law/STANDARDS-REGISTRY.md) — the standard's own
family/clause structure, read at its authoritative source — TOWARD the project, never from the
project's existing citations outward. The registry has one entry: NIST SP 800-53 (Security and
Privacy Controls), status NOT YET OPERATIONALIZED. This document is the family-by-family
posture matrix that entry's registry property 1 demands, plus the follow-up list its
ABSENT-AND-UNNAMED findings generate.

Scope disclaimer, mandatory under ADR-0000 Revisit #4 Clause 1: this audit classifies at the
**family** level (all 20 families, none skipped), with control-level enumeration inside the
families that plausibly intersect a governance harness (AU in full; AC, CM, IR, SI, SA at the
named-control level). It deliberately does NOT walk every one of the catalog's controls and
enhancements inside the remaining 14 families — a family classified ABSENT-AND-UNNAMED below is
absent wholesale, so its per-control walk would produce the same verdict N times. What this
audit therefore cannot claim: that no single control inside a PARTIAL family beyond those
named was silently missed. The next audit in this series (002+) narrows per the maintainer's
priorities. This audit also does not assess the ~25 standards in the registry's "historical
source set" — they are not registry entries, per the registry's own text.

## Method and sources (what was fetched, exactly)

Per the commission (row 249) and the OSCAL implementation note (tracker row 248), the control
checklist was generated from NIST's machine-readable OSCAL catalog — OSCAL is the Open
Security Controls Assessment Language, NIST's machine-readable format for publishing control
catalogs as structured JSON/XML (<https://pages.nist.gov/OSCAL/>) — not scraped from PDF prose
or recalled from training knowledge. What was fetched and verified on 2026-07-13:

- **The OSCAL catalog itself, downloaded and parsed** (not summarized through a fetch tool):
  <https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json>
  (10.4 MB JSON). Its metadata reads: title "Electronic (OSCAL) Version of NIST SP 800-53
  Rev 5.2.0 Controls and SP 800-53A Rev 5.2.0 Assessment Procedures", version **5.2.0**. Its
  `groups` array contains exactly **20** family groups; the family IDs and titles in the
  matrix below are printed verbatim from that array by a local `json` parse. Control counts
  per family and every control ID/title cited below come from the same parse. (Note the
  catalog is Rev 5.2.0 — NIST's current maintained revision of SP 800-53 Release 5; the
  registry entry says "NIST SP 800-53" without pinning a point release, so the current
  catalog is the honest reading of "its authoritative source".)
- **Cross-check of the 20-family list** against secondary sources via web search (NIST CSRC's
  Rev 5 publication page <https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final> among the
  results): agrees — 20 families, AC through SR, PT and SR being Rev 5's additions.

Repository-side grounding: every IMPLEMENTED/PARTIAL claim below names a real file that was
read (not a self-description trusted at face value). The repo-mapping pass was executed by a
subagent instructed to read each cited file and report skeptically; the audit author then
spot-verified the load-bearing citations (file existence, the `bork|f|t` superuser probe quote
in the regulator assessment, the absence of any dependency manifest, the
`hooks/pretooluse_read_observer.py` docstring) directly.

One prior in-repo document overlaps this territory and is cited rather than duplicated:
[design/MAINT-REGULATOR-ADOPTION-ASSESSMENT.md](MAINT-REGULATOR-ADOPTION-ASSESSMENT.md)
(2026-07-12) ran a regulator-lens gap assessment and returned "not-yet" for a NIST lens, with
live-verified findings (passwordless network superuser, TLS off, no backup, no dependency
manifest) that several rows below rest on. That document is corpus-rooted and advisory; this
one is registry-rooted and is the audit the registry entry names as pending.

## The four classes, and one honest refinement this audit had to make

The registry's property 1 names four classes: IMPLEMENTED, PARTIAL, NAMED-AS-EXCLUDED,
ABSENT-AND-UNNAMED. Walking the families exposed a real state the four classes cannot express:
a family where **nothing is implemented, no exclusion was ever ruled, but the gap IS named in a
project document** (example: Contingency Planning — no backup exists, and
the regulator assessment's Gap 2, linked below, says so plainly). That is not ABSENT-AND-UNNAMED
(the absence is on the record) and not NAMED-AS-EXCLUDED (nobody decided it is out of scope; it
is an acknowledged hole). This audit marks such rows **ABSENT-AND-NAMED** and proposes that
refinement as a registry amendment (proposal P6 below — the registry is maintainer-amendment-
only per its property 3, so this document proposes and does not edit). For headline-count
purposes ABSENT-AND-NAMED rows are counted with ABSENT-AND-UNNAMED (both mean "no mechanism"),
and the split is shown separately.

## The posture matrix — all 20 families

The table below has one row per NIST SP 800-53 Rev 5.2.0 control family, in the catalog's own
order. The first column is the family's two-letter OSCAL group ID and title, verbatim from the
catalog; "Controls" is the number of base controls in that family's catalog group (enhancements
not counted); "Classification" is one of the classes defined above; "Basis" names the
mechanism/file or the search that came up empty. One house term recurs in the Basis cells:
"seen-red" is this repository's convention (directory `seen-red/`, enforced by
`gates/fixture_census.py`) that every gate ships with a fixture proving it can FAIL — a gate
never witnessed red is a claim, not a check. Detail paragraphs for the six walked families
follow the table.

| Control family (NIST SP 800-53 Rev 5.2.0 group ID and title) | Controls | Classification | Basis (mechanism + witness, or the empty search) |
|---|---|---|---|
| AC — Access Control | 25 | PARTIAL | Real least-privilege grants in kernel SQL (`kernel/lineage/s18-criterion-principals.sql` column-scoped grants; `s17-stamp-mechanism.sql` secret-isolation via SECURITY DEFINER); role split provisioned by `bootstrap/freeze-at-stamp.sh`. Hole at the top: operating role `bork` is a passwordless network-reachable Postgres superuser (live-verified in the regulator assessment, linked above, `bork|f|t`); fix prepared-unapplied in `design/MAINT-PG-HBA-HARDENING.md`. |
| AT — Awareness and Training | 6 | ABSENT-AND-UNNAMED | No training/awareness artifact; grep found only unrelated uses of "training". |
| AU — Audit and Accountability | 16 | PARTIAL | Write-side audit is strong (s26/s27 hash chain + high-water witness); **audit-of-reads is a distinct line and is ABSENT at the database layer** — see the AU walk below, which is this audit's pre-registered success criterion. |
| CA — Assessment, Authorization, and Monitoring | 9 | ABSENT-AND-UNNAMED | No formal assessment/authorization/continuous-monitoring program; the seen-red/gate corpus (the "seen-red" convention is defined in the prose above this table) is mechanical self-checking, not a CA-style process. (This audit series itself, once recurring per the registry, would become the closest CA-shaped practice — noted, not claimed.) |
| CM — Configuration Management | 14 | PARTIAL | CM-8 inventory: `gates/layout_census.py` + `gates/fixture_census.py`; CM-3 change control: `hooks/pretooluse_change_gate.py` (edit refused unless a ticket declares the file); CM-6 partial: `gates/apparatus_unknown_keys.py` (harness config only). Gaps: no tool-version pinning of hooks against settled evidence (regulator assessment Gap 3), no host/Postgres configuration baseline. |
| CP — Contingency Planning | 13 | ABSENT-AND-NAMED | No backup, replication, retention, or disaster-recovery story for the single Postgres instance — stated plainly as Gap 2 in the regulator assessment (linked above the table). Named as a gap, never ruled out of scope. |
| IA — Identification and Authentication | 13 | PARTIAL | Internal write-attribution is real: the stamp mechanism (`kernel/lineage/s17-stamp-mechanism.sql`, `hooks/stamp_intercept.py`) binds ledger rows to agent invocations via HMAC. DB/OS-level authentication is the AC hole above (passwordless superuser; the regulator doc's own words: "a tripwire, not authentication"). |
| IR — Incident Response | 10 | PARTIAL | A live RCA-on-discovery discipline, witnessed repeatedly: the what-did-we-miss RCA (2026-07-12) produced ADR-0000 Revisit #4 + the standards registry; individual incidents drove named gates (`gates/no_conflict_markers.py`, `gates/staging_guard.py` each cite their motivating incident in their docstring); `design/USER-RETROSPECTIVE-RECIPE.md` formalizes retrospectives. No IR-8-style standing incident-response plan document exists. |
| MA — Maintenance | 7 | ABSENT-AND-UNNAMED | No maintenance-window/patch-management artifact found. |
| MP — Media Protection | 8 | ABSENT-AND-UNNAMED | No media-sanitization/removable-media artifact found. |
| PE — Physical and Environmental Protection | 23 | ABSENT-AND-UNNAMED | No physical-security artifact. Single-host tool on the maintainer's own machine — plausibly out of scope, but no ruling says so (see the perimeter note below the table). |
| PL — Planning | 11 | ABSENT-AND-UNNAMED | No system security plan (SSP) or equivalent. CLAUDE.md/ORCH-CAPABILITIES.md are operating doctrine, not a security plan; classifying them as PL coverage would be inflation. |
| PM — Program Management | 32 | ABSENT-AND-UNNAMED | No organizational security-program artifact; PM's premise (an organization-wide program) barely applies to a single-maintainer project, but that judgment is nowhere recorded. |
| PS — Personnel Security | 9 | ABSENT-AND-UNNAMED | No personnel-security artifact; single-operator project, same unrecorded-judgment caveat as PM. |
| PT — Personally Identifiable Information Processing and Transparency | 8 | ABSENT-AND-UNNAMED | No PII inventory or transparency artifact. Adjacent practice exists — the 2026-07-09 ephemera ruling in CLAUDE.md (transcripts are private, never committed, after the 2026-07-07 privacy incidents) is a real data-minimization decision — but it is one ruling about one surface, not PT coverage. |
| RA — Risk Assessment | 10 | PARTIAL | Risk-analysis practice without an RA-3 artifact: adversarial refutation panels (`vestigial_documentation/`-archived engine-panel documents), the standing estimates-as-hazard-detection discipline (tracker estimate rows, e.g. row 386), and the regulator-lens assessment itself. Weak but non-zero; no standing risk register. |
| SA — System and Services Acquisition | 24 | PARTIAL | SDLC/development-process discipline is deep and mechanized: ADR-0012/ADR-0013 (structural hygiene, execution completeness) enforced via the gates corpus and both-polarity seen-red fixtures (`gates/fixture_census.py`) — real SA-3/SA-11/SA-15 territory. SA-4/SA-10 acquisition/dependency management: ABSENT — no dependency manifest of any kind exists (no requirements.txt/pyproject.toml/package.json; verified by search here and independently in the regulator assessment). |
| SC — System and Communications Protection | 51 | PARTIAL | A built-but-unarmed crypto layer: `design/MAINT-GPG-TRUST-LAYER.md` mechanism is implemented and seen-red-witnessed against throwaway keys only (no real maintainer key generated — "inert" per the regulator doc). Network protection: TLS off (live-verified `SHOW ssl` → `off`), pg_hba fix prepared-unapplied (`design/MAINT-PG-HBA-HARDENING.md`). |
| SI — System and Information Integrity | 23 | PARTIAL | The strongest family: SI-7 integrity via the s26 row-hash chain + s27 high-water witness + `gates/append_only_integrity.py`; SI-10/SI-11 defect-class gates across `gates/` (13 gates, each with a seen-red fixture); SI-2 flaw tracking via the findings ledger + `gates/findings_gate.py` (an OPEN finding blocks close). Absent: SI-4 infrastructure/security monitoring (hook observers monitor agent process conduct, not host security), and SI-2 has no third-party-vulnerability dimension because no dependency manifest exists (see SA/SR). |
| SR — Supply Chain Risk Management | 12 | ABSENT-AND-UNNAMED | No dependency manifest and no supply-chain process at all — there is currently nothing enumerated to manage the supply-chain risk OF, and no document says that is acceptable. |

**Headline counts:** IMPLEMENTED (whole family): **0**. PARTIAL: **9** (AC, AU, CM, IA, IR,
RA, SA, SC, SI). NAMED-AS-EXCLUDED: **0**. ABSENT with no mechanism: **11**, splitting into
ABSENT-AND-NAMED: **1** (CP) and ABSENT-AND-UNNAMED: **10** (AT, CA, MA, MP, PE, PL, PM, PS,
PT, SR).

Two headline observations the counts carry:

1. **NAMED-AS-EXCLUDED is empty, and that is itself the audit's largest finding.** The project
   has never once formally ruled a control family out of scope. Ten families sit absent with
   nothing declaring the absence deliberate — exactly the state the what-did-we-miss RCA
   diagnosed for audit-of-reads, now shown to be the *default* state of most of the standard.
   Several of these (PE, PS, PM, MP, MA) are almost certainly out of scope for a single-host
   single-operator governance tool, but "almost certainly" is a judgment this audit is not
   licensed to make for the maintainer; converting them from ABSENT-AND-UNNAMED to
   NAMED-AS-EXCLUDED is a cheap, batched maintainer decision (proposal P1).
2. **No family is IMPLEMENTED whole.** Even AU/SI, where the write-side machinery is genuinely
   strong, carry named absent controls. This matches the registry's own posture ("a measuring
   stick, not a conformance claim") and the regulator assessment's "not-yet" verdict.

A note on the perimeter ruling, because it governs how several rows above may be read: the
standing maintainer ruling of 2026-07-12 ("host-perimeter questions are not re-raised to you",
[design/MAINT-MAINTAINER-DECISION-BRIEF.md](MAINT-MAINTAINER-DECISION-BRIEF.md)) is
decision-queue scoping — it stops agents from
repeatedly asking him to harden his own machine. It is NOT a scope exclusion: no document says
host hardening is outside the project's security scope, and the gaps themselves (superuser,
TLS, pg_hba) remain named-and-open in the PARTIAL rows above. This audit therefore marks
nothing NAMED-AS-EXCLUDED on that ruling's strength, and — honoring the same ruling — the
follow-up proposals below route perimeter items as adopter-facing documentation candidates,
not as questions re-raised to the maintainer about his host.

## The AU family walk — the pre-registered success criterion

The commission (row 249) pre-registers this audit's pass/fail condition: the AU family walk
MUST surface audit-of-reads (AU-2/AU-3/AU-12 territory) as a distinct posture line, because
five prior corpus-outward audit layers each missed it; if a registry-rooted walk missed it
too, the Revisit-#4 method itself would be refuted.

**Criterion outcome: MET.** Enumerating AU from the catalog's own 16 controls forces the
question "what events are logged?" (AU-2) to be answered per event class, and read events are
a class the catalog's structure will not let the enumerator skip — the walk below surfaces
audit-of-reads as its own line, in its true (mostly absent) state. Stated with the honesty the
method demands: this runner was not blind — the commission text itself names the criterion, so
this walk cannot claim to have *rediscovered* audit-of-reads unprompted, only that the
enumeration direction produces the line by construction, prompted or not. (The commission's
"blind-context runner preferred" was not satisfied this run; that residual is listed under
hazards in the closing section.)

All 16 AU controls, from the parsed catalog, each with its posture:

| AU control (ID and catalog title) | Posture in autoharn |
|---|---|
| AU-1 Policy and Procedures | ABSENT as a formal policy document; the ledger-and-witness doctrine in CLAUDE.md/ORCH-CAPABILITIES.md is the de-facto policy, unnamed as such. |
| AU-2 Event Logging (which events) | PARTIAL, split by event class — see the audit-of-reads line below. Write events: IMPLEMENTED. Read events, DB layer: ABSENT. Read events, agent-tool layer: IMPLEMENTED. |
| AU-3 Content of Audit Records | IMPLEMENTED for what is logged: ledger rows carry actor, timestamp, kind, statement, refs, stamp fields (kernel schema); the read-observer journals tool, path, session. |
| AU-4 Audit Log Storage Capacity | ABSENT-AND-UNNAMED. No capacity planning for ledger or journals (scale is trivially small today; nothing says so on the record). |
| AU-5 Response to Audit Logging Process Failures | PARTIAL: a ledger INSERT failure fails the write loudly (the append is the transaction); hook journal failures are fail-open by design and say so (`hooks/` observer convention). |
| AU-6 Audit Record Review, Analysis, and Reporting | PARTIAL: `./led review-gap`, `question-status`, the findings gate, and `./pickup` hydration are real standing review instruments over the ledger; no scheduled review of the hook journals exists. |
| AU-7 Audit Record Reduction and Report Generation | PARTIAL: the kernel's derived views (`ledger_current`, `review_gap`, `work_item_*`) are exactly report-generation machinery over the audit record. |
| AU-8 Time Stamps | IMPLEMENTED: every ledger row carries a server-side timestamp; single-host, so no clock-sync question. |
| AU-9 Protection of Audit Information | PARTIAL: strong against ordinary roles (append-only triggers + `gates/append_only_integrity.py`; s26 SHA-256 row-hash chain; s27 truncation high-water witness, `kernel/lineage/s26-row-hash-chain.sql`, `s27-chain-high-water.sql`) — and s27's own LIMITS section states plainly that a superuser/schema owner can disable the triggers or drop the table, which the live passwordless-superuser hole makes reachable. |
| AU-10 Non-repudiation | PARTIAL: HMAC stamps bind rows to invocations (s17/s23), and the GPG external-custody layer that would anchor the chain head is built but unarmed ([MAINT-GPG-TRUST-LAYER.md](MAINT-GPG-TRUST-LAYER.md)). |
| AU-11 Audit Record Retention | ABSENT-AND-NAMED: no backup/retention story for the Postgres instance (regulator assessment Gap 2). The git-tracked JSONL ledgers (attestations, journals) inherit git's retention; the database does not. |
| AU-12 Audit Record Generation (who/where generates) | PARTIAL, same split as AU-2: generation exists at the ledger-write and agent-hook surfaces; no generation capability exists for DB reads (pgAudit not installed — witnessed host probe in [ORCH-PGAUDIT-EXPLORATION.md](ORCH-PGAUDIT-EXPLORATION.md)). |
| AU-13 Monitoring for Information Disclosure | ABSENT-AND-UNNAMED (no monitoring of external disclosure; adjacent: the ephemera-privacy ruling exists but monitors nothing). |
| AU-14 Session Audit | PARTIAL: Claude Code session transcripts + hook journals capture agent sessions; DB sessions are not audited. |
| AU-15 Alternate Audit Logging Capability | ABSENT-AND-UNNAMED. |
| AU-16 Cross-organizational Audit Logging | ABSENT-AND-UNNAMED (single-organization tool; unrecorded judgment, same caveat as PM/PS). |

**The audit-of-reads line, distinctly, as the criterion requires.** Who read what, when:

- **Database layer (reads of the ledger itself): ABSENT.** Nothing records SELECTs against the
  tracker. pgAudit is not installed on the host (witnessed probe, 2026-07-13, in
  [design/ORCH-PGAUDIT-EXPLORATION.md](ORCH-PGAUDIT-EXPLORATION.md) — a design-space
  exploration that binds nothing); `pg_stat_statements` ships with the host's Postgres but is
  not preloaded. Per that document's own honest scoping, which this audit adopts verbatim:
  even if adopted, pgAudit would operationalize only the *generation* slice of an
  audit-of-reads posture (AU-2/AU-3/AU-12-shaped), and would do nothing for AU-9 protection
  (the log is the least-protected artifact in the system), AU-11 retention, or AU-6 review.
  This audit marks the slice exactly there and no better.
- **Agent-tool layer (file reads by agents): IMPLEMENTED.** `hooks/pretooluse_read_observer.py`
  journals every Claude Code Read-tool invocation, built to close a witnessed gap (its
  docstring: a reviewer inspecting files "via the Read tool leaves no trace", so independence
  claims were trusted, not witnessed). This is a different surface than DB reads and the two
  are not conflated here: an agent reading the ledger through `./led` (a Bash invocation
  wrapping SQL) is visible as a Bash action-stream event, but the *SQL read itself* leaves no
  database-side record.

## Follow-up proposals from the ABSENT findings

Per the commission, every ABSENT-AND-UNNAMED finding becomes a proposed follow-up — a
candidate tracker item or a candidate registry/scope amendment routed to the maintainer. These
are proposals for the maintainer to weigh, not decisions:

- **P1 — Scope-adjudication batch (largest lever, cheapest act).** One prepared decision batch
  putting each of the 10 ABSENT-AND-UNNAMED families (AT, CA, MA, MP, PE, PL, PM, PS, PT, SR)
  to the maintainer as "exclude from scope (becomes NAMED-AS-EXCLUDED with a dated ruling) or
  keep as an open gap (becomes ABSENT-AND-NAMED)". This converts the entire silent-absence
  class into contestable decisions in one sitting — the exact remedy Revisit #4 Clause 1
  prescribes. Where the ruling lands (the registry itself, or a scope companion the registry
  links) is the maintainer's choice; the registry is his to amend.
- **P2 — Dependency manifest (SR/SA-4/SI-2).** Even if the honest content is "Python stdlib +
  psql client only", a committed manifest converts "no supply chain story" into a checkable
  claim, gives SI-2 a third-party dimension to be trivially clean on, and closes the
  regulator assessment's fourth named gap. Small, Sonnet-executable, candidate tracker item.
- **P3 — Backup/retention decision for the tracker database (AU-11/CP).** The ledger is the
  project's audit trail and single point of loss. Routed with care for the standing
  perimeter ruling: this is not a host-hardening question re-raised — it is a "does the
  audit trail survive a disk failure" question, and the deliverable could be adopter-facing
  documentation plus whatever the maintainer chooses for his own host without being asked
  twice.
- **P4 — Audit-of-reads posture decision (AU-2/AU-12 read slice).** The staged path already
  exists in the pgAudit exploration document, linked in the AU walk above (Stage 0: decide
  the posture; nothing installed until
  the maintainer says so). This audit's contribution is only the classification: the read
  slice is ABSENT at the DB layer today, and either adopting Stage 0 or ruling read-auditing
  out of scope would move the line out of the silent class.
- **P5 — Commit the action-stream principle (PT/AU-13-adjacent, and flagged once already).**
  The action-stream-is-evidentiary-basis ruling and the transcripts-privacy ruling live in
  CLAUDE.md/operating memory; the pgAudit exploration document (linked in the AU walk above)
  already noted a reader "has nowhere
  committed to land" for the former's exact wording. A short committed standing document
  would give both rulings a single committed home: the transparency dimension PT asks about,
  and the two-tier distinction those rulings draw (the hook-observed action stream is the
  surface guarantees may rest on; everything else — transcripts, `~/.claude` internals, host
  logs — is diagnostics only, never evidence).
- **P6 — Registry taxonomy amendment (proposal only; registry is maintainer-amendment-only).**
  Add ABSENT-AND-NAMED as a fifth class to the registry's property-1 vocabulary, defined as
  "no mechanism exists; the gap is acknowledged in a committed document; no exclusion has been
  ruled". Witnessed need: CP in this audit could not be honestly expressed in the four-class
  vocabulary. An audit that must choose between calling a named gap "unnamed" and calling it
  "excluded" will misreport one way or the other.
- **P7 — SSP-equivalent pointer document (PL).** Not a bureaucratic SSP — a one-page map
  stating what the system is, its boundary, and where each security-relevant mechanism lives
  (mostly links into kernel/, gates/, hooks/, law/). Low priority; listed because PL is
  currently silent, and P1 may equally resolve it by exclusion.

Ranking against the project's stated assurance goals — the ledger as trustworthy audit trail,
and the maintainer's standing quality bar of "NRC-grade product, best-effort process" (NRC =
the US Nuclear Regulatory Commission; the bar means the *artifact* adopts high-assurance
mechanisms while the *process* stays lightweight, rejecting certification bureaucracy): P3
ranks first on protection-of-the-trail grounds
(everything else assumes the ledger survives), P1 first on method grounds (it closes the
silent-absence class wholesale), P2 is the cheapest real mechanism. P4–P7 follow.

## Witness summary

- WITNESSED: OSCAL catalog fetched 2026-07-13 from the usnistgov/oscal-content URL above,
  parsed locally; 20 groups; version string "5.2.0"; all family and AU/AC/CM/IR/SI/SA control
  IDs and titles in this document printed from that parse.
- WITNESSED: repository files read this session or by the directed repo-mapping subagent with
  author spot-verification — the kernel lineage files, all 13 `gates/*.py`,
  `hooks/pretooluse_read_observer.py`, the three MAINT design docs cited, ADR-0000 (in full,
  including Revisit #4), [ADR-0017](../law/adr/0017-the-zero-context-reader.md) (the
  documentation-legibility tenet this document's attestation runs under; read in full),
  [law/STANDARDS-REGISTRY.md](../law/STANDARDS-REGISTRY.md), and the pgAudit exploration
  document (linked in the AU walk above).
- WITNESSED: tracker rows 248, 249, 386 read via `./led show` / `./led --recent` this session.
- UNEXERCISED / residual hazards, marked plainly: (1) the commission's "blind-context runner
  preferred" was not satisfied — this runner read the commission, so the AU criterion is met
  by construction-of-method, not by blind rediscovery; (2) control-level completeness inside
  the 14 non-walked families is out of this audit's declared scope (scope disclaimer above);
  (3) live-host claims (superuser, TLS off, pgAudit absent) are cited from the two prior
  documents' dated witnessed probes, not re-probed by this audit; (4) the subagent's per-file
  readings were spot-verified, not each independently re-read by the author.

## License

Public Domain (The Unlicense).
