#!/usr/bin/env python
"""``HeadlessFrontend`` — the LLM-driver mechanism, as a Frontend (NOT a separate path).

The brief's hard requirement: "the LLM driver is the SAME Frontend protocol driven
programmatically/headlessly, NOT a separate code path." This module is that. A
``HeadlessFrontend`` is a real ``Frontend``; it derives its surface from the SAME
``render(schema, task)`` the Textual surface uses, serializes that render-model to a
text transcript, and asks an injected ``Policy`` for verdicts. Swap the policy and
the SAME frontend is human-rule-driven or LLM-driven — autonomy is a policy choice,
not a code fork.

Two policies:
  * ``RulePolicy`` (REAL now) — deterministic, no LLM. It adjudicates by accepting
    the unsupervised model's suggested label (a designated classification column
    whose value is a verdict name). This runs doc-selection autonomously end-to-end
    today and honors the maintainer's "no LLM for the PoC" constraint while proving
    the headless path.
  * ``LLMPolicy`` (DESIGNED-FOR / live-capable) — defines the LLM contract: it hands
    ``model.transcript()`` to an injected ``complete(prompt) -> str`` seam (a real
    Claude call, or a test fake) and parses the chosen verdict. Only the network
    call is deferred behind one function; the framing/parsing is real and tested.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable, Protocol, Sequence, assert_never

from schema import (Adjudication, AdjudicationMode, Field, RenderModel, Schema,
                    Task, render)


class Policy(Protocol):
    """The decision seam inside the headless frontend: (schema, task, render-model)
    -> adjudications. The render-model is passed so a policy adjudicates against the
    EXACT surface a human would see (the transcript), never a privileged side-channel."""

    def decide(self, schema: Schema, task: Task, model: RenderModel) -> Sequence[Adjudication]:
        ...


@dataclass
class RulePolicy:
    """REAL deterministic policy: accept the model's suggested verdict. ``suggestion``
    is the classification column carrying a verdict name (e.g. doc-selection's
    ``suggested`` column with values 'include'/'exclude'). For SINGLETON it emits one
    adjudication per row; for BATCH it adjudicates the group by majority suggestion."""

    suggestion: Field[object]

    def decide(self, schema: Schema, task: Task, model: RenderModel) -> Sequence[Adjudication]:
        if self.suggestion not in schema.columns:
            raise ValueError(f"RulePolicy suggestion column {self.suggestion.name!r} is not a "
                             f"schema column (ADR-0000: a policy cannot read a non-column).")
        match schema.mode:
            case AdjudicationMode.SINGLETON:
                out: list[Adjudication] = []
                for i, c in enumerate(task.classifications):
                    verdict = schema.verdicts.member(c.render(self.suggestion))
                    out.append(Adjudication.make(schema, task, verdict, row_index=i,
                                                 note="rule: accept model suggestion"))
                return out
            case AdjudicationMode.BATCH:
                votes = Counter(c.render(self.suggestion) for c in task.classifications)
                winner = votes.most_common(1)[0][0]
                verdict = schema.verdicts.member(winner)
                return [Adjudication.make(schema, task, verdict,
                                          note=f"rule: majority suggestion {dict(votes)}")]
        assert_never(schema.mode)


@dataclass
class LLMPolicy:
    """DESIGNED-FOR LLM policy. ``complete`` is the one injected seam — a real Claude
    completion or a test fake. The frontend serializes the render-model; this policy
    appends an instruction asking for a verdict name (per row for SINGLETON, one for
    BATCH), calls ``complete``, and parses the verdict from the vocabulary. The
    parsing refuses an out-of-vocabulary answer (ADR-0002)."""

    complete: Callable[[str], str]

    def _ask(self, model: RenderModel, instruction: str) -> str:
        return self.complete(model.transcript() + "\n\n" + instruction)

    def decide(self, schema: Schema, task: Task, model: RenderModel) -> Sequence[Adjudication]:
        options = ", ".join(v.name for v in schema.verdicts.verdicts)
        match schema.mode:
            case AdjudicationMode.SINGLETON:
                out: list[Adjudication] = []
                for i in range(len(task.classifications)):
                    answer = self._ask(model, f"For classification row {i}, reply with exactly "
                                              f"one verdict name from: {options}").strip()
                    verdict = schema.verdicts.member(answer)
                    out.append(Adjudication.make(schema, task, verdict, row_index=i,
                                                 note="llm"))
                return out
            case AdjudicationMode.BATCH:
                answer = self._ask(model, f"Reply with exactly one verdict name for the whole "
                                          f"group from: {options}").strip()
                verdict = schema.verdicts.member(answer)
                return [Adjudication.make(schema, task, verdict, note="llm")]
        assert_never(schema.mode)


@dataclass
class HeadlessFrontend:
    """A ``Frontend`` driven by a ``Policy`` — the autonomous surface. Same
    ``render`` as the human surface; the policy sees the transcript and returns
    adjudications. Conforms structurally to ``protocols.Frontend``."""

    policy: Policy

    def adjudicate(self, schema: Schema, tasks: Sequence[Task]) -> Sequence[Adjudication]:
        out: list[Adjudication] = []
        for task in tasks:
            model = render(schema, task)
            out.extend(self.policy.decide(schema, task, model))
        return out
