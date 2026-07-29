#!/usr/bin/env python3
"""review_fixpoint — the review fixed-point close line (design note ORCH-review-fixpoint-protocol.md; consult
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

SESSION-AWARE DISTINCTNESS (kernel/lineage/s21-session-aware-distinctness.sql, defect 1's named-in-passing
Python-instrument member): an invocation's identity is the PAIR (stamp_session, stamp_agent), never
stamp_agent alone — every interactive session's main thread stamps agent='main', so agent-only comparison
mis-scores a genuinely fresh cross-session criterion-reviewer as NOT stamp-distinct / NOT first-contact
(a false RED — refuses an honest closure, never admits a false one; s21's own compatibility framing).
`Invocation` (below) is the one constructing home for that pair (standing row 26, no bare types): every
distinctness/first-contact comparison in this module goes through `Invocation.same_as`, which mirrors
s21's NULL-half rule verbatim — a missing session or agent on EITHER side is NEVER distinct, fail-safe,
never fail-open.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Invocation:
    """The (stamp_session, stamp_agent) PAIR that identifies one invocation — the same identity rule
    kernel/lineage/s21-session-aware-distinctness.sql establishes for validate_independence() and
    review_stamp_distinctness, mirrored here for review_fixpoint's two comparisons. `of` is the ONE
    constructing home (standing row 26): it normalizes a SQL NULL/empty string and a Python '' to the
    same missing-half representation (`None`), so `same_as`'s fail-safe check is never fooled by an
    empty-string stand-in for missing data."""
    session: str | None
    agent: str | None

    @classmethod
    def of(cls, session: str | None, agent: str | None) -> "Invocation":
        return cls(session or None, agent or None)

    @property
    def complete(self) -> bool:
        return self.session is not None and self.agent is not None

    def same_as(self, other: "Invocation") -> bool:
        """SAME invocation iff either pair is incomplete (fail-safe — a NULL/missing half is NEVER
        distinct, s21's rule verbatim) or the two pairs are equal."""
        if not self.complete or not other.complete:
            return True
        return (self.session, self.agent) == (other.session, other.agent)


@dataclass(frozen=True)
class FpRow:
    """One row of a unit's ledger, enough to decide the fixed point. `stamp_session`/`stamp_agent` are
    the interception stamp's PAIR (the true invocation, F53 + s21); `disposed` applies to a refuse-verdict
    review-finding."""
    id: int
    kind: str                 # 'review' or an artifact-bearing kind (verification/revision/decision/…)
    regards: int | None       # for a review: the row it attests/refuses
    verdict: str | None       # for a review: 'attest' | 'attest_with_reservations' | 'refuse'
    stamp_session: str | None
    stamp_agent: str
    disposed: bool = False     # a refuse-verdict review-finding that has been disposed (fixed/waived/…)

    @property
    def invocation(self) -> Invocation:
        return Invocation.of(self.stamp_session, self.stamp_agent)


def review_fixpoint_verdict(rows: list[FpRow], author: Invocation, final_artifact_id: int) -> tuple[str, str]:
    """The three-join criterion over one unit. GREEN iff the final artifact version carries a
    stamp-distinct, first-contact attesting review AND no review-finding is left undisposed. `author` is
    the (session, agent) PAIR that built the final artifact — both comparisons below are computed on the
    PAIR (s21's rule), never on `stamp_agent` alone."""
    # (i) a stamp-distinct ATTESTING review of the FINAL artifact version
    attests = [r for r in rows if r.kind == "review" and r.regards == final_artifact_id
               and r.verdict == "attest"]
    distinct = [r for r in attests if not r.invocation.same_as(author)]
    if not distinct:
        return ("RED", f"no stamp-distinct attesting review of the final artifact (row {final_artifact_id}) "
                f"— an author self-attest or no attest at all does not close the fixed point")
    # (ii) FIRST-CONTACT: the attesting reviewer's (session, agent) pair must not appear on any EARLIER
    # row of the unit
    def seen_earlier(rev: FpRow) -> bool:
        return any(o.invocation.same_as(rev.invocation) and o.id < rev.id for o in rows)
    first_contact = [r for r in distinct if not seen_earlier(r)]
    if not first_contact:
        seen = sorted({(r.stamp_session, r.stamp_agent) for r in distinct})
        return ("RED", f"the final attest is a DELTA-review, not first-contact — reviewer (session, agent) "
                f"{seen} already appeared earlier in the unit; a fresh first-contact review is owed")
    # (iii) ZERO undisposed review-findings
    undisposed = sorted(r.id for r in rows if r.kind == "review" and r.verdict == "refuse" and not r.disposed)
    if undisposed:
        return ("RED", f"{len(undisposed)} undisposed review-finding(s): rows {undisposed} — the fixed "
                f"point requires every review-finding disposed")
    return ("GREEN", f"review_fixpoint satisfied: row {first_contact[0].id} (session "
            f"{first_contact[0].stamp_session}, agent {first_contact[0].stamp_agent}) is a stamp-distinct, "
            f"first-contact attest of the final artifact, zero undisposed review-findings")
