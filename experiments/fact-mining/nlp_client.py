#!/usr/bin/env python
"""Client for the GPU spaCy daemon (nlp_server.py).

RemoteNLP has TWO surfaces:
  * `.pipe_facts(texts)` -> list of JSON fact dicts (the LEAN, default --remote
    path). The daemon runs the SSOT extractor (extract.doc_to_facts) host-side and
    sends finished facts, so this client imports only json + zmq + psycopg — NEVER
    spaCy/torch/transformers. This is the whole point of the cut.
  * `.pipe(texts)` / `nlp(text)` -> real `Doc` objects, rehydrated from a DocBin
    (the demonstration path used by extract.py). spaCy is imported LAZILY inside
    .pipe(), so merely constructing a RemoteNLP and using the facts wire stays
    import-light. Only a caller that actually wants Docs pays for spaCy.

IMPORT DISCIPLINE (foreclosed by test_lean_remote_client.py): spaCy is NOT imported
at module scope. `import spacy` drags thinc->torch (~1.06s) + transformers; the lean
client must never pay that just to talk to the daemon. The DocBin rehydration in
.pipe() lazy-imports it; the facts wire does not touch it.

Wire safety: requests are JSON, replies are JSON (facts path) or DocBin bytes
(msgpack, Docs path). No pickle, no code execution on either side.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import zmq

from spans import get_tracer  # SSOT tracer; no-op unless the run enabled it

if TYPE_CHECKING:
    # type-only: the facts wire shape lives in extract.FactBundle (ADR-0012 P7/P8). This
    # import is NEVER executed at runtime (TYPE_CHECKING is False), so the lean client
    # stays spaCy-free — the gate (test_lean_remote_client.py) still sees no ML stack.
    from extract import FactBundle


class RemoteError(RuntimeError):
    pass


class RemoteNLP:
    def __init__(self, addr: str = "tcp://192.168.122.1:5599",
                 model: str | None = None, timeout_ms: int = 600_000,
                 coref: bool = False, coref_mode: str = "batched",
                 coref_backend: str = "maverick", decode_addr: str | None = None):
        self.addr = addr
        self.model = model
        self.timeout_ms = timeout_ms
        self.coref = coref  # ask the daemon to run maverick-coref and return clusters
        # how the daemon runs coref: "batched" (fast, default) | "serial"
        # (reference) | "verify" (run both, report fidelity). See nlp_server.py.
        self.coref_mode = coref_mode
        # which decode backend the daemon uses: "maverick" (reference, its own decode
        # tail) | "jax-daemon" (torch encodes on the daemon, the JAX decode daemon
        # decodes). decode_addr, when set, tells the daemon where that JAX daemon is.
        self.coref_backend = coref_backend
        self.decode_addr = decode_addr
        # filled from the daemon reply when coref_mode == "verify"; else None
        self.last_coref_verify: dict | None = None
        # the DocBin-rehydration vocab is built lazily on first .pipe() call (it needs
        # spaCy); the lean .pipe_facts() path never touches it, so constructing a
        # RemoteNLP imports no spaCy.
        self._vocab = None
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

    def _req(self, texts, fmt: str, disable=()) -> dict:
        """Build the parse request shared by both wire formats (ONE home, ADR-0012
        P1): only the `format` field differs between the facts and DocBin paths."""
        req = {
            "op": "parse", "texts": list(texts), "model": self.model,
            "format": fmt, "disable": list(disable), "coref": self.coref,
            "coref_mode": self.coref_mode, "coref_backend": self.coref_backend,
        }
        if self.decode_addr is not None:
            req["decode_addr"] = self.decode_addr
        return req

    # --- the LEAN facts wire (default --remote path) -------------------------
    def pipe_facts(self, texts, disable=()) -> list[FactBundle]:
        """Return the daemon's JSON facts: a list of extract.doc_to_facts dicts, one
        per input text. The daemon ran the SSOT extractor host-side, so this client
        deserializes JSON only — no spaCy, no Doc rehydration. The data-only,
        no-code-on-the-wire rule holds: JSON meta + JSON facts, never pickle."""
        req = self._req(texts, "facts", disable)
        # WIRE 1 (client<->nlp_server): the zmq_wait span IS the client's blocked time
        # on the daemon; inject the trace context into the JSON meta inside it so the
        # daemon's spans parent under this wait (ADR-0012 P2).
        with get_tracer().span("client.zmq_wait.nlp_server", n_texts=len(req["texts"])):
            get_tracer().inject(req)
            frames = self._roundtrip(req)
        meta = json.loads(frames[0])
        if not meta.get("ok"):
            raise RemoteError(meta.get("error", "server error"))
        self.last_coref_verify = meta.get("coref_verify")  # set only in verify mode
        return meta["facts"]

    # --- the DocBin wire (Docs path, used by extract.py's demo) --------------
    def pipe(self, texts, disable=()):
        # LAZY spaCy: only the DocBin-rehydration path needs it. Keeping it here (not at
        # module scope) is what makes `import nlp_client` + the facts wire import-light.
        import spacy
        from spacy.tokens import DocBin

        import resolve
        if self._vocab is None:
            # a blank vocab is enough to rehydrate a DocBin: all strings travel in it
            self._vocab = spacy.blank("en").vocab

        req = self._req(texts, "docbin", disable)
        with get_tracer().span("client.zmq_wait.nlp_server", n_texts=len(req["texts"])):
            get_tracer().inject(req)
            frames = self._roundtrip(req)
        meta = json.loads(frames[0])
        if not meta.get("ok"):
            raise RemoteError(meta.get("error", "server error"))
        self.last_coref_verify = meta.get("coref_verify")  # set only in verify mode
        docs = list(DocBin().from_bytes(frames[1]).get_docs(self._vocab))
        # attach coref clusters (if any) via the ONE wire decoder (ADR-0012 P1/P7):
        # resolve.attach_coref_clusters — the SAME decoder extract.doc_to_facts uses, so
        # the DocBin path and the facts path cannot drift on the cluster encoding. It
        # also registers the extension (folds in ensure_coref_extension).
        clusters = meta.get("coref")
        if clusters is not None:
            for doc, cl in zip(docs, clusters):
                resolve.attach_coref_clusters(doc, cl)
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
