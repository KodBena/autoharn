#!/usr/bin/env python
"""Pure-JAX DeBERTa-v2/v3 ENCODER forward (ADR-0012 P9 functional core).

HONEST FILENAME (test_import_xor.py contract): this name advertises the `jax`
device framework, so it promises to be DEVICE-ONLY. It imports `jax` + stdlib and
NEVER `numpy`. The XOR-gate rejects a `jax_*`-named file importing numpy
*regardless* of BOUNDARY_FILES — the promise is mechanically enforced. The
torch->jax weight conversion (the host/device BOUNDARY, which does import numpy)
lives in the neutrally-named `deberta_weights.py`, not here.

SCOPE — the ENCODER front half maverick-coref uses: input_ids + attention_mask ->
last_hidden_state. deberta-v3-large uses the deberta-v2 ARCHITECTURE in HF. We
mirror, line-for-line, the torch reference
  transformers/models/deberta_v2/modeling_deberta_v2.py
(transformers 4.53.2). The hard part — the DISENTANGLED ATTENTION (content->content
+ content->position + position->content), the relative-position bucketing
(make_log_bucket_position), the shared relative-position embeddings, the
(no-absolute-position) embeddings + LayerNorm — is reproduced exactly; every
divergence-prone term cites its reference line.

CONFIG is NOT hand-mirrored here (ADR-0012 P1/P7 derive-don't-re-author): the
`DebertaCfg` NamedTuple is BUILT FROM the HF `DebertaV2Config` in the boundary
(`deberta_weights.py`), so the single source of truth of every hyperparameter is
the HF config, read at conversion time, never a constant retyped here. The
LayerNorm form below (torch default, population/biased variance) is a property of
the reference *code*. The GELU is NOT: HF picks it from the config
(`ACT2FN[config.hidden_act]`, modeling_deberta_v2.py:394-397) -- 'gelu' -> exact
erf, 'gelu_new'/'gelu_pytorch_tanh' -> tanh approx. This core hardcodes the
exact-erf form (`_gelu`, approximate=False), so the boundary
`deberta_weights.cfg_from_hf` FAIL-LOUD asserts `config.hidden_act == 'gelu'`
rather than silently running a tanh-approx checkpoint through exact-erf GELU.

PARAM NAMING is the torch state_dict's, verbatim (derive-don't-re-author across the
torch->jax boundary): `deberta_weights.py` converts each `state_dict()` tensor to a
jax array under its ORIGINAL torch key, so there is no hand-authored rename layer
that could drift. torch `nn.Linear` stores weight as [out, in] and computes
`x @ W.T + b`; we keep that layout and transpose at use (`x @ w.T + b`).
"""

from __future__ import annotations

import math
from typing import NamedTuple

import jax
import jax.numpy as jnp


class DebertaCfg(NamedTuple):
    """Static (hashable -> jit-static) architecture config, built from the HF
    DebertaV2Config in the conversion boundary. NOT a hand-mirrored constant set:
    every field is read off the HF config (deberta_weights.cfg_from_hf)."""
    num_layers: int
    num_heads: int
    head_size: int          # hidden_size // num_heads (== attention_head_size)
    position_buckets: int   # config.position_buckets (the log-bucket size)
    max_relative_positions: int  # resolved: <1 -> max_position_embeddings
    pos_ebd_size: int       # att_span: position_buckets if >0 else max_relative_positions
    scale_factor: int       # 1 + ('c2p' in pos_att_type) + ('p2c' in pos_att_type)
    has_c2p: bool
    has_p2c: bool
    layer_norm_eps: float


# A per-layer block reads exactly these eight {.weight,.bias} sub-modules.
_LAYER_SUBMODULES = (
    "attention.self.query_proj",
    "attention.self.key_proj",
    "attention.self.value_proj",
    "attention.output.dense",
    "attention.output.LayerNorm",
    "intermediate.dense",
    "output.dense",
    "output.LayerNorm",
)
# Non-layer params the forward reads (embeddings + encoder-level rel-emb/LayerNorm).
_GLOBAL_KEYS = (
    "embeddings.word_embeddings.weight",
    "embeddings.LayerNorm.weight",
    "embeddings.LayerNorm.bias",
    "encoder.rel_embeddings.weight",
    "encoder.LayerNorm.weight",
    "encoder.LayerNorm.bias",
)


