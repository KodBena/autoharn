#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T20:10:34Z
#   last-change: 2026-07-19T20:10:34Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""gates/setup_tui_purity_gate.py -- the §2.8 AST purity gate (design/FABLE-SETUP-TUI-PURE-CORE-
SPEC.md §2.8, commission ledger rows 1823 point 2 / 1825 / 1835): "a census-registered gate
asserts, at the AST level over tools/setup_tui/, that calls to the three runner choke points
(run_command, start_background, write_file) appear ONLY in the commit-executor module and the
rehearsal module's declared exception -- a screen that acquires a direct effect call fails the
gate."

WHAT COUNTS AS THE DECLARED EXCEPTION SITE (named precisely, not "screens.py wholesale"):
`tools/setup_tui/commit_executor.py` may call all three choke points anywhere (it IS the one
commit boundary). `tools/setup_tui/screens.py`'s `screen_rehearsal` function -- and ONLY that
function -- may call them too (the P9-rule-4-shaped Workspace exception, spec §2.5/§3: a live
effect on a scratch target, mid-flow, with witnessed zero-residue teardown). Every OTHER function
in EVERY OTHER module under `tools/setup_tui/` is checked and must be clean.

DETECTION (AST, not text-grep -- a grep would false-positive on the docstrings/comments this very
module and screens.py itself carry, which mention "run_command" and "write_file" by name in prose):
walks every `ast.Call` node, matching either a bare-name call (`run_command(...)`, the shape every
converted call site now uses after `from tools.setup_tui.runner import run_command`) or an
attribute call (`runner.run_command(...)`, the shape `commit_executor.py` and `screen_rehearsal`
itself use) whose function name is one of the three. Each match is attributed to its ENCLOSING
function (the innermost `ast.FunctionDef`/`ast.AsyncFunctionDef` containing it, found via a parent
map built once per module) -- a call at module level (no enclosing function) is always a
violation, never exempt.

Exit 0 clean; exit 1 listing every violation as `path:line: <call text> (inside <function or
module-level>)`. The negative self-check (a synthetic violation must fail red) lives in
seen-red/setup-tui-purity-gate/run_fixtures.py, which imports and calls this module's own
`scan_file`/`check_tree` directly against synthetic source text -- never touching the real tree.

Usage: python3 gates/setup_tui_purity_gate.py
Lazy imports banned."""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(ROOT, "tools", "setup_tui")

FORBIDDEN_NAMES = {"run_command", "start_background", "write_file"}

# (relative filename under tools/setup_tui/) -> set of function qualnames permitted to call a
# choke point directly, OR the sentinel "*" meaning "the whole module is exempt" (commit_executor
# only -- it IS the boundary). A module/function NOT listed here gets NO exemption at all.
EXEMPT: dict[str, set[str]] = {
    "commit_executor.py": {"*"},
    "screens.py": {"screen_rehearsal"},
}


class _ParentFinder(ast.NodeVisitor):
    """Builds `node -> nearest enclosing FunctionDef/AsyncFunctionDef (or None for module-level)`
    for every node in a tree, in one pass -- the mechanism `check_tree` uses to attribute a call
    to the function it lexically sits inside, regardless of nesting depth (a call inside a nested
    closure, a comprehension, a `with`/`try` block, etc. -- all of those still resolve to their
    nearest enclosing `def`, not a synthetic new scope this gate would have to special-case)."""

    def __init__(self) -> None:
        self.owner: dict[ast.AST, "ast.FunctionDef | ast.AsyncFunctionDef | None"] = {}

    def visit(self, node: ast.AST, current: "ast.FunctionDef | ast.AsyncFunctionDef | None" = None) -> None:
        self.owner[node] = current
        next_current = current
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            next_current = node
        for child in ast.iter_child_nodes(node):
            self.visit(child, next_current)


def _call_name(node: ast.Call) -> str | None:
    """The forbidden-set-comparable name of a call's function, or None if it does not match the
    shape of either call style this gate checks (bare name, or `<anything>.name`)."""
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return None


def check_tree(tree: ast.AST, filename: str) -> list[str]:
    """Returns a list of violation strings (`filename:line: <call source> (inside <qualname>)`)
    for `tree`, applying `EXEMPT`'s per-file/per-function allowance. `filename` is the base name
    used to look up `EXEMPT` (e.g. `"screens.py"`) -- callers pass whatever key they want checked
    against, so a fixture can probe a SYNTHETIC tree under a chosen filename without touching the
    real files."""
    exempt_functions = EXEMPT.get(filename, set())
    if "*" in exempt_functions:
        return []

    finder = _ParentFinder()
    finder.visit(tree)

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name not in FORBIDDEN_NAMES:
            continue
        owner = finder.owner.get(node)
        qualname = owner.name if owner is not None else "<module level>"
        if qualname in exempt_functions:
            continue
        line = getattr(node, "lineno", "?")
        try:
            src = ast.unparse(node)
        except Exception:  # noqa: BLE001 -- unparse is best-effort for the message only
            src = name
        violations.append(f"{filename}:{line}: {src}  (inside {qualname})")
    return violations


def scan_file(path: str) -> list[str]:
    """Reads and AST-parses the REAL file at `path`, checked against `EXEMPT` keyed by its base
    filename. A syntax error in the file is itself reported as a violation line (never silently
    skipped -- an unparseable module cannot be honestly certified clean)."""
    filename = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        return [f"{filename}: SyntaxError, cannot check purity: {exc}"]
    return check_tree(tree, filename)


def scan_package(package_dir: str = PACKAGE_DIR) -> list[str]:
    violations: list[str] = []
    for name in sorted(os.listdir(package_dir)):
        if not name.endswith(".py"):
            continue
        violations.extend(scan_file(os.path.join(package_dir, name)))
    return violations


def main() -> int:
    violations = scan_package()
    if violations:
        print(f"setup_tui_purity_gate: {len(violations)} violation(s) -- a runner choke point "
              f"(run_command/start_background/write_file) was called outside "
              f"commit_executor.py or screens.py's screen_rehearsal:")
        for v in violations:
            print(f"  {v}")
        return 1
    print("setup_tui_purity_gate: clean ✓ -- every runner choke-point call under "
          "tools/setup_tui/ is confined to commit_executor.py or screen_rehearsal "
          "(design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.8)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
