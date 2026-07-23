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

from tools.setup_tui import config_file, destination, durable_decisions, governed_files, probes
from tools.setup_tui import runner
from tools.setup_tui.content import screens_data as SD
from tools.setup_tui.plan import CommandAct

# --------------------------------------------------------------------------------------------
# 1. --from-config: compile to the existing --scripted answers-file shape.
# --------------------------------------------------------------------------------------------


def _yn(val: bool) -> str:
    return "y" if val else "n"


def synthesize_scripted_lines(doc: config_file.ConfigDoc, *, world: str, dest: str) -> list[str]:
    """Mirrors `screens.py`'s own prompt sequence, screen by screen, driven by `doc`'s already-
    VALIDATED (`require_complete=True`) values -- never re-validates. `world`/`dest` are the
    CLI parameters (spec §2); every OTHER answer comes from the config file."""
    g = lambda k, default=None: config_file.get(doc, k, default)  # noqa: E731
    lines: list[str] = ["y"]  # preflight -- always run (read-only, no schema key needed)
    # `screen_preflight` pre-seeds `state["pghost"]` (NEVER `state["db"]`) from HARNESS_PGHOST/
    # EPISTEMIC_PGHOST when either is set in THIS process's own environment (screens.py's own
    # preflight probe, always reached above since preflight is always run) -- checked HERE, at
    # synthesis time, in the SAME environment the flow itself will run in, so this stays
    # deterministic per invocation rather than guessing. `host_known`/`db_known` are tracked
    # SEPARATELY (not one joint flag): every later screen's own `state.get("pghost") or ask_text`
    # / `state.get("db") or ask_text` pair gates each independently, and `screen_substrate`'s own
    # "Existing database name"/"New (dedicated) database name" ask_text is UNCONDITIONAL (never
    # gated on `state.get("db")` at all) -- db is asked exactly once, always, if substrate runs.
    host_known = bool(os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST"))
    db_known = False

    def _host_db_lines(need_host: bool = True, need_db: bool = True) -> None:
        """Appends "Postgres host"/"Database"-shaped answers for whichever of the two this
        screen's own `state.get(...) or ask_text(...)` pair will actually ask, given what is
        known SO FAR -- called at every later screen that shares this same pattern
        (rehearsal/birth/boundary), marking both known once either screen has asked."""
        nonlocal host_known, db_known
        if need_host and not host_known:
            lines.append(str(g("substrate.host", "192.168.122.1")))
        if need_db and not db_known:
            lines.append(str(g("substrate.db", "toy")))
        host_known = True
        db_known = True

    sub_run = bool(g("substrate.run", False))
    lines.append(_yn(sub_run))
    if sub_run:
        path = str(g("substrate.path", "existing"))
        lines.append(path)
        if not host_known:
            lines.append(str(g("substrate.host", "192.168.122.1")))
        host_known = True
        if path == "existing":
            lines.append(str(g("substrate.db", "toy")))
        else:
            lines += [str(g("substrate.db", "")), str(g("substrate.role", "")),
                      str(g("substrate.subnets", ""))]
        db_known = True

    # fork-target: destination is always the CLI parameter, "fresh" mode.
    lines += ["y", "fresh", dest]
    extend = bool(g("fork_target.governed_extend", False))
    lines.append(_yn(extend))
    if extend:
        lines.append(str(g("fork_target.governed_extensions", "")))

    reh_run = bool(g("rehearsal.run", False))
    lines.append(_yn(reh_run))
    if reh_run:
        _host_db_lines()
        lines += ["-", "-"]  # scratch world name / scratch dir -- accept the unique defaults

    birth_run = bool(g("birth.run", False))
    lines.append(_yn(birth_run))
    if birth_run:
        if not reh_run:
            lines.append("y")  # override: proceed without a green rehearsal
        _host_db_lines()
        lines.append(world)
        lines.append(str(g("birth.project_name", "") or "-"))

    # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159): "boundary"
    # moved to run BEFORE "principals-authority"/"signed-genesis" -- mirrored here to match.
    # legacy-led-retirement inventory pass (ledger row 1149/1150): the "Configure the boundary
    # service now?" gate this block used to emit a `_yn(b_run)` answer for is RETIRED --
    # screen_boundary no longer asks it (boundary is mandatory) -- no line emitted for it, block
    # runs unconditionally.
    if not birth_run:
        lines.append("y")  # override: proceed without a confirmed successful birth
        lines.append(world)  # "World/deployment name" -- only unasked when birth set it
    _host_db_lines()
    lines.append(_yn(bool(g("boundary.start_now", False))))

    pa_run = bool(g("principals_authority.run", False))
    lines.append(_yn(pa_run))
    if pa_run:
        for row in (g("principals_authority.register", []) or []):
            lines += ["y", str(row["name"]), str(row["agent_class"]), str(row["purpose"])]
        lines.append("n")
        for row in (g("principals_authority.competences", []) or []):
            lines += ["y", str(row["name"]), str(row["activity"]), str(row["band"]),
                      str(row["basis"])]
        lines.append("n")
        for row in (g("principals_authority.relations", []) or []):
            lines += ["y", str(row["subject"]), str(row["relation"]), str(row["object"])]
        lines.append("n")
        # role charters need a charter FILE PATH -- excluded-by-type (spec §1), so a config-
        # driven run never offers one; always declined here (a named, honest limitation: this
        # ONE hydration/principals-authority item cannot round-trip through --from-config).
        lines.append("n")

    sg_run = bool(g("signed_genesis.run", False))
    lines.append(_yn(sg_run))
    if sg_run:
        lines.append(str(g("signed_genesis.commission_statement", "")))
        lines += ["-", "-"]  # scripted/fixture keygen identity -- accept the fixture defaults

    o_run = bool(g("observability.run", False))
    lines.append(_yn(o_run))
    if o_run:
        lines.append(_yn(bool(g("observability.otelcol", False))))
        lines.append(_yn(bool(g("observability.otel_watch", False))))

    h_run = bool(g("hydration.run", False))
    lines.append(_yn(h_run))
    if h_run:
        lines.append(_yn(bool(g("hydration.fork_provenance", False))))
        if g("hydration.fork_provenance", False):
            lines.append(str(g("hydration.fork_provenance_statement", "")))
        # role charters -- same excluded-by-type reasoning as principals-authority's own item
        # above; always declined by a config-driven run.
        lines.append("n")
        wanted_decisions = set(g("hydration.durable_decisions", []) or [])
        for decision in durable_decisions.CATALOG:
            lines.append(_yn(decision.slug in wanted_decisions))
        wanted_adrs = set(g("hydration.adopt_adrs", []) or [])
        for number, _title, _relpath in durable_decisions.list_adrs():
            lines.append(_yn(number in wanted_adrs))

    # "Commit this plan now? (N entries)" -- ONLY fires on a LIVE run (`_execute_commit`'s own
    # `dry_run` branch returns before ever asking it); harmlessly unused under `--dry-run`
    # (`ScriptedUi` never complains about an unconsumed trailing line), REQUIRED live -- omitting
    # it here was a real gap this build caught live (a real, non-dry-run birth from the exemplar
    # exhausted the answers file one line short at this exact prompt).
    lines.append("y")
    lines.append("y")  # "Save this checklist into the new world?" -- always yes
    return lines


@contextlib.contextmanager
def scripted_answers_file(lines: list[str]) -> Iterator[str]:
    """Writes `lines` to a scratch file in the SAME shape a real `--scripted` answers file uses
    (one answer per line), yields its path, and removes it on exit -- `app.py`'s `_run_from_
    config` feeds the path straight to `tools.setup_tui.ui.ScriptedUi`, never builds one itself.

    DECLARED EXCEPTION (gates/setup_tui_purity_gate.py's EXTRA_EFFECT_EXEMPT table names this
    function): a real `tempfile`/`os.unlink` effect, but ORCHESTRATION-level, not a decision-
    phase screen effect -- it runs before any screen, any `Ui`, or any `Plan` exists (the same
    "outside the normal Ui-mediated flow" register `app.py`'s own `_select_backend` diagnostic
    already occupies), so the pure-core spec's decision-phase/commit-phase split does not apply
    to it at all; it is scoped here, not exempted wholesale, so a REAL decision-phase tempfile
    effect would still be caught."""
    fd, path = tempfile.mkstemp(prefix="setup-tui-from-config-", suffix=".txt")
    try:
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(lines) + "\n")
        yield path
    finally:
        os.unlink(path)


