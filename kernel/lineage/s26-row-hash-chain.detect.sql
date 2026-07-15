-- s26-row-hash-chain.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s26 file
-- itself (ADR-0005 Rule 8).
--
-- Detected via `row_hash`, the column s26 adds to `ledger`.
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'row_hash'
) AS applied;
