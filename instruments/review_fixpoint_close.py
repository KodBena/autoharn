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

  review_fixpoint_close.py <target> <final_artifact_id> [<author_stamp>=main]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger_target import resolve  # noqa: E402
from review_fixpoint import FpRow, review_fixpoint_verdict  # noqa: E402

# a refuse-verdict review-finding counts disposed iff a later revision row supersedes it (the unit's only
# disposal idiom at this tier); GREEN's join (iii) reads this flag.
_SQL = """
SELECT l.id, l.kind, l.regards, rd.verdict, l.stamp_agent,
       EXISTS (SELECT 1 FROM {rel} s WHERE s.supersedes = l.id) AS superseded
FROM {rel} l LEFT JOIN {detail} rd ON rd.ledger_id = l.id
ORDER BY l.id;
"""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    target, final_id = argv[0], int(argv[1])
    author = argv[2] if len(argv) > 2 else "main"
    t = resolve(target)
    rows = [FpRow(int(r[0]), r[1], int(r[2]) if r[2] else None, r[3] or None, r[4] or "",
                  disposed=(r[5] == "t"))
            for r in t.rows(_SQL.format(rel=t.rel(), detail=t.rel("review_detail")))]
    status, detail = review_fixpoint_verdict(rows, author, final_id)
    print(f"# review_fixpoint[{target}] final_artifact={final_id} author_stamp={author}")
    print(f"  [{status}] {detail}")
    return 0 if status == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
