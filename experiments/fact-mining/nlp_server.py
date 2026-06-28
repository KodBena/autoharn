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
   "format": "docbin" | "json", "disable": ["lemmatizer", ...],
   "coref": bool, "coref_mode": "batched" | "serial" | "verify"}
     coref_mode (only when coref=true):
       "batched" (default) — one batched deberta-encoder pass over all texts,
                  then maverick's per-doc clustering tail. Fast.
       "serial"           — the reference path: one maverick predict() per text.
       "verify"           — run BOTH, return the serial clusters AND a
                  "coref_verify" pass/fail diff so fidelity can be audited once.
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


class _PrecomputedEncoder:
    """Temporary stand-in for maverick's deberta encoder during batched coref.

    Installed into `model._modules['encoder']` only for the span of the per-item
    `predict()` calls in `Server.coref_clusters_batched`. Each call returns the
    precomputed batched hidden-state row for the NEXT item (predict() runs items
    in order), sliced to that item's true unpadded length, so maverick's
    forward/clustering tail runs unchanged on a per-document hidden state.

    It is a plain object (not an nn.Module) and is stuck into `_modules`
    deliberately: `self.encoder(...)` then resolves here, and `self.encoder.device`
    is proxied to the real encoder. Nothing in maverick's forward iterates the
    module tree between install and restore, so a non-Module sitting in `_modules`
    is safe for that window.
    """

    def __init__(self, real, hidden, lengths):
        # `real` first so __getattr__ (which proxies to it) never recurses.
        self.real = real
        self.device = real.device  # forward reads self.encoder.device in several spots
        self.hidden = hidden       # B×S×H, fp32, on device
        self.lengths = lengths
        self.i = 0

    def __call__(self, input_ids=None, attention_mask=None, **kw):
        i = self.i
        self.i += 1
        n = self.lengths[i]
        # Robustness: predict() re-tokenises deterministically, so the sequence it
        # asks us to encode must be exactly the one we batched. A length mismatch
        # means the per-item order desynced from the batch — fail loud, never serve
        # the wrong row.
        got = int(input_ids.shape[1])
        if got != n:
            raise RuntimeError(
                f"batched-coref desync: item {i} requested len {got} != precomputed {n}")
        return {"last_hidden_state": self.hidden[i:i + 1, :n, :]}

    def __getattr__(self, name):
        # proxy anything else (e.g. .config) to the wrapped encoder
        return getattr(self.__dict__["real"], name)


