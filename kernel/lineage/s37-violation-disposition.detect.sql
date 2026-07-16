-- s37-violation-disposition.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s37 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson; sharpened by the
-- migrate-detect-drift fix on s29/s30's own detects, 2026-07-16, restated in the s29/s30 detect
-- siblings' own headers: a fingerprint pinned to a single named object silently false-negatives
-- the moment a later refactor moves the marker elsewhere -- e.g. s35's dispatcher refactor moving
-- s29's marker into a leaf, or s32 single-homing s30's filter into a view). This detect confirms
-- THREE independent facts together, none alone sufficient, and NONE of them names a specific
-- function/view/trigger as the sole carrier -- each is a SHAPE search over the whole schema's
-- catalog:
--   1. ledger carries all three new columns (information_schema.columns -- never a bare
--      `SELECT work_violation_class FROM ledger`, which would error on a pre-s37 schema and turn
--      a clean applied=false into a hard failure).
--   2. the SHAPE INVARIANT is live: SOME CHECK constraint on ledger (any name, any owning
--      object) whose pg_get_constraintdef text contains the literal marker
--      'work_violation_target_id IS NOT NULL' -- proving the column is not merely present (a
--      differently-semantic future delta reusing the same column name could also produce that)
--      but carries THIS delta's own two-way kind-restriction shape. Read via pg_constraint/
--      pg_get_constraintdef keyed on the constraint's OID, never a bare name lookup.
--   3. a CATALOG-VISIBLE VIEW behavior-fingerprint (ADR-0011 Rule 4's "the class, never one
--      pinned name" -- this delta's own views could themselves be renamed/refactored into
--      differently-named objects by a future delta, exactly the s29/s32 precedent that motivated
--      the 2026-07-16 fix): SOME view :schema owns has a definition (via pg_views.definition,
--      never a bare `SELECT * FROM work_item_violations`, which would error on a pre-s37 schema)
--      containing BOTH 'work_violation_target_id' and the literal narrowing-join marker
--      'work_violation_disposition' -- proving a LIVE view reads the disposition-answered shape
--      through the kernel's own mechanism, not merely that a same-named view exists with
--      different semantics. This also independently confirms the validator's own re-derivation
--      posture is reachable (the view IS the re-derivation the trigger queries).
--
-- NEVER QUERY A POSSIBLY-ABSENT RELATION/COLUMN/CONSTRAINT DIRECTLY (bootstrap/migrate_core.py's
-- own documented lesson, section 7's "ACTUALLY delta-independent" comment): every fact below is
-- read through a catalog view (information_schema.columns, pg_constraint, pg_views) that is
-- ALWAYS resolvable regardless of whether the underlying object exists -- no branch of this
-- detect can hard-error against any pre-s37 schema, including a bare s15-only kernel.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger'
      AND column_name IN ('work_violation_class', 'work_violation_target_id', 'work_violation_witness')
    HAVING count(*) = 3
  )
  AND EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%work_violation_target_id IS NOT NULL%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_views v
     WHERE v.schemaname = :'schema'
       AND v.definition LIKE '%work_violation_target_id%'
       AND v.definition LIKE '%work_violation_disposition%'
  )
AS applied;
