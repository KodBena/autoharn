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
(the JAX cache-leak concern). `chunk_by_token_budget` (relocated HERE from nlp_server so
the OOM bound has ONE home — both the torch batcher and the jax batcher import it, never
copy it) groups multiple docs into OOM-bounded CHUNKS, bounding the linear N*max_S padded
footprint of one batched forward (the memory concern). `encode_batch_chunks` +
`ENCODE_BATCH_BUCKETS` round the BATCH axis B to a finite ladder rung (the SAME ADR-0000
move applied to B: a bucket-group batched encode that compiled per VARIABLE group size
would re-leak the cache `bucket_len` just bounded, so B is drawn from a fixed ladder ->
the (B, s_bucket) compile grid is bounded, not O(requests)). Chunking groups docs;
length-laddering rounds a length; batch-laddering rounds the batch count. Three orthogonal
operations, each its own function, kept on single-ownership grounds (P3) — but the OOM
inequality itself is authored exactly ONCE (chunk_by_token_budget): `encode_batch_chunks`
DERIVES its per-chunk capacity FROM that function, it does not re-derive `b*S<=budget`.

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
# Relocated HERE from nlp_server (it was nlp_server's, but the jax bucket-group batcher
# now needs the SAME bound — so per the do-not-copy mandate it moves to this SSOT home and
# nlp_server imports it). A batched deberta encode runs ONE padded forward over a
# [N, max_S, TH] tensor; unbounded N over a whole book OOMs the card (ADR-0000 Specimen
# 3/4: the bound has one home and is DERIVED from what actually exhausts memory — the
# linear N*max_S padded footprint — not a bare magic count). We cap a PADDED-TOKEN budget
# N*max_S (TH fixed per model) AND a hard per-chunk doc count, whichever binds first.
# SCOPE (honest): the per-layer attention activation is O(N*max_S^2); the budget bounds the
# linear N*max_S term batching ADDED, not that quadratic term (inherent to encoding a long
# doc at all, floored at one-doc-per-chunk + capped by deberta's max position length). The
# defaults are a CONSERVATIVE operator-tunable guess (keep a typical 5-paragraph request in
# ONE forward), not a VRAM-bytes-derived budget; tune COREF_ENCODE_MAX_* per card.
ENCODE_MAX_PADDED_TOKENS: int = int(os.environ.get("COREF_ENCODE_MAX_PADDED_TOKENS", "8192"))
ENCODE_MAX_DOCS: int = int(os.environ.get("COREF_ENCODE_MAX_DOCS", "64"))


def chunk_by_token_budget(lengths, max_padded_tokens: int, max_docs: int):
    """Greedily split doc indices [0..N) into CONTIGUOUS chunks (input order preserved) so
    each chunk's padded-cell count (len(chunk) * max(length in chunk)) stays within
    `max_padded_tokens`, and no chunk exceeds `max_docs` docs — whichever binds first.

    A single doc longer than the budget forms its OWN chunk (we never drop a doc — the
    bound degrades to one doc per forward, the safe floor). Pure python (framework-free),
    so the OOM bound is unit-testable on the guest without torch/jax. Returns list[list[int]]
    of original indices; concatenating chunk outputs in order rebuilds alignment.

    THE single author of the `padded-cells <= budget` OOM inequality (P1). The torch
    batched encode (nlp_server._encode_docs) and the jax bucket-group batched encode
    (coref_host_shell.encode_lhs_batched, via `encode_batch_chunks`) BOTH consume this one
    function; neither re-derives the inequality. Distinct from `bucket_len` (which rounds a
    LENGTH to bound the compile set) and from `encode_batch_chunks` (which rounds the BATCH
    count to a ladder for the compile bound and takes its OOM capacity FROM here).
    """
    chunks: list[list[int]] = []
    cur: list[int] = []
    cur_max = 0
    for i, n in enumerate(lengths):
        cand_max = cur_max if n <= cur_max else n
        cand_cells = cand_max * (len(cur) + 1)
        if cur and (len(cur) >= max_docs or cand_cells > max_padded_tokens):
            chunks.append(cur)
            cur, cur_max = [i], n
        else:
            cur.append(i)
            cur_max = cand_max
    if cur:
        chunks.append(cur)
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


def encode_batch_chunks(group_indices, s_bucket: int,
                        max_padded_tokens: int = ENCODE_MAX_PADDED_TOKENS,
                        max_docs: int = ENCODE_MAX_DOCS,
                        batch_ladder: tuple[int, ...] = ENCODE_BATCH_BUCKETS):
    """Split a SAME-s_bucket group of doc indices into FIXED-batch-size chunks for the
    bucket-group batched jax encode, returning (chunks, B) where every chunk has <= B docs
    and B is a single B-ladder rung (the last chunk is padded UP to B with masked dummy
    rows by the caller — that is what makes the forward shape a constant [B, s_bucket]).

    B is the largest B-ladder rung that fits the OOM bound at this s_bucket. The OOM
    capacity is taken FROM `chunk_by_token_budget` (the ONE author of the b*S<=budget
    inequality) on the uniform-length group, then floored to a ladder rung — this file does
    NOT re-derive the inequality. B is NOT a pure function of s_bucket: oom_cap == n for a
    group below the OOM ceiling, so B = batch_bucket_floor(min(n, floor(budget/s), max_docs))
    TRACKS the per-request group size n and, across a request stream at a fixed s_bucket,
    sweeps the whole B-ladder. The (B, s_bucket) compile grid is therefore bounded by
    len(ENCODE_BATCH_BUCKETS) * len(ENCODE_LEN_BUCKETS) — still a CONSTANT (no O(requests)
    re-leak — the leak fix holds), but LOOSER than the per-text (B=1) path by up to
    len(ENCODE_BATCH_BUCKETS): the honest cost batching trades for the dispatch collapse.
    FAIL LOUD via the helpers on a malformed ladder/length."""
    if not group_indices:
        return [], batch_ladder[0]
    n = len(group_indices)
    # OOM capacity for THIS s_bucket from the ONE bound (uniform lengths -> the first/full
    # chunk's size is the per-chunk doc capacity that keeps cap*s_bucket <= budget).
    oom_cap = max(len(c) for c in chunk_by_token_budget([s_bucket] * n, max_padded_tokens, max_docs))
    b = batch_bucket_floor(oom_cap, batch_ladder)  # round the capacity DOWN to a fixed B-rung
    chunks = [group_indices[i:i + b] for i in range(0, n, b)]
    return chunks, b
