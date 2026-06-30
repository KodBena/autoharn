#!/usr/bin/env python
"""w8a8_smoothquant — SmoothQuant-calibrated W8A8 INT8 encode (throughput lane, APPROXIMATE).

WHAT THIS VARIANT IS (Xiao et al. 2022, "SmoothQuant"). The round-1 `w8a8_int8` naive
quantizer run with a CALIBRATION SEAM in front of it. SmoothQuant's insight: INT8
activation quant is killed by a FEW per-input-CHANNEL outlier channels that blow up the
per-token activation scale (`amax/127`), forcing every other channel to round through a
coarse step. The fix migrates that outlier magnitude OUT of the activation and INTO the
weight via a per-input-channel SMOOTHING scale `s` (one scalar per input/contraction
channel j):

    s_j = max_i|X_ij|^alpha / max_k|W_kj|^(1-alpha)      (alpha = 0.5)

then rewrites the matmul, EXACTLY equivalently in full precision, as

    Y = X @ W^T = (X / s) @ (W * s)^T        (s broadcasts over the shared input axis j)

so the activation `X/s` has its outlier channels DIVIDED DOWN (cheaper to quantize per
token) and the weight `W*s` absorbs them (still cheap to quantize per OUTPUT channel,
since weights are quantized per row and `s` scales columns). THEN both `X/s` and `W*s`
quantize to INT8 and run through the SAME round-1 path: `lax.dot_general` with INT32
accumulation, dequantized by `x_scale * w_scale`. The benefit is DATA-DEPENDENT — it
appears only where the activation actually has per-channel outlier structure (the
canonical SmoothQuant/AWQ demonstration); on outlier-free data `s ~ 1` and it reduces to
the naive path. It is MEASURED, never asserted (ADR-0009 P6; see the variant's measurement
notes in the delivery report).

WHAT IS REUSED, WHAT THIS OWNS (ADR-0012 P1). The quantize + matmul PATH is the round-1
`w8a8_int8`'s, imported and called directly — `_quantize_per_channel_weight` (per-output-
channel symmetric INT8 weight pack) and `_qlinear` (per-token dynamic activation INT8 +
INT32-accumulating dot_general + dequant). Every NON-`_linear` op is the un-forked
`jax_deberta` core: the LayerNorms, GELU, head transpose, embeddings, attention mask,
rel-embedding, and — crucially — the DISENTANGLED POSITION bias (`_disentangled_bias`),
kept FULL PRECISION exactly as `w8a8_int8` does (the §6 caution: quantize the content
stream, never the position terms). The CALIBRATION FORWARD reuses `jax_deberta._self_attention`
WHOLE for the attention block (no re-fork of the disentangled bias). What this variant OWNS
and adds is ONLY the calibration seam: (1) collect per-input-channel activation magnitudes
from the first forward, (2) compute `s`, (3) fold `s` into the weights (`W*s`, quantized)
and into the activations (`X/s`) at each of the six projection sites. The forward wiring is
re-expressed (rather than importing `w8a8_int8._forward_q`, which has no place to thread
`s`) but every line of it dispatches to a reused `w8a8_int8`/`jax_deberta` helper — the
re-expression IS the seam, it forks no math.

WHERE THE SCALE IS APPLIED (folding posture). Production SmoothQuant folds `X/s` into the
PRIOR op (the layernorm/op feeding the projection) so it is free at inference. That fold is
exact for the q/k/v and intermediate.dense sites (their input is a LayerNorm output, whose
gamma/beta absorb `1/s`), but NOT for attention.output.dense (input is the attention
context) or output.dense (input is a GELU output) — neither prior is a linear LN. So this
variant applies `X/s` at runtime UNIFORMLY at all six sites: mathematically identical to the
fold (`X/s` is the same array either way), the same INT8 quant error, and it works at every
site. The throughput est is the SAME INT8 bytes-per-elem profile as `w8a8_int8` (R-MEM
below).

PER-SITE CALIBRATION. Each of the six projections per layer sees a DIFFERENT activation,
so each gets its OWN `s`: q/k/v share the layer input `hidden` (same activation max) but
DIFFER in `s` because their weight maxes differ; attention.output.dense calibrates on the
context, intermediate.dense on the post-LN, output.dense on the GELU output. The activation
maxes are collected at FULL PRECISION (so they reflect the true outlier structure the real
forward produces), keyed by the projection's weight name.

MEMOIZATION (R1-C / the contract's memoize-prep-on-self mandate). The calibration (one FP
forward to collect activation maxes) + the smoothed-weight INT8 pack + the per-site `s`
arrays are computed ONCE on the FIRST `encode` (keyed by `params` identity) and cached on
`self` (`_qweights`, `_sdict`). The bench's warmup forwards precede the timed window, so the
one-time calibration is amortized OUT of the reported latency. Subsequent forwards reuse the
memoized `s`/weights — calibration is paid once, exactly as the contract requires.

MEMORY (R-MEM) — DENSE BOUND, override DECLINED-as-shrink (identical to `w8a8_int8`). The
dominant variable-memory term is the quadratic `[B,H,S,S]` attention/softmax buffer, which a
faithful softmax keeps FP32 — SmoothQuant does not (and cannot, short of FlashAttention's
non-materialization) shrink it. INT8 weights are excluded from this VARIABLE-byte est; the
INT8 tensor-core win is COMPUTE, not memory. The transient INT8 activation buffers are 1
byte and live beside the FP32 dequant outputs, so the dense bound still UPPER-bounds the
real peak. Lowering `bytes_per_elem` here would be an OOM-class UNDER-estimate. The override
returns the dense bound EXPLICITLY via the ONE `shape_buckets` model (ADR-0012 P1).

HOST-XOR-DEVICE. Imports `jax` + `jax.numpy` + the neutral `jax_deberta`/`shape_buckets`
device cores + the round-1 `w8a8_int8` device variant + stdlib `math`; NO numpy. The
XOR-gate sees no host lib -> clean.
"""

