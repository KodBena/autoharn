-- s52-artifact-witness-check.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s52 file
-- itself (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (the s29/s30 detect ruling of 2026-07-16, ledger item
-- migrate-detect-drift): this delta's ONE observable surface is a NEW trigger function whose
-- body carries the literal marker text "artifact-witness citation" (taken VERBATIM from that
-- function's own RAISE EXCEPTION messages -- both the malformed-hex and the missing-hash arms
-- share this exact phrase) -- on WHATEVER plain function :schema owns that carries it, never a
-- name pinned to validate_artifact_witness_existence specifically (a future refactor could
-- single-home this check elsewhere, the s32/s39/s48 precedent this ruling exists to survive).
-- (Scoped to plain functions only, prokind = 'f' -- pg_get_functiondef errors on
-- aggregates/procedures, matching s39/s47/s48's own detect's identical scoping note.)
--
-- ROW-1657 LESSON APPLIED (ledger row 1657, s50-defeat-input-raw-domain.detect.sql's own
-- false-negative under the standard search_path preamble): row 1657's failure was
-- pg_get_viewdef rendering a RELATION reference (a table/view NAME) unqualified under
-- search_path, which made a schema-qualified LIKE pattern false-negative. THIS probe's LIKE
-- pattern matches a bare STRING LITERAL inside a RAISE EXCEPTION message body
-- (pg_get_functiondef's own rendering of a plpgsql function's source text, which is stored and
-- rendered VERBATIM -- string literals inside a function body carry no relation-qualification
-- axis at all, the same reasoning s51's own detect already applied one field over to a CHECK
-- constraint's value-list literal), so this probe carries none of row 1657's hazard. The marker
-- text is additionally distinct from s48's own detect marker ("review-witness citation" vs this
-- file's "artifact-witness citation"), so a schema carrying BOTH s48 and s52 triggers cannot
-- collapse the two probes into one false-positive for either.
--
-- Witnessed t on an s52-applied scratch chain and f on an s51-head (pre-s52) scratch chain (both
-- polarities) by seen-red/s52-artifact-witness-check/run_fixtures.py.
SELECT
  EXISTS (
    SELECT 1 FROM pg_proc p
      JOIN pg_namespace n ON n.oid = p.pronamespace
     WHERE n.nspname = :'schema'
       AND p.prokind = 'f'
       AND pg_get_functiondef(p.oid) LIKE '%artifact-witness citation%'
  )
AS applied;
