#!/usr/bin/env python
"""SSOT for the bounded SHAPE-BUCKET ladders and the masked-padding primitive
(ADR-0000 the-bounded-bucket-set / ADR-0012 P1 single-source-of-truth).

WHY THIS FILE EXISTS — the unbounded-distinct-shape class, made unrepresentable.
The unified jax-only coref daemon retained one compiled XLA executable per distinct
input shape, forever (JAX caches per shape). The shapes were UN-bucketed: the encode
compiled per raw sequence length S (~200 paragraph lengths -> ~200 large 24-layer
DeBERTa executables, >7GB host RAM -> OOM-kill), and the decode jits compiled per
data-dependent S/K/P (nearly unique per request -> a perpetual compile tail). This is
ADR-0000 Specimen 3/4 in the JAX-cache register: the "how do I fix it" reflex caps a
cache by count; the TYPE answer makes the unbounded-distinct-shape class
unrepresentable by drawing every traced shape from a FIXED, FINITE ladder. After
bucketing, the number of distinct compiles is bounded by the ladder size, not by the
request count (the ADR-0009 MEASURED gate: test_shape_bucket_compile_bound.py).

ONE HOME (P1, the audit's cancer B / "two writers of one truth"). `pad_to` is THE
single LIST padder (token-id lists): the batched torch encode (nlp_server._encode_docs),
the per-text jax encode/decode AND the bucket-group batched jax encode (coref_host_shell)
ALL call it — there is no hand-rolled second `list + [pad]*(n)` anywhere. The jax decode
ALSO right-pads device ARRAYS (lhs/reps/masks) with `jnp.pad` (coref_host_shell) — a
distinct mechanism because `pad_to` is a python-list padder and those are 2-D/3-D device
arrays — but it is NOT a second author of the ladder truth: every `jnp.pad` target length
is `bucket_len`'s output, so the ladder (the truth) still has exactly one home.
`bucket_len` is THE single length->bucket map.

TWO BOUNDED-SET LADDERS, TWO DISTINCT CONCERNS, ONE HOME (this file). `bucket_len` over
`ENCODE_LEN_BUCKETS` rounds ONE sequence's length S to bound the per-SHAPE COMPILE set
(the JAX cache-leak concern). `chunk_by_vram` (relocated HERE from nlp_server so the OOM
bound has ONE home — both the torch batcher and the jax batcher import it, never copy it)
groups multiple docs into OOM-bounded CHUNKS, bounding the QUADRATIC-DOMINATED activation
PEAK of one batched forward IN BYTES against the free device arena (the memory concern) —
NOT a linear token proxy (see `peak_variable_bytes` for why the proxy was blind to the OOM).
`encode_batch_chunks` + `ENCODE_BATCH_BUCKETS` round the BATCH axis B to a finite ladder
rung (the SAME ADR-0000 move applied to B: a bucket-group batched encode that compiled per
VARIABLE group size would re-leak the cache `bucket_len` just bounded, so B is drawn from a
fixed ladder -> the (B, s_bucket) compile grid is bounded, not O(requests)). Chunking groups
docs; length-laddering rounds a length; batch-laddering rounds the batch count. Three
orthogonal operations, each its own function, kept on single-ownership grounds (P3) — but the
OOM inequality itself (`peak_variable_bytes(B, max_S) <= available`) is authored exactly ONCE
(`peak_variable_bytes`): `chunk_by_vram` (variable lengths, torch) and `max_batch_for_length`
-> `encode_batch_chunks` (uniform s_bucket, jax B-ladder) BOTH consume that one inequality;
neither re-derives it. There is NO second budget.

MASKED-PADDING IS INERT (the contract this rests on, already proven). Padding a
sequence up to a bucket and extending the attention_mask with zeros leaves every REAL
position's encoder output bit-identical to the unpadded forward (the batched encode
proved this: nlp_server._encode_docs slices each doc's unpadded [S_i,TH] out of a
padded chunk and test_batched_encode_and_multidoc_wire asserts cluster-set identity;
test_shape_bucket_compile_bound re-proves bucketed-then-sliced == unpadded directly).
The encoder masks padding two ways (jax_deberta: `emb = emb * mask` zeros padded
embeddings, and `_get_attention_mask` -> masked_fill zeros padded attention columns),
so the pad VALUE is irrelevant to real outputs; it need only be a valid index.

FRAMEWORK-FREE: pure python (no numpy, no jax, no torch). Importable by the jax-only
device files (coref_host_shell — the import-XOR gate forbids numpy there) AND the
torch host (nlp_server) AND the host-only wire seam, so the one home is reachable from
every site without dragging a framework in. FAIL LOUD (ADR-0002): an over-ceiling
length raises, never silently falls back to an unbucketed (cache-leaking) shape.
"""

