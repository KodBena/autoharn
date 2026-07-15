-- s26-row-hash-chain.accommodate.verify.sql -- behavioral verification for the accommodation
-- (bootstrap/migrate_core.py's PER-DELTA VERIFICATION CONVENTION: zero or more SELECTs, each
-- returning exactly one row with one boolean column aliased `ok`). Run by `./migrate` after
-- applying the accommodation, both in rehearsal and against live.
--
-- Equivalence to the birth-chain case (design/MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md sec-2,
-- bullet 4's mechanical test) is proven separately, seen-red/s26-accommodate/, by comparing this
-- world's post-epoch verify-chain walk against a fresh --new-world's own walk over identical
-- post-epoch content -- not restatable as a single-schema SELECT, so it is not duplicated here.

-- (1) migration_epoch is present and carries exactly one row.
SELECT (SELECT count(*) FROM :"kern".migration_epoch) = 1 AS ok;

-- (2) every ledger row strictly after the epoch carries a non-NULL row_hash -- the exact
-- invariant the frozen file's own unconditional SET NOT NULL would have enforced, restated as a
-- live query rather than assumed from the trigger's mere presence.
SELECT NOT EXISTS (
    SELECT 1 FROM :"schema".ledger l, :"kern".migration_epoch e
    WHERE l.id > e.epoch AND l.row_hash IS NULL
) AS ok;

-- (3) the epoch-gated trigger exists (belt-and-braces guarantee is actually installed, not just
-- claimed by this file's header).
SELECT EXISTS (
    SELECT 1 FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = :'schema' AND c.relname = 'ledger'
      AND t.tgname = 'zzz_enforce_row_hash_not_null'
) AS ok;

-- (4) rows at-or-before the epoch are UNTOUCHED by this accommodation (still legitimately NULL
-- where they were NULL before -- this accommodation never backfills, per spec sec-2 principle
-- 3's rejection of backfill as its own class of dishonesty). A world with zero pre-existing
-- history (epoch = 0) has no such rows, so this is vacuously true there -- the SAME query
-- degrades correctly for both a migrated and a birth-chain world.
SELECT (
    SELECT count(*) FROM :"schema".ledger l, :"kern".migration_epoch e
    WHERE l.id <= e.epoch AND l.row_hash IS NOT NULL
) = 0 AS ok;
