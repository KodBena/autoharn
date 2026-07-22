#!/usr/bin/env python3
"""Seen-red specimen for the relevant-act-classification gate (forecloses finding 9). Reproduces the
defect the fix names: RELEVANT_KINDS silently re-including `message_in`, so a change-order receipt
becomes auto-relevant — an edge the act stream cannot mechanically ground. Patches RELEVANT_KINDS to
add message_in, re-runs the deriver against the gate's oracle, and shows act 1 (a message_in receipt)
flips to relevant=True where the oracle says False. The divergence is banked as red.txt."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "experiments" / "fact-mining"))
import acts_join  # noqa: E402
from verify_relevant_act import CASES, FENCED  # noqa: E402


def main() -> int:
    acts_join.RELEVANT_KINDS = acts_join.RELEVANT_KINDS | {"message_in"}   # the finding-9 regression
    acts = [a for a, _ in CASES]
    d = acts_join.derive(acts, [], FENCED)
    bad = [f"act {a.id} ({a.kind}): relevant={d.relevant.get(a.id)}, oracle={want}"
           for a, want in CASES if d.relevant.get(a.id, False) != want]
    if not bad:
        print("SPECIMEN INERT — re-including message_in did not diverge from the oracle (unexpected).")
        return 1
    for b in bad:
        print(f"RELEVANCE MISCLASSIFIED: {b}")
    print(f"# relevant-act-classification FAIL — {len(bad)} act(s) diverge from oracle §4 "
          f"(a message_in receipt re-included, or a fenced write dropped).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
