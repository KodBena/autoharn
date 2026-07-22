#!/usr/bin/env python3
"""tools/configtree/widgets.py -- the real Textual widgets a `SectionSpec`'s fields render as
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2): a scrollable row list + modal sub-form for a
`ListField`, and a checkbox GROUP for a `MultiChoiceField`. No autoharn vocabulary here -- this
module only knows the four field shapes `fields.py` declares.

The bare per-field-kind primitives (`Input`/`RadioSet`/`Checkbox` builders, `elucidation_widgets`,
`FieldError`) moved to `widget_primitives.py`, and `AddItemModal` moved to `item_modal.py` (cycle-3
fix round, ledger row 1136 -- see `item_modal.py`'s own docstring for the full account of why:
`AddItemModal` needs `widgets_choice_filter.build_choice_or_plain_widget`, which itself needs the
primitives, so `AddItemModal` could not stay in the SAME file as the primitives without those two
new modules importing each other)."""
from __future__ import annotations

from typing import Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, Label, ListItem, ListView, Static

from tools.configtree.fields import ListField, MultiChoiceField
from tools.configtree.filter_threshold import FILTER_THRESHOLD
from tools.configtree.item_modal import AddItemModal
# `FieldError`/`build_field_widget`/`read_field_value` are RE-EXPORTED here (not used by this
# file's own two widget classes) -- same "historical alias" discipline as `MULTICHOICE_FILTER_
# THRESHOLD` below: `tools.configtree.widgets` was these primitives' home before the cycle-3 fix
# round split them into `widget_primitives.py`, and at least one existing fixture (`seen-red/
# setup-tui-seeded-value-visibility`) `exec`s a HISTORICAL `panes.py` source straight from git
# history against the live `tools.configtree.widgets` module (its own RED leg) -- that historical
# source's own `from tools.configtree.widgets import FieldError, ...` must keep resolving.
from tools.configtree.widget_primitives import (FieldError, build_field_widget,
                                                 elucidation_widgets, field_widget_id,
                                                 read_field_value)


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
# 36-checkbox catalog renders as one unbroken scroll"). The actual numeric bar now lives in
# `filter_threshold.py` (cycle-2 fix round: `ChoiceFieldWidget`, in `widgets_choice_filter.py`,
# reuses the SAME constant for its own RadioSet filter -- one home for the number, not two
# hand-kept copies) -- this name is kept as the historical alias every existing caller/fixture
# already imports (`from tools.configtree.widgets import MULTICHOICE_FILTER_THRESHOLD`).
MULTICHOICE_FILTER_THRESHOLD = FILTER_THRESHOLD


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
        # DISTINCT CLASS FROM `ct-blocked-reason` (MINOR audit finding #4, cycle-2 AUDIT.md: "the
        # CSS class ct-blocked-reason doubles as the MultiChoiceFieldWidget's own 'no filter
        # match' message class" -- two semantically distinct signals, section-blocked vs.
        # filter-no-match, sharing one selector name). `ct-filter-no-match` is its own class,
        # styled identically (`app.py`'s own CSS) but never confusable in a stylesheet/DOM query
        # with a genuinely BLOCKED section's banner.
        self._no_match_static = Static("", id=f"{self.id}-no-match", classes="ct-filter-no-match")
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
