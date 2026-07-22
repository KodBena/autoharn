#!/usr/bin/env python3
"""tools/setup_tui/app.py -- entry point for the guided setup wizard
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md, the 2026-07-22 wholesale rebuild). Interactive mode is
Textual, full stop -- `tools/configtree`'s hierarchical configuration editor (a sidebar `Tree` of
the ENTIRE configuration, a form pane per section, dependency-as-data blocking, a commit node;
see `tools/setup_tui/tui_app.py`). If `textual` is not importable, this REFUSES with the install
command -- there is no fallback UI to maintain (`--from-config` is the no-TUI path; §3 v2's own
superseded-v1 text named this, unchanged by the amendment).

Usage:
    python3 -m tools.setup_tui
    python3 -m tools.setup_tui --dry-run
    python3 -m tools.setup_tui --initial-config /path/to/config.toml
    python3 -m tools.setup_tui --from-config /path/to/config.toml --world myworld /path/to/dest
    python3 -m tools.setup_tui --dry-run --from-config /path/to/config.toml --world w /path/to/d

`--dry-run` (unchanged semantics from the pre-rebuild wizard): every section still computes and
shows its would-be acts; the commit node performs no destructive or externally visible act, and
the closing checklist renders WOULD-DO rows instead of WITNESSED ones. Read-only probes stay
live -- a rehearsal that fakes its reads is a lie, not a rehearsal.

EXIT CODES (closed vocabulary, `tools.configtree.ExitCode`'s own contract): 0 clean completion;
1 a pre-flight refusal (bad flags, an unreadable/incomplete config file, a world/destination the
config seam refuses before any act); 2 the commit boundary itself halted (a commit-entry failure,
the genesis-gate hard-stop being the one currently-named instance); 3 a `--from-config` run's
synthesized answers were rejected by a section's own validator (a config-vs-schema mismatch --
the config file passed its own schema check but a section disagrees at apply time); 130
interrupted (SIGINT/SIGTERM), the standard shell convention.

Lazy imports are banned (CLAUDE.md, 2026-07-02): `tui_app`'s own `textual` dependency is imported
guarded by a top-level `try`/`except ImportError`, never a function-body import."""
from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import textwrap

from tools.configtree.measure import MEASURE
from tools.setup_tui import config_file, config_seam, steps
from tools.setup_tui.checklist import Checklist
from tools.setup_tui.plan import Plan

try:
    from tools.setup_tui import tui_app
except ImportError:
    tui_app = None  # type: ignore[assignment]


def _wrap(text: str) -> str:
    """The plain-text twin of `tools.configtree.app`'s CSS measure cap (maintainer round 4: "any
    place prose ... can render, in both the Textual panes and any plain-text output paths").
    `print()`ing a free-prose diagnostic straight to a real terminal has the SAME class of defect
    the Textual widgets had: the string is however long it is, and a very wide terminal (or a
    redirect to a file) shows it as one unbroken line -- several of this module's own messages
    were, at RUNTIME, exactly that (source-code line breaks between adjacent string literals are
    NOT newlines; Python concatenates them into one continuous string with nothing between).
    `textwrap.fill` at the SAME `MEASURE` the Textual layer uses is this module's own single
    render seam -- called at every free-prose print site, never at a TABULAR one (a checklist
    row, a `$ <argv>` echo, an install-command line an operator copy-pastes verbatim -- those
    keep the deleted `tools/setup_tui/elements.py`'s own "last column/command line never
    wrapped" exemption, the same one `tools/configtree/app.py`'s CSS deliberately carries
    forward)."""
    return textwrap.fill(text, width=MEASURE)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="setup_tui", description=__doc__)
    p.add_argument("--dry-run", action="store_true", default=False,
                    help="perform no destructive or externally visible act; every section still "
                         "computes and shows its would-be acts, the closing checklist renders "
                         "them WOULD-DO instead of WITNESSED")
    p.add_argument("--accept-unverified-genesis", action="store_true", default=False,
                    help="GENESIS-GATE OVERRIDE (ledger row 1918): by default, if the Signed "
                         "genesis ceremony's verify-commission gate does not confirm VERIFIED, "
                         "the commit HALTS there (exit 2). This flag proceeds anyway, eyes open.")
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
                    help="interactive run, config values pre-loaded as each section's default -- "
                         "partial configs are fine, missing keys keep normal defaults")
    return p.parse_args(argv)


def _check_config_flags(args: argparse.Namespace) -> None:
    """Spec §2's mode discipline, refused up front rather than discovered mid-flow."""
    if args.from_config and not (args.world and args.dest_dir):
        raise SystemExit(_wrap("setup_tui: --from-config requires both --world NAME and a "
                               "destination directory (positional argument)."))
    if (args.world or args.dest_dir) and not args.from_config:
        raise SystemExit(_wrap("setup_tui: --world/DEST_DIR are only meaningful together with "
                               "--from-config."))
    if args.from_config and args.initial_config:
        raise SystemExit(_wrap("setup_tui: --from-config and --initial-config are mutually "
                               "exclusive -- pick one consumption mode (design/FABLE-SETUP-TUI-"
                               "CONFIG-FILE-SPEC.md §2)."))


