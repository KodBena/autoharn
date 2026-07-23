#!/usr/bin/env python3
"""seen-red/setup-tui-commit-off-ui-thread/run_fixtures.py -- both-polarity proof that
`tools/configtree/commit_pane.py`'s `CommitPane` (split out of `panes.py`, ADR-0007, once this
very fix pushed it over 400 lines) no longer blocks the UI thread while its submit
sweep + commit act run (audit finding, ledger row 1130's own sibling audit; ADR-0019 C24/C26/C9),
census-registered in gates/fixture_census.py.

THE HAZARD: before this fix, `CommitPane.on_button_pressed` called the full submit sweep (every
section's own `submit` -- real subprocesses, a real 5s-timeout network probe) and, if it
cleared, the real commit act, ALL synchronously inside the Button's own `Pressed` handler. That
handler is a coroutine running on Textual's own single asyncio event loop -- a call inside it
that BLOCKS (e.g. `time.sleep`, a real subprocess `.wait()`, `socket.connect` without a
sub-second timeout) stalls that ONE loop entirely: no other coroutine, including Textual's own
input-dispatch/redraw machinery, gets a turn until the blocking call returns. Nothing short of a
worker thread (or a fully-async rewrite of every probe this sweep touches, a far larger change)
fixes this.

RED (case 1): loads the OLD, synchronous `CommitPane` straight from git history (`PRE_FIX_COMMIT`,
the last commit before this fix -- via `git show`, executed in an isolated namespace, never
`sys.modules`-registered) and drives it, via `tools.configtree.app`'s CURRENT `ConfigTreeApp`
(everything else about the app is unchanged; only `CommitPane` is swapped, restored immediately
after), against a SYNTHETIC section whose own `submit` sleeps for `SLOW_SUBMIT_SECONDS` --
exactly the shape a real network-probe/subprocess submit has, without this fixture actually
needing a live Postgres/git checkout to demonstrate the class of hazard. Proves the freeze is
real: a concurrently-scheduled `pilot.press("down")` on the ALWAYS-visible sidebar Tree does not
even begin dispatching until the blocking sleep ends -- its own wall-clock latency is
indistinguishable from `SLOW_SUBMIT_SECONDS` itself, i.e. the keypress is processed only AFTER
the freeze, never during it.

GREEN (cases 2-4): the REAL, current, `@work(thread=True)`-based `CommitPane`, same synthetic
slow section:
  2. the SAME concurrent keypress resolves in a small fraction of `SLOW_SUBMIT_SECONDS` -- the
     event loop was never blocked, so Tree cursor navigation is processed WHILE the sweep is
     still running in its background thread, not after it.
  3. the busy chrome (C26) is visible WHILE the sweep runs: the commit button is disabled and
     `#ct-commit-busy` shows non-empty, non-hidden text; both clear and the button re-enables
     once the (synthetic, always-successful) commit act completes, `is_committed` reading True.
  4. CANCELLATION (C9), both halves named honestly: (a) a Cancel press DURING the first of two
     slow sections stops the sweep cleanly BETWEEN sections -- the second slow section's own
     `submit` never runs, no `_commit_errors`/`_commit_ok` gets recorded, the button re-enables
     for a fresh attempt; (b) once the sweep clears and the (synthetic, instant) commit act
     itself is running, Cancel no longer has anything left to stop (the real commit act is
     documented, in `CommitPane`'s own class docstring, as NOT cancellable once started -- this
     case exercises the one moment cancellation IS honored, not a claim that every moment is).
  5. ctrl+q's exit-code contract still holds WHILE a sweep is in flight -- `App.return_code`
     reads 130 promptly, not only after the background sweep finishes (the priority key binding
     is dispatched on the same never-blocked event loop the worker thread leaves free).

Zero residue: everything is synthetic (`SectionSpec`/`CommitSpec` built in this file), no real
filesystem/network/subprocess act anywhere. Lazy imports banned.

Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-commit-off-ui-thread/run_fixtures.py
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from textual.widgets import Button, Static, Tree  # noqa: E402

from tools.configtree import CommitSpec, SectionResult, SectionSpec  # noqa: E402
import tools.configtree.app as ct_app_module  # noqa: E402
from tools.configtree.app import ConfigTreeApp  # noqa: E402

# The last commit before this fix (parent of the commit that introduces the worker) -- pinned by
# SHA, never HEAD, so this fixture stays reproducible regardless of what lands on top of it.
PRE_FIX_COMMIT = "3cc769d"

# How long the synthetic section's own `submit` sleeps -- long enough to dominate any ordinary
# scheduling jitter (a few ms) by at least an order of magnitude, short enough to keep this
# fixture fast. A concurrent keypress's own latency is compared against this constant, not a
# hardcoded threshold, so the fixture's own timing assumption is named in exactly one place.
SLOW_SUBMIT_SECONDS = 0.5
# A keypress counts as "processed during the sweep" (not merely eventually, after it) if its own
# latency stays under this fraction of the slow submit -- generous enough to absorb CI/dev-box
# scheduling noise, tight enough that the OLD (blocking) code's near-total-latency failure mode
# cannot accidentally pass it.
RESPONSIVE_FRACTION = 0.5


def load_old_commit_pane_class():
    """Fetches `CommitPane` exactly as it stood in `PRE_FIX_COMMIT` -- the synchronous,
    UI-thread-blocking version -- via `git show`, executed in an ISOLATED namespace (never
    imported as a module), so this fixture can hold both the old and the new class alive at
    once without one shadowing the other in `sys.modules`."""
    src = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:tools/configtree/panes.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {"__name__": "tools.configtree._old_panes_for_fixture"}
    exec(compile(src, f"<git show {PRE_FIX_COMMIT}:tools/configtree/panes.py>", "exec"), ns)
    return ns["CommitPane"]


def _synthetic_registry(*, n_slow: int = 1):
    """One `TextField`-free `SectionSpec` per slow section (`slow-0`, `slow-1`, ...), each own
    `submit` sleeping `SLOW_SUBMIT_SECONDS` and recording its OWN name into `state` so a
    cancelled-between-sections run is provably distinguishable from a completed one (case 4a
    checks `slow-1` never ran). `render_summary`/`commit` are trivial and instantaneous -- this
    fixture's OWN subject is the sweep's threading, not the commit act's own duration."""
    def _make_submit(name: str):
        def submit(state: dict, answers: dict) -> SectionResult:
            time.sleep(SLOW_SUBMIT_SECONDS)
            state.setdefault("_ran", []).append(name)
            return SectionResult(ok=True)
        return submit

    sections = tuple(
        SectionSpec(slug=f"slow-{i}", title=f"Slow {i}", group="Synthetic",
                    fields=lambda s: (), submit=_make_submit(f"slow-{i}"))
        for i in range(n_slow)
    )
    commit_spec = CommitSpec(
        render_summary=lambda s: "synthetic summary -- nothing real committed",
        commit=lambda s: SectionResult(ok=True, info_lines=("synthetic commit complete",)),
    )
    return sections, commit_spec


