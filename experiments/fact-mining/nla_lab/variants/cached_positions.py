#!/usr/bin/env python
"""cached_positions — cached disentangled-position structure (EXACT; speed for a small memory cost).

TECHNIQUE (NLA-OPTIMIZATION-PORTFOLIO.md §6a / §1; seam jax_deberta.py:174-225). The
disentangled c2p/p2c bias is computed every layer (24x) and every forward from THREE
pieces, only ONE of which is content-dependent:

  1. the log-bucketed relative-position GATHER tables `c2p_pos = clip(rel_pos+span,…)`
     and `p2c_pos = clip(-rel_pos+span,…)` — pure functions of `(s_bucket, att_span)`,
     INDEPENDENT of params AND content. jax_deberta recomputes them inside every layer;
  2. the position-projected K/Q `pos_key_layer = key_proj(rel_emb)` /
     `pos_query_layer = query_proj(rel_emb)` — functions of the layer weights + the
     (S-independent) relative-position embeddings, INDEPENDENT of content/input;
  3. the content matmuls `query·pos_keyᵀ` (c2p) and `key·pos_queryᵀ` (p2c) — the ONLY
     part that depends on the actual tokens of THIS forward.

So this variant MEMOIZES (1) per `s_bucket` and (2) per `params` identity on `self`, and
the jitted core recomputes ONLY (3) plus the content QKᵀ stream. EXACT: it is a pure
re-association of jax_deberta's own arithmetic — the gather tables are integer indices
(no float op on them) and the position projections are the identical `_linear /
_transpose_for_scores` leaf ops, just hoisted out of the per-forward path. Measured P6
lhs Δ vs exact_reference is reduction-order only (eager-vs-jitted matmul accumulation),
the EXACT tier (~1e-5); the real number is reported by the bench, not asserted here.

SSOT REUSE (ADR-0012 P1 — own only the seam). Every LEAF op is jax_deberta's: `_linear`,
`_layer_norm`, `_gelu`, `_transpose_for_scores`, `_get_rel_embedding`,
`_get_attention_mask`, `build_relative_position`. This file re-threads ONLY the
attention call-chain so the cached position structure flows in where
`_disentangled_bias` (174-225) used to recompute it — jax_deberta exposes no hook at
that seam, so the loop is re-wired while the math underneath stays the un-forked SSOT.
`_disentangled_bias_cached` is jax_deberta._disentangled_bias's body (199-225) verbatim
with pieces (1)+(2) received instead of recomputed.

MEMORY (R-MEM override). HONEST direction: this technique RAISES the peak by a small
RESIDENT cache (the per-layer position-projected K/Q + the [S,S] gather tables held
across forwards) — it trades a one-time buffer for dropped per-forward recompute, so
`est_peak_device_bytes` is the dense bound PLUS that retained cache (a conservative
upper bound, never under), mirroring shape_buckets.retained_lhs_bytes' additive-retained
pattern. The portfolio's "memory win" was about the [S,S] table baked into every
compiled EXECUTABLE (a compile-memory axis already won by jax_deberta's rel_pos hoist),
NOT the per-forward activation peak this dimension measures.

PREP MEMOIZATION (R1-C). Pieces (1)+(2) are computed ONCE and cached on `self` (the
bench's warmup forwards amortize the first build out of the timed window); the cache is
invalidated if `cfg` changes or the `params` object identity changes (correctness over a
new checkpoint), and the cached `params` is referenced so its `id()` cannot be reused.

HOST-XOR-DEVICE. Imports jax + jax_deberta (device) + shape_buckets (framework-free SSOT,
the same one the contract's default override uses) + the contract/registry. No numpy.
"""

from __future__ import annotations

import math

import jax
import jax.numpy as jnp

import jax_deberta as J
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register

# the memoized per-layer position-projected (Q, K) pairs (content-independent), pre-tile
# [H, 2*span, hs] each — one pair per encoder layer.
PosProjs = tuple[tuple[jax.Array, jax.Array], ...]


