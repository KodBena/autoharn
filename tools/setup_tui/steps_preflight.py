#!/usr/bin/env python3
"""tools/setup_tui/steps_preflight.py -- the preflight section's UI-free core (configtree
SectionSpec). Entirely read-only: builds no Plan entries, only checklist rows + info lines.
Ported from the pre-rebuild screens.py's `screen_preflight` -- behavior unchanged, `ui.emit`/
`cl.add` calls replaced by `SectionResult.info_lines`/a returned checklist-row list."""
from __future__ import annotations

import importlib.util
import os

from tools.configtree import ConfirmField, SectionResult, SectionSpec
from tools.setup_tui import checklist as ck
from tools.setup_tui import feature_facts, probes

PREFLIGHT_BINARIES = ("idris2", "clingo", "python3", "psql")


def _preflight_lines(state: dict) -> list[str]:
    lines: list[str] = []
    cl = state["_checklist"]
    repo_root = state["_repo_root"]

    lines.append(f"$ git -C {repo_root} rev-parse HEAD")
    ok, out = probes.git_head_commit(str(repo_root))
    lines.append(f"  repo commit: {'GREEN (' + out + ')' if ok else 'RED -- not a git checkout?'}")
    cl.add("preflight", "repo commit", ck.WITNESSED, out if ok else "RED: git rev-parse HEAD failed")

    lines.append(f"$ git -C {repo_root} submodule status")
    sub_ok, sub_out = probes.git_submodule_status(str(repo_root))
    dash_lines = [ln for ln in sub_out.splitlines() if ln.strip().startswith("-")]
    if sub_ok and not dash_lines:
        lines.append("  submodules populated: GREEN")
        cl.add("preflight", "submodules populated", ck.WITNESSED, "no '-' prefixed entries")
    else:
        lines.append(f"  submodules populated: RED ({len(dash_lines)} uninitialized)")
        lines.append("    fix: git -C <repo> submodule update --init --recursive")
        cl.add("preflight", "submodules populated", ck.WITNESSED,
               f"RED: {len(dash_lines)} uninitialized submodule(s)")

    for name in PREFLIGHT_BINARIES:
        lines.append(feature_facts.facts_block([f"preflight_{name}"]))
        path = probes.which(name)
        if path:
            lines.append(f"  {name}: GREEN ({path})")
            cl.add("preflight", f"{name} found", ck.WITNESSED, path)
        elif name in ("clingo", "idris2"):
            lines.append(f"  {name}: not found on PATH (non-fatal)")
            cl.add("preflight", f"{name} found", ck.WITNESSED, "not on PATH (non-fatal)")
        else:
            lines.append(f"  {name}: RED -- not found on PATH")
            cl.add("preflight", f"{name} found", ck.WITNESSED, "RED: not on PATH")

    host = os.environ.get("HARNESS_PGHOST") or os.environ.get("EPISTEMIC_PGHOST")
    if not host:
        lines.append("  HARNESS_PGHOST: RED -- not set (export HARNESS_PGHOST=<host>)")
        cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED, "RED: unset")
    else:
        ok2, detail = probes.pg_reachable(host)
        lines.append(f"  HARNESS_PGHOST ({host}): {'GREEN' if ok2 else 'RED'} -- {detail}")
        cl.add("preflight", "HARNESS_PGHOST reachable", ck.WITNESSED,
               f"{'GREEN' if ok2 else 'RED'}: {detail}")
        state["pghost"] = host

    for name in ("textual", "urwid"):
        lines.append(feature_facts.facts_block([f"ui_backend_{name}"]))
        available = importlib.util.find_spec(name) is not None
        lines.append(f"  {name}: {'available' if available else 'not installed'}")
        cl.add("preflight", f"{name} available", ck.WITNESSED,
               "available" if available else "not installed")
    return lines


def fields(state: dict) -> tuple:
    return (ConfirmField(name="run", label="Run preflight checks?", default=True),)


def submit(state: dict, answers: dict) -> SectionResult:
    if not answers["run"]:
        state["_checklist"].add("preflight", "all checks", ck.SKIPPED, "operator skipped screen 1")
        return SectionResult(ok=True, info_lines=("preflight skipped by operator.",))
    lines = _preflight_lines(state)
    return SectionResult(ok=True, info_lines=tuple(lines))


STEP = SectionSpec(slug="preflight", title="Preflight", group="Substrate & target",
                    fields=fields, submit=submit)
