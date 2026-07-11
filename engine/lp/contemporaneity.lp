% ===========================================================================
% contemporaneity.lp -- Part 2 of design/CONTEMPORANEITY-AUDIT.md: the correlation VERB's
% verdict logic, ASP-FIRST per the maintainer's standing directive (design memo's "Part 2
% implementation directive", 2026-07-11) and the delegation contract's ASP-first framing
% (research/design/possibly-addressable-concerns.md's warning against bending every problem
% into SQL). The event stream (the ledger + the hook-written journals) becomes an EDB; the
% batching verdict is DERIVED, not hand-correlated by a human running ad-hoc SQL every crisis
% (the exact "should have automated 11 runs ago" the maintainer named).
%
% SECOND-PRODUCER STATUS (named honestly, per ADR-0011 Rule 1's enforcement-surface
% declaration): this is the ONLY producer this pass ships. The marriage discipline's SQL-floor
% differential (engine/ledger_floor.py's sibling) is FILED, not built, in BACKLOG.md's dated
% entry -- the maintainer's critical-path resequencing (2026-07-11, "ship the minimal
% end-to-end core first") scoped this pass to the ASP derivation + its Python EDB/report
% harness. A verdict from ONE producer is not yet marriage-differential-grade trust; that gap
% is the filed deferral, not a silent claim of AGREE.
%
% EDB (engine/contemp_edb.py; a fact family absent because a world lacks the capability --
% pre-s23 (no stamp_invocation column), or hooks off/unwired (no invocations.jsonl), or no
% hook-journaled tool activity yet -- is a DECLARED EXCLUSION in the capability manifest the
% EDB header prints, never silence -- I12 / the ledger_edb.py idiom this program mirrors):
%
%   row_tokened(Id, Token, Kind, T).    a ledger row (Id) stamped with invocation Token
%                                       (s23's stamp_invocation column), of Kind, written at
%                                       epoch-MILLISECOND T (ledger.ts). "The recorded event."
%   row_untokened(Id, Kind, T).         a ledger row with NO invocation token (pre-s23 era, or
%                                       a non-intercepted write) -- same T convention.
%   invocation(Token, T).               a hook-minted per-Bash-invocation token, journaled at
%                                       epoch-MILLISECOND T (.claude/logs/invocations.jsonl
%                                       wall_clock). "The actual event" side of the correlation.
%   tool_event(Kind, T).                a hook-journaled tool-activity marker (Kind in
%                                       {mutation, change_gate, delegation} -- the three
%                                       existing observer journals), at epoch-MILLISECOND T.
%   burst_threshold_ms(N).              FACT, not a hardcoded rule literal (ADR-0012 P1 /
%                                       ADR-0000 2026-07-02 amendment's denomination check):
%                                       the max gap, in ms, within which N>=2 row writes are
%                                       structurally "one command wrote N rows", measured from
%                                       the runs-5-8 corpus (engine/contemp_thresholds.lp).
%   silence_threshold_ms(N).            FACT: the min gap, in ms, between two tool-activity
%                                       markers with ZERO ledger rows between them, below which
%                                       the gap is ordinary thinking/tool latency and above
%                                       which it is a genuine, flaggable silence.
% ---------------------------------------------------------------------------
#defined row_tokened/4.
#defined row_untokened/3.
#defined invocation/2.
#defined tool_event/2.
#defined burst_threshold_ms/1.
#defined silence_threshold_ms/1.

% NON-FORECLOSURE (the ledger_acts.lp / work_items.lp acceptance-criteria shape, applied here):
%   * base relations (row_id, tool_event_id, next_tool_event, row_ts_of, ...) are FIRST-CLASS
%     #shown outputs -- a consumer builds its own report from them without touching this program.
%   * NO verdict vocabulary over the SUBJECT's conduct/truth: batch/silence/backfill_suspect are
%     statements about the EVENT-STREAM SHAPE (a burst is N rows under one token; a silence is a
%     tool-activity gap with no row in it), never an accusation -- the design memo's own aim
%     ("some batching is irreducible ... the defect is that the record cannot distinguish that
%     from run-5-style backfill"). Adjudicating what a BACKFILL_SUSPECT verdict MEANS for a given
%     session is a human/ratifier act downstream of this report, not this program's job.
%   * ZERO `:-` integrity constraints. A record with a burst / a silence / a burned id stays
%     SATISFIABLE and queryable (paraconsistent) -- every world differentials to a report, never
%     a refusal-to-solve.
%   * MONOTONE base (row_id/token/tool_event_id/row_ts_of use no negation); the NAF seam is
%     confined to the "immediate successor" idiom (next_tool_event, skip_te / row_id gap-detection)
%     and to silence's "not row_between" -- named, not diffused through the whole program.
% ---------------------------------------------------------------------------

% ==== ID-SEQUENCE (refusal fingerprints) ====================================================
% A row id is EITHER tokened or untokened -- the union is "a row exists at this id". The kernel's
% id sequence (bigserial) burns a value on ANY attempted insert, including one a validation
% trigger later raised on (BACKLOG "run-5 forensics": row 62 missing = the refusal's fingerprint,
% not a deletion -- append-only forecloses UPDATE/DELETE, so a gap can ONLY be a burned id, never
% erased evidence). A gap in the [min,max] id range is therefore a refusal fingerprint, computed
% directly over the finite interval (clingo interval-in-body; no arithmetic-adjacency assumption).
row_id(Id) :- row_tokened(Id,_,_,_).
row_id(Id) :- row_untokened(Id,_,_).
row_id_bounds(Min,Max) :- Min = #min{ I : row_id(I) }, Max = #max{ I : row_id(I) }, row_id(_).
refusal_fingerprint(Id) :- row_id_bounds(Min,Max), Id = Min..Max, not row_id(Id).

% ==== TOKEN BURSTS (STATED -- design memo item 1: "N rows under one token = one command wrote N
% rows -- stated, not inferred from ts spacing") ============================================
token(T) :- row_tokened(_,T,_,_).
token_row_count(Tok,N) :- token(Tok), N = #count{ Id : row_tokened(Id,Tok,_,_) }.
token_burst(Tok) :- token_row_count(Tok,N), N > 1.
token_min_ts(Tok,Min) :- token(Tok), Min = #min{ Ts : row_tokened(_,Tok,_,Ts) }.
token_max_ts(Tok,Max) :- token(Tok), Max = #max{ Ts : row_tokened(_,Tok,_,Ts) }.

% ==== DEGRADED TS-CLUSTER (INFERRED -- pre-token era only; item 3's honest limit: "Inter-row ts
% deltas alone (available historically) may support a degraded BATCHED-pattern report" -- a
% DISTINCT predicate name from token_burst above so a consumer can never read an inferred cluster
% as a stated one). Adjacency is by ID-ORDER (the design/ledger-marriage "ids are the interchange"
% law), via the immediate-successor idiom -- NOT Id+1 arithmetic (a burned id would falsely break
% adjacency; work_items.lp's arithmetic +1 does not apply here for the same reason ledger_acts.lp's
% `reach` needed contiguous act ids and this domain is NOT guaranteed contiguous).
row_untokened_id(Id) :- row_untokened(Id,_,_).
skip_untokened(Id1,Id2) :- row_untokened_id(Id1), row_untokened_id(Id2), row_untokened_id(Id3),
    Id1 < Id3, Id3 < Id2.
next_untokened(Id1,Id2) :- row_untokened_id(Id1), row_untokened_id(Id2), Id2 > Id1,
    not skip_untokened(Id1,Id2).
ts_cluster(Id1,Id2) :- next_untokened(Id1,Id2), row_untokened(Id1,_,T1), row_untokened(Id2,_,T2),
    burst_threshold_ms(B), (T2-T1) <= B.

% ==== SILENCE (journaled era only -- design memo item 2: "journaled tool-invocation timeline vs
% ledger-write timeline; every gap > threshold where tool activity ran with zero rows") =========
tool_event_id(T) :- tool_event(_,T).
skip_te(T1,T2) :- tool_event_id(T1), tool_event_id(T2), tool_event_id(T3), T1 < T3, T3 < T2.
next_tool_event(T1,T2) :- tool_event_id(T1), tool_event_id(T2), T2 > T1, not skip_te(T1,T2).

row_ts_of(Id,T) :- row_tokened(Id,_,_,T).
row_ts_of(Id,T) :- row_untokened(Id,_,T).
row_ts(T) :- row_ts_of(_,T).
row_between(T1,T2) :- next_tool_event(T1,T2), row_ts(T), T1 < T, T < T2.
silence(T1,T2) :- next_tool_event(T1,T2), silence_threshold_ms(S), (T2-T1) > S,
    not row_between(T1,T2).

% ==== BACKFILL SUSPECT (design memo item 2/5 + item 4's row-62 framing: "the silence ... followed
% by the burst ... becomes one table line, mechanically"). A burst is flagged when its earliest row
% IS the very first row-bearing activity to appear after a silence's end -- i.e. nothing else
% (tokened or untokened, any token) landed a row between the silence's end and this burst's start.
% This is the precise, mechanical form of "the burst broke the silence", never an ts-proximity
% guess (no arbitrary extra margin constant -- the definition is structural: first-after wins).
first_row_after(T2,Min) :- silence(_,T2), Min = #min{ T : row_ts(T), T >= T2 }.
backfill_suspect(Tok) :- token_burst(Tok), token_min_ts(Tok,Min), first_row_after(T2,Min),
    silence(_,T2).

% ==== PER-ROW DELTAS (the maintainer's own asked-for number, design memo item 3) ===============
% (a) row ts minus its OWN invocation's journaled wall-clock -- "sanity: near-zero always" (the
%     hook journals the invocation just before the psql call that lands the row in the same
%     process breath; a large delta here is itself a finding, not assumed impossible).
row_delta_ms(Id,D) :- row_tokened(Id,Tok,_,RT), invocation(Tok,IT), D = RT - IT.
% (b) the age of the PRECEDING journaled tool-activity window at the moment the row landed --
%     the nearest STRICTLY EARLIER tool_event to this row's own ts (immediate-predecessor idiom,
%     mirroring next_tool_event above but walking backward).
skip_pte(Id,TE) :- row_ts_of(Id,RT), tool_event_id(TE), tool_event_id(TE2),
    TE < TE2, TE2 <= RT.
preceding_tool_event(Id,TE) :- row_ts_of(Id,RT), tool_event_id(TE), TE <= RT,
    not skip_pte(Id,TE).
preceding_activity_age_ms(Id,Age) :- preceding_tool_event(Id,TE), row_ts_of(Id,RT), Age = RT - TE.

% ==== SESSION-LEVEL VERDICT (closed vocabulary, judge-style -- design memo item 5). Mutually
% exclusive by construction (stratified negation over two monotone base facts): a session with
% at least one backfill_suspect burst is BACKFILL_SUSPECT outright (the loudest finding wins,
% never averaged away by a majority of clean bursts); absent that, any token_burst at all makes
% it BATCHED_DECLARED (batched, but every burst is accounted for -- no silence precedes it);
% absent both, CONTEMPORANEOUS. This predicate is grounded ONLY when the EDB actually carries
% row_tokened/invocation/tool_event facts (a token-less/journal-less world contributes none of
% these, so verdict/1 is legitimately EMPTY there -- the Python harness (engine/contemp_audit.py)
% reads that emptiness as the trigger for its own EXPLICIT typed refusal, never silence read as
% "clean" -- the exact vacuous-pass class ADR-0000/ADR-0015 forbid).
any_backfill :- backfill_suspect(_).
any_batch :- token_burst(_).
verdict(backfill_suspect) :- any_backfill.
verdict(batched_declared) :- any_batch, not any_backfill.
verdict(contemporaneous) :- token(_), not any_batch, not any_backfill.

#show refusal_fingerprint/1.
#show token_burst/1.
#show token_row_count/2.
#show token_min_ts/2.
#show token_max_ts/2.
#show ts_cluster/2.
#show silence/2.
#show backfill_suspect/1.
#show row_delta_ms/2.
#show preceding_activity_age_ms/2.
#show verdict/1.
