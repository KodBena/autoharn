-- s63-supersession-body-restoration.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s63 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s49/s52 re-issued-function detect precedent -- this delta adds ZERO columns, ZERO kinds, ZERO
-- new objects, per its own header: its WHOLE observable surface is validate_supersession_target
-- RE-ISSUED with the s58 belief/missive branches restored). This detect fingerprints the
-- LITERAL marker text s58 Element 5 minted for the missive_received branch --
-- "may NEVER be superseded" -- taken VERBATIM from that RAISE EXCEPTION message, on WHATEVER
-- plain function :schema owns that carries it (never a name pinned to
-- validate_supersession_target specifically, matching s39/s47/s48/s49/s52's own detect
-- precedent). This text is present at s58 head, ABSENT at s61/s62 head (s61 Element 7's stale-
-- base CREATE OR REPLACE silently dropped it, s62 does not touch this function at all -- verified
-- by inspection, this delta's own header), and RESTORED at s63 head -- exactly the gap this
-- delta closes, so the marker's presence/absence tracks s63's own applied-ness precisely across
-- the manifest's actual ordered walk (s58's own detect uses a DIFFERENT, disjoint fingerprint --
-- the widened kind check plus missive_thread column -- so the two probes never collide).
-- (Scoped to plain functions only, prokind = 'f' -- pg_get_functiondef errors on
-- aggregates/procedures, matching s39/s47/s48/s49/s52's own detect's identical scoping note.)
--
-- Witnessed t on an s63-applied scratch chain and f on an s62-head (pre-s63) scratch chain
-- (both polarities), this build's own report.
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%may NEVER be superseded%'
  )
AS applied;
