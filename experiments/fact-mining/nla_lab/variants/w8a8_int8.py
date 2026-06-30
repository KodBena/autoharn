#!/usr/bin/env python
"""w8a8_int8 — W8A8 INT8 encode (throughput lane, APPROXIMATE — mild).

WHAT THIS VARIANT IS. The `_linear` seam (jax_deberta.py:115-117) run in INT8: every
per-layer projection weight is INT8-quantized PER-OUTPUT-CHANNEL (one scale per row of
the [out,in] torch weight), the activations are INT8-quantized PER-TOKEN DYNAMICALLY
(one scale per [...,in] row, computed live each forward), and the matmul itself runs as
`lax.dot_general(..., preferred_element_type=jnp.int32)` — true INT8 inputs, INT32
accumulation — then dequantized by `x_scale * w_scale`. The six projections per layer
(q/k/v, attention.output.dense, intermediate.dense, output.dense) go through this path
(`_qlinear`). This is W8A8: Weights-8-bit, Activations-8-bit.

WHY THE STRUCTURE IS REUSED, NOT FORKED (ADR-0012 P1). Everything that is NOT the
`_linear` seam is the un-forked `jax_deberta` math, imported and called directly: the
LayerNorms (`_layer_norm`), GELU (`_gelu`), head transpose (`_transpose_for_scores`),
the embedding gather, the attention mask (`_get_attention_mask`), the relative-position
table (`build_relative_position`), the encoder rel-embedding (`_get_rel_embedding`), and
— crucially — the DISENTANGLED POSITION BIAS (`_disentangled_bias`) UNCHANGED. The forward
loop and `_self_attention` body are re-expressed ONLY because they are the call-sites of
`_linear`; they reuse every non-`_linear` helper verbatim. The variant owns its one seam.

THE §6 CAUTION, HONORED (NLA-OPTIMIZATION-PORTFOLIO.md §6 / synthesis §3). DeBERTa's
attention is the DISENTANGLED 3-term sum (content QK^T + content-to-position c2p +
position-to-content p2c over log-bucketed relative positions), NOT a plain softmax(QK^T).
The caution: approximate the CONTENT stream, FOLD the position terms via their structure,
NEVER approximate the position terms blindly. So this variant quantizes ONLY the CONTENT
projections (q/k/v of `hidden`, and the FFN); the c2p/p2c POSITION logits are computed at
FULL PRECISION by calling the un-forked `jax_deberta._disentangled_bias` (which re-projects
`rel_emb` through the FP q/k weights — share_att_key). The content score `QK^T` and the
`probs @ V` context are also kept FP (they consume the dequantized FP activations) — W8A8
quantizes the LINEAR layers, not the attention BMMs. The quantization touches the content
projection weights/activations; the position stream stays exact.

MEMOIZATION (R1-C). The per-output-channel weight INT8 pack + scales is computed ONCE per
`params` identity and cached on `self` (`_qweights`), so the bench amortizes it in warmup
and the reported latency is not inflated by re-quantizing every forward.

MEMORY (R-MEM) — THE HONEST FINDING, override DECLINED-as-shrink. The stub's premise ("int8
activations are 1 byte/elem -> bytes_per_elem shrinks") does NOT hold for this
fidelity-preserving scoping, and asserting it would be an OOM-CLASS UNDER-ESTIMATE (the one
thing the est contract forbids: "it must NEVER under-estimate"). Reason: the DOMINANT
variable-memory term is the quadratic `[B, H, S, S]` attention-score / softmax / context
buffer (`shape_buckets.peak_variable_bytes`'s `k_quad` term), and a faithful softmax keeps
it FP32 — W8A8 does not (and cannot, short of FlashAttention's non-materialization) shrink
it. W8A8's REAL wins are (i) INT8 WEIGHTS — excluded from this est, which scopes
VARIABLE/non-weight bytes — and (ii) INT8 tensor-core FLOPs — a COMPUTE/throughput win, not
a memory-peak one. The INT8 activation buffers this variant adds are transient and small
(1 byte) and live BESIDE the FP32 dequant outputs, so the dense bound still UPPER-bounds the
real peak. The override below therefore returns the dense bound EXPLICITLY (via the one
`shape_buckets` model, never a second one) and records, in type, that W8A8-linear does not
move the variable-activation peak. This is the honest Pareto entry: a throughput/compute
candidate, NOT a memory candidate.

HOST-XOR-DEVICE. Imports `jax` + `jax_deberta` (neutral device core) + stdlib `math`; no
numpy. The XOR-gate sees no host lib -> clean.
"""

from __future__ import annotations

import math

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register

