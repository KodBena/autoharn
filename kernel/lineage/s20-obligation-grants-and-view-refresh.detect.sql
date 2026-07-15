-- s20-obligation-grants-and-view-refresh.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s20 file itself (ADR-0005 Rule 8).
--
-- s20's own defect (1), fixed: `:"role"` had SELECT+INSERT granted on countersign_obligation.
-- Detected via information_schema.role_table_grants -- the grant s20 adds and no other manifest
-- entry touches.
SELECT EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
    WHERE table_schema = :'schema' AND table_name = 'countersign_obligation'
      AND grantee = :'role' AND privilege_type = 'INSERT'
) AS applied;
