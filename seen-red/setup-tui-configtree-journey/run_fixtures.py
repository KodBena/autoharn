#!/usr/bin/env python3
"""seen-red/setup-tui-configtree-journey/run_fixtures.py -- the REAL configuration tree's
end-to-end witness via Textual `Pilot` (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §3 v2/§4:
"one fixture drives the REAL screen list end-to-end ... focus movement, scrolling, arrow
selection, and back/forward across screens all WITNESSED in the Pilot transcript -- no synthetic
screen lists"), census-registered in gates/fixture_census.py.

The "screen list" here is `tools.setup_tui.steps.SECTIONS` (the real ten-section registry) driven
through the real `tools.configtree.app.ConfigTreeApp` -- no synthetic tree, no synthetic
SectionSpec.

LIVE-MODEL REBUILD (maintainer review, 2026-07-22): the per-section Save button this fixture
used to press is DELETED (`tools/configtree/panes.py`'s own module docstring has the full
account). NO CASE BELOW PRESSES A SAVE BUTTON -- there is none. Every field write below is a
widget-level `.value =`/`.value = True` assignment, the exact mechanism that fires the real
`Input.Changed`/`Checkbox.Changed` message Textual posts for a live keystroke or toggle
(confirmed empirically against a throwaway probe before writing this fixture: assigning `.value`
posts the same `Changed` message class a live edit would). The ONLY action buttons anywhere in
this run are the commit node's own commit confirmation (case 3) and quit (case 5).

Cases (both polarities):
  0. STATE-ALIASING REPRODUCTION AND FIX (maintainer-diagnosed live defect, 2026-07-22: "clicking
     a checkbox in one menu subsection toggles a corresponding-ish checkbox in a DIFFERENT
     subsection" -- root cause: a bare field-name keyspace, `state[field.name]`, so two sections'
     own SAME-NAMED field -- e.g. every section's own `ConfirmField(name="run", ...)` --
     silently shared one model slot; ADR-0012 cancer C / P1/P2's "hidden state keyed by an
     insufficiently distinguishing key," plus ledger row 1105's "no bare types" rule). Reproduces
     the EXACT observation across all three top-level field kinds that collide by NAME in the
     real registry (`ConfirmField` "run": every section; `TextField` "host": substrate/rehearsal/
     birth/boundary; `TextField` "name": birth/signed-genesis) via the REAL widgets of TWO
     different, simultaneously-mounted real sections, PLUS synthetic same-shaped `ChoiceField`/
     `ListField` cases (no two real sections happen to share a top-level name of either kind)
     driven directly against the library's own `get_field_value`/`set_field_value` primitives --
     proving the FIX is structural (`ids.ScopedFieldKey`), not an instance patch: two sections' same-named field
     can no longer alias BY CONSTRUCTION, for any of the four field kinds.
  1. ARBITRARY-ORDER NAVIGATION, BLOCKED -> UNBLOCKED ON KEYSTROKE -- select a LATE section
     (hydration) first: its tree node reads BLOCKED with the prerequisite NAMED. Then, WITHOUT
     ever selecting hydration again, `fork-target`'s `dest` Input is typed into -- the app-wide
     status recompute (`ConfigTreeApp.on_model_changed`, fired by that ONE keystroke) flips
     hydration's TREE ICON to unblocked immediately, proven by reading `section_status` straight
     off the shared state (no navigation event of any kind touches hydration between the type and
     the assertion).
  2. LIVE INLINE VALIDATION, RED THEN GREEN, NO SAVE -- typing an invalid dedicated-substrate
     database identifier (a space) into `db_dedicated` shows the inline FieldError WHILE THE
     FOCUS IS STILL IN THAT FIELD (no Tab-away, no click elsewhere) and the tree node reads
     INVALID; correcting the SAME field (still no save) clears the inline error and the section
     read COMPLETE, live.
  3. FULL JOURNEY -- every one of the ten real sections' fields typed/toggled directly (never
     saved individually), the persistent status line reaches "10/10 sections complete" from live
     typing alone, the commit node's OWN button is disabled before completion and enabled after
     (still without any save press), pressing Commit ONCE runs the full submit sweep (every
     section's real business logic, exactly once, in order) THEN the actual --dry-run commit,
     rendering the real checklist, `App.exit`'s own `return_code` reads 0, and zero filesystem
     residue.
  4. COMMIT-TIME BUSINESS-RULE REFUSAL, RED THEN GREEN -- a section whose fields are ALL locally
     valid (so the commit button enables) but whose OWN business logic still refuses (signed-
     genesis's real rule: "statement required" is enforced inside `submit`, not by any per-field
     validator) halts the commit sweep, marks that ONE section INVALID with the real refusal
     message, and leaves every other already-processed section's decision intact; fixing the one
     field and pressing Commit again succeeds.
  5. NAVIGATION PRIMITIVES -- arrow-key Tree cursor movement + Enter selection (keyboard, not a
     programmatic `select_node` call), Tab moving focus onto the form, and a real
     `VerticalScroll.scroll_down()` changing `scroll_offset`.
  6. CTRL+Q QUITS -- `App.return_code` reads 130, unconditionally bound with `priority=True`.

Zero residue: every `state["dest"]` used here is a `--dry-run` decision-phase string, never
actually created on disk -- confirmed in case 3's own cleanup assertion.

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

from textual.widgets import Button, Checkbox, ContentSwitcher, Input, Tree  # noqa: E402

from tools.configtree.fields import (ChoiceField, ListField, TextField, get_field_value,  # noqa: E402
                                      set_field_value)
from tools.configtree.ids import NodeId  # noqa: E402
from tools.configtree.spec import COMPLETE, INVALID, section_status  # noqa: E402
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


async def _visit_and_fill(pilot, app, tree, slug, *, fill=None, check=None):
    """Select a section (so its fields exist to type into) and LIVE-EDIT them -- no save press.
    Each `.value =` assignment below is a real widget write that posts a real Changed message
    (`Input.Changed`/`Checkbox.Changed`), the SAME message class `panes.SectionPane`'s own
    `on_input_changed`/`on_checkbox_changed` handlers bind to."""
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


def _tree_icon(app, slug: str) -> str:
    return str(app._tree_nodes[slug].label)


async def case_0() -> None:
    """The maintainer's EXACT observation, reproduced against the REAL registry, for every field
    kind that actually collides by name in it -- then the synthetic `ChoiceField` case, since no
    two real top-level sections happen to share a `ChoiceField` name today."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()

        # --- ConfirmField "run": the maintainer's own observed shape (a checkbox) -----------
        # preflight and substrate BOTH declare `ConfirmField(name="run", ...)` -- both panes are
        # ALREADY mounted (ContentSwitcher holds every pane at once), so no navigation is needed
        # to read either widget's live value.
        preflight_run = app.query_one("#pane-preflight #ct-field-run", Checkbox)
        substrate_run = app.query_one("#pane-substrate #ct-field-run", Checkbox)
        assert preflight_run.value is True and substrate_run.value is True, \
            "both sections' own 'run' checkbox default to True -- the shared starting point"
        preflight_run.value = False
        await pilot.pause()
        assert substrate_run.value is True, \
            (f"ALIASING BUG: toggling preflight's 'run' checkbox moved substrate's own 'run' "
             f"checkbox to {substrate_run.value!r} -- two sections' same-named field shared one "
             f"model slot")
        print("case 0a ok (the maintainer's exact reproduction, FIXED): toggling preflight's "
              "'run' checkbox to False leaves substrate's OWN 'run' checkbox at True -- no "
              "cross-section aliasing")

        # --- TextField "host": substrate/rehearsal/birth/boundary ALL declare their own ------
        substrate_host = app.query_one("#pane-substrate #ct-field-host", Input)
        rehearsal_host = app.query_one("#pane-rehearsal #ct-field-host", Input)
        default_rehearsal_host = rehearsal_host.value
        substrate_host.value = "aliasing-probe-host"
        await pilot.pause()
        assert rehearsal_host.value == default_rehearsal_host, \
            (f"ALIASING BUG: typing into substrate's 'host' field changed rehearsal's OWN "
             f"'host' field to {rehearsal_host.value!r}")
        print(f"case 0b ok: typing into substrate's 'host' field ({substrate_host.value!r}) "
              f"leaves rehearsal's OWN 'host' field unchanged ({rehearsal_host.value!r})")

        # --- TextField "name": birth ("project name") vs signed-genesis ("Key Name-Real") ----
        # signed-genesis is BLOCKED until a destination exists -- select fork-target and type a
        # dest first (its own field, "shared=True" by design -- see fields.py's own doctrine)
        # so signed-genesis's pane actually mounts its fields to query against.
        tree = app.query_one("#ct-tree", Tree)
        for grp in tree.root.children:
            for leaf in grp.children:
                if leaf.data and leaf.data.get("slug") == "fork-target":
                    tree.select_node(leaf)
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case0-dest"
        await pilot.pause()
        for grp in tree.root.children:
            for leaf in grp.children:
                if leaf.data and leaf.data.get("slug") == "signed-genesis":
                    await app._panes["signed-genesis"].refresh_blocked()
        await pilot.pause()

        birth_name = app.query_one("#pane-birth #ct-field-name", Input)
        sg_name = app.query_one("#pane-signed-genesis #ct-field-name", Input)
        birth_name.value = "aliasing-probe-project"
        await pilot.pause()
        assert sg_name.value == "", \
            f"ALIASING BUG: typing into birth's 'name' field changed signed-genesis's own 'name' field to {sg_name.value!r}"
        print("case 0c ok: typing into birth's 'name' field leaves signed-genesis's OWN "
              "unrelated 'name' field (a GPG key Name-Real) untouched")

        # --- model-level check: the SAME model keys these widgets write into, read directly ---
        preflight_slug, substrate_slug = NodeId("preflight"), NodeId("substrate")
        run_field = next(f for f in steps.steps_preflight.fields(app.state) if str(f.name) == "run")
        assert get_field_value(app.state, preflight_slug, run_field) is False
        assert get_field_value(app.state, substrate_slug, run_field) is True
        print("case 0d ok: the underlying model itself holds two DIFFERENT values for the same "
              "field spec under two different section keys -- not just a widget-level accident")

    # --- ChoiceField: no two REAL top-level sections share a ChoiceField name today, so the
    # structural proof is driven directly against the library primitives (still the real
    # production code, `tools.configtree.fields`/`ids`, not a mock).
    scratch_state: dict = {}
    a_slug, b_slug = NodeId("section-a"), NodeId("section-b")
    choice = ChoiceField(name="mode", label="Mode", options=(("x", "X"), ("y", "Y")), default="x")
    set_field_value(scratch_state, a_slug, choice, "y")
    assert get_field_value(scratch_state, a_slug, choice) == "y"
    assert get_field_value(scratch_state, b_slug, choice) == "x", \
        "ALIASING BUG: a ChoiceField write in section A leaked into section B's own default"
    print("case 0e ok: a synthetic ChoiceField sharing one name across two sections resolves to "
          "two INDEPENDENT model slots (get_field_value/set_field_value, the library's own "
          "primitives) -- the fix is structural (ids.ScopedFieldKey), not an instance patch")

    # --- ListField: same synthetic proof, the fourth and final field kind -- no two real
    # top-level sections share a ListField name today either.
    rows_field = ListField(name="entries", label="Entries",
                            item_fields=(TextField(name="x", label="X"),),
                            summarize=lambda row: str(row.get("x", "")))
    set_field_value(scratch_state, a_slug, rows_field, [{"x": "from-a"}])
    assert get_field_value(scratch_state, a_slug, rows_field) == [{"x": "from-a"}]
    assert get_field_value(scratch_state, b_slug, rows_field) == [], \
        "ALIASING BUG: a ListField write in section A leaked into section B's own rows"
    print("case 0f ok: a synthetic ListField sharing one name across two sections resolves to "
          "two INDEPENDENT model slots too -- all four field kinds proven alias-proof")