# The six per-layer projection weights that run through the INT8 `_qlinear` seam. The two
# LayerNorms are not matmuls; the position projections inside `_disentangled_bias` reuse the
# FP q/k weights (share_att_key) and are DELIBERATELY left full-precision (the §6 caution).
_QUANT_PROJ_SUBMODULES = (
    "attention.self.query_proj",
    "attention.self.key_proj",
    "attention.self.value_proj",
    "attention.output.dense",
    "intermediate.dense",
    "output.dense",
)

_INT8_MAX = 127.0


# ------------------------------------------------------------------ the INT8 seam
def _quantize_per_channel_weight(w: jax.Array) -> tuple[jax.Array, jax.Array]:
    """Symmetric per-OUTPUT-CHANNEL INT8 quantization of a torch [out,in] weight: one
    scale per row (`out`). Returns (`w_int8 [out,in]`, `w_scale [out]`)."""
    amax = jnp.max(jnp.abs(w), axis=1, keepdims=True)              # [out,1]
    scale = jnp.where(amax > 0, amax / _INT8_MAX, 1.0)            # avoid div0 on a zero row
    w_int8 = jnp.clip(jnp.round(w / scale), -_INT8_MAX, _INT8_MAX).astype(jnp.int8)
    return w_int8, scale[:, 0]                                     # [out,in], [out]


def _qlinear(x: jax.Array, w_int8: jax.Array, w_scale: jax.Array, b: jax.Array) -> jax.Array:
    """INT8 W8A8 replacement for `jax_deberta._linear` (x @ W.T + b). Per-token dynamic
    activation quant + per-channel weight quant + INT32-accumulating `dot_general`,
    dequantized by `x_scale * w_scale`. Returns FP32 (the dtype the next layer / the
    contract's lhs consumes)."""
    amax = jnp.max(jnp.abs(x), axis=-1, keepdims=True)            # [...,1] per-token
    x_scale = jnp.where(amax > 0, amax / _INT8_MAX, 1.0)
    x_int8 = jnp.clip(jnp.round(x / x_scale), -_INT8_MAX, _INT8_MAX).astype(jnp.int8)
    # contract x's last axis (in) with w_int8's axis 1 (in); INT32 accumulation.
    dn = (((x_int8.ndim - 1,), (1,)), ((), ()))
    acc = jax.lax.dot_general(x_int8, w_int8, dn, preferred_element_type=jnp.int32)  # [...,out] int32
    # dequant: x_scale [...,1] and w_scale [out] both broadcast against [...,out].
    return acc.astype(jnp.float32) * x_scale * w_scale + b


def _quantize_weights(
    params: dict[str, jax.Array], cfg: "jax_deberta.DebertaCfg"
) -> dict[str, tuple[jax.Array, jax.Array]]:
    """One-time per-channel INT8 pack of every projection weight (memoized on self)."""
    qw: dict[str, tuple[jax.Array, jax.Array]] = {}
    for i in range(cfg.num_layers):
        for sub in _QUANT_PROJ_SUBMODULES:
            key = f"encoder.layer.{i}.{sub}.weight"
            qw[key] = _quantize_per_channel_weight(params[key])
    return qw


def _proj(x: jax.Array, qw: dict[str, tuple[jax.Array, jax.Array]],
          p: dict[str, jax.Array], base: str) -> jax.Array:
    """One INT8 projection: fetch the pre-quantized weight + its bias from params."""
    w_int8, w_scale = qw[base + ".weight"]
    return _qlinear(x, w_int8, w_scale, p[base + ".bias"])


