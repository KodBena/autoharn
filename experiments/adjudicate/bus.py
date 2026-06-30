#!/usr/bin/env python
"""Bus adapters: the REAL ``InProcessBus`` and the DESIGNED-FOR ``ZmqBus``.

Per ADR-0012 P7 the SERIALIZATION CONTRACT is kept distinct from the
TRANSPORT/COORDINATION MECHANISM. ``wire`` below is the serialization contract —
the one authoritative codec for classifications/adjudications, derived from the
``Schema`` on BOTH ends (no second hand codec). The two buses share it:

  * ``InProcessBus`` (REAL now) — a degenerate single-process queue. Tasks are
    submitted by a loader, drained by ``poll``; adjudications are collected by
    ``publish``. This is the brief's "degenerate but real" seam.

  * ``ZmqBus`` (DESIGNED-FOR) — the ZMQ-shaped adapter the parent coref project
    orchestrates over. Only the SOCKET is deferred: the bus takes an injected
    ``Transport`` (send/recv of frames), so the reusable part — the wire codec and
    the poll/publish framing — is REAL and testable; binding an actual ``zmq``
    socket is the one injected dependency, kept an adapter because whether it ends
    up ZMQ depends on what claude-code hooks allow.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Protocol, Sequence

from schema import Adjudication, Record, Schema, Task


# ===================================================================== wire codec
class wire:
    """The ONE serialization contract for the bus payloads (ADR-0012 P7). Both ends
    derive field shapes from the ``Schema``, so a frame is just field-name->value
    plus the verdict name — never a re-authored layout."""

    @staticmethod
    def _record_obj(rec: Record) -> dict[str, object]:
        return {f.name: rec.get(f) for f in rec.fields}

    @staticmethod
    def encode_task(task: Task) -> bytes:
        obj = {
            "schema_key": task.schema.key,
            "task_id": task.task_id,
            "payload": wire._record_obj(task.payload),
            "classifications": [wire._record_obj(c) for c in task.classifications],
        }
        return json.dumps(obj).encode("utf-8")

    @staticmethod
    def decode_task(schema: Schema, frame: bytes) -> Task:
        obj = json.loads(frame.decode("utf-8"))
        if obj["schema_key"] != schema.key:
            raise ValueError(f"frame schema {obj['schema_key']!r} != {schema.key!r} "
                             "(ADR-0002: a boundary refuses what it cannot honor).")
        payload = schema.payload({f: obj["payload"][f.name] for f in schema.payload_fields})
        cls = [schema.classification({f: c[f.name] for f in schema.columns})
               for c in obj["classifications"]]
        return schema.task(obj["task_id"], payload, cls)

    @staticmethod
    def encode_adjudication(adj: Adjudication) -> bytes:
        return json.dumps({
            "schema_key": adj.schema_key,
            "task_id": adj.task_id,
            "verdict": adj.verdict.name,
            "row_index": adj.row_index,
            "note": adj.note,
        }).encode("utf-8")

    @staticmethod
    def decode_adjudication(schema: Schema, frame: bytes) -> Adjudication:
        obj = json.loads(frame.decode("utf-8"))
        # the ONE task-less reconstruction gate (shared with store.load): verdict
        # membership + row_index/mode consistency. A malformed frame is refused.
        return Adjudication.rehydrate(schema, obj["schema_key"], obj["task_id"],
                                      obj["verdict"], obj["row_index"], obj.get("note", ""))


# =================================================================== InProcessBus
@dataclass
class InProcessBus:
    """REAL degenerate bus: a single-process queue of tasks in, adjudications out."""

    _inbox: "deque[Task]" = field(default_factory=deque)
    _outbox: list[Adjudication] = field(default_factory=list)

    def submit(self, task: Task) -> None:
        """A loader/classifier places a task (payload + classifications) on the bus."""
        self._inbox.append(task)

    def poll(self, schema: Schema) -> Sequence[Task]:
        out: list[Task] = []
        while self._inbox:
            t = self._inbox.popleft()
            if t.schema.key == schema.key:
                out.append(t)
        return out

    def publish(self, adjudications: Sequence[Adjudication]) -> None:
        self._outbox.extend(adjudications)

    def published(self) -> Sequence[Adjudication]:
        return tuple(self._outbox)


# ===================================================================== ZmqBus
class Transport(Protocol):
    """The one injected dependency the ZMQ adapter needs — send/recv of opaque
    frames. A real ``zmq`` socket satisfies this; so does an in-memory fake (the
    test double), which is what keeps ``ZmqBus`` testable without a broker."""

    def recv_frames(self) -> Sequence[bytes]:
        ...

    def send_frame(self, frame: bytes) -> None:
        ...


@dataclass
class ZmqBus:
    """DESIGNED-FOR ZMQ-shaped bus. The codec and framing are real; ``transport`` is
    the injected socket seam (ADR-0012 P7: bytes-store/fabric kept an adapter). Frame
    contract: each inbound frame is a ``wire.encode_task`` blob; each outbound frame a
    ``wire.encode_adjudication`` blob, one per published adjudication."""

    transport: Transport

    def poll(self, schema: Schema) -> Sequence[Task]:
        return [wire.decode_task(schema, f) for f in self.transport.recv_frames()]

    def publish(self, adjudications: Sequence[Adjudication]) -> None:
        for a in adjudications:
            self.transport.send_frame(wire.encode_adjudication(a))
