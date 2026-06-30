#!/usr/bin/env python
"""``TextualFrontend`` — the pilot HUMAN Frontend (Textual; the maintainer's decision).

It is a peer of ``HeadlessFrontend`` behind the same ``Frontend`` seam, and — the
SSOT point (ADR-0012 P1) — it derives every widget from the SAME
``render(schema, task)`` render-model the headless transcript derives from. The
prompt, the less-style pager (preview), the classification ``DataTable``, and the
verdict bindings are all projections of that one model; there is no second
description of the surface.

The widget composition is declarative (Textual). Verdict keys 1..9 map to the
schema's verdict-vocabulary in order; SINGLETON adjudicates the table's selected
row and advances row-by-row, BATCH adjudicates the whole task. ``run_test`` (Textual's
headless pilot) drives this without a TTY in the test-suite.
"""

from __future__ import annotations

from typing import Sequence, assert_never

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import DataTable, Footer, Header, Static

from schema import Adjudication, AdjudicationMode, Schema, Task, render


class _AdjudicateApp(App[Sequence[Adjudication]]):
    """One app over a batch of tasks for a single schema. Exits returning the
    collected adjudications."""

    CSS = """
    #prompt { padding: 1; background: $panel; }
    #preview { padding: 1; height: 1fr; }
    #status { padding: 1; color: $text-muted; }
    """

    BINDINGS = [
        Binding("q", "quit_empty", "quit"),
        *[Binding(str(d), f"verdict('{d - 1}')", f"verdict {d}") for d in range(1, 10)],
    ]

    def __init__(self, schema: Schema, tasks: Sequence[Task]) -> None:
        super().__init__()
        self._schema = schema
        self._tasks = tuple(tasks)
        self._task_idx = 0
        self._row_idx = 0
        self._results: list[Adjudication] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="prompt")
        with VerticalScroll(id="preview"):
            yield Static(id="preview_body")
        yield DataTable(id="classifications")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#classifications", DataTable)
        table.cursor_type = "row"
        self._load_task()

    def _load_task(self) -> None:
        if self._task_idx >= len(self._tasks):
            self.exit(tuple(self._results))
            return
        task = self._tasks[self._task_idx]
        model = render(self._schema, task)
        self.query_one("#prompt", Static).update(model.prompt)
        self.query_one("#preview_body", Static).update(
            f"[b]{model.preview_title}[/b]\n\n{model.preview_body}")
        table = self.query_one("#classifications", DataTable)
        table.clear(columns=True)
        table.add_columns(*model.columns)
        for r in model.rows:
            table.add_row(*r)
        if model.mode is AdjudicationMode.SINGLETON and table.row_count:
            table.move_cursor(row=self._row_idx)
        self._update_status(model)

    def _update_status(self, model: object) -> None:
        opts = ", ".join(f"{i + 1}={v.name}" for i, v in enumerate(self._schema.verdicts.verdicts))
        mode = self._schema.mode.value
        where = (f"row {self._row_idx + 1}/{len(self._tasks[self._task_idx].classifications)}"
                 if self._schema.mode is AdjudicationMode.SINGLETON else "whole batch")
        self.query_one("#status", Static).update(
            f"task {self._task_idx + 1}/{len(self._tasks)} ({mode}, {where})  verdicts: {opts}  q=quit")

    def action_quit_empty(self) -> None:
        self.exit(tuple(self._results))

    def action_verdict(self, index: str) -> None:
        i = int(index)
        verdicts = self._schema.verdicts.verdicts
        if i >= len(verdicts):
            return
        if self._task_idx >= len(self._tasks):
            return
        task = self._tasks[self._task_idx]
        verdict = verdicts[i]
        match self._schema.mode:
            case AdjudicationMode.SINGLETON:
                self._results.append(Adjudication.make(
                    self._schema, task, verdict, row_index=self._row_idx, note="human"))
                self._row_idx += 1
                if self._row_idx >= len(task.classifications):
                    self._task_idx += 1
                    self._row_idx = 0
            case AdjudicationMode.BATCH:
                self._results.append(Adjudication.make(
                    self._schema, task, verdict, note="human"))
                self._task_idx += 1
            case _:
                assert_never(self._schema.mode)
        self._load_task()


class TextualFrontend:
    """The human ``Frontend`` adapter. Conforms structurally to ``protocols.Frontend``."""

    def adjudicate(self, schema: Schema, tasks: Sequence[Task]) -> Sequence[Adjudication]:
        if not tasks:
            return ()
        app = _AdjudicateApp(schema, tasks)
        result = app.run()
        return result if result is not None else ()
