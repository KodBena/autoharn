% ===========================================================================
% ordering_violations.lp -- design/ORCH-SPEC-RESOURCE-REGISTRY.md §5 stage 2: "the
% ordering-violations checker" (the spec's own name), over the work-item EDB (s22's
% work_opened/work_closed/work_depends_on rows, engine/ordering_edb.py) PLUS the `constraint:`
% convention rows design/USER-BLESSED-TABLE-TEMPLATE.md already shipped at stage 1
% (`constraint: precedes <slug-1> <slug-2> [<slug-n>...]` / `constraint: excludes ...`).
%
% NON-DUPLICATION (read this before touching anything below). §5's own text names three
% checks: "close-before-dependency (the verified missing check), conditional-precedence
% violations, and the existing cycle check re-derived." The tracker item that commissioned this
% file is explicit that Part 3's engine/lp/preamble_ordering.lp ALREADY covers three adjacent
% checks and this file must NOT rebuild them:
%   * F5 ob_open_before_claim   -- work_opened id < work_claimed id, per slug.
%   * F6 ob_claim_before_close  -- work_claimed id < work_closed id, per slug.
%   * F11's s22_violation arm's dangling-dependency member (work_depends_on_unknown, imported
%     from engine/lp/work_items.lp) -- an antecedent slug that was NEVER OPENED at all.
% This file's three checks are the RESIDUE, and are scoped to partition cleanly against those
% three rather than re-report the same defect under a second name:
%
%   1. close_before_dependency -- a Dependent CLOSES while an Antecedent it depends on has NOT
%      itself closed FIRST (id order). Guarded on `work_opened(Antecedent,_)` -- a dangling
%      antecedent (no work_opened row at all) is F11's own concern, not duplicated here; this
%      family's trigger simply does not fire for a dangling antecedent, so the two checkers
%      partition the failure space instead of double-reporting one defect under two names.
%      HONEST CAVEAT (found by an out-of-frame review, not silently left): F11's coverage of the
%      dangling-antecedent case is TIME-GATED, not unconditional -- preamble_ordering.lp's F11
%      rules (`ob_violated(f11,ST) :- stop_event(_,ST), s22_violation.` and its undecidable
%      sibling) both require a `stop_event` fact to exist, and f11 is ABSENT from that program's
%      own `ob_family_forced_undecidable/2` enumeration -- so on a world/session with ZERO
%      stop_event facts on record (mid-session, before any Stop), F11's family verdict falls
%      through to `vacuous`, not `undecidable`. In that window a real
%      dangling-dependency-plus-early-close defect is visible to NEITHER checker at the
%      OBSERVER layer (`./audit --preamble` / `./audit --ordering`, both explicitly
%      visible-only, gate nothing). This is NOT a live-safety gap: the write-time enforcement
%      hook (hooks/stop_clean_exit.py) queries `work_item_violations` (which includes
%      `depends_on_unknown_slug`) directly via SQL at every actual Stop attempt, unconditioned on
%      any EDB stop_event fact -- a session cannot actually EXIT with this defect present. The
%      gap is confined to the mid-session, human-run report, which is what an observer-only tool
%      is; it is named here so "not duplicated here" is never mistaken for "fully covered at all
%      times."
%   2. conditional_precedence -- a `constraint: precedes A B [C...]` row (parsed PAIRWISE into a
%      chain A-before-B, B-before-C, ... -- an executor scope decision, since the spec's own
%      grammar names N slugs without stating an N>2 semantics; a chain is the natural reading of
%      "precedes" applied left-to-right, and is what design/USER-BLESSED-TABLE-TEMPLATE.md's own
%      two-slug worked example degenerates to) violated: B closes while A has not itself closed
%      first. `excludes` rows are RECOGNIZED (engine/ordering_edb.py emits
%      constraint_excludes_deferred/1 for them) but NOT CHECKED this pass -- a named residue, not
%      a silent drop: the tracker item's own text names only "conditional-precedence", not mutual
%      exclusion, and BACKLOG.md records the deferral.
%   3. dependency_cycle -- RE-DERIVED (§5's own word) over the UNION of work_depends edges AND
%      constraint_precedes edges -- a strict SUPERSET of engine/lp/work_items.lp's own
%      work_dependency_cycle/1 (which sees ONLY work_depends edges, never a precedes edge). On a
%      world with zero constraint_precedes facts the two checks' findings COINCIDE exactly (an
%      EXPECTED overlap, named here so it does not read as an accidental duplicate); the
%      difference manifests only once a precedes edge closes a cycle spanning BOTH edge
%      families, which work_items.lp's own cycle check structurally cannot see (it never loads
%      constraint_precedes at all).
%
% HOUSE CONVENTIONS (matching engine/lp/work_items.lp and engine/lp/preamble_ordering.lp
% identically): zero `:-` integrity constraints (paraconsistent -- a violating record stays
% SATISFIABLE and reportable, never a refusal-to-solve); NAF confined to the named "not yet
% closed first" / "no cycle" seams below; base relations FIRST-CLASS #shown (non-foreclosure --
% a consumer builds its own report from these without touching the rules); a closed
% FAMILY-verdict layer (ordering_verdict/2, discharged|violated|undecidable|vacuous) grounded by
% engine/ordering_obligations.lp's ordering_family/1 so an EMPTY or PRE-S22 world still emits all
% THREE family verdicts, never silence (the F49 vacuous-pass class). Statements are about the
% RECORD'S SHAPE ("the discharging record is absent"), never a conviction of conduct --
% adjudicating what a violation MEANS is the human/ratifier act downstream, this program's own
% job stops at the derived flag (preamble_ordering.lp §5, verbatim in spirit).
%
% VISIBLE-ONLY (§5's own word): this program gates nothing. It is read by engine/ordering_audit.py
% (wired into `./audit --ordering`), never by a write-time hook.
% ---------------------------------------------------------------------------
#defined work_opened/2.
#defined work_closed/3.
#defined work_depends/3.
#defined constraint_precedes/3.
#defined constraint_precedes_unparsed/1.
#defined constraint_excludes_deferred/1.
#defined capable/1.
#defined any_row/1.
#defined ordering_family/1.

any_ledger_row :- any_row(_).

% ===========================================================================
% 1 -- close_before_dependency (the verified missing check: s22 carries work_depends edges but
% nothing checks that a CLOSE respects them).
% ===========================================================================
cbd_trigger(DepRowId,Dependent,Antecedent,CloseId) :-
    work_depends(Dependent,Antecedent,DepRowId), work_closed(Dependent,_,CloseId),
    work_opened(Antecedent,_).
cbd_antecedent_closed_first(DepRowId) :-
    cbd_trigger(DepRowId,_,Antecedent,CloseId), work_closed(Antecedent,_,AntCloseId),
    AntCloseId < CloseId.
close_before_dependency_discharged(DepRowId,Dependent,Antecedent) :-
    cbd_trigger(DepRowId,Dependent,Antecedent,_), cbd_antecedent_closed_first(DepRowId).
close_before_dependency_violated(DepRowId,Dependent,Antecedent) :-
    cbd_trigger(DepRowId,Dependent,Antecedent,_), not cbd_antecedent_closed_first(DepRowId).

% ===========================================================================
% 2 -- conditional_precedence (constraint: precedes rows -- design/USER-BLESSED-TABLE-TEMPLATE.md).
% ===========================================================================
cp_trigger(RowId,SlugA,SlugB,CloseB) :-
    constraint_precedes(SlugA,SlugB,RowId), work_closed(SlugB,_,CloseB).
cp_a_closed_first(RowId,SlugA,SlugB) :-
    cp_trigger(RowId,SlugA,SlugB,CloseB), work_closed(SlugA,_,CloseA), CloseA < CloseB.
conditional_precedence_discharged(RowId,SlugA,SlugB) :-
    cp_trigger(RowId,SlugA,SlugB,_), cp_a_closed_first(RowId,SlugA,SlugB).
conditional_precedence_violated(RowId,SlugA,SlugB) :-
    cp_trigger(RowId,SlugA,SlugB,_), not cp_a_closed_first(RowId,SlugA,SlugB).

% ===========================================================================
% 3 -- dependency_cycle (re-derived, union of BOTH edge families -- see header).
% ===========================================================================
ordering_edge(Dependent,Antecedent) :- work_depends(Dependent,Antecedent,_).
ordering_edge(SlugB,SlugA) :- constraint_precedes(SlugA,SlugB,_).
ordering_edge_star(F,D) :- ordering_edge(F,D).
ordering_edge_star(F,D) :- ordering_edge(F,X), ordering_edge_star(X,D).
dependency_cycle(F) :- ordering_edge_star(F,F).

% ===========================================================================
% Per-family aggregates + the forced-undecidable escape hatch (pre_s22: the s22 work-item
% columns this whole program reasons over do not exist on this schema at all -- named UNDECIDABLE
% at the family level whenever OTHER ledger activity is on record, never silently VACUOUS, the
% same discipline preamble_ordering.lp's own ob_family_forced_undecidable/2 uses).
% ===========================================================================
ordering_violated_any(close_before_dependency) :- close_before_dependency_violated(_,_,_).
ordering_discharged_any(close_before_dependency) :- close_before_dependency_discharged(_,_,_).
ordering_forced_undecidable(close_before_dependency,pre_s22) :- not capable(work_items), any_ledger_row.

ordering_violated_any(conditional_precedence) :- conditional_precedence_violated(_,_,_).
ordering_discharged_any(conditional_precedence) :- conditional_precedence_discharged(_,_,_).
ordering_undecidable_any(conditional_precedence) :- constraint_precedes_unparsed(_).
% NOTE this family's forced-undecidable guard is scoped to constraint_precedes existing (not to
% "any ledger row"): a `constraint:` decision row needs no s22 column at all to be WRITTEN, so a
% pre-s22 world with zero constraint: declarations is honestly VACUOUS (nothing declared), never
% UNDECIDABLE -- only a pre-s22 world that DOES carry a parsed precedes edge is genuinely
% undecidable (it declared an ordering it cannot be checked against, for lack of work_closed).
ordering_forced_undecidable(conditional_precedence,pre_s22) :-
    not capable(work_items), constraint_precedes(_,_,_).

ordering_violated_any(dependency_cycle) :- dependency_cycle(_).
ordering_discharged_any(dependency_cycle) :- ordering_edge(_,_), not dependency_cycle(_).
ordering_forced_undecidable(dependency_cycle,pre_s22) :- not capable(work_items), any_ledger_row.

% ===========================================================================
% THE FAMILY-STRATUM VERDICT LADDER (never silence; loudest-first: violated > undecidable >
% forced-undecidable > discharged > vacuous -- identical priority to preamble_ordering.lp's own).
% ===========================================================================
ordering_verdict(F,violated) :- ordering_violated_any(F).
ordering_verdict(F,undecidable) :- not ordering_violated_any(F), ordering_undecidable_any(F).
ordering_verdict(F,undecidable) :- not ordering_violated_any(F), not ordering_undecidable_any(F),
    ordering_forced_undecidable(F,_), ordering_family(F).
ordering_verdict(F,discharged) :- not ordering_violated_any(F), not ordering_undecidable_any(F),
    not ordering_forced_undecidable(F,_), ordering_discharged_any(F).
ordering_verdict(F,vacuous) :- ordering_family(F),
    not ordering_violated_any(F), not ordering_undecidable_any(F),
    not ordering_forced_undecidable(F,_), not ordering_discharged_any(F).

#show cbd_trigger/4.
#show close_before_dependency_discharged/3.
#show close_before_dependency_violated/3.
#show cp_trigger/4.
#show conditional_precedence_discharged/3.
#show conditional_precedence_violated/3.
#show ordering_edge/2.
#show ordering_edge_star/2.
#show dependency_cycle/1.
#show ordering_undecidable_any/1.
#show ordering_forced_undecidable/2.
#show ordering_verdict/2.
