#!/usr/bin/env python
"""tests/test_jax_lower_parity.py — the lowerable-jax adapter is value-identical to raw jnp.

The §3.3 lift reframes `nla_lab/lower` as one parametric adapter; this asserts the port changed
HOW the kernel is constructed (typed combinators over Pow2 tensors), not WHAT it computes — each
combinator IS its proven `jnp` expression. We verify the centerpiece (the band/onehot/select
GATHER-REPLACEMENT, value-identical to an actual gather) and a composite arithmetic/reduction
expression, self-contained (no nla_lab/jax_deberta import — the standalone extraction bar, §6).
"""

from __future__ import annotations

import jax.numpy as jnp
import numpy as np
import pytest

from impedance.dtype import F32
from impedance.lib import jax_lower, numpy as host
from impedance.shape import pow2


def test_gather_replacement_equals_a_real_gather() -> None:
    # build a [R, W] band of distinct values and a per-row column selector, then select via the
    # onehot+sum replacement; assert it equals the advanced-index gather it stands in for.
    R, W = pow2(2), pow2(4)
    band = jax_lower.ramp2(R, W)                       # ramp2[i,j] = i*W + j
    sel = jax_lower.mod_scalar(jax_lower.iota(R), int(W))
    out = jax_lower.select(band, jax_lower.onehot(sel, W), axis=-1)

    band_raw = (jnp.arange(R)[:, None] * W + jnp.arange(W)[None, :]).astype(jnp.float32)
    sel_raw = jnp.arange(R) % W
    gathered = band_raw[jnp.arange(R), sel_raw]        # the literal gather

    assert jnp.array_equal(jnp.asarray(jax_lower.unwrap(out)), gathered)


def test_arithmetic_reduction_parity() -> None:
    n = pow2(8)
    a = jax_lower.cast(jax_lower.iota(n), F32)         # [0, 1, ..., 7] as f32 (the dtype crossing)
    b = jax_lower.full(n, 2.0)                         # [2, 2, ..., 2]
    c = jax_lower.mul(a, b)                            # [0, 2, 4, ..., 14]
    s = jax_lower.rsum(c, axis=0)                      # scalar 56.0

    expected = jnp.sum(jnp.arange(n, dtype=jnp.float32) * jnp.full((n,), 2.0, jnp.float32))
    assert jnp.array_equal(jnp.asarray(jax_lower.unwrap(s)), expected)


def test_cast_is_the_only_dtype_crossing() -> None:
    # the dtype seam: iota is I32; turning it into an F32 tile is the explicit cast, value-faithful.
    n = pow2(4)
    f = jax_lower.cast(jax_lower.iota(n), F32)
    assert np.asarray(jax_lower.unwrap(f)).dtype == np.float32
    assert jnp.array_equal(jnp.asarray(jax_lower.unwrap(f)), jnp.arange(n, dtype=jnp.float32))


def test_as_pow2_admits_external_host_data() -> None:
    # the D2 fix: external host data enters the lowerable adapter via the checked Dyn->Pow2
    # promotion, then a Pow2-only kernel op runs on it — proving the centerpiece composes through
    # the bridge, not only in isolation. A [4, 4] host buffer (both dims powers of two) promotes,
    # and the value is preserved.
    buf = host.brand(np.arange(16, dtype=np.float32).reshape(4, 4), dev=host.HOST_DEVICE, dt=F32)
    kt = jax_lower.as_pow2(jax_lower.import_host(buf))  # Dyn -> Pow2, checked
    out = jax_lower.rsum(kt, axis=-1)                    # a Pow2-only capability now reachable
    assert jnp.array_equal(
        jnp.asarray(jax_lower.unwrap(out)),
        jnp.sum(jnp.arange(16, dtype=jnp.float32).reshape(4, 4), axis=-1),
    )


def test_as_pow2_raises_on_non_pow2_extent() -> None:
    # the honest construction-raise dual of pow2(): a non-power-of-2 dim cannot be promoted — the
    # shape-kind entry assertion fires (the 2S-1 trap, here a [3, 4] buffer with a non-pow2 first dim).
    buf = host.brand(np.zeros((3, 4), dtype=np.float32), dev=host.HOST_DEVICE, dt=F32)
    with pytest.raises(ValueError):
        jax_lower.as_pow2(jax_lower.import_host(buf))
