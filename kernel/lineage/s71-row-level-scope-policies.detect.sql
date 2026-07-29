-- s71-row-level-scope-policies.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s71 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s53/s57/s58/s70 detect precedent): TWO independent facts together, both read from always-
-- resolving catalog relations (no live INSERT; reads clean t/f on any pre-/post-s71 kernel):
--   1. RLS IS ENABLED: pg_class.relrowsecurity is true for :"schema".ledger -- a fact only s71's
--      ALTER TABLE ... ENABLE ROW LEVEL SECURITY produces.
--   2. THE NAMED POLICY EXISTS: pg_policies carries a row for schemaname=:'schema',
--      tablename='ledger', policyname='ledger_scope_read', cmd='SELECT' (pg_policies.cmd is the
--      spelled-out command name, not pg_policy.polcmd's single-char code -- verified live) -- a
--      fact only s71's own CREATE POLICY produces.
--
-- Witnessed t on an s71-applied scratch chain and f on an s70-head (pre-s71) scratch chain (both
-- polarities), this build's own report (seen-red/s71-row-level-scope-policies/run_fixtures.py).
SELECT
  EXISTS (
    SELECT 1 FROM pg_class rel
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND rel.relrowsecurity IS TRUE
  )
  AND EXISTS (
    SELECT 1 FROM pg_policies pol
     WHERE pol.schemaname = :'schema' AND pol.tablename = 'ledger'
       AND pol.policyname = 'ledger_scope_read' AND pol.cmd = 'SELECT'
  )
AS applied;
