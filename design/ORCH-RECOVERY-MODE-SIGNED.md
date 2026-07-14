# Recovery mode under signed authority — destructive database recovery for real deployments

Audience: orchestrator and maintainer. This document answers one question: **when a real
(non-experiment) autoharn deployment's database is inconsistent or broken and needs destructive
repair — the kind of operation that can lose data if done wrong or done by the wrong actor —
what stops that repair from being either (a) impossible in practice, so the deployment is
simply thrown away, or (b) possible for anyone who can reach a shell, so "destructive repair"
becomes an unaudited backdoor?** It is a design note, not a built change: no code in
`kernel/`, `hooks/`, or any deployment is written by this document. It answers the tracker item
`recovery-mode-signed-authority` — a row in this project's ledger, an append-only Postgres-backed
record of maintainer rulings and work items, read via the `./led` command-line tool (`./led show
687` prints this item's own row) rather than a file in this repository — the maintainer's
concern 1 from the 2026-07-14 commission (ledger row 680, quoted in full below).

## The problem, in the maintainer's own words

Quoted verbatim from the 2026-07-14 commission (ledger row 680, the source of this whole task):

> migration path: ~/ent being a broken installation, and *still being broken* … there should be
> a recovery mode, "assurances" be damned (a malfunctioning harness will be thrown away in
> practice, then providing nothing at all — it's a common theme and danger with "ceremony
> becomes cargo-cult"); maybe provide a fail-hard when the initial commission (or, let's say, a
> root provisioning ledger entry — and by the way, maybe this is something we need to have
> regardless and as a high-assurance service) has a cryptographic signature, then requiring the
> "recovery operation" itself to be signed. This is distinct from the decision that "old worlds
> are void and dust", which was a *posture* regarding *autoharn experiments* (which are
> throwaway and obviously need no backfilling or migration, or anything like that).

Two things this quote establishes that the rest of this note takes as given, not as this
document's own opinion:

1. **The hazard is real, not hypothetical.** A harness that can never be repaired, only
   discarded, is a harness operators will discard the first time it breaks — which means every
   assurance mechanism this project builds provides nothing at all for a deployment that hit
   this wall, because the deployment stops existing rather than getting fixed. ~/ent is the
   witnessed case: a broken installation, and, as of this note, still broken.
2. **The distinction from "runs are strictly linear" is the maintainer's own, and it is a real
   distinction, not a hair split.** This project's standing ruling ([CLAUDE.md](../CLAUDE.md), "Runs are
   strictly linear," maintainer-ratified 2026-07-11) states: *"Run M > N means run N's world is
   dust and settled: read-only evidence, never patched, never refreshed, never delta'd —
   'live world' is not a concept here and never was."* That ruling governs **autoharn's own
   experiment worlds** (`run5`, `run7`, and siblings) — throwaway habitats where a bad run is
   simply superseded by the next one, and "recovering" run N would defeat the entire point of
   having runs be disposable evidence in the first place. A **real deployment** (~/ent, and any
   other adopter running autoharn in production against its own actual work) is not a disposable
   experiment; it has no "run N+1" to supersede it, and its brokenness is not evidence of
   anything except a defect that needs fixing. The maintainer names this distinction explicitly
   so it is not lost in translation the way "ratified" already was for other rulings ([CLAUDE.md](../CLAUDE.md)'s
   own parenthetical on that point) — this document preserves it rather than collapsing the two
   postures into one because both cite "linear" reasoning.

## Design shape: fail-hard unless doubly signed

The maintainer's own proposed shape, restated precisely: a destructive recovery/repair operation
against a real deployment's database is refused by default — **fail-hard**, meaning the absence
of authority is a refusal, never a silent no-op that looks like success and never a soft warning
an operator can click through — unless two conditions both hold:

1. **A root provisioning ledger entry carries a cryptographic signature.** At the moment a real
   deployment is provisioned (scaffolded), one ledger entry — the deployment's own root
   provisioning record — is signed by an authority key, establishing "this deployment was
   legitimately created by an actor holding this key" as a fact a later reader can verify
   independently of trusting the database's own internal state (which is exactly what may be
   inconsistent by the time recovery is needed — the signature must not depend on the thing it
   is meant to help recover). The maintainer's own aside — "maybe this is something we need to
   have regardless and as a high-assurance service" — is worth carrying forward as its own
   observation: a signed root provisioning record is arguably useful independent of recovery
   (it is a verifiable birth certificate for any real deployment), and this design does not
   narrow it to a recovery-only mechanism even though recovery is what motivates it here.
