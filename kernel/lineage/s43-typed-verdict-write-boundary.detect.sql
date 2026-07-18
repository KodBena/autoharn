-- s43-typed-verdict-write-boundary.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s43 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s40/s42 detect precedent): THREE independent facts together, none alone sufficient, all read
-- from always-resolving catalog relations (no possibly-absent relation queried directly; no
-- live INSERT -- a detect has no business mutating a live schema; reads clean f, never errors,
-- on any pre-s43 kernel including a bare s15 one):
--   1. THE PRIVILEGE RESTRUCTURE is live: the ledger table exists in :schema AND no
--      non-owner role holds INSERT on it (information_schema.role_table_grants shows no
--      INSERT grant whose grantee differs from the table owner) -- the one fact a pre-s43
--      kernel can never exhibit (s15 grants :role INSERT at birth). Probed via the grants
--      catalog, not has_table_privilege on a hardcoded role name (the role name varies per
--      world).
--   2. THE BOUNDARY EXISTS: a function named ledger_write in :kern taking jsonb, SECURITY
--      DEFINER (pg_proc.prosecdef) -- the write path the revocation hands writes to.
--   3. THE REFUSAL RECORD IS ADMITTED: some CHECK constraint on ledger whose definition
--      carries 'write_refused' (the widened kind vocabulary), via pg_get_constraintdef --
--      never a live INSERT probe.
--
-- Witnessed t on an s43-applied scratch chain and f on an s42-head scratch chain (both
-- polarities) by seen-red/s43-typed-verdict-write-boundary/run_fixtures.py.
SELECT
  EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = :'schema' AND c.relname = 'ledger' AND c.relkind = 'r')
  AND NOT EXISTS (
    SELECT 1 FROM information_schema.role_table_grants g
    WHERE g.table_schema = :'schema' AND g.table_name = 'ledger'
      AND g.privilege_type = 'INSERT'
      AND g.grantee <> (SELECT pg_get_userbyid(c.relowner)
                        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE n.nspname = :'schema' AND c.relname = 'ledger')
  )
  AND EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = :'kern' AND p.proname = 'ledger_write'
      AND p.prosecdef AND p.prokind = 'f'
  )
  AND EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%write_refused%'
  )
AS applied;
