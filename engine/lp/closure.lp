% ===========================================================================
% closure.lp -- the ONE kind-indexed transitive-closure module (design/ORCH-CATEGORICAL-
% REFACTOR-CONSULT-2026-07-15.md F3 / plan step 4): a single generic star(K,X,Y) over a
% kind-tagged edge(K,X,Y), following ledger_support.lp's existing support_edge/3 kind-tagged
% idiom (F3's own named in-house precedent -- "ledger_support.lp's kind-tagged support_edge/3
% idiom already proves the idiom in-house").
%
% WHY THIS EXISTS (F3). Ten SQL `WITH RECURSIVE` instances and four ASP `_star` pairs were each
% hand-authored per program (sup_star in ledger_tnow.lp, support_star in ledger_support.lp,
% work_dep_star in work_items.lp, the w_succ walk in work_review.lp, ordering_edge_star in
% ordering_violations.lp, reach in ledger_acts.lp). SQL cannot parameterize a recursive CTE over
% a relation NAME without dynamic SQL; ASP CAN -- a kind atom is an ordinary term -- so the
% closure functor is stated ONCE here, and a work-layer program becomes a thin edge-contributor
% plus a star/3 reader, never a second recursion skeleton (ADR-0012 P1 applied to the recursion
% itself, not merely to its edge sources).
%
% SCOPE (this pass): the module registry (engine/lp_registry.py, plan step 8) records which
% programs CONTRIBUTE edge/3 facts and which READ star/3 -- that registry, not a second prose
% copy here, is the one home of "who composes with this file." Per plan step 4, work_items.lp
% (kind `work_dep`) and work_review.lp (kind `work_succ`) are the first two contributors; each
% ALSO keeps its own historical #shown predicate (work_dep_star/2, the w_tree_member/2 walk) so
% every existing consumer's banked derivation stays byte-identical -- this module ADDS a second,
% registry-driven reading of the SAME closure (`work_dep_star_via_closure/2`,
% `work_succ_star_via_closure/2` in those files), it does not retract the first. A future pass
% that retires the duplicate hand-rolled recursion once every consumer's program list is updated
% is the natural next step (filed, not built this pass -- see the registry's own `requires` note).
%
% CONSUMERS contribute their own edges as edge(Kind,X,Y) facts/rules (one Kind atom per distinct
% edge semantics -- e.g. work_dep, work_succ) and read star(Kind,X,Y). A consumer wanting ONLY
% its own kind's closure filters on Kind; cross-kind reachability (a chain crossing two edge
% kinds) is a DELIBERATE non-goal of this module -- ordering_violations.lp's own
% ordering_edge_star (a union of two edge families INTO one relation before closing it) is a
% different, already-working composition and is not superseded by this file.
%
% NOT A NEW SEMANTICS: this module computes the identical mathematical object (the transitive
% closure of a binary relation) every existing `_star` predicate already computed by hand; it is
% the SAME closure, parameterized, never a new derivation rule. ZERO `:-` integrity constraints
% (the corpus's own paraconsistent idiom); a cyclic edge set stays SATISFIABLE (star(K,X,X) fires
% for every kind on its own cycle, exactly as sup_star/support_star/work_dep_star already do).
% ---------------------------------------------------------------------------
#defined edge/3.

star(K,X,Y) :- edge(K,X,Y).
star(K,X,Z) :- edge(K,X,Y), star(K,Y,Z).

#show star/3.