# --------------------------------------------------------------------------------------------
# 2. --initial-config: seed the existing navigation prior-answers seam.
# --------------------------------------------------------------------------------------------

PROMPT_MAP: dict[str, tuple[str, str]] = {
    "substrate.run": ("substrate", "Configure substrate now?"),
    "substrate.host": ("substrate", "Postgres host"),
    "substrate.db": ("substrate", "Existing database name"),
    "substrate.role": ("substrate", "New (dedicated) role name"),
    "substrate.subnets": ("substrate", "Subnets to trust (comma-separated CIDR)"),
    "fork_target.governed_extend": ("fork-target", SD.CONFIRM_GOVERNED_FILES_EXTEND),
    "fork_target.governed_extensions": (
        "fork-target", "Extensions to add, comma-separated (e.g. .ts,.vue,.html)"),
    "rehearsal.run": (
        "rehearsal", "Run rehearsal (scratch birth + teardown + zero-residue check)?"),
    "birth.run": ("birth", "Run the real birth now?"),
    "birth.project_name": ("birth", "Project name (deployment.json 'name')"),
    "principals_authority.run": ("principals-authority", SD.CONFIRM_PRINCIPALS_AUTHORITY),
    "signed_genesis.run": ("signed-genesis", SD.CONFIRM_SIGNED_GENESIS_CEREMONY),
    "signed_genesis.commission_statement": (
        "signed-genesis", "Founding commission statement (the ask this world exists to carry "
                           "out)"),
    # "boundary.configure" has no prompt anymore (retired, ledger row 1149/1150 -- always walked).
    "boundary.start_now": ("boundary", "Start the boundary service now (this process)?"),
    "observability.run": ("observability", "Configure observability now?"),
    "observability.otelcol": (
        "observability", "Select the OTel collector (otelcol-contrib) to start with this "
                          "world?"),
    "observability.otel_watch": (
        "observability", "Select the OTel model-provenance watchdog (otel-watch) to start "
                          "with this world?"),
    "hydration.run": ("hydration", "Run hydration now?"),
    "hydration.fork_provenance": ("hydration", "Hydrate: fork provenance?"),
    "hydration.fork_provenance_statement": (
        "hydration", "Statement for 'fork provenance' decision row"),
    "hydration.role_charters": ("hydration", "Hydrate: role charters to register?"),
}


