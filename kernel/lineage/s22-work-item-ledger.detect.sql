-- s22-work-item-ledger.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s22 file
-- itself (ADR-0005 Rule 8).
--
-- Detected via `work_slug`, the first of s22's five new `ledger` columns.
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'work_slug'
) AS applied;
