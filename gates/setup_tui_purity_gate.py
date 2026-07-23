#!/usr/bin/env python3
"""gates/setup_tui_purity_gate.py -- REWRITTEN for the configtree-library rebuild
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §2/§6). THREE invariants, all AST-level (never a text
grep -- a grep would false-positive on this module's own docstrings):

1. **No `print(`/`input(`/`sys.stdin`/`sys.stdout` under `tools/setup_tui/`** except (a) the app
   glue (`tools/setup_tui/tui_app.py`, and `tools/configtree/` itself -- the Textual UI layer
   legitimately owns terminal I/O) and (b) `tools/setup_tui/app.py`'s own `--from-config`
   headless reporter and pre-UI refusal diagnostics (there is no other UI for that path). Every
   OTHER module (the core: `steps*.py`, `plan.py`, `checklist.py`, `commit_executor.py`,
   `runner.py`'s own child-output passthrough excepted below, `content.py`, `idtypes.py`, the
   surviving helper modules) must not touch the terminal directly -- a section's `submit`/
   `fields` communicates only via `SectionResult`/field specs, never a bare print. `runner.py`
   keeps its own narrow exemption: it is the child-process-output passthrough choke point
   (`run_command`'s streamed stdout), unrelated to operator-facing content.
2. **The core imports nothing from the app package** (`tools/setup_tui/tui_app.py`; and
   `tools/configtree/` as a whole is never imported by anything under `tools/setup_tui/` except
   `tui_app.py` -- library discipline, one-way, design/FABLE-SETUP-TUI-REBUILD-SPEC.md §6: "the
   library never imports from the consumer" is the mirror-image check, PROVEN here from the
   consumer's side). Checked over the REAL import graph (`ast.parse` every `.py` file under
   `tools/setup_tui/`), not a synthetic tree -- there is exactly one legitimate importer of
   `tui_app`/`configtree.app`/`configtree.widgets`/`configtree.panes` (`app.py`'s own guarded
   `try/except ImportError`, and `tui_app.py` itself), and this gate asserts no other module
   joins that set. Importing the library's own TOP-LEVEL (`tools.configtree` -- `SectionSpec`/
   `TextField`/...) is NOT flagged: every `steps_*.py` module needs those types to declare its
   section data WITHOUT paying textual's import cost -- exactly what makes `--from-config`
   genuinely textual-free (`tools/configtree/__init__.py`'s own docstring names the same split).

3. **No raw `Vertical`/`Horizontal`/`VerticalScroll` instantiation in a `tools/configtree/`
   content path outside `layout_primitives.ContentVertical`/`ContentHorizontal` (ledger row 1139,
   TYPE half).** A raw Textual `Vertical`/`Horizontal` defaults to `height: 1fr` -- an equal
   fractional share of whatever ancestor eventually resolves it, computed independent of actual
   content size; nested inside a `height: auto` chain this produces the "container claims height
   decoupled from content size" class this project has now patched locally three times (round-5
   overlap, cycle-3 starvation, cycle-6 phantom expanse -- `layout_primitives.py`'s own module
   docstring has the full account). `layout_primitives.ContentVertical`/`ContentHorizontal` fix
   this BY CONSTRUCTION (`height: auto` in their own `DEFAULT_CSS`); every content-path container
   in this package must be built from one of those two, never a raw `textual.containers.Vertical`/
   `Horizontal` call, and never a class declared `(Vertical)`/`(Horizontal)` outside the small,
   individually-justified `LAYOUT_EXCEPTIONS`/`LAYOUT_BASE_CLASS_EXCEPTIONS` below -- the genuinely
   fr-intended shells (a `ContentSwitcher` pane itself, the top-level split columns, an
   independently-scrollable column/section-body/modal-body region). `VerticalScroll` is not
   restricted the same way -- every current use of it in this package IS one of those declared
   scroll shells; the enumeration below is where that judgment is made explicit, checked against
   the real source, rather than silently assumed forever.

Exit 0 clean; exit 1 listing every violation. The negative self-check (a synthetic violation of
each detector must fail red) lives in seen-red/setup-tui-purity-gate/run_fixtures.py, which calls
this module's own `check_print_or_io`/`check_core_imports_app`/`check_raw_layout_containers`
directly against synthetic source text -- never touching the real tree for the red leg.

Usage: python3 gates/setup_tui_purity_gate.py
Lazy imports are banned."""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(ROOT, "tools", "setup_tui")

# Detection 1's per-file exemption -- "*" means the whole file is exempt.
PRINT_EXEMPT: dict[str, set[str]] = {
    "tui_app.py": {"*"},      # the Textual UI layer's own entry-point glue
    "runner.py": {"*"},       # child-process-output passthrough choke point
    "app.py": {"_run_from_config", "main", "_check_config_flags", "_terminate_boundary_proc",
               "_handle_sigterm", "_install_sigterm_handler", "_run_textual",
               "_check_adr_synopsis_freshness",
               "<module level>"},  # the --from-config headless reporter + the pre-UI refusal
                                    # diagnostics (bad flags, textual-missing, SIGTERM cleanup
                                    # notices, the ADR-synopsis freshness refusal/warning --
                                    # ledger row 1130's own driftability commission, checked at
                                    # TUI start before either run mode begins) -- fire before/
                                    # outside any Textual screen.
    "feature_facts.py": {"<module level>"},  # `python3 -m tools.setup_tui.feature_facts`'s own
                                    # standalone drift-check CLI entry point.
}

