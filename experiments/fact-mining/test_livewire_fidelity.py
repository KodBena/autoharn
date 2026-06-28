#!/usr/bin/env python
"""HOST live-wire fidelity proof: the FULL live coref path (torch ENCODE here +
JAX-DAEMON DECODE) == maverick's full `predict`, BIT-EXACT cluster SETS.

This is the Stage 1b-ii capstone. test_decode_daemon_fidelity.py already proves the
daemon's decode equals maverick's *captured* clusters when REPLAYING fixture
last_hidden_states. THIS test closes the remaining gap: it drives the actual live
path end to end on freshly-loaded maverick —

    text
      -> coref_decode_inputs.prepare_decode_inputs   (the SSOT preprocess+tokenize)
      -> nlp_server.encode_last_hidden_state          (maverick's torch deberta encoder)
      -> coref_decode_client.RemoteDecode.decode      (ship to the JAX decode daemon)
      -> coref_decode_inputs.clusters_token_to_char_offsets  (token->char mapping)

— and asserts, for each sample paragraph, that BOTH the token-offset cluster sets AND
the char-offset cluster sets equal maverick's own `predict(text)` output (ADR-0009:
the DISCRETE cluster sets must match bit-for-bit). A single flipped mantissa bit in
the torch->wire->jax hand-off near a sigmoid>0.5 / argmax boundary would show here.

For the CHAR clusters it drives the ACTUAL server orchestration —
`Server._run_coref(..., "jax-daemon", ...)` -> `Server.coref_clusters_jax_daemon`,
wired (via `Server.__new__` + preset `_coref`/`_decoders`) to this test's maverick and
daemon — so a green run certifies the live method's composition and the backend
dispatch, not a re-inlined parallel copy. (The only live seam not driven here is the
JSON `handle()` frame parse, which needs the spaCy pipeline; the request-field routing
above it is exercised by `_run_coref`.) The token offsets are decoded once more at the
leaf for the most sensitive bit-exact probe, since the server surfaces only char spans.
The decode daemon runs as a real subprocess, weights extracted from the very model we
encode with (so daemon weights == encoder model, no fixture dependency).

FAIL LOUD (ADR-0002). Skip ONLY on a genuine ModuleNotFoundError for the host-only
stack (maverick / torch / jax / zmq). Every other failure — daemon won't start, a real
protocol/decode bug, a cluster mismatch — RAISES. There is NO broad
`except Exception: skip`: that exact anti-pattern once turned a real import error into a
silent "host-only, skipped". Never again.

Host-only WIRE+MODEL scaffolding (it loads maverick on the GPU AND drives a jax
subprocess); like the other fidelity tests it is deliberately NOT in the import-XOR /
device-transfer gates' SCANNED set.

GPU co-residency: this runs maverick (torch) and the JAX decode daemon on the SAME
card. The daemon caps XLA at MEM_FRACTION=0.3; maverick takes its share. On a small
card, export MAVERICK_DEVICE=cpu to encode on CPU and leave the GPU to the daemon.

Run (on the host, in the maverick+jax env):
    python -m pytest test_livewire_fidelity.py    (NOT bare `pytest`: on this host the
    `pytest` console script may dispatch to an interpreter without jax and falsely skip)
or: python test_livewire_fidelity.py
"""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
import sys
import tempfile
import time

# Make sibling modules importable however this file is invoked (pytest / python / cwd).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import numpy as np                 # fixture/weights I/O (host); also used by the wire client
    import zmq                         # transport to the daemon
    import jax                         # the daemon needs jax; absence == guest -> legit skip
    import torch                       # maverick's framework
    from maverick import Maverick      # the reference model + the torch encoder
    import coref_decode_client
    from coref_decode_inputs import (clusters_token_to_char_offsets,
                                     prepare_decode_inputs)
    from maverick_load import safe_maverick_load
    from nlp_server import Server, encode_last_hidden_state
    from capture_fixtures import extract_weights
except ModuleNotFoundError as exc:     # genuinely no maverick/torch/jax/zmq -> legit skip
    _HAVE_DEPS = False
    _IMPORT_ERR = exc
else:
    _HAVE_DEPS = True
    # NOT guarded beyond ModuleNotFoundError: a failure importing a sibling we wrote is
    # a REAL bug, not a benign skip (the bug the old broad-except once masked).

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "coref_decode_server.py")

