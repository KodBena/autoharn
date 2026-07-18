-- s49-journaler-overflow-guard.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s49 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the s29/s30 detect ruling of 2026-07-16, ledger item
-- migrate-detect-drift): this delta re-issues an EXISTING function (kernel.journal_write_refusal,
-- :"kern" schema, not :"schema" -- unlike every prior sNN detect this repo ships, which reads
-- :"schema") -- its ONE observable surface is the function BODY gaining the guarded resolution.
-- This detect fingerprints the LITERAL marker text this delta's own new EXCEPTION handler
-- comment/condition carries -- "numeric_value_out_of_range" -- taken VERBATIM from the guard's
-- own WHEN clause, on WHATEVER function :kern owns that carries it (never a name pinned to
-- journal_write_refusal specifically, matching s39/s47/s48's own detect precedent).
-- (Scoped to plain functions only, prokind = 'f' -- pg_get_functiondef errors on
-- aggregates/procedures, matching s39/s47/s48's own detect's identical scoping note.)
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'kern'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%numeric_value_out_of_range%'
  )
AS applied;
