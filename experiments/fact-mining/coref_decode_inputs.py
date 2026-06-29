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
      * `StandalonePreprocessor` (torch-free AND transformers-free; the jax-only unified
        daemon), which reimplements those two methods — spaCy word-tokenize + raw
        sentencepiece sub-tokenisation — bit-identically (see its docstring + the gates).
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
    """Torch-free, transformers-free, maverick-free reimplementation of maverick's
    preprocess+tokenize FRONT half, so `prepare_decode_inputs` runs inside the jax-only
    unified daemon (no torch model, no maverick checkpoint, no Lightning/hydra, AND no
    HuggingFace `transformers`/`huggingface_hub`/`tokenizers`). It exposes `.preprocess(
    text)` and `.tokenize(tokens, eos, speakers)` with maverick's EXACT signatures and
    logic, so `prepare_decode_inputs(self, text)` is bit-identical to `prepare_decode_
    inputs(mav, text)` — the SAME spaCy en_core_web_sm rule-based tokenizer, the SAME
    deberta-v3 SentencePiece sub-word model (`spm.model`, + the two SPEAKER special
    tokens), and the SAME index/eos-mask logic.

    TOKENISER = RAW SENTENCEPIECE, NOT HF. maverick's `tokenize` calls a HF
    `DebertaV2TokenizerFast`; deberta-v3's fast tokenizer is a SentencePiece (unigram)
    model under the hood (`spm.model`). We tokenise with `sentencepiece.
    SentencePieceProcessor` loaded from a LOCAL `spm.model` directly — Apache-2.0,
    standalone, torch-free, and (unlike `transformers`) it never force-imports torch.
    That removes the entire HF surface from the daemon (the host `transformers`
    transitively force-imports torch, which jax_only_guard correctly blocks). To match
    the FAST tokenizer maverick actually used, two raw-spm-vs-fast divergences are
    reproduced in `_encode_word` (the fast `tokenizers` backend has NO byte-fallback):
      (1) BYTE-FALLBACK: raw spm maps an OOV piece to a run of `<0xNN>` byte tokens; the
          fast tokenizer emits ONE `[UNK]` for that whole run. We collapse each MAXIMAL
          CONTIGUOUS run of byte-fallback pieces (`sp.IsByte(id)`) to a single `unk_id`.
          (Probed decision boundary, ADR-0009: `ᚠᚠ` -> one `[UNK]`; `ᚠaᚠ` -> two, the
          known `a` between them breaking the run — exactly the fast lattice's behaviour.)
      (2) EMPTY NORMALISATION: a word that normalises to nothing yields `[]` from raw
          `sp.encode`, but the fast path splits on `word.strip()`: a ZERO-WIDTH non-blank
          (ZWSP, BOM, ZWJ) keeps a lone `▁` (the metaspace prefix) -> we emit `[space_id]`;
          PURE WHITESPACE (space/tab/newline/U+2028/U+3000) is stripped to nothing by the
          Metaspace normaliser -> the fast tokenizer emits ZERO tokens, so we emit `[]`.
          (spaCy emits a pure-whitespace token for any double-space/tab/mid-sentence
          newline — common in Gutenberg prose — so this boundary is reachable, not hypothetical.)
    Char OFFSETS are NOT this tokeniser's job — they come from `preprocess` (spaCy), per
    original token, unchanged. `word_ids()`/`word_to_tokens()` (the subtoken_map and the
    eos start positions) are reconstructed directly from the per-word piece spans.

    WHY A REIMPLEMENTATION (and why that is honest, not a P1/P7 two-writers violation).
    The unified daemon must NOT import maverick — maverick imports torch (and hydra/
    pytorch-lightning), the exact coexistence this workflow exists to eliminate. You
    cannot call maverick's `preprocess`/`tokenize` without importing maverick, so the
    front half MUST be reauthored on the torch-free side. This is the unavoidable cost
    of retiring torch from the daemon; the discipline is to make the copy FAITHFUL and
    KEEP it honest with a gate (ADR-0011): `preprocess`/`eos_mask`/the new_token_map loop
    are transcribed verbatim from maverick/models/maverick_model.py (`preprocess` L48-80,
    `tokenize` L155-208, `eos_mask` L84-93); the spm sub-tokenisation is proved equal to
    the fast HF tokenizer maverick uses. Bit-identity is GATED two ways:
      * GUEST: test_preprocess_bit_identity.py runs this against (a) a verbatim maverick
        reference using the real `DebertaV2TokenizerFast`, and (b) the fast tokenizer
        directly over a byte-fallback / >512 / unicode battery, asserting identical
        input_ids / attention_mask / eos_mask / subtoken_map / new_token_map / char_
        offsets. transformers is torch-free ON THE GUEST, so this comparison runs here;
      * HOST (the end-to-end authority): `--coref-verify` compares the unified daemon's
        clusters against maverick.predict — a preprocess drift changes input_ids -> lhs
        -> clusters and reds there (the discrete-set falsifier, ADR-0009).

    FRAMEWORK NOTE: sentencepiece / spaCy / nltk are NOT torch/numpy/jax — this module
    stays host-XOR-device clean (it imports none of the three at top; these are lazy in
    `from_spm`). sentencepiece is a standalone CPU lib that returns plain python lists; it
    authors no numpy/jax array, so it is host-XOR-device trivially (neither side) and is
    NOT a host-array concern. The torch spaCy's trf plugins would otherwise drag in is
    neutralised by `jax_only_guard.install()`, which the daemon calls BEFORE building this
    preprocessor (see jax_only_guard.py — the headline device-hygiene seam).
    """

    SPEAKER_SPECIAL_TOKENS = ["[SPEAKER_START]", "[SPEAKER_END]"]

    def __init__(self, nlp, sp):
        self.nlp = nlp
        self.sp = sp  # a loaded sentencepiece.SentencePieceProcessor (deberta-v3 spm.model)
        # Structural token ids — the deberta-v3 + maverick tokenizer contract. The spm
        # model owns [PAD]=0/[CLS]=1/[SEP]=2/[UNK]=3 and ▁ as real pieces (read off it,
        # P1); [MASK] and the two SPEAKER tokens are ADDED ABOVE the 128000-piece vocab,
        # in transformers' deterministic order: [MASK]=vocab, then additional_special_
        # tokens -> [SPEAKER_START]=vocab+1, [SPEAKER_END]=vocab+2 (maverick adds exactly
        # these two, the same way). These ids are VALIDATED bit-for-bit against the real
        # DebertaV2TokenizerFast in test_preprocess_bit_identity.py (the gate), so a wrong
        # id or a changed added-token order reds there rather than tokenising silently off.
        self.unk_id = sp.unk_id()                # 3   ([UNK]); the byte-fallback collapse target
        self.space_id = sp.PieceToId("▁")   # 507 (▁); the per-word metaspace prefix
        self.cls_id = sp.PieceToId("[CLS]")      # 1
        self.sep_id = sp.PieceToId("[SEP]")      # 2
        vocab = sp.GetPieceSize()                # 128000
        self.mask_id = vocab                     # 128000 ([MASK], added by deberta-v3)
        self.special_token_ids = {               # the two SPEAKER tokens, added next
            "[SPEAKER_START]": vocab + 1,        # 128001
            "[SPEAKER_END]": vocab + 2,          # 128002
        }

    @staticmethod
    def _resolve_cached_spm(model_name: str) -> str:
        """Locate `spm.model` in the local HuggingFace hub CACHE by globbing the snapshot
        dir — for guest/dev use only, WITHOUT importing `huggingface_hub`/`transformers`
        (the daemon never calls this; it loads the VENDORED spm.model via `from_spm`).
        FAIL LOUD (ADR-0002) if absent: the caller must point at a real spm.model."""
        import glob
        import os
        org_repo = model_name.replace("/", "--")
        pattern = os.path.expanduser(
            f"~/.cache/huggingface/hub/models--{org_repo}/snapshots/*/spm.model")
        hits = sorted(glob.glob(pattern))
        if not hits:
            raise FileNotFoundError(
                f"no cached spm.model for {model_name!r} (looked at {pattern}). The daemon "
                f"loads the VENDORED spm.model (export_deberta_maverick.py writes it next to "
                f"the weights) via from_spm(); from_pretrained is a guest/dev convenience "
                f"that needs the HF cache. Pass an explicit spm path to from_spm() instead.")
        return os.path.realpath(hits[0])

    @classmethod
    def from_spm(cls, spm_path: str):
        """Build the standalone preprocessor from a LOCAL spm.model file: en_core_web_sm
        rule-based tokenizer (spaCy) + a `sentencepiece.SentencePieceProcessor` loaded
        from `spm_path`. This is the DAEMON's constructor (the vendored spm.model, no HF
        cache, no transformers). Lazy imports (spaCy/nltk/sentencepiece) so the module top
        stays import-light and framework-free; `jax_only_guard.install()` must already
        have run (it neutralises the torch spaCy's trf plugins would otherwise drag in)."""
        import os

        import nltk
        import sentencepiece
        import spacy

        if not os.path.isfile(spm_path):
            raise FileNotFoundError(
                f"spm.model not found at {spm_path!r}. The unified daemon needs the VENDORED "
                f"sentencepiece model; run export_deberta_maverick.py (it copies maverick's "
                f"spm.model next to the deberta weights).")
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
        sp = sentencepiece.SentencePieceProcessor()
        sp.Load(spm_path)
        return cls(nlp, sp)

    @classmethod
    def from_pretrained(cls, model_name: str = "microsoft/deberta-v3-large"):
        """Guest/dev convenience: resolve the deberta-v3 spm.model from the local HF hub
        CACHE (no transformers/huggingface_hub import — a plain glob) and build via
        from_spm. The DAEMON does NOT use this — it loads the vendored spm.model with
        from_spm(<vendored path>); this exists so the guest tests and dev runs can build
        a preprocessor without the export having run."""
        return cls.from_spm(cls._resolve_cached_spm(model_name))

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

    def _encode_word(self, word):
        """Sub-tokenise ONE pre-split word into deberta-v3 ids, reproducing the FAST
        `DebertaV2TokenizerFast` per-word behaviour from raw sentencepiece (the fast
        tokenizer's per-word path under is_split_into_words=True + add_prefix_space=True):
        `sp.encode` already prepends the ▁ metaspace marker, so the only two corrections
        are the fast-vs-raw divergences documented on the class —
          (1) collapse each MAXIMAL CONTIGUOUS run of byte-fallback pieces (`sp.IsByte`)
              to a single `unk_id` (the fast backend has no byte-fallback -> one [UNK]);
          (2) a word that normalises to NOTHING (`sp.encode` -> []) splits two ways, which
              raw `sp.encode` cannot distinguish (both give []) but the fast Metaspace
              normaliser DOES (ADR-0009 decision boundary, `word.strip()==""`):
                - PURE WHITESPACE (space/tab/newline/U+2028/U+3000, `word.strip()==""`):
                  Metaspace strips it to nothing -> the fast tokenizer emits ZERO tokens.
                  We return [] (word_first then records None for this word, :383).
                - ZERO-WIDTH but non-blank (ZWSP/BOM/ZWJ, `word.strip()!=""`): the fast
                  tokenizer keeps the lone ▁ metaspace prefix -> we emit [space_id].
        Returns the list of ids for this word (>= 1, except pure-whitespace -> [])."""
        ids = self.sp.encode(word, out_type=int)
        out = []
        i = 0
        n = len(ids)
        while i < n:
            if self.sp.IsByte(ids[i]):
                while i < n and self.sp.IsByte(ids[i]):   # one [UNK] per byte-fallback run
                    i += 1
                out.append(self.unk_id)
            else:
                out.append(ids[i])
                i += 1
        if not out and word.strip() != "":   # zero-width non-blank -> lone ▁ the fast keeps
            out.append(self.space_id)         # (pure whitespace stays [] -> zero tokens)
        return out

    # --- maverick_model.Maverick.tokenize (L155-208), gold_mentions/add_gold_clusters
    # always None on the coref path (matches maverick.predict's defaults). The new_token_
    # map loop is verbatim maverick; the encoder call `self.tokenizer(new_tokens,
    # add_special_tokens=True, is_split_into_words=True)` and its `.word_ids()`/`.word_to_
    # tokens(...).start` are reconstructed from raw sentencepiece (see _encode_word) so the
    # daemon needs NO HF tokenizer — proved bit-identical in test_preprocess_bit_identity.
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

        # Reproduce tokenizer(new_tokens, add_special_tokens=True, is_split_into_words=True):
        #   input_ids = [CLS] + per-word pieces + [SEP]; attention_mask all 1s;
        #   subtoken_map = word_ids() (the word index per subtoken, None for CLS/SEP);
        #   word_first[wi] = word_to_tokens(wi).start (the first token index of word wi),
        #     or None if that word produced no tokens (here always >= 1 -> never None).
        input_ids = [self.cls_id]
        subtoken_map = [None]                       # word_ids(): None for [CLS]
        word_first = []                             # word_to_tokens(wi).start
        for wi, w in enumerate(new_tokens):
            start = len(input_ids)
            if w in self.special_token_ids:         # [SPEAKER_START]/[SPEAKER_END] specials
                ids = [self.special_token_ids[w]]
            else:
                ids = self._encode_word(w)
            word_first.append(start if ids else None)
            input_ids.extend(ids)
            subtoken_map.extend([wi] * len(ids))
        input_ids.append(self.sep_id)
        subtoken_map.append(None)                   # word_ids(): None for [SEP]
        attention_mask = [1] * len(input_ids)

        # eos start positions — verbatim maverick semantics, including the `is not None`
        # filter (a word that produced no tokens contributes no eos boundary).
        eos_out = []
        for eos in eos_indices:
            start = word_first[token_to_new_token_map[eos - 1]]
            if start is not None:
                eos_out.append(start)

        return {
            "tokens": tokens,
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "subtoken_map": subtoken_map,
            "new_token_map": new_token_map,
            "eos_mask": self.eos_mask(len(input_ids), eos_out),
            "gold_mentions": None,
            "added": None,
        }
