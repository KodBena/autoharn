#!/usr/bin/env python
"""distill.data — the HOST data pipeline + the DATA PLAN (residue §3 ladder).

Emits host token-id / mask rows already bucketed+padded to `[B, s_bucket]` (python
lists), exactly the shape `lab_measure.lift_batch` lifts. The device side never sees
text; this file never sees a device array. The teacher targets are computed device-side
(by the loop driver calling `ste.teacher_lhs` on each lifted batch).

THE DATA PLAN (what + how much, with the load-bearing diversity caveat):

  WHAT.  Deployment-representative *unlabeled* text. The coref deployment sees prose and
  dialogue; the Gutenberg paragraphs already mined are the available proxy and the
  teacher supplies the targets (no labeling). DIVERSITY CAVEAT (load-bearing): a SINGLE
  book is borderline-narrow — one author's register, vocabulary, sentence shape — and a
  student fit to it is quant-robust *on that distribution* and may regress elsewhere.
  SUPPLEMENT IT: multiple books across genres + registers (exposition, dialogue, modern
  text), so the feature-distillation covers the activation manifold the deployed encoder
  actually meets. The single-book PoC corpus is the floor, not the target.

  HOW MUCH.  Two rungs (residue §3 ladder):
    * Cheap GPTQ/calibration-style rung: ~128-512 sequences — enough to fit per-channel
      structure (the scale the AWQ calibrator already uses, `_CALIB_MAX_ROWS = 256`). A
      fast first signal, not the full lever.
    * Feature-distillation rung: ~few-K to 10-20K sequences — corpus-scale but nowhere
      near pretraining; where the W4 student earns the drop below the PTQ floor. Hours of
      teacher-forward compute, not labeling.

HOST-XOR-DEVICE: pure python (stdlib) + `shape_buckets` + `lab_corpus` (both
framework-free SSOTs). The host text path lazily imports the daemon's standalone
preprocessor BY MODULE NAME (the torch-free spm tokenizer behind its own seam), so this
file's AST carries no numpy and no jax — host-only, XOR-clean.
"""

from __future__ import annotations

from typing import Iterator

import shape_buckets
from nla_lab import lab_corpus

#: a host batch: (ids_rows, mask_rows), each a list of `[B, s_bucket]` python ints.
HostBatch = tuple[list[list[int]], list[list[int]]]


def synthetic_plan(
    n_batches: int, batch: int, seq_bucket: int, vocab: int, seed: int,
) -> list[HostBatch]:
    """The GUEST data plan: `n_batches` deterministic synthetic batches reusing the ONE
    `lab_corpus.make_batch` fixture builder (seeded ids + masks, padded by the one
    `shape_buckets.pad_to`). The machinery, not the production corpus — the host run uses
    `text_corpus_plan`. Each batch is independently seeded so the corpus is reproducible
    and the batches differ."""
    if seq_bucket not in shape_buckets.ENCODE_LEN_BUCKETS:
        raise ValueError(
            f"seq_bucket={seq_bucket} is not a rung of "
            f"shape_buckets.ENCODE_LEN_BUCKETS={shape_buckets.ENCODE_LEN_BUCKETS}.")
    return [lab_corpus.make_batch(batch, seq_bucket, vocab, seed + i)
            for i in range(n_batches)]


def _chunk(rows: list[list[int]], batch: int) -> Iterator[list[list[int]]]:
    """Yield `batch`-sized chunks; the trailing short chunk is dropped (a ragged final
    batch would change the compiled `[B, S]` shape — bucketing is upstream of the device,
    so keep every emitted batch a full `[B, s_bucket]`)."""
    for i in range(0, len(rows) - batch + 1, batch):
        yield rows[i:i + batch]


def text_corpus_plan(
    corpus_path: str, tokenizer_name: str, batch: int, seq_bucket: int,
    max_sequences: int | None = None,
) -> list[HostBatch]:
    """The HOST data plan: a text file (one document/paragraph per line) -> torch-free spm
    token ids -> truncate/pad to `seq_bucket` via the ONE `shape_buckets.pad_to` padder ->
    `[B, s_bucket]` host batches. The spm tokenizer is the daemon's standalone preprocessor
    (`coref_decode_inputs.StandalonePreprocessor`, the SAME vocab the maverick weights
    expect), imported BY NAME so this file stays host-XOR-device clean.

    `tokenizer_name` is the encoder HF tokenizer identity the npz codec wrote alongside
    the teacher weights (`load_deberta_npz` returns it) — never a host-side constant, so
    the student tokenizes with exactly the vocab the teacher was fine-tuned on (R2/F1).

    NOTE: this is the host-run path (real corpus, real spm). It is exercised on the host;
    the guest proof uses `synthetic_plan`. Rows longer than `seq_bucket` are truncated to
    the bucket (the bench's bucketing is upstream; the distillation fits the deployed
    bucket geometry, not arbitrary lengths)."""
    from coref_decode_inputs import StandalonePreprocessor

    # the SAME preprocess the daemon runs (sentence-split + spaCy words -> spm sub-word
    # ids), built from the encoder's tokenizer identity (the spm.model the maverick weights
    # expect). preprocess() -> words/eos/speakers; tokenize() -> the [CLS]..[SEP] input_ids.
    pre = StandalonePreprocessor.from_pretrained(tokenizer_name)
    ids_rows: list[list[int]] = []
    mask_rows: list[list[int]] = []
    with open(corpus_path, encoding="utf-8") as fh:
        for line in fh:
            text = line.strip()
            if not text:
                continue
            words, eos, speakers, _ = pre.preprocess(text)
            toks = pre.tokenize(words, eos, speakers)["input_ids"][:seq_bucket]
            if not toks:
                continue
            real = len(toks)
            ids_rows.append(shape_buckets.pad_to(toks, seq_bucket, shape_buckets.ENCODE_PAD_ID))
            mask_rows.append(shape_buckets.pad_to([1] * real, seq_bucket, 0))
            if max_sequences is not None and len(ids_rows) >= max_sequences:
                break

    batches: list[HostBatch] = []
    id_chunks = list(_chunk(ids_rows, batch))
    mask_chunks = list(_chunk(mask_rows, batch))
    for ic, mc in zip(id_chunks, mask_chunks):
        batches.append((ic, mc))
    if not batches:
        raise ValueError(
            f"{corpus_path} produced 0 full batches of size {batch} at seq_bucket "
            f"{seq_bucket} (got {len(ids_rows)} sequences). Provide more / longer text.")
    return batches
