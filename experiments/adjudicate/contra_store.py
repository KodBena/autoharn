#!/usr/bin/env python
"""``ContraStore`` — the SECOND ``protocols.Store`` adapter (the one the package already
named "designed-for": a non-SQLAlchemy store behind the same protocol), over the psql
``contra`` schema. ``SqlStore`` is UNTOUCHED — this is a new adapter, not a fork.

It is the SINGLE gateway to the ``contra`` schema (ADR-0012 P3 one-owner):
  * ``ensure_schema`` applies ``contra_schema.sql`` (idempotent CREATE … IF NOT EXISTS);
  * ``insert_findings`` writes the detector's rows (``ON CONFLICT DO NOTHING`` —
    re-running on the same doc adds no duplicate);
  * ``findings`` reads them back for the loader (rows → BATCH ``Task``s);
  * ``persist``/``load`` move the verdicts (``contra.adjudication``), via the SAME
    ``Adjudication.rehydrate`` gate ``SqlStore`` uses.

CROSS-PACKAGE coupling is the ``contra.finding`` rows, NOT a Python import: this module
imports nothing from fact-mining. The detector hands it plain string rows
(``Finding.as_row()``); the DSN (the one-home ``spans.DEFAULT_DSN``) and the DDL path are
INJECTED by the runner, so ContraStore stays a self-contained adjudicate-side adapter
(stdlib + psycopg + the package's ``schema``)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import psycopg

from schema import Adjudication, AdjudicationMode, Schema, Task

# the rule's autonomous provisional verdict (a finding means the rule fired). The
# detector's suggestion is always "candidate contradiction", honestly labelled; a
# human/LLM overrides through the same surface.
SUGGESTED_VERDICT = "contradiction"

# the columns the detector writes (the order the INSERT binds).
_FINDING_COLS = ("rule", "subj_key", "pred", "claim_a", "claim_b", "span_a", "span_b", "grounding")


@dataclass
class ContraStore:
    """psql ``contra`` store. ``dsn`` is the injected one-home harness DSN
    (``spans.DEFAULT_DSN``); ``adjudicator`` tags every verdict this store writes
    ('rule:auto' for the RulePolicy run); ``ddl_path`` is the rewindable DDL artifact."""

    dsn: str
    adjudicator: str = "rule:auto"
    ddl_path: Path = Path(__file__).resolve().parent.parent / "fact-mining" / "contra_schema.sql"

    # ---- Store protocol: ensure_schema / persist / load ----------------------------
    def ensure_schema(self, schema: Schema | None = None) -> None:
        """Apply the idempotent ``contra`` DDL (the one home for the schema shape)."""
        ddl = self.ddl_path.read_text(encoding="utf-8")
        with psycopg.connect(self.dsn) as conn:
            conn.execute(ddl)  # multi-statement idempotent DDL, no params
            conn.commit()

    def persist(self, schema: Schema, task: Task,
                adjudications: Sequence[Adjudication]) -> None:
        """Write each adjudication as a ``contra.adjudication`` row; the finding link is
        ``finding_id = int(task_id)`` (the loader set ``task_id = str(finding_id)``)."""
        if not adjudications:
            return
        finding_id = int(task.task_id)
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                for adj in adjudications:
                    cur.execute(
                        "INSERT INTO contra.adjudication (finding_id, verdict, adjudicator, note) "
                        "VALUES (%s, %s, %s, %s)",
                        (finding_id, adj.verdict.name, self.adjudicator, adj.note),
                    )
            conn.commit()

    def load(self, schema: Schema) -> Sequence[Adjudication]:
        """Read the verdicts back as ``Adjudication``s, through the SAME task-less
        ``rehydrate`` gate ``SqlStore.load`` uses (verdict membership + mode/shape).
        BATCH schema → ``row_index=None``."""
        out: list[Adjudication] = []
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT finding_id, verdict, note FROM contra.adjudication ORDER BY adjudication_id")
                rows = cur.fetchall()
        for finding_id, verdict, note in rows:
            out.append(Adjudication.rehydrate(
                schema, schema.key, str(finding_id), str(verdict),
                None if schema.mode is AdjudicationMode.BATCH else 0, str(note)))
        return out

    # ---- the detector + loader seam: insert_findings / findings --------------------
    def insert_findings(self, source_doc: str, rows: Sequence[Mapping[str, str]]) -> int:
        """Idempotent INSERT of detector rows into ``contra.finding``. Returns the number
        of NEW rows (``ON CONFLICT DO NOTHING`` skips a finding already present for this
        doc, so re-running the detector is a no-op)."""
        inserted = 0
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                for r in rows:
                    cur.execute(
                        "INSERT INTO contra.finding "
                        "(source_doc, rule, subj_key, pred, claim_a, claim_b, span_a, span_b, grounding) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (source_doc, rule, subj_key, pred, claim_a, claim_b) DO NOTHING "
                        "RETURNING finding_id",
                        (source_doc, *(r[c] for c in _FINDING_COLS)),
                    )
                    if cur.fetchone() is not None:
                        inserted += 1
            conn.commit()
        return inserted

    def findings(self, source_doc: str) -> list[dict[str, Any]]:
        """Read this doc's findings back (rows → the loader's BATCH ``Task``s)."""
        cols = ("finding_id", "source_doc", "rule", "subj_key", "pred",
                "claim_a", "claim_b", "span_a", "span_b", "grounding")
        out: list[dict[str, Any]] = []
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {', '.join(cols)} FROM contra.finding "
                    "WHERE source_doc = %s ORDER BY finding_id",
                    (source_doc,))
                for row in cur.fetchall():
                    out.append(dict(zip(cols, row)))
        return out
