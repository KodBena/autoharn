#!/usr/bin/env python3
"""no_lazy_imports.py — mechanical gate for the project law: LAZY IMPORTS ARE BANNED.

Law (CLAUDE.md, maintainer edict 2026-07-02): every `import` executes at module import
time. An `import` statement anywhere inside a function or method body is a violation —
no allowlist. Module-level imports under `if`/`try` still execute at import time and are
legal (they are eager); `if TYPE_CHECKING:` blocks never execute at runtime and are
legal wherever they are. Class-body imports execute at class-definition time (module
import) and are legal, if odd.

Exit 0 with no output when clean; exit 1 listing every violation as
`path:line: import <names>  (inside <qualname>)` otherwise.

READ MODE (gates-staged-vs-tree-blindness, ledger row 1234): this is a content-checking gate --
whether a file carries a lazy import is a property of its BYTES, not its filename -- so, like
gates/deep_walk_recursion_guard.py (this class's own pattern exemplar), it reads each file's
STAGED bytes by default (gates/_staged_read.py's `read_source_text`), falling back to the
working-tree file only when a path is not staged at all (untracked files, or the tempfile paths
this module's own seen-red-family fixture drives it against). Without this, staging a lazy
import and then restoring a clean file in the tree (without re-staging) would pass this gate
while the commit still embeds the violation -- the exact silent-pass shape
deep_walk_recursion_guard.py's own "Finding A" first closed for one gate; this is the same class,
closed here for this one. Pass `--tree` to force the working-tree read unconditionally instead.

Usage:
    python3 tools/no_lazy_imports.py [root] [--tree]   # default: repo root, git-tracked *.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _staged_read import read_source_text, run_git  # noqa: E402  (gates/_staged_read.py, shared home)

REPO = Path(__file__).resolve().parents[1]

# trees never subject to the gate: archived evidence and third-party/scratch dirs
EXCLUDE_PARTS = {"claude-ephemera", ".staging", "node_modules", ".venv", "venvs",
                 "__pycache__", ".git"}

# specific VENDORED third-party trees, excluded by full relative path prefix rather than a
# generic directory-name component (EXCLUDE_PARTS above is for whole classes of dependency
# tree -- venvs, node_modules -- never authored by a contributor here; this is the same
# exclusion class applied to a single, named, provenance-recorded vendor drop). CLAUDE.md's
# "no allowlist" text bans allowlisting a LAZY IMPORT a contributor writes in house code; it
# says nothing about linting code this project does not author and is committed not to edit
# (ADR-0004 read-only-vendor discipline -- see the named PROVENANCE.md at each path below).
# Each entry: the vendored directory, and why editing it to satisfy this gate is foreclosed.
#   tools/makespan-scheduler/ -- vendored 2026-07-14 (work item makespan-scheduler-vendoring;
#   tools/makespan-scheduler/PROVENANCE.md), byte-for-byte from an external side project;
#   independently patching its test suite's imports to satisfy this gate would silently
#   diverge the vendored copy from its recorded source commit, exactly what PROVENANCE.md's
#   own read-only-source rule forbids -- a fix belongs upstream, re-vendored here, never
#   patched in place.
#
# GENERAL FIX NAMED AND DEFERRED, NOT SKIPPED (an out-of-frame hack-rationalization audit,
# this same commission, asked directly whether a single self-declaring "this is a vendored
# tree" marker convention -- e.g. a PROVENANCE.md sibling this and every other gate could
# check for, rather than N separately hand-maintained path lists across gates/ -- would be the
# sounder fix than this per-gate tuple). This is the FIRST vendored tree in this repository;
# ADR-0011's own doctrine is to mechanize on the SECOND recurring instance of a shape, not the
# first (Rule 2: a recurrence converts to a mechanism). Building a shared marker convention now,
# for a population of one, would be exactly the "for now"/scale pre-emption ADR-0012 P7/P8/P9
# warn against in the other direction -- so the hand-typed tuple is deliberately the honest,
# minimal-for-now form, on the explicit condition that the SECOND vendored tree is the trigger
# to replace this (and doc_attestation_presence.py's parallel exclusion) with one shared
# mechanism, not a third hand-typed list.
EXCLUDE_PATH_PREFIXES = ("tools/makespan-scheduler/",)

_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _names(node: ast.Import | ast.ImportFrom) -> str:
    if isinstance(node, ast.ImportFrom):
        mod = "." * node.level + (node.module or "")
        return f"from {mod} import " + ", ".join(a.name for a in node.names)
    return "import " + ", ".join(a.name for a in node.names)


def violations_in(path: Path, base: Path = REPO, use_tree: bool = False) -> list[str]:
    try:
        tree = ast.parse(read_source_text(path, use_tree=use_tree), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"{path}:0: UNPARSEABLE ({e.__class__.__name__}) — gate cannot certify this file"]

    out: list[str] = []

    # Report paths relative to `base` (the scanned root), not the module-level REPO constant:
    # main()'s [root] argument mode may scan a directory outside this repo entirely, and
    # path.relative_to(REPO) raised ValueError there instead of reporting cleanly (finding 52).
    try:
        display = path.relative_to(base)
    except ValueError:
        display = path

    def walk(node: ast.AST, func_stack: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _FUNCS):
                walk(child, func_stack + (child.name,))
            elif isinstance(child, (ast.Import, ast.ImportFrom)) and func_stack:
                out.append(f"{display}:{child.lineno}: {_names(child)}"
                           f"  (inside {'.'.join(func_stack)})")
            else:
                walk(child, func_stack)

    walk(tree, ())
    return out


def tracked_py_files(root: Path) -> list[Path]:
    """Every git-tracked *.py under `root`, filtered by EXCLUDE_*. Routed through
    `_staged_read.run_git` (2026-07-26, gates-staged-vs-tree-blindness follow-up finding) rather
    than a bare `subprocess.run(["git", ...])`, so an inherited GIT_DIR/GIT_WORK_TREE/GIT_PREFIX/
    GIT_COMMON_DIR (a live pre-commit hook running inside a git WORKTREE) cannot silently
    misresolve `-C root` the same way it demonstrably can for the staged-blob read this module's
    READ MODE already fixed."""
    r = run_git(["-C", str(root), "ls-files", "*.py"],
                capture_output=True, text=True, check=True)
    files = []
    for line in r.stdout.splitlines():
        p = root / line
        if any(part in EXCLUDE_PARTS for part in p.parts):
            continue
        if any(line.startswith(prefix) for prefix in EXCLUDE_PATH_PREFIXES):
            continue
        files.append(p)
    return files


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--tree"]
    use_tree = "--tree" in sys.argv[1:]
    root = Path(argv[0]).resolve() if argv else REPO
    bad: list[str] = []
    for f in tracked_py_files(root):
        bad.extend(violations_in(f, base=root, use_tree=use_tree))
    if bad:
        print(f"LAZY-IMPORT VIOLATIONS ({len(bad)}) — banned by CLAUDE.md law 2026-07-02:")
        print("\n".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
