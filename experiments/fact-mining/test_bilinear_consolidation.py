#!/usr/bin/env python
"""Guest-runnable proof that the consolidated bilinear (`jax_decode._bilinear_coref`)
equals the literal 4-einsum maverick form it replaced.

The 4->1 contraction (four bilinear einsums + four bias einsums -> one each, via the
[S;E] / 2x2-weight-block stacking) is a MATHEMATICAL IDENTITY. This is its falsifier: it
runs on CPU jax (no GPU / maverick), so the algebra is proven here; the end-to-end
discrete-cluster equivalence on maverick's real fine-tuned weights is the host
`--coref-verify` run. fail-loud: a wrong block placement (Wse<->Wes, or a bias mispair)
makes this RED.

Run: `python -m pytest test_bilinear_consolidation.py`  or  `python test_bilinear_consolidation.py`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jax
import jax.numpy as jnp

import jax_decode


def _ref_4einsum(S, E, Wss, Wse, Wes, Wee, Bss, Bse, Bes, Bee):
    """The ORIGINAL literal-4 maverick form (the reference the consolidation must match)."""
    logits = (
        jnp.einsum("nkf, nfg, nlg -> nkl", S, Wss, S)
        + jnp.einsum("nkf, nfg, nlg -> nkl", E, Wee, E)
        + jnp.einsum("nkf, nfg, nlg -> nkl", S, Wse, E)
        + jnp.einsum("nkf, nfg, nlg -> nkl", E, Wes, S)
    )
    biases = (
        jnp.einsum("nkf, nf -> nk", S, Bss)[:, None, :]
        + jnp.einsum("nkf, nf -> nk", E, Bee)[:, None, :]
        + jnp.einsum("nkf, nf -> nk", E, Bse)[:, None, :]
        + jnp.einsum("nkf, nf -> nk", S, Bes)[:, None, :]
    )
    return logits + biases


def test_consolidation_matches_4einsum():
    n, K, f = jax_decode.NUM_CATS, 19, 32  # representative (7 cats, ~tens of mentions)
    ks = jax.random.split(jax.random.PRNGKey(0), 10)
    S = jax.random.normal(ks[0], (n, K, f), jnp.float32)
    E = jax.random.normal(ks[1], (n, K, f), jnp.float32)
    Wss = jax.random.normal(ks[2], (n, f, f), jnp.float32)
    Wse = jax.random.normal(ks[3], (n, f, f), jnp.float32)
    Wes = jax.random.normal(ks[4], (n, f, f), jnp.float32)
    Wee = jax.random.normal(ks[5], (n, f, f), jnp.float32)
    Bss = jax.random.normal(ks[6], (n, f), jnp.float32)
    Bse = jax.random.normal(ks[7], (n, f), jnp.float32)
    Bes = jax.random.normal(ks[8], (n, f), jnp.float32)
    Bee = jax.random.normal(ks[9], (n, f), jnp.float32)

    new = jax_decode._bilinear_coref(S, E, Wss, Wse, Wes, Wee, Bss, Bse, Bes, Bee)
    ref = _ref_4einsum(S, E, Wss, Wse, Wes, Wee, Bss, Bse, Bes, Bee)

    assert new.shape == ref.shape == (n, K, K), (new.shape, ref.shape)
    max_abs = float(jnp.max(jnp.abs(new - ref)))
    # algebraically exact; only float reduction-order noise remains.
    assert max_abs < 1e-4, f"consolidation diverges from the literal-4 form: max|Δ|={max_abs}"


if __name__ == "__main__":
    test_consolidation_matches_4einsum()
    print("PASS — consolidated bilinear == literal-4 einsum form")
