-- s32-edge-views-single-home.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s32 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied -- the same
-- discipline s29/s30/s31's own detects use): s32 adds NO column and NO base table -- its only new
-- objects are four VIEWS. This detect confirms the simplest reliable positive: the named view
-- `work_edge_obligation` EXISTS in the target schema (a relation that cannot exist on any pre-s32
-- kernel -- no prior delta names it) AND `work_item_strict_blockers()`'s live function body (via
-- pg_get_functiondef, keyed on OID/namespace, never bare name alone) reads FROM the collapsed
-- edge view rather than re-deriving its own two-arm UNION, proving the LIVE function is the s32
-- composed build, not the s29/s30/s31 inline-UNION build of the same-named function.
SELECT
  EXISTS (
    SELECT 1 FROM pg_views WHERE schemaname = :'schema' AND viewname = 'work_edge_obligation'
  )
  AND pg_get_functiondef(
    (SELECT p.oid FROM pg_proc p
       JOIN pg_namespace n ON n.oid = p.pronamespace
      WHERE p.proname = 'work_item_strict_blockers' AND n.nspname = :'schema')
  ) LIKE '%FROM work_edge_obligation%'
AS applied;
