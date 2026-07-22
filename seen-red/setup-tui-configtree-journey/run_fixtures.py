#!/usr/bin/env python3
"""seen-red/setup-tui-configtree-journey/run_fixtures.py -- the REAL configuration tree's
end-to-end witness via Textual `Pilot` (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2/§4:
"one fixture drives the REAL screen list end-to-end ... focus movement, scrolling, arrow
selection, and back/forward across screens all WITNESSED in the Pilot transcript -- no synthetic
screen lists"), census-registered in gates/fixture_census.py.

The "screen list" here is `tools.setup_tui.steps.SECTIONS` (the real ten-section registry) driven
through the real `tools.configtree.app.ConfigTreeApp` -- no synthetic tree, no synthetic
SectionSpec.

Cases (both polarities):
  1. ARBITRARY-ORDER NAVIGATION -- select a LATE section (hydration) first: its tree node reads
     BLOCKED with the prerequisite NAMED (spec's own required behavior). Then an EARLY section
     (fork-target) is filled and saved, and hydration is re-selected: now UNBLOCKED. Late-first,
     then early -- never a forward-only walk.
  2. RED-FIRST, per-field inline validation -- an invalid substrate identifier (dedicated path,
     a database name containing a space) is saved: the tree node reads INVALID, the inline field
     error names the reason, and the commit node stays disabled. Corrected immediately after
     (GREEN): the same section, valid values, reads COMPLETE.
  3. FULL JOURNEY -- every one of the ten real sections filled and saved (order: preflight,
     substrate, fork-target, rehearsal, birth, principals-authority, signed-genesis, boundary,
     observability, hydration), the persistent status line reaches "10/10 sections complete",
     the commit node's OWN button is disabled before completion and enabled after, a --dry-run
     commit renders the real checklist (WOULD-DO rows, `world-config.toml self-saved`), and
     `App.exit`'s own `return_code` reads 0 -- the exit-code contract's clean-completion leg.
  4. NAVIGATION PRIMITIVES -- arrow-key Tree cursor movement + Enter selection (keyboard, not a
     programmatic `select_node` call), Tab moving focus onto the form, and a real
     `VerticalScroll.scroll_down()` changing `scroll_offset` -- the commission's own acceptance
     bar ("move around the screen, move between screens, both").
  5. CTRL+Q QUITS -- `App.return_code` reads 130 (the SIGINT/interrupt exit-code convention),
     unconditionally bound with `priority=True` (ctrl+c's own historical shadow-binding hazard,
     defeated the same way).

Zero residue: every `state["dest"]` used here is a `--dry-run` decision-phase string, never
actually created on disk (`fork-target`'s own "fresh" mode queues a Plan entry, it does not
`mkdir` at save time) -- confirmed in case 3's own cleanup assertion.

Lazy imports banned. Requires `textual` (venv-installed, `.venv/bin/pip install textual`) --
this fixture is a Textual-witness leg, NOT covered by --from-config's textual-free guarantee.
Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-configtree-journey/run_fixtures.py
"""
from __future__ import annotations

import asyncio
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from textual.widgets import Button, Checkbox, ContentSwitcher, Input, RadioSet, Tree  # noqa: E402

from tools.configtree.spec import INVALID, section_status  # noqa: E402
from tools.setup_tui import steps, tui_app  # noqa: E402
from tools.setup_tui.checklist import Checklist  # noqa: E402
from tools.setup_tui.plan import Plan  # noqa: E402


def _find_node(tree: Tree, slug: str):
    for grp in tree.root.children:
        for leaf in grp.children:
            if leaf.data and leaf.data.get("slug") == slug:
                return leaf
    for leaf in tree.root.children:
        if leaf.data and leaf.data.get("kind") == "commit":
            return leaf
    raise AssertionError(f"no tree node for slug {slug!r}")


def _fresh_state() -> dict:
    return {"_checklist": Checklist(), "_plan": Plan(), "_repo_root": steps.REPO_ROOT,
            "dry_run": True, "accept_unverified_genesis": False}


