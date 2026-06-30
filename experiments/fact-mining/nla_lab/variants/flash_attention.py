#!/usr/bin/env python
"""flash_attention — FlashAttention (EXACT), the portfolio keystone.

STATUS: STUB. The follow-on agent fills ONLY `encode` (the math); the contract,
registry, bucketing, and bench are done and frozen.

SEAM IT REPLACES: the score-materialize + softmax + context in `_self_attention`
(jax_deberta.py:248-258) — without ever materializing the `[B,H,S,S]` matrix. It must
FOLD `rel_att` from `_disentangled_bias` (jax_deberta.py:250) into the kernel bias so
the disentangled c2p/p2c terms stay exact (NLA-OPTIMIZATION-PORTFOLIO.md §5, §10.2).
Exact, and it deletes the `B·H·S²` materialization that the OOM memory model bounds.
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


@register
class FlashAttention(EncodeVariant):
    name = "flash_attention"
    regime = Regime.BOTH                  # exact; relaxes the OOM bound (both lanes)
    fidelity_tier = FidelityTier.EXACT    # exact reformulation, ~1e-5 reduction-order

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        raise NotImplementedError(
            "flash_attention: tiled exact attention folding the disentangled rel_att "
            "bias into the kernel (no [B,H,S,S] materialize). "
            "See NLA-OPTIMIZATION-PORTFOLIO.md §5, §10.2; seam jax_deberta.py:248-258.")
