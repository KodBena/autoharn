#!/usr/bin/env python
"""HOST-run weight export: maverick's FINE-TUNED deberta encoder -> a torch-free .npz.

SUB-TASK 1 of the unified-daemon build. The unified jax-only daemon must run maverick's
fine-tuned deberta encoder WITHOUT importing torch or maverick at runtime. So we export
the encoder ONCE, here on the host (torch present), into a self-describing numpy archive
the daemon loads with `np.load` alone — no torch, no maverick, no checkpoint.

This is a BOUNDARY / fixture script, exactly like `capture_fixtures.py` and
`validate_deberta_keyset.py`: it imports torch + numpy + jax (via deberta_weights) ON
PURPOSE — its whole job is to cross the torch->jax boundary once. It is NEUTRALLY named
(no jax_*/torch_* token) and is NOT in the import-XOR / device-transfer SCANNED sets (it
is the declared conversion seam, the single home of this crossing — ADR-0012 P1/P7).

DERIVE-DON'T-RE-AUTHOR (ADR-0012 P7) + KEYSET-GUARDED (ADR-0002 fail-loud). It reuses the
PROVEN conversion: `deberta_weights.cfg_from_hf` (every hyperparameter read off the live
HF config, never retyped) and `deberta_weights.params_from_state_dict` (every tensor under
its ORIGINAL torch key; the converted keyset is asserted == `jax_deberta.param_keys(cfg)`
EXACTLY, so a fine-tuned checkpoint carrying a head/pooler/extra buffer, or a
share_att_key=False / non-'gelu' config, fails loud HERE rather than loading a silently-
wrong forward). What is written is therefore the SAME pytree + DebertaCfg the guest
fidelity test proved to 3e-5 vs torch — just frozen to disk for a torch-free reload.

THE ARCHIVE (`fixtures/deberta_maverick.npz`):
  * one entry per weight, keyed by its ORIGINAL torch key (dotted names; np.savez
    preserves them), value a float32 numpy array — the daemon hands these to
    `coref_host_shell.lift_deberta_params` (the jax home does the device lift);
  * one `__cfg__<field>` entry per DebertaCfg field (scalars) — the daemon hands these
    to `coref_host_shell.build_deberta_cfg`, so the jit-static config travels WITH the
    weights and is never a constant retyped in the daemon (P1);
  * one `__tokenizer__` entry: maverick's `encoder_hf_model_name` (the HF tokenizer the
    encoder was fine-tuned with). The tokenizer maps text->input_ids, so it is as
    load-bearing as the cfg; it travels WITH the weights for the same P1 reason, and the
    daemon builds its preprocessor from THIS, never a hardcoded `--coref-model` constant
    (R2/F1 — a maverick variant on a different encoder vocab would otherwise load the
    right weights but tokenize wrong → silently different clusters, no load-time failure).

THE VENDORED SENTENCEPIECE MODEL (`fixtures/deberta_maverick.spm`, sibling of the npz).
The unified daemon tokenises with RAW sentencepiece (no `transformers`/`huggingface_hub`
at runtime — that surface transitively force-imports torch, which jax_only_guard blocks),
so it needs the deberta-v3 `spm.model` as a LOCAL file, not an HF-cache lookup. This
export copies maverick's OWN spm.model (the exact sub-word model its encoder was trained
with) to `spm_sibling_path(<out>)` — a self-describing, vendored artifact (ADR-0012 P7)
the daemon loads with `StandalonePreprocessor.from_spm`. The npz + the .spm are the two
runtime tokenizer/weight artifacts; both must ship together (the daemon fails loud if the
sibling .spm is missing).

Run on the HOST (maverick + the fine-tuned checkpoint are host-only; no GPU needed):

    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python export_deberta_maverick.py
        [--out fixtures/deberta_maverick.npz]
        # writes BOTH fixtures/deberta_maverick.npz AND fixtures/deberta_maverick.spm

WHAT ONLY THE HOST CONFIRMS: this export. The guest proves the npz round-trip plumbing
with VANILLA deberta (export->reload->encode bit-identical), but maverick's FINE-TUNED
weights live only on the host, so the real `deberta_maverick.npz` and its keyset-bijection
pass against maverick's actual config are a host-only step.
"""