# -------------------------------------------- forward with the INT8 seam swapped in
def _self_attention_q(
    p: dict[str, jax.Array], qw: dict[str, tuple[jax.Array, jax.Array]],
    i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """`jax_deberta._self_attention` with the q/k/v CONTENT projections in INT8 and the
    DISENTANGLED POSITION bias kept EXACT (the un-forked `_disentangled_bias`). Every
    non-`_linear` op is the reused jax_deberta helper."""
    b, s, _ = hidden.shape
    base = f"encoder.layer.{i}.attention.self."
    q = jax_deberta._transpose_for_scores(_proj(hidden, qw, p, base + "query_proj"), cfg.num_heads)
    k = jax_deberta._transpose_for_scores(_proj(hidden, qw, p, base + "key_proj"), cfg.num_heads)
    v = jax_deberta._transpose_for_scores(_proj(hidden, qw, p, base + "value_proj"), cfg.num_heads)

    scale = math.sqrt(q.shape[-1] * cfg.scale_factor)
    kt = jnp.transpose(k, (0, 2, 1)) / scale
    attention_scores = jnp.matmul(q, kt)                                          # content QK^T (FP)
    # POSITION TERMS — full precision, folded via structure (§6): un-forked helper.
    rel_att = jax_deberta._disentangled_bias(p, i, q, k, rel_pos, rel_emb, cfg)
    attention_scores = attention_scores + rel_att

    attention_scores = attention_scores.reshape(b, cfg.num_heads, s, s)
    neg = jnp.finfo(jnp.float32).min  # type: ignore[no-untyped-call]
    attention_scores = jnp.where(att_mask.astype(bool), attention_scores, neg)
    attention_probs = jax.nn.softmax(attention_scores, axis=-1)

    context = jnp.matmul(attention_probs.reshape(b * cfg.num_heads, s, s), v)      # probs @ V (FP)
    context = context.reshape(b, cfg.num_heads, s, context.shape[-1])
    context = jnp.transpose(context, (0, 2, 1, 3)).reshape(b, s, -1)
    return context


def _layer_q(
    p: dict[str, jax.Array], qw: dict[str, tuple[jax.Array, jax.Array]],
    i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """`jax_deberta._layer` with the attention-output / FFN projections in INT8; the two
    post-LayerNorm residuals are the reused `jax_deberta._layer_norm`."""
    eps = cfg.layer_norm_eps
    pre = f"encoder.layer.{i}."
    ctx = _self_attention_q(p, qw, i, hidden, att_mask, rel_pos, rel_emb, cfg)
    ao = _proj(ctx, qw, p, pre + "attention.output.dense")
    ao = jax_deberta._layer_norm(ao + hidden, p[pre + "attention.output.LayerNorm.weight"],
                                 p[pre + "attention.output.LayerNorm.bias"], eps)
    inter = jax_deberta._gelu(_proj(ao, qw, p, pre + "intermediate.dense"))
    out = _proj(inter, qw, p, pre + "output.dense")
    out = jax_deberta._layer_norm(out + ao, p[pre + "output.LayerNorm.weight"],
                                  p[pre + "output.LayerNorm.bias"], eps)
    return out  # type: ignore[no-any-return]


def _forward_q(
    params: dict[str, jax.Array], qweights: dict[str, tuple[jax.Array, jax.Array]],
    input_ids: jax.Array, attention_mask: jax.Array,
    rel_pos: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """`jax_deberta.forward` with INT8 layers. Embeddings / mask / rel-embedding are the
    reused jax_deberta helpers; only the per-layer `_linear` seam is swapped."""
    eps = cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    emb = emb * attention_mask.astype(emb.dtype)[:, :, None]
    att_mask = jax_deberta._get_attention_mask(attention_mask)
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)
    hidden = emb
    for i in range(cfg.num_layers):
        hidden = _layer_q(params, qweights, i, hidden, att_mask, rel_pos, rel_emb, cfg)
    return hidden  # type: ignore[no-any-return]


# cfg (a NamedTuple of python scalars) stays the one static arg (argnum 5), exactly as
# jax_deberta._encode_core; rel_pos is the hoisted runtime arg.
_qencode_core = jax.jit(_forward_q, static_argnums=(5,))


@register
class W8A8Int8(EncodeVariant):
    name = "w8a8_int8"
    regime = Regime.THROUGHPUT            # int8 matmul pays on the compute-bound lane
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL
    IMPLEMENTED = True

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # R1-C: memoize the one-time per-channel INT8 weight pack on self (keyed by params
        # identity so a different fixture re-packs rather than serving a stale quant).
        if getattr(self, "_qweights_key", None) != id(params):
            self._qweights = _quantize_weights(params, cfg)
            self._qweights_key = id(params)
        s = input_ids.shape[1]
        rel_pos = jax_deberta.build_relative_position(
            s, cfg.position_buckets, cfg.max_relative_positions)
        # jax_deberta is a declared mypy stub-gap; its Array result is the contract's
        # jax.Array (named relaxation, ADR-0012 P8 — mirrors exact_reference.encode).
        return _qencode_core(  # type: ignore[no-any-return]
            params, self._qweights, input_ids, attention_mask, rel_pos, cfg)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        """HONEST override (R-MEM): the dense bound, EXPLICITLY declared — W8A8 does NOT
        reduce peak variable bytes. The dominant `[B,H,S,S]` attention term stays FP32
        (faithful softmax cannot quantize it; only FlashAttention's non-materialization
        collapses it), W8A8's INT8 weights are excluded from this VARIABLE-byte est, and the
        INT8 tensor-core win is COMPUTE not memory. Lowering `bytes_per_elem` here would be an
        OOM-class UNDER-estimate. Reuses the ONE shape_buckets model (ADR-0012 P1), never a
        second one."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm, bucket.batch, bucket.seq_bucket)
