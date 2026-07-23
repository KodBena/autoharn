#!/usr/bin/env python3
"""seen-red/setup-tui-configtree-journey/layout_invariant.py -- the GLOBAL post-interaction
layout invariant (ledger row 1139, NET half): wired into every `Pilot` interaction this fixture
drives (`wire_pilot` below, called once by `run_fixtures.py` at import time) -- not opt-in per
case. Row 1139's own diagnosed operational lapse was exactly this: "the fixture suite is a
museum of past incidents with no global invariant, so every layout change can remint the class
where no case looks" (the class had already recurred three times -- round-5 overlap, cycle-3
starvation, this round's own phantom expanse -- each patched locally, never checked for
globally). This module is that global net: once wired, EVERY existing case and every future one
added to this fixture is checked automatically, with no per-case opt-in required.

THREE checks, run over the app's entire mounted screen after every `Pilot.pause`/`click`/`press`:

  (a) GAP BUDGET -- no focusable/actionable widget (Textual's own `can_focus`: `Button`, `Input`,
      `RadioSet`, `Checkbox`, `ListView`) sits more than `BLANK_ROW_BUDGET` blank rows below its
      preceding VISIBLE sibling in the same parent container. A widget pushed far below a phantom
      expanse trips this the instant the expanse exists -- checked over the WIDGET TREE's own
      region geometry, never dependent on whether the viewport happens to be scrolled there (the
      maintainer's own bench report was framed in scrolling terms -- "reachable only by extensive
      scrolling" -- but the hazard is virtual-position, not viewport-position; this check reads
      the former).
  (b) CONTAINER HEIGHT VS CONTENT -- no container's own virtual height exceeds the sum of its
      DIRECT children's region heights plus `CONTAINER_HEIGHT_TOLERANCE`. This is the direct
      measurement of row 1139's own named class ("container claims height decoupled from content
      size") -- an `fr`-defaulting container handed 42 rows of virtual height for one real
      content row fails this by construction, independent of whether anything visibly ends up
      pushed below it (`item_modal.py`'s own "LATENT ROW-1139 SITE #2" note has an example that
      fails (b) without ever failing (a), because it happened to be the last child).
  (c) MASTER-DETAIL COMPLETENESS (maintainer refinement, same round) -- every declared sub-list of
      a `MasterDetailFieldWidget`'s CURRENTLY SELECTED master row has its own Add button present
      in the widget tree. This is the direct check for the "compose truncation" hypothesis this
      round's own reproduction work RULED OUT for the reported defect (every sub-list was present,
      just positioned below the phantom gap -- (a)/(b) above are what actually fired) -- checked
      unconditionally anyway, so a FUTURE regression that genuinely drops a sub-list (a swallowed
      compose exception, an early-return/loop bug) is caught by this same net, not only the
      height-decoupling class this round actually found.

BLANK_ROW_BUDGET=3 / CONTAINER_HEIGHT_TOLERANCE=1 are named constants, not guesses: calibrated
empirically against the REAL app's own ordinary chrome (a `.ct-md-block`'s own `margin: 1 0 0 0`,
a `Button`'s own 3-row rendered height including its border, a `.ct-field-label`'s own
`padding-top: 1`) -- the largest ORDINARY inter-sibling gap observed anywhere in a clean run of
this fixture is 1 row; 3 leaves headroom for legitimate future chrome without coming close to the
reproduced hazard's own 20-40+ row blank regions.

RED-FIRST: this module's own docstring in `run_fixtures.py`'s wiring note, and the fix round's own
report, record this invariant FAILING against the pre-fix `3f0e41b` tree's exact reproduction
(phantom gap measured) and PASSING after the fix -- the witness this file exists to make
routine, not a one-off.

Lazy imports banned."""
from __future__ import annotations

import contextlib

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widget import Widget

BLANK_ROW_BUDGET = 3
CONTAINER_HEIGHT_TOLERANCE = 1

_SUSPENDED = False


@contextlib.contextmanager
def suspended():
    """A NAMED, VISIBLE escape hatch -- never a silent one. `case_23` (this fixture's own file)
    deliberately execs a HISTORICAL `AddItemModal` snapshot straight from git history (`9fe6b64`,
    predating this fix round entirely) to RED-then-GREEN a DIFFERENT, already-fixed regression
    (the filter/option_help defect, ledger row 1136) -- that historical source's own `#ct-modal-
    buttons` predates row 1139's own fix too, and would otherwise trip this invariant for a defect
    class the historical block is not testing and was never meant to prove clean. Wrap ONLY that
    historical-specimen block in `with layout_invariant.suspended():` -- every current-code case
    in this fixture stays checked; this is not a general-purpose bypass, and its one call site is
    named in this module's own docstring precisely so it cannot quietly spread."""
    global _SUSPENDED
    previous = _SUSPENDED
    _SUSPENDED = True
    try:
        yield
    finally:
        _SUSPENDED = previous


def _visible_children(widget: Widget) -> "list[Widget]":
    return [c for c in widget.children if getattr(c, "display", True)]


def _ident(widget: Widget) -> str:
    wid = getattr(widget, "id", None)
    return f"{type(widget).__name__}#{wid}" if wid else f"{type(widget).__name__}(anon)"


def check_gap_budget(root: Widget) -> "list[str]":
    """Check (a): no focusable widget separated from its preceding visible sibling by more than
    `BLANK_ROW_BUDGET` blank rows."""
    violations: list[str] = []

    def walk(widget: Widget) -> None:
        children = _visible_children(widget)
        prev: "Widget | None" = None
        for child in children:
            if getattr(child, "can_focus", False) and prev is not None:
                gap = child.region.y - (prev.region.y + prev.region.height)
                if gap > BLANK_ROW_BUDGET:
                    violations.append(
                        f"GAP BUDGET: {_ident(child)} (y={child.region.y}) sits {gap} blank "
                        f"row(s) below its preceding sibling {_ident(prev)} (bottom="
                        f"{prev.region.y + prev.region.height}) inside {_ident(widget)} -- "
                        f"exceeds BLANK_ROW_BUDGET={BLANK_ROW_BUDGET}")
            prev = child
        for child in children:
            walk(child)

    walk(root)
    return violations


