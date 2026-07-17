-- s39-blocks-start.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION CONVENTION
-- (bootstrap/migrate_core.py module docstring). Never edits the frozen s39 file itself (ADR-0005
-- Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the s29/s30 detect ruling of 2026-07-16, ledger item
-- migrate-detect-drift, applied here from the start rather than retrofitted after a future
-- refactor moves the marker -- s35's dispatcher-into-leaves move and s32's edge-source
-- single-homing are the two witnessed cases this ruling exists to survive): this detect confirms
-- TWO independent facts together, neither pinned to a single named object:
--   1. the edge_type_check CONSTRAINT's own definition (pg_get_constraintdef, keyed on the
--      constraint's OID, never a bare column-presence check -- edge_type itself already exists as
--      of s30, so a column-presence check alone would false-positive on an s30..s38 schema that
--      has not yet applied s39) contains the literal marker text "blocks-start", proving the
--      CHECK's own vocabulary was actually widened, not merely that some other object mentions the
--      string.
--   2. SOME function or view :schema owns (never one pinned name -- a future refactor may
--      single-home the blocks-start filter into a different object, exactly as s32 did for
--      blocks-close) contains the literal marker text "edge_type = 'blocks-start'" -- taken
--      VERBATIM from this delta's own work_edge_blocks_start view and validate_work_item_depends'
--      new branch -- proving a LIVE object actually FILTERS on the new value, not merely that the
--      CHECK admits it in principle.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint c
      JOIN pg_namespace n ON n.oid = c.connamespace
     WHERE n.nspname = :'schema'
       AND c.conname = 'edge_type_check'
       AND pg_get_constraintdef(c.oid) LIKE '%blocks-start%'
  )
  AND (
    EXISTS (
      SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
       WHERE n.nspname = :'schema'
         AND p.prokind = 'f'  -- plain functions only: pg_get_functiondef errors on aggregates
         AND pg_get_functiondef(p.oid) LIKE '%edge_type = ''blocks-start''%'
    )
    OR EXISTS (
      SELECT 1 FROM pg_views v
       WHERE v.schemaname = :'schema'
         AND v.definition LIKE '%edge_type = ''blocks-start''%'
    )
  )
AS applied;
