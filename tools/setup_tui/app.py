#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:34:30Z
#   last-change: 2026-07-18T21:34:30Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/app.py -- entry point for the guided setup wizard
(design/FABLE-SETUP-TUI-SPEC.md). Runs `tools/setup_tui/screens.py`'s nine screens in order,
via the numbered-menu `Ui` backend (`tools/setup_tui/ui.py`) -- either interactive (a human at
the keyboard) or `--scripted <answers-file>` (the SAME screen functions, the SAME `Ui` call
sites, answers sourced from a file instead of stdin -- see `ui.py`'s own docstring for why this
still counts as driving "the same code paths").

Usage:
    python3 -m tools.setup_tui.app
    python3 -m tools.setup_tui.app --scripted /path/to/answers.txt
    python3 -m tools.setup_tui.app --scripted /path/to/answers.txt --start-at boundary

`--start-at <screen>` skips straight to a named screen (preflight, substrate, fork-target,
rehearsal, birth, boundary, observability, hydration, checklist) -- useful for a witness run
that only exercises one screen's flow rather than replaying the whole nine-screen sequence every
time (still drives the same screen function, same Ui, same checklist).
"""
from __future__ import annotations

import argparse
import sys

from tools.setup_tui.checklist import Checklist
from tools.setup_tui.screens import SCREENS
from tools.setup_tui.ui import ScriptExhausted, build_ui


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="setup_tui", description=__doc__)
    p.add_argument("--scripted", metavar="ANSWERS_FILE", default=None,
                    help="drive the flow non-interactively from this answers file")
    p.add_argument("--start-at", metavar="SCREEN", default=None,
                    choices=[name for name, _ in SCREENS],
                    help="skip straight to this screen (still runs the same screen function)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    ui = build_ui(args.scripted)
    cl = Checklist()
    state: dict = {}

    screens = SCREENS
    if args.start_at:
        idx = [name for name, _ in SCREENS].index(args.start_at)
        screens = SCREENS[idx:]

    ui.banner("autoharn setup — guided wizard (tools/setup_tui)")
    ui.say("Driver of existing verbs only: every action below shows the exact command it runs "
           "and streams that command's real output. If this process dies mid-flow, you can "
           "finish by hand from what was printed.")

    try:
        for _, fn in screens:
            state = fn(ui, cl, state)
    except ScriptExhausted as exc:
        print(f"\nsetup_tui: {exc}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("\nsetup_tui: interrupted -- nothing further run. See the streamed output above "
              "for what to finish by hand.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
