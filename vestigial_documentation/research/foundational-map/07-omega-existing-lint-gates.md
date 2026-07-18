# Report 07 — omega/existing-lint-gates

## Summary

omega already has five ADR-0011 mechanization gates plus a shared import-graph library and a Postgres anti-corruption layer — but each is a bespoke zero-dep Node script with its OWN output convention, OWN baseline constant, and OWN CI wiring. They share strong structural DNA (manifest/analyze/report/driver split; `--check`/`--json`/`--self-test` flags; fail-loud-on-crisp-structural-drift vs advisory-on-judgment; NO_NEW_*_RATCHET baselines hardcoded as magic literals in source) yet have NO common spine: no shared result schema, no ledger of findings over time, no queryable store, no attribution of a finding to the git-hash/session that introduced it. The ratchet baselines (doc-graph danglers=38, band findings=30, cycles=0/0) are duck-typed constants the maintainer hand-edits, and the band-conformance BAND_EXCEPTIONS list is a 30-entry hand-curated provenance log living as a JS Map literal — exactly the haphazard, non-queryable attribution the harness should mechanize. Three of five gates emit machine-readable `--json`; doc-graph emits a committed JSON manifest; cochange and source-headers misses are human-text-only. The harness should give all of them one schema + a findings ledger (git-hash-attributed) and reuse the already-extracted import-graph.mjs and the work_status_violations SQL-view pattern as the model.

## Key facts

