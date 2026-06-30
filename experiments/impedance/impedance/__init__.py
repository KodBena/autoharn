#!/usr/bin/env python
"""impedance — the library-parametric (lib, device, dtype, shape) tensor ACL.

A tagless-final typed-combinator embedded DSL with ONE opaque carrier `Tensor[L, Dev, D, S]`, a
library-agnostic CORE, and per-library ADAPTERS. Cross-library interface impedances are
UNCONSTRUCTABLE by construction (a `mypy --strict` error, or a non-existent constructor):

  * lib    — handing library A's value to library B's op (a torch tensor to a jax op) without
             the marked host bridge is a mypy `[arg-type]`.
  * device — host code touching device data (a CUDA torch tensor to numpy) without a marked
             device transfer is a mypy `[arg-type]`.
  * dtype  — a silent coercion (`float64` where `float32` is required) is a mypy `[arg-type]`;
             the only dtype change is the explicit `adapter.cast(x, F32)`.
  * shape  — a shape the target cannot accept (a non-pow2 kernel dim) is a mypy `[arg-type]` /
             a `pow2()` construction-raise.
  * capability — using an op the target adapter lacks is a mypy `[attr-defined]`.

It GENERALIZES the library axis of `nla_lab/lower` (the committed tagless-final four-seam closure
for jax/Pallas): that package's single implicit interpreter (jax) becomes one ADAPTER among many,
and the carrier gains a library tag so the type system names which interpreter owns a value.

The CORE (this module's re-exports) imports NO numerical library; each adapter in `impedance.lib`
imports exactly its own library, lazily — so `import impedance` is import-light.
"""

from __future__ import annotations

from impedance.adapter import LibAdapter
from impedance.dtype import BoolT, DType, F32, F64, I32, I64
from impedance.host import Host, HostBuffer, Numpy, bridge
from impedance.shape import Dyn, Pow2, Pow2Dim, ShapeKind, next_pow2, pow2
from impedance.tensor import Tensor

__all__ = [
    "Tensor",
    "LibAdapter",
    "bridge",
    "HostBuffer",
    "Numpy",
    "Host",
    "DType",
    "F32",
    "F64",
    "I32",
    "I64",
    "BoolT",
    "ShapeKind",
    "Dyn",
    "Pow2",
    "Pow2Dim",
    "pow2",
    "next_pow2",
]
