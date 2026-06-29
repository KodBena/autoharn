#!/usr/bin/env python
"""Imperative SHELL for the maverick decode tail (ADR-0012 P9 / P7).

This is the thin, honestly-named host-side shell that wraps the pure device core
in `jax_decode.py`. Its job is the irreducibly SEQUENTIAL / DATA-DEPENDENT glue
that cannot live inside a `jax.jit`:

  * the `torch.nonzero`-shaped index extraction between dense stages
    (start selection, eos candidate-pair enumeration, span selection),
  * the host-combinatorial per-pair category-mask construction
    (maverick._get_categories_labels — set logic over surface strings),
  * the inherently-sequential cluster union-find (maverick.create_clusters),
  * the bpe -> original-token offset mapping (maverick.original_token_offsets).

NUMPY POLICY (the reason there is NO test_import_xor.py BOUNDARY_FILES entry for
this file): this shell is DELIBERATELY numpy-free. It imports `jax` only — it
pulls device results to the host with `jax.device_get(...).tolist()` and does the
union-find / category logic in plain Python, and it builds the small index/mask
arrays it feeds back into the core with `jnp.asarray`. Per the project rule
"default to pure-python in the shell unless you can name the perf reason": at
paragraph scale K (mentions) is tens, the category pass is O(K^2) trivial set
ops, and there is no measured hot path here — so numpy would buy nothing and
would force a both-host-and-device file. The one place numpy legitimately lives
is the fixture I/O boundary (capture_fixtures.py / the fidelity test), not the
composed pipeline. If a future profile shows the O(K^2) category pack dominates,
THAT is the named perf + structural reason to vectorise it with numpy — at which
point this file (a neutrally-named seam, not a device-named one) earns a
BOUNDARY_FILES entry recording exactly that justification.

DEVICE EDGE (test_device_transfers.py HOMES["jax"]): this shell is the SINGLE
home for the jax host<->device boundary. Every `jax.device_get(...)` (device->host
pull) and every `jnp.asarray(<host data>)` (host->device lift) below carries an
inline `# host-device-boundary: <reason>` marker; the device-transfer gate reds if
one of these crossings appears anywhere else, or here without the marker. The pure
core (`jax_decode.py`) has ZERO transfers — all crossings live in this one file.

FAIL LOUD (ADR-0002): structural preconditions are asserted, never silently
coerced; there is no sentinel/None-instead-of-raise path.
"""

from __future__ import annotations

import os
from typing import Optional

import jax
import jax.numpy as jnp

import jax_decode
import jax_deberta  # the pure-JAX DeBERTa-v3 encoder core (device-named, numpy-free)
from spans import get_tracer  # SSOT tracer; imports no numpy/device lib, authors no device op

# The decode tail is pinned fp32 (jax_decode.py + decode_document both contract
# float32). The single jax home owns the jax config, so the wire seam
# (coref_decode_server.py) need not import jax to set it.
jax.config.update("jax_enable_x64", False)

# Persistent XLA compilation cache. The decode jits recompile per document shape
# (variable S/K); each compiled graph is tiny (~KB), so persist them to disk to
# amortize compile time across the many runs this project will do — the first run
# compiles a shape, every later run reuses it from disk. Overridable via
# JAX_COMPILATION_CACHE_DIR (default: a gitignored dir beside this file). We drop
# the size/time thresholds so the small, fast decode graphs are actually cached
# (jax's defaults only persist compiles >1s / above a size heuristic). Best-effort:
# a missing flag on a different jax version disables the cache, never breaks the
# daemon (correctness does not depend on it; only speed).
try:
    _JAX_CACHE_DIR = os.environ.get("JAX_COMPILATION_CACHE_DIR") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".jax_cache")
    jax.config.update("jax_compilation_cache_dir", _JAX_CACHE_DIR)
    jax.config.update("jax_persistent_cache_min_compile_time_secs", 0.0)
    jax.config.update("jax_persistent_cache_min_entry_size_bytes", 0)
