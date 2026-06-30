# Pallas FlashAttention for DeBERTa disentangled attention — design

Status: design, with a guest-provable correctness path and an explicit host-only
feasibility gate. Authored against ADR-0000 (the kernel is correct *by construction*
against the dense reference; the `est_peak_device_bytes` override reflects the TRUE
O(S) peak, not a fiction), ADR-0009 (flash is EXACT — fidelity ~1e-5 is a MEASURED
claim; the memory drop is a derived/MEASURED claim; guest-provable vs host-only is
split honestly), and ADR-0012 P1 (reuse `jax_deberta` for everything except the one
attention seam this kernel replaces).

## 0. The problem this kernel exists to solve, restated precisely

The dense disentangled self-attention (`jax_deberta._self_attention` +
`_disentangled_bias`) materialises several `[B, H, S, S]` float32 tensors per layer
(content `q·kᵀ`, the gathered c2p scores, the gathered+transposed p2c scores, the
score accumulator, the masked-fill, the softmax probs). At `B=16, H=16, S=1024` one
such buffer is `16·16·1024·1024·4 = 1.07 GB`; the conservative co-residency model
(`shape_buckets._K_QUAD=8`) bounds the live set at `8·1.07 = 8.6 GB`, and the whole
dense forward at `peak_variable_bytes(mm, 16, 1024) = 12.08 GB` — past the 2080Ti's
~11 GB usable arena. That cell **OOMs**.

The existing `nla_lab/variants/flash_attention.py` is the *correct* online-softmax
math at jnp level — but XLA **flattens its Python tile loop back to dense** (proven:
its latency was bit-identical to dense and its small-S memory was *worse*). XLA fuses
each tile's `q @ k_tileᵀ` and the online update, but it does not promise to keep the
`[B,H,S,S]` materialization from re-forming across the whole loop; the tiling is a
hint XLA is free to ignore, and it does.

A **Pallas kernel stays fused**: the `[block_q, block_k]` score tile lives in SRAM
inside one `pallas_call` grid cell and is *never* written to HBM as part of an
`[B,H,S,S]` array. The HBM traffic is the O(B·H·S·d) q/k/v/out activations plus the
O(B·H·S·2·span) disentangled-position intermediates — never the quadratic scores.

The payoff is the **feasibility frontier**, not a small-S latency win (a small
`[S,S]` is not IO-bound — be honest). The win is: (a) large-S **memory/feasibility**
— the OOM cells run; and (b) the IO **wall-clock** win at long S (the score tile
never round-trips HBM). This is the avenue being **exhausted**: if Pallas-on-Turing
genuinely cannot deliver, §1 states the fallback ladder and the conditions under
which that becomes a *measured* feasibility verdict, not a hand-wave.

## 1. FEASIBILITY — Pallas GPU (Triton backend) on Turing sm_75 (the 2080Ti)

**What is installed (guest, MEASURED here):** `jax 0.10.1`, `jaxlib 0.10.1`,
`default_backend()=='cpu'`. `jax.experimental.pallas` imports; the GPU lowering
module `jax.experimental.pallas.triton` (`plgpu`) imports; the reference kernel
`jax.experimental.pallas.ops.gpu.attention` imports and uses
`plgpu.TritonCompilerParams(num_warps=, num_stages=)`. `pl.pallas_call(...,
interpret=True)` runs on the CPU guest (verified: an `add_one` kernel and a
`BlockSpec`/`pl.dslice` load both execute). `triton` is **not** a standalone module
in the guest venv — expected: the CPU jaxlib carries no GPU lowering runtime; the
**CUDA** jaxlib bundles its own Triton. So **nothing GPU runs on the guest**; the
guest's job is interpret-mode correctness only.

**Pallas GPU → Triton → Turing.** Pallas's GPU path lowers to Triton IR. Triton
supports CUDA compute capability **≥ 7.0** (Volta); Turing **sm_75** is inside that
range, and Triton FlashAttention on a 2080Ti is a widely-run configuration. The
non-obvious constraint is the **tensor-core `tl.dot` dtype gate**, which is
hardware-tiered:

