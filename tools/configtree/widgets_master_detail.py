#!/usr/bin/env python3
"""tools/configtree/widgets_master_detail.py -- `MasterDetailFieldWidget`, split into its own
file (ADR-0007: no file over 400 lines; `widgets.py` was already at 385 with no `gates/
max_lines.py` baseline entry -- growing it past 400 would be refused outright, so this is a new,
composed file rather than a ratchet).

The `MasterDetailField` renderer (ADR-0019 Rule 4; genre exemplar: Django/Rails admin inline
formsets, `master_detail.py`'s own module docstring). One block per master row
(`spec.master.summarize`), each carrying its OWN nested Add/Remove per `DetailListField` -- a
detail row added from inside principal X's own block can never appear under principal Y's (the
link value is auto-injected from X's own `master_key`, never re-picked by the operator;
`master_detail.DetailListField`'s own docstring, "LINK FIELD"). Each detail's own elucidation
(`help`) renders ONCE, at the top, next to its label -- not repeated inside every master row's own
block, which would be the SAME teaching text duplicated once per principal for no reason.

Rebuilds via `recompose()` after every Add/Remove (master or any detail) -- discrete button
presses, not per-keystroke typing (`widgets.MultiChoiceFieldWidget`'s own docstring explains why a
recompose is UNSAFE mid-keystroke; a button press has no such hazard, the SAME reasoning
`widgets.ListFieldWidget` already relies on for its own Add/Remove, which has never had that
problem)."""
from __future__ import annotations

from typing import Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from tools.configtree.master_detail import MasterDetailField
from tools.configtree.widgets import AddItemModal, elucidation_widgets, field_widget_id


class MasterDetailFieldWidget(Vertical):
    """See this module's own docstring. `initial_master`/`initial_details` seed this widget's own
    in-memory rows from the CURRENT shared state (read once, at construction -- the enclosing
    `SectionPane` rebuilds this widget fresh on every recompose, so there is no staleness risk)."""

    def __init__(self, spec: MasterDetailField, initial_master: "list[dict] | None" = None,
                 initial_details: "dict[str, list[dict]] | None" = None,
                 on_master_change: "Callable[[list[dict]], None] | None" = None,
                 on_detail_change: "Callable[[str, list[dict]], None] | None" = None) -> None:
        super().__init__(id=field_widget_id(spec.name), classes="ct-field-group")
        self.spec = spec
        self.master_rows: list[dict] = list(initial_master or [])
        self.detail_rows: dict[str, list[dict]] = {
            str(d.list_field.name): list((initial_details or {}).get(str(d.list_field.name), []))
            for d in spec.details
        }
        self._on_master_change = on_master_change
        self._on_detail_change = on_detail_change

    def compose(self) -> ComposeResult:
        yield Static(str(self.spec.master.label), classes="ct-field-label")
        yield from elucidation_widgets(self.spec.master.help, "ct-field-help")
        yield from elucidation_widgets(self.spec.help, "ct-field-help")
        yield Button(f"Add {self.spec.master.label}", id=f"{self.id}-master-add")
        for d in self.spec.details:
            yield Static(str(d.list_field.label), classes="ct-md-detail-label")
            yield from elucidation_widgets(d.list_field.help, "ct-field-help")
        if not self.master_rows:
            yield Static("(none registered yet -- add one above)", classes="ct-md-empty")
        for idx, row in enumerate(self.master_rows):
            key = self.spec.master_key(row)
            with Vertical(id=f"{self.id}-block-{idx}", classes="ct-md-block"):
                with Horizontal():
                    yield Static(self.spec.master.summarize(row), classes="ct-md-row-summary")
                    yield Button("Remove", id=f"{self.id}-master-remove-{idx}", classes="ct-md-remove")
                for d in self.spec.details:
                    dname = str(d.list_field.name)
                    link = str(d.link_field)
                    rows = [r for r in self.detail_rows[dname] if str(r.get(link)) == key]
                    yield Static(f"{d.list_field.label}:", classes="ct-md-detail-sub-label")
                    if not rows:
                        yield Static("(none yet)", classes="ct-md-empty")
                    for ridx, r in enumerate(rows):
                        with Horizontal():
                            yield Static(d.list_field.summarize(r), classes="ct-info-line")
                            yield Button("Remove",
                                         id=f"{self.id}-detail-remove-{idx}-{dname}-{ridx}",
                                         classes="ct-md-remove")
                    yield Button(f"Add {d.list_field.label}",
                                 id=f"{self.id}-detail-add-{idx}-{dname}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == f"{self.id}-master-add":
            event.stop()
            self.app.push_screen(
                AddItemModal(f"Add {self.spec.master.label}", self.spec.master.item_fields),
                self._on_master_add_result)
            return
        master_remove_prefix = f"{self.id}-master-remove-"
        if bid.startswith(master_remove_prefix):
            event.stop()
            self._remove_master(int(bid[len(master_remove_prefix):]))
            return
        for idx, row in enumerate(self.master_rows):
            key = self.spec.master_key(row)
            for d in self.spec.details:
                dname = str(d.list_field.name)
                add_id = f"{self.id}-detail-add-{idx}-{dname}"
                if bid == add_id:
                    event.stop()
                    self.app.push_screen(
                        AddItemModal(f"Add {d.list_field.label}", d.list_field.item_fields),
                        self._make_detail_add_result(dname, d, key))
                    return
                remove_prefix = f"{self.id}-detail-remove-{idx}-{dname}-"
                if bid.startswith(remove_prefix):
                    event.stop()
                    ridx = int(bid[len(remove_prefix):])
                    self._remove_detail(dname, str(d.link_field), key, ridx)
                    return

    def _on_master_add_result(self, row: "dict | None") -> None:
        if row is None:
            return
        self.master_rows.append(row)
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

    def _notify_master(self) -> None:
        if self._on_master_change is not None:
            self._on_master_change(list(self.master_rows))

    def _notify_detail(self, dname: str) -> None:
        if self._on_detail_change is not None:
            self._on_detail_change(dname, list(self.detail_rows[dname]))
