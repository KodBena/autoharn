#!/usr/bin/env python
"""performer_favor — Performer / FAVOR+ linear attention on the CONTENT stream
(throughput lane, APPROXIMATE).

WHAT THIS VARIANT OWNS (its seam, ADR-0012 P1 — reuse jax_deberta for everything else).
It replaces ONLY the content score `softmax(q·kᵀ/scale)` of DeBERTa's disentangled
attention (jax_deberta._self_attention, :248-256) with a FAVOR+ positive-random-feature
softmax-kernel estimator `exp(q'·k') ≈ φ(q')·φ(k')` (Choromanski et al., 2021). Every
other piece — embeddings, q/k/v projections, the EXACT disentangled c2p/p2c position
bias (`jax_deberta._disentangled_bias`), the FFN, the LayerNorms, the rel-pos hoist — is
the un-forked jax_deberta code. This variant authors only the content kernel + the fold.

THE DeBERTa-3-TERM CAUTION, FACED HONESTLY (NLA-OPTIMIZATION-PORTFOLIO.md §6 — "Nyström/
Performer do NOT drop in unmodified … approximate the content stream and fold the
position terms in via their bucket structure; never approximate the position terms
blindly"). The pre-softmax logit here is NOT a single `q·kᵀ`; it is
    L[i,j] = (q_i·k_j)/scale   +   c2p[i,j]   +   p2c[i,j]
where c2p/p2c are gathered over LOG-BUCKETED relative positions. Only the FIRST term is a
token-factored inner product, so only it is FAVOR+-kernelizable; the position terms are
pairwise-bucketed and CANNOT be written as `f(i)·g(j)` over per-token vectors. So:
  * the CONTENT term is approximated by random features: `exp(content[i,j]) ≈ φ(q'_i)·φ(k'_j)`,
    with the content scale folded into q',k' so the kernel targets exactly `exp(content)`.
    No dense `softmax(QKᵀ)` content-score pipeline is ever materialised (the memory win,
    `est_peak_device_bytes` below).
  * the POSITION terms are kept EXACT (not approximated, not dropped — §6), computed by the
    un-forked `_disentangled_bias` and folded back MULTIPLICATIVELY:
    `exp(L[i,j]) ≈ φ(q'_i)·φ(k'_j) · exp(c2p[i,j]+p2c[i,j])`, then row-normalised.

THE HONEST LIMIT OF THIS REALISATION (ADR-0013 — report the truth, name the precondition;
a profile the code does not have must not be claimed). Folding the EXACT dense position
bias re-introduces an `[B,H,S,S]` multiply, so this realisation does NOT reach the textbook
O(S) Performer compute/peak — the content softmax PIPELINE is gone (a single kernel product
replaces q·kᵀ→scale→+rel→mask→softmax), but the combine stays quadratic. Reaching full O(S)
needs a STRUCTURED position fold (banded near-diagonal + low-rank tail over the 2·att_span
buckets) or DISTILLATION — the same precondition the portfolio names. `est_peak_device_bytes`
reflects the REALISED (reduced-but-present) quadratic, never the textbook one (no faking).

FIDELITY (ADR-0009 P6 — MEASURED, not asserted). Untrained random features are an UNBIASED
but high-variance estimator of the softmax kernel; the divergence vs the exact reference is a
real number this file does not pre-judge — see the measured result in the bench, and the fit
precondition (distillation / more features) for closing it. fit() retires below the
concentration crossover (random features do not concentrate at short S — portfolio §1/§3).
"""

from __future__ import annotations

import math

import jax
import jax.numpy as jnp
import jax_deberta as jd
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, FitVerdict, Regime
from nla_lab.registry import register

#: below this seq_bucket the random-feature estimator does not concentrate usefully and the
#: dense position fold buys nothing over exact Flash; ONE home (portfolio §1/§3 crossover).
CONCENTRATION_S_CROSSOVER = 512

