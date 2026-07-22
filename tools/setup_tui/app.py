#!/usr/bin/env python3
"""tools/setup_tui/app.py -- entry point for the guided setup wizard
(design/FABLE-SETUP-TUI-SPEC.md). Runs `tools/setup_tui/screens.py`'s eleven screens in order
(design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md's "Signed genesis" screen sits between Principals
& authority and Boundary, commission ledger rows 1724/1725; design/FABLE-SETUP-TUI-PRINCIPALS-
AUTHORITY-SPEC.md's "Principals & authority" screen sits between Birth and Signed genesis,
commission ledger row 1727),
via one of THREE `Ui` backends (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md, commission ledger row
1818) -- the SAME screen functions, the SAME `Ui` call sites, every time:

  * `TextualUi` (`tools/setup_tui/ui_textual.py`) -- a real Textual application. Selected for
    interactive runs when `textual` is importable (the default now that this build's spec
    supersedes the v1 "library ONLY if already installed" clause).
  * `InteractiveUi` (`tools/setup_tui/ui.py`) -- the zero-dependency numbered-menu fallback.
    Forced by `--plain`, or selected automatically (with one teaching line) when `textual` is not
    importable ("degraded-but-possible beats frozen").
  * `ScriptedUi` -- `--scripted <answers-file>` (a human is never at the keyboard; answers are
    consumed in prompt order). `--scripted` NEVER selects `TextualUi` -- headless witnessing must
    not grow a dependency.

Usage:
    python3 -m tools.setup_tui.app
    python3 -m tools.setup_tui.app --plain
    python3 -m tools.setup_tui.app --scripted /path/to/answers.txt
    python3 -m tools.setup_tui.app --scripted /path/to/answers.txt --start-at boundary
    python3 -m tools.setup_tui.app --dry-run --scripted /path/to/answers.txt

`--start-at <screen>` skips straight to a named screen (preflight, substrate, fork-target,
rehearsal, birth, principals-authority, signed-genesis, boundary, observability, hydration,
checklist) -- useful for a witness run
that only exercises one screen's flow rather than replaying the whole eleven-screen sequence
every time (still drives the same screen function, same Ui, same checklist).

`--dry-run` (design/FABLE-SETUP-TUI-SPEC.md 2026-07-19 amendment) runs the SAME ten screens,
composes with `--scripted`, `--plain`, and `--start-at` unchanged, but performs no destructive or
externally visible act: `state["dry_run"]` is set once here and read by `tools/setup_tui/
runner.py`'s three act-execution choke points (`run_command`, `start_background`, `write_file`)
and by `checklist.status_for`/`Checklist.save` -- no screen carries its own dry-run conditional.
Every screen still computes and shows its would-be acts (rule 1's exact-argv discipline is
unconditional); the closing checklist renders WOULD-DO/DRY-SKIPPED rows instead of
WITNESSED/PREPARED-verified ones. Read-only probes (preflight, connection checks, the pg_hba
read, the ADR glob) are UNCHANGED by `--dry-run` -- they stay live, because a rehearsal that
fakes its reads is a lie, not a rehearsal. Under `TextualUi` the dry-run notice ALSO renders as a
persistent banner (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §2 item 2), not merely a transcript
line that can scroll out of view.

v1 THREAT MODEL (ledger row 1810 finding 3, stated plainly rather than left implicit): this tool
is built for a SINGLE operator running it SEQUENTIALLY, one invocation at a time, against a given
destination. Concurrent invocations racing the SAME destination (two operators, or one operator
in two terminals) are OUT OF SCOPE BY DESIGN in v1 -- the isolation discipline this catalog
hydrates for the WORLDS it births (concurrent builders need worktree/serial isolation, per the
catalog items this wizard drives an operator through) governs those worlds, not this wizard's own
process against its own destination directory while it runs.

Import factoring (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §3, the lazy-import gate's own carve-
out): `textual` is optional for THIS package, so its import here is a top-level `try`/`except
ImportError`, never a function-body import -- eager at module-import time either way
(`gates/no_lazy_imports.py` only flags a function-body import, and explicitly permits a
module-level `try`/`except`). `tools/setup_tui/ui_textual.py` itself carries the honest,
unconditional `import textual`; this is the ONE place in the package that declares "textual may
not be here" instead of assuming it.
"""
from __future__ import annotations

