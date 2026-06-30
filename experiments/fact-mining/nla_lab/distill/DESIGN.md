# nla_lab/distill — QAT / feature-distillation of a quantized DeBERTa student against the maverick teacher (DESIGN)

Status: **design, not yet built**. This file is the implementable spec; no number in
it is asserted — every fidelity/loss claim below is marked as a quantity the guest
self-test or the host run **MEASURES** (ADR-0009: a perf/equivalence claim is honest
only with its substantiation attached; an un-run number is stated as un-run).

## 0. Why this exists, and the verdict that motivates it

On real maverick weights the PTQ ceiling was measured (the standing `--weights-npz`
bench): SmoothQuant pulled w8a8 lhs-Δ `0.128 → 0.035` (P6-promising), but AWQ barely
moved w4a16 `0.474 → 0.438`. **4-bit weight quant is past what scale-selection PTQ can
fix** — AWQ already grid-searches the best per-channel scale (`w4a16_awq.py`) and the
residual is still ~0.44, because the *untrained* weights do not live near the 4-bit
grid. Training is the lever: the student's full-precision **shadow** weights LEARN to
be quantization-robust, so the same int4 kernel rounds them with far less output error.
This is the §8 "Resolves finally" action (`NLA-OPTIMIZATION-PORTFOLIO.md:205-208`) and
the residue §3 fitting ladder's top rung (data-aware / full distillation,
`...RESIDUE-1.md:82-95`). The same lever is what would resurrect the retired structural
techniques (monarch ‖M−W‖≈49 untrained, nystrom ~0.85) — all failed because untrained
weights don't live near the approximation class. This module builds the lever for
quant (W4, the clear need) first; the structural techniques reuse the identical loop.

## 1. The fidelity-regime trade — named explicitly up front (ADR-0009 / ADR-0012 P6)

This module operates in a **different fidelity regime** from the inference path, and
the two must not be conflated:

- **The inference path proves bit-near-identity.** `exact_reference` round-trips to
  `fidelity-vs-self == 0`; `test_deberta_fidelity` holds the jax encode to ~1e-3 vs the
  torch reference; the daemon's `--coref-verify` proves the device forward reproduces
  the reference cluster set. That path's contract is **the SAME weights, reproduced
  exactly** — a reordering/port that must not move the float beyond tolerance.

- **The distilled QAT student is P6-aggregate via a TRAINED student — NOT bit-exact.**
  The student weights are *different numbers* from the teacher; the student lhs is a
  **trained approximation** of the teacher lhs, never a bit-reproduction of it. Its only
  honest claim is the **ADR-0009 tier-2 aggregate-behavioral** distance
  (`lab_measure.fidelity_delta`: `mean|Δ|` / `max|Δ|` over real tokens), and the claim
  is that this distance, after training, drops **below the PTQ w4a16 floor**. There is
  no `== 0`, no `ABS_TOL`, on the student-vs-teacher comparison — asserting one would be
  the ADR-0009 category error (pinning a float-sensitive, *learned* quantity bit-exact).

**State the trade in one line:** the inference path buys *exactness of a fixed
computation*; the distillation path buys *a smaller learned feature-error at 4 bits*,
measured, and gives up bit-exactness by construction. The `FidelityTier` the deployed
W4 student reports stays `AGGREGATE_BEHAVIORAL` (`contract.py:78`), the same as the PTQ
w4a16 variant — the student does not, and cannot, upgrade the tier; it improves the
*number within* that tier.

## 2. Module layout (ADR-0012 P1 SSOT + host-XOR-device P9/P7)

A NEW, cleanly-separated subpackage. The optimizer/training loop is new; **everything
it computes a forward with is reused, not re-authored** (P1): the teacher forward is
`jax_deberta.encode`; the student's fake-quant value is the round-1 int4 kernel
`w4a16_weightonly._quantize_dequantize_int4` verbatim; the corpus padder is
`shape_buckets.pad_to`; the npz codec is `export_deberta_maverick.save_npz` /
`coref_decode_server.load_deberta_npz`. The distill module adds exactly three things
that do not exist elsewhere: the **STE gradient routing**, the **feature-distillation
loss**, and the **training loop**.

