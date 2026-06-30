#!/usr/bin/env python
"""The DOMAIN-SCHEMA — the first-class artifact every adjudication interaction derives from.

ADR-0000 (type-driven design) is the governing law here, and this file is its
worked instance: the goal is that *an incoherent schema is UNREPRESENTABLE* — a
``Schema`` whose prompt interpolates a field that does not exist, whose preview
points at nothing, whose classification-table columns do not match the rows that
arrive, or whose adjudication-mode is a typo'd string, must not be constructable,
let alone typecheck. The four-specimen lesson of ADR-0000 ("a refined type makes
the illegal shape unconstructable at the boundary, not guarded three layers
downstream") is applied directly:

  * The closed axes — FieldKind, PreviewSource, AdjudicationMode, Verdict
    membership, prompt segments — are **exhaustive variants** (sealed unions /
    enums) the renderer matches with ``typing.assert_never``. A new case that the
    renderer forgets to handle is a mypy error, not a runtime ``KeyError`` (the
    BoundedBatch move: the class is foreclosed, not clamped). [ADR-0000 Rule 1]

  * The cross-references — prompt→fields, preview→fields, classification→columns,
    adjudication→mode, verdict→vocabulary — are validated at **construction
    time** and raise (the Port/ACL strict-decode of ADR-0012 P2: a boundary
    translates-and-validates and refuses what it cannot honor). A ``Schema`` /
    ``Task`` / ``Adjudication`` that would render an incoherent surface cannot be
    constructed, so it never reaches a Frontend. This is the *honestly declared*
    enforcement surface (ADR-0011 Rule 1): **construction/import-time raise**,
    not review-only prose. [ADR-0000 Rule 2(a)]

SSOT (ADR-0012 P1). This module is the ONE source. The Textual surface, the
headless/LLM driver, the SQLAlchemy Core DDL, and the prompt text are all
*derived* from a ``Schema`` — never restated. The single projection both the
human and the LLM Frontend consume is ``render(schema, task) -> RenderModel``;
the store's columns are ``schema.store_columns()``; the prompt string is
``schema.prompt.render(payload)``. There is no second hand-authored copy of "what
the interface shows".

This file imports only the standard library — it is the device-free, framework-
free SSOT both the TUI (Textual) and the store (SQLAlchemy) sit downstream of,
exactly as ``nla_lab/contract.py`` is the device-free SSOT its eight variants
sit downstream of. See GLOSSARY.md for the coined terms (domain-schema,
classification, adjudication-mode, verdict-vocabulary, render-model).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Mapping, Sequence, TypeVar, assert_never, cast

# Covariant: T appears ONLY in classmethod return positions (the kind/py_type is the
# real authority); a Field[str] is therefore usable wherever a Field[object] is, so a
# heterogeneous field tuple is a tuple[Field[object], ...]. T is a phantom parameter —
# never stored — so the covariance is sound.
T_co = TypeVar("T_co", covariant=True)


# ====================================================================== FieldKind
class FieldKind(Enum):
    """The closed vocabulary of cell types — the SINGLE owner (ADR-0012 P1) of how a
    value is (a) typed in Python, (b) rendered to a table/prompt string, and (c)
    mapped to a store column. An out-of-vocabulary kind is unrepresentable; every
    consumer matches this enum exhaustively (``assert_never``), so adding a kind is a
    compile-time obligation across the codebase, never a silent fail-open."""

    TEXT = "text"
    INT = "int"
    FLOAT = "float"

    def py_type(self) -> type[object]:
        """The Python type a cell of this kind must hold (the coercion authority)."""
        match self:
            case FieldKind.TEXT:
                return str
            case FieldKind.INT:
                return int
            case FieldKind.FLOAT:
                return float
        assert_never(self)

    def render(self, value: object) -> str:
        """Stringify a cell for the prompt / table / pager — ONE rendering authority
        so the human surface and the headless transcript cannot diverge."""
        match self:
            case FieldKind.TEXT:
                return str(value)
            case FieldKind.INT:
                return str(value)  # value is a validated int (Record.of enforced the kind)
            case FieldKind.FLOAT:
                return f"{cast(float, value):.4g}"
        assert_never(self)


# ========================================================================== Field
@dataclass(frozen=True)
class Field(Generic[T_co]):
    """A typed, named slot — the atom of the domain-schema. ``kind`` is the SSOT for
    the column's Python type, its rendering, and its store column; ``py_type`` is
    bound to ``kind`` by the constructors below so the two cannot disagree (a
    ``Field`` declaring ``kind=INT`` but holding strings is unrepresentable — you
    cannot build it). Frozen + hashable so a ``Field`` is a stable dict key the
    prompt, the preview, the columns, and the records all share BY VALUE — the
    reference that ties the schema's parts together (ADR-0012 P1: one home)."""

    name: str
    kind: FieldKind

    @classmethod
    def text(cls, name: str) -> "Field[str]":
        return Field(name, FieldKind.TEXT)

    @classmethod
    def integer(cls, name: str) -> "Field[int]":
        return Field(name, FieldKind.INT)

    @classmethod
    def number(cls, name: str) -> "Field[float]":
        return Field(name, FieldKind.FLOAT)


