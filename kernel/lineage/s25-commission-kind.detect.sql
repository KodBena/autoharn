-- s25-commission-kind.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s25 file
-- itself (ADR-0005 Rule 8).
--
-- s25 replaces `ledger_kind_check` to add 'commission' to the allowed `kind` vocabulary.
-- Detected by reading the live constraint definition back and checking for that literal --
-- the constraint is CREATEd fresh by s25 (DROP IF EXISTS + ADD), so its definition is exactly
-- what the applied file wrote, not a guess.
SELECT EXISTS (
    SELECT 1 FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = :'schema' AND t.relname = 'ledger' AND c.conname = 'ledger_kind_check'
      AND pg_get_constraintdef(c.oid) LIKE '%commission%'
) AS applied;