# Self-contained sample paragraphs with explicit coreference (named entity + pronouns),
# so the path actually produces >=2-mention clusters (stage-3 antecedent argmax fires).
SAMPLE_PARAGRAPHS = [
    "Galen was a physician in Pergamon. He later moved to Rome, where he treated the "
    "emperor. His writings shaped medicine for many centuries.",
    "Marie Curie discovered radium. She won two Nobel Prizes, and her research on "
    "radioactivity made her one of the most famous scientists of her time.",
    "The old hospital opened in 1900. It served the whole town for decades, and the "
    "doctors who worked there praised it for its modern equipment.",
]


def _cluster_set(clusters) -> set:
    """Order-independent canonical form: a set of frozensets of (start, end)."""
    return {frozenset((int(s), int(e)) for s, e in cluster) for cluster in clusters}


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def _daemon(weights_path: str):
    """Start coref_decode_server.py as a subprocess on a loopback port, wait until it
    answers ping, yield a connected RemoteDecode, and tear it down. The daemon OWNS the
    only jax process; this test process drives the wire and runs torch/maverick."""
    addr = f"tcp://127.0.0.1:{_free_port()}"
    env = dict(os.environ)
    env.setdefault("XLA_PYTHON_CLIENT_MEM_FRACTION", "0.3")  # polite GPU tenant beside torch
    proc = subprocess.Popen(
        [sys.executable, SERVER, "--addr", addr, "--weights", weights_path],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        client = coref_decode_client.RemoteDecode(addr, timeout_ms=120_000)
        deadline = time.time() + 180  # jax import + weight load can take a while
        while True:
            if proc.poll() is not None:  # daemon died during startup -> FAIL LOUD
                out = proc.stdout.read() if proc.stdout else ""
                raise RuntimeError(
                    f"decode daemon exited early (code {proc.returncode}):\n{out}")
            try:
                if client.ping(timeout_ms=2_000).get("ok"):
                    break
            except coref_decode_client.RemoteError:
                pass  # not up yet; ONLY a ping-timeout is swallowed, nothing else
            if time.time() > deadline:
                raise RuntimeError("decode daemon did not answer ping within 180s")
            time.sleep(0.5)
        yield client, addr
    finally:
        proc.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)
        if proc.poll() is None:
            proc.kill()


def _load_maverick():
    """Load maverick once, forced fp32 (matches nlp_server's coref() and the daemon's
    fp32 decode contract). Device: GPU by default, or MAVERICK_DEVICE=cpu to spare the
    card for the daemon."""
    dev = os.environ.get("MAVERICK_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")
    with safe_maverick_load():
        mav = Maverick(device=dev)
    mav.model.float()  # fp32: maverick's decisions are sigmoid>0.5 / argmax; match the daemon
    return mav


def _server_shim(mav, client, addr):
    """A real `Server` instance whose live coref methods are wired to THIS test's
    already-loaded maverick and running decode daemon — without `__init__` (which
    would reload spaCy + maverick and bind a socket). `coref()` returns our `mav`
    (since `_coref` is preset, the lazy loader short-circuits) and `_decoder(addr)`
    returns our `client`. So `srv.coref_clusters_jax_daemon` / `srv._run_coref` run
    the ACTUAL live orchestration, not a parallel copy."""
    srv = Server.__new__(Server)
    srv._coref = mav
    srv._decoders = {addr: client}
    srv.coref_backend = "jax-daemon"
    srv.decode_addr = addr
    return srv


def _live_path(mav, client, addr, text):
    """The FULL live coref path for one text.

    CHAR clusters are produced by driving the REAL server orchestration through
    `Server._run_coref(..., backend="jax-daemon", ...)` -> `coref_clusters_jax_daemon`
    (via `_server_shim`). So the live method's composition — the per-paragraph loop,
    the `singletons=False` choice, the `clusters_token_to_char_offsets` call, the
    `or []` — and the backend dispatch are CERTIFIED here, not re-inlined (closes the
    Stage-1b-ii review's 'orchestration is a parallel copy' finding).

    TOKEN clusters are decoded once more at the leaf (`client.decode`) because the
    server surfaces only char offsets; this keeps the most sensitive bit-exact probe
    (a flipped mantissa bit near a sigmoid>0.5 / argmax boundary shows in the raw
    token offsets). Decode is deterministic, so the extra round-trip is consistent.
    Returns (got_token_clusters, got_char_clusters)."""
    srv = _server_shim(mav, client, addr)
    got_char = srv._run_coref([text], "live", "jax-daemon", addr)[0][0]     # REAL orchestration

    di = prepare_decode_inputs(mav, text)                                   # SSOT prep
    lhs = encode_last_hidden_state(mav.model, di.input_ids, di.attention_mask)  # torch encode
    got_tok = client.decode(                                                # ship to JAX daemon
        lhs=lhs, attention_mask=di.attention_mask, eos_mask=di.eos_mask,
        tokens=di.tokens, subtoken_map=di.subtoken_map,
        new_token_map=di.new_token_map, singletons=False)
    return got_tok, got_char