async def _settle(commit_pane, timeout: float = 10.0) -> None:
    """Polls `CommitPane.is_commit_running` to False -- the worker runs in a real thread, so a
    single `pilot.pause()` is not a reliable settle signal (see `panes.py`'s own class
    docstring)."""
    deadline = time.monotonic() + timeout
    while commit_pane.is_commit_running:
        assert time.monotonic() < deadline, "commit worker did not settle within timeout"
        await asyncio.sleep(0.02)


async def _press_and_time_tree_response(pilot, tree: Tree, commit_btn: Button) -> float:
    """Presses `commit_btn` (starting the sweep) and, WHILE it is (or claims to be) still
    running, sends a single arrow-key press to the ALWAYS-visible sidebar `Tree` (never hidden
    behind whichever section pane happens to be showing) -- returns the wall-clock seconds that
    keypress itself took to be dispatched and processed. A frozen event loop cannot even START
    running the concurrently-scheduled key dispatch until the blocking call inside the button
    handler returns, so this latency is the fixture's ONE load-bearing measurement.

    Uses `Button.press()` (a PLAIN synchronous method -- posts the `Pressed` message and returns
    immediately, no mouse-down/up simulation, no focus change) rather than `pilot.click`
    deliberately: `pilot.click` moves focus onto the clicked button as part of its own mouse
    simulation, which would either steal focus from the Tree (breaking the subsequent key press)
    or require an AWAITED re-focus in between -- and awaiting anything between the press and the
    timed key send would itself block on the very freeze this fixture is trying to measure from
    its start, corrupting the measurement for the RED case."""
    tree.focus()
    await pilot.pause()  # let the (deferred, `call_later`-based) focus() actually land, BEFORE
    # any slow work starts -- this pause is free here, unlike one placed after the button press.
    before_line = tree.cursor_line
    commit_btn.press()
    t0 = time.monotonic()
    # "commit" is the tree's own LAST leaf (`ConfigTreeApp.on_mount` adds it last), so "up" is
    # the arrow guaranteed to have somewhere to go from it.
    await pilot.press("up")
    latency = time.monotonic() - t0
    assert tree.cursor_line != before_line, "the up-arrow press must have actually moved the tree cursor"
    return latency


