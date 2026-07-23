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

from tools.configtree.elucidation import (DescriptionElement, ElucidationHeading,
                                           ElucidationItem, ElucidationValue, PROVENANCE_LABEL,
                                           _check_elucidation_text, _check_no_bare_pipe)
from tools.configtree.ids import FieldName, Label, NodeId, ScopedFieldKey

# Re-exported here so every EXISTING call site in this file (and every consumer importing them
# FROM fields.py, the historical home) keeps working unchanged -- `elucidation.py` is where these
# now live (ADR-0007: no file over 400 lines), `fields.py` stays their public re-export point.
__all_elucidation__ = ("DescriptionElement", "ElucidationHeading", "ElucidationItem",
                        "ElucidationValue", "PROVENANCE_LABEL")

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


# ELUCIDATION DOCTRINE (maintainer round 5, ledger row 1115 -- the censure this note answers: "we
# were supposed to have an explanation for each feature, what our aspirations with it were,
# relative to existing standards" -- and a prior round's fix for readable-measure DELETED the
# elucidating option descriptions instead of rendering them within measure, malicious compliance).
# Every field kind below carries an OPTIONAL `help` string -- prose shown UNDER the field (Qt-
# style: description under the control, the "juxtaposed text" the maintainer named as this
# terminal's tooltip-equivalent), rendered by `tools.configtree.widgets`/`panes` at the SAME
# MEASURE cap every other prose class in this library uses (`tools.configtree.measure.MEASURE`).
# `ChoiceField`/`MultiChoiceField` ALSO carry a PER-OPTION help string (`option_help`, keyed by
# option value) -- the closed-vocabulary case: a `RadioButton`/`Checkbox` caption does not wrap
# (`widgets.build_field_widget`'s own docstring), so a long descriptive sentence about ONE option
# is never spliced into that option's own caption; it renders as its own capped line in a details
# region under the control instead, restoring exactly the content the deleted mirror used to
# carry, properly measured this time -- deletion was never the fix for a measure violation, only
# WRAPPING was.


# TOUCHED-FIELD TRACKING (maintainer round 5, ledger row 1115: "the checklist then recorded
# operator-declined for defaults the operator never touched -- false attribution of choice").
# `set_field_value` (this module's ONE write-through choke point, called ONLY from a real
# Textual Changed-message handler -- see `tools.configtree.panes.SectionPane._write_through`'s own
# docstring) ALSO marks the field TOUCHED, in a set keyed the same way its own live value is keyed
# (`ids.ScopedFieldKey` for a scoped field, the bare name for a `shared=True` one). A field whose
# CURRENT value merely equals its own compile-time default because the operator never interacted
# with the widget at all is thereby distinguishable, structurally, from a field the operator
# visited and left/set at that same value on purpose -- `is_field_touched` below is the ONE place
# a consumer's own `submit` asks the question, so a decision-record's wording (operator DECLINED
# vs the value is merely DEFAULTED, never touched) is never guessed from the bare value alone.


@dataclass(frozen=True)
class TextField:
    """One free-text input. `default` seeds the widget's initial value. `name`/`label` are
    checked, construction-IS-validation values (`ids.FieldName`/`ids.Label`) -- a plain `str` is
    accepted and coerced through the SAME checked constructor in `__post_init__` (frozen
    dataclasses use `object.__setattr__` for this, the standard idiom), so every call site keeps
    writing `TextField(name="dest", ...)` while the STORED value is always the checked type,
    never a bare string past construction. `shared` -- see this module's own "SHARED-FIELD
    DOCTRINE" note above; defaults to `False` (scoped, alias-proof). `help` -- see this module's
    own "ELUCIDATION DOCTRINE" note below; optional prose rendered under the field, capped at
    measure, never the field's only source of meaning (the label always stands alone)."""
    name: "str | FieldName"
    label: "str | Label"
    default: str = ""
    validator: Validator | None = None
    password: bool = False
    required: bool = True
    shared: bool = False
    help: "ElucidationValue | None" = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if isinstance(self.help, str):
            _check_no_bare_pipe(self.help, owner=f"TextField {self.name} help")


