-- s69-role-coherence-refusals.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s69 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s49/s52/s63 re-issued-function detect precedent): s69 adds ZERO columns, ZERO kinds, ZERO
-- views (its own header, verbatim: "This delta adds NO new columns, NO new kinds, NO new views")
-- -- its WHOLE observable surface is FOUR re-issued trigger functions, each gaining one new
-- refusal branch (or, for the rider, a pure teach-text spelling change). This detect fingerprints
-- the LITERAL marker text §1's new branch carries -- "claimant-of-record" -- taken VERBATIM from
-- validate_work_item_close's own new RAISE EXCEPTION message, on WHATEVER plain function :schema
-- owns that carries it (never a name pinned to validate_work_item_close specifically, matching
-- s39/s47/s48/s49/s52/s63's own detect precedent). Grep-verified unique to this one delta across
-- every tracked kernel/lineage/*.sql.
-- (Scoped to plain functions only, prokind = 'f' -- pg_get_functiondef errors on
-- aggregates/procedures, matching s39/s47/s48/s49/s52/s63's own detect's identical scoping note.)
--
-- Witnessed t on an s69-applied scratch chain and f on an s68-head (pre-s69) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%claimant-of-record%'
  )
AS applied;
