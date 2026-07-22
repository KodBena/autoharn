-- s55-dispatch-grain-independence.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s55 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH: review_detail_independence_check's definition carries
-- 'disclosed-isolated-dispatch' -- a fact only s55's re-issue produces (the s17-era CHECK names
-- four values, none of them this one; reads clean f on any pre-s55 kernel).
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'review_detail' AND con.contype = 'c'
       AND con.conname = 'review_detail_independence_check'
       AND pg_get_constraintdef(con.oid) LIKE '%disclosed-isolated-dispatch%'
  )
AS applied;
