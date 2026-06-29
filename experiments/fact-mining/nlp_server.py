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
   "format": "facts" | "docbin" | "json", "disable": ["lemmatizer", ...],
   "coref": bool, "coref_mode": "batched" | "serial" | "verify"}
     format="facts" (the LEAN default for load_facts --remote) — run the SSOT
       extractor (extract.doc_to_facts) host-side and return finished JSON facts,
       so the client deserializes JSON only and never imports spaCy/torch.
     coref_mode (only when coref=true):
       "batched" (default) — one batched deberta-encoder pass over all texts,
                  then maverick's per-doc clustering tail. Fast.
       "serial"           — the reference path: one maverick predict() per text.
       "verify"           — run BOTH, return the serial clusters AND a
                  "coref_verify" pass/fail diff so fidelity can be audited once.
  {"op": "info"}                      -> loaded models, gpu status
  {"op": "ping"}                      -> liveness

Reply: ZMQ multipart frames.
  parse + format=facts  -> [ <json {ok, format:"facts", n, model, lang, facts:[...]}> ]
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

from extract import doc_to_facts  # SSOT per-doc fact extractor (ADR-0012 P1)
# SSOT shape-policy primitives (ONE home; never copied): the masked-padding primitive and
# the OOM bound (the conservative memory model `MemModel`/`peak_variable_bytes` + the
# VRAM-derived `chunk_by_vram` + the shared `headroom_bytes` rule). The OOM bound lives in
# shape_buckets so the jax bucket-group batched encode shares the SAME inequality (the
# do-not-copy mandate); imported here so the torch batched encode consumes it, never forking
# a second budget. See the OOM-bound comment below + shape_buckets for the
# derive-from-what-actually-exhausts-memory (quadratic peak) rationale (ADR-0000 Specimen 3; P1).
from shape_buckets import (  # the ONE padder + the ONE OOM bound (P1)
    ENCODE_MAX_DOCS, MemModel, chunk_by_vram, cpu_fallback_available_bytes,
    forward_budget_after_retained, headroom_bytes, pad_to)
from spans import get_tracer  # SSOT tracer (no jax/numpy import; host-only psycopg, lazy)


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


def encode_last_hidden_state(model, input_ids, attention_mask):
    """Run maverick's deberta encoder for ONE document and return its
    `last_hidden_state` as a HOST tensor [S, TH] (batch axis removed).

    The single-document encode PRIMITIVE (one unpadded forward over [1, S, TH]). The
    LIVE coref backends no longer call this — they both go through the SSOT batched
    encode `Server._encode_docs` (ONE padded forward over all texts). This is retained
    as the leaf bit-exact probe for `test_livewire_fidelity.py`, which encodes a single
    text and compares the over-the-wire token offsets to maverick's own `predict` (at
    n==1 the batched path pads nothing, so the two encodes are bit-identical — that is
    why the livewire probe stays a valid single-doc oracle). It is a torch host<->device
    crossing, kept in nlp_server.py — the torch device home — per the device-transfer
    single-home mandate. nlp_server authors the torch op; it authors NO jax op.

    The encoder call is identical to maverick's own forward
    (`self.encoder(input_ids=..., attention_mask=...)["last_hidden_state"]`), so on the
    same inputs it is bit-identical to what maverick.predict would compute internally.
    fp32 throughout (the model is forced fp32 at load), matching the daemon's contract.
    """
    import torch

    dev = next(model.encoder.parameters()).device
    ids_t = torch.tensor([input_ids], dtype=torch.long).to(dev)        # host-device-boundary: stage coref input_ids onto the GPU
    mask_t = torch.tensor([attention_mask], dtype=torch.long).to(dev)  # host-device-boundary: stage coref attention_mask onto the GPU
    with torch.no_grad():
        hidden = model.encoder(input_ids=ids_t, attention_mask=mask_t)["last_hidden_state"]  # 1×S×TH, fp32
    # [S, TH] on the host: the wire client packs it to raw float32 bytes. Pulling to
    # the host HERE keeps the device->host pull in the torch home (the client is
    # host-only numpy and never touches the device).
    return hidden[0].detach().cpu()  # host-device-boundary: pull lhs device->host for the wire


