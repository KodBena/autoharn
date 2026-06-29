#!/usr/bin/env python
"""Guest gates for the SHAPE-BUCKET compile bound + its fidelity (ADR-0000 / ADR-0009).

The unified jax-only coref daemon leaked host RAM unbounded (>7GB -> OOM) because JAX
retains one compiled executable per distinct input shape, forever, and the shapes were
UN-bucketed (encode per raw S, decode per data-dependent S/K/P). `shape_buckets` draws
every traced shape from a FIXED finite ladder; this file is the MEASURED proof that the
fix bounds the distinct-compile count AND keeps the result bit-identical.

Three guest-provable claims (the host --coref-verify confirms the end-to-end cluster
identity on maverick's real fine-tuned weights, which the guest cannot run):

  (c) THE LEAK GATE (ADR-0009 measured): over a spread of MANY distinct shapes the
      distinct-compile count is bounded by the LADDER size, not the request count. Each
      bound test FIRST measures the un-bucketed leak (compiles == #distinct shapes) and
      THEN the bucketed path (compiles <= #buckets < leak) — so the bound is non-vacuous
      and the test FAILS on un-bucketed code (which has no `encode_lhs` and leaks).
  (a) ENCODE inertness: bucketed-then-sliced encode == unpadded encode over real
      positions, within the ADR-0009 float tier (~1e-5; the lhs is a 24-layer fp32
      aggregate, so the bar is a tolerance, NOT bit-identity).
  (b) DECODE cluster bit-exactness: the discrete cluster SETS are IDENTICAL bucketed vs
      un-bucketed (the logic-invariant tier — asserted exactly).
  + the REL-POSITION HOIST licence: build_relative_position is bit-identical eager vs
      jitted across the whole ladder, so hoisting rel_pos out of the baked per-executable
      constant changes the attention math by zero.

Imports torch+transformers ONLY inside the optional real-deberta test; the core gates
run on a tiny random model and pure jax, so they need no network. Not part of the
composed device pipeline -> not scanned by the import-XOR gate.

Run:  . ~/w/vdc/venvs/generic/bin/activate && python -m pytest test_shape_bucket_compile_bound.py -q
"""

from __future__ import annotations

import os

import jax
import jax.numpy as jnp
import numpy as np
import pytest

jax.config.update("jax_enable_x64", False)

import coref_host_shell as H
import jax_deberta as JD
import jax_decode as DEC
import shape_buckets as SB


# ----------------------------------------------------------------- tiny models
def _tiny_cfg() -> JD.DebertaCfg:
    """A small real-architecture DeBERTa config (2 layers) — the compile COUNT is a
    function of shapes, not weights, so a tiny model measures the bound faithfully and
    fast, and the masked-padding inertness it also proves is architecture-agnostic (the
    same `emb*mask` + masked attention path the full model runs)."""
    return JD.DebertaCfg(
        num_layers=2, num_heads=2, head_size=8,
        position_buckets=16, max_relative_positions=32, pos_ebd_size=16,
        scale_factor=3, has_c2p=True, has_p2c=True, layer_norm_eps=1e-7)


VOCAB = 50


