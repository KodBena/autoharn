# NLA optimization portfolio — for the post-correctness performance phase

**Status:** Filed for the **NLA phase** (per the roadmap: cruft removal → *correctness/OOM-proofing* →
NLA → use the software). **Not yet acted on.** The intent is a chocofarm-style portfolio — like the
inference service's 16 control algos (BangBang, contextual bandit, …) tried empirically — here a
scenario-contingent portfolio of numerical-linear-algebra accelerations, each measured, none assumed.

**Provenance + caveat (read first).** This is an external NLA-expert consultation. It has **NOT seen
this codebase** — its two code annexes are *illustrative*, not prescriptions to apply verbatim (it
guessed at interfaces). It was asked for *generic* advice **beyond** the families we already had in view as the obvious
starting candidates — (i) randomized NLA underwritten by matrix-concentration inequalities, and
(ii) butterfly decompositions, K-FAC, tensor trains, and stochastic rounding.

**Crucially: NONE of these has actually been tried yet — not even the named starting families.** They are
*candidates to evaluate*, each gated on whether it makes sense for this stack — e.g. randomized NLA may
pay nothing if the matrices are too small for matrix-concentration to buy a useful approximation. Where
the verbatim resolution below says these instruments are "already in the Member State's possession," read
that as *known-of and on the candidate list*, **not implemented**. So: take the *specifics* with a grain
of salt; the durable value is the **framing** — the regime axiom, the two-lane portfolio split, and the
encoder-first allocation.

---

## Bearing on the CURRENT work (the OOM / space-estimate workflow) — why this was filed now

The in-flight `oom-proof-encode-chunking` workflow derives a memory model whose dominant term is the
**dense disentangled-attention scores `B·H·S²`** and bounds the batch against free VRAM. Two items below
change *exactly that term*, so the memory model must stay a clean, **swappable SSOT**, not a frozen formula:

- **§5 FlashAttention** is *exact* and **never materializes the `n×n` matrix** → the `B·H·S²` memory term
  we're bounding **collapses** to ~`O(B·S·d)`. Adopting Flash would *relax* the OOM bound massively (much
  bigger batches fit). So the memory model's attention term must be a **named, replaceable component**
  (dense today; Flash/Nyström later → update that one term, the chunker logic unchanged). I'll verify this
  when folding the OOM workflow.
- **§6(a)** the DeBERTa **content-to-position / position-to-content logits over log-bucketed relative
  positions are low-rank and precomputable/cacheable** — this is the same `[S,S]` relative-position table
  we already saw *baked into every compiled executable* (the per-shape constant). Caching it is a **memory
  *and* speed** win, and it's the most natural *first* NLA-phase action because it also shrinks the very
  footprint the OOM workflow is fighting.

So the sequencing is coherent: OOM-proof the *current* dense attention now (correctness), keep the
attention-memory term swappable, then the NLA phase swaps in Flash/cached-positions and the bound *relaxes*.

It also **independently corroborates** our own measured finding: §1's regime axiom (latency = bandwidth/
launch-bound at small batch; throughput = compute-bound at large batch) is exactly the dispatch-bound encode
we traced (`[1,64]`=50ms vs `[2,256]`=16.5ms) and the two regimes the portfolio (§10) splits on.

---

## The consultation (verbatim)

