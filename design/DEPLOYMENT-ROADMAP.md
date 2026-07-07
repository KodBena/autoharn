# DEPLOYMENT ROADMAP — claude_harness fact-mining

The deployable thesis: **a claude-code hook interrogates an AI collaborator's
epistemic state.** When a collaborator (Claude, or a human) makes a claim, the hook
routes that claim's text through the NLP extraction service, turns the resulting
groundings into an adjudication task, presents it to a human-OR-LLM adjudicator, and
records the verdict in the harness DB. The NLP pipeline (`fact-mining/`: spaCy parse →
coref → SVO/entity/temporal facts) is the **PoC engine**; Project Gutenberg / RFC /
UN-TEI text is just **PoC fodder**. The `adjudicate/` package is the **human-OR-LLM
HITL interface**, and its `coref-adjudication` schema instance is the **hook-facing
surface**.

This is an analysis + plan, not code. Every readiness claim below is grounded in a
named file. Posture is the in-repo `docs/adr/` corpus read in full — ADR-0000 (type-driven /
illegal-states-unrepresentable), ADR-0012 (compositional/structural hygiene: P1 SSOT,
P2 seams, P7 serialization-XOR-transport, P9 host-XOR-device), ADR-0013 (execution
integrity: the mandate defines done; disclosure is not authorization; verify the
artifact). The deliberate consequence of that posture for *this* doc: the milestones
below are written so a de-scope is a **ratifier decision**, never something the
sequencing quietly assumes.

> **PERF IS SETTLED — not a deployment blocker.** The dense encode runs on the GPU via
> XLA. The Pallas flash kernel is *foreclosed* on the 2080Ti (Turing `sm_75` is below
> the `sm_80+` jax's Pallas-Triton backend needs; Mosaic is `sm_90` — both exclude
> Turing) and is shelved with its lowering interpret-proven correct
> (`nla_lab/PALLAS_FLASH_DESIGN.md`, `nla_lab/lower/`, `test_pallas_*`). Quantization +
> data-selection are de-prioritized. **Nothing in this roadmap waits on any of it.** The
> remaining work is *integration and operations*, not numerics.

---

## 1. CURRENT readiness — what works end-to-end TODAY

### 1.1 The NLP daemon + supervisor — WORKS

Two host services, split by ADR-0012 P9 host-XOR-device so no single process holds both
torch and jax:

- **`nlp_server.py`** (`:5599`) — client-facing spaCy parse + the maverick *serial
  reference* coref (torch-bearing). Ops are pure-data JSON in/out: `ping`, `info`,
  `parse` (`nlp_server.py:564` `handle`). `info` reports `gpu`, loaded models,
  `coref_backend`, `decode_addr` (`nlp_server.py:576`). `warmup()` pre-pays the ~12s
  cold init (CUDA ctx + cuDNN autotune + first deberta forward) on a 2-sentence
  coref-bearing paragraph so the first real request is warm (`nlp_server.py:662`), and a
  warmup failure is logged loudly but does **not** stop serving (ADR-0002
  genuinely-right fallback).
- **`coref_decode_server.py`** (`:5600`) — the unified **jax-only** coref daemon: text →
  tokenize (vendored sentencepiece `.spm`, raw, no transformers) → encode (jax deberta)
  → decode → clusters, in one process that imports jax and **never** torch/transformers/
  hf at runtime (`jax_only_guard` + `assert_torch_free`; the `--coref-backend
  jax-unified` path).
- **`run_coref_stack.py`** — the supervisor. Starts the decode daemon first, polls it
  with a ZMQ ping until it answers (so nlp_server's warmup never relays into a
  dead socket — `_wait_ready`, `run_coref_stack.py:50`), then starts nlp_server pointed
  at it (`--coref-backend jax-unified --decode-addr …`); prefixes both daemons' output
  `[decode]`/`[nlp]` onto one console; on ^C or if **either** daemon dies, tears both
  down in order (SIGINT, then escalate to kill after 10s — `:144`–`:160`). Children run
  `start_new_session=True` so ^C reaches only the supervisor.

