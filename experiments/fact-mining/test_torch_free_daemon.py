#!/usr/bin/env python
"""THE HEADLINE gate: the unified coref daemon is STRUCTURALLY torch-free.

The whole workflow's point (ADR-0012 host-XOR-device / device single-home) is to
ELIMINATE the torch/jax coexistence, not relocate it into the daemon. The trap is that
the daemon's torch-free-LOOKING dep `spaCy` drags torch in transitively (via its trf
plugins), which a STATIC import scan cannot see. So this is a RUN-TIME proof (ADR-0011
Rule 1: the strongest feasible surface for a failure the static gate misses). The daemon
no longer imports `transformers` AT ALL — it tokenises with raw sentencepiece from the
vendored spm.model — so this test also asserts the WHOLE HF surface (transformers /
huggingface_hub / tokenizers) is absent from the process, not merely torch.

Each check runs in a SUBPROCESS because `jax_only_guard.install()` blocks `torch`
process-globally (it must, to make "no torch" unrepresentable, not merely "not yet
imported"); blocking it in the shared pytest process would break torch-using tests. The
subprocess mirrors the daemon's exact startup: guard.install() -> build the torch-free
preprocess (spaCy + raw sentencepiece from the vendored spm.model) -> load the deberta
npz the daemon way (np.load) -> jax encode -> assert_torch_free. If torch ever
materialises, the daemon dies loudly.

Guest-runnable: the parent builds a VANILLA deberta npz (needs torch) and hands the path
to the torch-free subprocess. The decode-tail weights are host-only, so the subprocess
proves the encode half of the unified forward torch-free; the full decode->clusters
torch-free run + the bit-exact cluster fidelity are the HOST --coref-verify.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# Subprocess: the daemon's torch-free startup + a real encode, all under the guard.
# argv[1] is the vendored deberta npz; the .spm sibling sits next to it (the daemon's
# real tokenizer-load path — RAW sentencepiece, no transformers/huggingface_hub).
_TORCH_FREE_FORWARD = r'''
import sys, json
import jax_only_guard
jax_only_guard.install()                      # block torch + stub the trf plugins

# the torch-free, TRANSFORMERS-free SSOT preprocess: spaCy en_core_web_sm + RAW
# sentencepiece from the VENDORED spm.model (the npz's .spm sibling) — exactly the
# daemon's from_spm path, no HF cache, no transformers/huggingface_hub.
from coref_decode_inputs import StandalonePreprocessor, prepare_decode_inputs
from export_deberta_maverick import spm_sibling_path
pre = StandalonePreprocessor.from_spm(spm_sibling_path(sys.argv[1]))

# the daemon's deberta load path: np.load only (no torch), then the jax home lifts/builds
from coref_decode_server import load_deberta_npz
import coref_host_shell, jax_deberta
host_w, cfg_fields, tok_name = load_deberta_npz(sys.argv[1])
cfg = coref_host_shell.build_deberta_cfg(cfg_fields)
coref_host_shell.validate_deberta_load(host_w, cfg)   # the daemon's load-time keyset gate (R3/F1)
params = coref_host_shell.lift_deberta_params(host_w)

# a real encode through the jax home, exactly as the unified op does
di = prepare_decode_inputs(pre, "John saw Mary. He waved at her happily.")
import jax.numpy as jnp
lhs = jax_deberta.encode(params, jnp.asarray([di.input_ids]), jnp.asarray([di.attention_mask]), cfg)

jax_only_guard.assert_torch_free()            # FAIL LOUD if torch crept in anywhere

# prove torch is genuinely blocked (poisoned), not merely absent
try:
    import torch
    blocked = False
except ImportError:
    blocked = True

print("RESULT " + json.dumps({
    "torch_real": sys.modules.get("torch") is not None,
    "jax_loaded": "jax" in sys.modules,
    "sentencepiece_loaded": "sentencepiece" in sys.modules,
    "spacy_loaded": "spacy" in sys.modules,
    # the HF surface must be GONE from the daemon process — never imported at all
    "transformers_loaded": "transformers" in sys.modules,
    "huggingface_hub_loaded": "huggingface_hub" in sys.modules,
    "tokenizers_loaded": "tokenizers" in sys.modules,
    "torch_import_blocked": blocked,
    "lhs_shape": list(lhs.shape),
    "n_clusters_inputs": len(di.input_ids),
}))
'''

# Subprocess: the TOKENIZER path alone — build the spm StandalonePreprocessor under the
# guard and tokenize, asserting the WHOLE HF surface (transformers/huggingface_hub/
# tokenizers) AND torch are absent. This is the targeted sys.modules proof for the
# sentencepiece tokenizer swap; it needs only the tiny vendored spm.model (~2.4MB), so it
# fits any VM (unlike the full deberta-v3-large encode above, which is memory-heavy). It
# is the precise gate: tokenising with raw sentencepiece pulls NO transformers/hf/torch.
_TOKENIZER_TORCH_FREE = r'''
import sys, json
import jax_only_guard
jax_only_guard.install()                      # block torch + stub spaCy's trf plugins

from coref_decode_inputs import StandalonePreprocessor, prepare_decode_inputs
pre = StandalonePreprocessor.from_spm(sys.argv[1])   # raw sentencepiece from a local file
di = prepare_decode_inputs(pre, "John saw Mary. He waved at her happily. They left.")

jax_only_guard.assert_torch_free()            # FAIL LOUD if torch crept in via spaCy etc.
try:
    import torch
    blocked = False
except ImportError:
    blocked = True

print("RESULT " + json.dumps({
    "torch_real": sys.modules.get("torch") is not None,
    "torch_import_blocked": blocked,
    "sentencepiece_loaded": "sentencepiece" in sys.modules,
    "spacy_loaded": "spacy" in sys.modules,
    "transformers_loaded": "transformers" in sys.modules,
    "huggingface_hub_loaded": "huggingface_hub" in sys.modules,
    "tokenizers_loaded": "tokenizers" in sys.modules,
    "n_input_ids": len(di.input_ids),
    "n_clusters_inputs_ok": len(di.input_ids) > 0,
}))
'''

# Subprocess: merely importing the daemon module must not pull torch (lazy guard/deps).
_IMPORT_ONLY = r'''
import sys, json
import coref_decode_server   # noqa: F401
print("RESULT " + json.dumps({"torch_after_import": "torch" in sys.modules}))
'''


def _run(script: str, *args: str) -> dict:
    import json
    env = dict(os.environ, JAX_PLATFORMS="cpu")
    proc = subprocess.run([sys.executable, "-c", script, *args],
                          cwd=HERE, env=env, capture_output=True, text=True)
    line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT ")), None)
    assert line is not None, (
        f"subprocess produced no RESULT (exit {proc.returncode}).\n"
        f"STDOUT:\n{proc.stdout[-2000:]}\nSTDERR:\n{proc.stderr[-3000:]}")
    return json.loads(line[len("RESULT "):])


def _make_vanilla_npz(path: str):
    """Parent-side (torch OK): build a vanilla deberta npz with the daemon's npz codec
    AND vendor the deberta-v3 spm.model next to it (the .spm sibling), exactly as
    export_deberta_maverick does — so the torch-free subprocess loads the tokenizer the
    DEPLOYMENT way (RAW sentencepiece from a local file), not from the HF cache."""
    from coref_decode_inputs import StandalonePreprocessor
    from deberta_weights import load_jax_deberta
    from export_deberta_maverick import save_npz, vendor_spm
    params, cfg, _ = load_jax_deberta("microsoft/deberta-v3-large")
    save_npz(path, params, cfg, "microsoft/deberta-v3-large")  # tokenizer identity required
    vendor_spm(path, StandalonePreprocessor._resolve_cached_spm("microsoft/deberta-v3-large"))


def test_unified_forward_is_torch_free():
    """spaCy + sentencepiece + jax run the encode half of the unified forward in ONE
    process that imports jax and NEVER a real torch — AND never `transformers` /
    `huggingface_hub` / `tokenizers` at all (the entire HF surface eliminated, not just
    torch): the daemon tokenises with raw sentencepiece from the vendored spm.model."""
    with tempfile.TemporaryDirectory() as d:
        npz = os.path.join(d, "deberta_vanilla.npz")
        _make_vanilla_npz(npz)
        r = _run(_TORCH_FREE_FORWARD, npz)
    assert r["torch_real"] is False, f"torch materialised in the daemon process: {r}"
    assert r["torch_import_blocked"] is True, "import torch must be blocked (poisoned)"
    assert r["jax_loaded"] and r["sentencepiece_loaded"] and r["spacy_loaded"], (
        f"the daemon must load spaCy+sentencepiece+jax (all torch-free): {r}")
    # the HF surface must be ENTIRELY absent from the daemon process (sys.modules proof)
    assert r["transformers_loaded"] is False, (
        f"transformers must NOT be imported by the daemon (raw sentencepiece only): {r}")
    assert r["huggingface_hub_loaded"] is False, (
        f"huggingface_hub must NOT be imported by the daemon: {r}")
    assert r["tokenizers_loaded"] is False, (
        f"the HF `tokenizers` lib must NOT be imported by the daemon: {r}")
    assert r["lhs_shape"][0] == 1 and r["lhs_shape"][-1] == 1024, f"bad encode shape: {r}"


def test_tokenizer_path_is_torch_and_hf_free():
    """THE sys.modules proof for the sentencepiece tokenizer swap: building the spm
    StandalonePreprocessor and tokenising in ONE guarded process imports raw
    sentencepiece + spaCy + jax-guard, and NEVER torch, `transformers`, `huggingface_hub`,
    or `tokenizers`. Needs only the tiny vendored spm.model, so it runs on any VM (the
    full deberta-v3-large encode in test_unified_forward_is_torch_free is the broader,
    memory-heavy proof of the same property over the WHOLE forward)."""
    from coref_decode_inputs import StandalonePreprocessor
    from export_deberta_maverick import vendor_spm
    with tempfile.TemporaryDirectory() as d:
        npz = os.path.join(d, "deberta_maverick.npz")  # only its .spm sibling is needed here
        spm_dst = vendor_spm(npz, StandalonePreprocessor._resolve_cached_spm(
            "microsoft/deberta-v3-large"))
        r = _run(_TOKENIZER_TORCH_FREE, spm_dst)
    assert r["torch_real"] is False, f"torch materialised in the tokenizer process: {r}"
    assert r["torch_import_blocked"] is True, "import torch must be blocked under the guard"
    assert r["sentencepiece_loaded"] and r["spacy_loaded"], (
        f"the spm preprocess must load sentencepiece + spaCy: {r}")
    assert r["transformers_loaded"] is False, f"transformers must NOT be imported: {r}"
    assert r["huggingface_hub_loaded"] is False, f"huggingface_hub must NOT be imported: {r}"
    assert r["tokenizers_loaded"] is False, f"the HF tokenizers lib must NOT be imported: {r}"
    assert r["n_clusters_inputs_ok"], f"tokenize produced no input_ids: {r}"


def test_daemon_module_import_does_not_pull_torch():
    """Importing coref_decode_server (without enabling coref) must not pull torch — the
    guard + transformers/spaCy are lazy, so a plain import stays torch-free."""
    r = _run(_IMPORT_ONLY)
    assert r["torch_after_import"] is False, "importing the daemon module pulled torch"


def test_assert_torch_free_fails_loud_when_torch_present():
    """Mutation self-check (in-process, no poison): assert_torch_free raises if a REAL
    torch module is present. We simulate with a sentinel module and restore."""
    import jax_only_guard
    saved = sys.modules.get("torch", "absent")
    sys.modules["torch"] = type(sys)("torch")  # a real (non-None) module object
    try:
        raised = False
        try:
            jax_only_guard.assert_torch_free()
        except RuntimeError:
            raised = True
        assert raised, "assert_torch_free must raise when a real torch module is present"
    finally:
        if saved == "absent":
            del sys.modules["torch"]
        else:
            sys.modules["torch"] = saved


if __name__ == "__main__":
    test_assert_torch_free_fails_loud_when_torch_present()
    print("PASS assert_torch_free fails loud on a present torch")
    test_daemon_module_import_does_not_pull_torch()
    print("PASS daemon module import is torch-free")
    test_tokenizer_path_is_torch_and_hf_free()
    print("PASS spm tokenizer path is torch-free AND hf-free (no transformers/"
          "huggingface_hub/tokenizers)")
    test_unified_forward_is_torch_free()
    print("PASS unified forward (spaCy+sentencepiece+jax encode) is torch-free")
