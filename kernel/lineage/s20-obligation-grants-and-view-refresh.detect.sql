-- s20-obligation-grants-and-view-refresh.detect.sql -- sibling DETECT file, per the PER-DELTA
-- VERIFICATION CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen
-- s20 file itself (ADR-0005 Rule 8).
--
-- RE-FINGERPRINTED 2026-07-18 (ledger row 1657's defect (1); design/FABLE-DETECT-REPAIR-SPEC.md):
-- the ORIGINAL fingerprint here probed `:"role"` holding INSERT on countersign_obligation --
-- true on s20 alone, but s43-typed-verdict-write-boundary.sql's Element 7 REVOKEs exactly that
-- INSERT grant from `:"role"` (the write-boundary privilege restructure: `REVOKE INSERT ON
-- :"schema".countersign_obligation FROM :"role"`), so on every world whose chain includes s43
-- this detect read FALSE even though s20's own objects were fully live -- the walk stopped at
-- high_watermark_1 forever (witnessed, ledger row 1657; reproduced pre-fix in this delta's own
-- build). Re-fingerprinted on TWO facts s43 (and every delta after it, through s51 -- the
-- enumerated universe below) NEVER TOUCHES:
--
--   (1) GRANT SELECT (not INSERT) on countersign_obligation to `:"role"` -- s20's own DEFECT (1)
--       fix. s43 Element 7 revokes ONLY INSERT ("REVOKE INSERT ON ... countersign_obligation
--       FROM :"role""; the SELECT grant s20 issued is never named, let alone revoked). Read
--       straight off the read-only grant catalog (same information_schema.role_table_grants
--       convention this detect always used), not a live probe.
--   (2) ledger_current carries the `stamp_verified` column -- s20's own DEFECT (2) fix (the
--       stale `l.*` view re-issued with an EXPLICIT column list that, for the first time, added
--       the five s17 stamp_* columns Postgres's CREATE-time column-freezing had hidden from it).
--       Checked via information_schema.columns (column existence, not a text/LIKE match on
--       pg_get_viewdef -- side-steps the exact search_path-qualification trap that broke s50's
--       detect, named in this same repair spec, since information_schema.columns is never
--       schema-qualification-sensitive the way a rendered view-definition string is).
--
-- WHY THESE TWO SURVIVE EVERY LATER DELTA IN THE SHIPPED CHAIN (s21 through s51, the enumerated
-- universe as of this spec -- verified by reading every one of those files, not assumed):
--   - GRANT SELECT on countersign_obligation: grep-verified, the ONLY other manifest entries that
--     even MENTION countersign_obligation are s29 (comment prose, a different/legacy-vs-typed
--     obligation distinction, no grant statement), s32 (a read JOIN in a view body, not a grant),
--     s42 (a comment listing sibling tables, not a grant), and s43 itself (REVOKE INSERT only,
--     analyzed above). No manifest entry from s21 to s51 issues a REVOKE SELECT, DROP, or
--     re-GRANT touching countersign_obligation's SELECT privilege -- the s20 SELECT grant is
--     therefore the only member of its class in the whole chain and stays live at every later
--     point, exactly like the pre-existing audit note below already established for the
--     (now-superseded) INSERT probe.
--   - `ledger_current.stamp_verified`: grep-verified, `ledger_current` is re-issued by
--     s20/s22/s23/s24/s26/s28/s29/s30/s32/s33/s36/s37/s40/s41/s43/s44 -- every one of those
--     re-issues is an EXPLICIT column list (the s20 lesson: "never `l.*` again" -- s20's own
--     header) that carries `stamp_session, stamp_agent, stamp_ts, stamp_hmac, stamp_verified`
--     unchanged, only ever APPENDING new columns after them (s43 appends 6 refusal_* columns
--     after `stamp_verified`, unchanged in position; s44's re-issue -- the LAST one before head,
--     s46-s51 read `ledger_current` but never re-issue it -- still carries all five stamp_*
--     columns verbatim). No manifest entry from s21 to s51 issues a `DROP COLUMN` on `ledger` or
--     narrows `ledger_current`'s projection (grep-verified: zero `DROP COLUMN` occurrences
--     anywhere in kernel/lineage/s2*.sql, s3*.sql, s4*.sql, s5*.sql). A dropped/narrowed
--     `stamp_verified` would be an independent, much larger defect (breaking every consumer that
--     already reads it, e.g. s17's own review_stamp_distinctness cousin) long before it could
--     silently invalidate this detect -- so this observable is durable by the same construction
--     that keeps the view append-only.
--
-- AUDITED (zero-context audit, 2026-07-15, carried forward unchanged in substance for the SELECT
-- privilege in place of INSERT) for the same false-positive class s21's detect had:
-- information_schema.role_table_grants also lists a table's OWNER as implicitly holding every
-- privilege even when relacl is NULL (no GRANT ever issued) -- witnessed directly on this same
-- toy substrate: `CREATE TABLE t1 (id int);` with zero GRANTs still produces a
-- role_table_grants row for the creating/owning role with privilege_type IN ('SELECT', 'INSERT',
-- ...). So THIS query would false-positive if `:role` ever equaled the role that owns `:schema`
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
--
-- WD2 (this repair spec): on a world genuinely lacking s20 (a bare high_watermark_1 + s17 + s19
-- kernel, no s20 applied), countersign_obligation carries no SELECT grant to `:role` at all
-- (s20's own header: "UNGRANTED since s13/s14/s15") and `ledger_current` (if it exists pre-s20)
-- lacks `stamp_verified` (the CREATE-time column-freeze defect(2) itself) -- so this detect reads
-- FALSE there, exactly as a detect must.
SELECT
    EXISTS (
        SELECT 1 FROM information_schema.role_table_grants
        WHERE table_schema = :'schema' AND table_name = 'countersign_obligation'
          AND grantee = :'role' AND privilege_type = 'SELECT'
    )
    AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = :'schema' AND table_name = 'ledger_current'
          AND column_name = 'stamp_verified'
    )
AS applied;
