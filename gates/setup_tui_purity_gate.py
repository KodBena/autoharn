#!/usr/bin/env python3
"""gates/setup_tui_purity_gate.py -- REWRITTEN for the configtree-library rebuild
(design/FABLE-SETUP-TUI-REBUILD-SPEC.md §2/§6). Two invariants, both AST-level (never a text
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

Exit 0 clean; exit 1 listing every violation. The negative self-check (a synthetic violation of
each detector must fail red) lives in seen-red/setup-tui-purity-gate/run_fixtures.py, which calls
this module's own `check_print_or_io`/`check_core_imports_app` directly against synthetic source
text -- never touching the real tree for the red leg.

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
               "<module level>"},  # the --from-config headless reporter + the pre-UI refusal
                                    # diagnostics (bad flags, textual-missing, SIGTERM cleanup
                                    # notices) -- fire before/outside any Textual screen.
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


def _iter_py_files() -> "list[str]":
    out = []
    for dirpath, dirnames, filenames in os.walk(PACKAGE_DIR):
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


def scan_file(path: str) -> "list[str]":
    filename = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=path)
    return check_print_or_io(tree, filename) + check_core_imports_app(tree, filename)


def main() -> int:
    violations: list[str] = []
    for path in _iter_py_files():
        violations.extend(scan_file(path))
    if violations:
        print("setup_tui_purity_gate: VIOLATIONS FOUND:")
        for v in violations:
            print(f"  {v}")
        return 1
    print("setup_tui_purity_gate: clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
