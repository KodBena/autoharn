#!/usr/bin/env python3
"""tools/setup_tui/steps_principals_authority.py -- the Principals & authority step's UI-free
core, ported from `screen_principals_authority`. The four repeatable sub-flows (register a
principal / grant a competence / add a relation / register a charter) are `ListField`s -- an
"Add" per row, instead of the pre-rebuild's `while ui.confirm("... now?")` loop; each ADD still
queues the exact same `principals_authority.*_act` Plan entry."""
from __future__ import annotations

from tools.configtree import ListField, SectionResult, SectionSpec, TextField
from tools.setup_tui import checklist as ck
from tools.setup_tui import content, destination, feature_facts, principals_authority as pa
from tools.setup_tui.plan import PlanEntry
from tools.setup_tui.runner import legacy_led_path


def fields(state: dict) -> tuple:
    class_opts = tuple(content.PA_CLASS_CHOICES)
    rel_opts = tuple(content.PA_RELATION_CHOICES)
    return (
        TextField(name="dest", label="Destination directory (the born world)",
                  default=state.get("dest", ""), shared=True),
        ListField(name="register", label="Register a principal",
                  item_fields=(TextField(name="name", label="Principal name"),
                               TextField(name="agent_class", label=f"Class {class_opts}"),
                               TextField(name="purpose", label="Stated purpose")),
                  summarize=lambda r: f"{r['name']} ({r['agent_class']}): {r['purpose']}"),
        ListField(name="competences", label="Grant a competence",
                  item_fields=(TextField(name="name", label="Principal name"),
                               TextField(name="activity", label="Activity"),
                               TextField(name="band", label="Band"),
                               TextField(name="basis", label="Basis")),
                  summarize=lambda r: f"{r['name']}: {r['activity']} ({r['band']}/{r['basis']})"),
        ListField(name="relations", label="Add a typed relation",
                  item_fields=(TextField(name="subject", label="Subject principal"),
                               TextField(name="relation", label=f"Relation {rel_opts}"),
                               TextField(name="object", label="Object principal")),
                  summarize=lambda r: f"{r['subject']} {r['relation']} {r['object']}"),
        ListField(name="charters", label="Register a role charter",
                  item_fields=(TextField(name="role", label="Role name (registered principal)"),
                               TextField(name="path", label="Charter file path")),
                  summarize=lambda r: f"{r['role']} <- {r['path']}"),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    dest = answers["dest"].strip()
    lines = [feature_facts.facts_block(["principals_authority"])]
    if not dest:
        return SectionResult(ok=False, errors={"dest": "required"})

    dest_state = destination.classify_destination(dest)
    if dest_state.kind == destination.DestKind.FRESH and not state.get("dest_would_exist"):
        cl.add("principals-authority", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
        return SectionResult(ok=False, errors={"dest": "does not exist -- run a birth first"})

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
    return SectionResult(ok=True, state_updates={"dest": dest, "planned_principal_names": queued_names},
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


STEP = SectionSpec(slug="principals-authority", title="Principals & authority",
                    group="Authority & trust", fields=fields, submit=submit,
                    blocked=_blocked_needs_dest)