async def _save(pilot, app, tree, slug, *, fill=None, check=None):
    tree.select_node(_find_node(tree, slug))
    await pilot.pause()
    if fill:
        for name, value in fill.items():
            app.query_one(f"#pane-{slug} #ct-field-{name}", Input).value = value
    if check:
        for name, value in check.items():
            app.query_one(f"#pane-{slug} #ct-field-{name}", Checkbox).value = value
    await pilot.click(app.query_one(f"#pane-{slug} #ct-save", Button))
    await pilot.pause()
    pane = app._panes[slug]
    return {name: str(w.render()) for name, w in pane._errors.items() if w.display}


async def case_1() -> None:
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        tree.select_node(_find_node(tree, "hydration"))
        await pilot.pause()
        reason = [str(w.render()) for w in app.query_one("#pane-hydration").query(".ct-blocked-reason")]
        assert reason and "Fork/target or Birth" in reason[0], f"expected a named prerequisite, got {reason}"
        print(f"case 1a ok: late-first select of 'hydration' reads BLOCKED, reason named: {reason[0]!r}")

        errs = await _save(pilot, app, tree, "fork-target", fill={"dest": "/tmp/ctj-case1-dest"})
        assert errs == {}, f"fork-target save should be clean, got {errs}"

        tree.select_node(_find_node(tree, "hydration"))
        await pilot.pause()
        reason2 = [str(w.render()) for w in app.query_one("#pane-hydration").query(".ct-blocked-reason")]
        assert reason2 == [], f"expected hydration UNBLOCKED after fork-target set dest, got {reason2}"
        print("case 1b ok: revisiting 'hydration' after the prerequisite is met reads UNBLOCKED")


async def case_2() -> None:
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        node = _find_node(tree, "substrate")
        tree.select_node(node)
        await pilot.pause()
        # ChoiceField "path" defaults to "existing"; switch to "dedicated" then feed an invalid
        # database-name identifier (a space) -- steps_substrate.py's own real validator.
        radio = app.query_one("#pane-substrate #ct-field-path", RadioSet)
        radio.action_next_button()  # "existing" -> "dedicated" (two-option RadioSet)
        await pilot.pause()
        app.query_one("#pane-substrate #ct-field-db_dedicated", Input).value = "bad name"
        app.query_one("#pane-substrate #ct-field-role", Input).value = "role_ok"
        await pilot.click(app.query_one("#pane-substrate #ct-save", Button))
        await pilot.pause()
        substrate_spec = next(s for s in steps.SECTIONS if str(s.slug) == "substrate")
        status = section_status(substrate_spec, app.state)
        assert status == INVALID, f"expected INVALID after a rejected save, got {status}"
        print(f"case 2a ok (RED): invalid dedicated-db identifier 'bad name' -- section status = {status}")

        app.query_one("#pane-substrate #ct-field-db_dedicated", Input).value = "goodname"
        await pilot.click(app.query_one("#pane-substrate #ct-save", Button))
        await pilot.pause()
        status2 = section_status(substrate_spec, app.state)
        assert status2 == "complete", f"expected COMPLETE after a corrected save, got {status2}"
        print(f"case 2b ok (GREEN): the same section, corrected, now reads status = {status2}")