except Exception as e:  # the cache is a perf optimization, not correctness
    print(f"[jax] persistent compilation cache not enabled: {e!r}", flush=True)

# ---- maverick constants, inlined verbatim from maverick/common/constants.py.
# These are immutable lookup tables, not behaviour; inlining keeps the shell free
# of the torch-laden maverick package while remaining a faithful mirror.
CATEGORIES = {
    "pron-pron-comp": 0,
    "pron-pron-no-comp": 1,
    "pron-ent": 2,
    "match": 3,
    "contain": 4,
    "other": 5,
}
NUM_CATS = len(CATEGORIES) + 1  # == jax_decode.NUM_CATS == 7

PRONOUNS_GROUPS = {
    "i": 0, "me": 0, "my": 0, "mine": 0, "myself": 0,
    "you": 1, "your": 1, "yours": 1, "yourself": 1, "yourselves": 1,
    "he": 2, "him": 2, "his": 2, "himself": 2,
    "she": 3, "her": 3, "hers": 3, "herself": 3,
    "it": 4, "its": 4, "itself": 4,
    "we": 5, "us": 5, "our": 5, "ours": 5, "ourselves": 5,
    "they": 6, "them": 6, "their": 6, "themselves": 6,
    "that": 7, "this": 7,
}

STOPWORDS = {
    "'s", "a", "all", "an", "and", "at", "for", "from", "in", "into",
    "more", "of", "on", "or", "some", "the", "these", "those",
}


# --------------------------------------- mirrors maverick.common.util helpers
def get_pronoun_id(span: set) -> int:
    if len(span) == 1:
        only = next(iter(span))
        if only in PRONOUNS_GROUPS:
            return PRONOUNS_GROUPS[only]
    return -1


def get_category_id(mention, antecedent) -> int:
    span_m, pron_m = mention
    span_a, pron_a = antecedent
    if pron_m > -1 and pron_a > -1:
        if pron_m == pron_a:
            return CATEGORIES["pron-pron-comp"]
        return CATEGORIES["pron-pron-no-comp"]
    if pron_m > -1 or pron_a > -1:
        return CATEGORIES["pron-ent"]
    if span_m == span_a:
        return CATEGORIES["match"]
    union = span_m.union(span_a)
    if len(union) == max(len(span_m), len(span_a)):
        return CATEGORIES["contain"]
    return CATEGORIES["other"]


def original_token_offsets(clusters, subtoken_map, new_token_map):
    """maverick.common.util.original_token_offsets — bpe span -> original token
    span, dropping spans whose start/end map through to None (e.g. the model
    predicting <s> or a speaker name as a mention)."""
    out = []
    for cluster in clusters:
        mapped = []
        for start, end in cluster:
            sm_s = subtoken_map[start]
            sm_e = subtoken_map[end]
            if sm_s is None or sm_e is None:
                continue
            if new_token_map[sm_s] is None:
                continue
            mapped.append((new_token_map[sm_s], new_token_map[sm_e]))
        out.append(tuple(mapped))
    return out


# ----------------------------------------------- host: candidate enumeration
def _enumerate_eos_pairs(start_idxs, eos_mask):
    """mirrors model_mes.py:159-165.

    possibles_start_end_idxs = (eos_mask[start_idxs] == 1).nonzero()  row-major,
    then column 0 (a row index into start_idxs) is remapped to the real start
    token index. eos_mask is upper-triangular, so each yielded end >= its start.
    Returns two equal-length python lists (start_token_idx, end_token_idx).
    """
    p_start, p_end = [], []
    seq_len = len(eos_mask)
    for s in start_idxs:               # start_idxs ascending (nonzero order)
        row = eos_mask[s]
        for j in range(seq_len):       # ends ascending (row-major nonzero order)
            if row[j] == 1:
                p_start.append(s)
                p_end.append(j)
    return p_start, p_end


