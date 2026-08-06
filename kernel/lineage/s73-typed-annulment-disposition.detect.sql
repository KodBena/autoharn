-- s73-typed-annulment-disposition.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s73 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the s29/s30 detect ruling of 2026-07-16, ledger item
-- migrate-detect-drift): this detect confirms TWO independent facts together, neither pinned to
-- a single named object:
--   1. the work_review_disposition_check CONSTRAINT's own definition (pg_get_constraintdef, keyed
--      on the constraint's OID, never a bare column-presence check -- work_review_disposition
--      itself already exists as of s29, so a column-presence check alone would false-positive on
--      an s29..s72 schema that has not yet applied s73) contains the literal marker text
--      'annulled', proving the CHECK's own vocabulary was actually widened, not merely that some
--      other object mentions the string.
--   2. SOME function or view :schema owns (never one pinned name) contains the literal marker
--      text "work_review_disposition = 'annulled'" -- taken VERBATIM from this delta's own
--      validate_review_witness_existence/validate_work_item_close bodies and work_review_annulled
--      view -- proving a LIVE object actually reads/branches on the new value, not merely that
--      the CHECK admits it in principle.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint c
      JOIN pg_namespace n ON n.oid = c.connamespace
     WHERE n.nspname = :'schema'
       AND c.conname = 'work_review_disposition_check'
       AND pg_get_constraintdef(c.oid) LIKE '%annulled%'
  )
  AND (
    EXISTS (
      SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
       WHERE n.nspname = :'schema'
         AND p.prokind = 'f'  -- plain functions only: pg_get_functiondef errors on aggregates
         AND pg_get_functiondef(p.oid) LIKE '%work_review_disposition = ''annulled''%'
    )
    OR EXISTS (
      SELECT 1 FROM pg_views v
       WHERE v.schemaname = :'schema'
         AND v.definition LIKE '%work_review_disposition = ''annulled''%'
    )
  )
AS applied;
