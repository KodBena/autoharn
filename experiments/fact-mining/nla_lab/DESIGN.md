# nla_lab — modular inference interface + auto-benchmark harness (DESIGN)

Status: **built and proven** (this directory). The contract, registry, auto-bench,
exact-reference, and the ≤8 portfolio stubs exist and pass; the follow-on agents fill
ONLY their math. Self-proof: `python -m nla_lab.bench --self-test` (CPU jax, no
download) and `python -m pytest -q nla_lab/test_nla_lab.py`.

This synthesizes the control_lab study (TAKE the uniform-interface + registry +
auto-bench + metrics + config-driven pattern; LEAVE the operational lapses) and the
inference-seam study (the single chokepoint is `jax_deberta.encode`). chocofarm ADRs
0000/0009/0012/0013 are law; each design decision below names the GATE it answers.

---

## 1. The implementation unit — a whole-encode swappable variant (the granularity decision)

**The unit is the whole encode `(params, input_ids, attention_mask, cfg) ->
last_hidden_state`, NOT "an attention op."** This is forced by the heterogeneity of
the portfolio: the eight candidates hook **four orthogonal internal seams**, and no
narrower type is common to all eight.

| Candidate | Internal seam it rewrites (jax_deberta.py) | Seam class |
| — | — | — |
| exact-reference (baseline) | delegates to `encode` (:352) | — (proof) |
| FlashAttention (exact) | score materialize+softmax+context in `_self_attention` (:248-258), folding `rel_att` from `_disentangled_bias` (:250) | attention |
| Nyström / Performer / Linformer | ONLY the content `softmax(q·kᵀ)` (:248-256); c2p/p2c kept exact | attention |
| cached-disentangled-positions | memoize `_disentangled_bias` body (:174-225) per `(cfg, s_bucket)` | position-cache |
| W8A8 / W4A16 quant | `_linear` (:115-117) at EVERY projection (q/k/v/dense/inter/output) | linear |
| Monarch / low-rank FFN | the FFN pair in `_layer` (:277-284) | FFN |

A "single attention op" type **cannot represent** a weight-quantizer (rewrites
`_linear`) or an FFN-replacer — adopting it would force an interface change the moment
those land: the **ADR-0013 "interface the real impls force-change" failure**. The
whole-encode boundary makes a non-conforming impl **unrepresentable** (ADR-0000):
whatever a candidate rewrites internally, it still IS a function
`(params, ids, mask, cfg) -> lhs`. Each variant owns its own internal decomposition;
the contract fixes only the outer boundary. The four seam classes are mechanically
demonstrated by the four stub families type-checking against the **unchanged**
contract (the conformance test, §7).

**GATE: ADR-0013** (the interface is complete for all 8 heterogeneous units with no
per-member side-channel) **+ ADR-0000** (a non-conforming impl is unrepresentable).

---

## 2. The typed contract (`contract.py`)

The call boundary is **identical to `jax_deberta.encode`'s signature** (jax_deberta.py:352)
— deliberately, so the exact-reference variant is a one-line delegation that proves the
contract is satisfiable and round-trips.

```python
class EncodeVariant(ABC):
    name: str                    # registry key (class attribute)
    regime: Regime               # LATENCY | THROUGHPUT | BOTH      (declared)
    fidelity_tier: FidelityTier  # EXACT | AGGREGATE_BEHAVIORAL     (declared)
    IMPLEMENTED: bool = False    # flip True in your file when encode is filled (R3-F5)
    partition_is_fidelity_preserving: bool = True  # input-partition inertness (declared, DEFAULTED)

    def __init_subclass__(cls, **kw):  # by-TYPE metadata guard (R1-G / ADR-0000):
        ...                            # a concrete subclass missing/mis-typing the three
                                       # REQUIRED above (name/regime/fidelity_tier) is
                                       # UNIMPORTABLE (TypeError at class-creation). The
                                       # DEFAULTED flags (IMPLEMENTED, partition_*) are NOT in
                                       # the required set — a default must not make a variant
                                       # unimportable.

    @abstractmethod
    def encode(self, params: dict[str, jax.Array], input_ids: jax.Array,
               attention_mask: jax.Array, cfg: jax_deberta.DebertaCfg) -> jax.Array: ...

    def fit(self, bucket: EncodeBucket) -> FitVerdict: ...   # a-priori retire gate

    def est_peak_device_bytes(self, bucket: EncodeBucket,            # the MEMORY dimension —
                              cfg: jax_deberta.DebertaCfg) -> int: ... # conservative DEVICE-byte
                                       # upper bound; DEFAULT reuses shape_buckets' ONE OOM model;
                                       # a profile-changing variant OVERRIDES (additive — does NOT
                                       # touch the frozen encode boundary)
```

