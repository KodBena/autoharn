% core_a.lp — Core A of the corpus-consistency analysis, k-parameterized (external
% corpus-consistency-RESULT clauses 3/8; consult 17 §5.2, executed there and committed here as a
% standing instrument over ledger+principal facts — the "grown ASP encoding" of consult 17 §6 item 7).
%
% The corpus is CONSISTENT as a theory; its SATISFIABILITY is parameterized by principal cardinality
% and organizational partition (RESULT clause 3). This program computes the phase structure the
% waiver rows record as their evidence: at the harness population (k small, one org) the SoD triple
% and financial-independence cores are UNSAT — a model-SIZE failure, not a contradiction — and the
% honest disposition is the corpus's own recorded-waiver exit (RESULT clause 6), which the s13 ledger
% carries as two waiver rows.
%
% STRICT KERNEL ONLY (RESULT clause 7 / consult 17 §5.2 caution): countersign-not-author; SoD triple
% pairwise-distinct; financial independence = distinct org. Medium-confidence and J-triggered corpus
% entries are DELIBERATELY excluded — encoding a paraphrased synthesis as hard logic manufactures
% contradictions the sources may not contain.
%
% Sweep (each a separate clingo call with -c overrides), reproduced by run-core-a.sh:
%   k=1                -> UNSATISFIABLE   (the pre-actor-axis harness: one author, no signer)
%   k=2                -> SATISFIABLE     (technical independence — what the actor axis buys)
%   k=2 sod=1          -> UNSATISFIABLE   (the SoD triple needs a third principal)  -> WAIVER 1
%   k=3 sod=1          -> SATISFIABLE
%   k=2 fin=1 orgs=1   -> UNSATISFIABLE   (financial grade needs a real partition)  -> WAIVER 2
%   k=2 fin=1 orgs=2   -> SATISFIABLE

#const k=1.  #const orgs=1.  #const sod=0.  #const fin=0.
principal(1..k).  org(1..orgs).
1 { in_org(P,O) : org(O) } 1 :- principal(P).
author(w, 1).
1 { signs(w,Q) : principal(Q) } 1.
:- signs(w,Q), author(w,Q).                                  % G7/I6 technical: signer != author
1 { approves(w,Q) : principal(Q) } 1 :- sod=1.
1 { deploys(w,Q)  : principal(Q) } 1 :- sod=1.
:- sod=1, approves(w,Q), author(w,Q).
:- sod=1, deploys(w,Q),  author(w,Q).
:- sod=1, approves(w,Q), deploys(w,Q).                        % SoD triple: author/approver/deployer distinct
:- fin=1, signs(w,Q), author(w,P), in_org(Q,O), in_org(P,O).  % financial grade: signer in a distinct org
