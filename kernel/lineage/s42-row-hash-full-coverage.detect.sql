-- s42-row-hash-full-coverage.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s42 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s29/s30/s37/s38/s39/s40 detect precedent): the fact detected is that the LIVE
-- compute_row_hash body serializes the post-s26 column set -- probed by reading the function's
-- own source (pg_get_functiondef) for references to TWO marker columns from opposite ends of
-- the widened range (`r.work_parent`, the first s28 column, and `r.principal_competence_basis`,
-- the last s41 column), so a partial/hand-truncated re-issue cannot read as applied on either
-- marker alone. No live INSERT (a detect has no business mutating a live schema), and no
-- possibly-absent relation is queried directly: pg_proc/pg_namespace always resolve, so this
-- reads clean f (never errors) against any pre-s42 kernel, including a bare s15 one where
-- compute_row_hash does not exist at all.
--
-- Witnessed t on an s42-applied scratch chain and f on an s41-head scratch chain (both
-- polarities) by seen-red/s42-row-hash-full-coverage/run_fixtures.py.
SELECT EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.proname = 'compute_row_hash'
       AND p.prokind = 'f'  -- plain functions only: pg_get_functiondef errors on aggregates
       AND pg_get_functiondef(p.oid) LIKE '%r.work_parent%'
       AND pg_get_functiondef(p.oid) LIKE '%r.principal_competence_basis%'
) AS applied;
