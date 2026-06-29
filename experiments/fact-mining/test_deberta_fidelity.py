#!/usr/bin/env python
"""Guest fidelity falsifier: pure-JAX DeBERTa-v3 encoder vs transformers torch.

ADR-0009 (two-tier). last_hidden_state is a FLOAT aggregate (24 fp32 layers
accumulate), so the bar is an absolute tolerance, NOT bit-identity: TARGET
max|Δ| < 1e-3 over real sentences == architecture correct. 1e-3..1e-2 would be
benign reduction-order; > 1e-2 or a STRUCTURED (position/term-localized) error is
a real bug to diagnose. This test reports the ACHIEVED number (a real measured
figure), and additionally proves the relative-position BUCKET array — a discrete
invariant — matches torch's build_relative_position bit-for-bit (== exact).

This file imports torch + transformers + jax: it is a TEST, not part of the
composed device pipeline, so it is not scanned by the import-XOR gate.

Run:  . ~/w/vdc/venvs/generic/bin/activate && HF_HUB_DISABLE_XET=1 \
        python test_deberta_fidelity.py
or under pytest.
"""

from __future__ import annotations

import os

import jax
import jax.numpy as jnp
import numpy as np
import torch

import jax_deberta
from deberta_weights import cfg_from_hf, load_jax_deberta

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

MODEL = "microsoft/deberta-v3-large"
SENTENCES = [
    "The cat sat on the mat because it was warm.",
    "Marie Curie discovered radium; she won two Nobel Prizes for her research.",
    "After the company released its earnings, investors sold the stock sharply.",
    "DeBERTa uses disentangled attention to encode content and relative position.",
]
# A LONG document (S > 512): this is the regime maverick-coref actually runs and the
# ONLY regime that engages the float log-bucket path. make_log_bucket_position takes
# its float log branch only for |rel| >= mid = position_buckets//2 = 128; every
# SENTENCES item is S < 30, so they prove ONLY the short regime. Past 512 the bucket
# exceeds +/-att_span and the c2p/p2c gather CLIP engages too. Repeated-but-varied
# clauses so it tokenizes long without being degenerate.
LONG_TEXT = " ".join([
    "Marie Curie discovered radium and polonium while studying pitchblende, and she "
    "later won two Nobel Prizes, one in physics and one in chemistry, for that work.",
    "After the company released its quarterly earnings, which badly missed the "
    "analysts' consensus, investors sold the stock sharply in after-hours trading.",
    "The disentangled attention mechanism in DeBERTa encodes each token using both "
    "its content vector and its relative position, bucketed logarithmically for "
    "distant pairs so that long documents remain tractable to model.",
    "The cat sat on the warm mat by the window because the afternoon sun had heated "
    "the stone tiles, and the dog, who had chased it earlier, was now fast asleep.",
] * 4)
# A PADDED BATCH (batch>1 with right-padding): proves the [B,1,S,S] mask multiply and
# that padded query/key rows do not contaminate real tokens (both torch and JAX
# masked_fill the row -> identical). Varied lengths force real padding.
BATCH = [
    "DeBERTa uses disentangled attention.",
    "Marie Curie discovered radium; she won two Nobel Prizes for her research over many years.",
    "The cat sat on the mat.",
]
TARGET = 1e-3

_CACHE: dict = {}


def _load():
    if "loaded" not in _CACHE:
        from transformers import AutoTokenizer
        params, cfg, hf = load_jax_deberta(MODEL)
        tok = AutoTokenizer.from_pretrained(MODEL)
        _CACHE["loaded"] = (params, cfg, hf, tok)
    return _CACHE["loaded"]


def _torch_bucket(seq_len: int, cfg) -> np.ndarray:
    from transformers.models.deberta_v2.modeling_deberta_v2 import build_relative_position
    q = torch.zeros(1, seq_len, 1)
    rp = build_relative_position(q, q, bucket_size=cfg.position_buckets,
                                 max_position=cfg.max_relative_positions)
    return rp.squeeze(0).numpy()


def test_relative_position_buckets_exact():
    """Discrete invariant (ADR-0009 tier-1): the log-bucket relative-position array
    must equal torch's bit-for-bit. Probed across every edge the lens flags: below
    mid (no log path), at mid=128 (boundary), past it (log path), at max_position=512,
    and BEYOND it (513, 600) where the bucket saturates past +/-att_span and torch/JAX
    must clamp identically."""
    _, cfg, _, _ = _load()
    for s in (12, 128, 129, 400, 512, 513, 600):
        jx = np.asarray(jax_deberta.build_relative_position(
            s, cfg.position_buckets, cfg.max_relative_positions))
        th = _torch_bucket(s, cfg)
        assert jx.shape == th.shape
        assert np.array_equal(jx, th), (
            f"bucket array diverged at S={s}: "
            f"{int(np.abs(jx - th).max())} max abs index diff")


def _run_pair(text):
    """Run torch vs JAX on `text` (a str, or a list[str] -> padded batch). Returns
    (delta_over_real_tokens, input_ids.shape). Padded positions produce identical
    garbage in both engines (both masked_fill the row), so the meaningful figure is
    max|Δ| over REAL (attention_mask==1) tokens — the same convention the review used."""
    params, cfg, hf, tok = _load()
    if isinstance(text, (list, tuple)):
        enc = tok(list(text), return_tensors="pt", padding=True)
    else:
        enc = tok(text, return_tensors="pt")
    input_ids = enc["input_ids"]
    attention_mask = enc["attention_mask"]
    with torch.no_grad():
        ref = hf(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
    jx = jax_deberta.encode(
        params,
        jnp.asarray(input_ids.numpy()),
        jnp.asarray(attention_mask.numpy()),
        cfg,
    )
    full = np.abs(np.asarray(jx, dtype=np.float64) - ref.numpy().astype(np.float64))
    real = full[attention_mask.numpy().astype(bool)]    # [n_real_tokens, hidden]
    return real, tuple(input_ids.shape)


def test_last_hidden_state_matches_torch():
    """Tier-2 float aggregate (ADR-0009). Cases span every regime the reviews flag:
    the short SENTENCES (no log path), a LONG_TEXT (S>512: log-bucket path + gather
    clip — maverick's real regime), and a PADDED BATCH (batch>1 mask handling)."""
    worst = 0.0
    cases = ([(s, f"short {s[:34]!r}") for s in SENTENCES]
             + [(LONG_TEXT, "LONG log-bucket+clip path"),
                (BATCH, "PADDED batch (batch>1)")])
    for text, label in cases:
        real, shape = _run_pair(text)
        m = float(real.max())
        worst = max(worst, m)
        print(f"  shape={str(shape):10s} max|Δ|={m:.3e} mean|Δ|={float(real.mean()):.3e}  {label}")
    print(f"WORST max|Δ| over {len(cases)} cases = {worst:.3e}  (target {TARGET:.0e})")
    assert worst < TARGET, f"max|Δ|={worst:.3e} exceeds target {TARGET:.0e}"


if __name__ == "__main__":
    jax.config.update("jax_platform_name", "cpu")
    test_relative_position_buckets_exact()
    print("PASS bucket-array exact (S=12,128,129,400,512,513,600)")
    test_last_hidden_state_matches_torch()
    print("PASS last_hidden_state fidelity")
