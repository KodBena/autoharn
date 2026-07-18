% ===========================================================================
% unstratified_negative_control.lp -- THE MANDATED STRATIFICATION NEGATIVE CONTROL
% (design/FABLE-DEFEAT-PIPELINE-SPEC.md §10/§12 W10). NEVER placed under engine/lp/ -- placing
% it there is itself a defect (spec §15 item 6). This is a deliberately UNSTRATIFIED variant of
% engine/lp/ledger_defeat.lp's own defeat rule: the lawful rule's body is transcribed verbatim,
% then ONE clause is added -- `not model_defeated_row(A)` -- so the rule recurses through
% negation of its own derived predicate (model_defeated_row/1 is defined in terms of
% model_defeated/3, and model_defeated/3 now negates model_defeated_row/1). This is exactly the
% shape spec §10 law 1 forbids ("never `not model_defeated_row(X)` over the rule's own inputs")
% -- banked here, seen red, so the law is demonstrated broken rather than merely asserted.
%
% Run against seen-red/defeat-pipeline/run_fixtures.py's w10_stratification_red() fixture: two
% mutually mismatch-attesting rows (A1 mismatch-attests A2; A2 mismatch-attests A1, the guard
% removed) force a genuine odd cycle through negation -- X holds iff Y does not, Y holds iff X
% does not -- which has TWO stable models, not one. `clingo -n 0` (full enumeration) over this
% program and that EDB is expected to yield exactly 2 models, never 1; the SQL floor (monotone
% recursive SQL) cannot express this shape at all, so no SQL twin exists for it -- the pairing
% requirement of spec §7 forecloses this rule from ever reaching AGREE, which is the point.
% ---------------------------------------------------------------------------
#defined mismatch_attest/3.
#defined attest_row/1.
#defined grant_row/1.
#defined trust_grant/3.
#defined row_actor/2.
#defined agent_class/2.
#defined superseded/1.
#defined in_force/1.
#defined support_star/2.
#defined affirmed/2.

defeat_input(X) :- attest_row(X).
defeat_input(X) :- grant_row(X).

% THE UNSTRATIFIED VARIANT -- every clause of the lawful rule (engine/lp/ledger_defeat.lp)
% verbatim, PLUS `not model_defeated_row(A)`, the forbidden self-referential negation.
model_defeated(R,A,G) :-
    mismatch_attest(A,R,_),
    not superseded(A),
    row_actor(A,P),
    trust_grant(G,P,"model-identity-attestation"),
    not superseded(G),
    not defeat_input(R),
    not model_defeated_row(A).

model_defeated_row(R) :- model_defeated(R,_,_).

credited(R) :- in_force(R), not model_defeated_row(R).

exposure_model(F,D) :- in_force(F), support_star(F,D), model_defeated_row(D).
exposure_model_undischarged(F,D) :- exposure_model(F,D), not affirmed(F,D).

#show model_defeated/3.
#show credited/1.
#show exposure_model/2.
#show exposure_model_undischarged/2.
