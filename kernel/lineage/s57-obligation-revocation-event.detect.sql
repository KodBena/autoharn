-- s57-obligation-revocation-event.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s57 file itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH: kernel.obligation_revoke's mere existence, as a
-- SECURITY DEFINER function in :kern, is a fact only s57's CREATE OR REPLACE produces (no pre-s57
-- kernel has this function at all) -- the CHEAPEST, most reliable fingerprint of "s57 landed",
-- exactly the s54/s56 precedent one/two deltas over.
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'kern' AND p.proname = 'obligation_revoke' AND p.prosecdef
  )
AS applied;
