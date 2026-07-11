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

## FIXED: `ledger_differential.retain()`'s single mutable slot clobbered the first-AGREE evidence (2026-07-09)

`retain()` wrote every `--retain` run of a target to the SAME path (`RETENTION / target`), a
single mutable slot; a later run against `toy` silently overwrote the first-run banked
DerivationRecord pair with the second-run's (bit-for-bit clobber, uncommitted-but-in-place —
found as a hazard in passing, not part of this session's assigned task, and fixed per
CLAUDE.md's engineering-responsibility clause). Fixed: `retain()` now writes to a RUN-UNIQUE
subdir `<target>/<UTC-ts>_<input_hash[:12]>/` (`_run_unique_dir`, `engine/ledger_differential.py`),
`mkdir(..., exist_ok=False)` so a same-second/same-EDB collision fails loudly rather than
silently reusing a path. Both banked toy records were rescued from git history (`814bd79`) and
the working tree and now live side by side: `engine/docs/ledger-marriage/derivations/toy/
20260709T104914Z_8e3c0edcaa8a/` (first run, restored verbatim from `814bd79`) and
`.../20260709T112043Z_f6816fb75951/` (the second, previously-uncommitted run). No test
depended on the old flat layout (`engine/tests/` has no reference to `RETENTION`/`retain(`);
full suite re-run clean modulo two pre-existing, unrelated `test_ledger_acts.py` date-fixture
failures (reproduced identically before this change, via `git stash`).

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

## Toy run 1 findings (all-Sonnet session, 2026-07-09, inspector report + salvage)

1. **Claim/artifact drift, caught live**: the QEUBO smoke script was edited 16→3 dims AFTER
   its 16-dim evidence doc was written (mtime 13:45 vs 13:04), no ledger row/BACKLOG disclosure
   — the artifact in the tree no longer reproduced the recorded evidence. Canonical instance
   for the commission/conformance instrument (ADR-0013 R5); becomes its first fixture.
2. **Run 1's deliverables were never committed and were wiped from disk** (untracked docs/,
   index.html, scripts/ deleted at run-2 start) while five "task N complete" decisions assert
   finished work. Contents survive in the session transcript, salvaged to
   ephemera/toy-run1-salvage/ — UNTRACKED at the time of this finding, contrary to the "local,
   gitignored" claim this line originally made (`.gitignore` covered only `ephemera/session-*`,
   which does not match this path; corrected 2026-07-09). Interim protection added:
   `ephemera/toy-run1-salvage/` is now `.gitignore`d (survives `git clean -fd` without `-x`,
   unlike a plain untracked dir), pending the maintainer's disposition ruling (commit vs
   local-only). Fix shape for run prompts + eventually a gate: a completion claim on a
   file-producing task requires the file to be committed.
3. **Stamp-verified independence is architecturally unreachable from same-session subagents**
   (launch-dir-scoped hooks; Task-tool subagents share the dir). validate_independence's
   refusal taught correctly; the run honestly fell back to self-review every time, disclosed
   in-line, but never escalated the limitation (ADR-0014 gap worth noting). Design fix, cheap:
   the reviewer runs as a SEPARATE Claude Code process in toy-project (second terminal or
   claude -p), which fires the interceptor → distinct verified stamp → technical independence
   witnessed. The ephemeral-principals pattern (AGENTIC-PATTERNS 11) makes this the norm.
4. **Governed-set hole**: only *.py governed; index.html (the actual product wiring) and all
   docs bypassed the ledger discipline entirely. Instance decision: widen toy's
   governed_files.json (*.html at minimum) between runs.
5. **evidence column unused**: all evidence narrated in statement/rationale prose; the typed
   field NULL everywhere. led ergonomics candidate (--evidence exists; prompts should demand it).
6. Fix-point loop: 11 denies/11 allows/4 boundary closes in run 1's journal; zero
   teaching-failures (every unretried deny was a deliberate negative-control probe).

### Correction to finding 1 above (maintainer, 2026-07-09)
The 16→3 dims edit was the MAINTAINER's own manual test (verify the mechanism works where it
should, d=3 — it does; d=16 non-convergence unsurprising), not agent drift. Finding 1's
conduct claim is withdrawn. The residual, smaller lesson: a human's manual edit is invisible
to the ledger by construction (hooks see agent tool-calls only), so evidence docs can go stale
against human edits with no record — a known, acceptable bound worth one line in HOOKS.md.

### Correction to finding 3 above (Fable re-derivation from source, 2026-07-09)
"Architecturally unreachable" was WRONG — overstated by conflating two causes. True mechanism:
(a) cross-repo delegated agents miss the interceptor entirely (hook config is launch-dir-scoped
— real, but irrelevant to real use); (b) THE ACTUAL BUG: stamp_intercept.py's matcher
(_is_ledger_psql) requires the literal token `psql` naming the db — `./led ...` hides psql
inside the script, so every led-mediated write is passed through UNSTAMPED even in
toy-launched sessions. Evidence: rows 10-14 (raw psql, run 0) are stamp_verified=t/'main';
every led-written row unstamped. led is an accidental instance of the docstring's own
"script-evasion tripwire". Fix (post-run-2, hooks frozen meanwhile): extend the matcher to
match led invocations; the existing `export PGOPTIONS` mechanism inherits into the script's
psql with zero led changes. After the fix, independence='technical' is witnessable in ONE
toy session (main-thread author vs subagent reviewer = distinct agent ids per hook context).
Separate-process reviewer remains the stronger optional form, not a requirement.

## Independence investigation verdict + s21 candidate (Fable agent, 2026-07-09)

VERDICT: stamp-verified independence='technical' WAS witnessed passing in prior work — wmb
(e17) reviews 17/18 and qbx (e18) reviews 8/14/15, all both_stamped=t/same_invocation=f, gate
live at insert (pg_trigger confirmed); refusal path witnessed alongside (wmb 12, qbx 6/7).
e17's passing reviewer was a SAME-SESSION Task subagent — parent launched in the hook-wired
dir, reviews via direct psql (the matcher's one interceptable shape; arm.sh check (d) verified
the idiom pre-run). Toy's gap = launch topology + the led wrapper (pre-registered in s17
LIMITS as the script-evasion class). Mechanism difference, NOT a regression. Residual
uncertainty: agent_id presence in hook input on Claude Code 2.1.205 not re-probed (e-series
ran on a version two days older); 2-minute shakedown filed as part of the matcher-fix batch.

**s21 candidate — distinctness keys on stamp_agent ALONE**: validate_independence and
review_stamp_distinctness never consult stamp_session, so two different sessions' main
threads (both agent='main') are indistinguishable — a genuinely independent second-session
main-thread review claiming technical is FALSELY REFUSED as same-invocation. Fails safe, but
forecloses the "separate interactive reviewer session" idiom as the DDL stands (e18's
reviewers passed only as subagents). Fix shape: key distinctness on the (stamp_session,
stamp_agent) PAIR in both the trigger and the view; future sNN delta, needs maintainer ruling.

### s21 — AUTHORED + SCRATCH-WITNESSED (Sonnet, 2026-07-09); APPLY PENDING MAINTAINER RATIFICATION