```
nla_lab/distill/
  DESIGN.md            # this file
  __init__.py          # host: stdlib only (package marker); SCANNED host-side
  ste.py               # DEVICE (jax-only, numpy-free): the STE fake-quant + student forward + loss
  optim.py             # DEVICE (jax-only): optax-AdamW wrapper (+ hand-rolled AdamW fallback)
  train.py             # HOST (numpy-free, jax-free AST): the loop driver, CLI, data plan, checkpoint cadence
  data.py              # HOST (numpy-free, jax-free AST): text -> spm tokens -> bucketed host batches
  test_distill.py      # HOST test entry (drives the device self-test; like test_nla_lab.py)
```

**The host-XOR-device split (the ADR-0012 mandate the task names):**

- **Device math is confined to `ste.py` + `optim.py`** — jax + optax + `jax_deberta` +
  the int4 kernel; **never numpy**. Same posture as `lab_measure.py` (the import-XOR
  gate's "device math: lab_measure + every variant" lane). `optax` is gate-neutral (not
  numpy, not a name-flagged device lib) but the file also `import jax`, so its AST is a
  single side: device-only, XOR-clean.
- **Orchestration is host-clean** — `train.py` / `data.py` import only stdlib + the
  registry/corpus + the device module *by name* (`nla_lab.distill.ste`), exactly as
  `bench.py` calls `lab_measure` without importing jax itself. Their own AST carries no
  numpy and no jax, so the gate classifies them host-only.
- **The npz read/write is the declared BOUNDARY** — the distilled student is written by
  the ONE codec `export_deberta_maverick.save_npz` (numpy, already a `BOUNDARY_FILES`
  entry), the teacher is read by `coref_decode_server.load_deberta_npz`. The distill
  module re-authors **no** npz format (P7: one home for the cross-boundary truth).

**Gate registration (a real action item, not automatic):** `test_import_xor.py:SCANNED`
is an EXPLICIT list, not a glob — every new file gets an entry (`ste.py`/`optim.py` as
device-side, `train.py`/`data.py`/`__init__.py` as host-side). `nla_lab/mypy.ini` uses
`files = nla_lab`, so the subpackage is auto-covered by `mypy --strict`; any new local
untyped dep is a *named* `[mypy-...] follow_imports = skip`, never a blanket relaxation
(P8). These registrations are part of "done" (Rule 1) — the gate must stay green.

## 3. TEACHER — the frozen full-precision encode

```python
# device (ste.py). params_teacher is FROZEN: it never appears in any jax.grad argnums.
teacher_lhs = jax_deberta.encode(params_teacher, ids, mask, cfg)   # [B, S, H]
```

The teacher is `jax_deberta.encode` on the loaded maverick npz (host run) or the
`lab_measure.synthetic_deberta` fixture (guest). It produces the **target lhs** per
batch. It is differentiated against **never** — `jax.lax.stop_gradient(teacher_lhs)` at
the loss site makes the target a constant, so no gradient leaks into the teacher even by
accident. For the optional per-layer signal, a teacher `encode_all_hiddens` (below)
returns the list of per-layer hidden states; it too is `stop_gradient`-ed.

## 4. STUDENT + the straight-through estimator (the crux — get this exactly right)

The student is the **same architecture** with the six per-layer Linear weights replaced,
**every forward**, by their fake-quantized form, with gradients routed to the
full-precision shadow weights via a straight-through estimator. The non-negotiable
ADR-0013 cardinal sin is a loop that silently doesn't learn — gradients zero through the
fake-quant. Here is precisely why that happens and precisely how the STE prevents it.

