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
inside one `pallas_call` grid cell and is *never* written to global memory as part of an
`[B,H,S,S]` array. The global memory traffic is the O(B·H·S·d) q/k/v/out activations plus the
O(B·H·S·2·span) disentangled-position intermediates — never the quadratic scores.

The payoff is the **feasibility frontier**, not a small-S latency win (a small
`[S,S]` is not IO-bound — be honest). The win is: (a) large-S **memory/feasibility**
— the OOM cells run; and (b) the IO **wall-clock** win at long S (the score tile
never round-trips global memory). This is the avenue being **exhausted**: if Pallas-on-Turing
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
  IO-fusion win (no `[B,H,S,S]` global memory round-trip) **still holds and is the point**;
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
kernel's global memory inputs.

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
global memory array.

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
  `tl.gather`, recent), the drop-in is an **global-memory-offset load**: `plgpu.load` of
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
  global memory array. This is the term the kernel is built to delete (8 co-resident buffers ·
  `B·H·S²·4` = **8.6 GB** at `B=16,S=1024`, MEASURED-from-the-model → **0**).
- **`k_disent` covers the position intermediates.** `c2p_full`, `p2c_full`
  (`[B*H,S,2span]`, 2 buffers) are real global memory inputs — fold their count into
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

## sm_75 SMEM/backend fix

