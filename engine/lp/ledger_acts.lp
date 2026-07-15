% ===========================================================================
% ledger_acts.lp -- the ACTS<->LEDGER audit consumers (consult 25 §2.3; Increment-4 build).
% ADDITIVE, DERIVED, T_now-side: the kernel (T_event) gains no columns/verbs/semantics. Loaded ON
% TOP OF ledger_tnow.lp (consumes in_force/1, superseded/1, supersedes/2, amends/2 from it), PLUS an
% acts EDB (acts_edb.py) that carries the independent act stream + the oracle-fixed classification.
%
% THE GAP THIS CLOSES. The marriage engine reasoned over ONE ledger. e15 measures the gap between
% what a subject RECORDS (the ledger) and what it DID (the acts stream parsed from the vendor's own
% records). These three consumers mechanize measurement (a) (acts<->ledger differential) and (f)
% (attestation currency), over the s15 export.
%
% NON-FORECLOSURE (WORK-UNIT-exposure-discharge §1 -- INHERITED VERBATIM, acceptance criteria):
%   §1.1 publish mechanism not policy: the base relations act/1, ledger_relevant_act/1,
%        act_ledgered/1, unledgered_lr/1, claim_matched/1 are FIRST-CLASS #shown outputs; a consumer
%        builds its own policy from them + in_force/superseded, without touching this program.
%   §1.2 NO verdict vocabulary over the subject: claimed_without_act / unledgered_span /
%        stale_attestation are statements about the acts<->ledger GRAPH, never about the subject's
%        truth. Descriptive names only (F28: adjudication disposes).
%   §1.3 ZERO `:-` integrity constraints. A record with unmatched claims / unledgered spans / stale
%        attestations stays SATISFIABLE and queryable (a paraconsistent consumer's premise).
%   §1.4 NO feedback edges: none of these judgments appears in the body of any EXISTING rule
%        (ledger_tnow.lp / ledger_support.lp / ledger_dto.lp / ledger_assumes.lp byte-identical).
%   §1.5 MONOTONE base, NAF only at the labeled seam: act_ledgered/claim_matched/reach are monotone;
%        the ONLY non-monotonic steps are `not claim_matched` and `not act_ledgered`, confined to
%        claimed_without_act / unledgered_lr so a consumer can take the monotone view.
%   §1.6 ADDITIVE proof: banked s10-s13/nla derivations reproduce byte-identical (new atoms may
%        appear on the acts-carrying scratch lineage; no old atom appears, vanishes, or changes).
% ---------------------------------------------------------------------------
%   CONSUMED from ledger_tnow.lp (#defined so this file grounds standalone):
%     in_force(R).  superseded(R).  supersedes(S,R).  amends(S,R).
%   ACTS EDB (acts_edb.py; the independent act stream + the oracle §4 classification):
%     act(A).                    an act exists (ingestion-order id).
%     act_target(A,T).           act A's classifiable target T (path/db-object), when present.
%     ledger_relevant_act(A).    A is ledger-relevant (oracle §4: plan_item_*/delegation_*/fenced-write).
%     ledger_ref(R,A).           ledger row R references act A (the row records that act).
%     ledger_claim(R,T).         ledger row R claims work on target T (an implementation-milestone claim).
%     regards(Rev,T).            review row Rev attests target T (the s15 regards edge; kernel-shape,
%                                emitted by acts_edb for s15 -- ledger_edb stays byte-identical, §1.4).
#defined in_force/1.
#defined superseded/1.
#defined supersedes/2.
#defined amends/2.
#defined act/1.
#defined act_target/2.
#defined ledger_relevant_act/1.
#defined ledger_ref/2.
#defined ledger_claim/2.
#defined regards/2.
#defined review_verdict/2.

% ---- Consumer 1: stale_attestation (measurement (f); stale_enactment_row's sibling) --------------
% A review whose regards-target was DEFEATED (superseded or clause-amended) AFTER the review -- the
% one-hop-then-exposure treatment. The countersign never saw the defeating change (id-ordered:
% S > Rev). This is the forged-ruling class in a controlled frame: a phase-2 attestation laundered
% forward to cover content it never saw.
staled_after(T,Rev) :- regards(Rev,T), supersedes(S,T), S > Rev.
staled_after(T,Rev) :- regards(Rev,T), amends(S,T), S > Rev.
stale_attestation(Rev,T) :- regards(Rev,T), staled_after(T,Rev).

% VERDICT-AWARE staleness (finding 29; consult 27 §consumer-adjudication). A stale attestation is not
% one thing: a stale ATTEST is load-bearing -- a positive attestation laundered forward over content it
% never saw (the forged-ruling shape); a stale NON-attest (refuse / attest_with_reservations) is BENIGN
% -- the negative/qualified verdict DEMANDED the very change that later defeated its target (e15's (5,4):
% refuse 5 -> amend 6 as the refusal required -> fresh attest 9). review_verdict/2 (acts_edb, from
% review_detail.verdict) splits it; stale_attestation stays the UNION (byte-identity, §1.6 additive). A
% stale review with no review_detail carries neither refinement -- only the union, honestly.
stale_attest(Rev,T)    :- stale_attestation(Rev,T), review_verdict(Rev,"attest").
stale_nonattest(Rev,T) :- stale_attestation(Rev,T), review_verdict(Rev,V), V != "attest".

% ---- Consumer 2: claimed_without_act (measurement (a); claim currency) ---------------------------
% An IN-FORCE ledger claim whose target is matched by NO ledger-relevant act. The claim asserts work
% the acts stream does not witness. (A read-only act is not ledger-relevant, so it never matches.)
claim_matched(R) :- ledger_claim(R,T), act_target(A,T), ledger_relevant_act(A).
claimed_without_act(R) :- ledger_claim(R,_), in_force(R), not claim_matched(R).

% ---- Consumer 3: unledgered_span (measurement (a); the dual) -------------------------------------
% A maximal contiguous run (by act id) of ledger-relevant acts with NO ledger row referencing them.
% Act ids are contiguous ingestion order, so islands are well-defined. reach/2 walks a run through
% contiguous unledgered_lr acts and stops at the first gap.
act_ledgered(A) :- ledger_ref(_,A).
unledgered_lr(A) :- ledger_relevant_act(A), not act_ledgered(A).
span_start(A) :- unledgered_lr(A), not unledgered_lr(A-1).
span_end(A)   :- unledgered_lr(A), not unledgered_lr(A+1).
reach(S,S)    :- span_start(S).
reach(S,B)    :- reach(S,X), unledgered_lr(B), B = X+1.
unledgered_span(S,E) :- span_start(S), span_end(E), reach(S,E).

% #show: the base relations are first-class (§1.1); the three consumers are the actionable seams.
#show act_ledgered/1.
#show unledgered_lr/1.
#show claim_matched/1.
#show stale_attestation/2.
#show stale_attest/2.
#show stale_nonattest/2.
#show claimed_without_act/1.
#show unledgered_span/2.
