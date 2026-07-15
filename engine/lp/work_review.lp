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
% THIS PROGRAM STANDS ALONE (no ledger_tnow.lp load-on-top; mirrors work_items.lp's own standing-
% alone posture, s22) -- a work-item close is never whole-row superseded/amended by design (the
% s22 lesson, unchanged by s29).
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
#defined w_opened/1.
#defined w_parent/2.
#defined w_closed/3.
#defined w_disposition/2.
#defined w_discharged/1.
#defined w_dep/2.

% ---- the ONE combined successor relation (mirrors the SQL floor's `edges` CTE): an s28 w_parent
% edge walks parent->child literally; a w_dep edge walks OPPOSITE its own argument order (the
% dependent plays the "parent" role, its antecedent plays the "child" role -- see header) --------
w_succ(Parent,Child) :- w_parent(Child,Parent).
w_succ(Dependent,Antecedent) :- w_dep(Dependent,Antecedent).

% ---- tree membership: Root's tree is {Root} union every transitive successor via w_succ --------
w_tree_member(Root,Root) :- w_opened(Root).
w_tree_member(Root,C) :- w_tree_member(Root,P), w_succ(P,C).

% ---- own-leaf unresolved: a slug's OWN close row is deferred and not yet discharged ------------
w_own_leaf_unresolved(Slug) :-
    w_closed(Slug,R,_), w_disposition(R,deferred), not w_discharged(R).

% ---- a tree member (other than the root itself) with no work_closed row at all -----------------
w_not_closed(Slug) :- w_opened(Slug), not w_closed(Slug,_,_).

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
