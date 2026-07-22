#!/usr/bin/env python3
"""seen-red/setup-tui-textual-shell/run_fixtures.py -- WX1-WX6, the Textual-shell build's own
witnesses (design/FABLE-SETUP-TUI-TEXTUAL-SPEC.md §4, commission ledger row 1818).

INTERPRETER SPLIT (the honest reason this fixture is shaped the way it is): `textual` is an
OPTIONAL dependency of this package's interactive face only (tools/setup_tui/__init__.py's own
v1-boundary posture, carried forward) -- never of the harness, a born world, or the witnessing
path. This repo's own ambient `python3` (the interpreter `fixture_census`'s acceptance
re-execution runs every fixture under) does NOT have `textual` installed, so this file itself
must import cleanly there -- it does NOT `import tools.setup_tui.ui_textual` at its own module
level. Every WX case that needs `textual` runs in a SEPARATE SUBPROCESS under a interpreter this
fixture locates (below), never in this process; the cases that do not need `textual` (WX2's
plain-backend comparand, WX3) run directly here.

Locating a textual-capable interpreter (spec's own build condition: "if textual is missing from
the build interpreter, the builder creates a scratch venv for witnessing... if that is
impossible, WX1/WX2/WX4/WX6 are reported UNEXERCISED"): `SETUP_TUI_TEXTUAL_PYTHON` (an
operator/CI-settable env var pointing at a venv's python) is tried first; failing that, the
AMBIENT interpreter itself is probed (harmless -- a subprocess `-c "import textual"` probe, never
an import into THIS process). Neither resolving is reported, per-case, UNEXERCISED with this
exact remediation line -- never simulated.

WX1 headless Textual journey / WX6 dry-run under the shell / WX4's suspend-wiring unit check all
drive a small, UNCOMMITTED driver script this fixture writes into its own scratch tempdir at run
time (mirroring seen-red/setup-tui-boundary-proc-cleanup's own precedent: never a committed
product behavior, this driver exists only as this fixture's own scratch harness) -- it imports
`tools.setup_tui.ui_textual`/`tools.setup_tui.app` for real, under Textual's own headless
`run_test`/Pilot harness, and prints one `RESULT: <json>` line the outer process here parses.

WX5 (abnormal-exit cleanup under the shell) is the one case that does NOT use the headless
harness -- it needs a REAL process to deliver a REAL SIGTERM to, and Textual's own driver needs a
real controlling terminal (`pty.openpty()`) to attach to at all outside `run_test`. It drives
`tools.setup_tui.app._run_textual` directly (the unmodified, real function), with a FAKE
single-screen list whose one screen starts a real (synthetic, scratch-only) child process into
`state["boundary_proc"]` and then blocks on `ui.ask_text(...)` -- standing in for what
`screen_boundary`'s own live path would have started, without needing a live-birthed world
(no Postgres host is available to this build's environment; the existing, unchanged
`_terminate_boundary_proc` CHOKE POINT this exercises is ALREADY both-polarity proven against a
real birth by seen-red/setup-tui-boundary-proc-cleanup -- this case's OWN job is the NEW
Textual-shell wiring around it: does SIGTERM reach the App's own graceful exit path, and does a
worker parked at a prompt wake up, rather than hanging).

Zero residue: every scratch tempdir removed, every spawned child (synthetic boundary_proc,
driver subprocess) explicitly reaped in `finally` regardless of outcome. Lazy imports banned
(this file's own only -- the driver template's `import tools.setup_tui.ui_textual` is a STRING,
never evaluated by this process)."""
from __future__ import annotations

import json
import os
import pty
import re
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

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


# ---------------------------------------------------------------------------------------------
# The scratch driver (WX1/WX4/WX6): runs under the textual-capable interpreter ONLY, dispatches
# on sys.argv[1] (the case name), prints exactly one `RESULT: {...}` JSON line.
# ---------------------------------------------------------------------------------------------