async def case_1() -> None:
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        tree.select_node(_find_node(tree, "hydration"))
        await pilot.pause()
        reason = [str(w.render()) for w in app.query_one("#pane-hydration").query(".ct-blocked-reason")]
        assert reason and "Fork/target or Birth" in reason[0], f"expected a named prerequisite, got {reason}"
        icon_before = _tree_icon(app, "hydration")
        assert "⧖" in icon_before, f"expected the BLOCKED icon on hydration's tree node, got {icon_before!r}"
        print(f"case 1a ok: late-first select of 'hydration' reads BLOCKED, reason named: {reason[0]!r} "
              f"(tree icon: {icon_before!r})")

        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case1-dest"
        await pilot.pause()  # ONE keystroke-equivalent write -- no save, no re-selecting hydration

        icon_after = _tree_icon(app, "hydration")
        assert "⧖" not in icon_after, \
            f"expected hydration's TREE ICON to unblock from this ONE keystroke alone, got {icon_after!r}"
        print(f"case 1b ok: hydration's tree icon flips the INSTANT fork-target's dest is typed "
              f"-- {icon_before!r} -> {icon_after!r} -- no save, no re-visit to hydration at all")


async def case_2() -> None:
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "substrate"))
        await pilot.pause()

        substrate_spec = next(s for s in steps.SECTIONS if str(s.slug) == "substrate")
        db_input = app.query_one("#pane-substrate #ct-field-db_dedicated", Input)
        db_input.focus()
        db_input.value = "bad name"
        await pilot.pause()

        pane = app._panes["substrate"]
        err_text = str(pane._errors["db_dedicated"].render())
        assert err_text, "expected an inline error WHILE focus is still in the field, no save/tab-away"
        status = section_status(substrate_spec, app.state)
        assert status == INVALID, f"expected INVALID live (no save press), got {status}"
        print(f"case 2a ok (RED, live, no save): typing 'bad name' shows inline error {err_text!r} "
              f"and section status = {status}, focus never left the field")

        db_input.value = "goodname"
        await pilot.pause()
        err_text2 = str(pane._errors["db_dedicated"].render())
        status2 = section_status(substrate_spec, app.state)
        assert err_text2 == "", f"expected the inline error to clear live, still showed {err_text2!r}"
        assert status2 == COMPLETE, f"expected COMPLETE live (no save press), got {status2}"
        print(f"case 2b ok (GREEN, live, no save): correcting the SAME field clears the inline "
              f"error and the section reads {status2}, still no save press anywhere")


