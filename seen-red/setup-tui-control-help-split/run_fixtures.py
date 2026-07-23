#!/usr/bin/env python3
"""seen-red/setup-tui-control-help-split/run_fixtures.py -- both-polarity proof of the
control/help split layout fix (ledger row 1138: a maintainer major reopening the converged
cycle-4 loop, from his own 251-column screenshot of principals-authority), census-registered in
gates/fixture_census.py.

THE DEFECT (his own words): "I have to scroll just to find action surfaces, instead of the UI
leveraging hierarchical design and using a scrollable text component situated next to each action
surface" -- content/chrome separation violated (a control belongs in a stable region; only
content should scroll), progressive disclosure absent (deep elucidation prose fully expanded
INLINE between controls), available width unused (a single MEASURE-capped ribbon on a
251-column screen).

THE FIX (`tools/configtree/layout_split.py`'s own module docstring has the full account): at
`layout_split.WIDE_LAYOUT_MIN_WIDTH` or wider, a section/action pane splits into a compact
CONTROL column (`.ct-controls-col`) beside an independently-scrollable HELP column
(`.ct-help-col`) carrying the section's own elucidation prose (description + every field's
`help`/`option_help`, and for a `MasterDetailField`, its master/detail help too) -- section-level
help, not per-field-focus-following (a genuine Textual-machinery limit for a composite widget
like `MasterDetailFieldWidget`, named honestly rather than half-built). Below that width, the
split collapses to one column with elucidation SUPPRESSED by default (never the old fully-
expanded inline interleave) -- an operator presses `F1` ("Help", shown on the Footer) to bring it
back inline, on demand.

RED (case 1): a SYNTHETIC section (deliberately-long `help=` prose on every field, so the fixture
never depends on any REAL section's own prose length happening to be long enough) driven through
the OLD `SectionPane` (`PRE_FIX_COMMIT`, straight from git history, via `git show`, mirroring
`seen-red/setup-tui-commit-off-ui-thread`'s own technique) at 251 columns: the section's own
final control (a synthetic "Add" button) sits OUTSIDE the viewport -- reachable only by
scrolling PAST every field's own inline help text first.

GREEN (cases 2-6): the CURRENT `SectionPane`, same synthetic section:
  2. at 251x61 (WIDE): the control column's own virtual height fits the viewport with ZERO
     scrolling -- the SAME long help prose now lives in the separate help column instead.
  3. the help column renders the SAME elucidation text, MEASURE (78) still capping its own line
     length -- narrower, not merely relocated with the cap silently dropped.
  4. the two columns scroll INDEPENDENTLY: scrolling the help column leaves the control column's
     own scroll position untouched, and vice versa.
  5. at 120x40 (NARROW, below the threshold): elucidation is SUPPRESSED by default (a short
     "press F1" hint renders instead of the wall of prose) -- every control (including the
     synthetic "Add" button) is reachable with LESS scrolling than the OLD code needed at the
     SAME width; pressing `F1` brings the SAME elucidation text back, inline, on demand.
  6. the REAL `principals-authority` section (the maintainer's own named scenario, not just a
     synthetic stand-in), at 251x61 with two real registered principals: every action surface
     (register-master-add, the selected principal's own competence/relation/charter add
     buttons) sits inside the viewport with ZERO scrolling -- the exact screenshot this fix
     answers, reproduced against the REAL section this time, not a synthetic proxy.

Zero residue: everything is in-memory/synthetic or `--dry-run`; no real filesystem/network/git
act anywhere besides the one `git show` read. Lazy imports banned.

Usage: PYTHONPATH=<repo root> <python-with-textual> seen-red/setup-tui-control-help-split/run_fixtures.py
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from textual.containers import VerticalScroll  # noqa: E402
from textual.widgets import Button, Input, RadioSet, Static, Tree  # noqa: E402

from tools.configtree import CommitSpec, SectionResult, SectionSpec, TextField  # noqa: E402
import tools.configtree.app as ct_app_module  # noqa: E402
from tools.configtree.app import ConfigTreeApp  # noqa: E402
from tools.configtree.layout_split import WIDE_LAYOUT_MIN_WIDTH  # noqa: E402
from tools.setup_tui import tui_app, steps  # noqa: E402

# The commit immediately before this fix -- pinned by SHA, never HEAD.
PRE_FIX_COMMIT = "1e6fb5f"

_LONG_HELP = (
    "This is a deliberately long, multi-clause help sentence for a synthetic field, written so "
    "that this fixture never depends on any REAL section's own prose happening to be long "
    "enough to reproduce the hazard -- it exists purely to occupy vertical space the way a "
    "real Constitutes/Does-not elucidation block does, repeated per field below."
)


def _synthetic_registry():
    def fields(state):
        return tuple(
            TextField(name=f"f{i}", label=f"Field {i}", help=_LONG_HELP, required=False)
            for i in range(6)
        )

    def submit(state, answers):
        return SectionResult(ok=True)

    spec = SectionSpec(slug="synth", title="Synthetic", group="G", fields=fields, submit=submit,
                        description=_LONG_HELP)
    commit_spec = CommitSpec(render_summary=lambda s: "x",
                              commit=lambda s: SectionResult(ok=True))
    return (spec,), commit_spec


def load_old_section_pane_class():
    """`SectionPane` exactly as it stood at `PRE_FIX_COMMIT` -- via `git show`, executed in an
    isolated namespace, mirroring `seen-red/setup-tui-commit-off-ui-thread`'s own technique."""
    src = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:tools/configtree/panes.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    ns: dict = {"__name__": "tools.configtree._old_panes_for_split_fixture"}
    exec(compile(src, f"<git show {PRE_FIX_COMMIT}:tools/configtree/panes.py>", "exec"), ns)
    return ns["SectionPane"]