Client readiness is handled patiently: `RemoteNLP.await_ready()` polls `info()` through
a long warmup (deberta npz load + cold XLA compile outlast any 5s control-op timeout)
and prints honest progress, naming "warming up, or NOT STARTED?" rather than implying a
warm-up that may not be happening (`nlp_client.py:92`).

**Honest gaps (daemon/ops):**
- Lifecycle is **foreground-supervisor only**. `run_coref_stack.py` is a hand-launched
  console process; there is **no** systemd unit, no auto-restart-on-crash (the supervisor
  *exits* when a daemon dies — `:142` — it does not respawn), no boot persistence, no
  health endpoint beyond `ping`/`info`. A hook firing against a down stack gets a
  `RemoteError` after its timeout, not a managed failover.
- The runbook (`BOOTSTRAP.md`) documents from-scratch fixture production
  (`fixtures/weights.npz`, `deberta_maverick.npz`, `.spm`) and launch, but assumes a
  human at a terminal.

### 1.2 The fact extraction + facts wire — WORKS

- `extract.doc_to_facts` (`extract.py:238`) is the **SSOT** per-document extractor (one
  home, two callers — ADR-0012 P1). Output shape (`extract.py:254`): `sents`,
  `entities` (`text`/`canonical`/`label`), `temporal` (`DATE`/`TIME`), `triples`
  (`subj`/`pred`/`obj` + coref-and-entity-resolved `subj_key`/`obj_key` + `negated`).
  All strings + int offsets, so JSON is bit-exact (ADR-0009 discrete-invariant).
- The daemon runs `doc_to_facts` host-side (`nlp_server.py:620`, `format="facts"`), so
  the `--remote` client deserializes JSON only and **never imports spaCy/torch** — the
  lean-client cut, foreclosed by `test_lean_remote_client.py` and the import-XOR gate
  (`test_import_xor.py`). Coref clusters are attached per-doc before extraction via the
  ONE decoder `resolve.attach_coref_clusters`, shared with `nlp_client.pipe`, so the
  facts and DocBin paths cannot drift.
- Batched-vs-serial coref fidelity is checkable in-band: `--coref-verify` runs both and
  reports PASS/FAIL with per-paragraph mismatches, loading the *trusted serial* clusters
  (`load_facts.py:253`).

### 1.3 The psql sinks — WORK (two stores)

- **`mining` schema** (`schema.sql`) — the fact store. Logic-agnostic relational base
  (`document` / `sentence` / `assertion` / `entity` / `temporal`, each with a jsonb
  `extra` escape hatch) plus per-logic **views** (`fact_classical`, `contradiction`
  for paraconsistent/defeasible, `fact_temporal` for valid-time). `load_facts.py` mines
  a text and writes it, in `--batch-size` batches each written-and-freed before the next
  (the KNOWABLE host-memory cap, byte-identical to one-shot —
  `test_load_facts_batching.py`). Re-load replaces (`UNIQUE (sha256, model)`).
  Self-declared **ephemeral**: "not a blessed migration … a throwaway we keep only until
  the shape stabilises, then it graduates to a real `db/harness/NNN_*.sql`."
- **`nla` schema** (`nla_lab/lab_report.py:157`) — the bench-result store
  (`nla.bench_result`), the queryable perf/measurement ledger (`bench.py:470`,
  `test_bench_psql.py`). Separate concern from the fact store; mentioned because it is
  the *second* live psql sink and the model for an immutable-measurement table.
- **`adjudicate` store** (`store.py`) — `SqlStore`, SQLAlchemy Core, DDL **derived** from
  `schema.store_columns()` (`FieldKind` is the one owner of the SQL type — `_sa_type`,
  `assert_never`). One URL-parameterized adapter serves SQLite (pilot) **and** psql
  (prod, harness `postgresql+psycopg://` at 192.168.122.1); no caller branches on
  backend.

