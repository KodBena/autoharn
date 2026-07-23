# s46 defeat-input exclusion — one quantification domain (raw history)

<!-- doc-attest-exempt: build-basis spec; attestation rides witnessed delivery -->

**Status: Fable-authored 2026-07-18, build basis for one kernel lineage delta (next
free sNN at build time). Ratification: maintainer-delegated adjudication, ledger row
1647 ("I have to yield competence on the matter to you"), read plainly per the
2026-07-11 vocabulary note. Provenance: the divergence was named by s46's own header
(`kernel/lineage/s46-credited-views.sql`, the defeat-input-exclusion domain note at
approximately lines 55-70) and re-surfaced by the 2026-07-18 model consult
([design/FABLE-AUTOHARN-IDR-CONSULT-2026-07-18.md](../vestigial_documentation/design/FABLE-AUTOHARN-IDR-CONSULT-2026-07-18.md),
Part 2 item 4, moved to vestigial 2026-07-23 as a settled, fully-adjudicated consult record). Per runs-are-linear, the delta is a file + scratch witnesses; it
reaches reality in the NEXT world's birth chain, and entry into
`bootstrap/new-project.sh`'s LINEAGE_CHAIN remains the maintainer's act.**

## The defect

s46's credited views test defeat-input membership (the exclusion that keeps the
defeat calculus from defeating its own input rows) over `ledger_current`, while both
engine producers of `./judge --layer defeat` test it over full raw history. The two
domains diverge on exactly one shape: a row that served as machinery input and was
later superseded by a row of a different kind drops out of `ledger_current`, so the
view stops excluding a row the authoritative engine layer still protects — the view
can display as defeated what the differential says is not defeatable.

## The ruling (row 1647)

The exclusion quantifies over RAW HISTORY, the engine's domain. Grounds, verbatim
from the adjudication: the engine differential is authoritative and the view is
display-only, so where they diverge the view is wrong by architecture; "was this row
ever machinery input" is a history fact (the s31 reader-discipline class of
`LDuplicateOpen`) — later supersession cannot retroactively un-input it; and the
direction is fail-safe — raw history excludes strictly MORE rows from defeat, so
nothing becomes newly defeatable.

**Class: NOT letter-2(a)** (it re-issues existing view definitions, changing their
semantics on the divergence shape). It is built under the row-1647 delegated
ratification. Effect is strictly protective: the only behavioral change is that rows
previously defeatable-by-the-view-only stop being so.

## Mechanism

One lineage delta re-issuing (CREATE OR REPLACE) the s46 views whose defeat-input
exclusion currently reads `ledger_current`, with that exclusion subquery re-pointed
at the raw ledger — matching the engine producers' quantification exactly. The
builder reads `kernel/lineage/s46-credited-views.sql` in full first and changes ONLY
the exclusion's domain: no join, column, grant, or any other predicate changes. If
both `model_defeated_rows` and `credited_current` carry the exclusion, both are
re-issued; if only one does, one is. `.detect.sql` sibling per house convention.

## Witnesses (scratch schema, both polarities, judge differential AGREE)

- **WS46-a (the divergence world, red-then-green):** construct on the scratch pair
  the exact shape s46's header names — a defeat-machinery input row superseded by a
  different-kind row, plus a defeated-candidate row. BEFORE the delta: witness the
  view/engine disagreement (the pre-fix polarity reproduced). AFTER: view and both
  engine producers agree; `./judge --layer defeat` differential AGREE.
- **WS46-b (no regression):** a plain world with attestation mismatches and no
  kind-changing supersession chain — defeated set identical before and after the
  delta, byte-for-byte on the view output.
- **WS46-c (fail-safe direction):** confirm on WS46-a's world that the delta only
  SHRINKS the view's defeated set (set-difference emptiness in the
  newly-defeatable direction), witnessing the ruling's ground (3) mechanically.

The model-side counterpart (both-domain reads + the divergence characterization,
in build under the 2026-07-18 consult resurrection) is corroborating evidence and
will be cited on delivery; it is not a precondition for this delta.

## Build conditions

Scratch-only harness wiring; SQL/ASP differential AGREE per the standing class
requirement; NO edits to `bootstrap/new-project.sh` (maintainer's chain act); NO
edits to s46's shipped file (the delta is a NEW lineage file re-issuing the views,
the same way every amendment to shipped definitions has landed since
runs-are-linear).
