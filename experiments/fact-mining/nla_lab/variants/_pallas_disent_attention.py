#!/usr/bin/env python
"""_pallas_disent_attention — the Pallas FLASH KERNEL for DeBERTa disentangled attention.

WHAT THIS MODULE OWNS (and ONLY this): the single fused attention seam — a tiled,
online-softmax kernel that computes the FULL 3-term disentangled score (content `q·kᵀ`
+ content->position c2p + position->content p2c) tile-by-tile and NEVER materializes the
`[B,H,S,S]` score / probability matrix. The `[block_q, block_k]` score tile lives only in
SRAM inside one `pallas_call` grid cell; the HBM traffic is the O(B·H·S·d) q/k/v/out
activations + the O(B·H·S·span) disentangled-position intermediates — never the quadratic
scores. This is the structural difference vs `flash_attention.py` (jnp-level tiling that
XLA flattens back to dense): a Pallas kernel STAYS fused.

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
tensor-core-accelerated (bf16/tf32 MMA need sm_80+); the IO-fusion win (no `[B,H,S,S]` HBM
round-trip) still holds and is the point. The in-tile `jnp.take_along_axis` gather is the
primary; if it does not lower on Triton the host fallback is a `plgpu.load` HBM-offset
pointer-gather (same algebra) — recorded, host-gate-selected.

HOST-XOR-DEVICE. Neutrally named (no device token) and DEVICE-ONLY: imports jax + pallas,
NEVER numpy (`jnp.finfo`, not `np.finfo`). The XOR-gate stays green.
"""

from __future__ import annotations

import functools

import jax
import jax.numpy as jnp
from jax.experimental import pallas as pl


