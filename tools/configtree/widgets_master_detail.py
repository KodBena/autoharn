#!/usr/bin/env python3
"""tools/configtree/widgets_master_detail.py -- `MasterDetailFieldWidget`, split into its own
file (ADR-0007: no file over 400 lines; `widgets.py` was already at 385 with no `gates/
max_lines.py` baseline entry -- growing it past 400 would be refused outright, so this is a new,
composed file rather than a ratchet).

The `MasterDetailField` renderer (ADR-0019 Rule 4; genre exemplar: Django/Rails admin inline
formsets, `master_detail.py`'s own module docstring) -- a detail row added from inside principal
X's own context can never appear under principal Y's (the link value is auto-injected from X's
own `master_key`, never re-picked by the operator; `master_detail.DetailListField`'s own
docstring, "LINK FIELD").

SELECTION (cycle-3 fix round, ledger row 1136's own maintainer bench sighting, relayed live:
"add a principal -> scroll down -> 1 principal visible; can't select it"). The PRE-fix widget
rendered every master row as a bare, unfocusable `Static` -- no click/keyboard affordance existed
AT ALL, so an operator's instinct to click a rendered row (the natural next step after seeing it
appear, and the same instinct a `ListView` row elsewhere in this same app rewards) was a genuine,
reproducible no-op: nothing highlighted, nothing changed, no error, no feedback of any kind. The
coordinator's own naming of the fix's genre (Django admin/Qt master-detail split view: "a master
list's rows are selectable, detail follows selection") is what this module now implements: each
master row is a real, focusable `Button` (clickable AND keyboard-Tab-reachable for free);
clicking one SELECTS it (a visible `>`/`  ` marker plus a `-selected` CSS class), and the nested
per-row detail lists (competences/relations/charters, each with its OWN label/help/Add button)
render ONCE, for the CURRENTLY SELECTED row only -- never simultaneously for every row (that was
the OTHER half of the maintainer's own complaint, relayed by the coordinator: "the master list is
buried under the pane's preamble... looks ugly that you have to [scroll]" -- the pre-fix widget
rendered SOME piece of detail-label/help prose 3 TIMES PER ROW, for every row, always, whether or
not the operator cared about that particular principal's competences at that moment). A newly
added master row is auto-selected (the natural next step after registering a principal is
usually to grant it something), and removing the currently-selected row clears the selection
(never leaves it pointing at a row that no longer exists).

Rebuilds via `recompose()` after every Add/Remove/Select (master or any detail) -- discrete
button presses, not per-keystroke typing (`widgets.MultiChoiceFieldWidget`'s own docstring
explains why a recompose is UNSAFE mid-keystroke; a button press has no such hazard, the SAME
reasoning `widgets.ListFieldWidget` already relies on for its own Add/Remove, which has never had
that problem)."""
from __future__ import annotations

from typing import Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from tools.configtree.item_modal import AddItemModal
from tools.configtree.master_detail import MasterDetailField
from tools.configtree.widget_primitives import elucidation_widgets, field_widget_id


