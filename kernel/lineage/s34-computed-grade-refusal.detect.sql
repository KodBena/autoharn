-- s34-computed-grade-refusal.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s34 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied by s29's own
-- detect and carried forward here): a detect that only checked column presence (discharge_grade
-- on review_detail) could false-positive on any pre-s34 kernel back to s29, which already carries
-- that column. This detect instead confirms `validate_independence()`'s own function BODY (via
-- pg_get_functiondef, keyed on the function's OID/namespace, never its bare name alone) contains
-- the literal marker text 'ledger finding 1157' -- taken VERBATIM from this delta's own RAISE
-- EXCEPTION message (not merely a comment, which pg_get_functiondef would not even reproduce) --
-- proving the LIVE trigger is the s34 REFUSE-non-NULL-on-entry amendment, not a pre-s34 build of
-- this same function (s29's or s21's or s17's own version, each of which this schema could carry
-- from an earlier, unamended scratch apply).
--
-- NEVER QUERY A POSSIBLY-ABSENT RELATION/FUNCTION DIRECTLY (bootstrap/migrate_core.py's own
-- documented lesson, re-applied per s29's own detect precedent): `pg_get_functiondef` over a
-- `pg_proc` lookup that may return NO ROW (validate_independence undefined entirely, i.e. a
-- pre-s17 kernel) must not error the whole detect -- the subquery is wrapped so a missing function
-- yields NULL (and therefore `applied = false`), never a hard SQL error, keeping this detect's own
-- `applied` computation delta-independent exactly as bootstrap/migrate_core.py's section 7 requires.
SELECT
  COALESCE(
    pg_get_functiondef(
      (SELECT p.oid FROM pg_proc p
         JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE p.proname = 'validate_independence' AND n.nspname = :'schema')
    ) LIKE '%ledger finding 1157%',
    false
  )
AS applied;
