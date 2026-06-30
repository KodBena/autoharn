#!/usr/bin/env python
"""w4a16_awq — AWQ-CALIBRATED 4-bit weight-only quant (latency lane, APPROXIMATE).

WHAT THIS VARIANT IS. The round-1 `w4a16_weightonly` 4-bit weight-only path with an
AWQ calibration seam (Lin et al. 2023, *AWQ: Activation-aware Weight Quantization*).
Naive W4A16 quantizes every Linear weight with a uniform per-group absmax scale, so the
weight channels that multiply HIGH-MAGNITUDE activation inputs — the salient channels,
which dominate the layer's output — are crushed to the same 4-bit grid as every other
channel. AWQ protects them: it scales the salient input channels of the weight UP by a
per-channel factor `s` before the 4-bit group quantization and DOWN by `1/s` after, so
`W_eff = Q(W*s)/s`. The up-scaling lifts the salient channels' magnitude inside their
quant group (they keep more of the 15 int4 levels); the matching `1/s` folds back so the
matmul still computes `x @ W_eff.T ≈ x @ W.T` — but with the salient channels' relative
quant error reduced. `s` is derived from the per-INPUT-CHANNEL ACTIVATION magnitude
(`|x|`), the AWQ insight that weight saliency is set by the activation it multiplies, not
by the weight's own magnitude.

THE SEAM IT OWNS — the CALIBRATION SCALE, nothing else (ADR-0012 P1). The int4
quantize/dequantize kernel is NOT re-authored here: it is imported VERBATIM from the
round-1 `w4a16_weightonly` (`_quantize_dequantize_int4`), as is the Linear-seam selector
(`_LINEAR_PROJ_INFIXES`) and the group size (`_GROUP_SIZE`). AWQ adds exactly two things
around that one kernel: (1) collect per-input-channel activation magnitudes on the first
forward, (2) compute `s` and feed `Q(W*s)/s` through the SAME kernel. With the scale
`s≡1` (alpha=0) this variant reduces to the round-1 naive path BYTE-FOR-BYTE — so the
calibration is a strict superset, never a fork. Everything downstream of the weight
transform is the un-forked `jax_deberta.encode`, identical to the round-1 variant.

CALIBRATION ON THE FIRST FORWARD (R1-C / the contract's memoize-prep-on-self mandate).
AWQ is a post-training calibrator: it needs the activations the weights actually see. So
the FIRST `encode` runs the un-forked FULL-PRECISION `jax_deberta` forward once,
TAPPING the input to each of the six Linear projections per layer (the calibration set),
then per weight grid-searches the AWQ exponent `alpha` to MINIMIZE the true output MSE
`||X Wᵀ - X W_effᵀ||` on those tapped rows, and MEMOIZES the resulting `W_eff` dict on
`self` (keyed by `id(params)`). Subsequent forwards reuse the memoized `W_eff` — the
bench's warmup forward absorbs the one-time calibration, so the timed window is not
inflated (exactly the round-1 prep-memoization, with the calibration added to it).

THE BENEFIT IS MEASURED, NOT ASSERTED (ADR-0009 P6 / ADR-0013 no-faking). The alpha
grid INCLUDES alpha=0 (the naive W4A16 baseline), and the search picks the alpha with
the LOWEST measured calibration MSE — so AWQ can never score worse than naive ON THE
CALIBRATION OBJECTIVE, and where there is NO outlier structure to exploit it picks
alpha≈0 and `s≈1` (a real, honest finding, reported — not a silent no-op disguised as a
win). The DEMONSTRABLE benefit is data-dependent: it appears on weights/activations with
per-channel outlier structure (the canonical SmoothQuant/AWQ scenario). On THIS guest
(CPU jax + the synthetic fixture) the accompanying measurement (i) verifies the
machinery runs and produces non-trivial scales, and (ii) verifies on a CONSTRUCTED-
OUTLIER fixture that the calibrated quant error is strictly LOWER than the naive one.
The REAL maverick-weight benefit — where the round-1 naive W4A16 diverges (mean 0.474) —
is the host `--weights-npz` bench, the stated follow-up (only it confirms the production
payoff; this guest demonstrates the mechanism + the canonical outlier case).

MEMORY (R-MEM) — SAME AS W4A16. AWQ changes the WEIGHT-quant scale, not the activation
profile: the variable (non-weight) DEVICE peak is the ACTIVATIONS, and the A16 makes them
16-bit -> `bytes_per_elem` 4->2, halving the whole quadratic+linear bound; the 4-bit
weights are weight-STORAGE/bandwidth (the latency-lane payoff), excluded from this
variable-byte est. The override re-parameterises the ONE `shape_buckets.MemModel` with
`bytes_per_elem=2` and feeds the ONE `peak_variable_bytes` — identical to the round-1
variant, never a second model (ADR-0012 P1).

NO FIT CROSSOVER (same as W4A16). Weight-only quant pays in the bandwidth-bound
small-batch regime at every bucket; `fit` is the always-fits default.

HOST-XOR-DEVICE. Imports jax/jax.numpy + the neutral `jax_deberta` + the neutral
`shape_buckets`; NO numpy. The XOR-gate stays green.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register
# REUSE the round-1 naive W4A16 quantizer's kernel + seam selector + group size verbatim
# (ADR-0012 P1: the int4 quant/dequant path has exactly ONE home; AWQ owns only the
# calibration scale wrapped around it). Importing the sibling self-registers it under its
# own name (setdefault, identity-checked) — harmless: load_all would import it anyway.
from nla_lab.variants.w4a16_weightonly import (
    _GROUP_SIZE, _LINEAR_PROJ_INFIXES, _quantize_dequantize_int4)

#: cap on calibration rows tapped per Linear (the AWQ calibration set size). AWQ
#: calibrates on a small fixed activation sample; capping bounds the one-time calibration
#: cost + transient memory on the real-weight host bench (the synthetic fixture is far
#: smaller than this). The first real tokens of the first forward, deterministically.
_CALIB_MAX_ROWS = 256
#: the AWQ alpha grid (0.0 .. 1.0). alpha=0 => s≡1 => the naive W4A16 path EXACTLY, so the
#: grid contains the naive baseline and the MEASURED-best alpha is never worse than naive
#: on the calibration objective (ADR-0009: the benefit is measured, not asserted).
_ALPHA_GRID: tuple[float, ...] = tuple(round(a / 10.0, 2) for a in range(0, 11))
#: floor for the activation magnitude / scale (a never-zero divisor for the `/s` fold-back
#: on a dead channel; alpha=0 makes s≡1 regardless, so it bites only for alpha>0).
_EPS = 1e-4


# ------------------------------------------------------------------ the AWQ scale seam
def _awq_scale(act_mag: jax.Array, alpha: float) -> jax.Array:
    """AWQ per-INPUT-CHANNEL scale at exponent `alpha`: `s_j = |x|_j^alpha`, then balanced
    by `s / sqrt(max(s)*min(s))` so its geometric extent straddles 1 — keeping the scaled
    weight `W*s` inside the int4 range rather than pushing a whole side out of it. `alpha=0`
    yields `s≡1` (the naive W4A16 path EXACTLY); larger alpha lifts the high-activation
    (salient) channels more, the AWQ protection knob."""
    s = jnp.power(jnp.maximum(act_mag, _EPS), alpha)         # [in]
    s = s / jnp.sqrt(jnp.max(s) * jnp.min(s))                # balance around 1 (log-mean)
    return jnp.maximum(s, _EPS)


def _awq_quant_dequant(
    w: jax.Array, act_mag: jax.Array, calib_x: jax.Array, group_size: int,
    alpha_grid: tuple[float, ...],
) -> tuple[jax.Array, jax.Array, float]:
    """AWQ-calibrated `W_eff` for one `[out, in]` Linear weight. Grid-searches `alpha`,
    for each computing `W_eff = Q(W*s)/s` (s=_awq_scale) through the REUSED round-1 int4
    kernel, and keeps the alpha minimizing the TRUE output MSE `mean((X Wᵀ - X W_effᵀ)²)`
    on the calibration rows `calib_x [N, in]`. Returns `(W_eff in W's dtype, scale [in],
    alpha)`. The grid includes alpha=0 (==naive W4A16), so the choice is measured-best."""
    w32 = w.astype(jnp.float32)
    ref = calib_x @ w32.T                                    # FP output on calib rows [N,out]
    best: tuple[float, jax.Array, jax.Array, float] | None = None
    for alpha in alpha_grid:
        s = _awq_scale(act_mag, alpha)                       # [in]
        w_q = _quantize_dequantize_int4(w32 * s[None, :], group_size)   # Q(W*s) dequant
        w_eff = w_q / s[None, :]                             # /s -> back to the W scale
        err = float(jnp.mean(jnp.square(calib_x @ w_eff.T - ref)))
        if best is None or err < best[0]:
            best = (err, w_eff, s, alpha)
    assert best is not None                                  # alpha_grid is non-empty
    _, w_eff_best, s_best, alpha_best = best
    return w_eff_best.astype(w.dtype), s_best, alpha_best


# --------------------------------------------- the calibration forward (activation taps)
def _tap(x: jax.Array, mask_flat: jax.Array) -> jax.Array:
    """The input-activation tap: flatten `x [B,S,in]` to `[B*S, in]`, keep only REAL
    (mask==1) rows so padding does not pollute the per-channel magnitude, and cap to
    `_CALIB_MAX_ROWS`. Eager (calibration runs once, un-jitted), so boolean indexing is
    concrete-shaped and legal here."""
    xf = x.reshape(-1, x.shape[-1])
    return xf[mask_flat][:_CALIB_MAX_ROWS]


def _collect_acts(
    params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
    cfg: "jax_deberta.DebertaCfg",
) -> dict[str, jax.Array]:
    """Run the un-forked FULL-PRECISION `jax_deberta` forward ONCE, tapping the input
    activation to each of the six Linear seams per layer (the AWQ calibration set, keyed by
    the weight key). REUSES every `jax_deberta` helper for the actual math — embeddings,
    `_self_attention` (so the disentangled attention is NOT re-forked), `_linear`,
    `_layer_norm`, `_gelu`, the mask/rel-pos/rel-emb setup; it owns ONLY the activation
    taps (the calibration seam). The q/k/v projections share the layer input `hidden`, so
    they share one tap; the FFN inputs (context, post-attn-LN, gelu output) are tapped at
    their own call-sites, exactly mirroring `jax_deberta._layer`'s body."""
    eps = cfg.layer_norm_eps
    s = input_ids.shape[1]
    rel_pos = jax_deberta.build_relative_position(
        s, cfg.position_buckets, cfg.max_relative_positions)
    mask_flat = attention_mask.reshape(-1).astype(bool)

    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    emb = emb * attention_mask.astype(emb.dtype)[:, :, None]
    att_mask = jax_deberta._get_attention_mask(attention_mask)
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)

    acts: dict[str, jax.Array] = {}
    hidden = emb
    for i in range(cfg.num_layers):
        pre = f"encoder.layer.{i}."
        base = pre + "attention.self."
        qkv_in = _tap(hidden, mask_flat)                     # q/k/v share the layer input
        acts[base + "query_proj.weight"] = qkv_in
        acts[base + "key_proj.weight"] = qkv_in
        acts[base + "value_proj.weight"] = qkv_in
        # un-forked disentangled self-attention (content QK^T + c2p/p2c position bias)
        ctx = jax_deberta._self_attention(params, i, hidden, att_mask, rel_pos, rel_emb, cfg)
        acts[pre + "attention.output.dense.weight"] = _tap(ctx, mask_flat)
        ao = jax_deberta._linear(ctx, params[pre + "attention.output.dense.weight"],
                                 params[pre + "attention.output.dense.bias"])
        ao = jax_deberta._layer_norm(ao + hidden,
                                     params[pre + "attention.output.LayerNorm.weight"],
                                     params[pre + "attention.output.LayerNorm.bias"], eps)
        acts[pre + "intermediate.dense.weight"] = _tap(ao, mask_flat)
        inter = jax_deberta._gelu(
            jax_deberta._linear(ao, params[pre + "intermediate.dense.weight"],
                                params[pre + "intermediate.dense.bias"]))
        acts[pre + "output.dense.weight"] = _tap(inter, mask_flat)
        out = jax_deberta._linear(inter, params[pre + "output.dense.weight"],
                                  params[pre + "output.dense.bias"])
        hidden = jax_deberta._layer_norm(out + ao,
                                         params[pre + "output.LayerNorm.weight"],
                                         params[pre + "output.LayerNorm.bias"], eps)
    return acts


