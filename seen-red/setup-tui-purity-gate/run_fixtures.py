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
  4. RED, negative self-check for DETECTION 2 (CLASS FIX, fresh-context review of b565db1) --
     five synthetic shapes, each proving `check_extra_effects` catches what it claims to:
       4a. a bare `open(path, "w")` inside an ordinary function of a synthetic "screens.py" --
           caught (the EXACT shape the review's own instruction named: "a synthetic bare
           open-for-write in a screen must fail red").
       4b. `os.mkdir(...)` inside an ordinary function -- caught.
       4c. `tempfile.mkdtemp(...)` inside an ordinary function -- caught.
       4d. `subprocess.run(...)` inside an ordinary function of a synthetic "screens.py" --
           caught.
       4e. the negative control: a READ-mode `open(path)` (no mode arg at all) and
           `open(path, "r")` (explicit read mode) inside an ordinary function -- NOT caught
           (proving the detector discriminates read from write, never over-catching).
  5. GREEN -- DETECTION 2's exemption table applied correctly: a synthetic "probes.py" (whole-
     file exempt) with a `subprocess.run(...)` call is NOT caught; the SAME call in a synthetic
     "screens.py" (no exemption) IS caught -- proving the exemption is table-driven, not a
     blanket "subprocess is fine" rule.

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


SYNTH_OPEN_WRITE_IN_FUNCTION = """
def screen_boundary(ui, cl, state):
    with open("/tmp/x", "w") as f:
        f.write("hi")
    return state
"""

SYNTH_OS_MKDIR_IN_FUNCTION = """
import os

def screen_boundary(ui, cl, state):
    os.mkdir("/tmp/scratch-dir")
    return state
"""

SYNTH_TEMPFILE_MKDTEMP_IN_FUNCTION = """
import tempfile

def screen_signed_genesis(ui, cl, state):
    gnupghome = tempfile.mkdtemp(prefix="x-")
    return state
"""

SYNTH_SUBPROCESS_RUN_IN_FUNCTION = """
import subprocess

def screen_birth(ui, cl, state):
    subprocess.run(["echo", "hi"])
    return state
"""

SYNTH_OPEN_READ_IN_FUNCTION = """
def screen_hydration(ui, cl, state):
    with open("/tmp/x") as f:
        a = f.read()
    with open("/tmp/y", "r") as f:
        b = f.read()
    return state
"""

SYNTH_SUBPROCESS_IN_PROBES = """
import subprocess

def pg_reachable(host):
    return subprocess.run(["pg_isready", "-h", host])
"""


def case_4_extra_effects_negative_self_check() -> None:
    print("case 4: RED -- the negative self-check for DETECTION 2 (CLASS FIX), five shapes")

    tree_a = ast.parse(SYNTH_OPEN_WRITE_IN_FUNCTION, filename="screens.py")
    v_a = G.check_extra_effects(tree_a, "screens.py")
    check("4a: a bare open(path, 'w') inside an ordinary function IS caught",
          len(v_a) == 1 and "screen_boundary" in v_a[0], v_a)

    tree_b = ast.parse(SYNTH_OS_MKDIR_IN_FUNCTION, filename="screens.py")
    v_b = G.check_extra_effects(tree_b, "screens.py")
    check("4b: os.mkdir(...) inside an ordinary function IS caught",
          len(v_b) == 1 and "screen_boundary" in v_b[0], v_b)

    tree_c = ast.parse(SYNTH_TEMPFILE_MKDTEMP_IN_FUNCTION, filename="screens.py")
    v_c = G.check_extra_effects(tree_c, "screens.py")
    check("4c: tempfile.mkdtemp(...) inside an ordinary function IS caught",
          len(v_c) == 1 and "screen_signed_genesis" in v_c[0], v_c)

    tree_d = ast.parse(SYNTH_SUBPROCESS_RUN_IN_FUNCTION, filename="screens.py")
    v_d = G.check_extra_effects(tree_d, "screens.py")
    check("4d: subprocess.run(...) inside an ordinary function IS caught",
          len(v_d) == 1 and "screen_birth" in v_d[0], v_d)

    tree_e = ast.parse(SYNTH_OPEN_READ_IN_FUNCTION, filename="screens.py")
    v_e = G.check_extra_effects(tree_e, "screens.py")
    check("4e: a READ-mode open() (no mode arg, or explicit 'r') is NOT caught "
          "(read vs write discrimination, never over-catching)", v_e == [], v_e)


def case_5_extra_effects_exemption_table_driven() -> None:
    print("case 5: GREEN -- DETECTION 2's exemption table is applied correctly, per file")

    tree_probes = ast.parse(SYNTH_SUBPROCESS_IN_PROBES, filename="probes.py")
    v_probes = G.check_extra_effects(tree_probes, "probes.py")
    check("the SAME subprocess.run(...) shape in a synthetic 'probes.py' (whole-file exempt) "
          "is NOT caught", v_probes == [], v_probes)

    tree_screens = ast.parse(SYNTH_SUBPROCESS_IN_PROBES.replace("pg_reachable", "screen_x"),
                              filename="screens.py")
    v_screens = G.check_extra_effects(tree_screens, "screens.py")
    check("the IDENTICAL call shape in a synthetic 'screens.py' (no exemption) IS caught -- "
          "the exemption is table-driven, not a blanket subprocess allowance",
          len(v_screens) == 1, v_screens)


def main() -> int:
    case_1_real_tree_clean()
    case_2_negative_self_check()
    case_3_commit_executor_exempt()
    case_4_extra_effects_negative_self_check()
    case_5_extra_effects_exemption_table_driven()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nall cases GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
