#!/usr/bin/env python3
"""seen-red/setup-tui-governed-files-drift/run_fixtures.py -- both-polarity proof of
tools/setup_tui/governed_files.py's own drift BACKSTOP (ledger row 1799 finding 2),
census-registered in gates/fixture_census.py.

The module docstring's own "THE CONTRACT" note names the hazard: `DEFAULT_PATTERNS` is a THIRD
mirror of `["*.py"]`, alongside hooks/pretooluse_change_gate.py's `_DEFAULT_GOVERNED_PATTERNS`
and bootstrap/templates/governed_files.json's `{"patterns": [...]}` -- three different process
boundaries with no shared importable home, "kept in sync by inspection" per that docstring. This
fixture makes that claim a checked property:

  1. GREEN leg: the REAL DEFAULT_PATTERNS agrees with BOTH other real sources, read fresh from
     their own files -- `check_default_patterns_drift()` with no arguments returns zero drift
     messages.
  2. RED leg A: a SYNTHETIC hooks/pretooluse_change_gate.py source text carrying a DIFFERENT
     `_DEFAULT_GOVERNED_PATTERNS` literal -- `check_default_patterns_drift` must report the
     disagreement against the real hooks/ source.
  3. RED leg B: a SYNTHETIC bootstrap/templates/governed_files.json body carrying a DIFFERENT
     `patterns` list -- `check_default_patterns_drift` must report the disagreement against the
     real bootstrap/ source.

Both red legs feed `check_default_patterns_drift(hooks_source_text=..., bootstrap_source_text=...)`
a SYNTHETIC string (per governed_files.py's own docstring: injectable so a fixture can observe
the red leg without touching hooks/ or bootstrap/ on disk -- those trees stay read-only, per
this package's scope discipline). Neither hooks/ nor bootstrap/ is ever written to by this
fixture.

Zero residue: pure in-memory comparison + real file reads of the two OTHER read-only sources, no
filesystem mutation, no db state. Real functions under test (no mocks). Lazy imports banned."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.setup_tui import governed_files as gf  # noqa: E402


def main() -> int:
    # --- case 1: GREEN leg -- all three real sources agree ---
    real_drift = gf.check_default_patterns_drift()
    assert real_drift == [], (
        f"case 1 (GREEN leg): the real DEFAULT_PATTERNS must agree with the real hooks/ and "
        f"bootstrap/ sources with ZERO drift messages -- got: {real_drift}"
    )
    print("case 1 ok: DEFAULT_PATTERNS, hooks/pretooluse_change_gate.py, and "
          "bootstrap/templates/governed_files.json all agree (zero drift)")

    # --- case 2: RED leg A -- synthetic hooks/ source disagrees ---
    synthetic_hooks = '_DEFAULT_GOVERNED_PATTERNS = ["*.py", "*.ts"]\n'
    drift_a = gf.check_default_patterns_drift(hooks_source_text=synthetic_hooks)
    assert len(drift_a) == 1 and "hooks/pretooluse_change_gate.py" in drift_a[0], (
        f"case 2 (RED leg A): a disagreeing synthetic hooks/ source must read red -- "
        f"got: {drift_a}"
    )
    print("case 2 ok: a synthetic hooks/pretooluse_change_gate.py default reads red when it "
          "disagrees with DEFAULT_PATTERNS")

    # --- case 3: RED leg B -- synthetic bootstrap/ source disagrees ---
    synthetic_bootstrap = '{"patterns": ["*.py", "*.vue"]}'
    drift_b = gf.check_default_patterns_drift(bootstrap_source_text=synthetic_bootstrap)
    assert len(drift_b) == 1 and "bootstrap/templates/governed_files.json" in drift_b[0], (
        f"case 3 (RED leg B): a disagreeing synthetic bootstrap/ source must read red -- "
        f"got: {drift_b}"
    )
    print("case 3 ok: a synthetic bootstrap/templates/governed_files.json default reads red "
          "when it disagrees with DEFAULT_PATTERNS")

    # --- bonus case: both red legs stack ---
    drift_both = gf.check_default_patterns_drift(
        hooks_source_text=synthetic_hooks, bootstrap_source_text=synthetic_bootstrap)
    assert len(drift_both) == 2, (
        f"bonus case: both defects at once should report exactly 2 drift messages -- "
        f"got {len(drift_both)}: {drift_both}"
    )
    print("bonus case ok: both synthetic disagreements stack, reported separately")

    print("ALL CASES OK -- governed_files.py three-mirror drift backstop, both polarities proven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