Status: design + a guest-provable arithmetic gate. The HOST run on the 2080Ti
(sm_75) compile-FAILED with `ValueError: Mosaic GPU kernel exceeds available
shared memory: smem_bytes`. This section owns ONLY the tiling/backend/residence
fix (ADR-0012 P1): the index-collapse `idx1d` and the exact disentangled fold of
§2 are UNCHANGED — fidelity stays the EXACT ~1e-5 tier, re-MEASURED in interpret
mode after the retiling. Two root causes, both diagnosed at the jax-0.10.1 source
level (not inferred), and both turned into CAUGHT errors per ADR-0000 (the SMEM
budget is a derived/arithmetic claim the guest CAN check, so a "tiles exceed
SMEM" condition is a gate, not a host surprise).

### A. Root cause 1 — the Mosaic-GPU default backend (sm_90), not Triton (sm_75)

`pallas_disentangled_attention` calls `pl.pallas_call(...)` with **no**
`compiler_params`. VERIFIED in the guest venv (`jax/jaxlib 0.10.1`), the GPU
lowering dispatch (`jax/_src/pallas/pallas_call.py::gpu_lowering`) selects the
backend by the *type* of `compiler_params`, and when it is `None` it falls back
to the flag `_PALLAS_USE_MOSAIC_GPU`:

```python
# jax/_src/pallas/pallas_call.py  (0.10.1, verbatim slice)
if mosaic_gpu_backend is not None:
    if (isinstance(compiler_params, mgpu_core.CompilerParams)
        or (compiler_params is None and _PALLAS_USE_MOSAIC_GPU.value)):
        backend = mosaic_gpu_backend
if triton_backend is not None:
    if (isinstance(compiler_params, triton_core.CompilerParams)
        or (compiler_params is None and not _PALLAS_USE_MOSAIC_GPU.value)):
        backend = triton_backend
```

and the flag **defaults to `True`** (VERIFIED: `_PALLAS_USE_MOSAIC_GPU.value is
True`; `config.bool_env("JAX_PALLAS_USE_MOSAIC_GPU", True)`). So the current
no-`compiler_params` call lands on **Mosaic-GPU**, which is Hopper (sm_90)
oriented and emits the `Mosaic GPU kernel exceeds available shared memory` error
on Turing. This is the measured root cause #1, confirmed line-by-line.

**The fix — pin Triton by passing a `triton.CompilerParams`** (the `isinstance`
branch above selects `triton_backend` deterministically, regardless of the flag).
The EXACT verified jax-0.10.1 API (the design's earlier `TritonCompilerParams`
guess is WRONG for this version — the class was renamed to `CompilerParams`):

```python
from jax.experimental.pallas import triton as plgpu   # VERIFIED import (plgpu.__file__ resolves)

# plgpu.CompilerParams IS jax._src.pallas.triton.core.CompilerParams (VERIFIED identity),
# so isinstance(cp, triton_core.CompilerParams) is True -> Triton backend selected.
cp = plgpu.CompilerParams(num_warps=4, num_stages=1)   # frozen dataclass; fields VERIFIED
ctx = pl.pallas_call(
    kernel, grid=(bh, n_qt), in_specs=in_specs, out_specs=out_specs,
    out_shape=jax.ShapeDtypeStruct((bh, S, d), q.dtype),
    compiler_params=cp,            # <-- the one new argument that pins Triton
    interpret=interpret,
)(...)
```

VERIFICATION RECORD (run in the guest venv, all PASS):
- `from jax.experimental.pallas import triton as plgpu` imports (the `plgpu`
  alias the reference `pallas.ops.gpu.attention` itself uses).
- `plgpu.CompilerParams` is a frozen dataclass with fields
  `num_warps: int|None = None`, `num_stages: int|None = None`.
- `plgpu.CompilerParams is jax._src.pallas.triton.core.CompilerParams` → `True`,
  so the dispatch `isinstance` check fires Triton.
- `inspect.signature(pl.pallas_call)` lists `compiler_params` as a kwarg
  (`pallas_core.CompilerParams | None = None`).
- the bundled reference kernel `jax.experimental.pallas.ops.gpu.attention` pins
  Triton the SAME way: `compiler_params=plgpu.CompilerParams(num_warps=...,
  num_stages=...)` — so this is the sanctioned path, not a novel incantation.

The guest is CPU jax: it CANNOT compile the Triton kernel (no CUDA jaxlib), so
"Triton actually lowers the fp32 kernel on sm_75" stays the HOST gate. What the
guest PROVES is the API selection is correct (the symbols exist, the type drives
the backend) and the interpret-mode math is unchanged.

`interpret=True` ignores the backend entirely (CPU reference executor), so the
guest's fidelity gate is unaffected; `compiler_params` only bites when
`interpret=False` on the host. One flag, no forked path (§2.5 unchanged).

### B. Root cause 2 — the `[block, 2span]` position buffers staged in SRAM

The current kernel stages, per grid cell, the disentangled-position source rows
as full `2span`-wide tiles:

- `c2p_full_ref` BlockSpec `(1, block_q, span2)` → `c2p_blk = c2p_full_ref[0]` is
  `[block_q, 2span]` resident (line 73).
- `p2c_full_ref` sliced per k-tile → `p2c_blk = p2c_full_ref[0, ks, :]` is
  `[block_k, 2span]` (line 93).

At `block_q=block_k=128`, `span=256` (`2span=512`, DeBERTa-v3 head_size `d=64`),
**one** such buffer is `128·512·4 = 256 KB` — 4× Turing's whole 64 KB SMEM by
itself, and there are two. Even the core `q/k/v/score/acc` tiles at block 128
(`5·128·128·4 ≈ 320 KB` on the conservative co-resident count) blow the budget.
The `[block, 2span]` position buffers MUST NOT be SMEM-resident.

**The fix — gather the position terms per score-tile element, never stage the
`2span` axis.** The `2span` axis is the thing that makes the buffer fat, and the
kernel only ever reads ONE column per `(i,j)` element (`pos[i,j] =
idx1d[(i-j)+(S-1)]`, the §2.2 measured-equal collapse). So keep `c2p_full` and
`p2c_full` **global-memory-resident** (BlockSpec `memory_space=pl.ANY` — the whole
`[B*H, S, 2span]` stays in global memory, NOT tiled into SMEM) and gather only the
`[block_q, block_k]` entries the tile needs:

```python
# inside body(kt, carry), pos = idx1d[d_ij + (S-1)]  # [block_q, block_k] int32, as today
# PRIMARY: per-element global memory pointer-gather (no 2span axis ever in SRAM)
i_idx = (qi0 + jnp.arange(block_q))[:, None]            # [block_q, 1] global query rows
j_idx = (kj0 + jnp.arange(block_k))[None, :]            # [1, block_k] global key rows
c2p = plgpu.load(c2p_full_ref, (bh, i_idx, pos))        # [block_q, block_k]  row i, col pos[i,j]
p2c = plgpu.load(p2c_full_ref, (bh, j_idx, pos))        # [block_q, block_k]  row j, col pos[i,j]
s   = content + (c2p + p2c) / scale                      # fold UNCHANGED (§2.4)
```

`plgpu.load` is VERIFIED present in `jax.experimental.pallas.triton` (the dir
listing shows `load`, `store`). The gather pulls `block_q·block_k` fp32 elements
from global memory into the tile — the SAME footprint as the `score` tile — so the
position SRAM cost drops from `2·block·2span` to `2·block_q·block_k`. The c2p/p2c
**values** and their fold into `s` are bit-for-bit the same as §2.4; only the
RESIDENCE of the source buffer changes (global memory vs SMEM), so the EXACT ~1e-5
fidelity is untouched (re-MEASURED in interpret mode as Gate 1).

**Alternative (BANDED slice), if the per-element global memory gather does not lower on
Triton.** Within a `[block_q, block_k]` tile, `i-j` ranges over only
`block_q+block_k-1` distinct offsets, and `idx1d` is monotonic in `i-j`, so
`pos[i,j]` spans a contiguous **band** of at most `block_q+block_k-1` buckets
`[pos_lo, pos_hi]` of the `2span` axis (computed from the tile's `(qi0, kj0)`
corner). Load only that band — `c2p_full_ref[0, :, pl.dslice(pos_lo, band)]`
shaped `[block_q, band]` with `band = block_q+block_k-1` (e.g. `63` at block 32
vs `512` for full `2span`) — and gather within it (`pos - pos_lo`). SRAM cost
`block·band` ≈ `block·(2·block)`, still O(block²)-class, an 8× shrink vs the full
`2span` at block 32. The band bounds are a small in-kernel computation
(`idx1d[d_lo+(S-1)]`, `idx1d[d_hi+(S-1)]`). The HOST gate picks whichever lowers;
both are recorded, both remove the `[block, 2span]` SMEM cost, neither touches the
fold math. Primary = global memory gather (smallest SRAM, simplest); fallback = banded
slice.

### C. Chosen tiles + autotune knobs, with the SMEM byte budget

DeBERTa-v3 dims: `d = head_size = 64`, `span = pos_ebd_size = 256`
(`2span = 512`), `dtype_bytes = 4` (encode pinned fp32). The block size affects
ONLY the loop count / occupancy — online softmax is exact for ANY block (§2.3),
so we pick the largest square block that PROVABLY fits Turing's SMEM.

The conservative co-resident SRAM working set per grid cell (the budget the gate
counts — `q + k + v + score + acc + m + l + position scratch`), after the §B
redesign (position scratch = `2·block_q·block_k`, the c2p+p2c gather results, NOT
`block·2span`), with `num_stages` double-buffering the per-k-tile loaded
operands:

| block_q×block_k | num_stages | smem_bytes | vs 48 KiB (49152) | vs 64 KiB (65536) |
|—|—|—|—|—|
| 128×128 (broken, `2span` resident) | 1 | 721920 (705 KB) | **FAIL** | **FAIL** (the host error) |
| 64×64 | 1 | 115200 (112.5 KB) | **FAIL** | **FAIL** |
| 64×32 | 1 | 74240 (72.5 KB) | **FAIL** | **FAIL** |
| **32×32** | **1** | **45312 (44.25 KB)** | **PASS** | **PASS** |
| 32×32 | 2 | 73984 (72.25 KB) | FAIL | FAIL (so num_stages=2 is CAUGHT, not shipped) |

**CHOSEN: `block_q = block_k = 32`, `num_warps = 4`, `num_stages = 1`.**

- `45312 ≤ 49152` (the conservative **48 KiB** static-default cap — no opt-in
  carveout needed) with ~3.8 KB headroom, and ≤ `65536` (the **64 KiB** Turing
  opt-in carveout) with ~20 KB headroom.
- `num_warps = 4` (128 threads): a `[32,32]` tile is 1024 elements → 8
  elems/lane, a comfortable register budget; matches the reference kernel's
  `num_warps=4` for `head_dim ≤ 64`.
- `num_stages = 1` (no software pipelining): the conservative double-buffer model
  shows `num_stages=2` at block 32 is `73984 > 65536` — it would re-overflow even
  the 64 KiB carveout, so the gate FLAGS it as an arithmetic error rather than
  letting the host rediscover it (the ADR-0000 win: "tiles exceed SMEM" caught
  here). `num_stages=2` is admissible ONLY if a host profile both confirms the
  64 KiB carveout AND that the gathers are register- (not SMEM-) resident, which
  shrinks the pipelined set; until then `num_stages=1` is the guaranteed-fit
  default. This is the autotune knob, fenced by the gate.
- `block 64` (square OR `64×32`) overflows even 64 KiB → NOT shipped; the gate
  proves it. `block 32` is the Turing answer.

Because every `ENCODE_LEN_BUCKETS` rung is a power of two, `block=32` divides
`S` exactly (no ragged tile on the ladder; a sub-32 `S` uses `block=min(32,S)`).

### D. The guest-provable gate — `smem_bytes()` and the Turing limit constant

The budget is a DERIVED arithmetic claim the guest CAN check (ADR-0009: the SMEM
overflow becomes a CAUGHT arithmetic error, not a host `ValueError`; ADR-0000:
"tiles exceed SMEM" is unrepresentable past this gate). Pure-Python int
arithmetic — no jax, no numpy — so it lives in the device kernel module
(`_pallas_disent_attention.py`, host-XOR-device clean: it imports nothing
numpy-side) and is asserted by a guest test.

```python
# Turing (sm_75) shared-memory-per-block budget, bytes.
# 49152 = 48 KiB: the static-default cap a kernel gets with NO opt-in carveout (the
# conservative default this design targets). 65536 = 64 KiB: the sm_75 MAXIMUM, only
# via the dynamic-SMEM carveout opt-in. The gate asserts against the 48 KiB default.
TURING_SMEM_BUDGET_BYTES: int = 49152          # 48 KiB, conservative default
TURING_SMEM_CARVEOUT_MAX_BYTES: int = 65536    # 64 KiB, opt-in maximum (sm_75)

def smem_bytes(
    block_q: int,
    block_k: int,
    d: int,
    *,
    dtype_bytes: int = 4,
    num_stages: int = 1,
    pos_resident_2span: int = 0,   # 0 = the FIX (gather, [block,block]); >0 = span, the BROKEN [block,2span]
) -> int:
    """Conservative peak SMEM-resident bytes for ONE disent_flash_kernel grid cell.

    Counts q + k + v + score + acc + m + l + position-scratch as co-resident (an
    UPPER bound: when this passes, the tiles provably fit). `pos_resident_2span`
    selects the residence model — 0 is the shipped per-tile gather (position
    scratch = 2*block_q*block_k, the c2p+p2c results), a positive `span` reproduces
    the BROKEN [block,2span] staging for the regression assertion. `num_stages`
    double-buffers the per-k-tile loaded operands (k, v, score, position scratch)."""
    persistent = block_q * d + block_q * d + 2 * block_q          # q, acc, m+l
    if pos_resident_2span > 0:
        pos = 2 * block_q * (2 * pos_resident_2span)              # broken: [block,2span] x2
    else:
        pos = 2 * block_q * block_k                               # fix: [block_q,block_k] gathers
    pipelined = block_k * d + block_k * d + block_q * block_k + pos   # k, v, score, position
    return (persistent + num_stages * pipelined) * dtype_bytes
```

The TEST (guest, `nla_lab/test_pallas_smem_budget.py` or appended to
`test_nla_lab.py`) asserts the chosen tiles fit and the broken ones do NOT — so a
future block-size change that overflows fails CI here, never on the host:

```python
def test_chosen_tiles_fit_turing_default():
    # shipped config: block 32, num_stages 1, gather residence -> 45312 bytes
    assert smem_bytes(32, 32, d=64, num_stages=1) == 45312
    assert smem_bytes(32, 32, d=64, num_stages=1) <= TURING_SMEM_BUDGET_BYTES   # 48 KiB

def test_num_stages_2_is_caught():
    # the knob the gate fences: would re-overflow even the 64 KiB carveout
    assert smem_bytes(32, 32, d=64, num_stages=2) > TURING_SMEM_CARVEOUT_MAX_BYTES

def test_block64_is_caught():
    assert smem_bytes(64, 64, d=64, num_stages=1) > TURING_SMEM_CARVEOUT_MAX_BYTES

def test_broken_2span_residence_is_caught():
    # the host's actual failure mode, reproduced as arithmetic (block 128, span 256)
    assert smem_bytes(128, 128, d=64, pos_resident_2span=256) > TURING_SMEM_CARVEOUT_MAX_BYTES
```

### E. Guest vs host split for THIS fix (ADR-0009, honest)

The guest is CPU jax and CANNOT compile the Triton kernel. The split:

| claim | tier | where proven |
|—|—|—|
| `triton.CompilerParams` is the correct 0.10.1 symbol + `compiler_params` selects Triton | API/structural | **guest** — VERIFIED by import + isinstance + dispatch-source read (§A) |
| `smem_bytes(32,32,64) ≤ 48 KiB`; block 64 / num_stages 2 / `2span`-resident are CAUGHT | derived arithmetic | **guest** — the gate test (§D) |
| the retiling preserves the EXACT ~1e-5 fold (math unchanged, only residence/backend) | EXACT, MEASURED | **guest**, interpret mode (§3 Gate 1, re-run after retiling) |
| Pallas-Triton COMPILES + RUNS the fp32 kernel on sm_75 with these tiles | feasibility | **host** only (2080Ti) — NOT claimed here |
| the previously-OOM cell now lights up `ok`; real device SMEM/peak | MEASURED | **host** only — NOT claimed here |

The guest proves the SMEM arithmetic fits, the backend API is right, and the
math is unchanged; the HOST re-run is the gate that it now compiles, runs, and the
OOM cells go green. No GPU compile is claimed here.

## banded-select (gather-free)

This section designs the LAST in-Pallas rung: replacing the per-element advanced-index
**gather** of the c2p/p2c terms with a **band-slice + comparison-sum select** that uses no
`gather` primitive. It is anchored by a design-first interpret-mode proof of the load
primitives, run BEFORE any kernel edit (ADR-0000: prove the type/primitive exists before
building on it). It changes ONLY the c2p/p2c selection mechanism inside `body` (ADR-0012
P1): the fold, `idx1d`, the `Pow2` boundary, the online-softmax recurrence, and every
precompute (`c2p_full`/`p2c_full`/`k_scaled`) are UNCHANGED.

### The wall (host-measured), restated

On the 2080Ti (sm_75) the shipped kernel's `c2p = c2p_full_ref[bh, i_idx, pos]` /
`p2c = p2c_full_ref[bh, j_idx, pos]` advanced indexing fails at lowering:
`Unimplemented primitive in Pallas Triton lowering: gather`. The raw-Triton escape
(`jax_triton`) is DEAD (0.3.1 vs jax 0.10.1: `get_compute_capability` gone; abandoned).
So the only in-Pallas route is to express the same selection with primitives Triton's
Pallas lowering DOES implement: `dynamic_slice` (`pl.ds`), `iota`/`arange`, `==`, `where`,
and `sum`.

### The idea — a contiguous band, because `idx1d` is monotonic

For a (query-tile `qt`, key-tile `kt`) pair the relative offset `off = i - j` spans the
CONTIGUOUS range `[off_min, off_max]`, `off_min = qt*block_q - (kt*block_k + block_k - 1)`,
of width `block_q + block_k - 1`. `idx1d[off + (S-1)] = clip(bucket(off) + span)` is
MONOTONIC NON-DECREASING in `off` (`make_log_bucket_position` is monotonic; `clip` keeps it
so). Therefore the bucket COLUMN indices the tile needs form a CONTIGUOUS range of
`c2p_full`'s `2span` axis — so a single `pl.ds(base, W)` band slice (no gather) loads every
column the tile can reference. `W` is the next power of two of `block_q + block_k - 1`
(63 -> 64 at block 32), so the band fully covers the offset range and is itself `Pow2`.

### Design-first primitive proof (interpret mode) — does the load lower?

Two tiny `pallas_call`s, interpret mode, CPU jax 0.10.1 (`scratchpad/smoke_band.py`):

```python
# T1: (a) scalar read of idx_ref at a COMPUTED (program-id-arithmetic) index,
#     (b) pl.ds-slice src_ref by that idx-derived scalar start.
def k1(idx_ref, src_ref, o_ref, *, off_min_const):
    computed = off_min_const + pl.program_id(0)   # data-dependent (traced) index
    b_lo = idx_ref[computed]                       # SCALAR read at a computed index
    o_ref[...] = src_ref[pl.ds(b_lo, W)]           # dynamic-slice by the idx-derived start
# T2: the realistic [block_q, 2span] shape: src_ref[:, pl.ds(b_lo, W)] -> [block_q, W],
#     then the one-hot comparison-sum select (arange==sel -> *band -> sum).
# T3 CONTROL: the advanced-index gather that fails on host Triton.
```

OUTCOME (the literal run):

```
[PASS] T1 idx-read + pl.ds(b_lo,W): lowered+ran. out[:8]=[ 5. 6. 7. 8. 9. 10. 11. 12.]
[PASS] T2 [block,2span] band + onehot-sum select: lowered+ran.
[PASS] T3 CONTROL advanced-index gather: lowered+ran.
```

**The data-dependent `pl.ds(b_lo, W)` LOWERS in interpret mode** — and, crucially, T1/T2 use
a band start `b_lo` read from a ref at a traced index, NOT loop arithmetic: the jax/pallas
frontend and abstract-eval impose **no "the slice start must be a loop index" guard**; an
arbitrary traced `int32` scalar (here an `idx1d` read) is an accepted `pl.ds` start. Had
such a guard existed it would have fired at trace time in interpret mode (frontend guards
are backend-independent) — it did not. **This forecloses the "band-start is the wall"
hypothesis at the level the guest CAN measure**: the start is not rejected; the
arithmetic-band fallback is NOT needed.

**HONEST caveat (ADR-0009, the measured wall vs the structural argument).** T3 — the gather
— ALSO lowers in interpret mode. Interpret is the lax CPU executor; it does NOT reproduce
the Triton lowering, so **interpret-mode lowering is NON-DISCRIMINATING for the host wall**:
it cannot, on the guest, prove the band-slice lowers on Triton WHERE the gather does not.
What the guest establishes is two things, stated precisely:

1. **(measured, guest)** the band-select is a valid jax/pallas program — no frontend or
   abstract-eval rejection of the data-dependent `pl.ds` start, and it runs.
2. **(structural argument, host-confirmable)** `pl.ds` is `lax.dynamic_slice`, which Triton's
   Pallas backend lowers to a block pointer (`tl.make_block_ptr`/`tl.advance`) with a
   **runtime base offset** — the SAME primitive the existing k-tile loop already lowers
   successfully with `pl.dslice(kj0, block_k)` where `kj0 = kt*block_k` is a traced loop
   scalar. From Triton's view `b_lo` (an `idx1d` read) and `kj0` (loop arithmetic) are
   indistinguishable: both are runtime SSA `int32` values feeding the slice base. The band
   introduces NO new primitive class beyond what the shipped kernel already lowers. The
   `gather`, by contrast, lowers to an element-wise `tl.gather`/scatter the backend does not
   implement. So the band-slice is *expected* to lower where the gather does not — but that
   is a **HOST claim** (2080Ti), flagged, not a guest measurement. If a future host run
   reports `Unimplemented primitive ... dynamic_slice` (it should not, given the existing
   `kj0` dslice already lowers), THAT is the precise measured wall to report, and the
   arithmetic-band fallback (below) is the next rung.

### Numerical exactness — band-select == gather, bit-for-bit (the strong guest result)

The decisive guest proof is not "it lowers" but "it computes the SAME values." A second
interpret-mode kernel (`scratchpad/smoke_equiv.py`) computes BOTH the gather and the
band-select in one body and writes their difference:

```
S=32  span=16  2span=32  bq=16 W=32:  max|c2pΔ|=0.00e+00  max|p2cΔ|=0.00e+00  PASS
S=64  span=16  2span=32  bq=32 W=32:  max|c2pΔ|=0.00e+00  max|p2cΔ|=0.00e+00  PASS  (degenerate W==2span)
S=16  span=16  2span=32  bq=8  W=16:  max|c2pΔ|=0.00e+00  max|p2cΔ|=0.00e+00  PASS  (true narrowing, bh=2,3)
S=128 span=256 2span=512 bq=32 W=64:  max|c2pΔ|=0.00e+00  max|p2cΔ|=0.00e+00  PASS  (deberta-large, 512->64)
S=256 span=256 2span=512 bq=32 W=64:  max|c2pΔ|=0.00e+00  max|p2cΔ|=0.00e+00  PASS  (8x8 multi-tile grid)
```

**BIT-EXACT (`== 0.0`)** across the synthetic-cfg regime (`pos_ebd_size=16 -> 2span=32`),
the true-narrowing regime, and the deberta-v3-large regime (`2span=512 -> W=64`, an 8x
narrowing), single- and multi-tile, multi-batch. Because the selection is the ONLY changed
seam (ADR-0012 P1) and it is bit-identical to the gather it replaces, the WHOLE-kernel
fidelity vs `exact_reference` is UNCHANGED from the shipped gather kernel's measured ~1e-5
EXACT tier — proved compositionally, not re-asserted. (The `== 0.0` is the right bar here:
this is a pure-integer index/selection identity, a LOGIC invariant, asserted bit-exactly per
ADR-0009/ADR-0012 P6 — not a float-sensitive quantity that would warrant a tolerance.)

### The band geometry (and a real bug the proof caught — ADR-0000)

```python
W        = pow2(min(_next_pow2(block_q + block_k - 1), two_span))   # Pow2, and <= 2span
off_min  = qt*block_q - (kt*block_k + block_k - 1)   # arithmetic of grid (qt) + loop (kt) indices
b_lo     = idx1d[off_min + (S - 1)]                  # SCALAR idx1d read at the computed index
base     = clip(b_lo, 0, two_span - W)               # the CLAMPED band base (see below)
c2p_band = c2p_full_ref[bh, pl.ds(qi0,    block_q), pl.ds(base, W)]   # [block_q, W]
p2c_band = p2c_full_ref[bh, pl.ds(kj0,    block_k), pl.ds(base, W)]   # [block_k, W]
```

**The bug the design-first proof caught (this is why proving-first matters).** The naive
`base = b_lo`, `sel = pos - b_lo` gave a NONZERO residual (`max|Δ| ≈ 5.2`). Cause:
`lax.dynamic_slice` (= `pl.ds`) **silently clamps** its start to keep the window in-bounds,
so when `b_lo > two_span - W` the band Triton actually loads starts at `two_span - W`, not
`b_lo` — but `sel` was computed against the unclamped `b_lo`, so the one-hot picked the
wrong column at the high edge. ADR-0000 fix (make the mismatch unrepresentable): compute the
clamp EXPLICITLY as `base` and derive `sel` from the SAME `base` the slice uses, so the two
can never disagree. With `base = clip(b_lo, 0, two_span - W)` the residual is `0.0`. The
band's needed bucket range (width `<= block_q+block_k-1 <= W`, by `idx1d` monotonicity/
compression) is then always inside `[base, base+W)`, so `sel = pos - base` is provably in
`[0, W)` — confirmed by the `0.0` residual (an out-of-range `sel` would zero a one-hot row
and show as nonzero Δ).