# ---------------------------------------------------------------- OOM bound
# The memory model (MemModel/peak_variable_bytes), the VRAM chunker (chunk_by_vram) and the
# headroom rule are imported at the top (the ONE home is shape_buckets; the jax bucket-group
# batched encode shares the SAME inequality). A batched deberta encode runs ONE padded forward
# over [N, max_S, TH]; its peak is QUADRATIC in max_S (the disentangled-attention [N,H,S,S]
# scores), so the chunker bounds that derived BYTES peak against the free CUDA memory — not a
# linear token proxy that was blind to it (ADR-0000 Specimen 3; the full rationale + the
# functions live in shape_buckets.py). _encode_docs derives `mm` from the encoder's HF config +
# the actual FFN weight and `available` from torch.cuda.mem_get_info, mirroring the jax path.


class _PrecomputedEncoder:
    """Temporary stand-in for maverick's deberta encoder during batched coref.

    Installed into `model._modules['encoder']` only for the span of the per-item
    `predict()` calls in `Server.coref_clusters_batched`. Each call returns the
    precomputed per-document hidden-state slice for the NEXT item (predict() runs
    items in order), already sliced to that item's true unpadded length by the SSOT
    batched encode, so maverick's forward/clustering tail runs unchanged on a
    per-document hidden state. It holds the per-doc slices (not the padded batch +
    lengths), so it is agnostic to how `_encode_docs` chunked the padded forwards.

    It is a plain object (not an nn.Module) and is stuck into `_modules`
    deliberately: `self.encoder(...)` then resolves here, and `self.encoder.device`
    is proxied to the real encoder. Nothing in maverick's forward iterates the
    module tree between install and restore, so a non-Module sitting in `_modules`
    is safe for that window.
    """

    def __init__(self, real, slices, lengths):
        # `real` first so __getattr__ (which proxies to it) never recurses.
        self.real = real
        self.device = real.device  # forward reads self.encoder.device in several spots
        self.slices = slices       # list of per-doc [S_i, TH] device tensors (unpadded)
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
        return {"last_hidden_state": self.slices[i][None]}  # add batch axis -> 1×S_i×TH

    def __getattr__(self, name):
        # proxy anything else (e.g. .config) to the wrapped encoder
        return getattr(self.__dict__["real"], name)


