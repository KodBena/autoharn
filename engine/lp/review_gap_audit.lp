% ===========================================================================
% review_gap_audit.lp -- tracker item `content-free-review-audit`: flags a `review` row that
% MECHANICALLY DISCHARGES a countersign obligation (kernel/lineage/s13-schema.sql's
% `<schema>.review_gap` view semantics -- ANY unsuperseded, distinct-actor `attest` review
% discharges; content is never examined by the view) whose OWN statement is content-free
% (engine/review_gap_thresholds.py's shared threshold). WITNESSED SPECIMEN: run12 ledger row
% 20, statement="test" (4 chars), which discharged row 4's obligation while none of run12's six
% reviewer passes ever flagged it -- see engine/review_gap_edb.py's own docstring for the full
% account.
%
% VERDICT VOCABULARY: `flagged/1` ONLY -- never a `violated`/`refused` vocabulary. A short
% statement is suspicious, not proven dishonest (a legitimate terse review exists); this program
% NEVER substitutes for fresh-eyes review of reviews (engine/review_gap_edb.py's own "THE HONEST
% LIMIT" section states this in full -- restated here because a reader of THIS file alone should
% not have to chase the EDB module to learn the vocabulary's own honesty bound).
%
% discharges/2 MIRRORS `<schema>.review_gap`'s own SQL EXACTLY (kernel/lineage/s13-schema.sql,
% unchanged through s21): the join is on ACTOR IDENTITY ALONE (the maintainer-ratified
% review-gap-scope-semantics ruling, design/MAINT-REVIEW-GAP-SCOPE-SEMANTICS-RULING.md -- `scope`
% is a human-readable label, never a filter), superseded is SINGLE-HOP (`not superseded(X)`,
% never a transitive sup_star closure -- a different consumer's semantics, not this one's), and a
% review discharges REGARDLESS of whether the obliged row ALSO carries other reviews (the view's
% own `NOT EXISTS` is satisfied by the FIRST qualifying row found, exactly the mechanism the
% run12 specimen exploited).
%
% ZERO `:-` integrity constraints (the corpus's own paraconsistent idiom, matching
% engine/lp/work_items.lp / engine/lp/preamble_ordering.lp): a flagged row stays SATISFIABLE and
% reportable, never a refusal-to-solve.
% ---------------------------------------------------------------------------
#defined obliged/1.
#defined row_actor/2.
#defined superseded/1.
#defined review_row/1.
#defined review_regards/2.
#defined review_attest/1.
#defined content_free/1.

% ---- discharges(R,L): review row R discharges obliged row L's countersign obligation, under
% review_gap's OWN semantics (mirrored exactly -- see header) --------------------------------
discharges(R,L) :-
    review_row(R), review_regards(R,L), review_attest(R),
    row_actor(R,RA), row_actor(L,LA), RA != LA,
    obliged(LA),
    not superseded(L), not superseded(R).

% ---- flagged(R): a discharging review whose OWN statement is content-free ------------------
flagged(R) :- discharges(R,L), content_free(R).

#show discharges/2.
#show flagged/1.