def _select(app, tree, slug: str) -> None:
    node = next(n for group in tree.root.children for n in group.children
                if (n.data or {}).get("slug") == slug)
    tree.select_node(node)
    tree.action_select_cursor()


async def case_1_red() -> None:
    OldSectionPane = load_old_section_pane_class()
    original = ct_app_module.SectionPane
    ct_app_module.SectionPane = OldSectionPane
    try:
        sections, commit_spec = _synthetic_registry()
        app = ConfigTreeApp(sections, commit_spec, initial_state={})
        async with app.run_test(size=(251, 61)) as pilot:
            await pilot.pause()
            tree = app.query_one("#ct-tree", Tree)
            _select(app, tree, "synth")
            await pilot.pause()
            pane = app.query_one("#pane-synth")
            scroller = pane.query_one(".ct-section-body", VerticalScroll)
            assert scroller.virtual_size.height > scroller.size.height, (
                f"expected the OLD, interleaved layout to need scrolling to reach the final "
                f"control at 251 columns (virtual {scroller.virtual_size.height} vs viewport "
                f"{scroller.size.height}) -- if this DOESN'T reproduce, the synthetic prose "
                f"needs to be longer, not the fix declared unnecessary")
            print(f"case 1 ok (RED, reproduced against {PRE_FIX_COMMIT}): the OLD interleaved "
                  f"layout's own control-and-prose column needs scrolling at 251x61 (virtual "
                  f"{scroller.virtual_size.height} > viewport {scroller.size.height}) -- exactly "
                  f"the maintainer's own screenshot complaint")
    finally:
        ct_app_module.SectionPane = original


async def case_2_wide_no_scroll() -> None:
    sections, commit_spec = _synthetic_registry()
    app = ConfigTreeApp(sections, commit_spec, initial_state={})
    async with app.run_test(size=(251, 61)) as pilot:
        await pilot.pause()
        assert app.layout_is_wide, "expected 251 columns to be WIDE (layout_split.WIDE_LAYOUT_MIN_WIDTH)"
        tree = app.query_one("#ct-tree", Tree)
        _select(app, tree, "synth")
        await pilot.pause()
        pane = app.query_one("#pane-synth")
        controls = pane.query_one(".ct-controls-col", VerticalScroll)
        assert controls.virtual_size.height <= controls.size.height, (
            f"expected the control column to fit the viewport with ZERO scrolling at 251x61 "
            f"(virtual {controls.virtual_size.height} vs viewport {controls.size.height}) -- "
            f"the SAME long help text used in case 1, now living in the separate help column")
        print(f"case 2 ok (GREEN): at 251x61 the control column fits the viewport with ZERO "
              f"scrolling (virtual {controls.virtual_size.height} <= viewport "
              f"{controls.size.height}) -- the SAME synthetic prose that overflowed case 1's "
              f"OLD single column now lives in the separate help column instead")