**Honest gaps (schema):**
- The `mining` schema is **explicitly ephemeral** and has not graduated to a blessed
  `db/harness/NNN_*.sql` migration. The brief names a `nla` *fact/grounding* schema as a
  target distinct from the mining PoC store; today the only `nla.*` table that exists is
  the bench ledger, **not** a groundings/verdicts store. That table does not yet exist
  (see §3d).
- The `adjudicate` tables (`adj_doc_selection`, `adj_coref`) are created on demand via
  `ensure_schema`; there is no blessed DDL artifact for them either.

### 1.4 The adjudicate widget — doc-selection LIVE, coref DEFINED-not-wired

`adjudicate/` is `mypy --strict` clean (14 files) and `pytest` green (the suite under
`tests/`). The architecture is one schema → four seams (ADR-0012 P1/P2):

- **Schema SSOT** (`schema.py`) — illegal states unrepresentable: closed axes are
  exhaustive `assert_never` unions; cross-references are construction-time refusals (the
  coherence-gate). A `Schema`/`Record`/`Task`/`Adjudication` that would render an
  incoherent surface *cannot be constructed* (the unrepresentability table,
  `DESIGN.md` §1; `tests/test_schema_coherence.py`).
- **One render → both surfaces** (`render(schema, task) -> RenderModel`). `TextualFrontend`
  (human TUI) and `HeadlessFrontend` (policy-driven) consume the *same* render-model;
  `tests/test_frontend_parity.py` proves the human and headless surfaces produce the
  same `(schema_key, task_id, verdict, row_index)` adjudication contract for any
  decision, both modes, both drivers. **The LLM driver is not a separate code path** —
  it is `HeadlessFrontend` + `LLMPolicy`, whose only deferred piece is one
  `complete(prompt) -> str` seam (a real Claude call or a test fake — `frontend_headless.py:74`).
  `RulePolicy` is the real, no-LLM autonomous policy.
- **doc-selection (SINGLETON) runs end-to-end TODAY** against real corpora:
  `python -m app --corpus rfc|tei --frontend headless|textual` loads → bus → adjudicate
  → persist → load-back (`app.py:45`). Loaders read the located host corpora
  (`/home/bork/distill/rfc`, `/home/bork/distill/UNv1.0-TEI`).
- **coref-adjudication (BATCH) is DEFINED, not wired** (`instances.coref_schema`):
  payload `context`/`explanation`/`doc`; columns `antecedent`/`anaphor`/
  `grounding_source`/`confidence`; verdicts `coreferent`/`not-coreferent`/`uncertain`.
  It is exercised only by `loaders.coref_stub_tasks` — **placeholder** mention-pair rows
  standing in for the NLP service's output (`loaders.py:146`).
- **The Bus is the degenerate `InProcessBus`** (a single-process deque — `bus.py:82`).
  `ZmqBus` is **designed-for**: the `wire` codec (serialization, ADR-0012 P7) and the
  poll/publish framing are real and tested (`test_store_and_bus.py` roundtrips); only the
  socket is deferred behind an injected `Transport` Protocol (`bus.py:108`), "kept an
  adapter because whether it ends up ZMQ depends on what claude-code hooks allow."

**Honest gaps (widget):**
- No hook exists. `coref_schema` has never been fed a *real* grounding; the connective
  tissue from `nlp_server` output to a coref `Task` is unbuilt.
- `ZmqBus.transport` has no real `zmq` adapter — only the in-memory test fake.
- `LLMPolicy.complete` has no real Claude binding wired into a runnable entrypoint (the
  contract is tested with a fake).

### 1.5 The data-shape gap that the whole thing pivots on

This is the single most load-bearing gap, so it is stated up front, not buried (ADR-0013
Rule 4 — a known defect is named, not narrated-and-left):