class Server:
    def __init__(self, default_model: str, gpu: bool):
        self.gpu = gpu
        if gpu:
            # routes thinc ops to cupy and (for trf) torch to CUDA
            spacy.require_gpu()  # host-device-boundary: enable GPU for spaCy-trf
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
                self._coref = Maverick(device="cuda" if self.gpu else "cpu")  # host-device-boundary: place maverick on GPU
            finally:
                torch.load = _orig_load

            # In this process (alongside spaCy-trf on the GPU) maverick's deberta
            # encoder comes back fp16 while its classifier heads are fp32 -> the
            # "mat1 and mat2 must have the same dtype, Half and Float" matmul error.
            # Force the whole model to a consistent fp32 (kept fp32 deliberately:
            # maverick's mention/antecedent decisions are sigmoid>0.5 / argmax, and
            # fp16 rounding near those thresholds can flip a fact in the base; VRAM
            # is not a constraint here). Log the observed dtype to verify the fix.
            # A failed cast is FATAL on purpose: silently continuing would make every
            # later coref request throw the Half/Float matmul error instead.
            m = self._coref.model
            before = next(m.encoder.parameters()).dtype
            m.float()  # host-device-boundary: cast maverick to fp32 for dtype consistency
            print(f"[coref] encoder dtype {before} -> "
                  f"{next(m.encoder.parameters()).dtype} (forced fp32)", flush=True)

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
        """Return char-offset clusters [[[start,end],...],...] for one text.

        SERIAL REFERENCE PATH — one maverick predict() per text. This is the
        ground truth `coref_clusters_batched` is validated against; keep it
        untouched. Slow precisely because it issues one GPU encoder pass per
        paragraph (and power-cycles the PCIe GPU each call).
        """
        pred = self.coref().predict(text)
        # maverick returns char offsets under this key; keep as plain lists (JSON)
        return pred.get("clusters_char_offsets", [])

    # ------------------------------------------------------------------ batched
    def coref_clusters_batched(self, texts: list[str]):
        """Char-offset clusters for many texts, batching ONLY the deberta encoder.

        maverick's clustering tail cannot tensor-batch (model_mes.py does
        `mention_idxs = mention_idxs[0]` — per-document), but its deberta encoder
        is fully batchable. So we:

          1. replicate predict()'s preprocessing (preprocess + tokenize) per text
             to obtain each item's input_ids / true length — EXACTLY as predict
             does, so the per-item tokenisation is identical;
          2. pad to the batch max and run `model.encoder(...)` ONCE over B×S on the
             GPU (one pass instead of ~B sequential ones), fp32;
          3. temporarily swap `model.encoder` for a stand-in that hands back the
             precomputed hidden-state slice for item i (to that item's true,
             unpadded length), then call maverick's UNCHANGED `predict(text)` per
             item in order — its tokenize + clustering tail + char-offset mapping
             all run verbatim, only the encoder is served from the batch.

        Because the clustering tail is maverick's own code on per-item hidden
        states, cluster outputs stay faithful to the serial path (modulo the
        ~1e-5 batched-matmul/padding noise discussed in the README; verify mode
        and `coref_clusters` are how that is policed). fp32 throughout — no
        `.half()`.
        """
        import torch

        if not texts:
            return []

        c = self.coref()
        model = c.model
        tokenizer = c.tokenizer

        # (1) replicate predict()'s preprocessing for every text, in order.
        per_item_ids: list[list[int]] = []
        per_item_mask: list[list[int]] = []
        for text in texts:
            tokens, eos_indices, speakers, _char_offsets = c.preprocess(text)
            tok = c.tokenize(tokens, eos_indices, speakers)
            per_item_ids.append(list(tok["input_ids"]))
            per_item_mask.append(list(tok["attention_mask"]))

        lengths = [len(ids) for ids in per_item_ids]
        s_max = max(lengths)
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
        padded_ids = [ids + [pad_id] * (s_max - n) for ids, n in zip(per_item_ids, lengths)]
        padded_mask = [m + [0] * (s_max - n) for m, n in zip(per_item_mask, lengths)]

        # (2) one batched encoder pass on the GPU. Padding is masked out by the
        #     attention_mask, so each row's real positions match the unbatched
        #     encoder up to batched-matmul noise (~1e-5). Build the B×S tensors on
        #     the host then stage them onto the device — the ONLY new device legs.
        dev = next(model.encoder.parameters()).device
        ids_t = torch.tensor(padded_ids, dtype=torch.long).to(dev)      # host-device-boundary: stage batched coref input_ids onto the GPU
        mask_t = torch.tensor(padded_mask, dtype=torch.long).to(dev)    # host-device-boundary: stage batched coref attention_mask onto the GPU
        with torch.no_grad():
            hidden = model.encoder(input_ids=ids_t, attention_mask=mask_t)["last_hidden_state"]  # B×S×H, fp32

        # (3) serve precomputed slices through a temporary encoder stand-in, then
        #     run maverick's own predict() per item. Assign into `_modules`
        #     directly: nn.Module.__setattr__ refuses a non-Module under an
        #     existing module name. Restore unconditionally.
        real = model.encoder
        stand_in = _PrecomputedEncoder(real, hidden, lengths)
        model._modules["encoder"] = stand_in
        try:
            out = []
            for text in texts:
                pred = c.predict(text)
                out.append(pred.get("clusters_char_offsets", []) or [])
            return out
        finally:
            model._modules["encoder"] = real

    # ------------------------------------------------------------ fidelity check
    @staticmethod
    def _clusters_as_set(clusters):
        """Canonical, order-independent form of one doc's clusters for comparison.

        Char offsets are INTEGERS (no float slack possible at this layer), so exact
        set equality is the right test: a cluster set differs iff some upstream
        sigmoid>0.5 / argmax decision actually flipped. Cluster order, mention
        order within a cluster, and list-vs-tuple are all immaterial → frozenset.
        """
        return {frozenset(tuple(span) for span in cluster) for cluster in clusters}

    def _coref_fidelity(self, serial, batched) -> dict:
        """Compare serial vs batched clusters per text; return a pass/fail diff."""
        mismatches = []
        for i, (s, b) in enumerate(zip(serial, batched)):
            if self._clusters_as_set(s) != self._clusters_as_set(b):
                mismatches.append({"index": i, "serial": s, "batched": b})
        return {
            "ok": (not mismatches) and len(serial) == len(batched),
            "n": len(serial),
            "n_mismatch": len(mismatches),
            "mismatches": mismatches,
        }

    def _run_coref(self, texts, mode):
        """Dispatch a coref request. Returns (clusters_aligned_to_texts, verify|None)."""
        if mode == "serial":
            return [self.coref_clusters(t) for t in texts], None
        if mode == "verify":
            # run BOTH; load the SERIAL reference (trusted) and report fidelity, so
            # a --coref-verify run is also a safe run even if the fast path drifts.
            serial = [self.coref_clusters(t) for t in texts]
            batched = self.coref_clusters_batched(texts)
            return serial, self._coref_fidelity(serial, batched)
        # default: the fast batched path
        return self.coref_clusters_batched(texts), None

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
        # mode = "batched" (default, fast: one encoder pass) | "serial" (reference)
        # | "verify" (run both, report fidelity, return the serial reference).
        coref = coref_verify = None
        if req.get("coref"):
            mode = req.get("coref_mode", "batched")
            coref, coref_verify = self._run_coref(texts, mode)
            note = f" [{mode}]" + (
                ("" if coref_verify is None
                 else f" verify={'PASS' if coref_verify['ok'] else 'FAIL'}"
                      f"({coref_verify['n_mismatch']}/{coref_verify['n']})"))
            print(f"[timing] {len(texts)} texts: parse {t1 - t0:.1f}s, "
                  f"coref {time.perf_counter() - t1:.1f}s{note}", flush=True)

        if req.get("format") == "json":
            out = {"ok": True, "docs": [doc_to_json(d) for d in docs]}
            if coref is not None:
                out["coref"] = coref
            if coref_verify is not None:
                out["coref_verify"] = coref_verify
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
        if coref_verify is not None:
            meta["coref_verify"] = coref_verify
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
