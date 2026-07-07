#!/usr/bin/env python3
"""verify_review_without_detail — both-polarity fixture for the review-without-detail consumer (finding
38; consult 37 Addendum A). GREEN behavior: a detail-less review row is SURFACED; a review row that
carries its detail is NOT surfaced. Pins the descriptive derivation. Lazy imports banned."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_without_detail import ReviewRow, derive  # noqa: E402


def check() -> list[str]:
    bad: list[str] = []
    # a mixed unit: review 12 is the e17-shape STUB (no detail); reviews 17,18 carry their detail
    rows = [ReviewRow(12, has_detail=False), ReviewRow(17, has_detail=True), ReviewRow(18, has_detail=True)]
    got = derive(rows)
    if got != [12]:
        bad.append(f"the detail-less review 12 must be surfaced, the detailed ones not (got {got})")
    # all-detailed -> empty
    if derive([ReviewRow(1, True), ReviewRow(2, True)]) != []:
        bad.append("a unit whose every review carries its detail must surface nothing")
    # all-stub -> all surfaced
    if derive([ReviewRow(5, False), ReviewRow(6, False)]) != [5, 6]:
        bad.append("every detail-less review must be surfaced")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"REVIEW-WITHOUT-DETAIL WRONG: {b}")
    if bad:
        print(f"# review-without-detail FAIL — {len(bad)} defect(s).")
        return 1
    print("# review-without-detail PASS — detail-less review rows surfaced (the finding-38 stub), "
          "detailed reviews not; descriptive, non-gating.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
