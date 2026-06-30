#!/usr/bin/env python
"""lab_measure — the DEVICE-side measurement core of the bench (ADR-0012 P9 / P7).

This is the device shell, analogous to `coref_host_shell`: it owns every jax op the
bench needs — the host-list -> device-array LIFT (the one host↔device boundary), the
warm wall-timing (compile-excluded), the output shape/finiteness GUARD, and the P6
fidelity `max|Δ|` — and returns only PYTHON SCALARS to the host `bench.py`. So
`bench.py` (registry + sweep + stats + report + spans) never imports jax; the device
math lives here, exactly as `coref_decode_server` (host) delegates device lifts to
`coref_host_shell` (device).

HOST-XOR-DEVICE: imports `jax`/`jax.numpy` only, NEVER numpy. Neutrally named, so the
import-XOR gate enforces single-sided (device-only) cleanliness.

HONEST COMPILE/RUN SEPARATION (A6 / ADR-0009). `warm_time_seconds` pays the
compile+warmup forwards FIRST (discarded), then times `repeats` RUN-ONLY forwards,
each ended by `block_until_ready()` so the wall window encloses the real device work
(not async dispatch). The reported numbers are warm; compile is excluded by
construction.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import jax
import jax.numpy as jnp

import jax_deberta

if TYPE_CHECKING:
    from nla_lab.contract import EncodeVariant


def synthetic_cfg(num_layers: int = 2, num_heads: int = 2, head_size: int = 8,
                  position_buckets: int = 16, max_relative_positions: int = 64
                  ) -> "jax_deberta.DebertaCfg":
    """A tiny but ARCHITECTURE-FAITHFUL DebertaCfg for the self-test fixture: same
    disentangled-attention shape (c2p+p2c, scale_factor=3, log-bucketed rel-pos) as
    deberta-v3-large, scaled down so the round-trip runs in milliseconds on CPU jax.
    pos_ebd_size==position_buckets and scale_factor==1+c2p+p2c, exactly as
    deberta_weights.cfg_from_hf derives them."""
    return jax_deberta.DebertaCfg(
        num_layers=num_layers, num_heads=num_heads, head_size=head_size,
        position_buckets=position_buckets, max_relative_positions=max_relative_positions,
        pos_ebd_size=position_buckets, scale_factor=3, has_c2p=True, has_p2c=True,
        layer_norm_eps=1e-7)


# ----------------------------------------------------------- the host↔device lift
def lift_batch(ids_rows: list[list[int]], mask_rows: list[list[int]]) -> tuple[jax.Array, jax.Array]:
    """The ONE host->device boundary op the bench uses: lift bucketed+padded token-id
    / mask rows (host python lists, already `[B, s_bucket]`) to device int32 arrays.
    Mirrors the `jnp.asarray([...])` lift inside `coref_host_shell.encode_lhs`."""
    ids = jnp.asarray(ids_rows, dtype=jnp.int32)    # host-device-boundary: lift bucketed bench input_ids host->device [B,S]
    mask = jnp.asarray(mask_rows, dtype=jnp.int32)  # host-device-boundary: lift bucketed bench attention_mask host->device [B,S]
    return ids, mask


# --------------------------------------------------------------- the warm timing
def warm_time_seconds(
    variant: "EncodeVariant",
    params: dict[str, jax.Array],
    ids: jax.Array,
    mask: jax.Array,
    cfg: "jax_deberta.DebertaCfg",
    repeats: int,
    warmup: int,
) -> list[float]:
    """Pay compile + `warmup` forwards (discarded), then return `repeats` RUN-ONLY
    per-call wall times (seconds), each ended by block_until_ready (A6)."""
    for _ in range(max(1, warmup)):
        out = variant.encode(params, ids, mask, cfg)
        jax.block_until_ready(out)  # type: ignore[no-untyped-call]  # host-device-boundary: drain compile+warmup forwards
    times: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = variant.encode(params, ids, mask, cfg)
        jax.block_until_ready(out)  # type: ignore[no-untyped-call]  # host-device-boundary: barrier so the warm wall window encloses real device work
        times.append(time.perf_counter() - t0)
    return times


# ----------------------------------------------------------------- run + GUARD
def run_lhs(
    variant: "EncodeVariant",
    params: dict[str, jax.Array],
    ids: jax.Array,
    mask: jax.Array,
    cfg: "jax_deberta.DebertaCfg",
) -> jax.Array:
    """One forward, materialized (block_until_ready) so a downstream guard/fidelity
    read sees real values, not a pending computation."""
    out = variant.encode(params, ids, mask, cfg)
    jax.block_until_ready(out)  # type: ignore[no-untyped-call]  # host-device-boundary: materialize before guard/fidelity read
    return out


def guard_output(lhs: jax.Array, expected_shape: tuple[int, int, int]) -> tuple[str, str]:
    """The ONE output-shape+finiteness contract the bench derives (the watchdog's
    single home, A10/B12). Returns `(status, detail)`:
      * ("ok", "")                       — shape matches and all-finite
      * ("failed_shape", detail)         — wrong shape (a malformed variant)
      * ("failed_nonfinite", detail)     — NaN/Inf (a numerically-broken variant)
    In a BENCH lane a malformed output is a LOUD recorded FAILURE, never coerced
    (B8). The caller flags-and-continues; it does NOT substitute a clean output."""
    if tuple(lhs.shape) != expected_shape:
        return "failed_shape", f"shape {tuple(lhs.shape)} != expected {expected_shape}"
    if not bool(jnp.all(jnp.isfinite(lhs))):
        return "failed_nonfinite", "output contains NaN/Inf"
    return "ok", ""


# --------------------------------------------------------- P6 fidelity (device)
def fidelity_delta(
    lhs_variant: jax.Array, lhs_reference: jax.Array, mask: jax.Array
) -> tuple[float, float]:
    """P6 aggregate-behavioral distance vs the exact reference, over REAL tokens only
    (ADR-0009 tier-2; NOT bit-exact). Returns `(max_abs, mean_abs)` as python floats —
    the ONLY values that cross to the host report. Real-token convention matches
    test_deberta_fidelity._run_pair (mask==1 positions)."""
    diff = jnp.abs(lhs_variant.astype(jnp.float32) - lhs_reference.astype(jnp.float32))
    real = jnp.where(mask.astype(bool)[:, :, None], diff, 0.0)
    n_real = jnp.sum(mask.astype(jnp.float32)) * lhs_variant.shape[-1]
    max_abs = float(jnp.max(real))
    mean_abs = float(jnp.sum(real) / jnp.maximum(n_real, 1.0))
    return max_abs, mean_abs


# ------------------------------------------------ synthetic fixture (self-test)
def synthetic_deberta(cfg: "jax_deberta.DebertaCfg", vocab: int, intermediate: int,
                      seed: int) -> dict[str, jax.Array]:
    """A tiny RANDOM-init DeBERTa whose params cover EXACTLY `jax_deberta.param_keys(cfg)`
    — the harness self-proof fixture. It lets the bench prove the contract+registry+bench
    round-trip on the guest with CPU jax WITHOUT an HF download (the 24-layer real
    weights + the ~1e-3 vs-HF bar are the existing test_deberta_fidelity.py gate). LayerNorm
    weights=1/bias=0 and small-scaled projections keep the forward finite."""
    hidden = cfg.num_heads * cfg.head_size
    key = jax.random.PRNGKey(seed)
    params: dict[str, jax.Array] = {}

    def draw(shape: tuple[int, ...], scale: float = 0.02) -> jax.Array:
        nonlocal key
        key, sub = jax.random.split(key)
        return jax.random.normal(sub, shape, dtype=jnp.float32) * scale

    params["embeddings.word_embeddings.weight"] = draw((vocab, hidden))
    params["embeddings.LayerNorm.weight"] = jnp.ones((hidden,), jnp.float32)
    params["embeddings.LayerNorm.bias"] = jnp.zeros((hidden,), jnp.float32)
    params["encoder.rel_embeddings.weight"] = draw((2 * cfg.pos_ebd_size, hidden))
    params["encoder.LayerNorm.weight"] = jnp.ones((hidden,), jnp.float32)
    params["encoder.LayerNorm.bias"] = jnp.zeros((hidden,), jnp.float32)
    for i in range(cfg.num_layers):
        p = f"encoder.layer.{i}."
        for proj in ("attention.self.query_proj", "attention.self.key_proj",
                     "attention.self.value_proj", "attention.output.dense"):
            params[p + proj + ".weight"] = draw((hidden, hidden))
            params[p + proj + ".bias"] = jnp.zeros((hidden,), jnp.float32)
        for ln in ("attention.output.LayerNorm", "output.LayerNorm"):
            params[p + ln + ".weight"] = jnp.ones((hidden,), jnp.float32)
            params[p + ln + ".bias"] = jnp.zeros((hidden,), jnp.float32)
        params[p + "intermediate.dense.weight"] = draw((intermediate, hidden))
        params[p + "intermediate.dense.bias"] = jnp.zeros((intermediate,), jnp.float32)
        params[p + "output.dense.weight"] = draw((hidden, intermediate))
        params[p + "output.dense.bias"] = jnp.zeros((hidden,), jnp.float32)

    expected = jax_deberta.param_keys(cfg)
    got = set(params)
    if got != expected:                       # fail loud: the fixture must match the read-set
        raise AssertionError(
            f"synthetic_deberta key mismatch: missing={expected - got}, extra={got - expected}")
    return params
