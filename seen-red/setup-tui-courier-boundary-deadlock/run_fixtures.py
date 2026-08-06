#!/usr/bin/env python3
"""seen-red/setup-tui-courier-boundary-deadlock/run_fixtures.py -- ledger rows 149/150: the
maintainer's own reported dead end, `python3 -m tools.setup_tui`, courier's section reading
"BLOCKED -- requires: Boundary (a picked boundary URL) to be set first" -- "which is NOT even
possible to do." Census-registered in gates/fixture_census.py.

ROOT CAUSE (verified against the REAL registry, `tools.setup_tui.steps.SECTIONS`): courier's own
`blocked()` (`tools/setup_tui/steps_courier.py`, pre-fix `_blocked_needs_boundary`) required
`state["boundary_url"]` to already be set. `boundary_url` is not a shared/live field at all -- it
is a value Boundary's OWN `submit()` computes (`steps_boundary.py`: `port = probes.free_port()`
then `updates["boundary_url"] = boundary_url`) and returns via `state_updates`; `submit()` is
called ONLY from the commit sweep (`tools.configtree.commit_pane.CommitPane._run_submit_sweep`),
never merely by visiting/filling the Boundary screen. So courier could never leave BLOCKED before
a commit even started -- and `tools.configtree.spec.ready_for_commit` (the commit BUTTON's own
enablement predicate) refuses to enable while ANY section reads BLOCKED. A genuine catch-22: the
one screen that could satisfy courier's own precondition is a screen whose OWN submit only runs
AFTER the button courier itself is blocking.

THE FIX (`tools/setup_tui/steps_courier.py`, this same ledger-row pair): courier's `blocked()` now
gates on the TWO live-settable shared facts it actually reads directly in its own `submit`
("dest"/"world", Fork/target's and Birth's own owned fields, both flip the instant their OWNING
section's field is typed into) -- never on "boundary_url". `submit`'s own `self_base = state.
get("boundary_url", "")` already tolerated "not yet known" before this fix; the ONLY thing that
was ever missing was UNBLOCKING the screen to let that tolerance matter. Registry order
(`steps.py`'s own module docstring: "the sidebar order AND the real commit-time execution order")
still runs `boundary` immediately before `courier` in the SAME commit sweep, so by the time
courier's `submit` actually executes, `state["boundary_url"]` is already the real picked port --
the written `courier.toml`'s own `self_base` is correct, never blank, at the only time it is ever
actually written to a plan act.

Cases (both polarities, all driven against the REAL `tools.configtree.app.ConfigTreeApp` +
`tools.setup_tui.steps.SECTIONS`/`COMMIT` via Textual `Pilot` -- no synthetic screen list):

  1. RED, PINNED -- courier's `blocked()` reverted (in a synthetic SECTIONS tuple, `dataclasses.
     replace` swapping ONLY courier's `blocked` callable for a copy of the pre-fix predicate;
     every other section is the REAL, current one) to the pre-fix predicate. Fork/target's `dest`
     and Birth's `world` are filled (courier's own genuinely satisfiable prerequisites) and EVERY
     OTHER section is also visited/filled -- courier still reads BLOCKED, naming "Boundary (a
     picked boundary URL)" verbatim (the maintainer's own observed text), and `ready_for_commit`
     stays False: the commit button can never enable, reproducing the exact dead end.
  2. GREEN, SKIP POLARITY -- the REAL (current) app, the full 12-section journey, courier's own
     `counterparts` list left EMPTY (the section's own documented "skip" shape, `steps_courier.py`
     module docstring: "when the operator leaves `counterparts` empty, `courier.toml` is NOT
     queued for writing at all"). Courier never shows the retired "Boundary" reason at any point
     -- including when selected FIRST, before Fork/target/Birth are even touched. "12/12 sections
     complete", the commit button enables, one commit press succeeds, and the rendered
     dry-run checklist/plan carries NO `courier.toml` write act.
  3. GREEN, NON-SKIP POLARITY -- the same real journey, courier's `counterparts` filled with ONE
     row via the REAL "Add" button + `AddItemModal` (a real Textual modal, not a shortcut). The
     precondition this whole defect was about -- "a picked boundary URL" -- is now genuinely
     satisfiable: the commit succeeds, `courier.toml` IS queued for writing, and its queued
     content's own `self_base` line carries the SAME value as `state["boundary_url"]` (Boundary's
     own submit, run immediately before courier's in the same sweep) -- proving the derived value
     resolves correctly end-to-end, not merely that the gate stopped blocking.

Zero residue: every `state["dest"]` here is a `--dry-run` decision-phase string, never actually
created on disk (checked in cases 2/3's own cleanup assertions, the same convention seen-red/
setup-tui-configtree-journey/run_fixtures.py's case 3 already establishes).

Lazy imports banned. Requires `textual` (system `python3` on this host carries it; the venv-
installed copy `seen-red/setup-tui-configtree-journey` cites works equally well) -- this fixture
is a Textual-witness leg, NOT covered by --from-config's textual-free guarantee.
Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-courier-boundary-deadlock/run_fixtures.py
"""
from __future__ import annotations

