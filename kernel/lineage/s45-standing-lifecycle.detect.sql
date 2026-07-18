-- s45-standing-lifecycle.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s45 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s40/s42/s43 detect precedent): FOUR independent facts together, none alone sufficient, all
-- read from always-resolving catalog relations (no possibly-absent relation queried directly;
-- no live INSERT -- a detect has no business mutating a live schema; reads clean f, never
-- errors, on any pre-s45 kernel including a bare s15 one):
--   1. THE WIDENED CHECK: principal_binding_active_kind_shape's definition carries
--      'principal_standing_declared' -- a fact only s45's re-issue produces (the s41-era CHECK
--      names only the four binding kinds).
--   2. THE RESURRECTION-PROOF VIEW: kernel.principal_role's definition carries
--      'principal_binding_active' -- a fact only s45's re-issue produces (the s40/s43-era view
--      never references that column at all).
--   3. THE IN-FORCE SUSPENSION FILTER: kernel.principal_standing's definition carries
--      'principal_binding_active' -- a fact only s45's re-issue produces (the s40-era function
--      never references that column at all).
--   4. THE LIFECYCLE SUPERSESSION MARKER: validate_supersession_target's definition carries
--      's45-standing-lifecycle' -- a fact only s45's re-issue produces (the s43-era trigger's
--      only self-citation is 's43-typed-verdict-write-boundary').
--
-- Witnessed t on an s45-applied scratch chain and f on an s43-head scratch chain (both
-- polarities) by seen-red/s45-standing-lifecycle/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'principal_binding_active_kind_shape'
       AND pg_get_constraintdef(con.oid) LIKE '%principal_standing_declared%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'kern' AND c.relname = 'principal_role' AND c.relkind = 'v'
       AND pg_get_viewdef(c.oid, true) LIKE '%principal_binding_active%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'kern' AND p.proname = 'principal_standing' AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%principal_binding_active%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema' AND p.proname = 'validate_supersession_target'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%s45-standing-lifecycle%'
  )
AS applied;
