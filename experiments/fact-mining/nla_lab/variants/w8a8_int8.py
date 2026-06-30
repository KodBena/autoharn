#!/usr/bin/env python
"""w8a8_int8 — W8A8 INT8 encode (throughput lane, APPROXIMATE).

STATUS: STUB. The follow-on agent fills ONLY `encode` (the math) — a params transform
(quantize weights to int8 + per-channel scales) plus int8 `lax.dot_general` at every
projection.

SEAM IT REPLACES: `_linear` (jax_deberta.py:115-117) at EVERY projection
(q/k/v/dense/intermediate/output) — NOT attention. This is the orthogonal-seam proof
the whole-encode unit exists for: a "single attention op" type could not represent
this variant at all (NLA-OPTIMIZATION-PORTFOLIO.md §10). Compute-bound large-batch
win (int8 matmul throughput).

MEMORY (R-MEM — override mandate). int8 activations are 1 byte/elem (vs the dense fp32 4), so
this technique CHANGES the variable-memory profile. The follow-on implementer MUST OVERRIDE
`est_peak_device_bytes` with a re-parameterised `shape_buckets.MemModel` (smaller
`bytes_per_elem`) fed to `peak_variable_bytes` — NOT a hand-rolled second model — so the
recorded estimate is not silently the dense fp32 bound. The stub keeps the default for now.
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


@register
class W8A8Int8(EncodeVariant):
    name = "w8a8_int8"
    regime = Regime.THROUGHPUT            # int8 matmul pays on the compute-bound lane
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        raise NotImplementedError(
            "w8a8_int8: int8-quantize weights+activations and run int8 lax.dot_general "
            "at every _linear projection (q/k/v/dense/intermediate/output). "
            "See NLA-OPTIMIZATION-PORTFOLIO.md §10; seam jax_deberta.py:115-117.")
