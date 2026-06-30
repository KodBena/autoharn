#!/usr/bin/env python
"""Document-source loaders — read the real corpora into doc-selection ``Task``s.

Located corpora (verified on host):
  * RFCs:      /home/bork/distill/rfc/rfc*.txt   (~9.8k files, plain text)
  * UNv1.0-TEI: /home/bork/distill/UNv1.0-TEI/<year>/<body>/.../*.xml  (TEI.2 XML)

DOC-SOURCE FIELD EXTRACTION PLAN (the doc-selection payload fields):
  source     — literal 'rfc' | 'un-tei'
  domain     — RFC: the 'Category:' header line slug (standards-track / informational /
               experimental / best-current-practice / historic), else 'rfc';
               TEI: the first ``<term>`` keyword (or the ``idno type="symbol"`` prefix),
               else 'un-document'.
  text_len   — len(body) in characters
  word_count — len(body.split())
  body       — RFC: the whole file text; TEI: the ``<s>`` sentence texts joined.

Each document is paired with ONE unsupervised CLASSIFICATION (a placeholder heuristic
classifier standing in for the model whose suggestions arrive over the Bus) → a
one-row SINGLETON task. The heuristic is deliberately simple and is NOT the point: it
is the suggestion a human/LLM adjudicates. Swapping it for a real model is a loader
change with zero schema/Frontend/Store edits.

The coref stub grounding source builds a BATCH task with placeholder mention-pair
rows — the coref schema is DEFINED and exercised, but NOT wired to the (not-yet-built)
hook (brief scope)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import instances as inst
from docsource import TEI_ROOT as TEI_ROOT  # re-exported: callers import the root here
from docsource import parse_tei_meta, parse_tei_paragraphs, tei_doc_id
from schema import Schema, Task

RFC_ROOT = Path("/home/bork/distill/rfc")

_CATEGORY = re.compile(r"^\s*Category:\s*(.+?)\s*$", re.MULTILINE)
_CATEGORY_SLUG = {
    "standards track": "standards-track",
    "informational": "informational",
    "experimental": "experimental",
    "best current practice": "best-current-practice",
    "historic": "historic",
}


def _heuristic_suggestion(word_count: int) -> tuple[str, str, float]:
    """Placeholder unsupervised classifier: a length-band heuristic. Returns
    (suggested-verdict-name, rationale, score). Stands in for the model's bus
    suggestion; intentionally trivial."""
    if word_count < 50:
        return ("exclude", "very short — likely boilerplate/stub -> exclude", 0.2)
    if word_count > 200_000:
        return ("exclude", "extremely long — likely an index/aggregate -> exclude", 0.3)
    return ("include", "substantive length, in-band -> include", 0.8)


def _doc_task(schema: Schema, task_id: str, source: str, domain: str, body: str) -> Task:
    text_len = len(body)
    word_count = len(body.split())
    suggested, rationale, score = _heuristic_suggestion(word_count)
    payload = schema.payload({
        inst.DOC_SOURCE: source,
        inst.DOC_DOMAIN: domain,
        inst.DOC_TEXT_LEN: text_len,
        inst.DOC_WORD_COUNT: word_count,
        inst.DOC_BODY: body,
    })
    classification = schema.classification({
        inst.DOC_SUGGESTED: suggested,
        inst.DOC_RATIONALE: rationale,
        inst.DOC_SCORE: score,
    })
    return schema.task(task_id, payload, [classification])


# ----------------------------------------------------------------------- RFC loader
@dataclass
class RfcLoader:
    """Read RFC plain-text files into doc-selection tasks."""

    root: Path = RFC_ROOT
    limit: int | None = None

    def _domain(self, text: str) -> str:
        m = _CATEGORY.search(text[:4000])
        if m:
            return _CATEGORY_SLUG.get(m.group(1).strip().lower(), "rfc")
        return "rfc"

    def tasks(self, schema: Schema) -> Iterator[Task]:
        files = sorted(p for p in self.root.glob("rfc*.txt") if p.is_file())
        n = 0
        for p in files:
            if self.limit is not None and n >= self.limit:
                return
            text = p.read_text(encoding="latin-1", errors="replace")
            yield _doc_task(schema, p.stem, "rfc", self._domain(text), text)
            n += 1


# ------------------------------------------------------------------ UN-TEI loader
@dataclass
class UnTeiLoader:
    """Parse UNv1.0-TEI ``TEI.2`` XML into doc-selection tasks. The body + domain come
    from the SAME ``docsource`` TEI parse the ``read`` command uses (ADR-0012 P1: one
    TEI parse, not a second copy here) — the loader joins the structured paragraphs
    into the flat body the doc-selection payload/preview wants."""

    root: Path = TEI_ROOT
    limit: int | None = None

    def tasks(self, schema: Schema) -> Iterator[Task]:
        n = 0
        for p in sorted(self.root.rglob("*.xml")):
            if self.limit is not None and n >= self.limit:
                return
            try:
                root = ET.parse(p).getroot()
            except ET.ParseError:
                continue
            paras = parse_tei_paragraphs(root)
            if not paras:
                continue
            body = " ".join(par.text() for par in paras)
            domain = parse_tei_meta(root)["domain"]
            yield _doc_task(schema, tei_doc_id(self.root, p), "un-tei", domain, body)
            n += 1


# ----------------------------------------------------- coref stub grounding source
def coref_stub_tasks(schema: Schema) -> list[Task]:
    """A DEFINED-not-wired coref batch task with placeholder knowledge-grounding rows.
    Stands in for the NLP service's grounding output; proves the BATCH coref schema is
    exercisable without the (unbuilt) claude-code hook."""
    payload = schema.payload({
        inst.COREF_CONTEXT: "The committee reviewed the report. It found the measures adequate.",
        inst.COREF_EXPLANATION: ("Mention 'It' (sent 2) is a candidate anaphor. Antecedents under "
                                 "consideration: 'The committee' and 'the report'. Grounding from "
                                 "the NLP service's knowledge rows below."),
        inst.COREF_DOC: "tei:2002:cat:c:66",
    })
    rows = [
        schema.classification({
            inst.COREF_ANTECEDENT: "The committee", inst.COREF_ANAPHOR: "It",
            inst.COREF_GROUNDING: "subject-salience", inst.COREF_CONFIDENCE: 0.71}),
        schema.classification({
            inst.COREF_ANTECEDENT: "the report", inst.COREF_ANAPHOR: "It",
            inst.COREF_GROUNDING: "semantic-role:reviewed-obj", inst.COREF_CONFIDENCE: 0.52}),
    ]
    return [schema.task("coref-stub-1", payload, rows)]
