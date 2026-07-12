% ===========================================================================
% contemp_thresholds.lp -- the MEASURED thresholds for engine/lp/contemporaneity.lp, as FACTS
% (ADR-0012 P1 / the 2026-07-02 ADR-0000 amendment's denomination check: a bound is denominated
% in, and DERIVED FROM, the resource that actually detonates -- never a round guessed literal).
% Swappable per corpus (design memo item 5): re-measure and replace this file's facts; the
% rules in contemporaneity.lp never change.
%
% MEASUREMENT (WITNESSED, 2026-07-11): the only real ledger data in existence at measurement
% time is the runs 5-8 corpus (db `toy`, host 192.168.122.1, schemas run3/run4/run5/run6/run7 --
% run8's rows live IN run7's schema, same night, post-hydration, per BACKLOG's own "Run 8" prose;
% no separate run8 schema exists). NONE of these schemas carry stamp_invocation (s23 postdates
% them) or an invocations.jsonl/tool-event journal (the hooks that write those postdate them too)
% -- so this measurement is necessarily the DEGRADED, ts-gap-only kind the design memo's item 3
% names as available historically ("Inter-row ts deltas alone ... may support a degraded
% BATCHED-pattern report"). Run 9+ (born with s23 in the birth chain) is the real, full-capability
% audience; this measurement sets a defensible STARTING threshold for it, not a claim the
% tokened-era distribution will look identical.
%
% Query (read-only, against the live schemas -- reproducible):
%   WITH d AS (SELECT id, kind, ts,
%                EXTRACT(EPOCH FROM (ts - lag(ts) OVER (ORDER BY id)))::numeric(12,3) AS gap
%              FROM <schema>.ledger)
%   SELECT id, kind, gap FROM d ORDER BY id;
% run against run5.ledger (76 rows) and run7.ledger (79 rows, spanning run7's phase 1 AND the
% same-night run8 continuation).
%
% BURST_THRESHOLD_MS -- "the max gap within which N rows are structurally one command's write."
%   Every observed same-command burst gap (four work_opened rows, N-row review sweeps, N-row
%   work_claimed/work_closed sweeps -- the exact pattern BACKLOG's "Contemporaneity indictment"
%   names) fell in [0.021s, 0.040s] across BOTH corpora (run5: e.g. 0.021-0.032s repeatedly;
%   run7: 0.022-0.040s repeatedly). The SMALLEST gap that was NOT part of such a burst (a
%   genuine distinct-moment gap) was 1.141s (run7, decision id 12) -- a >28x separation from the
%   largest true-burst gap (0.040s), with zero observed values in between. 1000ms (1.0s) sits in
%   that empty gap, at the natural round unit: comfortably above every measured burst (25x
%   margin) and comfortably below the smallest measured non-burst gap (13% margin below 1141ms,
%   deliberately conservative -- a threshold flush against the boundary would misclassify the
%   very case that set it).
burst_threshold_ms(1000).

% SILENCE_THRESHOLD_MS -- "the min tool-activity-with-zero-rows gap that is a genuine, flaggable
%   silence, not ordinary per-call latency." This axis is NOT measurable from ts-gaps alone (the
%   whole point of Part 1/Part 2: a row-to-row gap of hundreds of seconds is indistinguishable,
%   from ts alone, between "real live interactive work with many untracked tool calls" and "the
%   agent went quiet" -- disambiguating the two is exactly what the invocation-journal/tool-event
%   correlation exists to do, and no run has produced that data yet since s23 landed 2026-07-11
%   with no run 9 started). The two HAND-CORRELATED true positives on record (BACKLOG "Run-5
%   forensics" / "Run-8 phase-2 verification", forensic transcript-vs-ledger reconstruction, the
%   exact ad-hoc method Part 2 replaces) are: run5's main thread, 8m23s (503s) of witnessed tool
%   activity (23 events) landing ZERO ledger rows before a 19-row burst; run8's mid-run gap,
%   5m12s (312s) of tool activity (13 calls) landing ZERO rows before its own burst. 180000ms
%   (180s = 3 minutes) is set BELOW the smaller confirmed true positive (312s, 42% margin) so a
%   future backfill smaller than either historical case still trips the threshold, while staying
%   an order of magnitude above ordinary single-tool-call latency (single-digit-to-tens of
%   seconds) and above the routine inter-burst "real work" gaps this corpus's OWN ts-only data
%   cannot itself validate as innocent (named honestly: this value is a REASONED lower bound from
%   two known positives, not a full ROC measurement over labeled negatives -- that measurement
%   needs the run 9+ tool-event corpus and is filed, not built, this pass; see BACKLOG.md).
silence_threshold_ms(180000).