#: FAVOR+ feature count m, as a function of head_size: enough samples to concentrate the
#: softmax-kernel estimate while staying small vs S (so the [B,H,S,m] feature buffers are
#: sub-[B,H,S,S]). ONE home; the fit/distillation tier would tune these from measured error.
_MIN_FEATURES = 64
_FEATURE_MULT = 8
#: fixed PRNG seed so the random projection is drawn ONCE and memoised (R1-C amortisation);
#: an untrained, fixed random basis — the very thing the fit precondition would replace.
_FEATURE_SEED = 0

#: co-resident [B,H,S,S] count for THIS variant's re-parameterised MemModel (R-MEM override).
#: The dense reference uses k_quad=8 for the content-softmax pipeline (q·kᵀ, scaled, +rel,
#: masked-fill, softmax-probs — ~6-8 distinct co-resident score buffers). FAVOR+ collapses the
#: content path to a SINGLE kernel product φ(q)·φ(k)ᵀ; the realised co-resident content/combine
#: buffers are the kernel product, exp(pos), the combined weight, an einsum scratch, and the
#: two [B,H,S,m] feature buffers (sub-[S,S] at the throughput-lane S where this runs) — a
#: conservative 6, strictly below the dense 8. The disentangled-position term (k_disent) is the
#: un-forked exact path and KEEPS its dense bound — the honest "quadratic reduced, not dropped".
_CONTENT_KQUAD = 6


def _n_features(head_size: int) -> int:
    """FAVOR+ feature count for a head of width `head_size` (one home)."""
    return max(_MIN_FEATURES, _FEATURE_MULT * head_size)


def _draw_omega(num_heads: int, head_size: int, m: int, seed: int) -> jax.Array:
    """Per-head Gaussian random projection ω ∈ R^{H×head_size×m} for the FAVOR+ softmax
    kernel (isotropic N(0,1) rows — the unbiased, untrained basis). Drawn ONCE and memoised
    on the variant (R1-C); the fit/distillation tier is exactly what would replace this fixed
    random ω with a learned / orthogonalised one to cut the estimator variance."""
    key = jax.random.PRNGKey(seed)
    return jax.random.normal(key, (num_heads, head_size, m), dtype=jnp.float32)


def _favor_features(x: jax.Array, omega: jax.Array, is_query: bool) -> jax.Array:
    """FAVOR+ positive random feature map (Choromanski et al. 2021, the softmax kernel):
        φ(x)_r = (1/√m) · exp(ω_r·x − ‖x‖²/2 − stab)
    so that E[φ(a)·φ(b)] = exp(a·b) — an UNBIASED estimate of the (unnormalised) softmax
    weight. `x` is `[B,H,S,head_size]`, ω is `[H,head_size,m]`, returns `[B,H,S,m]`.

    Numerical stabiliser `stab` is a SHIFT that cancels in the row-normalised attention:
    per-QUERY max (a `[B,H,S,1]` constant that multiplies a query's numerator and denominator
    equally), per-KEY a GLOBAL `[B,H,1,1]` max over all keys (a single per-(b,h) constant that
    factors out of both the numerator and denominator sums). Both are exactly the Performer-
    reference stabilisers — chosen so positivity/stability cost no bias in the final ratio."""
    proj = jnp.einsum("bhsd,hdm->bhsm", x, omega)              # ω·x, [B,H,S,m]
    diag = -0.5 * jnp.sum(jnp.square(x), axis=-1, keepdims=True)   # −‖x‖²/2, [B,H,S,1]
    z = proj + diag
    if is_query:
        stab = jnp.max(z, axis=-1, keepdims=True)             # per-query (cancels in ratio)
    else:
        stab = jnp.max(z, axis=(2, 3), keepdims=True)         # global per-(b,h) (factors out)
    return jnp.exp(z - stab) * (1.0 / math.sqrt(omega.shape[-1]))


