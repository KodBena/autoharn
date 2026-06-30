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
from typing import NewType

import jax
import jax.numpy as jnp
from jax.experimental import pallas as pl
from jax.experimental.pallas import triton as plgpu

import jax_deberta  # SSOT of the log-bucket arithmetic (make_log_bucket_position); device-only (no numpy)


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
# The Pallas-Triton lowering REJECTS any array shape that is not a power of 2 ("requires that all
# operations have array arguments and results whose size is a power of 2"). The bug that shipped:
# the relative-offset count 2S-1 — exactly ONE below the power of 2 2S — flowed unguarded into the
# kernel, and interpret mode (CPU) does not enforce the rule, so it only detonated on the host.
# Rather than CHECK the invariant at runtime, we make a non-pow2 kernel dimension UNCONSTRUCTABLE:
# `Pow2` is a NewType whose ONLY source is `pow2()`, which validates. So (a) mypy rejects a raw int
# where a kernel signature wants a `Pow2`, and (b) `pow2()` rejects a non-pow2 VALUE at the kernel
# boundary with a clear guest-side error. 2S-1 cannot become a `Pow2`; it cannot reach Triton.
Pow2 = NewType("Pow2", int)


def pow2(n: int) -> Pow2:
    """The single source of `Pow2` values — brand `n` as a power of two, or raise. A `Pow2`
    carries the proof; downstream code uses it as a plain int (NewType), but a non-pow2 (e.g.
    2S-1 = 127) cannot get past this constructor."""
    if n <= 0 or (n & (n - 1)) != 0:
        raise ValueError(
            f"kernel dimension {n} is not a power of 2 — Pallas-Triton requires every array shape "
            f"be a power of 2. The classic trap is the relative-offset count 2S-1 (one below the "
            f"power of 2 2S): every kernel array dim (block_q/block_k/S/d/W) must be a true pow2.")
    return Pow2(n)


def next_pow2(n: int) -> int:
    """Smallest power of two `>= n` (for `n >= 1`). Used to size the band width `W` from the
    offset-range width `block_q + block_k - 1`: the (i-j) offsets a (qt,kt) tile spans are a
    contiguous range of that width, so the bucket-column range it can reference fits a single
    `pl.ds(base, W)` slice once `W` is rounded UP to a power of two (Triton's shape rule —
    branded `Pow2` at the kernel boundary, never raw)."""
    return 1 << (n - 1).bit_length()


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
    *, scale: float, S: Pow2, block_q: Pow2, block_k: Pow2, W: Pow2, neg: float,
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
    d = q.shape[-1]
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
        # gather(band[row, sel]) as a one-hot contraction over the band's W axis (Triton-safe).
        sel = pos - base                                      # [block_q, block_k], provably in [0, W)
        onehot = (jnp.arange(W)[None, None, :] == sel[:, :, None]).astype(jnp.float32)  # [bq,bk,W]
        c2p = jnp.einsum("iw,ijw->ij", c2p_band, onehot)      # c2p_band rows = query i
        p2c = jnp.einsum("jw,ijw->ij", p2c_band, onehot)      # p2c_band rows = key   j

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


def pallas_disentangled_attention(
    q: jax.Array, k_scaled: jax.Array, v: jax.Array,
    c2p_full: jax.Array, p2c_full: jax.Array, am_bh: jax.Array,
    *, scale: float, block_q: Pow2, block_k: Pow2,
    position_buckets: int, max_relative_positions: int, span: int, interpret: bool,
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
    correctness); `interpret=False` is the real Triton path (host)."""
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

    kernel = functools.partial(
        disent_flash_kernel, scale=scale, S=Sp, block_q=block_q, block_k=block_k, W=W, neg=neg,
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
        kernel,
        grid=(bh, n_qt),
        in_specs=in_specs,
        out_specs=out_specs,
        out_shape=jax.ShapeDtypeStruct((bh, Sp, dp), q.dtype),  # type: ignore[no-untyped-call]
        compiler_params=cp,
        interpret=interpret,
    )(q, c2p_full, am_bh, k_scaled, v, p2c_full, am_bh)