- **Why an ABC + mypy `--strict`, not a `runtime_checkable` Protocol (B3).** A
  `runtime_checkable` Protocol checks only that method *names* exist at isinstance time
  — a wrong-arity `encode` is representable and detonates deep in the bench. The ABC
  makes a non-conforming impl unconstructable (the abstract method must be implemented),
  the exact 4-arg signature is checked by `mypy --strict` (`nla_lab/mypy.ini`), and the
  conformance test (§7) asserts every registered `encode`'s parameter list **equals
  `inspect.signature(jax_deberta.encode)`**. **GATE: ADR-0000 / ADR-0012 P8.**
- **Declared metadata, not call args (the two-tier bar).** `{regime, fidelity_tier}`
  are class metadata the registry lists and the bench records — never extra `encode`
  args. `fidelity_tier ∈ {exact(~1e-5), aggregate_behavioral(P6)}` is ADR-0009's
  two-tier bar; **bit-exactness binds nothing here (P6)**. **GATE: ADR-0009.**
- **Metadata enforced BY TYPE, not by convention (R1-G / ADR-0000).** `name`/`regime`/
  `fidelity_tier` were bare annotations — a concrete variant that forgot one was
  *representable* and only detonated at read time. `EncodeVariant.__init_subclass__` now
  asserts, for every CONCRETE subclass, that all three are set as class attributes AND
  correctly enum-typed (`name: str`, `regime: Regime`, `fidelity_tier: FidelityTier`),
  raising `TypeError` at **class-creation (import)** otherwise — a metadata-less variant
  is UNIMPORTABLE. It skips still-abstract intermediate bases and exempts `Decorated` &
  co. (`_metadata_is_dynamic = True`, which set the three per-INSTANCE). **GATE: ADR-0000.**
- **`IMPLEMENTED: bool` per-variant flag (R3-F5).** Defaults to `False` (a stub whose
  `encode` raises `NotImplementedError`); a real impl flips it `True` **in its own file**.
  The harness self-proof keys its expectation off THIS flag, not a global all-stub
  assumption — so one agent shipping their math never reds the shared `bench.self_test`
  for the other seven. `exact_reference.IMPLEMENTED = True`.
- **Prep memoization + return dtype (R1-C / R3-F6 — `encode` docstring contract).** A
  one-time per-variant weight transform (quant pack, Monarch/low-rank factor, the
  position-logit memo) MUST be memoized on `self` (the bench amortizes it via warmup, so
  re-transforming every forward silently inflates latency); `encode` MUST return the SAME
  dtype as `jax_deberta.encode` (the lhs dtype the decode tail consumes).
- **`fit_precondition` as the a-priori retire gate.** `fit(bucket) -> FitVerdict(ok,
  reason)` lets a variant retire itself below a crossover (Nyström/Performer `S >=
  512`) — recorded as a portfolio decision, not run as a bad number (the frontier creed:
  retire only by a failed experiment OR a stated structural mismatch).