# --------------------------------------------------------- the cached-seam math
def _disentangled_bias_cached(
    query_layer: jax.Array, key_layer: jax.Array,
    pos_query_layer: jax.Array, pos_key_layer: jax.Array,
    c2p_pos: jax.Array, p2c_pos: jax.Array, cfg: "J.DebertaCfg",
) -> jax.Array:
    """jax_deberta._disentangled_bias (199-225) VERBATIM, but the position-projected K/Q
    (`pos_*_layer`, content-independent, pre-tile [H, 2*span, hs]) and the gather index
    tables (`c2p_pos`/`p2c_pos`, position-only [S, S]) arrive PRECOMPUTED instead of being
    rebuilt here. Only the content matmuls (`query·pos_keyᵀ`, `key·pos_queryᵀ`) and the
    integer gathers run per call — the exact same ops jax_deberta runs, re-associated."""
    bh = query_layer.shape[0]                       # B*H
    b = bh // cfg.num_heads
    att_span = cfg.pos_ebd_size
    # repeat(B,1,1): the cached projections are stored B-independent ([H,2span,hs]).
    pos_query_layer = jnp.tile(pos_query_layer, (b, 1, 1))
    pos_key_layer = jnp.tile(pos_key_layer, (b, 1, 1))

    score = jnp.zeros((bh, query_layer.shape[1], key_layer.shape[1]), dtype=query_layer.dtype)

    if cfg.has_c2p:
        scale = math.sqrt(pos_key_layer.shape[-1] * cfg.scale_factor)
        c2p_att = jnp.matmul(query_layer, jnp.transpose(pos_key_layer, (0, 2, 1)))   # [B*H,S,2span]
        idx = jnp.broadcast_to(c2p_pos[None, :, :], (bh, c2p_pos.shape[0], c2p_pos.shape[1]))
        c2p_att = jnp.take_along_axis(c2p_att, idx, axis=-1)                          # [B*H,S,S]
        score = score + c2p_att / scale

    if cfg.has_p2c:
        scale = math.sqrt(pos_query_layer.shape[-1] * cfg.scale_factor)
        idx = jnp.broadcast_to(p2c_pos[None, :, :], (bh, p2c_pos.shape[0], p2c_pos.shape[1]))
        p2c_att = jnp.matmul(key_layer, jnp.transpose(pos_query_layer, (0, 2, 1)))    # [B*H,S,2span]
        p2c_att = jnp.take_along_axis(p2c_att, idx, axis=-1)                          # [B*H,S,S]
        p2c_att = jnp.transpose(p2c_att, (0, 2, 1))                                   # .transpose(-1,-2)
        score = score + p2c_att / scale

    return score


def _self_attention_cached(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, att_mask: jax.Array,
    pos_query_layer: jax.Array, pos_key_layer: jax.Array,
    c2p_pos: jax.Array, p2c_pos: jax.Array, cfg: "J.DebertaCfg",
) -> jax.Array:
    """jax_deberta._self_attention (228-261) with the ONLY change being that the
    disentangled bias is the cached-seam variant; every leaf (`_linear`,
    `_transpose_for_scores`, the QKᵀ content stream, mask, softmax, context) is identical."""
    b, s, _ = hidden.shape
    q = J._transpose_for_scores(J._linear(
        hidden, p[f"encoder.layer.{i}.attention.self.query_proj.weight"],
        p[f"encoder.layer.{i}.attention.self.query_proj.bias"]), cfg.num_heads)
    k = J._transpose_for_scores(J._linear(
        hidden, p[f"encoder.layer.{i}.attention.self.key_proj.weight"],
        p[f"encoder.layer.{i}.attention.self.key_proj.bias"]), cfg.num_heads)
    v = J._transpose_for_scores(J._linear(
        hidden, p[f"encoder.layer.{i}.attention.self.value_proj.weight"],
        p[f"encoder.layer.{i}.attention.self.value_proj.bias"]), cfg.num_heads)

    scale = math.sqrt(q.shape[-1] * cfg.scale_factor)
    kt = jnp.transpose(k, (0, 2, 1)) / scale
    attention_scores = jnp.matmul(q, kt)                                            # [B*H,S,S]

    rel_att = _disentangled_bias_cached(q, k, pos_query_layer, pos_key_layer,
                                        c2p_pos, p2c_pos, cfg)
    attention_scores = attention_scores + rel_att

    attention_scores = attention_scores.reshape(b, cfg.num_heads, s, s)
    neg = jnp.finfo(jnp.float32).min  # type: ignore[no-untyped-call]
    attention_scores = jnp.where(att_mask.astype(bool), attention_scores, neg)
    attention_probs = jax.nn.softmax(attention_scores, axis=-1)

    context = jnp.matmul(attention_probs.reshape(b * cfg.num_heads, s, s), v)
    context = context.reshape(b, cfg.num_heads, s, context.shape[-1])
    context = jnp.transpose(context, (0, 2, 1, 3)).reshape(b, s, -1)
    return context


