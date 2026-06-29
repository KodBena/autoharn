#!/usr/bin/env python
"""Guest plumbing falsifier: deberta export -> npz -> torch-free reload -> encode.

SUB-TASK 1 plumbing gate. The unified daemon loads the deberta encoder from the exported
.npz with `np.load` ALONE (no torch, no maverick). This proves that whole path is correct
and lossless on VANILLA deberta-v3 (the guest cannot load maverick's FINE-TUNED weights —
that, plus the keyset bijection against maverick's real config, is the HOST-only step).

It exercises the EXACT codecs the daemon uses, not parallel reimplementations:
  export  : export_deberta_maverick.save_npz  (the one npz writer)
  reload  : coref_decode_server.load_deberta_npz  (the daemon's host loader)
  cfg     : coref_host_shell.build_deberta_cfg     (the jax home's DebertaCfg rebuild)
  lift    : coref_host_shell.lift_deberta_params   (the jax home's host->device lift)
and asserts the encode from the reloaded npz is BIT-IDENTICAL to the encode from the
direct in-memory conversion — i.e. the disk round-trip and the cfg scalar round-trip lose
nothing, and the param_keys bijection holds on the reloaded keyset.

This file imports torch + transformers (to produce the vanilla reference weights) + jax:
it is a TEST, not part of the composed device pipeline, so it is not scanned by the
import-XOR gate (same posture as test_deberta_fidelity.py).
"""

from __future__ import annotations

import os
import tempfile

import jax
import jax.numpy as jnp
import numpy as np

import coref_host_shell
import jax_deberta
from coref_decode_server import load_deberta_npz
from deberta_weights import load_jax_deberta
from export_deberta_maverick import save_npz

MODEL = "microsoft/deberta-v3-large"
_CACHE: dict = {}


def _loaded():
    if "v" not in _CACHE:
        jax.config.update("jax_enable_x64", False)
        params, cfg, hf = load_jax_deberta(MODEL)
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(MODEL)
        _CACHE["v"] = (params, cfg, tok)
    return _CACHE["v"]


def test_npz_roundtrip_encode_is_bit_identical():
    ref_params, ref_cfg, tok = _loaded()

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "deberta_vanilla.npz")
        n = save_npz(path, ref_params, ref_cfg, MODEL)  # tokenizer identity is required
        assert n == len(ref_params)

        # the daemon's torch-free load path (np.load only)
        host_w, cfg_fields, tok_name = load_deberta_npz(path)
        rt_cfg = coref_host_shell.build_deberta_cfg(cfg_fields)
        rt_params = coref_host_shell.lift_deberta_params(host_w)

        # the tokenizer identity travelled WITH the weights (R2/F1)
        assert tok_name == MODEL, f"tokenizer identity drift: {tok_name!r} != {MODEL!r}"
        # cfg survived the scalar round-trip exactly
        assert rt_cfg == ref_cfg, f"cfg drift: {rt_cfg} != {ref_cfg}"
        # keyset bijection holds on the reloaded weights (the device read-set SSOT) — this
        # is the SAME assertion the daemon now runs at construction (R3/F1).
        assert set(host_w) == jax_deberta.param_keys(rt_cfg), "reloaded keyset != param_keys"
        coref_host_shell.validate_deberta_load(host_w, rt_cfg)  # the daemon's load-time gate
        # and it FAILS LOUD on a dropped weight (R3/F1: prove the guard bites)
        dropped = dict(host_w)
        dropped.pop(next(iter(dropped)))
        try:
            coref_host_shell.validate_deberta_load(dropped, rt_cfg)
        except ValueError as e:
            assert "param_keys" in str(e) or "read-set" in str(e)
        else:
            raise AssertionError("validate_deberta_load must reject a dropped-weight keyset")

        # encode from the reloaded npz vs the direct in-memory conversion -> bit-identical
        enc = tok(["DeBERTa uses disentangled attention.",
                   "Marie Curie discovered radium; she won two Nobel Prizes."],
                  return_tensors="np", padding=True)
        ids = jnp.asarray(enc["input_ids"])
        mask = jnp.asarray(enc["attention_mask"])
        ref_lhs = np.asarray(jax_deberta.encode(ref_params, ids, mask, ref_cfg))
        rt_lhs = np.asarray(jax_deberta.encode(rt_params, ids, mask, rt_cfg))
        assert ref_lhs.shape == rt_lhs.shape
        assert np.array_equal(ref_lhs, rt_lhs), (
            f"npz round-trip changed the encode: max|Δ|={np.abs(ref_lhs-rt_lhs).max():.3e} "
            "(float32 savez/load must be lossless and cfg must round-trip exactly)")


def test_loader_rejects_a_non_export():
    """load_deberta_npz fails loud (ADR-0002) on an npz that is not a deberta export."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "junk.npz")
        np.savez(path, foo=np.zeros(3, np.float32))  # weights but no __cfg__ fields
        try:
            load_deberta_npz(path)
        except ValueError as e:
            assert "cfg field" in str(e) or "valid deberta export" in str(e)
        else:
            raise AssertionError("load_deberta_npz must reject a non-export npz")


if __name__ == "__main__":
    test_npz_roundtrip_encode_is_bit_identical()
    print("PASS npz round-trip encode bit-identical (export->np.load->cfg rebuild->encode)")
    test_loader_rejects_a_non_export()
    print("PASS loader rejects a non-export npz")
