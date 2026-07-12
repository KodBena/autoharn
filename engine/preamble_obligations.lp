% ===========================================================================
% preamble_obligations.lp -- E8 of design/ORCH-CONTEMPORANEITY-PART3-SPEC.md §4: the recorded
% obligation catalogue, one fact per formalized family (F1-F12), naming the governance preamble
% point (bootstrap/templates/CLAUDE.md.tmpl, the twelve numbered points every scaffolded world
% receives at birth) it discharges. Mirrors engine/contemp_thresholds.lp's OWN role -- a standing
% facts file, swappable independently of the rules in engine/lp/preamble_ordering.lp (ADR-0012
% P1's denomination-check idiom, applied to a CATALOGUE rather than a MEASURED bound: adding or
% retiring an obligation is a facts-file edit plus its fixtures, never a rule rewrite -- spec §1).
%
% THIS IS THE ANDERSON-REDUCTION SUBSTRATE (spec §1): the obligation is a recorded, other-
% assigned fact -- here, "other-assigned" by the scaffold's own preamble text, not by `led
% obligate`. preamble_obligation/2 is what GUARANTEES §5's never-silence property: because this
% fact family grounds every family even on a completely empty world (an EDB with zero ledger
% rows, zero journals -- the VACUOUS witness case), the program emits twelve family verdicts
% ALWAYS, and a missing family verdict is itself a loud defect for the Python harness to catch,
% never read as clean (the vacuous-pass class ADR-0000/ADR-0015 forbid -- findings-register F49).
%
% CATALOGUE ENUMERATION VERIFIED against bootstrap/templates/CLAUDE.md.tmpl AS IT STANDS TODAY
% (2026-07-12, this same commission) -- the preamble carries exactly twelve numbered points,
% unchanged in count and in point-to-family mapping since design/ORCH-CONTEMPORANEITY-PART3-SPEC.md
% was authored: no template drift found. (Point 10's prose has grown more elaborate than the
% spec's own table paraphrase -- it now spells out the FULL/LAZY signing-mode split and the
% ./verify-commission gate in more words -- but the OBLIGATION SHAPE the spec's F1/F2/F3 rows
% formalize is unchanged: still "commission first", "verify it", "decompositions cite it".)
%
% F -> preamble point:  F1/F2/F3 -> 10 (intake capture);  F4/F5/F6 -> 1 (decompose-before-work,
% open-before-claim, claim-before-close);  F7 -> 2 (countersign the decomposition);  F8 -> 3
% (pre-registered criteria before work);  F9 -> 7 (ledger before delegation);  F10 -> 8 (stop is
% a ledgered act);  F11 -> 5 ("done means clean", re-derived retrospectively);  F12 -> 9
% (record-as-you-go, imported wholesale from Part 2/contemporaneity.lp).
%
% OUT OF SCOPE, NAMED (spec §7, not represented here -- a family only exists for a formalized
% point): preamble point 4 (files committed to git -- a third record system, filed as a possible
% Part 4), point 6 (assumption-before-commitment -- the J-boundary's cleanest case, no M-core
% trigger), point 11 (decisions name rejected alternatives -- a content convention, no ordering
% component), point 12 (subagent self-report marking -- a content convention, no ordering
% component). The closure statement (spec §7) is the prose account; this file is the machine-
% checkable half of it -- a `preamble_obligation(F,_)` fact exists for exactly the eight covered
% points' families (F1-F12, i.e. every family this spec catalogues), never for the four
% out-of-scope points.
% ---------------------------------------------------------------------------
preamble_obligation(f1,10).
preamble_obligation(f2,10).
preamble_obligation(f3,10).
preamble_obligation(f4,1).
preamble_obligation(f5,1).
preamble_obligation(f6,1).
preamble_obligation(f7,2).
preamble_obligation(f8,3).
preamble_obligation(f9,7).
preamble_obligation(f10,8).
preamble_obligation(f11,5).
preamble_obligation(f12,9).
