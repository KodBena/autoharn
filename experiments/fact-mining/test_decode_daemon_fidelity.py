#!/usr/bin/env python
"""HOST over-the-wire fidelity proof: the JAX decode DAEMON == maverick, BIT-EXACT
cluster sets. End-to-end through ZMQ.

This is test_jax_decode_fidelity.py's invariant (ADR-0009: the DISCRETE cluster
SETS, as sets of token-offset spans, must equal maverick's captured
`clusters_token_offsets`), now driven THROUGH THE WIRE: we start
coref_decode_server.py as a subprocess, ship each ./fixtures paragraph's
intermediates with coref_decode_client.RemoteDecode, and assert the returned
cluster sets match maverick's — for BOTH `singletons` flags. If the raw-float32
wire round-trip perturbed `last_hidden_state` by even one mantissa bit near a
decision boundary, this is the test that would catch it.

A WIRE-INTEGRITY unit (no daemon, no fixtures, no maverick) additionally proves
the pack/unpack is byte-identical, so a failure of the end-to-end test can be
localized to the decode math vs the transport.

FAIL LOUD (ADR-0002). We skip ONLY on genuine jax/zmq absence
(ModuleNotFoundError) — the guest. Every other failure (daemon won't start, a
real protocol/decoding bug) raises. We do NOT wrap the body in a broad
`except Exception: skip`: that exact anti-pattern once turned a real import error
into a silent "host-only, skipped" and cost a full debugging round. Never again.

This file is host-only WIRE scaffolding (numpy fixture I/O + the zmq client +
launching a jax subprocess); like test_jax_decode_fidelity.py it is deliberately
NOT in the import-XOR / device-transfer gates' SCANNED set.

Run: python -m pytest test_decode_daemon_fidelity.py     (use `python -m pytest`,
NOT bare `pytest` — on this host the `pytest` console script dispatches to an
interpreter without jax and would falsely "skip". Or: python test_decode_daemon_fidelity.py)
"""

from __future__ import annotations

import contextlib
import glob
import json
import os
import socket
import subprocess
import sys
import time

import numpy as np

# Make the port importable however this file is invoked (pytest / python / other cwd).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import zmq  # transport (client + daemon)
    import jax  # the daemon needs jax; absence == the guest -> legitimate skip
    import coref_decode_client
except ModuleNotFoundError as exc:        # genuinely no jax/zmq (the guest) -> legit skip
    _HAVE_DEPS = False
    _IMPORT_ERR = exc
else:
    _HAVE_DEPS = True
    # NOT guarded beyond ModuleNotFoundError: a failure importing the client is a
    # REAL bug, not a benign skip (the bug the old broad-except masked).

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
SERVER = os.path.join(HERE, "coref_decode_server.py")


def _cluster_set(clusters) -> set:
    """Order-independent canonical form: a set of frozensets of (start,end)."""
    return {frozenset((int(s), int(e)) for s, e in cluster) for cluster in clusters}


def _cases():
    return sorted(glob.glob(os.path.join(FIXTURES, "para_*.npz")))


def _free_port() -> int:
    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def _daemon(weights_path: str):
    """Start coref_decode_server.py as a subprocess on a loopback port, wait until
    it answers ping, yield a connected RemoteDecode, and tear it down. The daemon
    OWNS the only jax process here — the test process just drives the wire."""
    port = _free_port()
    addr = f"tcp://127.0.0.1:{port}"
    env = dict(os.environ)
    env.setdefault("XLA_PYTHON_CLIENT_MEM_FRACTION", "0.3")  # be a polite GPU tenant
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
                pass  # not up yet; only a ping-timeout is swallowed, nothing else
            if time.time() > deadline:
                raise RuntimeError("decode daemon did not answer ping within 180s")
            time.sleep(0.5)
        yield client
    finally:
        proc.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=10)
        if proc.poll() is None:
            proc.kill()


def _load_case(npz_path: str):
    stem = npz_path[:-len(".npz")]
    with open(stem + ".json", encoding="utf-8") as fh:
        meta = json.load(fh)
    with np.load(npz_path) as z:
        lhs = np.asarray(z["last_hidden_state"], dtype=np.float32)
        attention_mask = z["attention_mask"].tolist()
        eos_mask = z["eos_mask"].tolist()
    return meta, lhs, attention_mask, eos_mask


