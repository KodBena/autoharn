% ===========================================================================
% logic_repair.lp -- minimal-repair / blame over the functional conflicts.
% Loaded TOGETHER WITH logic_layer.lp (it reuses assertion/functional/exception).
%
% This is the one demonstration of "ASP does what SQL provably cannot": choose a
% SMALLEST set of assertions to retract so that NO functional conflict survives,
% then rank by cardinality. That is subset-optimization under a constraint -- a
% #minimize over a guessed `retract/1` set -- which a SQL view cannot express
% (B-autoharn-fit s.4: clingo's unique claim is the search SQL cannot rank).
% R-NEG/R-NUM are NOT repaired here: R-NEG is the SQL floor and R-NUM is plain
% disequality; the genuine ASP win is R-FUNC's defeasible blame assignment.
% ---------------------------------------------------------------------------

% Guess: any positive assertion under a functional predicate MAY be retracted.
{ retract(I) } :- assertion(I,_,P,_,pos), functional(P).

% Test: no functional conflict may survive the surviving (non-retracted) assertions.
% (Honours the same defeater `exception/2` from logic_layer.lp.)
:- functional(P),
   assertion(A,S,P,Oa,pos), assertion(B,S,P,Ob,pos), Oa != Ob,
   not exception(S,P),
   not retract(A), not retract(B).

% Optimise: fewest retractions = minimal repair = least blame.
#minimize { 1,I : retract(I) }.

#show retract/1.