def _tiny_deberta_params(cfg: JD.DebertaCfg, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    H_ = cfg.num_heads * cfg.head_size
    inter = 2 * H_

    def arr(*shape):
        return jnp.asarray((rng.standard_normal(shape) * 0.02).astype("float32"))

    p = {
        "embeddings.word_embeddings.weight": arr(VOCAB, H_),
        "embeddings.LayerNorm.weight": jnp.asarray(np.ones(H_, "float32")),
        "embeddings.LayerNorm.bias": arr(H_),
        "encoder.rel_embeddings.weight": arr(2 * cfg.pos_ebd_size, H_),
        "encoder.LayerNorm.weight": jnp.asarray(np.ones(H_, "float32")),
        "encoder.LayerNorm.bias": arr(H_),
    }
    for i in range(cfg.num_layers):
        b = f"encoder.layer.{i}."
        for sub in ("attention.self.query_proj", "attention.self.key_proj",
                    "attention.self.value_proj", "attention.output.dense"):
            p[b + sub + ".weight"] = arr(H_, H_)
            p[b + sub + ".bias"] = arr(H_)
        p[b + "attention.output.LayerNorm.weight"] = jnp.asarray(np.ones(H_, "float32"))
        p[b + "attention.output.LayerNorm.bias"] = arr(H_)
        p[b + "intermediate.dense.weight"] = arr(inter, H_)
        p[b + "intermediate.dense.bias"] = arr(inter)
        p[b + "output.dense.weight"] = arr(H_, inter)
        p[b + "output.dense.bias"] = arr(H_)
        p[b + "output.LayerNorm.weight"] = jnp.asarray(np.ones(H_, "float32"))
        p[b + "output.LayerNorm.bias"] = arr(H_)
    assert set(p) == JD.param_keys(cfg)  # bijection with the forward's read-set
    return p


# decode-tail dims (free, kept tiny & consistent)
TH, R, F = 16, 8, 4  # hidden, token-rep dim, coref-feature dim
NC = DEC.NUM_CATS


def _tiny_decode_params(seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)

    def lin(o, i):
        return (jnp.asarray(rng.standard_normal((o, i)).astype("float32")),
                jnp.asarray(rng.standard_normal((o,)).astype("float32")))

    def fc(prefix, i, o, h):
        d = {}
        w1, b1 = lin(h, i)
        w2, b2 = lin(o, h)
        d[prefix + ".dense1.weight"], d[prefix + ".dense1.bias"] = w1, b1
        d[prefix + ".layer_norm.weight"] = jnp.asarray(np.ones(h, "float32"))
        d[prefix + ".layer_norm.bias"] = jnp.asarray(np.zeros(h, "float32"))
        d[prefix + ".dense.weight"], d[prefix + ".dense.bias"] = w2, b2
        return d

    p: dict = {}
    p.update(fc("start_token_classifier", TH, 1, TH))
    p.update(fc("start_token_representation", TH, R, TH))
    p.update(fc("end_token_representation", TH, R, TH))
    p.update(fc("start_end_classifier", 2 * R, 1, TH))
    p.update(fc("coref_start_all_mlps", TH, NC * F, TH))
    p.update(fc("coref_end_all_mlps", TH, NC * F, TH))
    for nm in ("s2s", "s2e", "e2s", "e2e"):
        p[f"antecedent_{nm}_all_weights"] = jnp.asarray(
            rng.standard_normal((NC, F, F)).astype("float32"))
        p[f"antecedent_{nm}_all_biases"] = jnp.asarray(
            rng.standard_normal((NC, F)).astype("float32"))
    return p


def _synthetic_doc(S: int, seed: int):
    rng = np.random.default_rng(seed)
    lhs = jnp.asarray(rng.standard_normal((S, TH)).astype("float32"))
    eos = [[1 if j >= i else 0 for j in range(S)] for i in range(S)]  # upper-tri
    tokens = [f"w{i}" for i in range(S)]
    sub = list(range(S))
    ntm = list(range(S))
    return lhs, eos, tokens, sub, ntm


def _cluster_sets(clusters):
    """Order-independent normal form: a set of clusters, each a frozenset of spans."""
    return frozenset(frozenset(c) for c in clusters)


# =============================================================== rel-pos hoist
def test_relpos_hoist_bit_identical():
    """The licence for the rel-position hoist (frugality, fidelity-NEUTRAL). rel_pos is
    now a RUNTIME arg to `_encode_core` rather than a baked compile-time constant; that is
    fidelity-neutral iff the array is bit-identical whether computed eager or jitted. The
    encode consumes it only via integer clip + take_along_axis, so a bit-identical array
    -> bit-identical attention. Probe the whole ladder incl. the float-log path (S>mid)
    and the clip regime (S>max_relative_positions)."""
    PB, MR = 256, 512
    jit_brp = jax.jit(JD.build_relative_position, static_argnums=(0, 1, 2))
    for s in (12, 64, 128, 129, 256, 400, 512, 513, 768, 1024, 2048):
        eager = np.asarray(JD.build_relative_position(s, PB, MR))
        jitd = np.asarray(jit_brp(s, PB, MR))
        assert np.array_equal(eager, jitd), f"rel_pos diverged eager vs jit at S={s}"


# =============================================================== (c) leak gate
def test_encode_compile_bound():
    """ENCODE leak gate (the 7GB). Drive a spread of distinct lengths spanning only a few
    ladder rungs: un-bucketed compiles once per distinct length (the leak), bucketed
    compiles at most once per rung. FAILS on un-bucketed code (no encode_lhs / one big
    executable per length)."""
    cfg = _tiny_cfg()
    params = _tiny_deberta_params(cfg)
    lengths = [50, 57, 60, 63, 70, 88, 99, 120, 127, 130, 200, 250, 60, 88]  # rungs {64,128,256}
    rungs = sorted({SB.bucket_len(n, SB.ENCODE_LEN_BUCKETS) for n in lengths})
    distinct = len(set(lengths))

    # un-bucketed reference: the leak — one compile per distinct raw length
    JD._encode_core.clear_cache()
    for n in lengths:
        ids = jnp.ones((1, n), dtype=jnp.int32)
        mask = jnp.ones((1, n), dtype=jnp.int32)
        JD.encode(params, ids, mask, cfg)
    leak = JD._encode_core._cache_size()
    assert leak == distinct, f"expected un-bucketed leak == {distinct} distinct lengths, got {leak}"

    # bucketed path: compiles bounded by the ladder rungs touched
    JD._encode_core.clear_cache()
    for n in lengths:
        lhs = H.encode_lhs(params, cfg, [1] * n, [1] * n)
        assert lhs.shape == (n, cfg.num_heads * cfg.head_size)  # sliced back to real S
    bounded = JD._encode_core._cache_size()
    assert bounded <= len(rungs), f"bucketed compiles {bounded} > #rungs {len(rungs)}"
    assert bounded < leak, f"bound is vacuous: bucketed {bounded} !< leak {leak}"


def test_decode_compile_bound():
    """DECODE leak gate (the perpetual tail). Drive many docs of distinct S (-> distinct
    K and P); each of the three decode jits must compile a count bounded by its ladder,
    not by the request count."""
    params = _tiny_decode_params()
    s_values = list(range(24, 24 + 3 * 16, 3))  # 16 distinct S
    for jit in (DEC.mention_start_keep, DEC.span_mention_keep, DEC.coref_decode):
        jit.clear_cache()

    seen_s, seen_p, seen_k = set(), set(), set()
    for idx, S in enumerate(s_values):
        lhs, eos, toks, sub, ntm = _synthetic_doc(S, seed=100 + idx)
        # mirror the shell's shape choices to compute the expected bucket sets
        seen_s.add(SB.bucket_len(S, SB.ENCODE_LEN_BUCKETS))
        H.decode_document(params, lhs, [1] * S, eos, toks, sub, ntm)

    # mention_start_keep compiles per S-bucket
    msk = DEC.mention_start_keep._cache_size()
    assert msk <= len(seen_s) <= len(SB.ENCODE_LEN_BUCKETS)
    assert msk < len(s_values), f"start-keep compiles {msk} not below #requests {len(s_values)}"
    # coref_decode compiles per K-bucket
    cd = DEC.coref_decode._cache_size()
    assert cd <= len(SB.DECODE_K_BUCKETS), f"coref_decode compiles {cd} > K-ladder"
    assert cd < len(s_values), f"coref_decode compiles {cd} not below #requests"
    # span_mention_keep compiles per (S-bucket, P-bucket) combination — still bounded
    smk = DEC.span_mention_keep._cache_size()
    assert smk <= len(SB.ENCODE_LEN_BUCKETS) * len(SB.DECODE_P_BUCKETS)


# =============================================================== (a) encode inertness
def test_encode_bucketed_equals_unpadded_tiny():
    """Masked-padding inertness on the tiny real-architecture model: bucketed-then-sliced
    encode == unpadded encode over every real position, within the ADR-0009 float tier."""
    cfg = _tiny_cfg()
    params = _tiny_deberta_params(cfg)
    rng = np.random.default_rng(7)
    worst = 0.0
    # straddle EVERY rung incl. >512 (the shipped coverage stopped at 250 and never
    # exercised a doc past the 512 rung — the inertness property holds the whole ladder).
    for n in (30, 65, 100, 130, 250, 511, 513, 768, 1024):
        ids = [int(x) for x in rng.integers(0, VOCAB, size=n)]
        mask = [1] * n
        unpadded = np.asarray(JD.encode(params, jnp.asarray([ids]), jnp.asarray([mask]), cfg)[0])
        bucketed = np.asarray(H.encode_lhs(params, cfg, ids, mask))
        assert bucketed.shape == unpadded.shape
        worst = max(worst, float(np.abs(bucketed - unpadded).max()))
    # tightened from 1e-4 to the PROVEN ~1e-5 tier (measured max|Δ| ~3.6e-7 on this
    # real-architecture model — the masked-padding is inert to within XLA float noise).
    assert worst < 1e-5, f"bucketed-vs-unpadded encode max|Δ|={worst:.2e} exceeds 1e-5"
    print(f"\n[encode inertness tiny] max|Δ| real positions = {worst:.2e}")


@pytest.mark.skipif(os.environ.get("COREF_SKIP_REAL_DEBERTA") == "1",
                    reason="real deberta-v3-large encode-fidelity disabled")
def test_encode_bucketed_equals_unpadded_real_deberta():
    """The convincing fidelity proof on the REAL deberta-v3-large weights (HF-cached):
    bucketed-then-sliced == unpadded over real positions within the float tier. Skips if
    the model/weights are unavailable on this guest."""
    try:
        from transformers import AutoTokenizer
        from deberta_weights import load_jax_deberta
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"transformers/deberta weights unavailable: {e!r}")
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    try:
        params, cfg, _ = load_jax_deberta("microsoft/deberta-v3-large")
        tok = AutoTokenizer.from_pretrained("microsoft/deberta-v3-large")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"could not load real deberta: {e!r}")
    sentences = [
        "The cat sat on the mat because it was warm.",
        "Marie Curie discovered radium; she won two Nobel Prizes for her research over many years.",
    ]
    worst = 0.0
    for s in sentences:
        enc = tok(s, return_tensors="np")
        ids = [int(x) for x in enc["input_ids"][0]]
        mask = [int(x) for x in enc["attention_mask"][0]]
        unpadded = np.asarray(JD.encode(params, jnp.asarray([ids]), jnp.asarray([mask]), cfg)[0])
        bucketed = np.asarray(H.encode_lhs(params, cfg, ids, mask))
        worst = max(worst, float(np.abs(bucketed - unpadded).max()))
    assert worst < 1e-4, f"real-deberta bucketed-vs-unpadded max|Δ|={worst:.2e} exceeds 1e-4"
    print(f"\n[encode inertness real deberta-v3-large] max|Δ| = {worst:.2e}")