import asyncio
import dataclasses
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC.md §1: mark this process's own environment
# before any subprocess is spawned -- inherited by the whole process tree this fixture starts.
os.environ["AUTOHARN_FIXTURE_SANDBOX"] = "1"

from textual.widgets import Button, Checkbox, Input, Tree  # noqa: E402

from tools.configtree.app import ConfigTreeApp  # noqa: E402
from tools.configtree.spec import ready_for_commit, section_status  # noqa: E402
from tools.setup_tui import steps, tui_app  # noqa: E402
from tools.setup_tui.checklist import Checklist  # noqa: E402
from tools.setup_tui.plan import Plan  # noqa: E402


def _fresh_state() -> dict:
    return {"_checklist": Checklist(), "_plan": Plan(), "_repo_root": steps.REPO_ROOT,
            "dry_run": True, "accept_unverified_genesis": False}


def _pre_fix_blocked_needs_boundary(state: dict) -> "str | None":
    """`tools/setup_tui/steps_courier.py`'s own `_blocked_needs_boundary`, byte-for-byte, AS IT
    STOOD before this fix (ledger rows 149/150) -- the retired predicate this fixture's RED case
    pins back in, against every OTHER section left at its current, real logic."""
    missing = []
    if not state.get("dest"):
        missing.append("Fork/target (a destination directory)")
    if not state.get("world"):
        missing.append("Birth (a world name)")
    if not state.get("boundary_url"):
        missing.append("Boundary (a picked boundary URL)")
    if not missing:
        return None
    return f"requires: {' and '.join(missing)} to be set first"


def _find_node(tree: Tree, slug: str):
    for grp in tree.root.children:
        for leaf in grp.children:
            if leaf.data and leaf.data.get("slug") == slug:
                return leaf
    if slug == "commit":
        for leaf in tree.root.children:
            if leaf.data and leaf.data.get("kind") == "commit":
                return leaf
    raise AssertionError(f"no tree node for slug {slug!r}")


def _tree_icon(app, slug: str) -> str:
    return str(app._tree_nodes[slug].label)


async def _visit_and_fill(pilot, app, tree, slug, *, fill=None, check=None):
    """Select a section and LIVE-EDIT its Input/Checkbox fields -- the same, real
    widget-write-posts-a-real-Changed-message idiom `setup-tui-configtree-journey`'s own
    `_visit_and_fill` uses (no save button exists anywhere in this app)."""
    tree.select_node(_find_node(tree, slug))
    await pilot.pause()
    if fill:
        for name, value in fill.items():
            app.query_one(f"#pane-{slug} #ct-field-{name}", Input).value = value
            await pilot.pause()
    if check:
        for name, value in check.items():
            app.query_one(f"#pane-{slug} #ct-field-{name}", Checkbox).value = value
            await pilot.pause()


