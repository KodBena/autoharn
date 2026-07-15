# ORCH-HARNESS-FAILURE-LEDGER — a structured store for autoharn's own harness failures

This document is written for the orchestrator (secondarily for the maintainer, and for any
builder who later implements or extends `stores/008_harness_failure_ledger.sql`). It designs a
new Postgres store, `harness_failure`, that gives autoharn's own harness misbehavior — a hook
that blocks wrongly, a scaffold default that surprises an operator — a structured, queryable home
instead of scattered free-text tracker rows and dated reports. The rest of this section states
the commission that asked for it and this store's ratification posture before going further.

**The commission.** autoharn's own tracker (the append-only ledger the `./led`/`./pickup` verbs
read and write, hereafter "the tracker" — distinct from the new `harness_failure` store this
document designs, which this document always names in full or as "the store") carries row 425:
`work_opened: harness-failure-ledger`, a maintainer directive dated 2026-07-13, verbatim in
substance: *"in the interest of IMPROVING AUTOHARN, start collecting failures like the
stop-breaker stall in an auxiliary schema, for projects that subscribe to it — default on, since
he is currently the project's only known user."* This document, the DDL it describes, and the
apply script that arms it are the deliverables the commission asks for.

**Status: design + shipped store, no mandatory ratification.** Unlike a kernel/lineage delta,
this store carries no maintainer ratification gate before it ships as structure — it is additive,
fail-safe (it enforces no new refusal on anyone), and the standing pattern
(`stores/001_research_ledger.sql`) shipped the same way. What it does NOT do on its own: it is
never applied to a live database by this commission — applying is the operator's/maintainer's own
typed-confirmation act, exactly as for 001 (see "Applying this store" below).

## What this document is, who it is for, and what it decides

