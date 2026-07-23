#!/usr/bin/env python3
"""tools/configtree/widgets_choice_filter.py -- `ChoiceFieldWidget`, split into its own file
(ADR-0007 / `gates/max_lines.py`: `widgets.py` was already at 385 lines, no baseline headroom to
grow past 400 -- a new, composed file rather than a ratchet).

Extends `widget_primitives.build_field_widget`'s bare `RadioSet` rendering with the SAME
filter-above-threshold idiom `MultiChoiceFieldWidget` already has for checkbox catalogs
(`filter_threshold.FILTER_THRESHOLD`) -- cycle-2 AUDIT.md MINOR finding #3: "the
competence/relation/charter principal pickers are ChoiceFields with no equivalent of
MULTICHOICE_FILTER_THRESHOLD ... a growing principal roster renders as an ever-longer unfiltered
RadioSet."

SAME widget id contract as the bare `RadioSet` this replaces (`field_widget_id(f.name)`) -- so
`panes.SectionPane`/`actions.ActionPane`'s own `_find_field`/`on_radio_set_changed`, and
`item_modal.AddItemModal`'s own `query_one(f"#{field_widget_id(f.name)}")` Save-time read, need NO
change: a Textual CSS id selector matches anywhere in the queried subtree regardless of nesting
depth, so wrapping the SAME RadioSet inside this new container changes nothing any existing caller
depends on. `build_choice_or_plain_widget` (this module's own ONE call site every non-group field
now routes through, cycle-3 fix round, `item_modal.render_item_field`) is what makes the modal's
own ChoiceField -- the audit's exact named scenario, an 11-principal Relation object picker --
get this filter for the first time."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Input, RadioButton, RadioSet, Static

from tools.configtree.fields import ChoiceField
from tools.configtree.filter_threshold import FILTER_THRESHOLD
from tools.configtree.layout_primitives import ContentVertical
from tools.configtree.widget_primitives import build_field_widget, field_widget_id


class ChoiceFieldWidget(ContentVertical):
    """See this module's own docstring. `f`/`value` mirror `widgets.build_field_widget`'s own
    `ChoiceField` branch exactly -- this class is what that branch now returns once
    `len(f.options) > FILTER_THRESHOLD`, instead of a bare `RadioSet`.

    IMPLEMENTATION NOTE (same discipline as `widgets.MultiChoiceFieldWidget`'s own docstring):
    filtering toggles each `RadioButton`'s own `.display`, never a `recompose()` -- a fresh
    `RadioSet`/`Input` pair rebuilt mid-keystroke is exactly the hazard that docstring documents
    reproducing (lost characters on rapid typing); every widget here is built ONCE, in `compose`,
    and kept alive for the field's whole lifetime."""

    def __init__(self, f: ChoiceField, value: object) -> None:
        super().__init__(id=f"{field_widget_id(f.name)}-wrap", classes="ct-field-group")
        self.f = f
        self.value = value
        self._buttons: dict[str, RadioButton] = {}
        self._labels: dict[str, str] = {}
        self._no_match_static: "Static | None" = None
        self._filter_text = ""

    @property
    def _filter_id(self) -> str:
        return f"{self.id}-filter"

    def compose(self) -> ComposeResult:
        yield Input(placeholder=f"Filter {self.f.label}...", id=self._filter_id,
                    classes="ct-choice-filter")
        self._buttons = {}
        self._labels = {}
        buttons = []
        for val, label in self.f.options:
            self._labels[val] = label
            rb = RadioButton(label, value=(val == self.value))
            self._buttons[val] = rb
            buttons.append(rb)
        yield RadioSet(*buttons, id=field_widget_id(self.f.name), classes="ct-choice-field")
        self._no_match_static = Static("", classes="ct-filter-no-match")
        self._no_match_static.display = False
        yield self._no_match_static

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != self._filter_id:
            return
        event.stop()  # this Input is the filter box, never a section field -- never bubble it
        self._filter_text = event.value
        self._apply_filter()

    def _apply_filter(self) -> None:
        needle = self._filter_text.strip().lower()
        shown = 0
        for val, rb in self._buttons.items():
            label = self._labels[val]
            matches = not needle or needle in label.lower() or needle in val.lower()
            rb.display = matches
            if matches:
                shown += 1
        if self._no_match_static is not None:
            self._no_match_static.update(f"no option matches {self._filter_text!r}" if needle else "")
            self._no_match_static.display = bool(needle) and shown == 0


def build_choice_or_plain_widget(f, value: object):
    """`ChoiceField` above `FILTER_THRESHOLD` gets `ChoiceFieldWidget`'s own filtering wrapper
    (MINOR audit finding #3, cycle-2 AUDIT.md); every other field kind (and a short `ChoiceField`)
    renders exactly as `widgets.build_field_widget` always has. The ONE call site
    `panes.SectionPane` and `actions.ActionPane` both route their non-group fields through, so the
    two panes can never disagree about when a `ChoiceField` gets the filter."""
    if isinstance(f, ChoiceField) and len(f.options) > FILTER_THRESHOLD:
        return ChoiceFieldWidget(f, value)
    return build_field_widget(f, value)
