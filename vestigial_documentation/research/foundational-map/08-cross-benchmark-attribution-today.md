# Report 08 — cross/benchmark-attribution-today (Pillar 2 — provenance/accountability ledger)

## Summary

chocofarm already has a near-Federal-Reserve-grade benchmark provenance ledger (throughput-lab/harness/exp_db.py): a Postgres store with tlab_config / tlab_reading / tlab_finding / tlab_prereg / tlab_prereg_conclusion that mechanizes measurement vs interpretation vs criterion-before-data, each row stamped with a code_stamp {git_commit, git_tree=clean|DIRTY}, host, recorded_at, command, and tool. omega has a parallel discipline in tools/work-status/schema.sql: items/refs/deps/labels with a query-time work_status_violations gate ('shipped-without-ship-ref') and an audit_log trail that captures actor=application_name (PGAPPNAME, the closest thing to a session id) and commit_sha from a transaction GUC. So the building blocks of a ledger EXIST — but they are unconnected and incomplete in four specific ways. The accountability gap is precise: a perf claim in a commit message ("~12x", "11.6x", "-26%", "+85%") is hand-typed prose that is NOT machine-linked to (a) the benchmark artifact/rows, (b) the environment, (c) the hypothesis/finding it tested, or (d) the Claude session that authored it. Worse, the one link that exists (tlab_reading.git_commit) points at the commit the reading was MEASURED at (usually a DIRTY working tree or the prior baseline), never the BANKING commit that asserts the win — so the perf commit's hash appears in no reading row at all. Findings are cited across both stores as free-text ("finding #32", "tlab_finding #37", "DB findings #28->#34"), and the Claude session is recorded only as a model-name trailer (Co-Authored-By: Claude Opus 4.8) or a free string 'coordinator'.

## Key facts

