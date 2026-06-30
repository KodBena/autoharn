#!/usr/bin/env python
"""``DocumentSource`` — a FUNCTOR over document content, in the package idiom.

The loaders (``loaders.py``) read a corpus into doc-selection ``Task``s — they
PROJECT a document down to the doc-selection payload (source/domain/text_len/body)
and throw the document's structure away. Reading a document AS A DOCUMENT (plain
readable paragraphs) is a different ask, and the type-driven answer is not a second
ad-hoc TEI reader bolted next to the loader: it is the observation that "a source of
documents" is a **functor** over the document's content type, and reading is just a
content-transform mapped over it.

THE FUNCTOR (ADR-0000 / ADR-0012 P1). ``DocumentSource[T]`` is an endofunctor on the
category of content types:

  * on objects:    a content type ``T``  ->  ``DocumentSource[T]`` (a source whose
                   documents carry content of type ``T``);
  * on morphisms:  a content map ``f : A -> B``  ->  ``DocumentSource[A].map(f) :
                   DocumentSource[B]`` — STRUCTURE-PRESERVING: it changes ONLY each
                   document's content, never the set of documents, their ids, their
                   metadata, or their order.

It satisfies the functor laws (``tests/test_docsource_functor.py`` asserts both):

  * identity:     ``src.map(lambda c: c)`` yields the same documents as ``src``;
  * composition:  ``src.map(f).map(g)`` == ``src.map(lambda c: g(f(c)))``.

Because ``map`` is the ONLY way content is transformed, a new way to READ a document
(plain paragraphs, a word-frequency table, a token stream, …) is a new content
morphism mapped over the SAME source — no new source, no copy of the parse. The
paragraph reader (``read.py``) is exactly this: ``UnTeiSource(...).map(render)``.

This module is stdlib-only (``xml.etree`` + ``pathlib``) — the device-free, framework-
free reading SSOT, a sibling of ``schema.py``. ``loaders.UnTeiLoader`` derives its
body from the SAME ``parse_tei_paragraphs`` here (ADR-0012 P1: one TEI parse, not two)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Generic, Iterator, Mapping, TypeVar

# Invariant: unlike ``schema.Field``'s phantom covariant parameter, a source's content
# is REAL and is CONSUMED (it is the input of every mapped morphism ``Callable[[T], B]``),
# so the parameter must be invariant — a covariant one would be illegal in the ``map``
# argument position (the exact reason ``schema`` keeps T_co to return positions only).
T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")


# ======================================================================= Document
@dataclass(frozen=True)
class Document(Generic[T]):
    """One document with its identity, metadata, and content of type ``T``. ``map``
    is the functor action on a single object: it transforms the CONTENT and carries
    the id + metadata through unchanged (the structure the functor preserves)."""

    doc_id: str
    meta: Mapping[str, str]
    content: T

    def map(self, fn: Callable[[T], B]) -> "Document[B]":
        return Document(self.doc_id, self.meta, fn(self.content))


# ================================================================= DocumentSource
class DocumentSource(ABC, Generic[T]):
    """The functor: a source of ``Document[T]`` plus the structure-preserving ``map``.
    A concrete source implements ONLY ``documents`` (how it enumerates/parses); ``map``,
    ``get``, and iteration are derived once here for every source (ADR-0012 P1)."""

    @abstractmethod
    def documents(self) -> Iterator[Document[T]]:
        """Enumerate this source's documents, in a stable order."""
        ...

    def map(self, fn: Callable[[T], B]) -> "DocumentSource[B]":
        """Lift a content morphism ``T -> B`` to a source morphism — the functor's
        action on arrows. The result enumerates the SAME documents (same ids/meta/order)
        with their content transformed by ``fn``; nothing else changes."""
        return _MappedSource(self, fn)

    def get(self, doc_id: str) -> Document[T]:
        """The one document with this id — the ``--doc`` selector. Raises ``KeyError``
        if absent (a boundary refusal, not a silent ``None``; ADR-0002)."""
        for d in self.documents():
            if d.doc_id == doc_id:
                return d
        raise KeyError(
            f"no document with id {doc_id!r} in this source — check the id "
            "(run without --doc to list the available ids).")