**The NLP service does not emit what `coref_schema` consumes.** The facts wire emits
`triples` with `subj_key`/`obj_key` *already coref-resolved into canonical constants*
(`extract.py:289`), and the coref backend emits **clusters of `[start,end]` char spans**
(`nlp_server.py:657`). But `coref_schema`'s columns are **`antecedent`, `anaphor`,
`grounding_source`, `confidence`** — i.e. *candidate mention-pairs with a per-pair
grounding rationale and a confidence score*. The pipeline today produces neither
mention-*pairs* (it produces clusters), nor a per-pair `grounding_source` label, nor a
per-pair `confidence`. Bridging this — clusters → adjudicable candidate pairs with
grounding + confidence — is the **core adaptor** of the hook (§3a). It is exactly the
thing `coref_stub_tasks` is faking today.

---

## 2. THE SMALLEST VIABLE NEXT MILESTONE

**M0 — One real claim, end-to-end, recorded.** A single AI-collaborator claim string is
passed to the running NLP stack; one real grounding (not the stub) becomes one
coref-adjudication `Task`; the `HeadlessFrontend` + `RulePolicy` (no LLM — honors the
"no LLM for the PoC" constraint) adjudicates it; the verdict lands in psql; the row is
read back and printed. **No hook, no ZMQ, no LLM, no human TUI** — those are M1–M4.

Concretely, M0 is a single new script (call it `coref_grounding_loader.py`, sibling to
`loaders.py`) that:
1. takes a claim/context string,
2. calls `RemoteNLP(...).pipe_facts([text])` (or a `format="json"` parse for the raw
   clusters) against the live `:5599` stack,
3. runs the **clusters → candidate-pairs + grounding + confidence** adaptor (§3a) — the
   real replacement for `coref_stub_tasks`,
4. builds a `coref_schema` BATCH `Task` from those rows,
5. drives it through the existing `HeadlessFrontend(RulePolicy(...))` → `SqlStore(psql)`
   path that doc-selection already uses.

M0 deliberately reuses every proven seam (render, frontend, store) and changes exactly
**one** thing: the grounding source goes from stub to real. It proves the thesis's spine
(claim → grounding → adjudication → recorded verdict) with the *least* new surface, and
it makes the §1.5 data-shape gap concrete and testable instead of theoretical. It is the
ratifiable unit; M1+ are then honest, separately-ratified increments, not a monolith
this milestone pretends to include.

**Why not smaller:** dropping the real grounding (step 3) leaves `coref_stub_tasks`,
which proves nothing new — the suite already exercises that. Step 3 is the irreducible
core. **Why not bigger:** the hook, the ZMQ transport, the LLM policy binding, and the
human TUI each carry independent risk and each deserves its own ratifier checkpoint.

---

## 3. WHAT WE NEED TO MOVE FORWARD — concrete + sequenced

Ordered by dependency. M0 (§2) is the seed; each milestone below is independently
ratifiable.

### (a) The grounding adaptor — clusters → adjudicable rows  *(blocks everything; in M0)*

The keystone, because §1.5 is the gap the stub hides. Build a pure function
`groundings(parse_result) -> list[coref-row]` that maps the NLP service output to
`coref_schema`'s `(antecedent, anaphor, grounding_source, confidence)` columns:

- **Mention-pairs from clusters:** a coref cluster of char spans yields candidate
  antecedent→anaphor pairs (e.g. each non-first mention paired with its candidate
  antecedents). This is a deterministic transform over the cluster char spans the daemon
  already returns.
- **`grounding_source`:** the *reason* a pair is a candidate — the epistemic signal the
  collaborator is being interrogated on. Honest sourcing options, in order of fidelity:
  (i) the coref model's own scoring if surfaced, (ii) the linguistic feature that
  licensed the link (subject-salience, semantic-role, as the stub already gestures at),
  (iii) the SVO triple the mention participates in (`extract.py` already computes these).
  This is a **real modeling decision**, not a formatting one — it must be ratified, not
  silently picked. Surface the options with costs; do not pre-draw the conclusion
  (ADR-0013 Rule 3).