def _run_case(client, npz_path: str, singletons: bool):
    meta, lhs, attention_mask, eos_mask = _load_case(npz_path)
    got = client.decode(
        lhs=lhs, attention_mask=attention_mask, eos_mask=eos_mask,
        tokens=meta["tokens"], subtoken_map=meta["subtoken_map"],
        new_token_map=meta["new_token_map"], singletons=singletons)
    key = "clusters_token_offsets_singletons" if singletons else "clusters_token_offsets"
    return _cluster_set(got), _cluster_set(meta[key])


# ================================================ wire-integrity unit (no daemon)
def test_lhs_wire_roundtrip_is_bit_exact():
    """The transport itself loses NO bits: pack -> unpack reproduces the float32
    array byte-for-byte. Localizes any end-to-end failure to the decode math, not
    the wire. Needs neither a daemon, fixtures, nor jax — only numpy."""
    rng = np.random.default_rng(0)
    # include values that stress float32: tiny, huge, negative, subnormal, exact halves
    lhs = rng.standard_normal((37, 11)).astype(np.float32)
    lhs[0, 0] = np.float32(1e-38)      # near-subnormal
    lhs[1, 1] = np.float32(-3.4e38)    # near-max magnitude
    lhs[2, 2] = np.float32(0.5)        # exact half (JSON-decimal danger zone)

    from coref_decode_client import pack_lhs
    from coref_decode_server import unpack_lhs, WIRE_DTYPE

    shape, blob = pack_lhs(lhs)
    assert shape == [37, 11]
    assert len(blob) == 37 * 11 * WIRE_DTYPE.itemsize
    # Reconstruct on the HOST side exactly as the daemon does, minus the jax lift.
    back = np.frombuffer(blob, dtype=WIRE_DTYPE).reshape(tuple(shape))
    assert back.dtype == np.float32
    assert np.array_equal(back, lhs), "wire round-trip changed a value"
    assert back.tobytes() == lhs.tobytes(), "wire round-trip changed bytes"


# ========================================== wire-CONTRACT unit (server-side reject)
def test_unpack_lhs_fails_loud_on_bad_wire():
    """unpack_lhs NEVER silently coerces a malformed wire: a truncated blob, a wrong
    declared dtype, or a non-2D shape each raise (ADR-0002 fail-loud), so a protocol
    bug surfaces as an error, not a corrupt-but-plausible decode. Pins the wire
    contract independent of the decode math (complements the bit-exact round-trip
    unit above). Needs jax (the happy path lifts onto the device) -> shares the
    deps gate; the rejection branches themselves raise before any device touch."""
    if not _HAVE_DEPS:
        import pytest
        pytest.skip(f"jax/zmq unavailable (host-only test): {_IMPORT_ERR}")
    import pytest
    from coref_decode_server import unpack_lhs, WIRE_DTYPE

    good = np.ascontiguousarray(np.arange(12, dtype=WIRE_DTYPE).reshape(4, 3))
    blob = good.tobytes()
    meta = {"dtype": "float32", "shape": [4, 3]}

    with pytest.raises(ValueError):                       # one float short -> length mismatch
        unpack_lhs(meta, blob[:-WIRE_DTYPE.itemsize])
    with pytest.raises(ValueError):                       # extra bytes -> length mismatch
        unpack_lhs(meta, blob + b"\x00\x00\x00\x00")
    with pytest.raises(ValueError):                       # wrong declared dtype
        unpack_lhs({"dtype": "float64", "shape": [4, 3]}, blob)
    with pytest.raises(ValueError):                       # non-2D shape
        unpack_lhs({"dtype": "float32", "shape": [4, 3, 1]}, blob)

    # Non-vacuity: the GOOD blob is accepted and lifts to the exact [S, TH] values
    # (so the asserts above reject malformed input, not every input).
    out = unpack_lhs(meta, blob)
    assert tuple(out.shape) == (4, 3)
    assert np.array_equal(np.asarray(out), good)


# ===================================================================== the proof
def _require():
    if not _HAVE_DEPS:
        import pytest
        pytest.skip(f"jax/zmq unavailable (host-only test): {_IMPORT_ERR}")
    cases = _cases()
    if not cases:
        import pytest
        pytest.skip("no fixtures — run capture_fixtures.py on the host first")
    return cases