@dataclass(frozen=True)
class _MappedSource(DocumentSource[B], Generic[A, B]):
    """``src.map(fn)`` — the mapped functor. Holds the upstream source and the content
    morphism; enumerating it maps ``fn`` over each upstream document. Private: callers
    build it through ``DocumentSource.map`` only."""

    src: DocumentSource[A]
    fn: Callable[[A], B]

    def documents(self) -> Iterator[Document[B]]:
        for d in self.src.documents():
            yield d.map(self.fn)


# =================================================== TEI structured content + parse
@dataclass(frozen=True)
class Paragraph:
    """A readable paragraph: its ordered sentences (the TEI ``<p>``'s ``<s>`` texts).
    ``text`` is the readable rendering — sentences joined by a single space."""

    sentences: tuple[str, ...]

    def text(self) -> str:
        return " ".join(self.sentences)


# The TEI document's readable content: its body paragraphs in document order. This is
# the structured content type ``UnTeiSource`` carries; a reader maps it to plain text.
TeiBody = tuple[Paragraph, ...]

TEI_ROOT = Path("/home/bork/distill/UNv1.0-TEI")


def _sentence_text(s: ET.Element) -> str:
    """A sentence's text. ``<s>`` carries direct text; ``itertext`` folds in any
    inline children so no readable token is dropped (then whitespace-normalized)."""
    return " ".join("".join(s.itertext()).split())


def parse_tei_paragraphs(root: ET.Element) -> TeiBody:
    """The ONE TEI body parse (ADR-0012 P1) — used by the reader AND by
    ``loaders.UnTeiLoader``. SCOPED to ``text/body``: the readable document, NOT the
    ``teiHeader`` (whose ``<p>`` disclaimer would otherwise leak into the body). Empty
    paragraphs are dropped so the rendering has no blank gaps."""
    body = root.find("text/body")
    if body is None:
        return ()
    out: list[Paragraph] = []
    for p in body.findall("p"):
        sentences = tuple(t for t in (_sentence_text(s) for s in p.findall("s")) if t)
        if sentences:
            out.append(Paragraph(sentences))
    return tuple(out)


def parse_tei_meta(root: ET.Element) -> dict[str, str]:
    """The document's header metadata: ``symbol`` (the UN document symbol idno),
    ``title``, and ``domain`` (the doc-selection domain field — first ``<term>``
    keyword slugged, else the symbol prefix, else ``un-document``). One header parse,
    shared by the reader's banner and the loader's payload (ADR-0012 P1)."""
    meta: dict[str, str] = {}
    title = root.find(".//titleStmt/title")
    if title is not None and title.text:
        meta["title"] = title.text.strip()
    symbol = ""
    for idno in root.iter("idno"):
        if idno.get("type") == "symbol" and idno.text:
            symbol = idno.text.strip()
            break
    if symbol:
        meta["symbol"] = symbol
    term = root.find(".//term")
    if term is not None and term.text:
        meta["domain"] = term.text.strip().lower().replace(" ", "-")[:64]
    elif symbol:
        meta["domain"] = symbol.split("/")[0].strip().lower()
    else:
        meta["domain"] = "un-document"
    return meta


def tei_doc_id(root_dir: Path, path: Path) -> str:
    """The stable id for a TEI file — IDENTICAL to ``loaders.UnTeiLoader``'s task id
    (``tei:<relpath-with-colons>``), so a ``--doc`` id read here names the same
    document an adjudication task carries."""
    rel = path.relative_to(root_dir).with_suffix("")
    return "tei:" + str(rel).replace("/", ":")


@dataclass(frozen=True)
class UnTeiSource(DocumentSource[TeiBody]):
    """The UN-TEI instantiation of the functor: a ``DocumentSource`` whose content is
    each document's structured body paragraphs. ``map`` a reader over it (``read.py``)
    to get a ``DocumentSource[str]`` of plain readable text. ``limit``/``doc_id`` are
    optional filters; documents enumerate in sorted-path order (stable)."""

    root: Path = TEI_ROOT
    limit: int | None = None
    doc_id: str | None = field(default=None)

    def documents(self) -> Iterator[Document[TeiBody]]:
        n = 0
        for p in sorted(self.root.rglob("*.xml")):
            if self.limit is not None and n >= self.limit:
                return
            doc_id = tei_doc_id(self.root, p)
            if self.doc_id is not None and doc_id != self.doc_id:
                continue
            try:
                root = ET.parse(p).getroot()
            except ET.ParseError:
                continue
            paras = parse_tei_paragraphs(root)
            if not paras:
                continue
            yield Document(doc_id, parse_tei_meta(root), paras)
            n += 1
