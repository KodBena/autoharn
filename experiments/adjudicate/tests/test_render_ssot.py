#!/usr/bin/env python
"""ONE schema drives BOTH surfaces with no second source of truth (ADR-0012 P1).

The headless transcript and the Textual widgets are both projections of the SAME
``render(schema, task)`` render-model. These tests assert that equality: the
transcript carries exactly the render-model's prompt/preview/rows, and the Textual
app (driven headlessly via Textual's ``run_test`` pilot) shows the same prompt and
row count and returns the verdict the keypress selected."""

from __future__ import annotations

import asyncio

import instances as inst
from frontend_textual import _AdjudicateApp
from loaders import _doc_task
from schema import Adjudication, Schema, Task, render


def _one_task() -> tuple[Schema, Task]:
    s = inst.doc_selection_schema()
    return s, _doc_task(s, "doc1", "rfc", "standards-track", "the body text here " * 10)


def test_transcript_is_derived_from_render_model() -> None:
    s, task = _one_task()
    model = render(s, task)
    text = model.transcript()
    assert model.prompt in text
    assert model.preview_body in text
    assert model.preview_title in text
    for header in model.columns:
        assert header in text
    for row in model.rows:
        for cell in row:
            assert cell in text


def test_textual_surface_shows_the_same_model_and_returns_keypress_verdict() -> None:
    s, task = _one_task()
    model = render(s, task)

    async def drive() -> tuple[object, str, int]:
        app = _AdjudicateApp(s, [task])
        async with app.run_test() as pilot:
            from textual.widgets import DataTable, Static
            prompt_text = str(app.query_one("#prompt", Static).render())
            table = app.query_one("#classifications", DataTable)
            row_count = table.row_count
            await pilot.press("1")          # verdict index 0 == 'include'
            await pilot.pause()
        return app.return_value, str(prompt_text), row_count

    result, prompt_text, row_count = asyncio.run(drive())
    # the widget showed the render-model's prompt and one classification row
    assert prompt_text == model.prompt
    assert row_count == len(model.rows) == 1
    # pressing verdict 1 produced an include adjudication for row 0
    assert isinstance(result, tuple) and len(result) == 1
    adj = result[0]
    assert isinstance(adj, Adjudication)
    assert adj.verdict.name == "include"
    assert adj.row_index == 0
    assert adj.note == "human"
