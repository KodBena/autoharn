#!/usr/bin/env python3
"""seen-red/setup-tui-multichoice-filter/run_fixtures.py -- both-polarity proof of
`tools/configtree/widgets.py`'s `MultiChoiceFieldWidget` sub-heading + live-filter fix (MEDIUM
audit finding, ledger row 1130's own sibling audit: "hydration's 36-checkbox catalog renders as
one ~218-row unbroken scroll"), census-registered in gates/fixture_census.py.

RED (case 1): loads the OLD `MultiChoiceFieldWidget` straight from git history (`PRE_FIX_COMMIT`,
the last commit before this fix -- via `git show`, executed in an isolated namespace) against a
SYNTHETIC 20-option catalog (above `MULTICHOICE_FILTER_THRESHOLD`) with a `groups=` mapping the
CURRENT `MultiChoiceField` dataclass accepts but the OLD widget never reads -- proving the class
of defect: zero `ElucidationHeading`-classed `Static`s anywhere (no sub-headings at all,
whatever `groups` says) and no filter `Input` (the catalog just keeps growing, unbroken, however
large it gets).

GREEN (cases 2-5): the REAL, current `MultiChoiceFieldWidget`, same synthetic catalog:
  2. real sub-headings render (>=1 `.ct-elucidation-heading` `Static`), each a distinct group
     name, in the SAME order as the catalog.
  3. a filter `Input` renders (the catalog is above threshold) and narrows the VISIBLE checkbox
     count when typed into.
  4. clearing the filter restores every option (visible checkbox count back to the full catalog
     size).
  5. a selection made BEFORE filtering survives being filtered out of view and back in (`
     .selected` is the model's own source of truth, never rebuilt from a widget the filter
     hid) -- and a small (below-threshold) catalog renders NO filter Input at all (the threshold
     is a real gate, not decorative).

Zero residue: everything is synthetic (a bare `App` mounting one `MultiChoiceFieldWidget`), no
real filesystem/network act anywhere. Lazy imports banned.

Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-multichoice-filter/run_fixtures.py
"""
from __future__ import annotations

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from textual.app import App, ComposeResult  # noqa: E402
from textual.widgets import Checkbox, Input, Static  # noqa: E402

from tools.configtree.fields import MultiChoiceField  # noqa: E402
from tools.configtree.widgets import MULTICHOICE_FILTER_THRESHOLD  # noqa: E402
from tools.configtree.widgets import MultiChoiceFieldWidget as CurrentWidget  # noqa: E402

# The last commit before this fix -- pinned by SHA, never HEAD.
PRE_FIX_COMMIT = "3cc769d"


def _visible(widgets) -> list:
    """Filtering (the CURRENT widget) toggles `.display`, never unmounts -- `query()` alone
    finds every mounted Checkbox regardless of visibility, so every case below that cares what
    the OPERATOR actually sees filters through this."""
    return [w for w in widgets if w.display]

# One more option than the threshold allows without a filter -- exercises the ">" gate exactly,
# never leaves the "is this even above threshold" question ambiguous.
LARGE_N = MULTICHOICE_FILTER_THRESHOLD + 11
SMALL_N = MULTICHOICE_FILTER_THRESHOLD  # AT the threshold -- ">" means this must NOT filter.


def _synthetic_field(n: int, *, with_groups: bool) -> MultiChoiceField:
    options = tuple((f"opt-{i:02d}", f"Option {i:02d}") for i in range(n))
    groups = None
    if with_groups:
        groups = {f"opt-{i:02d}": f"Group {i // 5}" for i in range(n)}
    return MultiChoiceField(name="probe", label="Probe catalog", options=options, groups=groups)


