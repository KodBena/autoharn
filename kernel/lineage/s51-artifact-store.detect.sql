-- s51-artifact-store.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s51 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s40/s42/s43/s50 detect precedent): THREE independent facts, none alone sufficient, all read
-- from always-resolving catalog relations (no possibly-absent relation queried directly; no
-- live INSERT -- a detect has no business mutating a live schema; reads clean f, never errors,
-- on any pre-s51 kernel including a bare s15 one):
--   1. THE TABLE EXISTS: kernel.artifact (a relation named 'artifact' in :kern, relkind 'r') --
--      the one fact a pre-s51 kernel can never exhibit under any prior delta's own name.
--   2. THE BOUNDARY EXISTS: a function named artifact_write in :kern taking jsonb, SECURITY
--      DEFINER (pg_proc.prosecdef) -- the write path this delta mints.
--   3. THE REFUSAL VOCABULARY WAS WIDENED: some CHECK constraint on ledger whose definition
--      carries the literal 'artifact' as a refusal_surface member. ROW-1657 LESSON APPLIED
--      (ledger row 1657, s50-defeat-input-raw-domain.detect.sql's own false-negative under the
--      standard search_path preamble): row 1657's failure was pg_get_viewdef rendering a
--      RELATION reference (a table/view NAME) unqualified under search_path, so a schema-
--      qualified LIKE pattern false-negatived. THIS probe's LIKE pattern matches a bare STRING
--      LITERAL inside a CHECK's value list ('artifact' in refusal_surface_check's own
--      `= ANY (ARRAY['ledger', 'review', ..., 'artifact'])` rendering, or the equivalent IN-list
--      form) -- a literal has no relation-qualification axis to begin with (pg_get_constraintdef
--      never schema-qualifies a plain text constant), so this probe carries none of row 1657's
--      hazard; the constraint is additionally pinned by name (conname = 'refusal_surface_check')
--      and by contype = 'c', not by text-shape alone, so a coincidental substring match elsewhere
--      cannot false-positive it either.
--
-- Witnessed t on an s51-applied scratch chain and f on an s43-head (pre-s51) scratch chain (both
-- polarities) by seen-red/s51-artifact-store/run_fixtures.py.
SELECT
  EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE n.nspname = :'kern' AND c.relname = 'artifact' AND c.relkind = 'r')
  AND EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = :'kern' AND p.proname = 'artifact_write'
      AND p.prosecdef AND p.prokind = 'f'
  )
  AND EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND con.conname = 'refusal_surface_check'
       AND pg_get_constraintdef(con.oid) LIKE '%artifact%'
  )
AS applied;
