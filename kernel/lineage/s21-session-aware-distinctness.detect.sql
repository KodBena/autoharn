-- s21-session-aware-distinctness.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s21 file itself (ADR-0005 Rule 8).
--
-- Detected via the `validate_independence` trigger s21 installs on `review_detail` -- a
-- uniquely-named object this delta alone creates.
SELECT EXISTS (
    SELECT 1 FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = :'schema' AND c.relname = 'review_detail'
      AND t.tgname = 'validate_independence'
) AS applied;
