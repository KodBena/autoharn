#!/usr/bin/env python3
"""seen-red/setup-tui-seeded-value-visibility/run_fixtures.py -- both-polarity proof of the
config-load seeding visibility fix (maintainer-witnessed, ledger row 1130): the in-UI "Load a
configuration" action reported "seeded 21 field default(s)" but the maintainer's own bench
report was that sections did not show the values as set, census-registered in
gates/fixture_census.py.

ROOT CAUSE, established empirically (not assumed) before writing this fixture: `get_field_value`/
`set_field_value`/every widget builder in `tools/configtree/widgets.py` were verified correct for
ALL FOUR field kinds (`TextField`/`ChoiceField`/`ConfirmField`/`MultiChoiceField`) once a section
is genuinely UNBLOCKED -- a throwaway Pilot probe seeding `hydration.durable_decisions`/
`adopt_adrs` with NON-EMPTY lists (the shipped `known-good-blank.toml` seeds both as `[]`, which
cannot distinguish "seeded correctly to nothing" from "seeding is broken") showed every field
kind rendering its seeded value correctly once `dest` was set. The maintainer's own bench report
is reproduced by a DIFFERENT mechanism: `hydration` (like `boundary`/`observability`/`birth`/
`principals-authority`/`signed-genesis`) is `blocked` until a destination directory is set
elsewhere (Fork/target) -- and `SectionPane.compose`'s OLD code returned immediately on a
blocked reason, rendering ONLY the "BLOCKED -- ..." banner and NOTHING about the section's own
fields, seeded or not. An operator who loads a config and immediately checks a gated section
(without first visiting Fork/target) sees a blocked banner with zero cue that the seeded values
are sitting there, unseen, underneath -- exactly the "does not visibly take effect" report, for
EVERY field kind a blocked section carries, not one kind specifically.

RED (case 1): loads the OLD `SectionPane` straight from git history (`PRE_FIX_COMMIT`, the last
commit before this fix, via `git show`, executed in an isolated namespace) into the REAL running
app (`tools.setup_tui.tui_app`), reproduces the maintainer's own path EXACTLY -- launch, use the
in-UI "Load a configuration" node on a `known-good-blank.toml` variant seeded with non-empty
`durable_decisions`/`adopt_adrs` (so a MultiChoiceField's own seeding is genuinely checkable, not
vacuously "seeded to empty"), then visit `hydration` WITHOUT ever visiting Fork/target -- and
confirms the OLD pane shows ONLY the blocked banner, no hint any field holds a seeded value.

GREEN (cases 2-3): the REAL, current `SectionPane`, the SAME path:
  2. the SAME blocked visit to `hydration` now ALSO shows a line naming every field whose
     current value DIFFERS from its own compile-time default -- both `MultiChoiceField`s here.
     Named, honest limitation (not swept under "GREEN"): the loader ALSO seeds `ConfirmField`
     "run" to `True`, which happens to equal that field's own default, so the value!=default
     detector correctly has nothing new to report for it -- there was never a visible gap to
     close for a field whose seeded value coincides with its default.
  3. setting `dest` afterward (unblocking hydration) shows the `ConfirmField` AND both
     `MultiChoiceField`s all rendering their real seeded values -- the checkbox groups
     genuinely ticked, not merely counted in a seeding message -- confirming the fix is real
     feedback, not just a claim, across every field kind this section carries.

Zero residue: everything is `--dry-run`, no real filesystem/network act. Lazy imports banned.

Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-seeded-value-visibility/run_fixtures.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from textual.widgets import Checkbox, Input, Static, Tree  # noqa: E402

import tools.configtree.app as ct_app_module  # noqa: E402
from tools.configtree.widgets import MultiChoiceFieldWidget  # noqa: E402
from tools.setup_tui import steps, tui_app  # noqa: E402

# The last commit before this fix -- pinned by SHA, never HEAD.
PRE_FIX_COMMIT = "3cc769d"

TEMPLATE_PATH = os.path.join(REPO, "bootstrap", "templates", "known-good-blank.toml")


def _write_nonempty_multichoice_template() -> str:
    """A `known-good-blank.toml` variant with NON-EMPTY `durable_decisions`/`adopt_adrs` -- the
    shipped template seeds both as `[]`, which cannot distinguish "seeded correctly to nothing"
    from "MultiChoiceField seeding is broken" (this fixture's own docstring explains why)."""
    text = open(TEMPLATE_PATH, encoding="utf-8").read()
    assert 'durable_decisions = []' in text, "expected the shipped template's own empty-list line"
    assert 'adopt_adrs = []' in text, "expected the shipped template's own empty-list line"
    text = text.replace(
        'durable_decisions = []    # checklist: "tags-are-serious-business SKIPPED", '
        '"runs-are-strictly-linear SKIPPED" -- the only two durable decisions that existed in '
        "the catalog at this world's birth time, both declined",
        'durable_decisions = ["tags-are-serious-business", "single-branch-authoring"]',
    )
    text = text.replace(
        'adopt_adrs = []    # checklist: "adr adoption (ADR-0001: Immutability...) SKIPPED  '
        'operator declined" -- the only ADR line this checklist shows, declined',
        'adopt_adrs = ["0000", "0002"]',
    )
    assert 'durable_decisions = ["tags-are-serious-business"' in text, "template substitution failed"
    assert 'adopt_adrs = ["0000"' in text, "template substitution failed"
    fd, path = tempfile.mkstemp(suffix=".toml", prefix="seeded-visibility-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def load_old_section_pane_class():
    """Fetches `SectionPane` exactly as it stood in `PRE_FIX_COMMIT` -- the version whose
    `compose()` returned immediately on a blocked reason, saying nothing about seeded fields --
    via `git show`, executed in an ISOLATED namespace (never imported as a module)."""
    src = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:tools/configtree/panes.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {"__name__": "tools.configtree._old_panes_for_seeded_visibility_fixture"}
    exec(compile(src, f"<git show {PRE_FIX_COMMIT}:tools/configtree/panes.py>", "exec"), ns)
    return ns["SectionPane"]


def _find_node(tree: Tree, kind: str, slug: "str | None" = None):
    def _walk(node):
        for child in node.children:
            data = child.data or {}
            if data.get("kind") == kind and (slug is None or data.get("slug") == slug):
                return child
            found = _walk(child)
            if found is not None:
                return found
        return None
    return _walk(tree.root)


async def _load_config(pilot, app, path: str) -> None:
    tree = app.query_one("#ct-tree", Tree)
    action_node = _find_node(tree, "action", "load-config")
    tree.select_node(action_node)
    tree.action_select_cursor()
    await pilot.pause()
    # SCOPED, not a bare `#ct-field-path` (ledger row 1138 finding, control/help split): the
    # load-config action's own `path` TextField and substrate's own `path` ChoiceField share the
    # SAME bare field id (`ct-field-path` -- `field_widget_id` scopes by FIELD name only, not by
    # owning section/action) -- an existing, pre-fix latent ambiguity `query_one`'s own ID lookup
    # (a BREADTH-FIRST first-match, not a type-filtered search across every match) happened to
    # resolve correctly before this fix purely because of incidental DOM DEPTH: the action pane's
    # Input sat no deeper than substrate's RadioSet. The control/help split adds one nesting level
    # to the action pane's own DOM (the wide layout's `Horizontal` wrapper), making the Input
    # STRICTLY deeper than the RadioSet and flipping which one breadth-first search meets first --
    # not a defect in the split itself, but a genuinely pre-existing ambiguity the split exposed.
    # Scoped to the owning ActionPane's own id, this query is correct regardless of DOM depth,
    # section-registry order, or any future layout change -- the actually robust fix, not a
    # depth-coincidence someone else could just as easily re-break.
    path_input = app.query_one("#pane-action-load-config #ct-field-path", Input)
    path_input.value = path
    await pilot.pause()
    apply_btn = app.query_one("#ct-action-apply")
    apply_btn.press()
    await pilot.pause()


async def case_1_red(template_path: str) -> None:
    OldSectionPane = load_old_section_pane_class()
    original = ct_app_module.SectionPane
    ct_app_module.SectionPane = OldSectionPane
    try:
        state = steps.initial_state(dry_run=True)
        app = tui_app.build_app(state, dry_run=True)
        async with app.run_test(size=(150, 55)) as pilot:
            await pilot.pause()
            await _load_config(pilot, app, template_path)
            tree = app.query_one("#ct-tree", Tree)
            hyd_node = _find_node(tree, "section", "hydration")
            tree.select_node(hyd_node)
            tree.action_select_cursor()
            await pilot.pause()
            hyd_pane = app._panes["hydration"]
            assert hyd_pane._blocked_reason, "expected hydration to read BLOCKED (dest never set)"
            statics = [str(w.render()) for w in hyd_pane.query(Static)]
            seeded_mentions = [s for s in statics if "seeded" in s.lower()]
            assert not seeded_mentions, (
                f"expected the OLD pane to say NOTHING about seeded values while blocked -- "
                f"found {seeded_mentions!r}")
            print("case 1 ok (RED, reproduced against "
                  f"{PRE_FIX_COMMIT}): after loading a config that seeded hydration's own "
                  "ConfirmField + two MultiChoiceFields, visiting the (still-blocked, dest "
                  "never set) hydration section shows ONLY the blocked banner -- zero "
                  "indication any field holds a seeded value, exactly the maintainer's own "
                  "bench report")
    finally:
        ct_app_module.SectionPane = original


async def case_2_blocked_shows_seeded(template_path: str) -> None:
    state = steps.initial_state(dry_run=True)
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        await _load_config(pilot, app, template_path)
        tree = app.query_one("#ct-tree", Tree)
        hyd_node = _find_node(tree, "section", "hydration")
        tree.select_node(hyd_node)
        tree.action_select_cursor()
        await pilot.pause()
        hyd_pane = app._panes["hydration"]
        assert hyd_pane._blocked_reason, "expected hydration to still read BLOCKED (dest never set)"
        statics = [str(w.render()) for w in hyd_pane.query(Static)]
        seeded_line = next((s for s in statics if "seeded" in s.lower()), None)
        assert seeded_line is not None, (
            f"expected a line naming hydration's own seeded fields while blocked -- got {statics!r}")
        for name in ("durable_decisions", "adopt_adrs"):
            assert name in seeded_line, f"expected {name!r} named in the seeded-fields line: {seeded_line!r}"
        # NAMED, HONEST SCOPE NOTE: "run" is ALSO seeded by this template (True), but True is
        # ALSO `ConfirmField(name="run", default=True)`'s own compile-time default -- the fix's
        # own detector (`get_field_value(...) != default_of(f)`) has no way to tell "seeded to
        # the same value the default already was" from "never seeded at all" for a field whose
        # seeded value and default happen to coincide, and rightly does not claim to: there was
        # never a VISIBLE gap to close for "run" here (an operator glancing at a blocked banner
        # was never going to see anything but "default" for it either way). This is a genuine,
        # narrow limitation, not silently swept under the "GREEN" label.
        assert "run" not in seeded_line, (
            f"'run' is seeded to its own default value (True) -- expected it OMITTED from the "
            f"seeded-fields line (nothing to reveal), got {seeded_line!r}")
        print(f"case 2 ok (GREEN): the SAME blocked visit now shows {seeded_line!r} -- naming "
              "every seeded field whose value actually DIFFERS from its own default (both "
              "MultiChoiceFields), still correctly blocked from editing. 'run' is deliberately "
              "NOT named -- it was seeded to its own default value (True), so there was never "
              "a gap between what a blocked banner already implied and what the operator would "
              "see once unblocked (a named, honest limitation of the value!=default detector, "
              "not a regression).")


async def case_3_unblocked_shows_real_values(template_path: str) -> None:
    state = steps.initial_state(dry_run=True)
    app = tui_app.build_app(state, dry_run=True)
    async with app.run_test(size=(150, 55)) as pilot:
        await pilot.pause()
        await _load_config(pilot, app, template_path)
        tree = app.query_one("#ct-tree", Tree)

        ft_node = _find_node(tree, "section", "fork-target")
        tree.select_node(ft_node)
        tree.action_select_cursor()
        await pilot.pause()
        ft_pane = app._panes["fork-target"]
        dest_input = ft_pane.query_one("#ct-field-dest", Input)
        dest_input.value = "/tmp/seeded-visibility-fixture-dest"
        await pilot.pause()

        hyd_node = _find_node(tree, "section", "hydration")
        tree.select_node(hyd_node)
        tree.action_select_cursor()
        await pilot.pause()
        hyd_pane = app._panes["hydration"]
        assert not hyd_pane._blocked_reason, "expected hydration to be UNBLOCKED once dest is set"

        run_cb = hyd_pane.query_one("#ct-field-run", Checkbox)
        assert run_cb.value is True, "expected hydration's seeded ConfirmField 'run' to render checked"

        durable_mw = hyd_pane.query_one("#ct-field-durable_decisions", MultiChoiceFieldWidget)
        assert set(durable_mw.selected) == {"tags-are-serious-business", "single-branch-authoring"}, (
            f"expected durable_decisions seeded selection, got {durable_mw.selected!r}")

        adr_mw = hyd_pane.query_one("#ct-field-adopt_adrs", MultiChoiceFieldWidget)
        assert set(adr_mw.selected) == {"0000", "0002"}, (
            f"expected adopt_adrs seeded selection, got {adr_mw.selected!r}")

        print("case 3 ok (GREEN): once unblocked, hydration's seeded ConfirmField AND both "
              "seeded MultiChoiceFields render their real, correct values -- "
              f"run={run_cb.value}, durable_decisions={sorted(durable_mw.selected)}, "
              f"adopt_adrs={sorted(adr_mw.selected)}")


async def _main() -> None:
    template_path = _write_nonempty_multichoice_template()
    try:
        await case_1_red(template_path)
        await case_2_blocked_shows_seeded(template_path)
        await case_3_unblocked_shows_real_values(template_path)
    finally:
        os.unlink(template_path)
    print("ALL CASES OK -- config-load seeding visibility fix (ledger row 1130): RED-first "
          "against the OLD SectionPane (a blocked section's seeded fields were completely "
          "invisible, of any kind), GREEN against the CURRENT SectionPane (a blocked section "
          "now names every field already holding a seeded value; once unblocked, the "
          "ConfirmField and both MultiChoiceFields all render their real seeded selections).")


if __name__ == "__main__":
    import asyncio
    asyncio.run(_main())
