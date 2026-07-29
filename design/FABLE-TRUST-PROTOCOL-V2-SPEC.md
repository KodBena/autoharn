# FABLE-TRUST-PROTOCOL-V2-SPEC — multi-party trust, stated slowly

<!-- doc-attest-exempt: Fable-authored spec 2026-07-29, status=proposed, commissioned for
the maintainer's SLOW READ (his words, row 639: "you'll produce what I was supposed to read
slowly too"). Nothing here is buildable until he ratifies it AND performs the activation
ceremony in §6 personally; v1's single-trust-domain bound (durable row 31) STANDS in full
until that moment. Removal condition: the ratification row. -->
<!-- doc-attest-exempt addendum, 2026-07-29: a full +A:B:C loop has since run over this
file -- A-side pre-review (commit dbecee41), a blind B round (9 findings), and this C
repair (all nine applied; record appended to attestations/doc-legibility-attestations.jsonl,
schema doc-attestation/2, self-adjudicated per the dispatched-loop precedent already in that
ledger). This addendum records the loop; it does NOT strike the marker above, because the
marker's own removal condition names ratification, not loop completion, and this spec is
still status=proposed. Flagged for the coordinator: whether a completed loop should ever
supersede this marker while status stays proposed is an open question this repair round
did not resolve on its own authority. -->
<!-- design-currency: status=proposed depends-on=FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md -->