def test_daemon_decode_bit_exact_cluster_sets():
    """Default (singletons=False): every fixture's wire-decoded cluster set equals
    maverick's captured clusters_token_offsets, end-to-end through the daemon."""
    cases = _require()
    failures, wants = [], []
    with _daemon(os.path.join(FIXTURES, "weights.npz")) as client:
        for npz_path in cases:
            got, want = _run_case(client, npz_path, singletons=False)
            wants.append(want)
            if got != want:
                failures.append(
                    f"{os.path.basename(npz_path)}: cluster sets differ\n"
                    f"    only over-wire JAX: {sorted(map(sorted, got - want))}\n"
                    f"    only in maverick  : {sorted(map(sorted, want - got))}")
    assert not failures, (
        "over-the-wire decode divergence (ADR-0009 discrete invariant):\n"
        + "\n".join(failures))
    # NON-VACUITY (same guard as the in-process proof): an all-empty pass proves
    # nothing. At least one paragraph yields a cluster; at least one cluster has
    # >=2 mentions (so stage-3 antecedent argmax actually fired over the wire).
    assert any(want for want in wants), (
        "VACUOUS: no maverick clusters in ANY fixture — regenerate over real prose")
    assert any(any(len(c) >= 2 for c in want) for want in wants), (
        "VACUOUS: no fixture has a >=2-mention cluster — stage-3 argmax never exercised")


def test_daemon_singleton_decode_matches_maverick():
    """singletons=True over the wire: the BUG-FIXED singleton interleave path,
    end-to-end, equals maverick's captured singleton clusters."""
    cases = _require()
    failures, wants = [], []
    saw_singleton_field = False
    with _daemon(os.path.join(FIXTURES, "weights.npz")) as client:
        for npz_path in cases:
            stem = npz_path[:-len(".npz")]
            with open(stem + ".json", encoding="utf-8") as fh:
                if "clusters_token_offsets_singletons" not in json.load(fh):
                    continue
            saw_singleton_field = True
            got, want = _run_case(client, npz_path, singletons=True)
            wants.append(want)
            if got != want:
                failures.append(
                    f"{os.path.basename(npz_path)}: singleton cluster sets differ\n"
                    f"    only over-wire JAX: {sorted(map(sorted, got - want))}\n"
                    f"    only in maverick  : {sorted(map(sorted, want - got))}")
    if not saw_singleton_field:
        import pytest
        pytest.skip("fixtures predate the singleton capture — re-run capture_fixtures.py")
    assert not failures, (
        "over-the-wire singleton divergence:\n" + "\n".join(failures))
    assert any(any(len(c) == 1 for c in want) for want in wants), (
        "VACUOUS: no singleton (size-1 cluster) in any fixture — the singletons=True "
        "branch was not exercised; regenerate over prose with lone-mention entities")


if __name__ == "__main__":
    # Always run the wire-integrity unit (pure numpy).
    test_lhs_wire_roundtrip_is_bit_exact()
    print("PASS test_lhs_wire_roundtrip_is_bit_exact")
    if not _HAVE_DEPS:
        raise SystemExit(f"jax/zmq unavailable: {_IMPORT_ERR}")
    cases = _cases()
    if not cases:
        raise SystemExit("no fixtures — run capture_fixtures.py first")
    ok = True
    with _daemon(os.path.join(FIXTURES, "weights.npz")) as client:
        for sing in (False, True):
            print(f"--- singletons={sing} ---")
            for npz_path in cases:
                stem = npz_path[:-len(".npz")]
                with open(stem + ".json", encoding="utf-8") as fh:
                    has_field = "clusters_token_offsets_singletons" in json.load(fh)
                if sing and not has_field:
                    print("  (fixtures predate singleton capture)")
                    break
                got, want = _run_case(client, npz_path, singletons=sing)
                same = got == want
                ok = ok and same
                print(f"  {'PASS' if same else 'FAIL'} {os.path.basename(npz_path)} "
                      f"(wire={len(got)} clusters, maverick={len(want)} clusters)")
    print("ALL BIT-EXACT" if ok else "DIVERGENCE")
    raise SystemExit(0 if ok else 1)
