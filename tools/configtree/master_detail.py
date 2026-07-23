#!/usr/bin/env python3
"""tools/configtree/master_detail.py -- generic master-detail nesting for a `ListField`'s own
dependents (ADR-0019 Rule 4: "a dependent (foreign-keyed) entity is created and edited within its
parent's context, master-detail, never as a sibling flat list"; genre exemplar named by the
cycle-2 audit that minted this fix, `/home/bork/autoharn_series/cycle-2/AUDIT.md` finding #1:
Django/Rails admin inline formsets -- a parent model's own change page embeds its own children's
inline formset directly, add/edit/remove happening inside the parent's own context; a child is
never a second top-level list the operator cross-references by picking the parent from a
dropdown).

ZERO domain knowledge lives here (this module's own sibling discipline, `fields.py`'s own module
docstring): `MasterDetailField`/`DetailListField` know nothing about "principals" or
"competences" -- a consumer's own section (`tools.setup_tui.steps_principals_authority` is the
one instance today) declares the nesting; this module only knows "a list of rows, and N dependent
lists whose own rows are grouped by a key value drawn from a master row."

STORAGE IS UNCHANGED (ADR-0012 P1, "never a second implementation"): a `MasterDetailField`'s
`master` and every `DetailListField`'s own `list_field` ARE ordinary `ListField` instances -- their
live values still round-trip through `fields.get_field_value`/`set_field_value`, keyed by their
OWN name (`ids.ScopedFieldKey(section, name)`), exactly like a top-level `ListField` always has.
Master-detail nests the FORM RENDERING and the operator's own add/remove flow only; a consumer's
`submit(state, answers)` still reads `answers['register']`/`answers['competences']`/etc, the
IDENTICAL dict shape it always has -- nothing about the answers/state seam moved. `flatten_fields`
below is the ONE place a section's declared field tuple (which may now contain a
`MasterDetailField`) becomes the flat per-name list `spec.section_answers`/
`spec.section_field_errors`/the seeded-value-while-blocked check all still operate over.

LINK FIELD (the auto-injection contract): a `DetailListField`'s `link_field` names the key a
detail ROW carries that identifies which master row it belongs to (e.g. `link_field="name"` for a
competence naming the principal it is granted to, `link_field="subject"` for a relation --
ADR-0019 Rule 3, "one home per fact extends to the screen": a relation renders under its SUBJECT
principal only, the object side is a projection deliberately NOT mirrored there). This value is
auto-injected from the enclosing master row's own key (`MasterDetailField.master_key`) the INSTANT
a detail row is added inside that master row's own context -- it therefore must NEVER also appear
in the detail's own `item_fields` (checked below): the operator, already inside principal X's own
block, is never asked to re-pick "which principal" a row this obviously belongs to is for."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Union

from tools.configtree.fields import ElucidationValue, Field, ListField, _check_no_bare_pipe, _coerce_name
from tools.configtree.ids import FieldName


@dataclass(frozen=True)
class DetailListField:
    """One dependent sub-list nested under a `MasterDetailField`'s own master rows -- see this
    module's own docstring for the full account ("LINK FIELD"). `list_field` is the underlying
    storage (an ordinary `ListField` -- name/label/item_fields/summarize/help, read/written
    exactly like any top-level field would be)."""
    list_field: ListField
    link_field: "str | FieldName"

    def __post_init__(self) -> None:
        object.__setattr__(self, "link_field", _coerce_name(self.link_field))
        item_names = {str(f.name) for f in self.list_field.item_fields}
        if str(self.link_field) in item_names:
            raise ValueError(
                f"DetailListField {self.list_field.name}: link_field {self.link_field!r} must "
                f"NOT also appear in item_fields -- it is auto-injected from the enclosing "
                f"master row's own key (this module's docstring, 'LINK FIELD'), never re-picked "
                f"by the operator inside a context that already implies it")


@dataclass(frozen=True)
class MasterDetailField:
    """A master `ListField` whose rows own one or more `DetailListField` dependents, rendered
    nested under each master row (ADR-0019 Rule 4). `master_key` extracts the identity value from
    a master ROW dict (e.g. `lambda r: r["name"]`) that a detail row's own `link_field` value is
    matched against, to decide which master row's own block a detail row renders/adds under."""
    master: ListField
    details: "tuple[DetailListField, ...]"
    master_key: Callable[[dict], str]
    help: "ElucidationValue | None" = None

    def __post_init__(self) -> None:
        if not self.details:
            raise ValueError(
                f"MasterDetailField {self.master.name} must declare at least one "
                f"DetailListField -- a master list with no dependents is an ordinary ListField, "
                f"not a master-detail nesting")
        if isinstance(self.help, str):
            _check_no_bare_pipe(self.help, owner=f"MasterDetailField {self.master.name} help")

    @property
    def name(self) -> FieldName:
        return self.master.name

    @property
    def label(self):
        return self.master.label


AnyField = Union[Field, MasterDetailField]


def flatten_fields(section_fields: "tuple[AnyField, ...]") -> "tuple[Field, ...]":
    """Expands any `MasterDetailField` in `section_fields` into its own master `ListField` plus
    each `DetailListField`'s underlying `ListField`, in declaration order -- see this module's own
    docstring ("STORAGE IS UNCHANGED"). Every OTHER field passes through unchanged. The ONE place
    a section's declared field tuple becomes the flat per-name list `spec.section_answers`/
    `spec.section_field_errors`/`panes.SectionPane`'s own seeded-value-while-blocked check all
    operate over."""
    out: list[Field] = []
    for f in section_fields:
        if isinstance(f, MasterDetailField):
            out.append(f.master)
            out.extend(d.list_field for d in f.details)
        else:
            out.append(f)
    return tuple(out)
