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
#defined work_dep_type/2.
#defined w_vdisp/3.
#defined w_vdisp_resolution/2.
#defined w_vdisp_witness_present/1.
#defined w_vdisp_witness_in_force/1.

% ---- duplicate_open (invariant 2; PROVABLY VACUOUS under normal operation -- s22's
% validate_work_item() refuses a second work_opened row for one slug at construction time; this
% predicate is defense-in-depth, matching the SQL floor's identical member). NOT disposition-
% narrowed: this predicate's own atom shape (Slug only) carries no target_id, and the kernel
% view's own target_id for this class is the slug's own work_opened row id (a builder DESIGN
% CHOICE named in s37's own header, not a fact this EDB exports as a distinct id) -- a NAMED,
% disclosed gap (matching dependency_cycle/dangling_parent/parent_cycle/blocks_close_cycle
% below), not a silent omission: disposing THIS class is reachable only via a trigger-bypass
% negative-control write (s37's own closure statement), never ordinary operation. --------------
work_duplicate_open(Slug) :- work_opened(Slug,R1), work_opened(Slug,R2), R1 != R2.

% ---- shipped_without_witness (invariant 3; PROVABLY VACUOUS under normal operation -- s22's
% work_shipped_requires_witness CHECK constraint refuses this at construction time; defense in
% depth, matching the SQL floor's identical member). s37 fix (reviewer defect 4, ADR-0014-review
% round): disposition-narrowed like every OTHER id-bearing class -- w_vdisp_basis_holds/3 is
% GENERAL (see below), not hardcoded to one class, so this predicate inherits the SAME narrowing
% the kernel VIEW already applies uniformly, for free. --------------------------------------
work_shipped_without_witness(Slug,R) :-
    work_closed(Slug,shipped,R), not work_witness_present(R),
    not w_vdisp_basis_holds(shipped_without_witness,R,_).

% ---- depends_on_unknown_slug (invariant 4; GENUINELY REACHABLE -- s22 deliberately does not
% refuse a dangling antecedent at write time). work_dep_edge/2 (below) stays the GENERAL,
% id-less graph edge -- UNCHANGED, still the derivation of record for depends_on_unknown_slug's
% OWN unnarrowed sibling relation (the dependency GRAPH) and for work_dep_star/2's closure. s37
% fix (reviewer defects 1 + 4, ADR-0014-review round): the VIOLATIONS predicate reads
% work_depends/3 directly instead of through work_dep_edge/2, so the depending act's OWN row id
% (R) is available to key a disposition against -- mirroring the kernel fix (deps/dangling_dep
% gain `id`, kernel/lineage/s37-violation-disposition.sql) exactly: without R, this class's
% target_id was hardcoded NULL there and permanently unanswerable (defect 1); without the
% narrowing join here, a disposed instance would still show up in ASP after the kernel VIEW
% dropped it, a silent DIVERGE (defect 4). Same set as `work_dep_edge(Dependent,Antecedent) :-
% work_depends(Dependent,Antecedent,_), not work_opened(Antecedent,_)` would produce -- only the
% id-threading and the narrowing join are new. -------------------------------------------------
work_dep_edge(Dependent,Antecedent) :- work_depends(Dependent,Antecedent,_).
work_depends_on_unknown(Dependent,Antecedent) :-
    work_depends(Dependent,Antecedent,R), not work_opened(Antecedent,_),
    not w_vdisp_basis_holds(depends_on_unknown_slug,R,_).

% ---- dependency_cycle (invariant 4, "the omega port"). work_dep_star/2 (below) is the GENERAL,
% ALL-edge-type recursion -- UNCHANGED, byte-for-byte, still the derivation of record for the
% dependency GRAPH (depends_on_unknown_slug above deliberately reads every edge type too, and
% every consumer of work_dep_star/2 alone keeps reproducing byte-identical). s37
% (kernel/lineage/s37-violation-disposition.sql, RATIFIED sibling narrowing, consult A1(b)):
% the VIOLATIONS predicate work_dependency_cycle/1 now narrows to a SEPARATE, blocks-close-ONLY
% closure (work_dep_star_bc/2) -- blocks-close cycles are already refused at construction (s30),
% so this predicate becomes properly vacuous, defense-in-depth, matching work_dep_edge's own
% sibling s22 members' vacuous posture; an informs cycle is now a legal non-event (informs never
% gates, s30's own text), matching the SQL floor's identical narrowing. work_dep_type/2 is
% capability-gated (#defined above) -- a pre-s30 exporter emits none, so work_dep_edge_bc/2 (and
% therefore work_dependency_cycle/1) is vacuously empty on a pre-s30 target, the SAME fail-safe
% direction every other capability-gated family in this program already takes.
work_dep_star(F,D) :- work_dep_edge(F,D).
work_dep_star(F,D) :- work_dep_edge(F,X), work_dep_star(X,D).

work_dep_edge_bc(Dependent,Antecedent) :- work_depends(Dependent,Antecedent,R), work_dep_type(R,"blocks-close").
work_dep_star_bc(F,D) :- work_dep_edge_bc(F,D).
work_dep_star_bc(F,D) :- work_dep_edge_bc(F,X), work_dep_star_bc(X,D).
work_dependency_cycle(F) :- work_dep_star_bc(F,F).

edge(work_dep,Dependent,Antecedent) :- work_dep_edge(Dependent,Antecedent).
work_dep_star_via_closure(F,D) :- star(work_dep,F,D).

% ---- THE DISPOSITION-NARROWING JOIN, GENERALIZED (s37 fix, reviewer defect 4, ADR-0014-review
% round: w_vdisp_in_force/w_vdisp_basis_holds were HARDCODED to the literal atom
% `orphaned_by_retraction` in the first draft, while the kernel VIEW's own anti-join
% (kernel/lineage/s37-violation-disposition.sql, the FINAL `WHERE NOT EXISTS` after raw_violations'
% UNION ALL) is UNIFORM over every arm that carries a real target_id -- a future SQL-side member
% gaining a real target_id (as depends_on_unknown_slug and shipped_without_witness both do, this
% SAME fix) would then narrow in the kernel VIEW but NOT in ASP, a silent DIVERGE_DEFECT `./judge`
% would have no way to catch on its own (the mismatch IS what judge exists to catch, but a
% class-hardcoded join can never even LOOK at a class it wasn't told about). Fixed by making Class
% a VARIABLE throughout -- these two predicates now match the kernel's disposition_basis_holds
% CTE literally, clause for clause, independent of which violation class calls them. s37 fix
% (reviewer defect, post-first-draft: the kernel's disposition_basis_holds CTE JOINs
% ledger_current t ON t.id = d.target_id, i.e. the TARGET row itself must be current --
% w_vdisp_basis_holds/3 lacked this precondition, so a disposition whose target row was later
% superseded (e.g. the depends_on_unknown_slug or shipped_without_witness target, neither of
% which re-checks currency in its own raw derivation the way work_orphaned_by_retraction_raw
% does) would still narrow the violation in ASP after the kernel VIEW had already stopped
% narrowing it -- a silent DIVERGE_DEFECT. Fixed by adding `not superseded(R)` as a shared
% precondition to all four rules below, mirroring the kernel's `JOIN ledger_current t` literally).
% `retired` holds while the target row itself is current AND (if the target IS an opening row,
% work_opened(Slug,R)) its slug currently reads closed (an in-force work_closed row for that
% slug). `reissued` holds while no witness was cited, or the cited witness row is itself
% still in force. THREE CALLERS below (work_orphaned_by_retraction, work_depends_on_unknown above,
% work_shipped_without_witness above) -- the NAMED, disclosed exception is duplicate_open/
% dependency_cycle/dangling_parent/parent_cycle/blocks_close_cycle, whose atom shape carries no id
% at all (see work_duplicate_open's own comment). --------------------------------------------
w_vdisp_in_force(Class,R,Disp) :- w_vdisp(Class,R,Disp), not superseded(Disp).

w_vdisp_basis_holds(Class,R,Disp) :-
    w_vdisp_in_force(Class,R,Disp), w_vdisp_resolution(Disp,retired),
    not superseded(R),
    work_opened(Slug,R), work_closed(Slug,_,CloseR), not superseded(CloseR).
w_vdisp_basis_holds(Class,R,Disp) :-
    w_vdisp_in_force(Class,R,Disp), w_vdisp_resolution(Disp,retired),
    not superseded(R),
    not work_opened(_,R).
w_vdisp_basis_holds(Class,R,Disp) :-
    w_vdisp_in_force(Class,R,Disp), w_vdisp_resolution(Disp,reissued),
    not superseded(R),
    not w_vdisp_witness_present(Disp).
w_vdisp_basis_holds(Class,R,Disp) :-
    w_vdisp_in_force(Class,R,Disp), w_vdisp_resolution(Disp,reissued),
    not superseded(R),
    w_vdisp_witness_present(Disp), w_vdisp_witness_in_force(Disp).

% ---- orphaned_by_retraction (s31; GENUINELY REACHABLE -- retracting an opening act while later
% events survive is legal, surfaced never refused). The ONE current-truth judgment in this
% program: an IN-FORCE (not superseded) later event whose slug has NO in-force opening act.
% Mirrors work_item_violations' four orphan_* CTEs exactly, one atom shape (Slug, the surviving
% row's id) covering all four sub-cases -- the row id disambiguates which event is orphaned.
% work_orphaned_by_retraction_raw/2 is this UNCHANGED, byte-for-byte, four-rule derivation. s37 --
% ONE MORE JOIN, narrowing the SAME predicate name (matching s33's own w_tree_unresolved narrowing
% precedent, "no new predicate NAME, only a changed extension"), now via the GENERALIZED
% w_vdisp_basis_holds/3 above. -------------------------------------------------------------------
work_opened_in_force(S) :- work_opened(S,R), not superseded(R).
work_orphaned_by_retraction_raw(S,R) :- work_claimed(S,R),     not superseded(R), not work_opened_in_force(S).
work_orphaned_by_retraction_raw(S,R) :- work_closed(S,_,R),    not superseded(R), not work_opened_in_force(S).
work_orphaned_by_retraction_raw(S,R) :- work_depends(S,_,R),   not superseded(R), not work_opened_in_force(S).
work_orphaned_by_retraction_raw(C,R) :- work_parent_edge(C,P,R), not superseded(R), not work_opened_in_force(P).

work_orphaned_by_retraction(S,R) :-
    work_orphaned_by_retraction_raw(S,R),
    not w_vdisp_basis_holds(orphaned_by_retraction,R,_).

#show work_dep_edge/2.
#show work_dep_star/2.
#show work_dep_star_via_closure/2.
#show work_duplicate_open/1.
#show work_shipped_without_witness/2.
#show work_depends_on_unknown/2.
#show work_dependency_cycle/1.
#show work_orphaned_by_retraction/2.
#show work_orphaned_by_retraction_raw/2.
