-- s68-typed-absence-dispositions.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s68 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): s68 adds
-- NO new kind -- TWO new columns (Element 1: refusal_attempted_kind_disposition and
-- refusal_attempted_actor_disposition), reissuing kernel.journal_write_refusal to populate them.
-- TWO independent NEW-COLUMN facts together, both read from always-resolving catalog relations
-- (no live INSERT; reads clean f on any pre-s68 kernel), each a fact only s68's own ADD COLUMN
-- produces (grep-verified: only s68 ever issues either ALTER TABLE).
--
-- Witnessed t on an s68-applied scratch chain and f on an s67-head (pre-s68) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'refusal_attempted_kind_disposition'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_schema = :'schema' AND table_name = 'ledger'
       AND column_name = 'refusal_attempted_actor_disposition'
  )
AS applied;
