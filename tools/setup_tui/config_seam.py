#!/usr/bin/env python3
"""tools/setup_tui/config_seam.py -- the SCREEN-SEAM half of the config-file feature
(design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md, ledger row 1944): wires a validated
`config_file.ConfigDoc` into the flow's own two existing prompt seams, and captures a run's
resolved decisions back OUT into `config_file`'s save shape. `tools/setup_tui/config_file.py`
never imports this module (parse/validate stays screen-blind, ADR-0012 P1) -- this is the one
direction of dependency.

FOUR JOBS:
  1. `synthesize_scripted_lines` -- spec §2's `--from-config`: compiles a validated, COMPLETE
     config into the exact positional answer sequence the eleven-screen flow consumes, mirroring
     `screens.py`'s own prompt order. `app.py` feeds the result through the EXISTING
     `ScriptedUi` machinery (a real answers-file, reused -- not a second interactive driver),
     which is also why a `--from-config` run gets the SAME `is_scripted` scratch-GNUPGHOME
     treatment a `--scripted` witnessing run gets in `screen_signed_genesis` (correct: neither
     backend has a human at the keyboard for a live gpg pinentry).
  2. `build_initial_prior_answers` -- spec §2's `--initial-config`: a dotted-key -> (screen,
     prompt-text) table (`PROMPT_MAP`) turned into the SAME `FlowPosition.last_answers` shape
     the navigation seam (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md) already uses to re-offer a
     revisited screen's own prior answers as defaults -- reused wholesale, not reimplemented
     (spec §2: "works with navigation").
  3. `check_world_and_dest` -- spec §3's world-name/destination rejection, run once, before any
     act.
  4. `capture_resolved_config` / `save_world_config` -- spec §4's self-application: reads the
     resolved decision set back out of a finished run's `state`/`Plan`, and writes it (the ONE
     narrow declared exception this module carries, mirroring `checklist.Checklist.save`'s own
     precedent -- gates/setup_tui_purity_gate.py's EXEMPT table names both).

Stdlib + this package only, top-of-file imports (the lazy-import gate applies)."""
from __future__ import annotations

import contextlib
import json
import os
import re
import tempfile
from collections.abc import Iterator
from pathlib import Path

from tools.setup_tui import config_file, content, destination, durable_decisions, governed_files, probes
from tools.setup_tui import runner
from tools.setup_tui.plan import CommandAct

# --------------------------------------------------------------------------------------------
# 1. --from-config: compile to a per-step {slug: {field: value}} answers dict -- the shape
#    tools/setup_tui/app.py's headless driver hands straight to each StepSpec.submit, no answers-
#    file/fake-terminal indirection (that machinery -- ScriptedUi -- is deleted with --scripted;
#    design/FABLE-SETUP-TUI-REBUILD-SPEC.md §2/§6).
# --------------------------------------------------------------------------------------------


