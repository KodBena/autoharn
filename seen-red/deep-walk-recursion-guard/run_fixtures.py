#!/usr/bin/env python3
"""Both-polarity fixture for gates/deep_walk_recursion_guard.py (boundary-recursion-net-
single-invariant, ledger row 1628, re-asserted from autoharn1).

GREEN: the real serving/boundary_service.py passes -- `_guard_recursion` is the only place
`RecursionError` is ever caught in that file.

RED: a synthetic FOURTH deep-walk site, appended to a throwaway copy of the real module, that
bypasses `_guard_recursion` by open-coding its own `except RecursionError` clause -- exactly
the shape this gate exists to catch (row 1628's own words: "a fourth traversal site added
later could still miss it"). Refused, naming the offending line.

Runs against a throwaway tempfile copy; zero residue in the repo itself."""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..")
GATE = os.path.join(REPO, "gates", "deep_walk_recursion_guard.py")
TARGET = os.path.join(REPO, "serving", "boundary_service.py")

# A synthetic fourth traversal, never committed to the real module: it bypasses the shared
# helper by writing its OWN except-RecursionError clause rather than routing through
# `_guard_recursion`, the exact defect class row 1628 names.
SYNTHETIC_BYPASS_SITE = '''

def _fourth_deep_walk_site_synthetic_bypass(payload):
    """RED-fixture-only: a fourth traversal that bypasses _guard_recursion by open-coding its
    own except clause. Never present in the real module -- appended only to a throwaway copy
    by this fixture."""
    try:
        return list(_iter_strings(payload))
    except RecursionError as e:
        axis, detail = _classify_parse_failure(e)
        return None, axis, detail
'''


def main() -> int:
    # GREEN: the real file, unmodified.
    green = subprocess.run([sys.executable, GATE, TARGET], capture_output=True, text=True)
    assert green.returncode == 0, (
        f"GREEN expected exit 0 on the real module, got {green.returncode}: {green.stdout}")
    assert green.stdout == "", f"GREEN expected silent pass, got: {green.stdout}"
    print("GREEN ok: serving/boundary_service.py passes -- _guard_recursion is the only "
          "except-RecursionError site")

    # RED: append the synthetic bypass to a throwaway copy and re-run the gate against it.
    src = open(TARGET, encoding="utf-8").read()
    red_src = src + SYNTHETIC_BYPASS_SITE
    ast.parse(red_src)  # sanity: the synthetic fixture itself must be valid Python
    fd, red_path = tempfile.mkstemp(prefix="deep-walk-recursion-guard-red-", suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(red_src)
        red = subprocess.run([sys.executable, GATE, red_path], capture_output=True, text=True)
        assert red.returncode == 1, (
            f"RED expected exit 1 on the synthetic bypass, got {red.returncode}: {red.stdout}")
        assert "bypassing the single" in red.stdout, red.stdout
        assert "boundary-recursion-net-single-invariant" in red.stdout, red.stdout
        print("RED  ok: synthetic fourth bypassing site refused:")
        for line in red.stdout.splitlines():
            if "bypassing" in line:
                print(f"  {line}")
    finally:
        os.unlink(red_path)

    print("ALL CASES OK -- deep-walk-recursion-guard both polarities, zero residue")
    return 0


if __name__ == "__main__":
    sys.exit(main())
