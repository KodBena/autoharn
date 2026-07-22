#!/usr/bin/env python3
"""tools/configtree/fields.py -- typed field specs for a generic Textual hierarchical
configuration editor (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3/§6: "the entire UI should be a
library").

ZERO domain knowledge lives here: every field below is a UI primitive (text/choice/confirm/
repeated-row-list), never anything that knows what a "principal" or a "world" is -- that
vocabulary belongs entirely to a consumer's own section definitions (`tools/setup_tui/steps_*.py`
is the one instance today). ADR-0012 P2 (seam/port discipline): this module is the seam a
consumer hands typed data across; adding a new field SHAPE here would be a library change, but
adding a new SECTION never touches this file at all, only the consumer's own section list.

Four field kinds, matching the spec's own widget list (§3): `TextField` -> Textual `Input`,
`ChoiceField` -> `RadioSet`, `ConfirmField` -> `Checkbox`, `ListField` -> a scrollable row list
plus an "Add" button opening a small modal built from `item_fields` (repeatable sub-forms -- the
shape "register N principals in one visit" needs)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Union

from tools.configtree.ids import FieldName, Label, NodeId, ScopedFieldKey

# A validator returns an error message string on failure, or None when the value is acceptable.
# Applied to the RAW widget value (a str for TextField, the chosen key for ChoiceField) -- never
# to a ConfirmField (a Checkbox has no invalid state) or to a ListField itself (each of its
# per-row item_fields carries its own validators instead).
Validator = Callable[[str], "str | None"]


def _coerce_name(raw: "str | FieldName") -> FieldName:
    return raw if isinstance(raw, FieldName) else FieldName(raw)


def _coerce_label(raw: "str | Label") -> Label:
    return raw if isinstance(raw, Label) else Label(raw)


# SHARED-FIELD DOCTRINE (maintainer-diagnosed live defect, 2026-07-22: toggling a checkbox in one
# section toggled a "corresponding-ish" checkbox in ANOTHER section -- two sections' own
# `ConfirmField(name="run", ...)` were silently the SAME model slot, a bare-field-name collision;
# ADR-0012's own cancer C, "hidden state keyed by an insufficiently distinguishing key," read
# straight, plus the maintainer's standing "no bare types" rule, ledger row 1105). The STRUCTURAL
# fix: every field's live value is keyed by `ids.ScopedFieldKey(section, field)` by default --
# two sections' same-NAMED field CANNOT alias, because their model keys are never equal. `shared`
# is the one narrow, EXPLICIT, reviewed-per-field escape from that default: a field marked
# `shared=True` writes its live value to the bare top-level state key instead (`state[name]`) --
# reserved for the small, named set of facts multiple sections genuinely mean AS ONE (e.g. "the
# destination directory" -- fork-target/birth/boundary/observability/hydration/signed-genesis/
# principals-authority all have their OWN "dest" field, and mean the SAME real-world directory by
# it, not a coincidence of spelling). Defaulting to scoped and requiring an explicit, individually
# justified opt-in for sharing is the disciplined direction (ADR-0012's own "never settle for a
# weaker/less-safe default for scale/convenience" posture, read in the safety direction): the
# common case is unrepresentable-as-a-collision; the rare, real cross-section fact is a visible,
# reviewed exception, never an accident.


@dataclass(frozen=True)
class TextField:
    """One free-text input. `default` seeds the widget's initial value. `name`/`label` are
    checked, construction-IS-validation values (`ids.FieldName`/`ids.Label`) -- a plain `str` is
    accepted and coerced through the SAME checked constructor in `__post_init__` (frozen
    dataclasses use `object.__setattr__` for this, the standard idiom), so every call site keeps
    writing `TextField(name="dest", ...)` while the STORED value is always the checked type,
    never a bare string past construction. `shared` -- see this module's own "SHARED-FIELD
    DOCTRINE" note above; defaults to `False` (scoped, alias-proof)."""
    name: "str | FieldName"
    label: "str | Label"
    default: str = ""
    validator: Validator | None = None
    password: bool = False
    required: bool = True
    shared: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))


@dataclass(frozen=True)
class ChoiceField:
    """A closed set of mutually-exclusive options -- `options` is `((value, display-label), ...)`;
    `default`, if set, must be one of the option values. `shared` -- see this module's own
    "SHARED-FIELD DOCTRINE" note above."""
    name: "str | FieldName"
    label: "str | Label"
    options: tuple[tuple[str, str], ...]
    default: str | None = None
    shared: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if not self.options:
            raise ValueError(f"ChoiceField {self.name} must have at least one option")
        values = [v for v, _ in self.options]
        if self.default is not None and self.default not in values:
            raise ValueError(f"ChoiceField {self.name} default {self.default!r} not in {values}")


