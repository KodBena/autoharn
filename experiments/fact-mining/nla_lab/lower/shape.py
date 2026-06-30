#!/usr/bin/env python
"""nla_lab.lower.shape — the power-of-2 shape SSOT for the lowerable kernel algebra.

`Pow2` / `pow2()` / `next_pow2()` live HERE (P1: one home). They were the working shape
ACL inside `_pallas_disent_attention.py`; the algebra GENERALIZES them from "block dims
only" to EVERY shape-fixing combinator parameter (see `lower/ops.py`), so they are now the
SSOT the whole algebra shares rather than one kernel's local helper. The definitions are
unchanged — `_pallas_disent_attention` now imports them from here (re-export for the
existing call sites), and every `ops` constructor that fixes an array dimension takes a
`Pow2`, making the 2S-1 trap unconstructable across the surface.

HOST-XOR-DEVICE. Pure-python int arithmetic; imports neither numpy nor a device lib.
"""

from __future__ import annotations

from typing import NewType

# ----------------------------------------------------- the power-of-2 invariant, by TYPE (ADR-0000)
# The Pallas-Triton lowering REJECTS any array shape that is not a power of 2 ("requires that all
# operations have array arguments and results whose size is a power of 2"). The bug that shipped:
# the relative-offset count 2S-1 — exactly ONE below the power of 2 2S — flowed unguarded into the
# kernel, and interpret mode (CPU) does not enforce the rule, so it only detonated on the host.
# Rather than CHECK the invariant at runtime, we make a non-pow2 kernel dimension UNCONSTRUCTABLE:
# `Pow2` is a NewType whose ONLY source is `pow2()`, which validates. So (a) mypy rejects a raw int
# where a kernel signature wants a `Pow2`, and (b) `pow2()` rejects a non-pow2 VALUE at the kernel
# boundary with a clear guest-side error. 2S-1 cannot become a `Pow2`; it cannot reach Triton.
Pow2 = NewType("Pow2", int)


def pow2(n: int) -> Pow2:
    """The single source of `Pow2` values — brand `n` as a power of two, or raise. A `Pow2`
    carries the proof; downstream code uses it as a plain int (NewType), but a non-pow2 (e.g.
    2S-1 = 127) cannot get past this constructor."""
    if n <= 0 or (n & (n - 1)) != 0:
        raise ValueError(
            f"kernel dimension {n} is not a power of 2 — Pallas-Triton requires every array shape "
            f"be a power of 2. The classic trap is the relative-offset count 2S-1 (one below the "
            f"power of 2 2S): every kernel array dim (block_q/block_k/S/d/W) must be a true pow2.")
    return Pow2(n)


def next_pow2(n: int) -> int:
    """Smallest power of two `>= n` (for `n >= 1`). Used to size the band width `W` from the
    offset-range width `block_q + block_k - 1`: the (i-j) offsets a (qt,kt) tile spans are a
    contiguous range of that width, so the bucket-column range it can reference fits a single
    `pl.ds(base, W)` slice once `W` is rounded UP to a power of two (Triton's shape rule —
    branded `Pow2` at the kernel boundary, never raw)."""
    return 1 << (n - 1).bit_length()
