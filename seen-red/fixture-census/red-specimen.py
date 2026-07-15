#!/usr/bin/env python3
"""Seen-red specimen for the fixture-census gate ([C20]). Proves it goes RED when the seen-red
corpus is not intact — here by emptying its registry in memory, so every real seen-red dir reads
as ORPHANED (a gate's both-polarity proof with no owning registry entry, the exact rot the gate
exists to catch). The green half is the gate passing on the real corpus (gates/fixture_census.py
exit 0). Run from anywhere. Lazy imports banned."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gates"))
import fixture_census  # noqa: E402

fixture_census.REGISTRY = {}   # nothing registered -> every real seen-red dir is orphaned
rc = fixture_census.main()
print(f"# fixture-census red-specimen: exit={rc} (expect 1 — RED on an empty registry)")
raise SystemExit(0 if rc == 1 else 1)
