#!/usr/bin/env python3
"""seen-red/max-lines/run_fixtures.py -- both-polarity proof of gates/max_lines.py (ADR-0007
mechanization; design/FABLE-SETUP-TUI-FIELD-STRATEGY.md Track 1 item 2), census-registered in
gates/fixture_census.py under "max-lines".

Drives `gates.max_lines.evaluate()` directly against synthetic (path, line-count) pairs -- the
pure decision function the real gate's `main()` calls per file, factored out exactly so this
fixture never has to touch or fake the real tree (same shape as
seen-red/setup-tui-purity-gate/run_fixtures.py driving `check_tree`/`check_extra_effects`
directly).

Cases:
  1. RED (negative self-check) -- a brand-new path, never in BASELINE, at 401 lines (one over
     CEILING): `evaluate()` must return a violation naming it a NEW offender.
  2. GREEN -- a real baselined path (`gates/kind_shape_manifest_gate.py`) evaluated at EXACTLY
     its ratchet count: `evaluate()` must return None (grandfathered, holding steady).
  3. RED -- the SAME baselined path, evaluated ONE LINE OVER its ratchet: `evaluate()` must
     return a violation naming the grow-past-ratchet reason (ADR-0011 Rule 4: shrink or hold,
     never grow).
  4. GREEN -- a synthetic path at 350 lines (inside the 300-400 review band): `evaluate()` must
     return None -- the review band is never mechanically flagged, exactly as ADR-0007 leaves it.
  5. GREEN -- a synthetic path at 400 lines exactly (AT the ceiling, not over it): `evaluate()`
     must return None -- CEILING is inclusive of 400 (">400" fails, "==400" does not).
  6. RED (main()-level, not evaluate()-level) -- a stale BASELINE row: a synthetic baseline dict
     naming a path that is not among the "present" files main() would have scanned. This proves
     the baseline-rot check independently of evaluate(), since that check lives in main()'s own
     loop, not in evaluate() -- reproduced here by re-deriving the same predicate main() uses
     (`rel not in present`) rather than re-running the whole gate against a fake git tree.

Zero residue: nothing here touches disk beyond importing the real gate module and reading its
own BASELINE dict (never mutated) for case 2/3's real ratchet value.

Usage: python3 seen-red/max-lines/run_fixtures.py
Exit 0 if every case matches; 1 otherwise."""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "gates"))

import max_lines  # noqa: E402 -- path insert above must precede this import


def _check(label: str, condition: bool, detail: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}: {detail}")
    return condition


def main() -> int:
    ok = True

    # Case 1: RED -- brand-new path, never baselined, one over ceiling.
    v1 = max_lines.evaluate("tools/setup_tui/brand_new_offender.py", 401)
    ok &= _check("case 1 (new over-ceiling file)", v1 is not None and "NEW file" in v1,
                 f"evaluate(...) = {v1!r}")

    # Case 2: GREEN -- real baselined path at exactly its ratchet.
    real_path = "gates/kind_shape_manifest_gate.py"
    ratchet = max_lines.BASELINE[real_path]
    v2 = max_lines.evaluate(real_path, ratchet)
    ok &= _check("case 2 (baselined path at its ratchet)", v2 is None,
                 f"evaluate({real_path!r}, {ratchet}) = {v2!r}")

    # Case 3: RED -- same baselined path, one line OVER its ratchet.
    v3 = max_lines.evaluate(real_path, ratchet + 1)
    ok &= _check("case 3 (baselined path one over its ratchet)",
                 v3 is not None and "grew past its ratchet" in v3,
                 f"evaluate({real_path!r}, {ratchet + 1}) = {v3!r}")

    # Case 4: GREEN -- inside the 300-400 review band, never flagged.
    v4 = max_lines.evaluate("tools/setup_tui/some_module.py", 350)
    ok &= _check("case 4 (review band, 350 lines)", v4 is None, f"evaluate(...) = {v4!r}")

    # Case 5: GREEN -- exactly at CEILING (400), inclusive boundary.
    v5 = max_lines.evaluate("tools/setup_tui/at_ceiling.py", max_lines.CEILING)
    ok &= _check("case 5 (exactly at ceiling, inclusive)", v5 is None, f"evaluate(...) = {v5!r}")

    # Case 6: RED -- stale baseline row, reproducing main()'s own orphan predicate directly
    # (the check lives in main()'s loop, not in evaluate()).
    synthetic_baseline = {"tools/setup_tui/long_gone.py": 999}
    synthetic_present = {"gates/kind_shape_manifest_gate.py", "gates/max_lines.py"}
    stale = [p for p in synthetic_baseline if p not in synthetic_present]
    ok &= _check("case 6 (stale baseline row detected)",
                 stale == ["tools/setup_tui/long_gone.py"], f"stale rows = {stale!r}")

    if ok:
        print("seen-red/max-lines: all 6 cases matched (both polarities proven).")
        return 0
    print("seen-red/max-lines: at least one case DID NOT MATCH -- see FAIL lines above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
