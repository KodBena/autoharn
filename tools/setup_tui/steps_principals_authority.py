#!/usr/bin/env python3
"""tools/setup_tui/steps_principals_authority.py -- the Principals & authority step's UI-free
core, ported from `screen_principals_authority`. The four repeatable sub-flows (register a
principal / grant a competence / add a relation / register a charter) are `ListField`s -- an
"Add" per row, instead of the pre-rebuild's `while ui.confirm("... now?")` loop; each ADD still
queues the exact same `principals_authority.*_act` Plan entry."""
from __future__ import annotations

from tools.configtree import (ChoiceField, ListField, NodeId, SectionResult, SectionSpec,
                               TextField, get_field_value)
from tools.setup_tui import checklist as ck
from tools.setup_tui import content, destination, feature_facts, principals_authority as pa
from tools.setup_tui.plan import PlanEntry
from tools.setup_tui.runner import legacy_led_path

_SLUG = NodeId("principals-authority")


def _register_field() -> ListField:
    # EMITTING SITE this fixed (maintainer round 4): `label=f"Class {class_opts}"` used to
    # splice the WHOLE options tuple -- value AND its full descriptive sentence, for all four
    # classes -- into a single field label (measured 394 chars; "relation" measured 613). A
    # closed-vocabulary value belongs in a `ChoiceField` (a real picker), not free text with the
    # entire vocabulary dumped into its label as a "hint" -- the content-level half of the fix.
    # ELUCIDATION (maintainer round 5, ledger row 1115 -- the SAME predecessor round DELETED the
    # descriptive sentence entirely instead of rendering it within measure, malicious compliance):
    # the full sentence (`content.PA_CLASS_CHOICES`'s own `label` half) is restored here as
    # `option_help` -- a short value as the RadioButton's own caption (never spliced whole, a
    # `RadioButton` caption does not wrap), the full sentence rendered as its own capped line
    # under the control instead (this library's own "ELUCIDATION DOCTRINE", tools/configtree/
    # fields.py).
    class_opts = tuple((v, v) for v, _ in content.PA_CLASS_CHOICES)
    class_help = {v: full for v, full in content.PA_CLASS_CHOICES}
    return ListField(
        name="register", label="Principal",
        item_fields=(TextField(name="name", label="Principal name"),
                     ChoiceField(name="agent_class", label="Class", options=class_opts,
                                 option_help=class_help),
                     TextField(name="purpose", label="Stated purpose")),
        summarize=lambda r: f"{r['name']} ({r['agent_class']}): {r['purpose']}",
        help=content.PA_LESSONS["register"],
        # `refresh_siblings`: the competence/relation/charter ChoiceFields below derive their own
        # principal-name options from THIS list's current rows -- a name typed in THIS visit must
        # show up as a pickable option in a sibling list without leaving the pane.
        refresh_siblings=True)


def _known_principal_names(state: dict, register_field: ListField) -> tuple[str, ...]:
    """Every principal name this section already knows about, right now: rows already typed into
    THIS VISIT's own "register" list (read live, before any commit) plus this world's real,
    pre-existing registered principals (a best-effort live read -- never blocks the form on a
    read failure, matching `pa_is_known`'s own posture below). Feeds the competence/relation/
    charter ChoiceFields (maintainer round 5, ledger row 1115, defect B: "the principal fields in
    competence grants and relations become choice widgets fed LIVE from the register list already
    in the model this same session, plus genuinely pre-existing principals")."""
    names: set[str] = set()
    for row in get_field_value(state, _SLUG, register_field) or []:
        if row.get("name"):
            names.add(row["name"])
    dest = state.get("dest", "").strip()
    if dest:
        try:
            names.update(p["name"] for p in pa.list_principals(dest))
        except Exception:  # noqa: BLE001 -- best-effort live read, never blocks the form
            pass
    return tuple(sorted(names))


