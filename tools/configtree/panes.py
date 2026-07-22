#!/usr/bin/env python3
"""tools/configtree/panes.py -- `SectionPane`, the right-pane widget `app.py`'s `ContentSwitcher`
holds one of per `SectionSpec` (all fields at once, inline validation) (design/FABLE-SETUP-TUI-
REBUILD-SPEC.md §3 v2). Split out of `app.py` on ADR-0007 grounds (no file over 400 lines) --
still App-adjacent (imports `textual`), just not the App/Tree wiring itself. `CommitPane` (the
one generic commit node) lives in the sibling `commit_pane.py`, split out of THIS file for the
same ADR-0007 reason once the off-UI-thread worker fix (ledger row 1130's own sibling audit)
pushed it over 400 lines.

LIVE-MODEL REBUILD (maintainer review, 2026-07-22, same day as the tree+form rejection this
package answers): the maintainer's reference idiom (Qt settings GUI, SAP IMG) has NO per-section
Save button -- "the form IS a live view of the model." A Save button meant form state and model
state were two stores an operator had to keep in sync by remembering to press it; that dual-store
shape was the defect, not the button by itself. FIXED: every field writes straight into the
shared model on its own Textual `Changed` message (`on_input_changed`/`on_radio_set_changed`/
`on_checkbox_changed`, plus `ListFieldWidget`'s own `on_change` callback for Add/Remove) -- no
intermediate "answers" dict, no confirm step. A section's REAL business logic (`SectionSpec.
submit` -- which may perform a genuine effect, e.g. queuing a `Plan` entry or running a live
rehearsal probe) is no longer invoked per keystroke (it would re-run, and re-effect, on every
character typed); it now runs EXACTLY ONCE PER SECTION, in registry order, as part of the single
commit action (`CommitPane.on_button_pressed`'s own submit sweep, mirroring `tools/setup_tui/
app.py`'s existing `--from-config` headless replay -- both paths now converge on the identical
two-phase shape: finalize every section's decision in commit order, then commit). FIELD-LEVEL
validity (required/validator/choice-membership -- `fields.validate_value`) is the ONLY thing
computed live, both for a field's own inline error and for `spec.section_status`'s tree-node
coloring; a deeper business-rule refusal (a world that already exists, gpg missing from PATH,
...) surfaces only when the commit sweep actually calls `submit`, exactly like an ordinary
settings dialog's OK/Apply can still refuse on a cross-field rule no per-field check could see.

STATE ALIASING (a SEPARATE maintainer-diagnosed live defect, same day, caught from the running UI
alone: "clicking a checkbox in one menu subsection toggles a corresponding-ish checkbox in a
DIFFERENT subsection"): the first live-model draft's write-through wrote `self.state[name] =
value` -- a BARE field name -- so two sections' own SAME-NAMED field (every section has its own
`ConfirmField(name="run", ...)`) silently shared one model slot. ADR-0012's cancer C ("hidden
state keyed by an insufficiently distinguishing key") read straight, plus the maintainer's
standing "no bare types" rule (ledger row 1105). FIXED, structurally: `fields.set_field_value`/
`get_field_value` key every NON-`shared` field by `ids.ScopedFieldKey(section, field)`, never a
bare name -- see `fields.py`'s own "SHARED-FIELD DOCTRINE" note for the full account and the
narrow, explicit, individually-justified `shared=True` exception (the destination directory,
genuinely the SAME fact everywhere it appears).

BLOCKED RENDERING (spec §3 v2: "a field (or section) whose prerequisites are unmet shows disabled
with the prerequisite NAMED"): a `SectionPane` whose `spec.blocked(state)` returns a reason shows
ONLY that reason -- no fields -- re-checked every time the pane is (re)shown, never cached."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Checkbox, Input, RadioSet, Static

from tools.configtree.fields import ListField, MultiChoiceField, default_of, get_field_value, set_field_value, validate_value
from tools.configtree.item_modal import render_item_field
from tools.configtree.master_detail import MasterDetailField, flatten_fields
from tools.configtree.spec import SectionSpec, section_answers, section_field_errors
from tools.configtree.widget_primitives import FieldError, elucidation_widgets, field_widget_id, read_field_value
from tools.configtree.widgets import ListFieldWidget, MultiChoiceFieldWidget
from tools.configtree.widgets_master_detail import MasterDetailFieldWidget


class SectionPane(Vertical):
    """One configuration section's form -- a LIVE view of the shared state, mounted ONCE (by
    `app.py`, into the `ContentSwitcher`) and never rebuilt while the app runs except when
    `refresh_blocked` is explicitly asked to (another section's edit may have changed this one's
    prerequisite or, after a commit-sweep failure, its business-rule error)."""

    def __init__(self, spec: SectionSpec, state: dict) -> None:
        super().__init__(id=f"pane-{spec.slug}")
        self.spec = spec
        self.state = state
        self._field_specs: tuple = ()
        self._errors: dict[str, FieldError] = {}
        self._blocked_reason: "str | None" = None
        # SELECTION SURVIVES A WHOLE-SECTION RECOMPOSE (cycle-3 fix round, ledger row 1136):
        # `_make_md_master_change` ALWAYS recomposes this whole pane (its own docstring explains
        # why -- a sibling detail's own choices derive from the master's current rows), which
        # destroys and rebuilds a fresh `MasterDetailFieldWidget` instance on every master Add/
        # Remove -- a selection held only INSIDE that widget's own transient state would be lost
        # on the very same add that is supposed to auto-select the just-added row. THIS pane, by
        # contrast, is mounted ONCE and never destroyed (`app.py`'s own "EVERY SECTION PANE IS
        # MOUNTED ONCE" contract) -- keyed by `MasterDetailField` name (plural in principle, one
        # instance today), it is the one place selection can genuinely survive.
        self._md_selected: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        self._blocked_reason = self.spec.blocked(self.state) if self.spec.blocked else None
        self._errors = {}
        # HAZARD FIX (cycle-3 fix round, found in reach of TASK 1's own reproduction matrix,
        # ledger row 1136): the title/description used to render OUTSIDE this VerticalScroll, as
        # fixed-size siblings of it inside the enclosing `Vertical` -- Textual's `1fr` sizing gives
        # a flex child only what is LEFT after its fixed-size siblings take their own natural
        # height, so a long section description (principals-authority's own multi-line
        # Requires/Full-basis elucidation, wrapped narrow at a real terminal's actual content-pane
        # width) could squeeze this scroll region down to a sliver only a couple of rows tall --
        # reproduced live at 80x24: the section's own "Add a principal" master-detail widget
        # rendered at `y=46` while the visible screen was only 24 rows tall, and even
        # `scroll_end()` overshot it (the scroll viewport was so starved the button's own true
        # position never became reachable by a real Pilot mouse click, `OutOfBounds`). Title and
        # description now render INSIDE the same scroll region as the fields themselves: the
        # scroll always gets the FULL available height (no fixed-size sibling above it inside the
        # SAME parent to starve it), and if the combined content still exceeds the viewport, the
        # OPERATOR CAN SCROLL TO IT -- a starved sliver is unrepresentable, a normal scroll is not
        # a hazard.
        with VerticalScroll(classes="ct-section-body"):
            yield Static(f"{self.spec.title}", classes="ct-section-title")
            yield from elucidation_widgets(self.spec.description, "ct-section-description")
            if self._blocked_reason:
                yield Static(f"BLOCKED -- {self._blocked_reason}", classes="ct-blocked-reason")
                # SEEDED-VALUE VISIBILITY (maintainer-witnessed, ledger row 1130: an in-UI
                # config load reported "seeded N field default(s)" but a BLOCKED section (e.g.
                # Hydration/Boundary/Observability/Birth/Principals-authority/Signed-genesis,
                # every one gated on a destination directory) rendered NOTHING under it -- the
                # blocked banner swallowed the seeded values whole, with no cue they were even
                # there. Root cause was never field-KIND-specific (`get_field_value`/every
                # widget builder in this module were verified correct for all four field kinds,
                # empirically, once a section is unblocked) -- it was this early `return`, which
                # never even LOOKS at the section's own fields while blocked. FIXED: still
                # compute this section's fields against the CURRENT state (read-only -- no
                # widget is built, nothing here can write through) and name every one that
                # already carries a non-default (seeded, or previously touched) value, so a
                # seeded default is visible EVEN WHILE the section stays correctly blocked from
                # editing.
                seeded = [str(f.name) for f in flatten_fields(self.spec.fields(self.state))
                          if get_field_value(self.state, self.spec.slug, f) != default_of(f)]
                if seeded:
                    yield Static(
                        f"({len(seeded)} field(s) already hold a seeded/set value, hidden "
                        f"until unblocked: {', '.join(seeded)})", classes="ct-blocked-reason")
                return
            if self.spec.precheck is not None:
                for line in self.spec.precheck(self.state):
                    yield Static(line, classes="ct-precheck-line")
            self._field_specs = tuple(self.spec.fields(self.state))
            live_errors = section_field_errors(self.spec, self.state)
            # A prior commit-sweep business-rule refusal (`commit_pane.CommitPane`'s own submit sweep
            # -- a cross-field check no per-field validator could see) OUTRANKS the live
            # per-field check for the SAME field, exactly like the deleted Save-button flow's own
            # `result.errors` used to render (this is that same dict, just surfaced on visit
            # instead of on a save press).
            commit_errors: dict = self.state.get("_commit_errors", {}).get(str(self.spec.slug)) or {}
            answers = section_answers(self.spec, self.state)
            for f in self._field_specs:
                name = str(f.name)
                is_group_field = isinstance(f, (ListField, MultiChoiceField, MasterDetailField))
                if is_group_field:
                    yield Static("", classes="ct-field-label")
                if isinstance(f, MasterDetailField):
                    # ADR-0019 Rule 4 (master-detail, not a sibling flat list): a MasterDetailField
                    # renders as ONE widget managing its own master rows AND every nested detail
                    # list -- `answers` already carries the master's own name PLUS each detail's
                    # own name (`spec.section_answers` flattens via `master_detail.flatten_fields`
                    # before this pane ever sees it), so the initial values below are the SAME
                    # per-name live state every other field reads, just handed to one composite
                    # widget instead of several separate ones.
                    initial_details = {str(d.list_field.name): answers[str(d.list_field.name)]
                                       for d in f.details}
                    yield MasterDetailFieldWidget(
                        f, initial_master=answers[name], initial_details=initial_details,
                        initial_selected_key=self._md_selected.get(name),
                        on_master_change=self._make_md_master_change(f),
                        on_detail_change=self._make_md_detail_change(f),
                        on_select_change=self._make_md_select_change(f))
                elif isinstance(f, ListField):
                    yield ListFieldWidget(f, initial=answers[name], on_change=self._make_list_change(f))
                elif isinstance(f, MultiChoiceField):
                    yield MultiChoiceFieldWidget(f, initial=answers[name],
                                                  on_change=self._make_multi_change(f))
                else:
                    # CYCLE-3 FIX (ledger row 1136's own MAJOR findings #1/#2): the label, the
                    # filter-routed widget, and the field's own `help`/`option_help` elucidation
                    # are now rendered by the ONE shared `item_modal.render_item_field` --
                    # `AddItemModal.compose` calls the exact same function for its own item
                    # fields, so this pane and a modal can never drift again (ADR-0012 P1).
                    yield from render_item_field(f, answers[name])
                err = FieldError()
                err.set_text(commit_errors.get(name) or live_errors.get(name, ""))
                self._errors[name] = err
                yield err
            whole_err = FieldError()
            whole_err.set_text(commit_errors.get("", ""))
            self._errors[""] = whole_err
            yield whole_err

    async def refresh_blocked(self) -> None:
        """Re-renders this pane (blocked reason, or a commit-sweep business error, may have
        changed). `Widget.recompose()` (not a manual `remove_children`+`compose()` call --
        `compose()`'s own `with Vertical(...):` context-manager form only works inside Textual's
        own mount machinery, which `recompose()` re-enters correctly) is the library's own idiom
        for exactly this "re-render this widget's children from its `compose()` again" need."""
        await self.recompose()

    def _find_field(self, widget_id: "str | None"):
        if not widget_id:
            return None
        for f in self._field_specs:
            if field_widget_id(f.name) == widget_id:
                return f
        return None

    def _write_through(self, f, value: object) -> None:
        """The ONE write-through choke point: a field's raw Changed value goes straight into the
        shared model via `fields.set_field_value` -- ALIAS-PROOF BY CONSTRUCTION (maintainer-
        diagnosed live defect, 2026-07-22: two sections' own same-NAMED field, e.g.
        `ConfirmField(name="run", ...)`, silently shared one bare `state["run"]` slot; the fix is
        `ids.ScopedFieldKey(section, field)` for every field NOT explicitly declared
        `shared=True`, so this write can never land in another section's own slot by accident --
        see `fields.py`'s own "SHARED-FIELD DOCTRINE" note). This field's OWN inline error is
        recomputed and rendered, and the whole app is told to recompute every tree node's status
        live (cheap -- label text only, no recompose) so a prerequisite unblocks the moment its
        value lands, not on some later save/select event."""
        name = str(f.name)
        set_field_value(self.state, self.spec.slug, f, value)
        msg = validate_value(f, value)
        err = self._errors.get(name)
        if err is not None:
            err.set_text(msg or "")
        app = getattr(self, "app", None)
        if app is not None and hasattr(app, "on_model_changed"):
            app.on_model_changed()

    def _make_list_change(self, f):
        widget_id = field_widget_id(f.name)

        def _on_change() -> None:
            widget = self.query_one(f"#{widget_id}", ListFieldWidget)
            self._write_through(f, list(widget.rows))
            if getattr(f, "refresh_siblings", False):
                # `ListField.refresh_siblings`'s own docstring: another field in THIS section's
                # `fields(state)` derives its own choices from this list's CURRENT rows -- a full
                # recompose (scheduled, not awaited, from this sync callback -- `call_later` is
                # this library's own sanctioned "run this coroutine soon" idiom for exactly that,
                # verified empirically against the installed Textual version) makes the sibling
                # field's derived options current on the SAME visit, not only the next one.
                self.call_later(self.recompose)

        return _on_change

    def _make_multi_change(self, f):
        widget_id = field_widget_id(f.name)

        def _on_change() -> None:
            widget = self.query_one(f"#{widget_id}", MultiChoiceFieldWidget)
            self._write_through(f, list(widget.selected))

        return _on_change

    def _make_md_master_change(self, f: MasterDetailField):
        """`MasterDetailFieldWidget`'s own master-row callback -- writes through `f.master` (the
        underlying `ListField` this composite wraps, `master_detail.py`'s own "STORAGE IS
        UNCHANGED" doctrine) and ALWAYS recomposes this whole `SectionPane` (unlike an ordinary
        `ListField`'s own opt-in `refresh_siblings`): a master-detail's sibling detail lists
        almost always derive their OWN `item_fields` choices from the master's current rows (e.g.
        a relation's 'object' picker), so a newly registered master row must be pickable
        elsewhere on THIS SAME visit, not only the next time this section is re-selected."""
        def _on_change(rows: list) -> None:
            self._write_through(f.master, rows)
            self.call_later(self.recompose)
        return _on_change

    def _make_md_detail_change(self, f: MasterDetailField):
        by_name = {str(d.list_field.name): d.list_field for d in f.details}

        def _on_change(dname: str, rows: list) -> None:
            self._write_through(by_name[dname], rows)

        return _on_change

    def _make_md_select_change(self, f: MasterDetailField):
        """`MasterDetailFieldWidget`'s own selection callback -- stores the CURRENTLY selected
        master row's own key on THIS pane (never inside the widget, which does not survive a
        master Add/Remove's own full-pane recompose -- see `__init__`'s own note), so the next
        `MasterDetailFieldWidget` instance built for this SAME field starts already selecting the
        SAME row the operator was just looking at (or the just-added row, on an Add)."""
        name = str(f.name)

        def _on_change(key: "str | None") -> None:
            if key is None:
                self._md_selected.pop(name, None)
            else:
                self._md_selected[name] = key

        return _on_change

    def on_input_changed(self, event: Input.Changed) -> None:
        f = self._find_field(event.input.id)
        if f is not None:
            self._write_through(f, event.value)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        f = self._find_field(event.radio_set.id)
        if f is not None:
            self._write_through(f, read_field_value(f, event.radio_set))

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        f = self._find_field(event.checkbox.id)
        if f is not None:
            self._write_through(f, event.value)


# `CommitPane` moved to `tools/configtree/commit_pane.py` (ADR-0007: this fix's own worker/
# cancellation logic pushed this file from 288 to 432 lines) -- imported back into `__init__.py`
# and `app.py` from its new home; `panes.py` keeps `SectionPane` only.
