-- s59-missive-views.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s59 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16; the
-- s54/s56 new-object detect precedent, restated -- s59 ships new objects only, no re-issue of
-- anything s58 defined, so a single-fact "does the view exist" check is honest here, matching
-- s54-belief-views.detect.sql's own shape): view `missive_outbound` exists -- a fact only s59's
-- CREATE VIEW produces.
--
-- Witnessed t on an s59-applied scratch chain and f on an s58-head (pre-s59) scratch chain
-- (both polarities), this build's own report.
SELECT EXISTS (
  SELECT 1 FROM information_schema.views
   WHERE table_schema = :'schema' AND table_name = 'missive_outbound'
) AS applied;