# ========================================================================= Record
@dataclass(frozen=True)
class Record:
    """A validated value-tuple over a declared field set — the typed payload a
    document source emits and the typed row a classification arrives as. Construction
    is the Port/ACL (ADR-0012 P2): ``of`` decodes a raw ``{Field: value}`` mapping
    and REFUSES it unless the keys are EXACTLY the declared fields and every value
    matches its field's kind. A record that is missing a field the prompt will
    interpolate, or carries a wrong-typed cell, is therefore unconstructable — the
    ``KeyError``/``TypeError`` class is foreclosed at the boundary (ADR-0000)."""

    fields: tuple[Field[object], ...]
    values: tuple[object, ...]  # positional, aligned to ``fields``

    @classmethod
    def of(cls, fields: Sequence[Field[object]], cells: Mapping[Field[object], object]) -> "Record":
        declared = tuple(fields)
        declared_set = set(declared)
        got = set(cells)
        if got != declared_set:
            missing = declared_set - got
            extra = got - declared_set
            raise ValueError(
                f"Record does not match its field set: missing={sorted(f.name for f in missing)} "
                f"extra={sorted(f.name for f in extra)}. A record must carry EXACTLY the "
                "declared fields (ADR-0000: an under/over-specified record is unrepresentable).")
        out: list[object] = []
        for f in declared:
            v = cells[f]
            expected = f.kind.py_type()
            # ``bool`` is a SUBCLASS of ``int``, so a bare ``isinstance(True, int)`` is
            # True and would smuggle a bool into an INT field — a lying record the kind
            # vocabulary has no slot for (no FieldKind maps to bool). Reject bool unless
            # the field's own py_type IS bool (no current kind, but the guard forecloses
            # the class rather than the instance — ADR-0000 Rule 2(a)).
            wrong_type = not isinstance(v, expected)
            bool_smuggled = isinstance(v, bool) and expected is not bool
            if wrong_type or bool_smuggled:
                raise TypeError(
                    f"field {f.name!r} (kind {f.kind.value}) requires {expected.__name__}, "
                    f"got {type(v).__name__}={v!r} — a wrong-typed cell is a lying record "
                    "(ADR-0002 / ADR-0012 P2), refused at construction.")
            out.append(v)
        return cls(declared, tuple(out))

    def get(self, f: Field[object]) -> object:
        """Total lookup over a declared field — never a ``KeyError`` because ``of``
        guaranteed every declared field is present (the interpolation is total)."""
        return self.values[self.fields.index(f)]

    def render(self, f: Field[object]) -> str:
        return f.kind.render(self.get(f))


# ================================================================== PromptTemplate
@dataclass(frozen=True)
class LiteralSegment:
    """A fixed piece of prompt text."""

    text: str


@dataclass(frozen=True)
class FieldSegment:
    """An interpolation slot — references a ``Field`` BY VALUE, never a ``"{name}"``
    string. You cannot interpolate a field that does not exist because there is no
    name to typo: the segment IS the field object, and ``PromptTemplate`` refuses any
    segment whose field is outside the schema's payload fields (ADR-0000)."""

    field: Field[object]


PromptSegment = LiteralSegment | FieldSegment  # exhaustive (sealed) prompt vocabulary


@dataclass(frozen=True)
class PromptTemplate:
    """A question with interpolated typed fields, built from a sequence of segments.
    Its referenced fields are a guaranteed subset of the payload fields (checked by
    ``Schema``), so ``render`` over a payload ``Record`` is total — the stringly-typed
    ``"{missing_field}"`` KeyError class does not exist here."""

    segments: tuple[PromptSegment, ...]

    @classmethod
    def build(cls, *parts: "str | Field[object]") -> "PromptTemplate":
        segs: list[PromptSegment] = []
        for p in parts:
            if isinstance(p, Field):
                segs.append(FieldSegment(p))
            else:
                segs.append(LiteralSegment(p))
        return cls(tuple(segs))

    def referenced_fields(self) -> frozenset[Field[object]]:
        return frozenset(s.field for s in self.segments if isinstance(s, FieldSegment))

    def render(self, payload: Record) -> str:
        out: list[str] = []
        for s in self.segments:
            match s:
                case LiteralSegment(text=text):
                    out.append(text)
                case FieldSegment(field=f):
                    out.append(payload.render(f))
                case _:
                    assert_never(s)
        return "".join(out)


