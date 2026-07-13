% ===========================================================================
% verification_stats.lp -- work item `verification-stats-asp-harvester` (maintainer directive
% 2026-07-13, relayed from a downstream `ent` transcript): derives approve/revise/reject
% DISTRIBUTIONS, per workflow, per role, and per round, from the `kind=verification` ledger rows
% engine/verification_stats_edb.py grounds. The house EDB idiom that makes deriving these stats
% "not annoying from an ergonomics perspective" -- the whole point of this work item.
%
% VERDICT VOCABULARY: this program COUNTS, it does not JUDGE. Its only output is `count_*/N`
% distributions and `unparseable_verification/1` (carried through from the EDB, #show'n here so a
% reader of the DERIVED atoms sees it without having to separately inspect the EDB text) -- never
% an opinion about whether a workflow/role/round's approve-vs-revise ratio is GOOD or BAD. That
% judgment is downstream (ent's own dashboard/review), exactly as engine/lp/review_gap_audit.lp's
% own header states its own limit ("flagged/1 ONLY -- never a violated/refused vocabulary") for its
% domain. Stated here because a reader of THIS file alone should not have to chase the EDB module
% to learn the vocabulary's own honesty bound (mirroring that sibling's own discipline).
%
% ZERO `:-` integrity constraints (the corpus's own paraconsistent idiom, matching
% engine/lp/work_items.lp / engine/lp/review_gap_audit.lp): every distribution stays SATISFIABLE
% and reportable, never a refusal-to-solve -- an empty ledger, an all-unparseable ledger, and a
% fully-parsed ledger are all ordinary, satisfiable inputs.
%
% GENERIC OVER THE DEPLOYMENT SCHEMA (per this work item's own mandate): this program reasons only
% over the six EDB predicates below, never over a table/column name -- engine/verification_stats_edb.py
% is the one place a deployment schema's shape is read, so `ent` (or any other kind=verification
% deployment) consumes this program unchanged as a served capability.
% ---------------------------------------------------------------------------
#defined verification_row/1.
#defined verification_verdict/2.
#defined verification_role/2.
#defined verification_workflow/2.
#defined verification_round/2.
#defined verification_task/2.
#defined unparseable_verification/1.

% ---- observed (dimension, verdict) combinations -- the "GROUP BY" set each count ranges over ---
wf_verdict(Workflow,V)   :- verification_workflow(R,Workflow), verification_verdict(R,V).
role_verdict(Role,V)     :- verification_role(R,Role), verification_verdict(R,V).
round_verdict(Round,V)   :- verification_round(R,Round), verification_verdict(R,V).

% ---- the distributions themselves: one row count per observed combination ----------------------
count_workflow_verdict(Workflow,V,N) :-
    wf_verdict(Workflow,V),
    N = #count{ R : verification_workflow(R,Workflow), verification_verdict(R,V) }.

count_role_verdict(Role,V,N) :-
    role_verdict(Role,V),
    N = #count{ R : verification_role(R,Role), verification_verdict(R,V) }.

count_round_verdict(Round,V,N) :-
    round_verdict(Round,V),
    N = #count{ R : verification_round(R,Round), verification_verdict(R,V) }.

% ---- the overall per-verdict total (workflow/role/round-agnostic) -- the ergonomic "how many
% approve vs revise vs reject, full stop" figure the maintainer's relayed complaint names first --
count_verdict(V,N) :- verification_verdict(_,V), N = #count{ R : verification_verdict(R,V) }.

% ---- the honest-limit counterpart: how many rows this program could NOT ground at all -----------
count_unparseable(N) :- N = #count{ R : unparseable_verification(R) }.

#show count_workflow_verdict/3.
#show count_role_verdict/3.
#show count_round_verdict/3.
#show count_verdict/2.
#show count_unparseable/1.
#show unparseable_verification/1.
