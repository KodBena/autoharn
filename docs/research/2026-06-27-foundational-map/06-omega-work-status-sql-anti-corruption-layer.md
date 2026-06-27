# Report 06 — omega / work-status SQL anti-corruption layer (the key precedent for the harness's SQL layer)

## Summary

The work-status store is a Postgres anti-corruption layer that replaced a hand-edited docs/work-status.json: structured-only access by SQL, with no file to hand-edit. It demonstrates the exact pattern the harness should generalize. Within-row contract invariants are enforced as CHECK/FK constraints that fail the write loudly (ADR-0002); cross-row invariants a static constraint cannot express are surfaced as rows from a single VIEW (work_status_violations) that a CI gate fails on; the migrator self-certifies a faithful round-trip; and a hand-rolled audit_log + trigger + table_asof() function gives git-correlated, actor-attributed temporal time-travel (asof.sh <git-sha>). What made it succeed: a relational image of a JSON-schema contract with deliberate, amend-by-editing enums; fail-loud + self-certification; an attestation comment block treated as the contract. What is missing for capability-registry + provenance-ledger duty: it models ONE domain (todo items), the commit_sha link is weak/heuristic (committer-timestamp correlation, sha mostly null), there is no notion of a Claude Code session/benchmark/hypothesis as first-class rows, and the machine-readable capability inventory still lives as PROSE in services_local.gitignore (not queryable).

## Key facts

- The store lives in Postgres DB `todo` on the libvirt host (psql -h 192.168.122.1 -d todo); it REPLACED hand-edited docs/work-status.json — reads and status changes both go through SQL, 'there is no file to edit by hand' (services_local.gitignore Network-services table, work-status row).
- Schema is a relational image of docs/work-status.schema.json: one parent table `items` plus three multi-valued children (deps, refs, labels), a `meta` k/v table, and an `extra` jsonb column hoisting JSON-schema additionalProperties:true forward-compat (schema.sql:11-16, 59).
- Within-row contract is enforced structurally: id regex CHECK (schema.sql:47), closed-but-amendable enums as CHECK ... IN lists carrying the FULL vocabulary incl. unused values (state/disposition/resolution/scope/tier, lines 50-54), and a state-shape CHECK encoding the schema's open/closed allOf branches: open ⇒ disposition & no resolution; closed ⇒ resolution + closed_on & no disposition (items_state_shape, lines 64-67).
- Referential integrity via FOREIGN KEYs DEFERRABLE INITIALLY DEFERRED (parent, superseded_by, deps.depends_on) — checked at COMMIT so dangling refs fail loudly before self-certify (schema.sql:56-57,74-75; migrate-to-pg.py:116-118).
- Cheap within-row cycle guards as CHECK (items_no_self_parent, items_no_self_supersede, deps_no_self), with longer cycles deferred to the view (schema.sql:69-70,77).
- The cross-row invariant gate is a single VIEW `work_status_violations`: a non-empty result is the fail signal. A CI/validator runs `SELECT * FROM work_status_violations` and fails if any row returns (schema.sql:99-128).
- The view encodes three cross-row rules: (1) shipped-without-ship-ref — resolution='shipped' but no refs row of kind pr/commit/worklog (a provenance rule, lines 120-124); (2) depends_on-cycle and (3) parent-cycle via WITH RECURSIVE ... CYCLE detection (Postgres native CYCLE clause, lines 106-128).
- Audit layer is hand-rolled (no extensions installed on host, vanilla PG has no SYSTEM_TIME): audit_log table + record_audit() AFTER trigger on every table, capturing actor=application_name (PGAPPNAME, e.g. 'coordinator'), commit_sha=transaction-local GUC `audit.commit`, op, row_key, old_row/new_row jsonb (schema.sql:134-201).
- Temporal time-travel: table_asof(tbl, t) returns each row's last non-DELETE state at-or-before t via DISTINCT ON (row_key) ORDER BY at DESC, audit_id DESC (schema.sql:207-213); asof.sh resolves a git-sha to its COMMITTER timestamp (git show -s --format=%cI) and queries that — a HEURISTIC correlation, exact anchors only where audit_log.commit_sha is set (asof.sh:9-12,17-24).
- Audit-trail carve-out from re-runnable posture: audit_log is NOT dropped on reseed; migrate-to-pg.py calls audit_genesis_snapshot() to re-baseline (rows tagged actor 'genesis-snapshot') because DROP TABLE fires no per-row DELETE triggers, leaving a discontinuity (schema.sql:140-155,215-234; migrate-to-pg.py:153-162).
- Migrator self-certifies (ADR-0002): after load it checks row counts vs JSON, runs the violations view, and reconstructs every item from the relational tables comparing field-for-field (set/multiset, order-insensitive), exiting non-zero on any mismatch (migrate-to-pg.py:120-151).
- Enum amendment is deliberate and attributed: e.g. refs.kind 'audit' added 2026-06-10 with an inline comment citing the audit that surfaced the gap and maintainer approval (schema.sql:83-86) — a worked example of ADR-0011 turning a lapse into a mechanism + attribution.
- Schema/migrator insist on tooling discipline: psycopg3 never psycopg2 (migrate-to-pg.py:7,27), DDL via psql with ON_ERROR_STOP=1, data via parameterized statements (lines 87-114).

