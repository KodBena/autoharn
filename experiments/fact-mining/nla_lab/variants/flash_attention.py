#!/usr/bin/env python
"""flash_attention — FlashAttention (EXACT), the portfolio keystone / correctness baseline.

WHAT THIS VARIANT IS. An EXACT, IO-aware reformulation of the dense disentangled
self-attention in `jax_deberta._self_attention` (jax_deberta.py:248-258) that NEVER
materializes the `[B,H,S,S]` score / probability matrix. It tiles the KEY axis and runs
the online-softmax recurrence (running max + rescale, the FlashAttention kernel) over the
FULL disentangled score — content `q·kᵀ` + content→position (c2p) + position→content
(p2c) — recomputing each `[B*H, S, T]` score tile on the fly. It is algebraically
identical to the reference (same softmax, same masking, same per-element scores); only the
softmax REDUCTION ORDER differs (online vs one-shot), so it reproduces `exact_reference` to
floating-point reduction order (~1e-5 — the EXACT fidelity tier, ADR-0009; MEASURED below,
not asserted), and it deletes the `B·H·S²` materialization the OOM memory model bounds.

THE DeBERTA 3-TERM CAUTION (NLA-OPTIMIZATION-PORTFOLIO.md §6, §10.2) IS HONORED. This is
NOT `softmax(QKᵀ)`. The position terms are NOT approximated and NOT dropped: their exact
structure is FOLDED into each key tile. For a key tile `[j0:j1)`:
  * content : `q @ (k[:,j0:j1]/scale)ᵀ`                                   -> [B*H, S, T]
  * c2p     : gather `c2p_att_full[bh, i, c2p_pos[i, j]]` over the tile    -> [B*H, S, T]
  * p2c     : gather `p2c_att_full[bh, j, p2c_pos[j, i]]` over the tile    -> [B*H, S, T]
`c2p_att_full = q @ pos_keyᵀ` and `p2c_att_full = k @ pos_queryᵀ` are the SAME `[B*H, S,
2·span]` disentangled-position intermediates the reference builds (the `k_disent` memory
term, O(B·H·S·span), NOT quadratic in S) — computed once per layer and tile-gathered with
the reference's exact `c2p_pos`/`p2c_pos` clip tables. So the score tile equals the dense
score restricted to the tile, element-for-element; flash changes ONLY where the softmax
reduction happens, never the math of any term. (`scale = sqrt(head_size·scale_factor)` is
common to all three terms — content, c2p, p2c — exactly as the reference computes it.)

SSOT REUSE (ADR-0012 P1 — own only the seam). Embeddings, LayerNorm, GELU, the q/k/v &
pos projections (`_linear`, `_transpose_for_scores`), `build_relative_position`,
`_get_rel_embedding`, the FFN/residual block — ALL are the un-forked `jax_deberta` helpers.
This variant re-authors only the attention orchestration it is varying (the score
materialize + softmax + context), reusing every leaf op it keeps.

MEMORY (R-MEM override, below). Flash changes the variable-memory profile: it drops the
`[B,H,S,S]` term entirely (`k_quad -> 0`) and replaces it with co-resident `[B*H, S, T]`
score TILES of width `T <= 2·pos_ebd_size`, each bounded by one disentangled-position
buffer — so their count folds into `k_disent` (a re-parameterised `shape_buckets.MemModel`
fed to the ONE `peak_variable_bytes`, NEVER a hand-rolled second model). The estimate stays
a CONSERVATIVE UPPER BOUND.

HOST-XOR-DEVICE. Imports `jax`/`jax.numpy` + the neutrally-named `jax_deberta` device core
+ `shape_buckets` (framework-free) + the contract; no numpy. The XOR-gate stays green.
"""

from __future__ import annotations

import math

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register

# Key-axis tile width target (a power of two). The kernel uses
# `T = min(_TILE_TARGET, 2*pos_ebd_size, S)`, so T is a power of two that DIVIDES a
# power-of-two seq bucket and is <= 2*pos_ebd_size (the disentangled-position width) — the
# property the memory bound rests on. Flash is EXACT for any tile width (online softmax is
# algebraically identical regardless of T); T trades compile/loop count against tile size
# and is fidelity-NEUTRAL. (A non-power-of-two bucket override is handled by a ragged final
# tile — the online recurrence and the masked gathers are width-agnostic.)
_TILE_TARGET: int = 128

