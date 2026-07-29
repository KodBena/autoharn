# FABLE-TRUST-PROTOCOL-V2-SPEC — multi-party trust, stated slowly

<!-- doc-attest-exempt: Fable-authored spec 2026-07-29, status=proposed, commissioned for
the maintainer's SLOW READ (his words, row 639: "you'll produce what I was supposed to read
slowly too"). Nothing here is buildable until he ratifies it AND performs the activation
ceremony in §6 personally; v1's single-trust-domain bound (durable row 31) STANDS in full
until that moment. Removal condition: the ratification row. -->
<!-- design-currency: status=proposed depends-on=FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md -->

This document exists to be read slowly because it changes what one word means everywhere:
today, every refusal, every countersign, every SoD verdict in this system answers the
question *"did the right process shape occur?"* — after v2, some of them answer *"can a
party PROVE that, against the will of everyone else including the operator's own
machinery?"* Those are different questions with different costs, and the whole spec is the
line between them, drawn deliberately.

## 0. What trust is here, and what we actually have (the honest baseline)

The maintainer's working assumption (row 639, corrected there): that multi-party trust
already existed, minus an optional key-signing ritual. The true state: **every identity
channel in the system is forgeable by the same OS user** — the stamp secret is a
chmod-600 file the agent's own user can read (s17's LIMITS says so in its own header),
minted-principal headers are asserted strings, `LED_ACTOR` is a name you type. Within one
trust domain this is not a defect; it is the ratified design ("tripwire, not
authentication"), and it is why the kernel's SoD machinery polices *process shape*
(distinct invocations, distinct actors) rather than *adversarial identity*. The signing
"rigamarole" was never a ceremony on top of trust — it is the only thing that would make a
second party's claim verifiable rather than honored. What exists as real cryptography
today: the signed-genesis ceremony and the `verify-commission`/`attest-tags` rungs (GPG
against committed public keys) — one root, the maintainer's, used for provenance of
commissions and tags, not for per-principal runtime identity. The named-empty slots:
s41's `principal_key_bound`/possession-attestation kinds (recorded, gating nothing),
s58's missive signing slot, the wire protocol's `authn_mode` field (value: forever
`single-operator` so far). v2 is the act of filling those slots — and nothing else; the
slots were shaped for exactly this so the retrofit surface is small by construction.

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
  possession-attestation (the s61 canonical-statement ceremony, which already exists for
  exactly this and has simply never gated anything). Delegation between parties is the
  existing `acts-for` relation — but under v2, an acts-for edge involving a keyed
  principal must itself be SIGNED by the delegator, or it does not enter the authority
  chain walk. Trust composes only through proofs.
- **Worlds are parties to each other.** A counterpart world's courier identity gets a
  key like any party; missives from a keyed world carry the s58 signing slot filled.
  Cross-world citations (`xrow:` with content hash) already verify integrity; v2 adds
  origin.

## 2. What must be signed (the gating rule, stated once)

Under `authn_mode = multi-party`, an act is **signature-gated iff it claims authority or
attests independence across a trust boundary**: the eight (soon nine) authority-bearing
act classes when the actor is a keyed principal; reviews whose independence claim is load
bearing for another party's decision; missives from keyed worlds; and the enrollment acts
themselves. Everything else — ordinary rows, notes, work bookkeeping *within* one party's
own scope — stays stamp-grade, deliberately: signing everything would move the cost from
"where trust crosses a boundary" to "everywhere," which is how signing regimes die of
friction and start getting bypassed. The kernel enforces this as one new conjunct in the
s60 idiom (per-world armed, unarmed byte-identical — the same fail-safe shape as every
delta since s21): *for a gated act by a keyed principal, a valid detached signature over
the row's canonical bytes must verify against that principal's in-force bound key.*
Verification is kernel-side (pgcrypto or an equivalent verified path — the birth
dependency the fixture sweeps already witness), so a signature is checked where the row
lands, not where a client promises it was checked.

## 3. The wire protocol version

`protocol_version` goes to `2`; `authn_mode` gains `multi-party`. A v2 boundary session
for a keyed principal authenticates by signature over a server nonce (challenge-response
at session start; no long-lived bearer tokens, nothing replayable), and the session's
reads then resolve identity for the flow-control machinery (the AC spec's scopes — this
is where the two specs meet: scopes decide *what a party may see*, keys decide *whether
the party is who the session claims*). Anonymous reads remain legal exactly as the AC
spec rules, at open scope or whatever scope the world's posture assigns anonymity.
**Loopback stays the default binding.** The moment a deployment binds beyond loopback,
TLS becomes mandatory in the same config stroke (refused otherwise, teach-text naming
why) — but network exposure is its own operator decision this spec does not make; medical
tier on one host with keyed local parties is fully served on loopback.

## 4. The medical tier, composed (why this is enough, and what it is not)

The medical scenario from rows 567/608 and the maintainer's tier question: information
control at full-redaction grade for agents acting on behalf of arena principals.
Composition: **scopes at `full` disclosure** (AC spec §1c — existence-hidden, counts
scope-relative, instrument-only verification) carried by **keyed principals** (this
spec), with the **hash-stub tier** serving the auditor who must verify integrity without
seeing content. What this composition honestly is: HIPAA-*shaped* technical controls —
attributable, integrity-protected, access-scoped, journaled. What it is not, stated so
it is never oversold: a compliance claim (the project bar remains NRC-grade product,
best-effort process), an operator-proof system (§1), or a substitute for the
organizational controls every real medical deployment layers on top. The system's
contribution is that its records can *survive hostile audit* — every access attributable
to a key, every redaction typed, every chain verifiable at the tier the viewer is
entitled to.

## 5. Threat model (what v2 defends, and the honest not-covered list)

Defended, newly: cross-party forgery (party A cannot mint party B's acts — the core);
repudiation of signed acts (a party cannot disown its signature while its key was
in-force and possession-attested); operator-side *accidental* substitution (a mislabeled
agent cannot satisfy a signature gate); after-the-fact manufacture of signed history
(signatures bind to chain-hashed rows; back-dating requires breaking the chain the
instruments verify). NOT defended, named per ADR-0000's discipline: the root operator
acting deliberately (owns the host); key theft from a party's own custody (their
perimeter, not ours — revocation via the existing s45 lifecycle is the remedy, and s45's
prospective-only severance semantics apply to keys exactly as to standing); side channels
below the boundary (same tripwire posture as the AC spec §2, unchanged); coercion,
collusion, and every social channel; and quantum-era signature breakage (algorithm
agility is a config field on the binding act, not a promise).

## 6. The activation ceremony (all of it is the maintainer's, by design)

Nothing in this spec activates by merge. The sequence, each step his: (1) ratify this
spec, slowly — the reading IS the step; (2) the key ceremony he has reserved to himself
(row 264's grounding requirement is honored, not bypassed: this spec re-raises nothing —
it was commissioned); operator root key, then per-party enrollment as parties actually
appear; (3) flip a world's `authn_mode` to `multi-party` — per-deployment, the same
posture idiom the identity_enforcement split just built, grace-then-enforce staging
available for the same reasons; (4) the first keyed world birth carries the v2 conjunct
delta in its chain. Until (3), every world behaves byte-identically to today regardless
of how much of v2 has merged — the same unarmed-is-identical discipline every kernel
delta since s21 has carried.

## 7. Closure statement (ADR-0000 Rule 2(a))

**Invariant:** in a multi-party-armed world, no act that claims authority or
boundary-crossing independence enters the ledger attributed to a keyed principal without
a kernel-verified signature against that principal's in-force, possession-attested key;
and no unarmed world's behavior differs by one byte from v1.

**Quantification universe:** the gated act classes (the authority-bearing set as then
constituted, enumerated by `entitlement_act_class_of` at the delta's writing — nine with
s70 — plus reviews, missives-from-keyed-worlds, and the enrollment acts); the identity
channels (stamp, minted, anonymous, and new: signed-session); both arming states; the
key lifecycle states s45 admits (in-force, suspended, revoked — severance prospective);
both transports (loopback; network-with-TLS).

**Named as not covered:** everything in §5's not-defended list; the SPA/panel (a
browser cannot hold party keys safely — panel sessions ride operator identity or scoped
anonymity until a dedicated design earns otherwise, stated so nobody wires a private key
into a web bundle); automated key rotation (manual via bind/revoke acts until a need is
witnessed); and cross-project federation beyond pairwise world keys (no web of trust, no
CA — pairwise enrollment only, the smallest shape that serves the want).

**Denomination check:** trust is denominated in *verifiable acts* (signatures over
canonical row bytes against ledgered keys) — never in network position, process
ancestry, or environment variables, which are the proxies v1 honestly used and v2
honestly retires at each gate it arms.

## License

Public Domain (The Unlicense).
