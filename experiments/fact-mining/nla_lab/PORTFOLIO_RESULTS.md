# NLA Portfolio Bake-Off — Results (the HONEST Pareto)

Synthesis of the 7-technique non-linear-attention (NLA) optimization portfolio against
the frozen `nla_lab` contract (`contract.py`: `EncodeVariant`), each candidate a
whole-encode swap of the dense **disentangled** DeBERTa-v3 encoder
(`jax_deberta.encode` — content `QKᵀ` + content→position `c2p` + position→content `p2c`
over log-bucketed relative positions, **not** a plain `softmax(QKᵀ)`).

Every variant was implemented (real math in `encode`, `IMPLEMENTED=True`,
`est_peak_device_bytes` overridden to its own profile), **adversarially verified**
(real-technique / no-cardinal-sin / disentangled-3-term / honest-memory / own-file-only),
and **measured** through the shared harness against `exact_reference` on the bench's
synthetic CPU fixture (`python -m nla_lab.bench`). Fidelity is the encoder-`last_hidden_state`
aggregate distance `max|Δ|` / `mean|Δ|` vs the dense reference (P6, `lab_measure.fidelity_delta`).

> **Scope of these numbers (read first).** All fidelity/memory figures are on the bench's
> tiny synthetic fixture: `scale=0.02` random weights → small content logits → **near-uniform,
> near-low-rank attention**. That is the *easiest possible* regime for low-rank/random-feature
> approximators. It proves **math + structural correctness**; it does **not** establish
> real-trained-weight fidelity for the approximators. Representative GPU latency/throughput and
> real `deberta-v3-large` / maverick-coref-weight fidelity are the **host follow-ups** listed at
> the bottom. The memory estimates (`est_peak_device_bytes`) are exact arithmetic and fully
> valid here — they are declared a-priori bounds, not measurements.

---

## The Pareto table

Memory column = `est_peak_device_bytes` ratio vs the dense reference at **B=1, S=512**
(`dense = 17.12 MiB`); trend noted where it moves with S. "Drop-in" = reaches its claimed
tier on the dense weights with **no fitting pass**. "Needs fitting" = an untrained structured
operator whose divergence is real and only closes with a distillation / re-fit pass (the
portfolio §6 caution — a *recorded retirement is data, not a failure*).

| Technique | Regime | Tier (claimed→verified) | Verified P6 `max\|Δ\|` (mean) | Est device mem vs dense | Verdict |
|---|---|---|---|---|---|
| **exact_reference** (baseline) | both | EXACT | `0.00e+00` (by construction) | `1.00×` (dense bound) | **baseline** — the A/B control; `max\|Δ\|` vs itself = 0 |
| **flash_attention** | both | EXACT ✓ | `1.2e-7 … 4.8e-7` | `0.15×` @S512, **`0.08×` @S1024** (drops the `[B,H,S,S]` quadratic) | **PAYS — drop-in, exact.** Tiled online-softmax over all 3 disentangled terms; memory win grows with S |
| **cached_positions** | latency | EXACT ✓ | `0.0 … 1.2e-7` | `1.12×` (resident position cache — *above* dense, by design) | **PAYS — drop-in, exact (latency lane).** Hoists content-independent pos-projection + gather tables; trades resident memory for dropped recompute |
| **w8a8_int8** | throughput | AGGREGATE_BEHAVIORAL ✓ | `3.5e-4 … 4.0e-4` | `1.00×` (FP32 activations dominate; INT8 weights are out of variable scope) | **PAYS — drop-in (mild quant held P6-aggregate).** A compute/throughput candidate, honestly **not** a memory candidate |
| **w4a16_weightonly** | latency | AGGREGATE_BEHAVIORAL ✓ | `3.8e-3 … 4.1e-3` (mean `~9.2e-4`) | **`0.50×`** (A16 half-precision activations; 4-bit weights excluded from variable term) | **PAYS — drop-in, mild divergence.** Weight-only int4 has no structural crossover; ~4e-3 is the honest int4-of-σ0.02-weights error |
| **nystrom_attention** | throughput | AGGREGATE_BEHAVIORAL | retired <512; @S≥512 `2.2e-5 … 2.8e-5` *(soft fixture)* | `0.27×` @S512, **`0.14×` @S1024** (drops quadratic content scores) | **RETIRED-BY-FIT + NEEDS FITTING.** `fit()` retires below S=512. Near-exact **only** because the fixture is near-low-rank; untrained landmarks diverge on realistic peaked attention (stress: 0.2→`1.34`, 1.0→`5.4`). Needs distillation/landmark-fit for real weights |
| **performer_favor** | throughput | AGGREGATE_BEHAVIORAL | retired <512; @S≥512 `9.0e-5 … 1.07e-4` (mean `~3e-5`) *(soft fixture)* | `0.77×` @S512/S1024 (quadratic **reduced not dropped** — the position fold re-materializes the combine) | **RETIRED-BY-FIT + NEEDS FITTING.** FAVOR+ content kernel + **exact** position fold. Random features are unbiased but high-variance; soft fixture is the easy case. Needs more features / distillation for real-weight P6 |
| **monarch_ffn** | throughput | AGGREGATE_BEHAVIORAL | `2.4e-2 … 2.6e-2` (mean `~6.1e-3`) | `1.00×` (win is in **weights/FLOPs**, excluded by contract; gelu still spans full `[B,S,intermediate]`) | **DIVERGES — NEEDS FITTING.** Frobenius-optimal Monarch projection of the *trained* dense FFN is genuinely out-of-class (`‖M_proj−W‖≈49`); ~2.5e-2 divergence is unavoidable without a distillation pass. A correct, recorded a-priori retirement |

