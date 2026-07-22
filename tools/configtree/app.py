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
`ContentSwitcher` (never rebuilt on selection) -- switching away and back preserves whatever the
operator typed, Textual's own screen-stack trick generalized to a set of always-mounted panes
instead of a linear stack of pushed ones (`panes.SectionPane`'s own docstring)."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import ContentSwitcher, Footer, Header, Static, Tree

from tools.configtree.panes import CommitPane, SectionPane
from tools.configtree.spec import BLOCKED, COMPLETE, INVALID, CommitSpec, SectionSpec, section_status

_STATUS_ICON = {COMPLETE: "[green]✓[/]", INVALID: "[red]✗[/]", BLOCKED: "[yellow]⧖[/]",
                "incomplete": "[dim]○[/]"}


class ConfigTreeApp(App):
    """The generic hierarchical-configuration-editor shell. `sections` is a flat tuple grouped
    by `SectionSpec.group` into sidebar branches; `commit` is the terminal node. `state` is the
    shared dict every section's `fields`/`submit`/`precheck`/`blocked` reads and writes --
    entirely the consumer's vocabulary, this class never inspects its keys besides the two
    bookkeeping keys it itself writes (`_section_done`, `_section_errors`) and reads
    (`_commit_ok`). `banner`, if given, is shown on every screen (e.g. a --dry-run notice)."""

    CSS = """
    Tree { width: 40; border-right: solid $primary; }
    ContentSwitcher { width: 1fr; }
    #ct-status-line { background: $panel; padding: 0 1; height: 1; }
    #ct-banner { background: $warning-darken-2; color: $text; padding: 0 1; }
    .ct-section-title { text-style: bold; padding: 1 1 0 1; }
    .ct-section-body { padding: 0 1; height: 1fr; }
    .ct-section-buttons { padding: 1; height: auto; }
    .ct-field-label { padding-top: 1; }
    .ct-field-error { color: $error; }
    .ct-blocked-reason { color: $warning; padding: 1; }
    .ct-precheck-line, .ct-info-line { color: $text-muted; }
    """
    BINDINGS = [Binding("ctrl+q", "quit_app", "Quit", show=True, priority=True),
                Binding("ctrl+c", "quit_app", "Quit", show=False, priority=True)]

    def __init__(self, sections: "tuple[SectionSpec, ...]", commit: CommitSpec, *,
                 initial_state: dict | None = None, banner: str | None = None,
                 title: str = "Configuration") -> None:
        super().__init__()
        self.sections = sections
        self.commit_spec = commit
        self.state: dict = dict(initial_state or {})
        self.banner = banner
        self.title = title
        self._panes: dict[str, SectionPane] = {}
        self._commit_pane: "CommitPane | None" = None
        self._tree_nodes: dict[str, object] = {}

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
                for spec in self.sections:
                    pane = SectionPane(spec, self.state, self._on_section_saved)
                    self._panes[str(spec.slug)] = pane
                    yield pane
                self._commit_pane = CommitPane(self.commit_spec, self.sections, self.state,
                                                self._on_committed)
                yield self._commit_pane
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one("#ct-tree", Tree)
        groups: dict[str, object] = {}
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
        self._refresh_status()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        data = event.node.data or {}
        switcher = self.query_one("#ct-switcher", ContentSwitcher)
        if data.get("kind") == "section":
            switcher.current = f"pane-{data['slug']}"
        elif data.get("kind") == "commit":
            switcher.current = "pane-commit"

    def _on_section_saved(self, spec: SectionSpec, *, ok: bool) -> None:
        slug = str(spec.slug)
        done = self.state.setdefault("_section_done", set())
        errors = self.state.setdefault("_section_errors", {})
        if ok:
            done.add(slug)
            errors.pop(slug, None)
        else:
            errors[slug] = True
        # A save can unblock (or re-block) ANY other section (spec §3 v2: dependency edges are
        # data, checked against the CURRENT state) -- every other pane's blocked-reason and every
        # tree node's status is re-derived here, not only this one's.
        for other_slug, pane in self._panes.items():
            if other_slug != slug:
                pane.refresh_blocked()
        if self._commit_pane is not None:
            self._commit_pane.refresh_readiness()
        self._refresh_status()

    def _on_committed(self, ok: bool) -> None:
        self._refresh_status()

    def _refresh_status(self) -> None:
        statuses = {str(s.slug): section_status(s, self.state) for s in self.sections}
        for slug, node in self._tree_nodes.items():
            if slug == "commit":
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

    def action_quit_app(self) -> None:
        self.exit(return_code=130)

    def on_button_pressed(self, event) -> None:
        if getattr(event.button, "id", None) == "ct-finish":
            code = 0 if self.state.get("_commit_ok", True) else 2
            self.exit(return_code=code)