% LATE_THRESHOLD_MS -- "the min gap between a row's DECLARED event time and its own write time
%   that counts as a genuine late entry, not ordinary recording latency" (design/LATE-ENTRY-AND-
%   INTAKE-SEMANTICS.md Proposal 2, s24-era schemas only). NOT independently corpus-measurable
%   yet, honestly: `event_declared_ts` postdates every run in existence at authoring time (s24
%   lands same day as this fact), so there is no tokened, DECLARED-late-entry corpus to run the
%   burst_threshold_ms/silence_threshold_ms style gap analysis against -- the same "no run has
%   produced that data yet" limit silence_threshold_ms's own derivation names for a different
%   axis. The ONE real specimen on record of a genuinely late, HONESTLY-reported entry is run
%   10's row 1 (BACKLOG "Run-10 first audit verdict adjudicated", 2026-07-11): ~2 minutes
%   (measured ~120s) of pre-ledger investigation, self-reported in prose ("Recording this gap
%   honestly rather than back-dating") because s24's mechanism did not exist yet to hold it.
%   Mirroring silence_threshold_ms's own method -- set BELOW the one confirmed true positive, by
%   a margin comparable to that value's own 42% -- gives 60000ms (60s): half of the 120s
%   specimen (a 2x margin below it, so a future declared-late entry no larger than the one
%   real case on record still trips the threshold), while staying an order of magnitude above
%   ordinary single-call recording latency (the seconds a writer spends composing the `led`
%   invocation itself, single-digit-to-tens of seconds) -- the same two-sided bracket
%   silence_threshold_ms's own reasoning uses, applied to the one real number this axis has.
%   REASONED LOWER BOUND FROM ONE KNOWN POSITIVE, not a full ROC measurement over labeled
%   negatives (named honestly, same disclosure silence_threshold_ms's own header carries) --
%   re-measure once a run 24+ (s24-capable) corpus of genuinely declared late entries exists.
late_threshold_ms(60000).

% STOP_DISPOSITION_WINDOW_MS -- design/ORCH-CONTEMPORANEITY-PART3-SPEC.md E9: "the min gap, in ms,
%   before a stop_event within which a decision row counts as ITS disposition" (F10, preamble
%   point 8: "Stopping is a ledgered act ... write the disposition a successor resumes from").
%   MEASURED, 2026-07-12: the only world in existence carrying a stop_clean_exit.journal.jsonl
%   record at measurement time is run11 (`/home/bork/w/vdc/1/run11`, schema run11 -- the first
%   world born with hooks/stop_clean_exit.py wired; runs 5-10 predate it entirely, an ABSENCE
%   named honestly, not a second measurement). ONE real specimen: the journal's single
%   `clean_allow` stop_event at 2026-07-11T19:29:58.648Z; the ledger's own "stopping: commission
%   fulfilled ..." decision row (run11.ledger id 95, kind=decision, ts
%   2026-07-11T19:28:36.08488+02 = 19:28:36.085Z) precedes it by 82563ms; a LATER decision row
%   (id 96, "delegating a final ... reviewer countersign pass", 19:28:48.19Z) -- itself written
%   AFTER the disposition decision but BEFORE the stop event -- precedes the stop event by
%   70453ms. The wider of the two real gaps a window must cover is 82563ms.
%   (Query, read-only, reproducible: `SELECT id,kind,ts,left(statement,60) FROM run11.ledger
%   WHERE kind='decision' ORDER BY id DESC LIMIT 6;` joined against
%   run11/.claude/logs/stop_clean_exit.journal.jsonl's own `ts`.)
%   DIRECTION DIFFERS FROM burst/silence/late (named honestly): those three thresholds are set
%   BELOW their one confirmed positive (a gap must EXCEED the bound to count as a finding); this
%   window must instead COVER its confirmed positive -- setting W below 82563ms would misclassify
%   run11's own honestly-disposed stop as a VIOLATION, the exact false-positive class this
%   program exists to avoid (ADR-0000's engineering-responsibility corollary: a mechanism must not
%   indict the one real specimen its own measurement is drawn from). 120000ms (2 minutes) sits
%   ABOVE the measured 82563ms with a 45% margin -- comfortably covering the one real case while
%   staying an order of magnitude BELOW "an unrelated much-earlier decision" (the run11 corpus's
%   own decision cadence runs single-digit-minutes apart at the tightest, per the id 84-87 cluster
%   above) so the window does not credit a disposition that was not actually THIS stop's own.
%   REASONED BOUND FROM ONE KNOWN POSITIVE (the same honest disclosure silence_threshold_ms and
%   late_threshold_ms's own headers carry) -- re-measure once a corpus of multiple s-hook-wired
%   stop events exists; filed, not built, this pass.
stop_disposition_window_ms(120000).
