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

THE ONE O(S) BUCKET TABLE (MEASURED collapse). Because `make_log_bucket_position` is
antisymmetric, the dense c2p column index `clip(bucket(i-j)+span)` and the dense p2c
column index `clip(-bucket(j-i)+span)` are PROVABLY EQUAL — verified bit-equal over all
S² elements (S up to 1024) on the guest. So the kernel carries a SINGLE strict-O(S) index
array `idx1d[d] = clip(bucket(d)+span)` for `d in [-(S-1), S-1]`, gathered in-tile at
`idx1d[(i-j)+(S-1)]`; c2p and p2c differ ONLY in which buffer/row they gather (c2p_full
row i vs p2c_full row j), not in the column index. No `[S,S]` table, no two tables.

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
memory_space=pl.ANY`) and the kernel GATHERS only the `[block_q, block_k]` entries each
score-tile needs (`c2p_full[bh, i, pos]`, `p2c_full[bh, j, pos]`) — so the broken
`[block, 2span]` SRAM staging (256 KB/buffer at block 128) is gone. (3) `smem_bytes()` is
the guest-provable budget gate: it makes "tiles exceed SMEM" a CAUGHT arithmetic error
(chosen tiles block 32 -> 45312 B <= 48 KiB), not a host `ValueError`. The global memory gather is the
shipped primary; the banded-`2span`-slice is the recorded host-gate fallback if the
per-element gather does not lower on Triton.

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
            f"power of 2 2S): pad to 2S BEFORE the kernel (see _build_idx1d).")
    return Pow2(n)


def smem_bytes(
    block_q: Pow2,
    block_k: Pow2,
    d: Pow2,
    *,
    dtype_bytes: int = 4,
    num_stages: int = 1,
    pos_resident_2span: int = 0,
) -> int:
    """Conservative peak SMEM-resident bytes for ONE `disent_flash_kernel` grid cell.

    Pure-Python int arithmetic (no jax, no numpy) so it is host-XOR-device clean and the
    guest can ASSERT it. Counts `q + k + v + score + acc + m + l + position-scratch` as
    co-resident — an UPPER bound: when this passes, the tiles provably fit Turing's SMEM.

    `pos_resident_2span` selects the residence model: 0 (the SHIPPED fix) is the per-tile
    global memory gather, whose position scratch is the `2*block_q*block_k` c2p+p2c gather RESULTS
    (the source `[B*H,S,2span]` buffers stay in global memory, never staged); a positive `span`
    reproduces the BROKEN `[block, 2span]` SRAM staging for the regression assertion.
    `num_stages` double-buffers the per-k-tile loaded operands (k, v, score, position)."""
    persistent = block_q * d + block_q * d + 2 * block_q          # q, acc, m + l
    if pos_resident_2span > 0:
        pos = 2 * block_q * (2 * pos_resident_2span)              # broken: [block, 2span] x2
    else:
        pos = 2 * block_q * block_k                               # fix: [block_q, block_k] gathers
    pipelined = block_k * d + block_k * d + block_q * block_k + pos   # k, v, score, position
    return (persistent + num_stages * pipelined) * dtype_bytes


# Pallas kernel refs are SRAM-resident handles that index array-like (`ref[...]` -> jax.Array);
# jax 0.10.1's pallas exports no public `Ref` type, so they are annotated `jax.Array` — a NAMED
# relaxation (the ref indexes/assigns exactly as an array does here), not a precision loss.
def disent_flash_kernel(
    q_ref: jax.Array, c2p_full_ref: jax.Array, am_q_ref: jax.Array, idx1d_ref: jax.Array,  # c2p_full global-memory-resident (pl.ANY); q/am resident over the query tile
    k_ref: jax.Array, v_ref: jax.Array, p2c_full_ref: jax.Array, am_k_ref: jax.Array,      # p2c_full global-memory-resident (pl.ANY); k/v/am whole key axis (sliced per k-tile)
    o_ref: jax.Array,                                 # output context tile
    *, scale: float, S: Pow2, block_q: Pow2, block_k: Pow2, neg: float,
) -> None:
    """Online-softmax disentangled attention for ONE (bh, query-tile) grid cell.

    Grid is `(B*H, num_q_tiles)`; `program_id(1)` selects the query tile. The inner
    `fori_loop` walks key tiles, recomputing each `[block_q, block_k]` score tile (content
    + c2p + p2c) in SRAM and folding it into the running (max, denom, numerator) — the
    `[B,H,S,S]` score is never formed. EXACT vs `jax_deberta._self_attention`: same
    per-element score, only the softmax reduction order differs."""
    bh = pl.program_id(0)              # batch*head index, to address the global-memory-resident position buffers
    qt = pl.program_id(1)
    qi0 = qt * block_q

    q = q_ref[0]                       # [block_q, d]  (content query rows)
    am_i = am_q_ref[0]                 # [block_q]  (query mask)
    idx1d = idx1d_ref[...]             # [2S-1]  the ONE O(S) bucket table (c2p & p2c)
    arows = qi0 + jnp.arange(block_q)  # global query ids for this tile
    d = q.shape[-1]
    # c2p_full_ref / p2c_full_ref are NOT staged into SRAM (BlockSpec memory_space=pl.ANY):
    # the whole [B*H, S, 2span] stays global-memory-resident and is GATHERED per score-tile element
    # in `body`, so no [block, 2span] buffer ever lives in Turing's 64 KB SMEM (root cause #2).

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
        pos = idx1d[d_ij + (S - 1)]                 # [block_q, block_k] int = clip(bucket(i-j)+span)

        # global-memory-resident position gather (no [block, 2span] in SRAM): pull only the
        # [block_q, block_k] entries this tile needs from the pl.ANY buffers — row = the
        # global query/key id, col = the ONE collapsed bucket index `pos`. The gathered
        # VALUES and their fold are bit-identical to the staged `take_along_axis`; ONLY the
        # source residence (global memory vs SMEM) changes, so the EXACT ~1e-5 fold is untouched.
        # (p2c needs NO transpose here: indexing row j directly yields [block_q, block_k].)
        i_idx = arows[:, None] + jnp.zeros_like(pos)          # [block_q, block_k] query rows i
        j_idx = bcols[None, :] + jnp.zeros_like(pos)          # [block_q, block_k] key rows j
        c2p = c2p_full_ref[bh, i_idx, pos]                    # c2p_full[bh, i, pos[i,j]]
        p2c = p2c_full_ref[bh, j_idx, pos]                    # p2c_full[bh, j, pos[i,j]]

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
    c2p_full: jax.Array, p2c_full: jax.Array, idx1d: jax.Array, am_bh: jax.Array,
    *, scale: float, block_q: Pow2, block_k: Pow2, interpret: bool,
) -> jax.Array:
    """Fused disentangled FlashAttention over `[B*H, S, d]` activations -> context
    `[B*H, S, d]`. Builds the `BlockSpec`s and calls `pl.pallas_call`. All global memory inputs are
    O(B·H·S··): the quadratic score is never an array. `am_bh` is the `[B*H, S]` float
    attention mask (the reference's `[B,1,S,S]` mask factorizes as `am[b,i]·am[b,j]`).

    `idx1d` is the single O(S) bucket table (length `2S`, padded from the natural `2S-1` to a
    power of 2 — Triton requires it; the pad slot is inert, see _build_idx1d); it is passed once
    and gathered in-kernel for BOTH c2p and p2c (the MEASURED index collapse). `interpret=True` runs the
    kernel on CPU (guest correctness); `interpret=False` is the real Triton path (host)."""
    bh, S, d = q.shape
    # Pow2 BOUNDARY (ADR-0000): block_q/block_k arrive `Pow2` (the caller branded them). The
    # array-derived dims must ALSO be powers of 2, so brand them HERE — a non-pow2 head_dim, seq,
    # or idx1d length (the 2S-1 trap) raises a clear guest error at the boundary, never a cryptic
    # Triton failure on the host. The branded dims flow into every BlockSpec shape below, so the
    # kernel cannot even be BUILT from a non-pow2 dimension.
    Sp, dp, idx_len = pow2(S), pow2(d), pow2(idx1d.shape[0])
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
        bspec(memory_space=pl.ANY),                                 # c2p_full (global-memory-resident, gathered)
        bspec((1, block_q), lambda bh_, qt: (bh_, qt)),             # am_q (query mask tile)
        bspec((idx_len,), lambda bh_, qt: (0,)),                    # idx1d (whole, O(S); idx_len = 2S, pow2)
        bspec((1, Sp, dp), lambda bh_, qt: (bh_, 0, 0)),            # k_scaled (whole key axis)
        bspec((1, Sp, dp), lambda bh_, qt: (bh_, 0, 0)),            # v (whole key axis)
        bspec(memory_space=pl.ANY),                                 # p2c_full (global-memory-resident, gathered)
        bspec((1, Sp), lambda bh_, qt: (bh_, 0)),                   # am_k (whole key mask)
    ]
    out_specs = bspec((1, block_q, dp), lambda bh_, qt: (bh_, qt, 0))

    kernel = functools.partial(
        disent_flash_kernel, scale=scale, S=Sp, block_q=block_q, block_k=block_k, neg=neg)
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
    )(q, c2p_full, am_bh, idx1d, k_scaled, v, p2c_full, am_bh)