import argparse
import copy
import signal
import subprocess
import sys

from tools.setup_tui import config_file, config_seam
from tools.setup_tui.checklist import Checklist
from tools.setup_tui.content import app_data as AD
from tools.setup_tui.elements import Heading, Note, Paragraph, Rule
from tools.setup_tui.flow_position import FlowPosition, run_screen
from tools.setup_tui.screens import SCREENS
from tools.setup_tui.ui import ScriptedUi, ScriptExhausted, Ui, build_ui

try:
    from tools.setup_tui import ui_textual
except ImportError:
    ui_textual = None  # type: ignore[assignment]


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="setup_tui", description=__doc__)
    p.add_argument("--scripted", metavar="ANSWERS_FILE", default=None,
                    help="drive the flow non-interactively from this answers file")
    p.add_argument("--start-at", metavar="SCREEN", default=None,
                    choices=[name for name, _ in SCREENS],
                    help="skip straight to this screen (still runs the same screen function)")
    p.add_argument("--dry-run", action="store_true", default=False,
                    help="perform no destructive or externally visible act; every screen "
                         "computes and shows its would-be acts, the closing checklist renders "
                         "them WOULD-DO instead of WITNESSED (design/FABLE-SETUP-TUI-SPEC.md "
                         "2026-07-19 amendment)")
    p.add_argument("--plain", action="store_true", default=False,
                    help="force the zero-dependency numbered-menu interface even when "
                         "'textual' is installed (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md "
                         "selection rule); implied automatically, with one teaching line, when "
                         "'textual' is not importable")
    p.add_argument("--accept-unverified-genesis", action="store_true", default=False,
                    help="GENESIS-GATE OVERRIDE (ledger row 1918): by default, if the Signed "
                         "genesis ceremony's verify-commission gate does not confirm VERIFIED, "
                         "the commit HALTS there (non-zero exit; AUTOHARN_BACKFLOW.md finding "
                         "1's class -- a world must never complete birth on an unverifiable "
                         "genesis signature silently). This flag proceeds anyway, eyes open: "
                         "the world's audit chain will anchor to a signature that did not "
                         "verify, recorded as its own explicit checklist row, never silent. "
                         "Applies to every backend, including --scripted (the flag rides the "
                         "process argv, not an answers-file line).")
    # CONFIG-FILE (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md, ledger row 1944) -- the two
    # consumption modes, plus the two CLI parameters --from-config pairs a config with.
    p.add_argument("dest_dir", nargs="?", default=None, metavar="DEST_DIR",
                    help="destination directory -- REQUIRED with --from-config (spec §2: "
                         "--world/DEST_DIR are the only per-project variables a config needs)")
    p.add_argument("--from-config", metavar="CONFIG_FILE", default=None,
                    help="non-interactive application of a config file -- requires --world and "
                         "DEST_DIR; REFUSES up front on a missing/unknown key or an "
                         "already-existing world, never a mid-flow interactive fallback")
    p.add_argument("--world", metavar="NAME", default=None,
                    help="the world name --from-config births -- REFUSED if a schema/kernel "
                         "schema of this name already exists on the target Postgres, or if "
                         "DEST_DIR's own sentinel names a different world")
    p.add_argument("--initial-config", metavar="CONFIG_FILE", default=None,
                    help="interactive run, config values pre-loaded as each prompt's default "
                         "(the 'known good configuration' the operator edits individually) -- "
                         "partial configs are fine, missing keys keep normal defaults")
    return p.parse_args(argv)