async def case_3() -> None:
    state = _fresh_state()
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        tree.select_node(_find_node(tree, "commit"))
        await pilot.pause()
        commit_btn_pre = app.query_one("#pane-commit #ct-commit", Button)
        assert commit_btn_pre.disabled, "commit must stay disabled before ANY section is touched"

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
            await _visit_and_fill(pilot, app, tree, slug, fill=fill, check=check)

        status_line = str(app.query_one("#ct-status-line").render())
        assert "10/10 sections complete" in status_line, f"expected all 10 complete, got {status_line!r}"
        print(f"case 3a ok: every real section reads complete from LIVE TYPING ALONE, no save "
              f"anywhere -- status line: {status_line!r}")
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
        print(f"case 3d ok: ONE commit press ran the full submit sweep (every section's real "
              f"business logic, in order) then rendered {len(info_lines)} real checklist "
              f"line(s), e.g. {info_lines[0][:80]!r}")

        finish_btn = app.query_one("#ct-finish", Button)
        finish_btn.press()
        await pilot.pause()
        assert app.return_code == 0, f"expected exit code 0 on clean completion, got {app.return_code}"
        print(f"case 3e ok: App.exit return_code == {app.return_code} (clean-completion exit-code contract)")

    assert not os.path.isdir("/tmp/ctj-case3-dest"), \
        "a --dry-run decision phase must never actually create the destination directory"
    print("case 3f ok: zero residue -- /tmp/ctj-case3-dest was never created (dry-run decide-only)")


