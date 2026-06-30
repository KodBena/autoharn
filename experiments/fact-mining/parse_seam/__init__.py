#!/usr/bin/env python
"""parse_seam — the POLYMORPHIC parse backend for the fact extractor.

The fact-mining PARSE layer used to be welded to spaCy: `extract.doc_to_facts` /
`extract.extract_triples` read spaCy `Doc` attributes by name. This package is the
standardized adapter seam that unwelds it (the same shape as `experiments/impedance`):

  * `ParsedDoc` (+ `ParsedToken`/`ParsedEnt`/`ParsedSent`) — the NEUTRAL parse type the
    extractor consumes (ADR-0012 P8: the type is the contract SSOT);
  * `Parser` — the standardized Protocol seam: `parse(text) -> ParsedDoc` (ADR-0012 P2:
    a new backend is a new adapter behind the port, with ZERO core edits);
  * `SpacyParser` — the spaCy adapter, behavior-identical to today (the live backend);
  * `StanzaParser` — a SECOND adapter proving the seam (host-gated; Stanza is host-only);
  * `resolver_for` — the coref+entity resolver, ported to `ParsedDoc` (mirrors resolve.py).

IMPORT-LIGHT: no framework is imported at package load. Each adapter imports its own
framework lazily, inside its own `parse`, so `import parse_seam` (and `import extract`)
stays free of the thinc->torch drag.
"""

from __future__ import annotations

from parse_seam.parsed_doc import (
    CharSpan,
    CorefClusters,
    ParsedDoc,
    ParsedEnt,
    ParsedSent,
    ParsedToken,
)
from parse_seam.parser import Parser
from parse_seam.resolve_parsed import resolver_for
from parse_seam.spacy_parser import SpacyParser
from parse_seam.stanza_parser import StanzaParser

__all__ = [
    "ParsedDoc",
    "ParsedToken",
    "ParsedEnt",
    "ParsedSent",
    "CharSpan",
    "CorefClusters",
    "Parser",
    "SpacyParser",
    "StanzaParser",
    "resolver_for",
]
