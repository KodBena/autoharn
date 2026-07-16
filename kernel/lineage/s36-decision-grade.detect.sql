-- s36-decision-grade.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s36 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied by every prior
-- detect in this lineage, most recently sharpened by the migrate-detect-drift fix on s29/s30's own
-- detects, 2026-07-16: a fingerprint pinned to a single named object silently false-negatives the
-- moment a later refactor moves the marker elsewhere -- so this detect confirms the marker's
-- PRESENCE ANYWHERE :schema owns the shape, not the presence of one hardcoded name). This detect
-- confirms THREE independent facts together, none alone sufficient:
--   1. ledger carries the decision_grade column (information_schema.columns -- never a bare
--      `SELECT decision_grade FROM ledger`, which would error on a pre-s36 schema and turn a
--      clean applied=false into a hard failure -- the NEVER-QUERY-A-POSSIBLY-ABSENT-COLUMN
--      lesson every detect in this lineage since s29/s30 already applies).
--   2. the SHAPE INVARIANT is live: a CHECK constraint on ledger whose pg_get_constraintdef
--      text contains the literal marker 'decision_grade IS NULL' -- proving the column is not
--      merely present (which a differently-semantic future delta reusing the same column name
--      could also produce) but carries THIS delta's own kind-restriction shape. Read via
--      pg_constraint/pg_get_constraintdef keyed on the constraint's OID (never a bare name
--      lookup that could error if the constraint were renamed or absent), matching the
--      function-body-fingerprint discipline s29/s30/s34's own detects already use for triggers,
--      applied here to a CHECK constraint instead.
--   3. a CATALOG-VISIBLE VIEW behavior-fingerprint (ADR-0011 Rule 4's "the class, never one
--      pinned name" -- this delta's own view could itself be renamed or refactored into a
--      differently-named object by a future delta, exactly the s29/s32 precedent that motivated
--      the 2026-07-16 migrate-detect-drift fix): SOME view :schema owns has a definition (via
--      pg_views.definition, never a bare `SELECT * FROM standing_decisions`, which would error
--      on a pre-s36 schema) containing BOTH 'decision_grade' and the literal in-force filter
--      text "kind = 'decision'" -- proving a LIVE view reads the graded-decision shape through
--      the kernel's current-truth projection, not merely that a same-named view exists with
--      different semantics.
--
-- NEVER QUERY A POSSIBLY-ABSENT RELATION/COLUMN/CONSTRAINT DIRECTLY (bootstrap/migrate_core.py's
-- own documented lesson, section 7's "ACTUALLY delta-independent" comment, re-applied a sixth
-- time): every fact below is read through a catalog view (information_schema.columns,
-- pg_constraint, pg_views) that is ALWAYS resolvable regardless of whether the underlying object
-- exists -- no branch of this detect can hard-error against any pre-s36 schema, including a bare
-- s15-only kernel.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger'
      AND column_name = 'decision_grade'
  )
  AND EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%decision_grade IS NULL%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_views v
     WHERE v.schemaname = :'schema'
       AND v.definition LIKE '%decision_grade%'
       AND v.definition LIKE '%kind = ''decision''%'
  )
AS applied;
