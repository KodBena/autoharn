# FABLE-CONSULT-ACCESS-CONTROL-2026-07-21 — access control as a first-class concern: decomposition, posture, direction

<!-- doc-attest-exempt: banked consult verbatim; the standing rule is that consult
transcripts/documents are preserved as delivered -- fidelity IS the value. -->

**Provenance:** fresh-context Fable consult (ADR-0018-shaped: the witnessed problem, its
evidence, and the LAW only; no orchestrator candidate answers received). Commission, verbatim:
*"can we have a Fable consult on what we should do with access control as a first-class
concern?"* A maintainer addendum arrived mid-consult, verbatim: *"a specific concern you need
to address is what the various standards we hold ourselves to (NIST etc) have to do with
access control that we should be concerned about given the purpose of this project (so:
specifics relative to standards)"* — §3 carries it. Read-only consult; this file is the one
write. Not committed by the consultant.

**Sources read for the record** (all paths under `/home/bork/w/vdc/1/autoharn/` unless noted):
CLAUDE.md; ADR-0000 in full (incl. the 2026-07-02 closure-statement amendment and Revisit #4);
ADR-0011 in full; ADR-0016 in full; ADR-0018; ADR-0002/0012/0013/0017 by section map and via
their load-bearing citations throughout the corpus (named honestly: not line-by-line this
pass); law/STANDARDS-REGISTRY.md in full; design/FABLE-PRINCIPAL-IDENTITY-SPEC.md in full
(C1–C13); design/FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md in full;
design/MAINT-GPG-TRUST-LAYER.md in full; design/FABLE-SUBSTITUTION-OF-AUTHORITY-CONSULT-2026-07-19.md
in full; kernel/lineage/ headers for s40, s41, s43, s44, s45 and targeted reads of s17/s18/
s20/s21/s26/nla-schema; bootstrap/new-project.sh's LINEAGE_CHAIN; serving/boundary_service.py's
header and auth surface; tools/setup_tui/signed_genesis.py's header;
/home/bork/w/vdc/1/test/blank/AUTOHARN_BACKFLOW.md findings 1 and 6.

**One correction to the commission's own evidence framing, stated first:** the commission
describes the s40/s41 identity-events family as "ratified, not yet built." That was true of
the spec's era; it is no longer true of the repository. The lineage now runs to **s52**, and
`bootstrap/new-project.sh:246` wires s40–s52 into every future world's birth chain — including
s43 (the typed-verdict write boundary, i.e. the ratified refusal-recording direction, BUILT)
and s44 (model-identity attestation, BUILT). All of it reaches only future worlds
(runs-are-linear); the current live world remains a fourteen-kind kernel. This consult is
therefore not "should we build an identity layer" — that ship has been built and docked at the
next birth. The honest question is narrower and different: **what of access control remains
undone, unnamed, or unenforced after s40–s52, and what is deliberately out.**

---

## 0. Summary

Access control decomposes here into six senses (§1). Of them, **attribution, enforcement
locus, and audit-of-writes are strong and built** (s40/s43/s26+s42); **authentication is
honestly thin by design** (human GPG at three moments; everything else declared, stamped, or
attested — never authenticated, and the specs say so); **authorization — whether a principal
MAY perform the act its identity is bound to — is the one sense that is recorded but nowhere
enforced**: role bindings and competence grants exist as events and gate nothing
(kernel/lineage/s41:114, 229, 642 — "recordable, NOT gating," named follow-on). The
registry-rooted NIST 800-53 completeness audit that would make all of this a posture matrix
instead of a scatter is still pending (law/STANDARDS-REGISTRY.md:35). My recommendation, in
order: (1) run that audit for the AC and IA families now — it is the mechanism the LAW already
mandates and the maintainer's own "start from the conformance-to-standards view" ruling
(ledger row 1378) already shaped; (2) ratify authoring of the entitlement-enforcement delta
family (the D-5 follow-on s41 itself names), scoped to role-binding-gated countersign/review,
with competence staying recordable; (3) dispose of two small named items (the subagent
independence tier from the downstream finding 6; the unauthenticated read surface as a named
AC-14-style decision); (4) build nothing cryptographic beyond what exists, and touch nothing
the standing rulings exclude. Decision points prepared in §7. Confidence per section at each
section's end.

---

## 1. What "access control" means for THIS system

The term arrives from a world of multi-user confidentiality systems. This project is not one.
Its purpose — the kernel as an append-only, tamper-evident governance record for AI-agent work
under a single human maintainer, with guarantees resting on the hooks action stream and the
kernel write boundary — makes access control here primarily an **integrity and honesty**
concern, not a confidentiality one. The adversary model, stated plainly: not an outside
intruder (host/perimeter is excluded by standing ruling, 2026-07-12), but (a) the apparatus's
own agents drifting, overclaiming, or being silently substituted; (b) a future outside reader
who must be able to trust the record without trusting the host; (c) the honest operator's own
fallibility. Six senses, each with a different current standing:

- **S1 — Attribution** (which principal is this act FROM): s40's strict declared-not-silent
  attribution, standing checks, the anchor coupling, `principal_actor_resolution`. **Built.**
- **S2 — Authentication** (is the claimant really that principal): deliberately thin. A
  standing declaration "authenticates nothing" and the spec refuses to overclaim IA-2
  (FABLE-PRINCIPAL-IDENTITY-SPEC.md:270). Stamps are tripwires, never promoted. The only real
  authentication is the human GPG key at three deliberate moments (ratification tags, SIGNED
  commissions, signed chain heads — MAINT-GPG-TRUST-LAYER.md §2–§4), agent signing refused by
  design (§6). Model identity is evidence-lane diagnostics with named vendor ceilings
  (s44 + FABLE-SUBSTITUTION-OF-AUTHORITY-CONSULT-2026-07-19.md §1.2/§2.2). **Thin by ratified
  design; the thinness is documented, which is the house bar.**
- **S3 — Authorization / entitlement** (MAY this principal do this act): the thin sense that
  is NOT yet documented-as-final. Two layers exist: the Postgres privilege layer (narrow
  grants, s18/s20; s43 revokes ALL client INSERT and makes five SECURITY DEFINER functions the
  only write path — s43:177–184) and the semantic layer (role bindings, competence grants) —
  and the semantic layer gates nothing: any active principal may countersign, review, or
  commission regardless of what it is bound to. s41 names entitlement enforcement "the named
  follow-on ratified amendment" (s41:642). **Recorded, not enforced; the follow-on is due for
  a decision, not for silent aging.**
- **S4 — Enforcement locus** (WHERE decisions are made and recorded): s43 is a
  reference-monitor-shaped boundary — enforcement and recording share one trust boundary, a
  refusal is a committed, hash-chained, unretractable ledger row
  (s43:25 names the NIST AU-2/AC-7 shape; FABLE-REFUSAL-RECORDING-AND-HASH-COVERAGE-SPEC.md:459
  names AC-25's shape). **Built, and unusually good.**
- **S5 — Audit of access**: writes and refused writes, fully covered (s26/s42 chain, s43
  journal, signed heads). **Reads: nothing** — the boundary service serves every derived view
  with no caller identification (serving/boundary_service.py authenticates which *deployment*
  is addressed, "adds NO truth of its own," and has no principal surface — confirmed by
  reading its auth-relevant text this pass), and read-access logging is the project's own
  founding what-did-we-miss omission (ADR-0000 Revisit #4). **Half built, half a standing
  named absence.**
- **S6 — Separation of duties / independence**: s17 vocabulary, s21 (session, agent)-pair
  distinctness, s41 D-6's human-only managerial/financial scoping. **Built, with one
  witnessed granularity gap**: a genuinely isolated subagent dispatched by the orchestrating
  session is mechanically indistinguishable from the orchestrator itself, so its honest
  verdict must be filed as `self-review` (downstream AUTOHARN_BACKFLOW.md finding 6, lines
  170–211; the kernel's refusal was correct — the representable tier is what is missing).

**Principals in scope**, because "access control for whom" matters: the human maintainer;
orchestrating sessions; dispatched subagents; tool principals (s43's `write-boundary`);
downstream deployment operators; and nla-schema subjects (whose isolation is a genuine
confidentiality boundary — the one place classic access control applies here, done by
database catalog isolation, nla-schema.sql:12, with its own named CONNECT-denial hazard at
line 232).

*Confidence: high on the decomposition; it is derived from the corpus's own vocabulary rather
than imported.*

## 2. Current posture, in four honest states

**ENFORCED** (construction/write-time/run-time, per ADR-0011 vocabulary):
- Strict attribution, standing-at-write-time, anchor coupling — s40 (header, Elements 3–5).
- Sole-write-path boundary functions + refusal journaling + typed verdicts — s43.
- Append-only + hash chain over every column — s26/s42; signed heads (GPG rung 3).
- Independence distinctness (s21) and human-only unwitnessable-independence claims (s41 D-6).
- Human-only key binding; malformed fingerprints refused (s41 D-2/D-3).
- Privilege minimization: INSERT revoked, EXECUTE-only writers, narrow SELECT grants (s43, s20).
- Signed-genesis ceremony at world birth, key-pinning defect fixed 2026-07-21 (commit 238b4ea;
  tools/setup_tui/signed_genesis.py drives the shipped verbs only).

**RECORDED, NOT GATING** (declared-not-enforced, each named as such by its own spec):
- Role bindings and competence grants (s41:114/229/642; FABLE-PRINCIPAL-IDENTITY-SPEC.md §7
  items 4 and 6). The review_gap machinery's "missing premise."
- Key bindings: empty-until-ceremony slot (D-4; ceremony deferred by standing ruling).
- Model-identity attestation: representable everywhere, and per the 2026-07-19 consult,
  operationally unarmed (watchdog unbuilt, zero live attestation rows at that consult's date).

**ABSENT** (not yet even a named decision — the actual first-class gaps):
- The registry-rooted 800-53 AC/IA posture matrix (STANDARDS-REGISTRY.md:35: "NOT YET
  OPERATIONALIZED ... first registry-rooted completeness audit pending").
- Read-surface identification and read audit (S5 above) — currently a *silent* posture, which
  is exactly what ADR-0000 Revisit #4 Clause 1 forbids for standards-relevant omissions.
- A representable independence tier for dispatched-but-isolated subagents (finding 6).

**EXCLUDED BY STANDING RULING** (respected, not relitigated here):
- Host/perimeter hardening for the maintainer's machine (2026-07-12; adopter-facing guidance
  remains fair game). Broader cryptography beyond the signed-genesis scoped lift (2026-07-19).
- Hooks-layer identity: honor-system by argued exclusion (spec §5(i)); the action stream
  carries no model identity by vendor design — the ceiling is the vendor seam, already pressed
  through the feedback channel (substitution consult §2.2), not buildable here.
- The live world: every kernel mechanism above reaches only future births. Dust stays dust.

*Confidence: high; every row above carries a file citation I read this pass.*

## 3. Specifics relative to standards (the maintainer's addendum)

The registry rule governs the method: completeness runs FROM the registry's entries TOWARD the
project, reading each standard at its authoritative source (ADR-0000 Revisit #4 Clause 2; the
one witnessed precedent is the AC-2/OSCAL fetch, sha256-pinned, ledger rows 1432/1433). The
registry today holds exactly one entry: **NIST SP 800-53**. So the binding standards question
for access control is: *what does the AC family (and its IA/AU neighbors) demand, and what is
this project's honest per-control state?* What follows is a consult's orientation map — where
the project already stands against the controls I can name with confidence — **not** the
registry-rooted audit itself, which must enumerate the family from NIST's own catalog and
would be the audit's deliverable, not mine:

- **AC-2 (Account Management)** → substantially the s40/s41 family: registration with
  mandatory stated purpose (the spec cites AC-2 for exactly this, §3.2), lifecycle events,
  derived standing, succession-not-rename, free-text role types (the AC-2 governance-process
  reading witnessed at rows 1432/1433). Strong.
- **AC-3 (Access Enforcement) / AC-25 (Reference Monitor)** → s43: one enforcement point, the
  only write path, decisions and their records in one trust boundary. The refusal-recording
  consult already invoked AC-25's trust-boundary requirement to reject CLI-side recording;
  s43 is that argument built. Strong.
- **AC-7-shaped denied attempts / AU-2 (Event Logging)** → `write_refused` rows, unretractable,
  hash-covered (s43:25 names the shape itself). Strong — and unusual: most systems log denials
  to a file; here they enter the evidentiary record.
- **AC-5 (Separation of Duties)** → s17/s21/D-6. Real but honestly bounded: in a solo world
  SoD is recorded truthfully, not adversarially real (spec §8), and the subagent-tier gap
  (finding 6) is a granularity defect in exactly this control's territory.
- **AC-6 (Least Privilege)** → the grant surface: INSERT-only-through-functions, zero-SELECT
  writer roles (s18's finding-45 discipline), nla CONNECT denial. Good on the kernel; the
  hooks/operator layer is out of scope by the action-stream and perimeter rulings — the matrix
  should say so rather than leave it silent.
- **AC-4 (Information Flow)** → nla catalog isolation (the subject must not read the
  operator-side kernel). Narrow but real.
- **AC-14 (Permitted Actions without Identification)** → this is the control that names the
  read surface's current state: every derived view is readable without identification. AC-14
  exists precisely to force that to be a *documented decision* with a rationale. Today it is
  undocumented. Cheap to fix by naming; §7 D4.
- **AC-24 (Access Control Decisions)** → typed `write_verdict` values; decisions are explicit,
  typed, and recorded. Strong.
- **IA-2/IA-5 (Identification & Authentication, Authenticator Management)** → honestly NOT
  met for agent principals, and the spec says so in terms (spec:270). The human authenticator
  is the GPG key (hardware-token-preferred, rotation procedure witnessed on a throwaway key —
  MAINT-GPG-TRUST-LAYER §7). IA-4 (identifier management) is largely met: immutable ids/names,
  no reuse, succession. The matrix should mark IA-2-for-agents **named-as-excluded with the
  vendor-ceiling argument**, not "partial" — pretending partial coverage would be the
  overclaim the corpus keeps refusing.
- **AU-9/AU-10 (Protection of Audit Information, Non-repudiation)** → append-only + s42 full
  hash coverage + maintainer-signed heads; non-repudiation exists exactly where a human signs
  and deliberately nowhere else (agent signing refused, §6 — a correct refusal, worth
  preserving against future enthusiasm).
- **AU audit-of-reads** → the founding omission, still open, now at least named in the LAW.
  Priced honestly: on-host Postgres read logging (e.g. the already-deferred pgAudit lead)
  is diagnostics-grade at best under the action-stream principle; a load-bearing read audit
  would need the boundary service to become the sole read path with caller identification —
  real machinery, only worth it if the matrix or an adopter deployment demands it.

Two standards observations beyond 800-53, offered as registry *questions* because the registry
changes only by maintainer amendment:

1. **NIST SP 800-63** is already the de-facto design vocabulary of the principal surface (the
   identity/lifecycle/binding/relationship decomposition the ratified consultation grounded
   s40/s41 in) — but it is not a registry entry, so no completeness exercise will ever sweep
   it. Either it belongs in the registry or its use stays what it is: a cited source, audited
   never. §7 D2.
2. The founding brief's source set (21 CFR Part 11's electronic-signature shape — which the
   GPG spec's SIGNED rung already matches almost clause-for-clause, §3; IEC/ISO/DO-178C
   competence-record obligations that G13 already landed as typed events) remains what the
   registry says it is: the brief's bibliography, not bars. If any of them is a bar the
   maintainer holds, it enters by his word; nothing here presumes it.

Given the project's purpose, several AC-family members (session lock, remote access, external
information systems, publicly accessible content, etc.) are plausibly N/A — but per Revisit #4
Clause 1 the matrix must NAME them excluded with one line of reason each. That naming *is* the
deliverable; it converts every silent gap in this section into either work or a contestable
decision.

*Confidence: high on the mapping's individual rows (each anchored to a mechanism I read);
medium on family completeness — deliberately so, since enumerating the family from its
authoritative catalog is the audit's job, not a consult's memory.*

## 4. Which gaps matter at the mother's-life bar

**G1 — Entitlement enforcement (matters; the sharpest one).** The kernel can now represent
"X is bound as reviewer" and still accepts a countersign from Y, bound as nothing. That is a
drift between recorded authority and effective authority — the same defect class the principal
surface was remediated for, one level up: the record is honest, and the enforcement the record
implies is absent. s41 itself names the follow-on; leaving it unratified indefinitely would be
the filed-deferral decaying into a silent one. Two cautions that shape the fix: (a) the solo
world must stay zero-friction, which the house already knows how to do — the scaffold binds
the birth principals' roles as explicit acts, exactly as strict attribution's
declared-not-silent default reconciled row 1398; (b) competence should stay recordable-only
for now — its band vocabulary is a ratified placeholder (§9(g)), and gating on placeholder
semantics would enforce guesses.

**G2 — The pending registry audit (matters; it is the "first-class" move the commission asks
for).** Making access control first-class does not primarily mean building more; it means the
project can state, per control, what it enforces, what it records, and what it refuses to
pretend. That artifact is already mandated (Revisit #4), already shaped by the maintainer's
conformance-first ruling (row 1378), and still pending. Everything else in this consult should
be sequenced so its closure universe can enumerate from the family instead of from the corpus.

**G3 — The subagent independence tier (matters, moderately).** Finding 6 is a live downstream
deployment recording honest reviews at a falsely weak grade. The kernel refused correctly; the
gap is representational (no tier between `self-review` and cross-session independence for a
dispatched-but-isolated subagent). Two dispositions exist, both cheap relative to the family
work: a small delta keying distinctness on a dispatch identity if the harness can carry one to
the CLI honestly, or the documentation form (a named, sanctioned disclosure convention, like
LAZY commissions). Which one is a real design question — a dispatch id is *claimed* by the
orchestrating session, not witnessed, so the honest ceiling of a new tier is
"disclosed-isolated-dispatch," a claims-lane grade. That may still be worth typing: the whole
point of s44's lesson is that claims-lane facts are worth recording when they are typed,
dated, and marked as claims.

**G4 — Read surface (matters as a naming act; probably not as machinery).** For the
maintainer's own localhost use, reads-without-identification is a defensible posture the
perimeter ruling all but implies — but it is currently silent, and it stops being defensible
silently the moment a deployment serves anyone else. One named decision (AC-14 form) plus one
paragraph of adopter-facing guidance discharges it honestly. Building caller identification
now, for one operator on one host, would be ceremony.

**Honestly out of scope at this bar, by the standing rulings:** perimeter; key ceremony and
any new cryptographic machinery (nothing in this consult needs the scoped lift widened — I
looked for a reason to ask and found none: the entitlement family is pure kernel semantics,
no crypto); hooks-layer identity (vendor ceiling; keep the feedback-channel pressure, build
nothing); retroactive anything (runs-are-linear).

*Confidence: high on G1/G2; medium-high on G3's disposition being worth kernel space at all
(the documentation form may be lagom); high on G4's naming-not-building shape.*

## 5. Recommendation

**R1 (first): commission the registry-rooted NIST 800-53 completeness audit for the AC and IA
families** (AU's denied-attempt corner is already partially discharged by s43; the audit
should fold it in rather than re-open it). Method per Revisit #4 and the rows-1432/1433
precedent: fetch the catalog at source, pin it, walk the family control-by-control, emit the
four-state matrix (implemented / partial / named-as-excluded / absent-and-unnamed) with a
file:line witness or a one-line exclusion reason per row. Sonnet-executable under the standing
contract; no kernel edits; the output is an artifact plus, where it finds absent-and-unnamed
rows, filed work items. *Enforcement surface of the recommendation itself: review-only (an
audit is an artifact), but per ADR-0011 its findings convert to mechanisms, and the registry
entry's status line updates from "pending" — the one mechanically checkable trace.*

**R2 (second, gated on R1's AC-family read): ratify authoring of the entitlement-enforcement
delta family** — the D-5 follow-on by its own name. Scope I recommend: countersign/review/
commission acceptance gated on an in-force `principal_role_bound` event for a role the world's
own configuration names for that act; the scaffold binds author/reviewer/commissioner roles at
birth as explicit acts (declared-not-silent, the row-1398 pattern); competence grants stay
recordable-only. This is a kernel-semantics change to existing review paths — per the
orchestration contract it requires a Fable-authored, maintainer-ratified spec, is **not**
class-ratified fail-safe (it makes previously-accepted writes refusable), reaches only future
births, and its spec's closure statement should enumerate the acceptance-path universe (every
kind whose acceptance implies authority: review kinds, countersign, commission, obligation
assignment) rather than the one path the panel tripped on. *Enforcement surfaces, ADR-0011
vocabulary: write-time data constraint + run-time invariant (boundary-function refusals,
journaled by s43 for free); test/CI via the detect siblings and both-polarity scratch
witnesses; the role-to-act mapping's own quality stays review-only and is declared as such.*

**R3 (small, parallel): two naming acts.** (a) The AC-14 read-surface decision recorded as a
maintainer decision row plus an adopter-facing paragraph; no machinery. (b) Finding 6
disposed: my lean is the typed claims-lane tier (small delta, future worlds) *if* R1's AC-5
row concurs it is worth kernel space, else the sanctioned disclosure form documented where the
independence teach-text already points. *Surfaces: review-only naming + (optionally) one
additive refusal-relaxing-nothing delta — note honestly: a new, more permissive tier for a
previously-refused shape is NOT class-ratified fail-safe either; it relaxes a refusal and
routes to the maintainer by the contract's own rule.*

**R4 (refusals, so the direction is bounded):** no new cryptographic machinery; no per-request
authentication of the solo operator; no read-path identification build in v1; no certification
paperwork — every artifact above is either a mechanism or a matrix row someone can contest.

**Relationship to s40/s41, stated precisely:** this consult proposes **no change** to the
ratified and built s40/s41 family, and nothing that re-opens any of its thirteen corrections.
R2 is the family's own §7-item-4/D-5 named follow-on, sequenced after s43 exactly as that spec
sequenced it; R3(b) touches s21's distinctness grain, adjacent to but disjoint from the
family's surfaces; R1 audits the whole, changes nothing.

*Confidence: high on R1 (it is the LAW's own pending mechanism); medium-high on R2's scope
(role-gating yes / competence-gating not-yet is a judgment call the maintainer may reasonably
invert); medium on R3(b)'s delta-vs-documentation choice — that is why it is a decision point
and not a recommendation.*

## 6. Closure statement (ADR-0000, 2026-07-02 form) for the recommended direction

**Invariant:** every authority-relevant act the kernel accepts is checked at write time
against in-force, event-derived authority facts (standing today; role entitlement after R2),
and every access decision — acceptance or refusal — is itself a recorded, tamper-evident
event; wherever a decision is deliberately unchecked or unrecorded, that absence is a named
row in the registry-rooted posture matrix, never silent.

**Quantification universe, enumerated:**
- *Axes:* write path; refusal path; read path; authentication; delegation/dispatch;
  independence; lifecycle (registration through revocation); privilege (DB grants).
- *Principal population:* human maintainer; orchestrating sessions; dispatched subagents;
  tool principals; downstream operators; nla subjects.
- *Sibling surfaces:* kernel triggers + the five boundary functions; the `led` CLI; the
  boundary service; the SPA read views; nla-schema; the setup TUI (principals & authority,
  signed genesis); the scaffold birth sequence; the GPG verbs; the hooks/gates layer.
- *Worlds:* future birth chains only.

**Named as NOT covered, deliberately:** hooks-layer identity (vendor ceiling; feedback-channel
pressure only); model-identity foreclosure by construction (same ceiling); the live world's
history (runs-are-linear); host/perimeter (standing ruling); key ceremony and all new
cryptography (standing ruling; nothing here asks for the scoped lift to widen); read-path
identification machinery (named posture instead, until an adopter deployment or the matrix
demands more); competence *enforcement* (band vocabulary is a ratified placeholder).

**Denomination check:** authority is denominated in in-force binding *events*, never names;
independence in stamp pairs, never assertions; standing computed at read from dated events,
never stored; non-repudiation in human key signatures only; refusals in committed ledger rows,
never log lines. No bound in this consult is a bare literal; the only new "bound" proposed is
a membership check against events the kernel already owns.

## 7. The maintainer's decision points (separable; each answerable alone)

**D1 — Commission the registry-rooted 800-53 AC+IA posture-matrix audit now?** (R1. Discharges
the registry's own pending first audit for these families; Sonnet-executable; no kernel
surface. If no: the registry's "pending" line keeps aging, and §3's map stays a consult's
sketch with no successor.)

**D2 — Registry amendments (your file, your word alone):** add NIST SP 800-63 as an entry, so
the identity layer's own design vocabulary is auditable? And do any of the brief's source
standards (21 CFR Part 11 is the one the GPG layer already nearly matches) enter as bars, or
stay bibliography?

**D3 — Ratify authoring of the entitlement-enforcement family (R2)?** Sub-choice: role-binding
gating only (recommended), or competence gating folded in despite the placeholder band
vocabulary? A yes here commissions a Fable-authored spec, not code.

**D4 — The read surface:** record reads-without-identification as the named, accepted posture
(localhost + adopter-facing guidance paragraph), or commission caller discrimination for
multi-party deployments now? (Recommended: name it; build nothing yet.)

**D5 — Finding 6:** a typed claims-lane independence tier for dispatched-isolated subagents
(small future-world delta; relaxes a refusal, so it routes to you by the contract's own rule),
or the documentation form (sanctioned disclosure convention, zero kernel surface)? (My lean is
weakly toward the typed tier; the documentation form is the lagom floor and fully honest.)

Nothing else in this consult needs a ruling: R4's refusals follow from your standing rulings,
and the s40–s52 arc needs no decision — it needs a birth.
