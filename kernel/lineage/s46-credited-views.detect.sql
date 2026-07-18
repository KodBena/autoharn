-- s46-credited-views.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s46 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): TWO
-- independent facts together, both read from always-resolving catalog relations (no possibly-
-- absent relation queried directly; no live INSERT; reads clean f, never errors, on any pre-s46
-- kernel including a bare s15 one or an s44-head-but-pre-s46 one):
--   1. `credited_current` exists as a view in :schema.
--   2. `model_defeated_rows` exists as a view in :schema, and its definition carries
--      'model_identity_attested' -- a fact only THIS delta's typed-arm-only view produces (no
--      other object in the lineage references that kind).
--
-- Witnessed t on an s46-applied scratch chain (s44 + s46) and f on an s44-head (pre-s46) scratch
-- chain (both polarities) by seen-red/s46-credited-views/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'schema' AND c.relname = 'credited_current' AND c.relkind = 'v'
  )
  AND EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'schema' AND c.relname = 'model_defeated_rows' AND c.relkind = 'v'
       AND pg_get_viewdef(c.oid, true) LIKE '%model_identity_attested%'
  )
AS applied;
