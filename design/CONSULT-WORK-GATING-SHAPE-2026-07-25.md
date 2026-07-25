# CONSULT-WORK-GATING-SHAPE-2026-07-25 — refutation of signed-predicates-over-signed-facts; the shape the evidence actually supports

<!-- doc-attest-exempt: ADR-0014 refutation consult (fresh-context, adversarial mandate per
ledger row 1286; ADR-0018's no-front-loading deliberately varied BY the commissioning
maintainer — the sketch was received AS the thing to refute). Awaiting the maintainer's read.
Removal condition: superseded by his disposition of rows 1285/1286. -->

**Provenance.** Fresh-context Fable consult, 2026-07-25. Commission: ledger rows 1285/1286
(the maintainer's sketch and his own request to destroy it, both verbatim there). Read-only
consult; this file is the one write. Sources read this pass: CLAUDE.md; ADR-0014, 0018, 0020
in full; ADR-0000/0002/0008/0012/0017 via their load-bearing citations across the artifacts
below (named honestly: not line-by-line this pass); kernel/lineage/ s17 (both files), s21,
s39, s41 (header + D-1..D-8 + closure), s43 (header), s57 (header) in full or by header;
design/MAINT-GPG-TRUST-LAYER.md, FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md,
FABLE-DISCHARGE-PROBES-SPEC.md, FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md,
FABLE-CONSULT-ACCESS-CONTROL-2026-07-21.md in full; FABLE-CONSULT-ACCESS-CONTROL-DEPTH-2026-07-22
header/summary; law/adr/backlog/README.md; engine/lp/work_items.lp header;
bootstrap/new-project.sh LINEAGE_CHAIN; ledger rows 1284/1285/1286 via `./led show`.

**The one-paragraph verdict, first.** The need is real and smaller than the sketch. Most of
what "gate work items" requires is already kernel law: s39's `blocks-start` edge refuses a
claim whose precondition item is not closed, at write time, with teaching. What is missing is
one representational idiom (a *milestone* work item standing for an external condition such
as "v2 released") and one already-commissioned mechanism to witness it (row 1284's discharge
probes). Signing per-gate adds nothing the threat model asks for and re-creates the
rigamarole class the signed-genesis spec deliberately foreclosed; authority-gated
supersession is a sound instinct pointed at the wrong grain — it is the s41 entitlement
follow-on, which must land once at the write boundary for all acts, never specially for
gates; DAC consolidation is a category error that would flatten four different guarantees
into one vocabulary. The right shape costs approximately zero new kernel semantics.

---

## A. The actual needs, extracted from the evidence

Each need is stated as the evidence supports it, not as the sketch framed it.

**N1 — Sequencing constraints on work, checked at the moment of claim.** "Certain work items
could be gated as 'never before v2'" (row 1285, verbatim). The general form: item X may not
be *started* until condition C holds. Evidence that this is the real grain: s39 exists
because the maintainer commissioned exactly this for item-to-item preconditions on 2026-07-17
("so that a hook can tell the agent 'don't do that, do the right thing instead'", s39 header
verbatim), and it shipped as a kernel claim-time refusal plus the `work_startable` view. The
new need is only the case where C is not another work item's closure but a fact about the
world outside the ledger.

**N2 — The encoding act is human/LLM judgment, applied once.** His own note: "human/LLM
judgement has to be applied to encode the gates into something that can actually be checked"
(row 1285). The discharge-probes spec §2 already states the same split for its own domain:
judgment at declaration, mechanical evaluation, human confirmation. Nothing in the evidence
asks for a general predicate language; it asks that the one-time encoding produce something a
machine can then check.

**N3 — External-world conditions must enter the ledger through a witnessed path.** "v2
released" is not a ledger fact until someone writes it. The evidence for how this project
turns outside observations into record: claims carry witnesses (CLAUDE.md), and row 1284's
probes exist precisely to replace "orchestrator recall" with "witnessed observation + human
confirmation" for facts of this kind.

**N4 — Authority over gate changes.** "Requiring authority to supersede, or something like
that" (row 1285). This is real, and it is not gate-specific: the access-control consult's G1
names it as the one sense of access control that is recorded but nowhere enforced — s41 role
bindings and competence grants "RECORDABLE, NOT YET GATING" (s41 D-5, verbatim), with
entitlement enforcement "the NAMED follow-on ratified amendment ... never smuggled in as a
side effect." A gate's supersession is one instance of the general question "may this
principal perform this act."

**N5 — Understanding what the existing countersign mechanics actually guarantee.** "Whose
mechanical guarantees I am not, to be frank, quite sure how it is even guaranteed" (row
1285). This is a documentation/honesty need, not a build need. The answer exists in the
artifacts and is stated in §B.0 below in one paragraph, because not knowing it is itself a
hazard.

