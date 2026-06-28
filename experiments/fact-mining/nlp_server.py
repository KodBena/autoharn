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

import os
# The HF Xet backend stalls at 0% behind some networks (observed on this host).
# Force classic HTTPS LFS for every download this daemon triggers (maverick's
# encoder, nltk data, etc.). Must be set before any huggingface_hub import.
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

import argparse
import json
import time
import traceback

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
        self._coref = None       # maverick-coref, loaded lazily on first coref request

    def get(self, name: str | None):
        name = name or self.default_model
        if name not in self.models:
            self.models[name] = spacy.load(name)
        return self.models[name]

    def coref(self):
        """Lazily load maverick-coref (host-only dependency, GPU if available)."""
        if self._coref is None:
            import torch
            from maverick import Maverick  # host-only; imported on demand

            # maverick's official checkpoint is a PyTorch-Lightning/OmegaConf file
            # whose pickle contains omegaconf.DictConfig globals. PyTorch >=2.6
            # defaults torch.load(weights_only=True) and refuses those. The file is
            # the trusted sapienzanlp release, so force full unpickling — but ONLY
            # for the duration of model construction, then restore the default.
            _orig_load = torch.load

            def _trusting_load(*a, **k):
                k["weights_only"] = False
                return _orig_load(*a, **k)

            torch.load = _trusting_load
            try:
                self._coref = Maverick(device="cuda" if self.gpu else "cpu")
            finally:
                torch.load = _orig_load

            # In this process (alongside spaCy-trf on the GPU) maverick's deberta
            # encoder comes back fp16 while its classifier heads are fp32 -> the
            # "mat1 and mat2 must have the same dtype, Half and Float" matmul error.
            # Force the whole model to a consistent fp32. Log the observed dtype so
            # the fix is verified, not assumed.
            m = self._coref.model
            try:
                before = next(m.encoder.parameters()).dtype
                m.float()
                after = next(m.encoder.parameters()).dtype
                print(f"[coref] encoder dtype {before} -> {after} (forced fp32)", flush=True)
            except Exception as e:
                print(f"[coref] fp32 cast skipped: {e!r}", flush=True)

            # maverick reloads spaCy (spacy.load 'en_core_web_sm') on EVERY
            # predict() via download_load_spacy() — ~one CPU model-load per
            # paragraph, which is what makes it glacial with the GPU idle. Cache it
            # so spaCy loads once and is reused across all predicts.
            import functools
            import maverick.models.maverick_model as mmm
            mmm.download_load_spacy = functools.lru_cache(maxsize=1)(mmm.download_load_spacy)
            print("[coref] cached download_load_spacy (spaCy loads once, not per call)", flush=True)
        return self._coref

    def coref_clusters(self, text: str):
        """Return char-offset clusters [[[start,end],...],...] for one text."""
        pred = self.coref().predict(text)
        # maverick returns char offsets under this key; keep as plain lists (JSON)
        return pred.get("clusters_char_offsets", [])

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
        t0 = time.perf_counter()
        docs = list(nlp.pipe(texts, disable=disable))
        t1 = time.perf_counter()

        # optional coreference: per-text char-offset clusters, aligned to `docs`.
        coref = [self.coref_clusters(t) for t in texts] if req.get("coref") else None
        if req.get("coref"):
            print(f"[timing] {len(texts)} texts: parse {t1 - t0:.1f}s, "
                  f"coref {time.perf_counter() - t1:.1f}s", flush=True)

        if req.get("format") == "json":
            out = {"ok": True, "docs": [doc_to_json(d) for d in docs]}
            if coref is not None:
                out["coref"] = coref
            return [json.dumps(out).encode()]

        db = DocBin(store_user_data=True)
        for d in docs:
            db.add(d)
        meta = {
            "ok": True, "format": "docbin", "n": len(docs),
            "model": nlp.meta["name"], "lang": nlp.meta["lang"],
        }
        if coref is not None:
            meta["coref"] = coref  # list aligned with docs; clusters of [start,end] char spans
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
                traceback.print_exc()  # full traceback to host console for diagnosis
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
