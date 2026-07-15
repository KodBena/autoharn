% ===========================================================================
% work_items.lp -- the WORK-ITEM LEDGER violations layer (s22-work-item-ledger.sql;
% design/S22-WORK-ITEM-LEDGER.md, Fable-authored spec, session be693afb, 2026-07-09). ADDITIVE,
% DERIVED, engine-layer: the kernel (T_event, s22's DDL) gains no columns/verbs/semantics from
% this program -- it reasons over the s22 EDB (work_opened/2, work_closed/3, work_witness_present/1,
% work_depends/3), computing the SAME four judgments as work_item_violations (the SQL floor,
% work_item_floor_atoms in engine/ledger_floor.py), so the two producers differential
% bit-identically (spec witness protocol item 5: SQL floor vs .lp AGREE).
%
% SUPERSESSION (s31 -- kernel/lineage/s31-supersession-uniform-retraction.sql;
% design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md, RATIFIED 2026-07-15). This header's
% original premise -- "work-item events are never whole-row superseded/amended by design" (the s22
% spec's Q4 evidence) -- is SUPERSEDED on the record by that ratified spec: superseding a row of
% ANY kind now means uniform retraction from current truth, reinstatement-free. This program
% therefore COMPOSES with ledger_tnow.lp's supersession closure (`superseded/1`, derived there
% from supersedes/2) for its one current-truth judgment, work_orphaned_by_retraction below --
% loaded WITH ledger_tnow.lp over one shared EDB, or standalone (the `#defined superseded/1`
% guard makes an absent closure read as "nothing retracted", the fail-safe direction). The
% pre-existing judgments (duplicate opens, dangling deps, cycles, missing witnesses) deliberately
% KEEP their raw/history reading over ALL events, retracted or not -- they mirror
% work_item_violations' declared-history members byte-for-byte (duplicate_open is slug-burned by
% the spec's own ratified fork; the graph members answer "did this shape ever get written").
% Grounds standalone via the `#defined` guards below (an empty extension is silence, not a
% grounding warning -- the ledger_tnow.lp / why_layer.lp idiom).
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
%     work_claimed(Slug, RowId).            a work_claimed row exists for Slug (s31 addition --
%                                            needed only by work_orphaned_by_retraction below).
%     work_parent_edge(Child, Parent, RowId). Child's work_opened row (RowId) names Parent (the
%                                            s28 edge; s31 addition, same reason).
%     superseded(RowId).                     ledger_tnow.lp's supersession closure (composed, not
%                                            re-derived here -- ADR-0012 P1; absent when this
%                                            program runs standalone, which reads fail-safe as
%                                            "nothing retracted").
%
% CLOSURE.LP COMPOSITION (design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F3 / plan step
% 4; engine/lp_registry.py is the one home of the provides/requires declaration -- not restated
% here). This program CONTRIBUTES its dependency edge to the generic kind-indexed closure module
% as edge(work_dep,Dependent,Antecedent), and, when engine/lp/closure.lp is ALSO loaded, exposes
% the identical closure a second way via work_dep_star_via_closure/2 (READS star/3). The
% historical work_dep_star/2 rule below is UNCHANGED (ADDITIVE-ONLY per this file's own §1.6-
% style discipline) so every banked derivation that loads this program alone still reproduces
% byte-identical; a registry-aware consumer that also stacks closure.lp gets the SAME set through
% star/3 -- proven equal, not merely claimed, by the fixture the registry names.
#defined work_opened/2.
#defined work_closed/3.
#defined work_witness_present/1.
#defined work_depends/3.
#defined work_claimed/2.
#defined work_parent_edge/3.
#defined superseded/1.
#defined star/3.

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
% work_dep_star/2 is this program's own recursion (the derivation of record, kept byte-identical
% for every consumer that loads this file alone). edge/3 + work_dep_star_via_closure/2 is the
% SAME closure read through engine/lp/closure.lp's generic star/3 (see the header note above) --
% additive, never a replacement.
work_dep_star(F,D) :- work_dep_edge(F,D).
work_dep_star(F,D) :- work_dep_edge(F,X), work_dep_star(X,D).
work_dependency_cycle(F) :- work_dep_star(F,F).

edge(work_dep,Dependent,Antecedent) :- work_dep_edge(Dependent,Antecedent).
work_dep_star_via_closure(F,D) :- star(work_dep,F,D).

% ---- orphaned_by_retraction (s31; GENUINELY REACHABLE -- retracting an opening act while later
% events survive is legal, surfaced never refused). The ONE current-truth judgment in this
% program: an IN-FORCE (not superseded) later event whose slug has NO in-force opening act.
% Mirrors work_item_violations' four orphan_* CTEs exactly, one atom shape (Slug, the surviving
% row's id) covering all four sub-cases -- the row id disambiguates which event is orphaned. ----
work_opened_in_force(S) :- work_opened(S,R), not superseded(R).
work_orphaned_by_retraction(S,R) :- work_claimed(S,R),     not superseded(R), not work_opened_in_force(S).
work_orphaned_by_retraction(S,R) :- work_closed(S,_,R),    not superseded(R), not work_opened_in_force(S).
work_orphaned_by_retraction(S,R) :- work_depends(S,_,R),   not superseded(R), not work_opened_in_force(S).
work_orphaned_by_retraction(C,R) :- work_parent_edge(C,P,R), not superseded(R), not work_opened_in_force(P).

#show work_dep_edge/2.
#show work_dep_star/2.
#show work_dep_star_via_closure/2.
#show work_duplicate_open/1.
#show work_shipped_without_witness/2.
#show work_depends_on_unknown/2.
#show work_dependency_cycle/1.
#show work_orphaned_by_retraction/2.
