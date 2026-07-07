#!/usr/bin/env python3
"""review_fixpoint — the review fixed-point close line (design note review-fixpoint-protocol.md; consult
35 §5 e18 lever candidate). A completion claim for a unit under this policy is RED unless the FINAL
artifact version carries an attesting review that is (i) STAMP-DISTINCT from the author, (ii) FIRST-CONTACT
(its stamp never appeared earlier in the unit — a fresh reviewer, not a directed delta-review), and
(iii) leaves ZERO undisposed review-findings. Three derivable joins over stamps + the findings idiom; NO
new machinery. The fixed point is STRUCTURAL (zero surviving findings), never the verbal verdict
"flawless" (inflatable; biases the reviewer toward history-anchoring or nit-manufacturing).

IT GATES NOTHING YET. This module arms e18: the criterion-review lever. Attachment is per-unit via the
policy-instance idiom; wiring it into a gating set is e18's ratification step, not this build's.

Two review species (design note): a DELTA-review (same reviewer, briefed on the fix) is anchored by
construction and NEVER terminates the loop; only a CRITERION-review (fresh first-contact stamp, blind
brief) terminates. e17's terminating attest (row 18, reviewer a8d15e15 who already reviewed at row 17)
was a delta-review — so e17 does NOT satisfy this criterion (the banked RED specimen). Lazy imports banned.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FpRow:
    """One row of a unit's ledger, enough to decide the fixed point. `stamp_agent` is the interception
    stamp (the true invocation, F53); `disposed` applies to a refuse-verdict review-finding."""
    id: int
    kind: str                 # 'review' or an artifact-bearing kind (verification/revision/decision/…)
    regards: int | None       # for a review: the row it attests/refuses
    verdict: str | None       # for a review: 'attest' | 'attest_with_reservations' | 'refuse'
    stamp_agent: str
    disposed: bool = False     # a refuse-verdict review-finding that has been disposed (fixed/waived/…)


def review_fixpoint_verdict(rows: list[FpRow], author_stamp: str, final_artifact_id: int) -> tuple[str, str]:
    """The three-join criterion over one unit. GREEN iff the final artifact version carries a
    stamp-distinct, first-contact attesting review AND no review-finding is left undisposed."""
    # (i) a stamp-distinct ATTESTING review of the FINAL artifact version
    attests = [r for r in rows if r.kind == "review" and r.regards == final_artifact_id
               and r.verdict == "attest"]
    distinct = [r for r in attests if r.stamp_agent != author_stamp]
    if not distinct:
        return ("RED", f"no stamp-distinct attesting review of the final artifact (row {final_artifact_id}) "
                f"— an author self-attest or no attest at all does not close the fixed point")
    # (ii) FIRST-CONTACT: the attesting reviewer's stamp must not appear on any EARLIER row of the unit
    def seen_earlier(rev: FpRow) -> bool:
        return any(o.stamp_agent == rev.stamp_agent and o.id < rev.id for o in rows)
    first_contact = [r for r in distinct if not seen_earlier(r)]
    if not first_contact:
        seen = sorted({r.stamp_agent for r in distinct})
        return ("RED", f"the final attest is a DELTA-review, not first-contact — reviewer stamp(s) {seen} "
                f"already appeared earlier in the unit; a fresh first-contact review is owed")
    # (iii) ZERO undisposed review-findings
    undisposed = sorted(r.id for r in rows if r.kind == "review" and r.verdict == "refuse" and not r.disposed)
    if undisposed:
        return ("RED", f"{len(undisposed)} undisposed review-finding(s): rows {undisposed} — the fixed "
                f"point requires every review-finding disposed")
    return ("GREEN", f"review_fixpoint satisfied: row {first_contact[0].id} (stamp "
            f"{first_contact[0].stamp_agent}) is a stamp-distinct, first-contact attest of the final "
            f"artifact, zero undisposed review-findings")
