#!/usr/bin/env python
"""impedance.dtype — the SHARED phantom dtype tags (the core's dtype vocabulary).

These classes are NEVER instantiated. They exist only as the phantom type parameter `D`
of the carrier `Tensor[L, Dev, D, S]` (see `tensor.py`): `Tensor[Torch, TorchCPU, F32, S]`
is a float32 torch tile, `Tensor[Jax, JaxCPU, F64, S]` a float64 jax array, and so on. The
SAME tag instance flows across every library and every host bridge — there is ONE `F32`,
shared — which is exactly what lets a host bridge PRESERVE dtype in its signature (see
`host.py`) and an op pin it across operands.

They make the dtype SEAM type-closed: every adapter combinator pins `D`, so passing `F64`
where `F32` is required is a mypy `[arg-type]` error, and the ONLY way to change a tensor's
dtype is the explicit, diff-visible `adapter.cast(x, F32)` (the carrier exposes no `.astype`,
no coercion). A silent `float64 -> float32` is therefore UNCONSTRUCTABLE.

These are the CORE vocabulary, shared by every adapter. An adapter DECLARES which of these it
supports via its `supports_dtype`; the tag set itself is library-agnostic.

LIBRARY-AGNOSTIC. Pure-python marker classes; this module imports NO numerical library.
"""

from __future__ import annotations


class DType:
    """Phantom base — the type-level dtype tag. Never instantiated."""

    __slots__ = ()

    def __init__(self) -> None:  # pragma: no cover - phantom, never constructed
        raise TypeError("DType tags are phantom type parameters; they are never instantiated.")


class F32(DType):
    """Phantom tag: a 32-bit float element dtype."""

    __slots__ = ()


class F64(DType):
    """Phantom tag: a 64-bit float element dtype."""

    __slots__ = ()


class I32(DType):
    """Phantom tag: a 32-bit signed-integer element dtype."""

    __slots__ = ()


class I64(DType):
    """Phantom tag: a 64-bit signed-integer element dtype."""

    __slots__ = ()


class BoolT(DType):
    """Phantom tag: a boolean (predicate) element dtype."""

    __slots__ = ()
