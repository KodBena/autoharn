# Contradiction-detection end-to-end demo — run & writeup

A **real, end-to-end** demonstration of the project's core epistemic signal: extract
claims from a text, find contradictory pairs by **transparent rules**, surface them
through the reusable adjudicate widget for a rule/human/LLM verdict, and **record** them
in an isolated, reversible psql schema. It is built **entirely from already-built
pieces** (the fact-mining extractor + the adjudicate decision seam) and adds only the
contradiction-specific glue.

- **Status:** BUILT and RUN end-to-end. Findings recorded in the new `contra` schema;
  nothing in `mining` / `nla` / `trace` / `public` was referenced or touched.
- **The design SSOT this implements:** [`CONTRADICTION-DEMO-DESIGN.md`](CONTRADICTION-DEMO-DESIGN.md)
  (the five settled points, the reuse table, the rule definitions, the schema DDL).
- **Where:** `experiments/` — venv `~/w/vdc/venvs/generic` (spaCy 3.8 + `en_core_web_sm`,
  jax 0.10.1); psql harness `host=192.168.122.1 dbname=harness`.
- **Governing ADRs (read in full):** ADR-0000 (type-driven — illegal states
  unrepresentable), ADR-0002 (fail loud / no invented number), ADR-0009 (measured;
  honest toy-vs-real), ADR-0012 P1/P2 (SSOT/reuse; seam adapters), ADR-0013 (no
  de-scope, no mocked demo — a real contradiction found and shown, not staged).

---

## 1. What it does

```
text
  → extract.build_nlp / doc_to_facts        REUSED extractor → the SSOT FactBundle (no re-parse)
  → contra_detect.claims_from_bundle         pure function of the FactBundle → list[Claim]
  → contra_detect.find_contradictions        R-NEG / R-FUNC / R-NUM → list[Finding]
  → ContraStore.insert_findings              contra.finding  (idempotent ON CONFLICT DO NOTHING)
  → loaders.contra_finding_tasks             rows → BATCH Task
  → HeadlessFrontend(RulePolicy).adjudicate  REUSED decision seam, verbatim → list[Adjudication]
  → ContraStore.persist                      contra.adjudication
  → contra.review                            read back, print
```

The detector is a **transparent logic-layer first pass — explicitly NOT claimed
NLP-grade.** It is a pure function of the `FactBundle` that `extract.doc_to_facts`
already produces: it adds **no second parse** and **no fact the extractor did not
emit**. It normalises the bundle's triples into `Claim`s (canonical coref/entity-resolved
`subj_key`/`obj_key`, predicate lemma, the existing `neg`-dependency `negated` flag, and a
transparently parsed object number) and runs three explicit rules over claim pairs.

**The three rules** (each a pure predicate joining on the canonical keys the extractor
already computed):

- **R-NEG** — polarity clash on `(subj_key, pred, obj_key)`: one claim asserted, one
  denied (reuses spaCy's `neg` dependency, the same logic as the existing
  `mining.contradiction` VIEW, lifted into the finding→adjudication flow).
- **R-FUNC** — differing canonical object on a **functional predicate**: both asserted,
  same `(subj_key, pred)`, different `obj_key`, where `pred` is on the curated
  `FUNCTIONAL_PREDS` allowlist (`be, equal, bear, locate, situate, capital`). The
  allowlist **is** the precision control and is named in every finding's grounding.
- **R-NUM** — numeric mismatch on `(subj_key, pred)`: both asserted, both objects parse
  to a number, and the numbers differ. The parser is transparent (digits + a small
  spelled-number map `one…twelve`); an object that does not parse leaves `number=None`
  and **cannot match** — the system never guesses a number it did not read.

**The honesty posture (ADR-0002 / ADR-0009).** An epistemic-state interrogator must not
invent the numbers it reports. So **every finding carries its `rule` id + a `grounding`
string (spans + the rule-specific evidence) — that pair IS the confidence**, transparent
provenance, not a probability. There is **no score/probability field anywhere**, and the
guarantee is made **type-driven** (ADR-0000): the adjudicate contradiction schema declares
**no `FLOAT` column at all**, so a fabricated confidence is *unrepresentable* — contrast
the coref schema's `confidence: float`, which held a **real** NLP-model score we do not
have here. Rule reliability is likewise **not** encoded as a guessed ordering; any tier
would have to be a **measured** precision/recall on a labelled set (ADR-0009), recorded as
such. Until measured, the rule-id + grounding stand alone.

