#!/usr/bin/env python3
"""seen-red/setup-tui-ctrlc-quit-shadow/run_fixtures.py -- red-then-green proof of the ctrl+c
quit-key fix in tools/setup_tui/ui_textual.py (maintainer field observation d, verbatim:
"quit doesn't work (spurious?)").

MECHANISM (verified by a fresh-context investigator before this build, re-verified here against
the installed textual package's own source, not merely trusted secondhand): Textual's `Screen`
base class (textual/screen.py) carries its own DEFAULT_BINDINGS entry
`Binding("ctrl+c,super+c", "screen.copy_text", ..., show=False)` -- NOT `priority=True`. `App`'s
own built-in `ctrl+c` -> `help_quit` binding is likewise not `priority=True`. Textual's per-key
binding merge (`Screen.active_bindings`, the "Replace priority bindings" branch) keeps whichever
same-key binding is CLOSER to focus unless the more distant one is `priority=True` -- so the
Screen's `copy_text` silently wins over the App's built-in `help_quit` for bare ctrl+c, and
`App._check_bindings(key, priority=True)` (called first, `textual/app.py` around the main key
dispatch) never even sees a priority-True ctrl+c binding to catch this early, because before this
fix `SetupWizardApp.BINDINGS` only declared `ctrl+q` as priority. Net effect, witnessed directly
below: **ctrl+c did nothing at all** -- not copy (nothing is ever selected under this app's normal
prompt-driven flow), not quit, not even the built-in "press again to confirm" hint (which could
never have fired anyway, since this app renamed the quit action from "quit" to "request_quit",
and `action_help_quit`'s hint only recognizes the literal name). ADR-0002 (fail loudly) names this
exact shape a rung-5 failure: the universal interrupt keystroke silently swallowed.

THE FIX (tools/setup_tui/ui_textual.py, SetupWizardApp.BINDINGS): binds ctrl+c to the SAME
`request_quit` action as ctrl+q, ALSO `priority=True` -- which the source above confirms is
checked by `App._check_bindings(..., priority=True)` before the Screen's own (non-priority)
`copy_text` binding is ever reached, defeating the shadow explicitly rather than relying on
binding-merge accident. Design choice (stated in the source comment, restated here for the
record): ctrl+c reaches the SAME `request_shutdown` path ctrl+q already does -- not a
confirm-again hint -- because ctrl+q already performs this exact unconditional quit at any point
in the wizard including mid-commit, and making ctrl+c behave differently would invent a NEW
asymmetry between two keystrokes an operator reasonably expects to be synonyms. `request_shutdown`
is not an abrupt kill of in-flight work either way: it wakes a worker thread parked at a prompt,
but a worker mid-subprocess-call finishes that call before the next blocking point observes the
shutdown signal (module docstring, architecture point 4) -- unchanged by this fix.

METHOD: two textual-capable-interpreter subprocess legs, both against a scratch driver script
this fixture writes at run time (never committed, mirroring seen-red/setup-tui-textual-shell's own
precedent) that drives a REAL `SetupWizardApp` under Textual's own headless `run_test`/Pilot
harness -- no mocks of Binding/Screen/App resolution, the real classes decide which action fires.

  * RED leg: the driver loads `git show <PRE_FIX_COMMIT>:tools/setup_tui/ui_textual.py` (this
    fixture's own PRE_FIX_COMMIT, the exact HEAD commit immediately before this fix landed -- an
    EXPLICIT, pinned reference, never "HEAD", for the same staleness reason
    setup-tui-boundary-proc-cleanup's own driver pins one) into a scratch file, loaded via
    `importlib.util.spec_from_file_location` under an independent module name (its absolute
    `from tools.setup_tui import ...` imports resolve normally via sys.path -- it does not need to
    BE `tools.setup_tui.ui_textual` to work). Presses ctrl+q (expect: quits, unaffected -- proving
    the harness itself is sound) THEN, in a fresh App instance, presses ctrl+c (expect,
    reproducing the live defect: no shutdown, app still running -- the silent no-op).
  * GREEN leg: the driver imports the CURRENT, on-disk `tools.setup_tui.ui_textual` (this
    fixture's own fix) the normal way. Presses ctrl+q (still quits) and, in a fresh App instance,
    ctrl+c (now quits too -- shutdown_event set, app no longer running).

Needs a textual-capable interpreter (`SETUP_TUI_TEXTUAL_PYTHON` env var, or the ambient
`sys.executable` if it happens to have `textual` installed) exactly as
seen-red/setup-tui-textual-shell already requires -- absent one, every case is reported
UNEXERCISED with the concrete remediation, never simulated.

Zero residue: scratch tempdir removed in `finally`. Lazy imports banned (this file's own only --
the driver template's `import` lines are a STRING, never evaluated by this process)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

# The exact commit this fix's own diff applied on top of -- pinned explicitly (never "HEAD",
# which drifts the moment a LATER, unrelated commit touches this same file again; see this
# fixture's own module docstring and setup-tui-boundary-proc-cleanup's identical precedent).
PRE_FIX_COMMIT = "1de2553"

INSTALL_POINTER = (
    "set SETUP_TUI_TEXTUAL_PYTHON=/path/to/a/venv/bin/python with 'textual' installed "
    "(python3 -m venv .venv && .venv/bin/pip install textual), or install textual into the "
    "ambient interpreter this fixture runs under."
)


def _find_textual_python() -> str | None:
    override = os.environ.get("SETUP_TUI_TEXTUAL_PYTHON")
    if override and os.path.isfile(override):
        probe = subprocess.run([override, "-c", "import textual"], capture_output=True)
        if probe.returncode == 0:
            return override
    probe = subprocess.run([sys.executable, "-c", "import textual"], capture_output=True)
    if probe.returncode == 0:
        return sys.executable
    return None


DRIVER_SOURCE = textwrap.dedent('''\
    import asyncio
    import importlib.util
    import json
    import sys

    sys.path.insert(0, %(repo)r)

    from tools.setup_tui import checklist as ck

    MODE = sys.argv[1]  # "red" or "green"
    MODULE_PATH = sys.argv[2] if len(sys.argv) > 2 else None


    def _load_module():
        if MODE == "red":
            spec = importlib.util.spec_from_file_location("ui_textual_prefix", MODULE_PATH)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        else:
            import tools.setup_tui.ui_textual as mod
            return mod


    async def press_and_observe(mod, key: str) -> dict:
        """Fresh App instance per key so an earlier press's shutdown never contaminates the
        next -- each press is its own clean-room observation of exactly one binding's effect."""
        cl = ck.Checklist()
        app = mod.SetupWizardApp(dry_run=False, checklist=cl)
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press(key)
            await pilot.pause()
            await asyncio.sleep(0.1)
            await pilot.pause()
            result = {
                "key": key,
                "shutdown_event_set": app._shutdown_event.is_set(),
                "is_running_after_press": app.is_running,
            }
            if not result["shutdown_event_set"]:
                # this press was a no-op (or at least did not reach request_shutdown) -- close
                # the harness ourselves so run_test's own context manager does not hang waiting
                # for an exit that key press was never going to trigger.
                app.exit()
        return result


    async def run() -> dict:
        mod = _load_module()
        ctrl_q = await press_and_observe(mod, "ctrl+q")
        ctrl_c = await press_and_observe(mod, "ctrl+c")
        return {"mode": MODE, "ctrl_q": ctrl_q, "ctrl_c": ctrl_c}


    if __name__ == "__main__":
        print("RESULT: " + json.dumps(asyncio.run(run())))
