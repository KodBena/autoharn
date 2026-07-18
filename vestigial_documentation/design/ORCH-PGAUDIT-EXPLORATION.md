# pgAudit for autoharn — a design-space exploration

Audience: maintainer (and the orchestrator relaying to him)

**Status: design-space exploration. No mandatory ratification attached; nothing here binds.
Read at leisure.** Commissioned as tracker work item `pgaudit-exploration` (`./led show 281`
prints the commission — "the tracker" throughout this document means autoharn's append-only
Postgres decision ledger, database `toy` on host `192.168.122.1`, read via the `./led` and
`./pickup` verbs). The maintainer named three reasons to look at pgAudit, in his priority
order, and this document takes them in that order: (1) audit-of-reads over the tracker,
(2) mining the SQL agents actually issue to factor recurring patterns into scripted verbs,
(3) database performance observability. Each section states what was verified against the
live host or the extension's own documentation, what is a design sketch, and what remains
unexercised. **Nothing was installed, configured, or enabled during this investigation** —
the host probes below are read-only `SHOW`/catalog SELECTs, and every configuration fragment
in this document is a proposal requiring the maintainer's hand (the standing
config-fragments rule applies: final `postgresql.conf`/`pg_hba.conf` lines are authored
against the live file on his host, never from memory or from this document).

## What pgAudit is, verified against its own documentation

pgAudit is a PostgreSQL extension that emits detailed audit log entries for SQL statements
into the server's standard log stream. All claims in this subsection were read from the
extension's README on the branch matching this host's PostgreSQL major version —
`REL_18_STABLE`, i.e. pgAudit 18.x for PostgreSQL 18
(fetched 2026-07-13: <https://github.com/pgaudit/pgaudit/blob/REL_18_STABLE/README.md>;
the project "maintains a separate branch for each PostgreSQL major version (currently
PostgreSQL 14 - 19)"). Version assumption, stated: the host runs PostgreSQL 18.4 (witnessed
below), so 18.x is the branch that would be installed; if the maintainer upgrades Postgres,
the pgAudit branch moves with it.

It has two modes, different in granularity:

- **Session audit logging** logs statements by *class*, per the `pgaudit.log` setting. The
  classes are `READ`, `WRITE`, `FUNCTION`, `ROLE`, `DDL`, `MISC`, `MISC_SET`, `ALL`; `READ`
  covers "SELECT and COPY when the source is a relation or a query." Because `pgaudit.log`
  is an ordinary configuration parameter, the README states it can be set "globally (in
  postgresql.conf or using ALTER SYSTEM ... SET), at the database level (using ALTER
  DATABASE ... SET), or at the role level (using ALTER ROLE ... SET)" — so the practical
  granularity is per-role and per-database, by statement class. Two caveats the README
  itself makes: "Settings may be modified only by a superuser," and settings "are not
  inherited through normal role inheritance and SET ROLE will not alter a user's pgAudit
  settings."
- **Object audit logging** logs statements touching a *particular relation*: a dedicated
  audit role is named in `pgaudit.role`, and "a relation will be audit logged when the
  audit role has permissions for the command executed" — grant the audit role SELECT on one
  table (even one column) and only reads of that table are logged. Only SELECT, INSERT,
  UPDATE, DELETE are supported in this mode; TRUNCATE is not.

Where the log lands: "the standard PostgreSQL logging facility" — the server log stream on
the database host, formatted per `log_line_prefix`. This single fact drives most of the
design consequences below.

What pgAudit **cannot** give, each point verified against the same README rather than taken
from the commission's list:

- **Statements, not result rows.** It logs statement text (optionally with bind parameters,
  `pgaudit.log_parameter`); it does not log what data came back. CONFIRMED — the README
  describes statement/parameter logging only, nowhere result sets.
- **Superusers are not reliably auditable.** CONFIRMED, verbatim: "It is not possible to
  reliably audit superusers with pgAudit." A superuser can also simply alter or unset the
  logging settings (they are superuser-modifiable by design, per the settings rule above).
- **Best-effort, not transactional.** CONFIRMED, and stronger than the commission's list:
  "Audit logging is best-effort and not transactional... no guarantee that a committed
  transaction will have a corresponding audit log entry." Also: a logged statement may
  belong to a transaction that later rolled back, and statements executed after a
  transaction enters an aborted state are not logged at all.