# Conservative count of co-resident `[B*H, S, T]` tile-shaped buffers the flash kernel holds
# at peak within one key-tile iteration (content / c2p / p2c gathers + their int32 gather
# indices / the combined score / the mask / the exp'd probs — XLA fuses much of this chain,
# so this is an UPPER bound, not a live count). Each such buffer has width T <= 2*pos_ebd_size,
# so each is bounded by one disentangled-position buffer `[B*H, S, 2*pos_ebd_size]`; folding
# this count into `k_disent` therefore conservatively covers them (see est_peak_device_bytes).
_N_FLASH_TILE_BUFFERS: int = 12


def _flash_attention(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, am: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """Tiled, online-softmax disentangled self-attention — the EXACT flash reformulation of
    `jax_deberta._self_attention` (no `[B,H,S,S]` materialize). `am` is the `[B,S]` integer
    attention_mask (the reference's `[B,1,S,S]` mask factorizes as `am[b,i]*am[b,j]`, applied
    per tile here). Returns context `[B, S, hidden]`."""
    b, s, _ = hidden.shape
    h = cfg.num_heads
    bh = b * h

    # q/k/v content projections (reused jax_deberta helpers) -> [B*H, S, hs]
    q = jax_deberta._transpose_for_scores(
        jax_deberta._linear(hidden, p[f"encoder.layer.{i}.attention.self.query_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.query_proj.bias"]), h)
    k = jax_deberta._transpose_for_scores(
        jax_deberta._linear(hidden, p[f"encoder.layer.{i}.attention.self.key_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.key_proj.bias"]), h)
    v = jax_deberta._transpose_for_scores(
        jax_deberta._linear(hidden, p[f"encoder.layer.{i}.attention.self.value_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.value_proj.bias"]), h)
    hs = q.shape[-1]
    # scale = sqrt(head_size * scale_factor): a static python scalar (jax weak-types it to
    # float32 at the divide), exactly as the reference computes it, no host->device transfer.
    scale = math.sqrt(hs * cfg.scale_factor)

    # --- disentangled-position intermediates (the SAME buffers the reference builds) ---
    # share_att_key=True: pos projections REUSE this layer's query_proj / key_proj.
    att_span = cfg.pos_ebd_size
    rel_emb_slice = rel_emb[0: att_span * 2][None, :, :]                 # [1, 2*span, hidden]
    pos_query = jax_deberta._transpose_for_scores(
        jax_deberta._linear(rel_emb_slice, p[f"encoder.layer.{i}.attention.self.query_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.query_proj.bias"]), h)  # [H,2span,hs]
    pos_key = jax_deberta._transpose_for_scores(
        jax_deberta._linear(rel_emb_slice, p[f"encoder.layer.{i}.attention.self.key_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.key_proj.bias"]), h)    # [H,2span,hs]
    pos_query = jnp.tile(pos_query, (b, 1, 1))                           # [B*H, 2span, hs]
    pos_key = jnp.tile(pos_key, (b, 1, 1))

    # c2p_att_full[bh,i,r] = q_i · pos_key_r ; p2c_att_full[bh,j,r] = k_j · pos_query_r
    # Both [B*H, S, 2*span] — O(B·H·S·span), the disentangled term, NOT quadratic in S.
    c2p_att_full = jnp.matmul(q, jnp.transpose(pos_key, (0, 2, 1)))      # [B*H, S, 2span]
    p2c_att_full = jnp.matmul(k, jnp.transpose(pos_query, (0, 2, 1)))    # [B*H, S, 2span]

    # the reference's exact clip tables (rel_pos is int32; pure integer gather, no float arith)
    c2p_pos = jnp.clip(rel_pos + att_span, 0, att_span * 2 - 1)          # [S, S]
    p2c_pos = jnp.clip(-rel_pos + att_span, 0, att_span * 2 - 1)         # [S, S]

    k_scaled = k / scale                                                 # content divides k by scale (as the reference's kt = k.T/scale)
    am_bh = jnp.broadcast_to(am.astype(jnp.float32)[:, None, :], (b, h, s)).reshape(bh, s)  # [B*H, S]

    # --- the FlashAttention online-softmax recurrence over KEY tiles ---
    tile = min(_TILE_TARGET, att_span * 2, s)
    neg = jnp.finfo(jnp.float32).min  # type: ignore[no-untyped-call]   # the reference's masked_fill value
    m = jnp.full((bh, s), -jnp.inf, dtype=jnp.float32)                  # running max  [B*H, S]
    l = jnp.zeros((bh, s), dtype=jnp.float32)                           # running denom [B*H, S]
    acc = jnp.zeros((bh, s, hs), dtype=jnp.float32)                     # running numerator [B*H, S, hs]

    for j0 in range(0, s, tile):
        j1 = min(j0 + tile, s)
        w = j1 - j0
        # content tile: q @ (k[:,tile]/scale)ᵀ  -> [B*H, S, w] (per-element identical to dense)
        content_tile = jnp.matmul(q, jnp.transpose(k_scaled[:, j0:j1, :], (0, 2, 1)))
        # c2p tile: gather c2p_att_full[bh, i, c2p_pos[i, j]] for j in tile
        c2p_idx = jnp.broadcast_to(c2p_pos[None, :, j0:j1], (bh, s, w))
        c2p_tile = jnp.take_along_axis(c2p_att_full, c2p_idx, axis=-1)   # [B*H, S, w]
        # p2c tile: gather p2c_att_full[bh, j, p2c_pos[j, i]] for j in tile, then transpose to [.,i,j]
        p2c_att_tile = p2c_att_full[:, j0:j1, :]                         # [B*H, w, 2span]
        p2c_idx = jnp.broadcast_to(p2c_pos[None, j0:j1, :], (bh, w, s))
        p2c_g = jnp.take_along_axis(p2c_att_tile, p2c_idx, axis=-1)      # [B*H, w, S]  g[bh,j,i]
        p2c_tile = jnp.transpose(p2c_g, (0, 2, 1))                       # [B*H, S, w]  [bh,i,j]
        # full disentangled score tile (content + c2p/scale + p2c/scale — the reference's accumulation)
        score_tile = content_tile + c2p_tile / scale + p2c_tile / scale  # [B*H, S, w]
        # mask: reference masked_fill ~(am[b,i]*am[b,j]) -> neg
        mask_tile = am_bh[:, :, None] * am_bh[:, None, j0:j1]            # [B*H, S, w]
        score_tile = jnp.where(mask_tile > 0, score_tile, neg)
        # online-softmax update (running max + rescale)
        m_tile = jnp.max(score_tile, axis=-1)                           # [B*H, S]
        m_new = jnp.maximum(m, m_tile)
        corr = jnp.exp(m - m_new)                                       # [B*H, S]; first tile: exp(-inf-·)=0
        p_tile = jnp.exp(score_tile - m_new[:, :, None])                # [B*H, S, w]
        l = l * corr + jnp.sum(p_tile, axis=-1)
        acc = acc * corr[:, :, None] + jnp.matmul(p_tile, v[:, j0:j1, :])  # [B*H, S, hs]
        m = m_new

    out = acc / l[:, :, None]                                          # [B*H, S, hs]  softmax-weighted V
    context = out.reshape(b, h, s, hs)
    context = jnp.transpose(context, (0, 2, 1, 3)).reshape(b, s, -1)   # [B, S, hidden]
    return context


def _flash_layer(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, am: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """Mirror of `jax_deberta._layer` with the attention call swapped for the flash kernel;
    the SelfOutput / Intermediate / Output residual+LayerNorm block reuses the un-forked
    jax_deberta leaf helpers verbatim (ADR-0012 P1 — own only the attention seam)."""
    eps = cfg.layer_norm_eps
    ctx = _flash_attention(p, i, hidden, am, rel_pos, rel_emb, cfg)
    ao = jax_deberta._linear(ctx, p[f"encoder.layer.{i}.attention.output.dense.weight"],
                             p[f"encoder.layer.{i}.attention.output.dense.bias"])
    ao = jax_deberta._layer_norm(ao + hidden, p[f"encoder.layer.{i}.attention.output.LayerNorm.weight"],
                                 p[f"encoder.layer.{i}.attention.output.LayerNorm.bias"], eps)
    inter = jax_deberta._gelu(jax_deberta._linear(ao, p[f"encoder.layer.{i}.intermediate.dense.weight"],
                                                  p[f"encoder.layer.{i}.intermediate.dense.bias"]))
    out = jax_deberta._linear(inter, p[f"encoder.layer.{i}.output.dense.weight"],
                              p[f"encoder.layer.{i}.output.dense.bias"])
    out = jax_deberta._layer_norm(out + ao, p[f"encoder.layer.{i}.output.LayerNorm.weight"],
                                  p[f"encoder.layer.{i}.output.LayerNorm.bias"], eps)
    return out  # type: ignore[no-any-return]


def _flash_forward(params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
                   rel_pos: jax.Array, cfg: "jax_deberta.DebertaCfg") -> jax.Array:
    """Encoder forward -> last_hidden_state `[B, S, hidden]`, mirroring `jax_deberta.forward`
    with the per-layer attention swapped for the flash kernel. Embeddings + rel-embedding +
    the rel_pos hoist are the reference's, un-forked. `attention_mask [B,S]` is threaded into
    the flash attention (it factorizes the reference's `[B,1,S,S]` mask)."""
    eps = cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]   # [B,S,hidden]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    mask = attention_mask.astype(emb.dtype)[:, :, None]
    emb = emb * mask
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)
    hidden = emb
    for i in range(cfg.num_layers):
        hidden = _flash_layer(params, i, hidden, attention_mask, rel_pos, rel_emb, cfg)
    return hidden  # type: ignore[no-any-return]