# =================================================================== PreviewSource
@dataclass(frozen=True)
class TextFieldPreview:
    """The less-style pager renders this payload TEXT field: the document body
    (doc-selection) or the hook's explanation text (coref). One mechanism, one
    parameter (which field) — not two stringly-distinguished kinds (ADR-0008: do not
    fabricate a dimension a single parameter already carries)."""

    field: Field[object]
    title: str


# Sealed preview vocabulary. Realized today by TextFieldPreview; a second kind (a
# structured/diff preview, an external-pager command) is a NEW variant the renderer
# is forced to handle (mypy ``assert_never`` reports the gap) — the designed-for
# second adapter of this seam (ADR-0012 P12 / structural-hygiene "second designed-for").
PreviewSource = TextFieldPreview


# ================================================================= AdjudicationMode
class AdjudicationMode(Enum):
    """How many verdicts a Frontend collects per task — the exhaustive variant the
    brief names. SINGLETON (doc-selection, degenerate) collects ONE verdict per
    classification row; BATCH (coref, the parent project) collects ONE verdict for
    the whole group of rows. A Frontend matches this exhaustively; an ``Adjudication``
    whose shape contradicts the mode is unconstructable (see ``Adjudication``)."""

    SINGLETON = "singleton"
    BATCH = "batch"


# ======================================================================== Verdict
@dataclass(frozen=True)
class Verdict:
    """One member of a schema's closed verdict-vocabulary (e.g. include/exclude;
    coreferent/not-coreferent/uncertain). A verdict is a value, not a free string —
    an ``Adjudication`` may only carry a verdict drawn from its schema's vocabulary,
    so the typo'd ``"inclde"`` fail-open is unrepresentable."""

    name: str
    description: str


@dataclass(frozen=True)
class VerdictVocabulary:
    """The closed, ordered set of verdicts a schema admits. Non-empty by
    construction; ``member`` is the only sanctioned way to obtain a verdict, so a
    rogue verdict cannot enter an ``Adjudication``."""

    verdicts: tuple[Verdict, ...]

    def __post_init__(self) -> None:
        if not self.verdicts:
            raise ValueError("a verdict-vocabulary must be non-empty (ADR-0000: a schema "
                             "with no adjudicable outcome cannot render a coherent surface).")
        names = [v.name for v in self.verdicts]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate verdict names {names} — the vocabulary must be a set.")

    def __contains__(self, v: object) -> bool:
        return isinstance(v, Verdict) and v in self.verdicts

    def member(self, name: str) -> Verdict:
        for v in self.verdicts:
            if v.name == name:
                return v
        raise KeyError(
            f"verdict {name!r} is not in this schema's vocabulary "
            f"{[v.name for v in self.verdicts]} (ADR-0000: an out-of-vocabulary verdict "
            "is refused, never coerced).")