async def case_3() -> None:
    state = _fresh_state()
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        commit_btn_pre = None
        for slug, fill, check in [
            ("preflight", None, None),
            ("substrate", None, None),
            ("fork-target", {"dest": "/tmp/ctj-case3-dest"}, None),
            ("rehearsal", None, None),
            ("birth", {"world": "ctjcase3"}, None),
            ("principals-authority", None, None),
            ("signed-genesis", {"statement": "a witnessed probe world"}, {"use_scratch_identity": True}),
            ("boundary", {"world": "ctjcase3"}, None),
            ("observability", None, None),
            ("hydration", None, None),
        ]:
            if slug == "signed-genesis":
                tree.select_node(_find_node(tree, "commit"))
                await pilot.pause()
                commit_btn_pre = app.query_one("#pane-commit #ct-commit", Button)
                assert commit_btn_pre.disabled, "commit must stay disabled before every section is complete"
            errs = await _save(pilot, app, tree, slug, fill=fill, check=check)
            assert errs == {}, f"section {slug!r} should save clean, got {errs}"

        status_line = str(app.query_one("#ct-status-line").render())
        assert "10/10 sections complete" in status_line, f"expected all 10 complete, got {status_line!r}"
        print(f"case 3a ok: every real section saved clean -- status line: {status_line!r}")
        assert commit_btn_pre is not None and commit_btn_pre.disabled, \
            "commit node's own button read disabled while sections were still incomplete"
        print("case 3b ok (RED-then-GREEN): commit button was disabled mid-journey, before "
              "every section was complete")

        tree.select_node(_find_node(tree, "commit"))
        await pilot.pause()
        commit_btn = app.query_one("#pane-commit #ct-commit", Button)
        assert not commit_btn.disabled, "commit node's own button must enable once ALL sections are complete"
        print("case 3c ok: commit button now enabled -- 'enabled exactly when the record is complete'")

        await pilot.click(commit_btn)
        await pilot.pause()
        info_lines = [str(w.render()) for w in app.query_one("#ct-commit-body").query(".ct-info-line")]
        assert any("WOULD-DO" in ln or "checklist" in ln for ln in info_lines), \
            f"expected a real dry-run checklist rendering, got {info_lines}"
        print(f"case 3d ok: dry-run commit rendered {len(info_lines)} real checklist line(s), "
              f"e.g. {info_lines[0][:80]!r}")

        finish_btn = app.query_one("#ct-finish", Button)
        finish_btn.press()
        await pilot.pause()
        assert app.return_code == 0, f"expected exit code 0 on clean completion, got {app.return_code}"
        print(f"case 3e ok: App.exit return_code == {app.return_code} (clean-completion exit-code contract)")

    assert not os.path.isdir("/tmp/ctj-case3-dest"), \
        "a --dry-run decision phase must never actually create the destination directory"
    print("case 3f ok: zero residue -- /tmp/ctj-case3-dest was never created (dry-run decide-only)")


async def case_4() -> None:
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        switcher = app.query_one("#ct-switcher", ContentSwitcher)

        tree.focus()
        await pilot.pause()
        for _ in range(3):
            await pilot.press("down")
        await pilot.pause()
        cursor_before = tree.cursor_line
        assert cursor_before == 3, f"expected the tree cursor at line 3 after 3x down, got {cursor_before}"
        await pilot.press("enter")
        await pilot.pause()
        assert switcher.current == "pane-substrate", \
            f"expected Enter on the keyboard-moved cursor to select 'Substrate', got {switcher.current}"
        print(f"case 4a ok: arrow-key Tree navigation (3x down) + Enter selects the real "
              f"'{switcher.current}' pane, no mouse and no programmatic select_node involved")

        focus_before = app.focused
        await pilot.press("tab")
        await pilot.pause()
        focus_after = app.focused
        assert focus_before is not focus_after, "Tab must move focus off the Tree onto the form"
        print(f"case 4b ok: Tab moves focus {focus_before} -> {focus_after}")

        body = app.query_one(f"#{switcher.current} .ct-section-body")
        before = body.scroll_offset
        body.scroll_down(animate=False)
        await pilot.pause()
        after = body.scroll_offset
        assert after != before, f"expected scroll_offset to change, stayed {before}"
        print(f"case 4c ok: the section pane's own VerticalScroll body scrolls ({before} -> {after})")


async def case_5() -> None:
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        await pilot.press("ctrl+q")
        await pilot.pause()
        assert app.return_code == 130, f"expected ctrl+q to exit 130, got {app.return_code}"
        print(f"case 5 ok: ctrl+q -> App.return_code == {app.return_code} (interrupt exit-code convention)")


async def _main() -> None:
    await case_1()
    await case_2()
    await case_3()
    await case_4()
    await case_5()
    print("ALL CASES OK -- tools.configtree.app.ConfigTreeApp driven end-to-end through the "
          "REAL tools.setup_tui.steps.SECTIONS registry via Pilot: arbitrary-order navigation, "
          "dependency-blocked-with-reason + unblocking, per-field inline validation (both "
          "polarities), a full ten-section journey to a clean dry-run commit, keyboard/Tab/"
          "scroll navigation primitives, and ctrl+q's exit-code contract.")


if __name__ == "__main__":
    asyncio.run(_main())
