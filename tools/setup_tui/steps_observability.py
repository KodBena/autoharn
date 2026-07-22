#!/usr/bin/env python3
"""tools/setup_tui/steps_observability.py -- the Observability step's UI-free core, ported from
`screen_observability`."""
from __future__ import annotations

import os

from tools.configtree import ConfirmField, SectionResult, SectionSpec, TextField, is_field_touched
from tools.setup_tui import checklist as ck
from tools.setup_tui import daemon_scaffold, feature_facts, probes
from tools.setup_tui.plan import DaemonSelection, PlanEntry, WriteAct

_SLUG = "observability"


def fields(state: dict) -> tuple:
    # NO "dest" field here (maintainer ruling 2026-07-22, ADR-0019 single-editable-home): the
    # destination directory is owned by Fork/target -- observability reads the shared fact
    # straight out of state in `submit` below, never via a second field declaration (a
    # duplicated projection is refused at App construction,
    # `tools.configtree.spec.validate_shared_ownership`).
    return (
        ConfirmField(name="run", label="Configure observability now?", default=True),
        ConfirmField(name="otelcol", label="Select the OTel collector (otelcol-contrib) to start "
                     "with this world?", help=feature_facts.fact("observability_otelcol").line()),
        ConfirmField(name="otel_watch", label="Select the OTel model-provenance watchdog "
                     "(otel-watch) to start with this world?",
                     help=feature_facts.fact("observability_watchdog").line()),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    lines = [feature_facts.facts_block(["observability_otelcol", "observability_watchdog"])]
    if not answers["run"]:
        touched = is_field_touched(state, _SLUG, "run")
        cl.add("observability", "observability", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")
        return SectionResult(ok=True, info_lines=("observability configuration skipped.",))

    # "dest" is Fork/target's own owned field -- read the shared fact directly (already
    # guaranteed non-empty by `_blocked_needs_dest` below; this section is unreachable otherwise).
    dest = state.get("dest", "").strip()
    if not dest:
        return SectionResult(ok=False, errors={"": "destination (set in Fork/target) required"})
    plan = state["_plan"]

    if answers["otelcol"]:
        export_path = os.path.join(dest, "otel-data", "claude-events.jsonl")
        config_path = os.path.join(dest, "otelcol-config.yaml")
        config_content = daemon_scaffold.otelcol_config_content(export_path)
        lines.append(f"--- queuing write: {config_path} ---\n{config_content}")
        plan.append(PlanEntry(screen="observability", item="otelcol-config.yaml written",
                               lesson="otelcol's own config file (the start line's prerequisite)",
                               act=WriteAct(path=config_path, content=config_content)))
        otelcol_bin = probes.which("otelcol-contrib")
        argv = (otelcol_bin or "otelcol-contrib", "--config", config_path)
        plan.add_daemon(DaemonSelection(
            name="otelcol", argv=argv, cwd=dest,
            env_notes="OTLP gRPC receiver on 127.0.0.1:4317, file exporter",
            health_probe=f"http:{daemon_scaffold.OTELCOL_HEALTH_URL}",
            prerequisite=(otelcol_bin or "otelcol-contrib (not found on PATH at selection time)")))
        lines.append(f"queued daemon: {' '.join(argv)}")
        cl.add("observability", "otelcol selected", ck.INSTRUCTED, f"argv={' '.join(argv)}")
    else:
        touched = is_field_touched(state, _SLUG, "otelcol")
        cl.add("observability", "otelcol selected", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")

    if answers["otel_watch"]:
        watch_bin = str(state["_repo_root"] / "otel-watch")
        argv = (watch_bin, "--daemon")
        plan.add_daemon(DaemonSelection(
            name="otel-watch", argv=argv, cwd=str(state["_repo_root"]),
            env_notes="tails the collector's own JSONL export; no HTTP endpoint of its own",
            health_probe=f"pidof:{watch_bin}",
            prerequisite=(watch_bin if os.path.isfile(watch_bin) else None)))
        lines.append(f"queued daemon: {' '.join(argv)}")
        cl.add("observability", "otel-watch selected", ck.INSTRUCTED, f"argv={' '.join(argv)}")
    else:
        touched = is_field_touched(state, _SLUG, "otel_watch")
        cl.add("observability", "otel-watch selected", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")

    claude_line = f"cd {dest} && claude"
    lines.append(f"--- INSTRUCTED: Claude launch line ---\n{claude_line}")
    cl.add("observability", "claude launch line", ck.INSTRUCTED, claude_line)
    # NOTE: no "dest" in state_updates -- it is Fork/target's own owned fact already, never
    # re-written here (ADR-0012 P1: one writer of one truth).
    return SectionResult(ok=True, state_updates={"observability_engaged": True},
                       info_lines=tuple(lines))


def _blocked_needs_dest(state: dict) -> "str | None":
    """Daemon selection (spec §3 v2's own named example: "daemon selection on chosen features")
    writes its config/scripts INTO the born world's own destination -- nothing to write to until
    Fork/target or Birth has recorded one."""
    if state.get("dest"):
        return None
    return "requires: Fork/target or Birth (a destination directory) to be set first"


STEP = SectionSpec(slug="observability", title="Observability", group="Runtime", fields=fields,
                    submit=submit, blocked=_blocked_needs_dest,
                    description="Optional recurring daemons this world can start at commit -- "
                    "see each checkbox's own aspiration/external-cost note below before "
                    "selecting it.")
