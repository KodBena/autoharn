#!/usr/bin/env python
"""Client for the JAX coref decode daemon (coref_decode_server.py).

`RemoteDecode.decode_batch(...)` ships MANY documents' decode-tail intermediates —
each document's encoder `last_hidden_state` plus its structural maps — in ONE request
and returns the per-document cluster token-offset tuples the daemon's pure-JAX tail
produced. `RemoteDecode.decode(...)` is the single-document convenience: the batch-of-1
case of `decode_batch`, so there is exactly ONE multi-doc wire codec (ADR-0012 P7),
never a second hand-written single-doc one beside it.

Wire safety (mirrors nlp_client.py): the request is a JSON metadata frame (describing
every doc) + ONE RAW float32 bytes frame per document's `last_hidden_state`; the reply
is a single JSON frame. No pickle, no send_pyobj, no code on the wire.

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
    @staticmethod
    def _doc_meta(doc) -> tuple[dict, bytes]:
        """One document's (json meta, raw lhs blob). The PER-DOC half of the wire
        codec, composed N times by `decode_batch`. `pack_lhs` pins the lhs to raw
        '<f4' bytes (bit-exact); the structural maps are coerced to JSON-native
        ints/strings (never decimals) so the round-trip cannot perturb a discrete
        cluster decision."""
        shape, blob = pack_lhs(doc["lhs"])
        meta = {
            "shape": shape,
            "dtype": "float32",
            "attention_mask": _ints(doc["attention_mask"]),
            "eos_mask": [_ints(row) for row in doc["eos_mask"]],
            "tokens": [str(t) for t in doc["tokens"]],
            "subtoken_map": _opt_ints(doc["subtoken_map"]),
            "new_token_map": _opt_ints(doc["new_token_map"]),
        }
        return meta, blob

    def decode_batch(self, docs, singletons: bool = False):
        """Ship MANY documents' intermediates in ONE request; return a list aligned to
        `docs`, each entry that doc's clusters (a list of clusters, each a list of
        (start_token, end_token) tuples — maverick `clusters_token_offsets` shape).

        `docs` is a list of dicts: {lhs, attention_mask, eos_mask, tokens,
        subtoken_map, new_token_map}. The wire is ONE JSON meta frame with a `docs`
        list + ONE raw-float32 lhs frame per doc, in order. This is the ONE
        authoritative multi-doc codec (ADR-0012 P7). n==1 is just the batch-of-1 case.
        """
        _T = get_tracer()
        # Split the round-trip into serialize / wire+decode / parse so the trace can say
        # whether the wire cost is the dense eos_mask [S,S] JSON (serialize here +
        # parse_request on the server) or the lhs byte transfer. These spans cost a little
        # now; the breakdown they yield is what tells us which lever to pull.
        with _T.span("decode_client.serialize_request", n_docs=len(docs)):
            per_doc = [self._doc_meta(d) for d in docs]
            meta = {
                "op": "decode",
                "singletons": bool(singletons),
                "docs": [m for (m, _b) in per_doc],
            }
            # WIRE 2: stamp the trace context into the decode meta. The decode daemon
            # parents under this request's spans.
            get_tracer().inject(meta)
            out_frames = [json.dumps(meta).encode(), *[b for (_m, b) in per_doc]]
        with _T.span("decode_client.roundtrip", n_docs=len(docs)):
            frames = self._roundtrip(out_frames)
        with _T.span("decode_client.parse_reply"):
            reply = json.loads(frames[0])
            if not reply.get("ok"):
                raise RemoteError(reply.get("error", "server error"))
            # FAIL LOUD on a reply that is not one-cluster-list-per-doc (ADR-0002/P5).
            # The server guarantees this by construction (one append per doc), but the
            # caller (`coref_clusters_jax_daemon`) consumes the result with
            # `zip(docs, ...)`, which would SILENTLY TRUNCATE if the daemon ever returned
            # fewer doc-cluster lists than docs sent. Check the reply direction too.
            clusters = reply["clusters"]
            if len(clusters) != len(docs):
                raise RemoteError(
                    f"decode reply has {len(clusters)} doc-cluster list(s) for "
                    f"{len(docs)} doc(s) sent")
            return [[[tuple(span) for span in cluster] for cluster in doc_clusters]
                    for doc_clusters in clusters]

    def decode(self, lhs, attention_mask, eos_mask, tokens,
               subtoken_map, new_token_map, singletons: bool = False):
        """Single-document decode = the batch-of-1 case of `decode_batch` (ONE wire
        codec; no second hand-written single-doc codec). Returns the one document's
        clusters as a list of clusters, each a list of (start_token, end_token) tuples."""
        doc = {"lhs": lhs, "attention_mask": attention_mask, "eos_mask": eos_mask,
               "tokens": tokens, "subtoken_map": subtoken_map, "new_token_map": new_token_map}
        return self.decode_batch([doc], singletons=singletons)[0]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="smoke-test the jax decode daemon")
    ap.add_argument("--addr", default="tcp://192.168.122.1:5600")
    args = ap.parse_args()

    rd = RemoteDecode(args.addr, timeout_ms=60_000)
    print("ping:", rd.ping())
    print("info:", rd.info())