# =============================================================== (b) decode bit-exact
def test_decode_cluster_sets_bucketed_equals_unbucketed(monkeypatch):
    """The discrete logic invariant (ADR-0009 tier-1): the cluster SETS are IDENTICAL
    bucketed vs un-bucketed. The un-bucketed reference is produced by monkeypatching
    `shape_buckets.bucket_len` to the identity (round to the exact length -> pad_to is a
    no-op, jnp.pad adds zero rows) — reproducing the original per-raw-shape decode — then
    the real ladder bucketing is run on the SAME inputs and the cluster sets compared."""
    params = _tiny_decode_params()
    cases = [(S, 200 + S) for S in (18, 27, 33, 41, 55, 70)]  # varied S incl. cross-bucket K/P

    def run(singletons):
        out = []
        for S, seed in cases:
            lhs, eos, toks, sub, ntm = _synthetic_doc(S, seed)
            out.append(_cluster_sets(
                H.decode_document(params, lhs, [1] * S, eos, toks, sub, ntm, singletons=singletons)))
        return out

    for singletons in (False, True):
        # un-bucketed reference (identity ladder)
        monkeypatch.setattr(SB, "bucket_len", lambda n, ladder: n)
        ref = run(singletons)
        monkeypatch.undo()
        # real bucketed path
        got = run(singletons)
        for (S, _), r, g in zip(cases, ref, got):
            assert r == g, f"cluster sets differ bucketed vs un-bucketed at S={S}, singletons={singletons}"
    # non-vacuity: at least one case yields a real (>=2-mention) cluster
    any_multi = any(len(c) >= 2 for cs in run(False) for c in cs)
    assert any_multi, "VACUOUS: no >=2-mention cluster exercised — strengthen the fixture"