**Why the naive kernel kills the gradient.** `_quantize_dequantize_int4`
(`w4a16_weightonly.py:115`) computes `q = clip(round(w/scale), -8, 7)` then
`dq = q*scale`. `jnp.round` is piecewise-constant, so `d(round)/dw = 0` *almost
everywhere*; `jax.grad` through the round-1 kernel as-is returns a **zero** gradient to
`w`. Wiring the round-1 kernel straight into a training loop would produce exactly the
flat-loss, zero-gradient failure the standard forbids — and it would look like it ran.

**The STE — forward value reused verbatim (P1), gradient routed identity:**

```python
# ste.py — the ONLY new gradient mechanism in the module.
import jax
from nla_lab.variants.w4a16_weightonly import _quantize_dequantize_int4, _GROUP_SIZE
# (w4a16_awq.py already imports _quantize_dequantize_int4 the same way — the int4
#  math has exactly ONE home; this wrapper adds only the gradient routing around it.)

def fake_quant_int4_ste(w: jax.Array, group_size: int = _GROUP_SIZE) -> jax.Array:
    """W4 fake-quant with a straight-through estimator.
    forward  : == _quantize_dequantize_int4(w)   (the round-1 value, bit-for-bit)
    backward : d/dw == 1  (identity) — the gradient reaches the shadow weight w."""
    dq = _quantize_dequantize_int4(w, group_size)          # non-differentiable (round)
    return w + jax.lax.stop_gradient(dq - w)
```

Walk the autodiff:
- **Forward:** `w + stop_gradient(dq - w) = w + (dq - w) = dq`. The value the matmul
  consumes is *exactly* the round-1 dequantized weight — the same operand the deployed
  W4 kernel feeds. `stop_gradient` changes no forward value.
- **Backward:** `d/dw [ w + stop_gradient(dq - w) ] = 1 + 0 = 1`. The
  `stop_gradient(dq - w)` term is a constant to autodiff (its `round` is sealed off), so
  the gradient flows purely through the `+ w` identity path. The shadow weight receives
  `∂L/∂dq` straight through — the textbook STE.

**Why plain (identity) STE is the correct STE here, not the clipped variant.** The
round-1 kernel scales per group by `absmax/7`, so `|w/scale| ≤ 7` by construction and
the `clip(-8,7)` essentially never saturates — there are no out-of-range weights whose
gradient a clipped-STE would need to zero. (If a *static-range* quantizer were used
instead, the clipped STE — zero gradient where the weight saturated — would be the right
choice; noted, not needed.) The fp16 dequant inside the kernel does not block the
gradient: `dq` is cast back to fp32 before `dq - w`, and the gradient never traverses
the fp16 cast (it traverses `+ w`, fp32).

**The student forward — owns ONLY the weight seam (P1, mirrors `w4a16_weightonly`):**

```python
def quantize_shadow(shadow: dict, group_size: int) -> dict:
    # same seam selector as the PTQ variant: Linear .weight, 2-D, infix-matched.
    return {k: (fake_quant_int4_ste(v, group_size)
                if _is_linear_weight(k, v) else v)
            for k, v in shadow.items()}     # _is_linear_weight reuses _LINEAR_PROJ_INFIXES

def student_lhs(shadow: dict, ids, mask, cfg) -> jax.Array:
    return jax_deberta.encode(quantize_shadow(shadow, _GROUP_SIZE), ids, mask, cfg)
```

