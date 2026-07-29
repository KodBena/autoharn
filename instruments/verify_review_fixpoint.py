#!/usr/bin/env python3
"""verify_review_fixpoint — both-polarity fixtures for the review_fixpoint close line (design note
ORCH-review-fixpoint-protocol.md). Proves the three-join criterion GREEN when a fresh first-contact reviewer
attests the final artifact with zero undisposed findings, and RED for each way it can fail:

  RED-1 (the e17 shape) — the final attest is a DELTA-review: same reviewer stamp already appeared earlier
        in the unit. This is exactly e17's terminating attest (row 18, reviewer a8d15e15 who reviewed at
        row 17); under the criterion e17 owes one criterion-review.
  RED-2 — an undisposed refuse-verdict review-finding survives.
  RED-3 — only an author self-attest of the final artifact (not stamp-distinct).
  GREEN — a fresh first-contact reviewer attests the final artifact; zero undisposed findings.

SESSION-AWARE DISTINCTNESS (kernel/lineage/s21-session-aware-distinctness.sql, mirrored in
review_fixpoint.py's `Invocation`): every interactive session's main thread stamps agent='main', so
agent-only comparison mis-scores a genuinely fresh CROSS-SESSION criterion-reviewer (same agent stamp
'main', a DIFFERENT session) as a same-invocation delta-review. Three more legs prove the fix red-first:

  CROSS-1 (was mis-scored RED under agent-only, must be GREEN under the pair) — the author's session
        's-author' builds the final artifact; a FRESH reviewer session 's-reviewer' attests it, both
        stamped agent='main'. Old code (r.stamp_agent != author_stamp) sees 'main' == 'main' and refuses
        as not-distinct; the pair-aware fix sees the sessions differ and scores it distinct + first-contact.
  PRESERVED-1 (s21's compatibility clause, byte-unchanged) — SAME session, SAME agent stays NOT distinct
        (the e17-shape self-review case, same_invocation True either way).
  PRESERVED-2 (s21's compatibility clause, byte-unchanged) — SAME session, DIFFERENT agent stays distinct
        (a subagent reviewer within the author's own session, e17/e18's witnessed passing shape).

It gates nothing; it proves the criterion for e18. Lazy imports banned.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_fixpoint import FpRow, Invocation, review_fixpoint_verdict  # noqa: E402

AUTHOR_SESSION = "s-author"
AUTHOR = Invocation.of(AUTHOR_SESSION, "main")


def _e17_shape() -> list[FpRow]:
    """The e17 unit, abstracted: author 'main' builds (final artifact row 14, the Fraction revision);
    reviewer a8d15e15 refuses row 12 (row 17, disposed by the fix) then delta-attests row 14 (row 18). All
    rows share the author's session — the e17 run's own single-session shape."""
    return [
        FpRow(10, "verification", None, None, AUTHOR_SESSION, "main"),   # author builds
        FpRow(12, "review", 10, "attest", AUTHOR_SESSION, "main"),       # author self-review stub
        FpRow(14, "revision", None, None, AUTHOR_SESSION, "main"),       # THE FINAL artifact version
        FpRow(17, "review", 10, "refuse", AUTHOR_SESSION, "a8d15e15", disposed=True),  # disposed refuse
        FpRow(18, "review", 14, "attest", AUTHOR_SESSION, "a8d15e15"),   # DELTA attest — same reviewer, seen at 17
    ]


def check() -> list[str]:
    bad: list[str] = []
    ck = lambda cond, msg: bad.append(msg) if not cond else None  # noqa: E731

    # RED-1: e17 shape — delta-review, not first-contact
    st, d = review_fixpoint_verdict(_e17_shape(), AUTHOR, final_artifact_id=14)
    ck(st == "RED" and "delta-review" in d.lower(),
       f"e17 shape must be RED (delta-review not first-contact): got {st} :: {d}")

    # GREEN: a fresh first-contact reviewer attests the final artifact, zero undisposed
    green = [FpRow(10, "verification", None, None, AUTHOR_SESSION, "main"),
             FpRow(14, "revision", None, None, AUTHOR_SESSION, "main"),
             FpRow(20, "review", 14, "attest", "s-fresh", "fresh-reviewer-xyz")]  # never seen earlier
    st, d = review_fixpoint_verdict(green, AUTHOR, final_artifact_id=14)
    ck(st == "GREEN", f"a fresh first-contact attest of the final artifact must be GREEN: got {st} :: {d}")

    # RED-2: an undisposed refuse-finding survives
    red2 = green + [FpRow(21, "review", 14, "refuse", "s-another", "another-reviewer", disposed=False)]
    st, d = review_fixpoint_verdict(red2, AUTHOR, final_artifact_id=14)
    ck(st == "RED" and "undisposed" in d.lower(),
       f"an undisposed refuse-finding must be RED: got {st} :: {d}")

    # RED-3: only an author self-attest (not stamp-distinct)
    red3 = [FpRow(14, "revision", None, None, AUTHOR_SESSION, "main"),
            FpRow(15, "review", 14, "attest", AUTHOR_SESSION, "main")]
    st, d = review_fixpoint_verdict(red3, AUTHOR, final_artifact_id=14)
    ck(st == "RED" and "stamp-distinct" in d.lower(),
       f"an author self-attest must be RED (not stamp-distinct): got {st} :: {d}")

    # CROSS-1 — RED-FIRST: reproduce the old agent-only bug, then prove the pair-aware fix.
    # Two rows both stamp_agent='main' (every interactive session's main thread) but DIFFERENT
    # stamp_session: the author's build session, and a genuinely fresh reviewer's own session.
    cross = [FpRow(30, "verification", None, None, AUTHOR_SESSION, "main"),   # author builds, session s-author
             FpRow(34, "revision", None, None, AUTHOR_SESSION, "main"),       # final artifact, session s-author
             FpRow(40, "review", 34, "attest", "s-reviewer", "main")]         # fresh reviewer, session s-reviewer
    # OLD (agent-only) behavior, reproduced directly against the pre-fix join shape named by s21's closure
    # statement: `r.stamp_agent != author_stamp` — 'main' != 'main' is False, so this row would NOT have
    # been counted distinct at all (mis-scored RED, "no stamp-distinct attesting review"). We witness that
    # mis-score explicitly here (not by calling retired code, which no longer exists) so the red/green
    # contrast is on the record:
    old_agent_only_distinct = [r for r in cross if r.kind == "review" and r.regards == 34
                                and r.verdict == "attest" and r.stamp_agent != "main"]
    ck(old_agent_only_distinct == [],
       f"sanity: the agent-only shape must mis-score CROSS-1 as not-distinct (empty distinct set); "
       f"got {old_agent_only_distinct}")
    # NEW (pair-aware) behavior: the sessions differ, so the pair is distinct and first-contact.
    st, d = review_fixpoint_verdict(cross, AUTHOR, final_artifact_id=34)
    ck(st == "GREEN",
       f"CROSS-1: a same-agent('main'), different-session reviewer must be GREEN under the pair-aware "
       f"fix (old agent-only code mis-scored this RED): got {st} :: {d}")

    # PRESERVED-1 — s21 compatibility clause, byte-unchanged: SAME session, SAME agent stays NOT distinct.
    # (This is exactly RED-3 above, restated as an explicit same-session same-agent specimen.)
    same_session_same_agent = [FpRow(14, "revision", None, None, AUTHOR_SESSION, "main"),
                                FpRow(15, "review", 14, "attest", AUTHOR_SESSION, "main")]
    st, d = review_fixpoint_verdict(same_session_same_agent, AUTHOR, final_artifact_id=14)
    ck(st == "RED" and "stamp-distinct" in d.lower(),
       f"PRESERVED-1: same session + same agent must stay NOT distinct (RED): got {st} :: {d}")

    # PRESERVED-2 — s21 compatibility clause, byte-unchanged: SAME session, DIFFERENT agent stays distinct
    # (a subagent reviewer within the author's own session — e17/e18's witnessed passing shape).
    same_session_diff_agent = [FpRow(10, "verification", None, None, AUTHOR_SESSION, "main"),
                                FpRow(14, "revision", None, None, AUTHOR_SESSION, "main"),
                                FpRow(20, "review", 14, "attest", AUTHOR_SESSION, "subagent-reviewer")]
    st, d = review_fixpoint_verdict(same_session_diff_agent, AUTHOR, final_artifact_id=14)
    ck(st == "GREEN",
       f"PRESERVED-2: same session + different agent must stay distinct/first-contact (GREEN): "
       f"got {st} :: {d}")
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
