-- s57 OBLIGATION REVOCATION AS A TYPED EVENT (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A --
-- Fable-authored 2026-07-23, maintainer-ratified in the SAME act as Part B/C, ledger row 1150:
-- "Maintainer ratified all three parts of FABLE-LEGACY-LED-RETIREMENT-SPEC in one act, 2026-07-23:
-- A the revocation-as-typed-event kernel delta (the kernel's last destructive operator verb dies
-- at the grant layer, revocations become auditable events) ..."). Sonnet-executed per the standing
-- delegation contract, from this Fable-authored, maintainer-ratified spec.
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the
-- maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11) -- never taken
-- here.
--
-- PREREQUISITE: s43 (kernel/lineage/s43-typed-verdict-write-boundary.sql) -- a HARD dependency:
-- obligation_revoke is the SIXTH SECURITY DEFINER write-boundary function, reuses s43's own
-- write_verdict TYPE and journal_write_refusal FUNCTION unchanged (no new type, no second
-- journaling mechanism -- ADR-0012 P1), and widens s43's own refusal_surface_check CHECK by one
-- member, exactly the s51-artifact-store.sql precedent one delta over. Applying this file on a
-- pre-s43 kernel fails loudly at CREATE OR REPLACE FUNCTION time (no prior write_verdict type, no
-- journal_write_refusal to call) -- the correct, disclosed failure mode for a hard dependency.
--
-- THE CUSTODY GAP THIS DELTA CLOSES (spec Part A, "Today"): `legacy led obligate revoke` performs
-- a raw, privilege-gated DELETE on kernel/lineage/s15-schema.sql's countersign_obligation table.
-- This is the kernel's ONLY remaining destructive operator verb (s43's own CLOSURE STATEMENT
-- named it explicitly: "countersign_obligation DELETE (obligate revoke) -- owner-side escalation
-- path, unchanged, named"): the revocation leaves NO record -- an auditor cannot distinguish
-- "never obligated" from "obligated, then revoked" -- and a raw-DML path is structurally
-- unservable by the boundary service, whose charter (design/FABLE-LEDGER-BOUNDARY-SERVICE-
-- SPEC.md §4) forbids any DML code path. A sweep of legacy-led.tmpl for DML verbs (INSERT/UPDATE/
-- DELETE against a kernel-governed table, not a boundary FUNCTION CALL) at this delta's authoring
-- time found this ONE remaining raw DELETE and no other -- the s43 family's own four functions plus
-- s51's artifact_write already cover every other write surface; this is the last gap.
--
-- MECHANISM:
--   1. A new ledger kind, obligation_revoked (twenty-seventh member, widening s53's twenty-six-
--      member vocabulary) -- an ordinary, supersedable ledger event (NOT given write_refused's
--      R6 unretractability; a revocation is a maintainer act about POLICY, not a record of a
--      refused attempt, and no CLI verb ever exercises superseding one -- see LIMITS). Two new
--      nullable no-DEFAULT columns (the s30/s40 lesson), kind-shape CHECKs split from value
--      CHECKs per the s40 house idiom:
--        obligation_revoked_scope  text -- mandatory (two-way): the countersign_obligation.scope
--                                          this event revokes. NOT a foreign key (the scope may
--                                          legitimately continue to exist in countersign_obligation
--                                          -- revocation does not delete the row it revokes; see
--                                          MECHANISM item 3) -- existence is checked by the write
--                                          function BEFORE the event is written (a payload naming
--                                          an unknown scope is refused, not silently recorded).
--        obligation_revoke_reason text -- mandatory (two-way): the operator's stated ground for
--                                          the revocation -- a revocation is a maintainer act, and
--                                          ADR-0013's "recorded reasoning, not a bare verdict"
--                                          posture applies to it exactly as to a review disposition.
--   2. kernel.obligation_revoke(p_payload jsonb) -- the SIXTH SECURITY DEFINER boundary function,
--      same shape discipline as s43's four and s51's fifth: typed verdict (kernel.write_verdict,
--      reused, no new type), refusal caught and journaled through s43's ONE journaler
--      (kernel.journal_write_refusal), digest-only payload (R4 inherited by construction, exactly
--      s51's own reasoning: journal_write_refusal only ever computes sha256(p_payload::text), so
--      the reason/scope text can never be leaked in expanded form even though the JOURNAL only
--      ever sees a digest of it). Payload keys: scope (required), reason (required, non-empty),
--      actor (optional, the same s40/s43 standing-declaration default every ledger write already
--      falls to via set_actor -- this function does NOT re-derive actor resolution itself, it
--      passes actor through to the ledger INSERT exactly as kernel.ledger_write does, letting the
--      EXISTING set_actor trigger own that one mechanism, ADR-0012 P1). TWO refuse-before-write
--      checks, both loud RAISE EXCEPTIONs (caught and journaled like any other s43-class refusal):
--      (a) the named scope must exist in countersign_obligation (an unknown scope is refused, not
--      silently recorded as a revocation of nothing); (b) the named scope must not ALREADY carry
--      an un-superseded obligation_revoked event (revocation is a ONE-TIME fact about a scope in
--      v1 -- a second revocation event for an already-revoked scope is refused as a duplicate, the
--      same refuse-before-write idiom the legacy CLI's own `led obligate` duplicate-scope check
--      already uses one verb over).
--   3. THE OBLIGATION ROW ITSELF IS NEVER DELETED. Revocation is now expressed ENTIRELY as an
--      additive event; the countersign_obligation row the event names stands, unchanged, forever
--      (an auditor reading that table directly still sees "this obligation was once imposed" --
--      exactly the fact it always recorded -- and now ALSO sees, via the ledger, whether and when
--      it was later revoked and why). "In force" becomes a DERIVATION over events, never a row's
--      mere presence: review_gap (kernel/lineage/s32-edge-views-single-home.sql's latest re-issue,
--      re-verified below) is RE-ISSUED here with a third anti-join -- an un-superseded
--      obligation_revoked event naming the obligation's own scope removes it from the gap view's
--      output, from the revoking event's own moment (the event's mere existence, not a historical
--      backdating -- ledger rows have no "effective as of the past" concept anywhere in this
--      kernel, and this delta introduces none).
--   4. DELETE on countersign_obligation is REVOKEd from :role (belt-and-braces -- s20 never
--      granted it in the first place, matching the legacy CLI's own `has_table_privilege(...,
--      'DELETE')` check, which has always read false for the granted role; this REVOKE is
--      defense in depth against a future grant regression, exactly s43's own Element 7 posture
--      for its four tables, and PUBLIC is REVOKEd too, belt-and-braces) -- the destructive path
--      now dies at the grant layer for every role this kernel has ever granted, not merely by the
--      legacy CLI's own convention of checking before it DELETEs.
--
-- WHAT THIS DELTA DELIBERATELY DOES NOT DO (ADR-0013 Rule 4, filed not buried):
--   - NO reinstatement verb. Revocation is terminal-by-type in v1, exactly s40's principal_revoked
--     posture (no v1 verb lifts it) -- a maintainer who wants the SAME obligation back writes a
--     FRESH `led obligate <scope> ...` (a distinct scope value, since the old scope's PK row still
--     exists unchanged and a second row for the identical scope text would collide on the PK) --
--     named, not silently foreclosed at the type level (a raw supersession of the revocation
--     event, superseding it away, is not specially prevented at the kernel level the way s43's R6
--     prevents superseding a write_refused row -- no CLI verb exercises this, and doing so IS
--     technically a lawful, ordinary supersession under the existing s31 uniform-retraction
--     discipline; this is a disclosed, deliberate non-foreclosure, not an oversight).
--   - NO change to countersign_obligation's own shape, PK, or its pre-existing SELECT/INSERT
--     grants (s20/s43's own postures on it stand unchanged) -- this delta's only touch on that
--     table is the belt-and-braces DELETE revoke (MECHANISM item 4).
--   - NO retro-grading of past ledger PROSE -- a historical `led obligate revoke` performed on an
--     existing world before this delta lands is an absence without record (stated, not repaired,
--     exactly s43's own HISTORY note on write_refused: "history cannot be reconstructed").
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; per row 1150's ratification of the
-- spec's own closure statement, Part A):
--   - INVARIANT: no operator verb destroys kernel history; every obligation-state retraction is
--     an append-only typed event, and "in force" is always a derivation over events, never a raw
--     row's mere presence.
--   - QUANTIFICATION UNIVERSE (the spec's own, restated and checked against this delta's actual
--     text, per the succession-rule closure-check discipline): the obligation table's DELETE was
--     the LAST destructive operator path -- enumerated by sweeping legacy-led.tmpl for DML verbs
--     (the phase-1 sweep found none other) and the kernel's grants for operator-role DELETE/UPDATE
--     privileges (s43 Element 7 already revoked INSERT on every kernel-governed table for :role;
--     no table anywhere in this kernel has ever granted :role a DELETE or UPDATE except the
--     countersign_obligation gap this delta closes). Named as NOT covered: administrative acts
--     outside the operator surface (schema teardown, migration repair) -- deliberately not
--     operator verbs, exactly s43's own standing trust bound.
--     OBLIGATION-CONSUMING VIEWS, disposed one by one (the spec's own phrase, "review_gap and the
--     countersign_obligation family" -- this delta's own re-verification, per the s56 §7
--     precedent's "re-verified against its CURRENT (latest re-issued) definition" discipline,
--     `grep -l countersign_obligation kernel/lineage/*.sql` cross-checked against every CREATE OR
--     REPLACE VIEW in the tree): review_gap is the ONLY view anywhere in this kernel that joins
--     countersign_obligation directly (latest prior re-issue: s32-edge-views-single-home.sql,
--     Element 3a) -- RE-ISSUED here with the revocation anti-join (ELEMENT 2 below).
--     countersigned_in_force does NOT read countersign_obligation at all (it composes with
--     discharging_attest, an unrelated review-verdict concern) -- correctly untouched.
--     work_review_gap/work_item_strict_blockers/question_status likewise do not read
--     countersign_obligation -- correctly untouched, re-verified, named rather than assumed.
--   - ENGINE: engine/review_gap_edb.py (the ASP EDB producer) and engine/review_gap_floor.py (the
--     independent SQL floor) BOTH read countersign_obligation directly to derive `obliged/1` --
--     both encode in-force obligation semantics and are extended in this SAME commit (per the
--     s56 §7 precedent: "if any engine mirror encodes in-force obligation semantics, extend it ...
--     and witness the differential in AGREE") to exclude a scope carrying an un-superseded
--     obligation_revoked event, mirroring review_gap's own new anti-join exactly. No other engine
--     module reads countersign_obligation or obliges_actor (checked-and-absent, not assumed --
--     `grep -rl countersign_obligation engine/` was run at this delta's authoring time and named
--     every hit; the two floor/edb producers above are the whole set beside display-only
--     re-exports of their own output, e.g. engine/review_gap_audit.py, which consume the
--     producers' facts and need no independent obligation-table read of their own).
--     ./judge's SQL/ASP differential over the review-gap-audit layer is witnessed AGREE on this
--     delta's own fixture (both a revoked and an un-revoked obligation, both polarities).
--   - DENOMINATION: revocation is a boolean derived fact (an un-superseded obligation_revoked
--     event exists for a scope, or it does not) -- no numeric bound anywhere in this delta.
--
-- HISTORY: safe -- per-mechanism grounds, mirroring s43's/s51's own HISTORY paragraphs exactly:
--   * obligation_revoked is a WHOLLY NEW kind -- no pre-existing row of this kind exists on any
--     world, so its two mandatory-on-this-kind CHECKs validate vacuously everywhere else.
--   * kernel.obligation_revoke is a WHOLLY NEW FUNCTION -- no pre-existing caller.
--   * refusal_surface_check widens by ONE member ('obligation_revoke') -- additive, and every
--     pre-existing write_refused row's refusal_surface value remains valid unchanged (s43's own
--     kind/vocabulary-widening precedent, restated a third time after s51).
--   * review_gap is RE-ISSUED with an ADDITIONAL anti-join clause that can only NARROW its output
--     (a row that was in the gap view before this delta and whose obligation carries NO revocation
--     event is unaffected -- the new NOT EXISTS is vacuously true for it); a row can only newly
--     LEAVE the view (an obligation now shown revoked), never newly APPEAR. Protective-only,
--     exactly the s50 defeat-input-domain precedent's own HISTORY reasoning restated for this
--     view.
--   * countersign_obligation gains ONE belt-and-braces REVOKE (DELETE, already ungranted) --
--     nothing that succeeded before succeeds differently after (no pre-s57 world's :role has ever
--     held countersign_obligation DELETE to lose).
--   * compute_row_hash re-issued to 77 columns (the two new columns appended in catalog ordinal
--     order) under s42's own law, gate-witnessed (gates/hash_coverage_gate.py, mechanically
--     derived -- no manual column-count manifest to update).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED FAIL-SAFE,
-- stated plainly: this delta adds a WRITE PATH (a sixth SECURITY DEFINER function) and RE-ISSUES
-- an existing view's semantics (review_gap narrows, never widens, but a semantics change is a
-- semantics change) -- it does not qualify for the 2026-07-09 class-ratified-fail-safe track even
-- though its DIRECTION is fail-safe throughout (append-only event, narrowing-only view re-issue,
-- closed refusal vocabulary, a destructive path additionally foreclosed at the grant layer). It
-- ships under design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md's own maintainer ratification (ledger
-- row 1150, 2026-07-23) -- the s36/s37/s44/s51/s53/s56 precedent of routing a non-fail-safe,
-- ratified-by-name kernel delta through its own spec rather than self-certifying.
--
-- LIMITS (pre-registered):
--   - No v1 reinstatement verb (MECHANISM's own "WHAT THIS DELTA DELIBERATELY DOES NOT DO" above)
--     -- terminal-by-type, matching s40's principal_revoked posture exactly.
--   - A raw supersession of an obligation_revoked event is NOT specially foreclosed at the kernel
--     level (unlike s43's R6 for write_refused) -- no CLI verb exercises this; a disclosed,
--     deliberate non-foreclosure, named so a future reviewer does not assume symmetry with R6
--     that was never built.
--   - The owner/superuser direct-DML trust bound stands (s26..s56's own standing bound) -- an
--     owner connecting directly could still DELETE a countersign_obligation row (or an
--     obligation_revoked ledger row) bypassing this delta's grant-layer foreclosure entirely; this
--     delta closes the GRANTED-ROLE path only, exactly s43's own named scope.
--   - engine/review_gap_edb.py's/review_gap_floor.py's own extension reads
--     countersign_obligation's scope and the new obligation_revoked_scope/kind columns via THEIR
--     OWN independently-authored SQL, never by importing review_gap's kernel view definition or
--     each other's logic (I6/ADR-0000 INDEP, restated) -- an independent-authorship error in
--     either extension would still show as a differential DISAGREE, not a silent false AGREE.
--   - registered_by/actor resolution for obligation_revoke rides the SAME s40/s43
--     session_user-based standing-declaration default as the generic ledger_write path (no
--     independent actor-resolution logic of this function's own) -- s43 Element 8's own named
--     limit (one principal per login role via SET ROLE) applies identically here.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s43/../s56):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s57val -v kern=s57val_kernel -v role=s57val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        ... (s21..s56 as in s56's own VALIDATE list) ... \
--        -f s56-reservation-residue.sql -f s57-obligation-revocation-event.sql
--     (genesis seed per s26; register the write-boundary principal, and at least one standing
--     actor principal plus at least one countersign_obligation row, before exercising any
--     obligation_revoke path -- the write boundary's journaler aborts loudly by design otherwise,
--     exactly s43's own VALIDATE note.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's birth
--   chain via bootstrap/new-project.sh's LINEAGE_CHAIN, ONLY as the maintainer's own act
--   (runs-are-strictly-linear, 2026-07-11) -- NOT wired by this commit (the s56 precedent: s56 is
--   authored and scratch-witnessed only, not yet wired into new-project.sh's own LINEAGE_CHAIN at
--   this delta's own authoring time either). Authored and scratch-witnessed on scratch schema
--   pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP+ADD CONSTRAINT;
-- CREATE OR REPLACE FUNCTION/VIEW; REVOKE/GRANT are idempotent).
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
-- ELEMENT 1 -- KIND VOCABULARY WIDENED (twenty-seventh member) + THE TWO REVOCATION COLUMNS.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS ledger_kind_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT ledger_kind_check CHECK (kind IN
    ('assumption','decision','question','verification',
     'finding','snag','revision','note','review',
     'work_opened','work_claimed','work_depends_on','work_closed',
     'commission','work_violation_disposition',
     'principal_registered','principal_suspended','principal_revoked',
     'principal_standing_declared',
     'principal_relation_asserted','principal_role_bound','principal_key_bound',
     'principal_competence_granted',
     'write_refused',
     'model_identity_attested',
     'belief',
     'obligation_revoked'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s57-obligation-revocation-event.sql: widens s53''s twenty-six-member vocabulary
   by obligation_revoked -- the typed event that replaces the raw countersign_obligation DELETE
   (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A, ledger row 1150). An ORDINARY supersedable
   kind (unlike write_refused''s R6 unretractability -- see this delta''s own LIMITS for why no
   symmetry is claimed). Minted only by kernel.obligation_revoke.';

ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS obligation_revoked_scope text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS obligation_revoke_reason text;

COMMENT ON COLUMN :"schema".ledger.obligation_revoked_scope IS
  'The countersign_obligation.scope this event revokes (NOT a foreign key -- the named
   obligation row is never deleted, so its own existence is checked by kernel.obligation_revoke
   BEFORE the event is written, not enforced by a standing FK). Mandatory on obligation_revoked,
   forbidden elsewhere. kernel/lineage/s57-obligation-revocation-event.sql.';
COMMENT ON COLUMN :"schema".ledger.obligation_revoke_reason IS
  'The operator''s stated ground for the revocation, verbatim -- a revocation is a maintainer act,
   and its reasoning is part of the record (ADR-0013). Mandatory non-empty on obligation_revoked,
   forbidden elsewhere. kernel/lineage/s57-obligation-revocation-event.sql.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS obligation_revoked_scope_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT obligation_revoked_scope_kind_shape CHECK (
    (kind = 'obligation_revoked') = (obligation_revoked_scope IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS obligation_revoke_reason_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT obligation_revoke_reason_kind_shape CHECK (
    (kind = 'obligation_revoked') = (obligation_revoke_reason IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS obligation_revoked_scope_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT obligation_revoked_scope_nonempty CHECK (
    obligation_revoked_scope IS NULL OR btrim(obligation_revoked_scope) <> '');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS obligation_revoke_reason_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT obligation_revoke_reason_nonempty CHECK (
    obligation_revoke_reason IS NULL OR btrim(obligation_revoke_reason) <> '');

-- ============================================================================================
-- ELEMENT 2 -- review_gap RE-ISSUED (latest prior re-issue: s32-edge-views-single-home.sql
-- Element 3a): a THIRD anti-join, narrowing-only -- a row whose obligation carries no revocation
-- event is unaffected (the clause is vacuously true); an obligation now revoked leaves the view.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".review_gap
    WITH (security_invoker = true) AS
SELECT l.id, l.actor, o.scope, o.assigned_by
FROM   :"schema".ledger l JOIN :"schema".countersign_obligation o ON o.obliges_actor = l.actor
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    NOT EXISTS (SELECT 1 FROM :"schema".discharging_attest da
                    WHERE da.regards_id = l.id AND da.reviewer <> l.actor)
AND    NOT EXISTS (SELECT 1 FROM :"schema".ledger rv
                    WHERE rv.kind = 'obligation_revoked' AND rv.obligation_revoked_scope = o.scope
                      AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = rv.id));

COMMENT ON VIEW :"schema".review_gap IS
  'kernel/lineage/s32-edge-views-single-home.sql''s single home for this view, RE-ISSUED here
   (kernel/lineage/s57-obligation-revocation-event.sql) with a third, narrowing-only anti-join: an
   obligation whose scope carries an un-superseded obligation_revoked event is treated as
   not-in-force -- "in force" is a derivation over events, never countersign_obligation''s own
   row presence (that row is never deleted by kernel.obligation_revoke; see this delta''s own
   header MECHANISM item 3).';

-- ============================================================================================
-- ELEMENT 3 -- countersign_obligation: DELETE REVOKEd (belt-and-braces -- s20 never granted it;
-- this closes the grant layer for defense in depth, exactly s43''s own Element 7 posture).
-- ============================================================================================
REVOKE DELETE ON :"schema".countersign_obligation FROM :"role";
REVOKE DELETE ON :"schema".countersign_obligation FROM PUBLIC;

-- ============================================================================================
-- ELEMENT 4a -- s42'S LAW SELF-APPLIED: compute_row_hash re-issued to 77 columns (the two new
-- columns appended in catalog ordinal order, before the predecessor link; every other rendering
-- byte-identical to s53's).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".compute_row_hash(r :"schema".ledger, predecessor_hash text)
    RETURNS text LANGUAGE sql IMMUTABLE
    SET search_path = :"schema", pg_temp AS $fn$
  SELECT encode(sha256(convert_to(
    array_to_string(ARRAY[
      hashfield(r.id::text),
      hashfield(extract(epoch FROM r.ts)::text),
      hashfield(r.session),
      hashfield(r.kind),
      hashfield(r.statement),
      hashfield(r.rationale),
      hashfield(r.status),
      hashfield(r.evidence),
      hashfield(r.confidence),
      hashfield(r.supersedes::text),
      hashfield(r.refs),
      hashfield(r.concern),
      hashfield(array_to_string(r.enacts, ',')),
      hashfield(r.actor::text),
      hashfield(r.regards::text),
      hashfield(r.amends::text),
      hashfield(r.amends_scope),
      hashfield(r.answers::text),
      hashfield(r.stamp_session),
      hashfield(r.stamp_agent),
      hashfield(r.stamp_ts::text),
      hashfield(r.stamp_hmac),
      hashfield(r.stamp_verified::text),
      hashfield(r.work_slug),
      hashfield(r.work_title),
      hashfield(r.work_depends_on),
      hashfield(r.work_resolution),
      hashfield(r.work_witness),
      hashfield(r.stamp_invocation),
      hashfield(extract(epoch FROM r.event_declared_ts)::text),
      hashfield(r.work_parent),
      hashfield(r.work_review_disposition),
      hashfield(r.work_review_ref),
      hashfield(r.work_strict_close::text),
      hashfield(r.edge_type),
      hashfield(r.work_discharge),
      hashfield(r.decision_grade),
      hashfield(r.work_violation_class),
      hashfield(r.work_violation_target_id::text),
      hashfield(r.work_violation_witness::text),
      hashfield(r.principal_subject::text),
      hashfield(r.principal_purpose),
      hashfield(r.principal_db_role),
      hashfield(r.principal_actor_resolution),
      hashfield(r.principal_binding_active::text),
      hashfield(r.principal_object::text),
      hashfield(r.principal_relation),
      hashfield(r.principal_role_name),
      hashfield(r.principal_key_fingerprint),
      hashfield(r.principal_competence_activity),
      hashfield(r.principal_competence_band),
      hashfield(r.principal_competence_basis),
      hashfield(r.refusal_sqlstate),
      hashfield(r.refusal_message),
      hashfield(r.refusal_surface),
      hashfield(r.refusal_payload_digest),
      hashfield(r.refusal_attempted_actor::text),
      hashfield(r.refusal_attempted_role),
      hashfield(r.attest_row_id::text),
      hashfield(r.attest_model),
      hashfield(r.attest_grade),
      hashfield(r.attest_verdict),
      hashfield(r.attest_expected),
      hashfield(r.attest_session),
      hashfield(r.attest_basis),
      hashfield(r.belief_polarity),
      hashfield(r.belief_basis),
      hashfield(r.belief_universe),
      hashfield(r.belief_witness),
      hashfield(r.belief_source::text),
      hashfield(array_to_string(r.belief_premises, ',')),
      hashfield(r.belief_subject::text),
      hashfield(r.belief_contests::text),
      hashfield(r.belief_concurs::text),
      -- s57: the two obligation-revocation columns (catalog ordinals 76..77)
      hashfield(r.obligation_revoked_scope),
      hashfield(r.obligation_revoke_reason),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 4b -- the two column-complete views, +2 appended (the s20 lesson).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close, l.edge_type,
       l.work_discharge, l.decision_grade,
       l.work_violation_class, l.work_violation_target_id, l.work_violation_witness,
       l.principal_subject, l.principal_purpose, l.principal_db_role,
       l.principal_actor_resolution,
       l.principal_binding_active, l.principal_object, l.principal_relation,
       l.principal_role_name, l.principal_key_fingerprint,
       l.principal_competence_activity, l.principal_competence_band,
       l.principal_competence_basis,
       l.refusal_sqlstate, l.refusal_message, l.refusal_surface,
       l.refusal_payload_digest, l.refusal_attempted_actor, l.refusal_attempted_role,
       l.attest_row_id, l.attest_model, l.attest_grade, l.attest_verdict, l.attest_expected,
       l.attest_session, l.attest_basis,
       l.belief_polarity, l.belief_basis, l.belief_universe, l.belief_witness, l.belief_source,
       l.belief_premises, l.belief_subject, l.belief_contests, l.belief_concurs,
       l.obligation_revoked_scope, l.obligation_revoke_reason
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close, l.edge_type,
       l.work_discharge, l.decision_grade,
       l.work_violation_class, l.work_violation_target_id, l.work_violation_witness,
       l.principal_subject, l.principal_purpose, l.principal_db_role,
       l.principal_actor_resolution,
       l.principal_binding_active, l.principal_object, l.principal_relation,
       l.principal_role_name, l.principal_key_fingerprint,
       l.principal_competence_activity, l.principal_competence_band,
       l.principal_competence_basis,
       l.refusal_sqlstate, l.refusal_message, l.refusal_surface,
       l.refusal_payload_digest, l.refusal_attempted_actor, l.refusal_attempted_role,
       l.attest_row_id, l.attest_model, l.attest_grade, l.attest_verdict, l.attest_expected,
       l.attest_session, l.attest_basis,
       l.belief_polarity, l.belief_basis, l.belief_universe, l.belief_witness, l.belief_source,
       l.belief_premises, l.belief_subject, l.belief_contests, l.belief_concurs,
       l.obligation_revoked_scope, l.obligation_revoke_reason
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 5 -- refusal_surface_check WIDENED by one member ('obligation_revoke'), the SAME
-- pattern s51's own widening uses.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_surface_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_surface_check CHECK (
    refusal_surface IS NULL
    OR refusal_surface IN ('ledger', 'review', 'registration', 'obligation', 'artifact',
                            'obligation_revoke'));

COMMENT ON CONSTRAINT refusal_surface_check ON :"schema".ledger IS
  'kernel/lineage/s57-obligation-revocation-event.sql widens s51''s five-member closed vocabulary
   by ''obligation_revoke'' -- the sixth SECURITY DEFINER boundary function''s own surface name,
   journaled by the SAME kernel.journal_write_refusal every other surface already uses. Pure
   value-vocabulary addition: every pre-s57 write_refused row''s refusal_surface value remains
   valid unchanged.';

-- ============================================================================================
-- ELEMENT 6 -- kernel.obligation_revoke(jsonb): the SIXTH SECURITY DEFINER boundary function.
-- Reuses kernel.write_verdict (s43's TYPE, unchanged) and kernel.journal_write_refusal (s43's ONE
-- journaler, unchanged) -- no new type, no second journaling mechanism.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".obligation_revoke(p_payload jsonb)
    RETURNS :"kern".write_verdict LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  k text;
  v_scope text;
  v_reason text;
  v_id bigint;
  v_state text; v_msg text; v_refusal bigint;
BEGIN
  BEGIN
    FOR k IN SELECT jsonb_object_keys(p_payload) LOOP
      IF k NOT IN ('scope', 'reason', 'actor') THEN
        RAISE EXCEPTION 'write boundary: obligation-revocation payload key ''%'' is not a member of the revocation ceremony''s contract (scope, reason, actor -- kernel/lineage/s57-obligation-revocation-event.sql).', k;
      END IF;
    END LOOP;
    IF NOT (p_payload ? 'scope') OR btrim(p_payload->>'scope') = '' THEN
      RAISE EXCEPTION 'write boundary: obligation-revocation payload is missing a non-empty ''scope'' (kernel/lineage/s57-obligation-revocation-event.sql).';
    END IF;
    v_scope := p_payload->>'scope';
    IF NOT (p_payload ? 'reason') OR btrim(p_payload->>'reason') = '' THEN
      RAISE EXCEPTION 'write boundary: obligation-revocation payload is missing a non-empty ''reason'' -- a revocation is a maintainer act, and its stated ground is part of the record (kernel/lineage/s57-obligation-revocation-event.sql).';
    END IF;
    v_reason := p_payload->>'reason';
    IF NOT EXISTS (SELECT 1 FROM countersign_obligation WHERE scope = v_scope) THEN
      RAISE EXCEPTION 'write boundary: obligation-revocation names scope ''%'' -- no countersign_obligation row exists with that scope (kernel/lineage/s57-obligation-revocation-event.sql). Nothing was recorded.', v_scope;
    END IF;
    IF EXISTS (
      SELECT 1 FROM ledger e
      WHERE e.kind = 'obligation_revoked' AND e.obligation_revoked_scope = v_scope
        AND NOT EXISTS (SELECT 1 FROM ledger s2 WHERE s2.supersedes = e.id)
    ) THEN
      RAISE EXCEPTION 'write boundary: obligation-revocation names scope ''%'' -- ALREADY revoked (an earlier obligation_revoked event for this scope stands, un-superseded); revocation is a one-time fact about a scope in v1, and a second event would be a duplicate, not a new fact (kernel/lineage/s57-obligation-revocation-event.sql). Nothing was recorded.', v_scope;
    END IF;
    INSERT INTO ledger (kind, statement, actor, obligation_revoked_scope, obligation_revoke_reason)
    VALUES ('obligation_revoked',
            format('obligation revoked: scope %s (%s)', v_scope, v_reason),
            CASE WHEN p_payload ? 'actor' THEN (p_payload->>'actor')::bigint ELSE NULL END,
            v_scope, v_reason)
    RETURNING id INTO v_id;
    SET CONSTRAINTS ALL IMMEDIATE;
    RETURN ('accepted', v_id, NULL, NULL, NULL)::write_verdict;
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS v_state = RETURNED_SQLSTATE, v_msg = MESSAGE_TEXT;
    IF v_state LIKE '22%' OR v_state LIKE '23%' OR v_state LIKE 'P0%' THEN
      v_refusal := journal_write_refusal('obligation_revoke', p_payload, v_state, v_msg);
      RETURN ('refused', NULL, v_refusal, v_state, v_msg)::write_verdict;
    END IF;
    RAISE;   -- infrastructure classes (40/53/57/XX/...): not a denied attempt -- re-raised.
  END;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".obligation_revoke(jsonb) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".obligation_revoke(jsonb) TO :"role";

COMMENT ON FUNCTION :"kern".obligation_revoke(jsonb) IS
  'The SIXTH SECURITY DEFINER write boundary (design/FABLE-LEGACY-LED-RETIREMENT-SPEC.md Part A),
   beside s43''s four and s51''s fifth: payload keys scope (required), reason (required,
   non-empty), actor (optional, the same set_actor standing-declaration default every ledger
   write already falls to). Refuses an unknown scope and a duplicate revocation of an
   already-revoked scope, both loud, journaled refusals. On accept, writes an obligation_revoked
   ledger event -- the countersign_obligation row itself is NEVER deleted; "in force" becomes a
   derivation over events (review_gap''s own re-issue, this same delta). Replaces the raw,
   privilege-gated DELETE `legacy led obligate revoke` used to issue.
   kernel/lineage/s57-obligation-revocation-event.sql.';
