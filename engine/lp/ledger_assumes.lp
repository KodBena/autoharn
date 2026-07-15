% ===========================================================================
% ledger_assumes.lp -- I7 folded in: an `assumes` edge with VALIDITY BOUNDS and an
% ASP EXPIRY CLOSURE. An assumption past its bound is LOUDLY not-in-force.
%
% I7 (safety-critical BRIEF §2, register F2/F14) is the formal-methods spine the
% generic audit regime misses: "every assumption a proof rests on AND the conditions
% under which it ceases to hold ... never the QED alone." Its historical deferral
% reason was "no consumer" (consult 11 axis D); the engine layer is the consumer
% arriving, so it is built HERE (scheduling ruling: deferring a third time would be
% the consumer-first misfire).
%
% A validity bound is NOT a record ordering (so this is not the ts-keyed ordering
% AC2 forbids): it is a temporal/id horizon past which the assumption is void. The
% `now/1` fact is injected at run time; `horizon/1` an id/step bound. Both closures
% fire the SAME loud predicate: an assumption out of bound is not_in_force, and any
% scope resting on it is flagged.
%
% LOAD ORDER (F-C, fidelity review §1): this program MUST be loaded ON TOP OF
% ledger_tnow.lp -- it consumes `superseded/1` from that program's supersession closure.
% An assumption whose whole ROW is superseded is not in force EVEN IF it has not expired;
% before this fix `assumption_in_force` composed only with expiry, so a superseded (retracted)
% assumption still read in-force (the exact censored-record shape F-A closes for answers).
% `#defined superseded/1` keeps this file groundable standalone (an empty extension is silence,
% not a grounding warning), but its INTENDED deployment is stacked on ledger_tnow.lp; the DTO
% scratch loads [ledger_tnow.lp, ledger_dto.lp, ledger_assumes.lp] together, and the
% superseded-assumption fixture there proves supersession composes.
% ---------------------------------------------------------------------------
%   assumes(A, Scope).        assumption row A is relied on by Scope.
%     SCOPE DOMAIN (declared, not split -- fidelity review §1 sibling; ADR-0008 no fabricated
%     structure without a consumer): Scope is a LEDGER ROW id in every fixture and consumer
%     today (the thing whose ground the assumption is). The design doc's "row id OR judgment
%     id" dual reading is NOT exercised -- no consumer keys on the distinction -- so the domain
%     is DECLARED here (row id) rather than split into assumes_row/assumes_judgment; split it
%     the moment a consumer must tell the two apart (then this declaration becomes the spec).
%   valid_until(A, Bound).    temporal validity bound: A holds only while now <= Bound (epoch).
%   valid_within(A, Horizon). id/step horizon: A holds only while the record head id <= Horizon.
%   now(N).                   current wall-clock epoch (injected at run).
%   record_head(H).           current max id in the record (injected at run; the id horizon cursor).
%   superseded(A).            from ledger_tnow.lp: A's whole row is (transitively) superseded.
#defined assumes/2.
#defined valid_until/2.
#defined valid_within/2.
#defined now/1.
#defined record_head/1.
#defined superseded/1.

% ---- expiry closures ---------------------------------------------------------------
expired_temporal(A) :- valid_until(A,B), now(N), N > B.
expired_horizon(A)  :- valid_within(A,H), record_head(R), R > H.
expired_assumption(A) :- expired_temporal(A).
expired_assumption(A) :- expired_horizon(A).

% An assumption is in force iff it is asserted, not expired, AND not whole-row superseded
% (F-C: compose with the supersession closure, not only with expiry).
assumption_in_force(A) :- assumes(A,_), not expired_assumption(A), not superseded(A).
% LOUD: an assumption past its bound is not in force ...
assumption_not_in_force(A) :- assumes(A,_), expired_assumption(A).
% ... OR whose whole row is superseded (F-C: a retracted assumption is loudly not-in-force) ...
assumption_not_in_force(A) :- assumes(A,_), superseded(A).
% ... and every scope resting on an EXPIRED or SUPERSEDED assumption is flagged: ground void.
resting_on_expired(Scope,A) :- assumes(A,Scope), expired_assumption(A).
resting_on_superseded(Scope,A) :- assumes(A,Scope), superseded(A).

#show assumption_in_force/1.
#show assumption_not_in_force/1.
#show expired_temporal/1.
#show expired_horizon/1.
#show resting_on_expired/2.
#show resting_on_superseded/2.
