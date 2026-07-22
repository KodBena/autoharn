#!/usr/bin/env python3
"""tools/configtree/app.py -- the generic Textual driver (design/FABLE-SETUP-TUI-REBUILD-SPEC.md
§3 v2/§6): ONE main screen, a sidebar `Tree` of the ENTIRE configuration (every section and
subsection visible at once, arrow keys/mouse reach any node in any order) plus a right-pane form
for whichever section is selected, plus a persistent status line. Zero autoharn knowledge --
every string this module shows besides its own chrome comes from the `SectionSpec`/`CommitSpec`
a consumer hands it.

NAVIGATION (the spec's own acceptance bar): Tab/shift-Tab and arrow keys move focus; Up/Down move
the tree cursor; Enter/click selects a tree node (`Tree.NodeSelected`), switching the right
pane's `ContentSwitcher.current` to that node's pane -- NO Back/Next buttons, no screen stack, no
positional ordering of any kind. EVERY SECTION PANE IS MOUNTED ONCE, at startup, into the
`ContentSwitcher`.

LIVE MODEL (maintainer review, 2026-07-22): the ONLY action buttons in the whole app are the
commit node's own commit confirmation and quit (`panes.py`'s own module docstring has the full
account of the per-section-Save-button deletion this answers). Every field write reaches the
shared `state` immediately via `panes.SectionPane`'s own Changed-message handlers; this class's
own job is cheap, app-wide bookkeeping on every such change: `on_model_changed` (called by any
pane after ANY field write) recomputes every tree node's status label and the status line --
never a widget rebuild, just text -- so a dependency unblocks, or a field's own inline error
clears, the INSTANT its prerequisite value lands, not on some later save/select event. A pane's
own FORM CONTENT (its blocked-reason banner, its business-rule error) still only re-renders when
that pane is actually selected (`on_tree_node_selected`'s own `refresh_blocked` call) -- cheap
status recomputation is app-wide and constant; a full pane recompose stays lazy, on visit."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import ContentSwitcher, Footer, Header, Static, Tree

from tools.configtree.actions import ActionPane
from tools.configtree.measure import MEASURE
from tools.configtree.commit_pane import CommitPane
from tools.configtree.panes import SectionPane
from tools.configtree.spec import (BLOCKED, COMPLETE, INVALID, ActionSpec, CommitSpec,
                                    SectionSpec, section_status, validate_shared_ownership)

_STATUS_ICON = {COMPLETE: "[green]✓[/]", INVALID: "[red]✗[/]", BLOCKED: "[yellow]⧖[/]",
                "incomplete": "[dim]○[/]"}


class ConfigTreeApp(App):
    """The generic hierarchical-configuration-editor shell. `sections` is a flat tuple grouped
    by `SectionSpec.group` into sidebar branches; `commit` is the terminal node. `state` is the
    shared dict every section's `fields`/`submit`/`precheck`/`blocked` reads and writes directly
    -- entirely the consumer's vocabulary, this class never inspects its keys besides the small
    bookkeeping set `panes.py`/this module write (`_commit_errors`, `_commit_sweep_error`,
    `_commit_ok`). `banner`, if given, is shown on every screen (e.g. a --dry-run notice)."""

    # MEASURE (maintainer round 4, `measure.py`'s own docstring has the full account): every
    # TRUE-PROSE class below -- a field label, a field/business error, a blocked-reason banner, a
    # section/modal title, the persistent status line, the dry-run banner -- caps its own
    # `max-width` at the ONE named constant, so a `Static`/`Label` mounted in ANY of these roles
    # wraps at a readable measure regardless of how wide the actual terminal is (verified
    # empirically: an uncapped `Static` in a 400-column harness renders 400 columns wide, one
    # line; capped at `MEASURE`, it wraps into `ceil(len/MEASURE)` lines of <=`MEASURE` columns
    # each).
    #
    # DELIBERATELY NOT capped: `.ct-precheck-line`/`.ct-info-line` -- these carry the commit
    # boundary's own TABULAR/pre-formatted driver output (checklist rows, `$ <argv>` echoes,
    # `feature_facts.facts_block`'s own aligned blocks), the SAME genre the deleted
    # `tools/setup_tui/elements.py` explicitly exempted ("the LAST column is deliberately never
    # capped/wrapped ... wrapping it would silently split that text"); the coordinator's own
    # scope names "labels, help text, error messages, notes, refusal text" -- prose -- not driver
    # output, and wrapping a table row mid-column would be a NEW hazard, not a fix. `Input`/
    # `Checkbox`/`RadioSet` -- data-ENTRY controls, not prose -- are likewise not capped (a text
    # box legitimately wants to span available width); `ct-choice-field` (a `RadioSet`) IS capped
    # as defense-in-depth even though no current option string is long enough to need it
    # (`build_field_widget`'s own docstring: a `RadioButton`'s own caption does not wrap at all,
    # so a bounded-but-unwrapped box is the best available fallback for that widget class).
    CSS = f"""
    Tree {{ width: 40; border-right: solid $primary; }}
    ContentSwitcher {{ width: 1fr; }}
    #ct-status-line {{ background: $panel; padding: 0 1; height: auto; max-width: {MEASURE}; }}
    #ct-banner {{ background: $warning-darken-2; color: $text; padding: 0 1; max-width: {MEASURE}; }}
    .ct-section-title {{ text-style: bold; padding: 1 1 0 1; max-width: {MEASURE}; }}
    .ct-section-body {{ padding: 0 1; height: 1fr; }}
    .ct-section-buttons {{ padding: 1; height: auto; }}
    .ct-field-label {{ padding-top: 1; max-width: {MEASURE}; }}
    .ct-field-error {{ color: $error; max-width: {MEASURE}; }}
    .ct-blocked-reason {{ color: $warning; padding: 1; max-width: {MEASURE}; }}
    .ct-precheck-line, .ct-info-line {{ color: $text-muted; }}
    .ct-choice-field {{ max-width: {MEASURE}; }}
    .ct-section-description {{ color: $text-muted; padding: 0 1; max-width: {MEASURE}; }}
    .ct-field-help {{ color: $text-muted; padding: 0 0 1 0; max-width: {MEASURE}; }}
    .ct-choice-help {{ color: $text-muted; padding: 0 0 0 2; max-width: {MEASURE}; }}
    /* Round 7 (ledger row 1119, defect D9): a REAL sub-heading for a multi-group elucidation
    value (e.g. substrate's Existing-db/Dedicated-db paths) -- bold, unprefixed, distinct from
    both the section title (larger/bolder) and an ordinary labeled line (never a "Label: text"
    shape) -- so a grouped record's hierarchy is legible without diffing repeated line-prefixes. */
    .ct-elucidation-heading {{ text-style: bold; padding-top: 1; max-width: {MEASURE}; }}
    /* A `ListField`/`MultiChoiceField`'s own repeatable-row/checkbox-group widget must size to
    ITS OWN CONTENT, never `Vertical`'s own DEFAULT_CSS `height: 1fr` (an equal fractional share
    of the section body regardless of content) -- several such widgets stacked in the SAME
    `VerticalScroll` under `1fr` fight over one shared height and visually OVERLAP the instant
    any one of them (e.g. a long elucidation line, this round's own defect A fix) needs more room
    than its equal share; `height: auto` + the enclosing `VerticalScroll` is what makes "taller
    than the viewport" a SCROLL, not an overlap (verified empirically: this exact overlap, and
    its fix, both reproduced against the real principals-authority section). */
    .ct-field-group {{ height: auto; }}
    /* Round 6 (coordinator addendum): a bare Checkbox's OWN default CSS
    (`ToggleButton.DEFAULT_CSS`) draws `border: tall` -- a full top+bottom rule around EVERY
    option, a wall of borders once a catalog runs to a dozen-plus entries (otherwise Textual's
    default styling doing charity work nobody asked for). Slimmed to no per-option border at all
    (the Qt-idiom checklist look: a thin/no rule between entries, not a boxed control per row) --
    the option's own label and juxtaposed elucidation line underneath are separation enough. */
    .ct-checkbox-compact {{ border: none; padding: 0 1; }}
    /* C24/C26 (ledger row 1130's own sibling audit): the commit sweep+commit act now runs off
    the UI thread in a worker -- this is its ONLY visible chrome while running (the button's own
    label stays fixed; a disabled button alone is not a busy INDICATOR, C26's own distinction). */
    .ct-commit-busy {{ color: $warning; padding: 0 1; max-width: {MEASURE}; }}
    /* MEDIUM audit finding (ledger row 1130's own sibling audit): the live filter Input a
    large MultiChoiceField grows above `widgets.MULTICHOICE_FILTER_THRESHOLD` -- bounded at
    measure like every other data-entry control this library caps, margined off from the
    catalog below it. */
    .ct-multichoice-filter {{ max-width: {MEASURE}; margin-bottom: 1; }}
    """
    BINDINGS = [Binding("ctrl+q", "quit_app", "Quit", show=True, priority=True),
                Binding("ctrl+c", "quit_app", "Quit", show=False, priority=True),
                # ctrl+z SUSPEND (maintainer round 5, ledger row 1115: "ctrl-z suspend never
                # bound though Textual supports action_suspend_process" -- verified empirically
                # against the installed Textual version, `App.action_suspend_process` sends
                # SIGTSTP on a suspend-capable driver; a non-suspend-capable environment (this
                # harness's own headless/Pilot runs included) is a documented no-op on Textual's
                # own side, never a crash). `show=True` puts it on the Footer -- ADR-0019
                # appendix P20's own "the footer binding display is the natural, required
                # indicator surface" for a binding that changes what a keypress does.
                Binding("ctrl+z", "suspend_process", "Suspend", show=True)]

    def __init__(self, sections: "tuple[SectionSpec, ...]", commit: CommitSpec, *,
                 actions: "tuple[ActionSpec, ...]" = (), initial_state: dict | None = None,
                 banner: str | None = None, title: str = "Configuration") -> None:
        # TYPED REFUSAL AT LOAD (maintainer ruling, ADR-0019 + the maintainer's own ADR-0002
        # citation: "a duplicated mirror/projection of a value is a type error and refused on
        # TUI start"): checked BEFORE `super().__init__()` -- no Textual machinery starts at all
        # if two sections declare the same shared field, construction-time raise, the highest
        # rung of ADR-0002's loudness hierarchy.
        validate_shared_ownership(sections)
        super().__init__()
        self.sections = sections
        self.actions = actions
        self.commit_spec = commit
        self.state: dict = dict(initial_state or {})
        self.banner = banner
        self.title = title
        self._panes: dict[str, SectionPane] = {}
        self._action_panes: dict[str, ActionPane] = {}
        self._commit_pane: "CommitPane | None" = None
        self._tree_nodes: dict[str, object] = {}
        self._action_slugs: set[str] = {str(a.slug) for a in actions}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        if self.banner:
            yield Static(self.banner, id="ct-banner")
        yield Static("", id="ct-status-line")
        with Horizontal():
            tree: Tree = Tree(self.title, id="ct-tree")
            tree.root.expand()
            yield tree
            with ContentSwitcher(id="ct-switcher"):
                yield Static("Select a section on the left to begin.", id="pane-welcome")
                for action in self.actions:
                    apane = ActionPane(action, self.state)
                    self._action_panes[str(action.slug)] = apane
                    yield apane
                for spec in self.sections:
                    pane = SectionPane(spec, self.state)
                    self._panes[str(spec.slug)] = pane
                    yield pane
                self._commit_pane = CommitPane(self.commit_spec, self.sections, self.state)
                yield self._commit_pane
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one("#ct-tree", Tree)
        groups: dict[str, object] = {}
        # Action nodes (e.g. "load a configuration") mount FIRST -- the genre's own preset/
        # profile-picker convention sits above the ordinary configuration tree, reachable before
        # any section is ever visited (maintainer round 5, ledger row 1115, defect C: "usable at
        # start").
        for action in self.actions:
            group_name = str(action.group)
            branch = groups.get(group_name)
            if branch is None:
                branch = tree.root.add(group_name, expand=True)
                groups[group_name] = branch
            node = branch.add_leaf(str(action.title), data={"kind": "action", "slug": str(action.slug)})
            self._tree_nodes[str(action.slug)] = node
        for spec in self.sections:
            group_name = str(spec.group)
            branch = groups.get(group_name)
            if branch is None:
                branch = tree.root.add(group_name, expand=True)
                groups[group_name] = branch
            node = branch.add_leaf(str(spec.title), data={"kind": "section", "slug": str(spec.slug)})
            self._tree_nodes[str(spec.slug)] = node
        commit_node = tree.root.add_leaf("Commit", data={"kind": "commit"})
        self._tree_nodes["commit"] = commit_node
        self.on_model_changed()

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data or {}
        switcher = self.query_one("#ct-switcher", ContentSwitcher)
        if data.get("kind") == "section":
            slug = data["slug"]
            # Re-render on EVERY visit (never cached) -- spec §3 v2's own words for the blocked-
            # reason ("re-checked... rendered in place"): a sibling section's edit, or a prior
            # commit-sweep business-rule refusal, may have changed what THIS pane should show.
            await self._panes[slug].refresh_blocked()
            switcher.current = f"pane-{slug}"
        elif data.get("kind") == "action":
            switcher.current = f"pane-action-{data['slug']}"
        elif data.get("kind") == "commit":
            if self._commit_pane is not None and not self._commit_pane.is_committed:
                await self._commit_pane.refresh_readiness()
            switcher.current = "pane-commit"

    def on_model_changed(self) -> None:
        """Called by ANY pane after ANY field write (live, on every keystroke/toggle/choice) --
        cheap, app-wide: every tree node's status ICON and the persistent status line are
        recomputed from the CURRENT shared state, pure text updates, no widget rebuild. This is
        what makes a dependency unblock the instant its prerequisite value lands, even in a
        section pane that is not currently on screen (spec §3 v2's own acceptance bar). Action
        nodes carry no complete/incomplete concept (an immediate one-shot act, not a decision
        record) and are skipped here entirely."""
        statuses = {str(s.slug): section_status(s, self.state) for s in self.sections}
        for slug, node in self._tree_nodes.items():
            if slug == "commit" or slug in self._action_slugs:
                continue
            spec = next(s for s in self.sections if str(s.slug) == slug)
            icon = _STATUS_ICON.get(statuses[slug], "?")
            node.set_label(f"{icon} {spec.title}")
        n_complete = sum(1 for v in statuses.values() if v == COMPLETE)
        remaining = [slug for slug, v in statuses.items() if v != COMPLETE]
        line = self.query_one("#ct-status-line", Static)
        if remaining:
            line.update(f"{n_complete}/{len(statuses)} sections complete -- remaining: {', '.join(remaining)}")
        else:
            line.update(f"{n_complete}/{len(statuses)} sections complete -- ready to commit.")

    async def reload_all_panes(self) -> None:
        """`ActionPane`'s own post-apply hook (its module docstring's "usable at start" contract):
        recomposes every ALREADY-MOUNTED `SectionPane` so a value the action just seeded into the
        shared `state` (e.g. a loaded template's per-section defaults) renders as that section's
        own CURRENT live value immediately -- on the SAME visit an operator applies a preset,
        never merely the next time each section happens to be (re-)selected."""
        for pane in self._panes.values():
            await pane.refresh_blocked()

    def action_quit_app(self) -> None:
        self.exit(return_code=130)

    def on_button_pressed(self, event) -> None:
        if getattr(event.button, "id", None) == "ct-finish":
            code = 0 if self.state.get("_commit_ok", True) else 2
            self.exit(return_code=code)
