-- s27-chain-high-water.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s27 file
-- itself (ADR-0005 Rule 8).
--
-- Detected via `chain_high_water`, the table s27 creates in the KERNEL schema (`:kern`, not
-- `:schema` -- the one detect query in this directory that reads the kernel namespace, because
-- s27's witness table deliberately lives there, per its own header).
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = :'kern' AND table_name = 'chain_high_water'
) AS applied;
