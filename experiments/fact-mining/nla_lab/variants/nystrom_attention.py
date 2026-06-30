#!/usr/bin/env python
"""nystrom_attention — Nyström low-rank attention (throughput lane, APPROXIMATE).

WHAT THIS VARIANT IS. A Nyström landmark approximation of the DeBERTa disentangled
self-attention in `jax_deberta._self_attention` (jax_deberta.py:248-258) that
approximates the CONTENT softmax stream via segment-mean landmarks + a pinv core
(NLA-OPTIMIZATION-PORTFOLIO.md Annex II) while FOLDING the c2p/p2c position terms via
their EXACT bucket structure — it does NOT approximate the position terms (the §6
caution: "DeBERTa's three-term attention is not a single softmax(QKᵀ), so
Nyström/Performer do not drop in unmodified: approximate the content stream and fold
the position terms in via their bucket structure"). It NEVER materializes the dense
`[B,H,S,S]` content scores.

THE NYSTRÖM DECOMPOSITION (per head, content + folded bias). With `m` landmarks and
segment size `g = S/m`, the segment-mean landmark queries/keys `Ql,Kl ∈ [m, hs]` are
mask-weighted means of `Q,K` over each contiguous segment, and each landmark `ℓ` is
assigned its segment-CENTRE token position `p_ℓ = ℓ·g + g//2` — an EXACT grid position,
so the disentangled bias evaluated against it is the exact bias function read at a real
relative-position bucket (the structural fold), NOT an approximation of the bias value.
Three softmax sub-blocks carry content + the exactly-folded bias:

  * F = softmax( Q·Klᵀ/scale + bias(i, p_ℓ) )         [S, m]   real query  × landmark key
  * A = softmax( Ql·Klᵀ/scale + bias(p_ℓ, p_ℓ') )     [m, m]   landmark    × landmark
  * B = softmax( Ql·Kᵀ/scale  + bias(p_ℓ, j) )        [m, S]   landmark    × real key

and the attention output is `F @ pinv(A) @ (B @ V)` — the standard Nyström
reconstruction of `softmax(content+bias)`, evaluated WITHOUT ever forming `[S,S]`. The
ONLY approximation is the rank-`m` landmark factorisation of the (content+bias) kernel
plus the landmark-representative position choice for the bias on the landmark seam; every
bias entry that IS computed is computed EXACTLY from the bucket structure (the same
`_disentangled_bias` math, restricted to the required index sub-blocks — see
`_disent_bias_block`, which reproduces `jax_deberta._disentangled_bias` exactly on a full
block).

HONEST VERDICT (ADR-0013 — a recorded failure is data, not a defect). This is an
UNTRAINED landmark approximation against an EXACT reference. The Nyström factorisation
is exact only when the (content+bias) kernel is itself near low-rank / the landmarks
span its row space; for an arbitrary trained (or, on the self-test fixture, random)
DeBERTa it is NOT, so a real, measured P6 lhs divergence is EXPECTED and is the recorded
portfolio outcome (the bake-off retires a technique by MEASUREMENT or a-priori on FIT —
both valid). The variant reports the divergence it actually has; it does NOT silently
return the reference. See the measured number in the deliverable note / the bench output.

FIT PRECONDITION (a-priori retire gate). Linear/landmark attention is contra-indicated
at short S — its constants lose to exact Flash and matrix-concentration does not bite on
a small `[S,S]` (portfolio §1, §3). `fit` retires this variant below `SHORT_S_CROSSOVER`,
RECORDED as a portfolio decision (not run as a bad number). Above it the Nyström blocks
`[S,m]`/`[m,S]` pay only once `S >> m` (`m = NUM_LANDMARKS`).

SSOT REUSE (ADR-0012 P1 — own only the seam). Embeddings, LayerNorm, GELU, the q/k/v &
pos projections (`_linear`, `_transpose_for_scores`), the rel-pos log-bucketing
(`make_log_bucket_position`), `_get_rel_embedding`, the FFN/residual block — ALL are the
un-forked `jax_deberta` helpers. This variant re-authors ONLY the attention orchestration
it is varying (the score materialise + softmax + context).

MEMORY (R-MEM override, below). The landmark factorisation never materialises any
`[B,H,S,S]` buffer (content OR position) — the largest co-resident buffers are
`[B*H, S, m]`/`[B*H, S, 2·span]`, linear in S. So the dense quadratic term is DROPPED
(`k_quad -> 0`) and the override is a RE-PARAMETERISED `shape_buckets.MemModel` fed to the
ONE `peak_variable_bytes` (no hand-rolled second model), a CONSERVATIVE UPPER BOUND.

HOST-XOR-DEVICE. Imports `jax`/`jax.numpy` + the neutrally-named `jax_deberta` device
core + `shape_buckets` (framework-free) + the contract; no numpy. The XOR-gate stays green.
"""

