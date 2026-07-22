#!/usr/bin/env python3
"""tools/setup_tui/steps_observability.py -- the Observability step's UI-free core, ported from
`screen_observability`."""
from __future__ import annotations

import os

from tools.configtree import ConfirmField, SectionResult, SectionSpec, TextField
from tools.setup_tui import checklist as ck
from tools.setup_tui import daemon_scaffold, feature_facts, probes
from tools.setup_tui.plan import DaemonSelection, PlanEntry, WriteAct


def fields(state: dict) -> tuple:
    return (
        ConfirmField(name="run", label="Configure observability now?", default=True),
        TextField(name="dest", label="Destination directory", default=state.get("dest", ""),
                  shared=True),
        ConfirmField(name="otelcol", label="Select the OTel collector (otelcol-contrib) to start "
                     "with this world?"),
        ConfirmField(name="otel_watch", label="Select the OTel model-provenance watchdog "
                     "(otel-watch) to start with this world?"),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    lines = [feature_facts.facts_block(["observability_otelcol", "observability_watchdog"])]
    if not answers["run"]:
        cl.add("observability", "observability", ck.SKIPPED, "operator skipped screen 9")
        return SectionResult(ok=True, info_lines=("observability configuration skipped.",))

    dest = answers["dest"].strip()
    if not dest:
        return SectionResult(ok=False, errors={"dest": "required"})
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
        cl.add("observability", "otelcol selected", ck.SKIPPED, "operator declined")

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
        cl.add("observability", "otel-watch selected", ck.SKIPPED, "operator declined")

    claude_line = f"cd {dest} && claude"
    lines.append(f"--- INSTRUCTED: Claude launch line ---\n{claude_line}")
    cl.add("observability", "claude launch line", ck.INSTRUCTED, claude_line)
    return SectionResult(ok=True, state_updates={"dest": dest, "observability_engaged": True},
                       info_lines=tuple(lines))


def _blocked_needs_dest(state: dict) -> "str | None":
    """Daemon selection (spec §3 v2's own named example: "daemon selection on chosen features")
    writes its config/scripts INTO the born world's own destination -- nothing to write to until
    Fork/target or Birth has recorded one."""
    if state.get("dest"):
        return None
    return "requires: Fork/target or Birth (a destination directory) to be set first"


STEP = SectionSpec(slug="observability", title="Observability", group="Runtime", fields=fields,
                    submit=submit, blocked=_blocked_needs_dest)
