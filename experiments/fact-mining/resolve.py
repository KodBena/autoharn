#!/usr/bin/env python
"""Turn surface mentions into canonical constants for the fact base.

Two gaps cap the quality of every downstream logic (see README "Honest limits"):
  * entity normalization — 'the Greeks' / 'Greek' / 'Greeks' must be ONE constant;
  * coreference        — 'they' / 'he' / 'it' must resolve to their referent.

This module supplies both as a single `resolver_for(doc) -> key(token)` function:
  - entity-aware + morphological canonicalization (always available, no model);
  - pronoun resolution when the doc carries fastcoref clusters (the --coref path).

The result is a `key` for any token: the canonical constant the logics range over.
The original phrase is kept separately (human-readable); the key is for joins.
"""

from __future__ import annotations

import re

# determiners / possessives / quantifiers stripped from the front of a mention
_DET = {
    "the", "a", "an", "this", "that", "these", "those", "my", "our", "your",
    "his", "her", "its", "their", "some", "any", "all", "almost", "most",
    "each", "every", "no", "both", "such",
}


def _singular(w: str) -> str:
    if len(w) > 3 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if len(w) > 2 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def canonical_key(text: str) -> str:
    """Lowercase, strip leading determiners/punctuation, singularize the head word."""
    s = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w for w in s.split() if w]
    while words and words[0] in _DET:
        words.pop(0)
    if not words:
        return ""
    words[-1] = _singular(words[-1])
    return " ".join(words)


def _clusters(doc):
    try:
        return doc._.coref_clusters or []
    except (AttributeError, KeyError):
        return []  # extension not registered → no coref available


def _char_span(doc, s, e):
    """Tolerant char->Span: handles exclusive vs inclusive end offsets.

    fastcoref gives exclusive ends (slice-style); maverick may give inclusive.
    Try as-is, then end+1, so the same code consumes either engine's clusters.
    """
    return (doc.char_span(s, e, alignment_mode="expand")
            or doc.char_span(s, e + 1, alignment_mode="expand"))


def _pick_representative(spans):
    """Best mention to stand for a cluster — the most constant-like one.

    Prefer (in order): not a pronoun; carries a named entity; not a relative
    clause; and then the SHORTEST such mention (a clean constant beats a long
    descriptive noun phrase, even though both corefer)."""
    def score(sp):
        not_pron = 0 if all(t.pos_ in ("PRON", "DET") for t in sp) else 1
        has_ent = 1 if any(t.ent_type_ for t in sp) else 0
        no_relcl = 0 if any(t.dep_ == "relcl" for t in sp) else 1
        return (not_pron, has_ent, no_relcl, -len(sp.text))  # -len => shorter wins
    return max(spans, key=score)


def build_resolution_map(doc) -> dict[int, str]:
    """token index -> canonical key, for tokens inside a non-representative mention."""
    resmap: dict[int, str] = {}
    for cluster in _clusters(doc):
        spans = [_char_span(doc, s, e) for s, e in cluster]
        spans = [sp for sp in spans if sp is not None]
        if len(spans) < 2:
            continue
        rep = _pick_representative(spans)
        rep_key = canonical_key(rep.text)
        if not rep_key:
            continue
        for sp in spans:
            if sp is rep:
                continue
            for tok in sp:
                resmap[tok.i] = rep_key
    return resmap


def _entity_key(token):
    """Canonical key of the named entity the token belongs to, else None."""
    for e in token.doc.ents:
        if e.start <= token.i < e.end:
            return canonical_key(e.text)
    return None


def resolver_for(doc):
    """Return key(token) -> canonical constant, using coref (if present) + entity norm."""
    resmap = build_resolution_map(doc)

    def key(token):
        if token.i in resmap:           # 1) coref: pronoun -> referent
            return resmap[token.i]
        ek = _entity_key(token)
        if ek:                          # 2) entity normalization
            return ek
        if token.pos_ == "PRON":        # 3) an UNRESOLVED pronoun is not a constant
            return ""                   #    (e.g. authorial 'we', dangling 'which')
        return canonical_key(token.lemma_)  # 4) morphological fallback

    return key


def build_coref_nlp(model: str = "en_core_web_sm"):
    """Local spaCy pipeline with the fastcoref component added."""
    import spacy
    from fastcoref import spacy_component  # noqa: F401  (registers the "fastcoref" pipe)
    nlp = spacy.load(model)
    nlp.add_pipe("fastcoref")
    return nlp