# ----------------------------------------------- host: category-mask construction
def build_categories_masks(mention_start_idxs, mention_end_idxs,
                           tokens, subtoken_map, new_token_map):
    """mirrors model_mes.py:_get_categories_labels (~277).

    Returns categories_masks as an int list-of-lists-of-lists shaped
    [NUM_CATS, K, K]; the shell hands it to the core via jnp.asarray. The last
    category (index NUM_CATS-1) is the "ALL" mask (labels != -1); categories
    0..NUM_CATS-2 are the per-category equality masks.
    """
    k = len(mention_start_idxs)
    doc_spans = []
    for start, end in zip(mention_start_idxs, mention_end_idxs):
        sub_ids = set(subtoken_map[start:end + 1]) - {None}
        token_indices = [new_token_map[idx] for idx in sub_ids]
        span = {tokens[idx].lower() for idx in token_indices if idx is not None}
        pronoun_id = get_pronoun_id(span)
        doc_spans.append((span - STOPWORDS, pronoun_id))

    # categories_labels[i][j] for j<i, else -1  (model_mes.py:287-290)
    labels = [[-1] * k for _ in range(k)]
    for i in range(k):
        for j in range(i):
            labels[i][j] = get_category_id(doc_spans[i], doc_spans[j])

    masks = []
    for cat_id in range(NUM_CATS - 1):
        masks.append([[1 if labels[i][j] == cat_id else 0 for j in range(k)]
                      for i in range(k)])
    masks.append([[1 if labels[i][j] != -1 else 0 for j in range(k)]
                  for i in range(k)])  # the "ALL" mask
    return masks


# ----------------------------------------------- host: union-find clustering
def create_clusters(m2a, singletons):
    """mirrors model_mes.py:create_clusters (~344) with add=None.

    Each mention has exactly one antecedent (argmax), and antecedents always
    precede their mention (j<i), so the greedy single-pass below builds the same
    connected components a full union-find would — and we compare cluster SETS
    (order-independent) anyway. Singletons are interleaved exactly as maverick
    does (by leading-span order); ordering is irrelevant to set-equality but we
    keep it faithful.
    """
    clusters, mention_to_cluster = [], {}
    for mention, antecedent in m2a:
        mention, antecedent = tuple(mention), tuple(antecedent)
        if antecedent in mention_to_cluster:
            ci = mention_to_cluster[antecedent]
            if mention not in clusters[ci]:
                clusters[ci].append(mention)
                mention_to_cluster[mention] = ci
        elif mention in mention_to_cluster:
            ci = mention_to_cluster[mention]
            if antecedent not in clusters[ci]:
                clusters[ci].append(antecedent)
                mention_to_cluster[antecedent] = ci
        else:
            ci = len(clusters)
            mention_to_cluster[mention] = ci
            mention_to_cluster[antecedent] = ci
            clusters.append([antecedent, mention])

    clusters = [tuple(c) for c in clusters]
    if len(singletons) != 0:
        clust = []
        clusters = list(clusters)
        singletons = list(singletons)
        while len(clusters) != 0 or len(singletons) != 0:
            if len(singletons) == 0:
                clust.append(clusters[0]); clusters = clusters[1:]
            elif len(clusters) == 0:
                clust.append((tuple(singletons[0]),)); singletons = singletons[1:]
            elif singletons[0][0] < sorted(clusters[0], key=lambda x: x[0])[0][0]:
                clust.append((tuple(singletons[0]),)); singletons = singletons[1:]
            else:
                clust.append(clusters[0]); clusters = clusters[1:]
        return clust
    return clusters


