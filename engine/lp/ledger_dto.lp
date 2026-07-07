% ===========================================================================
% ledger_dto.lp -- the DECOMPOSE-THEN-OVERRULE (DTO) closures + I7 assumption
% expiry: the ENGINE-LAYER CONSUMER that ends the "no consumer" deferral.
%
% DTO is the ADOPTED clause-defeat shape (maintainer inverted-burden adoption). Its
% "worked out in full in THIS increment, trigger-gating STRUCK" authority is
% ENGINEER-UNDER-DELEGATION, maintainer-CONFIRMED by his subsequent explicit directions --
% the build instruction ("struck B5... replaced with the full §1.5 shape") and passing the
% Increment-1.1 fix-pass through on the full-DTO basis (fidelity review §2.3;
% deliberations/clause-defeat-decompose-then-overrule.md Provenance-correction append,
% 2026-07-06). It is NOT cited as a standalone "2026-07-06 SCHEDULING RULING" of the
% maintainer's own hand -- that section was engineer-authored under standing delegation; the
% authority is real and became so by the two confirming acts above. The
% degenerate supersede-and-reissue is NOT the exercise; the full §1.5 shape is:
%   decomposes edge + group identity + faithfulness/MECE attestation gate
%   (SoD-distinct attester) + one inbound-edge re-key.
% This program is loaded ON TOP OF ledger_tnow.lp (which supplies superseded/1,
% amends/2, enacts/2, answers/2). It is exercised on the SCRATCH lineage
% (ledger_dto_scratch.py) -- never a subject/evidence ledger, named in the witness.
%
% The hard rule (design §4): kernel validity stays TWO-VALUED and ROW-GRANULAR.
% Fragments are rows; DTO needs no third truth value. The displacement "false
% alarms" are CONSERVATIVE re-key debt, not unsoundness -- an inbound row-granular
% citation of a decomposed target has become ambiguous, and forcing the re-key
% makes the record say which fragment it meant (maintainer ruling on consult 19).
% ---------------------------------------------------------------------------

% ---- DTO EDB (apparatus-authored on the scratch lineage) --------------------------
%   decomposes(F, T).          fragment row F is a first-class re-issue of part of T.
%   decomp_group(G, F).        fragment F belongs to decomposition group G.
%   decomp_author(G, Author).  the principal who authored the decomposition (an id).
%   decomp_attests(G, By).     a principal who attested faithful + MECE (an id).
%   attester_authentic(By).    By is an AUTHENTIC (human) principal, not a labeled synthetic one.
%   rekeyed(Kind, Cite, F).    an inbound edge of Kind on the decomposed target has
%                              been re-keyed to fragment F (Kind in {enacts,answers,amends}).
#defined decomposes/2.
#defined decomp_group/2.
#defined decomp_author/2.
#defined decomp_attests/2.
#defined attester_authentic/1.
#defined rekeyed/3.

% A target that has been decomposed (its content re-issued as first-class fragments).
decomposed(T) :- decomposes(_,T).

% ---- the faithfulness/MECE attestation gate, SoD-checked ---------------------------
% A group is ATTESTED iff some principal DISTINCT from the decomposition's author
% attested it (segregation of duties -- the review/regards SoD discipline, F49-class
% for attestation). Self-attestation is NOT attestation.
decomp_attested(G) :- decomp_attests(G,By), decomp_author(G,Author), By != Author.
% LOUD flags (the human-attester touchpoint is the one pending step):
%  - a group with no SoD-distinct attestation is PENDING (not in force as standing).
decomp_pending_attestation(G) :- decomp_group(G,_), not decomp_attested(G).
%  - an attestation BY THE AUTHOR is an SoD VIOLATION (a red flag, never a pass).
decomp_sod_violation(G) :- decomp_attests(G,X), decomp_author(G,X).

