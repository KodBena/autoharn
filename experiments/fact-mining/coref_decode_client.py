#!/usr/bin/env python
"""Client for the JAX coref decode daemon (coref_decode_server.py).

`RemoteDecode.decode(...)` ships ONE document's decode-tail intermediates — the
encoder `last_hidden_state` plus the structural maps — and returns the cluster
token-offset tuples the daemon's pure-JAX tail produced.

Wire safety (mirrors nlp_client.py): the request is a JSON metadata frame + a RAW
float32 bytes frame for `last_hidden_state`; the reply is a single JSON frame. No
pickle, no send_pyobj, no code on the wire.

HOST-ONLY POLICY: this client imports numpy (to pack the float32 lhs into raw,
C-contiguous, little-endian bytes) and NO device framework — it is host-side. It
never touches jax/torch; the device lift happens on the daemon.

WHY RAW BYTES FOR lhs. JSON-decimal floats route every value through a float64
decimal round-trip and can flip the last mantissa bit; that perturbation can flip
a `sigmoid>0.5`/argmax decision near a boundary. Raw IEEE-754 little-endian bytes
('<f4') are bit-identical end to end, so the daemon decodes from the EXACT array
the encoder produced. Structural inputs (eos_mask/tokens/subtoken_map/
new_token_map/attention_mask/singletons) are integers/strings -> JSON is exact.
"""

from __future__ import annotations

import json

import numpy as np
import zmq

from spans import get_tracer  # SSOT tracer; host-only (no device import), no-op when off

WIRE_DTYPE = np.dtype("<f4")  # pinned little-endian float32; must match the server


class RemoteError(RuntimeError):
    pass


def pack_lhs(lhs) -> tuple[list[int], bytes]:
    """float32 [S, TH] array -> (shape, raw little-endian C-contiguous bytes).

    Forces dtype to '<f4' and C-contiguity so `.tobytes()` is row-major and
    endian-pinned — the two things that, if wrong, would scramble the wire bytes.
    Asserts 2-D so a stray batch axis fails LOUD at the boundary, not as a silent
    reshape on the far side.
    """
    arr = np.ascontiguousarray(lhs, dtype=WIRE_DTYPE)
    if arr.ndim != 2:
        raise ValueError(f"lhs must be [S, TH], got shape {arr.shape}")
    return [int(d) for d in arr.shape], arr.tobytes()


def _ints(seq) -> list[int]:
    """Coerce an integer map to NATIVE python ints. A real encoder tokenizer hands
    these as numpy/torch arrays whose elements are numpy.int64 — and json.dumps
    raises `TypeError: Object of type int64 is not JSON serializable` on those. The
    server already int()-coerces its RESULT offsets; this is the symmetric coercion
    on the REQUEST side so the wire stays value-exact for native AND array producers.
    int() is value-exact for any integer type, so this never perturbs a discrete map."""
    return [int(x) for x in seq]


def _opt_ints(seq) -> list[int | None]:
    """Like _ints but the map legitimately carries None (subtoken/new_token maps:
    [int|null,...]). None passes through as JSON null; integers coerce to native int."""
    return [None if x is None else int(x) for x in seq]


class RemoteDecode:
    def __init__(self, addr: str = "tcp://192.168.122.1:5600",
                 timeout_ms: int = 600_000):
        self.addr = addr
        self.timeout_ms = timeout_ms
        self._ctx = zmq.Context.instance()
        self._connect()

    def _connect(self):
        self._sock = self._ctx.socket(zmq.REQ)
        self._sock.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.connect(self.addr)

    def _roundtrip(self, frames: list[bytes], timeout_ms: int | None = None) -> list[bytes]:
        to = self.timeout_ms if timeout_ms is None else timeout_ms
        self._sock.send_multipart(frames)
        if self._sock.poll(to, zmq.POLLIN) == 0:
            # a REQ socket with an outstanding reply is wedged; reset before raising
            self._sock.close(0)
            self._connect()
            raise RemoteError(f"no reply within {to} ms")
        return self._sock.recv_multipart()

    # --- control ops (fail fast: a down daemon shouldn't block for minutes) ---
    def ping(self, timeout_ms: int = 5_000) -> dict:
        return json.loads(self._roundtrip(
            [json.dumps({"op": "ping"}).encode()], timeout_ms)[0])

    def info(self, timeout_ms: int = 5_000) -> dict:
        return json.loads(self._roundtrip(
            [json.dumps({"op": "info"}).encode()], timeout_ms)[0])

    # --- decode --------------------------------------------------------------
    def decode(self, lhs, attention_mask, eos_mask, tokens,
               subtoken_map, new_token_map, singletons: bool = False):
        """Ship one document's intermediates; return clusters as a list of clusters,
        each a list of (start_token, end_token) tuples (maverick
        `clusters_token_offsets` shape)."""
        shape, blob = pack_lhs(lhs)
        meta = {
            "op": "decode",
            "shape": shape,
            "dtype": "float32",
            # Coerce every structural map to JSON-native types so a numpy/torch
            # producer (numpy.int64 elements) cannot make json.dumps raise. These
            # are integers/strings only — never decimals — so the round-trip is
            # value-exact and cannot perturb a discrete cluster decision.
            "attention_mask": _ints(attention_mask),
            "eos_mask": [_ints(row) for row in eos_mask],
            "tokens": [str(t) for t in tokens],
            "subtoken_map": _opt_ints(subtoken_map),
            "new_token_map": _opt_ints(new_token_map),
            "singletons": bool(singletons),
        }
        # WIRE 2: stamp the trace context into the decode meta. The current span is the
        # nlp_server "zmq_wait.decode" wait, so the decode daemon parents under it.
        get_tracer().inject(meta)
        frames = self._roundtrip([json.dumps(meta).encode(), blob])
        reply = json.loads(frames[0])
        if not reply.get("ok"):
            raise RemoteError(reply.get("error", "server error"))
        return [[tuple(span) for span in cluster] for cluster in reply["clusters"]]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="smoke-test the jax decode daemon")
    ap.add_argument("--addr", default="tcp://192.168.122.1:5600")
    args = ap.parse_args()

    rd = RemoteDecode(args.addr, timeout_ms=60_000)
    print("ping:", rd.ping())
    print("info:", rd.info())
