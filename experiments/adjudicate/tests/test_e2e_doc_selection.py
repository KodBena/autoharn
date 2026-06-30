#!/usr/bin/env python
"""End-to-end doc-selection on REAL corpus samples — the brief's LIVE deliverable.

Unlike ``test_loaders_and_instances`` (loaders in isolation) and ``test_store_and_bus``
(store/bus in isolation), this drives the *whole* wired pipeline through the public
``app.run`` entrypoint — real corpus file -> ``RfcLoader``/``UnTeiLoader`` -> the
``InProcessBus`` -> the headless ``Frontend`` -> the ``SqlStore`` DDL -> persisted rows
-> reload — so it proves the four seams compose against the actual on-host data, not a
hand-built task. It writes to a real SQLite *file* (not ``:memory:``) and reloads from a
SECOND, independent ``SqlStore`` connection, so durability across connections is part of
the claim (an in-memory store would pass a weaker test by accident).

Skipped when a corpus root is absent, so the suite still runs off-host."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

import instances as inst
from app import run
from loaders import RFC_ROOT, TEI_ROOT
from schema import AdjudicationMode
from store import SqlStore

# (corpus tag understood by app.run, corpus root, expected payload_source value)
_CORPORA = [
    pytest.param("rfc", RFC_ROOT, "rfc",
                 marks=pytest.mark.skipif(not RFC_ROOT.exists(),
                                          reason="RFC corpus not on this host")),
    pytest.param("tei", TEI_ROOT, "un-tei",
                 marks=pytest.mark.skipif(not TEI_ROOT.exists(),
                                          reason="UNv1.0-TEI corpus not on this host")),
]


@pytest.mark.parametrize("corpus, _root, source_tag", _CORPORA)
def test_doc_selection_e2e_persists_real_corpus_sample(
    corpus: str, _root: Path, source_tag: str, tmp_path: Path
) -> None:
    schema = inst.doc_selection_schema()
    limit = 5
    db_url = f"sqlite+pysqlite:///{tmp_path / f'adj_e2e_{corpus}.db'}"

    persisted = run(corpus, limit, "headless", db_url)

    # the pipeline adjudicated and stored exactly the sampled documents
    assert len(persisted) == limit
    for adj in persisted:
        assert adj.schema_key == schema.key
        # only in-vocabulary verdicts can have been stored (rehydrate gate)
        assert adj.verdict in schema.verdicts
        # doc-selection is SINGLETON: every adjudication names its (only) row
        assert schema.mode is AdjudicationMode.SINGLETON
        assert adj.row_index == 0

    # durability: a SECOND, independent connection sees the same rows
    reloaded = SqlStore(db_url).load(schema)
    assert {a.task_id for a in reloaded} == {a.task_id for a in persisted}

    # the schema-derived payload columns actually carry the corpus' real fields
    store = SqlStore(db_url)
    table = store._table(schema)
    with store._engine.begin() as conn:
        for r in conn.execute(select(table)).mappings():
            assert r["payload_source"] == source_tag
            assert isinstance(r["payload_word_count"], int)
            assert r["payload_text_len"] == len(str(r["payload_body"]))
            # the adjudicated verdict matches the heuristic's stored suggestion column
            # (RulePolicy accepts the model's suggestion verbatim)
            assert r["verdict"] == r["cls_suggested"]
