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

from tools.configtree.fields import Field, get_field_value, validate_value
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
    concept of its own beyond the banner text `ConfigTreeApp` accepts).

    `reset`, OPTIONAL: called once at the START of every commit attempt, before any `submit` --
    the live-model rebuild's own submit sweep (`panes.CommitPane`) calls every section's
    `submit` FRESH each time Commit is pressed (a retry after fixing a business-rule refusal must
    re-derive the Plan from CURRENT field values, never append onto a stale one), so a consumer
    whose `submit` functions accumulate into a shared, consumer-owned structure under `state`
    (autoharn's own `state["_plan"]`/`state["_checklist"]`) needs a hook to reset THAT structure
    before the replay -- this library holds no opinion on what that structure even is (ADR-0012
    P2: zero autoharn knowledge), only that resetting it is the consumer's job, offered a clean
    place to do it."""
    render_summary: Callable[[dict], str]
    commit: Callable[[dict], SectionResult]
    confirm_label: str = "Commit"
    reset: "Callable[[dict], None] | None" = None


def section_answers(spec: SectionSpec, state: dict) -> dict:
    """The section's CURRENT live answers -- one entry per field, read via `fields.
    get_field_value` (each field writes there on its own Changed event, live-model rebuild
    2026-07-22: no per-section Save button, no second store to keep in sync). A field NOT marked
    `shared=True` is read from ITS OWN section-scoped slot (`ids.ScopedFieldKey(spec.slug,
    name)`) -- never a bare top-level key another section's same-named field could alias (the
    maintainer-diagnosed live defect this scoping exists to make unrepresentable). The ONE place
    this projection is computed -- shared by `section_status`'s live validity check and by the
    commit node's own submit sweep (`panes.CommitPane`), so both always agree on what a section's
    "current values" means."""
    return {str(f.name): get_field_value(state, spec.slug, f) for f in spec.fields(state)}


def section_field_errors(spec: SectionSpec, state: dict) -> dict[str, str]:
    """FIELD-LEVEL errors only (`fields.validate_value` -- required/validator/choice-membership),
    computed fresh from the CURRENT live answers. Never a business-rule/cross-field refusal --
    those come from the section's own `submit`, called once at commit time, and are recorded
    separately (see `section_status`'s own `_commit_errors` check)."""
    answers = section_answers(spec, state)
    errors: dict[str, str] = {}
    for f in spec.fields(state):
        name = str(f.name)
        msg = validate_value(f, answers[name])
        if msg:
            errors[name] = msg
    return errors


def section_status(spec: SectionSpec, state: dict) -> str:
    """The ONE place a section's tree-node status is computed -- a PURE function of `spec` and
    the CURRENT shared state, recomputed fresh on every call (live-model rebuild: no cached
    "done"/"visited" flag anywhere -- the tree reflects reality as the operator types, spec §3
    v2's own words). `blocked` outranks everything else: a section can be otherwise COMPLETE and
    still render BLOCKED if a later edit elsewhere broke its prerequisite. A recorded commit-time
    business-rule failure (`state["_commit_errors"][slug]`, written only by `panes.CommitPane`'s
    own submit sweep, the ONE place `SectionSpec.submit` is still called) reads INVALID until the
    operator edits that section again (which recomputes fresh here and naturally supersedes it).
    Otherwise: any required-but-empty or no-choice-made field reads INCOMPLETE; any field whose
    OWN validator rejects its current value reads INVALID; everything present and locally valid
    reads COMPLETE."""
    if spec.blocked is not None:
        reason = spec.blocked(state)
        if reason:
            return BLOCKED
    if str(spec.slug) in state.get("_commit_errors", {}):
        return INVALID
    errors = section_field_errors(spec, state)
    if any(msg not in ("required", "choose one") for msg in errors.values()):
        return INVALID
    if errors:
        return INCOMPLETE
    return COMPLETE


def all_sections_complete(sections: "tuple[SectionSpec, ...]", state: dict) -> bool:
    """The tree's own "how many sections read COMPLETE" reporting predicate (the status line,
    `spec §3 v2`'s "every section marked complete/incomplete/invalid/blocked"). Unlike
    `ready_for_commit` below, this DOES count a stale commit-sweep business-rule error against a
    section (it is still showing INVALID until the operator edits that section or the sweep
    clears it) -- reporting and "can I press Commit again" are deliberately different
    questions."""
    return all(section_status(s, state) == COMPLETE for s in sections)


def ready_for_commit(sections: "tuple[SectionSpec, ...]", state: dict) -> bool:
    """The commit BUTTON's own enablement predicate -- field-level readiness ONLY (not
    `blocked`ed, no required-missing, no validator failure), deliberately IGNORING a stale
    `_commit_errors` entry from a PRIOR failed sweep attempt. Without this distinction the button
    would deadlock itself: a failed sweep records `_commit_errors[slug]`, which
    `section_status`/`all_sections_complete` correctly reads as INVALID for DISPLAY, but if that
    same INVALID also gated the button, fixing the one field would never re-enable it -- the
    button's own press is the ONLY thing that clears `_commit_errors` (`panes.CommitPane._run_
    submit_sweep`'s first line), so gating on it would make the retry unreachable. A section
    whose FIELDS are all locally valid is ready to be swept again, full stop; the sweep itself is
    what re-validates the business rule."""
    for s in sections:
        if s.blocked is not None and s.blocked(state):
            return False
        if section_field_errors(s, state):
            return False
    return True
