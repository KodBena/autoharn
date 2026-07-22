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

from tools.configtree.ids import FieldName, Label

# A validator returns an error message string on failure, or None when the value is acceptable.
# Applied to the RAW widget value (a str for TextField, the chosen key for ChoiceField) -- never
# to a ConfirmField (a Checkbox has no invalid state) or to a ListField itself (each of its
# per-row item_fields carries its own validators instead).
Validator = Callable[[str], "str | None"]


def _coerce_name(raw: "str | FieldName") -> FieldName:
    return raw if isinstance(raw, FieldName) else FieldName(raw)


def _coerce_label(raw: "str | Label") -> Label:
    return raw if isinstance(raw, Label) else Label(raw)


@dataclass(frozen=True)
class TextField:
    """One free-text input. `default` seeds the widget's initial value. `name`/`label` are
    checked, construction-IS-validation values (`ids.FieldName`/`ids.Label`) -- a plain `str` is
    accepted and coerced through the SAME checked constructor in `__post_init__` (frozen
    dataclasses use `object.__setattr__` for this, the standard idiom), so every call site keeps
    writing `TextField(name="dest", ...)` while the STORED value is always the checked type,
    never a bare string past construction."""
    name: "str | FieldName"
    label: "str | Label"
    default: str = ""
    validator: Validator | None = None
    password: bool = False
    required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))


@dataclass(frozen=True)
class ChoiceField:
    """A closed set of mutually-exclusive options -- `options` is `((value, display-label), ...)`;
    `default`, if set, must be one of the option values."""
    name: "str | FieldName"
    label: "str | Label"
    options: tuple[tuple[str, str], ...]
    default: str | None = None

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
    """A yes/no toggle."""
    name: "str | FieldName"
    label: "str | Label"
    default: bool = False

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
    (`list[dict[str, str]]`, insertion order preserved) exactly like any other field's value."""
    name: "str | FieldName"
    label: "str | Label"
    item_fields: tuple[Union[TextField, ChoiceField], ...]
    summarize: Callable[[dict], str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if not self.item_fields:
            raise ValueError(f"ListField {self.name} must have at least one item_field")


Field = Union[TextField, ChoiceField, ConfirmField, ListField]

FIELD_TYPES = (TextField, ChoiceField, ConfirmField, ListField)
