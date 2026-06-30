# Contradiction-detection end-to-end demo — design

The settled design for a **real** end-to-end of the project's core epistemic signal:
extract claims from a text → find contradictory pairs by transparent rules → surface
them through the reusable adjudicate widget for human/LLM/rule verdict → record. It is
built **entirely from already-built pieces**, reversibly, and is implemented verbatim
from this document next.

- **Status:** DESIGN SETTLED — implementation pending (this doc is the SSOT it derives from).
- **Where:** `experiments/` (venv `~/w/vdc/venvs/generic`: spaCy 3.8 + `en_core_web_sm`,
  jax 0.10.1; psql harness `host=192.168.122.1 dbname=harness`).
- **Governing ADRs, read in full:** ADR-0000 (type-driven — illegal states
  unrepresentable), ADR-0002 (fail loud / no invented number), ADR-0009 (measured;
  honest toy-vs-real), ADR-0012 P1/P2 (SSOT/reuse; seam adapters), ADR-0013 (no
  de-scope, no mocked demo — a real contradiction found and shown).
- **The thesis it serves:** the project target is a claude-code **hook** interrogating
  an AI collaborator's **epistemic state**. Contradiction is a first-class epistemic
  signal; this demo is the real end-to-end the hook later drives. Gutenberg / RFCs /
  synthetic fixtures are the PoC corpus; the literal target is an AI collaborator
  contradicting itself across turns (the optional `.claude` stretch, §5.3).

---

## 0. What is reused, and what is genuinely new

ADR-0012 P1: reuse, do not fork. The demo adds **no second copy** of any fact a built
piece already owns.

| Concern | One home (REUSED, unchanged) | NEW code |
| --- | --- | --- |
| parse + claim extraction | `extract.build_nlp` + `extract.doc_to_facts` (the SSOT `FactBundle`; coref/entity-resolved `subj_key`/`obj_key`, `negated`) | — consumed, never re-walked |
| the decision surface | `schema.render` → `frontend_headless.HeadlessFrontend` + `RulePolicy` / `LLMPolicy` (and `frontend_textual.TextualFrontend` for a human) | `instances.contradiction_schema()` (a new BATCH schema instance) |
| the persistence seam | `protocols.Store` (the package already names "a non-SQL store … behind the same protocol" as the **designed-for second adapter**) | `contra_store.ContraStore` — that second adapter, over psql `contra` |
| the harness DSN | `spans.DEFAULT_DSN` (`HARNESS_DSN`-overridable) | — referenced, not re-typed |
| the corpus loaders | `loaders.RfcLoader` / `docsource` TEI parse (for the real-doc body) | `loaders.contra_finding_tasks` (read `contra.finding` → BATCH `Task`s) |

Genuinely new, and only this:

- `experiments/fact-mining/contra_detect.py` — claim normalisation + the three
  contradiction rules + the `Finding` shape (a **pure function of a `FactBundle`** — no
  second parse).
- `experiments/fact-mining/contra_schema.sql` — the reversible `contra` psql schema DDL.
- `experiments/fact-mining/fixtures/contra_synthetic.txt` — the planted-contradiction fixture.
- `experiments/fact-mining/test_contra_detect.py` — asserts the planted findings (the
  ADR-0013 Rule 5 artifact check: the demo is a checkable test, not a narrated claim).
- `experiments/adjudicate/instances.py` — **add** `contradiction_schema()` (one function).
- `experiments/adjudicate/loaders.py` — **add** `contra_finding_tasks(schema, store)`.
- `experiments/adjudicate/contra_store.py` — `ContraStore` (the `protocols.Store` adapter
  + the one gateway to the `contra` schema; SqlStore is **untouched**).
- `experiments/adjudicate/contra_app.py` — the end-to-end runner (parallels `app.py`).

**Cross-package coupling is the psql `contra.finding` rows, not a Python import.** The
fact-mining detector writes `contra.finding`; the adjudicate loader reads `contra.finding`.
The two packages meet only at that one authoritative wire (ADR-0012 P2), exactly as the
mining loader and the per-logic views meet only at the `mining` tables.

---

## 1. The pipeline

