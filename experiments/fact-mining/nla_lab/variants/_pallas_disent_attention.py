#!/usr/bin/env python
"""_pallas_disent_attention — the Pallas FLASH KERNEL for DeBERTa disentangled attention.

WHAT THIS MODULE OWNS (and ONLY this): the single fused attention seam — a tiled,
online-softmax kernel that computes the FULL 3-term disentangled score (content `q·kᵀ`
+ content->position c2p + position->content p2c) tile-by-tile and NEVER materializes the
`[B,H,S,S]` score / probability matrix. The `[block_q, block_k]` score tile lives only in
SRAM inside one `pallas_call` grid cell; the global memory traffic is the O(B·H·S·d) q/k/v/out
activations + the O(B·H·S·span) disentangled-position intermediates — never the quadratic
scores. This is the structural difference vs `flash_attention.py` (jnp-level tiling that
XLA flattens back to dense): a Pallas kernel STAYS fused.

(Memory hierarchy: "global memory" is the GPU's large device pool — GDDR6 on the 2080Ti /
Turing, NOT HBM, which is on datacenter parts. The FlashAttention IO-fusion win — keep the
score tile in on-chip SRAM, don't round-trip it through global memory — holds on GDDR6 too;
only the absolute bandwidth differs.)

THE c2p/p2c FOLD (what a plain flash kernel lacks). For query `i`, key `j`, the dense
reference (`jax_deberta._disentangled_bias`) adds, BEFORE the softmax max/exp:
    c2p[i,j] = c2p_full[bh, i, clip(bucket(i-j)+span)] / scale
    p2c[i,j] = p2c_full[bh, j, clip(-bucket(j-i)+span)] / scale
with `c2p_full = q @ pos_keyᵀ`, `p2c_full = k @ pos_queryᵀ` (the O(B·H·S·2span) buffers,
precomputed once per layer OUTSIDE the kernel — ADR-0012 P1, reuse jax_deberta). This
kernel re-adds those two terms into each `[block_q, block_k]` content tile before the
online-softmax update, so the per-element score is identical to the dense reference and
only the softmax REDUCTION ORDER differs (online vs one-shot) — the EXACT ~1e-5 tier.

THE ONE BUCKET INDEX, ARITHMETIC (MEASURED collapse, NO TABLE). Because `make_log_bucket_position`
is antisymmetric, the dense c2p column index `clip(bucket(i-j)+span)` and the dense p2c
column index `clip(-bucket(j-i)+span)` are PROVABLY EQUAL — verified bit-equal over all
S² elements (S up to 1024) on the guest. So the kernel computes a SINGLE collapsed column
index `clip(bucket(i-j)+span)` IN-KERNEL by pure arithmetic (`_bucket_index`, which reuses the
un-forked `jax_deberta.make_log_bucket_position` — ADR-0012 P1, derive-don't-duplicate); c2p
and p2c differ ONLY in which buffer/row they select (c2p_full row i vs p2c_full row j), not in
the column index. There is NO `idx1d` lookup table (it was a precompute, now derived) and so no
`gather` and no scalar table read — the index is `sign/abs/where/log/ceil/clip`, all
Triton-lowerable. No `[S,S]` table, no `[2S]` table, no two tables.

GUEST vs HOST (ADR-0009 honest split). The guest is CPU jax (no GPU); `pallas_call(...,
interpret=True)` runs the kernel logic on CPU for CORRECTNESS only. Whether Pallas-Triton
compiles & runs this fp32 kernel on Turing sm_75 (the 2080Ti) is a HOST gate, NOT claimed
here. On sm_75 the fp32 `pl.dot` lowers to the FMA (CUDA-core) path — exact, not
tensor-core-accelerated (bf16/tf32 MMA need sm_80+); the IO-fusion win (no `[B,H,S,S]` global memory
round-trip) still holds and is the point.

SMEM/BACKEND (the sm_75 fix — owns ONLY tiling/backend/residence; the §2 fold + idx1d
collapse are UNCHANGED, EXACT ~1e-5 preserved). (1) The Triton backend is PINNED via
`compiler_params=plgpu.CompilerParams(...)`; without it jax 0.10.1 defaults to Mosaic-GPU
(sm_90), the host's `Mosaic GPU kernel exceeds available shared memory` error on Turing.
(2) The `c2p_full`/`p2c_full` position buffers are global-memory-resident (`BlockSpec
memory_space=pl.ANY`) and the kernel selects only the `[block_q, block_k]` entries each
score-tile needs via a BANDED slice + one-hot comparison-sum — NO `gather` primitive (the
sm_75 wall was `Unimplemented primitive in Pallas Triton lowering: gather`). Because the bucket
map `clip(BUCKET(d)+span)` is monotonic, the bucket columns a (qt,kt) tile references are a contiguous `[base, base+W)`
range, loaded by one `pl.ds(base, W)` band slice (`W = next_pow2(block_q+block_k-1) = 64`)
and selected by `arange(W)==sel` (`sel = pos - base`), values BIT-IDENTICAL to the gather
(smoke_equiv `== 0.0`); so the broken `[block, 2span]` SRAM staging (256 KB/buffer at block
128) is gone AND the gather is gone. (3) `smem_bytes()` is the guest-provable budget gate:
it makes "tiles exceed SMEM" a CAUGHT arithmetic error (band block 32 / W 64 -> 53504 B,
PAST the 48 KiB static default but inside the <=64 KiB sm_75 carveout), not a host
`ValueError`. `pl.ds(base, W)` is the SAME `dynamic_slice` the k-loop already lowers with
`pl.dslice(kj0, block_k)`; whether Triton on sm_75 grants the 52 KiB carveout is the HOST
gate (ADR-0009), not claimed here.

HOST-XOR-DEVICE. Neutrally named (no device token) and DEVICE-ONLY: imports jax + pallas,
NEVER numpy (`jnp.finfo`, not `np.finfo`). The XOR-gate stays green.
"""