@dataclass(frozen=True)
class ChoiceField:
    """A closed set of mutually-exclusive options -- `options` is `((value, display-label), ...)`;
    `default`, if set, must be one of the option values. `shared` -- see this module's own
    "SHARED-FIELD DOCTRINE" note above. `help`/`option_help` -- see this module's own
    "ELUCIDATION DOCTRINE" note above: `help` is whole-field prose, `option_help` is an optional
    `{option_value: ElucidationValue}` map -- every key must be one of `options`' own values
    (checked below), rendered as its own capped line (or typed element group) under the control
    (a `RadioButton` caption does not wrap, so a long per-option sentence is never spliced into
    the caption itself)."""
    name: "str | FieldName"
    label: "str | Label"
    options: tuple[tuple[str, str], ...]
    default: str | None = None
    shared: bool = False
    help: "ElucidationValue | None" = None
    option_help: "dict[str, ElucidationValue] | None" = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if not self.options:
            raise ValueError(f"ChoiceField {self.name} must have at least one option")
        values = [v for v, _ in self.options]
        if self.default is not None and self.default not in values:
            raise ValueError(f"ChoiceField {self.name} default {self.default!r} not in {values}")
        if isinstance(self.help, str):
            _check_no_bare_pipe(self.help, owner=f"ChoiceField {self.name} help")
        if self.option_help is not None:
            unknown = set(self.option_help) - set(values)
            if unknown:
                raise ValueError(f"ChoiceField {self.name} option_help names unknown option(s): "
                                  f"{sorted(unknown)}")
            for opt_val, opt_help in self.option_help.items():
                if isinstance(opt_help, str):
                    _check_no_bare_pipe(opt_help, owner=f"ChoiceField {self.name} option_help[{opt_val!r}]")


