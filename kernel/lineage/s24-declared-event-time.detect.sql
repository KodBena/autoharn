-- s24-declared-event-time.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s24 file
-- itself (ADR-0005 Rule 8).
--
-- Detected via `event_declared_ts`, the column s24 adds to `ledger`.
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'event_declared_ts'
) AS applied;
