-- s40-principal-identity-events.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s40 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson; the migrate-detect-drift
-- ruling of 2026-07-16, s29/s30/s37/s38/s39's own detect siblings: a fingerprint pinned to a
-- single named object silently false-negatives the moment a later refactor moves the marker
-- elsewhere). This detect confirms THREE independent facts together, none alone sufficient, and
-- none naming one specific function/view as the sole carrier:
--   1. the WIDENED KIND VOCABULARY is live: SOME CHECK constraint on ledger (any name) whose
--      pg_get_constraintdef text contains BOTH 'principal_registered' AND
--      'principal_standing_declared' -- proving the identity-event kinds are actually admitted
--      by a live CHECK, never a live INSERT probe (which would write a real row against a live
--      schema this detect has no business mutating, and would error outright on a pre-s40
--      schema).
--   2. STRICT ATTRIBUTION is live, fingerprinted on BEHAVIOR: SOME function the :schema owns
--      (any name -- today set_actor, but a future decomposition could move the marker, exactly
--      the s35-dispatcher precedent the detect-drift ruling names) whose pg_get_functiondef
--      text contains the strict-refusal teach marker 'declare-standing' -- the refusal text a
--      pre-s40 body cannot carry (s19's set_actor has no refusal at all; the pre-s40 failure
--      mode was a bare NOT NULL violation).
--   3. principal_role is a VIEW, not a table, in the kernel namespace (pg_views on :'kern') --
--      the table->view conversion is the one non-purely-additive s40 act, and its presence
--      distinguishes an s40 kernel from every earlier one structurally, via information-schema-
--      class catalog reads only (the s40 delta's own detect requirement, basis §3.5:
--      "view-vs-table for principal_role via information_schema").
--
-- NEVER QUERY A POSSIBLY-ABSENT RELATION/COLUMN/CONSTRAINT DIRECTLY (bootstrap/migrate_core.py's
-- own documented lesson): every fact below reads pg_constraint/pg_proc/pg_views -- catalog
-- relations that always resolve -- so no branch can hard-error against any pre-s40 schema,
-- including a bare s15-only kernel (all three EXISTS clauses correctly read false there, never
-- error). Witnessed t on an s40-applied scratch chain and f on an s39-head scratch chain (both
-- polarities) by seen-red/s40-principal-identity-events/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%principal_registered%'
       AND pg_get_constraintdef(con.oid) LIKE '%principal_standing_declared%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'  -- plain functions only: pg_get_functiondef errors on aggregates
       AND pg_get_functiondef(p.oid) LIKE '%declare-standing%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_views v
     WHERE v.schemaname = :'kern' AND v.viewname = 'principal_role'
  )
AS applied;