2. **The recovery operation itself is separately signed**, at the time it is invoked, by an
   authority key — not merely "an operator with database credentials ran a script," which is the
   access level that already exists and is exactly the access level the pgAudit-incident item
   elsewhere in this same commission (`scaffold-owner-credential-separation`, ledger row 680's
   §B4) is narrowing for ordinary operation. A recovery operation is a *stronger* claim than
   ordinary write access ("I am authorized to destructively rewrite this deployment's data to
   fix it"), so it earns a stronger authorization artifact than ordinary writes carry.

Both signatures verify against the same authority-key material (or, if the project later wants
separation of duties between "who may provision" and "who may authorize recovery," two distinct
keys — a choice this design leaves open, named explicitly rather than silently assumed, because
it is a policy question for the maintainer, not an engineering default). Absent a valid signature
on **either** artifact, the recovery tool refuses outright: no partial recovery, no "proceed
anyway" flag, no default permissive path. This is the same fail-hard posture this project already
applies elsewhere (`bootstrap/bootstrap.sh`'s own DB-reachability check: "a DB-reachability
failure prints the pg_hba/host facts loudly and exits non-zero — it never soft-passes") extended
to a higher-stakes operation.

### What "signed" means here, concretely

The envelope is deliberately minimal and standard, so the design is buildable rather than
aspirational:

- **Algorithm:** a detached digital signature over a canonical serialization of the signed
  content (e.g. Ed25519 over the SHA-256 of a canonical-JSON encoding of the provisioning
  record or the recovery-operation request) — ordinary, well-understood asymmetric signing, not
  a bespoke scheme. The specific algorithm choice is not load-bearing to this design; any modern
  detached-signature scheme with a verify step that does not require the signing key satisfies
  it.
- **What gets signed, root provisioning:** the deployment's identity (name, creation timestamp,
  the [birth-chain](../GLOSSARY.md#birth-chain) commit it was scaffolded from — the ordered
  kernel SQL a new world receives at scaffold time; see the companion note,
  [`ORCH-DEPLOYMENT-PINNING.md`](ORCH-DEPLOYMENT-PINNING.md), for what "which commit" means once
  pinning lands), written once at scaffold time, never amended (this is the same
  never-retro-edited posture this project already applies to point-in-time records —
  [ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 8's convention, cited by name because this record is exactly that shape: a
  frozen, dated fact).
- **What gets signed, the recovery operation:** the target deployment's identity, the specific
  recovery action being authorized (not a blanket "may perform recovery" grant — a signature
  over "repair inconsistency X in table Y" is a narrower, more auditable claim than "may run
  arbitrary recovery SQL"), a timestamp, and — where feasible — a nonce or the target's current
  state hash, so a captured signature cannot be replayed against a different, later inconsistency
  than the one it was issued for.
- **Verification, not signing, is what the recovery tool needs to run.** This is the load-bearing
  asymmetry that makes the design buildable today: verifying a signature requires only the
  **public** key, which can ship with the deployment or the recovery tool; producing a signature
  requires the **private** key, which never needs to touch the deployment's own machine at all.
  The recovery tool's own code path is entirely: read the signed artifact, verify it against the
  known public key, refuse if verification fails for any reason (missing signature, malformed
  envelope, wrong target, expired/replayed nonce, verification error) — never attempt to
  interpret a missing or invalid signature as "probably fine."

## Constitutional vs. buildable now — read this section before treating anything above as ready to build

This project's standing rule ([CLAUDE.md](../CLAUDE.md), "ORCHESTRATION"): *"Nobody edits kernel/lineage (frozen
records), law/, or engine/lp/ semantics without a Fable-authored, maintainer-ratified spec."*
This design touches both kinds of surface, and conflating them would misrepresent what a Sonnet
builder may pick up today versus what waits on the constitutional route. Split explicitly:

**Constitutional (Fable-authored, maintainer-ratified route required):**

- Any change to `kernel/lineage` — a new column on an existing table, a new ledger kind, a new
  view — to actually *store* a root provisioning signature or a recovery-operation signature
  inside the kernel's own schema. The root provisioning ledger entry's signature, if it is to
  live in the kernel (as opposed to a deployment-local file, discussed below), is exactly the
  kind of lineage delta this project's "class-ratified fail-safe deltas" carve-out ([CLAUDE.md](../CLAUDE.md))
  might or might not cover — it is additive (a new signature column/table, nothing existing
  relaxed), which is the shape that carve-out pre-ratifies, but "doubt about which side a delta
  falls on IS the routing: ask" (the same ruling's own words), and a mechanism whose entire
  purpose is authorizing *destructive* operations is exactly the kind of thing worth asking about
  rather than assuming pre-ratified. This design recommends routing it to the maintainer
  explicitly rather than claiming the carve-out on this document's own authority.
- Any semantics change to `engine/lp/` if recovery-authority verification is ever meant to be
  checkable by the deductive engine — this project's `clingo`-based Answer Set Programming (ASP)
  logic layer — (e.g. "no recovery operation without a matching signed provisioning record" as an
  ASP constraint, a rule the engine enforces) — not proposed as buildable-now work below, named
  here only so a future extension in that direction is flagged as constitutional in advance.
- The **policy** questions this design deliberately leaves open above (one authority key or two;
  who holds the private key; what recovery actions are pre-authorized as a class versus require
  a fresh per-incident signature) are maintainer decisions, not engineering defaults a builder
  should silently pick.

**Buildable now (Sonnet-executable, no constitutional route needed):**

- This design document itself.
- The **signature envelope format** as a plain specification (field names, canonicalization
  rule, algorithm identifier) — a data-shape decision, not a kernel or law change, exactly the
  kind of thing ADR-0012's "typed signature is the single source of truth" principle asks be
  nailed down before any code assumes it.
- A **verification library/module** (`verify_authority_signature(payload, signature, pubkey) ->
  bool`, or equivalent) that implements the envelope format above and does nothing else — no
  storage decision, no kernel touch, pure verification logic, testable in isolation with
  synthetic keys.
- A **recovery-mode verb's control flow** (a "verb" in this project's own vocabulary is a
  repo-root executable command, the same family `led`/`judge`/`pickup` belong to — see
  [`GLOSSARY.md#the-scaffold`](../GLOSSARY.md#the-scaffold)), designed and even scaffolded as inert code: read the
  signed artifacts (from wherever they are decided to live — see "degrades honestly keyless"
  below for why this is the one place the design stops short of a concrete location), call the
  verification module, refuse loudly on any failure, and — only past that gate — invoke the
  actual destructive repair logic (which is itself out of this design's scope; recovering a
  specific inconsistency is a different, later engineering problem from authorizing that a
  recovery may proceed at all).
- The migration/composition point named in the companion note: recording *which* pinned autoharn
  commit performed a given recovery, once [`ORCH-DEPLOYMENT-PINNING.md`](ORCH-DEPLOYMENT-PINNING.md)
  lands, so a recovery operation's own provenance is answerable the same way a deployment's
  template provenance is.

## Degrading honestly keyless — the standing crypto-deferral ruling

This project has a standing ruling — restated in this same commission's own `recovery-mode-
signed-authority` ledger row (`./led show 687`, cited in this document's opening): "signing
design may be drafted though key generation remains deferred per the standing ruling" — that key
generation and signing infrastructure are deferred until other, more load-bearing work is
banked, and that this deferral is never re-raised as a recommendation on its own. This design
respects that ruling by construction rather than by
exception: **everything in "Buildable now" above can be built today, and if it is built today,
it fails hard on every single invocation**, because there is no signing key yet to produce a
valid root-provisioning signature or a valid recovery-operation signature. That is not a flaw in
the design — it is the fail-hard posture the maintainer asked for, applied to the honest current
state of the project rather than to a hypothetical future state where keys already exist. A
recovery-mode verb built exactly to this spec, run against ~/ent or any other real deployment
today, refuses every attempt — correctly, because no attempt today carries the authority the
design requires it to carry.

This has one concrete consequence worth stating plainly rather than leaving implicit: **building
this design's "Buildable now" pieces does not, by itself, give the maintainer a working recovery
mechanism for ~/ent today.** It gives the project a verification mechanism that is *ready* to
authorize recovery the moment key generation is un-deferred, and a documented, reviewable shape
for what "signed authority" means here, so that when key generation does happen (on its own
timeline, per the standing ruling, not accelerated by this document), the recovery mechanism is
not designed from scratch under the pressure of an already-broken deployment. Until then, ~/ent's
actual repair — if the maintainer wants it repaired sooner than key generation lands — remains an
out-of-band, manually-authorized act outside this mechanism, the same as it is today; this design
does not claim to shorten that path, only to build the machinery that will eventually replace it
with something auditable.

## Composition with the deployment-pinning design

Ledger row 687 names this composition explicitly ("Composes with deployment-live-exec-coupling").
The connection: a recovery operation is itself a destructive act performed by *some* version of
autoharn's own recovery logic, against *some* deployment's data. Once
[`ORCH-DEPLOYMENT-PINNING.md`](ORCH-DEPLOYMENT-PINNING.md) lands, "which version of autoharn ran
the recovery" is an answerable, recorded question (the pin at the time of the operation) rather
than "whatever the shared checkout happened to be running that day" — which matters for the same
reason a root-cause analysis (RCA, the after-the-fact investigation of what went wrong) needs a
stable execution provenance for anything destructive: a recovery that goes wrong needs its own
logic's version identified, not just the deployment's.

## What this design deliberately does not claim

- It does not claim to have diagnosed ~/ent's current brokenness — that is separate, read-only
  observation work (the "spy" method this same commission asks be formalized elsewhere,
  tracker item `spy-method-formalization`), and this task's own dispatch instructions hold
  ~/ent strictly read-only for this work.
- It does not propose *what* recovery actions exist or how they repair a specific class of
  inconsistency — that is deployment- and defect-specific engineering, downstream of "is this
  operation authorized at all," which is this document's entire scope.
- It does not claim the fail-hard-keyless state described above is a temporary inconvenience to
  route around. Per the standing crypto-deferral ruling, it is not to be re-raised as a
  recommendation; this document states the consequence once, honestly, and moves on.

## Related

- [`design/ORCH-DEPLOYMENT-PINNING.md`](ORCH-DEPLOYMENT-PINNING.md) — the composing design note
  (`deployment-live-exec-coupling`), read together with this one per ledger row 687's explicit
  composition.
- [CLAUDE.md](../CLAUDE.md), "Runs are strictly linear" — the ruling this document distinguishes itself from,
  quoted above, in the maintainer's own words as well as the ruling's own text.
- [CLAUDE.md](../CLAUDE.md), "ORCHESTRATION," the kernel/law/engine constitutional-route rule and the
  class-ratified fail-safe deltas carve-out — both cited above to place each piece of this design
  on the correct side of the constitutional line.
- [ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 8 (never-retro-edited point-in-time records) — the convention this design borrows
  for the root provisioning ledger entry's own immutability.
- [ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md), "the typed signature is the single source of truth of a function's contract" — the
  principle behind specifying the signature envelope format before any code assumes its shape.
- `bootstrap/bootstrap.sh` — the existing fail-hard precedent this design extends ("a
  DB-reachability failure … never soft-passes").
- `kernel/lineage/s17-stamp-mechanism.sql` — this project's existing HMAC-based write-provenance
  tripwire, a related but distinct mechanism worth naming so the two are not conflated: s17's
  stamp is a **symmetric**, server-held secret used to bind an ordinary ledger row to the session
  that wrote it (a tripwire against quiet self-review, explicitly documented as "not
  authentication"); this design's signatures are **asymmetric** and meant to authorize a single
  high-stakes destructive act independent of any server-side secret, verifiable by anyone holding
  the public key. Same family of idea (unforgeable-without-a-secret provenance), different
  strength and different purpose — s17 is not a substitute for what this document proposes, and
  this document does not propose replacing s17.
- This project's ledger, `./led show 680` (the full 2026-07-14 commission), `./led show 687`
  (the `recovery-mode-signed-authority` work item), and `./led show 684`/`686` (the go-ahead and
  its design-scope framing).