def load_old_widget_class():
    """Fetches `MultiChoiceFieldWidget` exactly as it stood in `PRE_FIX_COMMIT` via `git show`,
    executed in an ISOLATED namespace (never imported as a module). Its own `from tools.
    configtree.fields import ...` line resolves against the REAL, CURRENT `fields.py` (which now
    carries the `groups` field) -- harmless, since the OLD widget class never reads `.groups` at
    all; this is exactly what proves the defect is in the WIDGET, not the data model."""
    src = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:tools/configtree/widgets.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {"__name__": "tools.configtree._old_widgets_for_fixture"}
    exec(compile(src, f"<git show {PRE_FIX_COMMIT}:tools/configtree/widgets.py>", "exec"), ns)
    return ns["MultiChoiceFieldWidget"]


class _HarnessApp(App):
    """Mounts exactly one `MultiChoiceFieldWidget` (or an old-code stand-in) -- this fixture's
    own subject is the WIDGET, not the section/tree/commit machinery the other configtree
    fixtures already cover end-to-end."""

    def __init__(self, widget) -> None:
        super().__init__()
        self._widget = widget

    def compose(self) -> ComposeResult:
        yield self._widget


async def case_1_red() -> None:
    OldWidget = load_old_widget_class()
    field = _synthetic_field(LARGE_N, with_groups=True)
    widget = OldWidget(field)
    app = _HarnessApp(widget)
    async with app.run_test(size=(120, 200)) as pilot:
        await pilot.pause()
        headings = widget.query(".ct-elucidation-heading")
        inputs = widget.query(Input)
        assert len(headings) == 0, (
            f"expected the OLD widget to render ZERO sub-headings regardless of `groups` -- "
            f"got {len(headings)}")
        assert len(inputs) == 0, (
            f"expected the OLD widget to render NO filter Input regardless of catalog size -- "
            f"got {len(inputs)}")
        checkboxes = widget.query(Checkbox)
        assert len(checkboxes) == LARGE_N, f"expected all {LARGE_N} checkboxes rendered unbroken"
        print(f"case 1 ok (RED, reproduced against {PRE_FIX_COMMIT}): a {LARGE_N}-option "
              f"catalog with a `groups` mapping rendered ZERO sub-headings and NO filter Input "
              f"-- one unbroken {len(checkboxes)}-checkbox scroll, exactly the audited defect")


async def case_2_headings() -> None:
    field = _synthetic_field(LARGE_N, with_groups=True)
    widget = CurrentWidget(field)
    app = _HarnessApp(widget)
    async with app.run_test(size=(120, 200)) as pilot:
        await pilot.pause()
        headings = list(widget.query(".ct-elucidation-heading"))
        texts = [str(h.render()) for h in headings]
        assert len(headings) >= 2, f"expected multiple real sub-headings, got {texts}"
        assert texts == sorted(set(texts), key=texts.index), "expected headings in catalog order, no dupes out of order"
        assert len(set(texts)) == len(texts), f"expected each contiguous run to heading ONCE, got {texts}"
        print(f"case 2 ok (GREEN): {len(headings)} distinct sub-headings render for a "
              f"{LARGE_N}-option grouped catalog: {texts}")


async def case_3_filter_narrows() -> None:
    field = _synthetic_field(LARGE_N, with_groups=False)
    widget = CurrentWidget(field)
    app = _HarnessApp(widget)
    async with app.run_test(size=(120, 200)) as pilot:
        await pilot.pause()
        filter_input = widget.query_one(Input)
        assert len(_visible(widget.query(Checkbox))) == LARGE_N, "expected the full catalog before filtering"
        filter_input.focus()
        await pilot.pause()
        for ch in "opt-00":
            await pilot.press(ch if ch != "-" else "minus")
        await pilot.pause()
        narrowed = _visible(widget.query(Checkbox))
        assert 0 < len(narrowed) < LARGE_N, (
            f"expected the filter to narrow the visible catalog (got {len(narrowed)} of "
            f"{LARGE_N}) -- typed {filter_input.value!r}")
        print(f"case 3 ok (GREEN): typing {filter_input.value!r} narrowed the catalog from "
              f"{LARGE_N} to {len(narrowed)} visible checkbox(es)")


