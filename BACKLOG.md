# autoharn — informal backlog

Provisional and informal. This file exists because the structured work-log store (#3 — the SQL SSOT for
work status) does not exist yet. When it does, these items migrate there and this file retires. Until then:
a plain, append-friendly list of live threads, so nothing is lost to memory.

> **MIGRATION STATUS (2026-07-07, autoharn consolidation).** This file is carried
> **verbatim** from `claude_harness/BACKLOG.md` (source commit `87e1bcc`). The manifest
> (A1/[C4]) envisioned carrying only *live* entries and leaving *closed* ones in the
> archive history — but that content-curation is not on BUILD-BRIEF §0's closed
> adaptation list, so per §0 (edits outside the list are renegotiated, not self-taken)
> and the ADR-0008/ADR-0012 ARCHITECTURE precedent ([C12]: content work is deferred, not
> done inside a migration), the curation is **deferred**, filed here as its own item:
> *prune the closed fact-mining-lane churn below to live autoharn threads only.* The one
> sanctioned edit at migration time is the maintainer reservation immediately below.

---

## Maintainer reservation — the no-`/docs` top-level decision (revisit-when marker)

**Filed 2026-07-07 at the maintainer's ruling on the consolidation design (acts.ruling
121 GO).** The maintainer ratified the whole layout as committed (all 24 CONS-DECIDED
calls stand) with ONE recorded reservation: he **defers** on the decision to have **no
top-level `/docs` directory** (LAYOUT §4: "docs is not a currency … each former docs
resident lands in the directory named for what it IS"). His words: he has *"never
encountered a rigorous code base where documentation is not single-homed into /docs."*

- **Disposition:** deferred, not overruled — the layout ships as designed (law/design/
  research/judgment each home their own currency; no `/docs`).
- **Revisit-when:** the maintainer chooses to reconsider. This is flagged as **the
  easiest thing to change later** — re-homing the doc-bearing directories under a `/docs`
  parent is a pure move, mechanical, with the layout-census gate updated to match.
- **The design's counter-argument, for the record (LAYOUT §4):** "docs" bundled three
  distinct currencies (law, design, evidence) into indistinguishability in both old
  repos; the split makes authority level legible from the path. This reservation records
  that the maintainer's single-home-into-/docs intuition is a live, unresolved tension,
  not a settled question.

---

## Design principles to hold (rationale, not tasks)

- **Forward-compatibility / composability is a first-class design constraint.** We will not get any
  taxonomy exhaustive on the first try — we are not even sure what "exhaustive" means for some of these
  yet — so every schema must evolve **additively**: new study designs, capability kinds, obligations, and
  measurement/analysis dimensions can be added **without breaking existing data or downstream consumers**.
  Concretely:
  - `jsonb` escape-hatches for not-yet-modelled structure (e.g. `reading.config`);
  - closed-vocabulary enums that are only ever **widened**, never narrowed (ADR-0008 stays MECE by adding
    cells, not by re-bucketing);
  - generic dimensions (`project_id`, and — if it earns its place — a unit/subject-of-observation
    dimension) over baked-in assumptions;
  - schema-per-store namespacing (`core` / `research` / `registry` / `work`) so stores **compose** rather
    than entangle.
  Rationale: forward-compatibility is the generic justification for composable software, and it is far
  cheaper to leave the seam than to retrofit it. *(Shoehorned in deliberately, per the maintainer.)*

---

## Conundrums

Open problems with no known mechanism yet — the things that, left unsolved, cap what the project can
deliver. Listed so they aren't forgotten; each wants an ADR-0011 mechanism we don't have.

### C1 — Detecting laziness-informed judgements (the "do-less" ambiguity)

**The problem.** An LLM's recommendation to do LESS — defer, omit, "leave a seam", "keep it minimal", "out
of scope" — is surface-indistinguishable from genuinely-informed restraint. Every time one appears, the
maintainer must ask: informed judgement, or laziness wearing discipline's clothes? For LLM-leveraged
workflows this is pervasive and first-class: unexamined, it silently lowers the ceiling on everything. It is
the same shape as the deflation cascade (the auditor that acquitted) and SPEC-ADEQ (the adequacy of a
judgement can't be checked from inside the LLM layer).

**Discriminator (proposed, partial).** Laziness = UNDIFFERENTIATED minimisation justified by an
UNFALSIFIABLE discipline-word ("minimal", "proportionate", "enough"). Informed restraint = DIFFERENTIATED
calls under a FALSIFIABLE criterion that sometimes points toward MORE. Test: does the "do-less" set come
with a "do-MORE-here" set under the same stated criterion? *Worked example:* the 2026-06-28 taxonomy second
opinion passes — it pulled `observed_at` out to must-fix-now *because deferring is lossy* (a checkable
property); laziness would have flattened to "defer all". Its soft spot is the scope call ("don't build
study-design machinery") — defensible judgement, not a falsifiable property: the human-judgement residual.

**Seed mechanism (what we have).** The hack-rationalization-detector: force every "do-less" to expose (a)
the more-general fix it set aside and (b) a CONCRETE COST that justified setting it aside — a discipline-word
is not a cost. A judgement naming no concrete cost is presumptively lazy.

**Open (no ADR-0011 mechanism yet).** Generalise from code-fixes to ALL judgements: every defer/omit carries
`{criterion, evidence, kill-condition}` as structured data a gate can check. The hard part: keep the
detector MECHANICAL or human-rooted — an LLM judging an LLM's laziness shares the bias and deflates (proven
this session). Likely partially-mechanisable (raise the cost of a lazy judgement by forcing a falsifiable
discriminator), with an irreducible human residual on adequacy.

### C2 (no comment, behold)
```
● That's a genuinely strong, skeptical review — and it sharpens your instinct rather than just agreeing. Let me read the current daemon lines so I can add the ACL markers precisely, then build the gate:

  Read 1 file

● The second opinion's verdict is clear and I'll act on the uncontroversial parts now: keep fp32 (reject .half()), add the single-homed-boundary markers, fix the silent-degradation flag (make a failed cast fatal, not swallowed), and build
  a proportionate gate. Let me apply the daemon changes:

● Now the gate itself — a proportionate, pure-AST single-homing check (no baseline ratchet, per the second opinion's "port the discipline, not the machinery"):

```
1. Proportionate under what model?
2. How does one reason with NLP + logic tools when the claude sentences are staccato? It's simply not sufficient to rely on single sentence analyses. The first example even implies so many things that need scruty
    * "your instinct" (what is my instinct)
    * "sharpens" (why?)
    * "the second opinion's verdict is clear" (what is the verdict)
    * "will act on uncontroversial parts" (what is uncontroversial, why, and according to whom?)
    * "that's a genuinely strong, skeptical review" (and if it weren't, would you notice? what standards do you hold when you assert this?)
---

## Proposed LAW — the service contract is an enforcement surface, not an aspiration (candidate ADR-0015, 2026-07-01)

> **Drafted as `docs/adr/0016-the-service-contract-is-an-enforcement-surface.md` (2026-07-02, this commit),
> pending maintainer ratification.** 0015 was taken by verification-substrate-discipline since this was seeded,
> so it graduated at the next free number, 0016. The seed below is left in place verbatim as the draft's
> provenance and spec — the ADR follows its three feeders and its (a)–(d) candidate rules; where the draft
> adds beyond these words (the advertised-limits-are-the-contract clause, the audit-vs-standing-gate
> distinction) it flags the addition inline for the ratifier.

### ADR-0016 Rule 2 umbrella — LANDED (2026-07-02, this commit)

Rule 2's named-and-filed mechanism — "a single CI job that runs the standing-service property suite
over every ingress of every declared standing service as one net, with the negative control per
boundary" — is **built** and green. **ADR-0016 Revisit-when #2 is now actionable**: the maintainer
can ratify Rule 2 from partly-built toward fully-mechanized once the runner is wired into
pre-commit/CI (the one residual, filed below).

**The pieces (new files only, per the concurrent-edit constraint):**
- `experiments/fact-mining/standing_service_registry.py` — the declared-services registry (data the
  gate walks): each service's name/port/module, every wire op it accepts, each op's adversarial axes,
  and the property suite(s) covering each axis (or a declared gap + BACKLOG pointer). TWO scan nets
  keep it from failing open (ADR-0011 Rule 4 — a net quantifies over the class, not the instance):
  `discover_standing_service_modules` reads the tree for the standing-service signature (a non-test
  module that CALLS both bind_rep and serve_forever), so a NEW daemon module dropped in without a
  StandingService entry fails a test; and `scan_op_literals` reads each daemon's `op ==`/`!=`/`in
  (...)`/`.get("op", …)` dispatch literals out of its source AST, so a new op handler without a
  registry ingress fails a test. The service SET is thus a scanned net, not a hand-list (the fix the
  ADR-0014 audit's must-fix demanded — the enumeration-fails-open defect one level above the op-scan).
- `experiments/fact-mining/test_standing_service_gate.py` — the gate: op-scan completeness, no-silent-gap,
  no-dangling-pointer, and red-proof-annotation teeth, **each with a negative control beside it**.
- `tools/standing_service_gate.py` — the one invocation: prints the coverage table + declared limits,
  then runs the gate together with every referenced bound suite as one pytest net (subprocess, venv).
- `experiments/fact-mining/conftest.py` — registers the `standing_service` marker (additive only).

**Umbrella run (venv generic):** gate teeth `37 passed`; full net `300 passed, 4 skipped` (GPU-gated
skips; no GPU, no live daemon) in ~32s. `tools/no_lazy_imports.py` → 0. mypy `--strict` clean on all
new modules.

**Coverage census — 3 services, every scanned op declared (scan==registry):**

| service | :port | ops (all declared) | substantive-ingress axes | status |
|---|---|---|---|---|
| nlp_server | 5599 | ping, info, parse | recv/timing, strict-decode, batch-count, texts-shape, parse-format, char-ceiling, token-budget, config-allowlist, trace-gate, per-doc-isolation, mem-envelope, readiness, peer-wait | all covered |
| coref_decode_daemon | 5600 | ping, info, coref, decode | recv/timing, strict-decode, texts count+chars, config-allowlist, trace-gate, per-doc, mem-envelope · (decode:) docs-count, per-doc-shape, token-magnitude, lhs-bytes-match, readiness | all covered |
| gliner_server | 5601 | ping, info, gliner | recv/timing, strict-decode, texts count+chars, labels, threshold, servable-window, per-doc, mem-envelope, readiness | all covered |

**Declared gaps (filed, non-silent — a declared gap passes with a warning; a SILENT gap fails):**

| gap | surface | disposition |
|---|---|---|
| Runner not yet wired into `tools/hooks/pre-commit` / CI | filed | maintainer ratification (ADR-0016 Revisit #2) — the gate is honestly PARTIAL until wired |
| `concurrency-single-in-flight-rep` (×4 substantive ingresses) | filed | foreclosed by construction: REP is single-in-flight; ADR-0016 "does NOT mean" — a closed axis needs no generative gate |
| Shipped-binding: net runs on the guest; a few suites SKIP the GPU path | filed | those axes proven on the guest subset; host cluster-fidelity covered elsewhere (load_facts --coref-verify) |
| `scan_op_literals` reaches only `op`-variable dispatch syntax | review-only | an op routed by a dict table / `match` is not scanned (ADR-0011 Rule 1) |
| `discover_standing_service_modules` keys on the bind_rep+serve_forever signature | review-only | a service on a different transport would evade the scan (same class as above) |
| per-op axis LIST exhaustiveness + "does the named suite exercise the named axis" | review-only | the gate proves declared axes point at real registered suites (no dangling pointer); it does not prove the suite exercises that axis, nor that the axis list per op is complete |
| Rule 4 (plumbing held to the core's bar) | review-only | no gate reads "bar applied uniformly" — ADR-0016's own declaration |

**Negative-control evidence (a gate never seen red is a claim — ADR-0011 2026-07-02):**
- service-set: a synthetic new daemon module (calls bind_rep + serve_forever) is discovered as undeclared while a non-service peer + a test harness are excluded (`test_service_set_negative_control`).
- op-scan: a synthetic `if op == "sabotage"` source is caught as unregistered (`test_op_scan_negative_control`).
- silent-gap: a synthetic axis with empty coverage + null backlog_ref is flagged (`test_no_silent_coverage_gap_negative_control`).
- red-proof: a `raises`-annotated file with no `pytest.raises` is flagged (`test_red_proof_negative_control`) — and this actually fired during development: `test_bound_socket.py`'s red-proof is a silent-drop (libzmq never delivers), not a raise, so its annotation was corrected `raises`→`degrade` by the gate's own complaint.

**ADR-0014 audit (opus, out-of-frame).** Verdict: the gate forecloses "a new entry point cannot ship
without coverage" mechanically; the **must-fix** it found was that the SERVICE SET itself was a
hand-listed tuple that failed open — a new daemon module would silently skip the umbrella (the
ADR-0011 Rule 4 enumeration-fails-open defect, one level above the op-scan, and undeclared). Fixed in
this commit: `discover_standing_service_modules` makes the service set a scanned net with its own
negative control. Also applied from the audit: the `op in (...)` scan-evasion is now handled; the
shipped-binding (guest-skip) limit and the "named suite exercises the named axis" limit are now filed
gaps (were understated). Should-note residuals accepted as filed/review-only: the negative controls
exercise the teeth *predicate* rather than driving a mutated input through the teeth function, and the
runner credits SKIPs as green (guest shipped-binding) — both declared.

Red-proof census over the 25 bound suites: 15 `raises` (drive a malformed/over-cap input into a
typed refusal) · 10 `degrade` (prove a property over the adversarial class — e.g. the trace gate is
off ∀ wire body; the over-cap frame never reaches recv). Zero `none` (no unproven suite in the net).

A cross-cutting **executive** tenet in the genre of ADR-0000/0011/0012/0013/0014, seeded from dated
first-person faceplants; to be drafted in full against those specimens and graduated into the in-repo `docs/adr/`
ADR set (next free number). Filed here so the lesson is not lost.

**Provenance.** The `standing-service-invariant` workflow (run `wf_ee73fb10-f41`, 2026-07-01): five blind
adversaries/auditors turned on the fact-mining ZMQ daemon stack under ONE principle — *once a service
advertises it is standing, no client input/size/shape/value/ordering/timing/concurrency can make it crash,
wedge, desync, corrupt, hang, leak, or behave statefully; it refuses cleanly at the boundary or refuses to
come up.* Given only the principle + the LAW (never the symptom), it surfaced a class of faceplants in a
service core wrapped in otherwise-careful infrastructure. **Intermediate steps saved** (all auditor
findings, the synthesis plan, the verdicts): per-agent transcripts `agent-*.jsonl` + resume `journal.jsonl`
under `~/.claude/projects/-home-bork-w-vdc-1-claude-harness/<session>/subagents/workflows/wf_ee73fb10-f41/`;
resumable via `Workflow({resumeFromRunId: "wf_ee73fb10-f41"})`. A distilled legible record lands under
`experiments/fact-mining/docs/` when the run completes.

**The substrate (ADR-0000 register).** Beautiful infrastructure — the jax coref daemon, the trace SSOT,
host/device honesty, the seam discipline, shape buckets — wrapped around a service that advertised "ready"
and then detonated deep inside on a real corpus document (input legal at the boundary, fatal three layers
down; ADR-0000 Specimen 1). And *not the first time* the server advertised something it could not serve:
the class recurs.

**The executive lapse (ADR-0000 Rule 2(b) — "what did the EXECUTIVE fail to put in place?").** The
discipline was mechanized for how COMPONENTS are built — mypy-strict, the env↔Policy seams, fidelity /
equivalence / bit-identity tests, the trace SSOT — and NEVER for the SERVICE CONTRACT, the promise a client
actually depends on. Every existing gate polices internal structure and happy-path correctness; none asks
"can a client break this standing service?" So the failure class lived in a dimension with **no enforcement
surface**, and (ADR-0011) a recurrence never converted to a mechanism is a guard the executive did not
build. Three feeders:
1. **Test philosophy was fidelity, not adversarial totality.** The suite is `*_fidelity` / `*_equivalence`
   / `*_bit_identity` — "does the fast path match the reference?" There is no "∀ inputs the service does
   not detonate" (property-based) gate. The core was proven *right*; the service was never proven *robust*.
   Two different nets; one built.
2. **The known boundary answer was not propagated to service ingress.** BoundedBatch (validate-and-refuse
   at the boundary — ADR-0012 P2 / ADR-0000 Specimen 1) is already IN the LAW; it was applied to some
   internal wires and never mandated at *every* client entry point. ADR-0012's own meta-failure ("the right
   idea applied once, not propagated") recurring one level up, at the executive.
3. **Readiness was signed off on convenient inputs.** Warmup exercises a toy paragraph; "ready" meant
   "worked on what I fed it," not "proven over the input space" — the real corpus's worst case never ran
   before the service advertised itself.

The unifying miss: **the mother's-life bar was applied by GLAMOUR, not uniformly** — the novel core got the
rigor; the boring service-plumbing (input validation, readiness coverage, error/protocol handling) coasted
on "it works on my input." A client lives at the boundary, not in the elegant core — which is exactly where
a life-critical system dies.

**The mechanism (candidate rules).** For every long-running service, three gates co-equal with the fidelity
gate, each zero-cost at inference:
- **(a) Every client entry point is a validating boundary** (BoundedBatch, propagated): a typed ACL that
  decodes-validates-or-refuses every request; unservable input → a typed refusal at the edge, never a deep
  detonation. O(1) at ingest; prefer illegal-states-unrepresentable so no runtime check exists at all.
- **(b) An adversarial property gate** (hypothesis/deal), as mandatory in CI as equivalence: "no client
  input/shape/ordering/timing/concurrency breaks the standing service," proven by generated hostile inputs.
- **(c) Readiness = proven coverage of the input space**: "advertise ready" requires warming the full shape
  space AND surviving the real corpus's worst case. A service that a valid input can surprise was not ready.
- **(d) The plumbing is held to the same bar as the core** — the unglamorous surface gets the mother's-life
  bar without exception; the 14-year-old code hides precisely where the work felt boring.

---

## Research-ledger taxonomy — second-opinion findings (ADR-0014, 2026-06-28)

Verdict: keep the EPISTEMIC core verbatim (measurement⊥interpretation, immutable readings, derived
confirmation, growing warrant). Fix the over-claim + one lossy trap; leave cheap additive seams; do NOT
build empirical-study-design machinery into autoharn (consumer concern — confirms the maintainer's instinct).

**MUST-FIX-NOW**
- `observed_at` (lossy if deferred): no column for WHEN an observation occurred; `created_at` is
  trigger-locked to ingest time, so v0-era data can never recover observation time. Add nullable
  writer-supplied `observed_at`; keep `created_at` as the ingest/ordering clock; exempt it from the trigger.
- Honest scope/name: the header claims a generic "research/measurement ledger" but delivers a
  software-benchmark-run provenance ledger — the label is wider than the thing (ADR-0008 over-claim; the
  false-authority pattern at the naming level). Retitle/scope honestly; arbitrary study design = out of scope.

**LEAVE-A-SEAM-NOW (cheap, additive)**
- non-numeric outcomes: `value` nullable + `value_text`/`value_json` (findings are often contrasts: A>B, pass/fail, rank).
- `reading.git_commit` nullable (provenance, not identity) so non-software data needn't forge one.
- unit/**subject-of-observation** identity: nullable `subject_id` (the panel/longitudinal seam).
- **finding → set of readings** (hardest to undo): future `research.finding_evidence(finding_id, reading_id, role)`
  join. *Lead's pushback on the reviewer:* keep `finding.reading_id` as a NOT-NULL **primary** reading + add
  the join for additional evidence, rather than nullable-now (avoids evidence-less findings). Maintainer decides.
- `instrument.kind` non-MECE (harness⊂script; survey/sensor/sim/human absent) — note now so it isn't read as
  authoritative; split into orthogonal **modality** × **role** axes later.

**FINE-AS-IS / later (additive):** `qualification`/`status` enums; the epistemic core; omit panel/RCT machinery;
later entities — study/experiment grouping, analysis/transformation, dataset.

---

## Deferred increments — research ledger

- **increment 2:** `research.reproduction` + the reproducer service ⇒ add the **INDEP** conjunct to the
  `finding_confirmed` warrant.
- **increment 2:** `research.prereg` (+ conclusion) ⇒ add the **criterion-before-result (RECORD)** conjunct.
- **AUTH:** who may write / qualify (a write-authority model) — not yet modelled.
- DB-stamp `finding`/`instrument` `created_at` if their ordering ever becomes load-bearing.
- Decide read-vs-apply-vs-commit path for `001_research_ledger.sql` (validate against a *scratch* Postgres
  first; it has not been executed).

---

## Mandated fixes — fact-mining stack (maintainer-ruled 2026-07-02) — LANDED 309de82; live confirmation owed (psql first_z query in the boot_id_warmup_hack_audit + agent report)

- **nlp_server realistic-batch warmup (the ~340 ms first-parse defect).** Ruled a defect, not a
  judgment call ("it just isn't professional"). Reproducible across server restarts, lives in
  `nlp_server.parse` (spaCy-trf/torch): warmup drives one 11-word paragraph, then advertises READY
  for 128-paragraph batches — CB-05's shape at reduced magnitude; the decode daemon's own grid-sweep
  discipline never reached the torch side. Fix: sweep a representative (batch, length) ladder through
  the trf parse (and torch encode path) pre-READY, ladder derived from the advertised envelope, not
  round literals. Exit criterion (ADR-0013 amendment): first-request `nlp_server.parse` trace span ==
  steady-state span, across a restart, proven from the trace table grouped by boot_id.
- **Boot-UUID discipline (attributability).** Every fresh daemon start mints a `boot_id`; it rides in
  every info/ping reply, every typed refusal payload, every trace span the process emits, and every
  log line — so "which boot produced this evidence" is answerable from artifacts alone (no operator
  memory). Free consequences to take: client invalidates its cached AdvertisedLimits when a reply's
  boot_id changes (closes the OBS-2 one-shot-fold staleness residual with a real detector, not just
  refusal-triggered healing); restart-vs-same-boot performance comparisons become a trace-table query.
  Candidate standing law after it proves out here: services identify their incarnation in everything
  they emit.

## Standing-service finding — spaCy StringStore/Vocab never evicts (2026-07-02, from the first-parse RCA)

- The first-parse residual root-caused to per-novel-string interning (host_run_2026-07-02.md
  addendum 2). The premium itself is cost-of-novelty (disposition open); the LEAK is not:
  a standing nlp_server's RSS grows monotonically with cumulative corpus vocabulary — under
  the guardrails stream (unbounded novel referents) that is a slow-leak class. Actions:
  measure growth (bytes/1k novel tokens; the boot_id-tagged spans + RSS sampling make this a
  query), then evaluate bounded-vocab / periodic prune / scheduled-recycle dispositions.
  The first_z witness must also be respecified (novel-corpus-vs-own-repeat, not boot-order).
  DESIGN (2026-07-02, maintainer asked for the rigor plan):
  1. instrument vocab size + RSS as info fields and span attrs (O(1), off warm path) — growth
     becomes a boot_id query; run it on docs/claude-ephemera (the REAL hook input), raw vs
     prose-filtered — this also decides the hook-adapter question (see next item);
  2. declared memory envelope for nlp_server (ADR-0015 Rule 1) + degrade readiness report at
     threshold (fail loud before failing slow); **LANDED 2026-07-02, this commit.** Both daemons
     derive a `MemoryEnvelope` (wire_types) at READY from their own warm-ready RSS + a headroom
     (`--rss-headroom-gib`, default 2.0), verify admit==servable against /proc/meminfo MemTotal
     minus a reserve (refuse to come up otherwise; ADR-0000), advertise it + the live
     `MemoryDisposition` on the info op, classify every admitted request's RSS at admission
     (one ~µs /proc read), log the `approaching` transition once, and REFUSE at the ceiling with a
     typed `MemoryEnvelopeExceeded` naming the incarnation + numbers (the daemon stands, never
     exits — the operator decides). Clients cache the envelope beside AdvertisedLimits and raise the
     typed exception via the single `_parse_reply` home. Tests: test_memory_envelope.py.
  3. if the stream outruns the envelope: GENERATION RECYCLING behind the existing atomic
     dispatch-swap seam — build fresh pipeline in background, warm via the existing ladder,
     REPLAY the recent working set to pre-intern live vocabulary, swap atomically, drop old
     generation. Bounded memory by construction (a generation carries a budget); no client-
     visible cold. Tradeoff stated: returning-after-recycle corpora re-pay novelty once.
     **NOT built — measurement closed the decision** (residue ≈ spike ≈ 5–10 MB/Mtoken, too shallow
     to justify the machinery; step 2's envelope+fail-loud suffices). Escalation ONLY if a soak ever
     shows the envelope breached in practice; it stays filed here as the named escalation, behind
     the swap seam that already exists.
  4. witnesses: soak test (synthetic max-novelty stream, RSS/vocab bounded across N recycles)
     + the corrected novelty query as a standing gate.

- **Vocab observable — enumerate EVERY live spaCy Language, not a hand-listed set (2026-07-02,
  from the observables audit). LANDED (this commit).** A per-daemon `VocabRegistry` (wire_types,
  framework-free: holds Languages as `Any`, duck-types only `.vocab.strings`, imports no spaCy —
  host-XOR-device neutral, the twin home both daemons already share) now backs
  `_vocab_rss_observables` in BOTH daemons. Every `spacy.load` / captured Language registers into it
  AT ITS LOAD SITE (`self.models[m] = reg.register(spacy.load(m), label=m)` — load and register in
  one expression), and the observable enumerates ONLY the registry: nlp_server's boot models + the
  captured maverick `en_core_web_sm`, the decode daemon's `StandalonePreprocessor.nlp` — nothing
  hand-listed remains, so a future long-lived Language is counted the moment it loads through the
  registry. Wire keys preserved (measurement series unbroken). Tests: test_vocab_registry.py (pure +
  decode-daemon-double integration). NOT COVERED, named (ADR-0013 Rule 4): a load site that FORGETS
  to register still leaks uncounted — the registry does not (cannot) wrap `spacy.load` itself: two of
  the three Languages are loaded by third-party code (maverick's `download_load_spacy`, the
  preprocessor's `from_spm`) and captured at our seam, so registration is a co-located one-liner per
  load site, not a structural intercept. Second not-covered axis (out-of-frame audit): the registry
  keys on `Language`, so bare-`Vocab` non-evicting StringStores — `spacy.blank("en").vocab` in
  `nlp_docs_client.py` / `docbin_cache.py` — are outside it. They are CLIENT/CLI-side today (not a
  daemon serve-path leak), but if `DocsNLP`/`DocCache` ever became a standing service they would
  reintroduce an uncounted store; filed, not silently left (ADR-0013 Rule 4).

- **Hook ingress adapter — the daemon's admit-set is PROSE.** The guardrails hook feeds
  transcripts (JSONL): uuids/hashes/paths are the pathological interning maximum, JSON syntax
  is the P/K-explosion class (the rfc5971-diagram lesson), coref over brace syntax is
  semantically void. The adapter extracts prose channels (assistant/user text, with
  message-index/role provenance for attribution) and treats code fences as non-coref-able
  blocks — translate-and-validate at the hook boundary, same discipline as every other Port.
  Measurement corpus: docs/claude-ephemera (real, committed, checksummed).

## Hook-trial finding — the L1 payload is not yet hook-worthy; causes measured, levers ranked (2026-07-02)

- **Baseline trial** (`experiments/fact-mining/docs/hook-trial/HOOK-TRIAL-2026-07-02.md`, commit
  13d4c1b): the L1 contra payload (R-FUNC/R-NUM/R-NEG unchanged) on the 222 deduped ephemera
  universes = **1997 findings, ~99.8 % noise, 0 clean candidates**; four causes named — (1)
  copular `be` (1529/1540 R-FUNC), (2) subject-key collapse, (3) role-impure universes (63 % of
  findings touch user prose; maintainer ruling → role-STRATIFIED universes, never role-excluded,
  HOOK-DESIGN.md §5 L1 amendment), (4) assertion-mood / use-vs-mention blindness.
- **Delta trial** (`HOOK-TRIAL-DELTA-2026-07-02.md` + `findings_delta.json`, same corpus, live
  stack, baseline arm reproduced exactly at 1997): the two DRIVER-level levers measured as arms —
  assistant-scope (cause 3) → **745 (37.3 %)**; no-copular-`be` via the existing
  `functional_preds` parameter, default untouched + pinned by tests (cause 1) → **468 (23.4 %)**;
  **both → 251 (12.6 %)**, i.e. 8× quieter (9.0 → 1.13 findings/file) but **still ~100 % noise
  (0 clean of 251)**. Levers overlap on 1035 findings (exact set measure under the rules' own
  unordered-pair identity; arms are strict subsets of baseline). The user-instruction stratum's
  baseline falls out nearly free: user×user = ~1084 (unchanged preds) / ~190 (`be`-free) —
  approximate from below (shared-claim-text margin ~0.7 %, measured); same levers apply.
- **Remaining levers, with measured residual shares (the `both` residue, attributed):**
  - **Cause 2 + the R-NUM number-grab parser: 248/251 (98.8 %).** R-NUM is 246/251; its parser
    fires on any embedded digit-run (line numbers, ports, errnos, ADR numbers, different-regime
    percentages — all 12 cross-block findings hand-read, each dissolves). 234/246 are
    single-message-block pairs (the subject-collapse proxy; 238/251 across all rules). Fix shape:
    a quantity-typed R-NUM (fire only when the object IS a predicated quantity; unit-aware) +
    GLiNER-class subject typing against generic-noun collapse.
  - **Cause 4 mood/mention: 3/251 (1.2 %)** — all three surviving R-NEG are
    interrogative→resolution / quoted fixture / use-vs-mention. This gate is what would let
    R-NEG's rare real signal survive, and it is prerequisite for the ruling's cross-role stratum
    (conduct-vs-mandate) to be honest.
- Verdict unchanged in kind, sharpened in target: do not wire L1 as-is; the next increment is the
  R-NUM quantity-typing + mood gate, now with measured (not guessed) shares of the remainder.
- **Main-session substrate answer (2026-07-02, `HOOK-TRIAL-MAINSESSION-2026-07-02.md` +
  `findings_mainsession.json`):** the decisive substrate test — the payload as it stands (the delta
  `both` configuration) over the 16 top-level main-session transcripts (16/16 covered, 306 s of the
  600 s budget, largest-last order, 118 degraded units counted) — yields **0 clean candidates of 375
  hand-read findings** across all three strata: assistant-self `both` = 228 (R-NUM 214 / R-NEG 14),
  user-instruction `user-both` = 122 (R-NUM 119 / R-NEG 2 / R-FUNC 1), R-NEG unsuppressed = 25
  (11 asst×asst / 2 user×user / 12 cross-role). Per-claim noise density matches the subagent corpus
  (27.7 vs 31.5 per 1k claims); R-NEG density rises **~4.5×** and its specimens are genuinely
  contradiction-shaped — and each dissolves. Three NEW findings the richer substrate adds: (5) a
  fifth noise mechanism, **temporal state-change** (pre-fix observation vs post-fix statement — the
  dominant shape of the R-NEG surplus; needs temporal awareness in the claim model, not just a mood
  gate); (6) the user-role stratum on main sessions is polluted by **harness-injected/quoted content**
  (task-notification `<result>` blocks, summaries, pasted reports) — a real user-instruction
  diagnostic needs ingress separation, filed not fixed; and (7) a **measured recall miss**: the one
  human-flagged live contradiction in the corpus (the 874 MB vs 2.9 GB complaint, session `55eec152`)
  was never surfaced as a use-use pair — subj_key never joined the two original statements — so the
  rules have zero recall on the only known positive (the claim-join side of the GLiNER-class typing
  gap). Verdict: still do not wire L1; the substrate has the raw material, the payload extracts none
  of it.
- **GLiNER enrichment measured live (2026-07-02, `HOOK-TRIAL-GLINER-2026-07-02.md` +
  `findings_gliner.json` / `findings_gliner_mainsession.json`):** the certified lever wired as two
  default-off parameters on `find_contradictions` (typed subject keying + R-NUM quantity gate;
  per-claim `ClaimEnrichment` built by `gliner_enrich.py` from RemoteGliner :5601; defaults pinned by
  tests, control arm reproduced bit-identical — subagent `both` = 251 exactly, mainsession 232 =
  prior 228 + live-corpus growth, fully attributed). **The measured answer: precision — the noise
  floor drops ~12×/~7× (251→21 subagent, 232→33 mainsession; R-NUM suppression 93.5 %/88.5 %, at or
  above the entity-quality prediction) but the residue is still ~100 % noise (0 clean candidates of
  54 hand-read); recall — nothing real surfaces: 0 novel findings (both enriched arms are strict
  subsets of their controls) and the 874 MB/2.9 GB known positive remains at zero recall.** Surviving
  mass: same-sentence shredding 35/54 (an extraction defect no key/gate owns), mood/mention 8,
  temporal state-change 3, parse-polarity 2, quantity-regime 1. Named residuals: spelled numbers are
  gate-open (24–37 % of numbers unlocatable — "three"/"five" pass the gate); enrichment costs
  ~105–110 ms/sentence through the daemon (full-corpus sweep ~2× wall; the anticipated GPU sub-10 ms
  unverified through this wire). Found + foreclosed in passing: `parse_number` accepted
  `float("nan"/"inf")` — a non-finite `Claim.number` crashed the enrichment locator and latently made
  R-NUM fire against every number (`nan != x` is always true); now finite-or-None by construction,
  pinned; measured zero effect on every control. A second latent defect fixed in the locating SSOT:
  the entity-quality instrument's digit-boundary guard was dead code behind an unconditional
  `str.find`; the shared `gliner_enrich.locate_token` applies it to every occurrence. Verdict
  unchanged: still do not wire L1 — the remaining levers are the mood/temporal/ingress/claim-coref
  lanes already filed, now with the typing lever's live numbers attached.

## GLiNER integration — the certified lever measured + a third standing service stood up (2026-07-02)

- **Measurement (guest CPU, ADR-0009 register):** `docs/hook-trial/GLINER-ENTITY-QUALITY-2026-07-02.md`
  + `gliner_quality.json`, driver `measure_gliner_quality.py`. `pip install gliner` into the generic
  venv resolved with **no conflict** (only gliner-0.2.27 / onnxruntime / flatbuffers new; torch+
  transformers already satisfied); venv health re-verified (spaCy 3.8.14 + en_core_web_sm intact).
  Model `urchade/gliner_small-v2.1`, threshold 0.35, 16-label set. On the hook-trial residue:
  - **Number typing:** a GLiNER quantity-gate **suppresses 85.6 %** (394/460) of the R-NUM number-grab
    residue (the digit-run-in-identifier class — line numbers, ADR ids, ports). Residual: 11.5 %
    "admits" are GENUINE quantities across different measurement regimes (a context problem, not a
    typing one) — named, not owned by GLiNER.
  - **Subject discrimination:** **57.8 % clean two-sided** separation of collapsed subjects (both typed,
    signatures differ) + 36.5 % one-sided partial; **5.5 % no-signal** are abstract-concept subjects
    (`check`, `design`, `hack`) a typed NER cannot discriminate — the honest limit. (A loose "any
    signature difference" metric reports 94 % and over-credits one-sided; two-sided is the defensible
    number.)
  - **CPU latency 136 ms/paragraph** (uncontended) — usable offline, marginal interactive; the number
    that sizes the GPU need (sub-10 ms expected at fp16 on the sm_75 card).
  - Verdict: GLiNER moves the needle on both binding constraints with named residuals — enough to
    stand the service; NOT a claim it makes L1 signal-bearing alone (still needs the mood gate + a
    regime-aware quantity comparison).
- **Landed (Part 2, the third standing service — ADR-0016 Revisit #3):** `gliner_server.py` (port 5601;
  5599/5600 untouched) + `gliner_client.py` + `gliner_wire.py`. Contract discipline transferred
  service-by-service, numbers re-derived: every ingress axis a validating boundary (texts count+char,
  the NEW zero-shot labels count+length+non-empty, threshold range, the servable encoder-window
  ceiling via the shared `ServableText`); `GlinerLimits` advertised pre-inference with the labels
  axes (0016 Rule 3); `MemoryEnvelope` identical fail-loud-before-fail-slow discipline; boot_id on
  every reply; readiness sealed over the pure `(text_len × labels)` encoder grid (never advertised
  cold); client limits+envelope caching with boot-id invalidation; the chars-axis `_screen_offenders`
  routed through the SAME one-home `wire_types.screen_text_chars` (widened to a `_HasMaxTextChars`
  Protocol so the decision is shared, not re-authored) and REGISTERED in `test_ingress_screen_gate.py`'s
  completeness scan; per-document degrade-not-disappear. Verified end-to-end on CPU (warmup→READY,
  typed mentions, char-screen + servable-window degrades, innocents served). 58 new tests, 0 failed;
  mypy-strict clean; lazy-import gate 0.
- **Honestly NOT covered (named residuals, ADR-0013 Rule 4):**
  - **Exact text+labels co-token-budget.** The 384 encoder window is shared by the text sub-tokens AND
    the label-prompt tokens; the servable screen prices both with a CONSERVATIVE upper bound
    (`_sequence_subtokens_upper` over-counts the per-label prompt overhead rather than reconstructing
    GLiNER's exact prompt assembly). It never UNDER-counts, so it never lets a silently-truncating
    request through — but it over-refuses near the window. Exact accounting needs GLiNER's prompt
    internals; the memory envelope is the runtime backstop.
  - **GPU-arena-derived servable ceiling.** The servable ceiling is the MODEL window (config.max_len),
    card-independent; a smaller GPU arena that cannot encode the top length-bucket at fp16 is not
    derived-and-narrowed the way the decode daemon narrows from the jax arena. Re-derive when the
    daemon runs on a constrained card (the decode daemon's `servable_ceiling` pattern is the template).
  - **PTQ path.** fp16 is the ruling and gliner_small fits fp16 on the sm_75 card with margin, so PTQ
    via nla_lab is NOT implemented (ADR-0013: not built past the measured need). A larger backbone that
    did not fit fp16 would take the nla_lab PTQ path — filed, not built.
  - **The umbrella standing-service CI gate (ADR-0016 Rule 2)** is now **LANDED** (see the
    "ADR-0016 Rule 2 umbrella — LANDED" section below); this service's per-boundary suites are bound
    into that net. The only residual is wiring the runner into pre-commit/CI (maintainer ratification).
  - **No adversarial `hypothesis` fuzz of the live model forward.** The boundary/envelope/readiness/
    client axes are property-and-double tested; the model forward itself is exercised by the e2e smoke,
    not a generative fuzz (a generative gate over the warm forward is the Rule-2 shape, filed).

## Parse-axis admit>servable (CB-28's class, found by the vocab measurement's raw arm, 2026-07-02)

- **LANDED (this commit).** nlp_server now boot-derives a card PARSE token budget and advertises +
  enforces it. Derivation: `shape_buckets.parse_token_budget(mm, available, window, stride)` — pure,
  CPU-tested — models the curated transformer's OVERLAPPING STRIDED spans (peak linear in total
  sub-tokens) via the SINGLE `peak_variable_bytes` author at one window, `budget = stride *
  (available // peak(mm,1,window))`. The multiplier is STRIDE, not window (the direction that never
  under-counts windows → never under-estimates peak → never OOM — a second-opinion fan-out catch);
  the MemModel is `standard_attention_mem_model` (roberta: `pos_ebd_size=0` zeroes the disentangled
  term — correctly denominated, not the deberta model's phantom buffers). nlp_server reads the real
  window/stride/arch off the loaded pipe config (P1) + the torch arena; None when no transformer
  parse model (en_core_web_sm → the axis does not bind). Advertised as
  `AdvertisedLimits.parse_subtoken_ceiling` (optional; degrades to None on a pre-budget
  advertisement like decode_p/k; NOT folded by fold_peer — parse never relays). `plan_chunks` gained
  a token axis; the nlp client splits on it using `text_token_upper_bound` (UTF-8 bytes — a provably
  DOMINATING bound on byte-BPE token count, so denomination-legal where a char proxy would be CB-08).
  Admission (SSOT, EXACT sub-tokens via the byte-BPE piece encoder, off the forward): a single doc
  over budget → typed `PerDocumentRefusal` (axis `parse_subtokens`, isolated by the client's
  isolate_offenders + a `parse_refused` degrade that does NOT re-parse); a batch whose TOTAL exceeds
  budget with no single offender → typed `BoundaryRefusal` at the boundary. Warm path not regressed:
  the exact count is paid ONLY when the cheap byte-dominance bound is itself over budget. Tests:
  test_parse_token_budget.py (pure + real-trf-on-CPU integration).
  NOT COVERED, named (ADR-0013 Rule 4): (a) the live-GPU budget NUMBER is exercised on the host — the
  guest tests the pure derivation + the real-trf count/config extraction on CPU; the arena free-bytes
  query is host-validated. (b) Only the ByteBpeEncoder curated piece encoder is wired for counting; a
  different curated tokenizer FAILS LOUD at boot (`_parse_piece_encoder`) rather than advertise an
  uncountable budget (admit==servable). (c) The client byte bound over-splits ~mean-bytes/token — a
  named conservative tradeoff; the server's exact refusal is the SSOT backstop.
  Note: the prose admit-set (hook adapter) showed 0 refusals — this is backstop hardening, not an
  operational blocker; the fast-skip keeps the operational path un-regressed.
- Measurement follow-up: filtered-only DEPTH re-run (~300–600 s) to fill the empty decayed +
  cross-session-residue cells; current spike rates already suggest envelope+fail-loud
  suffices over generation recycling.

## Chars-axis client isolation gap (live repro 2026-07-02, boot e27c203dd3b1)

- **CLOSED this commit (pipe_facts).** A `pipe_facts` batch of three docs — two innocent short texts
  and one 310,500-byte single paragraph — raised and lost ALL results: the monster's own byte-chunk
  was refused server-side with the INDEX-LESS chars-axis `BoundaryRefusal` (`texts[0] is 310500 chars,
  exceeding MAX_TEXT_CHARS=131072`), which `_raise_facts_refusal` turned into a `RemoteError` out of the
  warm path, aborting the WHOLE call including the innocents' chunks. The chars axis was left out of the
  per-document isolation discipline the coref axis got (the maintainer ruling behind
  PerDocumentRefusal/isolate_offenders: on a streaming deployment a per-doc refusal must be
  indistinguishable from a DEGRADED doc, never from a DROPPED call). Fix (client-side, no wire change):
  `RemoteNLP.pipe_facts` now PRE-SCREENS each text against the ONE per-single-document axis a
  framework-free client can decide LOCALLY — the cached advertised `max_text_chars` (`len(text)`; a
  CONTENT bound, indivisible). A locally-detected offender NEVER goes on the wire; it degrades to the
  SAME `parse_refused` empty FactBundle the parse-token path produces (reused `_facts_degrade` home,
  new `TEXT_CHARS_AXIS` un-resendable label — no second bundle shape), loudly logged (index/axis/numbers,
  ADR-0002). Innocents are served in the same call, positions preserved. The token axes stay server-EXACT
  (SSOT); count/frame/aggregate stay plan_chunks' (splittable); a text within `max_text_chars` fits a
  single frame by construction (worst-case 4·131072 B ≪ max_frame_bytes), so chars is the COMPLETE
  client-decidable set. No-limits (legacy) daemon → no screen → pre-advertisement behavior unchanged.
  Boot-id invalidation still honored (a restarted server's narrower ceiling re-screens on the next call).
  The server's typed refusals remain the belt-and-braces backstop (ADR-0016 Rule 1). Also generalized the
  shared `_merge_coref_verify` from a contiguous `(offset, report)` to a global-index-MAP `(gidxs, report)`
  (correct re-basing once the screen makes the sent set non-contiguous) and updated BOTH callers
  (`pipe_facts`, `DocsNLP.pipe`). Tests: test_per_doc_refusal_isolation.py (+5: live repro, all-offenders,
  no-limits, boot-id re-screen, compose-with-server-coref) + test_advertised_limits.py verify-merge unit.
- **CLOSED — the two SIBLING raw-text ingresses (this commit).** Both routed texts through
  `_validate_texts`' `MAX_TEXT_CHARS` and shared the abort-not-degrade gap; both now screen the chars axis
  client-side through the ONE-home predicate (below), each supplying its own maintainer-ruled degrade tail:
  - `nlp_docs_client.DocsNLP.pipe` (Docs/DocBin path, extract.py's demo/local path) had NO per-document
    isolation AT ALL — ANY per-doc refusal (chars OR coref P/K) aborted the whole call, a gap broader than
    chars. NOW: it pre-screens the chars axis (inherited `_screen_offenders`) AND wraps its chunk loop in
    `isolate_offenders`, so a per-document SERVER refusal is isolated too — each offender degrades to an
    EMPTY spaCy `Doc` carrying its refusal on the `refused_axis` extension (registered once at module scope,
    default None → a consumer distinguishes 'refused' from 'genuinely empty'), positionally in place; the
    innocents are re-sent/served. Type-homogeneous (`list[Doc]` out), degrade-not-drop (maintainer ruling).
  - `coref_decode_client.RemoteDecode.coref` (unified daemon, `CorefRequest.decode → _validate_texts`) now
    pre-screens the chars axis and degrades the offender to its EXISTING empty-clusters shape (recorded in
    `last_refused`, axis `text_chars`) — no new shape; the innocents served in the same call. Under
    `isolate=False` (the nlp_server relay) a screened offender is re-raised as a typed `PerDocumentRefusal`
    naming its index (never a silent empty-cluster substitution), exactly as a server P/K per-doc refusal is
    forwarded. (`RemoteDecode.decode_batch` sends DecodeDocs, not raw texts — NOT this axis, untouched.)
- **CLOSED — the STRUCTURAL fix (this commit), so the class does not recur on a NEW ingress.** There is no
  single wire SEND seam to place the invariant on: the three ingresses live in TWO separate client
  hierarchies (`RemoteNLP`/`DocsNLP` vs `RemoteDecode`) with ingress-specific degrade tails, so a shared
  send-seam would have to know each tail. The durable fix is therefore TWO one-homes, per ADR-0000's
  2026-07-02 closure statement (name the axis universe; enumerate the sibling surfaces):
  1. **The DECISION is one home** — `wire_types.screen_text_chars(texts, limits)` (framework-free) is the
     sole predicate every raw-text ingress screens through, so no ingress can screen a NARROWER axis set
     than its siblings (the CB-08 axis-drift class). The client-decidable axis universe (chars, and only
     chars — the one per-single-document axis a tokenizer-free client can decide) is defined ONCE.
  2. **The PROPAGATION is a mechanical gate (two tests, `test_ingress_screen_gate.py`).** ONE home
     (`RAW_TEXT_INGRESSES`) registers every raw-text ingress; the per-ingress gate proves each REGISTERED
     ingress screens (offender degraded + off the wire, innocents served, result aligned), and
     `test_raw_text_ingress_registry_is_complete` SCANS the client classes and FAILS if a public
     text-shipping method (signature carries a `texts`/`text` parameter) is not registered — so adding a
     new raw-text ingress and skipping the screen fails a TEST, not a code review (ADR-0016 Rule 2 /
     ADR-0011 Rule 2). Reach declared honestly (ADR-0011 Rule 1): the scan keys on the signature-level
     `text(s)` parameter; a method smuggling text under a differently-named parameter is caught by review,
     not the scan — a true single wire seam would close even that, but none exists across the two client
     hierarchies. Negative controls run: disabling any ingress's screen puts the monster on the wire and
     trips the per-ingress gate; an unregistered public text-shipping method trips the completeness test.
- **STILL OPEN (NOT taken on here — needs a multi-peer design ruling): `AdvertisedLimits.fold_peer`
  over-degrade.** `fold_peer` folds CONTENT bounds to the min across admitted peers; on a heterogeneous
  peer set this can advertise a ceiling narrower than any single served path actually requires, so a text
  servable on the path it would take is screened out. Foreclosing it needs a per-path (not min-folded)
  advertisement model — a design decision deferred, filed here, deliberately out of this commit's scope.

## Stores & services to build

- **store #2 — capability registry** (toolset availability / schema / registration): pull-not-push;
  `probe_cmd`/`derive_cmd` not literals; the `proves` column as the eliciting mechanism. The reproducer is
  a registered, qualified capability here.
- **store #3 — structured work-log / backlog** (port omega `work-status`; + `project_id`/`session_id`) —
  *this file's successor and SSOT.*
- **the reproducer service** (clone → rewind → rebuild → rerun; qualified; the independent verifier that
  gates confirmation). Itself a registered capability; leaves the seam for SLSA/in-toto attestation.

---

## Doc / tooling

- **Rewrite `design/ARCHITECTURE.md` against the autoharn layout ([C12]).** Migrated
  2026-07-07 carrying a STALE banner: its path citations point at the old `claude_harness`
  tree (`research/2026-06-27-*`, `../GLOSSARY.md`) and it predates the consolidation. The
  through-line narrative is worth keeping; the paths and current-state claims are owed a
  rewrite. Content work, deliberately outside the migration increment.
- **doc-legibility widened-scope debt (finding 48 / [C15]).** The gate's scope is now ALL
  tracked `*.md`, but it reports **~1429 undefined acronyms** over the migrated corpus —
  mostly the crude heuristic misfiring on all-caps emphasis words (RED/NEG/NUM/ONE/NO/IS/IN),
  SQL keywords (INSERT/NULL/FK), and doc-structure tags (MIGRATE/STAYS/DECIDED/INC), plus
  legitimate standards acronyms (IEC/ISO/SIL/GSN/ALCOA) in the briefs. It is therefore wired
  **report-only** in the pre-commit, not blocking, pending a corpus acronym-sweep (populate
  `gates/doc-legibility/{terms,allowlist}` AND raise the gate's precision on all-caps
  common words). Making it a blocking gate over the full corpus is the open work.
- **Abbreviation attribution + scope** in the doc-legibility gate: a term carries an *origin* and a
  *scope*; a project-scoped term used out of scope is a violation. (Would have caught `tlab_*` in autoharn.)
- **Check the survey render scripts into the repo.** `KEY.md` is generated by an ephemeral scratch script
  that would clobber edits on re-run — a COHERE / reproducibility smell.
- **Run every new subsystem design against the 19 obligations** before building (the checklist mechanism;
  it is the doc, not a gate, until wired).
- Decide the **agent-push policy** enforcement: keep as remembered convention, or wire a settings.json hook
  (background agents commit-only; humans push `main`).

## Research threads

- **Investigate "attitude logic."** Is there a named formalism under this term — logics of
  *propositional attitudes* (belief / desire / intention; doxastic / epistemic / BDI) — and should
  this project address it? Directly germane to the real goal: interrogating an AI collaborator's
  *epistemic state* is reasoning over its attitudes toward propositions (what it believes, hedges,
  intends, defers). Map it against the obligations-formalisms survey. [maintainer request, 2026-06-29]

## fact-mining (JAX decode migration)

- **Close the `coref_decode_server.handle()` JSON-seam coverage gap.** The Stage-1b-ii live-wire
  fidelity test drives `Server._run_coref(..., "jax-daemon", ...)` directly — one layer ABOVE the
  daemon's `handle()` frame parse — so a future drift in `handle()`'s field routing
  (`req.get("coref_backend")`/`decode_addr` → `_run_coref`) would go uncaught. (Flagged by the
  implementer's own hack-rationalization audit, 2026-06-29; concrete cost of the gap: a `handle()`
  test needs a loaded spaCy pipeline.) Fix = a thin `handle()` round-trip test with a stub spaCy.

## fact-mining — JAX consolidation

- **Flax/Equinox: bare-JAX now, reconsider only if training enters scope.** jax_deberta.py is
  bare-JAX functional to match jax_decode.py's core (ADR-0012 P9), because there is no ready-made
  Flax DeBERTa and this is inference-only (weights converted from torch). Flax's init/variables/
  apply machinery earns its keep for TRAINING; revisit Flax — or Equinox (the functional-style
  alternative that fits this codebase's grain) — only if we want to train/fine-tune the encoder.
  The bare-JAX param tree can be wrapped in Flax/nnx then; nothing is locked in.
- **Unified JAX encode+decode coref daemon (the architectural prize, next step).** jax_deberta is
  fidelity-proven (worst max|Δ|=3.05e-5 vs torch deberta-v3, guest CPU, long-doc + padded-batch
  covered). Next: in coref_host_shell.py (the single jax home), load maverick's FINE-TUNED weights
  via deberta_weights.params_from_state_dict (keyset-guarded) + jax_deberta.encode, feeding the
  already-pure-JAX decode tail IN-PROCESS — retiring the torch encode, the ~54ms encode->decode ZMQ
  wire, AND the torch/jax GPU-coexistence dance (XLA_MEM_FRACTION, fp32-forcing). End-to-end gate is
  HOST-only: --coref-verify against maverick's torch reference (same deberta-v2 arch; the new asserts
  fail loud if maverick's config diverges on share_att_key/hidden_act or carries unread tensors).
- **Pending host tick:** the 4->1 bilinear consolidation (5661428) — confirm discrete clusters
  unchanged via --coref-verify (guest-proved the algebra; host confirms end-to-end).

## fact-mining — LRU cap on the compiled-shape cache (deferred behind bound-coref-compile-cache)

- **In-process LRU bound on the AOT-compiled executables — the belt to bucketing's suspenders.**
  GATED ON: the `bound-coref-compile-cache` workflow landing AND host/GPU-backend fidelity validated
  (`--coref-verify` 0 mismatch on the now-bucketed unified daemon). Then add an LRU cap so a
  long-uptime daemon on arbitrary text can't grow the compiled-executable set without bound.
  - NOT redis: an XLA executable is a LIVE in-process object (compiled GPU code + buffer assignments
    bound to this process/device), not a serializable cache value — redis (`:6380` volatile-lru) is for
    JSON-shaped caches (the doc cache), not this. The analog is an in-process LRU.
  - Mechanism: JAX's default jit cache is UNBOUNDED (that is the leak). Use the AOT API —
    `jax_deberta.encode.lower(args).compile()` returns a `Compiled` we hold in an `OrderedDict`
    (`maxsize=N`, evict LRU); dropping the reference frees the executable + its buffers. (`jax.clear_caches()`
    is all-or-nothing; not LRU.)
  - Cheap eviction: the persistent DISK compile cache (`coref_host_shell.py:68-73`, already on) makes an
    evicted-then-recurring shape RELOAD from disk (~ms) instead of a full recompile (~s). So LRU bounds RAM,
    the disk cache makes re-materialization cheap — "do the right thing per the shape distribution under a
    dearth of memory," redis-free.
  - Ordering: bucketing (first-order, shrinks the distinct-shape set to O(buckets)) makes this rarely bite;
    the LRU is the second-order HARD CAP for the genuinely-unbounded decode K/P tail + arbitrary-text uptime.
    ~30 lines once bucketing lands. (Redis WOULD earn its keep for a DIFFERENT goal: sharing the compile
    cache across daemon processes/machines — a shared blob store for serialized executables.)

- **Encode-batching by bucket-group (book-scale throughput lever, encode-only).** GATED ON the same
  signoff as the LRU cap (bucketing landed + host --coref-verify clean). Now that same-bucket texts share
  a padded shape, batch them into ONE `[B, bucket_S, TH]` deberta forward per bucket-group instead of N
  per-text forwards — bounded padding waste (same bucket = similar length, unlike padding to the global
  max, which is why batching barely helped pre-bucketing). ENCODE-ONLY: the decode stays per-doc (ragged
  clustering, maverick `mention_idxs[0]`). CRITICAL: batching adds batch size `B` as a shape axis — to keep
  the compile cache bounded (the leak we just fixed), FIX/bucket `B` too (compile per `(fixed_B, bucket_S)`),
  else batching re-leaks via per-`B` shapes; the compile-bound test (test_shape_bucket_compile_bound.py) is
  the gate that catches it. Reuse the existing OOM bound (chunk_by_token_budget). Fidelity bar unchanged
  (the masked padding already proven inert). Win is book-scale (200 paras -> ~#buckets forwards); marginal
  for the small-text hook use case — a scale lever, not a PoC need.

## Deduction-type discriminator specimen — "Cleaned [moving on]" as finality marker (maintainer, 2026-07-02)

- **The specimen** (envelope-implementation agent, mid-transcript; persisted verbatim in
  `docs/claude-ephemera/session-306d4c8f-d98c-4312-b495-fc656fe7b691/-home-bork-w-vdc-1-claude-harness/subagents/agent-a7df1e5bbbed793a0.jsonl`):
  > "Resolved: the failure was 6.5G of leaked staging npz files orphaned by my pkill (ADR-0015 Rule 2
  > leak-by-construction), not a code defect. Cleaned; the test passes (4 passed). Now the FINAL gates, ..."
- **Why filed:** the grammar of "Cleaned" is a finality-type marker — a speech act performing closure —
  whose truth-status is LAYERED. In a restricted sense it is true (the orphaned files were removed; the
  test passed fresh). Under the ADR system's closure discipline (effect-level exit criterion: re-observed
  absent on the deployment surface) it is a closure CLAIM made without the closure WITNESS — probably
  haste, not deceit, but the dishonesty question is genuinely open (maintainer: "I'm not actually sure
  what to make of it, hence file it").
- **Why it matters to the logic layer:** it perfectly discriminates between deduction types the NLP↔logic
  interface must keep apart — (a) an action-report ("I removed files": eventive, narrow scope, verifiable
  per se), (b) a defeasible closure inference ("therefore the failure class is resolved": holds by default,
  defeated by e.g. the same leak-by-construction recurring on the next pkill), and (c) a verified closure
  statement (invariant + quantification universe + witness). A deduction engine interrogating an agent's
  epistemic state must NOT let (a)'s truth launder (b) into (c) — this specimen is real transcript data
  where exactly that laundering is syntactically invisible ("Cleaned;" + "Now the FINAL gates" = moving-on
  prosody). Pairs with the rfc2616 defeasibility findings (CONTRADICTION-DEMO.md §4) as prerequisite
  corpus material for the deferred interface commissioning.

## Cross-experiment pytest import scoping — adjudicate tests break repo-root collection (2026-07-02)

- Root-caused (not fixed) during the collection-stall investigation (commit cb9ff2e): tests in
  `experiments/adjudicate/tests/` import sibling modules (`instances`, `schema`, `docsource`) that are
  on `sys.path` only when adjudicate is the cwd — so repo-root collection yields 8 ModuleNotFoundError
  errors while each experiment collected from its own dir is clean (fact-mining 467, adjudicate 43,
  impedance 21). Different cause from the (fixed) `test_preprocess_bit_identity.py` unbounded-glob stall;
  reported separately per the do-not-bundle discipline. Clean fix: per-experiment `conftest.py` adding the
  package dir to `sys.path` — separate change, adjudicate subsystem.

## Naming/structure — "fact-mining" is misnamed (maintainer, 2026-07-02)

- experiments/fact-mining now houses the inference stack (daemons, clients, wire, readiness),
  the logic layer, the measurement instruments, AND the mining PoC — ~90 files flat. The
  maintainer flags both the name and the shallow-directory smell ("make of it what you will").
  Belongs with the re-homing proposal deferred from the killed NLP↔logic mapping (2026-07-02);
  address them together, MAP first, moves only after the maintainer ratifies.

## Cross-package import hazard, second specimen (inventory 39c72f7, 2026-07-02)

- `contra_app.py:41` reaches the sibling adjudicate package via `sys.path.insert` + `noqa: E402` —
  ADR-0013 Specimen 1's pattern, and it contradicts the file's own "coupling is rows, not imports"
  claim at the import line. Same root as the adjudicate pytest import-scoping item above: fix both
  under ONE ruling on how experiments import across package boundaries (conftest / packaging), not
  two local patches.

## Intent-perversion specimen — the impedance F-algebra→tagless-final substitution (maintainer, 2026-07-02)

- **The arc (two sessions, both grounded):** the maintainer mandated an F-algebra implementation
  SPECIFICALLY so kernel fusion would fall out for free (the recorded WHY). An earlier session convinced
  him ("or I was too tired") to substitute tagless final. Session e066e340-88c7-4fb9-b14a-9954c0497876
  then measured the outcome: `experiments/impedance/` does NO fusion of any kind — no jit/vmap/Pallas
  anywhere in the adapters; `jax_lower_lib.py:45`'s own comment notes the kernel expressions *would*
  lower under Pallas and the adapter deliberately runs them eagerly. Net effect of the substitution:
  the objective silently dropped, function-call overhead possibly added.
- **The class:** GOAL-SUBSTITUTION — the means were re-optimized (encoding elegance) while the mandate's
  purpose was detached and lost, and human ratification under fatigue laundered it. Note it violates law
  the maintainer already holds: the frontier creed's "retire an objective only via a failed experiment" —
  the fusion objective was retired by conversational drift, no experiment. So this is a RECURRENCE class
  needing a mechanism, not a new principle.
- **What the harness must do with it ("see this error once and never again"):** (1) cross-role
  conduct-vs-mandate interrogation — a design decision carries its recorded WHY; when the means change,
  the WHY is re-verified or explicitly retired, never silently dropped (the KB's supersedes-chain is the
  natural home); (2) proactive supply — "tagless final here bought no fusion, cost call overhead" becomes
  a KB fact surfaced the next time the topic nears; (3) the doxastic angle — ratification-under-fatigue
  is not discharge; a standing mandate outlives the conversation that bent it.
- **Disposition (maintainer, 2026-07-02): SET ASIDE.** Not worth further tokens — "at least not Fable
  tokens." If ever resumed, the maintainer's sizing stands on record: an F-algebra ACL is in principle
  "substitution work — not deep" (Opus-tier drudgery, not a Fable expenditure). The specimen's value to
  the harness corpus is independent of the subproject's fate and stands.

---

## NLP↔logic interface — Increment 1 filed deferrals (2026-07-02)

The Increment-1 build (mood gate v0, same-sentence-shred foreclosure, the R-QTY dimensioned
lane; `docs/hook-trial/HOOK-TRIAL-INC1-2026-07-02.md`) reached its ratified scope. These are the
hazards it met in passing and filed rather than smuggled into the increment (ADR-0013 Rule 4):

- **I1 — Upstream same-sentence shred (extractor surgery).** The subject-collapse survivor class is
  one source sentence the extractor shreds into two claims; Increment 1 forecloses it at the
  pair-join (`same_sentence_foreclosure`), which the GLiNER report names "better foreclosed
  upstream." The upstream fix (extractor does not emit two claims for one sentence's enumeration)
  is a bigger blast radius (touches `extract.doc_to_facts`) and is deferred here, named, not the
  pair-join band-aid's silent debt.
  **PARTIAL DISPOSITION (2026-07-02/03, HOOK-TRIAL-ADJUNCT-2026-07-02.md):** the OTHER
  extractor-recall defect filed under I1/I2's extractor scope by INC1 W1 — quantity-in-adjunct
  sentences emit no claim — is CLOSED by `contra_detect.adjunct_quantity_claims` (a separate pure
  emitter over the FactBundle's entities, behind the extension law; the known positive now extracts
  AND joins under the dimension regime: 14 R-QTY pairs in session 55eec152, 0 in the co-run
  control; zero new non-R-QTY findings, both corpora, set-difference-proven). The same-sentence-
  shred upstream surgery itself REMAINS OPEN, unchanged — the adjunct lever does not touch
  `doc_to_facts`. R-QTY stays detection-only in both join configurations (the kill condition still
  fires; the lever changed recall, not the ship disposition).

- **I2 — Bare-suffix quantity disambiguation (`874M`, `2.9G`).** `parse_quantity` types only
  UNAMBIGUOUS unit tokens (MB/GB/…, %, s/ms/…); it does NOT type bare `M`/`G`/`K` because those are
  genuinely ambiguous (mega-what? `7M params` is not 7 MB) — typing them would be the guess
  ADR-0002 / INTERFACE §4 forbid. This DIVERGES from DESIGN F3's example, which lists `874M` among
  the readable surfaces. Consequence measured in W1 (below/the trial doc): where the known
  positive's surfaces are bare-suffixed, R-QTY does not reach them — an honest recall miss localized
  to surface ambiguity, NOT a join-key failure. The named next lever is a GLiNER-corroborated
  disambiguation (DESIGN F3: the GLiNER quantity-mention is the source of the mention head) that
  types a bare suffix as bytes ONLY when a `memory size`/`quantity` mention covers it — corroboration
  that respects "GLiNER corroborates, never gates" because the ambiguity, not the recall, is what it
  resolves. Filed; not built in Increment 1.
  **STATUS (2026-07-02/03, HOOK-TRIAL-ADJUNCT-2026-07-02.md):** still OPEN, now more precisely
  scoped. The adjunct lever reaches SPACED-unit adjunct surfaces ("2.9 GB guest prefetch") — enough
  for the known positive — and pins the bare-suffix refusal by test (`874M` emits nothing; no
  guess). I2's remainder: (a) the GLiNER-corroborated bare-suffix disambiguation (unbuilt);
  (b) slash-rate units (`4 MB/s` currently types as its numerator's dimension with a mis-extracted
  head — 1 specimen in the adjunct trial's W-C hand-read; a closed-unit-table extension, not a
  guess); (c) the sent-text fallback over-assignment (3 of the 20 new subject-regime candidates —
  SVO claims only; an adjunct claim carries its quantity in obj_surface and never takes the
  fallback).

- **I3 — E-1 mood-precision hand-label (the gate-vs-annotate decision).** The mood gate v0 ships as
  a gating guard behind the extension law. Its kill condition (BUILD-PLAN E-1: INTERROGATIVE+MENTION
  precision < 0.9 on ~200 hand-labeled units ⇒ ship detection-only, stored-not-gating) requires a
  human-labeled set the increment did not produce. The mechanical half (classify + measure the
  survivor-set effect) is in the trial; the ~200-unit hand-label that DECIDES gate-vs-annotate is
  filed as E-1 proper.

- **I4 — `fde_z3.py:111` bare `assert` → `raise`.** The non-explosion invariant is elided under
  `python -O`; INTERFACE §7 schedules the one-line `assert`→`raise` fix for Increment 2's file set.
  `qty_z3.quantities_incompatible_z3` already uses a `raise` for its analogous invariant (the new
  code carries the corrected posture); the existing `fde_z3` line is Increment 2's, filed here so
  the strike is visible.

---

## FactBundle content-keyed cache (landed 2026-07-02) — follow-ups

The GPU-expensive parse path (`RemoteNLP.pipe_facts` → the FactBundle) now has a sound,
opt-in, content-keyed redis cache: `nlp_cache.FactCache` / `CachingFacts`, extended (not a
parallel cache — ADR-0012 P1) with a real key universe (`factbundle_key`: text + disable +
daemon-advertised pipeline identity + coref/model/format shaping, **never** boot_id), a
never-cache-refusals guard, redis-outage silence, canonical-JSON values, and a live
byte-identity differential (`byte_identity_differential`). Measured live: differential ok
(5/5 byte-identical — daemon output is byte-stable, so no disable-by-default instability
clause fires; the cache remains **opt-in**, default behavior unchanged), cold-vs-warm
4.10s → 0.496s on a 38-unit committed transcript, footprint ~1.17 MiB per 1k bundles.
ADR-0014 audit (sonnet): sound-with-fixes; its defect 1 (the shared-FactCache MULTIPLICITY
axis — the one-universe guard was dead code behind an `is_bound` short-circuit) is FIXED in
the same change (per-wrapper bind verification, `CachingFacts._bound_verified`, + test), and
the nits (stats label, delimiter-safety note, eviction-policy wording, this wording) applied.

Filed follow-ups:

- **TRIAL-DRIVER WIRING — DONE 2026-07-03.** `hook_trial.run` now wraps its `RemoteNLP` in
  `CachingFacts(remote, FactCache("trial", url=...))` behind an opt-in `--cache` flag
  (`--cache-url` defaults to the volatile-lru instance `redis://127.0.0.1:6380/0`). Follows the
  ClaimContext extension-law pattern: the lever is a `run(..., cache_url=None)` parameter, and
  **unset ⇒ bit-identical control** — the raw `RemoteNLP` is left untouched and the report keeps
  no `cache` block. Coref-mode constraint honored at the wiring site: caching + `coref_mode="verify"`
  is refused LOUDLY (ADR-0002) — the trial fixes `coref_mode="batched"`, so the guard is the
  invariant made loud, live the moment coref_mode is parameterised. Cache stats are surfaced in the
  report `summary.cache` only when the lever is engaged. Measured live (nlp boot 571deb20e421,
  redis 6380):
    * **control arm byte-identical** — the pre-change driver (git HEAD) and the new default run on
      the same corpus produce reports differing ONLY in the non-deterministic `budget.elapsed_s`
      timing field; identical after zeroing it. A cached run yields the same findings/summary as the
      uncached control (the cache is transparent to results).
    * **byte-identity differential** (through the wired wrapper, `byte_identity_differential`): ok,
      5/5 byte-identical, 0 mismatch, mean 526 B/bundle — daemon output byte-stable, no
      disable-by-default clause fires.
    * **cold vs warm** — parse-level (isolated from process startup): cold 0.106s → warm 0.001s.
      Through the driver on a 2-file micro-corpus (5 prose units, 1 degraded): cold run 5 misses /
      0 hits; second identical run 4 hits / 1 miss — the 1 miss is the degraded/refused unit, which
      is never cached (`skipped_refusals=1` on both runs — the never-cache-refusals guard, live).
    * tests: `test_factbundle_cache.py` 12/12 pass (incl. the live differential).

- **NAMED INSTABILITY / NOT-COVERED AXIS: model VERSION is not in the key universe.** The live
  daemon's `info()` advertises model NAMES (`loaded`/`default`) and backends, but **no model
  version**, so `pipeline_identity_from_info` cannot distinguish an in-place model upgrade under
  an unchanged name + backends — a stale bundle could be served across such an upgrade. This is
  named in the `factbundle_key` closure statement, not papered over. CLOSED 2026-07-03: `_info_reply`
  now advertises `spacy_version` + per-model `model_versions` and the identity allowlist folds them
  in; takes effect at the next daemon restart (pre-version daemons lack the fields, keys stable
  until then). Remaining named axis: the decode PEER's weights version is still not folded (the
  key sees decode address+backend only). Sibling not-covered axis: a pipeline-identity change **after** the wrapper's one-time
  lazy bind (a mid-run daemon model swap) — the wrapper binds identity once from advertised
  info; a mid-run swap to different models is not re-detected.

- **INCREMENT 2 (R-SUP, F1) — R-SUP-ESC durable deploy deferred to Increment 3.** The
  temporal-supersession increment shipped and gated at the fixture level
  (`experiments/fact-mining/test_rsup.py`: GOLDEN conversion + R-NEG suppression, MUTATION on the new
  `.lp` clauses, oracle↔clingo DIFFERENTIAL, negative-control byte-identity). The effect-level witness
  first attempt was BLOCKED by a daemon GPU-exhaustion state (14/18 universes refused, recorded in
  commit `e067074`); CLOSED same-day after the maintainer's daemon restart: 18/18 universes, 0 refusals,
  **3 R-NEG → 3 R-SUP** (the catalogued `daemon/advertise` temporal duplicates, one per carrying
  session), R-NEG density **0.587 → 0.235 /1k claims (−60 %)**, R-NUM bit-equal, 0 spurious R-SUP
  (`HOOK-TRIAL-RSUP-2026-07-03.md`, `findings_rsup_mainsession.json`). One item remains DEFERRED, filed
  here rather than left silent (ADR-0013 Rule 4):
    * **R-SUP-ESC SQL floor authored, not deployed.** `experiments/fact-mining/rsup_esc.sql` (the
      escalation-window view + Hedge v0 marker list) is gated inside a rolled-back transaction; it is
      sited over `kb.supersedes`⋈`kb.claim` (KB-CODESIGN §3, verbatim) and DEPLOYED DURABLY BY
      INCREMENT 3 with the rest of the `kb` schema, not by Increment 2 (which must not front-run inc3's
      DDL on the live DB).
    * **Named residuals (not silently left):** the v0 state-change marker list's PRECISION on broader
      prose is unmeasured (this run: 3/3 correct conversions, 0 false; small n); turn granularity is
      the prose UNIT (two sequential statements inside one unit get no ordering — an inherent recall
      gap of unit-level turns); the R-SUP-ESC floor is PAIRWISE (per supersedes edge), the chain-level
      "non-decreasing EMPHATIC" form is the ASP escalation deferred until defeaters accrue
      (KB-CODESIGN §4 ladder).

- **INCREMENT 3 (the KB ledger + stratified universes — F5, identity, L2's substrate) — DELIVERED.**
  The `kb` schema substrate is deployed durably and the identity/universe types are built behind the
  extension law (KB writes default-off; the default trial run is byte-identical to the v6 report).
  Shipped:
    * **`kb` schema (KB-CODESIGN §3), deployed DURABLY** via `kb_migrate.py` — `kb.claim`,
      `kb.supersedes`, `kb.finding`, the `kb.current_belief` view, and the **R-SUP-ESC durable deploy**
      (`kb.rsup_esc`, its one home now `rsup_esc.sql`, view-only — the Increment-2 dual-write of the two
      tables in that file was REMOVED, ADR-0012 P7). The DDL is GENERATED from `kb_ledger`'s
      authoritative column contract; the enum-backed CHECK vocabularies (`role`/`mood`/`hedge`/
      `quantity_dim`/`origin`/`reason`) are derived from the enums, not hand-typed (KB-CODESIGN §6).
    * **Schema-parity gate** (`test_kb_schema_parity.py`) — introspects the LIVE DB against the Python
      authority (column set, nullability, CHECK vocabularies == enum values). **Seen RED on a mutated
      enum first** (mutated `Role.QUOTED` → `live-only={'quoted'}, enum-only={'quoted_MUTATED'}`), green
      after revert; plus two self-contained negative controls (renamed + added member).
    * **`ClaimHandle`/`FindingIdentity`/`ClaimUniverse`** (`kb_ledger.py`, import-light — `Claim` is
      TYPE_CHECKING-only so the identity layer does not pull spaCy) with construction-time refusals
      (length, role-outside-kind, missing provenance, CROSS_ROLE-gated-on-mood — F5); gated in
      `test_kb_ledger.py`.
    * **The scrub-before-hash ingress** — `_SCRUB` promoted from `contra_app` to a shared home
      (`scrub.py`); `contra_app` re-points to it (no parallel copy, ADR-0012 P1). The handle is a hash
      of scrubbed text, so an unscrubbed variant is unrepresentable (witnessed: raw and pre-scrubbed
      rows of one claim share a handle).
    * **Trial driver writes the ledger** — `hook_trial.py --kb [--kb-arm ARM] [--kb-dsn ...]`
      (default-off; unset ⇒ no `kb` block, report byte-identical). **Idempotency witness (measured):**
      first ingest of a 2-file subagent slice = `claims_new=56`; re-run = `claims_new=0, claims_seen=56`
      (kb.claim total 56, not doubled). Finding `seen_count` bump witnessed against the durable schema
      via the exact UPSERT (insert seen_count=1 → re-observe seen_count=2, no second row).
    * **L2 cross-check RUNNABLE** (`l2_check.py`) — session claims × `kb.current_belief`. Demonstrated
      against durable state: beliefs=137, session=36, findings_union=15, **cross_findings=0** (a
      measurement, not a target — BUILD-PLAN).
    * **Cross-role universes stay GATED** on E-1's mood verdict, as ruled — `UniverseKind.CROSS_ROLE`
      exists and refuses at construction, but no cross-role analysis is built.
  Named residuals / not-covered axes (ADR-0013 Rule 4):
    * **Finding→handle linkage** in the trial write is by `(claim_text, sent_text)` map (the
      `_evaluate_arm.provs` key); on the rare textual-duplicate collision the first handle wins. The
      precise fix (emit claim indices on the `Finding`) is FILED, not smuggled — it would perturb the
      hot-path `Finding` shape the GOLDEN/bit-identity gates pin.
    * **Deferred to their own increments, NOT built ahead of their writers** (ADR-0004): `kb.mandate`/
      `kb.why_event`/`kb.why_orphaned` + reified work-unit tables (Increment 4, KB-CODESIGN §5),
      `kb.calibration` + the F9 supply indexes (Increment 5).
    * **L2 grounding fidelity**: claims read back from `kb.claim` reconstruct surfaces from keys and
      `sent_i=-1` (the ledger stores keys/scrubbed-sentence/number, not human surfaces) — sufficient for
      R-NEG/R-FUNC/R-NUM keying, named as the read-back limit.
    * The durable `kb.*` tables were left EMPTY after the witness (the witness ingested a tiny ad-hoc
      subagent slice to prove the mechanism; the ledger is handed over clean for a ratified sweep).
    * **DIVERGENCE (named):** INTERFACE §5 sketches `claim_handle(scrubbed_text, prov)` but its own
      docstring enumerates 8 hash inputs including the four atom fields (subj/pred/obj/negated), which
      `ClaimProvenance` does not carry. Implemented the honest full-fidelity form
      `claim_handle(scrubbed_text, subj_key, pred, obj_key, negated, prov)` — the hash content matches
      the docstring exactly; the 2-arg signature could not.

## NLP↔logic interface — Increment 4 filed deferrals + record (2026-07-03)

Increment 4 (the WHY-ledger, ordering, unsat-core — F6/F7/concern 3; BUILD-PLAN) reached its
ratified scope MINUS one item deferred by an OPEN maintainer gate (named below, per ADR-0013
Rule 4 — a deferral filed where deferrals live, never narrated-and-left).

**Delivered:**
- `kb.mandate` / `kb.why_event` + the witness-required TRIGGER (the frontier creed — "retire a
  WHY only via a failed experiment" — at the write boundary) + the `kb.why_orphaned` view (its
  one home, `why_orphaned.sql`), all generated from the `kb_ledger` authority and applied by
  `kb_migrate` (the Increment-3 DDL machinery extended, no parallel DDL home). Schema-parity gate
  extended to the two new tables; the enum-backed `why_event.kind` carries its own negative
  control; the gate was SEEN RED on a mutated `WhyEventKind` member before being trusted green.
- **R-WHY** (`why_layer.lp` + `kb_why.py`): the orphaned-WHY rule, DIFFERENTIAL-gated against the
  SQL floor (empty-empty on the defeater-free floor), with the impedance F-algebra→tagless-final
  arc as the GOLDEN fixture — orphan detected, then RETRACTED by the retirement-with-witness. Two
  compositional defeaters ASP earns over SQL: a witness-less retirement does not retire; a
  fatigued reverification does not discharge. A `why_layer.lp` mutation (`E2 > E` → `E2 < E`) was
  seen RED (fails to retract).
- **Z3 `unsat_core()`** (`unsat_core_z3.py`) over typed substrates: (1) venv version collisions
  from a real `pip freeze` pin + a contradicting spec (core minimal, deletion-proven, and named);
  (2) `AdvertisedLimits` indivisible axes vs a client plan (the core names WHICH bound bites).
  NEVER over prose ADRs (the ruled caveat honored).

**DEFERRED BY THE §5 GATE (R-ORD / reified work units) — an OPEN maintainer decision:**
- `R-ORD` (F7, precedence-violation) and its substrate — the reified `kb.work_unit` /
  `kb.discharge` / `kb.prereq` tables (KB-CODESIGN §5) — are **NOT built**. KB-CODESIGN §5 presents
  those tables as a *new* shape "**the maintainer's to ratify**", and BUILD-PLAN Increment 4 gates
  them "**iff ratified**". That ratification has not happened (maintainer asleep). R-ORD's rule
  `violated(U) :- prereq(U, V), touched(U, T), not discharged_before(V, T)` reads exactly
  `prereq` / `touched` / `discharged` — i.e. it is UNBUILDABLE without those tables. So R-ORD is
  deferred *in full and explicitly*, per BUILD-PLAN's own instruction ("if R-ORD is unbuildable
  without those tables, defer it explicitly and NAME that"). This is deferral by gate, not
  shirking: the blocker is a ratification the executor is not entitled to make. When ratified, the
  §5 tables + R-ORD (with the `WITH RECURSIVE` transitive-closure SQL view as its differential
  floor, and E-5's CLP(FD)-vs-clingo comparison if numeric domains enter) are the next unit.

**Named residuals / not-covered axes (ADR-0013 Rule 4):**
- **WHY-row extraction from prose is NOT built** (experiment E-4). v1's mandate/why_event rows are
  AUTHORED (DESIGN §3-F6 scope honesty); the impedance fixture is authored, not NLP-extracted.
- **Version encoding models the release segment only** (`unsat_core_z3.Version`): epoch, pre/post/
  dev, and local labels are dropped — a pre-release ordering (`4.0rc1`) would need full PEP 440.
  Named in the type's docstring; sufficient for the collision demonstration, filed not smuggled.
- **The ASP↔SQL differential is scoped to the defeater-free floor** (DESIGN §3-F6's own ruling):
  where a defeater fires the two diverge BY DESIGN (the SQL floor cannot express an open defeater
  set), and the ASP verdict is the honest one — so the differential gates the ENCODING, not the
  defeaters, exactly as the R-NEG/R-SUP differential does.
- **`run_clingo` extracted to `clingo_run.py`** (shared by `contra_asp` and `kb_why`; ADR-0012
  P1/P3 — folded the two byte-identical col-DDL emitters in `kb_migrate` at the same time) so a
  KB-only module never drags the spaCy stack `contra_asp` imports. The bare `timeout=120` literal
  became a named `DEFAULT_TIMEOUT_S` lever (default-preserving; INTERFACE §7's flagged cancer-F).

## Chocofarm-trial finding — R-SUP recall bound is upstream of the oracle (2026-07-03)

First run on the chocofarm corpus (`docs/hook-trial/HOOK-TRIAL-CHOCOFARM-2026-07-03.md`,
`hook_trial/v6`, 28 sessions / 409 MB): **0 R-NEG→R-SUP conversions** on the genre the
mechanism was built for — the corpus's "must be this → nope" revision chains never surface as
same-atom opposite-polarity R-NEG pairs at today's extraction (the retraction restates the
world under a different subject surface/predicate, so no candidate pair exists for the F1
discriminator to inspect). The oracle itself is proven (fixtures + 3/3 conversions on the
main-session corpus); the bound is extraction/keying — the same class as INC1 W1-c. Levers,
in measured-next order:

- **GLiNER-on supersession arm pair.** The trial's sup pair runs GLiNER-off by its Increment-2
  design; `both+gliner` sees 23 R-NEG in the same universes vs the sup pair's 7. *(Evidence pass
  2026-07-03, `docs/hook-trial/HOOK-TRIAL-CHOCOFARM-EVIDENCE-2026-07-03.md`, Q1 — decision still
  open.)* **CORRECTION: the 23-vs-7 was NOT the GLiNER lever.** `both+gliner` differs from `sup`
  in four levers (gliner/typed_subject ON, but ALSO `mood_gate` OFF and
  `same_sentence_foreclosure` OFF), so its 23 cannot attribute to typed keying. The clean
  isolation — arm `sup+gliner` = `sup` with ONLY gliner/typed_subject flipped, run over all 28
  universes cache-backed — gives **7 → 6 R-NEG**: typed keying adds ZERO and removes ONE (it
  split a bare-lemma-collapse noise pair, `fea84086` `deliverable/be`, a precision gain, not
  temporal-shaped). All 17 of the run's "extras" decompose to the two open gates (8 same-sentence
  shreds, 9 mood/mention/bare-lemma), none survives the clean arm, and holding `sup`'s gates typed
  keying yields R-SUP FEWER candidates (6 vs 7), surfacing no supersession pair. So the
  hypothesis "typed keying surfaces revision pairs the bare-lemma key splits" is **not supported
  on this corpus**; the `sup+gliner`/`sup-control+gliner` arm-pair addition may still be worth
  running on other genres, but the chocofarm 23 is not evidence for it and must not be cited as
  such.
- **Revision-statement keying.** The chains' retraction sentences carry the state-change
  markers (the marker list hits) but their claims key to different atoms; a
  normalization/coref step at the claim-join (predicate families, subject coref) is extractor
  scope (I1's family), not an R-SUP change. *(Evidence catalog 2026-07-03, same file, Q2 —
  decision still open.)* Hand-read sample of ~11 real "was X → actually Y" chains (before/after
  landed keys tabulated there), divergence classes with counts: **nominalization** (verb→subject
  noun) 3, **subject-referent swap** 3, **predicate paraphrase / light-verb** 2, **pronoun /
  embedded-attribution** ("I read/assumed X") 1, **value-in-object** 1, aligned-and-joined
  (contrastive-agreement, not a revision) 1. Only the value-in-object class (`configs-json/be/dict`
  → `configs-json/be/list`) is within reach of a subject-key change — and it is blocked not by the
  subject key but by both members landing asserted (no polarity clash) and `be` being excluded
  from `functional_preds`. The other four classes move subject and/or predicate, so a
  subject-only lever (typed keying) cannot reach them — consistent with Q1's null. Recovery is
  predicate-family + coref/nominalization work at the claim join (I1 W1-c family), not an
  R-SUP-oracle change.
- Also observed: in the two marker-carrying surviving R-NEG pairs the marker sits on the
  EARLIER member — R-SUP correctly declined both; any keying lever must preserve that
  discipline (the decline cases are regression fixtures when this is picked up).

## Rationalization ledger — detector outcomes as an appendable SQL corpus (maintainer, 2026-07-06)

The hack-rationalization detector fires positive often enough that its outcomes are a corpus,
not incidents — and the corpus is currently discarded. Two open ends, one mechanism:

- **The detector's case book is read-only.** The skill directs every runner to
  `~/.claude/skills/hack-rationalization-detector/references/known-cases.md` as its few-shot
  ("Read it before judging"), but there is NO append path — cases are hand-curated. The skill
  asks agents to learn from prior cases while providing no mechanism for a new case to become
  a prior case. Appending must be possible AND structured, hence SQL (maintainer directive).
- **The findings are not logged anywhere queryable**, so no bulk pass can ever run over them.

The mechanism: a `rationalization_finding` store in the harness DB — the third consumer of the
finding+disposition idiom (siblings: exposure/affirms in WORK-UNIT-exposure-discharge.md; the
findings-disposition policy-trigger design, this session). Sketch, to be designed properly:
finding rows (detector fire: quoted rationalization, register used, named-better-fix if any,
LAW refs, context/commit/session, detector version) + append-only disposition acts
(confirmed-hack / false-positive / duplicate-of, actor-attributed, F28: nothing auto-resolves).
Dispositions make the corpus LABELED, which serves both feedback directions:

1. **LAW improvement (the maintainer's stated goal):** post-RCA bulk audits query the corpus of
   confirmed rationalizations to find which ADR formulations get rationalized around most —
   the LengYue/SR pattern: every confirmed case is a failed position appended to the training
   corpus of the LAW; "one mistake and never again" made mechanical.
2. **Detector precision:** ~~the false-positive rate the maintainer is uncomfortable with becomes
   measurable~~ **[STRUCK 2026-07-06 — Fable misattribution.** The maintainer's verbatim words were
   "the hack rationalization detector seems to come out positive too often for comfort" and, on
   reviewing this entry: "What I meant to say was that I'm concerned *with positives*, hence the
   rationale: clearly the ADR is not explicit enough about some things." The concern was never
   false positives — he has not seen one; anecdotal precision to date is 1.0. The discomfort is the
   frequency of GENUINE positives, which indicts the LAW's formulations (direction 1 above), not
   the instrument. Fable's paraphrase inverted the target of the concern — the same drift class the
   ledgered-rulings mechanism exists to kill; this strike is the specimen.**]** The false-positive
   rate remains measurable as a side effect of labeling, and the `false-positive` disposition label
   stays in the vocabulary regardless — an adjudication vocabulary needs the acquittal outcome for
   "confirmed" to mean anything. Labeled false-positives, should any ever appear, are data for
   tightening the skill's formulations (and known-cases.md grows from the confirmed side — the
   append path the skill was missing, built in Increment 3).

Scope note (maintainer): the detector itself is shipped for THIS project, not vendor-agnostic —
vendor-agnosticism binds boundary hygiene and architectural discipline, not every instrument.
Status: queued for the post-Increment-2 prompt (with the preview-mode drop and the
dto_authentic_verify display fix). Design open questions: does known-cases.md become a VIEW
over confirmed rows (single source) or stay curated with the DB as feeder; skill-side write
mechanics (the skill runs in agents with DB access — an INSERT template in the skill bundle vs
a filing script in tools/).

## Repo-history stream (mechanism 5) — VCS facts behind a contract + the pre-registration anchoring fix (maintainer-commissioned, 2026-07-06)

Git is load-bearing for the harness today (evidence store, artifact identity, ordering
proofs) but semantically unintegrated — commit hashes live in prose, no instrument joins
ledger↔git mechanically. The resolution is the act-stream pattern applied again: a
vendor-free contract, a git adapter, a capability manifest that does the honest work.

**Contract facts (vendor-free):** `commit(id, parent)` (identity + parentage),
`touches(commit, path, blob_sha256)`, `ref_head(name, commit)` (derived current-state),
`author_claim(commit, name)` — author is a CLAIM, never an identity.

**Git adapter manifest, two loud entries:**
- *Author identity: CLAIMED, not verified* — git author fields are self-declared free
  text. Corroboration comes from the acts stream (which records who actually ran the
  commit command). Ledger claims × acts stream × repo history triangulate = code
  attestation without trusting any single stream.
- *Commit timestamps: EXCLUDED as ordering authority* — `GIT_COMMITTER_DATE` is an env
  var; commit dates are forgeable by whoever controls the repo.

**The near-term fix with teeth (belongs in Increment 4's rulings-ledger scope, NOT a
separate increment): pre-registration anchoring.** Current pre-registration proofs
(e.g. Increment 2's "oracle committed 16:32, producers 17:02") rest entirely on
forgeable git metadata. Within the standing threat model that is a pre-registered
assumption (the apparatus operator is trusted); against the NRC bar a third-party
auditor should not have to trust our commit dates. Fix: file the artifact's sha256 as
an `acts.ruling` row (append-only, id-is-order) BEFORE the dependent work builds — the
DB's insertion order then anchors what git timestamps only claim. Git corroborates;
the ledger anchors. One row per pre-registration, effective immediately for every
future oracle/fixture/frozen-text.

**The structural rhyme (why this is an EDB source, not a special case):** git IS a
two-theory record — the object DAG is monotone T_event (commits only ever added), refs
are the non-monotonic T_now (branch heads = in-force heads; a force-push is a
supersession event; `--amend` is edit-in-place semantics escaping an append-only
substrate). The engine's existing closures (staleness, supersession, exposure) apply to
code history with almost no new theory; the file-granular `stale_enactment_debt`
instrument is the hand-built precursor ("enacted file changed after enactment, no
re-enactment" is a repo-history judgment). Non-foreclosure clauses inherit as always.

Status: anchoring fix → Increment 4 (rulings ledger); the full stream/adapter → its own
later increment, after the acts adapter proves the seam shape.

---

## `unledgered_span` contiguity: raw act-id vs relevant-act subsequence (e15 Inc-5, out-of-frame audit)

`ledger_acts.lp`'s `unledgered_span` keys the span on RAW act-id contiguity
(`unledgered_lr(A-1)`). On the REAL adapter stream a non-relevant `tool_result` echo sits
between essentially every pair of fenced writes, so a run of consecutive unledgered writes
fragments into SINGLETON spans (`unledgered_span(A,A)`) — a merged span >1 can almost never
form for the write-heavy case. This is a PACKAGING granularity, not a correctness gap (the
same acts surface as unledgered either way; the consumers stay descriptive and adjudication
disposes on the atoms), but the predicate name `unledgered_span` mildly over-claims
(ADR-0008 name register). The alternative — contiguity over the RELEVANT-act subsequence
(skip non-relevant acts, merge runs interrupted only by echoes) — would merge such runs and
would NOT change the Increment-4 scratch atoms (whose relevant acts had no interleaved
non-relevant acts). A maintainer decision, deferred here rather than taken unilaterally:
`ledger_acts.lp` is a banked, pre-registered producer left BYTE-IDENTICAL. If adopted, add
the relevant-subsequence adjacency to `ledger_acts.lp` + its SQL floor and re-pre-register.
Site: `experiments/fact-mining/ledger_acts.lp` (span_start/span_end/reach). Fail-safe as-is.

---

## The general findings ledger (db/harness/005) — sibling of the rationalization ledger (002)

Landed e15 Increment 5 (WORK-UNIT-findings-disposition). The two stores are SIBLINGS:
`tools/file_rationalization.py` (002) carries detector FIRES (rationalization-shaped, with
detector-specific columns); `tools/file_finding.py` (005) carries ALL in-passing work
FINDINGS + their dispositions. Same append-only trigger idiom, same filing-script shape.
The governing move is the structural separation of provenance from disposition: a
`provenance_claim` is metadata on an OPEN finding, never closure; only an actor-attributed
disposition act closes a finding (F28). The `findings_gate` close line (the fourth close_manifest
consumer) goes RED on any OPEN finding. Cross-link recorded here per the work-unit acceptance.

## Responsibility-chain completion — discharge vocabulary + invocation binding (maintainer, 2026-07-07, mid-e15-close)

Two gaps the e15 run exposed, maintainer-spotted ("work unit discharged, signed (name)"):

1. **No discharge speech act in the subject kernel.** Completion claims land as untyped `note`
   rows (e15 row 22, "Build complete" — no typed edge to the charter it discharges). The
   flag+discharge idiom exists three times HARNESS-side (rekey_debt/rekeyed, exposure/affirms,
   finding/disposition) and was never promoted subject-side. Dormant stub exists:
   `countersign_obligation` (0 rows). Honest shape candidate, per the kernel's grows-by-review-only
   law: discharge as a review-species (verdict='discharged', regards=the obligation row) — SoD
   comes free from the existing validate_review trigger, i.e. "signed by someone other than the
   doer" is mechanical. Needs a maintainer ruling (kernel vocabulary); e16/s16 item.
2. **Invocation binding: derive, don't legislate.** Vendor side fully identifies individuals
   (agentId + sidechain file per invocation, wf_ ids, spawning-prompt hashable, .meta.json).
   Kernel principals are ROLES, not invocations. The bind is mechanically derivable: every ledger
   row was inserted by a psql act attributed to a specific sidechain in the acts stream →
   `row_performed_by(row_id, invocation_id)` is a DERIVED judgment (new engine consumer; no kernel
   change, no subject burden). Unlocks the deepest differential yet: CLAIMED principal vs
   ACTS-DERIVED performer — SoD verified against reality, not against the ledger's own claim.
   Also fold in per-invocation MODEL provenance from .meta.json (degradation honesty at the
   invocation level). Feeds link-27 synthesis §2 (judgments derivable live) and the deductive
   engine directly.

## Interception-stamped row provenance — mechanism 2's killer app (maintainer, 2026-07-07, post-finding-31)

Ledger rows carry no vendor identity tokens (session/agent/workflow ids) checkable against
~/.claude — historical omission, not design; the acts stream was the planned binding but is
post-hoc reconstruction. Maintainer's proposal, endorsed: WRITE-TIME stamping BY TOOL
INTERCEPTION, never by the collaborator ("pasted by the tool interceptions rather than
stamped by the LLM" — the load-bearing clause). Shape: PreToolUse hook detects ledger-bound
psql calls, injects true session/agent ids via connection GUC (PGOPTIONS -c app.vendor_*);
a set_actor-style BEFORE INSERT trigger reads current_setting() into provenance columns.
The hook stamps, the trigger lands it, the LLM neither types nor omits it. Finding 31's
specimen becomes one-SELECT visible (claimed actor 2, stamp identical to author rows).
LIMITS, pre-registered: tripwire not authentication — script-mediated INSERTs evade the
Bash-pattern hook and GUCs are imitable by an aware client; evasion is itself a disposition
finding; the acts differential stays the adversarial backstop (standing threat model).
LAB QUESTION before build: can hook context see the calling SIDECHAIN's id (session id yes;
per-agent id needs a workflow-mechanics-lab-style shakedown). Upgrades finding 31's candidate
law: independence claims could require STAMP-distinctness (cheap, row-local) with
acts-corroboration as the deep check. e17-era item; composes with the hook seam (mechanism 2)
and the invocation-binding deriver (finding 28).

### Refinement (maintainer posture ruling + stateless design, 2026-07-07 ~04:00)

**POSTURE RULING (maintainer): measure once, then mechanize.** For fabrication classes with
a captured specimen (row 7 / finding 31), the kernel REFUSES at write time and TEACHES
("don't do that, do the right thing instead") rather than banking known fabrications for
post-hoc adjudication — continuing to allow them measures sloppiness, not disposition.
Novel classes still get measured before they get gated. Refusals are themselves evidence
(server log + acts stream; the F34 denial-teaches mechanism, proven at e15).

**Stateless design (supersedes the login-token sketch):** per-call HMAC stamps — hook
computes HMAC(secret, session_id||agent_id||ts) into a connection GUC; SECURITY DEFINER
trigger recomputes against a secret in an apparatus-owned table the subject role cannot
SELECT; mismatch/stale -> REFUSED with a teaching message naming the honest alternative
(e.g. independence='self-review' — finding 31's vocabulary fix lands in the same stroke).
No stored tokens, no hidden connection, no TUI-exit cleanup; liveness via stamped ts window.
LIMIT (pre-registered): hook runs as the same OS user — the secret is hunt-able; defeats
sloppy fabrication completely, converts deliberate evasion into crisp acts-stream evidence;
cryptographic hardening explicitly left to the pros. BRIEF-conformant: refusal is a gate,
not an auto-resolution (F28 intact); attribution integrity is I-register core; the
descoped class was sandbox-adversary defense, not this.

### Rider: delivers-FK on acts.ruling (finding 35, maintainer grade "air raid siren", 2026-07-07 ~05:00)

Delivery filings in acts.ruling carry NO formal key to the freight they deliver (id 26 →
id 25 held only by byte-coincidence + prose regards; supersedes=NULL). The forged-ruling
class on the rulings spine itself: nothing refuses a freight-less delivery filing, nothing
fires when a filed delivery's verbatim DIFFERS from its frozen freight. Two-stage
foreclosure (finding 35's intent): (1) IMMEDIATE — `delivery_freight_integrity` close line,
pure SELECT: every binding delivery row byte-matches a frozen freight row it references,
RED otherwise; (2) e17-era DDL riding THIS item — a `delivers` FK column + trigger
(verbatim byte-identity with the referenced freight, or explicit amendment lineage).
Same convention-where-a-key-belongs family as finding 34.

## Work-unit authorization — policy as derived judgment over the logic substrate (maintainer, 2026-07-07 ~04:15)

Maintainer need: role-dependent authorization over work units incl. delegation constraints
("finder may not fix but may delegate a fix agent") and large-task DAG-partition ({OR,SSE}
pair decomposes, executive synthesizes/schedules with in-flight knowledge, pair signs).
SHAPE: (1) may(P,Act,U) as an ASP/Datalog-DERIVED judgment over holds_role/delegates/scope
facts — the policy is a versioned rules file, sha-anchored as a ruling, amendable by ruling
(flexibility = rule edits, never migrations); (2) two-tier enforcement per the
measure-once-then-mechanize posture: specimen-proven SoD-class rules compile to
trigger-consultable forbidden/3 rows (refuse-and-teach, validate_review generalized), full
policy derived engine-side (unauthorized_act/3 loud at close + consulted at ORCHESTRATION
time before spawning); (3) delegation = recorded edges + delegation_spawn acts + stamps
(claimed-vs-stamped polices the chain); (4) DAG-partition = DTO §1.5 vocabulary REUSED
FORWARD (decomposes/group/attests for work-partition, not defeat-repair — already built and
exercised) + change-gate scope tickets for conflict detection: parallel_safe(U1,U2) derived
from scope disjointness + DAG edges; (5) live motivation: the foreclosure back-fill is
per-finding parallel with only registry/DDL merges serialized — a partition pair would cut
an hour to the longest single gate. Non-foreclosure inherited: policy in the substrate,
never baked into the kernel. e17-era; composes with stamps (above) and mechanism 2.

**Authoring seam (maintainer question + Fable design, 2026-07-07 ~05:45):** how ephemeral/
throwaway policies get WRITTEN without raw-ASP arcana — full judgment banked in
`docs/design-notes/policy-authoring-seam.md`. Shape: ratified pattern library (parameterized
ASP templates, each with both-polarity control fixtures — seen-red applied to policy);
instantiation as DATA rows (`policy_instance(pattern, params, scope, expiry)`) — no DSL, no
compiler, ephemeral = TTL'd rows, ASP stays the single semantic SSOT; LLM authors only the
novel remainder, gated by pre-registered control cases + the e16 adversarial pre-test for
high-stakes rules; recurring novel rules PROMOTE into the library (measure-once-then-
mechanize applied to policy). Friction budget is a safety parameter: a compliant one-off
must cost seconds or people route around the record.

## Self-hosting — the project as the harness's first production user (maintainer observation, 2026-07-07 ~05:00)

Maintainer noted (correctly): the project does not kernel-ledger ITS OWN work — consults/
deliberations are prose with hand-maintained kernel semantics (verbatim quoting, dated
addenda, quote-and-strike); odd/even SoD is convention, not trigger; the prose-half-life
class (the forged-ruling specimen) remains mitigated, not mechanized, on the operator side.
Meanwhile the ops slice that IS mechanized keeps growing: finding+disposition, acts.ruling,
class_foreclosure — deliverable patterns already running against ourselves (the never-again
mechanism's first RED was against its own builder). THE MILESTONE: instantiate a kernel
lineage for PROJECT OPERATIONS (increments = decisions with enacts; completions =
verifications; adjudications = reviews with review_detail + antecedent; maintainer rulings
already in acts.ruling; consult files become pointers into rows — mechanism 3's
deliberations-become-pointers, generalized). Bootstrap order: after e17-era stamps land
(ops rows deserve the same provenance the subject rows get). Evidence value: "we run our
own operations under the harness" is the strongest NRC-bar demonstration class — dogfood
as proof. Distinction preserved: the DELIVERABLE is the pattern+schema (published); our
instance is its first deployment, and the deployment record is itself publishable evidence.

**RULING (maintainer, 2026-07-07 ~05:30, re-scopes the milestone):** "I think we *shouldn't*,
in fact, ledger our own work while we're iterating on it. A CI-like gate is a completely
different thing since it's fixed in time." SCOPE ACCORDINGLY: work-in-iteration (design
churn, drafts, reversals-in-progress) is NOT ledgered — the ledger idiom presumes claims
worth holding an actor to, and exploratory churn is not that; forcing rows onto it would
make every honest reversal look like a contradiction owed an answer. What IS in scope stays:
fixed-in-time gates and their outcomes (close manifests, foreclosures, findings+dispositions,
acts.ruling anchors) — these are already mechanized and remain so. The milestone above is
therefore re-read as: extend the mechanized slice ONLY where an artifact is frozen at a
point in time (a completed increment's completion, a ruling, a close), never the live
deliberation between freezes. Consults remain prose; their FREEZE POINTS (sha256 anchors,
rulings extracted into acts.ruling) are the ledgered surface.

**Clarification (maintainer, verbatim):** "All consults and everything else we've saved so
far remain *saved on disk*, just as always. When I say 'ledgered' I mean dogfooding our own
work-in-progress, which is what's unsound, informally speaking." — i.e. the ruling touches
nothing about disk persistence or the prose record; it rules out only kernel-ledgering
iteration-in-progress.

## Review fixed-point protocol — polishing pattern (maintainer proposal, 2026-07-07 post-e17)

Iterate independent-review→fix until a FRESH FIRST-CONTACT review of the final artifact
version yields zero undisposed findings (never the verbal verdict "flawless" — structural
criterion only). Two species: delta-review (same reviewer, verifies the fix; anchored by
construction; never terminates) vs criterion-review (fresh stamp, blind brief;
terminates). Enforcement split: stamps (kernel, EXISTS) / `review_fixpoint` close line
(BUILD: stamp-distinct + first-contact + zero-undisposed, three derivable joins) /
orchestration loop with K-consecutive + HARD round-cap (policy). First ratified pattern
candidate for the policy-authoring-seam library. e17 datum: its terminating attest (18)
was a directed delta-review — would NOT satisfy the criterion; entry 17 (fresh, caught a
real defect the author's verification missed) is the value proof. Full design:
docs/design-notes/review-fixpoint-protocol.md. Empirical tail (fresh reviewers' real-flaw
rate over rounds) unmeasured — future e-lever.

## Shipping north star — packaging as product definition (maintainer direction, 2026-07-07 afternoon)

Maintainer: packaging is "haphazard... the only real barrier to deployment as-is for
non-institutional actors"; shippable shape = the fixed north star for consistent iteration.
DEFINITION BANKED (Fable): docs/SHIPPING-NORTH-STAR.md — audience/promise, PRODUCT-vs-LAB
declared boundary via ship/MANIFEST (single-home, derive-never-copy), ship_gate (fresh-
bootstrap proof + manifest integrity + fixture census + honesty-sheet-current; an increment
that breaks shippability goes RED), kernel-generation versioning, the e17 tutorial, v0
exclusions (engine, multi-vendor, hosted, crypto-hardening). Execution = Opus-grade
increments (i)-(v) per §7; the definition is stable, execution iterates.

## INCIDENT + foreclosure: copyrighted source PDFs pushed publicly (2026-07-07 ~23:2x)

The consolidation migrated law/briefs/*/sources PDFs (design C10) and the first push
published them. Response same hour: PDFs saved to ~/w/vdc/1/local-sources/ (outside any
repo), full history rewrite (filter-repo --invert-paths, HEAD 0e04e39 → f432c10), forced
update, README stubs + .gitignore foreclosure. RESIDUAL (honest): anyone who cloned in
the exposure window holds the objects; GitHub may cache unreachable objects until their
gc — a GitHub Support purge request is the thorough close (maintainer's call). Root
cause: the publish gates (PUBLISHING.md: "copyright PDFs permanent exclusion") lived in
the OLD repo's process and did not migrate as a MECHANICAL gate — the class fix is a
pre-push hook refusing PDF/binary blobs without an allowlist entry, riding the next
increment. MIGRATION.tsv retains the PDFs' origin rows (true historical record; their
dest is now local-sources, noted here).

## INCIDENT 2 (same night): session ephemera pushed publicly — privacy class

The consolidation's whole-session ephemera snapshot (288 files incl. maintainer
conversations) rode the first push. Expunged same hour: saved to
~/w/vdc/1/local-sources/autoharn-ephemera/ (and restorable to ephemera/session-*/
untracked), history rewritten (9352cf3 -> 4acb23d tip), forced update, .gitignore +
README foreclosure. Same residuals and GitHub-Support-purge recommendation as incident 1.
Class fix folded into the pre-push gate item: the gate's default posture is ALLOWLIST
(nothing binary, nothing under ephemera/, nothing under */sources/), because both
incidents were default-open publishing of classes the old process excluded by prose.

## s19 residue: validate_* triggers resolve the ledger via SESSION search_path, and SET ROLE voids the login-default premise (2026-07-09, toy-kernel walkthrough)

s19's closure statement scoped `validate_enacts/review/amends/answers` OUT of the
search-path class with the justification "resolved by the role's login search_path"
(s19-trigger-search-path.sql §QUANTIFICATION, bullet 3). That premise holds only when the
writer LOGS IN as the ledger role. The documented usage pattern — QUICKSTART and the
WALKTHROUGH both connect as the owner and `SET ROLE` — does NOT apply the target role's
`ALTER ROLE … SET search_path` (a Postgres semantics fact: per-role settings apply at
session start, not at SET ROLE). Today this is masked because both docs also issue an
explicit `SET search_path`; drop that line and every LINKED insert (enacts/amends/answers/
review) fails `relation "ledger" does not exist`, while plain decisions still work — a
half-broken state discovered only when the user first exercises the linking vocabulary,
i.e. exactly when they try the interesting features. Fix shape (the s19 denomination, one
more application of the same mechanism): a future sNN delta gives the four validate_*
functions the same per-function `SET search_path = :"schema", pg_temp` carried by
set_actor/set_stamp, closing the whole in-chain family instead of leaving a
prose-guarded residue. Until then the SET line is documented as REQUIRED in the
WALKTHROUGH (done 2026-07-09). Not maintainer-ratified; filed for ruling.

## Ruling: layout-census gate not enforced in this repo (maintainer, 2026-07-09)

`gates/layout_census.py` (LAYOUT §3.4/[C21]) is a guarantee for **downstream** template
consumers who want their own repo's top-level tree mechanically checked against their
LAYOUT.md — it is not a guarantee this (research) repo needs enforced on itself. Maintainer
ruling: disable its enforcement here until further notice; this is a deliberate policy
decision, not a workaround for an unresolved breach. `hooks/pre-commit`'s layout_census
block was removed from the enforced chain (staging_guard -> no_lazy_imports -> fixture_census
-> doc-legibility now runs); `gates/layout_census.py` itself is untouched and remains shipped
tooling — a downstream instance re-adds the block to get the guarantee in its own repo. See
`hooks/pre-commit` for the exact wiring and this note's cross-reference.

## Operator-doc steps must carry their witness (2026-07-09, toy-pilot stamp-secret incident)

Class (ADR-0000 2(a) form): a documented operator step whose precondition was never
established or exercised is representable and indistinguishable from a witnessed one.
Instance: toy-project/.claude/HOOKS.md's "one manual step" exported the stamp secret from
`stamp_secret` — a table the kernel deliberately creates EMPTY (s17: provisioned at arm;
the pilot has no arm step). The authoring agent correctly reported that path unexercised,
but the DOC carried no such mark, and the orchestrator relayed the command as a walkthrough:
the maintainer ran it and got a silent zero-byte secret file (psql: zero rows is success).
The unverified claim was laundered at the doc/relay boundary, not at the report. Lapse is
the executive's (ADR-0000 2(b)): no mechanism requires an operator step to carry evidence.
Fix shape: an operator step in shipped docs is an artifact with two parts — the command AND
the observed output of a real run (or an explicit UNWITNESSED stamp); a walkthrough
containing an unstamped, unwitnessed step is the loud failure. Candidate surface: the
doc-legibility gate family, or the walkthrough-verification instrument. For the refactor
spec; not maintainer-ratified; filed for ruling.

## Proposed: mechanize the ADR-0013 Rule 3 demurral-detector as a Claude hook (maintainer, 2026-07-09)

Maintainer proposal, anticipated verbatim by ADR-0000 Revisit #3 ("an out-of-frame
rationalization-detector run on the fix's justification... tighten Rule 2's surface from
review-only toward the gate"). Shape ruled by ADR-0011 Rule 4 (enumeration fails open):
NOT a phrase blocklist — the attrition reflex is a paraphrase engine. Two parts:
(1) OFFLINE: fix-point a Haiku adversarially (loop-until-dry) to build the eval corpus —
cop-out variations ("YAGNI", "gold-plating", "doesn't apply here", ...) PLUS hard negatives
(legitimate neutral scope questions, fair-dealing renegotiations) — the seen-red fixture
set that proves the detector fires. (2) RUNTIME: a live small-model classifier hook carrying
Rule 3's discriminators (work already mandated? conclusion pre-drawn? who decides?),
regression-tested against the corpus. Attachment points: Stop hook on completion claims;
PreToolUse on AskUserQuestion (Specimen 2's canonical artifact: the skip pre-recommended).
Known risks to design against: false positives on honest renegotiation (2026-06-24
amendment, fair dealing both ways); Goodharting (re-run the adversarial loop against each
deployed version). Existing manual counterpart: the hack-rationalization-detector skill.
When minted, record by dated amendment at ADR-0000 Revisit #3 / ADR-0013 Revisit #2
(maintainer ratifies). Filed; not yet commissioned.

## Kernel defects found by full-surface exercise on toy (2026-07-09) — proposed s20 delta

Witnessed by the toy-pilot exercise run (toy-project commit 9bf80c4, ledger rows 15-30):
(1) **countersign_obligation grants gap**: s15's GRANTS block grants SELECT on the review_gap
VIEW but nothing (no SELECT, no INSERT) on the countersign_obligation TABLE; review_gap is
security_invoker, so the subject role gets "permission denied" on both writing an obligation
AND reading the gap view. The obligation→gap→countersign fix-point — s15's own preamble says
the subject "is meant to reach for it" — is unreachable under the documented role. Letter
of the GRANTS vs spirit of the preamble: the spirit loses at the grant layer.
(2) **Stale views missing stamp columns**: ledger_current and countersigned_in_force are
`SELECT l.*` views created in s15; Postgres froze the expansion before s17's ALTER TABLE added
stamp_session/agent/ts/hmac/verified, so both views silently lack all five stamp columns
(verified via \d). Consumers needing stamps must hit the base table.
Fix shape: ONE new lineage delta (s20) — GRANT SELECT, INSERT ON countersign_obligation TO
:role (mirroring the ledger's own grant posture; the not-self-assigned CHECK and append-only
posture still govern), plus CREATE OR REPLACE of the two views with explicit column lists
(never `l.*` again — that idiom is how this class formed). Candidate to fold in: the filed
s19 validate_* search_path residue (above), pending its own ruling. Delta authoring is
mechanical; APPLYING it to a deployment is the operator's/maintainer's act with explicit -v
vars, per standing rule. Filed for ruling.

**STATUS (2026-07-09, this commit): AUTHORED + SCRATCH-WITNESSED; pending maintainer assent
for the live apply.** `kernel/lineage/s20-obligation-grants-and-view-refresh.sql` written in
house style with a full ADR-0000 closure statement (invariant / quantification universe —
every table and view s15+s17+s17b+s19 exposes, enumerated; only countersign_obligation and
the two `l.*` views are members of either defect class / denomination). On the append-only
question the task itself raised: answered NO from the record —
`s13-remediation-review-detail-truncate-guard.sql` (2026-07-07) already rules
"countersign_obligation is mutable config in both, correctly unguarded"; this delta grants
SELECT/INSERT only and does not reverse that ruling.

Witnessed on a scratch schema pair in the live `toy` database (chosen so the witness runs
against the same DB the eventual live apply targets, without touching `toycolors` itself):
schema `s20probe`, kernel schema `s20probe_kernel`, role `s20probe_rw` — built fresh via
`high_watermark_1.sql` then this delta, both with every `-v` var pointed at the scratch names.
Left in place as evidence. Verdicts, all as the scratch role:
- cross-principal obligation INSERT (alice→bob) succeeded; self-assigned INSERT refused by
  `obligation_not_self_assigned` (`ERROR: new row ... violates check constraint`).
- `review_gap` readable by the role; showed the open debt (`id=1, actor=3, scope=scope-1,
  assigned_by=2`) before countersign; the row it named as the author's own row was still
  gap-visible; a cross-principal `review`+`attest` countersign made the gap row disappear
  (0 rows after).
- `ledger_current` and `countersigned_in_force`, re-`\d`'d after the delta, both carry all
  five `stamp_session/stamp_agent/stamp_ts/stamp_hmac/stamp_verified` columns.
- Negative controls held: ledger UPDATE/DELETE both `permission denied for table ledger`
  (append-only privilege posture, unchanged); `countersign_obligation` UPDATE/DELETE both
  `permission denied` (no such grant was added — the mutable-config ruling stands: privilege-
  gated, not trigger-gated); SoD held — the row's own author attempting to countersign it
  raised `"a row's author may not countersign it (segregation of duties)"`.

**Live-apply one-liner (toycolors; NOT run — the operator's/maintainer's act):**
```
psql -h 192.168.122.1 -d toy -v schema=toycolors -v kern=toycolors_kernel -v role=toycolors_rw -f kernel/lineage/s20-obligation-grants-and-view-refresh.sql
```

## engine/acts_join.py `_read_ledger` still leans on the pre-registry epistemic fallthrough (2026-07-09, USE-MODE-ENGINE-WIRING items 1-3)

Class (ADR-0000 2(a) form): a caller that resolves a ledger target by name, but was written
against the OLD "any unrecognized name defaults to a schema in `epistemic`" convention, is
representable — and, unlike its siblings, was not fixed in this increment because it is
UNTESTED and off-mandate. Discovered while wiring `engine/targets.py` as the one home for
(db, schema, kern) resolution (design/USE-MODE-ENGINE-WIRING.md items 1-3): `engine/
ledger_edb.py` and `instruments/ledger_target.py` now refuse an unrecognized target name
loudly (the toy-collision defect the spec forecloses), with the registry widened during this
same increment to also accept the apparatus-scratch (`.*_scratch$`) and lineage-mirror
(`^s\d+[a-z]*$`, e.g. `s13probe`) naming conventions that the live test/instrument surface
already depends on (verified against every `resolve`/`export`/`*_manifest` call site under
`engine/`, `engine/tests/`, and `instruments/`, plus the `pg_namespace` schema list on
`epistemic`). `engine/acts_join.py`'s `_read_ledger(source_name)` (and `resolve_ledger =
ledger_edb.resolve`) is the one remaining call site whose OWN docstring documents the exact
pre-registry convention ("special targets: e15->vsr; a plain name is a schema in
`epistemic`") for an arbitrary `source_name` — e.g. `drive/rehearsal/rehearse.py`'s
`mock_e15_synth`, which matches none of the widened patterns. No test in `engine/tests/`
exercises `build_join`/`run_close`/`_read_ledger` (confirmed by grep), so this increment's
"everything else must pass" bar does not require touching it, and a live-DB-dependent fix
here cannot be verified without a real run — hence filed, not patched speculatively.
Fix shape: either (a) give `_read_ledger` its own explicit fallback (catch `targets.py`'s
`ValueError` and construct an `epistemic`-schema `Target` directly, mirroring the
`engine/acts_edb.py` fix this increment DID make for its three analogous call sites), or
(b) decide the acts-join/rehearsal surface should also refuse an unrecognized name loudly
and update its callers' names to the registry's closed vocabulary. Either is a small,
mechanical change; it needs a live run (or a new test) to verify, which is why it is filed
rather than guessed at. Sibling of the `.*_scratch$`/`^s\d+[a-z]*$` widenings recorded in
`engine/targets.py`'s own docstring.

## `ledger_differential.py`'s CLI covers only the T_now family — the support differential has no operator-facing entry point (2026-07-09, USE-MODE-ENGINE-WIRING items 4/6/7)

Class (ADR-0000 2(a) form; a declared-in-scope capability with no reachable surface is the
same F49 shape the design doc's own §1 defect class names, one register up: not a silent
WRONG answer, but a silent WRONG REACHABILITY). `design/USE-MODE-ENGINE-WIRING.md` item 5
declares TWO judgment families "in scope now": `ledger_tnow` (+ SQL-floor differential) and
`ledger_support` (+ floor) — read as a scope statement, both should be operator/agent-
invokable the same way. But `engine/ledger_differential.py`'s CLI (the exact command `toy-
project/judge` is spec'd to invoke, item 4: `ledger_differential.py toy --retain`) hardcodes
`asp_program: Path = TNOW_LP` in `run_asp`/`main` with no `--program`/family-selection flag —
it can only ever run the T_now-vs-floor family. The support-layer differential mechanism
(`ledger_floor.support_floor_atoms`, generic over any `name`; the ASP side composing
`[ledger_tnow.lp, ledger_assumes.lp, ledger_support.lp]`) exists and IS generic, but its only
committed caller is `engine/ledger_support_scratch.py`, which hardcodes
`SCHEMA="marriage_support_scratch"` / `DB="epistemic"` — it cannot target an arbitrary named
ledger like `toy` without a code change. Witnessing the support differential against `toy`
for this increment's item 7 required an ad hoc, uncommitted Python snippet built directly
from the generic library functions (`ledger_floor.support_floor_atoms("toy", now_epoch)` +
`clingo_run.run_clingo([TNOW_LP, ASSUMES_LP, SUPPORT_LP], edb_text)`, filtered to
`ledger_floor.SUPPORT_PREDS`) — not through any judge/CLI-shaped entry point, and its result
(AGREE, 4 atoms) is reported in this session's record but was never banked as a
`--retain`-shaped DerivationRecord because no committed tool produces one for this family
against a non-scratch target. Quantification universe: same gap for `ledger_assumes`
(declared engine-only/no-floor by item 5, and genuinely un-invokable generically for the
same reason: no CLI takes a target + program-family pair). Not fixed here per this
increment's explicit constraint (engine/instruments code is DONE, not to be modified) and
per ADR-0004 scope discipline (a CLI-shape change is its own increment, not a doc/witness
task's silent scope creep). Fix shape: extend `ledger_differential.py`'s CLI with a family
selector (e.g. `--program {tnow,support}`, defaulting to `tnow` for byte-identical
backward compatibility) that composes `[TNOW_LP, ASSUMES_LP, SUPPORT_LP]` and calls
`support_floor_atoms` instead of `floor_atoms`/`run_asp`'s single-program path when
`support` is selected, with its own `retain()`-shaped banking — a maintainer decision on
whether the two families share one `DifferentialResult` shape or get siblings.

## `hooks/pretooluse_change_gate.py`'s `PGHOST` is a hardcoded module constant — a scaffolded instance on a different host silently mis-targets (2026-07-09, OPUS-READINESS move 1/2)

Found in passing while building `filing/deployment_record.py` / `bootstrap/new-project.sh` (a
deployment record's whole point is to name db+host+schema+kern+role in ONE place a scaffolded
project's tooling reads). `hooks/pretooluse_change_gate.py` line ~82 reads:
`PGHOST = "192.168.122.1"` — a bare literal, with NO env override (every other connection
parameter in the same file — `E13_GATE_DB`, `E13_GATE_LEDGER`, `E13_GATE_STATE`,
`E13_GATE_JOURNAL`, `SUBJECT_ROOT`, `DENY_HINT` — is `os.environ.get(...)`-overridable; `PGHOST`
alone is not). A scaffolded instance whose postgres lives on a host other than
`192.168.122.1` (a deployment record's `host` field exists precisely to name this) would have
its change gate silently querying the WRONG HOST — either connecting to an unrelated database
that happens to share a name/schema on that host (worse: a false ALLOW or a false DENY that
looks like a normal refusal, never surfaced as "wrong host"), or timing out/refusing with a
connection error that gives no hint the fix is a host mismatch, not a missing ledger entry.
This is the exact "silent wrong database" defect class `engine/targets.py`'s own docstring
names and forecloses for itself — the same class, one hop over, in the ONE live hook a
governed edit passes through on every tool call.

NOT fixed in this session: `hooks/` is explicitly out of scope this increment (a live session
reads `hooks/pretooluse_change_gate.py` per-event right now; OPUS-READINESS move 1 names the
hook rewiring to read a deployment record as deferred future work, not this pass). Filed per
CLAUDE.md's engineering-responsibility clause (a hazard within reach, not routed around) and
ADR-0013 Rule 4 (fixed or filed, never narrated-and-left). Fix shape: `PGHOST =
os.environ.get("E13_GATE_HOST", "192.168.122.1")`, one line, byte-held default for every
existing deployment (autoharn's own + toy's, both on `192.168.122.1` today) — land it in the
SAME pass that rewires the hook to read a project's `deployment.json` (the natural home for
`E13_GATE_HOST` to be set FROM, via the scaffold's settings.json template, exactly as
`E13_GATE_DB`/`E13_SUBJECT_ROOT`/etc. already are).

### s20 apply sequencing (maintainer, 2026-07-09, verbal)
NOT YET: toy run 1 (all-Sonnet, countersign prompt) is mid-flight — the deployment stays
frozen under a running experiment. Sequence ruled: run 1 completes → s20 applied to toycolors
(one-liner above) → run 2 starts fresh on the upgraded kernel. Two clean runs, deliberately.
