#!/usr/bin/env python
"""HOST fixture-capture for the maverick decode-tail JAX migration (Stage 1a).

Runs ONLY where maverick + torch + CUDA live (the host). It runs maverick SERIAL
(one paragraph at a time, never a B*S batch) over N paragraphs of pg78966.txt and
dumps, per paragraph, the exact inputs the decode tail consumes plus maverick's
resulting clusters. test_jax_decode_fidelity.py replays these against the pure
JAX core and asserts bit-exact cluster-set equality.

This file is the FIXTURE-I/O BOUNDARY: it legitimately mixes torch (device) and
numpy (host) because its whole job is to pull device tensors to host and persist
them. It is host-only scaffolding, NOT part of the composed device pipeline, so
it is deliberately NOT listed in the import-XOR / device-transfer gates'
SCANNED set (same rationale those gates use to exclude vendored maverick and
pytest itself).

Captured per paragraph (arrays -> <stem>.npz, structured -> <stem>.json):
  npz : last_hidden_state [S, TH] float32, attention_mask [S] int, eos_mask [S,S] int
  json: tokens, subtoken_map, new_token_map, clusters_bpe, clusters_token_offsets,
        clusters_token_offsets_singletons  (the singletons=True variant)
Captured ONCE (shared): weights.npz — the decode-tail learned parameters.

Usage (on the host, inside the maverick env):
    python capture_fixtures.py [N] [OUTDIR]
Defaults: N=6, OUTDIR=./fixtures
"""

from __future__ import annotations

import json
import os
import re
import sys

import numpy as np
import torch

from maverick import Maverick
from maverick.common.util import original_token_offsets

from maverick_load import safe_maverick_load  # SSOT safe checkpoint load (ADR-0012 P1)

SAMPLE_TXT = "/home/bork/pg/pg78966.txt"

# decode-tail FC RepresentationLayers (module attr on Maverick_mes) to dump.
FC_LAYERS = [
    "start_token_classifier",
    "start_token_representation",
    "end_token_representation",
    "start_end_classifier",
    "coref_start_all_mlps",
    "coref_end_all_mlps",
]
# bilinear antecedent parameters (direct nn.Parameter attrs).
BILINEAR = [
    "antecedent_s2s_all_weights", "antecedent_e2e_all_weights",
    "antecedent_s2e_all_weights", "antecedent_e2s_all_weights",
    "antecedent_s2s_all_biases", "antecedent_e2e_all_biases",
    "antecedent_s2e_all_biases", "antecedent_e2s_all_biases",
]


def _np(t: torch.Tensor) -> np.ndarray:
    return t.detach().to("cpu").float().numpy()


def extract_weights(model) -> dict:
    """Pull every decode-tail parameter to numpy float32 with the exact keys the
    JAX core indexes by. FAIL LOUD if a layer is missing."""
    out = {}
    for name in FC_LAYERS:
        rep = getattr(model, name)
        fc = rep.layer  # FullyConnectedLayer
        out[f"{name}.dense1.weight"] = _np(fc.dense1.weight)
        out[f"{name}.dense1.bias"] = _np(fc.dense1.bias)
        out[f"{name}.layer_norm.weight"] = _np(fc.layer_norm.weight)
        out[f"{name}.layer_norm.bias"] = _np(fc.layer_norm.bias)
        out[f"{name}.dense.weight"] = _np(fc.dense.weight)
        out[f"{name}.dense.bias"] = _np(fc.dense.bias)
    for name in BILINEAR:
        out[name] = _np(getattr(model, name))
    return out


