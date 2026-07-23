#!/usr/bin/env python3
"""tools/configtree/item_modal.py -- `AddItemModal`, the sub-form a `ListField`'s (or a
`MasterDetailField`'s master/`DetailListField`'s) "Add" button opens, built from `item_fields`.

CYCLE-3 FIX ROUND (ledger row 1136's two MAJOR findings, `/home/bork/autoharn_series/cycle-3/
AUDIT.md`):

  1. `AddItemModal.compose` used to call `widgets.build_field_widget` directly, bypassing
     `widgets_choice_filter.build_choice_or_plain_widget` entirely -- every ChoiceField inside
     ANY Add-item modal was permanently excluded from the over-threshold RadioSet filter, no
     matter how many options it had, even though (post the cycle-2 master-detail restructure)
     EVERY real-world large ChoiceField in this app lives inside a modal (the audit's own named
     scenario: an 11-principal roster's Relation add-modal "object" picker).
  2. `AddItemModal.compose` rendered `Label` + widget + `FieldError` only -- it never called
     `elucidation_widgets`, so a field's own `help` and a `ChoiceField`'s own `option_help` (the
     descriptive sentences round 5/ledger row 1115 fought to have rendered "within measure," not
     deleted) were silently absent for every field inside a modal, a recurrence of that exact
     censured class via a different code path.

ROOT CAUSE (both, one site): `AddItemModal`'s own per-field rendering was a SEPARATE, hand-
copied loop from `panes.SectionPane`'s (ADR-0012 P1: "never a second implementation") -- the two
drifted the moment one of them changed and the other didn't. FIXED structurally, not
patched per-symptom: `render_item_field` below is the ONE per-field renderer (label -> widget,
routed through the SAME `build_choice_or_plain_widget` filter-threshold logic, plus `help`/
`option_help` elucidation) -- both `AddItemModal.compose` here AND `panes.SectionPane.compose`
call it for every non-group field, so the two can never drift again: there is only one function
to change.

MODAL OVERFLOW (a hazard found IN REACH of this same fix, cycle-3 fix round TASK 1's own
reproduction matrix): adding real elucidation content to every modal field makes a modal
TALLER -- `ct-modal-body` used to be a bare `Vertical` (no scroll), so a modal whose content now
exceeds the screen's height would push its own Save/Cancel buttons off-screen with NO way to
reach them (worse than `panes.py`'s own squeezed-`VerticalScroll` hazard, this fix round's
OTHER finding: THAT one is at least scrollable). `ct-modal-body` is now a `VerticalScroll` --
the same "never silently unreachable" discipline every other scrollable region in this library
already has (`panes.SectionPane`'s own `.ct-section-body`, `MultiChoiceFieldWidget`'s implicit
reliance on its own enclosing scroll)."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from tools.configtree.fields import ChoiceField, TextField
from tools.configtree.layout_primitives import ContentHorizontal
from tools.configtree.widget_primitives import FieldError, elucidation_widgets, field_widget_id, read_field_value
from tools.configtree.widgets_choice_filter import build_choice_or_plain_widget


def render_item_field(f, value: object, *, help_sink: "list | None" = None,
                       suppress_help: bool = False):
    """The ONE per-field renderer for a NON-group field (`TextField`/`ChoiceField` -- the only two
    kinds `ListField.item_fields`/a top-level section's own non-group fields ever carry): its
    label, its live widget (routed through `build_choice_or_plain_widget`, so a `ChoiceField`
    above `filter_threshold.FILTER_THRESHOLD` gets the SAME filter Input a top-level section's
    ChoiceField would), its own `help` elucidation, and -- for a `ChoiceField` -- each option's own
    `option_help` elucidation. Used by BOTH `AddItemModal.compose` (below) and
    `panes.SectionPane.compose`/`actions.ActionPane.compose` for their non-group fields -- the
    drift this fix answers becomes unrepresentable because there is only one function to call.

    CONTROL/HELP SPLIT (ledger row 1138): `AddItemModal` never passes either new keyword (a modal
    is always its own single, self-contained column, no side help region to divert into), so its
    own behavior is byte-for-byte unchanged. A `SectionPane`/`ActionPane` rendering the WIDE
    layout passes `help_sink` (a list this function APPENDS `(value, css_class, prefix)` triples
    to, `layout_split.yield_help_items`'s own shape, instead of yielding widgets here) so the
    label+widget stay in the compact control column while the prose renders in the separate help
    column. One rendering the NARROW, on-demand-disclosure-collapsed layout passes
    `suppress_help=True` instead -- the prose is not shown ANYWHERE in that state (an operator
    toggles it back with the `F1`/"Help" footer binding, `app.action_toggle_help`), never
    silently reproduced inline the old way."""
    yield Static(str(f.label), classes="ct-field-label")
    yield build_choice_or_plain_widget(f, value)
    if suppress_help:
        return
    if help_sink is not None:
        help_sink.append((getattr(f, "help", None), "ct-field-help", None))
        if isinstance(f, ChoiceField) and f.option_help:
            for opt_value, _ in f.options:
                help_sink.append((f.option_help.get(opt_value), "ct-choice-help", opt_value))
        return
    yield from elucidation_widgets(getattr(f, "help", None), "ct-field-help")
    if isinstance(f, ChoiceField) and f.option_help:
        for opt_value, _ in f.options:
            yield from elucidation_widgets(f.option_help.get(opt_value), "ct-choice-help",
                                            prefix=opt_value)


class AddItemModal(ModalScreen[dict | None]):
    """The sub-form a `ListField`'s "Add" button opens -- built from `item_fields`, exactly the
    same widget vocabulary (via `render_item_field`) as a top-level section's own non-group
    fields. Dismisses with the collected `{name: value}` dict on Save, or `None` on Cancel/Escape
    (never reads back a partial row)."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, item_fields: tuple) -> None:
        super().__init__()
        self._title = title
        self._item_fields = item_fields
        self._errors: dict[str, FieldError] = {}

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="ct-modal-body"):
            yield Label(self._title, id="ct-modal-title", classes="ct-section-title")
            for f in self._item_fields:
                yield from render_item_field(f, f.default if hasattr(f, "default") else "")
                err = FieldError()
                self._errors[str(f.name)] = err
                yield err
            # LATENT ROW-1139 SITE #2 (cycle-6 fix round): this was a bare `Horizontal(id=
            # "ct-modal-buttons")` with NO CSS anywhere for that id -- Textual's own default
            # `height: 1fr` handed it the whole remaining `ct-modal-body` scroll region (measured:
            # a 251x61 run gave it height=31, filling straight to the bottom of the screen).
            # Harmless today only because it happens to be the LAST child (nothing renders below
            # it to be pushed down) -- but it still inflated the modal's own scrollable virtual
            # size well past its real content, the SAME class this round's invariant is built to
            # catch regardless of whether a sibling was visibly pushed. `ContentHorizontal` closes
            # it the same way as every other site.
            with ContentHorizontal(id="ct-modal-buttons"):
                yield Button("Save", id="ct-modal-save", variant="primary")
                yield Button("Cancel", id="ct-modal-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ct-modal-cancel":
            self.dismiss(None)
            return
        if event.button.id == "ct-modal-save":
            row: dict[str, object] = {}
            valid = True
            for f in self._item_fields:
                widget = self.query_one(f"#{field_widget_id(f.name)}")
                val = read_field_value(f, widget)
                err_msg = None
                if isinstance(f, TextField):
                    if f.required and not str(val).strip():
                        err_msg = "required"
                    elif f.validator is not None:
                        err_msg = f.validator(str(val))
                elif isinstance(f, ChoiceField) and val is None:
                    err_msg = "choose one"
                self._errors[str(f.name)].set_text(err_msg or "")
                if err_msg:
                    valid = False
                row[str(f.name)] = val
            if valid:
                self.dismiss(row)

    def action_cancel(self) -> None:
        self.dismiss(None)