from __future__ import annotations

import functools
from typing import Callable

import jax
import jax.numpy as jnp
from jax.experimental import pallas as pl
from jax.experimental.pallas import triton as plgpu

import jax_deberta  # SSOT of the log-bucket arithmetic (make_log_bucket_position); device-only (no numpy)

# The lowerable kernel algebra (nla_lab/lower/DESIGN.md): the opaque carrier `Tile`, the
# combinator surface `ops`, and the shape SSOT `Pow2`/`pow2`/`next_pow2` (P1 relocation —
# they MOVED to lower.shape and are re-exported here for the existing call sites).
from nla_lab.lower import ops
from nla_lab.lower.dtype import F32, I32
# explicit re-export (mypy --strict no-implicit-reexport): the existing call sites
# (pallas_flash_attention, test_pallas_smem_budget) import these names from THIS module.
from nla_lab.lower.shape import Pow2 as Pow2
from nla_lab.lower.shape import next_pow2 as next_pow2
from nla_lab.lower.shape import pow2 as pow2
from nla_lab.lower.tile import Tile


# ===================================================================== SMEM budget
# Turing (sm_75 / 2080Ti) shared-memory-per-block budget, BYTES. The host run
# compile-FAILED with `Mosaic GPU kernel exceeds available shared memory` — two root
# causes (the Mosaic-GPU default backend instead of Triton, and the `[block, 2span]`
# position buffers staged in SRAM). The SMEM budget is a DERIVED arithmetic claim the
# guest CAN check (ADR-0009), so a "tiles exceed SMEM" condition is a CAUGHT error here,
# never a host `ValueError` (ADR-0000: the overflow is unrepresentable past this gate).
# 49152 = 48 KiB: the static-default cap a kernel gets with NO opt-in carveout (the
# conservative default this design targets). 65536 = 64 KiB: the sm_75 MAXIMUM, only via
# the dynamic-SMEM carveout opt-in.
TURING_SMEM_BUDGET_BYTES: int = 49152          # 48 KiB, conservative static-default cap
TURING_SMEM_CARVEOUT_MAX_BYTES: int = 65536    # 64 KiB, sm_75 opt-in maximum

# The Triton autotune knobs for the chosen tiles (block 32, §C of the design). num_warps=4
# (128 threads) matches the reference kernel's choice for head_dim<=64; num_stages=1 (no
# software pipelining) is the guaranteed-fit default — num_stages=2 at block 32 would
# re-overflow even the 64 KiB carveout (CAUGHT by smem_bytes, not shipped).
_NUM_WARPS: int = 4
_NUM_STAGES: int = 1