**W vs 2span.** `pl.ds(base, W)` requires `W <= two_span`, so `W = min(next_pow2(block_q+
block_k-1), two_span)`. Both operands are powers of two (`two_span = 2*pos_ebd_size`,
`pos_ebd_size` pow2), so the `min` is `Pow2` — branded by `pow2()` at the kernel boundary
(ADR-0000), like every other kernel dim. For deberta-large `W=64` (`2span=512`, real
8x narrowing); for the tiny synthetic cfg `W` clamps to `2span=32` (the band degenerates to
the whole axis — still gather-free, just not narrowing). `base` is then always `0` and
`sel = pos`, correct by the same argument.

### The comparison-sum select (c2p AND p2c) — no gather

`sel[i,j] = idx1d[(i-j)+(S-1)] - base` (in `[0, W)`). The gather `band[row, sel]` is
expressed as a one-hot contraction over the band's `W` axis (`arange`/`==`/`*`/`sum` — all
Triton-supported):

```python
sel    = pos - base                                          # [block_q, block_k], in [0, W)
onehot = (jnp.arange(W)[None,None,:] == sel[:,:,None])        # [block_q, block_k, W], bool
c2p    = jnp.einsum("iw,ijw->ij", c2p_band, onehot.astype(f32))   # c2p_band rows = query i
p2c    = jnp.einsum("jw,ijw->ij", p2c_band, onehot.astype(f32))   # p2c_band rows = key   j
```

