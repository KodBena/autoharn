#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T20:11:03Z
#   last-change: 2026-07-19T20:11:03Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""seen-red/setup-tui-purity-gate/run_fixtures.py -- both-polarity proof of
gates/setup_tui_purity_gate.py (design/FABLE-SETUP-TUI-PURE-CORE-SPEC.md §2.8, commission ledger
rows 1823 point 2 / 1825 / 1835), census-registered in gates/fixture_census.py.

Cases:
  1. GREEN, real tree -- the gate reports zero violations against the ACTUAL
     tools/setup_tui/*.py files (`gates/setup_tui_purity_gate.scan_package()`), proving the
     Phase-2 rewire genuinely confined every runner choke-point call to commit_executor.py /
     screen_rehearsal, not merely that the gate script runs.
  2. RED, negative self-check (a synthetic violation must fail red -- spec §2.8's own standing
     requirement) -- three synthetic ast.Module trees, checked via `check_tree` under a chosen
     filename, each proving the gate actually CATCHES the shape it claims to forbid:
       2a. a bare `run_command(...)` call inside an ordinary function of a synthetic
           "screens.py" -- caught, not exempt.
       2b. a `runner.write_file(...)` attribute call at MODULE LEVEL (no enclosing function) of a
           synthetic "screens.py" -- caught (the "always a violation, never exempt" module-level
           case named in the gate's own docstring).
       2c. the SAME `run_command(...)` call, but placed inside `screen_rehearsal` -- NOT caught
           (the declared exception working correctly is also a claim this gate could get wrong in
           either direction; proving the exception fires only where it should is as load-bearing
           as proving the forbidden call is caught elsewhere).
  3. GREEN -- `commit_executor.py`'s own real, load-bearing choke-point calls (three of them,
     verified present) are correctly exempted (module-level '*' entry), never mistaken for a
     violation.

Zero residue: everything is synthetic AST text, nothing touches disk beyond the real files this
fixture reads. Lazy imports banned.

Usage: python3 seen-red/setup-tui-purity-gate/run_fixtures.py
Exit 0 if every case matches; 1 otherwise."""
from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from gates import setup_tui_purity_gate as G  # noqa: E402

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  OK   {label}")
    else:
        msg = f"FAIL {label}" + (f" -- {detail}" if detail else "")
        print(f"  {msg}")
        FAILURES.append(msg)


def case_1_real_tree_clean() -> None:
    print("case 1: GREEN -- the real tools/setup_tui/*.py tree has zero purity violations")
    violations = G.scan_package()
    check("zero violations against the real tree", violations == [], violations)


SYNTH_BARE_IN_FUNCTION = """
from tools.setup_tui.runner import run_command

def screen_boundary(ui, cl, state):
    res = run_command(["echo", "hi"])
    return state
"""

SYNTH_ATTR_MODULE_LEVEL = """
from tools.setup_tui import runner

runner.write_file("/tmp/x", "content")
"""

SYNTH_BARE_IN_REHEARSAL = """
from tools.setup_tui.runner import run_command

def screen_rehearsal(ui, cl, state):
    res = run_command(["echo", "hi"])
    return state
"""


def case_2_negative_self_check() -> None:
    print("case 2: RED -- the negative self-check, three synthetic violations")

    tree_a = ast.parse(SYNTH_BARE_IN_FUNCTION, filename="screens.py")
    v_a = G.check_tree(tree_a, "screens.py")
    check("2a: a bare run_command() inside an ordinary function IS caught",
          len(v_a) == 1 and "screen_boundary" in v_a[0], v_a)

    tree_b = ast.parse(SYNTH_ATTR_MODULE_LEVEL, filename="screens.py")
    v_b = G.check_tree(tree_b, "screens.py")
    check("2b: a module-level runner.write_file() call IS caught (never exempt)",
          len(v_b) == 1 and "<module level>" in v_b[0], v_b)

    tree_c = ast.parse(SYNTH_BARE_IN_REHEARSAL, filename="screens.py")
    v_c = G.check_tree(tree_c, "screens.py")
    check("2c: the SAME call, inside screen_rehearsal, is NOT caught (declared exception works)",
          v_c == [], v_c)


def case_3_commit_executor_exempt() -> None:
    print("case 3: GREEN -- commit_executor.py's real choke-point calls are correctly exempted")
    path = os.path.join(REPO, "tools", "setup_tui", "commit_executor.py")
    with open(path, encoding="utf-8") as f:
        source = f.read()
    real_call_count = sum(
        1 for node in ast.walk(ast.parse(source, filename="commit_executor.py"))
        if isinstance(node, ast.Call) and G._call_name(node) in G.FORBIDDEN_NAMES
    )
    check("commit_executor.py really DOES call all three choke points (>= 3 real call sites)",
          real_call_count >= 3, real_call_count)
    v = G.scan_file(path)
    check("but the gate reports zero violations for it (module-level '*' exemption)", v == [], v)


def main() -> int:
    case_1_real_tree_clean()
    case_2_negative_self_check()
    case_3_commit_executor_exempt()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
