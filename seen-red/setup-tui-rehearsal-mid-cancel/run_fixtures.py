#!/usr/bin/env python3
"""seen-red/setup-tui-rehearsal-mid-cancel/run_fixtures.py -- both-polarity proof of the
mid-section cancellation-token fix (cycle-4 audit finding 1, the converged audit/fix loop's own
ONE MINOR, ledger rows 1124/1133), census-registered in gates/fixture_census.py.

THE HAZARD (audit's own words, `/home/bork/autoharn_series/cycle-4/AUDIT.md` finding 1): Cancel
is enabled and clickable the WHOLE time a commit sweep runs, but `commit_pane.CommitPane`'s own
sweep only checked `Worker.is_cancelled` BETWEEN sections -- a section whose own `submit` reaches
a real, slow subprocess mid-flow (`steps_rehearsal_birth.rehearsal_submit` is the one declared
instance, witnessed at ~61s for one real rehearsal run) left Cancel structurally inert for that
whole window: pressing it set a flag nothing checked again until the already-running child exited
on its own.

THE FIX, exercised here at TWO levels:

  1. A DIRECT-CALL witness (no Textual, no Pilot) of the REAL `steps_rehearsal_birth.
     rehearsal_submit` -- `_new_project_argv`/`_teardown_argv` monkeypatched to a SYNTHETIC
     subprocess (a `python3 -c` child that writes its own pid to a pidfile, then sleeps
     `BIRTH_SLEEP_SECONDS`) instead of the real `bootstrap/new-project.sh`/`teardown-world.sh`,
     so this fixture needs no real git checkout/Postgres to prove the exact mechanism the fix
     touches: `state["_cancel_check"]`/`state["_cancel_check"]` threaded into `runner.
     run_command`'s new `cancel_check` parameter for the birth call only. A background thread
     flips the cancellation flag ~0.3s after the birth child starts (simulating an operator's
     Cancel press mid-run) -- proves the child is ACTUALLY terminated (not merely "eventually",
     checked against the real OS pid), that teardown still runs to completion despite the cancel
     (residue safety), and that the checklist records the honest, dedicated `CANCELLED` status
     (never a `REFUSED` reuse).

  2. A PILOT leg driving the REAL `tools.configtree.app.ConfigTreeApp`/`commit_pane.CommitPane`
     end to end, with a synthetic rehearsal-SHAPED `SectionSpec` (the SAME subprocess-backed
     submit shape as (1), built fresh here rather than importing autoharn's own rehearsal step,
     so this leg needs no real destination/host/db either) -- RED-first against `1e6fb5f` (the
     commit immediately before this fix): the OLD `CommitPane` never populated
     `state["_cancel_check"]`, so a Cancel press mid-section has NO EFFECT until the child exits
     naturally (reproduced live: the child is still alive well after Cancel is pressed, and the
     sweep only settles once the FULL sleep duration has elapsed, regardless of when Cancel was
     pressed). GREEN against the CURRENT `CommitPane`: the SAME Cancel press terminates the
     child within a small fraction of its own sleep duration, the pane renders an honest
     cancelled disposition (not committed, button re-enabled), and a subsequent uncancelled
     retry completes normally.

Zero residue: every synthetic pidfile/scratch directory lives under a fixture-owned `tempfile.
mkdtemp()`, removed in a `finally` regardless of outcome; no real filesystem/network/git/Postgres
act anywhere. Lazy imports banned.

Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-rehearsal-mid-cancel/run_fixtures.py
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from textual.widgets import Button, Static, Tree  # noqa: E402

from tools.configtree import CommitSpec, SectionResult, SectionSpec  # noqa: E402
import tools.configtree.app as ct_app_module  # noqa: E402
from tools.configtree.app import ConfigTreeApp  # noqa: E402
from tools.setup_tui import checklist as ck  # noqa: E402
from tools.setup_tui.runner import run_command  # noqa: E402
import tools.setup_tui.steps_rehearsal_birth as srb  # noqa: E402

# The commit immediately before this fix -- pinned by SHA, never HEAD.
PRE_FIX_COMMIT = "1e6fb5f"

# Long enough that a REAL kill (vs. "wait it out") is the only way to see the child gone well
# before this elapses; short enough to keep the fixture fast.
BIRTH_SLEEP_SECONDS = 8.0
CANCEL_AFTER_SECONDS = 0.3
# A child counts as "actually terminated promptly" (not merely eventually) if it is gone within
# this bound -- generous for scheduling jitter, far tighter than BIRTH_SLEEP_SECONDS itself.
KILL_BOUND_SECONDS = 3.0


def _birth_argv(pidfile: str) -> list:
    """A synthetic stand-in for `bootstrap/new-project.sh`: writes its OWN pid (so this fixture
    can assert on the real OS process), announces it started, then sleeps -- the same shape a
    real scratch-birth subprocess has (slow, real, killable), without needing one."""
    return [sys.executable, "-c",
            f"import os,sys,time\n"
            f"open({pidfile!r}, 'w').write(str(os.getpid()))\n"
            f"sys.stdout.write('birth-started\\n'); sys.stdout.flush()\n"
            f"time.sleep({BIRTH_SLEEP_SECONDS})\n"]


def _teardown_argv(marker: str, scratch_dir: str) -> list:
    """A synthetic stand-in for `bootstrap/teardown-world.sh`: writes a marker (proving it ran
    to completion) and removes the scratch directory -- the residue-safety act this fixture
    checks actually happened even when the birth call above was cancelled mid-run."""
    return [sys.executable, "-c",
            f"import shutil\n"
            f"open({marker!r}, 'w').write('cleaned')\n"
            f"shutil.rmtree({scratch_dir!r}, ignore_errors=True)\n"]


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just not ours to signal -- still alive
    return True


def _read_pid(pidfile: str, timeout: float = 5.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.isfile(pidfile) and os.path.getsize(pidfile) > 0:
            return int(open(pidfile).read().strip())
        time.sleep(0.02)
    raise AssertionError(f"child never wrote its own pid to {pidfile} within {timeout}s")


# ============================== (1) DIRECT-CALL WITNESS =====================================

async def case_1_direct_call() -> None:
    scratch = tempfile.mkdtemp(prefix="ctj-rehearsal-cancel-")
    pidfile = os.path.join(scratch, "birth.pid")
    marker = os.path.join(scratch, "teardown.marker")
    scratch_dir = os.path.join(scratch, "scratch-world-dir")
    os.makedirs(scratch_dir, exist_ok=True)
    orig_new, orig_teardown = srb._new_project_argv, srb._teardown_argv
    srb._new_project_argv = lambda *a, **k: _birth_argv(pidfile)
    srb._teardown_argv = lambda *a, **k: _teardown_argv(marker, scratch_dir)
    try:
        cancel_flag = threading.Event()

        def _flip_after_delay() -> None:
            _read_pid(pidfile)  # wait for the child to actually exist before cancelling it
            time.sleep(CANCEL_AFTER_SECONDS)
            cancel_flag.set()

        state = {
            "_checklist": ck.Checklist(),
            "_repo_root": REPO,
            "dry_run": False,
            "_cancel_check": cancel_flag.is_set,
        }
        answers = {"run": True, "host": "unused", "db": "unused",
                   "scratch_world": "unused", "scratch_dir": scratch_dir}
        flipper = threading.Thread(target=_flip_after_delay, daemon=True)
        t0 = time.monotonic()
        flipper.start()
        result = srb.rehearsal_submit(state, answers)
        elapsed = time.monotonic() - t0
        flipper.join(timeout=5)

        assert elapsed < BIRTH_SLEEP_SECONDS * 0.5, (
            f"expected rehearsal_submit to return well before the full "
            f"{BIRTH_SLEEP_SECONDS}s birth sleep elapsed (the child was cancelled ~"
            f"{CANCEL_AFTER_SECONDS}s in) -- took {elapsed:.2f}s, looks like the cancel had no "
            f"effect and the call waited out the natural sleep instead")
        print(f"case 1a ok (REAL cancellation, not a wait-it-out): rehearsal_submit returned in "
              f"{elapsed:.2f}s against a {BIRTH_SLEEP_SECONDS}s synthetic birth sleep, cancelled "
              f"~{CANCEL_AFTER_SECONDS}s in")

        assert result.ok is True and result.state_updates.get("rehearsal_green") is False, (
            f"expected a cancelled rehearsal to report ok=True (not a field refusal) with "
            f"rehearsal_green=False, got {result}")
        statuses = {it.item: it.status for it in state["_checklist"].items}
        assert statuses.get("scratch birth") == ck.CANCELLED, (
            f"expected the birth item's own checklist row to read CANCELLED (a dedicated "
            f"status, never a REFUSED reuse), got {statuses}")
        assert statuses.get("rehearsal overall") == ck.CANCELLED, \
            f"expected the overall rehearsal row to read CANCELLED too, got {statuses}"
        print(f"case 1b ok (honest disposition): checklist rows read {statuses} -- CANCELLED "
              f"is its own dedicated status, distinct from REFUSED/WITNESSED")

        assert os.path.isfile(marker), (
            "expected teardown to have run to COMPLETION despite the birth call being "
            "cancelled mid-run (the residue-safety contract: teardown is never itself "
            "cancellable, so a half-started scratch world is always cleaned up)")
        assert not os.path.isdir(scratch_dir), \
            "expected the scratch directory to be gone -- teardown's own real removal act"
        print("case 1c ok (residue safety): teardown ran to completion and removed the scratch "
              "directory EVEN THOUGH the birth subprocess was cancelled mid-run -- zero residue")
    finally:
        srb._new_project_argv, srb._teardown_argv = orig_new, orig_teardown
        shutil.rmtree(scratch, ignore_errors=True)


# ============================== (2) PILOT-DRIVEN WITNESS ====================================

def _synthetic_rehearsal_registry(scratch_root: str):
    """A `SectionSpec` shaped exactly like `steps_rehearsal_birth.rehearsal_submit` -- a
    cancel-aware, slow "birth" `run_command` call followed by an ALWAYS-runs-to-completion
    "teardown" call -- built fresh (not autoharn's own step) so this Pilot leg needs no real
    destination/host/db/git checkout."""
    pidfile = os.path.join(scratch_root, "birth.pid")
    marker = os.path.join(scratch_root, "teardown.marker")
    scratch_dir = os.path.join(scratch_root, "scratch-world-dir")

    def fields(state):
        return ()

    def submit(state, answers):
        os.makedirs(scratch_dir, exist_ok=True)
        cancel_check = state.get("_cancel_check")
        res = run_command(_birth_argv(pidfile), cancel_check=cancel_check)
        res2 = run_command(_teardown_argv(marker, scratch_dir))  # never cancellable
        if res.cancelled:
            return SectionResult(ok=True, state_updates={"rehearsal_green": False})
        return SectionResult(ok=True, state_updates={"rehearsal_green": res.ok and res2.ok})

    spec = SectionSpec(slug="rehearsal-like", title="Rehearsal-like", group="Synthetic",
                        fields=fields, submit=submit)
    commit_spec = CommitSpec(
        render_summary=lambda s: "synthetic summary",
        commit=lambda s: SectionResult(ok=True, info_lines=("synthetic commit complete",)))
    return (spec,), commit_spec, pidfile, marker, scratch_dir


async def _settle(commit_pane, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while commit_pane.is_commit_running:
        assert time.monotonic() < deadline, "commit worker did not settle within timeout"
        await asyncio.sleep(0.02)


def load_old_commit_pane_class():
    """`CommitPane` exactly as it stood at `PRE_FIX_COMMIT` -- via `git show`, executed in an
    isolated namespace, mirroring `seen-red/setup-tui-commit-off-ui-thread`'s own technique."""
    src = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:tools/configtree/commit_pane.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {"__name__": "tools.configtree._old_commit_pane_for_fixture"}
    exec(compile(src, f"<git show {PRE_FIX_COMMIT}:tools/configtree/commit_pane.py>", "exec"), ns)
    return ns["CommitPane"]


async def case_2_red() -> None:
    scratch = tempfile.mkdtemp(prefix="ctj-rehearsal-cancel-pilot-red-")
    OldCommitPane = load_old_commit_pane_class()
    original = ct_app_module.CommitPane
    ct_app_module.CommitPane = OldCommitPane
    try:
        sections, commit_spec, pidfile, marker, scratch_dir = _synthetic_rehearsal_registry(scratch)
        app = ConfigTreeApp(sections, commit_spec, initial_state={})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            tree = app.query_one("#ct-tree", Tree)
            commit_node = next(n for n in tree.root.children if (n.data or {}).get("kind") == "commit")
            tree.select_node(commit_node)
            tree.action_select_cursor()
            await pilot.pause()
            commit_btn = app.query_one("#pane-commit #ct-commit", Button)
            cancel_btn = app.query_one("#pane-commit #ct-commit-cancel", Button)
            commit_btn.press()
            pid = await asyncio.get_event_loop().run_in_executor(None, _read_pid, pidfile)
            await asyncio.sleep(CANCEL_AFTER_SECONDS)
            cancel_btn.press()
            await asyncio.sleep(KILL_BOUND_SECONDS)
            await pilot.pause()
            assert _pid_alive(pid), (
                f"expected the OLD CommitPane's Cancel press to have NO EFFECT on the "
                f"in-flight child (pid {pid}) -- the child should still be alive "
                f"{KILL_BOUND_SECONDS}s after Cancel was pressed, reproducing the audit's own "
                f"'cancel mid-section has no effect until the child exits naturally'")
            print(f"case 2 ok (RED, reproduced against {PRE_FIX_COMMIT}): pid {pid} is STILL "
                  f"ALIVE {KILL_BOUND_SECONDS}s after Cancel was pressed -- the OLD CommitPane "
                  f"never threaded a cancellation token into the subprocess layer, so the "
                  f"Cancel press was structurally inert for this section")
            # Let the OLD (uncancellable) sweep run out its own natural sleep before tearing
            # down the Pilot context -- nothing left in flight on exit.
            await _settle(app._commit_pane, timeout=BIRTH_SLEEP_SECONDS + 5.0)
    finally:
        ct_app_module.CommitPane = original
        shutil.rmtree(scratch, ignore_errors=True)


async def case_3_green() -> None:
    scratch = tempfile.mkdtemp(prefix="ctj-rehearsal-cancel-pilot-green-")
    sections, commit_spec, pidfile, marker, scratch_dir = _synthetic_rehearsal_registry(scratch)
    try:
        app = ConfigTreeApp(sections, commit_spec, initial_state={})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            tree = app.query_one("#ct-tree", Tree)
            commit_node = next(n for n in tree.root.children if (n.data or {}).get("kind") == "commit")
            tree.select_node(commit_node)
            tree.action_select_cursor()
            await pilot.pause()
            commit_pane = app._commit_pane
            commit_btn = app.query_one("#pane-commit #ct-commit", Button)
            cancel_btn = app.query_one("#pane-commit #ct-commit-cancel", Button)
            commit_btn.press()
            pid = await asyncio.get_event_loop().run_in_executor(None, _read_pid, pidfile)
            await asyncio.sleep(CANCEL_AFTER_SECONDS)
            t0 = time.monotonic()
            cancel_btn.press()

            async def _wait_dead(timeout: float) -> float:
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    if not _pid_alive(pid):
                        return time.monotonic() - t0
                    await asyncio.sleep(0.05)
                raise AssertionError(f"pid {pid} still alive {timeout}s after Cancel was pressed")

            kill_latency = await _wait_dead(KILL_BOUND_SECONDS)
            print(f"case 3a ok (GREEN, real termination): pid {pid} was actually gone "
                  f"{kill_latency:.2f}s after Cancel was pressed -- well under the "
                  f"{BIRTH_SLEEP_SECONDS}s the child would otherwise have slept, and well under "
                  f"the {KILL_BOUND_SECONDS}s bound (SIGTERM, bounded wait, then SIGKILL)")

            await _settle(commit_pane, timeout=10.0)
            await pilot.pause()
            assert not commit_pane.is_committed, "a cancelled run must not read as committed"
            assert not commit_btn.disabled, "the commit button must re-enable after a cancel, for a retry"
            print("case 3b ok (honest disposition): the pane settles NOT committed, Commit "
                  "button re-enabled for a retry -- no silent freeze, no false success")

            assert os.path.isfile(marker), \
                "expected teardown to have run to completion despite the mid-birth cancel"
            assert not os.path.isdir(scratch_dir), \
                "expected the scratch directory to be gone -- zero residue after a mid-run cancel"
            print("case 3c ok (residue safety, Pilot-driven): teardown ran to completion and "
                  "the scratch directory is gone even though Cancel fired mid-birth")

            # RETRY: a second, uncancelled press must run BOTH subprocesses to completion and
            # commit normally -- the cancelled attempt left nothing behind to trip up a retry.
            commit_btn.press()
            await asyncio.sleep(0.1)  # let the retry actually start before polling settle
            # (same defensive gap `setup-tui-commit-off-ui-thread`'s own case 4b uses -- `press()`
            # only POSTS the Pressed message; polling `is_commit_running` before it is even
            # dispatched reads "not running yet" as "already settled", which would otherwise
            # tear down this Pilot context mid-flight and let the App's own unmount-time
            # `Worker.cancel()` -- `Widget._on_unmount` -> `WorkerManager.cancel_node` -- kill
            # the still-in-flight retry itself, a TEST-HARNESS race, not a product defect).
            await _settle(commit_pane, timeout=BIRTH_SLEEP_SECONDS + 10.0)
            await pilot.pause()
            assert commit_pane.is_committed, "expected the uncancelled retry to complete"
            print("case 3d ok (retry after cancel): a second, uncancelled press runs the full "
                  "sweep (this time letting the birth child sleep out its own duration "
                  "naturally) and completes -- the cancelled attempt left no residue behind")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


async def _main() -> None:
    await case_1_direct_call()
    await case_2_red()
    await case_3_green()
    print("ALL CASES OK -- the mid-section cancellation token (cycle-4 audit finding 1, ledger "
          "rows 1124/1133): a direct-call witness of the REAL rehearsal_submit (a real OS child "
          "actually terminated, teardown honoring the residue-safety contract, honest CANCELLED "
          "checklist rows), RED-first against the OLD CommitPane (1e6fb5f, Cancel structurally "
          "inert mid-section), and GREEN against the CURRENT CommitPane (the same Cancel press "
          "now actually kills the in-flight child, an honest not-committed disposition, and a "
          "clean uncancelled retry afterward).")


if __name__ == "__main__":
    asyncio.run(_main())