# ============================================================ the orchestrator
def decode_document(params, lhs, attention_mask, eos_mask,
                    tokens, subtoken_map, new_token_map,
                    singletons: bool = False):
    """Full decode tail for ONE document. Pure-python/jax host shell driving the
    jax_decode device core. Returns clusters as token-offset tuples, matching
    maverick `result["clusters_token_offsets"]`.

    params           : dict[str, jax.Array]  decode-tail weights (device arrays)
    lhs              : jax.Array [S, TH]      encoder last_hidden_state (batch removed)
    attention_mask   : list[int] / seq        (carried for parity; unused in mes tail)
    eos_mask         : list[list[int]] [S,S]  upper-triangular sentence-block mask
    tokens           : list[str]
    subtoken_map     : list[Optional[int]]    bpe pos -> new-token idx
    new_token_map    : list[Optional[int]]    new-token idx -> original token idx
    singletons       : emit singletons (maverick `singletons=` flag); default False
    """
    assert lhs.ndim == 2, f"lhs must be [S, TH], got {lhs.shape}"
    seq_len = lhs.shape[0]
    assert len(eos_mask) == seq_len, "eos_mask must be [S, S] aligned to lhs"
    # float32 is an INVARIANT of the decode tail (matches torch fp32; the fidelity
    # test pins x64-off). Assert it at the boundary so a float64 lhs (e.g. if x64
    # got enabled process-wide once this is wired into nlp_server.py) fails LOUD
    # here instead of silently widening every matmul. (review watch-item)
    assert lhs.dtype == jnp.float32, f"lhs must be float32, got {lhs.dtype}"

    _T = get_tracer()  # records spans only when the decode_server adopted a trace context

    # ---- STAGE 1 (device): start keep-mask ; (host): nonzero -> start indices
    with _T.span("host_shell.stage1_start_keep", seq_len=seq_len):
        start_keep = jax.device_get(  # host-device-boundary: pull start keep-mask device->host
            jax_decode.mention_start_keep(params, lhs)).tolist()
    start_idxs = [i for i, keep in enumerate(start_keep) if keep]

    if len(start_idxs) == 0:
        return []

    # ---- (host): eos candidate (start,end) pairs
    p_start, p_end = _enumerate_eos_pairs(start_idxs, eos_mask)
    if len(p_start) == 0:
        return []

    # ---- STAGE 2 (device): span keep-mask ; (host): select mention pairs
    with _T.span("host_shell.stage2_span_keep", n_pairs=len(p_start)):
        span_keep = jax.device_get(  # host-device-boundary: pull span keep-mask device->host
            jax_decode.span_mention_keep(
                params, lhs,
                jnp.asarray(p_start),  # host-device-boundary: lift candidate start idxs
                jnp.asarray(p_end),    # host-device-boundary: lift candidate end idxs
            )
        ).tolist()
    mention_start_idxs = [p_start[i] for i, keep in enumerate(span_keep) if keep]
    mention_end_idxs = [p_end[i] for i, keep in enumerate(span_keep) if keep]

    k = len(mention_start_idxs)
    if k == 0:
        return []  # mes_span_clustering early-returns [] on zero mentions

    # ---- (host): category masks (O(K^2) set logic — a genuinely-long python op)
    with _T.span("host_shell.build_categories_masks", k=k):
        masks = build_categories_masks(
            mention_start_idxs, mention_end_idxs, tokens, subtoken_map, new_token_map
        )
    # ---- gather per-mention start/end reps on device
    with _T.span("host_shell.gather_reps", k=k):
        start_reps = lhs[jnp.asarray(mention_start_idxs)]  # host-device-boundary: lift start idxs [K,TH]
        end_reps = lhs[jnp.asarray(mention_end_idxs)]      # host-device-boundary: lift end idxs [K,TH]

    # ---- STAGE 3 (device): coref logits + no_ant + argmax antecedent decode
    with _T.span("host_shell.stage3_coref_decode", k=k):
        max_ant = jax.device_get(  # host-device-boundary: pull argmax antecedents device->host
            jax_decode.coref_decode(
                params, start_reps, end_reps,
                jnp.asarray(masks, dtype=jnp.float32),  # host-device-boundary: lift category masks
            )
        ).tolist()

    # ---- (host): mention->antecedent edges + singletons (BUG-FIXED) + union-find
    span_indices = list(zip(mention_start_idxs, mention_end_idxs))
    m2a = []
    antecedent_set = set()
    for i in range(k):
        a = max_ant[i]
        if a < k:                       # has a real antecedent (column j<i)
            m2a.append((span_indices[i], span_indices[a]))
            antecedent_set.add(a)

    sing_spans = []
    if singletons:
        # model_mes.py:324-327. non_mentions = argmax hit the no_ant column.
        # setdiff1d(non_mentions, antecedent_indices) sorts+uniques. The maverick
        # line `np.zeros_like(len(...))` produces a SCALAR 0 used as the (always-0)
        # batch index — harmless at B=1 but a latent trap. We compute the CORRECT
        # singleton spans directly: each singleton's own (start,end).
        non_mentions = [i for i in range(k) if max_ant[i] == k]
        singleton_idxs = sorted(set(non_mentions) - antecedent_set)
        sing_spans = [span_indices[s] for s in singleton_idxs]

    # ---- (host): sequential cluster union-find (a genuinely-long python op)
    with _T.span("host_shell.union_find", k=k, n_edges=len(m2a)):
        clusters_bpe = create_clusters(m2a, sing_spans)
    return original_token_offsets(clusters_bpe, subtoken_map, new_token_map)