_JOURNEY_FILLS = [
    ("preflight", None, None),
    ("features", None, None),
    ("substrate", None, None),
    ("fork-target", {"dest": "/tmp/courier-deadlock-dest"}, None),
    ("rehearsal", None, None),
    ("birth", {"world": "courierdeadlk"}, None),
    ("principals-authority", None, None),
    ("signed-genesis", {"statement": "a witnessed probe world"}, {"use_scratch_identity": True}),
    ("boundary", None, None),
    ("observability", None, None),
    ("hydration", None, None),
]


async def case_1_red_pinned_deadlock() -> None:
    """RED: the pre-fix predicate pinned back onto courier alone -- everything else real,
    current code. Fills EVERY section (courier's own genuinely satisfiable prerequisites
    included) and still finds courier permanently BLOCKED and the commit unreachable."""
    pinned_courier = dataclasses.replace(steps.steps_courier.STEP,
                                          blocked=_pre_fix_blocked_needs_boundary)
    sections = tuple(pinned_courier if str(s.slug) == "courier" else s for s in steps.SECTIONS)
    state = _fresh_state()
    app = ConfigTreeApp(sections, steps.COMMIT, actions=steps.ACTIONS, initial_state=state)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        for slug, fill, check in _JOURNEY_FILLS:
            await _visit_and_fill(pilot, app, tree, slug, fill=fill, check=check)

        assert app.state.get("boundary_url") is None, \
            ("expected 'boundary_url' to still be ABSENT pre-commit (it is only ever produced "
             f"inside Boundary's own submit(), commit-sweep-only) -- got "
             f"{app.state.get('boundary_url')!r}")

        tree.select_node(_find_node(tree, "courier"))
        await pilot.pause()
        reason = [str(w.render()) for w in app.query_one("#pane-courier").query(".ct-blocked-reason")]
        assert reason and "Boundary (a picked boundary URL)" in reason[0], \
            f"expected the maintainer's own observed reason, got {reason}"
        icon = _tree_icon(app, "courier")
        assert "⧖" in icon, f"expected courier's tree node BLOCKED, got {icon!r}"
        status = section_status(pinned_courier, app.state)
        assert status == "blocked", f"expected courier status 'blocked', got {status!r}"
        ready = ready_for_commit(sections, app.state)
        assert ready is False, \
            "expected ready_for_commit() False -- the commit button can never enable"
        tree.select_node(_find_node(tree, "commit"))
        await pilot.pause()
        commit_btn = app.query_one("#pane-commit #ct-commit", Button)
        assert commit_btn.disabled, \
            "expected the commit button to stay disabled -- a real, permanent dead end"
        print(f"case 1 ok (RED, pinned pre-fix courier gate): every OTHER section filled "
              f"(including courier's own genuinely satisfiable dest/world prerequisites), "
              f"courier STILL reads BLOCKED: {reason[0]!r} -- ready_for_commit()={ready}, "
              f"commit button disabled={commit_btn.disabled} -- the maintainer's exact dead end, "
              f"reproduced against the real app")


