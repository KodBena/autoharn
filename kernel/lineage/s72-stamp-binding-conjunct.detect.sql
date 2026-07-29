-- s72-stamp-binding-conjunct.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s72 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s53/s57/s58/s70 detect precedent): TWO independent facts together, both read from always-
-- resolving catalog relations (no live INSERT; reads clean f on any pre-s72 kernel):
--   1. THE WIDENED KIND CHECK: ledger_kind_check's definition carries 'principal_stamp_bound' --
--      a fact only s72's re-issue produces.
--   2. A NEW COLUMN: ledger.stamp_binding_agent exists -- a fact only s72's ADD COLUMN produces.
--
-- Witnessed t on an s72-applied scratch chain and f on an s71-head (pre-s72) scratch chain (both
-- polarities), this build's own report (seen-red/s72-stamp-binding-conjunct/run_fixtures.py).
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'ledger_kind_check'
       AND pg_get_constraintdef(con.oid) LIKE '%''principal_stamp_bound''%'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'stamp_binding_agent'
  )
AS applied;