# ----------------------------------------------------- the power-of-2 invariant, by TYPE (ADR-0000)
# `Pow2` / `pow2()` / `next_pow2()` are the shape SSOT of the lowerable kernel algebra; they MOVED
# to `nla_lab.lower.shape` (P1: one home) and are imported above (re-exported here so the existing
# call sites — `pallas_flash_attention`, `test_pallas_smem_budget` — keep importing them from this
# module). Pallas-Triton rejects any non-pow2 array shape (the 2S-1 trap); `Pow2` makes a non-pow2
# kernel dimension UNCONSTRUCTABLE (a mypy error for a raw int, a `pow2()` raise for a runtime value).
# The algebra GENERALIZES them from "block dims only" to EVERY shape-fixing combinator param (see
# lower/ops.py). The names `Pow2`/`pow2`/`next_pow2` are re-bound by the import above.


def _bucket_index(
    rel: jax.Array, position_buckets: int, max_relative_positions: int, span: int, two_span: int,
) -> jax.Array:
    """The disentangled bucket COLUMN INDEX `clip(BUCKET(rel) + span, 0, two_span - 1)` as pure
    arithmetic — the IN-KERNEL replacement for the precomputed `idx1d` gather table.

    ADR-0012 P1 (derive-don't-duplicate): the bucket has exactly ONE home,
    `jax_deberta.make_log_bucket_position`, computed at the point of use — not re-encoded as a
    hand-built O(S) lookup that is then GATHERED (the `gather` was the sm_75 Pallas-Triton wall).
    `BUCKET = make_log_bucket_position(rel, position_buckets, max_relative_positions)` when both
    are > 0 (the `build_relative_position` predicate, mirrored from `_build_idx1d`), else identity.
    This is BYTE-FOR-BYTE the formula `_build_idx1d` baked into `idx1d`, so reading it at
    `idx1d[rel + (S-1)]` and evaluating `_bucket_index(rel, …)` are the SAME integer (max|Δ| == 0).

    Elementwise on any shape: the `[block_q, block_k]` offset tile `d_ij` (the per-element `pos`)
    AND a scalar offset `off_min` (the band base `b_lo`) both flow through unchanged. Every op is
    sign / abs / where / log / ceil / clip — primitives the Triton Pallas backend lowers (the
    `jnp.log`/`jnp.ceil` lowering on sm_75 is the HOST gate, ADR-0009; interpret mode cannot
    discriminate it, exactly as it could not the prior gather)."""
    if position_buckets > 0 and max_relative_positions > 0:
        rel = jax_deberta.make_log_bucket_position(rel, position_buckets, max_relative_positions)
    return jnp.clip(rel.astype(jnp.int32) + span, 0, two_span - 1).astype(jnp.int32)


def smem_bytes(
    block_q: Pow2,
    block_k: Pow2,
    d: Pow2,
    *,
    dtype_bytes: int = 4,
    num_stages: int = 1,
    pos_resident_2span: int = 0,
    band_w: int = 0,
) -> int:
    """Conservative peak SMEM-resident bytes for ONE `disent_flash_kernel` grid cell.

    Pure-Python int arithmetic (no jax, no numpy) so it is host-XOR-device clean and the
    guest can ASSERT it. Counts `q + k + v + score + acc + m + l + position-scratch` as
    co-resident — an UPPER bound: when this passes, the tiles provably fit Turing's SMEM.

    Three position-residence models, selected by the keyword args (UPPER bound each):
    * `pos_resident_2span > 0` — the BROKEN `[block, 2span]` SRAM staging at the named span,
      kept ONLY so the regression assertion reproduces the host's actual OOM as arithmetic.
    * `band_w > 0` — the BANDED-select fix (the shipped seam now): two `[block, W]` band
      slices (`c2p_band` query rows, `p2c_band` key rows) replace the gather scratch. At
      block 32 / W 64 this is `2*32*64 = 4096` words, +8 KiB over the gather, pushing the
      total PAST the 48 KiB static default INTO the <=64 KiB sm_75 carveout (intended).
    * neither (both 0) — the prior per-tile gather residence, whose scratch is the
      `2*block_q*block_k` c2p+p2c gather RESULTS (source `[B*H,S,2span]` stays global memory).
    `num_stages` double-buffers the per-k-tile loaded operands (k, v, score, position)."""
    persistent = block_q * d + block_q * d + 2 * block_q          # q, acc, m + l
    if pos_resident_2span > 0:
        pos = 2 * block_q * (2 * pos_resident_2span)              # broken: [block, 2span] x2
    elif band_w > 0:
        pos = block_q * band_w + block_k * band_w                # fix: c2p_band[bq,W] + p2c_band[bk,W]
    else:
        pos = 2 * block_q * block_k                               # prior: [block_q, block_k] gather results
    pipelined = block_k * d + block_k * d + block_q * block_k + pos   # k, v, score, position
    return (persistent + num_stages * pipelined) * dtype_bytes