async def case_2_green_skip_polarity() -> None:
    """GREEN, skip polarity: the REAL (current) app end-to-end, courier's counterparts left
    empty. Courier never shows the retired 'Boundary' reason, even selected FIRST before
    Fork/target/Birth are touched; the full journey reaches 12/12 and commits; courier.toml is
    NOT queued (the section's own documented skip contract)."""
    state = _fresh_state()
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        # Select courier FIRST, before anything else -- prove its blocked reason (while genuinely
        # blocked) never names "Boundary" even in the earliest possible state.
        tree.select_node(_find_node(tree, "courier"))
        await pilot.pause()
        reason0 = [str(w.render()) for w in app.query_one("#pane-courier").query(".ct-blocked-reason")]
        assert reason0, f"expected courier BLOCKED before dest/world are set, got {reason0}"
        assert "Boundary" not in reason0[0], \
            f"the retired 'Boundary (a picked boundary URL)' reason must never reappear, got {reason0[0]!r}"
        assert "Fork/target" in reason0[0] and "Birth" in reason0[0], \
            f"expected the genuinely satisfiable prerequisites named, got {reason0[0]!r}"
        print(f"case 2a ok: courier selected FIRST reads BLOCKED on ONLY its true, "
              f"live-settable prerequisites: {reason0[0]!r} -- 'Boundary' never named")

        for slug, fill, check in _JOURNEY_FILLS:
            await _visit_and_fill(pilot, app, tree, slug, fill=fill, check=check)
        # courier itself: select it, confirm UNBLOCKED, leave counterparts empty (skip).
        tree.select_node(_find_node(tree, "courier"))
        await pilot.pause()
        assert not app.query_one("#pane-courier").query(".ct-blocked-reason"), \
            "expected courier UNBLOCKED once dest+world are set (no Boundary visit needed)"
        courier_status = section_status(steps.steps_courier.STEP, app.state)
        assert courier_status == "complete", \
            f"expected courier 'complete' with zero counterparts (skip is valid), got {courier_status}"
        print("case 2b ok: courier reads COMPLETE with an empty counterparts list -- the skip "
              "affordance IS 'leave the list empty', per the section's own documented contract")

        status_line = str(app.query_one("#ct-status-line").render())
        assert "12/12 sections complete" in status_line, f"expected all 12 complete, got {status_line!r}"
        print(f"case 2c ok: status line -- {status_line!r}")

        tree.select_node(_find_node(tree, "commit"))
        await pilot.pause()
        commit_btn = app.query_one("#pane-commit #ct-commit", Button)
        assert not commit_btn.disabled, "expected the commit button enabled -- no more dead end"
        await pilot.click(commit_btn)
        await pilot.pause()
        pane = app._commit_pane
        while pane.is_commit_running:
            await asyncio.sleep(0.02)
        assert app.state.get("_commit_ok") is True, \
            f"expected the commit to succeed, state={app.state.get('_commit_ok')}"
        plan_items = [e.item for e in app.state["_plan"].entries]
        assert not any("courier.toml" in item for item in plan_items), \
            f"expected NO courier.toml write act queued (empty counterparts) -- got {plan_items}"
        print(f"case 2d ok (GREEN, skip polarity): commit succeeded, _commit_ok=True, and the "
              f"queued plan carries NO courier.toml write act -- {len(plan_items)} other "
              f"plan item(s) present")

    assert not os.path.isdir("/tmp/courier-deadlock-dest"), \
        "a --dry-run decision phase must never actually create the destination directory"
    print("case 2e ok: zero residue -- /tmp/courier-deadlock-dest was never created")


async def _add_counterpart_row(pilot, app, world: str, base_url: str) -> None:
    """Drives the REAL 'Add' button + `AddItemModal` -- the actual Textual widgets an operator
    presses, not a state shortcut (this app is Textual-based end to end; this fixture drives it
    as such)."""
    add_btn = app.query_one("#pane-courier #ct-field-counterparts-add", Button)
    add_btn.scroll_visible(animate=False)
    await pilot.pause()
    await pilot.click(add_btn)
    await pilot.pause()
    # `app.screen` (not the bare `app.query_one`, which resolves against the App's own base
    # screen) -- the Add button just pushed `AddItemModal` on top of the screen stack, and its
    # fields live in THAT screen, not the underlying `pane-courier` one (confirmed empirically:
    # a bare `app.query_one("#ct-field-base_url")` raises `NoMatches` against `Screen(id=
    # '_default')` while the modal is on top; `app.screen.query_one` finds it every time).
    app.screen.query_one("#ct-field-world", Input).value = world
    await pilot.pause()
    app.screen.query_one("#ct-field-base_url", Input).value = base_url
    await pilot.pause()
    save_btn = app.screen.query_one("#ct-modal-save", Button)
    await pilot.click(save_btn)
    await pilot.pause()


