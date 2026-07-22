% ===========================================================================
% ledger_belief.lp -- the v1 belief-substrate ASP rules (design/FABLE-BELIEF-SUBSTRATE-SPEC.md
% §2-§3.4, ratified ledger rows 1914/1919). Derives contested_belief/2, contest_resolved/2,
% credited_belief/1, corroboration_grade/2, shared_ancestor/3 from the v1 statement-prefix
% convention's EDB (engine/ledger_edb.py's export_belief()), backed by the existing defeat
% pipeline for un-founding a belief whose premise/source chain rests on a model-defeated row.
%
% LOAD ORDER (spec §2.2 item 3): loaded ON TOP OF ledger_tnow.lp + ledger_support.lp +
% ledger_defeat.lp -- it consumes in_force/1, superseded/1 (ledger_tnow.lp) and
% model_defeated_row/1 (ledger_defeat.lp, itself stacked on ledger_support.lp). LAYERS["belief"]
% in engine/lp_registry.py is the checkable required stack.
%
% BELIEF CREDIT COMPOSES BESIDE in_force/1, NEVER INTO IT (spec §3.4, the ledger_defeat.lp §10
% stratification laws extended to this layer): credited_belief/1 is its own separately-named
% stratum; in_force/1 stays supersession-only permanently.
%
% EDB (engine/ledger_edb.py's export_belief(), row_actor/agent_class REUSED from export_defeat()
% -- spec §2.2's own fact-family table names this reuse):
%   belief(Id).                         Id is a well-formed v1 belief row.
%   belief_polarity(Id,universal|existential).
%   belief_basis(Id,observed|derived|testimony|assumed).
%   belief_has_universe(Id).            Id carries a non-empty universe= (universal only).
%   belief_has_witness(Id).             Id carries a non-empty witness=.
%   belief_edge(Id,premise,T).          T is a cited premise (basis=derived).
%   belief_edge(Id,source,T).           T is the relayed source (basis=testimony).
%   belief_edge(Id,contests,T).         Id contests belief T (cross-principal, validated at parse).
%   belief_edge(Id,concurs,T).          Id concurs with belief T (cross-principal, validated at parse).
%   belief_subject(Id,T).               T is the row Id's proposition is about.
%   row_actor(Id,P).                    the principal id P who authored row Id (export_defeat()).
%   agent_class(P,C).                   kern.principal's agent_class (export_defeat()).
% Consumed from the stack (#defined so this file grounds standalone):
%   in_force(F).  superseded(D).  model_defeated_row(R).
% ---------------------------------------------------------------------------

#defined belief/1.
#defined belief_polarity/2.
#defined belief_basis/2.
#defined belief_has_universe/1.
#defined belief_has_witness/1.
#defined belief_edge/3.
#defined belief_subject/2.
#defined row_actor/2.
#defined agent_class/2.
#defined in_force/1.
#defined superseded/1.
#defined model_defeated_row/1.

% ---- Contest (spec §3.3) -----------------------------------------------------------
% A contest edge between two IN-FORCE beliefs. (belief_edge's own parse-time validation --
% export_belief() -- already refused a contest naming a non-belief, superseded, or
% same-actor target; this rule additionally requires BOTH ends in-force at read time, since a
% belief can be superseded by its own holder after the contest edge was written.)
contested_belief(C,T) :- belief_edge(C,contests,T), belief(C), belief(T), in_force(C), in_force(T).

% Evidence-class precedence (spec §3.3, closed, small, applied ONLY to resolve a contest, ONLY
% when the bases differ): observed > derived > testimony > assumed.
belief_basis_rank(observed,4).
belief_basis_rank(derived,3).
belief_basis_rank(testimony,2).
belief_basis_rank(assumed,1).

% contest_resolved(Winner,Loser): on a STRICT basis-rank inequality, the higher-basis belief is
% the contest's resolved survivor. Recency never resolves a contest between distinct principals
% (Q3) -- no rule here ever consults ts/id ordering, only belief_basis_rank.
contest_resolved(C,T) :- contested_belief(C,T), belief_basis(C,BC), belief_basis(T,BT),
                         belief_basis_rank(BC,RC), belief_basis_rank(BT,RT), RC > RT.
contest_resolved(T,C) :- contested_belief(C,T), belief_basis(C,BC), belief_basis(T,BT),
                         belief_basis_rank(BC,RC), belief_basis_rank(BT,RT), RT > RC.

% belief_doubt(X): X is demoted to visible doubt by an unresolved (tied-basis) contest, or X is
% the LOSING side of a resolved one. The winning side of a resolved contest is NOT doubted BY
% THAT PAIR (it may still be doubted by a different, unresolved contest elsewhere).
belief_doubt(C) :- contested_belief(C,T), belief_basis(C,B), belief_basis(T,B).
belief_doubt(T) :- contested_belief(C,T), belief_basis(C,B), belief_basis(T,B).
belief_doubt(L) :- contest_resolved(W,L).

% ---- Well-foundedness (spec §3.4 credited_beliefs semantics) -----------------------
% A non-belief ledger row grounds a chain iff it is in force and not defeated by the model-
% identity defeat pipeline (ledger_defeat.lp's model_defeated_row/1 -- composed here, neither
% calculus knowing the other's internals, exactly the chain-in-force test the spec names).
belief_grounded(X) :- in_force(X), not belief(X), not model_defeated_row(X).

% basis=observed: existential requires belief_has_witness (already existence-checked at parse
% time by export_belief()); universal is grounded by its mandatory, parse-checked universe.
belief_wellfounded(X) :- belief(X), belief_basis(X,observed), belief_polarity(X,existential),
                         belief_has_witness(X), in_force(X), not belief_doubt(X).
belief_wellfounded(X) :- belief(X), belief_basis(X,observed), belief_polarity(X,universal),
                         belief_has_universe(X), in_force(X), not belief_doubt(X).

% basis=derived: well-founded iff IN FORCE, UNCONTESTED, and every cited premise is itself
% either well-founded (a belief) or grounded (a non-belief, undefeated row). premises are
% mandatory+non-empty by construction (parse-time CHECK), so a derived belief with zero
% belief_edge(X,premise,_) facts cannot occur in a well-formed EDB.
belief_founded_node(T) :- belief_wellfounded(T).
belief_founded_node(T) :- belief_grounded(T).
belief_premise_unfounded(X) :- belief_edge(X,premise,T), not belief_founded_node(T).
belief_wellfounded(X) :- belief(X), belief_basis(X,derived), in_force(X), not belief_doubt(X),
                         belief_edge(X,premise,_), not belief_premise_unfounded(X).

% basis=testimony: well-founded iff IN FORCE, UNCONTESTED, and the relayed source is founded.
belief_wellfounded(X) :- belief(X), belief_basis(X,testimony), in_force(X), not belief_doubt(X),
                         belief_edge(X,source,T), belief_founded_node(T).

% basis=assumed: DELIBERATELY no well-foundedness rule -- an assumption is recorded, defeasible,
% and NEVER credited (spec §3.4 -- "an assumption's consumer is its future defeat, not credit").

% credited_belief/1: in force, not doubted by an unresolved (or losing-side) contest, and
% well-founded. Composes BESIDE in_force/1, never into it.
credited_belief(X) :- belief(X), belief_wellfounded(X).

% ---- Corroboration (spec §3.4 item 4) ----------------------------------------------
% A concurrence edge is SYMMETRIC for corroboration purposes (the spec's "concurrence-connected,
% SoD-distinct" set is unordered) -- concur_pair/2 is the symmetric closure of one hop of
% belief_edge(_,concurs,_); export_belief() already refused same-actor concurrence at parse time.
concur_pair(X,Y) :- belief_edge(Y,concurs,X), belief(X), belief(Y), in_force(X), in_force(Y).
concur_pair(X,Y) :- concur_pair(Y,X).

% The diversity grade is computed from agent_class over the concurrence-connected set (never a
% witness COUNT -- the attestation incident's own lesson, restated in spec §6's denomination
% clause). corroboration_grade is reported per credited belief only (an uncredited belief's
% corroboration reading is not this layer's concern -- the spec's own view lists credited_beliefs
% as corroboration's consumer).
concur_class(X,C) :- concur_pair(X,Y), row_actor(Y,P), agent_class(P,C).

corroboration_grade(X,"corroborated-cross-class") :-
    credited_belief(X), row_actor(X,P0), agent_class(P0,C0), concur_class(X,C1), C1 != C0.
corroboration_grade(X,"corroborated-same-class") :-
    credited_belief(X), concur_class(X,_), not corroboration_grade(X,"corroborated-cross-class").
corroboration_grade(X,"uncorroborated") :-
    credited_belief(X), not concur_class(X,_).

% ---- Shared premise/source ancestry (spec §3.4 item 5) -----------------------------
% Transitive closure over premise/source edges -- ASP's home ground for "five independent layers
% checked this" becoming a query whose answer can be no. Terminates: a premise/source must
% already exist at write time (append-only), so the edge graph is acyclic.
belief_ancestor(X,A) :- belief_edge(X,premise,A).
belief_ancestor(X,A) :- belief_edge(X,source,A).
belief_ancestor(X,A) :- belief_ancestor(X,Y), belief_edge(Y,premise,A).
belief_ancestor(X,A) :- belief_ancestor(X,Y), belief_edge(Y,source,A).

% shared_ancestor(A,B,S): for a concurrence-connected pair (A<B, one row per unordered pair),
% S is a common ancestor of both their premise/source closures.
shared_ancestor(A,B,S) :- concur_pair(A,B), A < B, belief_ancestor(A,S), belief_ancestor(B,S).

#show contested_belief/2.
#show contest_resolved/2.
#show credited_belief/1.
#show corroboration_grade/2.
#show shared_ancestor/3.
