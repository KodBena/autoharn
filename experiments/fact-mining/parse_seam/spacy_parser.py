#!/usr/bin/env python
"""parse_seam.spacy_parser — the spaCy adapter (the live backend, BEHAVIOR-IDENTICAL to today).

`SpacyParser` is the Port/ACL (ADR-0012 P2) for spaCy: `adapt(doc)` is the ONE place a
spaCy attribute name is read (`doc.sents`, `sent.ents`, `ent.label_`/`.text`/char+token
spans, `tok.pos_`/`dep_`/`lemma_`/`head.i`/`idx`, `doc._.coref_clusters`) — it decodes a
spaCy `Doc` into a neutral `ParsedDoc` carrying EXACTLY those fields. After this adapter,
the extractor names none of them. `parse(text)` loads a local pipeline and adapts its
output; `adapt(doc)` adapts an ALREADY-parsed `Doc` (what the live daemon holds), so the
spaCy code path is preserved byte-for-byte — only its read-site is funnelled here.

IMPORT-LIGHT: spaCy is NOT imported at module scope. `adapt` only reads duck attributes
off the passed object (no import), and `parse` lazy-imports a loader. So `import
parse_seam` (hence `import extract`) stays free of the thinc->torch drag, exactly as
extract.py's existing lazy-`import spacy` discipline requires.
"""

from __future__ import annotations

from typing import Any

from parse_seam.parsed_doc import (
    CorefClusters,
    ParsedDoc,
    ParsedEnt,
    ParsedSent,
    ParsedToken,
)


def _normalize_clusters(raw: Any) -> CorefClusters:
    """Coerce a clusters payload (list-of-list-of-[start,end], or the fastcoref-style
    list-of-list-of-(start,end) attached on `doc._.coref_clusters`) into the neutral
    immutable tuple form. None / empty -> ()."""
    if not raw:
        return ()
    return tuple(
        tuple((int(span[0]), int(span[1])) for span in cluster)
        for cluster in raw
    )


class SpacyParser:
    """The spaCy parse backend. Satisfies `parse_seam.parser.Parser` structurally."""

    def __init__(self, model: str = "en_core_web_sm") -> None:
        self.model = model
        self._nlp: Any = None

    # ---- parse(text): load + pipe + adapt (the from-text entry) -------------------------
    def parse(self, text: str) -> ParsedDoc:
        if self._nlp is None:
            import spacy  # lazy: only when a local pipeline is actually loaded
            self._nlp = spacy.load(self.model)
        return self.adapt(self._nlp(text))

    # ---- adapt(doc): the Port/ACL — spaCy Doc -> neutral ParsedDoc ----------------------
    @staticmethod
    def adapt(doc: Any, coref_clusters: Any = None) -> ParsedDoc:
        """Translate a parsed spaCy `Doc` into a `ParsedDoc`. This is the SINGLE site that
        reads spaCy attribute names; the extractor reads only the neutral fields it fills.

        `coref_clusters` (the daemon's per-doc wire payload) takes precedence when given;
        otherwise any clusters already attached to the Doc (`doc._.coref_clusters`, e.g.
        the local fastcoref pipe) are carried — matching `extract.doc_to_facts`, which
        attaches the param when present and otherwise resolves off whatever the Doc holds.
        """
        tokens = tuple(
            ParsedToken(
                i=tok.i,
                text=tok.text,
                pos=tok.pos_,
                dep=tok.dep_,
                lemma=tok.lemma_,
                head=tok.head.i,   # spaCy's head is a token; we keep only its INDEX
                idx=tok.idx,
            )
            for tok in doc
        )
        ents = tuple(
            ParsedEnt(
                text=e.text,
                label=e.label_,
                start_char=e.start_char,
                end_char=e.end_char,
                start_token=e.start,
                end_token=e.end,
            )
            for e in doc.ents
        )
        sents = tuple(
            ParsedSent(
                index=si,
                text=sent.text,
                start_token=sent.start,
                end_token=sent.end,
            )
            for si, sent in enumerate(doc.sents)
        )

        clusters: CorefClusters
        if coref_clusters is not None:
            clusters = _normalize_clusters(coref_clusters)
        else:
            attached = None
            try:
                attached = doc._.coref_clusters
            except (AttributeError, KeyError):
                attached = None
            clusters = _normalize_clusters(attached)

        return ParsedDoc(text=doc.text, tokens=tokens, ents=ents, sents=sents,
                         coref_clusters=clusters)
