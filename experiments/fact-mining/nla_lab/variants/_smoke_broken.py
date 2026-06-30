#!/usr/bin/env python
"""_smoke_broken — a DELIBERATELY broken variant, the bench's watchdog smoke test
(ported from control_lab's MalfunctioningController, A10).

Underscore-prefixed `name` -> EXCLUDED from `registry.portfolio_names()` (the default
sweep), invoked only by the harness self-test to PROVE the bench's fidelity/shape
guard catches a malformed variant: it returns a wrong-shape, NaN-poisoned array, and
the bench must record a FAILURE (status failed_shape / failed_nonfinite) and CONTINUE
the sweep without tearing down the warm fixture — never silently substitute a clean
output (B8: in a BENCH lane numerical misbehavior is a LOUD flagged failure, not a
clamped low score).
"""

from __future__ import annotations

import jax
import jax.numpy as jnp
import jax_deberta
from nla_lab.contract import EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


@register
class SmokeBroken(EncodeVariant):
    name = "_smoke_broken"
    regime = Regime.BOTH
    fidelity_tier = FidelityTier.EXACT   # CLAIMS exact, then violates it — the test
    IMPLEMENTED = True   # its encode IS filled (deliberately broken output) — not a stub;
    #: kept honest so a reader never mistakes the watchdog fixture for an unfilled skeleton.
    #: (Underscore-prefixed -> excluded from portfolio_names(), so the self-proof's per-
    #: variant IMPLEMENTED check never reads it; the bench catches its bad OUTPUT instead.)

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # Wrong shape (drops the hidden axis) AND NaN-poisoned: the guard must reject
        # on shape first; a shape-correct NaN variant would trip the finiteness check.
        b, s = input_ids.shape
        return jnp.full((b, s), jnp.nan, dtype=jnp.float32)