# Detection 2: the app package is `tools.configtree.app`/`tools.configtree.widgets`/
# `tools.configtree.panes` specifically (the modules that import `textual`) -- NOT the whole
# `tools.configtree` package, whose top-level (`fields.py`/`spec.py`/`ids.py`) every `steps_*.py`
# module legitimately imports to DECLARE its section data without paying textual's import cost.
APP_SUBMODULES: set[str] = {"tools.configtree.app", "tools.configtree.widgets", "tools.configtree.panes"}
# `tui_app.py` is the app package's own entry point; `app.py` is the CLI dispatcher that
# guardedly imports it (`try: from tools.setup_tui import tui_app except ImportError: ...`) to
# choose the Textual face when available -- legitimate at the CLI-dispatch layer, unlike a
# business-logic `steps_*.py` module reaching into the UI.
CORE_MAY_IMPORT_APP: set[str] = {"tui_app.py", "app.py"}

_IO_ATTR_BASES = {"sys": {"stdin", "stdout"}}

# Detection 3 (ledger row 1139, TYPE half) scans `tools/configtree/` -- the package the raw-
# container hazard actually lives in, not `tools/setup_tui/` (which never composes a Textual
# container directly). `layout_primitives.py` is exempt from its OWN rule (it is where
# `ContentVertical`/`ContentHorizontal` themselves subclass the raw containers).
CONFIGTREE_DIR = os.path.join(ROOT, "tools", "configtree")
LAYOUT_PRIMITIVES_FILE = "layout_primitives.py"

# `class Foo(Vertical)`/`class Foo(Horizontal)` declarations exempt from Detection 3: these are
# genuinely fr-intended SHELLS, not content groupers -- `SectionPane`/`ActionPane`/`CommitPane`
# are the ONE widget `app.py`'s `ContentSwitcher` swaps in for the currently-selected node, and a
# `ContentSwitcher` child legitimately wants the switcher's own full available height (Textual's
# default `1fr`), the same way the switcher itself does (`ContentSwitcher { width: 1fr; }` in
# `app.py`'s own CSS). `ContentVertical`/`ContentHorizontal` are the primitive's own base
# definitions -- exempt from a rule they exist to enforce on everything ELSE.
LAYOUT_BASE_CLASS_EXCEPTIONS: set[str] = {
    "SectionPane", "ActionPane", "CommitPane", "ContentVertical", "ContentHorizontal",
}

# Raw call-site exceptions for Detection 3, keyed by container name -> the set of `classes`/`id`
# CONSTANT string values that mark a declared, individually-justified fr-intended shell. Anything
# else constructed via a raw `Vertical(`/`Horizontal(`/`VerticalScroll(` call is a violation.
#   Horizontal:
#     "ct-split"      -- the wide-layout two-column split (`panes.SectionPane`/`actions.
#                        ActionPane`'s own control/help divide, ledger row 1138) -- genuinely
#                        wants an equal fractional height share of its pane.
#     "ct-app-split"  -- `app.py`'s own top-level Tree|ContentSwitcher split -- fills the whole
#                        screen below the header/banner/status line, always.
#   VerticalScroll:
#     "ct-controls-col", "ct-help-col" -- the wide layout's own two independently-scrollable
#                        columns (ledger row 1138) -- each is a genuine SCROLL REGION, not a
#                        content grouper; it earns its own height from the split above it and
#                        scrolls its own overflow.
#     "ct-section-body" -- the narrow-layout equivalent (one scroll region instead of two).
#     "ct-modal-body"   -- `AddItemModal`'s own top-level scroll shell (cycle-3 fix round, ledger
#                        row 1136's "MODAL OVERFLOW" fix) -- same genre, a modal's own content can
#                        exceed the screen and must scroll, never silently truncate.
LAYOUT_EXCEPTIONS: dict[str, set[str]] = {
    "Horizontal": {"ct-split", "ct-app-split"},
    "VerticalScroll": {"ct-controls-col", "ct-help-col", "ct-section-body", "ct-modal-body"},
    "Vertical": set(),  # no raw `Vertical(...)` CALL is exempt -- every content grouper migrates
}
RAW_LAYOUT_CONTAINERS: set[str] = {"Vertical", "Horizontal", "VerticalScroll"}