## Existing mechanisms (reuse, don't reinvent)

| Mechanism | What it does | Location |
|---|---|---|
| **work_status_violations (cross-row invariant gate)** | Single SQL VIEW whose non-empty result fails a CI gate; encodes provenance rule (shipped ⇒ has pr/commit/worklog ref) and graph cycle rules via WITH RECURSIVE CYCLE. The exact 'logic-gate as a query' the harness wants to generalize. | `/home/bork/w/omega/tools/work-status/schema.sql:99-128` |
| **CHECK/FK contract constraints** | Closed-but-amendable enums (CHECK IN), regex id, within-row state-shape allOf, deferred FKs checked at COMMIT — a write that violates the contract fails loudly (ADR-0002). | `/home/bork/w/omega/tools/work-status/schema.sql:45-97` |
| **audit_log + record_audit() trigger + table_asof()** | Hand-rolled append-only history with actor (application_name) and optional commit_sha (GUC), plus a STABLE function giving as-of-timestamp reconstruction. The provenance-ledger seed. | `/home/bork/w/omega/tools/work-status/schema.sql:159-213` |
| **asof.sh git-sha → committer-timestamp time-travel** | Resolves a git-hash to its committer timestamp and queries table_asof — the existing (heuristic) git-hash ↔ store-state link. | `/home/bork/w/omega/tools/work-status/asof.sh:13-24` |
| **migrate-to-pg.py self-certifying round-trip** | Counts + violations + field-for-field reconstruction comparison, non-zero exit on any divergence; re-baselines audit trail via audit_genesis_snapshot(). The pattern for proving a registry/ledger faithfully images its source. | `/home/bork/w/omega/tools/work-status/migrate-to-pg.py:120-162` |
| **services_local.gitignore (prose capability inventory)** | The de-facto, human-readable capability registry: services, addresses, venvs, browser automation, X11 access, Redis topology. Names work_status_violations as THE gate. Currently prose, not queryable — the gap the capability-registry fills. | `/home/bork/w/omega/services_local.gitignore (Network services / Filesystem resources tables)` |

## Gaps (where the haphazardness lives)

- Single-domain: the schema models only todo items; it has no tables for tools/services/venvs (capability registry) nor for sessions/benchmarks/hypotheses (provenance ledger). The pattern is proven but un-generalized.
- The git link is weak: audit_log.commit_sha is set only by writers who set the `audit.commit` GUC (ship-closures), null otherwise; asof.sh otherwise correlates by committer TIMESTAMP within ~a minute — explicitly heuristic, not attributable. No FK to a real commit table.
- No first-class Claude Code SESSION entity. actor is just a free-text application_name string ('coordinator', 'unknown'); there is no row linking a change → the session that produced it → the hypothesis/interpretation → a benchmark result. This is exactly the maintainer's stated non-attribution gap.
- The capability inventory is unverifiable prose in a gitignored file (services_local.gitignore). Nothing checks that listed services/venvs/Z3/OR-Tools are actually present and usable; 'assume these are up' is policy enforced by attention, the failure mode ADR-0011 §Context names as structurally weak.
- Invariant logic is confined to one VIEW per store and to Postgres-native graph recursion; there is no non-classical / external solver (Z3, OR-Tools) hook — provable results the maintainer wants are not yet wired into the gate.
- Audit reseed creates a genuine history discontinuity (DROP TABLE fires no DELETE triggers); time-travel across a reseed boundary is approximate, mitigated only by genesis-snapshot baselining.
- The violations view is the only place cross-row rules live; there is no registry OF the invariants themselves (each rule is hand-written SQL UNION ALL arms) — adding a rule means editing the view, not registering a fact.

