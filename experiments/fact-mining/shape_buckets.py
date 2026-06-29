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
single LIST padder (token-id lists): the batched torch encode (nlp_server._encode_docs)
and the jax-unified encode/decode (coref_host_shell) BOTH call it — there is no
hand-rolled second `list + [pad]*(n)` anywhere. The jax decode ALSO right-pads device
ARRAYS (lhs/reps/masks) with `jnp.pad` (coref_host_shell) — a distinct mechanism
because `pad_to` is a python-list padder and those are 2-D/3-D device arrays — but it is
NOT a second author of the ladder truth: every `jnp.pad` target length is `bucket_len`'s
output, so the ladder (the truth) still has exactly one home. `bucket_len` is THE single
length->bucket map. These are
DISTINCT from nlp_server.chunk_by_token_budget, which is NOT a second bucketer of this
truth: it groups multiple docs into OOM-bounded CHUNKS (bounding the linear N*max_S
padded footprint of one batched forward), an orthogonal concern from laddering ONE
sequence's length to bound the per-shape COMPILE set. Chunking groups docs; laddering
rounds a length. Kept separate on single-ownership grounds (P3), cross-referenced here
so the distinction is not left to the reader.

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
