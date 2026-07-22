-- s53-belief-substrate.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s53 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s44/s48/s52 detect precedent): TWO independent facts together, both read from always-
-- resolving catalog relations (no live INSERT; reads clean f on any pre-s53 kernel):
--   1. THE WIDENED KIND CHECK: ledger_kind_check's definition carries 'belief' -- a fact only
--      s53's re-issue produces.
--   2. A NEW COLUMN: ledger.belief_polarity exists -- a fact only s53's ADD COLUMN produces.
--
-- Witnessed t on an s53-applied scratch chain and f on an s52-head (pre-s53) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'ledger_kind_check'
       AND pg_get_constraintdef(con.oid) LIKE '%''belief''%'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'belief_polarity'
  )
AS applied;
