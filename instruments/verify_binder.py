#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T12:25:31Z
#   last-change: 2026-07-07T12:25:31Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""verify_binder — pins row_performed_by's ONE-ACT-MAY-BIND-MANY binding (forecloses finding 39, the
binder batch-insert artifact; consult 35 (b)). A single act may INSERT several rows (a heredoc), so its
command carries each batched row's statement; the binder must bind ALL of them, while still binding two
rows that share a truncated key but were inserted by DIFFERENT acts to their own act. Both polarities:

  1. BATCH — one act inserts three distinct rows -> all three bound to it (the finding-39 fix; the prior
     'used-once' rule left the non-first two UNBOUND).
  2. GENUINE-ABSENT — a row whose statement no act carries stays unbound (no fabricated binding).
  3. PREFIX-COLLISION — two rows sharing the first 40 chars but inserted by different acts each bind to
     their OWN act (the first act's single key-occurrence is consumed by the first row).

Registered close/lint line id: `binder-bind-many`. Lazy imports banned.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from row_performed_by import InsertAct, PerfRow, derive  # noqa: E402

A40 = "A" * 40  # a shared 40-char (== _KEYLEN) prefix for the collision case


def _insert(*statements: str) -> str:
    return "; ".join(f"INSERT INTO ledger(statement) VALUES ('{s}')" for s in statements)


def check() -> list[str]:
    bad: list[str] = []
    rows = [
        PerfRow(1, "author", "Row alpha — the first batched statement"),
        PerfRow(2, "author", "Row beta — the second batched statement"),
        PerfRow(3, "author", "Row gamma — the third batched statement"),
        PerfRow(4, "author", "Row delta — never inserted by any act"),
        PerfRow(5, "author", A40 + "-five"),
        PerfRow(6, "author", A40 + "-six"),
    ]
    acts = [
        InsertAct(act_id=10, stream="main",
                  command=_insert(rows[0].statement, rows[1].statement, rows[2].statement)),  # batch of 3
        InsertAct(act_id=11, stream="main", command=_insert(rows[4].statement)),  # collision row 5
        InsertAct(act_id=12, stream="main", command=_insert(rows[5].statement)),  # collision row 6
    ]
    d = derive(rows, acts)

    # 1. BATCH — rows 1,2,3 all bound to act 10
    for rid in (1, 2, 3):
        if d.row_insert.get(rid) != 10:
            bad.append(f"batch row {rid} must bind to act 10 (got {d.row_insert.get(rid)}) — the finding-39 fix")
    # 2. GENUINE-ABSENT — row 4 unbound
    if 4 not in d.unbound_row or 4 in d.row_insert:
        bad.append(f"row 4 (never inserted) must be UNBOUND (unbound={d.unbound_row})")
    # 3. PREFIX-COLLISION — row 5 -> act 11, row 6 -> act 12
    if d.row_insert.get(5) != 11:
        bad.append(f"collision row 5 must bind to its own act 11 (got {d.row_insert.get(5)})")
    if d.row_insert.get(6) != 12:
        bad.append(f"collision row 6 must bind to its own act 12 (got {d.row_insert.get(6)}) — not steal act 11")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"BINDER WRONG: {b}")
    if bad:
        print(f"# binder-bind-many FAIL — {len(bad)} defect(s): a batch act did not bind all its rows, or a "
              f"collision mis-bound.")
        return 1
    print("# binder-bind-many PASS — a batch act binds all its rows; a genuinely-absent row stays unbound; "
          "colliding rows bind to their own acts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