This document exists to be read slowly because it changes what one word — **trust** — means
everywhere: today, every refusal (a hard stop where the kernel or a gate declines to accept a
write or act rather than silently allowing it), every countersign (a second, distinct-actor
review that discharges a row's outstanding review debt — [`review_gap`](../GLOSSARY.md#review_gap)),
and every SoD (separation-of-duties) verdict in this system answers the question *"did the
right process shape occur?"* — after v2, some of them answer *"can a party PROVE that,
against the will of everyone else including the operator's own machinery?"* Those are
different questions with different costs, and the whole spec is the line between them, drawn
deliberately.

## 0. What trust is here, and what we actually have (the honest baseline)

The maintainer's working assumption (row 639 — a convention this document uses throughout:
"row N" cites this project's append-only decision ledger, readable via `./autoharn led show
N`, corrected there) was that multi-party trust already existed, minus an optional
key-signing ritual. The true state is that **every
identity channel in the system is forgeable by the same OS user**: the
[stamp](../GLOSSARY.md#stamp) — the HMAC that binds a ledger row to the session that
wrote it — has its secret held in a chmod-600 file the agent's own user can read, a
limitation [`kernel/lineage/s17-stamp-mechanism.sql`](../kernel/lineage/s17-stamp-mechanism.sql)
names in its own header comment (this document cites several kernel-lineage schema
migrations this way, each numbered `sNN`); minted-principal headers are asserted strings,
and `LED_ACTOR` is a name you type. Within one trust domain this is not a defect; it is
the ratified design ("tripwire, not authentication"), and it is why the kernel's SoD
machinery polices *process shape* (distinct invocations, distinct actors) rather than
*adversarial identity*. The signing "rigamarole" was never a ceremony
on top of trust — it is the only thing that would make a second party's claim verifiable
rather than honored. What exists as real cryptography today is the signed-genesis
ceremony and the `verify-commission`/`attest-tags` rungs (GPG against committed public
keys) — one root, the maintainer's, used for provenance of commissions and tags, not for
per-principal runtime identity. Three places already have named slots that presently do
nothing — "named-empty" meaning the field or act-kind exists and is recorded, but nothing
in the kernel gates on it yet. First, migration s41 defines two such kinds, a
`principal_key_bound` act and a possession-attestation act (detailed in §1 below); both
are recorded when they occur, but neither currently gates anything. Second, migration s58
defines a missive signing slot, for signing cross-world messages, that the wire format
carries but nothing yet populates or checks. Third, the wire protocol's `authn_mode`
field has so far only ever held the value `single-operator`. v2 is the act of filling
these three slots — and nothing else; they were shaped in advance for exactly this, so
the retrofit surface this spec describes is small by construction.

## 1. The trust topology (who can prove what to whom)

- **The operator remains the root.** v2 does not make the system operator-proof and no
  honest design at this substrate can: the operator owns the host, the database, the
  keys' storage, the birth ceremony. What v2 adds is that *parties below the root* become
  cryptographically distinct from each other and from the operator's own machinery — a
  party's signature is something the operator's agents cannot mint, so a signed act is
  evidence *against* operator-side confusion, substitution, or (the medical case) an
  auditor's suspicion that records were manufactured after the fact.
- **A party is a principal with a bound key.** The existing s41 registry grows no new
  concept: a party enrolls by the operator registering the principal and the party's
  public key landing as a `principal_key_bound` act, countersigned by a
  possession-attestation (the s61 canonical-statement ceremony: `led principal
  attest-possession` has the principal GPG-sign a fixed statement text naming their own
  fingerprint, verified against the deployment's committed public key — proof of possessing
  the private key, not merely asserting the fingerprint; this ceremony already exists for
  exactly this and has simply never gated anything). Delegation between parties is the
  existing `acts-for` relation — but under v2, an acts-for edge involving a keyed
  principal must itself be SIGNED by the delegator, or it does not enter the authority
  chain walk (the kernel's existing check, s60: an actor's `acts-for` chain must reach
  back to the world's genesis principal, walked fresh at every act rather than cached).
  Trust composes only through proofs.
- **Worlds are parties to each other.** A counterpart world's courier identity gets a
  key like any party; missives from a keyed world carry the s58 signing slot filled.
  Cross-world citations (`xrow:` with content hash) already verify integrity; v2 adds
  origin.

## 2. What must be signed (the gating rule, stated once)

Under `authn_mode = multi-party`, an act is **signature-gated iff it claims authority or
attests independence across a trust boundary**: the eight authority-bearing act classes
that `entitlement_act_class_of` (s60/s62/s64's kernel-computed vocabulary) currently emits —
`principal_registered`, `principal_role_bound`, `standing_lifecycle`, `milestone_closure`,
`gate_edge_supersession`, `entitlement_class_configured`, `delegation_lifecycle`, and
`independent_verification_delegation` — when the actor is a keyed principal; reviews whose
independence claim is load bearing for another party's decision; missives from keyed
worlds; and the enrollment acts themselves. The AC spec's own s70 delta adds a ninth,
`principal_scope_bound`, to that same vocabulary — named here so the count needs no forward
dependency on §7's closure statement. Everything else — ordinary rows, notes, work bookkeeping *within* one party's
own scope — stays **stamp-grade** (protected only by the existing
[stamp](../GLOSSARY.md#stamp), not a signature), deliberately: signing everything would
move the cost from "where trust crosses a boundary" to "everywhere," which is how signing
regimes die of friction and start getting bypassed. The kernel enforces this as one new
**conjunct** — one clause ANDed into an existing all-must-pass check, the same sense
[GLOSSARY.md's entitlement entry](../GLOSSARY.md#entitlement) uses for s60's two existing
conjuncts — added to the s60 idiom. That idiom is **armed** or **unarmed** per world: a
world's configuration turns the check on or leaves it off, and an unarmed world behaves
byte-identically to today — the same fail-safe shape every kernel-lineage delta since s21
has carried. The new conjunct itself: *for a gated act by a keyed principal, a valid
**detached signature** (a signature stored and verified separately from the data it
covers) over the row's **canonical bytes** (the row's one fixed, deterministic byte
serialization — the same bytes every verifier reproduces) must verify against that
principal's **in-force** (currently valid — not suspended or revoked) bound key.*
Verification is kernel-side (pgcrypto or an equivalent verified path — the birth
dependency the fixture sweeps already witness), so a signature is checked where the row
lands, not where a client promises it was checked.

## 3. The wire protocol version

`protocol_version` goes to `2`; `authn_mode` gains `multi-party`. A v2 boundary session
for a keyed principal authenticates by signature over a server nonce (challenge-response
at session start; no long-lived bearer tokens, nothing replayable).
[FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md](FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md)
(called "the AC spec" below) is the flow-control machinery that decides what a party may
see, through its scopes; this session's reads resolve the identity those scopes are
evaluated against. This is where the two specs meet: scopes decide *what a party may see*,
keys decide *whether the party is who the session claims*.
Anonymous reads remain legal exactly as the AC spec rules, at open scope or whatever
scope the world's posture assigns anonymity.
**Loopback stays the default binding.** The moment a deployment binds beyond loopback,
TLS becomes mandatory in the same config stroke (refused otherwise, teach-text naming
why) — but network exposure is its own operator decision this spec does not make; medical
tier on one host with keyed local parties is fully served on loopback.

## 4. The medical tier, composed (why this is enough, and what it is not)

The medical scenario from rows 567/608 and the maintainer's tier question concern this:
information control at full-redaction grade for agents acting on behalf of arena
principals (the AC spec §1c's term for the principals participating in a scope's
domain — here, the medical scenario). The composition has three parts. First, **scopes at `full` disclosure** — the AC spec §1c
tier where a row's existence is hidden, counts stay scope-relative, and verification is
possible only through the instrument, never a raw read. Second, those scopes are carried by
**keyed principals**, this spec's own contribution. Third, the **hash-stub tier** — the AC
spec §1c's middle disclosure tier, where a row's existence and hash are visible but its
content is withheld — serves the auditor who must verify integrity without seeing content. What this
composition honestly is: HIPAA-*shaped* technical controls —
attributable, integrity-protected, access-scoped, journaled. What it is not, stated so
it is never oversold: a compliance claim (the project bar remains NRC-grade product,
best-effort process), an operator-proof system (§1), or a substitute for the
organizational controls every real medical deployment layers on top. The system's
contribution is that its records can *survive hostile audit* — every access attributable
to a key, every redaction typed, every chain verifiable at the tier the viewer is
entitled to.

The PRIMARY medical control deserves naming on its own (maintainer, 2026-07-29, from
Swedish practice: a physician may not open the record of a patient who is not theirs —
the problem is not only after-the-fact manufacture but unauthorized reading by
legitimately-credentialed insiders): that control is the AC spec's half of this
composition, not this spec's. The scope IS the care relation — a keyed clinician
principal's scope covers their own patients' rows and excludes everyone else's — and
the journaled read channel is the audit substrate such regimes actually run on: every
look-up attributable, every scoped-out access a typed refusal on the record, sampled
audit possible over the journal. What this spec's keys add on top is that the journal's
attributions and the records' provenance survive dispute. Insider read control without
keys is already real (tier 1, one operator's own agents); keys make it real against
parties.

## 4a. Backwards compatibility (maintainer question 2026-07-29, answered in the design)

Compatibility is designed-in at five seams, of different kinds. (1) **Unarmed is
byte-identical:** a world birthed with the v2-capable kernel but `authn_mode =
single-operator` behaves exactly like v1, the same per-world arming discipline every
kernel delta since s21 carries. (2) **Per-deployment coexistence:** one hub serves
armed and unarmed worlds simultaneously — the per-deployment posture machinery
(`serving/boundary_multiplex_config.py`'s override idiom) is the template `authn_mode`
reuses. (3) **Per-principal gradualism:** inside an armed world, an UNKEYED principal's
acts stay stamp-grade — obligations attach as principals enroll, never to the world
wholesale, so legacy agents run unmodified. (4) **Recorded-not-gated degradation:** a
v2-aware client writing into an unarmed or v1-era world lands its signatures in the
slots that have existed since v1 — the proof is stored even where the kernel does not
check it, which makes v1-era signed rows RETROACTIVELY verifiable by any later or
external verifier; cross-world correspondence between keyed and unkeyed worlds degrades
pairwise to the weaker party's tier with the grade visible per row, never silently
flattened. (5) **Runs-are-linear is itself the deepest seam:** nothing upgrades, worlds
are born at their protocol level, so no migration surface exists to break. The one
honest asymmetry: DISARMING an armed world weakens guarantees for rows written after
the disarm — the arming state is ledgered, so every row carries its era and an auditor
can always tell which guarantee it was written under. Backwards compatible, yes; a
silent downgrade, deliberately never.

## 5. Threat model (what v2 defends, and the honest not-covered list)

This version newly defends against: cross-party forgery (party A cannot mint party B's
acts — the core); repudiation of signed acts (a party cannot disown its signature while
its key was in-force and possession-attested); operator-side *accidental* substitution (a
mislabeled agent cannot satisfy a signature gate); and after-the-fact manufacture of
signed history (signatures bind to chain-hashed rows — every ledger row carries a hash
binding it to its predecessor, and the `verify-chain` instrument walks that chain end to
end; back-dating requires breaking the chain the instrument verifies). Not defended — named per ADR-0000's discipline, which
requires stating a guarantee's honest limits rather than leaving them unsaid — are: the
root operator acting deliberately (owns the host); key theft from a party's own custody
(their perimeter, not ours — revocation via the existing migration-s45 standing-lifecycle
machinery is the remedy, and that same machinery's prospective-only severance semantics
apply to keys exactly as they already apply to a principal's standing); side channels
below the boundary (same tripwire posture as the AC spec §2, unchanged); coercion,
collusion, and every social channel; and quantum-era signature breakage (algorithm
agility is a config field on the binding act, not a promise).

## 6. The activation ceremony (all of it is the maintainer's, by design)

Nothing in this spec activates by merge. The sequence, each step his: (1) ratify this
spec, slowly — the reading IS the step; (2) the key ceremony he has reserved to himself
(row 264's grounding requirement — his standing rule that he personally grounds any
cryptographic key generation before it proceeds, rather than putting his name on
crypto-related assurance without that grounding — is honored, not bypassed: this spec
re-raises nothing — it was commissioned) — he establishes the operator root key first, then enrolls each
party's key as parties actually appear; (3) flip a world's `authn_mode` to
`multi-party` — per-deployment, the same posture idiom the `identity_enforcement`
grace/enforce split just built (`serving/boundary_multiplex_config.py`), with
grace-then-enforce staging available for the same reasons; (4) the first keyed world
birth carries the v2 conjunct delta in its chain. Until (3), every world behaves
byte-identically to today regardless of how much of v2 has merged — the same
unarmed-is-identical discipline every kernel delta since s21 has carried.

## 7. Closure statement (ADR-0000 Rule 2(a))

**Invariant:** in a multi-party-armed world, no act that claims authority or
boundary-crossing independence enters the ledger attributed to a keyed principal without
a kernel-verified signature against that principal's in-force, possession-attested key;
and no unarmed world's behavior differs by one byte from v1.

**Quantification universe:** the gated act classes (the authority-bearing set as then
constituted, enumerated by `entitlement_act_class_of` at the delta's writing — nine once
the AC spec's own s70 delta lands, adding `principal_scope_bound` — plus reviews,
missives-from-keyed-worlds, and the enrollment acts); the identity channels (stamp,
minted, anonymous, and new: signed-session); both arming states; the key lifecycle
states migration s45 admits (in-force, suspended, revoked — severance prospective); both
transports (loopback; network-with-TLS).

**Named as not covered:** everything in §5's not-defended list; the SPA (single-page
application) / panel (a browser cannot hold party keys safely — panel sessions ride
operator identity or scoped anonymity until a dedicated design earns otherwise, stated so
nobody wires a private key into a web bundle); automated key rotation (manual via
bind/revoke acts until a need is witnessed); and cross-project federation beyond pairwise
world keys (no web of trust, no certificate authority (CA) — pairwise enrollment only,
the smallest shape that serves the want).

**Denomination check:** trust is denominated in *verifiable acts* (signatures over
canonical row bytes against ledgered keys) — never in network position, process
ancestry, or environment variables, which are the proxies v1 honestly used and v2
honestly retires at each gate it arms.

## License

Public Domain (The Unlicense).
