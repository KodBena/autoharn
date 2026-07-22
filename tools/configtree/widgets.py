#!/usr/bin/env python3
"""tools/configtree/widgets.py -- the real Textual widgets a `SectionSpec`'s fields render as
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2): `Input` for text, `RadioSet` for a closed
choice, `Checkbox` for a boolean, and a scrollable row list + modal sub-form for a `ListField`.
No autoharn vocabulary here -- this module only knows the four field shapes `fields.py`
declares."""
from __future__ import annotations

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
    """One field spec + its current value -> the live widget instance."""
    wid = field_widget_id(f.name)
    if isinstance(f, TextField):
        return Input(value=str(value), placeholder=str(f.label), password=f.password, id=wid)
    if isinstance(f, ChoiceField):
        buttons = [RadioButton(label, value=(val == value)) for val, label in f.options]
        radio = RadioSet(*buttons, id=wid)
        return radio
    if isinstance(f, ConfirmField):
        return Checkbox(str(f.label), value=bool(value), id=wid)
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
    line (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3: 'a refusal renders inline on the form')."""

    def __init__(self, text: str = "") -> None:
        super().__init__(text, classes="ct-field-error")

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
            yield Label(self._title, id="ct-modal-title")
            for f in self._item_fields:
                yield Label(str(f.label))
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
    """The `ListField` renderer: an already-added-rows `ListView` plus Add/Remove buttons. Rows
    live in `self.rows` (`list[dict]`, insertion order) -- the section pane reads this back at
    submit time via `.rows`, exactly like `read_field_value` reads any other widget's value."""

    def __init__(self, spec: ListField, initial: list[dict] | None = None) -> None:
        super().__init__(id=field_widget_id(spec.name))
        self.spec = spec
        self.rows: list[dict] = list(initial or [])

    def compose(self) -> ComposeResult:
        yield Label(str(self.spec.label))
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
            lv.append(ListItem(Label(self.spec.summarize(row))))

    def add_row(self, row: dict) -> None:
        self.rows.append(row)
        self._refresh()

    def remove_selected(self) -> None:
        lv = self.query_one(f"#{self.id}-list", ListView)
        idx = lv.index
        if idx is not None and 0 <= idx < len(self.rows):
            del self.rows[idx]
            self._refresh()

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
