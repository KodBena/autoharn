#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-07T01:52:33Z
#   last-change: 2026-07-07T01:52:33Z
#   contributors: 37017f46/main
# <<< PROVENANCE-STAMP <<<

"""Seen-red specimen for the verify-adapter gate (forecloses findings 5, 17, 23 — the act-stream
adapter's oracle-agreement class: a manifest family that is loud-in-prose but unchecked; a delegation
tool the adapter fails to recognize; a mis-attribution of subagent acts). verify_adapter.py asserts the
adapter's output AGREES with the pre-registered independent oracle across exactly these dimensions and
that deliberate defects flip RED. This specimen reproduces the load-bearing detection: it takes the
adapter's own synthetic stream, applies the attribution-defeat defect (re-attribute subagent acts to
'main' — the shape finding 23/17's mis-recognition would produce), and shows the oracle comparison
DIVERGES (the verifier's core assertion fails). The captured DIVERGE is banked as red.txt.

Run from the harness repo root. No DB writes; pure in-memory adapter comparison."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

_ADAPTER = Path("/home/bork/w/vdc/1/epistemic-operator/tools/act_stream")
sys.path.insert(0, str(_ADAPTER))
sys.path.insert(0, str(_ADAPTER.parent.parent / "instruments"))  # for any shared deps
from verify_adapter import EXPECT_SYN, _syn_stream, _tuples  # noqa: E402


def main() -> int:
    syn = _syn_stream()
    baseline = _tuples(syn.acts)
    if baseline != EXPECT_SYN:
        print("SPECIMEN INERT — the clean adapter already diverges from the oracle (unexpected).")
        return 1
    # the defect: attribute the subagent's acts to 'main' (a delegation/attribution mis-recognition)
    defect = [replace(a, actor="main") if a.actor.startswith("sub:") else a for a in syn.acts]
    got = _tuples(tuple(defect))
    if got == EXPECT_SYN:
        print("SPECIMEN INERT — the defect did NOT flip the oracle comparison (verifier is decorative).")
        return 1
    print("verify-adapter oracle comparison: adapter output vs pre-registered oracle -> DIVERGE (RED)")
    for i, (g, e) in enumerate(zip(got, EXPECT_SYN)):
        if g != e:
            print(f"  row {i}: got {g} expected {e}")
    print("# ADAPTER RED — a mis-attributed/mis-recognized act flips the verifier; the finding-5/17/23 "
          "class (unchecked manifest family, unrecognized delegation, attribution defeat) is caught.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