`quantize_shadow` is applied **fresh every forward** (NOT memoized — the opposite of the
PTQ variant's R1-C prep cache): the quantized weights must be re-derived from the
*current* shadow each step so the gradient reaches the *current* shadow. The selector,
the infix set, and the int4 math are all the round-1 home; the only delta is the STE
wrapper and the per-step (un-memoized) application.

## 5. OBJECTIVE — feature-distillation loss (no labels; the teacher is the target)

Primary: final-lhs MSE over **real tokens** (the squared form of
`lab_measure.fidelity_delta`'s convention, `lab_measure.py:116-128` — mask==1 positions,
normalized by `n_real * H`):

```python
def feature_loss(shadow, ids, mask, cfg, teacher_lhs) -> jax.Array:
    s = student_lhs(shadow, ids, mask, cfg)
    diff2 = jnp.square(s - jax.lax.stop_gradient(teacher_lhs))
    m = mask.astype(diff2.dtype)[:, :, None]
    return jnp.sum(diff2 * m) / jnp.maximum(jnp.sum(m) * s.shape[-1], 1.0)
```

Optional stronger signal — per-layer hidden-state matching. A reused
`encode_all_hiddens(params, ids, mask, cfg) -> list[[B,S,H]]` mirrors
`jax_deberta.forward` (`jax_deberta.py:303-342`) but appends each `_layer` output; it
reuses `jax_deberta._layer`, `_get_attention_mask`, `_get_rel_embedding`,
`build_relative_position` (no re-authoring of the disentangled attention). The loss adds
`Σ_l β_l · MSE(student_h_l, stop_gradient(teacher_h_l))`. Per-layer matching gives a
denser gradient (every block is supervised, not only the output) and is the documented
stronger-signal option; the final-lhs MSE is the safe primary because it is *exactly*
the quantity the bench measures. There are **no labels** — the teacher's activations are
the entire supervision (residue §3: "run the corpus we have through the teacher and
fit").

## 6. OPTIMIZER + LOOP

- **Baseline: optax AdamW** (`optax==0.2.8` is in the generic venv — verified importable;
  `jax==0.10.1`). `optim.py` wraps `optax.adamw(lr, weight_decay)` into `(init, update)`
  over the shadow pytree. AdamW is the safe, known-good baseline for STE gradients.
- **Aspiration: Muon / Newton–Schulz** (§8, `PORTFOLIO.md:116-119`). The shadow Linear
  weights are exactly the 2-D matrices Muon's orthogonalizing update targets; the
  Newton–Schulz coupled iteration sidesteps eigendecomposition. **Noted as the §8
  aspiration, not the baseline** — minted as a second `optim.py` transform only if a
  measured AdamW run motivates it (ADR-0011: mechanism on the second occurrence, not
  speculatively). AdamW ships first.
- **The step (device, `jax.jit`):**
  ```python
  loss, grads = jax.value_and_grad(feature_loss)(shadow, ids, mask, cfg, teacher_lhs)
  updates, opt_state = opt.update(grads, opt_state, shadow)
  shadow = optax.apply_updates(shadow, updates)
  ```
  `jax.grad` differentiates w.r.t. `shadow` (argnum 0) only — teacher params/targets are
  closed-over constants. The STE makes `grads` for the Linear weights **nonzero**; the
  bias/LayerNorm/embedding entries (passed through unquantized in `quantize_shadow`) get
  ordinary gradients. Whether to also train the non-quantized params or freeze them to
  the teacher is a flag (`--train-nonquant`, default: train only the quantized Linear
  shadows — that is the QAT lever; freezing the rest keeps the student close to the
  teacher and shrinks the trainable set).
- **Gradient checkpointing:** `jax.checkpoint` (`jax.remat`) around `jax_deberta._layer`
  for the 24-layer real forward if the 2080Ti's ~11 GB needs it (recompute activations
  in backward, trade compute for memory). **Noted** — the guest fixture (2-layer) does
  not need it; the **real run is host**, where memory is decided. The student forward
  also holds *two* forwards' activations (student + the teacher target), so remat is the
  likely lever; the host run flags it on if OOM.
- **Loop (host, `train.py`):** for each epoch, iterate the bucketed corpus, compute the
  teacher target per batch once (it is constant across epochs — cache the teacher lhs per
  batch to disk/host if memory allows, else recompute), call the device step, log
  `loss` every N steps. Checkpoint the shadow npz on a cadence. Honest compile/run
  separation is inherited (the device step is jitted once).

## 7. DATA PIPELINE + the DATA PLAN

**Pipeline:** text → spm tokenize (reuse the daemon's torch-free preprocess / the
vendored `spm.model` the maverick export ships, `coref_decode_server` §preprocess) →
bucket+pad to `[B, s_bucket]` via `shape_buckets.bucket_len`/`pad_to` (the ONE ladder,
never re-bucketed) → host batches → teacher lhs targets via `jax_deberta.encode`. On the
guest the pipeline shortcuts to `lab_corpus.make_batch` (seeded synthetic ids) +
`synthetic_deberta` teacher — the machinery, not the production corpus.

**The data plan (what + how much, with the diversity caveat) — residue §3 ladder:**

- **WHAT.** Deployment-representative *unlabeled* text. The coref deployment sees prose
  and dialogue; the Gutenberg paragraphs already mined are the available proxy and the
  teacher supplies the targets (no labeling). **Diversity caveat (load-bearing):** a
  *single book* is borderline-narrow — one author's register, vocabulary, and sentence
  shape — and a student fit to it will be quant-robust *on that distribution* and may
  regress elsewhere. **Supplement it:** multiple books across genres + registers
  (exposition, dialogue, modern text), so the feature-distillation covers the activation
  manifold the deployed encoder actually meets. This is the §3 "needs diversity" point
  made concrete: the single-book PoC corpus is the floor, not the target.
- **HOW MUCH.** Two rungs, matching the residue §3 ladder (`...RESIDUE-1.md:84-88`):
  - *Cheap GPTQ/calibration-style rung:* ~**128–512** sequences — enough to fit
    per-channel structure (this is the scale the AWQ calibrator already uses,
    `_CALIB_MAX_ROWS = 256`). A fast first signal, not the full lever.
  - *Feature-distillation rung:* ~**few-K to 10–20K** sequences — corpus-scale but
    nowhere near pretraining; this is where the W4 student earns the drop below the PTQ
    floor. Hours of teacher-forward compute, not labeling.

## 8. GUEST VERIFICATION — the machinery, not the production number (ADR-0009/0013)

All on the synthetic fixture (`synthetic_deberta` teacher, `lab_corpus` batches), CPU
jax, no download. These prove the **mechanism**; the production number is the host run
(§9). **None of these is asserted here — they are the tests to RUN; the design does not
claim they pass.** They go in `test_distill.py` (host entry driving the device self-test,
like `test_nla_lab.py`).

1. **The STE actually passes gradient (the anti-cardinal-sin test).**
   `g = jax.grad(feature_loss)(shadow, ...)`; assert `‖g‖` over the Linear-weight leaves
   is **strictly > 0**. A single optimizer step must **change** the shadow Linear weights
   (`shadow_after ≠ shadow_before` on the quantized keys).
2. **The NEGATIVE control — proving the STE is load-bearing.** Re-run the gradient with
   the round-1 kernel **without** the STE wrapper (plain `_quantize_dequantize_int4` in
   the forward). Assert that gradient is `≈ 0` on the Linear weights. This demonstrates,
   honestly and on the artifact, that it is the STE — not some other path — carrying the
   gradient: the round kills it, the STE restores it. (This is the test that would have
   caught a silently-flat loop.)
3. **The loss decreases.** Over a few hundred steps on the fixture, `feature_loss`
   **drops monotone-in-trend** (report the curve; do not fake a decreasing loss — a flat
   or rising loss is a real finding to report, ADR-0013).
4. **QAT < PTQ — the whole point, MEASURED on the fixture.** Compute, against the FROZEN
   fixture teacher lhs:
   - `e_ptq  = fidelity_delta( w4a16_weightonly(teacher_weights),  teacher_lhs )` — quantize
     the teacher directly (the round-1 PTQ baseline).
   - `e_qat  = fidelity_delta( w4a16_weightonly(distilled_shadow), teacher_lhs )` — quantize
     the trained shadow.
   Assert `e_qat < e_ptq`. **This is a cross-weights comparison** (both quantized, both
   scored against the *same* teacher), which the standing bench's per-params fidelity
   (variant-vs-`exact_reference`-on-same-params) does not do — so the **distill module
   owns this number**, computed in its own eval. If `e_qat ≥ e_ptq` on the fixture after a
   real training run, that is a genuine finding and is reported, not hidden.
5. **Gates stay green.** `mypy --strict` (`nla_lab/mypy.ini`), the import-XOR gate with
   the new SCANNED entries, and `test_distill.py` all pass. host-XOR-device: training
   device-math confined to `ste.py`/`optim.py`, the loop orchestration host-clean.

## 9. THE REAL DISTILLATION — the host run (exact command + artifact)

The production number — maverick teacher + a real corpus, a student npz that benchmarks
**below the PTQ floor** — is the **host run** (real weights, real GPU, real corpus). The
guest proves only the machinery (§8).

```bash
# HOST (real maverick weights + real corpus). venv: . ~/w/vdc/venvs/generic/bin/activate
python -m nla_lab.distill.train \
    --teacher-npz fixtures/deberta_maverick.npz \
    --corpus      <diverse multi-book / deployment-representative text> \
    --bits 4 --group-size 64 \
    --epochs <E> --lr <lr> --batch <B> --seq-buckets <ladder> \
    --train-nonquant=false --remat=true \
    --out fixtures/deberta_maverick_w4_distilled.npz
```

**The artifact:** `fixtures/deberta_maverick_w4_distilled.npz` — the trained **shadow**
weights (full-precision fp32), written by the ONE codec `export_deberta_maverick.save_npz`
(same `__cfg__*` + `__tokenizer__` layout the teacher uses; **no second npz format**).
It is the deployed W4 student: at inference the *same* int4 kernel PTQ-quantizes these
trained-to-be-robust weights.

**The benchmark that closes the loop:**
```bash
python -m nla_lab.bench --weights-npz fixtures/deberta_maverick_w4_distilled.npz \
    --variants exact_reference w4a16_weightonly --psql --run-tag w4-distilled
```
plus the distill module's own **teacher-referenced** eval (§8 rung 4) reporting
`e_qat` vs the recorded `e_ptq ≈ 0.474` PTQ floor. The expected, to-be-measured result:
`w4a16_weightonly(distilled_shadow)` feature-error vs the teacher lands **below** the
0.474 PTQ floor — the demonstrable distillation benefit. (Optional standing-bench
integration: a `--reference-npz <teacher>` flag pinning the teacher as the fidelity
reference would fold the cross-weights number into `nla.bench_result`; minted if the
recurrence warrants it, ADR-0011.)

## 10. ADR ledger (which gate each decision answers)

- **ADR-0009.** The benefit is MEASURED, never asserted: §8 rung 4 (`e_qat < e_ptq`),
  the loss curve, the host bench. The fidelity-regime trade is named (§1): trained-P6
  aggregate, NOT the bit-exact `--coref-verify` inference contract. No number in this
  design is claimed as run.
- **ADR-0012 P1/P7.** Teacher = `jax_deberta.encode` reused; student fake-quant value =
  `_quantize_dequantize_int4` reused verbatim; npz = the one codec; corpus padder = the
  one ladder. The loop/optimizer is the new, cleanly-separated module. host-XOR-device:
  device math in `ste.py`/`optim.py`, orchestration host-clean, npz at the declared
  boundary (§2).
- **ADR-0012 P6/P8.** The student stays `AGGREGATE_BEHAVIORAL` (no false tier upgrade);
  `mypy --strict` covers the subpackage; new untyped deps are named skips.
- **ADR-0013.** The cardinal sin (flat loss / zero gradient through fake-quant) is
  directly tested AND has a negative control proving the STE is what carries the gradient
  (§8 rungs 1–2). The build is the full mandate — STE + loss + loop + data plan +
  guest proof + host command — not a safe subset; a non-decreasing loss is reported as a
  real finding, not papered over.