```
text
  │  extract.build_nlp(...).pipe([paragraphs])         # REUSE (local | --remote daemon | cached)
  ▼
spaCy Doc(s)
  │  extract.doc_to_facts(doc)  ──►  FactBundle         # REUSE the SSOT extractor (no re-walk)
  ▼
FactBundle{ sents, entities, temporal, triples }        # triples: subj/pred/obj + subj_key/obj_key + negated
  │  contra_detect.claims_from_bundle(bundle, source_doc)
  ▼
list[Claim]                                             # normalised: canonical keys + surface + sentence + parsed number
  │  contra_detect.find_contradictions(claims, FUNCTIONAL_PREDS)
  ▼
list[Finding]                                           # (claim_a, claim_b, rule, grounding)  — §2
  │  ContraStore.insert_findings(source_doc, findings)  # idempotent INSERT … ON CONFLICT DO NOTHING
  ▼
contra.finding rows  ◄────────────────────────────────  the one home for "what the rules found"
  │  loaders.contra_finding_tasks(schema, store)         # rows → BATCH Task (one per finding)
  ▼
list[Task]
  │  HeadlessFrontend(RulePolicy(CONTRA_SUGGESTED)).adjudicate(schema, tasks)   # REUSE verbatim
  │      (swap in TextualFrontend for a human, or LLMPolicy for an LLM — same seam)
  ▼
list[Adjudication]
  │  ContraStore.persist(schema, task, adjs)             # finding_id ← task_id; verdict; adjudicator; ts
  ▼
contra.adjudication rows  ──►  ContraStore.load / contra.review view  (read back, print)
```

`Claim` (the normalisation, the new bridge type) carries exactly what the rules read,
all **derived from the `FactBundle`** (ADR-0000: it adds no fact the extractor did not
already produce):

```python
@dataclass(frozen=True)
class Claim:
    subj_key: str        # canonical subject constant (coref + entity resolved) — the join key
    pred: str            # verb lemma (the predicate)
    obj_key: str         # canonical object constant
    negated: bool        # spaCy `neg` dependency on the verb (already in TripleRecord)
    subj_surface: str    # human-readable subtree text (for grounding)
    obj_surface: str
    sent_i: int          # provenance: sentence index
    sent_text: str       # provenance: the source sentence
    number: float | None # parsed numeric value of the object, or None if the object is not a number
```

`claims_from_bundle` zips `bundle["triples"]` with `bundle["sents"]` (by `sent`/`index`)
and runs the **transparent numeric parser** on each object surface (digits via `float`,
plus a small spelled-number map `one…twelve`); a surface that does not parse leaves
`number=None` — **it never guesses** (ADR-0002 rule 3: no sentinel-as-value). Claims with
an empty `subj_key` or `obj_key` (unresolved pronoun / punctuation — not usable constants)
are dropped, exactly as `mining.fact_classical` excludes them.

---

## 2. The three contradiction rules (and the honest confidence posture)

A **transparent logic-layer first pass — explicitly NOT claimed NLP-grade.** Each rule is
a pure predicate over a pair of `Claim`s; each finding records its **rule-id and its source
spans**, and **no fabricated probability anywhere** (§2.4). This is the demonstrator and
the scaffold the logic layer (Prolog/ASP/SMT) later replaces — every finding is labelled
with the rule that fired and the exact evidence, so a reader calibrates from the grounding,
not from a number the system invented.

All three join candidate pairs on the **canonical** keys the extractor already computed
(`subj_key`, `pred` lemma) — the same keys `mining.contradiction` joins on — so coref /
entity resolution is what lets "France" and "the country" be the same subject.

### R-NEG — negation / polarity clash

Two claims share `(subj_key, pred, obj_key)`, one with `negated=False` and one with
`negated=True`. **From the parse:** `negated` is `extract_triples`' existing
`any(c.dep_ == "neg" for c in verb.children)` — spaCy's `neg` dependency ("not", "n't").
R-NEG is exactly the `mining.contradiction` VIEW's logic (positive vs negative at the same
canonical S-P-O), lifted from a passive view into the finding→adjudication flow.
*Grounding:* both sentences, both subtree spans, the shared `(subj_key, pred, obj_key)`,
and `polarity: asserted vs denied`.
*Honest caveat (recorded, not hidden):* same lemma + same canonical object does not
guarantee same word **sense**, and negation **scope** can attach to a different clause; the
rule surfaces the spans and the adjudicator decides. No NLP-grade claim is made.

