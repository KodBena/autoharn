#!/usr/bin/env python
"""tests/fixtures/carrier_neg.py — the carrier-discipline NEGATIVE fixture (mypy regression).

Asserts (via tests/test_typecheck.py running mypy on this file) that the carrier's load-bearing
NON-COERCIBLE / NON-CONSTRUCTABLE discipline is type-enforced: a `Tensor` is rejected wherever an
array/ArrayLike is expected, is not indexable, and cannot be constructed with a value. Each line is
tagged `# EXPECT[<code>]`. Never part of the clean gate; checked by its own test.
"""

from __future__ import annotations

import jax.numpy as jnp

from impedance.dtype import F32
from impedance.lib.jax_lib import Jax, JaxCPU
from impedance.shape import Dyn
from impedance.tensor import Tensor


def _t() -> Tensor[Jax, JaxCPU, F32, Dyn]: raise NotImplementedError


# NON-COERCIBLE: a Tensor is not ArrayLike — feeding it to a native op does not type-check.
# (numpy's `np.asarray` has an object-accepting overload, a known numpy-typing looseness, so the
# runtime backstop in test_carrier_runtime covers the numpy side; jax's stricter `ArrayLike`
# rejects it at the type layer here.)
jnp.sum(_t())  # EXPECT[arg-type]

# NON-COERCIBLE: no __getitem__ — the raw fancy-index (the gather) is not even indexable.
_t()[0]  # EXPECT[index]

# NON-CONSTRUCTABLE: __init__ takes no value params — Tensor(<anything>) is a call-arg error.
Tensor(0)  # EXPECT[call-arg]
