#!/usr/bin/env python3
"""tools/configtree/widgets.py -- the real Textual widgets a `SectionSpec`'s fields render as
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2): `Input` for text, `RadioSet` for a closed
choice, `Checkbox` for a boolean, and a scrollable row list + modal sub-form for a `ListField`.
No autoharn vocabulary here -- this module only knows the four field shapes `fields.py`
declares."""
from __future__ import annotations

from typing import Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, ListItem, ListView, RadioButton, RadioSet, Static

from tools.configtree.fields import ChoiceField, ConfirmField, ListField, TextField

FIELD_ID_PREFIX = "ct-field-"


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


class AddItemModal(ModalScreen[dict | None]):
    """The sub-form a `ListField`'s "Add" button opens -- built from `item_fields`, exactly the
    same widget vocabulary as a top-level section. Dismisses with the collected `{name: value}`
    dict on Save, or `None` on Cancel/Escape (never reads back a partial row)."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, item_fields: tuple) -> None:
        super().__init__()
        self._title = title
        self._item_fields = item_fields
        self._errors: dict[str, FieldError] = {}

    def compose(self) -> ComposeResult:
        with Vertical(id="ct-modal-body"):
            yield Label(self._title, id="ct-modal-title", classes="ct-section-title")
            for f in self._item_fields:
                yield Label(str(f.label), classes="ct-field-label")
                yield build_field_widget(f, f.default if hasattr(f, "default") else "")
                err = FieldError()
                self._errors[str(f.name)] = err
                yield err
            with Horizontal(id="ct-modal-buttons"):
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


class ListFieldWidget(Vertical):
    """The `ListField` renderer: an already-added-rows `ListView` plus Add/Remove buttons -- the
    repeatable-row equivalent of a Qt list-editor's own +/- controls, not a save/apply ceremony
    (there is nothing to "save": each Add/Remove writes `self.rows` immediately, live, and
    `on_change` -- if given -- fires right after so the owning `SectionPane` can mirror the same
    list into the shared state on the spot, matching every other field's live-write contract).
    Rows live in `self.rows` (`list[dict]`, insertion order)."""

    def __init__(self, spec: ListField, initial: list[dict] | None = None,
                 on_change: "Callable[[], None] | None" = None) -> None:
        super().__init__(id=field_widget_id(spec.name))
        self.spec = spec
        self.rows: list[dict] = list(initial or [])
        self._on_change = on_change

    def compose(self) -> ComposeResult:
        yield Label(str(self.spec.label), classes="ct-field-label")
        yield ListView(id=f"{self.id}-list")
        with Horizontal():
            yield Button(f"Add {self.spec.label}", id=f"{self.id}-add")
            yield Button("Remove selected", id=f"{self.id}-remove")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        lv = self.query_one(f"#{self.id}-list", ListView)
        lv.clear()
        for row in self.rows:
            lv.append(ListItem(Label(self.spec.summarize(row), classes="ct-info-line")))

    def add_row(self, row: dict) -> None:
        self.rows.append(row)
        self._refresh()
        if self._on_change is not None:
            self._on_change()

    def remove_selected(self) -> None:
        lv = self.query_one(f"#{self.id}-list", ListView)
        idx = lv.index
        if idx is not None and 0 <= idx < len(self.rows):
            del self.rows[idx]
            self._refresh()
            if self._on_change is not None:
                self._on_change()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handled here, not by the enclosing `SectionPane` -- `event.stop()` keeps it from also
        being read as a Save press (Textual bubbles an unstopped message to every ancestor,
        `SectionPane.on_button_pressed` included, and neither `ct-save`'s id would match here,
        but stopping keeps the two handlers' concerns cleanly separated)."""
        if event.button.id == f"{self.id}-add":
            event.stop()

            def _on_result(row: "dict | None") -> None:
                if row is not None:
                    self.add_row(row)

            self.app.push_screen(AddItemModal(f"Add: {self.spec.label}", self.spec.item_fields),
                                  _on_result)
        elif event.button.id == f"{self.id}-remove":
            event.stop()
            self.remove_selected()
