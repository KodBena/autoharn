#!/usr/bin/env python3
"""tools/setup_tui/tui_app.py -- the ONE place this package imports `textual`
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §6): builds a `tools.configtree.app.ConfigTreeApp` from
`tools.setup_tui.steps.SECTIONS`/`COMMIT`. Genuinely thin -- no Tree/pane code; all of that is
the library's job."""
from __future__ import annotations

from tools.configtree.app import ConfigTreeApp
from tools.setup_tui import content, steps


def build_app(state: dict, *, dry_run: bool) -> ConfigTreeApp:
    banner = str(content.APP_INTRO["dry_run_notice"]) if dry_run else None
    app = ConfigTreeApp(steps.SECTIONS, steps.COMMIT, actions=steps.ACTIONS, initial_state=state,
                         banner=banner, title=str(content.APP_INTRO["heading"]))
    return app
