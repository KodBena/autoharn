#!/usr/bin/env python
"""Bit-identity falsifier: the sentencepiece StandalonePreprocessor == the HF tokeniser.

SUB-TASK 2 gate. The unified daemon cannot import maverick (torch) OR `transformers`
(it transitively force-imports torch — jax_only_guard blocks it). deberta-v3's fast
tokenizer is a SentencePiece (unigram) model under the hood, so `StandalonePreprocessor`
now tokenises with RAW `sentencepiece` from a local `spm.model`. P1/P7 say a
reimplementation across a boundary is honest ONLY if a mechanism keeps the copy from
drifting (ADR-0011). This is that mechanism on the GUEST, and `transformers` is torch-
FREE on the guest (4.53.2), so the reference fast tokenizer — the exact thing maverick
uses — runs HERE; a divergence is a FAIL to surface.

TWO falsifiers, both BIT-IDENTITY over input_ids + ALL maps:

  1. test_standalone_tokenize_matches_fast_tokenizer (PRIMARY; needs only transformers,
     NOT maverick source). It runs `StandalonePreprocessor.tokenize` against maverick's
     tokenize logic reproduced inline on the REAL `DebertaV2TokenizerFast`, over a battery
     of word-lists that INCLUDES a >512-subtoken doc and tricky-unicode / byte-fallback
     probes (ADR-0009: the byte-fallback edge is a DISCRETE decision boundary — the fast
     tokenizer has NO byte-fallback and emits ONE [UNK] per OOV run where raw spm emits a
     run of <0xNN> byte tokens; the standalone must reproduce the FAST behaviour). Asserts
     input_ids / attention_mask / subtoken_map(word_ids) / eos_mask are IDENTICAL.

  2. test_standalone_preprocess_is_bit_identical_to_maverick (needs maverick source). It
     execs maverick's ACTUAL preprocess/tokenize/eos_mask source as a reference (binding
     its `self.tokenizer` to the real fast HF tokenizer) and asserts the FULL decode
     inputs match end to end — input_ids, attention_mask, eos_mask, subtoken_map,
     new_token_map, char_offsets, tokens — including the long / unicode docs.

The end-to-end cluster authority is the HOST `--coref-verify` (a preprocess drift changes
input_ids -> lhs -> clusters); these two prove the tokenisation is bit-identical on the
guest, which is fully guest-provable (sentencepiece vs the transformers reference).
"""

from __future__ import annotations

import ast
import glob
import os
import textwrap

import pytest

CANDIDATES = []
if os.environ.get("MAVERICK_SRC"):
    CANDIDATES.append(os.environ["MAVERICK_SRC"])
CANDIDATES += glob.glob(os.path.expanduser(
    "~/w/vdc/venvs/*/lib*/python*/site-packages/maverick/models/maverick_model.py"))
CANDIDATES += glob.glob("/tmp/claude-*/**/maverick/models/maverick_model.py", recursive=True)
CANDIDATES += glob.glob(os.path.expanduser(
    "~/**/maverick-coref*/maverick/models/maverick_model.py"), recursive=True)

MODEL = "microsoft/deberta-v3-large"

# A >512-subtoken doc (a long paragraph forces the long-sequence path), tricky unicode,
# and the byte-fallback probe (chars OUTSIDE the 128k spm vocab — runic, plane-14 tag
# chars, an embedded tag char), plus zero-width / BOM that normalise to nothing, plus
# real-prose INTERNAL whitespace (double-space, tab, mid-sentence newline) that spaCy
# emits as a pure-whitespace token (the R1 boundary: must transcribe to ZERO subtokens).
_LONG = ("Marie Curie discovered radium and polonium. " * 40).strip()
TEXTS = [
    "John saw Mary. He waved at her happily.",
    "Marie Curie discovered radium; she won two Nobel Prizes. The committee honored her work.",
    "It's 3.14. Mr. Smith's dog—the big one—ran. They chased it.",
    "The cat sat on the mat.",
    _LONG,
    "Café naïve résumé — the committee’s ℳ stood for Curie. "
    "She used \U0001d54f and Ⅸ in her notes.",
    # INTERNAL whitespace tokens (R1): double-space-after-period typesetting, a tab, and a
    # mid-sentence newline — each makes spaCy emit a pure-whitespace token. The standalone
    # must transcribe these to zero subtokens, bit-identical to the fast tokenizer.
    "Hello  world. They left.",
    "a\tb done. It ran.",
    "The wrapped\nline broke. She read it.",
]

