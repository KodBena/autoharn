#!/usr/bin/env python
"""THE HEADLINE gate: the unified coref daemon is STRUCTURALLY torch-free.

The whole workflow's point (ADR-0012 host-XOR-device / device single-home) is to
ELIMINATE the torch/jax coexistence, not relocate it into the daemon. The trap is that
the daemon's torch-free-LOOKING deps (`transformers` and `spaCy`) drag torch in
transitively, which a STATIC import scan cannot see. So this is a RUN-TIME proof
(ADR-0011 Rule 1: the strongest feasible surface for a failure the static gate misses).

Each check runs in a SUBPROCESS because `jax_only_guard.install()` poisons `torch`
process-globally (it must, to make "no torch" unrepresentable, not merely "not yet
imported"); poisoning the shared pytest process would break torch-using tests. The
subprocess mirrors the daemon's exact startup: guard.install() -> build the torch-free
preprocess (spaCy + HF tokenizer) -> load the deberta npz the daemon way (np.load) ->
jax encode -> assert_torch_free. If torch ever materialises, the daemon dies loudly.

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
_TORCH_FREE_FORWARD = r'''
import sys, json
import jax_only_guard
jax_only_guard.install()                      # poison torch + stub the trf plugins

# the torch-free SSOT preprocess (spaCy en_core_web_sm + deberta-v3 fast tokenizer)
from coref_decode_inputs import StandalonePreprocessor, prepare_decode_inputs
pre = StandalonePreprocessor.from_pretrained("microsoft/deberta-v3-large")

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
    "transformers_loaded": "transformers" in sys.modules,
    "spacy_loaded": "spacy" in sys.modules,
    "torch_import_blocked": blocked,
    "lhs_shape": list(lhs.shape),
    "n_clusters_inputs": len(di.input_ids),
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
    """Parent-side (torch OK): build a vanilla deberta npz with the daemon's npz codec."""
    from deberta_weights import load_jax_deberta
    from export_deberta_maverick import save_npz
    params, cfg, _ = load_jax_deberta("microsoft/deberta-v3-large")
    save_npz(path, params, cfg, "microsoft/deberta-v3-large")  # tokenizer identity required


def test_unified_forward_is_torch_free():
    """spaCy + transformers + jax run the encode half of the unified forward in ONE
    process that imports jax and NEVER a real torch — the coexistence eliminated."""
    with tempfile.TemporaryDirectory() as d:
        npz = os.path.join(d, "deberta_vanilla.npz")
        _make_vanilla_npz(npz)
        r = _run(_TORCH_FREE_FORWARD, npz)
    assert r["torch_real"] is False, f"torch materialised in the daemon process: {r}"
    assert r["torch_import_blocked"] is True, "import torch must be blocked (poisoned)"
    assert r["jax_loaded"] and r["transformers_loaded"] and r["spacy_loaded"], (
        f"the daemon must load spaCy+transformers+jax (all torch-free): {r}")
    assert r["lhs_shape"][0] == 1 and r["lhs_shape"][-1] == 1024, f"bad encode shape: {r}"


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
    test_unified_forward_is_torch_free()
    print("PASS unified forward (spaCy+transformers+jax encode) is torch-free")
