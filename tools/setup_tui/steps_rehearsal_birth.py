#!/usr/bin/env python3
"""tools/setup_tui/steps_rehearsal_birth.py -- rehearsal + birth steps' UI-free core, ported from
`screen_rehearsal`/`screen_birth`. Rehearsal is the ONE declared exception (besides the commit
boundary) that calls a runner choke point directly, live, mid-flow, on a scratch target -- kept
unchanged from the pre-rebuild shape (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §1)."""
from __future__ import annotations

import os
import time
from pathlib import Path

from tools.configtree import ConfirmField, SectionResult, SectionSpec, TextField, is_field_touched
from tools.setup_tui import checklist as ck
from tools.setup_tui import destination, governed_files
from tools.setup_tui.idtypes import DestPath, DestPathError, WorldName, WorldNameError
from tools.setup_tui.plan import CommandAct, PlanEntry
from tools.setup_tui.runner import run_command

BIRTH_PRODUCES = "birth-ran"


def _new_project_argv(repo_root, dest, world, db, host, extra=None):
    argv = [str(repo_root / "bootstrap" / "new-project.sh"), dest, "--new-world", world,
            "--db", db, "--host", host]
    return argv + (extra or [])


def _teardown_argv(repo_root, world, db, host, extra=None):
    argv = [str(repo_root / "bootstrap" / "teardown-world.sh"), world, "--db", db, "--host", host]
    return argv + (extra or [])


def rehearsal_fields(state: dict) -> tuple:
    return (
        ConfirmField(name="run", label="Run rehearsal (scratch birth + teardown + zero-residue "
                     "check)?", default=True),
        TextField(name="host", label="Postgres host", default=state.get("pghost", "192.168.122.1"),
                  required=False),
        TextField(name="db", label="Database", default=state.get("db", "toy"), required=False),
        TextField(name="scratch_world", label="Scratch world name (probeworldNNNN)",
                  default=f"probeworld{int(time.time())}", required=False),
        TextField(name="scratch_dir", label="Scratch scaffold directory", required=False),
    )


