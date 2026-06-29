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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-s"]))
