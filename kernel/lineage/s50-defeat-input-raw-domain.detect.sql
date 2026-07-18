-- s50-defeat-input-raw-domain.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s50 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): s50
-- re-issues an EXISTING view (`model_defeated_rows`, s46's own object) under its own s46 name --
-- a name-match or existence check alone cannot distinguish "s46 applied, s50 not yet" from "s46
-- and s50 both applied," so this detect fingerprints the ONE line s50 actually changes: the
-- defeat-input exclusion subquery's FROM-target. Read straight off `pg_get_viewdef`, verified
-- empirically on a live scratch pair before being committed here (not assumed from the SQL
-- source text alone): on the s46-only chain, the exclusion subquery selects `ledger_current.id
-- FROM <schema>.ledger_current WHERE ledger_current.kind = ANY (...)` (the column/table are named
-- `ledger_current` throughout, because Postgres renders an unaliased subquery's projected column
-- qualified by the FROM-relation's own name); on the s50-applied chain the SAME subquery selects
-- `ledger.id FROM <schema>.ledger WHERE ledger.kind = ANY (...)` -- the raw table, no `_current`
-- suffix anywhere in that one subquery. The pattern below anchors on `SELECT ledger.id` (which the
-- s46-only rendering can never produce -- its own equivalent text always reads
-- `SELECT ledger_current.id`), plus `FROM %.ledger` and `WHERE ledger.kind = ANY` for the same
-- reason, so a coincidental partial match is not possible: the three fragments only co-occur when
-- the subquery's own FROM-relation is the raw `ledger` table.
--
-- Witnessed t on an s46+s50-applied scratch chain and f on an s44+s46-applied (pre-s50) scratch
-- chain (both polarities) by seen-red/s50-defeat-input-raw-domain/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'schema' AND c.relname = 'model_defeated_rows' AND c.relkind = 'v'
       AND pg_get_viewdef(c.oid, true) LIKE '%SELECT ledger.id%FROM%.ledger%WHERE ledger.kind = ANY%'
  )
AS applied;
