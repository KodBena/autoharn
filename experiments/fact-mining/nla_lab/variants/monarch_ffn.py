#!/usr/bin/env python
"""monarch_ffn — Monarch / block-butterfly FFN (throughput lane, APPROXIMATE).

WHAT THIS REPLACES (the SEAM, ADR-0012 P1 — own only your seam). The two dense FFN
projections in `jax_deberta._layer` (jax_deberta.py:277-284): `intermediate.dense`
(hidden -> intermediate, then gelu) and `output.dense` (intermediate -> hidden). NOTHING
else: the embeddings, the disentangled 3-term attention, every LayerNorm, the rel-pos
machinery and the FFN BIASES are reused VERBATIM from the `jax_deberta` helpers
(`_self_attention`, `_layer_norm`, `_gelu`, `_get_attention_mask`, `_get_rel_embedding`,
`build_relative_position`) — this variant re-authors only the per-layer COMPOSITION so it
can splice the Monarch operator in where the two FFN `_linear`s were, and approximates
ONLY the two FFN weight MATMULS. The position terms are NOT touched (NLA portfolio §6 / §3
caution); only the content-path FFN weights are structured.

THE MONARCH STRUCTURE (NLA portfolio §3 butterfly lineage; the §10 "shared across both"
row). Each dense FFN weight W (a square-padded N x N, N = k*k) is replaced by an order-2
block-butterfly M = (block-diagonal R) then a stride permutation then (block-diagonal L):
in index n = i*k + j, out index o = a*k + c,
    M[a,c,i,j] = w1[i,a,j] * w2[a,c,i]          (w1, w2 each k x k x k)
computed as two batched matmuls separated by a transpose (the permutation that mixes
across blocks — what makes a butterfly expressive). Param/FLOP count drops from O(N^2) to
2*k^3 = 2*N*sqrt(N) = O(N*sqrt(N)) (the est note's target), the Monarch win.

CRITICAL HONESTY (ADR-0013 — a technique that can't reach P6 without fitting REPORTS that;
the NLA portfolio §10 names it: Monarch "cuts bytes and FLOPs ... AT THE COST OF a
retraining/distillation pass to recover the accuracy that bit-fidelity would have
guaranteed"). A Monarch substituted for a trained dense FFN withOUT a distillation pass
does NOT reproduce the dense map. To give the BEST possible a-priori fit (so the reported
divergence is a real upper bound on the structure's reach, not a strawman random init),
the dense W is PROJECTED onto the Monarch class by the EXACT Frobenius-optimal projection:
under the parametrization above each (a,i) super-block of W must be rank-1, so a per-block
rank-1 SVD gives the optimal (w1, w2). That projection is verified (an in-class matrix
round-trips to ~1e-6 — see the measurement runbook). Even so the dense FFN is NOT in the
Monarch class, so the residual is real and MEASURED, never asserted: the bench reports the
P6 lhs max|Delta| this produces. This is the recorded a-priori-on-fit outcome (a retirement
reason IS data) — see VERDICT at the bottom.

NO fit() CROSSOVER (deliberate). Unlike the randomized-NLA variants (Nystrom/Performer,
which retire BELOW a sequence-length crossover where matrix-concentration has not yet
bitten), Monarch is structurally applicable at EVERY bucket — its precondition is
DISTILLATION, not sequence length. So `fit()` stays the default (always ok): the variant
RUNS at every bucket and the divergence is MEASURED, not pre-asserted by a fit gate
(measuring the real divergence IS the assignment).

MEMORY (R-MEM, override mandate — and an honest correction). `est_peak_device_bytes` is the
VARIABLE (NON-weight) activation peak. Monarch's O(N*sqrt(N)) win is in WEIGHTS and FLOPs,
which that metric EXCLUDES by contract. The gelu still consumes the full [B,S,intermediate]
activation (Monarch preserves the FFN's full intermediate WIDTH; it only structures the two
projections), so the variable-activation peak is UNCHANGED from dense. The stub's R-MEM note
("smaller effective intermediate") is true for a low-rank BOTTLENECK FFN but NOT for Monarch,
which keeps full intermediate width. The override below therefore deliberately returns the
DENSE variable bound (re-using the one shape_buckets model) rather than fabricating a
reduction the technique does not deliver on this axis (ADR-0013: do not silently execute a
mandate found wrong — surface it and do the correct thing).

HOST-XOR-DEVICE. Imports jax + jax_deberta (device core) + the framework-free shape_buckets
+ the contract; no numpy. The XOR-gate sees no host lib -> clean.
"""

from __future__ import annotations

import math
from typing import Any

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register