@dataclass(frozen=True)
class ConfirmField:
    """A yes/no toggle. `shared` -- see this module's own "SHARED-FIELD DOCTRINE" note above
    (the exact field kind the maintainer's own live defect report named -- every
    `ConfirmField(name="run", ...)` across every section defaults `shared=False`, precisely so
    two sections' own "run" toggles can never again collide)."""
    name: "str | FieldName"
    label: "str | Label"
    default: bool = False
    shared: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))


@dataclass(frozen=True)
class ListField:
    """A repeatable group of rows, each row itself a small sub-form (`item_fields` -- only
    `TextField`/`ChoiceField` sub-fields are supported; a nested `ListField` is not, ADR-0000:
    no type without a concrete instance that needs it). Rendered as the already-added rows (each
    summarized by `summarize`, a pure function of that row's `{sub_field_name: value}` dict) plus
    an "Add" button opening a modal built from `item_fields`; a "Remove" action deletes the
    selected row. The section's own `submit` reads the finished list back from `answers[name]`
    (`list[dict[str, str]]`, insertion order preserved) exactly like any other field's value.
    `shared` -- see this module's own "SHARED-FIELD DOCTRINE" note above; a `ListField`'s own rows
    are already scoped to its OWN `ListFieldWidget` instance, so `shared=True` here is a narrower
    case (no consumer currently needs it) kept only for uniformity across the four field kinds."""
    name: "str | FieldName"
    label: "str | Label"
    item_fields: tuple[Union[TextField, ChoiceField], ...]
    summarize: Callable[[dict], str]
    shared: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if not self.item_fields:
            raise ValueError(f"ListField {self.name} must have at least one item_field")


Field = Union[TextField, ChoiceField, ConfirmField, ListField]

FIELD_TYPES = (TextField, ChoiceField, ConfirmField, ListField)


def get_field_value(state: dict, section: NodeId, f: Field) -> object:
    """The ONE place a field's CURRENT live value is read out of the shared state -- a bare
    `state[str(name)]` for a field explicitly declared `shared=True` (the deliberate
    cross-section fact case, e.g. "dest"), or `state["_live_fields"][ScopedFieldKey(section,
    name)]` otherwise (the DEFAULT, alias-proof case -- see this module's own "SHARED-FIELD
    DOCTRINE" note). `set_field_value` is this function's write-side twin; every reader/writer of
    a field's live value calls one of this PAIR, so the two can never disagree about which slot a
    given field's value lives in."""
    if f.shared:
        return state.get(str(f.name), default_of(f))
    key = ScopedFieldKey(section=section, field=f.name)
    return state.get("_live_fields", {}).get(key, default_of(f))


def set_field_value(state: dict, section: NodeId, f: Field, value: object) -> None:
    """`get_field_value`'s write-side twin -- see its own docstring."""
    if f.shared:
        state[str(f.name)] = value
    else:
        key = ScopedFieldKey(section=section, field=f.name)
        state.setdefault("_live_fields", {})[key] = value


def default_of(f: Field) -> object:
    """A field's own default value -- the ONE place this is computed, shared by the live widget
    layer (a fresh field's initial value) and the model layer (`spec.section_status`'s own
    `state.get(name, default_of(f))` fallback for a field never yet touched)."""
    if isinstance(f, ConfirmField):
        return f.default
    if isinstance(f, ChoiceField):
        return f.default
    if isinstance(f, ListField):
        return []
    return getattr(f, "default", "")


def validate_value(f: Field, value: object) -> "str | None":
    """FIELD-LEVEL validity only -- required + this field's own `validator`/choice-membership.
    Never a cross-field or business-rule check (a world that already exists, a destination that
    is FOREIGN, gpg missing from PATH, ...) -- those live entirely in the section's own `submit`,
    which this library now calls exactly once, at commit time (design note, live-model rebuild:
    a per-section Save button meant form state and model state were two stores needing manual
    sync -- deleted; every field writes straight into the shared state on its own Changed event,
    and this function is what makes that write's IMMEDIATE inline-error feedback possible without
    invoking a section's real business logic, which may perform a live effect, on every
    keystroke)."""
    if isinstance(f, TextField):
        if f.required and not str(value).strip():
            return "required"
        if f.validator is not None and str(value).strip():
            return f.validator(str(value))
        return None
    if isinstance(f, ChoiceField):
        return None if value is not None else "choose one"
    return None  # ConfirmField/ListField: no field-level invalid state at this layer