def param_keys(cfg: DebertaCfg) -> set[str]:
    """The EXACT torch-key set this forward READS — the device core's read-set, and
    the SSOT the conversion boundary reconciles its converted keyset against
    (deberta_weights.params_from_state_dict asserts set-equality). Deriving it HERE,
    next to the forward that consumes it, gives 'which weights the encoder reads' a
    single home (ADR-0012 P1/P7): a converted-but-unread tensor (silent: a forward
    that runs but is subtly wrong -- e.g. a fine-tuned checkpoint carrying a head,
    pooler, or a share_att_key=False pos_*_proj) and a read-but-unconverted key (loud
    KeyError) are both caught by set-equality at conversion time, exhaustively, not
    by a non-exhaustive assert list. `share_att_key=True` is assumed: pos projections
    REUSE query_proj/key_proj, so no separate pos_*_proj keys appear here."""
    keys = set(_GLOBAL_KEYS)
    for i in range(cfg.num_layers):
        for sub in _LAYER_SUBMODULES:
            keys.add(f"encoder.layer.{i}.{sub}.weight")
            keys.add(f"encoder.layer.{i}.{sub}.bias")
    return keys


# ----------------------------------------------------------- elementwise pieces
def _layer_norm(x: jax.Array, weight: jax.Array, bias: jax.Array, eps: float) -> jax.Array:
    """torch.nn.LayerNorm over the last axis (population/biased variance)."""
    mu = jnp.mean(x, axis=-1, keepdims=True)
    var = jnp.mean(jnp.square(x - mu), axis=-1, keepdims=True)   # unbiased=False
    xhat = (x - mu) * jax.lax.rsqrt(var + eps)
    return xhat * weight + bias


def _linear(x: jax.Array, w: jax.Array, b: jax.Array) -> jax.Array:
    """torch.nn.Linear: weight stored [out, in], computes x @ W.T + b."""
    return x @ w.T + b


def _gelu(x: jax.Array) -> jax.Array:
    """ACT2FN['gelu'] == nn.functional.gelu (EXACT erf form). The jax default is
    the tanh approximation, which would NOT match — so approximate=False."""
    return jax.nn.gelu(x, approximate=False)


# ------------------------------------------------- relative position machinery
def make_log_bucket_position(relative_pos: jax.Array, bucket_size: int, max_position: int) -> jax.Array:
    """Mirror of modeling_deberta_v2.make_log_bucket_position (lines 58-71).

    sign = sign(rel); mid = bucket_size//2
    abs_pos = where(-mid < rel < mid, mid-1, |rel|)
    log_pos = ceil( log(abs_pos/mid) / log((max_position-1)/mid) * (mid-1) ) + mid
    bucket  = where(abs_pos <= mid, rel, log_pos*sign)
    torch computes the log path in float32 then truncates to long; we match
    (x64 disabled -> jnp float32). For |rel| < mid the log path is never taken
    (bucket == rel), so short sequences are exact by construction; the float path
    only engages for |rel| >= mid (long sequences), where the test verifies the
    integer bucket array equals torch's bit-for-bit."""
    sign = jnp.sign(relative_pos)
    mid = bucket_size // 2
    abs_pos = jnp.where(
        (relative_pos < mid) & (relative_pos > -mid),
        mid - 1,
        jnp.abs(relative_pos),
    )
    log_pos = (
        jnp.ceil(jnp.log(abs_pos / mid) / jnp.log((max_position - 1) / mid) * (mid - 1)) + mid
    )
    bucket_pos = jnp.where(abs_pos <= mid, relative_pos.astype(log_pos.dtype), log_pos * sign)
    return bucket_pos


def build_relative_position(seq_len: int, bucket_size: int, max_position: int) -> jax.Array:
    """Mirror of build_relative_position for the square (query_size==key_size)
    encoder self-attention case: rel[i,j] = i - j, then log-bucketed. Returns
    int32[seq_len, seq_len] (the [1, S, S] of the reference, batch dim dropped)."""
    ids = jnp.arange(seq_len)
    rel = ids[:, None] - ids[None, :]
    if bucket_size > 0 and max_position > 0:
        rel = make_log_bucket_position(rel, bucket_size, max_position)
    return rel.astype(jnp.int32)