def _square_dims(d: int) -> tuple[int, int]:
    """Smallest perfect square N = k*k >= d, and its k. The Monarch operator is defined on
    a square N x N block grid (k blocks of k); a rectangular FFN weight is zero-padded up to
    N x N so the block structure stays clean and the rank-1 projection (below) is exact for
    an in-class matrix. (Every dim this stack uses — 16/64/1024/4096 — is already an even
    power of two, hence a perfect square, so the padding is usually a no-op on the larger
    axis; the smaller axis is padded.)"""
    k = math.isqrt(d)
    if k * k < d:
        k += 1
    return k * k, k


def monarch_apply(x: jax.Array, w1: jax.Array, w2: jax.Array,
                  k: int, N: int, out_dim: int) -> jax.Array:
    """Apply the order-2 block-butterfly M to x along its last axis. x[..., in_dim] is
    zero-padded to N, viewed as k blocks of k, run through (batched R) -> transpose
    permutation -> (batched L), giving y[..., N] sliced back to out_dim. Realizes
    M[a,c,i,j] = w1[i,a,j] * w2[a,c,i] (in=i*k+j, out=a*k+c) as two einsums + a swapaxes —
    never materializing the dense N x N matrix."""
    pad = N - x.shape[-1]
    xp = jnp.pad(x, [(0, 0)] * (x.ndim - 1) + [(0, pad)]) if pad else x
    X = xp.reshape(*xp.shape[:-1], k, k)                 # [..., i, j]
    o1 = jnp.einsum("...ij,iaj->...ia", X, w1)           # block-diagonal R: [..., i, a]
    t = jnp.swapaxes(o1, -1, -2)                         # stride permutation: [..., a, i]
    o2 = jnp.einsum("...ai,aci->...ac", t, w2)           # block-diagonal L: [..., a, c]
    y = o2.reshape(*o2.shape[:-2], N)                    # out = a*k + c
    return y[..., :out_dim]


def project_to_monarch(W: jax.Array, N: int, k: int) -> tuple[jax.Array, jax.Array]:
    """The EXACT Frobenius-optimal projection of a dense weight W ([out, in], torch layout)
    onto the Monarch class of `monarch_apply`. Under M[a,c,i,j] = w1[i,a,j]*w2[a,c,i], the
    (a,i) super-block W[a,:,i,:] (rows c, cols j) is forced rank-1, so its best Monarch fit
    is its rank-1 SVD; batching that over all k*k super-blocks gives the optimal (w1, w2).
    Returns w1 [i,a,j], w2 [a,c,i]. (Verified: an in-class matrix round-trips ~1e-6.)"""
    out_dim, in_dim = W.shape
    Wp = jnp.zeros((N, N), W.dtype).at[:out_dim, :in_dim].set(W)
    W4 = Wp.reshape(k, k, k, k)                          # [a, c, i, j]
    Wb = jnp.transpose(W4, (0, 2, 1, 3))                # [a, i, c, j] — the super-blocks
    U, S, Vh = jnp.linalg.svd(Wb, full_matrices=False)  # U[a,i,c,r], S[a,i,r], Vh[a,i,r,j]
    sq = jnp.sqrt(S[..., 0])                            # [a, i] — split the singular value
    u0 = U[..., :, 0]                                   # [a, i, c]
    v0 = Vh[..., 0, :]                                  # [a, i, j]
    w2 = jnp.transpose(u0, (0, 2, 1)) * sq[:, None, :]  # [a, c, i]
    w1 = jnp.transpose(v0 * sq[..., None], (1, 0, 2))   # [i, a, j]
    return w1, w2


def _monarch_forward(params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
                     rel_pos: jax.Array, cfg: "jax_deberta.DebertaCfg",
                     w1in: jax.Array, w2in: jax.Array, w1out: jax.Array, w2out: jax.Array,
                     k_in: int, N_in: int, k_out: int, N_out: int,
                     inter: int, hidden: int) -> jax.Array:
    """jax_deberta.forward with ONLY the two FFN `_linear`s replaced by `monarch_apply`. Every
    other op delegates to the un-forked jax_deberta helper (P1). `k_*/N_*/inter/hidden` are
    static python ints (captured into the jitted closure); the Monarch factors are stacked
    [num_layers, k, k, k] arrays."""
    eps = cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    emb = emb * attention_mask.astype(emb.dtype)[:, :, None]
    att_mask = jax_deberta._get_attention_mask(attention_mask)
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)

    hidden_state = emb
    for i in range(cfg.num_layers):
        ctx = jax_deberta._self_attention(params, i, hidden_state, att_mask, rel_pos, rel_emb, cfg)
        ao = jax_deberta._linear(ctx, params[f"encoder.layer.{i}.attention.output.dense.weight"],
                                 params[f"encoder.layer.{i}.attention.output.dense.bias"])
        ao = jax_deberta._layer_norm(ao + hidden_state,
                                     params[f"encoder.layer.{i}.attention.output.LayerNorm.weight"],
                                     params[f"encoder.layer.{i}.attention.output.LayerNorm.bias"], eps)
        # Intermediate: gelu(MONARCH(ao) + bias)  — replaces intermediate.dense (hidden -> inter)
        inter_pre = monarch_apply(ao, w1in[i], w2in[i], k_in, N_in, inter) \
            + params[f"encoder.layer.{i}.intermediate.dense.bias"]
        inter_act = jax_deberta._gelu(inter_pre)
        # Output: MONARCH(inter) + bias  — replaces output.dense (inter -> hidden)
        out = monarch_apply(inter_act, w1out[i], w2out[i], k_out, N_out, hidden) \
            + params[f"encoder.layer.{i}.output.dense.bias"]
        out = jax_deberta._layer_norm(out + ao,
                                      params[f"encoder.layer.{i}.output.LayerNorm.weight"],
                                      params[f"encoder.layer.{i}.output.LayerNorm.bias"], eps)
        hidden_state = out
    return hidden_state  # type: ignore[no-any-return]


