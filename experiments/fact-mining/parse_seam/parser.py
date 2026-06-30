#!/usr/bin/env python
"""parse_seam.parser — THE STANDARDIZED PARSE SEAM (so adding a backend is JUST one file).

`Parser` is the port (ADR-0012 P2): a structural `Protocol` with ONE method,
`parse(text) -> ParsedDoc`. Every parse backend is an adapter that satisfies it BY SHAPE
(no inheritance) — `SpacyParser`, `StanzaParser`, … each live in their own module and
each translate-and-validate their framework's parse into the neutral `ParsedDoc`. The
extractor (`extract.doc_to_facts`) depends only on this seam + `ParsedDoc`, never on a
concrete backend, so a new backend requires ZERO core edits (P2 check (a)).

This module is FRAMEWORK-NEUTRAL: it imports only the neutral type. A concrete adapter
imports its own framework, lazily, inside its own module — mirroring impedance's
`LibAdapter` Protocol (the library-agnostic seam) vs its per-library `lib/*_lib.py`
adapters.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from parse_seam.parsed_doc import ParsedDoc


@runtime_checkable
class Parser(Protocol):
    """The seam every parse backend plugs into. Implement `parse` — and, optionally, a
    backend-specific `adapt(native_doc) -> ParsedDoc` for callers that already hold a
    framework-parsed document (the live daemon holds a spaCy `Doc`). `parse` is the only
    member the seam pins; `adapt` is the adapter's own entry, not part of the contract."""

    def parse(self, text: str) -> ParsedDoc:
        """Parse raw text into the neutral `ParsedDoc` (tokens with dependency + POS +
        lemma + head-index, entities with labels + spans, sentences, coref clusters)."""
        ...