**N6 — Forward compatibility to multi-operator adopters without designing trust tiers now.**
The standing constraint (row 1162 slot discipline; umbrella spec §3 `authn_mode:
single-operator` as v1's value, not the system's identity; s41's key-binding
empty-until-ceremony slot). The gate shape must not need reworking when a second operator
exists.

What the evidence does **not** contain: any consumer for a general priority *ordering*
(rankings, scores, urgency numbers). The commission says "prioritize work," but every
concrete instance given is a *gate* (a binary may-not-start-until), and the named-consumer
test (row 1906) applies: no consumer of a priority number is nameable today, so none is
proposed.

## B. The refutation, element by element

### B.0 First, the answer to N5, because two of the verdicts depend on it

What the countersign/stamp machinery mechanically guarantees, exactly: a verified HMAC stamp
proves *this row was written through the intercepted psql path by an invocation holding a
fresh HMAC computed from the one apparatus secret* (s17-stamp-mechanism: the writer can
neither omit nor forge it; ±300s freshness; fail-closed). s21 then proves *distinctness*: two
rows whose `(stamp_session, stamp_agent)` pairs differ were written by different invocations,
and a review claiming technical/managerial/financial independence is refused unless that
distinctness holds (NULL half = not distinct, fail-safe). The pre-registered limits are part
of the guarantee's honest statement: the hook runs as the same OS user, so the secret is
hunt-able — "A TRIPWIRE, not authentication" (s17, verbatim); a script-mediated write
bypassing interception is unstamped and refused where a stamp is required. So: the split-work
countersign guarantee is **stamp-distinctness of invocations under one shared secret** —
"a different context wrote this review than wrote the work." It guarantees *nothing* about
authority, human identity, or entitlement. That is not a defect to fix by consolidation; it
is a different guarantee (separation-of-duties integrity) than the one the sketch reaches for
(authorization), and conflating them is where the DAC-consolidation element goes wrong.

### B.1 Signing (signed predicates, signed facts, "sign an allocation") — OVERBUILT-FOR-NEED

Three arguments, each sufficient alone.

1. **The threat a signature defeats is not the threat gates face.** A GPG signature's three
properties — non-repudiation, forgery resistance against the apparatus itself,
outside-verifiability (MAINT-GPG-TRUST-LAYER §1) — matter when the host or apparatus is the
adversary. A work gate's adversary is an agent (or an operator in a hurry) talking itself
past a priority *inside* the trust domain. Against that adversary the kernel's existing
machinery is already the right instrument: the gate fact is an attributed, stamped,
hash-chained, append-only row; its check is a write-time refusal; its retraction is a
recorded supersession event. A signature on top defends against an adversary who could
equally well drop the trigger that checks the signature — inside the domain it adds ceremony,
not assurance.

2. **The trust layer's own §6 already refuted the automated variant.** "Anything signed
automatically, by a key stored on the host, is a glorified HMAC wearing a stronger uniform"
(verbatim). Gate flips that happen in workflow — allocations made and superseded as work
proceeds — would be signed automatically or not at all. If signed manually per flip, the
signed-genesis spec's own target is violated: "no further crypto rigamarole" after the one
ceremony, "no signing hooks, no signature gates on ordinary verbs" (§1.5, verbatim) — the
why-PGP-failed friction class, rebuilt on purpose. Signature fatigue converts a deliberate
act into a reflex (§6); a signature that costs no deliberate human moment carries no meaning.

