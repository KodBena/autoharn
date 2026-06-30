#!/usr/bin/env python
"""monarch_ffn — Monarch / low-rank FFN (throughput lane, APPROXIMATE).

STATUS: STUB. The follow-on agent fills ONLY `encode` (the math) — replace the two
dense FFN projections with a structured (Monarch block-diagonal / butterfly) or
low-rank `W=UVᵀ` factorization.

SEAM IT REPLACES: the FFN pair in `_layer` (jax_deberta.py:277-284) — the
intermediate `dense` (hidden->4·hidden, gelu) and the output `dense` (4·hidden->hidden).
NOT attention, NOT the projections. The fourth orthogonal seam, completing the proof
that the whole-encode unit accommodates attention / linear / FFN / position-cache
candidates uniformly (NLA-OPTIMIZATION-PORTFOLIO.md §10; the butterfly lineage of §0).
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


@register
class MonarchFFN(EncodeVariant):
    name = "monarch_ffn"
    regime = Regime.THROUGHPUT
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        raise NotImplementedError(
            "monarch_ffn: replace the two FFN dense projections with a Monarch/"
            "block-diagonal or low-rank UVᵀ factorization. "
            "See NLA-OPTIMIZATION-PORTFOLIO.md §10; seam jax_deberta.py:277-284.")