- chocofarm's ledger is already built: exp_db.py defines tlab_config (HP config, dedup on config_key), tlab_reading (one row per replicate; metrics leaf_rows_s/dps/server_util_pct + raw counts + provenance), tlab_finding (append-only interpretations, status {provisional,confirmed,retracted}, supersedes FK), tlab_prereg (typed criterion-before-data), tlab_prereg_conclusion (Criterion.evaluate verdict, links resolved_by_reading/resolved_by_finding).
- The provenance stamp on every chocofarm row = git_commit + git_tree CHECK IN ('clean','DIRTY') + host + recorded_at (exp_db.py lines 200-203). It is produced by code_stamp.py via `git rev-parse --short HEAD` + `git status --porcelain`; a DIRTY tree marks a non-reproducible artifact.
- DIRECTION MISMATCH: tlab_reading.git_commit is the commit the reading was measured AGAINST (often DIRTY candidate or baseline HEAD), not the later perf(...) commit that BANKS the claim. The 'vectorize encode_response ~12x' commit hash is recorded in zero reading rows.
- Perf claims live as prose in commit BODIES: the encode_response commit body states '11.6x faster', 'inflight=1 RTT 453.5 -> 335.8 us (-26%)', 'saturated 4281 -> 7776 msg/s (+85%)' — hand-transcribed from bench output, machine-checked by nothing.
- Findings are referenced as free text, never FKs: commit bodies say 'finding #32', 'Recorded as tlab_finding #37 (provisional)', 'DB findings #28->#34', 'tlab_finding #22 as the OOM RCA'. The number is a human pointer, not a database edge.
- Claude session attribution is absent. chocofarm: only the git trailer 'Co-Authored-By: Claude Opus 4.8' (model name, not a session UUID). omega: audit_log.actor = current_setting('application_name') defaulting to 'coordinator'/'unknown' (schema.sql line 162) — a free string, not a stable session id.
- Environment is under-captured: tlab_reading stores only host (socket.gethostname()). The commit prose discusses load-bearing env that has no column: 'intra-VM', 'VM<->host-GPU boundary', AVX2 gated on __AVX2__, taskset -c 3 pinning, 5-rep median. None is queryable.
- No benchmark-artifact pointer: tlab_reading has command + raw counts but no path/hash to the raw bench output, tensorboard run dir, or perf.data. Profiles live unlinked on disk under ~/w/vdc/chocobo/profiles/*.log and *.perf.data (docs/operations.md lines 296-349).
- omega's work_status_violations view ALREADY encodes the pattern to generalize: a row resolution='shipped' with NO ref of kind IN ('pr','commit','worklog') is a query-time violation (schema.sql lines 120-124). This is exactly the shape a 'perf-claim-without-evidence-reading' gate would take.
- omega audit_log already supports per-commit time-travel: commit_sha from GUC `audit.commit`, plus table_asof() and asof.sh <git-sha> resolving a commit's committer timestamp (schema.sql lines 159-213).
- BACKLOG.md already names the discipline the ledger should enforce: 'a baseline/target is a stamped reading, not a prose number, and a finding cites a reading_id not a bare figure' (BACKLOG.md, finding-#12 entry ~line 207-208) — currently policy, not mechanism.
- ADR-0011 Rule 1 (omega docs/adr/0011) enumerates the enforcement-surface vocabulary the harness's logic-gates must pick from: compile-time | build/CI gate | write-time data constraint | query-time gate | advisory surface | checklist-at-a-named-moment | review-only.

## Existing mechanisms (reuse, don't reinvent)

| Mechanism | What it does | Location |
|---|---|---|
| **exp_db.py benchmark-results store** | Postgres ledger: tlab_config/reading/finding/prereg/conclusion; persists every replicate with code_stamp provenance, command, tool, tag; separates measurement (auto-recorded) from interpretation (deliberately authored finding) from criterion (immutable prereg). Reading.__post_init__ rejects a rate field whose count/span/quotient are inconsistent (forecloses the reference-140k cross-window class). | `/home/bork/w/vdc/1/chocofarm/throughput-lab/harness/exp_db.py (schema lines 167-340; record_reading 653; record_finding 801; register/conclude_prereg 923/998)` |
| **code_stamp** | Single home for the ADR-0011 measurement-provenance stamp: returns {commit short-hash, tree clean\|DIRTY}; degrades to {unknown,DIRTY} off-repo; mirrored inline by episodic_dps.sh's two git invocations. | `/home/bork/w/vdc/1/chocofarm/throughput-lab/harness/code_stamp.py` |
| **omega work-status store + work_status_violations** | Relational SSOT (items/refs/deps/labels) mirroring work-status.schema.json; refs.kind enum includes 'commit'/'pr'/'worklog'; a query-time view flags shipped items lacking a pr/commit/worklog ref and dependency/parent cycles. | `/home/bork/w/omega/tools/work-status/schema.sql (refs lines 80-90; view lines 105-128)` |
| **audit_log + table_asof/asof.sh** | Append-only history trigger on every work-status table; captures actor=application_name (session marker via PGAPPNAME) and commit_sha from the `audit.commit` GUC; supports time-travel by timestamp and per-git-sha. | `/home/bork/w/omega/tools/work-status/schema.sql (lines 150-213)` |
| **ADR-0009 performance investigation discipline** | Defines a closed vocabulary of perf claims (improvement/regression/null) and requires a captured before/after profile attached to any such claim — the policy the ledger would enforce as a write-time constraint. | `/home/bork/w/omega/docs/adr/0009-performance-investigation-discipline.md (and chocofarm docs/adr/0009)` |
| **ADR-0011 Rule 1 enforcement-surface vocabulary** | Names the seven enforcement mechanisms a discipline may declare; the catalog from which each harness logic-gate selects its surface (write-time constraint vs query-time gate vs build/CI hook). | `/home/bork/w/omega/docs/adr/0011-mechanization-discipline.md (Rule 1)` |

## Gaps (where the haphazardness lives)

- No banking-commit edge: a perf(...) commit's hash is in no reading row, so 'which commit asserts this win and on what evidence' is unanswerable by query. tlab_reading.git_commit is the MEASURED-at commit, a different (often DIRTY) state.
- No machine link commit->finding/reading: commit bodies cite 'finding #32' / 'tlab_finding #37' as prose; no FK, so the recurrence-net's findings cannot be joined to the commits that acted on them.
- No Claude-session column anywhere: the only attributions are a model-name git trailer (chocofarm) and a free 'coordinator' PGAPPNAME string (omega). A bug cannot be traced to the session that introduced it; a reading cannot be traced to the session that banked it.
- Perf-claim numbers are unverified prose: '~12x'/'-26%'/'+85%' are hand-typed into commit messages with nothing checking them equal median(candidate)/median(baseline) over the cited readings.
- Environment is one column (host): no CPU model/governor/turbo, taskset pinning, kernel, build flags (AVX2), JAX/CUDA versions, or VM-vs-host-GPU boundary — all of which the commit prose treats as load-bearing.
- Benchmark artifacts are unlinked files: raw bench logs, tensorboard run dirs, and perf.data profiles sit under ~/w/vdc/chocobo/profiles/ with no path/hash column joining them to a reading.
- Two disjoint stores, no shared provenance schema: chocofarm has readings/findings but no audit_log/session attribution; omega has audit/session-ish attribution but no reading/finding/prereg tables. The 'bug -> introducing session' and 'commit -> evidence' edges exist in neither.
- Prereg conclusions link readings/findings but not the commit that shipped the consequent change, so 'decisive -> what did we build because of it' is not closed.

## Harness hooks (where a registry / ledger / logic-gate plugs in)

- Add a session_id (and agent/model) column to every provenance-stamped row: tlab_reading/finding/prereg/conclusion (exp_db.py) and replace omega audit_log's free 'coordinator' actor with the Claude Code session id. Source it from a SessionStart hook / env var so code_stamp() can emit {commit, tree, session_id} as one unit.
- Add a banked_commit (or a separate commit<->reading join table) to tlab_reading so the perf(...) commit that asserts a win links to the baseline-reading(s) and candidate-reading(s) that justify it; this is the missing inverse of the existing measured-at git_commit.
- Parse a commit-message trailer at commit time via a git hook (ADR-0011 Rule 1 'build/CI gate'): `Tlab-Reading: <ids>`, `Tlab-Finding: <id>`, `Tlab-Prereg: <slug>`, `Claude-Session: <uuid>` -> write rows into a provenance-edge table, converting today's free-text 'finding #32' into FKs.
- A logic-gate (Z3/OR-Tools/datalog) modeled on omega's work_status_violations: 'every perf(...) commit carrying a % or x claim MUST reference >=1 reading measured at a baseline commit AND >=1 candidate reading, and the claimed ratio MUST equal median(candidate)/median(baseline) within tolerance' — a provable check replacing the prose number. The existing view's 'shipped-without-ship-ref' is the template.
- A tlab_env table keyed by content-hash (CPU model, governor, taskset, kernel, build flags, lib/CUDA/JAX versions, VM-vs-host-GPU boundary), FK'd from tlab_reading — mirrors the tlab_config dedup pattern; makes 'intra-VM', '__AVX2__', 'taskset -c 3' queryable instead of prose.
- A tlab_artifact table (path + sha256 + kind in {bench_log, tensorboard_run, perf_data}) FK'd from tlab_reading, so the ~/w/vdc/chocobo/profiles/*.perf.data and bench logs become code-addressable evidence (closes ADR-0009's 'profile attached to the claim').
- Generalize omega's audit_log triggers + table_asof/asof.sh onto chocofarm's reading/finding tables to give chocofarm the same per-commit time-travel and the 'bug -> introducing session/commit' trace it currently lacks.
- Promote BACKLOG's policy 'a finding cites a reading_id not a bare figure' into a write-time data constraint: make tlab_finding.refs / motivated_change require at least one resolvable reading_id FK rather than free jsonb.

## Anchors (attribution)

| Claim | Where |
|---|---|
| tlab_reading provenance = git_commit + git_tree CHECK(clean\|DIRTY) + recorded_at + host | `/home/bork/w/vdc/1/chocofarm/throughput-lab/harness/exp_db.py:200-203` |
| code_stamp returns {commit, tree clean\|DIRTY}; DIRTY = non-reproducible artifact | `/home/bork/w/vdc/1/chocofarm/throughput-lab/harness/code_stamp.py:27-44` |
| tlab_finding append-only, status enum, supersedes FK (interpretation layer) | `/home/bork/w/vdc/1/chocofarm/throughput-lab/harness/exp_db.py:240-262` |
| tlab_prereg criterion-before-data + tlab_prereg_conclusion links resolved_by_reading/finding | `/home/bork/w/vdc/1/chocofarm/throughput-lab/harness/exp_db.py:277-340` |
| Perf claim '11.6x faster', RTT -26%, +85% live as hand-typed commit-body prose | `chocofarm git log body of 'perf(throughput-lab/wire): vectorize encode_response ... ~12x'` |
| Findings cited as free text: 'Recorded as tlab_finding #37 (provisional)', 'finding #32', 'DB findings #28->#34' | `chocofarm git log -60 bodies (HEAD..~40)` |
| Only session marker in chocofarm is model-name trailer Co-Authored-By: Claude Opus 4.8 | `chocofarm commit trailers` |
| omega audit_log.actor = application_name (PGAPPNAME), commit_sha = GUC audit.commit; default 'coordinator'/'unknown' | `/home/bork/w/omega/tools/work-status/schema.sql:150-169` |
| work_status_violations: shipped item with no pr/commit/worklog ref is a query-time violation | `/home/bork/w/omega/tools/work-status/schema.sql:120-128` |
| Discipline already stated as policy: 'a finding cites a reading_id not a bare figure' | `/home/bork/w/vdc/1/chocofarm/BACKLOG.md (finding-#12 entry, ~line 207-208)` |
| Profiles stored unlinked on disk under ~/w/vdc/chocobo/profiles/*.perf.data and *.log | `/home/bork/w/vdc/1/chocofarm/docs/operations.md:296-349` |
| ADR-0011 Rule 1 enforcement-surface vocabulary (compile-time..review-only) | `/home/bork/w/omega/docs/adr/0011-mechanization-discipline.md (Rule 1)` |


---
*Generated by the `claude-harness-understand` workflow (run `wf_64eb31fd-6c9`, model claude-opus-4-8[1m]), 2026-06-27. Reader findings are structured agent output, verbatim. Anchors cite `file:line/section` in the source projects.*