class MasterDetailFieldWidget(Vertical):
    """See this module's own docstring. `initial_master`/`initial_details` seed this widget's own
    in-memory rows from the CURRENT shared state (read once, at construction -- the enclosing
    `SectionPane` rebuilds this widget fresh on every recompose, so there is no staleness risk).
    `self._selected_key` (a `spec.master_key(row)` value, never a positional index -- survives a
    remove-then-reorder without pointing at the wrong row) is seeded from `initial_selected_key`
    and reported on every change via `on_select_change` -- a bare instance attribute here would
    NOT survive `panes.SectionPane._make_md_master_change`'s own ALWAYS-recompose-the-whole-pane
    contract (its own docstring explains why), which destroys and rebuilds a fresh instance of
    THIS class on every master Add/Remove; `panes.SectionPane` is what actually persists across
    that rebuild (`__init__`'s own note there), so it is the one place selection survives, and it
    hands the current value back in on every reconstruction."""

    def __init__(self, spec: MasterDetailField, initial_master: "list[dict] | None" = None,
                 initial_details: "dict[str, list[dict]] | None" = None,
                 initial_selected_key: "str | None" = None,
                 on_master_change: "Callable[[list[dict]], None] | None" = None,
                 on_detail_change: "Callable[[str, list[dict]], None] | None" = None,
                 on_select_change: "Callable[[str | None], None] | None" = None) -> None:
        super().__init__(id=field_widget_id(spec.name), classes="ct-field-group")
        self.spec = spec
        self.master_rows: list[dict] = list(initial_master or [])
        self.detail_rows: dict[str, list[dict]] = {
            str(d.list_field.name): list((initial_details or {}).get(str(d.list_field.name), []))
            for d in spec.details
        }
        self._on_master_change = on_master_change
        self._on_detail_change = on_detail_change
        self._on_select_change = on_select_change
        # `initial_selected_key` -- the ENCLOSING `SectionPane`'s own remembered selection (this
        # widget's own docstring, "SELECTION": a bare instance attribute here does NOT survive a
        # master Add/Remove, which always rebuilds a fresh instance of THIS class -- the pane is
        # what persists, and hands the current selection back in on every (re)construction).
        self._selected_key: "str | None" = initial_selected_key

    def compose(self) -> ComposeResult:
        yield Static(str(self.spec.master.label), classes="ct-field-label")
        yield from elucidation_widgets(self.spec.master.help, "ct-field-help")
        yield from elucidation_widgets(self.spec.help, "ct-field-help")
        yield Button(f"Add {self.spec.master.label}", id=f"{self.id}-master-add")
        if not self.master_rows:
            yield Static("(none registered yet -- add one above)", classes="ct-md-empty")
            return
        # THE COMPACT LIST (this module's own docstring, "SELECTION") -- one line per master row,
        # a real clickable/focusable `Button`, never a bare `Static`. No per-row detail content
        # renders here at all -- that is the whole point: an unselected row costs exactly one
        # line, so the operator sees the FULL roster without scrolling past repeated detail-label/
        # help prose for rows they are not currently working with.
        selected_row = None
        for idx, row in enumerate(self.master_rows):
            key = self.spec.master_key(row)
            is_selected = key == self._selected_key
            if is_selected:
                selected_row = row
            marker = "> " if is_selected else "  "
            row_classes = "ct-md-row-select -selected" if is_selected else "ct-md-row-select"
            with Horizontal(classes="ct-md-row"):
                yield Button(f"{marker}{self.spec.master.summarize(row)}",
                             id=f"{self.id}-master-select-{idx}", classes=row_classes)
                yield Button("Remove", id=f"{self.id}-master-remove-{idx}", classes="ct-md-remove")
        if selected_row is None:
            yield Static("(select a principal above to manage its own competences, relations, "
                         "and role charters)", classes="ct-md-empty")
            return
        # DETAIL SECTION -- ONLY for the selected row (never repeated per row; see this module's
        # own docstring for why that was the OTHER half of the maintainer's own complaint).
        key = self.spec.master_key(selected_row)
        with Vertical(id=f"{self.id}-detail", classes="ct-md-block"):
            yield Static(f"Details for {self.spec.master.summarize(selected_row)}",
                         classes="ct-md-row-summary")
            for d in self.spec.details:
                dname = str(d.list_field.name)
                link = str(d.link_field)
                rows = [r for r in self.detail_rows[dname] if str(r.get(link)) == key]
                yield Static(str(d.list_field.label), classes="ct-md-detail-label")
                yield from elucidation_widgets(d.list_field.help, "ct-field-help")
                if not rows:
                    yield Static("(none yet)", classes="ct-md-empty")
                for ridx, r in enumerate(rows):
                    with Horizontal():
                        yield Static(d.list_field.summarize(r), classes="ct-info-line")
                        yield Button("Remove", id=f"{self.id}-detail-remove-{dname}-{ridx}",
                                     classes="ct-md-remove")
                yield Button(f"Add {d.list_field.label}", id=f"{self.id}-detail-add-{dname}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == f"{self.id}-master-add":
            event.stop()
            self.app.push_screen(
                AddItemModal(f"Add {self.spec.master.label}", self.spec.master.item_fields),
                self._on_master_add_result)
            return
        select_prefix = f"{self.id}-master-select-"
        if bid.startswith(select_prefix):
            event.stop()
            idx = int(bid[len(select_prefix):])
            self._set_selected(self.spec.master_key(self.master_rows[idx]))
            self.call_later(self.recompose)
            return
        master_remove_prefix = f"{self.id}-master-remove-"
        if bid.startswith(master_remove_prefix):
            event.stop()
            self._remove_master(int(bid[len(master_remove_prefix):]))
            return
        if self._selected_key is not None:
            for d in self.spec.details:
                dname = str(d.list_field.name)
                add_id = f"{self.id}-detail-add-{dname}"
                if bid == add_id:
                    event.stop()
                    self.app.push_screen(
                        AddItemModal(f"Add {d.list_field.label}", d.list_field.item_fields),
                        self._make_detail_add_result(dname, d, self._selected_key))
                    return
                remove_prefix = f"{self.id}-detail-remove-{dname}-"
                if bid.startswith(remove_prefix):
                    event.stop()
                    ridx = int(bid[len(remove_prefix):])
                    self._remove_detail(dname, str(d.link_field), self._selected_key, ridx)
                    return

    def _on_master_add_result(self, row: "dict | None") -> None:
        if row is None:
            return
        self.master_rows.append(row)
        # Auto-select the just-added row (this module's own docstring, "SELECTION") -- the
        # natural next step after registering a principal is usually to grant it something.
        self._set_selected(self.spec.master_key(row))
        self._notify_master()
        self.call_later(self.recompose)

    def _make_detail_add_result(self, dname: str, d, key: str):
        def _on_result(item: "dict | None") -> None:
            if item is None:
                return
            item = dict(item)
            item[str(d.link_field)] = key
            self.detail_rows[dname].append(item)
            self._notify_detail(dname)
            self.call_later(self.recompose)
        return _on_result

    def _remove_master(self, idx: int) -> None:
        removed_key = self.spec.master_key(self.master_rows[idx])
        del self.master_rows[idx]
        if self._selected_key == removed_key:
            self._set_selected(None)
        # CASCADE (decision-time-only, this run's own in-progress model, never a real DB delete):
        # a dependent row naming a master row that no longer exists in THIS visit is dropped with
        # it -- an orphan left behind would otherwise surface only as a confusing commit-time
        # failure ("grant a competence to a principal that was never registered") instead of
        # right here, where the operator can see and understand the removal.
        for d in self.spec.details:
            dname = str(d.list_field.name)
            link = str(d.link_field)
            before = self.detail_rows[dname]
            after = [r for r in before if str(r.get(link)) != removed_key]
            if after != before:
                self.detail_rows[dname] = after
                self._notify_detail(dname)
        self._notify_master()
        self.call_later(self.recompose)

    def _remove_detail(self, dname: str, link: str, key: str, ridx: int) -> None:
        matching = [r for r in self.detail_rows[dname] if str(r.get(link)) == key]
        if ridx >= len(matching):
            return
        target = matching[ridx]
        self.detail_rows[dname].remove(target)
        self._notify_detail(dname)
        self.call_later(self.recompose)

    def _set_selected(self, key: "str | None") -> None:
        self._selected_key = key
        if self._on_select_change is not None:
            self._on_select_change(key)

    def _notify_master(self) -> None:
        if self._on_master_change is not None:
            self._on_master_change(list(self.master_rows))

    def _notify_detail(self, dname: str) -> None:
        if self._on_detail_change is not None:
            self._on_detail_change(dname, list(self.detail_rows[dname]))
