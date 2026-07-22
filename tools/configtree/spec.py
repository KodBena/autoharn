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

from tools.configtree.fields import (ElucidationValue, Field, _check_no_bare_pipe,
                                      get_field_value, validate_value)
from tools.configtree.ids import Label, NodeId
from tools.configtree.master_detail import AnyField, flatten_fields

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
    the REAL dependency mechanism is `blocked`. `description` -- this library's own section-level
    ELUCIDATION slot (maintainer round 5, ledger row 1115: "we were supposed to have an
    explanation for each feature, what our aspirations with it were, relative to existing
    standards"): optional prose rendered under the section title, before its fields, capped at
    measure like every other prose class this library renders."""
    slug: "str | NodeId"
    title: "str | Label"
    group: "str | Label"
    # `AnyField` (`master_detail.py`): `fields` may return a `MasterDetailField` alongside the
    # four primitive kinds -- `flatten_fields` is the ONE place that composite gets expanded back
    # to the flat per-name list this module's own answers/error/status functions operate over.
    fields: Callable[[dict], "tuple[AnyField, ...]"]
    submit: Callable[[dict, dict], SectionResult]
    precheck: "Callable[[dict], tuple[str, ...]] | None" = None
    blocked: "Callable[[dict], 'str | None'] | None" = None
    description: "ElucidationValue | None" = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "slug", self.slug if isinstance(self.slug, NodeId) else NodeId(self.slug))
        object.__setattr__(self, "title", self.title if isinstance(self.title, Label) else Label(self.title))
        object.__setattr__(self, "group", self.group if isinstance(self.group, Label) else Label(self.group))
        if isinstance(self.description, str):
            _check_no_bare_pipe(self.description, owner=f"SectionSpec {self.slug} description")


@dataclass(frozen=True)
class CommitSpec:
    """The library's own generic commit node (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2's
    "commit is a tree node enabled exactly when the record is complete"): a scrollable rendering
    of the resolved decision set (`render_summary`) plus ONE commit confirmation. `commit`
    performs the consumer's real commit act (or, under a dry run, only renders what it would have
    done -- a fact the CONSUMER's own `commit` closure decides, this library carries no dry-run
    concept of its own beyond the banner text `ConfigTreeApp` accepts).

    `reset`, OPTIONAL: called once at the START of every commit attempt, before any `submit` --
    the live-model rebuild's own submit sweep (`commit_pane.CommitPane`) calls every section's
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


@dataclass(frozen=True)
class ActionSpec:
    """An IMMEDIATE-action tree node -- the genre's own "load defaults" / "import a profile"
    picker (Qt/SAP settings dialogs' own preset affordance, ADR-0019 Rule 1), distinct from an
    ordinary `SectionSpec`: its `apply` runs THE INSTANT the operator presses this node's own
    button, never deferred to the commit sweep (maintainer round 5, ledger row 1115, defect C:
    "an in-UI affordance to load a configuration file ... usable at start" -- a config-loading
    action is useless if it only takes effect after every OTHER section has already been visited
    and committed). `apply(state, answers)` may merge facts straight into the shared `state`
    (`SectionResult.state_updates`, read the SAME way a section's own commit-time `submit` return
    is read) -- `tools.configtree.panes.ActionPane` does that merge AND asks `ConfigTreeApp` to
    recompose every ALREADY-MOUNTED `SectionPane` afterward, so a value this action seeded shows
    up as every other section's OWN live default immediately, not merely on next visit. Fields
    work exactly like a section's own (live write-through, inline validation) -- an action can
    still ask for input (e.g. "which template?") before its one button fires."""
    slug: "str | NodeId"
    title: "str | Label"
    group: "str | Label"
    fields: Callable[[dict], "tuple[Field, ...]"]
    apply: Callable[[dict, dict], SectionResult]
    apply_label: str = "Apply"
    description: "ElucidationValue | None" = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "slug", self.slug if isinstance(self.slug, NodeId) else NodeId(self.slug))
        object.__setattr__(self, "title", self.title if isinstance(self.title, Label) else Label(self.title))
        object.__setattr__(self, "group", self.group if isinstance(self.group, Label) else Label(self.group))
        if isinstance(self.description, str):
            _check_no_bare_pipe(self.description, owner=f"ActionSpec {self.slug} description")


