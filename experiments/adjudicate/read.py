#!/usr/bin/env python
"""``read`` — read a corpus document as PLAIN READABLE PARAGRAPHS (the XML stripped).

This is the ``DocumentSource`` functor (``docsource.py``) instantiated for reading:
``UnTeiSource(...).map(render_paragraphs)`` lifts the readable-text content-morphism
over the UN-TEI source, giving a ``DocumentSource[str]`` whose documents ARE plain
text. The XML is never the maintainer's concern — the functor strips it.

  # read the first UN-TEI document as plain text (paged like ``less`` on a TTY):
  python -m read --corpus un-tei

  # read a SPECIFIC document by its id (the same id a task carries):
  python -m read --corpus un-tei --doc tei:1990:trans:wp_29:1999:14:add_1

  # list the available document ids (no body):
  python -m read --corpus un-tei --list --limit 20

  (also reachable as a subcommand: ``python -m app read --corpus un-tei``)

PAGER. On a TTY the body is paged through the stdlib ``pydoc.pager`` (honors ``$PAGER``
/ ``less``); piped or with ``--no-pager`` it prints plainly. The package's INTERACTIVE
pager is the Textual preview (``frontend_textual``); this read path is the plain-file
analogue and reuses the stdlib pager rather than reinventing one."""

from __future__ import annotations

import argparse
import pydoc
import sys
from typing import Sequence

from docsource import Document, DocumentSource, TeiBody, UnTeiSource


def render_paragraphs(body: TeiBody) -> str:
    """The content-morphism mapped over the source: structured paragraphs -> plain
    readable text. Sentences within a paragraph join with a space; paragraphs are
    separated by a blank line — exactly how a normal text file reads."""
    return "\n\n".join(p.text() for p in body)


def _banner(doc: Document[str]) -> str:
    """The document's header line(s) — id, symbol, title (metadata the functor carried
    through ``map`` unchanged)."""
    lines = [f"# {doc.doc_id}"]
    symbol = doc.meta.get("symbol")
    title = doc.meta.get("title")
    if symbol:
        lines.append(f"# symbol: {symbol}")
    if title:
        lines.append(f"# title:  {title}")
    return "\n".join(lines)


def render_readable(doc: Document[str]) -> str:
    """A full readable document: its banner, a rule, then the plain-text body."""
    return f"{_banner(doc)}\n{'-' * 72}\n\n{doc.content}\n"


def _source(corpus: str, limit: int | None, doc_id: str | None) -> DocumentSource[str]:
    """Build the plain-text source for a corpus — the functor instantiated and mapped.
    Only ``un-tei`` needs un-XML-ing; the seam is open to a second corpus the same way
    (a new ``DocumentSource`` + the SAME ``render_paragraphs``-shaped morphism)."""
    if corpus == "un-tei":
        return UnTeiSource(limit=limit, doc_id=doc_id).map(render_paragraphs)
    raise ValueError(f"unknown corpus {corpus!r} (expected un-tei)")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="read", description="read a corpus document as plain readable paragraphs")
    ap.add_argument("--corpus", choices=["un-tei"], default="un-tei")
    ap.add_argument("--doc", default=None,
                    help="document id to read (default: the first document)")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap how many documents are scanned (with --list)")
    ap.add_argument("--list", action="store_true",
                    help="list available document ids instead of printing a body")
    ap.add_argument("--no-pager", action="store_true",
                    help="print plainly instead of paging through less/$PAGER")
    args = ap.parse_args(argv)

    if args.list:
        listing = _source(args.corpus, args.limit, None)
        for entry in listing.documents():
            print(f"{entry.doc_id}\t{entry.meta.get('symbol', '')}")
        return 0

    # read ONE document (the named one, else the first available)
    source = _source(args.corpus, limit=1 if args.doc is None else None, doc_id=args.doc)
    doc: Document[str] | None = None
    if args.doc is not None:
        try:
            doc = source.get(args.doc)
        except KeyError as e:
            print(str(e), file=sys.stderr)
            return 1
    else:
        for d in source.documents():
            doc = d
            break
    if doc is None:
        print("no readable documents found in this corpus", file=sys.stderr)
        return 1

    text = render_readable(doc)
    if args.no_pager or not sys.stdout.isatty():
        print(text)
    else:
        pydoc.pager(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
