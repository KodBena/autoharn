# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:31:50Z
#   last-change: 2026-07-18T21:31:57Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/checklist.py -- honesty rule 3 ("checklist truth"): a per-item
WITNESSED/SKIPPED/PREPARED record of everything the flow touched, kept as ONE list every screen
appends to (ADR-0012 P1 -- no screen keeps its own private tally), rendered as the closing
screen 9 table and, if the operator opts in, saved as a dated file inside the target directory
(v1 boundary: nothing written outside the target dir + this saved checklist)."""
from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field

WITNESSED = "WITNESSED"
SKIPPED = "SKIPPED"
PREPARED = "PREPARED"
REFUSED = "REFUSED"

_VALID = {WITNESSED, SKIPPED, PREPARED, REFUSED}


@dataclass
class ChecklistItem:
    screen: str
    item: str
    status: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in _VALID:
            raise ValueError(f"checklist status '{self.status}' not one of {_VALID}")


@dataclass
class Checklist:
    items: list[ChecklistItem] = field(default_factory=list)

    def add(self, screen: str, item: str, status: str, detail: str = "") -> None:
        self.items.append(ChecklistItem(screen=screen, item=item, status=status, detail=detail))

    def render(self) -> str:
        lines = []
        lines.append(f"{'SCREEN':<14} {'ITEM':<38} {'STATUS':<10} DETAIL")
        lines.append("-" * 100)
        for it in self.items:
            lines.append(f"{it.screen:<14} {it.item:<38} {it.status:<10} {it.detail}")
        counts: dict[str, int] = {}
        for it in self.items:
            counts[it.status] = counts.get(it.status, 0) + 1
        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        lines.append("-" * 100)
        lines.append(f"totals: {summary or '(none)'}")
        return "\n".join(lines)

    def save(self, target_dir: str) -> str:
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(target_dir, f"setup-checklist-{stamp}.txt")
        with open(path, "w") as f:
            f.write(self.render())
            f.write("\n")
        return path