from __future__ import annotations

import math

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register
# REUSE the round-1 naive W8A8 quantize/matmul path verbatim (ADR-0012 P1): the per-output-
# channel INT8 weight pack and the per-token-dynamic INT8 + INT32-accumulating dot_general.
# This variant adds ONLY the calibration seam around them.
from nla_lab.variants import w8a8_int8 as w8

#: SmoothQuant migration strength. alpha=0.5 splits the outlier magnitude evenly between
#: activation and weight (Xiao et al.'s default and the canonical operating point); alpha->1
#: pushes everything into the weight, alpha->0 leaves it in the activation.
_ALPHA = 0.5

#: the six per-layer projection weights that run through the INT8 seam — the SAME set the
#: round-1 `w8a8_int8` quantizes (the position stream inside `_disentangled_bias` stays FP).
_QUANT_PROJ_SUBMODULES = w8._QUANT_PROJ_SUBMODULES


# ----------------------------------------------------- the calibration seam (what this owns)
def _channel_absmax(x: jax.Array) -> jax.Array:
    """Per-INPUT-CHANNEL (last-axis) absolute max of an activation `[..., in]`, reduced over
    every token axis -> `[in]`. This is the activation statistic SmoothQuant calibrates on."""
    return jnp.max(jnp.abs(x), axis=tuple(range(x.ndim - 1)))


def _smoothing_scale(act_absmax: jax.Array, w_absmax: jax.Array, alpha: float) -> jax.Array:
    """`s_j = act_absmax_j^alpha / w_absmax_j^(1-alpha)` per input channel j. A channel that
    is dead in EITHER operand (act or weight max == 0) gets `s=1` (no migration — dividing the
    activation by 0, or scaling a zero weight column, would be meaningless); a non-finite or
    non-positive `s` likewise falls back to 1. So `s` is always a valid, strictly-positive
    per-channel scale, and on outlier-free data it sits near 1 (the naive path)."""
    s = (act_absmax ** alpha) / (w_absmax ** (1.0 - alpha))
    valid = (act_absmax > 0) & (w_absmax > 0) & jnp.isfinite(s) & (s > 0)
    return jnp.where(valid, s, jnp.float32(1.0))


def _collect_act_absmax(
    params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
    rel_pos: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> dict[str, jax.Array]:
    """One FULL-PRECISION forward over the first batch, recording the per-input-channel
    activation absmax feeding EACH of the six projections, keyed by the projection's `.weight`
    name. Reuses `jax_deberta._self_attention` WHOLE for the attention block (so the
    disentangled-position bias is NOT re-forked) and the un-forked `_linear`/`_gelu`/
    `_layer_norm` for the FFN — the activations are exactly those the dense reference produces,
    so the calibration sees the real outlier structure. Run eager (once, in warmup)."""
    eps = cfg.layer_norm_eps
    acc: dict[str, jax.Array] = {}

    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    emb = emb * attention_mask.astype(emb.dtype)[:, :, None]
    att_mask = jax_deberta._get_attention_mask(attention_mask)
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)

    hidden = emb
    for i in range(cfg.num_layers):
        pre = f"encoder.layer.{i}."
        # q/k/v all consume the layer input `hidden` (same activation max; s differs by weight).
        for sub in ("attention.self.query_proj", "attention.self.key_proj",
                    "attention.self.value_proj"):
            acc[pre + sub + ".weight"] = _channel_absmax(hidden)
        # whole attention block, un-forked (disentangled bias included) -> context.
        ctx = jax_deberta._self_attention(params, i, hidden, att_mask, rel_pos, rel_emb, cfg)
        acc[pre + "attention.output.dense.weight"] = _channel_absmax(ctx)
        ao = jax_deberta._linear(ctx, params[pre + "attention.output.dense.weight"],
                                 params[pre + "attention.output.dense.bias"])
        ao = jax_deberta._layer_norm(ao + hidden, params[pre + "attention.output.LayerNorm.weight"],
                                     params[pre + "attention.output.LayerNorm.bias"], eps)
        acc[pre + "intermediate.dense.weight"] = _channel_absmax(ao)
        inter = jax_deberta._gelu(jax_deberta._linear(
            ao, params[pre + "intermediate.dense.weight"], params[pre + "intermediate.dense.bias"]))
        acc[pre + "output.dense.weight"] = _channel_absmax(inter)
        out = jax_deberta._linear(inter, params[pre + "output.dense.weight"],
                                  params[pre + "output.dense.bias"])
        out = jax_deberta._layer_norm(out + ao, params[pre + "output.LayerNorm.weight"],
                                      params[pre + "output.LayerNorm.bias"], eps)
        hidden = out
    return acc


