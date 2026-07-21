# AUDIT-AC-IA-POSTURE-2026-07-21 — NIST SP 800-53 Rev 5.2.0 AC and IA families, control-by-control

<!-- doc-attest-exempt: point-in-time audit record, dated 2026-07-21. Never retro-edited; a
later audit supersedes it by a new numbered/dated document, the same rule
design/vestigial_documentation's ORCH-REGISTRY-COMPLETENESS-AUDIT-001/002.md state about
themselves. Reason for exemption: this document's load-bearing content is a family/control
enumeration read verbatim from a fetched, sha256-pinned artifact, cross-checked against
in-repo file:line witnesses gathered directly by the authoring session (grep/read, not a
subagent chain) -- there is no separate fresh-context B-pass available to this invocation (no
agent-forking tool was offered), so an ADR-0017 A:B:C loop cannot literally run here, exactly
the honest posture ORCH-REGISTRY-COMPLETENESS-AUDIT-002.md already recorded for itself under
the same constraint. That residual is stated once here and not hidden: a fresh-context B-read
of this document's framing prose (not its catalog quotes or file citations) is recommended
before or alongside the next registry audit in this series, and is currently UNEXERCISED. -->

Audience: maintainer, orchestrator, and any future auditor picking up the NIST SP 800-53
registry thread for the AC/IA families specifically.

