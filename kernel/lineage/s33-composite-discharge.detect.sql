-- s33-composite-discharge.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s33 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied -- the same
-- discipline s29/s30/s31/s32's own detects use). s33 adds one COLUMN (work_discharge, on
-- ledger) and one derived VIEW COLUMN (work_item_current.effective_state) plus one derived
-- VIEW MEMBER (work_item_violations.closed_but_tree_defeated) -- no new relation. This detect
-- confirms three independent facts together:
--   1. the `work_discharge` column exists on `ledger` (a column no prior delta names).
--   2. `work_item_current`'s live view definition (via pg_get_viewdef) carries the column
--      `effective_state` -- proving the LIVE view is the s33 build, not an s29..s32 build of the
--      same-named view.
--   3. `work_item_violations`'s live view definition contains the literal member tag
--      'closed_but_tree_defeated' -- proving the s33 member landed.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'work_discharge'
  )
  AND pg_get_viewdef((:'schema' || '.work_item_current')::regclass) LIKE '%effective_state%'
  AND pg_get_viewdef((:'schema' || '.work_item_violations')::regclass) LIKE '%closed_but_tree_defeated%'
AS applied;
