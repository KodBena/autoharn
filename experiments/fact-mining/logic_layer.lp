% ===========================================================================
% logic_layer.lp -- the paraconsistent, differential-gated LOGIC LAYER over the
% contradiction detector (clingo 5.8.0 / stable-model semantics).
%
% This is ADDITIVE and REVERSIBLE: contra_detect.py (the Python oracle) and
% schema.sql (the SQL substrate) are UNCHANGED. This program re-expresses the
% SAME three rules -- R-NEG / R-FUNC / R-NUM -- as declarative clauses over an
% EDB exported from the SAME FactBundle/Claims the Python detector consumes, so
% a divergence between the two is an ENCODING BUG surfaced before trust
% (B-autoharn-fit s.5: the encoding is the least-reviewed, highest-authority
% artifact; the differential gate is how it is qualified -- ADR-0000/INDEP).
%
% Obligation discharged: CONSIST -- "contradictions are quarantined; no ex-falso,
% no silent side-picking" (01-obligation-taxonomy s.10). The R-NEG glut is a
% first-class inspectable VALUE (`both`), not a `:- ` integrity constraint that
% detonates -- the FDE/Belnap move of doc 25-paraconsistent-manyvalued.
%
% EDB (contra_asp.edb_from_claims, derived from contra_detect.claims_from_bundle):
%   assertion(Id, SubjKey, Pred, ObjKey, Pol).  Pol = pos | neg   (the `negated` seam)
%   functional(Pred).                           the FUNCTIONAL_PREDS allowlist AS DATA
%   number(Id, CanonStr).                       transparent parsed value, only if parseable
%   multi_valued(SubjKey, Pred).                defeater seam for R-FUNC (default: empty)
% Ids are the claim's index in claims_from_bundle(bundle) -- a stable shared identity
% the differential maps back through (so neither side re-derives the other's text).
% ---------------------------------------------------------------------------

% These EDB predicates may legitimately be EMPTY on a given document (a doc with
% no numbers, no functional clash, no declared defeater). Declare them so an empty
% extension is silence, not a "never appears in a head" warning -- ADR-0002: the
% absence of a number is data, never an error.
#defined functional/1.
#defined number/2.
#defined multi_valued/2.

% ---- R-NEG : paraconsistent GLUT (three-valued, `Both` designated) ----------
% The SAME canonical (subject, predicate, object) asserted AND denied. We DERIVE a
% truth value `both` (FDE/LP) -- contained and queryable -- instead of exploding.
% This mirrors the mining.contradiction SQL view EXACTLY: R-NEG is the cheap SQL
% floor, re-expressed here only so the three rules share one substrate.
truth(S,P,O,both) :- assertion(_,S,P,O,pos), assertion(_,S,P,O,neg).
finding(neg, A, B)  :- assertion(A,S,P,O,pos), assertion(B,S,P,O,neg).

% ---- R-FUNC : functional-integrity violation, DEFEASIBLE --------------------
% A functional predicate carrying two DISTINCT objects for one subject is a
% conflict -- UNLESS defeated. Two things SQL cannot do declaratively and ASP can
% (this is where ASP earns its keep over the SQL floor -- B-autoharn-fit N15):
%   (1) functional/1 is DATA, not a hard-coded frozenset -- the precision control
%       is an auditable EDB fact, retractable without touching this program;
%   (2) `not exception(S,P)` is recursion-through-negation: a default with an
%       exception. Adding a `multi_valued(S,P)` fact RETRACTS the finding
%       non-monotonically -- the ADR-amendment-supersession shape, additive.
exception(S,P)    :- multi_valued(S,P).
conflict_func(S,P) :- functional(P),
                      assertion(_,S,P,Oa,pos), assertion(_,S,P,Ob,pos), Oa != Ob,
                      not exception(S,P).
finding(func, A, B) :- functional(P),
                       assertion(A,S,P,Oa,pos), assertion(B,S,P,Ob,pos),
                       Oa != Ob, A < B,
                       not exception(S,P).

% ---- R-NUM : numeric mismatch -----------------------------------------------
% Both asserted, both objects parsed to a number, the CANONICAL values differ.
% The parse happens in Python (contra_detect.parse_number, already audited) and the
% canonical value is shipped as a term; clingo does the disequality. This is
% FAITHFUL to the Python rule, which is itself disequality -- NOT magnitude
% arithmetic. True magnitude/tolerance reasoning (>, approx-equal, unit coercion)
% needs clingcon or the Z3 two-bit encoding of doc 25; that is HONESTLY future
% work, not claimed here.
finding(num, A, B) :- assertion(A,S,P,_,pos), assertion(B,S,P,_,pos), A < B,
                      number(A,Na), number(B,Nb), Na != Nb.

#show finding/3.
#show truth/4.
#show conflict_func/2.