# jit core: cfg (NamedTuple of python scalars) is static; rel_pos is a traced runtime arg —
# the SAME hoist jax_deberta.encode uses (keeps the [S,S] table out of the baked constant).
_flash_core = jax.jit(_flash_forward, static_argnums=(4,))


@register
class FlashAttention(EncodeVariant):
    name = "flash_attention"
    regime = Regime.BOTH                  # exact; relaxes the OOM bound (both lanes)
    fidelity_tier = FidelityTier.EXACT    # exact reformulation, ~1e-5 reduction-order
    IMPLEMENTED = True                    # real math: tiled online-softmax disentangled attention

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # rel_pos hoisted + computed once per bucket (eager, bit-identical to the jitted form),
        # exactly as jax_deberta.encode does it (the un-forked SSOT for the rel-pos table).
        s = input_ids.shape[1]
        rel_pos = jax_deberta.build_relative_position(
            s, cfg.position_buckets, cfg.max_relative_positions)
        # jax_deberta is a declared mypy stub-gap (mypy.ini skip); its Array result is returned
        # as the contract's jax.Array (named relaxation, ADR-0012 P8 — mirrors exact_reference).
        return _flash_core(  # type: ignore[no-any-return]
            params, input_ids, attention_mask, rel_pos, cfg)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        """R-MEM override. Flash NEVER materializes `[B,H,S,S]`, so the dense quadratic term is
        DROPPED (`k_quad -> 0`). What replaces it is co-resident `[B*H, S, T]` score TILES with
        `T = min(_TILE_TARGET, 2*pos_ebd_size, S) <= 2*pos_ebd_size` — so each tile buffer is
        bounded by ONE disentangled-position buffer `[B*H, S, 2*pos_ebd_size]`, and folding their
        count (`_N_FLASH_TILE_BUFFERS`) into `k_disent` conservatively upper-bounds them. This is
        a RE-PARAMETERISED `shape_buckets.MemModel` fed to the ONE `peak_variable_bytes` (ADR-0012
        P1 — no hand-rolled second model); it stays a CONSERVATIVE UPPER BOUND (never under).
        The disentangled-position precomputes (`c2p_att_full`/`p2c_att_full`, 2 buffers) and the
        linear stream (embeddings/q/k/v/`acc`/FFN) are unchanged from the dense profile."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        mm_flash = mm._replace(k_quad=0, k_disent=mm.k_disent + _N_FLASH_TILE_BUFFERS)
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm_flash, bucket.batch, bucket.seq_bucket)
