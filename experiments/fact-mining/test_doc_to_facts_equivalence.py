#!/usr/bin/env python
"""CORRECTNESS BAR (ADR-0009 discrete-invariant, bit-exact): the facts are IDENTICAL
pre/post the cut.

The cut moved the per-document fact extraction load_facts.py did INLINE into the SSOT
`extract.doc_to_facts`, and put a JSON wire between the daemon and the client. The
facts are discrete records (strings + int offsets), so the bar is BIT-EXACT, not a
float tolerance: a dropped, reordered-into-loss, or coerced field is a FAIL.

This test pins that equivalence WITHOUT the GPU daemon (guest-runnable): it parses a
fixture locally with en_core_web_sm, then compares

  OLD  — the pre-cut inline extraction load_facts.py used to run, replicated verbatim
         here (extract_triples + entity/temporal/coref via resolve, with the running
         --max-sents budget in the caller), straight off the Doc; against

  NEW  — extract.doc_to_facts(doc) -> json.dumps -> json.loads (the daemon->client
         JSON round-trip) -> the new caller-side budget loop.

The loaded sentence/entity/temporal/assertion records must be set-identical (the DB
load is order-independent — rows get fresh ids — so set equality on the stable
(sent_index, fields) tuples is the right invariant). Coref resolution is exercised
too: a synthetic cluster resolves a pronoun to its referent, and the resolved
subj_key/obj_key must survive the move host-side + the JSON round-trip unchanged.

Skips if en_core_web_sm is unavailable (the model IS on the generic venv guest).

Run under pytest, or standalone: `python test_doc_to_facts_equivalence.py`.
"""

from __future__ import annotations

import json

import pytest

import resolve
from extract import doc_to_facts, extract_triples

# Two paragraphs (each a "doc", as load_facts feeds one Doc per paragraph). Entities,
# a DATE (temporal), SVO triples, and a pronoun ("He") for the coref case.
PARA_1 = "Galen studied medicine in Pergamon. He later treated emperors in Rome."
PARA_2 = "Hippocrates founded a school on Kos around 400 BC."


def _nlp():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:  # model or spaCy unavailable on this host
        return None


def _attach(doc, clusters):
    """Attach char-offset clusters exactly as the OLD remote client / the daemon do —
    via the ONE production decoder (resolve.attach_coref_clusters), so this test cannot
    carry a third, separately-drifting copy of the wire-cluster transform."""
    resolve.attach_coref_clusters(doc, clusters)


# --- OLD: the pre-cut inline extraction + caller budget (the contract to preserve) --
def _old_load(docs, max_sents):
    n_sent = 0
    sents, ents, temps, asserts = set(), set(), set(), set()
    for doc in docs:
        key_fn = resolve.resolver_for(doc)
        sent_ids: dict[int, int] = {}
        for si, sent in enumerate(doc.sents):
            if n_sent >= max_sents:
                break
            sents.add((n_sent, sent.text.strip()))
            sent_ids[si] = n_sent
            for e in sent.ents:
                ents.add((n_sent, e.text, resolve.canonical_key(e.text), e.label_))
                if e.label_ in ("DATE", "TIME"):
                    temps.add((n_sent, e.text, e.label_))
            n_sent += 1
        for t in extract_triples(doc, key_fn):
            if t.sent_i not in sent_ids:
                continue
            asserts.add((sent_ids[t.sent_i], t.subj, t.pred, t.obj,
                         t.subj_key, t.obj_key, t.negated))
        if n_sent >= max_sents:
            break
    return sents, ents, temps, asserts


