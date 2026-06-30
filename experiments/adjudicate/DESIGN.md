# `adjudicate` — design

A reusable **human-OR-LLM interface for HITL machine-learning / auto-deduction
adjudication**. The [domain-schema](GLOSSARY.md#domain-schema) (the Python type
artifact, **not** the SQL schema) is the first-class thing that determines how the
interface interacts; the widget renders, *from* a schema, a prompt + a less-style
preview pager + a table of unsupervised [classifications](GLOSSARY.md#classification),
and collects [adjudications](GLOSSARY.md#adjudication).

This document is the SSOT everything downstream derives from. It is governed by three
chocofarm ADRs read in full: **ADR-0000** (type-driven design — illegal states
unrepresentable), **ADR-0012** (compositional/structural hygiene — P1 SSOT, P2 seams,
P8 typed signatures), **ADR-0013** (anti-work-shirking — the widget is built
first-class and generic even though this subproject needs little data).

- Location: `experiments/adjudicate/` — a standalone package, sibling to
  `fact-mining/`, depended on by this subproject **and** the parent coref hook.
- Status: **doc-selection LIVE end-to-end**; **coref-adjudication DEFINED** (types +
  a schema instance + a stub grounding source), not wired to the unbuilt hook.
- Gates: `mypy --strict` clean (19 files, `mypy.ini`), `pytest` green (43 tests).
- Env: `~/w/vdc/venvs/generic` + `textual` 8.2.8 + `sqlalchemy` 2.0.51 (pure-Python;
  `jax`/`jaxlib` verified **unchanged** at 0.10.1 after install).

Run it:
```
cd experiments/adjudicate
python -m app --corpus rfc --limit 20 --frontend headless          # autonomous, no LLM
python -m app --corpus tei --limit 10 --frontend textual           # human TUI
MYPYPATH=. python -m mypy --config-file mypy.ini .                  # strict gate
python -m pytest tests/ -q                                          # suite
```

---

## 1. The domain-schema as type-driven types (ADR-0000)

The schema (`schema.py`) is the SSOT. The design question came **first** (ADR-0000
Rule 1): *what types make an incoherent {prompt, preview, classification-table,
adjudication-mode} unrepresentable?* The answer is split across two enforcement
surfaces, **declared honestly** (ADR-0011 Rule 1):

- **Closed axes → exhaustive variants, mypy-checked.** [field-kind](GLOSSARY.md#field-kind)
  (`TEXT|INT|FLOAT`), [preview-source](GLOSSARY.md#preview-source),
  [adjudication-mode](GLOSSARY.md#adjudication-mode) (`SINGLETON|BATCH`), and the prompt
  segment union are sealed; every consumer matches them with `typing.assert_never`. A
  forgotten case is a **compile error**, not a runtime `KeyError` — the BoundedBatch
  move of ADR-0000 Specimen 1 (the class is foreclosed, not clamped downstream).
- **Cross-references → construction-time refusal** (the [coherence-gate](GLOSSARY.md#coherence-gate);
  the Port/ACL of ADR-0012 P2). A `Schema`/`Record`/`Task`/`Adjudication` that would
  render an incoherent surface **cannot be constructed**, so it never reaches a
  Frontend. Python cannot express a row-typed compile error over a heterogeneous
  record, so this is the strongest faithful surface — and it is named as such
  (`construction/import-time raise`), exactly as `nla_lab/contract.py` uses an ABC +
  `__init_subclass__` raise rather than a names-only `Protocol`.

### What a schema instance declares

```python
@dataclass(frozen=True)
class Schema:
    key: str
    title: str
    prompt: PromptTemplate            # a question over payload_fields
    payload_fields: tuple[Field, ...] # the interpolation/preview namespace
    preview: PreviewSource            # which payload TEXT field the pager renders
    columns: tuple[Field, ...]        # the classification-table column spec
    verdicts: VerdictVocabulary       # the closed adjudication outcome set
    mode: AdjudicationMode            # SINGLETON | BATCH
    table: str                        # persistence table; the DDL is DERIVED, not restated
```

The prompt is **not** a `str.format` template. It is a sequence of segments, each a
literal or a `FieldSegment` holding a [field](GLOSSARY.md#field) *object*:

```python
PromptTemplate.build("Include this document?  source=", DOC_SOURCE,
                     "  length=", DOC_TEXT_LEN, " chars")
```

Because an interpolation slot *is* a field object (there is no name to typo), and
`Schema.__post_init__` checks the prompt's referenced fields are a subset of
`payload_fields`, **a prompt that interpolates a non-existent field is
unrepresentable**.

### The unrepresentability proof (a sample of the coherence-gate)

Each of these raises at construction — the test suite (`tests/test_schema_coherence.py`)
asserts all of them:

| Incoherent intent | Refused by | Result |
| --- | --- | --- |
| prompt interpolates a non-payload field | `Schema.__post_init__` | `ValueError: not in payload_fields` |
| preview points at a non-payload field | `Schema.__post_init__` | `ValueError: not a payload field` |
| preview points at a non-TEXT field | `Schema.__post_init__` | `ValueError: not text` |
| empty `payload_fields` / `columns` | `Schema.__post_init__` | `ValueError: empty` |
| empty verdict-vocabulary | `VerdictVocabulary.__post_init__` | `ValueError: non-empty` |
| a record missing/extra a field | `Record.of` | `ValueError: missing/extra` |
| a wrong-typed cell (str in an INT field) | `Record.of` | `TypeError: requires int` |
| a SINGLETON adjudication with no `row_index` | `Adjudication.make` | `ValueError: row_index is required` |
| a BATCH adjudication with a `row_index` | `Adjudication.make` | `ValueError: must be None` |
| a verdict outside the vocabulary | `Adjudication.make` | `ValueError: not in schema vocabulary` |
| a classification over the wrong field set | `Task.create` | `ValueError: do not match schema columns` |

Past these constructors a `Schema` is *guaranteed* to render a coherent
{prompt, preview, classification-table, adjudication-mode}, and an `Adjudication` is
*guaranteed* to fit its schema's mode and vocabulary. That guarantee is the types'
whole reason to exist.

### The persistence mapping

`Schema.store_columns()` **derives** the column spec (payload fields as task context,
columns as per-row context), and `FieldKind` is the one owner of the SQL type
(`store._sa_type`, matched exhaustively). The DDL is never hand-restated (ADR-0012 P1);
adding a `FieldKind` forces a case in `_sa_type` (`assert_never`), never a silent
untyped column.

---

## 2. The protocol seams (ADR-0012 P2 / "every seam a protocol, ≥1 real adapter + the second designed-for")

Each seam (`protocols.py`) takes the `Schema` as **data**; a new adapter is added
behind the seam with **zero edits** to the schema or the other seams (the inversion of
control P2 mandates).

| Seam | Protocol | Real now | Designed-for |
| --- | --- | --- | --- |
| [Frontend](GLOSSARY.md#frontend-protocol) | `adjudicate(schema, tasks) -> adjudications` | **`TextualFrontend`** (human TUI) **and** **`HeadlessFrontend`** (policy-driven — the LLM-driver mechanism). *Two* real adapters, both deriving from `render`. | a web/HTTP surface (same protocol, remote transport) |
| [Bus](GLOSSARY.md#bus-protocol) | `poll(schema) -> tasks`; `publish(adjudications)` | **`InProcessBus`** — degenerate single-process queue (the brief's "degenerate but real" seam) | **`ZmqBus`** — ZMQ-shaped, for the parent coref project's orchestration; kept an adapter because whether it ends up ZMQ depends on what claude-code hooks allow |
| [Store](GLOSSARY.md#store-protocol) | `ensure_schema`; `persist`; `load` | **`SqlStore`** (SQLAlchemy Core) over **SQLite** (pilot) *and* **psql** (prod, the harness `postgresql+psycopg://` at 192.168.122.1) through one URL-parameterized adapter | a non-SQL store (e.g. JSONL) behind the same protocol |

**Serialization split from transport (ADR-0012 P7).** The `bus.wire` codec is the one
authoritative classification/adjudication serializer, derived from the `Schema` on both
ends (no second hand codec). `InProcessBus` and `ZmqBus` share it; `ZmqBus` defers only
the *socket* behind an injected `Transport` (send/recv frames), so the reusable codec +
framing is real and tested (`tests/test_store_and_bus.py::test_zmq_wire_codec_roundtrips…`)
while binding an actual `zmq` socket stays a future adapter detail.

---

## 3. One schema, both surfaces, no second source of truth (ADR-0012 P1)

The pivot is the [render-model](GLOSSARY.md#render-model):

```python
def render(schema: Schema, task: Task) -> RenderModel   # the ONE projection
```

`RenderModel` is a pure dataclass carrying the interpolated prompt, the preview
title+body, the column headers, the stringified classification rows, the verdict
options, and the mode. **Both** frontends consume it and nothing else:

- `TextualFrontend` (`frontend_textual.py`) builds its `Static` prompt, its
  `VerticalScroll` less-style pager, its `DataTable`, and its verdict key-bindings from
  the render-model.
- `HeadlessFrontend` (`frontend_headless.py`) calls `RenderModel.transcript()` —
  derived from the *same* fields — and hands the text to a [policy](GLOSSARY.md#policy).

So "autonomous Sonnet runs it" and "a human runs it" are **two adapters of one seam**,
adjudicating against byte-identical content. The LLM driver is **not a separate code
path**: it is `HeadlessFrontend` with an `LLMPolicy` whose only deferred piece is a
`complete(prompt) -> str` seam (a real Claude call, or a test fake). `RulePolicy` is the
real, autonomous, no-LLM policy (accept the model's suggested label) that runs
doc-selection end-to-end today and honors the "no LLM for the PoC" constraint.

`tests/test_render_ssot.py` asserts the equality directly: the transcript carries the
render-model's prompt/preview/rows, and the Textual app (driven via Textual's headless
`run_test` pilot) shows the same prompt and row count and returns the keypress verdict.
`tests/test_headless_drives_frontend.py` asserts the LLM policy sees the *same*
transcript the human surface renders.

`tests/test_frontend_parity.py` discharges the load-bearing proof: for the **same
schema+input**, the human `TextualFrontend` and the headless `HeadlessFrontend` (both
typed as `protocols.Frontend`) produce the **same adjudication contract** —
`(schema_key, task_id, verdict, row_index)` per `Adjudication`, the `note` excluded as
provenance — across **both** modes (SINGLETON doc-selection incl. a row-by-row two-row
case, BATCH coref) and **both** drivers (`RulePolicy`, `LLMPolicy`). It drives the
headless surface first and presses exactly the verdict the policy chose, so the claim is
*interchangeability for any decision*, not a fixed answer that happens to coincide.

---

## 4. The two concrete schema instances (the abstraction covers both)

Both in `instances.py`, built from the one type system — that a singleton and a batch
schema with different fields/preview/columns/verdicts need **no** change to the schema
types is the coverage proof (ADR-0013: first-class and generic, not a doc-selection-only
throwaway).

### doc-selection — SINGLETON (this subproject, LIVE)
- **payload fields:** `source`, `domain`, `text_len:int`, `word_count:int`, `body`
- **prompt:** "Include this document in the training corpus? source={source} domain={domain} length={text_len} chars / {word_count} words"
- **preview:** the document `body` in the pager
- **columns:** `suggested` (a verdict name), `rationale` (e.g. "difficult coref-resolution example -> include"), `score:float`
- **verdicts:** `include` | `exclude`
- **mode:** `SINGLETON` (one document → one classification row → one verdict)

### coref-adjudication — BATCH (parent project, DEFINED not wired)
- **payload fields:** `context`, `explanation`, `doc`
- **prompt:** "Coreference adjudication for context: {context}"
- **preview:** the hook's `explanation` text in the pager
- **columns:** `antecedent`, `anaphor`, `grounding_source`, `confidence:float` — the NLP service's knowledge-grounding rows
- **verdicts:** `coreferent` | `not-coreferent` | `uncertain`
- **mode:** `BATCH` (a cluster of mention-pair rows → one verdict for the group)

`loaders.coref_stub_tasks` supplies the stub grounding source (placeholder mention-pair
rows) so the BATCH schema is exercised without the unbuilt hook
(`tests/test_loaders_and_instances.py`, `test_headless_drives_frontend.py::…batch…`).

---

## 5. Located corpora + the doc-source field-extraction plan

Both corpora were located on host (not re-downloaded):

- **RFCs:** `/home/bork/distill/rfc/` — ~9,800 `rfc*.txt` plain-text files (plus
  `bcp/`, `fyi/`, `ien/` subtrees and `*-index.txt` files the loader ignores). Sample:
  `rfc2616.txt` (HTTP/1.1), header carries a `Category:` line.
- **UNv1.0-TEI:** `/home/bork/distill/UNv1.0-TEI/` — 4.5 GB, `<year>/<body>/.../*.xml`
  in **TEI.2** XML (no namespace). `teiHeader` carries `<idno type="symbol">`, `<term>`
  keywords; `text/body/p/s` carries the sentence text (`<s id="…">…</s>`).

`loaders.py` reads these into the doc-selection [payload](GLOSSARY.md#payload):

| Payload field | RFC (`RfcLoader`) | UN-TEI (`UnTeiLoader`) |
| --- | --- | --- |
| `source` | literal `"rfc"` | literal `"un-tei"` |
| `domain` | the `Category:` header line, slugged (`standards-track`, `informational`, `experimental`, `best-current-practice`, `historic`), else `"rfc"` | the first `<term>` keyword (slugged), else the `idno type="symbol"` prefix (e.g. `CAT`), else `"un-document"` |
| `text_len` | `len(body)` chars | `len(body)` chars |
| `word_count` | `len(body.split())` | `len(body.split())` |
| `body` | the whole file text (latin-1, errors replaced) | the `<s>` sentence texts joined |

Each document is paired with **one** unsupervised classification from a placeholder
length-band heuristic (`_heuristic_suggestion`) standing in for the model whose
suggestions arrive over the Bus — intentionally trivial; it is the *suggestion* a
human/LLM adjudicates, and swapping it for a real model is a loader change with **zero**
schema/Frontend/Store edits. `RFC_ROOT`/`TEI_ROOT` are parameterized so the loaders run
against the documented format even if a path moves.

Verified live: `python -m app --corpus rfc --limit 5 --frontend headless` and
`--corpus tei` both adjudicate + persist real documents end-to-end.

---

## File map

| File | Role |
| --- | --- |
| `schema.py` | the domain-schema SSOT: Field, Record, PromptTemplate, PreviewSource, AdjudicationMode, Verdict, Schema, Task, Adjudication, RenderModel, `render` |
| `protocols.py` | the Frontend / Bus / Store protocol seams |
| `bus.py` | `wire` codec; `InProcessBus` (real); `ZmqBus` (designed-for) |
| `store.py` | `SqlStore` (SQLAlchemy Core, SQLite + psql; DDL derived from schema) |
| `frontend_headless.py` | `HeadlessFrontend`; `Policy`; `RulePolicy` (real); `LLMPolicy` (LLM seam) |
| `frontend_textual.py` | `TextualFrontend` (pilot human surface) |
| `instances.py` | `doc_selection_schema()` (singleton), `coref_schema()` (batch) |
| `loaders.py` | `RfcLoader`, `UnTeiLoader`, `coref_stub_tasks`; the field-extraction plan |
| `docsource.py` | the `DocumentSource[T]` FUNCTOR (`map` = structure-preserving content transform); `UnTeiSource`; the one TEI body/meta parse (shared with `loaders`) |
| `read.py` | `render_paragraphs` (the readable-text content-transform) + the `read` CLI — read a UN-TEI doc as plain paragraphs (see `USAGE.md`) |
| `app.py` | end-to-end doc-selection runner / CLI (+ the `read` subcommand) |
| `mypy.ini` | the `mypy --strict` gate |
| `tests/` | coherence, render-SSOT, headless-drives-frontend, store+bus, loaders+instances |
