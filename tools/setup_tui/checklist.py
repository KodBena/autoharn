"""tools/setup_tui/checklist.py -- honesty rule 3 ("checklist truth"): a per-item status record
of everything the flow touched, kept as ONE list every screen appends to (ADR-0012 P1 -- no
screen keeps its own private tally), rendered as the closing checklist screen's table and, if
the operator opts in, saved as a dated file inside the target directory (v1 boundary: nothing
written outside the target dir + this saved checklist).

STATUS-VOCABULARY SPLIT (design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md \xa72, backflow finding
3): the original single `PREPARED` status blurred two different claims -- "the operator was
told what to run" and "the thing this line depends on exists / is running" -- into one word.
The witnessed consequence: an opted-in monitoring feature's PREPARED rows read as assurance
while the printed start line referenced a config file the scaffold never wrote, so a real
coverage gap was invisible. `PREPARED` splits into three closed members, names final per the
spec:

  * `INSTRUCTED` -- the operator was shown a command/unit text; nothing about the world's state
    is claimed. (The old PREPARED's honest reading -- always legal, never lies.)
  * `PREPARED` -- NARROWED: every prerequisite artifact the printed instruction references was
    confirmed present AT PRINT TIME (a config file exists, a resolved interpreter exists). A
    PREPARED row names its confirmed prerequisites in its own `detail` -- enforced below,
    construction-time (ADR-0002 rung 1): a screen may not emit PREPARED with an empty detail.
  * `VERIFIED_UP` -- a live probe, taken AFTER the thing it verifies actually ran, confirmed the
    named service running/healthy (the substrate/boundary screens' existing post-keypress-probe
    pattern, promoted to vocabulary for the new daemon-selection sweep, spec \xa73 point 3).

  and one closed, NAMED absence-rendering the spec's \xa75 note asks this module to resolve
  (rather than leaving "selected but never came up" as an ad hoc REFUSED/WITNESSED-with-a-sad-
  detail): `NOT_UP` -- the end-of-run daemon-verification sweep probed a SELECTED daemon and it
  was not there. Chosen as a NAMED closed-vocabulary member (not an ad hoc `REFUSED` reuse or a
  bare absent-row convention) because it is neither "an operator declined" (SKIPPED) nor "a
  validation gate said no before anything ran" (REFUSED) nor "the effect happened but reported
  failure" (WITNESSED with a red detail, the pattern boundary's own /health probe already uses)
  -- it is its own honest claim, "selected, attempted, and STILL not observably up", and giving
  it its own word is what makes it impossible to confuse with a REFUSED validation gate in a
  report or a fixture assertion (ADR-0008: a fuzzy reuse of an existing status is exactly the
  vocabulary drift this closed-enum discipline exists to foreclose).

`--dry-run` (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19 amendment) adds two more statuses to the
SAME table, deliberately -- the amendment's own words are "the checklist's own per-item
discipline", not a second table shape: WOULD_DO (an act that would have run, live, but did not --
`runner.run_command`/`start_background`/`write_file`'s `dry_run=True` path) and DRY_SKIPPED (a
PREPARED-block verification gate -- a post-keypress probe or a live re-check -- that a dry run
skips rather than fakes, 'never silently passed' per the amendment).

CHOICE-ATTRIBUTION SPLIT (maintainer round 5, ledger row 1115: "the checklist then recorded
operator-declined for defaults the operator never touched -- false attribution of choice"). A
single generic `SKIPPED` used to carry THREE different claims about an item the flow never
finalized: "the operator interacted and said no", "the widget's own compile-time default was
never touched at all", and "a PARENT gate being off made this item's own state moot, never
evaluated". Collapsing all three into one word made a report reader see "the operator declined
X" for an X nobody ever looked at. Split into three closed, honest members (a report reader can
now tell "he said no" from "he never got here" from "nothing upstream of this ever ran"):

  * `DECLINED` -- the operator TOUCHED this decision (visited/toggled it,
    `tools.configtree.fields.is_field_touched` reads True) and its final value says no/skip.
  * `DEFAULTED` -- the value is exactly its own compile-time default AND was never touched
    (`is_field_touched` reads False) -- an absence of interaction, never an operator's word.
  * `SKIPPED` -- NARROWED to its one remaining honest meaning: a PARENT gate/section being off
    (or blocked) made this item's own state moot before it was ever individually evaluated --
    never reused for "the operator said no" (that is `DECLINED` now)."""
from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field

from tools.setup_tui.runner import write_file