# Word-list batteries for the direct fast-tokenizer comparison (each entry is a list of
# pre-split "tokens" fed to tokenize). Cover the discrete edges explicitly.
_RUNIC = "ᚠ"          # runic FEHU — OUTSIDE the spm vocab -> byte fallback -> [UNK]
_TAG = "\U000e0041"        # plane-14 tag latin A — OUTSIDE vocab -> byte fallback -> [UNK]
_ZWSP = "​"           # zero-width space — normalises to nothing -> lone metaspace
_BOM = "﻿"            # BOM — normalises to nothing
WORD_BATTERIES = [
    ["John", "saw", "Mary", "."],
    ["It's", "3.14", "—", "naïve", "café", "résumé"],
    # byte-fallback edges: a single OOV char, a RUN of two (one [UNK]), OOV-known-OOV
    # (two [UNK]s, the known char breaks the run), and an embedded OOV char in a word.
    [_RUNIC, _RUNIC + _RUNIC, _RUNIC + "a" + _RUNIC, _TAG, "x" + _TAG + "y", "ok"],
    # ZERO-WIDTH non-blank words (ZWSP/BOM) keep the lone metaspace token (one ▁).
    [_ZWSP, "a", _ZWSP + _ZWSP, "b", _BOM],
    # PURE-WHITESPACE words (the R1 boundary): space/tab/newline/double-space/U+2028/U+3000
    # all strip to nothing -> the fast tokenizer emits ZERO tokens (no lone ▁). spaCy emits
    # exactly such a token for any double-space/tab/mid-sentence newline in real prose, so
    # the standalone MUST also emit []; emitting [▁] here drifts input_ids/subtoken_map/eos.
    ["Hello", " ", "world", "\t", "ok", "\n", "x", "  ", "y", " ", "z", "　", "end"],
    # complex unicode that IS in-vocab (emoji, ZWJ sequence, double-struck X, aleph, roman)
    ["\U0001d54f", "ℵ", "\U0001f389", "\U0001f468‍\U0001f469‍\U0001f467",
     "Ⅷ", "straße"],
    # the >512-subtoken doc as words (forces the long path through tokenize)
    ["The", "quick", "brown", "fox"] * 200,
]


def _find_source():
    for p in CANDIDATES:
        if p and os.path.exists(p):
            return p
    return None


# R2/F2 — the drift falsifier must NOT no-op green when the daemon is in play. On a
# host/CI that exercises the unified daemon, the transcription-drift gate is load-bearing
# (it is the whole ADR-0011 justification for allowing the StandalonePreprocessor copy),
# so a missing maverick source must be a HARD FAIL, not a silent skip that "proves
# nothing about drift". Set COREF_REQUIRE_BIT_IDENTITY=1 in that environment: then a
# missing source fails the suite instead of skipping it. Off (the bare guest), it still
# skips — the guest legitimately may lack maverick source. (The PRIMARY falsifier below,
# test_standalone_tokenize_matches_fast_tokenizer, does NOT need maverick source, so the
# byte-fallback / >512 gate runs on the bare guest regardless.)
_REQUIRE = os.environ.get("COREF_REQUIRE_BIT_IDENTITY") not in (None, "", "0")


def _source_or_fail():
    """The source path, or — when COREF_REQUIRE_BIT_IDENTITY is set — a hard failure.
    Used by the skipif: when required, _find_source() must be non-None so the gate
    cannot silently SKIP on a daemon-bearing host (R2/F2)."""
    src = _find_source()
    if src is None and _REQUIRE:
        raise AssertionError(
            "COREF_REQUIRE_BIT_IDENTITY is set (the unified daemon is in play) but "
            "maverick source was not found — the StandalonePreprocessor drift gate cannot "
            "run, so it would prove nothing. Set MAVERICK_SRC to maverick_model.py. "
            "Refusing to skip the transcription-drift falsifier on a daemon-bearing host.")
    return src


