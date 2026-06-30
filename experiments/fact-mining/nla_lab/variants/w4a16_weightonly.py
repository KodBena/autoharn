#!/usr/bin/env python
"""w4a16_weightonly — W4A16 weight-only quant (latency lane, APPROXIMATE).

WHAT THIS VARIANT IS. 4-bit (int4) WEIGHT-ONLY quantization of every linear projection
weight in the encoder, with per-group fp16 scales; activations stay 16-bit (the "A16").
At inference a real W4A16 kernel keeps the weight in 4-bit storage (the bandwidth win)
and DEQUANTIZES it to the 16-bit activation precision just before each matmul. The
NUMERICAL effect of weight-only quant on the encoder output is, EXACTLY, the
quantization error baked into the dequantized weight `W' = dequant(quant(W))` the matmul
actually consumes — there is no activation-quant rounding in W4A16 (activations are full
16-bit). So this variant materializes `W'` once per weight and runs the un-forked dense
forward with it: the lhs it produces is bit-identical to what an on-the-fly W4A16 dequant
kernel would compute for the same weight operand. That is the honest measurement of the
WEIGHT-quantization divergence in isolation, which IS the defining error of *weight-only*
quant (the P6 number reported below).

SEAM IT OWNS — the WEIGHTS (the `_linear` operand). The portfolio's W4A16 hooks the
weight load inside `_linear` (jax_deberta.py:115-117) at every projection (q/k/v, the
attention-output dense, the FFN intermediate + output dense — the six `nn.Linear`
matmuls per layer). Owning that seam WITHOUT forking the encode (ADR-0012 P1: reuse
jax_deberta's structure; the variant owns only its seam) is exactly the
exact_reference delegation with quantized weights: every other op — embeddings,
LayerNorm, GELU, `build_relative_position`, the disentangled-attention 3-term bias, the
FFN/residual block, bucketing — is the un-forked `jax_deberta` core, called through
`jax_deberta.encode` on a params dict whose six per-layer Linear weights are replaced by
their int4 dequantized form. Nothing about the forward's shape, the disentangled
attention, or the position terms is touched.

WHY THE DISENTANGLED 3-TERM STRUCTURE NEEDS NO SPECIAL HANDLING (contrast the §6
caution). The NLA portfolio §6 caution — "linear-attention approximations do NOT drop
into disentangled attention unmodified; approximate the content stream and fold the
position terms" — binds the SOFTMAX-replacing techniques (Nyström/Performer), which
restructure `softmax(QKᵀ)`. W4A16 is ORTHOGONAL to the attention algebra: it perturbs
the projection WEIGHTS, not the attention structure. The position streams (c2p/p2c)
reuse this layer's query_proj/key_proj weights (share_att_key=True, jax_deberta.py:192-195);
quantizing that ONE shared weight matrix once propagates the SAME dequantized weight into
the content score AND both position scores — precisely what a real W4A16 kernel does
(one 4-bit weight, dequantized once, fed to every matmul that reads it). So the
disentangled terms are handled correctly by construction, not approximated and not
folded.

WHAT IS AND IS NOT MODELED IN THE NUMERICS (honest scope, ADR-0013). The W4 (4-bit
weight quant, incl. the fp16 dequant rounding of the weight operand) IS modeled and
MEASURED in the P6 lhs below. The A16 (16-bit *activations*) is NOT applied to the
delegated forward's activations: the jax_deberta encode is pinned fp32 (shape_buckets
`_BYTES_PER_ELEM`), forking it to cast activations to fp16 would violate P1, and CPU jax
fp16 matmul is upcast/unrepresentative of the GPU latency lane this technique targets —
so faking fp16 activations on the guest would corrupt, not improve, the measurement. The
A16 is instead modeled where it is a real, exact, guest-valid quantity: the MEMORY
estimate (`est_peak_device_bytes` override below). Activations are the VARIABLE peak;
16-bit activations halve their bytes-per-element. This split is stated loudly rather than
papered over.

MEMORY (R-MEM override — be careful what the est models). The est is a conservative
upper bound on the VARIABLE (non-weight) DEVICE peak — i.e. the ACTIVATIONS. W4A16's
4-bit WEIGHTS are NOT in this term at all (weights are not variable/activation memory;
the 4-bit packing is a weight-STORAGE and bandwidth win, which is the latency-lane payoff
but does not touch the activation peak). What W4A16 changes in the variable peak is the
A16: 16-bit (fp16) activations -> `bytes_per_elem` 4 -> 2, halving the whole
quadratic+linear activation bound. So the override re-parameterises the ONE
`shape_buckets.MemModel` with `bytes_per_elem=2` and feeds it to the ONE
`peak_variable_bytes` (never a hand-rolled second model); the co-residency multiples
(k_quad/k_disent/a_hidden/a_inter) are unchanged because the technique changes the
activation PRECISION, not the activation SHAPE/count.

NO FIT CROSSOVER. Unlike Nyström/Performer (whose concentration only bites past S>=512),
W4A16 has no a-priori structural retire condition — weight-only quant pays in the
bandwidth-bound small-batch regime it is built for and is well-defined at every bucket.
So `fit` is the always-fits default (not overridden).

PREP MEMOIZATION (R1-C). The int4 quant + dequant of the six per-layer Linear weights is
a one-time per-`params` transform, computed ONCE and cached on `self` (keyed by the
params object's identity), so the bench's warmup amortizes it out of the timed window and
no forward re-quantizes.

HOST-XOR-DEVICE. Imports jax/jax.numpy + the neutrally-named jax_deberta + the
host-XOR-device-neutral shape_buckets (the R-MEM override's SSOT, exactly as the contract
default and the sibling overrides use it); NO numpy. The XOR-gate stays green.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register

#: int4 GROUP size along the input (contraction) dim: one fp16 scale is shared by this
#: many input channels per output channel (the standard per-group weight-quant grouping,
#: GPTQ/AWQ-style). A weight row narrower than the group degrades gracefully to a single
#: per-output-channel scale. Smaller groups -> finer scales -> less quant error, more
#: scale bytes; 64 is the common latency-lane default.
_GROUP_SIZE = 64

#: the six per-layer `nn.Linear` weight sub-modules whose `.weight` is an `_linear`
#: matmul operand (jax_deberta.py:235-240, 273, 278, 281) — the EXACT W4A16 seam. A
#: `.weight` key is quantized iff it is 2-D AND its name contains one of these infixes,
#: which selects precisely the Linear projections and EXCLUDES the 1-D LayerNorm gains,
#: the word-embedding table, and the rel-embedding table (none of them `_linear`
#: operands). ("output.dense" also matches inside "attention.output.dense"; both ARE
#: Linear weights to quantize, so the overlap is correct, not a bug.)
_LINEAR_PROJ_INFIXES = (
    "attention.self.query_proj",
    "attention.self.key_proj",
    "attention.self.value_proj",
    "attention.output.dense",
    "intermediate.dense",
    "output.dense",
)


def _quantize_dequantize_int4(w: jax.Array, group_size: int) -> jax.Array:
    """`W' = dequant(quant(W))` for one `[out, in]` Linear weight: per-group symmetric
    int4 (15-level, absmax-scaled), with the dequant evaluated at fp16 — the operand a
    W4A16 kernel feeds the matmul. Returns `W'` in W's ORIGINAL dtype (so the delegated
    fp32 encode is unperturbed in structure and returns the contract dtype).

    Grouping is along the INPUT (contraction) dim: a separate fp16 scale per
    `group_size` input channels, per output channel — the standard per-group scheme. The
    input dim is zero-padded up to a group multiple so the grouping vectorizes; padded
    lanes carry magnitude 0 (no effect on any group's absmax) and are sliced off after
    dequant."""
    w32 = w.astype(jnp.float32)
    out_dim, in_dim = w32.shape
    n_groups = (in_dim + group_size - 1) // group_size
    padded = n_groups * group_size
    if padded != in_dim:
        w32 = jnp.pad(w32, ((0, 0), (0, padded - in_dim)))
    wr = w32.reshape(out_dim, n_groups, group_size)

    absmax = jnp.max(jnp.abs(wr), axis=-1, keepdims=True)             # [out, n_groups, 1]
    # symmetric int4: map the group's absmax magnitude to level 7 (range [-8, 7], the
    # -8 slot unused by a symmetric absmax scale). Guard an all-zero group (scale -> 1 so
    # the quotient is a finite 0, dequantizing back to 0).
    scale = jnp.where(absmax == 0.0, jnp.float32(1.0), absmax / 7.0)
    q = jnp.clip(jnp.round(wr / scale), -8.0, 7.0)                    # int4 codes (as float)
    # DEQUANT at fp16 — the 16-bit weight operand a W4A16 dequant kernel produces (the
    # int4 code is exact; the fp16 scale + fp16 product carry the A16 dequant precision).
    dq = (q.astype(jnp.float16) * scale.astype(jnp.float16)).astype(jnp.float32)
    return dq.reshape(out_dim, padded)[:, :in_dim].astype(w.dtype)


def _quantize_params(params: dict[str, jax.Array], group_size: int) -> dict[str, jax.Array]:
    """A new params dict with every Linear `.weight` replaced by its int4 dequantized
    form; all other entries (biases, LayerNorm gains, embeddings, rel-embeddings) pass
    through UNCHANGED (W4A16 quantizes only the matmul weights). The seam the variant
    owns — everything downstream is the un-forked jax_deberta forward."""
    out: dict[str, jax.Array] = {}
    for k, v in params.items():
        if (k.endswith(".weight") and v.ndim == 2
                and any(infix in k for infix in _LINEAR_PROJ_INFIXES)):
            out[k] = _quantize_dequantize_int4(v, group_size)
        else:
            out[k] = v
    return out


@register
class W4A16WeightOnly(EncodeVariant):
    name = "w4a16_weightonly"
    regime = Regime.LATENCY              # bandwidth (fewer weight bytes) wins the launch-bound lane
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL
    IMPLEMENTED = True                   # real math: int4 per-group weight quant + dequant-on-load

    def __init__(self) -> None:
        # PREP MEMOIZATION (R1-C): the int4 dequantized params, cached per source-params
        # identity so the one-time transform is paid on the first (warmup) forward only.
        self._prepared_for: int | None = None
        self._dq_params: dict[str, jax.Array] | None = None

    def _prepared(self, params: dict[str, jax.Array]) -> dict[str, jax.Array]:
        if self._prepared_for != id(params) or self._dq_params is None:
            self._dq_params = _quantize_params(params, _GROUP_SIZE)
            self._prepared_for = id(params)
        return self._dq_params

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # own ONLY the weight seam: quantize→dequant the Linear weights once (memoized),
        # then delegate the WHOLE un-forked encode to jax_deberta (ADR-0012 P1). The
        # returned lhs is jax_deberta.encode's exact dtype (R3-F6).
        dq_params = self._prepared(params)
        return jax_deberta.encode(  # type: ignore[no-any-return]
            dq_params, input_ids, attention_mask, cfg)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        # R-MEM override. The variable (non-weight) DEVICE peak is the ACTIVATIONS; W4A16's
        # A16 makes them 16-bit -> bytes_per_elem 4->2, halving the whole bound. The 4-bit
        # WEIGHTS are NOT in this term (weight storage/bandwidth, not activation memory), so
        # only bytes_per_elem changes — the activation SHAPE/count (k_quad/k_disent/a_*) is
        # unchanged. Re-parameterised single MemModel fed to the single peak_variable_bytes
        # (never a second model); a tight, conservative upper bound for fp16 activations.
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        mm = mm._replace(bytes_per_elem=2)        # A16: 16-bit activations
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm, bucket.batch, bucket.seq_bucket)
