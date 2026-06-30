# Glossary — `adjudicate`

The single home (SSOT) for every coined term in this package. Each term is defined
once here; downstream prose wiki-links to it on first use rather than re-defining it
(the maintainer's doc-legibility rule). Anchors are the lowercased hyphenated term.

---

### domain-schema
<a id="domain-schema"></a>
The first-class artifact that determines how the adjudication interface interacts —
**NOT** the SQL schema. A `Schema` instance (`schema.py`) declares, as one
construction-validated unit: a [prompt-template](#prompt-template) over typed
[fields](#field), a [preview-source](#preview-source), a
[classification](#classification)-table column spec, a
[verdict-vocabulary](#verdict-vocabulary), an [adjudication-mode](#adjudication-mode),
and a persistence table name. It is the SSOT everything downstream derives from: the
Textual surface, the headless/LLM driver, the SQLAlchemy DDL, and the prompt text are
all *projections* of it, never restatements. ADR-0000's law applies to it directly —
an incoherent domain-schema is unrepresentable (see [coherence-gate](#coherence-gate)).

### field
<a id="field"></a>
A typed, named slot — `Field(name, kind)`. Its [field-kind](#field-kind) is the SSOT
for the slot's Python type, its rendering, and its store column. Fields are shared
*by value* across the prompt, preview, columns, and records, so they are the reference
that binds the [domain-schema](#domain-schema)'s parts together.

### field-kind
<a id="field-kind"></a>
The closed vocabulary of cell types — `TEXT | INT | FLOAT`. One owner of three
derivations (Python type, string rendering, SQL column type); every consumer matches
it exhaustively (`assert_never`), so adding a kind is a compile-time obligation, never
a silent fail-open.

### record
<a id="record"></a>
A construction-validated value-tuple over a declared [field](#field) set. Both a
document [payload](#payload) and a [classification](#classification) row are records.
`Record.of` is the Port/ACL: it refuses a record whose keys are not exactly the
declared fields or whose cell types do not match their kinds.

### payload
<a id="payload"></a>
The [record](#record) of a document's intrinsic fields (e.g. `source`, `domain`,
`text_len`, `word_count`, `body`) — the namespace the [prompt-template](#prompt-template)
interpolates and the [preview-source](#preview-source) draws from.

### prompt-template
<a id="prompt-template"></a>
A question with interpolated typed fields, built from a sequence of segments that are
either literal text or a [field](#field) *object* (never a `"{name}"` string). Because
an interpolation slot IS a field object, you cannot reference a field that does not
exist — the stringly-typed `KeyError` class is foreclosed.

### preview-source
<a id="preview-source"></a>
Declares what the less-style pager renders: a payload TEXT field (the document body for
doc-selection; the hook's explanation text for coref). A sealed variant — a second
preview kind is a new case the renderer is forced to handle.

### classification
<a id="classification"></a>
One unsupervised suggestion arriving over the [bus-protocol](#bus-protocol) — the
model's proposed label the human/LLM adjudicates (e.g. doc-selection: "difficult
coref-resolution example -> include"; coref: an NLP-service knowledge-grounding row).
Represented as a [record](#record) over the [domain-schema](#domain-schema)'s columns.

### adjudication
<a id="adjudication"></a>
The verdict a [frontend-protocol](#frontend-protocol) renders for a
[classification](#classification) (singleton) or a whole batch (batch). Its shape is
tied to the [adjudication-mode](#adjudication-mode) at construction, and its
[verdict](#verdict) must be a member of the schema's [verdict-vocabulary](#verdict-vocabulary).

### adjudication-mode
<a id="adjudication-mode"></a>
The exhaustive variant `SINGLETON | BATCH` governing how many verdicts a frontend
collects per task. SINGLETON (doc-selection, degenerate) → one verdict per
classification row; BATCH (coref, the parent project) → one verdict for the whole
group. An [adjudication](#adjudication) whose shape contradicts the mode is
unconstructable.

### verdict / verdict-vocabulary
<a id="verdict"></a><a id="verdict-vocabulary"></a>
A **verdict** is one named adjudication outcome (e.g. `include`, `coreferent`). A
**verdict-vocabulary** is the closed, non-empty, ordered set a [domain-schema](#domain-schema)
admits. An [adjudication](#adjudication) may only carry a vocabulary member, so a
typo'd verdict is unrepresentable.

### render-model
<a id="render-model"></a>
The pure projection `render(schema, task) -> RenderModel` that BOTH frontends consume —
the SSOT for "what the interface shows". The Textual surface builds widgets from it;
the headless/LLM driver serializes it to a text transcript from it. One render feeds
both, so a human and an autonomous LLM adjudicate against byte-identical content.

### coherence-gate
<a id="coherence-gate"></a>
The construction-time validation (`Schema.__post_init__`, `Record.of`, `Task.create`,
`Adjudication.make`) that refuses an incoherent instance — a prompt/preview referencing
a non-payload field, mismatched record/column shapes, a mode-contradicting adjudication,
a rogue verdict. This is the honestly-declared enforcement surface
(**construction/import-time raise**, ADR-0011 Rule 1) standing in for the
Python-unreachable row-typed compile error; the closed variants get their teeth from
mypy exhaustiveness instead.

### frontend-protocol
<a id="frontend-protocol"></a>
The seam `adjudicate(schema, tasks) -> adjudications`. Real adapters now:
`TextualFrontend` (human TUI) and `HeadlessFrontend` (policy-driven — the LLM-driver
mechanism). The LLM driver is NOT a separate code path; it is this protocol driven
programmatically with an LLM [policy](#policy).

### policy
<a id="policy"></a>
The decision seam inside `HeadlessFrontend`: `decide(schema, task, render-model) ->
adjudications`. `RulePolicy` (real, autonomous, no LLM — accept the model's suggestion)
and `LLMPolicy` (an injected `complete` seam; Claude or a test fake) are two policies;
swapping the policy is how the same frontend becomes rule-driven or LLM-driven.

### bus-protocol
<a id="bus-protocol"></a>
The seam carrying [classifications](#classification) in / [adjudications](#adjudication)
out. `InProcessBus` (real, degenerate single-process queue) now; `ZmqBus` (ZMQ-shaped,
the parent project's orchestration fabric) designed-for, with the wire codec real and
only the socket deferred.

### store-protocol
<a id="store-protocol"></a>
The backend-agnostic persistence seam. `SqlStore` (SQLAlchemy Core) serves SQLite
(pilot) and psql (prod) through one adapter; the table DDL is derived from the
[domain-schema](#domain-schema)'s columns, never hand-restated.
