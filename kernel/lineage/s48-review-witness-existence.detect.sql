-- s48-review-witness-existence.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s48 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the s29/s30 detect ruling of 2026-07-16, ledger item
-- migrate-detect-drift): this delta's ONE observable surface is a NEW trigger function whose body
-- carries the literal marker text "review-witness citation" (taken VERBATIM from that function's
-- own RAISE EXCEPTION message) -- on WHATEVER plain function :schema owns that carries it, never a
-- name pinned to validate_review_witness_existence specifically (a future refactor could
-- single-home this check elsewhere, the s32/s39 precedent this ruling exists to survive).
-- (Scoped to plain functions only, prokind = 'f' -- pg_get_functiondef errors on
-- aggregates/procedures, matching s39/s47's own detect's identical scoping note.)
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%review-witness citation%'
  )
AS applied;
