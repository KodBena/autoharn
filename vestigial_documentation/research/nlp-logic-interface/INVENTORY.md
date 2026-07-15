# INVENTORY — the NLP↔logic interface surfaces (2026-07-02)

**Purpose.** A factual catalog of the existing surfaces where NLP-extracted facts meet
the logic layer, produced as the evidence base for a separate commissioning that owns
design. This document inventories and renders verdicts; it proposes nothing. All code
was read read-only.

**Method.** Every source file listed was read in full (not the docstring alone). The
four **LAW ADRs** named in `CLAUDE.md` — ADR-0000 (type-driven design), ADR-0012
(compositional/structural hygiene), ADR-0013 (execution integrity), ADR-0014
(second-opinion) — were read in full first, and the verdicts below are rendered against
them with `file:line` citations. The live database was enumerated read-only over
`psql -h 192.168.122.1 -d harness`.

**What a "verdict" is here.** A short judgement of the surface against the LAW, both
ways: where it conforms (typed boundaries, one-home/SSOT, honest tests, honest
deferrals) and where a **hazard** sits (a defect in reach of this work — the
mother's-life bar of `CLAUDE.md`). A hazard is flagged, never designed around.

**Coined terms, legible on first use.**
- **interchange / substrate** — the logic-agnostic data every backend consumes: the
  `FactBundle` (JSON fact records) and its normalized form the `Claim` list. No backend
  re-parses text; the `Claim` list is the carrier.
- **EDB** (extensional database) — in ASP/Datalog, the ground facts fed to a program
  (here, `assertion/5`, `functional/1`, `number/2` clauses generated from `Claim`s).
- **differential gate** — a mechanical set-equality between two independent producers'
  findings on the *same* substrate; empty-empty = pass. An encoding-trust check, not a
  model's judgement.
- **glut** — in Belnap-Dunn FDE / Priest's LP paraconsistent logic, a proposition that
  is *both* told-true and told-false; a contained truth value (`both`) rather than an
  explosion (`ex falso quodlibet`).
- **defeasible** — a rule whose conclusion can be retracted by an exception without
  editing the rule (here R-FUNC's `not exception(S,P)` default).
- **oracle** — the reference Python implementation (`contra_detect.find_contradictions`)
  the ASP and z3 engines are differentialed against.

---

## 0. The interchange spine (read this first — everything joins on it)

Two type homes define the whole NLP↔logic contract. Every logic surface consumes them
and no other NLP internals.

### `extract.py` — the `FactBundle` wire shape (the NLP→everything boundary)
- **What it is.** `doc_to_facts(doc) -> FactBundle` (`extract.py:316`) is the SSOT
  per-document fact extractor: one home, two callers (the GPU daemon host-side; and
  `load_facts.py` locally). It consumes a neutral `parse_seam.ParsedDoc` (a spaCy `Doc`
  is decoded at the boundary via `SpacyParser.adapt`, `extract.py:352`) and emits a
  `FactBundle` `TypedDict` (`extract.py:297`).
- **The contract (typed).** `FactBundle` = `{sents, entities, temporal, triples}` with
  `TripleRecord` = `{sent, subj, pred, obj, subj_key, obj_key, negated}`
  (`extract.py:269–301`). All fields are `str`/`int`/`bool`, so JSON is bit-exact
  (no float coercion) — the discrete-invariant bar named at `extract.py:329`. Two
  `NotRequired` degradation markers (`coref_refused`, `parse_refused`,
  `extract.py:307/313`) are typed first-class, not out-of-band keys.
- **Verdict (LAW).** Strong ADR-0012 P1/P7/P8 conformance: the wire shape has one typed
  home; the spaCy-Doc→ParsedDoc decode is a single Port/ACL; the functional-core split
  (extractor owns *what a fact is*, caller owns *which survive the budget*) is stated
  and enforced (`extract.py:341–343`, ADR-0012 P9). No hazard observed in this boundary.

### `contra_detect.py` — the `Claim`/`Finding` types and the reference oracle
- **What it does.** Pure function of the `FactBundle` (no second parse, no fact the
  extractor did not emit). `claims_from_bundle` (`contra_detect.py:93`) zips triples
  with sentence text, parses the object number, and **drops** claims with empty
  `subj_key`/`obj_key` (`contra_detect.py:102`) exactly as `mining.fact_classical`
  excludes them. `find_contradictions` (`contra_detect.py:171`) runs three rules over
  claim pairs and dedups on `(rule, subj_key, pred, claim_a, claim_b)` with reverse-pair
  collapse (`contra_detect.py:187–193`).
- **The three rules.** R-NEG = polarity clash on `(subj_key, pred, obj_key)`
  (`:196–207`); R-FUNC = differing `obj_key` on a functional predicate, both asserted
  (`:218`); R-NUM = differing parsed numbers on `(subj_key, pred)` (`:224`).
- **Engine touched.** Plain Python. This is the **oracle**.
- **Interface contract.** Input `list[Claim]`; output `list[Finding]`. Every `Finding`
  carries `rule` + `grounding` (the transparent provenance that *is* the confidence);
  **there is no score/probability field anywhere** (`contra_detect.py:16–21`). The
  numeric parser returns `None`, never a guess (`parse_number`, `:58–71`). `Finding.as_row`
  (`:142`) is the wire to `contra.finding` — the cross-package coupling is these rows,
  not a Python import.
- **Depended on by.** `logic_backend.py` (types + oracle), `contra_asp.py`, `fde_z3.py`,
  `contra_app.py`. It is the hub.
- **Verdict (LAW).** Conforms to ADR-0000/ADR-0002 with unusual discipline: frozen typed
  dataclasses (`Claim` `:75`, `Finding` `:125`); no-sentinel-as-value (`:49–50`,
  `:17–18`); the precision control is *named data in the grounding*, never hidden. Two
  factual notes, neither a hazard at current scale: (1) `FUNCTIONAL_PREDS` is a
  hand-curated 6-lemma frozenset (`:42–44`) — honestly labelled a "stand-in for a real
  functional-dependency declaration", and moved to auditable EDB data on the ASP side;
  (2) `find_contradictions` is O(n²) within each `(subj_key,pred)` group via
  `combinations` (`:216`) — fine on the current corpus, a scaling axis a designer should
  know.

---

## 1. The logic-layer code surfaces

### `logic_backend.py` — the standardized pluggable backend seam
- **What it does.** Defines the `LogicBackend` Protocol (`:107`, `runtime_checkable`)
  every logic plugs into: three members — `name`, `rules: frozenset[str]`,
  `analyze(claims) -> list[LogicFinding]`. `LogicFinding` (`:58`) is the engine-neutral
  finding, frozen, carrying the shared `signature` (`:79`) plus a paraconsistent `value`
  (e.g. `"both"`). The mechanical gate `cross_engine_differential` (`:163`) returns
  `(only_in_a, only_in_b)` over the **shared** rule set (`shared_rules`, `:157`).
- **Engine touched.** None directly (imports only `contra_detect` + stdlib). It is the
  seam; the two engines are adapters.
- **Contract.** A backend need not cover every rule — `rules` makes a differential
  honest by running only on the intersection (`:118`, `fde_z3` covers only `{"R-NEG"}`).
- **Depended on by.** `contra_asp.AspBackend`, `fde_z3.FdeZ3Backend`, `test_logic_backend.py`.
- **Verdict (LAW).** The Protocol seam is a clean ADR-0012 P2/P8 instance, and
  `cross_engine_differential` is a genuine ADR-0000/INDEP independent-channel gate.
  **HAZARD (flagged, in reach): stale, self-contradicting docstring advertising a now-
  banned pattern.** `logic_backend.py:40` states *"No clingo, no z3 -- those are each
  adapter's own lazy import"* and `:120` repeats the framing. This is (a) **factually
  wrong** — `fde_z3.py:40` imports `z3` at module top level, and `contra_asp.py` shells
  out to the clingo *CLI* (`:106`), importing no `clingo` at all — and (b) it **advertises
  the lazy-import architecture the maintainer edict of 2026-07-02 (`CLAUDE.md`) bans
  outright.** It is a load-bearing comment that lies about the module's dependency posture
  (ADR-0012 cancer G; the doc-register form of ADR-0002's lying signature). The code is
  correct; the docstring must be corrected or it will mislead the next contributor into a
  banned pattern.

### `logic_layer.lp` — the ASP re-expression of the three rules (clingo)
- **What it does.** Re-expresses R-NEG/R-FUNC/R-NUM as declarative clauses over an EDB
  exported from the same `Claim`s (`:1–25` header). R-NEG derives a first-class `both`
  truth value (`truth(S,P,O,both)`, `:40`) rather than a detonating integrity constraint
  — the FDE/Belnap move. R-FUNC is defeasible: `exception(S,P) :- multi_valued(S,P)`
  (`:52`) and the finding carries `not exception(S,P)` (`:59`), so adding one EDB fact
  retracts the finding non-monotonically. R-NUM is disequality on canonical parsed values
  (`:69–70`).
- **Engine touched.** clingo 5.8 / stable-model semantics.
- **Verdict (LAW).** Honest and closure-conscious. `#defined` guards (`:31–33`) make an
  empty EDB extension *silence, not error* (ADR-0002: absence is data). The module
  **names what it does not do**: R-NUM is "FAITHFUL to the Python rule, which is itself
  disequality -- NOT magnitude arithmetic. True magnitude/tolerance … is HONESTLY future
  work, not claimed here" (`:65–68`). That is a textbook ADR-0013 Rule 4 filed deferral
  and an ADR-0000 closure statement (the quantification universe named, the uncovered
  axis named as uncovered). No hazard.

### `logic_repair.lp` — minimal-repair / blame over functional conflicts (clingo)
- **What it does.** Loaded together with `logic_layer.lp`. Guesses a `retract/1` set over
  positive functional assertions (`:15`), constrains that no functional conflict survives
  (`:19–22`), and `#minimize`s the retraction count (`:25`) — subset-optimization under a
  constraint, the one demonstration of "ASP does what a SQL view provably cannot rank".
- **Engine touched.** clingo (optimization mode).
- **Verdict (LAW).** Small, honest, scope-disciplined: R-NEG/R-NUM are explicitly *not*
  repaired here with the reason given (`:10–11`). No hazard.

### `contra_asp.py` — the ASP driver + `AspBackend` adapter
- **What it does.** Renders the EDB from `Claim`s (`edb_from_claims`, `:65`; the
  `FUNCTIONAL_PREDS` frozenset becomes `functional/1` DATA, `:76`), runs clingo as a
  **subprocess** over the `.lp` files with JSON output (`run_clingo`, `:100`, `--outf=2`
  parsed — no text scraping), maps `finding(tag,A,B)` atoms back to `Claim`s by id
  (`:158`), and exposes `differential` (`:198`), `minimal_repair` (`:206`), and the
  `AspBackend` seam adapter (`:224`).
- **Engine touched.** clingo CLI (the Python `clingo` binding is not in the venv — stated
  `:4–5`). Shared identity between sides = a `Claim`'s index in `claims_from_bundle`
  (`:14`); only integer id-pairs cross the clingo wire, text never does.
- **Contract.** `analyze` re-shapes `asp_findings` into `LogicFinding`s, tagging R-NEG
  with `value="both"` (`:254`). Engine-specific config (`functional_preds`,
  `extra_facts` defeaters) is constructor state, off the Protocol (`:240–246`).
- **Depended on by.** `test_contra_asp.py`, `test_logic_backend.py`, and
  `claims_from_text/_paragraphs` helpers reused by tests.
- **Verdict (LAW).** Solid ADR-0002/ADR-0012 conformance: `_clingo_bin` fails loud when
  the binary is absent (`:95–96`); the EDB `_quote` escapes both metacharacters so any
  key is a legal term (`:51–54`); clingo's bitmask exit codes are handled and a
  parse/grounding failure is surfaced with the real stderr (`:117–120`). One factual
  note (minor, not a hazard): the subprocess `timeout=120` is a bare literal
  (`:111`) — a magic constant in the ADR-0012 cancer-F register, unshared so low-risk,
  but a designer wiring this into a time-budgeted hook (per HOOK-DESIGN §3) will want it
  denominated, not guessed.

### `fde_z3.py` — the second adapter, on a different engine (z3)
- **What it does.** Encodes R-NEG's polarity contradiction in Belnap-Dunn FDE / Priest's
  LP via the two-bit trick: each atom carries `_t`/`_f` bits, a pos+neg atom yields
  `Both` and stays SAT while the classical single-Bool encoding is UNSAT
  (`classical_explodes`, `:117`; `atom_is_glut`, `:80`; `fde_contains`, `:129`). The four
  load-bearing semantic knobs are named auditable fields on `FdeSemantics` (`:47–64`) and
  mutation-tested. `FdeZ3Backend` (`:137`) covers **only** `{"R-NEG"}`.
- **Engine touched.** z3-solver 4.16 (`import z3` at module top, `:40` — **correct** per
  the lazy-import ban; a real solve per atom-pair, `:92`).
- **Verdict (LAW).** Honest earns-its-keep framing (`:18–29`: FDE's win is non-explosion
  + a queryable `both`, *not* a precision win; it finds the same R-NEG set as ASP through
  a different paradigm — that agreement is the pluggability proof). Two factual notes:
  (1) **minor hazard** — the non-explosion invariant is asserted with a bare Python
  `assert s.check() == z3.sat` (`:111`); `assert` is elided under `python -O`, so a
  load-bearing invariant would vanish in an optimized run. ADR-0002's hierarchy prefers a
  `raise` for an invariant that must always hold. Worth a designer's note. (2) `analyze`
  constructs a fresh `z3.Solver()` per atom-pair (`:92`, called inside the double loop
  `:165–166`) — an O(pairs) solve count; fine at fixture scale, a cost axis to know.

### `contra_app.py` — the end-to-end runner (detector → store → adjudicate)
- **What it does.** The real pipeline: `extract` → `claims_from_bundle` →
  `find_contradictions` → `ContraStore.insert_findings` (`contra.finding`, ON CONFLICT DO
  NOTHING) → `contra_finding_tasks` → `HeadlessFrontend(RulePolicy).adjudicate` →
  `ContraStore.persist` (`contra.adjudication`) → read back `contra.review`
  (`:1–13`, `:73–93`). Modes: `--synthetic`, `--rfc`, `--ephemeral-claude` (stdout-only,
  scrubbed, writes nothing, `:172–213`).
- **Engine touched.** Python oracle only (does not invoke ASP/z3).
- **Depended on by.** It is a leaf CLI; nothing imports it.
- **Verdict (LAW).** **HAZARD (flagged, in reach): `sys.path.insert` to reach a sibling
  package.** `contra_app.py:41–43` does `sys.path.insert(0, _ADJ)` and then imports
  `instances`, `contra_store`, `frontend_headless`, `loaders` behind `# noqa: E402`
  (`:45–48`). This is precisely the `sys.path.insert` preamble ADR-0013 Specimen 1
  identified as the structural centerpiece that "≈half the plan" failed to remove
  (48 files carrying it). The architectural coupling *claim* is clean — "the cross-package
  coupling … is the contra.finding ROWS, not a Python import" (`:24–25`) — but the runner
  itself still couples by `sys.path` + import, contradicting that claim at the import line.
  A designer joining these packages should know the row-coupling is real for data but the
  *runner* reaches across by path injection. Secondary factual note: the `_SCRUB` regex
  list (`:127–133`) is the PII boundary the HOOK-DESIGN privacy ruling (§4) leans on;
  it is a hand-authored allowlist, not a shared one.

### `load_facts.py` — the mining-schema loader
- **What it does.** Mines a text and writes the logic-agnostic `mining` base tables.
  Reuses `extract.doc_to_facts` (SSOT, one extractor two callers, `:170–171`); supports a
  lean `--remote` wire path and a local spaCy path; processes the corpus in
  `--batch-size` batches each written-and-freed before the next (the KNOWABLE
  host-memory cap, `:172–289`); optional distributed-span tracing into the `trace` schema.
- **Engine touched.** None (it is the *producer* of the substrate, not a logic).
- **Depended on by.** CLI entry; `test_load_facts_batching.py`.
- **Verdict (LAW).** The leanness posture is honestly documented post-ban (`:29–36`: the
  remote wire client's leanness is tested directly on `nlp_client`/`nlp_cache`, not via
  `import load_facts` which now legitimately carries the local spaCy footprint). Degraded
  (coref-refused) paragraphs are counted and logged loudly, load proceeds (`:232–240`,
  ADR-0002 degrade-not-disappear). Factual note (density, not a hazard): `main()` is a
  single ~265-line function (`:50–314`) that owns arg parsing, coref-mode selection,
  batching, the DB write loop, and trace-span lifecycle — a large imperative shell that
  brushes ADR-0007/ADR-0012 P3; it is imperative-shell code (no pure logic buried in it),
  so the pressure is on readability, not correctness.

### `resolve.py` / `resolve_coref.py` — canonical-constant resolution (the coref/entity seam)
- **`resolve.py`** — pure canonicalization: `canonical_key` (strip determiners,
  singularize head, `:44`), `resolver_for(doc) -> key(token)` (`:122`) using coref
  clusters if present then entity normalization then morphological fallback, with an
  **unresolved pronoun returning `""`** (not a constant, `:132–133`). Imports nothing from
  spaCy — reads `Doc` attributes duck-typed (`:56–60`), so `import resolve` stays free of
  the spaCy/torch drag.
- **`resolve_coref.py`** — the spaCy/fastcoref-bearing half, **split out to honor the
  lazy-import ban** (spaCy + fastcoref imported at module top, `:24–26`).
  `attach_coref_clusters` (`:38`) is **THE ONE decoder** of the wire coref payload into
  the `Doc` extension — both wire consumers call it, closing a prior two-decoder
  split-brain (`:44–49`, ADR-0012 P1/P7).
- **Engine touched.** spaCy pipeline + fastcoref (local path); the remote path decodes
  daemon-supplied clusters.
- **Verdict (LAW).** The `resolve`/`resolve_coref` split is a clean, *documented* response
  to the lazy-import ban (a module mis-factored to defer a dep is split, not deferred) —
  the edict's prescribed remedy applied. `_singular` (`resolve.py:34–41`) is a naive
  pluralization heuristic and the README's "Honest limits" flags entity/coref quality as
  the cap on every downstream logic; that is a named limitation, not a hidden one. No
  hazard.

### `schema.sql` / `contra_schema.sql` — the DB DDL
- **`schema.sql`** — the `mining` schema: a provenance spine (`document`→`sentence`) and a
  **logic-agnostic** SVO base (`assertion`) with `subj_key`/`obj_key` canonical constants
  and a `negated` seam, plus `entity`/`temporal` raw material. Each per-logic view is a
  *projection* over the one base: `fact_classical` (`:78`), `contradiction` (`:86` — the
  SQL R-NEG floor), `fact_temporal` (`:96`). Every table has a jsonb `extra` escape hatch.
- **`contra_schema.sql`** — the `contra` schema: `finding` (with a UNIQUE idempotency key,
  `:22`), `adjudication` (FK CASCADE), and a derived `review` view (`:36`).
- **Verdict (LAW).** Model ADR-0012 P1: the logic is a *view*, the base commits to no
  logic; the DDL is derived/idempotent and reversible (`DROP SCHEMA … CASCADE`). No
  hazard. The `mining.contradiction` view is exactly the SQL floor the ASP layer
  re-expresses and is differentialed against — a genuine independent baseline.

### The tests — `test_logic_backend.py`, `test_contra_asp.py`, `test_contra_detect.py`, `test_doc_to_facts_equivalence.py` (+ siblings)
- **`test_contra_detect.py`** — the oracle's golden gate: the fixture must produce
  *exactly* the three planted findings and the named decoys stay silent
  (`:37–59`); grounding-content assertions (`:62–74`); the parser tested in isolation
  including "returns None, never guesses" (`:78–89`).
- **`test_contra_asp.py`** — encoding-trust for the ASP layer, three independent checks
  that never trust the `.lp` on its face: GOLDEN (`:50`), MUTATION (flip each load-bearing
  `.lp` token, every mutant must change the verdict; the mutation target's uniqueness is
  itself asserted, `:123`), DIFFERENTIAL vs the oracle on the fixture **and** real RFCs
  (`:67–83`). Plus the two ASP-over-SQL wins: defeasible retraction via one EDB fact
  (`:131`) and minimal-repair cardinality (`:146`).
- **`test_logic_backend.py`** — the pluggability + cross-engine gate: both adapters
  satisfy the Protocol (`:51`); z3/FDE, clingo/ASP, and the oracle agree *exactly* on the
  shared rule set on fixture and rfc2616 (`:75–108`); FDE golden + mutation + the honest
  non-explosion contrast (`:112–176`).
- **`test_doc_to_facts_equivalence.py`** — pins the SSOT cut: OLD inline extraction ==
  NEW `doc_to_facts` + JSON round-trip, bit-for-bit, including under the `--max-sents`
  budget and with coref (`:133–188`).
- **Verdict (LAW).** These are genuinely strong ADR-0013 Rule 5 artifact tests: mutation
  testing (a surviving mutant = a dead clause), and — notably honest — **both** the ASP
  `A<B` dedup-equivalence and the FDE full-symmetry relabeling are *named as honestly
  excluded non-mutants*, not dressed up as caught (`test_logic_backend.py:152`,
  `test_contra_asp.py:90`). That is exactly the closure-statement candor ADR-0000's
  2026-07-02 amendment demands. **One factual coverage note a designer must know (not a
  hazard):** the differential gate's *real-document* arm is gated on host files —
  `~/distill/rfc/rfc791.txt|rfc2616.txt|rfc793.txt` — that are **not in the repo** and are
  `pytest.skip`ped when absent (`test_contra_asp.py:73–76`, `test_logic_backend.py:94–97`).
  So in a clean checkout the differential runs only on the single committed synthetic
  fixture; the real-prose agreement claim is contingent on the host corpus being present.
  Siblings that touch the substrate but not the logic rules: `test_load_facts_batching.py`
  (DB write sequence == one-shot), `test_parse_seam.py` (parse-backend adapter),
  `test_transcript_prose.py` (the prose admit-set feeding the future hook).

---

## 2. The data substrate (live + DDL)

Enumerated read-only on `192.168.122.1/harness`. Application schemas: `mining`, `contra`,
`trace`, `nla`. `public` is empty.

### `mining` (the fact substrate) — DDL `schema.sql`, matches live exactly
| table/view | rows | shape |
| --- | --- | --- |
| `document` | 12 | provenance; UNIQUE(sha256, model) |
| `sentence` | 3 449 | FK→document CASCADE; UNIQUE(doc_id, sent_index) |
| `assertion` | 4 703 | the SVO atom; `subj_key`/`obj_key`/`negated`; index on (pred,subj_key,obj_key) |
| `entity` | 3 702 | canonical constants (NER) |
| `temporal` | 524 | DATE/TIME raw material |
| `fact_classical` / `contradiction` / `fact_temporal` | views | per-logic projections, no independent storage |

### `contra` (the findings/adjudication store) — DDL `contra_schema.sql`, matches live
| table/view | rows | shape |
| --- | --- | --- |
| `finding` | 16 | candidate contradictions; UNIQUE(source_doc,rule,subj_key,pred,claim_a,claim_b) idempotency |
| `adjudication` | 55 | verdicts (rule/human/llm); FK→finding CASCADE |
| `review` | view | finding LEFT JOIN adjudication |

Live sample: findings are the synthetic R-NEG/R-FUNC/R-NUM fixtures on
`synthetic:contra_synthetic.txt`, each auto-adjudicated `contradiction` by `rule:auto`.

### `trace` (the distributed-span store) — DDL `trace_schema.sql`, matches live
`run` (158) ← `span` (**119 484**) ← both CASCADE; `finding` (**0 rows**); views
`span_stats`, `blocking`. **`trace.finding` is defined but empty** — the
measurement/interpretation split is half-populated: 119k measurements, zero authored
interpretations. `span.parent_span_id` is deliberately *not* an FK (cross-process soft
link, documented).

### `nla` (a benchmark ledger) — **no DDL in this repo path**
`nla.bench_result` (355 rows): a latency/fidelity ledger for a `deberta_maverick.npz`
variant, backed by a live sequence. **This schema exists live but its DDL is not among
`schema.sql`/`contra_schema.sql`/`trace_schema.sql`** — an unversioned store sitting in
the same DB. Flagged factually per the auditability posture (`CLAUDE.md`).

**Other claim-ledger-shaped stores referenced in the repo.** The maintainer's MEMORY
notes an operational harness DB ("perf/research ledger, toolset registry, work log" as
"one claim-ledger shape"); those live under `db/harness/` migrations, distinct from these
throwaway experiment schemas. The three experiment schemas above plus `trace.finding`
(supersession chain via `supersedes` self-FK) are the claim-ledger-shaped stores in the
fact-mining tree.

---

## 3. The consumers-to-be (declared contracts, as facts)

### `experiments/fact-mining/docs/HOOK-DESIGN.md` — the L1–L3 interrogation ladder
The guardrails hook (design only, no code yet) will demand of the logic layer a
**time-budgeted, shallow-first ladder** (HOOK-DESIGN §5):
- **L0 — ingest.** Prose units → `Claim`s stored. Always completes; the spine.
- **L1 — self-consistency candidates.** The contra rules (R-FUNC/R-NUM as they stand)
  over the session's own claim set; findings carry rule + grounding + both provenances.
- **L2 — KB cross-check.** The same rules run session-claims × durable-KB (the `mining`
  schema + harness ledgers), gated on the §4 privacy ruling (durable storage approved,
  option (a), scrub-at-ingress).
- **L3 — engine interrogation.** The defeasible machinery (ASP defaults/exceptions, the
  FDE z3 lane) over the claim graph. **Explicitly DEFERRED to this NLP↔logic interface
  commissioning** (HOOK-DESIGN §5, L3). The hook's stated contract to the logic layer is
  exactly *"a claim set with provenance in, findings with grounding out"* — i.e. the
  `LogicBackend` seam (`analyze(claims) -> list[LogicFinding]`) is the polymorphic seam
  the interface work is expected to formalize.
- **Demanded envelope (§3).** The logic layer, called from the hook, must degrade to a
  typed no-op within a hard wall-clock budget (daemons down ⇒ exit 0, inject nothing, log
  loudly). This is the direct downstream reason the `contra_asp` subprocess `timeout=120`
  literal (`:111`) and the per-pair z3 solves (`fde_z3.py:165`) are load-bearing facts:
  the interface must be time-budgetable.
- **Storage seam.** Findings are to land in `contra.finding` from day one (the
  adjudication widget is "the consumer of record").

### `experiments/adjudicate` — the schema-first shape it expects
- **Contract.** `adjudicate` is a standalone, `mypy --strict`-clean package (DESIGN.md
  §0) whose **domain-schema** (`schema.py`, a Python type artifact, not SQL) is the SSOT
  that determines the whole interaction. Illegal states are unrepresentable: closed axes
  (`FieldKind`, `AdjudicationMode`, verdict membership) are sealed unions matched with
  `assert_never`; cross-references (prompt→fields, preview→field, classification→columns,
  verdict→vocabulary) are **construction-time refusals** (`schema.py:336–387`,
  `Record.of` `:134`, `Adjudication.make` `:482`). It is a worked ADR-0000 instance.
- **The binding to the logic layer (concrete).** `contra_app.py` drives `adjudicate`'s
  `HeadlessFrontend(RulePolicy)` over `instances.contradiction_schema()`
  (`instances.py:116`). That schema is **BATCH** mode
  (`instances.py:127`), payload `{source_doc, subject, predicate, explanation}`, columns
  `{claim_a, claim_b, rule, grounding, suggested}` — and it declares **no `Field.number`
  anywhere**, so a fabricated confidence is *unrepresentable by type* (`instances.py:93–97`).
  This is the exact honest-confidence posture the detector holds (rule-id + grounding =
  confidence), enforced at the adjudication boundary. `SUGGESTED_VERDICT = "contradiction"`
  (`contra_store.py:33`) is the always-honest candidate label.
- **Status.** Doc-selection is LIVE end-to-end; the contradiction schema is wired via
  `contra_app.py`; the coref-adjudication BATCH schema is **DEFINED, not wired** to the
  unbuilt hook (DESIGN.md §4). The `Bus` seam's `ZmqBus` is a designed-for second adapter
  "kept an adapter because whether it ends up ZMQ depends on what claude-code hooks allow"
  (DESIGN.md §2).

---

## 4. What exists vs what is missing (strictly factual gap list)

**Exists (built + tested):**
- The interchange spine: `FactBundle`/`Claim`/`Finding` typed homes, one SSOT extractor.
- The Python oracle detector (R-NEG/R-FUNC/R-NUM), differential-gated.
- A standardized `LogicBackend` Protocol seam with **two** adapters on **two** engines:
  `AspBackend` (clingo CLI, all three rules + defeasible R-FUNC + minimal-repair) and
  `FdeZ3Backend` (z3, R-NEG glut only).
- The mechanical cross-engine + oracle differential gate, with mutation-tested encodings.
- The `mining`/`contra`/`trace` DB substrate (logic-agnostic base + per-logic views),
  live and populated (12 docs, 4 703 assertions, 16 findings, 55 adjudications).
- The `adjudicate` schema-first consumer, live for doc-selection, wired for contradiction.

**Missing / not-yet-built (named, not designed):**
1. **L3 engine interrogation from the hook** — the hook shell (`hook_guard.py`), the
   `mining.hook_cursor` table, and L2/L3 rungs are unbuilt (HOOK-DESIGN §5/§7).
2. **Deontic / obligation-execution logic** — explicitly off this seam's menu
   (`logic_backend.py:24–30`); it lives in the obligations pillar and is not implemented
   here.
3. **Magnitude/tolerance/unit numeric reasoning** — R-NUM is disequality only; `>`,
   approx-equal, and unit coercion are named future work needing clingcon or a Z3 encoding
   (`logic_layer.lp:65–68`).
4. **Temporal reasoning** — `mining.temporal` + `fact_temporal` exist as *raw material
   only*; no valid-time/temporal logic consumes them.
5. **The other surveyed logic families** — of the 14 in the fair-trials survey, only ASP
   and SMT/FDE have adapters. Modal/epistemic, defeasible-argumentation, Datalog,
   description logic, linear/substructural, relevance, abductive/ILP, probabilistic-SRL,
   and probabilistic-programming have **no** adapter.
6. **FDE coverage** — `FdeZ3Backend` covers only R-NEG; R-FUNC/R-NUM stay ASP's.
7. **`trace.finding` is empty** — zero authored interpretations against 119 484 spans.
8. **`nla` schema has no DDL in the repo** — an unversioned live store (355 rows).
9. **Session/message provenance on findings** — `contra.finding.source_doc` is a single
   string; the per-turn (session_id, line, byte-span) provenance the hook needs
   (HOOK-DESIGN §4) is not yet in the schema.
10. **The Python `clingo` binding** — not in the venv; ASP is subprocess-only, so the
    per-call cost is a process spawn (relevant to the hook's time budget).
11. **The real-document differential arm is host-contingent** — the RFC corpus it runs
    against is not in the repo; a clean checkout exercises the differential on the
    synthetic fixture only.
12. **The coref-adjudication BATCH schema is defined but unwired** — no hook feeds it.

---

## 5. ADR-0014 out-of-frame audit of this inventory

Rendered on my own deliverable, as commissioned.

- **Are the verdicts evidence or vibes?** Each verdict cites `file:line` and quotes the
  load-bearing text where the claim turns on exact wording (the two flagged hazards — the
  `logic_backend.py:40` lazy-import docstring and the `contra_app.py:41` `sys.path.insert`
  — are quoted, and each is cross-checked against a second file: `fde_z3.py:40` /
  `contra_asp.py:106` disprove the docstring; ADR-0013 Specimen 1 names the `sys.path`
  pattern). The conformance verdicts likewise point at the specific mechanism (the
  `#defined` guards, the named-exclusion tests, the no-`Field.number` type). I judge the
  verdicts **evidence-backed**, not impressionistic. The one place I was careful to label
  *contingency, not defect* is the host-file test coverage note — stated as a fact about
  where the gate runs, not a claim that the code is wrong.
- **Is any summary editorializing?** The consumers-to-be section (§3) reports declared
  contracts with citations and repeatedly marks status (LIVE / DEFINED-not-wired /
  DEFERRED) rather than endorsing the design. The gap list (§4) is enumerated from what is
  absent in code/DB, with no proposal attached. I found and removed no design suggestions;
  the deferrals I cite are the *code's own* filed deferrals, quoted, not mine.
- **The trap ADR-0014 guards (anchoring).** My prior was "Opus-built, trust it less". The
  evidence cut both ways and I recorded both: the encoding-trust machinery and honest
  test exclusions are genuinely strong (I did not manufacture hazards to fit the prior),
  and the two real hazards I did find are documentation/coupling defects, not soundness
  defects in the deduction. That asymmetry is reported as found.
- **Verdict:** the inventory meets the ADR-0014 bar — the load-bearing claims are
  artifact-anchored and the summaries report rather than litigate. Residual honest
  limitation: I did not *execute* the test suites (read-only inventory), so the "tests
  pass" property is asserted from the code + the adjudicate DESIGN's stated green state,
  not re-observed; a designer wanting the effect-level guarantee (ADR-0013 2026-07-02
  amendment) should run them.
