#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T01:58:01Z
#   last-change: 2026-07-07T01:58:01Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""verify_relevant_act — the standing fixture for the deriver's ledger-relevance classification
(forecloses finding 9: `ledger_relevant_act` is oracle §4 MINUS the change-order-receipt `message_in`
clause — a deliberate, NAMED omission, not silent; the risk is that a later edit silently re-includes
message_in as auto-relevant, fabricating a mechanical edge the stream cannot ground). This pins
acts_join.derive()'s relevance verdict against a pre-registered oracle table so that drift flips RED.

Registered close/lint line id: `relevant-act-classification`. Lazy imports banned.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))  # autoharn: acts_join lives in engine/
from acts_join import ActRow, LedgerRow, derive  # noqa: E402

FENCED = "/fenced/"

# pre-registered (act -> is it ledger-relevant per oracle §4?). message_in/out and tool_result are NOT;
# plan_item_*/delegation_* are; a Write/Bash tool_call is relevant ONLY when its target is fenced.
CASES = [
    (ActRow(1, "message_in", "", ""), False),        # a change-order receipt is NOT auto-relevant (finding 9)
    (ActRow(2, "message_out", "", ""), False),
    (ActRow(3, "tool_result", "Bash", ""), False),
    (ActRow(4, "plan_item_created", "step1 parse", ""), True),
    (ActRow(5, "plan_item_closed", "step1 parse", ""), True),
    (ActRow(6, "delegation_spawn", "sub:general-purpose", ""), True),
    (ActRow(7, "delegation_return", "sub:general-purpose", ""), True),
    (ActRow(8, "tool_call", "Write", "/fenced/out.py"), True),      # fenced write IS relevant
    (ActRow(9, "tool_call", "Write", "/outside/x.py"), False),      # unfenced write is NOT
    (ActRow(10, "tool_call", "Read", "/fenced/out.py"), False),     # a read is NOT
]


def check() -> list[str]:
    acts = [a for a, _ in CASES]
    d = derive(acts, [LedgerRow(1, "note", "s", "/fenced/out.py", "")], FENCED)
    bad = []
    for a, want in CASES:
        got = d.relevant.get(a.id, False)
        if got != want:
            bad.append(f"act {a.id} ({a.kind}/{a.name or '-'}): relevant={got}, oracle={want}")
    return bad


def main() -> int:
    bad = check()
    for b in bad:
        print(f"RELEVANCE MISCLASSIFIED: {b}")
    if bad:
        print(f"# relevant-act-classification FAIL — {len(bad)} act(s) diverge from oracle §4 "
              f"(a message_in receipt re-included, or a fenced write dropped).")
        return 1
    print(f"# relevant-act-classification PASS — all {len(CASES)} acts classified per oracle §4 "
          f"(message_in receipts excluded by design; named kinds + fenced writes relevant).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
