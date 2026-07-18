-- s50-defeat-input-raw-domain.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s50 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the migrate-detect-drift ruling of 2026-07-16): s50
-- re-issues an EXISTING view (`model_defeated_rows`, s46's own object) under its own s46 name --
-- a name-match or existence check alone cannot distinguish "s46 applied, s50 not yet" from "s46
-- and s50 both applied," so this detect fingerprints the ONE line s50 actually changes: the
-- defeat-input exclusion subquery's FROM-target. Read straight off `pg_get_viewdef`, verified
-- empirically on a live scratch pair before being committed here (not assumed from the SQL
-- source text alone): on the s46-only chain, the exclusion subquery selects `ledger_current.id
-- FROM <schema>.ledger_current WHERE ledger_current.kind = ANY (...)` (the column/table are named
-- `ledger_current` throughout, because Postgres renders an unaliased subquery's projected column
-- qualified by the FROM-relation's own name); on the s50-applied chain the SAME subquery selects
-- `ledger.id FROM <schema>.ledger WHERE ledger.kind = ANY (...)` -- the raw table, no `_current`
-- suffix anywhere in that one subquery. The pattern anchors on `SELECT ledger.id` (which the
-- s46-only rendering can never produce -- its own equivalent text always reads
-- `SELECT ledger_current.id`), plus `FROM ... ledger` and `WHERE ledger.kind = ANY` for the same
-- reason, so a coincidental partial match is not possible: the three fragments only co-occur when
-- the subquery's own FROM-relation is the raw `ledger` table.
--
-- SEARCH_PATH-ROBUSTNESS FIX 2026-07-18 (ledger row 1657's defect (2); design/
-- FABLE-DETECT-REPAIR-SPEC.md): the ORIGINAL pattern's middle fragment, `FROM%.ledger%`, HARD-
-- CODED a literal `.` immediately before `ledger` -- true only when `pg_get_viewdef` renders the
-- FROM-target schema-qualified (`FROM <schema>.ledger`). `pg_get_viewdef` omits the schema
-- qualifier whenever the object's schema sits on the CALLING SESSION's `search_path` (an ordinary
-- Postgres rendering rule, not a bug) -- and every real caller of this detect (`./migrate`,
-- `serving/boundary_service.py`'s `_lineage_head`) connects with `:schema` already on
-- `search_path` (the standing deployment convention), so in every real deployment the rendering
-- was ALWAYS `FROM ledger` (no dot), never `FROM <schema>.ledger` -- the pattern could not match
-- on any real caller, only on a bespoke session that had deliberately unset search_path first.
-- s50 was confirmed genuinely live by a direct viewdef read at the time this was found (ledger
-- row 1657) -- a real false negative, not a hypothetical one.
--
-- FIX: normalize the rendered definition before matching, by stripping the literal
-- `"<schema>."` prefix wherever it occurs (`replace()`, a plain substring substitution -- never a
-- regex, so no metacharacter-escaping question arises for an identifier-shaped `:schema`, and no
-- risk of a coincidental partial match inside unrelated text, since the substituted substring
-- must be the exact three characters `<schema>` immediately followed by `.`). The qualified
-- rendering (`FROM <schema>.ledger`) collapses to the unqualified one (`FROM ledger`) under this
-- normalization; the already-unqualified rendering (`FROM ledger`, the real-world case) is
-- untouched by a substitution that finds nothing to replace. The SAME normalized text then
-- matches the SAME three-fragment pattern, now written without the schema-qualification-
-- dependent dot -- `FROM%ledger%` alone is not ambiguous against `ledger_current` here because
-- the pattern requires `SELECT ledger.id` (never produced by the s46-only rendering, per the
-- paragraph above) to occur first in the same LIKE chain, and the subquery's own single FROM
-- clause is what follows it in the view's DDL text.
--
-- WD3 (this repair spec): witnessed `applied = t` under BOTH a bare search_path (`search_path =
-- ''`, forcing the schema-qualified rendering `FROM <schema>.ledger`) and a schema-including
-- search_path (`search_path = <schema>, public`, forcing the unqualified rendering `FROM
-- ledger`) against the SAME live s50-applied world -- the normalization collapses both renderings
-- to the same matched text.
--
-- Witnessed t on an s46+s50-applied scratch chain and f on an s44+s46-applied (pre-s50) scratch
-- chain (both polarities) by seen-red/s50-defeat-input-raw-domain/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = :'schema' AND c.relname = 'model_defeated_rows' AND c.relkind = 'v'
       AND replace(pg_get_viewdef(c.oid, true), :'schema' || '.', '')
           LIKE '%SELECT ledger.id%FROM%ledger%WHERE ledger.kind = ANY%'
  )
AS applied;