def section_answers(spec: SectionSpec, state: dict) -> dict:
    """The section's CURRENT live answers -- one entry per field, read via `fields.
    get_field_value` (each field writes there on its own Changed event, live-model rebuild
    2026-07-22: no per-section Save button, no second store to keep in sync). A field NOT marked
    `shared=True` is read from ITS OWN section-scoped slot (`ids.ScopedFieldKey(spec.slug,
    name)`) -- never a bare top-level key another section's same-named field could alias (the
    maintainer-diagnosed live defect this scoping exists to make unrepresentable). The ONE place
    this projection is computed -- shared by `section_status`'s live validity check and by the
    commit node's own submit sweep (`commit_pane.CommitPane`), so both always agree on what a section's
    "current values" means."""
    return {str(f.name): get_field_value(state, spec.slug, f)
            for f in flatten_fields(spec.fields(state))}


def section_field_errors(spec: SectionSpec, state: dict) -> dict[str, str]:
    """FIELD-LEVEL errors only (`fields.validate_value` -- required/validator/choice-membership),
    computed fresh from the CURRENT live answers. Never a business-rule/cross-field refusal --
    those come from the section's own `submit`, called once at commit time, and are recorded
    separately (see `section_status`'s own `_commit_errors` check)."""
    answers = section_answers(spec, state)
    errors: dict[str, str] = {}
    for f in flatten_fields(spec.fields(state)):
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
    business-rule failure (`state["_commit_errors"][slug]`, written only by `commit_pane.CommitPane`'s
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


class DuplicatedSharedFieldError(ValueError):
    """A shared fact (`shared=True`) is declared by MORE THAN ONE section -- a typed refusal at
    load, never a runtime surprise (maintainer ruling, ADR-0019 + the maintainer's own verbatim
    ADR-0002 citation: "a duplicated mirror/projection of a value is a type error and refused on
    TUI start"). ANY second declaration of a shared field's name is refused -- editable or not;
    this library carries no read-only-reference rendering at all (struck entirely, same
    ruling) -- a shared fact renders in EXACTLY ONE owning section and nowhere else; every other
    section that needs the value reads it from the shared state directly in its own `submit`/
    `blocked`, never via a second field declaration."""


def validate_shared_ownership(sections: "tuple[SectionSpec, ...]") -> None:
    """The registry-wide check `ConfigTreeApp.__init__` runs automatically, at construction (spec
    §3 v2 + ADR-0019: single-editable-home for a shared fact is STRUCTURAL, not a review-time
    convention). Calls every section's own `fields({})` once (a structural pass -- ADR-0012 P1:
    a field's NAME/`shared` flag is part of its fixed declaration, never conditional on state
    content, so an empty dict is a legitimate probe) and groups every `shared=True` field by name;
    more than one declaring section for the SAME name raises `DuplicatedSharedFieldError`, naming
    the field and every section that declares it -- so a regression is caught the moment the App
    is built, never discovered live."""
    owners: dict[str, list[str]] = {}
    for spec in sections:
        for f in flatten_fields(spec.fields({})):
            if getattr(f, "shared", False):
                owners.setdefault(str(f.name), []).append(str(spec.slug))
    for name, declaring in owners.items():
        if len(declaring) > 1:
            raise DuplicatedSharedFieldError(
                f"tools.configtree: shared field {name!r} is declared editable by MORE THAN ONE "
                f"section ({', '.join(declaring)}) -- a shared fact renders in exactly one "
                f"owning section (ADR-0019 single-editable-home; the maintainer's own ADR-0002 "
                f"citation: a duplicated projection of a value is a type error). Pick ONE owner "
                f"and drop the field declaration from every other section listed above (they "
                f"read the value from shared state directly, never via a second field).")


def owner_of(sections: "tuple[SectionSpec, ...]", field_name: str) -> "SectionSpec | None":
    """The section that owns (declares) the shared field named `field_name`, or `None` if no
    section declares it. Used by consumers/tests that want to name the owner in a message; the
    library itself never renders a cross-reference to it (struck entirely -- see
    `DuplicatedSharedFieldError`'s own docstring)."""
    for spec in sections:
        for f in flatten_fields(spec.fields({})):
            if getattr(f, "shared", False) and str(f.name) == field_name:
                return spec
    return None


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
    button's own press is the ONLY thing that clears `_commit_errors` (`commit_pane.CommitPane.
    _run_submit_sweep`'s first line), so gating on it would make the retry unreachable. A section
    whose FIELDS are all locally valid is ready to be swept again, full stop; the sweep itself is
    what re-validates the business rule."""
    for s in sections:
        if s.blocked is not None and s.blocked(state):
            return False
        if section_field_errors(s, state):
            return False
    return True
