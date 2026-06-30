#!/usr/bin/env python
"""cached_positions — cached disentangled-position logits (EXACT; memory + speed).

STATUS: STUB. The follow-on agent fills ONLY `encode` (the math).

SEAM IT REPLACES: precompute the `_disentangled_bias` body (jax_deberta.py:174-225)
ONCE per `(cfg, s_bucket)` and reuse it across the 24 layers / repeated requests,
instead of recomputing the low-rank c2p/p2c logits over log-bucketed relative
positions every layer. EXACT (a pure memoization of an existing computation). It MAY
read `s_bucket = input_ids.shape[1]` as the cache key (the legitimate use of the
bucket as a key — it does not re-bucket). Touches the memory model
(NLA-OPTIMIZATION-PORTFOLIO.md §6a, §1) — the most natural first NLA-phase action.
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


@register
class CachedPositions(EncodeVariant):
    name = "cached_positions"
    regime = Regime.LATENCY               # cuts recompute on the launch-bound small-batch lane
    fidelity_tier = FidelityTier.EXACT    # pure memoization -> bit-near-identical

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        raise NotImplementedError(
            "cached_positions: memoize _disentangled_bias per (cfg, s_bucket) and "
            "reuse across layers/requests (s_bucket = input_ids.shape[1] as key). "
            "See NLA-OPTIMIZATION-PORTFOLIO.md §6a; seam jax_deberta.py:174-225.")
