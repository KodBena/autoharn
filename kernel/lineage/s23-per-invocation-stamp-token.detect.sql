-- s23-per-invocation-stamp-token.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s23 file itself (ADR-0005 Rule 8).
--
-- Detected via `stamp_invocation`, the column s23 adds to `ledger`.
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'stamp_invocation'
) AS applied;
