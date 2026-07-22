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

from tools.configtree.fields import (ChoiceField, ConfirmField, DescriptionElement,
                                      ElucidationHeading, ElucidationValue, ListField,
                                      MultiChoiceField, TextField)

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
        super().__init__(id=field_widget_id(spec.name), classes="ct-field-group")
        self.spec = spec
        self.rows: list[dict] = list(initial or [])
        self._on_change = on_change

    def compose(self) -> ComposeResult:
        yield Label(str(self.spec.label), classes="ct-field-label")
        yield from elucidation_widgets(self.spec.help, "ct-field-help")
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

            self.app.push_screen(AddItemModal(f"Add {self.spec.label}", self.spec.item_fields),
                                  _on_result)
        elif event.button.id == f"{self.id}-remove":
            event.stop()
            self.remove_selected()


# FILTER THRESHOLD (MEDIUM audit finding, ledger row 1130's own sibling audit: "hydration's
# 36-checkbox catalog renders as one unbroken scroll"). Named, not inlined, so the rationale
# lives in exactly one place: Miller (1968)/Nielsen's own working-set heuristic puts a single
# glanceable list at roughly 7 (+-2) items (the SAME pedigree ADR-0019's C7/C28 already cite) --
# past that, a catalog stops being a single glance and becomes a search task, the point at which
# a filter earns its own keep (VS Code settings search / Group Policy editor idiom: the filter
# Input appears only once the list is long enough to need one, never above a short list where it
# would be one more control for nothing).
MULTICHOICE_FILTER_THRESHOLD = 9


