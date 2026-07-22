% ADR-0011 Rule 3 negative control (seen-red ONLY -- never engine/lp/): a deliberately BROKEN
% copy of engine/lp/ledger_belief.lp with the basis=assumed exclusion REMOVED from
% credited_belief/1's well-foundedness, so an assumed belief is WRONGLY credited. Proves the
% differential goes DIVERGE_DEFECT against the correct SQL floor (belief_floor.py), which never
% credits an assumed belief (spec §3.4: "assumed beliefs ... never credited").
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

contested_belief(C,T) :- belief_edge(C,contests,T), belief(C), belief(T), in_force(C), in_force(T).

belief_basis_rank(observed,4).
belief_basis_rank(derived,3).
belief_basis_rank(testimony,2).
belief_basis_rank(assumed,1).

contest_resolved(C,T) :- contested_belief(C,T), belief_basis(C,BC), belief_basis(T,BT),
                         belief_basis_rank(BC,RC), belief_basis_rank(BT,RT), RC > RT.
contest_resolved(T,C) :- contested_belief(C,T), belief_basis(C,BC), belief_basis(T,BT),
                         belief_basis_rank(BC,RC), belief_basis_rank(BT,RT), RT > RC.

belief_doubt(C) :- contested_belief(C,T), belief_basis(C,B), belief_basis(T,B).
belief_doubt(T) :- contested_belief(C,T), belief_basis(C,B), belief_basis(T,B).
belief_doubt(L) :- contest_resolved(W,L).

belief_grounded(X) :- in_force(X), not belief(X), not model_defeated_row(X).

belief_wellfounded(X) :- belief(X), belief_basis(X,observed), belief_polarity(X,existential),
                         belief_has_witness(X), in_force(X), not belief_doubt(X).
belief_wellfounded(X) :- belief(X), belief_basis(X,observed), belief_polarity(X,universal),
                         belief_has_universe(X), in_force(X), not belief_doubt(X).

belief_founded_node(T) :- belief_wellfounded(T).
belief_founded_node(T) :- belief_grounded(T).
belief_premise_unfounded(X) :- belief_edge(X,premise,T), not belief_founded_node(T).
belief_wellfounded(X) :- belief(X), belief_basis(X,derived), in_force(X), not belief_doubt(X),
                         belief_edge(X,premise,_), not belief_premise_unfounded(X).

belief_wellfounded(X) :- belief(X), belief_basis(X,testimony), in_force(X), not belief_doubt(X),
                         belief_edge(X,source,T), belief_founded_node(T).

% THE INJECTED DEFECT (the negative control): assumed beliefs are wrongly well-founded here,
% never in the real ledger_belief.lp -- an in-force, uncontested assumed belief needs NOTHING
% else to be "founded", the exact overclaim spec §3.4 forbids ("an assumption's consumer is its
% future defeat, not credit").
belief_wellfounded(X) :- belief(X), belief_basis(X,assumed), in_force(X), not belief_doubt(X).

credited_belief(X) :- belief(X), belief_wellfounded(X).

concur_pair(X,Y) :- belief_edge(Y,concurs,X), belief(X), belief(Y), in_force(X), in_force(Y).
concur_pair(X,Y) :- concur_pair(Y,X).

concur_class(X,C) :- concur_pair(X,Y), row_actor(Y,P), agent_class(P,C).

corroboration_grade(X,"corroborated-cross-class") :-
    credited_belief(X), row_actor(X,P0), agent_class(P0,C0), concur_class(X,C1), C1 != C0.
corroboration_grade(X,"corroborated-same-class") :-
    credited_belief(X), concur_class(X,_), not corroboration_grade(X,"corroborated-cross-class").
corroboration_grade(X,"uncorroborated") :-
    credited_belief(X), not concur_class(X,_).

belief_ancestor(X,A) :- belief_edge(X,premise,A).
belief_ancestor(X,A) :- belief_edge(X,source,A).
belief_ancestor(X,A) :- belief_ancestor(X,Y), belief_edge(Y,premise,A).
belief_ancestor(X,A) :- belief_ancestor(X,Y), belief_edge(Y,source,A).

shared_ancestor(A,B,S) :- concur_pair(A,B), A < B, belief_ancestor(A,S), belief_ancestor(B,S).

#show contested_belief/2.
#show contest_resolved/2.
#show credited_belief/1.
#show corroboration_grade/2.
#show shared_ancestor/3.