### R-FUNC — incompatible object on a functional predicate

Two claims share `(subj_key, pred)`, both `negated=False`, with **different** `obj_key`,
where `pred` is on a **curated functional-predicate allowlist** `FUNCTIONAL_PREDS`
(predicates that admit at most one object per subject: `be`, `capital`, `bear` (born-in),
`equal`, `locate`, …). **From the parse:** `pred` is the verb lemma `doc_to_facts` emits;
copular "X is Y" surfaces as `pred="be"` with the attribute as the object. The functionality
judgement lives **entirely** in the explicit allowlist — it is the precision control, and it
is **visible in the grounding**, never hidden. A predicate not on the list (e.g. `visit`,
`like`) does not fire, by construction, so "Marie visited Paris / Lyon" is correctly silent.
*Grounding:* both spans, the shared `(subj_key, pred)`, the two differing objects, and
`functional-by: <allowlist entry that licensed it>`.
*Honest caveat:* functionality is a property of the predicate's **meaning**, which spaCy
does not know; the allowlist is a hand-curated stand-in. This is the honest first-pass
scaffold a real functional-dependency declaration in ASP/SMT later replaces — and the
allowlist entry is named in every finding so the reader sees precisely what licensed it.

### R-NUM — numeric mismatch

Two claims share `(subj_key, pred)`, both `negated=False`, with `number` set on both and
`number_a != number_b`. **From the parse / normalisation:** `Claim.number` is the
transparent parse of the object surface (digits + the small spelled-number map); a
non-numeric or unparseable object has `number=None` and cannot match. "The committee has
three members / five members" → `3.0` vs `5.0` → finding.
*Grounding:* both spans, the shared `(subj_key, pred)`, and the two **parsed numbers**.
*Honest caveat:* units / scales ("3 metres" vs "5 feet"), hedges ("about three"), and
predicate sense are **not** modelled; surfaced, not claimed. R-NUM is formally a numeric
sub-case of R-FUNC but kept a distinct rule because its evidence (two values) is sharper
grounding and a different downstream logic (arithmetic / SMT) replaces it.

### 2.4 Confidence posture — the rule-id IS the confidence; no invented number

ADR-0002 + ADR-0009 are decisive here: **an epistemic-state interrogator must not invent
the very numbers it reports.** So:

- Every finding carries `rule` (`R-NEG` | `R-FUNC` | `R-NUM`) and `grounding` (the spans +
  the rule-specific evidence). **That pair is the confidence** — transparent provenance, not
  a probability.
- **No probability/score column exists in the contradiction adjudicate schema** (contrast
  the coref schema's `confidence: float`, which held a **real** NLP-model score — we have
  no such score, so emitting one would be the ADR-0002 fabrication / ADR-0009
  unsubstantiated-claim failure). The honesty is made **type-driven** (ADR-0000): the schema
  declares **no `FLOAT` field at all**, so a fabricated confidence is *unrepresentable* —
  the demo cannot emit a number it did not measure because the type has no slot for one.
- Rule reliability is **not** encoded as a fabricated ordering either; if a tier is ever
  wanted it must be a **measured** precision/recall on a labelled set (ADR-0009), recorded
  as such — not a guessed float. Until measured, the rule-id + grounding stand alone.

---

## 3. The contradiction-adjudication schema (a new `instances.py` BATCH instance) + the loader

A **new schema instance**, built from the one type system in `schema.py` — no schema-type
edits (ADR-0013: the widget is generic, this is the coverage proof, like coref was).

### 3.1 `instances.contradiction_schema()` — BATCH