## Harness hooks (where a registry / ledger / logic-gate plugs in)

- Generalize work_status_violations into a per-store violations VIEW convention: every harness DB (capability registry, provenance ledger) exposes a `*_violations` view; one uniform gate `SELECT * FROM <store>_violations` empty ⇒ clean. This is the ADR-0011 safety-net primitive.
- Promote audit_log into the provenance ledger: replace free-text actor with a sessions table (claude_code session id, model, start/end) and make commit_sha a FK to a commits table; add hypothesis/interpretation/benchmark_result tables with FKs so a bug row can be joined back to the session+commit that introduced it (closes the non-attributable git-hash↔perf gap).
- Reuse table_asof()/asof.sh as the ledger's temporal query layer, but strengthen the git link: have ship/commit writers always set the `audit.commit` GUC (or a commit-hook that inserts the commit row) so attribution is exact, not timestamp-heuristic.
- Turn services_local.gitignore into a CAPABILITY REGISTRY table set (services, venvs, tools incl. Z3/OR-Tools, addresses) seeded from a single source, with a `capability_violations` view + a liveness self-certify probe (mirror migrate-to-pg.py's self-certification: a tool that pings each service/imports each venv package and fails loudly if a registered capability is absent).
- Adopt the migrate-to-pg.py self-certify pattern as the harness's 'faithful image' contract for every store: counts + violations + round-trip reconstruction, non-zero exit on divergence.
- Add an external-solver hook to the violations layer: for invariants beyond SQL recursion (scheduling/feasibility/proof obligations), let a view emit obligations that a Z3/OR-Tools checker discharges, writing PROVABLE pass/fail back as ledger rows — wiring the neglected OR/automated-reasoning tools into the gate.
- Register invariants as data: a table of named rules (id, description, owning-ADR, severity) that the violations view references, so adding a rule is a registered, attributable fact (mirrors the inline 'enum amended, maintainer-approved, cite the audit' discipline at schema.sql:83-86).

## Anchors (attribution)

| Claim | Where |
|---|---|
| SQL store replaced hand-edited JSON as anti-corruption layer; no file to edit by hand; gate is SELECT * FROM work_status_violations | `/home/bork/w/omega/services_local.gitignore (Network services table, Postgres work-status/todo row)` |
| Within-row contract: amendable enums as CHECK IN, regex id, open/closed state-shape allOf, self-ref guards | `/home/bork/w/omega/tools/work-status/schema.sql:45-71` |
| work_status_violations view encodes shipped-without-ship-ref + depends_on-cycle + parent-cycle via WITH RECURSIVE CYCLE | `/home/bork/w/omega/tools/work-status/schema.sql:99-128` |
| Audit layer: audit_log with actor=application_name, commit_sha=GUC audit.commit, record_audit() triggers on all tables | `/home/bork/w/omega/tools/work-status/schema.sql:159-201` |
| table_asof(tbl,t) reconstructs last non-DELETE state at-or-before t via DISTINCT ON row_key | `/home/bork/w/omega/tools/work-status/schema.sql:207-213` |
| asof.sh resolves git-sha to committer timestamp (heuristic ~1min correlation), exact anchors only in audit_log.commit_sha | `/home/bork/w/omega/tools/work-status/asof.sh:9-24` |
| Self-certifying migrator: counts, violations view, field-for-field round-trip, non-zero exit on mismatch; genesis re-baseline | `/home/bork/w/omega/tools/work-status/migrate-to-pg.py:120-162` |
| Enum amended deliberately with attribution (refs.kind 'audit' added 2026-06-10, maintainer-approved, cites audit) | `/home/bork/w/omega/tools/work-status/schema.sql:83-86` |
| ADR-0011 north star: characteristic failure mode is invisible-at-authoring defect; only mechanical nets help, not attention/memory | `/home/bork/w/omega/docs/adr/0011-mechanization-discipline.md §Context` |


---
*Generated by the `claude-harness-understand` workflow (run `wf_64eb31fd-6c9`, model claude-opus-4-8[1m]), 2026-06-27. Reader findings are structured agent output, verbatim. Anchors cite `file:line/section` in the source projects.*
