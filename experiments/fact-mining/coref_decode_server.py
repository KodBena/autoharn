#!/usr/bin/env python
"""JAX coref DECODE daemon — a ZMQ REP server (Stage 1b-i of the JAX migration).

This is the WIRE<->DEVICE BOUNDARY for the already-proven pure-JAX decode tail.
It is NOT a pure `jax_*` core file: it is the honestly-named imperative seam that

  1. loads the decode-tail weights ONCE into jax arrays (`--weights`), and
  2. per request, lifts the encoder `last_hidden_state` off the wire onto the
     device, runs `coref_host_shell.decode_document` (the single proven jax
     host<->device home for the decode PIPELINE), and returns the cluster
     token-offset tuples.

Relationship to the proven core (DO NOT modify those):
  * jax_decode.py          — pure jax device core (3 jit stages).  bit-exact.
  * coref_host_shell.py    — decode_document orchestrator; the pipeline's jax home.
This file is a SECOND, distinct jax host<->device edge — the WIRE seam — declared
as such in BOTH guard gates (test_import_xor.BOUNDARY_FILES and
test_device_transfers.HOMES["jax"]). Single-homing is kept intact at per-EDGE
granularity: the pipeline edge lives in coref_host_shell.py; the wire edge lives
here, and nowhere else.

NUMPY POLICY (why this file is a declared host<->device boundary, unlike the
deliberately numpy-free shell): the ONLY honest, bit-exact way to carry a float32
`last_hidden_state` over the wire is as RAW IEEE-754 little-endian bytes — JSON
decimal floats route every value through a float64 decimal round-trip and can flip
the last mantissa bit, which is exactly the kind of perturbation that can flip a
`sigmoid>0.5`/argmax decision near a boundary (ADR-0009's residual risk). Unpacking
those raw bytes back into a typed, shaped, C-contiguous array is `numpy.frombuffer`
— a host-side structural concern. So this file legitimately imports BOTH numpy
(host: wire unpack) and jax (device: the lift onto the accelerator). That mix is
sanctioned by a BOUNDARY_FILES entry, and the file name is NEUTRAL (not jax_*) so
it does not lie about being a device-only core.

SAFETY — no code on the wire (mirrors nlp_server.py). The protocol carries DATA
only: a JSON metadata frame + a RAW float32 bytes frame. We NEVER use
send_pyobj/recv_pyobj (those pickle == arbitrary code execution on deserialize).

MEMORY (GPU co-residency). One document per request — the jax stages recompile per
document shape, never an unbounded B*S batch (see jax_decode.py's "per-document
MEMORY BUDGET"). When this daemon shares a GPU with the torch encoder, cap XLA's
arena so it does not pre-grab the whole card: export
`XLA_PYTHON_CLIENT_MEM_FRACTION=0.3` (or `XLA_PYTHON_CLIENT_PREALLOCATE=false`)
BEFORE launching. We set a conservative default below if neither is set, so a
naive launch alongside torch does not OOM the encoder.

Protocol
--------
Request: ZMQ multipart.
  decode -> [ <json meta>, <raw float32 lhs bytes> ]
      meta = {"op": "decode", "shape": [S, TH], "dtype": "float32",
              "attention_mask": [int,...], "eos_mask": [[int,...],...],
              "tokens": [str,...], "subtoken_map": [int|null,...],
              "new_token_map": [int|null,...], "singletons": bool}
      frame 1 = lhs as C-contiguous little-endian float32, len == S*TH*4 bytes.
  info / ping -> [ <json meta> ]   (single frame, no binary frame)

Reply: ZMQ multipart (always a single JSON frame for this daemon).
  decode ok  -> [ {"ok": true, "clusters": [[[s,e],...],...], "singletons": bool} ]
  info/ping  -> [ {"ok": true, ...} ]
  error      -> [ {"ok": false, "error": "..."} ]

Run (on the host, in the jax env):
  XLA_PYTHON_CLIENT_MEM_FRACTION=0.3 \
    python coref_decode_server.py --addr tcp://0.0.0.0:5600 --weights ./fixtures/weights.npz
"""

from __future__ import annotations

import os

# GPU co-residency guard: if the operator has not chosen an XLA memory policy,
# default to a fraction so this decode daemon does not pre-allocate the whole card
# out from under a co-resident torch encoder. Must be set before jax initialises.
if ("XLA_PYTHON_CLIENT_MEM_FRACTION" not in os.environ
        and "XLA_PYTHON_CLIENT_PREALLOCATE" not in os.environ):
    os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "0.3"

import argparse
import json
import traceback

import numpy as np
import zmq

import jax
import jax.numpy as jnp

import coref_host_shell

# Match torch float32 exactly — the decode tail is pinned fp32 (jax_decode.py and
# decode_document both assert/contract float32). Never let x64 widen a matmul.
jax.config.update("jax_enable_x64", False)