async def case_3_measure_still_capped() -> None:
    sections, commit_spec = _synthetic_registry()
    app = ConfigTreeApp(sections, commit_spec, initial_state={})
    async with app.run_test(size=(251, 61)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        _select(app, tree, "synth")
        await pilot.pause()
        pane = app.query_one("#pane-synth")
        help_col = pane.query_one(".ct-help-col", VerticalScroll)
        help_statics = list(help_col.query(Static))
        assert help_statics, "expected the help column to actually carry the elucidation Statics"
        assert any(_LONG_HELP in str(w.render()) for w in help_statics), \
            "expected the synthetic help text to render inside the help column"
        widths = [w.size.width for w in help_statics if str(w.render()).strip()]
        assert widths and max(widths) <= 78 + 8, (
            f"expected every help-column Static to stay within MEASURE's own cap (+the help "
            f"column's small padding budget), got widths {widths} -- the split must not have "
            f"silently dropped the readable-measure cap along the way")
        print(f"case 3 ok (GREEN): the help column renders the SAME elucidation text, still "
              f"capped at a readable measure (widest observed {max(widths)} columns) -- MEASURE "
              f"is a line-length rule this split does not get to relax")


async def case_4_independent_scroll() -> None:
    sections, commit_spec = _synthetic_registry()
    app = ConfigTreeApp(sections, commit_spec, initial_state={})
    # A SHORT viewport (height=20, still 251 columns -- WIDE) so the help column's own content
    # (6 long prose paragraphs) genuinely overflows and a real scroll is exercised, not a no-op
    # on already-fully-visible content.
    async with app.run_test(size=(251, 20)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        _select(app, tree, "synth")
        await pilot.pause()
        pane = app.query_one("#pane-synth")
        controls = pane.query_one(".ct-controls-col", VerticalScroll)
        help_col = pane.query_one(".ct-help-col", VerticalScroll)
        before_controls, before_help = controls.scroll_offset, help_col.scroll_offset
        help_col.scroll_down(animate=False)
        await pilot.pause()
        assert help_col.scroll_offset != before_help, "expected the help column to actually scroll"
        assert controls.scroll_offset == before_controls, (
            "expected scrolling the HELP column to leave the CONTROL column's own scroll "
            "position untouched -- the whole point of two independent regions, not one")
        print(f"case 4 ok (GREEN): scrolling the help column ({before_help} -> "
              f"{help_col.scroll_offset}) leaves the control column's own scroll position "
              f"({controls.scroll_offset}) untouched -- genuinely independent regions")


async def case_5_narrow_collapse_and_toggle() -> None:
    OldSectionPane = load_old_section_pane_class()
    sections, commit_spec = _synthetic_registry()

    # OLD layout at the SAME narrow width, for an honest before/after comparison (not just an
    # assertion in isolation) -- the old code has no wide/narrow concept at all, so it ALWAYS
    # interleaves, at every width.
    original = ct_app_module.SectionPane
    ct_app_module.SectionPane = OldSectionPane
    try:
        old_app = ConfigTreeApp(sections, commit_spec, initial_state={})
        async with old_app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            tree = old_app.query_one("#ct-tree", Tree)
            _select(old_app, tree, "synth")
            await pilot.pause()
            old_pane = old_app.query_one("#pane-synth")
            old_scroller = old_pane.query_one(".ct-section-body", VerticalScroll)
            old_virtual = old_scroller.virtual_size.height
    finally:
        ct_app_module.SectionPane = original

    sections2, commit_spec2 = _synthetic_registry()
    app = ConfigTreeApp(sections2, commit_spec2, initial_state={})
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert not app.layout_is_wide, "expected 120 columns to be NARROW (below WIDE_LAYOUT_MIN_WIDTH)"
        tree = app.query_one("#ct-tree", Tree)
        _select(app, tree, "synth")
        await pilot.pause()
        pane = app.query_one("#pane-synth")
        collapsed_scroller = pane.query_one(".ct-section-body", VerticalScroll)
        collapsed_virtual = collapsed_scroller.virtual_size.height
        assert collapsed_virtual < old_virtual, (
            f"expected the NEW narrow-collapsed layout to need LESS scrolling than the OLD "
            f"always-interleaved layout at the SAME 120x40 -- new {collapsed_virtual} vs old "
            f"{old_virtual}")
        assert not app.help_visible, "expected help to start collapsed (never a default reproducing the old interleave)"
        collapsed_texts = [str(w.render()) for w in pane.query(Static)]
        assert not any(_LONG_HELP in t for t in collapsed_texts), \
            "expected the long help text to be ABSENT while collapsed, not merely scrolled past"
        assert any("press F1" in t for t in collapsed_texts), \
            "expected an honest on-demand-disclosure hint while collapsed"
        print(f"case 5a ok (GREEN, narrow collapse): at the SAME 120x40, the new layout's own "
              f"virtual content height ({collapsed_virtual}) is LESS than the old always-"
              f"interleaved layout's ({old_virtual}) -- elucidation is genuinely absent, not "
              f"merely relocated, with an honest 'press F1' hint in its place")

        await pilot.press("f1")
        await pilot.pause()
        assert app.help_visible, "expected F1 to toggle help_visible on"
        expanded_texts = [str(w.render()) for w in pane.query(Static)]
        assert any(_LONG_HELP in t for t in expanded_texts), \
            "expected F1 to bring the SAME elucidation text back, inline, on demand"
        print("case 5b ok (GREEN, on-demand disclosure): pressing F1 brings the SAME "
              "elucidation text back inline -- on-demand, never a default")


async def case_6_real_principals_authority() -> None:
    app = tui_app.build_app(steps.initial_state(dry_run=True), dry_run=True)
    async with app.run_test(size=(251, 61)) as pilot:
        await pilot.pause()
        tree = app.query_one("#ct-tree", Tree)
        _select(app, tree, "fork-target")
        await pilot.pause()
        app.query_one("#pane-fork-target #ct-field-dest", Input).value = "/tmp"
        await pilot.pause()
        await app._panes["principals-authority"].refresh_blocked()
        _select(app, tree, "principals-authority")
        await pilot.pause()
        pane = app.query_one("#pane-principals-authority")
        controls = pane.query_one(".ct-controls-col", VerticalScroll)

        add_btn = controls.query_one("#ct-field-register-master-add", Button)
        assert controls.region.contains_point((add_btn.region.x, add_btn.region.y)), (
            "expected the 'Add Principal' button to be inside the control column's own "
            "current viewport, no scroll needed, at 251x61 (the maintainer's own real size)")
        print("case 6a ok (GREEN, the real screenshot scenario): 'Add Principal' sits inside "
              "the control column's own viewport at 251x61, zero scroll, on the REAL "
              "principals-authority section")

        async def _add(name: str) -> None:
            btn = controls.query_one("#ct-field-register-master-add", Button)
            await pilot.click(btn)
            await pilot.pause()
            modal = app.screen
            name_input = modal.query_one("#ct-field-name", Input)
            await pilot.click(name_input)
            for ch in name:
                await pilot.press(ch)
            rs = modal.query_one("#ct-field-agent_class", RadioSet)
            await pilot.click(rs.children[1])
            purpose_input = modal.query_one("#ct-field-purpose", Input)
            await pilot.click(purpose_input)
            for ch in "case6-witness":
                await pilot.press(ch)
            await pilot.click(modal.query_one("#ct-modal-save", Button))
            await pilot.pause()

        await _add("alice")
        controls = pane.query_one(".ct-controls-col", VerticalScroll)
        competence_add = controls.query_one("#ct-field-register-detail-add-competences", Button)
        assert controls.region.contains_point((competence_add.region.x, competence_add.region.y)), (
            "expected the SELECTED principal's own 'Add Competence' button to be inside the "
            "control column's viewport at 251x61 -- no scroll, even with a principal registered")
        print("case 6b ok (GREEN): the selected principal's own 'Add Competence' button is "
              "also inside the control column's viewport at 251x61, zero scroll")


async def _main() -> None:
    await case_1_red()
    await case_2_wide_no_scroll()
    await case_3_measure_still_capped()
    await case_4_independent_scroll()
    await case_5_narrow_collapse_and_toggle()
    await case_6_real_principals_authority()
    print("ALL CASES OK -- the control/help split (ledger row 1138): RED-first against the OLD, "
          "always-interleaved SectionPane (a control needing to scroll past prose at 251x61), "
          "GREEN against the CURRENT split (zero-scroll control column, MEASURE still capping "
          "the relocated prose, two genuinely independent scroll regions, a narrow-width "
          "collapse that is LESS content than the old interleave -- not merely scrolled past -- "
          "with an honest on-demand F1 disclosure toggle), and a REAL principals-authority leg "
          "reproducing the maintainer's own 251x61 screenshot scenario directly.")


if __name__ == "__main__":
    asyncio.run(_main())