# Pallas kernel refs are SRAM-resident handles that index array-like (`ref[...]` -> jax.Array);
# jax 0.10.1's pallas exports no public `Ref` type, so they are annotated `jax.Array` — a NAMED
# relaxation (the ref indexes/assigns exactly as an array does here), not a precision loss.
def disent_flash_kernel(
    q_ref: jax.Array, c2p_full_ref: jax.Array, am_q_ref: jax.Array, idx1d_ref: jax.Array,  # resident over the query tile
    k_ref: jax.Array, v_ref: jax.Array, p2c_full_ref: jax.Array, am_k_ref: jax.Array,      # whole key axis (sliced per k-tile)
    o_ref: jax.Array,                                 # output context tile
    *, scale: float, S: int, block_q: int, block_k: int, neg: float,
) -> None:
    """Online-softmax disentangled attention for ONE (bh, query-tile) grid cell.

    Grid is `(B*H, num_q_tiles)`; `program_id(1)` selects the query tile. The inner
    `fori_loop` walks key tiles, recomputing each `[block_q, block_k]` score tile (content
    + c2p + p2c) in SRAM and folding it into the running (max, denom, numerator) — the
    `[B,H,S,S]` score is never formed. EXACT vs `jax_deberta._self_attention`: same
    per-element score, only the softmax reduction order differs."""
    qt = pl.program_id(1)
    qi0 = qt * block_q

    q = q_ref[0]                       # [block_q, d]  (content query rows)
    c2p_blk = c2p_full_ref[0]          # [block_q, 2span]  (c2p source rows = queries i)
    am_i = am_q_ref[0]                 # [block_q]  (query mask)
    idx1d = idx1d_ref[...]             # [2S-1]  the ONE O(S) bucket table (c2p & p2c)
    arows = qi0 + jnp.arange(block_q)  # global query ids for this tile
    d = q.shape[-1]

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
        p2c_blk = p2c_full_ref[0, ks, :]   # [block_k, 2span]  (p2c source rows = keys j)
        am_j = am_k_ref[0, ks]        # [block_k]  (key mask)
        bcols = kj0 + jnp.arange(block_k)  # global key ids

        # --- content term (fp32 -> FMA on sm_75; exact). q · k_scaledᵀ ---
        content = pl.dot(q, k.T)      # [block_q, block_k]

        # --- ONE bucket-index tile, used for BOTH terms (MEASURED-equal collapse) ---
        d_ij = arows[:, None] - bcols[None, :]      # [block_q, block_k] = i - j
        pos = idx1d[d_ij + (S - 1)]                 # [block_q, block_k] int = clip(bucket(i-j)+span)

        # c2p: gather c2p_blk[i, pos[i,j]] along the 2span axis (row = query i)
        c2p = jnp.take_along_axis(c2p_blk, pos, axis=1)        # [block_q, block_k]
        # p2c: gather p2c_blk[j, pos[i,j]] (row = key j) -> need [block_k, block_q] idx = pos.T
        p2c = jnp.take_along_axis(p2c_blk, pos.T, axis=1).T    # [block_q, block_k]

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
    *, scale: float, block_q: int, block_k: int, interpret: bool,
) -> jax.Array:
    """Fused disentangled FlashAttention over `[B*H, S, d]` activations -> context
    `[B*H, S, d]`. Builds the `BlockSpec`s and calls `pl.pallas_call`. All HBM inputs are
    O(B·H·S··): the quadratic score is never an array. `am_bh` is the `[B*H, S]` float
    attention mask (the reference's `[B,1,S,S]` mask factorizes as `am[b,i]·am[b,j]`).

    `idx1d` is the single O(S) bucket table (length `2S-1`); it is passed once and gathered
    in-kernel for BOTH c2p and p2c (the MEASURED index collapse). `interpret=True` runs the
    kernel on CPU (guest correctness); `interpret=False` is the real Triton path (host)."""
    bh, S, d = q.shape
    span2 = c2p_full.shape[-1]                       # 2 * pos_ebd_size
    # jnp.finfo is untyped in jax 0.10.1's stubs (named relaxation, ADR-0012 P8).
    neg = float(jnp.finfo(jnp.float32).min)          # type: ignore[no-untyped-call]  # the reference's masked_fill value
    n_qt = pl.cdiv(S, block_q)

    bspec = pl.BlockSpec
    in_specs = [
        bspec((1, block_q, d), lambda bh_, qt: (bh_, qt, 0)),       # q (query tile)
        bspec((1, block_q, span2), lambda bh_, qt: (bh_, qt, 0)),   # c2p_full (query rows)
        bspec((1, block_q), lambda bh_, qt: (bh_, qt)),             # am_q (query mask tile)
        bspec((2 * S - 1,), lambda bh_, qt: (0,)),                  # idx1d (whole, O(S))
        bspec((1, S, d), lambda bh_, qt: (bh_, 0, 0)),              # k_scaled (whole key axis)
        bspec((1, S, d), lambda bh_, qt: (bh_, 0, 0)),              # v (whole key axis)
        bspec((1, S, span2), lambda bh_, qt: (bh_, 0, 0)),         # p2c_full (whole key axis)
        bspec((1, S), lambda bh_, qt: (bh_, 0)),                    # am_k (whole key mask)
    ]
    out_specs = bspec((1, block_q, d), lambda bh_, qt: (bh_, qt, 0))

    kernel = functools.partial(
        disent_flash_kernel, scale=scale, S=S, block_q=block_q, block_k=block_k, neg=neg)
    # pl.pallas_call returns an untyped callable -> Any result (named relaxation, mirrors
    # exact_reference.encode's no-any-return); jax.ShapeDtypeStruct is untyped in jax 0.10.1.
    return pl.pallas_call(  # type: ignore[no-any-return]
        kernel,
        grid=(bh, n_qt),
        in_specs=in_specs,
        out_specs=out_specs,
        out_shape=jax.ShapeDtypeStruct((bh, S, d), q.dtype),  # type: ignore[no-untyped-call]
        interpret=interpret,
    )(q, c2p_full, am_bh, idx1d, k_scaled, v, p2c_full, am_bh)
