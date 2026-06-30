#!/usr/bin/env python
"""parse_seam.stanza_parser — the Stanza adapter (PROOF the seam is real: add-a-backend = one file).

This file is the whole cost of teaching the fact extractor a SECOND parser. It satisfies
`parse_seam.parser.Parser` by translating a Stanza `Document` into the neutral `ParsedDoc`
— the same Port/ACL shape as `SpacyParser`, against Stanza's API (`doc.sentences[*].words`
with 1-based per-sentence `head`, `doc.ents` with char spans). ZERO edits to the extractor.

HOST-GATED (mirrors impedance's honest host-gated adapters). Stanza is a heavy host-side
dependency (it pulls torch) and is NOT installed on this guest. So:

  * `parse(text)` lazy-imports `stanza` and raises a CLEAR, NAMED error if it is absent —
    the host gate is explicit, never a silent no-op (ADR-0002 fail-loud);
  * `adapt(native_doc)` is PURE field-mapping over duck attributes — it imports nothing,
    so its MAPPING LOGIC is unit-tested against a tiny fake-Stanza fixture WITHOUT Stanza
    installed (tests/conftest-free, the honest host-gate: the structural seam is proven on
    the guest; the live parse is proven only where Stanza lives).

HONEST LIMIT (named, not hidden — ADR-0008 Rule 3): Stanza emits Universal-Dependencies
relation labels (`nsubj`/`obj`/`obl`/…) and UD POS, whereas the current SVO extractor keys
on spaCy's label set (`dobj`/`attr`/`oprd`/`dative`/`prep`+`pobj`). The neutral `dep` field
faithfully carries WHATEVER the backend's vocabulary is; this adapter therefore proves the
STRUCTURAL seam (a Stanza parse flows through `doc_to_facts` and yields a `FactBundle`), not
cross-backend triple identity — a UD-aware SVO pass would be its own additive change.
"""

from __future__ import annotations

from typing import Any

from parse_seam.parsed_doc import (
    ParsedDoc,
    ParsedEnt,
    ParsedSent,
    ParsedToken,
)


class StanzaParser:
    """The Stanza parse backend. Satisfies `parse_seam.parser.Parser` structurally."""

    def __init__(self, lang: str = "en",
                 processors: str = "tokenize,pos,lemma,depparse,ner") -> None:
        self.lang = lang
        self.processors = processors
        self._nlp: Any = None

    # ---- parse(text): host-gated load + pipe + adapt -----------------------------------
    def parse(self, text: str) -> ParsedDoc:
        if self._nlp is None:
            try:
                # lazy + HOST-GATED: heavy (torch), host-only. The `import-not-found` is
                # NAMED, not blanket-suppressed (ADR-0012 P8): stanza is genuinely absent
                # on the guest by design — the gate below turns its absence into a loud,
                # named error, and adapt()'s mapping is proven Stanza-free via a fixture.
                import stanza  # type: ignore[import-not-found]
            except ImportError as exc:  # fail loud, named (ADR-0002)
                raise RuntimeError(
                    "StanzaParser.parse requires the `stanza` package, which is NOT "
                    "installed on this host. Install it where Stanza lives (the host has "
                    "it; the guest does not), or use SpacyParser. The MAPPING logic of "
                    "this adapter is host-gate-free and unit-tested via a fake-Stanza "
                    "fixture (StanzaParser.adapt)."
                ) from exc
            self._nlp = stanza.Pipeline(lang=self.lang, processors=self.processors)
        return self.adapt(self._nlp(text))

    # ---- adapt(doc): the Port/ACL — Stanza Document -> neutral ParsedDoc ----------------
    @staticmethod
    def adapt(doc: Any) -> ParsedDoc:
        """Translate a parsed Stanza `Document` into a `ParsedDoc`. Stanza numbers words
        1-based PER SENTENCE with `head==0` meaning root; we flatten to doc-global token
        indices and convert head to a doc-global index (root -> the token's own index, the
        spaCy convention `ParsedDoc` uses). This is the single site that reads Stanza
        attribute names."""
        tokens: list[ParsedToken] = []
        sents: list[ParsedSent] = []

        for si, sent in enumerate(doc.sentences):
            words = list(sent.words)
            sent_start = len(tokens)            # global index of this sentence's first word
            for w in words:
                gi = len(tokens)
                head_local = int(w.head)        # 1-based within sentence; 0 == root
                head_global = gi if head_local == 0 else sent_start + (head_local - 1)
                lemma = w.lemma if w.lemma is not None else w.text
                tokens.append(ParsedToken(
                    i=gi,
                    text=w.text,
                    pos=w.upos,
                    dep=w.deprel,
                    lemma=lemma,
                    head=head_global,
                    idx=int(w.start_char),
                ))
            sents.append(ParsedSent(
                index=si,
                text=sent.text,
                start_token=sent_start,
                end_token=len(tokens),
            ))

        # entities: map each Stanza entity's char span to the doc-global token range it
        # covers (words whose char span lies within the entity's char span).
        ents: list[ParsedEnt] = []
        for ent in getattr(doc, "ents", []) or []:
            s_char, e_char = int(ent.start_char), int(ent.end_char)
            covered = [t for t in tokens if t.idx >= s_char and t.end_char <= e_char]
            if not covered:
                continue
            ents.append(ParsedEnt(
                text=ent.text,
                label=ent.type,
                start_char=s_char,
                end_char=e_char,
                start_token=covered[0].i,
                end_token=covered[-1].i + 1,
            ))

        return ParsedDoc(text=doc.text, tokens=tuple(tokens), ents=tuple(ents),
                         sents=tuple(sents), coref_clusters=())