### Drop-in vs needs-a-fitting-pass — stated plainly

- **Drop-in (no fitting; reach their tier on the dense weights):**
  `flash_attention` and `cached_positions` (both **EXACT**, ~1e-7, exact reassociations of
  the same arithmetic), plus the two quantizers that held their aggregate tier —
  `w8a8_int8` (~3.5e-4) and `w4a16_weightonly` (~4e-3, mild). These are deployable today;
  their open work is GPU perf + real-weight confirmation, not algorithmic fitting.
- **Need a distillation / fitting pass (untrained structured operators, per the portfolio
  §6 caution that linear approximators do not drop into disentangled attention unmodified):**
  `nystrom_attention`, `performer_favor`, `monarch_ffn`. Each is a **real, correct**
  implementation that **folds the position terms exactly and approximates only the content /
  FFN stream** — and each honestly **declines to claim** real-weight P6, naming its fit
  precondition. Their small fixture numbers are the soft-fixture easy case, **not** evidence
  of trained-weight fidelity. nystrom/performer additionally `fit()`-retire below the S=512
  concentration crossover (a recorded portfolio decision; raise `--seq-buckets` to exercise).

---

## Unified bench tables (`python -m nla_lab.bench`)

CPU jax, synthetic fixture. `devMiB` = the variant's declared conservative **upper bound** on
peak **variable** (non-weight) **device** bytes (the 4th dimension). `max|Δ|` = P6 lhs distance
vs `exact_reference`. `fit_retired` = a-priori recorded retirement (not a break).

### Default geometry — B∈{1,2} × S∈{64,128} (the latency-lane self-test)

```
variant            regime       B  Sbkt     p50ms     p95ms     rows/s     max|Δ|     devMiB     status
cached_positions   latency      1    64     0.358     0.580     2792.5   0.00e+00       0.43         ok
cached_positions   latency      2    64     0.529     0.709     3779.2   0.00e+00       0.82         ok
cached_positions   latency      1   128     0.581     0.916     1722.5   1.19e-07       1.41         ok
cached_positions   latency      2   128     0.972     1.234     2057.8   2.98e-08       2.70         ok
exact_reference    both         1    64     1.056     1.109      947.0   0.00e+00       0.39         ok
exact_reference    both         2    64     1.237     1.571     1616.5   0.00e+00       0.78         ok
exact_reference    both         1   128     1.524     1.790      656.0   0.00e+00       1.28         ok
exact_reference    both         2   128     1.901     2.167     1052.1   0.00e+00       2.56         ok
flash_attention    both         1    64     1.108     1.207      902.4   2.38e-07       0.33         ok
flash_attention    both         2    64     1.304     1.378     1534.1   1.19e-07       0.66         ok
flash_attention    both         1   128     1.571     2.003      636.7   1.19e-07       0.66         ok
flash_attention    both         2   128     2.008     2.323      996.2   2.38e-07       1.31         ok
monarch_ffn        throughput   1    64     1.074     1.210      931.3   2.42e-02       0.39         ok
monarch_ffn        throughput   2    64     1.269     1.528     1575.4   2.59e-02       0.78         ok
monarch_ffn        throughput   1   128     1.563     1.980      639.9   2.59e-02       1.28         ok
monarch_ffn        throughput   2   128     2.008     2.299      995.9   2.59e-02       2.56         ok
nystrom_attention  throughput   1    64         —         —          —          —       0.58 fit_retired
nystrom_attention  throughput   2    64         —         —          —          —       1.16 fit_retired
nystrom_attention  throughput   1   128         —         —          —          —       1.16 fit_retired
nystrom_attention  throughput   2   128         —         —          —          —       2.31 fit_retired
performer_favor    throughput   1    64         —         —          —          —       0.33 fit_retired
performer_favor    throughput   2    64         —         —          —          —       0.66 fit_retired
performer_favor    throughput   1   128         —         —          —          —       1.03 fit_retired
performer_favor    throughput   2   128         —         —          —          —       2.06 fit_retired
w4a16_weightonly   latency      1    64     1.090     1.300      917.7   4.03e-03       0.20         ok
w4a16_weightonly   latency      2    64     1.347     1.442     1484.7   4.00e-03       0.39         ok
w4a16_weightonly   latency      1   128     1.463     1.529      683.8   3.78e-03       0.64         ok
w4a16_weightonly   latency      2   128     1.907     2.187     1048.8   4.11e-03       1.28         ok
w8a8_int8          throughput   1    64     1.141     1.241      876.7   3.51e-04       0.39         ok
w8a8_int8          throughput   2    64     1.319     1.625     1516.4   3.69e-04       0.78         ok
w8a8_int8          throughput   1   128     1.616     1.772      618.9   3.72e-04       1.28         ok
w8a8_int8          throughput   2   128     2.173     2.395      920.6   4.03e-04       2.56         ok
```