```python
# payload fields (the finding's intrinsic, interpolated/previewed context)
CONTRA_SOURCE      = Field.text("source_doc")
CONTRA_SUBJECT     = Field.text("subject")       # the shared canonical subj_key
CONTRA_PREDICATE   = Field.text("predicate")     # the shared pred lemma
CONTRA_EXPLANATION = Field.text("explanation")   # previewed: both sentences/spans + the rule's evidence
# classification columns (the evidence row the verdict adjudicates) — ALL TEXT (no float; §2.4)
CONTRA_CLAIM_A   = Field.text("claim_a")
CONTRA_CLAIM_B   = Field.text("claim_b")
CONTRA_RULE      = Field.text("rule")            # R-NEG | R-FUNC | R-NUM
CONTRA_GROUNDING = Field.text("grounding")       # the rule-specific evidence (allowlist entry / numbers / polarity)
CONTRA_SUGGESTED = Field.text("suggested")       # a verdict name — what RulePolicy reads

CONTRA_YES    = Verdict("contradiction",     "the two claims genuinely contradict")
CONTRA_NO     = Verdict("not-contradiction", "the rule fired but the claims are compatible")
CONTRA_UNSURE = Verdict("uncertain",         "insufficient evidence to decide")

def contradiction_schema() -> Schema:
    return Schema(
        key="contradiction-adjudication",
        title="Contradiction adjudication",
        prompt=PromptTemplate.build(
            "Are these two claims contradictory?  subject=", CONTRA_SUBJECT,
            "  predicate=", CONTRA_PREDICATE),
        payload_fields=(CONTRA_SOURCE, CONTRA_SUBJECT, CONTRA_PREDICATE, CONTRA_EXPLANATION),
        preview=TextFieldPreview(CONTRA_EXPLANATION, title="contradiction grounding"),
        columns=(CONTRA_CLAIM_A, CONTRA_CLAIM_B, CONTRA_RULE, CONTRA_GROUNDING, CONTRA_SUGGESTED),
        verdicts=VerdictVocabulary((CONTRA_YES, CONTRA_NO, CONTRA_UNSURE)),
        mode=AdjudicationMode.BATCH,
        table="contra_adjudication",   # logical key; ContraStore writes the fixed contra.* DDL
    )
```

- **Columns = `claim_a / claim_b / rule / grounding` (+ `suggested`)** per the brief. The
  pair is one classification **row**; **BATCH** = one verdict for that row-group (here a
  group of one, leaving room for an n-way mutual-contradiction cluster later — the same
  reason coref is BATCH). `suggested` is the one extra column, carrying a **verdict name**
  so the existing `RulePolicy` can consume it (§3.3); it is not a fabricated score.
- All columns are `TEXT` — the §2.4 type-driven no-float guarantee.

### 3.2 `loaders.contra_finding_tasks(schema, store)` — `contra.finding` rows → BATCH Tasks

Mirrors `RfcLoader`/`coref_stub_tasks`: read each `contra.finding` row via the store, build
one BATCH `Task` whose `task_id = str(finding_id)` (the verdict's reference back to the
finding), payload from `(source_doc, subject=subj_key, predicate=pred, explanation)`, and
one classification row `(claim_a, claim_b, rule, grounding, suggested="contradiction")`.
The detector's suggestion is always **"contradiction"** — the rule fired, so the autonomous
provisional verdict is "candidate contradiction", honestly labelled; a human/LLM overrides
through the same surface. `Record.of` / `Task.create` validate the shapes at construction
(ADR-0000): a malformed finding row cannot become a `Task`.

### 3.3 Driving it — the EXISTING `HeadlessFrontend(RulePolicy) → Store` path, verbatim

`HeadlessFrontend(RulePolicy(CONTRA_SUGGESTED)).adjudicate(schema, tasks)` is reused
**unchanged**: for BATCH, `RulePolicy` takes the majority `suggested` value → `"contradiction"`
→ one `Adjudication(row_index=None)` per finding, `note="rule: majority suggestion …"`. The
same `tasks` drive `LLMPolicy` (an LLM reads the identical transcript and answers a verdict
name from the vocabulary) or `TextualFrontend` (a human presses a verdict key) with **zero**
code change — that is the whole point of the seam, and `test_frontend_parity` already proves
the three are interchangeable for any decision.

---

## 4. The `contra` psql schema (NEW, reversible, idempotent)

`experiments/fact-mining/contra_schema.sql`. A clearly-named NEW schema that **never touches
`mining` / `nla` / `trace` / `public`**, drops with one statement, and is re-runnable.