def answers_for_from_config(doc: config_file.ConfigDoc, *, world: str, dest: str) -> dict[str, dict]:
    """Mirrors `tools.setup_tui.steps.STEPS`'s own field names, screen by screen, driven by
    `doc`'s already-VALIDATED (`require_complete=True`) values -- never re-validates. `world`/
    `dest` are the CLI parameters (spec §2); every OTHER value comes from the config file. A
    field this dict does not set falls back to that field's own default (matching an operator
    who accepted every default in the interactive UI)."""
    g = lambda k, default=None: config_file.get(doc, k, default)  # noqa: E731
    host_env = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")

    out: dict[str, dict] = {
        "preflight": {"run": True},
        "substrate": {
            "run": bool(g("substrate.run", False)),
            "path": str(g("substrate.path", "existing")),
            "host": str(g("substrate.host", host_env or "192.168.122.1")),
            "db_existing": str(g("substrate.db", "toy")),
            "db_dedicated": str(g("substrate.db", "")),
            "role": str(g("substrate.role", "")),
            "subnets": str(g("substrate.subnets", "")),
        },
        "fork-target": {
            "run": True, "mode": "fresh", "dest": dest, "src": "",
            "accept_foreign": False,
            "governed_extend": bool(g("fork_target.governed_extend", False)),
            "governed_extensions": str(g("fork_target.governed_extensions", "")),
        },
        "rehearsal": {"run": bool(g("rehearsal.run", False)), "host": str(g("substrate.host", "")),
                      "db": str(g("substrate.db", "")), "scratch_world": "", "scratch_dir": ""},
        "birth": {"override": True, "run": bool(g("birth.run", False)),
                  "host": str(g("substrate.host", "")), "db": str(g("substrate.db", "")),
                  "world": world, "dest": dest, "name": str(g("birth.project_name", ""))},
        "principals-authority": {
            "dest": dest,
            "register": list(g("principals_authority.register", []) or []) if g("principals_authority.run", False) else [],
            "competences": list(g("principals_authority.competences", []) or []) if g("principals_authority.run", False) else [],
            "relations": list(g("principals_authority.relations", []) or []) if g("principals_authority.run", False) else [],
            "charters": [],  # excluded-by-type (spec §1): a charter needs a file path a
                              # config file cannot round-trip; always empty from --from-config.
        },
        "signed-genesis": {
            "run": bool(g("signed_genesis.run", False)), "dest": dest,
            "statement": str(g("signed_genesis.commission_statement", "")),
            "use_scratch_identity": True,  # --from-config is never a human at the keyboard
            "name": "", "email": "", "gnupghome": "",
        },
        "boundary": {
            "run": bool(g("boundary.configure", False)), "override": True, "dest": dest,
            "world": world, "host": str(g("substrate.host", "")), "db": str(g("substrate.db", "")),
            "start_now": bool(g("boundary.start_now", False)),
        },
        "observability": {
            "run": bool(g("observability.run", False)), "dest": dest,
            "otelcol": bool(g("observability.otelcol", False)),
            "otel_watch": bool(g("observability.otel_watch", False)),
        },
        "hydration": {
            "run": bool(g("hydration.run", False)), "dest": dest,
            "fork_provenance": bool(g("hydration.fork_provenance", False)),
            "fork_provenance_statement": str(g("hydration.fork_provenance_statement", "")),
            "role_charters": False,
            # TYPED LIST, NEVER A JOINED STRING (maintainer round 5, ledger row 1115, defect F):
            # `hydration.durable_decisions`/`.adopt_adrs` are TOML arrays in the config file
            # (`config_file.render_toml`'s own list handling already emits them that way) and a
            # `MultiChoiceField`'s own model value is a `list[str]` -- the comma-join here used
            # to exist only because the field it fed was a free-text `TextField` the operator
            # had to hand-edit; that field is gone, so is the join.
            "durable_decisions": list(g("hydration.durable_decisions", []) or []),
            "adopt_adrs": list(g("hydration.adopt_adrs", []) or []),
        },
    }
    return out


# --------------------------------------------------------------------------------------------
# 2. --initial-config: seed the wizard's shared `state` -- every `steps_*.py` field default reads
#    `state.get(...)` (e.g. `state.get("pghost")`, `state.get("dest")`), so pre-loading these few
#    shared keys is enough to make a partial config's values show up as widget defaults on first
#    visit -- no separate prior-answers seam needed (unlike the deleted `flow_position.py`'s
#    per-prompt map: Textual's own screen stack already retains values across Back, module
#    docstring's job 2 no longer needs to simulate that for a FIRST visit).
# --------------------------------------------------------------------------------------------

_STATE_OVERRIDE_KEYS: dict[str, str] = {
    "substrate.host": "pghost",
    "substrate.db": "db",
    "substrate.role": "dedicated_role",
    "substrate.path": "substrate_path",
}


