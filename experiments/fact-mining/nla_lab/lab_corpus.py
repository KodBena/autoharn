#!/usr/bin/env python
"""lab_corpus — the FIXED, seeded, code-addressable input corpus for the bench
(ADR-0009 reproducibility, B9 answer).

control_lab's bench was not reproducible in isolation — it needed a live
taskset-pinned C++ producer streaming over redis, with no captured state to replay.
Our bench runs against a FIXED corpus drawn deterministically from a seed, so it is
re-runnable on the guest with CPU jax (the `capture_states.py -> states.npz`
discipline, here in-process and seed-addressable).

HOST-XOR-DEVICE: pure python (stdlib `random` only). Reuses the `shape_buckets.pad_to`
SSOT padder (no second author) and `ENCODE_PAD_ID`. Emits host token-id / mask rows
already at `[B, s_bucket]`; the device-side `lab_measure.lift_batch` lifts them — the
bench keeps the bucketing+padding UPSTREAM of the variant, exactly as the host shell
does (the contract's placement decision).
"""

from __future__ import annotations

import random

import shape_buckets

#: a real vocab is ~128k for deberta-v3; the synthetic self-test uses a small vocab
#: passed in. The corpus draws ids in [1, vocab) (0 is the masked pad id, ENCODE_PAD_ID).
def make_batch(batch: int, seq_bucket: int, vocab: int, seed: int
               ) -> tuple[list[list[int]], list[list[int]]]:
    """Deterministically build `batch` rows of token ids + masks, each a real length in
    [seq_bucket//2+1, seq_bucket] padded to `seq_bucket` by the ONE `shape_buckets.pad_to`
    padder, mask = 1s over real tokens then 0s. Seeded by `(seed, batch, seq_bucket)` so
    the same call yields the same corpus on any host — the reproducible fixture."""
    rng = random.Random((seed, batch, seq_bucket).__hash__())
    ids_rows: list[list[int]] = []
    mask_rows: list[list[int]] = []
    lo = max(1, seq_bucket // 2 + 1)
    for _ in range(batch):
        real = rng.randint(lo, seq_bucket)
        toks = [rng.randint(1, max(1, vocab - 1)) for _ in range(real)]
        ids_rows.append(shape_buckets.pad_to(toks, seq_bucket, shape_buckets.ENCODE_PAD_ID))
        mask_rows.append(shape_buckets.pad_to([1] * real, seq_bucket, 0))
    return ids_rows, mask_rows
