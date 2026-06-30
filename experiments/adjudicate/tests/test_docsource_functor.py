#!/usr/bin/env python
"""The ``DocumentSource`` functor — laws + the UN-TEI reading instantiation.

Two things are proved:
  * the FUNCTOR LAWS (identity, composition) hold for ``DocumentSource.map`` over a
    pure in-memory source (no corpus needed) — the structure-preservation the design
    claims is checked, not asserted in prose;
  * the UN-TEI instantiation reads a REAL document as plain paragraphs with the XML
    stripped and the ``teiHeader`` disclaimer NOT leaking into the body (skipped when
    the corpus is absent, like the other corpus-touching tests)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator, TypeVar

import pytest

from docsource import (TEI_ROOT, Document, DocumentSource, Paragraph, TeiBody,
                       UnTeiSource, parse_tei_paragraphs)
from read import render_paragraphs, render_readable


@dataclass(frozen=True)
class _FakeSource(DocumentSource[int]):
    """A pure in-memory source of int content — enough to exercise the functor laws
    with no I/O."""

    values: tuple[int, ...]

    def documents(self) -> Iterator[Document[int]]:
        for i, v in enumerate(self.values):
            yield Document(f"d{i}", {"k": str(v)}, v)


_S = TypeVar("_S")


def _snapshot(src: DocumentSource[_S]) -> list[tuple[str, dict[str, str], _S]]:
    return [(d.doc_id, dict(d.meta), d.content) for d in src.documents()]


def test_functor_identity_law() -> None:
    src = _FakeSource((1, 2, 3))
    mapped = src.map(lambda c: c)
    # same documents: same ids, same meta, same content, same order
    assert _snapshot(mapped) == _snapshot(src)


def test_functor_composition_law() -> None:
    src = _FakeSource((1, 2, 3))
    f: Callable[[int], int] = lambda c: c + 1
    g: Callable[[int], int] = lambda c: c * 10
    two_steps = src.map(f).map(g)
    one_step = src.map(lambda c: g(f(c)))
    assert _snapshot(two_steps) == _snapshot(one_step)


def test_map_preserves_structure_changes_only_content() -> None:
    src = _FakeSource((5, 6))
    mapped = src.map(lambda c: f"<{c}>")
    before = list(src.documents())
    after = list(mapped.documents())
    assert [d.doc_id for d in after] == [d.doc_id for d in before]
    assert [dict(d.meta) for d in after] == [dict(d.meta) for d in before]
    assert [d.content for d in after] == ["<5>", "<6>"]


def test_render_paragraphs_is_plain_readable_text() -> None:
    body: TeiBody = (Paragraph(("First sentence.", "Second sentence.")),
                     Paragraph(("Lone line.",)))
    assert render_paragraphs(body) == "First sentence. Second sentence.\n\nLone line."


def test_get_refuses_unknown_id() -> None:
    src = _FakeSource((1,))
    with pytest.raises(KeyError):
        src.get("nope")


@pytest.mark.skipif(not TEI_ROOT.exists(), reason="UNv1.0-TEI corpus not on this host")
def test_un_tei_reads_a_real_document_as_plain_paragraphs() -> None:
    text_source = UnTeiSource(limit=1).map(render_paragraphs)
    doc = next(iter(text_source.documents()))
    # the content is plain text — no XML angle brackets survived the functor
    assert "<" not in doc.content and ">" not in doc.content
    assert doc.content.strip() != ""
    assert doc.doc_id.startswith("tei:")
    # render_readable adds a banner carrying the id the functor preserved
    out = render_readable(doc)
    assert doc.doc_id in out


@pytest.mark.skipif(not TEI_ROOT.exists(), reason="UNv1.0-TEI corpus not on this host")
def test_body_parse_excludes_tei_header_disclaimer() -> None:
    # the availability disclaimer lives in teiHeader/<p>; scoping to text/body must
    # keep it OUT of the readable paragraphs (the latent bug a whole-tree iter hides)
    import xml.etree.ElementTree as ET

    for p in sorted(TEI_ROOT.rglob("*.xml"))[:50]:
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        paras = parse_tei_paragraphs(root)
        joined = render_paragraphs(paras)
        if joined:
            assert "shall be respected in regard to the Corpus" not in joined