def _smooth_and_quantize(
    params: dict[str, jax.Array], cfg: "jax_deberta.DebertaCfg",
    act_absmax: dict[str, jax.Array], alpha: float,
) -> tuple[dict[str, tuple[jax.Array, jax.Array]], dict[str, jax.Array]]:
    """Fold `s` into the weights and INT8-pack them (the memoized weight side of the
    migration), returning `(qweights, sdict)`. `qweights[key] = quantize(W*s)` via the REUSED
    round-1 per-output-channel packer; `sdict[key] = s` is applied to the ACTIVATION (`X/s`) at
    forward time. `W*s` scales columns (input channels) of the `[out,in]` weight, so the
    per-OUTPUT-channel (row) quant the round-1 packer does is unchanged in structure."""
    qw: dict[str, tuple[jax.Array, jax.Array]] = {}
    sdict: dict[str, jax.Array] = {}
    for i in range(cfg.num_layers):
        for sub in _QUANT_PROJ_SUBMODULES:
            key = f"encoder.layer.{i}.{sub}.weight"
            w = params[key]                                    # [out, in]
            w_absmax = jnp.max(jnp.abs(w), axis=0)             # [in] per-input-channel weight max
            s = _smoothing_scale(act_absmax[key], w_absmax, alpha)   # [in]
            w_smoothed = w * s[None, :]                        # migrate outliers INTO the weight
            qw[key] = w8._quantize_per_channel_weight(w_smoothed)    # REUSED round-1 INT8 pack
            sdict[key] = s
    return qw, sdict


# ------------------------------------------ forward with the smoothed INT8 seam (threads s)
def _proj_s(x: jax.Array, qw: dict[str, tuple[jax.Array, jax.Array]],
            sdict: dict[str, jax.Array], p: dict[str, jax.Array], base: str) -> jax.Array:
    """One smoothed INT8 projection: divide the activation by the per-channel `s` (migrate the
    outliers OUT), then run the REUSED round-1 `_qlinear` against the pre-smoothed-and-packed
    weight. `_qlinear`'s per-token activation scale now sees `X/s`, whose outlier channels are
    divided down — the whole point of the calibration."""
    w_int8, w_scale = qw[base + ".weight"]
    s = sdict[base + ".weight"]
    return w8._qlinear(x / s, w_int8, w_scale, p[base + ".bias"])