- **`est_peak_device_bytes(bucket, cfg) -> int` — the MEMORY dimension (R-MEM).** The fourth
  benchmark axis alongside latency / throughput / fidelity: a CONSERVATIVE UPPER BOUND (never
  under — the same discipline as the OOM model) on the forward's peak VARIABLE (non-weight)
  **DEVICE** bytes at `bucket`. **DEVICE bytes only, NOT host RSS** (ratified): host RSS (parse
  + Python + GC) is a REQUEST-level cost, not a per-variant property, and stays the client's
  `--batch-size` knob; this axis is the per-variant device-activation cost the technique moves.
  The **DEFAULT reuses the ONE memory model** (ADR-0012 P1 — there is exactly one, in
  `shape_buckets`; this does NOT mint a second): it builds the dense deberta MemModel from `cfg`
  via `shape_buckets.dense_deberta_mem_model` (the cfg-only twin of
  `coref_host_shell.mem_model_from`, differing ONLY in the source of `intermediate` — the
  weight-derived exact width when params are in hand vs the canonical dense 4× ratio when only
  the cfg is known) and returns `shape_buckets.peak_variable_bytes(mm, B, S)`. **OVERRIDE
  MANDATE:** a variant whose technique CHANGES the variable-memory profile MUST OVERRIDE this so
  the estimate is not silently the dense bound — FlashAttention / Nyström / Performer drop the
  quadratic `[B,H,S,S]` term, W8A8 / W4A16 shrink `bytes_per_elem`, a structured/low-rank FFN
  shrinks `[B,S,intermediate]`, cached-positions reflects the retained position-logit buffer.
  Each profile-changing stub's docstring carries this mandate; the override stays a
  re-parameterised `MemModel` fed to `peak_variable_bytes`, NEVER a hand-rolled second model.
  **Additive**: it does not alter the frozen `encode` call boundary. **GATE: ADR-0012 P1 (one
  memory model) / ADR-0000 (conservative upper bound, never under).**