DRIVER_SOURCE = textwrap.dedent('''\
    import asyncio
    import json
    import sys

    sys.path.insert(0, %(repo)r)

    from tools.setup_tui import checklist as ck
    from tools.setup_tui.elements import Heading
    from tools.setup_tui.screens import SCREENS, screen_banner
    from tools.setup_tui.ui_textual import SetupWizardApp, TextualUi

    # The ten confirm() prompts a full "run preflight, decline everything else" pass hits, in
    # order -- derived from screens.py's own flow (each declined screen's function returns
    # before asking anything else): preflight(y), substrate(n), fork-target(n), rehearsal(n),
    # birth's rehearsal-not-green override(n), principals-authority(n), signed-genesis(n),
    # boundary's birth-not-ok override(n), observability(n), hydration(n). Checklist's own save
    # prompt is never reached (no destination was ever chosen), matching the plain backend's
    # identical flow for the SAME answers (WX2's own comparand).
    ANSWERS = ["y", "n", "n", "n", "n", "n", "n", "n", "n", "n"]


    # NOTE on this helper's shape (calibrated empirically, not guessed): an earlier version
    # added a second "wait for _pending to clear back to None before arming the next prompt"
    # step after pressing enter, plus a hard AssertionError the instant a poll iteration found
    # the wrong pending kind. Both together produced an intermittent hang -- reproduced twice,
    # at two DIFFERENT screens across separate runs, so it read as a race rather than a fixed
    # logic bug. Dropping the extra "wait to clear" step (this shape below: press enter, then
    # go straight back to polling for the NEXT prompt) reproduced ZERO hangs across a dedicated
    # stress pass (5 consecutive full-journey runs, this build's own report). Kept exactly this
    # simple, per that empirical finding -- do not reintroduce the extra clear-wait without
    # re-running that stress pass.
    async def _wait_pending(app, timeout=15.0):
        waited = 0.0
        while app._pending is None and waited < timeout:
            await asyncio.sleep(0.02)
            waited += 0.02
        return app._pending is not None


    async def _answer_confirm(pilot, app, value):
        ok = await _wait_pending(app)
        if not ok or app._pending_kind != "confirm":
            raise AssertionError(
                f"expected a confirm prompt, got pending_kind={app._pending_kind!r} "
                f"(pending={app._pending!r})")
        await pilot.click("#prompt-input")
        if value:
            await pilot.press(*value)
        await pilot.press("enter")


    async def run_journey(dry_run: bool) -> dict:
        cl = ck.Checklist()
        app = SetupWizardApp(dry_run=dry_run, checklist=cl)

        def body():
            ui = TextualUi(app)
            from tools.setup_tui.app import _intro, _drive_screens
            import argparse
            args = argparse.Namespace(dry_run=dry_run)
            _intro(ui, args)
            code = _drive_screens(ui, cl, {"dry_run": dry_run}, [{"dry_run": dry_run}], SCREENS)
            app.call_from_thread(app.exit, return_code=code)

        app.wizard_body = body
        async with app.run_test(size=(120, 45)) as pilot:
            for ans in ANSWERS:
                await _answer_confirm(pilot, app, ans)
            waited = 0.0
            while app.return_code is None and waited < 15.0:
                await pilot.pause()
                await asyncio.sleep(0.05)
                waited += 0.05
            # let the checklist banner's own refresh (note_banner) and the final exit()-time
            # refresh both land before reading the table back out.
            await pilot.pause()
            # `app.transcript_log` (NOT the RichLog widget's own `.lines`): the widget wraps a
            # long `$ argv` line across several rendered rows, so `str(rendered_row)` for the
            # first one is a truncated prefix, not the full logical line -- confirmed
            # empirically while building this witness (see the report). `transcript_log` is the
            # un-wrapped record `SetupWizardApp.on_print` keeps precisely for this reason.
            transcript_lines = list(app.transcript_log)
            table = app.query_one("#checklist-table")
            rows = []
            for row_key in list(table.rows):
                row = table.get_row(row_key)
                rows.append([str(c) for c in row])
            sidebar_number = app.query_one("#sidebar")._current_number
            return {
                "return_code": app.return_code,
                "transcript": transcript_lines,
                "checklist_rows": rows,
                "sidebar_number": sidebar_number,
            }


    async def run_wx4() -> dict:
        """Unit-level suspend-wiring check (module docstring): confirms `TextualUi.suspend()`
        really reaches `App.suspend()` (never a no-op silently skipping it) by observing the
        SAME `SuspendNotSupported` the headless driver is documented to raise -- the concrete,
        structural reason the LIVE pinentry leg cannot run under this harness regardless of any
        other blocker. `TextualUi`'s own contract is worker-thread-only (`_SuspendBridge` calls
        `App.call_from_thread`, which itself raises RuntimeError if invoked from the App's OWN
        thread) -- this check therefore runs `ui.suspend()` inside a REAL worker
        (`run_worker(..., thread=True)`), exactly how `screens.py` actually calls it, never from
        the test coroutine's own (main) thread."""
        cl = ck.Checklist()
        app = SetupWizardApp(dry_run=False, checklist=cl)
        result_box: list = []

        def _check():
            ui = TextualUi(app)
            raised = None
            try:
                with ui.suspend():
                    pass
            except Exception as exc:  # noqa: BLE001 -- reporting the exact type, not hiding it
                raised = type(exc).__name__
            result_box.append(raised)

        async with app.run_test() as pilot:
            await pilot.pause()
            app.run_worker(_check, thread=True)
            waited = 0.0
            while not result_box and waited < 10.0:
                await pilot.pause()
                await asyncio.sleep(0.02)
                waited += 0.02
            raised = result_box[0] if result_box else "TIMEOUT-no-result"
            return {
                "raised": raised,
                "is_suspend_not_supported": raised == "SuspendNotSupported",
            }


    # ---------------------------------------------------------------------------------------
    # WX7 (design/FABLE-SETUP-TUI-NAVIGATION-SPEC.md, this build): the Textual backend's own
    # backward-navigation affordances -- typed "<" AND the ctrl+b binding -- against a REAL
    # SetupWizardApp/TextualUi/tools.setup_tui.app._drive_screens, no mocks. Uses a small,
    # synthetic THREE-screen list (never the real eleven) deliberately: the real journey's own
    # Preflight screen runs LIVE subprocess/network probes whose wall-clock time this build found
    # to make the shared WX1 driver's fixed poll timing flaky in some environments (see this
    # build's report) -- orthogonal to what WX7 itself needs to prove, so sidestepped rather than
    # inherited. The middle screen ("two") is deliberately NOT the last screen in the list, so
    # `tools.setup_tui.flow_position.run_screen`'s own commit-screen exemption (never wraps the
    # LAST screen in `NavigableUi`) does not apply to it -- back-navigation must work from it.
    from tools.setup_tui.app import _drive_screens

    def nav_screen_one(ui, cl, state):
        ui.emit(Heading("1/3 One"))
        state["a"] = ui.ask_text("Name A")
        cl.add("one", "name", "WITNESSED", state["a"])
        return state

    def nav_screen_two(ui, cl, state):
        ui.emit(Heading("2/3 Two"))
        state["b"] = ui.ask_text("Name B")
        cl.add("two", "name", "WITNESSED", state["b"])
        return state

    def nav_screen_three(ui, cl, state):
        ui.emit(Heading("3/3 Three"))
        cl.add("three", "final", "WITNESSED", "reached")
        return state

    NAV_SCREENS = [("one", nav_screen_one), ("two", nav_screen_two), ("three", nav_screen_three)]


    async def _answer_text(pilot, app, text):
        """Types `text` into the docked `#prompt-input` and submits it -- the SAME path an
        operator's own keystrokes take (never `App.call_from_thread`/`_resolve` directly)."""
        ok = await _wait_pending(app)
        if not ok or app._pending_kind != "text":
            raise AssertionError(
                f"expected a text prompt, got pending_kind={app._pending_kind!r} "
                f"(pending={app._pending!r})")
        await pilot.click("#prompt-input")
        if text:
            await pilot.press(*text)
        await pilot.press("enter")


    async def _press_ctrl_b(pilot, app):
        """The `ctrl+b` binding (module docstring architecture point 6, ui_textual.py) -- waits
        for a prompt to be pending, THEN drives the REAL keypress through `Pilot.press` (Textual's
        own binding dispatch, not a direct `action_go_back()` call), exactly like `_answer_text`
        waits before typing (never fired blind, mid-transition)."""
        ok = await _wait_pending(app)
        if not ok:
            raise AssertionError("expected a pending prompt before ctrl+b, got none")
        await pilot.press("ctrl+b")


    async def run_wx7() -> dict:
        cl = ck.Checklist()
        app = SetupWizardApp(dry_run=False, checklist=cl)

        def body():
            ui = TextualUi(app)
            code = _drive_screens(ui, cl, {}, [{}], NAV_SCREENS)
            app.call_from_thread(app.exit, return_code=code)

        app.wizard_body = body
        async with app.run_test(size=(120, 45)) as pilot:
            # 1: screen one, answer "Alpha" (a normal forward answer).
            await _answer_text(pilot, app, "Alpha")
            # 2: screen two, type the LITERAL "<" trigger and submit it (module docstring
            # architecture point 6(a): the SAME `Input`-submits-text path a normal answer takes,
            # recognized by `TextualUi.ask_text` before any of its own coercion) -- pops back to
            # screen one.
            await _answer_text(pilot, app, "<")
            # 3: screen one AGAIN -- a DIFFERENT answer than the first visit (spec: revisit
            # REPLACES the popped visit, never appends alongside it).
            await _answer_text(pilot, app, "AlphaTwo")
            # 4: screen two AGAIN -- this time via the ctrl+b BINDING, never typed text (module
            # docstring architecture point 6(c)) -- pops back to screen one a second time.
            await _press_ctrl_b(pilot, app)
            # 5: screen one a THIRD time -- confirms the back-and-forth is not a one-shot fluke.
            await _answer_text(pilot, app, "AlphaThree")
            # 6: screen two, answered normally this time -- proceeds to screen three (the commit
            # screen, `NavigableUi`-exempt, asks nothing) and the flow completes.
            await _answer_text(pilot, app, "Beta")
            waited = 0.0
            while app.return_code is None and waited < 15.0:
                await pilot.pause()
                await asyncio.sleep(0.05)
                waited += 0.05
            await pilot.pause()
            transcript_lines = list(app.transcript_log)
            return {
                "return_code": app.return_code,
                "transcript": transcript_lines,
            }


    def main():
        case = sys.argv[1]
        if case == "wx1":
            result = asyncio.run(run_journey(dry_run=False))
        elif case == "wx6":
            result = asyncio.run(run_journey(dry_run=True))
        elif case == "wx4":
            result = asyncio.run(run_wx4())
        elif case == "wx7":
            result = asyncio.run(run_wx7())
        else:
            raise SystemExit(f"unknown case {case!r}")
        print("RESULT: " + json.dumps(result))


    if __name__ == "__main__":
        main()
''')


