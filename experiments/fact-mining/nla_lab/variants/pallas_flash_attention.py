#!/usr/bin/env python
"""pallas_flash_attention — FlashAttention (EXACT) realized as a PALLAS KERNEL.

WHAT THIS VARIANT IS, and how it differs from `flash_attention.py`. Both compute the
EXACT dense disentangled self-attention (content `q·kᵀ` + c2p + p2c) by tiling the key
axis and running the online-softmax recurrence — algebraically identical to
`exact_reference`, differing only in softmax REDUCTION ORDER (~1e-5, the EXACT tier).
The difference is WHERE the tiling lives:

  * `flash_attention.py` tiles at the jnp level; XLA is FREE to (and does) FLATTEN the
    Python tile loop back to a dense `[B,H,S,S]` materialization (proven: its latency was
    bit-identical to dense, its small-S memory WORSE). The tiling is a hint XLA ignores.
  * THIS variant moves the tile loop INTO a `pallas_call` kernel
    (`_pallas_disent_attention.disent_flash_kernel`). A Pallas kernel STAYS fused: the
    `[block_q, block_k]` score tile lives in SRAM inside one grid cell and is NEVER written
    to global memory as part of a `[B,H,S,S]` array. So the quadratic materialization is gone by
    CONSTRUCTION (ADR-0000), not by an optimizer's goodwill — this is the realization path
    NLA-OPTIMIZATION-PORTFOLIO.md §9 names.

THE PAYOFF is the FEASIBILITY FRONTIER, not a small-S latency win (a small `[S,S]` is not
IO-bound — honest). Dense OOMs at `B=16,S=1024` (the `[16,16,1024,1024]` score term); true
flash drops the peak to the O(B·H·S·d) activations + O(B·H·S·span) position intermediates,
so those cells RUN. The `est_peak_device_bytes` override (below) shows the model drop
(12.08 GB -> 4.56 GB at B=16/S=1024); the ACTUAL device peak + the long-S IO wall-clock win
are the HOST follow-up on the 2080Ti (ADR-0009 host-only half), NOT claimed here.

GUEST vs HOST (ADR-0009 split, stated explicitly). GUEST-provable now: (1) the kernel
reproduces dense disentangled attention to ~1e-5 (Pallas interpret mode, CPU); (2) the
`est_peak_device_bytes` drops the `B·H·S²` term to 0 (arithmetic + inspection). HOST-only
(NOT claimed here): Pallas-Triton compiling/running the fp32 kernel on Turing sm_75, the
OOM cell actually running, the real device peak, the long-S latency. `interpret` is
selected by backend: CPU guest -> True (correctness); a CUDA jaxlib on the 2080Ti -> False
(real Triton). One flag, no forked code path.

SSOT REUSE (ADR-0012 P1 — own ONLY the attention seam). Embeddings, LayerNorm, GELU, the
q/k/v & pos projections (`_linear`, `_transpose_for_scores`), `make_log_bucket_position`,
`_get_rel_embedding`, the FFN/residual block — ALL are the un-forked `jax_deberta` helpers
(mirroring `flash_attention._flash_layer`). The owned surface is the kernel module + this
orchestration; everything else is the existing core.

HOST-XOR-DEVICE. Neutrally named (no device token); imports jax/jnp + jax_deberta +
shape_buckets + the kernel module + the contract; NO numpy (`jnp.finfo`, not `np.finfo`).
The XOR-gate stays green (both new files are in test_import_xor.py's SCANNED list).
"""

from __future__ import annotations

import math

import jax
import jax.numpy as jnp

import jax_deberta
import shape_buckets
from nla_lab.contract import EncodeBucket, EncodeVariant, FidelityTier, Regime
from nla_lab.registry import register
from nla_lab.variants._pallas_disent_attention import pallas_disentangled_attention, pow2

