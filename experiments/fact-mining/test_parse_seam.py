#!/usr/bin/env python
"""test_parse_seam.py — the parse backend is POLYMORPHIC, and the spaCy path is BYTE-IDENTICAL.

Three proofs, matching the seam's three promises:

  1. BYTE-IDENTICAL spaCy path — `extract.doc_to_facts` (which now consumes the neutral
     `parse_seam.ParsedDoc`, decoding a spaCy Doc at the boundary) produces a FactBundle
     bit-for-bit equal to the UNTOUCHED spaCy-native extractor (`extract.extract_triples`
     + `resolve.resolver_for` walked straight off the Doc). The records are discrete
     (strings + int offsets) so the bar is `==`, not a tolerance (ADR-0009). With AND
     without a coref cluster.

  2. ADD-A-BACKEND = ONE FILE — a `StanzaParser.adapt` over a tiny FAKE-Stanza fixture
     (Stanza is host-gated / not on the guest) yields a correct `ParsedDoc`: the 1-based
     per-sentence `head` is flattened to doc-global indices, root -> self, entity char
     spans map to token spans. The MAPPING is what we pin (the live parse is host-only).

  3. ONE EXTRACTOR, MANY BACKENDS — a `ParsedDoc` from `SpacyParser` AND one from the
     fake-Stanza adapter BOTH flow through `extract.doc_to_facts` and yield a FactBundle
     with real records — the extractor names no backend.

Skips the spaCy proofs if en_core_web_sm is unavailable (it is on the generic venv guest).
"""

from __future__ import annotations

import importlib.util

import pytest

import extract
import resolve
from parse_seam import ParsedDoc, SpacyParser, StanzaParser

PARA = "Galen studied medicine in Pergamon. He later treated emperors in Rome."


def _nlp():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


# --- the spaCy-native golden (the UNTOUCHED functions), replicating doc_to_facts' body ---
def _spacy_native_bundle(doc) -> extract.FactBundle:
    key_fn = resolve.resolver_for(doc)
    sents: list[extract.SentRecord] = []
    entities: list[extract.EntityRecord] = []
    temporal: list[extract.TemporalRecord] = []
    for si, sent in enumerate(doc.sents):
        sents.append({"index": si, "text": sent.text.strip()})
        for e in sent.ents:
            entities.append({"sent": si, "text": e.text,
                             "canonical": resolve.canonical_key(e.text), "label": e.label_})
            if e.label_ in ("DATE", "TIME"):
                temporal.append({"sent": si, "text": e.text, "label": e.label_})
    triples: list[extract.TripleRecord] = []
    for t in extract.extract_triples(doc, key_fn):
        triples.append({"sent": t.sent_i, "subj": t.subj, "pred": t.pred, "obj": t.obj,
                        "subj_key": t.subj_key, "obj_key": t.obj_key, "negated": t.negated})
    return {"sents": sents, "entities": entities, "temporal": temporal, "triples": triples}


# ===================================================================== proof 1
def test_spacy_path_byte_identical_no_coref():
    nlp = _nlp()
    if nlp is None:
        pytest.skip("en_core_web_sm unavailable")
    doc = nlp(PARA)
    native = _spacy_native_bundle(nlp(PARA))   # untouched spaCy-native extractor
    seam = extract.doc_to_facts(doc)           # neutral ParsedDoc seam (spaCy decoded)
    assert seam == native
    assert native["entities"] and native["triples"], "fixture must be non-vacuous"


def test_spacy_path_byte_identical_with_coref():
    nlp = _nlp()
    if nlp is None:
        pytest.skip("en_core_web_sm unavailable")
    g0 = PARA.index("Galen"); g1 = g0 + len("Galen")
    h0 = PARA.index("He"); h1 = h0 + len("He")
    clusters = [[[g0, g1], [h0, h1]]]

    native_doc = nlp(PARA)
    resolve.attach_coref_clusters(native_doc, clusters)
    native = _spacy_native_bundle(native_doc)

    seam = extract.doc_to_facts(nlp(PARA), coref_clusters=clusters)
    assert seam == native
    keys = {k for t in native["triples"] for k in (t["subj_key"], t["obj_key"])}
    assert "galen" in keys, "coref must resolve the pronoun to its referent"


# --- a tiny FAKE Stanza Document (duck-typed; no `stanza` import needed) -----------------
class _W:
    def __init__(self, text, upos, deprel, lemma, head, start_char):
        self.text = text; self.upos = upos; self.deprel = deprel
        self.lemma = lemma; self.head = head; self.start_char = start_char


