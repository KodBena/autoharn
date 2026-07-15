# MIGRATION MANIFEST — file-by-file dispositions for the consolidation

- **Served model (self-report):** claude-fable-5. No introspective channel could detect
  a silent substitution; this is the session's own system-context report.
- **Status:** DESIGN, maintainer-scannable BEFORE bulk building. Companions: `LAYOUT.md`
  (the destination tree and its justifications), `BUILD-BRIEF.md` (the executable steps).
- **Dispositions:** **MIGRATE** (copied into `~/w/vdc/1/autoharn` at the stated
  destination; source repos untouched — salvage-by-supersession, mandate §5),
  **ATTIC-STAYS** (the NLP lane: stays operational in `claude_harness`, kept "just in
  case", never consolidated — mandate §4), **EVIDENCE-STAYS** (banked evidence: stays
  where it happened; the old repos become read-only archives at the HOME-FLIP), **DEAD**
  (churn with no live consumer; evidence of deadness stated; **deletion is the
  maintainer's call, never ours**).
- **Provenance mechanics:** the per-file `source repo + commit + sha256` record required
  by mandate §5 is generated MECHANICALLY at copy time into
  `autoharn/provenance/MIGRATION.tsv` (BUILD-BRIEF §3) — pre-computing hashes here would
  go stale with any interim commit; the copy-time record is the one that can be
  re-derived and checked. This manifest is the disposition design that TSV must match
  1:1; a mismatch is a build failure, not a shrug.
- **Vocabulary:** as LAYOUT.md's vocabulary block (ADR, DDL, EDB, ASP, DTO, kernel,
  stores, seen-red, arm/drive); NLP = the natural-language-processing daemon lane.

## Counts (by disposition; the build-time TSV is the mechanical census)

| Disposition | Count | Of which |
|---|---|---|
| MIGRATE | **≈253** | claude_harness ≈187 (engine 26, instruments +4, stores 10, gates/filing/hooks 17, law 84, design 14, research 95→as 4 corpora… see rows), epistemic-operator ≈88 |
| ATTIC-STAYS | **≈330** | fact-mining NLP lane ≈277, adjudicate 21, impedance 31, standing-service gate machinery |
| EVIDENCE-STAYS | **≈3,939** | docs/claude-ephemera 3,493; epistemic-operator run evidence ≈300; fact-mining evidence docs ≈130; misc records |
| DEAD | **2 entries** | `.probe_test.txt`; the whole discarded `~/w/vdc/1/autoharn-drive/` |

Numbers marked ≈ are the row-sums of this manifest; the acceptance gate (BUILD-BRIEF §9)
requires the TSV row-count to reconcile against these dispositions exactly, so any
drift between design and build is loud.

## Judgment-call index ([CONS-DECIDED], scannable)

- **[CONS-DECIDED: C1]** Evidence trees are classified at directory granularity with
  exact counts (uniform disposition; per-file rows reserved for the working surface).
  Compression, not omission: a directory row disposes of every file under it.
- **[CONS-DECIDED: C2]** `judgment/` is split from `law/`: ratified tenets/briefs BIND;
  governing consults/operating brief GOVERN but carry proposal-status content. One
  directory would read two authority levels as one (ADR-0008).
- **[CONS-DECIDED: C3]** GOVERNS set = engine seeds (4) + seed-review + panel (10) +
  inc-0 + e15–e18 analyses (+e15 FRAME) + e19 seed + POST-FABLE brief + the ratified
  clause-defeat deliberation. e16/e17/e18 **design**-SEEDs classified EVIDENCE — POST-
  FABLE's own rule: "the consult, once committed, supersedes its SEED" (overrides the
  characterization agent's GOVERNS tag on them).
- **[CONS-DECIDED: C4]** `FINDINGS.md` MIGRATES as a root live ledger (verified live,
  F1–F53, no supersession language); `RATIFICATION.md` stays (2026-07-04 runbook,
  superseded in practice by e6+ protocols and the harness machinery).
- **[CONS-DECIDED: C5]** The three pending FINDINGS-ratification packages (e15/e16/e17)
  MIGRATE into `judgment/e-series/` — the maintainer's ratification pass is owed and
  must be runnable from the continuation home.
- **[CONS-DECIDED: C6]** Of version-lineaged machinery, the LATEST deployed version
  migrates as the working copy (e14 change gate + delivery drill + gate probe, e17
  stamp intercept + launch.conf, e18 arm + freeze); earlier versions stay as evidence.
  `s18-atomic-review-detail.sql` stays: a rejected, NOT-SHIPPED design witness, not
  kernel lineage.
- **[CONS-DECIDED: C7]** `clingo_run.py` — the one genuinely cross-lane module (both
  the engine and the mined-facts lane import it) — migrates with the engine. No
  dual-write forms: the old repo freezes as archive at the flip and its attic copy
  serves only the attic; post-flip the autoharn copy is authoritative (provenance
  direction reverses, mandate §5).
- **[CONS-DECIDED: C8]** Zero-consumer flags: `law_census.py`/`law_census_entries.py`/
  `verify_registry_parity.py` MIGRATE despite no importers — mandate §3 names the law
  census and registry surface explicitly, and mtimes show fresh build, not churn.
  `l2_check.py` (mining-KB CLI, zero importers, zero tests, prose-only reference)
  is ATTIC-STAYS and flagged as churn-candidate for the maintainer.
