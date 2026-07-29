-- s64-principal-stamps-delegation-conditions.detect.sql -- sibling DETECT file, per the
-- PER-DELTA VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits
-- the frozen s64 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): s64 adds
-- NO new kind (its own Element 1 header, verbatim: "NO new kind") -- so there is no widened
-- ledger_kind_check to lean on. TWO independent facts together instead, both read from
-- always-resolving catalog relations (no live INSERT; reads clean f on any pre-s64 kernel):
--   1. A NEW COLUMN: ledger.delegation_redelegate_depth exists -- a fact only s64's ADD COLUMN
--      produces (Element 1), and only s64 ever issues that ALTER TABLE (grep-verified against
--      every tracked kernel/lineage/*.sql before writing this probe).
--   2. A NEW FUNCTION: principal_redelegate_budget(pid) exists -- a fact only s64's Element 6
--      CREATE produces, no pre-existing reader, no other file ever creates this name.
--
-- Witnessed t on an s64-applied scratch chain and f on an s63-head (pre-s64) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'delegation_redelegate_depth'
  )
  AND EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.proname = 'principal_redelegate_budget'
  )
AS applied;
