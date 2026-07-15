-- s28-work-parent-edge.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s28 file
-- itself (ADR-0005 Rule 8).
--
-- Detected via `work_parent`, the column s28 adds to `ledger`.
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'work_parent'
) AS applied;