def _run_driver(textual_python: str, case: str, scratch: str) -> dict:
    driver_path = os.path.join(scratch, "driver.py")
    with open(driver_path, "w") as f:
        f.write(DRIVER_SOURCE % {"repo": REPO})
    cp = subprocess.run([textual_python, driver_path, case], capture_output=True, text=True,
                         timeout=90, cwd=REPO)
    out = cp.stdout + cp.stderr
    m = re.search(r"^RESULT: (.*)$", out, re.MULTILINE)
    if not m:
        raise AssertionError(f"case {case}: driver produced no RESULT line (rc={cp.returncode}):"
                              f"\n{out[-4000:]}")
    return json.loads(m.group(1))


# ---------------------------------------------------------------------------------------------
# WX5: a real SIGTERM delivered to a real `_run_textual` process under a pty, no mocks.
# ---------------------------------------------------------------------------------------------

WX5_DRIVER_SOURCE = textwrap.dedent('''\
    import subprocess
    import sys

    sys.path.insert(0, %(repo)r)

    from tools.setup_tui import checklist as ck
    from tools.setup_tui import app as app_mod


    def fake_screen(ui, cl, state):
        # Synthetic stand-in for screen_boundary's own live child (module docstring) -- a real
        # OS process, never mocked, so `_terminate_boundary_proc`'s `.terminate()`/`.wait()`/
        # `.poll()` calls exercise the real subprocess API.
        proc = subprocess.Popen(["sleep", "120"])
        state["boundary_proc"] = proc
        print(f"FIXTURE-BOUNDARY-PROC-READY pid={proc.pid}", flush=True)
        ui.ask_text("waiting for SIGTERM (fixture)")  # blocks until request_shutdown wakes it
        return state


    class _Args:
        dry_run = False


    def main():
        cl = ck.Checklist()
        state = {"dry_run": False}
        state_holder = [state]
        screens = [("fake", fake_screen)]
        code = app_mod._run_textual(cl, state, state_holder, screens, _Args())
        print(f"FIXTURE-EXIT-CODE={code}", flush=True)


    if __name__ == "__main__":
        main()
''')


