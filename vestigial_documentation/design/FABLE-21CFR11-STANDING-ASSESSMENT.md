<!-- doc-attest-exempt: DRAFT standing assessment 2026-07-18, maintainer-read gated -->

# 21 CFR Part 11 standing assessment — where autoharn's mechanisms land, requirement by requirement

- **Status:** DRAFT (standing assessment; maintainer-read gated)
- **Date:** 2026-07-18
- **Audience:** maintainer (planning input; prompted by a family member's question)
- **Author:** Fable, fresh-context session, per the missing-standards-coverage defect class
  (ADR-0000 Revisit #4, the what-did-we-miss RCA of 2026-07-12) — this document continues
  that thread; it does not restart it. Its sibling is
  [MAINT-REGULATOR-ADOPTION-ASSESSMENT.md](MAINT-REGULATOR-ADOPTION-ASSESSMENT.md)
  (2026-07-12, four institutional lenses), whose gap inventory this document deliberately
  reuses rather than re-derives — Part 11's clauses land on largely the same walls that
  assessment already named, and where they do, the gap is cited, not rediscovered.

## Scope honesty, stated before anything else

**Part 11 does not apply to autoharn.** 21 CFR Part 11 governs electronic records and
electronic signatures created under FDA predicate rules (GxP records — drug, device,
biologics, food). autoharn is a governance/audit harness for AI-agent software work on a
single maintainer's host; no record in any of its worlds is an FDA-regulated record, and
nothing here creates, implies, or moves toward a regulatory obligation. This document is a
**capability-mapping exercise**: *if an adopter needed Part 11 for records kept in an
autoharn-shaped system, which clauses would autoharn's mechanisms already serve, which
partially, and which not at all.* Every verdict below is that mapping and nothing more.

**Standards-scope disclaimer (mandatory per ADR-0000 Revisit #4 Clause 1).** This document
deliberately does NOT cover: (1) the FDA predicate rules themselves (GMP/GLP/GCP — which
records must exist at all is their question, not Part 11's, and not this document's);
(2) FDA's enforcement-discretion posture (the 2003 "Part 11, Scope and Application"
guidance and later e-systems guidances), beyond one honesty note below; (3) EU Annex 11 or
any non-US analogue; (4) HIPAA, GDPR, or any privacy regime; (5) the validation of any
*subject* product a world governs — this maps the harness, never the work inside it;
(6) legal opinion of any kind. **Verification caveat:** the clause-by-clause structure of
Part 11 below is reproduced from the author's knowledge (the rule's operative text has been
substantively stable since 1997, with no finalized amendment the author knows of), but it
was NOT checked against the current eCFR text during this session — any clause quoted or
paraphrased here should be re-verified against eCFR before this document is relied on for
anything beyond planning. That is a named limitation, not a formality.

**Honesty note on enforcement reality (out of scope beyond this paragraph):** FDA's 2003
guidance narrowed practical enforcement to a subset of Part 11 (audit trails, record
retention, record copying enforced per predicate-rule significance; broad "validation of
everything" claims relaxed). This assessment maps against the rule's full text anyway,
because the ask is a grounded gap map, not a minimal-compliance argument.

**Two standing constraints this document honors throughout:**

- **The cryptographic signing layer is DEFERRED by standing maintainer ruling** (key
  generation, GPG trust arming — deferred until all else is banked; never to be re-raised
  as a recommendation). Where a Part 11 clause maps onto that layer, the mapping is stated
  factually — *what the built-but-inert machinery would provide* — and no line below
  recommends un-deferring it.
- **The house quality bar is NRC-grade mechanisms, no certification bureaucracy**
  (maintainer ruling; the refgraph-schema condemnation). Several Part 11 clauses demand
  procedural/paperwork machinery — SOPs, training files, a certification letter to FDA —
  that this project deliberately rejects. Those are flagged as **bureaucracy-class**
  honestly, rather than pretending a mechanism could or should discharge them.

## Verdict vocabulary

Per the house rule (claims carry witnesses; no umbrella claims), each clause gets one of:

- **WITNESSED-BY-DESIGN** — a named mechanism (delta file, gate, hook, verb) exists whose
  design directly serves the clause, with banked seen-red/witness evidence. This is a
  statement about the mechanism, never a compliance claim.
- **PARTIAL** — something real exists; what is missing is named.
- **ABSENT** — nothing in the repository serves the clause.
- **BUREAUCRACY-CLASS** — the clause demands procedure/paperwork rather than mechanism;
  the house bar rejects building it; an adopter would have to supply it themselves.

One cross-cutting caveat applies to nearly every WITNESSED-BY-DESIGN verdict below and is
stated once here rather than repeated: **the strongest mechanisms are birth-chain-only.**
Under the runs-are-strictly-linear ruling (CLAUDE.md, 2026-07-11), kernel deltas reach
reality only via a future world's birth chain. The row-hash chain (s26), full hash coverage
(s42), the write boundary (s43), principal identity (s40/s41), and standing lifecycle (s45)
are wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` for the *next* world; no
existing world — including this repository's own live tracker (`autoharn1`) — carries them
(witnessed consequence: `./judge --layer defeat` QUARANTINED on `autoharn1`,
ORCH-CAPABILITIES.md item 12). An adopter starting fresh gets the full chain from birth;
the existing corpus does not and never will.

## At a glance — the whole map in one table

Compressed from the clause-by-clause sections below, which remain the authoritative
reading (every verdict there carries its file-path witnesses; this table carries none).
Two caveats travel with every row: the strongest mechanisms are **birth-chain-only** (no
live world carries them yet), and **no clause verdict is a compliance claim** — this is a
capability map of a system Part 11 does not apply to.

| Part 11 clause | Asks for | Standing | One line |
| --- | --- | --- | --- |
| §11.10(a) validation; discern altered records | invalid/altered records discernible | PARTIAL — altered-record half is the repo's strongest suit | full-row hash chain + tamper walk, every column witnessed; hook layer itself has no test suite yet |
| §11.10(b) inspection copies | accurate, complete, human-readable copies | PARTIAL | every row readable in full today; the one-act signed export verb is planned, unbuilt |
| §11.10(c) record protection & retention | records survive the retention period | PARTIAL — the worst floor | nothing is ever deleted by design; but one disk, no backup, no restore drill |
| §11.10(d) access limits | only authorized individuals | PARTIAL | per-world DB roles + a no-raw-INSERT write boundary; host perimeter is the adopter's scope |
| §11.10(e) audit trails | secure, time-stamped, changes never obscure | WITNESSED-BY-DESIGN | the clause the system was practically built for — even *refused* writes become permanent rows |
| §11.10(f) sequencing enforcement | permitted order of steps enforced | WITNESSED-BY-DESIGN | permit-to-work: edits refused without an open+claimed work item; typed state machine; clean-exit gate |
| §11.10(g) authority checks | only authorized users act/sign | PARTIAL | typed identity, standing, suspension/revocation events; authentication behind it is one trust domain |
| §11.10(h) device checks | validity of input source | PARTIAL (reinterpreted) | for AI-agent records the "device" is the model — a served-vs-declared identity sentry watches exactly that |
| §11.10(i) training records | qualification files | BUREAUCRACY-CLASS | adopter-supplied; a typed competence-grant record exists to hang a regime on |
| §11.10(j) signature accountability policy | written + enforced | PARTIAL | governance preamble is mechanically enforced (hooks refuse, refusals teach); no signatures exist yet |
| §11.10(k) documentation control | versioned, change-controlled docs | WITNESSED-BY-DESIGN | amend-by-append law, legibility attestation loop, git — with an honest unsigned-history caveat |
| §11.30 open systems | encryption + signatures in transit | N/A (closed posture) | would be ABSENT if opened; stated, not worked |
| §11.50 signature manifestation | signer, time, meaning shown | PARTIAL | the record shapes already carry all three; the signatures themselves are inert |
| §11.70 signature/record linking | signatures cannot be excised/transferred | MACHINERY BUILT, INERT | signature welded to the hash chain (transfer breaks it); witnessed with test keys, zero real bytes signed |
| §11.100 signature uniqueness & identity | unique, never reassigned, verified owner | PARTIAL | identity is append-only events, duplicate registration refused; key slots typed and empty |
| §11.100(c) certification letter to FDA | a paper letter | ABSENT, categorically | an adopter's act, never a repository artifact |
| §11.200 signing ceremony | two-component non-biometric signatures | ABSENT | hardware-token GPG route exists on paper; whether it meets the two-component letter is flagged, unanswered |
| §11.300 credential controls | unique, aged, loss-managed credentials | MOSTLY ABSENT | two genuine matches: recorded revocation lifecycle, and refusal-recording + phone-alert watchdog for §11.300(d) |

The signature-shaped half of the table (§11.50 through §11.300) terminates almost entirely
at the cryptographic layer that is **deferred by standing maintainer ruling** — built,
witnessed with throwaway keys, covering zero real bytes, and deliberately not being armed
yet. That is a ruling, not an oversight.

---

## Subpart B — §11.10, controls for closed systems

autoharn's posture is closed-system-shaped by construction: one host, one operator, access
by provisioned Postgres roles. The clause letters follow §11.10(a)–(k).

### (a) Validation — accuracy, reliability, consistent intended performance, ability to discern invalid or altered records

**PARTIAL — the altered-records half is the strongest thing in the repo; the
formal-validation half is real but carries no coverage claim.**

*Discerning altered records:* WITNESSED-BY-DESIGN outright. The row-hash chain
(`kernel/lineage/s26-row-hash-chain.sql`: SHA-256 over an injective, length-prefixed
serialization of every column plus predecessor hash; a found-and-fixed NULL/'' collision
documented in its own header), tail-deletion witness (`kernel/lineage/s27-chain-high-water.sql`,
TRUNCATION-attack literature cited in ORCH-CAPABILITIES.md item 37), full-row coverage
(`kernel/lineage/s42-row-hash-full-coverage.sql`, closing the 22-column coverage hole of
ledger row 1449, held complete forever by `gates/hash_coverage_gate.py`), and the
`./verify-chain` walk (`bootstrap/templates/verify-chain.tmpl`: INTACT / BROKEN /
TAIL-DELETION-SUSPECT / REFUSAL-ORACLE-FORGERY-SUSPECT). Both-polarity evidence:
`seen-red/s26-row-hash-chain/`, `seen-red/s42-row-hash-full-coverage/red.txt` (all 52
columns tampered individually, each breaking the chain).

*Validation of the system itself:* the project's evidence discipline is unusually strong in
kind — 40+ dated both-polarity `seen-red/` fixture directories registered in
`gates/fixture_census.py`, per-delta `.detect.sql` verification siblings
(`bootstrap/migrate_core.py`'s PER-DELTA VERIFICATION CONVENTION), and dual independent
derivation on every kernel verdict (`./judge`, `engine/ledger_differential.py`, AGREE
vocabulary with banked DerivationRecords). But: the hook/gate layer — the enforcement
surface everything rests on — has **no unit/regression test suite and no coverage claim**
(MAINT-REGULATOR-ADOPTION-ASSESSMENT.md Gap 5(a); a witnessed fail-open doc gate,
BACKLOG's run-11 forensics), and no validation *protocol* (IQ/OQ/PQ-shaped documentation)
exists. The protocol paperwork is arguably bureaucracy-class under the house bar; the
missing hook tests are mechanism and are already Tier-2 item 10 of the regulator
assessment's proceed-plan.

### (b) Accurate and complete copies, human-readable and electronic, for inspection

**PARTIAL.** Human-readable retrieval exists per-row and per-view (`led show <id>` prints
every column in full, ORCH-CAPABILITIES.md item 31; `./pickup`'s live-derived sections;
`led --recent`), and the record is plain SQL — electronically copyable by any reader with a
role. What is missing is a **scripted export/inspection-copy verb**: nothing produces a
complete, portable, integrity-carrying copy of a world's record in one witnessed act. The
regulator assessment's Tier-2 item 9 (export each settled world read-only, hash the export,
sign the digest as an "as-of attestation") is exactly the (b)-shaped verb, planned and
unbuilt. Under the self-application ruling this must be a verb, not a runbook, when built.

### (c) Protection of records; accurate and ready retrieval throughout the retention period

**PARTIAL — protection against modification is strong; protection against loss is the
single worst floor in the map.** Modification: append-only by trigger (`append_only_row`,
s15 lineage; refused mutations banked in `seen-red/06-append-only-integrity/`), plus the
(a)-clause hash machinery. Retention-as-such is trivially satisfied in one direction —
nothing is ever deleted; supersession (`kernel/lineage/s31-supersession-uniform-retraction.sql`)
retracts by new row, never removal. But *retrieval throughout the retention period*
presumes the record survives its substrate, and **no backup, replication, or
disaster-recovery story exists anywhere** for the single Postgres instance holding every
world (MAINT-REGULATOR-ADOPTION-ASSESSMENT.md Gap 2, "the floor"; three lenses searched
independently, no artifact found; re-confirmed structurally by this session — the only
retention language in the tree covers engine derivation records under `engine/docs/`). A
Part 11 reading fails (c) on this alone. The scripted backup verb is Tier-2 item 6 of the
standing proceed-plan.

### (d) Limiting system access to authorized individuals

**PARTIAL — real inside the schema, open at the perimeter.** Inside: per-world Postgres
roles scaffolded per deployment (`bootstrap/new-project.sh`), and — for worlds born at the
current chain head — the s43 write boundary
(`kernel/lineage/s43-typed-verdict-write-boundary.sql`): the granted role holds NO INSERT
privilege on any kernel-governed table; four SECURITY DEFINER functions are the only write
path (raw INSERT REFUSED-AS-EXPECTED, `seen-red/s43-typed-verdict-write-boundary/red.txt`).
Perimeter: as live-verified 2026-07-12 (MAINT-REGULATOR-ADOPTION-ASSESSMENT.md, not
re-verified this session), the host ran a **passwordless network-reachable Postgres
superuser with TLS off**, and pg_hba hardening remains listed as "a maintainer act,
unscheduled" in ORCH-CAPABILITIES.md's "Not yet enforced" section. That credential bypasses
every in-schema control. Additionally, all principals share one OS user; the HMAC stamp is
"a tripwire, not authentication" (ORCH-CAPABILITIES.md "Honest limits", the project's own
words). (Per standing ruling, host-hardening for the maintainer's own machine is not a
question this document raises — the fact is recorded because a Part 11 map without it would
be dishonest; adopter-facing framing only.)

### (e) Secure, computer-generated, time-stamped audit trails; changes shall not obscure previously recorded information

**WITNESSED-BY-DESIGN — this is the clause autoharn was practically built for, with two
honest caveats.** Every row carries insert-time `ts` (database-generated), actor resolved
from the connection, HMAC stamp binding session/agent (s17), a per-invocation token (s23),
and — separated by type, never conflated — a writer-declared event time
(`kernel/lineage/s24-declared-event-time.sql`, disclosed in its own header as an
unauthenticated declaration). Corrections never obscure: `supersedes`/`amends` are new
linked rows, the old row stands forever — the "shall not obscure previously recorded
information" clause implemented as a database type rather than a procedure. Two mechanisms
go *beyond* the clause: refusals are themselves recorded (s43's `write_refused` rows —
denied-attempt logging, which the delta's own header names as NIST AU-2/AC-7-shaped;
unretractable per ratified R6), and the trail's own contemporaneity is audited with a typed
verdict vocabulary (`./audit`: CONTEMPORANEOUS | BATCHED_DECLARED | LATE_DECLARED |
BACKFILL_SUSPECT, dual-producer since 24b — `engine/lp/contemporaneity.lp`,
`engine/contemp_floor.py`).

Caveats, both self-documented: (1) ledger rows are *writer-authored declarations*, not
automatic captures — the automatic layer is the hook journals
(`.claude/logs/invocations.jsonl`, read/mutation/delegation observers), and the project's
own conformance map records contemporaneity as historically "VIOLATED in witnessed
practice" (rows landing in retroactive bursts, run-5/7/8 forensics); (2) "secure" holds
against the granted role, not against the schema-owner/superuser — that residue is exactly
what the deferred signed-chain-head layer exists to close (see §11.70 below).

### (f) Operational system checks to enforce permitted sequencing of steps and events

**WITNESSED-BY-DESIGN.** This is the permit/obligation machinery: permit-to-work (an edit
to a governed file DENIED without an open+claimed work item —
`hooks/pretooluse_change_gate.py`, `seen-red/change-gate-subject-root/` cases f/g/h),
work-item state validation (`kernel/lineage/s22-work-item-ledger.sql`: no claim/close
without an opening act; `shipped` requires a witness, as a table CHECK),
`kernel/lineage/s39-blocks-start.sql`, obligation → review-gap → countersign ordering
(s20), and the clean-exit Stop gate (`hooks/stop_clean_exit.py`: a session cannot end
"done" while debt views are non-empty; live-witnessed run 7). Sequencing of the *record*
itself is the (a)/(e) chain machinery.

### (g) Authority checks — only authorized individuals use the system, sign, or access the operation

**PARTIAL — a genuinely typed authority model exists at the chain head; authentication
under it is weak.** The s40/s41/s45 family is an authority-check substrate most compliance
systems lack: identity as append-only attributed events with registrar recorded and
duplicate registration refused (`kernel/lineage/s40-principal-identity-events.sql`);
role/key/competence bindings and typed relations, retraction by supersession only
(`kernel/lineage/s41-principal-bindings-and-relations.sql`); suspension/revocation with a
sanctioned lift and resurrection-proof standing derivation
(`kernel/lineage/s45-standing-lifecycle.sql`, `seen-red/s45-standing-lifecycle/red.txt` —
a write under a revoked principal refused and *recorded*). Independence claims are refused
unless invocation-distinct (s21). What is weak: the authority checks authenticate a
*database role plus an HMAC tripwire*, all inside one trust domain ("everything the harness
proves today, it proves inside one trust domain" — MAINT-GPG-TRUST-LAYER.md §1, quoted in
the regulator assessment Gap 4), and the whole family is scratch-witnessed only, applied to
no live world yet (the birth-chain caveat above).

### (h) Device checks — validity of source of data input

**PARTIAL, leaning ABSENT in the classical sense.** No terminal/device validity checking
exists or would fit this deployment. Two mechanisms rhyme with the clause: the stamp
interceptor binds every write to the actual invoking session unconditionally (matcherless,
`hooks/stamp_intercept.py`, ORCH-CAPABILITIES.md item 19), and the model-identity sentry
layer checks that the *serving model* is the declared one — the one input source the hooks
cannot see (`./otel-attest`, `design/FABLE-OTEL-SENTRY-SPEC.md`; the host-side watchdog,
`local/OTEL-WATCHDOG.md`, which phones the maintainer on a served/declared mismatch —
built after the real substitution incident of ledger row 1434). For an AI-agent record
system, "which model actually produced this" arguably *is* the device check; stated as an
interpretation, not a compliance argument.

### (i) Education, training, and experience of persons who develop/maintain/use the system

**BUREAUCRACY-CLASS as written; one mechanism is adjacent.** Training files and
qualification records for a system whose "persons" are AI agents plus one maintainer are
exactly the certification paperwork the house bar rejects. The adjacent mechanism, named
for fairness: s41's `principal_competence_granted` is a typed, attributed, retractable
competence record per principal per activity — an (i)-shaped *record type* that an adopter
could hang a qualification regime on. The regime itself would be theirs to write.

### (j) Written policies holding individuals accountable for actions under their electronic signatures

**PARTIAL / BUREAUCRACY-CLASS.** The governance preamble every world receives at birth
(`bootstrap/templates/CLAUDE.md.tmpl`) plus this repo's CLAUDE.md are, functionally,
written accountability policy — and unlike most SOPs they are mechanically enforced (hooks
refuse; refusals teach). But Part 11's (j) is specifically about accountability under
*signatures*, and no real signature exists yet (deferred layer). A standalone
accountability SOP would be paperwork the project would not write.

### (k) Systems documentation controls — distribution/access; revision and change control with an audit trail

**WITNESSED-BY-DESIGN, with one disclosed weakness.** Documentation discipline is law here:
ADR-0005 (filing, amend-by-append, Rule 8's never-retro-edit — frozen sNN records with
defects foreclosed by new deltas), ADR-0017 (zero-context legibility, with an attestation
record at `attestations/doc-legibility-attestations.jsonl` and the `attest-doc` /
`gates/doc_attestation_presence.py` loop), doc gates in the pre-commit chain, and git
version control over everything. The weakness, already on record: the git substrate is
unsigned and was legitimately rewritten twice (the 2026-07-07 privacy incidents) —
documented and defensible, but it means the *documentation* audit trail rests on an
unsigned, once-rewritten history (regulator assessment gap 9). The signing half belongs to
the deferred layer.

## §11.30 — open systems

**Not applicable to the current posture; ABSENT if it were.** autoharn is deployed as a
closed system (one host, provisioned access). If a deployment were open-system-shaped,
§11.30's additional measures (encryption in transit, digital signatures) are today: TLS
off (as of the 2026-07-12 verification), and the signature layer deferred-inert. Stated for
completeness, not as a gap to work.

## §11.50 — signature manifestations (signer's name, date/time, meaning displayed in the signed record)

**PARTIAL — the manifestation *shape* exists; no Part 11 signature exists to manifest.**
Rows already carry actor, timestamp, and typed meaning (kind: `review`, `attest`,
`commission`, `decision`; grade columns; countersign linkage) in human-readable retrieval
(`led show`). The cryptographic manifestations are built and inert: a FULL-mode commission
signed by the human commissioner manifests signer/time/meaning
(`verify-commission`, `bootstrap/templates/verify-commission.tmpl`, closed vocabulary
VERIFIED | UNSIGNED | FORGED-OR-CORRUPT plus typed refusals); the signed chain head
manifests world/max_id/hash/UTC/apparatus_hash (`verify-chain --head`). All witnessed
against throwaway test keys only — no real maintainer key exists (deferred ruling;
`law/keys/README.md` is its own AWAITING-KEY stub). The mapping is factual: were the layer
armed, §11.50's elements are already in the record shapes.

## §11.70 — signature/record linking (signatures cannot be excised, copied, or transferred)

**WITNESSED-BY-DESIGN as machinery; inert pending the deferred layer.** This clause is
precisely what the three-rung GPG design exists for (design/MAINT-GPG-TRUST-LAYER.md,
design/USER-GPG-TRUST-LAYER-FAQ.md): a detached signature is over the exact statement bytes
(the byte-fidelity defect found and fixed — `printf '%s' | gpg --detach-sign`,
ORCH-CAPABILITIES.md item 29); the row is welded into the hash chain (s26/s42), so a
signature cannot be transferred to altered content without breaking the chain from that row
onward; the signed head binds the whole chain to a moment. Copy/excise/transfer resistance
is exactly the property the s26 collision fix and the s42 coverage gate protect. Every
mechanism witnessed both-polarity with throwaway keys; covering **zero real bytes today**
(the regulator assessment's Gap 1, verbatim thrust). Per the standing ruling, arming it is
deferred and not recommended here.

## Subpart C — electronic signatures

### §11.100(a) — uniqueness; never reused or reassigned

**PARTIAL (chain-head worlds).** s40 makes identity an append-only event with duplicate
registration refused and no silent re-registration (the exact `ON CONFLICT DO NOTHING`
disease it was built against, named in its header); s41's `principal_key_bound` is the
typed principal↔key binding slot ("the empty slot, not the ceremony" — its own words);
reassignment-without-record is unrepresentable at the chain head (retraction only by
superseding row). No real key occupies any slot yet.

### §11.100(b) — verify the individual's identity before establishing their e-signature

**PARTIAL.** Registration is itself an attributed, registrar-recorded event (s40), so *who
vouched* is on the record. But no identity-verification procedure exists or is meaningful
in a one-human deployment; a multi-human adopter (the MAINT-GPG-TRUST-LAYER.md §5
extension) would need to supply the verification ceremony themselves.

### §11.100(c) — certification to FDA that e-signatures are legally binding

**ABSENT and BUREAUCRACY-CLASS by definition.** A paper letter to FDA. Categorically
outside a capability map; an adopter's act, never a repository artifact.

### §11.200(a) — non-biometric signatures: two distinct components; genuine-owner use; misuse requiring collaboration of two or more individuals

**ABSENT as specified; one honest interpretive note.** No id-code+password signing ceremony
exists or is planned. The interpretive note: Part 11 distinguishes *digital signatures*
(cryptographic, §11.3(b)(5)) from generic electronic signatures, and the deferred GPG layer
is squarely the digital-signature route (hardware token per USER-GPG-TRUST-LAYER-FAQ.md's
recommendation — a possession+PIN token is arguably two-component); whether that satisfies
§11.200(a)'s letter is a regulatory-interpretation question this document flags and does
not answer. The "collaboration of two or more" misuse bar has a structural echo in the
countersign/independence machinery (s21: a claimed second pair of eyes must be provably
distinct), but that governs review claims, not signature custody — noted to avoid
overclaiming, not to claim.

### §11.200(b) — biometric signatures

**ABSENT.** Nothing biometric exists or would fit. Stated for completeness.

### §11.300 — controls for identification codes/passwords

**Mostly ABSENT; two genuine mechanism matches.**

- (a) unique id/password combinations: Postgres roles are unique per world; the 2026-07-12
  verified state (passwordless superuser) is the direct anti-pattern. ABSENT in substance.
- (b) periodic checking/aging/revision: ABSENT; no credential-aging machinery anywhere, and
  password-aging SOPs are bureaucracy-class besides.
- (c) loss management — deauthorize lost/compromised credentials, issue replacements:
  **PARTIAL by mechanism**: the key-rotation ceremony (revoke → generate → commit →
  re-sign) is exercised and witnessed with a test key, including the genuine finding that a
  revoked key is immediately unusable (USER-GPG-TRUST-LAYER-FAQ.md §8), and s45 gives
  standing suspension/revocation/lift a sanctioned, recorded lifecycle.
- (d) transaction safeguards — detect and report unauthorized-use attempts in an immediate
  and urgent manner to security and management: **PARTIAL by mechanism, and a genuinely
  good match**: s43 commits every refused write as an unretractable `write_refused` row
  (the attempt survives its own refusal), `./verify-chain` carries
  REFUSAL-ORACLE-FORGERY-SUSPECT, and the host watchdog mails the maintainer's phone on a
  model-identity mismatch within moments (local/OTEL-WATCHDOG.md — "immediate and urgent
  manner" implemented literally, for the one substitution class the hooks cannot see).
  Coverage is narrow (kernel writes; model identity), not a general intrusion-detection
  claim.
- (e) periodic testing of tokens/devices: ABSENT (no devices exist yet to test).

---

## Gap summary, ranked by how load-bearing each gap is for a Part 11 reading

1. **The signature layer is inert (deferred by standing ruling).** §11.50, §11.70,
   §11.100–11.300 all terminate here: the machinery is built, witnessed with test keys, and
   covers zero real bytes — no maintainer key, no `ratified/*` tag, no signed head over any
   real world (Gap 1 of MAINT-REGULATOR-ADOPTION-ASSESSMENT.md, unchanged). This is a
   *ruling*, not an oversight; the map states it and stops. Everything Subpart C asks for
   beyond it is either adopter ceremony or bureaucracy-class.
2. **No backup/retention floor — §11.10(c) fails on substrate survival.** The single most
   clause-fatal gap that is pure mechanism-work: one disk, no copy, no restore drill.
   Already Tier-2 item 6 of the standing proceed-plan.
3. **Perimeter access — §11.10(d)/(g) undermined from outside the schema.** Passwordless
   network superuser, TLS off (as verified 2026-07-12; unre-verified since), hardening
   prepared-unapplied. Every in-schema authority check is bypassable by the one credential.
   (Recorded for adopters; not raised as a maintainer question, per standing ruling.)
4. **Birth-chain-only coverage.** The clauses autoharn serves best — (a) altered-record
   discernment, (e) audit trail, (g) authority model, refusal recording — are at full
   strength only for a world born at the current `LINEAGE_CHAIN` head. No such world exists
   yet; the live tracker and every settled run predate s26 or s40+. The fix is one future
   `--new-world` birth, which the linearity ruling already prescribes.
5. **Validation formalization — §11.10(a)'s system half.** Hook/gate unit tests (mechanism,
   already planned) and, only if an adopter needs the paperwork, a validation protocol
   (bureaucracy-class here).
6. **No inspection-copy verb — §11.10(b).** The planned as-of export/hash/sign verb closes
   it; unbuilt.
7. **Bureaucracy-class residue an adopter must supply themselves:** FDA certification
   letter (§11.100(c)), training/qualification regime (§11.10(i)), signature
   accountability SOP (§11.10(j)), credential-aging procedures (§11.300(b)). The project's
   deliberate rejection of certification paperwork means these will never be repository
   artifacts; a Part 11 adopter takes them as their own scope.

## What this is NOT

Not a compliance claim — no record in any autoharn world is FDA-regulated, and no clause
verdict above asserts Part 11 conformance of anything. Not a certification path — the
project's quality bar explicitly adopts high-assurance *mechanisms* and rejects
certification *bureaucracy*, and several Part 11 clauses are the latter by nature. Not a
recommendation to arm the deferred signing layer — that ruling stands and this document
does not touch it. Not verified against the current eCFR text — the clause structure is
from the author's knowledge and should be re-checked before any use beyond the maintainer's
planning. And not a restart: the load-bearing gap inventory here is the 2026-07-12
regulator-adoption assessment's, re-cut along Part 11's clause lines.

## Related

- [MAINT-REGULATOR-ADOPTION-ASSESSMENT.md](MAINT-REGULATOR-ADOPTION-ASSESSMENT.md) — the
  four-lens sibling whose gaps this document reuses.
- [law/adr/0000-the-alpha-and-the-omega-type-driven-design.md](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
  Revisit #4 — the standards-coverage RCA whose Clause 1 this document's scope disclaimer
  discharges.
- [ORCH-CAPABILITIES.md](../../ORCH-CAPABILITIES.md) — the witnessed-capability inventory
  every mechanism citation above leans on.
- [design/MAINT-GPG-TRUST-LAYER.md](../../design/MAINT-GPG-TRUST-LAYER.md) /
  [design/USER-GPG-TRUST-LAYER-FAQ.md](../../user-guide/USER-GPG-TRUST-LAYER-FAQ.md) — the built, inert,
  deferred layer Subpart C maps onto.
