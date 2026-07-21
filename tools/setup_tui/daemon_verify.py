#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-21T22:25:09Z
#   last-change: 2026-07-21T22:25:09Z
#   contributors: 43f77bff/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/daemon_verify.py -- the end-of-run daemon-verification sweep
(design/FABLE-SETUP-TUI-CHECKLIST-SPLIT-SPEC.md \xa73 point 3): "one screen-agnostic sweep probes
each DaemonSelection with its health_probe and writes a VERIFIED_UP or a loud not-up row per
daemon." Split into its own module (cohesion, and to keep `commit_executor.py` -- the one
commit boundary -- under ADR-0007's line ceiling): this is READ-ONLY probing logic, a distinct
concern from `daemon_scaffold.py` (pure DATA -- the config template and script text) and from
`commit_executor.py` (the write/resume machinery). `commit_executor.execute` is the only caller,
right after every plan entry (including the generated start-daemons script) has reached DONE.

Every probe here goes through `probes.py`'s own read-only functions (`http_get_json`,
`process_running`) -- never a second implementation of a network/process check (ADR-0012 P1).
Nothing here writes a file, starts a process, or runs a command -- it is outside the §2.8 purity
gate's field of view by construction, the same standing `probes.py` itself already has.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file."""
from __future__ import annotations

from dataclasses import dataclass

from tools.setup_tui import probes
from tools.setup_tui.plan import DaemonSelection


@dataclass
class DaemonVerification:
    """One row of the sweep: "selected but never started" rendered as a NAMED fact, never
    silence. `up`/`detail` are `probes.py`'s own verdict (`http_get_json`'s ok/status, or
    `process_running`'s pid list) -- this dataclass adds no judgment beyond dispatching on
    `DaemonSelection.health_probe`'s closed two-scheme vocabulary."""
    daemon: DaemonSelection
    up: bool
    detail: str


def probe_daemon(sel: DaemonSelection) -> DaemonVerification:
    """Dispatches on `sel.health_probe`'s scheme -- `"http:<url>"` (a GET, ok iff 2xx/3xx) or
    `"pidof:<pattern>"` (a `pgrep -f` liveness check). An empty/unrecognized probe string is the
    honest absence case: NOT-UP, named as such, never a fabricated WITNESSED."""
    probe = sel.health_probe
    if probe.startswith("http:"):
        url = probe[len("http:"):]
        ok, status, _body = probes.http_get_json(url)
        return DaemonVerification(daemon=sel, up=ok, detail=f"GET {url} -> status={status}")
    if probe.startswith("pidof:"):
        pattern = probe[len("pidof:"):]
        ok, detail = probes.process_running(pattern)
        return DaemonVerification(daemon=sel, up=ok, detail=detail)
    return DaemonVerification(
        daemon=sel, up=False,
        detail="no health probe named for this daemon at selection time -- NOT-UP is the "
               "honest absence-rendering (checklist.NOT_UP), never a silent WITNESSED",
    )


def verify_daemons(daemons: "list[DaemonSelection]") -> "list[DaemonVerification]":
    """The full sweep, one probe per selected daemon."""
    return [probe_daemon(d) for d in daemons]