async def case_1_red() -> None:
    OldCommitPane = load_old_commit_pane_class()
    original = ct_app_module.CommitPane
    ct_app_module.CommitPane = OldCommitPane
    try:
        sections, commit_spec = _synthetic_registry(n_slow=1)
        app = ConfigTreeApp(sections, commit_spec, initial_state={})
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            tree = app.query_one("#ct-tree", Tree)
            commit_node = next(n for n in tree.root.children if (n.data or {}).get("kind") == "commit")
            tree.select_node(commit_node)
            tree.action_select_cursor()
            await pilot.pause()
            commit_btn = app.query_one("#pane-commit #ct-commit", Button)
            latency = await _press_and_time_tree_response(pilot, tree, commit_btn)
            assert latency >= SLOW_SUBMIT_SECONDS * RESPONSIVE_FRACTION, (
                f"expected the OLD synchronous CommitPane to freeze the event loop for roughly "
                f"the full {SLOW_SUBMIT_SECONDS}s sleep -- the concurrent keypress took only "
                f"{latency:.3f}s, i.e. this reproduction did not actually exercise the hazard")
            print(f"case 1 ok (RED, reproduced against {PRE_FIX_COMMIT}): a concurrent Tree "
                  f"keypress took {latency:.3f}s to process against a {SLOW_SUBMIT_SECONDS}s "
                  f"synthetic slow submit -- the OLD synchronous sweep froze the whole event "
                  f"loop, the keypress was processed only AFTER the freeze, never during it")
            # Let the OLD handler's own (now-finished) commit act settle before the Pilot
            # context tears down -- nothing left in flight, no dangling-task noise on exit.
            await pilot.pause()
    finally:
        ct_app_module.CommitPane = original


async def case_2_responsive() -> None:
    sections, commit_spec = _synthetic_registry(n_slow=1)
    app = ConfigTreeApp(sections, commit_spec, initial_state={})
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        commit_node = next(n for n in tree.root.children if (n.data or {}).get("kind") == "commit")
        tree.select_node(commit_node)
        tree.action_select_cursor()
        await pilot.pause()
        commit_btn = app.query_one("#pane-commit #ct-commit", Button)
        latency = await _press_and_time_tree_response(pilot, tree, commit_btn)
        assert latency < SLOW_SUBMIT_SECONDS * RESPONSIVE_FRACTION, (
            f"expected the CURRENT worker-based CommitPane to leave the event loop free -- the "
            f"concurrent keypress took {latency:.3f}s, indistinguishable from a frozen loop")
        print(f"case 2 ok (GREEN): the SAME concurrent Tree keypress now takes only "
              f"{latency:.3f}s (< {SLOW_SUBMIT_SECONDS * RESPONSIVE_FRACTION:.3f}s) against the "
              f"SAME {SLOW_SUBMIT_SECONDS}s synthetic slow submit -- processed DURING the sweep, "
              f"not after it")
        await _settle(app._commit_pane)


async def case_3_busy_chrome() -> None:
    sections, commit_spec = _synthetic_registry(n_slow=1)
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
        await asyncio.sleep(0.05)
        await pilot.pause()
        assert commit_pane.is_commit_running, "expected the sweep to still be in flight"
        assert commit_btn.disabled, "the commit button must be disabled WHILE a run is in flight (C26)"
        assert not cancel_btn.disabled, "Cancel must be enabled while a run is in flight"
        busy = app.query_one("#ct-commit-busy", Static)
        assert busy.display, "expected a visible busy indicator while the sweep runs (C26)"
        assert str(busy.render()).strip(), "expected non-empty busy text, not merely a shown-but-blank widget"
        print(f"case 3 ok (GREEN): WHILE the sweep runs -- commit button disabled, Cancel "
              f"enabled, busy indicator shown with text {str(busy.render())[:60]!r}")
        await _settle(commit_pane)
        await pilot.pause()
        assert not commit_pane.is_commit_running, "expected the run to have settled"
        assert commit_pane.is_committed, "expected the synthetic (always-successful) commit to complete"
        assert commit_btn.disabled, "the button stays disabled once committed (unchanged contract)"
        assert cancel_btn.disabled, "Cancel disables again once settled"
        assert not busy.display, "the busy indicator must clear once the run settles"
        print("case 3 ok (GREEN, completion): busy chrome clears, is_committed=True, matching "
              "the pre-existing post-commit disabled-button contract")


