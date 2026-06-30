# NLA optimization — residue & roadmap, round 1

**Status:** the forward plan after the first bake-off (`nla_lab/PORTFOLIO_RESULTS.md`).
Companion to `docs/NLA-OPTIMIZATION-PORTFOLIO.md` (the original consultation) — this is what's
*left*, how the tested methods *combine*, and the sequence to finish. Same discipline: the
bake-off retires a technique only by **measurement** or **a-priori fit** ([[GLOSSARY]] frontier
creed), bit-exactness binds nothing (P6), and every estimate/claim is measured not asserted.

---

## 1. Where round 1 left us

Seven encode variants implemented against the frozen `nla_lab` contract, measured on the
synthetic CPU fixture (the **real-weight maverick run is pending** — see §5.1):

| seam touched | variant | verdict (fixture) |
|---|---|---|
| attention | **flash_attention** | EXACT (~1e-7) — **pays, drop-in** |
| position | **cached_positions** | EXACT (~1e-7) — **pays, drop-in** (latency) |
| precision | **w8a8_int8** | ~3.5e-4 — **pays, drop-in** (throughput) |
| precision | **w4a16_weightonly** | ~4e-3 — **pays, drop-in** (latency) |
| attention | nystrom_attention | retired < S=512; soft-fixture only — **needs fitting** |
| attention | performer_favor | retired < S=512; soft-fixture only — **needs fitting** |
| FFN | monarch_ffn | ‖M_proj−W‖≈49 — **needs fitting** (data-free projection insufficient) |

The clean split: **lossless/mild** (flash, cached_positions, the two quantizers) are drop-in;
**aggressive structural** approximations (nystrom, performer, monarch) cannot match an exact
reference without a fitting pass (§3).

---

## 2. The residue — what's left to try

Grouped by whether it pays *on this hardware (2080Ti / Turing), inference-only*:

### 2a. Worth doing (high value, near-term)
- **Calibrated quantization — SmoothQuant / GPTQ / AWQ** (consultation §4). Our quantizers use
  naive per-channel/dynamic scales; calibrated scales (chosen from a small activation sample)
  *tighten* the measured divergence — likely the cheapest fidelity win, applied to the
  techniques that **already pay**. Needs calibration-scale data only (§3). New precision-seam
  variants: `w8a8_smoothquant`, `w4a16_gptq`.
