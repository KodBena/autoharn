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
  AND pg_get_functiondef(
        (SELECT p.oid FROM pg_proc p
           JOIN pg_namespace n ON n.oid = p.pronamespace
          WHERE p.proname = 'work_item_strict_blockers' AND n.nspname = :'schema')
      ) LIKE '%edge_type = ''blocks-close''%'
AS applied;