# Pallas kernel refs are SRAM-resident handles that index array-like (`ref[...]` -> jax.Array);
# jax 0.10.1's pallas exports no public `Ref` type, so they are annotated `jax.Array` — a NAMED
# relaxation (the ref indexes/assigns exactly as an array does here), not a precision loss.
def disent_flash_kernel(
    q_ref: jax.Array, c2p_full_ref: jax.Array, am_q_ref: jax.Array,  # c2p_full global-memory-resident (pl.ANY); q/am resident over the query tile
    k_ref: jax.Array, v_ref: jax.Array, p2c_full_ref: jax.Array, am_k_ref: jax.Array,      # p2c_full global-memory-resident (pl.ANY); k/v/am whole key axis (sliced per k-tile)
    o_ref: jax.Array,                                 # output context tile
    *, scale: float, S: Pow2, block_q: Pow2, block_k: Pow2, d: Pow2, W: Pow2, neg: float,
    position_buckets: int, max_relative_positions: int, span: int,
) -> None:
    """Online-softmax disentangled attention for ONE (bh, query-tile) grid cell.

    Grid is `(B*H, num_q_tiles)`; `program_id(1)` selects the query tile. The inner
    `fori_loop` walks key tiles, recomputing each `[block_q, block_k]` score tile (content
    + c2p + p2c) in SRAM and folding it into the running (max, denom, numerator) — the
    `[B,H,S,S]` score is never formed. EXACT vs `jax_deberta._self_attention`: same
    per-element score, only the softmax reduction order differs.

    `W` is the BAND WIDTH (a `Pow2`, 64 at block 32 / 2span>=64): the (i-j) offsets a
    (query-tile, key-tile) pair spans are a contiguous range, and the bucket map
    `clip(BUCKET(d)+span)` is monotonic, so the bucket columns the tile references form a
    contiguous `[base, base+W)` slice of the `2span` axis. The c2p/p2c terms are selected by a
    `pl.ds(base, W)` BAND slice + a one-hot comparison-sum (no `gather` primitive — the sm_75
    Triton-lowering wall the gather hit). The column index itself is `_bucket_index(...)`, pure
    arithmetic computed in-kernel (no `idx1d` table, no scalar table read)."""
    bh = pl.program_id(0)              # batch*head index, to address the global-memory-resident position buffers
    qt = pl.program_id(1)
    qi0 = qt * block_q
    two_span = 2 * span                # == c2p_full_ref.shape[-1]; the disentangled column axis (2*pos_ebd_size)

    q = q_ref[0]                       # [block_q, d]  (content query rows)
    am_i = am_q_ref[0]                 # [block_q]  (query mask)
    arows = qi0 + jnp.arange(block_q)  # global query ids for this tile
    # `d` (head_size) is a `Pow2` kernel param (was `q.shape[-1]`; identical value — the
    # BlockSpec query tile is `(1, block_q, d)`). Threading it lets the ONE pallas builder
    # serve both this oracle kernel and the algebra port, whose `Tile` q has no `.shape`.
    # c2p_full_ref / p2c_full_ref are NOT staged into SRAM (BlockSpec memory_space=pl.ANY):
    # the whole [B*H, S, 2span] stays global-memory-resident and only a [block, W] BAND is sliced
    # per score-tile in `body`, so no [block, 2span] buffer ever lives in Turing's 64 KB SMEM
    # (root cause #2). The bucket column itself is `_bucket_index(...)` arithmetic — no idx1d table.

    m = jnp.full((block_q,), -jnp.inf, dtype=jnp.float32)     # running max
    l = jnp.zeros((block_q,), dtype=jnp.float32)              # running denom
    acc = jnp.zeros((block_q, d), dtype=jnp.float32)          # running numerator

    n_kt = pl.cdiv(S, block_k)

    def body(
        kt: jax.Array, carry: tuple[jax.Array, jax.Array, jax.Array],
    ) -> tuple[jax.Array, jax.Array, jax.Array]:
        m, l, acc = carry
        kj0 = kt * block_k
        ks = pl.dslice(kj0, block_k)
        k = k_ref[0, ks, :]            # [block_k, d]  (already /scale: k_scaled)
        v = v_ref[0, ks, :]           # [block_k, d]
        am_j = am_k_ref[0, ks]        # [block_k]  (key mask)
        bcols = kj0 + jnp.arange(block_k)  # global key ids

        # --- content term (fp32 -> FMA on sm_75; exact). q · k_scaledᵀ ---
        content = pl.dot(q, k.T)      # [block_q, block_k]

        # --- ONE bucket-index tile, used for BOTH terms (MEASURED-equal collapse) ---
        d_ij = arows[:, None] - bcols[None, :]      # [block_q, block_k] = i - j
        pos = _bucket_index(d_ij, position_buckets, max_relative_positions, span, two_span)  # [block_q,block_k] int = clip(bucket(i-j)+span)

        # --- BANDED select (gather-free): replace the c2p/p2c advanced-index gather (the sm_75
        # Triton wall `Unimplemented primitive ... gather`) with a band SLICE + one-hot sum,
        # using only primitives Triton's Pallas backend lowers (dynamic_slice, arange, ==, *,
        # sum). Bit-identical to the gather (smoke_equiv == 0.0 over deberta-large dims), so the
        # EXACT ~1e-5 fold is untouched — ONLY the selection mechanism changed (ADR-0012 P1). ---
        # off_min for this (query-tile, key-tile): ARITHMETIC of grid (qi0) + loop (kj0) scalars.
        # clip(BUCKET(d)+span) monotonic => the band's bucket columns are [b_lo, b_lo+width), width <= W.
        off_min = qi0 - (kj0 + block_k - 1)                   # min (i-j) offset in the tile
        b_lo = _bucket_index(off_min, position_buckets, max_relative_positions, span, two_span)  # SCALAR bucket col, arithmetic (no table)
        # pl.ds/dynamic_slice SILENTLY CLAMPS its start to keep the window in-bounds; compute
        # that clamp EXPLICITLY as `base` and derive `sel` from the SAME `base`, so the slice and
        # the one-hot can never disagree at the high edge (ADR-0000: mismatch unrepresentable).
        base = jnp.clip(b_lo, 0, two_span - W)               # the CLAMPED band base
        c2p_band = c2p_full_ref[bh, pl.ds(qi0, block_q), pl.ds(base, W)]   # [block_q, W] query rows
        p2c_band = p2c_full_ref[bh, pl.ds(kj0, block_k), pl.ds(base, W)]   # [block_k, W] key rows
        # gather(band[row, sel]) as a one-hot select over the band's W axis, reduced by a
        # BROADCAST-MULTIPLY + sum — NOT jnp.einsum. The einsum form "iw,ijw->ij" shares index i
        # across both operands + the output, so jax lowers it to a BATCHED dot_general, and
        # Pallas-Triton asserts batch_dims==((),()) (no batched matmul). Broadcasting the band
        # against the one-hot and summing the W axis is the same value with zero dot_general.
        sel = pos - base                                      # [block_q, block_k], provably in [0, W)
        onehot = (jnp.arange(W)[None, None, :] == sel[:, :, None]).astype(jnp.float32)  # [bq,bk,W]
        c2p = jnp.sum(c2p_band[:, None, :] * onehot, axis=-1)  # [bq,1,W]*[bq,bk,W] -> sum_W -> [bq,bk]
        p2c = jnp.sum(p2c_band[None, :, :] * onehot, axis=-1)  # [1,bk,W]*[bq,bk,W] -> sum_W -> [bq,bk]

        # --- combined score / scale, then mask (content already /scale via k_scaled) ---
        s = content + (c2p + p2c) / scale
        s = jnp.where((am_i[:, None] * am_j[None, :]) > 0, s, neg)

        # --- online-softmax update (running max + rescale) ---
        m_tile = jnp.max(s, axis=-1)
        m_new = jnp.maximum(m, m_tile)
        corr = jnp.exp(m - m_new)                   # first tile: exp(-inf - ·) = 0
        p = jnp.exp(s - m_new[:, None])
        l = l * corr + jnp.sum(p, axis=-1)
        acc = acc * corr[:, None] + pl.dot(p, v)
        return m_new, l, acc

    m, l, acc = jax.lax.fori_loop(0, n_kt, body, (m, l, acc))
    o_ref[0] = (acc / l[:, None]).astype(o_ref.dtype)


