-- s70-scope-binding.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION CONVENTION
-- (bootstrap/migrate_core.py module docstring). Never edits the frozen s70 file itself (ADR-0005
-- Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s53/s57/s58 detect precedent): TWO independent facts together, both read from always-resolving
-- catalog relations (no live INSERT; reads clean f on any pre-s70 kernel):
--   1. THE WIDENED KIND CHECK: ledger_kind_check's definition carries 'principal_scope_bound' --
--      a fact only s70's re-issue produces.
--   2. A NEW COLUMN: ledger.scope_disclosure_mode exists -- a fact only s70's ADD COLUMN
--      produces.
--
-- Witnessed t on an s70-applied scratch chain and f on an s69-head (pre-s70) scratch chain (both
-- polarities), this build's own report (seen-red/s70-scope-binding/run_fixtures.py).
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'ledger_kind_check'
       AND pg_get_constraintdef(con.oid) LIKE '%''principal_scope_bound''%'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'scope_disclosure_mode'
  )
AS applied;
