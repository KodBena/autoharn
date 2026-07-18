% ===========================================================================
% ledger_defeat.lp -- the minimal model-defeat pipeline's ASP rule pair
% (design/FABLE-DEFEAT-PIPELINE-SPEC.md §5; ratified build basis, ledger row 1481). Derives
% model_defeated/3, credited/1, exposure_model/2, exposure_model_undischarged/2 from a
% mismatch attestation, backed by an in-force trust grant, that defeats an attested row.
%
% LOAD ORDER (spec §5.1/§7): loaded ON TOP OF ledger_tnow.lp -- it consumes in_force/1 and
% superseded/1 from that program. The CASCADE half additionally composes with
% ledger_support.lp WHEN stacked (support_star/2, affirmed/2) -- the `#defined` guards below
% keep this file GROUNDABLE STANDALONE, matching the ledger_support.lp / ledger_assumes.lp
% idiom exactly. engine/lp_registry.py's "defeat" LAYER is the checkable required stack
% (ledger_tnow.lp, ledger_support.lp, ledger_defeat.lp) -- see that registry entry for what a
% runner must load before grounding this program.
%
% NORMATIVE TEXT (spec §5.1 -- transcribed, not adapted; the builder does not fork on it. Any
% rule that will not ground or whose SQL twin cannot reach AGREE is a spec defect to surface,
% never a rule to adjust here -- spec §10's closing clause / §15 item 3).
%
% THE THREE STRATIFICATION LAWS THIS FILE OBEYS (spec §10, BINDING BUILDER LAW):
%   1. every in-force test in a defeat rule's body is `not superseded/1` (plus same-row
%      attribute projection, e.g. the active flag at export) -- never `credited/1`, never
%      `not model_defeated_row/1` over the rule's own inputs.
%   2. the machinery's own input kinds (attest_row/1, grant_row/1) are outside its target
%      domain -- `not defeat_input/1`, never removed or narrowed.
%   3. defeat composes BESIDE in_force/1, never into it -- `in_force/1` stays supersession-only
%      permanently; `credited/1` is a separately-named stratum on top.
%
% EDB (engine/ledger_edb.py's export_defeat(); a fact family absent because the target cannot
% produce it is a DECLARED EXCLUSION in the capability manifest, never silence -- I12):
%   row_actor(Id,P).            the principal id P who authored ledger row Id (actor column).
%   attest_row(A).               A is a valid attestation row (either arm, any verdict).
%   mismatch_attest(A,R,Grade).  attestation A asserts a model-identity mismatch about row R.
%   trust_grant(G,P,Activity).   grant row G: P holds Activity competence, ACTIVE (I1 two-conjunct).
%   grant_row(G).                EVERY principal_competence_granted row, active or not (the guard basis).
%   agent_class(P,Class).        kern.principal's agent_class -- emitted, consumed by no rule here.
% ---------------------------------------------------------------------------

% Declared-optional EDB families (empty extension = silence, the house #defined idiom):
#defined mismatch_attest/3.
#defined attest_row/1.
#defined grant_row/1.
#defined trust_grant/3.
#defined row_actor/2.
#defined agent_class/2.
% Consumed from ledger_tnow.lp / ledger_support.lp when stacked (LAYERS "defeat"):
#defined superseded/1.
#defined in_force/1.
#defined support_star/2.
#defined affirmed/2.

% The defeat machinery's own input kinds are outside its target domain (spec §10 law 2):
defeat_input(X) :- attest_row(X).
defeat_input(X) :- grant_row(X).

% THE DEFEAT RULE (envelope §3.2, I1-corrected; row-1481 rulings honored by construction).
% Every in-force test is `not superseded/1` -- the supersession layer, never this layer
% (§10 law 1). Grade is carried, deliberately unread (grade-conditioned defeat is OUT).
model_defeated(R,A,G) :-
    mismatch_attest(A,R,_),
    not superseded(A),
    row_actor(A,P),
    trust_grant(G,P,"model-identity-attestation"),
    not superseded(G),
    not defeat_input(R).

model_defeated_row(R) :- model_defeated(R,_,_).

% The credited reading: beside in_force, never inside it (§10 law 3).
credited(R) :- in_force(R), not model_defeated_row(R).

% CASCADE, the ratified direction (e): hard defeat above; dependents FLAGGED over the
% EXISTING support closure, discharged by the EXISTING SoD-gated affirmation -- a join,
% not new machinery (ledger_support.lp is byte-untouched; this program only reads it).
exposure_model(F,D) :- in_force(F), support_star(F,D), model_defeated_row(D).
exposure_model_undischarged(F,D) :- exposure_model(F,D), not affirmed(F,D).

#show model_defeated/3.
#show credited/1.
#show exposure_model/2.
#show exposure_model_undischarged/2.
