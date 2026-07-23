#!/usr/bin/env python3
"""tools/configtree/layout_primitives.py -- `ContentVertical`/`ContentHorizontal`, the ONE typed
layout primitive every "this holds a variable amount of content, size to it" container in this
package must use in place of a raw `textual.containers.Vertical`/`Horizontal` instantiation in a
content path (ledger row 1139, TYPE half).

THE CLASS (row 1139's own conviction): a raw Textual `Vertical`/`Horizontal` DEFAULT_CSS is
`height: 1fr` -- an EQUAL FRACTIONAL SHARE of whatever ancestor eventually resolves it, computed
independent of how much content the container actually holds. Nested inside another container
that is itself `height: auto` (sized FROM its own children), an `1fr` child creates exactly the
circular claim this project has now patched locally three times without ever naming it: round-5
overlap, cycle-3 starvation, and this round's own reproduction (a single competence's own detail
row -- one Static + one Remove button, one real line of content -- rendered inside an unclassed
`Horizontal()` in `widgets_master_detail.MasterDetailFieldWidget.compose`, which Textual gave a
virtual height of 42 rows, pushing the Relation/Role-charter sub-lists and their own Add buttons
below a blank region the operator had to scroll through to reach -- see this package's own
`layout_split.py` sibling docstring and git history for the fuller account, and ledger row 1139
for the maintainer's own conviction of the class). `.ct-field-group`/`.ct-md-block`/`.ct-md-row`
each already carry a HAND-ADDED `height: auto` CSS override in `app.py`'s own stylesheet -- proof
the class was recognized locally, twice, without ever becoming a construction-time guarantee: a
freshly written, unclassed container (this round's own culprit) silently inherits the library
DEFAULT, and the default is exactly the hazard.

`ContentVertical`/`ContentHorizontal` fix this BY CONSTRUCTION, not by convention: `DEFAULT_CSS`
sets `height: auto` at the CLASS level, so every instance is auto-sized the moment it is used --
no caller-remembered CSS class required, and no possibility of a bare, freshly-added container
ever reproducing this class again. Every content-path container in this package (a field's own
widget-group shell, a button row, a nested detail block, a modal's own button row) is built from
one of these two, never from `textual.containers.Vertical`/`Horizontal` directly --
`gates/setup_tui_purity_gate.py` REFUSES a raw instantiation of either outside its own small,
individually-justified, ENUMERATED exception list (the genuinely fr-intended shells: the
top-level split columns and the independently-scrollable column/section-body/modal-body scroll
regions -- see that gate's own `LAYOUT_EXCEPTIONS` for the full, named list and the rationale for
each).

`VerticalScroll` is deliberately NOT wrapped here: every current use of it in this package IS one
of those declared fr-intended scroll shells (a `VerticalScroll` earns its own height from its
enclosing layout and scrolls its own overflow -- that is its whole point, unlike a `Vertical`/
`Horizontal` used only to GROUP a fixed amount of sibling content). A future `VerticalScroll`
used as a plain content grouper (not a scroll region) would be the same class again -- the gate's
own enumeration is where that judgment call is made explicit, not silently defaulted.

Lazy imports are banned."""
from __future__ import annotations

from textual.containers import Horizontal, Vertical


class ContentVertical(Vertical):
    """A `Vertical` that sizes to its own content by construction (`height: auto`), never an
    equal `1fr` share of its parent regardless of how much it actually holds. Use this for any
    content-path vertical grouping (a field's own widget-group shell, a nested detail block) --
    never a bare `Vertical(...)` (see this module's own docstring for the reproduced hazard)."""

    DEFAULT_CSS = """
    ContentVertical {
        height: auto;
    }
    """


class ContentHorizontal(Horizontal):
    """A `Horizontal` that sizes to its own content by construction (`height: auto`) -- the
    row-shaped sibling of `ContentVertical` above, for a button row or a one-line detail row
    (item + its own Remove button) that must NEVER claim a fractional share of whatever ancestor
    eventually resolves it. This module's own docstring has the exact reproduction this class
    exists to make unrepresentable: a bare `Horizontal()` wrapping one competence's detail row
    was handed a virtual height of 42 by Textual's own `1fr` default, nested inside an
    otherwise-`height: auto` chain."""

    DEFAULT_CSS = """
    ContentHorizontal {
        height: auto;
    }
    """