def _check_config_flags(args: argparse.Namespace) -> None:
    """Spec §2's mode discipline, refused up front rather than discovered mid-flow."""
    if args.from_config and not (args.world and args.dest_dir):
        raise SystemExit("setup_tui: --from-config requires both --world NAME and a "
                          "destination directory (positional argument).")
    if (args.world or args.dest_dir) and not args.from_config:
        raise SystemExit("setup_tui: --world/DEST_DIR are only meaningful together with "
                          "--from-config.")
    if args.from_config and args.initial_config:
        raise SystemExit("setup_tui: --from-config and --initial-config are mutually exclusive "
                          "-- pick one consumption mode (design/FABLE-SETUP-TUI-CONFIG-FILE-"
                          "SPEC.md §2).")
    if args.from_config and args.scripted:
        raise SystemExit("setup_tui: --scripted and --from-config are mutually exclusive -- "
                          "--from-config already drives a non-interactive run.")
    if args.from_config and args.start_at:
        raise SystemExit("setup_tui: --from-config does not compose with --start-at -- the "
                          "synthesized answer sequence assumes the full eleven-screen flow "
                          "(out of scope for this build; run the two modes separately).")


def _run_from_config(args: argparse.Namespace) -> int:
    """`--from-config`: validate, refuse-before-any-act (spec §3), compile to the EXISTING
    `--scripted` answers-file shape, then drive it through the exact same `ScriptedUi` path a
    real `--scripted` run takes (`config_seam`'s own module docstring explains why that is the
    correct, not merely convenient, choice for the Signed genesis leg)."""
    try:
        doc = config_file.load_config_file(args.from_config)
        config_file.validate(doc, require_complete=True)
    except config_file.ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    host = str(config_file.get(doc, "substrate.host", "192.168.122.1"))
    db = str(config_file.get(doc, "substrate.db", "toy"))
    refusal = config_seam.check_world_and_dest(world=args.world, dest=args.dest_dir, host=host,
                                                db=db)
    if refusal:
        print(f"setup_tui: {refusal}", file=sys.stderr)
        return 1
    lines = config_seam.synthesize_scripted_lines(doc, world=args.world, dest=args.dest_dir)
    with config_seam.scripted_answers_file(lines) as answers_path:
        ui = ScriptedUi(answers_path)
        cl = Checklist()
        state: dict = {"dry_run": args.dry_run,
                       "accept_unverified_genesis": args.accept_unverified_genesis}
        state_holder: list[dict] = [state]
        return _run_plain(ui, cl, state, state_holder, SCREENS, args)


def _select_backend(args: argparse.Namespace) -> tuple[str, Ui | None]:
    """Selection (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §3): `--scripted` NEVER touches
    textual (returns `ScriptedUi` straight away); `--plain` forces the numbered-menu fallback
    explicitly, no teaching needed (the operator already chose it); otherwise `TextualUi` when
    `textual` is importable, else ONE teaching line naming the exact venv/pip command, then the
    numbered-menu fallback proceeds ("degraded-but-possible beats frozen"). Returns
    `(backend_name, ui_or_None)` -- `ui` is `None` only for `"textual"`, since that backend
    needs a live `SetupWizardApp` instance to bridge to (`_run_textual` builds both together)."""
    if args.scripted:
        return "scripted", build_ui(args.scripted)
    if args.plain:
        return "plain", build_ui(None)
    if ui_textual is not None:
        return "textual", None
    print(
        "setup_tui: 'textual' is not installed -- the guided wizard's real TUI face needs it.\n"
        "  Install it into this interpreter's venv, e.g.:\n"
        "    python3 -m venv .venv && .venv/bin/pip install textual\n"
        "  (or, inside an already-active venv: pip install textual)\n"
        "  Falling back to the numbered-menu interface for this run -- pass --plain to choose "
        "it explicitly and silence this line.",
        file=sys.stderr,
    )
    return "plain", build_ui(None)


