% ===========================================================================
% contemp_thresholds.lp -- the MEASURED thresholds for engine/lp/contemporaneity.lp, as FACTS
% (ADR-0012 P1 / the 2026-07-02 ADR-0000 amendment's denomination check: a bound is denominated
% in, and DERIVED FROM, the resource that actually detonates -- never a round guessed literal).
% Swappable per corpus (design memo item 5): re-measure and replace this file's two facts; the
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
