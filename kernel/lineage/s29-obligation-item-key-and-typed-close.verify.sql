-- s29-obligation-item-key-and-typed-close.verify.sql -- sibling VERIFY file (OPTIONAL per the
-- PER-DELTA VERIFICATION CONVENTION, bootstrap/migrate_core.py module docstring), run by
-- ./migrate AFTER this delta is applied (rehearsal AND live) to confirm the invariant BEHAVES,
-- not merely that the objects exist (`.detect.sql`'s job). s29 is "the FIRST delta shipped with
-- both files from birth" (migrate_core.py's own docstring, naming this file explicitly). Each
-- SELECT below returns exactly one row, one boolean column aliased `ok`. Never edits the frozen
-- s29 file itself (ADR-0005 Rule 8).

-- 1. THE EPOCH INVARIANT ITSELF, behaviorally: every work_closed row STRICTLY PAST the recorded
--    epoch carries a non-NULL disposition (the trigger's own job -- this re-reads the LIVE data
--    to confirm the invariant holds, the same "behave, not just exist" standard the module
--    docstring names). Rows at-or-before the epoch are DELIBERATELY excluded from this check --
--    they are exempt BY TYPE (sec-10), so their disposition being NULL is not a defect.
SELECT NOT EXISTS (
    SELECT 1 FROM :"schema".ledger l, :"kern".migration_epoch m
    WHERE l.kind = 'work_closed' AND l.id > m.epoch AND l.work_review_disposition IS NULL
) AS ok;

-- 2. THE EPOCH ROW ITSELF is sane: exactly one row, non-negative, and no larger than the current
--    ledger max id (an epoch claiming to be "in the future" relative to the ledger it was drawn
--    from would be a defect in how it was written, not a fact about this world).
SELECT (SELECT count(*) FROM :"kern".migration_epoch) = 1
   AND (SELECT epoch FROM :"kern".migration_epoch LIMIT 1) >= 0
   AND (SELECT epoch FROM :"kern".migration_epoch LIMIT 1)
       <= COALESCE((SELECT max(id) FROM :"schema".ledger), 0)
AS ok;

-- 3. THE OLD, EPOCH-BLIND CHECK CONSTRAINT IS GONE (sec-10's whole reason for existing): if some
--    earlier, pre-amendment apply of this file left `work_review_disposition_kind_shape` behind
--    as a table CHECK, this file's own DROP CONSTRAINT IF EXISTS (see the amendment) must have
--    removed it -- otherwise a historical deployment migrating THROUGH the pre-amendment build
--    would still carry the exact constraint the ent rehearsal falsified.
SELECT NOT EXISTS (
    SELECT 1 FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = :'schema' AND t.relname = 'ledger'
      AND c.conname = 'work_review_disposition_kind_shape'
) AS ok;
