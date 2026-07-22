-- s54-belief-views.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION CONVENTION
-- (bootstrap/migrate_core.py module docstring). Never edits the frozen s54 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH: the derived view credited_beliefs exists -- a fact only
-- s54's CREATE OR REPLACE produces (no pre-s54 kernel has this relation at all; reads clean f).
SELECT
  EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'schema' AND c.relname = 'credited_beliefs' AND c.relkind = 'v'
  )
AS applied;