# ========================================================================= Schema
@dataclass(frozen=True)
class Schema:
    """The domain-schema instance — the SSOT that determines how the interface
    interacts. It binds, as ONE coherent unit validated at construction:

      * ``prompt``        — a question over ``payload_fields``;
      * ``payload_fields``— the interpolation/preview namespace (the document's
                            intrinsic fields: text_len, word_count, source, domain,
                            body, …);
      * ``preview``       — which payload TEXT field the pager renders;
      * ``columns``       — the classification-table column spec (the model's
                            suggestion fields arriving on the Bus);
      * ``verdicts``      — the closed adjudication outcome set;
      * ``mode``          — singleton | batch;
      * ``table``         — the persistence table name (the store DDL is DERIVED
                            from ``columns``+``payload_fields``, never hand-restated).

    ``__post_init__`` is the coherence gate (ADR-0000 / ADR-0012 P2): it refuses a
    schema whose prompt or preview references a non-payload field, or whose
    fields/columns are empty. Past this constructor a ``Schema`` is *guaranteed* to
    render a coherent {prompt, preview, classification-table, adjudication-mode} —
    that guarantee is the type's whole reason to exist."""

    key: str  # stable identifier (also the default table/bus topic namespace)
    title: str
    prompt: PromptTemplate
    payload_fields: tuple[Field[object], ...]
    preview: PreviewSource
    columns: tuple[Field[object], ...]
    verdicts: VerdictVocabulary
    mode: AdjudicationMode
    table: str

    def __post_init__(self) -> None:
        if not self.payload_fields:
            raise ValueError(f"schema {self.key!r}: payload_fields is empty — nothing to "
                             "interpolate or preview (ADR-0000: incoherent surface).")
        if not self.columns:
            raise ValueError(f"schema {self.key!r}: columns is empty — the classification-table "
                             "has no columns (ADR-0000: incoherent surface).")
        payload_set = frozenset(self.payload_fields)
        dangling = self.prompt.referenced_fields() - payload_set
        if dangling:
            raise ValueError(
                f"schema {self.key!r}: prompt interpolates field(s) "
                f"{sorted(f.name for f in dangling)} not in payload_fields "
                f"{sorted(f.name for f in payload_set)} — a prompt that references a "
                "non-existent field is unrepresentable (ADR-0000 / the BoundedBatch move).")
        if self.preview.field not in payload_set:
            raise ValueError(
                f"schema {self.key!r}: preview field {self.preview.field.name!r} is not a "
                "payload field — the pager would have nothing to render.")
        if self.preview.field.kind is not FieldKind.TEXT:
            raise ValueError(
                f"schema {self.key!r}: preview field {self.preview.field.name!r} is "
                f"{self.preview.field.kind.value}, not text — the less-style pager renders text.")

    # ---- factories that produce ONLY coherent tasks/adjudications for THIS schema ----
    def payload(self, cells: Mapping[Field[object], object]) -> Record:
        """Build a payload record over ``payload_fields`` (validated by ``Record.of``)."""
        return Record.of(self.payload_fields, cells)

    def classification(self, cells: Mapping[Field[object], object]) -> Record:
        """Build a classification row over ``columns`` (validated by ``Record.of``)."""
        return Record.of(self.columns, cells)

    def task(self, task_id: str, payload: Record, classifications: Sequence[Record]) -> "Task":
        return Task.create(self, task_id, payload, classifications)

    def store_columns(self) -> tuple[tuple[str, FieldKind], ...]:
        """The DERIVED persistence column spec (ADR-0012 P1: the store does not
        re-author the column types — it reads them here). Payload fields are stored as
        task context; classification columns are stored per adjudicated row."""
        out: list[tuple[str, FieldKind]] = []
        for f in self.payload_fields:
            out.append((f"payload_{f.name}", f.kind))
        for f in self.columns:
            out.append((f"cls_{f.name}", f.kind))
        return tuple(out)


# =========================================================================== Task
@dataclass(frozen=True)
class Task:
    """A unit handed to a Frontend: one payload (over ``schema.payload_fields``) plus
    a batch of classifications (each over ``schema.columns``). ``create`` validates
    both against the schema, so a task whose payload/classification shapes do not fit
    the schema is unconstructable. SINGLETON tasks may carry one-or-more
    classifications (each adjudicated individually); BATCH tasks carry the group
    adjudicated as a whole — the count is not constrained, only the per-record shape."""

    schema: Schema
    task_id: str
    payload: Record
    classifications: tuple[Record, ...]

    @classmethod
    def create(cls, schema: Schema, task_id: str, payload: Record,
               classifications: Sequence[Record]) -> "Task":
        if payload.fields != schema.payload_fields:
            raise ValueError(
                f"task {task_id!r}: payload fields {[f.name for f in payload.fields]} do not "
                f"match schema {schema.key!r} payload_fields {[f.name for f in schema.payload_fields]}.")
        if not classifications:
            raise ValueError(f"task {task_id!r}: no classifications to adjudicate.")
        for i, c in enumerate(classifications):
            if c.fields != schema.columns:
                raise ValueError(
                    f"task {task_id!r}: classification[{i}] columns {[f.name for f in c.fields]} "
                    f"do not match schema columns {[f.name for f in schema.columns]}.")
        return cls(schema, task_id, payload, tuple(classifications))


