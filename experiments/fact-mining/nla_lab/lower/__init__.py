#!/usr/bin/env python
"""nla_lab.lower — the lowerable kernel algebra (SETTLED design; see DESIGN.md).

A tagless-final typed-combinator embedded DSL with ONE opaque carrier (`Tile`) and smart
constructors (`ops`), whose signatures make the four interface impedances UNCONSTRUCTABLE
(a mypy error / a non-existent constructor / a trace-time raise), in one composable SSOT:

  * lib    — a non-Pallas/Triton-lowerable op (gather; a batched `dot_general` from a
             shared-index einsum) is not in the `ops` surface and cannot be built from the
             non-coercible carrier.
  * device — host code touching device data is a type error (`Tile` vs host `int`/`float`).
  * dtype  — a silent `float->int` coercion is a type error (only `ops.to_i32` crosses).
  * shape  — a non-power-of-2 kernel dim is a type error / `pow2()` raise (`Pow2`).

The carrier folds to LOWERABLE jax/Pallas primitives and hands them to `pl.pallas_call`,
which Pallas lowers and XLA fuses. We constrain only our INPUT to the stack; we never reach
past it (no Triton emission, no `triton.compile`, no `jax.ffi`).

HOST-XOR-DEVICE. The carrier/ops/kernel files are device-only (jax, no numpy); `shape`/
`dtype` are pure-python tags. See test_import_xor.py / test_device_transfers.py SCANNED.
"""

from __future__ import annotations

from nla_lab.lower import ops
from nla_lab.lower.dtype import BoolT, DType, F32, I32
from nla_lab.lower.shape import Pow2, next_pow2, pow2
from nla_lab.lower.tile import Idx, Tile

__all__ = [
    "ops",
    "Tile", "Idx",
    "DType", "F32", "I32", "BoolT",
    "Pow2", "pow2", "next_pow2",
]