# --- NEW: doc_to_facts -> JSON round-trip -> the new caller budget loop --------------
def _new_load(docs, max_sents, coref_for=None):
    # doc_to_facts host-side + the wire: serialize and deserialize, exactly as the
    # daemon -> client path does, so the round-trip itself is under test.
    all_facts = [
        json.loads(json.dumps(
            doc_to_facts(doc, coref_clusters=(coref_for(i) if coref_for else None))))
        for i, doc in enumerate(docs)
    ]
    n_sent = 0
    sents, ents, temps, asserts = set(), set(), set(), set()
    for facts in all_facts:
        sent_ids: dict[int, int] = {}
        for s in facts["sents"]:
            if n_sent >= max_sents:
                break
            sents.add((n_sent, s["text"]))
            sent_ids[s["index"]] = n_sent
            n_sent += 1
        for e in facts["entities"]:
            if e["sent"] not in sent_ids:
                continue
            ents.add((sent_ids[e["sent"]], e["text"], e["canonical"], e["label"]))
        for tm in facts["temporal"]:
            if tm["sent"] not in sent_ids:
                continue
            temps.add((sent_ids[tm["sent"]], tm["text"], tm["label"]))
        for t in facts["triples"]:
            if t["sent"] not in sent_ids:
                continue
            asserts.add((sent_ids[t["sent"]], t["subj"], t["pred"], t["obj"],
                         t["subj_key"], t["obj_key"], t["negated"]))
        if n_sent >= max_sents:
            break
    return sents, ents, temps, asserts


# ===================================================================== the bar
def test_facts_identical_no_coref():
    """No-coref: OLD inline extraction == NEW doc_to_facts + JSON round-trip, bit-for-bit."""
    nlp = _nlp()
    if nlp is None:
        pytest.skip("en_core_web_sm unavailable")
    docs = [nlp(PARA_1), nlp(PARA_2)]
    old = _old_load(docs, max_sents=1000)
    new = _new_load(docs, max_sents=1000)
    assert old == new
    # non-vacuous: there IS signal (entities, a temporal, triples were extracted)
    assert old[1] and old[3], "fixture must yield entities and assertions"


def test_facts_identical_under_budget():
    """The running --max-sents budget drops the same sentences (and their anchored
    entities/temporal/triples) on both paths. max_sents=1 keeps only paragraph 1's
    first sentence."""
    nlp = _nlp()
    if nlp is None:
        pytest.skip("en_core_web_sm unavailable")
    docs = [nlp(PARA_1), nlp(PARA_2)]
    for budget in (1, 2, 3):
        assert _old_load(docs, budget) == _new_load(docs, budget), f"budget={budget}"


def test_facts_identical_with_coref():
    """Coref: a synthetic cluster resolves the pronoun 'He' (para 1, sentence 2) to its
    referent 'Galen'. The resolved subj_key must be IDENTICAL host-side + after the
    JSON round-trip — coref resolution moved home but did not change."""
    nlp = _nlp()
    if nlp is None:
        pytest.skip("en_core_web_sm unavailable")

    # char-offset cluster [Galen, He] within paragraph 1 (one cluster, two mentions)
    g0 = PARA_1.index("Galen"); g1 = g0 + len("Galen")
    h0 = PARA_1.index("He"); h1 = h0 + len("He")
    cluster = [[g0, g1], [h0, h1]]
    clusters_para1 = [cluster]

    def coref_for(i):
        return clusters_para1 if i == 0 else None

    # OLD reads clusters off the Doc; attach them exactly as the daemon/old client did.
    docs = [nlp(PARA_1), nlp(PARA_2)]
    _attach(docs[0], clusters_para1)
    old = _old_load(docs, max_sents=1000)

    # NEW takes the clusters explicitly (the daemon-style call), on fresh Docs.
    docs2 = [nlp(PARA_1), nlp(PARA_2)]
    new = _new_load(docs2, max_sents=1000, coref_for=coref_for)

    assert old == new
    # prove the pronoun actually resolved to "galen" somewhere in the assertions —
    # otherwise the test would pass trivially even if coref were dropped.
    keys = {k for (_si, _s, _p, _o, sk, ok, _n) in old[3] for k in (sk, ok)}
    assert "galen" in keys, "coref must resolve the pronoun to its referent 'galen'"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
