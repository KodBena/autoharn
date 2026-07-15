-- s29-obligation-item-key-and-typed-close.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s29 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied): a detect that
-- only checked column presence (work_review_disposition on ledger) could false-positive on some
-- future, differently-semantic delta that happens to reuse the same column name. This detect
-- instead confirms THREE independent facts together, the same "does the live BODY carry this
-- delta's own marker" discipline finding 781 fixed s21's detect with:
--   1. :"kern".migration_epoch is a REAL, CATALOG-VISIBLE table (via information_schema.tables,
--      never a literal `FROM :"kern".migration_epoch` -- see the NEVER-QUERY-A-POSSIBLY-ABSENT-
--      RELATION note below for why).
--   2. ledger carries work_review_disposition (Element B's own column) AND review_detail carries
--      discharge_grade (Element C's own column).
--   3. validate_work_item()'s own function BODY (via pg_get_functiondef, keyed on the function's
--      OID/namespace, never its bare name alone) contains the literal marker text 'sec-10 epoch
--      amendment' -- taken VERBATIM from that function's own RAISE EXCEPTION message (not merely
--      a comment, which pg_get_functiondef would not even reproduce) -- proving the LIVE trigger
--      is the sec-10 EPOCH-AWARE amendment (which reads migration_epoch AND refuses a
--      review-silent post-epoch close with this exact wording), not a pre-amendment build of this
--      same file that used a bare, epoch-blind CHECK constraint instead (a shape this schema
--      could carry from an earlier, unamended scratch apply).
--
-- NEVER QUERY A POSSIBLY-ABSENT RELATION DIRECTLY (bootstrap/migrate_core.py's own documented
-- lesson, section 7's "ACTUALLY delta-independent" comment: "a single statement referencing the
-- [possibly absent] table always errors ... regardless of which CASE arm runs" -- Postgres binds
-- a literal relation name at PARSE time, before any runtime branch is even considered). A first
-- draft of this file wrote `(SELECT count(*) FROM :"kern".migration_epoch) = 1` directly --
-- witnessed FAILING with `relation "migration_epoch" does not exist` against exactly the
-- deployment this detect exists to recognize as "s29 NOT yet applied" (any pre-s29 head, autoharn1
-- included), turning `./migrate`'s missing-chain computation into a hard error instead of a clean
-- `applied=false`. Fixed the same way `information_schema.columns` already sidesteps this for
-- ordinary columns: `information_schema.tables` is queried instead of the table itself -- catalog
-- metadata about a relation is always resolvable, whether or not the relation exists.
SELECT
  EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = :'kern' AND table_name = 'migration_epoch'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'ledger'
      AND column_name = 'work_review_disposition'
  )
  AND EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = :'schema' AND table_name = 'review_detail'
      AND column_name = 'discharge_grade'
  )
  AND pg_get_functiondef(
        (SELECT p.oid FROM pg_proc p
           JOIN pg_namespace n ON n.oid = p.pronamespace
          WHERE p.proname = 'validate_work_item' AND n.nspname = :'schema')
      ) LIKE '%sec-10 epoch amendment%'
AS applied;