- sm_75 (Turing) tensor cores are **fp16 / int8 only**. **bf16 and tf32 MMA require
  sm_80+** (Ampere). 
- DeBERTa encode is **pinned fp32** (`shape_buckets._BYTES_PER_ELEM=4`, "the encode
  is pinned fp32"). An fp32 `pl.dot` on Turing therefore lowers to the **FMA
  (CUDA-core) path** — *correct and EXACT, but not tensor-core-accelerated.* The
  IO-fusion win (no `[B,H,S,S]` HBM round-trip) **still holds and is the point**;
  the compute is FMA-bound, modestly slower than a tensor-core matmul but exact.
- Casting the matmul inputs to fp16 with fp32 accumulation
  (`preferred_element_type=jnp.float32`) *would* engage Turing tensor cores, but
  fp16 inputs carry ~1e-3 error → that **breaks the ~1e-5 EXACT tolerance** and
  drops the variant to the `AGGREGATE_BEHAVIORAL` tier. That is a **separate**
  portfolio entry (a throughput-lane fp16 flash), not this exact-tier kernel.

**Verdict and its honesty boundary (ADR-0009 guest-provable vs host-only).** The
*correctness* of the kernel is guest-provable now (interpret mode, §3). Whether
Pallas-Triton actually **compiles and runs the fp32 kernel on sm_75** is **not**
guest-provable — the guest has no CUDA jaxlib. It is a **HOST gate**: on the 2080Ti
box, `pip install -U "jax[cuda12]"`, set `interpret=False`, run the
interpret-validated kernel, and confirm (i) it compiles, (ii) it matches the dense
reference to ~1e-5, (iii) the previously-OOM cell runs. **Do not claim the GPU
compile/run works until that gate is green** — it is asserted here as a *plan*, not
a result.

**If the host gate fails — the fallback ladder (so a failure is a MEASURED verdict,
not abandonment):**

1. **fp32 `pl.dot` won't lower on sm_75 via Pallas-Triton.** Drop to a hand-written
   Triton kernel bound through `jax_triton.triton_call`. Triton itself targets
   sm_75; this removes the Pallas lowering layer as the suspect while keeping the
   exact same tiling/online-softmax/fold math. The kernel source is the same algebra
   as §2.
2. **Mosaic-GPU backend?** Ruled out by evidence:
   `jax.experimental.pallas.mosaic_gpu` is **Hopper-only (sm_90)** — not available on
   Turing. Explicitly *not* a fallback here.
3. **Last resort — `lax.scan` fused tiling with input donation.** Keep the kernel in
   pure jnp/`lax.scan` over key tiles with `donate_argnums` and `jax.checkpoint`,
   accepting that XLA may *partially* flatten (the known failure of the current jnp
   flash). This is the floor; if even (1) fails, the honest written conclusion is
   *"Pallas/Triton cannot deliver a fused fp32 disentangled-flash kernel on Turing;
   here is the compile error / the measured re-materialization,"* with the artifact
   attached — a feasibility verdict with evidence, per the standard.

The avenue is exhausted in this order; each rung's failure is recorded with its
compile error or its measured memory trace, never inferred.

## 2. Kernel STRUCTURE — tiling, online softmax, and the c2p/p2c fold

### 2.1 The dense reference the kernel must reproduce, element for element

For batch·head index `bh`, query `i`, key `j` (scale `= sqrt(head_size·scale_factor)`,
common to all three terms; `span = cfg.pos_ebd_size`, rel-pos table
`rel_pos[i,j] = make_log_bucket_position(i−j)`):

```
content[i,j] = (q[i] · k[j]) / scale
c2p[i,j]     = c2p_full[bh, i, c2p_pos[i,j]] / scale ,  c2p_pos[i,j] = clip(rel_pos[i,j]+span, 0, 2span−1)
p2c[i,j]     = p2c_full[bh, j, p2c_pos[j,i]] / scale ,  p2c_pos[j,i] = clip(−rel_pos[j,i]+span, 0, 2span−1)
score[i,j]   = content + c2p + p2c , then masked_fill(¬(am[b,i]·am[b,j]), neg)
out[bh,i,:]  = softmax_j(score[i,:]) · v
```

where (the SAME buffers the reference and the jnp flash build — O(B·H·S·span), NOT
quadratic):

```
c2p_full[bh,i,r] = q[bh,i] · pos_key[bh,r]    # [B*H, S, 2span]
p2c_full[bh,j,r] = k[bh,j] · pos_query[bh,r]  # [B*H, S, 2span]
pos_query, pos_key = transpose_for_scores(linear(rel_emb_slice, {query,key}_proj))  # share_att_key=True
```

This is exactly `jax_deberta._disentangled_bias` and `flash_attention._flash_attention`'s
fold; the kernel **moves that math inside the tile loop**, it does not re-derive it.

### 2.2 What is precomputed outside the kernel (input-independent given S; memoized on `self`)

Per ADR-0012 P1 the kernel owns **only** the tiled score+softmax+context seam.
Everything below is the un-forked `jax_deberta` helpers, computed once per
`(layer, cfg, S)` and (per the contract's PREP-MEMOIZATION note) cached on the
variant instance so the warmup forward amortizes it out of the timed window:

- `q, k, v = transpose_for_scores(linear(hidden, {q,k,v}_proj))` → `[B*H, S, d]`
  (jax_deberta `_linear`, `_transpose_for_scores`). **k is pre-scaled**:
  `k_scaled = k / scale` — mirroring `flash_attention.py`'s already-MEASURED-~1e-5
  reduction order (content uses `k_scaled`; c2p/p2c divide by scale in-kernel).
- `pos_query, pos_key`, then `c2p_full = q @ pos_keyᵀ`, `p2c_full = k @ pos_queryᵀ`
  → two `[B*H, S, 2span]` buffers (the `k_disent` term).
- **Index table, ONE strict-O(S) array (MEASURED collapse).** Build `rel1d[d] =
  make_log_bucket_position(d)` for `d ∈ [−(S−1), S−1]` (one call to the *un-forked*
  `jax_deberta.make_log_bucket_position` on the 1-D relative-offset arange — SSOT
  reuse, not a re-author), then `idx1d[d] = clip(rel1d[d]+span, 0, 2span−1)`, int32
  length `2S−1`. In-kernel **both** the c2p and the p2c gather use this *same* table
  at offset `(i−j)+(S−1)`. This is not an approximation: the dense c2p index
  `clip(rel_pos[i,j]+span)` and the dense p2c index `clip(−rel_pos[j,i]+span)` are
  **provably equal** (because `make_log_bucket_position` is antisymmetric,
  `bucket(j−i) = −bucket(i−j)`), and the collapse is **MEASURED** equal over all
  `S²=1,048,576` elements at S=1024 (`c2p_pos == p2c_pos[j,i]` and the 1-D table
  reproduces both). c2p and p2c differ only in *which buffer/row* they gather
  (`c2p_full` row `i` vs `p2c_full` row `j`), not in the column index. Index memory
  is **O(S)** (`(2S−1)·4` ≈ 8 KB at S=1024); the naive `[S,S]` table (`S²·4` ≈ 4 MB,
  B/H-free) is the trivially-correct interpret-mode debug equivalent.

These arrays (`q`, `k_scaled`, `v`, `c2p_full`, `p2c_full`, `idx1d`, `am`) are the
kernel's HBM inputs.

### 2.3 Grid and BlockSpec

Grid `= (B*H, num_q_tiles)`, `num_q_tiles = ceil(S/block_q)`. `program_id(0)=bh`,
`program_id(1)=qt`. Defaults `block_q=block_k=128` (the reference default; powers of
two that divide the power-of-two `ENCODE_LEN_BUCKETS` rungs; a ragged final tile is
handled by `pl.dslice`+masking, exactly as `mha_forward_kernel` does for `head_dim`).

| kernel input            | shape `[B*H,S,·]` (or 1-D) | BlockSpec block            | index_map     | role |
|—|—|—|—|—|
| `q`                     | `[B*H, S, d]`              | `[1, block_q, d]`           | `(bh, qt, 0)` | query tile, resident |
| `c2p_full`              | `[B*H, S, 2span]`         | `[1, block_q, 2span]`       | `(bh, qt, 0)` | c2p source rows, resident |
| `am_q`                  | `[B*H, S]`                | `[1, block_q]`              | `(bh, qt)`    | query mask, resident |
| `k_scaled`              | `[B*H, S, d]`             | `[1, S, d]` (whole key axis)| `(bh, 0, 0)`  | sliced per inner k-tile |
| `v`                     | `[B*H, S, d]`             | `[1, S, d]`                 | `(bh, 0, 0)`  | sliced per inner k-tile |
| `p2c_full`              | `[B*H, S, 2span]`         | `[1, S, 2span]`             | `(bh, 0, 0)`  | p2c source rows (keys), sliced |
| `am_k`                  | `[B*H, S]`                | `[1, S]`                     | `(bh, 0)`     | key mask, sliced |
| `idx1d`                 | `[2S−1]`                  | whole (small)               | —             | one bucket table, both terms |
| `out` (output)          | `[B*H, S, d]`            | `[1, block_q, d]`           | `(bh, qt, 0)` | context tile |

The inner key loop is a `lax.fori_loop` **inside** the kernel (like the reference),
so `k/v/p2c_full/am_k` are passed whole-S-per-`bh` and sliced with
`pl.dslice(kt*block_k, block_k)`; the quadratic axis is never a grid dim and never an
HBM array.

### 2.4 The kernel body (online softmax with the 3-term fold)

```python
def disent_flash_kernel(q_ref, c2p_full_ref, am_q_ref,        # resident (query tile)
                        k_ref, v_ref, p2c_full_ref, am_k_ref,  # sliced per k-tile
                        idx1d_ref,                             # ONE O(S) bucket table (c2p & p2c)
                        o_ref, *, scale, span, S, block_q, block_k, neg):
    qt   = pl.program_id(1)
    qi0  = qt * block_q
    q    = q_ref[0]                       # [block_q, d]
    c2p_blk = c2p_full_ref[0]            # [block_q, 2span]   (c2p source rows for this q-tile)
    am_i = am_q_ref[0]                   # [block_q]
    arows = qi0 + jnp.arange(block_q)    # global query ids

    m   = jnp.full((block_q,), -jnp.inf, jnp.float32)   # running max
    l   = jnp.zeros((block_q,), jnp.float32)            # running denom
    acc = jnp.zeros((block_q, q.shape[-1]), jnp.float32)# running numerator

    n_kt = pl.cdiv(S, block_k)
    def body(kt, carry):
        m, l, acc = carry
        kj0   = kt * block_k
        ks    = pl.dslice(kj0, block_k)
        k     = k_ref[0, ks, :]                  # [block_k, d]  (already /scale)
        v     = v_ref[0, ks, :]                  # [block_k, d]
        p2c_blk = p2c_full_ref[0, ks, :]         # [block_k, 2span] (p2c source rows = keys)
        am_j  = am_k_ref[0, ks]                  # [block_k]
        bcols = kj0 + jnp.arange(block_k)        # global key ids

        # --- content (FMA fp32 on Turing; exact) ---
        content = pl.dot(q, k.T)                 # [block_q, block_k]  == q·k_scaledᵀ

        # --- ONE bucket-index tile, used for BOTH terms (MEASURED-equal collapse, §2.2) ---
        d_ij = arows[:, None] - bcols[None, :]              # [block_q, block_k] = i-j
        pos  = idx1d_ref[d_ij + (S - 1)]                    # [block_q, block_k] int32 = clip(bucket(i-j)+span)

        # c2p: gather c2p_blk[a, pos[a,b]] along the 2span axis (row = query i)
        c2p = jnp.take_along_axis(c2p_blk, pos, axis=1)     # [block_q, block_k]

        # p2c: gather p2c_blk[b, pos[a,b]] (row = key j); take_along_axis on p2c_blk[block_k,2span]
        #      needs a [block_k, block_q] index -> use pos.T, gather, transpose back.
        p2c = jnp.take_along_axis(p2c_blk, pos.T, axis=1).T # [block_q, block_k]

        # --- combined score / scale, then mask ---
        s = (content + (c2p + p2c) / scale)                 # content already /scale via k_scaled
        s = jnp.where((am_i[:, None] * am_j[None, :]) > 0, s, neg)

        # --- online-softmax update (running max + rescale) ---
        m_tile = jnp.max(s, axis=-1)
        m_new  = jnp.maximum(m, m_tile)
        corr   = jnp.exp(m - m_new)                         # first tile: exp(-inf)=0
        p      = jnp.exp(s - m_new[:, None])
        l      = l * corr + jnp.sum(p, axis=-1)
        acc    = acc * corr[:, None] + pl.dot(p, v)
        return m_new, l, acc

    m, l, acc = lax.fori_loop(0, n_kt, body, (m, l, acc))
    o_ref[0] = (acc / l[:, None]).astype(o_ref.dtype)
```

Notes that make this **exact**, not approximate:

- The c2p/p2c are folded into `s` **before** `max/exp/rescale` — the single thing a
  plain flash kernel lacks. The fold reproduces `_disentangled_bias` term-for-term:
  `c2p_idx1d`/`p2c_idx1d` come from the un-forked `make_log_bucket_position`; the
  `clip` is the reference's; the `/scale` and the `k_scaled` placement mirror the
  already-~1e-5-MEASURED `flash_attention.py`.
- `take_along_axis` along the in-SRAM `2span` axis is the primary gather. **If it
  does not lower on Pallas-Triton** (a host-gate risk — Triton in-register gather is
  `tl.gather`, recent), the drop-in is an **HBM-offset load**: `plgpu.load` of
  `c2p_full[bh]` at offsets `(qi0+a)*2span + pos[a,b]` (and `p2c_full[bh]` at
  `(kj0+b)*2span + pos[a,b]`) — a standard Triton pointer-gather of
  `block_q·block_k` elements, exact, no re-materialization. Both are recorded; the
  host gate picks the one that lowers.
- `pl.dot` is fp32 (FMA on sm_75). The base-2 `exp2` trick the reference uses
  (`qk_scale=log2(e)`) is an *optional* host perf tuning gated by re-MEASURING
  fidelity; the exact path uses natural `jnp.exp` to match the dense reduction.
- Only one layer's attention is live at a time (layers run sequentially), so nothing
  here multiplies by `num_layers`.

### 2.5 Interpret/real switch

The variant selects `interpret = (jax.default_backend() != 'gpu')`. On the guest
(CPU) → `interpret=True` (correctness). On the 2080Ti with a CUDA jaxlib → `False`
(real Triton). One flag, no forked code path.

## 3. Fidelity strategy (interpret-mode vs the dense reference, the tolerance)

The kernel is **correct by construction** (ADR-0000): it computes the same
per-element `score[i,j]` as `jax_deberta._self_attention`, differing only in softmax
**reduction order** (online vs one-shot) — the same algebraic identity the existing
flash already rides at ~1e-5.

**Gate 1 — kernel vs dense, interpret mode, guest CPU.** Run the full
`PallasFlashAttention.encode` (interpret=True) and `exact_reference.encode` on the
real `nla_lab` corpus buckets; compute `lab_measure.fidelity_delta` over **real
(unpadded, mask=1) tokens only**. Tolerance: `max|Δ| ≤ 1e-5` (the EXACT tier
ADR-0009 names, the same bar `flash_attention.py` claims and the dense reduction
permits — same dtype, same algebra). This is a **MEASURED** gate, asserted in a test
(`nla_lab/test_nla_lab.py` extension or a dedicated
`test_pallas_disent_flash_fidelity.py`), not an assumption.

**Gate 2 — kernel vs the jnp flash, per-tile (stronger localiser).** Since
`flash_attention._flash_attention` already reproduces the dense fold, assert the
Pallas kernel's per-`(i,j)`-tile `s` equals the jnp flash's `score_tile` to ~1e-6
*before* softmax — this isolates "the fold is right" from "the online softmax is
right," so a regression points at the exact failing term.

**Gate 3 — host, real GPU (the follow-up, NOT claimed here).** With `interpret=False`
on the 2080Ti: re-run Gate 1 to confirm Triton lowering preserves ~1e-5, and capture
the actual device peak (the OOM cell now running). This is the host-only half of the
ADR-0009 split; the guest **cannot** produce these numbers.

## 4. `est_peak_device_bytes` — the O(S) derivation (ADR-0000: the TRUE peak)

The override **reuses the one memory model** (`shape_buckets`, ADR-0012 P1), never a
second one. The dense profile is `peak_variable_bytes(mm, B, S)` with
`mm.k_quad·B·H·S²` the dominant term. The Pallas kernel **never materialises
`[B,H,S,S]`**:

- **`k_quad → 0`.** The `[B,H,S,S]` content/c2p/p2c/probs buffers are gone — they
  exist only as `[block_q, block_k]` **SRAM** tiles inside one grid cell, never as an
  HBM array. This is the term the kernel is built to delete (8 co-resident buffers ·
  `B·H·S²·4` = **8.6 GB** at `B=16,S=1024`, MEASURED-from-the-model → **0**).
- **`k_disent` covers the position intermediates.** `c2p_full`, `p2c_full`
  (`[B*H,S,2span]`, 2 buffers) are real HBM inputs — fold their count into
  `k_disent` (`mm.k_disent + 2`), the existing O(B·H·S·span) term. The per-tile SRAM
  `c2p_blk/p2c_blk` are bounded by one such buffer → already covered.
- **Linear term unchanged.** Embeddings, q/k/v, `acc`/out (`[B,H,S,d]`), the FFN
  `[B,S,intermediate]` — the `a_hidden`/`a_inter` terms, untouched.
- **Index table: O(S), B/H-free, negligible.** The single `idx1d` is `(2S−1)·4 ≈
  8 KB` at S=1024 — *strictly O(S)*, independent of B and H, so it does **not**
  reintroduce the quadratic. (The `[S,S]` debug variant is `S²·4 ≈ 4 MB`, B/H-free,
  also dominated; the O(S) 1-D form is the shipped choice precisely so the headline
  is airtight.)

So:

```python
def est_peak_device_bytes(self, bucket, cfg):
    mm = shape_buckets.dense_deberta_mem_model(cfg.num_heads, cfg.head_size, cfg.pos_ebd_size)
    mm_flash = mm._replace(k_quad=0, k_disent=mm.k_disent + 2)   # drop [B,H,S,S]; cover c2p/p2c_full
    base = shape_buckets.peak_variable_bytes(mm_flash, bucket.batch, bucket.seq_bucket)
    idx  = (2 * bucket.seq_bucket - 1) * 4                       # O(S) bucket table, B/H-free
    return base + idx
```

This stays a **conservative upper bound** (never under — the OOM-class invariant).
At `B=16, S=1024`: dense model **12.08 GB** → flash model **4.56 GB** (and the *raw*
score buffer the kernel eliminates is the 1.07 GB single / 8.6 GB co-resident term).
The remaining 4.56 GB is the `k_disent`+`lin` activations, genuinely O(B·H·S·d) +
O(B·H·S·span), no `S²` factor. The previously-OOM cell now fits. (These are the
guest-provable **model** figures; the *actual* device peak is Gate 3, host-only.)

Honesty note (ADR-0009): the model's `k_quad=8` co-residency is a conservative
over-count; the real dense peak is lower than 12.08 GB and the real flash peak lower
than 4.56 GB. The *claim* is the structural one — the `B·H·S²` term is gone — which
is provable by inspection (ADR-0009 structural-by-inspection exception) and
re-MEASURED on the host.

## 5. File layout (host-XOR-device) and SSOT reuse

Two new files, both **device** (jax/jnp/pallas only, **no numpy** — use `jnp.finfo`,
not `np.finfo`; the reference kernel's `import numpy` is *not* copied):

- `nla_lab/variants/_pallas_disent_attention.py` — the **kernel module**. Owns only
  `disent_flash_kernel` and a `pallas_disentangled_attention(q, k_scaled, v,
  c2p_full, p2c_full, c2p_idx1d, p2c_idx1d, am_bh, *, scale, span, block_q, block_k,
  interpret)` wrapper that builds the `BlockSpec`s and calls `pl.pallas_call`. Pure
  device. Neutrally/`pallas_`-named (not `jax_*`), so the honest-filename rule is
  satisfied by it being numpy-free.
- `nla_lab/variants/pallas_flash_attention.py` — the **variant**.
  `PallasFlashAttention(EncodeVariant)`: `regime=BOTH`, `fidelity_tier=EXACT`,
  `IMPLEMENTED=True`. `encode` reuses **un-forked** `jax_deberta` for embeddings,
  `_linear`/`_transpose_for_scores`, `build_relative_position` /
  `make_log_bucket_position`, `_get_rel_embedding`, and the SelfOutput / Intermediate
  / Output residual+LayerNorm block (mirroring `flash_attention._flash_layer`); it
  computes the §2.2 precomputes (memoized on `self` per the contract), calls the
  kernel module per layer, and provides the §4 `est_peak_device_bytes` override. Owns
  **only** the attention seam (ADR-0012 P1).

**XOR-gate registration.** Add both files to `test_import_xor.py`'s `SCANNED` list
(else the gate goes blind to new device modules — the documented failure that list
exists to catch). Register the variant with `@register` (the metadata-by-type guard
makes a malformed one unimportable).

**Why this composes cleanly.** The frozen `EncodeVariant` boundary
(`(params, input_ids, attention_mask, cfg) -> last_hidden_state`) is untouched; the
`Decorated` meta-wrapper and the bench's fidelity/latency/memory dimensions read it
with zero interface change. The kernel is the *only* new owned surface; everything
else is the existing SSOT, reused.

## 6. What is proven where (the explicit guest/host split)

| claim | tier | where proven |
|—|—|—|
| kernel reproduces dense disentangled attention to ~1e-5 | EXACT, MEASURED | **guest**, interpret mode (§3 Gates 1–2) |
| `est_peak_device_bytes` drops the `B·H·S²` term to 0 (true O(S) per-batch peak) | derived/structural | **guest**, arithmetic + inspection (§4) |
| Pallas-Triton compiles & runs the fp32 kernel on sm_75 | feasibility | **host** only (2080Ti, §1 gate) — NOT claimed here |
| the OOM cell (`B=16,S=1024`) actually runs; real device peak | MEASURED | **host** only (§3 Gate 3) — NOT claimed here |
| long-S IO/wall-clock win | MEASURED | **host** only — NOT claimed here |

The guest exhausts correctness and the memory *model*; the host gate is the
feasibility verdict. If the host gate fails, §1's ladder turns it into a recorded,
evidenced "Pallas cannot deliver on Turing" — not a hand-wave, and not an
abandonment of the complexity drop without a real attempt.
