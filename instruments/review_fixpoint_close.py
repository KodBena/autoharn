#!/usr/bin/env python3
"""review_fixpoint_close — run the review_fixpoint criterion (review_fixpoint.py, the e18 lever) over a
LIVE unit ledger at close. Pulls the unit's rows from the target (ledger LEFT JOIN review_detail — a
detail-less review row carries verdict NULL, finding 38's shape), builds FpRow per row, and prints the
three-join verdict. DESCRIPTIVE at close-1 AND close-2 (consult 37 two-close structure): the oracle's
anchor is which verdict each close records, not a gate. Lazy imports banned.

Calibration vocabulary (maintainer ruling, 2026-07-07 e18-ratification forward; SSOT =
claude_harness/docs/design-notes/ORCH-review-fixpoint-protocol.md): this line evaluates ONE round of the
fixpoint loop. The loop's per-unit parameters are named in full words only — confirmation-depth
(consecutive clean rounds to terminate, default 1), panel-width (fresh reviewers per round, default 1
at e-series grain), round-ceiling (hard cap on total rounds including dirty ones; hitting it closes
RED-honest, never auto-attested). Single-letter/abbreviated spellings are retired (same-spelling-drift).
e18's phase, retroactively: confirmation-depth=1, panel-width=2, round-ceiling=1.

SESSION-AWARE (kernel/lineage/s21-session-aware-distinctness.sql): the author identity is now the
(session, agent) PAIR, threaded through as two optional trailing args below — an `author_stamp` with no
`author_session` degrades fail-safe (a missing session half is NEVER distinct, s21's rule; see
`review_fixpoint.py`'s `Invocation.same_as`), never fail-open into agent-only comparison. If the target's
`ledger` table itself has no `stamp_session` column (s21 not applied to that schema — true of every
pre-s21 historical target: e15..e18), this line REFUSES loudly rather than silently falling back to
agent-only reads (ADR-0015 Rule 4) — the target's `led show`/schema needs s21 (or a later lineage that
folds it in) before this line can compute session-aware distinctness there.

  review_fixpoint_close.py <target> <final_artifact_id> [<author_stamp>=main] [<author_session>]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_target import resolve  # noqa: E402
from review_fixpoint import FpRow, Invocation, review_fixpoint_verdict  # noqa: E402

# a refuse-verdict review-finding counts disposed iff a later revision row supersedes it (the unit's only
# disposal idiom at this tier); GREEN's join (iii) reads this flag.
_SQL = """
SELECT l.id, l.kind, l.regards, rd.verdict, l.stamp_session, l.stamp_agent,
       EXISTS (SELECT 1 FROM {rel} s WHERE s.supersedes = l.id) AS superseded
FROM {rel} l LEFT JOIN {detail} rd ON rd.ledger_id = l.id
ORDER BY l.id;
"""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    target, final_id = argv[0], int(argv[1])
    author_stamp = argv[2] if len(argv) > 2 else "main"
    author_session = argv[3] if len(argv) > 3 else None
    author = Invocation.of(author_session, author_stamp)
    t = resolve(target)
    if not t.has_col("stamp_session"):
        print(f"# review_fixpoint[{target}]: target's ledger has no stamp_session column (s21 not applied "
              f"to this schema) — refusing rather than silently computing agent-only distinctness "
              f"(kernel/lineage/s21-session-aware-distinctness.sql's fail-safe rule).", file=sys.stderr)
        return 2
    rows = [FpRow(id=int(r[0]), kind=r[1], regards=(int(r[2]) if r[2] else None), verdict=(r[3] or None),
                  stamp_session=(r[4] or None), stamp_agent=(r[5] or ""), disposed=(r[6] == "t"))
            for r in t.rows(_SQL.format(rel=t.rel(), detail=t.rel("review_detail")))]
    status, detail = review_fixpoint_verdict(rows, author, final_id)
    print(f"# review_fixpoint[{target}] final_artifact={final_id} "
          f"author=(session={author_session!r}, agent={author_stamp!r})")
    print(f"  [{status}] {detail}")
    return 0 if status == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
