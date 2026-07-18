-- s50 DEFEAT-INPUT RAW-HISTORY DOMAIN (design/FABLE-S46-DEFEAT-INPUT-DOMAIN-SPEC.md, RATIFICATION
-- ledger row 1647 -- maintainer-delegated adjudication, "I have to yield competence on the matter
-- to you," read plainly per the 2026-07-11 vocabulary note; Fable-authored, next free sNN at build
-- time confirmed by directory listing (s46/s47/s48/s49 exist, s50 free)). Sonnet-executed per the
-- standing delegation contract, from this ratified spec.
--
-- ADR-0000 2(a), the two questions this delta answers: (a) the TYPE that forecloses "the view's
-- defeat-input exclusion and the engine's defeat-input exclusion quantify over different domains"
-- is a SINGLE shared quantification domain for "was this row ever machinery input" -- raw history,
-- the engine's own domain (engine/lp/ledger_defeat.lp's `defeat_input/1`, fed by attest_row/1 +
-- grant_row/1 EDB families that engine/ledger_edb.py's attest_row/grant_row NEVER ledger_current-
-- filter; engine/ledger_floor.py::defeat_floor_atoms's SQL twin mirrors this exactly --
-- `attest_any`/`grant_any` both read the raw relation `{rel}`, unfiltered by supersession, and
-- `grant_any` in particular carries NO active/binding/activity narrowing at all, matching
-- `grant_row(G)` "EVERY principal_competence_granted row, active or not"); s46's own header
-- (kernel/lineage/s46-credited-views.sql, ELEMENT 1, "NAMED CHOICE" paragraph) named the
-- divergence as a spec-silent choice at its own authoring -- this delta is the maintainer's
-- resolution of that named choice, not a fresh defect discovery. (b) the operational lapse
-- (ADR-0000 Rule 2(b), self-directed, executive-owned) is that s46's own commission (design/
-- FABLE-DEFEAT-PIPELINE-SPEC.md §8) fixed the kernel view to "typed columns only, ledger_current
-- only" without asking whether the ENGINE's own defeat-input test read the same table -- the two
-- producers of `./judge --layer defeat` (ledger_defeat.lp, ledger_floor.py) were built to the raw-
-- history domain from the start, and the kernel view's ledger_current-only mandate silently pulled
-- ONE of its own predicates (the exclusion) off that shared domain without the divergence being
-- asked about at s46's own build time; it was named, not silently absorbed (s46's header again),
-- and row 1647 is the asking answered.
--
-- THE RULING (row 1647, verbatim grounds, transcribed from design/FABLE-S46-DEFEAT-INPUT-DOMAIN-
-- SPEC.md's own "The ruling" section): the engine differential is authoritative and the view is
-- display-only, so where they diverge the view is wrong by architecture; "was this row ever
-- machinery input" is a history fact (the s31 reader-discipline class of `LDuplicateOpen`) --
-- later supersession cannot retroactively un-input it; and the direction is fail-safe -- raw
-- history excludes strictly MORE rows from defeat, so nothing becomes newly defeatable.
--
-- CLASS: NOT letter-2(a) (it re-issues an existing view definition, changing its semantics on the
-- divergence shape) -- built under the row-1647 delegated ratification, not the class-ratified
-- fail-safe track s48/s49 use. Effect is strictly protective: the only behavioral change is that
-- rows previously defeatable-by-the-view-only stop being so (WS46-c below witnesses this
-- mechanically as an empty set-difference in the newly-defeatable direction).
--
-- MECHANISM: re-issues (CREATE OR REPLACE) ONLY `model_defeated_rows` -- the sole s46 view whose
-- defeat-input exclusion reads ledger_current (verified against kernel/lineage/s46-credited-
-- views.sql in full before authoring: `credited_current`, s46 ELEMENT 2, carries NO defeat-input
-- exclusion of its own -- it is `ledger_current MINUS model_defeated_rows.row_id`, a wholly
-- different predicate; per the spec's own "if only one does, one is" instruction, only ELEMENT 1
-- is re-issued here). The ONLY text change from s46's own shipped definition: the exclusion
-- subquery's `FROM :"schema".ledger_current` becomes `FROM :"schema".ledger` (the raw table, the
-- s31-discipline's OWN raw leg, used elsewhere in this same lineage e.g. kernel/lineage/
-- s31-supersession-uniform-retraction.sql's own `:"schema".ledger` reads) -- matching the engine
-- producers' unfiltered-by-supersession domain exactly. NO join, column, grant, security_invoker
-- setting, or any other predicate changes: the two main-query legs (the attestation leg, the grant
-- leg) are BYTE-IDENTICAL to s46's own text; only the exclusion subquery's FROM-target changes.
--
-- PREREQUISITE: this delta REQUIRES s46 (kernel/lineage/s46-credited-views.sql) applied first --
-- it re-issues `model_defeated_rows`, the view s46 defined, in the EXACT shape s46 left it except
-- for the one named subquery change. Applying this file on a pre-s46 kernel fails loudly at
-- CREATE OR REPLACE VIEW time (there is no prior `model_defeated_rows` to re-issue, and no
-- `ledger_current`/`ledger` columns of the s44 shape for it to read), the correct, disclosed
-- failure mode for a hard dependency, matching every prior delta's own PREREQUISITE precedent
-- (s47's identical posture, verbatim-mirrored here).
--
-- HISTORY: safe -- ONE existing object (`model_defeated_rows`, s46's own view) re-issued with its
-- exclusion subquery's FROM-target changed from `ledger_current` to `ledger`; every other line is
-- byte-identical to s46's own shipped text. No table, column, kind, or CHECK constraint of any
-- kind is added or altered. `credited_current` is NOT touched (it carries no defeat-input
-- exclusion of its own -- named above). compute_row_hash untouched (ZERO ledger columns, ZERO
-- kinds, mirroring s46's own "WHAT THIS DELTA DOES NOT TOUCH" posture).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's own slice):
--   - INVARIANT: in an s46+world carrying this delta, `model_defeated_rows`'s defeat-input
--     exclusion (ELEMENT 1's own "THE DEFEAT-INPUT EXCLUSION MIRRORED" paragraph) quantifies over
--     EVERY attestation/grant row EVER WRITTEN (raw history, including superseded ones) exactly as
--     the engine's `defeat_input/1` (ledger_defeat.lp) and its SQL twin's `attest_any`/`grant_any`
--     (ledger_floor.py::defeat_floor_atoms) do -- the two domains no longer diverge on the
--     kind-changing-supersession shape s46's own header named.
--   - QUANTIFICATION UNIVERSE: the change is scoped to exactly ONE axis -- the defeat-input
--     exclusion subquery's row-source (ledger_current -> ledger) -- named explicitly as the ONLY
--     axis touched; every other axis of `model_defeated_rows` (attestation-leg join, grant-leg
--     join, verdict filter, kind literals, security_invoker, GRANT) is UNCHANGED, and named as
--     unchanged rather than silently left; the sibling surface `credited_current` carries no
--     defeat-input exclusion and is therefore out of this delta's scope, named rather than
--     silently skipped (mirroring the spec's own "if only one does, one is" instruction).
--   - DENOMINATION: the exclusion still compares immutable ledger row ids against a closed pair of
--     kind literals ('model_identity_attested', 'principal_competence_granted') -- unchanged from
--     s46; only the row-source relation changed, never the comparison's currency.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT class-ratified fail-safe
-- (it changes an EXISTING view's semantics on the divergence shape, not a pure addition) -- ships
-- under design/FABLE-S46-DEFEAT-INPUT-DOMAIN-SPEC.md's own row-1647 delegated ratification. The
-- DIRECTION is fail-safe (raw history excludes strictly MORE rows than ledger_current-only ever
-- could, so nothing becomes newly defeatable -- WS46-c witnesses this mechanically), which is the
-- ground the ratification itself rests on, not a claim of class-ratified routing.
--
-- LIMITS (pre-registered, per the spec's own build-conditions section):
--   - This delta does not touch the v1 statement-convention arm (s46's own TYPED-ARM-ONLY choice
--     stands, unrevisited here) -- named, not silently left.
--   - Live operation awaits an s46+ world entering a scaffold's LINEAGE_CHAIN (the maintainer's
--     own act, per runs-are-strictly-linear) -- UNEXERCISED live, scratch-witnessed only, exactly
--     as s46/s47/s48/s49 stand at this same build time.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s46/.../s49):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s50val -v kern=s50val_kernel -v role=s50val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        ... (s21..s45 as in s46's own VALIDATE list) ... \
--        -f s44-model-identity-attestation.sql -f s46-credited-views.sql \
--        -f s50-defeat-input-raw-domain.sql
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's birth
--   chain via bootstrap/new-project.sh's LINEAGE_CHAIN, ONLY as the maintainer's own act
--   (runs-are-strictly-linear, 2026-07-11) -- NOT wired by this commit. Authored and
--   scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE VIEW).
-- ============================================================================================

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif
\if :{?role}
\else
  \set role vsr_rw
\endif

-- ============================================================================================
-- ELEMENT 1 (re-issue) -- model_defeated_rows: BYTE-IDENTICAL to s46's own shipped text except
-- the exclusion subquery's FROM-target, `ledger_current` -> `ledger` (raw history, matching the
-- engine producers' own unfiltered-by-supersession domain).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".model_defeated_rows
    WITH (security_invoker = true) AS
SELECT DISTINCT
       a.attest_row_id AS row_id,
       a.id             AS attest_id,
       g.id             AS grant_id,
       a.attest_model   AS model,
       a.attest_grade   AS grade
FROM   :"schema".ledger_current a
JOIN   :"schema".ledger_current g
       ON  g.kind = 'principal_competence_granted'
       AND g.principal_binding_active
       AND g.principal_competence_activity = 'model-identity-attestation'
       AND g.principal_subject = a.actor
WHERE  a.kind = 'model_identity_attested'
AND    a.attest_verdict = 'mismatch'
AND    a.attest_row_id NOT IN (
         SELECT id FROM :"schema".ledger
         WHERE kind IN ('model_identity_attested', 'principal_competence_granted')
       );

COMMENT ON VIEW :"schema".model_defeated_rows IS
  'design/FABLE-DEFEAT-PIPELINE-SPEC.md §8''s with-cause defeat surface: one row per (defeated
   row, attestation, grant), TYPED (s44) ARM ONLY -- the v1 convention-row arm is deliberately
   unread here (cancer G; the engine floor, engine/ledger_floor.py::defeat_floor_atoms, is the
   authoritative both-arm computation until an s44+ world exists). Display only, never
   enforcement. DEFEAT-INPUT EXCLUSION DOMAIN (kernel/lineage/s50-defeat-input-raw-domain.sql,
   design/FABLE-S46-DEFEAT-INPUT-DOMAIN-SPEC.md, ledger row 1647): the exclusion quantifies over
   RAW HISTORY (every attestation/grant row ever written, including superseded ones), matching
   the engine producers'' own domain exactly -- the s46-era ledger_current-only reading is
   superseded by this delta. kernel/lineage/s46-credited-views.sql (original); this file
   (domain fix).';

GRANT SELECT ON :"schema".model_defeated_rows TO :"role";
