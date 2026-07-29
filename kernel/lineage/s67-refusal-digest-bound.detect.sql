-- s67-refusal-digest-bound.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s67 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): s67 adds
-- NO new kind -- ONE new column only (Element 1: refusal_digest_disposition), reissuing
-- kernel.journal_write_refusal to populate it. A NEW COLUMN's mere existence is a fact only
-- s67's ADD COLUMN produces (grep-verified: only s67 ever issues that ALTER TABLE; s68 later
-- adds refusal_attempted_kind_disposition and refusal_attempted_actor_disposition, both
-- DIFFERENT column names, never this one) -- the cheapest, most reliable fingerprint of "s67
-- landed", matching the s51/s53/s65 single-new-object precedent.
--
-- Witnessed t on an s67-applied scratch chain and f on an s66-head (pre-s67) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'refusal_digest_disposition'
  )
AS applied;
