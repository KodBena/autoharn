#!/usr/bin/env python
"""tests/test_brand_raises.py — the honest construction-raise residuals (DESIGN.md §2.1/§2.4).

The entry BRAND asserts a raw object's claimed device/dtype at construction — it does not prove
them (a raw tensor carries no static residence/dtype a type can read). This proves that assertion
FIRES: a raw tensor whose actual device or dtype contradicts the claimed brand raises, and the
runtime-dim `pow2()` brand raises on a non-power-of-2 (the 2S-1 trap). These are the named,
non-type-closed seams — demonstrated, not hidden behind the types.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch as _torch

from impedance.dtype import F32
from impedance.lib import numpy as host, torch
from impedance.lib.torch_lib import TorchCPU, TorchCUDA
from impedance.shape import next_pow2, pow2


def test_brand_device_mismatch_raises() -> None:
    cpu_tensor = _torch.zeros((2, 2), dtype=_torch.float32)  # actually on CPU
    with pytest.raises(TypeError, match="device"):
        torch.brand(cpu_tensor, dev=TorchCUDA, dt=F32)       # but claims CUDA


def test_brand_dtype_mismatch_raises() -> None:
    f64_tensor = _torch.zeros((2, 2), dtype=_torch.float64)  # actually float64
    with pytest.raises(TypeError, match="dtype"):
        torch.brand(f64_tensor, dev=TorchCPU, dt=F32)        # but claims F32


def test_numpy_brand_dtype_mismatch_raises() -> None:
    f64 = np.zeros((2, 2), dtype=np.float64)
    with pytest.raises(TypeError, match="dtype"):
        host.brand(f64, dev=host.HOST_DEVICE, dt=F32)


def test_pow2_rejects_the_2s_minus_1_trap() -> None:
    with pytest.raises(ValueError):
        pow2(127)              # 2S-1 for S=64 — exactly one below 128
    assert int(next_pow2(127)) == 128  # ...and next_pow2 rounds it up to a legal kernel dim
    assert int(pow2(128)) == 128       # a true power of two passes


def test_brand_happy_path_succeeds() -> None:
    ok = _torch.zeros((2, 2), dtype=_torch.float32)
    t = torch.brand(ok, dev=TorchCPU, dt=F32)
    assert isinstance(torch.unwrap(t), _torch.Tensor)
