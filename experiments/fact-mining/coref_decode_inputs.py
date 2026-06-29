#!/usr/bin/env python
"""SHARED, single-source extraction of the maverick decode-tail INPUTS (ADR-0012 P1).

The decode tail (now the JAX daemon) consumes a small, exact set of intermediates
produced by maverick's FRONT half. There were THREE hand-rolled producers of that
preprocess+tokenize prep — `capture_fixtures.capture_one` (host fixture capture),
the jax-daemon live path (`nlp_server.coref_clusters_jax_daemon`), and the batched
live path (`nlp_server.coref_clusters_batched`, which needs only the ids/mask) —
and ADR-0012 P1 says there must be ONE authoritative source for it, or they drift.
This module is that one source; all three now call `prepare_decode_inputs`.

It owns the HOST-SIDE prep that is byte-identical between both callers:

  * `prepare_decode_inputs(mav, text)` — runs maverick's `preprocess` (sentence
    split + spaCy word-tokenize, which ALSO yields the per-token char_offsets) and
    `tokenize` (the deberta sub-word encoding + the structural maps), and returns
    the exact tuple of decode inputs MINUS the encoder forward:
      tokens, input_ids, attention_mask, eos_mask [S,S], subtoken_map,
      new_token_map, AND char_offsets (per ORIGINAL token, inclusive char ends).
  * `clusters_token_to_char_offsets(...)` — maps cluster TOKEN offsets to CHAR
    offsets, a verbatim mirror of maverick.predict's `clusters_char_offsets`
    construction, so the jax-daemon path reproduces maverick's char-span contract.

DELIBERATELY FRAMEWORK-FREE (no torch / numpy / jax import). It only orchestrates
methods on the already-loaded `mav` object and does plain-python index mapping, so
it is host-XOR-device trivially (neither side) and is imported safely by BOTH the
torch-only `nlp_server.py` and the host fixture scaffolding `capture_fixtures.py`.

WHERE THE ENCODER LIVES (and why it is NOT here). Producing `last_hidden_state`
is the ONE device op (maverick's deberta forward, a torch host<->device crossing).
Per the device-transfer single-home mandate that keeps the torch edge in
`nlp_server.py`, the encoder forward stays in the torch home
(`nlp_server.encode_last_hidden_state`), NOT in this framework-free module — which
is also why `capture_fixtures` can keep capturing its `last_hidden_state` through
its own encoder forward hook unchanged. This module factors everything ELSE the
two callers shared (the fiddly tokenisation + structural maps + char_offsets),
which is exactly the part that was duplicated.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecodeInputs:
    """The decode-tail inputs for ONE document, minus `last_hidden_state` (the
    encoder forward is the torch home's job). Field shapes mirror maverick's
    `tokenize` output plus `preprocess`'s char_offsets:

      tokens         : list[str]                 original (pre-subword) tokens
      input_ids      : list[int]                 deberta sub-word ids [S]
      attention_mask : list[int]                 [S]
      eos_mask       : [S, S] int mask           upper-triangular sentence blocks
      subtoken_map   : list[int | None]          bpe pos -> new-token idx (word_ids)
      new_token_map  : list[int | None]          new-token idx -> original token idx
      char_offsets   : list[(int, int)]          per ORIGINAL token, (start_char,
                                                 end_char) with end_char INCLUSIVE
    """
    tokens: list
    input_ids: list
    attention_mask: list
    eos_mask: object          # maverick hands this back as a numpy [S,S]; carried opaquely
    subtoken_map: list
    new_token_map: list
    char_offsets: list


def prepare_decode_inputs(src, text: str) -> DecodeInputs:
    """Run the FRONT half (preprocess + tokenize) for one text and return the decode
    inputs. This is the exact prep `capture_fixtures.capture_one` and ALL three live
    coref paths (batched, jax-daemon, jax-unified) need; factoring it here is the
    ADR-0012 P1 single source — the ONE orchestration every path calls.

    `src` is duck-typed: ANY object exposing maverick's `.preprocess(text)` and
    `.tokenize(tokens, eos, speakers)` contract. Two implementations satisfy it and
    BOTH flow through this one function (so there is one orchestration home, P1):
      * the maverick object itself (the torch-bearing reference / batched paths), and
      * `StandalonePreprocessor` (torch-free; the jax-only unified daemon), which
        reimplements those two methods byte-for-byte (see its docstring + the gates).
    Callers that need only a subset (the batched path uses just `input_ids`/
    `attention_mask`) read those fields off the result.

    Byte-identical to the inlined version it replaces: same `src.preprocess(text)`
    (speakers default None) feeding the same `src.tokenize(tokens, eos, speakers)`.
    """
    tokens, eos_indices, speakers, char_offsets = src.preprocess(text)
    tok = src.tokenize(tokens, eos_indices, speakers)
    return DecodeInputs(
        tokens=tok["tokens"],
        input_ids=tok["input_ids"],
        attention_mask=tok["attention_mask"],
        eos_mask=tok["eos_mask"],
        subtoken_map=tok["subtoken_map"],
        new_token_map=tok["new_token_map"],
        char_offsets=char_offsets,
    )


def clusters_token_to_char_offsets(clusters_token_offsets, char_offsets):
    """Map cluster TOKEN offsets -> CHAR offsets, a verbatim mirror of
    maverick.predict's `clusters_char_offsets`:

        [[(char_offsets[span[0]][0], char_offsets[span[1]][1]) for span in cluster]
         for cluster in clusters_token_offsets]

    `clusters_token_offsets` are in ORIGINAL-token space (post `original_token_offsets`),
    and `char_offsets` is indexed by original token, so the two align directly. The
    char end is INCLUSIVE (maverick: `off + tok.idx + len(tok.text) - 1`); we keep it
    exactly so the result equals maverick's char-span contract bit-for-bit.

    FAIL LOUD (ADR-0002): char_offsets is None only for pre-tokenised maverick inputs;
    the coref path always feeds raw `str`, so a None here is a real contract breach.
    """
    if char_offsets is None:
        raise ValueError(
            "char_offsets is None — token->char mapping needs maverick.preprocess's "
            "char_offsets (only produced for str input, which the coref path always uses)")
    return [
        [(char_offsets[start][0], char_offsets[end][1]) for (start, end) in cluster]
        for cluster in clusters_token_offsets
    ]


class StandalonePreprocessor:
    """Torch-free, maverick-free reimplementation of maverick's preprocess+tokenize
    FRONT half, so `prepare_decode_inputs` runs inside the jax-only unified daemon
    (no torch model, no maverick checkpoint, no Lightning/hydra). It exposes
    `.preprocess(text)` and `.tokenize(tokens, eos, speakers)` with maverick's EXACT
    signatures and logic, so `prepare_decode_inputs(self, text)` is byte-identical to
    `prepare_decode_inputs(mav, text)` BY CONSTRUCTION — the SAME spaCy en_core_web_sm
    rule-based tokenizer, the SAME HF deberta-v3 fast tokenizer (+ the two SPEAKER
    special tokens), and the SAME index/eos-mask logic.

    WHY A REIMPLEMENTATION (and why that is honest, not a P1/P7 two-writers violation).
    The unified daemon must NOT import maverick — maverick imports torch (and hydra/
    pytorch-lightning), the exact coexistence this workflow exists to eliminate. You
    cannot call maverick's `preprocess`/`tokenize` without importing maverick, so the
    front half MUST be reauthored on the torch-free side. This is the unavoidable cost
    of retiring torch from the daemon; the discipline is to make the copy FAITHFUL and
    KEEP it honest with a gate (ADR-0011): transcribed verbatim from
    maverick/models/maverick_model.py (`preprocess` L48-80, `tokenize` L155-208,
    `eos_mask` L84-93) and maverick/common/util.py (`download_load_spacy`, `flatten`,
    nltk `sent_tokenize`), each method citing its source. Bit-identity is GATED two ways:
      * GUEST: test_preprocess_bit_identity.py runs this against a verbatim maverick
        reference on shared (spaCy, tokenizer) and asserts identical input_ids /
        eos_mask / subtoken_map / new_token_map / char_offsets;
      * HOST (the end-to-end authority): `--coref-verify` compares the unified daemon's
        clusters against maverick.predict — a preprocess drift changes input_ids -> lhs
        -> clusters and reds there (the discrete-set falsifier, ADR-0009).

    FRAMEWORK NOTE: spaCy / transformers / nltk are NOT torch/numpy/jax — this module
    stays host-XOR-device clean (it imports none of the three at top; these are lazy in
    `from_pretrained`). The torch those packages would otherwise drag in transitively is
    neutralised by `jax_only_guard.install()`, which the daemon calls BEFORE building
    this preprocessor (see jax_only_guard.py — that is the headline device-hygiene seam).
    """

    SPEAKER_SPECIAL_TOKENS = ["[SPEAKER_START]", "[SPEAKER_END]"]

    def __init__(self, nlp, tokenizer):
        self.nlp = nlp
        self.tokenizer = tokenizer

    @classmethod
    def from_pretrained(cls, model_name: str = "microsoft/deberta-v3-large"):
        """Build the standalone preprocessor: en_core_web_sm rule-based tokenizer +
        the deberta-v3 fast tokenizer with maverick's two SPEAKER special tokens. Lazy
        imports (spaCy/transformers/nltk) so the module top stays import-light and
        framework-free; `jax_only_guard.install()` must already have run."""
        import nltk
        import spacy
        from transformers import AutoTokenizer

        # nltk punkt (sentence splitter) — maverick.common.util.download_load_spacy
        for res in ("punkt", "punkt_tab"):  # punkt_tab: newer nltk split
            try:
                nltk.data.find(f"tokenizers/{res}")
            except LookupError:
                try:
                    nltk.download(res, quiet=True)
                except Exception:  # punkt_tab absent on older nltk -> punkt suffices
                    pass
        nlp = spacy.load(
            "en_core_web_sm",
            exclude=["tagger", "parser", "lemmatizer", "ner", "textcat"],
        )
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, use_fast=True, add_prefix_space=True)
        tokenizer.add_special_tokens(
            {"additional_special_tokens": cls.SPEAKER_SPECIAL_TOKENS})
        return cls(nlp, tokenizer)

    # --- maverick.common.util.flatten (L44-45), verbatim
    @staticmethod
    def _flatten(seq):
        return [item for sublist in seq for item in sublist]

    # --- maverick_model.Maverick.preprocess, str branch (L48-80), verbatim
    def preprocess(self, sample, speakers=None):
        from nltk import sent_tokenize

        char_offsets = []
        sentences = []
        off = 0
        s = sent_tokenize(sample)
        for sent, sentence in zip(self.nlp.pipe(s), s):
            char_offsets.append(
                [(off + tok.idx, off + tok.idx + len(tok.text) - 1) for tok in sent])
            sentences.append([tok.text for tok in sent])
            off += len(sentence) + 1
        char_offsets = self._flatten(char_offsets)
        tokens = self._flatten(sentences)
        eos_len = [len(value) for value in sentences]
        eos = [sum(eos_len[0: (i[0] + 1)]) for i in enumerate(eos_len)]
        if speakers is None:
            speakers = ["-"] * len(tokens)
        else:
            speakers = self._flatten(speakers)
        return tokens, eos, speakers, char_offsets

    # --- maverick_model.Maverick.eos_mask (L84-93). np.triu reproduced in pure python
    # (keeps the module framework-free: no numpy import). Returns list[list[int]] [S,S],
    # which the decode path indexes identically to maverick's numpy array.
    @staticmethod
    def eos_mask(input_ids_len, eos_indices):
        mask = [[0] * input_ids_len for _ in range(input_ids_len)]
        prec = 0
        for eos_idx in eos_indices:
            for i in range(prec, eos_idx + 1):
                for j in range(prec, eos_idx + 1):
                    mask[i][j] = 1
            prec = eos_idx
        # np.triu(mask, k=0): keep upper triangle INCLUDING the diagonal (j>=i), zero rest
        for i in range(input_ids_len):
            for j in range(i):
                mask[i][j] = 0
        return mask

    # --- maverick_model.Maverick.tokenize (L155-208), gold_mentions/add_gold_clusters
    # always None on the coref path (matches maverick.predict's defaults), verbatim
    def tokenize(self, tokens, eos_indices, speakers=None, gold_mentions=None,
                 add_gold_clusters=None):
        token_to_new_token_map = []
        new_token_map = []
        new_tokens = []
        last_speaker = None
        for idx, (token, speaker) in enumerate(zip(tokens, speakers)):
            if last_speaker != speaker:
                new_tokens += ["[SPEAKER_START]", speaker, "[SPEAKER_END]"]
                new_token_map += [None, None, None]
                last_speaker = speaker
            token_to_new_token_map.append(len(new_tokens))
            new_token_map.append(idx)
            new_tokens.append(token)

        encoded_text = self.tokenizer(
            new_tokens, add_special_tokens=True, is_split_into_words=True)
        eos_indices = [
            encoded_text.word_to_tokens(token_to_new_token_map[eos - 1]).start
            for eos in eos_indices
            if encoded_text.word_to_tokens(token_to_new_token_map[eos - 1]) is not None
        ]
        return {
            "tokens": tokens,
            "input_ids": encoded_text["input_ids"],
            "attention_mask": encoded_text["attention_mask"],
            "subtoken_map": encoded_text.word_ids(),
            "new_token_map": new_token_map,
            "eos_mask": self.eos_mask(len(encoded_text["input_ids"]), eos_indices),
            "gold_mentions": None,
            "added": None,
        }