# Square tile width target (a power of two). The kernel uses `block = min(_TILE_TARGET, S)`;
# since every ENCODE_LEN_BUCKETS rung is a power of two, `block` divides S exactly (no ragged
# tile on the ladder). Flash is EXACT for any tile width (online softmax is algebraically
# identical regardless of block); block trades loop count against tile size, fidelity-NEUTRAL.
#
# CHOSEN 32 for Turing sm_75: `_pallas_disent_attention.smem_bytes(32, 32, d=64) == 45312`
# bytes (44.25 KB) <= the conservative 48 KiB SMEM default — block 64 (115200) and 64x32
# (74240) overflow even the 64 KiB carveout, PROVEN by the smem_bytes gate (the host's
# `Mosaic GPU kernel exceeds available shared memory` made a CAUGHT arithmetic error). The
# fidelity is block-NEUTRAL, so this is a pure tiling/residence change (ADR-0012 P1).
_TILE_TARGET: int = 32

# The kernel adds exactly TWO O(B·H·S·2span) global memory inputs beyond the linear stream:
# `c2p_full` and `p2c_full` (the disentangled-position intermediates). Their count folds into
# the `k_disent` term of the ONE memory model (see est_peak_device_bytes). The per-tile SRAM
# `c2p_blk/p2c_blk` are bounded by one such buffer -> already covered. The `[B,H,S,S]` score
# is NOT an global memory array (it is SRAM-only inside one grid cell) -> `k_quad -> 0`.
_N_DISENT_POSITION_BUFFERS: int = 2


def _build_idx1d(s: int, cfg: "jax_deberta.DebertaCfg") -> jax.Array:
    """The ONE strict-O(S) bucket table `idx1d[d] = clip(make_log_bucket_position(d)+span)`
    for `d in [-(s-1), s-1]` (length `2s-1`), int32. Reuses the UN-FORKED
    `jax_deberta.make_log_bucket_position` on the 1-D relative-offset arange (SSOT, not a
    re-author), mirroring `build_relative_position`'s bucketing predicate. Indexed in-kernel
    at `(i-j)+(s-1)`, it reproduces BOTH the dense c2p column index `clip(bucket(i-j)+span)`
    AND the dense p2c column index `clip(-bucket(j-i)+span)` — MEASURED bit-equal over all S²
    elements (antisymmetry of make_log_bucket_position). Hoisted as a runtime arg (like
    `jax_deberta.encode`'s rel_pos) so it never bakes into the per-S executable constant."""
    span = cfg.pos_ebd_size
    # [2s], NOT [2s-1]: the table is d in [-(s-1), s-1] (length 2s-1), but the Pallas TRITON
    # lowering requires every array shape be a power of 2. 2s-1 is one short, so we extend by
    # one (d=s, a valid-but-UNUSED bucket — the kernel only ever gathers indices [0, 2s-2]) to
    # length 2s, which IS a power of 2 since s is. The pad slot is inert (never gathered).
    d = jnp.arange(-(s - 1), s + 1)                                  # [2s] = (2s-1)+1 pad, pow2
    if cfg.position_buckets > 0 and cfg.max_relative_positions > 0:   # build_relative_position predicate
        rel1d = jax_deberta.make_log_bucket_position(
            d, cfg.position_buckets, cfg.max_relative_positions)
    else:
        rel1d = d
    return jnp.clip(rel1d.astype(jnp.int32) + span, 0, span * 2 - 1).astype(jnp.int32)


