#!/usr/bin/env python3
"""tools/configtree/actions.py -- `ActionPane`, split out of `tools.configtree.panes` on ADR-0007
grounds (no file over 400 lines, `gates/max_lines.py`'s own ratcheting-baseline gate: this
package has no baselined entry, so growth over 400 is refused outright, not merely reviewed).

One `ActionSpec`'s own pane (`tools.configtree.spec.ActionSpec`'s own docstring): fields render
and write-through exactly like an ordinary `SectionPane`'s (the SAME field-kind widgets, live, no
per-field save button), but the ONE button here calls `ActionSpec.apply` IMMEDIATELY -- never
deferred to the commit sweep (maintainer round 5, ledger row 1115, defect C: an in-UI
config-loading affordance "usable at start"). A successful apply's `state_updates` merge into the
shared `state` right away, and `ConfigTreeApp.reload_all_panes` is asked to recompose every
ALREADY-MOUNTED `SectionPane` so a value this action just seeded shows up as that section's own
live default on the SAME visit, never merely the next one."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Input, RadioSet, Static

from tools.configtree.fields import (ChoiceField, ListField, MultiChoiceField, get_field_value,
                                      set_field_value, validate_value)
from tools.configtree.spec import ActionSpec
from tools.configtree.widgets import (FieldError, ListFieldWidget, MultiChoiceFieldWidget,
                                       build_field_widget, field_widget_id, read_field_value)


class ActionPane(Vertical):
    """See this module's own docstring for the "immediate, not deferred" contract."""

    def __init__(self, spec: ActionSpec, state: dict) -> None:
        super().__init__(id=f"pane-action-{spec.slug}")
        self.spec = spec
        self.state = state
        self._field_specs: tuple = ()
        self._errors: dict[str, FieldError] = {}

    def compose(self) -> ComposeResult:
        yield Static(f"{self.spec.title}", classes="ct-section-title")
        if self.spec.description:
            yield Static(self.spec.description, classes="ct-section-description", markup=False)
        self._errors = {}
        with VerticalScroll(id=f"{self.id}-body", classes="ct-section-body"):
            self._field_specs = tuple(self.spec.fields(self.state))
            answers = {str(f.name): get_field_value(self.state, self.spec.slug, f)
                       for f in self._field_specs}
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
                    if getattr(f, "help", None):
                        yield Static(f.help, classes="ct-field-help", markup=False)
                    if isinstance(f, ChoiceField) and f.option_help:
                        for value, _ in f.options:
                            help_text = f.option_help.get(value)
                            if help_text:
                                yield Static(f"{value}: {help_text}", classes="ct-choice-help",
                                             markup=False)
                err = FieldError()
                self._errors[name] = err
                yield err
            whole_err = FieldError()
            self._errors[""] = whole_err
            yield whole_err
        with Horizontal(classes="ct-section-buttons"):
            yield Button(self.spec.apply_label, id="ct-action-apply", variant="primary")

    def _find_field(self, widget_id: "str | None"):
        if not widget_id:
            return None
        for f in self._field_specs:
            if field_widget_id(f.name) == widget_id:
                return f
        return None

    def _write_through(self, f, value: object) -> None:
        set_field_value(self.state, self.spec.slug, f, value)
        msg = validate_value(f, value)
        err = self._errors.get(str(f.name))
        if err is not None:
            err.set_text(msg or "")

    def _make_list_change(self, f):
        widget_id = field_widget_id(f.name)

        def _on_change() -> None:
            widget = self.query_one(f"#{widget_id}", ListFieldWidget)
            self._write_through(f, list(widget.rows))

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

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "ct-action-apply":
            return
        answers = {str(f.name): get_field_value(self.state, self.spec.slug, f)
                   for f in self._field_specs}
        result = self.spec.apply(self.state, answers)
        for name, err in self._errors.items():
            if name:
                err.set_text((result.errors or {}).get(name, ""))
        self._errors[""].set_text((result.errors or {}).get("", "") if not result.ok else "")
        if not result.ok:
            return
        if result.state_updates:
            self.state.update(result.state_updates)
        body = self.query_one(f"#{self.id}-body", VerticalScroll)
        for line in result.info_lines:
            body.mount(Static(line, classes="ct-info-line"))
        app = getattr(self, "app", None)
        if app is not None and hasattr(app, "reload_all_panes"):
            await app.reload_all_panes()
        if app is not None and hasattr(app, "on_model_changed"):
            app.on_model_changed()
