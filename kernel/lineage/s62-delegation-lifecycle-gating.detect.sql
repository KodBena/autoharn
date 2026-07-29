-- s62-delegation-lifecycle-gating.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s62 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): s62 adds
-- ZERO columns and ZERO kinds -- its whole observable surface is re-issuing two EXISTING
-- functions (entitlement_act_class_of, validate_entitlement, s60's own) plus TWO BRAND NEW
-- functions with no pre-existing reader: entitlement_act_class_of_target and
-- entitlement_enforce_class (round 2, row 1403). A name-match/existence check on either NEW
-- function is the cheapest, most reliable fingerprint of "s62 landed" -- no s60/s61-head kernel
-- has either of these names at all (grep-verified against every tracked kernel/lineage/*.sql
-- before writing this probe: only s62 and s64 -- which re-issues both unedited, per s64's own
-- header -- ever CREATE these names, so existence alone, once true, stays true through s64+ as
-- well, correctly).
-- (Scoped to plain functions only, prokind = 'f' -- pg_get_functiondef errors on
-- aggregates/procedures, matching s39/s47/s48's own detect's identical scoping note; not
-- exercised here since existence alone suffices, kept for parity with this repo's own idiom.)
--
-- Witnessed t on an s62-applied scratch chain and f on an s61-head (pre-s62) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.proname = 'entitlement_act_class_of_target'
  )
AS applied;