async def case_4_clear_restores() -> None:
    field = _synthetic_field(LARGE_N, with_groups=False)
    widget = CurrentWidget(field)
    app = _HarnessApp(widget)
    async with app.run_test(size=(120, 200)) as pilot:
        await pilot.pause()
        filter_input = widget.query_one(Input)
        filter_input.focus()
        await pilot.pause()
        for ch in "zzz-no-match":
            await pilot.press({"-": "minus"}.get(ch, ch))
        await pilot.pause()
        assert len(_visible(widget.query(Checkbox))) == 0, "expected a non-matching filter to hide every checkbox"
        no_match = [w for w in widget.query(".ct-blocked-reason") if w.display]
        assert no_match, "expected an honest 'no option matches' line, not a silent blank"
        filter_input.value = ""
        await pilot.pause()
        restored = _visible(widget.query(Checkbox))
        assert len(restored) == LARGE_N, f"expected clearing the filter to restore all {LARGE_N}, got {len(restored)}"
        print(f"case 4 ok (GREEN): a non-matching filter hides every option (with an honest "
              f"'no match' line, not a silent blank), clearing it restores all {LARGE_N}")


async def case_5_selection_survives_filter() -> None:
    field = _synthetic_field(LARGE_N, with_groups=False)
    widget = CurrentWidget(field)
    app = _HarnessApp(widget)
    async with app.run_test(size=(120, 200)) as pilot:
        await pilot.pause()
        cb0 = widget.query_one("#" + widget.id + "-opt-opt-00", Checkbox)
        cb0.value = True
        await pilot.pause()
        assert "opt-00" in widget.selected, "expected the checkbox toggle to register in .selected"

        filter_input = widget.query_one(Input)
        filter_input.focus()
        await pilot.pause()
        for ch in "opt-19":
            await pilot.press({"-": "minus"}.get(ch, ch))
        await pilot.pause()
        cb0_hidden = widget.query_one("#" + widget.id + "-opt-opt-00", Checkbox)
        assert not cb0_hidden.display, \
            "expected opt-00's own checkbox to be filtered OUT of view (does not match 'opt-19')"
        assert "opt-00" in widget.selected, \
            "expected opt-00 to STAY selected in the model even while its checkbox is hidden"

        filter_input.value = ""
        await pilot.pause()
        cb0_again = widget.query_one("#" + widget.id + "-opt-opt-00", Checkbox)
        assert cb0_again.value is True, "expected opt-00's checkbox to render CHECKED again once the filter no longer excludes it"
        print("case 5 ok (GREEN): a selection made before filtering survives being filtered "
              "out of view and reappears checked once the filter clears")

    small_field = _synthetic_field(SMALL_N, with_groups=False)
    small_widget = CurrentWidget(small_field)
    small_app = _HarnessApp(small_widget)
    async with small_app.run_test(size=(120, 60)) as pilot:
        await pilot.pause()
        assert not small_widget.query(Input), (
            f"expected NO filter Input for a catalog AT the threshold ({SMALL_N} options) -- "
            f"the gate is '>', not '>='")
        print(f"case 5b ok (GREEN): a {SMALL_N}-option catalog (AT threshold) renders NO filter "
              f"Input -- the gate only fires once the catalog is genuinely large")


async def _main() -> None:
    await case_1_red()
    await case_2_headings()
    await case_3_filter_narrows()
    await case_4_clear_restores()
    await case_5_selection_survives_filter()
    print("ALL CASES OK -- MultiChoiceFieldWidget's sub-heading (spec.groups) + live-filter "
          "(above MULTICHOICE_FILTER_THRESHOLD) fix: RED-first against the OLD widget (zero "
          "headings, no filter, whatever the data said), GREEN against the CURRENT widget "
          "(real sub-headings in catalog order, a filter that narrows/restores/keeps an honest "
          "no-match line, and selections that survive being filtered out of view).")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_main())