```sql
-- experiments/fact-mining/contra_schema.sql
-- NEW, REVERSIBLE contradiction store. Idempotent + re-runnable.
-- REWIND (the exact command):  DROP SCHEMA contra CASCADE;
-- Touches NOTHING else: mining / nla / trace / public are never referenced.

CREATE SCHEMA IF NOT EXISTS contra;

-- a candidate contradiction the transparent rules found (the detector's one home)
CREATE TABLE IF NOT EXISTS contra.finding (
  finding_id  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_doc  text NOT NULL,                       -- provenance: the document the claims came from
  rule        text NOT NULL,                       -- 'R-NEG' | 'R-FUNC' | 'R-NUM'  (the rule-id IS the confidence)
  subj_key    text NOT NULL,                       -- canonical subject the two claims share (the join key)
  pred        text NOT NULL,                       -- predicate lemma the two claims share
  claim_a     text NOT NULL,                       -- human-readable claim A
  claim_b     text NOT NULL,                       -- human-readable claim B
  span_a      text NOT NULL,                       -- source sentence grounding claim A
  span_b      text NOT NULL,                       -- source sentence grounding claim B
  grounding   text NOT NULL,                        -- the rule-specific evidence (allowlist entry / numbers / polarity)
  extra       jsonb NOT NULL DEFAULT '{}'::jsonb,  -- additive escape hatch (char offsets, sent ids)
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_doc, rule, subj_key, pred, claim_a, claim_b)   -- re-run = idempotent (no duplicate finding)
);

-- a verdict on a finding (rule / human / llm), via the REUSED adjudicate stack
CREATE TABLE IF NOT EXISTS contra.adjudication (
  adjudication_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  finding_id  bigint NOT NULL REFERENCES contra.finding ON DELETE CASCADE,
  verdict     text NOT NULL,                       -- 'contradiction' | 'not-contradiction' | 'uncertain'
  adjudicator text NOT NULL,                       -- 'rule:auto' | 'llm' | a human id
  note        text NOT NULL DEFAULT '',            -- the adjudicate Adjudication.note (policy provenance)
  ts          timestamptz NOT NULL DEFAULT now()
);

-- convenience projection for review (DERIVED, not a third store — ADR-0012 P1)
CREATE OR REPLACE VIEW contra.review AS
  SELECT f.finding_id, f.source_doc, f.rule, f.subj_key, f.pred,
         f.claim_a, f.claim_b, f.grounding,
         a.verdict, a.adjudicator, a.ts
  FROM contra.finding f
  LEFT JOIN contra.adjudication a USING (finding_id);
```

- **Idempotent + re-runnable:** `CREATE … IF NOT EXISTS` + the `finding` `UNIQUE` constraint
  (the loader inserts `… ON CONFLICT DO NOTHING`), so re-running the detector on the same doc
  adds no duplicate. Applying the file twice is a no-op.
- **One writer per fact (P1):** `contra.finding` is written only by the detector path;
  `contra.adjudication` only by `ContraStore.persist`; `contra.review` is a derived view, not
  a third store. `finding ↔ adjudication` link = `task_id == str(finding_id)`.
- **`ContraStore`** (the new `protocols.Store` adapter — the package's designed-for second
  Store adapter, P2) is the **single gateway** to this schema (P3 one-owner): `ensure_schema`
  runs this DDL; `insert_findings`/`findings` serve the detector + loader; `persist`/`load`
  move verdicts. `SqlStore` is **untouched** — `ContraStore` is a new adapter, not a fork. It
  reaches the DB via `spans.DEFAULT_DSN` (the one-home DSN), through `psycopg` exactly as
  `load_facts.py` does.
- **Rewind:** `DROP SCHEMA contra CASCADE;` — recorded here and in the SQL header.

---

## 5. The data plan

### 5.1 Synthetic planted-contradiction fixture (committed; public/synthetic)

`experiments/fact-mining/fixtures/contra_synthetic.txt` — proves detection **fires on known
cases** and that the gates **suppress the obvious false positives**. One planted pair per
rule, plus decoys that share a subject but must stay silent, plus a clean control paragraph:

