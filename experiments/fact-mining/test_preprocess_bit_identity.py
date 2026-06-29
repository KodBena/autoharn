#!/usr/bin/env python
"""Bit-identity falsifier: StandalonePreprocessor == maverick's preprocess+tokenize.

SUB-TASK 2 gate. The unified daemon cannot import maverick (torch), so it reimplements
maverick's preprocess/tokenize/eos_mask front half in `StandalonePreprocessor`. P1/P7
say a reimplementation across a boundary is honest ONLY if a mechanism keeps the copy
from drifting (ADR-0011). This is that mechanism on the GUEST.

It does NOT compare a copy to another copy: it extracts maverick's ACTUAL method source
(`preprocess`, `tokenize`, `eos_mask`, `__sample_type__`) from the on-disk
`maverick/models/maverick_model.py` and execs it as a reference class, then runs the
reference AND `StandalonePreprocessor` on the SAME spaCy nlp + the SAME HF tokenizer, and
asserts the decode inputs are IDENTICAL: input_ids, attention_mask, eos_mask,
subtoken_map, new_token_map, char_offsets, tokens. Same tokenizer + same logic => equal
by construction; this proves the logic was copied faithfully (the only thing the guest
can prove — the end-to-end cluster authority is the HOST --coref-verify).

The reference uses maverick's real bytes, so this catches a transcription slip in the
standalone. It does NOT need the maverick model/checkpoint (these four methods are pure
given a tokenizer + spaCy), so it runs without torch weights — but it DOES read maverick's
source file, found via $MAVERICK_SRC, the pip install, or a local extraction.
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
TEXTS = [
    "John saw Mary. He waved at her happily.",
    "Marie Curie discovered radium; she won two Nobel Prizes. The committee honored her work.",
    "It's 3.14. Mr. Smith's dog—the big one—ran. They chased it.",
    "The cat sat on the mat.",
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
# skips — the guest legitimately may lack maverick source.
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


def _build_reference(src_path, nlp, tokenizer):
    """Exec maverick's ACTUAL preprocess/tokenize/eos_mask/__sample_type__ source as a
    reference class, with download_load_spacy/sent_tokenize/flatten/np bound to the SAME
    spaCy + nltk the standalone uses (so any difference is logic, not inputs)."""
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


@pytest.mark.skipif(_source_or_fail() is None,
                    reason="maverick source not found (set MAVERICK_SRC); skip only "
                           "allowed when COREF_REQUIRE_BIT_IDENTITY is unset")
def test_standalone_preprocess_is_bit_identical_to_maverick():
    from coref_decode_inputs import StandalonePreprocessor, prepare_decode_inputs

    pre = StandalonePreprocessor.from_pretrained(MODEL)
    # the reference must share the EXACT same nlp + tokenizer objects as the standalone,
    # so a divergence is provably logic, not a different tokenizer build.
    ref = _build_reference(_find_source(), pre.nlp, pre.tokenizer)

    for text in TEXTS:
        di = prepare_decode_inputs(pre, text)                 # standalone
        r_tokens, r_eos, r_speakers, r_choff = ref.preprocess(text)
        r_tok = ref.tokenize(r_tokens, r_eos, r_speakers)     # maverick's real bytes

        assert list(di.input_ids) == list(r_tok["input_ids"]), f"input_ids drift on {text!r}"
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


if __name__ == "__main__":
    src = _source_or_fail()  # raises if COREF_REQUIRE_BIT_IDENTITY set and source absent
    print("maverick source:", src or "NOT FOUND (bit-identity test will skip)")
    test_standalone_is_self_consistent()
    print("PASS self-consistent")
    if src:
        test_standalone_preprocess_is_bit_identical_to_maverick()
        print("PASS bit-identical to maverick (input_ids/eos_mask/subtoken_map/"
              "new_token_map/char_offsets/tokens)")