def disent_flash_kernel_algebra(
    q_ref: jax.Array, c2p_full_ref: jax.Array, am_q_ref: jax.Array,
    k_ref: jax.Array, v_ref: jax.Array, p2c_full_ref: jax.Array, am_k_ref: jax.Array,
    o_ref: jax.Array,
    *, scale: float, S: Pow2, block_q: Pow2, block_k: Pow2, d: Pow2, W: Pow2, neg: float,
    position_buckets: int, max_relative_positions: int, span: int,
) -> None:
    """The lowerable-kernel-ALGEBRA port of `disent_flash_kernel` (DESIGN.md §7): each line of
    the oracle's body is one `nla_lab.lower.ops` combinator call, so the kernel is the SAME
    computation (bit-identical under interpret, proven in test_pallas_lower_algebra.py) but is
    now UNCONSTRUCTABLE in any of the four impedance modes — a gather/batched-einsum is not in
    the surface, host vs device is `Tile` vs host scalar, the `log/ceil` float->int is an
    explicit `to_i32` inside `ops.bucket_index`, and every dim is a `Pow2`.

    The carrier is non-coercible, so feeding any `Tile` to a raw `jnp`/`lax` primitive (the
    construction backstop, e.g. `jnp.einsum`) raises at trace. The refs are branded `Ref` once
    at the boundary (`ops.ref`, the device-seam crossing); the `Tile` running state is carried
    across key tiles by `ops.fold_kt` (NOT a pytree — the wrap/unwrap lives inside lower/, so a
    `Tile` is an opaque leaf and `tree_map` cannot rewrap it; see lower/tile.py)."""
    neg_inf = float("-inf")
    q_r = ops.ref(q_ref); am_q_r = ops.ref(am_q_ref)          # device-ref brands (the device seam)
    k_r = ops.ref(k_ref); v_r = ops.ref(v_ref); am_k_r = ops.ref(am_k_ref)
    c2p_r = ops.ref(c2p_full_ref); p2c_r = ops.ref(p2c_full_ref); o_r = ops.ref(o_ref)

    bh = ops.pid(0)                                   # batch*head index (0-d Idx)
    qt = ops.pid(1)                                   # query-tile index (0-d Idx)
    qi0 = ops.imul_scalar(qt, block_q)                # qi0 = qt * block_q
    two_span = 2 * span

    q = ops.load(q_r, block_q, d)                     # [block_q, d]
    am_i = ops.load(am_q_r, block_q)                  # [block_q] query mask
    arows = ops.add(ops.iota(block_q), qi0)           # qi0 + arange(block_q)

    m0 = ops.full(block_q, neg_inf)                   # running max
    l0 = ops.full(block_q, 0.0)                       # running denom
    acc0 = ops.zeros(block_q, d, F32)                 # running numerator

    n_kt = pl.cdiv(S, block_k)

    def body(
        kt: Tile[I32], m: Tile[F32], l: Tile[F32], acc: Tile[F32],
    ) -> tuple[Tile[F32], Tile[F32], Tile[F32]]:
        kj0 = ops.imul_scalar(kt, block_k)            # kj0 = kt * block_k
        k = ops.load_block(k_r, kj0, block_k)         # [block_k, d]  (already /scale)
        v = ops.load_block(v_r, kj0, block_k)         # [block_k, d]
        am_j = ops.load_block_1d(am_k_r, kj0, block_k)     # [block_k] key mask
        bcols = ops.add(ops.iota(block_k), kj0)       # kj0 + arange(block_k)

        # --- content term q · k_scaledᵀ (the ONLY contraction; 2-D pl.dot, no batch) ---
        content = ops.dot(q, ops.transpose(k))        # [block_q, block_k]

        # --- ONE bucket-index tile, used for BOTH c2p/p2c (the measured-equal collapse) ---
        d_ij = ops.sub(ops.bcast_row(arows), ops.bcast_col(bcols))   # [bq,bk] = i - j
        pos = ops.bucket_index(d_ij, position_buckets=position_buckets,
                               max_relative_positions=max_relative_positions, span=span, two_span=two_span)

        # --- BANDED select (gather-free): pl.ds band slice + one-hot comparison-sum ---
        off_min = ops.sub(qi0, ops.iadd_scalar(kj0, block_k - 1))    # qi0 - (kj0 + block_k - 1)
        b_lo = ops.bucket_index(off_min, position_buckets=position_buckets,
                                max_relative_positions=max_relative_positions, span=span, two_span=two_span)
        base = ops.clip(b_lo, 0, two_span - int(W))   # the CLAMPED band base
        c2p_band = ops.band(c2p_r, bh, qi0, block_q, base, W)   # [block_q, W] query rows
        p2c_band = ops.band(p2c_r, bh, kj0, block_k, base, W)   # [block_k, W] key rows
        sel = ops.sub(pos, base)                      # [bq,bk], provably in [0, W)
        oh = ops.onehot(sel, W)                       # [bq,bk,W] one-hot, no gather
        c2p = ops.select(c2p_band, oh, row_axis=0)    # [bq,bk] broadcast-mul + sum, NOT einsum
        p2c = ops.select(p2c_band, oh, row_axis=1)    # [bq,bk]

        # --- combined score / scale, then mask ---
        s = ops.add(content, ops.div_scalar(ops.add(c2p, p2c), scale))
        mask2d = ops.mul(ops.bcast_row(am_i), ops.bcast_col(am_j))    # [bq,bk]
        s = ops.where(ops.gt(mask2d, ops.zeros(block_q, block_k, F32)),
                      s, ops.full2(block_q, block_k, neg))

        # --- online-softmax update (running max + rescale) ---
        m_tile = ops.rmax(s, axis=-1)
        m_new = ops.where(ops.gt(m, m_tile), m, m_tile)   # maximum(m, m_tile)
        corr = ops.exp(ops.sub(m, m_new))                 # first tile: exp(-inf - ·) = 0
        p = ops.exp(ops.sub(s, ops.bcast_row(m_new)))
        l = ops.add(ops.mul(l, corr), ops.rsum(p, axis=-1))
        acc = ops.add(ops.mul(acc, ops.bcast_row(corr)), ops.dot(p, v))
        return m_new, l, acc

    m, l, acc = ops.fold_kt(n_kt, (m0, l0, acc0), body)   # online-softmax fold over key tiles
    ops.store(o_r, ops.div(acc, ops.bcast_row(l)))        # o_ref[0] = acc / l[:, None]


