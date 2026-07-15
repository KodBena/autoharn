-- s20-obligation-grants-and-view-refresh.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s20 file itself (ADR-0005 Rule 8).
--
-- s20's own defect (1), fixed: `:"role"` had SELECT+INSERT granted on countersign_obligation.
-- Detected via information_schema.role_table_grants -- the grant s20 adds and no other manifest
-- entry touches.
--
-- AUDITED (zero-context audit, 2026-07-15) for the same false-positive class s21's detect had:
-- information_schema.role_table_grants also lists a table's OWNER as implicitly holding every
-- privilege even when relacl is NULL (no GRANT ever issued) -- witnessed directly on this same
-- toy substrate: `CREATE TABLE t1 (id int);` with zero GRANTs still produces a
-- role_table_grants row for the creating/owning role with privilege_type IN ('INSERT', ...).
-- So THIS query would false-positive if `:role` ever equaled the role that owns `:schema`
-- (i.e. the DB user new-project.sh/./migrate connect as when creating the schema). Verdict:
-- NOT a real vector for how this lineage is actually deployed -- s15-schema.sql's own role-
-- creation block (`CREATE ROLE :"role" LOGIN INHERIT` iff it does not already exist) and
-- new-project.sh's `--new-world` naming convention (`--role` always `<world>_rw`, distinct from
-- the operator/OS DB user that runs the scaffold and therefore owns the schemas it creates)
-- together guarantee `:role` is a freshly-created, non-owning role, never the connecting/owning
-- user, in every scripted deployment path. The vector only opens if an operator hand-passes
-- `--role <the-connecting-user>` against the documented convention -- named here rather than
-- silently assumed away, but not fixed, since there is no sound query-level fix that
-- distinguishes "owner with an implicit grant" from "owner with an explicit matching GRANT" and
-- the documented path never produces the former.
SELECT EXISTS (
    SELECT 1 FROM information_schema.role_table_grants
    WHERE table_schema = :'schema' AND table_name = 'countersign_obligation'
      AND grantee = :'role' AND privilege_type = 'INSERT'
) AS applied;
