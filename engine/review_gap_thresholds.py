#!/usr/bin/env python3
"""review_gap_thresholds -- the ONE home (ADR-0012 P1) of the content-free-review-statement
threshold shared, single-homedly, by every consumer that needs to answer "is this review
statement content-free?":

  1. engine/review_gap_edb.py -- the EDB exporter feeding engine/lp/review_gap_audit.lp (the
     ASP producer of the content-free-review-discharge audit).
  2. engine/review_gap_floor.py -- the independent SQL floor (producer two of the same marriage;
     it does NOT call `is_content_free` below -- see that module's own docstring for why an
     independently-authored SQL regex is the correct move for I6 independence -- but it DOES
     import `CONTENT_FREE_STATEMENT_THRESHOLD` from here, interpolated into its own SQL text, so
     the *value* still has one home even though the *computation path* is deliberately separate).
  3. bootstrap/templates/led.tmpl's `review` subcommand -- the warn-only intake tripwire, which
     shells out to this module's own CLI (`main()` below) exactly as that file already shells out
     to `python3` for `filing/deployment_record.py` (led.tmpl's own established convention: a
     bash verb reads a Python-owned fact via a `python3` subprocess rather than re-implementing
     it in shell).

THE WITNESSED SPECIMEN (run12 ledger row 20 -- the audit family this module underwrites is
commissioned directly off it): a `review` row whose entire statement is `"test"` (4 chars) was
written by the reviewer principal while syntax-testing the LIVE ledger. Under
`<schema>.review_gap`'s discharge semantics (kernel/lineage/s13-schema.sql: ANY unsuperseded
`attest` from a distinct actor discharges the obligation -- content is never examined by the
view), that 4-char row MECHANICALLY DISCHARGED row 4's countersign obligation. Row 4 also
happened to receive a genuine, 935-char review (row 22) later -- but the discharge had already
happened via row 20, and none of run12's six reviewer passes ever flagged it. See
engine/review_gap_edb.py's own docstring for the full audit-family account; this module owns
only the one shared number and the one shared normalization rule the Python-side consumers apply
directly (the SQL floor re-derives the SAME rule independently, in SQL).

THRESHOLD JUSTIFICATION (documented in-code per this work item's own instruction: "pick and
DOCUMENT it in the code ... justify your choice against the real corpus"). Measured read-only,
2026-07-12, against run12's real `review`-kind rows (`psql -h 192.168.122.1 -d toy` -- `SELECT
id, length(btrim(regexp_replace(statement,'\\s+',' ','g'))) AS norm_len FROM run12.ledger WHERE
kind='review' ORDER BY norm_len;`, n=42 review rows total including the specimen):

    row 20 (the specimen):  norm_len =    4   "test"
    row 55 (shortest GENUINE review): norm_len =  130  "Straightforward work_claimed row for..."
    every other genuine review: norm_len in [130, 2441], median in the several-hundred range.

There is a wide, empty gap between the specimen (4 chars) and the shortest real review this
project's own history has ever produced (130 chars) -- no genuine review in the measured corpus
falls anywhere near this boundary. CONTENT_FREE_STATEMENT_THRESHOLD = 40 sits in the middle of
that gap: ~36 chars of headroom above the specimen (so trivially-worse specimens like "ok",
"lgtm", "fine", "confirmed", "attest", "looks good to me" are ALSO caught -- the class the
specimen represents, not just its exact instance) and ~90 chars of headroom below the shortest
genuine review this corpus has ever produced (so the check has never, on the one real corpus
measured, produced a false positive against a genuine review). 40 is a shape, not a proof: a
future genuine review terser than 40 normalized chars is conceivable (a one-line "Confirmed,
matches row N's criteria exactly." runs closer to 40 than 130), which is exactly why this audit's
own verdict vocabulary is FLAGGED, never VIOLATED -- see engine/review_gap_edb.py's docstring for
the honest limit this check does not claim to close.

Lazy imports banned (top-of-file only; this module needs only `sys`, for its own CLI)."""
from __future__ import annotations

import sys

# The one shared number (ADR-0012 P1) -- see the docstring's THRESHOLD JUSTIFICATION section for
# the corpus measurement backing this exact value. A whitespace-normalized statement STRICTLY
# BELOW this length is content-free-shaped.
CONTENT_FREE_STATEMENT_THRESHOLD = 40


def normalize(statement: str) -> str:
    """Whitespace-normalize a statement for length measurement: collapse every run of whitespace
    (space, tab, newline, ...) to a single ASCII space, and strip leading/trailing whitespace --
    so 'test   ', '  test', and 'te   st' are measured honestly, never inflated or deflated by
    incidental whitespace a paste or a terminal line-wrap introduced. `str.split()` with no
    argument already splits on any run of whitespace and drops empty tokens, so a plain
    `" ".join(...)` round-trip is the whole rule -- no regex needed on the Python side (the SQL
    floor's own independent re-implementation, per this module's own docstring, IS a regex,
    because SQL has no equivalent primitive)."""
    return " ".join(statement.split())


def is_content_free(statement: str) -> bool:
    """True iff `statement`'s whitespace-normalized length is strictly below
    CONTENT_FREE_STATEMENT_THRESHOLD -- the one predicate every consumer of this module shares."""
    return len(normalize(statement)) < CONTENT_FREE_STATEMENT_THRESHOLD


def main(argv: list[str] | None = None) -> int:
    """CLI surface for bootstrap/templates/led.tmpl's bash intake tripwire (mirrors led.tmpl's
    own existing `python3 - <<PYEOF` convention for reading `filing/deployment_record.py`'s
    facts): with no arguments, prints the threshold alone (an operator/gate sanity check); with
    one or more arguments (led.tmpl passes `"$statement"` as a single arg, but every arg is
    joined so a caller need not worry about internal quoting), prints `FLAGGED <n>` or
    `CLEAN <n>` where `<n>` is the normalized length -- so the bash side needs neither a
    hand-copied number nor a second normalization algorithm (ADR-0012 P1: one home)."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(CONTENT_FREE_STATEMENT_THRESHOLD)
        return 0
    statement = " ".join(args)
    n = len(normalize(statement))
    print(f"{'FLAGGED' if n < CONTENT_FREE_STATEMENT_THRESHOLD else 'CLEAN'} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
