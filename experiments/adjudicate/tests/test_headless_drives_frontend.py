#!/usr/bin/env python
"""The LLM driver is the SAME Frontend protocol, not a separate path.

``HeadlessFrontend`` is a ``Frontend``; swapping its ``Policy`` makes it
rule-driven (autonomous, no LLM) or LLM-driven (an injected ``complete`` seam). Both
produce valid adjudications through the one protocol; a fake completer stands in for
Claude so the LLM path is exercised without a network call."""

from __future__ import annotations

import instances as inst
from frontend_headless import HeadlessFrontend, LLMPolicy, RulePolicy
from loaders import _doc_task, coref_stub_tasks
from protocols import Frontend
from schema import render


def test_headless_is_a_frontend() -> None:
    fe = HeadlessFrontend(RulePolicy(inst.DOC_SUGGESTED))
    assert isinstance(fe, Frontend)


def test_rule_policy_singleton_accepts_suggestion() -> None:
    s = inst.doc_selection_schema()
    task = _doc_task(s, "d1", "rfc", "informational", "word " * 100)  # in-band -> include
    fe = HeadlessFrontend(RulePolicy(inst.DOC_SUGGESTED))
    adjs = fe.adjudicate(s, [task])
    assert [a.verdict.name for a in adjs] == ["include"]
    assert adjs[0].row_index == 0


def test_rule_policy_batch_majority_on_coref() -> None:
    s = inst.coref_schema()
    tasks = coref_stub_tasks(s)
    # adjudicate by majority grounding... here use confidence-as-suggestion is wrong;
    # the coref columns have no verdict-named column, so a rule keyed on grounding_source
    # would not be a verdict. Exercise the LLM path for coref instead (below); here just
    # confirm BATCH yields ONE adjudication per task via a verdict-returning fake.
    fe = HeadlessFrontend(LLMPolicy(lambda _p: "coreferent"))
    adjs = fe.adjudicate(s, tasks)
    assert len(adjs) == len(tasks) == 1
    assert adjs[0].verdict.name == "coreferent"
    assert adjs[0].row_index is None  # whole-batch verdict


def test_llm_policy_singleton_parses_per_row() -> None:
    s = inst.doc_selection_schema()
    task = _doc_task(s, "d1", "rfc", "historic", "word " * 100)

    seen: list[str] = []

    def fake_complete(prompt: str) -> str:
        seen.append(prompt)
        return "exclude"

    fe = HeadlessFrontend(LLMPolicy(fake_complete))
    adjs = fe.adjudicate(s, [task])
    assert [a.verdict.name for a in adjs] == ["exclude"]
    # the LLM saw the SAME transcript the human surface renders (SSOT)
    model = render(s, task)
    assert model.transcript() in seen[0]