**Reuse, no fork (ADR-0012 P1/P2).** The only new code is `contra_detect.py`,
`contra_schema.sql`, the fixture, `test_contra_detect.py`, `contra_app.py`, one
`instances.contradiction_schema()`, one `loaders.contra_finding_tasks`, and
`contra_store.ContraStore` (the package's *designed-for second `Store` adapter* —
`SqlStore` is untouched). The detector and the adjudicator couple **only through the
`contra.finding` rows**, not a Python import.

---

## 2. How to run it (exact commands)

```sh
. ~/w/vdc/venvs/generic/bin/activate
cd /home/bork/w/vdc/1/claude_harness/experiments/fact-mining

# (1) synthetic planted fixture — proves detection FIRES on known cases, records to psql
python contra_app.py --synthetic

# (2) a real ~/distill RFC — proves the pipeline RUNS on real text (expect few/none real)
python contra_app.py --rfc /home/bork/distill/rfc/rfc2616.txt --max-paras 200

# (3) OPTIONAL stretch — the literal thesis: an AI collaborator self-contradiction.
#     EPHEMERAL: stdout-only, redacted, writes NOTHING to the DB or any file.
python contra_app.py --ephemeral-claude --max-files 40 --max-examples 3

# the checkable artifact (ADR-0013 Rule 5): the planted findings as an asserted test
python -m pytest test_contra_detect.py -q

# inspect the recorded state
psql -h 192.168.122.1 -d harness -c \
  "SELECT finding_id AS id, rule, subj_key, pred, verdict, adjudicator FROM contra.review ORDER BY finding_id;"
```

`--dsn` overrides the harness DSN (default `spans.DEFAULT_DSN`, `HARNESS_DSN`-overridable).
Running with no mode flag defaults to `--synthetic`.

---

## 3. Synthetic results — detection fires on every planted case

The committed fixture (`fixtures/contra_synthetic.txt`) plants **one contradiction per
rule**, plus **decoys** that share a subject but must stay silent, plus a **control**
paragraph. The detector finds exactly the three planted contradictions and stays silent on
the decoys and control (asserted by `test_contra_detect.py`):

```
claims extracted: 14; findings: 3
  [R-NEG]  subject='socrate'   predicate='be'
      A: Socrates [be] a philosopher
      B: Socrates [NOT be] a philosopher
      grounding: polarity clash on (subj_key='socrate', pred='be', obj_key='philosopher'):
                 claim A asserted, claim B denied (spaCy neg dependency)
  [R-FUNC] subject='capital'   predicate='be'
      A: The capital of France [be] Paris
      B: The capital of France [be] Lyon
      grounding: functional predicate 'be' (FUNCTIONAL_PREDS allowlist) with differing
                 objects 'pari' vs 'lyon'; functional-by: 'be'
  [R-NUM]  subject='committee' predicate='have'
      A: The committee [have] three members
      B: The committee [have] five members
      grounding: numeric mismatch on (subj_key='committee', pred='have'): 3.0 vs 5.0
                 (transparent parse of the object surface)
```

The decoys stay silent as designed: **"Marie visited Paris / Lyon"** does not fire
(`visit` is not on the `FUNCTIONAL_PREDS` allowlist); **"The shelf holds three books /
three novels"** does not fire (same number); the control paragraph yields no findings.

**The recorded psql rows** (`contra.review`, the canonical clean state — one rule:auto
verdict per finding):

```
 id |  rule  | subj_key  | pred |    verdict    | adjudicator
----+--------+-----------+------+---------------+-------------
  1 | R-NEG  | socrate   | be   | contradiction | rule:auto
  2 | R-FUNC | capital   | be   | contradiction | rule:auto
  3 | R-NUM  | committee | have | contradiction | rule:auto
```

Re-running inserts **0 new findings** (idempotent `UNIQUE` + `ON CONFLICT DO NOTHING`);
the loader → `HeadlessFrontend(RulePolicy)` → `ContraStore.persist` path then writes the
`contra.adjudication` verdict.

