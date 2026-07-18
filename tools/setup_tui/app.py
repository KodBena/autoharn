#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-18T21:34:30Z
#   last-change: 2026-07-18T22:47:19Z
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
import signal
import subprocess
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
    # `state_holder` is the SIGTERM handler's only view of the live `state` dict -- registered
    # once below, before the screen loop starts, and kept current every iteration (screens
    # mutate `state` in place and also return it, so `state_holder[0] = state` after each call
    # is cheap insurance against a screen that ever returns a fresh dict instead of mutating).
    # A bare closure over the loop-local `state` name would see whatever `state` was bound to at
    # REGISTRATION time, not at SIGNAL time -- the one-element list is the mutable indirection
    # that keeps the handler honest across every reassignment.
    state_holder: list[dict] = [state]

    def _handle_sigterm(signum: int, frame: object) -> None:
        # `kill <pid>` sends SIGTERM by default -- without this handler the interpreter's
        # default disposition (terminate immediately, no cleanup) orphans a boundary_proc
        # screen_boundary started (app.py's own docstring/rule 1: "no hidden state" applies to
        # what THIS process started, not only to the acts it merely printed). This invokes the
        # SAME termination path the normal-exit branches above already use, then exits nonzero
        # (128 + SIGTERM, the standard shell convention for a signal-caused exit) rather than
        # returning from main() the ordinary way.
        print("\nsetup_tui: received SIGTERM -- terminating any boundary service this process "
              "started before exiting (no orphaned residue).", file=sys.stderr)
        _terminate_boundary_proc(state_holder[0])
        sys.exit(128 + signal.SIGTERM)

    signal.signal(signal.SIGTERM, _handle_sigterm)

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
            state_holder[0] = state
    except ScriptExhausted as exc:
        print(f"\nsetup_tui: {exc}", file=sys.stderr)
        _terminate_boundary_proc(state)
        return 3
    except KeyboardInterrupt:
        print("\nsetup_tui: interrupted -- nothing further run. See the streamed output above "
              "for what to finish by hand.", file=sys.stderr)
        _terminate_boundary_proc(state)
        return 130

    return 0


def _terminate_boundary_proc(state: dict) -> None:
    """If screen_boundary started a live service (`state["boundary_proc"]`), an abnormal exit
    from this process must not leave it running silently, orphaned, and unmentioned -- rule 1
    ("no hidden state") applies to what THIS process itself started, not only to the cluster-
    host acts it merely printed. Terminates it and says so; a process this function never
    started (screen 6 not reached, or the PREPARED/systemd path taken) is left untouched."""
    proc = state.get("boundary_proc")
    if proc is None or proc.poll() is not None:
        return
    print(f"setup_tui: terminating the boundary service this process started (pid {proc.pid}) "
          f"before exiting -- it will not be left running silently.", file=sys.stderr)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
