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
  7. SINGLE-EDITABLE-HOME (maintainer round 3, ADR-0019 + the maintainer's own ADR-0002
     citation, "a duplicated mirror/projection of a value is a type error and refused on TUI
     start"): "dest" is owned by Fork/target, "world" by Birth; every OTHER section that used to
     declare either had the field DROPPED entirely -- no read-only reference anywhere either
     (struck, same ruling). Proves: `owner_of` agrees with the chosen owners; "dest"/"world"
     each render an editable widget in EXACTLY their owner and NOWHERE else, checked once each
     dependent section is genuinely UNBLOCKED (not merely hidden behind a blocked banner);
     editing dest in Fork/target then world in Birth propagates LIVE to boundary's own
     `blocked()` check (boundary itself never selected during either edit); and a synthetic
     double-owner declaration is refused BEFORE any Textual machinery starts (RED-first,
     construction-time raise).
  8. READABLE-MEASURE WIDTH CAP (maintainer round 4: a field label measured 394/613 characters,
     rendered as one unwrapped-feeling line spanning a wide terminal's full width -- "unbounded
     text measure ... bound to terminal width instead of a readable measure"). RED-first: a
     synthetic, uncapped `Static` at a 400-column terminal reproduces the class before any fix is
     shown. GREEN: the REAL app, at the SAME 400-column width, swept across EVERY section (not
     just principal registration) -- no capped-class widget anywhere exceeds
     `tools.configtree.measure.MEASURE` (78, matching the deleted `elements.py`'s own historical
     convention) -- including the ORIGINAL emitting site itself, the "Add a principal" modal's
     `agent_class`/`relation` fields, now real `ChoiceField` pickers with short labels instead of
     free text with the whole closed vocabulary dumped into its label.

Zero residue: every `state["dest"]` used here is a `--dry-run` decision-phase string, never
actually created on disk -- confirmed in case 3's own cleanup assertion.

Lazy imports banned. Requires `textual` (venv-installed, `.venv/bin/pip install textual`) --
this fixture is a Textual-witness leg, NOT covered by --from-config's textual-free guarantee.
Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-configtree-journey/run_fixtures.py
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
# `layout_invariant.py` is this fixture's own sibling module (ledger row 1139's NET half) -- its
# directory goes on `sys.path` too so it imports as a bare top-level name, no package `__init__`
# needed for a single-fixture-scoped helper.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from textual.app import App, ComposeResult  # noqa: E402
from textual.containers import VerticalScroll  # noqa: E402
from textual.pilot import Pilot  # noqa: E402
from textual.widgets import Button, Checkbox, ContentSwitcher, Input, RadioSet, Static, Tree  # noqa: E402

from tools.configtree import CommitSpec, DuplicatedSharedFieldError, SectionResult, SectionSpec  # noqa: E402
from tools.configtree.app import ConfigTreeApp  # noqa: E402
from tools.configtree.fields import (ChoiceField, DescriptionElement, ElucidationHeading,  # noqa: E402
                                      ListField, TextField, get_field_value, is_field_touched,
                                      set_field_value)
from tools.configtree.ids import NodeId  # noqa: E402
from tools.configtree.item_modal import AddItemModal as CurrentAddItemModal  # noqa: E402
from tools.configtree.master_detail import DetailListField, MasterDetailField  # noqa: E402
from tools.configtree.measure import MEASURE  # noqa: E402
from tools.configtree.spec import COMPLETE, INVALID, owner_of, section_status  # noqa: E402
from tools.configtree.widgets_master_detail import MasterDetailFieldWidget  # noqa: E402
from tools.setup_tui import checklist as ck  # noqa: E402
from tools.setup_tui import config_file, content, durable_decisions, feature_facts, steps, tui_app  # noqa: E402
from tools.setup_tui.checklist import Checklist  # noqa: E402
from tools.setup_tui.plan import Plan  # noqa: E402

import layout_invariant  # noqa: E402
from layout_invariant import wire_pilot  # noqa: E402

# GLOBAL POST-INTERACTION LAYOUT INVARIANT (ledger row 1139, NET half) -- wired here, ONCE, at
# import time, so EVERY case below (existing and any added later) is checked after every single
# `pilot.pause()`/`click()`/`press()` automatically; no case opts in, none can opt out.
# `layout_invariant.py`'s own module docstring has the full account of what it checks and why.
wire_pilot(Pilot)


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


async def _wait_commit_settled(app, timeout: float = 10.0) -> None:
    """The commit sweep+commit act now runs off the UI thread (`CommitPane`'s own `@work
    (thread=True)` worker, ledger row 1130's own sibling audit, ADR-0019 C24) -- a fixture
    pressing the commit button must POLL for the worker's own completion (`is_commit_running`
    flips False from the worker's `call_from_thread` completion callback) instead of assuming one
    `pilot.pause()` is enough, the way every OTHER (synchronous) write-through in this app still
    is."""
    pane = app._commit_pane
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while pane.is_commit_running:
        if loop.time() > deadline:
            raise AssertionError(f"commit worker did not settle within {timeout}s")
        await asyncio.sleep(0.02)


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
        # birth AND signed-genesis are both BLOCKED until a destination exists -- select
        # fork-target and type a dest first (its own OWNED field) so both panes actually mount
        # their fields to query against.
        tree = app.query_one("#ct-tree", Tree)
        for grp in tree.root.children:
            for leaf in grp.children:
                if leaf.data and leaf.data.get("slug") == "fork-target":
                    tree.select_node(leaf)
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case0-dest"
        await pilot.pause()
        for slug in ("birth", "signed-genesis"):
            await app._panes[slug].refresh_blocked()
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
            ("boundary", None, None),
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
        await _wait_commit_settled(app)
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
            ("boundary", None, None),
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
        await _wait_commit_settled(app)

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
        await _wait_commit_settled(app)
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
        # 5x down, not 3x (maintainer round 5, ledger row 1115, defect C(i)): the tree now has a
        # "Setup" group + "Load a configuration" node ABOVE "Substrate & target" (root, Setup,
        # Load a configuration, Substrate & target, Preflight, Substrate == cursor line 5) --
        # the offset shift is the direct, correct consequence of a real, reachable tree node
        # being added, not a fixture artifact to paper over.
        for _ in range(5):
            await pilot.press("down")
        await pilot.pause()
        cursor_before = tree.cursor_line
        assert cursor_before == 5, f"expected the tree cursor at line 5 after 5x down, got {cursor_before}"
        await pilot.press("enter")
        await pilot.pause()
        assert switcher.current == "pane-substrate", \
            f"expected Enter on the keyboard-moved cursor to select 'Substrate', got {switcher.current}"
        print(f"case 5a ok: arrow-key Tree navigation (5x down, past the new 'Setup' group) + "
              f"Enter selects the real '{switcher.current}' pane, no mouse and no programmatic "
              f"select_node involved")

        focus_before = app.focused
        await pilot.press("tab")
        await pilot.pause()
        focus_after = app.focused
        assert focus_before is not focus_after, "Tab must move focus off the Tree onto the form"
        print(f"case 5b ok: Tab moves focus {focus_before} -> {focus_after}")

        # CONTROL/HELP SPLIT (ledger row 1138): at this fixture's own 150-column width (WIDE,
        # `layout_split.WIDE_LAYOUT_MIN_WIDTH`), the section's own scrollable body is
        # `.ct-controls-col`, not the narrow-layout-only `.ct-section-body` -- the combined
        # selector matches whichever this pane actually rendered, so this case still proves the
        # SAME thing (a real scroll, not a no-op) regardless of which layout mode is current.
        body = app.query_one(f"#{switcher.current} .ct-controls-col, #{switcher.current} .ct-section-body")
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


def _synth_fields_a(state: dict) -> tuple:
    return (TextField(name="dest", label="Destination", shared=True),)


def _synth_fields_b(state: dict) -> tuple:
    return (TextField(name="dest", label="Destination (again)", shared=True),)


def _synthetic_submit(state: dict, answers: dict) -> SectionResult:
    return SectionResult(ok=True)


async def case_7() -> None:
    """SINGLE-EDITABLE-HOME (maintainer round 3, ADR-0019 + the maintainer's own ADR-0002
    citation, "a duplicated mirror/projection of a value is a type error and refused on TUI
    start"): a shared fact renders in EXACTLY ONE owning section -- no read-only reference
    anywhere either (struck entirely, same ruling). 'dest' is owned by Fork/target (the section
    whose whole purpose is choosing it); 'world' is owned by Birth (the section whose whole
    purpose is naming the world being born). Every other declaring section from the prior
    (rejected) draft had its field DROPPED outright -- reads the shared state directly instead."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        # --- (i.5) the library's own owner_of() agrees, checked FIRST (state-independent) ---
        dest_owner = owner_of(app.sections, "dest")
        world_owner = owner_of(app.sections, "world")
        assert dest_owner is not None and str(dest_owner.slug) == "fork-target", \
            f"expected 'dest' owner == fork-target, got {dest_owner}"
        assert world_owner is not None and str(world_owner.slug) == "birth", \
            f"expected 'world' owner == birth, got {world_owner}"
        print(f"case 7a ok: owner_of(sections, 'dest') == {dest_owner.slug!r}, "
              f"owner_of(sections, 'world') == {world_owner.slug!r} -- matches the chosen owners")

        # --- (ii) editing the OWNER propagates to dependent sections' blocked() checks, AND
        # every other declaring section's field is genuinely GONE (checked once each is
        # actually UNBLOCKED and showing its real fields, not merely hidden behind a blocked
        # banner -- a stronger proof than checking while still blocked).
        boundary_icon_before = _tree_icon(app, "boundary")
        assert "⧖" in boundary_icon_before, f"expected boundary BLOCKED before dest/world are set, got {boundary_icon_before!r}"

        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case7-dest"
        await pilot.pause()
        boundary_icon_dest_only = _tree_icon(app, "boundary")
        assert "⧖" in boundary_icon_dest_only, \
            "boundary needs BOTH dest and world -- must still read BLOCKED with only dest set"

        for slug in ("birth", "principals-authority", "signed-genesis", "boundary",
                     "observability", "hydration"):
            await app._panes[slug].refresh_blocked()
        await pilot.pause()

        # Every dest-only-gated section is now genuinely UNBLOCKED, real fields mounted --
        # NOW "dest" has no widget anywhere except Fork/target is a meaningful check.
        for slug in ("birth", "principals-authority", "signed-genesis", "observability", "hydration"):
            assert not app.query(f"#pane-{slug} #ct-field-dest"), \
                f"'dest' must have NO widget in {slug!r} (now UNBLOCKED) -- it is Fork/target's own owned field"
        assert app.query("#pane-fork-target #ct-field-dest"), \
            "'dest' must have its ONE editable widget in Fork/target (the owner)"
        print("case 7b ok: 'dest' renders editable in Fork/target ONLY -- every other section "
              "that needs it (birth/principals-authority/signed-genesis/observability/"
              "hydration), now UNBLOCKED and showing its real fields, has NO 'dest' widget at all")

        tree.select_node(_find_node(tree, "birth"))
        await pilot.pause()
        app.query_one("#pane-birth #ct-field-world", Input).value = "ctjcase7"
        await pilot.pause()
        await app._panes["boundary"].refresh_blocked()
        await pilot.pause()
        boundary_icon_after = _tree_icon(app, "boundary")
        assert "⧖" not in boundary_icon_after, \
            (f"expected boundary to UNBLOCK once Birth's OWN 'world' field is set (no navigation "
             f"to boundary at all), got {boundary_icon_after!r}")
        print(f"case 7c ok: editing dest in its OWNER (Fork/target) then world in ITS owner "
              f"(Birth) propagates live to boundary's own blocked() check -- "
              f"{boundary_icon_before!r} -> {boundary_icon_dest_only!r} -> {boundary_icon_after!r} "
              f"-- boundary itself never selected during either edit")

        # boundary is now genuinely UNBLOCKED too -- confirm its OWN "world" widget is gone.
        assert not app.query("#pane-boundary #ct-field-world"), \
            "'world' must have NO widget in boundary (now UNBLOCKED) -- it is Birth's own owned field"
        assert app.query("#pane-birth #ct-field-world"), \
            "'world' must have its ONE editable widget in Birth (the owner)"
        print("case 7d ok: 'world' renders editable in Birth ONLY -- boundary, now UNBLOCKED and "
              "showing its real fields, has NO 'world' widget at all -- single editable home "
              "for both shared facts, no mirrors, confirmed live")

    # --- (iii) load-time refusal, RED-FIRST: a synthetic double-owner declaration ------------
    synth_a = SectionSpec(slug="synth-a", title="Synth A", group="G", fields=_synth_fields_a,
                           submit=_synthetic_submit)
    synth_b = SectionSpec(slug="synth-b", title="Synth B", group="G", fields=_synth_fields_b,
                           submit=_synthetic_submit)
    synth_commit = CommitSpec(render_summary=lambda s: "", commit=_synthetic_submit)
    try:
        ConfigTreeApp((synth_a, synth_b), synth_commit)
        raise AssertionError("expected DuplicatedSharedFieldError, no exception was raised")
    except DuplicatedSharedFieldError as exc:
        assert "dest" in str(exc) and "synth-a" in str(exc) and "synth-b" in str(exc), \
            f"expected the refusal to name the field and both sections, got: {exc}"
        print(f"case 7e ok (RED-FIRST, load-time refusal): a synthetic double-owner declaration "
              f"of 'dest' across two sections is refused BEFORE any Textual machinery starts "
              f"(construction-time raise, ADR-0002's own highest rung): {exc}")


_MEASURE_CAPPED_SELECTOR = (".ct-field-label, .ct-field-error, .ct-blocked-reason, "
                            ".ct-section-title, #ct-status-line, #ct-banner, .ct-choice-field, "
                            ".ct-section-description, .ct-field-help, .ct-choice-help")


class _UncappedProbe(App):
    """Case 8a's own synthetic RED proof: an ORDINARY `Static`, no cap class at all, holding a
    400-character string -- the exact shape the maintainer's own bug had before this fix, minus
    the autoharn-specific content. Proves the class is real (an uncapped Static DOES render
    unreadably wide on a wide terminal) before case 8b/8c prove the real, capped app does not."""

    def compose(self) -> ComposeResult:
        yield Static("x" * 400, id="uncapped")


async def case_8() -> None:
    """READABLE-MEASURE WIDTH CAP (maintainer round 4: "the principal-registration flow greeted
    him with ONE line of ~348 characters spanning his full tmux width -- unbounded text measure").
    The EMITTING SITE: `steps_principals_authority.py`'s `agent_class`/`relation` fields used to
    splice the WHOLE closed-vocabulary options tuple (value + full descriptive sentence, all four
    entries) into a single field label -- measured 394 and 613 characters respectively (fixed at
    the content layer: converted to real `ChoiceField` pickers with short, value-only option
    labels). The CLASS: any `Static`/`Label` mounted in a container that stretches to its
    parent's width wraps at THAT width, not a readable one -- verified empirically against a
    bare, uncapped `Static` in a 400-column harness (case 8a's own synthetic RED proof below).
    Fixed structurally: `tools.configtree.measure.MEASURE = 78` (matching the deleted
    `tools/setup_tui/elements.py`'s own historical convention) capped via CSS on every TRUE-PROSE
    class (`app.py`'s own CSS docstring has the deliberate exemption list: tabular/pre-formatted
    driver output -- checklist rows, `$ argv` echoes -- is NOT capped, matching the SAME house
    precedent). This fixture drives the REAL app at a 400-column terminal (10x the ceiling) and
    asserts NO capped-class widget anywhere -- across every real section AND the "Add a
    principal" modal specifically -- ever exceeds the measure."""
    # --- 8a. RED-FIRST, synthetic: an UNCAPPED Static at 400 columns reproduces the class ------
    probe = _UncappedProbe()
    async with probe.run_test(size=(400, 20)) as pilot:
        await pilot.pause()
        uncapped = probe.query_one("#uncapped", Static)
        assert uncapped.size.width > MEASURE, \
            (f"expected the RED proof itself to exceed MEASURE ({MEASURE}) when uncapped, got "
             f"width={uncapped.size.width} -- the proof is supposed to demonstrate the class is "
             f"real before showing the fix catches it")
        print(f"case 8a ok (RED-FIRST, synthetic): an UNCAPPED Static holding a 400-character "
              f"string at a 400-column terminal renders {uncapped.size.width} columns wide, one "
              f"line -- reproduces the maintainer's own observed class before any fix is applied")

    # --- 8b. GREEN: the REAL app, at the SAME 400-column width, capped everywhere -------------
    state = _fresh_state()
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(400, 60)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        # Unblock every dest-/world-gated section so its REAL fields (not a blocked banner) are
        # what gets measured below.
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/measure-case8-dest"
        await pilot.pause()
        tree.select_node(_find_node(tree, "birth"))
        await pilot.pause()
        app.query_one("#pane-birth #ct-field-world", Input).value = "measurecase8"
        await pilot.pause()
        for slug in app._panes:
            await app._panes[slug].refresh_blocked()
        await pilot.pause()

        offenders: list[tuple[str, int]] = []
        max_seen = 0
        for slug in app._panes:
            tree.select_node(_find_node(tree, slug))
            await pilot.pause()
            pane = app.query_one(f"#pane-{slug}")
            for w in pane.query(_MEASURE_CAPPED_SELECTOR):
                width = w.size.width
                max_seen = max(max_seen, width)
                if width > MEASURE:
                    offenders.append((f"{slug}#{w.id}", width))
        assert not offenders, f"MEASURE ({MEASURE}) exceeded by: {offenders}"
        print(f"case 8b ok (GREEN): every REAL section's own prose widgets, at a 400-column "
              f"terminal, stay within MEASURE={MEASURE} (widest seen: {max_seen} columns) -- "
              f"swept ALL {len(app._panes)} sections, not just principal registration")

        # --- 8c. The ORIGINAL emitting site specifically: the "Add a principal" modal ---------
        # MASTER-DETAIL RESTRUCTURE (cycle-2 fix round, ADR-0019 Rule 4): "register" is now the
        # MASTER row of a `MasterDetailField` -- its own Add button carries the "-master-add"
        # suffix `widgets_master_detail.MasterDetailFieldWidget` mints (`master_detail.py`'s own
        # module docstring), not the bare "-add" a top-level `ListField` gets.
        tree.select_node(_find_node(tree, "principals-authority"))
        await pilot.pause()
        add_btn = app.query_one("#pane-principals-authority #ct-field-register-master-add")
        await pilot.click(add_btn)
        await pilot.pause()
        modal_offenders = [(str(w.id), w.size.width) for w in
                            app.screen.query(_MEASURE_CAPPED_SELECTOR) if w.size.width > MEASURE]
        assert not modal_offenders, f"MEASURE exceeded in the Add-a-principal modal: {modal_offenders}"
        print(f"case 8c ok (GREEN, the original emitting site): the 'Add a principal' modal's "
              f"'Class' field label -- the exact site that measured 394 characters before this "
              f"fix -- stays within MEASURE={MEASURE} at a 400-column terminal")
        await pilot.press("escape")
        await pilot.pause()

        # --- 8d. Content-level confirmation: the labels themselves are short now --------------
        pa_fields = steps.steps_principals_authority.fields(app.state)
        register_field = next(f for f in pa_fields if str(f.name) == "register")
        agent_class_field = next(f for f in register_field.master.item_fields if str(f.name) == "agent_class")
        assert len(str(agent_class_field.label)) <= MEASURE, \
            f"expected a short label, got {len(str(agent_class_field.label))} chars"
        assert isinstance(agent_class_field, ChoiceField), \
            "expected agent_class to be a real ChoiceField picker, not free text with the vocabulary dumped into its label"
        print(f"case 8d ok: 'agent_class' is now a real ChoiceField (label {str(agent_class_field.label)!r}, "
              f"{len(str(agent_class_field.label))} chars) -- the content-level half of the fix, "
              f"not merely wrapped")


async def case_9() -> None:
    """ELUCIDATION (maintainer round 5, ledger row 1115 -- the round-4 fix DELETED the
    elucidating option descriptions instead of rendering them within measure, malicious
    compliance; the censure this fresh session was dispatched to answer). Proves: a section's
    OWN description renders under its title (`SectionSpec.description`), a `MultiChoiceField`
    option's own elucidation renders juxtaposed under its checkbox (`option_help`), and a
    `ListField`'s own elucidation (the CONSTITUTES/DOES NOT text recovered from
    `principals_authority.toml`'s `[lessons]` table) renders under its own Label -- every one of
    them within MEASURE."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)

        # --- section-level description (signed-genesis: feature_facts' own aspiration/external
        # line, the exact "what our aspirations with it were, relative to existing standards"
        # class the maintainer named) ---
        tree.select_node(_find_node(tree, "signed-genesis"))
        await pilot.pause()
        desc_widgets = list(app.query_one("#pane-signed-genesis").query(".ct-section-description"))
        desc = [str(w.render()) for w in desc_widgets]
        # Round 7 (ledger row 1119): the LEAD is unlabeled connective prose (D7/D8), never a
        # "Aspiration:" telegraphy line -- the first element must NOT be a labeled slot at all.
        assert desc and not desc[0].startswith(("Aspiration:", "Standards:", "Mechanism:", "External:")), \
            f"expected the LEAD to be unlabeled connective prose, not slot:value telegraphy, got {desc[0]!r}"
        assert any(d.startswith("Requires:") for d in desc), \
            f"expected a typed 'Requires:' element for the standing gpg key-custody obligation, got {desc}"
        assert any(d.startswith("Full basis:") for d in desc), \
            f"expected a demoted 'Full basis:' provenance element (the real user-guide FAQ), got {desc}"
        assert len(desc_widgets) >= 2, \
            f"expected the section description to render as SEPARATE typed elements, not one blob -- got {len(desc_widgets)} widget(s)"
        offenders = [(w.id, w.size.width) for w in desc_widgets if w.size.width > MEASURE]
        assert not offenders, f"section description RENDERED width exceeds MEASURE={MEASURE}: {offenders}"
        print(f"case 9a ok: signed-genesis's OWN section description leads with UNLABELED "
              f"connective prose (round 7, ledger row 1119), a 'Requires:' obligation, and a "
              f"demoted 'Full basis:' pointer, within MEASURE (rendered width "
              f"{desc_widgets[0].size.width}): {desc[0][:90]!r}...")

        # --- MultiChoiceField option-level elucidation (hydration: each durable-decision's own
        # 'why' citation, juxtaposed under its own checkbox -- the tooltip-equivalent this
        # terminal offers). Hydration is BLOCKED until a destination exists -- set one first via
        # its OWNER (Fork/target) so its real fields render instead of a blocked banner.
        for grp in tree.root.children:
            for leaf in grp.children:
                if leaf.data and leaf.data.get("slug") == "fork-target":
                    tree.select_node(leaf)
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case9b-dest"
        await pilot.pause()
        await app._panes["hydration"].refresh_blocked()
        tree.select_node(_find_node(tree, "hydration"))
        await pilot.pause()
        pane = app.query_one("#pane-hydration")
        choice_help_widgets = list(pane.query(".ct-choice-help"))
        choice_help_lines = [str(w.render()) for w in choice_help_widgets]
        assert choice_help_lines, "expected at least one per-option elucidation line under the durable-decisions/ADR checkbox groups"
        offenders = [(w.id, w.size.width) for w in choice_help_widgets if w.size.width > MEASURE]
        assert not offenders, f"a per-option elucidation line exceeds MEASURE={MEASURE}: {offenders}"
        print(f"case 9b ok: hydration's durable-decision/ADR checkboxes each carry their own "
              f"elucidation line, within MEASURE -- {len(choice_help_lines)} line(s), e.g. "
              f"{choice_help_lines[0][:90]!r}...")

        # --- ListField-level elucidation, recovered from principals_authority.toml's [lessons]
        # table (CONSTITUTES/DOES NOT text) -- was in the data all along, never previously
        # surfaced in the UI ---
        for grp in tree.root.children:
            for leaf in grp.children:
                if leaf.data and leaf.data.get("slug") == "fork-target":
                    tree.select_node(leaf)
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case9-dest"
        await pilot.pause()
        await app._panes["principals-authority"].refresh_blocked()
        tree.select_node(_find_node(tree, "principals-authority"))
        await pilot.pause()
        pa_pane = app.query_one("#pane-principals-authority")
        help_widgets = list(pa_pane.query(".ct-field-help"))
        help_lines = [str(w.render()) for w in help_widgets]
        assert any(ln.startswith("Constitutes:") for ln in help_lines), \
            f"expected the register ListField's own typed 'Constitutes:' element, got {help_lines}"
        assert any(ln.startswith("Does not:") for ln in help_lines), \
            f"expected the register ListField's own typed 'Does not:' element, got {help_lines}"
        offenders = [(w.id, w.size.width) for w in help_widgets if w.size.width > MEASURE]
        assert not offenders, f"a ListField's own help line exceeds MEASURE={MEASURE}: {offenders}"
        print(f"case 9c ok: principals-authority's 'Principal' master list carries its own "
              f"CONSTITUTES/DOES NOT elucidation (principals_authority.toml's own [lessons] "
              f"table), within MEASURE, with zero principals registered yet")

        # SELECTION (cycle-3 fix round, ledger row 1136): a dependent list's OWN elucidation
        # (competence/relation/charter) only renders for the currently SELECTED master row (this
        # fix round's own "the master list is buried under repeated preamble" remediation) --
        # register one, select it, and confirm all THREE dependents' own Constitutes/Does not
        # elements are now ALSO present, not merely the master's.
        await _pa_add_row(pilot, app, pa_pane, "ct-field-register-master-add",
                    {"name": "ctj-case9c", "purpose": "case 9c own selection probe"})
        await pilot.pause()
        selected_help_lines = [str(w.render()) for w in pa_pane.query(".ct-field-help")]
        constitutes_count = sum(1 for ln in selected_help_lines if ln.startswith("Constitutes:"))
        does_not_count = sum(1 for ln in selected_help_lines if ln.startswith("Does not:"))
        assert constitutes_count >= 4, \
            (f"expected 4 'Constitutes:' elements (register + its 3 auto-selected dependents) "
             f"once a principal is registered (auto-selected on add), got {constitutes_count}: {selected_help_lines}")
        assert does_not_count >= 4, \
            f"expected 4 'Does not:' elements the same way, got {does_not_count}: {selected_help_lines}"
        print(f"case 9c-selected ok: registering (and auto-selecting) a principal reveals all "
              f"THREE dependents' own CONSTITUTES/DOES NOT elucidation too ({constitutes_count} "
              f"'Constitutes:'/{does_not_count} 'Does not:' elements total) -- 'Principal'/"
              f"'Competence'/'Relation'/'Role charter' each carry their own")


async def _pa_add_row(pilot, app, pane, add_id: str, values: dict, *,
                       radio_index_by_field: "dict | None" = None) -> None:
    """Presses a master-detail Add button (`.press()`, not `pilot.click` -- these buttons can sit
    deep inside a nested, scrolled block; `Button.press()` posts the identical `Pressed` message
    a real click does, without needing screen coordinates to be in view, the same idiom this
    fixture already uses for `finish_btn.press()`), fills the opened modal's fields, and saves.
    `radio_index_by_field` -- `{field_name: option_index}` for any `ChoiceField` in the modal
    (defaults to index 0, i.e. the first option, for every ChoiceField not named)."""
    pane.query_one(f"#{add_id}", Button).press()
    await pilot.pause()
    modal = app.screen
    for name, val in values.items():
        modal.query_one(f"#ct-field-{name}", Input).value = val
        await pilot.pause()
    for rs in modal.query(RadioSet):
        fname = str(rs.id or "").removeprefix("ct-field-")
        idx = (radio_index_by_field or {}).get(fname, 0)
        rs.children[idx].value = True
        await pilot.pause()
    modal.query_one("#ct-modal-save", Button).press()
    await pilot.pause()


async def _pa_select_row(pilot, pane, idx: int) -> None:
    """Selects master row `idx` (cycle-3 fix round, ledger row 1136's own selection fix,
    `widgets_master_detail.MasterDetailFieldWidget`'s own docstring, "SELECTION") -- `.press()`,
    matching `_pa_add_row`'s own idiom (a real click's identical `Pressed` message, no screen-
    coordinate dependency)."""
    pane.query_one(f"#ct-field-register-master-select-{idx}", Button).press()
    await pilot.pause()


async def case_10() -> None:
    """PRINCIPAL REFERENCES ARE SELECTIONS + MASTER-DETAIL NESTING (ADR-0019 Rule 4, cycle-2 fix
    round; supersedes maintainer round 5's ledger row 1115 defect B, still true under the new
    shape). SELECTION (cycle-3 fix round, ledger row 1136): the maintainer's own live bench
    sighting -- "add a principal -> can't select it" -- was reproduced (the pre-fix master row
    was a bare, unfocusable `Static`, genuinely unclickable) and fixed: each master row is now a
    real, focusable `Button`; clicking one selects it, and ONLY the selected row's own dependent
    lists (competence/relation/charter) render -- never all rows' own simultaneously, which was
    the OTHER half of the same live complaint ("the master list is buried... looks ugly that you
    have to scroll," relayed by the coordinator: every unselected row used to cost a full
    label+help+Add-button block per dependent, always, whether or not the operator cared).
    Proves, against the REAL registry:
      (a) the four-parallel-flat-lists shape is GONE -- no top-level Competence/Relation/Charter
          Add button exists anywhere in this section (the audit's own named assertion);
      (b) adding a master row auto-selects it, and a competence added while A is selected renders
          in the (one, shared) detail area -- but SWITCHING selection to B shows a CLEAN detail
          area, never A's own competence leaking through -- the master-detail isolation the whole
          restructure exists for, now expressed through selection rather than simultaneous blocks;
      (c) a relation's own 'object' picker is still fed LIVE from the register list's current
          rows (the ORIGINAL defect-B fix, preserved) -- and the relation itself, added while A
          (the subject) is selected, is visible under A's own selection and genuinely ABSENT once
          B (the object) is selected instead (Rule 3, now via selection-switch);
      (d) removing the CURRENTLY SELECTED master row (a principal) clears the selection AND
          cascades: its own dependent rows are dropped with it, never left behind as a
          commit-time-only surprise, and never resurface under the remaining row either.
    """
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 400)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case10-dest"
        await pilot.pause()
        await app._panes["principals-authority"].refresh_blocked()
        tree.select_node(_find_node(tree, "principals-authority"))
        await pilot.pause()
        pane = app.query_one("#pane-principals-authority")

        # --- (a) no top-level Competence/Relation/Charter Add button anywhere -----------------
        stale_flat_ids = [str(b.id) for b in pane.query(Button)
                          if str(b.id or "") in ("ct-field-competences-add",
                                                  "ct-field-relations-add", "ct-field-charters-add")]
        assert not stale_flat_ids, \
            f"the four-parallel-flat-lists shape is back: {stale_flat_ids}"
        add_ids = [str(b.id) for b in pane.query(Button) if "-add" in str(b.id or "")]
        assert add_ids == ["ct-field-register-master-add"], \
            (f"expected EXACTLY ONE top-level Add button (the master's own, 'Principal') before "
             f"any principal is registered -- every dependent's own Add button only exists "
             f"nested inside a SELECTED registered principal's own detail area -- got {add_ids}")
        print(f"case 10a ok (ADR-0019 Rule 4): the four-parallel-flat-lists shape is gone -- the "
              f"ONLY top-level Add button in this section is {add_ids[0]!r} (the master, "
              f"'Principal'); no top-level Competence/Relation/Charter Add button exists")

        # --- register TWO principals: A ('ctj-a') and B ('ctj-b') ------------------------------
        await _pa_add_row(pilot, app, pane, "ct-field-register-master-add",
                    {"name": "ctj-a", "purpose": "witnessing case 10, principal A"})
        await pilot.pause()
        await _pa_add_row(pilot, app, pane, "ct-field-register-master-add",
                    {"name": "ctj-b", "purpose": "witnessing case 10, principal B"})
        await pilot.pause()

        # Adding B auto-selected it (this fix round's own "SELECTION" note) -- exactly B's own 3
        # dependent Add buttons exist right now, never A's and B's simultaneously.
        detail_add_ids = sorted(str(b.id) for b in pane.query(Button) if "-detail-add-" in str(b.id or ""))
        assert detail_add_ids == [
            "ct-field-register-detail-add-charters", "ct-field-register-detail-add-competences",
            "ct-field-register-detail-add-relations",
        ], f"expected exactly the SELECTED row's own 3 dependent Add buttons, got {detail_add_ids}"
        select_labels = {str(b.label): "-selected" in (b.classes or ())
                         for b in pane.query(".ct-md-row-select")}
        assert select_labels.get("> ctj-b (human): witnessing case 10, principal B") is True, \
            f"expected B (just added) to be auto-selected, got {select_labels}"
        print(f"case 10b ok (SELECTION, cycle-3 fix round): registering two principals (A, B) "
              f"auto-selects B; its own nested Competence/Relation/Role-charter Add buttons "
              f"({len(detail_add_ids)} total) are the ONLY ones visible -- A's own are not "
              f"simultaneously rendered, closing the 'buried under repeated preamble' complaint")

        # --- (b) switch selection to A, add a competence -- it must NOT leak once B is reselected
        await _pa_select_row(pilot, pane, 0)
        await _pa_add_row(pilot, app, pane, "ct-field-register-detail-add-competences",
                    {"activity": "witness-activity", "band": "witness-band", "basis": "witness-basis"})
        await pilot.pause()
        lines_while_a = [str(w.render()) for w in pane.query(".ct-info-line")]
        assert any("witness-activity" in ln for ln in lines_while_a), \
            f"expected the competence added while A was selected to render in the (one) detail area, got {lines_while_a}"
        await _pa_select_row(pilot, pane, 1)
        lines_while_b = [str(w.render()) for w in pane.query(".ct-info-line")]
        assert not any("witness-activity" in ln for ln in lines_while_b), \
            (f"MASTER-DETAIL ISOLATION BUG: a competence added while PRINCIPAL A was selected "
             f"leaked into PRINCIPAL B's own detail area once B was selected: {lines_while_b}")
        print(f"case 10c ok (master-detail isolation, the restructure's own point, now expressed "
              f"through selection): a competence added while A was selected ({lines_while_a}) "
              f"never appears once B is selected instead ({lines_while_b})")

        # --- (c) 'object' picker still fed live from register; relation visible under SUBJECT's
        # own selection only (Rule 3) ---
        await _pa_select_row(pilot, pane, 0)  # back to A (the intended subject)
        await _pa_add_row(pilot, app, pane, "ct-field-register-detail-add-relations",
                    {}, radio_index_by_field={"relation": 0, "object": 1})  # object index 1 == "ctj-b"
        await pilot.pause()
        lines_a2 = [str(w.render()) for w in pane.query(".ct-info-line")]
        assert any("ctj-b" in ln for ln in lines_a2), \
            f"expected the relation ('ctj-a acts-for ctj-b') visible while SUBJECT ctj-a is selected, got {lines_a2}"
        await _pa_select_row(pilot, pane, 1)  # switch to B (the object)
        lines_b2 = [str(w.render()) for w in pane.query(".ct-info-line")]
        assert not any(ln for ln in lines_b2 if any(rel in ln for rel in
                       ("acts-for", "dispatched-by", "same-natural-person", "succeeds"))), \
            (f"RULE 3 VIOLATION: the SAME relation also rendered under its OBJECT principal's "
             f"own selection (a duplicated projection of one fact) -- {lines_b2}")
        print(f"case 10d ok (ADR-0019 Rule 3, 'one home per fact extends to the screen', now via "
              f"selection-switch): the relation is visible under its SUBJECT (ctj-a)'s own "
              f"selection -- {lines_a2} -- and genuinely absent once its OBJECT (ctj-b) is "
              f"selected instead: {lines_b2}")

        # --- (d) removing the CURRENTLY SELECTED master row (A) clears selection AND cascades --
        # C10 GATE (cycle-5 audit finding #1): A carries a competence AND a relation, so removing
        # it now pushes `ConfirmModal` first (`widgets_master_detail._remove_master`'s own
        # docstring) -- press its own "Remove" confirm button, matching a real operator's second
        # click, before the cascade actually runs.
        await _pa_select_row(pilot, pane, 0)
        pane.query_one("#ct-field-register-master-remove-0", Button).press()
        await pilot.pause()
        app.screen.query_one("#ct-confirm-yes", Button).press()
        await pilot.pause()
        remaining_selects = list(pane.query(".ct-md-row-select"))
        assert len(remaining_selects) == 1, \
            f"expected exactly 1 principal row after removing A, got {len(remaining_selects)}"
        placeholder = [str(w.render()) for w in pane.query(".ct-md-empty")]
        assert any("select a principal" in p for p in placeholder), \
            f"expected removing the SELECTED row to clear selection (a 'select a principal above' hint), got {placeholder}"
        await _pa_select_row(pilot, pane, 0)  # select the sole remaining row (B)
        remaining_lines = [str(w.render()) for w in pane.query(".ct-info-line")]
        assert not any("witness-activity" in ln for ln in remaining_lines), \
            f"CASCADE BUG: A's own competence survived A's own removal (visible under B): {remaining_lines}"
        assert not any("ctj-b" in ln and "acts-for" in ln for ln in remaining_lines), \
            f"CASCADE BUG: A's own relation survived A's own removal (visible under B): {remaining_lines}"
        print(f"case 10e ok (cascade on master removal + selection clears with it): removing the "
              f"SELECTED principal A drops A's OWN competence and relation with it -- never left "
              f"as an orphan for commit time to discover as a confusing failure, and never "
              f"resurfaces once the remaining principal (B) is selected; remaining row: "
              f"{[str(w.render()) for w in remaining_selects]}")


async def case_11() -> None:
    """CONFIG LOADING IS DISCOVERABLE + RECORDS STOP LYING (maintainer round 5, ledger row 1115,
    defect C). (i) 'Load a configuration' is a real, reachable tree node from app start, offering
    the known-good template and a custom path -- applying it seeds every OTHER section's own live
    default immediately. (ii) an untouched default is NEVER recorded as 'operator declined' --
    DECLINED (touched, said no) vs DEFAULTED (never touched) are two distinct, honest checklist
    statuses."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "load-config"))
        await pilot.pause()
        rs = app.query_one("#pane-action-load-config #ct-field-template", RadioSet)
        idx = next(i for i, b in enumerate(rs.children) if "known-good-blank" in str(b.label))
        await pilot.click(rs.children[idx])
        await pilot.pause()
        await pilot.click(app.query_one("#pane-action-load-config #ct-action-apply", Button))
        await pilot.pause()

        tree.select_node(_find_node(tree, "substrate"))
        await pilot.pause()
        substrate_run = app.query_one("#pane-substrate #ct-field-run", Checkbox)
        assert substrate_run.value is True, \
            f"expected the loaded template's own substrate.run=true to seed the live checkbox, got {substrate_run.value}"
        print("case 11a ok: 'Load a configuration' is a real tree node, reachable and usable at "
              "app start -- loading bootstrap/templates/known-good-blank.toml seeds substrate's "
              "own 'run' checkbox to True immediately, no re-launch, no --initial-config flag")

        # --- record-wording: DECLINED (touched) vs DEFAULTED (never touched), same field kind,
        # same section, same false value -- only the touch history differs.
        state_touched: dict = _fresh_state()
        state_touched["dest"] = "/tmp/ctj-case11-dest"
        state_touched["dest_would_exist"] = True
        cb_field = next(f for f in steps.steps_observability.fields(state_touched) if str(f.name) == "otelcol")
        set_field_value(state_touched, NodeId("observability"), cb_field, False)  # a real, deliberate touch
        result_touched = steps.steps_observability.submit(state_touched, {"run": True, "otelcol": False, "otel_watch": False})
        rows_touched = {(it.screen, it.item): it.status for it in state_touched["_checklist"].items}
        assert rows_touched[("observability", "otelcol selected")] == ck.DECLINED, \
            f"expected DECLINED for a TOUCHED false value, got {rows_touched}"
        print("case 11b ok (RED-class distinguished): a TOUCHED-but-false otelcol selection "
              "records DECLINED -- 'operator declined', an honest attribution of an actual choice")

        state_default: dict = _fresh_state()
        state_default["dest"] = "/tmp/ctj-case11-dest"
        state_default["dest_would_exist"] = True
        result_default = steps.steps_observability.submit(state_default, {"run": True, "otelcol": False, "otel_watch": False})
        rows_default = {(it.screen, it.item): it.status for it in state_default["_checklist"].items}
        assert rows_default[("observability", "otelcol selected")] == ck.DEFAULTED, \
            (f"FALSE-ATTRIBUTION BUG (maintainer round 5, ledger row 1115): an UNTOUCHED "
             f"checkbox recorded as {rows_default[('observability', 'otelcol selected')]!r}, "
             f"expected DEFAULTED -- 'the operator never touched this', not a claimed decision")
        print("case 11c ok (the false-attribution bug itself, now impossible): the IDENTICAL "
              "false value, NEVER touched, records DEFAULTED -- never 'operator declined' for a "
              "default nobody looked at")
        assert result_touched.ok and result_default.ok


async def case_12() -> None:
    """ONE FACT, ONE RECORD AT COMMIT (maintainer round 5, ledger row 1115, defect D): a
    commit-sweep validation must never re-probe a TRANSITIONAL, pre-act disk state for a fact
    THIS SAME commit's own earlier act (birth) will make true -- `dest_would_exist` is now
    consulted FIRST and trusted outright, never re-checked against physical disk state that a
    same-session birth has simply not written yet. RED-FIRST: the OLD ordering (physical
    `os.path.isdir` checked BEFORE `dest_would_exist`) is replicated verbatim below and shown to
    misfire on a REAL, realistic transitional state (a destination directory that already exists
    -- e.g. fork-copy's own `cp -a` already ran -- but whose scaffold-written keys/+verify-
    commission+legacy/led do not exist YET, because birth's own scaffold act has not run this
    commit). GREEN: the CURRENT `steps_signed_genesis.submit` gets the SAME state right, and
    records EXACTLY ONE disposition for the 'world has keys/+...' item, never two.
    Also proves the 'screen 7' sequential-era ghost wording is gone."""
    dest = tempfile.mkdtemp(prefix="ctj-case12-dest-")
    try:
        state = _fresh_state()
        state["dest"] = dest
        state["dest_would_exist"] = True  # birth is queued THIS SAME commit, earlier in registry order

        # --- RED: the OLD branch order (verbatim replica of the pre-fix shape) ---
        def _old_would_refuse(dest: str, dest_would_exist: bool) -> "str | None":
            if not os.path.isdir(dest):
                return None if dest_would_exist else "REFUSED: not a directory"
            missing = [n for n, ok in (
                ("keys/", os.path.isdir(os.path.join(dest, "keys"))),
                ("verify-commission", os.path.isfile(os.path.join(dest, "verify-commission"))),
                ("legacy/led", os.path.isfile(os.path.join(dest, "legacy", "led")))) if not ok]
            return f"REFUSED: missing {missing} -- not a scaffolded world" if missing else None

        old_verdict = _old_would_refuse(dest, True)
        assert old_verdict is not None, \
            "expected the OLD ordering to WRONGLY refuse a real, transitional pre-birth directory"
        print(f"case 12a ok (RED, reproduced): the OLD check-physical-state-first ordering "
              f"refuses a real transitional directory even though this SAME commit's own birth "
              f"act (dest_would_exist=True) has not run yet: {old_verdict!r}")

        # --- GREEN: the CURRENT code, same transitional state, same dest_would_exist=True ---
        answers = {"run": True, "statement": "case 12 witness", "use_scratch_identity": True,
                   "name": "", "email": "", "gnupghome": ""}
        result = steps.steps_signed_genesis.submit(state, answers)
        cl = state["_checklist"]
        matching = [it for it in cl.items if it.item == "world has keys/+verify-commission+legacy/led"]
        assert len(matching) == 1, \
            f"expected EXACTLY ONE disposition row for this item, got {len(matching)}: {matching}"
        assert matching[0].status == ck.DRY_SKIPPED, \
            f"expected the CURRENT ordering to TRUST dest_would_exist and skip the stale probe, got {matching[0].status}"
        assert "screen 7" not in " ".join(str(v) for it in cl.items for v in (it.item, it.detail)), \
            "the sequential-era 'screen 7' ghost text must be gone from a tree UI"
        print(f"case 12b ok (GREEN, single disposition): the CURRENT ordering trusts "
              f"dest_would_exist FIRST -- exactly ONE row for this item "
              f"({matching[0].status}), no 'screen 7' ghost text anywhere in the checklist")

        # --- run=False path: ALSO exactly one disposition, and the SAME item-name discipline.
        # Called directly (no widget write-through, matching a --from-config-style invocation --
        # `is_field_touched` therefore reads False, so the honest record is DEFAULTED here, not
        # DECLINED; case 11b/11c already prove the widget-driven, TOUCHED case reads DECLINED).
        state2 = _fresh_state()
        result2 = steps.steps_signed_genesis.submit(state2, {"run": False, "statement": "", "use_scratch_identity": False, "name": "", "email": "", "gnupghome": ""})
        cl2 = state2["_checklist"]
        ceremony_rows = [it for it in cl2.items if it.item == "ceremony"]
        assert len(ceremony_rows) == 1, f"expected exactly one 'ceremony' row, got {ceremony_rows}"
        assert ceremony_rows[0].status == ck.DEFAULTED, \
            f"expected DEFAULTED (no widget write-through in this call -- untouched), got {ceremony_rows[0].status}"
        assert result2.ok
        print(f"case 12c ok: the run=False path ALSO yields exactly ONE disposition row "
              f"('ceremony', {ceremony_rows[0].status}), never a second contradicting one")
    finally:
        shutil.rmtree(dest, ignore_errors=True)


async def case_13() -> None:
    """BIND SUSPEND (maintainer round 5, ledger row 1115): ctrl+z is bound to Textual's own
    `action_suspend_process` (verified empirically against the installed Textual version --
    `App.action_suspend_process` exists and sends SIGTSTP on a suspend-capable driver), shown in
    the Footer. Witnesses what a headless harness honestly can: the binding is present and
    invocable. The live-terminal leg (does the terminal ACTUALLY suspend/resume) is UNEXERCISED
    here -- named in the report, with the exact command for the maintainer to try."""
    calls = []
    orig = App.action_suspend_process

    def _patched(self):
        calls.append(True)
        return orig(self)

    App.action_suspend_process = _patched
    try:
        app = tui_app.build_app(_fresh_state(), dry_run=True)
        async with app.run_test(size=(150, 55)) as pilot:
            await pilot.pause()
            bound = any(str(getattr(b, "key", "")) == "ctrl+z" for b in ConfigTreeApp.BINDINGS)
            assert bound, "expected an explicit ctrl+z binding on ConfigTreeApp.BINDINGS"
            await pilot.press("ctrl+z")
            await pilot.pause()
            assert calls, "expected ctrl+z to invoke action_suspend_process"
            print("case 13 ok: ctrl+z is bound and invokes App.action_suspend_process "
                  "(headless-safe -- a non-suspend-capable driver is Textual's own documented "
                  "no-op, never a crash). UNEXERCISED: the live-terminal leg -- an operator "
                  "should run 'python3 -m tools.setup_tui' in a REAL terminal, press ctrl+z, and "
                  "confirm the shell job actually suspends (fg to resume).")
    finally:
        App.action_suspend_process = orig


async def case_14() -> None:
    """ROUND 6 (ledger row 1117, companion rule C13): the ELUCIDATION AREA itself renders no
    bare ' | ' anywhere -- a real sweep of the LIVE app's own rendered elucidation widgets, not
    just the data file -- and the content-loader refuses a synthetic delimiter-flattened string
    RED-FIRST, at load, before it ever reaches a widget."""
    # --- (a) RED-FIRST: the loader refuses a synthetic piped string, naming the key ---
    try:
        content._forbid_pipe_delimiter(
            {"fact": [{"key": "x", "aspiration": "a | b", "external": "none"}]},
            path="synthetic.toml")
        raise AssertionError("expected the loader to refuse a synthetic ' | ' delimiter")
    except content.ContentError as exc:
        assert "synthetic.toml" in str(exc) and "aspiration" in str(exc), \
            f"expected the refusal to NAME the offending file/key, got: {exc}"
        print(f"case 14a ok (RED-FIRST, loader refusal): a synthetic piped string is refused at "
              f"load, naming the file and key: {exc}")

    # --- (b) GREEN: the REAL, currently-loaded data files carry no bare ' | ' at all (the fix
    # that answers ledger row 1117's own specimen -- feature_facts.toml's aspiration/external,
    # durable_decisions.toml's why, principals_authority.toml's lessons) ---
    for _mod_name, _table in (("feature_facts", content.FEATURE_FACTS),
                               ("durable_decisions", content.DURABLE_DECISIONS)):
        for _row in _table:
            for _k, _v in _row.items():
                if isinstance(_v, str):
                    assert " | " not in _v, f"{_mod_name} row {_row.get('key') or _row.get('slug')}.{_k} still carries a bare ' | ': {_v!r}"
    print("case 14b ok: the REAL feature_facts.toml/durable_decisions.toml carry zero bare ' | ' "
          "delimiters -- the loader's own refusal is exercised on every real load, not just a "
          "synthetic probe")

    # --- (c) GREEN, LIVE: sweep every rendered elucidation widget in the REAL running app for a
    # bare pipe, and confirm components render as SEPARATE labeled elements (never one blob) ---
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        # Unblock dest-gated sections so their real elucidation renders.
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case14-dest"
        await pilot.pause()
        for slug in app._panes:
            await app._panes[slug].refresh_blocked()
        await pilot.pause()

        pipe_offenders: list[str] = []
        elucidation_selector = ".ct-section-description, .ct-field-help, .ct-choice-help"
        section_element_counts: dict[str, int] = {}
        for slug in app._panes:
            tree.select_node(_find_node(tree, slug))
            await pilot.pause()
            pane = app.query_one(f"#pane-{slug}")
            widgets = list(pane.query(elucidation_selector))
            section_element_counts[slug] = len(widgets)
            for w in widgets:
                text = str(w.render())
                if " | " in text:
                    pipe_offenders.append(f"{slug}#{w.id}: {text!r}")
        assert not pipe_offenders, f"bare ' | ' found in LIVE elucidation rendering: {pipe_offenders}"
        print(f"case 14c ok (GREEN, live): swept EVERY section's own rendered elucidation "
              f"widgets ({elucidation_selector}) across all {len(app._panes)} sections -- zero "
              f"bare ' | ' separators anywhere; per-section element counts: "
              f"{section_element_counts}")


async def case_15() -> None:
    """ADR-ADOPTION SYNOPSES (round-6 addendum, maintainer's own verdict: "helpful only to
    someone who already knows every ADR ... a pointer is not an elucidation ... fails the
    named-consumer test"). Proves: each adoptable ADR renders a non-empty Synopsis element that
    is NOT the file-path pointer, and the pointer renders AFTER it, never replacing it."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case15-dest"
        await pilot.pause()
        await app._panes["hydration"].refresh_blocked()
        tree.select_node(_find_node(tree, "hydration"))
        await pilot.pause()
        pane = app.query_one("#pane-hydration")
        choice_lines = [str(w.render()) for w in pane.query(".ct-choice-help")]

        synopsis_lines = [ln for ln in choice_lines if ln.startswith("Synopsis:")]
        pointer_lines = [ln for ln in choice_lines if ln.startswith("File:")]
        assert synopsis_lines, f"expected at least one ADR entry's own Synopsis element, got sample: {choice_lines[:5]}"
        assert pointer_lines, "expected at least one ADR entry's own File pointer element"
        for syn in synopsis_lines:
            assert not syn.startswith("File:"), f"a Synopsis line must not double as the pointer line: {syn!r}"
        pending = [ln for ln in synopsis_lines if "synopsis pending maintainer review" in ln]
        authored = [ln for ln in synopsis_lines if "synopsis pending maintainer review" not in ln]
        assert authored, f"expected at least one REAL, non-pending ADR synopsis, got only: {synopsis_lines}"
        print(f"case 15a ok: {len(authored)} ADR entries render a real, authored synopsis "
              f"(distinct from the pointer line); {len(pending)} named as pending maintainer "
              f"review (never fabricated) -- e.g. {authored[0][:100]!r}...")

        # Ordering: for the SAME ADR option, the synopsis widget mounts BEFORE the file-pointer
        # widget (synopsis first, pointer follows, per the coordinator's own instruction) --
        # checked pairwise by list POSITION (each option's own Synopsis/File pair is adjacent,
        # in that order, in the widget-mount stream).
        all_help_widgets = list(pane.query(".ct-choice-help"))
        rendered = [str(w.render()) for w in all_help_widgets]
        checked = 0
        for i, text in enumerate(rendered):
            if text.startswith("Synopsis:") and i + 1 < len(rendered):
                assert rendered[i + 1].startswith("File:"), \
                    f"expected the Synopsis element to be immediately followed by its own File pointer, got: {text!r} then {rendered[i+1]!r}"
                checked += 1
        assert checked > 0, "expected at least one matched synopsis/pointer pair to check ordering on"
        print(f"case 15b ok: synopsis renders BEFORE its own file-path pointer for every matched "
              f"ADR entry checked ({checked} pair(s)) -- the pointer follows the synopsis, "
              f"never replaces it")

        # content.ADR_SYNOPSES sanity: authored for every ADR list_adrs() currently returns,
        # named-pending for none silently missing.
        adrs = durable_decisions.list_adrs()
        missing_synopsis = [n for n, _, _ in adrs if n not in content.ADR_SYNOPSES]
        print(f"case 15c ok: {len(adrs)} adoptable ADR(s) known; {len(missing_synopsis)} have no "
              f"authored synopsis entry at all (render as the honest pending marker): {missing_synopsis}")


async def case_16() -> None:
    """CHECKBOX CHROME (round-6 addendum, point 4): a bare Checkbox's own default CSS draws
    `border: tall` -- a full top+bottom rule around EVERY option, a wall of borders once a
    catalog runs to a dozen-plus entries. Proves the `.ct-checkbox-compact` class (no border) is
    actually applied to every MultiChoiceField option, at a normal terminal size."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case16-dest"
        await pilot.pause()
        await app._panes["hydration"].refresh_blocked()
        tree.select_node(_find_node(tree, "hydration"))
        await pilot.pause()
        pane = app.query_one("#pane-hydration")
        # Only the MultiChoiceField's OWN option checkboxes (id contains "-opt-") are in scope --
        # an ordinary standalone ConfirmField checkbox (e.g. "Run hydration now?") was never the
        # "wall of borders" complaint (that is specifically a STACKED catalog of many options).
        boxes = [cb for cb in pane.query(Checkbox) if "-opt-" in str(cb.id or "")]
        assert boxes, "expected at least one MultiChoiceField option Checkbox in hydration"
        bordered = [str(cb.id) for cb in boxes if str(cb.styles.border.top[0]) not in ("", "none")]
        assert not bordered, f"expected NO per-option border (Qt-idiom checklist, not a boxed control per row), still bordered: {bordered}"
        print(f"case 16 ok: all {len(boxes)} checkbox options in hydration's MultiChoiceField "
              f"groups render with NO per-option border ('.ct-checkbox-compact') -- no wall of "
              f"borders even with a durable-decisions catalog this size")


_ALL_ELUCIDATION_SELECTOR = (".ct-section-description, .ct-field-help, .ct-choice-help, "
                             ".ct-elucidation-heading")

_INTERNAL_MEMORY_RE = re.compile(r"\bs\d\d(?:/s\d\d)*-family\b", re.IGNORECASE)


async def _sweep_all_elucidation_text(app, pilot) -> "list[str]":
    """Visits every section (unblocking dest-gated ones first) and returns every rendered
    elucidation-class Static's own text, across the whole app -- the shared sweep round 7's own
    cases 17-19 all build on."""
    tree = app.query_one("#ct-tree", Tree)
    tree.select_node(_find_node(tree, "fork-target"))
    await pilot.pause()
    app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case17-dest"
    await pilot.pause()
    for slug in app._panes:
        await app._panes[slug].refresh_blocked()
    await pilot.pause()
    texts: list[str] = []
    for slug in app._panes:
        tree.select_node(_find_node(tree, slug))
        await pilot.pause()
        pane = app.query_one(f"#pane-{slug}")
        texts.extend(str(w.render()) for w in pane.query(_ALL_ELUCIDATION_SELECTOR))
    return texts


async def case_17() -> None:
    """PLACEHOLDER TOKENS (round 7, ledger row 1119, defect D3: "<dest>/legacy/led" reached the
    screen literally -- a raw, unexpanded template variable). RED-FIRST: construction of a
    DescriptionElement/ElucidationHeading/plain-string elucidation value carrying a raw
    `<placeholder>` token is refused, naming the token. GREEN: the REAL, currently-authored
    feature_facts.toml carries none (the two literal `<dest>/...` occurrences the round-6
    content had are fixed, generic phrasing now)."""
    # --- (a) RED-FIRST: a bare string ---
    try:
        SectionSpec(slug="synth-ph", title="Synthetic", group="Synthetic",
                    fields=lambda state: (), submit=lambda state, answers: SectionResult(ok=True),
                    description="drives this world's own <dest>/legacy/led")
        raise AssertionError("expected construction to refuse a raw <placeholder> token")
    except ValueError as exc:
        assert "<dest>" in str(exc) and "placeholder" in str(exc), \
            f"expected the refusal to NAME the offending token, got: {exc}"
        print(f"case 17a ok (RED-FIRST): a bare-string SectionSpec.description carrying "
              f"'<dest>' is refused at construction, naming the token: {exc}")

    # --- (b) RED-FIRST: inside a DescriptionElement ---
    try:
        DescriptionElement("Requires", "run <dest>/verify-commission by hand")
        raise AssertionError("expected DescriptionElement to refuse a raw <placeholder> token")
    except ValueError as exc:
        assert "<dest>" in str(exc)
        print(f"case 17b ok (RED-FIRST): a DescriptionElement carrying '<dest>' is refused at "
              f"construction: {exc}")

    # --- (c) RED-FIRST: inside an ElucidationHeading ---
    try:
        ElucidationHeading("<dest> path")
        raise AssertionError("expected ElucidationHeading to refuse a raw <placeholder> token")
    except ValueError as exc:
        assert "<dest>" in str(exc)
        print(f"case 17c ok (RED-FIRST): an ElucidationHeading carrying '<dest>' is refused at "
              f"construction: {exc}")

    # --- (d) GREEN: the REAL app's own rendered elucidation carries no raw placeholder anywhere
    # (the two literal <dest>/... occurrences round 6's own feature_facts.toml had -- the
    # principals_authority and hydration_role_charters "external" lines -- are fixed) ---
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        texts = await _sweep_all_elucidation_text(app, pilot)
        offenders = [t for t in texts if re.search(r"<[A-Za-z_][A-Za-z0-9_-]*>", t)]
        assert not offenders, f"a raw <placeholder> token reached the REAL rendered elucidation: {offenders}"
        print(f"case 17d ok (GREEN, live): swept {len(texts)} rendered elucidation line(s) "
              f"across every section -- zero raw <placeholder> tokens anywhere")


async def case_18() -> None:
    """NULL-SLOT SUPPRESSION (round 7, ledger row 1119, defect D6: "Aspiration: none named."
    rendered a null as if it were content -- "either suppress the slot or say something the
    reader can use"). Proves NO rendered elucidation line anywhere is a bare null-shaped
    statement ("none named", "none.", "(no operator-facing content)") -- an empty component is
    simply ABSENT, never printed as prose."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        texts = await _sweep_all_elucidation_text(app, pilot)
        null_shaped = [t for t in texts if re.search(r"\bnone\b", t, re.IGNORECASE) and len(t) < 40]
        assert not null_shaped, f"a null-shaped line reached the REAL rendered elucidation (D6): {null_shaped}"
        print(f"case 18 ok: swept {len(texts)} rendered elucidation line(s) across every "
              f"section -- zero bare null-shaped statements ('none named.', 'none.') anywhere; "
              f"an empty component is simply absent")


async def case_19() -> None:
    """AUDIENCE BOUNDARY (round 7, ledger row 1119, defect D2: an AI-collaborator's own internal
    memory note, an insider codename ("the omega-lab shape"), and internal delta/session
    numbering ("the s40/s41 family") all reached the operator-facing screen verbatim). Proves
    NONE of these three specific strings -- named explicitly by the coordinator's own brief --
    appear anywhere in the REAL app's rendered elucidation."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        texts = await _sweep_all_elucidation_text(app, pilot)
        joined = "\n".join(texts)
        assert "memory:" not in joined.lower(), \
            f"an AI-collaborator internal-memory note reached rendered elucidation: {[t for t in texts if 'memory:' in t.lower()]}"
        assert "omega-lab" not in joined.lower(), \
            f"the insider 'omega-lab' referent reached rendered elucidation: {[t for t in texts if 'omega-lab' in t.lower()]}"
        assert not _INTERNAL_MEMORY_RE.search(joined), \
            f"internal delta/session-numbering jargon (sNN-family) reached rendered elucidation: {[t for t in texts if _INTERNAL_MEMORY_RE.search(t)]}"
        print(f"case 19 ok: swept {len(texts)} rendered elucidation line(s) -- zero "
              f"'memory:' AI-collaborator notes, zero 'omega-lab' insider referents, zero "
              f"'sNN-family' internal numbering anywhere in the operator-facing surface")


async def case_20() -> None:
    """REAL SUB-HEADINGS (round 7, ledger row 1119, defect D9: "Existing-db path --"/
    "Dedicated-db path --" repeated as a line PREFIX on every row was a flat key-value dump
    faking a hierarchy -- a real heading, once per group, is the fix). Proves the substrate
    pane renders exactly two `.ct-elucidation-heading` elements, "Existing-db path" and
    "Dedicated-db path", each unprefixed and each followed by that group's own content before
    the next heading."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "substrate"))
        await pilot.pause()
        pane = app.query_one("#pane-substrate")
        headings = [str(w.render()) for w in pane.query(".ct-elucidation-heading")]
        assert headings == ["Existing-db path", "Dedicated-db path"], \
            f"expected exactly two real, unprefixed sub-headings in order, got {headings}"
        # No description line anywhere still carries the OLD repeated-prefix hack.
        desc_lines = [str(w.render()) for w in pane.query(".ct-section-description")]
        prefixed = [ln for ln in desc_lines if ln.startswith(("Existing-db path --", "Dedicated-db path --"))]
        assert not prefixed, f"expected the OLD repeated-line-prefix hack gone, still found: {prefixed}"
        print(f"case 20 ok: the substrate pane renders TWO real HEADED groups "
              f"({headings!r}), never a repeated line-prefix -- {len(desc_lines)} content "
              f"line(s) total across both groups")


async def case_21() -> None:
    """STANDARDS-ASPIRATION RESTORATION (maintainer round-8 verdict, ledger row 1123-family:
    round 7's schema fix, in the SAME pass that killed the truth-inflating `standards` slot
    (case 9's own D1 fix), deleted several entries' STANDARD NAME wholesale instead of keeping it
    as an explicitly aspiration-marked mention -- "the standards-aspirations were removed
    wholesale instead of indicating that they were aspirations -- better than lying, to be sure,
    but still." Every `feature_facts.REGISTRY` entry whose pre-round-7 text named an external
    standard (via the deleted `standards` field) must still name that standard in its live
    `lead`, phrased as an explicit aspiration ("aspires to <standard>...") -- never a bare
    `Standards: <name>`-shaped resurrection, never silent deletion.

    RED-FIRST is against the round-7 (pre-restoration) state of two of these five entries: with
    the fix reverted, `observability_watchdog` and `hydration_role_charters` name NO standard at
    all in their `lead` (verified directly against feature_facts.toml's own round-7 text, git blob
    1308bd5). GREEN: the current, restored `lead` for every one of the five names its standard AND
    marks it as an aspiration, never bare conformance telegraphy."""
    # --- RED-FIRST: the round-7 (pre-restoration) blob names no standard for two of the five ---
    pre_restoration_toml = subprocess.run(
        ["git", "show", "1308bd5:tools/setup_tui/data/feature_facts.toml"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    pre_leads = {}
    for block in pre_restoration_toml.split("[[fact]]")[1:]:
        km = re.search(r'key\s*=\s*"([^"]+)"', block)
        lm = re.search(r'lead\s*=\s*"((?:[^"\\]|\\.)*)"', block)
        if km and lm:
            pre_leads[km.group(1)] = lm.group(1)
    for key in ("observability_watchdog", "hydration_role_charters"):
        assert "nist" not in pre_leads[key].lower(), (
            f"fixture assumption stale: round-7's own '{key}' lead already names a standard -- "
            f"{pre_leads[key]!r}"
        )
    print("case 21a ok (RED-FIRST): round-7's own committed feature_facts.toml (blob 1308bd5) "
          "names NO standard at all in 'observability_watchdog'/'hydration_role_charters' -- "
          "the wholesale-deletion defect, reproduced straight from git history")

    # --- GREEN: the REAL, current REGISTRY restores every one of the five, aspiration-marked ---
    expect_standard_terms = {
        "principals_authority": "NIST SP 800-63",
        "signed_genesis": "NIST-lineage authenticity",
        "observability_otelcol": "NIST",
        "observability_watchdog": "NIST",
        "hydration_role_charters": "NIST SP 800-63",
    }
    for key, term in expect_standard_terms.items():
        fact = feature_facts.fact(key)
        assert term.lower() in fact.lead.lower(), (
            f"'{key}' lost its standards mention -- expected {term!r} inside its lead, "
            f"got: {fact.lead!r}"
        )
        assert re.search(r"aspir", fact.lead, re.IGNORECASE), (
            f"'{key}' names a standard without aspiration marking -- got: {fact.lead!r}"
        )
        assert not re.match(r"^\s*Standards?\s*:", fact.lead, re.IGNORECASE), (
            f"'{key}' resurrected a bare 'Standards:'-shaped conformance line -- got: {fact.lead!r}"
        )
        print(f"case 21b ok: '{key}' names {term!r} inside an aspiration-marked lead "
              f"(never a bare Standards: line): {fact.lead[:100]!r}...")

    print("case 21 ok: every feature-fact entry that named an external standard before round 7 "
          "still names it live, explicitly aspiration-marked, never a bare conformance line")


async def case_22() -> None:
    """CONFIG-LOAD COMPLETENESS (cycle-2 fix round, AUDIT.md MAJOR #2): loading a file whose
    `[[principals_authority.register]]`/`.competences`/`.relations` rows are populated used to
    drop them SILENTLY while the section's own text claimed --initial-config equivalence.
    RED-FIRST against e1b99da (the audited commit) proves the drop; GREEN drives the REAL,
    CURRENT app end-to-end with `bootstrap/templates/known-good-blank.toml` and confirms the
    principals-authority section ACTUALLY shows 'maintainer'/'orchestrator' with their own
    competences and the 'acts-for' relation, matching the file -- and that the one genuinely
    unseedable fact (a role charter's own host-specific file path) is DISCLOSED by name in the
    same info-line block, never silently omitted."""
    # --- RED-FIRST: e1b99da's own steps_load_config.py never named principals_authority at all --
    old_source = subprocess.run(
        ["git", "show", "e1b99da:tools/setup_tui/steps_load_config.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    assert "principals_authority" not in old_source, \
        ("fixture assumption stale: e1b99da's own steps_load_config.py already names "
         "principals_authority -- the RED reproduction below no longer demonstrates the drop")
    print("case 22a ok (RED-FIRST, reproduced against e1b99da): the audited commit's own "
          "steps_load_config.py contains the string 'principals_authority' NOWHERE -- the "
          "repeatable rows had no seeding code path to drop into at all")

    blank_toml = Path(REPO) / "bootstrap" / "templates" / "known-good-blank.toml"
    doc = config_file.load_config_file(str(blank_toml))
    config_file.validate(doc, require_complete=False)
    old_scoped_keys = {
        "substrate.run": ("substrate", "run"), "substrate.path": ("substrate", "path"),
        "substrate.host": ("substrate", "host"),
        "fork_target.governed_extend": ("fork-target", "governed_extend"),
        "fork_target.governed_extensions": ("fork-target", "governed_extensions"),
        "rehearsal.run": ("rehearsal", "run"), "birth.run": ("birth", "run"),
        "signed_genesis.run": ("signed-genesis", "run"),
        "signed_genesis.commission_statement": ("signed-genesis", "statement"),
        "boundary.configure": ("boundary", "run"), "boundary.start_now": ("boundary", "start_now"),
        "observability.run": ("observability", "run"),
        "observability.otelcol": ("observability", "otelcol"),
        "observability.otel_watch": ("observability", "otel_watch"),
        "hydration.run": ("hydration", "run"),
        "hydration.fork_provenance": ("hydration", "fork_provenance"),
        "hydration.fork_provenance_statement": ("hydration", "fork_provenance_statement"),
        "hydration.role_charters": ("hydration", "role_charters"),
        "hydration.durable_decisions": ("hydration", "durable_decisions"),
        "hydration.adopt_adrs": ("hydration", "adopt_adrs"),
    }
    old_seeded = [d for d in old_scoped_keys if config_file.get(doc, d) is not None]
    assert "principals_authority.register" not in old_seeded
    assert not any(d.startswith("principals_authority") for d in old_seeded), \
        "the OLD scoped-keys table (verbatim replica) must name zero principals_authority keys"
    print(f"case 22b ok (RED, reproduced against the real known-good-blank.toml): the OLD "
          f"scoped-override table seeds {len(old_seeded)} field(s), NONE of them "
          f"'principals_authority.*', even though the file defines "
          f"{len(config_file.get(doc, 'principals_authority.register'))} register row(s), "
          f"{len(config_file.get(doc, 'principals_authority.competences'))} competence row(s), "
          f"and {len(config_file.get(doc, 'principals_authority.relations'))} relation row(s)")

    # --- GREEN: the REAL, CURRENT app, end to end -----------------------------------------------
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(150, 400)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "load-config"))
        await pilot.pause()
        rs = app.query_one("#pane-action-load-config #ct-field-template", RadioSet)
        idx = next(i for i, b in enumerate(rs.children) if "known-good-blank" in str(b.label))
        await pilot.click(rs.children[idx])
        await pilot.pause()
        await pilot.click(app.query_one("#pane-action-load-config #ct-action-apply", Button))
        await pilot.pause()

        info_lines = [str(w.render()) for w in
                      app.query_one("#pane-action-load-config").query(".ct-info-line")]
        seeded_line = next((ln for ln in info_lines if ln.startswith("seeded ")), "")
        assert "principals_authority.register" in seeded_line, \
            f"expected the seeded-fields line to NAME principals_authority.register, got: {seeded_line!r}"
        assert "principals_authority.competences" in seeded_line
        assert "principals_authority.relations" in seeded_line
        not_seeded_line = next((ln for ln in info_lines if ln.startswith("not seeded")), "")
        assert "charters" in not_seeded_line and "host-specific" in not_seeded_line, \
            f"expected the unseedable charter fact DISCLOSED BY NAME, got: {not_seeded_line!r}"
        print(f"case 22c ok (GREEN): the REAL 'Load a configuration' action's own info-lines now "
              f"name principals_authority.register/.competences/.relations as seeded, AND "
              f"disclose the charter gap by name: {seeded_line!r} / {not_seeded_line!r}")

        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case22-dest"
        await pilot.pause()
        await app._panes["principals-authority"].refresh_blocked()
        tree.select_node(_find_node(tree, "principals-authority"))
        await pilot.pause()
        pane = app.query_one("#pane-principals-authority")

        # SELECTION (cycle-3 fix round, ledger row 1136): the compact master-row list shows every
        # loaded principal's own one-line summary (via its SELECT button caption) regardless of
        # selection; a loaded row's own nested competences/relations only render once THAT row is
        # selected (this fix round's own remediation for "buried under repeated preamble").
        select_labels = [str(b.label) for b in pane.query(".ct-md-row-select")]
        assert any("maintainer" in s for s in select_labels), \
            f"expected 'maintainer' (from the loaded file's own register rows) to actually SHOW as a selectable principal row, got {select_labels}"
        assert any("orchestrator" in s for s in select_labels), \
            f"expected 'orchestrator' to actually SHOW as a selectable principal row, got {select_labels}"

        maintainer_idx = next(i for i, s in enumerate(select_labels) if "maintainer" in s)
        pane.query_one(f"#ct-field-register-master-select-{maintainer_idx}").press()
        await pilot.pause()
        maintainer_lines = [str(w.render()) for w in pane.query(".ct-info-line")]
        assert any("governance and agent orchestration" in ln for ln in maintainer_lines), \
            f"expected maintainer's own loaded competence to render once maintainer is selected, got {maintainer_lines}"

        orchestrator_idx = next(i for i, s in enumerate(select_labels) if "orchestrator" in s)
        pane.query_one(f"#ct-field-register-master-select-{orchestrator_idx}").press()
        await pilot.pause()
        orchestrator_lines = [str(w.render()) for w in pane.query(".ct-info-line")]
        assert any("acts-for" in ln and "maintainer" in ln for ln in orchestrator_lines), \
            (f"expected the loaded 'orchestrator acts-for maintainer' relation to render once "
             f"orchestrator (its own SUBJECT) is selected, got {orchestrator_lines}")
        print(f"case 22d ok (GREEN, end to end): after loading known-good-blank.toml and setting "
              f"a destination, the principals-authority section's own compact list actually shows "
              f"{select_labels!r}; selecting maintainer reveals its own loaded competence "
              f"({maintainer_lines}), and selecting orchestrator reveals its own loaded 'acts-for "
              f"maintainer' relation ({orchestrator_lines}) -- matching the file, not merely "
              f"claimed equivalent to it")


def _load_old_add_item_modal_class():
    """Fetches `AddItemModal` exactly as it stood at `9fe6b64` (this cycle-3 fix round's own
    starting commit) -- the version whose `compose()` called `build_field_widget` directly
    (never `build_choice_or_plain_widget`) and rendered NO elucidation at all -- via `git show`,
    executed in an ISOLATED namespace (never imported as a module, same idiom `seen-red/setup-
    tui-seeded-value-visibility`'s own `load_old_section_pane_class` established)."""
    src = subprocess.run(
        ["git", "show", "9fe6b64:tools/configtree/widgets.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {"__name__": "tools.configtree._old_widgets_for_case23"}
    exec(compile(src, "<git show 9fe6b64:tools/configtree/widgets.py>", "exec"), ns)
    return ns["AddItemModal"]


async def case_23() -> None:
    """CYCLE-3 FIX (ledger row 1136's own two MAJOR findings): `AddItemModal.compose` used to
    call `build_field_widget` directly (bypassing the over-threshold ChoiceField filter entirely)
    and never rendered `help`/`option_help` elucidation at all. RED-FIRST against the OLD
    `AddItemModal` (`9fe6b64`, this round's own starting commit) reproduces BOTH exactly; GREEN
    against the CURRENT `item_modal.AddItemModal` (now built on the SAME shared
    `render_item_field` `panes.SectionPane` uses) proves both fixed, via the audit's own named
    scenario: an 11-option ChoiceField (a growing principal roster's own object picker) and a
    4-option ChoiceField carrying real `option_help` sentences (agent_class)."""
    synth_options = tuple((f"opt-{i}", f"Option {i}") for i in range(11))
    synth_help = {v: f"elucidation for {v}" for v, _ in synth_options}
    synth_fields = (
        TextField(name="label", label="Label"),
        ChoiceField(name="pick", label="Pick", options=synth_options, option_help=synth_help),
    )

    OldAddItemModal = _load_old_add_item_modal_class()

    class _HarnessApp(App):
        def compose(self) -> ComposeResult:
            yield Static("harness")

    # --- RED: the OLD AddItemModal, driven live -------------------------------------------------
    # `layout_invariant.suspended()` (ledger row 1139, NET half's own named escape hatch): this
    # block execs a HISTORICAL `9fe6b64` snapshot that predates row 1139's own fix entirely --
    # its own `#ct-modal-buttons` would otherwise trip the invariant for a defect class this
    # block is not testing (it RED/GREENs the filter/option_help defect, ledger row 1136, not
    # this round's phantom-expanse class). See that context manager's own docstring.
    app = _HarnessApp()
    async with app.run_test(size=(150, 60)) as pilot:
        with layout_invariant.suspended():
            await pilot.pause()
            await app.push_screen(OldAddItemModal("Add synthetic", synth_fields))
            await pilot.pause()
            modal = app.screen
            old_filters = list(modal.query(".ct-choice-filter"))
            old_help = list(modal.query(".ct-choice-help"))
            assert not old_filters, \
                f"fixture assumption stale: the OLD AddItemModal already renders a filter Input, got {len(old_filters)}"
            assert not old_help, \
                f"fixture assumption stale: the OLD AddItemModal already renders option_help, got {len(old_help)}"
            print(f"case 23a ok (RED, reproduced against 9fe6b64): the OLD AddItemModal renders a "
                  f"BARE 11-option RadioSet (0 filter Input) and ZERO option_help lines for a field "
                  f"that carries real option_help -- both of ledger row 1136's own MAJOR findings, "
                  f"reproduced live, not merely asserted from reading the diff")
            await pilot.press("escape")
            await pilot.pause()

    # --- GREEN: the CURRENT AddItemModal (`CurrentAddItemModal`, imported at module top), the
    # SAME synthetic fields ----------------------------------------------------------------------
    app2 = _HarnessApp()
    async with app2.run_test(size=(150, 60)) as pilot:
        await pilot.pause()
        await app2.push_screen(CurrentAddItemModal("Add synthetic", synth_fields))
        await pilot.pause()
        modal = app2.screen
        new_filters = list(modal.query(".ct-choice-filter"))
        new_help = [str(w.render()) for w in modal.query(".ct-choice-help")]
        assert new_filters, "expected the CURRENT AddItemModal to route an 11-option ChoiceField through the SAME filter panes.py's own fields get"
        assert len(new_help) >= len(synth_options), \
            f"expected one option_help line per option ({len(synth_options)}), got {len(new_help)}: {new_help}"
        print(f"case 23b ok (GREEN): the CURRENT AddItemModal renders the filter Input "
              f"({len(new_filters)}) AND all {len(new_help)} option_help line(s) for the SAME "
              f"synthetic 11-option ChoiceField -- the shared `item_modal.render_item_field` is "
              f"what `panes.SectionPane` ALSO calls, so the two can never drift again")

    # --- the audit's own EXACT scenario, against the REAL registry ------------------------------
    app3 = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app3.run_test(size=(150, 400)) as pilot:
        await pilot.pause()
        tree = app3.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app3.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case23-dest"
        await pilot.pause()
        await app3._panes["principals-authority"].refresh_blocked()
        tree.select_node(_find_node(tree, "principals-authority"))
        await pilot.pause()
        pane = app3.query_one("#pane-principals-authority")
        for i in range(11):
            await _pa_add_row(pilot, app3, pane, "ct-field-register-master-add",
                        {"name": f"ctj23-{i}", "purpose": "case 23 witness"})
            await pilot.pause()
        pane = app3.query_one("#pane-principals-authority")
        rel_add = pane.query_one("#ct-field-register-detail-add-relations", Button)
        rel_add.press()
        await pilot.pause()
        modal = app3.screen
        real_filters = list(modal.query(".ct-choice-filter"))
        assert real_filters, \
            "expected the REAL Relation add-modal's 11-principal object picker to get the filter Input"
        real_help = [str(w.render()) for w in modal.query(".ct-choice-help")]
        assert len(real_help) >= 4, \
            f"expected the Relation field's own 4-entry option_help (acts-for/dispatched-by/same-natural-person/succeeds), got {real_help}"
        print(f"case 23c ok (GREEN, the audit's own exact named scenario): registering 11 "
              f"principals then opening the REAL Relation add-modal's 'object' picker shows the "
              f"filter Input ({len(real_filters)}) AND the Relation field's own {len(real_help)} "
              f"option_help line(s), live against the real registry")
        await pilot.press("escape")
        await pilot.pause()


async def case_24() -> None:
    """ledger row 1136's own TASK 1: the maintainer's live "adding a principal is a no-op" bench
    report, driven via the REAL operator paths this file's every OTHER case deliberately avoids
    (this file's own module docstring: "NO CASE BELOW PRESSES A SAVE BUTTON... every field write
    is a widget-level .value= assignment" -- true for every case ABOVE, none of which walks a
    real mouse click, real character-by-character typing, or a real RadioSet click). Reproduces
    the maintainer's OWN exact sequence (relayed live by the coordinator): terminal 251x61,
    `dry_run=False`, `dest=/tmp` (an existing, occupied, non-fresh directory), mouse-click Add,
    TYPE into the modal's Inputs, mouse-click a RadioButton, mouse-click Save -- twice, with an
    explicit selection attempt in between.

    ROOT CAUSES FOUND (both real, neither a literal "the add silently drops the row" defect --
    the model and a full end-to-end mouse+typing add both provably worked in every cell this
    fixture drove): (A) a master row was a bare, unfocusable `Static` -- an operator's instinct to
    click a rendered row (the natural next step, and what a `ListView` row elsewhere in this same
    app rewards) was a genuine, reproducible no-op: nothing highlighted, nothing changed, no
    feedback of any kind (`widgets_master_detail.py`'s own docstring, "SELECTION", has the full
    account). (B) the master-detail widget's own preamble (repeated per-row detail labels/help,
    rendered for EVERY row, always) crowded the compact roster far enough down the pane that a
    real terminal at reasonable height needed scrolling just to see the first added row at all
    (the coordinator's own relayed complaint: "looks ugly that you have to do that") -- BOTH are
    now fixed: a master row is a real clickable/focusable `Button` that visibly selects (a `>`
    marker + `-selected` styling), and only the SELECTED row's own dependent lists render, so an
    11-row roster costs 11 LINES, not 11 repeated detail-preamble blocks."""
    app = tui_app.build_app(_fresh_state(), dry_run=False)
    async with app.run_test(size=(251, 61)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        # dest = /tmp verbatim (the maintainer's own real bench value -- an EXISTING, occupied,
        # non-autoharn directory, never a fresh scratch path every OTHER case in this file uses).
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp"
        await pilot.pause()
        await app._panes["principals-authority"].refresh_blocked()
        tree.select_node(_find_node(tree, "principals-authority"))
        await pilot.pause()
        pane = app.query_one("#pane-principals-authority")

        # CONTROL/HELP SPLIT (ledger row 1138): 251 columns is WIDE
        # (`layout_split.WIDE_LAYOUT_MIN_WIDTH`), so the section's own scrollable body is the
        # CONTROL column (`.ct-controls-col`) -- title/description/master-list no longer share
        # ONE scroll region (the description/help now render in the separate `.ct-help-col`
        # instead), which makes this claim (zero scrolling needed to reach the master-list/Add
        # button) hold even more comfortably than the cycle-3 fix this case originally proved.
        scroller = pane.query_one(".ct-controls-col, .ct-section-body", VerticalScroll)
        assert scroller.virtual_size.height <= scroller.size.height, \
            (f"expected the section's own CONTROL content to fit the {scroller.size.height}-row "
             f"viewport with ZERO principals registered yet (virtual height "
             f"{scroller.virtual_size.height}) -- the control/help split (ledger row 1138) moves "
             f"description/help prose out of this column entirely at this width, so this should "
             f"be the common case at a real terminal's real height, more comfortably than before")
        print(f"case 24a ok (layout fix + control/help split): at 251x61 (the maintainer's own "
              f"real terminal), the principals-authority pane's own CONTROL column fits the "
              f"viewport with ZERO scrolling needed before any principal exists (virtual "
              f"{scroller.virtual_size.height} <= viewport {scroller.size.height})")

        async def _mouse_add(name: str) -> None:
            add_btn = pane.query_one("#ct-field-register-master-add", Button)
            await pilot.click(add_btn)
            await pilot.pause()
            modal = app.screen
            name_input = modal.query_one("#ct-field-name", Input)
            await pilot.click(name_input)
            await pilot.pause()
            for ch in name:
                await pilot.press(ch)
            await pilot.pause()
            rs = modal.query_one("#ct-field-agent_class", RadioSet)
            await pilot.click(rs.children[1])
            await pilot.pause()
            purpose_input = modal.query_one("#ct-field-purpose", Input)
            await pilot.click(purpose_input)
            await pilot.pause()
            for ch in "case24-witness":
                await pilot.press(ch)
            await pilot.pause()
            save_btn = modal.query_one("#ct-modal-save", Button)
            await pilot.click(save_btn)
            await pilot.pause()

        await _mouse_add("alice")
        pane = app.query_one("#pane-principals-authority")
        md = pane.query_one(MasterDetailFieldWidget)
        assert md.master_rows == [{"name": "alice", "agent_class": "model", "purpose": "case24-witness"}], \
            f"expected the mouse+typed add to actually land in the model, got {md.master_rows}"
        print(f"case 24b ok (real mouse click + real character-by-character typing + real "
              f"RadioSet click + real mouse-click Save): the row genuinely lands, {md.master_rows}")

        # --- (A) SELECTION -- the maintainer's own "can't select it" -- now genuinely works -----
        select_btns = list(pane.query(".ct-md-row-select"))
        assert len(select_btns) == 1 and select_btns[0].can_focus, \
            f"expected a real, focusable select control per row, got {select_btns}"
        await pilot.click(select_btns[0])
        await pilot.pause()
        select_btns = list(pane.query(".ct-md-row-select"))
        assert "-selected" in (select_btns[0].classes or ()), \
            f"expected clicking the row to actually select it (a visible marker), got classes={select_btns[0].classes}"
        print(f"case 24c ok (DEFECT A FIXED -- 'can't select it'): a real mouse click on the "
              f"rendered principal row NOW selects it (was a bare, unfocusable Static before this "
              f"fix -- a genuine no-op the maintainer's own instinct correctly caught)")

        # --- (C) ROW 1139, THE MAINTAINER'S OWN EXACT CYCLE-6 REPRODUCTION: wide layout (this
        # case's own 251x61), add a principal (alice, above), add a competence to it via the real
        # modal (real mouse click + real character-by-character typing, matching the maintainer's
        # OWN mechanism, not `_pa_add_row`'s `.value=` shortcut), re-observe the detail -- measure
        # the blank gap between the competence's own detail row and the Relation sub-list's own
        # Add button. GREEN here alone would not distinguish "never broke" from "fixed" -- the RED
        # leg (case 26 below) drives the IDENTICAL construction through the PRE-fix `3f0e41b`
        # widget class and proves the SAME measurement fails there.
        add_comp_btn = pane.query_one("#ct-field-register-detail-add-competences", Button)
        await pilot.click(add_comp_btn)
        await pilot.pause()
        modal = app.screen
        for fname, value in (("activity", "orchestrate"), ("band", "x"), ("basis", "x")):
            comp_input = modal.query_one(f"#ct-field-{fname}", Input)
            await pilot.click(comp_input)
            await pilot.pause()
            for ch in value:
                await pilot.press(ch)
            await pilot.pause()
        await pilot.click(modal.query_one("#ct-modal-save", Button))
        await pilot.pause()

        pane = app.query_one("#pane-principals-authority")
        detail_row = pane.query_one(".ct-md-detail-row")
        comp_add_btn = pane.query_one("#ct-field-register-detail-add-competences", Button)
        relation_add = pane.query_one("#ct-field-register-detail-add-relations", Button)
        detail_block = pane.query_one(f"#{pane.query_one(MasterDetailFieldWidget).id}-detail")
        # The GAP right after the competence's own detail row (its immediate next sibling, the
        # "Add Competence" button) is the direct measurement of the row-1139 hazard: pre-fix, a
        # bare `Horizontal()` there claimed a virtual height of ~40+ rows, so THIS gap alone used
        # to read in the dozens; every row after "Add Competence" (the Relation label, its own
        # empty-catalog placeholder, its own Add button) is legitimate rendered CONTENT, not blank
        # space, so a gap measured all the way down to `relation_add` is reported for narrative
        # completeness only, never asserted against the tight blank-row budget.
        gap_after_detail_row = comp_add_btn.region.y - (detail_row.region.y + detail_row.region.height)
        assert gap_after_detail_row <= layout_invariant.BLANK_ROW_BUDGET, (
            f"ROW 1139 REGRESSION -- the maintainer's own exact bench reproduction: after adding "
            f"a competence to alice at the real 251x61 wide layout (mouse click + real typing), "
            f"the 'Add Competence' button sits {gap_after_detail_row} blank row(s) below the "
            f"competence's own detail row -- exceeds BLANK_ROW_BUDGET={layout_invariant.BLANK_ROW_BUDGET}")
        # The direct, structural measurement (row 1139's own named class): the detail BLOCK's own
        # virtual height must not exceed the sum of its children's region heights + tolerance --
        # pre-fix this was 70 (measured against the real app during this round's own diagnosis)
        # for what should be roughly 20-odd rows of real content; post-fix the two must match.
        children_sum = sum(c.region.height for c in detail_block.children if c.display)
        assert detail_block.virtual_size.height <= children_sum + layout_invariant.CONTAINER_HEIGHT_TOLERANCE, (
            f"ROW 1139 REGRESSION: the detail block's own virtual height "
            f"({detail_block.virtual_size.height}) exceeds the sum of its children's region "
            f"heights ({children_sum}) -- PHANTOM VERTICAL EXPANSE")
        print(f"case 24e ok (ROW 1139, the maintainer's own EXACT bench reproduction, GREEN): "
              f"after adding a competence to alice via a real mouse click + real "
              f"character-by-character typing at the real 251x61 wide layout, the 'Add "
              f"Competence' button sits {gap_after_detail_row} blank row(s) below the "
              f"competence's own detail row (no phantom vertical expanse there), and the whole "
              f"detail block's own virtual height ({detail_block.virtual_size.height}) matches "
              f"the sum of its real children's region heights ({children_sum}) -- the Relation "
              f"Add button ({relation_add.region}) is reached by real content, not a blank gap; "
              f"the global invariant (`layout_invariant.check_all`, wired into every Pilot "
              f"interaction in this whole fixture via `wire_pilot`) was ALREADY checking every "
              f"step above and would have failed loudly the instant this regressed")

        # --- (B) a SECOND mouse+typed add, with no manual scroll required in between -----------
        await _mouse_add("bob")
        pane = app.query_one("#pane-principals-authority")
        md = pane.query_one(MasterDetailFieldWidget)
        names = sorted(r["name"] for r in md.master_rows)
        assert names == ["alice", "bob"], \
            f"expected BOTH principals to survive a second mouse+typed add, got {names}"
        select_labels = sorted(str(b.label) for b in pane.query(".ct-md-row-select"))
        assert any("alice" in s for s in select_labels) and any("bob" in s for s in select_labels), \
            f"expected BOTH rows to actually render in the compact list, got {select_labels}"
        print(f"case 24d ok (DEFECT B -- second add): both {names} survive two consecutive real "
              f"mouse+typed adds at the maintainer's own terminal size/dest/dry-run combination, "
              f"and both render in the compact list ({select_labels})")


async def case_25() -> None:
    """TASK 1's own reproduction-matrix small-terminal cell (80x24) -- the ONE cell that DID
    fail, distinct from the maintainer's own 251x61: a real mouse click on the master Add button
    (and, once the modal itself grew content-rich from TASK 2's own elucidation fix, a real click
    inside the modal's own body too) raised `Pilot.OutOfBounds` when the target sat below the
    viewport -- reproduced RED against the OLD (pre this round) layout, where even
    `VerticalScroll.scroll_end()` OVERSHOT the true button position (the section body's own `1fr`
    share was squeezed to a couple of rows by fixed-size title/description siblings above it,
    `panes.py`'s own compose() docstring has the measured account). GREEN: at the SAME 80x24, a
    real click that starts off-viewport, then scrolls its own container to the end and retries
    (matching the maintainer's own "scroll down" step, never a positional-coordinate hack), reaches
    the master Add button, every modal field (now including agent_class's own option_help), and
    the Save button -- and the row genuinely lands."""
    app = tui_app.build_app(_fresh_state(), dry_run=True)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        tree.select_node(_find_node(tree, "fork-target"))
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp/ctj-case25-dest"
        await pilot.pause()
        await app._panes["principals-authority"].refresh_blocked()
        tree.select_node(_find_node(tree, "principals-authority"))
        await pilot.pause()
        pane = app.query_one("#pane-principals-authority")

        async def _click_scrolling_if_needed(widget, container: VerticalScroll) -> None:
            try:
                await pilot.click(widget)
            except Exception:
                container.scroll_end(animate=False)
                await pilot.pause()
                await pilot.click(widget)

        section_body = pane.query_one(".ct-section-body", VerticalScroll)
        add_btn = pane.query_one("#ct-field-register-master-add", Button)
        await _click_scrolling_if_needed(add_btn, section_body)
        await pilot.pause()

        modal = app.screen
        modal_body = modal.query_one("#ct-modal-body", VerticalScroll)
        name_input = modal.query_one("#ct-field-name", Input)
        await _click_scrolling_if_needed(name_input, modal_body)
        await pilot.pause()
        for ch in "smallterm":
            await pilot.press(ch)
        await pilot.pause()
        rs = modal.query_one("#ct-field-agent_class", RadioSet)
        await _click_scrolling_if_needed(rs.children[1], modal_body)
        await pilot.pause()
        purpose_input = modal.query_one("#ct-field-purpose", Input)
        await _click_scrolling_if_needed(purpose_input, modal_body)
        await pilot.pause()
        for ch in "case25":
            await pilot.press(ch)
        await pilot.pause()
        save_btn = modal.query_one("#ct-modal-save", Button)
        await _click_scrolling_if_needed(save_btn, modal_body)
        await pilot.pause()

        pane = app.query_one("#pane-principals-authority")
        md = pane.query_one(MasterDetailFieldWidget)
        assert md.master_rows == [{"name": "smallterm", "agent_class": "model", "purpose": "case25"}], \
            f"expected a real mouse-driven add (scroll-and-retry, never a coordinate hack) to land at 80x24, got {md.master_rows}"
        print(f"case 25 ok (small-terminal, 80x24): a real mouse click that starts off-viewport, "
              f"scrolls its own container, and retries reaches the master Add button AND every "
              f"modal field (now content-rich with elucidation) AND the Save button -- the row "
              f"genuinely lands: {md.master_rows}")


def _load_old_master_detail_widget_class():
    """Fetches `MasterDetailFieldWidget` exactly as it stood at `3f0e41b` (cycle-6's own starting
    commit -- the tree the maintainer's row-1139 screenshots were taken against): the PRE-fix
    version whose detail-row loop wraps each row in a bare, unclassed `Horizontal()` -- row
    1139's own convicted culprit. Via `git show`, executed in an isolated namespace -- the SAME
    idiom `_load_old_add_item_modal_class` (case_23) already established for this file."""
    src = subprocess.run(
        ["git", "show", "3f0e41b:tools/configtree/widgets_master_detail.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {"__name__": "tools.configtree._old_widgets_master_detail_for_case26"}
    exec(compile(src, "<git show 3f0e41b:tools/configtree/widgets_master_detail.py>", "exec"), ns)
    return ns["MasterDetailFieldWidget"]


def _synth_master_detail_spec() -> MasterDetailField:
    """A minimal, domain-free master-detail spec (this module's own `master_detail.py` sibling
    docstring: "ZERO domain knowledge") -- one master ('register') plus THREE dependents, the
    SAME shape (competences/relations/charters) the real principals-authority section declares,
    so the reproduction below is structurally identical to the maintainer's own, not merely
    similarly-shaped."""
    register = ListField(name="register", label="Principal",
                          item_fields=(TextField(name="name", label="Name"),),
                          summarize=lambda r: str(r["name"]))
    competences = ListField(name="competences", label="Competence",
                             item_fields=(TextField(name="activity", label="Activity"),),
                             summarize=lambda r: str(r["activity"]))
    relations = ListField(name="relations", label="Relation",
                           item_fields=(TextField(name="object", label="Object"),),
                           summarize=lambda r: str(r["object"]))
    charters = ListField(name="charters", label="Role charter",
                          item_fields=(TextField(name="path", label="Path"),),
                          summarize=lambda r: str(r["path"]))
    return MasterDetailField(
        master=register,
        details=(DetailListField(list_field=competences, link_field="name"),
                  DetailListField(list_field=relations, link_field="name"),
                  DetailListField(list_field=charters, link_field="name")),
        master_key=lambda r: r["name"])


async def _drive_synth_master_detail(pilot, app, widget_cls) -> None:
    """Add one master row ('alice') then one competence to it -- the maintainer's own EXACT
    reproduction recipe, driven against WHICHEVER `widget_cls` the caller mounted."""
    add_btn = app.query_one(f"#ct-field-register-master-add", Button)
    await pilot.click(add_btn)
    await pilot.pause()
    modal = app.screen
    modal.query_one("#ct-field-name", Input).value = "alice"
    await pilot.pause()
    await pilot.click(modal.query_one("#ct-modal-save", Button))
    await pilot.pause()
    md = app.query_one(widget_cls)
    comp_add = md.query_one(f"#{md.id}-detail-add-competences", Button)
    await pilot.click(comp_add)
    await pilot.pause()
    modal2 = app.screen
    modal2.query_one("#ct-field-activity", Input).value = "orchestrate"
    await pilot.pause()
    await pilot.click(modal2.query_one("#ct-modal-save", Button))
    await pilot.pause()


async def case_26() -> None:
    """RED-then-GREEN, ISOLATED (ledger row 1139): drives the IDENTICAL synthetic master-detail
    construction (`_synth_master_detail_spec`, structurally the same shape as the real
    principals-authority section: one master, three dependents) through the PRE-fix `3f0e41b`
    `MasterDetailFieldWidget` (RED -- reproduces the phantom vertical expanse as a
    `layout_invariant` failure, isolated from any real section/dest/dry-run scaffolding) and the
    CURRENT one (GREEN, and already checked live by the wired `Pilot` throughout its own drive).
    `case_24`'s own step (C) is the SAME reproduction against the REAL app/registry/271x61
    terminal; this case is the isolated, minimal-construction twin that makes the RED leg
    possible without needing to also rebuild the whole real registry against historical code."""
    spec = _synth_master_detail_spec()
    OldMasterDetailFieldWidget = _load_old_master_detail_widget_class()

    class _HarnessApp(App):
        # Reuses the REAL app's own CSS verbatim (`.ct-field-group`/`.ct-md-block`/`.ct-md-row`'s
        # own hand-added `height: auto` overrides live there) -- a bare `App` with no CSS at all
        # would make the OLD widget's OWN partial local patches not even apply, over-reproducing
        # the hazard rather than reproducing it exactly as the maintainer saw it.
        CSS = ConfigTreeApp.CSS

        def __init__(self, widget_cls) -> None:
            super().__init__()
            self._widget_cls = widget_cls

        def compose(self) -> ComposeResult:
            yield self._widget_cls(spec)

    # --- RED: the PRE-fix (3f0e41b) widget class --------------------------------------------
    app = _HarnessApp(OldMasterDetailFieldWidget)
    async with app.run_test(size=(251, 61)) as pilot:
        with layout_invariant.suspended():
            # Suspended for the DRIVE itself (an intermediate frame mid-add is not the claim);
            # the invariant is asserted explicitly, once, against the settled post-add state --
            # the actual RED leg, below.
            await pilot.pause()
            await _drive_synth_master_detail(pilot, app, OldMasterDetailFieldWidget)
        violations = layout_invariant.check_all(app.screen)
    assert violations, \
        "expected the PRE-fix (3f0e41b) MasterDetailFieldWidget to reproduce the phantom-expanse invariant failure, got none"
    assert any("PHANTOM VERTICAL EXPANSE" in v for v in violations), violations
    print(f"case 26a ok (RED, isolated, against 3f0e41b -- ledger row 1139): the PRE-fix "
          f"MasterDetailFieldWidget, driven through the IDENTICAL synthetic master-detail "
          f"construction (add a principal, add a competence), trips the layout invariant -- "
          f"{violations}")

    # --- GREEN: the CURRENT widget class -----------------------------------------------------
    app2 = _HarnessApp(MasterDetailFieldWidget)
    async with app2.run_test(size=(251, 61)) as pilot:
        await pilot.pause()
        await _drive_synth_master_detail(pilot, app2, MasterDetailFieldWidget)
        # Every `pilot.pause()`/`click()` inside `_drive_synth_master_detail` already ran the
        # invariant (wired globally, `wire_pilot` at this module's own top) -- if the CURRENT
        # widget had regressed, THAT call would already have raised. This final explicit check
        # is the same assertion made visible in this case's own witness, not a new code path.
        violations2 = layout_invariant.check_all(app2.screen)
    assert not violations2, f"expected the CURRENT MasterDetailFieldWidget to read clean, got {violations2}"
    print("case 26b ok (GREEN, isolated): the CURRENT MasterDetailFieldWidget, the IDENTICAL "
          "synthetic construction, passes the layout invariant clean -- both the explicit "
          "post-drive check above AND every wired pilot.pause()/click() during the drive itself")


async def _main() -> None:
    await case_0()
    await case_1()
    await case_2()
    await case_3()
    await case_4()
    await case_5()
    await case_6()
    await case_7()
    await case_8()
    await case_9()
    await case_10()
    await case_11()
    await case_12()
    await case_13()
    await case_14()
    await case_15()
    await case_16()
    await case_17()
    await case_18()
    await case_19()
    await case_20()
    await case_21()
    await case_22()
    await case_23()
    await case_24()
    await case_25()
    await case_26()
    print("ALL CASES OK -- tools.configtree.app.ConfigTreeApp driven end-to-end through the "
          "REAL tools.setup_tui.steps.SECTIONS registry via Pilot, LIVE-MODEL semantics "
          "throughout (no per-section save exists): a state-aliasing reproduction and structural "
          "fix across every field kind, arbitrary-order navigation with a "
          "blocked-to-unblocked flip on a SINGLE keystroke, live inline validation both "
          "polarities with focus never leaving the field, a full ten-section journey typed live "
          "to a clean dry-run commit via the ONE commit button, a commit-time business-rule "
          "refusal (red) and its retry (green), keyboard/Tab/scroll navigation primitives, "
          "ctrl+q's exit-code contract, single-editable-home for both shared facts (dest "
          "owned by Fork/target, world by Birth) with a RED-first load-time refusal for a "
          "synthetic double-owner declaration, and a readable-measure width cap (MEASURE=78) "
          "swept across every section plus the original emitting site (the 'Add a principal' "
          "modal), RED-first against a synthetic uncapped Static at a 400-column terminal.")


if __name__ == "__main__":
    asyncio.run(_main())