% ---- fragment standing -------------------------------------------------------------
% A fragment carries the original's standing (is treated as in force) ONLY once its
% group is attested and it is not itself superseded. Before attestation it is PENDING
% -- a consumer must not read an unattested fragment as carrying the referent's status.
fragment_in_force(F) :- decomp_group(G,F), decomp_attested(G), not superseded(F).
fragment_pending(F)  :- decomp_group(G,F), not decomp_attested(G).

% SYNTHETIC vs AUTHENTIC standing (out-of-frame audit finding 3). `By != Author` is only
% STRUCTURAL SoD -- on a scratch lineage two LABELED SYNTHETIC principals (same apparatus,
% distinct labels) satisfy it, which is fine for the exercise but must NEVER let synthetic
% self-review confer real standing on a real lineage. So standing carries its attestation's
% KIND: a fragment is authentic-attested only when a distinct AUTHENTIC principal attested it,
% and a fragment whose standing rests ONLY on a synthetic attestation is flagged LOUDLY -- a
% real-lineage consumer keys on fragment_in_force_authentic and refuses synthetic_standing.
decomp_attested_authentic(G) :- decomp_attests(G,By), decomp_author(G,Author),
                                By != Author, attester_authentic(By).
fragment_in_force_authentic(F) :- decomp_group(G,F), decomp_attested_authentic(G), not superseded(F).
synthetic_standing(F) :- fragment_in_force(F), not fragment_in_force_authentic(F).

% ---- F-B: DERIVED EVICTION + the premature-eviction guard (fidelity review §1 / §2.2) ---------
% Consult 19 §1.5 (adopted as MANDATORY DTO freight): "the target leaves ledger_current IFF an
% in-force, SoD-independent review attests the group faithful and complete. An unattested or
% partial decomposition evicts NOTHING."
%
% RATIFIED (maintainer, 2026-07-06): evict-on-attest -- "a decomposition's referent does NOT leave
% the current view until the group is attested" (deliberations/clause-defeat-decompose-then-overrule.md
% RATIFIED §1). The full DERIVED-eviction fix is now owed BEYOND the premature_eviction flag: a
% decomposed target's presence in the current view (T_now) is DERIVED from group attestation, so a DTO
% consumer reads the referent as RETAINED (not gone) until the group is attested -- an AUTHORITATIVE
% corrected view, not merely the flag.
%
% HONEST SCOPE (out-of-frame hack-rationalization audit, 2026-07-06 -- not overstated). This does NOT
% make the forbidden state literally unrepresentable in the kernel: the append-only record is never
% rewritten, so raw kernel in_force(T)/superseded(T) STILL renders the eviction (that is T_event, and
% correct). What this adds is the AUTHORITATIVE T_now predicate a decomposed target's consumer must
% read INSTEAD of raw in_force (referent_in_current below) -- and there is NOT YET a mechanism FORCING
% a consumer onto it. The constraint that would make the void supersede UNAUTHORABLE at all (so the
% half-decomposed-original-gone state is truly unrepresentable) is a write-boundary ORDERING gate,
% which RATIFIED §1 DEFERS to when DTO reaches a real subject lineage. Until then the disposition is:
% the authoritative corrected view (referent_in_current) + the loud premature_eviction flag; and the
% latent hazard that a future DTO consumer reads raw in_force for a decomposed target is named in the
% link-25 handoff (no referent-currency differential yet exists on this side, unlike the F-D keying).
%
% WHERE THE DERIVATION LIVES, AND WHY NOT THE KERNEL `in_force`/floor (letter-vs-spirit, surfaced per
% CLAUDE.md / ADR-0013 fair-dealing-both-ways). The eviction is carried by an APPEND-ONLY `supersedes`
% row (the record is never rewritten -- that is T_event). A DTO program loaded ON TOP of ledger_tnow.lp
% can only ADD atoms; it cannot RETRACT the kernel `superseded(T)`/`in_force`/`head` closure. Jamming
% retention into kernel `in_force` would ALSO make a retained referent both `in_force(T)` AND
% `head(T, evictor)` -- a contradiction in head-resolution -- and would force the deliberately DTO-free
% SQL floor (ledger_floor.py: "DTO ... has no SQL floor") to grow a decomposition reader for a predicate
% NO floored/banked target exercises (fabricated structure, ADR-0008). So the correct, two-valued
% row-granular (design §4) home is the DTO LAYER: kernel `in_force`/head and its SQL floor are UNTOUCHED
% (they render T_event faithfully), and the DTO layer supplies the CORRECTED current-view membership a
% decomposed target's consumer reads -- exactly as fragment_in_force sits beside kernel in_force. The
% "(+ ledger_floor.py mirror)" is therefore SATISFIED VACUOUSLY: no kernel/floored predicate changes,
% so the marriage differential (ledger_tnow.lp vs ledger_floor.py) is byte-identical -- verified, not
% asserted. (The write-boundary ordering constraint that STOPS the void supersede from being authored
% at all is owed when DTO reaches a real subject lineage; RATIFIED §1 defers it to then.)

