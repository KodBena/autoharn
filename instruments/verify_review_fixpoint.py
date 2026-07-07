#!/usr/bin/env python3
"""verify_review_fixpoint — both-polarity fixtures for the review_fixpoint close line (design note
review-fixpoint-protocol.md). Proves the three-join criterion GREEN when a fresh first-contact reviewer
attests the final artifact with zero undisposed findings, and RED for each way it can fail:

  RED-1 (the e17 shape) — the final attest is a DELTA-review: same reviewer stamp already appeared earlier
        in the unit. This is exactly e17's terminating attest (row 18, reviewer a8d15e15 who reviewed at
        row 17); under the criterion e17 owes one criterion-review.
  RED-2 — an undisposed refuse-verdict review-finding survives.
  RED-3 — only an author self-attest of the final artifact (not stamp-distinct).
  GREEN — a fresh first-contact reviewer attests the final artifact; zero undisposed findings.

It gates nothing; it proves the criterion for e18. Lazy imports banned.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_fixpoint import FpRow, review_fixpoint_verdict  # noqa: E402

AUTHOR = "main"


def _e17_shape() -> list[FpRow]:
    """The e17 unit, abstracted: author 'main' builds (final artifact row 14, the Fraction revision);
    reviewer a8d15e15 refuses row 12 (row 17, disposed by the fix) then delta-attests row 14 (row 18)."""
    return [
        FpRow(10, "verification", None, None, "main"),         # author builds
        FpRow(12, "review", 10, "attest", "main"),             # author self-review stub (refused-detail)
        FpRow(14, "revision", None, None, "main"),              # THE FINAL artifact version (the fix)
        FpRow(17, "review", 10, "refuse", "a8d15e15", disposed=True),   # reviewer's refuse (disposed by the fix)
        FpRow(18, "review", 14, "attest", "a8d15e15"),         # DELTA attest — same reviewer, seen at 17
    ]


def check() -> list[str]:
    bad: list[str] = []
    ck = lambda cond, msg: bad.append(msg) if not cond else None  # noqa: E731

    # RED-1: e17 shape — delta-review, not first-contact
    st, d = review_fixpoint_verdict(_e17_shape(), AUTHOR, final_artifact_id=14)
    ck(st == "RED" and "delta-review" in d.lower(),
       f"e17 shape must be RED (delta-review not first-contact): got {st} :: {d}")

    # GREEN: a fresh first-contact reviewer attests the final artifact, zero undisposed
    green = [FpRow(10, "verification", None, None, "main"),
             FpRow(14, "revision", None, None, "main"),
             FpRow(20, "review", 14, "attest", "fresh-reviewer-xyz")]  # never seen earlier
    st, d = review_fixpoint_verdict(green, AUTHOR, final_artifact_id=14)
    ck(st == "GREEN", f"a fresh first-contact attest of the final artifact must be GREEN: got {st} :: {d}")

    # RED-2: an undisposed refuse-finding survives
    red2 = green + [FpRow(21, "review", 14, "refuse", "another-reviewer", disposed=False)]
    st, d = review_fixpoint_verdict(red2, AUTHOR, final_artifact_id=14)
    ck(st == "RED" and "undisposed" in d.lower(),
       f"an undisposed refuse-finding must be RED: got {st} :: {d}")

    # RED-3: only an author self-attest (not stamp-distinct)
    red3 = [FpRow(14, "revision", None, None, "main"), FpRow(15, "review", 14, "attest", "main")]
    st, d = review_fixpoint_verdict(red3, AUTHOR, final_artifact_id=14)
    ck(st == "RED" and "stamp-distinct" in d.lower(),
       f"an author self-attest must be RED (not stamp-distinct): got {st} :: {d}")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"REVIEW-FIXPOINT WRONG: {b}")
    if bad:
        print(f"# review-fixpoint FAIL — {len(bad)} polarity(ies) wrong.")
        return 1
    print("# review-fixpoint PASS — GREEN on a fresh first-contact attest; RED on e17's delta-review, on "
          "an undisposed finding, and on an author self-attest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