# The one wire dtype. Pinned little-endian float32: both the client pack and this
# unpack agree on '<f4' so the raw bytes are bit-identical regardless of host
# endianness. JSON-decimal floats are NOT acceptable for lhs (see module docstring).
WIRE_DTYPE = np.dtype("<f4")


def load_params(path: str) -> dict:
    """weights.npz -> dict[str, jax.Array] float32. The single np->jax conversion
    seam for the LEARNED params; done ONCE at startup, not per request."""
    with np.load(path) as z:
        return {k: jnp.asarray(z[k], dtype=jnp.float32)  # host-device-boundary: lift decode-tail weights numpy->jax once at startup
                for k in z.files}


def unpack_lhs(meta: dict, blob: bytes) -> jax.Array:
    """RAW wire bytes -> device float32 [S, TH], BIT-EXACT.

    numpy.frombuffer reinterprets the bytes as little-endian float32 with NO value
    conversion (unlike a JSON decimal parse), reshapes to the declared [S, TH], and
    we lift that onto the device. FAIL LOUD on any wire/shape mismatch — a wrong
    byte length or dtype is a real protocol bug, never silently coerced.
    """
    if meta.get("dtype") != "float32":
        raise ValueError(f"lhs dtype must be 'float32', got {meta.get('dtype')!r}")
    shape = tuple(meta["shape"])
    if len(shape) != 2:
        raise ValueError(f"lhs shape must be [S, TH], got {shape}")
    expected = shape[0] * shape[1] * WIRE_DTYPE.itemsize
    if len(blob) != expected:
        raise ValueError(
            f"lhs byte length {len(blob)} != expected {expected} for shape {shape}")
    host = np.frombuffer(blob, dtype=WIRE_DTYPE).reshape(shape)
    return jnp.asarray(host, dtype=jnp.float32)  # host-device-boundary: lift the wire last_hidden_state numpy->jax (the wire seam)


class DecodeServer:
    def __init__(self, weights_path: str):
        self.weights_path = weights_path
        self.params = load_params(weights_path)
        # how many distinct weight tensors we loaded (info/diagnostics)
        self.n_params = len(self.params)

    # ----------------------------------------------------------- request handler
    def handle(self, frames: list[bytes]) -> list[bytes]:
        """Map request frames -> reply frames. Pure data in/out, one doc/request."""
        meta = json.loads(frames[0])
        op = meta.get("op", "decode")

        if op == "ping":
            return [json.dumps({"ok": True, "pong": True}).encode()]
        if op == "info":
            return [json.dumps({
                "ok": True, "weights": os.path.basename(self.weights_path),
                "n_params": self.n_params, "wire_dtype": "float32",
                "x64": bool(jax.config.read("jax_enable_x64")),
            }).encode()]
        if op != "decode":
            return [json.dumps({"ok": False, "error": f"unknown op {op!r}"}).encode()]

        if len(frames) < 2:
            raise ValueError("decode request needs a second frame: raw float32 lhs bytes")

        lhs = unpack_lhs(meta, frames[1])
        singletons = bool(meta.get("singletons", False))

        clusters = coref_host_shell.decode_document(
            params=self.params,
            lhs=lhs,
            attention_mask=meta["attention_mask"],
            eos_mask=meta["eos_mask"],
            tokens=meta["tokens"],
            subtoken_map=meta["subtoken_map"],
            new_token_map=meta["new_token_map"],
            singletons=singletons,
        )
        # token-offset tuples -> plain [[ [s,e], ... ], ...] for JSON. Offsets are
        # INTEGERS (no float slack), so JSON is bit-exact for the RESULT.
        out = [[[int(s), int(e)] for (s, e) in cluster] for cluster in clusters]
        return [json.dumps({"ok": True, "clusters": out,
                            "singletons": singletons}).encode()]

    def serve(self, addr: str):
        sock = zmq.Context.instance().socket(zmq.REP)
        sock.bind(addr)
        print(f"jax decode daemon listening on {addr} | weights="
              f"{os.path.basename(self.weights_path)} ({self.n_params} tensors) | "
              f"mem_fraction={os.environ.get('XLA_PYTHON_CLIENT_MEM_FRACTION')}",
              flush=True)
        while True:
            frames = sock.recv_multipart()  # one request (>=1 frame) per REP turn
            try:
                reply = self.handle(frames)
            except Exception as e:  # never crash the daemon on a bad request
                traceback.print_exc()  # full traceback to host console for diagnosis
                reply = [json.dumps({"ok": False, "error": repr(e)}).encode()]
            sock.send_multipart(reply)  # exactly one reply per request


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--addr", default="tcp://0.0.0.0:5600",
                    help="ZMQ bind address (default %(default)s)")
    ap.add_argument("--weights", default=os.path.join(here, "fixtures", "weights.npz"),
                    help="decode-tail weights .npz (default %(default)s)")
    args = ap.parse_args()
    DecodeServer(args.weights).serve(args.addr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