3. **The sound residue already exists and needs no build.** Where a *specific* gate act
genuinely warrants the stronger claim ("the maintainer himself ordered this hold"), SIGNED
commission mode exists today: sign the commission that establishes the gate, verify with
`verify-commission`, done — deliberate, optional, human, zero new mechanism. And the signed
chain head already makes the whole ledger — gates included — tamper-evident against the
apparatus itself, wholesale, which is strictly better than per-row signatures retail.

Verdict: **OVERBUILT-FOR-NEED.** "Possibly signed" survives only as: the establishing
commission MAY be SIGNED, using machinery already shipped.

### B.2 Authority-gated supersession ("flip the switch") — UNSOUND as a gate-special mechanism; SOUND as an instance of the named s41 follow-on

The instinct is right: retracting a gate should require authority. The sketch's location for
it is wrong twice over.

1. **The switch already exists.** s31 uniform supersession + derived current-truth views are
the one retraction mechanism, one home (ADR-0012 P1). A gate that "flips" on supersession is
not a new mechanism to design — it is how every ledger fact already behaves. Designing a
second, gate-specific supersession semantics would mint a duplicate home for retraction.

2. **Authority-gating only gate supersession is incoherent.** If supersession needs
authority, it needs it for *every* authority-bearing act — closing a milestone, revoking an
obligation (s57), retracting a role binding — or the enforcement is a fence with one post.
The house has already named where this lands: entitlement enforcement at the write boundary,
consulting s41 role bindings before accepting an act — "the named follow-on ratified
amendment," explicitly *not* to be smuggled in as a side effect of something else (s41 D-5).
Building it here, for gates only, is precisely the smuggling that clause forbids, and it
would fabricate a category (ADR-0008) where an existing one cleanly fits.

3. **Meanwhile the v1 answer is not "nothing."** Today, supersession already passes through
the s43 SECURITY DEFINER boundary under the grant layer (owner discretion — which IS
discretionary access control, already in service), is attributed under s40 strict
attribution, stamped, and hash-chained. "Who flipped the switch, when, as whom" is fully
answerable now; "may they" waits for the follow-on that answers it uniformly.

