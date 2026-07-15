# WORK-STATUS-OFFERING — the omega work-status question, closed as a product

<!-- doc-attest-exempt: v1.1.2 release-cut mechanical edit (de-linked dangling references into paths excluded from this public cut -- observatory/, research/foundational-map/, design/MAINT-PG-HBA-HARDENING.md -- plain-text citation, no prose rewrite), same disposition as the v1.0/v1.1 cuts' own markers on their touched files. Removal condition: strike this marker and run the real A:B:C loop next time this file is touched for content, not just link repair. -->

Audience: adopter

This document answers a question this project has opened and re-closed at least three times
without ever shipping an answer: "how does a project track its own open work?" It describes a
new, project-agnostic tool — `bootstrap/track-work.sh` — that gives any directory a
standing, Postgres-backed work tracker in one command, explains how to adopt it, and states
plainly what BACKLOG.md is and is not from this point on. It is for whoever next asks "didn't we
already solve this?" (the maintainer's own framing, this commission) — the answer is now "yes,
here", with a link, not a re-litigation.

## The question this closes

The maintainer's framing, near-verbatim, is the charter this document discharges: work-status
tracking is "a perpetual need in all projects... of which autoharn is among one of 1-epsilon
fraction of projects, for some epsilon approaching 0." Despite that near-universal need, this
project had litigated the question at least three times (closed by the mapping table in
"The three litigations, closed by this table" below; the citation trail for the "three times"
claim itself is in "Provenance: verifying the 'three times' claim") and
left it, in the maintainer's words, "as nebulous as ever" while "abusing a 2k+ line BACKLOG.md as
a work tracker." A single append-only prose file cannot answer "what is open, what is blocked,
what is done" without a human reading it end to end — the same anti-corruption-layer problem
omega (internal research note, not part of this public release)'s
`work-status` Postgres store solved for hand-edited JSON, unsolved here for hand-edited BACKLOG
prose. This document's job is to end that gap, not describe it further.

## What the offering is

`bootstrap/track-work.sh` is a new scaffold entry point (deliberately separate from
[`bootstrap/new-project.sh`](../bootstrap/new-project.sh) — see "Standing vs world" below)
that gives **any directory** — not just an autoharn-governed world — a standing work tracker:

