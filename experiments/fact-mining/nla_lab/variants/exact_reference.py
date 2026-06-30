#!/usr/bin/env python
"""exact_reference — the REQUIRED baseline variant (A8): the current dense
disentangled-attention DeBERTa encode, registered as a variant by delegating
straight to `jax_deberta.encode` (jax_deberta.py:352).

THIS IS THE HARNESS SELF-PROOF (ADR-0013 "prove it with a working impl that
round-trips, or it isn't done"). It is the A/B control arm and the seam where every
real NLA policy plugs in. Its fidelity-vs-ITSELF is 0 by construction (same function,
same inputs -> bit-identical output) — so if it resolves through the registry, runs
through the bench, and reports max|Δ|==0 against the reference (itself), the whole
contract+registry+bench is proven end to end. Its fidelity vs vanilla HF DeBERTa is
the existing ~1e-3 gate in test_deberta_fidelity.py (the AutoModel round-trip) — this
variant reuses the SAME `jax_deberta.encode` that test already falsifies, so no second
fidelity claim is minted here.

NO REIMPLEMENTATION (ADR-0012 P1). It calls the existing `jax_deberta.encode` — it
does not re-author the forward, the bucketing (upstream in the host shell), or the
rel-pos hoist. The unit is the whole encode; this one delegates the whole encode.

HOST-XOR-DEVICE. Imports `jax_deberta` (the neutrally-named device core) + the
contract; no numpy. The XOR-gate sees no host lib -> clean.
"""

from __future__ import annotations

import jax
import jax_deberta
from nla_lab.contract import EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


@register
class ExactReference(EncodeVariant):
    name = "exact_reference"
    regime = Regime.BOTH            # the dense baseline runs in either lane
    fidelity_tier = FidelityTier.EXACT  # it IS the reference: max|Δ| vs itself == 0
    IMPLEMENTED = True              # the one filled variant (delegates to jax_deberta.encode)

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # jax_deberta is a declared mypy stub-gap (mypy.ini skip); its Array result
        # is returned as the contract's jax.Array (named relaxation, ADR-0012 P8).
        return jax_deberta.encode(  # type: ignore[no-any-return]
            params, input_ids, attention_mask, cfg)