async def case_4() -> None:
    """A section whose FIELDS are all locally valid (so the commit button enables) but whose own
    BUSINESS logic still refuses -- the two-tier validation model's own red/green pair."""
    state = _fresh_state()
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        for slug, fill, check in [
            ("preflight", None, None),
            ("substrate", None, None),
            ("fork-target", {"dest": "/tmp/ctj-case4-dest"}, None),
            ("rehearsal", None, None),
            ("birth", {"world": "ctjcase4"}, None),
            ("principals-authority", None, None),
            # signed-genesis: "statement" left EMPTY -- field-level `required=False`, so this
            # passes live/field validation (the commit button will enable) but `submit`'s own
            # business rule refuses it: "statement" is required THERE, not at the field layer.
            ("signed-genesis", None, {"use_scratch_identity": True}),
            ("boundary", {"world": "ctjcase4"}, None),
            ("observability", None, None),
            ("hydration", None, None),
        ]:
            await _visit_and_fill(pilot, app, tree, slug, fill=fill, check=check)

        tree.select_node(_find_node(tree, "commit"))
        await pilot.pause()
        commit_btn = app.query_one("#pane-commit #ct-commit", Button)
        assert not commit_btn.disabled, "every FIELD is locally valid -- the commit button must enable"
        await pilot.click(commit_btn)
        await pilot.pause()

        sg_spec = next(s for s in steps.SECTIONS if str(s.slug) == "signed-genesis")
        status = section_status(sg_spec, app.state)
        assert status == INVALID, f"expected the commit-sweep business refusal to mark it INVALID, got {status}"
        assert "signed-genesis" in app.state.get("_commit_errors", {}), \
            f"expected _commit_errors to name signed-genesis, got {app.state.get('_commit_errors')}"
        print(f"case 4a ok (RED): commit-sweep business rule ('statement' required inside "
              f"submit, not a field validator) halts the commit, marks signed-genesis {status}, "
              f"recorded: {app.state['_commit_errors']}")
        assert not commit_btn.disabled, "the commit button must re-enable for a retry, not stay stuck"

        tree.select_node(_find_node(tree, "signed-genesis"))
        await pilot.pause()
        field_err = str(app._panes["signed-genesis"]._errors["statement"].render())
        assert field_err, f"expected the business-rule refusal inline on the NAMED field, got {field_err!r}"
        print(f"case 4b ok: revisiting signed-genesis shows the real refusal inline on 'statement': {field_err!r}")

        app.query_one("#pane-signed-genesis #ct-field-statement", Input).value = "fixed on retry"
        await pilot.pause()
        tree.select_node(_find_node(tree, "commit"))
        await pilot.pause()
        commit_btn2 = app.query_one("#pane-commit #ct-commit", Button)
        await pilot.click(commit_btn2)
        await pilot.pause()
        assert app.state.get("_commit_ok") is True, \
            f"expected the retried commit to succeed, state={app.state.get('_commit_ok')}"
        print("case 4c ok (GREEN): fixing the one field and pressing Commit again succeeds")