# ---------------------------------------------------- per-layer attention core
def _transpose_for_scores(x: jax.Array, num_heads: int) -> jax.Array:
    """modeling_deberta_v2.DisentangledSelfAttention.transpose_for_scores.
    [B, S, all_head] -> [B, S, H, hs] -> [B, H, S, hs] -> [B*H, S, hs]."""
    b, s = x.shape[0], x.shape[1]
    x = x.reshape(b, s, num_heads, -1)
    x = jnp.transpose(x, (0, 2, 1, 3))
    return x.reshape(b * num_heads, s, x.shape[-1])


def _disentangled_bias(
    p: dict, i: int,
    query_layer: jax.Array, key_layer: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: DebertaCfg,
) -> jax.Array:
    """Mirror of DisentangledSelfAttention.disentangled_attention_bias (282-351),
    share_att_key=True branch, pos_att_type=['p2c','c2p'].

    rel_pos : int32[S, S]   (the reference's [1,1,S,S], leading dims dropped)
    rel_emb : float[2*att_span, hidden]  (post norm_rel_ebd LayerNorm, get_rel_embedding)
    """
    bh = query_layer.shape[0]           # B*H
    b = bh // cfg.num_heads
    att_span = cfg.pos_ebd_size
    # rel_embeddings[0 : att_span*2] (already exactly that many rows for v3-large)
    rel_emb = rel_emb[0: att_span * 2][None, :, :]           # [1, 2*span, hidden]

    # share_att_key: pos projections reuse THIS layer's query_proj / key_proj.
    qp_w, qp_b = p[f"encoder.layer.{i}.attention.self.query_proj.weight"], p[f"encoder.layer.{i}.attention.self.query_proj.bias"]
    kp_w, kp_b = p[f"encoder.layer.{i}.attention.self.key_proj.weight"], p[f"encoder.layer.{i}.attention.self.key_proj.bias"]
    pos_query_layer = _transpose_for_scores(_linear(rel_emb, qp_w, qp_b), cfg.num_heads)   # [H, 2span, hs]
    pos_key_layer = _transpose_for_scores(_linear(rel_emb, kp_w, kp_b), cfg.num_heads)     # [H, 2span, hs]
    pos_query_layer = jnp.tile(pos_query_layer, (b, 1, 1))   # repeat(B,1,1) -> [B*H, 2span, hs]
    pos_key_layer = jnp.tile(pos_key_layer, (b, 1, 1))

    score = jnp.zeros((bh, query_layer.shape[1], key_layer.shape[1]), dtype=query_layer.dtype)

    # content -> position (c2p)
    if cfg.has_c2p:
        # scale = sqrt(d*scale_factor): a STATIC python scalar (shapes/scale_factor
        # are python ints). Kept a python float -> jax weak-types it to the array's
        # float32 at the divide, matching torch's float32 sqrt, with NO host->device
        # `jnp.array` transfer (device-transfers gate stays green for this device file).
        scale = math.sqrt(pos_key_layer.shape[-1] * cfg.scale_factor)
        c2p_att = jnp.matmul(query_layer, jnp.transpose(pos_key_layer, (0, 2, 1)))   # [B*H, S, 2span]
        c2p_pos = jnp.clip(rel_pos + att_span, 0, att_span * 2 - 1)                  # [S, S]
        idx = jnp.broadcast_to(c2p_pos[None, :, :], (bh, c2p_pos.shape[0], c2p_pos.shape[1]))
        c2p_att = jnp.take_along_axis(c2p_att, idx, axis=-1)                         # [B*H, S, S]
        score = score + c2p_att / scale

    # position -> content (p2c)
    if cfg.has_p2c:
        scale = math.sqrt(pos_query_layer.shape[-1] * cfg.scale_factor)
        # build_rpos: key_size == query_size (square self-attn) -> r_pos == rel_pos
        p2c_pos = jnp.clip(-rel_pos + att_span, 0, att_span * 2 - 1)                 # [S, S]
        p2c_att = jnp.matmul(key_layer, jnp.transpose(pos_query_layer, (0, 2, 1)))   # [B*H, S, 2span]
        idx = jnp.broadcast_to(p2c_pos[None, :, :], (bh, p2c_pos.shape[0], p2c_pos.shape[1]))
        p2c_att = jnp.take_along_axis(p2c_att, idx, axis=-1)                         # [B*H, S, S]
        p2c_att = jnp.transpose(p2c_att, (0, 2, 1))                                  # .transpose(-1,-2)
        score = score + p2c_att / scale

    return score


