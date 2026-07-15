#!/usr/bin/env python3
"""Seen-red specimen for the layout-census gate ([C21]). Proves it goes RED on a tree that
breaches LAYOUT §1 — here by emptying its registered-directory allowlist in memory, so every
real top-level directory reads as an UNREGISTERED misfit-absorbing parent (the exact failure
the gate exists to catch). The green half is the gate passing on the real tree
(gates/layout_census.py exit 0). Run from anywhere. Lazy imports banned."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gates"))
import layout_census  # noqa: E402

layout_census.ROOT_DIRS = set()   # nothing registered -> every real top-level dir is unregistered
layout_census.ROOT_FILES = set()  # -> and every root doc too
rc = layout_census.main()
print(f"# layout-census red-specimen: exit={rc} (expect 1 — RED on an empty allowlist)")
raise SystemExit(0 if rc == 1 else 1)