- **Log rotation loses history — via core Postgres, not pgAudit.** The pgAudit README says
  nothing about rotation or retention. But because entries land in the standard server log,
  core PostgreSQL's `log_rotation_age`/`log_rotation_size`/`log_truncate_on_rotation`
  behavior governs them; retention is entirely the host operator's log-management posture.
  So the commission's concern stands, with the mechanism correctly attributed.
- **Not logged at all:** autovacuum/autoanalyze activity, and (object mode) TRUNCATE.

## Host reality, witnessed 2026-07-13

Read-only probes against the tracker host (`psql -h 192.168.122.1 -d toy`, connecting as
the ambient `bork` user; no writes issued):

- `SELECT version()` → **PostgreSQL 18.4** on x86_64, Gentoo-built.
- `SHOW shared_preload_libraries` → **empty**. Neither pgAudit nor pg_stat_statements is
  preloaded today.
- `pg_available_extensions` → **pgAudit is not installed on the host** (no row); shipped
  but not activated: `pg_stat_statements` (default_version 1.12, installed_version empty)
  and `pgstattuple`.

Consequences: adopting pgAudit requires (a) installing the extension package on the Gentoo
host (or a PGXS build — PostgreSQL's standard extension-build makefile infrastructure —
against Postgres 18 dev headers, the README's documented build route), (b) adding it to `shared_preload_libraries` — which requires a **server restart**,
not a reload, and (c) `CREATE EXTENSION pgaudit`. All three are maintainer acts on his
machine. By contrast, `pg_stat_statements` needs only (b) and (c) — the module already
ships with his Postgres. This asymmetry matters for reason 2 below.

## Reason 1 — audit-of-reads over the tracker

### What it would buy

The tracker's existing integrity story is entirely **write-side**: append-only triggers,
HMAC stamps binding rows to invocations, the s26 row-hash chain, the s27 high-water
truncation tripwire (`kernel/lineage/s26-row-hash-chain.sql:6-19`,
`kernel/lineage/s27-chain-high-water.sql:8-24`). Nothing today records who *read* what.
pgAudit is the stock mechanism that adds exactly that: session mode with
`pgaudit.log = 'read'` scoped per-role logs every SELECT those roles issue, with statement
text; object mode with an audit role granted SELECT on the ledger relations narrows it to
reads *of the ledger specifically*.

The fit with the freeze-at-stamp design is real and was anticipated by the maintainer
before this investigation existed. Tracker rows 225/228/229 (`./led show 228`) record why
the frozen-snapshot database was moved out of `toy` into a standing dedicated
`autoharn_test` database with an owner/read-only role split: "if read-access tracking into
the db is ever instrumented, experiment/probe reads against a same-database copy would
contaminate the live db's read-access record... isolation is about the OBSERVATION SURFACE,
not only the data" (row 228), and the two-role split is "load-bearing for his read-tracking
motive: provisioning reads vs experiment reads distinguishable by ROLE as well as database"
(row 229). pgAudit's granularity matches that design point-for-point: per-database and
per-role setting scope means the live tracker's roles can carry `pgaudit.log = 'read'`
while `autoharn_test` roles carry nothing (or vice versa), and every emitted line is
attributable to its database and role via `log_line_prefix`. Row 228's honest residual also
stands unchanged: the *log stream itself* is one shared, cluster-wide surface — separation
of observation records is by filtering on database/role fields within one file, not
physical separation. That was named and accepted in row 228 and is not re-litigated here.

One concretely valuable use this project has *today*: probe hygiene. The
registry-completeness-audit commission (row 249) prescribes a blind-context runner working
from a freeze-at-stamp snapshot with probe-adjacent tracker rows scrubbed from its view. A
read log on the live tracker roles would let the orchestrator check, after the fact, that
the blind runner's session issued no reads against the live ledger — turning "the probe was
blind" from an assertion about setup into a checkable claim. Honest limits on that claim,
from pgAudit's own caveats: absence of a log line is best-effort negative evidence
(non-transactional logging, superuser exemption), so this is **tripwire-grade, not a
trust root** — deliberately the same vocabulary the s27 delta uses about its own witness
(`kernel/lineage/s27-chain-high-water.sql:30-35`).

### The log as an evidence surface outside the ledger

This is the design point that most deserves the maintainer's attention, because it cuts
against the adoption reflex. Everything the project currently treats as evidence lives in
one of two places: the ledger (append-only, stamped, hash-chained, truncation-witnessed) or
committed artifacts. A pgAudit log is a third surface with **none of those properties**:

- It is a text file on the database host, writable by root and by the postgres OS user;
  no trigger refuses edits, no hash chain detects them, no high-water witness detects
  truncation. The s26/s27 tamper-evidence story covers the ledger table only.
- The database superuser — the very actor the s26 header names as the adversary the hash
  chain exists to catch (`kernel/lineage/s26-row-hash-chain.sql:11-14`) — can disable or
  reconfigure pgAudit logging at will, and pgAudit documents superusers as not reliably
  auditable. So the read log is *weaker* against precisely the adversary class the
  ledger's own machinery is hardened against.
- Rotation ages it out unless the host's retention policy says otherwise.

The project's standing principle already has a name for this tier: the
action-stream-is-evidentiary-basis ruling (a maintainer principle of 2026-07-11, carried
in the orchestrator's operating memory rather than as a committed standing document — a
reader who wants its exact wording currently has nowhere committed to land, said plainly)
holds that guarantees rest on the hook-observed action stream, while `~/.claude` internals
and similar surfaces are *diagnostics*. A pgAudit read log belongs on the diagnostics side of
that line: genuinely useful for RCA, probe hygiene checks, and pattern mining — never a
surface a guarantee is allowed to rest on, unless the maintainer someday chooses to anchor
it separately (e.g. shipping log segments through the same external-custody route as the
GPG-signed chain head, `design/MAINT-GPG-TRUST-LAYER.md`). This document recommends
adopting that classification explicitly if pgAudit is adopted at all, so no future reader
mistakes the read log for a ledger-grade record. Who audits the audit log is then a
question with a stated answer: nobody, mechanically; it is diagnostics, and it is read when
a question arises.

### Against the registry-completeness criterion (row 249)

Row 249 pre-registers a success criterion for the NIST SP 800-53 audit: the AU (Audit and
Accountability) control family must surface audit-of-reads by construction. Assessed
honestly: **pgAudit operationalizes the *generation* half of an audit-of-reads posture and
only that.** In AU terms it produces the event records (which events, what content, per
role/relation — the AU-2/AU-3-shaped territory of *what is logged and with what detail*).
It does nothing for protection of audit information against tampering (AU-9 territory —
see the previous subsection: the log is the *least* protected artifact in the system),
nothing for retention (AU-11 — rotation is the opposite), and nothing for review/analysis
(AU-6 — someone or something must actually read the log; reason 2's scanner is the only
candidate consumer sketched anywhere). Control-number mapping is deliberately left to the
registry-completeness-audit item itself, which will enumerate from NIST's own OSCAL
catalog — the Open Security Controls Assessment Language, NIST's machine-readable control
catalog format (its commission's method, row 249) — this document only answers the cross-read question it
was asked: pgAudit is a real mechanism for one slice of the AU family, not a checkbox that
discharges it. Claiming "AU: covered" on the strength of pgAudit alone would be exactly the
gesture the commission warned against.

### What adopting it would look like (proposal shapes, not final lines)

Marked plainly: **every fragment below is illustrative shape only, requiring the
maintainer's hand.** The standing config-fragments rule governs — final lines are authored
against the live `postgresql.conf`/`pg_hba.conf` on his host, in its ordering and idiom,
never copied from this document. Installation and configuration of the extension is a
maintainer act (the commission says so; so does the hard constraint this investigation ran
under).

1. Install the pgAudit package for PostgreSQL 18 on the Gentoo host (package availability
   on Gentoo was not verified by this investigation — UNEXERCISED; the PGXS build from
   `REL_18_STABLE` is the documented fallback).
2. `shared_preload_libraries = 'pgaudit'` (shape only; the live file currently has the
   setting empty, so this is an addition, and it takes a server **restart**).
3. `CREATE EXTENSION pgaudit;` in `toy` (the README requires the extension to exist before
   `pgaudit.log` is set).
4. Scope, per-role rather than global — the shape that matches row 229's role split:
   `ALTER ROLE autoharn_rw SET pgaudit.log = 'read';` (and per his choice, the same on
   `autoharn_test_ro`/`autoharn_test_owner`, or deliberately not, to keep experiment reads
   dark). Global `pgaudit.log = 'all'` is *not* proposed: the verbs are chatty (every
   `./pickup` issues several SELECTs), and an unscoped read log would be mostly verb noise.
   `pgaudit.log_statement_once = on` is the README's own volume reducer if volume becomes
   a problem.
5. If per-relation focus is wanted later: an object-mode audit role granted SELECT on the
   ledger relations only.

Whether the project *wants* this at all is the maintainer's open question (his own framing
in the commission: "which the project may or may not want"). The honest trade: real
diagnostics and probe-hygiene value, purchased with an extension install, a restart, log
volume on his host, and a third evidence surface that must be explicitly classified as
diagnostic-grade so it never silently competes with the ledger.

## Reason 2 — mining the audit log to factor common patterns into verbs

### The idea, grounded in a live specimen

The house self-application rule ([CLAUDE.md](../../CLAUDE.md), ORCHESTRATION section) forbids
hand-pasted SQL where a scripted, witnessed verb is possible. The live specimen is tracker row 265 (2026-07-13):
the orchestrator itself ran raw psql SELECTs against the tracker — out of lane even
read-side — and the correction was registered on the record. A statement-level audit log is
an *empirical* answer to "which raw SQL keeps recurring and should become a verb":
instead of noticing lane violations one at a time, mine the workload.

### The minimal loop, sketched

1. **Capture.** pgAudit session logging (`read`+`write` classes) on the agent-facing roles
   produces log lines carrying full statement text, role, database, timestamp.
2. **Normalize.** Collapse statements to shapes: strip literals/parameters so
   `SELECT * FROM ledger WHERE id = 214` and `... = 907` are one shape. pgAudit does not
   do this — it logs raw text, so normalization is the miner's job (a small parser, or
   Postgres's own `queryid` machinery via pg_stat_statements — next subsection).
3. **Count and rank.** Frequency per shape, split by role (verb-issued vs raw), with the
   verbs' own known statements allow-listed out so the residue is exactly the ad-hoc SQL.
4. **Candidate list.** Shapes above a recurrence threshold become tracker findings:
   "this SELECT shape was issued N times raw; candidate verb or view."

Who runs it: a Haiku-tier scanner is plausible for steps 2–4 — the input after
normalization is discrete and small, exactly the "formal substrate a small model can read"
that the concurrent kr-titration-design-exploration item (rows 266/268) is exploring for
ledger *content*. The two items connect without overlapping: kr-titration asks how to make
the ledger's *information* discrete enough for a small reader; this loop asks the same
question about the *query workload*. If kr-titration lands a packet idiom, mined statement
shapes are an obvious additional packet kind. The one real access-path constraint: the
pgAudit log lives on the database host's filesystem, **outside** every existing verb's
reach (the verbs speak SQL over a connection; none reads server logs). A log-reading
scanner therefore needs either a host-side step (maintainer's machine, his call) or a
db-readable capture path — which is an argument for the next subsection's alternative.

### The cheaper first instrument: pg_stat_statements

For frequency-of-shape mining specifically, `pg_stat_statements` already does steps 2–3
in-database: it normalizes statements (constants replaced) and keeps per-(role, database,
queryid) call counts, queryable over an ordinary connection — no log parsing, no host-side
access, and the module already ships with the host's Postgres (witnessed above; only
preload + `CREATE EXTENSION` missing). Its known weaknesses are already on this project's
record: the engine-panel refutation (`judgment/engine/engine-panel/refute-architecture.md:32-34`)
documents that it keeps cumulative aggregates — no percentiles, no per-session attribution,
counters shared across everything in the database. For *performance* claims that was a
disqualifying flaw. For *pattern mining* it is mostly harmless: the miner wants "which
shapes recur, issued by which role," and per-role split plus counts is exactly what the
view provides. What pg_stat_statements cannot give the miner and pgAudit can: per-session
*sequences* (which shapes co-occur in one session — the signal for "these two queries are
always run together and should be one view") and exact literal values. So the honest
ordering is: **pg_stat_statements first** (lower cost, no new package, answers the
frequency question), **pgAudit if and when sequence/co-occurrence analysis earns its
install**. Both still require the maintainer's preload change and restart.

### Calibration: would mining have discovered the views the kernel already ships?

The commission asks this as a test of the idea. The kernel's derived views and the
recurring raw query each one replaced (view list enumerated from `kernel/lineage/`
grep, witnessed 2026-07-13; the pre-view query shapes are reconstructions, since no
audit log existed to mine — the whole point of this calibration being a thought
experiment, marked UNEXERCISED as a measured claim). The table below names each existing
view and the raw-SQL shape whose recurrence mining would have had to flag for the
"discovery" to count:

| Existing kernel view | The recurring raw shape it factored away |
|---|---|
| `ledger_current` | latest-per-supersession-chain filtering repeated in every read query |
| `countersigned_in_force` | join of decisions against countersigning reviews, re-derived per reader |
| `review_gap` | obligations LEFT JOIN reviews WHERE unmet — the standing "what's undischarged" question |
| `question_status` | per-question latest-answer aggregation |
| `review_stamp_distinctness` | pairwise stamp-field comparison between review and regarded row |
| `work_item_current` | latest work event per slug (GROUP BY slug, max id) |
| `work_item_violations` | cross-check of work rows against declared dependencies |
| `work_item_descendants` | recursive walk of the parent edge |

The plausible verdict, honestly split: shapes like `work_item_current` and
`question_status` (simple recurring aggregations any session reading work state must
issue) would almost certainly surface in a frequency-ranked shape list — these are the
same query typed many times. Shapes like `review_stamp_distinctness` would likely *not*:
that view exists because a kernel *correctness rule* (s21's pair-keyed distinctness,
`kernel/lineage/s21-session-aware-distinctness.sql`) needed one home, not because readers
kept typing its query. So mining is a real
discovery instrument for **convenience views** (the reason-2 goal: stop agents
reinventing wheels) and no substitute for **rule-bearing views**, which come from the
law, not the workload. That boundary is worth keeping if the loop is ever built: a mined
candidate becomes a *convenience* view or verb; anything semantics-bearing still routes
through the birth chain as a ratified delta ([CLAUDE.md](../../CLAUDE.md), ORCHESTRATION
section, class-ratified fail-safe deltas).

## Reason 3 — database performance (short, per the commission)

pgAudit offers approximately nothing here: it records *that* statements ran, with no
timings, no counts, no I/O statistics — it is an audit tool, and its README never claims
otherwise. Performance observability on this host is `pg_stat_statements`' territory
(timings, calls, block stats per normalized statement), with the limits the project
already documented when it refuted the engine-panel's latency-budget leg: cumulative
means only, no tails, no per-session attribution
(`judgment/engine/engine-panel/refute-architecture.md:32-34`). At the tracker's actual
scale (row IDs in the low hundreds after weeks of work) there is no live performance
question; if one appears, pg_stat_statements — not pgAudit — is the first instrument,
and it is already sitting on the host waiting for a preload line. That is the whole of
reason 3.

## Recommendation and staged adoption path

Stated as ideas for the maintainer to weigh, not directives:

- **Stage 0 (decide the posture, no install).** The load-bearing question is reason 1's:
  does the project want read-tracking on the tracker at all? This document's contribution
  to that decision: yes-shaped value exists (probe hygiene for row-249-style blind runs;
  diagnostics), but only if the read log is explicitly classified diagnostic-grade/
  tripwire-grade — it must never be presented as part of the ledger's tamper-evidence
  story, because it is weaker than the ledger against exactly the adversary that story
  names.
- **Stage 1 (one preload change, no new package).** If reason 2 or 3 is wanted first:
  enable `pg_stat_statements` — already shipped with his Postgres, needs only the preload
  line and `CREATE EXTENSION`, and answers the pattern-frequency question a Haiku-tier
  scanner would consume. A `led`-style read-only verb over its view keeps the mining
  in-lane (no raw psql, no host-side log access).
- **Stage 2 (pgAudit proper).** If the maintainer wants audit-of-reads: install pgAudit
  18.x, preload it, and scope `pgaudit.log = 'read'` per-role per the shape sketched in
  reason 1 — authored against his live config, by him. Object-mode narrowing to the ledger
  relations is available later without re-architecture.
- **Either way:** the registry-completeness audit (row 249) should treat pgAudit as
  evidence for the *generation* slice of AU and cite this document's honest scoping rather
  than marking the family discharged.

## Witness summary

- WITNESSED: host version 18.4, empty `shared_preload_libraries`, pgAudit absent /
  pg_stat_statements present-but-inactive (read-only psql probes, 2026-07-13, output
  quoted in "Host reality").
- WITNESSED: pgAudit behavior claims — all fetched 2026-07-13 from the `REL_18_STABLE`
  README (URL above); quoted phrases are verbatim from it.
- WITNESSED: tracker rows 225/228/229/249/265/266/281 read via `./led show` this session.
- UNEXERCISED: any actual pgAudit log output (nothing installed — hard constraint);
  Gentoo package availability for pgAudit; the calibration table's "mining would have
  found X" claims (thought experiment by construction, no log exists to mine); Haiku-tier
  scanner feasibility (design sketch only).

## License

Public Domain (The Unlicense).