WITNESSED = "WITNESSED"
SKIPPED = "SKIPPED"
DECLINED = "DECLINED"
DEFAULTED = "DEFAULTED"
INSTRUCTED = "INSTRUCTED"
PREPARED = "PREPARED"
VERIFIED_UP = "VERIFIED-UP"
NOT_UP = "NOT-UP"
REFUSED = "REFUSED"
WOULD_DO = "WOULD-DO"
DRY_SKIPPED = "DRY-SKIPPED"

_VALID = {WITNESSED, SKIPPED, DECLINED, DEFAULTED, INSTRUCTED, PREPARED, VERIFIED_UP, NOT_UP,
          REFUSED, WOULD_DO, DRY_SKIPPED}


def choice_status(touched: bool) -> str:
    """The ONE place a NOT-chosen decision's own checklist status is computed from
    (`tools.configtree.is_field_touched`'s own answer) -- never inlined ad hoc per call site, so
    `DECLINED` vs `DEFAULTED` is never a judgment call two screens make differently. Only for the
    "why is this NOT happening" question -- a chosen/affirmed item gets its own WITNESSED/queued
    row elsewhere, never this function."""
    return DECLINED if touched else DEFAULTED


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
        if self.status == PREPARED and not self.detail.strip():
            raise ValueError(
                "checklist status PREPARED requires a non-empty detail NAMING the "
                "prerequisite(s) confirmed present at print time (design/FABLE-SETUP-TUI-"
                "CHECKLIST-SPLIT-SPEC.md \xa72: 'a screen may not emit PREPARED without "
                "listing what it checked') -- use INSTRUCTED if nothing about the world's "
                "state was confirmed, only a command/unit text shown"
            )


@dataclass
class Checklist:
    items: list[ChecklistItem] = field(default_factory=list)

    def add(self, screen: str, item: str, status: str, detail: str = "") -> None:
        self.items.append(ChecklistItem(screen=screen, item=item, status=status, detail=detail))

    def counts(self) -> dict[str, int]:
        """Per-status tally -- the one home (ADR-0012 P1) both `render()` (the saved-file form)
        and `tools/setup_tui/screens.py`'s on-screen `Table` display (design/FABLE-SETUP-TUI-
        TYPED-UI-SPEC.md) read, so the two never drift into two counting implementations."""
        out: dict[str, int] = {}
        for it in self.items:
            out[it.status] = out.get(it.status, 0) + 1
        return out

    def summary_line(self) -> str:
        return ", ".join(f"{k}={v}" for k, v in sorted(self.counts().items())) or "(none)"

    def render(self) -> str:
        lines = []
        lines.append(f"{'SCREEN':<14} {'ITEM':<38} {'STATUS':<10} DETAIL")
        lines.append("-" * 100)
        for it in self.items:
            lines.append(f"{it.screen:<14} {it.item:<38} {it.status:<10} {it.detail}")
        lines.append("-" * 100)
        lines.append(f"totals: {self.summary_line()}")
        return "\n".join(lines)

    def save(self, target_dir: str, *, dry_run: bool = False) -> str:
        """Writes the rendered checklist into `target_dir` (v1 boundary: the one place besides
        the target dir itself this package writes) UNLESS `dry_run`, in which case the path is
        still computed and returned (so the caller can name it in the WOULD-DO row) but nothing
        is written.

        FINDING-3 FIX (fresh-context review of b565db1): this used to be a bare
        `open(path, "w").write(...)` -- the EXACT truncate-then-write shape `runner.write_file`
        exists to prevent (a kill mid-write leaves `path` neither pre- nor post-state), with a
        comment claiming "the same discipline, inlined" that the code did not actually carry (no
        temp-file-then-atomic-rename anywhere). Routed through the REAL choke point,
        `runner.write_file`, now -- genuinely the same atomicity every other write in this
        package gets, not a claim.

        This IS a declared exception site, alongside `commit_executor.py` and
        `screen_rehearsal` (gates/setup_tui_purity_gate.py's own EXEMPT table names it
        explicitly) -- but a narrower one than either: the checklist save is structurally
        POST-commit machinery, not a decision-phase effect. It cannot be a plan entry executed
        DURING the commit (the checklist's own final content, including every entry's real
        commit-time status, is not known until the commit has already finished), and it runs
        only from the flow's own terminal step (`screen_checklist`), after `_execute_commit` has
        already run (or been declined, or been a dry run) -- never before, never mid-flow."""
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = os.path.join(target_dir, f"setup-checklist-{stamp}.txt")
        content = self.render() + "\n"
        wrote = write_file(path, content, dry_run=dry_run)
        assert wrote or dry_run  # write_file's own contract: False only under dry_run
        return path
