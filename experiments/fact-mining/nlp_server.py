#!/usr/bin/env python
"""GPU spaCy daemon — a ZMQ REP server. Runs on the VM *host* (the GPU side).

It is a thin, general-purpose interface to a spaCy pipeline: send text, get back
parsed annotations. The model is loaded once (the expensive step) and reused for
every request, on the GPU.

SAFETY — no code on the wire. The protocol carries DATA only:
  * requests are JSON;
  * parsed results come back as a spaCy DocBin (msgpack-based serialization).
We never use ZMQ's send_pyobj/recv_pyobj (those pickle, i.e. execute arbitrary
code on deserialization). A malicious/garbled message can at worst cause a
parse error, never code execution.

Protocol
--------
Request: one JSON frame.
  {"op": "parse", "texts": [str, ...], "model": "en_core_web_trf",
   "format": "docbin" | "json", "disable": ["lemmatizer", ...]}
  {"op": "info"}                      -> loaded models, gpu status
  {"op": "ping"}                      -> liveness

Reply: ZMQ multipart frames.
  parse + format=docbin -> [ <json meta>, <docbin bytes> ]
  parse + format=json   -> [ <json {ok, docs:[...]}> ]
  info / ping / error   -> [ <json> ]

Run (on the host):
  python nlp_server.py --addr tcp://0.0.0.0:5599 --model en_core_web_trf --gpu
"""

from __future__ import annotations

import argparse
import json

import spacy
import zmq
from spacy.tokens import DocBin


def doc_to_json(doc):
    return {
        "text": doc.text,
        "tokens": [
            {
                "i": t.i, "text": t.text, "lemma": t.lemma_, "pos": t.pos_,
                "tag": t.tag_, "dep": t.dep_, "head": t.head.i,
                "is_stop": t.is_stop, "ent_type": t.ent_type_,
            }
            for t in doc
        ],
        "ents": [
            {"text": e.text, "label": e.label_, "start": e.start, "end": e.end}
            for e in doc.ents
        ],
        "sents": [{"start": s.start, "end": s.end} for s in doc.sents],
    }


class Server:
    def __init__(self, default_model: str, gpu: bool):
        self.gpu = gpu
        if gpu:
            # routes thinc ops to cupy and (for trf) torch to CUDA
            spacy.require_gpu()
        self.default_model = default_model
        self.models: dict[str, "spacy.Language"] = {}
        self.get(default_model)  # preload — the slow part, done once

    def get(self, name: str | None):
        name = name or self.default_model
        if name not in self.models:
            self.models[name] = spacy.load(name)
        return self.models[name]

    def handle(self, raw: bytes) -> list[bytes]:
        """Map one request frame to the reply frames. Pure data in/out."""
        req = json.loads(raw)
        op = req.get("op", "parse")

        if op == "ping":
            return [json.dumps({"ok": True, "pong": True}).encode()]
        if op == "info":
            return [json.dumps({
                "ok": True, "gpu": self.gpu,
                "loaded": list(self.models),
                "default": self.default_model,
            }).encode()]
        if op != "parse":
            return [json.dumps({"ok": False, "error": f"unknown op {op!r}"}).encode()]

        texts = req.get("texts") or []
        nlp = self.get(req.get("model"))
        disable = [p for p in (req.get("disable") or []) if p in nlp.pipe_names]
        docs = list(nlp.pipe(texts, disable=disable))

        if req.get("format") == "json":
            return [json.dumps({"ok": True, "docs": [doc_to_json(d) for d in docs]}).encode()]

        db = DocBin(store_user_data=True)
        for d in docs:
            db.add(d)
        meta = {
            "ok": True, "format": "docbin", "n": len(docs),
            "model": nlp.meta["name"], "lang": nlp.meta["lang"],
        }
        return [json.dumps(meta).encode(), db.to_bytes()]

    def serve(self, addr: str):
        sock = zmq.Context.instance().socket(zmq.REP)
        sock.bind(addr)
        print(f"spaCy daemon listening on {addr} | default={self.default_model} "
              f"| gpu={self.gpu} | pipes={self.get(None).pipe_names}", flush=True)
        while True:
            raw = sock.recv()  # exactly one frame per request (REP state machine)
            try:
                frames = self.handle(raw)
            except Exception as e:  # never crash the daemon on a bad request
                frames = [json.dumps({"ok": False, "error": repr(e)}).encode()]
            sock.send_multipart(frames)  # exactly one reply per request


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--addr", default="tcp://0.0.0.0:5599",
                    help="ZMQ bind address (default %(default)s)")
    ap.add_argument("--model", default="en_core_web_trf",
                    help="default pipeline to preload (default %(default)s)")
    ap.add_argument("--gpu", action="store_true", help="use the GPU (require_gpu)")
    args = ap.parse_args()
    Server(args.model, args.gpu).serve(args.addr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
