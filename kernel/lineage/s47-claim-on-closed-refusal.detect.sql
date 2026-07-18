-- s47-claim-on-closed-refusal.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s47 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the s29/s30 detect ruling of 2026-07-16, ledger item
-- migrate-detect-drift): this delta adds NO new column and NO new CHECK constraint (unlike s39's
-- own edge_type_check widening) -- its ONE observable surface is validate_work_item_claim's own
-- function BODY gaining the new closed-item check. A future refactor could single-home this check
-- elsewhere (the s32/s39 precedent this ruling exists to survive), so this detect fingerprints the
-- LITERAL marker text this delta's own new RAISE EXCEPTION message carries -- "is not claimable"
-- -- taken VERBATIM from that message, on WHATEVER function or view :schema owns that carries it,
-- never a name pinned to validate_work_item_claim specifically. (The marker is scoped to plain
-- functions only, prokind = 'f' -- pg_get_functiondef errors on aggregates/procedures, matching
-- s39's own detect's identical scoping note.)
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%is not claimable%'
  )
AS applied;