- **R-NEG:** "Socrates is mortal." / "Socrates is not mortal." → fires.
- **R-FUNC:** "The capital of France is Paris." / "The capital of France is Lyon." → fires
  (`be` on the allowlist). Decoy: "Marie visited Paris." / "Marie visited Lyon." → **silent**
  (`visit` not on the allowlist).
- **R-NUM:** "The committee has three members." / "The committee has five members." → fires.
  Decoy: "The shelf holds three books." / "The shelf holds three novels." → **silent** (same number).
- **Control:** a consistent paragraph with no planted clash → no findings.

`test_contra_detect.py` asserts the **exact** finding set (the `{(rule, subj_key, pred)}` it
must produce and the decoys it must not) — the demo is a checkable artifact, not a narrated
claim (ADR-0013 Rule 5; ADR-0002 fail-loud test). The fixture is fully synthetic, contains
no private content, and is safe to commit.

### 5.2 Real `~/distill` document (proves the pipeline runs on real text)

Primary: an RFC — `/home/bork/distill/rfc/rfc2616.txt` (HTTP/1.1), read through
`extract.load_body`/`normalise` then `build_nlp`/`doc_to_facts` (the same parse the
`RfcLoader` feeds the doc-selection demo). Documented alternative reusing the same loaders: a
UN-TEI paragraph set via `docsource`'s TEI parse. **Honest expectation (ADR-0009):** an RFC is
internally consistent edited prose, so the detector will likely find **few or none** — and
that is the correct, honest outcome, not a failed demo. We report the **real** numbers (claims
extracted, candidate findings by rule) over a bounded `--max-paras` sample; we do **not** stage
a hit. A real run that finds little, reported truthfully, is the ADR-0013 anti-mock standard
met — the contrast is precisely the synthetic fixture, where planted contradictions are *known*
to exist and the detector is shown firing on them.

### 5.3 Optional stretch — ephemeral `.claude` self-contradiction (best-effort; skip if messy)

The literal thesis: an AI collaborator contradicting **itself** across turns. Run the detector
over a small sample of assistant turns from `~/.claude/projects/*/*.jsonl`. **EPHEMERAL ONLY,
hard constraints:**

- Gated behind an explicit `--ephemeral-claude` flag; writes findings **only to stdout**,
  **never** to `contra.finding` / the DB / any file.
- Report **aggregate counts** (turns scanned, candidate findings by rule) + at most a few
  **REDACTED / PARAPHRASED** examples.
- **Scrub secrets before any display** (DSNs, tokens, hostnames, absolute paths) with a
  denylist + the `192.168.*` / `host=…` patterns; commit **nothing** private.

If the transcript shapes are awkward, this is skipped without prejudice (brief sanction) — the
committed demo stands on §5.1 (proof it fires) + §5.2 (proof it runs on real text).

---

## Gates & hygiene (binding on the implementation)

- `mypy --strict` clean for the new adjudicate files (`mypy.ini`, the package's gate);
  `contra_detect.py` typed at the same bar. `pytest` green (the existing 43 adjudicate tests
  unchanged + `test_contra_detect.py`). `jax`/`jaxlib` stay **0.10.1** (the detector reuses the
  import-light `extract.py`, which lazy-imports spaCy; no torch/HF on the demo path).
- **No existing schema or data touched** — `mining` / `nla` / `trace` / `public` are never
  referenced; the `contra` schema is the only write surface and `DROP SCHEMA contra CASCADE`
  is the complete rewind.
- Committed as `bork <you@example.com>`, **never pushed** (a human/lead pushes). No private
  `~/.claude` content in any commit.

---

## Terms

This doc reuses adjudicate's coined terms — **domain-schema**, **classification**,
**adjudication-mode**, **verdict-vocabulary**, **render-model** — defined in
`experiments/adjudicate/GLOSSARY.md` (their SSOT). New here: **finding** (a candidate
contradictory claim-pair a rule produced), **rule-id** (`R-NEG`/`R-FUNC`/`R-NUM` — the
transparent confidence), **functional-predicate allowlist** (the curated single-valued-predicate
set R-FUNC gates on).
