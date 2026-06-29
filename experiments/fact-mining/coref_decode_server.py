#!/usr/bin/env python
"""JAX coref DECODE daemon — a ZMQ REP server (Stage 1b-i of the JAX migration).

The HOST-SIDE wire seam for the already-proven pure-JAX decode tail. It owns the
transport (ZMQ + a raw-float32 wire) and delegates EVERY device op to the single
jax home, `coref_host_shell.py`:

  1. at startup, loads the decode-tail weights as HOST arrays and hands them to
     `coref_host_shell.lift_params` (the device lift lives THERE, not here), and
  2. per request, unpacks the encoder `last_hidden_state` off the wire into a HOST
     numpy array and calls `coref_host_shell.decode_document_host`, which lifts it
     onto the device and runs the decode, returning cluster token-offset tuples.

SINGLE HOME (mandate — two homes is a drift hazard). There is exactly ONE jax
host<->device home: coref_host_shell.py. This file authors NO jax device op; it
imports numpy (wire unpack) + zmq + the shell, and is host-only by the import-XOR
gate (no jax import, no BOUNDARY_FILES entry). The jax runtime still initialises in
THIS process because it imports the shell, so the XLA memory guard below applies.

NUMPY POLICY: the only honest, bit-exact way to carry a float32 last_hidden_state
over the wire is RAW IEEE-754 little-endian bytes — JSON decimal floats route every
value through a float64 decimal round-trip and can flip the last mantissa bit
(ADR-0009's residual risk). Unpacking those bytes into a typed, shaped array is
`numpy.frombuffer` — a host-side structural concern. This file touches numpy only
on the HOST side; it never authors a device lift.

SAFETY — no code on the wire (mirrors nlp_server.py): a JSON metadata frame + a RAW
float32 bytes frame. We NEVER use send_pyobj/recv_pyobj (pickle == arbitrary code
execution on deserialize).

MEMORY (GPU co-residency). The WIRE batches many docs per request, but the decode
COMPUTE stays per-document: this daemon loops `decode_document_host` per doc, and the
jax stages recompile per document SHAPE, never an unbounded B*S padded batch. So the
per-doc memory budget is exactly what it was when the wire carried one doc — collapsing
the round-trips did not enlarge the decode footprint. jax initialises in this process
via the shell import, so cap XLA's arena when sharing a GPU with the torch encoder:
export `XLA_PYTHON_CLIENT_MEM_FRACTION=0.3` (or `XLA_PYTHON_CLIENT_PREALLOCATE=false`)
BEFORE launching; we set a conservative default below if neither is set.

Protocol
--------
Request: ZMQ multipart. ONE meta frame + ONE raw float32 lhs frame PER document.
  decode -> [ <json meta>, <raw f32 lhs doc 0>, <raw f32 lhs doc 1>, ... ]
      meta = {"op": "decode", "singletons": bool,
              "docs": [ {"shape": [S, TH], "dtype": "float32",
                         "attention_mask": [int,...], "eos_mask": [[int,...],...],
                         "tokens": [str,...], "subtoken_map": [int|null,...],
                         "new_token_map": [int|null,...]}, ... ]}
      frame 1+i = doc i's lhs as C-contiguous little-endian float32, len == Sᵢ*TH*4
      bytes; there are exactly len(docs) lhs frames. n==1 is the batch-of-1 case.
  info / ping -> [ <json meta> ]   (single frame, no binary frame)

Reply: ZMQ multipart (always a single JSON frame).
  decode ok  -> [ {"ok": true, "clusters": [[[[s,e],...],...], ...], "singletons": bool} ]
                (clusters[i] is doc i's clusters, aligned to the request's docs)
  info/ping  -> [ {"ok": true, ...} ]
  error      -> [ {"ok": false, "error": "..."} ]

Run (on the host, in the jax env):
  XLA_PYTHON_CLIENT_MEM_FRACTION=0.3 \
    python coref_decode_server.py --addr tcp://0.0.0.0:5600 --weights ./fixtures/weights.npz
"""

from __future__ import annotations

import os

# GPU co-residency guard: jax initialises in THIS process via the coref_host_shell
# import below; if the operator chose no XLA memory policy, default to a fraction so
# this daemon does not pre-grab the whole card from a co-resident torch encoder.
# Must be set before jax initialises (i.e. before importing the shell).
if ("XLA_PYTHON_CLIENT_MEM_FRACTION" not in os.environ
        and "XLA_PYTHON_CLIENT_PREALLOCATE" not in os.environ):
    os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "0.3"

import argparse
import json
import traceback

import numpy as np
import zmq

import coref_host_shell  # the single jax home: it owns the device lifts + the jax config
from spans import get_tracer  # SSOT tracer (host-only; no jax import here)

# The one wire dtype. Pinned little-endian float32: both the client pack and this
# unpack agree on '<f4' so the raw bytes are bit-identical regardless of host
# endianness. JSON-decimal floats are NOT acceptable for lhs (see module docstring).
WIRE_DTYPE = np.dtype("<f4")


