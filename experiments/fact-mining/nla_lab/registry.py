#!/usr/bin/env python
"""The variant REGISTRY: name -> zero-arg factory, additively self-registered, with
DEFERRED discovery (ported from control_lab adapter.py:147 / methods/__init__.py — the
core "what's good" of the model).

THE FAN-OUT ENABLER (A3 + A4). Each variant lives in ITS OWN file under `variants/`
and appends itself at module bottom with `register(Class)` (which calls
`REGISTRY.setdefault(name, Class)`), so ONE method = ONE file + ONE entry, ZERO edits
to any shared file. Discovery is EXPLICIT and DEFERRED — `load_all()` walks
`variants/` and imports each module ONCE, called by the harness, NOT at package
import. So importing one variant for its own unit test does not pull its siblings; a
half-written sibling cannot break another's test. This is precisely what lets the
eight follow-on agents work in parallel against the unchanged contract.

FAIL LOUD (A5 / ADR-0002). `setdefault` so a re-import or name-clash never silently
clobbers an existing entry (a clash raises here, loudly). `resolve` raises a KeyError
listing the known names — it refuses to guess. A module that raises on import
PROPAGATES (never a silent no-show).

HOST-XOR-DEVICE. Stdlib only (`importlib`/`pkgutil` + the contract type). `load_all`
imports the device-side variant modules at RUNTIME; this file's own AST imports no
numpy and no device lib, so the import-XOR gate stays green (host orchestration).
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Callable

from nla_lab.contract import EncodeVariant

Factory = Callable[[], EncodeVariant]   # NOT `Any` — the registry value type is the
#: real factory type, so `mypy --strict` checks it (avoids control_lab's `Factory =
#: Any` erasure, ADR-0012 P8). One entry per variant name.
REGISTRY: dict[str, Factory] = {}


def register(cls: type[EncodeVariant]) -> type[EncodeVariant]:
    """Self-register a variant CLASS as its own zero-arg factory under `cls.name`.
    Returns `cls` so it can be used as a decorator. Clash-loud: a second class
    claiming an existing name raises rather than clobbering."""
    name = cls.name
    existing = REGISTRY.get(name)
    if existing is not None and existing is not cls:
        raise ValueError(
            f"registry name clash: {name!r} already registered to {existing!r}, "
            f"refusing to clobber with {cls!r} (one name = one variant).")
    REGISTRY.setdefault(name, cls)
    return cls


def load_all() -> dict[str, Factory]:
    """Import every module under `variants/` ONCE so each self-registers, then return
    the populated REGISTRY. Called by the harness (deferred discovery, A4). Fail-loud:
    a variant module that raises on import propagates here."""
    from nla_lab import variants  # the subpackage (imported here, not at this module's import)

    for mod in pkgutil.iter_modules(variants.__path__):
        importlib.import_module(f"nla_lab.variants.{mod.name}")
    return REGISTRY


def resolve(name: str) -> Factory:
    """name -> factory, or raise KeyError listing the known names (refusing to guess —
    ADR-0002). `load_all()` must have run first."""
    try:
        return REGISTRY[name]
    except KeyError:
        known = ", ".join(sorted(REGISTRY)) or "(none loaded — call load_all())"
        raise KeyError(f"unknown variant {name!r}; known: {known}") from None


def make(name: str) -> EncodeVariant:
    """Instantiate the named variant, checking the factory produced a real
    `EncodeVariant` before it is used (loud type-check at the boundary, A5)."""
    obj = resolve(name)()
    if not isinstance(obj, EncodeVariant):
        raise TypeError(
            f"factory for {name!r} produced {type(obj)!r}, not an EncodeVariant.")
    return obj


def portfolio_names() -> list[str]:
    """The sweepable portfolio: every registered name NOT prefixed `_` (the underscore
    prefix marks harness-internal fixtures — e.g. the deliberately-broken watchdog
    smoke variant — which the default bench sweep excludes but the self-test invokes
    explicitly)."""
    return sorted(n for n in REGISTRY if not n.startswith("_"))