# ===================================================== (BATCHED ENCODE) the bucket-group
# encode by bucket-group collapses the per-text B=1 forwards into ONE [B, s_bucket] forward
# per (length-bucket, fixed-B) chunk. Three guest-provable claims mirror the per-text ones:
#   (a) batched-then-sliced encoder lhs == per-text encode_lhs (within the ~1e-5 float tier);
#   (b) the (B, s_bucket) compile grid stays BOUNDED over a spread of (B, S) — B is drawn
#       from a fixed ladder and is single-valued per s_bucket, so the leak gate still holds;
#   (c) the cluster SETS through the full coref path are bit-identical batched vs per-text.
class _Doc:
    """A synthetic per-doc input (duck-typed DecodeInputs) for the batched coref path:
    real token ids (so the encode actually runs) + the structural decode maps."""
    def __init__(self, S: int, seed: int):
        rng = np.random.default_rng(seed)
        self.input_ids = [int(x) for x in rng.integers(0, VOCAB, size=S)]
        self.attention_mask = [1] * S
        self.eos_mask = [[1 if j >= i else 0 for j in range(S)] for i in range(S)]
        self.tokens = [f"w{i}" for i in range(S)]
        self.subtoken_map = list(range(S))
        self.new_token_map = list(range(S))


def test_encode_batched_equals_per_text():
    """(a) Masked DUMMY-row + col padding is INERT to real rows: the bucket-group batched
    encode (encode_lhs_batched) sliced back per doc == the per-text encode_lhs (B=1) over
    every real position, within the ADR-0009 float tier. Drive a spread of S spanning
    several rungs AND group sizes that force remainder chunks (the last chunk padded up to B
    with masked dummy rows) — the case where batch-axis inertness is load-bearing."""
    cfg = _tiny_cfg()
    params = _tiny_deberta_params(cfg)
    # mixed S across rungs {64,128,256}; sizes chosen so groups have remainders under B.
    Ss = [30, 31, 32, 100, 101, 102, 103, 200, 250, 33, 34, 99]
    docs = [_Doc(S, seed=400 + i) for i, S in enumerate(Ss)]
    # small budget -> small B per bucket -> multiple chunks + remainders exercised.
    batched = H.encode_lhs_batched(
        params, cfg, [d.input_ids for d in docs], [d.attention_mask for d in docs],
        max_padded_tokens=256, max_docs=64)
    worst = 0.0
    for d, lhs_b in zip(docs, batched):
        per_text = np.asarray(H.encode_lhs(params, cfg, d.input_ids, d.attention_mask))
        lhs_b = np.asarray(lhs_b)
        assert lhs_b.shape == per_text.shape == (len(d.input_ids), cfg.num_heads * cfg.head_size)
        worst = max(worst, float(np.abs(lhs_b - per_text).max()))
    assert worst < 1e-5, f"batched-vs-per-text encode max|Δ|={worst:.2e} exceeds 1e-5"
    print(f"\n[encode batched==per-text] max|Δ| real positions = {worst:.2e}")


