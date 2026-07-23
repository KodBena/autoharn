#!/usr/bin/env python3
"""tools/configtree/widget_primitives.py -- the field-kind-agnostic widget PRIMITIVES every
other widget module in this package builds on: `elucidation_widgets` (the ONE renderer for a
`fields.ElucidationValue`), `field_widget_id`/`build_field_widget`/`read_field_value` (the
name<->widget-id mapping and the bare per-field-kind widget builder), and `FieldError` (the one
inline validation-error line).

SPLIT OUT OF `widgets.py` (cycle-3 fix round, ledger row 1136's own MAJOR findings #1/#2):
`widgets.py` (home of `ListFieldWidget`/`MultiChoiceFieldWidget`, both of which use
`AddItemModal`) and `item_modal.py` (home of `AddItemModal`, which needs
`widgets_choice_filter.build_choice_or_plain_widget` -- itself built on `build_field_widget`)
would otherwise import each other -- a two-way cycle. This module sits BELOW both: no
`tools.configtree` sibling except `fields.py` (the field-kind dataclasses themselves), so
`widgets.py`, `widgets_choice_filter.py`, and `item_modal.py` can all import from here with no
cycle anywhere in the graph. No autoharn vocabulary here -- this module only knows the four
field shapes `fields.py` declares, same discipline as its former home."""
from __future__ import annotations

from textual.widgets import Checkbox, Input, RadioButton, RadioSet, Static

from tools.configtree.fields import (ChoiceField, ConfirmField, DescriptionElement,
                                      ElucidationHeading, ElucidationValue, TextField)

FIELD_ID_PREFIX = "ct-field-"


def elucidation_widgets(value: "ElucidationValue | None", css_class: str, *,
                         prefix: "str | None" = None):
    """The ONE renderer for `fields.ElucidationValue` (round 7, ledger row 1119, following the
    Fable RCA consult, design/CONSULT-FABLE-ELUCIDATION-RCA-2026-07-22.md): a plain string renders
    as ONE capped, UNLABELED `Static` -- ordinary connective prose (D7/D8). A tuple's own items
    render per kind, each its own capped `Static`, never concatenated into one paragraph:
      - a bare `str` item -- unlabeled connective prose, exactly like the plain-string case (the
        LEAD content of a multi-item value: what choosing this costs/requires/changes, D7);
      - a `DescriptionElement` -- a short, closed-vocabulary LABELED line ("Label: text"), never
        a per-component telegraphy vocabulary (D9's own "serialization masquerading as layout");
      - an `ElucidationHeading` -- a real, unprefixed sub-heading (`.ct-elucidation-heading`)
        breaking a multi-group value into named parts (D9: never a repeated line-prefix hack).
    `prefix`, if given (a `ChoiceField`'s own option VALUE -- its `option_help` entries render
    together, disambiguated by option, under one `RadioSet` rather than next to individual
    buttons the way `MultiChoiceFieldWidget` can), is prepended to a bare-str/DescriptionElement
    line so the operator can tell which option it belongs to; a heading is never prefixed (a
    heading names ITS OWN group, prefixing it with an unrelated option value would misname it)."""
    if value is None:
        return
    if isinstance(value, str):
        text = f"{prefix}: {value}" if prefix else value
        yield Static(text, classes=css_class, markup=False)
        return
    for item in value:
        if isinstance(item, ElucidationHeading):
            yield Static(item.text, classes="ct-elucidation-heading")
        elif isinstance(item, DescriptionElement):
            label = f"{prefix} -- {item.label}" if prefix else item.label
            yield Static(f"{label}: {item.text}", classes=css_class, markup=False)
        else:  # bare str -- unlabeled connective prose, its own line
            text = f"{prefix}: {item}" if prefix else item
            yield Static(text, classes=css_class, markup=False)


def field_widget_id(name: object) -> str:
    """`name` is a `fields.FieldName` (or a plain str at a caller that has not gone through a
    field spec yet) -- `str(name)` is the SAME text either way (`FieldName.__str__` returns its
    checked `.value`), so this is the ONE place a field name becomes a widget-id string."""
    return f"{FIELD_ID_PREFIX}{name}"


def build_field_widget(f, value: object):
    """One field spec + its current value -> the live widget instance.

    MEASURE (maintainer round 4, `measure.py`'s own docstring has the full account): a
    `Checkbox`/`RadioButton` (both `ToggleButton` subclasses) do NOT wrap their own caption text
    at all, verified empirically -- given a long string they render it as one line, sized to full
    content width, straight past any container cap. `ConfirmField`'s label is therefore NEVER
    passed to `Checkbox` as its own caption (an empty string instead) -- the section's own
    preceding `Static(str(f.label), classes="ct-field-label")` (panes.py's own per-field loop) is
    the ONE place that label renders, and IT wraps correctly under the CSS measure cap. `RadioSet`
    gets `classes="ct-choice-field"` so its own container -- and by inheritance its RadioButton
    children -- is bounded by the same cap even though a bounded-but-unwrapped RadioButton label
    is a lesser, defense-in-depth case (no current option string is long; kept honest for the
    next one)."""
    wid = field_widget_id(f.name)
    if isinstance(f, TextField):
        return Input(value=str(value), placeholder=str(f.label), password=f.password, id=wid)
    if isinstance(f, ChoiceField):
        buttons = [RadioButton(label, value=(val == value)) for val, label in f.options]
        return RadioSet(*buttons, id=wid, classes="ct-choice-field")
    if isinstance(f, ConfirmField):
        return Checkbox("", value=bool(value), id=wid)
    raise TypeError(f"build_field_widget: unsupported field type {type(f).__name__}")


def read_field_value(f, widget) -> object:
    if isinstance(f, TextField):
        return widget.value
    if isinstance(f, ChoiceField):
        idx = widget.pressed_index
        if idx is None or idx < 0:
            return None
        return f.options[idx][0]
    if isinstance(f, ConfirmField):
        return widget.value
    raise TypeError(f"read_field_value: unsupported field type {type(f).__name__}")


class FieldError(Static):
    """One inline validation-error line, rendered directly under its field -- never a scrollback
    line (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3: 'a refusal renders inline on the form').
    `markup=False`: a validator's own message is free-form text that may legitimately contain
    Rich-markup-shaped substrings (e.g. a regex character class like `[A-Za-z0-9_]+` in a
    "must match ..." message) -- interpreting it as markup would silently eat the brackets
    instead of showing the operator the real message."""

    def __init__(self, text: str = "") -> None:
        super().__init__(text, classes="ct-field-error", markup=False)

    def set_text(self, text: str) -> None:
        self.update(text)
        self.display = bool(text)
