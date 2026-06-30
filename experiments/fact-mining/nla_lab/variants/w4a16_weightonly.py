#!/usr/bin/env python
"""w4a16_weightonly — W4A16 weight-only quant (latency lane, APPROXIMATE).

STATUS: STUB. The follow-on agent fills ONLY `encode` (the math) — int4-pack weights
+ scales, dequantize-on-load into the fp16/fp32 matmul at every projection.

SEAM IT REPLACES: the weight load inside `_linear` (jax_deberta.py:115-117) at every
projection — int4 weights, fp16 activations. The win is the BANDWIDTH term: fewer
weight bytes to move, which is exactly what pays on our dispatch/launch-bound
small-batch encode (NLA-OPTIMIZATION-PORTFOLIO.md §1, §10). Hence regime=latency,
distinct from W8A8 (throughput).
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


@register
class W4A16WeightOnly(EncodeVariant):
    name = "w4a16_weightonly"
    regime = Regime.LATENCY              # bandwidth (fewer weight bytes) wins the launch-bound lane
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        raise NotImplementedError(
            "w4a16_weightonly: int4-pack weights + scales, dequant-on-load into the "
            "fp16 matmul at every _linear projection (bandwidth-cut, latency lane). "
            "See NLA-OPTIMIZATION-PORTFOLIO.md §1, §10; seam jax_deberta.py:115-117.")
