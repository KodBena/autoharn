-- s44 MODEL-IDENTITY ATTESTATION (design/FABLE-OTEL-SENTRY-SPEC.md §8, the RATIFIED-per-
-- commission typed delta, working name "s44-model-identity-attestation" fixed by the spec's own
-- §8 heading and §17 executor guidance item 7; authored pre-freeze at the maintainer's word
-- ("no reason to do less than what is appropriate", the revision response quoted in that
-- spec's header) under the succession/authoring discipline CLAUDE.md's ORCHESTRATION section
-- fixes for Fable-authored kernel deltas). Sonnet-built (the standing build split: Fable
-- authors kernel/law specs, Sonnet executes them -- CLAUDE.md ORCHESTRATION, and this spec's
-- own §17 addresses "a non-Fable builder" throughout). This delta is AUTHORED and
-- SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the maintainer's act at a
-- FUTURE world's birth (runs-are-strictly-linear, 2026-07-11) -- never taken here.
--
-- PREREQUISITE: the spec's own §8.1 fixes s43 (and transitively s42/s41/s40) as the HARD
-- dependency -- this delta re-issues s43's compute_row_hash, s43's widened ledger_kind_check,
-- and s43's ledger_current/countersigned_in_force bodies. THE HEAD-BODY RULE (the same
-- discipline s45's own header names as "the builder's own most important standing
-- instruction"): at this delta's authoring the actual repository lineage head is s45
-- (kernel/lineage/s45-standing-lifecycle.sql, already in bootstrap/new-project.sh's
-- LINEAGE_CHAIN, applied AFTER s43) -- so this file lands ON TOP of s45 in the real chain, not
-- directly on s43. Checked before authoring (per the s45 head-body rule's own STOP-and-surface
-- duty): does this delta re-issue anything s45 also touched? NO -- s45's own header states
-- plainly "No ledger_current/countersigned_in_force re-issue" and it never touches
-- compute_row_hash or ledger_kind_check (its ONE re-issued CHECK is
-- principal_binding_active_kind_shape, a column this delta does not touch, and its other three
-- re-issues -- kernel.principal_role, the two standing functions, validate_supersession_target
-- -- are none of this delta's five re-issued objects either). So every base body this file
-- re-issues below is quoted, verified, against the s43 HEAD TEXT unchanged by s45 -- confirmed
-- by reading s45-standing-lifecycle.sql in full before authoring this file, not assumed.
-- A future s-delta landing between s45 and this one that re-issues compute_row_hash,
-- ledger_kind_check, or the two projection views would need this file re-verified against ITS
-- head text -- named, not silently assumed forever-safe (the same disclosure s45's own header
-- makes about itself).
--
-- WHY (operator-side prose; NOT subject-visible): the spec §1(a)'s class, in its most general
-- form: *an authority-carrying act whose acting model identity is unrepresentable in the
-- record, so a substituted authority is indistinguishable from the authority it substituted.*
-- The 2026-07-17 specimen (ledger row 1434): the ledger's actor column said "author" for every
-- orchestrator act; nothing recorded the MODEL behind the principal; the substitution was
-- invisible in the very record system built to make substituted authority representable. This
-- delta is the DISCIPLINED closure of that gap for every world born with it: a model-identity
-- attestation becomes representable only in a typed shape -- FK-structural target, verbatim
-- model string, closed-vocabulary grade/verdict, a structural expectation/verdict coupling --
-- attributed, hash-covered, boundary-written, supersedable; a malformed attestation is
-- unrepresentable at construction and its attempt is itself a recorded refusal event (s43's
-- write_refused machinery, inherited for free -- this delta adds no new refusal MECHANISM, only
-- a new CHECK-guarded shape the existing boundary/journaler already enforces generically).
-- The spec's own v1 (ordinary `verification`/`note` rows, unchanged by this file) remains the
-- ONLY path that can attest the CURRENT live world's rows (runs-are-linear forecloses a new
-- kind ever reaching a past world); this delta is v2, the typed form for every FUTURE world.
--
-- ELEMENT 1 -- THE KIND (spec §8.2): `model_identity_attested`, twenty-fifth member of the
-- kind vocabulary (s43's twenty-four, widened by exactly one). Kind CHECK re-issued DROP+ADD
-- (its ONE home, the s41->s43 idiom continued -- never a second patching constraint).
--
-- ELEMENT 2 -- SEVEN KIND-SCOPED COLUMNS (spec §8.2, shape fixed, transcribed verbatim): all
-- nullable, no column DEFAULT (the s30 lesson), each split into a kind-shape CHECK (one concern
-- per CHECK, the s40 idiom, for gates/kind_shape_manifest_gate.py's classifier) plus separate
-- value CHECKs where the column also carries a vocabulary/shape constraint:
--   attest_row_id bigint REFERENCES ledger(id)  -- the attested row. Mandatory (two-way). The
--     FK is to the SAME table -- the target's existence is thereby structural, never CLI-side.
--   attest_model text        -- mandatory non-empty (two-way kind-shape + separate non-empty
--     value CHECK); the event's `model` string VERBATIM, never normalized (the spec's own §11
--     denomination discipline transposed to this column: identity in the emitter's own
--     vocabulary, aliasing is a reader concern).
--   attest_grade text        -- mandatory (two-way); closed value CHECK IN ('exact-command',
--     'turn-bracketed','session-scoped','ambiguous') -- the spec's own closed grade
--     vocabulary. Closed is right here (kernel-structural, like s43's refusal_surface): the
--     grades enumerate THIS design's own join algebra, not organizational naming (contrast
--     s41's free-text role names).
--   attest_verdict text      -- mandatory (two-way); closed value CHECK IN ('match','mismatch',
--     'unevaluated') -- lowercase, per the spec's own denomination note (§11 of the pipeline
--     spec: "the verdict casing in each arm's own written form -- MISMATCH v1, mismatch s44,
--     never case-folded into a third convention").
--   attest_expected text     -- nullable WITHIN the kind (one-way kind-shape CHECK: non-NULL
--     only on this kind); non-empty when present (separate value CHECK). NULL means the
--     session declared no expected model. STRUCTURALLY coupled to the verdict (spec's own
--     fixed rule, transcribed exactly): (attest_expected IS NULL) = (attest_verdict =
--     'unevaluated') -- an unevaluated verdict WITH a declared expectation, or a match/mismatch
--     claim with nothing to match against, is unrepresentable.
--   attest_session text      -- mandatory non-empty (two-way + value CHECK); the OTel
--     `session.id`.
--   attest_basis text        -- mandatory non-empty (two-way + value CHECK); the
--     comma-separated join keys used (the spec's own §6 vocabulary).
--
-- Supersession: ALLOWED, deliberately (spec §8.2's own argued contrast with s43's
-- write_refused) -- an attestation is a defeasible claim, retractable and correctable by
-- design, so s31 uniform supersession applies UNCHANGED; no validate_supersession_target
-- re-issue is needed or made (the standing-lifecycle discipline s45 added is scoped to its own
-- three kinds and stays untouched here -- this kind is NOT one of them, by design: the two
-- postures differ because the two kinds' semantics differ, per the spec's own argued text).
--
-- ELEMENT 3 -- DERIVED VIEW `model_attestations` (spec §8.2): security_invoker, factoring
-- through ledger_current exclusively (the s31 reader discipline, no raw-`ledger` leg) -- one
-- row per in-force attestation (attested row id, model, grade, verdict, expected, session,
-- attesting actor, ts, row id). GRANT SELECT TO :role. The human/SPA audit surface; display,
-- never enforcement.
--
-- ELEMENT 4 -- SAME-COMMIT SET (spec §8.2's "Same-commit set" paragraph, executed): (a)
-- ledger_current/countersigned_in_force RE-ISSUED with the seven columns appended at the END
-- (the s20 lesson; the column list = the s43 head's exact list + seven -- verified against the
-- s43 head text quoted above, unedited by s45); (b) compute_row_hash RE-ISSUED to 65 columns
-- (the seven appended in catalog ordinal order, all text/bigint renderings per s42's fixed
-- per-type rules -- s42's law self-applied, the first exercise of it by a delta that is NOT
-- part of the s42/s43 family itself); (c) the kind CHECK re-issued widened (Element 1); (d)
-- gates/kind_shape_manifest_gate.py CHAIN += s44 plus seven MANIFEST rows (this same commit);
-- (e) gates/ledger_reader_allowlist.py CHAIN += s44 (the new view is expected to classify
-- clean -- witnessed at §8.4's ceremony below, never merely asserted); (f) this file's
-- .detect.sql sibling, behavior-fingerprinted per the migrate-detect-drift ruling
-- (2026-07-16); (g) the engine leg -- entry/6 is kind-generic (verified at s40/s41/s43/s45,
-- unchanged here); the new kind flows through with NO new `.lp` predicate of its own (the
-- defeat pipeline's `ledger_defeat.lp`, already built per FABLE-DEFEAT-PIPELINE-SPEC.md, reads
-- this kind's typed columns via `engine/ledger_edb.py`'s existing `export_defeat` typed-arm
-- detection -- capability-gated on the `attest_row_id` COLUMN's presence, not on this file's
-- name, so it needs no edit of its own to recognize a world carrying this delta); `./judge`
-- witnessed in AGREE on a fixture carrying it, never asserted (§8.4 below, and the pipeline
-- spec's own W12).
--
-- WHAT THIS DELTA DOES NOT TOUCH, stated as loudly as what it does (mirroring s45's own
-- discipline): ZERO new triggers (all constraints are same-row CHECKs plus the one FK --
-- deliberately trigger-free, spec §8.5's own closure line); ZERO edits to
-- validate_supersession_target, set_actor, kernel.principal_role, or either standing function
-- (this delta's kind participates in NONE of the standing-lifecycle machinery s45 added); ZERO
-- CLI (led.tmpl) edits -- writing this kind is the future otel-attest verb's own concern, per
-- the sentry spec's own §17 item 7 ("build ... exactly per §8" -- the KERNEL shape only; the
-- verb itself stays UNBUILT against this kind, named in this delta's own LIMITS below,
-- matching the sentry spec's §8.6 "the delta still reaches reality only at a future world's
-- birth" and the pipeline spec's honest-limits section naming the current world as
-- watch-and-attest-only).
--
-- CLI-SIDE RESIDUE, named per the spec §8.3 (not silently left): one in-force attestation per
-- (actor, attested row) and the no-self-attestation rule are cross-row properties the CHECK
-- machinery cannot express without lookups -- verb-enforced (a direct-psql writer could
-- double-attest or self-attest; the accepted direct-writer boundary s41 D-8 already names for
-- value-continuity, disclosed here on the same footing). A MISMATCH companion `finding` row
-- remains verb-side convention in v2 as in v1 (a trigger minting side-effect rows would open a
-- new kernel idiom this spec does not license, per its own §8.3).
--
-- HISTORY: safe -- per-mechanism grounds (spec §8.1/§8.5, executed):
--   * the kind CHECK is re-issued WIDER (additive: every pre-existing s43-head kind's legality
--     is unchanged; the new kind is disjoint and, being BORN in this delta on any birth chain
--     that carries it, no pre-existing row of it can exist to violate the widened CHECK --
--     vacuous ADD CONSTRAINT validation, the s40/s41/s43 precedent).
--   * all seven new columns' kind-shape CHECKs validate vacuously for the same reason (the kind
--     is born here); the six mandatory (two-way) columns' CHECKs and the one legitimately-NULL
--     (one-way, attest_expected) column's CHECK are each safe by the same vacuous-validation
--     argument s40's own basis names (C5).
--   * ledger_current/countersigned_in_force gain seven columns APPENDED at the end -- no
--     existing consumer's column-position assumption breaks (the s20 lesson, applied again).
--   * compute_row_hash is re-issued to 65 columns -- s42's law, self-applied; every pre-existing
--     row's hash is UNAFFECTED because this file, like every kernel-lineage file, is never
--     applied to a world with existing rows (runs-are-linear; "before" exists only on scratch).
--   * the FK (attest_row_id -> ledger.id) and the model_attestations view are new objects with
--     no pre-existing reader.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's OWN slice -- the spec's
-- own §8.5 is the FAMILY-INTENDED closure text, reproduced faithfully here as this file's):
--   - INVARIANT: in an s44 world, a model-identity attestation is representable only in the
--     typed shape -- target structural (FK), model verbatim, grade and verdict in closed
--     vocabularies, expectation/verdict coupling structural -- attributed, hash-covered,
--     boundary-written, supersedable; a malformed attestation is unrepresentable at
--     construction and its attempt is itself a recorded refusal event.
--   - QUANTIFICATION UNIVERSE: kinds carrying each new column: exactly `model_identity_attested`
--     (two-way CHECKs; attest_expected one-way within the kind plus the coupling CHECK); views:
--     the two projection homes re-issued +7, model_attestations new, non-members re-verified
--     per the s40/s41/s43/s45 lists (none does general column passthrough -- checked against
--     each prior delta's own closure text, none touches this delta's seven columns); triggers:
--     NONE new (all constraints are same-row CHECKs plus the FK -- deliberately trigger-free);
--     hash: the seven columns inside the v2 serialization, gate-enforced; CLI-side residue:
--     enumerated above, not silent.
--   - DENOMINATION: grade in the join-set vocabulary; verdict in a three-member closed set
--     coupled structurally to the expectation's presence; model identity in the emitter's
--     verbatim string; the target in an immutable ledger id via FK. No bound is a bare round
--     literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (mirroring the spec's own §8 framing: "kernel-touching by
-- definition... ships only under this spec's ratification -- it is not class-ratifiable (new
-- semantics, not only new refusals)"). It ships under design/FABLE-OTEL-SENTRY-SPEC.md's own
-- authoring authority (its header: "Fable-authored, fresh-context... REVISED same day per the
-- maintainer's response") plus this build's own commission.
--
-- LIMITS (pre-registered, per the spec §16 transposed to this delta's own slice):
--   - This file ships the KERNEL SHAPE only. NO verb writes this kind yet -- `otel-attest`
--     (the existing repo-root verb) remains unedited by this commission: the sentry spec
--     directs v1's ordinary-row convention as the ONLY live-world write path (§5, §17 item 5),
--     and nowhere directs the VERB itself to gain typed-column writes; the spec's own §17 item
--     7 commissions only "build kernel/lineage/s44-... exactly per §8" -- the kernel delta, not
--     a verb change. Named here so a future reader does not infer a write path that does not
--     exist.
--   - The two CLI-side cross-row properties named above (one-attestation-per-actor-per-row,
--     no-self-attestation) are unenforced by any CHECK -- a direct-psql writer bypasses both;
--     the same accepted bound s41 D-8 already carries.
--   - Everything in the sentry spec's own §7 (R1-R7) and §16 honest limits applies to every row
--     this kind can ever hold -- an attestation is defeasible evidence from a diagnostics-tier,
--     unauthenticated-emitter channel; this delta only makes THAT evidence's shape typed and
--     structural, never makes it true.
--   - No cryptography of any kind is added, generated, or required by this delta (the standing
--     crypto deferral, honored).
--   - Reaches reality only at a FUTURE world's birth (RD-2 per FABLE-DEFEAT-PIPELINE-SPEC.md's
--     ratified row 1481: "s44 enters the first birth chain AFTER v1 attestation rows have run
--     live and the maintainer has reviewed them -- evidence-triggered, no calendar"). This
--     builder's act does NOT trigger RD-2; wiring this file into bootstrap/new-project.sh's
--     LINEAGE_CHAIN (this same commit, per the s40/s41/s42/s43/s45 precedent) makes the delta
--     APPLICABLE to a future --new-world run, which is a distinct act from the maintainer's own
--     sequencing decision about WHEN to actually run one.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s45):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s44val -v kern=s44val_kernel -v role=s44val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        ... (s21..s43, s45 as in s45's own VALIDATE list) ... \
--        -f s45-standing-lifecycle.sql -f s44-model-identity-attestation.sql
--     (genesis seed per s26; the s40 birth acts through the BOUNDARY functions -- the
--     scaffold's scripted form in bootstrap/new-project.sh is authoritative.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in this SAME commit, at the
--   maintainer's own future sequencing act (RD-2). Authored and scratch-witnessed on scratch
--   schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW).
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
-- ELEMENT 1 -- KIND VOCABULARY WIDENED (twenty-fifth member).
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
     'model_identity_attested'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s44-model-identity-attestation.sql: widens s43''s twenty-four-member
   vocabulary by model_identity_attested -- the typed form of a defeasible model-identity
   attestation (design/FABLE-OTEL-SENTRY-SPEC.md §8). Supersession-retractable (s31 uniform
   retraction, unchanged) -- an attestation is a defeasible claim, deliberately NOT given
   write_refused''s R6 unretractability.';

-- ============================================================================================
-- ELEMENT 2 -- THE SEVEN KIND-SCOPED COLUMNS.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS attest_row_id bigint
    REFERENCES :"schema".ledger(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS attest_model text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS attest_grade text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS attest_verdict text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS attest_expected text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS attest_session text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS attest_basis text;

COMMENT ON COLUMN :"schema".ledger.attest_row_id IS
  'The ATTESTED row -- self-referencing FK, so the target''s existence is structural, never
   CLI-side. Mandatory on model_identity_attested, forbidden elsewhere.
   kernel/lineage/s44-model-identity-attestation.sql (design/FABLE-OTEL-SENTRY-SPEC.md §8.2).';
COMMENT ON COLUMN :"schema".ledger.attest_model IS
  'The observed model string, VERBATIM from the OTel event -- never normalized (identity in the
   emitter''s own vocabulary; aliasing is a reader concern). Mandatory non-empty.
   kernel/lineage/s44-model-identity-attestation.sql.';
COMMENT ON COLUMN :"schema".ledger.attest_grade IS
  'The closed join-set confidence grade: exact-command | turn-bracketed | session-scoped |
   ambiguous (design/FABLE-OTEL-SENTRY-SPEC.md §6). Kernel-structural closed vocabulary (it
   enumerates this design''s own join algebra, like s43''s refusal_surface) -- deliberately
   UNREAD by the defeat rule (grade-conditioned defeat is a ratified direction-only decision,
   Q3, not yet built -- design/FABLE-DEFEAT-PIPELINE-SPEC.md §13).
   kernel/lineage/s44-model-identity-attestation.sql.';
COMMENT ON COLUMN :"schema".ledger.attest_verdict IS
  'The closed verdict: match | mismatch | unevaluated (lowercase -- the s44 typed arm''s own
   casing, distinct from the v1 convention''s uppercase MISMATCH; never case-folded into a
   third convention, design/FABLE-DEFEAT-PIPELINE-SPEC.md §11). Structurally coupled to
   attest_expected (see that column''s comment). kernel/lineage/s44-model-identity-attestation.sql.';
COMMENT ON COLUMN :"schema".ledger.attest_expected IS
  'The declared expected model, or NULL when the session declared none. Nullable WITHIN the
   kind (one-way kind-shape CHECK) -- coupled structurally to attest_verdict: (attest_expected
   IS NULL) = (attest_verdict = ''unevaluated''). An unevaluated verdict with a declared
   expectation, or a match/mismatch claim with nothing to match against, is unrepresentable.
   kernel/lineage/s44-model-identity-attestation.sql.';
COMMENT ON COLUMN :"schema".ledger.attest_session IS
  'The OTel session.id the observed event belongs to. Mandatory non-empty.
   kernel/lineage/s44-model-identity-attestation.sql.';
COMMENT ON COLUMN :"schema".ledger.attest_basis IS
  'The comma-separated join keys actually used (design/FABLE-OTEL-SENTRY-SPEC.md §6''s
   vocabulary). Mandatory non-empty. kernel/lineage/s44-model-identity-attestation.sql.';

-- kind-shape CHECKs (one concern per CHECK -- the s40 idiom; two-way where mandatory, one-way
-- for the legitimately-NULL expectation):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_row_id_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_row_id_kind_shape CHECK (
    (kind = 'model_identity_attested') = (attest_row_id IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_model_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_model_kind_shape CHECK (
    (kind = 'model_identity_attested') = (attest_model IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_grade_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_grade_kind_shape CHECK (
    (kind = 'model_identity_attested') = (attest_grade IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_verdict_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_verdict_kind_shape CHECK (
    (kind = 'model_identity_attested') = (attest_verdict IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_expected_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_expected_kind_shape CHECK (
    attest_expected IS NULL OR kind = 'model_identity_attested');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_session_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_session_kind_shape CHECK (
    (kind = 'model_identity_attested') = (attest_session IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_basis_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_basis_kind_shape CHECK (
    (kind = 'model_identity_attested') = (attest_basis IS NOT NULL));

-- value CHECKs (no kind test -- out of the kind-shape manifest's scope by its classifier):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_model_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_model_nonempty CHECK (
    attest_model IS NULL OR btrim(attest_model) <> '');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_grade_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_grade_check CHECK (
    attest_grade IS NULL
    OR attest_grade IN ('exact-command','turn-bracketed','session-scoped','ambiguous'));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_verdict_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_verdict_check CHECK (
    attest_verdict IS NULL OR attest_verdict IN ('match','mismatch','unevaluated'));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_expected_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_expected_nonempty CHECK (
    attest_expected IS NULL OR btrim(attest_expected) <> '');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_session_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_session_nonempty CHECK (
    attest_session IS NULL OR btrim(attest_session) <> '');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_basis_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_basis_nonempty CHECK (
    attest_basis IS NULL OR btrim(attest_basis) <> '');

-- the structural expectation/verdict coupling (spec §8.2's own fixed rule, transcribed):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS attest_expected_verdict_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT attest_expected_verdict_coupling CHECK (
    kind <> 'model_identity_attested'
    OR (attest_expected IS NULL) = (attest_verdict = 'unevaluated'));

COMMENT ON CONSTRAINT attest_expected_verdict_coupling ON :"schema".ledger IS
  'design/FABLE-OTEL-SENTRY-SPEC.md §8.2''s fixed structural rule: an unevaluated verdict with a
   declared expectation, or a match/mismatch claim with nothing to match against, is
   unrepresentable. kernel/lineage/s44-model-identity-attestation.sql.';

-- ============================================================================================
-- ELEMENT 3 -- s42'S LAW SELF-APPLIED: compute_row_hash re-issued to 65 columns (the seven
-- attest_* columns appended in catalog ordinal order, before the predecessor link; every other
-- rendering byte-identical to the s43 head's -- verified against that file's own text above,
-- unedited by s45).
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
      -- s44: the seven model-identity-attestation columns (catalog ordinals 60..66)
      hashfield(r.attest_row_id::text),
      hashfield(r.attest_model),
      hashfield(r.attest_grade),
      hashfield(r.attest_verdict),
      hashfield(r.attest_expected),
      hashfield(r.attest_session),
      hashfield(r.attest_basis),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 4 -- THE TWO COLUMN-COMPLETE VIEWS, +7 APPENDED (the s20 lesson). Base bodies: the
-- s43 head's, unedited by s45 (verified above).
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
       l.attest_session, l.attest_basis
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
       l.attest_session, l.attest_basis
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 5 -- THE DERIVED VIEW model_attestations (spec §8.2): security_invoker, factoring
-- through ledger_current exclusively (the s31 reader discipline, no raw-`ledger` leg). The
-- human/SPA audit surface; display, never enforcement.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".model_attestations
    WITH (security_invoker = true) AS
SELECT lc.attest_row_id AS attested_row_id,
       lc.attest_model AS model,
       lc.attest_grade AS grade,
       lc.attest_verdict AS verdict,
       lc.attest_expected AS expected,
       lc.attest_session AS session,
       lc.actor AS attesting_actor,
       lc.ts,
       lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'model_identity_attested';

COMMENT ON VIEW :"schema".model_attestations IS
  'The human/SPA audit surface for model-identity attestations (design/FABLE-OTEL-SENTRY-SPEC.md
   §8.2): one row per IN-FORCE attestation, factored through ledger_current exclusively (the s31
   reader discipline -- no raw ledger leg). Display only, never enforcement -- the defeat
   pipeline (design/FABLE-DEFEAT-PIPELINE-SPEC.md) reads the typed columns directly via
   engine/ledger_edb.py''s export_defeat, not this view. kernel/lineage/
   s44-model-identity-attestation.sql.';

GRANT SELECT ON :"schema".model_attestations TO :"role";
