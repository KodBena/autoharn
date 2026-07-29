-- s66-forged-stamp-journal-totality.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s66 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s49/s52 re-issued-function detect precedent): s66 adds ZERO columns, ZERO kinds, ZERO new
-- objects (its own header, verbatim: "no new column, no new kind, no CHECK narrowed or
-- widened") -- its WHOLE observable surface is kernel.set_stamp RE-ISSUED with ONE new ELSIF
-- branch gated on NEW.kind = 'write_refused'. This detect fingerprints the LITERAL marker text
-- that branch's own comment carries -- "s66 GUARD" -- taken VERBATIM from the guard's own
-- header comment inside the function body, on WHATEVER plain function :schema owns that carries
-- it (never a name pinned to set_stamp specifically, matching s39/s47/s48/s49/s52's own detect
-- precedent) -- set_stamp lives in :"schema", not :"kern" (kernel.set_stamp in this file's own
-- header prose refers to it by the project's informal "kernel policy" shorthand, not its actual
-- namespace -- verified by inspection of the CREATE OR REPLACE FUNCTION statement itself,
-- s17/s23/s66 all bind it to :"schema"). Grep-verified unique to this one delta across every
-- tracked kernel/lineage/*.sql.
-- (Scoped to plain functions only, prokind = 'f' -- pg_get_functiondef errors on
-- aggregates/procedures, matching s39/s47/s48/s49/s52's own detect's identical scoping note.)
--
-- Witnessed t on an s66-applied scratch chain and f on an s65-head (pre-s66) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%s66 GUARD%'
  )
AS applied;
