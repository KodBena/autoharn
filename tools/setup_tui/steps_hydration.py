#!/usr/bin/env python3
"""tools/setup_tui/steps_hydration.py -- the Hydration step's UI-free core, ported from
`screen_hydration`. The per-ADR/per-durable-decision individual confirms become a `ListField` of
free-text slugs the operator names, checked against the live catalog at submit -- a small,
honest departure from the original's one-Checkbox-per-catalog-entry shape (which would make this
step's field COUNT open-ended and grow with the catalog; ADR-0007 discourages exactly that
un-bounded a form)."""
from __future__ import annotations

from tools.configtree import ConfirmField, ListField, SectionResult, SectionSpec, TextField
from tools.setup_tui import checklist as ck
from tools.setup_tui import durable_decisions, feature_facts
from tools.setup_tui.plan import CommandAct, PlanEntry
from tools.setup_tui.runner import legacy_led_path, resolve_led


def _decision_act(led: str, statement: str):
    return CommandAct(argv=(led, "decision", statement)), f"decision:{hash(statement) & 0xffffffff}"


def fields(state: dict) -> tuple:
    catalog_help = ", ".join(d.slug for d in durable_decisions.CATALOG)
    adrs = durable_decisions.list_adrs()
    adr_help = ", ".join(number for number, _, _ in adrs)
    return (
        ConfirmField(name="run", label="Run hydration now?", default=True),
        TextField(name="dest", label="Destination directory (with a led shim)",
                  default=state.get("dest", ""), shared=True),
        ConfirmField(name="fork_provenance", label="Hydrate: fork provenance?"),
        TextField(name="fork_provenance_statement", label="Statement for 'fork provenance' "
                  "decision row", required=False),
        ConfirmField(name="role_charters", label="Hydrate: role charters to register? (see "
                     "the Principals & authority step for the actual charter form)"),
        TextField(name="durable_decisions", label=f"Durable decisions to adopt, comma-separated "
                  f"slugs (available: {catalog_help})", required=False),
        TextField(name="adopt_adrs", label=f"ADR numbers to adopt, comma-separated "
                  f"(available: {adr_help})", required=False),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    lines = []
    if not answers["run"]:
        cl.add("hydration", "hydration", ck.SKIPPED, "operator skipped screen 10")
        return SectionResult(ok=True, info_lines=("hydration skipped by operator.",))

    dest = answers["dest"].strip()
    if not dest:
        return SectionResult(ok=False, errors={"dest": "required"})
    if state.get("dest_would_exist"):
        led = legacy_led_path(dest)
        cl.add("hydration", "led present", ck.DRY_SKIPPED, f"'{led}' queued earlier")
    else:
        led = resolve_led(dest)
        if led is None:
            cl.add("hydration", "led present", ck.WITNESSED, f"RED: no led under {dest}")
            return SectionResult(ok=False, errors={"dest": f"no led/legacy-led found under {dest}"})
        cl.add("hydration", "led present", ck.WITNESSED, led)

    plan = state["_plan"]
    selected_fragments: list[str] = []

    lines.append(feature_facts.facts_block(["hydration_fork_provenance"]))
    if answers["fork_provenance"]:
        stmt = answers["fork_provenance_statement"].strip()
        if not stmt:
            return SectionResult(ok=False, errors={"fork_provenance_statement": "required when fork "
                                                 "provenance is selected"})
        act, produces = _decision_act(led, stmt)
        plan.append(PlanEntry(screen="hydration", item="fork provenance", lesson="a real led "
                               "decision row", act=act, produces=produces))
        lines.append(f"queued: {act.render()}")
    else:
        cl.add("hydration", "fork provenance", ck.SKIPPED, "operator declined")

    lines.append(feature_facts.facts_block(["hydration_role_charters"]))
    if answers["role_charters"]:
        cl.add("hydration", "role charters to register", ck.WITNESSED,
               "see the Principals & authority step's 'Register a role charter' rows")
    else:
        cl.add("hydration", "role charters to register", ck.SKIPPED, "operator declined")

    wanted = {s.strip() for s in answers["durable_decisions"].split(",") if s.strip()}
    catalog_by_slug = {d.slug: d for d in durable_decisions.CATALOG}
    unknown = wanted - set(catalog_by_slug)
    if unknown:
        return SectionResult(ok=False, errors={"durable_decisions": f"unknown slug(s): {sorted(unknown)}"})
    lines.append(feature_facts.facts_block(["hydration_adr_adoption"]))
    for decision in durable_decisions.CATALOG:
        if decision.slug not in wanted:
            cl.add("hydration", decision.slug, ck.SKIPPED, "operator declined")
            continue
        act, produces = _decision_act(led, decision.hydrates)
        plan.append(PlanEntry(screen="hydration", item=decision.slug, lesson="a curated "
                               "durable-decision row + CLAUDE.md fragment", act=act, produces=produces))
        lines.append(f"queued: {act.render()}")
        selected_fragments.append(decision.claude_md)

    adrs = durable_decisions.list_adrs()
    wanted_adrs = {s.strip() for s in answers["adopt_adrs"].split(",") if s.strip()}
    known_adr_numbers = {number for number, _, _ in adrs}
    unknown_adrs = wanted_adrs - known_adr_numbers
    if unknown_adrs:
        return SectionResult(ok=False, errors={"adopt_adrs": f"unknown ADR number(s): {sorted(unknown_adrs)}"})
    for number, title, relpath in adrs:
        label = f"ADR-{number}: {title}"
        if number not in wanted_adrs:
            cl.add("hydration", f"adr adoption ({label})", ck.SKIPPED, "operator declined")
            continue
        statement = durable_decisions.adr_decision_statement(number, title, relpath)
        act, produces = _decision_act(led, statement)
        plan.append(PlanEntry(screen="hydration", item=f"adr adoption ({label})", lesson="a real "
                               "led decision row adopting this ADR", act=act, produces=produces))
        lines.append(f"queued: {act.render()}")
        selected_fragments.append(durable_decisions.adr_claude_md_fragment(number, title, relpath))

    claude_write = durable_decisions.hydration_claude_md_write_act(
        dest, selected_fragments, state.get("birth_produces", "birth-ran"))
    plan.append(PlanEntry(screen="hydration", item="CLAUDE.md durable-decisions section compiled",
                           lesson=f"{len(selected_fragments)} fragment(s) compiled between markers",
                           act=claude_write))
    lines.append(f"queued: write CLAUDE.md ({len(selected_fragments)} fragment(s))")
    return SectionResult(ok=True, state_updates={"dest": dest, "hydration_engaged": True},
                       info_lines=tuple(lines))


def _blocked_needs_dest(state: dict) -> "str | None":
    """Hydration writes CLAUDE.md/durable-decision rows into the born world's own destination --
    nothing to hydrate until Fork/target or Birth has recorded one."""
    if state.get("dest"):
        return None
    return "requires: Fork/target or Birth (a destination directory) to be set first"


STEP = SectionSpec(slug="hydration", title="Hydration", group="Runtime", fields=fields,
                    submit=submit, blocked=_blocked_needs_dest)