def _layer_cached(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, att_mask: jax.Array,
    pos_query_layer: jax.Array, pos_key_layer: jax.Array,
    c2p_pos: jax.Array, p2c_pos: jax.Array, cfg: "J.DebertaCfg",
) -> jax.Array:
    """jax_deberta._layer (264-285) VERBATIM (SelfOutput -> intermediate -> Output, each a
    post-LayerNorm residual) except the attention call is the cached-seam one. FFN +
    LayerNorm + GELU are the un-forked jax_deberta leaves."""
    eps = cfg.layer_norm_eps
    ctx = _self_attention_cached(p, i, hidden, att_mask, pos_query_layer, pos_key_layer,
                                 c2p_pos, p2c_pos, cfg)
    ao = J._linear(ctx, p[f"encoder.layer.{i}.attention.output.dense.weight"],
                   p[f"encoder.layer.{i}.attention.output.dense.bias"])
    ao = J._layer_norm(ao + hidden, p[f"encoder.layer.{i}.attention.output.LayerNorm.weight"],
                       p[f"encoder.layer.{i}.attention.output.LayerNorm.bias"], eps)
    inter = J._gelu(J._linear(ao, p[f"encoder.layer.{i}.intermediate.dense.weight"],
                              p[f"encoder.layer.{i}.intermediate.dense.bias"]))
    out = J._linear(inter, p[f"encoder.layer.{i}.output.dense.weight"],
                    p[f"encoder.layer.{i}.output.dense.bias"])
    out = J._layer_norm(out + ao, p[f"encoder.layer.{i}.output.LayerNorm.weight"],
                        p[f"encoder.layer.{i}.output.LayerNorm.bias"], eps)
    return out  # type: ignore[no-any-return]  # J._layer_norm is the skipped-stub SSOT leaf


def _forward_cached_impl(
    params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
    pos_projs: PosProjs, c2p_pos: jax.Array, p2c_pos: jax.Array, cfg: "J.DebertaCfg",
) -> jax.Array:
    """jax_deberta.forward (303-342) with the cached position structure threaded in.
    `pos_projs` (one (pos_q, pos_k) pair per layer) and the gather tables are RUNTIME
    args — the same hoist jax_deberta uses for `rel_pos` (keeps the [S,S]/projection
    buffers out of the baked per-executable constant; compile keys on S via the gather
    table shape, bounded by the bucket ladder). Embeddings + masks are the SSOT leaves."""
    eps = cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]
    emb = J._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                        params["embeddings.LayerNorm.bias"], eps)
    mask = attention_mask.astype(emb.dtype)[:, :, None]
    emb = emb * mask

    att_mask = J._get_attention_mask(attention_mask)
    hidden = emb
    for i in range(cfg.num_layers):                 # cfg static -> the loop unrolls
        pos_q_i, pos_k_i = pos_projs[i]
        hidden = _layer_cached(params, i, hidden, att_mask, pos_q_i, pos_k_i,
                               c2p_pos, p2c_pos, cfg)
    return hidden  # type: ignore[no-any-return]  # embeddings chain through skipped J leaves


# cfg (NamedTuple of python scalars) is static (argnum 6); pos_projs + the gather tables
# are TRACED runtime args (the position-structure hoist, mirroring jax_deberta's rel_pos).
_forward_cached = jax.jit(_forward_cached_impl, static_argnums=(6,))