def test_encode_batch_compile_bound():
    """(b) THE LEAK GATE for the batch axis (WITHIN one call). Batching by bucket-group must
    NOT re-leak the cache the length-ladder just bounded: B is drawn from the finite
    ENCODE_BATCH_BUCKETS ladder, so the (B, s_bucket) compile grid is bounded — NOT by the
    number of distinct (real chunk size, s_bucket) shapes a VARIABLE-B encode would mint.
    First measure that variable-B leak, then the bounded batched path, and assert the bound is
    non-vacuous (bucketed < leak).

    SCOPE of this gate: ONE call at a SATURATING budget (max_padded_tokens=256), where each
    s_bucket appears as exactly one group and the small budget pins B at the OOM cap, so the
    per-call grid == #s-buckets touched. B is NOT a pure function of s_bucket in general — it
    tracks the request's group size — so the LIFETIME grid across a request stream is looser
    (up to len(BATCH)*len(LEN)); that regime is the separate
    test_encode_batch_compile_bound_across_requests gate at the default budget. Do not read
    this per-call `== #s-buckets` as the daemon's lifetime bound."""
    cfg = _tiny_cfg()
    params = _tiny_deberta_params(cfg)
    # group sizes per bucket chosen to produce remainder chunks of DIFFERENT real sizes
    # (a variable-B encode would compile one executable per distinct real size).
    Ss = ([40] * 7 + [90] * 5 + [200] * 6 + [40] * 3 + [90] * 2)  # rungs {64,128,256}
    docs = [_Doc(S, seed=500 + i) for i, S in enumerate(Ss)]
    ids = [d.input_ids for d in docs]
    mask = [d.attention_mask for d in docs]
    s_buckets = {SB.bucket_len(len(x), SB.ENCODE_LEN_BUCKETS) for x in ids}

    # --- variable-B reference: encode each chunk at its REAL (un-padded-to-B) size -> the
    #     leak (one compile per distinct (real_size, s_bucket)). Reproduces the grouping but
    #     WITHOUT the B-ladder rounding, to show the ladder is what bounds the grid.
    JD._encode_core.clear_cache()
    groups: dict[int, list[int]] = {}
    for i, x in enumerate(ids):
        groups.setdefault(SB.bucket_len(len(x), SB.ENCODE_LEN_BUCKETS), []).append(i)
    leak_shapes = set()
    for s_bucket, group in groups.items():
        chunks, _b = SB.encode_batch_chunks(group, s_bucket, 256, 64)
        for ch in chunks:
            r = len(ch)  # REAL chunk size (no dummy-row padding to a fixed B)
            rows_ids = [SB.pad_to(ids[j], s_bucket, SB.ENCODE_PAD_ID) for j in ch]
            rows_mask = [SB.pad_to(mask[j], s_bucket, 0) for j in ch]
            JD.encode(params, jnp.asarray(rows_ids), jnp.asarray(rows_mask), cfg)
            leak_shapes.add((r, s_bucket))
    leak = JD._encode_core._cache_size()
    assert leak == len(leak_shapes), f"variable-B leak {leak} != distinct shapes {len(leak_shapes)}"
    assert leak > len(s_buckets), "fixture too weak: variable-B did not leak past #s-buckets"

    # --- bounded batched path: B from the ladder, fixed per s_bucket -> grid == #s-buckets.
    JD._encode_core.clear_cache()
    out = H.encode_lhs_batched(params, cfg, ids, mask, max_padded_tokens=256, max_docs=64)
    bounded = JD._encode_core._cache_size()
    assert len(out) == len(docs) and all(o is not None for o in out)
    assert bounded == len(s_buckets), (
        f"batched compiles {bounded} != #s-buckets {len(s_buckets)} "
        f"(ONE call at the saturating budget 256 -> one group, B pinned at the OOM cap, "
        f"so the per-call grid is #s-buckets; NOT a claim that B is single-valued in general)")
    assert bounded < leak, f"bound is vacuous: bucketed {bounded} !< variable-B leak {leak}"
    # every B used is a ladder rung (the structural bounded-set invariant)
    for s_bucket in s_buckets:
        _ch, b = SB.encode_batch_chunks(groups[s_bucket], s_bucket, 256, 64)
        assert b in SB.ENCODE_BATCH_BUCKETS, f"B={b} for s={s_bucket} not on the B-ladder"
    print(f"\n[encode batch compile bound] variable-B leak={leak}, batched={bounded}, "
          f"#s-buckets={len(s_buckets)}")