async def case_4_cancellation() -> None:
    sections, commit_spec = _synthetic_registry(n_slow=2)
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
        # Cancel mid-way through the FIRST slow section (well before the second one would start).
        await asyncio.sleep(SLOW_SUBMIT_SECONDS * 0.3)
        cancel_btn.press()
        await _settle(commit_pane)
        assert app.state.get("_ran", []) == ["slow-0"], (
            f"expected ONLY the first slow section to have run before cancellation stopped the "
            f"sweep between sections -- got {app.state.get('_ran')!r}")
        assert not commit_pane.is_committed, "a cancelled run must not read as committed"
        assert not commit_btn.disabled, "the button must re-enable after a cancelled run for a fresh attempt"
        print("case 4a ok (GREEN, clean between-section cancel): Cancel pressed during the "
              "first of two slow sections stopped the sweep before the second one ran -- "
              f"app.state['_ran'] == {app.state.get('_ran')!r}, nothing committed, button "
              "re-enabled for a retry")

        # A second, full press now succeeds normally (the cancelled attempt left no stale
        # residue behind to trip up a retry -- CommitSpec.reset has no synthetic accumulator
        # here, but `_commit_errors`/`_commit_sweep_error` must both still be clear).
        app.state.pop("_ran", None)
        commit_btn.press()
        await asyncio.sleep(0.1)  # let the retry actually start before polling settle
        await _settle(commit_pane, timeout=SLOW_SUBMIT_SECONDS * 2 + 5.0)
        assert app.state.get("_ran") == ["slow-0", "slow-1"], (
            f"expected BOTH slow sections to run on the uncancelled retry -- got "
            f"{app.state.get('_ran')!r}")
        assert commit_pane.is_committed, "expected the retried, uncancelled run to complete"
        print("case 4b ok (GREEN, retry after cancel): both synthetic sections ran and the "
              "commit act completed -- the cancelled attempt left no residue behind")


async def case_5_ctrl_q_during_run() -> None:
    sections, commit_spec = _synthetic_registry(n_slow=1)
    app = ConfigTreeApp(sections, commit_spec, initial_state={})
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        commit_node = next(n for n in tree.root.children if (n.data or {}).get("kind") == "commit")
        tree.select_node(commit_node)
        tree.action_select_cursor()
        await pilot.pause()
        commit_btn = app.query_one("#pane-commit #ct-commit", Button)
        commit_pane = app._commit_pane
        commit_btn.press()
        await asyncio.sleep(0.05)
        assert commit_pane.is_commit_running, "expected the sweep to still be in flight"
        t0 = time.monotonic()
        await pilot.press("ctrl+q")
        quit_latency = time.monotonic() - t0
        assert app.return_code == 130, f"expected ctrl+q's exit-code contract (130), got {app.return_code}"
        assert quit_latency < SLOW_SUBMIT_SECONDS * RESPONSIVE_FRACTION, (
            f"expected ctrl+q to be honored PROMPTLY during a run ({quit_latency:.3f}s), not "
            f"only after the background sweep settles")
        print(f"case 5 ok (GREEN): ctrl+q during an in-flight sweep still exits with "
              f"return_code=130 in {quit_latency:.3f}s (< the {SLOW_SUBMIT_SECONDS}s sweep "
              f"itself) -- the priority binding is honored on the never-blocked event loop")


async def _main() -> None:
    await case_1_red()
    await case_2_responsive()
    await case_3_busy_chrome()
    await case_4_cancellation()
    await case_5_ctrl_q_during_run()
    print("ALL CASES OK -- tools.configtree.commit_pane.CommitPane's submit sweep + commit act run "
          "off the UI thread (@work(thread=True)): RED-first against the OLD synchronous code "
          "(a concurrent keypress froze behind the sweep), GREEN against the CURRENT worker-"
          "based code (the same keypress, and ctrl+q's own exit-code contract, both processed "
          "DURING the sweep), a visible busy chrome (C26) while running, and a clean "
          "between-section cancel (C9) honored up to -- but honestly not into -- the "
          "non-cancellable commit act itself.")


if __name__ == "__main__":
    asyncio.run(_main())