def _run_wx5(textual_python: str, scratch: str) -> None:
    driver_path = os.path.join(scratch, "wx5_driver.py")
    with open(driver_path, "w") as f:
        f.write(WX5_DRIVER_SOURCE % {"repo": REPO})

    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        [textual_python, driver_path], cwd=REPO,
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)
    child_pid = None
    buf = b""
    try:
        deadline = time.time() + 30
        while time.time() < deadline:
            r, _, _ = select.select([master_fd], [], [], 1.0)
            if master_fd in r:
                try:
                    chunk = os.read(master_fd, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                buf += chunk
                m = re.search(rb"FIXTURE-BOUNDARY-PROC-READY pid=(\d+)", buf)
                if m:
                    child_pid = int(m.group(1))
                    break
        assert child_pid is not None, (
            f"WX5: driver never printed the boundary-proc-ready marker within 30s -- pty "
            f"output so far: {buf[-4000:]!r}")
        # confirm the synthetic child is really alive before we ask for cleanup
        os.kill(child_pid, 0)  # raises ProcessLookupError if not alive

        proc.send_signal(signal.SIGTERM)
        # KEEP DRAINING the pty while waiting for exit -- do not switch to a blind `proc.wait()`.
        # Root-caused empirically (this build's own report, a faulthandler all-threads dump
        # caught mid-hang): a bare `proc.wait()` here left the master fd unread from the moment
        # the ready-marker loop above broke out. Textual's own driver runs a background
        # `WriterThread` (textual/drivers/_writer_thread.py) that writes redraws to the pty
        # slave through a bounded `Queue(maxsize=30)`; once the kernel-level pty buffer fills
        # because NOTHING is reading the master side, that thread's `write()` syscall blocks,
        # and `App._shutdown()`'s own `driver.close()` -> `WriterThread.stop()` -> `.join()`
        # then waits forever for a thread that can never finish -- a test-harness deadlock, not
        # a product one (the dump showed the App's OWN shutdown machinery stuck, nothing in
        # this package's code). Continuing to read here is what keeps that buffer from ever
        # filling.
        deadline3 = time.time() + 45
        while time.time() < deadline3:
            if proc.poll() is not None:
                break
            r, _, _ = select.select([master_fd], [], [], 1.0)
            if master_fd in r:
                try:
                    chunk = os.read(master_fd, 65536)
                except OSError:
                    break
                if not chunk:
                    break
        else:
            raise AssertionError(
                "WX5: the Textual-shell process did not exit within 45s of SIGTERM -- a worker "
                "parked on a prompt likely hung interpreter shutdown instead of waking via "
                "request_shutdown's shutdown-event poll")
        if proc.poll() is None:
            # the loop above broke on a closed/errored pty read, not a confirmed exit -- give
            # the process a final bounded wait rather than assuming.
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                raise AssertionError(
                    "WX5: the pty closed but the Textual-shell process did not actually exit "
                    "within 5s more")

        time.sleep(0.3)  # let the terminated child actually leave the process table
        child_gone = False
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            child_gone = True
        assert child_gone, (
            f"WX5: synthetic boundary_proc (pid {child_pid}) is STILL ALIVE after the "
            f"Textual-shell process exited on SIGTERM -- _terminate_boundary_proc did not run "
            f"(or did not run in time) under the new SIGTERM handler")
    finally:
        os.close(master_fd)
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        if child_pid is not None:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


# ---------------------------------------------------------------------------------------------
# WX2 plain-backend comparand + WX3: no textual needed, run directly in this process.
# ---------------------------------------------------------------------------------------------

ANSWERS_TEXT = "y\n" + "n\n" * 9


def _run_plain_journey(scratch: str) -> str:
    ans_path = os.path.join(scratch, "answers-plain.txt")
    with open(ans_path, "w") as f:
        f.write(ANSWERS_TEXT)
    cp = subprocess.run(
        [sys.executable, "-m", "tools.setup_tui.app", "--plain", "--scripted", ans_path],
        cwd=REPO, capture_output=True, text=True, timeout=60,
    )
    return cp.stdout + cp.stderr


def _dollar_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.startswith("$ ")]


