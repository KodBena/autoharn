#!/usr/bin/env python3
"""tools/configtree/layout_split.py -- the control/help split every section (`panes.SectionPane`)
and action (`actions.ActionPane`) pane renders through (ledger row 1138: maintainer major
reopening the converged cycle-4 loop, from his own 251-column screenshot of principals-authority
-- "I have to scroll just to find action surfaces ... instead of the UI leveraging hierarchical
design and using a scrollable text component situated next to each action surface").

THE DEFECT, in his own naming: content/chrome separation violated (a control -- a label, a
widget, an Add button -- belongs in a STABLE, always-reachable region; only CONTENT should have
to scroll past itself), progressive disclosure absent (deep reference prose -- a section's own
Constitutes/Does-not elucidation, a field's `help`, a `ChoiceField` option's `option_help` --
rendered fully expanded INLINE, between the very controls an operator is trying to reach), and
available width unused (a single `MEASURE`-capped (78-column) content ribbon on a 251-column
screen, `measure.py`'s own docstring's cap being "a prose line-length rule, not a one-column
layout mandate" -- his own words, restated, since this fix is the direct answer to that
distinction).

GENRE (his own proposal, and the one this fix implements): Qt Creator's docked help pane / SAP's
F1 side panel -- a compact CONTROL column (what you interact with) beside an independently-
scrollable HELP column (what you might want to read), at a width comfortable enough for both;
below that width, the split collapses and the help content becomes ON-DEMAND disclosure (a
footer keybinding toggles it back inline, single-column, exactly the shape this pane rendered
before this fix) rather than silently reverting to the old fully-expanded interleave.

WIDE_LAYOUT_MIN_WIDTH (a named constant, not a guess): the FULL terminal width (this is what an
operator's real resize/Pilot `size=(w, h)` actually varies, and what the maintainer's own two
named acceptance widths -- 251 and 120 -- are given in) at which BOTH columns can be genuinely
usable at once, summed from its own named parts so there is exactly one number to revisit if any
part of it changes:
    TREE_WIDTH (40, `app.py`'s own CSS `Tree { width: 40; }`) -- the sidebar's own CONTENT
    footprint. `border-right: solid` in that same rule draws INSIDE the declared `width: 40`
    (Textual's border-box model, confirmed empirically: the Tree's content region measures 39,
    not 40, at any terminal width), so the border itself adds no column beyond the 40 already
    counted here -- TREE_BORDER (1) is NOT a second border-width term stacked on top of it (an
    earlier draft of this comment read that way, a one-column bookkeeping slip this cycle's
    audit caught, ledger row 1140's own m1); it is one column of DELIBERATE margin between the
    sidebar and the control column, kept because 127 is the maintainer-witnessed, field-
    validated boundary (his own 251/120 acceptance pair below) -- dropping it would shave the
    threshold to 126 and move that already-verified boundary for a cosmetic naming fix, not a
    real one
  + CONTROL_COL_WIDTH (44 -- comfortable for a field label, an `Input`, and an "Add ..." button
    side by side without wrapping every label; close to the sidebar Tree's own 40, since a
    control column carries similar content -- short labels and buttons, not paragraphs)
  + LAYOUT_GUTTER (2 -- a visible seam between the two columns, so neither reads as a stray
    continuation of the other)
  + HELP_COL_MIN (40 -- a comfortable MINIMUM for the help column to read as more than a sliver;
    deliberately NOT the full `MEASURE` (78) -- `measure.py`'s own cap already bounds how wide a
    help line ever needs to be to read well, so the SPLIT only needs "wide enough that neither
    column is a sliver," not "wide enough for the help column to hit its own cap already." A
    terminal wider than this threshold gives the surplus to whichever column has room to use it
    (Textual's own `1fr`/`max-width` interplay -- `app.py`'s own CSS note), the help column
    capped at `MEASURE + 8` regardless, so extra width past that cap flows to the control column,
    never to an ever-wider text column nobody reads any faster for)
  = 127. Verified against the maintainer's own two acceptance widths: 251 >= 127 (wide, split
    renders) and 120 < 127 (narrow, collapses) -- the exact two outcomes his own report expects
    at those two sizes, not a coincidence; also keeps every EXISTING seen-red/setup-tui-
    configtree-journey fixture's own 150-column width on the WIDE side of the line (unchanged
    layout family for all of them -- only the ONE narrower, 80-column cell in that same fixture
    was ever narrow, and stays narrow here too)."""
from __future__ import annotations

from tools.configtree.widget_primitives import elucidation_widgets

TREE_WIDTH = 40
TREE_BORDER = 1  # margin, not a second border-width -- the border draws INSIDE TREE_WIDTH (module docstring, ledger row 1140 m1)
CONTROL_COL_WIDTH = 44
LAYOUT_GUTTER = 2
HELP_COL_MIN = 40

WIDE_LAYOUT_MIN_WIDTH = TREE_WIDTH + TREE_BORDER + CONTROL_COL_WIDTH + LAYOUT_GUTTER + HELP_COL_MIN


def is_wide(width: int) -> bool:
    """The ONE place a terminal width becomes a wide/narrow layout decision -- `app.py`'s own
    resize handler and every pane's `compose()` call this, never re-deriving the comparison."""
    return width >= WIDE_LAYOUT_MIN_WIDTH


def yield_help_items(items: "list[tuple]"):
    """`items` is a list of `(value, css_class, prefix)` triples -- exactly `elucidation_widgets`'
    own positional shape, collected instead of yielded inline so a pane can render them ALL
    together in its own separately-scrollable help column instead of interleaved among its
    controls. The SAME renderer (`elucidation_widgets`) is still the one thing that turns a value
    into widgets -- this function only changes WHERE (which container) that happens, never HOW."""
    for value, css_class, prefix in items:
        yield from elucidation_widgets(value, css_class, prefix=prefix)
