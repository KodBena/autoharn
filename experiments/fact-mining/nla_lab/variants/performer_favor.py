#!/usr/bin/env python
"""performer_favor — Performer / FAVOR+ (or Linformer) linear attention (throughput,
APPROXIMATE).

STATUS: STUB. The follow-on agent fills ONLY `encode` (the math) and may tune
`CONCENTRATION_S_CROSSOVER` (declared below, one home).

SEAM IT REPLACES: ONLY the content stream `softmax(q·kᵀ)` (jax_deberta.py:248-256)
with a random-feature (FAVOR+) / low-rank (Linformer) linear-attention kernel; KEEPS
the disentangled c2p/p2c terms exact and separate (NLA-OPTIMIZATION-PORTFOLIO.md §3).

FIT PRECONDITION: random-feature concentration needs matrices large enough for the
estimator to concentrate; at short S the variance dominates and exact Flash wins
(portfolio §1, §3). `fit` retires below the crossover, RECORDED as a portfolio
decision.
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, FitVerdict, Regime
from nla_lab.registry import register

#: below this seq_bucket the random-feature estimator does not concentrate usefully;
#: ONE home, tuned by the follow-on from the measured crossover.
CONCENTRATION_S_CROSSOVER = 512


@register
class PerformerFavor(EncodeVariant):
    name = "performer_favor"
    regime = Regime.THROUGHPUT
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL

    def fit(self, bucket: EncodeBucket) -> FitVerdict:
        if bucket.seq_bucket < CONCENTRATION_S_CROSSOVER:
            return FitVerdict(
                False, f"seq_bucket={bucket.seq_bucket} < crossover "
                f"{CONCENTRATION_S_CROSSOVER}: random-feature attention does not "
                "concentrate at short S — retired a-priori (portfolio §1/§3).")
        return FitVerdict(True, f"seq_bucket={bucket.seq_bucket} >= crossover "
                          f"{CONCENTRATION_S_CROSSOVER}")

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        raise NotImplementedError(
            "performer_favor: FAVOR+/Linformer linearization of the CONTENT stream "
            "only; keep c2p/p2c disentangled terms exact. "
            "See NLA-OPTIMIZATION-PORTFOLIO.md §3; seam jax_deberta.py:248-256.")