% the referent LEAVES the current view IFF its group is attested (faithful+MECE, SoD-distinct --
% decomp_attested already encodes the SoD gate and, via the EDB, faithful AND mece):
decomp_evicts_referent(T) :- decomposed(T), decomp_group(G,_), decomposes(_,T), decomp_attested(G).
% ... and until then the referent is RETAINED in the current view -- the F44 aspectual state, strictly
% better than a gone original under an unattested paraphrase. This is the authoritative "is the
% decomposed referent still current?" a DTO consumer reads INSTEAD of the raw kernel in_force:
referent_in_current(T) :- decomposed(T), not decomp_evicts_referent(T).

% the LOUD transitional signal STAYS (the void supersede is in the record until write-boundary ordering
% lands): a target decomposed AND superseded AND whose group is not yet attested is premature_eviction.
% Now redundant-with-safe -- referent_in_current(T) still holds for exactly these T (they are retained),
% so the forbidden state is unrepresentable in the derived view AND announced by this flag.
premature_eviction(T,G) :- decomposed(T), superseded(T),
                           decomp_group(G,F), decomposes(F,T), not decomp_attested(G).

% ---- DTO-ready moot extension (design §4; deliberation clause_defeat_moot) ----------
% An `amends` on a target that is later DECOMPOSED (not only superseded) is MOOT
% through the ledger's own vocabulary -- no new mechanism (the deliberation's posture,
% now with a live consumer).
clause_defeat_moot_dto(A,T) :- amends(A,T), decomposed(T).

% ---- inbound-edge re-key debt (the conservative "false alarm" as TRUE information) --
% A row-granular inbound edge citing a decomposed target, not yet re-keyed to a
% fragment, is AMBIGUOUS between a defeated and a surviving fragment: flag it (force
% the re-key). Re-keying (rekeyed/3) RETRACTS the debt non-monotonically.
rekey_debt(enacts,E,T)  :- enacts(E,T),  decomposed(T), not rekeyed(enacts,E,T).
rekey_debt(answers,A,T) :- answers(A,T), decomposed(T), not rekeyed(answers,A,T).
rekey_debt(amends,A,T)  :- amends(A,T),  decomposed(T), not rekeyed(amends,A,T).

#show decomposed/1.
#show decomp_attested/1.
% decomp_attested_authentic/1 is EXPORTED (Increment 3 item 2, 2026-07-06): it is a first-class
% standing predicate (a group attested by a DISTINCT AUTHENTIC principal) that a consumer -- and
% dto_authentic_verify.py -- queries. Absent from #show it derived internally yet printed "(none)",
% the F49 not-shown-conflated-with-false defect. Additive: every OTHER banked predicate is byte-identical.
#show decomp_attested_authentic/1.
#show decomp_pending_attestation/1.
#show decomp_sod_violation/1.
#show fragment_in_force/1.
#show fragment_in_force_authentic/1.
#show synthetic_standing/1.
#show fragment_pending/1.
#show clause_defeat_moot_dto/2.
#show rekey_debt/3.
#show premature_eviction/2.
#show referent_in_current/1.
#show decomp_evicts_referent/1.
