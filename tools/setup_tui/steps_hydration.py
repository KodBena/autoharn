#!/usr/bin/env python3
"""tools/setup_tui/steps_hydration.py -- the Hydration step's UI-free core, ported from
`screen_hydration`. The durable-decisions catalog and the ADR-adoption submenu are BOTH closed,
finite vocabularies -- rendered as `MultiChoiceField` checkbox groups (one checkbox per catalog
entry, its own elucidation juxtaposed under it), never a free-text comma-separated list of slugs
the operator has to already know by heart (maintainer round 5, ledger row 1115, defect F: "I had
to hand-edit a comma-separated list instead of ticking checkboxes with tooltips ... for both ADR
and the durable decisions"). The model value is the SAME typed `list[str]` everywhere -- the
comma-joined string dies here and in `config_seam.answers_for_from_config`; `world-config.toml`
already emitted a TOML array for both keys (`config_file.render_toml`'s own list handling), so no
change was needed on that side."""
from __future__ import annotations

from tools.configtree import (ConfirmField, MultiChoiceField, SectionResult, SectionSpec,
                               TextField, is_field_touched)
from tools.setup_tui import checklist as ck
from tools.setup_tui import durable_decisions, feature_facts
from tools.setup_tui.plan import CommandAct, PlanEntry
from tools.setup_tui.runner import legacy_led_path, resolve_led

_SLUG = "hydration"

# GROUPING (MEDIUM audit finding, ledger row 1130's own sibling audit: "hydration's 36-checkbox
# catalog renders as one ~218-row unbroken scroll"). Both catalogs get MECHANICAL sub-headings
# (derived from existing data, never a hand-authored taxonomy that could misclassify a rule's own
# content -- ADR-0012 P10's own "data is not code" boundary read the safe direction: inventing a
# thematic category per entry is a CONTENT judgment call this module has no business making
# unreviewed): ADRs group by their own decade (0000s/0010s/...), a grouping that already exists
# in the numbering itself; durable decisions, which carry no numeric or thematic axis in their
# own data, group by fixed-size chunks in catalog (registration) order -- a real visual break
# every `DURABLE_DECISION_GROUP_SIZE` entries, same rationale as `widgets.
# MULTICHOICE_FILTER_THRESHOLD` (Miller 1968's glanceable-span heuristic), not a claim that
# entries N..N+4 share a theme.
DURABLE_DECISION_GROUP_SIZE = 5


def _decision_act(led: str, statement: str):
    return CommandAct(argv=(led, "decision", statement)), f"decision:{hash(statement) & 0xffffffff}"


