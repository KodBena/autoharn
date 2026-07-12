% ===========================================================================
% preamble_ordering.lp -- Part 3 of design/ORCH-CONTEMPORANEITY-PART3-SPEC.md: the governance
% preamble's ordering obligations (bootstrap/templates/CLAUDE.md.tmpl, the twelve numbered points
% every scaffolded world receives at birth) as one deontic/temporal ASP program, F1-F12, inside
% the settled Anderson-reduction frame (spec §1: obligations are recorded facts -- E8's
% preamble_obligation/2 -- violations are derived flags, no modal operators; ordering is over
% recorded events via id-is-order + the two-clock bridge, never a temporal modal logic).
%
% LOAD ORDER (spec §4, the ledger_assumes.lp-on-tnow precedent): this file stacks ON TOP of
% engine/lp/contemporaneity.lp (F12's imports: token/1, backfill_suspect/1, late_declared/1) and
% engine/contemp_thresholds.lp + engine/preamble_obligations.lp (E8/E9 facts) and, OPTIONALLY,
% engine/lp/work_items.lp (F11's s22-violations arm -- #defined guards make every predicate
% groundable standalone when work_items.lp is not loaded too).
%
% THE TWO-CLOCK BRIDGE (spec §3), reused identically for every cross-seam "before"/"after" in
% this file: a tokened ledger row occupies the closed interval [invocation(Tok,Lo),
% invocation_completed(Tok,Hi)]. Row BEFORE journal event E iff Hi < E; journal event E BEFORE
% row iff E < Lo (sound even without Hi). Interval semantics, never point semantics: a
% comparison is decided ONLY when the whole interval is on one side -- an untokened row, a
% missing Hi when the upper bound is needed, or a straddling interval are each refused with
% their own typed reason (untokened_row / open_window / window_overlap), never guessed. `ts`
% NEVER keys a cross-record comparison (spec §3, binding) -- only `id` order (ledger-vs-ledger)
% and the invocation window (ledger-vs-journal) ever appear on the right of a `<`/`<=` below.
%
% THE VERDICT LAYER (spec §5) -- two strata:
%   INSTANCE: ob_discharged(F,Anchor) / ob_violated(F,Anchor) / ob_undecidable(F,Anchor,Reason),
%   mutually exclusive per instance by stratified NAF over the monotone base (the
%   contemporaneity.lp ladder idiom -- VIOLATED always the loudest, UNDECIDABLE next, DISCHARGED
%   the clean residual).
%   FAMILY: preamble_verdict(F,violated|undecidable|discharged|vacuous), exactly one atom per
%   catalogued family per run -- E8's preamble_obligation/2 grounds every family even on an
%   empty world, so this program emits TWELVE family verdicts always (never silence read as
%   clean -- the F49 vacuous-pass class ADR-0000/ADR-0015 forbid). `ob_family_forced_undecidable
%   (F,Reason)` is this file's own extension of spec §5's four-member ladder (used identically by
%   F10's own spec text: "UNDECIDABLE(no_stop_record) at the family level when other activity
%   exists, never silence" -- generalized here to every family whose TRIGGER depends on a journal
%   or schema capability that may be genuinely absent rather than merely empty, so "capability
%   absent, other activity on record" is never misread as the SAME vacuous silence a truly fresh,
%   idle world legitimately reports).
%
% ZERO `:-` integrity constraints (paraconsistent posture, the whole corpus's own idiom): a
% record with a violated/undecidable obligation stays SATISFIABLE and reportable, never a
% refusal-to-solve. NAF confined to the named seams below (the bridge classifiers, the
% "no OTHER dispatch between" idiom, the family-ladder's own priority chain) -- not diffused
% through the whole program. NO vocabulary over the SUBJECT's conduct/truth: `ob_violated` says
% "the discharging record is absent," an indictment of the RECORD, never a conviction of the
% conduct (spec §5, verbatim in spirit) -- adjudicating what a violation MEANS is the
% human/ratifier act downstream, not this program's job.
%
% RESIDUES, NAMED HONESTLY (this build's own scope decisions, distinct from spec's J-residues):
%   F11's question_open arm and review-gap arm are NOT wired to ledger_tnow.lp in this pass (that
%   would require composing THIS EDB with engine/ledger_edb.py's own separate export -- a
%   cross-domain composition the spec's own text anticipates ("when the ledger EDB is also
%   exported") but this build does not implement, honestly deferred, not silently skipped): both
%   arms are UNCONDITIONALLY ob_undecidable(f11,_,capability_absent) whenever no s22 violation is
%   ALSO found (a real violation still wins, loudest-first) -- filed, not built, this pass.
% ---------------------------------------------------------------------------
#defined row_tokened/4.
#defined row_untokened/3.
#defined invocation/2.
#defined invocation_completed/2.
#defined tool_event/2.
#defined row_declared/2.
#defined work_opened/2.
#defined work_claimed/2.
#defined work_closed/3.
#defined work_witness_present/1.
#defined work_depends/3.
#defined row_refs_row/2.
#defined row_refs_present/1.
#defined row_regards/2.
#defined row_actor/2.
#defined countersign_obliged/1.
#defined stop_event/2.
#defined delegation_dispatch/1.
#defined delegation_return/1.
#defined verify_commission_event/2.
#defined capable/1.
#defined preamble_obligation/2.
#defined stop_disposition_window_ms/1.
#defined token/1.
#defined backfill_suspect/1.
#defined late_declared/1.
#defined work_duplicate_open/1.
#defined work_shipped_without_witness/2.
#defined work_depends_on_unknown/2.
#defined work_dependency_cycle/1.

% ==== SHARED HELPERS (id-is-order base; the two-clock bridge's row-side window) ================
row_id(Id) :- row_tokened(Id,_,_,_).
row_id(Id) :- row_untokened(Id,_,_).
row_kind(Id,Kind) :- row_tokened(Id,_,Kind,_).
row_kind(Id,Kind) :- row_untokened(Id,Kind,_).
row_window_lo(Id,Lo) :- row_tokened(Id,Tok,_,_), invocation(Tok,Lo).
row_window_hi(Id,Hi) :- row_tokened(Id,Tok,_,_), invocation_completed(Tok,Hi).

commission_row(Id) :- row_kind(Id,"commission").
review_row(Id) :- row_kind(Id,"review").
verification_row(Id) :- row_kind(Id,"verification").
decision_row(Id) :- row_kind(Id,"decision").

first_row(Min) :- Min = #min{ Id : row_id(Id) }, row_id(_).
first_work_opened(Min) :- Min = #min{ Id : work_opened(_,Id) }, work_opened(_,_).
first_mutation_event(Min) :- Min = #min{ T : tool_event(mutation,T) }, tool_event(mutation,_).
any_stop_event :- stop_event(_,_).

% ===========================================================================
% F1 -- ob_commission_first(RowId) -- preamble pt 10: the min-id row must be kind=commission.
% Trigger: any row exists. UNDECIDABLE(pre_s25) when this schema's own kind vocabulary cannot
% even carry 'commission' (capable(commission_kind) absent) -- the fallback point 10 itself
% sanctions there (a decision row) is textually indistinguishable from any other decision.
% ===========================================================================
ob_discharged(f1,Min) :- first_row(Min), row_kind(Min,"commission"), capable(commission_kind).
ob_violated(f1,Min)   :- first_row(Min), not row_kind(Min,"commission"), capable(commission_kind).
ob_undecidable(f1,Min,pre_s25) :- first_row(Min), not capable(commission_kind).

% ===========================================================================
% F2 -- ob_verify_commission(CommissionId) -- preamble pt 10: verify-commission ran (any
% verdict) after the commission row and before the first work_opened row (E6 carries no
% CommissionId -- a coarse temporal check, per spec §4's own E6 signature).
% ===========================================================================
cr_before(Id,E) :- row_tokened(Id,Tok,"commission",_), invocation_completed(Tok,Hi),
    verify_commission_event(_,E), Hi < E.
cr_overlap(Id,E) :- row_tokened(Id,Tok,"commission",_), invocation(Tok,Lo), invocation_completed(Tok,Hi),
    verify_commission_event(_,E), Lo <= E, E <= Hi.
cr_open(Id,E) :- row_tokened(Id,Tok,"commission",_), invocation(Tok,Lo), not invocation_completed(Tok,_),
    verify_commission_event(_,E), Lo <= E.
evt_before_wo(E) :- first_work_opened(Min), row_tokened(Min,Tok,_,_), invocation(Tok,Lo),
    verify_commission_event(_,E), E < Lo.

ob_discharged(f2,Id) :- commission_row(Id), capable(verify_commission_journal),
    cr_before(Id,E), verify_commission_event(_,E), not first_work_opened(_).
ob_discharged(f2,Id) :- commission_row(Id), capable(verify_commission_journal),
    cr_before(Id,E), evt_before_wo(E).
ob_undecidable(f2,Id,no_verify_journal) :- commission_row(Id), not capable(verify_commission_journal).
ob_undecidable(f2,Id,untokened_row) :- commission_row(Id), capable(verify_commission_journal),
    row_untokened(Id,"commission",_).
ob_undecidable(f2,Id,open_window) :- commission_row(Id), capable(verify_commission_journal),
    row_tokened(Id,_,"commission",_), cr_open(Id,_), not ob_discharged(f2,Id).
ob_undecidable(f2,Id,window_overlap) :- commission_row(Id), capable(verify_commission_journal),
    row_tokened(Id,_,"commission",_), cr_overlap(Id,_), not cr_before(Id,_), not ob_discharged(f2,Id).
ob_violated(f2,Id) :- commission_row(Id), capable(verify_commission_journal), row_tokened(Id,_,"commission",_),
    not ob_discharged(f2,Id), not ob_undecidable(f2,Id,open_window), not ob_undecidable(f2,Id,window_overlap).

% ===========================================================================
% F3 -- ob_decomposition_refs_commission(WorkRowId) -- preamble pt 10: a work_opened row's own
% refs carries a parsed row:<id> edge to a (preceding) commission row.
% ===========================================================================
wo_trigger(WId) :- work_opened(_,WId).
ob_undecidable(f3,WId,pre_s25) :- wo_trigger(WId), not capable(commission_kind).
ob_discharged(f3,WId) :- wo_trigger(WId), capable(commission_kind),
    row_refs_row(WId,CId), commission_row(CId), CId < WId.
ob_undecidable(f3,WId,refs_unparsed) :- wo_trigger(WId), capable(commission_kind),
    row_refs_present(WId), not ob_discharged(f3,WId).
ob_violated(f3,WId) :- wo_trigger(WId), capable(commission_kind),
    not ob_discharged(f3,WId), not ob_undecidable(f3,WId,refs_unparsed).

% ===========================================================================
% F4 -- ob_decompose_before_work(ToolEventT) -- preamble pt 1: at least one work_opened row
% wholly before the world's first artifact-mutation tool_event.
% ===========================================================================
ob_discharged(f4,T) :- first_mutation_event(T), work_opened(_,WId), row_tokened(WId,Tok,_,_),
    invocation_completed(Tok,Hi), Hi < T.
ob_undecidable(f4,T,untokened_row) :- first_mutation_event(T), work_opened(_,WId),
    row_untokened(WId,_,_), not ob_discharged(f4,T).
ob_undecidable(f4,T,open_window) :- first_mutation_event(T), work_opened(_,WId), row_tokened(WId,Tok,_,_),
    invocation(Tok,Lo), not invocation_completed(Tok,_), Lo <= T,
    not ob_discharged(f4,T), not ob_undecidable(f4,T,untokened_row).
ob_violated(f4,T) :- first_mutation_event(T),
    not ob_discharged(f4,T), not ob_undecidable(f4,T,untokened_row), not ob_undecidable(f4,T,open_window).

% ===========================================================================
% F5 -- ob_open_before_claim(Slug) -- preamble pt 1: work_opened id < work_claimed id, per slug.
% F6 -- ob_claim_before_close(Slug) -- preamble pt 1: work_claimed id < work_closed id, per slug.
% Pure id order, no cross-seam (work_items.lp's own domain -- s22's DDL already forecloses a
% work_claimed/closed row with no prior work_opened at the write boundary; these are the
% ORDER checks that DDL does NOT enforce -- a work_opened row that itself lands AFTER its own
% claim/close is impossible by that same DDL gate, so DISCHARGED is the expected common case).
% ===========================================================================
ob_discharged(f5,Slug) :- work_claimed(Slug,ClaimId), work_opened(Slug,OpenId), OpenId < ClaimId.
ob_violated(f5,Slug) :- work_claimed(Slug,_), not ob_discharged(f5,Slug).

ob_discharged(f6,Slug) :- work_closed(Slug,_,CloseId), work_claimed(Slug,ClaimId), ClaimId < CloseId.
ob_violated(f6,Slug) :- work_closed(Slug,_,_), not ob_discharged(f6,Slug).

% ===========================================================================
% F7 -- ob_countersign_decomposition(WorkRowId) -- preamble pt 2: a review-kind row with larger
% id than the work_opened row, before the stop event when one exists (no upper bound needed
% otherwise -- the session may still be live).
% ===========================================================================
ob_discharged(f7,WId) :- work_opened(_,WId), review_row(RId), RId > WId, not any_stop_event.
ob_discharged(f7,WId) :- work_opened(_,WId), review_row(RId), RId > WId, row_tokened(RId,Tok,"review",_),
    invocation_completed(Tok,Hi), stop_event(_,ST), Hi < ST.
ob_undecidable(f7,WId,untokened_row) :- work_opened(_,WId), review_row(RId), RId > WId,
    row_untokened(RId,"review",_), any_stop_event, not ob_discharged(f7,WId).
ob_undecidable(f7,WId,open_window) :- work_opened(_,WId), review_row(RId), RId > WId,
    row_tokened(RId,Tok,"review",_), invocation(Tok,Lo), not invocation_completed(Tok,_),
    stop_event(_,ST), Lo <= ST, not ob_discharged(f7,WId), not ob_undecidable(f7,WId,untokened_row).
ob_violated(f7,WId) :- work_opened(_,WId),
    not ob_discharged(f7,WId), not ob_undecidable(f7,WId,untokened_row), not ob_undecidable(f7,WId,open_window).

% ===========================================================================
% F8 -- ob_criteria_before_work(CriteriaId) -- preamble pt 3: a verification row's refs edge
% names a criteria row C; C must be wholly before the world's first artifact-mutation tool_event
% (the id-ordering half is kernel-foreclosed VACUOUS BY CONSTRUCTION -- refs of a later row can
% only point earlier, append-only -- so only the temporal half is checked here).
% ===========================================================================
criteria_ref(VId,CId) :- verification_row(VId), row_refs_row(VId,CId).

ob_discharged(f8,CId) :- criteria_ref(_,CId), row_tokened(CId,Tok,_,_), invocation_completed(Tok,Hi),
    first_mutation_event(T), Hi < T.
ob_discharged(f8,CId) :- criteria_ref(_,CId), not first_mutation_event(_).
ob_undecidable(f8,CId,untokened_row) :- criteria_ref(_,CId), row_untokened(CId,_,_),
    first_mutation_event(_), not ob_discharged(f8,CId).
ob_undecidable(f8,CId,open_window) :- criteria_ref(_,CId), row_tokened(CId,Tok,_,_), invocation(Tok,Lo),
    not invocation_completed(Tok,_), first_mutation_event(T), Lo <= T, not ob_discharged(f8,CId).
ob_violated(f8,CId) :- criteria_ref(_,CId),
    not ob_discharged(f8,CId), not ob_undecidable(f8,CId,untokened_row), not ob_undecidable(f8,CId,open_window).
% refs present on a verification row but unparseable -- anchored on the CITING row (VId), the
% only id known when no CId could be identified at all.
ob_undecidable(f8,VId,refs_unparsed) :- verification_row(VId), row_refs_present(VId), not criteria_ref(VId,_).

% ===========================================================================
% F9 -- ob_ledger_before_delegation(DispatchT) -- preamble pt 7: a decision row wholly before
% the dispatch, with no OTHER dispatch between that decision and this one (one fresh decision
% per dispatch -- "Dispatching a subagent is a decision row").
% ===========================================================================
decision_before_dispatch(Id,T) :- decision_row(Id), row_tokened(Id,Tok,"decision",_),
    invocation_completed(Tok,Hi), delegation_dispatch(T), Hi < T.
other_dispatch_between(Id,T) :- decision_before_dispatch(Id,T), row_tokened(Id,Tok,"decision",_),
    invocation_completed(Tok,Hi), delegation_dispatch(T2), Hi < T2, T2 < T.

ob_discharged(f9,T) :- delegation_dispatch(T), decision_before_dispatch(Id,T), not other_dispatch_between(Id,T).
% CONSERVATIVE SCOPE (named, not silently precise): an untokened/open-window decision ANYWHERE
% in the world is enough to mark a not-yet-discharged dispatch UNDECIDABLE, since this program
% cannot tell whether THAT row was meant to be the fresh decision for THIS dispatch without a
% sound comparison -- never a guessed VIOLATED over an ambiguous record.
ob_undecidable(f9,T,untokened_row) :- delegation_dispatch(T), decision_row(Id), row_untokened(Id,"decision",_),
    not ob_discharged(f9,T).
ob_undecidable(f9,T,open_window) :- delegation_dispatch(T), decision_row(Id), row_tokened(Id,Tok,"decision",_),
    invocation(Tok,Lo), not invocation_completed(Tok,_), Lo <= T,
    not ob_discharged(f9,T), not ob_undecidable(f9,T,untokened_row).
ob_violated(f9,T) :- delegation_dispatch(T),
    not ob_discharged(f9,T), not ob_undecidable(f9,T,untokened_row), not ob_undecidable(f9,T,open_window).

% ===========================================================================
% F10 -- ob_stop_disposition(StopT) -- preamble pt 8: a decision row wholly within
% [StopT-W, StopT], W = stop_disposition_window_ms/1 (E9). FAMILY-LEVEL: a session with other
% ledger activity but NO stop_event at all is UNDECIDABLE(no_stop_record), never silence
% (spec's own text, verbatim) -- see ob_family_forced_undecidable below.
% ===========================================================================
decision_in_stop_window(Id,ST) :- decision_row(Id), row_tokened(Id,Tok,"decision",_), invocation(Tok,Lo),
    invocation_completed(Tok,Hi), stop_event(_,ST), stop_disposition_window_ms(W),
    Lo >= ST - W, Hi <= ST.

ob_discharged(f10,ST) :- stop_event(_,ST), decision_in_stop_window(_,ST).
ob_undecidable(f10,ST,untokened_row) :- stop_event(_,ST), decision_row(Id), row_untokened(Id,"decision",_),
    not ob_discharged(f10,ST).
ob_undecidable(f10,ST,open_window) :- stop_event(_,ST), decision_row(Id), row_tokened(Id,Tok,"decision",_),
    invocation(Tok,Lo), not invocation_completed(Tok,_), stop_disposition_window_ms(W),
    Lo >= ST - W, Lo <= ST, not ob_discharged(f10,ST), not ob_undecidable(f10,ST,untokened_row).
ob_violated(f10,ST) :- stop_event(_,ST),
    not ob_discharged(f10,ST), not ob_undecidable(f10,ST,untokened_row), not ob_undecidable(f10,ST,open_window).

% ===========================================================================
% F11 -- ob_clean_at_stop(StopT) -- preamble pt 5: at StopT, no open s22 violation (the arm this
% build actually re-derives); the question_open and review-gap arms are UNCONDITIONALLY
% capability_absent this pass (see this file's own header RESIDUES note) -- a real s22 violation
% still outranks the capability gap (loudest-first).
% ===========================================================================
s22_violation :- work_duplicate_open(_).
s22_violation :- work_shipped_without_witness(_,_).
s22_violation :- work_depends_on_unknown(_,_).
s22_violation :- work_dependency_cycle(_).

ob_violated(f11,ST) :- stop_event(_,ST), s22_violation.
ob_undecidable(f11,ST,capability_absent) :- stop_event(_,ST), not s22_violation.

% ===========================================================================
% F12 -- ob_record_as_you_go(Token) -- preamble pt 9: IMPORTED WHOLESALE from
% engine/lp/contemporaneity.lp (Part 2) -- re-derives nothing, only maps those atoms into this
% file's own verdict layer. A backfill_suspect token is VIOLATED; a late_declared token is
% DISCHARGED (the mandate's own permitted late-entry act); every other tokened invocation is
% DISCHARGED (contemporaneous/batched_declared, both legitimate).
% ===========================================================================
ob_violated(f12,Tok) :- backfill_suspect(Tok).
ob_discharged(f12,Tok) :- late_declared(Tok).
ob_discharged(f12,Tok) :- token(Tok), not backfill_suspect(Tok), not late_declared(Tok).

% ===========================================================================
% FAMILY-LEVEL FORCED UNDECIDABLE (this file's own extension of spec §5's ladder -- see header):
% a capability genuinely absent, with OTHER ledger activity on record, is never silently VACUOUS.
% ===========================================================================
ob_family_forced_undecidable(f4,pre_s22)  :- not capable(work_items), row_id(_).
ob_family_forced_undecidable(f5,pre_s22)  :- not capable(work_items), row_id(_).
ob_family_forced_undecidable(f6,pre_s22)  :- not capable(work_items), row_id(_).
ob_family_forced_undecidable(f7,pre_s22)  :- not capable(work_items), row_id(_).
ob_family_forced_undecidable(f10,no_stop_record) :- not any_stop_event, row_id(_).
ob_family_forced_undecidable(f12,capability_absent) :- not capable(s23_capable), row_id(_).

% ===========================================================================
% THE FAMILY-STRATUM VERDICT LADDER (spec §5, extended with the forced-undecidable escape hatch
% above) -- exactly one atom per catalogued family per run, loudest-first.
% ===========================================================================
preamble_verdict(F,violated) :- ob_violated(F,_).
preamble_verdict(F,undecidable) :- not ob_violated(F,_), ob_undecidable(F,_,_).
preamble_verdict(F,undecidable) :- not ob_violated(F,_), not ob_undecidable(F,_,_),
    ob_family_forced_undecidable(F,_), preamble_obligation(F,_).
preamble_verdict(F,discharged) :- not ob_violated(F,_), not ob_undecidable(F,_,_),
    not ob_family_forced_undecidable(F,_), ob_discharged(F,_).
preamble_verdict(F,vacuous) :- preamble_obligation(F,_),
    not ob_violated(F,_), not ob_undecidable(F,_,_), not ob_family_forced_undecidable(F,_), not ob_discharged(F,_).

#show ob_discharged/2.
#show ob_violated/2.
#show ob_undecidable/3.
#show ob_family_forced_undecidable/2.
#show preamble_verdict/2.
% base relations, first-class (non-foreclosure -- a consumer builds its own report from these
% without touching the rules above) -- LIMITED HERE to Id/Slug/Token-typed relations only (never
% anchor-relative-ms), a deliberate scope choice: several base relations this program computes
% internally (row_window_lo/2, row_window_hi/2, first_mutation_event/1,
% decision_in_stop_window/2, decision_before_dispatch/2) carry a relative-ms argument, and the
% SQL-floor differential's denomination-normalization step (mirroring
% engine/contemp_differential.py's own CLOSED, named-list discipline) is scoped to the
% VERDICT-LAYER predicates above, whose Anchor argument is ms-typed ONLY for four of twelve
% families (F4/F9/F10/F11) and handled there by a family-keyed rewrite -- extending that same
% keyed rewrite to five MORE bare relative-ms base relations was judged disproportionate scope
% for this pass and is filed, not built (a consumer needing them can still query this program's
% own EDB+rules directly with clingo; #show is a convenience list, not the only access path).
#show commission_row/1.
#show first_row/1.
#show first_work_opened/1.
#show criteria_ref/2.
