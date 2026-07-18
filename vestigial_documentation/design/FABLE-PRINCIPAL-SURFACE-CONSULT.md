# FABLE-PRINCIPAL-SURFACE-CONSULT — the polished living edition of the 2026-07-18 principal-surface consultation

**What this document is.** This is a legibility-rewritten edition of a banked, verbatim
consultation record:
[`design/ORCH-CONSULT-PRINCIPAL-SURFACE-2026-07-18.md`](ORCH-CONSULT-PRINCIPAL-SURFACE-2026-07-18.md)
(the "source"). The source is a point-in-time record — the complete, unedited output of a
fresh-context Fable consultation, commissioned by the maintainer on 2026-07-18 under
[ADR-0018](../../law/adr/0018-consults-are-not-front-loaded.md) ("consults are not front-loaded":
the consulted model receives only the witnessed problem, its evidence, and the governing LAW —
never the commissioner's own candidate answers) — and it is frozen: nothing in it is ever
retro-edited. **Where this edition and the source diverge on any point of substance, the source
governs** ([ADR-0005](../../law/adr/0005-documentation-discipline.md) Rule 8, the frozen-record
rule). This edition adds no claim, opinion, or recommendation the source does not already make,
and strengthens or softens none of the source's confidence marks; it exists solely to make the
same content parseable by a reader who was not in the room when it was written, per
[ADR-0017](../../law/adr/0017-the-zero-context-reader.md) (the project's documentation-legibility
law — every sentence must parse standalone, every referent must resolve, every structure must
be grounded, and the opening must orient a reader who has none of the author's context).

**Who this is for.** Anyone who needs to understand or act on the consultation without having
watched it happen: the author of the principal-surface remediation spec this consult feeds, a
reviewer of that spec, or a later auditor asking why the spec's design choices are what they
are.

**What question it answers.** What is `kernel.principal` — the autoharn kernel's table of
registered identities (humans, models, subagents, tools) — today; what do the relevant
standards families (NIST, nuclear/functional-safety, aviation, cryptographic-signature) say a
system's identity layer should be able to represent; where does the current table fall short;
what would a type-driven redesign look like; and what, in an actually-deployed downstream
instance of this harness, has already been improvised to work around the shortfall. The
consult does not itself write the remediation spec — it is the researched, opinionated input
that spec is built from (source, opening line: "It informs the principal-surface remediation
spec that follows separately; it is not that spec.").

**Section numbering.** This edition keeps the source's section numbers 0–5 unchanged, so that
any later document citing "§2.2" or "§4 Axis B" of the source lands on the same content here.
An unnumbered orientation (this preamble) precedes §0; nothing else is renumbered.

---

## 0. What the principal surface currently is (verified, not summarized from prose)

This section reports what the consultant found by reading the schema and running read-only
queries against a live deployment — not a paraphrase of someone else's description of the
schema.

`kernel.principal` is the autoharn kernel's table of registered identities. It has four
columns: `id`; `name` (declared UNIQUE); `agent_class` (constrained by a database CHECK
constraint to one of `human`, `model`, `subagent`, `tool`); and `acts_for` (a nullable
self-referencing foreign key — a principal row can point at another principal row — glossed in
the table's own comment as "delegation; NULL = own right", meaning a NULL value signals the
principal acts on its own authority rather than on another's behalf). The table was created in
kernel-lineage delta s13 and re-instanced in deltas s14 and s15 — "delta" here means a numbered,
append-only schema-migration file under
[`kernel/lineage/`](../../kernel/lineage), the mechanism by which this project's core database
schema evolves (never edited in place; the files are numbered s13, s14, and so on, and are
applied in that order) — and the consultant verified,
by grepping every file under `kernel/lineage/`, that **no lineage delta since s15 has touched
the table's structure**: the table is referenced constantly elsewhere in the schema, but no
`ALTER TABLE ... principal` statement exists anywhere in the lineage. Registering a new
principal is done with `INSERT ... ON CONFLICT (name) DO NOTHING` — a Postgres insert that
silently does nothing if a row with that name already exists, rather than erroring. A companion
table, `principal_role`, maps each database connection role to a principal — this is a second,
independently-assigned way a principal gets attributed, used when the *database connection
itself* (rather than an explicit actor argument) determines who is acting. In the project's
Idris formal model (`design/Autoharn.idr`, referenced later in this document as "the Idris
model"), the type standing in for a principal's identity, `PrincipalId`, is simply a bare
natural number (`Nat`) — a type that faithfully mirrors how thin the real schema's identity
concept is.

Thin as the identity record is, what depends on it is the heaviest load any single concept
carries in the kernel:

- Every row of `ledger` — the kernel's central append-only table of recorded events — has a
  NOT NULL foreign key to `ledger.actor`, meaning every event must be attributed to a
  principal.
- `set_actor` is the mechanism that stamps a database connection's default actor.
- `validate_review` is a trigger that refuses a review row if its actor is the same as the
  actor of the thing being reviewed (a same-actor self-review refusal).
- The independence-tracking machinery added in lineage deltas s17 and s21 (glossed further in
  §1.1 below) depends on principal identity to reason about whether two actions came from
  provably distinct actors.
- Delta s29 computes a `discharge_grade` column — a machine-derived label for how strong a
  review's independence claim is — from principal/stamp data (a "stamp" is a per-invocation
  cryptographic marker distinct from a principal name; see the Glossary entry linked at first
  full use in §1.1).
- The `obligation` table's `assigned_by`/`obliges_actor` columns and the s32-added
  `countersign_obligation`/`review_gap` views (this project's mechanism for tracking which
  principals' writes are outstanding "review debt" until a distinct actor countersigns them;
  see [GLOSSARY.md#obligation](../../GLOSSARY.md#obligation) and
  [GLOSSARY.md#review_gap](../../GLOSSARY.md#review_gap)) key off principal identity throughout.
- Delta s25's "commission signing modes" (ways a maintainer-authored commission document can be
  cryptographically or procedurally signed) key off principal identity.
- The operator CLI's actor-resolution surface — the `LED_ACTOR` environment variable (which
  selects which principal a `led` command runs as) and the `resolve_actor` function that
  interprets it — covers, by its own header comments, four different write paths, and honestly
  names three of those four (`work depends`, `work close`, and `resolve-violation`) as *not yet
  wired* to real actor resolution. This is not a theoretical gap: it is the exact gap that a
  downstream deployment (the "panel deployment," glossed in the next paragraph) hit in
  production — five `work close` commands dispatched with the intended actor
  `item-countersign` all landed instead attributed to `actor=author`, a misattribution recorded
  in that deployment's own findings file as the addendum to its Finding 1, at its
  ledger rows 1710, 1716, 1719, 1732, and 1746.

Two terms used repeatedly below, glossed once: **the panel deployment** ("the panel," in the
source's shorthand) is `autoharn-panel`, a separate, real, running adoption of this harness by
a different (non-Fable) orchestrator, used throughout this consult as a source of *lived*
evidence about how the principal surface behaves under actual use — its own ledger is queried
directly, and its own "ledger rows" (e.g. "row 1691") are cited positionally, following the
source's own citation practice. (An editorial note of this edition, not a claim of the source:
that practice is sanctioned by [ADR-0017](../../law/adr/0017-the-zero-context-reader.md) Rule 2(c),
which permits positional citations into frozen, append-only records because they never move —
unlike positional citations into documents that get rewritten wholesale.)
**AUTOHARN_BACKFLOW.md** (cited below as "the backflow," with numbered "Findings" and
"Suggestions") is a document of structured feedback the panel deployment sent back to this
project, naming defects and improvements it discovered by living with the harness; it is not
currently present as a file in this repository's tree, so it is cited here as a named artifact
rather than as a resolving link.

Two live findings from the consultant's own queries against the panel deployment, worth having
in front of any design discussion:

- **The panel's principal roster** (queried live during this consult) has 13 principals, with
  `id` values running from 1 to 27 but with *gaps* at 5–6, 8–14, and 16–20. Postgres burns a
  sequence value on every insert attempt, including ones the `ON CONFLICT DO NOTHING` clause
  silently discards — so these gaps are the silent-duplicate-registration defect made visible
  directly in the id column: registration attempts against already-taken names vanished with no
  signal, burning the skipped sequence values (counting the gaps — an editorial computation of
  this edition, not a source claim — more than a dozen such attempts).
- Three of the panel's 13 principals — named `commissioner`, `maintainer`, and `bork` — are all
  classified `agent_class = human` and are, in fact, the *same human being* under three
  different names. The `acts_for` delegation column is NULL on every single row in the
  deployment's entire history — it has never once been used, despite existing since s13/s14/s15.
  Meanwhile two principals minted a day apart for what appears to be the identical job —
  `reviewer` and `reviewer2` — are classified differently: `reviewer` is `subagent`,
  `reviewer2` is `model`. The relationship column that exists specifically to record such
  relationships has never been used, and the classification column contradicts itself across
  what should be sibling principals.

**One structural observation that frames everything that follows:** the principal table is the
only load-bearing surface in the kernel that violates the kernel's own record-keeping
discipline. Every row of `ledger` is append-only, attributed to a principal, timestamped, and
chained by cryptographic hash to the row before it. A row in `principal`, by contrast, is
mutable in principle, carries no record of who registered it, no timestamp, no stated reason,
and its creation produces no corresponding `ledger` event at all. The very identity layer that
is supposed to anchor **ALCOA attributability** — ALCOA is the data-integrity mnemonic
(Attributable, Legible, Contemporaneous, Original, Accurate; see
[`law/briefs/safety-critical-logging/BRIEF.md:124`](../../law/briefs/safety-critical-logging/BRIEF.md)
for its full definition and standards provenance) that this project's own safety-critical
logging BRIEF adopts as the acceptance test for every record — is itself the one artifact in
the whole system that fails that same test. This is precisely the kind of finding [ADR-0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
(this project's foundational type-driven-design law) asks a reviewer to surface — a *type-level*
diagnosis, not an instance-level bug report — and most of the design proposals in §2 below
follow directly from it.

---

## 1. What the standards families actually say, mapped against this surface

The maintainer's commission for this consult specifically asked that the analysis start from
external standards rather than from the project's own existing design. Per
[ADR-0000's Revisit #4 (2026-07-12, codified from the what-did-we-miss RCA), Clause 2](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
(a rule requiring that a defect-class analysis run "registry-rooted" — starting from the
standard and working toward the project, rather than starting from the project's felt pain and
reaching for standards to justify it), this section runs in that direction. This project keeps
a [`law/STANDARDS-REGISTRY.md`](../../law/STANDARDS-REGISTRY.md) — a registry of which external
standards this project has formally adopted as governing references — and, at the time of this
consult, it carried exactly one entry: NIST SP 800-53, added 2026-07-12 and marked "NOT YET
OPERATIONALIZED" (meaning: adopted as a reference, but not yet wired into any enforcement
mechanism). This consult is, in effect, the first registry-rooted audit pass over the identity
(IA) and access-control (AC) control families that entry names.

The maintainer had also expressed surprise that principal-level identity granularity had "never
come up" in prior law/brief audits of this project. The consult gives a precise answer: the
project's own founding safety-critical-logging BRIEF *does* already obligate the relevant
records — its register entries I2, I6, G7, G9, and G13 (codes into the BRIEF's own obligation
register, each resolvable there; G13, the competence record, is the load-bearing one for this
consultation and is glossed in §1.3 below)
— but every prior audit of that BRIEF ran "corpus-rooted" (starting from documents already in
the repository and checking them against the BRIEF) rather than "registry-rooted" (starting
from the standard and checking the running system), and the principal table happens to be
exactly the kind of artifact no *document* cites, so a corpus-rooted audit was structurally
blind to it — the consult calls this "the same silent-omission mechanism" already named by the
what-did-we-miss RCA (the earlier root-cause analysis of a read-logging gap, recorded on the
project tracker and cited by name in ADR-0000's Revisit section).

### 1.1 NIST SP 800-53 rev 5 — the Identification-and-Authentication (IA) and Access-Control (AC) families

Sources consulted this session:
[IA-4](https://csf.tools/reference/nist-sp-800-53/r5/ia/ia-4/),
[AC-2](https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-2/),
[IA-5](https://csf.tools/reference/nist-sp-800-53/r5/ia/ia-5/),
[AU-10](https://grcacademy.io/nist-800-53/controls/au-10/), and the
[full SP 800-53r5 text](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf).
**Confidence for this whole subsection:** high on the *intent* of each control family and how
it maps onto this project; medium on anything phrased as if it were a direct quotation — the
consultant did not retrieve exact clause text to quote verbatim from the primary documents, and
says so explicitly.

- **IA-4 (Identifier Management).** The control's requirement: an identifier may be assigned
  only with authorization; it must actually identify the intended entity; reuse of an
  identifier is controlled. Mapped onto autoharn: `register-principal` (the operator command
  that inserts a row into `kernel.principal`) requires no authorization step of any kind — any
  writer with INSERT privilege on the table can mint a new identity. The table's UNIQUE
  constraint on `name` does prevent literal name reuse permanently, which is *stronger* than
  IA-4's stated minimum — but because a duplicate registration attempt is silently discarded
  (the `ON CONFLICT DO NOTHING` behavior from §0) rather than rejected with an error, a second
  registration attempt for a name that already exists **silently aliases onto the existing
  identity with no signal to the caller that anything unusual happened**. That is IA-4's
  "identifies the intended entity" property failing in the *worse* of the two possible
  directions — not a hard failure the caller notices, but a silent one. The panel deployment hit
  this defect in production (the id-gap evidence in §0).
- **AC-2 (Account Management).** The control's requirement: account *types* are defined in
  advance; **approval is required before an account is created**; accounts are
  created/enabled/disabled/removed following a defined procedure; account use is monitored;
  accounts are periodically reviewed. autoharn currently implements none of this at the schema
  level — there is no approval step, no way to disable a principal, no removal procedure, and no
  review cycle. Notably, the panel deployment independently built its own hand-rolled
  approval-before-creation process for naming principals (assessed in full in §3 below) without
  knowing AC-2 existed as a named control. The consultant reads that convergence — a real,
  lived deployment reinventing AC-2's shape from felt need — as evidence that the control
  addresses a genuine gap, not bureaucratic overhead.
- **IA-2 (Identification and Authentication of Organizational Users).** This is, in the
  consultant's assessment, the deepest gap of the group. A principal's *name* in autoharn is
  merely *asserted* — set via the `LED_ACTOR` environment variable — never authenticated (i.e.,
  never cryptographically or otherwise proven to actually be who it claims). Authentication of
  a kind does exist elsewhere in the system, but at two *other* layers, neither of which is the
  principal layer itself: (a) the database connection layer, via `principal_role` (§0's
  connection-to-principal mapping); and (b) the invocation layer, via the "stamp" mechanism
  added in lineage delta s17 — a per-invocation cryptographic marker (HMAC) that binds a ledger
  row to the actual session/agent invocation that wrote it (full definition:
  [GLOSSARY.md#stamp](../../GLOSSARY.md#stamp)) — which its own code header explicitly describes
  as "a tripwire, not authentication." The principal layer proper has *no* authenticator at all:
  any writer can sign a ledger row as any registered principal name it chooses. A prior
  incident this project calls "Finding 31" — one session registering itself as a principal named
  `reviewer` and then countersigning its own work under that name — was exactly this control
  failing, and the project's response (lineage deltas s17, s21, and s29) was to route
  independence claims *around* the untrustworthy principal layer and onto the stamp layer
  instead. The consultant judges that response correct and honest as far as it goes — but it
  means the principal table's *names* now carry social and audit weight that the kernel
  deliberately does not actually trust, and that mismatch is currently documented nowhere a
  reader of the table would encounter it.
- **IA-5 (Authenticator Management).** The control's requirement: the *lifecycle* of an
  authenticator — how it is bound to an identity, rotated, and revoked if compromised — is
  managed. Because principals currently have no authenticator at all (per IA-2 above), there is
  literally nothing for this control to manage yet; the consultant characterizes the control as
  not "partially met" but "structurally inapplicable" until the design in §2 creates a slot for
  a principal-to-authenticator binding.
- **AC-5 (Separation of Duties).** By contrast, this is the comparatively *strong* part of the
  story. `validate_review`'s same-actor refusal, stamp-distinctness checking, and the fact that
  delta s18's reviewer-role grants are enforced by database privilege (INSERT-only) rather than
  by convention, together implement separation of duties by mechanism, not by asking people
  nicely. Stated plainly: autoharn's separation-of-duties machinery is *ahead of* its identity
  machinery — the reverse of what is typical in most systems the consultant is aware of.
- **AU-10 (Non-Repudiation) and its enhancements** — specifically the sub-controls "Association
  of Identities," "Validate Binding of Information Producer Identity," "Chain of Custody,"
  "Validate Binding of Information Reviewer Identity," and "Digital Signatures." This family, in
  the consultant's assessment, reads almost like a direct description of autoharn's existing
  architecture: producer-identity binding is implemented by the stamp mechanism
  (invocation-grade, and present today); reviewer-identity binding is implemented by
  countersigns (also stamp-grade, present); chain of custody is implemented by the s26/s27
  row-hash chain (present); digital signatures are implemented by the project's GPG
  (cryptographic signing) layer (present). **And the principal table references none of these
  four mechanisms.** Every piece of machinery AU-10 asks for already exists in this project;
  what is missing is not machinery but a *join* — a way for the identity record itself to point
  at the mechanisms that authenticate and sign on its behalf.

### 1.2 NIST SP 800-63-3 — the conceptual model this schema needs

Sources: [SP 800-63-3](https://pages.nist.gov/800-63-3/sp800-63-3.html) and
[SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) (the consultant notes SP 800-63-4
now exists as a newer revision, but was only noted, not read in depth, for this consult).

The durable lesson the consultant draws from this standard for autoharn's design is not any
specific numeric assurance level, but its underlying *decomposition* of identity into three
independent axes, each with its own separate lifecycle:

- **IAL — Identity Assurance Level.** Identity *proofing*: is this record actually about the
  real-world entity it claims to be about?
- **AAL — Authenticator Assurance Level.** *Authentication*: is the actor present in this
  specific transaction actually the holder of that identity record?
- **FAL — Federation Assurance Level.** *Federation*: when identity claims cross between
  systems, how strongly can the receiving system trust the claim?

These three axes are independent of one another, and — crucially for this design — SP 800-63-3
treats an *authenticator* as something *bound to* an identity record, never *conflated with* it,
with explicit, dated bind/rebind/revoke events marking changes to that binding.

autoharn's current four-column `principal` table collapses all of this into a bare name. The
stamp mechanism is roughly AAL-like (it authenticates a specific invocation) but has no formal
binding to the identity layer; the `principal_role` database-connection map is a second, parallel
authenticator that is also not named as such anywhere; a GPG cryptographic key would be a third.
The type that would make the current confusion structurally impossible to represent is precisely
800-63-3's own spine: *"an identity record is not an authenticator; bindings between the two are
first-class, dated, and revocable."* That principle happens to coincide exactly with a rule this
project's own architecture-hygiene law already states independently — [ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md)
Principle P1, "single source of truth / derive-don't-duplicate: every fact has one home."

### 1.3 NRC / 10 CFR 50 Appendix B — organization, qualification, independence

Sources: [10 CFR 50 Appendix B, eCFR](https://www.ecfr.gov/current/title-10/chapter-I/part-50/subject-group-ECFR89aa6ca4aada73c/appendix-Appendix%20B%20to%20Part%2050)
and [Cornell LII's copy](https://www.law.cornell.edu/cfr/text/10/appendix-B_to_part_50). This
is the U.S. Nuclear Regulatory Commission's quality-assurance regulation for nuclear power
plants.

- **Criterion I** requires that persons performing quality-assurance functions have "sufficient
  authority and organizational freedom," including independence from cost and schedule
  pressure, with that authority and those duties *documented*.
- **Criterion II** requires that the QA program be carried out by *trained and qualified*
  personnel — qualification is a *recorded fact*, never an assumption the system is allowed to
  make silently.
- **Criterion XVII** requires that QA records be attributable (traceable to who produced them).

Mapped onto autoharn: the kernel does record *that* a distinct identity countersigned a piece of
work — but it records nowhere *what that identity is qualified to countersign*, and nowhere its
organizational position. This project's own founding BRIEF already names the matching
obligation as register entry **G13** — a "competence record": for every person or agent
assigned to a safety-relevant activity, log the actor's identity, the activity/role, the basis
for believing they're competent (training, qualification, or "increased confidence from
extended use"), and the assurance-level band the role demands (backed by two external standards,
IEC 61508-1 §6 and ISO 26262 Part 8 §9 — full definition:
[`law/briefs/safety-critical-logging/BRIEF.md:175`](../../law/briefs/safety-critical-logging/BRIEF.md)).
G13 is already law-adjacent in this project's own corpus, and there is currently no column,
table, or event kind anywhere in the kernel for it to land in. This is the item the maintainer
himself had described, in his own words, as "domains of competence" — and the consultant notes
it is not an exotic or unusual requirement: it is the single most-repeated identity requirement
across the nuclear and functional-safety standards cluster the founding BRIEF surveyed.

One honesty point the nuclear/independent-verification-and-validation cluster forces, worth
stating plainly: IEEE 1012 (the IV&V standard whose independence vocabulary this project's own
lineage delta s17 imported verbatim) distinguishes three *dimensions* of independence —
technical, managerial, and financial. In a single-human deployment (one maintainer, one payer,
one orchestrator), **no schema can ever substantiate managerial or financial independence
between model-class principals** — every agent involved shares the same one orchestrator and the
same one payer; there is no organizational separation to check. A stamp can witness *technical*
distinctness (a genuinely different invocation happened) and nothing beyond that. The consultant
observes that the current independence vocabulary lets a review claim `managerial` or
`financial` independence resting on the exact same stamp-distinctness evidence that legitimately
supports only a `technical` claim. The standards-consistent answer is not to fabricate the
missing evidence, but to *scope the claim honestly*: independence grades the schema can actually
witness should stay computed (delta s29 already does this correctly); grades it cannot witness
should either be refused outright, or explicitly carried as human-attested rather than
machine-derived. As things stand, the vocabulary promises more than any mechanism in the system
can actually check — a quiet instance, at the identity layer, of the same "discharge-status
dishonesty" this project's own BRIEF register entry **I9** already names as a hazard elsewhere
(I9: never conflate "proved automatically," "proved interactively," "reviewed but not proved,"
and "undischarged" into one umbrella "verified" claim — full definition:
[`law/briefs/safety-critical-logging/BRIEF.md:142`](../../law/briefs/safety-critical-logging/BRIEF.md)).

### 1.4 FAA / DO-178C-adjacent

Sources: [AdaCore, "A Fresh Take on DO-178C Software Reviews"](https://www.adacore.com/blog/a-fresh-take-on-do-178c-software-reviews)
and the [ISIT independent-verification white paper](https://www.isit.fr/documents/2114/safety_assurance_through_independent_verification_white_paper_v3.3.pdf).
Confidence: paraphrase-grade — the primary DO-178C standard itself was not retrieved for this
consult.

DO-178C is the civil-aviation software-certification standard. Its objectives that require
independence require not just that the verifier is a different person from the author, but
that **this separation is itself documented in the evidence** — the Software Verification Plan
must record the reporting structure and review authority, and reviewer identity must appear in
the verification records (DO-178C §11, cited at high confidence via this project's own BRIEF).
Separately, 21 CFR Part 11 §11.50/§11.70 (the U.S. FDA electronic-records/electronic-signatures
regulation, again cited via the BRIEF at high confidence) adds a further requirement on the
*form* a signature must take: it must be cryptographically bound to the specific version of the
record it signs, and its *meaning* — author, reviewer, or approver — must be explicit, not
implied.

Mapped onto autoharn: the kernel already documents the *separation* (via stamps and independence
grades) but not the *authority* — nothing in the schema states which principals are actually
*entitled* to act as reviewers in the first place. This is, in different vocabulary, the same
complaint the panel deployment's own backflow "Suggestion" already raised (see §3).

### 1.5 Cryptographic authentication — what the standards actually require, and reconciling two prior rulings

This subsection responds directly to a specific uncertainty the maintainer had stated: whether
cryptographic authentication of every actor is actually required by any of the standards
surveyed. The consultant's finding: **none of the surveyed standards families require
cryptographic authentication of every actor.** What they do require is two narrower things: (a)
non-repudiation specifically for *defined, authority-carrying actions* — approvals, sign-offs,
releases (AU-10 calls these "organization-defined actions"; Part 11 requires signatures on
records, bound to a version and typed by meaning; the professional-engineer stamp tradition
treats this as the point where liability formally transfers to the signer); and (b) that
*wherever* a signature mechanism does exist, the signer's identity and key must themselves be
*managed artifacts* — the record system must be able to say which cryptographic key speaks for
which identity, and for what span of time.

That finding maps exactly onto a design this project has already ratified separately:
[`design/MAINT-GPG-TRUST-LAYER.md`](../../design/MAINT-GPG-TRUST-LAYER.md). That design signs only the
authority-carrying moments — ratifications, commissions, and lineage chain heads — and
deliberately refuses to let autonomous agents hold signing keys (its §6, "What is deliberately
NOT signed, and why": an agent's key on the host machine would prove nothing a stamp doesn't
already prove more honestly — the consultant judges this correct and standards-consistent). That
same design's §5 already names, but has not built, "fingerprints committed per principal" for
the eventual multi-human case. The gap this consult names is precise: **the GPG trust-layer
design already assumes a principal-to-key binding exists; the principal table itself has no
column, slot, or table to hold that binding.** The signature mechanism exists; the record system
simply cannot say whose signature it is.

There are, on the maintainer's own record, two prior rulings that touch this ground, and the
consult reconciles them explicitly rather than leaving the tension implicit: a standing
deferral states that "key generation/signing" work is deferred "until all else banked" and
should "never [be] re-raise[d] as recommendation"; separately, the commission that produced this
consult itself named cryptographic authentication as a first-class concern for the
principal-surface design specifically. The consultant's reading: these do not actually conflict,
because they govern different things. The standing deferral governs the *operational ceremony* —
actually generating keys, adopting a signing ritual, provisioning hardware tokens. The newer
commission concerns *modeling the binding* in the schema — a `principal ↔ key-fingerprint`
binding table, with dated bind/revoke events, that can sit populated with zero rows indefinitely.
That is the same posture the project's own STANDARDS-REGISTRY already uses ("an entry may sit
unoperationalized; what it cannot be is silently absent"). Designing the slot re-raises nothing
about the ceremony; it simply makes the GPG design's already-ratified §5 representable in the
schema instead of remaining only prose. One residual tension the consultant flags honestly rather
than resolving unilaterally: the standing deferral's own wording says "never re-raise" — and yet
the maintainer himself re-raised the topic in commissioning this very consult. The consultant's
position is that the newer, more specific maintainer instruction governs, and recommends that
whatever spec follows this consult should state this reconciliation explicitly in its own text,
so that a future auditor does not have to re-derive it.

**Section 1 confidence, restated as the source states it:** high on control-family intent and
how each maps onto autoharn; medium on anything phrased as if quoting clause text directly —
nothing in this section is a verbatim quotation, and several primary standards (DO-178C, IEEE
1012, and SP 800-63-4 especially) were not retrieved in full, so those mappings are
paraphrase-grade. **Explicitly flagged as UNVERIFIED:** whether NRC regulatory practice anywhere
requires *cryptographic* (as opposed to merely attributable-and-immutable) records. The
consultant found no such requirement in the sources reviewed — but states plainly that an
absence of finding is not the same thing as a finding of absence.

---

## 2. The design space: what a principal must BE in this system

This section applies [ADR-0000 Rule 2(a)](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md)
— "when a defect is identified, ask first what type would make this defect class
unrepresentable" — to the identity concept itself, rather than to any one symptom of it.

The defect class, named at its most general: **an authority-carrying identity whose authority,
scope, and validity period are not representable in the schema — and therefore every possible
misuse of that identity is equally representable, with nothing distinguishing legitimate use
from misuse at the type level.** The candidate answers below are laid out with their trade-offs
stated, per the consultant's own confidence marks at the end of the section.

### 2.1 The root move: identity events, not identity columns

The maintainer had already proposed, in one recorded moment (panel ledger row 1691), an
instance-level fix: adding a boolean `revoked` column to the table. The consultant frames this
as correct in spirit but too narrow in scope: it fixes revocation specifically, while leaving
every other lifecycle fact (who registered a principal, when, on whose approval; who changed its
class; who bound a key to it) equally unrecorded. The *class*-level fix follows directly from
§0's structural observation — the principal table is the kernel's one surface that predates and
violates the kernel's own append-only-record discipline. The type that forecloses the whole
class of problem, not just revocation: **event-sourced identity**. Under this design, `principal`
stays as a minimal, immutable *anchor* — just an id and a name, never changed once created — and
every fact that changes over a principal's lifetime (registration circumstances, class
assignment, role/purpose binding, competence grant, key binding, suspension, revocation,
succession) becomes its own append-only, actor-attributed, stamp-carrying row in an event stream,
with the "current state" of a principal computed as a *derived view* over that event stream,
consulted by triggers whenever a decision depends on it. The consultant is explicit that this is
not an imported, foreign architecture — it is the kernel's *own* existing idiom (already used for
supersession in lineage delta s31, for the `effective_state` derived-view pattern, and for
composite discharge logic in delta s33), simply not yet applied to the one table that predates
that idiom.

The consultant states the trade-off honestly: this is a real, non-trivial delta — new tables, a
new derived view, and extensions to existing triggers — and only *part* of it qualifies for this
project's class-ratified fail-safe fast lane (the standing rule, stated in this project's
[CLAUDE.md](../../CLAUDE.md), that a kernel delta which strictly adds refusals, vocabulary, or derived views —
nothing existing relaxed, no existing semantics changed — AND arrives witnessed on a
[scratch schema](../../GLOSSARY.md#scratch-schema) (a throwaway test instance of the kernel) on
[both polarities](../../GLOSSARY.md#both-polarity) (the refusal shown firing on the illegal case
AND the legal case shown passing) with the SQL/ASP differential — the
[`./judge`](../../GLOSSARY.md#judge) tool's comparison of two independent encodings — in AGREE
(its green verdict), can enter the birth chain —
this project's term for how a schema change actually reaches a running deployment — without a
per-delta maintainer question; the witnessing precondition is part of the bar, not optional
ceremony). The consultant
proposes a pragmatic two-rung ladder:

- **Rung 1** (fail-safe, class-ratifiable as stated above): add `revoked_at`/`revoked_by`
  columns to `principal` as a first, narrow step, paired with a write-path refusal added to
  `set_actor`/`resolve_actor` that blocks writes from a revoked principal, and a loud refusal
  (rather than the current silent no-op) when `register-principal` is asked to create a
  duplicate name. Both of the CLI-side fixes the panel deployment's own backflow already asked
  for, verbatim (its "asks #1 and #2").
- **Rung 2**: the full event stream and derived-state view described above, which would
  *supersede* rung 1's plain columns by folding them into the view.

The consultant is explicit that shipping rung 1 alone and stopping there would be exactly the
kind of narrow, symptom-only patch this project's own type-driven-design law names as a defect
in itself (the "contrast specimen" ADR-0000 uses to illustrate a patch that fixes an instance
while leaving the class representable) — but that shipping rung 1 *as an explicitly filed first
step toward a documented rung 2* is legitimate, per [ADR-0013](../../law/adr/0013-execution-integrity.md)
Rule 4 ("a known defect is fixed or filed, never narrated-and-left" — filing a deferred remainder
with enough detail to act on later satisfies this rule; leaving it unfixed and undocumented does
not).

### 2.2 Granularity: four facts, four homes (the 800-63 decomposition applied)

Today, a single principal *name* conflates four genuinely separate facts. Applying §1.2's
800-63-3 decomposition, the consultant separates them into four distinct homes:

1. **Identity** — the durable anchor: an immutable name and an immutable id. (This already
   exists — it is the current table, minus everything else it currently also tries to carry.)
2. **Role/purpose** — *what job this name is entitled to sign for.* Today this fact, at best,
   lives only in the free-text prose of one panel-deployment decision row — nowhere structured,
   nowhere queryable. The consultant proposes this become a typed, dated binding instead, drawn
   from a small, closed, initially-narrow vocabulary — the consultant suggests, as a starting
   point drawn from the panel's own observed practice, something like: author / item-reviewer /
   whole-diff-reviewer / commissioner / orchestrator / scout. With this in place, the kernel
   could finally answer the question its own review-debt machinery currently cannot: "was this
   countersign performed by an identity actually *entitled* to countersign this kind of act?" —
   which is precisely the missing premise behind the review_gap machinery, and precisely the fix
   the panel's backflow "Suggestion" already asked for (§3).
3. **Competence/qualification** — the G13 record described in §1.3: an integrity band, the basis
   for believing the actor meets it, who granted it, and when. For a deployment with only one
   human today, the consultant suggests this can legitimately be a **named-but-not-built** slot
   — following the same posture the project's own STANDARDS-REGISTRY already uses for entries
   that are adopted but not yet operationalized. The point of naming it now is only that, when
   the BRIEF's G13 obligation actually fires (i.e., when this becomes load-bearing), there is
   already a place for it to land. The existing `agent_class` column is, in effect, already a
   crude two-value competence taxonomy (roughly: human vs. not); it should stay, but stop being
   treated as if it were sufficient on its own.
4. **Authenticator bindings** — the joins to the three authentication mechanisms that already
   exist elsewhere in the project but are not currently linked to the identity record: the
   database-connection role (`principal_role`, which already exists), the per-invocation stamp
   (which exists, but per §2.5 below should deliberately stay *not* durable — its whole value is
   that it is invocation-scoped, not identity-scoped), and a cryptographic key fingerprint (which
   does not exist yet, and per the GPG trust-layer design's own §6, should apply to human
   principals only). Each binding should be dated and independently revocable.

The consultant explicitly guards against over-typing here, echoing ADR-0000's own "do not type
everything" caution: the goal is not to build per-deployment qualification bureaucracy that a
single-human deployment has no way to actually exercise. The discriminator the consultant
proposes: does the missing type foreclose a *class* of defect that has actually been witnessed?
Role-binding forecloses a class already witnessed (the reviewer/reviewer2 ambiguity in §0), so it
earns a real slot now. Competence machinery only earns a slot — not yet working machinery —
because it becomes load-bearing only once acts are actually graded against competence bands,
which nothing in the system does yet.

### 2.3 Cross-principal relationships

The existing `acts_for` column, the consultant judges, is simply the wrong type for what it is
trying to represent: it is single-valued (a principal can point at only one other principal),
undated (no record of when the relationship started or ended), kind-less (it cannot distinguish
"delegates for" from any other kind of relationship), and — per §0's live query — entirely unused
across more than 1,800 rows of the panel deployment's history. The kernel already has the right
pattern for this elsewhere: lineage delta s30 introduced *typed dependency edges* for work items
(a small table recording, for each pair of related work items, what kind of relationship links
them). The consultant proposes the identical move for principals: a typed, dated,
actor-attributed edge table drawn from a small, closed vocabulary of relationships this project's
own lived evidence actually needs — `acts-for` (delegation, the one relationship the current
column already names, just done properly); `dispatched-by` (supervision — today only inferable
indirectly, by matching up pairs of stamps, never recorded directly); `same-natural-person` (the
`bork`/`maintainer`/`commissioner` case from §0 — currently invisible to any auditor who doesn't
already know); `succeeds` (one principal formally taking over a role previously held by another —
the panel's own lived `reviewer` → `reviewer2` transition); and `holds-key` (if this relationship
is not instead modeled directly as one of the authenticator bindings from §2.2.4). Each of these
is a fact an auditor of the panel's own ledger genuinely needed this past week and had no way to
query. The consultant recommends retiring `acts_for` by supersession — this project's term for
formally superseding an old mechanism with a documented new one while leaving the old rows
intact as history — rather than by deletion, consistent with the kernel's general lineage
discipline of never discarding history.

This same typed-relationship design is also what makes a previously-open question in the
project's own ledger (panel row 1343, described there as involving "118 precedents") finally
answerable in general, rather than needing to be litigated case by case. That question, in
essence, was: does registering a name for the purpose of self-review disclosure "taint" that same
name's later reuse in an independent review? The consultant's answer: the confusion dissolves
once the three facts currently tangled into one *name* are pulled apart — identity (the name
itself), role-binding (what the name currently signs as), and grade (which should stay denominated
in stamps, not names — delta s29 already does this part correctly: independence grades are
computed from pairs of invocations, never from which name was used). The general rule the
consultant proposes the schema should be able to express directly: **names carry
discoverability; stamps carry independence; role-bindings carry entitlement.** Three separate
facts, three separate homes — the row-1343 confusion exists today only because all three
currently ride on one shared name.

### 2.4 Registration ceremony

The consultant proposes formalizing AC-2's "approval required before creation" directly at the
write path, in code, rather than leaving it as unenforced prose: a registration event that
carries a stated purpose and a reference to the approving principal, with `register-principal`
refusing — or, mirroring the honesty pattern lineage delta s25 already uses for its own
commission-signing modes, grading as `LAZY` (s25's vocabulary for a commission signed with
less than its full ceremony: the act is recorded but carries a typed mark of its reduced
grade rather than passing as fully signed) — a bare registration that supplies no purpose or
approver. The silent-duplicate-registration no-op described in §0 becomes a loud, visible
refusal under any variant of this design; the consultant flags this specific piece as unambiguous
and cheap to fix regardless of which broader design is chosen.

### 2.5 What stays deliberately un-typed

Not everything should be pulled into this new structure. The stamp mechanism should remain
exactly what its own header already calls it — a tripwire, not an authenticator — and nothing in
this design should promote it into something it is not. Agent-held cryptographic keys should stay
refused, per the GPG trust-layer design's own §6. Managerial and financial independence (the two
dimensions §1.3 showed cannot be substantiated by any schema in a single-human deployment) should
stay explicitly unclaimable by computation; if the independence vocabulary keeps those two values
at all, the consultant recommends the spec require them to be either explicitly human-attested,
or refused outright, in single-human deployments.

**Section 2 confidence, as stated by the source:** high on the diagnosis and on the
event-sourced direction generally — the consultant notes this is not a novel idea being imported,
but the kernel's own already-established idiom, simply not yet applied here. Medium on the
specific proposed role vocabulary and on exactly where the rung-1/rung-2 split should fall — the
consultant states plainly that these are design judgments the eventual spec's author and the
maintainer should make themselves, and notes explicitly that, per the terms of this commission,
the consultant has not written the spec.

---

## 3. The downstream deployment's invented practice, assessed

This section assesses a procedure the panel deployment built for itself, entirely independently,
to work around gaps in the current schema: a role-name-governance process (recorded at panel
ledger row 1729, with the full commission that led to it at row 1691 and the actually-executed
sequence of registrations at rows 1736–1754). Under this procedure, before registering a new
principal name, the deployment's orchestrator: proposes the new name with a stated purpose; walks
the *live* roster of existing principals, arguing explicitly why the proposed name is
distinguishable from each existing one; obtains an independent countersign (from a different
actor than the proposer); only then gates the actual registration on that countersigned
attestation; and refuses the whole proposal if any step fails. Four purpose-named principals were
registered under this procedure, each with a recorded job description and sign-off.

**Read against AC-2 (§1.1), what this procedure gets right — and is worth formalizing into the
schema itself:** approval genuinely precedes creation (AC-2's core requirement — and the
consultant notes the panel arrived at this shape entirely from first principles, without knowing
AC-2 existed, which the consultant reads as strong independent evidence that the requirement is
actually load-bearing, not merely a standards checkbox). The roster walk functions as an
anti-duplication check — precisely the check the schema's own silent `ON CONFLICT DO NOTHING`
behavior actively undermines; the human procedure is compensating for a real kernel defect. The
stated purpose is concrete enough that a later duplicate proposal could actually be detected as
one. A conflict-of-interest carve-out — the `item-countersign` principal may not countersign
proposals about registering itself — applies separation-of-duties reflexively, to the
registration process about itself, which the consultant calls "a genuinely sophisticated touch."
And the whole procedure produces a ledger-native record, rather than living only in someone's
memory or a chat transcript.

**What the procedure gets wrong, or simply cannot get right by procedure alone, without schema
support:**

- **(a)** The kernel has no way to distinguish a registration performed under this careful
  procedure from a bare, ungoverned one — `register-principal` still works with no proposal row
  behind it at all, so the procedure's actual guarantee is, in practice, exactly the kind of
  unenforced "verbal policy" this project's own backflow document already indicts elsewhere as
  insufficient. Per [ADR-0011](../../law/adr/0011-mechanization-discipline.md) Rule 2 ("a failure
  shape that recurs after being described converts to a mechanism, not more prose"), this is
  precisely the situation §2.4's proposed write-path mechanism is meant to address.
- **(b)** The role/purpose the procedure so carefully records ends up living in the free-form
  prose of a decision row — unqueryable, and not joinable to whatever acts are later signed
  under that name. §2.2's item 2 (a typed role/purpose binding) is the proposed home for this.
- **(c)** The procedure's final step files its record only in the panel deployment's own ledger —
  the right call for that one deployment, but it makes the procedure a house rule invisible to
  every *other* deployment of this harness; formalizing it at the harness level is exactly what
  the spec this consult feeds is for.
- **(d)** The procedure governs only a principal's *birth* — it has no way to handle revocation,
  succession, or the "these are actually the same person" case, all three of which the very same
  deployment session needed shortly afterward (when retiring the `author` principal) and had no
  way to enforce procedurally.
- **(e)** The default sign-off reviewer used by the procedure is itself an identity with no
  formally bound entitlement to review anything — the procedure bootstraps itself on exactly the
  same gap (unbound reviewer entitlement) that it exists to work around for everyone else.

None of these five points, the consultant stresses, are criticisms of the deployment or the
people who built the procedure — they are simply the honest boundary of what a human-run
procedure can accomplish without schema support behind it. As a candidate for formalization: the
consultant recommends adopting the procedure's overall *shape* (propose → roster-walk → 
independent countersign → gate), moving its *enforcement* down to the write path in the schema,
and giving its *purpose* field a real type.

**Section 3 confidence, as stated by the source:** high — this section is a direct-evidence
assessment of artifacts the consultant read in full, not an inference from secondary description.

---

## 4. Closure-statement candidate

This section offers a candidate **closure statement** — this project's formal name, defined in
[ADR-0000's 2026-07-02 amendment](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
for a defect-class claim that is checkable rather than merely asserted. A closure statement has
three required parts: (1) an invariant, stated in its most general form; (2) an explicitly
enumerated quantification universe — every axis of the problem, and every sibling surface the
same shape occurs on, with anything deliberately excluded named as excluded rather than silently
dropped; and (3) a denomination check — every bound in the claim must be measured in the actual
resource that matters, never a proxy. This section is offered as a *candidate* for the spec that
follows this consult to adopt, refine, or reject — it is not itself the ratified spec.

**Invariant (candidate, stated in its most general form):** every act the kernel records is
attributable to an identity whose registration, current standing (active, suspended, or
revoked), role entitlement, and authenticator bindings are themselves recorded as append-only,
attributed facts; no act is acceptable under an identity whose standing does not permit it at the
time of the act; and no fact about an identity is ever mutable or unattributed.

**Quantification universe** — enumerated explicitly, so that whatever spec follows this consult
can be checked against this exact list:

*Axis A — every place in the kernel that currently asks "who" (the sibling surfaces a fix here
must not silently leave behind):*

1. `ledger.actor` and its NOT NULL constraint, plus `set_actor`'s connection-default stamping.
2. `principal_role`, the database-connection-role axis of attribution.
3. The stamp pair (`stamp_session`, `stamp_agent`) plus the delta-s23 per-invocation token.
4. `validate_review`'s same-actor refusal trigger.
5. `validate_independence` and the s17 independence vocabulary.
6. Delta s29's `discharge_grade` computation, plus delta s34's refusal of writer-asserted grades.
7. `obligation.assigned_by` / `obliges_actor`.
8. `countersign_obligation` / `review_gap` (deltas s15/s32).
9. Delta s25's commission signing modes (FULL being s25's grade for a commission carrying its
   complete signing ceremony; the specific identity assumption here is FULL mode's
   actor-plus-absent-stamp presumption — a human-signed commission is identified by its actor
   with no invocation stamp expected).
10. Delta s18's criterion-reviewer roles (privilege-enforced identity).
11. Work-item claim/close/depends actor attribution.
12. The CLI's `resolve_actor` function — its four wired paths, and its three currently unwired
    paths (`work depends`, `work close`, `resolve-violation`, as described in §0). These three
    unwired paths are explicitly declared **in-universe but not covered by any schema-level fix
    proposed here** — they are CLI-level debt, separately tracked upstream under the name
    "write-path-actor-completion."
13. `register-principal` itself — specifically, the fact that the identity of the *registrar* is
    currently unrecorded.
14. The GPG surfaces: ratification tags, commission signatures, chain-head signatures, and the
    §5 session sign-off (all from `design/MAINT-GPG-TRUST-LAYER.md`).
15. `nla-schema` — a named sibling schema in this project that deliberately opts *out* of
    foreign-keying its actor column to `principal`; the consultant notes this exemption must be
    explicitly re-argued under any new design, never silently inherited from the old one.
16. The Idris formal model (`PrincipalId = Nat`, `Entry.actor`, and the closing argument of its
    `attests` predicate) — any enrichment of the principal concept owes this model a matching
    "s-parity" update (this project's term for keeping the formal model synchronized with the
    schema state it claims to model).
17. The SPA (single-page application) and other read-only surfaces that render actor names to a
    human — misattribution would render visibly there too; these are display-only surfaces, but
    are explicitly in-universe for audit purposes.
18. Every existing deployment's own running kernel instance — the fix, whatever it ends up being,
    travels forward only through the birth chain (this project's mechanism by which a schema
    change reaches new deployments — see
    [GLOSSARY.md#birth-chain](../../GLOSSARY.md#birth-chain)), because runs in this project are
    strictly linear (an already-run world's history is permanently frozen and is never patched in
    place). Existing deployments' *already-misattributed history* is explicitly named as **not
    covered** — it stays as frozen, if imperfect, history.

*Axis B — every lifecycle event an identity can undergo:* registration (governed, per §2.4, or
bare); a duplicate-registration attempt; class assignment, and any later change to that
assignment (the `reviewer`/`reviewer2` model-vs-subagent drift from §0 is the witnessed real-world
specimen of this); role/purpose binding, rebinding, and release; competence grant and withdrawal;
authenticator binding, rotation, and revocation, separately for each kind of authenticator
(database role, cryptographic key — stamps are deliberately excluded from this durable-binding
list, per §2.5); suspension; revocation; succession (one principal formally taking over a role
from another); merging two names later discovered to be the same real-world entity; and renaming
a principal — which the consultant explicitly flags as a case the eventual spec must rule in or
out rather than leaving implicit, recommending it be ruled *out* (principal names should stay
immutable forever; a "rename" should instead be modeled as a succession event). For every one of
the events above, the identity of the registrar or approver, and the time, must also be recorded.
Any event kind the spec deliberately chooses not to support should be named as unsupported, not
silently absent.

*Axis C — every relationship one identity can have to another:* delegation (`acts-for`);
dispatch/supervision (orchestrator-to-subagent; today inferable only indirectly, from stamp
pairs); same-natural-person; role succession; review/countersign edges (these already exist
today: `regards` is the ledger's typed link from a review row to the row it reviews); obligation
edges (already exist); key custody
(human-to-fingerprint); and cross-deployment identity — the same real-world "maintainer" showing
up as a principal in multiple separate deployments — which the consultant explicitly names as
**not covered by this consult** (see §5 below).

**Denomination check:** independence must remain denominated in stamp pairs (the resource that
actually witnesses genuine distinctness between two invocations), never in names; entitlement
must be denominated in role-bindings; standing must be denominated in dated lifecycle events; and
non-repudiation must be denominated in key bindings — a bare *name* must never be allowed to stand
as a proxy for any of these four measurements.

**Presumption of narrowness, checked outward:** per the closure-statement discipline's own
requirement that a first-drafted class boundary is presumed too narrow until checked, the
consultant names one sibling area it most suspects this enumeration still misses: the hooks and
gate layer (the mechanisms that intercept tool calls and enforce policy, including documentation
attestation by out-of-frame reviewer agents), which reasons about "who is acting" entirely outside
the kernel's own tables. The consultant states plainly that this area was *not* audited for
identity assumptions as part of this consult, and flags it for whoever writes the following spec
to sweep separately.

**Section 4 confidence, as stated by the source:** high on Axes A and B — both were derived from
grep-verified code surfaces and directly witnessed events, not inference. Medium on Axis C's
completeness — relationship kinds are, in the consultant's judgment, the least mechanically
enumerable of the three axes, which is exactly why the "presumption of narrowness" note above
exists rather than being omitted.

---

## 5. Deliberately not covered

Nine items the consultant explicitly excluded from this consult's scope, named so that each
absence is a filed deferral rather than a silent gap:

1. **The migration/remediation spec itself.** Per the terms of this commission, this consult
   feeds that spec; it is not that spec.
2. **Key-ceremony operations** — actually generating keys, issuing tokens, or running rotation
   drills — are excluded per the standing deferral discussed and reconciled in §1.5; only the
   schema *slot* for a key binding is in scope of this consult.
3. **Host and perimeter hardening.** Excluded per an existing standing ruling; not re-raised
   here.
4. **Cross-deployment / federated identity** — SP 800-63-3's FAL axis (§1.2), i.e. the question
   of one real maintainer identity spanning many separate deployments. The consultant judges this
   real but premature to design before per-deployment identity is itself sound; it is named here
   so it is a filed deferral rather than a silently missed one.
5. **Multi-human quorum / governance.** The GPG trust-layer design's own §5 deferral (one human
   today) stands unchanged by this consult.
6. **A ruling on panel row 1343 on the maintainer's behalf.** §2.3 supplies the *frame* for
   answering it (names, stamps, and bindings as three separated facts) but the consultant
   explicitly declines to make the taxonomy ruling itself — that remains the maintainer's call.
7. **Identity assumptions inside `hooks/` and the ASP-based logic engine (`engine/lp/`).** Not
   audited as part of this consult — named explicitly in §4's "presumption of narrowness" note
   above.
8. **Retroactive repair of misattributed history in already-existing deployments.** Foreclosed
   by this project's runs-are-strictly-linear rule; per §4 Axis A item 18, any fix travels
   forward through the birth chain only.
9. **Exact clause-text conformance claims.** Everything in §1 above is control-*intent* grade;
   a spec that later wants quotable, verbatim clause citations must retrieve and read the primary
   standards documents directly, following the same discipline the project's own safety-critical
   BRIEF already applies to its own citations.

---

## Overall confidence

Stated by the source as a single closing assessment: the consultant holds the *central* finding
— that the principal table is the one surface in the kernel exempt from the kernel's own record
discipline, and that the right remediation is to apply the kernel's own already-established
event-sourced idiom to it, paired with an AC-2/IA-4-style approval ceremony at the write path, a
named-but-not-yet-built G13 competence slot, s30-style typed relationship edges, and an
empty-until-ceremony key binding — with **high confidence**. The consultant states this
confidence is "over-determined": three independent lines of evidence (the standards research in
§1, this project's own existing type-driven-design law, and the panel deployment's own
independently-lived need, assessed in §3) all point at the same overall shape.

## Sources consulted this session

External, web-retrieved: [NIST SP 800-53 rev 5, full text](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf) ·
[IA-4](https://csf.tools/reference/nist-sp-800-53/r5/ia/ia-4/) ·
[AC-2](https://csf.tools/reference/nist-sp-800-53/r5/ac/ac-2/) ·
[IA-5](https://csf.tools/reference/nist-sp-800-53/r5/ia/ia-5/) ·
[AU-10](https://grcacademy.io/nist-800-53/controls/au-10/) ·
[NIST SP 800-63-3](https://pages.nist.gov/800-63-3/sp800-63-3.html) ·
[SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) ·
[10 CFR 50 Appendix B, eCFR](https://www.ecfr.gov/current/title-10/chapter-I/part-50/subject-group-ECFR89aa6ca4aada73c/appendix-Appendix%20B%20to%20Part%2050) ·
[10 CFR 50 Appendix B, Cornell LII](https://www.law.cornell.edu/cfr/text/10/appendix-B_to_part_50) ·
[AdaCore, "A Fresh Take on DO-178C Software Reviews"](https://www.adacore.com/blog/a-fresh-take-on-do-178c-software-reviews) ·
[ISIT independent-verification white paper](https://www.isit.fr/documents/2114/safety_assurance_through_independent_verification_white_paper_v3.3.pdf).

In-repository, read directly: the eight LAW files the commission named
([CLAUDE.md](../../CLAUDE.md), and [ADR-0000](../../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
[ADR-0011](../../law/adr/0011-mechanization-discipline.md),
[ADR-0012](../../law/adr/0012-compositional-and-structural-hygiene.md),
[ADR-0013](../../law/adr/0013-execution-integrity.md),
[ADR-0014](../../law/adr/0014-executor-second-opinion.md),
[ADR-0017](../../law/adr/0017-the-zero-context-reader.md), and
[ADR-0018](../../law/adr/0018-consults-are-not-front-loaded.md)); every file under
[`kernel/lineage/`](../../kernel/lineage) numbered s13 through s39 (grep-swept, not individually
read in full); [`bootstrap/templates/led.tmpl`](../../bootstrap/templates/led.tmpl); the
`attest-tags` operator verb; [`design/MAINT-GPG-TRUST-LAYER.md`](../../design/MAINT-GPG-TRUST-LAYER.md);
[`law/briefs/safety-critical-logging/BRIEF.md`](../../law/briefs/safety-critical-logging/BRIEF.md);
[`law/STANDARDS-REGISTRY.md`](../../law/STANDARDS-REGISTRY.md);
[`design/Autoharn.idr`](../../design/Autoharn.idr); `AUTOHARN_BACKFLOW.md` (cited as a named artifact, not a
resolving link — see §0); and, read read-only via direct SQL query, the panel deployment's own
ledger rows 407/408, 415, 1306–1343, 1406–1417, and 1691–1769.