- **[CONS-DECIDED: C9]** `docs/research/` corpora MIGRATE as the research library even
  though the mandate does not name them: the engine's formal-systems direction reads
  against the obligations survey, and a continuation home without its research library
  forces cross-repo reads for live design work. Cheap (markdown).
- **[CONS-DECIDED: C10]** The two external-standards BRIEFs migrate WITH their
  `sources/` PDFs (~9 MB): the authority and its evidence base travel together;
  PUBLISHING.md's redaction posture governs any future push.
- **[CONS-DECIDED: C11]** The engine/hook design docs buried in fact-mining
  (`LEDGER-LOGIC-MARRIAGE.md`, `LOGIC-LAYER-*.md`, `HOOK-DESIGN.md`,
  `DEPLOYMENT-ROADMAP.md`) MIGRATE to `design/`; the NLP runtime they describe stays
  attic. The thesis travels; the lab stays.
- **[CONS-DECIDED: C12]** `ARCHITECTURE.md` migrates carrying an explicit STALE banner
  + a BACKLOG entry (rewrite owed) — rewriting it is content work outside a migration
  increment; the banner is ADR-0008's deliberately-imprecise tag, not a shrug.
- **[CONS-DECIDED: C13]** Renames: `db/harness/` → `stores/` (single-occupant parent
  flattened); `docs/claude-ephemera/` → `ephemera/`; `pretooluse_change_policy.py` →
  `hooks/pretooluse_change_gate.py`; `arm_e18.sh` → `drive/arm.sh` (parameterized
  template; e18-specifics stripped, recorded); every rename is a row below.
- **[CONS-DECIDED: C14]** `standing_service_gate.py` + `standing_service_registry.py`
  + their test STAY with the attic: they gate the NLP daemons that stay. A migrated
  copy with zero services would be a silent vacuous pass (the F49 class); the gate
  joins autoharn when its first standing service does (ADR-0016 scope clause).
- **[CONS-DECIDED: C15]** Doc-legibility gate migrates with scope widened to ALL
  tracked human-readable `*.md` (maintainer ruling 2026-07-07: the gate "ought to apply
  to any documentation a human might read"; filed as finding **48** in the general
  findings ledger). Definition surfaces (GLOSSARY/terms/allowlist) stay global.
- **[CONS-DECIDED: C16]** The four fact-mining harness verifiers
  (`row_performed_by.py`, `verify_binder.py`, `verify_operator_turns.py`,
  `verify_relevant_act.py`) land in `instruments/` (they read the harness substrate at
  verification time and pair with seen-red 39/25/09); `verify_registry_parity.py`
  lands in `engine/` (it pins the judgment registry).
- **[CONS-DECIDED: C17]** The acts adapter (`tools/act_stream/`) lands at
  `instruments/act_stream/` — it is the Port/ACL the close instruments consume through.
- **[CONS-DECIDED: C18]** `hooks/` split from `gates/`: interception surfaces vs
  refusal logic; the new pre-commit invokes gates by REPO-RELATIVE path, dissolving
  epistemic-operator's absolute-path reach into the sibling repo (a two-repo coupling
  the fresh home must not inherit).
- **[CONS-DECIDED: C19]** `runs/` + `ephemera/` are the forward evidence homes:
  "evidence stays where it happened" applied forward — after the flip, where it
  happens is autoharn.
- **[CONS-DECIDED: C20]** A **fixture-census gate** is minted in the build increment
  (no such gate exists today — grep-verified): it enumerates `seen-red/` against the
  registered gates/close-lines and fails on a gate without both-polarity proof. It is
  the mechanization of mandate §6's "every migrated gate's seen-red still proves it
  can fail".
- **[CONS-DECIDED: C21]** A **layout-census gate** is minted in the build increment
  (maintainer ruling: LAYOUT conformance must be a checked property): top-level
  registry + per-directory currency patterns, both polarities; the "single-currency"
  judgment residue is declared review-only (ADR-0011 Rule 1).
