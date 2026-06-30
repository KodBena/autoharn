#!/usr/bin/env python
"""tests/test_carrier_runtime.py — the carrier discipline at RUNTIME (the construction backstop).

Complements the type-layer regression (tests/fixtures/carrier_neg.py): proves the carrier is
NON-CONSTRUCTABLE (the public ctor raises; no clean-idiom mint) and NON-COERCIBLE (feeding a
`Tensor` to an un-wrapped native op raises — the backstop that closes the residual mypy cannot
reach, e.g. numpy's object-accepting `asarray` overload).
"""

from __future__ import annotations

import numpy as np
import pytest

from impedance.dtype import F32
from impedance.lib import jax, numpy as host
from impedance.tensor import Tensor, _wrap


def _a_tensor() -> Tensor[object, object, F32, object]:
    return host.brand(np.zeros((2, 2), dtype=np.float32), dev=host.HOST_DEVICE, dt=F32)


def test_tensor_is_non_constructable() -> None:
    with pytest.raises(TypeError, match="NON-CONSTRUCTABLE"):
        Tensor()  # the public ctor raises; there is no clean-idiom mint


def test_tensor_has_no_dict_and_mangled_slot() -> None:
    # the deserialization-shaped mint `object.__new__(Tensor); t._raw = ...` cannot seat the slot.
    t = _a_tensor()
    with pytest.raises(AttributeError):
        object.__getattribute__(t, "_raw")  # the un-mangled name does not exist


def test_tensor_non_coercible_under_jax() -> None:
    yj = jax.import_host(_a_tensor())  # a real Jax-tagged carrier
    import jax.numpy as jnp
    with pytest.raises(Exception):
        jnp.sum(yj)  # the opaque carrier cannot be coerced to a jax array — raises at trace


def test_wrap_unwrap_roundtrips_internally() -> None:
    arr = np.arange(6, dtype=np.float32)
    t = _wrap(arr)
    assert host.unwrap(t) is arr  # the one mint path is value-faithful