async def case_3_green_non_skip_polarity() -> None:
    """GREEN, non-skip polarity: courier's counterparts filled with ONE real row via the actual
    Add button/modal. The precondition this whole defect was about -- 'a picked boundary URL' --
    is now genuinely satisfiable: the commit succeeds, courier.toml IS queued, and its own
    self_base line carries the SAME value Boundary's own submit picked this run."""
    state = _fresh_state()
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        for slug, fill, check in _JOURNEY_FILLS:
            await _visit_and_fill(pilot, app, tree, slug, fill=fill, check=check)

        tree.select_node(_find_node(tree, "courier"))
        await pilot.pause()
        await _add_counterpart_row(pilot, app, "courierdeadlkpeer", "http://127.0.0.1:9999")
        await pilot.pause()
        courier_status = section_status(steps.steps_courier.STEP, app.state)
        assert courier_status == "complete", \
            f"expected courier 'complete' with one real counterpart row added, got {courier_status}"
        print("case 3a ok: one counterpart row added via the REAL Add button + AddItemModal -- "
              "courier reads COMPLETE")

        status_line = str(app.query_one("#ct-status-line").render())
        assert "12/12 sections complete" in status_line, f"expected all 12 complete, got {status_line!r}"

        tree.select_node(_find_node(tree, "commit"))
        await pilot.pause()
        commit_btn = app.query_one("#pane-commit #ct-commit", Button)
        assert not commit_btn.disabled, "expected the commit button enabled"
        await pilot.click(commit_btn)
        await pilot.pause()
        pane = app._commit_pane
        while pane.is_commit_running:
            await asyncio.sleep(0.02)
        assert app.state.get("_commit_ok") is True, \
            f"expected the commit to succeed, state={app.state.get('_commit_ok')}"

        real_boundary_url = app.state.get("boundary_url")
        assert real_boundary_url, \
            (f"expected Boundary's own submit to have picked a real boundary_url by commit "
             f"time, got {real_boundary_url!r}")

        courier_entry = next((e for e in app.state["_plan"].entries if "courier.toml" in e.item), None)
        assert courier_entry is not None, "expected a courier.toml write act to be queued this time"
        written_content = courier_entry.act.content
        assert f'self_base = "{real_boundary_url}"' in written_content, \
            (f"expected the queued courier.toml's own self_base to equal the REAL picked "
             f"boundary_url {real_boundary_url!r}, got:\n{written_content}")
        assert 'courierdeadlkpeer = "http://127.0.0.1:9999"' in written_content, \
            f"expected the real counterpart row in the queued TOML, got:\n{written_content}"
        print(f"case 3b ok (GREEN, non-skip polarity): commit succeeded, courier.toml WAS "
              f"queued, and its own self_base line equals the REAL boundary_url picked this "
              f"run ({real_boundary_url!r}) -- the precondition this whole defect was about is "
              f"now genuinely satisfiable end-to-end:\n{written_content}")

    assert not os.path.isdir("/tmp/courier-deadlock-dest"), \
        "a --dry-run decision phase must never actually create the destination directory"
    print("case 3c ok: zero residue -- /tmp/courier-deadlock-dest was never created")


async def _main() -> None:
    await case_1_red_pinned_deadlock()
    await case_2_green_skip_polarity()
    await case_3_green_non_skip_polarity()
    print("ALL CASES OK -- courier's blocked() gate no longer depends on a value only ever "
          "produced inside the commit sweep it is itself gating; both the skip and non-skip "
          "polarities reach a complete, committed config; the retired 'Boundary (a picked "
          "boundary URL)' reason never reappears")


if __name__ == "__main__":
    asyncio.run(_main())
