#!/usr/bin/env python
"""HOST pre-check: does maverick's FINE-TUNED deberta convert cleanly to the JAX port?

The jax-deberta port (jax_deberta.py) was fidelity-proven against VANILLA deberta-v3-large
on the guest (max|Δ|=3e-5). Before the unified-daemon integration, this confirms maverick's
*fine-tuned* checkpoint is the same architecture and converts through the SAME keyset-guarded
path — i.e. that params_from_state_dict's fail-loud asserts (share_att_key=True,
hidden_act=='gelu', and set(converted)==jax_deberta.param_keys bijection) are HAPPY with
maverick's real weights, not just the vanilla model.

Run on the HOST (maverick is host-only); no GPU needed, no daemons needed:

    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python validate_deberta_keyset.py

PASS  => the integration's weight path is safe (the guard fails loud if anything ever diverges).
RAISE => maverick's deberta diverges from the port's assumptions (config or tensor set); the
         message names exactly which — that is the thing to resolve before integrating.
"""
from __future__ import annotations


def main() -> int:
    from maverick import Maverick
    from maverick_load import safe_maverick_load

    import deberta_weights

    with safe_maverick_load():
        mav = Maverick(device="cpu")  # weight conversion only — no forward, no GPU
    mav.model.float()                 # match the daemon's fp32 contract
    enc = mav.model.encoder           # the DebertaV2Model maverick encodes with
    print(f"maverick encoder: {type(enc).__name__} | config: {type(enc.config).__name__}",
          flush=True)

    # cfg_from_hf asserts share_att_key / hidden_act; params_from_state_dict asserts the
    # converted keyset == jax_deberta.param_keys(cfg) exactly (the 390-key bijection). Any
    # divergence in maverick's fine-tuned checkpoint raises here with the offending keys.
    cfg = deberta_weights.cfg_from_hf(enc.config)
    params = deberta_weights.params_from_state_dict(enc.state_dict(), cfg)

    print(f"PASS — maverick deberta -> JAX pytree: {len(params)} params, keyset bijection holds.",
          flush=True)
    print("The unified encode+decode JAX daemon's weight path is safe to build.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