from __future__ import annotations

import math

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, FitVerdict, Regime
from nla_lab.registry import register

#: below this seq_bucket the low-rank content approx is contra-indicated (short-S
#: constants lose to exact Flash; concentration does not bite). ONE home.
SHORT_S_CROSSOVER = 512

#: number of segment-mean landmarks (a power of two). Clamped to `min(NUM_LANDMARKS, S)`
#: and reduced to a divisor of S so the segment reshape `S = m·g` is exact. The Nyström
#: blocks are `[B*H, S, m]`, so the technique pays only once `S >> m`. ONE home.
NUM_LANDMARKS: int = 64

#: conservative count of co-resident `[B*H, S, <=2·eff_span]`-bounded buffers the kernel
#: holds at peak (the content sub-blocks Fc/Bc, their folded-bias gathers c2p_full/p2c_full,
#: the softmax probs, B@V) — folded into `k_disent` against an effective span that covers
#: the landmark width m (see est_peak_device_bytes). An UPPER bound, not a live count.
_N_NYSTROM_BUFFERS: int = 12


def _landmark_count(s: int) -> int:
    """`m` = the largest power-of-two `<= min(NUM_LANDMARKS, S)` that DIVIDES `S`, so the
    segment reshape `S = m·g` is exact. For the power-of-two `ENCODE_LEN_BUCKETS` rungs and
    `NUM_LANDMARKS` a power of two `<= S`, this is just `min(NUM_LANDMARKS, S)`; the divisor
    reduction is a safety net for an off-power-of-two ladder override."""
    m = min(NUM_LANDMARKS, s)
    while s % m:
        m //= 2
    return max(1, m)


def _disent_bias_block(
    p: dict[str, jax.Array], i: int,
    q_rows: jax.Array, k_cols: jax.Array, q_pos: jax.Array, k_pos: jax.Array,
    pos_query: jax.Array, pos_key: jax.Array, cfg: "jax_deberta.DebertaCfg", scale: float,
) -> jax.Array:
    """The EXACT disentangled bias `(c2p+p2c)/scale` between query rows at positions
    `q_pos` (content `q_rows [bh,R,hs]`) and key cols at positions `k_pos` (content
    `k_cols [bh,C,hs]`). Reproduces `jax_deberta._disentangled_bias` EXACTLY on a full
    block (R=C=S, q_pos=k_pos=arange(S), q_rows=Q, k_cols=K) — same `make_log_bucket_position`
    bucketing, same gather index `clip(bucket(q_pos-k_pos)+span)` shared by BOTH the c2p and
    p2c terms (the reference's `c2p_pos`; its `-rel_pos` p2c index resolves to the SAME bucket
    after the bucket's odd symmetry + the `.transpose(-1,-2)`). The position terms are NOT
    approximated: every entry is the exact bias read off the bucket table — only the index
    SET is restricted to the Nyström sub-block."""
    bh, r = q_rows.shape[0], q_rows.shape[1]
    c = k_cols.shape[1]
    span = cfg.pos_ebd_size
    rel = q_pos[:, None] - k_pos[None, :]                                   # [R,C]
    relb = jax_deberta.make_log_bucket_position(
        rel, cfg.position_buckets, cfg.max_relative_positions).astype(jnp.int32)
    gather_pos = jnp.clip(relb + span, 0, span * 2 - 1)                     # [R,C] (c2p & p2c)
    # c2p: (q_rows @ pos_keyᵀ)[bh,R,2span] gathered along the bucket axis at gather_pos
    c2p_full = jnp.matmul(q_rows, jnp.transpose(pos_key, (0, 2, 1)))        # [bh,R,2span]
    c2p = jnp.take_along_axis(
        c2p_full, jnp.broadcast_to(gather_pos[None], (bh, r, c)), axis=-1)  # [bh,R,C]
    # p2c: (k_cols @ pos_queryᵀ)[bh,C,2span] gathered at gather_posᵀ, then transposed back
    p2c_full = jnp.matmul(k_cols, jnp.transpose(pos_query, (0, 2, 1)))      # [bh,C,2span]
    p2c_g = jnp.take_along_axis(
        p2c_full, jnp.broadcast_to(jnp.transpose(gather_pos)[None], (bh, c, r)), axis=-1)
    p2c = jnp.transpose(p2c_g, (0, 2, 1))                                   # [bh,R,C]
    return (c2p + p2c) / scale