DDL: `kernel/lineage/s21-session-aware-distinctness.sql`, authored from
`design/S21-SESSION-AWARE-DISTINCTNESS.md` in the s20 house style (header/closure-statement/
parameterization, additive-on-s15/s17/s19/s20, per-function `SET search_path`). Covers BOTH
defects the spec names: (1) `validate_independence` + `review_stamp_distinctness.same_invocation`
recomputed on the `(stamp_session, stamp_agent)` PAIR, NULL-half = not distinct, fail-safe; (2)
the s19 residue fold-in — `validate_enacts/review/amends/answers` each gain
`SET search_path = :"schema", pg_temp`. Universe grep (whole tree, not just kernel/lineage/) found
ONE additional stamp_agent-alone consumer NOT coverable by this DDL: `instruments/
review_fixpoint.py`'s `FpRow`/`review_fixpoint_verdict` (+ its caller `review_fixpoint_close.py`)
carries `stamp_agent` only, no `stamp_session` — the identical session-blind shape, in a Python
instrument reading the ledger directly rather than a SQL trigger/view. Filed as its own entry below
(fix or file, ADR-0013 Rule 4); not fixed here (out of a DDL-only touch's scope, per ADR-0004).

SCRATCH-WITNESSED in the TOY db (never toycolors/live; schema `s21probe`/`s21probe_kernel`, role
`s21probe_rw`, dropped after each run). `kernel/fixtures/s21_session_aware_fixture.py` runs the
spec's witness protocol items (1)-(5) as one automated, rerunnable script; observed GREEN, one run,
both polarities where applicable:

```
ITEM 5 RED  (pre-s21, no SET search_path): ok=False
    CONTEXT:  PL/pgSQL function s21probe.validate_review() line 8 at SQL statement
    [full message: ERROR:  relation "ledger" does not exist — the s19 residue, reproduced]
ITEM 5 GREEN (post-s21, no SET search_path): ok=True
    INSERT 0 1
ITEM 1 (same-session s1/main vs s1/sub-xyz): insert ok=True, same_invocation='f'
ITEM 2 (cross-session s1/main vs s2/main): insert ok=True, same_invocation='f'
    [the retired false refusal: agent='main' both sides, session differs -> DISTINCT]
ITEM 3 (same pair s1/main vs s1/main): insert ok=False
    CONTEXT:  PL/pgSQL function validate_independence() line 20 at RAISE
    [ERROR: "...the SAME invocation (session=s1, agent=main) wrote both it and the row it regards..."]
ITEM 4a (unstamped reviewing row): insert ok=False
    CONTEXT:  PL/pgSQL function validate_independence() line 11 at RAISE
    [ERROR: "...must carry a VERIFIED interception stamp..."]
ITEM 4b (verified reviewer, NULL-stamp target): insert ok=False
    CONTEXT:  PL/pgSQL function validate_independence() line 20 at RAISE
    [ERROR: "...the SAME invocation (session=s3, agent=distinct-agent)..." -- NULL-half on the
     TARGET forces not-distinct even though the reviewing row is itself verified+stamp-distinct
     in the ordinary sense; fail-safe, never fail-open]
# S21 FIXTURE GREEN -- (session,agent)-pair distinctness (items 1-4) and the s19 residue cure
# (item 5) all witnessed, both polarities where applicable.
```

APPLY ONE-LINER (pending maintainer assent; NOT run against toycolors or any live schema by this
pass — spell out every `-v` var explicitly, never bare, per the lineage's standing rule):

```
psql -h 192.168.122.1 -d toy -v schema=toycolors -v kern=toycolors_kernel \
  -f kernel/lineage/s21-session-aware-distinctness.sql
```

Engine tests unaffected (s21 touches only `kernel/lineage/`, no engine code); `engine/tests` re-run
clean modulo the two pre-existing, unrelated `test_ledger_acts.py` date-fixture failures noted above.

## `instruments/review_fixpoint.py` reads `stamp_agent` alone — the SAME session-blind distinctness defect s21 fixes, one register up (found in passing, 2026-07-09)

Class: identical to s21 defect 1 (BACKLOG "s21 candidate" above), one level up the stack. Found
while grepping the full tree for other `stamp_agent`/`same_invocation` consumers per
`design/S21-SESSION-AWARE-DISTINCTNESS.md`'s closure-statement universe clause — not part of this
session's assigned DDL task, filed per CLAUDE.md's engineering-responsibility clause (a hazard
within reach, named loudly, not routed around) and ADR-0013 Rule 4 (fixed or filed, never
narrated-and-left). `instruments/review_fixpoint.py`'s `FpRow` dataclass carries `stamp_agent: str`
with NO `stamp_session` field; `review_fixpoint_verdict`'s two joins — the stamp-distinct check
(`r.stamp_agent != author_stamp`) and the first-contact check
(`o.stamp_agent == rev.stamp_agent and o.id < rev.id`) — both decide distinctness from `stamp_agent`
ALONE. A genuinely fresh, cross-session criterion-reviewer whose invocation also stamps
`agent='main'` (the common case for any interactive main-thread session) would be mis-scored: NOT
stamp-distinct from a `main`-authored artifact, and/or NOT first-contact if any earlier `main`-agent
row exists in the unit — exactly the false-refusal-of-an-honest-reviewer shape s21 fixes for
`validate_independence`/`review_stamp_distinctness`, here silently accepting the WRONG verdict
(RED where GREEN is owed) rather than refusing loudly, because this is Python arithmetic, not a
DB-side refusal — arguably a worse failure mode (silent miscategorization vs. a loud REFUSE).
`instruments/review_fixpoint_close.py`'s `_SQL` is the root: `SELECT l.id, l.kind, l.regards,
rd.verdict, l.stamp_agent, ...` never selects `l.stamp_session`. NOT fixed here: this is a Python
instrument change (thread `stamp_session` through `FpRow`, the SELECT, and both joins in
`review_fixpoint.py`, mirroring s21's pair rule), not a `kernel/lineage/` DDL touch, and this
session's mandate was specifically the DDL file — a genuine type whose blast radius (two files,
FpRow's shape, both call sites) is deferred per ADR-0000's Exceptions clause, filed rather than
silently left. Fix shape: add `stamp_session: str` to `FpRow`, select `l.stamp_session` in
`review_fixpoint_close.py`'s `_SQL`, and recompute both joins on the `(stamp_session, stamp_agent)`
pair (NULL-half = not distinct, same fail-safe rule s21 states) — the exact `_run_unique_dir`-style
type-driven fix, one register up from the DDL.

## Ruling: one world per run (maintainer, 2026-07-09, "many-worlds" argument)

A run's subject must not see sibling runs' history — branches share only the branch point
(the kernel apply: schema/triggers/secret/roles), never each other's ledgers. ledger_current/
T_now over a mixed ledger computes "in force" ACROSS universes — epistemically wrong for the
in-world agent (cribbing, bias, cross-world in-force leakage). Precedent: the e-series already
practiced this (one db per experiment: vsr/hvn/wmb/qbx); toy deviated by reusing toycolors
across runs 0-2. Consequences: (a) per-run schema becomes the DEFAULT for experiment runs —
scaffold/new-project.sh grows a new-world mode (apply watermark chain + s20 into runNN
schemas, fresh deployment.json); (b) pickup/bootstrap queries are branch-local by
construction; (c) cross-run comparison is the analyst layer's job, from outside, via the
engine over any named world; (d) run 2 is RECORDED as contaminated by run-1 visibility —
results read with that caveat; run 3 starts in a fresh world. Never flush: worlds are opened,
not emptied.

## Assent batch outcomes (maintainer, 2026-07-09, verbatim "All as recommended" + specifics)

1-2. s20 apply + hooks-before-run-2: executed under standing authority, now ratified.
3. OPUS-READINESS: RATIFIED as written.
4. s21: RATIFIED (spec design/S21-SESSION-AWARE-DISTINCTNESS.md; delta+witness in flight).
   Under delegated driving, s21 will be APPLIED to toycolors and the run3 world once its
   scratch witness lands green — ratified content, mechanical apply, departure imminent.
5. Succession rule: option (b) RATIFIED — codified in CLAUDE.md ORCHESTRATION.
6. Ephemera: local-only, none committed — CLAUDE.md auditability section amended; salvage
   dir stays gitignored; nothing deleted (still local evidence).
7. NO PUSH until the project is usable by a non-expert operator without consulting a
   frontier model ("even an idiot like me... without the brightest LLM on the planet") —
   that bar is the OPUS-READINESS/pickup/brief work's acceptance criterion, decided by the
   maintainer trying it.

## Integrated hooks+deployment batch: landed (2026-07-09, under the standing run1→s20→run2 sequencing + delegated driving authority)

All seven items of this batch witnessed against live systems (autoharn `next`, toy-project
`master`); details/verbatim output live in the session record, summarized here per-item:

1. **Stamp matcher fix** (`hooks/stamp_intercept.py`): the matcher now ALSO recognizes a
   command whose first word (after optional `VAR=value` prefixes) is `./led`, bare `led`, or a
   path ending `/led`, alongside the existing raw-psql shape — closing the "Correction to
   finding 3" gap (every `led`-mediated write in run 1 was silently unstamped). Hook-I/O
   simulations witnessed both matches, both negative controls (`echo led is a word`;
   `ledger-tool --status`), and the existing raw-psql path unaffected.
2-3. **PGHOST env override + deployment.json consumption** (`hooks/pretooluse_change_gate.py`,
   `hooks/stamp_intercept.py`): both hooks now resolve db/host/schema-derived-ledger from a
   project's `deployment.json` (located via the hook input's own `cwd`, falling back to
   `os.getcwd()`, mirroring `stamp_provenance.py`'s existing convention), with a neutral env-var
   family (`LEDGER_DB`/`LEDGER_HOST`/`GATE_LEDGER`/`GATE_SUBJECT_ROOT`/`GATE_STATE`/
   `GATE_JOURNAL`) overriding it, and the old `E13_GATE_*`/`E13_SUBJECT_ROOT`/`STAMP_DB` names
   kept working as silent deprecated aliases. Re-ran the change-gate hook-I/O simulations
   (allow / window-reuse / boundary-close-then-deny / fail-closed-on-DB-error) against a scratch
   project dir with only a `deployment.json` and NO env vars at all — all four paths reproduced
   byte-identically to the pre-existing env-var-driven behavior, and a bad `LEDGER_HOST`
   produced the expected fail-CLOSED `gate_error` deny, proving the host override is genuinely
   live. `toy-project/.claude/settings.json` updated to the neutral env names.
4. **s20 applied to `toycolors`** (the live one-liner, idempotent — grants/views were already
   present, confirming a prior pass had reached this db; re-run produced a clean
   `GRANT`/`CREATE VIEW`/`CREATE VIEW`). Post-conditions witnessed: `review_gap` readable by
   `toycolors_rw` with no permission error; `ledger_current`/`countersigned_in_force` both carry
   all five `stamp_*` columns; a full cross-principal obligate → review-gap-shows-debt →
   countersign → debt-cleared round trip (ledger rows 71-73, prefixed "exercise: s20 apply
   witness"); the `obligation_not_self_assigned` CHECK now genuinely reachable (self-assigned
   obligate refuses on the CHECK, not a grant wall).
5. **toy-project wiring**: `deployment.json` written; `pickup` instantiated from
   `bootstrap/templates/pickup.tmpl`; `governed_files.json` widened to `["*.py","*.html"]`
   (BACKLOG "toy run 1 findings" item 4); `./pickup` run FOR REAL post-s20 — REVIEW-DEBT
   returned real rows, not `BLOCKED: pre-s20 grants`. `.claude/HOOKS.md` updated: pickup
   section (real output), stamp-matcher-fix note, governed-set-change note, s20-resolution note
   superseding the old grants-gap finding, doc-witness convention header, and an explicit
   "what remains UNWITNESSED" closing section.
6. **Stamped-led witness**: simulated `stamp_intercept.py`'s stdin JSON for
   `./led decision "exercise: stamped-led witness"` with a fake `session_id`/`agent_id`,
   executed the REWRITTEN command, read the row back — `stamp_session='fable-batch-sim'`,
   `stamp_agent='fake-agent-xyz-001'`, `stamp_verified=t` (row 74) — the first `led`-mediated
   row in this project's history to carry a genuinely verified stamp. UNWITNESSED, named
   explicitly: Claude Code itself populating `agent_id`/`cwd` in a REAL toy-launched session
   (needs run 2's first minutes, not a hand-built JSON).
7. **`bootstrap/new-project.sh --new-world <world>`**: derives `--schema`/`--kern`/`--role`
   from one world name (explicit override still honored), applies
   `high_watermark_1.sql` + s20 with every `-v` var spelled out, seeds the stamp secret
   idempotently (mirrors `drive/arm.sh` ruling 43's own guarded pattern), and writes
   `deployment.json` — automating the operator step HOOKS.md otherwise documents as manual.
   Witnessed end-to-end against `toy` as world `run3` (schema `run3`/`run3_kernel`/`run3_rw`):
   kernel+s20 applied clean, `author` principal auto-seeded by `s15-schema.sql`, secret
   provisioned (`.claude/secrets/stamp_secret.hex`, 65 bytes), `./led decision`/`./judge`/
   `./pickup` all run clean against the fresh, empty ledger (row id starts at 1 — genuine
   world isolation). Scaffold left at `/home/bork/w/vdc/1/run3` (moved off `/tmp` for
   persistence) — **run3 IS run 3's clean room**, per the one-world-per-run ruling above; s21
   (once its own scratch witness lands, per "Assent batch outcomes" item 4) applies here too,
   not re-scaffolded.

Friction/notes: `led obligate`'s error message for the self-assigned refusal is the raw
Postgres CHECK-violation text (`ERROR:  new row for relation "countersign_obligation" violates
check constraint "obligation_not_self_assigned"`), not the friendlier trigger-raised message
the pre-s20 HOOKS.md excerpt implied — cosmetic, the refusal itself is correct and was the
whole point of the CHECK. The harness's own auto-mode classifier refused a literal
`SELECT secret FROM stamp_secret` negative-control read (credential-materialization guard) —
respected rather than routed around; the item-6 stamped round trip is strictly stronger
evidence the secret is correctly wired anyway (a bit-exact HMAC match end to end).

### s21 apply status (2026-07-09, end of Fable session)
Authored, scratch-witnessed green, RATIFIED. Apply to toycolors/run3 NOT yet run: the
executing agent's permission layer refused (its dispatch predated ratification; it correctly
declined to treat an agent message as consent — the refusal honors "applying stays the
maintainer's act"). The two apply one-liners are in the run-2 walkthrough (transcript) and
below; each expects CREATE FUNCTION/TRIGGER/VIEW lines, no ERROR. Optional before run 2
(same-session technical independence passes without s21; s21 adds cross-session correctness
+ the s19 residue cure):
  psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 -v schema=toycolors -v kern=toycolors_kernel -f kernel/lineage/s21-session-aware-distinctness.sql
  psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 -v schema=run3 -v kern=run3_kernel -f kernel/lineage/s21-session-aware-distinctness.sql
After applying, a one-line BACKLOG note "s21 APPLIED <date>" keeps the record true.

## Doc-witness fix: "how was run3 created?" + a hazard the reconstruction turned up (2026-07-09)

Maintainer finding: run3 carried no provenance of its own creation, `WALKTHROUGH.md` had zero
mentions of `--new-world`, and an operator could not open world 4 without reading script source
(the "Operator-doc steps must carry their witness" class, above). Fixed:

1. **Reconstructed run3's exact creation command** from `bootstrap/new-project.sh` source +
   `deployment.json` + this file's own item-7 entry above (confirms "moved off `/tmp`"):
   `bootstrap/new-project.sh /tmp/run3_dest --new-world run3 --db toy --host 192.168.122.1 --name
   run3`, then `mv /tmp/run3_dest /home/bork/w/vdc/1/run3` (evidence: every templated file under
   run3's `.claude/` still baked in `/tmp/run3_dest`; the directory's own SELinux context is
   `user_tmp_t`, `/tmp`'s label, not `/home`'s). Recorded, honestly marked RECONSTRUCTED (not a
   captured transcript), in `run3/.claude/HOOKS.md`'s new PROVENANCE header.
2. **A real hazard fell out of that reconstruction, in reach of the same file, fixed rather than
   routed around**: because `.claude/settings.json`'s two hook commands and `.claude/HOOKS.md`
   bake `<dest-dir>`'s absolute path in at scaffold time, the post-move run3 had every one of
   them still pointing at `/tmp/run3_dest`. Consequence, verified by direct invocation of
   `hooks/pretooluse_change_gate.py` both ways: with the stale `SUBJECT_ROOT`, an edit to a
   governed `.py` path under the REAL run3 directory returned exit 0 with no output — the change
   gate was silently defeated, matching no file under the real project at all — and the stamp
   interceptor's `STAMP_SECRET` path pointed at a file that no longer existed, so writes would
   have passed through unstamped despite a secret genuinely being provisioned (at the new,
   correct path). Fixed in place: `run3/.claude/settings.json` and `.claude/HOOKS.md` now say
   `/home/bork/w/vdc/1/run3`; re-verified the gate now correctly denies the same edit
   (`permission denied` / `needs_entry`, not a silent pass). `led`/`judge`/`pickup` themselves
   were never affected — each resolves its own directory at runtime, not a baked one.
3. **A second, smaller doc/reality mismatch in the same template**: `HOOKS.md.tmpl`'s stamp-secret
   section always said "one manual step remains ... UNWITNESSED", even for `--new-world` scaffolds
   that had ALREADY auto-provisioned the secret — an operator trusting that stale claim and
   re-running the seeding block would have ROTATED an already-live secret, invalidating every
   stamp written under it. Fixed: the scaffold now writes a mode-appropriate status line
   (`__STAMP_SECRET_STATUS__`, computed in `new-project.sh` from whether `--new-world` fired).
4. **Scaffold now self-documents provenance** (checked feasibility, was trivial — templating is
   already the pattern `led`/`judge`/`pickup` use): `bootstrap/new-project.sh` captures its own
   real argv + UTC timestamp BEFORE argument parsing consumes `"$@"`, computes which kernel
   lineage it applied (or didn't), and writes all three into a new PROVENANCE header at the top
   of every scaffolded `.claude/HOOKS.md` — created-at, exact command, world schema/kern/role,
   lineage chain, an s21-status pointer to this file, and a `./pickup` orientation pointer. No
   future world should need script-source reconstruction the way run3 did. Witnessed both modes
   (`--new-world` and classic `--schema/--kern/--role`) on throwaway probe worlds
   (`docprobe2`/`docprobe3`/`docprobe4`, torn down after — `DROP SCHEMA ... CASCADE` +
   `DROP OWNED BY`/`DROP ROLE`, mirroring the s21probe teardown pattern).
5. **`WALKTHROUGH.md`** gained a "4. Opening a new world (one world per run)" section (the
   one-world-per-run why, the exact `--new-world` command with every flag, a real witnessed
   capture from a throwaway `docprobe` world torn down after, what success looks like, the s21/
   future-delta-is-an-explicit-operator-act reminder, a pointer to `./pickup` for orienting in
   any world, and the directory-move hazard above called out so the next operator sees it before
   tripping over it) and **`bootstrap/QUICKSTART.md`** gained a one-paragraph pointer to it.

Not touched: `toycolors`/`toy-project` (per scope); s21 was not applied anywhere by this pass.

## Run-2 integrity finding: world born with dead hooks; kernel fail-safe held; one rule breach filed (2026-07-09)

Timeline (all 2026-07-09 local time, pid/mtime-witnessed):
- ~14:53 — run3 scaffolded at `/tmp/run3_dest` and `mv`'d to its final path (reconstruction in
  the entry above); both hook commands in `.claude/settings.json` baked the pre-move path.
- 15:15:02 — the maintainer launched run 2 in run3 (pid 694135, `/proc` cwd-witnessed). Claude
  Code snapshots hook config at session start, so this session runs its ENTIRE life with the
  change gate FAIL-OPEN (stale `SUBJECT_ROOT` matches no real file — verified both polarities by
  the doc pass above) and the stamp interceptor inert (secret path nonexistent → writes pass
  unstamped).
- In-run conduct (run3.ledger rows 16–20, maintainer-pasted): the kernel layer held exactly as
  designed — `validate_independence` refused every technical claim on unverified stamps; the
  subject agent fell back to MARKED self-review, flagged the misconfiguration as a ledger
  decision (row 20), and did not fix governance infra outside its scope. Defense in depth
  witnessed in the wild: hook layer dead, kernel layer fail-safe, agent conduct correct.
- 15:27–15:28 — the documentation pass repaired `run3/.claude/settings.json` + `HOOKS.md` in
  place, 12 minutes AFTER the live session launched. That is a breach of the standing rule
  (never modify a user project while a live session runs there), filed here against THIS
  session's commissioning: the constraint list named toy-project but not run3, because run 2 had
  not started at commission time and nobody re-checked liveness at edit time. Functional damage
  assessed nil (snapshot semantics: the live session's captured config was unchanged by the
  edit; the fix takes effect next session). Standing lesson: LIVENESS IS CHECKED BY THE EDITOR
  AT EDIT TIME (`pgrep` + `/proc/<pid>/cwd`), never assumed from the commission.

Standing caveat on run 2's evidence: every run3.ledger row from this session is unstamped and
ungated; independence was never attainable. The run remains valid evidence for decomposition /
prereg / self-review-fallback conduct and for the kernel fail-safe; it is NOT the working-stamps
witness run 2 was commissioned to be — that objective moves to a fresh world (one-world ruling;
the scaffold now self-documents, and with hook fix 1 below a moved instance becomes loudly
taught instead of silently defeated).

Hook fixes filed (Sonnet-executable; do NOT edit `hooks/` until no wired session anywhere is
live — every wired project re-executes these scripts from this repo on each hook invocation):
1. `pretooluse_change_gate.py` — if `SUBJECT_ROOT` does not exist on disk, DENY loudly with
   teach-text instead of governing nothing (fail-open → fail-closed). Seen-red fixture required.
   STATUS: built, commit 296ce6d (seen-red/change-gate-subject-root/, 5 cases, real captured
   output both polarities).
2. `stamp_intercept.py` — if `STAMP_SECRET` is configured but the file is missing/unreadable,
   DENY ledger writes with the seed-command teach-text instead of passing them unstamped (the
   silent-unstamped class, now twice witnessed: run 1, run 2).
   STATUS: built, commit 296ce6d (seen-red/stamp-intercept-secret/, 5 cases, real captured output
   both polarities; also closed a related hazard found in-flight — a present-but-EMPTY secret file
   used to silently produce a valid zero-length HMAC key rather than an honest missing-secret
   disposition).

For the record, resolving the doc pass's two flagged anomalies: `design/WORK-ITEM-DECISION-MEMO.md`
is Fable-authored this session (the parent session's own write landing mid-pass — no anomaly);
the empty `/home/bork/w/vdc/1/run_3/` (underscore) dir looks like a typo artifact of run3's
creation — maintainer may `rmdir` it.

## Maintainer ruling: self-application — the harness's own ops must meet the harness's bar (2026-07-09)

Ruling, issued after run 2 and codified in CLAUDE.md ORCHESTRATION: the run-2 world (dir
"run3") was broken from the start by manual munging that should have been scripted from the
start; operator procedures of the form "do 1. [pages of SQL], do 2. [pages of bash]" are
condemned as unprofessional. Two parts, binding on every orchestrator including Fable:
(1) no operator step ships as prose + hand-paste where a scripted, witnessed verb is possible —
"why is this not a verb?" is now the first question every walkthrough must answer;
(2) every orchestrator choice or judgment is explained on the record at the moment it is made.

Honest self-assessment attached to the filing: the scripted replacements in flight today
(apply-delta, s21-in-birth-chain, fail-closed hooks, self-documenting scaffold) were each
commissioned REACTIVELY, after its manual counterpart had already bitten. The ruling makes
proactive scripting the default stance, not the post-incident remedy.

Newly filed consequence (Sonnet-executable once the in-flight bootstrap changes land):
**starting a run becomes a verb** — today it is still a walkthrough (hand-register a reviewer
principal, hand-paste a six-point governance prompt). Target shape: the scaffold (or a
`new-run` helper) registers the standard principals and emits/queues the governance prompt, so
opening AND starting a run is one witnessed command each, or one total.

State note: the maintainer removed `/home/bork/w/vdc/1/run3/` (and `run_3/`). The run-2
EVIDENCE is unaffected — the ledger lives in db `toy`, schema `run3`, not in the deleted
directory. Full outside-inspection of run 2 is DEFERRED (decision + reason: its primary
objective, working stamps, was structurally unmet from birth, and the conduct findings are
already extracted and filed above — a full pass would spend turns on a known-degraded run).

## apply-delta + s21-in-birth-chain: landed (2026-07-09, closing the two "in-flight" items above)

Both scripted replacements the ruling above names as in-flight are now landed and witnessed.

1. **`bootstrap/apply-delta.sh <world-dir> <delta.sql>`** (new) — the scripted, confirmed apply
   step the ruling demands in place of "do 1. [pages of SQL]". Resolves db/host/schema/kern from
   `<world-dir>/deployment.json` (`filing/deployment_record.py`, refuses loudly with its own
   teach-text on a missing file/key — never guesses), prints the fully-resolved `psql -v ...`
   command before doing anything, requires the operator to type the schema name back (a mismatch
   aborts, no `--yes`), runs with `ON_ERROR_STOP=1`, and on success appends a dated `APPLIED`
   line to the world's `.claude/HOOKS.md` PROVENANCE section (never creating one if absent) plus
   a BACKLOG-note reminder. On `psql` failure it prints the output verbatim and states plainly
   that the delta is NOT transaction-wrapped (a mid-file error can leave a partial apply) —
   instructing not to re-run blind. Witnessed on a throwaway probe (`deltaprobe`/
   `deltaprobe_kernel`/`deltaprobe_rw`, `toy` db, scaffolded classic-mode on s15/s17/s19/s20 only
   — a genuine pre-s21 world): wrong-confirmation abort (no db change, verified by column
   absence before/after), missing-`deployment.json` refusal, a deliberately-broken delta's
   psql-failure path, and the real positive apply (CREATE FUNCTION/TRIGGER/VIEW, no ERROR;
   `review_stamp_distinctness` gained `review_stamp_session`/`regards_stamp_session`; HOOKS.md
   PROVENANCE got the APPLIED line). Torn down after (`DROP SCHEMA ... CASCADE` both schemas +
   `DROP OWNED BY`/`DROP ROLE`). **Not** applied to `toycolors`/`run3` by this pass — those two
   one-liners in the "s21 apply status" entry above remain the maintainer's own act.
2. **`bootstrap/new-project.sh --new-world` now applies s21 automatically**, after s20, in the
   same call (high_watermark_1.sql → s20-obligation-grants-and-view-refresh.sql →
   s21-session-aware-distinctness.sql) — s21 was RATIFIED (see "s21 apply status" above), so
   folding it into every new world's birth lineage is no longer a lineage-authoring act, only a
   scaffold-wiring one. The scaffold-written `.claude/HOOKS.md` records this in its PROVENANCE
   header (`__LINEAGE_CHAIN__` now names s21; the former static "NOT applied by any scaffold
   mode" bullet is now a mode-aware `__S21_STATUS__` computed per invocation, and also points at
   `apply-delta.sh` for any future delta). Classic (`--schema/--kern/--role`) scaffold mode is
   unchanged — it applies no kernel lineage at all, s21 included. Witnessed end to end on a
   second throwaway probe (`deltaprobe2`, `toy` db): clean apply (no `psql` errors), the
   PROVENANCE header naming `s21-session-aware-distinctness` in the lineage chain, `\df
   deltaprobe2.validate_independence` showing the function, `review_stamp_distinctness`'s
   columns carrying `review_stamp_session`/`regards_stamp_session` from birth, and a live
   `./led decision` → `./led --recent 1` → `./judge` (AGREE) → `./pickup` round trip against the
   fresh world. Torn down after, same as above.

`WALKTHROUGH.md`'s "Opening a new world" section and `bootstrap/templates/HOOKS.md.tmpl` updated
to match (real captured output, not the stale `docprobe`/pre-s21 capture); `bootstrap/
QUICKSTART.md` left untouched — it neither states the `--new-world` lineage chain nor the s21
status (its own scratch-kernel demo is a separate, already-accurate s15-through-s19 hand walk),
so there was nothing stale to fix there.

## Run-5 forensics (2026-07-10, mid-run snapshot): back-filled ledger + matcher evasion 3.0; s21 witnessed live; two hook fixes queued

Timing correlation (Sonnet forensic pass, read-only, transcript ~/.claude/projects/-home-bork-
w-vdc-1-run5/ vs live run5.ledger; session was LIVE — 38-row snapshot):
1. **Contemporaneity failed twice.** Main thread: 8m23s of witnessed work (23 tool events incl.
   4 curls against the provisioned QEUBO service) with ZERO rows, then 19 rows in 89.4s (18 in
   36.1s). Reviewer subagent: 5m07s silent investigation, then 19 review rows in 0.43s via a
   generated run_reviews.sh executed as one Bash call. The ledger is a retroactive diary, not a
   permit log. FIX QUEUED (post-run5-exit, hooks/ frozen while wired sessions live):
   **permit-to-work gate** — no open+claimed work item in the world's ledger ⇒ substantive tool
   calls (Write/Edit anywhere in the world, mutating bash) DENY with teach-text naming
   `./led work open`/`claim`. s22 supplies the queryable state; the change gate is the
   enforcement point; deny→teach→retry is the proven loop.
2. **Stamp interceptor: third run, third distinct failure shape — enumeration fails open
   (ADR-0011 Rule 4).** Config correct, hook alive: fired exactly TWICE, both on read-only
   commands; ZERO times on any of the 38 writes. Evasion shapes this run: `cd run5 && ./led …`
   (first word cd) and `cat > run_reviews.sh …; bash run_reviews.sh` (first word cat). All 38
   rows stamp_verified=false, stamp columns NULL. FIX QUEUED (post-run5-exit): **delete the
   matcher** — stamp_intercept injects PGOPTIONS unconditionally into every Bash call in a
   wired world (harmless to non-psql descendants, inherited by generated scripts); the
   enumeration and its evasion class cease to exist. Both fixes are strictly fail-safe and
   class-covered (CLAUDE.md class-ratification + sub-constitutional hook work) — no maintainer
   question pending.
3. **s21 witnessed live for the first time, in anger:** the reviewer's initial `technical`
   claim was REFUSED by validate_independence ("SAME invocation wrote both"), burning ledger id
   20 in the rollback (sequence gap is the refusal's fingerprint, not a deletion — append-only
   trigger blocks UPDATE/DELETE). The reviewer then honestly downgraded all 19 reviews to
   marked self-review, citing the unstamped rows and the NULL-half fail-safe rule verbatim.
   Kernel fail-safe + agent conduct: both held, again, with the hook layer dark.
4. No backdating found: ledger ts strictly increasing, every row consistent with the transcript
   action that produced it; row content matches witnessed work. Honest-but-late, unstamped.
5. Standing gap re-confirmed by run 4's abort (2026-07-10): the scaffold captures governance
   but not the TASK BRIEF — the operator's kickoff prompt lives nowhere durable. Fix candidate:
   `--task` flag / TASK.md slot at world birth. Sonnet-sized, unqueued (bootstrap/ is not
   frozen; can build any time).
   **DISPOSED same day, maintainer ruling: the task is the USER'S work to specify at startup —
   it does not belong in CLAUDE.md or any scaffold-baked file. No TASK.md, no --task flag; the
   task-brief candidate above is withdrawn. (The agent's first ledgered act naturally quotes
   the task via its opening question/decision rows, which is durable enough for the record.)**

## Run-7 phase-1 verification (2026-07-10): full mechanized loop closed live; two findings; one self-correction

Ledger/git/transcript verification (Sonnet, read-only) of run 7's completion claims:
- **27/27 rows stamp_verified (run 5: 0%)**; technical independence attested both directions on
  distinct (session, agent) pairs (s21 e17-shape: same session, distinct stamped subagent —
  cross-session independence remains live-unwitnessed). Work items: opened→claimed→closed in
  order, commit witnesses exist and match (`7adaf2b`); the one raw-psql call in the transcript
  was a read-only introspection — every mutation went through led, so the s23
  claim-before-close-in-kernel candidate keeps prudential status only, no witnessed need.
- Acceptance criteria pre-registered (row 21) 18s before the first Write; result row 23 cites
  it via the queryable `refs` edge (row 22 left refs empty — minor citation inconsistency).
- **Stop gate fired live for the first time** (silent-allow; block path still fixture-only).
  Mutation observer silent (consistent with clean conduct; warn path still fixture-only).
  Demurral hook exited in 78ms with classifier off — the costed-off default works; no billing.
- **Self-correction (citation currency, checklist item 6, violated by the orchestrator):** the
  "first-ever live stamped independence" framing was WRONG — run 6's ledger shows the same
  shape ~2h earlier (hooks execute from autoharn per invocation, so matcherless stamping
  reached every wired world the moment it was committed). Run 7's real novelty: first run with
  the FULL mechanism set active and the loop closed by committed deliverables.
- **Finding 1 — review_gap over-catch:** the gap view caught the reviewer's own countersign
  rows under an obligation scoped to the decomposition, forcing an author counter-countersign
  round (SoD held; pairs distinct; `led obligate revoke` existed and went unused). Fail-safe
  direction, but the semantics — does an obligation cover the principal's every row or the
  obligated scope? — deserve a deliberate ruling. Second consecutive run where obligate
  direction/scope cost a workaround; obligate teach-text rewrite also owed.
- **Finding 2 — written-only governance is invisibly skippable:** zero `assumption` rows and no
  antecedent-audit trace despite row 21 baking in unstated numeric choices (tolerance, timebox,
  budgets). No existing gate can see this. This is the artifact-vs-requirements detector class
  (run-5 implementer's analysis), now witnessed as a real blind spot: the next mechanization
  frontier, deliberately NOT rushed — it needs a design pass, not a regex.

## Session 2026-07-11: Opus-readiness pass + HANDOFF items 1-2 discharged to their honest depth

Orchestrator: Fable (this entry written at the moment of the acts, per the
self-application ruling). Four acts, each with its artifact:

1. **Opus fresh-context probe (the readiness test run as an experiment, not asserted).**
   An Opus-model agent with zero working context read the committed entry docs and
   reported comprehension gaps. BLOCKING findings: the two-cwd model (verbs live in
   worlds, not in autoharn) stated nowhere; GLOSSARY.md carried ZERO occurrences of
   "world"/"run"/"birth chain" (its own Stand-Alone Principle violated); the four ADRs'
   chocofarm-native scope/paths freeze-or-bluff a newcomer. FRICTION: run-8 resume
   command written nowhere; "s15→s22" compresses a chain with no s16 and s18 excluded;
   judge verdicts detectable but not diagnosable from the operating set. FIXES LANDED
   same session: OPERATING-CARD.md (≤200-line orientation: two-cwd model, vocabulary,
   verbs, start/RESUME commands, delta decision tree, hooks×kernel map, verification
   checklist, ADR-foreign-substrate note), GLOSSARY operating-era section (9 terms),
   HANDOFF reading-order item 0. The probe's full report is session ephemera
   (local-only, per ruling); its load-bearing claims were re-verified at source before
   any fix landed (GLOSSARY grep, lineage README, new-project.sh chain).
2. **HANDOFF item 1 discharged as designed:** design/ARTIFACT-VS-REQUIREMENTS-DETECTOR.md
   (memo, not spec — deliberately). Key verified fact: run7 was scaffolded 21:18:32Z,
   AFTER the assumption discipline landed (a9e7f52, 18:02 UTC), so run-7 finding 2 is a
   RECURRENCE of an in-force written discipline — the ADR-0011 Rule 2 warrant. Design:
   totality move (explicit assumption-disposition per increment; silence stops being a
   legal state) as free Register 1 on the stop-gate/pickup chassis; out-of-frame
   classifier (demurral chassis, default OFF) as costed Register 2, built only on
   witnessed Register-1 residue. One open design question (disposition→increment
   attachment) deliberately parked for run-8 evidence.
3. **HANDOFF item 2 discharged as drafted:** design/REVIEW-GAP-SCOPE-SEMANTICS-RULING.md
   — one prepared yes/no (recommend ratifying principal-wide semantics; scope = label).
   Root cause of both paid episodes was DIRECTION, not scope. Related Sonnet-sized fix
   LANDED: led.tmpl obligate teach-text now spells out direction/worker-not-reviewer/
   label-not-filter/over-catch + worked example (Sonnet-executed, Fable-reviewed; the
   agent also caught actively-wrong text conflating self-ASSIGNMENT with
   self-REGISTRATION). NOTE: run5/run6/run7/toy-project carry materialized led copies
   that predate this teach-text — templates reach only future worlds; existing worlds
   keep their birth copy (accepted: led is world-frozen by design, same as the kernel).
4. **Run 8 prepared, not started:** live claude session observed in run7 (pid checked at
   /proc/<pid>/cwd, started 23:18 local 2026-07-10 — run 7's own terminal still open),
   so run7 remains hands-off; resumption walkthrough delivered to the maintainer in the
   session reply; resume commands also now in OPERATING-CARD (marked UNWITNESSED until
   run 8 banks the witness).

### Addendum, same day: resumption doctrine sharpened (maintainer, 2026-07-11)

Governed resumption = a FRESH session hydrated from the ledger via ./pickup — never
`claude --continue`. His words, near-verbatim: if the harness works it should NEVER be
necessary to resume with full context; otherwise it's pointless — especially for
Fable/Mythos, whose O(N^2) context cost is literally why HANDOFF.md exists. Card + HANDOFF
corrected (they had described --continue as the path); --continue demoted to a diagnostic
comparison variant. Run 8's witness bar accordingly: the resumed agent must reconstruct
the open work FROM LEDGER ROWS (citing them), not from replayed conversation. An agent
that has to ask the user what the work was is a hydration FAILURE — and a valuable
finding, not a broken run.

## Run-8 mid-run forensics (2026-07-11): the commission never entered the record — hydration failed for a reason upstream of pickup

Sonnet harvest, read-only, live session (snapshot at ledger id 47); maintainer observed
"archaeology" and asked what is wrong with the harness. Evidence-confirmed answer:

1. **FINDING (root cause): phase 2 was never ledgered — by anyone, ever.** Rows 1-27
   (all of run 7) contain zero mentions of phase-2/swatch/render/16-color; the four
   opening decompose-decisions covered phase 1 only. The spec existed solely in the
   maintainer's first chat message (raw run-7 transcript — ephemera-class) and in
   autoharn/HANDOFF.md's gloss (outside the world). ./pickup honestly showed IN-FLIGHT:
   0 rows — the empty brief is the PROXIMATE cause of the archaeology; the ABSENT
   COMMISSION is the root cause. **This falsifies the premise of the 2026-07-10
   task-brief disposition** ("the agent's first ledgered act naturally quotes the task
   via its opening rows") at the first real resumption: the agent decomposed what it was
   about to DO, not what it was ASKED — the class named at the scope of the work in
   hand, ADR-0000's amendment shape, at the commission boundary.
2. **COROLLARY, the sharpest consequence: run 7's clean Stop was vacuously green.** The
   stop gate's live-witnessed silent-allow (BACKLOG run-7 entry) was true over the
   ledger it could see — and the ledger was missing half the commission, so "done means
   clean" passed over undone work it had no row for. An unledgered increment makes every
   downstream gate green by omission. Enumeration fails open at intake.
3. **FINDING: investigation is ungoverned.** 5m12s and 13 tool calls between pickup's
   empty answer and the first ./led call — six Bash reads, a 100-second Explore subagent
   ("Find run7 phase-2 task spec", which recovered the spec by grepping the raw run-7
   transcript), more reads, 7 private TaskCreate calls — zero ledger rows for any of it;
   no question row was filed for "the spec is missing" (kind='question' count across the
   ENTIRE ledger, all runs: 0). Permit-to-work gates the writing hand; the investigating
   hand is still run 5's diary problem. The subagent dispatch is a machine-observable
   tool event, so a permit/observer at PreToolUse(Task/Agent) IS mechanizable — filed as
   designed-unbuilt (observer-first, permit-to-work chassis); hooks/ frozen while run 8
   lives.
4. **What WORKED (credit where due):** rows 28-47 all stamp_verified under run-8's own
   distinct stamp_session (cross-session stamping now live-witnessed — the prudential
   item arrives half-free; the cross-session independence ATTESTATION is still owed);
   after self-recovering the spec the agent ran the full discipline unprompted — 4 work
   items opened, claims, 8 assumption rows (the run-7-finding-2 discipline FIRING this
   run), obligate, review-gap check. Conduct held; the record's intake boundary did not.
5. **FIX LANDED (sub-constitutional, template text; judged consistent with the
   task-brief ruling's intent — it makes that ruling's stated premise true by
   instruction instead of assumed; maintainer veto welcome):** preamble point 1
   sharpened to decompose the ENTIRE commission at intake (open every increment the
   task names, claim only what you start — an unledgered increment is invisible to
   resumption and vacuously green at Stop); new point 7: ledger investigation and
   delegation BEFORE doing them, and — maintainer refinement, mid-run-8, near-verbatim —
   "I lack the spec" has more than one honest kind (ADR-0008: classify, don't default):
   question when the operator should answer, decision when resolving to excavate/author
   the spec from context at hand, assumption when proceeding on an inferred reading;
   new point 8 (maintainer, same exchange): STOPPING IS A LEDGERED ACT — workers leave
   their work resumable for successors; a stop-disposition row (why stopping / what
   stands / what remains) is owed before any stop. Note the composition: point 8 would
   have caught run 7's gap at its own exit — "stopping: phase 2 remains" cannot be
   written without ledgering phase 2. Points 1 and 8 close the intake hole from both
   ends. Reaches future worlds; run7's copy is birth-frozen as designed.
6. **QUEUED, Sonnet-sized, unblocked after run 8 exits:** pickup IN-FLIGHT surfaces each
   open item's statement text (the spec a fresh session builds from), not just
   slug/title/claimant; the PreToolUse delegation observer per (3); the stop-disposition
   check folded into stop_clean_exit (the hook already fires at Stop — warn when no
   stop-disposition row landed this session; observer-first, points 7/8's mechanized
   half).

## Contemporaneity indictment (2026-07-11, maintainer-raised mid-run-8): batching is systemic and its disposition had slid

The maintainer, watching `./led --recent` against the live window, called the batching
"largely dishonestly disposed" — and the record agrees:

1. **Run 7's celebrated clean loop batched exactly like run 5.** Its own timestamps: four
   work_opened rows 0.02s apart; reviews 13-16 within 0.07s; all four work_claimed within
   0.07s; all four work_closed within 0.11s (items the preamble orders closed "once
   delivered", closed in one sweep). Run 8 same night, post-hydration: 4 decisions in
   0.07s, 8 assumptions in 0.16s. Inter-burst gaps of 35-250s are where the work lived.
2. **The disposition slide, named:** run-5 finding 1 = no-permit + no-contemporaneity.
   Permit-to-work fixed the first half; CAPABILITIES' Honest limits then said "NOW FIXED"
   for the whole finding and nobody re-measured the second half for three runs.
   CAPABILITIES corrected this pass (HALF FIXED, overclaim named, dated).
3. **Aim, so the fix isn't theater:** some batching is irreducible (an LLM emits N
   simultaneous conclusions); the defect is the record cannot distinguish honest
   simultaneity from run-5-style backfill — ts is INSERT time masquerading as event time
   and no row is bound to the tool invocation that wrote it. Forbidding bursts would just
   breed theatrical row-spacing (enumeration-fails-open, conduct edition).
4. **Design filed: design/CONTEMPORANEITY-AUDIT.md** — (a) per-invocation stamp token:
   stamp_intercept mints a UUID per Bash call, journals (token, wall-clock, command hash)
   to .claude/logs/invocations.jsonl, exports it via the same PGOPTIONS/GUC path as
   stamp_session; sixth stamp column captured by the existing trigger (additive delta,
   class-shaped, doubt-routes-to-ask since it touches stamp machinery); (b) a first-class
   correlation verb: rows-per-token burst table, journaled-activity-vs-ledger-write
   silence/backfill table, per-row deltas, burned-id refusal fingerprints (row 62 is
   missing tonight; row 63 self-reports a provenance defect), closed verdict vocabulary
   (CONTEMPORANEOUS | BATCHED_DECLARED | BACKFILL_SUSPECT), thresholds set from the
   measured runs-5-8 corpus, observer-first. Sonnet authors the delta FROM the memo after
   run 8 exits; scratch witness + differential per standing rules.
5. **Orchestrator self-correction, on the record:** the evidence above was pulled by the
   orchestrator running psql SELECTs itself — a breach of the standing "Fable never
   writes SQL" delegation policy, rationalized in the moment as "reading isn't writing"
   (the ADR-0013 R3 shape). Maintainer caught it live. Data (read-only) retained rather
   than ceremonially discarded; further DB work re-delegated. The correlation VERB is
   also the structural fix for this class: nobody hand-runs forensic SQL once the audit
   is a verb — which is the maintainer's "should have automated 11 runs ago", verbatim.

## Run-8 phase-2 verification (2026-07-11): all trailer claims witnessed; Stop-gate BLOCK path live-witnessed (first time)

Ledger/git/transcript verification (Sonnet, read-only) of run 8's completion trailer —
all seven claims WITNESSED, none refuted:

- **Commit 166a341 real** in run7's own git: terminal_palette.html (338 lines) +
  verify_phase2_backend.py (131), tracked at HEAD, tree clean. All four phase-2 work
  items closed shipped with non-empty witnesses (incl. commit:166a341).
- **Views clean and non-vacuously so** for review_gap/work_item_violations;
  question_status vacuous honestly (zero question rows this run — the preamble point-7
  gap, already filed, stands).
- **Independence mechanical, both directions:** reviewer rows 50-55 stamped
  (session, agent=a609c686...) against author rows stamped main; author countersigns
  64-70 the reverse; review_detail independence='technical' throughout, confirmed by
  countersigned_in_force, not self-report.
- **The antecedent audit CAUGHT A REAL DEFECT:** reviewer row 55 independently computed
  tolerance 0.5657 vs the author's wrongly-stated 1.0 in row:48; correction row 71
  supersedes the numeric parts with the derivation shown. The reviewer discipline added
  after run-5 (a9e7f52) is now witnessed working end-to-end.
- **LED_ACTOR defect confirmed at source:** rows 56-61 carry actor=1 (author) but
  stamp_agent = the reviewer's hash — the exact provenance mismatch row 63 self-reports;
  row 63 honestly marked self-review/attest_with_reservations; row 70 (author)
  independently reproduced the defect. Row 62 confirmed the only burned id in 50-80
  (refusal fingerprint). Fix commissioned (led.tmpl generic-path, in flight this
  session).
- **Non-convergence FAIL genuinely pre-registered:** row 48 (pre-implementation) names
  non-convergence/TIMEOUT as valid recorded outcomes per row:21's phase-1 convention;
  verification row 78's "FAIL by tolerance, distance 0.7688 vs 0.5657" is the
  pre-registered outcome, not a reframe.
- **STOP-GATE BLOCK PATH LIVE-WITNESSED (first time; prudential item discharged free):**
  at 23:12:16Z the gate BLOCKED the exit ("work item 'swatch-verify-commit' is open and
  claimed ... seen 1/3 times at stop"); the agent closed the item, committed, and the
  23:14:04Z retry was a clean silent-allow. deny→teach→comply→allow, live, at the Stop
  surface. The trailer omitted the block episode (no dishonesty — it wasn't asked for
  gate telemetry; noted so the witness is banked HERE).

CAPABILITIES item 20's "BLOCK path and circuit breaker remain fixture-witnessed only"
is now half-stale: BLOCK is live-witnessed; the circuit breaker (3/3) remains
fixture-only. Update owed with the next CAPABILITIES pass.

## Maintainer ruling (2026-07-11): runs are strictly linear; "live world" does not exist; delta-application ceremony is dead paperwork

His words, near-verbatim: if M > N then run M automatically means run N is dust and
settled. "Live world" doesn't apply in our setting, at all — it never has. The only thing
it has caused is rigamarole: a non-expert told to "run a delta" did the ceremony and then
realized it does nothing at all. Paperwork's real purpose is safety/RCA (NIST stuff);
requiring a non-programmer to do cargo-cult sysadmin acts has the OPPOSITE effect in a
high-assurance project.

Dispositions, effective now:
1. **The only present-tense world is the current run's.** Older worlds are settled
   evidence: read-only archaeology, never patched, never "refreshed", never delta'd.
   Fixes reach reality via the birth chain / templates at the NEXT world's scaffold.
2. **bootstrap/apply-delta.sh is demoted to history.** No operator scenario exists for
   applying a delta to an existing world. The script stays on disk as record; it leaves
   the operator surface (CAPABILITIES item 14 and the OPERATING-CARD delta tree amended
   this pass). The typed-confirmation ceremony dies with it.
3. **"s22 not applied to toycolors" (CAPABILITIES 'Not yet enforced') is DEAD**, not
   pending — toycolors is dust; there is nothing to apply anything to.
4. **The orchestrator's run7-led-refresh suggestion (earlier tonight) is WITHDRAWN** on
   the same grounds; the fixed led reaches the next scaffold automatically.
5. **CLAUDE.md ORCHESTRATION still carries the dead clause** ("Applying such a delta to
   an EXISTING live deployment remains the operator's scripted act...") — ratified text,
   so amending it is the maintainer's word: one yes/no put to him this session (transcribe
   the ruling into ORCHESTRATION, dated and attributed). Operational docs updated now
   regardless; on divergence the SSOT rule already sends readers here.
6. **Candidate filed (one maintainer nod to build): live verbs.** Hooks already execute
   from autoharn per invocation in every world; the verbs are frozen birth copies — the
   asymmetry is why five worlds carry tonight's led defect forever. Proposal: scaffolded
   verbs become thin shims exec'ing autoharn's current templates (deployment.json stays
   the only per-world fact), so a template fix reaches every world instantly and
   "refresh" stops being a concept. The self-contained-world objection collapses under
   this ruling (old worlds are dust; the LEDGER is the evidence, per the audit-trail
   ruling). Sonnet-sized.

## Omega work-tracking disposition (2026-07-11, night shift): s22 vs the documented omega store

Maintainer asked "where do we stand" on omega's work tracking. Analysis grounded in the
in-project record (research/foundational-map/06-omega-work-status-sql-anti-corruption-
layer.md, design/WORK-ITEM-DECISION-MEMO.md, design/S22-WORK-ITEM-LEDGER.md), spot-verified
against ~/w/omega source. Verdict: s22 adopted or strengthened most of what mattered
(construction-time CHECK/trigger where omega had view-level detection; a claim verb omega
never had; append-only-ledger-as-audit-trail replacing omega's bolted-on audit_log — a
strictly better answer, per the decision memo's own reasoning). Correctly-dead weight:
hierarchy (evidenced-away by flat run decompositions), disposition sub-states (33/33 omega
items never left 'open'), the extra-jsonb junk drawer.

Genuinely missing, ranked (the silently-dropped set):
1. **work_item_violations wired into a gate** — cycles/dangling deps sit silent until
   someone runs `led work violations` by hand; the s22 SQL header itself names the gap.
   Sonnet-sized, NO kernel touch (judge.tmpl or gate script). TOP pickup; queued behind
   the live-verbs refactor (same template files).
2. **`led work asof <ts>`** — point-in-time backlog reconstruction; the append-only ledger
   already carries everything, only the read verb is missing. Sonnet-sized, no kernel
   touch. Queued with (1).
3. **superseded_by (what superseded a closed item)** and **priority/tier** — both need a
   kernel column ⇒ Fable-authored spec by rule; both class-shaped (additive). NO witnessed
   need yet (runs 1-8 never exceeded 4 items); filed as candidates per the prudential
   rule — build on witnessed need, not omega nostalgia.
4. **Scope tagging + JSON Schema contract** — need design (what is "scope" for a generic
   project? generated-from-DDL vs hand-authored?); not urgent absent external tooling.

## Chocofarm experiment-ledger disposition (2026-07-11, night shift): designed, reviewed, SHELVED — plus two new findings

Maintainer asked whether chocofarm's performance/experiment ledger is implemented here.
Answer: **its adaptation already exists as stores/001_research_ledger.sql** (chocofarm's
measurement-⊥-interpretation discipline: typed value/unit/n/stderr readings, git_commit +
git_tree code stamp, instrument qualification, a DERIVED non-writable finding_confirmed
view — stricter than chocofarm's own writable status), taken through an ADR-0014
second-opinion pass 2026-06-28 with real fixes — and then never executed: header still
says PROPOSAL v0.1, the research db is empty, and no operator-surface doc cites it, so by
this repo's own archive rule it vanished. Run 7's QEUBO rows prove the cost: evidence is
prose text (distance=0.7688 unqueryable, no GROUP BY, no replicate structure, no code
stamp on ledger rows, a screenshot "saved for visual record" with no path or hash).
Honest counterweight: the ledger BEATS chocofarm on attribution (HMAC stamp vs a commit
trailer) and on live independent review (rows 57-59 caught row 48's arithmetic before the
run) — the typed store complements the narrative ledger, never replaces it. Sonnet-sized
execution gap; prep commissioned tonight (scratch witness + thin recording writer +
scripted apply), the standing-db apply armed for one maintainer word.

Two findings from the same pass:
1. **ADR-0009 in law/adr/ is an UNADAPTED chocofarm copy** (byte-identical diff; Scope
   still binds "the chocofarm/ package", tool list still chocofarm's harness). Law edits
   need the maintainer's word: morning question — re-instance its Scope for autoharn's
   experiment domain (governed runs), amendment drafted on his yes.
2. **Typed edges silently degrade to prose (run7 row 71):** the statement text ends
   "--supersedes 48 --refs row:57,row:58,row:59" but the supersedes/refs COLUMNS are
   NULL — the flags landed inside the quoted statement on a usage slip, and nothing
   caught it. Across all 79 run7 rows: supersedes/amends/answers used 0 times; the FK
   vocabulary exists and practice bypasses it. Sonnet-sized teach-fix commissioned: led
   warns when a statement's text contains what looks like its own flag vocabulary.

### Chocofarm experiment-ledger disposition — APPLY-READY (2026-07-11, this commit)

The prep commissioned above is done: `stores/001_research_ledger.sql` is scratch-witnessed
both polarities and APPLY-READY; the standing `research` db is untouched (armed, not run).

**Fixes to 001, each with reason** (2 weeks' drift since the 2026-06-28 second opinion):
1. Header path comment (`-- db/harness/001_research_ledger.sql`) was chocofarm's OLD path
   convention — this repo renamed `db/harness/` → `stores/` (filing/file_finding.py's own
   comment documents the rename); fixed to `-- stores/001_research_ledger.sql`.
2. Two STATUS lines said "not applied to `harness`" / "validate ... not `harness`" —
   `harness` is a DIFFERENT, existing store (filing/file_finding.py's), unrelated to this
   ledger; the real target, confirmed live, is the standing `research` db (empty, per the
   entry above). Left uncorrected this could point an operator's `psql -d harness` at the
   wrong database. Fixed to name `research`.
3. **`research.instrument` had no dedupe constraint** despite `source_hash` visibly being
   intended as a content-identity column (name + comment) — a re-run writer that
   re-registers the same built apparatus every call would flood the table with duplicate
   rows, each needing its own qualification bookkeeping (the exact class exp_db's
   `tlab_config` UNIQUE(config_key) + ON CONFLICT exists to foreclose). Added
   `UNIQUE (project_id, source_hash)`, scratch-witnessed (a second registration of the same
   apparatus converges on the existing row, not a duplicate).

**Scratch validation** (throwaway schema pair `rlprobe_core`/`rlprobe_research` in the `toy`
db, torn down zero-residue, confirmed by `\dn` before/after): both polarities witnessed.
POSITIVE — project/session/instrument/two-readings/finding insert; `finding_confirmed`
correctly derives the finding (clean tree + qualified instrument + attributed + not
superseded). NEGATIVE, all real refusals with real output — value+value_text both NULL
(`reading_check`); `finding.status='confirmed'` (`finding_status_check` — confirmation
cannot be asserted, only derived); `INSERT INTO finding_confirmed` (`cannot insert into
view`); `UPDATE`/`DELETE` on `research.reading` (the immutability trigger); a bad
`git_tree='DIRTY'` (uppercase — 001's own CHECK is lowercase, unlike exp_db's); a bad
`instrument.kind`.

**The thin writer**: `filing/record_reading.py` (psql-subprocess, matching
`filing/file_finding.py`'s house convention — this repo has no psycopg dependency).
Inherits exp_db's load-bearing choices: content-hash instrument dedupe
(`upsert_instrument`, mirrors `upsert_config`'s `ON CONFLICT`), and a construction-time
derived-value consistency refusal (`Reading.derived_from`, generalized from exp_db's fixed
rate columns to 001's metric-name-agnostic shape, raw operands riding in `config` jsonb) —
foreclosing chocofarm's finding-12 class before any SQL is built. Deliberately diverges on
transport (psql, not psycopg3), git_tree vocabulary (001's own lowercase), and status
enum ('confirmed' is not writable, matching 001's stricter CHECK). No `ensure-schema` verb
here on purpose — `bootstrap/apply-research-ledger.sh` is the one owner of that DDL apply
(ADR-0012 P1). Gate-clean: `gates/no_lazy_imports.py` exit 0 across the repo including this
file.

**Witnessed live** (real re-record of run7 ledger row 78, via the writer's own CLI, against
the scratch schema pair): `record-reading` banked `distance=0.7688` and `tolerance=0.5657`
(both n=1, git_commit=166a341e73fd2e906599ecc42559c763a2823121, tree=clean, instrument
`verify_phase2_backend.py`/kind=script/source_hash=6b5452d... — the actual git blob hash at
that commit); instrument dedupe confirmed (2 readings, 1 instrument row); `record-finding`
appended the FAIL-by-tolerance interpretation citing the distance reading;
`finding_confirmed` derived it correctly. Negative polarity witnessed at BOTH the writer
layer (argparse `choices` rejects `--status confirmed` before any connection; `Reading`'s
`__post_init__` rejects a missing outcome and a derived-value inconsistency, e.g. a claimed
rate 999.0 against operands 100/4.2=23.8095) and the DB layer directly (bypassing the
writer, same six refusals as the scratch validation pass). Zero-residue teardown confirmed
(`\dn` before/after).

**The scripted apply**: `bootstrap/apply-research-ledger.sh` — resolves host/db from
`RL_PGHOST`/`RL_DB` (default `192.168.122.1`/`research`, matching the writer's own env
vars), prints the exact `psql ... -f stores/001_research_ledger.sql` command before doing
anything, preflights for "already applied" and refuses loudly rather than hitting a
mid-transaction `already exists` (001's DDL is `CREATE TABLE`, not `IF NOT EXISTS` —
idempotent-or-refusing per the commission, achieved by the refusing half), and requires the
operator to type the db name back to confirm — same posture as `bootstrap/apply-delta.sh`.
Test-driven end to end against `toy` (never `research`): abort path, real apply (schemas
landed, verified via `\dt`), preflight-refusal on a second run, zero-residue teardown — all
witnessed live, `research` confirmed untouched throughout (`\dn` shows only `public`).

**Apply one-liner for the maintainer's morning word** (NOT run):
```
bootstrap/apply-research-ledger.sh
```
(or `RL_PGHOST=... RL_DB=... bootstrap/apply-research-ledger.sh` to target something other
than the default `192.168.122.1`/`research`). It prints its plan and asks for the db name
back before touching anything.

## Documentation legibility indictment (maintainer, 2026-07-11 morning)

The maintainer, reading the morning batch cold, hit three defects in ten minutes and named
the class: "you shouldn't have to navigate the doc graph like a squirrel just to figure out
what the insane staccato — a consistent malady of our documentation — is supposed to mean."

The three instances, all confirmed at source and fixed same morning:
1. design/REVIEW-GAP-SCOPE-SEMANTICS-RULING.md cited "HANDOFF open-work item 2" — a pointer
   into a SUPERSEDED HANDOFF revision (the slot now holds the audit verb). A cross-reference
   by position into a mutable document is a dangling pointer waiting to happen. Fixed: cites
   the item by name; a plain-words statement of the question now leads the file.
2. Same file assumed the reader knew what review_gap/countersign_obligation are — a ruling
   prepared for a non-expert opened with a SQL quote. Fixed (plain-words lead).
3. law/briefs/BRIEF-CONFORMANCE-MAP.md used "J-boundary" with no definition a reader could
   reach — the BRIEF path it cited was the source project's tree
   (experiments/fact-mining/...), not a link, and wrong for this repo. Fixed: relative link,
   self-standing M/J definitions in the map itself.

CLASS, not instances: (a) positional cross-references into mutable docs; (b) coined terms
used without the GLOSSARY.md wiki-posture link; (c) paths cited as prose instead of
resolvable relative links; (d) maintainer-facing docs that open in apparatus jargon instead
of a plain-words statement. The GLOSSARY Stand-Alone Principle already legislates (b); nothing
mechanizes any of it. Commissioned same morning (Sonnet): a repo-wide sweep for the four
shapes plus a class-not-instance gate for the mechanizable core — every relative markdown
link in maintainer-facing docs must resolve on disk. Disposition of the sweep lands as its
own entry.

## Contemporaneity audit, Part 2 — CORE LANDED (2026-07-11, Sonnet, commissioned build)

Part 2 of design/CONTEMPORANEITY-AUDIT.md (the correlation verb) built and witnessed, per a
maintainer critical-path resequencing mid-build ("run 9 will not start until this instrument
lands") that scoped the FIRST landing to a minimal end-to-end core; the SQL-floor differential
(item 2 below) is filed here, not built, as that resequencing's own deferral.

**Landed, this pass:**
1. `engine/contemp_thresholds.lp` — the two measured thresholds (`burst_threshold_ms(1000)`,
   `silence_threshold_ms(180000)`) as FACTS, with their full derivation from the runs 5-8
   corpus (db `toy`, 192.168.122.1) in the file's own comments — the query, the raw gap
   numbers, and the two hand-forensic true positives (run5's 503s / run8's 312s silence-then-
   burst) the silence threshold sits below.
2. `engine/lp/contemporaneity.lp` — the ASP verdict program: EDB
   (`invocation/2`, `row_tokened/4`, `row_untokened/3`, `tool_event/2`), derived predicates
   (`token_burst`, `ts_cluster` — degraded/inferred, kept structurally distinct from the stated
   token burst — `silence`, `backfill_suspect`, `refusal_fingerprint`, `row_delta_ms`,
   `preceding_activity_age_ms`), and the closed session verdict (`contemporaneous` |
   `batched_declared` | `backfill_suspect`), mutually exclusive by stratified negation.
3. `engine/contemp_edb.py` — the EDB builder, joining Postgres (the ledger) against a world's
   `.claude/logs/*.jsonl` (the s23 invocation-token journal + the three existing tool-activity
   observer journals), with a capability manifest (mirrors `engine/ledger_edb.py`'s
   produced/declared-exclusion idiom) so a world missing a capability is named, never silent.
4. `engine/contemp_audit.py` — the CLI/report layer: runs clingo, parses atoms, prints the
   burst/silence/backfill tables, the per-row deltas (ts minus the row's own invocation's
   journaled wall-clock; the age of the preceding tool-activity window — the maintainer's own
   asked-for number), refusal fingerprints, and the verdict. Exit codes: 0 clean, 1
   BACKFILL_SUSPECT (loud), 2 tool error, 3 N/A (capability-gated refusal — mirrors the
   existing `contemporaneity-degrade` exit-3 convention in `instruments/`).
5. `bootstrap/templates/audit.tmpl` — a fifth operator verb (`./audit`), wired into
   `bootstrap/new-project.sh --new-world`'s shim loop alongside `led`/`judge`/`pickup`
   (live-verbs convention: execs straight out of this checkout, no scaffold-time copy).
   Witnessed live: a throwaway `--new-world auditprobe` scaffold wrote the shim; `./audit` run
   from inside the fresh (empty) world produced the correct N/A refusal against the real
   scratch schema; torn down clean.
6. `seen-red/contemporaneity-audit/run_fixtures.py`, registered in `gates/fixture_census.py`.
   Four cases: an empty ledger (N/A, never a guessed verdict); a clean multi-row token burst
   with dense tool activity (BATCHED_DECLARED, zero backfill_suspect); a manufactured >300s
   tool-activity silence with zero rows immediately followed by a burst (BACKFILL_SUSPECT,
   naming the token — the banked `red.txt`); and — the one case run against REAL data, not a
   fixture — run7's own live (read-only) pre-s23 schema, confirming the N/A refusal, the
   missing-capability name, and the exact burned-id refusal fingerprint (id 62) BACKLOG's own
   hand forensics already found.

**Two hazards found live during this build, one fixed in-pass, one flagged:**
- **FIXED**: clingo/clasp's integer terms are 32-bit signed C ints; an absolute 2026-era
  epoch-millisecond value silently wraps (verified: `echo 'a(2000001010000).' | clingo -
  --outf=2` prints `a(-1453749936)`, no error). `contemp_edb.py` now emits every T relative to
  a per-export minimum-timestamp anchor, never absolute — closed before this landed, not
  deferred (found in this module's own first test against real run7 data).
- **FLAGGED, not fixed**: the three hook journals `contemp_edb.py` reads disagree on a
  timestamp convention — `mutation_observer.journal.jsonl`/`invocations.jsonl` write UTC with
  a trailing `Z`; `change_gate.journal.jsonl`/`delegation_observer.journal.jsonl` write a
  naive-local `datetime.now().isoformat()` with no tz suffix. Parsed correctly for both shapes
  today (`contemp_edb.py::_parse_ts_ms`), but the naive-local reading is only correct on the
  same host/timezone that wrote it. Fixing the two hooks' own convention is outside this
  commission's touch-list (and a hooks/ edit is gated on no wired session being live); named
  here as a genuine, if currently harmless (one-operator, one-host), inconsistency for a
  future pass.

**Filed, not built, this pass (the maintainer resequencing's own deferral):**
1. **The SQL-floor differential** (this domain's sibling to `engine/ledger_floor.py` /
   `engine/ledger_differential.py`) — a second, independent producer over the same EDB so a
   verdict here earns the marriage discipline's AGREE bar. Today's verdict is single-producer
   (ASP only); `contemp_audit.py`'s own report and `engine/lp/contemporaneity.lp`'s header say
   so on every run, never silently upgraded to "AGREE". Candidate shape: stage the
   invocation/tool_event JSONL data into a scratch Postgres table (or a `VALUES(...)` literal
   built from the same parsed tuples) and re-derive batch/silence/backfill_suspect via
   recursive CTEs / window functions, independently coded from the ASP rules — the established
   `ledger_floor.py` idiom, extended across a file-plus-DB input rather than a DB-only one.
2. **Scaffold wiring for the DerivationRecord retention convention** (`--retain`'s banked
   artifacts under `engine/docs/contemporaneity-audit/runs/`) exists (`contemp_audit.py
   --retain`) but `./audit`'s own shim does not default to `--retain` the way `judge.tmpl`
   does for the marriage differential — left as an explicit flag pending the maintainer's
   preference on whether every `./audit` run should bank evidence by default (a disk-growth
   question `judge`'s own precedent answered "yes" for; not re-litigated here).
3. **Part 3** (the deontic/temporal ASP program over the whole governance preamble's ordering
   obligations, design/CONTEMPORANEITY-AUDIT.md's own "sketch, research direction, filed not
   committed") — untouched, as the design memo itself scoped it.
4. **Session-level verdict granularity**: today's verdict is computed over the WHOLE exported
   ledger window (all rows in the schema), not sub-divided by the ledger's own `session`
   column — a coarser grain than "per session" as the design memo's item 5 literally reads.
   Defensible for a single-session scratch/small world; a multi-session world would want the
   `session` column folded into the EDB and the verdict computed per-session. Named, not built.

Every claim above is either WITNESSED (with the observed output quoted in the commit/report
this entry accompanies) or explicitly filed as UNEXERCISED/deferred — no umbrella claim.

## Hook-journal timestamp convention unified (2026-07-11, pre-run-9 window)

The contemporaneity-audit commission flagged (its BACKLOG entry, same day) that the hook
journals disagreed on timestamp convention: stamp_intercept and the mutation observer wrote
UTC-Z; the change gate and the delegation observer wrote naive-local with no timezone suffix.
The EDB builder parses both shapes explicitly, so audit deltas were correct on this
one-operator, one-host setup — but naive-local timestamps under a time-delta auditor are
correct by accident of same-host reading, and go wrong for an hour at every DST transition.
That is a nail pointing up in the audit's own floor.

Fixed at the source in the only cheap window (no wired session live — pgrep + /proc cwd
checked, WITNESSED: three claude processes, cwds autoharn/parent/home, no run* world):
both naive-local hooks now write UTC-Z `datetime.now(timezone.utc)` like their siblings.
contemp_edb.py's naive-local parse branch is KEPT for pre-fix journal lines on disk; its
NAMED HAZARD docstring now records the resolution. The internal naive-vs-naive lag
comparison in the change gate (both operands naive local, no journal surface) is untouched
and internally consistent.
## Documentation legibility indictment — disposition (Sonnet, 2026-07-11)

Three deliverables against the commission above. Every number below is a live re-run captured
the same session; no figure is carried from memory.

**1. The gate: `gates/link_integrity.py`.** Every relative markdown link `[text](target)` in
every tracked `*.md` file must resolve on disk (v1: `#anchor` fragments are flagged, never
failed — a separate, non-blocking report section). Modeled on `gates/fixture_census.py` /
`gates/layout_census.py` (same `git ls-files '*.md'` scope, same closure-statement docstring
shape, same `ROOT`-relative resolution) and registered the same way: `link-integrity` ->
`seen-red/link-integrity/run_fixtures.py` in `gates/fixture_census.py`'s REGISTRY (WITNESSED:
`fixture-census: clean ✓ (32 seen-red gates...)`), wired as a fifth BLOCKING step in
`hooks/pre-commit` (after `fixture_census`, before the disabled `layout_census` /
report-only `doc-legibility`).
Two principled exclusions, both PRINTED in the gate's own output every run, never silent:
`judgment/**` (OPERATING-CARD.md's own words: "predecessor era — history unless a current
spec cites it") and `design/ARCHITECTURE.md` (carries its own `⚠ STALE` banner declaring its
paths point at the old pre-consolidation layout and that its rewrite is separately filed —
patching its links piecemeal would manufacture false current-ness the banner itself disclaims).
WITNESSED, both polarities, `seen-red/link-integrity/run_fixtures.py`:
```
RED:   fixture.md -> ./nonexistent-target.md   =>  exit 1, "!! <tmp>/fixture.md:3  ./nonexistent-target.md"
GREEN: fixture.md -> ./sibling.md (exists)     =>  exit 0, "link-integrity: clean ✓"
```
(banked verbatim in `seen-red/link-integrity/red.txt` / `green.txt`). WITNESSED live over the
full corpus: `link-integrity: 180 docs in scope (209 tracked *.md, 29 excluded), 1537 relative
link(s) checked. ... link-integrity: clean ✓` (exit 0).

**2. The sweep.** Building the gate required first making the corpus pass it — 96 broken links
turned up on the first full-corpus run, almost all in `research/**` and
`gates/doc-legibility/{README.md,terms.md}`: an off-by-one path depth left over from the
chocofarm→autoharn consolidation (old paths assumed a `docs/research/2026-06-27-<name>/`
layout; the renamed tree is `research/<name>/`, one level shallower, no date prefix). This
is the exact hazard class the commission names, found in reach of the work — fixed
mechanically (80 links auto-fixed by a depth/prefix-correcting script, verified resolving
before writing; 6 more needing individual judgment fixed by hand: 3 `tools/doc-legibility/`
→ `gates/doc-legibility/` renames, 2 genuine sibling-chocofarm citations in
`design/LOGIC-LAYER-SEAM.md` de-linked to plain non-clickable citations — consistent with how
this repo already treats chocofarm-native ADR paths — rather than faked into a local link,
1 `tools/` → `gates/` rename). `design/ARCHITECTURE.md`'s 10 broken links were left standing
and the file excluded from the gate (see above) rather than patched — its own banner calls
for a full rewrite, not a path graft. `gates/doc-legibility/README.md`'s "Scope" section also
described the gate's OLD (pre-finding-48) scope; corrected to state the actual scope and the
report-only pre-commit disposition honestly.

Named-surface fixes (HANDOFF.md, OPERATING-CARD.md, CAPABILITIES.md, GLOSSARY.md, the four
active design docs, law/briefs/*.md):
- `design/REVIEW-GAP-SCOPE-SEMANTICS-RULING.md` — a LIVE RECURRENCE of the exact defect this
  file documents having fixed: it still cited "HANDOFF 'Open work' item 1" positionally.
  Fixed: cites the entry by name ("Maintainer's morning batch").
- `design/ARTIFACT-VS-REQUIREMENTS-DETECTOR.md` — "This is HANDOFF open-work item 1" was now
  FALSE (HANDOFF's current list has it at item 3). Fixed: cites by name, with a one-line note
  on why a positional cite is the wrong pointer to leave standing.
- `GLOSSARY.md` — `obligation` is used throughout OPERATING-CARD.md and CAPABILITIES.md but
  had no entry here at all (a genuine Stand-Alone Principle gap, not a link omission). Added
  `### obligation`, placed after `### principal`.
- `OPERATING-CARD.md` — its "Vocabulary" section restates 11 GLOSSARY.md terms locally with
  ZERO links (the exact anti-pattern the wiki posture exists to prevent — a second,
  divergence-prone copy). Fixed: every term now links to its GLOSSARY.md anchor (verified by
  slugifying every `### heading` and checking the anchor matches, not assumed).
- `HANDOFF.md` — linked `world`/`permit-to-work`/`stamp`/`principal` on first use in its
  opening "Where the project stands" paragraph (the doc's own designated entry point).

Checked and left alone, with reasons: `design/PG-HBA-HARDENING.md`'s `step N` and
`law/briefs/*`'s `item N`/`point N` are self-referential within their own numbered list (not
a cross-doc pointer — no hazard). `design/ARTIFACT-VS-REQUIREMENTS-DETECTOR.md`'s "world
preamble point 6/2" cites `bootstrap/templates/CLAUDE.md.tmpl`, explicitly out of this
commission's touch-scope, and is a versioned template rather than a nightly-rewritten
narrative doc (lower drift risk) — left as prose. `CAPABILITIES.md`'s many internal `item N`
self-references are stable (append-only numbering to date) but not name-anchored; flagged as
residue below rather than mass-edited.

**Honest residue (not silently closed):** before this pass, ZERO of the 10 named-surface
files linked to `GLOSSARY.md` at all, despite heavy, page-one use of coined terms (`world`,
`run`, `stamp`, `delta`, `principal`, `obligation`, `seen-red`...) — systemic under-linking,
not isolated instances. This entry fixed the highest-leverage subset (the orientation card's
own vocabulary section, the entry-point doc's first paragraph, the one missing GLOSSARY
definition found in-flight) rather than claim a full first-use sweep of `CAPABILITIES.md`, the
other three active design docs, and `law/briefs/*.md` that this pass did not do — that is a
separately-sized follow-up (most paragraphs of roughly 1600 lines of prose), not something
"surgical edits" discharges honestly in one sitting. Filed here so the gap is visible, not
inferred clean because the gate is green (the gate checks link RESOLUTION, not link
PRESENCE — a term with no link at all never fails it).

**3. The `doc-legibility` gate assessment.** This morning's report — "1614 undefined
acronym(s) across 206 docs," blocking nothing — is real: `hooks/pre-commit`'s own header
already says why (report-only pending a corpus sweep, finding 48). It is not "advisory by
design" as a chosen posture so much as "blocked from arming by an unmanaged corpus" per that
same header's own honest words.

The heuristic IS partly salvageable, cheaply: seeded `gates/doc-legibility/allowlist.txt`
with two mechanical, low-risk categories, spot-checked against real usage before listing
(never guessed) — (a) ALL-CAPS common-English/emphasis words, several of which the project's
OWN commentary already names verbatim as this exact noise class (`BACKLOG.md:623-624`,
`hooks/pre-commit`: "RED/NEG/NUM/ONE/NO/IS/IN", "INSERT/NULL/FK",
"MIGRATE/STAYS/DECIDED/INC" — a mechanical transcription of an already-made call, not a fresh
judgment) plus verdict/ledger-state vocabulary (AGREE/DIVERGE/DEFECT/QUARANTINED/
WITNESSED/REFUSED/RATIFIED/...); (b) this project's own SSOT document names used bare
(ADR, BACKLOG, CLAUDE, BRIEF, FINDINGS, HANDOFF, CAPABILITIES, GLOSSARY, PROVENANCE,
ORCHESTRATION, DESIGN, LAW — the "acronym" IS the filename, not jargon needing a definition);
plus verified proper nouns (ISO, IEC, NRC) and common terms (JSON, URL, ID, GB, NLP, GPU,
HMAC, PR, FK) and Claude Code's own event-name vocabulary (`PreToolUse`, `PostToolUse`).
Separately, excluded `judgment/**` from `SCOPE` — the same declared-history rationale as
`link_integrity.py`'s exclusion (a structural scope fix, not acronym classification).

WITNESSED, before -> after (`python3 gates/doc-legibility/check.py`, live re-runs):
```
BEFORE (this morning, unmodified):        1614 undefined acronym(s) across 206 docs  (10750 flagged occurrence-locations)
AFTER allowlist seeding only:             1524 undefined acronym(s) across 206 docs  ( 6145 flagged occurrence-locations)
AFTER + judgment/ exclusion:              1319 undefined acronym(s) across 178 docs  ( 4865 flagged occurrence-locations)
FINAL (incl. this very BACKLOG entry's
own prose, re-observed after writing it): 1328 undefined acronym(s) across 178 docs  ( 4910 flagged occurrence-locations)
```
The last line is CITATION CURRENCY, not a regression: writing this entry itself added ~9 new
ALL-CAPS tokens (REGISTRY, CONFORMANCE, BLOCKING, ...) to the corpus the gate scans, so the
honest final figure is the one re-run AFTER this text existed, not the number measured
mid-edit. Net vs. this morning: unique undefined tokens -17.7%, flagged occurrence-locations
-54.3% (the seeded tokens were disproportionately high-frequency — `ADR` alone was 1410 of
the original 10750).

**Recommendation: KEEP-ADVISORY-WITH-SEEDED-ALLOWLIST** (not fix-and-arm, not
demote-to-removed). Costs of the alternatives: FIX-AND-ARM needs the remaining ~1328 unique
tokens correctly defined — dominated by two genuine jargon corpora
(`law/briefs/safety-critical-logging/BRIEF.md`'s cross-domain safety-standards survey — SIL,
DAL, ASIL, GSN, ALCOA, MHRA, FDA, CFR, PVS, WODES, CIF, ESCET, FINRA, ISA, and more — and
`research/`'s formal-systems corpus) that need researched, correct expansions, not casual
allow-listing (allow-listing real jargon to pass the gate is the exact false-authority failure
this gate exists to catch, per its own README) — a dedicated multi-hour authoring session,
explicitly outside this commission's "do not hand-classify" bound. DEMOTE-TO-REMOVED throws
away a gate that already caught two real maintainer-hit defects (SBC, then MC/DC) and, after
this seeding pass, runs at under half its original noise floor — removing a working detector
because its tail is unmanaged is the wrong trade. KEEP-ADVISORY is the honest middle: it still
prints on every commit (visible, not hidden), the seeding measurably improved its
signal-to-noise, and arming should wait on either a dedicated terms.md authoring pass over the
two named corpora, or a narrower blocking SCOPE (the same "narrow enough to arm today" move
`link_integrity.py` made instead of gating the full corpus at all).

**Flagged, not fixed (out of this commission's scope):** `doc-legibility` itself carries no
`seen-red/` directory and no `gates/fixture_census.py` registration — a pre-existing gap
surfaced while reading the registry for this work, not introduced by it. Building its
both-polarity fixture harness is a distinctly-sized task, named here rather than silently
left for the next reader to assume already covered.

## Contemporaneity audit: run9 false refusal — capability-vs-corpus conflation fixed; witness record reconciled (2026-07-11, Sonnet, same commission)

**The live specimen (maintainer-stopped run):** run9 — the FIRST s23-capable world, correctly
wired end to end (settings.json wires all journaling hooks; apparatus modes on; 12
invocations.jsonl lines) — ran `./audit` and got `NO_VERDICT` exit 3, "Missing/excluded:
['tool_event']". The maintainer stopped the run over it. Verified at source: the world was
healthy and merely YOUNG — the session had run only orientation commands, so zero tool events
and zero ledger rows were the TRUE state, not a capability absence.

**The defect (engine/contemp_edb.py, first landing):** every journal family's capability was
keyed on corpus non-emptiness (`produced = len(events) > 0`), conflating "observers unwired /
pre-journal era" with "observers wired, nothing journal-worthy has happened yet". The refusal
message then asserted "observer hooks off/unwired" about a world whose hooks were demonstrably
wired — a false claim in exactly the message the commission's honest-refusal constraint exists
to keep true.

**The fix (both halves, this pass):**
1. **Capability means CAPABILITY.** `contemp_edb.Capability` now carries the
   `produced`-vs-`capable` two-axis split `engine/ledger_edb.py` already uses: `capable` is
   read from the world's OWN wiring (`_wired_journaling_mechanisms`: the hook script referenced
   in `.claude/settings.json`, not explicitly `"off"` in `.claude/apparatus.json`), `produced`
   stays "facts actually emitted". The verdict gate (`contemp_audit.py::run_audit`) and the
   refusal's "Missing/excluded" list both key on `capable`. All four families audited for the
   same conflation: `invocation_journal` had it too (fixed identically);
   `s23_capable`/`stamp_invocation_column` are schema facts, no conflation. A wired-but-empty
   journal now prints "EMPTY (capable, zero events yet)", structurally distinct from
   "EXCLUDED".
2. **The empty-corpus verdict path.** A fully-capable world with ZERO ledger rows now gets an
   explicit `VACUOUSLY_CLEAN` (exit 0): "0 ledger rows — nothing to audit yet ... NOT evidence
   of conduct and NOT a capability refusal." Refusal (exit 3) is reserved for genuinely missing
   capabilities; the third state — rows present but ALL untokened in a wired world — keeps its
   own distinct NO_VERDICT (that one IS a finding to investigate: writes escaped interception).

**Re-witnessed, live, run9's real world (read-only):** post-fix `./audit` output banked
verbatim as seen-red/contemporaneity-audit/run9-vacuous-clean-witness.txt — capabilities
(family, capable, produced): tool_event (True, False) tagged "EMPTY (capable, zero events
yet)", VACUOUSLY_CLEAN, exit 0. Fixture suite extended (CASE e reproduces the run9 shape
synthetically: wired-but-empty world → exit 0 vacuous; CASE d re-scoped to the honest refusal
case: UNWIRED empty world → exit 3; CASE c's assertion sharpened: run7's refusal must name its
REAL blocker, s23_capable, since run7's settings.json does wire stamping and its invocation
journal now correctly reads capable-but-empty). All five cases pass; contempprobe torn down
clean; no wired session was live during the engine/ edits (pgrep/cwd checked; run9's session
confirmed stopped).

**Witness-record reconciliation (owed per the correction commission):** the first landing's
report described the auditprobe fresh-world run as clean, and its committed record blessed the
observed exit-3 refusal as "the correct N/A refusal". The observation REPRODUCED exactly —
auditprobe (fresh, empty, scaffolded, hence wired) exited 3 with NO_VERDICT, precisely as run9
later did; there was no witness divergence between the two worlds. The two real defects were:
(a) the report message's wording ("ran it clean") misdescribed an exit-3 refusal as a clean
run — the committed BACKLOG/CAPABILITIES text said "N/A refusal" accurately, but the summary
message did not match the banked artifact; and (b) the deeper design defect that the refusal
itself — the behavior the record blessed as "correct" — was wrong for a wired world. Under the
fix, the auditprobe shape and run9 both verdict VACUOUSLY_CLEAN exit 0. CAPABILITIES item 24
amended accordingly (the stale "correct N/A refusal" claim corrected in place, with this entry
as the trail).

**Also reconciled while here:** item 24's "named hazard, flagged not fixed" paragraph on the
journals' timestamp-convention disagreement was stale — a separate pre-run-9 pass (commit
19c9159) unified the hooks to UTC-Z after this build flagged it; the CAPABILITIES text now says
so instead of claiming the hazard is still open.

## Run-10 first audit verdict adjudicated: INTAKE-SHAPE HONEST BATCH (2026-07-11)

The maintainer ran ./audit on the freshly-started run 10 and got its first real verdict:
BATCHED_DECLARED — rows 2-11 written by one invocation (token dad9e364), deltas 291-1025ms,
zero tool events. A read-only Sonnet adjudication (no writes anywhere; run 10's session was
live) classified all eleven rows against the journal record:

- Rows 2-11: present-tense task declarations ("task N: ..."), one shell script of ten
  sequential ./led decision calls (command_head witnessed in invocations.jsonl). DECISIVE
  evidence they are not backfill: task 1's own subject, git init, had not yet happened on
  disk at adjudication time (stat .git -> no such file) — a statement cannot narrate
  conduct that has not occurred. Causal order in the journal: decision burst -> obligate
  decomposition review -> work-open burst (ids 12-21, mirroring 1:1) -> stamp-distinct
  reviewer countersigns (delegation journal 15:37:51; review rows 22-42). The run-8-minted
  intake mechanisms are visibly operating in run 10.
- Row 1: the one row narrating past conduct (~2 min of pre-ledger API discovery at 15:34),
  and it SELF-REPORTS the gap: "Recording this gap honestly rather than back-dating." An
  improvised declared late entry, performed in prose because no mechanism holds it.

Disposition: the verdict was correct and the batch honest. The specimen set (benign intake
burst; improvised declared late entry; runs-5-8 hostile undeclared backfill) is now
complete on all three polarities, and design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md (same day)
proposes the mechanism: intake-shape annotation (engine-side), declared event time +
LATE_DECLARED verdict (kernel delta + closed-vocabulary extension, maintainer's word),
preamble teaching line. One prepared yes/no rides in that memo.
## Zero-context-reader documentation discipline — ADR-0017 DRAFT + measured enforcement (2026-07-11, Fable, commissioned; RATIFICATION PACKET)

The maintainer's morning legibility indictment (the entry above, "Documentation legibility
indictment") commissioned a law-track discipline by name. This entry is its ratification
packet. The draft is design/ADR-DRAFT-documentation-discipline.md — intended home
law/adr/0017-the-zero-context-reader.md (0016 is the last occupied number); nothing binds
until the maintainer's word.

**The one question (yes/no, single recommendation):** Ratify ADR-0017 into law/adr/, and arm
the A:B:C fresh-context audit loop (your own 2026-07-11 proposal, adopted in the draft's
"fresh-context audit loop" section) as the discipline's primary transport for
maintainer-facing doc work — accepting its honest cost, roughly 2–3x tokens per
documentation change, on session billing? **Recommendation: YES.** The loop's reviewer B is
the zero-context reader by construction — the only instrument that attacks the root cause
(the author's live context silently completing skeletal text) rather than approximating it —
and the measured alternative is mediocre (below).

**The separate sub-question (explicitly not folded into the yes):** may any LLM verdict ever
sit in a BLOCKING path for this discipline? **Recommendation: NO.** Blocking surfaces stay
deterministic: gates/doc_shapes.py on touched files, and — once built — the
attestation-presence gate, which checks that a fresh-context read HAPPENED and has the
required per-finding shape, never what it concluded. B's and the critic's content judgment
stays advisory; the promotion question returns only with measured LIVE precision (draft
Revisit #2), never before.

**Delivered, witnessed:**
1. design/ADR-DRAFT-documentation-discipline.md — the draft tenet: root cause named
   (documentation written against a context window that dies with the session — the
   maintainer's "life-time of about 2 hours" made precise), the mandate as the zero-context
   reader test (the academic self-explanatory-figure rule generalized), the banned shapes as
   quoted specimens (BRIEF staccato + the 48dce0c morning defects), GLOSSARY's Stand-Alone
   Principle subsumed, per-rule enforcement surfaces declared, binds-on-touch migration
   (never big-bang), portable core with autoharn bindings quarantined in one section.
   WITNESSED self-application: the draft passes gates/doc_shapes.py (gate mode, 0 findings)
   and every relative link in it resolves on disk.
2. gates/doc_shapes.py — the deterministic core, measure-first (the acronym gate's 1619-
   violation cry-wolf failure is the design's named cautionary tale; witnessed live this
   pass, exit 1, 1410 of the 1619 being the token "ADR"). Ships the two checks that measured
   sound on the 208-doc corpus: standalone fragments (18 hits, 16 = the license line,
   exempted; 2 genuine) and bare positional refs into HANDOFF (1 live flag, 0 false
   positives; the quoted-named-anchor form the 48dce0c fix uses is exempt). Gate mode
   (named files, blocking) for the touched set; report mode (repo-wide) never fails.
   Declined with measurements, in the gate's own header: grounding-before-table (602 hits =
   house style), slash-soup density, coinage-linking, jargon-openings (no sound predicate;
   critic/review). WITNESSED both polarities: seen-red/doc-shapes/red.txt; registered in
   gates/fixture_census.py (census re-run clean, 34 gates).
3. hooks/doc_legibility_critic.py — the headless critic on the demurral-detector chassis
   exactly: observer-only, fail-open, apparatus.json switch `doc_legibility_critic`,
   DEFAULT OFF (costed — a real `claude -p` haiku call per .md Write/Edit), structured
   findings (shape, verbatim quote, suggested repair; an umbrella DEFECT with no per-finding
   line is treated as no verdict), journal under .claude/logs/. Delivered UNWIRED (no
   hooks-wiring or template edits this pass, per the standing rule); the PostToolUse block
   to drop in is in its docstring. Its prompt is the SSOT of B's briefing in the A:B:C loop.
   WITNESSED live, three polarities: warning fired on the BRIEF-shaped defective write,
   silent on clean, instant no-cost exit with no apparatus.json
   (seen-red/doc-legibility-critic/red.txt).
4. instruments/doc_legibility_corpus.jsonl (n=24, 12 DEFECT / 12 CLEAN, every row a real
   in-repo passage incl. the 48dce0c before/after pairs and hard negatives) +
   instruments/doc_critic_eval.py. MEASURED, both prompt versions banked in
   seen-red/doc-legibility-critic/eval-witness.txt: v1 RAW precision 0.524 / recall 1.000
   (punished excerpts for document-scope cross-references — the measurement is why v2
   exists); shipped v2 RAW precision 0.692 / recall 0.750 / F1 0.720 (EFFECTIVE, fail-open
   folded: 0.692/0.750). Caveat stated in the witness: v2 calibrated in-sample against these
   same 24 rows, one iteration, same loop the demurral build ran; out-of-sample unknown
   until live findings grow the corpus. The design conclusion travels with the number: a
   passage-scoped headless haiku is a mediocre transport for this judgment — evidence FOR
   the A:B:C whole-document fresh reviewer as primary.

**Designed, UNBUILT (named, not smuggled):** the commit-time attestation-presence gate for
the A:B:C loop (record format + pre-commit wiring are one decision; blocked on the main
question's answer — building the gate before the loop is armed would gate on a record
nothing produces). Kernel note, verified against the pending review_gap scope-semantics
ruling: countersign_obligation/review_gap already model "writes are debt until a
stamp-distinct attest," so a wired world can carry doc attestation with zero kernel change,
at the ruling-pending coarseness that an obligation binds the whole principal.

**Coordination:** this pass was authored against next @ 5a0bbbe, where the concurrent Sonnet
sweep + link gate had not yet merged; the merge (b5f9180) landed MID-PASS and this branch
was fast-forwarded onto it before committing, so the two compose as merged fact, not as
design intent. Division of labor as landed: gates/link_integrity.py owns link RESOLUTION
(blocking, pre-commit, its exclusions printed); gates/doc_shapes.py owns the disjoint
prose shapes (fragments; bare positional HANDOFF refs); no overlap. Two of this pass's
authored-time findings were independently confirmed and fixed by that sweep before merge —
the ARTIFACT-VS-REQUIREMENTS-DETECTOR.md:4 bare positional ref, and the acronym README's
stale tools/ path — a small live instance of two independent producers converging on the
same defects. doc_shapes gained a quoted-mention exemption (odd-quote-parity) post-merge,
because the sweep's own fix of REVIEW-GAP left a QUOTED historical mention of the defect
that the gate must not flag; the draft's Rule 2(b) text and the acronym-gate cautionary
tale were updated to cite the sweep's landed disposition (KEEP-ADVISORY, allowlist seeded).

**Standing findings, flagged not fixed:** doc_shapes report mode (post-merge re-run) leaves
2 findings — FINDINGS.md:107 ("Block-and-ask + witness-integrity mandate.") and
law/adr/0015:50 ("Four rules."), both genuine fragments — left in place per the draft's own
Rule 4 (binds on touch; law/ is not edited without a ratified spec) and filed here as the
back-catalog's first known migration candidates.

Every claim above is WITNESSED (output banked at the named seen-red paths or quoted in this
entry), or explicitly UNBUILT/UNEXERCISED with its blocker named. No umbrella claims.

## Two ratifications (maintainer, 2026-07-11 evening)

1. **ADR-0017 ACCEPTED with one proviso.** Moved to law/adr/0017-the-zero-context-reader.md
   (links re-rooted; added to CLAUDE.md's binding law list). The proviso, his words: Rule 4
   must not prohibit "large sweeps (which I intend to do, when the time is right)" — the
   draft's "*never* migrated" emphasis was "undue and inflexible discipline for, to me
   anyways, no discernible purpose." Rule 4 amended at ratification: three legitimate
   migration routes (on touch / opportunistic / maintainer-initiated sweep); the draft's
   rationale survives as advice to a sweep's initiator, never prohibition; the two hard
   limits (no retro-editing point-in-time records; quoting defects is not violating) stand.
   Ratification question 1's YES arms the A:B:C loop — the attestation-presence commit gate
   (DESIGNED-UNBUILT in the packet) is commissioned same evening. Sub-question 2 (may an
   LLM verdict ever block): unanswered explicitly; the packet's recommendation NO is also
   the default state, so nothing blocks on LLM judgment absent a future word.
2. **Late-entry design RATIFIED, all three proposals** (design/LATE-ENTRY-AND-INTAKE-
   SEMANTICS.md status flipped, implementation commissioned same evening). His "own up"
   reading recorded in the memo's ratification note: the mechanized owning-up is the
   involuntary s23 token (why the verdict is BATCHED_DECLARED); the spirit-level duty is
   the preamble line + declared event time; no prose confession mandate — his brittleness
   instinct is agreed with and the reasoning is in the note.

## Configuration-surface survey, adopter's eyes (2026-07-11, maintainer question)

The maintainer asked whether the configuration surface is legible and easy for adopters.
Surveyed at source (new-project.sh usage block; run10's real config files; the hooks'
apparatus-reading code). Genuinely good in the small: one switchboard per world
(apparatus.json) with a closed mode vocabulary VALIDATED with teach-text on bad values;
cost_note travels IN the config with each costed mechanism (billing consent where the
decision is made); every world carries self-describing companion docs (APPARATUS.md,
HOOKS.md, GOVERNED_FILES.md); deployment.json is the single source for world facts; the
scaffold documents its flags and refuses overwrite without --force.

Not yet adopter-grade in the large — five gaps, in severity order:
1. A typo'd mechanism NAME in apparatus.json is silently ignored (mode VALUES are
   validated; nothing sweeps unknown keys — each hook reads only its own entry). Fail-open,
   the shape this project distrusts most. Cheap fix: unknown-key sweep -> loud warn/refuse.
2. Absolute autoharn paths are baked into every world's settings.json and verb shims —
   deliberate (live verbs) but it means autoharn has a fixed, unstated install-path
   contract; relocating it breaks every wired world with no teach-text anywhere.
3. No single adopter-facing CONFIGURATION document: the surface is legible in pieces but
   scattered across scaffold flags, per-world JSON files, and per-world docs;
   OPERATING-CARD is orchestrator-facing. "What can I configure, what are the defaults,
   what costs money, what needs Postgres set up first" exists nowhere as one page.
4. The Postgres prerequisite (host, db, role grants, pg_hba) is assumed, not offered — the
   hardest step of adoption has the least surface.
5. Era-coded env names (E13_GATE_*) leak internal archaeology into the surface an adopter
   reads first.

This list is the concrete content of the standing NO-PUSH bar ("until a non-expert can use
this without a frontier model"). Queued as one commission (CONFIGURATION.md meeting
ADR-0017 + unknown-key validation + install-path contract statement) AFTER the two in-
flight worktree agents land, to avoid same-file collisions. The "offered in configuration"
half for the doc discipline itself was added to the A:B:C arming agent's commission the
same hour (apparatus entry per the demurral precedent, scaffold-time).

## Maintainer priority ruling: auditability outranks agent ergonomics (2026-07-11)

Stated while run10 was live and its agent visibly struggling with compliant closure, near-
verbatim: "Although we want compliance, on a lower priority, we *also* want compliance to
be easy on the agents, but not at the cost of auditability -- in that case, it's preferred
to see the agents struggle if it's a choice between two bad things."

Standing consequence for every mechanism decision: ergonomics improvements are welcome ONLY
when they hold auditability constant (better teach-text, clearer refusal paths, tooling
that makes the compliant path the short path); any proposal that eases agents by weakening
what the record can prove is rejected at the door. An agent seen struggling is not by
itself evidence a mechanism is wrong — the run10 audit pass (queued for when the run
closes; maintainer will give the word) classifies each struggle as agent defect vs
mechanism-that-refuses-without-teaching vs legitimate-requirement-being-felt, and only the
middle class produces changes.

## bootstrap/apply-delta.sh deleted, executing the linearity ruling (2026-07-11)

The s24 commission's adversarial reviewer flagged that the script was still present and
executable although the runs-are-linear ruling (2026-07-11, transcribed in CLAUDE.md)
retired it with the explicit vocabulary "deleted, not documented." The transcription
session (this one) had updated every doc but never removed the file — an executable whose
every legitimate scenario the law had abolished is a loaded ritual waiting for a confused
operator. Deleted now; CAPABILITIES item 14 records the deletion, and item 15's stale
"remains the apply act" clause (written before the linearity ruling) is corrected in place
with a dated note. The delta path is unchanged and single: birth chain, next scaffold.

## Maintainer dispositions: adoption bar 4, run11 doc gate (2026-07-11)

- Configuration-survey gap 4 (Postgres provisioning surface) DISPOSED as a non-issue by the
  maintainer: "provisioning a postgres db is something even I can do (though I needed some
  help for the pg_hba, and that help can be FAQ'd so to speak)." Consequence: the queued
  CONFIGURATION.md commission drops the provisioning-surface ambition and gains a short
  pg_hba/setup FAQ section instead.
- Run 11 intent (maintainer): recent runs' commissions carry a mandatory documentation step;
  leverage it — run 11's world should carry the ADR-0017 doc gate applied to world-produced
  documents. Commissioned same hour as an extension to the A:B:C arming agent (world-native
  hook surface reading apparatus.json, since worlds are not git repos at scaffold time).

## Run-10 closure audit (2026-07-11)

Read-only forensic pass over run10 (`/home/bork/w/vdc/1/run10`, ledger `run10`/`run10_kernel`
on `toy`@192.168.122.1) per the maintainer's queued directive (BACKLOG "Maintainer priority
ruling: auditability outranks agent ergonomics", 2026-07-11) and the observation "the agent
implementing run10 seems to have problems actually executing compliant closure." End-state
was already CLEAN before this pass (judge AGREE asp=323/sql=323, work_item_violations empty,
audit BATCHED_DECLARED 162/162 stamped+tokened, no silence-table entries) — this audit is
about the STRUGGLE en route, not the outcome. Evidence: ledger rows 1–165 (162 landed, 3
burned — 67, 112, 113, confirmed by sequence gaps and cross-referenced against
`.claude/logs/invocations.jsonl`, 299 rows), `.claude/logs/change_gate.journal.jsonl` (2
lines), `.claude/logs/delegation_observer.journal.jsonl` (5 lines), `git log`/`git show` in
the run10 repo, and `hooks/stop_clean_exit.py` read against the run10 `.claude/apparatus.json`
(`clean_exit.mode: "enforce"`). Classification rubric is the BACKLOG entry named above,
binding: (a) AGENT DEFECT, (b) MECHANISM-REFUSES-WITHOUT-TEACHING, (c)
LEGITIMATE-REQUIREMENT-BEING-FELT — only (b) produces change proposals.

STRUGGLE INVENTORY

1. **Row 67 (burned) — invented ledger kind.** Invocation `883c071d` (15:48:16Z) ran
   `./led acceptance-criteria "QEUBO smoke-test acceptance criterion..."` — `acceptance-criteria`
   is not a member of `ledger_kind_check`'s vocabulary (`decision, assumption, question,
   verification, finding, snag, revision, note, review, work_opened, work_claimed,
   work_depends_on, work_closed`); the kernel refused the INSERT and burned sequence id 67.
   4 seconds later (`911ff8fd`, 15:48:20Z) the agent ran
   `psql ... "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname='ledger_kind_check'"`
   to self-diagnose, then 13 seconds after that (`66b3d9c0`, 15:48:33Z) retried as
   `./led --refs "row:5,row:6,docs/QEUBO.md" decision "QEUBO smoke-test acceptance criterion..."`,
   landing clean as row 68 (ts 17:48:33.782 local). Total refusal-to-compliant-retry: 17s, one
   extra diagnostic command. **Classification: (b), low severity.** `bootstrap/templates/led.tmpl`'s
   generic `<kind> <statement>` path (lines 690–717) does a raw `INSERT` with no client-side
   kind validation and no custom catch on the CHECK-constraint refusal; Postgres's bare
   "violates check constraint ledger_kind_check" error names the constraint, not the valid
   kind vocabulary, so the agent had to separately query `pg_get_constraintdef` to learn what
   `led` itself already documents in its own header comment. The refusal was correct; its
   teach-text did not name the compliant path — the agent supplied that step itself.

2. **Rows 112–113 (burned) — self-review-as-technical-independence.** Invocation `a26b78cd`
   (16:10:51Z) ran `LED_ACTOR=reviewer ./led review 110 attest technical "..."` (and a second
   review of row 111 in the same invocation) — refused by `validate_independence()`
   (kernel/lineage/s21-session-aware-distinctness.sql:137–161): rows 110/111 (the
   `reviewer-dispatch` work-item bookkeeping) and this review shared the same
   `stamp_session` (the reviewer was a Task-dispatched subagent within the SAME top-level
   Claude session, not a separate session), so "technical" independence is structurally
   impossible regardless of the differing `actor`. The exception text names the fix verbatim:
   *"Record independence='self-review' if you reviewed your own work, or have a genuinely
   distinct invocation... write the review."* 6 seconds later (`6abf45ba`, 16:10:57Z) the
   agent retried both reviews with `independence=self-review`, landing clean as rows 114/115
   — both of which quote the refusal's own reasoning verbatim in their statement text
   ("technical independence refused by the kernel: same session/agent wrote both..., per
   finding 31/s21"). **Classification: (c).** The refusal is structurally correct (a
   Task-dispatched subagent can never be session-distinct from its parent) and the teach-text
   named the compliant path explicitly; the agent complied on the very next attempt. This is
   NOT the same class as the historical LED_ACTOR defect (the run-7 generic-path bug where
   `LED_ACTOR` was silently ignored, already fixed — led.tmpl:685–688) — that was b-class;
   this is the mechanism teaching correctly.

3. **Rows 48–49 — misplaced `--amends`/`--amends-scope` flags.** At 17:42:01 local the agent
   issued two `led decision` amendments with `--amends`/`--amends-scope` positioned AFTER the
   statement text; `led.tmpl`'s own header documents flags as "consumed before `<kind>`" —
   placed after, they are silently absorbed into the statement string instead of erroring
   (no refusal fires; only the pre-existing warn-only tripwire `warn_flag_in_statement`,
   led.tmpl:289–302, prints a stderr notice: *"the statement text contains '--amends', which
   looks like one of led's own flags... NOT parsed... re-issue OUTSIDE the quotes."*). Rows
   48/49 landed malformed. 10 seconds later (17:42:11 local) the agent re-issued corrected
   versions with the flags properly positioned, landing as rows 50/51 and explicitly
   superseding 48/49 ("row 48 malformed the --amends/--amends-scope flags by placing them
   after the statement text, where led does not parse them"). **Classification: (a).** A
   documented convention (flag-before-kind ordering, stated in led.tmpl's own usage header)
   was misread on first attempt. Recovery was fast specifically because the warn-only
   tripwire caught and explained the exact mistake — the teach-text worked once triggered.
   Worth naming as a standing risk (a less attentive agent could have left 48/49 uncorrected,
   since nothing BLOCKS a misordered-flag write, it only warns) but the observed event is an
   agent misread of an existing teachable convention, not a mechanism gap.

4. **Repeated reviewer-dispatch + review-gap polling.** 5 `Agent`/Task dispatches of the
   `reviewer` principal across the session (`delegation_observer.journal.jsonl`), with
   escalating self-description in the LAST four: "Fast reviewer countersign to clear stop
   gate" (18:08:07 local) → "Countersign final ledger row 143" (18:15:35) → "Truly final
   countersign pass" (18:22:40, review-gap expected to show 6 rows: 151–156) → "Countersign
   the last row, 164" (18:28:14). Alongside these, 21 separate `./led review-gap` invocations
   span the whole session (17:42:35–18:31:07 local), clustering around two windows: two
   `sleep 20 && ./led review-gap` polls at 18:12:08/18:12:52 while waiting on a dispatched
   subagent, and six checks in the final four minutes (18:27:12–18:31:07) confirming the
   truly-clean state before the last stop. **Classification: (c).** Every `review-gap`
   invocation truthfully reported the live debt (1 row, then 6, then 1) — the mechanism never
   claimed anything was final; the orchestrator's own "truly final"/"last row" language was
   self-assessment optimism, repeatedly corrected by genuinely NEW debt each round (real
   defects surfaced by the antecedent audit, requiring their own fix→verify→close→review
   cycle). This is the two-principal SoD loop iterating until actually done, which is what
   the maintainer's ruling explicitly accepts as non-findable struggle.

5. **Row 143 — premature "stopping: commission complete", superseded by row 156.** At
   18:12:41 local the author wrote a `stopping:` disposition claiming "remains: nothing
   ledgered as outstanding" while review-gap/question-status/work-violations were
   mechanically 0 at that instant. But six EARLIER review rows (80, 83, 136, 139, 141, 142)
   had already attested `attest_with_reservations` on two substantive, real defects
   (`num_init_queries` regressing the vendor default below 5 controlled colors; `connect()`
   silently discarding accumulated preference progress on reload) — `attest_with_reservations`
   closes `review_gap` exactly like a clean `attest`, so the mechanized "clean" bar does not
   distinguish "reviewed, no issues" from "reviewed, real issues disclosed and left open."
   Reviewer's own countersign of row 143 (rows 146–147, 18:14:21–18:14:47) caught the
   mismatch: *"this row's 'remains: nothing ledgered as outstanding' framing overstates the
   state of the substantive open reservations."* This forced a second work item
   (`fix-reload-and-init-scaling`, rows 151–155), a real code fix (commit `ee44487`: `Math.min
   (20, 4*dim)` for the init-query regression; persisted fixed-swatch/controlled-set state so
   an unchanged reload resumes instead of wiping), independent re-verification (rows 157–162),
   and a corrected stopping row (156, 18:22:17 local) that names row 143's error explicitly
   and supersedes it. Total added time: ~15.5 minutes (18:12:41→18:28:11), 22 more ledger
   rows, one more subagent dispatch. **Classification: (a)**, with a caveat: the reservations
   that later drove the second closure round were ALREADY independently ledgered before row
   143 was written — a teachable signal (the agent's own prior review-mediated reservations)
   existed and was not synthesized when the stopping disposition was drafted. The CATCH itself
   (CLAUDE.md point 2's antecedent audit + reviewer SoD, which is what actually found and
   fixed this) is (c)-quality governance working as designed; the root cause of the extra
   ~15 minutes is the agent's own premature synthesis, not a mechanism gap.

MECHANISM OBSERVATION (checked in passing, per the task) — `.claude/stop_clean_exit_state.json`
existed mid-run and is absent post-run. `hooks/stop_clean_exit.py`'s `main()` calls
`_clear_state()` on every fully-clean allow (line 577) — DESIGNED, documented behavior ("A
clean stop also clears the state file, so an old fingerprint never leaks into an unrelated
future debt episode"), not an accidental deletion. Assessed against the auditability-outranks-
ergonomics ruling: the deleted file only ever held one `{debt_hash, count}` pair (the
3-strike circuit breaker's own fingerprint cache), never a history — its loss does not erase
the substantive struggle record, which lives durably in the ledger's own row timestamps and
in `delegation_observer.journal.jsonl` (both used above to reconstruct the whole closure
struggle with no gaps). However, a REAL and separate gap exists alongside it: `_journal()` is
only ever called from the OBSERVE-mode allow path (`_allow_with_observe_warning`) — never
from `_block()` (enforce-mode block) nor from `_allow_with_warning` (the circuit-breaker
fail-open path). Run10's `apparatus.json` sets `clean_exit.mode: "enforce"`, so for THIS run,
neither a blocked stop nor a circuit-breaker fail-open (had one occurred — none did; the
ledger shows no repeated-identical-debt streak reaching 3) would ever have been durably
journaled; only the now-cleared state file and an ephemeral stderr banner (session-transcript
only) would have recorded it. Nothing was actually lost for run10 specifically (the ledger +
delegation log fully reconstruct the struggle), but the design leaves a durable-audit gap for
any future enforce-mode session where the breaker actually fires or where blocked-stop counts
matter and don't happen to be reconstructable another way. This is a genuine, minor
audit-trail gap under the maintainer's own ruling — see change proposal below.

CHANGE PROPOSALS (class-b items only)

- **Item 1 fix — name the valid kind vocabulary on a `ledger_kind_check` refusal.** Smallest
  sound fix: in `bootstrap/templates/led.tmpl`'s generic `<kind> <statement>` path (around
  line 695), detect the psql exit code from the `INSERT`, and on failure append one stderr
  line naming the valid kind list (already hand-maintained in this same file's header comment
  at the `led [flags] <kind> <statement...>` usage block — no new source of truth, just
  surfaced at the point of refusal instead of only in a static comment the agent has to
  already know to re-read). Fail-safe, additive-only (adds teach-text, changes no refusal) —
  qualifies as a class-ratified fail-safe delta once scratch-witnessed per OPERATING-CARD's
  decision tree.
- **Mechanism-observation fix — journal every `stop_clean_exit` outcome, not just observe-mode
  allows.** Smallest sound fix: call `_journal()` unconditionally from all four outcome paths
  in `main()` (`_block`, `_allow_with_warning`, `_allow_with_observe_warning`, and the
  all-clean return) — mirroring the pattern `_journal()` already implements for observe mode,
  just no longer gated on `CLEAN_EXIT_MODE == "observe"`. This only ADDS a durable record of
  every Stop-gate decision (block/allow/breaker-fired/clean); it relaxes no refusal, changes
  no gate behavior, and the existing 3-strike breaker logic is untouched. Qualifies as a
  class-ratified fail-safe delta (adds a derived audit trail, nothing existing relaxed) per
  BACKLOG's own fail-safe-delta ruling — pending the scratch-witness protocol before it enters
  the birth chain.

DISPOSITION — The maintainer's impression of struggle is borne out, but not as mechanism
failure: of five identified struggle episodes, one was legitimate friction the ruling already
accepts (item 2, textbook-correct refusal with named compliant path), one was genuinely
working governance catching a real gap (item 4, the review-gap draining loop), one was a
minor, fast-recovered agent misread of a documented convention (item 3), one was a genuine
but narrow mechanism-teaching gap of low severity (item 1), and the costliest one — the
~15.5-minute, 22-row second closure round — was the agent's own premature "done" claim
overriding reservations already on its own ledger (item 5, agent defect), caught and fixed by
the SoD/antecedent-audit design working exactly as intended. Net: run10's closure took longer
than a single pass because the governance loop is doing real work — surfacing and forcing
fixes for two substantive product defects the agent would otherwise have shipped-and-stopped
past — not because the harness is hard to operate. Two small, purely-additive mechanism fixes
are proposed (kind-refusal teach-text; unconditional stop-gate journaling); neither loosens
anything, matching the maintainer's standing bar that ergonomics improvements are welcome only
when they hold auditability constant.

## Run-10 process-improvement retrospective, reconstructed from the record (2026-07-11)

A maintainer-commissioned experiment: retrospect run10 from its governed record alone (ledger,
invocation log, delegation journal, git repo), and record separately what the record turns out
UNABLE to answer — each unanswerable question being itself a harness finding. Written up as a
standing document at [design/RETROSPECTIVE-RUN10.md](design/RETROSPECTIVE-RUN10.md) (ADR-0017
compliant; passes gates/doc_shapes.py and gates/link_integrity.py). Read-only pass; no writes to
run10's world. It does NOT re-cover run10's closure fingerprints (refused ids 67/112/113, stop
discipline, countersign rounds) — that is the concurrent Sonnet forensic pass's territory and is
referenced, not duplicated.

Headline findings, each with a run11 or harness recommendation:
- FLOW: build ~22 min, governed closure tail ~25 min; 190 of 299 invocations fall in the second
  half and 47 (~16%) merely poll `./led review-gap`. Proposed: a single "distance-to-clean" verb
  (reads existing debt views only — auditability constant) to replace the piecemeal polling.
- DECISION QUALITY: all ten intake tasks closed 1:1, none split/merged; two decomposition rows
  (5, 9) over-specified downstream design and were amended (rows 43/44 → 50/51); one design
  decision (row 80 flat num_init_queries) passed its first review and was reversed by later
  passes (fix commit ee44487). Tasks 6/7/8 decomposed finer than the delivery unit (one file, one
  commit a77786c). Proposed intake conventions: state deliverable + acceptance handle, defer
  mechanism to the owning task; decompose to the unit of independent resumption.
- ASSUMPTIONS: three filed by the reviewer's antecedent audit; two discharged before code, one
  (row 144 device-local identity) left standing. None violated into rework. Keep the audit.
- DELEGATION: five reviewer subagent dispatches; review was load-bearing (changed the shipped
  product three times — commits a60d993, ee44487, and the rewritten stop row 156). Review
  load-bearingness and closure friction are the same phenomenon from two sides.
- DELIVERABLE vs COMMISSION: every task shipped witnessed, nothing silently dropped, no
  gold-plating; one disclosed narrowing (the smoke test covers the QEUBO machinery, not the
  16-color product). But the commission itself is UNLEDGERED — the diff runs against the agent's
  decomposition, not the ask.

The could-not-answer list (the experiment's second half — direct harness inputs): (1) why the two
app defects arose (oversight vs bad bet) — need an alternatives-considered decision field; (2) the
deliberation-vs-execution wall-clock split — need turn-level timing / token accounting; (3)
whether reviewer subagents read independently — the invocation log captures only Bash, so Read-tool
reads leave no trace; need per-subagent tool-call attribution; (4) the verbatim commission — absent
from the whole record, survives only as reviewer paraphrase; need it ledgered at intake; (5) cost
efficiency — no token/dollar accounting exists; (6) whether the ten-task granularity matched the
user's mental model — undecidable without the user's own breakdown. The single most consequential
gap: the harness ledgers the decomposition but never the source it decomposes.
## Late-entry discipline implemented (2026-07-11 evening, Sonnet, commissioned build from
## design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md, ratified this same evening — see the
## "Two ratifications" entry above)

All three ratified proposals delivered in one worktree pass. Per-claim witness status below;
"scratch" means an apparatus-authored throwaway schema pair, torn down to zero residue after
(verified via `information_schema`/`pg_roles` re-query, empty both times).

**Proposal 1 — intake-shape annotation (engine-side, no vocabulary change).**
`engine/lp/contemporaneity.lp` gains `intake_shape/1`: a `token_burst` is annotated when its
latest row precedes this world's own earliest `tool_event` (or when no `tool_event` exists at
all yet). `engine/contemp_audit.py` prints `intake-shape (precedes all tool activity)` on the
burst-table line. WITNESSED: `seen-red/contemporaneity-audit/run_fixtures.py` case (h)
reproduces run-10's own rows-2-11 shape (a 3-row burst before any tool activity) on a scratch
world — `VERDICT: BATCHED_DECLARED`, exit 0, the burst line carrying the annotation. The live
run-10 world itself was never touched (runs are strictly linear; a settled world is read-only
evidence, never a fixture substrate).

**Proposal 2 — declared late entries.**

- `kernel/lineage/s24-declared-event-time.sql`: a nullable `event_declared_ts` (timestamptz)
  column on `ledger`, writer-supplied (no trigger, no GUC, no HMAC — the opposite shape from
  s23's capture-only `stamp_invocation`, disclosed as such in the delta's own header).
  `ledger_current`/`countersigned_in_force` re-issued with the column appended (the s20/s23
  view-reissue discipline, re-applied); `review_gap`/`question_status`/`work_item_current`/
  `work_item_violations`/`review_stamp_distinctness` checked and confirmed NOT members of that
  class (named, not assumed) — mirrors s23's own enumeration exactly, one column later.
  WITNESSED, scratch schema `s24val`/`s24val_kernel`/`s24val_rw` (TOY db, full s15…s23 chain
  applied first): both polarities (a row with no declared time reads NULL; a row with one
  round-trips exactly); the existing HMAC/stamp machinery is BYTE-IDENTICAL before/after (a
  forged HMAC against a real provisioned secret still raises the exact same refusal; a valid
  stamp still verifies true and coexists cleanly with a declared time on the same row) — no
  trigger touched, grep-verified. `engine/ledger_differential.py s24val` (via
  `LEDGER_DEPLOYMENT`) reports **AGREE**: `asp=10 sql=10 atoms; Δasp=[] Δsql=[]` — re-run after
  real `led --event-time` writes landed through the shim, still AGREE. Class-ratified per
  CLAUDE.md's decision tree (additive only, both polarities scratch-witnessed, differential
  AGREE) — enters `bootstrap/new-project.sh`'s `--new-world` birth chain (LINEAGE_CHAIN updated,
  DDL apply list updated); NEVER applied to any existing world (runs are linear — no
  apply-to-existing-world step exists for anyone).
- `bootstrap/templates/led.tmpl`: `--event-time <iso-ts>` flag on the generic `<kind>
  <statement...>` path, writing `event_declared_ts`. Teach-text in the top-of-file comment
  (verbatim intent, not the spec's exact sentence): "recording an act after the fact? declare
  its event time — never narrate the past as if live." **Hazard caught and closed, unprompted**
  (CLAUDE.md's engineering-responsibility corollary): `led.tmpl` executes LIVE for every
  already-scaffolded world regardless of when it was born (the "live verbs" ruling) — hardcoding
  `event_declared_ts` into the generic INSERT's column list would have broken `./led` on every
  pre-s24 world the instant this template merges (a silent-breakage class this project exists to
  foreclose). Fixed with a LIVE `information_schema.columns` capability check, paid only when
  `--event-time` is actually passed (the common no-flag path is byte-identical to before, zero
  extra query): an s24-capable world writes the column; a pre-s24 world REFUSES loudly (exit 1,
  teach-text naming the fix), never a silent drop of a value the operator explicitly asked to be
  recorded. WITNESSED live on two fresh scratch worlds built end-to-end (schema, secret, `./led`
  shim): world A (s24-capable) — `--event-time` succeeds and round-trips
  (`event_declared_ts=2026-07-11 12:00:00+02`), no-flag path unaffected (NULL); world B
  (deliberately pre-s24, s15…s23 only) — `--event-time` REFUSED with the exact teach-text above,
  exit 1; world B's no-flag path unaffected (exit 0). Both worlds torn down after, zero residue.
- The verdict: `engine/lp/contemporaneity.lp` gains **LATE_DECLARED**. A burst's
  silence-breaking row (the one that would otherwise make its token BACKFILL_SUSPECT) is
  reclassified LATE_DECLARED when it carries a declared event time whose gap from its own write
  time exceeds `late_threshold_ms` (60000ms, `engine/contemp_thresholds.lp` — reasoned below the
  one real specimen on record, run-10 row 1's self-reported ~120s gap, same
  below-the-smallest-true-positive method `silence_threshold_ms` already uses).
  BACKFILL_SUSPECT now means precisely the UNDECLARED case; verdict priority is
  BACKFILL_SUSPECT > LATE_DECLARED > BATCHED_DECLARED > CONTEMPORANEOUS (loudest wins). A
  pre-s24 world emits no `row_declared/2` facts at all, so LATE_DECLARED can never fire there and
  BACKFILL_SUSPECT's pre-existing behavior is provably unchanged (the wiredness-not-corpus-
  emptiness lesson from the run9 fix, applied one delta later — `event_declared_ts_column` is a
  named capability in `engine/contemp_edb.py`'s manifest, EXCLUDED not EMPTY on a pre-s24 world).
  **SEEN-RED, BOTH POLARITIES** (`seen-red/contemporaneity-audit/run_fixtures.py`, extended,
  cases f/g — the IDENTICAL silence-then-burst gap shape, disjoint offset ranges so the shared
  scratch ledger's earlier fixture rows never bleed into a later case's own silence/backfill
  computation): case (f) declares the silence-breaking row's event time near the start of the
  ~305s silence window → `VERDICT: LATE_DECLARED`, exit 0, token named, banked verbatim as
  `late-declared-green.txt`; case (g) re-runs the identical shape with no declaration → `VERDICT:
  BACKFILL_SUSPECT`, exit 1, token named, banked verbatim as `late-declared-red.txt` — proving
  case (b)'s own pre-extension behavior is byte-identical post-s24, not merely asserted. Full
  8-case suite (`python3 seen-red/contemporaneity-audit/run_fixtures.py`, `PYTHONPATH=engine`)
  passes clean, exit 0, including case (c) live against run7's real pre-s23 schema.

**Proposal 3 — preamble line.** `bootstrap/templates/CLAUDE.md.tmpl` gains point 9, verbatim
from the ratified memo: "Record as you go — one row at the moment of the act. Batching
declarations you are making right now (an intake decomposition) is fine; the token declares it.
If you must record an act after the fact, declare its event time — never narrate the past as if
live." WITNESSED: reads correctly in the templated file; not yet exercised inside a live governed
session (UNEXERCISED, concrete blocker: no new `--new-world` scaffold was stood up by this pass
to carry it into a real session — the next scaffolded world inherits it automatically).

**Docs updated honestly:** CAPABILITIES.md item 24a (this addendum, in place, matching item 24's
own existing "same day" amendment pattern); design/CONTEMPORANEITY-AUDIT.md's own appended
Status section gains a new dated paragraph (ADR-0005 Rule 8 — the original memo and the Part
1/Part 2 status entries stand unedited). design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md itself (the
frozen ratified record) was deliberately left untouched — not in this task's named scope, and
ADR-0005 Rule 8 governs against retro-editing a point-in-time decision record.

**Gates run clean on the touched surface:** `gates/no_lazy_imports.py` (zero violations);
`py_compile` on every touched `.py` file; `sh -n` on `bootstrap/new-project.sh`; the extended
seen-red fixture suite (11/11 cases, see the audit-driven extension below). `gates/link_
integrity.py`/`gates/doc_shapes.py` were run over the touched docs before commit (see this
session's commit for the exact invocation).

**Out-of-frame hack-rationalization audit run on this diff before commit (required by the
skill's own FRAME CHECK — the implementer cannot self-audit), verdict UNDISCHARGED-HACK on the
first pass, closed same session.** A separate subagent, given only the diff and this repo (no
implementer reasoning), found: (1) `--event-time` was parsed by `led.tmpl`'s shared top-level
flag loop but silently did nothing on `led review`/`led work *` — the flag's own comment called
this "a no-op today" instead of a refusal, an inconsistency with this same file's own idiom
(missing-column case two hunks above gets a loud REFUSE) and with `warn_flag_in_statement`'s
never-silently-drop posture; (2) no fixture or script exercised `led.tmpl`'s actual `--event-time`
CLI path end-to-end — every claim of it working was unscripted prose, weaker than this project's
own "Self-application" bar; (3) `kernel/lineage/s24-declared-event-time.sql`'s own header
asserted "bootstrap/apply-delta.sh is retired" as if the script no longer existed, when it is in
fact still present, executable, and functionally capable of applying a delta to an existing world
today — a pre-existing repo state (CAPABILITIES.md item 14 already documents it as "demoted to
history" by POLICY, not deletion) that this delta's own prose stated more strongly than true.
Disposition, same session: (1) fixed — `led.tmpl` gains a coverage guard (right after the shared
flag loop) that REFUSES loudly, exit 1, naming the reason, when `--event-time` is passed to
`--recent`/`current`/`question-status`/`review-gap`/`stamp-distinctness`/`register-principal`/
`obligate`/`review`/`work`; witnessed live on a fresh scratch world before being folded into the
scripted fixture. (2) fixed — `seen-red/contemporaneity-audit/run_fixtures.py` gains a SECOND
scratch schema (`contempprobe_pre24`, s23-only, no s24) and three new cases (i/j/k) that invoke
the REAL `led` shim (the same 3-line exec-wrapper `bootstrap/new-project.sh` writes) as a
subprocess: case (i) generic-path `--event-time` success + round-trip read-back; case (j) the new
coverage-refusal on `work open`; case (k) the pre-s24-schema capability refusal, against the real
second schema. All three witnessed, exit codes as expected, both schemas torn down to zero
residue after. (3) fixed — the SQL header's claim corrected to name the discrepancy explicitly
(quoted below) rather than asserting the script's absence; deleting/neutering
`bootstrap/apply-delta.sh` itself is named as a separate, larger decision, not taken here (out of
this commission's scope; routes to the maintainer like any other destructive/ambiguous act).

**Hazard flagged, not fixed this pass (CLAUDE.md engineering-responsibility corollary — met in
passing while touching apply-delta.sh's retirement status in prose, not this commission's own
assigned task):** `bootstrap/apply-delta.sh` is still present, executable, and end-to-end
functional (`ls -la` shows `-rwxr-xr-x`, last touched by an unrelated prior commit `cba2f0c`), and
its body still resolves a world's `deployment.json`, prompts a typed confirmation, and applies an
arbitrary `kernel/lineage/sNN-*.sql` — including, as of this pass, `s24-declared-event-time.sql` —
to a LIVE, EXISTING world via `psql -f`. This directly contradicts CLAUDE.md's own "runs are
strictly linear" ruling ("there is NO apply-to-existing-world step, for anyone... bootstrap/
apply-delta.sh is retired... an operator step that is ritual rather than load-bearing is deleted,
not documented") and is stronger than CAPABILITIES.md item 14's older framing ("no operator
scenario... demoted to history... stays as history"). An operator who runs `bootstrap/apply-
delta.sh <existing-world-dir> kernel/lineage/s24-declared-event-time.sql` today would succeed,
silently violating the newer, more categorical ruling. Not fixed here: deleting or neutering a
script that other maintainer-facing docs (WALKTHROUGH.md, design/S22-WORK-ITEM-LEDGER.md) still
cite as an operator-facing act is a decision with its own blast radius, deserving its own
commission rather than a rushed side-fix inside this one — named loudly instead, per the
corollary's "fix or flag" bar.

**Deferred, named, not silently dropped:** the SQL-floor differential for the contemp_audit
verb itself (Part 2's own second-producer gap, filed since the original core landing — untouched
by this pass, still ONE producer, the ASP derivation); session-level (vs whole-ledger-window)
verdict granularity (same pre-existing filed gap); Part 3 of the ORIGINAL contemporaneity design
(the deontic/temporal ordering research direction — unrelated to this late-entry commission,
still just filed); widening `--event-time` to `led review`/`led work *` (named in the audit
disposition above as a future increment, refused loudly rather than silently today).
## ADR-0017 A:B:C attestation loop — the enforcement floor built and armed (Sonnet, 2026-07-11)

The ratification packet ("Zero-context-reader documentation discipline — ADR-0017 DRAFT +
measured enforcement", above) left the A:B:C fresh-context audit loop's commit-time
attestation-presence gate DESIGNED-UNBUILT, gated on the maintainer's word. "Two
ratifications (maintainer, 2026-07-11 evening)" gave that word: ratify ADR-0017, arm the
A:B:C loop as the discipline's primary transport, and never let any LLM verdict sit in a
blocking path (sub-question 2, answered NO). This entry is that word carried into code.

**Delivered, witnessed:**

1. **The attestation record format**, defined in
   [`gates/doc_attestation_presence.py`](gates/doc_attestation_presence.py)'s own module
   docstring (the ADR names no filename for this decision, so the format lives where the
   gate that reads it lives — the smallest sound place, said plainly there). One JSON object
   per line in the git-tracked, append-only `attestations/doc-legibility-attestations.jsonl`:
   which document and content-hash a fresh-context B read, B's self-declared identifying
   string, one object per B→C round (verdict, and either per-finding `file`/`line`/`quote`/
   `repair` specimens or the four checked Rule-1 clauses), and an `escalated` flag. Chosen
   over agent-identity checks per the ADR's own instruction ("the enforced surface is the
   attestation, not the agent's identity... identity enumeration fails open"). The ADR's
   instance-bindings note that a wired kernel world could ride
   `countersign_obligation`/`review_gap` for this relation is real but does not apply here:
   autoharn's own repo carries no world ledger, so the record lives in-repo, per the
   commission's own instruction not to touch kernel/.

2. **The attestation-presence commit gate**,
   [`gates/doc_attestation_presence.py`](gates/doc_attestation_presence.py): checks PRESENCE
   (a record exists whose content hash matches the doc's current bytes) and SHAPE (per-round
   validity, the two-round cap, an unescalated still-DEFECT final round refused) — never the
   attestation's conclusions, mechanizing the ratified sub-question-2 answer literally in
   code, not just in prose. **Armed ENFORCE, not observe-first**, because the ADR's own text
   says so, not by this pass's assumption: "The fresh-context audit loop" section states the
   gate's enforcement surface as "deterministic and commit-time-blockable once built," and
   Revisit-when #2 names it the one exception to the tenet's unmeasured-promotion bar ("may
   be built and armed on the packet's word") — the packet's word already said yes. Unlike the
   costed critic hook, this gate spends nothing (a hash lookup and a JSON shape check), the
   same free-per-commit class as `gates/doc_shapes.py` and `gates/link_integrity.py`, neither
   of which carries an apparatus.json switch — so this gate carries none either.
   Scope/exclusions (every one printed by the gate itself, per the ADR's own printed-
   exclusion convention): `BACKLOG.md` wholesale (point-in-time dated entries — this entry
   included), `judgment/**` wholesale (declared history, matching `gates/link_integrity.py`'s
   own exclusion), and an inline `<!-- doc-attest-exempt: <reason> -->` waiver.
   WITNESSED both polarities: `seen-red/doc-attestation-presence/red.txt` (RED on a missing
   attestation; three malformed-record shapes refused at write time and never appended to the
   ledger; GREEN once a well-shaped record is recorded; report mode never fails); registered
   in `gates/fixture_census.py` REGISTRY, census re-run clean at 36 seen-red gates.
   **A live hazard the build caught in itself, fixed before shipping:** the waiver check was
   first written as a bare substring match, and it self-triggered — the recipe document
   below explains the waiver token in worked-example prose, and that explanation alone
   produced a false wholesale exemption. Fixed by requiring the token inside an HTML comment
   (`<!-- doc-attest-exempt: reason -->`), the same device `gates/link_integrity.py` already
   uses to keep a code-fenced example from being mistaken for a real link; the fixture pins
   the regression (`WAIVER-NOT-PROSE` case).
   **Not wired into `hooks/pre-commit`** — this commission's own constraint forbids editing
   hooks/ existing files while a governed session (run10) is live. The exact stanza to drop
   in (mirroring the `link_integrity.py` block already there) is printed in the gate's module
   docstring under "WIRING STANZA," ready for the orchestrator once the freeze lifts.
   **Flagged in passing, not fixed (same frozen file):** `gates/doc_shapes.py`, though built
   and seen-red days earlier, is *also* not actually invoked from `hooks/pre-commit`'s body
   despite the header comment's "FINAL WIRING" note listing it — a pre-existing gap this pass
   noticed but did not cause and cannot touch.

3. **The workflow recipe**, [`design/ABC-AUDIT-LOOP-RECIPE.md`](design/ABC-AUDIT-LOOP-RECIPE.md)
   (the ADR names no companion-doc location for this, so a new `design/` note, per the
   commission's own fallback instruction): step-by-step, self-contained instructions for
   spawning B as a genuinely fresh `Agent`-tool invocation, the two-round cap, the
   non-converging-review-loop escalation, and recording the result.
   **This recipe was itself run through a real A:B:C loop while being written**, not merely
   asserted compliant: a fresh `Agent`-tool invocation (`general-purpose`, no parent
   conversation context, prompt carrying only ADR-0017's complete verbatim text and the
   recipe's text — nothing else) served as B. Round 1 found two genuine defects (a cost
   figure mis-cited to the wrong ADR-0017 section; a bare unlinked `BACKLOG` citation
   inconsistent with the document's own convention); both were fixed; a second fresh B
   invocation returned CLEAN across all four Rule-1 clauses, explicitly checking every
   ADR-0017-attributed quotation in the document against the ADR's real text. Two rounds,
   converged, not escalated. The attestation is recorded in
   `attestations/doc-legibility-attestations.jsonl` with both rounds' findings and verdicts.
   (A methodological note for whoever runs this loop next: an earlier, discarded attempt fed
   B an abridged paraphrase of ADR-0017 instead of its literal text, and B correctly flagged
   two accurate quotations as unresolvable — an artifact of the abridgement, not a real
   defect. The recipe's own step 2 says "paste in the full text" for exactly this reason; the
   discarded attempt is why that line is there, not a hypothetical.)

4. **The "offered in configuration" half** (orchestrator-added mid-commission, closing the
   half of ADR-0017's portability intent that "arm it for autoharn" alone does not reach):
   `bootstrap/templates/apparatus.json` and `bootstrap/templates/APPARATUS.md` now carry a
   `doc_legibility_critic` mechanism entry, shaped exactly like `demurral_detect`'s (`mode:
   "off"`, `cost_note`, `classifier_command`, `timeout_s`) — the one ADR-0017 mechanism a
   freshly scaffolded world's own hook actually reads (`hooks/doc_legibility_critic.py`'s
   `MECHANISM_KEY`). No apparatus.json key was added for the attestation-presence gate: it
   is autoharn-repo-side only (its ledger and its git-history assumptions are this repo's,
   not a fresh scaffold's), and per this file's own convention a free deterministic gate
   (`doc_shapes.py`, `link_integrity.py`, now this one) is not switchboard-gated at all — a
   dead key nothing reads would have been the exact defect the commission warned against.
   `bootstrap/new-project.sh` was not edited (it only `cp`s the templates); editing the
   templates was verified safe against a live session before doing it — they are copied
   once at scaffold time, never re-read from a running world, unlike hooks/ files. This
   closes the "offered in the configuration" half of ADR-0017's portability intent, alongside
   the arming above.

**How the two just-ratified pieces compose:** the A:B:C primary-transport decision (ADR-0017's
"fresh-context audit loop" section) names *who* does the reading (a fresh fork) and *what*
shape the verdict must have; this pass's attestation-presence gate is the *commit-time floor*
under that transport — it does not care whether the record came from a real A:B:C run, a
human doing the same thing by hand, or (structurally, if someone chose to) a fabricated
claim, because the ADR's own design explicitly declines to police that ("the gate checks the
record, indifferent to how the file was written"). The two are deliberately decoupled at that
seam: the workflow produces evidence, the gate demands evidence exists and parses, and never
the twain audit each other's honesty — that gap is named, not hidden, and is exactly the gap
Revisit-when #2 leaves open for a future promotion question once live attestations exist to
measure.

**Deferred, with blockers:**
- Wiring `gates/doc_attestation_presence.py` into `hooks/pre-commit` — blocked on the
  standing "never modify hooks/ while a governed session is live" rule (run10); stanza
  prepared in the gate's own docstring.
- The pre-existing `gates/doc_shapes.py` pre-commit non-wiring, noticed in passing — same
  blocker, not this pass's defect to fix.
- Back-catalog attestation debt: `python3 gates/doc_attestation_presence.py` (report mode,
  no args) currently lists every tracked `.md` file outside `BACKLOG.md`/`judgment/**` as
  unattested (report mode, never fails) — expected and correct per Rule 4's binds-on-touch
  posture; not a gap to close by sweep.

Every claim above is WITNESSED (fixture output banked at the named seen-red path, or the
live Agent-tool transcript this entry describes), or explicitly deferred with its blocker
named. No umbrella claims.

## ADR-0017 world-side doc_shapes gate — offered for run11 (Sonnet, 2026-07-11)

Second orchestrator extension of the same commission (maintainer instruction, near-verbatim):
"One nice side-effect of the task that our recent runs have, is a mandatory documentation
step; we should leverage that opportunistically for run11 and apply the doc gate there, if
possible." This entry makes `gates/doc_shapes.py`'s two measured-sound checks (standalone
fragment paragraphs; bare positional HANDOFF references) reachable INSIDE a scaffolded world,
not only against this repo's own tree.

**Delivered, witnessed:**

1. **`hooks/pretooluse_doc_shapes_gate.py`** — a new hook (safe to add per this commission's
   own constraint: new files in `hooks/` are inert until wired). PreToolUse on `Write`/`Edit`
   of a `.md` file, not PostToolUse: a scaffolded world is not a git repository at scaffold
   time (`run10`'s task 1 was `git init`), so a pre-commit surface has nothing to attach to —
   the sound surface is the write itself, refusing a defective document before it lands, the
   same PreToolUse-deny contract `hooks/pretooluse_change_gate.py` already uses (identical
   `permissionDecision`/`permissionDecisionReason` JSON shape, identical exit codes) rather
   than inventing a second refusal vocabulary. It imports `gates/doc_shapes.py` directly by
   path (sibling directory, same checkout every scaffolded world already references
   absolutely for every other hook) — one judgment, one home, ADR-0012 P1. For a `Write`, the
   full proposed content is checked directly; for an `Edit`, the current on-disk file is read
   and `old_string`→`new_string` applied to reconstruct the FULL post-edit content before
   checking — necessary because the FRAGMENT check is context-sensitive (it looks at the
   blank-or-not lines around a candidate paragraph), so checking an isolated `new_string`
   snippet would misjudge its edges as the whole file's edges. WITNESSED both polarities plus
   four more cases: `seen-red/doc-shapes-gate-world/red.txt` — ENFORCE denies a defective
   `Write` naming both checks (exit 2); ENFORCE silently allows a clean `Write` (exit 0);
   OBSERVE allows the identical defective `Write` with a loud `additionalContext` warning;
   OFF is silent regardless of content; a MISSING `apparatus.json` resolves to observe
   behavior (never off, never enforce); an `Edit`'s reconstructed content is checked and the
   deny names the REAL target path, never the internal temp file. Registered in
   `gates/fixture_census.py` REGISTRY as `doc-shapes-gate-world`; census re-run clean at 37
   seen-red gates.

2. **Default mode: `observe`, not `off` and not `enforce` — the arming-mode question answered
   from first principles, not by copying the critic's or the repo-side gate's defaults.** Not
   `"off"`: this check spends nothing (pure text scanning, no `claude -p` call), so the "no
   world may silently bill its operator" reason that keeps `demurral_detect`/
   `doc_legibility_critic` off by default does not apply — a free check with nothing to hide
   costs nothing to expose. Not `"enforce"`: this is the FIRST time `gates/doc_shapes.py`'s
   two checks run as a LIVE, interactive, write-time blocking gate anywhere — even this
   repo's own pre-commit chain does not yet invoke it (the pre-existing gap flagged in the
   entry above) — so its measured false-positive rate (18 fragment hits / 208 docs, 1
   HANDOFF-positional hit, both near-zero after exemptions) is measured against this repo's
   OWN static corpus, not against the different shape of documents a fresh world's agents
   write in real time. `"observe"` matches this project's own precedent for a newly
   introduced observation point (`mutation_observer`, `delegation_observer` both defaulted to
   `"observe"`, never `"enforce"`, on first introduction). **The one-line flip to enforce for
   run11 specifically**, if the maintainer wants it live-blocking from birth: set
   `"doc_shapes_gate": {"mode": "enforce"}` in run11's `.claude/apparatus.json` under
   `mechanisms` — no code change, no re-scaffold, live on the very next `Write`/`Edit` of a
   `.md` file inside that world. This is the orchestrator's one-line offer to the maintainer
   at scaffold time, named per this project's self-application standard (every orchestrator
   choice explained on the record).

3. **Offered in the switchboard, not just built.** `bootstrap/templates/apparatus.json` now
   carries `"doc_shapes_gate": {"mode": "observe"}` (a bare entry, no `cost_note` — nothing
   costed to disclose); `bootstrap/templates/APPARATUS.md`'s table grew from eight to nine
   mechanisms and its "Named nuances" list grew a matching bullet, both WITNESSED against a
   real A:B:C loop on the added text (two rounds: round 1 found undefined "world" jargon and
   an awkward forward-pointing "for that reason," both repaired; round 2 CLEAN), recorded in
   `attestations/doc-legibility-attestations.jsonl`. **`bootstrap/templates/settings.json.tmpl`**
   grew a new `PreToolUse` block, matcher `Write|Edit`, wiring
   `hooks/pretooluse_doc_shapes_gate.py` with `GATE_SUBJECT_ROOT=__PROJECT_ROOT__` — the same
   two placeholders (`__PROJECT_ROOT__`, `__AUTOHARN_ROOT__`) every other entry in that file
   already uses, substituted the same way by `bootstrap/new-project.sh`'s existing `sedsubst`
   (no new placeholder needed). Editing these three template files was verified safe against
   the live run10 session before doing it, same reasoning as the apparatus-offering entry
   above: `bootstrap/new-project.sh` only `cp`/`sed`s them once at scaffold time into a new
   world's `.claude/`; they are never re-read by an already-running session.

**Composition with the earlier extension in this same session:** the two apparatus.json
entries this commission added (`doc_legibility_critic`, `doc_shapes_gate`) sit side by side in
one switchboard, as instructed — the costed LLM critic (off by default, per-`.md`-write
`claude -p` cost) and the free deterministic write-time gate (observe by default, first live
deployment) are visibly distinct choices an operator scaffolding a new world can see and set
independently, never a single conflated "doc discipline" toggle.

**Deferred, with blockers:** none new. The same `hooks/pre-commit` freeze named in the entry
above does not apply here — this hook is wired via the SCAFFOLD templates, not the live
`hooks/pre-commit` file, and is therefore live for the very next world scaffolded after this
commit merges (run11, if scaffolded after).

Every claim above is WITNESSED (fixture output at the named seen-red path, the live A:B:C
transcript this entry describes, or a direct subprocess run quoted in this session's own
tool-call record) or explicitly named as a deferred/no-blocker case. No umbrella claims.

## Run-10 closure audit — both class-b fixes landed (2026-07-11, integration-merge-window
## worktree)

Delivers both change proposals filed in "Run-10 closure audit (2026-07-11)" above, plus a
second hazard caught in passing per CLAUDE.md's engineering-responsibility corollary
(`gates/doc_shapes.py` was built and seen-red but never actually wired into `hooks/pre-commit`,
flagged by name in `gates/doc_attestation_presence.py`'s own docstring — fixed here alongside
its sibling rather than left for a future pass).

**Item 1 — `bootstrap/templates/led.tmpl` names the valid-kind list on a `ledger_kind_check`
refusal.** A new `_led_kind_refusal_teach()` function, called identically from both INSERT
shapes (event-time column present or not — factored once, not duplicated per shape) ONLY after
their own `psql` invocation has already failed. Detection is deliberately NOT a grep of psql's
error TEXT (which could read differently across postgres versions): it independently re-queries
`pg_get_constraintdef` for `ledger_kind_check` scoped to this schema's own `ledger` table (never
a second hand-maintained kind enumeration to drift out of sync with s22's kernel-side one — the
vocabulary already drifted once), and only prints the extra teach block if `$kind` is genuinely
absent from that live list — so a non-kind INSERT failure (a bad `--supersedes` id, etc.) is
untouched, unrewrapped, unswallowed, same exit code as before. The success path is not
wrapped at all in a way that changes its output — `if psql ...; then :; else ...; fi` mirrors
this file's own `set -euo pipefail`-safe idiom (a command tested as an `if` condition does not
trigger `set -e`), so a valid write's stdout/stderr are exactly what `psql` itself produces,
untouched.

WITNESSED, both polarities, extending `seen-red/contemporaneity-audit/run_fixtures.py` (cases
l/m, THIRTEEN cases total now) — real `led` shim, real scratch schema (`contempprobe`/
`contempprobe_kernel`/`contempprobe_rw`, TOY db), full suite exit 0:

```
# CASE l (led kind-refusal teach, run-10 row-67 specimen): exit=3, REFUSED, original ledger_kind_check error preserved, live valid-kind list now taught (decision/assumption/work_opened/review confirmed present)
# CASE m (success path, OLD vs NEW led.tmpl): exit_old=0, exit_new=0, stdout byte-identical ('SET\nSET\nINSERT 0 1\n')
```

Case (m) is a REAL old-vs-new diff, not an assertion pinned to a hardcoded string: one shim
execs this commit's own PARENT `led.tmpl` (`git show HEAD:bootstrap/templates/led.tmpl`, read
into a throwaway temp file, AUTOHARN passed explicitly via led.tmpl's own already-documented
override since the copy lives outside the checkout tree), the other execs the just-edited file;
both writes' stdout compared byte-for-byte and found identical.

The run-10 row-67 specimen itself, reproduced live outside the fixture suite for the literal
transcript (`./led acceptance-criteria "QEUBO smoke-test acceptance criterion..."` against a
fresh scratch schema, s24-capable, torn down after):

```
ERROR:  new row for relation "ledger" violates check constraint "ledger_kind_check"
DETAIL:  Failing row contains (1, 2026-07-11 19:27:52.535863+02, main, acceptance-criteria, ...).

led: 'acceptance-criteria' is not a member of ledger_kind_check's vocabulary (the refusal above).
  valid kinds (live, queried from the kernel's own constraint definition -- never
  hardcoded here): assumption, decision, question, verification, finding, snag, revision, note, review, work_opened, work_claimed, work_depends_on, work_closed
```

The same schema's valid-kind write (`./led decision "..."`) landed exit 0 with stdout
`SET\nSET\nINSERT 0 1\n` — unchanged. Scratch schema torn down to zero residue, re-verified
directly: `SELECT nspname FROM pg_namespace WHERE nspname LIKE 'contempprobe%'` and `SELECT
rolname FROM pg_roles WHERE rolname LIKE 'contempprobe%'` both returned empty after teardown.

**Item 2 — `gates/doc_shapes.py` and `gates/doc_attestation_presence.py` wired into
`hooks/pre-commit`.** Both ordered after the existing `link_integrity` block (staging_guard ->
no_lazy_imports -> fixture_census -> link_integrity -> doc_shapes -> doc-attestation-presence ->
layout_census (disabled) -> doc-legibility (report-only)), sharing one `git diff --cached
--name-only --diff-filter=ACMR -- '*.md'` computation rather than running it twice. The
doc-attestation-presence stanza is the gate's own docstring WIRING STANZA applied verbatim
(only generalized to the shared touched-file variable); doc_shapes gets the analogous shape,
matching the chain's existing invocation style (a `"$PY" gate.py ARGS || { teach-text; exit 1;
}` block per gate). Neither gate is softened — doc-attestation-presence stays authored ENFORCE
per ADR-0017, no observe/off mode added.

WITNESSED, both refusals AND a clean pass, via a scratch commit cycle in this worktree (using
`git -c core.hooksPath=hooks commit ...` to point at THIS worktree's own `hooks/pre-commit`
rather than the shared `.git/config`'s `core.hooksPath`, which — a pre-existing worktree
config quirk, unrelated to this commission and left untouched — currently resolves to the main
checkout's `hooks/` for a bare `git commit`; the override is a single-invocation flag, no
lasting config change). A scratch file `design/_scratch_gate_witness.md` (created, exercised,
then fully removed — never landed in a real commit) carrying a deliberate FRAGMENT violation:

```
doc_shapes (gate mode): 1 finding(s) across 1 file(s)
  design/_scratch_gate_witness.md:7: FRAGMENT standalone 1-word paragraph ('Nope.') — a noun phrase is not a paragraph; write the sentence (or waive with 'doc-shapes-allow: <reason>')

pre-commit: doc-shapes gate FAILED — a changed doc has a legibility shape defect
(FRAGMENT or HANDOFF-POSITIONAL; see gates/doc_shapes.py's own header).
```

Same file, fragment fixed (clean prose) but carrying no attestation record — the SAME commit
attempt now clears doc_shapes and is refused one gate later:

```
doc_attestation_presence (gate mode): 1 finding(s):
  design/_scratch_gate_witness.md: NO-ATTESTATION no fresh-context attestation record in attestations/doc-legibility-attestations.jsonl matches this file's current content (sha256 426008abd73e...) — run the A:B:C loop (design/ABC-AUDIT-LOOP-RECIPE.md) and record it with 'gates/doc_attestation_presence.py --record', or waive with '<!-- doc-attest-exempt: <reason> -->' if this is a point-in-time record or quoted-defect specimen the wholesale exclusions do not already cover

pre-commit: doc-attestation-presence FAILED — a changed doc carries no
fresh-context attestation record for its current content (ADR-0017).
```

The scratch file was then unstaged and deleted (`git reset HEAD --`, `rm`) before any real
commit — it never landed. "A clean commit passes" is witnessed by this commission's own real
commits below: this very BACKLOG append touches `BACKLOG.md`, which both gates exempt by name
(doc-attestation-presence's `EXCLUDE_FILES_WHOLESALE`, ADR-0017's own "point-in-time dated
entries" exception) — a real, non-scratch commit that touches a real in-scope `.md` and clears
the whole chain, printed live: `doc_shapes (gate mode): clean` / `doc_attestation_presence
(gate mode): ... excluded ... BACKLOG.md — point-in-time dated entries (ADR-0017 Exceptions)`.
No attestation was authored for this entry (none needed — the exclusion is the intended path
ADR-0017 names for exactly this document class), matching the task's own instruction that a
touched doc tripping the gate is the discipline working as designed, not a bug to route around.

**Deferred, with blockers:** none. Neither item touches `kernel/lineage`, `law/`, or
`engine/lp/` semantics, so neither is a kernel-lineage delta requiring birth-chain ratification
— item 1 is a purely additive teach-text change to a live template (already class-ratified
fail-safe per BACKLOG's own proposal above: adds teach-text, changes no exit code, nothing
existing relaxed); item 2 wires two already-authored, already-ratified gates (`doc_shapes.py`
registered days ago; `doc_attestation_presence.py` "authored ENFORCE... ratified" per its own
docstring and ADR-0017) into an existing chain, softening neither. Both scratch-witnessed on
both polarities as shown above.

**Self-caught hazard, fixed same session:** while wrapping up item 1's witness, case (m) of
`run_fixtures.py` was found comparing led.tmpl's success-path output against `git show
HEAD:bootstrap/templates/led.tmpl` — correct only in the window between editing the file and
committing the fix; the instant that commit (`e1059ef`) landed, `HEAD` walked past it and every
future run would silently diff the fixed file against itself, a vacuous pass that never errors
and stops proving what its own comment claims. Pinned to a fixed historical SHA
(`PRE_KIND_TEACH_FIX_SHA = 95622f3`, `e1059ef`'s own parent) instead, with a `ck()` that asserts
the pinned commit genuinely predates the fix (no `_led_kind_refusal_teach` in its content)
rather than trusting the SHA by convention — commit `485e463`. Full suite re-verified clean,
exit 0, scratch schema torn down to zero residue.

## First live enforcement of ADR-0017's loop — on the orchestrator's own merge (2026-07-11)

The run10-window merge train (landed 33f6a9d) was REFUSED by the just-wired
doc_attestation_presence gate: two edited docs (CAPABILITIES.md,
design/CONTEMPORANEITY-AUDIT.md) carried no fresh-context attestation. The compliant path
was followed, not waived: two fresh-fork B reviewers (Rule 4 remit: edited sections +
opening), 13 findings total round 1 — including "the harness" undefined in CAPABILITIES'
first line, the purest author-context-blindness specimen yet — all repaired; the
contemporaneity memo closed CLEAN round 2; CAPABILITIES' round 2 found ONE new defect
INTRODUCED BY a round-1 repair (crossed parenthetical referents), hit the two-round cap,
and ESCALATED per the recipe — the orchestrator, as escalation recipient, adjudicated by
applying B's own suggested one-clause reorder verbatim. Both attestations recorded
(CAPABILITIES' with escalated=true); the merge then passed every gate on earned evidence.

SEAM FOUND by this first live escalation, for the ADR's next revisit: the attestation
record format has no field for the escalation recipient's adjudication — it lives in b_id
free text today. Also committed alongside: the run10 ./judge DerivationRecord pair from
the closure audit (engine/docs/ledger-marriage/derivations/run10/), the audit's own banked
evidence. HANDOFF.md is now materially stale (pre-dates this entire day) — refresh queued
as the next standing task before any session handoff.

## Five-item batch, maintainer-approved 2026-07-11 evening (Sonnet, executed same window)

Delivers all five items the maintainer approved in one commission: (1) a composed
distance-to-clean verb, (2) the `commission` ledger kind with two signing modes, (3) a
read-observer journal hook, (4) intake-granularity teach-text, (5) an alternatives-considered
decision convention. No `run11` session ever appeared under `/home/bork/w/vdc/1/run*` during
this work (`pgrep -a claude` + `readlink /proc/<pid>/cwd` re-checked before every
`bootstrap/templates/`/`bootstrap/new-project.sh` edit; only this checkout's own sessions and
the operator's parent-dir/daemon processes were ever live) — nothing was frozen mid-work.

**Item 1 — `distance-to-clean` composed closure-debt verb
(`bootstrap/templates/distance-to-clean.tmpl`; design/RETROSPECTIVE-RUN10.md Finding 1).** The
maintainer's condition, honored literally: `led review-gap`/`question-status`/`work violations`
stay untouched and remain the documented, disaggregated default. This is a sixth operator verb,
wired into `bootstrap/new-project.sh`'s shim loop, reading the SAME three existing views in one
pass, computing nothing new. **WITNESSED live** on a throwaway `--new-world` probe
(`batch5probe`, torn down after, zero residue re-verified): a clean world reports `TOTAL debt: 0`
exit 0; after registering a real obligation and writing an unreviewed row, an open question, and
a work item with a dangling dependency, it reports `review-gap: 6 row(s) -- ids: [2, 3, 4, 5, 6,
7]`, `question-status: 1 open of 1 total -- open ids: [6]`, `work-violations: 1 violation(s) --
slugs: [widget-x]`, `TOTAL debt: 8`, exit 1 — cross-checked id-for-id against
`led review-gap`/`question-status`/`work violations` run separately on the same probe (identical
rows). CAPABILITIES.md item 25.

**Item 2 — `commission` ledger kind, two signing modes (`kernel/lineage/s25-commission-
kind.sql`; design/RETROSPECTIVE-RUN10.md Finding 5 + could-not-answer item 4).** A pure
vocabulary UNION on `ledger_kind_check` (s22's own re-issue point, one member later) — every
prior kind stays legal, unchanged; no new column, no new table, no new view, no trigger touched.
Class-ratified per CLAUDE.md's decision tree (additive vocabulary only). Closure statement
(ADR-0000 2026-07-02 amendment) in the delta's own header: quantification universe grepped
across kernel/lineage/*.sql (frozen, untouched), engine/lp/*.lp (zero kind-literal hits — kind is
an opaque atom there), engine/*.py (zero closed-set hits), and led.tmpl's own
`_led_kind_refusal_teach()` (re-queries the live constraint, never a hand-copy — needs zero
led.tmpl change to pick up the new member).

SCRATCH-WITNESSED, both polarities, differential AGREE:
```
=== a-commission-legal-post-s25 === [ok] exit=0 id=1
=== b-refs-commission === [ok] refs=row:1
=== c-existing-kinds-unchanged === [ok] decision_ok=True work_opened_refused_by=work_slug_kind_shape
=== d-invalid-kind-still-refused === [ok] refused=True live_def_has_commission=True
=== e-full-mode-actor-distinct === [ok] full_actor='commissioner' lazy_actor='author'
=== f-prior-columns-untouched === [ok] columns=event_declared_ts,stamp_hmac,stamp_verified
=== g-pre-s25-refused-with-teach === [ok] exit=3, teach names the pre-s25 world's OWN 13-member list (no 'commission')

# marriage differential -- ASP T_now (ledger_tnow.lp) vs SQL floor (ledger_floor.py)
  [OK ] s25fxprobe AGREE              asp=10 sql=10 atoms; Δasp=[] Δsql=[]
# DIFFERENTIAL GREEN
[ok] zero residue: schemas='' roles=''
```
Full suite: `seen-red/s25-commission-kind/run_fixtures.py`, banked at `red.txt`, registered in
`gates/fixture_census.py` (39 seen-red gates, clean). Entered `bootstrap/new-project.sh`'s
`LINEAGE_CHAIN` and DDL apply list; **NEVER applied to any existing world** (runs are linear).

**FULL mode**: `bootstrap/new-project.sh --new-world` now registers a `commissioner` principal
(class `human`) alongside `author`/`reviewer`, and prints this exact copy-paste line at the end
of every scaffold run (WITNESSED verbatim, `batch5probe`'s real stdout):
```
To SIGN this run's commission yourself (FULL mode -- kernel/lineage/s25-commission-
kind.sql; the ask carries the commissioner's own guarantee, not a vicarious one), type
this in YOUR OWN terminal, inside <PROJECT_ROOT> (not inside the agent's session):
  LED_ACTOR=commissioner ./led commission "<the ask verbatim>"
```
**WITNESSED live** on `batch5probe`: `LED_ACTOR=commissioner ./led commission "Build a widget
that does X..."` landed `id=1, kind=commission, actor=commissioner, stamp_agent=NULL,
stamp_verified=f` — the honest "unstamped-but-attributed" row the design names (typed from a
bare shell, no live Claude session to inject a stamp). A second write under the default actor
with the vicarious-transcription prefix landed `id=2, actor=author` — the two rows are
mechanically distinguishable by actor alone here; in a REAL governed session LAZY mode's row
would additionally carry a live `stamp_agent`/`stamp_verified=t` (this probe was a bare-shell
test, not a live Claude Code session, so only the actor half of the two-signal distinction was
exercised for LAZY mode — named honestly, not overclaimed).

**LAZY mode**: `bootstrap/templates/CLAUDE.md.tmpl` point 10 — the FIRST ledger act on receiving
a commission is `./led commission "<ask verbatim>"`, prefixed "(vicarious transcription by the
implementer; carries no commissioner guarantee)" IN ADDITION to the stamp already proving it
vicarious by construction. Decomposition rows `--refs row:<commission-id>`.

**Pre-s25 interaction VERIFIED, not assumed**: a `commission` write against a genuinely pre-s25
world (schema applied through s24 only) is refused by `ledger_kind_check`, exit 3, and the
run-10 closure-audit fix's live teach-text names that world's own 13-member list — no
`commission` — proving the interaction works with zero `led.tmpl` change, exactly as designed.
CAPABILITIES.md item 26.

**Item 3 — Read-observer journal (`hooks/pretooluse_read_observer.py`;
design/RETROSPECTIVE-RUN10.md could-not-answer item 3: "a reviewer that inspects files via the
Read tool leaves no trace").** New `PreToolUse(Read)` hook, mirrors `hooks/
pretooluse_delegation_observer.py`'s shape/switchboard/UTC-Z convention exactly: journals ts
(UTC-Z), session_id, file_path to `.claude/logs/read_observer.journal.jsonl`. No warning, no
deny path — reading is never a policy violation, so `enforce` is a NAMED-NOT-YET-SANCTIONED
downgrade, not an impossibility. Default `mechanisms.read_observer.mode = "observe"` (costless
observer, house convention: defaults ON like `mutation_observer`/`delegation_observer`). Wired
into `bootstrap/templates/settings.json.tmpl` (`PreToolUse` matcher `Read`) and `bootstrap/
templates/apparatus.json`. **WITNESSED, both polarities**, `seen-red/read-observer/
run_fixtures.py` (6 cases, pure filesystem, no DB): observe-default journals one line;
mode=off writes nothing even though a real Read happened; mode=enforce downgrades with a
loud stderr warning and still journals; a non-Read tool call produces nothing; an unwired
invocation is silent; two further real reads append two more lines in order (accumulation, not
overwrite) — all green, registered in `gates/fixture_census.py`. **Re-witnessed live** on the
final `finalprobe` scaffold (torn down after): the real hook, invoked through the real wiring
path, journaled `{"ts": "...Z", "session_id": "final-check", "file_path": "/etc/hostname"}`.
CAPABILITIES.md item 27.

**Item 4 — Intake-granularity teach-text (`bootstrap/templates/CLAUDE.md.tmpl` point 1,
amended).** Judgment guidance, no numeric rule, per the maintainer's explicit warning against a
cargo-cultable count: "decompose to the UNIT OF INDEPENDENT RESUMPTION ... state each item's
deliverable and its acceptance handle, and leave the mechanism/HOW to the task chartered to own
it," with the one-question test ("could a fresh session pick up this slug alone and know what
to build and how to tell it's done?") and both failure directions named (too fine: run10's three
items that collapsed to one file/one commit; too coarse: a hidden resumable seam).

**Item 5 — Alternatives-considered convention (`bootstrap/templates/CLAUDE.md.tmpl` point 11,
new).** "A load-bearing decision names what was rejected and why, IN THE STATEMENT."
Convention only — explicitly filed as awaiting a witnessed need before any kernel column is
built, stated as such in the preamble text itself, not silently implied.

**A:B:C fresh-context attestation loop, both edited maintainer-facing `.md` files.**
`bootstrap/templates/APPARATUS.md` (new `read_observer` row + Named-nuances bullet, "nine" ->
"ten" mechanisms): round 1 DEFECT (1 finding — the illustrative JSON example was missing the
new mechanism's entry, inconsistent with the table it sits beside), fixed, round 2 CLEAN
(all four Rule-1 clauses enumerated). Attestation recorded, `escalated: false`.
`CAPABILITIES.md` (items 25-27 added): round 1 DEFECT (2 findings — a stale "four operator
verbs" claim in the opening, and item 25's own "sixth verb" enumeration silently missing the
scaffold as the fourth prior verb), fixed; round 2 DEFECT (2 NEW findings — a dangling
"CLAUDE.md's decision tree" cross-reference that actually lives in OPERATING-CARD.md, and an
unglossed first-and-only use of `delegation_observer`), hit the two-round cap per ADR-0017 (no
third round). **Non-converging-review-loop escalation, adjudicated by the orchestrator**
(the same disposition the "First live enforcement" entry above set as precedent): both round-2
findings fixed by applying B's own suggested repairs verbatim, no third B round spawned.
Attestation recorded, `escalated: true`, `rounds` carrying both real B verdicts as they
happened. `gates/doc_shapes.py`/`gates/link_integrity.py` clean on both files throughout;
`gates/doc_attestation_presence.py` gate mode: clean, 2/2 docs in scope.

**Gates run clean on the touched surface:** `gates/no_lazy_imports.py` (0 violations, whole
repo); `py_compile` on every touched `.py` file; `sh -n` on `bootstrap/new-project.sh` and
`bootstrap/templates/led.tmpl` (verified UNCHANGED — the generic `<kind> <statement...>` path
already supports `commission` with zero code change, confirmed by direct exercise, not
assumed); `gates/fixture_census.py` clean at 39 seen-red gates (two new: `read-observer`,
`s25-commission-kind`).

**`bootstrap/templates/led.tmpl` — VERIFIED, not touched.** The generic path's INSERT has no
kind-specific gating; `commission` flows through it exactly as any other prose kind. Confirmed
by direct exercise on both a post-s25 and a pre-s25 schema (item 2 above), not asserted.

**Deferred, named, not silently dropped:** no new ASP/SQL derived view consumes `commission`
rows yet (e.g. "every `work_opened` traceable to its commission via `--refs`") — filed as a
possibility in `s25-commission-kind.sql`'s own header, not built or claimed built. LAZY mode's
full two-signal distinction (actor + live stamp) was only partially exercised in this pass's own
witness (a bare-shell probe cannot produce a real Claude-session stamp) — named honestly above,
not overclaimed; a real governed session will produce the complete signal the first time point
10 fires in anger.

Every claim above is WITNESSED with the artifact quoted, or explicitly named as a limited/partial
witness with the reason stated. No umbrella claims.

## Run-11 first-shift forensics (2026-07-11)

Read-only forensic pass over run11 (`/home/bork/w/vdc/1/run11`, ledger `run11`/`run11_kernel` on
`toy`@192.168.122.1) — the first run under the FULL current mechanism set (change_gate,
stamp_intercept, clean_exit all "enforce"; doc_shapes_gate "enforce" for the first time anywhere;
mutation_observer/delegation_observer/read_observer "observe"; demurral_detect/doc_legibility_critic
"off"). Session closed CLEAN, independently re-confirmed live during this pass (not just trusted
from the prompt): `./judge` → `AGREE asp=199 sql=199 atoms; Δasp=[] Δsql=[]`, `work_item_violations:
none`; `./distance-to-clean` → `TOTAL debt: 0`; `./audit` → `VERDICT: BATCHED_DECLARED`. Evidence:
97 ledger rows (ids 1–100, 3 burned: 62, 97, 98 — matches `./audit`'s own `REFUSAL FINGERPRINTS:
[62, 97, 98]`), `.claude/logs/invocations.jsonl` (246 rows, Bash-only), `read_observer.journal.jsonl`
(16 rows), `delegation_observer.journal.jsonl` (6 rows), `change_gate.journal.jsonl` (8 rows),
`stop_clean_exit.journal.jsonl` (1 row), the world's git repo (5 commits), and `run11/CLAUDE.md`'s
governance preamble. Classification rubric per "Maintainer priority ruling" above: (a) AGENT DEFECT,
(b) MECHANISM-REFUSES-WITHOUT-TEACHING, (c) LEGITIMATE-REQUIREMENT-BEING-FELT — only (b) produces
change proposals.

**1. SIGNED-COMMISSION INTAKE (first ever).** Row 1 (`kind=commission, actor=3/commissioner,
stamp_verified=f, ts=2026-07-11 20:37:40.23+02`) predates the Claude session's first invocation
(`18:43:01Z` = `20:43:01+02`, `invocations.jsonl` line 1) by ~5.3 minutes — the maintainer typed
`LED_ACTOR=commissioner ./led commission "<ask>"` in his own terminal before starting Claude Code
(FULL mode; `stamp_verified=f` is exactly the expected signature of a write that never passed
through Claude Code's own PreToolUse `stamp_intercept` hook, not a defect). The agent's FIRST
invocation of the whole session was `./led --recent 5` (`18:43:05Z`), confirming CLAUDE.md point
10's "check before writing your own" discipline; `grep -c "commission" invocations.jsonl` for any
agent-issued `./led commission` call returns zero matches for the whole 246-row log — the agent
never double-recorded the ask. Every decomposition row from 3 onward carries `--refs row:1`
(rows 3, 4, 5, 6, 26, 27, 37, 48, 49, 53, 54, 55, 59, 61, 87, 95, 96 all cite `row:1`, confirmed by
direct query). **No confusion is visible around the unstamped commissioner row** — but also no
explicit narration of *why* row 1 needed no vicarious re-transcription; the agent silently
complied with point 10 rather than stating "row 1 is already FULL-mode signed, skipping my own."
Benign, not a finding. **Classification: (c)**, textbook compliance.

**2. DOC GATE, ENFORCE MODE (first ever live-blocking deployment anywhere).** Wired
(`.claude/settings.json`, `Write|Edit` matcher → `pretooluse_doc_shapes_gate.py`,
`GATE_SUBJECT_ROOT=/home/bork/w/vdc/1/run11`), mode read live as `"enforce"` from
`.claude/apparatus.json`. `docs/qeubo-interface.md` was written/edited across 3 commits
(`6d9d450` 93 lines, `ef8ccad` +28, `ac22f7b` +3/-1) plus `webapp/README.md`, `.claude/APPARATUS.md`,
`.claude/GOVERNED_FILES.md`, `.claude/HOOKS.md`, `CLAUDE.md` — no `doc_shapes_gate.journal.jsonl`
file exists in `.claude/logs/` at all (by the gate's own documented convention, a clean pass is
never journaled — only DENY/OBSERVED-WOULD-DENY are). Re-running `gates/doc_shapes.check_file()`
directly against each of the three committed snapshots of `docs/qeubo-interface.md` (git-show'd
into scratch files, checked read-only from autoharn, never written back to run11) returns `CLEAN`
for all three — consistent with "the gate ran and found nothing," not merely "the gate never ran."
**No refusals, no retry cycles, no flailing.** **Classification: (c)** — the first live enforce-mode
deployment of ADR-0017's checks passed with zero friction on real, freshly-written prose.
**Epistemic limit, named plainly per the task's instruction:** the gate fail-opens silently on ANY
internal exception (its own documented posture — "a legibility check must never block a write"),
and a clean pass and a silently-broken gate are BYTE-IDENTICAL from world-side evidence alone (both
produce zero journal lines and zero visible refusals). This pass cannot distinguish "gate ran,
found nothing" from "gate always raised and always fail-opened" using only run11's own record — the
`check_file()` replay above raises confidence (the content really is clean by the same logic the
gate would apply) but does not prove the LIVE hook process executed without error on each call. No
dedicated unit/integration test for `pretooluse_doc_shapes_gate.py` was found in this repo.

**3. READ-OBSERVER (first ever, 16 read events).** All 16 events share ONE `session_id`
(`b188580a-2d70-4990-949c-49205c4ca8b3` — the run's sole top-level Claude Code session; every
`Agent`-dispatched reviewer subagent runs INSIDE that same session_id, same as run10's s21
finding). The mechanically-enforced independence signal for reviewer countersigns is real but
lives elsewhere: `run11.review_detail` shows all 49 reviews claim `independence=technical`, none
refused, because `kernel/lineage/s21-session-aware-distinctness.sql`'s `validate_independence()`
keys on the PAIR `(stamp_session, stamp_agent)`, not session alone — reviewer rows carry a
per-dispatch `stamp_agent` (e.g. `a8b1c1d45dee78cce` for the first dispatch, `a5c80ae88e23a75c9`
for a later one) distinct from the author's `stamp_agent='main'`, so technical independence holds
STRUCTURALLY (kernel-enforced) even though `read_observer` cannot see that distinction (its schema
carries only `ts, session_id, file_path` — no agent/actor/tool_use_id field). Time-correlation,
not structural proof, is what read_observer offers: the reviewer's 4th dispatch ("Final reviewer
pass over implementation rows", `delegation_observer` ts `19:19:21.326Z`) is followed within 8s by
Read events on exactly the four work items' shipped artifacts — `docs/qeubo-interface.md`
(19:19:29.174Z), `webapp/palette.js` (19:19:29.311Z), `webapp/qeubo-client.js` (19:19:35.539Z),
`webapp/README.md`/`index.html`/`compare.html` (19:21:21.1–1.8Z) — and `invocations.jsonl` in the
same window shows `git show --stat 6d9d450/ef8ccad/ec817aa` (19:19:28Z) alongside them. The review
rows citing these artifacts as "verified" land 1–2 minutes LATER (row 66, 19:22:33Z: *"verified
against git log: commit 6d9d450... exists and its diff includes docs/qeubo-interface.md (93
lines)"*; row 79, 19:23:20Z: *"verified: commit ec817aa... exists, diff adds webapp/index.html,
webapp/palette.js, webapp/README.md as described... webapp/README.md and index.html both
accurately describe the shipped renderer"*; row 82: *"Read compare.html and qeubo-client.js in
full: the auth flow, pair/preference/best wiring, and index.html hand-off link all match"*) — a
temporally coherent trace (dispatch → reads of the named artifacts → verification claims quoting
their content) that a lazy "verified" without reading would not produce this shape of specific,
content-accurate claims. **What the traces DO prove:** the exact files a review row claims to have
checked were in fact Read (by the Read tool, PreToolUse-observed) in the same session, in a tight
window immediately preceding the claim, and the claims' content-specificity (e.g. quoting
`compare.html`'s auth/hand-off wiring correctly) is consistent with an actual read having occurred.
**What they do NOT prove:** WHICH agent (main thread vs. the dispatched reviewer subagent)
performed a given read — `read_observer`'s schema has no field to attribute a read to a specific
dispatch, only to the shared session_id, so the correlation above is temporal/circumstantial, not
structural. Independence of the WRITE (kernel-enforced, `(stamp_session, stamp_agent)` pair) and
independence of the READ (unenforced, unattributed) are two different invariants — I6 read-trace
evidence answers "was something read before this was attested," not "did the SAME entity that
signs as reviewer do its own reading, independent of the author's."

**4. STOP GATE JOURNAL (first durable record; class-b fix from the run-10 audit confirmed live).**
`stop_clean_exit.journal.jsonl` carries exactly ONE line: `{"ts": "2026-07-11T19:29:58.648Z",
"outcome": "clean_allow"}`. This matches the run-10 audit's own change proposal ("journal every
`stop_clean_exit` outcome, not just observe-mode allows") — the `"clean_allow"` outcome kind did
not exist in run10's observe-mode-only journaling scheme, so its presence here is live evidence the
fix landed and fired correctly on its first exercise. The outcome matches the session's actual
ending: the last ledger act before stop is row 95 (`21:28:36.08+02` = `19:28:36Z`, decision,
*"stopping: commission fulfilled — all four decomposed work items shipped and committed..."*),
naming what stands (all four artifacts, live-verified) and what remains (*"nothing decomposed is
left unclaimed... a fresh session resuming this world would start from a clean slate"* — plus two
disclosed non-blocking residues: a hardcoded demo credential, and the QEUBO demo backend left
un-seeded between runs). CLAUDE.md point 8's "stopping is a ledgered act" is satisfied by row 95
precisely. Row 95 was itself countersigned (dispatch 6, `19:28:56.653Z`, landing as reviewer rows
99/100, `19:29:31–35Z`) BEFORE the Stop hook fired clean at `19:29:58.648Z` — the full sequence
(stop-disposition row → countersign dispatch → countersign lands → clean Stop) is intact and in
the right order.

**5. CLOSURE — sequence, shape, and composed-verb usage.** Reconstructed timeline: session start
`18:43:01Z`; four work items shipped by `19:18:36Z` (commits `6d9d450` 19:03:41Z, `ef8ccad`
19:08:16Z, `ec817aa` 19:14:15Z, `6d50e64` 19:18:36Z) — a **~35.6-minute build phase**; final
reviewer pass dispatched `19:19:21Z` catches a real citation defect (rows 70–72, *"Broken
antecedent citation: this row's own refs field is row:19 and its prose calls the first... but row
19 is..."*), fixed as commit `ac22f7b` (19:25:59Z) with corrected re-review (rows 88–94,
19:27:33–48Z), stopping disposition row 95 (19:28:36Z), final countersign (19:29:31–35Z), clean
Stop (19:29:58.648Z) — a **~11.4-minute closure tail**. Total session ≈46:57, 246 invocations.
Compared to run10 (build ~22 min, closure tail ~25 min, 190/299 invocations in the closure half, 47
review-gap polls, per `design/RETROSPECTIVE-RUN10.md`): run11's TOTAL wall-clock is comparable
(~47 min both), but the SPLIT inverted — more of the budget went to building (35.6 vs 22 min) and
much less to closure firefighting (11.4 vs 25 min, **less than half**). Disaggregated-view polling:
`review-gap` 20×, `question-status` 10×, `work violations` 4× (34 total) vs run10's 47
`review-gap`-alone polls — also roughly halved. **The composed `distance-to-clean` verb was NOT
invoked even once as a command** — it was `cat`'d for inspection (18:43:10Z) and `git add`'d
(19:03:37Z) but never executed; the agent used only the disaggregated `review-gap` /
`question-status` / `work violations` views throughout, confirming the "disaggregated-default is BY
DESIGN, usage is data not defect" framing — here the data says: even with a one-shot composed verb
available, an agent reaching for the individually-documented, individually-taught verbs it already
knows is the more natural path. Not a finding requiring a fix; worth noting for anyone tuning
`pickup`/`HOOKS.md` toward foregrounding the composed verb more, should the maintainer want that
usage pattern to shift.

**6. LATE ENTRIES — `--event-time` live for the first time, and it worked.** Two rows use s24's
declared-event-time mechanism: row 26 (`event_declared_ts=20:52:00+02`, written `20:55:07+02`,
*"LATE-DECLARED: this row is written after the dispatch actually happened (delegation-observer
hook caught the missing before-the-fact ledger row) — event-time above marks the actual dispatch
moment, not this write"*) and row 37 (same pattern, `event_declared_ts=20:56:00+02`, written
`20:58:39+02`). Both are DECLARED, not silent — this is `./audit`'s own
`honestly-declared-late row id(s): [26, 37]` line, independently reproduced live during this pass.
Mechanistically: `delegation_observer` (mode `"observe"`, never blocks) emitted its non-blocking
`additionalContext` warning ("dispatching a subagent is work: ledger it BEFORE doing them") when
the agent dispatched an `Agent` Task without a preceding ledger row (CLAUDE.md point 7) — TWICE —
and BOTH times the agent responded not by ignoring the warning but by writing a compliant
LATE-DECLARED row with the true dispatch time, exactly the discipline `design/LATE-ENTRY-AND-
INTAKE-SEMANTICS.md` was built to produce. This is a genuine, positive first-live-fire result for
two mechanisms at once: the s24 declared-event-time column (previously only scratch-witnessed,
BACKLOG "Late-entry discipline implemented") and observe-mode `delegation_observer`'s power to
shape conduct despite never blocking. `./audit`'s overall verdict — `BATCHED_DECLARED` — is
consistent with the ledger: no row narrates past conduct WITHOUT declaration (the run-10 row-1
pattern this mechanism exists to catch did not recur). No undeclared silence-table gaps: `./audit`'s
own SILENCE TABLE section is empty of entries beyond the two intake-shape bursts (both `--refs
row:1`-chained decomposition bursts preceding any tool activity, annotated `intake-shape (precedes
all tool activity)` exactly as the run-10 audit's Proposal 1 intended, and correctly NOT flagged as
undeclared since they are the intake decomposition itself, permitted batched-and-declared by
CLAUDE.md point 9).

**7. STRUGGLE INVENTORY — one item found beyond the six questions above, self-discovered while
reconciling `./audit`'s `REFUSAL FINGERPRINTS: [62, 97, 98]` against the session transcript.**
`led.tmpl` defines no `show` subcommand (`grep -n "show" bootstrap/templates/led.tmpl` returns only
comment/help-text hits, never a `case` arm) — `./led show <id>` (2 positional args, so it clears the
generic path's `$# -lt 2` usage guard) falls through to the generic `<kind> <statement...>` INSERT
path with `kind="show"`, which `ledger_kind_check`'s CHECK constraint refuses (confirmed live:
`SELECT pg_get_constraintdef(...)` on `run11.ledger` lists `assumption, decision, question,
verification, finding, snag, revision, note, review, work_opened, work_claimed, work_depends_on,
work_closed, commission` — no `show`), burning the attempted row's identity value (standard
Postgres sequence-non-transactionality). `invocations.jsonl` shows the agent reached for this
naturally-guessed verb (mirroring `git show`) twice: `./led show 19|20|27` (three chained calls,
`19:19:45Z`, immediately preceded by a `review-gap`/`--recent 30` orientation pass and followed at
`19:22:21–24Z` by the agent grepping `led.tmpl` itself for the REAL `review` syntax before its
first successful countersign at `19:22:33Z`, landing as row 63) and `./led show 47|48`
(`19:29:17Z`, mid-final-review, immediately preceding rows 99/100). Both windows land exactly one
burned id apiece in `62` and the pair `97, 98` respectively — the mapping between five individual
`show N` calls and three total burns does not fully arithmetically reconcile from Bash-level
evidence alone (`invocations.jsonl` logs command_head, not exit codes or stdout; **marked
UNDECIDABLE**: whether every `show` call reached the INSERT, or some failed earlier for an
unlogged reason, cannot be settled without either a transcript replay or a live reproduction this
pass declined to run against run11's own database to honor "write nothing there"). The run-10
fix (`_led_kind_refusal_teach`, landed and confirmed present in the CURRENTLY-EXECUTING
`led.tmpl` — `run11/led` is a thin `exec` wrapper to the live autoharn template, not a scaffold-time
frozen copy) DOES fire on this refusal and names the valid kind vocabulary — but both observed
invocations piped output through `2>&1 | head -30`/`head -5`, which may or may not have preserved
the teach-text lines depending on exact psql error line-count (not independently verified).
**Classification: (b), low-to-moderate severity.** Unlike run10's item-1 (an invented kind reached
via the WRITE path, refused and taught), `led show` is reached via what reads as a READ-shaped verb
(mirroring `--recent`/`current`, and the universal `git show`/`docker inspect` convention) but is
silently absorbed into the WRITE path instead of erroring "unknown command, see usage" — the
failure mode is a phantom ledger-sequence burn plus a possibly-clipped teach-text, not a clean
usage refusal. The mechanism partially teaches (once triggered, if not piped away) but nothing
teaches the agent that `show` was never a real verb in the first place; `led --help`'s own usage
block (which the agent DID consult minutes later, `19:19:54Z`/`19:20:15Z`) does not list `show`
either way it could have self-corrected from that alone had it read closely, but the fall-through
insert fires before any such check.

CHANGE PROPOSALS (class-b items only)

- **Item 7 fix — give `led show <id>` a real, read-only implementation (or refuse it cleanly).**
  Smallest sound fix: add a `show <id>` case to `led.tmpl`'s dispatch (alongside `--recent`/
  `current`) that runs a single read-only `SELECT * FROM ledger WHERE id = <id>` (matching the
  `\x` display `led --recent` already uses) — this is what an agent reaching for `led show N`
  evidently expects, and it is a natural, useful verb to actually have. If the maintainer prefers
  NOT to add the verb, the smaller alternative is to make the generic path's arg-count guard (or
  `resolve_actor`) reject when `$1` is not a recognized subcommand AND the write-path is about to
  attempt an insert with an unrecognized-looking kind heuristically shaped like a lookup — but this
  is more fragile than just implementing the read the agent visibly wants. Either shape is
  fail-safe and additive-only (adds a verb or tightens a usage message; loosens no refusal, changes
  no INSERT-path semantics for any currently-valid kind) — qualifies as a class-ratified fail-safe
  delta once scratch-witnessed.
- **Item 2 observation — give the doc-shapes gate a minimal "exercised" signal.** Not a defect (no
  friction was observed — this is a hardening proposal against the specific epistemic limit named
  in item 2 above). Smallest sound fix: on a clean pass in `enforce`/`observe` mode, increment a
  tiny per-session counter file (or emit one low-volume journal line per N clean passes, not per
  call) so a future forensic pass can distinguish "the gate ran zero times" / "ran and found
  nothing" / "silently fail-opened every time" without replaying `gates/doc_shapes.py` by hand
  against git history. Purely additive (a presence/count signal, never file content or violation
  detail); does not change the "clean pass is silent" design intent for the interesting-case
  journal, just adds a cheap liveness counter alongside it.

DISPOSITION — Every new mechanism's first live shift is accounted for with row ids / journal lines
/ quotes above, and the picture is a strong, evidence-backed "the arc paid off": the signed-
commission intake worked cleanly on its actual first live occurrence (FULL mode, no double-record,
no confusion); the first-ever enforce-mode doc gate produced zero friction on real freshly-authored
prose (though this pass is honest that "zero friction" and "silently broken" are indistinguishable
from world-side evidence alone — a small hardening proposal, not a defect, follows from that
limit); the read-observer's 16 events give real, if circumstantial, corroboration of reviewer
countersign behavior, while the kernel's OWN `(stamp_session, stamp_agent)` pair-keyed
`validate_independence()` is what actually makes technical independence structurally true here (49
reviews, 49 legitimate `technical` claims, zero refused) — a cleaner outcome than run10's rows
112/113, because every review this run genuinely came from a freshly-dispatched subagent, never a
subagent re-reviewing its own prior review; the stop-gate journal fix proposed by the run-10 audit
is confirmed landed and firing correctly on its very first exercise; closure, by the numbers, is
where the arc shows up most concretely — total session wall-clock held roughly flat versus run10
(~47 min both) but the SHAPE inverted, with the closure tail cut from ~25 minutes to ~11.4 (more
than 50% reduction) and disaggregated-view polling roughly halved (34 vs 47), even though this
run's build phase itself ran longer; late-entry declaration (s24, plus observe-mode
`delegation_observer`'s non-blocking nudge) fired live for the first time and worked exactly as
designed, twice, with zero undeclared-narration gaps for `./audit` to catch. The one real new
finding — `led show`'s silent fall-through into the write path, burning ledger ids on what reads
as an intuitive read-only verb — is class (b) and gets a proposed fix above; it is minor (never
blocked real work, self-recovered within seconds each time) but is exactly the kind of "mechanism
invites a mistake instead of teaching against one" gap the maintainer's rubric exists to catch and
fix regardless of severity. Net: five of six named mechanisms performed at or above the bar their
run-10-era design work aimed for on their actual first live exercise; the sixth (doc gate) cannot
be fully distinguished from silent failure by this evidence alone, which is itself the honest
finding, not a claim of success.

Every claim above is WITNESSED with the row id / journal line / quote / independently-reproduced
command output cited in place, or explicitly marked UNDECIDABLE with the concrete evidence gap
named (the `led show` burn-to-attempt arithmetic; the doc-gate exercised-vs-idle question). No
umbrella claims.

---

## RETROSPECTIVE-RUN11 — second iteration of the record-sufficiency experiment (2026-07-11)

Filed alongside the mechanism-forensics entry above; the two are complementary passes on the same
run11 world (this one is the six-questions-re-asked / process-lenses retrospective, that one the
per-mechanism first-shift forensics). Deliverable:
[design/RETROSPECTIVE-RUN11.md](design/RETROSPECTIVE-RUN11.md), attested through the ADR-0017
A:B:C fresh-context loop (round 1 DEFECT — one unglossed coinage "flat-20" — repaired, round 2
CLEAN; record in `attestations/doc-legibility-attestations.jsonl`).

Headline verdicts on run10's six could-not-answer questions, re-asked against run11's richer
record: Q1 (alternatives-considered) NOW ANSWERABLE — preamble point 11's convention was honored
across every load-bearing decision (rows 4/7/27/46/56) and even invoked under a live operator
directive (row 6), though no design defect occurred to test its oversight-vs-bad-bet
discriminator; Q3 (independent reviewer reads) PARTIALLY — the read-observer positively places the
implementation-review dispatch (rows 63–83) reading all shipped webapp files during its exclusive
window, but attribution rests on dispatch-window exclusivity, not a per-read stamp; Q4 (verbatim
commission) NOW ANSWERABLE — row 1 is the maintainer's FULL-signed ask, and diffing shipped
artifacts against it newly shows the agent tracing design choices to his stated motivation (the
low-contrast complaint), not just his nouns; Q6 (granularity vs mental model) NOW ANSWERABLE — the
four work items track the maintainer's own text structure, and run10-derived preamble point 1
visibly reshaped the grain from run10's over-carved ten; Q2 (deliberation/execution split) and Q5
(cost) STILL BLOCKED, unchanged — no turn-timing or token accounting was added, exactly the two
questions no new record-kind targeted. Flow headline: closure (~10 min) ran about half the build
(~19 min), inverting run10's closure-dominated tail. The one finding this iteration most wants
run12 to close is new and could-not-have-been-raised-before: with the product shipping clean,
the record can witness that review HAPPENED and READ the files but not that it REASONED HARD, so
review's load-bearingness turns UNDECIDABLE precisely in the run where review found no product
defect — an instrument for the DEPTH of an independent read, not only its occurrence, is the
named gap.

## Maintainer principle: the action stream is the evidentiary basis; session internals are diagnostics (2026-07-11)

Stated while clarifying the deliberation-vs-execution timing gap, near-verbatim: "the end
goal of the project should require no low-level access into ~/.claude just on principle
(it should be robust in working by what claude does); the fact that we use it is for
diagnostics/debugging."

Standing consequences: (1) every harness guarantee rests on the sanctioned hook surface —
the action stream — never on reading session transcripts or other ~/.claude internals;
transcript archaeology remains legitimate as diagnostics only, per-study, never
load-bearing. (2) The deliberation-vs-execution timing gap (retrospectives run-10/11) is
therefore split: the TIMING half is solvable inside the principle — journal a PostToolUse
completion timestamp beside the existing PreToolUse stamp; tool runtime and model
deliberation then separate arithmetically — queued into the small-follow-ups commission.
The TOKEN/COST half requires session internals and is by this principle permanently
diagnostic-grade: buildable as a local opt-in instrument at most, never part of the audit
trail, and the previously-pending "privacy call on committing aggregates" is DISSOLVED —
nothing load-bearing depends on it. (3) The retrospectives' could-not-answer lists are
re-scored accordingly: "cost efficiency" moves from awaiting-decision to
out-of-scope-by-principle.

## Follow-ups commission scope extended (maintainer, 2026-07-11): timing tail + token self-reports

Three additions to the queued small-follow-ups commission (behind the GPG merge), all
maintainer-directed the same evening and all inside the action-stream principle:
1. PostToolUse completion timestamps beside the existing PreToolUse stamps — the value is
   the non-null tail (builds, test suites, dispatches), per the maintainer's own reading
   that most calls are ~0s; nearly free since the hook surface exists.
2. The delegation observer gains a return leg (PostToolUse on Task) — dispatch-to-return
   duration per subagent, closing the reviewer-execution-window inference gap by
   measurement.
3. Token-usage self-reports, the maintainer's design near-verbatim: the orchestrating
   agent SEES usage numbers when a subagent returns, so the preamble exhorts ledgering
   them — "with no harness guarantee, just a 'hope it's being honest' sort of thing."
   Implemented as an explicitly-unverified self-report convention (the marking is the
   guarantee: same trust class as a LAZY commission — attributable claim, no witness);
   diagnostic-grade forever per the action-stream principle.
Previously queued in the same commission: the led show read verb (run-11 class-b), the
doc-gate liveness counter, the distance-to-clean preamble sentence.

## Omega work-status question CLOSED as a product: bootstrap/track-work.sh + design/WORK-STATUS-OFFERING.md (2026-07-11, Sonnet, commissioned build)

Delivers the commission that ends the 3x-litigated omega work-status question (see this
file's own "Omega work-tracking disposition (2026-07-11, night shift)" entry above for the
most recent prior pass): a new, project-agnostic scaffold entry point, `bootstrap/
track-work.sh`, that gives ANY directory a standing, unwired, Postgres-backed work tracker
in one command — applying the full current kernel lineage (identical chain to `new-project.sh
--new-world`, through s25) to a fresh schema pair, writing `deployment.json` + the five verb
shims (`led`/`pickup`/`distance-to-clean`/`judge`/`audit`), and registering the three standard
principals. Deliberately NOT `new-project.sh` (collision constraint honored: neither that file
nor any existing `bootstrap/templates/*.tmpl` was touched — this offering gets its own entry
point, only new template-adjacent files). NO hooks wired — a standing project is not a
governed world; hook wiring is named as a separate, deliberate act. Full design + the
omega-capability mapping table (the actual closure of the litigation): [design/
WORK-STATUS-OFFERING.md](design/WORK-STATUS-OFFERING.md).

**A hazard found and fixed in passing** (CLAUDE.md's hazard-flagging duty): the birth chain's
individual files are each idempotent, but re-applying the FULL high_watermark_1.sql -> ... ->
s25 sequence against a schema that already carries it is NOT safe — intermediate deltas grow a
view's column list monotonically, so an earlier file's own (shorter) view definition collides
with Postgres's "cannot drop columns from a view" rule under `CREATE OR REPLACE VIEW`. This is
a general property of the chain — `new-project.sh --new-world --force` against an
already-migrated schema would hit the identical failure — flagged here since fixing that file
is out of this session's scope (the collision constraint forbids editing it; the kernel SQL
itself is frozen, maintainer-ratified-spec-only). Fixed within `track-work.sh`'s own scope:
`--force` now skips the DDL re-apply entirely when the target kernel schema already exists,
touching only deployment.json/the verb shims/the principals — never re-running kernel DDL a
second time. Live proof both polarities: `seen-red/track-work/run_fixtures.py` (RED-USAGE,
GREEN-ADOPT + live `led work open/claim` + `pickup` IN-FLIGHT + `distance-to-clean` clean,
RED-EXISTING with ledger rows provably unchanged, GREEN-FORCE with the hazard closed), banked
`seen-red/track-work/red.txt`, registered in `gates/fixture_census.py` (40 seen-red gates,
clean). `gates/layout_census.py` extended with the six new root-level entries this
self-hosted deployment introduces (`deployment.json`, `led`, `judge`, `pickup`, `audit`,
`distance-to-clean`) plus one pre-existing, unrelated gap caught in passing: `attestations/`
(ADR-0017's own attestation ledger dir, landed 2026-07-11, never previously registered here).

**Consumer #1: autoharn deployed on itself.** `bootstrap/track-work.sh /home/bork/w/vdc/1/
autoharn --name autoharn --db toy --host 192.168.122.1` (schema `autoharn`, kern
`autoharn_kernel`, role `autoharn_rw`) — WITNESSED live, kernel applied clean, `deployment.json`
+ the five verb shims written at the repo root. Open work migrated from HANDOFF.md's "Open
work" section and this file's own queued-commission entries (the small-follow-ups commission,
the configuration commission, the maintainer decision queue, the run-11 watch duties) into 13
real `led work open` items: one genesis `decision` row (row 1) stating this store's charter —
BACKLOG.md is henceforth the findings JOURNAL, this store is the work TRACKER — plus one
`--refs row:1` `assumption` row citing every migrated slug's HANDOFF/BACKLOG provenance. 10
items open (6 maintainer decisions, the configuration commission, the audit-verb completions,
the small-follow-ups commission, this build itself — claimed); 3 closed on migration, each
correcting stale HANDOFF text rather than blindly carrying it forward: cost-timing-accounting
(dropped — DISSOLVED by the same-day "action stream is the evidentiary basis" ruling), run11-
watch-duties (superseded — run11 finished and was forensically audited after HANDOFF's text
was written), prudential-filed-candidates (deferred, per the prudential rule). WITNESSED:
`./led work violations` (0 rows), `./pickup` (IN-FLIGHT shows all 10 open items with full spec
text), `./distance-to-clean` (`TOTAL debt: 0`) — all run live against the real deployment, not
a scratch probe.

**HANDOFF.md's "Open work" section replaced** with a one-paragraph pointer at the tracker
(`./pickup` at the autoharn root), per the commission's instruction; the prior itemized list
(items 1-5, HANDOFF's own numbering) is retired there, superseded by the ledger's live state.

**ADR-0017 A:B:C loop, both edited/new maintainer-facing docs.** `design/
WORK-STATUS-OFFERING.md`: round 1 DEFECT (5 findings — an ungrounded code block, three
unglossed/unlinked artifacts, one non-stable-handle BACKLOG link), fixed; round 2 DEFECT (4
NEW findings — the `audit` verb never explained in-document, two near-duplicate section
headings causing a navigational ambiguity, two more unlinked artifacts), hit the two-round cap
per ADR-0017 (no third round) — **non-converging-review-loop escalation, adjudicated by the
orchestrator** (same disposition precedent as this file's "First live enforcement of ADR-0017's
loop" entry): all four round-2 findings fixed by applying B's own suggested repairs, no third B
round spawned. `HANDOFF.md` (opening + the edited "Open work" section, Rule 4 remit): round 1
DEFECT (7 findings — two unglossed opening terms, a verbless colon-list, two dangling named
commissions, a broken clause, an unlinked coined term), fixed; round 2 DEFECT (7 NEW findings —
"commission" itself ungrossed as a category, a self-admitted-unresolved "GPG merge" referent, a
still-unglossed `work_opened`, an ambiguous item-count reconciliation, a malformed clause, a
dangling fragment, one unlinked CLAUDE.md mention), hit the two-round cap, same escalation
disposition, all seven fixed verbatim from B's repairs. Both attestations recorded with
`escalated: true`, `rounds` carrying both real B verdicts as they happened (per
`gates/doc_attestation_presence.py`'s own honest-record design — a DEFECT-with-escalated-true
round is exactly as valid a record as a CLEAN one; the gate checks presence+shape, never the
verdict).

**The self-admitted-unresolved "GPG merge" referent turned out to be resolvable**, caught while
checking `git log`: `e9fe589` ("design: GPG trust layer spec...") names `design/
GPG-TRUST-LAYER.md`, whose implementation is visibly in progress in a concurrent worktree
(`.claude/worktrees/agent-a44608a4cd12fb911/`, untouched by this session per its own collision
constraint). Per ADR-0013 Rule 5 ("verify the artifact"), HANDOFF.md's text was corrected to
link the resolved referent rather than ship a known-fixable "cannot identify" claim — a small
follow-up edit, which the content-hash-keyed attestation gate correctly treated as a NEW
document state needing its own fresh read (not a continuation of the already-recorded,
already-escalated loop above). A fresh two-round mini-loop ran on that one edit alone: round 1
DEFECT (3 findings — two unlinked sibling paths, CONFIGURATION.md and BACKLOG.md, plus the
same item-count reconciliation ambiguity recurring in slightly different form after the edit
disturbed the surrounding prose), fixed by renumbering the enumeration explicitly (1)-(10)
with the 3 closed items stated as outside that count; round 2 CLEAN, all four Rule-1 clauses
enumerated, `escalated: false`. HANDOFF.md now carries TWO attestation records (the escalated
one for its first migrated state, the clean one for its current, GPG-referent-corrected state)
— both true, both kept, per the ledger's own append-only, latest-content-wins design.

`gates/doc_shapes.py` / `gates/doc_attestation_presence.py` gate mode: clean, 2/2
docs in scope (both design/WORK-STATUS-OFFERING.md and HANDOFF.md, checked against their
FINAL content). `gates/link_integrity.py`: clean (1220 unchecked-but-non-failing anchor notes,
0 broken paths).

Both B rounds for each document were genuinely fresh `Agent` dispatches (no shared context with
the authoring session or with each other) — the ADR's own "provably distinct from A" property
by construction, not merely asserted.

## A:B:C recipe friction, twice-witnessed: background-spawned B verdicts orphan (2026-07-11)

When a SUBAGENT runs the ADR-0017 loop and spawns its fresh-context B as a background
agent, B's completion routes to the main orchestrator session, not to the spawning
subagent — and B's attempt to SendMessage "general-purpose" fails (that is an agent type,
not an address). Witnessed twice tonight during the GPG implementation's doc loops; both
B's correctly fell back to reporting in their final output, and the orchestrator relayed
+ adjudicated. Fix for the recipe (design/ABC-AUDIT-LOOP-RECIPE.md, next natural touch,
attestation loop applies): B must be spawned SYNCHRONOUSLY by whoever runs the loop so
the verdict returns in-band as the Agent tool result; a background B is only sound when
the loop-runner is the main session. Queued into the tracker as part of the follow-ups
item rather than a new thread.
## GPG trust layer — all three rungs built and witnessed (Sonnet, 2026-07-11/12)

Implements `design/GPG-TRUST-LAYER.md` in full — signed ratification tags (Rung 1), SIGNED-mode
commissions (Rung 2), and the anchored ledger (Rung 3, kernel delta s26 + the signed head) —
commissioned per the standing delegation contract. Worked from the isolated worktree at
`.claude/worktrees/agent-a44608a4cd12fb911`, discovered 143 commits behind `next`'s live tip
partway through (the worktree branch carried zero unique commits, so `git reset --hard next`
was safe and used before any implementation work began — named here per the self-application
rule, an orchestrator-facing fact worth recording even though it cost no rework).

**Rung 1 — `attest-tags`** (repo root, autoharn-side, never scaffolded into a world — mirrors
the per-world verb naming without being one). Enumerates `ratified/*` git tags, verifies each
against `law/keys/*.asc` via a throwaway per-invocation GNUPGHOME (`filing/gpg_trust.py`, the
one shared home for this mechanic across all three rungs — ADR-0012 P1), and reports any commit
whose message claims ratification with no covering tag. **WITNESSED**, both polarities,
`seen-red/attest-tags/run_fixtures.py` (real GPG, a fresh Ed25519 test key generated per run, a
scratch git repo, zero residue after): GOOD (signed with a committed key), BAD-unsigned
(lightweight tag, git's own "cannot verify a non-tag object" detail), BAD-forged (signed by a
key deliberately never committed), and the uncovered-ratification-claim detector, all exit-coded
correctly. Run against this repository's OWN real history: zero `ratified/*` tags exist and
`law/keys/` is genuinely AWAITING-KEY, so it honestly reports every commit whose message says
"RATIFIED" as uncovered — an expected finding, not a defect, given no key has landed yet.

**Rung 2 — `verify-commission`** (`bootstrap/templates/verify-commission.tmpl`, wired into
`bootstrap/new-project.sh`'s shim loop, the `distance-to-clean` precedent for adding a verb
without touching a live-executed template). Implements `VERIFIED | UNSIGNED | FORGED-OR-CORRUPT`
(exit non-zero only on the third), recomputing a commission's digest from the ledger row's OWN
current bytes and checking any banked `.claude/commission-<id>.asc` against `law/keys/*.asc`.
**A real byte-fidelity hazard in the spec's own illustrative ceremony was found and fixed, not
merely flagged** (CLAUDE.md's engineering-responsibility corollary): `gpg --detach-sign --armor
~/aa` signs the raw file's trailing newline, but `$(cat ~/aa)` — what actually lands in the
ledger — strips it, so an honest, unaltered commission would verify as FORGED-OR-CORRUPT under
the spec's own example. Fixed by signing `printf '%s' "$STATEMENT"` instead (byte-identical to
what the ledger stores); the corrected ceremony ships in both `bootstrap/new-project.sh`'s
printed SIGNED-mode block and `design/GPG-TRUST-LAYER-FAQ.md` §5, with the hazard explained in
full in `verify-commission.tmpl`'s own module docstring. **WITNESSED**, all five outcomes,
`seen-red/verify-commission/run_fixtures.py` (a real throwaway `--new-world` scaffold, a real
FULL-mode commission via `led`, a fresh Ed25519 test key, zero residue): UNSIGNED (no `.asc`),
VERIFIED (byte-fidelity-fixed signature against a committed key), FORGED-OR-CORRUPT (signature
over different bytes), FORGED-OR-CORRUPT-via-no-committed-key (a deliberate judgment call,
explained in the module docstring: an unverifiable claim of a signature is loud, never folded
into the weaker UNSIGNED bucket), and the absent-`gpg`-binary typed refusal (exit 2, a FOURTH,
distinct outcome from the three verdicts). One preamble sentence added to
`bootstrap/templates/CLAUDE.md.tmpl` point 10: run `verify-commission` at intake, carry the
verdict into the decomposition's first row.

**Rung 3 — kernel delta s26 + `verify-chain`** (`kernel/lineage/s26-row-hash-chain.sql`,
`bootstrap/templates/verify-chain.tmpl`). Every ledger row gains a SHA-256 `row_hash` (hex text)
of a canonical, NULL-coalesced, TIMEZONE-SAFE (a hazard caught before it could bite — `ts::text`
renders in the connection's session timezone, so the canonicalization uses
`extract(epoch FROM ts)` instead, a numeric instant immune to TZ-rendering drift between the
insert-time connection and a later `verify-chain` connection) serialization of every OTHER
column, concatenated with the predecessor row's `row_hash` (or a per-world genesis seed,
`kernel.chain_genesis` — NOT a secret, contrast `stamp_secret`; its only job is making two
worlds' row-1 hashes differ). Computed by ONE shared SQL function, `compute_row_hash()`, called
identically by the insert trigger AND by `verify-chain`'s read-only walk — no second
re-derivation of "what a row means" to drift (ADR-0012 P1/P7). **A genuine concurrency race was
found and CLOSED, not merely named**: `bigserial` allocates `NEW.id` before a `BEFORE INSERT`
trigger runs, so two truly concurrent inserts could interleave their predecessor-hash reads and
fork the chain; closed with `pg_advisory_xact_lock(hashtext(TG_TABLE_SCHEMA ||
'.row_hash_chain')::bigint)` at the top of the trigger — schema-scoped, so concurrent writers in
DIFFERENT worlds never contend, and negligible cost given the ledger's already-low-concurrency
"one row at a time" operating mode. Postgres 18.4's BUILT-IN `sha256()` (core, PG11+, verified
live against this toy db before assuming) is used, not `pgcrypto`'s `digest()` — one fewer
extension dependency where the built-in is strictly sufficient. Class-ratified (strictly
additive: one column, one genesis table, one function, one trigger that fires LAST — by
alphabetical trigger-name ordering, `zz_set_row_hash`, a mechanism not a convention — and writes
only the new column) and entered `bootstrap/new-project.sh`'s `LINEAGE_CHAIN`, with automatic
genesis-seed provisioning added right alongside the existing stamp-secret seeding block.
**WITNESSED, both polarities plus the differential**, `seen-red/s26-row-hash-chain/
run_fixtures.py` (a real throwaway `--new-world` scaffold, zero residue): an INSERT before the
genesis seed exists is refused loudly; three real `led`-written rows build a chain
`verify-chain` reports INTACT; `--head` emits exactly `{world, max_id, head_hash, utc}` and
NOTHING else on stdout; a historical row's content surgically altered (trigger disabled, then
re-enabled — a real schema-owner-level tamper, on a scratch schema) while its own `row_hash` is
left stale BREAKS THE CHAIN AT THE ALTERED ROW, the spec's own words, verified literally; the
more sophisticated variant — the tamperer ALSO rewrites that row's own hash to match its new
content — moves the detected break to the immediately NEXT row instead (never later, proven both
ways); `--head` against a broken chain REFUSES with empty stdout, exit 1 (never signs a head it
has not verified); the EXISTING SQL/ASP marriage differential (`engine/ledger_differential.py`)
still verdicts AGREE on an s26 world, proving the delta does not perturb existing T_now facts
(`[OK ] s26fxprobe AGREE asp=4 sql=4 atoms; Δasp=[] Δsql=[]`).

**The signed-head ceremony and key rotation were both exercised end to end on the throwaway test
key**, live, not just in the scratch-schema fixtures: a real `--new-world` scaffold's
`verify-chain --head` output was piped to `gpg --detach-sign --armor`, banked as
`.claude/head.json` + `.claude/head.json.asc`, and `gpg --verify` reported `Good signature`.
Rotation (revoke → generate → commit → re-sign) was exercised on the same key: applying the
auto-generated revocation certificate (note for future exercisers: it ships with a colon before
`-----BEGIN` deliberately, to prevent accidental import — strip it first) made the OLD key
IMMEDIATELY UNUSABLE for new signing (`gpg: skipped "...": Unusable secret key` — stronger than
a mere warning, a genuine finding of this pass, not assumed in advance); a freshly generated
replacement key then signed and verified cleanly, including re-signing a chain-head-shaped
document. Full transcripts of both ceremonies are quoted in `design/GPG-TRUST-LAYER-FAQ.md` §§6
and 8.

**Docs.** `design/GPG-TRUST-LAYER-FAQ.md` (new, the operator FAQ: key generation, hardware-token
recommendation, revocation, all three ceremonies, rotation — all witnessed, none aspirational).
`law/keys/README.md` (new, the AWAITING-KEY stub — explains what belongs in the directory,
explicitly does NOT fabricate a maintainer key). `CAPABILITIES.md` items 28/29/30. Both new docs
plus the CAPABILITIES.md addition ran the ADR-0017 A:B:C fresh-context loop (a genuinely separate
`Agent` dispatch as B, briefed with ADR-0017's full text and nothing else — see the loop's own
recipe, `design/ABC-AUDIT-LOOP-RECIPE.md`): round 1 found 4 findings in the FAQ (two lead
fragments matching the ADR's own named specimen shape; "detached signature" and `GNUPGHOME` used
ungrossed against a stated first-time-GPG-user audience), 1 in `law/keys/README.md` (FULL/LAZY
cited with no definition or link), and 4 in the CAPABILITIES excerpt ("Rung" undefined; "the
third signing strength" naming an unlinked ladder; an arrow-chain list violating Rule 1a's own
named anti-pattern; a missing relative pronoun producing a garden-path sentence) — all repaired.
Round 2: the FAQ and CAPABILITIES verdicted CLEAN (all four Rule-1 clauses enumerated);
`law/keys/README.md` hit ONE surviving finding — introduced by the round-1 repair itself, a
compound sentence dropped mid-predicate across three em-dashes — at the two-round cap. Per
ADR-0017 this routed as a non-converging-review-loop; the orchestrator (the escalation
recipient) adjudicated by applying B's own suggested mechanical sentence-split verbatim.
This FIRST loop's attestations recorded FAQ/CAPABILITIES `escalated: false`,
`law/keys/README.md` `escalated: true` with the orchestrator's adjudication noted — but all
three documents were edited AGAIN immediately after, to reflect the hack-rationalization fixes
below (a new exit code and verdict-label scheme), which invalidated those attestations against
the new content (the gate keys on exact content hash; a superseded version's attestation is
just history, never a pass for new bytes). A SECOND A:B:C loop ran against the post-fix content:
round 1 found 2 more findings in the FAQ (`./led` and "commission" used undefined/unlinked in
§5) — repaired; round 2 found 3 more findings across all three documents (the ADR-0012 P1
expansion applied to only one of its two occurrences; a repair-introduced "absent stamp" phrase
left unglossed in the FAQ; `law/keys/README.md` overgeneralizing a verdict label — `UNVERIFIABLE`
— across three tools that do not all actually emit it) — again at the two-round cap, again a
non-converging-review-loop, again adjudicated by the orchestrator applying B's own suggested
repairs verbatim. FINAL recorded state in `attestations/doc-legibility-attestations.jsonl`
(matching the actual committed bytes): all three documents `escalated: true`, each `b_id` noting
the second loop and the orchestrator's adjudication. Two escalations on one small documentation
set, both from the SAME root cause — fixing a real code defect (the hack-rationalization audit's
findings) forced a second documentation pass, and that pass itself needed the loop's full two
rounds — recorded honestly rather than smoothed into a single clean pass that did not happen.

**Out-of-frame hack-rationalization audit, before reporting this commission done (CLAUDE.md's
own standing rubric — run EVEN THOUGH every seen-red fixture was already green).** A fresh,
independent subagent (no memory of this session, briefed to treat the implementer's own
reasoning as suspect, per the skill's own anti-self-audit rule) reviewed five judgment calls.
Verdict: 2 of 5 `UNDISCHARGED-HACK`, 1 `narrower-but-justified`, 2 `general`. Both hacks were
FIXED before this commission closed, not merely noted:

1. **`verify-commission`'s `FORGED-OR-CORRUPT` overload (fixed).** An earlier version folded "a
   `.asc` is banked but `law/keys/` carries zero committed keys" into `FORGED-OR-CORRUPT`,
   reasoning the spec's vocabulary was "closed to three members" — a reason the SAME file's own
   missing-`gpg` handling already contradicted (it already used a distinct exit code for an
   analogous precondition), and the wrong structural choice relative to the very `attest-tags`
   precedent it cited (which uses a DISTINCT `UNVERIFIABLE` label, never a relabeled `BAD`).
   Fixed: a new, distinct outcome, `NO-COMMITTED-KEY` (exit 3), separate from all three verdicts
   — a fresh, keyless repository's commissions (this repository's own real state today) are no
   longer indistinguishable, by verdict string alone, from an actual forgery. Every doc, the
   scaffold's printed ceremony, and the seen-red fixture updated to match; re-witnessed green.
2. **`compute_row_hash()`'s NULL-vs-empty-string collision (fixed, the more serious finding).**
   The audit constructed a concrete counter-example: `coalesce(rationale, '')` mapped BOTH
   `rationale IS NULL` and `rationale = ''` — different, SQL-observable facts — to the identical
   serialized token, a genuine hash COLLISION (not merely "an adversary who already has stronger
   attacks", the framing an earlier version of this file used to wave it off). A schema-owner
   tamper exploiting this would produce ZERO change to the stored hash anywhere in the chain —
   defeating not just the chain walk but the §4 SIGNED HEAD backstop the spec names as the actual
   closing move, for free. Fixed by replacing the delimiter-join with a length-prefixed,
   presence-tagged encoding (`hashfield()`, `kernel/lineage/s26-row-hash-chain.sql`) — a standard
   self-delimiting code, injective by construction. Re-witnessed on a fresh scratch schema
   (`s26val2`) via direct SQL recomputation before touching the automated suite, then added as
   its own seen-red case (`h-null-vs-empty-string-collision-closed`,
   `seen-red/s26-row-hash-chain/run_fixtures.py`) proving the specific collision the audit found
   is now detected; full suite re-run green, zero residue.
   Both fixes are also documented as REVISION NOTEs in the affected source files themselves
   (`verify-commission.tmpl`, `s26-row-hash-chain.sql`'s own header), not just here — a future
   reader opening the code directly sees the same account.

The audit's smaller, undischarged residual findings (not fixed, named honestly): (a) the spec
document `design/GPG-TRUST-LAYER.md` §3 itself still shows the original, byte-fidelity-buggy
signing example verbatim, with no errata pointer to the FAQ's correction — left untouched
deliberately, since the document is concurrently in its own ADR-0017 attestation loop and its
technical content is ratified; the correction is instead prominent everywhere a reader is likely
to actually land (FAQ, CAPABILITIES, BACKLOG, the two affected scripts' own docstrings). (b) the
SIGNED-mode ceremony's Step 1 (typing the ask inline for FULL mode) and Step 2 (re-reading a file
for the signature) were two independent renderings of "the same" text — fixed in both
`bootstrap/new-project.sh`'s printed ceremony and the FAQ: Step 1 now reads the ask from the SAME
file into `$STATEMENT` first, used for both the `led commission` call and the signature, closing
the adjacent hazard the audit named. (c) the advisory-lock fix's correctness is stated
unconditionally in the SQL comment where it is actually conditional on READ COMMITTED isolation
(true of every writer in this codebase today, named but not enforced) — filed as a residual note,
not fixed, since no current writer uses a stronger isolation level. (d) the `zz_` trigger-naming
convention that guarantees firing order has no enforcement mechanism for a FUTURE ninth trigger —
inherent to how PostgreSQL's own same-timing-trigger ordering works, filed as a note for whoever
adds trigger #9, not a defect this delta could close differently.

**Not done, named**: `kernel/lineage/README.md` was NOT updated to document s20 through s26 in
its own apply-order prose — it was already stale before this pass (it stops narrating at s19),
so this is a PRE-EXISTING gap this pass did not create, not one it is filing new; named here
because CLAUDE.md's hazard-flagging duty applies to gaps met in passing even when out of the
immediate mandate's scope, and a full README refresh across seven un-narrated deltas is a
separate, larger piece of work than this commission's remit. A real maintainer keypair
(`law/keys/maintainer.asc`) does not exist — every ceremony above is witnessed on a THROWAWAY
test key, clearly marked as such throughout; nothing here fabricates or assumes a real key.

## Small-follow-ups commission: seven items shipped (Sonnet, 2026-07-12)

Executes the `small-follow-ups-commission` work-tracker item (`./led work` slug, this repo's
own self-hosted tracker per BACKLOG "autoharn deployed on itself"), whose seven items were
specced across "Run-11 first-shift forensics", "Maintainer principle: the action stream is the
evidentiary basis; session internals are diagnostics", "Follow-ups commission scope extended",
and "A:B:C recipe friction, twice-witnessed" (all above, 2026-07-11). Liveness checked before
every hooks/ and bootstrap/templates/ edit (`pgrep -a claude` + `readlink /proc/<pid>/cwd`
against every candidate PID) — no cwd ever resolved under `/home/bork/w/vdc/1/run*` across the
session, so no template/hook edit was frozen.

**1. `led show <id>`** (`bootstrap/templates/led.tmpl`) — a real, read-only subcommand: one
ledger row, every column, in full (`psql -x`), refusing loudly with teach-text on a missing id
instead of the prior silent fall-through into the generic write path (kind="show", refused by
`ledger_kind_check`, burning a sequence id every time — the run-11 class-b finding). The gotcha
this codebase already names for itself (`led work asof`'s own comment) bit here too and was
caught before shipping: `psql -c "... :id ..."` does NOT interpolate bind variables — only a
script fed via heredoc/stdin does — so the `-x` display query is a heredoc, matching every other
bound query in this file. *Witnessed*, both polarities, extending
`seen-red/contemporaneity-audit/run_fixtures.py` with cases n (show success, full statement
printed, id column matches) and o (missing id: REFUSED, no `ledger_kind_check` fall-through
text, and the ledger id sequence's own `last_value` PROVABLY unchanged across the refused
attempt — the phantom-burn class itself foreclosed, not merely the visible symptom).

**2. Doc-shapes gate exercised-liveness counter** (`hooks/pretooluse_doc_shapes_gate.py`) — a
second, separate journal (`doc_shapes_gate.exercised.jsonl`, distinct from the existing
DENY-only journal) gets one line per COMPLETED evaluation — clean, denied, or
observed-would-deny alike — written only after the check runs to completion, never from the
fail-open except branch. A gap between a world's `.md` Write/Edit count and its exercised-line
count is therefore the run-11-named epistemic limit's own detector: "a clean pass and a
silently-broken gate are byte-identical from the DENY-only journal alone" no longer holds once
this second journal exists. Observer-grade, no verdict change. *Witnessed*, both polarities,
extending `seen-red/doc-shapes-gate-world/run_fixtures.py` with an EXERCISED-LIVENESS case: five
real evaluations (enforce-deny, enforce-clean, observe-warn, default-observe-warn,
edit-reconstruct-deny) produce five lines in order; the sixth call (mode="off", which returns
before the check ever runs) produces none.

**3. `distance-to-clean` preamble sentence** (`bootstrap/templates/CLAUDE.md.tmpl` point 5) —
one added sentence naming `./distance-to-clean` as available for a one-command closure check;
the three disaggregated views (`review-gap`/`question-status`/`work violations`) remain the
sentence's own stated default, per the maintainer's standing condition. `.tmpl` files are not
`.md` files (`gates/doc_attestation_presence.py` globs `*.md` only), so this edit and item 6's
below carry no ADR-0017 attestation obligation.

**4. PostToolUse Bash completion timestamps** (`hooks/posttooluse_bash_completion.py`, new hook)
— a sibling journal, `bash_completions.jsonl`, banks each Bash call's completion time (UTC-Z)
beside `hooks/stamp_intercept.py`'s existing PreToolUse dispatch token. Deliberately a SIBLING
file, not a new line shape inside `invocations.jsonl` itself: `engine/contemp_edb.py`'s own
`export()` reads every line there as an unconditional `token`+`wall_clock` dispatch record, so
injecting a differently-shaped completion line would either inflate its `skipped_lines` count or
risk a wrong-shape misread — the existing contemporaneity EDB stays byte-untouched (ADR-0004).
Pairing is the maintainer's own named design, "invocation token if recoverable, else
ts-pairing": a FIFO match against unpaired `invocations.jsonl` dispatch records sharing the same
`command_sha256`, yielding `pairing: "token"` plus `dispatch_wall_clock`, or the honest
`pairing: "ts-only"` fallback when no dispatch record matches — a named residual gap (two truly
concurrent Bash calls with byte-identical command text can pair to the wrong dispatch),
disclosed rather than silently risked. Wired into `bootstrap/templates/settings.json.tmpl`'s
PostToolUse `Bash` matcher, alongside the existing `mutation_observer` entry. *Witnessed*, both
polarities plus the FIFO-double-dispatch case, new `seen-red/bash-completion/run_fixtures.py`
(pure filesystem, no DB), registered in `gates/fixture_census.py`.

**5. Delegation observer return leg** (`hooks/pretooluse_delegation_observer.py`, extended) —
this file now attaches at BOTH `PreToolUse` (the original dispatch leg, byte-unchanged) and
`PostToolUse` on `Task|Agent`, mirroring `hooks/posttooluse_mutation_observer.py`'s own
established one-file-two-legs shape (and that file's own basename precedent: staying
"pretooluse_..." even though it now also handles PostToolUse, matching the sibling's
"posttooluse_..." staying that even though it handles a PreToolUse leg too). The return leg
journals a strictly additive `kind: "return"` line into the SAME journal, FIFO-paired against
its own dispatch line by `session_id` + `prompt` sha256 (recomputed from the PostToolUse
payload's own `tool_input.prompt`) — carrying `dispatch_ts`/`duration_ms` on a match, honestly
`pairing: "unresolved"` on none. Closes the reviewer-execution-window inference gap
RETROSPECTIVE-RUN11 named as still blocked ("the record can witness that review HAPPENED and
READ the files but not that it REASONED HARD"). Wired into `bootstrap/templates/
settings.json.tmpl`'s new PostToolUse `Task|Agent` matcher entry (same edit as item 4's Bash
wiring). *Witnessed*, both polarities plus the FIFO-double-dispatch case, extending
`seen-red/delegation-observer/run_fixtures.py`'s existing stateful sequence with three new
return-leg cases (g/h/i), the pre-existing dispatch-leg cases (a-f) unbroken.

**6. Token self-report convention** (`bootstrap/templates/CLAUDE.md.tmpl`, new preamble point
12) — the maintainer's own design, near-verbatim: when a dispatched subagent returns, the
orchestrating agent SEES its reported token/usage numbers in the tool result; if ledgered at
all, the statement carries an explicit "(self-reported by the subagent; no harness guarantee)"
marker, the same trust class as point 10's LAZY-mode commission transcription. Convention only —
no kernel column, no gate; diagnostic-grade forever per BACKLOG "Maintainer principle: the
action stream is the evidentiary basis; session internals are diagnostics".

**7. ABC recipe amendment: B spawned synchronously, always** (`design/ABC-AUDIT-LOOP-RECIPE.md`
step 2) — a hard requirement, not a preference, added with the exact failure mechanism named:
a background-spawned B's completion routes to the ORCHESTRATOR session, not to whichever
subagent spawned it, so a loop run *inside* a dispatched subagent (a common shape) never
receives its own B's verdict when B runs in the background — the two live instances BACKLOG
"A:B:C recipe friction, twice-witnessed" already banked. Fix: `run_in_background: false` on
every B dispatch, always, regardless of which session runs the loop. This edit is in-scope
`.md`, so it ran its own A:B:C loop, with a synchronous B throughout (dogfooding the very fix
being made): round 1 (fresh Agent, briefed by a hand-excerpted copy of ADR-0017 pasted inline)
returned two findings later found to be ARTIFACTS of that excerpt's own incompleteness (it
trimmed exactly the clauses the findings cited) — discarded, and a corrected protocol adopted:
round 1 proper re-ran with B instructed to Read the two real files directly rather than trust a
pasted excerpt, returning 4 genuine referent-resolution findings (BACKLOG unlinked/
inconsistently named, `apparatus.json` undefined, two gates unlinked, `judgment/**` unglossed),
all fixed; round 2 (the cap) found one further genuine ambiguity (a dangling "its own module
docstring" pronoun between two just-named files), fixed by the orchestrator directly per
ADR-0017's non-converging-review-loop disposition (no third B round) — `escalated: true`
recorded, both real rounds' findings preserved verbatim in
`attestations/doc-legibility-attestations.jsonl`.

**CAPABILITIES.md item 31** bundles items 1/2/4/5's built mechanisms into one minimal entry
(items 3/6 are convention-only preamble sentences in a non-`.md` template, noted in the entry's
closing paragraph rather than each earning their own item). Ran its own two-round A:B:C loop
(synchronous B throughout, scoped explicitly to item 31 alone — the rest of the 30-item, ~850-line
document is out of that pass's remit): round 1 found 9 findings (unresolved run-11/gate/commission
referents, and four noun-phrase-fragment sentences the entry's own new prose introduced — B noted
this fragment shape recurs throughout items 1-30 too, flagged as pre-existing and out of this
pass's scope, not fixed here), all fixed; round 2 found 2 further small referent gaps (an
unglossed `HANDOFF.md`, an unexplained quoted docstring-section name), fixed by the orchestrator
directly at the two-round cap, `escalated: true` recorded alongside item 7's above in the same
attestations ledger append.

**Not done, named**: `OPERATING-CARD.md`'s hooks × kernel map table was NOT updated with the two
new mechanisms (`bash_completion`; the delegation observer's new PostToolUse leg) — a real,
named gap (the map is now one row short of the live wiring) filed here rather than silently
left, deferred because each additional `.md` touch under ADR-0017 costs its own full A:B:C loop
(2-3x token cost per the ADR's own disclosed price) and this commission's seven items were
already sized without it. `kernel/lineage/README.md`'s stale apply-order prose (noted un-fixed
in the entry immediately above this one) remains untouched, unrelated to this pass.

Tracker item closed: `./led work close small-follow-ups-commission shipped --witness
"ea55214..937cfa7"` (six commits: `ea55214` item 1, `c8dc2ea` item 2, `1e8a3f8` items 3+6,
`1e51181` item 4, `3c3b6f9` item 5, `937cfa7` item 7 + CAPABILITIES item 31).
## Key-residence refactor: `law/keys/` scoped to autoharn's own law; every deployment gets its own `keys/` (Sonnet, 2026-07-11/12)

Refines the GPG trust layer's key residence per the maintainer finding recorded above (`led`
row 28, "Key-residence conflation... THIS repository should not have anything to do with end
user's keys"): the FAQ had directed every end user to commit their signing key to autoharn's
own `law/keys/`, conflating autoharn's own law-signing domain (Rung 1, `ratified/*` tags) with
every downstream deployment's commission-signing domain (Rung 2/3). Worked from the isolated
worktree at `.claude/worktrees/agent-a75f5048475925f82`; discovered, same as the prior GPG
commission, that the worktree branch was 154 commits behind `next`'s live tip with zero unique
commits of its own — `git merge --ff-only next` was safe and used before any edit began (named
per the self-application rule; a clean fast-forward, not a `reset --hard`, since the worktree
had no divergent history to discard).

**New layout, in two sentences.** `law/keys/` remains, but is now scoped EXPLICITLY to
autoharn's own law-signing — `./attest-tags` is the only verb that reads it, and nothing else
does. Every scaffolded deployment (a world via `bootstrap/new-project.sh --new-world`, or a
standing project via `bootstrap/track-work.sh`) now carries its OWN `keys/` directory next to
its `deployment.json`, and `verify-commission` resolves ONLY that directory — never autoharn's
`law/keys/` — with the `NO-COMMITTED-KEY` refusal's teach-text naming the deployment-local path.

**Per-file changes.**
- `design/GPG-TRUST-LAYER.md` §7 — the key-residence sentence refined to name the two domains
  explicitly; the spec's technical content (keygen, hardware token, revocation cert, rotation)
  otherwise stands, per the commission's own scope.
- `design/GPG-TRUST-LAYER-FAQ.md` — §3 split into 3a (autoharn's own law) / 3b (every
  deployment), each with its own commit ceremony; a new fingerprint-vs-public-key-vs-revocation-
  certificate passage appended to §1 (the maintainer's own live confusion, named as FAQ-worthy
  in the commission); §5's closing NO-COMMITTED-KEY paragraph, §6 (a clarifying note that the
  signed-head ceremony reads no committed-keys directory at all), §7 (throwaway-key export
  guidance corrected — `verify-commission` has no `AUTOHARN`/`--keys-dir` override for keys any
  more), §8 Step 3, §9's trust-boundary bullet, and Related all updated to match.
- `law/keys/README.md` — rewritten to state the autoharn-only scope plainly, with an explicit
  "this directory has nothing to do with any deployment's own signing" section and a pointer to
  the FAQ's two-domain split; the old "what tools do" section's `verify-commission`/`verify-chain`
  entries removed since neither reads this directory (verify-chain never did — see below).
- `bootstrap/templates/keys-README.md.tmpl` (NEW) — the deployment-local `keys/README.md` stub
  every scaffold writes, AWAITING-KEY state stated honestly, sedsubst-driven (`__PROJECT_NAME__`,
  `__CREATED_AT__`).
- `bootstrap/track-work.sh` — now creates `<project-dir>/keys/` + writes the stub from the new
  template, and extends its verb-shim loop from five verbs to seven (`verify-commission`,
  `verify-chain` added — `verify-chain` degrades honestly to `UNAVAILABLE` on a standing
  deployment's pre-s26 kernel, no s26 apply added here, out of this commission's scope).
- `bootstrap/templates/verify-commission.tmpl` — `keys_dir` changed from `AUTOHARN / "law" /
  "keys"` to `world_root / "keys"` (the same residence `.claude/commission-<id>.asc` already
  uses); module docstring, `NoCommittedKey`, and `verify()`'s own comments updated to match, with
  a REVISION NOTE naming the finding and the fix.
- `filing/gpg_trust.py` — module docstring corrected: `verify-chain.tmpl` was claimed as a third
  caller of the shared scratch-keyring mechanism, but it has never actually imported this module
  (grep-verified) — a pre-existing doc inaccuracy, flagged and fixed in passing per CLAUDE.md's
  engineering-responsibility corollary, not a code change (there was nothing to relocate).
- `CAPABILITIES.md` items 29/30 — item 29 records the key-residence revision and the frozen
  `new-project.sh` remainder; item 30 adds a note correcting the same `gpg_trust.py` inaccuracy
  for `verify-chain` (it reads no committed-keys directory in either domain — its signed-head
  ceremony is a direct `gpg --verify` against the operator's own ambient keyring).

**Frozen, and why.** `bootstrap/new-project.sh` was left untouched: `pgrep -a claude` at commission
start showed multiple live sessions with cwd `/home/bork/w/vdc/1/autoharn` (the shared checkout,
not this worktree), so per the commission's own liveness rule this script was read-only this
pass. The mechanism does not depend on the change (`gpg_trust.committed_keys()` already degrades
an absent `keys/` directory to "zero committed keys," identical in effect to an empty one — the
`NO-COMMITTED-KEY` refusal fires correctly on a world scaffolded by today's unmodified
`new-project.sh`, witnessed live in the re-run fixture below); only the friendly `keys/README.md`
stub is missing until this diff lands. The exact pending diff, to apply once no live session
is running there:
1. In the `--new-world` branch's `sedsubst` table (already carries `__PROJECT_NAME__`/
   `__CREATED_AT__`), add, right after the `.claude/` wiring block and before the seven-verb
   shim loop: `mkdir -p "$PROJECT_ROOT/keys"` then
   `sedsubst < "$TEMPLATES/keys-README.md.tmpl" > "$PROJECT_ROOT/keys/README.md"` (mirrors
   `track-work.sh`'s own new block verbatim — same template, same two lines).
2. In the closing `--new-world` echo block's SIGNED-mode paragraph, replace
   `"a real key is committed at law/keys/maintainer.asc"` (line ~394) and the two adjacent lines
   with the deployment-local path (`$PROJECT_ROOT/keys/`), matching the FAQ §3b wording.
3. No other line in `new-project.sh` names `law/keys` in a way that needs to change (the seven-
   verb shim loop and `verify-commission`/`verify-chain` shim wiring are already residence-
   agnostic — they just `exec` the templates, which now resolve `keys/` themselves).

**WITNESSED.** `seen-red/verify-commission/run_fixtures.py` rewritten to vary
`world_dir/keys/` (writing the test key in for VERIFIED/FORGED-OR-CORRUPT, temporarily moving
it out — never deleting — for NO-COMMITTED-KEY) instead of an `AUTOHARN` override; re-run clean,
all five cases, zero residue (schema/role check after teardown: empty). Quoted output, the
NO-COMMITTED-KEY case (the one the commission called out by name):
```
=== d-no-committed-key-distinct-refusal ===
  [ok] exit=3 refusal=NO-COMMITTED-KEY
```
and the full run: `a-unsigned` exit=0 UNSIGNED; `b-verified` exit=0 VERIFIED; `c-forged-tampered-
bytes` exit=1 FORGED-OR-CORRUPT; `d-no-committed-key-distinct-refusal` exit=3 NO-COMMITTED-KEY;
`e-gpg-absent-typed-refusal` exit=2 GPG-UNAVAILABLE. `seen-red/attest-tags/run_fixtures.py` and
`seen-red/s26-row-hash-chain/run_fixtures.py` re-run UNMODIFIED as regression confirmation (both
unaffected by this refactor — attest-tags stays on autoharn's own domain by design;
`verify-chain.tmpl` never read a committed-keys directory at all, confirmed by grep before
touching anything): both green, zero residue. Gates re-run clean: `gates/no_lazy_imports.py`
(exit 0), `gates/fixture_census.py` (43 seen-red dirs, clean — no new dirs added, so no registry
change needed), `gates/link_integrity.py` and `gates/doc_shapes.py` against every edited `.md`
(clean, 0 findings).

**BOUNDARY-HYGIENE CLASS, second instance.** Filed per the finding's own framing: upstream/
downstream trust-domain conflation — a mechanism built for THIS repository's own governance
(autoharn's law-signing) documented as if every consumer of the mechanism (a scaffolded
deployment) should reach back INTO this repository rather than owning its own instance. First
instance was the baked install path (an earlier finding, same class, different mechanism); this
is the second. Same acceptance test both times: "usable as a library" — would an end user
standing up a deployment ever need write access to, or knowledge of, autoharn's own repository
internals? Here the answer was accidentally yes (commit your key to `law/keys/`) until this
pass; the fix is the general shape any future instance of this class should match — a
deployment-local directory, scaffold-written, resolved by the deployment's own verbs, with the
upstream-only directory's README stating its scope in the first paragraph rather than leaving it
to infer from usage.

**Attestation loop.** `design/GPG-TRUST-LAYER.md` (opening + §7), `design/GPG-TRUST-LAYER-FAQ.md`
(full document, this pass's own rewrite), `law/keys/README.md` (full document, a fresh rewrite),
and `CAPABILITIES.md` (opening + items 29/30) each ran the A:B:C fresh-context loop
(`design/ABC-AUDIT-LOOP-RECIPE.md`) before this entry closed, B spawned synchronously
(`run_in_background: false`, per that recipe's own hard requirement) both rounds, four B
instances per document (round 1 + round 2), eight total. Round 1: DEFECT on all four (7, 5, 4,
and 5 findings respectively — link-on-first-use gaps, undefined jargon, a dropped gloss, bare
noun-phrase bullets); every finding repaired by C (this session) before round 2. Round 2:
`CAPABILITIES.md` came back CLEAN (all four Rule 1 clauses enumerated); the other three still
found small residual defects (a wrong section cross-reference, "apparatus"/"HMAC"/"Ed25519" used
before being glossed, two bare re-stated filenames breaking the document's own link convention,
a doubled-preposition sentence) — 2, 4, and 3 findings respectively. Per ADR-0017's own two-round
cap, none of the three got a third B round: each is recorded `escalated: true` and the orchestrator
(this session) applied round 2's suggested repairs verbatim before recording the attestation,
mirroring the precedent this same BACKLOG already set for the GPG trust layer's own first pass
(entry above, "Two escalations on one small documentation set"). All four records appended to
`attestations/doc-legibility-attestations.jsonl`; `gates/doc_attestation_presence.py` run in gate
mode over all four afterward reports clean (0 findings) — the record's content hash matches the
FINAL, post-repair bytes in every case, since the record is written after the last repair, not
before.

## Contemporaneity Part 3 — the preamble's ordering obligations SPEC authored (Fable, 2026-07-12)

`design/CONTEMPORANEITY-PART3-SPEC.md` discharges the Part 3 sketch that
`design/CONTEMPORANEITY-AUDIT.md` filed ("the whole governance preamble's ORDERING
obligations become one deontic/temporal ASP program"). Authoring only — nothing
implemented; Sonnet executes from the spec, observer-grade, standard scratch ceremony.
What it fixes in place: (1) a twelve-family obligation catalogue (F1–F12) over the
scaffolded preamble's twelve points — 8 of 12 points get an M-core (with every J-residue
named against the conformance map's M/J split), 4 are out of scope with reasons (git
commits = a third record system, filed as possible Part 4; assumption-before-commitment =
the J-boundary's cleanest case; points 11/12 = content conventions with no ordering
component); (2) the cross-clock "before": a tokened row is placed on the hook-journal
clock via its s23 invocation's [mint, completion] interval (invocations.jsonl +
bash_completions.jsonl, one host clock), interval semantics with typed UNDECIDABLE
refusals — the DB host's `ts` and s24's unauthenticated declared event time never key a
cross-record comparison (a backdated declaration must not retro-discharge an ordering
obligation); (3) Anderson reduction held: obligations enter as recorded facts
(`preamble_obligation/2`, scaffold-assigned), violations are derived flags, no modal
operators — no divergence from the settled position; (4) SQL floor pair REQUIRED, no
#minimize exemption invocable, Part 2's single-producer resequencing explicitly not
repeated silently; (5) EDB extensions E1–E9 all named with sources — no kernel delta;
the only new record anywhere is E6 (verify-commission verb journals its verdict,
template-side). ADR-0017 A:B:C loop run with SYNCHRONOUS B both rounds: round 1 eight
findings (all repaired and round-2-verified), round 2 ONE repair-introduced finding —
C applied B's exact specified fix but no third B round was run (the two-round cap), so
the attestation records round 2 DEFECT with `escalated: true` (content_sha256
8b5bf4d4c76a760e9d1186a26f2881e37e811e8f1aad74b0facc0c841ca9b5e5) — the
non-converging-review-loop typed event, routed upward by this entry and the authoring
session's report rather than laundered into a CLEAN. Deterministic gates
(link_integrity, doc_shapes, doc_attestation_presence) all clean on the committed text.

## Maintainer decision brief published: the six open maintainer-only decisions in plain language (Sonnet, 2026-07-12)

`design/MAINTAINER-DECISION-BRIEF.md` — the review-gap ruling, the two ADR amendment texts,
ADR-0009 re-instancing, the research-ledger apply, pg_hba hardening, and the maintainer's own
key-generation act, each reduced to a plain-words question, a yes/no cost, and an exact
copy-paste act, per ADR-0017's zero-context-reader standard for the maintainer's own
non-technical read; ran its own two-round A:B:C loop (synchronous B both rounds), round 1 five
findings (undefined "terminal"/"fingerprint" jargon, an unresolved git-revision citation, a
bare Related list, noun-phrase bylines) all repaired, round 2 two further findings ("ratified"
used before its gloss, a stray "the orchestrator" breaking the document's own plain-English
convention) fixed by the orchestrator at the two-round cap, `escalated: true` recorded.
## Regulator-adoption assessment delivered: four institutional lenses, all not-yet, convergent (Fable, commissioned, 2026-07-12)

Discharges the maintainer's commission "what would NRC, NIST, FAA, ICJ have to say about the
state of the system — would they be able to adopt it for software development with Claude,
and if not, why not?" plus its frame question "are there features missing from
BRIEF-CONFORMANCE-MAP.md?" (read as: gaps in the map's own frame, not unfilled rows).
Deliverable: design/REGULATOR-ADOPTION-ASSESSMENT.md — the honesty constraint is stated in
its opening and binds it throughout: the four lens verdicts are Sonnet analyst outputs used
as gap-finding lenses, never certifications, legal opinions, or compliance determinations.

Method, per the delegation contract: four self-contained Sonnet lens agents (NRC / NIST /
FAA-DO-178C / ICJ-evidentiary), each reading the real artifacts and citing them; the
synthesis re-verified every load-bearing live claim directly before publishing (verify
artifacts, never reports). Witnessed 2026-07-12 by this session's own re-observation:
`git tag -l` empty (zero ratified/* tags); law/keys/ holds only README.md (AWAITING-KEY);
run11.ledger has no row_hash column (s26 postdates every settled world); pg_authid shows
role bork passwordless + rolsuper with SHOW ssl = off (PG-HBA-HARDENING.md still
prepared-unapplied); no requirements.txt/pyproject.toml anywhere at the top two levels.

All four lenses verdict not-yet and CONVERGE on the same blockers — the convergence is the
planning signal: (1) the GPG trust layer is built+witnessed but inert, covering zero bytes
of the existing evidence corpus; (2) open perimeter + no backup/retention story for the one
Postgres instance under everything; (3) no configuration index — the live-verbs model leaves
the audit instruments unpinned against the evidence they produce and read; (4) independence
is invocation-distinctness inside one host/vendor/human trust domain, with the run-11
depth-of-review gap on top; (5) the verifier itself is unverified (hooks/gates have no test
suite; the contemporaneity audit is a single producer with N≈1-2 thresholds). Map-frame gaps
(what the BRIEF/map never ask): substrate durability and perimeter, the apparatus as its own
subject (who verifies the verifier; instrument pinning; model-version drift as a tool-qual
event), the institution around the record (custodianship, key-person continuity, incident
response, data classification of ledger content, git-substrate spoliation posture,
key-custody gradient), proportionality/DAL-grading and subject product depth, cross-world
common cause. Proceed-plan in the deliverable: Tier 1 arms what exists (real key, pg_hba,
first s26 world + signed head, scaffold-time commit-hash anchor, apparatus unknown-key
sweep); Tier 2 closes named halves (backup verb, audit second producer, commission-orphan
view, hook unit tests, finding-disposition vocabulary, signed commits); Tier 3 routes
decisions to the maintainer (trust-domain acceptance-or-second-channel, independence for
the apparatus's own change process, tool-qualification package, corpus accretion). Out of
scope on principle, named in the deliverable: no ephemera committing, no LLM verdict in
any blocking path, no patching settled worlds, no token accounting in the audit trail.

ADR-0017 A:B:C loop, B spawned SYNCHRONOUSLY per the twice-witnessed orphaning friction:
round 1 DEFECT (6 findings — DO-330/s23/DAL-SIL/class-ratifiable/succession-rule referents,
fragment lead-ins), repaired; round 2 DEFECT (4 NEW findings — one fragment, I<n> shorthand
unglossed, DerivationRecords unexplained, one subject-less opener), two-round cap hit,
non-converging-review-loop escalation adjudicated by the loop-runner applying B's repairs
verbatim (the banked GPG/work-status precedent); attestation recorded escalated:true,
content_sha256 5d534cfbfc2b..., in attestations/doc-legibility-attestations.jsonl.
Self-application notes: this session's worktree was found 156 commits behind next and
fast-forwarded before any work (the GPG worktree's own precedent, named per the same rule);
the tracker item regulator-adoption-assessment was already open+claimed, so the permit
existed without a new opening act; the four lens reports are session working input, not
banked — every claim carried into the deliverable points at a repo artifact or a named
re-observation instead.

---

## Contemporaneity audit, Part 2 — the SQL-floor marriage differential CLOSED (2026-07-12, Sonnet, commissioned build)

Closes the deferral `design/CONTEMPORANEITY-AUDIT.md`'s own Status section named ("this verb
ships ONE producer today, not the marriage discipline's cross-validated pair") and
CAPABILITIES.md item 24's own "Second-producer status, declared honestly" note — the
marriage-grade half of the audit-verb-completions work item (`--retain`-by-default wiring and
session-granularity questions stay filed, unchanged by this pass; Part 3, which landed as an
authoring-only Fable spec — `design/CONTEMPORANEITY-PART3-SPEC.md` — during this same window per
`next`'s own history, is also untouched by this pass — a spec, not yet built).

**Built**: `engine/contemp_floor.py` (the SQL floor, `engine/ledger_floor.py`'s sibling for this
domain) and `engine/contemp_differential.py` (the differential runner, `engine/ledger_differential
.py`'s sibling). `./audit --differential` (opt-in, default OFF) wires both into the operator verb.

**INDEPENDENCE DECISION, ARGUED (the honest choice the commission asked for by name):** the SQL
floor RE-DERIVES FROM SOURCE rather than consuming `engine/contemp_edb.py`'s own staged EDB text.
Reasoning, stated in `contemp_floor.py`'s own docstring and re-derived here: `engine/
ledger_floor.py`'s own precedent already settles this question for the ledger marriage (its SQL
floor reads live DB rows directly, never `ledger_edb.py`'s exported text) — consuming the OTHER
producer's own staging/parsing code would let a bug IN THAT SHARED LAYER (a mis-parsed timestamp,
a mis-read column) show up identically in both producers, and the differential would silently
AGREE on a wrong answer, defeating the entire reason a differential exists. So `contemp_floor.py`
(a) queries `ledger` directly via its own SQL text, never calling `contemp_edb.export()`, and
(b) re-reads and re-parses the raw `.claude/logs/*.jsonl` journal bytes with its own small parser
(`_floor_read_jsonl`/`_floor_parse_ts_ms`), never importing `contemp_edb.py`'s `_read_jsonl`/
`_parse_ts_ms` — mirroring the established `_wi_quote`-not-`quote_term` precedent already in
`ledger_floor.py`'s own `work_item_floor_atoms`. The shared INPUT is the real bytes on disk (the
live ledger table; the raw journal files) — exactly the "one ledger, read-only" shared-input
posture `ledger_floor.py`'s own docstring already states, extended here to the second real source
(the journals) this domain also has. Thresholds are read from the SAME text file
(`engine/contemp_thresholds.lp`) the ASP side loads as a program, parsed here as DATA (regex over
the fact lines) — one textual source of truth, never a hand-copied duplicate literal.

**DENOMINATION NORMALIZATION**, the one place this marriage differs mechanically from the ledger
marriage (the commission's own mandate: "mind the 32-bit clingo anchor convention ... the
COMPARISON must normalize to one denomination before diffing, stated explicitly"). The SQL floor
emits every timestamp as its true ABSOLUTE epoch-ms (Postgres `bigint`, no ceiling); the ASP
producer emits every timestamp anchor-relative (`contemp_edb.py`'s own documented dodge of
clingo/clasp's 32-bit signed-int wraparound on an absolute 2026-era epoch-ms value). Exactly three
`#show` predicates carry an absolute-ts argument — `token_min_ts/2`, `token_max_ts/2`, `silence/2`
— found by reading every predicate `contemporaneity.lp` shows and classifying each as Id/Tok-only
(no normalization needed), already-a-difference (`row_delta_ms/2`, `preceding_activity_age_ms/2`
— anchor-invariant by construction, since subtracting a constant from both operands of a
subtraction leaves the result unchanged), or absolute-ts-bearing (these three). The differential
normalizes those three UP to absolute (adding the SAME `anchor_ms` the EDB export computed for
that exact EDB) before the set-comparison runs — a closed, named list in
`contemp_differential.py`'s own `_TS_SINGLE_PREDS`/`_TS_PAIR_PREDS`, not a heuristic regex over
every predicate, so a future predicate defaults to "no normalization" (correct for the common
case) rather than being silently mis-normalized by an over-eager pattern.

**A SECOND, PREVIOUSLY-LATENT 32-BIT HAZARD, FOUND LIVE authoring this commission's own seen-red
fixture (not fixed at the source; flagged, and guarded against in-scope) — the actual finding this
build's own two failed-then-fixed test runs surfaced, named honestly rather than smoothed over.**
The first version of case (p) (the AGREE demonstration) manufactured a scratch world combining
case (h)'s intake-shape burst and case (f)'s late-declared shape, positioned in the fixture's
execution order AFTER cases (i)-(o) — which write rows via a REAL `led` shim, whose `ts` defaults
to actual wall-clock `NOW()` (~2026). Combined with the fixture's own synthetic `BASE` constant
(epoch ~2000000000s, ~2033) in the SAME accumulated scratch ledger (`contemp_edb.py` and
`contemp_floor.py` both read the WHOLE `ledger` table unconditionally, no windowing), that
produced a ~7-YEAR audited window — about 100x past clingo/clasp's signed-32-bit ceiling
(`2**31-1` ms, ~24.8 days). `contemp_edb.py`'s own docstring claims its anchor-relative encoding
is "safely under the 2^31 ceiling" for "even a full week" — true for a bounded window, but nothing
enforces that bound, and this fixture accidentally built an unbounded one. The relative DELTA
itself wrapped silently inside clingo (no error, no warning — exactly the class of hazard
`contemp_edb.py`'s own docstring already documents for the ABSOLUTE-value case, now shown to also
apply to the anchor-relative encoding once the window is wide enough): the first test run reported
a spurious `DIVERGE_DEFECT` with 25 mismatched atoms, all differing by exactly a clean multiple of
`2**31` ms — the wraparound's own signature, not a real encoding bug in either producer. **Fixed
two ways, both in-scope, neither touching `engine/contemp_edb.py`'s own semantics** (out of this
commission's touch-list — its normal ASP-producer role, single-producer contract, and everything
else about it stand untouched): (1) `contemp_differential.py` gained `_max_abs_relative_ms`, a
defensive pre-flight scan of the EDB text's own fact lines that QUARANTINEs loudly (NO RESULT,
ADR-0015 Rule 3) whenever a world's audited window exceeds the safe 32-bit bound, rather than
silently comparing two producers where the ASP side's numeric encoding may already be corrupted —
a genuine, durable hardening any REAL long-lived project ledger could eventually need too, not
just this fixture's own artifact (a project's ledger naturally widens as months/years of real
rows accumulate, and nothing today windows the export). (2) the seen-red fixture's case (p)/(q)
block was moved to run BEFORE cases (i)-(o) (documented inline, in the fixture file itself, with
the full diagnosis) so it demonstrates a genuine AGREE on a still-honestly-narrow window, not a
QUARANTINE of its own fixture's making. A SEPARATE bug was found and fixed in the SAME debugging
pass: case (q)'s negative-control subprocess script passed `root` as a bare Python `str` instead
of a `Path` into `contemp_differential.run_differential()`, which raised
`TypeError: unsupported operand type(s) for /: 'str' and 'str'` the moment either producer tried
`root / ".claude" / "logs"` — caught by the SAME live re-run, fixed by wrapping the interpolated
path in `Path(...)` inside the generated script.

**WITNESSED, both polarities, live.** `seen-red/contemporaneity-audit/run_fixtures.py` now carries
SEVENTEEN cases (was fifteen). Case (p) (GREEN): the combined intake-shape + late-declared world,
differentialed via a REAL `python3 engine/contemp_differential.py --root <world> --retain`
subprocess (the exact invocation `./audit --differential` makes) →
**AGREE, `asp=63 sql=63 atoms; Δasp=[] Δsql=[]`**, exit 0, DerivationRecord pair retained under
`engine/docs/ledger-marriage/derivations/contemporaneity/contempprobe/<ts>_<hash>/` (committed;
banked verbatim as `seen-red/contemporaneity-audit/differential-agree.txt`). Case (q) (RED,
manufactured): the SAME override seam `engine/tests/test_ledger_marriage.py::
test_single_producer_mutation_is_diverge_defect` already precedents for the ledger marriage
(`run_differential(..., sql_atoms_override=...)`) substitutes a single forged atom
(`token_burst("forged-token-not-real")`) for the SQL floor's ENTIRE returned set, in an isolated
subprocess (a throwaway tempfile script, never imported into the fixture's own process) — never
touching `engine/contemp_floor.py`'s or `engine/lp/contemporaneity.lp`'s own source to fake it →
**DIVERGE_DEFECT**, `only_sql` naming exactly the one forged atom, `only_asp` naming the 63
legitimate atoms the forgery discarded (banked verbatim as
`seen-red/contemporaneity-audit/differential-diverge-defect.txt`). Full 17-case suite re-run
clean end to end after both fixes, exit 0, zero scratch residue confirmed directly (`information_
schema.schemata` query for `contempprobe%`/`cfloorprobe%` returns empty; every world tempdir
removed). `gates/fixture_census.py` and `gates/no_lazy_imports.py` both re-run clean (44 seen-red
gates registered, zero lazy-import violations across the two new modules).

**`./audit --differential` exit-code wiring**: a new exit code 4 is reserved, reachable ONLY when
`--differential` is passed AND `contemp_audit`'s own verdict was clean (exit 0) but the
differential verdicted DIVERGE_DEFECT/QUARANTINED — never silently folded into a clean exit 0
(ADR-0015's "no result is not a clean result", applied to the differential axis, not just the
verdict axis). A non-zero `contemp_audit` exit (1/2/3) is never overwritten by the differential's
own code — the first problem found stays the reported one, and the differential's own `[OK]`/`[!!]`
line still prints either way. Smoke-tested live (a fresh scratch world, `./audit --differential`
via the real bash script, both the AGREE path — exit 0, both report sections printed — and the
exit-4 bash-arithmetic path in isolation).

**Default OFF, reasoned (not silently assumed):** unlike `judge` (which IS the differential — no
cheaper single-producer fallback exists), `audit`'s primary report is useful and cheap standalone,
and `--differential` roughly doubles the work per invocation (a second live-DB read, a second
independent journal re-parse, a second clingo invocation) for a check most turns of this observer
verb do not need. `audit.tmpl`'s own header states this reasoning inline, not just here.

**Deferrals, unchanged, named again for this pass's own record:** `contemp_audit.py`'s own
`--retain` still defaults OFF; the verdict is still computed over the WHOLE ledger window, never
per-session; Part 3 (the deontic/temporal ordering-obligations ASP program) is untouched, as
scoped — a separate, Fable-authored spec in progress.

**Files**: `engine/contemp_floor.py` (new), `engine/contemp_differential.py` (new),
`bootstrap/templates/audit.tmpl` (edited — `--differential` flag + exit-4 wiring + updated header),
`seen-red/contemporaneity-audit/run_fixtures.py` (edited — cases (p)/(q), `run_differential`/
`run_differential_diverge_defect` helpers, updated docstring), `seen-red/contemporaneity-audit/
differential-agree.txt` + `differential-diverge-defect.txt` (new, banked evidence),
`engine/docs/ledger-marriage/derivations/contemporaneity/contempprobe/<ts>_<hash>/` (new, banked
DerivationRecord pair), `design/CONTEMPORANEITY-AUDIT.md` (Status section extended),
`CAPABILITIES.md` item 24b (new, minimal), this entry.
