-- s65-refusal-attempted-kind.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s65 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): s65 adds
-- NO new kind -- ONE new column only (Element 1: refusal_attempted_kind), reissuing
-- kernel.journal_write_refusal/kernel.ledger_write to populate it. A NEW COLUMN's mere existence
-- is a fact only s65's ADD COLUMN produces (grep-verified: only s65 ever issues that ALTER
-- TABLE; s68 later adds refusal_attempted_kind_DISPOSITION, a DIFFERENT column name, never this
-- bare one) -- the cheapest, most reliable fingerprint of "s65 landed", matching the s51/s53
-- single-new-object precedent (a new column is exactly as much a new catalog object as a new
-- view/function, for this purpose).
--
-- Witnessed t on an s65-applied scratch chain and f on an s64-head (pre-s65) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'refusal_attempted_kind'
  )
AS applied;