@register
class MonarchFFN(EncodeVariant):
    name = "monarch_ffn"
    regime = Regime.THROUGHPUT
    fidelity_tier = FidelityTier.AGGREGATE_BEHAVIORAL
    IMPLEMENTED = True

    def __init__(self) -> None:
        # PREP MEMOIZATION (R1-C): the one-time Monarch projection of every FFN weight + the
        # jitted core are cached on self, keyed by id(params); the bench's warmup amortizes
        # this out of the timed window (re-projecting per forward would silently inflate latency).
        self._prepared: dict[int, tuple[Any, ...]] = {}

    def _prepare(self, params: dict[str, jax.Array], cfg: "jax_deberta.DebertaCfg") -> tuple[Any, ...]:
        key = id(params)
        cached = self._prepared.get(key)
        if cached is not None:
            return cached
        w_in0 = params["encoder.layer.0.intermediate.dense.weight"]   # [inter, hidden]
        inter, hidden = int(w_in0.shape[0]), int(w_in0.shape[1])
        N_in, k_in = _square_dims(max(inter, hidden))      # intermediate.dense: hidden -> inter
        N_out, k_out = _square_dims(max(hidden, inter))    # output.dense:       inter -> hidden
        w1in, w2in, w1out, w2out = [], [], [], []
        for i in range(cfg.num_layers):
            a1, a2 = project_to_monarch(params[f"encoder.layer.{i}.intermediate.dense.weight"], N_in, k_in)
            b1, b2 = project_to_monarch(params[f"encoder.layer.{i}.output.dense.weight"], N_out, k_out)
            w1in.append(a1); w2in.append(a2); w1out.append(b1); w2out.append(b2)
        factors = (jnp.stack(w1in), jnp.stack(w2in), jnp.stack(w1out), jnp.stack(w2out))

        # jit the splice with cfg static (argnum 4) and the static block dims captured by the
        # closure — exactly as jax_deberta._encode_core jits forward (timing parity).
        def core(p, ids, mask, rel_pos, c, W1i, W2i, W1o, W2o):  # type: ignore[no-untyped-def]  # noqa: ANN001
            return _monarch_forward(p, ids, mask, rel_pos, c, W1i, W2i, W1o, W2o,
                                    k_in, N_in, k_out, N_out, inter, hidden)
        jcore = jax.jit(core, static_argnums=(4,))
        cached = (factors, jcore)
        self._prepared[key] = cached
        return cached

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        (w1in, w2in, w1out, w2out), jcore = self._prepare(params, cfg)
        s = input_ids.shape[1]
        rel_pos = jax_deberta.build_relative_position(
            s, cfg.position_buckets, cfg.max_relative_positions)
        # jax_deberta is a declared mypy stub-gap (mypy.ini skip); its Array result is
        # returned as the contract's jax.Array (named relaxation, ADR-0012 P8).
        return jcore(  # type: ignore[no-any-return]
            params, input_ids, attention_mask, rel_pos, cfg, w1in, w2in, w1out, w2out)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        """The VARIABLE (non-weight) activation peak — UNCHANGED from the dense bound, and
        that is the honest answer (see the module MEMORY note). Monarch structures the two FFN
        WEIGHT matmuls (O(N*sqrt(N)) params/FLOPs) but PRESERVES the full intermediate WIDTH:
        the gelu still consumes the same [B,S,intermediate] activation, so this metric — which
        excludes weight bytes by contract — does not move. The override is explicit (engaging
        the dimension, ADR-0012 R-MEM) and returns the DENSE bound via the one shape_buckets
        model rather than fabricating a reduction the technique does not deliver on this axis."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        return shape_buckets.peak_variable_bytes(  # type: ignore[no-any-return]
            mm, bucket.batch, bucket.seq_bucket)