def main() -> int:
    scratch = tempfile.mkdtemp(prefix="setup-tui-textual-shell-")
    textual_python = _find_textual_python()
    try:
        # --- WX3: fallback teaching + --plain silences it (no textual needed) ---------------
        cp = subprocess.run(
            [sys.executable, "-m", "tools.setup_tui.app"],
            cwd=REPO, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL,
        )
        out = cp.stdout + cp.stderr
        has_teaching = "'textual' is not installed" in out
        has_isatty_refusal = "stdin is not a terminal" in out
        if textual_python is None:
            assert has_teaching, (
                f"WX3: expected the one teaching line naming the venv/pip command when "
                f"textual is not importable; got:\n{out[-2000:]}")
            print("WX3a ok: textual absent -> one teaching line rendered, "
                  "then the numbered-menu fallback proceeded (refusing non-interactive stdin, "
                  "same as InteractiveUi always has)")
        else:
            print(f"WX3a UNEXERCISED (this ambient interpreter HAS textual -- "
                  f"{sys.executable} -- so the natural fallback-teaching leg cannot fire here; "
                  f"the teaching-line CODE PATH is exercised directly by "
                  f"_select_backend's own logic regardless): "
                  f"has_teaching={has_teaching}")
        assert has_isatty_refusal, (
            f"WX3: the numbered-menu fallback must still refuse non-interactive stdin exactly "
            f"as InteractiveUi always has; got:\n{out[-2000:]}")

        cp2 = subprocess.run(
            [sys.executable, "-m", "tools.setup_tui.app", "--plain"],
            cwd=REPO, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL,
        )
        out2 = cp2.stdout + cp2.stderr
        assert "'textual' is not installed" not in out2, (
            f"WX3b: --plain must silence the teaching line (the operator already chose "
            f"explicitly) -- got:\n{out2[-2000:]}")
        assert "stdin is not a terminal" in out2, out2[-2000:]
        print("WX3b ok: --plain forces the fallback silently (no teaching line), still refuses "
              "non-interactive stdin the same honest way")

        # --- WX1 / WX4 / WX6: need a textual-capable interpreter -----------------------------
        if textual_python is None:
            for wx in ("WX1", "WX2", "WX4", "WX5", "WX6", "WX7"):
                print(f"{wx} UNEXERCISED: no textual-capable interpreter found. "
                      f"{INSTALL_POINTER}")
            print("ALL EXERCISABLE CASES OK (WX3 only -- textual unavailable in every "
                  "candidate interpreter)")
            return 0

        print(f"using textual-capable interpreter: {textual_python}")

        wx1 = _run_driver(textual_python, "wx1", scratch)
        transcript_wx1 = "\n".join(wx1["transcript"])
        assert wx1["return_code"] == 0, f"WX1: expected return_code 0, got {wx1}"
        assert "1/11 Preflight" in transcript_wx1, transcript_wx1[-2000:]
        assert "11/11 Checklist" in transcript_wx1, transcript_wx1[-2000:]
        assert wx1["sidebar_number"] == 11, wx1["sidebar_number"]
        assert any(row[:3] == ["birth", "world birth", "SKIPPED"] for row in wx1["checklist_rows"]), \
            wx1["checklist_rows"]
        assert any(row[:3] == ["boundary", "boundary", "REFUSED"] for row in wx1["checklist_rows"]), \
            wx1["checklist_rows"]
        assert len(wx1["checklist_rows"]) > 10, wx1["checklist_rows"]
        print(f"WX1 ok: headless Textual journey (Pilot) through all eleven screens, "
              f"checklist ({len(wx1['checklist_rows'])} rows) and sidebar (11/11) both correct, "
              f"clean exit 0")

        # --- WX2: transcript parity ------------------------------------------------------------
        plain_out = _run_plain_journey(scratch)
        plain_dollar = _dollar_lines(plain_out)
        textual_dollar = _dollar_lines(transcript_wx1)
        assert plain_dollar, f"WX2: the plain-backend comparand produced no $ lines: {plain_out[-2000:]}"
        assert textual_dollar == plain_dollar, (
            f"WX2: the Textual transcript's $ -prefixed lines differ from the plain backend's "
            f"for the SAME journey:\n  textual: {textual_dollar}\n  plain:   {plain_dollar}")
        print(f"WX2 ok: transcript parity -- {len(textual_dollar)} $ -prefixed line(s) "
              f"byte-identical between the Textual shell and the plain backend for the same "
              f"journey: {textual_dollar}")

        # --- WX4: suspend-wiring unit check + the honest live-leg blocker ----------------------
        wx4 = _run_driver(textual_python, "wx4", scratch)
        assert wx4["is_suspend_not_supported"], (
            f"WX4: expected TextualUi.suspend() to reach App.suspend() and observe "
            f"SuspendNotSupported under the headless driver; got {wx4}")
        print("WX4 ok (wiring): TextualUi.suspend() reaches the real App.suspend() -- observed "
              "the expected SuspendNotSupported under the headless driver (never a silent "
              "no-op standing in for the real bridge)")
        print("WX4 UNEXERCISED (live ceremony leg): TWO independent blockers, named honestly -- "
              "(a) no reachable Postgres host in this environment to birth the scratch world "
              "the Signed genesis screen requires (set HARNESS_PGHOST/EPISTEMIC_PGHOST); "
              "(b) even with one, the headless test driver structurally does not support "
              "App.suspend() (SuspendNotSupported, confirmed above) -- a real pinentry-under-"
              "suspend leg needs an actual controlling terminal, not this harness, regardless "
              "of infra. Never simulated.")

        # --- WX5: real SIGTERM, real child process, real cleanup -------------------------------
        _run_wx5(textual_python, scratch)
        print("WX5 ok: a real SIGTERM delivered to a real tools.setup_tui.app._run_textual "
              "process (via a pty) terminated the synthetic boundary_proc child AND the "
              "process itself exited promptly (the worker, parked on ui.ask_text, woke via "
              "request_shutdown's shutdown-event poll rather than hanging)")

        # --- WX6: dry-run under the shell -------------------------------------------------------
        wx6 = _run_driver(textual_python, "wx6", scratch)
        transcript_wx6 = "\n".join(wx6["transcript"])
        assert wx6["return_code"] == 0, wx6
        assert "--dry-run: NOTHING below is destructive" in transcript_wx6, transcript_wx6[-2000:]
        statuses = {row[2] for row in wx6["checklist_rows"]}
        assert "WITNESSED" not in statuses or all(
            row[2] != "WITNESSED" or row[0] == "preflight"  # preflight's reads stay live/real
            for row in wx6["checklist_rows"]
        ), f"WX6: a non-preflight row claimed WITNESSED under --dry-run: {wx6['checklist_rows']}"
        assert any(row[2] == "WOULD-DO" or row[2] == "SKIPPED" or row[2] == "REFUSED"
                   for row in wx6["checklist_rows"]), wx6["checklist_rows"]
        print(f"WX6 ok: --dry-run under the Textual shell -- persistent banner rendered, "
              f"no non-preflight row claimed WITNESSED, {len(wx6['checklist_rows'])} checklist "
              f"row(s) recorded honestly")

        # --- WX7: backward navigation under the Textual shell (design/FABLE-SETUP-TUI-
        # NAVIGATION-SPEC.md) -- the DEFECT this build fixes: BEFORE this build, typing "<" (or
        # any keybinding) at a Textual prompt did nothing/landed as a literal answer -- the
        # maintainer's own live report. This case backs up one screen via TYPED "<", changes the
        # answer, backs up AGAIN via the NEW ctrl+b binding, changes it again, then proceeds --
        # against the real SetupWizardApp/TextualUi/tools.setup_tui.app._drive_screens, no mocks.
        wx7 = _run_driver(textual_python, "wx7", scratch)
        transcript_wx7 = "\n".join(wx7["transcript"])
        assert wx7["return_code"] == 0, f"WX7: expected return_code 0, got {wx7}"
        assert "Traceback" not in transcript_wx7, transcript_wx7[-2000:]
        # Screen "one" must have been (re-)entered three times (Alpha, AlphaTwo, AlphaThree) and
        # screen "two" armed three times too (the two aborted attempts + the one that stuck) --
        # the FINAL answer, "AlphaThree", must be the one that survives to the end (revisit
        # REPLACES the popped visit, spec §1(a)) -- "Alpha"/"AlphaTwo" must each appear (proving
        # they really were typed/submitted and the back-navigation really fired, not a no-op that
        # skipped straight to the last answer) but the flow must never have carried BOTH "Alpha"
        # and "AlphaTwo" forward into a final state alongside "AlphaThree" (that would mean a
        # stale, un-discarded visit).
        # NOTE: a REVISIT's own prompt echoes with the prior answer offered as a default
        # ("Name A [Alpha]: AlphaTwo" -- `NavigableUi._note_prior`/`ask_text`'s own `suffix`), so
        # the second/third checks below only require the ANSWER text itself to land, not a fixed
        # "Name A: <value>" prefix shape (the first visit has no prior yet, so its own echo is
        # the plain "Name A: Alpha" shape and is checked exactly).
        assert "Name A: Alpha" in transcript_wx7, transcript_wx7[-3000:]
        for expect in ("AlphaTwo", "AlphaThree", "Name B: Beta"):
            assert expect in transcript_wx7, (
                f"WX7: expected {expect!r} in the transcript -- {transcript_wx7[-3000:]}")
        # The typed "<" and the ctrl+b binding must EACH have produced exactly one recorded
        # "<BACK>" -- "Name A: <BACK>" (typed, at screen one's SECOND arming... no: the "<" was
        # typed answering screen TWO's own "Name B" prompt, so it is "Name B: <BACK>" that
        # records the typed leg) and screen two's ctrl+b leg leaves NO transcript answer line at
        # all (a keybinding is not a submitted `Input` value) -- proven instead by screen one
        # being armed a THIRD time ("AlphaThree" reached), which is only reachable if the ctrl+b
        # press really did pop the cursor back a second time.
        assert "Name B: <BACK>" in transcript_wx7, (
            f"WX7: the TYPED '<' leg must be recognized at screen two's own prompt: "
            f"{transcript_wx7[-3000:]}")
        assert transcript_wx7.count("2/3 Two") == 3, (
            f"WX7: screen two must be (re-)entered exactly three times (aborted via typed '<', "
            f"aborted via ctrl+b, then completed) -- got "
            f"{transcript_wx7.count('2/3 Two')}: {transcript_wx7[-3000:]}")
        assert transcript_wx7.count("1/3 One") == 3, (
            f"WX7: screen one must be (re-)entered exactly three times (Alpha, AlphaTwo, "
            f"AlphaThree) -- got {transcript_wx7.count('1/3 One')}: {transcript_wx7[-3000:]}")
        print("WX7 ok: backward navigation under the Textual shell -- typed '<' at a docked "
              "Input AND the new ctrl+b binding each popped the cursor back one screen, offered "
              "the prior answer again, and the changed answer (not the discarded one) reached "
              "the end of the run, against the real SetupWizardApp/TextualUi, no mocks")

        print("ALL CASES OK -- WX1-WX7 (textual " +
              subprocess.run([textual_python, "-c",
                               "import importlib.metadata as m; print(m.version('textual'))"],
                              capture_output=True, text=True).stdout.strip() + ")")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