- applies this repo's full kernel lineage (the same chain a governed
  [world](../GLOSSARY.md#world) is born on) to a fresh Postgres schema pair named for the
  target project;
- writes `deployment.json` (the project's own name + where its ledger lives — the [SSOT](../GLOSSARY.md#ssot)
  [`filing/deployment_record.py`](../filing/deployment_record.py) already defines for every
  scaffolded instance) and the five operator verbs — `led` (write/read the ledger), `pickup`
  (live resume brief), `distance-to-clean` (composed closure-debt read), `judge` (the ASP/SQL
  differential verdict), and `audit` (contemporaneity check: does each row's record time match
  its actual event time) — as live shims — the
  same "a template fix here reaches every deployment instantly" mechanism a governed world's
  verbs already use;
- registers the three standard principals (`author`, `reviewer`, `commissioner`);
- wires **no hooks**. A standing project is not a [governed](../GLOSSARY.md#permit-to-work)
  world — none of the three hooks a governed world wires are present here: the change-gate
  (refuses a file edit with no open+claimed work item), stamp interception (HMAC-signs every
  ledger write), or Stop-gate (blocks a session from ending with outstanding review/work debt)
  — see the "hooks × kernel map" table in [OPERATING-CARD.md](../ORCH-OPERATING-CARD.md) for what
  each does when wired. Nor is there a CLAUDE.md governance preamble. Every row this
  deployment's `./led` writes lands **unstamped**
  (`stamp_agent`/`stamp_session`/`stamp_hmac` all `NULL`, `stamp_verified=false`) — visible in
  `./led --recent`, not hidden. This is the honest state of an unwired store: an unwired
  project produces unstamped-but-attributed rows, and that is a deliberate, documented choice,
  not a defect to route around (see "Why the full chain, unwired" below). Hook wiring — the
  step that turns a standing tracker into a governed world — remains a **separate, deliberate
  act**, done by copying `new-project.sh`'s own `.claude/` wiring stanzas by hand.

### Standing vs world

The distinction this offering exists to keep honest:

| | A **world** (`new-project.sh --new-world`) | A **standing deployment** (`track-work.sh`) |
|---|---|---|
| Lifetime | One [run](../GLOSSARY.md#run); settles into read-only evidence when a newer run supersedes it (the [runs-are-strictly-linear](../CLAUDE.md#orchestration--the-standing-delegation-contract-2026-07-09) ruling) | Indefinite — the same way an issue tracker never "expires" |
| Hooks | Wired: change-gate, stamp interception, Stop-gate | None — a separate, deliberate act if ever wanted |
| Governance preamble | `CLAUDE.md` auto-loaded at session start | None |
| Stamp secret | Provisioned | Not provisioned — nothing would read it |
| Purpose | A habitat for one governed Claude Code session | A perpetual work-tracking store for a project's whole life |

### Why the full chain, unwired

`track-work.sh` applies the identical birth chain a governed world gets — through
[`s25-commission-kind.sql`](../kernel/lineage/s25-commission-kind.sql) (the kernel delta adding
signed-commission rows, the newest step in the chain) — even though most of it (the stamp
mechanism, the independence vocabulary, commission signing) is inert without hooks. The
alternative — a trimmed "unwired"
kernel variant — would mean maintaining two kernel shapes for one mechanism
([ADR-0012](../law/adr/0012-compositional-and-structural-hygiene.md) P1: one home per fact), for
a capability that is dormant, not harmful, when unused. A project that later *does* wire hooks
gets the stamp/independence/commission machinery for free, with no second kernel apply.

### One-command adoption

Adopting the tracker in a fresh directory is one scaffold command followed by the same verbs
a governed world already uses, shown here end to end:

```sh
cd /path/to/autoharn
bootstrap/track-work.sh /path/to/your-project --name yourproject --db toy --host 192.168.122.1
cd /path/to/your-project
./led work open first-item "Describe the first thing to track"
./pickup            # live resume brief, including every open work item in full
```

Re-running the same command against an already-deployed directory is **refused** (a standing
deployment persists indefinitely; there is no "refresh" concept, mirroring the
runs-are-strictly-linear ruling's posture on worlds) unless `--force` is given — and `--force`
itself never re-runs kernel DDL against a schema that already carries it (a hazard found and
closed during this build; see `bootstrap/track-work.sh`'s own header comment and
`seen-red/track-work/red.txt` for the live, both-polarity proof).

## The three litigations, closed by this table

The maintainer named the pattern: this question keeps getting re-opened without a shipped
answer. The table below is that closure — every capability
omega's `work-status` store (internal research note, not part of this public release)
built, one row each, mapped to its home in this offering (built here, inherited from this
repo's existing kernel conventions, deliberately not ported, or genuinely new). Read this table,
not a re-derivation of the question, the next time "didn't we solve this already" comes up.

| Omega capability | Home in this offering | Disposition |
|---|---|---|
| SQL anti-corruption layer replacing a hand-edited file (no file to edit by hand) | `s22-work-item-ledger.sql`'s five ledger columns + derived views; this document's own BACKLOG-demotion statement generalizes the same move to autoharn's own BACKLOG.md | **Ported and generalized** — one mechanism now serves any project, not one hand-built store for one project |
| Relational image: parent `items` table + 3 child tables + `extra` jsonb junk drawer | **No new base table at all** — work state rides FIVE COLUMNS (`work_slug`, `work_title`, `work_depends_on`, `work_resolution`, `work_witness`) on the existing append-only `ledger` table | **Simplified, not ported 1:1** — the SSOT is the ledger itself; the `extra` jsonb forward-compat drawer is not carried (no witnessed need — the prudential rule this repo already applies to speculative columns, e.g. BACKLOG.md's dated entry "Omega work-tracking disposition (2026-07-11, night shift)": "build on witnessed need, not omega nostalgia") |
| Within-row contract: id regex, closed-but-amendable enums, open/closed state-shape CHECK | `work_slug_kind_shape` / `work_title_kind_shape` / `work_resolution_kind_shape` / `work_witness_kind_shape` / `work_resolution_check` CHECK constraints — construction-time refusal | **Ported and strengthened** — a CHECK constraint refuses an illegal row before it can exist even transiently, the loudest surface [ADR-0000](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) names, where omega's shape rule was itself already a CHECK but its cross-row rules lived only in a view |
| Deferred FK referential integrity (parent, superseded_by, deps.depends_on) | `validate_work_item()` trigger refuses a claim/depends/close row naming a slug with no opening act; a `work_depends_on` row's *antecedent* slug is deliberately **not** refused | **Partially ported, divergence named on purpose** — identity integrity (a typo'd own-slug) is refused at construction, stronger than an FK; a dangling *dependency* antecedent is surfaced, not refused (`work_item_violations.depends_on_unknown_slug`) — the s22 spec's own invariant 4 choice, carried forward here unchanged |
| Cheap self-reference CHECKs + `WITH RECURSIVE ... CYCLE` for longer cycles | `work_item_violations`'s `dependency_cycle` member, a recursive CTE reachability check | **Ported directly** |
| Cross-row invariant gate: `work_status_violations` VIEW, empty ⇒ CI-clean | `work_item_violations` VIEW (`duplicate_open`, `shipped_without_witness` — both provably vacuous defense-in-depth; `depends_on_unknown_slug`, `dependency_cycle` — genuinely reachable), wired into `./judge`'s exit code | **Ported and wired to a gate** — `./judge` now fails non-zero on a non-empty `work_item_violations`, the CI-gate analog omega's own tooling never had built in (a validator had to be run separately) |
| `audit_log` table + `record_audit()` trigger on every table, actor = free-text `application_name` | **Not ported as a separate table** — the append-only `ledger` table already IS the audit trail; every event is a permanent, timestamped row with no shadow table to keep in sync | **Structurally superseded** — s22's own header calls this "a strictly better answer" than a bolted-on audit log; actor attribution is a cryptographic HMAC stamp (`stamp_intercept`, when hooks are wired) rather than an unverified process name |
| `table_asof(tbl, t)` + `asof.sh` git-sha → committer-timestamp heuristic time-travel | `led work asof <timestamp>` — a pure `SELECT` over the append-only ledger, filtering to `ts <= <timestamp>` before picking each item's latest state | **Ported and strengthened** — a native timestamp comparison, not a ~1-minute heuristic correlation to a git commit's committer time |
| Audit-log reseed discontinuity (`DROP TABLE` fires no per-row `DELETE` trigger; needs `audit_genesis_snapshot()` to re-baseline) | N/A | **Does not apply** — there is no reseed concept for an append-only ledger; nothing is ever dropped or truncated, so the discontinuity omega had to work around cannot occur here |
| Migrator self-certification: row counts, violations view, field-for-field round-trip, non-zero exit on mismatch | N/A directly (no JSON file to migrate *from* — this store is the source of truth from its first write) | **Does not apply as a migration step**; the equivalent discipline for THIS offering is its own both-polarity seen-red proof (`seen-red/track-work/run_fixtures.py`) |
| Deliberate, attributed, dated enum amendment (e.g. `refs.kind` gaining a value, comment citing the audit that found the gap) | Inherited wholesale from this repo's kernel/lineage convention — every `sNN` delta is a dated, attributed, reasoned record (see `kernel/lineage/README.md`) | **Inherited, not reinvented** |
| Tooling discipline: psycopg3 not psycopg2, `psql ON_ERROR_STOP=1`, parameterized statements | Inherited wholesale — every kernel apply and every `led`/`pickup`/`judge` invocation already follows this | **Inherited, not reinvented** |
| Hierarchy: `parent`/`superseded_by` linking items into a tree | **Not ported** | **Correctly dead weight** — this project's own omega-disposition finding (BACKLOG, 2026-07-11) found hierarchy "evidenced-away by flat run decompositions": autoharn's own work items never needed a tree |
| Disposition sub-states (`open` → several intermediate states before `closed`) | **Not ported** — `work_item_current.state` is `open`/`closed` only | **Correctly dead weight** — the same disposition finding: "33/33 omega items never left 'open'"; the sub-states were never exercised in three months of real use |
| `extra` jsonb forward-compat drawer | **Not ported** | **Correctly dead weight** — no witnessed need; JSON-schema forward-compat solves a problem this ledger-native design does not have |
| Capability inventory as prose (`services_local.gitignore`) | Out of scope | **Not this offering's job** — that is [Pillar 1](../GLOSSARY.md#pillar-1) (the Capability Registry), a distinct piece of the [metaproject](../GLOSSARY.md#metaproject) |
| *(new, not in omega)* An explicit **claim** verb, separating "opened" from "someone is actively working it" | `led work claim <slug>` | **New capability** — omega had no assignment state at all |
| *(new, not in omega)* One command stands up the whole mechanism for **any** project | `bootstrap/track-work.sh` | **New capability, and the actual closure** — omega was one hand-built store serving one project; this offering is the same mechanism made reusable, discharging the maintainer's "1-epsilon fraction of projects" framing directly |

## BACKLOG.md's charter, restated

Effective 2026-07-11 (the genesis `decision` row on this store, row 1, `schema=autoharn` on
`toy`@192.168.122.1): **BACKLOG.md is the findings JOURNAL — dated rulings, findings, and
dispositions, append-only, read chronologically — and is no longer the work TRACKER.** Open,
blocked, and closed work for the autoharn project itself lives in this standing deployment,
read via `./pickup` (live resume brief, every open item in full) and `./distance-to-clean`
(one command reporting how many review/question/work-item obligations are still outstanding,
and their ids) at the autoharn repository root. A reader asking "what is open
right now" runs `./pickup` there; a reader asking "what happened, and when, and why" reads
BACKLOG.md's dated tail. The two serve different questions and neither substitutes for the
other — exactly the split omega's own precedent already proved for one project, generalized
here to every project this offering serves.

## Provenance: verifying the "three times" claim

Referenced above ("The three litigations, closed by this table") as the pattern this document
closes; named here so a future reader can verify
the claim rather than take it on faith. The maintainer's own framing (this commission) states
the question was litigated "at least three times" and left "as nebulous as ever" — the
BACKLOG.md dated tail carries the record of each pass (search for "work-status",
"work tracking", and "omega" in its history); the most recent, `s22-work-item-ledger.sql`
itself (2026-07-09) plus the "Omega work-tracking disposition" entry (2026-07-11), is what this
document's mapping table above formalizes into a shippable product rather than a fourth
open question.

## Related

- [`bootstrap/track-work.sh`](../bootstrap/track-work.sh) — the offering itself; its own header
  comment carries the full usage contract and the standing-vs-world rationale in detail.
- [`kernel/lineage/s22-work-item-ledger.sql`](../kernel/lineage/s22-work-item-ledger.sql) — the
  work-item layer's own closure statement, invariant-by-invariant.
- omega's work-status precedent (internal research note, not part of this public release) —
  the source this offering generalizes.
- [`seen-red/track-work/`](../seen-red/track-work/) — both-polarity live proof (a refused
  re-run against an existing deployment; a clean adoption on a throwaway directory, torn down).
- [`OPERATING-CARD.md`](../ORCH-OPERATING-CARD.md) — the operator verbs (`led`, `pickup`,
  `distance-to-clean`, `judge`, `audit`) this offering reuses unchanged.
- [`GLOSSARY.md`](../GLOSSARY.md) — `world`, `run`, `ephemera`, and every other coined term this
  document links on first use.