def rehearsal_submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    if not answers["run"]:
        touched = is_field_touched(state, "rehearsal", "run")
        cl.add("rehearsal", "rehearsal", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")
        return SectionResult(ok=True, state_updates={"rehearsal_green": False},
                           info_lines=("rehearsal skipped by operator.",))

    host = answers["host"].strip() or state.get("pghost", "192.168.122.1")
    db = answers["db"].strip() or state.get("db", "toy")
    scratch_world = answers["scratch_world"].strip() or f"probeworld{int(time.time())}"
    scratch_dir = answers["scratch_dir"].strip() or f"/tmp/setup_tui_rehearsal_{scratch_world}"
    repo_root, dry_run = state["_repo_root"], state.get("dry_run", False)
    lines: list[str] = []

    argv = _new_project_argv(repo_root, scratch_dir, scratch_world, db, host, extra=["--force"])
    res = run_command(argv, dry_run=dry_run)
    lines.append(res.output.strip()[:2000])
    cl.add("rehearsal", "scratch birth", ck.status_for(res), "exit 0" if res.ok else f"exit {res.returncode}")

    argv = _teardown_argv(repo_root, scratch_world, db, host, extra=["--dir", scratch_dir])
    res2 = run_command(argv, stdin_text=f"{scratch_world}\n", dry_run=dry_run)
    lines.append(res2.output.strip()[:2000])
    cl.add("rehearsal", "scratch teardown", ck.status_for(res2),
           "exit 0" if res2.ok else f"exit {res2.returncode}")

    if dry_run:
        cl.add("rehearsal", "scratch scaffold dir removed", ck.WOULD_DO, scratch_dir)
    else:
        removed = not os.path.isdir(scratch_dir)
        cl.add("rehearsal", "scratch scaffold dir removed", ck.WITNESSED if removed else ck.REFUSED,
               scratch_dir if removed else f"STILL PRESENT: {scratch_dir}")

    green = res.ok and res2.ok
    lines.append(f"rehearsal: {'GREEN' if green else 'RED'}{' (simulated, --dry-run)' if dry_run else ''}")
    cl.add("rehearsal", "rehearsal overall", ck.WOULD_DO if dry_run else ck.WITNESSED,
           "GREEN" if green else "RED")
    return SectionResult(ok=True, state_updates={"rehearsal_green": green, "pghost": host, "db": db},
                       info_lines=tuple(lines))


REHEARSAL_STEP = SectionSpec(slug="rehearsal", title="Rehearsal", group="World lifecycle",
                              fields=rehearsal_fields, submit=rehearsal_submit)


def birth_fields(state: dict) -> tuple:
    # NO "dest" field here (maintainer ruling 2026-07-22, ADR-0019 single-editable-home): the
    # destination directory is owned by Fork/target (the section whose whole purpose is choosing
    # it) -- birth reads the shared fact straight out of state in `birth_submit` below, never via
    # a second field declaration (a duplicated projection is refused at App construction,
    # `tools.configtree.spec.validate_shared_ownership`).
    return (
        ConfirmField(name="override", label="Override and proceed WITHOUT a green rehearsal? "
                     "(only used if rehearsal was not green)"),
        ConfirmField(name="run", label="Run the real birth now?", default=True),
        TextField(name="host", label="Postgres host", default=state.get("pghost", "192.168.122.1"),
                  required=False),
        TextField(name="db", label="Database", default=state.get("db", "toy"), required=False),
        TextField(name="world", label="World name", default=state.get("world", ""), shared=True),
        TextField(name="name", label="Project name (deployment.json 'name')", required=False),
    )


def _birth_blocked(state: dict) -> "str | None":
    """The real dependency (spec §3 v2's own named example class): birth writes INTO the
    destination Fork/target owns -- nothing to write into until Fork/target has recorded one."""
    if state.get("dest"):
        return None
    return "requires: Fork/target (a destination directory) to be set first"


def birth_submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    if not state.get("rehearsal_green") and not answers["override"]:
        return SectionResult(ok=False, errors={"override": "rehearsal was not green (or was skipped) "
                                             "-- check this box to proceed anyway, or go back and "
                                             "run a green rehearsal first"})
    if not state.get("rehearsal_green") and answers["override"]:
        cl.add("birth", "rehearsal gate", ck.WITNESSED, "OVERRIDDEN by operator")
    if not answers["run"]:
        touched = is_field_touched(state, "birth", "run")
        cl.add("birth", "world birth", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")
        return SectionResult(ok=True, info_lines=("birth skipped by operator.",))

    host = answers["host"].strip() or state.get("pghost", "192.168.122.1")
    db = answers["db"].strip() or state.get("db", "toy")
    name = answers["name"].strip() or answers["world"].strip()
    try:
        world_name = WorldName.parse(answers["world"])
    except WorldNameError as exc:
        return SectionResult(ok=False, errors={"world": str(exc)})
    try:
        # "dest" is Fork/target's own owned field -- read the shared fact directly, never via a
        # field of birth's own (dropped, see `birth_fields`'s own docstring above).
        dest_path = DestPath.parse(state.get("dest", ""))
    except DestPathError as exc:
        return SectionResult(ok=False, errors={"": f"destination (set in Fork/target): {exc}"})
    world, dest = str(world_name), str(dest_path)

    dest_state = destination.classify_destination(dest)
    if (dest_state.kind == destination.DestKind.FOREIGN
            and not state.get("dest_accept_foreign") and not state.get("dest_would_exist")):
        cl.add("birth", "destination classification", ck.REFUSED, f"REFUSED: '{dest}' is FOREIGN")
        return SectionResult(ok=False, errors={"": f"destination '{dest}' (set in Fork/target) is "
                                             "FOREIGN content -- acknowledge it at the fork/target "
                                             "step first"})

    extra = ["--name", name]
    if state.get("governed_patterns"):
        extra += ["--governed", governed_files.governed_flag_value(state["governed_patterns"])]
    if state.get("dest_accept_foreign"):
        extra += ["--accept-existing-content"]
    argv = _new_project_argv(state["_repo_root"], dest, world, db, host, extra=extra)
    lines = [f"$ {' '.join(argv)}", "(the real birth output streams at commit time; this step "
             "only queues the act.)"]
    state["_plan"].append(PlanEntry(
        screen="birth", item="world birth", lesson="the world's founding scaffold + kernel chain",
        act=CommandAct(argv=tuple(argv)), produces=BIRTH_PRODUCES))
    return SectionResult(ok=True, info_lines=tuple(lines), state_updates={
        "world": world, "dest": dest, "dest_would_exist": True, "birth_ok": True,
        "birth_produces": BIRTH_PRODUCES, "birth_world": world, "birth_host": host, "birth_db": db,
        "pghost": host, "db": db,
    })


BIRTH_STEP = SectionSpec(slug="birth", title="Birth", group="World lifecycle",
                          fields=birth_fields, submit=birth_submit, blocked=_birth_blocked)