def _awq_quantize_params(
    params: dict[str, jax.Array], acts: dict[str, jax.Array], group_size: int,
    alpha_grid: tuple[float, ...],
) -> tuple[dict[str, jax.Array], dict[str, tuple[jax.Array, float]]]:
    """A new params dict with every Linear `.weight` replaced by its AWQ-calibrated
    `W_eff`; all other entries pass through UNCHANGED (the same seam as the round-1
    variant). Also returns, per quantized key, the chosen `(scale [in], alpha)` — the
    calibration record the measurement reads to prove the scales are non-trivial."""
    out: dict[str, jax.Array] = {}
    scales: dict[str, tuple[jax.Array, float]] = {}
    for k, v in params.items():
        if (k.endswith(".weight") and v.ndim == 2
                and any(infix in k for infix in _LINEAR_PROJ_INFIXES)):
            calib_x = acts[k]
            act_mag = jnp.mean(jnp.abs(calib_x), axis=0)     # [in] per-channel magnitude
            w_eff, s, alpha = _awq_quant_dequant(v, act_mag, calib_x, group_size, alpha_grid)
            out[k] = w_eff
            scales[k] = (s, alpha)
        else:
            out[k] = v
    return out, scales


@register
class W4A16AWQ(EncodeVariant):
    name = "w4a16_awq"
    regime = Regime.LATENCY              # bandwidth (fewer weight bytes) wins the launch-bound lane
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL
    IMPLEMENTED = True                   # real math: AWQ-calibrated int4 per-group weight quant

    def __init__(self) -> None:
        # PREP MEMOIZATION (R1-C): the AWQ-calibrated dequantized params + the calibration
        # record, cached per source-params identity. The one-time calibration (an FP
        # forward + the per-weight alpha grid search) is paid on the FIRST (warmup) forward
        # only; subsequent forwards reuse the memoized W_eff (the bench warmup amortizes it).
        self._prepared_for: int | None = None
        self._dq_params: dict[str, jax.Array] | None = None
        #: the chosen (scale, alpha) per quantized weight — the calibration evidence the
        #: P6/benefit measurement reads (proves the scales are non-trivial, not a no-op).
        self._scales: dict[str, tuple[jax.Array, float]] | None = None

    def _prepared(
        self, params: dict[str, jax.Array], input_ids: jax.Array,
        attention_mask: jax.Array, cfg: "jax_deberta.DebertaCfg",
    ) -> dict[str, jax.Array]:
        if self._prepared_for != id(params) or self._dq_params is None:
            acts = _collect_acts(params, input_ids, attention_mask, cfg)
            self._dq_params, self._scales = _awq_quantize_params(
                params, acts, _GROUP_SIZE, _ALPHA_GRID)
            self._prepared_for = id(params)
        return self._dq_params

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # own ONLY the calibration + weight seam: AWQ-calibrate→quant→dequant the Linear
        # weights once (memoized on the FIRST forward's activations), then delegate the
        # WHOLE un-forked encode to jax_deberta (ADR-0012 P1). The returned lhs is
        # jax_deberta.encode's exact dtype (R3-F6).
        dq_params = self._prepared(params, input_ids, attention_mask, cfg)
        return jax_deberta.encode(  # type: ignore[no-any-return]
            dq_params, input_ids, attention_mask, cfg)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        # R-MEM override — SAME AS W4A16 (AWQ changes the weight-quant scale, not the
        # activation profile). The variable (non-weight) peak is the ACTIVATIONS; the A16
        # makes them 16-bit -> bytes_per_elem 4->2, halving the whole bound. The 4-bit
        # weights are weight storage/bandwidth, NOT in this variable term. Re-parameterised
        # single MemModel fed to the single peak_variable_bytes (never a second model).
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        mm = mm._replace(bytes_per_elem=2)        # A16: 16-bit activations
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm, bucket.batch, bucket.seq_bucket)