def _intro(ui: Ui, args: argparse.Namespace) -> None:
    """The banner + dry-run notice every backend shows, identically, before the screen loop
    starts -- factored out so `_run_plain` and `_run_textual` (via the Textual worker body) call
    the exact same sequence of `Ui` calls rather than two copies that could drift."""
    ui.emit(Heading(AD.INTRO_HEADING))
    ui.emit(Paragraph(AD.INTRO_DRIVER_LINE))
    # NAVIGATION (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md, observation (e)): named once here,
    # not repeated at every prompt (spec §3). Stops at the final review screen's own commit
    # confirm -- see `_drive_screens`'s own docstring for why.
    ui.emit(Note(AD.NAV_HINT, tone="info"))
    ui.emit(Rule())
    ui.emit(Paragraph(AD.GUARANTEE_ENVELOPE_HEADING))
    for text in AD.GUARANTEE_ENVELOPE_PARAGRAPHS:
        ui.emit(Paragraph(text))
    if args.dry_run:
        ui.emit(Rule())
        ui.emit(Note(AD.DRY_RUN_NOTICE, tone="warn"))


def _drive_screens(ui: Ui, cl: Checklist, state: dict, state_holder: list[dict],
                    screens: list) -> int:
    """The core screen-loop body (ledger row 1799 finding 6's try/finally discipline), shared by
    every backend: runs `screens` in order, guarantees `_terminate_boundary_proc` fires on any
    ABNORMAL exit (a typed `ScriptExhausted`/`KeyboardInterrupt`, or an ordinary uncaught
    exception this function does not swallow -- including `tools.setup_tui.ui_textual.
    WizardShutdown`, the Textual worker's own deliberate-shutdown signal, which propagates
    through exactly the same "ordinary uncaught exception" path and is caught one level up, by
    the Textual worker body, never here). `completed_normally` keeps the `finally` block from
    ALSO firing on the success path, where a boundary service `screen_boundary` started is the
    operator's live service and is meant to keep running after the wizard exits cleanly.

    BACKWARD NAVIGATION (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md, observation (e)): a
    `FlowPosition` tracks every screen completed so far; `tools.setup_tui.flow_position.
    run_screen` (called below) does the per-screen work of wrapping `ui` in a `NavigableUi`,
    catching `NavigateBack`, and popping/restoring the cursor -- see its own docstring for the
    exact contract and for why the final screen (the commit boundary) is never wrapped."""
    completed_normally = False
    # --initial-config (design/FABLE-SETUP-TUI-CONFIG-FILE-SPEC.md §2): `main()` stashes the
    # {screen: {prompt: value}} seed under this transient state key -- popped here (never left
    # in `state`, which every screen also reads) and handed to `FlowPosition` as `last_answers`,
    # the SAME slot backward-navigation already re-offers a revisited screen's own prior answers
    # from (config_seam.build_initial_prior_answers's own docstring: "works with navigation").
    initial_prior = state.pop("_initial_config_prior_answers", {})
    flow = FlowPosition(base_state=copy.deepcopy(state), last_answers=initial_prior)
    idx = 0
    try:
        try:
            while idx < len(screens):
                name, fn = screens[idx]
                state, advance, went_back = run_screen(
                    fn, ui, cl, state, name, idx == len(screens) - 1, flow)
                state_holder[0] = state
                if went_back:
                    idx -= 1
                    continue
                if not advance:
                    print(f"\nsetup_tui: already at the first screen ('{name}') -- nothing to "
                          f"go back to; re-asking this screen.", file=sys.stderr)
                    continue
                idx += 1
            completed_normally = True
        except ScriptExhausted as exc:
            print(f"\nsetup_tui: {exc}", file=sys.stderr)
            return 3
        except KeyboardInterrupt:
            print("\nsetup_tui: interrupted -- nothing further run. See the streamed output "
                  "above for what to finish by hand.", file=sys.stderr)
            return 130
    finally:
        if not completed_normally:
            _terminate_boundary_proc(state_holder[0])

    # GENESIS-GATE HARD-STOP (ledger row 1918): a halted commit -- `screens.py`'s `_execute_
    # commit` sets `state["commit_halted"]` whenever `commit_executor.execute()` returns
    # `completed=False` (the genesis-gate verify-commission stop is one instance of this; ANY
    # commit-entry failure halts the same way) -- must exit NON-ZERO. Previously this function
    # always returned 0 once the screen loop itself finished without an exception, even when the
    # commit it drove never completed: indistinguishable from success to a caller checking only
    # the process exit code. `2` is otherwise unused by this module (3/130/1/128+SIGTERM already
    # taken).
    if state_holder[0].get("commit_halted"):
        return 2
    return 0