- doc-graph/generate.mjs: emits committed machine-readable manifest docs/doc-graph.json {nodes,edges} as source of truth, projects 4 artifacts (json/svg/md/report.md). CI gate (doc-graph-ci.yml) checks STRUCTURE freshness only (--check), never gates on broken refs. Carries an advisory NO_NEW_DANGLERS_RATCHET {baselineDate:'2026-06-10', baseline:38} that is REPORT-ONLY (not wired to gate). generate.mjs:206-209.
- cochange-advisory.mjs: per-PR-diff (not state-based) check that a derived doc (declares `<!-- derived-from: <glob> -->`) was updated when its source changed; silence via `cochange-ack:` token in a commit message. ALWAYS exits 0 (never gates); only its --selftest gates. Human-text output only, no JSON. cochange-advisory.mjs:44-45,128.
- band-conformance/check.mjs: enforces ADR-0003 band ordering band(file)>=band(import) over the frontend/src import graph from FILES.md [B1/B2/B3] tags. Emits --json. NO_NEW_FINDINGS_RATCHET {baselineDate:'2026-06-12', baseline:30} IS wired to gate --check (sibling-divergence from doc-graph's report-only ratchet, noted at check.mjs:90-96). Crisp structural drift (ghost row / missing row / broken edge) is fatal (ADR-0002); judgment-shaped band findings stay advisory in detail, gated only on count delta.
- band-conformance BAND_EXCEPTIONS (check.mjs:206-330): a hand-curated Map of ~30 'from|to' edge keys each with a prose reason + date + adjudicating PR number — a provenance/attribution ledger living as a source-code literal. HUB_EXEMPT_TARGETS (check.mjs:174-192) similarly hardcodes 2 exempt hubs with reasons.
- cycle-check/check.mjs: Tarjan SCC over runtime VALUE edges (type-only excluded) of frontend/src; NO_NEW_CYCLES_RATCHET {clusters:0, cyclicNodes:0} IS wired to gate --check on either count exceeding baseline. Emits --json. The baseline comment records the full break history (18->15->12->0 files) as prose in the source constant (check.mjs:52-80). Motivated by vite-8.0.12 vitest-teardown deadlock PR #444.
- source-headers/check.mjs: ADR-0006 path-presence check over frontend src/**.{ts,vue} + backend **/*.py. ADVISORY only — misses never gate (--check exits 0); only a missing-subproject-root is fatal. EXEMPTIONS encoded as data array (check.mjs:165-202). Emits --json. Its --self-test gates the tool itself.
- tools/import-graph.mjs: SHARED library (already extracted per ADR-0012 P1 derive-don't-duplicate) owning the one fact 'how a frontend/src import edge is recovered' — enumerateSrcFiles, resolveImport, extractEdges, collectEdges. Consumed by BOTH band-conformance and cycle-check. This is the existing precedent for a common spine.
- tools/work-status/schema.sql: Postgres `todo` DB anti-corruption layer. Cross-row invariants a CHECK/FK cannot express are surfaced by the SQL VIEW work_status_violations — 'a validator/CI gate fails if it returns rows' (schema.sql:8-10). This is omega's one QUERYABLE, SQL-native gate pattern and the model for a queryable findings store.
- Common shape across all 5 Node gates: substrate-token constants block, parseX -> analyze (pure over inputs) -> printReport / --json / driver; flags --check (CI), --json (machine), --self-test/--selftest (probe-before-trust, gating), --strict (local zero-drift). Zero runtime deps (Node builtins + git [+ dot for doc-graph]); all Public Domain.
- CI wiring is fragmented across 4 workflow files: doc-graph-ci.yml, cochange-advisory-ci.yml, source-headers-ci.yml (both subprojects), and frontend-ci.yml (hosts band-conformance + cycle-check jobs because their inputs are frontend/-scoped). Each duplicates checkout+setup-node+self-test+check steps with path-filter triggers; permissions: contents:read everywhere.

## Existing mechanisms (reuse, don't reinvent)

| Mechanism | What it does | Location |
|---|---|---|
| **doc-graph manifest + freshness gate** | Prose-scans docs, emits committed JSON manifest {nodes,edges} (machine-readable SoT), 4 projections, and an advisory NO_NEW_DANGLERS_RATCHET (report-only). CI gate checks structural freshness, not refs. | `/home/bork/w/omega/tools/doc-graph/generate.mjs + .github/workflows/doc-graph-ci.yml` |
| **cochange-advisory** | Per-PR-diff flag of derived docs whose source changed; commit-message ack token to silence. Never gates (human text only). | `/home/bork/w/omega/tools/doc-graph/cochange-advisory.mjs + .github/workflows/cochange-advisory-ci.yml` |
| **band-conformance + NO_NEW_FINDINGS_RATCHET** | ADR-0003 band-ordering gate over import graph; crisp drift fatal, judgment findings advisory-in-detail/gated-on-count; --json. Holds the BAND_EXCEPTIONS hand-curated attribution ledger. | `/home/bork/w/omega/tools/band-conformance/check.mjs (ratchet:376-379, exceptions:206-330)` |
| **cycle-check + NO_NEW_CYCLES_RATCHET** | Tarjan SCC over runtime value edges; gates on cluster/node count exceeding baseline; --json; --self-test proofs. | `/home/bork/w/omega/tools/cycle-check/check.mjs (ratchet:52-80)` |
| **source-headers path-presence** | ADR-0006 advisory path-presence audit over both subprojects; EXEMPTIONS-as-data; --json; only missing-root gates. | `/home/bork/w/omega/tools/source-headers/check.mjs` |
| **import-graph shared library** | Single home for frontend/src import-edge recovery (enumerate/resolve/extract/collect); consumed by band-conformance + cycle-check. The existing 'common spine' precedent. | `/home/bork/w/omega/tools/import-graph.mjs` |
| **work_status_violations SQL view** | Cross-row invariant gate: a CI gate fails if the view returns rows. omega's only queryable/SQL-native gate; the Postgres anti-corruption layer. | `/home/bork/w/omega/tools/work-status/schema.sql (view defn + header lines 8-10)` |

## Gaps (where the haphazardness lives)

- No common result schema: each gate invents its own --json shape (band: {counts,ghostRows,findings,...}; cycle: {counts,cyclic}; source-headers: {missingRoots,subprojects}; doc-graph: full manifest). Nothing can query 'all findings across all gates' uniformly.
- No findings ledger / time series: ratchet baselines (doc-graph 38, band 30, cycle 0/0) are magic-literal constants hand-edited in source with prose change-logs in comments. There is no queryable record of when a finding appeared/cleared or which git-hash crossed a baseline.
- Non-attributable provenance lives as code: BAND_EXCEPTIONS (~30 entries) and HUB_EXEMPT_TARGETS encode 'who/when/why a leak was adjudicated' (with PR numbers and dates) as JS Map literals — exactly the haphazard attribution the ledger should own; not joinable to git-hash or Claude session.
- Inconsistent gate semantics with no central policy: doc-graph ratchet is report-only, band/cycle ratchets gate, source-headers/cochange never gate — the gate-vs-advisory decision is re-argued in each script's header prose (ADR-0011 Rule 1/3/5) rather than declared in one queryable policy table.
- Two gates emit human-text only (cochange-advisory, source-headers misses are printed but the misses aren't in a stable queryable store beyond --json), and findings are re-derived every run with no persistence — a regression's introducing commit/session is never recorded.
- No use of automated-reasoning tools: band-ordering, cycle-freedom, and exemption-coverage are all decidable constraints (a SAT/Z3/Datalog problem) but are implemented as bespoke imperative scans + hand-maintained baselines; the 'provable vs statistical' capability the harness wants to surface is absent here.
- CI duplication: 4 workflow files re-implement checkout/setup-node/self-test/check with path filters; no shared composite action or single gate runner.

## Harness hooks (where a registry / ledger / logic-gate plugs in)

- Define ONE finding schema (gate_id, finding_kind, subject_path/edge, severity[fatal|advisory], explained_by, baseline_ref, first_seen_hash, cleared_hash) and have each gate's analyze() emit rows in it; the existing --json outputs are the adapters to retrofit.
- Replace the in-source NO_NEW_*_RATCHET magic literals with rows in a queryable baselines table; the harness ledger records crossings and attributes the introducing git-hash/session, closing the non-attributable-git-hash-vs-perf gap the brief names.
- Migrate BAND_EXCEPTIONS / HUB_EXEMPT_TARGETS / source-headers EXEMPTIONS from JS Map literals into an exemptions/adjudications ledger table (subject, reason, adjudicated_date, PR/session) — these are already attribution records, just trapped in source.
- Model the work_status_violations SQL-view pattern as the spine: load each gate's findings into SQL and express 'gate fails iff query returns rows' uniformly; the Postgres `todo` DB at 192.168.122.1 is an existing host for it.
- Generalize import-graph.mjs into the registry's notion of a reusable derived-fact provider (it already serves 2 gates); a CAPABILITY REGISTRY entry should advertise it so new gates derive rather than re-author.
- Encode the decidable invariants (band ordering, acyclicity, exemption coverage) as Z3/OR-Tools/Datalog constraints behind a common gate runner, giving PROVABLE results and replacing hand-maintained baselines — the OR/automated-reasoning capability the registry should surface.
- Unify the 4 CI workflows into one gate-runner step that reads a gate registry (id, command, inputs, gate-vs-advisory policy, baseline-ref) instead of 4 bespoke YAMLs.

## Anchors (attribution)

| Claim | Where |
|---|---|
| doc-graph emits a committed machine-readable manifest as source of truth; CI checks structural freshness only and broken-ref report never gates | `/home/bork/w/omega/tools/doc-graph/generate.mjs:9-33,599-650; .github/workflows/doc-graph-ci.yml:6-19,97-98` |
| NO_NEW_DANGLERS_RATCHET is report-only (baseline 38, 2026-06-10) | `/home/bork/w/omega/tools/doc-graph/generate.mjs:196-209` |
| cochange-advisory is per-PR-diff, advisory, exits 0; ack via commit token; no JSON output | `/home/bork/w/omega/tools/doc-graph/cochange-advisory.mjs:25-45,110-129` |
| band-conformance ratchet (baseline 30) is wired to gate, unlike doc-graph's report-only sibling | `/home/bork/w/omega/tools/band-conformance/check.mjs:90-96,376-379,800-815` |
| BAND_EXCEPTIONS is a ~30-entry hand-curated attribution ledger as a JS Map literal with dates and PR numbers | `/home/bork/w/omega/tools/band-conformance/check.mjs:206-330` |
| cycle-check gates on NO_NEW_CYCLES_RATCHET (clusters 0 / cyclicNodes 0), break-history recorded in the source comment | `/home/bork/w/omega/tools/cycle-check/check.mjs:41-80,362-375` |
| source-headers is advisory-only (misses never gate); EXEMPTIONS encoded as data; only missing-root fatal | `/home/bork/w/omega/tools/source-headers/check.mjs:10-25,165-202,606-620` |
| import-graph.mjs is the already-extracted shared library serving both band-conformance and cycle-check (ADR-0012 P1) | `/home/bork/w/omega/tools/import-graph.mjs:3-22,105-177` |
| work_status_violations is a SQL view that gates when it returns rows — the queryable/SQL-native gate pattern | `/home/bork/w/omega/tools/work-status/schema.sql:8-10 (header) + view definition` |
| CI is split across 4 workflows; band-conformance + cycle-check ride frontend-ci.yml because their inputs are frontend-scoped | `/home/bork/w/omega/.github/workflows/frontend-ci.yml:16-29,69-118` |


---
*Generated by the `claude-harness-understand` workflow (run `wf_64eb31fd-6c9`, model claude-opus-4-8[1m]), 2026-06-27. Reader findings are structured agent output, verbatim. Anchors cite `file:line/section` in the source projects.*
