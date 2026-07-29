-- s60-entitlement-enforcement.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s60 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s58/s59 detect precedent one delta back): TWO independent facts together, both read from
-- always-resolving catalog relations (no live INSERT; reads clean f on any pre-s60 kernel):
--   1. THE WIDENED KIND CHECK: ledger_kind_check's own definition carries
--      'entitlement_class_configured' -- a fact only s60's re-issue produces (Element 1).
--   2. A NEW COLUMN: ledger.entitlement_act_class exists -- a fact only s60's ADD COLUMN
--      produces (Element 2), and only s60 ever issues that ALTER TABLE (grep-verified against
--      every tracked kernel/lineage/*.sql before writing this probe).
--
-- Witnessed t on an s60-applied scratch chain and f on an s59-head (pre-s60) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'ledger_kind_check'
       AND pg_get_constraintdef(con.oid) LIKE '%''entitlement_class_configured''%'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'entitlement_act_class'
  )
AS applied;
