-- s61-signature-symmetry-and-key-binding.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s61 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the s60
-- detect precedent immediately above): TWO independent facts together, both read from
-- always-resolving catalog relations (no live INSERT; reads clean f on any pre-s61 kernel):
--   1. THE WIDENED KIND CHECK: ledger_kind_check's own definition carries
--      'commission_signature_verified' -- a fact only s61's re-issue produces (Element 1).
--   2. A NEW COLUMN: ledger.signature_attests_row exists -- a fact only s61's ADD COLUMN
--      produces (Element 2), and only s61 ever issues that ALTER TABLE (grep-verified against
--      every tracked kernel/lineage/*.sql before writing this probe; s64/s65/s67/s68 later refer
--      to the SAME physical column in their own compute_row_hash serialization comments, never
--      re-adding it).
--
-- Witnessed t on an s61-applied scratch chain and f on an s60-head (pre-s61) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'ledger_kind_check'
       AND pg_get_constraintdef(con.oid) LIKE '%''commission_signature_verified''%'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'signature_attests_row'
  )
AS applied;