- **`confidence`:** a real score or an explicitly-declared placeholder. If the maverick/
  jax decode does not expose per-pair scores cheaply, declare the placeholder loudly
  (ADR-0002) rather than inventing a number — a fabricated confidence on an
  epistemic-state interrogator is the worst-case lie.

Built as a pure function, it is unit-testable against fixed cluster fixtures with **no**
daemon (mirrors how `doc_to_facts` is tested), and it is the direct, honest replacement
for `coref_stub_tasks`.

### (b) The claude-code HOOK integration  *(M1; depends on a)*

The hook is the product. Mechanism, grounded in what the seams already expose:

1. **Trigger.** A claude-code hook fires on an AI-collaborator turn carrying a claim
   (the hook event + matcher is a settings.json concern — see the open question in §5).
   The hook hands the claim text (and minimal context) to a thin client.
2. **Invoke the NLP service.** The client is the *lean* `RemoteNLP` (`nlp_client.py`) —
   json + zmq + psycopg only, **no spaCy/torch** (the import-XOR gate guarantees the hook
   process stays light). It calls `pipe_facts` / parse against `:5599`, after
   `await_ready()` so a warming daemon is waited through, not crashed on.
3. **Route to the coref-adjudication frontend.** The grounding adaptor (a) turns the
   result into a `coref_schema` BATCH `Task`. The task goes onto the **Bus** (degenerate
   in-process for M1; ZMQ for M2 — (c)) and is drained by a **Frontend**:
   - autonomous: `HeadlessFrontend(RulePolicy)` (M1, no LLM) or `HeadlessFrontend(LLMPolicy)`
     (M3) — the LLM-as-adjudicator, *not* a separate path;
   - human: `TextualFrontend` (M4).
4. **Record the verdict.** `SqlStore(psql)` persists the adjudication with its task
   context (payload + adjudicated cells — `store.persist`). This is the recorded
   epistemic-state verdict; `store.load` reads it back.

The hook's own logic is deliberately thin: it is *transport + the adaptor (a)*, because
every decision/render/persist seam already exists and is parity-tested. ADR-0013 Rule 1:
the hook's "done" is *a real collaborator turn producing a recorded verdict*, not a
mock.

### (c) Wire the Bus from in-process to the real (ZMQ-shaped) transport  *(M2; depends on b)*

`ZmqBus` is designed-for and the codec/framing are already real and tested (`bus.py:121`,
`test_store_and_bus.py`). The remaining work is the **one injected dependency**: a real
`Transport` (`recv_frames`/`send_frame`) backed by an actual `zmq` socket. The project
*already runs ZMQ everywhere else* (`nlp_client`, `coref_decode_client`,
`run_coref_stack._wait_ready` are all `zmq.REQ`/`REP`), so the socket idiom is in-house
and proven — this is binding a known transport behind a tested seam, not new
infrastructure. The frame contract is fixed: inbound = `wire.encode_task`, outbound =
`wire.encode_adjudication` (`bus.py:126`). The open dependency (named honestly in the
docstrings) is **what claude-code hooks actually permit** for transport — the seam is
kept an adapter precisely so this can resolve to ZMQ, a pipe, or a file drop without
touching the schema (§5).

### (d) NLP service deployment / ops  *(M2-parallel; independent of the hook)*

Turn the hand-launched supervisor into a managed service. Concrete, sequenced:

1. **Managed lifecycle.** Wrap `run_coref_stack.py` in a systemd unit (or equivalent) on
   the host: start on boot, `Restart=on-failure`. Today the supervisor *exits* when
   either daemon dies (`run_coref_stack.py:142`); a unit makes that a *restart*, not a
   stall. Keep `XLA_PYTHON_CLIENT_MEM_FRACTION` capped so the jax daemon does not pre-grab
   the card from the torch encoder (the supervisor already passes `--mem-fraction 0.3`).
2. **Health.** `ping`/`info` exist; add a periodic external probe (the unit's health
   check, or a tiny watchdog using `RemoteNLP.ping`/`info` with the existing fail-fast
   5s timeout) so a wedged daemon is detected, not discovered by a hook timing out.