def build_initial_state_overrides(doc: config_file.ConfigDoc) -> dict[str, object]:
    """`{state_key: value}` merged into `tools.setup_tui.steps.initial_state`'s own dict --
    partial configs are fine (spec §2); a key not present in `doc` is simply omitted, never
    guessed. Fields with no shared-state home (the register/competence/relation/charter lists,
    a per-screen scalar like the signed-genesis commission statement) are NOT seeded this way --
    a named, honest limitation (mirrors the pre-rebuild PROMPT_MAP's own documented gap for the
    same fields)."""
    out: dict[str, object] = {}
    for dotted, state_key in _STATE_OVERRIDE_KEYS.items():
        val = config_file.get(doc, dotted)
        if val is not None:
            out[state_key] = val
    return out


# --------------------------------------------------------------------------------------------
# 3. World-name / destination rejection (spec §3), checked once, before any act.
# --------------------------------------------------------------------------------------------

def check_world_and_dest(*, world: str, dest: str, host: str, db: str) -> str | None:
    """Returns a refusal message, or `None` if both checks pass. Called once by `app.py`'s
    `--from-config` handling, before the flow starts (spec §3: "checked before any act")."""
    for candidate in (world, f"{world}_kernel"):
        exists, detail = probes.pg_schema_exists(host, db, candidate)
        if exists:
            return (f"world name '{world}' REFUSED -- schema '{candidate}' already exists on "
                     f"{host}/{db} ({detail}); pick a different --world, or use the existing "
                     f"world's own destination directly.")

    sentinel_path = Path(dest) / destination.SENTINEL_NAME
    if sentinel_path.is_file():
        try:
            sentinel_world = json.loads(sentinel_path.read_text(encoding="utf-8")).get("world")
        except (OSError, ValueError):
            sentinel_world = None
        if sentinel_world and sentinel_world != world:
            return (f"world name '{world}' REFUSED -- destination '{dest}' sentinel names a "
                     f"different world ({sentinel_world!r}); this looks like the wrong "
                     f"destination for '{world}', or the wrong --world for this destination.")

    dest_state = destination.classify_destination(dest)
    if dest_state.kind != destination.DestKind.FRESH:
        return (f"destination '{dest}' REFUSED -- classifies as {dest_state.kind.value} "
                f"({'; '.join(dest_state.evidence)}); --from-config only births into a FRESH "
                f"destination (design/FABLE-SETUP-TUI-DESTINATION-STATE-SPEC.md's own refusal "
                f"paths apply unchanged -- this spec adds no second opinion on destinations).")
    return None


# --------------------------------------------------------------------------------------------
# 4. Self-application (spec §4): capture + save.
# --------------------------------------------------------------------------------------------

_ADR_ITEM_RE = re.compile(r"^adr adoption \(ADR-(\d+):")


def _command_rows(entries, screen: str, argv_prefix: tuple[str, ...], fields: dict[str, int]):
    rows = []
    for e in entries:
        if e.screen != screen or not isinstance(e.act, CommandAct):
            continue
        argv = e.act.argv
        if len(argv) <= max(fields.values()) or tuple(argv[1:1 + len(argv_prefix)]) != argv_prefix:
            continue
        rows.append({name: argv[idx] for name, idx in fields.items()})
    return rows