def _performer_self_attention(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, omega: jax.Array, jd_cfg: "jd.DebertaCfg",
) -> jax.Array:
    """jax_deberta._self_attention with ONLY the content score swapped for the FAVOR+ kernel;
    the disentangled c2p/p2c bias is the un-forked exact path, folded multiplicatively."""
    b, s, _ = hidden.shape
    H = jd_cfg.num_heads
    q = jd._transpose_for_scores(jd._linear(
        hidden, p[f"encoder.layer.{i}.attention.self.query_proj.weight"],
        p[f"encoder.layer.{i}.attention.self.query_proj.bias"]), H)   # [B*H,S,hs]
    k = jd._transpose_for_scores(jd._linear(
        hidden, p[f"encoder.layer.{i}.attention.self.key_proj.weight"],
        p[f"encoder.layer.{i}.attention.self.key_proj.bias"]), H)
    v = jd._transpose_for_scores(jd._linear(
        hidden, p[f"encoder.layer.{i}.attention.self.value_proj.weight"],
        p[f"encoder.layer.{i}.attention.self.value_proj.bias"]), H)

    # EXACT disentangled position bias (un-forked; takes the UNSCALED q,k like the reference).
    rel_att = jd._disentangled_bias(p, i, q, k, rel_pos, rel_emb, jd_cfg)   # [B*H,S,S] logits

    # content scale = sqrt(head_size * scale_factor); fold it into q',k' so the FAVOR+ kernel
    # targets exactly exp(content[i,j]) = exp((q·k)/scale) = exp((q/√scale)·(k/√scale)).
    hs = q.shape[-1]
    inv = 1.0 / math.sqrt(math.sqrt(hs * jd_cfg.scale_factor))
    qb = q.reshape(b, H, s, hs) * inv
    kb = k.reshape(b, H, s, hs) * inv
    vb = v.reshape(b, H, s, hs)

    phi_q = _favor_features(qb, omega, is_query=True)     # [B,H,S,m]
    phi_k = _favor_features(kb, omega, is_query=False)    # [B,H,S,m]
    content_kernel = jnp.einsum("bhim,bhjm->bhij", phi_q, phi_k)   # ≈ exp(content), [B,H,S,S]

    # fold the EXACT position bias back in MULTIPLICATIVELY: exp(L) ≈ kernel · exp(rel_att).
    # Subtract the per-row (per-query) max of rel_att — a row-constant shift that cancels in the
    # normalisation but keeps exp() from overflowing on the (possibly large) position logits.
    rel = rel_att.reshape(b, H, s, s)
    rel = rel - jax.lax.stop_gradient(jnp.max(rel, axis=-1, keepdims=True))
    weight = content_kernel * jnp.exp(rel)               # [B,H,S,S] unnormalised joint weight
    weight = jnp.where(att_mask.astype(bool), weight, 0.0)   # zero padded keys (masked-inert)

    den = jnp.sum(weight, axis=-1, keepdims=True)         # [B,H,S,1]
    num = jnp.einsum("bhij,bhjd->bhid", weight, vb)       # [B,H,S,hs]
    # padded queries (all-masked row) -> den==0 -> 0 context (finite; those rows are not scored).
    context = num / jnp.where(den > 0.0, den, 1.0)
    return jnp.transpose(context, (0, 2, 1, 3)).reshape(b, s, -1)   # [B,S,hidden]


def _performer_layer(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, att_mask: jax.Array,
    rel_pos: jax.Array, rel_emb: jax.Array, omega: jax.Array, jd_cfg: "jd.DebertaCfg",
) -> jax.Array:
    """jax_deberta._layer with the FAVOR+ attention; the SelfOutput/FFN/Output tail is
    un-forked jax_deberta (ADR-0012 P1 — this variant owns only the content seam)."""
    eps = jd_cfg.layer_norm_eps
    ctx = _performer_self_attention(p, i, hidden, att_mask, rel_pos, rel_emb, omega, jd_cfg)
    ao = jd._linear(ctx, p[f"encoder.layer.{i}.attention.output.dense.weight"],
                    p[f"encoder.layer.{i}.attention.output.dense.bias"])
    ao = jd._layer_norm(ao + hidden, p[f"encoder.layer.{i}.attention.output.LayerNorm.weight"],
                        p[f"encoder.layer.{i}.attention.output.LayerNorm.bias"], eps)
    inter = jd._gelu(jd._linear(ao, p[f"encoder.layer.{i}.intermediate.dense.weight"],
                                p[f"encoder.layer.{i}.intermediate.dense.bias"]))
    out = jd._linear(inter, p[f"encoder.layer.{i}.output.dense.weight"],
                     p[f"encoder.layer.{i}.output.dense.bias"])
    return jd._layer_norm(out + ao, p[f"encoder.layer.{i}.output.LayerNorm.weight"],  # type: ignore[no-any-return]
                          p[f"encoder.layer.{i}.output.LayerNorm.bias"], eps)


