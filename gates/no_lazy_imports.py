#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-02T01:30:29Z
#   last-change: 2026-07-02T01:30:29Z
#   contributors: 306d4c8f/main
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
        if not any(part in EXCLUDE_PARTS for part in p.parts):
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
