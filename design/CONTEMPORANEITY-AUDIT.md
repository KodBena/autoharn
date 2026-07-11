# Contemporaneity audit — per-invocation stamp token + a first-class correlation verb

This memo proposes a way to tell, mechanically, whether a ledger row's timestamp
reflects when the recorded event actually happened or whether the row was written later
in a batch — and a tool that reports the difference per row. It is written for the
maintainer and for the executor who builds from it.

STATUS: DESIGN MEMO (Fable-authored, 2026-07-11; the eventual kernel delta is
Sonnet-authored FROM this memo per the delegation contract, then scratch-witnessed).
Commissioned by the maintainer mid-run-8 (a [run](../GLOSSARY.md#run) is one governed
Claude Code session executing a task inside one [world](../GLOSSARY.md#world)),
near-verbatim: the ledger-vs-window batching "seems largely dishonestly disposed"; we
want a tool that runs the correlation first-class — "the DB actually records a token
specifically for this purpose" — not "Sonnet, please do the dirty work we should have
automated 11 runs ago". Of particular interest: time deltas between actual events and
recorded events.

## The evidence (read from run7's ledger, 2026-07-11; full row dump in the session record)

- **Run 7 phase 1 — the celebrated clean loop — batched exactly like run 5 did.**
  Rows 5-8 (work_opened) 0.02s apart; reviews 13-16 within 0.07s; all four
  work_claimed within 0.07s; all four work_closed within 0.11s at 23:26:47 — items the
  preamble orders closed "once delivered" were closed in one end-of-phase sweep.
- **Run 8 (same night, post-hydration): same signature.** 4 decisions in 0.07s, 4
  work_opened in 0.07s, 8 assumptions in 0.16s, reviewer countersigns in batches.
- Inter-burst gaps (35s / 48s / 134s / 250s) are where the actual work lived; the rows
  describe it retrospectively at burst boundaries.
- Row 62 is missing (sequence gap = refusal fingerprint, per run-5 forensics), and row
  63's own statement reports "Provenance defect found while filing this" — refusals and
  self-reported provenance defects are ALSO contemporaneity data an auditor should see.
- **The dishonest disposition, named:** run-5 finding 1 had two halves — no-permit and
  no-contemporaneity. [Permit-to-work](../GLOSSARY.md#permit-to-work) (item 18 of
  [CAPABILITIES.md](../CAPABILITIES.md)) fixed the first. That same document's "Honest
  limits" section then said "NOW FIXED" for the whole finding, and no run since has
  re-measured the second half. Amended same day as this memo.

## What the defect actually is (aim before building)

Some batching is irreducible: an LLM thinks, then emits N conclusions — four
simultaneous decompose-decisions logged 0.02s apart may be perfectly honest. The defect
is that the record CANNOT DISTINGUISH that from run 5's 19-rows-backfilled-in-0.43s:

1. `ts` is INSERT time masquerading as event time; nothing else exists.
2. Nothing binds a row to the tool invocation that wrote it, so "which command produced
   these rows, and when did that command run relative to the work it describes" is
   answerable only by hand-correlating transcripts — which is why it kept being done by
   ad-hoc agent passes (runs 5, 7, 8), i.e. not done at all between crises.

The fix is therefore NOT "forbid batching" (that demand would produce theatrical row
spacing — conduct faked to satisfy a shape-matcher; this repo's witnessed failure class
where a gate that pattern-matches known shapes is defeated by the next unknown one, see
[class-not-instance net](../GLOSSARY.md#class-not-instance-net)).
The fix is to make the batching structure VISIBLE, measured, and queryable, so honest
simultaneity and retroactive backfill stop being the same row shape.

## Part 1 — the per-invocation token (kernel delta, additive)

Mechanism: identical to how `stamp_session` works today, one register down.

- `hooks/stamp_intercept.py` already rewrites EVERY Bash command in a wired world to
  export the stamp GUCs via PGOPTIONS (matcherless, item 19). It additionally mints a
  per-invocation token: `stamp_invocation = <uuid>`, exported the same way, AND appends
  one line to a world-local journal (`.claude/logs/invocations.jsonl`): token, wall-clock
  at injection, session id, tool_use_id if the hook payload carries it, sha256 of the
  command text. The journal is the "actual event" side of the correlation; the hook is
  already the choke point every Bash call passes through.
- Kernel delta: a sixth stamp column `stamp_invocation` on the ledger, captured by the
  existing stamp trigger path exactly as `stamp_session` is; `ledger_current` /
  `countersigned_in_force` re-issued with the column (the s20 shape). No refusal
  relaxed, no semantics changed, columns+views only → the class-ratified fail-safe
  shape, pending the standing doubt-check: it touches the stamping machinery, so if the
  Sonnet-authored delta's review finds ANY existing-semantics wobble, it routes to the
  maintainer instead.
- Backward-honest: rows written before the delta have NULL stamp_invocation — visible
  as "pre-token era", never guessed.

## Part 2 — the correlation verb (`audit` — a fifth operator verb, or a judge subcommand)

Pure join of the two machine-recorded sides — ledger (token, ts, id sequence) against
the invocation journal (token, wall time, command hash) — plus the hook-journaled tool
activity that already exists (mutation-observer markers, change-gate journal). Reports,
per session:

1. **Burst table**: rows-per-invocation-token; N rows under one token = one command
   wrote N rows (generated script / led loop) — stated, not inferred from ts spacing.
2. **Silence/backfill table**: journaled tool-invocation timeline vs ledger-write
   timeline; every gap > threshold where tool activity ran with zero rows, and the burst
   that followed it (run 8's 5m12s/13-calls/0-rows becomes one table line, mechanically).
3. **Delta column**: for each row, ts minus its invocation's journaled wall time
   (sanity: near-zero always) and — the maintainer's asked-for number — the age of the
   PRECEDING journaled activity window at the moment the row describing it landed.
4. **Refusal fingerprints**: id-sequence gaps (burned ids), surfaced with the
   surrounding rows.
5. Closed verdict vocabulary, judge-style, so escalation is TYPED — e.g.
   `CONTEMPORANEOUS | BATCHED_DECLARED | BACKFILL_SUSPECT` per session — exact
   thresholds to be set from the first measured corpus (runs 5-8 give it), not guessed.

Observer-first: the verb reports; it gates nothing. Whether a BACKFILL_SUSPECT verdict
ever feeds the Stop gate is a later maintainer question, asked with measurements in hand.

## What this does NOT do (honest limits, day one)

- It cannot recover the true time of the JUDGMENT a row records — only the tool-event
  chain around the write. "When was this actually decided" stays unobservable; what
  becomes observable is "how long after the surrounding work did the record appear, and
  via how many commands".
- A subject could still front-load thinking and write honest-looking interleaved rows;
  the token makes the record's SHAPE honest, not the mind legible (the standing
  machine-observable-events-only limit).
- The invocation journal is world-local and hook-written; a session with hooks off
  (apparatus mode) produces no journal — the verb must report that absence loudly
  (UNJOURNALED ERA), never as "no findings".

## Part 2 implementation directive — the verdict logic is ASP, not SQL (added 2026-07-11)

The maintainer's standing framing binds here: this is a research project about deductive
engines and how they can be leveraged (design/possibly-addressable-concerns.md, including
its explicit warning against bending every problem into SQL). The audit verb is the best
showcase this repo has yet had, because its logic is genuinely deductive, not relational:

- The event stream becomes an EDB: `invocation(Token, T)` (from the journal),
  `row(Id, Token, Kind, T)` (from the ledger), `tool_event(Kind, T)` (from the hook
  journals — change-gate, mutation-observer marker, delegation journal).
- Verdicts are DERIVED: `batch(Token) :- N rows share Token` (one command wrote N rows —
  stated from structure); `silence(T1,T2) :- tool activity in [T1,T2], no row in [T1,T2],
  T2-T1 > threshold`; `backfill_suspect(S) :- silence(...) followed by burst(...)` —
  thresholds as facts, swappable per the measured runs-5-8 corpus, defeasible by declared
  exceptions rather than hardcoded branches.
- This slots into the existing marriage discipline: the ASP derivation banks a
  DerivationRecord like every engine run, and where a SQL floor for the same verdict is
  cheap, the differential's AGREE vocabulary applies to the auditor itself.

**Part 3 sketch (research direction, filed not committed):** with s23 tokens the whole
governance preamble's ORDERING obligations become one deontic/temporal ASP program over
the event stream — decompose-before-implement, criteria-before-first-write,
assumption-before-commitment, disposition-before-stop — each a violation atom derived
from the same EDB, replacing N bespoke hook checks with one auditable logic program.
That is possibly-addressable-concerns items 1 (ordering) and 4 (deontic) made concrete,
and it is the shape in which the deductive engine stops being an observer of the harness
and becomes its auditor. Needs its own design pass; named here so Part 2's author builds
the EDB with this consumer in mind.

## Sequencing

1. This memo: filed. 2. Sonnet authors the s-delta + hook change from it AFTER run 8
exits (hooks/ frozen while a wired session lives), scratch-witnesses both polarities,
differential AGREE. 3. The verb lands template-side (`audit` in bootstrap/templates/)
with seen-red fixtures — including a synthetic backfill corpus replayed from run-5/7/8
real timings. 4. First measured report over runs 5-8 sets the verdict thresholds; the
numbers go to the maintainer with the first prepared question this design actually
needs.

## Status (appended, dated per [ADR-0005](../law/adr/0005-documentation-discipline.md) Rule 8 — the original memo above stands unedited)

**Part 1: LANDED** (kernel/lineage/s23-per-invocation-stamp-token.sql;
hooks/stamp_intercept.py mints the token + journals `.claude/logs/invocations.jsonl`; both in
the [birth chain](../GLOSSARY.md#birth-chain) — the kernel SQL every new world receives at
scaffold time — since `bootstrap/new-project.sh --new-world`).

**Part 2: CORE LANDED, 2026-07-11 (Sonnet, commissioned build) — see BACKLOG.md's
"Contemporaneity audit, Part 2 — CORE LANDED" entry for the full disposition.** Sequencing
steps 1-4 above are done: the ASP verdict program + EDB builder + `./audit` verb + seen-red
fixtures all landed and witnessed (live against run7's real pre-s23 schema AND on an
apparatus-authored scratch world exercising the full CONTEMPORANEOUS|BATCHED_DECLARED|
BACKFILL_SUSPECT vocabulary both polarities); the thresholds were measured from the runs 5-8
corpus, not guessed (`engine/contemp_thresholds.lp`'s own derivation comments). **Filed, not
built, this pass** (a maintainer critical-path resequencing scoped the first landing to this
core): the SQL-floor differential (this verb ships ONE producer today, not the marriage
discipline's cross-validated pair — "marriage" is this repo's name for deriving every
verdict independently in ASP and SQL and requiring the two to AGREE byte-identically,
the `./judge` verb's own standard), `--retain`-by-default wiring in the `./audit` shim
itself, session-level (vs whole-ledger-window) verdict granularity, and Part 3 (untouched, as
scoped above). Two hazards surfaced live during the build: a clingo/clasp 32-bit integer
overflow on absolute epoch-ms values (FIXED in-pass — every emitted timestamp is now
anchor-relative) and a timestamp-convention disagreement across the three existing hook
journals (FLAGGED, not fixed — outside this commission's touch-list). Both named in
BACKLOG.md and in `engine/contemp_edb.py`'s own docstring, not silently routed around.

**Part 1½/late-entry extension: LANDED, 2026-07-11 evening (Sonnet, commissioned build from
design/LATE-ENTRY-AND-INTAKE-SEMANTICS.md, the ratified spec).** The maintainer's own
adjudication of Part 2's first live verdict (BACKLOG "Run-10 first audit verdict adjudicated")
surfaced the gap this design's Part 2 core left standing: the closed vocabulary could not
distinguish an honest intake burst from a suspect one by eye, and had no way for a writer to
DECLARE a late entry the way a paper log legitimately can. The late-entry design closes both,
additively: **Proposal 1** annotates a `token_burst` `intake-shape (precedes all tool activity)`
when every row in it predates this world's first `tool_event` (engine-side only, no vocabulary
change) — witnessed on a scratch world reproducing run-10's own rows-2-11 shape, never against
the live run-10 world (runs are linear). **Proposal 2** adds `kernel/lineage/
s24-declared-event-time.sql` (a nullable `event_declared_ts` column, `led --event-time <iso-ts>`)
and one new closed-vocabulary verdict, **LATE_DECLARED** (exit 0): the identical
silence-then-burst gap that would otherwise verdict BACKFILL_SUSPECT now verdicts
LATE_DECLARED instead, when the silence-breaking row carries a declared event time
exceeding `late_threshold_ms` — BACKFILL_SUSPECT now means precisely the UNDECLARED case. Scratch-witnessed
both polarities, SQL/ASP differential AGREE (`asp=10 sql=10 atoms; Δasp=[] Δsql=[]`), zero
residue; seen-red both polarities banked (`seen-red/contemporaneity-audit/run_fixtures.py` cases
f/g, `late-declared-green.txt`/`late-declared-red.txt`). **Proposal 3** adds the preamble
teaching line to `bootstrap/templates/CLAUDE.md.tmpl` (point 9), verbatim from the ratified
memo. Full disposition, per-claim witness status, and the scratch-witness/differential
transcripts: BACKLOG.md's dated entry beside this one. See CAPABILITIES.md item 24a for the
operator-facing summary.

**SQL-floor differential: LANDED, 2026-07-12 (Sonnet, commissioned build — the marriage-grade
half of the audit-verb-completions work item).** This closes the deferral item 24/24a and this
memo's own Part 2 status both named: "this verb ships ONE producer today, not the marriage
discipline's cross-validated pair." `engine/contemp_floor.py` is the SQL floor (`engine/ledger_floor.py`'s
sibling for this domain) — RE-DERIVES FROM SOURCE rather than consuming `engine/contemp_edb.py`'s
own staged EDB text (the honest choice, argued in that module's own docstring: consuming the
sibling producer's staging code would let a bug there show up identically in both producers and
the differential would silently agree on a wrong answer). It independently re-reads the live
ledger via its own SQL query and independently re-parses the raw `.claude/logs/*.jsonl` journal
bytes with its own small parser (never importing `contemp_edb.py`'s `_read_jsonl`/`_parse_ts_ms`),
computing burst/silence/intake_shape/backfill_suspect/late_declared/the per-row deltas, plus a
degraded `ts_cluster` signal (a row-adjacency burst GUESS for a pre-s23 world that carries no
invocation tokens at all — INFERRED from row timing alone, never presented as the same thing as a
STATED, token-backed burst), and the closed verdict, in Postgres window functions + set logic (no
recursion needed, unlike the ledger floor's transitive closures). `engine/contemp_differential.py`
is the differential runner, matching `engine/ledger_differential.py`'s conventions EXACTLY BY
IMPORT (never a re-derived copy): the closed verdict vocabulary (AGREE / DIVERGE_BY_DESIGN /
DIVERGE_DEFECT / QUARANTINED), the `DerivationRecord` dataclass, and the override-one-producer
negative-control seam. Both producers' DerivationRecord pairs bank under
`engine/docs/ledger-marriage/derivations/contemporaneity/<target>/<ts>_<hash>/` — one level
deeper than the ledger marriage's own tree, so a contemporaneity world's own (arbitrary,
per-project) name can never collide with a curated ledger target. **DENOMINATION NORMALIZATION**
(the one place this marriage differs mechanically from the ledger marriage, per this commission's
own mandate): the SQL floor emits every timestamp as its true ABSOLUTE epoch-ms value natively
(Postgres `bigint` has no 32-bit ceiling); the ASP producer emits every timestamp anchor-relative
(`engine/contemp_edb.py`'s own documented 32-bit clasp-wraparound dodge). Exactly three of the
ASP program's declared output facts (a clingo `#show` directive names which derived facts an ASP
program actually emits, out of everything it internally derives) carry an absolute-ts argument
(`token_min_ts/2`, `token_max_ts/2`, `silence/2`); the
differential normalizes those three UP to absolute (adding the same `anchor_ms` the EDB export
computed) before the set-comparison runs — stated explicitly in `contemp_differential.py`'s own
docstring, not silently assumed. **A SECOND, PREVIOUSLY-LATENT 32-BIT HAZARD WAS FOUND LIVE
AUTHORING THIS COMMISSION'S OWN SEEN-RED FIXTURE, FLAGGED AND GUARDED (not fixed at the source):**
`contemp_edb.py`'s anchor-relative encoding only protects a BOUNDED audited window (its own
docstring: "even a full week is ~6e8, safely under the 2^31 ceiling") — nothing enforces that
bound, and a scratch fixture mixing a synthetic far-future BASE (~2033) with real rows written
through `led` (`bootstrap/templates/led.tmpl`, this harness's own row-writing operator verb —
its `ts` column defaults to actual wall-clock now, ~2026) in the same accumulated ledger produced
a ~7-year window, ~100x past the ceiling, silently wrapping. `contemp_differential.py`'s own
`_max_abs_relative_ms` guard now refuses loudly (QUARANTINED) rather than comparing a
possibly-corrupted ASP producer whenever a world's audited window is unsafe — a real, in-scope
hardening (this file is the one that owns the anchor normalization step), not a fix to
`contemp_edb.py`'s own semantics (out of this commission's touch-list; named in BACKLOG.md's
dated entry). The seen-red fixture's own case (p) is positioned BEFORE the fixture cases that
write through `led` for exactly this reason (documented inline), so it demonstrates a genuine
AGREE rather than a QUARANTINE of its own fixture's making.

**`./audit --differential` (opt-in, default OFF)** wires the differential into the operator verb
(`bootstrap/templates/audit.tmpl`): plain `./audit` is unchanged (the same single-producer report
it has always printed); `./audit --differential` additionally runs
`engine/contemp_differential.py --retain` and prints its own AGREE/DIVERGE line beneath the normal
report. Default is OFF, not always-on like `judge` — reasoned in `audit.tmpl`'s own header: unlike
`judge` (which IS the differential; there is no cheaper single-producer fallback), `audit`'s
primary report is useful and cheap on its own, and `--differential` roughly doubles the work (a
second live-DB read, a second independent journal re-parse, a second clingo invocation) for a
check most invocations do not need turn-by-turn. Exit code 4 is newly reserved: reachable only
when `--differential` is passed AND `engine/contemp_audit.py`'s own verdict was clean (exit 0)
but the differential verdicted DIVERGE_DEFECT/QUARANTINED — a second-producer disagreement is
never silently folded into a clean exit 0 (ADR-0015 "no result is not a clean result", applied to
the differential axis). A non-zero `engine/contemp_audit.py` exit (1/2/3) is never overwritten by
the differential's own code.

**WITNESSED, both polarities, live**: `seen-red/contemporaneity-audit/run_fixtures.py` now carries
SEVENTEEN cases, adding (p) and (q). Case (p) builds a scratch world combining case (h)'s own
run-10 intake-shape burst and case (f)'s own manufactured LATE_DECLARED silence-then-burst, and
runs it through a REAL `engine/contemp_differential.py --retain` subprocess (the same invocation
`./audit --differential` makes): the differential returns **AGREE** (`asp=63 sql=63 atoms;
Δasp=[] Δsql=[]`), exits 0, and retains the DerivationRecord pair (banked
`differential-agree.txt`). Case (q) uses the SAME override seam
`engine/tests/test_ledger_marriage.py::test_single_producer_mutation_is_diverge_defect` already
precedents for the ledger marriage (`sql_atoms_override`) to forge one atom
(`token_burst("forged-token-not-real")`) into the SQL floor's returned set, in an isolated
subprocess — never touching `engine/contemp_floor.py`'s or `engine/lp/contemporaneity.lp`'s own
source — and the differential correctly returns **DIVERGE_DEFECT**, with `only_sql` naming
exactly the forged atom and `only_asp` naming the 63 legitimate atoms the forgery discarded
(banked `differential-diverge-defect.txt`). The full suite (17 cases) re-runs clean end to end,
exit 0, with zero scratch residue (both `contempprobe`/
`contempprobe_pre24` schema pairs dropped, every world tempdir removed).

**Deferrals still standing, unchanged by this pass** (named in the marriage-grade commission's own
scope: "the `--retain` default and session-granularity questions stay filed"):
`engine/contemp_audit.py` (Part 2's own single-producer report script, the one `./audit` execs)
still defaults its own `--retain` flag OFF, untouched by this pass; the verdict is still computed
over the WHOLE ledger window, not per-session (still filed); Part 3 (the deontic/temporal
ordering-obligations program) remains untouched, as scoped.