def _fast_tokenizer():
    """The REAL deberta-v3 fast tokenizer maverick uses (DebertaV2TokenizerFast + the two
    SPEAKER special tokens), built the exact maverick way. transformers is torch-free on
    the guest. This is the bit-identity REFERENCE the sentencepiece path must match."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL, use_fast=True, add_prefix_space=True)
    tok.add_special_tokens({"additional_special_tokens": ["[SPEAKER_START]", "[SPEAKER_END]"]})
    return tok


def _fast_tokenize_reference(tok, tokens, eos_indices, speakers=None):
    """maverick.Maverick.tokenize (L155-208) reproduced inline on the REAL fast HF
    tokenizer — the reference the raw-sentencepiece StandalonePreprocessor must match
    bit-for-bit. Returns the same dict shape tokenize() returns. Needs NO maverick source
    (it IS maverick's documented logic), so it is the guest gate for the byte-fallback /
    >512 / unicode battery."""
    from coref_decode_inputs import StandalonePreprocessor
    if speakers is None:
        speakers = ["-"] * len(tokens)
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
    enc = tok(new_tokens, add_special_tokens=True, is_split_into_words=True)
    eos = [
        enc.word_to_tokens(token_to_new_token_map[e - 1]).start
        for e in eos_indices
        if enc.word_to_tokens(token_to_new_token_map[e - 1]) is not None
    ]
    return {
        "input_ids": list(enc["input_ids"]),
        "attention_mask": list(enc["attention_mask"]),
        "subtoken_map": list(enc.word_ids()),
        "new_token_map": new_token_map,
        "eos_mask": StandalonePreprocessor.eos_mask(len(enc["input_ids"]), eos),
    }


def _build_reference(src_path, nlp, tokenizer):
    """Exec maverick's ACTUAL preprocess/tokenize/eos_mask/__sample_type__ source as a
    reference class, with download_load_spacy/sent_tokenize/flatten/np bound to the SAME
    spaCy + nltk the standalone uses (so any difference is logic, not inputs). The
    reference's `self.tokenizer` is the REAL fast HF tokenizer (maverick calls it); the
    standalone uses raw sentencepiece on the SAME spm.model -> equal IFF the reproduction
    is faithful."""
    import numpy as np
    from nltk import sent_tokenize

    src = open(src_path, encoding="utf-8").read()
    tree = ast.parse(src)
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "Maverick")
    wanted = ("__sample_type__", "preprocess", "eos_mask", "tokenize")
    bodies = {}
    for n in cls.body:
        if isinstance(n, ast.FunctionDef) and n.name in wanted:
            bodies[n.name] = textwrap.dedent(ast.get_source_segment(src, n))
    missing = [w for w in wanted if w not in bodies]
    assert not missing, f"maverick source missing methods {missing} in {src_path}"

    def flatten(seq):
        return [item for sublist in seq for item in sublist]

    ns = {"np": np, "download_load_spacy": lambda: nlp,
          "sent_tokenize": sent_tokenize, "flatten": flatten}
    class_src = "class _MavRef:\n" + textwrap.indent(
        "\n".join(bodies[w] for w in wanted), "    ")
    exec(compile(class_src, "<maverick_ref>", "exec"), ns)
    ref = ns["_MavRef"]()
    ref.tokenizer = tokenizer
    return ref


# ===================================================================== PRIMARY gate
def test_standalone_tokenize_matches_fast_tokenizer():
    """BIT-IDENTITY (guest-runnable, NO maverick source): raw-sentencepiece tokenize ==
    the real DebertaV2TokenizerFast, over a battery INCLUDING a >512-subtoken doc, the
    byte-fallback edge (one [UNK] per OOV run), empty-normalising words, and complex
    unicode. input_ids / attention_mask / subtoken_map / eos_mask all IDENTICAL — a
    divergence (the silent byte-fallback drift) reds here."""
    import numpy as np

    from coref_decode_inputs import StandalonePreprocessor

    pre = StandalonePreprocessor.from_pretrained(MODEL)
    tok = _fast_tokenizer()

    # the standalone's structural special-token ids must equal the fast tokenizer's,
    # else input_ids diverge silently (the added-token numbering is part of the contract).
    assert pre.cls_id == tok.cls_token_id
    assert pre.sep_id == tok.sep_token_id
    assert pre.special_token_ids["[SPEAKER_START]"] == tok.convert_tokens_to_ids("[SPEAKER_START]")
    assert pre.special_token_ids["[SPEAKER_END]"] == tok.convert_tokens_to_ids("[SPEAKER_END]")

    n_subtokens_max = 0
    for tokens in WORD_BATTERIES:
        eos_indices = [len(tokens)]  # one sentence -> eos at the end (exercises word_to_tokens)
        # speakers supplied exactly as maverick.preprocess does (["-"]*n); tokenize itself
        # does not default speakers (faithful to maverick — preprocess always supplies them).
        speakers = ["-"] * len(tokens)
        got = pre.tokenize(tokens, eos_indices, speakers=speakers)
        ref = _fast_tokenize_reference(tok, tokens, eos_indices, speakers=speakers)
        n_subtokens_max = max(n_subtokens_max, len(ref["input_ids"]))

        assert list(got["input_ids"]) == ref["input_ids"], (
            f"input_ids drift on {tokens[:6]}...:\n  spm : {got['input_ids']}\n"
            f"  fast: {ref['input_ids']}")
        assert list(got["attention_mask"]) == ref["attention_mask"], "attention_mask drift"
        assert list(got["subtoken_map"]) == ref["subtoken_map"], "subtoken_map(word_ids) drift"
        assert np.array_equal(np.asarray(got["eos_mask"]), np.asarray(ref["eos_mask"])), \
            "eos_mask drift (word_to_tokens start positions diverged)"

    # prove the battery actually exercised the long path (>512 subtokens)
    assert n_subtokens_max > 512, f"battery never exceeded 512 subtokens ({n_subtokens_max})"


# ============================================== maverick-source end-to-end gate
@pytest.mark.skipif(_source_or_fail() is None,
                    reason="maverick source not found (set MAVERICK_SRC); skip only "
                           "allowed when COREF_REQUIRE_BIT_IDENTITY is unset")
def test_standalone_preprocess_is_bit_identical_to_maverick():
    """Full preprocess+tokenize bit-identity vs maverick's ACTUAL source (its tokenize
    bound to the real fast HF tokenizer), over the TEXTS battery incl the >512 doc and
    the unicode doc. Proves the standalone reproduces maverick end to end."""
    from coref_decode_inputs import StandalonePreprocessor, prepare_decode_inputs

    pre = StandalonePreprocessor.from_pretrained(MODEL)
    tok = _fast_tokenizer()
    # the reference shares the EXACT same nlp (standalone's spaCy) + a real fast tokenizer
    # on the SAME model, so a divergence is provably logic, not a different tokenizer build.
    ref = _build_reference(_find_source(), pre.nlp, tok)

    for text in TEXTS:
        di = prepare_decode_inputs(pre, text)                 # standalone (sentencepiece)
        r_tokens, r_eos, r_speakers, r_choff = ref.preprocess(text)
        r_tok = ref.tokenize(r_tokens, r_eos, r_speakers)     # maverick's real logic + fast tok

        assert list(di.input_ids) == list(r_tok["input_ids"]), f"input_ids drift on {text[:40]!r}"
        assert list(di.attention_mask) == list(r_tok["attention_mask"]), "attention_mask drift"
        assert list(di.subtoken_map) == list(r_tok["subtoken_map"]), "subtoken_map drift"
        assert list(di.new_token_map) == list(r_tok["new_token_map"]), "new_token_map drift"
        assert list(di.tokens) == list(r_tokens), "tokens drift"
        # char_offsets: standalone keeps tuples, maverick may produce tuples/lists -> normalise
        assert [tuple(x) for x in di.char_offsets] == [tuple(x) for x in r_choff], "char_offsets drift"
        # eos_mask: standalone is list[list[int]]; maverick is np [S,S] -> compare values
        import numpy as np
        std_mask = np.asarray(di.eos_mask)
        ref_mask = np.asarray(r_tok["eos_mask"])
        assert std_mask.shape == ref_mask.shape, f"eos_mask shape {std_mask.shape} != {ref_mask.shape}"
        assert np.array_equal(std_mask, ref_mask), "eos_mask drift"


def test_standalone_is_self_consistent():
    """Runs without maverick source: structural invariants of the standalone output
    (so the plumbing is exercised even where the reference is unavailable)."""
    from coref_decode_inputs import StandalonePreprocessor, prepare_decode_inputs

    pre = StandalonePreprocessor.from_pretrained(MODEL)
    for text in TEXTS:
        di = prepare_decode_inputs(pre, text)
        s = len(di.input_ids)
        assert len(di.attention_mask) == s
        assert len(di.subtoken_map) == s                      # word_ids() aligns to input_ids
        assert len(di.eos_mask) == s and all(len(row) == s for row in di.eos_mask)
        assert len(di.char_offsets) == len(di.tokens)         # one (start,end) per original token
        # eos_mask is upper-triangular (np.triu): no mass below the diagonal
        assert all(di.eos_mask[i][j] == 0 for i in range(s) for j in range(i))
        # input_ids start with [CLS] and end with [SEP] (the special-token framing)
        assert di.input_ids[0] == pre.cls_id and di.input_ids[-1] == pre.sep_id


if __name__ == "__main__":
    print("maverick source:", _find_source() or "NOT FOUND (end-to-end test will skip)")
    test_standalone_tokenize_matches_fast_tokenizer()
    print("PASS bit-identical to the fast tokenizer (input_ids/attention_mask/"
          "subtoken_map/eos_mask) over the >512 + byte-fallback + unicode battery")
    test_standalone_is_self_consistent()
    print("PASS self-consistent")
    if _source_or_fail():
        test_standalone_preprocess_is_bit_identical_to_maverick()
        print("PASS bit-identical to maverick end to end (input_ids/eos_mask/subtoken_map/"
              "new_token_map/char_offsets/tokens)")
