#!/usr/bin/env python3
"""Seen-red specimen for the binder-bind-many gate (forecloses finding 39). Reproduces the pre-fix
binder — the earliest-UNUSED-act rule that marked an act 'used' after ONE binding — over the fixture's
batch case (one act inserting three rows). The old rule binds only the first row and leaves the other
two UNBOUND, exactly the e17 artifact (unbound_row(2,3,5,6,7,8,14)). Banked as red.txt."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "experiments" / "fact-mining"))
from verify_binder import A40, PerfRow, _insert  # noqa: E402
from row_performed_by import InsertAct  # noqa: E402


def _old_bind(rows, acts):
    """The pre-fix rule: each act binds at most ONE row (marked 'used')."""
    row_insert, used = {}, set()
    for r in sorted(rows, key=lambda x: x.id):
        k = r.statement.strip()[:40].strip()
        if not k:
            continue
        for a in sorted(acts, key=lambda x: x.act_id):
            if a.act_id in used:
                continue
            if k in a.command:
                row_insert[r.id] = a.act_id
                used.add(a.act_id)
                break
    return row_insert


def main() -> int:
    rows = [PerfRow(1, "author", "Row alpha — the first batched statement"),
            PerfRow(2, "author", "Row beta — the second batched statement"),
            PerfRow(3, "author", "Row gamma — the third batched statement")]
    acts = [InsertAct(act_id=10, stream="main",
                      command=_insert(rows[0].statement, rows[1].statement, rows[2].statement))]
    bound = _old_bind(rows, acts)
    unbound = sorted(r.id for r in rows if r.id not in bound)
    if not unbound:
        print("SPECIMEN INERT — the old rule bound all batch rows (unexpected).")
        return 1
    print(f"BINDER WRONG: batch rows {unbound} UNBOUND under the one-act-one-row rule "
          f"(only row {sorted(bound)[0]} bound to act 10; the other batch members have no act left to bind).")
    print("# binder-bind-many FAIL — a batch act did not bind all its rows (the finding-39 artifact).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