@register
class CachedPositions(EncodeVariant):
    name = "cached_positions"
    regime = Regime.LATENCY               # cuts recompute on the launch-bound small-batch lane
    fidelity_tier = FidelityTier.EXACT    # pure re-association of jax_deberta's own arithmetic
    IMPLEMENTED = True

    def __init__(self) -> None:
        # per-variant memoized prep (R1-C), amortized by the bench's warmup forwards.
        self._cfg: "J.DebertaCfg | None" = None
        self._proj_params_id: int | None = None
        self._proj_params_ref: object = None        # keep params alive -> id() cannot be reused
        self._pos_projs: PosProjs | None = None
        self._idx_cache: dict[int, tuple[jax.Array, jax.Array]] = {}

    def _invalidate_if_cfg_changed(self, cfg: "J.DebertaCfg") -> None:
        if self._cfg is not None and self._cfg != cfg:
            self._proj_params_id = None
            self._proj_params_ref = None
            self._pos_projs = None
            self._idx_cache = {}
        self._cfg = cfg

    def _prepare(self, params: dict[str, jax.Array], cfg: "J.DebertaCfg") -> PosProjs:
        """Memoize the CONTENT-INDEPENDENT per-layer position-projected K/Q (piece 2):
        `query_proj(rel_emb)` / `key_proj(rel_emb)`, pre-tile [H, 2*span, hs]. Keyed by
        params identity (a new checkpoint rebuilds). Identical leaf ops to
        jax_deberta._disentangled_bias's 189-195."""
        if self._proj_params_id != id(params) or self._pos_projs is None:
            att_span = cfg.pos_ebd_size
            rel_emb = J._get_rel_embedding(params, cfg)            # [2*pos_ebd, hidden], LN'd
            rel_emb = rel_emb[0:att_span * 2][None, :, :]          # [1, 2*span, hidden]
            projs = []
            for i in range(cfg.num_layers):
                qp_w = params[f"encoder.layer.{i}.attention.self.query_proj.weight"]
                qp_b = params[f"encoder.layer.{i}.attention.self.query_proj.bias"]
                kp_w = params[f"encoder.layer.{i}.attention.self.key_proj.weight"]
                kp_b = params[f"encoder.layer.{i}.attention.self.key_proj.bias"]
                pos_q = J._transpose_for_scores(J._linear(rel_emb, qp_w, qp_b), cfg.num_heads)
                pos_k = J._transpose_for_scores(J._linear(rel_emb, kp_w, kp_b), cfg.num_heads)
                projs.append((pos_q, pos_k))
            self._pos_projs = tuple(projs)
            self._proj_params_id = id(params)
            self._proj_params_ref = params
        assert self._pos_projs is not None
        return self._pos_projs

    def _index(self, s: int, cfg: "J.DebertaCfg") -> tuple[jax.Array, jax.Array]:
        """Memoize the POSITION-ONLY gather tables (piece 1) per s_bucket — pure integer
        functions of (S, att_span), identical to jax_deberta._disentangled_bias's 209/218.
        Reading `s = input_ids.shape[1]` as the cache key is the contract-sanctioned use
        of the bucket as a key (it does NOT re-bucket)."""
        cached = self._idx_cache.get(s)
        if cached is None:
            att_span = cfg.pos_ebd_size
            rel_pos = J.build_relative_position(s, cfg.position_buckets, cfg.max_relative_positions)
            c2p_pos = jnp.clip(rel_pos + att_span, 0, att_span * 2 - 1)
            p2c_pos = jnp.clip(-rel_pos + att_span, 0, att_span * 2 - 1)
            cached = (c2p_pos, p2c_pos)
            self._idx_cache[s] = cached
        return cached

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: "J.DebertaCfg",
    ) -> jax.Array:
        self._invalidate_if_cfg_changed(cfg)
        pos_projs = self._prepare(params, cfg)
        c2p_pos, p2c_pos = self._index(int(input_ids.shape[1]), cfg)
        # jax_deberta is a declared mypy stub-gap (mypy.ini skip); its Array result is
        # returned as the contract's jax.Array (named relaxation, ADR-0012 P8).
        return _forward_cached(  # type: ignore[no-any-return]
            params, input_ids, attention_mask, pos_projs, c2p_pos, p2c_pos, cfg)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: "J.DebertaCfg"
    ) -> int:
        """Dense per-forward peak (the ONE shape_buckets model) PLUS the RESIDENT position
        cache this technique retains across forwards — a conservative UPPER bound (never
        under), additive like shape_buckets.retained_lhs_bytes. Reflects the HONEST
        direction: cached_positions costs a small extra resident buffer to drop the
        per-forward position recompute; it is NOT a per-forward-peak memory saver."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        B, S = bucket.batch, bucket.seq_bucket
        dense = shape_buckets.peak_variable_bytes(mm, B, S)
        span2 = 2 * mm.pos_ebd_size
        # retained per-layer position-projected K and Q (pre-tile [H,2span,hs] = hidden*span2
        # elements each), q+k, all layers; B-independent (tiling to B*H is transient, already
        # in the dense disent term).
        pos_proj = cfg.num_layers * 2 * mm.hidden * span2 * mm.bytes_per_elem
        # retained [S,S] int32 gather tables (c2p_pos + p2c_pos) for this s_bucket.
        idx = 2 * S * S * mm.bytes_per_elem
        # shape_buckets is a declared mypy stub-gap; its int is returned as the contract int.
        return int(dense + pos_proj + idx)
