-- s38-bookkeeping-close.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s38 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson; the migrate-detect-drift
-- ruling of 2026-07-16, s29/s30/s37's own detect siblings: a fingerprint pinned to a single named
-- object silently false-negatives the moment a later refactor moves the marker elsewhere -- e.g.
-- s35's dispatcher refactor moving s29's own marker into a leaf, or s32 single-homing s30's filter
-- into a view). This detect confirms TWO independent facts together, neither alone sufficient, and
-- neither naming a specific function/view as the sole carrier -- each is a SHAPE search over the
-- whole schema's catalog:
--   1. the WIDENED VOCABULARY is live: SOME CHECK constraint on ledger (any name, any owning
--      object) whose pg_get_constraintdef text contains the literal 'bookkeeping' AND the literal
--      'work_review_disposition' -- proving the third value is actually admitted by a live CHECK,
--      never a bare `SELECT ... FROM ledger` probe insert (which would write a real row against a
--      live schema this detect has no business mutating, and would error outright on a pre-s38
--      schema with no bookkeeping-shaped semantics to accept it).
--   2. the NEW SHAPE CHECK is live: SOME CHECK constraint on ledger (any name) whose
--      pg_get_constraintdef text contains the literal 'bookkeeping' AND the literal
--      'work_review_ref' AND the literal regex marker '[0-9a-f]' -- proving a commit-shaped-ref
--      requirement exists FOR the bookkeeping value specifically, not merely that the word
--      'bookkeeping' appears somewhere incidental (e.g. a future, unrelated delta's own CHECK that
--      happens to mention the same word in a comment -- pg_get_constraintdef never includes SQL
--      comments, only the constraint's own normalized expression text, so this risk is already
--      structurally foreclosed, named here for a zero-context reader rather than left implicit).
--
-- NEVER QUERY A POSSIBLY-ABSENT RELATION/COLUMN/CONSTRAINT DIRECTLY (bootstrap/migrate_core.py's
-- own documented lesson, restated verbatim in s37's own detect sibling): every fact below is read
-- through pg_constraint (a catalog view that is ALWAYS resolvable regardless of whether any
-- particular constraint exists) -- no branch of this detect can hard-error against any pre-s38
-- schema, including a bare s15-only kernel with no work_review_disposition column at all (a CHECK
-- naming a nonexistent column simply cannot exist in that schema's pg_constraint, so both EXISTS
-- clauses below correctly read false, never error).
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%bookkeeping%'
       AND pg_get_constraintdef(con.oid) LIKE '%work_review_disposition%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%bookkeeping%'
       AND pg_get_constraintdef(con.oid) LIKE '%work_review_ref%'
       AND pg_get_constraintdef(con.oid) LIKE '%[0-9a-f]%'
  )
AS applied;