A reader who has never seen this project's tracker or observatory reports should still be able to
follow this. autoharn is a harness — a set of Claude Code hooks, verbs (`led`/`judge`/`pickup`),
and gates that govern how agent sessions work inside a deployed project. Those mechanisms
themselves sometimes misbehave, teach badly, or surprise an operator — the concrete trigger for
this document was the "stop-breaker stall": a 3-strike circuit breaker meant to let a session exit
cleanly turned out to be keyed to the exact *set* of open work items rather than a monotonic
counter, so closing one item mid-session reset the breaker and cost the session two fresh Stop
blocks per unit of real progress (`work_opened: stop-breaker-progress-reset-defect`, ledger row
419 — "ENT TESTBED FINDING 5" below). The stall was witnessed live in `ent` (a subject deployment
this project's harness governs, used here as the audit testbed the appendix's backfill data comes
from — see the Appendix's preamble). Today, evidence like this lives scattered across
free-text ledger rows and dated observatory markdown reports (`observatory/ent/cycle-*.md`) — real
but unindexed: no single place answers "what harness mechanisms have misbehaved, across every
project that runs this harness, and what happened to each one." This document designs that place:
a Postgres schema (`harness_failure`, in the same standing `research` database
`stores/001_research_ledger.sql` uses), the record shape it holds, who writes to it and when, and
how a deployment opts in or out. The DDL itself is `stores/008_harness_failure_ledger.sql`; the
typed apply script is `bootstrap/apply-harness-failure-ledger.sh`. Both ship in this same commit;
scaffold wiring (making new deployments subscribe by default) is a separate concern addressed as a
**proposal**, not code, in this document's final section — the reason is stated there.

## Why `research`, not a new database (the placement argument)

The commission named `db research` as the default target and asked for a strong argument only if
another placement is better. None emerged. `research` already carries `core.project` and
`core.session` — the exact "which deployment, which session" spine a harness-failure record
needs (WHO/WHERE identity), built and proven by `stores/001_research_ledger.sql`. Reusing them
instead of re-deriving a parallel project/session registry is the single-source-of-truth
discipline this codebase's own law names first (ADR-0012 P1, "derive, don't duplicate" — and
ADR-0000 Rule 1 elevates exactly this to the design's starting question, not an afterthought).
A harness failure and a research finding are different KINDS of record (one is "this mechanism
misbehaved," the other is "this measurement supports this claim") — different tables, different
schema — but they share the same deployment/session identity, and `research` is already the
project's one standing home for "autoharn-external evidence about a project," per
`stores/001_research_ledger.sql`'s own framing: "chocofarm's throughput_lab and omega's perf work
are consumers that write here." A harness-failure record is exactly one more such consumer,
except the consumer is autoharn's own observatory practice rather than a project's benchmark
suite. A second database would duplicate `core.project`/`core.session` for no offsetting benefit
and would cost every future cross-store query (e.g. "which project's findings correlate with
which harness failures") a cross-database join Postgres does not do cleanly. Verdict: `harness_failure`
schema, `research` db, second auxiliary schema alongside `core`/`research` — no new database.

## The record shape

Worked from five ledger rows (the "ENT TESTBED FINDING" rows 351/353/354/362/419 — a real
harness defect each) and the `observatory/ent/cycle-001.md`/`cycle-002.md` lessons sections (the
same shape of evidence, generated by a read-only audit rather than a live session hitting the
defect itself). Every one of those nine records is worked through the schema in the Appendix
below, which is the proof the shape actually holds real evidence, not a shape invented in the
abstract.

The shape splits into two tables, mirroring the finding+disposition idiom this project's other
ledgers already use (`research.finding` + the derived `research.finding_confirmed`;
`stores/002_rationalization_ledger.sql`'s finding+disposition split, cited there as "the THIRD
consumer of the finding+disposition idiom"): **an immutable observation** (what happened, once)
and **an append-only disposition trail** (what became of it, which can change over time as an
open failure gets filed, fixed, or waved off). Splitting these two concerns is itself a
[type-driven-design](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md) answer (the
project's law that a defect's shape is fixed by choosing the right types first, not patched onto
one) to a concrete risk: without the split, "this record's summary" and
"this record's current status" would share one row, and an UPDATE meant only to move
`open → filed-as-item` would carry write access to the observation text too — exactly the kind
of accidental double-purpose column ADR-0012 P3 (no god-objects) flags. Two tables make the two
kinds of fact structurally distinct, the way `research.reading`/`research.finding` already do.

### `harness_failure.record` — one immutable row per observed failure

| column | type | notes |
|---|---|---|
| `record_id` | `bigint identity PK` | |
| `schema_version` | `text NOT NULL DEFAULT 'harness-failure/1'` | the schema-versioned envelope the commission asked for — see "Growing the envelope" below |
| `project_id` | `text NOT NULL REFERENCES core.project` | deployment identity — reuses `research`'s existing project registry (P1); a deployment must be registered (`INSERT INTO core.project ... ON CONFLICT DO NOTHING`, exactly as `stores/001_research_ledger.sql`'s own writers already do) before it can carry a harness-failure record |
| `observed_at` | `timestamptz NOT NULL` | when the failure was OBSERVED (writer-supplied, like `research.reading.observed_at` — distinct from `created_at`'s ingest-time stamp; `stores/001_research_ledger.sql`'s own header comment states it added this same field deliberately, having judged that deferring it would lose real information rather than merely defer a convenience) |
| `mechanism` | `text NOT NULL` | the harness surface involved — free text, not a closed CHECK vocabulary, because the mechanism set (`stop_clean_exit`, `change_gate`, `mutation_observer`, `pickup`, `new-project.sh`, …) grows as the harness grows and a closed list would need editing on every new hook; `filing/apparatus_registry.py`'s own live-derived mechanism set is the natural cross-check for a future report, not a DB constraint here |
| `event_class` | `text NOT NULL CHECK (event_class IN ('defect','friction','watch','teach-gap'))` | the four classes below |
| `evidence_kind` | `text NOT NULL CHECK (evidence_kind IN ('journal','ledger_row','git_commit'))` | which evidence pointer variant this record carries |
| `evidence_journal_file` | `text` | e.g. `.claude/logs/stop_clean_exit.journal.jsonl` (repo- or deployment-relative path) |
| `evidence_journal_line` | `integer` | the specific journal line/entry, when known |
| `evidence_ledger_row_id` | `bigint` | a `./led show <id>`-resolvable row id, in the DEPLOYMENT's own tracker (not `research`'s) |
| `evidence_git_commit` | `text` | a git hash, in the deployment's or autoharn's own tree |
| `summary` | `text NOT NULL` | free-text account of what happened |
| `session_id` | `text REFERENCES core.session` | who/what filed this record (an orchestrator session, an observatory-cycle session) |
| `git_commit` | `text` | the AUTOHARN checkout's own commit at observation time, when known (ties the record to the harness VERSION that produced the behavior — the same discipline `bootstrap/new-project.sh`'s `AUTOHARN_COMMIT` stamp already applies at birth) |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | ingest/ordering clock, DB-stamped by trigger — never the observation time (mirrors `research.reading`'s own `created_at`/`observed_at` split exactly) |

The table above lists this table's *columns*; one further constraint governs the table as a
whole, not any single column, so it is stated here in prose rather than as a table row: a `CHECK`
requires `evidence_kind`'s declared variant to carry its required field non-null (e.g.
`evidence_kind = 'journal'` requires `evidence_journal_file IS NOT NULL`) — a record cannot claim
an evidence kind with no pointer to show for it.

**Never a transcript.** The `evidence_*` columns deliberately have no "session transcript" or
"conversation excerpt" variant. This is not an oversight — it is the action-stream-is-evidentiary-
basis ruling, deposited on the tracker (row 296, 2026-07-13, recorded as "made by the maintainer
2026-07-11"): *"the harness's guarantees rest on the hook-observed action stream only;
`~/.claude` internals, session transcripts, token/cost accounting, and host-side logs … are
DIAGNOSTIC-GRADE, never guarantee surfaces."* A harness-failure record's evidence must be
something a fresh reader can independently re-open and check — a journal line, a ledger row, a git
commit — never a private transcript excerpt that vanishes with the session, and never anything
whose truth depends on trusting the filer's memory of a conversation.

**The four `event_class` values, worked against the nine backfill records** (full mapping in the
Appendix):

- **`defect`** — the harness mechanism did something structurally wrong (blocked incorrectly,
  silently swallowed a failure, mis-keyed a counter). The Appendix's backfill records for ledger
  rows 351, 354, and 419 (the tracker's own row numbers, not this document's finding numbering)
  are `defect`.
- **`friction`** — the mechanism worked as designed but cost real session time/confusion getting
  through it (per the 2026-07-11 auditability ruling's own vocabulary: "struggling agents are
  acceptable; classify, and only refuses-without-teaching is a defect class to fix" — a `friction`
  record is exactly one of the acceptable, classified struggles, kept for the record rather than
  silently absorbed). Finding 2 (the pg_hba/verify-chain gap) reads as `friction` at the reporting
  layer even though its *root cause* was fixed as a defect.
- **`watch`** — nothing has gone wrong yet, but a latent false-positive/failure-mode has been
  identified and is worth monitoring if a mode changes (e.g. `mutation_observer` promoted from
  `observe` to `enforce`). Cycle-001 lesson 1 and cycle-002 lesson 1 (the git-tracked-log and
  git-plumbing false-positive triggers) are `watch`.
- **`teach-gap`** — the mechanism behaved correctly and taught correctly in the moment, but the
  *documentation* around it has a gap an operator could trip on later (cycle-001 lesson 2, the
  stop-hook/wide-decomposition doc note; cycle-002 lesson 5, the audit-cycle-completion framing
  note). Distinct from `friction`: a `friction` record is about session cost paid IN THE MOMENT; a
  `teach-gap` record is about a DOCUMENTATION debt for the future, independent of whether anyone
  actually struggled this time.

### `harness_failure.disposition` — append-only disposition trail

| column | type | notes |
|---|---|---|
| `disposition_id` | `bigint identity PK` | id-is-order — the identity PK IS the record order, same convention `stores/002_rationalization_ledger.sql` states for its own disposition table |
| `record_id` | `bigint NOT NULL REFERENCES harness_failure.record` | |
| `disposition` | `text NOT NULL CHECK (disposition IN ('open','filed-as-item','fixed','wontfix'))` | |
| `tracker_item_slug` | `text` | the autoharn tracker item slug once filed — `CHECK (disposition = 'open' OR tracker_item_slug IS NOT NULL)`: any disposition past `open` must name the item that disposed it, so "fixed" or "wontfix" can never float free of a citable tracker row |
| `note` | `text` | free-text rationale for this disposition act |
| `session_id` | `text REFERENCES core.session` | who recorded this disposition |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | append-only, DB-stamped, immutable by trigger (same `freeze`/`stamp` pair as `research.reading`) |

A record's **current** disposition is the disposition row with the greatest `disposition_id` for
that `record_id` — never re-derived by any other ordering, and never a writable column on
`harness_failure.record` itself (that would reintroduce the god-object risk the split above
exists to avoid). A record with **no** disposition rows yet is implicitly `open` — inserting an
explicit `open` row at record-creation time is allowed but not required, exactly as
`research.finding`'s own `status` column defaults to `'provisional'` without a forced first write.

### The derived view: `harness_failure.open_records`

```sql
CREATE VIEW harness_failure.open_records AS
  SELECT r.*
    FROM harness_failure.record r
    LEFT JOIN LATERAL (
      SELECT d.disposition, d.tracker_item_slug
        FROM harness_failure.disposition d
       WHERE d.record_id = r.record_id
       ORDER BY d.disposition_id DESC
       LIMIT 1
    ) latest ON true
   WHERE latest.disposition IS NULL OR latest.disposition = 'open';
```

This is the mechanized "derived view for open-disposition records" the commission asked for —
DERIVED, never a writable flag, exactly the posture `research.finding_confirmed` already
established for this project's ledgers (a status is asserted by writing an append-only act; being
"currently open" is *computed* from the latest act, never asserted directly).

### Growing the envelope: `schema_version`

`schema_version` starts at `'harness-failure/1'` (mirroring the `doc-attestation/1` /
`doc-attestation/2` versioning convention `gates/doc_attestation_presence.py` and
`design/ORCH-SPEC-DOC-ATTESTATION-2.md` already use for the exact same problem — a JSON-shaped
envelope that needs to grow additive fields later without breaking readers of the old shape). A
future `harness-failure/2` widens the shape (a new evidence kind, a new event class) by adding
nullable columns and a new `schema_version` literal, never by silently repurposing an existing
column — the same "seams left for additive growth" discipline `stores/001_research_ledger.sql`'s
own closing comment states for `research.reading`.

## The write path: harvested or filed, never obligated

Two legitimate ways a record lands in `harness_failure.record`, per the commission's own framing:

1. **Harvested by an observatory cycle.** A recurring, read-only audit session (the
   `ent-observatory` series, `observatory/ent/cycle-*.md`) reads a subject deployment's action-stream
   surfaces — its tracker via read verbs, its `.claude/logs/*.journal.jsonl` files, its git state —
   and, where it identifies a NEW lesson (not a KNOWN-do-not-re-file recurrence), files a
   `harness_failure.record` row citing that evidence directly. This is the primary intended path:
   the observatory practice already exists and already produces exactly this shape of finding in
   prose; this store gives it a structured, queryable home instead of only a dated markdown file.
2. **Filed by the orchestrator at a seam.** When an orchestrating session hits a harness failure
   directly (the stop-breaker stall itself was discovered this way, live, in ent's own session —
   not by an observatory cycle after the fact), the orchestrator files the record at the natural
   seam (task completion, a merge, a retrospective) citing the ledger row or journal line that
   evidences it.

**A deployment's own session MAY file a record directly (nothing forbids it — the schema does not
check who the writer is beyond the `session_id`/`core.session` reference) but is never obligated
to.** No hook in this project's harness writes to `harness_failure` automatically, and this
design does not propose one: a governed session that hits friction is not made to stop and file a
DB row before it can continue — that would turn a diagnostic aid into another gate to fight
through, the opposite of what this store is for. Filing is something the orchestrator or an
observatory cycle does ON BEHALF OF a deployment's evidence, from outside the deployment's own
gated write path — consistent with the observatory series' own hard constraint (never write under
a live deployment's own tree; `observatory/ent/cycle-001.md`'s "strictly read-only against
~/ent" language) extended one step further: harvesting into `harness_failure` writes to
`research`, never to the subject deployment itself, so the read-only constraint on the SUBJECT
holds even while the harvest itself is, necessarily, a write — just to a different database
entirely.

