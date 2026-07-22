-- s56-reservation-residue.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s56 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH: the derived view reservations_outstanding exists -- a
-- fact only s56's CREATE OR REPLACE produces (no pre-s56 kernel has this relation at all; reads
-- clean f). A pre-s56 discharging_attest also lacks the widened verdict IN (...) predicate this
-- delta introduces, but the CHEAPEST, most reliable fingerprint of "s56 landed" is the NEW
-- object's mere existence, exactly the s54 precedent (credited_beliefs) one delta over.
SELECT
  EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'schema' AND c.relname = 'reservations_outstanding' AND c.relkind = 'v'
  )
AS applied;