def _durable_decision_groups(catalog: list) -> dict[str, str]:
    groups: dict[str, str] = {}
    for i, d in enumerate(catalog):
        lo = (i // DURABLE_DECISION_GROUP_SIZE) * DURABLE_DECISION_GROUP_SIZE + 1
        hi = min(lo + DURABLE_DECISION_GROUP_SIZE - 1, len(catalog))
        groups[d.slug] = f"Durable decisions {lo}-{hi} of {len(catalog)}"
    return groups


def _adr_decade_groups(adrs: list) -> dict[str, str]:
    groups: dict[str, str] = {}
    for number, _, _ in adrs:
        decade = (int(number) // 10) * 10
        groups[number] = f"ADR {decade:04d}s"
    return groups


def fields(state: dict) -> tuple:
    # NO "dest" field here (maintainer ruling 2026-07-22, ADR-0019 single-editable-home): the
    # destination directory is owned by Fork/target -- hydration reads the shared fact straight
    # out of state in `submit` below, never via a second field declaration (a duplicated
    # projection is refused at App construction, `tools.configtree.spec.validate_shared_ownership`).
    decision_opts = tuple((d.slug, d.slug) for d in durable_decisions.CATALOG)
    decision_help = {d.slug: d.elements() for d in durable_decisions.CATALOG}
    decision_groups = _durable_decision_groups(durable_decisions.CATALOG)
    adrs = durable_decisions.list_adrs()
    adr_opts = tuple((number, f"ADR-{number}: {title}") for number, title, _ in adrs)
    adr_groups = _adr_decade_groups(adrs)
    # ORIENTATION, NOT THE LAW (maintainer round-6 addendum: "a pointer is not an elucidation"):
    # a real 1-3 sentence synopsis of what the ADR binds you to, THEN the file-path pointer --
    # `durable_decisions.adr_synopsis_elements` is the one place this is built, from
    # `content.ADR_SYNOPSES` data, never hardcoded here.
    adr_help = {number: durable_decisions.adr_synopsis_elements(number, relpath)
                for number, _, relpath in adrs}
    return (
        ConfirmField(name="run", label="Run hydration now?", default=True,
                     help="Compiles CLAUDE.md durable-decision fragments and files real 'led "
                     "decision' rows for whatever is selected below -- turning this off skips "
                     "the whole step, nothing selected below is applied."),
        ConfirmField(name="fork_provenance", label="Hydrate: fork provenance?",
                     help=feature_facts.fact("hydration_fork_provenance").elements()),
        TextField(name="fork_provenance_statement", label="Statement for 'fork provenance' "
                  "decision row", required=False),
        ConfirmField(name="role_charters", label="Hydrate: role charters to register? (see "
                     "the Principals & authority step for the actual charter form)",
                     help=feature_facts.fact("hydration_role_charters").elements()),
        MultiChoiceField(name="durable_decisions", label="Durable decisions to adopt",
                          options=decision_opts, option_help=decision_help,
                          groups=decision_groups,
                          help="Each selected entry writes one real 'led decision' row and "
                          "compiles a CLAUDE.md fragment for the new world -- the why/citation "
                          "for each is shown under its own checkbox."),
        MultiChoiceField(name="adopt_adrs", label="ADR numbers to adopt", options=adr_opts,
                          option_help=adr_help, groups=adr_groups,
                          help="Each selected ADR gets one real 'led decision' row and a "
                          "CLAUDE.md pointer line naming it."),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    if not answers["run"]:
        touched = is_field_touched(state, _SLUG, "run")
        cl.add("hydration", "hydration", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")
        return SectionResult(ok=True, info_lines=("hydration skipped by operator.",))

    # "dest" is Fork/target's own owned field -- read the shared fact directly (already
    # guaranteed non-empty by `_blocked_needs_dest` below; this section is unreachable otherwise).
    dest = state.get("dest", "").strip()
    if not dest:
        return SectionResult(ok=False, errors={"": "destination (set in Fork/target) required"})
    if state.get("dest_would_exist"):
        led = legacy_led_path(dest)
        cl.add("hydration", "led present", ck.DRY_SKIPPED, f"'{led}' queued earlier")
    else:
        led = resolve_led(dest)
        if led is None:
            cl.add("hydration", "led present", ck.WITNESSED, f"RED: no led under {dest}")
            return SectionResult(ok=False, errors={"": f"no led/legacy-led found under {dest} "
                                                 "(destination set in Fork/target)"})
        cl.add("hydration", "led present", ck.WITNESSED, led)

    plan = state["_plan"]
    selected_fragments: list[str] = []

    lines = [feature_facts.facts_block(["hydration_fork_provenance"])]
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
        touched = is_field_touched(state, _SLUG, "fork_provenance")
        cl.add("hydration", "fork provenance", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")

    lines.append(feature_facts.facts_block(["hydration_role_charters"]))
    if answers["role_charters"]:
        cl.add("hydration", "role charters to register", ck.WITNESSED,
               "see the Principals & authority step's 'Register a role charter' rows")
    else:
        touched = is_field_touched(state, _SLUG, "role_charters")
        cl.add("hydration", "role charters to register", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")

    wanted = set(answers["durable_decisions"])
    catalog_by_slug = {d.slug: d for d in durable_decisions.CATALOG}
    unknown = wanted - set(catalog_by_slug)
    if unknown:
        return SectionResult(ok=False, errors={"durable_decisions": f"unknown slug(s): {sorted(unknown)}"})
    lines.append(feature_facts.facts_block(["hydration_adr_adoption"]))
    decisions_touched = is_field_touched(state, _SLUG, "durable_decisions")
    for decision in durable_decisions.CATALOG:
        if decision.slug not in wanted:
            cl.add("hydration", decision.slug, ck.choice_status(decisions_touched),
                   "operator did not select this entry" if decisions_touched else
                   "default (list never visited/toggled)")
            continue
        act, produces = _decision_act(led, decision.hydrates)
        plan.append(PlanEntry(screen="hydration", item=decision.slug, lesson="a curated "
                               "durable-decision row + CLAUDE.md fragment", act=act, produces=produces))
        lines.append(f"queued: {act.render()}")
        selected_fragments.append(decision.claude_md)

    adrs = durable_decisions.list_adrs()
    wanted_adrs = set(answers["adopt_adrs"])
    known_adr_numbers = {number for number, _, _ in adrs}
    unknown_adrs = wanted_adrs - known_adr_numbers
    if unknown_adrs:
        return SectionResult(ok=False, errors={"adopt_adrs": f"unknown ADR number(s): {sorted(unknown_adrs)}"})
    adrs_touched = is_field_touched(state, _SLUG, "adopt_adrs")
    for number, title, relpath in adrs:
        label = f"ADR-{number}: {title}"
        if number not in wanted_adrs:
            cl.add("hydration", f"adr adoption ({label})", ck.choice_status(adrs_touched),
                   "operator did not select this entry" if adrs_touched else
                   "default (list never visited/toggled)")
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
    # NOTE: no "dest" in state_updates -- it is Fork/target's own owned fact already (ADR-0012
    # P1: one writer of one truth).
    return SectionResult(ok=True, state_updates={"hydration_engaged": True},
                       info_lines=tuple(lines))


def _blocked_needs_dest(state: dict) -> "str | None":
    """Hydration writes CLAUDE.md/durable-decision rows into the born world's own destination --
    nothing to hydrate until Fork/target or Birth has recorded one."""
    if state.get("dest"):
        return None
    return "requires: Fork/target or Birth (a destination directory) to be set first"


STEP = SectionSpec(
    slug="hydration", title="Hydration", group="Runtime", fields=fields, submit=submit,
    blocked=_blocked_needs_dest,
    description="Compiles this new world's own CLAUDE.md durable-decisions section and files "
                "real 'led decision' rows -- a curated catalog of standing rules 'borne out of "
                "our painful experience' (see each entry's own why/citation below), plus any "
                "ADRs from this repo's own law/adr/ this world should adopt at birth.")
