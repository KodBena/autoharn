#!/usr/bin/env python3
"""tools/setup_tui/steps_boundary.py -- the Boundary step's UI-free core, ported from
`screen_boundary`."""
from __future__ import annotations

import json
import os

from tools.configtree import ConfirmField, SectionResult, SectionSpec, TextField
from tools.setup_tui import checklist as ck
from tools.setup_tui import destination, feature_facts, governed_files, probes
from tools.setup_tui.idtypes import DestPath, DestPathError, WorldName, WorldNameError
from tools.setup_tui.plan import (BackgroundAct, CallableAct, CommandAct, DaemonSelection,
                                   PlanEntry, WriteAct)

BOUNDARY_PROC_PRODUCES = "boundary-proc"
_SLUG = "boundary"


def fields(state: dict) -> tuple:
    # NO "dest"/"world" fields here (maintainer ruling 2026-07-22, ADR-0019 single-editable-
    # home): the destination directory is owned by Fork/target, the world name by Birth --
    # boundary reads both shared facts straight out of state in `submit` below, never via a
    # second field declaration (a duplicated projection is refused at App construction,
    # `tools.configtree.spec.validate_shared_ownership`).
    #
    # legacy-led-retirement inventory pass (ledger row 1149/1150): the "Configure the boundary
    # service now?" decline gate that stood here is REMOVED -- the boundary is MANDATORY at
    # every birth per the ratified coupling (row 1150) now that legacy-led.tmpl is retired:
    # declining used to fall back to `legacy/led`, now a one-line teaching-refusal stub, never a
    # working CLI -- "decline" would brick the rest of this run's commit. Configuration CHOICES
    # (host/db/port/auto-start-now-vs-later) are unchanged; only the existence gate is gone.
    # BASIS (corrected, retirement review round 1, ledger row 1173): the decision rests on the
    # ratified boundary coupling alone -- ledger row 1150 ("the boundary becomes every world's
    # standing service per the spec's stated coupling") -- plus the plain operational fact stated
    # above: post-retirement, declining now falls through to a one-line refusal stub (legacy/led
    # is no longer a working CLI at all), which bricks the rest of this run's commit. ERRATUM:
    # this comment previously cited "row 1942 (autoharn1's own ledger)" as a DEFECT-FIX WITNESS
    # for Case 14 (runner.resolve_led) supporting this removal. That citation was independently
    # verified FALSE -- autoharn1 row 1942 is autoharn1's OWN succession commission (the
    # maintainer-commissioned rebirth to autoharn2), not a witness of any decline-mode fallback
    # defect. The removal decision above does not need, and never needed, that citation; it
    # stands on row 1150 and the operational fact alone.
    return (
        ConfirmField(name="override", label="Override and proceed WITHOUT a confirmed successful "
                     "birth? (only used if birth was not confirmed)"),
        TextField(name="host", label="Postgres host", default=state.get("pghost", "192.168.122.1"),
                  required=False),
        TextField(name="db", label="Database", default=state.get("db", "toy"), required=False),
        ConfirmField(name="start_now", label="Start the boundary service now (this process)?",
                     default=True),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    lines = [feature_facts.facts_block(["boundary_service"])]
    if not state.get("birth_ok") and not answers["override"]:
        return SectionResult(ok=False, errors={"override": "birth was not confirmed successful -- "
                                             "check this box to proceed anyway"})
    if not state.get("birth_ok") and answers["override"]:
        cl.add("boundary", "birth gate", ck.WITNESSED, "OVERRIDDEN by operator")

    # "dest"/"world" are Fork/target's and Birth's own owned fields respectively -- read the
    # shared facts directly, never via a field of boundary's own (dropped, see `fields`'s own
    # docstring above).
    try:
        dest_path = DestPath.parse(state.get("dest", ""))
    except DestPathError as exc:
        return SectionResult(ok=False, errors={"": f"destination (set in Fork/target): {exc}"})
    dest = str(dest_path)
    if destination.classify_destination(dest).kind == destination.DestKind.FRESH:
        if not state.get("dest_would_exist"):
            cl.add("boundary", "destination exists", ck.REFUSED, f"'{dest}' not a directory")
            return SectionResult(ok=False, errors={"": "destination (set in Fork/target) does not "
                                                 "exist -- run a birth first"})
        cl.add("boundary", "destination exists", ck.DRY_SKIPPED, f"'{dest}' queued earlier")

    try:
        world_name = WorldName.parse(state.get("world", ""))
    except WorldNameError as exc:
        return SectionResult(ok=False, errors={"": f"world name (set in Birth): {exc}"})
    world = str(world_name)
    host = answers["host"].strip() or state.get("pghost", "192.168.122.1")
    db = answers["db"].strip() or state.get("db", "toy")

    port = probes.free_port()
    boundary_url = f"http://127.0.0.1:{port}"
    lines.append(f"picked free port: {port} ({boundary_url})")

    dep_json_path = os.path.join(dest, "deployment.json")
    dep = {}
    if os.path.isfile(dep_json_path):
        with open(dep_json_path) as f:
            dep = json.load(f)
    schema, kern, role = dep.get("schema", world), dep.get("kern", f"{world}_kernel"), dep.get("role", f"{world}_rw")

    for label, val, checker in (("host", host, probes.valid_hostname), ("database", db, probes.valid_identifier),
                                 ("role", role, probes.valid_identifier), ("schema", schema, probes.valid_identifier),
                                 ("kern", kern, probes.valid_identifier), ("world", world, probes.valid_identifier)):
        if not checker(val):
            cl.add("boundary", "multiplex TOML values validated", ck.REFUSED, f"'{val}' ({label}) invalid")
            return SectionResult(ok=False, errors={"": f"{label} '{val}' fails the interpreter-boundary "
                                                 "allowlist"})

    toml_text = (f"[deployments.{world}]\npghost = \"{host}\"\npgdatabase = \"{db}\"\n"
                 f"pguser = \"{role}\"\npgschema = \"{schema}\"\npgkern = \"{kern}\"\n")
    toml_path = os.path.join(dest, "boundary-multiplex.toml")
    lines.append(f"--- queuing write: {toml_path} ---\n{toml_text}")
    plan = state["_plan"]
    plan.append(PlanEntry(screen="boundary", item="multiplex TOML written",
                           lesson="the boundary service's own config file",
                           act=WriteAct(path=toml_path, content=toml_text)))

    argv = [str(state["_repo_root"] / "bootstrap" / "new-project.sh"), dest, "--db", db, "--host", host,
            "--schema", schema, "--kern", kern, "--role", role, "--name", dep.get("name", world),
            "--force", "--boundary-url", boundary_url, "--boundary-deployment", world]
    if state.get("governed_patterns"):
        argv += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    lines.append(f"$ {' '.join(argv)}")
    plan.append(PlanEntry(screen="boundary", item="deployment.json boundary keys written",
                           lesson="classic-mode re-scaffold", act=CommandAct(argv=tuple(argv))))

    preferred_python = os.path.expanduser("~/w/vdc/venvs/generic/bin/python")
    fallback_python = probes.which("python3")
    if os.access(preferred_python, os.X_OK):
        venv_python, interp_reason = preferred_python, f"venv interpreter: {preferred_python}"
    elif fallback_python:
        venv_python, interp_reason = fallback_python, f"venv absent -- using python3 on PATH: {fallback_python}"
    else:
        venv_python, interp_reason = None, f"NEITHER {preferred_python} NOR python3 is on PATH"

    updates = {"boundary_url": boundary_url, "boundary_port": port}
    if answers["start_now"] and venv_python:
        argv2 = [venv_python, "-m", "serving.boundary_service", "--config", toml_path, "--port", str(port)]
        lines.append(f"interpreter: {interp_reason}")
        lines.append(f"$ {' '.join(argv2)}   (background)")
        plan.append(PlanEntry(screen="boundary", item="service started",
                               lesson="starts the boundary service, this process's own child",
                               act=BackgroundAct(argv=tuple(argv2), cwd=str(state["_repo_root"])),
                               produces=BOUNDARY_PROC_PRODUCES))

        # design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part C completion (row 1158/1159, item 2 --
        # FAILURE HONESTY): the BackgroundAct above reports ok=True the instant Popen() succeeds
        # (commit_executor.py's own `_run_entry` -- forking/exec'ing is not the same fact as "the
        # service actually came up"), so a genuinely failed start (the concrete case this closes:
        # the picked port is ALREADY occupied -- uvicorn's own bind refuses and the child exits
        # within milliseconds) would otherwise sail through as a false accept, and every act
        # queued AFTER it -- principals-authority, signed-genesis, hydration -- would then run
        # against a boundary that is not there: a half-born world, no different from the
        # silent-fallback class this whole re-sequencing exists to foreclose. This CallableAct
        # (the one generic commit-time-effect escape hatch, `plan.py`'s own docstring) polls the
        # SAME health URL for up to 10s (`probes.wait_for_health`) and is the ACT that actually
        # fails the commit -- REFUSED, with the last probe's own detail as teaching -- when the
        # service never answers; per-act atomicity means NOTHING queued after this entry ever
        # runs (`commit_executor.execute`'s own "stops at the FIRST entry whose act does not
        # succeed"). No silent fallback to legacy/led exists to reach for either way -- the
        # operator's only lawful next step is fixing the port/env and re-running the commit
        # (which resumes exactly here, the journal's own resume-from-PENDING contract).
        def _boundary_health_gate() -> tuple[bool, str]:
            ok, last = probes.wait_for_health(f"{boundary_url}/d/{world}/health", timeout_s=10.0)
            if ok:
                return True, f"boundary healthy: {last}"
            return False, (
                f"REFUSED -- the boundary service never answered {boundary_url}/d/{world}/health "
                f"within 10s (last probe: {last}). The most likely cause is the port ({port}) "
                f"already being occupied by another process -- check with `ss -ltnp | grep "
                f"{port}` (or lsof -i :{port}), free the port or re-run this section to pick a "
                f"different one, then retry the commit. NOTHING after this act ran (per-act "
                f"atomicity); principals-authority/signed-genesis/hydration never touched a "
                f"half-born world.")
        plan.append(PlanEntry(screen="boundary", item="service health gate",
                               lesson="confirms the boundary actually came up before any "
                                      "ledger-writing act trusts it",
                               act=CallableAct(fn=_boundary_health_gate,
                                                label=f"poll {boundary_url}/d/{world}/health")))
        updates["boundary_will_start"] = True
        updates["boundary_world"] = world
    else:
        if answers["start_now"] and not venv_python:
            cl.add("boundary", "service auto-start", ck.REFUSED, interp_reason)
        unit_text = (f"[Unit]\nDescription=autoharn boundary service ({world})\n\n[Service]\n"
                     f"ExecStart={venv_python or preferred_python} -m serving.boundary_service "
                     f"--config {toml_path}\nWorkingDirectory={state['_repo_root']}\n"
                     f"Restart=on-failure\n\n[Install]\nWantedBy=multi-user.target\n")
        lines.append(f"--- PREPARED: systemd unit text (operator installs/starts) ---\n{unit_text}")
        plan.add_daemon(DaemonSelection(
            name="boundary", argv=(venv_python or preferred_python, "-m", "serving.boundary_service",
                                    "--config", toml_path, "--port", str(port)),
            cwd=str(state["_repo_root"]), env_notes="boundary-multiplex.toml's own deployment section",
            health_probe=f"http:{boundary_url}/d/{world}/health", prerequisite=(venv_python or preferred_python)))
        cl.add("boundary", "service unit text", ck.INSTRUCTED, "systemd unit, not started")

    # NOTE: no `updates["dest"] = dest` here -- "dest" is Fork/target's own owned fact, already
    # in state; re-writing the same value here would be a second writer of one truth (ADR-0012
    # P1), even though harmless today (same value) -- removed on principle.
    return SectionResult(ok=True, state_updates=updates, info_lines=tuple(lines))


def _blocked_needs_dest(state: dict) -> "str | None":
    """The boundary service is started FROM the born world's own destination, under its own
    world name -- nothing to start until Fork/target has recorded a destination AND Birth has
    recorded a world name (both are now read directly from shared state, boundary's own "dest"/
    "world" fields having been dropped in favor of their single owning section)."""
    missing = []
    if not state.get("dest"):
        missing.append("Fork/target (a destination directory)")
    if not state.get("world"):
        missing.append("Birth (a world name)")
    if not missing:
        return None
    return f"requires: {' and '.join(missing)} to be set first"


STEP = SectionSpec(slug="boundary", title="Boundary", group="Runtime", fields=fields,
                    submit=submit, blocked=_blocked_needs_dest,
                    description=feature_facts.fact("boundary_service").elements())
