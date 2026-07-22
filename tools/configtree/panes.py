#!/usr/bin/env python3
"""tools/configtree/panes.py -- the right-pane widgets `app.py`'s `ContentSwitcher` holds: one
`SectionPane` per `SectionSpec` (all fields at once, inline validation) plus the one `CommitPane`
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2). Split out of `app.py` on ADR-0007 grounds (no
file over 400 lines) -- these are still App-adjacent (they import `textual`), just not the
App/Tree wiring itself.

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
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Input, RadioSet, Static

from tools.configtree.fields import ListField, set_field_value, validate_value
from tools.configtree.spec import (CommitSpec, SectionSpec, ready_for_commit, section_answers,
                                    section_field_errors)
from tools.configtree.widgets import (FieldError, ListFieldWidget, build_field_widget,
                                       field_widget_id, read_field_value)


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
        self._blocked_reason = self.spec.blocked(self.state) if self.spec.blocked else None
        self._errors = {}
        with VerticalScroll(classes="ct-section-body"):
            if self._blocked_reason:
                yield Static(f"BLOCKED -- {self._blocked_reason}", classes="ct-blocked-reason")
                return
            if self.spec.precheck is not None:
                for line in self.spec.precheck(self.state):
                    yield Static(line, classes="ct-precheck-line")
            self._field_specs = tuple(self.spec.fields(self.state))
            live_errors = section_field_errors(self.spec, self.state)
            # A prior commit-sweep business-rule refusal (`panes.CommitPane`'s own submit sweep
            # -- a cross-field check no per-field validator could see) OUTRANKS the live
            # per-field check for the SAME field, exactly like the deleted Save-button flow's own
            # `result.errors` used to render (this is that same dict, just surfaced on visit
            # instead of on a save press).
            commit_errors: dict = self.state.get("_commit_errors", {}).get(str(self.spec.slug)) or {}
            answers = section_answers(self.spec, self.state)
            for f in self._field_specs:
                name = str(f.name)
                yield Static(str(f.label) if not isinstance(f, ListField) else "", classes="ct-field-label")
                if isinstance(f, ListField):
                    yield ListFieldWidget(f, initial=answers[name], on_change=self._make_list_change(f))
                else:
                    yield build_field_widget(f, answers[name])
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


class CommitPane(Vertical):
    """The library's own generic commit node (spec §3 v2): the resolved decision set, ONE commit
    confirmation -- the ONLY action button in the app besides quit. Pressing it runs the FULL
    two-phase sequence: every section's `submit` exactly once, in registry order (the live-model
    rebuild's own deferred business-logic pass -- see this module's docstring), THEN, only if
    every section accepted, the actual commit boundary (`CommitSpec.commit`). A section that
    REFUSES at this point (a business-rule check no field-level validator could see) halts the
    sweep before any commit act runs, records the refusal into `state["_commit_errors"]` (so the
    tree reads that section INVALID with the reason), and re-enables this button for a retry."""

    def __init__(self, commit: CommitSpec, sections: tuple, state: dict) -> None:
        super().__init__(id="pane-commit")
        self.commit_spec = commit
        self.sections = sections
        self.state = state
        self._committed = False

    def compose(self) -> ComposeResult:
        yield Static("Review & commit", classes="ct-section-title")
        with VerticalScroll(id="ct-commit-body", classes="ct-section-body"):
            yield Static(self.commit_spec.render_summary(self.state), id="ct-commit-summary")
            sweep_error = self.state.get("_commit_sweep_error")
            if sweep_error:
                yield Static(sweep_error, classes="ct-blocked-reason")
        ready = ready_for_commit(self.sections, self.state)
        with Horizontal(classes="ct-section-buttons"):
            label = self.commit_spec.confirm_label if ready else \
                f"{self.commit_spec.confirm_label} (blocked -- sections incomplete)"
            yield Button(label, id="ct-commit", variant="primary", disabled=not ready)

    @property
    def is_committed(self) -> bool:
        return self._committed

    async def refresh_readiness(self) -> None:
        await self.recompose()

    def _run_submit_sweep(self) -> "str | None":
        """Every section's `submit`, exactly once, in registry order, REPLAYED FRESH on every
        commit attempt (a retry after fixing one section must not append onto a stale prior
        attempt's queued effects -- `CommitSpec.reset`, if given, clears the consumer's own
        accumulator first). Returns `None` on full success (every section accepted its own
        current live answers); otherwise the human-readable refusal to show, having already
        recorded which section failed into `state["_commit_errors"]`."""
        self.state.pop("_commit_errors", None)
        if self.commit_spec.reset is not None:
            self.commit_spec.reset(self.state)
        for spec in self.sections:
            answers = section_answers(spec, self.state)
            result = spec.submit(self.state, answers)
            if not result.ok:
                errors = result.errors or {"": "refused (no field named)"}
                self.state["_commit_errors"] = {str(spec.slug): errors}
                return (f"REFUSED at section '{spec.slug}' ({spec.title}): {errors} -- fix it "
                        f"there (the tree node now reads INVALID) and commit again.")
            if result.state_updates:
                self.state.update(result.state_updates)
            # NOTE: no blind `self.state.update(answers)` here (removed 2026-07-22, the same
            # fix as `_write_through`'s own docstring) -- a section's OWN field values already
            # live in their scoped slots (or the bare key, for an explicitly `shared=True`
            # field); re-copying every field's raw value onto a bare top-level key here was the
            # SAME aliasing hazard `set_field_value` exists to prevent, just at commit time
            # instead of per-keystroke. `submit`'s own `state_updates` is the sole, deliberate,
            # named channel by which a section exports a fact to the rest of the model.
        return None

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "ct-commit" or self._committed:
            return
        if not ready_for_commit(self.sections, self.state):
            return
        sweep_error = self._run_submit_sweep()
        if sweep_error:
            self.state["_commit_sweep_error"] = sweep_error
            app = getattr(self, "app", None)
            if app is not None and hasattr(app, "on_model_changed"):
                app.on_model_changed()
            await self.recompose()
            return
        self.state.pop("_commit_sweep_error", None)
        self._committed = True
        event.button.disabled = True
        result = self.commit_spec.commit(self.state)
        body = self.query_one("#ct-commit-body", VerticalScroll)
        for line in result.info_lines:
            body.mount(Static(line, classes="ct-info-line"))
        body.mount(Button("Finish", id="ct-finish", variant="success"))
        self.state["_commit_ok"] = result.ok
