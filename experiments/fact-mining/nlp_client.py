#!/usr/bin/env python
"""Client for the GPU spaCy daemon (nlp_server.py).

RemoteNLP is a near-drop-in for a loaded spaCy `nlp`: `.pipe(texts)` and
`nlp(text)` return real `Doc` objects, rehydrated from the DocBin the server
sends. Guest-side code (e.g. extract.py) then works on Docs exactly as if the
model were local — only the heavy GPU inference happens on the host.

Wire safety: requests are JSON, replies are DocBin bytes (msgpack). No pickle,
no code execution on either side.
"""

from __future__ import annotations

import json

import spacy
import zmq
from spacy.tokens import DocBin


class RemoteError(RuntimeError):
    pass


class RemoteNLP:
    def __init__(self, addr: str = "tcp://192.168.122.1:5599",
                 model: str | None = None, timeout_ms: int = 600_000):
        self.addr = addr
        self.model = model
        self.timeout_ms = timeout_ms
        # a blank vocab is enough to rehydrate a DocBin: all strings travel in it
        self._vocab = spacy.blank("en").vocab
        self._ctx = zmq.Context.instance()
        self._connect()

    def _connect(self):
        self._sock = self._ctx.socket(zmq.REQ)
        self._sock.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.connect(self.addr)

    def _roundtrip(self, req: dict) -> list[bytes]:
        self._sock.send_json(req)
        try:
            return self._sock.recv_multipart()
        except zmq.Again:
            # a REQ socket that timed out is wedged; reset it before raising
            self._sock.close(0)
            self._connect()
            raise RemoteError(f"no reply within {self.timeout_ms} ms")

    # --- control ops ---------------------------------------------------------
    def ping(self) -> dict:
        return json.loads(self._roundtrip({"op": "ping"})[0])

    def info(self) -> dict:
        return json.loads(self._roundtrip({"op": "info"})[0])

    # --- parsing -------------------------------------------------------------
    def pipe(self, texts, disable=()):
        frames = self._roundtrip({
            "op": "parse", "texts": list(texts), "model": self.model,
            "format": "docbin", "disable": list(disable),
        })
        meta = json.loads(frames[0])
        if not meta.get("ok"):
            raise RemoteError(meta.get("error", "server error"))
        db = DocBin().from_bytes(frames[1])
        return list(db.get_docs(self._vocab))

    def __call__(self, text: str, **kw):
        return self.pipe([text], **kw)[0]


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="smoke-test the spaCy daemon")
    ap.add_argument("--addr", default="tcp://192.168.122.1:5599")
    ap.add_argument("--text", default="Galen studied medicine in Pergamon and Rome.")
    args = ap.parse_args()

    nlp = RemoteNLP(args.addr, timeout_ms=60_000)
    print("ping:", nlp.ping())
    print("info:", nlp.info())
    doc = nlp(args.text)
    print("tokens:", [(t.text, t.pos_, t.dep_, t.head.text) for t in doc])
    print("ents:  ", [(e.text, e.label_) for e in doc.ents])