- **[CONS-DECIDED: C22]** `experiments/adjudicate/` and `experiments/impedance/` are
  classified at directory granularity (uniform ATTIC-STAYS): self-contained
  sub-projects with their own internal docs; per-file rows would add length, not
  information. (C1's rule applied to attic, flagged separately for visibility.)
- **[CONS-DECIDED: C23]** The e15 rehearsal machinery (`anchor_pre_registration.py`,
  `make_mock_session.py`, `rehearse.py`) migrates to `drive/rehearsal/` — it is the
  reusable negative-control toolchain (a mock close distinguishable from a real one),
  not run evidence; its outputs stay as evidence.
- **[CONS-DECIDED: C24]** `test_rationalization_ledger.py` migrates to `stores/` as
  the 002 store's fixture (DDL and its proof are one lineage entry), leaving its
  fact-mining location — it tested repo-root machinery from inside the wrong lane.

---

## Repo A — claude_harness

### A1. Root + config

| Source | Disposition → destination | Role |
|---|---|---|
| `README.md` | MIGRATE → source for `autoharn/README.md` (rewritten: new tree map; old text archived by the frozen repo) | repo orientation |
| `CLAUDE.md` | MIGRATE → `CLAUDE.md` (adapted: same law, paths updated; adaptation recorded in provenance TSV) | the working standard |
| `GLOSSARY.md` | MIGRATE → `GLOSSARY.md` | coined-term SSOT |
| `BACKLOG.md` | MIGRATE → `BACKLOG.md` (live entries carried; closed entries remain in archive history) | filed-deferral home |
| `HANDOFF.md` | EVIDENCE-STAYS | 2026-07-03 session handoff, superseded by POST-FABLE brief |
| `OOM-TMPFS-INCIDENT-2026-07-02.md` | EVIDENCE-STAYS | incident record (point-in-time) |
| `PUBLISHING.md` | MIGRATE → `design/PUBLISHING.md` | publish/redaction posture |
| `.claude/settings.json` | MIGRATE → `.claude/settings.json` (adapted: hook paths inside autoharn) | Claude Code hook wiring |
| `.gitignore` | MIGRATE → `.gitignore` (adapted) | ignore rules |
| `docs/CONSOLIDATION-MANDATE.md` | MIGRATE → `provenance/CONSOLIDATION-MANDATE.md` | the law of this transition |
| `docs/consolidation/` (3 files, this design) | MIGRATE → `provenance/` | the transition's design record |
| `docs/ARCHITECTURE.md` | MIGRATE → `design/ARCHITECTURE.md` + STALE banner + BACKLOG entry [C12] | stale (2026-06-27) architecture through-line |
| `docs/SHIPPING-NORTH-STAR.md` | MIGRATE → `design/SHIPPING-NORTH-STAR.md` (marked PROPOSAL — maintainer's court) | product definition proposal |
| `docs/possibly-addressable-concerns.md` | MIGRATE → `design/possibly-addressable-concerns.md` | live concern inventory |
| `docs/publish-commit-map-2026-07-07.txt` | EVIDENCE-STAYS | old-sha/new-sha publish rewrite map (binds old history) |
| `docs/evidence-strays/…` (1) | EVIDENCE-STAYS | filed stray-output record |
| `docs/bug-reports/*.md` (3) | EVIDENCE-STAYS | upstream Claude Code bug reports (point-in-time) |
| `docs/bug-reports/.probe_test.txt` | **DEAD** — stray probe artifact; zero references (grep), dot-file droppings of a bash probe | deletion = maintainer's call |
| `docs/work-units/*` (3) | EVIDENCE-STAYS | completed work-unit specs + witness for stores 005/006 |

### A2. db/harness → stores/ (10 files, all MIGRATE)

| Source | Destination | Role |
|---|---|---|
| `db/harness/001_research_ledger.sql` | `stores/001_research_ledger.sql` | perf/research claim-ledger DDL |
| `db/harness/002_rationalization_ledger.sql` | `stores/002_rationalization_ledger.sql` | detector-fire store DDL |
| `db/harness/003_acts_stream.sql` | `stores/003_acts_stream.sql` | vendor-neutral acts stream DDL |
| `db/harness/004_rulings_ledger.sql` | `stores/004_rulings_ledger.sql` | acts.ruling (anchors, supersedes chains) DDL |
| `db/harness/005_findings_ledger.sql` | `stores/005_findings_ledger.sql` | general findings ledger DDL |
| `db/harness/006_foreclosure_debt.sql` | `stores/006_foreclosure_debt.sql` | foreclosure-debt store DDL |
| `db/harness/006_foreclosure_debt_fixture.py` | `stores/006_foreclosure_debt_fixture.py` | both-polarity fixture for 006 |
| `db/harness/007_ruling_delivers_fk.sql` | `stores/007_ruling_delivers_fk.sql` | delivers-FK (ruling→delivery integrity) DDL |
| `db/harness/007_ruling_delivers_fixture.py` | `stores/007_ruling_delivers_fixture.py` | both-polarity fixture for 007 |
| `experiments/fact-mining/test_rationalization_ledger.py` | `stores/test_rationalization_ledger.py` [C24] | fixture for 002 + filing tool |

### A3. tools/ → gates/ · filing/ · hooks/ (18 files: 17 MIGRATE, 1 ATTIC)

| Source | Destination | Role |
|---|---|---|
| `tools/staging_guard.py` | `gates/staging_guard.py` | explicit-paths commit guard (finding 33/fc20) |
| `tools/no_lazy_imports.py` | `gates/no_lazy_imports.py` | lazy-import ban gate (edict 2026-07-02) |
| `tools/no_destructive_ddl.py` | `gates/no_destructive_ddl.py` | destructive-DDL refusal gate |
| `tools/append_only_integrity.py` | `gates/append_only_integrity.py` | append-only store integrity gate |
| `tools/findings_gate.py` | `gates/findings_gate.py` | close line: RED on any OPEN finding |
| `tools/findings_gate_fixture.py` | `gates/findings_gate_fixture.py` | both-polarity fixture for findings gate |
| `tools/doc-legibility/` (4 files) | `gates/doc-legibility/` — scope widened to all tracked `*.md` [C15] | coined-term legibility gate |
| `tools/standing_service_gate.py` | ATTIC-STAYS [C14] | umbrella gate over the NLP daemons that stay |
| `tools/file_finding.py` | `filing/file_finding.py` | finding filing CLI (005) |
| `tools/file_foreclosure.py` | `filing/file_foreclosure.py` | foreclosure filing CLI (006) |
| `tools/file_resolution.py` | `filing/file_resolution.py` | resolution filing CLI |
| `tools/file_rationalization.py` | `filing/file_rationalization.py` | rationalization-fire filing CLI (002) |
| `tools/persist_claude_ephemera.py` | `filing/persist_claude_ephemera.py` (target: `ephemera/`) [C13] | whole-session ephemera snapshotter |
| `tools/hooks/pre-commit` | `hooks/pre-commit` (rewritten: repo-relative gate paths; staging guard + no_lazy_imports + fixture census + layout census + doc-legibility) [C18][C20][C21] | git pre-commit |
| `tools/hooks/stamp_provenance.py` | `hooks/stamp_provenance.py` | Claude-harness provenance stamper |

### A4. docs/adr + adr-evidence → law/adr + seen-red (62 files, all MIGRATE)

| Source | Destination | Role |
|---|---|---|
| `docs/adr/0000…0016` (17 files) | `law/adr/` verbatim | the LAW corpus |
| `docs/adr-evidence/seen-red/**` (44 files, 17 gate dirs) | `seen-red/<gate>/` verbatim | both-polarity gate proofs (04 consumer-no-vacuous, 05 verify-adapter, 06 append-only, 09 relevant-act, 12 contemporaneity-degrade, 18 bash-write, 24 destructive-DDL, 25 operator-turn, 31 interception-stamp, 33 staging-guard, 35 delivery-freight, 36 substrate-required, 38 review-without-detail, 39 binder, 42 gate-journal-registered, 43 arming-delivery-set, 45 criterion-reviewer-grants, engine-inc1-controls, review-fixpoint) |
| `docs/adr-evidence/foreclosure-waiver-requests.md` | `judgment/rulings/foreclosure-waiver-requests.md` (pending maintainer waiver decisions) | waiver-request queue |

### A5. docs/design-notes → design/ (7 files, all MIGRATE)

| Source | Destination | Role |
|---|---|---|
| `design-notes/review-fixpoint-protocol.md` | `design/review-fixpoint-protocol.md` | the fixpoint protocol (read with the three-knob vocabulary) |
| `design-notes/never-again-mechanism-fable-main.md` | `design/never-again-mechanism-fable-main.md` | foreclosure-mechanism design (main) |
| `design-notes/never-again-mechanism-fable-consult.md` | `design/never-again-mechanism-fable-consult.md` | foreclosure-mechanism consult |
| `design-notes/never-again-synthesis.md` | `design/never-again-synthesis.md` | foreclosure-mechanism synthesis |
| `design-notes/policy-authoring-seam.md` | `design/policy-authoring-seam.md` | policy-authoring seam design |
| `design-notes/deductive-engine-fable-main-shape.md` | `design/deductive-engine-fable-main-shape.md` | engine main-shape note |
| `design-notes/human-side-fragility.md` | `design/human-side-fragility.md` | human-side failure-mode note |

### A6. docs/research → research/ (4 corpora, ~95 files, all MIGRATE [C9])

| Source | Destination | Role |
|---|---|---|
| `research/2026-06-27-foundational-map/` (12) | `research/foundational-map/` | cross-repo mechanization/typing map |
| `research/2026-06-27-logic-investigation/` (18) | `research/logic-investigation/` | 14-logic survey + software landscape + autoharn fit |
| `research/2026-06-27-logic-fair-trials/` (18) | `research/logic-fair-trials/` | re-run fair-trials survey + audit + exemplar |
| `research/2026-06-27-obligations-formalisms-survey/` (35) | `research/obligations-formalisms-survey/` | obligation taxonomy × 27 formal systems (doc-legibility SCOPE member today) |
| `research/2026-07-02-nlp-logic-interface/` (7) | `research/nlp-logic-interface/` | NLP→logic interface design research (the hook thesis) |

### A7. docs/claude-ephemera (3,493 files) — EVIDENCE-STAYS [C1]

Whole-session audit snapshots; stays in the archive. Autoharn starts its own
`ephemera/` (empty at init; first occupant = the build session's own snapshot —
auditability law applies to the builder too).

### A8. experiments/fact-mining — the engine extraction (30 MIGRATE)

The deductive-engine surface, extracted whole from the negative specimen. Import-path
fixes are a recorded adaptation (BUILD-BRIEF §5); everything else verbatim.

**→ `engine/`** (16 py + 1 json + tests):

| Source (`experiments/fact-mining/`) | Destination | Role |
|---|---|---|
| `ledger_edb.py` | `engine/ledger_edb.py` | typed EDB export from any ledger target |
| `ledger_floor.py` | `engine/ledger_floor.py` | SQL floor (recursive CTEs), differential producer 1 |
| `ledger_differential.py` | `engine/ledger_differential.py` | bit-identical ASP-vs-SQL marriage gate + DerivationRecord |
| `clingo_run.py` | `engine/clingo_run.py` [C7] | shared clingo subprocess runner |
| `acts_edb.py` | `engine/acts_edb.py` | acts EDB + SQL floor for ledger_acts.lp |
| `acts_join.py` | `engine/acts_join.py` | acts↔ledger relevance/claim/ref derivation |
| `ledger_acts_scratch.py` | `engine/ledger_acts_scratch.py` | scratch exercise, acts program vs SQL |
| `ledger_diff_scratch.py` | `engine/ledger_diff_scratch.py` | scratch lineage firing every T_now predicate |
| `ledger_dto_scratch.py` | `engine/ledger_dto_scratch.py` — **NEVER run against the live scratch** (standing constraint: rebuild erases the maintainer's authentic attestation act) | DTO scratch exercise |
| `ledger_support_scratch.py` | `engine/ledger_support_scratch.py` | support-closure scratch exercise |
| `dto_authentic_verify.py` | `engine/dto_authentic_verify.py` | derive-only DTO/T_now/assumes re-run |
| `judgment_registry.py` | `engine/judgment_registry.py` | authority registry of engine judgment classes |
| `registry_baseline.json` | `engine/registry_baseline.json` | sha256 baseline of judgment-class specs |
| `verify_registry_parity.py` | `engine/verify_registry_parity.py` [C8][C16] | registry-vs-live-surface parity |
| `law_census.py` | `engine/law_census.py` [C8] | machine-readable law census w/ ratification depth |
| `law_census_entries.py` | `engine/law_census_entries.py` [C8] | hand-maintained census data half |
| `ledger_acts.lp` | `engine/lp/ledger_acts.lp` | acts↔ledger audit consumers (ASP) |
| `ledger_assumes.lp` | `engine/lp/ledger_assumes.lp` | assumes-edge validity/expiry closure |
| `ledger_dto.lp` | `engine/lp/ledger_dto.lp` | DTO clause-defeat closures |
| `ledger_support.lp` | `engine/lp/ledger_support.lp` | support-exposure closure + flag-discharge |
| `ledger_tnow.lp` | `engine/lp/ledger_tnow.lp` | T_now derived-validity program |
| `test_ledger_acts.py` | `engine/tests/test_ledger_acts.py` | acts program differential tests |
| `test_ledger_marriage.py` | `engine/tests/test_ledger_marriage.py` | marriage/differential/DTO tests |
| `test_ledger_support.py` | `engine/tests/test_ledger_support.py` | support-closure differential tests |
| `test_acts_join.py` | `engine/tests/test_acts_join.py` | acts-join classification tests |

**→ `instruments/`** [C16]:

| Source | Destination | Role |
|---|---|---|
| `row_performed_by.py` | `instruments/row_performed_by.py` | binds ledger rows' claimed actor to the writing acts-stream INSERT |
| `verify_binder.py` | `instruments/verify_binder.py` | standing fixture: one-act-binds-many-rows (seen-red 39) |
| `verify_operator_turns.py` | `instruments/verify_operator_turns.py` (import fixed: `delivery_drill` now repo-local in `drive/`) | standing fixture: operator-turn/splice extraction (seen-red 25) |
| `verify_relevant_act.py` | `instruments/verify_relevant_act.py` | standing fixture: ledger-relevance classification (seen-red 09) |

### A9. experiments/fact-mining — the NLP lane (ATTIC-STAYS, ≈277 files)

Everything below stays in `claude_harness`, operational, per mandate §4 — the attic is
kept, not consolidated. Roles compressed; the standing-service gate and its path-gated
pre-commit trigger stay with it [C14].

| Source (`experiments/fact-mining/`) | Role — all ATTIC-STAYS |
|---|---|
| `README.md`, `BOOTSTRAP.md` | NLP-lane overview + jax-only coref daemon runbook |
| `nlp_server.py`, `nlp_client.py`, `nlp_docs_client.py`, `nlp_cache.py`, `docbin_cache.py` | GPU spaCy daemon + clients + caches |
| `coref_decode_{server,daemon,client,wire,inputs}.py`, `coref_host_shell.py`, `run_coref_stack.py` | jax coref decode daemon stack |
| `jax_deberta.py`, `jax_decode.py`, `jax_only_guard.py`, `deberta_weights.py`, `deberta_export_codec.py`, `export_deberta_maverick.py`, `validate_deberta_keyset.py`, `enumerate_ckpt_globals.py`, `maverick_load.py`, `capture_fixtures.py`, `profile_decode.py` | DeBERTa/maverick export + pure-jax forward + guards |
| `gliner_{server,client,wire,enrich}.py`, `measure_gliner_quality.py` | GLiNER daemon stack |
| `extract.py`, `resolve.py`, `resolve_coref.py`, `load_facts.py`, `standalone_preprocess.py`, `transcript_prose.py`, `shape_buckets.py`, `spans.py`, `span_store.py`, `staging.py`, `scrub.py`, `wire_types.py`, `readiness.py`, `bound_socket.py`, `boot_id.py`, `hook_trial.py`, `measure_vocab_growth.py` | extraction pipeline, wire types, daemon infra, hook-trial driver |
| `kb_{ledger,writer,why,migrate}.py`, `logic_backend.py`, `logic_layer.lp`, `logic_repair.lp`, `why_layer.lp`, `why_orphaned.sql`, `rsup_esc.sql`, `l2_check.py` (churn-candidate [C8]), `fde_z3.py`, `qty_z3.py`, `unsat_core_z3.py` | mined-facts KB + its logic layers (NOT the harness ledger) |
| `contra_{app,asp,context,detect}.py`, `contra_schema.sql`, `fixtures/contra_synthetic.txt` | contradiction demo over mined claims |
| `schema.sql`, `trace_schema.sql` | `mining` + `trace` schema DDL |
| `standing_service_registry.py`, `conftest.py` | declared-services registry + pytest marker config [C14] |
| `parse_seam/` (7 files) | polymorphic parse backend (spaCy/Stanza) |
| `nla_lab/` (50 files) | numerics lab: encode-variant portfolio, Pallas kernels, distill, bench (production coref imports `variants/cached_positions`) |
| `test_*.py` (69 files: all root tests except the 5 engine/store tests migrated in A8/A2) | the daemon-hardening/KB/wire/fidelity test net — each stays with its module-under-test |

### A10. experiments/{adjudicate, impedance, stamp-lab}

| Source | Disposition | Role |
|---|---|---|
| `experiments/adjudicate/` (21 files) | ATTIC-STAYS [C22] | standalone schema-first HITL adjudication widget (reused by the coref hook) |
| `experiments/impedance/` (31 files) | ATTIC-STAYS [C22] | standalone typed host/device impedance library |
| `experiments/stamp-lab/` (3 files) | EVIDENCE-STAYS | e17 stamp-mechanism shakedown record (precondition evidence) |

### A11. experiments/fact-mining/docs

| Source (`…/fact-mining/docs/`) | Disposition | Role |
|---|---|---|
| `LEDGER-LOGIC-MARRIAGE.md` | MIGRATE → `design/LEDGER-LOGIC-MARRIAGE.md` [C11] | the engine thesis: ledger⇄logic marriage |
| `LOGIC-LAYER-ASP.md` | MIGRATE → `design/LOGIC-LAYER-ASP.md` [C11] | ASP logic-layer design |
| `LOGIC-LAYER-SEAM.md` | MIGRATE → `design/LOGIC-LAYER-SEAM.md` [C11] | logic-backend seam design |
| `HOOK-DESIGN.md` | MIGRATE → `design/HOOK-DESIGN.md` [C11] | the epistemic-state hook design (project thesis) |
| `DEPLOYMENT-ROADMAP.md` | MIGRATE → `design/DEPLOYMENT-ROADMAP.md` [C11] | deployable-thesis roadmap |
| `safety-critical-logging-standards/` (17 files incl. sources/) | MIGRATE → `law/briefs/safety-critical-logging/` [C10] | THE authoritative BRIEF + sources + sweep intermediates |
| `incomplete-evidence-standards/` (6 files incl. sources/) | MIGRATE → `law/briefs/incomplete-evidence/` [C10] | sibling BRIEF + sources |
| `CONTRADICTION-DEMO.md`, `CONTRADICTION-DEMO-DESIGN.md` | ATTIC-STAYS | contra-demo docs (with their code) |
| `NLA-OPTIMIZATION-PORTFOLIO.md`, `NLA-OPTIMIZATION-PORTFOLIO-RESIDUE-1.md` | ATTIC-STAYS | nla_lab portfolio docs |
| `HANDOFF.md`, `RELEASE-LEGAL-CONSULT.md`, `decode_forward.dot`, `decode_math.tex` | ATTIC-STAYS | NLP-lane handoff, licensing consult, decode diagrams |
| `hook-trial/` (27 files) | EVIDENCE-STAYS [C1] | hook-trial run evidence (findings JSONs, reports) |
| `recidivism-study/` (35 files) | EVIDENCE-STAYS [C1] | the recidivism study (cited by ADR amendments — citations stay valid in the archive; provenance path-note covers them) |
| `ledger-marriage/` (24 files) | EVIDENCE-STAYS [C1] | marriage witnesses + per-substrate derivations |
| `audit-evidence/` (12 files) | EVIDENCE-STAYS [C1] | workflow audit transcripts |

---

## Repo B — epistemic-operator

### B1. Root documents

| Source | Disposition | Role |
|---|---|---|
| `POST-FABLE-OPERATING-BRIEF.md` | MIGRATE → `judgment/POST-FABLE-OPERATING-BRIEF.md` | the operating law for stand-ins |
| `BRIEF-CONFORMANCE-MAP.md` | MIGRATE → `law/briefs/BRIEF-CONFORMANCE-MAP.md` | apparatus↔BRIEF invariant map |
| `FINDINGS.md` | MIGRATE → `FINDINGS.md` (root) [C4] | live F-series findings ledger |
| `RATIFICATION.md` | EVIDENCE-STAYS [C4] | superseded 2026-07-04 run-1 runbook |
| `marriage-increment-1-closeout.md` | EVIDENCE-STAYS | increment close-out record |
| `harness/workflow-mechanics-lab.md` | EVIDENCE-STAYS | pre-e15 arming-precondition shakedown record |
| `docs/deletions.md` | EVIDENCE-STAYS | append-only removal-rationale log (binds old tree) |
| `e6…e9-operator-protocol.md` (4) | EVIDENCE-STAYS | per-experiment operator protocols |
| `publish-commit-map-2026-07-07.txt` | EVIDENCE-STAYS | publish-rewrite sha map |
| `tainted/e9-design-consult-9.TAINTED.md` | EVIDENCE-STAYS — never read, never migrated | quarantined by standing constraint |
| `.gitignore` | (source repo config; autoharn writes its own) | — |

### B2. instruments/ → instruments/ (30 MIGRATE, 1 EVIDENCE)

All of `close_manifest.py` (the mandatory-close-lines registry), `close_sweep.py`,
`cite_check.py`, `contemporaneity.py`, `coverage_audit.py`, `derive_trail.py`,
`enacts_chain.py`, `ledger_target.py` (the target SSOT — registry updated for autoharn,
recorded adaptation), `observed_currency.py`, `read_currency.py`, `review_fixpoint.py`,
`review_fixpoint_close.py`, `review_queue.py`, `review_without_detail.py`,
`soundness.py`, `soundness_twin.py`, `stale_enactment_debt.py`, `core_a.lp`,
`soundness.lp`, `run-core-a.sh` (stderr plank already fixed at source — verified),
`verify_consumer_no_vacuous.py`, `verify_contemporaneity_degrade.py`,
`verify_delivery_freight.py`, `verify_gate_journal_registered.py`,
`verify_review_fixpoint.py`, `verify_review_without_detail.py`,
`verify_substrate_required.py`, `README.md`, `fixtures/core-a-broken.lp`
→ **MIGRATE → `instruments/`** (flat, same names; `fixtures/` kept).
`sweep-results.txt` → **EVIDENCE-STAYS** (banked sweep output; the one evidence file
committed inside the old instruments dir — the mixing the new layout forbids).

### B3. tools/ → instruments/act_stream/ + hooks/ (7 MIGRATE)

| Source | Destination | Role |
|---|---|---|
| `tools/act_stream/contract.py` | `instruments/act_stream/contract.py` [C17] | vendor-neutral Act/Stream contract + persist |
| `tools/act_stream/claude_code_adapter.py` | `instruments/act_stream/claude_code_adapter.py` | Claude Code JSONL → acts adapter |
| `tools/act_stream/verify_adapter.py` | `instruments/act_stream/verify_adapter.py` | adapter fixture/mutation verifier (seen-red 05) |
| `tools/act_stream/verify_bash_write.py` | `instruments/act_stream/verify_bash_write.py` | bash-write classification fixture (seen-red 18) |
| `tools/act_stream/fixtures/syn_session/` (2) | `instruments/act_stream/fixtures/syn_session/` | synthetic transcript fixtures |
| `tools/hooks/pre-commit` | merged into `hooks/pre-commit` [C18] | staging-guard shim (absolute-path reach dissolved) |

### B4. harness/ — machinery MIGRATE set [C6]

| Source | Destination | Role |
|---|---|---|
| `harness/launch_subject.sh` | `drive/launch_subject.sh` | packet staging + journal truncate + leak checks |
| `harness/e18-build/arm_e18.sh` | `drive/arm.sh` (parameterized template; e18-specifics stripped — recorded adaptation) [C13] | the arm-script idiom: mechanical pre-arm checks + frozen delivery set |
| `harness/e18-build/freeze_manifest.sh` | `drive/freeze_manifest.sh` | anchor-order freeze-manifest emitter |
| `harness/e17-build/launch.conf` | `drive/launch.conf.template` (latest instance as template) | per-run config consumed by launch_subject.sh |
| `harness/e14-build/delivery_drill.py` | `drive/delivery_drill.py` | splice-free tmux delivery drill + `--check` |
| `harness/e14-build/gate_probe.py` | `drive/gate_probe.py` | change-gate probe against a scratch mirror |
| `harness/e18-build/adjudicate_repro.py` | `drive/adjudicate_repro.py` | findings repro-recipe adjudicator |
| `harness/e15-build/rehearsal/{anchor_pre_registration,make_mock_session,rehearse}.py` | `drive/rehearsal/` [C23] | mock-session negative-control toolchain |
| `harness/e14-build/pretooluse_change_policy.py` | `hooks/pretooluse_change_gate.py` [C13] | the subject-side change gate (latest, exploit-hardened) |
| `harness/e17-build/stamp_intercept.py` | `hooks/stamp_intercept.py` | HMAC stamp hook for psql ledger writes |
| `harness/e9-build/s10-schema.sql` | `kernel/lineage/s10-schema.sql` | kernel gen s10 (standalone) |
| `harness/e10-build/s11-schema.sql` | `kernel/lineage/s11-schema.sql` | kernel gen s11 (standalone) |
| `harness/e11-build/s12-schema.sql` | `kernel/lineage/s12-schema.sql` | kernel gen s12 (standalone) |
| `harness/e13-build/s13-schema.sql` | `kernel/lineage/s13-schema.sql` | kernel gen s13 (standalone) |
| `harness/e14-build/s14-schema.sql` | `kernel/lineage/s14-schema.sql` | kernel gen s14 (+amends_scope uniqueness) |
| `harness/e14-build/nla/nla-schema.sql` | `kernel/lineage/nla-schema.sql` | catalog-isolated `nla` re-instantiation |
| `harness/e15-build/s15-schema.sql` | `kernel/lineage/s15-schema.sql` | kernel gen s15 (isolated db + typed antecedent; **carries the set_actor hardcode — foreclosed by a new lineage increment, BUILD-BRIEF §6**) |
| `harness/e15-build/s13-review_detail-truncate-guard-remediation.sql` | `kernel/lineage/s13-remediation-review-detail-truncate-guard.sql` [C13] | s13 truncate-guard remediation |
| `harness/e17-build/s17-stamp-mechanism.sql` | `kernel/lineage/s17-stamp-mechanism.sql` | delta: stamp_secret + HMAC columns |
| `harness/e17-build/s17-independence-vocabulary.sql` | `kernel/lineage/s17-independence-vocabulary.sql` | delta: self-review vocab + stamp-distinctness |
| `harness/e18-build/s18-criterion-principals.sql` | `kernel/lineage/s18-criterion-principals.sql` | delta: INSERT-only criterion-reviewer principals |
| `harness/e17-build/s17_stamp_fixture.py` | `kernel/fixtures/s17_stamp_fixture.py` | forgery/staleness refusal proof |
| `harness/e17-build/s17_independence_fixture.py` | `kernel/fixtures/s17_independence_fixture.py` | self-review/proxy/distinct proof |
| `harness/e15-build/readiness_vs_close_fixture.py` | `kernel/fixtures/readiness_vs_close_fixture.py` | close-mode vs readiness-mode gating proof |
| `harness/e16-build/FINDINGS-RATIFICATION-PACKAGE.md` | `judgment/e-series/e16-FINDINGS-RATIFICATION-PACKAGE.md` [C5] | pending maintainer pass |
| `harness/e17-build/FINDINGS-RATIFICATION-PACKAGE.md` | `judgment/e-series/e17-FINDINGS-RATIFICATION-PACKAGE.md` [C5] | pending maintainer pass |

**Everything else under `harness/`** — packets, oracles, kickoffs, frozen texts,
fixtures-for-subjects, transcripts, closes, pretests, ambiguity rounds, arm witnesses,
lab sessions, ruling packets, verification outputs, `s18-atomic-review-detail.sql`
(rejected NOT-SHIPPED design witness [C6]), earlier hook/gate/probe versions, e7–e13
build dirs in full — **EVIDENCE-STAYS** [C1] (≈250 files by directory).

### B5. consults/ (per-file, GOVERNS → judgment/ vs RECORD → stays)

**MIGRATE → `judgment/engine/`** [C3]: `engine-design-SEED.md`,
`engine-frontier-semantics-SEED.md`, `engine-frontier-semantics-SEED-review.md`,
`engine-assurance-arguments-SEED.md`, `engine-obligations-epochs-SEED.md`,
`engine-increment-0-unification.md`, `engine-panel/` (all 10: 4 design + 4 refute +
critic-completeness + DECISION-BRIEF-deny-surface).

**MIGRATE → `judgment/e-series/`** [C3][C5]: `e15-analysis-consult-27.md`,
`e15-analysis-consult-27-FRAME.md`, `e16-analysis-consult-31.md`,
`e17-analysis-consult-35.md` (§0 ERRATUM governs its mapping),
`e18-analysis-consult-39.md`, `e19-design-SEED.md`,
`e15-FINDINGS-ratification-package.md`.

**MIGRATE → `judgment/rulings/`** [C3]:
`deliberations/clause-defeat-decompose-then-overrule.md` (contains a ratified,
binding ruling).

**EVIDENCE-STAYS (RECORD)** — everything else in `consults/` and `deliberations/`
(~80 files): e5–e14 design/build consults + BRIEFs (10 experiments × 2–4 files),
`e14-nla-rebuild(.md/-BRIEF.md)`, e15 design consults 21/25 + span-inspection +
PRELIM, e16/e17/e18 design SEEDs + design consults 29/33/37 (superseded per POST-FABLE
supersession rule [C3]), `next-increment-design-consult-23(+BRIEF)`, all
`marriage-i1…i5` consults + BRIEFs + fixpass + completion, `engine-census-ratification-*`
and `engine-inc0-ratification-*` filings (.md/.sql/.out — acts already landed in the
DB), `consults/external/` (4), `consults/e6-evidence/`, and the 10 remaining
`deliberations/` records.

### B6. witness/ (28 files) — EVIDENCE-STAYS [C1]

Change-gate journals, gate-state snapshots, witness transcripts, off-host tees,
close records: run evidence in full, no machinery present (verified).

---

## Repo C — the discarded attempt

| Source | Disposition | Evidence of deadness |
|---|---|---|
| `~/w/vdc/1/autoharn-drive/` (entire tree) | **DEAD** | The maintainer's own ruling, verbatim in CONSOLIDATION-MANDATE.md: "built on the WRONG MANDATE … and is DISCARDED — not salvaged, not extended." Its CENSUS's set_actor finding is carried as risk input (BUILD-BRIEF §6/§8); nothing else is consumed. **Deletion is the maintainer's call** — this manifest only records that no live consumer remains. |

## Reconciliation

MIGRATE row-sum: ≈253 files (A: ~187 — root/config 14, stores 10, gates+filing+hooks 17,
law/adr 17, seen-red 44+1, design-notes 7, research ~95 in 5 corpora counted at A6,
engine+instruments 30, design docs from fact-mining 5, briefs 23; B: ~88 — root 3,
instruments 30, act_stream+hooks 7, drive+hooks+kernel machinery 26, judgment 22).
ATTIC-STAYS: ≈330. EVIDENCE-STAYS: ≈3,939 (3,493 ephemera + ~446 across both repos).
DEAD: 2 entries. Every tracked file in both repos falls under exactly one row above
(per-file or directory row); the build-time `provenance/MIGRATION.tsv` must reconcile
against this manifest 1:1 before the acceptance run counts (BUILD-BRIEF §9).