@dataclass(frozen=True)
class ConfirmField:
    """A yes/no toggle. `shared` -- see this module's own "SHARED-FIELD DOCTRINE" note above
    (the exact field kind the maintainer's own live defect report named -- every
    `ConfirmField(name="run", ...)` across every section defaults `shared=False`, precisely so
    two sections' own "run" toggles can never again collide). `help` -- see this module's own
    "ELUCIDATION DOCTRINE" note above."""
    name: "str | FieldName"
    label: "str | Label"
    default: bool = False
    shared: bool = False
    help: "ElucidationValue | None" = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if isinstance(self.help, str):
            _check_no_bare_pipe(self.help, owner=f"ConfirmField {self.name} help")


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
    case (no consumer currently needs it) kept only for uniformity across the four field kinds.
    `help` -- see this module's own "ELUCIDATION DOCTRINE" note above. `refresh_siblings` -- set
    True when THIS list's own rows are read (via `get_field_value`) by another field's `options`
    computation in the SAME section's `fields(state)` callback (e.g. a `ChoiceField` picker whose
    choices are "principals registered so far, this visit") -- forces the whole `SectionPane` to
    recompose right after an Add/Remove of THIS list, so a sibling field's derived choices reflect
    the change on the SAME visit, not only the next time the section is (re-)selected."""
    name: "str | FieldName"
    label: "str | Label"
    item_fields: tuple[Union[TextField, ChoiceField], ...]
    summarize: Callable[[dict], str]
    shared: bool = False
    help: "ElucidationValue | None" = None
    refresh_siblings: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if not self.item_fields:
            raise ValueError(f"ListField {self.name} must have at least one item_field")
        if isinstance(self.help, str):
            _check_no_bare_pipe(self.help, owner=f"ListField {self.name} help")


@dataclass(frozen=True)
class MultiChoiceField:
    """A CLOSED, finite catalog rendered as a checkbox GROUP -- one checkbox per option, each
    option's own elucidation juxtaposed under it (this module's own "ELUCIDATION DOCTRINE" note),
    never a free-text delimited string over a finite vocabulary (maintainer round 5, ledger row
    1115: "I had to hand-edit a comma-separated list instead of ticking checkboxes with tooltips
    ... for both ADR and the durable decisions" -- the same class as a closed-vocabulary value
    entered as free text, one rung worse since it also demands the operator know the exact
    slugs). The model VALUE is a `list[str]` (option values currently checked, catalog order,
    never a joined string) -- `submit`/config round-trips read/write this SAME typed list; only a
    TOML file's own array-of-strings representation is an honest re-encoding of it, never a
    comma-joined scalar. `shared` -- see this module's own "SHARED-FIELD DOCTRINE" note above.

    `groups` (MEDIUM audit finding, ledger row 1130's own sibling audit -- "hydration's
    36-checkbox catalog renders as one unbroken scroll"): OPTIONAL `{option_value: heading_text}`
    -- an option whose value is a key here gets a REAL sub-heading (`widgets.py`'s own
    `ElucidationHeading` rendering, the SAME machinery `substrate`'s Existing-db/Dedicated-db
    groups already use) rendered immediately before it, IF that heading text differs from the
    heading already showing (so a contiguous run of options sharing one heading gets it ONCE, at
    the top of the run, not repeated per option). Every option named here must be one of
    `options`' own values (checked below, same discipline as `option_help`); an option NOT named
    here renders with no heading above it (legal -- grouping is optional, not every catalog needs
    one)."""
    name: "str | FieldName"
    label: "str | Label"
    options: tuple[tuple[str, str], ...]
    default: tuple[str, ...] = ()
    shared: bool = False
    help: "ElucidationValue | None" = None
    option_help: "dict[str, ElucidationValue] | None" = None
    groups: "dict[str, str] | None" = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _coerce_name(self.name))
        object.__setattr__(self, "label", _coerce_label(self.label))
        if not self.options:
            raise ValueError(f"MultiChoiceField {self.name} must have at least one option")
        values = [v for v, _ in self.options]
        dupes = {v for v in values if values.count(v) > 1}
        if dupes:
            # Construction-time refusal, not a widget crash discovered live: two options sharing
            # one VALUE would mint two checkboxes claiming the same identity (and, concretely,
            # the same widget id -- this is exactly how a catalog-derivation bug upstream, e.g.
            # two files parsing to the SAME ADR number, was first caught here).
            raise ValueError(f"MultiChoiceField {self.name} has duplicate option value(s): "
                              f"{sorted(dupes)} -- every option value must be unique")
        unknown_default = set(self.default) - set(values)
        if unknown_default:
            raise ValueError(f"MultiChoiceField {self.name} default names unknown option(s): "
                              f"{sorted(unknown_default)}")
        if isinstance(self.help, str):
            _check_no_bare_pipe(self.help, owner=f"MultiChoiceField {self.name} help")
        if self.option_help is not None:
            unknown = set(self.option_help) - set(values)
            if unknown:
                raise ValueError(f"MultiChoiceField {self.name} option_help names unknown "
                                  f"option(s): {sorted(unknown)}")
            for opt_val, opt_help in self.option_help.items():
                if isinstance(opt_help, str):
                    _check_no_bare_pipe(opt_help,
                                         owner=f"MultiChoiceField {self.name} option_help[{opt_val!r}]")
        if self.groups is not None:
            unknown_g = set(self.groups) - set(values)
            if unknown_g:
                raise ValueError(f"MultiChoiceField {self.name} groups names unknown "
                                  f"option(s): {sorted(unknown_g)}")
            for heading in self.groups.values():
                _check_no_bare_pipe(heading, owner=f"MultiChoiceField {self.name} groups heading")


Field = Union[TextField, ChoiceField, ConfirmField, ListField, MultiChoiceField]

FIELD_TYPES = (TextField, ChoiceField, ConfirmField, ListField, MultiChoiceField)


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
    """`get_field_value`'s write-side twin -- see its own docstring. ALSO marks the field TOUCHED
    (this module's own "TOUCHED-FIELD TRACKING" note above) -- this function is called ONLY from
    a real Changed-message handler (`tools.configtree.panes.SectionPane._write_through`/its
    `ListField`-change and `MultiChoiceField`-change callbacks), never at compose time for a
    field's mere default, so every call here IS a genuine operator interaction."""
    if f.shared:
        state[str(f.name)] = value
        state.setdefault("_touched_shared", set()).add(str(f.name))
    else:
        key = ScopedFieldKey(section=section, field=f.name)
        state.setdefault("_live_fields", {})[key] = value
        state.setdefault("_touched_scoped", set()).add(key)


def is_field_touched(state: dict, section: "str | NodeId", field_name: "str | FieldName") -> bool:
    """Has the operator EVER written through this field's own slot this run (`set_field_value`
    having been called for it at least once), as opposed to the value merely reading its
    compile-time default because nothing ever touched the widget? Takes bare strings (not a
    `Field` instance) so a consumer's own `submit(state, answers)` -- which has `state` but not
    the `Field` objects `fields(state)` built -- can ask this question without reconstructing
    them. `section`/`field_name` are coerced through the SAME checked constructors every other
    entry point uses, so a typo here fails loudly rather than silently reading "never touched"."""
    section_id = section if isinstance(section, NodeId) else NodeId(section)
    name = field_name if isinstance(field_name, FieldName) else FieldName(field_name)
    key = ScopedFieldKey(section=section_id, field=name)
    if key in state.get("_touched_scoped", set()):
        return True
    return str(name) in state.get("_touched_shared", set())


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
    if isinstance(f, MultiChoiceField):
        return list(f.default)
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
    return None  # ConfirmField/ListField/MultiChoiceField: no field-level invalid state here