class _S:
    def __init__(self, text, words):
        self.text = text; self.words = words


class _E:
    def __init__(self, text, type_, start_char, end_char):
        self.text = text; self.type = type_
        self.start_char = start_char; self.end_char = end_char


class _Doc:
    def __init__(self, text, sentences, ents):
        self.text = text; self.sentences = sentences; self.ents = ents


def _fake_stanza_doc() -> _Doc:
    # "Galen studied medicine in Pergamon. Galen treated emperors."
    text = "Galen studied medicine in Pergamon. Galen treated emperors."
    s1 = _S("Galen studied medicine in Pergamon.", [
        _W("Galen", "PROPN", "nsubj", "Galen", 2, 0),
        _W("studied", "VERB", "root", "study", 0, 6),
        _W("medicine", "NOUN", "obj", "medicine", 2, 14),
        _W("in", "ADP", "case", "in", 5, 23),
        _W("Pergamon", "PROPN", "obl", "Pergamon", 2, 26),
        _W(".", "PUNCT", "punct", ".", 2, 34),
    ])
    s2 = _S("Galen treated emperors.", [
        _W("Galen", "PROPN", "nsubj", "Galen", 2, 36),
        _W("treated", "VERB", "root", "treat", 0, 42),
        _W("emperors", "NOUN", "obj", "emperor", 2, 50),
        _W(".", "PUNCT", "punct", ".", 2, 58),
    ])
    ents = [_E("Galen", "PERSON", 0, 5), _E("Pergamon", "GPE", 26, 34),
            _E("Galen", "PERSON", 36, 41)]
    return _Doc(text, [s1, s2], ents)


# ===================================================================== proof 2
def test_stanza_adapt_mapping():
    pdoc = StanzaParser.adapt(_fake_stanza_doc())
    assert isinstance(pdoc, ParsedDoc)
    assert len(pdoc.tokens) == 10 and len(pdoc.sents) == 2

    # 1-based per-sentence head flattened to doc-global; root points to itself.
    assert pdoc.tokens[1].text == "studied" and pdoc.tokens[1].head == 1  # root -> self
    assert pdoc.tokens[0].head == 1                                       # Galen -> studied
    assert pdoc.tokens[7].text == "treated" and pdoc.tokens[7].head == 7  # s2 root -> self
    assert pdoc.tokens[6].head == 7 and pdoc.tokens[8].head == 7          # s2 deps -> treated

    # sentence token spans + index
    assert (pdoc.sents[1].index, pdoc.sents[1].start_token, pdoc.sents[1].end_token) == (1, 6, 10)

    # entity char spans mapped to token spans
    spans = {(e.text, e.start_token, e.end_token) for e in pdoc.ents}
    assert ("Galen", 0, 1) in spans and ("Pergamon", 4, 5) in spans and ("Galen", 6, 7) in spans


# ===================================================================== proof 3
def test_both_backends_flow_through_doc_to_facts():
    stanza_pdoc = StanzaParser.adapt(_fake_stanza_doc())
    stanza_facts = extract.doc_to_facts(stanza_pdoc)
    # the SAME extractor consumed a Stanza-derived ParsedDoc, no backend named:
    assert set(stanza_facts) == {"sents", "entities", "temporal", "triples"}
    assert len(stanza_facts["sents"]) == 2
    # entities are dep-label-independent, so they flow even though Stanza's UD relations
    # differ from spaCy's (the documented honest limit for SVO): non-vacuous proof.
    assert {e["text"] for e in stanza_facts["entities"]} == {"Galen", "Pergamon"}

    nlp = _nlp()
    if nlp is None:
        pytest.skip("en_core_web_sm unavailable for the spaCy half")
    spacy_pdoc = SpacyParser.adapt(nlp(PARA))
    assert isinstance(spacy_pdoc, ParsedDoc)
    spacy_facts = extract.doc_to_facts(spacy_pdoc)
    assert set(spacy_facts) == {"sents", "entities", "temporal", "triples"}
    assert spacy_facts["triples"], "spaCy backend must still produce SVO triples"


# ===================================================================== host gate
def test_stanza_parse_is_host_gated():
    if importlib.util.find_spec("stanza") is not None:
        pytest.skip("stanza IS installed here; the host gate is exercised on the guest")
    with pytest.raises(RuntimeError, match="stanza"):
        StanzaParser().parse("Galen studied medicine.")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