def check_container_height(root: Widget) -> "list[str]":
    """Check (b): no container's own virtual height exceeds the sum of its direct children's
    region heights plus `CONTAINER_HEIGHT_TOLERANCE` -- the direct measurement of row 1139's own
    named class.

    `VerticalScroll` (and any subclass) is EXCLUDED from this check by construction, not an
    oversight: a scroll shell's whole job is to offer a viewport that may legitimately be TALLER
    than its current content (that is what "nothing to scroll yet" looks like, verified
    empirically -- a `.ct-controls-col` region at a 400-row terminal with 43 rows of real content
    reports `virtual_size.height == 390`, its own allocated `1fr` share, not the content extent).
    That is not a phantom expanse pushing a SIBLING out of place -- it is the scroll shell's own
    trailing empty space, harmless by definition. The hazard this check exists for is an
    AUTO-height container (a `Vertical`/`Horizontal`/`ContentVertical`/`ContentHorizontal`) whose
    own size is supposed to be DERIVED from its children yet is not -- `VerticalScroll` never
    makes that promise in the first place. `Screen`/`ModalScreen` is excluded the SAME way, one
    level up: the screen canvas itself is always the FULL terminal size regardless of how much
    content it holds (verified empirically -- `ConfirmModal`, a short two-line dialog, reports its
    own `Screen.virtual_size.height` as the terminal's full height) -- that is centering/letterbox
    space around genuinely short content, not a phantom expanse either."""
    violations: list[str] = []

    def walk(widget: Widget) -> None:
        children = _visible_children(widget)
        if children and not isinstance(widget, (VerticalScroll, Screen)):
            children_sum = sum(c.region.height for c in children)
            vheight = widget.virtual_size.height
            if vheight > children_sum + CONTAINER_HEIGHT_TOLERANCE:
                violations.append(
                    f"PHANTOM VERTICAL EXPANSE: {_ident(widget)} virtual height {vheight} "
                    f"exceeds the sum of its {len(children)} visible children's region heights "
                    f"({children_sum}) + tolerance {CONTAINER_HEIGHT_TOLERANCE} -- row 1139's own "
                    f"'container claims height decoupled from content size' class")
        for child in children:
            walk(child)

    walk(root)
    return violations


def check_master_detail_completeness(root: Widget) -> "list[str]":
    """Check (c): every declared sub-list of a `MasterDetailFieldWidget`'s CURRENTLY SELECTED
    master row is present in the widget tree (its own Add button queryable). Imported lazily-by-
    name-only at call time via `root.query` -- no import of `tools.configtree.widgets_master_
    detail` here (this module stays importable even where that class is not; the identification
    below is duck-typed on the two attributes this check actually needs, `_selected_key`/`spec`,
    which only `MasterDetailFieldWidget` instances carry)."""
    violations: list[str] = []
    for widget in root.walk_children():
        selected_key = getattr(widget, "_selected_key", None)
        spec = getattr(widget, "spec", None)
        details = getattr(spec, "details", None)
        if selected_key is None or details is None:
            continue
        for d in details:
            dname = str(d.list_field.name)
            add_id = f"{widget.id}-detail-add-{dname}"
            if not widget.query(f"#{add_id}"):
                violations.append(
                    f"MASTER-DETAIL COMPLETENESS: {_ident(widget)}'s selected row is missing "
                    f"its own {dname!r} sub-list's Add button (#{add_id}) from the widget tree "
                    f"-- COMPOSE TRUNCATION")
    return violations


def check_all(root: Widget) -> "list[str]":
    return (check_gap_budget(root) + check_container_height(root)
            + check_master_detail_completeness(root))


def assert_layout_invariant(app) -> None:
    """The ONE call site every wired `Pilot` interaction (see `wire_pilot` below) runs. Checks
    over `app.screen` (the currently active screen -- a pushed modal, or the main screen), which
    covers every mounted content pane/dialog without needing the caller to name one."""
    if _SUSPENDED:
        return
    violations = check_all(app.screen)
    assert not violations, (
        "layout_invariant: " + str(len(violations)) + " violation(s):\n  "
        + "\n  ".join(violations))


def wire_pilot(pilot_cls) -> None:
    """Wraps `Pilot.pause`/`click`/`press` so `assert_layout_invariant` runs after EVERY
    interaction any case in this fixture drives -- called ONCE, at import time, by
    `run_fixtures.py` (never per-case: row 1139's own point is that no case should have to
    remember to check this). Idempotent (a repeated `wire_pilot` call is a harmless no-op) so
    importing this module twice in one process can never double-wrap."""
    if getattr(pilot_cls, "_layout_invariant_wired", False):
        return
    orig_pause = pilot_cls.pause
    orig_click = pilot_cls.click
    orig_press = pilot_cls.press

    async def pause(self, *a, **kw):
        result = await orig_pause(self, *a, **kw)
        assert_layout_invariant(self.app)
        return result

    async def click(self, *a, **kw):
        result = await orig_click(self, *a, **kw)
        assert_layout_invariant(self.app)
        return result

    async def press(self, *a, **kw):
        result = await orig_press(self, *a, **kw)
        assert_layout_invariant(self.app)
        return result

    pilot_cls.pause = pause
    pilot_cls.click = click
    pilot_cls.press = press
    pilot_cls._layout_invariant_wired = True
