#!/usr/bin/env python
"""torch -> JAX weight + config conversion for the DeBERTa-v2/v3 encoder.

THIS IS THE HOST<->DEVICE BOUNDARY (ADR-0012 P7, P9 imperative shell). It imports
torch + numpy + jax in one file ON PURPOSE: its whole job is to translate the HF
torch reference (state_dict + config) into the jax pytree + `DebertaCfg` the pure
device core `jax_deberta.py` consumes. It is NEUTRALLY NAMED (not `jax_*`/`torch_*`)
because an honest device-named file may not import numpy; this is the one audited
seam where the two meet, exactly like `capture_fixtures.py`. It is therefore NOT in
the import-XOR composed-pipeline SCANNED set — it is the declared fixture/conversion
boundary, the single home of the torch<->jax crossing (ADR-0012 P1: one home).

DERIVE-DON'T-RE-AUTHOR (ADR-0012 P7). Two facts cross this boundary and BOTH are
derived from the HF authority, never hand-mirrored:
  * the WEIGHTS — every `state_dict()` tensor becomes a jax array under its
    ORIGINAL torch key (no rename table that could drift); torch nn.Linear weight
    layout [out, in] is preserved as-is, `jax_deberta._linear` transposes at use.
  * the CONFIG — `DebertaCfg` is computed from the live `DebertaV2Config`, so every
    architecture hyperparameter has one home (the HF config), read here, not a
    constant retyped in the device file.
"""

from __future__ import annotations

import jax.numpy as jnp
import numpy as np
import torch

from jax_deberta import DebertaCfg, param_keys


