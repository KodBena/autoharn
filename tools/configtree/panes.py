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

from tools.configtree.fields import (ChoiceField, ListField, MultiChoiceField, default_of,
                                      get_field_value, set_field_value, validate_value)
from tools.configtree.spec import SectionSpec, section_answers, section_field_errors
from tools.configtree.widgets import (FieldError, ListFieldWidget, MultiChoiceFieldWidget,
                                       build_field_widget, elucidation_widgets, field_widget_id,
                                       read_field_value)


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

    def compose(self) -> ComposeResult:
        yield Static(f"{self.spec.title}", classes="ct-section-title")
        yield from elucidation_widgets(self.spec.description, "ct-section-description")
        self._blocked_reason = self.spec.blocked(self.state) if self.spec.blocked else None
        self._errors = {}
        with VerticalScroll(classes="ct-section-body"):
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
                seeded = [str(f.name) for f in self.spec.fields(self.state)
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
                is_group_field = isinstance(f, (ListField, MultiChoiceField))
                yield Static(str(f.label) if not is_group_field else "", classes="ct-field-label")
                if isinstance(f, ListField):
                    yield ListFieldWidget(f, initial=answers[name], on_change=self._make_list_change(f))
                elif isinstance(f, MultiChoiceField):
                    yield MultiChoiceFieldWidget(f, initial=answers[name],
                                                  on_change=self._make_multi_change(f))
                else:
                    yield build_field_widget(f, answers[name])
                    # ELUCIDATION (ledger row 1115): a plain field's own `help` renders as its
                    # own capped element(s) right under it -- `ListField`/`MultiChoiceField`
                    # render their own `help` INSIDE their dedicated widget instead (its own
                    # Label sits above the rows/checkboxes, not a bare section-loop Static).
                    yield from elucidation_widgets(getattr(f, "help", None), "ct-field-help")
                    if isinstance(f, ChoiceField) and f.option_help:
                        for value, _ in f.options:
                            yield from elucidation_widgets(f.option_help.get(value),
                                                             "ct-choice-help", prefix=value)
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