def capture_resolved_config(state: dict) -> dict[str, object]:
    """Reads the resolved decision set back OUT of a just-finished (or just-planned, under
    `--dry-run`) run's `state`/`Plan` -- spec §4's self-save. Deliberately reads only what
    `state`/the plan already carry (no new bookkeeping added to `screens.py` beyond the two
    narrow `*_engaged` flags `screen_observability`/`screen_hydration` set) -- a field this
    function cannot recover honestly (dedicated-substrate subnets; a role-charter's own file
    path) is simply omitted, never guessed (ADR-0002 rule 2)."""
    plan = state.get("plan")
    entries = plan.entries if plan else []
    daemons = plan.daemons if plan else []
    out: dict[str, object] = {}

    sub_run = "substrate_path" in state
    out["substrate.run"] = sub_run
    if sub_run:
        out["substrate.path"] = state["substrate_path"]
        out["substrate.host"] = state.get("pghost", "")
        out["substrate.db"] = state.get("db", "")
        if state["substrate_path"] == "dedicated":
            out["substrate.role"] = state.get("dedicated_role", "")

    governed = state.get("governed_patterns")
    if governed is not None:
        extra = [p for p in governed if p not in governed_files.DEFAULT_PATTERNS]
        out["fork_target.governed_extend"] = bool(extra)
        out["fork_target.governed_extensions"] = ",".join(extra)

    out["rehearsal.run"] = bool(state.get("rehearsal_green"))
    out["birth.run"] = bool(state.get("birth_ok"))

    pa_run = "planned_principal_names" in state
    out["principals_authority.run"] = pa_run
    if pa_run:
        out["principals_authority.register"] = _command_rows(
            entries, "principals-authority", ("register-principal",),
            {"name": 2, "agent_class": 3, "purpose": 5})
        out["principals_authority.competences"] = _command_rows(
            entries, "principals-authority", ("principal", "grant-competence"),
            {"name": 3, "activity": 5, "band": 7, "basis": 9})
        out["principals_authority.relations"] = _command_rows(
            entries, "principals-authority", ("principal", "relate"),
            {"subject": 3, "relation": 4, "object": 5})

    sg_run = any(e.screen == "signed-genesis" for e in entries)
    out["signed_genesis.run"] = sg_run
    if sg_run:
        stmt_rows = _command_rows(entries, "signed-genesis", ("commission",), {"statement": 2})
        if stmt_rows:
            out["signed_genesis.commission_statement"] = stmt_rows[0]["statement"]

    out["boundary.configure"] = "boundary_url" in state
    out["boundary.start_now"] = bool(state.get("boundary_will_start"))

    out["observability.run"] = bool(state.get("observability_engaged"))
    out["observability.otelcol"] = any(d.name == "otelcol" for d in daemons)
    out["observability.otel_watch"] = any(d.name == "otel-watch" for d in daemons)

    h_run = bool(state.get("hydration_engaged"))
    out["hydration.run"] = h_run
    if h_run:
        out["hydration.fork_provenance"] = any(
            e.screen == "hydration" and e.item == "fork provenance" for e in entries)
        out["hydration.role_charters"] = any(
            e.screen == "hydration" and e.item == "role charters to register" for e in entries)
        slugs = {d.slug for d in durable_decisions.CATALOG}
        out["hydration.durable_decisions"] = [
            e.item for e in entries if e.screen == "hydration" and e.item in slugs]
        out["hydration.adopt_adrs"] = [
            m.group(1) for e in entries if e.screen == "hydration"
            for m in [_ADR_ITEM_RE.match(e.item)] if m
        ]
    return out


def save_world_config(dest: str, state: dict, *, dry_run: bool) -> tuple[str, bool]:
    """Renders + writes `<dest>/world-config.toml` (spec §4). Returns `(path, wrote)`.

    DECLARED EXCEPTION (mirrors `checklist.Checklist.save`'s own precedent exactly --
    gates/setup_tui_purity_gate.py's EXEMPT table names both by function): this is structurally
    POST-commit machinery -- the resolved decision set is not complete until every screen (and,
    live, the commit itself) has run, so it cannot be a `Plan` entry executed DURING the commit;
    it runs once, from `screens.py`'s own `_execute_commit`, after `commit_executor.execute` has
    already returned (or a dry run has already rendered its WOULD-DO table)."""
    resolved = capture_resolved_config(state)
    content = config_file.render_toml(
        resolved, produced_by="setup_tui self-application (commit)",
        source=f"world '{state.get('world', '?')}' at {dest}")
    path = os.path.join(dest, "world-config.toml")
    wrote = runner.write_file(path, content, dry_run=dry_run)
    return path, wrote
