#!/usr/bin/env python3
"""tools/configtree/panes.py -- the right-pane widgets `app.py`'s `ContentSwitcher` holds: one
`SectionPane` per `SectionSpec` (all fields at once, inline validation, a Save button) plus the
one `CommitPane` (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2). Split out of `app.py` on ADR-0007
grounds (no file over 400 lines) -- these are still App-adjacent (they import `textual`), just not
the App/Tree wiring itself.

BLOCKED RENDERING (spec §3 v2: "a field (or section) whose prerequisites are unmet shows disabled
with the prerequisite NAMED"): a `SectionPane` whose `spec.blocked(state)` returns a reason shows
ONLY that reason -- no fields, no Save button -- so there is nothing to interact with until the
prerequisite is met; re-checked every time the pane is (re)shown via `refresh`, never cached."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static

from tools.configtree.fields import ListField, TextField, ChoiceField, ConfirmField
from tools.configtree.spec import CommitSpec, SectionSpec, all_sections_complete
from tools.configtree.widgets import FieldError, ListFieldWidget, build_field_widget, field_widget_id, read_field_value


def _default_of(f) -> object:
    if isinstance(f, ConfirmField):
        return f.default
    if isinstance(f, ChoiceField):
        return f.default
    return getattr(f, "default", "")


class SectionPane(Vertical):
    """One configuration section's form. Mounted ONCE (by `app.py`, into the `ContentSwitcher`)
    and never rebuilt while the app runs -- switching away and back preserves whatever the
    operator typed, exactly the durable-widget-instance idiom the deleted screen-stack wizard
    used, generalized to arbitrary-order tree navigation instead of a linear Back stack."""

    def __init__(self, spec: SectionSpec, state: dict, on_saved) -> None:
        super().__init__(id=f"pane-{spec.slug}")
        self.spec = spec
        self.state = state
        self._on_saved = on_saved
        self._field_specs: tuple = ()
        self._errors: dict[str, FieldError] = {}
        self._blocked_reason: "str | None" = None

    def compose(self) -> ComposeResult:
        yield Static(f"{self.spec.title}", classes="ct-section-title")
        self._blocked_reason = self.spec.blocked(self.state) if self.spec.blocked else None
        with VerticalScroll(classes="ct-section-body"):
            if self._blocked_reason:
                yield Static(f"BLOCKED -- {self._blocked_reason}", classes="ct-blocked-reason")
                return
            if self.spec.precheck is not None:
                for line in self.spec.precheck(self.state):
                    yield Static(line, classes="ct-precheck-line")
            self._field_specs = tuple(self.spec.fields(self.state))
            for f in self._field_specs:
                yield Static(str(f.label) if not isinstance(f, ListField) else "", classes="ct-field-label")
                if isinstance(f, ListField):
                    yield ListFieldWidget(f, initial=self.state.get(str(f.name)))
                else:
                    yield build_field_widget(f, self.state.get(str(f.name), _default_of(f)))
                if not isinstance(f, ListField):
                    err = FieldError()
                    self._errors[str(f.name)] = err
                    yield err
            whole_err = FieldError()
            self._errors[""] = whole_err
            yield whole_err
        with Horizontal(classes="ct-section-buttons"):
            yield Button("Save section", id="ct-save", variant="primary")

    def refresh_blocked(self) -> None:
        """Re-renders this pane (blocked reason may have changed -- another section's edit can
        unblock or re-block this one). Called by `app.py` after ANY section's successful save."""
        self.remove_children()
        self.mount_all(list(self.compose()))

    def _collect_answers(self) -> tuple[dict, dict[str, str]]:
        answers: dict[str, object] = {}
        errors: dict[str, str] = {}
        for f in self._field_specs:
            name = str(f.name)
            if isinstance(f, ListField):
                widget = self.query_one(f"#{field_widget_id(f.name)}", ListFieldWidget)
                answers[name] = list(widget.rows)
                continue
            widget = self.query_one(f"#{field_widget_id(f.name)}")
            val = read_field_value(f, widget)
            if isinstance(f, TextField):
                if f.required and not str(val).strip():
                    errors[name] = "required"
                elif f.validator is not None:
                    msg = f.validator(str(val))
                    if msg:
                        errors[name] = msg
            elif isinstance(f, ChoiceField) and val is None:
                errors[name] = "choose one"
            answers[name] = val
        return answers, errors

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "ct-save" or self._blocked_reason:
            return
        answers, errors = self._collect_answers()
        for name, err_widget in self._errors.items():
            err_widget.set_text(errors.get(name, ""))
        if errors:
            self._on_saved(self.spec, ok=False)
            return
        result = self.spec.submit(self.state, answers)
        if not result.ok:
            for name, msg in (result.errors or {}).items():
                if name in self._errors:
                    self._errors[name].set_text(msg)
                else:
                    self._errors[""].set_text(msg)
            self._on_saved(self.spec, ok=False)
            return
        if result.state_updates:
            self.state.update(result.state_updates)
        # `answers` are also folded into `state` under each field's own name -- a later section's
        # `fields(state)` default (e.g. observability's "dest") reads exactly this, no separate
        # prior-answers seam needed (mirrors `config_seam.build_initial_state_overrides`'s own
        # note that the deleted per-prompt map is no longer needed).
        self.state.update(answers)
        body = self.query_one(".ct-section-body", VerticalScroll)
        for line in result.info_lines:
            body.mount(Static(line, classes="ct-info-line"))
        self._on_saved(self.spec, ok=True)


class CommitPane(Vertical):
    """The library's own generic commit node (spec §3 v2): the resolved decision set, one commit
    confirmation, enabled exactly when `all_sections_complete` -- re-checked every time this pane
    is refreshed, never cached."""

    def __init__(self, commit: CommitSpec, sections: tuple, state: dict, on_committed) -> None:
        super().__init__(id="pane-commit")
        self.commit_spec = commit
        self.sections = sections
        self.state = state
        self._on_committed = on_committed
        self._committed = False

    def compose(self) -> ComposeResult:
        yield Static("Review & commit", classes="ct-section-title")
        with VerticalScroll(id="ct-commit-body", classes="ct-section-body"):
            yield Static(self.commit_spec.render_summary(self.state), id="ct-commit-summary")
        ready = all_sections_complete(self.sections, self.state)
        with Horizontal(classes="ct-section-buttons"):
            label = self.commit_spec.confirm_label if ready else \
                f"{self.commit_spec.confirm_label} (blocked -- sections incomplete)"
            yield Button(label, id="ct-commit", variant="primary", disabled=not ready)

    def refresh_readiness(self) -> None:
        self.remove_children()
        self.mount_all(list(self.compose()))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "ct-commit" or self._committed:
            return
        if not all_sections_complete(self.sections, self.state):
            return
        self._committed = True
        event.button.disabled = True
        result = self.commit_spec.commit(self.state)
        body = self.query_one("#ct-commit-body", VerticalScroll)
        for line in result.info_lines:
            body.mount(Static(line, classes="ct-info-line"))
        body.mount(Button("Finish", id="ct-finish", variant="success"))
        self.state["_commit_ok"] = result.ok
        self._on_committed(result.ok)
