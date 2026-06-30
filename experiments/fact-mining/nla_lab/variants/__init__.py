#!/usr/bin/env python
"""The `variants/` subpackage — one file per encode-variant, each self-registering at
module bottom via `registry.register(...)`.

DISJOINT FILES FOR THE PARALLEL FAN-OUT (A4). This package's import does NOTHING
eager: discovery is the registry's `load_all()`, which `pkgutil.iter_modules` over
THIS package's `__path__` and imports each module once. So a follow-on agent owns
exactly one file here (its math), touches no shared file, and a half-written sibling
cannot break another's unit test (importing one variant does not pull the rest).
"""

from __future__ import annotations