# =================================================================== Adjudication
@dataclass(frozen=True)
class Adjudication:
    """The verdict a human/LLM Frontend renders. Its SHAPE is tied to the schema's
    mode at construction (ADR-0000): a SINGLETON adjudication MUST name which
    classification row it judges (``row_index`` in range); a BATCH adjudication MUST
    NOT (``row_index is None`` — it judges the whole group). The verdict MUST be a
    member of the schema's vocabulary. Each of these is a construction-time refusal,
    so an adjudication that contradicts its schema's mode or carries a rogue verdict
    cannot exist to be persisted or published."""

    schema_key: str
    task_id: str
    verdict: Verdict
    row_index: int | None
    note: str = ""

    @staticmethod
    def _check_mode_shape(schema: Schema, row_index: int | None) -> None:
        """The schema-ONLY mode/shape invariant (verdict-vocabulary aside): SINGLETON
        requires a row_index, BATCH forbids it. Shared by EVERY constructor — ``make``
        (task-bearing) and ``rehydrate`` (task-less) — so there is ONE gate over all
        producers, never a per-site subset (ADR-0000 / ADR-0012 P1: one invariant over
        all writers, not N partial re-validations)."""
        match schema.mode:
            case AdjudicationMode.SINGLETON:
                if row_index is None:
                    raise ValueError(
                        f"schema {schema.key!r} is SINGLETON: an adjudication must name the "
                        "classification row it judges (row_index is required).")
            case AdjudicationMode.BATCH:
                if row_index is not None:
                    raise ValueError(
                        f"schema {schema.key!r} is BATCH: an adjudication judges the whole group, "
                        "so row_index must be None.")
            case _:
                assert_never(schema.mode)

    @classmethod
    def make(cls, schema: Schema, task: Task, verdict: Verdict, *,
             row_index: int | None = None, note: str = "") -> "Adjudication":
        """The task-bearing gate (a human/LLM frontend has the task). Adds the
        in-RANGE check ``make`` alone can do (it needs the task's row count) on top of
        the shared verdict + mode/shape invariant."""
        if verdict not in schema.verdicts:
            raise ValueError(
                f"verdict {verdict.name!r} not in schema {schema.key!r} vocabulary "
                f"{[v.name for v in schema.verdicts.verdicts]}.")
        cls._check_mode_shape(schema, row_index)
        if row_index is not None and not (0 <= row_index < len(task.classifications)):
            raise ValueError(
                f"row_index {row_index} out of range for task with "
                f"{len(task.classifications)} classification(s).")
        return cls(schema.key, task.task_id, verdict, row_index, note)

    @classmethod
    def rehydrate(cls, schema: Schema, schema_key: str, task_id: str, verdict_name: str,
                  row_index: int | None, note: str) -> "Adjudication":
        """The ONE task-less reconstruction gate — used by BOTH ``store.load`` and
        ``bus.wire.decode_adjudication`` so a persisted row and a wire frame are
        validated identically (the verdict is a vocabulary member; the row_index
        agrees with the schema's mode). The in-range check is omitted only because no
        task is present; everything checkable from the schema alone IS checked, closing
        the asymmetry where one reconstruction site validated less than another."""
        verdict = schema.verdicts.member(verdict_name)  # rogue verdict refused (ADR-0002)
        cls._check_mode_shape(schema, row_index)
        return cls(schema_key, task_id, verdict, row_index, note)


# ===================================================================== RenderModel
@dataclass(frozen=True)
class RenderModel:
    """The pure projection of (schema, task) that BOTH Frontends consume — the SSOT
    for "what the interface shows" (ADR-0012 P1). The Textual surface builds widgets
    from it; the headless/LLM driver serializes it to a text transcript from it.
    There is no second description of the surface: one ``render`` feeds both, so the
    human and the autonomous LLM adjudicate against byte-identical content."""

    schema_key: str
    title: str
    task_id: str
    prompt: str
    preview_title: str
    preview_body: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    verdict_options: tuple[Verdict, ...]
    mode: AdjudicationMode

    def transcript(self) -> str:
        """The headless/LLM serialization of the surface — derived from the SAME
        fields the TUI widgets are derived from (no second source of truth)."""
        lines = [f"# {self.title}  [task {self.task_id}, mode={self.mode.value}]",
                 "", self.prompt, "",
                 f"--- {self.preview_title} ---", self.preview_body, "",
                 "Classifications:", "\t".join(self.columns)]
        for r in self.rows:
            lines.append("\t".join(r))
        lines.append("")
        lines.append("Verdicts: " + ", ".join(f"{v.name} ({v.description})"
                                               for v in self.verdict_options))
        return "\n".join(lines)


def render(schema: Schema, task: Task) -> RenderModel:
    """THE one projection (schema, task) -> render-model. Every Frontend derives its
    surface from this; nothing re-describes the surface independently."""
    prompt = schema.prompt.render(task.payload)
    preview_body = task.payload.render(schema.preview.field)
    columns = tuple(f.name for f in schema.columns)
    rows = tuple(tuple(c.render(f) for f in schema.columns) for c in task.classifications)
    return RenderModel(
        schema_key=schema.key,
        title=schema.title,
        task_id=task.task_id,
        prompt=prompt,
        preview_title=schema.preview.title,
        preview_body=preview_body,
        columns=columns,
        rows=rows,
        verdict_options=schema.verdicts.verdicts,
        mode=schema.mode,
    )