def _run_from_config(args: argparse.Namespace) -> int:
    """`--from-config`: validate, refuse-before-any-act (spec §3), then drive every section's
    `submit` directly against the synthesized per-section answers dict
    (`config_seam.answers_for_from_config`) -- zero Textual involved, the headless witness."""
    try:
        doc = config_file.load_config_file(args.from_config)
        config_file.validate(doc, require_complete=True)
    except config_file.ConfigError as exc:
        print(_wrap(str(exc)), file=sys.stderr)
        return 1
    host = str(config_file.get(doc, "substrate.host", "192.168.122.1"))
    db = str(config_file.get(doc, "substrate.db", "toy"))
    refusal = config_seam.check_world_and_dest(world=args.world, dest=args.dest_dir, host=host,
                                                db=db)
    if refusal:
        print(_wrap(f"setup_tui: {refusal}"), file=sys.stderr)
        return 1
    answers_by_slug = config_seam.answers_for_from_config(doc, world=args.world, dest=args.dest_dir)

    state = steps.initial_state(dry_run=args.dry_run,
                                 accept_unverified_genesis=args.accept_unverified_genesis)
    state_holder: list[dict] = [state]
    _install_sigterm_handler(state_holder)
    for section in steps.SECTIONS:
        slug = str(section.slug)
        answers = answers_by_slug.get(slug, {})
        result = section.submit(state, answers)
        if not result.ok:
            print(_wrap(f"setup_tui: --from-config REFUSED at section '{slug}': "
                        f"{result.errors}"), file=sys.stderr)
            _terminate_boundary_proc(state)
            return 3
        if result.state_updates:
            state.update(result.state_updates)
        # NOTE: no blind `state.update(answers)` here (removed 2026-07-22 -- the SAME
        # bare-field-name aliasing hazard class the maintainer caught live in the interactive
        # Tree+Form UI, ADR-0012 cancer C/P1/P2: a per-section-local answer like "host"/"run"
        # written to a bare top-level key could silently be read back by an UNRELATED later
        # section's own same-named field. No `submit()` in this package actually reads such a
        # bare per-field key (verified: every `state.get(...)` read inside a `submit` is either
        # an infrastructure key or an explicitly-named cross-section fact written via THIS
        # section's own `state_updates`), so the copy was dead weight as well as a hazard --
        # removing it changes no observable behavior, only deletes the risk).
        for line in result.info_lines:
            print(line)
    commit_result = steps.commit(state)
    for line in commit_result.info_lines:
        print(line)
    if state.get("commit_halted"):
        return 2
    return 0


def _install_sigterm_handler(state_holder: list[dict]) -> None:
    def _handle_sigterm(signum: int, frame: object) -> None:
        print("\n" + _wrap("setup_tui: received SIGTERM -- terminating any boundary service "
                            "this process started before exiting (no orphaned residue)."),
              file=sys.stderr)
        _terminate_boundary_proc(state_holder[0])
        sys.exit(128 + signal.SIGTERM)
    signal.signal(signal.SIGTERM, _handle_sigterm)


def _run_textual(args: argparse.Namespace) -> int:
    if tui_app is None:
        # Prose paragraphs go through `_wrap`; the install COMMAND line does not (an operator
        # copy-pastes it verbatim -- the SAME "command line never wrapped" exemption `_wrap`'s
        # own docstring names).
        print(_wrap("setup_tui: 'textual' is not installed -- the guided configuration editor "
                    "needs it, and there is no fallback UI (design/FABLE-SETUP-TUI-REBUILD-"
                    "SPEC.md §3: 'Interactive mode = Textual, full stop')."),
              file=sys.stderr)
        print("  Install it into this interpreter's venv, e.g.:", file=sys.stderr)
        print("    python3 -m venv .venv && .venv/bin/pip install textual", file=sys.stderr)
        print(_wrap("  (or, inside an already-active venv: pip install textual) Or pass "
                    "--from-config for the non-interactive, textual-free path."),
              file=sys.stderr)
        return 1
    if not sys.stdin.isatty():
        print(_wrap("setup_tui: stdin is not a terminal -- refusing to run an interactive "
                    "editor against a non-interactive stdin (it would hang or read garbage). "
                    "Pass --from-config <config> --world <name> <dest> for a non-interactive "
                    "run."), file=sys.stderr)
        return 1

    state: dict = {"_checklist": Checklist(), "_plan": Plan(),
                   "_repo_root": steps.REPO_ROOT, "dry_run": args.dry_run,
                   "accept_unverified_genesis": args.accept_unverified_genesis}
    if args.initial_config:
        try:
            initial_doc = config_file.load_config_file(args.initial_config)
            config_file.validate(initial_doc, require_complete=False)
        except config_file.ConfigError as exc:
            print(_wrap(str(exc)), file=sys.stderr)
            return 1
        state.update(config_seam.build_initial_state_overrides(initial_doc))

    state_holder: list[dict] = [state]
    app = tui_app.build_app(state, dry_run=args.dry_run)

    def _handle_sigterm(signum: int, frame: object) -> None:
        print("\n" + _wrap("setup_tui: received SIGTERM -- terminating any boundary service "
                            "this process started before exiting (no orphaned residue)."),
              file=sys.stderr)
        _terminate_boundary_proc(state_holder[0])
        app.exit(return_code=128 + signal.SIGTERM)

    signal.signal(signal.SIGTERM, _handle_sigterm)
    try:
        app.run()
    except Exception as exc:  # noqa: BLE001 -- surfaced as a plain nonzero exit, not a 2nd traceback
        print(_wrap(f"setup_tui: the Textual application exited on an unhandled error: {exc}"),
              file=sys.stderr)
        return 1
    finally:
        _terminate_boundary_proc(state_holder[0])
    return app.return_code or 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    _check_config_flags(args)
    if args.from_config:
        return _run_from_config(args)
    return _run_textual(args)


def _terminate_boundary_proc(state: dict) -> None:
    """If a section started a live boundary service (`state["boundary_proc"]`), an abnormal exit
    from this process must not leave it running silently, orphaned, and unmentioned."""
    proc = state.get("boundary_proc")
    if proc is None or proc.poll() is not None:
        return
    print(_wrap(f"setup_tui: terminating the boundary service this process started "
                f"(pid {proc.pid}) before exiting -- it will not be left running silently."),
          file=sys.stderr)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
