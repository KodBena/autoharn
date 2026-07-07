% ===========================================================================
% ledger_support.lp -- the transitive SUPPORT-EXPOSURE closure + flag-discharge
% vocabulary (Increment 2; WORK-UNIT-exposure-discharge.md, maintainer-commissioned,
% filed by Fable session 7be3443d, 2026-07-06). ADDITIVE, DERIVED, T_now-side: the
% kernel (T_event) gains no columns, no verbs, no semantics changes.
%
% THE GAP THIS CLOSES (work unit §0). The harness detects dependents of an invalidated
% row ONE HOP OUT only. Depth >= 2 was dark: D superseded, E enacts D (flagged), F enacts
% E -- F's exposure was invisible in both producers. This program computes the transitive
% support graph so an in-force row resting at ANY depth on a defeated antecedent is visible.
% Separately it gives the flags an honest discharge path (generalizing rekeyed/3): a flag is
% retracted only by a recorded, actor-attributed act keyed to the specific antecedent.
%
% LOAD ORDER (work unit §2; the ledger_dto.lp / ledger_assumes.lp contract). This program is
% loaded ON TOP OF ledger_tnow.lp -- it consumes in_force/1, superseded/1, enacts/2, answers/2
% from that program. exposure_expired additionally composes with ledger_assumes.lp
% (assumes/2, expired_assumption/1) WHEN loaded. The `#defined` guards below keep this file
% GROUNDABLE STANDALONE (an empty extension is silence, not a "never appears in a head"
% grounding warning -- the ledger_tnow.lp / why_layer.lp idiom); its INTENDED deployment is
% stacked [ledger_tnow.lp, ledger_assumes.lp, ledger_support.lp].
%
% NON-FORECLOSURE (work unit §1 -- ACCEPTANCE CRITERIA, not advice; deduction policy is a
% consumer choice, so nothing here forecloses paraconsistent or non-monotonic consumption):
%   §1.1 the base relations support_edge/3 + support_star/2 are FIRST-CLASS #shown outputs
%        (mechanism, not policy) -- a consumer builds its own policy from them + superseded/1.
%   §1.2 NO verdict vocabulary over the dependent: `exposure` is a statement about the SUPPORT
%        GRAPH, never about the dependent's truth. Descriptive names only.
%   §1.3 ZERO `:-` integrity constraints. A record with contradictions/cycles/arbitrary depth
%        stays SATISFIABLE and queryable; pathologies are FLAGGED (support_cycle/1), never UNSAT.
%   §1.4 NO feedback edges: none of these judgments appears in the body of any EXISTING rule
%        (ledger_tnow.lp / ledger_dto.lp / ledger_assumes.lp are byte-identical -- verified).
%   §1.5 MONOTONE base, NAF only at the labeled seam: support_edge/support_star use no
%        negation-as-failure (safe for any logic); the ONLY non-monotonic step is the discharge
%        join, confined to exposure_undischarged/2 so a consumer can take the monotone view.
%   §1.6 ADDITIVE proof: banked derivations reproduce byte-identical (new atoms may appear;
%        no old atom appears, vanishes, or changes).
%
% §3 RULING A -- RATIFIED (maintainer-ratified, Fable-recommended; 2026-07-06). The §3 question --
%   whether `affirms` becomes a KERNEL EDGE KIND or a `review`-row CONVENTION on real lineages -- is
%   RESOLVED: on a REAL lineage, affirmation is a REVIEW-SPECIES. It is a `review` row whose `regards`
%   is the DEPENDENT, PLUS a TYPED antecedent column in `review_detail` (the two-place judgment gets two
%   typed places, never prose). The kernel's vocabulary therefore grows by `review` ONLY -- NOT a new
%   `affirms` edge kind -- and the kernel's EXISTING review SoD trigger then enforces Ruling B (below)
%   FOR FREE. The kernel change is NOT built in this increment: it binds when `affirms` reaches a real
%   subject lineage (link-25/e15 scope, off this increment). Until then, scratch `affirms/3` +
%   `affirm_author/2` are the apparatus-authored EXERCISE STAND-IN for that ratified review-species
%   shape (exactly as the DTO EDB stood in before its exercise); the pending marker is DISCHARGED.
% ---------------------------------------------------------------------------
%   CONSUMED (from ledger_tnow.lp / ledger_assumes.lp; #defined so this file grounds standalone):
%     enacts(E,D).            E enacts design antecedent D.
%     answers(A,Q).           A resolves question Q.
%     in_force(F).            F is not (transitively) superseded.
%     superseded(D).          D's whole row is (transitively) superseded.
%     assumes(A,Scope).       assumption row A is relied on by Scope (ledger_assumes.lp).
%     expired_assumption(A).  A is past its validity bound (ledger_assumes.lp).
%   APPARATUS-AUTHORED SCRATCH-ONLY EDB (§3 RATIFIED Ruling A -- the EXERCISE STAND-IN for the real-
%   lineage review-species shape; on the scratch lineage, named in witness):
%     affirms(R,F,D).         row R records: F was re-examined and survives D's defeat.
%     affirm_author(R,P).     the principal who authored affirmation R.
%     row_actor(F,P).         the principal who authored row F (from the ledger `actor` column).
#defined enacts/2.
#defined answers/2.
#defined in_force/1.
#defined superseded/1.
#defined assumes/2.
#defined expired_assumption/1.
#defined affirms/3.
#defined affirm_author/2.
#defined row_actor/2.

% ---- Item 1: the support-exposure closure -----------------------------------------
% The neutral support-edge relation, KIND-TAGGED so consumers can filter.
% Direction: support_edge(Dependent, Antecedent, Kind) -- the dependent RESTS ON the antecedent.
support_edge(E,D,enacts)  :- enacts(E,D).
support_edge(A,Q,answers) :- answers(A,Q).
support_edge(S,A,assumes) :- assumes(A,S).   % Scope S rests on assumption A

% DELIBERATE EXCLUSIONS (work unit §2; the kind-tag exists so a future ruling that reclassifies
% an edge is ONE line here, not a schema change):
%   - amends is a CHALLENGE edge (clause-defeat vocabulary), not support.
%   - regards/review is judgment-about, not resting-on.
%   - supersedes is replacement lineage (sup_star's job in ledger_tnow.lp), not support.
%   - decomposes is re-issue lineage (DTO's job), not support.

% Pure reachability. MONOTONE -- no validity filtering, no NAF (§1.5). This is the relation
% consumers of any logic build on.
support_star(F,D) :- support_edge(F,D,_).
support_star(F,D) :- support_edge(F,X,_), support_star(X,D).

% Cycle flag (descriptive §1.3; the kernel's append-only earlier-target validation makes
% forward-id cycles unlikely, but the program must not ASSUME acyclicity -- flag, never constrain).
support_cycle(F) :- support_star(F,F).

% The convenience judgment: an IN-FORCE row whose support graph reaches a DEFEATED antecedent.
% Carries the ROOT so the adjudicator knows what died. It deliberately traces THROUGH dead
% intermediates -- "my chain died at depth 1" does not erase "and its root was D" (§2, fixture 2).
exposure(F,D) :- in_force(F), support_star(F,D), superseded(D).

% Expired-assumption variant (composes with ledger_assumes.lp when loaded; #defined guards keep
% this file groundable standalone). An in-force row resting transitively on an EXPIRED (not
% superseded) assumption.
exposure_expired(F,A) :- in_force(F), support_star(F,A), expired_assumption(A).

% ---- Item 2: discharge vocabulary (generalizing rekeyed/3) -------------------------
% SoD: self-affirmation is a RED FLAG, never a pass. The author of the DEPENDENT row F may not be
% the discharging affirmer (the actor of the affirmation row R equals the actor of F). This is the
% FLAG half of the mirror of decomp_sod_violation.
affirm_sod_violation(R) :- affirms(R,F,_), affirm_author(R,P), row_actor(F,P).

% An affirmation discharges ONE exposure pair -- keyed to the antecedent. ATTESTATION CURRENCY:
% a fresh defeat X != D raises fresh exposure the old affirmation does NOT cover; an affirmation
% row that is itself superseded no longer discharges (the affirmation is a row like any other).
%
% RULING B -- RATIFIED (maintainer-ratified, Fable-recommended; 2026-07-06): `affirmed` is SoD-GATED;
% a self-affirmation NEVER discharges. The flag-only reading is FORECLOSED (not parked). The work unit
% §3 originally gave affirmed/2 as `affirms(R,F,D), not superseded(R)` -- UNGATED -- with
% `affirm_sod_violation` as a SEPARATE flag ("never a pass, mirror of decomp_sod_violation"). But the
% named precedent does the OPPOSITE of flag-only: decomp_attested (ledger_dto.lp) HARD-GATES on
% `By != Author`, and fragment_in_force REQUIRES decomp_attested, so a self-attestation confers NO
% standing AND is flagged (the safe reading is the DEFAULT; the flag is belt-and-braces). An ungated
% rule contradicts its own named precedent and leaves a self-dealing trap: a consumer querying the
% natural actionable seam (exposure_undischarged) ALONE would read a self-affirmed exposure as cleanly
% discharged. So affirmed/2 GATES on `not affirm_sod_violation(R)`, the exact mirror of decomp_attested
% -- a self-affirmation does NOT discharge (never a pass) and IS flagged. This does NOT foreclose §1.1:
% the base relations (support_edge/support_star/exposure) and the raw affirms/row_actor EDB stay
% published, so a consumer that WANTS to honor a self-affirmation rebuilds it from those; only the
% CONVENIENCE predicate encodes the sound default (as exposure/2 and exposure_undischarged already do).
% This is ALSO how Ruling A's real-lineage shape enforces B for free: as a `review` row, the kernel's
% existing review SoD trigger rejects the self-review, so the gate here is the scratch STAND-IN for
% that trigger. (The former one-line "revert to the ungated rule if the maintainer rules flag-only" is
% GONE -- the flag-only reading is foreclosed, so there is nothing to revert to.)
affirmed(F,D) :- affirms(R,F,D), not superseded(R), not affirm_sod_violation(R).

% The NAF seam (§1.5): the discharge join is the ONLY non-monotonic step in this work unit (affirmed
% and exposure_undischarged), confined here so a consumer can take the monotone view (exposure/2).
% F28 posture -- discharge is an explicit ledgered act; nothing auto-clears; the monotone exposure/2
% remains visible even when discharged (a consumer that wants discharged history has it -- §1.1 again).
exposure_undischarged(F,D) :- exposure(F,D), not affirmed(F,D).

% #show: the base relations support_edge/3 + support_star/2 are FIRST-CLASS shown outputs (§1.1),
% not scaffolding hidden inside derived judgments. (If support_star atom volume is ever a problem
% on a large target the fallback is a documented #show-toggle, never removal of the relation.)
#show support_edge/3.
#show support_star/2.
#show support_cycle/1.
#show exposure/2.
#show exposure_expired/2.
#show affirmed/2.
#show exposure_undischarged/2.
#show affirm_sod_violation/1.
