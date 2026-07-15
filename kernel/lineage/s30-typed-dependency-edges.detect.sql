-- s30-typed-dependency-edges.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s30 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied a third time, same
-- discipline s29's own detect already used): a detect that only checked column presence (edge_type
-- on ledger) could false-positive on some future, differently-semantic delta that happens to reuse
-- the same column name. This detect instead confirms TWO independent facts together:
--   1. ledger carries the edge_type column (information_schema.columns -- never a bare `SELECT
--      edge_type FROM ledger`, which would error on a pre-s30 schema and turn a clean
--      applied=false into a hard failure -- the same NEVER-QUERY-A-POSSIBLY-ABSENT-COLUMN lesson
--      s29's own detect names for a possibly-absent RELATION, applied here to a possibly-absent
--      COLUMN).
--   2. work_item_strict_blockers()'s own function BODY (via pg_get_functiondef, keyed on the
--      function's OID/namespace, never its bare name alone) contains the literal marker text
--      "edge_type = 'blocks-close'" -- taken VERBATIM from this delta's own Element 3 filter (not a
--      comment, which pg_get_functiondef would not reproduce) -- proving the LIVE function is the
--      s30-filtered build, not a pre-s30 (s29-only) build of the same-named function that walked
--      every work_depends_on row regardless of type. This is the SAME class of function-body
--      fingerprint s29's own detect uses for validate_work_item()'s "sec-10 epoch amendment" marker,
--      applied here to work_item_strict_blockers() instead.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger'
      AND column_name = 'edge_type'
  )
  -- REVISED 2026-07-16 (maintainer-authorized, same verbatim authorization as s29's sibling;
  -- ledger item migrate-detect-drift): the marker was pinned to work_item_strict_blockers()'s
  -- own body, but s32 single-homed the blocks-close filter into the work_edge_blocks_close
  -- VIEW (its whole point, ADR-0012 P1) -- so the fingerprint now accepts the filter's
  -- presence in ANY function OR view :schema owns (behavior-fingerprint over the schema,
  -- never over one pinned name).
  AND (
    EXISTS (
      SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
       WHERE n.nspname = :'schema'
         AND p.prokind = 'f'  -- plain functions only: pg_get_functiondef errors on aggregates
         AND pg_get_functiondef(p.oid) LIKE '%edge_type = ''blocks-close''%'
    )
    OR EXISTS (
      SELECT 1 FROM pg_views v
       WHERE v.schemaname = :'schema'
         AND v.definition LIKE '%edge_type = ''blocks-close''%'
    )
  )
AS applied;