def _run_plain(ui: Ui, cl: Checklist, state: dict, state_holder: list[dict], screens: list,
                args: argparse.Namespace) -> int:
    """`InteractiveUi`/`ScriptedUi` path -- BYTE-IDENTICAL in behavior to this module before the
    Textual build (every existing seen-red fixture stays green unmodified, per that build's own
    hard constraint): same prints, same order, same SIGTERM handling, same exit codes. The only
    difference from the pre-Textual `main()` is mechanical factoring (`_intro`/`_drive_screens`
    extracted so `_run_textual` can share them), not behavior."""
    # `state_holder` is the SIGTERM handler's only view of the live `state` dict -- registered
    # once below, before the screen loop starts, and kept current every iteration (screens
    # mutate `state` in place and also return it, so `state_holder[0] = state` inside
    # `_drive_screens` after each call is cheap insurance against a screen that ever returns a
    # fresh dict instead of mutating). A bare closure over the loop-local `state` name would see
    # whatever `state` was bound to at REGISTRATION time, not at SIGNAL time -- the one-element
    # list is the mutable indirection that keeps the handler honest across every reassignment.
    def _handle_sigterm(signum: int, frame: object) -> None:
        # `kill <pid>` sends SIGTERM by default -- without this handler the interpreter's
        # default disposition (terminate immediately, no cleanup) orphans a boundary_proc
        # screen_boundary started (this module's own docstring/rule 1: "no hidden state" applies
        # to what THIS process started, not only to the acts it merely printed). This invokes
        # the SAME termination path the normal-exit branches already use, then exits nonzero
        # (128 + SIGTERM, the standard shell convention for a signal-caused exit) rather than
        # returning from main() the ordinary way.
        print("\nsetup_tui: received SIGTERM -- terminating any boundary service this process "
              "started before exiting (no orphaned residue).", file=sys.stderr)
        _terminate_boundary_proc(state_holder[0])
        sys.exit(128 + signal.SIGTERM)

    signal.signal(signal.SIGTERM, _handle_sigterm)

    _intro(ui, args)
    return _drive_screens(ui, cl, state, state_holder, screens)


