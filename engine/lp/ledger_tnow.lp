% ===========================================================================
% ledger_tnow.lp -- the T_now derived-validity program of the ledger-logic
% marriage (design LEDGER-LOGIC-MARRIAGE.md §4; the soundness.lp semantics of
% consult 11 §4.2 promoted from one hardcoded EDB to the whole epistemic record).
%
% SECOND PRODUCER, differential-gated. The SQL FLOOR (ledger_floor.py, recursive
% CTEs -- SQL's home turf for monotone closure) is producer one; this program is
% the independent second producer over the SAME typed EDB (ledger_edb.py). On the
% record the two must agree BIT-IDENTICALLY (the kb_why / ADR-0000 INDEP idiom):
% empty symmetric-difference == the encoding is trustworthy. Where the two would
% diverge it is BY DESIGN and named (a defeater fires); a defect divergence turns
% the run red (ledger_differential.py, the closed vocabulary).
%
% ID IS THE ORDER, NEVER ts (design §3 rule 2; consult 17 §5.3: same-second and
% 41 ms neighbours exist in the record; the single id sequence is the sound total
% order). EVERY "earlier" below keys on the integer id, never on Ts. Ts is carried
% in entry/6 for report/display and for I7 temporal validity bounds ONLY (a bound
% is not a record ordering) -- it never keys a precedence rule here. A same-second
% neighbour fixture (the DTO scratch) proves the sort key is id.
%
% Acyclic by construction: append-only + earlier-target validation makes every
% edge strictly backward in id, so all closures terminate (consult 11 §4.2).
%
% EDB (ledger_edb.py; a fact family absent because the TARGET cannot produce it is
% a DECLARED EXCLUSION in the capability manifest, never silence -- I12):
%   entry(Id, Ts, Kind, Concern, Status, Confidence).
%   supersedes(A, B).   % A (newer, higher id) whole-row defeats B (older).
%   enacts(E, D).        % E enacts design antecedent D.
%   answers(A, Q).       % A resolves question Q.   (capability: amends/answers targets)
%   amends(A, T).        % A clause-defeats target T (verbatim-quotation edge).
% ---------------------------------------------------------------------------

% Declare the optionally-empty EDB families so an empty extension is silence, not a
% "never appears in a head" grounding warning (ADR-0002 / why_layer.lp idiom).
#defined entry/6.
#defined supersedes/2.
#defined enacts/2.
#defined answers/2.
#defined amends/2.

% ---- supersession closure (whole-row defeat), id-ordered --------------------------
sup_star(X,Y) :- supersedes(X,Y).
sup_star(X,Z) :- supersedes(X,Y), sup_star(Y,Z).
superseded(Y) :- sup_star(_,Y).

% ---- in-force / head-resolution ----------------------------------------------------
% A row is in force iff nothing (transitively) supersedes it.
in_force(Id) :- entry(Id,_,_,_,_,_), not superseded(Id).
% Head: an unsuperseded row is its own head; else follow the inverse-supersedes chain
% (supersedes(X,Y) => X replaces Y) up to the row nothing supersedes.
head(Y,Y) :- entry(Y,_,_,_,_,_), not superseded(Y).
head(Y,H) :- supersedes(X,Y), head(X,H).

% ---- enacts soundness (the deployed gate vs the sound judgment) --------------------
% The DEPLOYED gate's actual judgment: existence + id-precedence only (it consults
% supersedes/status nowhere). "earlier" is id, never ts.
gate_ok(E,D) :- enacts(E,D), D < E.
% D is defeated as of E iff some superseder X of D precedes E in id order. E ranges over
% entries (an enacting row's id) -- id-precedence, never ts.
defeated_asof(D,E) :- sup_star(X,D), entry(E,_,_,_,_,_), X < E.
% The SOUND judgment: antecedent in force at citation.
sound_ok(E,D) :- enacts(E,D), D < E, not defeated_asof(D,E).
% The live divergence: gate accepts, soundness rejects (rows 25/27 in s10).
unsound_derivation(E,D) :- enacts(E,D), gate_ok(E,D), not sound_ok(E,D).
% What auto-resolve-to-head would REWRITE the edge to (a coherent, FALSE record --
% the launder negative control; the only evidence-preserving move is flag-and-journal).
resolved(E,H) :- enacts(E,D), head(D,H).
launder(E,D,H) :- unsound_derivation(E,D), resolved(E,H), D != H.

% ---- reference-domain hygiene ------------------------------------------------------
% enacts target that is not a design `decision` (an alias surface -- F49 class).
alias_surface(E,D) :- enacts(E,D), entry(D,_,K,_,_,_), K != decision.

% ---- stale-enactment ROW debt ------------------------------------------------------
% An in-force enactment whose design antecedent is superseded NOW: the file work
% stands on a defeated design (the L2' live-debt readout, design §7).
% RENAMED stale_enactment_debt -> stale_enactment_row (fidelity review "Minor" / item 6):
% THIS predicate is ROW-granular; the operator instrument `stale_enactment_debt`
% (instruments/stale_enactment_debt.py) is FILE-granular (journal-joined) -- same name, a
% DIFFERENT judgment. A distinct name so a reader never conflates the two.
stale_enactment_row(E,D) :- enacts(E,D), in_force(E), superseded(D).

% ---- question status ---------------------------------------------------------------
% F-A (fidelity review §1 / §2.1): a question is answered ONLY by an answer still IN FORCE.
% The kernel's ratified consumer (s13.question_status) reopens a question whose answering row
% is superseded; the earlier marriage encoding joined ALL answers (`answers(_,Q)`), so a
% RETRACTED answer left the question "answered" forever -- the censored-record shape BRIEF
% I3/§11.10(e) forbids. Both producers shared the weaker rule, so the differential was
% structurally BLIND to it (twins agree; agreement is not fidelity). `answered/1` is now the
% ONE home of the in-force-answer judgment (P1); question_open/question_answered derive from it.
answered(Q) :- answers(A,Q), not superseded(A).
question_open(Q)     :- entry(Q,_,question,_,_,_), not answered(Q).
question_answered(Q) :- entry(Q,_,question,_,_,_), answered(Q).

% ---- clause-level defeat (amends; F44 aspectual axis) ------------------------------
% Mutually exclusive dispositions, matching soundness.py's precedence (withdrawn
% before moot before live): an amends whose author A is itself superseded is
% WITHDRAWN; else whose target T is whole-row superseded is MOOT; else LIVE.
clause_defeat_withdrawn(A,T) :- amends(A,T), superseded(A).
clause_defeat_moot(A,T)      :- amends(A,T), superseded(T), not superseded(A).
clause_defeat(A,T)           :- amends(A,T), not superseded(T), not superseded(A).
% condition-2 (DTO re-entry recognition, consult 19 §1.7): >=2 in-force amends on
% one target -- the row's individuation is wrong, it is due decomposition.
condition2_individuation(T) :- clause_defeat(A1,T), clause_defeat(A2,T), A1 < A2.

#show in_force/1.
#show head/2.
#show unsound_derivation/2.
#show launder/3.
#show alias_surface/2.
#show stale_enactment_row/2.
#show question_open/1.
#show question_answered/1.
#show clause_defeat/2.
#show clause_defeat_moot/2.
#show clause_defeat_withdrawn/2.
#show condition2_individuation/1.
