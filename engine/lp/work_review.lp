% ===========================================================================
% work_review.lp -- the s29 TYPED-CLOSE / OBLIGATION-TREE resolution layer
% (kernel/lineage/s29-obligation-item-key-and-typed-close.sql; design/
% MAINT-COUNTERSIGN-CLOSE-SEMANTICS-SPEC.md, Fable-authored spec, RATIFIED 2026-07-14). ADDITIVE,
% DERIVED, engine-layer: the kernel gains no columns/verbs/semantics from this program -- it
% reasons over the s29 EDB (below), computing the SAME judgments as
% work_item_strict_blockers()/work_review_gap (the SQL floor, work_review_floor_atoms in
% engine/ledger_floor.py), so the two producers differential bit-identically (this delta's own
% scratch fixture: SQL floor vs .lp AGREE).
%
% SUPERSESSION (s31 -- kernel/lineage/s31-supersession-uniform-retraction.sql;
% design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md, RATIFIED 2026-07-15). This header's
% original premise -- "a work-item close is never whole-row superseded/amended by design" (the
% s22 lesson, carried into s29) -- is SUPERSEDED on the record by that ratified spec: superseding
% a row of ANY kind is uniform retraction from current truth, reinstatement-free. This program
% now COMPOSES with ledger_tnow.lp's supersession closure (`superseded/1`): in-force work events
% ONLY feed the tree/close state derivation below, exactly mirroring the SQL twin's s31 re-issue
% (work_item_strict_blockers()'s edges/closes CTEs now read ledger_current). Loaded WITH
% ledger_tnow.lp over one shared EDB, or standalone (the `#defined superseded/1` guard makes an
% absent closure read fail-safe as "nothing retracted" -- pre-s31 fixtures keep grounding and
% keep their pre-s31 meaning). The w_discharged/1 leg is UNCHANGED: the discharge-review side was
% already in-force-filtered at its source (the spec's own sec-2 finding), on both producers.
%
% TEXT STAYS HOME (design rule, ledger_edb.py rule 1): work_review_ref (prose / a free-text
% reference) does NOT cross into this EDB -- only the SLUG, the ROW ID (an opaque identifier,
% never prose), and the closed-vocabulary DISPOSITION atom cross.
%
% CORRECTED (out-of-frame hack-rationalization audit, same session, before this file's first
% commit -- caught, not shipped): a first draft's `w_tree_member` walked ONLY the s28 `w_parent`
% edge, and `w_dep_unresolved` treated a `work_depends_on` antecedent as resolved the moment it had
% ANY `w_closed` row -- a one-hop "is it closed" check standing in for "is it RESOLVED" (spec
% sec-5's own text: "Interior nodes resolve derivationally as the conjunction of their children --
% children via `work_depends_on`, the s28 parent edge, AND the obligations keyed to the item"). THE
% FIX (a type, not a special case, ADR-0000 Rule 2(a)): `w_tree_member` now walks BOTH edge kinds
% TRANSITIVELY and UNIFORMLY -- a `work_depends_on` antecedent is a full tree member exactly like
% an s28 child, so its OWN leaf resolution (and its own further antecedents/children, recursively)
% is checked, not merely its existence. This mirrors kernel/lineage/s29-...sql's
% `work_item_strict_blockers()`'s identical correction, made in the SAME session, exact same
% direction fix (a `work_depends_on` edge is walked OPPOSITE its own column names: the dependent
% plays the "parent" role in tree-membership terms, its antecedent plays the "child" role).
%
% NON-FORECLOSURE (the ledger_support.lp / work_items.lp acceptance-criteria shape, applied here):
%   * base relations (w_tree_member/2, w_own_leaf_unresolved/1, w_not_closed/1,
%     w_tree_unresolved/1) are FIRST-CLASS #shown outputs -- a consumer builds its own policy
%     from them.
%   * NO verdict vocabulary over the work item's TRUTH: these are statements about the OBLIGATION
%     GRAPH (an undischarged deferred review, an unclosed tree member), descriptive names only,
%     mirroring work_items.lp's own restraint.
%   * ZERO `:-` integrity constraints (the corpus's paraconsistent idiom). A record with an
%     unresolved leaf stays SATISFIABLE and queryable -- the strict-mode REFUSAL itself lives only
%     in the kernel trigger (validate_work_item -- a write-boundary act), never here (this program
%     answers "what is unresolved", never "refuse this write").
%   * The NAF seam is confined to `w_own_leaf_unresolved` (`not w_discharged(RowId)`) and
%     `w_not_closed`/`w_tree_unresolved`'s "not yet closed" checks (`not w_closed(Slug,_,_)`),
%     mirroring work_items.lp's own NAF confinement to its two genuinely-reachable members.
% ---------------------------------------------------------------------------
%   EDB (kernel/fixtures/ or seen-red/s29-.../ scratch fixture; engine/ledger_floor.py's SQL-side
%   mirror reads the identical facts directly off the s29 ledger columns):
%     w_opened(Slug).                       a work_opened row exists for Slug.
%     w_parent(Child, Parent).              Child's work_opened row names Parent (s28 edge).
%     w_closed(Slug, RowId, Closer).        a work_closed row for Slug; RowId = its ledger id;
%                                            Closer = the closing actor's principal id.
%     w_disposition(RowId, witnessed).      the work_closed row RowId carries disposition=witnessed.
%     w_disposition(RowId, deferred).       the work_closed row RowId carries disposition=deferred.
%     w_discharged(RowId).                  a distinct-actor attest review regards RowId (the SAME
%                                            join shape work_review_gap's own SQL uses: verdict=
%                                            attest, actor<>closer, not superseded).
%     w_dep(Dependent, Antecedent).         a work_depends_on row: Dependent depends on Antecedent.
%     w_open(Slug, RowId).                  s31: a work_opened row (RowId) exists for Slug -- the
%                                            row-id-carrying form w_opened/1 is now DERIVED from,
%                                            in-force only (below).
%     w_parent_e(Child, Parent, RowId).     s31: the row-id-carrying s28 edge; w_parent/2 is now
%                                            derived from it, in-force only.
%     w_dep_e(Dependent, Antecedent, RowId). s31: the row-id-carrying dependency edge; w_dep/2 is
%                                            now derived from it, in-force only.
%     superseded(RowId).                    ledger_tnow.lp's supersession closure (composed, not
%                                            re-derived -- ADR-0012 P1).
%     w_composite(Slug).                    s33 (kernel/lineage/s33-composite-discharge.sql;
%                                            design/FABLE-COMPOSITE-DISCHARGE-SPEC.md, RATIFIED
%                                            2026-07-15): Slug's OWN work_opened row (in force)
%                                            carries work_discharge='composite'.
%
% s33 COMPOSITE-DISCHARGE EXTENSION (design/FABLE-COMPOSITE-DISCHARGE-SPEC.md sec-3, "no second
% tree walker" -- the derivation is a READ of this SAME conjunction, extended once, here). A
% composite tree member with AT LEAST ONE CHILD in this SAME `w_succ` walk is resolved through
% ITS OWN children (already tree members here, already separately contributing their own
% w_own_leaf_unresolved/w_not_closed facts to the SAME w_tree_unresolved derivation below) -- it
% never additionally requires its own w_closed row. A composite with ZERO children is NOT
% exempted (never vacuously discharged). This is the INDEPENDENT ASP twin of the SQL floor's
% identical `not_closed` extension (engine/ledger_floor.py's work_review_floor_atoms) and the DDL
% kernel's identical `work_item_strict_blockers()` extension (s33) -- three independent
% derivations of the SAME rule, per the standing do-not-abstract (I6) ruling, never shared code.
%
% CLOSURE.LP COMPOSITION (design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F3 / plan step
% 4; engine/lp_registry.py is the one home of the provides/requires declaration -- not restated
% here). This program CONTRIBUTES its combined successor edge (w_succ -- see the direction note
% above) to the generic kind-indexed closure module as edge(work_succ,Parent,Child), and, when
% engine/lp/closure.lp is ALSO loaded, exposes the pairwise closure a second way via
% work_succ_star_via_closure/2 (READS star/3). The historical w_tree_member/2 walk below is
% UNCHANGED (ADDITIVE-ONLY) so every banked derivation that loads this program alone still
% reproduces byte-identical.
#defined w_opened/1.
#defined w_parent/2.
#defined w_closed/3.
#defined w_disposition/2.
#defined w_discharged/1.
#defined w_dep/2.
#defined w_open/2.
#defined w_parent_e/3.
#defined w_dep_e/3.
#defined superseded/1.
#defined star/3.
#defined w_composite/1.

% ---- s31: the in-force projections (one factoring, mirroring SQL's ledger_current reads). A
% pre-s31 fixture that supplies w_opened/1 / w_parent/2 / w_dep/2 facts DIRECTLY still grounds
% (additive; those facts are then un-filtered, exactly the pre-s31 reading it was banked under).
w_opened(S)    :- w_open(S,R),       not superseded(R).
w_parent(C,P)  :- w_parent_e(C,P,R), not superseded(R).
w_dep(D,A)     :- w_dep_e(D,A,R),    not superseded(R).
w_closed_in_force(S,R,C) :- w_closed(S,R,C), not superseded(R).

% ---- the ONE combined successor relation (mirrors the SQL floor's `edges` CTE): an s28 w_parent
% edge walks parent->child literally; a w_dep edge walks OPPOSITE its own argument order (the
% dependent plays the "parent" role, its antecedent plays the "child" role -- see header) --------
w_succ(Parent,Child) :- w_parent(Child,Parent).
w_succ(Dependent,Antecedent) :- w_dep(Dependent,Antecedent).

% ---- tree membership: Root's tree is {Root} union every transitive successor via w_succ --------
% w_tree_member/2 is this program's own recursion (the derivation of record, kept byte-identical
% for every consumer that loads this file alone). edge/3 + work_succ_star_via_closure/2 is the
% SAME pairwise closure read through engine/lp/closure.lp's generic star/3 (see the header note
% above) -- additive, never a replacement; note star/3 has no reflexive Root-to-itself atom
% (closure.lp computes the pure edge closure, never a member's own tree membership over itself),
% so the equivalence a consumer checks is w_tree_member(Root,C), C != Root <-> star(work_succ,Root,C).
w_tree_member(Root,Root) :- w_opened(Root).
w_tree_member(Root,C) :- w_tree_member(Root,P), w_succ(P,C).

edge(work_succ,Parent,Child) :- w_succ(Parent,Child).
work_succ_star_via_closure(F,D) :- star(work_succ,F,D).

% ---- own-leaf unresolved: a slug's OWN IN-FORCE close row is deferred and not yet discharged
% (s31: a retracted close is no unresolved leaf -- the item simply reads not-closed again) -------
w_own_leaf_unresolved(Slug) :-
    w_closed_in_force(Slug,R,_), w_disposition(R,deferred), not w_discharged(R).

% ---- a tree member (other than the root itself) with no IN-FORCE work_closed row (s31) ---------
% s33: exempted when the member is itself a composite WITH at least one child in this walk (see
% the extension note above the EDB list) -- its resolution is delegated to its own children.
w_closed_any(Slug) :- w_closed_in_force(Slug,_,_).
w_composite_with_children(Slug) :- w_composite(Slug), w_succ(Slug,_).
w_not_closed(Slug) :- w_opened(Slug), not w_closed_any(Slug), not w_composite_with_children(Slug).

% ---- tree-level unresolved (Element C's derived conjunction, negated): Root's obligation tree is
% UNRESOLVED iff any tree member (Root itself, or a transitive successor via EITHER edge kind) has
% an unresolved own-leaf, or -- for a non-root member -- is not itself closed yet. Mirrors
% work_item_strict_blockers()'s own two UNION members exactly, one column over (predicate, not
% row set) -----------------------------------------------------------------------------------
w_tree_unresolved(Root) :- w_tree_member(Root,M), w_own_leaf_unresolved(M).
w_tree_unresolved(Root) :- w_tree_member(Root,M), M != Root, w_not_closed(M).

#show w_tree_member/2.
#show w_own_leaf_unresolved/1.
#show w_tree_unresolved/1.
#show work_succ_star_via_closure/2.
