#!/usr/bin/env python3
"""tools/configtree/spec.py -- the section contract a consumer hands this library
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2/§6). A `SectionSpec` is pure data plus two
pure-ish callables (`fields`/`submit` -- "pure-ish" because a consumer's `submit` is free to
perform real work, e.g. autoharn's core queues a `Plan` entry; this library never inspects what
`submit` does, only its typed return shape) plus one OPTIONAL callable, `blocked`, which is the
spec's own "dependencies declared as DATA" requirement: given the shared state, it returns a
human-readable reason string when this section's prerequisites are unmet, or `None` when it is
free to be worked on. Nothing in this module imports Textual or anything autoharn-specific --
ADR-0012 P2, the library's own one-way seam.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from tools.configtree.fields import Field
from tools.configtree.ids import Label, NodeId

# The closed vocabulary of a tree node's rendered status (spec §3 v2: "each node marked complete
# / incomplete / invalid / blocked-with-reason").
COMPLETE = "complete"
INCOMPLETE = "incomplete"
INVALID = "invalid"
BLOCKED = "blocked"

NODE_STATUSES = frozenset({COMPLETE, INCOMPLETE, INVALID, BLOCKED})


@dataclass
class SectionResult:
    """What a section's `submit` (or the commit node's `commit`) hands back.

    `ok=True` marks the section COMPLETE and merges `state_updates` into the shared state dict.
    `ok=False` marks the section INVALID; `errors` renders inline next to the named field (an
    empty-string key `""` is a whole-section error, shown above the fields rather than pinned to
    one). `info_lines` are appended to that section's own scrollable output pane either way."""
    ok: bool
    state_updates: dict | None = None
    errors: "dict[str, str] | None" = None
    info_lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class SectionSpec:
    """One configuration section -- one tree leaf, rendered as a form in the right pane.
    `fields`/`precheck`/`blocked` are called fresh every time the section is (re-)selected, with
    the CURRENT shared state, so a field's default (or a precheck's own read-only probe output,
    or a blocked reason) can depend on decisions made in any OTHER section, in any order --
    there is no positional "prior step" concept here, only the current shared state.

    `group` places this section under a named branch in the sidebar tree (spec §3 v2: "every
    section and subsection visible at once") -- purely a display grouping, never a dependency;
    the REAL dependency mechanism is `blocked`."""
    slug: "str | NodeId"
    title: "str | Label"
    group: "str | Label"
    fields: Callable[[dict], "tuple[Field, ...]"]
    submit: Callable[[dict, dict], SectionResult]
    precheck: "Callable[[dict], tuple[str, ...]] | None" = None
    blocked: "Callable[[dict], 'str | None'] | None" = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "slug", self.slug if isinstance(self.slug, NodeId) else NodeId(self.slug))
        object.__setattr__(self, "title", self.title if isinstance(self.title, Label) else Label(self.title))
        object.__setattr__(self, "group", self.group if isinstance(self.group, Label) else Label(self.group))


@dataclass(frozen=True)
class CommitSpec:
    """The library's own generic commit node (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2's
    "commit is a tree node enabled exactly when the record is complete"): a scrollable rendering
    of the resolved decision set (`render_summary`) plus ONE commit confirmation. `commit`
    performs the consumer's real commit act (or, under a dry run, only renders what it would have
    done -- a fact the CONSUMER's own `commit` closure decides, this library carries no dry-run
    concept of its own beyond the banner text `ConfigTreeApp` accepts)."""
    render_summary: Callable[[dict], str]
    commit: Callable[[dict], SectionResult]
    confirm_label: str = "Commit"


def section_status(spec: SectionSpec, state: dict) -> str:
    """The ONE place a section's tree-node status is computed -- a pure function of `spec` and
    the CURRENT shared state's own bookkeeping keys (`_section_done`/`_section_errors`, written
    only by `app.py`'s own submit handler). `blocked` outranks everything else: a section can be
    otherwise COMPLETE from an earlier visit and still render BLOCKED if a later edit elsewhere
    broke its prerequisite (re-checked every time, never cached)."""
    if spec.blocked is not None:
        reason = spec.blocked(state)
        if reason:
            return BLOCKED
    slug = str(spec.slug)
    if slug in state.get("_section_errors", {}):
        return INVALID
    if slug in state.get("_section_done", set()):
        return COMPLETE
    return INCOMPLETE


def all_sections_complete(sections: "tuple[SectionSpec, ...]", state: dict) -> bool:
    """The commit node's own enablement predicate (spec §3 v2, verbatim): "enabled exactly when
    the record is complete" -- every section must have been visited and saved without error."""
    return all(section_status(s, state) == COMPLETE for s in sections)