### Extended geometry — B∈{1,2} × S∈{512,1024} (exercises the linear-attention crossover)

```
variant            regime       B  Sbkt     p50ms     p95ms     rows/s     max|Δ|     devMiB     status
cached_positions   latency      1   512    11.487    12.276       87.1   7.45e-09      19.13         ok
cached_positions   latency      2   512    31.428    34.927       63.6   7.45e-09      36.26         ok
cached_positions   latency      1  1024   104.164   107.132        9.6   5.96e-08      74.26         ok
cached_positions   latency      2  1024   208.085   215.627        9.6   1.19e-07     140.51         ok
exact_reference    both         1   512    11.057    12.305       90.4   0.00e+00      17.12         ok
exact_reference    both         2   512    26.300    27.507       76.0   0.00e+00      34.25         ok
exact_reference    both         1  1024    59.901    67.706       16.7   0.00e+00      66.25         ok
exact_reference    both         2  1024   116.474   134.403       17.2   0.00e+00     132.50         ok
flash_attention    both         1   512     7.473     8.254      133.8   1.19e-07       2.62         ok
flash_attention    both         2   512    12.551    13.628      159.3   2.38e-07       5.25         ok
flash_attention    both         1  1024    32.691    36.165       30.6   2.98e-07       5.25         ok
flash_attention    both         2  1024    57.103    63.499       35.0   4.77e-07      10.50         ok
monarch_ffn        throughput   1   512    10.431    11.684       95.9   2.59e-02      17.12         ok
monarch_ffn        throughput   2   512    26.099    27.752       76.6   2.59e-02      34.25         ok
monarch_ffn        throughput   1  1024    62.886    66.258       15.9   2.59e-02      66.25         ok
monarch_ffn        throughput   2  1024   115.275   119.516       17.3   2.59e-02     132.50         ok
nystrom_attention  throughput   1   512     6.668    10.980      150.0   2.81e-05       4.62         ok
nystrom_attention  throughput   2   512    10.993    11.999      181.9   2.83e-05       9.25         ok
nystrom_attention  throughput   1  1024    10.291    19.034       97.2   2.21e-05       9.25         ok
nystrom_attention  throughput   2  1024    17.433    26.985      114.7   2.33e-05      18.50         ok
performer_favor    throughput   1   512    12.061    13.358       82.9   1.04e-04      13.12         ok
performer_favor    throughput   2   512    27.770    29.900       72.0   1.07e-04      26.25         ok
performer_favor    throughput   1  1024    62.344    68.061       16.0   9.02e-05      50.25         ok
performer_favor    throughput   2  1024   112.474   119.505       17.8   1.00e-04     100.50         ok
w4a16_weightonly   latency      1   512    10.702    11.928       93.4   4.02e-03       8.56         ok
w4a16_weightonly   latency      2   512    25.108    27.719       79.7   4.01e-03      17.12         ok
w4a16_weightonly   latency      1  1024    62.811    67.315       15.9   4.04e-03      33.12         ok
w4a16_weightonly   latency      2  1024   115.356   117.381       17.3   3.97e-03      66.25         ok
w8a8_int8          throughput   1   512    11.411    12.756       87.6   3.92e-04      17.12         ok
w8a8_int8          throughput   2   512    25.835    31.324       77.4   3.90e-04      34.25         ok
w8a8_int8          throughput   1  1024    60.517    63.391       16.5   4.07e-04      66.25         ok
w8a8_int8          throughput   2  1024   112.713   117.189       17.7   4.02e-04     132.50         ok
```