from __future__ import annotations

import os
from typing import NamedTuple


def _ladder_from_env(name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    """A ladder is operator-tunable (per card / corpus) but ALWAYS a finite, sorted,
    strictly-increasing tuple — the bounded-set invariant ADR-0000 rests on. Parse a
    comma-list override and FAIL LOUD on a malformed one rather than silently keeping a
    shape unbucketed."""
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        vals = tuple(int(x) for x in raw.split(",") if x.strip())
    except ValueError as e:
        raise ValueError(f"{name} must be a comma-list of ints, got {raw!r}: {e}") from e
    if not vals or list(vals) != sorted(vals) or len(set(vals)) != len(vals) or vals[0] <= 0:
        raise ValueError(
            f"{name}={raw!r} must be a non-empty, strictly-increasing, positive ladder")
    return vals


# ENCODE / decode SEQUENCE-LENGTH ladder (S). Powers of two cap worst-case padding
# waste below 2x (a length just over a rung rounds to the next ~2x rung) with only a
# handful of rungs, so the 24-layer DeBERTa executable count — the >7GB bulk — is
# bounded by SIX large executables instead of ~200. Ceiling 2048: the preprocess works
# at PARAGRAPH granularity (nltk sentence-split), so a single >2048-bpe-token paragraph
# is pathological; per ADR-0002 it FAILS LOUD here rather than minting an unbounded
# giant compile. Tunable via COREF_LEN_BUCKETS for a different corpus/card.
ENCODE_LEN_BUCKETS: tuple[int, ...] = _ladder_from_env(
    "COREF_LEN_BUCKETS", (64, 128, 256, 512, 1024, 2048))

# DECODE per-mention (K) and per-candidate-pair (P) ladders — the perpetual tail. K
# (kept mentions) is tens at paragraph scale; P (eos candidate (start,end) pairs) is
# larger. Both finite -> the per-K and per-(S,P) decode-jit compile sets are bounded.
DECODE_K_BUCKETS: tuple[int, ...] = _ladder_from_env(
    "COREF_K_BUCKETS", (16, 32, 64, 128, 256, 512))
DECODE_P_BUCKETS: tuple[int, ...] = _ladder_from_env(
    "COREF_P_BUCKETS", (32, 64, 128, 256, 512, 1024, 2048, 4096))

# The pad token id for the encoder. Masked-inert (see module docstring) so the VALUE is
# irrelevant to real outputs — it need only be a valid word-embedding row index; 0 is
# valid for every vocab and is deberta-v3's pad id. The torch batched encode passes its
# tokenizer's own pad_token_id to pad_to; the jax encode uses this (the lhs is
# mask-zeroed regardless, so the two agree on every real position).
ENCODE_PAD_ID: int = 0


def bucket_len(n: int, ladder: tuple[int, ...]) -> int:
    """The smallest ladder rung >= n (the bounded-set map that makes the
    unbounded-distinct-shape class unrepresentable — ADR-0000). FAIL LOUD (ADR-0002) if
    n exceeds the ceiling: that is a real, diagnosable condition (a pathologically long
    input), never a silent fall-through to an unbucketed shape."""
    if n < 0:
        raise ValueError(f"bucket_len: negative length {n}")
    for b in ladder:
        if n <= b:
            return b
    raise ValueError(
        f"bucket_len: length {n} exceeds the ladder ceiling {ladder[-1]} "
        f"(ladder={ladder}). Inputs are expected at paragraph granularity; a longer "
        f"unit should be split upstream. Raise the ceiling deliberately if this is real.")


def pad_to(seq, target: int, pad_value: int) -> list[int]:
    """THE single masked-padding primitive (P1): right-pad `seq` to length `target` with
    `pad_value`. Used by BOTH the torch batched encode (pad to chunk-max) and the jax
    encode/decode (pad to a ladder bucket). FAIL LOUD if `seq` is already longer than
    `target` (a caller bug — the bucket must be >= the real length)."""
    seq = list(seq)
    if len(seq) > target:
        raise ValueError(f"pad_to: seq length {len(seq)} exceeds target {target}")
    return seq + [pad_value] * (target - len(seq))


# ============================================================ the ONE OOM bound
# A CONSERVATIVE MEMORY MODEL of the forward's variable peak + a chunker that PROVABLY keeps
# every chunk within the free device arena. Relocated HERE from nlp_server (the jax
# bucket-group batcher needs the SAME bound — do-not-copy mandate -> this SSOT home; both
# nlp_server and coref_host_shell import it).
#
# WHY THIS REPLACED A LINEAR TOKEN BUDGET (ADR-0000: foreclose the OOM CLASS, not an
# instance). The previous bound capped the LINEAR padded footprint B*max_S against a GUESSED
# constant (8192 "padded tokens"). But a batched deberta-v3 encode's peak is DOMINATED by the
# QUADRATIC disentangled-attention scores [B, num_heads, S, S] (plus the c2p/p2c position
# terms, all O(B*num_heads*S^2)). A chunk with a large max_S and B>1 blew past the ~30%-arena
# while SATISFYING the linear budget -> jax RESOURCE_EXHAUSTED. A linear bound CANNOT see a
# quadratic peak, so it could only ever fix the instance that happened to fail, never the
# class. The TYPE answer (ADR-0000 Specimen 3 — the byte-budgeted high-water-mark): derive the
# bound from what ACTUALLY exhausts memory — a CONSERVATIVE upper-bound memory model of the
# forward's variable (activation) peak IN BYTES — and chunk so EVERY chunk provably fits the
# free arena. Over-estimation is SAFE (smaller, slower chunks); the invariant forbids only
# UNDER-estimation (an OOM). The never-OOM property is unit-tested in test_oom_invariant.py
# and FAILS on the old linear chunker (which packs a quadratic over-budget chunk).
ENCODE_MAX_DOCS: int = int(os.environ.get("COREF_ENCODE_MAX_DOCS", "64"))


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    """An operator-tunable positive int (fail-loud on malformed/too-small), mirroring
    `_ladder_from_env` for the scalar memory-model knobs."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        v = int(raw)
    except ValueError as e:
        raise ValueError(f"{name} must be an int, got {raw!r}: {e}") from e
    if v < minimum:
        raise ValueError(f"{name}={v} must be >= {minimum}")
    return v


# CONSERVATIVE co-residency multiples for the memory model (operator-tunable per ADR-0009
# once a host profile tightens them; the DEFAULTS are reasoned UPPER bounds — see
# `peak_variable_bytes`). Each must be >= 1; a larger value only makes chunks SMALLER/safer.
_K_QUAD: int = _int_env("COREF_MEM_K_QUAD", 8)       # co-resident [B,H,S,S] score buffers
_K_DISENT: int = _int_env("COREF_MEM_K_DISENT", 4)   # co-resident [B*H,S,2*span] pos buffers
_A_HIDDEN: int = _int_env("COREF_MEM_A_HIDDEN", 8)   # co-resident [B,S,hidden] activations
_A_INTER: int = _int_env("COREF_MEM_A_INTER", 3)     # co-resident [B,S,intermediate] FFN bufs
_BYTES_PER_ELEM: int = 4                             # fp32 throughout (the encode is pinned fp32)

# Headroom carved off the arena before the budget: a fraction (allocator fragmentation, XLA
# scratch, the per-doc decode tail's transient) with a fixed floor. Conservative; tunable.
_VRAM_HEADROOM_FRAC: float = float(os.environ.get("COREF_VRAM_HEADROOM_FRAC", "0.15"))
_VRAM_HEADROOM_FLOOR: int = _int_env(
    "COREF_VRAM_HEADROOM_FLOOR_BYTES", 256 << 20, minimum=0)  # 256 MiB


def headroom_bytes(arena_or_total: int) -> int:
    """The ONE headroom rule (P1): the bytes reserved off an arena/total before the activation
    budget. Used by BOTH framework derivations (jax memory_stats in coref_host_shell, torch
    mem_get_info in nlp_server) so the safety margin has one home, not two."""
    return max(int(arena_or_total * _VRAM_HEADROOM_FRAC), _VRAM_HEADROOM_FLOOR)


def cpu_fallback_available_bytes() -> int:
    """The available-bytes fallback for a NON-GPU run (no device arena to exhaust): an
    operator-overridable generous default so a CPU daemon still CHUNKS rather than packing a
    whole book into one forward. ONE home (P1) for BOTH framework derivations' CPU branch
    (jax in coref_host_shell, torch in nlp_server) — the env name + the default literal are not
    re-typed at each site (the very two-writers-of-one-literal shape this file's bound replaced,
    kept from re-forming here at small scale)."""
    return _int_env("COREF_AVAILABLE_VRAM_BYTES", 8 << 30)


class MemModel(NamedTuple):
    """The architecture-derived inputs to the forward's memory model — a CONSERVATIVE upper
    bound on the VARIABLE (non-weight) peak of ONE batched deberta-v3 encode at (B, S).
    Framework-free (plain ints): the caller DERIVES every field from the SSOT (DebertaCfg +
    the ACTUAL weight shapes), so nothing here is hand-guessed (P1). The `k_*`/`a_*`
    co-residency multiples are CONSERVATIVE over-estimates (reasoned upper bounds; ADR-0009-
    tunable), captured on the model so a test can pin them and so a DocTooLargeError can quote
    them."""
    num_heads: int
    hidden: int          # num_heads * head_size (the model's hidden width)
    intermediate: int    # FFN inner width (intermediate.dense out-features) — derived from weights
    pos_ebd_size: int    # att_span; the disentangled position tables are width 2*pos_ebd_size
    bytes_per_elem: int = _BYTES_PER_ELEM
    k_quad: int = _K_QUAD
    k_disent: int = _K_DISENT
    a_hidden: int = _A_HIDDEN
    a_inter: int = _A_INTER


# The DENSE deberta-v2/v3 FFN expansion ratio (intermediate_size / hidden_size). The whole
# deberta-v2 family fixes this 4x block — v3-large is exactly 4x (hidden 1024 -> intermediate
# 4096). The WEIGHT-derived path (coref_host_shell.mem_model_from) reads the EXACT intermediate
# off the loaded FFN weight and NEVER consults this ratio; this constant feeds ONLY the
# CFG-ONLY path (`dense_deberta_mem_model` below) — when a caller holds a DebertaCfg but NOT the
# weights (the nla_lab EncodeVariant.est_peak_device_bytes contract), so `intermediate` cannot be
# read off a weight. A CONSERVATIVE upper bound for the dense profile: over-estimating the FFN
# width only inflates the byte bound (smaller/safer chunks; the invariant forbids only
# UNDER-estimation). Operator-tunable (raise it for a wider-than-4x FFN).
_DENSE_FFN_RATIO: int = _int_env("COREF_DENSE_FFN_RATIO", 4)


def dense_deberta_mem_model(num_heads: int, head_size: int, pos_ebd_size: int) -> MemModel:
    """The dense deberta-v2/v3 MemModel derived from ARCHITECTURE FIELDS ALONE (num_heads,
    head_size, pos_ebd_size) — the CFG-ONLY twin of `coref_host_shell.mem_model_from`, which
    derives the EXACT FFN inner width off the loaded `intermediate.dense` weight. SAME single
    memory model (this builds a `MemModel`, consumed by `peak_variable_bytes`) — NOT a second
    one (P1): only the SOURCE of `intermediate` differs. When the weights are in hand, use
    `mem_model_from` (exact). When ONLY a DebertaCfg is known (no params — the nla_lab
    `EncodeVariant.est_peak_device_bytes` contract, which is host-XOR-device neutral and never
    touches device arrays), the FFN inner width is the canonical dense ratio `_DENSE_FFN_RATIO *
    hidden` — a CONSERVATIVE upper bound for the dense profile (v3-large is exactly 4x). The
    conservative k_*/a_* co-residency multiples stay the MemModel defaults (one home), exactly
    as `mem_model_from`."""
    hidden = num_heads * head_size
    return MemModel(
        num_heads=num_heads,
        hidden=hidden,
        intermediate=_DENSE_FFN_RATIO * hidden,
        pos_ebd_size=pos_ebd_size,
    )


def peak_variable_bytes(mm: MemModel, B: int, S: int) -> int:
    """A CONSERVATIVE UPPER BOUND, in bytes, on the VARIABLE (non-weight) peak of one batched
    deberta-v3 encoder forward at batch B, padded length S. THE single author of the OOM
    inequality `peak <= available` (P1): the variable-length chunker (`chunk_by_vram`, torch)
    and the uniform-length B cap (`max_batch_for_length` -> `encode_batch_chunks`, jax) BOTH
    consume it; neither re-derives it.

    WHY IT IS AN UPPER BOUND (reasoned — only the host run profiles the exact constants, but
    the FORM and the co-residency counts are over-estimates by construction; ADR-0009):

      * QUADRATIC term — the dominant one, and the one the old linear budget was blind to.
        Disentangled self-attention (jax_deberta._self_attention + _disentangled_bias)
        materialises several [B, num_heads, S, S] float32 tensors that are LIVE within one
        layer: the content->content scores (matmul q·kᵀ), the c2p scores (post take_along_axis),
        the p2c scores (post take_along_axis AND its transpose), the score accumulator, the
        masked-fill, and the softmax probs — ~6-8 distinct [B,H,S,S] buffers. `k_quad`
        (default 8) is a conservative count of how many XLA may hold co-resident. Only ONE
        layer's attention is live at a time (layers run sequentially; each layer's S^2 buffers
        free before the next), so this is NOT multiplied by num_layers.
      * DISENTANGLED-POSITION term — before the gather, c2p/p2c hold [B*H, S, 2*pos_ebd_size]
        intermediates; `k_disent` (default 4) bounds those.
      * LINEAR term — per-(b,s) activations: embeddings, q/k/v, context, the residual stream
        ([B,S,hidden], `a_hidden` of them) and the FFN expansion ([B,S,intermediate],
        `a_inter` of them; intermediate ~= 4*hidden for v3-large).

    Every term is LINEAR in B (a batched matmul/elementwise scales the batch axis exactly), so
    peak_variable_bytes(mm, B, S) == B * peak_variable_bytes(mm, 1, S) EXACTLY — the property
    `max_batch_for_length` relies on to solve for B in O(1) (proven in test_oom_invariant)."""
    H = mm.num_heads
    quad = mm.k_quad * B * H * S * S
    disent = mm.k_disent * B * H * S * (2 * mm.pos_ebd_size)
    lin = B * S * (mm.a_hidden * mm.hidden + mm.a_inter * mm.intermediate)
    return (quad + disent + lin) * mm.bytes_per_elem


def max_batch_for_length(mm: MemModel, S: int, available_bytes: int) -> int:
    """The largest batch B whose forward at padded length S provably fits `available_bytes`
    (the ONE inequality `peak_variable_bytes(B, S) <= available`, solved for B). Since the peak
    is exactly linear in B, this is `available // peak_variable_bytes(1, S)`. Returns 0 when
    even B=1 overflows — the single-doc-too-big condition the caller must handle LOUDLY (a
    bounded DocTooLargeError), NEVER a raw RESOURCE_EXHAUSTED."""
    per_row = peak_variable_bytes(mm, 1, S)
    if per_row <= 0:
        raise ValueError(f"degenerate memory model: per-row peak {per_row} bytes at S={S}")
    return available_bytes // per_row


class DocTooLargeError(RuntimeError):
    """A single document does not fit the device arena even alone (B=1). Raised with a CLEAR,
    BOUNDED diagnosis (tokens, GiB needed, GiB free, the exact knob) INSTEAD of letting XLA
    raise a raw RESOURCE_EXHAUSTED (ADR-0002 fail-loud at the strongest surface; ADR-0000 — the
    OOM class is foreclosed: an unfittable input is a NAMED, actionable condition, not a crash,
    and not a silently dropped doc)."""

    def __init__(self, seq_len: int, needed_bytes: int, available_bytes: int, mm: MemModel):
        self.seq_len = seq_len
        self.needed_bytes = needed_bytes
        self.available_bytes = available_bytes
        gib = float(1 << 30)
        super().__init__(
            f"single document of {seq_len} padded tokens needs ~{needed_bytes / gib:.2f} GiB "
            f"for one deberta forward at B=1, but only ~{available_bytes / gib:.2f} GiB of "
            f"device arena is free (after weights + headroom). This is a hard hardware limit, "
            f"not a defect: raise XLA_PYTHON_CLIENT_MEM_FRACTION (the daemon's --mem-fraction), "
            f"split the paragraph upstream so each unit is shorter, or run on a larger card. "
            f"(conservative model: k_quad={mm.k_quad}, k_disent={mm.k_disent}, "
            f"a_hidden={mm.a_hidden}, a_inter={mm.a_inter}.)")


# =============================================== the RETAINED-OUTPUT co-residency (FINDING 1)
# THE SECOND OOM class the per-FORWARD budget alone does not cover (ADR-0000 — one level up
# from the quadratic-forward fix). The batched encode hands each doc back an UNPADDED
# [S_i, hidden] fp32 lhs slice, and a consumer that decodes only AFTER encoding every doc
# keeps ALL of them co-resident on the SAME arena the next forward competes for. The forward
# budget proves `forward_peak(chunk) <= available`, but the TRUE co-resident high-water mark is
# `forward_peak(chunk) + Σ(retained slices still live)`. That Σ is O(total docs): a book's
# worth of slices (thousands of paragraphs * S * hidden * 4B) can be MULTIPLE GiB — far past
# the flat headroom — so a later, individually-in-budget forward raw-OOMs. The invariant: at
# the instant ANY forward runs, the arena must hold that forward PLUS every slice still retained.
#
# TWO forced tactics for ONE invariant (the two consumers have different decode structures):
#   * jax (coref_documents_host): decode is IN-PROCESS and interleavable -> STREAM
#     decode-after-encode, freeing each lhs once its (host-side) clusters are produced, so
#     co-resident retained never exceeds ONE chunk and the per-forward budget stays sufficient.
#     This is the capacity-preserving general fix (the full book still processes).
#   * torch (nlp_server._encode_docs): decode is maverick's per-item predict() served by a
#     stand-in that holds ALL slices by construction (the reference path's bit-faithfulness),
#     so it RESERVES the full retained sum up front (forward_budget_after_retained) — never a
#     raw OOM, a bounded RetainedTooLargeError instead, pointing at the streaming jax path.
def retained_lhs_bytes(mm: MemModel, lengths) -> int:
    """Total device bytes the batched encode RETAINS co-resident when EVERY doc's lhs is held
    at once (decode-after-encode-all): each doc's UNPADDED [S_i, hidden] fp32 last-hidden-state
    slice. This is the O(total docs) accumulation term the per-forward budget omits — exact for
    the unpadded slice (S_i * hidden elements, fp32), derived from the SAME MemModel (no second
    literal)."""
    return sum(int(s) for s in lengths) * mm.hidden * mm.bytes_per_elem


class RetainedTooLargeError(RuntimeError):
    """The batched encode's RETAINED lhs slices (every doc's [S_i, hidden] held co-resident
    until decode drains them) do not leave room in the arena for even one forward — an
    O(total docs) ACCUMULATION across the call, NOT a single oversized doc (that is
    DocTooLargeError). Raised LOUD and BOUNDED (ADR-0000/ADR-0002) on the path that retains all
    slices, INSTEAD of letting a later in-budget forward hit a raw RESOURCE_EXHAUSTED. The
    remediation is concrete: use the streaming jax-unified path (which frees each slice after
    its decode and processes an unbounded corpus), send fewer docs per request, raise
    --mem-fraction, shorten the docs, or use a larger card."""

    def __init__(self, n_docs: int, retained_bytes: int, available_bytes: int):
        self.n_docs = n_docs
        self.retained_bytes = retained_bytes
        self.available_bytes = available_bytes
        gib = float(1 << 30)
        super().__init__(
            f"{n_docs} documents retain ~{retained_bytes / gib:.2f} GiB of [S_i, hidden] encode "
            f"slices co-resident (held until decode), but only ~{available_bytes / gib:.2f} GiB "
            f"of device arena is free (after weights + headroom) — leaving no room for even one "
            f"forward. This is the retained-output accumulation OOM class, not a single huge doc: "
            f"use the STREAMING jax-unified coref path (frees each slice after its decode, so an "
            f"unbounded corpus fits), send fewer documents per request, raise "
            f"XLA_PYTHON_CLIENT_MEM_FRACTION (--mem-fraction), shorten the documents, or run on a "
            f"larger card.")


def forward_budget_after_retained(available_bytes: int, mm: MemModel, lengths) -> int:
    """The arena left for ANY ONE forward's variable peak after RESERVING every doc's retained
    lhs slice (`retained_lhs_bytes`) — the budget the chunker must use on a path that holds ALL
    slices co-resident (the torch reference path). Reserving the FULL retained sum UP FRONT,
    before chunking, conservatively foreclosees the retained-accumulation OOM class: the chunker
    that consumes this reduced budget can never schedule a forward that, together with the slices
    already on-arena, exceeds `available_bytes`. It over-reserves by the current chunk's own
    not-yet-produced slice (the forward runs before its outputs materialise) — SAFE; the
    invariant forbids only UNDER-estimation. If the retained set alone leaves no room for a
    forward, raises RetainedTooLargeError (loud, bounded) rather than handing the chunker a
    non-positive budget that would mis-report as a per-doc DocTooLargeError."""
    lengths = list(lengths)  # materialise once (a generator would be drained by retained_lhs_bytes)
    retained = retained_lhs_bytes(mm, lengths)
    reserved = available_bytes - retained
    if reserved <= 0:
        raise RetainedTooLargeError(len(lengths), retained, available_bytes)
    return reserved


def chunk_by_vram(lengths, mm: MemModel, available_bytes: int, max_docs: int):
    """Greedily split doc indices [0..N) into CONTIGUOUS chunks (input order preserved) so that
    EVERY chunk's forward provably fits `available_bytes` — i.e.
    `peak_variable_bytes(mm, len(chunk), max(length in chunk)) <= available_bytes` — and no
    chunk exceeds `max_docs`. The variable-length chunker for the TORCH batched encode
    (nlp_server._encode_docs): a large max_S forces a small B (down to 1), a small max_S admits
    a large B — the OOM CLASS is unrepresentable because the bound IS the quadratic peak itself,
    not a linear proxy. Returns list[list[int]] of original indices; concatenating chunk outputs
    in order rebuilds alignment.

    A single doc that does not fit even alone (peak at B=1 > available) raises DocTooLargeError —
    a clear, bounded error, NEVER a silent drop and NEVER a raw RESOURCE_EXHAUSTED. (The greedy
    loop never PACKS an overflow: a doc only joins a chunk when the candidate peak still fits, so
    the ONLY way a chunk can exceed `available` is a LONE doc too big at B=1 — exactly the raise
    below.)

    THE single author of the `peak <= available` decision is `peak_variable_bytes` (P1); this
    function only sequences the greedy grouping. Pure python (framework-free) -> the never-OOM
    invariant is unit-testable on the guest without torch/jax."""
    chunks: list[list[int]] = []
    cur: list[int] = []
    cur_max = 0
    for i, n in enumerate(lengths):
        cand_max = n if n > cur_max else cur_max
        cand_peak = peak_variable_bytes(mm, len(cur) + 1, cand_max)
        if cur and (len(cur) >= max_docs or cand_peak > available_bytes):
            chunks.append(cur)
            cur, cur_max = [i], n
        else:
            cur.append(i)
            cur_max = cand_max
    if cur:
        chunks.append(cur)
    # PROVABLE never-OOM invariant + the single-huge-doc raise. By construction every MULTI-doc
    # chunk already fits (the greedy test gated each admission); the only chunk that can fail
    # this check is a LONE doc too big at B=1 -> fail LOUD, bounded (never a raw OOM).
    for ch in chunks:
        s_max = max(lengths[j] for j in ch)
        peak = peak_variable_bytes(mm, len(ch), s_max)
        if peak > available_bytes:
            assert len(ch) == 1, (  # a packed-overflow would be an invariant violation (a bug)
                f"chunk_by_vram packed an over-budget multi-doc chunk {ch} "
                f"(peak {peak} > available {available_bytes}) — greedy admission is broken")
            raise DocTooLargeError(s_max, peak, available_bytes, mm)
    return chunks


# ===================================================== the BATCH-axis (B) ladder
# The bucket-group batched jax encode runs ONE [B, s_bucket] forward per group. JAX caches
# one compiled executable per distinct (B, S) shape, so a VARIABLE B (the raw group size:
# 1, 3, 5, 7, ...) would re-leak the very cache `ENCODE_LEN_BUCKETS` bounded — a second
# axis of the ADR-0000 unbounded-distinct-shape class. The TYPE answer is the same: draw B
# from a FIXED finite ladder, so the (B, s_bucket) compile grid is bounded by
# len(ENCODE_BATCH_BUCKETS) * len(ENCODE_LEN_BUCKETS) — a CONSTANT, NOT O(requests). B is
# NOT single-valued per s_bucket: it TRACKS the per-request group size (oom_cap == n below
# the OOM ceiling — see `encode_batch_chunks`), so across a request stream B sweeps the whole
# ladder at one fixed s_bucket and the lifetime grid reaches the full len(BATCH)*len(LEN)
# product — looser than the per-text (B=1) path by up to len(BATCH), the honest RAM cost
# batching trades for the dispatch collapse (the grid is still bounded — that is the leak fix).
# Powers of two: a group rounds DOWN to a rung (so the padded footprint never exceeds the
# OOM capacity it was floored from). Tunable via COREF_BATCH_BUCKETS per card/corpus.
ENCODE_BATCH_BUCKETS: tuple[int, ...] = _ladder_from_env(
    "COREF_BATCH_BUCKETS", (1, 2, 4, 8, 16, 32))


def batch_bucket_floor(n: int, ladder: tuple[int, ...]) -> int:
    """The LARGEST ladder rung <= n (round the batch count DOWN to a B-rung). Unlike
    `bucket_len` (smallest rung >= n, round UP for a length we must not truncate), B rounds
    DOWN: the OOM bound already fixed an upper capacity for B, and a fixed ladder rung at or
    below it keeps the padded footprint within budget while drawing B from the finite set
    (so the compile grid stays bounded). Floors at the smallest rung (>=1), never 0."""
    if n < 1:
        raise ValueError(f"batch_bucket_floor: batch count {n} < 1")
    chosen = ladder[0]
    for b in ladder:
        if b <= n:
            chosen = b
        else:
            break
    return chosen


def encode_batch_chunks(group_indices, s_bucket: int, mm: MemModel, available_bytes: int,
                        max_docs: int = ENCODE_MAX_DOCS,
                        batch_ladder: tuple[int, ...] = ENCODE_BATCH_BUCKETS):
    """Split a SAME-s_bucket group of doc indices into FIXED-batch-size chunks for the
    bucket-group batched jax encode, returning (chunks, B) where every chunk has <= B docs
    and B is a single B-ladder rung (the last chunk is padded UP to B with masked dummy rows
    by the caller — that is what makes the forward shape a constant [B, s_bucket]).

    B is the largest B-ladder rung that PROVABLY fits the VRAM bound at this s_bucket. The OOM
    capacity comes FROM `max_batch_for_length(mm, s_bucket, available_bytes)` — the ONE
    inequality `peak_variable_bytes(B, S) <= available` solved for B at the uniform group
    length — then min'd with the group size and max_docs and floored to a ladder rung. This
    file does NOT re-derive the inequality (P1). Because batch_bucket_floor rounds DOWN to a
    rung <= the VRAM cap, peak_variable_bytes(B, s_bucket) <= available for EVERY emitted chunk
    (the never-OOM invariant, on the jax path).

    B is NOT a pure function of s_bucket: the VRAM cap == the group size n whenever n is below
    the per-s_bucket ceiling, so B TRACKS n and, across a request stream at a fixed s_bucket,
    sweeps the whole B-ladder. The (B, s_bucket) compile grid is therefore bounded by
    len(ENCODE_BATCH_BUCKETS) * len(ENCODE_LEN_BUCKETS) — still a CONSTANT (no O(requests)
    re-leak — the leak fix holds), but LOOSER than the per-text (B=1) path by up to
    len(ENCODE_BATCH_BUCKETS): the honest cost batching trades for the dispatch collapse.

    A doc whose s_bucket cannot fit even at B=1 (VRAM cap == 0) raises DocTooLargeError — the
    SAME loud, bounded handling as chunk_by_vram, never a raw RESOURCE_EXHAUSTED."""
    if not group_indices:
        return [], batch_ladder[0]
    n = len(group_indices)
    vram_cap = max_batch_for_length(mm, s_bucket, available_bytes)  # largest B that fits at s_bucket
    if vram_cap < 1:
        raise DocTooLargeError(
            s_bucket, peak_variable_bytes(mm, 1, s_bucket), available_bytes, mm)
    oom_cap = min(vram_cap, max_docs, n)
    b = batch_bucket_floor(oom_cap, batch_ladder)  # round the capacity DOWN to a fixed B-rung
    chunks = [group_indices[i:i + b] for i in range(0, n, b)]
    return chunks, b
