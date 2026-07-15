-- s30-typed-dependency-edges.verify.sql -- sibling VERIFY file (OPTIONAL per the PER-DELTA
-- VERIFICATION CONVENTION, bootstrap/migrate_core.py module docstring), run by ./migrate AFTER this
-- delta is applied (rehearsal AND live) to confirm the invariant BEHAVES on the LIVE data, not
-- merely that the objects exist (`.detect.sql`'s job). Each SELECT below returns exactly one row,
-- one boolean column aliased `ok`. Never edits the frozen s30 file itself (ADR-0005 Rule 8).

-- 1. THE SHAPE INVARIANT ITSELF, behaviorally: no NON-work_depends_on row ever carries a non-NULL
--    edge_type (the ONE-WAY CHECK's own job, re-confirmed against live data rather than merely
--    trusting the constraint is still attached). A work_depends_on row's edge_type MAY be NULL
--    (any pre-s30 legacy row -- unwritable by the append-only guarantee, see this delta's own
--    HISTORY header) or a legal non-NULL value; both are fine, so this check does not require
--    edge_type IS NOT NULL on work_depends_on rows the way a two-way iff would.
SELECT NOT EXISTS (
    SELECT 1 FROM :"schema".ledger
    WHERE kind <> 'work_depends_on' AND edge_type IS NOT NULL
) AS ok;

-- 2. THE CLOSED VOCABULARY, behaviorally: no live row carries an edge_type outside
--    {blocks-close, informs} -- in particular, 'supersedes' never appears here (the REVIEW NOTE
--    DISPOSITION's reserved-word refusal, re-confirmed against live data).
SELECT NOT EXISTS (
    SELECT 1 FROM :"schema".ledger
    WHERE edge_type IS NOT NULL AND edge_type NOT IN ('blocks-close', 'informs')
) AS ok;

-- 3. NO BLOCKS-CLOSE EDGE DANGLES: every blocks-close antecedent has an opening act (Element 2's
--    endpoint refusal, re-confirmed behaviorally -- a bypassed-trigger write is the only way this
--    could ever be false, the same disclosed bound every trigger-enforced refusal in this lineage
--    carries).
SELECT NOT EXISTS (
    SELECT 1 FROM :"schema".ledger d
    WHERE d.kind = 'work_depends_on' AND d.edge_type = 'blocks-close'
      AND NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = d.work_depends_on)
) AS ok;

-- 4. NO BLOCKS-CLOSE SELF-EDGE and NO BLOCKS-CLOSE CYCLE survive live: both are PROVABLY VACUOUS
--    under normal operation (refused at construction), re-confirmed via work_item_violations'
--    defense-in-depth read (this delta's own new blocks_close_cycle member) plus a direct self-edge
--    scan.
SELECT NOT EXISTS (
    SELECT 1 FROM :"schema".ledger
    WHERE kind = 'work_depends_on' AND edge_type = 'blocks-close' AND work_depends_on = work_slug
) AND NOT EXISTS (
    SELECT 1 FROM :"schema".work_item_violations WHERE violation = 'blocks_close_cycle'
) AS ok;

-- 5. THE ELEMENT 3 FILTER IS LIVE: work_item_strict_blockers()'s function body carries the
--    blocks-close marker (belt-and-braces re-confirmation of what .detect.sql already fingerprints,
--    kept here too so a verify-only consumer that skips detect still catches a stale pre-s30 build).
SELECT pg_get_functiondef(
        (SELECT p.oid FROM pg_proc p
           JOIN pg_namespace n ON n.oid = p.pronamespace
          WHERE p.proname = 'work_item_strict_blockers' AND n.nspname = :'schema')
      ) LIKE '%edge_type = ''blocks-close''%'
AS ok;
