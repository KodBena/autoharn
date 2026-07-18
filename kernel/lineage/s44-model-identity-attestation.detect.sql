-- s44-model-identity-attestation.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s44 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s40/s42/s43/s45 detect precedent): TWO independent facts together, both read from
-- always-resolving catalog relations (no possibly-absent relation queried directly; no live
-- INSERT -- a detect has no business mutating a live schema; reads clean f, never errors, on
-- any pre-s44 kernel including a bare s15 one):
--   1. THE WIDENED KIND CHECK: ledger_kind_check's definition carries
--      'model_identity_attested' -- a fact only s44's re-issue produces (the s43-era CHECK
--      names twenty-four kinds, none of them this one).
--   2. THE DERIVED VIEW: :"schema".model_attestations exists as a view -- a fact only s44's
--      CREATE OR REPLACE produces (no pre-s44 kernel has this relation at all).
--
-- Witnessed t on an s44-applied scratch chain and f on an s45-head (pre-s44) scratch chain
-- (both polarities) by seen-red/s44-model-identity-attestation/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'ledger_kind_check'
       AND pg_get_constraintdef(con.oid) LIKE '%model_identity_attested%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'schema' AND c.relname = 'model_attestations' AND c.relkind = 'v'
  )
AS applied;
