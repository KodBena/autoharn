#!/usr/bin/env python
"""The three protocol SEAMS (ADR-0012 P2 / P12): Frontend, Bus, Store.

Each seam is an explicit ``Protocol`` with its dependency injected — never an
import-coupling or a reach into an implementation's internals. Per the
structural-hygiene rule "every seam is a protocol with >=1 real adapter and the
second designed-for", each protocol below names, in its docstring, the adapter
that is REAL now and the one DESIGNED-FOR next:

  * Frontend — render(schema, task-batch) -> adjudications.
      REAL now:        TextualFrontend (human TUI) AND HeadlessFrontend (policy-
                       driven, the LLM-driver mechanism) — TWO real adapters, both
                       deriving their surface from the SAME ``render_model``.
      designed-for:    a web/HTTP surface (same protocol, remote transport).

  * Bus — classifications IN / adjudications OUT.
      REAL now:        InProcessBus (degenerate single-process queue — the brief's
                       "the bus is degenerate here but must be a real seam").
      designed-for:    ZmqBus (ZMQ-shaped) for the parent coref project's
                       orchestration; kept an adapter because whether it ends up
                       ZMQ depends on what claude-code hooks allow.

  * Store — persist/load, backend-agnostic.
      REAL now:        SqlStore over SQLite (pilot) AND psql (prod) through ONE
                       SQLAlchemy Core adapter (the DDL derived from the schema).
      designed-for:    a non-SQL store (e.g. JSONL) behind the same protocol.

A protocol takes the ``Schema`` as data (never a subclass to edit); a new Frontend
/ Bus / Store is a new implementation behind the seam with ZERO edits to the
schema or to the other seams — the env<->Policy inversion ADR-0012 P2 mandates.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from schema import Adjudication, Schema, Task


@runtime_checkable
class Frontend(Protocol):
    """The human-OR-LLM adjudication surface. ONE method: present a batch of tasks
    for a schema and return the adjudications. The LLM driver is NOT a separate code
    path — it is a Frontend implementation (HeadlessFrontend) driven programmatically,
    so "autonomous Sonnet runs it" and "a human runs it" are two adapters of this one
    seam, both consuming ``schema.render`` (no second source of truth)."""

    def adjudicate(self, schema: Schema, tasks: Sequence[Task]) -> Sequence[Adjudication]:
        ...


@runtime_checkable
class Bus(Protocol):
    """The message seam: classifications arrive (the unsupervised model's
    suggestions), adjudications depart. Degenerate in this subproject (nothing to
    orchestrate) but a REAL seam, ZMQ-shaped, because the parent coref project
    orchestrates the NLP service's knowledge-grounding rows over it.

    ``poll`` returns the tasks currently awaiting adjudication (built from the
    classifications on the wire); ``publish`` emits the rendered adjudications."""

    def poll(self, schema: Schema) -> Sequence[Task]:
        ...

    def publish(self, adjudications: Sequence[Adjudication]) -> None:
        ...


@runtime_checkable
class Store(Protocol):
    """The persistence seam, backend-agnostic. ``ensure_schema`` materializes the
    table DERIVED from the schema (``schema.store_columns``); ``persist`` writes
    adjudications with their task context; ``load`` reads them back. The same
    protocol serves SQLite (pilot) and psql (prod) through one SQLAlchemy Core
    adapter parameterized by engine URL — no per-backend branch in any caller."""

    def ensure_schema(self, schema: Schema) -> None:
        ...

    def persist(self, schema: Schema, task: Task, adjudications: Sequence[Adjudication]) -> None:
        ...

    def load(self, schema: Schema) -> Sequence[Adjudication]:
        ...