# ------------------------------------ wire/host entry points (the single jax home)
# coref_decode_server.py (the ZMQ wire seam) delegates ALL its device lifts here so
# it can stay host-only — single-homing the jax host<->device edge (mandate).
def lift_params(host_params):
    """Lift the decode-tail weights (host arrays) onto the device — the one place
    the weights cross host->device."""
    return {k: jnp.asarray(v, dtype=jnp.float32)  # host-device-boundary: lift decode-tail weights host->device
            for k, v in host_params.items()}


def decode_document_host(params, lhs_host, attention_mask, eos_mask,
                         tokens, subtoken_map, new_token_map, singletons: bool = False):
    """Wire entry point: lift the host last_hidden_state onto the device HERE, then
    run the (untouched) decode. Keeps coref_decode_server.py free of any jax op."""
    with get_tracer().span("host_shell.lift_lhs", s=len(lhs_host)):
        lhs = jnp.asarray(lhs_host, dtype=jnp.float32)  # host-device-boundary: lift wire last_hidden_state host->device
    return decode_document(params, lhs, attention_mask, eos_mask,
                           tokens, subtoken_map, new_token_map, singletons)


# ============================== the UNIFIED encode+decode (the architectural prize)
# The unified daemon runs the WHOLE coref forward in ONE jax-only process. The encode
# is the SECOND device op (after the decode), so it joins the decode in THIS single jax
# home — there is no separate "jax encode home". The deberta last_hidden_state is
# produced on the device and fed straight into the decode WITHOUT crossing a wire (the
# whole point: the dense lhs + eos_mask never serialise). nlp_server's torch encode is
# off the path entirely for the jax-unified backend.
def lift_deberta_params(host_params):
    """Lift the FINE-TUNED deberta encoder weights (host arrays from the exported
    fixtures/deberta_maverick.npz) onto the device — the one place these weights cross
    host->device, mirroring `lift_params` for the decode tail. The daemon does the
    numpy `np.load` (host) and hands the host dict here; the lift is the jax home's."""
    return {k: jnp.asarray(v, dtype=jnp.float32)  # host-device-boundary: lift deberta encoder weights host->device
            for k, v in host_params.items()}