def _performer_forward(
    params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
    rel_pos: jax.Array, omega: jax.Array, jd_cfg: "jd.DebertaCfg",
) -> jax.Array:
    """jax_deberta.forward with the FAVOR+ per-layer attention. Embeddings, mask, rel-emb and
    the rel-pos hoist are the un-forked reference; `omega` is the runtime random-feature arg
    (a traced input like params, NOT baked into the executable)."""
    eps = jd_cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]
    emb = jd._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                         params["embeddings.LayerNorm.bias"], eps)
    emb = emb * attention_mask.astype(emb.dtype)[:, :, None]
    att_mask = jd._get_attention_mask(attention_mask)         # [B,1,S,S]
    rel_emb = jd._get_rel_embedding(params, jd_cfg)
    hidden = emb
    for i in range(jd_cfg.num_layers):
        hidden = _performer_layer(params, i, hidden, att_mask, rel_pos, rel_emb, omega, jd_cfg)
    return hidden  # type: ignore[no-any-return]


# cfg is static (argnum 5, a hashable NamedTuple); rel_pos + omega are TRACED runtime args, so
# neither the [S,S] table nor the random basis is baked into the per-(cfg,S) executable.
_jit_forward = jax.jit(_performer_forward, static_argnums=(5,))


@register
class PerformerFavor(EncodeVariant):
    name = "performer_favor"
    regime = Regime.THROUGHPUT
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL  # P6 lhs distance (cluster-set deferred)
    IMPLEMENTED = True   # FAVOR+ content kernel + exact disentangled-position fold (this file)

    def _omega(self, cfg: "jd.DebertaCfg") -> jax.Array:
        """Memoise the random projection ONCE per (heads, head_size, m, seed) on the instance
        (R1-C — the bench warmup amortises it out of the reported latency)."""
        hs = cfg.head_size
        m = _n_features(hs)
        keyt = (cfg.num_heads, hs, m, _FEATURE_SEED)
        cache = self.__dict__.setdefault("_omega_cache", {})
        if keyt not in cache:
            cache[keyt] = _draw_omega(cfg.num_heads, hs, m, _FEATURE_SEED)
        return cache[keyt]  # type: ignore[no-any-return]

    def fit(self, bucket: EncodeBucket) -> FitVerdict:
        if bucket.seq_bucket < CONCENTRATION_S_CROSSOVER:
            return FitVerdict(
                False, f"seq_bucket={bucket.seq_bucket} < crossover "
                f"{CONCENTRATION_S_CROSSOVER}: FAVOR+ random features do not concentrate at "
                "short S and the dense position fold buys nothing over exact Flash — retired "
                "a-priori (portfolio §1/§3).")
        return FitVerdict(True, f"seq_bucket={bucket.seq_bucket} >= crossover "
                          f"{CONCENTRATION_S_CROSSOVER}")

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: "jd.DebertaCfg"
    ) -> int:
        """R-MEM override: re-parameterise the ONE memory model (shape_buckets), NOT a second
        one — FAVOR+ replaces the dense content-softmax PIPELINE (k_quad=8 co-resident
        [B,H,S,S]) with a single kernel product + the multiplicative fold (a conservative
        `_CONTENT_KQUAD`). The disentangled-position term (k_disent) is the un-forked exact
        path and keeps its dense bound — this honestly reflects 'content quadratic reduced, not
        dropped' (the full drop is gated on a structured position fold or distillation)."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        mm = mm._replace(k_quad=_CONTENT_KQUAD)
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm, bucket.batch, bucket.seq_bucket)

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: "jd.DebertaCfg",
    ) -> jax.Array:
        s = input_ids.shape[1]
        rel_pos = jd.build_relative_position(
            s, cfg.position_buckets, cfg.max_relative_positions)
        omega = self._omega(cfg)
        return _jit_forward(  # type: ignore[no-any-return]
            params, input_ids, attention_mask, rel_pos, omega, cfg)
