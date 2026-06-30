#!/usr/bin/env python
"""``SqlStore`` — the REAL persistence adapter (SQLAlchemy Core, NOT the ORM).

Backend-agnostic by construction: one adapter parameterized by an engine URL
serves SQLite (pilot) and psql (prod, the harness ``postgresql+psycopg://`` at
192.168.122.1). No caller branches on backend.

SSOT (ADR-0012 P1). The table DDL is DERIVED from ``schema.store_columns()`` — the
column names and types are NOT re-authored here; ``FieldKind`` is the one owner of
the SQL type, mapped in exactly one place (``_sa_type``). Adding a ``FieldKind``
forces a case here (``assert_never``), never a silent untyped column.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence, assert_never

from sqlalchemy import (Column, Float, Integer, MetaData, String, Table, Text,
                        create_engine, insert, select)
from sqlalchemy.engine import Engine
from sqlalchemy.types import TypeEngine

from schema import Adjudication, FieldKind, Schema, Task


def _sa_type(kind: FieldKind) -> TypeEngine[Any]:
    """The ONE FieldKind -> SQLAlchemy type authority (ADR-0012 P1)."""
    match kind:
        case FieldKind.TEXT:
            return Text()
        case FieldKind.INT:
            return Integer()
        case FieldKind.FLOAT:
            return Float()
    assert_never(kind)


@dataclass
class SqlStore:
    """Persist/load adjudications, backend-agnostic. Construct with an engine URL;
    ``ensure_schema`` builds the schema-derived table; ``persist``/``load`` move
    adjudications with their task context."""

    url: str = "sqlite+pysqlite:///:memory:"
    _engine: Engine = field(init=False)
    _meta: MetaData = field(init=False)
    _tables: dict[str, Table] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._engine = create_engine(self.url)
        self._meta = MetaData()

    def _table(self, schema: Schema) -> Table:
        if schema.table in self._tables:
            return self._tables[schema.table]
        cols: list[Column[Any]] = [
            Column("id", Integer(), primary_key=True, autoincrement=True),
            Column("schema_key", String(128), nullable=False),
            Column("task_id", String(256), nullable=False),
            Column("verdict", String(128), nullable=False),
            Column("row_index", Integer(), nullable=True),
            Column("note", Text(), nullable=False, default=""),
        ]
        for name, kind in schema.store_columns():
            cols.append(Column(name, _sa_type(kind), nullable=True))
        table = Table(schema.table, self._meta, *cols, extend_existing=True)
        self._tables[schema.table] = table
        return table

    def ensure_schema(self, schema: Schema) -> None:
        table = self._table(schema)
        table.create(self._engine, checkfirst=True)

    def persist(self, schema: Schema, task: Task,
                adjudications: Sequence[Adjudication]) -> None:
        table = self._table(schema)
        payload_ctx = {f"payload_{f.name}": task.payload.get(f)
                       for f in schema.payload_fields}
        rows: list[dict[str, object]] = []
        for adj in adjudications:
            row: dict[str, object] = {
                "schema_key": adj.schema_key,
                "task_id": adj.task_id,
                "verdict": adj.verdict.name,
                "row_index": adj.row_index,
                "note": adj.note,
            }
            row.update(payload_ctx)
            # the adjudicated classification cells, when a single row was judged
            if adj.row_index is not None:
                cls = task.classifications[adj.row_index]
                for f in schema.columns:
                    row[f"cls_{f.name}"] = cls.get(f)
            rows.append(row)
        if rows:
            with self._engine.begin() as conn:
                conn.execute(insert(table), rows)

    def load(self, schema: Schema) -> Sequence[Adjudication]:
        table = self._table(schema)
        out: list[Adjudication] = []
        with self._engine.begin() as conn:
            result = conn.execute(
                select(table).where(table.c.schema_key == schema.key).order_by(table.c.id))
            for r in result.mappings():
                ri = r["row_index"]
                # the ONE task-less reconstruction gate (shared with bus.wire.decode):
                # a persisted row is validated identically to a wire frame — verdict
                # membership + row_index/mode consistency — closing the asymmetry where
                # load once validated less than decode.
                out.append(Adjudication.rehydrate(
                    schema,
                    str(r["schema_key"]),
                    str(r["task_id"]),
                    str(r["verdict"]),
                    None if ri is None else int(ri),
                    str(r["note"]),
                ))
        return out
