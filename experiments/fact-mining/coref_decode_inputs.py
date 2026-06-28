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


def prepare_decode_inputs(mav, text: str) -> DecodeInputs:
    """Run maverick's FRONT half (preprocess + tokenize) for one text and return the
    decode inputs. This is the exact prep `capture_fixtures.capture_one` and BOTH
    live coref paths (jax-daemon and batched) need; factoring it here is the
    ADR-0012 P1 single source. Callers that need only a subset (the batched path
    uses just `input_ids`/`attention_mask`) read those fields off the result.

    Byte-identical to the inlined version it replaces: same `mav.preprocess(text)`
    (speakers default None) feeding the same `mav.tokenize(tokens, eos, speakers)`.
    """
    tokens, eos_indices, speakers, char_offsets = mav.preprocess(text)
    tok = mav.tokenize(tokens, eos_indices, speakers)
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