def _self_attention_qs(
    p: dict[str, jax.Array], qw: dict[str, tuple[jax.Array, jax.Array]],
    sdict: dict[str, jax.Array], i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """`w8a8_int8._self_attention_q` with the q/k/v CONTENT projections SMOOTHED (`_proj_s`)
    and the DISENTANGLED POSITION bias kept EXACT (the un-forked `_disentangled_bias`, FP
    weights). Every non-projection op is the reused jax_deberta helper."""
    b, s, _ = hidden.shape
    base = f"encoder.layer.{i}.attention.self."
    q = jax_deberta._transpose_for_scores(_proj_s(hidden, qw, sdict, p, base + "query_proj"), cfg.num_heads)
    k = jax_deberta._transpose_for_scores(_proj_s(hidden, qw, sdict, p, base + "key_proj"), cfg.num_heads)
    v = jax_deberta._transpose_for_scores(_proj_s(hidden, qw, sdict, p, base + "value_proj"), cfg.num_heads)

    scale = math.sqrt(q.shape[-1] * cfg.scale_factor)
    kt = jnp.transpose(k, (0, 2, 1)) / scale
    attention_scores = jnp.matmul(q, kt)                                          # content QK^T (FP)
    # POSITION TERMS — full precision, un-forked helper (§6: never quantize the position stream).
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


def _layer_qs(
    p: dict[str, jax.Array], qw: dict[str, tuple[jax.Array, jax.Array]],
    sdict: dict[str, jax.Array], i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """`w8a8_int8._layer_q` with the attention-output / FFN projections SMOOTHED; the two
    post-LayerNorm residuals are the reused `jax_deberta._layer_norm`."""
    eps = cfg.layer_norm_eps
    pre = f"encoder.layer.{i}."
    ctx = _self_attention_qs(p, qw, sdict, i, hidden, att_mask, rel_pos, rel_emb, cfg)
    ao = _proj_s(ctx, qw, sdict, p, pre + "attention.output.dense")
    ao = jax_deberta._layer_norm(ao + hidden, p[pre + "attention.output.LayerNorm.weight"],
                                 p[pre + "attention.output.LayerNorm.bias"], eps)
    inter = jax_deberta._gelu(_proj_s(ao, qw, sdict, p, pre + "intermediate.dense"))
    out = _proj_s(inter, qw, sdict, p, pre + "output.dense")
    out = jax_deberta._layer_norm(out + ao, p[pre + "output.LayerNorm.weight"],
                                  p[pre + "output.LayerNorm.bias"], eps)
    return out  # type: ignore[no-any-return]


def _forward_qs(
    params: dict[str, jax.Array], qweights: dict[str, tuple[jax.Array, jax.Array]],
    sdict: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
    rel_pos: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """`w8a8_int8._forward_q` with the smoothed INT8 layers. Embeddings / mask / rel-embedding
    are the reused jax_deberta helpers; only the per-layer projection seam is swapped."""
    eps = cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    emb = emb * attention_mask.astype(emb.dtype)[:, :, None]
    att_mask = jax_deberta._get_attention_mask(attention_mask)
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)
    hidden = emb
    for i in range(cfg.num_layers):
        hidden = _layer_qs(params, qweights, sdict, i, hidden, att_mask, rel_pos, rel_emb, cfg)
    return hidden  # type: ignore[no-any-return]


# cfg (a NamedTuple of python scalars) is the one static arg (argnum 6); rel_pos is the
# hoisted runtime arg — the same jit shape as jax_deberta._encode_core / w8a8_int8.
_qsencode_core = jax.jit(_forward_qs, static_argnums=(6,))


@register
class W8A8SmoothQuant(EncodeVariant):
    name = "w8a8_smoothquant"
    regime = Regime.THROUGHPUT            # INT8 matmul pays on the compute-bound lane (as w8a8)
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL
    IMPLEMENTED = True                    # real math: SmoothQuant calibration + INT8 W8A8

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # CALIBRATION SEAM (memoized on self, R1-C / contract memoize-prep mandate): on the
        # FIRST forward per `params`, collect per-channel activation maxes (one FP forward),
        # compute `s`, fold it into the INT8-packed weights + the per-site `s` dict. Keyed by
        # params identity so a different fixture re-calibrates rather than serving stale scales.
        # The bench warmup absorbs this one-time cost out of the timed window.
        if getattr(self, "_calib_key", None) != id(params):
            s_cal = input_ids.shape[1]
            rel_pos_cal = jax_deberta.build_relative_position(
                s_cal, cfg.position_buckets, cfg.max_relative_positions)
            act_absmax = _collect_act_absmax(params, input_ids, attention_mask, rel_pos_cal, cfg)
            self._qweights, self._sdict = _smooth_and_quantize(params, cfg, act_absmax, _ALPHA)
            self._calib_key = id(params)
        s = input_ids.shape[1]
        rel_pos = jax_deberta.build_relative_position(
            s, cfg.position_buckets, cfg.max_relative_positions)
        # jax_deberta is a declared mypy stub-gap; its Array result is the contract's jax.Array
        # (named relaxation, ADR-0012 P8 — mirrors exact_reference/w8a8_int8.encode).
        return _qsencode_core(  # type: ignore[no-any-return]
            params, self._qweights, self._sdict, input_ids, attention_mask, rel_pos, cfg)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        """HONEST override (R-MEM): the dense bound, EXPLICITLY — SmoothQuant has the SAME INT8
        bytes-per-elem profile as `w8a8_int8` and does NOT reduce peak variable bytes. The
        dominant `[B,H,S,S]` attention term stays FP32, INT8 weights are excluded from this
        VARIABLE-byte est, and the INT8 tensor-core win is COMPUTE not memory. Lowering
        `bytes_per_elem` here would be an OOM-class UNDER-estimate. Reuses the ONE shape_buckets
        model (ADR-0012 P1), never a second one."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm, bucket.batch, bucket.seq_bucket)