def pallas_disentangled_attention(
    q: jax.Array, k_scaled: jax.Array, v: jax.Array,
    c2p_full: jax.Array, p2c_full: jax.Array, am_bh: jax.Array,
    *, scale: float, block_q: Pow2, block_k: Pow2,
    position_buckets: int, max_relative_positions: int, span: int, interpret: bool,
    kernel: Callable[..., None] = disent_flash_kernel_algebra,
) -> jax.Array:
    """Fused disentangled FlashAttention over `[B*H, S, d]` activations -> context
    `[B*H, S, d]`. Builds the `BlockSpec`s and calls `pl.pallas_call`. All global memory inputs are
    O(B·H·S··): the quadratic score is never an array. `am_bh` is the `[B*H, S]` float
    attention mask (the reference's `[B,1,S,S]` mask factorizes as `am[b,i]·am[b,j]`).

    `position_buckets`/`max_relative_positions`/`span` (= `cfg.pos_ebd_size`) are the STATIC
    log-bucket parameters threaded to the kernel: it computes BOTH c2p and p2c's ONE collapsed
    column index `clip(BUCKET(i-j)+span)` and the band base `clip(BUCKET(off_min)+span)` by pure
    arithmetic (`_bucket_index`), so there is NO `idx1d` table and NO `gather`/scalar table read.
    The c2p/p2c values are then selected from a `pl.ds(base, W)` band by one-hot comparison-sum —
    no `gather` (the sm_75 Triton wall). `interpret=True` runs the kernel on CPU (guest
    correctness); `interpret=False` is the real Triton path (host).

    `kernel` selects the kernel body: the default `disent_flash_kernel_algebra` is the
    lowerable-kernel-algebra port (every op a `nla_lab.lower.ops` combinator, the four
    impedances unconstructable); `disent_flash_kernel` is the pristine oracle the algebra
    port is proven bit-identical to (test_pallas_lower_algebra.py)."""
    bh, S, d = q.shape
    # Pow2 BOUNDARY (ADR-0000): block_q/block_k arrive `Pow2` (the caller branded them). The
    # array-derived dims must ALSO be powers of 2, so brand them HERE — a non-pow2 head_dim or seq
    # raises a clear guest error at the boundary, never a cryptic Triton failure on the host. The
    # branded dims flow into every BlockSpec shape below, so the kernel cannot even be BUILT from a
    # non-pow2 dimension.
    Sp, dp = pow2(S), pow2(d)
    # Band width (ADR-0000 Pow2 boundary): the contiguous (i-j)-offset range a tile spans has
    # width block_q+block_k-1; round UP to a power of two, but never exceed `2span` (pl.ds needs
    # W <= the sliced axis). two_span = 2*pos_ebd_size is pow2, next_pow2(...) is pow2, so the
    # min is pow2 — branded here; a non-pow2 W is unconstructable, never a cryptic Triton error.
    two_span = int(c2p_full.shape[-1])
    W = pow2(min(next_pow2(int(block_q) + int(block_k) - 1), two_span))
    # jnp.finfo is untyped in jax 0.10.1's stubs (named relaxation, ADR-0012 P8).
    neg = float(jnp.finfo(jnp.float32).min)          # type: ignore[no-untyped-call]  # the reference's masked_fill value
    n_qt = pl.cdiv(Sp, block_q)

    bspec = pl.BlockSpec
    # c2p_full / p2c_full are global-memory-resident (memory_space=pl.ANY): the whole [B*H, S, 2span]
    # stays in global memory and the kernel gathers only the [block_q, block_k] entries per score-tile
    # (root cause #2 fix) — staging them as [block, 2span] SRAM tiles was 256 KB/buffer at
    # block 128, 4x Turing's whole 64 KB SMEM. The score tile is never a global-memory array (k_quad=0).
    in_specs = [
        bspec((1, block_q, dp), lambda bh_, qt: (bh_, qt, 0)),      # q (query tile)
        bspec(memory_space=pl.ANY),                                 # c2p_full (global-memory-resident, band-sliced)
        bspec((1, block_q), lambda bh_, qt: (bh_, qt)),             # am_q (query mask tile)
        bspec((1, Sp, dp), lambda bh_, qt: (bh_, 0, 0)),            # k_scaled (whole key axis)
        bspec((1, Sp, dp), lambda bh_, qt: (bh_, 0, 0)),            # v (whole key axis)
        bspec(memory_space=pl.ANY),                                 # p2c_full (global-memory-resident, band-sliced)
        bspec((1, Sp), lambda bh_, qt: (bh_, 0)),                   # am_k (whole key mask)
    ]
    out_specs = bspec((1, block_q, dp), lambda bh_, qt: (bh_, qt, 0))

    # `kernel` defaults to the lowerable-algebra port (disent_flash_kernel_algebra); the oracle
    # `disent_flash_kernel` is selectable for the bit-identity regression. Both have the same
    # signature, so the ONE partial/BlockSpec build serves either (DESIGN.md §7: same kernel).
    kfn = functools.partial(
        kernel, scale=scale, S=Sp, block_q=block_q, block_k=block_k, d=dp, W=W, neg=neg,
        position_buckets=position_buckets, max_relative_positions=max_relative_positions, span=span)
    # Pin the TRITON backend (root cause #1 fix): a `triton.CompilerParams` makes the
    # gpu_lowering dispatch `isinstance(cp, triton_core.CompilerParams)` fire Triton
    # deterministically — without it, compiler_params=None falls back to _PALLAS_USE_MOSAIC_GPU
    # (which DEFAULTS True) and lands on Mosaic-GPU (sm_90), the host's SMEM-overflow error on
    # sm_75. `interpret=True` ignores the backend entirely (CPU executor), so the guest
    # fidelity gate is unaffected; compiler_params only bites when interpret=False on the host.
    cp = plgpu.CompilerParams(num_warps=_NUM_WARPS, num_stages=_NUM_STAGES)
    # pl.pallas_call returns an untyped callable -> Any result (named relaxation, mirrors
    # exact_reference.encode's no-any-return); jax.ShapeDtypeStruct is untyped in jax 0.10.1.
    return pl.pallas_call(  # type: ignore[no-any-return]
        kfn,
        grid=(bh, n_qt),
        in_specs=in_specs,
        out_specs=out_specs,
        out_shape=jax.ShapeDtypeStruct((bh, Sp, dp), q.dtype),  # type: ignore[no-untyped-call]
        compiler_params=cp,
        interpret=interpret,
    )(q, c2p_full, am_bh, k_scaled, v, p2c_full, am_bh)
