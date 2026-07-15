-- high_watermark_1.detect.sql -- sibling DETECT file for high_watermark_1.sql, per the
-- PER-DELTA VERIFICATION CONVENTION documented in bootstrap/migrate_core.py's module docstring.
-- Never edits high_watermark_1.sql itself (ADR-0005 Rule 8 -- a shipped generation is a
-- point-in-time record); this is a new, purely additive sibling file.
--
-- high_watermark_1.sql chains s15-schema.sql -> s17-stamp-mechanism.sql ->
-- s17-independence-vocabulary.sql -> s19-trigger-search-path.sql in one apply (kernel/lineage/
-- README.md). Detected here via `stamp_hmac`, the column s17-stamp-mechanism.sql adds to
-- `ledger` -- the single latest-landing, uniquely-named object of the four files this bundle
-- applies, so its presence implies the whole bundle already ran (nothing in this lineage removes
-- a column once added, so a later delta's presence never falsely implies an earlier one's
-- absence -- and conversely no other manifest entry adds a column named `stamp_hmac`).
--
-- Run with: -v schema=... -v kern=... -v role=... (kern/role unused by this particular check,
-- accepted only so every detect file in this directory takes the same three variables).
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger' AND column_name = 'stamp_hmac'
) AS applied;
