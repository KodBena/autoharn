-- s31-supersession-uniform-retraction.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s31 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied -- the same
-- discipline s29/s30's own detects use): s31 adds NO column and NO relation, so a
-- presence-of-object check cannot fingerprint it at all. This detect instead confirms TWO
-- independent BEHAVIORAL facts together, each taken verbatim from the delta's own body text (not
-- comments, which pg_get_functiondef/pg_get_viewdef would not reproduce):
--   1. work_item_strict_blockers()'s live function BODY (via pg_get_functiondef, keyed on
--      OID/namespace, never bare name alone) reads `FROM ledger_current` -- proving the live
--      function is the s31 in-force-factored build, not the s29/s30 raw-`ledger` build of the
--      same-named function.
--   2. work_item_violations' live VIEW definition (via pg_get_viewdef) contains the literal
--      member tag 'orphaned_by_retraction' -- proving the s31 member landed, not merely that the
--      view exists (it has existed since s22).
-- Together these fingerprint exactly this delta's two behavioral surfaces (the reader
-- re-factoring and the new derived member); neither can be true on a pre-s31 kernel, and a future
-- delta reusing either marker would have to reproduce s31's own semantics to do so.
SELECT
  pg_get_functiondef(
    (SELECT p.oid FROM pg_proc p
       JOIN pg_namespace n ON n.oid = p.pronamespace
      WHERE p.proname = 'work_item_strict_blockers' AND n.nspname = :'schema')
  ) LIKE '%FROM ledger_current%'
  AND pg_get_viewdef((:'schema' || '.work_item_violations')::regclass)
      LIKE '%orphaned_by_retraction%'
AS applied;