> Latency columns are **CPU-fixture** numbers, not the verdict — small-S CPU jax is launch/overhead
> bound and not representative of the GPU latency/throughput these techniques target. They are recorded
> for completeness; the memory bound and the fidelity are the load-bearing CPU-valid results.

---

## Gates — frozen contract + host-XOR-device

All gates green after synthesis (run from `experiments/fact-mining/`, venv `~/w/vdc/venvs/generic`):

| Gate | Result |
|---|---|
| `pytest nla_lab/test_nla_lab.py test_import_xor.py test_device_transfers.py` | **21 passed** |
| `mypy --config-file nla_lab/mypy.ini` | **Success: no issues found in 18 source files** |
| `python -m nla_lab.bench` (default + extended sweeps) | all 7 + baseline `ok` / `fit_retired`; no `failed_*`, no `not_implemented` |

**Two finalization fixes (both behavior-preserving) applied at synthesis** — the parallel
sibling agents each ran a narrower self-check; the unified gate surfaced:

1. **mypy `--strict` (34 cosmetic-typing errors across 5 variant files).** Bare `dict` / `tuple`
   annotations and `Returning Any` / untyped-`jnp.finfo` calls that needed the **same named-relaxation
   posture** `contract.py` / `exact_reference.py` already use (`dict[str, jax.Array]`, precise
   quantized-weight tuple types, `# type: ignore[no-any-return | no-untyped-call]`). **Annotations and
   `type: ignore` comments only — no executable code touched.** Proven by re-running the bench: every
   `max|Δ|` is bit-identical to the pre-edit run.
2. **`test_nla_lab.py::test_implemented_flag_marks_stub_vs_real` was a stale *build-phase* assertion.**
   It asserted the 7 portfolio variants were still unimplemented stubs (`IMPLEMENTED is False`) — the
   pre-fill bookkeeping. Filling them is the bake-off's deliverable, and the contract itself states
   "a real implementation flips it TRUE in its own variant file," so the test's premise is **inverted by
   completion, not violated**. Updated to the **post-fill invariant** (every registered portfolio variant
   is now `IMPLEMENTED=True` — catches a silent revert-to-stub) while **strengthening** the fill-state-
   independent half: a fresh `EncodeVariant` subclass that omits `IMPLEMENTED` still inherits the `False`
   default, proving the flag is a real per-variant opt-in, never vacuously true.

No fakes and no broken implementations were found among the 7 — every adversarial verification returned
**REAL + honest**. The only "break" was the stale scaffolding test above (updated, not deleted) and the
strict-typing gaps (fixed). `_smoke_broken` (the deliberately NaN/wrong-shape watchdog fixture) is
correctly caught by the bench and excluded from the portfolio sweep.

---

## Host follow-ups the maintainer must run

The CPU fixture proves **math correctness + structural fidelity + exact memory arithmetic**. It does
**not** prove deployment perf or real-trained-weight fidelity. The maintainer should run, on the host
(GPU + real weights):

1. **Representative GPU latency / throughput** for all 7 at the real coref geometry (latency lane:
   small-batch S≤512; throughput lane: `--batches 16 32 --seq-buckets 512 1024`). The CPU `p50/p95`
   columns here are launch-bound and are explicitly **not** the perf verdict — flash's S²-drop and the
   quantizers' compute win only show on device.
2. **Real-weight P6 fidelity for the two approximators that held an aggregate tier** —
   `w8a8_int8` (~3.5e-4) and `w4a16_weightonly` (~4e-3) — on `deberta-v3-large` / maverick-coref
   weights, and ideally the **fuller P6 comparable** (downstream coref cluster-set agreement, DESIGN §5):
   a small lhs Δ can still flip a cluster, so confirm the quant divergence does not move clusters.
3. **The distillation / fitting pass for the three structured operators** —
   `nystrom_attention`, `performer_favor`, `monarch_ffn`. Their fixture numbers are the soft-attention
   easy case; on trained weights they diverge (monarch's `‖M_proj−W‖≈49`; nystrom/performer's untrained
   stress divergence). Each names its precondition: landmark/feature re-fit or a Frobenius-distillation
   pass against the dense teacher. Re-measure P6 **after** fitting before promoting any of them — a
   retire-by-fit verdict here is a recorded datum, to be revisited only via that experiment.