def _require():
    if not _HAVE_DEPS:
        import pytest
        pytest.skip(f"maverick/torch/jax/zmq unavailable (host-only test): {_IMPORT_ERR}")


def test_livewire_token_and_char_clusters_match_maverick():
    """Full torch-encode + jax-daemon-decode == maverick.predict, for BOTH the token
    offsets and the char offsets, on every sample paragraph (bit-exact cluster sets)."""
    _require()
    mav = _load_maverick()

    # daemon weights == the very model we encode with (extracted post-fp32-cast).
    with tempfile.TemporaryDirectory() as td:
        weights_path = os.path.join(td, "weights.npz")
        np.savez(weights_path, **extract_weights(mav.model))

        tok_failures, char_failures = [], []
        ref_tok_all = []
        with _daemon(weights_path) as (client, addr):
            for text in SAMPLE_PARAGRAPHS:
                ref = mav.predict(text)  # singletons=False (default) — the reference
                ref_tok = ref["clusters_token_offsets"]
                ref_char = ref["clusters_char_offsets"]
                ref_tok_all.append(ref_tok)

                got_tok, got_char = _live_path(mav, client, addr, text)

                if _cluster_set(got_tok) != _cluster_set(ref_tok):
                    tok_failures.append(
                        f"  token sets differ for {text!r}\n"
                        f"    only live : {sorted(map(sorted, _cluster_set(got_tok) - _cluster_set(ref_tok)))}\n"
                        f"    only mav  : {sorted(map(sorted, _cluster_set(ref_tok) - _cluster_set(got_tok)))}")
                if _cluster_set(got_char) != _cluster_set(ref_char):
                    char_failures.append(
                        f"  char sets differ for {text!r}\n"
                        f"    only live : {sorted(map(sorted, _cluster_set(got_char) - _cluster_set(ref_char)))}\n"
                        f"    only mav  : {sorted(map(sorted, _cluster_set(ref_char) - _cluster_set(got_char)))}")

    assert not tok_failures, (
        "live-wire TOKEN-offset divergence from maverick (ADR-0009 discrete invariant):\n"
        + "\n".join(tok_failures))
    assert not char_failures, (
        "live-wire CHAR-offset divergence from maverick (token->char mapping):\n"
        + "\n".join(char_failures))

    # NON-VACUITY (same guard the other fidelity proofs use): an all-empty pass proves
    # nothing. The reference must actually produce clusters, and at least one with >=2
    # mentions, so stage-3 antecedent argmax really fired over the wire.
    assert any(ref for ref in ref_tok_all), (
        "VACUOUS: maverick produced NO clusters on ANY sample paragraph")
    assert any(any(len(c) >= 2 for c in ref) for ref in ref_tok_all), (
        "VACUOUS: no >=2-mention cluster in any sample — stage-3 argmax never exercised")


if __name__ == "__main__":
    if not _HAVE_DEPS:
        raise SystemExit(f"maverick/torch/jax/zmq unavailable: {_IMPORT_ERR}")
    mav = _load_maverick()
    with tempfile.TemporaryDirectory() as td:
        wp = os.path.join(td, "weights.npz")
        np.savez(wp, **extract_weights(mav.model))
        ok = True
        with _daemon(wp) as (client, addr):
            for text in SAMPLE_PARAGRAPHS:
                ref = mav.predict(text)
                got_tok, got_char = _live_path(mav, client, addr, text)
                t_ok = _cluster_set(got_tok) == _cluster_set(ref["clusters_token_offsets"])
                c_ok = _cluster_set(got_char) == _cluster_set(ref["clusters_char_offsets"])
                ok = ok and t_ok and c_ok
                print(f"  {'PASS' if (t_ok and c_ok) else 'FAIL'} token={t_ok} char={c_ok} "
                      f"(live={len(got_tok)} clusters, maverick={len(ref['clusters_token_offsets'])}) "
                      f"{text[:48]!r}")
    print("ALL BIT-EXACT" if ok else "DIVERGENCE")
    raise SystemExit(0 if ok else 1)
