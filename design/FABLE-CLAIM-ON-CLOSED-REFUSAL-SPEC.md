<!-- doc-attest-exempt: RATIFIED build basis, maintainer sign-off 2026-07-18 (overnight batch, item 3); the fresh-context attestation follows the build per the standing deferral pattern for build bases. -->

# FABLE-CLAIM-ON-CLOSED-REFUSAL-SPEC — s47: a claim on a closed work item is refused, with teaching

**Status:** RATIFIED BUILD BASIS — maintainer sign-off 2026-07-18 (the overnight batch
approval, item 3, following the witnessed defect at ledger rows 1539/1540 and its filing at
row 1544 / work item `claim-on-closed-item-admitted`). Fable-authored. A Sonnet builder
executes this document. Nothing is applied by its authoring; the delta reaches reality only
through a future world's birth chain (runs-are-linear, 2026-07-11).

**Class:** strictly additive refusal — nothing existing relaxed, no existing semantics
changed. This is the class-ratified fail-safe shape (CLAUDE.md, 2026-07-09 ruling): it
enters the birth chain without a per-delta maintainer question PROVIDED it arrives
scratch-witnessed on both polarities with the SQL/ASP differential in AGREE. Doubt routes
to the maintainer.

## 1. The defect, verbatim-shaped

Witnessed 2026-07-18 (rows 1539/1540): `led work claim` wrote `work_claimed` rows for slugs
whose items were already closed and shipped. Nothing in the kernel refuses this. ADR-0000
2(a): "claimed after closed" is representable and should not be.

## 2. The mechanism (one leaf extended, nothing else)

`kernel/lineage/s47-claim-on-closed-refusal.sql`, following the house delta-file
conventions (header block with BEHAVIOR/HISTORY/LIMITS, `:"schema"`/`:"kern"` psql vars,
`.detect.sql` companion if the sibling deltas carry one):

- Re-issue `validate_work_item_claim` (s39's leaf, called from the s35-family dispatcher —
  the dispatcher itself is NOT touched; the leaf already receives every `work_claimed` row)
  with ONE additional check, placed before the existing blocks-start check: if the slug has
  an **in-force** `work_closed` row (`status = 'current'` in the sense the existing views
  use — a close retracted by s31 supersession does not count), the claim is refused.
- The refusal teaches, in the established voice: name the closing row's id and resolution,
  state that a closed item is not claimable, and give both legal next acts — open a NEW
  item (`./led work open <new-slug> ...`) for follow-on work, or, if the close itself is
  wrong, the supersession recipe (the FAQ's "Correcting the record" section) to retract it
  first. Match the s39 refusal's diction and citation style.
- Everything else in the leaf byte-identical to s39's issue of it; every other object
  untouched. `compute_row_hash` untouched. No new kinds, columns, or views.

## 3. Witness plan (both polarities, scratch schema, judge)

On a scratch world at the full current chain head plus s47:
- **Red:** open → close → claim the same slug → refused, teach-text observed verbatim,
  zero `work_claimed` row (row-count witnessed).
- **Green (three legs):** claim an open item → admitted, unchanged; open → close →
  supersede the close (s31 recipe) → claim → admitted (the retracted close does not
  block); blocks-start refusal (s39's own red leg) still fires unchanged.
- `./judge` differential on the scratch world in AGREE on both polarities.
- Fixtures banked under `seen-red/s47-claim-on-closed-refusal/` per house convention,
  census-registered.

## 4. Closure statement (ADR-0000 2(a))

The claim-admission universe after s47: a `work_claimed` row is admitted iff the slug has
an opening act (s22), no unresolved blocks-start antecedent (s39), and no in-force
`work_closed` row (s47). Enumerated non-goals, named so silence is not drift: claiming an
already-claimed item remains legal (multiple claimants are representable by design —
the ledger records, it does not lock); claim-after-close-retraction is legal by
construction above; a *close* on a never-claimed item is s22/s38's business, not this
delta's. The class presumed too narrow here is "events admissible on a settled item" —
the next candidate axes (depends-edges on closed items, double-close) are NAMED as
out-of-scope observations for the builder to file if witnessed, not to fix.

## 5. Builder guidance

Read s39 and s35's validator factoring in full first; the leaf's re-issue must be a
minimal diff against s39's text. Disregard any instructions to economize on time. Wire the
delta into the gates' scratch-only CHAIN extensions the way s44/s46 are wired (scratch
witness plumbing only — NOT into `bootstrap/new-project.sh`'s LINEAGE_CHAIN; after the
s44/s46 lineage-review finding, birth-chain entry is the maintainer's act, performed
delta-by-delta at the next `--new-world`).