def _run_textual(cl: Checklist, state: dict, state_holder: list[dict], screens: list,
                  args: argparse.Namespace) -> int:
    """`TextualUi` path (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §2). The App must exist and be
    RUNNING (its asyncio loop live) before any `Ui` call can bridge to it via `call_from_thread`
    -- so, unlike `_run_plain`, the intro banner and the whole screen loop run INSIDE the
    Textual worker thread (`SetupWizardApp.wizard_body`, set here, run by `on_mount`), not
    before `app.run()` is called."""
    if not sys.stdin.isatty():
        # Same honest refusal `ui.build_ui` already gives the plain-interactive path -- Textual's
        # own driver would otherwise fail with a less legible error against a non-terminal stdin.
        raise SystemExit(
            "setup_tui: stdin is not a terminal and --scripted was not given -- refusing to "
            "run an interactive flow against a non-interactive stdin (it would hang or read "
            "garbage). Pass --scripted <answers-file> for a non-interactive run, or --plain if "
            "you have a terminal but want the numbered-menu interface."
        )

    app = ui_textual.SetupWizardApp(dry_run=args.dry_run, checklist=cl)
    ui = ui_textual.TextualUi(app)

    def _wizard_body() -> None:
        _intro(ui, args)
        try:
            code = _drive_screens(ui, cl, state, state_holder, screens)
        except ui_textual.WizardShutdown:
            # A deliberate shutdown (SIGTERM, or the operator quitting the App mid-flow) --
            # `request_shutdown` below already set the return code and asked the App to exit;
            # letting this propagate further would be read as a worker crash (Textual's
            # `exit_on_error` panic path), the wrong signal for an expected, requested unwind.
            return
        app.call_from_thread(app.exit, return_code=code)

    app.wizard_body = _wizard_body

    def _handle_sigterm(signum: int, frame: object) -> None:
        # Same cleanup obligation as `_run_plain`'s handler, adapted for the Textual shell
        # (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §2 item 5): terminate any boundary service
        # THIS process started, and ask the App to exit (never a raw `sys.exit()` here -- that
        # would skip Textual's own terminal-restore teardown and leave the shell in alternate-
        # screen/raw mode).
        #
        # ORDER IS LOAD-BEARING (calibrated empirically -- this build's own WX5 stress pass,
        # see the report, hit an intermittent hang before this reordering): `request_shutdown`
        # runs FIRST, never after. `_terminate_boundary_proc` calls `proc.wait(timeout=5)` --
        # up to 5 SYNCHRONOUS seconds on THIS thread (a signal handler; Python only ever
        # delivers a signal to the main thread, so this freezes the App's own asyncio loop for
        # that whole window, since nothing else can run on this thread until the handler
        # returns). If a worker thread happens to be mid-bridge-call at that exact moment
        # (`ui_textual._call_from_thread_safe`, itself bounded so it cannot hang forever), that
        # frozen loop is what it is waiting ON -- calling `request_shutdown` first sets the
        # shutdown event and resolves any ALREADY-armed prompt synchronously, right here, before
        # the freeze, so a worker parked in `_wait_answer` or about to start a NEW bridge call
        # (which checks the shutdown event before it even tries) unblocks immediately rather
        # than queueing behind the boundary-proc wait. The boundary proc is still terminated
        # before this handler returns -- cleanup is not skipped, only reordered.
        print("\nsetup_tui: received SIGTERM -- terminating any boundary service this process "
              "started before exiting (no orphaned residue).", file=sys.stderr)
        app.request_shutdown(128 + signal.SIGTERM)
        _terminate_boundary_proc(state_holder[0])

    signal.signal(signal.SIGTERM, _handle_sigterm)

    try:
        app.run()
    except Exception as exc:  # noqa: BLE001 -- see below: this never hides the failure
        # Textual's own `exit_on_error=True` (the default `run_worker` behavior) already turns
        # an uncaught WORKER exception into a legible panic/crash report, terminal cleanly
        # restored first, before re-raising it here (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §2
        # item 5: "a worker exception must surface legibly ... never vanish into a blank
        # alternate screen" -- verified empirically, see this build's report). This catch exists
        # only so `main()` returns a plain nonzero exit code instead of a SECOND, redundant raw
        # Python traceback stacked on top of the one Textual already printed.
        print(f"setup_tui: the Textual application exited on an unhandled error: {exc}",
              file=sys.stderr)
        return 1
    return app.return_code or 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    _check_config_flags(args)
    if args.from_config:
        return _run_from_config(args)

    cl = Checklist()
    state: dict = {"dry_run": args.dry_run,
                   "accept_unverified_genesis": args.accept_unverified_genesis}
    if args.initial_config:
        try:
            initial_doc = config_file.load_config_file(args.initial_config)
            config_file.validate(initial_doc, require_complete=False)
        except config_file.ConfigError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        state["_initial_config_prior_answers"] = config_seam.build_initial_prior_answers(
            initial_doc)
    state_holder: list[dict] = [state]

    screens = SCREENS
    if args.start_at:
        idx = [name for name, _ in SCREENS].index(args.start_at)
        screens = SCREENS[idx:]

    backend, ui = _select_backend(args)
    if backend == "textual":
        return _run_textual(cl, state, state_holder, screens, args)
    assert ui is not None  # "scripted"/"plain" always build a Ui above
    return _run_plain(ui, cl, state, state_holder, screens, args)


def _terminate_boundary_proc(state: dict) -> None:
    """If screen_boundary started a live service (`state["boundary_proc"]`), an abnormal exit
    from this process must not leave it running silently, orphaned, and unmentioned -- rule 1
    ("no hidden state") applies to what THIS process itself started, not only to the cluster-
    host acts it merely printed. Terminates it and says so; a process this function never
    started (the boundary screen not reached, or the PREPARED/systemd path taken) is left
    untouched."""
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