def test_encode_batch_compile_bound_across_requests():
    """(b') THE LIFETIME LEAK GATE at the DEFAULT (non-saturating) budget. JAX's compile
    cache persists ACROSS daemon requests, so the daemon's real bound is the (B, s_bucket)
    grid accumulated over a request STREAM, not within one call. At the default budget B is
    NOT single-valued per s_bucket: B = batch_bucket_floor(min(n, floor(budget/s), max_docs)),
    and for a group below the OOM ceiling oom_cap == n, so B sweeps the ENCODE_BATCH_BUCKETS
    ladder as the per-bucket group size varies request to request. The grid is therefore
    bounded by len(ENCODE_BATCH_BUCKETS) * len(ENCODE_LEN_BUCKETS) — a CONSTANT (the
    O(requests) leak is NOT back), but LOOSER than the per-text (B=1) path by up to
    len(ENCODE_BATCH_BUCKETS). This gate accumulates the persistent cache over a stream that
    touches ONLY one s_bucket and asserts: (a) the real constant bound holds, AND (b) it is
    NON-vacuous — the same s_bucket really mints MULTIPLE B (the spread the single-call gate
    at the saturating budget structurally cannot see, and the old 'single-valued' claim
    denied)."""
    cfg = _tiny_cfg()
    params = _tiny_deberta_params(cfg)
    JD._encode_core.clear_cache()
    # a STREAM of requests, every one touching ONLY s_bucket=64 (S~40), with DIFFERENT
    # per-bucket group sizes so B walks the ladder. DEFAULT budget (no max_padded_tokens
    # override): floor(8192/64)=128 >= max_docs=64 -> oom_cap = min(n, 64) -> B tracks n.
    seen_b = set()
    seed = 700
    for n in (1, 3, 5, 10, 20, 40):
        docs = [_Doc(40, seed=seed + j) for j in range(n)]
        seed += n
        ids = [d.input_ids for d in docs]
        mask = [d.attention_mask for d in docs]
        H.encode_lhs_batched(params, cfg, ids, mask)  # DEFAULT budget — the daemon's regime
        _ch, b = SB.encode_batch_chunks(list(range(n)), 64)
        seen_b.add(b)
    grid = JD._encode_core._cache_size()
    # (b) NON-vacuous: one s_bucket ALONE minted >1 compile -> B is NOT single-valued per
    #     s_bucket (the precise refutation of the old docstring/gate tightness claim).
    assert len(seen_b) > 1, f"fixture too weak: B did not spread across the stream (seen={seen_b})"
    assert grid == len(seen_b), (
        f"one-s_bucket lifetime grid {grid} != #distinct B {len(seen_b)} ({sorted(seen_b)}) "
        f"-> B IS variable per s_bucket across requests (not the per-text len(LEN) bound)")
    # (a) the REAL constant bound: len(BATCH)*len(LEN), NOT the per-text len(LEN). Still a
    #     CONSTANT independent of the request count -> no O(requests) re-leak.
    ceiling = len(SB.ENCODE_BATCH_BUCKETS) * len(SB.ENCODE_LEN_BUCKETS)
    assert grid <= ceiling, f"lifetime grid {grid} exceeds len(BATCH)*len(LEN)={ceiling} — re-leak!"
    print(f"\n[encode batch lifetime grid] one s_bucket=64 over a request stream -> {grid} "
          f"compiles, B spread={sorted(seen_b)} (bound len(BATCH)*len(LEN)={ceiling})")


