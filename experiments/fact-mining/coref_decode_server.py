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

  coref -> [ <json meta> ]  (single frame, no binary)   [UNIFIED jax-only op]
      meta = {"op": "coref", "texts": [str, ...], "singletons": bool}
      The daemon does tokenize+mask -> deberta encode -> decode IN-PROCESS; only TEXT
      crosses the wire (the dense lhs + eos_mask never serialise). Requires the daemon
      to be started with --deberta-weights (the fine-tuned deberta export).

Reply: ZMQ multipart (always a single JSON frame).
  decode ok  -> [ {"ok": true, "clusters": [[[[s,e],...],...], ...], "singletons": bool} ]
                (clusters[i] is doc i's clusters in TOKEN offsets, aligned to the docs)
  coref ok   -> [ {"ok": true, "clusters": [[[[s,e],...],...], ...], "singletons": bool} ]
                (clusters[i] is text i's clusters in CHAR offsets — this daemon owns the
                 preprocess, so it returns maverick's clusters_char_offsets contract)
  info/ping  -> [ {"ok": true, ...} ]
  error      -> [ {"ok": false, "error": "..."} ]

TWO MODES (one daemon). Decode-only (the A/B `jax-daemon` backend: nlp_server encodes,
ships lhs, this daemon decodes) is the default. Pass --deberta-weights to ALSO serve the
UNIFIED `coref` op, which is JAX-ONLY (torch-free, enforced by jax_only_guard) and runs
the WHOLE forward here. The existing `decode` op is kept for the A/B + fidelity tests.

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
import time
import traceback

import numpy as np
import zmq

import coref_host_shell  # the single jax home: it owns the device lifts + the jax config
from coref_decode_inputs import (  # SSOT preprocess orchestration (framework-free)
    StandalonePreprocessor, clusters_token_to_char_offsets, prepare_decode_inputs)
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


# the reserved npz key carrying the encoder's tokenizer identity (mirrors
# export_deberta_maverick.TOKENIZER_KEY — the daemon must not retype it; P1).
DEBERTA_TOKENIZER_KEY = "__tokenizer__"


def load_deberta_npz(path: str) -> tuple[dict, dict, str]:
    """fixtures/deberta_maverick.npz -> (weights host-dict, cfg-fields dict,
    encoder_hf_model_name). HOST-only: `np.load` + scalar `.item()`; the device lift
    (lift_deberta_params) and the DebertaCfg build (build_deberta_cfg) are the jax home's,
    so this wire seam authors NO jax op. Weight entries are the dotted torch keys;
    `__cfg__<field>` entries are the DebertaCfg scalars and `__tokenizer__` is the HF
    tokenizer identity the export wrote alongside them (config AND tokenizer travel with
    the weights — P1, never retyped in the daemon; see R2/F1)."""
    weights: dict = {}
    cfg_fields: dict = {}
    tokenizer_name: str | None = None
    with np.load(path) as z:
        for k in z.files:
            if k == DEBERTA_TOKENIZER_KEY:
                tokenizer_name = str(z[k].item())
            elif k.startswith("__cfg__"):
                cfg_fields[k[len("__cfg__"):]] = z[k].item()
            else:
                weights[k] = z[k].astype(np.float32)
    if not weights or not cfg_fields or not tokenizer_name:
        raise ValueError(
            f"{path} is not a valid deberta export: {len(weights)} weights, "
            f"{len(cfg_fields)} cfg fields, tokenizer={tokenizer_name!r} "
            f"(expected weights + cfg non-empty and a {DEBERTA_TOKENIZER_KEY} identity). "
            f"Re-export with export_deberta_maverick.py (it now writes the tokenizer).")
    return weights, cfg_fields, tokenizer_name


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
    def __init__(self, weights_path: str, deberta_weights_path: str | None = None,
                 coref_model: str | None = None):
        self.weights_path = weights_path
        # the device lift happens in the shell (single jax home); we hold the
        # resulting device arrays opaquely and pass them straight back to the shell.
        self.params = coref_host_shell.lift_params(load_params(weights_path))
        self.n_params = len(self.params)

        # UNIFIED ("coref") op: optional. When the fine-tuned deberta encoder export is
        # provided, this daemon runs the WHOLE coref forward (tokenize -> encode ->
        # decode) in-process and is JAX-ONLY (no torch). The torch-free preprocess and
        # the deberta-weight lift are set up here.
        self.deberta_params = None
        self.deberta_cfg = None
        self.preprocessor = None
        self.coref_model = coref_model
        self.deberta_weights_path = deberta_weights_path
        if deberta_weights_path is not None:
            # Make this process STRUCTURALLY torch-free BEFORE the preprocess imports
            # transformers/spaCy (both of which drag torch in transitively otherwise).
            # This is the headline device-hygiene seam — see jax_only_guard.py.
            import jax_only_guard
            jax_only_guard.install()
            host_w, cfg_fields, npz_tok_name = load_deberta_npz(deberta_weights_path)
            self.deberta_cfg = coref_host_shell.build_deberta_cfg(cfg_fields)
            # FAIL LOUD AT CONSTRUCTION (ADR-0002 loudness hierarchy; ADR-0012 P5): the
            # weights are a STARTUP artifact, so the keyset bijection that the export
            # asserted (set(converted) == param_keys(cfg)) must be RE-ASSERTED on the npz
            # the daemon actually loads — a dropped tensor would otherwise surface only as
            # a per-request KeyError deep in encode, and an extra/unread tensor would load
            # SILENTLY (the exact "converted-but-unread → silent wrong forward" class the
            # export guard exists to kill). The check lives in the jax home (it needs
            # param_keys(cfg)), keeping this file jax-free. (R3/F1.)
            coref_host_shell.validate_deberta_load(host_w, self.deberta_cfg)
            self.deberta_params = coref_host_shell.lift_deberta_params(host_w)
            self.n_deberta_params = len(self.deberta_params)
            # The TOKENIZER IDENTITY travels WITH the weights (R2/F1): the export wrote
            # maverick's encoder_hf_model_name into the npz, so the preprocess tokenizes
            # with the SAME vocab the weights expect — never a daemon-side constant. An
            # explicit --coref-model is an OVERRIDE that must AGREE, else fail loud (a
            # disagreement means tokenizing with a vocab the fine-tuned weights were not
            # trained on → silently different input_ids → clusters, no shape/keyset error).
            if coref_model is not None and coref_model != npz_tok_name:
                raise ValueError(
                    f"--coref-model {coref_model!r} disagrees with the tokenizer identity "
                    f"recorded in {os.path.basename(deberta_weights_path)} "
                    f"({npz_tok_name!r}). The tokenizer that produced the fine-tuned "
                    f"weights' input_ids travels WITH the weights; omit --coref-model to "
                    f"use it, or pass the matching name. (R2/F1)")
            self.coref_model = npz_tok_name
            # the SSOT torch-free preprocess: spaCy en_core_web_sm + RAW sentencepiece
            # loaded from the VENDORED spm.model (the npz's `.spm` sibling the export
            # wrote — no transformers/huggingface_hub, no HF cache at runtime). The
            # sibling path has ONE definition (export_deberta_maverick.spm_sibling_path),
            # imported here so the convention cannot drift into two hand-typed paths (P1).
            from export_deberta_maverick import spm_sibling_path
            spm_path = spm_sibling_path(deberta_weights_path)
            if not os.path.isfile(spm_path):
                raise FileNotFoundError(  # FAIL LOUD (ADR-0002): the vendored tokenizer
                    f"vendored spm.model not found at {spm_path!r} (the `.spm` sibling of "
                    f"{os.path.basename(deberta_weights_path)}). Re-run "
                    f"export_deberta_maverick.py — it vendors the spm.model next to the "
                    f"weights; the daemon needs it as a local file (no HF cache at runtime).")
            self.preprocessor = StandalonePreprocessor.from_spm(spm_path)
            # FAIL LOUD (ADR-0002): prove no dependency dragged torch into this jax
            # process. The coexistence-elimination is the whole point; assert it.
            jax_only_guard.assert_torch_free()
        # cache_hit proxy: the decode jits recompile per lhs shape (variable S). A
        # shape decoded before in this process has WARM compiled graphs; the first is
        # a COLD compile. This per-process set is a documented, honest proxy for that
        # warm/cold distinction — the host run confirms its correlation with dur_ms.
        self._seen_shapes: set[tuple[int, ...]] = set()
        get_tracer().configure(process="decode_server")  # OFF until a request carries a context

    # ----------------------------------------------------------- request handler
    def handle(self, frames: list[bytes]) -> list[bytes]:
        """Map request frames -> reply frames. Pure data in/out, one doc/request."""
        # Time the meta parse explicitly: it happens BEFORE the trace context is
        # extracted (the context rides inside this very JSON), so it cannot be a span —
        # we stamp it onto the handle span as `parse_request_ms`. This is the server half
        # of the dense eos_mask [S,S] JSON cost (the client half is serialize_request).
        _t_parse = time.perf_counter()
        meta = json.loads(frames[0])
        parse_request_ms = (time.perf_counter() - _t_parse) * 1000.0
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
                "coref": self.preprocessor is not None,  # is the unified op available?
                "deberta_weights": (os.path.basename(self.deberta_weights_path)
                                    if self.deberta_weights_path else None),
            }).encode()]
        if op == "coref":
            return self._handle_coref(meta, _T)
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

        with _T.span("decode_server.handle", op=op, n_docs=len(docs_meta),
                     parse_request_ms=round(parse_request_ms, 3)):
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

    # ---------------------------------------------- the UNIFIED jax-only coref op
    def _handle_coref(self, meta: dict, _T) -> list[bytes]:
        """{texts:[...]} -> per-text CHAR-offset clusters, the WHOLE coref forward in
        this one jax-only process: torch-free preprocess (tokenize+mask) -> deberta
        encode (fine-tuned weights) -> the proven decode -> token offsets -> char
        offsets. nlp_server ships only TEXT (tiny); the dense lhs + eos_mask NEVER cross
        a wire. The decode COMPUTE stays per-document (per text), exactly like `decode`.

        Reply mirrors `decode`'s shape: clusters[i] is text i's clusters, but the spans
        are CHAR offsets [start,end] (maverick's `clusters_char_offsets` contract), since
        this daemon owns the preprocess and thus the char_offsets — nlp_server just relays.
        """
        if self.preprocessor is None:
            return [json.dumps({
                "ok": False,
                "error": "coref op unavailable: daemon was not started with "
                         "--deberta-weights (the fine-tuned deberta export)",
            }).encode()]
        texts = meta.get("texts")
        if texts is None:
            raise ValueError("coref request needs meta['texts']: a list of strings")
        singletons = bool(meta.get("singletons", False))

        clusters_per_text = []
        with _T.span("decode_server.coref", n_texts=len(texts)):
            for text in texts:
                # (a) torch-free SSOT preprocess (the SAME prepare_decode_inputs the
                #     maverick paths use; here driven by StandalonePreprocessor).
                di = prepare_decode_inputs(self.preprocessor, text)
                # (b)+(c) deberta encode -> decode, ALL on device in the jax home; the
                #     last_hidden_state never crosses a wire.
                with _T.span("decode_server.coref_doc", s=len(di.input_ids)):
                    clusters_tok = coref_host_shell.coref_document_host(
                        deberta_params=self.deberta_params,
                        deberta_cfg=self.deberta_cfg,
                        decode_params=self.params,
                        input_ids=di.input_ids,
                        attention_mask=di.attention_mask,
                        eos_mask=di.eos_mask,
                        tokens=di.tokens,
                        subtoken_map=di.subtoken_map,
                        new_token_map=di.new_token_map,
                        singletons=singletons,
                    )
                # (d) token offsets -> CHAR offsets (the shared SSOT mapper). Char offsets
                #     are INTEGERS -> JSON is bit-exact for the result.
                char_clusters = clusters_token_to_char_offsets(
                    clusters_tok, di.char_offsets) or []
                clusters_per_text.append(
                    [[[int(s), int(e)] for (s, e) in cluster] for cluster in char_clusters])
        return [json.dumps({"ok": True, "clusters": clusters_per_text,
                            "singletons": singletons}).encode()]

    def serve(self, addr: str):
        sock = zmq.Context.instance().socket(zmq.REP)
        sock.bind(addr)
        mode = ("UNIFIED encode+decode (jax-only; torch-free)"
                if self.preprocessor is not None else "decode-only")
        deberta = (f" | deberta={os.path.basename(self.deberta_weights_path)} "
                   f"({self.n_deberta_params} tensors)" if self.preprocessor else "")
        print(f"jax coref daemon [{mode}] listening on {addr} | decode-weights="
              f"{os.path.basename(self.weights_path)} ({self.n_params} tensors){deberta} | "
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
    ap.add_argument("--deberta-weights", default=None,
                    help="fine-tuned deberta encoder export (export_deberta_maverick.py). "
                         "When given, the daemon serves the UNIFIED 'coref' op (jax-only, "
                         "torch-free: text -> encode -> decode -> clusters) in addition to "
                         "'decode'. Omit for a decode-only daemon (the A/B jax-daemon path).")
    ap.add_argument("--coref-model", default=None,
                    help="OPTIONAL override of the HF tokenizer for the torch-free "
                         "preprocess. By default the daemon uses the tokenizer identity "
                         "recorded IN the --deberta-weights npz (it travels with the "
                         "weights). If given, it must AGREE with that identity or the "
                         "daemon fails loud at startup (R2/F1).")
    args = ap.parse_args()
    DecodeServer(args.weights, deberta_weights_path=args.deberta_weights,
                 coref_model=args.coref_model).serve(args.addr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