c2p contracts the band's QUERY-indexed rows (`iw`), p2c the KEY-indexed rows (`jw`), against
the SAME `onehot` (both terms reuse the one collapsed `pos`/`sel` — the MEASURED c2p==p2c
column-index collapse, UNCHANGED). The result feeds the existing fold verbatim:
`s = content + (c2p + p2c)/scale`, then mask, then the online-softmax update.

The one-hot intermediate is `[block_q, block_k, W]` (= 32x32x64 fp32 = 256 KB) — a
TRANSIENT consumed immediately by the `sum`, NOT an SRAM-resident buffer (it is budgeted
like the existing `content`/`p = exp(...)` transients, which `smem_bytes` also does not
count as co-resident). Its `W=64` reduction depth is a HOST register-pressure consideration
(ADR-0009 host gate — does Triton keep it in registers or spill to local memory), not a
guest SMEM-resident overflow.

### SMEM budget with the `[block, W]` bands (<= 64 KiB carveout)

`smem_bytes` gains a band-residence model (the design extends the SHIPPED gate, ADR-0012
P1 — no second model):

```python
def smem_bytes(block_q, block_k, d, *, dtype_bytes=4, num_stages=1,
               pos_resident_2span=0, band_w=0):           # band_w: the [block,W] band residence
    persistent = block_q*d + block_q*d + 2*block_q        # q, acc, m+l
    if pos_resident_2span > 0:
        pos = 2*block_q*(2*pos_resident_2span)            # broken [block,2span] (regression)
    elif band_w > 0:
        pos = block_q*band_w + block_k*band_w             # FIX: c2p_band[bq,W] + p2c_band[bk,W]
    else:
        pos = 2*block_q*block_k                           # prior gather-result residence
    pipelined = block_k*d + block_k*d + block_q*block_k + pos   # k, v, score, position
    return (persistent + num_stages*pipelined)*dtype_bytes
```

