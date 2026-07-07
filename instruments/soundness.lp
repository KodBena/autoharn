% ledger soundness — derived-validity semantics over the append-only ledger (consult 11 §4.2).
% Committed as the parameterizable ASP artifact §8.3 asks for; `soundness.py` is the same
% semantics run directly on live psql data. The EDB below is the s10 record (the worked
% instance, extracted read-only) so `clingo soundness.lp` reproduces the banked model. For any
% other session, regenerate the entry/enacts/supersedes facts from {session}.ledger and reload.
%
% Output (clingo 5.8.0, SATISFIABLE, one model):
%   alias_surface(10,4) alias_surface(25,4) alias_surface(27,4)
%   unsound_derivation(25,4) unsound_derivation(27,4)
%   launder(25,4,22) launder(27,4,22)
%   inexpressible(multi_enacts(13)) inexpressible(none_enacts(14))

% ---- EDB (generated from s10.ledger, read-only): entry(Id,Ts,Kind,Concern); enacts/2; supersedes/2.
entry(1,1783264680,note,process).      entry(2,1783264941,decision,design).
entry(3,1783264946,decision,design).   entry(4,1783264950,question,design).
entry(5,1783264960,decision,design).   entry(6,1783264964,decision,design).
entry(7,1783264970,decision,design).   entry(8,1783264996,note,enactment).
entry(9,1783265037,note,enactment).    entry(10,1783265074,note,enactment).
entry(11,1783265107,note,enactment).   entry(12,1783265374,decision,design).
entry(13,1783265383,note,enactment).   entry(14,1783265434,note,enactment).
entry(15,1783265487,note,process).     entry(16,1783265624,finding,design).
entry(17,1783265636,note,process).     entry(18,1783265711,note,process).
entry(19,1783265772,verification,enactment). entry(20,1783265784,verification,enactment).
entry(21,1783265818,note,process).     entry(22,1783266237,decision,design).
entry(23,1783266249,decision,design).  entry(24,1783266258,note,process).
entry(25,1783266320,note,enactment).   entry(26,1783266350,note,process).
entry(27,1783266384,note,enactment).   entry(28,1783266407,note,process).
entry(29,1783266494,note,process).     entry(30,1783266556,note,process).
entry(31,1783266610,verification,enactment). entry(32,1783266641,note,process).
enacts(8,2). enacts(9,2). enacts(10,4). enacts(11,7). enacts(13,7).
enacts(19,7). enacts(25,4). enacts(27,4). enacts(31,22).
supersedes(22,4).

% ---- IDB
% ID-KEYING RETROFIT (F-D, clingo-fidelity review 2026-07-06; consult 17 §5.3 id-is-order law).
% This instrument formerly keyed defeat/precedence on ts with `<=`; the ratified marriage program
% (ledger_tnow.lp) keys on the integer id with STRICT `<`. On every banked record id-order and
% ts-order agree, so the shown model is unchanged -- but at the boundary they diverged: a row that
% both supersedes D and enacts D (a self-superseding citation) is called UNSOUND by ts-`<=` (the
% superseder's own citation-instant is <= itself) and SOUND by strict id-`<` (the row names the
% antecedent it replaces). Keying on ts made THIS instrument the non-conforming encoding by the
% operator side's own id-is-order law. Retrofitted to id-`<` so it conforms.
% RATIFIED (maintainer, 2026-07-06): strict id-precedence -- a row citing the row it supersedes is
% SOUND (deliberations/clause-defeat-decompose-then-overrule.md RATIFIED §2). The live-psql twin
% soundness.py is now retrofitted to the SAME id-`<` / highest-id keying, and the operator-twin
% differential (soundness_twin.py, a close_manifest declared-observer line) is the standing net that
% makes any future divergence between these two encodings a RED, non-skippable close line. The banked
% s10 record has no boundary case, so the model below reproduces BYTE-IDENTICALLY after the retrofit.
sup_star(X,Y) :- supersedes(X,Y).
sup_star(X,Z) :- supersedes(X,Y), sup_star(Y,Z).
% D is defeated as of citing row E iff some superseder X of D precedes E in ID order (strict `<`).
defeated_asof(Y,E) :- sup_star(X,Y), entry(E,_,_,_), X < E.
head(Y,Y) :- entry(Y,_,_,_), not sup_star(_,Y).
head(Y,H) :- sup_star(X,Y), head(X,H).
% the gate's ACTUAL judgment (deployed enacts check: existence + id-precedence only)
gate_ok(E)  :- enacts(E,D), D < E.
% the SOUND ticket judgment (antecedent in force at citation -- id-keyed, strict)
sound_ok(E) :- enacts(E,D), D < E, not defeated_asof(D,E).
unsound_derivation(E,D) :- enacts(E,D), gate_ok(E), not sound_ok(E).
% what auto-resolve-to-head would rewrite the record to
resolved(E,H) :- enacts(E,D), head(D,H).
launder(E,D,H) :- unsound_derivation(E,D), resolved(E,H), D != H.
% reference-domain hygiene: enacts targets that are not design decisions
alias_surface(E,D) :- enacts(E,D), entry(D,_,K,_), K != decision.
% axes the scalar schema cannot express (representable only as absence; e10's bigint[] closes both):
inexpressible(multi_enacts(13)).   % row 13 names designs 5,7,12; the scalar column carries one
inexpressible(none_enacts(14)).    % row 14's honest value was "no single antecedent"; NULL was denied

#show unsound_derivation/2. #show launder/3. #show alias_surface/2. #show inexpressible/1.