def _nystrom_attention(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, am: jax.Array,
    rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """Nyström-approximate disentangled self-attention (no `[B,H,S,S]` materialise). `am`
    is the `[B,S]` integer attention_mask. Returns context `[B, S, hidden]`."""
    b, s, _ = hidden.shape
    h = cfg.num_heads
    bh = b * h
    m = _landmark_count(s)
    g = s // m

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
    scale = math.sqrt(hs * cfg.scale_factor)

    # share_att_key=True: the pos projections REUSE this layer's query_proj / key_proj.
    att_span = cfg.pos_ebd_size
    rel_emb_slice = rel_emb[0: att_span * 2][None, :, :]                    # [1, 2span, hidden]
    pos_query = jnp.tile(jax_deberta._transpose_for_scores(
        jax_deberta._linear(rel_emb_slice, p[f"encoder.layer.{i}.attention.self.query_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.query_proj.bias"]), h), (b, 1, 1))
    pos_key = jnp.tile(jax_deberta._transpose_for_scores(
        jax_deberta._linear(rel_emb_slice, p[f"encoder.layer.{i}.attention.self.key_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.key_proj.bias"]), h), (b, 1, 1))

    # --- mask-weighted segment-mean landmarks (Q,K averaged over real tokens per segment) ---
    am_bh = jnp.broadcast_to(am.astype(jnp.float32)[:, None, :], (b, h, s)).reshape(bh, s)
    am_seg = am_bh.reshape(bh, m, g)                                        # [bh,m,g]
    real_per_seg = jnp.sum(am_seg, axis=-1)                                 # [bh,m]
    denom = jnp.maximum(real_per_seg, 1.0)[:, :, None]                      # avoid /0
    w_seg = am_seg[:, :, :, None]                                           # [bh,m,g,1]
    ql = jnp.sum(q.reshape(bh, m, g, hs) * w_seg, axis=2) / denom           # [bh,m,hs]
    kl = jnp.sum(k.reshape(bh, m, g, hs) * w_seg, axis=2) / denom           # [bh,m,hs]
    landmark_valid = real_per_seg > 0                                       # [bh,m] bool

    # landmark representative positions: each segment's centre token (an exact grid position)
    idx = jnp.arange(s)
    land_pos = jnp.arange(m) * g + (g // 2)                                 # [m] int

    neg = jnp.finfo(jnp.float32).min  # type: ignore[no-untyped-call]
    real_col = am_bh > 0                                                    # [bh,S] real-key mask
    land_col = landmark_valid                                              # [bh,m] landmark mask

    # --- content + exactly-folded bias on the three Nyström sub-blocks ---
    # F: real query (pos i, content q) × landmark key (pos land_pos, content kl)
    fc = jnp.matmul(q, jnp.transpose(kl, (0, 2, 1))) / scale               # [bh,S,m]
    f_score = fc + _disent_bias_block(p, i, q, kl, idx, land_pos, pos_query, pos_key, cfg, scale)
    f_score = jnp.where(land_col[:, None, :], f_score, neg)                # mask dead landmarks
    f = jax.nn.softmax(f_score, axis=-1)                                   # [bh,S,m]

    # A: landmark query (pos land_pos, content ql) × landmark key (pos land_pos, content kl)
    ac = jnp.matmul(ql, jnp.transpose(kl, (0, 2, 1))) / scale              # [bh,m,m]
    a_score = ac + _disent_bias_block(p, i, ql, kl, land_pos, land_pos, pos_query, pos_key, cfg, scale)
    a_score = jnp.where(land_col[:, None, :], a_score, neg)
    a = jax.nn.softmax(a_score, axis=-1)                                  # [bh,m,m]
    a_pinv = jnp.linalg.pinv(a)                                           # [bh,m,m]

    # B: landmark query (pos land_pos, content ql) × real key (pos j, content k)
    bc = jnp.matmul(ql, jnp.transpose(k, (0, 2, 1))) / scale              # [bh,m,S]
    b_score = bc + _disent_bias_block(p, i, ql, k, land_pos, idx, pos_query, pos_key, cfg, scale)
    b_score = jnp.where(real_col[:, None, :], b_score, neg)               # mask padded real keys
    bmat = jax.nn.softmax(b_score, axis=-1)                               # [bh,m,S]

    # Nyström reconstruction: F @ pinv(A) @ (B @ V), never forming [S,S]
    bv = jnp.matmul(bmat, v)                                              # [bh,m,hs]
    ctx = jnp.matmul(f, jnp.matmul(a_pinv, bv))                          # [bh,S,hs]

    context = ctx.reshape(b, h, s, hs)
    context = jnp.transpose(context, (0, 2, 1, 3)).reshape(b, s, -1)      # [B,S,hidden]
    return context


def _nystrom_layer(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, am: jax.Array,
    rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """Mirror of `jax_deberta._layer` with the attention call swapped for the Nyström
    kernel; the SelfOutput / Intermediate / Output residual+LayerNorm block reuses the
    un-forked jax_deberta leaf helpers verbatim (ADR-0012 P1 — own only the attention seam)."""
    eps = cfg.layer_norm_eps
    ctx = _nystrom_attention(p, i, hidden, am, rel_emb, cfg)
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


def _nystrom_forward(params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
                     cfg: "jax_deberta.DebertaCfg") -> jax.Array:
    """Encoder forward -> last_hidden_state `[B, S, hidden]`, mirroring `jax_deberta.forward`
    with the per-layer attention swapped for the Nyström kernel. Embeddings + rel-embedding
    are the reference's, un-forked. (No rel_pos hoist arg: the Nyström sub-blocks compute
    their bucket tables from static landmark/real positions inside the kernel.)"""
    eps = cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]   # [B,S,hidden]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    mask = attention_mask.astype(emb.dtype)[:, :, None]
    emb = emb * mask
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)
    hidden = emb
    for i in range(cfg.num_layers):
        hidden = _nystrom_layer(params, i, hidden, attention_mask, rel_emb, cfg)
    return hidden  # type: ignore[no-any-return]


# jit core: cfg (NamedTuple of python scalars) is static; everything else is a traced
# runtime arg. The landmark/real positions are functions of S (static) -> the graph is static.
_nystrom_core = jax.jit(_nystrom_forward, static_argnums=(3,))


@register
class NystromAttention(EncodeVariant):
    name = "nystrom_attention"
    regime = Regime.THROUGHPUT
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL  # P6: lhs aggregate distance (cluster-set deferred, DESIGN §5)
    IMPLEMENTED = True              # real math: segment-mean Nyström content approx + exact folded position bias

    def fit(self, bucket: EncodeBucket) -> FitVerdict:
        if bucket.seq_bucket < SHORT_S_CROSSOVER:
            return FitVerdict(
                False, f"seq_bucket={bucket.seq_bucket} < crossover {SHORT_S_CROSSOVER}: "
                "low-rank content attention contra-indicated at short S (loses to exact "
                "Flash; concentration does not bite) — retired a-priori (portfolio §1/§3).")
        return FitVerdict(True, f"seq_bucket={bucket.seq_bucket} >= crossover {SHORT_S_CROSSOVER}")

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        # jax_deberta is a declared mypy stub-gap (mypy.ini skip); its Array result is returned
        # as the contract's jax.Array (named relaxation, ADR-0012 P8 — mirrors exact_reference).
        return _nystrom_core(  # type: ignore[no-any-return]
            params, input_ids, attention_mask, cfg)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        """R-MEM override. The landmark factorisation NEVER materialises any `[B,H,S,S]`
        buffer (content OR position): the largest co-resident buffers are the Nyström
        sub-blocks `[B*H, S, m]` and the disentangled gathers `[B*H, S, 2·span]`, all LINEAR
        in S. So the dense quadratic term is DROPPED (`k_quad -> 0`); the `[B*H,S,m]` blocks
        (m = NUM_LANDMARKS) are covered by folding `_N_NYSTROM_BUFFERS` co-resident buffers
        into `k_disent` against an EFFECTIVE span `max(pos_ebd_size, ceil(m/2))` so
        `2·eff_span >= m` makes the fold a CONSERVATIVE upper bound of each `[B*H,S,m]` buffer.
        A RE-PARAMETERISED `shape_buckets.MemModel` fed to the ONE `peak_variable_bytes`
        (ADR-0012 P1 — no hand-rolled second model); stays an UPPER BOUND (never under)."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        m = _landmark_count(bucket.seq_bucket)
        eff_span = max(cfg.pos_ebd_size, (m + 1) // 2)
        mm_nys = mm._replace(
            k_quad=0, pos_ebd_size=eff_span, k_disent=mm.k_disent + _N_NYSTROM_BUFFERS)
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm_nys, bucket.batch, bucket.seq_bucket)
