# Recovery mode under signed authority — design note (framing only, constitutional questions unresolved)

<!-- doc-attest-exempt: design note explicitly scoped to framing, not a ratified build-basis spec -- work item recovery-mode-signed-authority's own text: "Design note first ... may be drafted though key generation remains deferred per the standing ruling"; the constitutional pieces (any kernel/lineage touch, any engine/lp/ touch, the open policy choices) route to Fable+maintainer per CLAUDE.md ORCHESTRATION and are stated here as open questions, never answered on this document's own authority. Remove this marker only once a maintainer-ratified spec supersedes this note or a full A:B:C pass is deliberately run over it. -->

Audience: orchestrator and maintainer. This note exists to FRAME the problem and state the
open constitutional questions plainly, not to answer them — per the work item's own text
(`recovery-mode-signed-authority`, this project's decision ledger, `./led work list`):
*"Design note first... may be drafted though key generation remains deferred per the
standing ruling; Sonnet-draftable, constitutional pieces route to Fable+maintainer."* This
document is that Sonnet-draftable piece. Nothing below authorizes building kernel, law, or
`engine/lp/` changes; nothing below is a spec a builder should pick up as build basis.

## Prior art this note builds on, rather than restates

A design note answering a closely related ask (same maintainer commission, same
distinction from "runs are strictly linear") already exists in this repository's history:
[`vestigial_documentation/design/ORCH-RECOVERY-MODE-SIGNED.md`](../vestigial_documentation/design/ORCH-RECOVERY-MODE-SIGNED.md)
(banked at `autoharn v1.0`, commit `4ede79c`, later relocated — not edited — by the
doc-tree reorg). It already works through: the fail-hard-unless-doubly-signed shape (a
signed root provisioning record plus a separately signed recovery operation), a candidate
signature envelope (detached signature over canonical-JSON, algorithm left open), the
constitutional-vs-buildable-now split under CLAUDE.md's ORCHESTRATION rules, and the honest
consequence of the (then-standing) crypto deferral: everything buildable fails hard on
every invocation until keys exist. That analysis is not repeated here — read it first. This
note exists because two things have changed since it was written, both of which shift what
the still-open questions actually are, and because that file's own ledger citations
(`./led show 680/684/686/687`) point at a prior world's ledger and do not resolve against
this one — this note re-derives its own citations from the current ledger and current tree
instead of inheriting stale ones.

## What has changed since the prior note, and why it matters here

1. **The standing crypto deferral is no longer a blanket "no keys yet."** As of the
   Setup TUI's signed-genesis ceremony
   ([`design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md`](FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md),
   commission ledger row 1724, explicitly framed in its own text as lifting "the standing
   crypto deferral... in this scoped form"), a real deployment born through the guided
   setup TUI can now, by default, generate an ed25519 signing key, export the public half
   into the deployment's `keys/`, and sign its own founding commission row — verified live
   by `./verify-commission` before the ceremony is recorded WITNESSED. This is built ON the
   already-shipped GPG trust layer
   ([`design/MAINT-GPG-TRUST-LAYER.md`](MAINT-GPG-TRUST-LAYER.md)): signed ratification
   tags, SIGNED commissions, `verify-commission`/`verify-chain`, and the anchored-ledger
   signed chain head. **The prior note's "root provisioning ledger entry carries a
   cryptographic signature" condition is, in substance, no longer hypothetical machinery —
   a mechanism that produces exactly that artifact now exists and is exercised for real
   deployments born after this ceremony landed.** Whether recovery-mode should *reuse* this
   same key/verification path, rather than invent a second one, is the first open question
   below.
2. **A content-addressed, append-only artifact store now exists in the kernel** (s51,
   `kernel/lineage/s51-artifact-store.sql`, `led artifact put/get/stat`) — a place a signed
   recovery-operation artifact, or its detached signature, could plausibly be registered
   and later retrieved for audit, where none existed when the prior note was written. Not
   proposed as the answer here — named only because it is new surface area the eventual
   constitutional design will need to weigh against "a deployment-local file" and "a new
   kernel column," the three options the prior note left open without a fourth candidate.

## The problem, restated from the work item's own text

Quoted from the current ledger's `recovery-mode-signed-authority` work item (`./led work
list`), itself re-asserting a 2026-07-14 maintainer commission verbatim in substance:
`~/ent` is a broken installation and, per that commission, was *still* broken as of this
note being drafted — a live example of the hazard, not a hypothetical: **"a malfunctioning
harness gets thrown away in practice, providing nothing at all"** if there is no sanctioned
path to destructively repair it. The maintainer's own suggested shape: destructive
recovery/repair of an inconsistent database, permitted **under appropriate authority** —
fail-hard when (a) the initial commission, or a **root provisioning ledger entry**
(possibly a needed high-assurance mechanism regardless of recovery), carries a
cryptographic signature, and (b) the recovery operation itself is **separately signed**.
Explicitly **distinct** from "runs are strictly linear" — that ruling is a posture about
throwaway autoharn *experiments*; a real deployment like `~/ent` is not disposable, and its
brokenness is a defect to fix, not evidence to preserve as dust. The item also names one
composition point: `deployment-live-exec-coupling` (design/ORCH-DEPLOYMENT-PINNING.md) —
"which version of autoharn performed a recovery" becomes an answerable, pinned fact once
that design lands, which matters for the same reason any destructive act needs a stable
execution provenance.

## Constraints carried forward from the item's own text (binding on any future spec, not this note's to relax)

- **Fail-hard, never a soft no-op.** Absence of valid authority is a refusal, never a
  silent success-looking no-op and never a "proceed anyway" escape hatch.
- **Two-signature shape, not one.** A signed root provisioning record establishes "this
  deployment was legitimately created under this authority"; the recovery operation itself
  needs its own, separate signature — a stronger claim than ordinary write access, earning
  a stronger authorization artifact.
- **Distinct from the runs-are-linear posture.** This mechanism governs real deployments,
  not throwaway experiment worlds; a future spec must not collapse the two postures
  because both cite "linear" reasoning, per the maintainer's own explicit warning against
  exactly that conflation.
- **The crypto-deferral discipline still applies to whatever remains undecided.** Per this
  project's standing ruling, a deferred piece is stated once, honestly, and not re-raised
  as a standing recommendation on its own — this note names open questions below without
  nagging for their resolution.
- **Composes with, does not duplicate, `deployment-live-exec-coupling`.** Recovery
  provenance ("which autoharn version ran this repair") is the pinning design's concern;
  this note does not restate that design, only cites the composition point.

## Open constitutional questions — framed here, answered by nobody on this document's authority

These are the questions this note explicitly does NOT resolve. Per CLAUDE.md's
ORCHESTRATION rules, any kernel/lineage delta, any `engine/lp/` semantics touch, and any of
the policy choices below route to Fable + the maintainer — not to a Sonnet builder picking
a default.

1. **Does recovery-mode authority reuse the signed-genesis / GPG-trust-layer key material
   (the same key that signs a founding commission and that `verify-commission` already
   verifies), or does it need a distinct authority key with separated duties ("who may
   provision" vs. "who may authorize recovery")?** The prior note left this open in the
   abstract; it is no longer abstract, because a concrete signing mechanism a recovery
   design could plausibly reuse now actually exists and is in service for real
   deployments born after the signed-genesis ceremony.
2. **Where does a signed recovery-operation artifact (or its signature) live?** A
   deployment-local file, a new kernel table/column (which the "class-ratified fail-safe
   deltas" carve-out might or might not cover — additive, but "doubt about which side a
   delta falls on IS the routing: ask"), or the newly-shipped s51 artifact store
   (`kernel.artifact`) registering the signed request as a content-addressed blob? Each has
   a different audit-retrieval and tamper-evidence shape; none is this note's to pick.
3. **Is a recovery signature scoped per-incident ("repair inconsistency X in table Y") or
   pre-authorized as a class for a given deployment?** The prior note recommended the
   narrower, per-incident shape as more auditable; whether that recommendation should
   become the ratified default, or the maintainer wants a broader pre-authorization for
   named recovery classes, is unresolved.
4. **What is the actual repair logic for a given class of inconsistency?** Explicitly out
   of scope for any design at this framing level — "is this operation authorized at all"
   is a different, prior question from "what does fixing `~/ent`'s specific brokenness
   look like," and this note does not conflate them.
5. **Does an eventual ASP-checkable constraint belong in `engine/lp/`** (e.g. "no recovery
   operation without a matching signed provisioning record" as a rule the deductive engine
   itself enforces), or does verification stay entirely outside the kernel/engine layer, in
   an ordinary Python verification module? Named as a possible future extension, not
   proposed as buildable-now work — an `engine/lp/` touch is squarely constitutional route
   territory regardless of how this note's other questions resolve.

## What this note deliberately does not do

- It does not propose a signature envelope format, a verification module signature, or a
  recovery-verb control-flow sketch — the prior vestigial note already did that
  exploratory work; a maintainer-ratified spec, when commissioned, should read both notes
  and decide what to keep, revise, or discard, not treat either as pre-approved.
- It does not diagnose or touch `~/ent`'s actual brokenness. `~/ent` carries a live
  session this project treats as strictly read-only; this note is aware of it only as the
  motivating evidence the maintainer himself cited.
- It does not re-raise the crypto-deferral as something to accelerate. The scoped lift
  (signed-genesis) is named above as changed context, not as license to declare the
  broader deferral over.

## Related

- [`vestigial_documentation/design/ORCH-RECOVERY-MODE-SIGNED.md`](../vestigial_documentation/design/ORCH-RECOVERY-MODE-SIGNED.md)
  — the fuller prior-art design note this one builds on and deliberately does not repeat.
- [`design/ORCH-DEPLOYMENT-PINNING.md`](ORCH-DEPLOYMENT-PINNING.md) — the composing design
  (`deployment-live-exec-coupling`), named by the work item as a required composition
  point.
- [`design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md`](FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md)
  and [`design/MAINT-GPG-TRUST-LAYER.md`](MAINT-GPG-TRUST-LAYER.md) — the signing
  infrastructure that now exists and reframes open question 1 above.
- `CLAUDE.md`, "ORCHESTRATION" — the kernel/law/engine constitutional-route rule and the
  class-ratified fail-safe deltas carve-out, both cited above.
- This project's ledger: `./led work list` for the current `recovery-mode-signed-authority`
  item's own text, quoted from throughout this note.
