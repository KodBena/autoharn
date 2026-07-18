-- s41-principal-bindings-and-relations.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s41 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; s29/s30/
-- s37/s38/s39/s40's own detect siblings). THREE independent facts, none alone sufficient, none
-- pinned to a single named object; all catalog reads (pg_constraint/pg_proc always resolve, so
-- no branch can hard-error on a pre-s41 schema -- every clause reads false there, never errors;
-- no live INSERT is ever attempted):
--   1. the WIDENED KIND VOCABULARY is live: SOME CHECK on ledger whose constraintdef contains
--      BOTH 'principal_relation_asserted' AND 'principal_competence_granted' (the first and
--      fourth s41 kinds -- the fourth being the maintainer-ruled competence build, row 1411, so
--      its presence distinguishes the RATIFIED s41 from any hypothetical three-kind draft).
--   2. the CANONICAL-ORDER CLOSURE is live: SOME CHECK on ledger whose constraintdef contains
--      'same-natural-person' AND 'principal_subject < principal_object' -- the kernel-enforced
--      canonicalization (D-3's fourth refusal), a shape no other delta could plausibly carry.
--   3. D-6 is live, fingerprinted on BEHAVIOR: SOME function the :schema owns whose
--      pg_get_functiondef contains the human-attested-scoping refusal marker
--      'no schema can witness' -- today validate_independence, but a future decomposition
--      could move the marker (the s35-dispatcher precedent), so the search is schema-wide.
-- Witnessed t on an s41-applied scratch chain and f on an s40-head scratch chain (both
-- polarities) by seen-red/s41-principal-bindings-and-relations/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%principal_relation_asserted%'
       AND pg_get_constraintdef(con.oid) LIKE '%principal_competence_granted%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_constraint con
      JOIN pg_class rel ON rel.oid = con.conrelid
      JOIN pg_namespace ns ON ns.oid = rel.relnamespace
     WHERE ns.nspname = :'schema' AND rel.relname = 'ledger' AND con.contype = 'c'
       AND pg_get_constraintdef(con.oid) LIKE '%same-natural-person%'
       AND pg_get_constraintdef(con.oid) LIKE '%principal_subject < principal_object%'
  )
  AND EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'  -- plain functions only: pg_get_functiondef errors on aggregates
       AND pg_get_functiondef(p.oid) LIKE '%no schema can witness%'
  )
AS applied;