> *Recalling* the instruments already in the Member State's possession — randomized NLA under matrix
> concentration, the butterfly lineage, K-FAC, tensor trains, and stochastic rounding,
>
> *Noting* the operational theatre: a DeBERTa encoder coupled to the Maverick coreference head, under
> migration to a sovereign JAX/XLA workflow, with throughput and latency weighted *pari passu*,
>
> *Having considered* the architecture as published at the ACL Sovereign Repository — wherein the encoder
> forward pass dominates cost while the Maverick head (endpoint-bilinear mention extraction and antecedent
> scoring) is deliberately lightweight, and wherein mention proposal and clustering are separable stages,
>
> *Affirming* that bit-level fidelity binds no party hereto, and that a scenario-contingent portfolio is
> the sought deliverable,
>
> The Secretariat hereby:
>
> 1. *Observes* the unifying axiom under which every "cheat code" is one trade against exact arithmetic —
>    fewer FLOPs, fewer bytes in motion, or lower precision per byte — and that the binding regime decides
>    which trade is paid: latency at small batch is **bandwidth- and launch-overhead-bound**, throughput at
>    large batch is **compute-bound**, so a single technique occupies different points on the Pareto
>    frontier in each;
>
> 2. *Notes* the spectral and sketching family extending the cited randomized NLA — randomized SVD with
>    power iteration, leverage-score and CountSketch / sparse-JL subsampling, the **Nyström** column-sampling
>    approximation, the subsampled randomized Hadamard transform and **Fastfood** (whose engine is the fast
>    Walsh–Hadamard transform, itself a butterfly, closing the loop to the Member State's existing tooling),
>    and **Hutch++** / stochastic Lanczos quadrature for traces, log-determinants, and spectral densities —
>    all underwritten by the same matrix-Bernstein machinery;
>
> 3. *Notes also* the structured-matrix family extending butterfly / TT / K-FAC — **Monarch** matrices (the
>    hardware-efficient generalization of butterfly, expressive enough to absorb FFT, low-rank, and sparse
>    as special cases), low-displacement-rank and circulant operators (matmul via `jnp.fft` in O(n log n)),
>    Tucker and CP decompositions for tensors, and **hierarchical matrices** (HODLR / HSS / H²) for any
>    operator whose off-diagonal blocks are low rank;
>
> 4. *Notes further* the number-format family extending stochastic rounding — INT8/INT4, **FP8** (E4M3 for
>    weights, E5M2 for gradients), microscaling **MX** block formats, NF4, the post-training calibrators
>    GPTQ / AWQ / SmoothQuant, per-channel scaling, mixed-precision accumulation, and mixed-precision
>    iterative refinement (GMRES-IR) — with stochastic rounding retained as the unbiasing instrument that
>    makes the others statistically honest under accumulation;
>
> 5. *Observes*, as the bridge most material to this workload, the locus where the foregoing families enter
>    attention itself, the Member State's existing categories reappearing in disguise: **FlashAttention**
>    (exact, IO-optimal — the correct baseline, not an approximation), **Nyströmformer** (Nyström of the
>    softmax matrix), **Performer / FAVOR+** (random Fourier/positive features), **Linformer** (low-rank
>    projection along the sequence axis), and **MLA / GQA / MQA** (low-rank or shared compression of the
>    K/V state) — such that adopting "linear attention" *is* adopting randomized NLA against the attention
>    operator;
>
> 6. *Urges* the encoder-first allocation of effort for this specific stack — because the Maverick head was
>    engineered down and DeBERTa dominates the budget, the highest-leverage targets are (a) the
>    **disentangled-attention** structure, whose content-to-position and position-to-content logits are
>    computed over *log-bucketed* relative positions and are therefore low-rank and precomputable/cacheable
>    rather than recomputed per pair; (b) the FFN projections, candidates for Monarch / low-rank / structured
>    replacement; and (c) quantization of the encoder weights — and *cautions* that DeBERTa's three-term
>    attention is **not** a single `softmax(QKᵀ)`, so Nyström/Performer do not drop in unmodified:
>    approximate the content stream and fold the position terms in via their bucket structure;
>
> 7. *Recommends* the coref-head accelerations as the secondary tier, decisive only for long documents with
>    many mention candidates — namely low-rank factorization of the antecedent bilinear (W = UVᵀ, the reduced
>    factors precomputed once per document) and **hierarchical or banded** antecedent scoring exploiting
>    mention locality (the H-matrix logic: dense scoring within a window, a handful of long-range landmarks
>    elsewhere) — and *notes* that the head's published `predefined_mentions` / clustering-only interface
>    natively supports a **cascade**: cheap proposal, selective expensive resolution;
>
> 8. *Recommends*, should the Member State fine-tune rather than merely infer, the matrix-function family on
>    the optimizer side — **Newton–Schulz** coupled iterations for inverse matrix roots and orthogonalization
>    (the engine beneath Shampoo, SOAP, and **Muon**), which sidestep eigendecomposition entirely — paired
>    with bf16 storage under stochastic rounding;
>
> 9. *Calls upon* the following JAX realization paths: **Pallas** for fused Flash/Nyström kernels on TPU and
>    GPU; Google's **AQT** for quantization-aware execution; `lax.dot_general` with
>    `preferred_element_type=jnp.int32` for INT8 accumulation and the `precision` flag to govern TF32/bf16
>    matmul on TPU; `jnp.fft` for circulant operators; `lax.reduce_precision` composed with the PRNG for
>    stochastic rounding; and, at the parallelism layer, `shard_map`/`pmap` to saturate the bulk regime
>    versus a single-device `jit` tuned for the realtime one;
>
> 10. *Decides* the portfolio split, which is the operative crux:
>
> > **Realtime / latency lane** — weight-only **W4A16** quantization (the bandwidth-bound regime where
> > 4-bit weights pay and de-quant overhead amortizes over few tokens); exact FlashAttention on short
> > documents; aggressive kernel fusion and minimized launch count; structured-position caching in DeBERTa.
> > *Avoid* linear-attention here — at short sequence length its constants lose to exact Flash.
> >
> > **Bulk / throughput lane** — full **W8A8** INT8 (or FP8 on Hopper/Blackwell/TPU v5+) so the *matmul
> > itself* runs on low-precision tensor cores; 2:4 structured sparsity where supported; **Nyström or
> > Performer** attention once documents are long enough to clear the crossover; maximal batch with
> > **length-bucketing** to evict padding waste; approximation error tolerated because it averages over the
> > batch.
> >
> > **Shared across both** — Monarch/TT-structured weights and distillation cut *bytes and FLOPs
> > simultaneously* and so serve either lane, at the cost of a retraining/distillation pass to recover the
> > accuracy that bit-fidelity would have guaranteed.
>
> ---
>
> Two reference implementations are appended outside the diplomatic syntax, each the cleanest expression of
> one family against one half of the stack.
>
> **Annex I — low-rank antecedent scoring (Maverick head, long-document regime).** Replaces the
> O(M·d² + M²·d) full bilinear with O(M·d·r + M²·r), r ≪ d:
>
> ```python
> import jax
> import jax.numpy as jnp
>
> def factored_antecedent_scores(g_start, g_end, U_s, U_e, V_s, V_e):
>     """
>     g_start, g_end : [M, d]  endpoint reps of M mention candidates
>     U_*, V_*       : [d, r]  low-rank factors of the antecedent bilinear (r << d)
>     Returns S : [M, M], S[i, j] ~= score that j is an antecedent of i.
>     Cost: O(M*d*r + M^2*r) vs O(M*d^2 + M^2*d) for the dense bilinear.
>     """
>     phi = g_start @ U_s + g_end @ U_e        # [M, r]  left reduced rep
>     psi = g_start @ V_s + g_end @ V_e        # [M, r]  right reduced rep
>     S   = phi @ psi.T                        # [M, M]
>
>     M = S.shape[0]
>     causal = jnp.tril(jnp.ones((M, M), dtype=bool), k=-1)  # attend only earlier
>     return jnp.where(causal, S, -jnp.inf)
> ```
>
> **Annex II — Nyström attention (DeBERTa content stream, long-document bulk regime).** Bidirectional, so
> no causal bookkeeping; never materializes the n×n matrix:
>
> ```python
> import jax
> import jax.numpy as jnp
>
> def nystrom_attention(Q, K, V, num_landmarks=64):
>     """
>     Q, K, V : [n, d]. Approximates softmax(Q K^T / sqrt(d)) V in O(n*m*d),
>     m = num_landmarks << n. Assumes n % m == 0 (pad upstream otherwise).
>     For DeBERTa, apply to the content term; handle the bucketed position
>     terms separately via their (low-rank) structure.
>     """
>     n, d = Q.shape
>     m = num_landmarks
>     scale = 1.0 / jnp.sqrt(d)
>
>     Ql = Q.reshape(m, n // m, d).mean(axis=1)         # [m, d] segment-mean landmarks
>     Kl = K.reshape(m, n // m, d).mean(axis=1)         # [m, d]
>
>     F = jax.nn.softmax(scale * (Q  @ Kl.T), axis=-1)  # [n, m]
>     A = jax.nn.softmax(scale * (Ql @ Kl.T), axis=-1)  # [m, m]
>     B = jax.nn.softmax(scale * (Ql @ K.T),  axis=-1)  # [m, n]
>
>     A_pinv = jnp.linalg.pinv(A)                       # [m, m]; swap for an
>                                                       # iterative Moore-Penrose
>                                                       # step if differentiability
>                                                       # or speed demands it
>     return F @ (A_pinv @ (B @ V))                     # [n, d]
> ```
>
> *Resolves*, finally, to flag the single highest-yield action not reducible to a kernel: since fidelity is
> unconstrained, **distilling the DeBERTa+Maverick pipeline into a structured-and-quantized student**
> dominates every per-operator trick above on the latency lane, and composes with all of them on the
> throughput lane.

---

## Synthesis — what's most material, and when (our reading, against our measured stack)

1. **Encoder-first is correct for us, with a twist — our encode is *dispatch*-bound at small batch.** Our
   trace shows the small-batch deberta forward is launch/overhead-bound, not compute-bound (`[1,64]`=50ms).
   So on the **latency lane** (the hook's real workload), the §10 prescriptions that pay are the ones that
   cut *launch/bandwidth*: kernel **fusion** (fewer launches), **W4A16** weight-only quant (fewer weight
   bytes to move — the bandwidth term), and **structured-position caching** (§6a — and it shrinks memory).
   Linear attention is correctly *contra-indicated* here (its constants lose to exact Flash at short S).
2. **FlashAttention is the keystone, and it touches the OOM work first** (see "Bearing" above): exact, and
   it deletes the `B·H·S²` materialization — both a speed win *and* the thing that relaxes our memory bound.
3. **The DeBERTa-3-term caution is the real engineering content.** Disentangled attention ≠ `softmax(QKᵀ)`;
   any Nyström/Performer adoption (bulk lane) must approximate only the *content* stream and fold the
   bucketed position terms via their low-rank structure. This is the non-obvious part that a codebase-blind
   agent got right in principle and would get wrong in code — so the annexes are sketches, not patches.
4. **Coref-head accelerations are secondary** (§7) — the head is already lightweight; only long-document,
   many-mention regimes justify the low-rank/H-matrix antecedent scoring or the proposal→resolve cascade.
   (Annex I's factored bilinear is the same `W=UVᵀ` move our `_bilinear_coref` 4→1 consolidation already
   leaned on — a natural first head experiment if/when it's the bottleneck.)
5. **Distillation is the dominating latency move** — but it trades the bit-fidelity we currently *prove*
   (`--coref-verify` 0 mismatch) for a retrained student. That's a different fidelity regime (P6 aggregate-
   behavioral, not discrete-exact) and a deliberate decision, not a free lunch — flag it as such when we get
   there.

**Portfolio discipline (the chocofarm parallel):** like the inference service's control-algo bake-off, each
of these — **including the named starting families, none yet tried** — is a *registered candidate to
evaluate*, not a mandate. The dimensions of the experiment are the regime (latency vs throughput), the
crossover points, and the fidelity tier. A candidate can be retired **two** ways: by *measurement* (it
underperformed), or **a priori on fit** (the structure doesn't apply — e.g. randomized NLA on matrices too
small for matrix-concentration to bite, low-rank on an already-full-rank operator). Both are portfolio
decisions worth *recording* — a retirement reason is data, per the frontier creed (retire a technique only
via a named, failed experiment or a stated structural mismatch, never by unexamined assumption). Bit-
exactness binds nothing here, so the surviving bar is P6 aggregate-behavioral equivalence (ADR-0009),
measured.
