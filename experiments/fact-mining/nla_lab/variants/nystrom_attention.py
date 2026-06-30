#!/usr/bin/env python
"""nystrom_attention — Nyström low-rank attention (throughput lane, APPROXIMATE).

STATUS: STUB. The follow-on agent fills ONLY `encode` (the math) and may tune
`SHORT_S_CROSSOVER` (declared below, one home — not a strewn literal).

SEAM IT REPLACES: ONLY the content stream `softmax(q·kᵀ)` (jax_deberta.py:248-256)
with a landmark/Nyström approximation; it KEEPS the disentangled c2p/p2c terms exact
and separate (the DeBERTa-3-term caution — NLA-OPTIMIZATION-PORTFOLIO.md §3, §6). A
codebase-blind adoption that approximates the whole score (folding the position terms
into the low-rank content approx) is the documented wrong-in-code trap.

FIT PRECONDITION (a-priori retire gate). Linear/landmark attention is contra-indicated
at short S — its constants lose to exact Flash, and matrix-concentration does not bite
on a small [S,S] (NLA-OPTIMIZATION-PORTFOLIO.md §1, §3). So `fit` retires this variant
below a crossover seq length, RECORDED as a portfolio decision (not run as a bad
number).
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, FitVerdict, Regime
from nla_lab.registry import register

#: below this seq_bucket the low-rank content approx is contra-indicated (short-S
#: constants lose to exact Flash; concentration does not bite). ONE home; the
#: follow-on tunes it from the measured crossover, never re-types it per use site.
SHORT_S_CROSSOVER = 512


@register
class NystromAttention(EncodeVariant):
    name = "nystrom_attention"
    regime = Regime.THROUGHPUT
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL  # P6: lhs aggregate distance (cluster-set deferred, DESIGN §5)

    def fit(self, bucket: EncodeBucket) -> FitVerdict:
        if bucket.seq_bucket < SHORT_S_CROSSOVER:
            return FitVerdict(
                False, f"seq_bucket={bucket.seq_bucket} < crossover {SHORT_S_CROSSOVER}: "
                "low-rank content attention contra-indicated at short S (loses to exact "
                "Flash; concentration does not bite) — retired a-priori (portfolio §1/§3).")
        return FitVerdict(True, f"seq_bucket={bucket.seq_bucket} >= crossover {SHORT_S_CROSSOVER}")

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        raise NotImplementedError(
            "nystrom_attention: Nyström-approximate the CONTENT stream only; keep "
            "c2p/p2c disentangled terms exact and separate. "
            "See NLA-OPTIMIZATION-PORTFOLIO.md §3, §6; seam jax_deberta.py:248-256.")
