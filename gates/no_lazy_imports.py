#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-02T01:30:29Z
#   last-change: 2026-07-14T01:56:02Z
#   contributors: 306d4c8f/main, a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""no_lazy_imports.py — mechanical gate for the project law: LAZY IMPORTS ARE BANNED.

Law (CLAUDE.md, maintainer edict 2026-07-02): every `import` executes at module import
time. An `import` statement anywhere inside a function or method body is a violation —
no allowlist. Module-level imports under `if`/`try` still execute at import time and are
legal (they are eager); `if TYPE_CHECKING:` blocks never execute at runtime and are
legal wherever they are. Class-body imports execute at class-definition time (module
import) and are legal, if odd.

Exit 0 with no output when clean; exit 1 listing every violation as
`path:line: import <names>  (inside <qualname>)` otherwise.

Usage:
    python3 tools/no_lazy_imports.py [root]          # default: repo root, git-tracked *.py
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

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


def violations_in(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as e:
        return [f"{path}:0: UNPARSEABLE ({e.__class__.__name__}) — gate cannot certify this file"]

    out: list[str] = []

    def walk(node: ast.AST, func_stack: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _FUNCS):
                walk(child, func_stack + (child.name,))
            elif isinstance(child, (ast.Import, ast.ImportFrom)) and func_stack:
                out.append(f"{path.relative_to(REPO)}:{child.lineno}: {_names(child)}"
                           f"  (inside {'.'.join(func_stack)})")
            else:
                walk(child, func_stack)

    walk(tree, ())
    return out


def tracked_py_files(root: Path) -> list[Path]:
    r = subprocess.run(["git", "-C", str(root), "ls-files", "*.py"],
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
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO
    bad: list[str] = []
    for f in tracked_py_files(root):
        bad.extend(violations_in(f))
    if bad:
        print(f"LAZY-IMPORT VIOLATIONS ({len(bad)}) — banned by CLAUDE.md law 2026-07-02:")
        print("\n".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