def build_initial_prior_answers(doc: config_file.ConfigDoc) -> dict[str, dict[str, object]]:
    """`{screen: {prompt_text: value}}`, fed to `tools.setup_tui.flow_position.FlowPosition`'s
    own `last_answers` at construction (`app.py`) -- from there the EXISTING navigation seam
    (`NavigableUi`/`FlowPosition.prior_answers_for`) does the rest, unmodified: a config value
    shows as "you answered this X last time -- press enter to keep it, or answer again" exactly
    like a real prior visit would. Partial configs are fine (spec §2) -- only keys present in
    `doc` contribute a default; every field not in `PROMPT_MAP` (the register/competence/
    relation loops, which have no single prompt to default) is simply not offered as a default,
    named here rather than silently absent."""
    out: dict[str, dict[str, object]] = {}
    for dotted, (screen, prompt) in PROMPT_MAP.items():
        val = config_file.get(doc, dotted)
        if val is None:
            continue
        out.setdefault(screen, {})[prompt] = val
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

    # legacy-led-retirement inventory pass (ledger row 1149/1150): "boundary.configure" is
    # retired from SCHEMA entirely -- capturing it here would make `render_toml` raise (its own
    # "not in SCHEMA -- caller bug" guard), correctly, since it is no longer a decision this run
    # made (the section is unconditional).
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
