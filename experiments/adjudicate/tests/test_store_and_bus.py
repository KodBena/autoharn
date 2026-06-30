#!/usr/bin/env python
"""Store roundtrip (DDL derived from the schema) and Bus seams (both adapters)."""

from __future__ import annotations

from typing import Sequence

import instances as inst
from bus import InProcessBus, ZmqBus, wire
from frontend_headless import HeadlessFrontend, RulePolicy
from loaders import _doc_task
from schema import Adjudication, Schema, Task
from store import SqlStore


def _task() -> tuple[Schema, Task]:
    s = inst.doc_selection_schema()
    return s, _doc_task(s, "d1", "rfc", "standards-track", "word " * 100)


def test_store_roundtrip_and_derived_columns() -> None:
    s, task = _task()
    store = SqlStore("sqlite+pysqlite:///:memory:")
    store.ensure_schema(s)
    fe = HeadlessFrontend(RulePolicy(inst.DOC_SUGGESTED))
    adjs = fe.adjudicate(s, [task])
    store.persist(s, task, adjs)
    loaded = store.load(s)
    assert len(loaded) == 1
    assert loaded[0].verdict.name == "include"
    assert loaded[0].task_id == "d1"
    # the DDL carried the schema-derived columns
    table = store._table(s)
    colnames = set(table.c.keys())
    assert "payload_source" in colnames and "payload_word_count" in colnames
    assert "cls_suggested" in colnames and "cls_score" in colnames


def test_inprocess_bus_submit_poll_publish() -> None:
    s, task = _task()
    bus = InProcessBus()
    bus.submit(task)
    polled: Sequence[Task] = bus.poll(s)
    assert [t.task_id for t in polled] == ["d1"]
    assert bus.poll(s) == []  # drained
    adj = Adjudication.make(s, task, s.verdicts.member("include"), row_index=0)
    bus.publish([adj])
    assert [a.verdict.name for a in bus.published()] == ["include"]


def test_zmq_wire_codec_roundtrips_task_and_adjudication() -> None:
    """The DESIGNED-FOR ZmqBus over a fake transport: the wire codec (the real,
    reusable serialization contract) roundtrips a task and an adjudication; only the
    socket is deferred."""
    s, task = _task()

    class FakeTransport:
        def __init__(self) -> None:
            self.sent: list[bytes] = []
            self.inbound: list[bytes] = [wire.encode_task(task)]

        def recv_frames(self) -> Sequence[bytes]:
            return list(self.inbound)

        def send_frame(self, frame: bytes) -> None:
            self.sent.append(frame)

    tr = FakeTransport()
    bus = ZmqBus(tr)
    tasks = bus.poll(s)
    assert [t.task_id for t in tasks] == ["d1"]
    assert tasks[0].payload.get(inst.DOC_SOURCE) == "rfc"
    adj = Adjudication.make(s, tasks[0], s.verdicts.member("exclude"), row_index=0)
    bus.publish([adj])
    decoded = wire.decode_adjudication(s, tr.sent[0])
    assert decoded.verdict.name == "exclude"
    assert decoded.task_id == "d1"


def test_rehydrate_is_the_one_taskless_gate() -> None:
    """store.load and wire.decode share ONE reconstruction gate; both refuse a
    mode/shape-inconsistent record identically (no per-site validation subset)."""
    import pytest

    from schema import Adjudication
    s = inst.doc_selection_schema()           # SINGLETON
    cor = inst.coref_schema()                 # BATCH
    # SINGLETON row with a null row_index is refused
    with pytest.raises(ValueError, match="row_index is required"):
        Adjudication.rehydrate(s, s.key, "d1", "include", None, "")
    # BATCH row carrying a row_index is refused
    with pytest.raises(ValueError, match="must be None"):
        Adjudication.rehydrate(cor, cor.key, "c1", "coreferent", 0, "")
    # a rogue verdict is refused
    with pytest.raises(KeyError, match="not in this schema"):
        Adjudication.rehydrate(s, s.key, "d1", "inclde", 0, "")
    # a well-formed row rehydrates
    ok = Adjudication.rehydrate(s, s.key, "d1", "include", 0, "human")
    assert ok.verdict.name == "include" and ok.row_index == 0