3. **Failure modes to handle explicitly:** (i) decode daemon down → nlp_server's
   jax-unified relay fails; warmup already tolerates this (logs loudly, keeps serving a
   *parse-only* path) — decide whether the hook degrades to parse-only groundings or
   fails closed; (ii) cold compile on restart (the 300s readiness window — handled by
   `await_ready`); (iii) GPU OOM under concurrent load (the OOM invariant work exists —
   `test_oom_invariant.py`, `shape_buckets.py` compile-bound — but **concurrency policy
   for many hook firings is unspecified**: the daemons are single-REP-socket request/
   reply, so concurrent hooks serialize; decide queue vs. reject-with-backpressure).
4. **Restart semantics.** Document and test that a restart loses no committed facts
   (psql is durable) and that an in-flight hook gets a clean `RemoteError`, not a hang.

### (e) Data / schema gaps  *(threads through M0-M2)*

1. **Graduate the stores from ephemeral to blessed.** The `mining` schema self-declares
   throwaway status; `adjudicate` tables are `ensure_schema`-on-demand with no DDL
   artifact. Per the brief, the **groundings + verdicts** belong in a blessed `nla`
   schema (today only `nla.bench_result` exists — the perf ledger, a *different*
   concern). Decision needed (ratifier): is the hook's grounding/verdict store
   (i) the `adjudicate` `adj_coref` table pointed at psql, (ii) a new `nla.grounding` +
   `nla.verdict` pair, or (iii) both joined? Recommend modeling it on the
   `tlab_reading`/`tlab_finding` split the corpus already uses (ADR-0009): **immutable
   grounding** (what the NLP service produced for a claim) vs. **supersedable verdict**
   (the human/LLM adjudication of it), so an overturned verdict is auditable, not lost.
2. **Provenance join.** A recorded verdict must be joinable to: the claim text, the NLP
   `model` label (the facts wire carries it), the grounding rows, the adjudicator
   identity (human vs. which policy/LLM), and ideally the claude-code session id (the
   harness's existing perf-provenance gap, §ADR-0009 report — do not repeat omega's
   timestamp-only non-attribution). `Adjudication.note` carries provenance today
   ("rule: …" / "llm") but it is unstructured; structure it.
3. **The doc-selection store** already proves the psql path works; the coref store is the
   same `SqlStore` with `coref_schema` — the gap is the blessed DDL + the provenance
   columns, not the adapter.

### (f) The END-TO-END DEMO that proves the thesis  *(M3/M4 — the ratifiable proof)*

The demo script that, run once, demonstrates the whole claim:

> An AI collaborator asserts *"The committee reviewed the report; it found the measures
> adequate"* → the hook routes it through the NLP service → the grounding adaptor
> surfaces the candidate coreference (does *it* = the committee or the report?) with
> grounding + confidence rows → a human (TUI) **or** an LLM (`LLMPolicy` with a real
> Claude `complete`) adjudicates `coreferent`/`not-coreferent`/`uncertain` → the verdict
> is written to psql and read back, joined to the claim and the adjudicator identity.

The demo is the *same* example `coref_stub_tasks` already encodes (`loaders.py:152`) —
which is the point: it makes the stub real. Running it through **both** a human
`TextualFrontend` and a headless `LLMPolicy` on the *same* task discharges the thesis's
"human-OR-LLM" claim with the parity machinery (`test_frontend_parity.py`) already proven.

---

## 4. THE SEQUENCE (assembled)

| Milestone | Deliverable | Depends on | LLM? | Hook? | Transport |
| --- | --- | --- | --- | --- | --- |
| **M0** (smallest viable) | grounding adaptor (a) + one claim → real coref task → RulePolicy → psql → read-back | live `:5599`/`:5600` stack | no | no | in-process |
| **M1** | claude-code hook (b): real turn → lean client → adaptor → headless RulePolicy → psql | M0 | no | yes | in-process |
| **M2** | ZmqBus real `Transport` (c) **and** managed daemon ops (d) — parallel tracks | M1 (c); none (d) | no | yes | ZMQ |
| **M3** | `LLMPolicy.complete` bound to a real Claude call; LLM-as-adjudicator end-to-end | M1 | yes | yes | either |
| **M4** | human `TextualFrontend` reachable from the hook; the §3f demo through both surfaces | M1–M3 | both | yes | either |

