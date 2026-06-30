#!/usr/bin/env python
"""impedance.shape — the SHARED, adapter-declared shape kinds, plus the power-of-2 dim brand.

Two distinct things live here, and the distinction is load-bearing:

  1. The SHAPE KIND (`ShapeKind` family) — the phantom type parameter `S` of the carrier
     `Tensor[L, Dev, D, S]`. The core ships two kinds, and an adapter DESCRIBES ITS SHAPE
     MODEL by which kind it brands its tensors with:

       * `Dyn`  — the untracked dynamic shape. Operand-shape *agreement* (`[m,k]·[k,n]`) is
                  interpret/runtime-checked, NOT type-carried — the deliberate, honest stop
                  (full shape tuples are not phantom-typed; see DESIGN.md §2.4). The demo's
                  general adapters use `Dyn`, so the pipeline reads naturally and a shape
                  mismatch is a clear runtime error rather than type noise.
       * `Pow2` — the power-of-2 shape kind. A kernel/Pallas adapter (`lib/jax_lower_lib.py`)
                  *declares its shape model as `Pow2`*, so a `Pow2`-demanding adapter cannot
                  be handed a `Dyn` tensor (the kinds do not unify) — the shape seam is
                  type-closed where the constraint is a static brand.

  2. The DIMENSION VALUE BRAND (`Pow2Dim` / `pow2()`) — a power-of-2 *integer*, lifted
     VERBATIM from `nla_lab/lower/shape.py` (the committed jax/Pallas reference). The kernel
     adapter's constructors take `Pow2Dim` dims, so a raw `int` dimension is a mypy
     `[arg-type]` error, and a runtime-derived non-pow2 (the classic `2S-1` trap) cannot be
     branded — `pow2()` raises. This is the §2.4 honest split: type-closed for a static dim,
     construction-raise for a runtime one.

LIBRARY-AGNOSTIC. Pure-python; imports NO numerical library.
"""

from __future__ import annotations

from typing import NewType

# ----------------------------------------------------------------- the shape KINDS (carrier S)


class ShapeKind:
    """Phantom base — the type-level shape-kind tag. Never instantiated."""

    __slots__ = ()

    def __init__(self) -> None:  # pragma: no cover - phantom, never constructed
        raise TypeError("ShapeKind tags are phantom type parameters; they are never instantiated.")


class Dyn(ShapeKind):
    """Phantom tag: an untracked dynamic shape. Operand agreement is interpret/runtime-checked
    (the honest stop — full shape tuples are not phantom-typed; DESIGN.md §2.4)."""

    __slots__ = ()


class Pow2(ShapeKind):
    """Phantom tag: a power-of-2 shape (a kernel/Pallas shape model). An adapter that declares
    `shape_kind() == Pow2` brands its tensors with this kind; a `Dyn` tensor does not unify
    with it, so a `Dyn` value cannot reach a `Pow2`-demanding adapter (type-closed)."""

    __slots__ = ()


# --------------------------------------------------------------- the power-of-2 DIM VALUE brand
# Lifted VERBATIM from nla_lab/lower/shape.py (the committed jax/Pallas reference). The
# Pallas-Triton lowering REJECTS any array dimension that is not a power of 2. Rather than
# CHECK at runtime, a non-pow2 kernel dimension is made UNCONSTRUCTABLE: `Pow2Dim` is a
# NewType whose ONLY source is `pow2()`, which validates. So (a) mypy rejects a raw int where
# a kernel constructor wants a `Pow2Dim`, and (b) `pow2()` rejects a non-pow2 VALUE (the 2S-1
# trap, e.g. 127) at construction with a clear error. 2S-1 cannot become a `Pow2Dim`.
Pow2Dim = NewType("Pow2Dim", int)


def pow2(n: int) -> Pow2Dim:
    """The single source of `Pow2Dim` values — brand `n` as a power of two, or raise. A
    `Pow2Dim` carries the proof; downstream code uses it as a plain int (NewType), but a
    non-pow2 (e.g. 2S-1 = 127) cannot get past this constructor."""
    if n <= 0 or (n & (n - 1)) != 0:
        raise ValueError(
            f"kernel dimension {n} is not a power of 2 — a Pallas/Triton-style kernel adapter "
            f"requires every array dimension be a power of 2. The classic trap is the relative-"
            f"offset count 2S-1 (one below the power of 2 2S): brand only true powers of two.")
    return Pow2Dim(n)


def next_pow2(n: int) -> Pow2Dim:
    """Smallest power of two `>= n` (for `n >= 1`), already branded. Rounds a runtime extent
    UP to a kernel-legal dimension (the band-width discipline of the jax/Pallas reference)."""
    if n < 1:
        raise ValueError(f"next_pow2 needs n >= 1, got {n}")
    return Pow2Dim(1 << (n - 1).bit_length())