- **Distillation into a structured+quantized student** (consultation §10, "the single
  highest-yield action"). The unlock for the aggressive approximations — train the student to
  match the dense teacher (§3, §8 optimizer = Newton-Schulz/Muon). A training effort, not an
  inference variant; the largest lever and the largest cost.

### 2b. Worth trying (same fit caveat as nystrom/monarch — need fitting)
- **Linformer** (§5) — low-rank projection along the *sequence* axis; a distinct attention
  approximation from Nyström/Performer. New attention-seam variant.
- **Circulant / low-displacement-rank weights** (§3, via `jnp.fft`, O(n log n)) and **low-rank
  SVD weights** (§2) — structured-weight alternatives to Monarch, from the FFT/butterfly family
  the Member State already tools. New FFN/linear-seam variants.

### 2c. Skip on Turing — hardware-gated (revisit on Hopper/Blackwell/TPU v5+)
- **FP8 (E4M3/E5M2)** — no FP8 tensor cores on Turing.
- **2:4 structured sparsity** — Ampere+ sparse tensor cores; also needs retraining.
Record these as *retired-by-fit (hardware)*, not abandoned — a retirement reason is data.

### 2d. Skip for inference — architecture changes (need retraining)
- **MLA / GQA / MQA** (§5) — they compress the K/V state the model was *trained* with full
  heads; not drop-in onto a full-MHA checkpoint.

### 2e. A separate axis we have not touched — the coref HEAD (§7)
The decode tail, not the encode: low-rank antecedent bilinear (`W=UVᵀ`, the same move our
`_bilinear_coref` 4→1 already leans on), hierarchical/banded antecedent scoring, the
proposal→resolve cascade. The head was engineered lightweight, so this is **lower priority** —
it only pays for long-document, many-mention regimes. It needs its **own variant interface**
(a `DecodeVariant`, mirroring `EncodeVariant` against the decode boundary). Deferred to round 2.

---

## 3. The nature of "fitting" (the crux for monarch/nystrom/performer)

Two distinct kinds — and the distinction is *why* round 1's aggressive variants diverged:

1. **Data-free, against the weights themselves** — project the dense weight onto the structured
   class, minimizing ‖W_struct − W_dense‖_F (SVD truncation for low-rank; FFT projection for
   circulant; ALS for Monarch). **This is what already ran** — monarch's `‖M_proj−W‖≈49` *is*
   that residual. Needs no data, and it is **structurally insufficient**: a trained dense FFN
   does not live near the Monarch class, so the closest Monarch is still far.

2. **Data-aware, against the outputs** — minimize the *output* error on real activations,
   ‖(W_struct − W_dense)·x‖ over inputs x, weighting the directions of W that matter for the
   data. This is what pays, and it needs **modest** data:
   - *Calibration-scale* (activation-aware projection; SmoothQuant/GPTQ/AWQ): a few hundred to a
     few thousand forward passes. Cheap.
   - *Full distillation*: train the student to match the teacher's outputs — more, but
     corpus-scale, nowhere near pretraining.

**The data is the corpus we already mine.** Pipe the Gutenberg paragraphs (or any representative
coref text) through the dense teacher, capture encoder activations, fit the structure to match.
Not a data-acquisition problem — "run the corpus we have through the teacher and fit," hours of
compute, not labeling. This is also why **calibrated quantization (2a) is the cheapest next
step**: the same small-calibration-sample idea, applied to techniques that already pass rather
than to rescue ones that don't.

---

## 4. Combinations — the composition structure & how to explore it (ADR-0012)

### 4a. The structure: orthogonal seams
The encode decomposes into seams. Methods on **different** seams compose; methods on the **same**
seam are mutually exclusive. Three are *places*, one is a *cross-cutting transform*:

| seam | kind | options | pick |
|---|---|---|---|
| **attention** | place | dense / flash / nystrom / performer / linformer | ≤1 |
| **position** | place (sub-of-attention) | recomputed / **cached** | on/off |
| **FFN** | place | dense / monarch / low-rank / circulant | ≤1 |
| **precision** | **cross-cutting** (every matmul) | fp32 / w8a8 / w4a16 / calibrated / fp8(future) | ≤1 |

A **combination** is one choice per seam: `(attention, position, ffn, precision)`. Today's 7
variants are each a combination with exactly **one** non-default seam (flash =
`(flash, recomputed, dense, fp32)`; w8a8 = `(dense, recomputed, dense, w8a8)`; etc.). The
unexplored space is the **multi-seam** combinations.

### 4b. The composition matrix (does X compose with Y?)
- **precision (quant) composes with everything** — it just quantizes whatever matmuls the
  place-seams emit. `flash+w8a8`, `monarch+w4a16`, `nystrom+w8a8` all valid. (The only conflict
  is precision-vs-precision: pick one scheme.)
- **`cached_positions` composes with most** — *your assumption is correct*. It caches the
  input-independent position structure (the projected position embeddings + the rel-pos gather),
  so it composes with quant, monarch, and the **content-stream** attention approximations
  (nystrom/performer **fold** the exact position terms — the cache feeds that folding). `nystrom
  + cached_positions + w8a8` is the natural throughput stack.
  - **One caveat: `cached_positions + flash`.** Flash's whole point is to never materialize the
    `[S,S]` attention; the position **cache reintroduces an `[S,S]`-ish buffer**, partially
    negating flash's memory benefit. They compose *functionally* but fight on the memory axis —
    record it, flag it, don't pretend it's free.
- **attention-vs-attention** and **FFN-vs-FFN** are mutually exclusive (one structural choice per
  place).

### 4c. The ADR-0012-appropriate mechanism (don't hand-write N×M combination variants)
The contract already anticipated this: `Decorated` is documented as "the COMPLETENESS LEVER —
if a decorator composes over any variant with zero interface change, the interface is complete."
But the round-1 variants are **monolithic** encodes (each reimplements the whole forward), so a
decorator can only wrap the *outer* encode, not intercept internal matmuls. To explore
combinations without combinatorial code duplication (the split-brain ADR-0012 P1 forbids):

1. **Route every matmul through one `matmul(a, b, *, precision)` indirection** — the precision
   seam becomes a *single home* applied throughout; swapping it quantizes the entire encode.
   (This is the cross-cutting transform made structural.)
2. **Factor each place-seam into a pluggable seam-fn with one home per option** —
   `attention_fn ∈ {dense, flash, nystrom, …}`, `ffn_fn ∈ {dense, monarch, …}`,
   `position_fn ∈ {recomputed, cached}`. Reuse the round-1 variant math as the seam-fns (it
   already exists — this is a *refactor toward composition*, not a rewrite).
3. **`SeamConfig = (attention, position, ffn, precision)`** is a typed combination; the encode is
   `compose(config)`. A registered variant becomes a `SeamConfig`; the 7 current ones are the
   single-seam configs. ADR-0000: an invalid config is unrepresentable (closed enums per seam).
4. **A `compatible(config) -> Verdict` gate** (the combination analog of `fit()`) records
   incompatible/caveat combos — `flash + cached_positions` returns a memory-caveat verdict, not
   a silent pass. This keeps the bake-off honest about combinations.
5. **The bench sweeps a *curated* config set**, not the full product (which is large): the
   single-seam baselines (regression guard) + the hypothesized Pareto stacks (e.g. the
   latency stack `flash + cached_positions[caveat] + w4a16`, the throughput stack `nystrom +
   cached_positions + w8a8`). Each config is one more row in `nla.bench_result`, measured on the
   four dimensions — combinations are first-class benchmark subjects, not special cases.

This is the structural payoff of having built the seams separately first: combinations cost a
`SeamConfig`, not new code.

---

## 5. Sequenced plan

Ordered so each step's result informs the next (the data picks the lever, not a guess):

1. **Finish the bench infrastructure** *(in progress)* — psql sink (`nla.bench_result`),
   process-per-variant isolation (no accumulation-OOM), and **real maverick-weight loading**
   (`--weights-npz`). Gate: the runner is genuinely a fresh subprocess per variant.
2. **Run the real-weight Pareto** — `run_portfolio_bench.py --weights-npz
   fixtures/deberta_maverick.npz --batches 1 2 16 32 --seq-buckets 64 128 512 1024`. This is the
   first verdict that *counts* (round-1 numbers are synthetic-fixture). Plus the deeper P6 rung:
   downstream **cluster-set agreement** (DESIGN §5) for the quantizers, not just lhs distance —
   a small lhs Δ can flip a cluster.
3. **Calibrated quantization (2a)** — add `w8a8_smoothquant` / `w4a16_gptq`, calibrated on a
   corpus sample; re-measure. Cheapest fidelity win on techniques that already pay.
4. **The seam-composition refactor (4c)** — matmul indirection + seam-fns + `SeamConfig` +
   `compatible()`. Then sweep the curated combination stacks. This turns "7 points" into "the
   Pareto surface."
5. **Distillation (2b/2a heavy)** — *if* the combination Pareto shows the aggressive structural
   methods (monarch/nystrom/linformer) are worth rescuing: pipe the corpus through the teacher,
   fit/distill (Muon/§8), re-measure. The big lever, gated on whether the surface says it's worth
   the training cost.
6. **Round 2 — the coref-HEAD axis (2e)** — a `DecodeVariant` interface + the head's low-rank /
   hierarchical / cascade techniques, *if* the head ever shows up as a bottleneck at scale.

Each step ends at a measured `nla.bench_result` row, queryable from the guest — so the decision
to proceed (or retire) is always backed by data, never by inertia.

---

## 6. Discipline (unchanged)
- The bake-off: retire only by **measurement** or **a-priori fit**; record the reason (data).
- ADR-0012 P1 for combinations: one seam-fn home per option, `SeamConfig` composes them, **no**
  hand-written N×M variants.
- Fidelity is P6 (aggregate-behavioral, measured) — except flash/cached_positions, which are
  exact and must hold ~1e-5.
- The mother's-life bar: a faked-passing or unmeasured number is the cardinal sin; an honestly
  retired technique is not a failure.