from __future__ import annotations

import argparse
import os
import shutil

import numpy as np

# DebertaCfg field order is the SSOT for what __cfg__* keys to write; importing it from
# jax_deberta keeps the field set derived-from-one-home (P1), never hand-listed here.
from jax_deberta import DebertaCfg


# Reserved npz key carrying the encoder's TOKENIZER IDENTITY (the HF model name the
# fine-tuned encoder was trained with). It is NOT a DebertaCfg field (cfg is structural
# hyperparameters: num_layers/heads/buckets/…), but it is equally load-bearing for the
# forward: the tokenizer maps text->input_ids, so a wrong vocab silently changes
# input_ids->lhs->clusters with NO shape/keyset failure. Per ADR-0012 P1/P7 this identity
# must TRAVEL WITH THE WEIGHTS (like the cfg), never be a constant retyped in the daemon.
TOKENIZER_KEY = "__tokenizer__"


def spm_sibling_path(npz_path: str) -> str:
    """The ONE definition of the vendored-spm naming convention (ADR-0012 P1): the
    daemon's `spm.model` is the npz's sibling with a `.spm` extension
    (`fixtures/deberta_maverick.npz` -> `fixtures/deberta_maverick.spm`). Both the
    export (writer) and coref_decode_server (reader) import THIS, so the convention has
    a single home and cannot drift into two hand-typed paths."""
    return os.path.splitext(npz_path)[0] + ".spm"


def vendor_spm(npz_path: str, spm_src: str) -> str:
    """Copy the deberta-v3 `spm.model` to the npz's `.spm` sibling so the daemon loads it
    as a LOCAL file (no HF cache at runtime). Returns the destination path. FAIL LOUD
    (ADR-0002) if the source spm.model is absent — without it the daemon cannot tokenise."""
    if not os.path.isfile(spm_src):
        raise FileNotFoundError(
            f"source spm.model not found at {spm_src!r}; cannot vendor the tokenizer. "
            f"It is maverick's encoder sub-word model (the deberta-v3 spm.model).")
    dst = spm_sibling_path(npz_path)
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    shutil.copyfile(spm_src, dst)
    return dst


def resolve_maverick_spm(mav, tok_name: str) -> str:
    """The on-disk `spm.model` maverick's encoder tokenizer was built from — the
    authoritative source to vendor. Prefer the tokenizer's own `vocab_file` (the exact
    file maverick loaded); fall back to the local HF hub cache resolver the guest
    preprocessor uses (one spm-cache resolver, P1) when the attribute is unavailable."""
    tok = getattr(getattr(mav, "model", None), "tokenizer", None)
    vocab_file = getattr(tok, "vocab_file", None)
    if vocab_file and os.path.isfile(vocab_file):
        return os.path.realpath(vocab_file)
    from coref_decode_inputs import StandalonePreprocessor
    return StandalonePreprocessor._resolve_cached_spm(tok_name)