def load_params(path: str) -> dict:
    """weights.npz -> dict[str, np.ndarray] float32 (HOST). The device lift is the
    shell's job (coref_host_shell.lift_params — the single jax home), so this wire
    seam stays host-only."""
    # use .astype (not np.asarray): the device gate flags the bare token `.asarray()`
    # by name (can't tell np from jnp), and this file authors NO device op.
    with np.load(path) as z:
        return {k: z[k].astype(np.float32) for k in z.files}


def unpack_lhs(meta: dict, blob: bytes) -> np.ndarray:
    """RAW wire bytes -> HOST float32 [S, TH], BIT-EXACT.

    numpy.frombuffer reinterprets the bytes as little-endian float32 with NO value
    conversion (unlike a JSON decimal parse) and reshapes to the declared [S, TH].
    The device lift is the shell's job. FAIL LOUD on any wire/shape mismatch — a
    wrong byte length or dtype is a real protocol bug, never silently coerced.
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
    return np.frombuffer(blob, dtype=WIRE_DTYPE).reshape(shape)  # HOST array; the shell lifts it


class DecodeServer:
    def __init__(self, weights_path: str):
        self.weights_path = weights_path
        # the device lift happens in the shell (single jax home); we hold the
        # resulting device arrays opaquely and pass them straight back to the shell.
        self.params = coref_host_shell.lift_params(load_params(weights_path))
        self.n_params = len(self.params)
        # cache_hit proxy: the decode jits recompile per lhs shape (variable S). A
        # shape decoded before in this process has WARM compiled graphs; the first is
        # a COLD compile. This per-process set is a documented, honest proxy for that
        # warm/cold distinction — the host run confirms its correlation with dur_ms.
        self._seen_shapes: set[tuple[int, ...]] = set()
        get_tracer().configure(process="decode_server")  # OFF until a request carries a context

    # ----------------------------------------------------------- request handler
    def handle(self, frames: list[bytes]) -> list[bytes]:
        """Map request frames -> reply frames. Pure data in/out, one doc/request."""
        meta = json.loads(frames[0])
        op = meta.get("op", "decode")
        # WIRE 2 receipt: adopt nlp_server's trace context (enables iff sent). The
        # host shell's device/long-op spans then nest under this request's spans.
        _T = get_tracer()
        _T.extract(meta)

        if op == "ping":
            return [json.dumps({"ok": True, "pong": True}).encode()]
        if op == "info":
            return [json.dumps({
                "ok": True, "weights": os.path.basename(self.weights_path),
                "n_params": self.n_params, "wire_dtype": "float32",
            }).encode()]
        if op != "decode":
            return [json.dumps({"ok": False, "error": f"unknown op {op!r}"}).encode()]

        # MULTI-DOC decode: meta["docs"] is a list of per-doc metas; frames[1:] are the
        # per-doc raw-float32 lhs blobs, one per doc, in order. n==1 is the batch-of-1
        # case (the single-doc client `decode` ships exactly one doc here). The decode
        # COMPUTE stays per-doc/ragged (decode_document_host per doc, never a padded
        # B*S batch) — only the WIRE batches, so the per-doc memory budget is unchanged.
        docs_meta = meta.get("docs")
        if docs_meta is None:
            raise ValueError(
                "decode request needs meta['docs']: a list of per-doc metas "
                "(one raw float32 lhs frame follows per doc)")
        if len(frames) != 1 + len(docs_meta):
            raise ValueError(
                f"decode expects {len(docs_meta)} lhs frame(s) after meta, "
                f"got {len(frames) - 1}")
        singletons = bool(meta.get("singletons", False))

        with _T.span("decode_server.handle", op=op, n_docs=len(docs_meta)):
            clusters_per_doc = []
            for i, dm in enumerate(docs_meta):
                lhs_host = unpack_lhs(dm, frames[1 + i])
                shape_key = tuple(dm["shape"])
                # cache_hit/_seen_shapes is TRACING-ONLY state (the warm/cold-compile
                # proxy attr). Keep it off the OFF-by-default path: when tracing is
                # disabled this is a dead attr, so don't even touch the set.
                cache_hit = False
                if _T.enabled:
                    cache_hit = shape_key in self._seen_shapes
                    self._seen_shapes.add(shape_key)
                with _T.span("decode_server.jax_decode", cache_hit=cache_hit,
                             s=shape_key[0], th=shape_key[1]):
                    clusters = coref_host_shell.decode_document_host(
                        params=self.params,
                        lhs_host=lhs_host,
                        attention_mask=dm["attention_mask"],
                        eos_mask=dm["eos_mask"],
                        tokens=dm["tokens"],
                        subtoken_map=dm["subtoken_map"],
                        new_token_map=dm["new_token_map"],
                        singletons=singletons,
                    )
                # token-offset tuples -> plain [[ [s,e], ... ], ...] for JSON. Offsets
                # are INTEGERS (no float slack), so JSON is bit-exact for the RESULT.
                clusters_per_doc.append(
                    [[[int(s), int(e)] for (s, e) in cluster] for cluster in clusters])
        return [json.dumps({"ok": True, "clusters": clusters_per_doc,
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
            get_tracer().flush()  # persist this request's spans (no-op when untraced)


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