def _pallas_attention(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, am_bh: jax.Array,
    idx1d: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg", interpret: bool,
) -> jax.Array:
    """The EXACT flash reformulation of `jax_deberta._self_attention`, computed by the Pallas
    kernel (no `[B,H,S,S]` materialize). The precomputes below — q/k/v, the pos projections,
    `c2p_full`/`p2c_full`, `k_scaled` — are the SAME buffers the dense reference and the jnp
    flash build (the un-forked jax_deberta helpers, ADR-0012 P1); only the score+softmax+
    context seam is owned, and it is the kernel. Returns context `[B, S, hidden]`."""
    b, s, _ = hidden.shape
    h = cfg.num_heads

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
    # scale = sqrt(head_size * scale_factor): static python scalar (weak-typed to float32 at
    # the divide), exactly as the reference computes it — no host->device transfer.
    scale = math.sqrt(hs * cfg.scale_factor)

    # --- disentangled-position intermediates (the SAME buffers the reference builds) ---
    # share_att_key=True: pos projections REUSE this layer's query_proj / key_proj.
    att_span = cfg.pos_ebd_size
    rel_emb_slice = rel_emb[0: att_span * 2][None, :, :]                # [1, 2*span, hidden]
    pos_query = jax_deberta._transpose_for_scores(
        jax_deberta._linear(rel_emb_slice, p[f"encoder.layer.{i}.attention.self.query_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.query_proj.bias"]), h)  # [H,2span,hs]
    pos_key = jax_deberta._transpose_for_scores(
        jax_deberta._linear(rel_emb_slice, p[f"encoder.layer.{i}.attention.self.key_proj.weight"],
                            p[f"encoder.layer.{i}.attention.self.key_proj.bias"]), h)    # [H,2span,hs]
    pos_query = jnp.tile(pos_query, (b, 1, 1))                          # [B*H, 2span, hs]
    pos_key = jnp.tile(pos_key, (b, 1, 1))

    # c2p_full[bh,i,r] = q_i · pos_key_r ; p2c_full[bh,j,r] = k_j · pos_query_r — both
    # [B*H, S, 2*span], O(B·H·S·span), NOT quadratic. The kernel gathers from these.
    c2p_full = jnp.matmul(q, jnp.transpose(pos_key, (0, 2, 1)))         # [B*H, S, 2span]
    p2c_full = jnp.matmul(k, jnp.transpose(pos_query, (0, 2, 1)))       # [B*H, S, 2span]

    # content divides k by scale (the reference's kt = k.T/scale); c2p/p2c divide in-kernel.
    k_scaled = k / scale

    # Pow2 (ADR-0000): brand the tile width for the kernel's typed signature. min(_TILE_TARGET, s)
    # is a power of 2 (both 32 and the seq_bucket s are), so this always succeeds here; a non-pow2
    # would raise at this boundary, on the guest, not as a cryptic Triton error on the host.
    block = pow2(min(_TILE_TARGET, s))
    ctx_bh = pallas_disentangled_attention(
        q, k_scaled, v, c2p_full, p2c_full, idx1d, am_bh,
        scale=scale, block_q=block, block_k=block, interpret=interpret)   # [B*H, S, hs]

    context = ctx_bh.reshape(b, h, s, hs)
    context = jnp.transpose(context, (0, 2, 1, 3)).reshape(b, s, -1)    # [B, S, hidden]
    return context


def _pallas_layer(
    p: dict[str, jax.Array], i: int, hidden: jax.Array, am_bh: jax.Array,
    idx1d: jax.Array, rel_emb: jax.Array, cfg: "jax_deberta.DebertaCfg", interpret: bool,
) -> jax.Array:
    """Mirror of `jax_deberta._layer` with the attention call swapped for the Pallas kernel;
    the SelfOutput / Intermediate / Output residual+LayerNorm block reuses the un-forked
    jax_deberta leaf helpers verbatim (ADR-0012 P1 — own only the attention seam)."""
    eps = cfg.layer_norm_eps
    ctx = _pallas_attention(p, i, hidden, am_bh, idx1d, rel_emb, cfg, interpret)
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


def _pallas_forward(
    params: dict[str, jax.Array], input_ids: jax.Array, attention_mask: jax.Array,
    idx1d: jax.Array, cfg: "jax_deberta.DebertaCfg", interpret: bool,
) -> jax.Array:
    """Encoder forward -> last_hidden_state `[B, S, hidden]`, mirroring `jax_deberta.forward`
    with the per-layer attention swapped for the Pallas flash kernel. Embeddings + rel-emb are
    the reference's, un-forked. `idx1d` (the O(S) bucket table) is threaded as a runtime arg
    (hoist, like jax_deberta's rel_pos). `attention_mask [B,S]` factorizes the reference's
    `[B,1,S,S]` mask -> the `[B*H, S]` `am_bh` the kernel consumes per (query,key) tile."""
    eps = cfg.layer_norm_eps
    inputs_embeds = params["embeddings.word_embeddings.weight"][input_ids]   # [B,S,hidden]
    emb = jax_deberta._layer_norm(inputs_embeds, params["embeddings.LayerNorm.weight"],
                                  params["embeddings.LayerNorm.bias"], eps)
    mask = attention_mask.astype(emb.dtype)[:, :, None]
    emb = emb * mask
    rel_emb = jax_deberta._get_rel_embedding(params, cfg)

    b, s = input_ids.shape
    h = cfg.num_heads
    am_bh = jnp.broadcast_to(
        attention_mask.astype(jnp.float32)[:, None, :], (b, h, s)).reshape(b * h, s)  # [B*H, S]

    hidden = emb
    for i in range(cfg.num_layers):
        hidden = _pallas_layer(params, i, hidden, am_bh, idx1d, rel_emb, cfg, interpret)
    return hidden  # type: ignore[no-any-return]