**One honest fixture adjustment, flagged.** The originally-planted "Socrates is mortal"
makes "mortal" an `acomp` the existing extractor does not capture as an object. Rather than
**fork the extractor** (ADR-0012 P1), the fixture plants a copular `attr` instead ("is a
philosopher"), which the extractor already emits. The detector was not bent to the data; the
fixture was written to the extractor's existing, unchanged capability.

---

## 4. Real-doc result — `/home/bork/distill/rfc/rfc2616.txt`, `--max-paras 200`

The pipeline **runs without error** on real edited prose:

```
paragraphs parsed: 200; claims extracted: 208; findings: 13  by-rule={R-FUNC: 11, R-NUM: 2}
```

**Honest reading (ADR-0009): these are mostly false positives**, and reporting that
truthfully is the demonstration. The over-firing has two transparent causes, both visible
in the grounding:

- **Subject canonicalization collapses distinct subjects.** Two unrelated sentences both
  reduce to `subj_key='response'` or `'port'` or `'proxy'`, so R-FUNC sees "two different
  objects for the same subject" where there is really no shared referent. Example grounding:
  `[R-FUNC] proxy/be :: functional predicate 'be' … differing objects 'proxy' vs 'agent'`.
- **`be` is over-broad.** Copular "X is Y" is on the functional allowlist for the
  clean synthetic case, but in natural prose "X is Y" rarely asserts a single-valued
  functional fact.

This is the **truthful** outcome the design predicted: an RFC is internally consistent,
so a precise detector should find few or **no** real contradictions. What this run proves
is that the pipeline runs on real text and surfaces **candidates with rule + exact source
spans for adjudication** — the reader calibrates from the grounding, not from an invented
number. A real run that finds little, reported as such, is the ADR-0013 anti-mock standard
met; the contrast is precisely §3, where planted contradictions are *known* to exist and
the detector is shown firing on exactly them.

All 13 RFC findings are recorded under `source_doc='rfc:rfc2616.txt'` and are idempotent on
re-run.

---

## 5. Optional stretch — ephemeral `~/.claude` self-contradiction (the literal thesis)

The literal target: an AI collaborator contradicting **itself** across its own turns. Run
over assistant turns from `~/.claude/projects/*/*.jsonl`. **EPHEMERAL by hard constraint:**
gated behind `--ephemeral-claude`, writes findings **only to stdout**, **never** to
`contra.finding` / the DB / any file; secrets/PII are scrubbed (DSN / IP / token / path /
email denylist) before any display; **commits nothing private**.

```
files scanned: 40; assistant turns: 2214; claims extracted: 7123;
candidate findings: 2164  by-rule={R-FUNC: 1850, R-NUM: 304, R-NEG: 10}
```

Same over-firing of `be` on natural prose → dominated by false positives, with **R-NEG the
sharper signal** (10 of 2164). The few REDACTED examples printed are clean
`be`-collapses across unrelated sentences (e.g. two different completions of "The only
thing that resolves it is …" reduced to the same `subj_key='thing'`); the secret/PII scrub
ran and surfaced nothing sensitive. **Verified zero DB writes:** `contra.finding` row count
was unchanged (16) before and after the run. This confirms the literal thesis path runs
end-to-end while honoring the ephemeral constraint — but it equally confirms (§7) that a
transparent rule pass is a *scaffold*, not the finished interrogator.

---

## 6. How it carries into the project-proper

The project target is a **claude-code hook interrogating an AI collaborator's epistemic
state**. Contradiction is a first-class epistemic signal, and this demo is the real
end-to-end that hook drives:

- **The hook is the §5 ephemeral path, made first-class.** Instead of a `--ephemeral-claude`
  batch over historical transcripts, the hook runs the same `extract → claims_from_bundle →
  find_contradictions` pass over the collaborator's **current** claims (the turn's assertions,
  optionally accumulated against the session's prior claims), and surfaces self-contradiction
  candidates for human/LLM adjudication — exactly the finding→adjudication flow §3 records,
  but live.
- **The adjudicate seam is already the human/LLM/rule switch.** The same `Task`s that
  `RulePolicy` auto-verdicts here drive `LLMPolicy` (an LLM reads the identical transcript
  and answers a verdict from the vocabulary) or `TextualFrontend` (a human presses a verdict
  key) with **zero code change** — that interchangeability is the whole point of the reused
  seam and is already covered by the package's `test_frontend_parity`.
- **The logic layer replaces the rule pass.** The three transparent rules are deliberately a
  **scaffold**. R-FUNC's hand-curated `FUNCTIONAL_PREDS` allowlist becomes a real
  functional-dependency declaration in ASP/SMT; R-NUM's value compare becomes arithmetic /
  SMT reasoning; R-NEG's polarity clash becomes proper negation-scope handling. The
  `contra.finding` rows — rule-id + grounding + spans — are exactly the shape a Prolog/ASP/SMT
  layer consumes and emits, so swapping the detector for a solver does not change the schema,
  the loader, the decision seam, or the store. The over-firing measured in §4/§5 is the
  motivating evidence for that replacement, recorded honestly rather than hidden.

---

## 7. Honest critique — what is real vs toy

- **Real:** the end-to-end wiring. Reused extractor → new pure detector → isolated psql
  schema → reused adjudicate decision seam → recorded verdicts, all running on real text,
  with a checkable test pinning the planted findings. The reuse is real (no fork: `SqlStore`
  untouched, the coupling is the `contra.finding` rows). The no-fabricated-confidence stance
  is real and **type-enforced** (no float column exists to hold an invented score).
- **Toy:** the **detector's precision**. The three rules are a transparent first pass, **not
  NLP-grade**. On real prose (§4/§5) they are dominated by false positives, driven by subject
  canonicalization collapsing distinct referents and by `be` being over-broad. This is
  surfaced, not claimed: every finding carries its rule + exact source spans so a reader
  calibrates from the evidence.
- **Precision / recall caveats (unmeasured, by design).** No precision/recall number is
  reported because none has been **measured** on a labelled set, and ADR-0002/0009 forbid
  inventing one. The synthetic fixture proves the rules *fire on known cases* and *stay silent
  on the planted decoys*; it does **not** establish a population precision. The honest read is:
  high recall on the narrow patterns it models, low precision on open prose — a candidate
  generator for adjudication, not a verdict engine.
- **The no-fabricated-confidence stance.** The "confidence" of a finding is its rule-id plus
  its grounding (spans + rule-specific evidence), nothing more. The schema has no slot for a
  probability, so the demo *cannot* emit a number it did not measure. Any future reliability
  tier must be a measured precision/recall, recorded as such.

---

## 8. Rewind — exact command

The entire demo is contained in the new `contra` schema. The complete, single-statement
rewind (also recorded in the header of `contra_schema.sql`):

```sql
DROP SCHEMA contra CASCADE;
```

`mining` / `nla` / `trace` / `public` are never referenced and are not affected. The
schema and rows are left in place so the demo is inspectable.

---

## 9. Gates (verified)

- **adjudicate `mypy --strict`:** Success, 20 source files. `contra_detect.py`: no errors
  attributable to it (the only `mypy --strict` errors under `--follow-imports` are
  pre-existing in the reused `extract.py` dependency, not in the new code).
- **pytest:** 43 adjudicate tests green (unchanged) + 8 new `test_contra_detect.py` green
  (the planted finding set + decoy silence + the parser).
- **jax / jaxlib:** both 0.10.1 (the detector reuses the import-light `extract.py`; no
  torch/HF on the demo path).
- **schemas after run:** `contra, mining, nla, public, trace` — `contra` is new (`finding`,
  `adjudication` tables + `review` view); the others untouched.

---

## Terms

This doc reuses the adjudicate coined terms — **domain-schema**, **classification**,
**adjudication-mode**, **verdict-vocabulary**, **render-model** — defined in
[`../../adjudicate/GLOSSARY.md`](../../adjudicate/GLOSSARY.md) (their SSOT). New here, as in
the design doc: **finding** (a candidate contradictory claim-pair a rule produced),
**rule-id** (`R-NEG`/`R-FUNC`/`R-NUM` — the transparent confidence), **functional-predicate
allowlist** (the curated single-valued-predicate set R-FUNC gates on).