Computed budget (block 32, d 64, fp32, num_stages 1):

| residence | pos scratch | total bytes | 48 KiB default | 64 KiB carveout |
|—|—|—|—|—|
| gather (shipped) | 2*32*32 = 2048 | **45312** | OK (3.8 KB headroom) | OK |
| **band W=64 (the fix)** | 32*64 + 32*64 = 4096 | **53504** | **OVER by 4352 B** | **OK (12 KB headroom)** |
| band W=64, num_stages=2 | — | 90368 | OVER | OVER (CAUGHT) |
| band W=64, block 64 | — | 115200 | OVER | OVER (CAUGHT) |
| band W=32 (synthetic cfg) | 32*32 + 32*32 = 2048 | 45312 | OK | OK |

The band costs **+8192 B (+8 KiB)** over the gather at block 32 / W 64 — exactly two
`[32,64]` bands (8 KB each) replacing the `2x[32,32]` gather scratch (8 KB total). At
**53504 B (52.25 KiB) the band pushes PAST the 48 KiB static default INTO the dynamic-SMEM
carveout** — this is FINE (sm_75's max is 64 KiB) and is the documented intent: the shipped
gather fit the conservative default; the band requires the carveout opt-in. `num_stages=2`
(90368) and block 64 (115200) overflow even the carveout and stay CAUGHT by the gate.

**Carveout-opt-in HONESTY (host gate).** `plgpu.CompilerParams` in jax 0.10.1 exposes only
`num_warps`/`num_stages` — there is NO explicit `shared_memory`/carveout knob. Triton
requests the >48 KiB dynamic-SMEM carveout IMPLICITLY from the kernel's computed footprint
(it emits `cudaFuncAttributeMaxDynamicSharedMemorySize`). The guest can ASSERT only
`band_smem <= TURING_SMEM_CARVEOUT_MAX_BYTES` (the arithmetic); whether the sm_75 driver
GRANTS 52.25 KiB is a HOST gate (ADR-0009), not claimed here.

Gate test (extends `test_pallas_smem_budget.py`):

```python
def test_band_select_fits_carveout_not_default():
    # the band residence at block 32 / W 64 is the deberta-large shipped config
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1, band_w=pow2(64)) == 53504
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1, band_w=pow2(64)) >  TURING_SMEM_BUDGET_BYTES        # past 48 KiB
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1, band_w=pow2(64)) <= TURING_SMEM_CARVEOUT_MAX_BYTES  # within 64 KiB
    # +8 KiB vs the gather residence is the whole cost of the two [block,W] bands
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1, band_w=pow2(64)) \
         - smem_bytes(pow2(32), pow2(32), d=_D, num_stages=1) == 8192

def test_band_num_stages_2_is_caught():
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=2, band_w=pow2(64)) == 90368
    assert smem_bytes(pow2(32), pow2(32), d=_D, num_stages=2, band_w=pow2(64)) > TURING_SMEM_CARVEOUT_MAX_BYTES
```

### Invariants preserved (ADR-0000 / ADR-0012 P1)

- **Pow2.** `W = pow2(min(next_pow2(block_q+block_k-1), two_span))` is branded at the kernel
  boundary; a non-pow2 `W` is unconstructable. The existing `block_q`/`block_k`/`S`/`d`/
  `idx1d`-length `Pow2` boundary is untouched.
- **idx1d.** The ONE strict-O(S) bucket table is UNCHANGED — still length `2S` (padded),
  still `clip(bucket(d)+span)`, still the MEASURED c2p==p2c column collapse. It is now read
  in TWO ways: the per-element `pos = idx1d[d_ij+(S-1)]` (as before) AND one extra SCALAR
  `b_lo = idx1d[off_min+(S-1)]` for the band base. No new table, no `[S,S]` matrix.
- **The fold.** `s = content + (c2p + p2c)/scale`, the mask, and the online-softmax
  recurrence (`m`/`l`/`acc` rescale) are byte-for-byte the shipped body; only how `c2p`/`p2c`
  are produced changed, and that production is bit-identical to the gather (`== 0.0`).
- **Precomputes.** `c2p_full`/`p2c_full`/`k_scaled`/`pos_query`/`pos_key` and every
  `jax_deberta` helper are reused un-forked (ADR-0012 P1). `c2p_full`/`p2c_full` stay
  `memory_space=pl.ANY` (global-memory-resident); the band reads `[block,W]` slices from
  them, never staging the full `[block,2span]`.

### Guest vs host split for the band-select (ADR-0009, honest)

| claim | tier | where proven |
|—|—|—|
| data-dependent `pl.ds(b_lo, W)` start is not rejected by the frontend/abstract-eval; the band program runs | structural | **guest** — interpret smoke T1/T2 (`smoke_band.py`) |
| band-select == gather BIT-EXACTLY (`==0.0`), incl. the clamp fix, multi-tile, deberta-large dims | LOGIC invariant, MEASURED | **guest** — `smoke_equiv.py` (0.0 over 5 regimes) |
| whole-kernel fidelity vs `exact_reference` unchanged from the shipped ~1e-5 | EXACT, compositional | **guest** — selection is the only change and it is bit-identical |
| `smem_bytes(band) = 53504 <= 64 KiB`; num_stages 2 / block 64 CAUGHT | derived arithmetic | **guest** — the gate test |
| interpret-mode lowering DISCRIMINATES band from gather | — | **NOT provable on guest** — interpret lowers gather too (T3); the discriminator is host-only |
| Triton on sm_75 lowers `pl.ds(b_lo,W)` (where `gather` failed); driver grants the 52 KiB carveout; OOM cell goes green | feasibility | **host** only (2080Ti) — NOT claimed; structural argument: same `dynamic_slice` the `kj0` k-loop already lowers |

The guest proves the band-select is a valid program, computes the gather's values
bit-for-bit, and fits the carveout arithmetic; it CANNOT prove the Triton lowering
discriminates band from gather (interpret is non-discriminating). The structural argument —
`pl.ds` is the `dynamic_slice` the existing k-loop already lowers, fed a traced scalar that
Triton cannot tell apart from `kj0` — is why the band-start is not expected to be the wall,
but the host re-run on the 2080Ti is the gate that settles it, and if it reports
`Unimplemented primitive ... dynamic_slice` THAT is the next measured wall (with the
arithmetic-band fallback — a static over-wide offset-space band mapped through a static
`idx1d` slice — the following rung).