**No writer script ships in this commit.** `stores/001_research_ledger.sql` shipped without
`filing/record_reading.py` in the same delivery (that writer helper exists today, but as a
distinct artifact) — the DDL and the apply script are this ticket's mechanized scope, matching
001's own precedent exactly. A future `filing/record_harness_failure.py`, mirroring
`filing/record_reading.py`'s CLI/env-var shape (`RL_PGHOST`/`RL_DB`-style overrides, the same
`research` db default), is the natural next artifact once an observatory cycle or orchestrator
seam needs to file its first LIVE record — named here as anticipated future work, not silently
assumed to already exist.

## The subscription model: default ON, apparatus-style opt-out

The maintainer's own framing is the whole requirement: **default ON**, because he is currently the
project's only known user, with an opt-out for a future adopter who does not want their project's
evidence harvested this way.

**Chosen: an `apparatus.json` mechanism entry, not a new scaffold flag.** This project already has
exactly the vocabulary for "a per-deployment, independently-switchable posture, readable live,
without a re-scaffold": every mechanism in `.claude/apparatus.json`'s `mechanisms` object is
switched `"off"` / `"observe"` / `"enforce"`, read live at invocation time
(`bootstrap/templates/APPARATUS.md`, "Unlike the OLD `assurance` block … every hook below reads
its own mode live"). A subscription to harness-failure harvesting is not a gate that blocks
anything — there is no "enforce" state to reach for, because nothing is refused — so it takes
exactly the same shape `doc_attestation` already uses in this file: a mechanism that only ever
occupies `"off"` or `"observe"` (never `"enforce"`), with `"observe"` as its default:

```json
"harness_failure_subscription": {
  "mode": "observe",
  "note": "Whether this deployment's evidence MAY be harvested into the standing harness_failure schema (db research) by an observatory cycle or orchestrator seam (design/ORCH-HARNESS-FAILURE-LEDGER.md). Spends nothing at runtime -- no hook reads this key on any tool call; it is read by whoever RUNS an observatory cycle, as a should-I-harvest-this-deployment check, exactly like doc_attestation gates distance-to-clean rather than a live hook. Default ON (the maintainer's own framing, 2026-07-13: he is currently the project's only known user) -- set 'off' to opt this deployment out."
}
```

Why this over a new `bootstrap/new-project.sh --harvest-failures[=off]` argument (the other
candidate the commission named): a scaffold flag is fixed at BIRTH — changing a deployment's mind
later requires either re-scaffolding (destructive, per this project's own `--force` semantics) or
hand-editing `deployment.json` in a way no other tooling reads. An `apparatus.json` entry is
already a live-read, no-re-scaffold-needed switch for every OTHER posture question this project
asks (see the mode-reading guarantee quoted above) — reusing it costs nothing new to explain to an
operator who already knows `apparatus.json`, and it is strictly lighter than teaching
`new-project.sh` a fifteenth argument for a decision an operator can and does revisit. It also
composes cleanly with the existing unknown-mechanism-name / unknown-mode-value hardening
(`gates/apparatus_unknown_keys.py`, `filing/apparatus_registry.py`'s live-derived mechanism set) —
a scaffold flag would need its own, separate validation path for the same never-widens-silently
guarantee apparatus.json already has.

**This key governs nothing that blocks a tool call.** No hook in this project's harness reads
`harness_failure_subscription` today (unlike `change_gate`/`clean_exit`, which fire on every
governed `Write`/`Edit`/`Stop`); it is read by whoever RUNS an observatory cycle or files a seam
record, as a should-I-harvest-this-deployment check before writing to `research`. This mirrors
`doc_attestation`'s own stated posture exactly ("Gates ONLY whether `./distance-to-clean`'s
DOC-ATTESTATION section counts debt … NOT a cost switch") — a declarative subscription flag, not
a runtime mechanism, and this document says so rather than implying a hook exists that does not.

## Scaffold wiring — a PROPOSAL, not code (and why)

The commission asked for scaffold wiring as a separate, reviewable commit, with an explicit escape
valve: *"if the wiring is more than ~20 lines or touches the birth chain, deliver it as a PROPOSAL
section in the design note instead of code and say so."* (See [GLOSSARY.md's "birth chain"
entry](../GLOSSARY.md#birth-chain) for what that names.) The wiring itself IS small — the
`harness_failure_subscription` block above, added once to `bootstrap/templates/apparatus.json`
(the file every scaffolded deployment's own `.claude/apparatus.json` is a straight `cp` of,
per `bootstrap/new-project.sh`'s own `cp "$TEMPLATES/apparatus.json" …` line) plus one new table
row in `bootstrap/templates/APPARATUS.md`'s mechanism table — well under the 20-line bar and it
touches no kernel/lineage birth-chain file. **But this builder's own commission explicitly lists
`bootstrap/templates/` among the paths NOT to touch** ("concurrent builder" work is happening
there right now). That constraint, not the line-count or birth-chain tests, is why this section
ships as a proposal rather than a diff: the wiring is ready to apply, but applying it here would
step on concurrent work this ticket was explicitly told to leave alone.

**Proposed diff, for whoever next has `bootstrap/templates/` open:**

1. In `bootstrap/templates/apparatus.json`, inside the `"mechanisms"` object, add:

   ```json
   "harness_failure_subscription": {
     "mode": "observe",
     "note": "Whether this deployment's evidence MAY be harvested into the standing harness_failure schema (db research) by an observatory cycle or orchestrator seam (design/ORCH-HARNESS-FAILURE-LEDGER.md). Spends nothing at runtime -- no hook reads this key on any tool call. Default ON (maintainer framing 2026-07-13: he is currently the project's only known user) -- set 'off' to opt this deployment out."
   }
   ```

2. In `bootstrap/templates/APPARATUS.md`'s mechanism table (whose existing header row reads
   `| mechanism | hook | default | why |`), add one row matching that same four-column shape:

   | mechanism | hook | default | why |
   |---|---|---|---|
   | `harness_failure_subscription` | *(no hook — read by observatory cycles / orchestrator seams, not a PreToolUse/PostToolUse hook)* | `observe` | default ON per the maintainer's own framing (2026-07-13); a declarative subscription flag, not a runtime mechanism, same posture as `doc_attestation` |

Both are additive-only (a new key, a new table row); neither relaxes any existing refusal or
changes any existing mechanism's behavior, so this is class-ratified as a fail-safe delta under
the maintainer's own 2026-07-09 ruling (CLAUDE.md, "Class-ratified fail-safe deltas") once whoever
owns `bootstrap/templates/` applies it — no separate maintainer question should be needed for
this specific two-line addition, though the concurrent-builder constraint is a scheduling
question, not a ratification one, and is exactly why it is left to that builder's own commit
rather than folded into this one.

## Applying this store

`stores/008_harness_failure_ledger.sql` and `bootstrap/apply-harness-failure-ledger.sh` clone
`stores/001_research_ledger.sql`/`bootstrap/apply-research-ledger.sh`'s pattern exactly: a
resolved-target print before anything runs, a typed database-name confirmation (no `--yes`, no
env-var bypass), `ON_ERROR_STOP=1`, the whole DDL transaction-wrapped (`BEGIN`…`COMMIT`) so a
mid-file failure rolls back cleanly, and a preflight that refuses loudly rather than hitting
"relation already exists" mid-transaction on a second run. Neither this document nor the DDL/apply
script applies anything to any database — the maintainer's own typed confirmation is the only
path from structure to a live schema, exactly as for 001.

## Appendix: backfill records, ready to INSERT (data, not DDL)

**This section is data, not structure.** Nothing here is applied by
`stores/008_harness_failure_ledger.sql` (which creates empty tables, like 001's own DDL); these
are the nine ready-to-INSERT records the commission asked for, one per distinct piece of evidence
already on the tracker or in `observatory/ent/`, for the orchestrator or maintainer to apply once
the store exists. Two observatory lessons (cycle-001's "governed-set default", cycle-002's
"verify-chain family") are explicitly marked KNOWN/reconfirmed in their own reports and are NOT
given separate rows below — they restate findings 4 and 2 respectively, and a duplicate row for
the same underlying fact would violate the very single-source-of-truth discipline this design
leans on elsewhere (ADR-0012 P1). Every `evidence_ledger_row_id`/`evidence_journal_file` cited
below is a real, independently-resolvable pointer (`./led show <id>` in the `ent` deployment's own
tracker, or a named journal file in `observatory/ent/cycle-*.md`'s own evidence), never a
transcript excerpt.

```sql
-- preamble: register the 'ent' deployment and an 'observatory' filing session, ON CONFLICT DO
-- NOTHING (mirrors stores/001_research_ledger.sql's own core.project/core.session seeding
-- convention -- these two INSERTs are idempotent and safe to run before every backfill batch).
INSERT INTO core.project (project_id, name) VALUES ('ent', 'ent (picom hardening testbed)')
  ON CONFLICT (project_id) DO NOTHING;
INSERT INTO core.session (session_id, project_id, summary)
  VALUES ('ent-observatory-backfill-2026-07-13', 'ent',
          'ent-observatory cycle-001/cycle-002 backfill into harness_failure, 2026-07-13')
  ON CONFLICT (session_id) DO NOTHING;

-- Finding 1 (ledger row 351): scaffold pre-flight gap on a pre-created subject role.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_ledger_row_id,
   summary, session_id)
VALUES
  ('ent', '2026-07-13T00:00:00Z', 'bootstrap/new-project.sh --new-world', 'defect',
   'ledger_row', 351,
   'new-project.sh --new-world run as the db-owner role fails at kernel/lineage/s15-schema.sql:93 (ALTER ROLE <subject> SET search_path) when the subject role was pre-created by the maintainer -- s15''s idempotent role-create is skipped and the connecting owner lacks CREATEROLE+ADMIN on a role it did not create. Candidate fix: pre-flight the privilege pair and refuse-with-teach-text before any DDL runs.',
   'ent-observatory-backfill-2026-07-13');

-- Finding 2 (ledger row 353): verify-chain (this project's mechanism that reports could-not-look
-- as its own honest outcome rather than confusing it with a checked-and-passed result) hitting its
-- CANNOT-VERIFY path (exit code 5) for the first time in production.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_ledger_row_id,
   summary, session_id)
VALUES
  ('ent', '2026-07-13T00:00:00Z', 'verify-chain (CANNOT-VERIFY path)', 'friction',
   'ledger_row', 353,
   'verify-chain''s CANNOT-VERIFY (exit 5) fired for the first time in production, hours after merging the error-conflation fix -- a pg_hba (Postgres''s host-based-authentication config file, which lists which OS users/hosts may connect as which db roles) connection refusal correctly reported as could-not-look, never as the benign pre-fix absence the old code would have claimed. Root cause: the ent pg_hba block admitted only the three ent roles, not the broad host-db-all pair this project''s house connection idiom needs; lines provided to the maintainer.',
   'ent-observatory-backfill-2026-07-13');

-- Finding 3 (ledger row 354): pickup silently reads as an empty tracker on connection failure.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_ledger_row_id,
   summary, session_id)
VALUES
  ('ent', '2026-07-13T00:00:00Z', 'pickup', 'defect',
   'ledger_row', 354,
   './pickup against an unreachable/unauthorized db exits 0 with empty sections and empty stderr -- a hydration brief indistinguishable from "tracker is empty" when the truth is "could not look". Same defect class as verify-chain-error-conflation, one verb over -- a fresh session that hydrates by reading the tracker via ./pickup rather than any prior transcript (this project''s resumption convention) would act on an EMPTY world-view. Fix shape: detect psql execution failure distinct from empty result, refuse loudly.',
   'ent-observatory-backfill-2026-07-13');

-- Finding 4 (ledger row 362): scaffold's governed_files.json default is wrong for non-Python projects.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_ledger_row_id,
   summary, session_id)
VALUES
  ('ent', '2026-07-13T00:00:00Z', 'bootstrap/new-project.sh (governed_files.json default)', 'defect',
   'ledger_row', 362,
   'The scaffold''s governed_files.json default is [''*.py''] -- correct for autoharn-shaped Python worlds, silently wrong for any other-language deployment: ent''s change gate governed zero C/GLSL/meson files while the taxonomies seeded into ent''s own tracker at provisioning time (its declared list of the project''s real review surfaces) declared exactly those surfaces. Fixed locally in ent (six patterns, ledgered there). Reconfirmed unchanged in observatory/ent/cycle-002.md ("KNOWN, re-confirmed -- do not re-file").',
   'ent-observatory-backfill-2026-07-13');

-- Finding 5 (ledger row 419): the stop-breaker signature-reset stall -- the commission's own trigger.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_journal_file,
   evidence_journal_line, summary, session_id)
VALUES
  ('ent', '2026-07-13T16:32:00Z', 'stop_clean_exit', 'defect',
   'journal', '.claude/logs/stop_clean_exit.journal.jsonl', NULL,
   'The 3-strike breaker is keyed to the debt SIGNATURE (exact open-item set), so when a wide decomposition CLOSES an item the signature changes and the breaker RESETS -- the session eats 2 fresh Stop blocks per unit of progress (witnessed: fail-open at count 4 at 16:18, item upstream-anchoring closed, then blocked/blocked/fail-open again 16:31:30-57). Fix shape: a signature change that is a strict SUBSET of the prior entry set (items only left, none added) inherits the open breaker state instead of resetting.',
   'ent-observatory-backfill-2026-07-13');

-- Cycle-001 lesson 1: git-tracked session logs are a latent mutation_observer false-positive source.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_journal_file,
   evidence_journal_line, summary, session_id)
VALUES
  ('ent', '2026-07-13T14:22:13Z', 'mutation_observer', 'watch',
   'journal', '.claude/logs/mutation_observer.journal.jsonl', 1,
   'picom/.claude/logs/invocations.jsonl is tracked in picom''s own git repo and churns on ordinary session activity -- handled correctly this cycle (observe mode, explicit diff exclusion) but a latent false-positive source if mutation_observer or any future "diff purity" gate is ever promoted to enforce without an exemption for scaffolding-owned logs living inside a governed tree.',
   'ent-observatory-backfill-2026-07-13');

-- Cycle-001 lesson 2: stop-hook/wide-decomposition tension deserves a doc line (teach-gap).
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_journal_file,
   evidence_journal_line, summary, session_id)
VALUES
  ('ent', '2026-07-13T15:09:52Z', 'stop_clean_exit', 'teach-gap',
   'journal', '.claude/logs/stop_clean_exit.journal.jsonl', 6,
   'A decomposition that intentionally opens many parallel work items for resumability will reliably run the clean_exit 3-strike breaker to exhaustion within one sustained session (2 blocks + 4 breaker_fail_open in ~13 minutes on an unchanged 17-item debt set here). The mechanism worked exactly as designed (fail-open, fully journaled, correct teach-text) -- but an operator seeing 4 breaker_fail_open lines in a row with no accompanying panic could reasonably wonder if the breaker is broken. A short doc note pre-empts that; no code change proposed.',
   'ent-observatory-backfill-2026-07-13');

-- Cycle-002 lesson 1: the false-positive class has a SECOND trigger -- git's own plumbing, not just tracked logs.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_journal_file,
   evidence_journal_line, summary, session_id)
VALUES
  ('ent', '2026-07-13T15:58:30Z', 'mutation_observer', 'watch',
   'journal', '.claude/logs/mutation_observer.journal.jsonl', 2,
   'Two new mutation_observer entries triggered by .git/objects/pack/* and FETCH_HEAD -- files git itself writes during ordinary remote add/fetch/background pack maintenance, not files the agent directly edited. If "diff purity"/"pristine-tree" enforcement is ever built on mutation_observer, it needs to tolerate BOTH classes of incidental writes (scaffolding-owned logs, per cycle-001 lesson 1, AND git''s own internal bookkeeping), not just the first one found.',
   'ent-observatory-backfill-2026-07-13');

-- Cycle-002 lesson 5: "audit cycle complete" needs a sub-phase qualifier in maintainer-facing framing.
INSERT INTO harness_failure.record
  (project_id, observed_at, mechanism, event_class, evidence_kind, evidence_ledger_row_id,
   summary, session_id)
VALUES
  ('ent', '2026-07-13T18:35:00Z', 'observatory reporting / commission framing', 'teach-gap',
   'ledger_row', 372,
   'This cycle''s own commission described the ent deployment''s "first audit cycle" as COMPLETED; the ledger''s own vocabulary distinguishes cycle-1a (FIND, actually complete per row 47) from cycle-1b (FIX, dispatched per row 52 but zero commits landed, zero harden-* items closed as of row 53). Not a harness bug -- the ledger is precise -- but an external status question answered from plain-English framing alone would have missed the distinction. No action item; noted so a future cycle report does not inherit the imprecise premise unchallenged.',
   'ent-observatory-backfill-2026-07-13');
```

## A:B:C attestation

Attested per the amended recipe (`design/ORCH-ABC-AUDIT-LOOP-RECIPE.md`): fresh forks both
rounds, table row/column labels walked as referents, the broadcast/inhabitation test applied to
every table above, verdicts printed as B's own final message (never routed via `SendMessage`),
round 2 a full fresh re-sweep rather than a finding-list check. Recorded via
`gates/doc_attestation_presence.py --record`; see `attestations/doc-legibility-attestations.jsonl`
for the record.

## Related

- [`stores/001_research_ledger.sql`](../stores/001_research_ledger.sql) — the pattern precedent
  this store's finding+disposition split, immutability triggers, and `observed_at`/`created_at`
  split are all derived from.
- [`stores/002_rationalization_ledger.sql`](../stores/002_rationalization_ledger.sql) — the
  finding+disposition idiom's other worked instance, cited above for the append-only-disposition
  shape.
- [`bootstrap/apply-research-ledger.sh`](../bootstrap/apply-research-ledger.sh) — the apply-script
  pattern `bootstrap/apply-harness-failure-ledger.sh` clones.
- [`observatory/ent/cycle-001.md`](../observatory/ent/cycle-001.md) and
  [`cycle-002.md`](../observatory/ent/cycle-002.md) — the evidence this schema was worked out
  against; the backfill appendix above transcribes their lessons into this store's shape.
- [`bootstrap/templates/APPARATUS.md`](../bootstrap/templates/APPARATUS.md) — the mode vocabulary
  (`off`/`observe`/`enforce`) the subscription flag above reuses rather than reinventing.
- [`law/adr/0000-the-alpha-and-the-omega-type-driven-design.md`](../law/adr/0000-the-alpha-and-the-omega-type-driven-design.md),
  [`0012-compositional-and-structural-hygiene.md`](../law/adr/0012-compositional-and-structural-hygiene.md) —
  the type-driven-design and P1/P3 principles this design's table split and `research`-db
  placement both answer to directly.
- Ledger row 296 — the action-stream-is-evidentiary-basis ruling this store's evidence-kind
  vocabulary (never a transcript variant) is built to honor.
