# Migration accommodations for frozen deltas — spec (RATIFIED)

Date: 2026-07-15, night. Author: the orchestrating Fable session (constitutional route:
Fable-authored, maintainer-ratified before any build). Status: RATIFIED 2026-07-15 (ledger
decision row 1018, verbatim: "design/FABLE-OBLIGATION-DEPENDENT-TYPING-SPEC.md, design/
MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md accepted, apply"); section 3's build shipped under
ledger work item `s26-accommodation-build` (claim-then-close, see that item's own commit for the
build report). Motivating evidence: ledger finding row 972 — the live world `autoharn1` heads at
s25, and `./migrate` rehearsal against a clone of its real history fails at s26
(`ALTER COLUMN row_hash SET NOT NULL` validates pre-existing rows), the same class sec-10 of
`MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md` cured for s29. s26 is frozen and predates the cure;
the class audit built under this spec (section 3, item 2) confirms s27/s28 (and every other
frozen delta s15 through s28) carry no comparable hazard — s26 is the sole blocker.

## 1. The problem, stated once for the class

A lineage delta authored for birth-chain delivery may carry constraints that VALIDATE
EXISTING ROWS at apply time (`ADD CONSTRAINT` without `NOT VALID`, `SET NOT NULL`,
two-way CHECKs). Against an empty birth-chain world these are inert; against a world
with history they refuse the whole migration. sec-10 fixed this for s29 by typing the
exemption (the migration epoch). Every OTHER frozen delta with the same shape is a
landmine on the migration path, discovered only when a real world steps on it — row 972
is the first witnessed instance.

## 2. Principle (sec-10's epoch rule, generalized; nothing else invented)

- **Frozen deltas stay byte-frozen.** No sNN file that has ever been applied to any
  world is edited. Ever. (ADR-0005 Rule 8 posture; this spec exists so nobody is
  tempted.)
- **Accommodations are siblings, not edits.** A delta that cannot apply over history
  gains a sibling file `kernel/lineage/sNN-<name>.accommodate.sql` — same convention
  family as the existing `.detect.sql`/`.verify.sql` siblings, which are precedent that
  siblings accompany frozen deltas without violating their freeze.
- **The exemption is typed, never catalog-state.** An accommodation may exempt only
  rows at-or-before the world's `migration_epoch` (sec-10's table — the one home for
  that fact), and the exemption must be expressed as a queryable predicate (trigger
  body or epoch-gated constraint), never as `NOT VALID` catalog subtlety — same
  legibility argument sec-10 already ratified for s29, applied uniformly.
- **Nothing relaxes for post-epoch rows.** An accommodation that weakens any guarantee
  for rows written after the migration is not an accommodation; it is a semantics
  change and routes to the maintainer as its own spec. Mechanical test: the delta's
  `.verify.sql` behavioral checks must pass identically on (a) a birth-chain world and
  (b) a migrated world, for all post-epoch rows.
- **Who applies what:** the birth chain NEVER uses accommodations (fresh worlds get the
  frozen delta verbatim, epoch 0, full governance). Only `./migrate`, on detecting
  pre-epoch history, applies `sNN.accommodate.sql` IN PLACE OF the frozen delta's
  history-validating statements — and the accommodation file itself carries, in its
  header, the exact statements of the frozen delta it substitutes for, so the
  substitution is reviewable line-against-line.

## 3. Scope of the initial build (on ratification)

1. **s26 accommodation** (`row_hash SET NOT NULL` → epoch-gated: post-epoch rows must
   carry `row_hash`, pre-epoch rows exempt by type; the hash-chain verification
   instruments must already tolerate a chain that starts mid-history — verify, do not
   assume). This is the one row-972 witnessed blocker.
2. **Class audit of every frozen delta** (s15 through s28): enumerate each
   history-validating statement, disposition each as SAFE-OVER-HISTORY (witnessed on
   the rehearsal clone) or NEEDS-ACCOMMODATION (built under this spec) — the audit
   table is the deliverable even where the answer is "safe."
3. **Authorship rule, forward-binding:** every FUTURE delta states its
   history-posture in its own header (`HISTORY: safe — reasons` or `HISTORY: requires
   accommodation — provided as sibling`), and `./migrate`'s rehearsal step refuses any
   delta whose header is silent. New deltas ship their accommodation at authorship or
   declare they need none; the landmine class ends at s29's successors.

## 4. Acceptance (all witnessed, both polarities, on a clone of real history)

- Rehearsal of the full s25→s29 chain over the autoharn1 clone: PASSES end-to-end;
  pre-epoch rows exempt; post-epoch governance witnessed identical to a birth-chain
  world (the `.verify.sql` equivalence test of §2).
- Negative controls: an accommodation attempting to relax a post-epoch guarantee is
  refused by the acceptance harness; a future delta without a HISTORY header is
  refused by `./migrate` rehearsal.
- The conveyor-death proof re-run on the migrated clone (witnessed close deposits zero
  `review_gap` debt) — the original point of the whole chain.

## 5. What this spec does not do

No frozen file edited; no live apply authorized (that remains the maintainer's typed
confirmation, per the recorded execution boundary); no change to birth-chain semantics;
the maintainer may instead choose world-rebirth over migration for autoharn1 — this
spec makes migration POSSIBLE, not mandatory.

<!-- doc-attest-exempt: RATIFIED 2026-07-15 (ledger decision row 1018) constitutional spec;
its own content is now final. Exempt marker KEPT (not removed) pending its own fresh-context
A:B:C loop (law/adr/0017), which has not run yet -- attesting is a separate act from
ratifying, and this build's own brief (ledger work item s26-accommodation-build) did not
commission that loop. Removal condition: the A:B:C loop runs and an attestation record for
this exact content lands in attestations/doc-legibility-attestations.jsonl. -->