class MultiChoiceFieldWidget(Vertical):
    """The `MultiChoiceField` renderer -- a checkbox GROUP, one `Checkbox` per catalog option,
    each option's own `option_help` (if any) rendered as its own capped `.ct-choice-help` line
    directly under it (the "juxtaposed text" tooltip-equivalent this terminal offers, maintainer
    round 5, ledger row 1115) -- never a free-text delimited string over a closed vocabulary.
    Mirrors `ListFieldWidget`'s own self-contained shape (composes itself, fires `on_change`) so
    the enclosing `SectionPane` wires it the SAME way; `self.selected` is always `list[str]`, in
    catalog order, the model value `panes.py`'s write-through stores verbatim.

    GROUPING + FILTER (MEDIUM audit finding, ledger row 1130's own sibling audit: "hydration's
    36-checkbox catalog renders as one ~218-row unbroken scroll"). `spec.groups`, if given,
    renders a real `ElucidationHeading` (the SAME sub-heading machinery `substrate`'s
    Existing-db/Dedicated-db groups already use) before each contiguous run of options sharing
    one heading. Past `MULTICHOICE_FILTER_THRESHOLD` options, a live filter `Input` appears above
    the catalog -- typing narrows the VISIBLE rows to those whose label or value contains the
    typed text (case-insensitive); clearing it restores every option.

    IMPLEMENTATION NOTE (verified empirically, the hard way): filtering toggles each row's own
    `.display` -- it does NOT `recompose()`. An earlier draft rebuilt the whole widget (Checkbox
    + Input included) via `recompose()` on every keystroke; Textual's own `Input.Changed` firing
    during that VERY recompose (the freshly-built Input re-validates itself on mount) fed back
    into this same handler, and re-focusing the brand-new Input instance after each rebuild could
    not reliably outrun the operator's own next keystroke -- rapid typing lost every character
    after the first. Every Checkbox/heading/help widget is instead built ONCE, in `compose`, and
    kept alive for the field's whole lifetime; a checked box that the filter hides stays checked
    (its own `Checkbox.value` never changes, only `.display`), and a heading shows/hides based on
    whether ANY option under it is currently visible."""

    def __init__(self, spec: MultiChoiceField, initial: "list[str] | None" = None,
                 on_change: "Callable[[], None] | None" = None) -> None:
        super().__init__(id=field_widget_id(spec.name), classes="ct-field-group")
        self.spec = spec
        self.selected: list[str] = list(initial or [])
        self._on_change = on_change
        self._boxes: dict[str, Checkbox] = {}
        self._labels: dict[str, str] = {}
        # Every widget belonging to ONE option (its checkbox + its own option_help lines),
        # keyed by option value -- toggled together as one unit when the filter narrows.
        self._option_widgets: dict[str, list] = {}
        # heading Static -> the option values it covers, so a heading shows iff at least one of
        # ITS OWN options is currently visible.
        self._heading_members: dict[object, list[str]] = {}
        self._heading_for_value: dict[str, object] = {}
        self._no_match_static: "Static | None" = None
        self._filter_text: str = ""

    @property
    def _filter_id(self) -> str:
        return f"{self.id}-filter"

    def compose(self) -> ComposeResult:
        yield Label(str(self.spec.label), classes="ct-field-label")
        yield from elucidation_widgets(self.spec.help, "ct-field-help")
        if len(self.spec.options) > MULTICHOICE_FILTER_THRESHOLD:
            yield Input(placeholder=f"Filter {self.spec.label}...", id=self._filter_id,
                        classes="ct-multichoice-filter")
        self._boxes = {}
        self._labels = {}
        self._option_widgets = {}
        self._heading_members = {}
        self._heading_for_value = {}
        groups = self.spec.groups or {}
        current_heading_widget = None
        current_heading_text = None
        for value, option_label in self.spec.options:
            self._labels[value] = option_label
            heading_text = groups.get(value)
            if heading_text is not None and heading_text != current_heading_text:
                heading_widget = Static(heading_text, classes="ct-elucidation-heading")
                yield heading_widget
                current_heading_widget = heading_widget
                current_heading_text = heading_text
                self._heading_members[heading_widget] = []
            if heading_text is not None and heading_text == current_heading_text:
                self._heading_members[current_heading_widget].append(value)
                self._heading_for_value[value] = current_heading_widget
            # `classes="ct-checkbox-compact"` (round 6, coordinator addendum): a bare `Checkbox`
            # defaults to `border: tall` (Textual's own `ToggleButton.DEFAULT_CSS`) -- a full
            # top+bottom rule around EVERY option; stacked across a catalog of a dozen-plus
            # entries this reads as a wall of borders, Textual's default styling doing charity
            # work nobody asked for. Slimmed via CSS (`app.py`'s own `.ct-checkbox-compact` rule)
            # to a single thin rule between entries, the Qt-idiom checklist look.
            cb = Checkbox(option_label, value=(value in self.selected),
                          id=f"{self.id}-opt-{value}", classes="ct-checkbox-compact")
            self._boxes[value] = cb
            yield cb
            widgets_for_value = [cb]
            for w in elucidation_widgets((self.spec.option_help or {}).get(value), "ct-choice-help"):
                yield w
                widgets_for_value.append(w)
            self._option_widgets[value] = widgets_for_value
        self._no_match_static = Static("", id=f"{self.id}-no-match", classes="ct-blocked-reason")
        self._no_match_static.display = False
        yield self._no_match_static

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        for value, cb in self._boxes.items():
            if cb is event.checkbox:
                event.stop()
                if event.value and value not in self.selected:
                    self.selected.append(value)
                elif not event.value and value in self.selected:
                    self.selected.remove(value)
                if self._on_change is not None:
                    self._on_change()
                return

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != self._filter_id:
            return
        event.stop()  # this Input is the filter box, never a section field -- never bubble it
        self._filter_text = event.value
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Toggles `.display` on every already-built row -- see this class's own docstring for
        why this is a toggle, never a `recompose()`. Fully synchronous: no keystroke can ever
        outrun it, because there is nothing here to await."""
        needle = self._filter_text.strip().lower()
        visible_headings: set = set()
        shown = 0
        for value, widgets in self._option_widgets.items():
            label = self._labels[value]
            matches = not needle or needle in label.lower() or needle in value.lower()
            for w in widgets:
                w.display = matches
            if matches:
                shown += 1
                heading = self._heading_for_value.get(value)
                if heading is not None:
                    visible_headings.add(heading)
        for heading_widget in self._heading_members:
            heading_widget.display = heading_widget in visible_headings
        if self._no_match_static is not None:
            self._no_match_static.update(f"no option matches {self._filter_text!r}" if needle else "")
            self._no_match_static.display = bool(needle) and shown == 0