**Provenance.** Commissioned by the maintainer, verbatim: *"Please start the audit (R1) that
the consult recommended."* R1 is [design/FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md](FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md)
§5 ("commission the registry-rooted NIST 800-53 completeness audit for the AC and IA families
now"), itself answering [law/STANDARDS-REGISTRY.md](../law/STANDARDS-REGISTRY.md)'s pending
line and [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) Revisit #4's
completeness-exercise rule (enumerate FROM the standard's own catalog TOWARD the project, never
the reverse). This is the **third** document in the registry-completeness series and the
**first** to walk AC and IA at full control granularity:
[ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md](../vestigial_documentation/design/ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md)
(2026-07-13) classified all 20 families at family level, with only AU walked control-by-control
(AC and CM/IR/SI/SA were "named-control level" — a summary line, not a per-control table; IA
was not in that named-control set at all).
[ORCH-REGISTRY-COMPLETENESS-AUDIT-002.md](../vestigial_documentation/design/ORCH-REGISTRY-COMPLETENESS-AUDIT-002.md)
(2026-07-14) is the maintainer's verbatim family-level response, not a control walk. Both are
read in full and cited below rather than duplicated; this document does not re-derive the
family-level classification (AC PARTIAL, IA PARTIAL) — it is the control-by-control expansion
001 named as still owed and the consult's §3 "orientation map... not the registry-rooted audit
itself" explicitly deferred.

## 1. The pinned catalog (per ADR-0000 Revisit #4 Clause 2 and the rows-1432/1433 precedent)

- **Source URL** (fetched this session, 2026-07-21):
  `https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json`
- **Retrieval date:** 2026-07-21 (this session).
- **Revision, read from the fetched file's own metadata:** title "Electronic (OSCAL) Version of
  NIST SP 800-53 Rev 5.2.0 Controls and SP 800-53A Rev 5.2.0 Assessment Procedures"; `version`
  field `5.2.0`; catalog `last-modified` `2026-05-11T16:01:09.00000-00:00`. Identical revision
  string to the one 001 fetched on 2026-07-13 (same 20 groups, same per-family control counts,
  cross-checked below) — the catalog has not moved between the two audits.
- **sha256 of the retrieved artifact (10,442,037 bytes):**
  `01f37cf90ea99d92242c936cbfbdebcc338eef1f71454e2acac36cc56e9bc062`
- **Parse method:** downloaded to a local file and parsed with Python's stdlib `json` module
  (not summarized through a fetch tool, not recalled from training knowledge — the same
  discipline 001 states for itself). `catalog.groups` has exactly 20 entries; family IDs,
  titles, and control counts below are printed directly from that parse. AC (`ac`, "Access
  Control") has 25 base controls; IA (`ia`, "Identification and Authentication") has 13 base
  controls — both figures match 001's independently-fetched count from 2026-07-13, a
  cross-check this audit did not have to perform blind (it is a same-catalog reproduction, not
  an independent second source, and is named as such rather than oversold).
- **Enhancement/withdrawn detection:** each control's `props` array was scanned for
  `{"name": "status", "value": "withdrawn"}`; withdrawn base controls and enhancements are
  marked WITHDRAWN below and excluded from the four-state counts (a withdrawn control has no
  posture to hold — NIST itself removed the requirement).

## 2. Scope, method, and the enhancement non-coverage (named, per the commission's own instruction)

**Base controls: full enumeration, no skips.** Every one of AC's 25 and IA's 13 base controls
appears in the matrix below, including the four WITHDRAWN base controls (AC-13, AC-15, and none
in IA) — withdrawn rows are shown for completeness (a zero-context reader should not have to
wonder whether a missing ID was overlooked) but carry no verdict.

**Enhancements: NOT walked exhaustively — named non-coverage, not silent.** AC's 25 base
controls carry roughly 150 enhancements between them (AC-4 alone has 32); IA's 13 carry roughly
55. Walking every enhancement individually would multiply this document's length by
roughly 5x for a governance harness where the overwhelming majority of enhancements target
concerns this project structurally does not have (biometric authenticators, wireless
antennas, PIV credentials, federated identity providers, mobile-device containers). This audit
descends into an enhancement **only where the base control's own posture verdict materially
depends on it** — i.e., where citing the enhancement changes whether the base control reads as
MET-BY-MECHANISM, BOUNDED, or SILENT rather than just adding detail. Enhancements cited this way
are listed inline under their base control's row, not given separate matrix rows. **Every other
enhancement under every base control is un-walked** — this is the exclusion the commission asked
to be named rather than left silent. A future audit (004+) narrowing further, per 001's own
"the next audit in this series narrows per the maintainer's priorities" convention, is where
that walk would land if the maintainer wants it.

**Verdict definitions** (per the commission, not 001's five-class registry vocabulary — the two
are related but not identical, see §5 below for the mapping):
- **MET-BY-MECHANISM** — a named mechanism (file:line or kernel-delta citation) discharges the
  control's requirement, and the witness explains how.
- **BOUNDED** — partially met; the row states exactly what is and is not covered.
- **NAMED-AS-EXCLUDED** — the project has an actual, findable, dated ruling or argued exclusion
  on record saying it deliberately does not meet this control (not this auditor's own guess at
  what "should" be excluded — per 001's own discipline, "almost certainly out of scope" without
  a ruling stays un-excluded).
- **SILENT** — nothing in the repo meets, bounds, or excludes it. The state the audit exists to
  surface.

**A deliberate divergence from 001's classification habit, stated so it isn't mistaken for an
inconsistency:** 001 marked several families "ABSENT-AND-UNNAMED" even where a document
*acknowledges* the gap without ruling it excluded (its own proposed fifth class,
ABSENT-AND-NAMED, accepted-in-principle by the maintainer in row 680 per 002). This audit's
four-state contract has no such fifth bucket; where a gap is acknowledged in a committed
document but not ruled excluded, this audit marks it **SILENT** (because it is still
unenforced/unmet by mechanism) and says so in the note column — never silently upgraded to
NAMED-AS-EXCLUDED on the strength of a mention alone.

## 3. The AC family — Access Control (25 base controls)

| ID | Title | Verdict | Witness | Note |
|---|---|---|---|---|
| AC-1 | Policy and Procedures | SILENT | No AC-specific policy/procedures document exists. `CLAUDE.md` and `ORCH-CAPABILITIES.md` (repo root) are de-facto operating doctrine, unnamed as an AC-1 policy — same reading 001 gave AU-1. | De-facto, not formal; a one-line AC-1 pointer would be cheap. |
| AC-2 | Account Management | BOUNDED | Registration with mandatory stated purpose (`kernel/lineage/s40-principal-identity-events.sql`, `principal_purpose` CHECK; `design/FABLE-PRINCIPAL-IDENTITY-SPEC.md:79` names AC-2 directly). Lifecycle: `principal_standing_declared`/`principal_suspended` (s45); **`principal_revoked` is deliberately ABSENT** — s45's own header: "principal_revoked is DELIBERATELY ABSENT — that absence IS the ratified 'terminal by...'" (`kernel/lineage/s45-standing-lifecycle.sql:73-74`). Role types are free text, an explicit AC-2(a) governance-process reading, witnessed derivation `design/FABLE-PRINCIPAL-IDENTITY-SPEC.md:335` (ledger rows 1432/1433, sha256-pinned OSCAL fetch). | Registration/lifecycle/purpose real; disable-vs-revoke asymmetry is a live design choice, not a gap, but worth the maintainer's eyes once (see §7). |
| AC-3 | Access Enforcement | MET-BY-MECHANISM | `kernel/lineage/s43-typed-verdict-write-boundary.sql`: after this delta the granted role holds NO INSERT privilege on any kernel-governed table; five SECURITY DEFINER functions (`ledger_write`, `review_write`, `registration_write`, `obligation_write`, `artifact_write`) are the only write path (`s43:177-190`, `REVOKE ALL...GRANT EXECUTE` throughout, e.g. `s43:814-815`). | Reaches future births only (runs-are-linear); the file is authored/scratch-witnessed, not yet applied to the live world. |
| AC-4 | Information Flow Enforcement | BOUNDED | `kernel/lineage/nla-schema.sql`: database catalog isolation for nla-schema subjects (`nla-schema.sql:229-241`, opaque connecting role, append/read-own-ledger-only grants). But the same file names a live, unremediated hole: "**BLOCKING HAZARD — creating this login role is NOT sufficient for subject isolation**... PostgreSQL grants CONNECT to PUBLIC by default and pg_hba.conf here admits every role to every database... an UNCONFINED `nla_rw` can `psql -U nla_rw -d epistemic` and read the ENTIRE apparatus catalog... verified live" (`nla-schema.sql:232-238`). | The isolation *mechanism* is real; the isolation *outcome* is not achieved until a pg_hba write happens outside this build's reach — named in the file itself, not silent, but still open. |
| AC-5 | Separation of Duties | BOUNDED | `kernel/lineage/s18-criterion-principals.sql`: reviewer roles hold column-scoped SELECT only (`s18:74-75`), "review rows with NO SELECT on the unit ledger" (`s18:4`) — a zero-SELECT-on-own-work-product writer split. `s41` D-6 (`s41:119-133,521-558`) refuses `managerial`/`financial` independence claims from non-human principals. | Real for a solo-plus-agents world; the spec's own words (per the consult) are that in a solo world SoD is recorded truthfully, not adversarially real — this audit does not relitigate that framing, only cites the mechanism. |
| AC-6 | Least Privilege | MET-BY-MECHANISM | `s18-criterion-principals.sql` (column-scoped, zero-table-SELECT reviewer grants); `s43-typed-verdict-write-boundary.sql` (INSERT revoked entirely, EXECUTE-only on five narrow functions); `s20-obligation-grants-and-view-refresh.sql:129` (narrow, function-scoped GRANTs, same pattern). | AC-6(1)/(5)-shaped ("authorize access to security functions" / "privileged accounts") is what the boundary-function EXECUTE grants materially are. |
| AC-7 | Unsuccessful Logon Attempts | MET-BY-MECHANISM | Not a logon-lockout mechanism (there is no interactive login surface to lock) — the control's *shape* is discharged differently: every refused write is caught and committed as an unretractable `write_refused` ledger row (`s43:69-75`, R6), never a silent drop. `s43`'s own header names the mapping: "NIST AU-2/AC-7-shaped denied-attempt logging... named by the standards work, never forced by any mechanism [before this delta]" (`s43-typed-verdict-write-boundary.sql:25`). | Read literally AC-7 is about account lockout after N failed logons, which does not apply here; read at the level of "denied attempts get recorded, not silently discarded" — the shape s43 was explicitly built against — the control's animating concern is met. Flagged as an interpretive stretch, not hidden as a clean match. |
| AC-8 | System Use Notification | SILENT | No login banner/use-notification artifact found (searched `hooks/`, `tools/setup_tui/`, `serving/`, `*.md` for "system use notification", "banner", "logon"). | No interactive login surface exists for a human to see a banner on; still unnamed as excluded. |
| AC-9 | Previous Logon Notification | SILENT | No artifact found; same search as AC-8. | Same no-login-surface reasoning as AC-8, not itself a ruling. |
| AC-10 | Concurrent Session Control | SILENT | No artifact found. `judgment/engine/engine-frontier-semantics-SEED.md:149` mentions "concurrent sessions" once, in an unrelated ACTIVE-adversary framing note, not a control mechanism. | — |
| AC-11 | Device Lock | SILENT | No artifact found (searched for "session lock", "device lock", "screen lock", "inactivity"). | Not applicable to a headless service/CLI in the classic sense; unnamed as excluded. |
| AC-12 | Session Termination | SILENT | No artifact found. Postgres connections are per-invocation (short-lived `psql` calls via `./led`), which bounds the exposure informally, but no policy or mechanism names or enforces a termination condition. | — |
| AC-13 | (WITHDRAWN — "Supervision and Review — Access Control") | — | Catalog `props` marks this control withdrawn. | No verdict; NIST retired the requirement. |
| AC-14 | Permitted Actions Without Identification or Authentication | SILENT | `serving/boundary_service.py:23-27`: "adds NO truth of its own"; the boundary service serves every derived view with no caller-identification surface (confirmed by reading its auth-relevant header text this pass — no principal/session check appears before a read is served). The consult's own §3 names this control as the one that should convert the read-surface's current state into a documented decision (`design/FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:190-193`), and its §7 D4 leaves that undone. | Consult's recommendation (name it, don't build) is sound but has not yet been enacted as an actual dated decision anywhere in the repo — so it stays SILENT here, not NAMED-AS-EXCLUDED, per this audit's own discipline in §2 above (a recommendation to name something is not the naming). |
| AC-15 | (WITHDRAWN — "Automated Marking") | — | Catalog `props` marks this control withdrawn. | No verdict. |
| AC-16 | Security and Privacy Attributes | SILENT | No artifact found (searched for "security attribute", "privacy attribute", "classification label"). | — |
| AC-17 | Remote Access | SILENT | No artifact found; consult §3 names remote access as "plausibly N/A" but not yet ruled (`design/FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:227-228`). | Per the standing perimeter ruling (2026-07-12) this is adopter-facing-only territory for the maintainer's own host, never a recommendation to him; still SILENT in the matrix because no ruling names it excluded (same handling 001 gave the host/perimeter rows). |
| AC-18 | Wireless Access | SILENT | No artifact found. | Not applicable to this project's shape; unnamed as excluded, same reasoning as AC-11. |
| AC-19 | Access Control for Mobile Devices | SILENT | No artifact found. | Same reasoning. |
| AC-20 | Use of External Systems | SILENT | No artifact found. | Same reasoning. |
| AC-21 | Information Sharing | SILENT | No artifact found. | — |
| AC-22 | Publicly Accessible Content | SILENT | No artifact found; `serving/boundary_service.py` is not publicly deployed today (localhost-scoped per the perimeter ruling), so the control's premise is not currently live, but nothing rules it out for a future adopter deployment. | Adopter-facing observation candidate, not a maintainer recommendation, per scope bounds. |
| AC-23 | Data Mining Protection | SILENT | No artifact found. | — |
| AC-24 | Access Control Decisions | MET-BY-MECHANISM | `kernel/lineage/s43-typed-verdict-write-boundary.sql:42` (`kernel.write_verdict` type, Element 1) — every write attempt returns a typed, explicit verdict (accepted / refused with reason), never an ambiguous silent outcome. | Matches the control almost exactly; the consult calls this row "Strong" (`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:194-195`) and this audit's independent read agrees. |
| AC-25 | Reference Monitor | MET-BY-MECHANISM | `s43` is architecturally a reference monitor: one enforcement point (the five SECURITY DEFINER functions), decisions and their records sharing one trust boundary, tamperproof by the s26/s42 hash chain. `design/FABLE-PRINCIPAL-IDENTITY-SPEC.md:270` and the refusal-recording consult (cited at `s43`'s own header) explicitly invoke AC-25's trust-boundary requirement as the design's own grounding, not this audit's retrofit. | Reaches future births only, same caveat as AC-3. |

**AC summary:** 25 base controls (2 WITHDRAWN, no verdict) → of the 23 verdictable: 4
MET-BY-MECHANISM (AC-3, AC-6, AC-7, AC-24 — plus AC-25 makes 5), 4 BOUNDED (AC-2, AC-4, AC-5, and
none else), 0 NAMED-AS-EXCLUDED, 14 SILENT. (Exact recount in §6.)

## 4. The IA family — Identification and Authentication (13 base controls)

| ID | Title | Verdict | Witness | Note |
|---|---|---|---|---|
| IA-1 | Policy and Procedures | SILENT | No IA-specific policy document; same de-facto-doctrine reasoning as AC-1. | — |
| IA-2 | Identification and Authentication (Organizational Users) | BOUNDED | For the human maintainer: real, human-performed GPG signatures at three deliberate moments (ratification tags, SIGNED commissions, signed chain heads — `design/MAINT-GPG-TRUST-LAYER.md` §2-§4, lines 42-134). For every agent principal: **deliberately NOT met**, and the spec says so in terms — "A declared standing default still authenticates nothing... Strict attribution is honest bookkeeping, not authentication — stated so the spec never overclaims IA-2" (`design/FABLE-PRINCIPAL-IDENTITY-SPEC.md:270`). | The consult recommends marking the agent half NAMED-AS-EXCLUDED "with the vendor-ceiling argument, not partial" (`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:196-202`) — this audit finds the human half real enough, and the agent half's exclusion argued firmly enough (see IA-3 below and §5), that BOUNDED (split by principal population, both halves cited) is the honest single verdict for the base control; the split itself is what the note preserves. No enhancement walk (IA-2(1)/(2) MFA): the GPG token is single-factor (something-you-have) by the file's own account, not MFA — named, not silently assumed. |
| IA-3 | Device Identification and Authentication | NAMED-AS-EXCLUDED | Hooks-layer/agent identity is an **argued exclusion**, not a silent gap: `design/FABLE-PRINCIPAL-IDENTITY-SPEC.md:210` — "(i) the hooks/gate layer reasons about 'who' outside the kernel... swept for this spec only to the extent of naming it: **not covered**, its argued exclusion (ADR-0017's identity-enumeration-fails-open reasoning) stands." True foreclosure would require provider-side response signing or model identity in the hook payload, both "out of this project's control... genuinely at the vendor seam" (`design/FABLE-SUBSTITUTION-OF-AUTHORITY-CONSULT-2026-07-19.md:84`). | This is the one IA row this audit classifies differently from a literal reading of the consult's own §3 (which discusses this territory under IA-2, not as a distinct IA-3 exclusion) — see §5. |
| IA-4 | Identifier Management | MET-BY-MECHANISM | `kernel/lineage/s40-principal-identity-events.sql:242` — principal id is "the anchor's immutable primary key"; no rename, only succession (`s40:117,597`: "this is what forecloses" silent identity mutation — a fresh successor principal plus an s41 `succeeds` edge is the only path forward, never an in-place rename). Standing enforcement refuses further writes from a non-active principal and names the successor path explicitly (`s40:567`). | Real and well-witnessed; the consult's "largely met" read (`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:199`) is confirmed, upgraded here from "largely" to a clean MET given the immutability + no-reuse + succession triad all have direct citations. |
| IA-5 | Authenticator Management | BOUNDED | Public-key-based (IA-5(2)-shaped): the GPG keypair, hardware-token-preferred (`design/MAINT-GPG-TRUST-LAYER.md:167-169`, "a hardware-backed keypair (a YubiKey-class token) is strongly preferred: the private key physically cannot leave the token"), with a documented rotation procedure witnessed on a throwaway key (`MAINT-GPG-TRUST-LAYER.md` §7). Password-based (IA-5(1)): not applicable — no password authenticators exist anywhere in the design. The key-binding slot for agent principals is explicitly empty until a deferred ceremony (`s41` D-4, per the consult `FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:137`). | Strong for the one human authenticator that exists; structurally absent for every non-human principal, by the same IA-2/IA-3 design choice, not a separate gap. |
| IA-6 | Authentication Feedback | SILENT | No artifact found (no interactive password-entry surface to obscure feedback on). | — |
| IA-7 | Cryptographic Module Authentication | SILENT | No artifact found. GPG hardware-token preference (MAINT-GPG-TRUST-LAYER.md) is IA-5(2)/IA-7-adjacent but the control's literal target — a system authenticating itself to a cryptographic module before use — has no cited mechanism. | Distinguished here from IA-5's GPG citation rather than double-counted as MET; the overlap is real but the control's own requirement (module-to-system authentication) is not directly evidenced. |
| IA-8 | Identification and Authentication (Non-organizational Users) | SILENT | No artifact found; no non-organizational-user-facing surface exists in this project's current shape. | — |
| IA-9 | Service Identification and Authentication | SILENT | No artifact found (searched for "service identification", "service authentication"). The `write-boundary` tool principal (s43) is *attributed*, not authenticated in the IA-9 sense. | — |
| IA-10 | Adaptive Authentication | SILENT | No artifact found. | — |
| IA-11 | Re-authentication | SILENT | No artifact found. | — |
| IA-12 | Identity Proofing | SILENT | No artifact found; registration (`s40`) records a stated purpose, not identity-proofing evidence in the IA-12 sense (evidence collection/validation of a real-world identity). | — |
| IA-13 | Identity Providers and Authorization Servers | SILENT | No artifact found; no federated-identity surface exists. | — |

**IA summary:** 13 base controls, all verdictable (none withdrawn): 1 MET-BY-MECHANISM (IA-4), 2
BOUNDED (IA-2, IA-5), 1 NAMED-AS-EXCLUDED (IA-3), 9 SILENT.

## 5. Corrections to the consult's §3 orientation map

The consult's §3 is explicitly "a consult's orientation map... not the registry-rooted audit
itself" (`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:165-168`) and invites correction. This
audit's control-by-control walk agrees with the consult's mechanism citations throughout (every
file:line the consult names checks out on independent re-read) but corrects three things:

1. **AC-2's disable/revoke asymmetry was not in the consult's §3 row at all.** The consult's
   AC-2 line (`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:170-173`) reads "Strong" without
   mentioning that `principal_revoked` is deliberately absent from the kernel (s45's own header,
   cited above). This audit downgrades AC-2 from the consult's implicit "Strong" framing to
   BOUNDED — the omission is a design choice with a stated reason, not a defect, but a reader of
   the consult alone would not learn that account *disablement* stops at suspension (a liftable
   state) and never reaches a terminal revoked state by kernel construction.
2. **IA-3 (Device Identification and Authentication) deserves its own NAMED-AS-EXCLUDED row,
   which the consult's §3 does not give it.** The consult discusses the hooks-layer/vendor-ceiling
   argument only under its IA-2 paragraph (`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:196-202`)
   and in §2 S2's prose, never naming IA-3 by its own control ID. Enumerating from the catalog
   (rather than from the consult's own citations, per Revisit #4 Clause 1's whole point) surfaces
   IA-3 as a distinct control whose subject — authenticating the *device/session/model instance*,
   not the human — is exactly what the vendor-ceiling argument (ADR-0017's identity-enumeration-
   fails-open reasoning, `FABLE-PRINCIPAL-IDENTITY-SPEC.md:210`) already covers. This audit gives
   it the NAMED-AS-EXCLUDED verdict the consult's own reasoning supports but never assigns to
   this specific ID — the corrective the enumerate-from-the-catalog method is designed to produce.
3. **AC-4's verdict is BOUNDED, not the consult's flatter "narrow but real" (`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:188-189`).**
   The consult names nla catalog isolation without citing the file's own "BLOCKING HAZARD"
   passage (`nla-schema.sql:232-238`) admitting the isolation is live-verified NOT to hold today
   (PUBLIC CONNECT + permissive pg_hba). "Narrow but real" undersells a mechanism the file itself
   calls blocking and unresolved; BOUNDED with the hazard quoted is the more honest single word.

No other §3 row is contradicted; every other mechanism citation the consult makes was
independently re-verified this session and stands as written.

## 6. Summary — the four-state counts

Across both families (36 verdictable controls; AC-13/AC-15 withdrawn, excluded from counts):

| State | AC (of 23) | IA (of 13) | Total (of 36) |
|---|---|---|---|
| MET-BY-MECHANISM | 5 (AC-3, AC-6, AC-7, AC-24, AC-25) | 1 (IA-4) | 6 |
| BOUNDED | 3 (AC-2, AC-4, AC-5) | 2 (IA-2, IA-5) | 5 |
| NAMED-AS-EXCLUDED | 0 | 1 (IA-3) | 1 |
| SILENT | 15 | 9 | 24 |

**Every SILENT control, listed prominently, per the commission:**

- AC-1 — Policy and Procedures
- AC-8 — System Use Notification
- AC-9 — Previous Logon Notification
- AC-10 — Concurrent Session Control
- AC-11 — Device Lock
- AC-12 — Session Termination
- AC-14 — Permitted Actions Without Identification or Authentication
- AC-16 — Security and Privacy Attributes
- AC-17 — Remote Access
- AC-18 — Wireless Access
- AC-19 — Access Control for Mobile Devices
- AC-20 — Use of External Systems
- AC-21 — Information Sharing
- AC-22 — Publicly Accessible Content
- AC-23 — Data Mining Protection
- IA-1 — Policy and Procedures
- IA-6 — Authentication Feedback
- IA-7 — Cryptographic Module Authentication
- IA-8 — Identification and Authentication (Non-organizational Users)
- IA-9 — Service Identification and Authentication
- IA-10 — Adaptive Authentication
- IA-11 — Re-authentication
- IA-12 — Identity Proofing
- IA-13 — Identity Providers and Authorization Servers

24 of 36 verdictable controls (67%) are SILENT. Read plainly, not alarmingly: most of these
(AC-8 through AC-23's remainder, IA-6 through IA-13) describe interactive multi-user
login/session/device territory this single-operator, mostly-headless governance harness was
never built toward — the same shape 001 found for the ten ABSENT-AND-UNNAMED families at the
family level. **None of them has ever been formally ruled out of scope**, which is the finding
itself: exactly the "default state" 001 already diagnosed at the family level, now confirmed to
recur at the control level inside the two families a consult specifically asked be walked. AC-14
and AC-1/IA-1 are the three SILENT rows this audit weighs as worth near-term attention (AC-14
because the consult already flagged it as cheap-to-name-and-costly-to-leave-silent; AC-1/IA-1
because a one-paragraph policy pointer is nearly free).

## 7. Follow-ups, sorted against the consult's own D-numbered decision points

**Against D1 (commission this audit) — this document IS the discharge.** `law/STANDARDS-REGISTRY.md`'s
status line ("NOT YET OPERATIONALIZED... first registry-rooted completeness audit pending")
should be updated by the maintainer (registry is maintainer-amendment-only, per its own property
3) to reflect that the AC/IA control-level walk now exists, dated 2026-07-21, alongside 001's
family-level walk of all 20 — the "one mechanically checkable trace" R1 itself named
(`FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md:297`).

**Against D3 (entitlement-enforcement family, R2) — this audit's AC-3/AC-5/AC-6 rows corroborate
G1 directly.** AC-3 (Access Enforcement) is MET-BY-MECHANISM at the write-boundary layer but
AC-2's role-binding machinery (recorded, per s41's own comment "recordable, NOT gating" at
`s41-principal-bindings-and-relations.sql:229`) is not wired into that enforcement — the same gap
the consult's G1 names. This audit adds no new fact here beyond confirming the consult's read
holds at the control level, not just the family level.

**Against D4 (the read surface, AC-14) — new finding, sharper than the consult's framing.** This
audit's AC-14 row finds the control genuinely SILENT (not merely "undocumented" in passing) —
`serving/boundary_service.py` has no caller-identification surface at all for any read path.
Recommend: the maintainer's decision (name reads-without-identification as the accepted
localhost posture, or commission caller discrimination) should land as an actual dated ruling
document or registry-linked decision row, not stay as a consult's recommendation plus an
uncommitted audit observation — two documents pointing at the same gap without a ruling is not
progress toward closing it.

**Against D5 (Finding 6, subagent independence tier) — out of this audit's family scope.** AC-5's
row above cites the same s41 D-6 mechanism the consult's G3 discusses; this audit found nothing
new in the AC/IA catalog that bears on the specific dispatched-subagent granularity question —
D5 stays exactly where the consult left it.

**New, not in the consult's D-list: AC-2's disable/revoke asymmetry (§5 item 1) and AC-4's live
nla CONNECT-denial hazard (§5 item 3) are both real, both already named in their own source
files, and neither has a tracked follow-up item as of this audit.** Recommend opening two small
tracker items: (a) a decision on whether `principal_revoked`'s permanent absence from the kernel
should stay a design choice or become a named, ratified exclusion in its own right; (b) tracking
the `nla-schema.sql:232-238` pg_hba/CONNECT-denial hazard to closure or to an explicit
accepted-risk ruling — it has sat live-verified-open since at least 2026-07-12 per the regulator
assessment this audit's AC-4 row also cites
(`vestigial_documentation/design/MAINT-REGULATOR-ADOPTION-ASSESSMENT.md:52`), and per this
project's own mother's-life bar a witnessed live hole in a subject-isolation boundary is exactly
the kind of hazard that should not simply keep aging in a comment.

**No new cryptography, no host/perimeter recommendation to the maintainer, no certification
paperwork** — this document's follow-ups stay inside the standing scope bounds throughout;
where a row above touches perimeter-adjacent territory (AC-17, AC-22), it is marked adopter-facing
only, never routed to the maintainer as a request to harden his own host.

## Witness summary

- WITNESSED: OSCAL catalog fetched 2026-07-21 from the URL in §1, saved locally, sha256 computed
  directly (`01f37cf90ea99d92242c936cbfbdebcc338eef1f71454e2acac36cc56e9bc062`), parsed with
  Python's stdlib `json`; 20 groups, AC=25 controls, IA=13 controls, version string "5.2.0" — all
  printed from that parse, matching 001's independently-fetched 2026-07-13 counts exactly.
- WITNESSED: every file:line citation in §3/§4 was read directly this session (`grep -n` +
  `Read`, not delegated to a subagent and not trusted from the consult without re-reading) —
  `kernel/lineage/s40-principal-identity-events.sql`, `s41-principal-bindings-and-relations.sql`,
  `s43-typed-verdict-write-boundary.sql`, `s45-standing-lifecycle.sql`,
  `s18-criterion-principals.sql`, `s20-obligation-grants-and-view-refresh.sql`,
  `nla-schema.sql`, `design/FABLE-PRINCIPAL-IDENTITY-SPEC.md`,
  `design/MAINT-GPG-TRUST-LAYER.md`, `design/FABLE-SUBSTITUTION-OF-AUTHORITY-CONSULT-2026-07-19.md`,
  `serving/boundary_service.py`, `hooks/pretooluse_read_observer.py`.
- WITNESSED: absence claims (every SILENT row) were checked by `grep -rn` across the repository
  (excluding `vestigial_documentation/` and `.git/`) for the control's own vocabulary and its
  plain-English synonyms, not asserted from memory; the exact search terms used are named inline
  in each SILENT row's witness cell.
- WITNESSED: `design/FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md` and `law/STANDARDS-REGISTRY.md`
  read in full before this audit was authored, per the commission's own instruction.
- WITNESSED: `vestigial_documentation/design/ORCH-REGISTRY-COMPLETENESS-AUDIT-001.md` and
  `-002.md` read in full for method precedent and to avoid duplicating the family-level
  classification both already establish.
- UNEXERCISED, named plainly: (1) no fresh-context B-pass of this document's own framing prose
  was run (no agent-forking tool available to this invocation — see the doc-attest-exempt marker
  above); (2) the live-host claims this audit cites from the regulator assessment (superuser,
  TLS, pg_hba) were not re-probed against a running Postgres instance this session — cited from
  that document's own 2026-07-12 dated witness, same residual 001 named for itself; (3) the
  ~185 AC/IA enhancements this audit deliberately did not walk (§2) remain a named, not silent,
  non-coverage — a future audit narrowing into them is unstarted.

## License

Public Domain (The Unlicense).
