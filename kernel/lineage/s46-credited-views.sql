-- s46 CREDITED VIEWS (design/FABLE-DEFEAT-PIPELINE-SPEC.md §8, the RATIFIED BUILD BASIS's own
-- "credited read surface" -- the envelope's serving option (c)). Working-name history, per that
-- spec's own dated amendment A2: the delta was first drafted under the name "s45" and collided
-- with the shipped kernel/lineage/s45-standing-lifecycle.sql (both authored the same night with
-- no shared delta-number registry -- A2's own process note); the spec's A2 text renumbers the
-- working name to "s46-credited-views.sql", and this builder takes that as the next free
-- number at build time (confirmed by directory listing before authoring: s44 is this same
-- commission's sibling delta, landing immediately before this file in the birth chain; s45 is
-- already taken; s46 is free). VIEW-ONLY, ZERO NEW LEDGER COLUMNS, ZERO NEW KINDS -- therefore
-- compute_row_hash is UNTOUCHED and gates/hash_coverage_gate.py stays green trivially (stated
-- here per the spec's own explicit instruction, "the builder states this in the delta header
-- rather than leaving it inferred," §8). Writes are unaffected -- the s43 boundary continues to
-- own them; this delta touches no INSERT path whatsoever.
--
-- Sonnet-built (the standing build split: Fable authors kernel/law specs, Sonnet executes them
-- -- CLAUDE.md ORCHESTRATION; this spec's own §15 item 5 commissions exactly this file). This
-- delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the
-- maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11) -- never
-- taken here.
--
-- PREREQUISITE: s44 (kernel/lineage/s44-model-identity-attestation.sql), and transitively
-- s43/s42/s41/s40 -- a HARD dependency (spec §8's own first bullet): "the kernel views read the
-- TYPED attestation columns only -- a kernel view parsing the v1 statement convention would be
-- load-bearing knowledge in an unenforceable convention inside the kernel (cancer G), refused
-- here explicitly." THE HEAD-BODY RULE: at this delta's authoring the lineage head is
-- s44-model-identity-attestation.sql (this same commission's sibling, landing immediately
-- before this file) -- ledger_current's column list this file reads FROM is s44's own
-- (66 columns, the s43 head's 59 + s44's seven attest_* columns), verified against that file's
-- own text, not assumed. This file does NOT re-issue ledger_current or countersigned_in_force
-- (it has no columns of its own to append -- the s20 lesson does not apply to a zero-column
-- delta); it only READS ledger_current as already re-issued by s44.
--
-- WHY (operator-side prose; NOT subject-visible): the spec's own §8 framing, transcribed: an
-- ordinary SQL view, read the way ledger_current already is, that shows "what currently stands"
-- MINUS whatever a model-identity mismatch attestation, backed by an in-force competence grant,
-- has defeated -- computed fresh on every read from typed, structural facts, nothing stored,
-- nothing edited, no write ever gated, the underlying row never touched. The class this closes:
-- *a derived "current" reading whose defeat status a display client would otherwise have to
-- re-derive itself* (the spec's own §9.3 "no client-side defeat logic" rule) -- one home for the
-- judgment, here, rather than a second computation living in every future SPA/panel consumer.
--
-- ELEMENT 1 -- `model_defeated_rows` (spec §8's own fixed shape): security_invoker, GRANT SELECT
-- TO :role. Columns: row_id, attest_id, grant_id, model, grade -- the "with-cause" surface (the
-- spec's own §9.2 auditability-wall rule: "a defeated row is always displayed WITH its cause").
-- Both legs factor through ledger_current (never raw ledger -- the s31 reader discipline; TYPED
-- ARM ONLY, per this delta's own PREREQUISITE note): the attestation leg is
-- kind='model_identity_attested' AND attest_verdict='mismatch'; the grant leg is
-- kind='principal_competence_granted' AND principal_binding_active (the I1 two-conjunct's SQL
-- side, design/FABLE-DEFEAT-PIPELINE-SPEC.md §4.2's own note transposed to this view) AND
-- principal_competence_activity = 'model-identity-attestation' (the ONE fixed activity literal,
-- spec §5.2), joined on the grant's principal_subject = the attestation row's own actor (the
-- attesting principal). THE DEFEAT-INPUT EXCLUSION MIRRORED (spec §10 law 2, "the machinery's
-- input kinds are outside its target domain"): the attested row (attest_row_id) is excluded as
-- a target when it is ITSELF a currently-in-force attestation or grant row. NAMED CHOICE (spec-
-- silent, flagged per this build's own reporting duty): the two independent engine producers
-- (engine/lp/ledger_defeat.lp's `defeat_input/1`, engine/ledger_floor.py's `attest_any`/
-- `grant_any` CTEs) test defeat-input membership over EVERY attestation/grant row EVER WRITTEN
-- (the full raw history, including superseded ones -- ledger_edb.py's attest_row/grant_row
-- families are NOT ledger_current-filtered), while this kernel view -- confined by its own
-- PREREQUISITE note to ledger_current-only reads (never a raw `ledger` leg, the s31 discipline)
-- -- tests membership over CURRENTLY-IN-FORCE attestation/grant rows only. The two readings can
-- diverge only in the vanishingly narrow case of a target row that WAS once an attestation or
-- grant row and has SINCE been fully superseded to a non-attestation/non-grant kind (i.e. a kind
-- CHANGE across a supersession chain -- itself unusual, since every existing supersession idiom
-- in this kernel is same-kind-restating); named here as the smallest-honest choice available
-- inside the "typed columns only, ledger_current only" mandate, not silently absorbed. The
-- engine differential (`./judge --layer defeat`) remains the AUTHORITATIVE computation (spec §7:
-- "agreement is the authority"); this view is the DISPLAY surface, and the spec's own §8 names
-- the engine floor as the interim credited computation until an s44+ world exists -- this view
-- is UNEXERCISED live for the same reason, scratch-witnessed only (§12 W12).
--
-- ELEMENT 2 -- `credited_current` (spec §8's own fixed shape): security_invoker, GRANT SELECT TO
-- :role. `ledger_current` MINUS every row whose id appears in `model_defeated_rows.row_id` --
-- column list IDENTICAL to `ledger_current`'s (the s20 lesson, transposed: any LATER column
-- addition to ledger_current binds this view to re-issue in the SAME delta that adds it, exactly
-- as the s20 obligation already binds `countersigned_in_force`).
--
-- WHAT THIS DELTA DOES NOT TOUCH, stated as loudly as what it does: ZERO new ledger columns
-- (compute_row_hash untouched -- witnessed green on this head with NO re-issue, and its own
-- --inject-column negative control still red, mirroring s45's own "zero columns" witness);
-- ZERO new kinds (no kind_shape_manifest_gate.py MANIFEST edit -- its CHAIN gains this file
-- purely to exercise these two views under the scratch apply, no new/widened CHECK exists for
-- it to classify); ZERO triggers; ZERO writes (this file contains no INSERT/UPDATE/DELETE of any
-- kind -- a pure CREATE OR REPLACE VIEW pair); ZERO edits to s44's own objects (ledger_current,
-- countersigned_in_force, compute_row_hash, model_attestations, the kind CHECK -- all read
-- as-is).
--
-- HISTORY: safe -- both objects are NEW (no pre-existing reader of either view name); reading
-- ledger_current is the standing s31-discipline read every prior view in this lineage already
-- performs; no existing object's behavior changes.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's own slice -- the FAMILY
-- closure is design/FABLE-DEFEAT-PIPELINE-SPEC.md §11, checked there in full):
--   - INVARIANT: in an s44+world carrying this delta, `credited_current` shows exactly the rows
--     `ledger_current` shows minus those a currently-in-force typed mismatch attestation, backed
--     by a currently-in-force typed competence grant for `model-identity-attestation`, has
--     defeated (this view's own defeat-input-exclusion caveat named above); `model_defeated_rows`
--     names, for every such exclusion, the attesting row, the empowering grant, the observed
--     model, and its confidence grade -- so a defeated row's cause is always reconstructable from
--     this surface alone, never hidden.
--   - QUANTIFICATION UNIVERSE: attestation sources -- TYPED (s44) ARM ONLY, the v1 convention-row
--     arm is DELIBERATELY EXCLUDED from this kernel surface (cancer G, named above) and remains
--     the engine floor's own concern; verdicts -- mismatch defeats, match/unevaluated never
--     appear in `model_defeated_rows`; grant states -- active only (withdrawn/superseded grants
--     confer no defeat force here, matching the engine's own I1 two-conjunct); targets -- every
--     row EXCEPT a currently-in-force attestation or grant row (the named divergence from the
--     engine's full-history exclusion, above); worlds -- s44+ only (undefined, name-collision-
--     proof by PREREQUISITE, on any earlier world -- this file simply cannot apply without s44's
--     columns existing).
--   - DENOMINATION: every compared value is an immutable ledger row id, a verbatim model string,
--     or a closed-vocabulary grade/verdict atom -- no text convention crosses (contrast the v1
--     arm, which this view refuses to read at all).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- CANDIDATE in shape (view-only, zero columns, zero kinds, strictly additive, nothing existing
-- relaxed) but NOT claimed as such here -- it ships under design/FABLE-DEFEAT-PIPELINE-SPEC.md's
-- own RATIFIED BUILD BASIS status (maintainer batch ratification ledger row 1481) plus this
-- build's own commission, the more conservative and already-available routing.
--
-- LIMITS (pre-registered, per the spec §14/§16 transposed to this delta's own slice):
--   - The defeat-input exclusion divergence named in ELEMENT 1 (ledger_current-only vs the
--     engine's full-history test) -- a spec-silent choice, smallest honest available inside the
--     "typed columns only" mandate, flagged for the maintainer's own future call.
--   - This view NEVER reads the v1 statement-convention rows -- a world running v1-only
--     attestations (any world before an operator's `./otel-attest` writer gains typed-row
--     support, itself UNBUILT per s44's own LIMITS) shows NO defeats here at all, even though
--     the engine floor (which DOES read both arms) may show some -- named, not silently
--     inconsistent: the spec's own §9 display contract binds a CONSUMER to read one computation
--     consistently, and names the engine floor as authoritative until this view's world exists.
--   - Live operation awaits an s44+ world (RD-2, evidence-triggered) -- UNEXERCISED live, said so
--     in this build's own report, scratch-witnessed only (§12 W12).
--   - Everything in the sentry spec's own §7 (R1-R7) applies transitively to every attestation
--     this view can ever read -- this delta only computes CONSEQUENCES of trusting an
--     attestation at its granted scope, never its truth.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s45):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s46val -v kern=s46val_kernel -v role=s46val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        ... (s21..s43, s45 as in s45's own VALIDATE list) ... \
--        -f s45-standing-lifecycle.sql -f s44-model-identity-attestation.sql \
--        -f s46-credited-views.sql
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in this SAME commit, at the
--   SAME evidence-triggered sequencing point as s44 (RD-2). Authored and scratch-witnessed on
--   scratch schema pairs in the TOY db only.
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
-- ELEMENT 1 -- model_defeated_rows: the with-cause surface (spec §8's own fixed shape).
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
         SELECT id FROM :"schema".ledger_current
         WHERE kind IN ('model_identity_attested', 'principal_competence_granted')
       );

COMMENT ON VIEW :"schema".model_defeated_rows IS
  'design/FABLE-DEFEAT-PIPELINE-SPEC.md §8''s with-cause defeat surface: one row per (defeated
   row, attestation, grant), TYPED (s44) ARM ONLY -- the v1 convention-row arm is deliberately
   unread here (cancer G; the engine floor, engine/ledger_floor.py::defeat_floor_atoms, is the
   authoritative both-arm computation until an s44+ world exists). Display only, never
   enforcement. kernel/lineage/s46-credited-views.sql.';

GRANT SELECT ON :"schema".model_defeated_rows TO :"role";

-- ============================================================================================
-- ELEMENT 2 -- credited_current: ledger_current minus every model_defeated_rows.row_id (spec
-- §8's own fixed shape). Column list IDENTICAL to ledger_current's (the s20 lesson).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".credited_current
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
       l.attest_session, l.attest_basis
FROM   :"schema".ledger_current l
WHERE  l.id NOT IN (SELECT row_id FROM :"schema".model_defeated_rows);

COMMENT ON VIEW :"schema".credited_current IS
  'design/FABLE-DEFEAT-PIPELINE-SPEC.md §8''s credited read surface: ledger_current minus every
   row model_defeated_rows names -- column list identical to ledger_current''s (the s20 lesson:
   a later column addition to ledger_current re-issues BOTH views in the same delta). The SPA
   display contract (spec §9) binds any consumer: default view = credited-only; defeated history
   stays reachable in an explicit history mode, always with cause; no client-side re-derivation.
   kernel/lineage/s46-credited-views.sql.';

GRANT SELECT ON :"schema".credited_current TO :"role";