def test_coref_documents_batched_equals_per_text():
    """(c) The DISCRETE invariant end-to-end (ADR-0009 tier-1): the cluster SETS through the
    FULL coref forward (encode -> decode) are IDENTICAL whether the encode is batched by
    bucket-group (coref_documents_host) or run per-text (coref_document_host, B=1). The
    decode tail is the unchanged per-doc path; only the encode grouping differs."""
    cfg = _tiny_cfg()
    dparams = _tiny_deberta_params(cfg)
    decode_params = _tiny_decode_params()
    Ss = [18, 27, 33, 41, 55, 70, 19, 28]  # varied S incl. cross-bucket K/P, same rung 64
    docs = [_Doc(S, seed=600 + i) for i, S in enumerate(Ss)]

    for singletons in (False, True):
        # per-text reference (B=1): the existing coref_document_host, one doc at a time
        ref = [_cluster_sets(H.coref_document_host(
            dparams, cfg, decode_params, d.input_ids, d.attention_mask, d.eos_mask,
            d.tokens, d.subtoken_map, d.new_token_map, singletons=singletons)) for d in docs]
        # batched path (small budget -> real multi-doc batches with remainders)
        got_tok = H.coref_documents_host(dparams, cfg, decode_params, docs, singletons=singletons)
        got = [_cluster_sets(c) for c in got_tok]
        for S, r, g in zip(Ss, ref, got):
            assert r == g, f"cluster sets differ batched vs per-text at S={S}, singletons={singletons}"
    # non-vacuity: at least one >=2-mention cluster exercised
    any_multi = any(len(c) >= 2 for cs in got for c in cs)
    assert any_multi, "VACUOUS: no >=2-mention cluster — strengthen the fixture"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