def validate_deberta_load(host_params: dict, cfg: "jax_deberta.DebertaCfg") -> None:
    """CONSTRUCTION-TIME keyset bijection on the npz the daemon ACTUALLY loads (R3/F1).

    The export asserted `set(converted) == jax_deberta.param_keys(cfg)`, but that ran on
    the host at export time — the daemon loads a frozen npz that could be stale, truncated,
    or built by mismatched code. The deberta weights are a STARTUP artifact, so per ADR-0002's
    loudness hierarchy (construction-time raise > per-request exception, ADR-0012 P5) this
    bijection must be RE-ASSERTED here, at daemon construction, BEFORE serving:

      * a DROPPED tensor would otherwise surface only as a per-request `KeyError` deep inside
        `jax_deberta.encode` (the daemon would serve `{ok:false}` forever, never fail at start);
      * an EXTRA/unread tensor would load SILENTLY — exactly the "converted-but-unread → silent
        wrong forward" class param_keys exists to kill — reintroduced at load.

    Lives in the jax home (not the host-only daemon file) because it needs the device core's
    read-set `jax_deberta.param_keys(cfg)`; this keeps coref_decode_server.py jax-free
    (import-XOR) while restoring the bijection guard on the loaded artifact. Set-equality is
    EXHAUSTIVE (both directions) — the same SSOT the export reconciles against."""
    expected = jax_deberta.param_keys(cfg)
    got = set(host_params)
    if got != expected:
        missing = sorted(expected - got)
        extra = sorted(got - expected)
        raise ValueError(
            "deberta npz keyset != jax_deberta.param_keys(cfg) — the loaded encoder "
            "weights do not bijectively match the forward's read-set, so the encode would "
            "be silently wrong (dropped weight) or carry unread tensors (wrong export). "
            f"missing {len(missing)}: {missing[:8]}{'…' if len(missing) > 8 else ''} | "
            f"extra {len(extra)}: {extra[:8]}{'…' if len(extra) > 8 else ''}. "
            "Re-export with export_deberta_maverick.py against the matching code/config.")


def build_deberta_cfg(cfg_fields: dict) -> "jax_deberta.DebertaCfg":
    """Reconstruct the jit-static DebertaCfg from the plain python scalars the daemon
    read out of the npz (the `__cfg__*` entries). DebertaCfg lives in the device-named
    jax_deberta module, so it is built HERE (the jax home), never in the host-only wire
    seam — keeping the daemon file free of any jax import. The scalar set is the SSOT
    the export wrote from `deberta_weights.cfg_from_hf`; we cast each to its declared
    python type so the NamedTuple stays hashable (jit-static)."""
    return jax_deberta.DebertaCfg(
        num_layers=int(cfg_fields["num_layers"]),
        num_heads=int(cfg_fields["num_heads"]),
        head_size=int(cfg_fields["head_size"]),
        position_buckets=int(cfg_fields["position_buckets"]),
        max_relative_positions=int(cfg_fields["max_relative_positions"]),
        pos_ebd_size=int(cfg_fields["pos_ebd_size"]),
        scale_factor=int(cfg_fields["scale_factor"]),
        has_c2p=bool(cfg_fields["has_c2p"]),
        has_p2c=bool(cfg_fields["has_p2c"]),
        layer_norm_eps=float(cfg_fields["layer_norm_eps"]),
    )


def coref_document_host(deberta_params, deberta_cfg, decode_params,
                        input_ids, attention_mask, eos_mask,
                        tokens, subtoken_map, new_token_map, singletons: bool = False):
    """ONE document, the full jax-only coref forward: tokenised inputs -> deberta
    encode (fine-tuned weights) -> the proven decode tail -> cluster token offsets.

    The encode's `last_hidden_state` stays a DEVICE array and is fed straight into
    `decode_document` — it NEVER crosses a wire, the architectural win over the
    jax-daemon backend (whose ~67ms cost was shipping the dense lhs + eos_mask as JSON).
    `input_ids`/`attention_mask` are the only new host->device crossings (lists from the
    torch-free preprocess), lifted here in the single jax home with a batch axis for the
    encoder's [B,S] contract; the encoder output's batch axis is dropped for the decode's
    [S,TH] contract. The decode is the EXISTING `decode_document`, untouched."""
    _T = get_tracer()
    with _T.span("host_shell.coref_encode", s=len(input_ids)):
        ids = jnp.asarray([input_ids])             # host-device-boundary: lift coref input_ids host->device [1,S]
        mask = jnp.asarray([attention_mask])       # host-device-boundary: lift coref attention_mask host->device [1,S]
        lhs = jax_deberta.encode(deberta_params, ids, mask, deberta_cfg)[0]  # [S, TH] device, fp32
    return decode_document(decode_params, lhs, attention_mask, eos_mask,
                           tokens, subtoken_map, new_token_map, singletons)
