#!/usr/bin/env python
"""Frontend PARITY — the human surface and the LLM/headless surface produce the
SAME adjudication contract for the same schema+input (the brief's required proof).

``TextualFrontend`` (human) and ``HeadlessFrontend`` (LLM/rule-driven) are two
adapters of the ONE ``Frontend`` protocol (``protocols.Frontend``), and — the SSOT
point (ADR-0012 P1) — both derive their surface from the SAME ``render(schema, task)``
render-model; neither re-describes prompt/preview/columns. This module discharges the
explicit deliverable: for identical inputs, across BOTH adjudication modes (SINGLETON
doc-selection, BATCH coref) AND across BOTH drivers, the *decision-bearing* adjudication
contract — ``(schema_key, task_id, verdict, row_index)`` per ``Adjudication`` — is
identical.

Method (ADR-0013 Rule 5 — verify the artifact, not the claim): the headless Frontend is
driven first; the human surface is then driven by pressing exactly the verdict the policy
chose (the verdict's 1-based vocabulary index), so the test proves the two surfaces are
INTERCHANGEABLE for *any* decision over a given input — not that one hard-coded answer
happens to match. The ``note`` field is provenance ("human" vs the policy's rationale)
and is asserted to DIFFER, so the parity claim is precisely about the decision contract,
not the audit trail.

On driving the human surface: ``TextualFrontend.adjudicate`` is a thin ``app.run()``
wrapper that returns exactly ``_AdjudicateApp(schema, tasks).return_value``; ``app.run()``
needs a TTY, so this test exercises the SAME ``_AdjudicateApp`` artifact through Textual's
sanctioned headless ``run_test`` pilot (the official harness — identical app logic, no
TTY). The structural ``isinstance(TextualFrontend(), Frontend)`` check below pins that the
wrapper is a real ``Frontend``; the pilot pins the contract its app produces.
"""

from __future__ import annotations

import asyncio
from typing import Sequence

import instances as inst
from frontend_headless import HeadlessFrontend, LLMPolicy, RulePolicy
from frontend_textual import TextualFrontend, _AdjudicateApp
from loaders import _doc_task, coref_stub_tasks
from protocols import Frontend
from schema import Adjudication, Schema, Task

# The decision-bearing identity of an adjudication: everything EXCEPT the provenance note.
Contract = tuple[str, str, str, "int | None"]


def _contract(adjs: Sequence[Adjudication]) -> list[Contract]:
    """Project a batch onto its decision-bearing identity. Two Frontends agree on the
    contract iff these lists are equal (the ``note`` is provenance, deliberately excluded)."""
    return [(a.schema_key, a.task_id, a.verdict.name, a.row_index) for a in adjs]


def _verdict_keys(schema: Schema, adjs: Sequence[Adjudication]) -> list[str]:
    """The keypresses a human makes to reach the SAME verdicts the policy chose: each
    verdict's 1-based index in the schema's vocabulary, in order. Deriving the human's
    action from the machine's decision is what makes the claim *interchangeability for any
    decision*, not a coincidence on one fixed answer."""
    names = [v.name for v in schema.verdicts.verdicts]
    return [str(names.index(a.verdict.name) + 1) for a in adjs]


def _drive_human(schema: Schema, tasks: Sequence[Task],
                 keys: Sequence[str]) -> Sequence[Adjudication]:
    """Drive the real Textual surface headlessly via Textual's ``run_test`` pilot and
    return the adjudications it produced — byte-for-byte what ``TextualFrontend.adjudicate``
    returns for the same keypresses (it is a thin ``app.run()`` wrapper over this app)."""
    async def go() -> "Sequence[Adjudication] | None":
        app = _AdjudicateApp(schema, tasks)
        async with app.run_test() as pilot:
            for k in keys:
                await pilot.press(k)
                await pilot.pause()
        return app.return_value

    result = asyncio.run(go())
    assert result is not None, "the Textual app exited without a return value"
    return result