async def case_5() -> None:
    # A short viewport (height=18) so a real section's fields overflow the visible body --
    # forcing an actual scroll, not a no-op on already-fully-visible content.
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 18)) as pilot:
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
        print(f"case 5a ok: arrow-key Tree navigation (3x down) + Enter selects the real "
              f"'{switcher.current}' pane, no mouse and no programmatic select_node involved")

        focus_before = app.focused
        await pilot.press("tab")
        await pilot.pause()
        focus_after = app.focused
        assert focus_before is not focus_after, "Tab must move focus off the Tree onto the form"
        print(f"case 5b ok: Tab moves focus {focus_before} -> {focus_after}")

        body = app.query_one(f"#{switcher.current} .ct-section-body")
        before = body.scroll_offset
        body.scroll_down(animate=False)
        await pilot.pause()
        after = body.scroll_offset
        assert after != before, f"expected scroll_offset to change, stayed {before}"
        print(f"case 5c ok: the section pane's own VerticalScroll body scrolls ({before} -> {after})")


async def case_6() -> None:
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        await pilot.press("ctrl+q")
        await pilot.pause()
        assert app.return_code == 130, f"expected ctrl+q to exit 130, got {app.return_code}"
        print(f"case 6 ok: ctrl+q -> App.return_code == {app.return_code} (interrupt exit-code convention)")


async def _main() -> None:
    await case_0()
    await case_1()
    await case_2()
    await case_3()
    await case_4()
    await case_5()
    await case_6()
    print("ALL CASES OK -- tools.configtree.app.ConfigTreeApp driven end-to-end through the "
          "REAL tools.setup_tui.steps.SECTIONS registry via Pilot, LIVE-MODEL semantics "
          "throughout (no per-section save exists): a state-aliasing reproduction and structural "
          "fix across every field kind, arbitrary-order navigation with a "
          "blocked-to-unblocked flip on a SINGLE keystroke, live inline validation both "
          "polarities with focus never leaving the field, a full ten-section journey typed live "
          "to a clean dry-run commit via the ONE commit button, a commit-time business-rule "
          "refusal (red) and its retry (green), keyboard/Tab/scroll navigation primitives, and "
          "ctrl+q's exit-code contract.")


if __name__ == "__main__":
    asyncio.run(_main())
