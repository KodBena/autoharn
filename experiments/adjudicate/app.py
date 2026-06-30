#!/usr/bin/env python
"""End-to-end doc-selection runner — the LIVE instantiation (this subproject).

Wires the four seams from ONE schema: a corpus loader builds doc-selection tasks ->
the Bus carries them -> a Frontend (human Textual or headless rule/LLM) adjudicates
-> the Store persists. Every piece derives from ``instances.doc_selection_schema()``;
nothing about the surface, the wire, or the DDL is restated.

  python -m app --corpus rfc --limit 20 --frontend headless --db sqlite+pysqlite:///adj.db
  python -m app --corpus tei --limit 10 --frontend textual
  python -m app read --corpus un-tei --doc tei:1990:trans:wp_29:1999:14:add_1
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

import instances as inst
from bus import InProcessBus
from frontend_headless import HeadlessFrontend, RulePolicy
from loaders import RfcLoader, UnTeiLoader
from protocols import Frontend
from schema import Adjudication, Schema, Task
from store import SqlStore


def _load_tasks(schema: Schema, corpus: str, limit: int) -> list[Task]:
    if corpus == "rfc":
        return list(RfcLoader(limit=limit).tasks(schema))
    if corpus == "tei":
        return list(UnTeiLoader(limit=limit).tasks(schema))
    raise ValueError(f"unknown corpus {corpus!r} (expected rfc|tei)")


def _frontend(kind: str) -> Frontend:
    if kind == "headless":
        # autonomous, no LLM: accept the model's suggested label (RulePolicy)
        return HeadlessFrontend(RulePolicy(inst.DOC_SUGGESTED))
    if kind == "textual":
        from frontend_textual import TextualFrontend  # imported lazily (TTY dependency)
        return TextualFrontend()
    raise ValueError(f"unknown frontend {kind!r} (expected headless|textual)")


def run(corpus: str, limit: int, frontend_kind: str, db_url: str) -> Sequence[Adjudication]:
    schema = inst.doc_selection_schema()
    bus = InProcessBus()
    store = SqlStore(db_url)
    store.ensure_schema(schema)

    for task in _load_tasks(schema, corpus, limit):
        bus.submit(task)

    tasks = list(bus.poll(schema))
    frontend = _frontend(frontend_kind)
    adjudications = frontend.adjudicate(schema, tasks)
    bus.publish(adjudications)

    # persist per-task (so each adjudication carries its task context)
    by_task = {t.task_id: t for t in tasks}
    for adj in adjudications:
        store.persist(schema, by_task[adj.task_id], [adj])

    return store.load(schema)


def main() -> None:
    # ``read`` is a sibling surface over the SAME corpora (read a document as plain
    # paragraphs rather than adjudicate it); dispatch to it before the adjudication
    # argument parser so ``python -m app --corpus ...`` keeps its exact meaning.
    argv = sys.argv[1:]
    if argv and argv[0] == "read":
        from read import main as read_main
        raise SystemExit(read_main(argv[1:]))

    ap = argparse.ArgumentParser(description="doc-selection adjudication end-to-end")
    ap.add_argument("--corpus", choices=["rfc", "tei"], default="rfc")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--frontend", choices=["headless", "textual"], default="headless")
    ap.add_argument("--db", default="sqlite+pysqlite:///:memory:")
    args = ap.parse_args()
    persisted = run(args.corpus, args.limit, args.frontend, args.db)
    print(f"adjudicated + persisted {len(persisted)} record(s) to {args.db}")
    for rec in persisted[:20]:
        print(" ", rec)


if __name__ == "__main__":
    main()