def _assert_frontend_parity(schema: Schema, tasks: Sequence[Task],
                            headless: Frontend) -> list[Contract]:
    """The one parity gate, quantified over (schema, input, headless-Frontend): drive the
    headless Frontend, then drive the human Frontend to the same verdicts, and assert the
    decision contracts are identical while the provenance notes differ. Returns the shared
    contract so a caller can additionally pin its shape."""
    # Both are adapters of the ONE Frontend protocol — the LLM driver is NOT a separate path.
    assert isinstance(headless, Frontend)
    assert isinstance(TextualFrontend(), Frontend)

    machine = headless.adjudicate(schema, tasks)
    human = _drive_human(schema, tasks, _verdict_keys(schema, machine))

    machine_contract = _contract(machine)
    assert machine_contract, "no adjudications produced — a parity match would be vacuous"
    # The brief's proof: identical decision contract from both surfaces, same schema+input.
    assert _contract(human) == machine_contract
    # Provenance differs — the parity is about the decision, not the note.
    assert all(a.note == "human" for a in human)
    assert all(a.note != "human" for a in machine)
    return machine_contract


# ------------------------------------------------------------------ SINGLETON (doc-selection)
def test_parity_singleton_include() -> None:
    s = inst.doc_selection_schema()
    task = _doc_task(s, "rfc-incl", "rfc", "standards-track", "word " * 200)  # in-band -> include
    contract = _assert_frontend_parity(s, [task], HeadlessFrontend(RulePolicy(inst.DOC_SUGGESTED)))
    assert contract == [("doc-selection", "rfc-incl", "include", 0)]


def test_parity_singleton_exclude() -> None:
    s = inst.doc_selection_schema()
    task = _doc_task(s, "rfc-excl", "rfc", "historic", "tiny stub")  # <50 words -> exclude
    contract = _assert_frontend_parity(s, [task], HeadlessFrontend(RulePolicy(inst.DOC_SUGGESTED)))
    assert contract == [("doc-selection", "rfc-excl", "exclude", 0)]


def _doc_multirow(s: Schema) -> Task:
    """A SINGLETON doc-task carrying TWO classifications (suggesting include then exclude),
    so parity must hold ROW-BY-ROW: both surfaces advance row 0 -> row 1 and emit two
    distinct verdicts in order."""
    payload = s.payload({
        inst.DOC_SOURCE: "rfc", inst.DOC_DOMAIN: "informational",
        inst.DOC_TEXT_LEN: 1234, inst.DOC_WORD_COUNT: 200,
        inst.DOC_BODY: "the body text here " * 50,
    })
    c_incl = s.classification({inst.DOC_SUGGESTED: "include",
                               inst.DOC_RATIONALE: "in-band -> include", inst.DOC_SCORE: 0.9})
    c_excl = s.classification({inst.DOC_SUGGESTED: "exclude",
                               inst.DOC_RATIONALE: "boilerplate -> exclude", inst.DOC_SCORE: 0.1})
    return s.task("doc-multi", payload, [c_incl, c_excl])


def test_parity_singleton_multirow_advances_identically() -> None:
    s = inst.doc_selection_schema()
    contract = _assert_frontend_parity(s, [_doc_multirow(s)],
                                       HeadlessFrontend(RulePolicy(inst.DOC_SUGGESTED)))
    assert contract == [("doc-selection", "doc-multi", "include", 0),
                        ("doc-selection", "doc-multi", "exclude", 1)]


# ----------------------------------------------------------------------- BATCH (coref)
def test_parity_batch_coref_coreferent() -> None:
    s = inst.coref_schema()
    tasks = coref_stub_tasks(s)
    contract = _assert_frontend_parity(s, tasks, HeadlessFrontend(LLMPolicy(lambda _p: "coreferent")))
    # BATCH: one whole-group verdict per task, row_index is None.
    assert contract == [("coref-adjudication", "coref-stub-1", "coreferent", None)]


def test_parity_batch_coref_uncertain() -> None:
    s = inst.coref_schema()
    tasks = coref_stub_tasks(s)
    contract = _assert_frontend_parity(s, tasks, HeadlessFrontend(LLMPolicy(lambda _p: "uncertain")))
    assert contract == [("coref-adjudication", "coref-stub-1", "uncertain", None)]