def fields(state: dict) -> tuple:
    # NO "dest" field here (maintainer ruling 2026-07-22, ADR-0019 single-editable-home): the
    # destination directory is owned by Fork/target -- principals-authority reads the shared
    # fact straight out of state in `submit` below, never via a second field declaration (a
    # duplicated projection is refused at App construction,
    # `tools.configtree.spec.validate_shared_ownership`).
    rel_opts = tuple((v, v) for v, _ in content.PA_RELATION_CHOICES)
    rel_help = {v: full for v, full in content.PA_RELATION_CHOICES}
    register = _register_field()
    known = _known_principal_names(state, register)
    # A ChoiceField needs at least one option (tools.configtree.fields.ChoiceField.__post_init__)
    # -- before any principal is registered/known, offer one honest, non-selectable-as-real
    # sentinel naming the gap, rather than refusing to render the form at all.
    name_opts = tuple((n, n) for n in known) or (("", "(no principals known yet -- register one above first)"),)
    return (
        register,
        ListField(name="competences", label="Competence",
                  item_fields=(ChoiceField(name="name", label="Principal", options=name_opts),
                               TextField(name="activity", label="Activity"),
                               TextField(name="band", label="Band"),
                               TextField(name="basis", label="Basis")),
                  summarize=lambda r: f"{r['name']}: {r['activity']} ({r['band']}/{r['basis']})",
                  help=content.PA_LESSONS["competence"]),
        ListField(name="relations", label="Relation",
                  item_fields=(ChoiceField(name="subject", label="Subject principal", options=name_opts),
                               ChoiceField(name="relation", label="Relation", options=rel_opts,
                                           option_help=rel_help),
                               ChoiceField(name="object", label="Object principal", options=name_opts)),
                  summarize=lambda r: f"{r['subject']} {r['relation']} {r['object']}",
                  help=content.PA_LESSONS["relation"]),
        ListField(name="charters", label="Role charter",
                  item_fields=(ChoiceField(name="role", label="Role (registered principal)", options=name_opts),
                               TextField(name="path", label="Charter file path")),
                  summarize=lambda r: f"{r['role']} <- {r['path']}",
                  help=content.PA_LESSONS["charter"]),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    # "dest" is Fork/target's own owned field -- read the shared fact directly (already
    # guaranteed non-empty by `_blocked_needs_dest` below; this section is unreachable otherwise).
    dest = state.get("dest", "").strip()
    lines = [feature_facts.facts_block(["principals_authority"])]
    if not dest:
        return SectionResult(ok=False, errors={"": "destination (set in Fork/target) required"})

    dest_state = destination.classify_destination(dest)
    if dest_state.kind == destination.DestKind.FRESH and not state.get("dest_would_exist"):
        cl.add("principals-authority", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
        return SectionResult(ok=False, errors={"": "destination (set in Fork/target) does not "
                                             "exist -- run a birth first"})

    plan = state["_plan"]
    queued_names: set = set(state.get("planned_principal_names", set()))

    for row in answers["register"]:
        act, produces = pa.register_principal_act(dest, row["name"], row["agent_class"], row["purpose"])
        plan.append(PlanEntry(screen="principals-authority", item=f"register principal '{row['name']}'",
                               lesson=pa.LESSON_REGISTER, act=act, produces=produces))
        queued_names.add(row["name"])
        lines.append(f"queued: {act.render()}")

    for row in answers["competences"]:
        act, produces = pa.grant_competence_act(dest, row["name"], row["activity"], row["band"], row["basis"])
        plan.append(PlanEntry(screen="principals-authority",
                               item=f"grant competence '{row['activity']}' to '{row['name']}'",
                               lesson=pa.LESSON_COMPETENCE, act=act, produces=produces))
        lines.append(f"queued: {act.render()}")

    for row in answers["relations"]:
        act, produces = pa.relate_act(dest, row["subject"], row["relation"], row["object"])
        plan.append(PlanEntry(screen="principals-authority",
                               item=f"relate '{row['subject']}' {row['relation']} '{row['object']}'",
                               lesson=pa.LESSON_RELATION, act=act, produces=produces))
        lines.append(f"queued: {act.render()}")

    for row in answers["charters"]:
        role = row["role"]
        if role not in queued_names and not pa_is_known(dest, role):
            lines.append(f"NOTE: '{role}' is not yet a registered principal -- register it first "
                         "(a separate 'register a principal' row above) or the charter act may "
                         "fail at commit.")
        act, produces = pa.charter_register_act(dest, role, row["path"])
        plan.append(PlanEntry(screen="principals-authority", item=f"charter '{role}' <- {row['path']}",
                               lesson=pa.LESSON_CHARTER, act=act, produces=produces))
        lines.append(f"queued: {act.render()}")

    lines.append(pa.LESSON_WORKFLOW_POINTER)
    cl.add("principals-authority", "workflow on-ramp pointer", ck.WITNESSED, "pointer only, no mechanism")
    # NOTE: no "dest" in state_updates -- it is Fork/target's own owned fact already (ADR-0012
    # P1: one writer of one truth).
    return SectionResult(ok=True, state_updates={"planned_principal_names": queued_names},
                       info_lines=tuple(lines))


def pa_is_known(dest: str, name: str) -> bool:
    try:
        return pa.is_registered(dest, name)
    except Exception:  # noqa: BLE001 -- best-effort hint only, never blocks the queue
        return True  # unknown -- assume registered rather than nag on a read failure


def _blocked_needs_dest(state: dict) -> "str | None":
    """The REAL dependency edge (spec §3 v2: "declared as data ... typed edge"): registering a
    principal writes into the born world's own `led` -- there is no destination to write into
    until Fork/target or Birth has recorded one in the shared state."""
    if state.get("dest"):
        return None
    return "requires: Fork/target or Birth (a destination directory) to be set first"


STEP = SectionSpec(
    slug="principals-authority", title="Principals & authority", group="Authority & trust",
    fields=fields, submit=submit, blocked=_blocked_needs_dest,
    description=feature_facts.fact("principals_authority").line())
