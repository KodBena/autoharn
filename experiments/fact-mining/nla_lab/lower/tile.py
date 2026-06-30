#!/usr/bin/env python
"""nla_lab.lower.tile — the opaque carrier `Tile[D]`, the single SSOT for all four seams.

`Tile[D]` is an opaque device register-tile, phantom-typed by its element dtype `D`
(`F32`/`I32`/`BoolT`). It is DELIBERATELY non-ArrayLike and NON-COERCIBLE: it defines NO
`__array__`, NO `__jax_array__`, NO `__array_namespace__`, NO arithmetic dunders, and NO
`__getitem__`. Two consequences, which are the whole design:

  (a) mypy rejects a `Tile` anywhere an `ArrayLike`/array is expected (it is not ArrayLike),
      so a raw fancy-index `a[idx]` (the gather) or `jnp.sum(tile)` does not type-check; and
  (b) at TRACE/construction time, feeding a `Tile` to ANY un-wrapped `jnp`/`lax` primitive
      raises (jax cannot convert a non-coercible object to an array) — the construction-time
      backstop that closes the ONE residual mypy cannot (`jnp.einsum`'s `Any`-typed
      `*operands`; see `ops.py` / `DESIGN.md` §4.lib).

NO CLEAN-IDIOM CONSTRUCTION FROM OUTSIDE (the foundation, hardened after CRITICAL-1). The
PUBLIC surface is fully closed, in the types and at runtime: `Tile.__init__` unconditionally
RAISES, so `Tile(...)` is a runtime error AND `Tile(arr, tok)` is a mypy `[call-arg]` error
(no value params); the earlier importable `_PRIV` token (`from …tile import _PRIV`, which let
a caller mint a dtype-LYING `Tile` mypy-clean) is GONE; and the backing array sits in a NAME-
MANGLED slot, so the deserialization-shaped `object.__new__(Tile); t._arr = …` is a mypy
`[attr-defined]` error AND a runtime `AttributeError`. The package mints a `Tile` ONLY through
the package-private `_wrap` brand. HONEST RESIDUE (ADR-0009, not papered over): Python has no
enforced package-private visibility, so `from …tile import _wrap; _wrap(x)` can still mint —
this is the EXACT symmetric status of the shape brand, where `Pow2(127)` likewise bypasses the
validating `pow2()` mypy-clean (the design's already-accepted construction-tier split, §4.shape).
A mint past `_wrap` (e.g. `object.__setattr__(t, "_Tile__arr", …)`) is unmistakable reflection,
the gc-tier the design does not claim to defend — the same tier as `_arr` read-extraction.

NOT A PYTREE (the foundation, hardened after HIGH-2). `Tile` is deliberately NOT registered
as a jax pytree. Registration made `jax.tree_util.tree_map(f, tile)` reach the backing array
and REWRAP an arbitrary (gather/coerced) result back into a valid `Tile` — a mypy-invisible
re-entry vector. Unregistered, a `Tile` is an OPAQUE LEAF: `tree_map(f, tile)` calls `f(tile)`
on the carrier itself (which `f` cannot touch — non-coercible), never `f(_arr)`. The kernel's
running (max, denom, numerator) state is carried through `fori_loop` by `ops.fold_kt`, which
keeps the wrap/unwrap INSIDE `lower/` (the jax carry is the raw backing arrays), so no pytree
registration is needed and the re-entry vector does not exist.

HOST-XOR-DEVICE. Imports `jax` only (device); never numpy. Device-only by construction. A
`Ref` (a NewType over `jax.Array`) is the device memory reference handed to a kernel by
`pl.pallas_call`; the boundary loaders/stores in `ops.py` take a `Ref`, so a raw host
`jax.Array` cannot enter a kernel-boundary load without the explicit, diff-visible `ops.ref`
brand — the type-surface half of the device seam (the file-level import-XOR gate is the other
half; see `DESIGN.md` §4.device for the honest type-closable / boundary-brand / file split).
"""

from __future__ import annotations

from typing import Any, Generic, NewType, TypeVar, cast, final

import jax

from nla_lab.lower.dtype import DType, I32

D = TypeVar("D", bound=DType)

