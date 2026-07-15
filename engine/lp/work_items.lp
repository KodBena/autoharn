% ===========================================================================
% work_items.lp -- the WORK-ITEM LEDGER violations layer (s22-work-item-ledger.sql;
% design/S22-WORK-ITEM-LEDGER.md, Fable-authored spec, session be693afb, 2026-07-09). ADDITIVE,
% DERIVED, engine-layer: the kernel (T_event, s22's DDL) gains no columns/verbs/semantics from
% this program -- it reasons over the s22 EDB (work_opened/2, work_closed/3, work_witness_present/1,
% work_depends/3), computing the SAME four judgments as work_item_violations (the SQL floor,
% work_item_floor_atoms in engine/ledger_floor.py), so the two producers differential
% bit-identically (spec witness protocol item 5: SQL floor vs .lp AGREE).
%
% THIS PROGRAM STANDS ALONE (no ledger_tnow.lp load-on-top). Work-item events are never whole-row
% superseded/amended by design (the spec's Q4 evidence: "status never left 'open' in 33/33 rows" --
% v1's vocabulary is open->closed only, no disposition-churn machinery) -- so the supersession
% closure ledger_tnow.lp supplies has nothing to compose with here. Grounds standalone via the
% `#defined` guards below (an empty extension is silence, not a grounding warning -- the
% ledger_tnow.lp / why_layer.lp idiom).
%
% TEXT STAYS HOME (design rule, ledger_edb.py rule 1): work_title and work_witness (prose / free
% text) do NOT cross into this EDB -- only the SLUG (a stable identifier, atom-quoted like `kind`/
% `concern`, never prose) and a WITNESS-PRESENT boolean flag (work_witness_present/1) cross. A
% consumer that wants the witness/title TEXT reads work_item_current (the SQL view), not the EDB.
%
% NON-FORECLOSURE (the ledger_support.lp / ledger_acts.lp acceptance-criteria shape, applied here):
%   * base relations (work_dep_edge/2, work_dep_star/2) are FIRST-CLASS #shown outputs -- a
%     consumer builds its own policy from them, without touching this program.
%   * NO verdict vocabulary over the work item's TRUTH: these are statements about the EVENT
%     GRAPH (duplicate opens, dangling deps, cycles, missing witnesses), descriptive names only.
%   * ZERO `:-` integrity constraints. A record with a cycle / a dangling dependency / a duplicate
%     open stays SATISFIABLE and queryable (paraconsistent) -- the SAME posture s22's own DDL
%     takes for the two members it does NOT refuse at construction (dangling dep, cycle); for the
%     two it DOES refuse at construction (duplicate open, shipped-without-witness) this program's
%     matching predicates are PROVABLY VACUOUS under normal operation too (named, not hidden --
%     see s22-work-item-ledger.sql's header for why both producers carry a defense-in-depth member
%     the write-boundary should already have foreclosed).
%   * MONOTONE base (work_dep_edge, work_dep_star use no negation-as-failure); the NAF seam is
%     confined to work_shipped_without_witness (`not work_witness_present(R)`) and
%     work_depends_on_unknown (`not work_opened(Antecedent,_)`), so a consumer can take the
%     monotone view of the rest.
% ---------------------------------------------------------------------------
%   EDB (engine/work_item_scratch.py / kernel/fixtures/s22_work_item_fixture.py; read from the
%   s22 ledger columns via the ledger_edb.py capability-export convention):
%     work_opened(Slug, RowId).             a work_opened row exists for Slug (RowId = its id).
%     work_closed(Slug, Resolution, RowId).  a work_closed row for Slug; Resolution in
%                                            {shipped,superseded,dropped,deferred}.
%     work_witness_present(RowId).          the work_closed row RowId carries a non-empty witness.
%     work_depends(Dependent, Antecedent, RowId). a work_depends_on row: Dependent (=its own
%                                            work_slug) depends on Antecedent (=work_depends_on).
#defined work_opened/2.
#defined work_closed/3.
#defined work_witness_present/1.
#defined work_depends/3.

% ---- duplicate_open (invariant 2; PROVABLY VACUOUS under normal operation -- s22's
% validate_work_item() refuses a second work_opened row for one slug at construction time; this
% predicate is defense-in-depth, matching the SQL floor's identical member) -------------------
work_duplicate_open(Slug) :- work_opened(Slug,R1), work_opened(Slug,R2), R1 != R2.

% ---- shipped_without_witness (invariant 3; PROVABLY VACUOUS under normal operation -- s22's
% work_shipped_requires_witness CHECK constraint refuses this at construction time; defense in
% depth, matching the SQL floor's identical member) --------------------------------------------
work_shipped_without_witness(Slug,R) :- work_closed(Slug,shipped,R), not work_witness_present(R).

% ---- depends_on_unknown_slug (invariant 4; GENUINELY REACHABLE -- s22 deliberately does not
% refuse a dangling antecedent at write time) ---------------------------------------------------
work_dep_edge(Dependent,Antecedent) :- work_depends(Dependent,Antecedent,_).
work_depends_on_unknown(Dependent,Antecedent) :-
    work_dep_edge(Dependent,Antecedent), not work_opened(Antecedent,_).

% ---- dependency_cycle (invariant 4, "the omega port"; GENUINELY REACHABLE) --------------------
work_dep_star(F,D) :- work_dep_edge(F,D).
work_dep_star(F,D) :- work_dep_edge(F,X), work_dep_star(X,D).
work_dependency_cycle(F) :- work_dep_star(F,F).

#show work_dep_edge/2.
#show work_dep_star/2.
#show work_duplicate_open/1.
#show work_shipped_without_witness/2.
#show work_depends_on_unknown/2.
#show work_dependency_cycle/1.