# jit core: cfg (NamedTuple of python scalars, argnum 4) and `interpret` (python bool, argnum
# 5) are static; `idx1d` is a TRACED runtime arg (argnum 3) — the same hoist jax_deberta uses
# for rel_pos, keeping the O(S) table out of the baked per-S constant. `interpret` is static so
# the SINGLE backend choice (CPU interpret vs GPU Triton) bakes per executable without forking.
_pallas_core = jax.jit(_pallas_forward, static_argnums=(4, 5))


@register
class PallasFlashAttention(EncodeVariant):
    name = "pallas_flash_attention"
    regime = Regime.BOTH                   # exact; relaxes the OOM bound (the feasibility lane)
    fidelity_tier = FidelityTier.EXACT     # exact reformulation, ~1e-5 reduction-order (MEASURED)
    IMPLEMENTED = True                     # real math: Pallas-kernel tiled disentangled flash

    def encode(
        self,
        params: dict[str, jax.Array],
        input_ids: jax.Array,
        attention_mask: jax.Array,
        cfg: jax_deberta.DebertaCfg,
    ) -> jax.Array:
        s = input_ids.shape[1]
        # The O(S) bucket table, computed once per bucket (eager, like jax_deberta.encode's
        # rel_pos hoist). interpret=True on CPU guest (correctness); =False only on a real GPU
        # backend (Triton) — the ADR-0009 guest/host switch, one flag, no forked path.
        idx1d = _build_idx1d(s, cfg)
        interpret = jax.default_backend() != "gpu"
        # jax_deberta is a declared mypy stub-gap (mypy.ini skip); its Array result is returned
        # as the contract's jax.Array (named relaxation, ADR-0012 P8 — mirrors exact_reference).
        return _pallas_core(  # type: ignore[no-any-return]
            params, input_ids, attention_mask, idx1d, cfg, interpret)

    def est_peak_device_bytes(
        self, bucket: EncodeBucket, cfg: jax_deberta.DebertaCfg
    ) -> int:
        """R-MEM override. The Pallas kernel NEVER materializes `[B,H,S,S]` (the score tile is
        SRAM-only inside one grid cell), so the dense quadratic term is DROPPED (`k_quad -> 0`)
        — the TRUE O(S) per-batch peak (ADR-0000), not a fiction. What remains in global memory is the
        linear stream (embeddings/q/k/v/acc/FFN, unchanged) + the TWO O(B·H·S·2span)
        disentangled-position buffers `c2p_full`/`p2c_full`, folded into `k_disent`; plus the
        single O(S) `idx1d` table (`(2S-1)*4` bytes, B/H-free, negligible — does NOT reintroduce
        the quadratic). This is a RE-PARAMETERISED `shape_buckets.MemModel` fed to the ONE
        `peak_variable_bytes` (ADR-0012 P1 — no hand-rolled second model); CONSERVATIVE UPPER
        BOUND (never under). At B=16/S=1024 the model drops 12.08 GB -> 4.56 GB; the actual
        device peak is the HOST gate (ADR-0009)."""
        mm = shape_buckets.dense_deberta_mem_model(
            cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
        mm_flash = mm._replace(k_quad=0, k_disent=mm.k_disent + _N_DISENT_POSITION_BUFFERS)
        base = shape_buckets.peak_variable_bytes(mm_flash, bucket.batch, bucket.seq_bucket)
        idx = (2 * bucket.seq_bucket - 1) * 4                          # O(S) bucket table, B/H-free
        return base + idx  # type: ignore[no-any-return]
