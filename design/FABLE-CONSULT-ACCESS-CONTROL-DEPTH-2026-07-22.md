# FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22 — the D2–D4 decision series, elaborated to the maintainer's own depth axes

<!-- doc-attest-exempt: ADR-0014 consult deliverable, banked as delivered 2026-07-22
(fidelity is the value; committed 2026-07-26, ledger rows 1377/1378). STATUS CORRECTED at
banking (row 1378): the maintainer REJECTED this document at delivery for a commissioning
defect -- the brief asked for a GENERIC access-control depth treatment covering taint+DMZ
as instances, and the examples became the scope: the deliverable covers exactly taint+DMZ
and nothing generic (the examples-became-the-scope commissioning-defect specimen, third of
its class). Its taint and zone content remains sound AS INSTANCE ELABORATION and is read
that way under the generic frame the later work-gating consult supplied
(CONSULT-WORK-GATING-SHAPE-2026-07-26.md's factored acceptance predicate, whose conjunct
seats are where this document's mechanisms slot). Removal condition: superseded by the
maintainer's D2-D4 ruling or the access-control spec. -->


**Provenance.** Fresh-context Fable consult, commissioned by the maintainer 2026-07-22
(ledger row 1911, near-verbatim: the D-series "needs DEPTH before he can decide — 'you'll
have to go more into detail. I don't think we should be haphazard on this surface of
autoharn. For example, we should service taint semantics for web-using agents (due to PI
[prompt injection]) and DMZ type semantics, and so on; I'll be thinking seriously about this
to address all possible consumers (including NIH, DOD).'"). This document is a
decision-support **elaboration** of the base consult's D2–D4, not a redo of it. Read-only
consult; this file is the one write. Not committed by the consultant.

**Sources read for the record** (paths under `/home/bork/w/vdc/1/autoharn/` unless noted):
design/FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md in full (the base consult; its §7 D-list
is this document's subject); design/AUDIT-AC-IA-POSTURE-2026-07-21.md in full (the corrected
posture matrix: 1 MET / 12 BOUNDED / 3 NAMED-AS-EXCLUDED / 20 SILENT); law/STANDARDS-REGISTRY.md
in full; CLAUDE.md in full; ledger rows 1878, 1880, 1884–1887, 1906, 1911 via `./led show`;
design/FABLE-CONSULT-EPISTEMIC-DOXASTIC-SUBSTRATE-2026-07-22.md in full (the belief
substrate whose basis/testimony vocabulary §2 composes with);
kernel/lineage/nla-schema.sql in full including its BLOCKING-HAZARD comment (lines 232–241);
kernel/lineage/s43-typed-verdict-write-boundary.sql, s44-model-identity-attestation.sql,
and s51-artifact-store.sql headers; kernel/lineage/s15-schema.sql review machinery;
hooks/pretooluse_read_observer.py and hooks/pretooluse_delegation_observer.py headers
(the observability facts §2 rests on); .claude/settings.json (this repo's own hook wiring).

**One epistemic disclosure, stated first because the audit two-bias rule (row 1887) demands
it of exactly this document's §1:** the consumer-class characterizations in §1 are drawn
from this consultant's training knowledge of the named frameworks (NIST SP 800-171/172,
CMMC, DoD SRG, 21 CFR Part 11, NIH controlled-access data policy), **not** from
authoritative-source fetches performed this session. They are decision-support
characterizations of what those consumers' reviewers typically demand — input to the
maintainer's D2 registry decision — and are marked UNWITNESSED-AT-SOURCE throughout. If any
of them becomes a registry entry, the registry rule takes over: the actual audit enumerates
from the standard's own catalog, fetched and pinned, exactly as the AC/IA audit did. Nothing
in §1 is a satisfaction or absence claim about those standards; where §1 says "the matrix
would read to them as X," that is a claim about the matrix (read in full this session), not
about the standard's clause text.

---

## 0. Summary

Four consumer classes are characterized (§1): NIH-grade research infrastructure, defense-grade
(DoD SRG / 800-171 / CMMC-shaped), commercial-regulated (21 CFR Part 11-shaped), and
open-source adopters. The one-line headline per class: **research reviewers would find the
posture unusually honest and mostly sufficient once AC-20 and information-flow are named;
defense-grade reviewers would find the audit-trail core strong and the information-flow /
external-content story absent — taint and DMZ are precisely the two mechanisms that
distinguish "research prototype" from "adoptable in that world"; Part 11 reviewers would find
the e-signature and audit-trail shape nearly clause-adjacent already; open-source adopters
consume honest defaults and named holes, both of which exist.** §2 derives taint semantics
for web-using agents in this system's own terms: a session-granularity, hook-witnessed
exposure mark, composed with the belief substrate as a *derived provenance predicate over the
basis DAG* (never a stored bit, never a fifth basis) and with s43 as flag-in-v1,
gate-only-after-D3. §3 derives DMZ semantics: the project already has three zone-shaped
mechanisms (nla catalog isolation, worktree isolation, fresh-context consult convention);
the smallest honest v1 is *declared zones at dispatch + the s51 artifact store as the
airlock between them*, with DB-role-enforced zoning named as the real v2 and the nla
BLOCKING HAZARD named as the standing proof that declared zones without connection-level
confinement do not isolate. §4 re-presents D2–D4 with per-class readings, costs, seams, and
recommendations with confidence. Nothing here asks for new cryptography, host/perimeter work
on the maintainer's machine, or any retroactive change; every proposed record names its
consumer (row 1906).

---

## 1. Consumer classes — what each one's reviewers would demand of THIS surface

Method note: each class gets (a) the demand profile its reviewers bring to an
access-control surface, (b) which registry entries (present or candidate) those demands map
to, and (c) what the corrected posture matrix — 1 MET-BY-MECHANISM / 12 BOUNDED /
3 NAMED-AS-EXCLUDED / 20 SILENT across 36 verdictable AC+IA controls — would read as to
them. Consumer of this whole section, named: **the maintainer, deciding D2** (which
measuring sticks enter law/STANDARDS-REGISTRY.md). Characterizing a class commits the
project to nothing; the no-certification-bureaucracy ruling stands — the question is which
sticks to measure against, never which paperwork to produce.

### 1.1 Research-institution grade (the NIH shape)

**Who the reviewer actually is:** a data-governance office or information-security officer
evaluating whether a tool may touch controlled-access or human-subjects-adjacent data, plus
an IRB asking narrower questions (who accessed what, can the audit trail support an
incident inquiry, is data flow to third parties controlled). UNWITNESSED-AT-SOURCE, from
training knowledge: NIH's controlled-access data policy has been converging on NIST
SP 800-171-shaped attestations for institutions holding such data, and FISMA/800-53
moderate-baseline expectations apply to systems NIH itself operates or funds as
infrastructure.

**Demand profile on this surface:** (1) a reliable, protected audit trail of who did what
(800-53 AU family, AC-2, AC-6); (2) demonstrable control of data flow to external parties —
and for an AI harness, "the model vendor" IS the external party (AC-4, AC-20, SA/SR-adjacent);
(3) account lifecycle with deprovisioning; (4) a written answer, not necessarily machinery,
for every control in the baseline ("not applicable, because…" is acceptable; silence is not).

**Registry mapping:** entirely inside the existing NIST SP 800-53 entry, plus SP 800-171 as
the candidate entry if controlled-access data hosting is ever a real deployment target.

**How the current matrix reads to them:** better than its raw counts suggest. The AU-side
core (append-only, hash-chained, refusals committed as evidence, signed heads) is the part
of this project that exceeds what research reviewers usually see. The 12 BOUNDED rows with
per-clause residuals are exactly the artifact style such a review consumes. The problems are
the 20 SILENT rows read as a category — a governance office's checklist treats silence as
failure regardless of applicability — and specifically **AC-20 (Use of External Systems),
the audit's own named most-live SILENT row**: this system routes all governed work through
an external AI vendor and says nothing typed about it. For this class, converting the
SILENT set into named-N/A rows plus a real AC-20 posture statement closes most of the gap
without building anything. Taint semantics (§2) is a differentiator here, not a
prerequisite: it is the mechanism that would let a data-governance reviewer see that
web-derived (or any external) content entering an agent's context is *tracked*, which is a
stronger answer than any policy paragraph.

### 1.2 Defense-grade (DoD SRG / NIST SP 800-171/172 / CMMC shape)

**Who the reviewer actually is:** an assessor working a controls checklist with low
tolerance for unnamed gaps (CMMC L2 ≈ 800-171's 110 requirements; L3 adds 800-172's
enhanced set), and, for anything connected, an authorizing official reasoning in impact
levels and boundary diagrams. UNWITNESSED-AT-SOURCE, from training knowledge: this world's
distinctive vocabulary is exactly the maintainer's two named axes — *cross-domain thinking*
(content moving between trust domains passes inspection/filtering at a guarded boundary:
the DMZ/CDS ancestry of §3) and *marking/flow control* (data carries labels; flow between
labeled domains is enforced, AC-4/AC-16 territory). Post-2023 DoD generative-AI guidance
additionally treats untrusted content reaching a model's context — prompt injection — as a
first-class threat vector, which is precisely the maintainer's PI concern.

**Demand profile on this surface:** (1) enforced information flow between trust zones, with
the zones drawn and the crossings enumerated (AC-4 and its enhancements); (2) marking:
external/untrusted content identifiable as such wherever it propagates (AC-16); (3) least
privilege enforced per role, not just per DB grant (AC-3/AC-6 — the D3 gap, verbatim);
(4) multifactor and device authentication (IA-2 enhancements, IA-3) — where this project's
honest answer is the argued vendor-ceiling exclusion, which an assessor can accept only as
a documented deviation, never as silence; (5) incident-relevant forensics: when a
compromise via injected content is suspected, the record must support "which acts happened
downstream of the exposure" — which is taint's RCA consumer, named.

**Registry mapping:** 800-53 (present) covers the control vocabulary; 800-171 is the
candidate entry that would make this class's checklist auditable; 800-172 and CMMC are
process shells around the same requirements and are exactly the certification bureaucracy
the quality-bar ruling rejects — mechanisms from them, paperwork never.

**How the current matrix reads to them:** split verdict. The evidentiary core (s26/s42/s43:
tamper-evident chain, sole write path, refusals as committed evidence, AC-24 MET) is
genuinely strong by this world's standards — reference-monitor-shaped write enforcement
with the decision record inside the trust boundary is the part assessors rarely get.
Everything zone-and-flow-shaped is absent or admittedly broken: AC-4 is BOUNDED *with a
live-verified isolation failure quoted in its own witness cell* (nla BLOCKING HAZARD),
AC-16 and AC-20 are SILENT, entitlement is recorded-not-gating, and there is no zone
concept at all for the agents themselves. For this class, §2 and §3 are not enhancements;
they are the admission ticket. Stated with confidence high on the reading, and stated
plainly: nothing obliges the project to serve this class — but the maintainer named it, and
the honest report is that taint + DMZ + D3 are the three mechanisms between here and there,
in that dependency order's reverse (D3 first, because both others want its enforcement
point).

### 1.3 Commercial regulated (FDA 21 CFR Part 11 shape)

**Who the reviewer actually is:** a quality/validation auditor asking whether electronic
records and signatures are trustworthy: computer-generated time-stamped audit trails that
cannot be modified without trace, signature-to-record binding that cannot be excised,
operational system checks, and validation evidence. UNWITNESSED-AT-SOURCE, from training
knowledge; Part 11 is also already in this project's bloodstream — the founding brief's
source set, and the base consult's observation that the GPG SIGNED rung "already matches
almost clause-for-clause" (base consult §3).

**Demand profile → matrix reading, together because they nearly coincide:** append-only +
full-column hash chain + signed heads + refusals-as-records is the Part 11 audit-trail
requirement exceeded; human GPG signature at deliberate moments with the signature bound
into the signed content is the e-signature shape; the typed-verdict boundary is the
"operational system check." The residuals a Part 11 auditor would press: account lifecycle
(the AC-2 disable/revoke asymmetry — a liftable suspension with no terminal revocation is a
design choice they would want named), authority checks (D3 again — Part 11 wants "authority
checks to ensure only authorized individuals can use the system, electronically sign,
access the operation" — that is entitlement enforcement, almost verbatim), and validation
records (which the both-polarity scratch-witness discipline substantially IS, unlabelled).
This is the class the project is accidentally closest to. Registry mapping: Part 11 as a
bar is a cheap, high-yield D2 entry *if* this consumer class is real for the maintainer.

### 1.4 Open-source adopters

**Who the reviewer actually is:** nobody, which is the point — there is no assessor, so the
project's own documents are the entire review. This class consumes: secure defaults, holes
named where they stand (the nla hazard comment is exemplary — a BLOCKING HAZARD stated in
the file that creates the hazard's precondition), adopter-facing guidance for the things
excluded on the maintainer's own machine (perimeter, pg_hba, remote access), and the
install-vs-fallback honesty the project already holds as a founding motivation.

**Matrix reading:** the honest-partial posture is exactly right for this class as-is; what
they lack is the adopter-facing paragraph per excluded control (AC-17's own row already
anticipates this: "adopter-facing residual preserved"). D4's naming act is mostly *for*
this class. Taint and DMZ, if built, must ship with the same install-vs-fallback surfacing:
a world that doesn't wire the web-exposure observer should know it is running without one.

*Confidence for §1 overall: high on the matrix readings (matrix read in full this session);
medium on the per-class demand profiles (training knowledge, marked UNWITNESSED-AT-SOURCE;
directionally stable frameworks, but any registry adoption re-derives from source).*

---

## 2. Taint semantics for web-using agents (the prompt-injection axis)

### 2.1 The threat, in this system's terms

Prompt injection is, in this project's own vocabulary, **an unregistered principal speaking
through a registered one.** A web page fetched into an agent's context can carry
instructions; the agent's subsequent acts are attributed (s40, honestly) to the agent's
principal, but their *authorship* may be partially the page's. The kernel's attribution
machinery is not wrong — the session really did perform the act — but a reader of the
record cannot currently distinguish "this verdict was formed from repository evidence" from
"this verdict was formed after ingesting arbitrary external text." That distinction is
exactly what taint tracking supplies, and note what it is: **a provenance fact about an
act's context, not an accusation.** Most web-exposed acts are fine. The mark exists so that
the ones that are not fine are findable afterward, and so that crediting policy *may* weigh
exposure — the same carried-but-unread posture as `confidence` and `attest_grade`.

### 2.2 What the hooks action stream can and cannot observe (the honest floor)

Guarantees rest on the hooks action stream (standing principle, 2026-07-11). Facts, from
reading the hook layer this session:

- **CAN observe: every harness web-tool invocation.** PreToolUse/PostToolUse hooks match on
  tool name; `WebFetch`/`WebSearch` calls deliver tool input (URL/query) and, at
  PostToolUse, the response. No hook currently matches them — searched `hooks/*.py` for
  `WebFetch`/`WebSearch`/`web` this session, zero hits; this repo's own `settings.json`
  wires only `stamp_provenance` on edit tools — so today the exposure event exists nowhere.
  A `web_exposure_observer` in the exact mold of `pretooluse_read_observer.py` (journal ts,
  session, URL, and — at PostToolUse — a sha256 of the fetched content; costless, observer-
  only, apparatus.json switchboard) is the buildable floor. The read observer's own header
  is the precedent: it exists to convert "trusted claim" into "witnessed record," which is
  verbatim the job here.
- **CAN observe, with named leakage: web access via Bash.** `curl`/`wget`/`python -c
  urllib` in a Bash tool call is web exposure the tool-name matcher never sees. Command-line
  classification is enumeration, and enumeration fails open (ADR-0011 Rule 4) — a static
  pattern list over Bash commands is a worthwhile *weak additional tier* (the
  demurral-detector static-tier precedent, disclosed-as-weak by design), never the
  guarantee. The honest statement: **hook-level taint marking is complete over the
  harness's typed web tools and best-effort over Bash.** A zone-level answer (§3: deny
  network egress to kernel-zone agents by sandbox policy) is the only way to close the Bash
  channel, and it belongs to DMZ, not taint.
- **CANNOT observe: propagation inside the model.** Once tainted bytes enter a context
  window, the harness has no visibility into which subsequent tokens they influenced. So
  the honest granularity is **session-level and monotone**: a session is untainted until
  its first web exposure and tainted thereafter; every act after the mark is
  "tainted-context," with no claim about which acts were actually influenced. Token-level
  taint is unbuildable here and this document does not pretend otherwise.
- **Partially observable: cross-session propagation via files.** A tainted session writes a
  file; a clean session reads it. The mutation/provenance hooks journal the write, the read
  observer journals the read — so file-mediated taint transitivity is *computable from the
  journals*, but journals are local, non-hash-chained diagnostics (the action-stream
  principle's own grading). v1 should name this: cross-session taint closure is
  diagnostic-grade; intra-session marking is the evidentiary product.

### 2.3 Composition with the belief substrate (basis/testimony vocabulary)

The belief consult's spine — basis ∈ {observed, derived, testimony, assumed} with mandatory
edges — composes with taint cleanly, provided one temptation is refused: **taint is not a
fifth basis and not a stored bit on the belief row.** Basis types the *justification
structure* of an assertion; taint is a *provenance attribute of the asserting act's
context*. Storing "tainted" on the row would be a second writer of a derivable truth (the
substrate's own cancer-B argument, §3.0 there): given (a) exposure events keyed by session
and time and (b) every row's `stamp_session` + `ts`, taintedness of any row — and, via the
substrate's premise/testimony DAG, of any belief's full basis closure — is a **derived
predicate**, computed fresh, never stored:

- `tainted_context(Row)` — the writing session had a web exposure at an earlier ts.
  (EDB: a new `web_exposure(Session, Ts, ArtifactHash)` fact family, capability-gated
  PRODUCED | CAPABLE | DEFERRED per the F49 discipline, so a world without the observer
  reports "cannot know," never a silent clean.)
- `taint_reachable(Belief)` — some row in the belief's premise/testimony/witness closure is
  `tainted_context`. This is the same transitive-closure query as the substrate's
  `shared_premise` view, on the same edges — ASP home ground, one rule.
- Web content itself, when it becomes *evidence* rather than mere exposure, enters the
  record the way the substrate already demands: banked to the s51 artifact store
  (content-addressed, size-capped) and cited as `basis=testimony` with the artifact as
  source — the fetched page is testimony from an unregistered, unvetted source, and the
  type says so. The exposure journal's content-sha256 and the s51 hash coincide by
  construction when the content is banked, which gives the taint mark a resolvable witness.

Consumers, named (row 1906): `tainted_context` — the maintainer or an auditor running a
suspected-PI RCA ("which acts happened downstream of the exposure"); `taint_reachable` — a
reviewer or crediting rule deciding how much to credit a verdict whose evidentiary
ancestry includes web-derived content; the banked artifact — the same RCA, needing the
actual bytes that entered the context, tamper-evidently.

### 2.4 Composition with s43 (flag vs gate), and the registry rows it moves

**v1: flag, never gate.** The write boundary stays untouched; taintedness is a derived
view beside `credited`/`corroboration`, displayed with cause (the credited-view display
contract). Gating — refusing or specially-journaling a countersign from a tainted-context
session — is the same mechanism shape as D3's entitlement gating: an acceptance predicate
over in-force facts, evaluated inside the boundary functions. It should therefore arrive,
if ever, as a *policy input to the D3 machinery* (one more conjunct in a factored
acceptance predicate, per-world-configured via the s36 graded-token idiom), not as its own
parallel enforcement path. One honest asymmetry to record: exposure events would be
hook-authored (a tool-principal write through the boundary, the s43 `write-boundary`
precedent), which means a kernel-side gate consumes hook-side facts — the guarantee is
exactly as strong as the action stream, and a world that disabled the observer has silently
disabled the gate. F49's PRODUCED/CAPABLE/DEFERRED declaration is what keeps that failure
loud instead of silent, and it is load-bearing here, not decorative.

**Matrix rows this moves** (the D2-relevant payoff): AC-4 (information flow — the first
flow-*tracking* mechanism for the agent layer, strengthening a row currently BOUNDED on the
nla mechanism alone); **AC-16 (Security and Privacy Attributes — currently SILENT: a taint
mark is precisely an attribute bound to information, the control's own subject)**;
**AC-20 (Use of External Systems — currently SILENT and the audit's named priority: the
exposure record plus the banked-content path is a typed posture toward external content,
the beginning of an AC-20 answer)**; and it supplies the forensic substrate the defense
class's incident demand (§1.2 item 5) consumes.

*Confidence: high on the derivation (session-granularity, derived-never-stored, hook floor
— each follows from a standing principle read this session); high on the honest limits;
medium on v1 scope (the Bash static tier could reasonably be v1 or v2).*

---

## 3. DMZ-type semantics

### 3.1 What a DMZ means for agent infrastructure

The network DMZ's essence, transposed: **a zone whose occupants touch the untrusted
outside, structurally prevented from touching the trusted inside, with all crossings
passing through a narrow, inspected, typed interface.** For this system the trust gradient
is not network segments but *what an agent's context has ingested and what its credentials
can reach*. Three zones fall out of the existing work almost without invention:

- **Z-WEB (web-touching agents):** may fetch external content; context presumed
  taintable; must not hold kernel write capability. Deep-research-style consults, doc
  fetchers, dependency investigators live here.
- **Z-KERNEL (kernel-writing agents):** may write through the s43 boundary (`./led`,
  boundary functions); must not fetch external content — no network egress beyond the
  vendor API itself (which is the named, unavoidable vendor seam, not a zone violation).
  Orchestrators, builders, the commit path live here.
- **Z-REVIEW (consult/review agents):** fresh-context by construction, read-mostly, one
  deliverable write, no ledger writes, no web unless the commission grants it. The house
  already runs this zone by convention — this very consult's bounds are its membership
  card. The nla subject is a fourth, stricter zone (Z-SUBJECT), already database-enforced.

### 3.2 What already exists that is zone-shaped (read this session)

1. **nla catalog isolation** — the real thing, one zone deep: a separate database so the
   subject role *physically cannot* read the apparatus catalog (nla-schema.sql:12). And its
   BLOCKING-HAZARD comment (lines 232–241) is the single most instructive artifact in this
   whole section: catalog isolation held, **and isolation still failed live**, because
   PostgreSQL grants CONNECT to PUBLIC by default and the local pg_hba admits every role to
   every database — `psql -U nla_rw -d epistemic` read the entire apparatus catalog,
   verified live, confinement requiring an out-of-reach pg_hba/CONNECT change. The lesson,
   generalized and load-bearing for everything below: **a zone is only as real as the
   credential/connection layer beneath it; a declared zone with shared credentials is
   documentation.** (This hazard is already flagged to the maintainer — audit §7, row 1880
   — and per the standing bounds this consult does not re-raise host configuration; it
   cites the hazard as the witnessed design lesson it is.)
2. **Worktree isolation** — filesystem zoning for concurrent builders (standing rule after
   the 2026-07-19 scope-bleed incident): per-agent git worktrees, an isolation the dispatch
   machinery can grant at dispatch time. Same shape, different resource.
3. **The fresh-context consult convention (ADR-0018)** — context zoning: the consult sees
   the problem and the LAW, not the orchestrator's candidate answers. Enforced socially,
   observable in the dispatch journal, not mechanized.
4. **s43's tool principal + s51's artifact store** — the narrow-interface half: writes
   cross into the kernel only through five typed functions, and content crosses zones
   custody-grade only as content-addressed, size-capped artifacts. s51 is the natural
   **airlock**: a Z-WEB agent's findings enter Z-KERNEL as a banked artifact plus a
   testimony-basis record citing it — typed, hashed, inspectable — never as prose pasted
   into an orchestrator's context. (Pasting findings into the orchestrator IS a zone
   crossing without inspection; the airlock does not prevent it — see limits below — but
   gives the compliant path a mechanism.)

### 3.3 Boundary crossings in the dispatch/hook machinery, and declarability

Dispatch is the zone-assignment moment, and it is already observed: the delegation observer
journals every Agent/Task dispatch (ts, session, description, prompt sha+excerpt) and
already warns toward a `decision` row answering "what is delegated, why." Zone membership
is **declarable today** with zero new machinery: the dispatch decision row states the
zone (`zone=web|kernel|review`), and the subagent's toolset is constrained to match (the
harness's per-agent tool restriction — e.g. review agents without write tools, a shape the
project has already used and even ledgered: the migrated "report-only-means-no-write-tools"
rule). What is **observable** is whether the session then behaved as declared: the
delegation journal names the dispatch, the web-exposure journal (§2) names web use, the
read/mutation journals name file traffic, the ledger names kernel writes — a
zone-conformance check is a join over records that (given §2's observer) all exist.
What is **enforceable**, in three honest grades:

- *Grade 1, harness-level (buildable now):* tool restriction at dispatch (no
  WebFetch/WebSearch for Z-KERNEL agents; no write tools for Z-REVIEW) plus sandbox
  network policy for the Bash channel where the harness supports it. Real enforcement, but
  configuration-grade: it constrains the dispatched agent, and its evidence is the dispatch
  record, not a kernel refusal.
- *Grade 2, hook-level (buildable now, observer-first per house rule):* a PreToolUse
  matcher that warns — later, if ever sanctioned, denies — when a session's journaled zone
  declaration conflicts with the attempted tool (a declared-Z-WEB session invoking `./led`
  write verbs; a declared-Z-KERNEL session invoking WebFetch). The delegation observer's
  own header shows both the pattern and the house's deliberate never-blocks posture; a
  deny path is a maintainer sanction, not a default.
- *Grade 3, credential-level (the real thing; v2+):* per-zone DB roles, so a Z-WEB
  session's credentials cannot reach the boundary functions at all — the nla precedent
  applied to the operator side. This is where the BLOCKING-HAZARD lesson binds: without
  connection-level confinement it reduces to Grade-2 theater. Adopter-facing guidance can
  say all of this plainly (pg_hba per zone role); for the maintainer's own machine it stays
  unraised per the standing ruling.

### 3.4 The smallest honest v1 of zoning

Three pieces, each with its consumer named (row 1906):

1. **Zone vocabulary + declaration at dispatch** — the closed zone vocabulary documented in
   one place; the dispatch decision row carries the zone; the subagent's toolset matches
   it. Consumer: the orchestrator's own dispatch policy at dispatch time, and the
   post-incident RCA asking "was this agent supposed to be able to do that."
   Cost: a documentation page and an orchestration habit; zero kernel surface.
2. **The web-exposure observer (§2's v1)** — without it, zone conformance for the one zone
   the maintainer named (web-using agents) is unwitnessable. Consumer: the
   zone-conformance check and the taint RCA, jointly.
3. **The airlock convention** — cross-zone deliverables travel as s51 artifacts cited by
   testimony-basis records, not as pasted prose. Consumer: the reviewer of any Z-WEB
   product deciding what to credit, who gets a hash-addressed object instead of an
   orchestrator's paraphrase (the commissions-verbatim lesson, mechanized at the zone
   boundary). Cost: convention plus the already-built s51.

Honest limits, named: v1 zoning is *declared and witnessed*, not *enforced* — an agent in
the orchestrator's own session is in whatever zone the orchestrator's session is in, and
the orchestrator reading a Z-WEB agent's report ingests its text (a context crossing no
airlock prevents; the mitigation is the airlock convention making the compliant path
cheaper than pasting, plus taint marks making the crossing visible). Grade-3 enforcement is
the v2 that makes zones real in the nla sense, and it inherits the nla hazard's whole
lesson. This staged honesty — declared now, witnessed now, enforced later — is the same
arc s41 walked for entitlements (recordable v1, gating as the named follow-on), which is
why §4's D3 seams matter.

*Confidence: high on the zone decomposition and on what exists (all read this session);
high on the v1 shape being the lagom floor; medium on Grade-2 deny ever being wanted —
observer-first has served the house well and the deny path should wait for a witnessed
need.*

---

## 4. D2–D4, re-presented in the deeper frame

### D2 — Registry amendments (the maintainer's file, his word alone)

**The decision, restated with §1's depth:** which measuring sticks enter
law/STANDARDS-REGISTRY.md, knowing each entry obligates a future registry-rooted audit
(enumerate-from-catalog, pinned source) and forecloses silent absence — and knowing the
consumer classes he intends to address.

**Options and per-class reading:**

| Option | Research (NIH) | Defense (DoD) | Part 11 | OSS adopters | Cost shape |
|---|---|---|---|---|---|
| (a) Add **NIST SP 800-63** | neutral-positive | positive (IAL/AAL vocabulary for the IA exclusions) | neutral | positive (names the identity design's own stick) | Low: one audit of a family the identity layer already speaks |
| (b) Add **21 CFR Part 11** as a bar | positive where FDA-adjacent | neutral | the admission ticket | neutral | Low-medium: small clause set, GPG/audit-trail work already near it |
| (c) Add **NIST SP 800-171** | increasingly expected for controlled-access data | the checklist their assessors run | neutral | neutral | Medium-high: 110 requirements, a real audit commitment |
| (d) Add nothing; keep 800-53 alone | acceptable if SILENT set gets named | reads as not-serious about the class he named | misses a near-free match | acceptable | Zero now; the depth commission's intent unserved |

**Recommendation:** (a) now — the base consult's own argument stands and nothing this
session weakened it: 800-63 is already the de-facto design vocabulary and is currently
sweep-proof (confidence: high). (b) if and only if the commercial-regulated class is a real
target — it is the cheapest real entry relative to existing mechanism (confidence: medium,
because the "if" is the maintainer's market judgment, not an engineering fact). (c) **as a
staged entry**: enter it when either a research-data or defense-class adopter is concrete,
and until then have the taint/DMZ/D3 mechanisms — which are 800-171-shaped work in
substance (3.1 access control, 3.13 system/communications protection analogues) — accrue
toward it; entering it today buys an audit obligation ahead of any consumer who would read
the result (the named-consumer test, applied to the registry itself: an audit row's
consumer must exist) (confidence: medium-high). Against all four: registry entries are
sticks, not paperwork; none of this proposes producing a certification artifact for
anyone.

### D3 — Ratify authoring of the entitlement-enforcement family

**The decision, restated:** commission a Fable-authored, maintainer-ratified spec gating
countersign/review/commission acceptance on an in-force `principal_role_bound` event
(scaffold binds birth roles explicitly; competence stays recordable-only). Kernel-semantics
change; future births only; not class-ratified fail-safe (it makes previously-accepted
writes refusable) — routes to the maintainer by the contract's own rule.

**Per-class reading:** this is the one D-item every class demands in nearly the same
words. Research/defense: AC-3/AC-6's "who MAY," the matrix's most-corroborated gap (three
BOUNDED rows cite it). Part 11: "authority checks" nearly verbatim. OSS adopters: the
difference between a governance kernel that records roles and one whose roles mean
something. The audit's §7 already found AC-3/AC-5/AC-6 corroborating G1 at control level;
nothing this session weakens that — this consult independently reaches the same
recommendation as the base consult's R2 (noting honestly: same model lineage, so this is
same-class corroboration in the belief substrate's own grading, not cross-class).

**Composition with taint/DMZ if adopted later — the seams, no dependency built:**

1. **One acceptance predicate, factored for conjuncts.** The spec should shape the boundary-
   side check as a conjunction of typed predicates over in-force facts — v1 containing
   exactly one conjunct (role binding for the act). Zone membership (an in-force
   zone-declaration fact) and taint policy (no countersign from a tainted-context session,
   or journal-specially) are then later conjuncts entering by their own ratified deltas
   through the same enforcement point — no second gate, no parallel path. The seam is the
   factoring, not any reference to taint or zones in the D3 spec.
2. **Per-world policy via the s36 idiom.** Which conjuncts are armed, and at what
   strictness, is deployment configuration reading kernel-stored typed tokens — so a
   solo world runs role-gating alone at zero added friction while a defense-shaped
   deployment arms all three, without kernel divergence.
3. **Refusal vocabulary sized for successors.** `refusal_surface`/teach-text conventions in
   the D3 spec should anticipate sibling refusal reasons (entitlement-refused today;
   zone-refused, taint-refused if ever) as vocabulary additions, which are class-ratified
   fail-safe by the standing rule — the expensive ratification is spent once, on the
   enforcement point.

**Recommendation:** yes, ratify authoring now, role-binding scope only, with the factored-
predicate seam written into the commission. Every path in this document that ends in
enforcement passes through this point; building taint or DMZ enforcement before it exists
would mint a second enforcement locus and violate the one-home discipline. (Confidence:
high on yes-and-scope — unchanged from the base consult and now corroborated by the audit;
high on the seam shape — it is the house's existing pattern, not an invention.)

### D4 — The read surface (AC-14)

**The decision, restated:** record reads-without-identification as the named, accepted
posture (localhost + adopter-facing paragraph), or commission caller discrimination now.
The audit sharpened the stakes: two documents now point at the gap without a ruling, and
its §7 asks for an actual dated decision row, not a third recommendation.

**Per-class reading:** research and defense reviewers both eventually require identified
reads for multi-party deployments — but both consume a *documented* AC-14 decision with a
stated revisit trigger as a fully respectable answer for a single-operator localhost
system; that is what AC-14 exists for. Part 11: read-access identification is not its
center of gravity; the named posture suffices. OSS adopters: the adopter-facing paragraph
is the actual deliverable — "this boundary service identifies no callers; here is what
that means for your deployment and what to put in front of it."

**Composition with taint/DMZ:** zoning changes the read surface's *description*, not the
D4 answer — the one enforced read control (nla: the subject cannot read the operator
kernel) is a zone boundary already, and Grade-3 zoning would add per-zone read scopes as a
natural extension. The D4 ruling should therefore state its revisit triggers explicitly:
**(i) any deployment serving a second party; (ii) adoption of credential-level (Grade-3)
zoning, which supplies caller discrimination as a side effect.** Consumer of the ruling,
named: the AC-14 matrix row's future auditor (who gets NAMED-AS-EXCLUDED instead of
SILENT), and the adopter reading the paragraph.

**Recommendation:** name it now — one dated decision row plus the adopter paragraph, with
the two revisit triggers in the ruling's own text; build nothing. (Confidence: high;
unchanged from base consult and audit, now with the triggers that keep the naming honest
under the futures §2–§3 open.)

---

## 5. Bounds respected, and what this document deliberately does not cover

No host/perimeter recommendation to the maintainer is made anywhere above (the nla hazard
and pg_hba appear only as cited existing flags and adopter-facing material). No new
cryptography: taint marks are derived predicates over hook journals and existing hashes;
zones are declarations, tool restrictions, and existing DB machinery; s51 hashing is
already built. Runs are linear: everything kernel-touching reaches future births only.
Every proposed record and mechanism carries a named consumer inline (§2.3, §3.4, §4).
Absence claims in this document name their searched surfaces (§2.2's hooks search; the
testimony-vocabulary search that located the belief consult). Not covered, named: the SC
and SR families (the natural 800-53 homes for much of §2–§3 — the AC/IA audit's method
extends to them and a defense-class future would want them walked); enhancement-level
audit depth (row 1883's follow-up, untouched here); any live-world change; and the
maintainer's actual market judgment about which consumer classes are real — §1
characterizes them so that judgment can be made, and stops there.

*Point-in-time consult record, 2026-07-22. Not committed by its author (consult bound);
superseded by any maintainer word and by whatever specs follow his D2–D4 rulings.*
