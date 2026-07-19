# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:31:50Z
#   last-change: 2026-07-19T01:00:14Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/checklist.py -- honesty rule 3 ("checklist truth"): a per-item
WITNESSED/SKIPPED/PREPARED record of everything the flow touched, kept as ONE list every screen
appends to (ADR-0012 P1 -- no screen keeps its own private tally), rendered as the closing
screen 9 table and, if the operator opts in, saved as a dated file inside the target directory
(v1 boundary: nothing written outside the target dir + this saved checklist).

`--dry-run` (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19 amendment) adds two more statuses to the
SAME table, deliberately -- the amendment's own words are "the checklist's own per-item
discipline", not a second table shape: WOULD_DO (an act that would have run, live, but did not --
`runner.run_command`/`start_background`/`write_file`'s `dry_run=True` path) and DRY_SKIPPED (a
PREPARED-block verification gate -- a post-keypress probe or a live re-check -- that a dry run
skips rather than fakes, 'never silently passed' per the amendment)."""
from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field

WITNESSED = "WITNESSED"
SKIPPED = "SKIPPED"
PREPARED = "PREPARED"
REFUSED = "REFUSED"
WOULD_DO = "WOULD-DO"
DRY_SKIPPED = "DRY-SKIPPED"

_VALID = {WITNESSED, SKIPPED, PREPARED, REFUSED, WOULD_DO, DRY_SKIPPED}


def status_for(res) -> str:
    """The ONE place a screen turns a `runner.CommandResult`/`runner.BackgroundResult` into a
    checklist status -- reads `res.dry_run`/`res.ok` off the result itself rather than making
    every call site re-derive the same three-way branch (a live success is WITNESSED, a live
    failure is REFUSED, anything under `dry_run=True` is WOULD_DO regardless of the simulated
    `ok` -- `runner.run_command`'s own docstring: 'a SIMULATED success ... never mistaken for a
    real one', this is the one function trusted to un-mistake it)."""
    if getattr(res, "dry_run", False):
        return WOULD_DO
    return WITNESSED if res.ok else REFUSED


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

    def save(self, target_dir: str, *, dry_run: bool = False) -> str:
        """Writes the rendered checklist into `target_dir` (v1 boundary: the one place besides
        the target dir itself this package writes) UNLESS `dry_run`, in which case the path is
        still computed and returned (so the caller can name it in the WOULD-DO row) but nothing
        is written -- the same `runner.write_file` discipline, inlined here since this is the
        one file-write site that is not driven by a caller-supplied content string."""
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(target_dir, f"setup-checklist-{stamp}.txt")
        if dry_run:
            return path
        with open(path, "w") as f:
            f.write(self.render())
            f.write("\n")
        return path
