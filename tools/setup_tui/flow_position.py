#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-22T00:10:59Z
#   last-change: 2026-07-22T00:14:07Z
#   contributors: 1fa3ab69/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/flow_position.py -- the operator's position over the decision-phase screen
sequence, and the ability to move it backward (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md,
commission the maintainer's verbatim observation (e): "no way to navigate back and forth in the
TUI, so if you change your mind you have to start over").

THE TYPE (spec §1(a)): a cursor over the screen list, plus per-screen visit records, both
first-class -- `ScreenVisit` is one completed screen (which screen, and the WHOLE decision-phase
`state` dict as it stood the instant that screen finished); `FlowPosition` is the ordered stack of
visits plus the cursor. "Go back" = pop the most recent visit and restore the state exactly as it
stood before that screen ran (`visits[-1]`'s own recorded post-state, or the flow's `base_state`
if nothing is left) -- copy-on-write over the visit list (ADR-0001): a revisit REPLACES the
popped visit's record when the screen completes again, it is never patched in place, so a
downstream screen whose inputs changed is simply re-entered when the driver reaches it again
(invalidation is structural -- the driver's own forward walk -- not tracked by hand, spec §1(a)).

WHY A WHOLE-STATE SNAPSHOT PER VISIT, NOT A HAND-ENUMERATED FOOTPRINT: the spec's own worked
`ScreenVisit` sketch carries a `facts: dict` footprint a screen would compute by hand ("the state
keys this visit wrote"). This module derives the equivalent property structurally instead: a deep
copy of `state` (and the shared `Checklist`'s row count) taken the instant a screen finishes IS
the fold of every visit up to and including it, by construction -- restoring it is exactly
"refold up to cursor N", without asking any of the eleven screens to enumerate their own writes
by hand (a duplicative, drift-prone catalog `tools/setup_tui/screens.py` -- explicitly out of
scope for this build, per the commission's own scope discipline -- would otherwise need). The
same reasoning applies to `state["plan"]` (`tools.setup_tui.plan.Plan`, append-only): a deep copy
naturally discards any plan entries a since-abandoned screen attempt queued, and any checklist
rows it added are discarded by truncating `Checklist.items` back to the recorded row count --
both mutable objects a screen writes into directly rather than reassigning, so a snapshot taken
AFTER a screen completes is the only way to see everything it did.

Nothing here calls a runner choke point, writes a file, or starts a process -- this module is
pure bookkeeping over in-memory `state`/`Checklist` snapshots, exempt from
`gates/setup_tui_purity_gate.py`'s tables by simply never doing anything they check for."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from tools.setup_tui.ui import NavigableUi, NavigateBack, Ui


@dataclass
class ScreenVisit:
    """One completed screen: which `SCREENS` entry it was, the full decision-phase `state` dict
    exactly as it stood the instant this screen returned (a deep copy -- the screen's own dict
    object is never retained, so a LATER in-place mutation of that dict by a subsequent screen can
    never reach back and corrupt this record), the shared `Checklist`'s row count at that same
    instant (so going back can truncate away every row this screen or anything after it added),
    and this screen's own answers (prompt text -> answer), offered back as defaults if the
    operator returns to this screen again."""

    screen: str
    state_after: dict
    checklist_len: int
    answers: dict[str, object] = field(default_factory=dict)


@dataclass
class FlowPosition:
    """The back stack (spec §1(a)): `visits` holds one `ScreenVisit` per screen completed so far,
    in order; `cursor` is always `len(visits)` in normal forward motion (kept as an explicit field
    rather than derived, so a caller can read "how far in" without also needing the list). `
    base_state` is a deep copy of `state` as it stood before ANY screen ran -- what `go_back`
    restores when it pops the very first visit (there is no `visits[-2]` to fall back on there).
    `last_answers` remembers each screen's own most recent answers EVEN AFTER its visit is popped,
    so answers survive across more than one single-step back-and-forth (spec §1(a): "re-enter the
    screen with its previous answers offered as defaults" -- true of the last time it ran, not
    merely the time immediately before the current cursor)."""

    base_state: dict
    visits: list[ScreenVisit] = field(default_factory=list)
    cursor: int = 0
    last_answers: dict[str, dict[str, object]] = field(default_factory=dict)

    def can_go_back(self) -> bool:
        """True iff at least one completed screen precedes the one now live -- "any completed
        screen is a legal target" (spec §2); false only at the very first screen of this session
        (or of a `--start-at` sub-sequence, which is exactly where the spec says navigation
        should stay a documented no-op, not a crash)."""
        return len(self.visits) > 0

    def prior_answers_for(self, screen: str) -> dict[str, object]:
        """The answers this screen gave the LAST time it ran (empty dict on a screen's first-ever
        visit) -- what a re-entering `NavigableUi` offers back as defaults/hints."""
        return dict(self.last_answers.get(screen, {}))

    def record(self, screen: str, state_after: dict, checklist_len: int,
               answers: dict[str, object]) -> None:
        """Called once a screen returns NORMALLY (never on a `NavigateBack`) -- appends this
        visit and advances the cursor. `state_after`/`answers` are deep-copied here (the ONE
        place this module ever copies out of the driver's live objects), so nothing the driver
        does to its own `state`/`answers` dicts afterward can reach back into this record."""
        self.visits.append(ScreenVisit(screen=screen, state_after=copy.deepcopy(state_after),
                                        checklist_len=checklist_len, answers=dict(answers)))
        self.last_answers[screen] = dict(answers)
        self.cursor += 1

    def go_back(self) -> tuple[dict, int]:
        """Pops the most recently completed visit and returns `(state, checklist_len)` -- the
        state and checklist-row-count exactly as they stood right before that screen ran, so the
        caller can re-enter it fresh. Raises `IndexError` if `can_go_back()` is False; callers
        are expected to check first (the driver's own "already at the first screen" message is
        the honest response to that case, not a crash)."""
        self.visits.pop()
        self.cursor -= 1
        if self.visits:
            prior = self.visits[-1]
            return copy.deepcopy(prior.state_after), prior.checklist_len
        return copy.deepcopy(self.base_state), 0


def run_screen(fn, ui: Ui, cl, state: dict, name: str, is_commit_screen: bool,
               flow: FlowPosition) -> tuple[dict, bool, bool]:
    """Runs one screen with the navigation seam wired -- factored out of `app.py._drive_screens`
    to keep that function's own size down (ADR-0007). Returns `(state, advance, went_back)`:

      - normal completion -> `(new_state, True, False)`; the caller advances its cursor (this
        function already called `flow.record(...)`).
      - `NavigateBack`, nothing to go back to (`flow.can_go_back()` False) -> `(state, False,
        False)`; the caller retries the SAME screen (its own cursor unchanged).
      - `NavigateBack`, popped to a prior screen -> `(restored_state, False, True)`; the caller
        decrements its cursor (this function already popped `flow` and truncated `cl.items`).

    `is_commit_screen` (True only for the final screen, `screen_checklist`, which alone calls
    `commit_executor.execute`) skips the `NavigableUi` wrap entirely -- spec §2's "once the
    operator confirms the final review screen ... navigation ends" boundary."""
    if is_commit_screen:
        return fn(ui, cl, state), True, False
    nav_ui = NavigableUi(ui, prior_answers=flow.prior_answers_for(name))
    try:
        new_state = fn(nav_ui, cl, state)
    except NavigateBack:
        if not flow.can_go_back():
            return state, False, False
        restored_state, checklist_len = flow.go_back()
        del cl.items[checklist_len:]
        return restored_state, False, True
    flow.record(name, new_state, len(cl.items), nav_ui.answers)
    return new_state, True, False