def save_npz(out_path: str, params: dict, cfg: DebertaCfg,
             encoder_hf_model_name: str) -> int:
    """THE one npz codec (ADR-0012 P1/P7): weights under their original torch keys +
    one `__cfg__<field>` scalar per DebertaCfg field + the `__tokenizer__` encoder HF
    model name. Both the maverick export below and the guest vanilla-deberta round-trip
    test call THIS — there is no second hand-written npz format that could drift from it.
    `encoder_hf_model_name` is REQUIRED (no default): the tokenizer identity is part of
    the codec contract, so the weights can never be written WITHOUT recording which
    tokenizer produces their input_ids (R2/F1 — the identity travels with the weights,
    like the cfg). `params` may be jax or numpy arrays; each is pulled to float32 numpy
    for `np.savez`. Returns the weight-tensor count."""
    arrays: dict[str, np.ndarray] = {
        k: np.asarray(v, dtype=np.float32) for k, v in params.items()
    }
    overlap = [f for f in DebertaCfg._fields if f"__cfg__{f}" in arrays]
    assert not overlap, f"weight key collides with a __cfg__ field name: {overlap}"
    assert TOKENIZER_KEY not in arrays, f"weight key collides with {TOKENIZER_KEY}"
    for field in DebertaCfg._fields:  # field set derived from the NamedTuple (P1)
        arrays[f"__cfg__{field}"] = np.asarray(getattr(cfg, field))
    # 0-d unicode array; load_deberta_npz reads it back with .item() -> python str.
    arrays[TOKENIZER_KEY] = np.asarray(str(encoder_hf_model_name))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    np.savez(out_path, **arrays)
    return len(params)


def export(out_path: str, hf_name_or_path: str | None = None) -> int:
    from maverick import Maverick

    import deberta_weights
    from maverick_load import safe_maverick_load

    with safe_maverick_load():
        # weight conversion only — CPU, no forward, no GPU. device placement stays in the
        # caller (the device-transfer single-home rule), exactly as validate_deberta_keyset.
        mav = (Maverick(device="cpu") if hf_name_or_path is None
               else Maverick(hf_name_or_path, device="cpu"))
    mav.model.float()                 # match the daemon's fp32 contract
    enc = mav.model.encoder           # the DebertaV2Model maverick encodes with
    # the TOKENIZER IDENTITY: maverick's OWN SSOT for which HF tokenizer produced the
    # input_ids this encoder was fine-tuned on (model_*.py: AutoTokenizer.from_pretrained(
    # encoder_hf_model_name)). We export THIS so the daemon tokenizes with the same vocab
    # the weights expect — never a daemon-side constant (R2/F1).
    tok_name = mav.model.encoder_hf_model_name
    print(f"maverick encoder: {type(enc).__name__} | config: {type(enc.config).__name__} "
          f"| tokenizer: {tok_name}", flush=True)

    # PROVEN, keyset-guarded conversion (fails loud on any config/keyset divergence).
    cfg = deberta_weights.cfg_from_hf(enc.config)
    params = deberta_weights.params_from_state_dict(enc.state_dict(), cfg)

    # Weights + config + tokenizer identity -> the ONE npz codec (shared with the test).
    n_w = save_npz(out_path, params, cfg, tok_name)
    print(f"PASS — wrote {out_path}: {n_w} weight tensors + {len(DebertaCfg._fields)} "
          f"cfg fields + tokenizer={tok_name!r}. Keyset bijection held "
          f"(deberta_weights asserted it).", flush=True)
    print(f"cfg = {cfg}", flush=True)

    # VENDOR the sentencepiece model next to the weights so the daemon tokenises with a
    # LOCAL spm.model — no transformers/huggingface_hub at runtime (P7 self-describing
    # artifact). The .spm is maverick's OWN encoder sub-word model (the same vocab the
    # fine-tuned weights expect), shipped as the npz's sibling.
    spm_src = resolve_maverick_spm(mav, tok_name)
    spm_dst = vendor_spm(out_path, spm_src)
    print(f"PASS — vendored spm.model: {spm_src} -> {spm_dst} "
          f"({os.path.getsize(spm_dst)} bytes).", flush=True)
    print("The unified jax-only daemon loads THESE TWO (npz + .spm): no torch, no "
          "maverick, no transformers/huggingface_hub at runtime.", flush=True)
    return 0


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(here, "fixtures", "deberta_maverick.npz"),
                    help="output .npz (default %(default)s)")
    ap.add_argument("--hf", default=None,
                    help="maverick hf name or local checkpoint path (default: maverick's default)")
    args = ap.parse_args()
    return export(args.out, args.hf)


if __name__ == "__main__":
    raise SystemExit(main())