def _self_attention(
    p: dict, i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: DebertaCfg,
) -> jax.Array:
    """Mirror of DisentangledSelfAttention.forward (196-280). att_mask is the
    [B,1,S,S] boolean mask from get_attention_mask. Returns context [B,S,hidden]."""
    b, s, _ = hidden.shape
    q = _transpose_for_scores(_linear(hidden, p[f"encoder.layer.{i}.attention.self.query_proj.weight"],
                                      p[f"encoder.layer.{i}.attention.self.query_proj.bias"]), cfg.num_heads)
    k = _transpose_for_scores(_linear(hidden, p[f"encoder.layer.{i}.attention.self.key_proj.weight"],
                                      p[f"encoder.layer.{i}.attention.self.key_proj.bias"]), cfg.num_heads)
    v = _transpose_for_scores(_linear(hidden, p[f"encoder.layer.{i}.attention.self.value_proj.weight"],
                                      p[f"encoder.layer.{i}.attention.self.value_proj.bias"]), cfg.num_heads)

    # scale_factor = 1 + c2p + p2c ; scale = sqrt(head_size * scale_factor). Static
    # python scalar (no host->device jnp.array transfer); jax weak-types it to q's
    # float32 at the divide, matching torch's float32 sqrt.
    scale = math.sqrt(q.shape[-1] * cfg.scale_factor)
    # torch: bmm(query, key.transpose(-1,-2) / scale)  -> divide key.T BEFORE matmul
    kt = jnp.transpose(k, (0, 2, 1)) / scale
    attention_scores = jnp.matmul(q, kt)                                            # [B*H, S, S]

    rel_att = _disentangled_bias(p, i, q, k, rel_pos, rel_emb, cfg)
    attention_scores = attention_scores + rel_att

    attention_scores = attention_scores.reshape(b, cfg.num_heads, s, s)             # [B,H,S,S]
    neg = jnp.finfo(jnp.float32).min
    attention_scores = jnp.where(att_mask.astype(bool), attention_scores, neg)      # masked_fill ~mask
    attention_probs = jax.nn.softmax(attention_scores, axis=-1)

    context = jnp.matmul(attention_probs.reshape(b * cfg.num_heads, s, s), v)        # [B*H, S, hs]
    context = context.reshape(b, cfg.num_heads, s, context.shape[-1])
    context = jnp.transpose(context, (0, 2, 1, 3)).reshape(b, s, -1)                 # [B,S,hidden]
    return context


def _layer(
    p: dict, i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: DebertaCfg,
) -> jax.Array:
    """Mirror of DebertaV2Layer.forward: attention -> SelfOutput -> intermediate ->
    Output, each ending in a post-LayerNorm residual (eps=cfg.layer_norm_eps)."""
    eps = cfg.layer_norm_eps
    ctx = _self_attention(p, i, hidden, att_mask, rel_pos, rel_emb, cfg)
    # SelfOutput: LayerNorm(dense(ctx) + hidden)
    ao = _linear(ctx, p[f"encoder.layer.{i}.attention.output.dense.weight"],
                 p[f"encoder.layer.{i}.attention.output.dense.bias"])
    ao = _layer_norm(ao + hidden, p[f"encoder.layer.{i}.attention.output.LayerNorm.weight"],
                     p[f"encoder.layer.{i}.attention.output.LayerNorm.bias"], eps)
    # Intermediate: gelu(dense(ao))
    inter = _gelu(_linear(ao, p[f"encoder.layer.{i}.intermediate.dense.weight"],
                          p[f"encoder.layer.{i}.intermediate.dense.bias"]))
    # Output: LayerNorm(dense(inter) + ao)
    out = _linear(inter, p[f"encoder.layer.{i}.output.dense.weight"],
                  p[f"encoder.layer.{i}.output.dense.bias"])
    out = _layer_norm(out + ao, p[f"encoder.layer.{i}.output.LayerNorm.weight"],
                      p[f"encoder.layer.{i}.output.LayerNorm.bias"], eps)
    return out