# A DEVICE memory reference: the ref a `pl.pallas_call` hands its kernel. A NewType over
# `jax.Array`, so `ops.{load,band,store,…}` can demand a `Ref` and mypy rejects a raw host
# `jax.Array` passed in — the single diff-visible host-array -> device-ref crossing is the
# `ops.ref(...)` brand (analogous to `to_i32` for dtype). This is a boundary ASSERTION, not a
# residence proof: stock `jax.Array` carries no host/device residence tag, so the brand says
# "this array is a device kernel ref"; the import-XOR file gate enforces the residence class.
Ref = NewType("Ref", jax.Array)


@final
class Tile(Generic[D]):
    """An opaque device register-tile, phantom-typed by element dtype `D`. See the module
    docstring: non-ArrayLike, non-coercible, non-constructable from outside, NOT a pytree —
    its ONLY surface is the combinators in `lower/ops.py`. The single carrier for all four
    seams (lib/device/dtype/shape)."""

    # The backing array lives in a NAME-MANGLED slot (`__arr` -> `_Tile__arr`), accessible only
    # inside this class body. So the ordinary-attribute mint `object.__new__(Tile); t._arr = …`
    # (which reads like plausible deserialization code) is BOTH a runtime AttributeError (no
    # `_arr` slot, no `__dict__`) AND a mypy `[attr-defined]` error — closed to the criterion bar.
    __slots__ = ("__arr",)
    __arr: jax.Array

    def __init__(self) -> None:
        # NO public, clean-idiom construction. `Tile(...)` lands here and raises; `Tile(arr, tok)`
        # is additionally a mypy `[call-arg]` error (no value params); there is no importable
        # construction TOKEN (the holed `_PRIV` is gone). The package mints a `Tile` ONLY through
        # the package-private `_wrap` brand (below). HONEST RESIDUE (ADR-0009): `_wrap` is a single-
        # underscore module internal, so `from …tile import _wrap; _wrap(x)` can still mint — this
        # is the EXACT symmetric status of `Pow2`'s brand, where `Pow2(127)` likewise bypasses the
        # validating `pow2()` mypy-clean (the design's accepted construction-tier split, §4.shape).
        # Reaching the brand requires importing a `_`-internal across the package boundary; the
        # PUBLIC surface (the constructor + every attribute write) is fully mypy + runtime closed.
        raise TypeError(
            "Tile has no public constructor: a Tile is born ONLY inside a lower.ops combinator "
            "(via the package-private _wrap brand). There is no importable construction token.")


# The integer index/position tile alias (a `Tile` whose element dtype is `I32`).
Idx = Tile[I32]

# The mangled backing slot's runtime name. Reaching it requires this literal string (or explicit
# `object.__setattr__` reflection) — ordinary `t._arr`/`t._Tile__arr` attribute syntax is a mypy
# `[attr-defined]` error, so the only mypy-clean mint is the `_wrap` brand below (the Pow2-symmetric
# construction-tier residue); a slot write past it is unmistakable reflection (gc-tier, out of scope).
_SLOT = "_Tile__arr"


def _wrap(arr: jax.Array) -> Tile[Any]:
    """Package-internal: mint a `Tile` around a backing `jax.Array`, bypassing the raising
    `__init__` via `object.__new__` and seating the mangled slot by its literal name. The ONE
    mint brand (the carrier analog of `pow2()` for `Pow2`); the phantom dtype is erased at
    runtime and the calling combinator restores the static `Tile[D]` via its return annotation."""
    t: Tile[Any] = object.__new__(Tile)
    object.__setattr__(t, _SLOT, arr)
    return t


def _arr(t: Tile[Any]) -> jax.Array:
    """Package-internal: unwrap a `Tile` to its backing `jax.Array`. Used ONLY by `ops.py`
    (the eager interpreter of each combinator); never re-exported to callers. Extraction is
    read-only — a raw array cannot RE-ENTER the algebra except through an `ops` combinator (the
    only mint is `_wrap`, and `Tile` is not a pytree, so `tree_map` cannot rewrap)."""
    return cast(jax.Array, object.__getattribute__(t, _SLOT))
