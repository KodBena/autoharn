#!/usr/bin/env python3
"""tools/setup_tui/steps_fork_target.py -- the fork/target step's UI-free core, ported from
`screen_fork_target`. `cp -a`/`mv` become Plan entries (never run directly, as pre-rebuild)."""
from __future__ import annotations

import json
from pathlib import Path

from tools.configtree import (ChoiceField, ConfirmField, SectionResult, SectionSpec, TextField,
                               is_field_touched)
from tools.setup_tui import checklist as ck
from tools.setup_tui import content, destination, feature_facts, governed_files
from tools.setup_tui.plan import CommandAct, PlanEntry

_SLUG = "fork-target"


def _governed_step(state: dict, dest: str, extend: bool, extensions_raw: str) -> tuple[list, list]:
    cl = state["_checklist"]
    lines = [feature_facts.facts_block(["fork_target_governed_files"]), governed_files.TEACHING_LINE,
              f"default pattern set: {governed_files.DEFAULT_PATTERNS}"]
    if not extend:
        patterns = governed_files.DEFAULT_PATTERNS
        cl.add("fork-target", "governed-files pattern set chosen", ck.WITNESSED,
               f"kept default: {patterns}")
    else:
        patterns, hostile = governed_files.build_pattern_set(extensions_raw)
        if hostile:
            lines.append(f"REFUSED: hostile extension token(s) {hostile} -- reverted to default.")
            cl.add("fork-target", "governed-files pattern set chosen", ck.REFUSED,
                   f"hostile token(s) {hostile}; reverted to default {patterns}")
        else:
            cl.add("fork-target", "governed-files pattern set chosen", ck.WITNESSED,
                   f"extended: {patterns}")
    path = governed_files.governed_files_path(dest)
    preview = json.dumps({"patterns": patterns}, indent=2)
    lines.append(f"--- PREVIEW: {path} (written by new-project.sh --governed at birth) ---")
    lines.append(preview)
    return patterns, lines


def fields(state: dict) -> tuple:
    return (
        ConfirmField(name="run", label="Choose destination now?", default=True),
        ChoiceField(name="mode", label="Destination kind?",
                    options=(("fresh", "fresh directory"), ("fork", "fork-copy of an existing project")),
                    default="fresh"),
        TextField(name="dest", label="Destination directory", required=False, shared=True),
        TextField(name="src", label="Source directory to fork-copy (fork mode only)", required=False),
        ConfirmField(name="accept_foreign", label="Accept scaffolding into existing (non-empty, "
                     "non-autoharn) content, if the destination turns out to be FOREIGN?"),
        ConfirmField(name="governed_extend", label=content.SCREEN_PROMPTS["governed_files_extend"]),
        TextField(name="governed_extensions", label="Extensions to add, comma-separated "
                  "(e.g. .ts,.vue,.html)", required=False),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    if not answers["run"]:
        touched = is_field_touched(state, _SLUG, "run")
        cl.add("fork-target", "destination", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")
        return SectionResult(ok=True, info_lines=("fork/target skipped by operator.",))

    dest = answers["dest"].strip()
    if not dest:
        return SectionResult(ok=False, errors={"dest": "required"})
    lines: list[str] = []

    if answers["mode"] == "fresh":
        dest_state = destination.classify_destination(dest)
        if dest_state.kind == destination.DestKind.AUTOHARN_COMPLETE:
            cl.add("fork-target", "destination", ck.REFUSED, f"REFUSED: '{dest}' is AUTOHARN_COMPLETE")
            return SectionResult(ok=False, errors={"dest": "already a complete autoharn world"})
        if dest_state.kind == destination.DestKind.AUTOHARN_PARTIAL:
            cl.add("fork-target", "destination", ck.REFUSED, f"REFUSED: '{dest}' is AUTOHARN_PARTIAL")
            return SectionResult(ok=False, errors={"dest": "an interrupted prior birth (see "
                                                 "bootstrap/teardown-world.sh)"})
        if dest_state.kind == destination.DestKind.FOREIGN and not answers["accept_foreign"]:
            cl.add("fork-target", "destination", ck.REFUSED, "REFUSED: FOREIGN content, not acknowledged")
            return SectionResult(ok=False, errors={"accept_foreign": "destination is non-empty, non-"
                                                 "autoharn content -- check the box to accept it"})
        accept_foreign = dest_state.kind == destination.DestKind.FOREIGN
        cl.add("fork-target", "destination", ck.WITNESSED,
               f"{'FOREIGN content acknowledged' if accept_foreign else 'fresh dir'}: {dest}")
        patterns, glines = _governed_step(state, dest, answers["governed_extend"],
                                           answers["governed_extensions"])
        lines += glines
        updates = {"dest": dest, "governed_patterns": patterns}
        if accept_foreign:
            updates["dest_accept_foreign"] = True
        return SectionResult(ok=True, state_updates=updates, info_lines=tuple(lines))

    src = answers["src"].strip()
    if not src or not Path(src).is_dir():
        cl.add("fork-target", "fork-copy", ck.REFUSED, f"REFUSED: '{src}' not a directory")
        return SectionResult(ok=False, errors={"src": "not a directory"})
    dest_state = destination.classify_destination(dest)
    if dest_state.kind != destination.DestKind.FRESH:
        cl.add("fork-target", "fork-copy", ck.REFUSED, f"REFUSED: '{dest}' is {dest_state.kind.value}")
        return SectionResult(ok=False, errors={"dest": f"already exists ({dest_state.kind.value})"})

    plan = state["_plan"]
    lines.append(f"$ cp -a {src} {dest}")
    plan.append(PlanEntry(screen="fork-target", item="fork-copy", lesson="directory tree copy (cp -a)",
                           act=CommandAct(argv=("cp", "-a", src, dest))))
    src_path, dest_path = Path(src), Path(dest)
    updates: dict = {"dest": dest, "dest_would_exist": True}
    if (src_path / "CLAUDE.md").is_file():
        dest_claude, dest_project = dest_path / "CLAUDE.md", dest_path / "CLAUDE.project.md"
        lines.append(f"$ mv {dest_claude} {dest_project}")
        plan.append(PlanEntry(screen="fork-target", item="CLAUDE.md preserved",
                               lesson="rename to CLAUDE.project.md before the scaffold write",
                               act=CommandAct(argv=("mv", str(dest_claude), str(dest_project)))))
    else:
        cl.add("fork-target", "CLAUDE.md preserved", ck.SKIPPED, "fork source had no CLAUDE.md")
    patterns, glines = _governed_step(state, dest, answers["governed_extend"], answers["governed_extensions"])
    lines += glines
    updates["governed_patterns"] = patterns
    return SectionResult(ok=True, state_updates=updates, info_lines=tuple(lines))


STEP = SectionSpec(slug="fork-target", title="Fork/target", group="Substrate & target",
                    fields=fields, submit=submit,
                    description=feature_facts.fact("fork_target_governed_files").elements())