Schema graduation (e) and provenance structuring thread through M0–M2 (the verdict store
must be blessed before M1 writes production verdicts).

---

## 5. GAPS, RISKS, OPEN QUESTIONS (risk-averse posture)

**Open questions that need a ratifier decision (do not silently resolve):**
- **`grounding_source` semantics (3a)** — what epistemic signal the column carries is a
  modeling decision, not formatting. Surface options + costs; do not pre-pick.
- **`confidence` provenance (3a)** — real score vs. declared placeholder. A fabricated
  confidence on an epistemic-state interrogator is the worst-case lie; declare loudly if
  the decode does not expose one cheaply.
- **The verdict store (3e)** — `adj_coref`@psql vs. a new blessed `nla.grounding`/
  `nla.verdict` pair; recommend the immutable-grounding / supersedable-verdict split.
- **Hook transport (3c)** — ZMQ vs. pipe vs. file-drop is gated on *what claude-code
  hooks actually permit*; the Bus is kept an adapter for exactly this reason. Settling it
  needs the claude-code hook execution model confirmed (a hook runs a command with an
  event payload; whether it can hold a long-lived ZMQ socket vs. a short-lived
  request/reply is the deciding fact).
- **Hook trigger point** — which hook event (and matcher) carries an "AI-collaborator
  claim", and whether the hook blocks the turn or fires async, is unspecified and is a
  settings.json/event-model question.

**Risks (with the maintainer's risk-averse, life-critical bar in mind):**
- **R1 — the stub masks unsolved modeling (HIGH).** The single biggest risk: the
  attractive demo is to wire `coref_stub_tasks` to the bus and call it "the hook." That
  ships a fabricated grounding past review. M0 forecloses it by making the *real* grounding
  the irreducible core (ADR-0013 Rule 3: "lower-ROI to do it properly" is the tell).
- **R2 — fabricated confidence/grounding (HIGH, would-not-trust-my-mother bar).** An
  epistemic-state interrogator that emits invented confidence numbers is actively
  misleading. Mitigation: declared placeholders, loud (ADR-0002), never silent invention.
- **R3 — daemon single-point-of-failure (MEDIUM).** No managed lifecycle today; a down
  stack fails every hook. Mitigation: (d) systemd `Restart=on-failure` + external health
  probe before M1 writes production verdicts.
- **R4 — concurrency unspecified (MEDIUM).** Single REP socket per daemon serializes hook
  firings; many simultaneous turns queue or time out. Mitigation: decide queue vs.
  backpressure in (d); the OOM-invariant + shape-bucket work bounds the per-request memory,
  not the concurrency.
- **R5 — ephemeral schema in a production path (MEDIUM).** Writing real verdicts into an
  explicitly-throwaway `mining`-style schema risks a `DROP SCHEMA … CASCADE` of audited
  data. Mitigation: graduate to a blessed migration (e) **before** M1.
- **R6 — provenance non-attribution (LOW-MEDIUM, but a named corpus failure).** The
  ADR-0009 report documents omega shipping perf numbers with timestamp-only,
  non-attributable provenance. The same trap here = a verdict not joinable to its claim/
  model/session. Mitigation: structure provenance (3e.2) from M0, not retrofitted.

**What is NOT a gap (settled — do not reopen):** the encode/decode numerics, the Pallas
kernel, quantization, data selection. The fidelity (serial-vs-batched coref), the
host-XOR-device split, the lean-client import discipline, the memory-cap batching, and
the render/parity proofs are all built and gated. The remaining distance to the thesis is
**integration and operations**, and it is tractable.
