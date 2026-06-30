#!/usr/bin/env python
"""impedance.tensor — the opaque carrier `Tensor[L, Dev, D, S]`, the single SSOT for all seams.

`Tensor[L, Dev, D, S]` is an opaque tensor handle, phantom-typed by FOUR axes simultaneously:

  * `L`   — the LIBRARY tag (`Torch` / `Numpy` / `Jax` / `JaxLower` …): which interpreter owns
            the value. A cross-library handoff is an ill-typed expression (an op of library B
            does not accept a carrier tagged for library A).
  * `Dev` — the DEVICE tag (per-library: `TorchCPU` / `TorchCUDA` / `Host` / `JaxCPU` …):
            where the value resides. A host op on device data is a type error.
  * `D`   — the DTYPE tag (SHARED core vocabulary: `F32` / `F64` / `I32` …): a silent coercion
            is a type error.
  * `S`   — the SHAPE-KIND tag (`Dyn` / `Pow2`, adapter-declared): a shape the target cannot
            accept (a non-pow2 kernel dim) is a type error.

The discipline is LIFTED VERBATIM from `nla_lab/lower/tile.py` (the committed jax/Pallas
reference's `Tile`), with three phantom params added (`L`, `Dev`) and `(D, S)` kept. Its four
load-bearing properties (hardened there against three real CRITICALs) are reproduced here:

  1. NON-COERCIBLE. No `__array__`, `__jax_array__`, `__array_namespace__`, no arithmetic
     dunders, no `__getitem__`. Two consequences, which are the whole design:
       (a) mypy rejects a `Tensor` anywhere an `ArrayLike`/array is expected, so a raw fancy-
           index `a[idx]` or `np.sum(tensor)` / `jnp.matmul(tensor, ...)` does not type-check;
           and
       (b) at RUNTIME, feeding a `Tensor` to ANY un-wrapped native op raises (no library can
           convert a non-coercible object to an array) — the construction-time backstop that
           closes the residual mypy cannot reach (a library's `*args: Any` op).
  2. NON-CONSTRUCTABLE. `__init__` unconditionally RAISES (so `Tensor(...)` is a runtime error
     AND a mypy `[call-arg]` error: no value params), and there is NO importable construction
     TOKEN. The backing object sits in a NAME-MANGLED slot, so the deserialization-shaped
     `object.__new__(Tensor); t._raw = ...` is a mypy `[attr-defined]` AND a runtime
     `AttributeError`. The package mints a `Tensor` ONLY through the package-private `_wrap`
     brand. (Honest residue, ADR-0009: `from .tensor import _wrap; _wrap(x)` can still mint —
     the EXACT symmetric status of `pow2()` bypassing validation; the PUBLIC surface is fully
     closed; a slot write past `_wrap` is unmistakable reflection, the gc-tier not claimed.)
  3. NOT A PYTREE. An opaque leaf — no `tree_map` rewrap re-entry vector. Any control-flow
     carry stays wrap/unwrap-internal to the owning adapter.
  4. ONE SSOT, FOUR AXES + capability. `Tensor` is simultaneously the lib brand, the device
     brand, the dtype phantom, and the shape-kind brand; the capability surface is the adapter
     that accepts it. No second mechanism.

LIBRARY-AGNOSTIC. This module imports NO numerical library — the backing object is typed
`object`, and each adapter narrows it (`cast(torch.Tensor, _unwrap(x))`) at the one place the
phantom meets reality. So `import impedance.tensor` is import-light and host-XOR-device-neutral.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar, cast, final

from impedance.dtype import DType
from impedance.shape import ShapeKind

L = TypeVar("L")  # library tag      (Torch / Numpy / Jax / JaxLower / …)
Dev = TypeVar("Dev")  # device tag       (per-library: TorchCPU / Host / JaxCPU / …)
D = TypeVar("D", bound=DType)  # dtype tag        (SHARED core vocabulary: F32 / F64 / I32 / …)
S = TypeVar("S", bound=ShapeKind)  # shape kind   (SHARED, adapter-declared: Dyn / Pow2)


@final
class Tensor(Generic[L, Dev, D, S]):
    """An opaque tensor handle, phantom-typed by (library, device, dtype, shape-kind). See the
    module docstring: non-coercible, non-constructable, NOT a pytree — its ONLY surface is the
    adapter combinators. The single carrier for every seam."""

    # The backing object lives in a NAME-MANGLED slot (`__raw` -> `_Tensor__raw`), reachable
    # only inside this class body. So the ordinary-attribute mint `object.__new__(Tensor);
    # t._raw = ...` (which reads like plausible deserialization) is BOTH a runtime
    # AttributeError (no `_raw` slot, no `__dict__`) AND a mypy `[attr-defined]` error.
    __slots__ = ("__raw",)
    __raw: object

    def __init__(self) -> None:
        # NO public, clean-idiom construction. `Tensor(...)` lands here and raises; `Tensor(x)`
        # is additionally a mypy `[call-arg]` error (no value params). There is no importable
        # construction token. The package mints a `Tensor` ONLY through `_wrap` (below).
        raise TypeError(
            "Tensor is core-private and NON-CONSTRUCTABLE: a Tensor is born ONLY inside an "
            "impedance adapter combinator (via the package-private _wrap brand). No public "
            "constructor, no importable token.")


# The mangled backing slot's runtime name. Reaching it requires this literal string (or an
# explicit `object.__setattr__` reflection) — ordinary `t._raw`/`t._Tensor__raw` attribute
# syntax is a mypy `[attr-defined]` error, so the only mypy-clean mint is the `_wrap` brand.
_SLOT = "_Tensor__raw"


def _wrap(raw: object) -> Tensor[Any, Any, Any, Any]:
    """Package-internal: mint a `Tensor` around a backing native object, bypassing the raising
    `__init__` via `object.__new__` and seating the mangled slot by its literal name. The ONE
    mint brand. The phantom (L, Dev, D, S) is erased at runtime; the calling combinator restores
    the static `Tensor[L, Dev, D, S]` via its return annotation (an `Any`-parametrized carrier
    is assignable to any concrete one, so a combinator body needs no per-call cast)."""
    t: Tensor[Any, Any, Any, Any] = object.__new__(Tensor)
    object.__setattr__(t, _SLOT, raw)
    return t


def _unwrap(t: Tensor[Any, Any, Any, Any]) -> object:
    """Package-internal: extract a `Tensor`'s backing native object. Used ONLY by the adapters
    (the eager interpreters), each of which narrows the `object` to its own library's array
    type at the call site. Extraction is read-only — a raw object cannot RE-ENTER the algebra
    except through an adapter combinator (the only mint is `_wrap`, and `Tensor` is not a
    pytree, so `tree_map` cannot rewrap)."""
    return cast(object, object.__getattribute__(t, _SLOT))