def select_paragraphs(path: str, n: int) -> list[str]:
    """Blank-line-delimited paragraphs of moderate length (bounds S for an 11GB
    card: per-paragraph, never the whole book)."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", raw)]
    picked = [p for p in paras if 30 <= len(p.split()) <= 300]
    assert len(picked) >= n, f"only {len(picked)} usable paragraphs in {path}"
    return picked[:n]


@torch.no_grad()
def capture_one(mav: Maverick, text: str) -> tuple[dict, dict]:
    """Mirror Maverick.predict's input prep, run the full model SERIAL, and grab
    the encoder last_hidden_state via a forward hook so the captured lhs is byte-
    identical to the one the clustering consumed."""
    model = mav.model
    device = mav.device

    tokens, eos_indices, speakers, _ = mav.preprocess(text)
    tok = mav.tokenize(tokens, eos_indices, speakers)

    input_ids = torch.tensor(tok["input_ids"]).unsqueeze(0).to(device)        # host-device-boundary
    attention_mask = torch.tensor(tok["attention_mask"]).unsqueeze(0).to(device)  # host-device-boundary
    eos_mask = torch.tensor(tok["eos_mask"]).unsqueeze(0).to(device)          # host-device-boundary

    grabbed = {}

    def hook(_module, _inp, output):
        grabbed["lhs"] = output["last_hidden_state"]

    def _forward(singletons: bool):
        return model(
            stage="test",
            input_ids=input_ids,
            attention_mask=attention_mask,
            eos_mask=eos_mask,
            tokens=[tok["tokens"]],
            subtoken_map=[tok["subtoken_map"]],
            new_token_map=[tok["new_token_map"]],
            singletons=singletons,
            add=None,
            gold_mentions=None,
        )

    handle = model.encoder.register_forward_hook(hook)
    try:
        out = _forward(singletons=False)
        # Capture BOTH flag values so the fidelity test can prove the singleton
        # decode path (coref_host_shell's BUG-FIXED `singletons=True` branch), not
        # just the default. The encoder is deterministic, so the second forward
        # reuses the same lhs (we only need its clusters).
        out_sing = _forward(singletons=True)
    finally:
        handle.remove()

    assert "lhs" in grabbed, "encoder forward hook did not fire"
    lhs = _np(grabbed["lhs"][0])  # [S, TH]
    clusters_bpe = out["pred_dict"]["clusters"]
    clusters_tok = original_token_offsets(
        clusters_bpe, tok["subtoken_map"], tok["new_token_map"]
    )
    clusters_bpe_sing = out_sing["pred_dict"]["clusters"]
    clusters_tok_sing = original_token_offsets(
        clusters_bpe_sing, tok["subtoken_map"], tok["new_token_map"]
    )

    arrays = {
        "last_hidden_state": lhs,
        "attention_mask": np.asarray(tok["attention_mask"], dtype=np.int64),
        "eos_mask": _np(eos_mask[0]).astype(np.int64),
    }
    structured = {
        "text": text,
        "tokens": tok["tokens"],
        "subtoken_map": tok["subtoken_map"],
        "new_token_map": tok["new_token_map"],
        "clusters_bpe": [[list(s) for s in c] for c in clusters_bpe],
        "clusters_token_offsets": [[list(s) for s in c] for c in clusters_tok],
        # singletons=True variant: same lhs, maverick's singleton-interleaved clusters.
        "clusters_token_offsets_singletons":
            [[list(s) for s in c] for c in clusters_tok_sing],
    }
    return arrays, structured


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fixtures"
    )
    os.makedirs(outdir, exist_ok=True)

    with safe_maverick_load():
        mav = Maverick(device="cuda")  # host-device-boundary: maverick on GPU
    # match the daemon: force fp32 so captured hidden states satisfy jax_decode's
    # fp32 contract (the encoder loads fp16 natively alongside fp32 heads).
    mav.model.float()  # host-device-boundary: cast maverick to fp32
    model = mav.model

    np.savez(os.path.join(outdir, "weights.npz"), **extract_weights(model))
    print(f"wrote weights.npz ({len(FC_LAYERS)} FC layers + {len(BILINEAR)} bilinear)")

    for i, para in enumerate(select_paragraphs(SAMPLE_TXT, n)):
        arrays, structured = capture_one(mav, para)
        stem = os.path.join(outdir, f"para_{i:03d}")
        np.savez(stem + ".npz", **arrays)
        with open(stem + ".json", "w", encoding="utf-8") as fh:
            json.dump(structured, fh)
        s = arrays["last_hidden_state"].shape
        nc = len(structured["clusters_token_offsets"])
        ncs = len(structured["clusters_token_offsets_singletons"])
        print(f"para_{i:03d}: S={s[0]} TH={s[1]} clusters={nc} clusters+singletons={ncs}")

    print(f"done -> {outdir}")


if __name__ == "__main__":
    main()
