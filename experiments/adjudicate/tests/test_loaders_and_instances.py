#!/usr/bin/env python
"""Loaders read the REAL corpora into valid tasks; both schema instances render.

These touch the located corpora (RFC plain-text, UNv1.0-TEI XML) with a tiny limit;
they are skipped if a corpus path is absent so the suite stays runnable off-host."""

from __future__ import annotations

import pytest

import instances as inst
from loaders import RFC_ROOT, TEI_ROOT, RfcLoader, UnTeiLoader, coref_stub_tasks
from schema import AdjudicationMode, render


def test_doc_selection_and_coref_both_construct_and_render() -> None:
    ds = inst.doc_selection_schema()
    assert ds.mode is AdjudicationMode.SINGLETON
    cs = inst.coref_schema()
    assert cs.mode is AdjudicationMode.BATCH
    # coref stub renders a batch task with the grounding rows
    task = coref_stub_tasks(cs)[0]
    model = render(cs, task)
    assert "Coreference adjudication" in model.prompt
    assert model.preview_title == "hook explanation"
    assert len(model.rows) == 2
    assert "antecedent" in model.columns


@pytest.mark.skipif(not RFC_ROOT.exists(), reason="RFC corpus not on this host")
def test_rfc_loader_yields_valid_tasks() -> None:
    s = inst.doc_selection_schema()
    tasks = list(RfcLoader(limit=3).tasks(s))
    assert len(tasks) == 3
    for t in tasks:
        assert t.payload.get(inst.DOC_SOURCE) == "rfc"
        assert isinstance(t.payload.get(inst.DOC_TEXT_LEN), int)
        assert t.payload.get(inst.DOC_TEXT_LEN) == len(str(t.payload.get(inst.DOC_BODY)))
        render(s, t)  # renders without error


@pytest.mark.skipif(not TEI_ROOT.exists(), reason="UNv1.0-TEI corpus not on this host")
def test_tei_loader_yields_valid_tasks() -> None:
    s = inst.doc_selection_schema()
    tasks = list(UnTeiLoader(limit=3).tasks(s))
    assert len(tasks) == 3
    for t in tasks:
        assert t.payload.get(inst.DOC_SOURCE) == "un-tei"
        assert str(t.payload.get(inst.DOC_BODY)).strip() != ""
        render(s, t)