- **`partition_is_fidelity_preserving: bool = True` — input-partition inertness (declared).**
  TRUE for this whole stack: coref is **per-paragraph independent** (no cross-paragraph
  attention; each paragraph's clusters come from its own encode) and masked padding is inert, so
  the partition the host chooses for memory/throughput reasons cannot move a real token's
  encoder output — this inertness is the BASIS for the client's `--batch-size` knob and
  `shape_buckets.chunk_by_vram` / `encode_batch_chunks` being safe to apply at all. The contract
  CARRIES the distinction so a future **cross-chunk-dependent** model (a sliding-window /
  cross-paragraph-attention encode, where a partition boundary WOULD change a token's context)
  declares `False` and the host refuses to silently re-partition it. It is DECLARED metadata but
  DEFAULTED (safe), so — unlike `{name, regime, fidelity_tier}` — it is deliberately NOT in the
  `__init_subclass__` by-TYPE required set (a defaulted flag must never make an existing variant
  unimportable; the R1-G guard's required set is unchanged). **GATE: ADR-0000.**
- **`EncodeBucket(batch, seq_bucket)` validated against the `shape_buckets` ladders.**
  Its `__post_init__` asserts `seq_bucket ∈ ENCODE_LEN_BUCKETS` and `batch ∈
  ENCODE_BATCH_BUCKETS` — an off-ladder shape is **unconstructable** (ADR-0000), sourced
  FROM the SSOT, never a re-typed second ladder. **GATE: ADR-0012 P1.**
- **`Decorated` meta-wrapper (A11 completeness lever).** Wraps ANY variant uniformly
  (same contract in/out) delegating `encode`/`fit`. The conformance test proves
  `Decorated(ExactReference())` is bit-identical — if a `Cached`/`Quantized`/`Guarded`
  decorator can compose over any variant with zero interface change, the interface is
  complete; if it could not, it is incomplete (ADR-0013).

---

## 3. Bucketing reuse — UPSTREAM, no fork (the placement decision)

The variant receives **already-bucketed, already-padded `[B, s_bucket]`** arrays. The
host shell (`coref_host_shell.encode_lhs` / `iter_encode_lhs_batched`) owns
`shape_buckets.bucket_len` / `pad_to` / the OOM B-ladder. A variant MUST NOT re-pad or
re-bucket; it MAY read `s_bucket = input_ids.shape[1]` as a cache key (the
position-cacher needs it) but does not own the ladder. The bench's corpus
(`lab_corpus.py`) pads via the ONE `shape_buckets.pad_to`; `EncodeBucket` validates
against the ladders; `rel_pos` stays each variant's internal detail (via the un-forked
`jax_deberta.build_relative_position`). This is the only way to reuse `shape_buckets`
and `jax_deberta` as SSOT without forking them. **GATE: ADR-0012 P1 (one home).**

---

## 4. The registry (`registry.py`) — the parallel-fan-out enabler

Ported verbatim from control_lab's good core, with its lapses left:

- **`REGISTRY: dict[str, Callable[[], EncodeVariant]]`** — the real factory type, NOT
  `Factory = Any` (control_lab's erasure). `mypy --strict` checks it. **GATE: ADR-0012 P8 (B2).**
- **Self-registration** — each variant appends itself at module bottom via
  `@register` (`REGISTRY.setdefault`, clash-loud). ONE variant = ONE file + ONE entry,
  ZERO edits to shared files.
- **DEFERRED discovery** — `load_all()` `pkgutil.iter_modules` over `variants/` and
  imports each ONCE, called by the harness, NOT at package import. Importing one variant
  for its unit test does not pull siblings; a half-written sibling cannot break
  another's test. This is what lets ≤8 agents work in parallel.
- **Fail-loud resolution** — `resolve` raises `KeyError` listing known names (refusing
  to guess, ADR-0002); `make` type-checks the factory output. **GATE: ADR-0002 (A5).**
- `portfolio_names()` excludes `_`-prefixed fixtures (the watchdog smoke variant).

---

## 5. The auto-benchmark runner (`bench.py` + `lab_report.py` + `lab_corpus.py` + `lab_measure.py`)

Split into one-owner collaborators (NOT control_lab's ~720-line god-file, B6):
runner (`bench.py`) · scorer+schema+sinks (`lab_report.py`) · corpus
(`lab_corpus.py`) · device measurement core (`lab_measure.py`).

**Sweep (A6/A7).** For each variant over `(batch ∈ ENCODE_BATCH_BUCKETS, seq_bucket ∈
ENCODE_LEN_BUCKETS)`: check `fit` (record `fit_retired` if it declines), else load the
warm fixture ONCE, compile-once + warm-time the **run-only** forward, and compute P6
fidelity vs the exact reference. **Honest compile/run separation:** `warm_time_seconds`
pays compile+warmup forwards first (discarded), then times `repeats` run-only forwards,
each ended by `block_until_ready` so the wall window encloses real device work — warm,
compile excluded by construction. **GATE: ADR-0009.**

**Three distinct lanes, never collapsed (B10).** `lab_report.BenchRecord` carries all of:
- **latency lane** — `lat_p50_ms / p95 / min / mean` over the warm sample (the hook
  workload, small B);
- **throughput lane** — `rows_per_s` = real-rows / warm-median (compute-bound, large B);
- **memory lane** — `est_peak_device_bytes` (the `devMiB` column), the variant's DECLARED
  conservative upper bound on the forward's peak VARIABLE (non-weight) device bytes at `(B,
  s_bucket)` (`EncodeVariant.est_peak_device_bytes`, §2). It is the **declared estimate** (the
  contract dimension the portfolio compares on), not a live device measurement — recorded on
  EVERY record, including non-ok (fit_retired / not_implemented / failed) rows, since it is an
  a-priori quantity. It is the dense-reference bound (`shape_buckets.peak_variable_bytes`) unless
  a profile-changing variant overrides it. A live `jax memory_stats` measured-vs-estimate column
  is a possible future add (`lab_measure` already touches device memory), but the estimate is
  what the portfolio ranks on. **GATE: ADR-0009 (measured/declared dimensions) / ADR-0012 P1.**

Robust stats (`agg` → p50/p95/min/mean/n), never one eyeballed number (A7 /
robust-benchmark-statistics).

**Fidelity lane vs the exact reference (B11 — the abstraction control_lab lacks).**
The bench runs `exact_reference` once per `(B, s_bucket)`, caches its lhs, and scores
every variant's `max|Δ|` / `mean|Δ|` over REAL tokens (`lab_measure.fidelity_delta`),
the **P6 aggregate-behavioral** bar (ADR-0009 tier-2; the same real-token convention as
`test_deberta_fidelity._run_pair`). The reference's fidelity-vs-itself is **exactly
0.0** — the self-proof. **Measured scope (stated loudly).** The lane scores
encoder-`last_hidden_state` aggregate distance ONLY. Cluster-set agreement is the
FULLER P6 comparable for this coref stack and is DEFERRED until a variant feeds the
decode tail: a perturbation the Maverick decode amplifies into a different cluster set
can show a small lhs `max|Δ|` and escape this lane, so the shipped lane is a proxy one
boundary upstream of the decision that ultimately matters. lhs-level aggregate distance
is the right (and sufficient) scope for the harness self-proof and the encoder-only
bench; an approximate variant accepted on fidelity grounds must be re-checked against
cluster-set agreement before it is trusted downstream. Note too that the declared
`fidelity_tier` is RECORDED and the measured Δ is REPORTED, but the harness does not
itself assert the measured Δ against the declared tier (a mis-declared tier is a
finding authored elsewhere, ADR-0009 measurement-vs-interpretation) — `fidelity_tier`
is a label, not a gate. **GATE: ADR-0009 two-tier bar.**

**Safety envelope (A10) — a bad variant cannot tear down the fixture, and a bench
FAILURE is recorded, not substituted (B8).** Every variant call is wrapped: a
`NotImplementedError` → `not_implemented`; any other exception → `failed_error`; a
wrong-shape output → `failed_shape`; a NaN/Inf output → `failed_nonfinite`
(`lab_measure.guard_output`, the ONE shape+finiteness contract, the watchdog's single
home). The sweep CONTINUES; the warm `params` fixture is loaded once and never torn
down. In a BENCH lane numerical misbehavior is a LOUD recorded failure, never a
clamped low score. **GATE: ADR-0002.** The deliberately-broken `_smoke_broken` variant
proves the guard fires.

**Reproducible corpus (B9).** `lab_corpus.make_batch(batch, seq_bucket, vocab, seed)`
builds the input deterministically from a seed (re-runnable on the guest with CPU jax),
padded by the ONE `shape_buckets.pad_to` — replacing control_lab's live
taskset-pinned C++ producer + redis stream. **GATE: ADR-0009 reproducibility.**

**One bench/trace home (B2).** Each `BenchRecord` is recorded to the `trace.span` store
via `spans.get_tracer()` (the SSOT tracer) at the between-trial seam, off the timed
path (A12), and mirrored to a local JSONL belt-and-suspenders. No second bench/registry
store is minted (the ADR-0009 measurement-vs-finding split: a reading is immutable, a
perf claim is a supersedable finding authored elsewhere). **GATE: ADR-0012 P1.**

---

## 6. Host-XOR-device file layout (`test_import_xor.py` + `test_device_transfers.py`)

| File | Side | Imports | Role |
| — | — | — | — |
| `contract.py` | neutral (type-only jax under TYPE_CHECKING) | stdlib + shape_buckets | the typed ABC |
| `registry.py` | host | stdlib | name→factory + deferred discovery |
| `lab_corpus.py` | host | stdlib + shape_buckets | seeded reproducible corpus |
| `lab_report.py` | host | stdlib + spans | record schema, stats, sinks |
| `bench.py` | host | stdlib + shape_buckets (+deberta_weights boundary) | the runner |
| `lab_measure.py` | **device** | jax only (numpy-free) | the one device shell: lift + warm-time + guard + fidelity |
| `variants/*.py` | **device** | jax + jax_deberta | the variant math (one file each) |

- **Device math in device files (B12).** Every jax op the bench needs lives in
  `lab_measure.py` (the device shell, analogous to `coref_host_shell`); the
  registry/runner/report/corpus are host and import no jax/numpy. The fidelity `max|Δ|`
  is computed device-side and only scalars cross to the host report (exactly as
  `coref_decode_server` delegates device lifts to `coref_host_shell`). `bench.py` holds
  `params`/`cfg` as **opaque object handles** (typed `dict[str, object]` / `object`),
  passing them through to `lab_measure`; the one host→device cast is named at the
  fixture boundary.
- **Gate updates (so the gate does not go blind, B12).** All nla_lab files are added to
  `test_import_xor.py:SCANNED` (host orchestration → neutral; device math → jax-only,
  numpy-free; none mixing). `lab_measure.py` is registered as nla_lab's **single jax
  host↔device home** in `test_device_transfers.py:HOMES["jax"]` (one home per
  subsystem; its lift + `block_until_ready` carry the `# host-device-boundary:` marker),
  and the variant files + contract are scanned there to PROVE the jax edge stays
  single-homed in `lab_measure` and did not leak into a variant. **GATE: ADR-0012 P7 +
  the workspace import-XOR / device-transfer gates.**
- **Typed-contract gate.** `nla_lab/mypy.ini` runs `mypy --strict` over the package;
  `jax` is real (it ships `py.typed`); the only relaxations are the pre-existing UNTYPED
  local workspace deps (`jax_deberta`/`shape_buckets`/`spans`/`deberta_weights`),
  declared `follow_imports = skip` per the P8 named-stub-gap posture + ADR-0004
  no-retroactive-sweep. **GATE: ADR-0012 P8.**

---

## 7. The exact-reference + the ≤8 stubs + the conformance proof

- **`variants/exact_reference.py`** — the REQUIRED baseline (A8): `encode` delegates
  straight to `jax_deberta.encode`. Its fidelity-vs-itself is 0 by construction; if it
  resolves through the registry, runs through the bench, and reports `max|Δ| == 0`, the
  whole contract+registry+bench is proven end to end (ADR-0013 "prove it with a working
  impl that round-trips"). Its vs-vanilla-HF ~1e-3 bar is the existing
  `test_deberta_fidelity.py` gate (same `jax_deberta.encode` — no second fidelity claim
  minted).
- **The ≤8 stub slots** — `flash_attention` · `cached_positions` · `nystrom_attention`
  · `performer_favor` · `w8a8_int8` · `w4a16_weightonly` · `monarch_ffn` (the seven
  portfolio candidates) each in its own file, declaring `{regime, fidelity_tier}` and
  (Nyström/Performer) a `fit` crossover, with the math a `NotImplementedError` naming the
  technique + the seam line + the portfolio §. The follow-on agent fills ONLY `encode`.
- **`variants/_smoke_broken.py`** — the deliberately-broken watchdog (A10), `_`-prefixed
  (excluded from the sweep), returns wrong-shape NaN to prove the guard flags a failure.
- **`test_nla_lab.py` (mechanizes B4 — a conformance test, not a docstring).** Asserts:
  the self-proof; every registered variant is a by-TYPE `EncodeVariant` whose `encode`
  parameter list **equals `jax_deberta.encode`'s**; `Decorated` composition is
  bit-identical (A11); off-ladder `EncodeBucket` is unconstructable; the registry is
  fail-loud; the by-TYPE metadata guard FIRES on a dynamically-built metadata-less subclass
  (R1-G, non-vacuous) and exempts the abstract/dynamic cases; and the `IMPLEMENTED` flag
  marks exact_reference real and the seven stubs as stubs (R3-F5). This is the "follow-on
  needs zero interface changes" check: the ≤8 stubs type-check against the unchanged
  contract and the exact-reference round-trips today.

**Proven self-test output** (synthetic fixture, CPU jax — the harness self-proof):

```
variant            regime       B  Sbkt     p50ms     p95ms     rows/s     max|Δ|     devMiB           status
exact_reference    both         1    64     1.088     1.094      919.4   0.00e+00       0.39               ok
exact_reference    both         2   128     1.891     1.960     1057.7   0.00e+00       2.56               ok
flash_attention    both         1    64         —         —          —          —       0.39  not_implemented
nystrom_attention  throughput   1    64         —         —          —          —       0.39      fit_retired
_smoke_broken      both         1    64         —         —          —          —       0.39     failed_shape
...

status legend:
  fit_retired      an a-priori portfolio decision (e.g. Nyström/Performer below S>=512),
                   NOT a broken impl — raise --seq-buckets to exercise it.
  not_implemented  a stub: the EXPECTED pre-fill state until the agent fills the math.
devMiB:            the variant's DECLARED conservative UPPER BOUND on the forward's peak
                   VARIABLE (non-weight) DEVICE bytes (the memory lane) — dense bound by
                   default; a profile-changing variant overrides it. Recorded even for non-ok.
regime coverage: the default (batch 1-2 x seq 64-128) is the CPU self-test geometry
  (LATENCY lane). The THROUGHPUT lane + the S>=512 fit window need a larger sweep, e.g.
  --batches 16 32 --seq-buckets 512 1024.

SELF-TEST PASS: exact_reference round-trips (fidelity-vs-self==0), watchdog flags the
broken variant, all stubs are not_implemented.
```

A `fit_retired` / `not_implemented` row is therefore an EXPECTED state, printed with a
legend (`lab_report.status_legend`), never to be misread as "my impl is broken"; and
the throughput regime (the second half of the regime axiom) is reached only by the
larger sweep above — the default deliberately stays in the fast latency-lane geometry.

---

## 8. AUDIT — does this resurface a documented failure? (each with its GATE)

1. **A by-convention-not-by-type contract** → NO. `EncodeVariant` is a typed ABC whose
   `encode` has exactly `jax_deberta.encode`'s signature; non-conforming is
   unrepresentable; proven by `mypy --strict` + the exact-reference round-trip + the
   signature-equality conformance test. **GATE: ADR-0000 / ADR-0012 P8.** (Avoids
   control_lab's `runtime_checkable` + frozen-by-comment — B3 — and `Factory = Any` — B2.)
2. **A second benchmark/registry home** → NO. The bench routes through
   `spans.get_tracer()` (the one trace store) and the one `REGISTRY`; no forked store.
   **GATE: ADR-0012 P1.**
3. **Device code in a host file** → NO. Device math is confined to `lab_measure.py` +
   the variant files (jax-only, numpy-free); registry/runner/report/corpus are host; all
   added to both gates' scan lists so coverage is not blind. **GATE: import-XOR +
   device-transfer gates (B12).**
4. **An unmeasured perf claim** → NO. The bench MEASURES warm latency/throughput per
   `(B, s_bucket)` with compile separated from run; no asserted speedups; the
   reference's fidelity-vs-self == 0 is the self-proof; readings are immutable, perf
   claims are supersedable findings. **GATE: ADR-0009 / P6.**
5. **An interface the real impls force-change** → NO. §1's seam table proves all 8 share
   the outer type while touching four distinct inner seams; the ≤8 stubs type-check
   against the **unchanged** contract today and the exact-reference round-trips — the
   "follow-on needs zero interface changes" check is mechanized by `test_nla_lab.py`.
   **GATE: ADR-0013.**

And the control_lab lapses left behind: misplacement under a misleading parent (B1 — we
sit next to `jax_deberta.py`); the god-file harness (B6 — split runner/scorer/report);
SSOT-dissolved copy-paste `_fit` (B7 — bucketing validated once at the boundary,
`EncodeBucket`); silent defensive coercion on the scored path (B8 — fidelity failures
are loud); the speculative dead `TrainableRecipe` arm (B5 — the contract carries no
member-specific side-channel; every candidate satisfies the same `encode`); magic
constants (B13 — crossovers/ladders are named, config-derived, one home).
