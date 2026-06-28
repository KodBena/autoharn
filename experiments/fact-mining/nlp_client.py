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
from spacy.tokens import Doc, DocBin

# Same attribute fastcoref used, so resolve.py consumes daemon coref unchanged.
# Value: list of clusters, each a list of (start_char, end_char) spans.
if not Doc.has_extension("coref_clusters"):
    Doc.set_extension("coref_clusters", default=None)


class RemoteError(RuntimeError):
    pass


class RemoteNLP:
    def __init__(self, addr: str = "tcp://192.168.122.1:5599",
                 model: str | None = None, timeout_ms: int = 600_000,
                 coref: bool = False):
        self.addr = addr
        self.model = model
        self.timeout_ms = timeout_ms
        self.coref = coref  # ask the daemon to run maverick-coref and return clusters
        # a blank vocab is enough to rehydrate a DocBin: all strings travel in it
        self._vocab = spacy.blank("en").vocab
        self._ctx = zmq.Context.instance()
        self._connect()

    def _connect(self):
        self._sock = self._ctx.socket(zmq.REQ)
        self._sock.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
        self._sock.setsockopt(zmq.LINGER, 0)
        self._sock.connect(self.addr)

    def _roundtrip(self, req: dict, timeout_ms: int | None = None) -> list[bytes]:
        to = self.timeout_ms if timeout_ms is None else timeout_ms
        self._sock.send_json(req)
        if self._sock.poll(to, zmq.POLLIN) == 0:
            # a REQ socket with an outstanding reply is wedged; reset before raising
            self._sock.close(0)
            self._connect()
            raise RemoteError(f"no reply within {to} ms")
        return self._sock.recv_multipart()

    # --- control ops (fail fast: a down daemon shouldn't block for minutes) ---
    def ping(self, timeout_ms: int = 5_000) -> dict:
        return json.loads(self._roundtrip({"op": "ping"}, timeout_ms)[0])

    def info(self, timeout_ms: int = 5_000) -> dict:
        return json.loads(self._roundtrip({"op": "info"}, timeout_ms)[0])

    # --- parsing -------------------------------------------------------------
    def pipe(self, texts, disable=()):
        frames = self._roundtrip({
            "op": "parse", "texts": list(texts), "model": self.model,
            "format": "docbin", "disable": list(disable), "coref": self.coref,
        })
        meta = json.loads(frames[0])
        if not meta.get("ok"):
            raise RemoteError(meta.get("error", "server error"))
        docs = list(DocBin().from_bytes(frames[1]).get_docs(self._vocab))
        # attach coref clusters (if any) under the fastcoref-compatible attribute
        clusters = meta.get("coref")
        if clusters is not None:
            for doc, cl in zip(docs, clusters):
                doc._.coref_clusters = [[tuple(span) for span in cluster] for cluster in cl]
        return docs

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
