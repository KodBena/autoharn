#!/usr/bin/env python3
"""seen-red/setup-tui-purity-gate/run_fixtures.py -- both-polarity proof of the REWRITTEN
gates/setup_tui_purity_gate.py (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §2/§6, the 2026-07-22
wholesale rebuild onto tools/configtree): its two detectors (no print/input/stdin/stdout outside
the app package + the --from-config reporter; the core imports nothing from the app package),
plus a real-tree GREEN leg (the actual gate, run against the actual package, is clean today).

Cases:
  1. `check_print_or_io` -- RED on a synthetic `steps_boundary.py`-named tree with a bare
     `print(...)` inside a function; GREEN once the same call sits in an exempted file
     (`runner.py`).
  2. `check_print_or_io` -- RED on `sys.stdout`/`sys.stdin` attribute access in a non-exempt file.
  3. `check_core_imports_app` -- RED on a synthetic `steps.py`-named tree importing
     `tools.configtree.app`; GREEN for the library's top-level types (`SectionSpec`/`TextField`,
     every `steps_*.py` module's own real import shape); GREEN for the same textual-dependent
     import inside `tui_app.py` (the one legitimate importer).
  4. Real-tree leg: `gates/setup_tui_purity_gate.main()` against the ACTUAL `tools/setup_tui/`
     tree exits 0 today (a negative control that the real package is clean, not just the
     synthetic cases).

Zero residue (no filesystem writes at all -- every tree here is synthetic `ast.parse`d text).
Lazy imports banned."""
from __future__ import annotations

import ast
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from gates import setup_tui_purity_gate as G  # noqa: E402


def _tree(src: str) -> ast.AST:
    return ast.parse(src)


def case_1() -> None:
    red_src = (
        "def submit(state, answers):\n"
        "    print('leaking straight to stdout')\n"
    )
    v = G.check_print_or_io(_tree(red_src), "steps_boundary.py")
    assert v and "print" in v[0], f"expected a print violation, got {v}"
    print("case 1a ok: bare print() inside a non-exempt module reads red")

    green_src = "def run_command(argv):\n    print(f'$ {argv}')\n"
    v2 = G.check_print_or_io(_tree(green_src), "runner.py")
    assert v2 == [], f"expected runner.py exempt, got {v2}"
    print("case 1b ok: the same shape inside runner.py (the exempted choke point) reads green")


def case_2() -> None:
    src = "def f():\n    line = sys.stdin.readline()\n    sys.stdout.write(line)\n"
    v = G.check_print_or_io(_tree(src), "steps_preflight.py")
    assert len(v) == 2, f"expected two IO violations (stdin+stdout), got {v}"
    print("case 2 ok: sys.stdin/sys.stdout attribute access in a non-exempt module reads red "
          f"({len(v)} hit(s))")


def case_3() -> None:
    red_src = "from tools.configtree.app import ConfigTreeApp\n"
    v = G.check_core_imports_app(_tree(red_src), "steps.py")
    assert v, "expected a core-imports-app violation"
    print("case 3a ok: steps.py importing tools.configtree.app (the textual-dependent submodule) "
          "reads red")

    ok_src = "from tools.configtree import SectionSpec, TextField\n"
    v_ok = G.check_core_imports_app(_tree(ok_src), "steps.py")
    assert v_ok == [], f"expected the library's TOP-LEVEL types to be importable from core, got {v_ok}"
    print("case 3b ok: steps.py importing the library's top-level types (SectionSpec/TextField) "
          "reads green -- every section module needs these to declare its data")

    green_src = "from tools.configtree.app import ConfigTreeApp\n"
    v2 = G.check_core_imports_app(_tree(green_src), "tui_app.py")
    assert v2 == [], f"expected tui_app.py exempt, got {v2}"
    print("case 3c ok: the same textual-dependent import inside tui_app.py (the one "
          "legitimate importer) reads green")


def case_4() -> None:
    code = G.main()
    assert code == 0, f"expected the real tree to be clean (exit 0), got {code}"
    print("case 4 ok: the rewritten gate against the REAL tools/setup_tui/ tree exits 0 (clean)")


if __name__ == "__main__":
    case_1()
    case_2()
    case_3()
    case_4()
    print("ALL CASES OK -- setup_tui_purity_gate.py's two rewritten detectors, both polarities, "
          "plus a real-tree clean confirmation")