''')


def _run_driver(textual_python: str, mode: str, scratch: str, module_path: str | None) -> dict:
    driver_path = os.path.join(scratch, "driver.py")
    with open(driver_path, "w") as f:
        f.write(DRIVER_SOURCE % {"repo": REPO})
    argv = [textual_python, driver_path, mode]
    if module_path:
        argv.append(module_path)
    cp = subprocess.run(argv, capture_output=True, text=True, timeout=60, cwd=REPO)
    out = cp.stdout + cp.stderr
    m = re.search(r"^RESULT: (.*)$", out, re.MULTILINE)
    if not m:
        raise AssertionError(f"mode {mode}: driver produced no RESULT line (rc={cp.returncode}):"
                              f"\n{out[-4000:]}")
    return json.loads(m.group(1))


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-ctrlc-quit-shadow-")
    try:
        textual_python = _find_textual_python()
        if textual_python is None:
            print(f"RED UNEXERCISED: no textual-capable interpreter found. {INSTALL_POINTER}")
            print(f"GREEN UNEXERCISED: no textual-capable interpreter found. {INSTALL_POINTER}")
            print("ALL EXERCISABLE CASES OK (none -- textual unavailable in every candidate "
                  "interpreter; the live legs are the maintainer's own real-terminal check)")
            return 0

        print(f"using textual-capable interpreter: {textual_python}")

        # ------------------------------------------------------------------------------- RED --
        r = subprocess.run(["git", "-C", REPO, "show", f"{PRE_FIX_COMMIT}:tools/setup_tui/ui_textual.py"],
                            capture_output=True, text=True)
        assert r.returncode == 0 and r.stdout.strip(), (
            f"could not read {PRE_FIX_COMMIT}:tools/setup_tui/ui_textual.py -- {r.stderr}")
        assert 'Binding("ctrl+c"' not in r.stdout, (
            f"fixture assumption stale: {PRE_FIX_COMMIT}:tools/setup_tui/ui_textual.py ALREADY "
            f"carries a ctrl+c binding -- PRE_FIX_COMMIT needs repinning to a genuinely earlier "
            f"commit (one before whichever commit introduced this fix)")
        prefix_path = os.path.join(scratch, "ui_textual_prefix.py")
        with open(prefix_path, "w") as f:
            f.write(r.stdout)

        red = _run_driver(textual_python, "red", scratch, prefix_path)
        assert red["ctrl_q"]["shutdown_event_set"] and not red["ctrl_q"]["is_running_after_press"], (
            f"RED leg: ctrl+q itself must still work pre-fix (proves the harness is sound, "
            f"isolates the defect to ctrl+c specifically) -- got {red['ctrl_q']}")
        assert not red["ctrl_c"]["shutdown_event_set"] and red["ctrl_c"]["is_running_after_press"], (
            f"RED leg: expected ctrl+c to be a SILENT NO-OP pre-fix (the live defect this "
            f"fixture reproduces) -- got {red['ctrl_c']} -- either the defect no longer "
            f"reproduces against {PRE_FIX_COMMIT}, or the harness itself is unsound")
        print(f"RED ok (pre-fix, {PRE_FIX_COMMIT}:tools/setup_tui/ui_textual.py): ctrl+q quits "
              f"(shutdown_event set, app stopped) but ctrl+c does NOTHING (shutdown_event stays "
              f"unset, app keeps running) -- the exact silent-swallow defect reproduced live, "
              f"against the real Screen/App binding-merge machinery, no mocks")

        # ----------------------------------------------------------------------------- GREEN --
        current_text = open(os.path.join(REPO, "tools", "setup_tui", "ui_textual.py")).read()
        assert 'Binding("ctrl+c", "request_quit"' in current_text, (
            "fixture assumption stale: the current tools/setup_tui/ui_textual.py no longer "
            "carries the ctrl+c priority binding this fixture's GREEN leg expects -- update "
            "this fixture")

        green = _run_driver(textual_python, "green", scratch, None)
        assert green["ctrl_q"]["shutdown_event_set"] and not green["ctrl_q"]["is_running_after_press"], (
            f"GREEN leg: ctrl+q must still work post-fix (no regression) -- got {green['ctrl_q']}")
        assert green["ctrl_c"]["shutdown_event_set"] and not green["ctrl_c"]["is_running_after_press"], (
            f"GREEN leg: expected ctrl+c to now quit via the SAME request_shutdown path as "
            f"ctrl+q -- got {green['ctrl_c']}")
        print("GREEN ok (post-fix, current tools/setup_tui/ui_textual.py): both ctrl+q AND "
              "ctrl+c quit -- shutdown_event set, app no longer running, for both keys -- the "
              "designed behavior (never a silent no-op) confirmed live")

        print("ALL CASES OK -- ctrl+c quit-key shadow fixed, red before green, live Textual "
              "binding-merge machinery, zero residue")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