Verdict: **UNSOUND** as sketched (gate-special); the need it expresses is **SOUND** and
already has a named, general home whose ratification is a separate maintainer decision (the
AC consult's G1/D-list, pending).

### B.3 DAC consolidation ("it would all be consolidated under a DAC") — UNSOUND (category error), and the desire behind it is served differently

The mechanisms the sketch wants consolidated do four different jobs with four different
guarantees:

| mechanism | guarantee | kind |
|---|---|---|
| HMAC stamps (s17/s21) | distinct invocation wrote it | integrity tripwire / SoD |
| countersign obligations (s15/s20/s29) | a review is owed and its absence is visible debt | process obligation |
| Postgres grants + s43 boundary | only these roles may perform these writes, refusals journaled | authorization (already literally DAC) |
| GPG signatures (trust layer) | a human deliberately vouched; survives host compromise | non-repudiation |

"Consolidating under DAC" either (a) renames three non-authorization mechanisms as access
control — an overclaim of exactly the kind the corpus keeps refusing (the stamp spec's own
"tripwire, not authentication"; the identity spec's refusal to claim IA-2), or (b) rebuilds
them inside one framework, destroying the property that each is enforced at its own strongest
feasible surface (ADR-0011's vocabulary). Either way the ADR-0020 lesson applies: a
re-rendering that files distinct guarantees under one label strengthens claims silently.

And DAC-the-model requires no adoption decision: the grant layer is already owner-discretion
DAC, in service, enforcing the write boundary. There is nothing to migrate to.

The legitimate desire underneath — "I wanted something generic," and "I am not sure what is
guaranteed" — is served by a *statement*, not a framework: the AC consult's six-sense
decomposition and the posture matrix (AUDIT-AC-IA-POSTURE-2026-07-21) already state, per
mechanism, what is enforced, recorded, or absent. If anything is missing it is one page in
the user-guide tier naming each mechanism's guarantee in operator words (§B.0 is the seed for
its stamp entry). Verdict: **UNSOUND** as consolidation; the underlying need is real and is
discharged by naming, not by building.

### B.4 Gates as predicates over facts (and where evaluation belongs) — the general form OVERBUILT; the specific form SOUND and mostly already shipped

The honest, boring answer the commission asked me not to flatter away:

- **A general predicate language over ledger facts is a rules engine**, and it would arrive
with the known costs: predicates become code that someone must review (the discharge-probes
spec just spent its load-bearing line on exactly this — registry code, never executed ledger
text; the fixture-leak lesson), a second evaluator whose disagreement with the kernel's
refusals must then be adjudicated, and a temptation to encode judgment that should stay
human. No evidenced need reaches past the specific form below, so the general form fails the
named-consumer test.

- **The specific form — "may X start?" as a conjunction of closed antecedents — is already a
kernel predicate**, evaluated in SQL at the only place a gate can actually gate: the write
boundary, at claim time (s39's refusal; `work_startable` as the derived read). This is where
it belongs. A gate enforced anywhere else (a hook, an ASP program, a CLI) is advisory by the
action-stream principle; only the kernel refusal is load-bearing.

- **The ASP layer's honest role here is what it already is**: the second producer. The engine
is deliberately descriptive and paraconsistent — "ZERO `:-` integrity constraints," "NO
verdict vocabulary" (work_items.lp header, verbatim) — and it differentials bit-identically
against the SQL floor in `./judge`. Extending `work_items.lp` with the blocks-start
startability predicate so the differential covers it is right and cheap; making ASP the gate
*evaluator* would invert the house architecture (the kernel refuses; the engine reasons).
The raison-d'être claim is not flattered by wiring clingo into a job SQL triggers already do
better; it is honored by keeping the engine the place where an operator can *ask why* — "what
blocks X, transitively, and what retractions would unblock it" is a genuinely deductive
question the .lp layer answers and SQL answers awkwardly. That is a Use-mode consumer, and it
composes with, rather than replaces, the kernel gate.

Verdict: predicates-over-facts as a new evaluator: **OVERBUILT-FOR-NEED**. Gate-as-predicate
in the kernel at claim time: **SOUND — and shipped** (s39, in the birth chain
s15→...→s57 for every future world). The residual build is the milestone idiom below.

## C. The proposed shape

**One sentence: a gate is a `blocks-start` edge to a milestone work item; the milestone
closes on probe-witnessed evidence confirmed by a human; authority over closing and
superseding stays with the write boundary and grant layer today, and becomes role-bound when
the s41 entitlement follow-on lands — the gate representation itself never changes.**

The moving parts, each with its mechanical guarantee named:

1. **The milestone item.** A work item standing for an external condition (`release-2.1.0`).
   No new kind, no new column — `work_opened` as it exists. Guarantee: attributed,
   hash-chained, append-only event (s40, s26/s42); duplicate opens refused (s22).
2. **The gate edge.** `work_depends_on` with `edge_type='blocks-start'` from the gated item
   to the milestone. Guarantee: claim of the dependent is REFUSED by the kernel with teaching
   until the antecedent is closed — a BEFORE INSERT trigger, write-time data constraint, not
   advice (s39 Element 3); cycles refused at construction (Element 2); `work_startable` is
   the derived what-may-I-start-now read (Element 5).
3. **The witness path for the external condition.** A discharge probe registered against the
   milestone (row 1284 machinery, verbatim shape). Guarantee: evaluation is mechanical and
   read-only (registry code, reviewed like code); the sweep writes nothing; "likely released"
   is replaced by observed output. Composition with the sibling spec is read-only in both
   directions: this shape consumes the probe registry and sweep report exactly as any
   consumer may; it does not make probes mandatory, gating, or blocking — the thing that
   blocks is the edge (kernel), the probe only feeds the human close. Nothing in the
   discharge-probes spec needs a single change, honoring its own §4 ("nothing here
   presupposes it").
4. **The close (the switch flips).** A human — the maintainer, or the orchestrator for items
   inside its ordinary closure authority — closes the milestone citing the sweep's observed
   output as `--witness`. Guarantee: witness-carrying close enforced (s22/s29 typed close);
   attributed and chained like every row. Judgment sits exactly where N2 demands: once at
   encoding (writing the probe), once at confirmation (the close). Everything between is
   mechanical.
5. **Early retraction (the maintainer changes his mind).** Supersede the edge row — ordinary
   s31 supersession through the s43 boundary. Guarantee today: only grant-holding roles can
   write at all; the act is attributed, stamped, chained, and `write_refused` journals any
   refused attempt. Guarantee after the s41 entitlement follow-on (a separate ratification,
   not smuggled here): the boundary additionally refuses the act from a principal not
   role-bound for it — one rule, all acts, gates included.
6. **Optional strong provenance.** The commission establishing a gate of unusual weight MAY
   be SIGNED (trust layer §3, shipped): a deliberate human act, verified by
   `verify-commission`, surviving host compromise. Never automatic, never required — §B.1.

**Worked end-to-end: "never before v2" — a live specimen, not a hypothetical.** The
pre-umbrella `./verb` alias shims are ledger law to be "removed at the first post-2.0.0
minor" (umbrella spec §6; CLAUDE.md). Encoded:

```
autoharn led work open shim-removal "remove the ten ./verb alias shims (umbrella spec §6)"
autoharn led work open release-2.1.0 "milestone: first post-2.0.0 minor is tagged"
autoharn led work depends shim-removal --on release-2.1.0 --edge blocks-start
# probe registry entry (tools/discharge_probes/registry.py, reviewed like any code):
#   probe: git tag --list 'v2.*' => stdout matches ^v2\.[1-9] -- a post-2.0.0 minor exists
```

An agent attempting `work_claimed` on `shim-removal` today: the kernel refuses, naming the
unclosed antecedent and the right next act — mechanically, regardless of what the agent's
context believes about versions. Routine `probe-sweep` runs report the milestone probe as
HOLDS (no such tag) — the gate is visibly alive, not folklore. The day `v2.1.0` is tagged,
the sweep reports PROBE-WITNESSED with the observed tag list; the maintainer closes
`release-2.1.0` citing that output; `work_startable` now lists `shim-removal`; the next claim
succeeds. If he instead decides to pull the shims early, he supersedes the edge row — one
attributed, chained event, and the record shows who unlocked it, when, with what stated
reason. Every step above is existing or already-commissioned machinery except the habit of
opening milestone items — which is why this consult proposes an idiom and roughly zero build.

**Across the horizon, without trust modeling now.** The representation is
authority-neutral: it states *what* blocks, never *who* may unblock — that separation is what
makes the trust deferral safe. Single operator today: "who may" is owner discretion at the
grant layer, fully attributed. A multi-operator adopter tomorrow: the same edges and
milestones, unchanged; the s41 slots fill (role bindings gate the close/supersede acts once
entitlement enforcement is ratified; per-principal keys occupy the key-binding slot; the
trust layer §5's per-human signed heads take over sign-off), and the umbrella `authn_mode`
slot moves off `single-operator` — all named empty slots filling, no gate redesign. Nothing
in this shape needs to know how many principals exist or how much they trust each other.

## D. What this consult deliberately does NOT propose, and why

- **No predicate language, DSL, or rules engine for gates.** No consumer past the
  conjunction-of-closed-antecedents form is evidenced (B.4); a gate that genuinely needs
  richer logic should arrive as a named kernel delta with its own closure statement, when it
  has a name.
- **No priority scores, rankings, or urgency fields.** No nameable consumer (row 1906).
  Ordering among *startable* items is the orchestrator's explained-on-the-record judgment
  (self-application ruling), which a number would launder, not improve.
- **No per-gate or automated signing, no new crypto.** Refuted at B.1; the trust layer's §6
  boundary ("worth preserving against future enthusiasm" — the AC consult's words) is
  preserved.
- **No gate-special authority mechanism.** The entitlement follow-on is the general home
  (B.2); building its gate-shaped corner here would smuggle kernel authorization semantics in
  under a prioritization commission.
- **No DAC framework, table, or vocabulary.** The grant layer already is DAC; the felt gap is
  a missing one-page statement of per-mechanism guarantees, which is a documentation item the
  maintainer can commission for a fraction of any build (B.3).
- **No ASP gate evaluator, and no new trust tiers.** The engine stays the second producer and
  the why-explainer (B.4); trust modeling stays deferred behind the named slots, per the
  standing constraint, exactly as received.
- **No changes to the discharge-probes spec.** It composes as-is (C.3); coupling the two
  commissions any tighter would make the best-effort sibling load-bearing against its own
  ratified posture.

## License

Public Domain (The Unlicense).