def _iter_py_files(package_dir: "str | None" = None) -> "list[str]":
    out = []
    for dirpath, dirnames, filenames in os.walk(package_dir or PACKAGE_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__" and d != "data"]
        for fn in filenames:
            if fn.endswith(".py"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


class _ParentFinder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.owner: dict[ast.AST, "ast.FunctionDef | ast.AsyncFunctionDef | None"] = {}

    def visit(self, node: ast.AST, current=None) -> None:
        self.owner[node] = current
        nxt = current
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nxt = node
        for child in ast.iter_child_nodes(node):
            self.visit(child, nxt)


def check_print_or_io(tree: ast.AST, filename: str) -> "list[str]":
    """Detection 1. Flags a bare `print(...)` call, and `sys.stdin`/`sys.stdout` attribute
    access, attributed to its enclosing function (module-level if none)."""
    exempt = PRINT_EXEMPT.get(filename, set())
    if "*" in exempt:
        return []
    finder = _ParentFinder()
    finder.visit(tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        hit = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("print", "input"):
            hit = f"{node.func.id}(...)"
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            allowed_attrs = _IO_ATTR_BASES.get(node.value.id)
            if allowed_attrs and node.attr in allowed_attrs:
                hit = f"{node.value.id}.{node.attr}"
        if hit is None:
            continue
        owner = finder.owner.get(node)
        qualname = owner.name if owner is not None else "<module level>"
        if qualname in exempt:
            continue
        line = getattr(node, "lineno", "?")
        violations.append(f"{filename}:{line}: {hit}  (inside {qualname})")
    return violations


def check_core_imports_app(tree: ast.AST, filename: str) -> "list[str]":
    """Detection 2. Flags an import of `tools.configtree.app`/`.widgets`/`.panes` (the
    textual-dependent app submodules -- see `APP_SUBMODULES`'s own docstring above), or of
    `tools.setup_tui.tui_app`, in any module not in `CORE_MAY_IMPORT_APP`."""
    if filename in CORE_MAY_IMPORT_APP:
        return []
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in APP_SUBMODULES:
                    violations.append(f"{filename}:{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in APP_SUBMODULES:
                violations.append(f"{filename}:{node.lineno}: from {mod} import ...")
            if mod == "tools.setup_tui" and any(a.name == "tui_app" for a in node.names):
                violations.append(f"{filename}:{node.lineno}: from tools.setup_tui import tui_app")
    return violations


def _const_str_kwarg(call: ast.Call, name: str) -> "str | None":
    for kw in call.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
    return None


def check_raw_layout_containers(tree: ast.AST, filename: str) -> "list[str]":
    """Detection 3 (ledger row 1139, TYPE half -- see this module's own docstring). Flags:
      (a) a class declared `(Vertical)`/`(Horizontal)` whose name is not in
          `LAYOUT_BASE_CLASS_EXCEPTIONS`;
      (b) a raw `Vertical(`/`Horizontal(`/`VerticalScroll(` CALL whose `classes=`/`id=` constant
          string is not one of `LAYOUT_EXCEPTIONS[container]`.
    `layout_primitives.py` itself is exempt (it is where `ContentVertical`/`ContentHorizontal`
    subclass the raw containers in the first place -- flagging that would be flagging the fix)."""
    if filename == LAYOUT_PRIMITIVES_FILE:
        return []
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id in RAW_LAYOUT_CONTAINERS:
                    if node.name not in LAYOUT_BASE_CLASS_EXCEPTIONS:
                        violations.append(
                            f"{filename}:{node.lineno}: class {node.name}({base.id}) -- raw "
                            f"fr-default base class outside LAYOUT_BASE_CLASS_EXCEPTIONS; use "
                            f"layout_primitives.Content{base.id} instead")
            continue
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in RAW_LAYOUT_CONTAINERS:
            container = node.func.id
            marker = _const_str_kwarg(node, "classes") or _const_str_kwarg(node, "id")
            allowed = LAYOUT_EXCEPTIONS.get(container, set())
            if marker in allowed:
                continue
            violations.append(
                f"{filename}:{node.lineno}: raw {container}(...) (classes/id={marker!r}) -- not "
                f"a declared LAYOUT_EXCEPTIONS shell; use layout_primitives.Content{container} "
                f"instead")
    return violations


def scan_file(path: str) -> "list[str]":
    """Detections 1+2, over `tools/setup_tui/` (PACKAGE_DIR) only."""
    filename = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=path)
    return check_print_or_io(tree, filename) + check_core_imports_app(tree, filename)


def scan_configtree_file(path: str) -> "list[str]":
    """Detection 3 only, over `tools/configtree/` -- kept as its OWN scan (never folded into
    `scan_file`'s detections 1/2, which are specifically about `tools/setup_tui/`'s core-vs-app
    boundary and key their exemption dicts by basename; `tools/configtree/app.py` and
    `tools/setup_tui/app.py` share a basename, and running detections 1/2 against the former under
    the LATTER's own exemptions would be a category error, not a real check)."""
    filename = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=path)
    return check_raw_layout_containers(tree, filename)


def main() -> int:
    violations: list[str] = []
    for path in _iter_py_files():
        violations.extend(scan_file(path))
    for path in _iter_py_files(CONFIGTREE_DIR):
        violations.extend(scan_configtree_file(path))
    if violations:
        print("setup_tui_purity_gate: VIOLATIONS FOUND:")
        for v in violations:
            print(f"  {v}")
        return 1
    print("setup_tui_purity_gate: clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