def cfg_from_hf(hf_config) -> DebertaCfg:
    """Build the jit-static DebertaCfg from a live transformers.DebertaV2Config.

    Mirrors the resolution logic in DisentangledSelfAttention.__init__ /
    DebertaV2Encoder.__init__: max_relative_positions < 1 falls back to
    max_position_embeddings; pos_ebd_size (att_span) is position_buckets when > 0
    else max_relative_positions; scale_factor = 1 + c2p + p2c."""
    num_heads = hf_config.num_attention_heads
    head_size = getattr(hf_config, "attention_head_size", hf_config.hidden_size // num_heads)
    max_rel = getattr(hf_config, "max_relative_positions", -1)
    if max_rel < 1:
        max_rel = hf_config.max_position_embeddings
    position_buckets = getattr(hf_config, "position_buckets", -1)
    pos_ebd_size = position_buckets if position_buckets > 0 else max_rel
    pos_att_type = hf_config.pos_att_type if hf_config.pos_att_type is not None else []
    has_c2p = "c2p" in pos_att_type
    has_p2c = "p2c" in pos_att_type
    scale_factor = 1 + int(has_c2p) + int(has_p2c)

    # Guard the assumptions the device core mirrors (deberta-v3-large): no absolute
    # position embedding, no token type, no embed_proj, no conv, no z_steps. These
    # are fail-loud (ADR-0002): a checkpoint that violates them must NOT be silently
    # run through a core that ignores those weights.
    assert getattr(hf_config, "relative_attention", False), "encoder mirrors relative_attention=True only"
    assert not getattr(hf_config, "position_biased_input", True), "core assumes position_biased_input=False"
    assert hf_config.type_vocab_size <= 0, "core assumes no token_type embeddings"
    assert getattr(hf_config, "embedding_size", hf_config.hidden_size) == hf_config.hidden_size, \
        "core assumes embedding_size == hidden_size (no embed_proj)"
    assert getattr(hf_config, "conv_kernel_size", 0) <= 0, "core assumes no ConvLayer"
    assert "layer_norm" in [x.strip() for x in getattr(hf_config, "norm_rel_ebd", "none").lower().split("|")], \
        "core assumes norm_rel_ebd contains layer_norm"
    # share_att_key is config-driven in HF (default FALSE, modeling_deberta_v2.py:168).
    # jax_deberta._disentangled_bias hardcodes the share_att_key=True branch (pos
    # projections REUSE query_proj/key_proj). A share_att_key=False checkpoint has
    # SEPARATE pos_key_proj/pos_query_proj weights and would be silently computed from
    # the wrong (content) projections -> fail loud (ADR-0002). The keyset check in
    # params_from_state_dict is the exhaustive backstop (it would flag the extra
    # pos_*_proj tensors); this assert gives the precise diagnosis first.
    assert getattr(hf_config, "share_att_key", False), \
        "core mirrors share_att_key=True only (pos projections reuse query_proj/key_proj)"
    # hidden_act is config-driven in HF (ACT2FN[hidden_act], modeling_deberta_v2.py:394).
    # jax_deberta._gelu hardcodes the EXACT-erf form ('gelu'); a 'gelu_new'/
    # 'gelu_pytorch_tanh' (tanh-approx) checkpoint would be silently wrong -> fail loud.
    assert hf_config.hidden_act == "gelu", \
        f"core hardcodes exact-erf GELU; config.hidden_act={hf_config.hidden_act!r} != 'gelu'"

    return DebertaCfg(
        num_layers=hf_config.num_hidden_layers,
        num_heads=num_heads,
        head_size=head_size,
        position_buckets=position_buckets,
        max_relative_positions=max_rel,
        pos_ebd_size=pos_ebd_size,
        scale_factor=scale_factor,
        has_c2p=has_c2p,
        has_p2c=has_p2c,
        layer_norm_eps=float(hf_config.layer_norm_eps),
    )


def params_from_state_dict(state_dict: dict, cfg: DebertaCfg) -> dict:
    """Convert a DebertaV2Model.state_dict() to a flat {torch_key: jax.Array} pytree.

    No rename, no transpose: the key IS the torch key, the layout IS the torch
    layout ([out, in] for Linear weights). float32 throughout.

    DEFENSIVE drop: `embeddings.position_ids` is a persistent=False buffer, so it is
    normally ABSENT from state_dict() (verified for v3-large: the keyset is a clean
    bijection without it); this skip only fires for a checkpoint that re-persists it,
    and it is not a learned parameter (the v3 forward never adds it -- the core builds
    positions itself).

    KEYSET RECONCILIATION (ADR-0012 P7 cross-boundary truth + ADR-0002 fail-loud):
    the converted keyset MUST equal the device core's read-set jax_deberta.param_keys(cfg)
    EXACTLY. This is the strongest-feasible-level enforcement (set-equality is
    exhaustive by construction, unlike the structural assert list above) of the one
    fact viewed from both sides of the boundary -- 'the encoder's param set'. It
    catches the silent failure the assert list cannot: a converted-but-NEVER-read
    tensor (e.g. a fine-tuned checkpoint carrying a head/pooler/extra buffer, or a
    share_att_key=False pos_*_proj) that would otherwise load into the pytree and be
    quietly ignored by a forward that runs but is subtly wrong."""
    out: dict = {}
    for k, t in state_dict.items():
        if k.endswith("embeddings.position_ids"):
            continue
        out[k] = jnp.asarray(t.detach().to(torch.float32).numpy())
    expected = param_keys(cfg)
    converted = set(out)
    missing = expected - converted          # read-but-unconverted -> loud KeyError at forward
    extra = converted - expected            # converted-but-unread  -> SILENT wrong forward
    assert not (missing or extra), (
        "weight-conversion keyset != encoder read-set (jax_deberta.param_keys):\n"
        f"  read-but-unconverted ({len(missing)}): {sorted(missing)[:8]}\n"
        f"  converted-but-unread ({len(extra)}): {sorted(extra)[:8]}")
    return out


def load_jax_deberta(model_name: str = "microsoft/deberta-v3-large"):
    """Convenience: load the HF torch reference (CPU, eval) and return
    (params_pytree, DebertaCfg, hf_model). The hf_model is returned so a fidelity
    test can run the torch reference on the SAME inputs."""
    from transformers import DebertaV2Model
    hf = DebertaV2Model.from_pretrained(model_name).eval()
    cfg = cfg_from_hf(hf.config)
    params = params_from_state_dict(hf.state_dict(), cfg)
    return params, cfg, hf