# ----------------------------------------------------------- top-level forward
def _get_rel_embedding(p: dict, cfg: DebertaCfg) -> jax.Array:
    """DebertaV2Encoder.get_rel_embedding: rel_embeddings.weight, then (since
    norm_rel_ebd == 'layer_norm') the encoder-level LayerNorm."""
    rel = p["encoder.rel_embeddings.weight"]
    return _layer_norm(rel, p["encoder.LayerNorm.weight"], p["encoder.LayerNorm.bias"], cfg.layer_norm_eps)


def _get_attention_mask(attention_mask: jax.Array) -> jax.Array:
    """DebertaV2Encoder.get_attention_mask for a [B,S] mask: extended[B,1,1,S];
    mask = extended * extended.squeeze(-2).unsqueeze(-1) -> [B,1,S,S]."""
    ext = attention_mask[:, None, None, :]                  # [B,1,1,S]
    return ext * jnp.transpose(ext, (0, 1, 3, 2))           # [B,1,S,S] = am[b,i]*am[b,j]


def forward(params: dict, input_ids: jax.Array, attention_mask: jax.Array,
            rel_pos: jax.Array, cfg: DebertaCfg) -> jax.Array:
    """Pure encoder forward -> last_hidden_state [B, S, hidden].

    Mirrors DebertaV2Model.forward for deberta-v3-large config: no absolute
    position embedding (position_biased_input=False), no token-type embedding
    (type_vocab_size=0), no embed_proj (embedding_size==hidden_size), no conv,
    z_steps==0.

    REL-POSITION HOIST (frugality, fidelity-NEUTRAL — MEASURED). `rel_pos` (the
    int32[S,S] log-bucketed relative-position table) is a RUNTIME ARGUMENT, not
    computed inside this jitted core. Computing it inside folded an [S,S] int32 array
    into EVERY compiled executable as a baked compile-time constant (24 layers read it);
    as an argument it is a runtime input, so the executable no longer carries the table
    (smaller executables) and it is computed ONCE per bucket by the public `encode`
    wrapper. This is fidelity-NEUTRAL by construction: the core consumes `rel_pos` only
    through integer clip + take_along_axis (pure gather, no float arithmetic on it), so a
    bit-identical `rel_pos` array yields bit-identical attention. And the array IS
    bit-identical whether `build_relative_position` runs eager or jitted, across the whole
    ladder incl. the float-log-path (S>128) and clip (S>512) regimes — proven by
    test_shape_bucket_compile_bound.test_relpos_hoist_bit_identical (the ADR-0009 measured
    gate that licenses the hoist). cfg stays the only static arg, so `rel_pos`'s [S,S]
    shape still keys the compile per S — which BUCKETING bounds."""
    eps = cfg.layer_norm_eps

    # --- embeddings (DebertaV2Embeddings.forward) ---
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]   # [B,S,hidden]
    emb = _layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                      params["embeddings.LayerNorm.bias"], eps)
    mask = attention_mask.astype(emb.dtype)[:, :, None]                      # mask.unsqueeze(2)
    emb = emb * mask

    # --- encoder setup ---
    att_mask = _get_attention_mask(attention_mask)
    rel_emb = _get_rel_embedding(params, cfg)

    hidden = emb
    for i in range(cfg.num_layers):
        hidden = _layer(params, i, hidden, att_mask, rel_pos, rel_emb, cfg)
    return hidden


# jit core: cfg is a NamedTuple of python scalars -> hashable -> jit-static (argnum 4).
# rel_pos is a TRACED runtime arg (argnum 3) — the hoist that keeps the [S,S] table out
# of the baked per-executable constant. The unified daemon measures THIS object's
# `_cache_size()` for the compile-count bound; bucketing keeps it <= the ladder size.
_encode_core = jax.jit(forward, static_argnums=(4,))


def encode(params: dict, input_ids: jax.Array, attention_mask: jax.Array,
           cfg: DebertaCfg) -> jax.Array:
    """Public encoder entry (signature UNCHANGED — every existing caller/test still calls
    `encode(params, input_ids, attention_mask, cfg)`). Computes the hoisted `rel_pos`
    table once (eager — small, and bit-identical to the jitted form, see `forward`), then
    runs the jitted `_encode_core`. The eager `build_relative_position` adds negligible
    dispatch next to the 24-layer forward and, under bucketing, recurs only per bucket."""
    s = input_ids.shape[1]
    rel_pos = build_relative_position(s, cfg.position_buckets, cfg.max_relative_positions)
    return _encode_core(params, input_ids, attention_mask, rel_pos, cfg)
