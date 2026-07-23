#!/usr/bin/env python3
"""tools/configtree/confirm_modal.py -- `ConfirmModal`, the ONE confirm-before-destroy screen in
this package (ADR-0019 appendix C10: "a destructive/irreversible action ... that commits without
either a confirm step or a registered undo is refused ... neither being present is the defect").

CYCLE-5 AUDIT FINDING #1 (`/home/bork/autoharn_series/cycle-5/AUDIT.md`, MAJOR): removing a
master row in `widgets_master_detail.MasterDetailFieldWidget` used to cascade-delete every
dependent competence/relation/charter row with ONE click, no confirm, no undo, no after-the-fact
notice -- directly contradicting `_remove_master`'s own docstring claim ("right here, where the
operator can see and understand the removal"). Nothing on screen ever communicated that a removal
cascaded at all.

FIX (the confirm branch of C10's own either/or -- chosen over a registered undo because the genre
exemplar the master-detail restructure already cites, Django/Rails admin inline formsets, marks a
row for deletion and asks before it actually discards on save; a confirm step here is the same
"ask before you lose data you can name" discipline, one step earlier, and needs no session-scoped
undo stack to get right): `MasterDetailFieldWidget._remove_master` now pushes `ConfirmModal`
naming the EXACT cascade inventory (competence/relation/charter counts, by name, never a bare
"are you sure?") whenever the row being removed has at least one dependent row anywhere; the
removal only actually runs if the operator confirms. A row with ZERO dependents removes
immediately, no confirm shown -- C10's own class is "destructive actions" and removing a
principal that carries nothing else destroys nothing beyond the one row already visible and
already the direct target of the click; forcing a confirm on that case would be gratuitous
ceremony Cooper's own pedigree note (C10's "Cooper on gratuitous vs. earned confirmation")
explicitly warns against."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from tools.configtree.layout_primitives import ContentHorizontal, ContentVertical


class ConfirmModal(ModalScreen[bool]):
    """A short, named-consequence confirm step. `lines` -- one `Static` per line, e.g. the exact
    cascade inventory ("1 competence", "0 relations", "0 charters") -- never a single generic
    sentence; the whole point of C10's confirm branch is that the operator can read WHAT is about
    to be destroyed, not just that something will be. Dismisses `True` on confirm, `False` on
    Cancel/Escape (the same "never ambiguous, never a silent default" discipline `AddItemModal`
    already uses for its own Save/Cancel)."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, lines: "tuple[str, ...]") -> None:
        super().__init__()
        self._title = title
        self._lines = lines

    def compose(self) -> ComposeResult:
        with ContentVertical(id="ct-confirm-body"):
            yield Static(self._title, id="ct-confirm-title", classes="ct-section-title")
            for line in self._lines:
                yield Static(line, classes="ct-info-line")
            with ContentHorizontal(id="ct-confirm-buttons"):
                yield Button("Remove", id="ct-confirm-yes", variant="error")
                yield Button("Cancel", id="ct-confirm-no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ct-confirm-yes":
            self.dismiss(True)
        elif event.button.id == "ct-confirm-no":
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)
