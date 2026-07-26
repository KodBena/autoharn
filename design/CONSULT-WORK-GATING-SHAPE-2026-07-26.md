# CONSULT-WORK-GATING-SHAPE-2026-07-26 — work gating and flexible access control: the sketch judged, the shape proposed

<!-- doc-attest-exempt: ADR-0014 fresh-context consult deliverable awaiting the maintainer's
read (commission ledger rows 1285/1286, re-dispatched after rows 1297/1298 discarded the
prior run for a pre-framed brief). Consult transcripts/deliverables are banked as delivered;
fidelity is the value. Removal condition: superseded by the maintainer's ruling on this
document or by the spec that follows it. -->

**Provenance.** Fresh-context consult under ADR-0014's second-opinion posture and
ADR-0018's no-front-loading rule: the commission carried the witnessed problem, the
evidence list, and the LAW — plus the maintainer's own sketch, supplied *for adversarial
judgment*, with a symmetric mandate (destroy what is wrong, build the right shape at
whatever size the need actually is; neither direction pre-framed — the row-1298 repair).
Read-only consult; this file is the one write. Sources read this session, in full unless
noted: CLAUDE.md; law/adr/ 0000 (incl. the 2026-07-02 closure-statement amendment and
Revisit #4), 0002 (opening/Decision), 0008 (Decision spine), 0012 (principle map via its
load-bearing citations), 0014, 0017 (via its instance bindings), 0018, 0020;
kernel/lineage/ s17 (both files), s21, s39, s40, s41, s43 (header+Elements), s45;
engine/lp/ledger_defeat.lp and ledger_belief.lp headers; s36 and s46 headers;
tools/dispatch_principal.py; design/ORCH-DISPATCH-PRINCIPAL-WIRING.md,
MAINT-GPG-TRUST-LAYER.md, FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md,
FABLE-SETUP-TUI-PRINCIPALS-AUTHORITY-SPEC.md, FABLE-DISCHARGE-PROBES-SPEC.md,
RECOVERY-MODE-SIGNED-AUTHORITY-NOTE.md, FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md,
FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22.md, AUDIT-AC-IA-POSTURE-2026-07-21.md;
GLOSSARY.md (#judge and neighbors); ledger rows 1285, 1297, 1298, 1350 via `./autoharn led
show`. Witness grades in this document: every mechanism claim cites the file read; nothing
was executed against a live or scratch world (read-only bounds), so behavioral claims are
READ-FROM-DDL, marked where it matters, never presented as run output.

The maintainer's sketch, verbatim (row 1285): *"we're going to need to service a need to
prioritize work, and I say it's (possibly signed) predicates against (possibly signed)
facts... certain work items could be gated as never before v2, though note: human/LLM
judgement has to be applied to encode the gates into something that can actually be
checked... I have a vague sense that I could e.g. sign an allocation and its supersession
(requiring authority to supersede, or something like that) would flip the switch... this is
bringing together so much that we have been doing in an ad-hoc manner thus far, like
requiring counter-signatures for split-work, whose mechanical guarantees I am not, to be
frank, quite sure how it is even guaranteed. It would be nice if it could all be
consolidated under a DAC (which is the only AC mechanism I think we can work with without a
Fable->Opus demotion)."*

**The size finding, stated first because the mandate makes it the headline judgment and
because the prior run died on it:** the two halves size in opposite directions. The
work-gating half is SMALLER than the sketch — the flagship "not before v2" case needs zero
new kernel machinery, because s39 blocks-start plus a milestone-item convention already is
the gate, and the judgment-encode/mechanical-evaluate split the sketch demands is exactly
the split s39 and the discharge-probes spec already drew. The access-control half is
LARGER than the sketch — "requiring authority to supersede" is not a signature bolt-on but
the entitlement-enforcement kernel arc the corpus has been converging on from three
independent directions (s41's own named follow-on, the base consult's R2/D3, the AC/IA
audit's AC-3/AC-6 downgrades), plus one genuinely new piece this consult adds: rooting the
authority-granting acts themselves in a chain that terminates at the signed genesis, so
"who may bind roles / suspend / supersede an allocation" stops being "any active
principal" (the IA-4 clause-(a) gap the audit found in `registration_write`). Destroy the
signed-predicate machinery; build the entitlement enforcement.

---

## 0. Ground truth first: what the existing mechanisms actually guarantee

The commission asks this be established, and the sketch's own uncertainty ("whose
mechanical guarantees I am not... sure how it is even guaranteed") makes it the right
foundation. Four mechanisms, four different guarantees, none interchangeable.

### 0.1 The s17/s21 countersignature stamps

Mechanics (read from `kernel/lineage/s17-stamp-mechanism.sql` and
`s21-session-aware-distinctness.sql`): a PreToolUse hook injects
`app.vendor_session/agent/ts/hmac` GUCs on the intercepted psql path; a BEFORE INSERT
trigger derives the row's stamp columns from those GUCs only (writer-supplied stamp
columns are overwritten); `stamp_valid` recomputes HMAC-SHA256 over
`session|agent|ts` against a secret held in a kernel table the subject role cannot read
(SECURITY DEFINER verdict function; ±300 s freshness window). A present-but-invalid stamp
refuses the write; an absent stamp records `stamp_verified=false`. Independence-claiming
reviews (`technical`/`managerial`/`financial`) are refused unless the review row is
verified AND its `(stamp_session, stamp_agent)` pair differs from the regarded row's pair
(s21; NULL half = not distinct, fail-safe); `managerial`/`financial` additionally require
a human-class actor (s41 D-6).

**So the countersignature guarantee is exactly this:** *"the review and the work it
regards were written by two distinct tool invocations — distinct (session, agent) contexts
— as witnessed by the interception hook, under one shared apparatus secret, on one host."*
Three honest bounds, all stated in s17's own LIMITS: (1) it is a **tripwire, not
authentication** — the secret lives in the same trust domain as the writer's OS user and
is in principle hunt-able; (2) it distinguishes *invocations*, not *principals* — it says
nothing about who operated either invocation, and a subagent dispatched by the same
orchestrator is a distinct invocation without being an independent party (the finding-6
granularity gap); (3) bypassing the intercepted path yields an unverified row, which
fail-safes: the independence claim is refused, never falsely admitted. The maintainer's
instinct in row 1285 — "independence is stamp-distinctness of INVOCATIONS under one shared
secret, not per-principal authority" — is exactly right, and the DDL confirms it.

### 0.2 Attribution (s40/s45) and the LED_ACTOR channel

Strict attribution guarantees every accepted row resolves to a registered, currently
non-suspended, non-revoked principal — either explicitly (`LED_ACTOR`, refused loudly on
an unregistered name; `tools/dispatch_principal.py` is the preflight) or via a declared
standing default (a recorded event, never a silent map row). This is **honest
bookkeeping, not authentication** — s40's own LIMITS: "a declared standing default still
AUTHENTICATES nothing... never overclaims IA-2." The declaration says who the connection
speaks for; nothing verifies who is at the keyboard or which model is in the seat (the
vendor ceiling, argued and standing).

### 0.3 The hash chain and the write boundary (s26/s42/s43)

Every write goes through five SECURITY DEFINER boundary functions (granted role holds no
INSERT anywhere); every refusal is a committed, unretractable, journaled `write_refused`
row returned as a typed verdict; every column is inside the row-hash chain (s42). Guarantee:
**tamper-evidence and refusal-completeness inside the trust domain** — a superuser can
still tamper, detectably against a signed head, and that bound is disclosed in every
delta's LIMITS.

### 0.4 Where the ed25519/GPG layer actually reaches today

Read from MAINT-GPG-TRUST-LAYER.md, FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md, and the s41
key-binding DDL. The private key lives with the human, outside the host trust domain —
that is the one property no in-domain mechanism can imitate. Reach, exhaustively:

1. **Signed ratification tags** (`ratified/*`): one signature pins the entire repository
   state — law, gates, and, load-bearingly for this consult, every registered predicate
   and policy file in the tree at that commit.
2. **SIGNED commissions**: detached signature over the commission text;
   `verify-commission` reports VERIFIED | UNSIGNED | FORGED-OR-CORRUPT. "The maintainer
   asked for X" becomes unforgeable by any agent or host compromise.
3. **Signed chain heads**: at run close, the head hash is signed; retroactive ledger
   alteration — including by the superuser — becomes provable against the signed head.
4. **The signed genesis ceremony** (on by default at world birth): keygen, public key into
   the deployment's `keys/`, founding commission signed, verification witnessed live.
5. **The s41 key-binding slot** (`principal_key_bound`, human subjects only, OpenPGP-v4
   fingerprint shape-checked): the principal↔key binding is representable and
   empty-until-ceremony; agent keys are refused by ratified design (§6: an agent's key
   lives in the domain it would attest — "a glorified HMAC wearing a stronger uniform").

What does NOT exist: no allocation, gate, delegation, or revocation act is signed today;
no verb verifies a signature against a *principal's bound key* (verify-commission checks
the deployment's keys/ directory, not the s41 binding); nothing signs automatically, by
ratified refusal.

### 0.5 The terms of art, so the spec after this consult can use them precisely

- **Data-origin authentication**: the verifier learns which key produced the message.
- **Integrity**: the signed bytes were not altered (a detached signature over canonical
  text gives both).
- **Non-repudiation**: the signer cannot later plausibly deny the act — requires the key
  to live only with the signer (hardware token preference is this requirement, costed).
- **Existential unforgeability under chosen-message attack (EUF-CMA)**: the standard
  formal bar for "non-forgeable" — no adversary can produce a valid signature on ANY new
  message, even after seeing signatures on messages of its choice. Ed25519 meets it; this
  is the property the maintainer's "non-forgeable" asks for, and "signature conformance"
  is not the term of art — the correct decomposition of "a conformant, non-forgeable
  delegation/revocation act" is three separately checkable properties:
  1. **well-formed** — the act parses as its typed kind with its kind-shape columns
     (kernel CHECKs, already built);
  2. **authentic** — bound to its author at the author's honest grade (signature verified
     against a **trust anchor** — the pinned public key — for humans; attribution + stamp
     for agents; see §B.2);
  3. **authorized** — the author held, at declared event time, in-force authority for
     that act, established by a **delegation chain** (the SPKI/SDSI-lineage idea: a chain
     of grants each itself authorized, terminating at a root of authority) — the piece
     that is representable today (s41 `acts-for`, `principal_role_bound`) and enforced
     nowhere (s41's own "recordable, NOT gating").

  A "valid revocation" is the same three checks on a superseding act, plus s45's
  supersession discipline (same-kind, identity-continuous — already kernel-enforced for
  the standing-lifecycle kinds).

---

## A. The sketch, element by element

**A1 — "prioritize work... predicates against facts." UPHELD as architecture, with one
cut.** Predicates-over-facts is not a proposal; it is a description of the kernel as
built: every gate in the lineage is a predicate (trigger/CHECK/view) over ledger facts,
evaluated mechanically at write time, with the ASP layer deriving the same verdicts
independently and `./judge` holding the differential in AGREE. The cut: **prioritization
and gating must not share a mechanism.** A gate is fail-safe enforcement (a refusal at
claim time); a priority is a defeasible ordering someone reads (a derived view, like
`work_startable` ordered by whatever policy). Nothing in the kernel should ever refuse a
claim because something else is "higher priority" — that is an orchestrator's judgment,
and freezing it into a refusal would manufacture false blockers. Prioritization stays a
read surface; only gating gets enforcement.

**A2 — "(possibly signed)" on both nouns. REFUTED in the general form; survives at
exactly the human-authority moments, where it is already built.** Two separate
refutations:

- *Signed facts.* Agent-written facts must not be signed — the ratified §6 argument is
  correct and this consult re-derives it independently: an agent-held key lives in the
  trust domain it would attest, adds nothing over the HMAC stamp, and would *launder* —
  a verifier who sees "signed" infers non-repudiation that does not exist. Facts already
  carry layered, honestly-graded authenticity (stamp + attribution + chain + signed
  head). The only facts whose signing adds a real property are human authority acts
  (allocations, ratifications, closures of authority-bearing items), and for those the
  SIGNED-commission mechanism exists, is witnessed, and costs one gpg line.
- *Signed predicates.* A predicate is code. Signing an individual predicate buys nothing:
  evaluation runs on the same host, so a tampered evaluator defeats a signed predicate
  exactly as easily as an unsigned one — the signature would attest the text while the
  threat is the execution. The controls that actually govern code are already law:
  predicates enter through the commit path and review (the discharge-probes spec's own
  "probes are code... the sweep executes only registry entries, never raw ledger text" —
  the fixture-leak lesson, and ADR-0000's 2026-07-18 data-crosses-an-interpreter-
  boundary-as-data amendment), and the signed ratification tag (rung 1) already pins
  every predicate in the tree under one human signature at zero marginal ceremony.
  Per-predicate signatures are signature fatigue (§6's third refusal) re-invented.

**A3 — "gated as never before v2; judgment encodes the gate, evaluation is mechanical."
UPHELD — and the flagship case is already built.** s39 is precisely this: a typed
`blocks-start` edge, refused-with-teaching at claim time, cycle-refused at construction,
with `work_startable` as the honest "what may I start" read. "v2" is representable today
as a work item (a milestone); "never before v2" is one `led work depends <slug>
v2-release --type blocks-start` edge. The human/LLM judgment is spent exactly once, at
encoding (choosing to draw the edge); evaluation is a mechanical membership test the
kernel already performs. What s39 does not cover — conditions that are not "a work item
reached closed" — is real but smaller than it looks; §B.4 disposes of it without a
predicate language.

**A4 — "sign an allocation and its supersession (requiring authority to supersede) would
flip the switch." The switch: UPHELD, already the house idiom. The authority: UPHELD as
the need. The signature as the enforcement mechanism: REFUTED for agents, correct for
humans.** Supersession-as-the-switch is not new — it is the kernel's one retraction
mechanism (s31), and s45 already enforces the WHAT half of supersession discipline for
the standing-lifecycle kinds (same-kind, identity-continuous, revocation
terminal-by-type). What is missing is the WHO half: nothing checks that the superseding
actor holds authority over the superseded thing — any active principal may supersede an
allocation, bind a role, or register a principal (the audit's IA-4 clause-(a) finding:
`registration_write` "accepts a registration naming any actor as the assigning party,
with no check that the assigning actor holds authority to register"). The right
enforcement is not signature verification per act — that would demand agent keys, refused
— but an **in-force-authority membership test at the s43 boundary** (§B.3), with the
signature reserved for the human grade: an allocation whose flip must survive host
compromise is a SIGNED commission, and its supersession is SIGNED symmetrically (the
recovery-mode note's two-signature shape, generalized). Grade the guarantee honestly:
in-domain acts get boundary-enforced authorization; human-anchor acts additionally get
EUF-CMA non-repudiation.

**A5 — "consolidate the ad-hoc mechanisms (countersignatures for split-work...)."
PARTIALLY UPHELD — consolidate the decision point, not the mechanisms.** §0 shows the
mechanisms are not redundant copies of one thing; they are four distinct guarantees at
four grades (invocation distinctness; declared identity; tamper-evidence; human
non-repudiation). Merging them would collapse grades that the record's honesty depends on
keeping distinct — the corpus's whole standards posture is built on never letting a
weaker guarantee wear a stronger one's uniform. What IS duplicable, and should be
consolidated before it duplicates, is the *authorization decision point*: today
independence checks live in `validate_independence`, standing checks in `set_actor`,
supersession discipline in `validate_supersession_target`, claim gating in
`validate_work_item_claim` — all correctly single-homed so far, but entitlement, zone,
and taint conjuncts are queued to arrive. The consolidation that matters: **one factored
acceptance predicate per act class, inside the s43 boundary** — the DEPTH consult's D3
seam, which this consult reaches independently and endorses (noting honestly: same model
lineage as that consult, so this is same-class corroboration, not cross-class). Work
gating needs no new locus at all — s39's claim leaf already sits inside the s35
dispatcher family.

**A6 — "consolidated under a DAC (the only AC mechanism... without a Fable→Opus
demotion)." REFUTED as stated; the worry behind it is answered differently.** Postgres
grants are literal DAC and remain exactly right as the *substrate*: who may connect, who
may execute the boundary functions, who may read which views (s18/s20/s43 — the AC-6
layer). But pushing the *semantic* authority layer down into grants would be the wrong
type: (1) grants cannot express "actor P holds role reviewer in-force for act class K"
without a combinatorial role-per-(principal×act) explosion and dynamic GRANT churn on
every delegation change; (2) GRANT/REVOKE are not ledger events — not attributed, dated,
superseded, hash-chained, or journaled-on-refusal — so authority would acquire a second,
unaudited home, an ADR-0012 P1 violation against the very facts s40/s41 just gave one
home; (3) the discretionary-ness DAC names (the object owner grants at discretion) is not
actually the model here — authority derives from the maintainer's root, through
delegations, which is relationship-derived access control over event facts. The house
already built most of it. And the demotion worry is answered by that same observation:
nothing in §B requires new invention at authoring time — the shape is the composition of
mechanisms that exist (s39, s41, s43, s45, GPG rungs), and the one kernel arc it needs
(entitlement enforcement) is already the named, scoped follow-on that Sonnet builds from
a ratified spec like every delta since s45. Simplicity is served by finishing the built
design, not by demoting to grants.

---

## B. The shape

Four layers, bottom-up. Each names its mechanism, its guarantee grade, and its consumer
(the row-1906 test).

### B.1 The authority model: roles at the leaf, delegation at the root, overlap resolved

The maintainer suspects roles and delegation overlap. They do, and the resolution is that
they answer two different questions and should be wired in series, not merged:

- **A role binding** (`principal_role_bound`, in-force) answers: *may P perform acts of
  class K in this world?* It is the ENFORCEMENT KEY — the fact the boundary checks at act
  time. Role names stay free text by ratified ruling (§9(c)); which role a world's
  configuration requires for which act class is deployment policy (the s36
  graded-token idiom), not kernel vocabulary.
- **A delegation** (`principal_relation_asserted`, relation `acts-for`, in-force) answers:
  *from whom does P's authority derive?* It is the PROVENANCE CHAIN — what authorizes the
  *authority-granting acts themselves*. A role binding written by Q is valid-at-birth only
  if Q holds granting authority, which Q holds by being the root or by an in-force chain
  of acts-for/grants terminating at the root.
- **The root of authority** is the world's genesis: the founding commission, signed by
  default since the signed-genesis ceremony, naming the maintainer principal. This is the
  trust anchor in both senses — the GPG public key in `keys/` for authenticity, and the
  genesis authority row for authorization chains.

So: RBAC is the per-act check; delegation is the meta-level that makes the RBAC facts
themselves conformant acts. Neither subsumes the other, and competence grants stay a
third, non-enforcing thing (recorded belief with a basis — the ratified placeholder;
gating on placeholder band vocabulary would enforce guesses).

**Chain evaluation.** "Q held granting authority at event time" is transitive
reachability over in-force events — in SQL, a recursive view in the exact shape of
`work_blocks_start_would_cycle` (depth-capped, in-force-filtered); in ASP, a two-rule
closure in the exact shape `ledger_defeat.lp`/`ledger_support.lp` already stratify
(beside `in_force/1`, never into it). This is the honest answer to the commission's
"where does predicate evaluation belong": **enforcement predicates live in SQL inside
the kernel/boundary** — the only evaluator inside the AC-25 trust boundary, the only
place a refusal is a journaled typed verdict; **the ASP layer is the independent second
derivation** of the same verdicts, held in AGREE by `./judge`, and the natural home for
the chain/closure queries (reachability is its home ground); **a free-form predicate
language lives nowhere** (§B.4). The authority-chain layer should be specced with its
ASP twin from birth, not filed as an I2-style pairing debt.

**Depth and revocation semantics, fixed rather than left vague:** a chain link is dead
the moment its carrying event is superseded-inactive or its subject principal leaves
active standing — evaluated fresh at each act, never cached (the s40 "computed at read,
never stored" law). Suspending a delegate therefore severs every chain through them
prospectively while leaving their past accepted acts credited unless positively defeated
— which is not a new choice but the ratified I5 asymmetry (s45 Element 3: "lifecycle
standing NEVER conditions defeat force"), inherited here deliberately.

### B.2 Authenticity of the acts, mechanism by mechanism (the "conformant and
non-forgeable" requirement, discharged per §0.5's three properties)

| Act | Well-formed | Authentic | Authorized |
|---|---|---|---|
| Delegation / role grant / suspension / revocation by an **agent principal** (orchestrator granting a builder) | kind-shape CHECKs (s41/s45, built) | DB login (`session_user`, server-witnessed) + strict attribution + stamp tripwire + hash chain; no signature, by ratified refusal — grade stated as bookkeeping, never IA-2 | NEW: boundary check — actor's in-force chain to root covers the granted scope (§B.3) |
| The same acts by the **human maintainer** | same | same, PLUS optional SIGNED mode: detached Ed25519 signature over the act text, verified against `keys/` AND (once the key ceremony binds it) the actor's in-force `principal_key_bound` fingerprint — closing the gap that `verify-commission` today checks a directory, not the principal binding | root of chain; trivially authorized |
| **Supersession/revocation of a SIGNED act** | s45 supersession discipline (built for lifecycle kinds; extended to allocation kinds by the spec) | must itself be SIGNED — signature symmetry: an act whose force rests on non-repudiation cannot be withdrawn by an act with less (the recovery-mode note's two-signature shape, generalized to one rule) | boundary check as above |
| **Key binding / key revocation** | s41 fingerprint shape CHECK (built) | the binding act SIGNED by the key being bound (proof of possession — otherwise a binding is an assertion); revocation by GPG revocation certificate (§7, documented) plus the s41 retraction event | maintainer-root only in v1 (one human) |

Non-forgeability, graded honestly: human-grade acts are EUF-CMA-non-forgeable (forgery
requires the private key, held off-host); agent-grade acts are non-forgeable only against
actors outside the granted-role write path (boundary + refusal journal + chain), and
tamper-evident-not-tamperproof against the host itself — the same disclosed bound every
delta carries, with the signed head as the closing move. No mechanism claims a grade
above its trust domain; that discipline is the corpus's spine and this shape keeps it.

### B.3 The enforcement point: one factored acceptance predicate at the s43 boundary

The entitlement-enforcement delta family (the D3 arc, already recommended twice and
corroborated by the audit; this consult makes it three independent arrivals) with two
sharpenings from this consult:

1. **Factor the acceptance predicate as a conjunction of typed checks over in-force
   facts**, per act class, evaluated inside the boundary functions, refusals journaled as
   `write_refused` with taught text (all machinery that exists). v1 conjuncts: (a) the
   actor holds an in-force role binding the world's configuration names for this act
   class; (b) for authority-bearing acts (registration, role binding, standing lifecycle,
   allocation supersession): the actor's authority chain roots at genesis (§B.1). Later
   conjuncts (zone, taint, gate-conditions) enter by their own ratified deltas through
   the same point — vocabulary additions to `refusal_surface`/teach-text are
   class-ratified fail-safe; the enforcement point is ratified once.
2. **Solo-world zero-friction by construction, not by toggle**: the scaffold's birth
   sequence already registers maintainer/orchestrator principals, grants competences, and
   records `orchestrator acts-for maintainer` (witnessed in the 2026-07-19 field-test
   birth the audit cites) — the same birth run binds the roles the default configuration
   names, so a solo world's every act passes conjunct (a) exactly as strict attribution's
   declared-default reconciled row 1398. No dormant permissive branch (the s40 lesson).

### B.4 Work gating on top, and the worked example

**The construction, complete:** a gate is a `blocks-start` edge to a milestone work item.
Encoding is judgment (a human or LLM decides the condition and draws the edge — one
recorded act); evaluation is mechanical (the s39 claim-time check, kernel-side);
**the flip is an authority act** — closing or superseding the milestone — which is
exactly where §B.3's enforcement attaches: close/supersession of a gate-bearing milestone
is an authority-bearing act class, so who may flip is a role-binding question, and a
maintainer who wants the flip non-repudiable closes it via SIGNED commission. The
sketch's "sign an allocation and its supersession flips the switch" lands here with
every noun made concrete: the allocation is the milestone item (optionally SIGNED), the
switch is in-force-ness, the authority is the boundary check, the signature is the human
grade.

**Worked end to end — "spa-polish not before v2"** (verbs from `led.tmpl` and s39's own
DDL; refusal text quoted verbatim from `s39-blocks-start.sql:258`; READ-FROM-DDL — this
consult ran nothing; s39 is scratch-witnessed by its own delta's fixture and reaches
worlds born at s39+):

```
./led work open v2-release   --title "v2.0.0 ships"        # the milestone
./led work open spa-polish   --title "SPA polish pass"
./led work depends spa-polish v2-release --type blocks-start   # judgment, spent once

./led work claim spa-polish
  → REFUSED (write_refused row journaled, s43):
    "Ledger policy: claim of work item 'spa-polish' refused — its blocks-start
     antecedent(s) are not yet resolved: v2-release (item is not yet closed).
     Claim and finish each named antecedent first (./led work claim <antecedent>,
     then ./led work close <antecedent> <resolution> ...), or -- if the dependency
     itself is wrong -- correct the record (see design/USER-RECIPES-FAQ.md's
     'Correcting the record' section for the supersession recipe ...)"

# ... months later, v2 ships. The flip, at whichever grade the act warrants:
./led work claim v2-release
./led work close v2-release shipped --witness "tag v2.0.0"
#   under the B.3 delta: accepted only from an actor whose in-force role binding
#   covers milestone closure; optionally commissioned SIGNED for non-repudiation.

./led work startable         # spa-polish now listed (work_startable, s39 Element 5)
./led work claim spa-polish  # accepted; work proceeds
```

Wrong-gate repair is already first-class: the edge row is superseded and re-issued
(the teach-text's own recipe) — and under §B.3 that supersession is itself an
authority-checked act, closing the loophole where anyone could quietly unbolt a gate.

**Conditions that are not work items.** Three dispositions, and then the line is drawn:
(i) most "conditions" are honestly milestones and should be items ("AC-14 ruling
recorded", "v2 shipped", "maintainer approves X" — each is a closable act); (ii)
conditions the kernel can see are candidate future conjuncts through §B.3 (a gate on "no
open work_item_violations for the parent", say) — each a typed, ratified predicate,
added only on a witnessed need; (iii) conditions about the world outside the ledger are
**discharge-probe territory and stay advisory**: a probe (registry code, read-only,
best-effort by ratified posture, row 1286) reports PROBE-WITNESSED-SUPERSEDED /
HOLDS, and an authorized principal closes or re-edges the milestone citing the probe's
output as witness. That is the composition with the postponed probes spec (row 1350),
stated so the two do not fight: **probes recommend the flip; the milestone act IS the
flip; the s39 edge enforces it.** They must not merge — a probe that gates would violate
its own ratified best-effort posture and would execute code on the enforcement path,
and a gate that probes would hang fail-safe refusals on best-effort observations. The
registry-not-ledger-text discipline is shared; the enforcement/advice line is the design.

**No predicate DSL, stated as a refusal:** a general predicate language stored in ledger
rows and evaluated by the kernel is not proposed and should be refused if proposed later
— ledger statements are data, data is never executed (ADR-0000's interpreter-boundary
amendment; the fixture-leak lesson; the probes spec's own §1 rule). Every enforced
predicate is a typed, reviewed, ratified kernel object; every advisory predicate is
registry code. "Nowhere" is the answer for free text.

### B.5 Degradation across the operator-to-adopter horizon

- **Solo maintainer (today):** everything works at zero added friction — birth acts bind
  the roles, gates are opt-in edges, the flip is one close, SIGNED remains a deliberate
  one-line act. The record is complete and attributed, not adversarially independent
  (s17's own honesty, unchanged).
- **Maintainer + agents (the working shape):** dispatch-principal wiring gives builders
  real identities; role gating makes "builder may not close milestones, reviewer may not
  supersede allocations" enforced rather than conventional; the stamp keeps invocation
  distinctness; nothing authenticates agents, and the record says so.
- **Multi-human team:** per-human keys (fingerprints per principal via
  `principal_key_bound` once the ceremony runs), session sign-offs as signed heads (§5 of
  the GPG spec, filed), SIGNED supersession symmetry live; delegation chains now cross
  humans and the acts-for record carries real weight.
- **Adopter / regulated deployment:** conjuncts armed per world via the s36 token idiom
  (role gating alone for a lab; +zone/taint for the defense shape per the DEPTH consult);
  the posture matrix rows this moves: AC-3/AC-6 entitlement halves from BOUNDED toward
  MET, IA-4 clause (a) closed, and Part 11's "authority checks" clause — the audit's
  words, "entitlement enforcement, almost verbatim" — discharged by mechanism.

---

## C. Consolidation, argued per case

1. **One enforcement locus (CONSOLIDATE).** All acceptance-time authority checks —
   entitlement, authority-chain, and any later zone/taint/gate conjunct — evaluate as one
   factored predicate family inside the s43 boundary. Argument: s43 is the only surface
   where a refusal is a committed typed verdict; a second locus would fork the refusal
   record and re-open the class s43 closed. Work gating is already correctly homed
   (claim leaf, s35 family) and needs no move.
2. **The four authenticity mechanisms (DO NOT CONSOLIDATE).** Stamp, attribution, chain,
   GPG stay separate because their guarantees are different truths at different grades
   (§0); merging is exactly the uniform-borrowing the corpus refuses. The consolidation
   the sketch wants is achieved at the decision point (case 1), not by fusing evidence
   types.
3. **Authority vocabulary (CONSOLIDATE the question, keep the records).** Today
   "authority" is scattered across role bindings, acts-for relations, competence grants,
   and registered charters. Enforcement should key on exactly one: in-force role
   bindings, with acts-for as the chain that legitimates binding acts (§B.1). Competence
   stays recordable (ratified placeholder); charters stay documentation. One question —
   "may P do K?" — gets one home; the other records keep their distinct, non-enforcing
   meanings.
4. **Supersession authority (CONSOLIDATE into s45's existing discipline).** The WHO check
   extends `validate_supersession_target`'s already-single home (which s45 itself chose
   over minting a second trigger — the precedent is in its own header) rather than any
   signature-verification parallel path.
5. **Postgres DAC (KEEP AS SUBSTRATE, do not absorb upward or downward).** Grants keep
   answering connection/execution/read questions; the event layer keeps answering
   semantic authority; neither duplicates the other (§A6).
6. **Milestone gating over s39 (CONSOLIDATE by reuse — zero new kernel surface for the
   flagship class).** No `work_gated_until` kind, no gate table: the blocks-start edge
   plus the milestone convention is the mechanism, documented as a recipe. New kernel
   vocabulary only when a witnessed condition class genuinely cannot be a milestone —
   filed then, not speculated now.

## D. What this consult deliberately does not propose, and why

- **Per-row or per-agent signatures, and any agent-held key** — ratified refusal (§6),
  independently re-derived here (§A2): same trust domain, laundered grade.
- **A predicate language over ledger text** — data is not code (§B.4).
- **Signing individual predicates/gates** — redundant with the ratified/* tag that pins
  the tree; signature fatigue.
- **Gating on competence bands** — the band vocabulary is a ratified placeholder;
  enforcing placeholders enforces guesses.
- **Automatic gate flipping from probe results** — probes are best-effort and read-only
  by the maintainer's own ratified posture; the flip stays an authorized, recorded act.
- **Mandatory-access-control labels / trust tiers / DMZ machinery** — the taint/zone arc
  is real, separately elaborated (DEPTH consult), and composes later as boundary
  conjuncts; building it into this shape now would couple two ratification arcs the
  maintainer sequenced apart (row 1350's own logic).
- **Read-path caller identification, host/perimeter work, retroactive changes to any
  existing world, and new cryptography beyond the scoped lift** — standing rulings, all
  respected; the one crypto-adjacent addition proposed (verify against the s41 key
  *binding*, not just the keys/ directory; proof-of-possession at binding) uses only the
  lifted, in-service mechanism and activates only when the deferred key ceremony runs.
- **Prioritization machinery in the kernel** — ordering is judgment over derived views,
  never a refusal (§A1).

---

**Closure statement for the proposed direction (ADR-0000, 2026-07-02 form).**
*Invariant:* every authority-bearing act the kernel accepts — registration, role
binding, delegation, suspension, revocation, allocation/milestone closure and
supersession, gate-edge supersession — is checked at write time against in-force,
event-derived authority rooted at the world's (by-default-signed) genesis, and every
acceptance or refusal is a committed, hash-chained, typed record; wherever an act's
authenticity is below the human grade, the record says so by construction. *Universe:*
act classes — the eight principal_* kinds, work_opened/claimed/closed/depends_on and
their supersessions, commission; principals — human maintainer, orchestrating sessions,
dispatched builders, tool principals, adopter operators; surfaces — the five boundary
functions and their trigger chains, `led` verbs, the scaffold birth sequence, the GPG
verbs, the setup TUI screens; worlds — future births only. *Named as not covered:*
agent authentication (vendor ceiling); reads; probes' external conditions (advisory by
construction); competence enforcement; the live world's history. *Denomination:*
authority in in-force events and chains over immutable principal ids, never names or
grants; gates in typed edges to closable items, never free-text predicates;
non-repudiation in off-host keys only; every refusal a journaled row.

*Point-in-time ADR-0014 consult record, 2026-07-26, awaiting the maintainer's read.
Superseded by his ruling and by the Fable-authored spec (row 1285's own route) that
should follow a yes.*
