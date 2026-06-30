#!/usr/bin/env python
"""ADR-0000: an INCOHERENT schema/task/adjudication is UNREPRESENTABLE.

Every test here asserts a construction-time REFUSAL — the illegal state cannot be
built, so it can never reach a Frontend. These are the boundary raises that stand in
for the (Python-unreachable) row-typed compile error; the closed variants
(FieldKind/PreviewSource/AdjudicationMode) get their teeth from mypy's exhaustiveness
instead and are not re-tested at runtime."""

from __future__ import annotations

import pytest

from schema import (Adjudication, AdjudicationMode, Field, PromptTemplate, Record,
                    Schema, TextFieldPreview, Verdict, VerdictVocabulary)

A = Field.text("a")
B = Field.integer("b")
OUTSIDE = Field.text("outside")
V = VerdictVocabulary((Verdict("yes", "y"), Verdict("no", "n")))


def _schema(**kw: object) -> Schema:
    base: dict[str, object] = dict(
        key="t", title="T",
        prompt=PromptTemplate.build("a=", A),
        payload_fields=(A, B),
        preview=TextFieldPreview(A, title="p"),
        columns=(A,),
        verdicts=V,
        mode=AdjudicationMode.SINGLETON,
        table="t_tbl",
    )
    base.update(kw)
    return Schema(**base)  # type: ignore[arg-type]


def test_prompt_referencing_nonpayload_field_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="not in payload_fields"):
        _schema(prompt=PromptTemplate.build("x=", OUTSIDE))


def test_preview_nonpayload_field_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="not a payload field"):
        _schema(preview=TextFieldPreview(OUTSIDE, title="p"))


def test_preview_nontext_field_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="not text"):
        _schema(preview=TextFieldPreview(B, title="p"))


def test_empty_payload_fields_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="payload_fields is empty"):
        _schema(payload_fields=(), prompt=PromptTemplate.build("k"),
                preview=TextFieldPreview(A, title="p"))


def test_empty_columns_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="columns is empty"):
        _schema(columns=())


def test_empty_verdict_vocabulary_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        VerdictVocabulary(())


def test_record_missing_field_is_unrepresentable() -> None:
    with pytest.raises(ValueError, match="missing"):
        Record.of((A, B), {A: "x"})


def test_record_wrongtype_cell_is_unrepresentable() -> None:
    with pytest.raises(TypeError, match="requires int"):
        Record.of((A, B), {A: "x", B: "not-an-int"})


def test_record_bool_in_int_field_is_unrepresentable() -> None:
    # bool is a subclass of int, so a naive isinstance check would smuggle True into
    # an INT field — the coherence-gate must foreclose it (ADR-0000 Rule 2(a)).
    with pytest.raises(TypeError, match="requires int"):
        Record.of((A, B), {A: "x", B: True})


def test_singleton_adjudication_without_row_index_is_unrepresentable() -> None:
    s = _schema()
    task = s.task("t1", s.payload({A: "x", B: 1}), [s.classification({A: "x"})])
    with pytest.raises(ValueError, match="row_index is required"):
        Adjudication.make(s, task, V.member("yes"))


def test_batch_adjudication_with_row_index_is_unrepresentable() -> None:
    s = _schema(mode=AdjudicationMode.BATCH)
    task = s.task("t1", s.payload({A: "x", B: 1}), [s.classification({A: "x"})])
    with pytest.raises(ValueError, match="must be None"):
        Adjudication.make(s, task, V.member("yes"), row_index=0)


def test_rogue_verdict_is_unrepresentable() -> None:
    s = _schema()
    task = s.task("t1", s.payload({A: "x", B: 1}), [s.classification({A: "x"})])
    with pytest.raises(ValueError, match="not in schema"):
        Adjudication.make(s, task, Verdict("maybe", "rogue"), row_index=0)


def test_duplicate_payload_field_name_is_unrepresentable() -> None:
    # same-name, DIFFERENT kind: distinct Field objects a set/identity check would miss,
    # but they collide on the derived store column ``payload_dup`` (silently de-duped by
    # SQLAlchemy if it slipped through — ADR-0002). Foreclosed at the namespace owner.
    dup_text = Field.text("dup")
    dup_int = Field.integer("dup")
    with pytest.raises(ValueError, match="payload_fields.*duplicate field name"):
        _schema(payload_fields=(dup_text, dup_int), prompt=PromptTemplate.build("a=", A),
                preview=TextFieldPreview(dup_text, title="p"))


def test_duplicate_column_name_is_unrepresentable() -> None:
    # same-name, SAME kind in the classification columns: two identical column titles ->
    # an ambiguous table and a colliding ``cls_score`` DDL column.
    with pytest.raises(ValueError, match="columns.*duplicate field name"):
        _schema(columns=(Field.number("score"), Field.number("score")))


def test_cross_namespace_name_reuse_is_coherent_and_allowed() -> None:
    # payload "x" and a column "x" do NOT collide — distinct store columns (payload_x vs
    # cls_x) on distinct surfaces (prompt/preview vs table) — so the coherence-gate must
    # NOT reject it. Pins the fix to the real defect class, guarding against over-rejection.
    px = Field.text("x")
    cx = Field.text("x")
    s = _schema(payload_fields=(A, px), preview=TextFieldPreview(A, title="p"), columns=(cx,))
    store_cols = {name for name, _kind in s.store_columns()}
    assert "payload_x" in store_cols and "cls_x" in store_cols


def test_task_classification_shape_mismatch_is_unrepresentable() -> None:
    s = _schema()
    # a classification over the wrong field set (payload fields, not columns)
    bad = Record.of((A, B), {A: "x", B: 1})
    with pytest.raises(ValueError, match="do not match schema columns"):
        s.task("t1", s.payload({A: "x", B: 1}), [bad])
