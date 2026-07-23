#!/usr/bin/env python3
"""seen-red/setup-tui-purity-gate/run_fixtures.py -- both-polarity proof of the REWRITTEN
gates/setup_tui_purity_gate.py (design/FABLE-SETUP-TUI-REBUILD-SPEC.md §2/§6, the 2026-07-22
wholesale rebuild onto tools/configtree): its three detectors (no print/input/stdin/stdout outside
the app package + the --from-config reporter; the core imports nothing from the app package; no
raw fr-default layout container in a tools/configtree content path, ledger row 1139), plus a
real-tree GREEN leg (the actual gate, run against the actual package, is clean today).

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
  5. `check_raw_layout_containers` (ledger row 1139, TYPE half) -- RED on a synthetic raw
     `class Foo(Vertical)` and a raw, unclassed `Horizontal()` call inside it -- byte-for-byte the
     SAME shape `widgets_master_detail.py`'s own pre-fix culprit had; GREEN once the same class
     uses `layout_primitives.ContentVertical`/`ContentHorizontal` instead, and GREEN for the
     declared `LAYOUT_EXCEPTIONS`/`LAYOUT_BASE_CLASS_EXCEPTIONS` shells (`ct-split`, the wide
     layout's own scroll columns, `SectionPane`). PLUS a real-tree leg:
     `gates/setup_tui_purity_gate.main()` against the ACTUAL, now-fixed `tools/configtree/` tree
     exits 0 (the real migration is genuinely gate-clean, not just the synthetic cases).

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


def case_5() -> None:
    """`check_raw_layout_containers` (ledger row 1139, TYPE half): the maintainer's own
    reproduced hazard -- a raw `(Vertical)` base class holding a raw, unclassed `Horizontal()`
    call, exactly `widgets_master_detail.MasterDetailFieldWidget`'s pre-fix shape -- RED; the
    same shape migrated to the typed primitive, and every declared exception, GREEN."""
    red_src = (
        "from textual.containers import Vertical, Horizontal\n"
        "class SomeContentWidget(Vertical):\n"
        "    def compose(self):\n"
        "        with Horizontal():\n"
        "            yield None\n"
    )
    v = G.check_raw_layout_containers(_tree(red_src), "some_widget.py")
    assert len(v) == 2, f"expected 2 violations (base class + bare call), got {v}"
    assert any("class SomeContentWidget(Vertical)" in line for line in v), v
    assert any("raw Horizontal(...)" in line for line in v), v
    print(f"case 5a ok (RED, the exact reproduced class): a raw `(Vertical)` base class "
          f"nesting a raw, unclassed `Horizontal()` call reads red -- {v}")

    green_src = (
        "from tools.configtree.layout_primitives import ContentHorizontal, ContentVertical\n"
        "class SomeContentWidget(ContentVertical):\n"
        "    def compose(self):\n"
        "        with ContentHorizontal():\n"
        "            yield None\n"
    )
    v_ok = G.check_raw_layout_containers(_tree(green_src), "some_widget.py")
    assert v_ok == [], f"expected the typed-primitive shape to read clean, got {v_ok}"
    print("case 5b ok (GREEN): the SAME shape, built from layout_primitives.ContentVertical/"
          "ContentHorizontal instead, reads clean")

    exceptions_src = (
        "from textual.containers import Horizontal, Vertical, VerticalScroll\n"
        "class SectionPane(Vertical):\n"
        "    def compose(self):\n"
        "        with Horizontal(classes='ct-split'):\n"
        "            with VerticalScroll(classes='ct-controls-col'):\n"
        "                pass\n"
        "            with VerticalScroll(classes='ct-help-col'):\n"
        "                pass\n"
    )
    v_exc = G.check_raw_layout_containers(_tree(exceptions_src), "panes.py")
    assert v_exc == [], f"expected every declared LAYOUT_EXCEPTIONS shell to read clean, got {v_exc}"
    print("case 5c ok (GREEN): every declared fr-intended shell (SectionPane's own base class, "
          "'ct-split', 'ct-controls-col', 'ct-help-col') reads clean -- the gate does not refuse "
          "the shells it is meant to leave alone")

    code = G.main()
    assert code == 0, f"expected the real, now-migrated tools/configtree/ tree to be clean, got {code}"
    print("case 5d ok: the rewritten gate against the REAL, now-fixed tools/configtree/ tree "
          "exits 0 (clean) -- the actual row-1139 migration, not just the synthetic cases")


if __name__ == "__main__":
    case_1()
    case_2()
    case_3()
    case_4()
    case_5()
    print("ALL CASES OK -- setup_tui_purity_gate.py's three detectors, both polarities, plus a "
          "real-tree clean confirmation")