class Server:
    def __init__(self, default_model: str, gpu: bool,
                 coref_backend: str = "maverick",
                 decode_addr: str = "tcp://192.168.122.1:5600"):
        self.gpu = gpu
        if gpu:
            # routes thinc ops to cupy and (for trf) torch to CUDA
            spacy.require_gpu()  # host-device-boundary: enable GPU for spaCy-trf
        self.default_model = default_model
        self.models: dict[str, "spacy.Language"] = {}
        self.get(default_model)  # preload — the slow part, done once
        self._coref = None       # maverick-coref, loaded lazily on first coref request
        # coref decode backend: "maverick" (reference, default — its own decode tail)
        # or "jax-daemon" (retire the decode tail from the live path: torch encodes
        # here, the JAX decode daemon at decode_addr decodes). A request may override
        # both per call (coref_backend / decode_addr fields).
        self.coref_backend = coref_backend
        self.decode_addr = decode_addr
        self._decoders: dict[str, object] = {}  # addr -> RemoteDecode (lazy, reused)
        get_tracer().configure(process="nlp_server")  # tracing stays OFF until a request carries a context

    def get(self, name: str | None):
        name = name or self.default_model
        if name not in self.models:
            self.models[name] = spacy.load(name)
        return self.models[name]

    def coref(self):
        """Lazily load maverick-coref (host-only dependency, GPU if available)."""
        if self._coref is None:
            from maverick import Maverick  # host-only; imported on demand

            # The checkpoint is a PyTorch-Lightning/OmegaConf pickle PyTorch >=2.6
            # refuses under weights_only=True; the SSOT loader allowlists its
            # specific omegaconf globals (no arbitrary-execution exposure; one home
            # so no site forgets it — ADR-0012 P1).
            from maverick_load import safe_maverick_load
            with safe_maverick_load():
                self._coref = Maverick(device="cuda" if self.gpu else "cpu")  # host-device-boundary: place maverick on GPU

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

    # ------------------------------------------------------- SSOT batched encode
    def _encode_docs(self, texts: list[str]):
        """THE one home for the batched deberta encode (ADR-0012 P1) — shared by BOTH
        coref backends (`coref_clusters_batched` and `coref_clusters_jax_daemon`).

        maverick's clustering/decode tail cannot tensor-batch (model_mes.py does
        `mention_idxs = mention_idxs[0]` — per-document), but its deberta encoder is
        fully batchable. So, ONCE here:

          1. run the SSOT preprocess+tokenize (`prepare_decode_inputs`) per text — the
             SAME prep capture_fixtures and the decode tail consume — to obtain each
             doc's `DecodeInputs` (input_ids / true length / structural maps / char
             offsets), EXACTLY as predict does, so the per-item tokenisation is identical;
          2. pad to the (chunk) max and run `model.encoder(...)` ONCE per chunk over
             [N, max_S, TH] on the GPU (one pass instead of N sequential ones), fp32 —
             chunked by `chunk_by_vram` so the padded forward is OOM-bounded
             (never one giant pad over a book);
          3. slice each doc's UNPADDED hidden state `[S_i, TH]` back out of its chunk.

        Returns, in TEXT ORDER, a list of `(DecodeInputs, lhs_slice)`:
          * `coref_clusters_batched` feeds each device slice back through maverick's
            own clustering tail (via the `_PrecomputedEncoder` stand-in);
          * `coref_clusters_jax_daemon` pulls each slice to the host and ships it to the
            JAX decode daemon.
        There is exactly ONE writer of the padded-forward logic (this method) — the
        padded encode is NOT hand-duplicated into a second backend (audit cancer B,
        ADR-0012 P1). Padding is masked out by the attention_mask, so each row's real
        positions match the unbatched encoder up to batched-matmul noise (~1e-5); the
        discrete cluster SETS must still equal the serial reference (ADR-0009 discrete
        tier), which `coref_mode='verify'` confirms. fp32 throughout — no `.half()`.
        """
        import torch

        from coref_decode_inputs import prepare_decode_inputs

        _T = get_tracer()
        c = self.coref()
        model = c.model
        tokenizer = c.tokenizer

        # (1) SSOT preprocess+tokenize for every text, in order. Spanned separately from
        # the GPU forward so the trace says whether the encode cost is CPU tokenisation or
        # the deberta forward (and thus whether length-bucketing the batch would help).
        with _T.span("encode.tokenize_prep", n_texts=len(texts)):
            dis = [prepare_decode_inputs(c, text) for text in texts]
        lengths = [len(di.input_ids) for di in dis]
        pad_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0
        dev = next(model.encoder.parameters()).device

        # OOM bound inputs — the SAME memory model + headroom rule as the jax path; only the
        # free-memory QUERY differs by framework (here torch/CUDA). `mm` from the encoder's HF
        # config (num_heads/hidden/pos_ebd_size) + its real FFN width (intermediate_size);
        # `available` from torch's driver-level free (the maverick weights are already resident,
        # so free already excludes them) minus the shared headroom.
        enc_cfg = model.encoder.config
        _max_rel = getattr(enc_cfg, "max_relative_positions", -1)
        if _max_rel < 1:
            _max_rel = enc_cfg.max_position_embeddings
        _pos_buckets = getattr(enc_cfg, "position_buckets", -1)
        mm = MemModel(
            num_heads=enc_cfg.num_attention_heads,
            hidden=enc_cfg.hidden_size,
            intermediate=enc_cfg.intermediate_size,
            pos_ebd_size=_pos_buckets if _pos_buckets > 0 else _max_rel,
        )
        if dev.type == "cuda":
            free, total = torch.cuda.mem_get_info(dev)  # driver free already excludes resident weights
            available = max(0, free - headroom_bytes(total))
        else:
            available = cpu_fallback_available_bytes()  # ONE home (P1), shared with the jax path

        # FINDING 1 — the RETAINED-OUTPUT OOM class (one level up from the per-forward bound).
        # This method RETURNS every doc's [S_i, TH] slice (its consumers — coref_clusters_batched
        # via the _PrecomputedEncoder, coref_clusters_jax_daemon via the wire — hold ALL of them
        # co-resident, by construction of maverick's per-item predict()). So the chunker's budget
        # must RESERVE that O(total docs) accumulation up front, not just one forward's peak. The
        # jax-unified path STREAMS instead (frees each slice after decode); this torch reference
        # path cannot without re-architecting the predict() stand-in, so it reserves and fails
        # LOUD (RetainedTooLargeError, pointing at the streaming path) rather than raw CUDA-OOM.
        available = forward_budget_after_retained(available, mm, lengths)

        # (2)+(3) one padded forward per VRAM-bounded chunk; slice unpadded lhs per doc. A doc
        # too big even at B=1 raises shape_buckets.DocTooLargeError (loud, bounded), never a raw
        # CUDA OOM.
        with _T.span("encode.forward", n_texts=len(texts), max_len=max(lengths) if lengths else 0):
            slices: list[object] = [None] * len(texts)
            for chunk in chunk_by_vram(lengths, mm, available, ENCODE_MAX_DOCS):
                s_max = max(lengths[i] for i in chunk)
                # ONE padder (P1): the SSOT `pad_to` — the SAME primitive the jax-unified
                # encode/decode use (shape_buckets.pad_to). No hand-rolled second padder.
                # Here the target is the chunk-max (OOM-bounding the batched forward); the
                # jax encode targets a ladder bucket (compile-bounding). Different targets,
                # one padder.
                padded_ids = [pad_to(dis[i].input_ids, s_max, pad_id) for i in chunk]
                padded_mask = [pad_to(dis[i].attention_mask, s_max, 0) for i in chunk]
                ids_t = torch.tensor(padded_ids, dtype=torch.long).to(dev)    # host-device-boundary: stage batched coref input_ids onto the GPU
                mask_t = torch.tensor(padded_mask, dtype=torch.long).to(dev)  # host-device-boundary: stage batched coref attention_mask onto the GPU
                with torch.no_grad():
                    hidden = model.encoder(input_ids=ids_t, attention_mask=mask_t)["last_hidden_state"]  # [chunk, s_max, TH] fp32
                for row, i in enumerate(chunk):
                    # CLONE (not a bare view): hidden[row, :S_i, :] is a prefix slice of the
                    # contiguous [chunk, s_max, TH] base, so it shares — and PINS RESIDENT —
                    # the WHOLE padded chunk (every row + every padding column) until drained.
                    # `.contiguous()` would be a no-op here (a prefix slice is already
                    # contiguous), so it would NOT free the padding; `.clone()` gives each doc
                    # its own [S_i, TH] buffer and lets the padded base free at chunk end, so
                    # co-resident memory is sum-of-unpadded-slices, not sum-of-padded-chunks.
                    slices[i] = hidden[row, :lengths[i], :].clone()  # [S_i, TH] unpadded device slice
                del hidden  # drop the padded chunk now that every doc owns its own slice
        return list(zip(dis, slices))

    # ------------------------------------------------------------------ batched
    def coref_clusters_batched(self, texts: list[str]):
        """Char-offset clusters for many texts, batching ONLY the deberta encoder.

        The encode is the SSOT `_encode_docs` (one OOM-bounded padded forward, shared
        with the jax-daemon backend). Here we temporarily swap `model.encoder` for a
        stand-in that hands back each doc's precomputed hidden-state slice (to its true,
        unpadded length), then call maverick's UNCHANGED `predict(text)` per item in
        order — its tokenize + clustering tail + char-offset mapping all run verbatim,
        only the encoder is served from the batch.

        Because the clustering tail is maverick's own code on per-item hidden states,
        cluster outputs stay faithful to the serial path (modulo the ~1e-5 batched-
        matmul/padding noise discussed in the README; verify mode and `coref_clusters`
        are how that is policed).
        """
        if not texts:
            return []

        c = self.coref()
        model = c.model
        encoded = self._encode_docs(texts)  # SSOT batched encode (ONE home)
        slices = [lhs for (_di, lhs) in encoded]
        lengths = [len(di.input_ids) for (di, _lhs) in encoded]

        # serve precomputed slices through a temporary encoder stand-in, then run
        # maverick's own predict() per item. Assign into `_modules` directly:
        # nn.Module.__setattr__ refuses a non-Module under an existing module name.
        # Restore unconditionally.
        real = model.encoder
        stand_in = _PrecomputedEncoder(real, slices, lengths)
        model._modules["encoder"] = stand_in
        try:
            out = []
            for text in texts:
                pred = c.predict(text)
                out.append(pred.get("clusters_char_offsets", []) or [])
            return out
        finally:
            model._modules["encoder"] = real

    # -------------------------------------------------------------- jax-daemon
    def _decoder(self, addr: str):
        """Lazily create + reuse a RemoteDecode client per decode-daemon address.

        coref_decode_client is HOST-ONLY (numpy wire-pack + zmq, no device framework),
        so importing it here does NOT make nlp_server author a jax op — the JAX decode
        runs in the daemon. One client per addr, reused across requests."""
        from coref_decode_client import RemoteDecode  # host-only wire client

        if addr not in self._decoders:
            self._decoders[addr] = RemoteDecode(addr)
        return self._decoders[addr]

    def coref_clusters_jax_daemon(self, texts: list[str], decode_addr: str):
        """Char-offset clusters via the JAX decode DAEMON — maverick's decode tail
        retired from the live path.

        Two collapsed steps over ALL paragraphs (no per-paragraph round-trips):
        (1) ONE batched deberta encode via the SSOT `_encode_docs` (the SAME OOM-bounded
            padded forward `coref_clusters_batched` uses), then pull each doc's
            `last_hidden_state` slice [S_i, TH] to the host for the wire;
        (2) ship ALL docs' decode inputs in ONE multi-doc request to the jax decode
            daemon (`RemoteDecode.decode_batch`), which loops `decode_document_host`
            per doc (the decode compute stays per-doc/ragged — only the WIRE batches)
            and returns every doc's `clusters_token_offsets` in one reply;
        (3) map each doc's token offsets -> CHAR offsets with the shared SSOT mapper
            (maverick's `clusters_char_offsets` replica), so the result matches
            `coref_clusters`' contract exactly.

        nlp_server authors NO jax op here: the decode is the daemon's. The encode is
        ONE padded forward (was N sequential) and the decode is ONE wire round-trip
        (was N) — the two cuts the run-28 trace flagged. singletons=False to match
        `coref_clusters` (maverick.predict's default).
        """
        # SSOT token->char mapper (framework-free; ADR-0012 P1)
        from coref_decode_inputs import clusters_token_to_char_offsets

        if not texts:
            return []

        client = self._decoder(decode_addr)
        _T = get_tracer()

        # (1) ONE batched encode for every paragraph (SSOT home), then host-pull per doc.
        with _T.span("nlp_server.encode", n_texts=len(texts)):
            encoded = self._encode_docs(texts)
            docs = []
            for di, lhs in encoded:
                host_lhs = lhs.detach().cpu()  # host-device-boundary: pull per-doc lhs device->host for the wire
                docs.append({
                    "lhs": host_lhs,
                    "attention_mask": di.attention_mask,
                    "eos_mask": di.eos_mask,
                    "tokens": di.tokens,
                    "subtoken_map": di.subtoken_map,
                    "new_token_map": di.new_token_map,
                })

        # (2) ONE multi-doc decode request (collapses N round-trips to 1).
        # WIRE 2 (nlp_server<->decode daemon): this span IS the daemon's blocked time on
        # decode; coref_decode_client.decode_batch injects the context INSIDE it so the
        # decode daemon's spans parent under this single wait.
        with _T.span("nlp_server.zmq_wait.decode", n_texts=len(texts)):
            clusters_tok_per_doc = client.decode_batch(docs, singletons=False)

        # (3) token offsets -> char offsets per doc (maverick clusters_char_offsets replica)
        out = []
        for (di, _lhs), clusters_tok in zip(encoded, clusters_tok_per_doc):
            out.append(clusters_token_to_char_offsets(clusters_tok, di.char_offsets) or [])
        return out

    # ------------------------------------------------------------- jax-unified
    def coref_clusters_jax_unified(self, texts: list[str], decode_addr: str):
        """Char-offset clusters via the UNIFIED jax-only daemon — the torch encode is
        OFF the path entirely.

        nlp_server ships only TEXT (tiny) and gets CHAR-offset clusters back. The whole
        coref forward (tokenize+mask -> deberta encode -> decode -> token->char offsets)
        runs IN the jax-only daemon, in ONE process that imports jax and never torch. So
        unlike the `jax-daemon` backend, this path does NOT encode here (no
        `_encode_docs`, no torch deberta forward) and ships NO dense lhs / eos_mask over
        the wire — nlp_server is a pure TEXT relay for coref. nlp_server stays torch-only
        (spaCy-trf for the OTHER nlp ops); it authors no jax op (the client is host-only
        zmq+json). singletons=False to match `coref_clusters` (maverick.predict default).
        """
        if not texts:
            return []
        client = self._decoder(decode_addr)
        _T = get_tracer()
        with _T.span("nlp_server.zmq_wait.coref", n_texts=len(texts)):
            return client.coref(texts, singletons=False)

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

    def _coref_fidelity(self, serial, candidate, cand_label: str = "batched") -> dict:
        """Compare the SERIAL reference vs a candidate path per text; pass/fail diff.
        `cand_label` names the candidate in the mismatch records ("batched" for the
        maverick encoder-batch path, "jax_daemon" for the jax decode backend)."""
        mismatches = []
        for i, (s, b) in enumerate(zip(serial, candidate)):
            if self._clusters_as_set(s) != self._clusters_as_set(b):
                mismatches.append({"index": i, "serial": s, cand_label: b})
        return {
            "ok": (not mismatches) and len(serial) == len(candidate),
            "candidate": cand_label,
            "n": len(serial),
            "n_mismatch": len(mismatches),
            "mismatches": mismatches,
        }

    def _run_coref(self, texts, mode, backend, decode_addr):
        """Dispatch a coref request. Returns (clusters_aligned_to_texts, verify|None).

        backend = "maverick" (reference: its own decode tail, batched/serial/verify)
                | "jax-daemon"  (torch encodes here, the JAX daemon decodes)
                | "jax-unified" (the JAX daemon does EVERYTHING: text -> encode ->
                                 decode -> clusters; torch encode off the path).
        For any backend, mode == "verify" runs the trusted SERIAL maverick reference
        too and reports a pass/fail fidelity diff against it.
        """
        if backend == "jax-unified":
            jaxu = self.coref_clusters_jax_unified(texts, decode_addr)
            if mode == "verify":
                serial = [self.coref_clusters(t) for t in texts]
                return serial, self._coref_fidelity(serial, jaxu, "jax_unified")
            return jaxu, None
        if backend == "jax-daemon":
            jaxd = self.coref_clusters_jax_daemon(texts, decode_addr)
            if mode == "verify":
                serial = [self.coref_clusters(t) for t in texts]
                return serial, self._coref_fidelity(serial, jaxd, "jax_daemon")
            return jaxd, None
        # backend == "maverick" (reference)
        if mode == "serial":
            return [self.coref_clusters(t) for t in texts], None
        if mode == "verify":
            # run BOTH; load the SERIAL reference (trusted) and report fidelity, so
            # a --coref-verify run is also a safe run even if the fast path drifts.
            serial = [self.coref_clusters(t) for t in texts]
            batched = self.coref_clusters_batched(texts)
            return serial, self._coref_fidelity(serial, batched, "batched")
        # default: the fast batched path
        return self.coref_clusters_batched(texts), None

    def handle(self, raw: bytes) -> list[bytes]:
        """Map one request frame to the reply frames. Pure data in/out."""
        req = json.loads(raw)
        op = req.get("op", "parse")
        # WIRE 1 receipt: adopt the client's trace context (enables tracing for this
        # request iff the client sent one; disables it otherwise). Subsequent spans
        # parent under the client's zmq_wait span (ADR-0012 P2).
        _T = get_tracer()
        _T.extract(req)

        if op == "ping":
            return [json.dumps({"ok": True, "pong": True}).encode()]
        if op == "info":
            return [json.dumps({
                "ok": True, "gpu": self.gpu,
                "loaded": list(self.models),
                "default": self.default_model,
                "coref_backend": self.coref_backend,
                "decode_addr": self.decode_addr,
            }).encode()]
        if op != "parse":
            return [json.dumps({"ok": False, "error": f"unknown op {op!r}"}).encode()]

        # ONE per-request root span (mirrors decode_server.handle): parse, coref AND
        # the reply serialization below all nest UNDER it. This makes the client's
        # client.zmq_wait.nlp_server have EXACTLY ONE peer-process child by
        # construction, so trace.blocking's overhead_ms = wait - handle is the real
        # transport/queue cost — not wait - parse with coref+serialize mis-attributed
        # to "transport" (the adversarial-review WIRE-1 fan-out finding).
        with _T.span("nlp_server.handle", op=op, n_texts=len(req.get("texts") or [])):
            texts = req.get("texts") or []
            nlp = self.get(req.get("model"))
            disable = [p for p in (req.get("disable") or []) if p in nlp.pipe_names]
            t0 = time.perf_counter()
            with _T.span("nlp_server.parse", n_texts=len(texts)):
                docs = list(nlp.pipe(texts, disable=disable))
            t1 = time.perf_counter()

            # optional coreference: per-text char-offset clusters, aligned to `docs`.
            # mode = "batched" (default, fast: one encoder pass) | "serial" (reference)
            # | "verify" (run both, report fidelity, return the serial reference).
            coref = coref_verify = None
            if req.get("coref"):
                mode = req.get("coref_mode", "batched")
                # per-request backend / decode-addr override the server defaults
                backend = req.get("coref_backend") or self.coref_backend
                decode_addr = req.get("decode_addr") or self.decode_addr
                with _T.span("nlp_server.coref", backend=backend, mode=mode, n_texts=len(texts)):
                    coref, coref_verify = self._run_coref(texts, mode, backend, decode_addr)
                note = f" [{backend}/{mode}]" + (
                    ("" if coref_verify is None
                     else f" verify={'PASS' if coref_verify['ok'] else 'FAIL'}"
                          f"({coref_verify['n_mismatch']}/{coref_verify['n']})"))
                print(f"[timing] {len(texts)} texts: parse {t1 - t0:.1f}s, "
                      f"coref {time.perf_counter() - t1:.1f}s{note}", flush=True)

            if req.get("format") == "facts":
                # THE FACTS WIRE (ADR-0012 P7): run the SSOT extractor host-side so the
                # --remote client receives finished JSON facts and never imports spaCy.
                # Coref clusters (if computed) are attached PER DOC here, exactly where
                # the OLD remote client used to attach them — the resolution is
                # identical, only its home moved host-side. Discrete records (strings +
                # int offsets) -> JSON is exact (ADR-0009 bit-invariant).
                with _T.span("nlp_server.facts", n_docs=len(docs)):
                    facts = [doc_to_facts(d, coref_clusters=(coref[i] if coref is not None else None))
                             for i, d in enumerate(docs)]
                out = {
                    "ok": True, "format": "facts", "n": len(docs),
                    "model": nlp.meta["name"], "lang": nlp.meta["lang"], "facts": facts,
                }
                if coref_verify is not None:
                    out["coref_verify"] = coref_verify
                return [json.dumps(out).encode()]

            if req.get("format") == "json":
                out = {"ok": True, "docs": [doc_to_json(d) for d in docs]}
                if coref is not None:
                    out["coref"] = coref
                if coref_verify is not None:
                    out["coref_verify"] = coref_verify
                return [json.dumps(out).encode()]

            # DocBin serialization + meta build are SERVER work inside the client's
            # blocked window, so they belong INSIDE the handle span (not stranded
            # out-of-span and silently mis-attributed to transport overhead).
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

    def warmup(self):
        """Pre-pay the one-time lazy GPU init at BOOT so the FIRST real request is warm.

        The first request otherwise eats ~12s (measured, run 27): CUDA-context init +
        cuDNN autotune + model->GPU + the first deberta/roberta forward (and, on the
        jax-daemon backend, the decode daemon's first XLA compile). After warmup the
        first request matches steady state (~0.45s/5-para, run 28). We run ONE dummy
        paragraph through the SAME path a real request takes — parse + the configured
        coref backend + the SSOT extractor — so every lazy init fires here, not on a
        user's first call. Launch with the --coref-backend you will actually request so
        warmup covers that exact path (the deberta encode is shared by both backends;
        only the jax-daemon decode round-trip is backend-specific).

        Best-effort (ADR-0002 genuinely-right fallback): a warmup failure is logged
        LOUDLY but does NOT stop the daemon serving — a cold first request is slow, not
        broken (e.g. the decode daemon may not be up yet for the jax-daemon path)."""
        # a 2-sentence paragraph WITH a coreference, so coref (encode + decode tail)
        # actually runs and the cluster path is exercised, not just the parse.
        text = "Alice met Bob in Paris. She greeted him warmly there."
        t0 = time.perf_counter()
        try:
            docs = list(self.get(None).pipe([text]))      # warms the spaCy-trf GPU forward
            coref, _ = self._run_coref([text], "batched", self.coref_backend, self.decode_addr)
            for i, d in enumerate(docs):                   # warms the SSOT extractor path
                doc_to_facts(d, coref_clusters=(coref[i] if coref is not None else None))
            print(f"[warmup] pipeline warm in {time.perf_counter() - t0:.1f}s "
                  f"(coref_backend={self.coref_backend}) — first request will be warm",
                  flush=True)
        except Exception as e:  # cold-but-serving beats refusing to boot
            traceback.print_exc()
            print(f"[warmup] FAILED after {time.perf_counter() - t0:.1f}s ({e!r}) — the "
                  f"first real request will pay the cold cost", flush=True)

    def serve(self, addr: str, warmup: bool = True):
        sock = zmq.Context.instance().socket(zmq.REP)
        sock.bind(addr)
        print(f"spaCy daemon listening on {addr} | default={self.default_model} "
              f"| gpu={self.gpu} | pipes={self.get(None).pipe_names}", flush=True)
        # LIVENESS INVARIANT (ADR-0014 second-opinion fix): NEVER block before the recv
        # loop. A synchronous warmup() here bound the socket but left it UNSERVABLE — the
        # daemon could not answer ping/info while warming, so (a) the client's await_ready
        # could never tell "warming" from "down", and (b) a stalled warmup (maverick's
        # first-load HF read on this host, or warming the WRONG hardcoded backend) wedged
        # the daemon forever with idle CPU and no error. We now serve IMMEDIATELY: the
        # first real request compiles lazily (one-time; the persistent XLA cache makes it
        # fast thereafter) and warms the REQUEST's backend, not a hardcoded default. The
        # `warmup` flag and warmup() are retained for an OPTIONAL explicit pre-warm but are
        # never auto-run before serving (that is the bug). `_ = warmup` keeps the CLI flag.
        _ = warmup
        while True:
            raw = sock.recv()  # exactly one frame per request (REP state machine)
            try:
                frames = self.handle(raw)
            except Exception as e:  # never crash the daemon on a bad request
                traceback.print_exc()  # full traceback to host console for diagnosis
                frames = [json.dumps({"ok": False, "error": repr(e)}).encode()]
            sock.send_multipart(frames)  # exactly one reply per request
            get_tracer().flush()  # persist this request's spans (no-op when untraced)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--addr", default="tcp://0.0.0.0:5599",
                    help="ZMQ bind address (default %(default)s)")
    ap.add_argument("--model", default="en_core_web_trf",
                    help="default pipeline to preload (default %(default)s)")
    ap.add_argument("--gpu", action="store_true", help="use the GPU (require_gpu)")
    ap.add_argument("--coref-backend", default="maverick",
                    choices=["maverick", "jax-daemon", "jax-unified"],
                    help="default coref decode backend: 'maverick' (reference, its own "
                         "decode tail), 'jax-daemon' (torch encodes here, the JAX decode "
                         "daemon decodes), or 'jax-unified' (the JAX daemon does the WHOLE "
                         "forward: text -> encode -> decode; torch encode off the path). A "
                         "request may override per call. (default %(default)s)")
    ap.add_argument("--decode-addr", default="tcp://192.168.122.1:5600",
                    help="ZMQ address of the JAX coref daemon (coref_decode_server.py), "
                         "used by the jax-daemon and jax-unified backends "
                         "(default %(default)s)")
    ap.add_argument("--no-warmup", action="store_true",
                    help="skip the boot-time pipeline warmup; the first real request "
                         "then pays the ~12s cold CUDA/cuDNN/first-forward cost")
    args = ap.parse_args()
    Server(args.model, args.gpu,
           coref_backend=args.coref_backend,
           decode_addr=args.decode_addr).serve(args.addr, warmup=not args.no_warmup)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
