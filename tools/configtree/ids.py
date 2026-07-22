#!/usr/bin/env python3
"""tools/configtree/ids.py -- checked value types for this library's own API surface (maintainer's
permanent rule, ledger row 1105: "no bare types ... construction IS validation"). An illegal
instance is UNCONSTRUCTABLE -- every contract below is enforced in `__post_init__`, never left to
a bypassable "checked by review" convention on an open constructor.

Four types, one per bare value this library's boundary carries:
  - `FieldName` -- a field's `name` (spliced into a Textual widget id, `ct-field-<name>`, and used
    as an `answers`/`state` dict key) -- contract: a valid identifier.
  - `Label` -- a field/section/group's human-readable label/title -- contract (modest, for a
    prose-like value): non-empty, single-line, printable.
  - `NodeId` -- a `SectionSpec.slug` -- contract: same identifier shape as `FieldName` (spliced
    into a tree-node/widget id and used as a state dict key); `unique_node_ids` below adds the
    collision guard a single `NodeId` cannot see on its own.
  - `ExitCode` -- a process exit code this library's own `App.exit`/`sys.exit` boundary uses --
    contract: a member of the closed vocabulary (0/1/2/3/130, or 128+signal).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_IDENT_RE = re.compile(r"^[a-z][a-z0-9_-]*$")

_CLOSED_EXIT_CODES = frozenset({0, 1, 2, 3, 130})


@dataclass(frozen=True)
class FieldName:
    value: str

    def __post_init__(self) -> None:
        if not _IDENT_RE.match(self.value):
            raise ValueError(
                f"FieldName {self.value!r} must match [a-z][a-z0-9_-]* (spliced into a Textual "
                f"widget id 'ct-field-<name>' and used as an answers/state dict key)")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Label:
    """A human-readable field/section/group label -- MODEST contract: non-empty, single-line,
    printable. Not a shape check beyond that -- a label's wording is content, not this type's
    business."""
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Label must be non-empty")
        if "\n" in self.value:
            raise ValueError(f"Label {self.value!r} must be single-line")
        if not self.value.isprintable():
            raise ValueError(f"Label {self.value!r} must be printable")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class NodeId:
    value: str

    def __post_init__(self) -> None:
        if not _IDENT_RE.match(self.value):
            raise ValueError(
                f"NodeId {self.value!r} must match [a-z][a-z0-9_-]* (spliced into a tree-node/"
                f"widget id and used as a state dict key)")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ExitCode:
    value: int

    def __post_init__(self) -> None:
        if self.value in _CLOSED_EXIT_CODES:
            return
        if 128 < self.value < 160:  # 128+signal, the standard shell convention (e.g. 128+SIGTERM)
            return
        raise ValueError(
            f"ExitCode {self.value} is not one of this app's closed vocabulary "
            f"{sorted(_CLOSED_EXIT_CODES)} or a 128+signal value")

    def __int__(self) -> int:
        return self.value


def unique_node_ids(slugs: "list[str]") -> "tuple[NodeId, ...]":
    """The ONE place a list of raw section slugs becomes a checked, DEDUPLICATED tuple of
    `NodeId` -- each slug's own shape is checked by `NodeId.__post_init__`; this function adds
    the collision guard a single `NodeId` construction cannot see on its own (two sections
    sharing one slug would collide in the widget-id/state-key namespace)."""
    seen: set[str] = set()
    out: list[NodeId] = []
    for raw in slugs:
        nid = NodeId(raw)
        if nid.value in seen:
            raise ValueError(f"duplicate NodeId {nid.value!r} in section registry")
        seen.add(nid.value)
        out.append(nid)
    return tuple(out)
