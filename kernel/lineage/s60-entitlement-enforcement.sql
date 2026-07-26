-- s60 ENTITLEMENT ENFORCEMENT (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1, the RATIFIED
-- assembly basis -- rows 1379/1380 ratify design/CONSULT-WORK-GATING-SHAPE-2026-07-26.md §§B-C
-- as the elaborated content the spec cites; row 1377 folds in the domains/read-access
-- requirements as LATER conjunct seats, reserved, not built here). FAIL-SAFE-ADDITIVE
-- (CLAUDE.md 2026-07-09 class rule): this delta ONLY ADDS refusals -- one new kind, one new
-- column (plus a widened re-use of an existing column), one new BEFORE INSERT trigger member,
-- and read-only derived views/functions; nothing existing is relaxed, no existing CHECK
-- narrowed, no existing trigger BODY re-issued. Sonnet-built per the standing delegation
-- contract, from the ratified spec; the ASP twin ships in the SAME delta (spec §1 item 2),
-- not filed as pairing debt.
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s59 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second copy of any existing mechanism (ADR-0012 P1: entitlement gains ONE new trigger member,
-- validate_entitlement, coexisting with validate_principal_binding/validate_supersession_target/
-- validate_work_item exactly as those already coexist with one another -- each a separate,
-- disjoint-concern member of the same BEFORE INSERT chain, never a second copy of any of them;
-- role bindings ride the EXISTING principal_role_bound kind and principal_role_bindings view
-- (s41), acts-for chains ride the EXISTING principal_relation_asserted/'acts-for' kind and
-- principal_relations view (s41) -- entitlement invents no second delegation/role primitive).
--
-- PREREQUISITE: this delta REQUIRES s59 (kernel/lineage/s59-missive-views.sql) applied first --
-- it re-issues compute_row_hash/ledger_current/countersigned_in_force in the EXACT 87-column
-- shape s58 left them (s59 added no column), and re-issues ledger_kind_check in the exact
-- thirty-member shape s58 left it, widened by one. It ALSO reads (never re-issues)
-- kernel.principal_standing (s40/s45), principal_relations/principal_role_bindings (s41 D-5),
-- work_edge_blocks_start (s39 Element 1b), work_item_current (s22+), and ledger_current itself
-- -- every one of those objects must already exist in its s59-head shape. Applying this file on
-- a pre-s59 kernel fails loudly at CREATE OR REPLACE VIEW/FUNCTION time (a column or relation
-- referenced does not exist), the correct, disclosed failure mode, matching every prior
-- PREREQUISITE precedent. THE HEAD-BODY RULE (s45's own standing instruction, carried here
-- verbatim): at this delta's authoring the lineage head is s59 (kernel/lineage/'s own directory
-- listing, confirmed by the builder before authoring); this file's re-issued bodies are quoted,
-- verified, against the s59 head text -- NOTE, surfaced rather than silently assumed: the
-- scaffold's own LINEAGE_CHAIN (bootstrap/new-project.sh) currently wires only through s57 --
-- s58/s59 exist as authored, scratch-witnessed files not yet entered into any birth chain. This
-- delta is authored against the true lineage HEAD (s59), per the head-body rule's own text
-- ("the lineage head" means the latest authored file, not the latest WIRED one); the scaffold's
-- own LINEAGE_CHAIN wiring gap (s58/s59 unwired) is a PRE-EXISTING condition this delta neither
-- creates nor is required to close -- named here as a divergence surfaced, not silently
-- absorbed, per CLAUDE.md's spirit-governs rule. This delta's own scaffold edit (below, the
-- birth-sequence role binding) is written assuming s58/s59/s60 all precede it in whichever
-- chain a future integration wires -- if s58/s59 land unwired ahead of this delta at
-- integration time, this file's own VALIDATE list names the exact intermediate files a scratch
-- apply needs, and the scaffold edit is a pure append at the SAME point s40's own three birth
-- acts already sit, colliding with no other in-review scaffold edit by construction (append-
-- only insertion after the existing step-4 loop, nothing existing moved or re-ordered).
--
-- WHY (operator-side prose; NOT subject-visible): the spec's own headline, inherited from the
-- consult (§A4/§A6): s41 could RECORD a role binding or an acts-for delegation, but nothing
-- CHECKED either at write time -- "any active principal may supersede an allocation, bind a
-- role, or register a principal" (the AC/IA audit's IA-4 clause-(a) finding). This delta closes
-- exactly that gap, and no more: a factored acceptance predicate, evaluated inside the s43
-- write-boundary's own trigger chain, per act class. Conjunct (a): the actor holds an in-force
-- role binding this world's configuration names for the act class (the s36 graded-token idiom:
-- the kernel stores and matches free-text tokens, no enum, no closed vocabulary of role OR
-- act-class names -- which words a deployment configures is policy, read here only by
-- string-equality). Conjunct (b): for the authority-bearing act set (spec §1.1b, verbatim:
-- principal registration, role binding, standing lifecycle, allocation/milestone closure and
-- supersession, gate-edge supersession), the actor's authority chain -- transitive
-- reachability over in-force acts-for relations -- roots at the world's genesis principal,
-- evaluated FRESH at act time (the s40 "computed at read, never stored" law), never cached.
--
-- ATTENTION POINT 1 (spec §5.1, provisional, maintainer's leisure): the DEFAULT act-class role
-- map is POLICY, not kernel vocabulary -- built here as the spec's own named authority-bearing
-- set (below), one uniform role name ('authority') across all five default-mapped classes, for
-- the simplest possible birth-sequence discharge (one role, one bind act). A deployment
-- reconfigures by writing fresh entitlement_class_configured rows (Element 6) naming different
-- role names per class; nothing in this delta's CHECKs or triggers hardcodes 'authority' as
-- special. MARKED PROVISIONAL, per the commission's own instruction.
--
-- ATTENTION POINT 2 (spec §5.2, provisional, the commission's own NARROWER inclination, taken):
-- "allocation/milestone closure and supersession" gates ONLY a work_closed act on a slug that
-- ITSELF carries at least one IN-FORCE inbound blocks-start edge (i.e. IS a milestone something
-- else's claim depends on) -- an ordinary, non-milestone work item's close is NOT
-- entitlement-gated. Taken because the commission named it "my inclination" and because the
-- WIDER reading (every close, milestone or not) would make entitlement enforcement a standing
-- tax on ordinary solo-world work-item bookkeeping, in tension with the zero-friction
-- requirement (spec §1.3) for a class of act the consult's own worked example never asks to be
-- gated (§B.4: only the MILESTONE's own close is the "switch"). MARKED PROVISIONAL.
--
-- A THIRD ADDITION, SURFACED RATHER THAN SILENTLY FOLDED IN (CLAUDE.md's hazard-in-reach
-- corollary; NOT one of the spec's own numbered attention points, added by this builder's own
-- judgment and named here for the maintainer's review): the act of WRITING an
-- entitlement_class_configured row -- i.e. reconfiguring which role a class requires -- is
-- itself placed in the authority-bearing set (conjunct (b), unconditionally, never
-- configuration-gated by conjunct (a) in the default map -- see Element 7's own note on why).
-- The spec's §1.1b list does not name this class explicitly; the mechanism that decides "who
-- may act" is a hazard in reach of this very delta if its own configuration surface ships
-- unprotected (the nail left standing next to the plank this delta drives down) -- so entering
-- it in the hardcoded authority-bearing set is a strictly ADDITIVE refusal (fail-safe-additive
-- discipline honored: this only narrows who may reconfigure entitlement, it relaxes nothing).
-- Flagged loudly per the commission's own instruction ("divergences surfaced, never silently
-- applied"), not silently folded into the spec's own enumerated set.
--
-- ELEMENT 1 -- ONE NEW KIND: entitlement_class_configured (thirty-first member). A configuration
-- EVENT (the s36 graded-token idiom applied to a second axis): each row NAMES the act class it
-- configures (entitlement_act_class, a new column, IDENTITY field, free text, no enum -- the
-- kernel matches act-class strings this delta's OWN code computes, see Element 4) and the role
-- name required for it (principal_role_name, REUSED from s41 -- one column, one home, ADR-0012
-- P1, rather than a second near-identical "role name" column; its kind-shape CHECK is widened
-- below to license this second kind). No active/inactive discriminator: unlike s41's bindings
-- (which support withdrawal-with-no-replacement), a configuration row supports only FRESH
-- assertion and ROTATION (a later row for the SAME act class supersedes or simply out-dates the
-- prior one by id -- the governing row is the latest unsuperseded one, kernel.principal_role's
-- own pre-s45 shape, Element 5 below) -- DE-CONFIGURING an act class entirely (removing its role
-- requirement) is deliberately NOT representable in v1: that would be a mechanism for RELAXING
-- an existing refusal, out of the fail-safe-additive class this delta ships under. Rotation to a
-- DIFFERENT role name stays available (still requires SOME role); named as a LIMIT, not
-- silently built anyway.
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
     'obligation_revoked',
     'missive_sent','missive_received','missive_disposed',
     'entitlement_class_configured'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s60-entitlement-enforcement.sql: widens s58''s thirty-member vocabulary by
   entitlement_class_configured -- the configuration event naming which role name a given act
   class requires (conjunct (a) of the factored acceptance predicate, design/
   FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1). Governing row per act class = latest unsuperseded
   (kernel.principal_role''s own pre-s45 max-id-per-key shape, Element 5 below); no
   de-configuration path exists in v1 (LIMITS).';

-- ============================================================================================
-- ELEMENT 2 -- THE ONE NEW COLUMN + THE ONE WIDENED REUSE.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS entitlement_act_class text;

COMMENT ON COLUMN :"schema".ledger.entitlement_act_class IS
  'kernel/lineage/s60-entitlement-enforcement.sql: the act-class token an
   entitlement_class_configured row names (identity field, mandatory on that kind, forbidden
   elsewhere). Free text, no enum -- the kernel-computed set of act-class strings this delta''s
   own entitlement_act_class_of() function emits is the only vocabulary a configuration row can
   USEFULLY match (an unrecognized token is legal to write, simply never matches any write --
   the s36 decision_grade precedent for a free-text policy token, named explicitly in that
   delta''s own LIMITS as the accepted shape).';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS entitlement_act_class_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT entitlement_act_class_kind_shape CHECK (
    (kind = 'entitlement_class_configured') = (entitlement_act_class IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS entitlement_act_class_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT entitlement_act_class_nonempty CHECK (
    entitlement_act_class IS NULL OR btrim(entitlement_act_class) <> '');

-- principal_role_name's kind-shape CHECK (s41's ONE home) widened to license the SECOND kind
-- that carries it -- never a second, parallel column (ADR-0012 P1). Additive on both sides of
-- the iff: principal_role_bound keeps its exact pre-existing legality; entitlement_class_configured
-- joins the licensed set.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_role_name_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_role_name_kind_shape CHECK (
    (kind IN ('principal_role_bound', 'entitlement_class_configured'))
    = (principal_role_name IS NOT NULL));

COMMENT ON COLUMN :"schema".ledger.principal_role_name IS
  'The organizational role name a row binds or requires. FREE NON-EMPTY TEXT, NOT a closed
   vocabulary (s41 basis §9(c)/C13, unchanged). Licensed on TWO kinds since s60
   (kernel/lineage/s60-entitlement-enforcement.sql): principal_role_bound (s41, "this role is
   bound to this principal") and entitlement_class_configured ("this act class requires this
   role") -- the SAME free-text vocabulary answers both questions by design, so a deployment
   names its roles once.';

-- ============================================================================================
-- ELEMENT 3 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 88 COLUMNS (the one new
-- column appended in serialization order, before the predecessor link; base body = s58's own
-- text, verified unedited by s59). principal_role_name is ALREADY serialized (s41) -- reusing
-- the column costs this re-issue nothing beyond the one new field.
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
      hashfield(r.obligation_revoked_scope),
      hashfield(r.obligation_revoke_reason),
      hashfield(r.missive_protocol::text),
      hashfield(r.missive_author_world),
      hashfield(r.missive_addressee_world),
      hashfield(r.missive_thread),
      hashfield(r.missive_seq::text),
      hashfield(r.missive_act),
      hashfield(r.missive_responds_to),
      hashfield(r.missive_provenance),
      hashfield(r.missive_cites),
      hashfield(r.missive_disposition),
      hashfield(r.missive_regards::text),
      -- s60: the one new column, appended last before the predecessor link.
      hashfield(r.entitlement_act_class),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 3b -- the two column-complete views, +1 appended (the s20 lesson).
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
       l.obligation_revoked_scope, l.obligation_revoke_reason,
       l.missive_protocol, l.missive_author_world, l.missive_addressee_world, l.missive_thread,
       l.missive_seq, l.missive_act, l.missive_responds_to, l.missive_provenance,
       l.missive_cites, l.missive_disposition, l.missive_regards,
       l.entitlement_act_class
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
       l.obligation_revoked_scope, l.obligation_revoke_reason,
       l.missive_protocol, l.missive_author_world, l.missive_addressee_world, l.missive_thread,
       l.missive_seq, l.missive_act, l.missive_responds_to, l.missive_provenance,
       l.missive_cites, l.missive_disposition, l.missive_regards,
       l.entitlement_act_class
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 4 -- THE GOVERNING CONFIG READ: entitlement_class_roles (mirrors kernel.principal_role's
-- own pre-s45 max-id-per-key shape exactly -- no active flag, no reinstatement machinery: v1
-- supports fresh-assert and rotation only, LIMITS above).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".entitlement_class_roles
    WITH (security_invoker = true) AS
SELECT lc.entitlement_act_class AS act_class, lc.principal_role_name AS role_name,
       lc.actor AS configured_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'entitlement_class_configured'
  AND  lc.id = (SELECT max(lc2.id) FROM :"schema".ledger_current lc2
                WHERE lc2.kind = 'entitlement_class_configured'
                  AND lc2.entitlement_act_class = lc.entitlement_act_class);

COMMENT ON VIEW :"schema".entitlement_class_roles IS
  'kernel/lineage/s60-entitlement-enforcement.sql: the governing entitlement_class_configured row
   per act-class token -- the LATEST unsuperseded configuration event for that class (rotation =
   a newer row; no de-configuration path in v1, mirroring kernel.principal_role''s own pre-s45
   shape, kernel/lineage/s40-principal-identity-events.sql Element 5). An act class absent from
   this view is UNCONFIGURED -- conjunct (a) reads that as vacuously satisfied (Element 7).';

GRANT SELECT ON :"schema".entitlement_class_roles TO :"role";

-- ============================================================================================
-- ELEMENT 5 -- THE GENESIS READ: entitlement_genesis_principal(). Deliberately RAW `ledger`, NOT
-- ledger_current -- genesis identity must be an immutable HISTORICAL fact (the first-ever
-- principal_registered row's own subject, by insertion order), never a current-truth read: s45's
-- own LIMITS name principal_registered targets as OUTSIDE its supersession discipline (no
-- same-kind/identity-continuity guard exists for that kind), so if genesis identification read
-- ledger_current, a later (unprotected) supersession of the genesis principal''s OWN
-- registration event could silently shift WHO genesis is. Reading raw, first-by-id, sidesteps
-- that gap entirely rather than depending on a protection s45 does not provide -- named here as
-- a load-bearing design choice, not an oversight. Declared allowlist reader (gates/
-- ledger_reader_allowlist.py, this same commit): :role already holds SELECT on raw `ledger`
-- (s15), so no grant is needed.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_genesis_principal()
    RETURNS bigint LANGUAGE sql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
  SELECT principal_subject FROM ledger
  WHERE  kind = 'principal_registered'
  ORDER BY id ASC LIMIT 1;
$fn$;

COMMENT ON FUNCTION :"schema".entitlement_genesis_principal() IS
  'kernel/lineage/s60-entitlement-enforcement.sql: the world''s genesis principal -- the subject
   of the FIRST-EVER principal_registered row, by insertion order, read from RAW `ledger` (never
   ledger_current -- see this function''s own header note for why: a genesis identity must be an
   immutable historical fact, not a current-truth read s45''s own disclosed gap could destabilize).
   NULL only in a world where no principal has ever been registered (the bootstrapping case
   principal_authority_chain_reaches_genesis treats as a genesis exception, Element 6).';

-- ============================================================================================
-- ELEMENT 6 -- THE CHAIN READ: principal_authority_chain_reaches_genesis(pid). Depth-capped
-- (10000, the work_blocks_start_would_cycle shape, s39) transitive reachability over IN-FORCE
-- acts-for relations (principal_relations, s41 D-5 -- already unsuperseded-AND-active filtered),
-- computed FRESH on every call (STABLE, never cached across statements -- the s40 "computed at
-- read" law). Each hop requires the DELEGATING principal (the far endpoint, `object`) to be
-- presently 'active' standing (kernel.principal_standing -- called UNQUALIFIED inside this
-- function's own body, deliberately: a dollar-quoted body is NOT a site psql performs :"var"
-- substitution in -- verified empirically THIS delta's own first scratch-witness attempt, the
-- exact NOTE s39's work_item_blocks_start_blockers already carries for the identical reason --
-- so `kernel.principal_standing(...)` with a LITERAL schema prefix fails loudly the moment :kern
-- is anything other than literally "kernel" [ERROR: schema "kernel" does not exist], caught here
-- rather than shipped; this function's own SET search_path clause resolves the unqualified name)
-- -- a suspended or revoked delegate
-- SEVERS every chain through them PROSPECTIVELY (I5 asymmetry, kernel/lineage/
-- s45-standing-lifecycle.sql Element 3: "lifecycle standing NEVER conditions defeat force" governs
-- a DIFFERENT layer; here it is the ENTITLEMENT chain, evaluated fresh, that a standing change
-- naturally re-derives differently on the NEXT act -- it does not retroactively alter any row
-- already accepted, which is exactly I5's own asymmetry one mechanism over). THE GENESIS
-- EXCEPTION (mirrors the s40 birth sequence's own "genesis exception: self-attributed" precedent
-- for the world''s first identity event): if no genesis principal exists yet
-- (entitlement_genesis_principal() IS NULL -- no principal has ever been registered), every
-- principal trivially reaches genesis -- this is the act THAT ESTABLISHES genesis, and refusing
-- it for "no chain to a genesis that does not exist yet" would brick every solo world at its own
-- birth (the zero-friction requirement, spec §1.3, taken to its own bootstrapping edge).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".principal_authority_chain_reaches_genesis(pid bigint)
    RETURNS boolean LANGUAGE plpgsql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_genesis bigint;
BEGIN
  v_genesis := entitlement_genesis_principal();
  IF v_genesis IS NULL THEN
    RETURN true;
  END IF;
  RETURN EXISTS (
    WITH RECURSIVE chain(cur, depth) AS (
      SELECT pid, 0
      UNION ALL
      SELECT pr.object, c.depth + 1
      FROM chain c
      JOIN principal_relations pr ON pr.subject = c.cur AND pr.relation = 'acts-for'
      WHERE c.depth < 10000
        AND c.cur <> v_genesis
        AND principal_standing(pr.object) = 'active'
    )
    SELECT 1 FROM chain WHERE cur = v_genesis
  );
END; $fn$;

COMMENT ON FUNCTION :"schema".principal_authority_chain_reaches_genesis(bigint) IS
  'kernel/lineage/s60-entitlement-enforcement.sql: whether principal pid''s authority chain
   (transitive reachability over IN-FORCE acts-for relations, principal_relations, s41 D-5) roots
   at this world''s genesis principal (entitlement_genesis_principal()). Depth-capped at 10000
   (the s39 work_blocks_start_would_cycle shape); each hop requires the delegating principal to
   be presently ''active'' standing (I5 asymmetry: chain death is prospective, past accepted acts
   stay credited -- this function is never consulted to re-judge history, only fresh acts, s40''s
   "computed at read" law). GENESIS EXCEPTION: TRUE for every pid when no genesis principal
   exists yet (the world''s own first registration act, self-establishing).';

-- ============================================================================================
-- ELEMENT 7 -- entitlement_act_class_of(r): the ONE home computing which act-class token (if
-- any) a candidate row belongs to. NULL for every ordinary row (assumption/decision/finding/
-- work_opened/work_claimed/...) -- the vast majority of writes never reach Element 8's trigger
-- body past its own early-return. THE AUTHORITY-BEARING SET (spec §1.1b, verbatim, PLUS the
-- one addition surfaced in this file''s own header note): principal_registered,
-- principal_role_bound, standing_lifecycle (the three s45/s40 lifecycle kinds, bundled -- the
-- spec names them as ONE bullet, "standing lifecycle"), milestone_closure (ATTENTION POINT 2:
-- gated ONLY when the closing slug carries an IN-FORCE inbound blocks-start edge --
-- work_edge_blocks_start, s39, joined to ledger_current so a RETRACTED gate edge no longer
-- qualifies its antecedent as a milestone, matching every other in-force edge reading in this
-- lineage), gate_edge_supersession (a work_depends_on row whose supersedes target is itself an
-- IN-FORCE blocks-start edge -- "quietly unbolting a gate", the consult''s own phrase), and
-- entitlement_class_configured (this file''s own header-surfaced addition). Every one of these
-- six tokens is ALSO the DEFAULT conjunct-(b) authority-bearing set (Element 8) -- five of the
-- six (all but entitlement_class_configured itself) are ALSO the default conjunct-(a) role map
-- (Element 9's birth-sequence discharge; entitlement_class_configured is deliberately left
-- OUT of the default role map -- see Element 8''s own note for why).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_act_class_of(r :"schema".ledger)
    RETURNS text LANGUAGE plpgsql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_edge_type text;
BEGIN
  IF r.kind = 'principal_registered' THEN
    RETURN 'principal_registered';
  END IF;
  IF r.kind = 'principal_role_bound' THEN
    RETURN 'principal_role_bound';
  END IF;
  IF r.kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
    RETURN 'standing_lifecycle';
  END IF;
  IF r.kind = 'entitlement_class_configured' THEN
    RETURN 'entitlement_class_configured';
  END IF;
  IF r.kind = 'work_closed' THEN
    IF EXISTS (SELECT 1 FROM work_edge_blocks_start e
               JOIN ledger_current lc ON lc.id = e.edge_row_id
               WHERE e.antecedent_slug = r.work_slug) THEN
      RETURN 'milestone_closure';
    END IF;
    RETURN NULL;
  END IF;
  IF r.kind = 'work_depends_on' AND r.supersedes IS NOT NULL THEN
    SELECT l.edge_type INTO v_target_edge_type FROM ledger l WHERE l.id = r.supersedes;
    IF v_target_edge_type = 'blocks-start' THEN
      RETURN 'gate_edge_supersession';
    END IF;
    RETURN NULL;
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of(:"schema".ledger) IS
  'kernel/lineage/s60-entitlement-enforcement.sql: the act-class token a candidate ledger row
   belongs to, or NULL if it belongs to none (the common case -- entitlement gates nothing about
   most kinds). validate_entitlement (Element 8) is the ONE caller; entitlement_class_roles
   (Element 4) and this function''s own hardcoded authority-bearing set (Element 8) are matched
   against its output by simple string equality -- the s36 graded-token idiom applied to a
   kernel-computed (not writer-supplied) vocabulary.';

-- ============================================================================================
-- ELEMENT 8 -- THE FACTORED ACCEPTANCE PREDICATE: validate_entitlement, a NEW BEFORE INSERT
-- trigger member (alphabetical position: set_actor < set_stamp < validate_entitlement <
-- validate_independence [review_detail, unaffected] < validate_principal_binding <
-- validate_supersession_target < validate_work_item < zz_set_row_hash -- 'validate_entitlement'
-- sorts before every other validate_* member, immaterial here since each guards disjoint
-- concerns over NEW, matching the s41/s45 precedent of coexisting validate_* triggers; it MUST
-- run after set_actor, which it does by alphabetical construction, since it reads NEW.actor).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_entitlement() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_act_class text;
  v_required_role text;
  v_has_role boolean;
  v_authority_bearing boolean;
  v_reaches boolean;
BEGIN
  v_act_class := entitlement_act_class_of(NEW);
  IF v_act_class IS NULL THEN
    RETURN NEW;
  END IF;

  -- CONJUNCT (a): an in-force role binding naming the configured role for this act class, IF
  -- one is configured (entitlement_class_roles, Element 4). An UNCONFIGURED act class is
  -- vacuously satisfied here -- this is what makes the birth sequence's own bootstrapping order
  -- (bind the role BEFORE writing the config that would require it) work with zero special-
  -- casing in this trigger (Element 9's own header explains the ordering).
  SELECT role_name INTO v_required_role FROM entitlement_class_roles WHERE act_class = v_act_class;
  IF v_required_role IS NOT NULL THEN
    SELECT EXISTS (SELECT 1 FROM principal_role_bindings prb
                   WHERE prb.subject = NEW.actor AND prb.role_name = v_required_role)
      INTO v_has_role;
    IF NOT v_has_role THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60, factored acceptance predicate conjunct a) — act class ''%'' requires an in-force role binding named ''%'' (this world''s configured entitlement map, see entitlement_class_roles); actor % holds no such binding. Remedy: a principal who ALREADY holds the ''%'' role (or genesis-chain authority) binds it to you: ./led principal bind-role <your-principal-name> "%" (kernel/lineage/s41-principal-bindings-and-relations.sql), then retry this act. See design/USER-RECIPES-FAQ.md''s entitlement-enforcement recipe for the worked example (kernel/lineage/s60-entitlement-enforcement.sql).', v_act_class, v_required_role, NEW.actor, v_required_role, v_required_role;
    END IF;
  END IF;

  -- CONJUNCT (b): for the authority-bearing act set (this file''s own header note names the one
  -- addition beyond spec §1.1b's literal six), the actor's authority chain must root at
  -- genesis -- UNCONDITIONAL, never configuration-gated (this class of check protects the
  -- configuration surface itself, so it cannot depend on that surface having been configured).
  v_authority_bearing := v_act_class IN (
      'principal_registered', 'principal_role_bound', 'standing_lifecycle',
      'milestone_closure', 'gate_edge_supersession', 'entitlement_class_configured');
  IF v_authority_bearing THEN
    SELECT principal_authority_chain_reaches_genesis(NEW.actor) INTO v_reaches;
    IF NOT v_reaches THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60, factored acceptance predicate conjunct b) — act class ''%'' is authority-bearing (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1.1b); actor %''s authority chain (transitive reachability over in-force acts-for relations, kernel/lineage/s41-principal-bindings-and-relations.sql) does not reach this world''s genesis principal. Remedy: an in-force acts-for relation from your principal, through zero or more active delegates, to a principal that is itself chain-connected to genesis (./led principal relate <your-principal-name> acts-for <delegator-principal-name>) — or have a severed link repaired (suspension/revocation severs a chain PROSPECTIVELY only; past accepted acts through that link stay credited, kernel/lineage/s45-standing-lifecycle.sql''s I5 asymmetry).', v_act_class, NEW.actor;
    END IF;
  END IF;

  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_entitlement ON :"schema".ledger;
CREATE TRIGGER validate_entitlement BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_entitlement();

COMMENT ON FUNCTION :"schema".validate_entitlement() IS
  'kernel/lineage/s60-entitlement-enforcement.sql: the factored acceptance predicate (design/
   FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1) -- conjunct (a) in-force role binding per configured
   act class, conjunct (b) authority-chain-to-genesis for the authority-bearing act set. Fires
   only when entitlement_act_class_of(NEW) is non-NULL (Element 7); a no-op for every ordinary
   kind. Refusals journal as write_refused rows via the s43 boundary exactly like every other
   kernel policy refusal -- no second refusal surface.';

-- ============================================================================================
-- ELEMENT 9 -- GRANTS (belt-and-braces; CREATE OR REPLACE VIEW preserves grants on
-- ledger_current/countersigned_in_force, s21's own additive-column-order idiom, re-verified here
-- exactly as every prior column-appending delta re-verified it for its own append).
-- ============================================================================================
-- (entitlement_class_roles' GRANT SELECT is issued at Element 4, immediately after its
-- CREATE OR REPLACE -- kept there rather than duplicated here, matching s36's own single-grant-
-- site idiom for standing_decisions.)

-- ============================================================================================
-- HISTORY: safe -- per-mechanism grounds:
--   * ledger_kind_check re-issued WIDER (additive vocabulary: every pre-existing kind''s
--     legality is unchanged; entitlement_class_configured is disjoint from the thirty existing
--     members and is BORN in this delta -- no pre-existing row can carry it).
--   * ONE new nullable no-DEFAULT column (entitlement_act_class), kind-scoped mandatory/
--     forbidden by a two-way CHECK that validates vacuously on every pre-existing row (no
--     pre-existing row carries the new kind).
--   * principal_role_name_kind_shape re-issued WIDER (additive on both sides of the iff:
--     principal_role_bound keeps its exact legality; the new kind joins the licensed set --
--     the s41/s45 precedent for widening an existing two-way CHECK to a second kind).
--   * validate_entitlement is a NEW trigger member, firing only on kinds/shapes this SAME
--     delta makes representable (entitlement_class_configured) or on PRE-EXISTING kinds
--     (principal_registered, principal_role_bound, the three standing kinds, work_closed,
--     work_depends_on) where it ADDS a refusal that did not exist before -- new-refusal-only,
--     the exact shape s40/s41/s43/s45''s own set_actor/validate_independence/
--     validate_supersession_target re-issues each carry (a write that succeeded before this
--     delta''s birth chain applies is not touched -- deltas are never applied to an existing
--     world, runs-are-strictly-linear; on any FUTURE world that DOES carry this delta from
--     birth, the birth sequence (Element 10 in bootstrap/new-project.sh) discharges the two new
--     acts BEFORE any other actor could ever observe the gate, so the zero-friction leg is
--     byte-comparable to a pre-delta world''s transcript for every act the birth sequence itself
--     performs afterward).
--   * entitlement_class_roles/entitlement_genesis_principal/
--     principal_authority_chain_reaches_genesis/entitlement_act_class_of are brand-new objects
--     with no pre-existing reader.
--   * compute_row_hash/ledger_current/countersigned_in_force re-issues are s42''s law, self-
--     applied, pure column-list appends (s20 lesson), byte-identical to the s28..s58 precedent.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: every authority-bearing act the kernel accepts (principal registration, role
--     binding, standing lifecycle, milestone closure/supersession, gate-edge supersession,
--     entitlement reconfiguration) is checked at write time against (a) an in-force role
--     binding naming this world''s configured role for the act''s class, when one is configured,
--     and (b) an in-force authority chain, transitive over acts-for relations, rooted at the
--     world''s genesis principal, evaluated fresh at act time, never cached, never stored; a
--     chain link dies PROSPECTIVELY the moment its delegating principal loses active standing,
--     while acts already accepted through it stay credited (I5); every refusal is a committed,
--     journaled write_refused row via the existing s43 boundary, never a second refusal surface.
--   - QUANTIFICATION UNIVERSE:
--       ACT CLASSES gated by conjunct (b), the hardcoded authority-bearing set: exactly six
--         tokens (principal_registered, principal_role_bound, standing_lifecycle,
--         milestone_closure, gate_edge_supersession, entitlement_class_configured) --
--         enumerated once, inside validate_entitlement, never a second copy. Every OTHER kind
--         (the eight-plus s10..s59 kinds this delta does not enumerate) is UNTOUCHED --
--         entitlement_act_class_of returns NULL for all of them, and validate_entitlement
--         returns immediately.
--       ACT CLASSES gated by conjunct (a): whichever tokens entitlement_class_roles currently
--         governs -- POLICY, not kernel vocabulary; the birth sequence''s own default discharge
--         (bootstrap/new-project.sh, this same commit) configures five of the six conjunct-(b)
--         tokens (every one but entitlement_class_configured itself, Element 8''s own note) to
--         role ''authority''; a deployment may configure MORE, FEWER (down to zero, but never
--         the genesis-protecting entitlement_class_configured token, which conjunct (b) guards
--         unconditionally regardless of configuration), or DIFFERENT role names per class by
--         writing fresh entitlement_class_configured rows.
--       KINDS/COLUMNS: entitlement_act_class licensed on exactly one kind (two-way);
--         principal_role_name''s existing CHECK widened to two kinds (both two-way). No other
--         column touched.
--       VIEWS: entitlement_class_roles is new, factors through ledger_current exclusively (no
--         raw `ledger` reference of its own -- classifies clean under gates/
--         ledger_reader_allowlist.py with no allowlist entry needed); ledger_current/
--         countersigned_in_force re-issued (+1 column, Element 3b); no other pre-existing view
--         touched.
--       FUNCTIONS: entitlement_genesis_principal and entitlement_act_class_of are DECLARED
--         history/forensic readers (raw `ledger`, gates/ledger_reader_allowlist.py entries,
--         this same commit) for the load-bearing reasons named at Element 5/7''s own headers;
--         principal_authority_chain_reaches_genesis reads only current-truth views
--         (principal_relations, kernel.principal_standing).
--       TRIGGERS: ONE new BEFORE INSERT member (validate_entitlement); no pre-existing trigger
--         BODY re-issued (validate_supersession_target, set_actor, validate_principal_binding,
--         validate_work_item all stay byte-identical to their s58/s59 head text -- entitlement
--         is a SEPARATE, coexisting concern, not folded into any of them, per Element 8''s own
--         ordering note).
--       ENGINE: the ASP twin ships in this SAME delta (engine/lp/ledger_entitlement.lp, this
--         same commit) -- the chain closure in the ledger_defeat.lp stratification shape,
--         BESIDE in_force/1, never into it; ./judge holds AGREE on this delta''s fixture from
--         birth, per the spec''s own item 2 ("not filed as pairing debt"). entry/6 remains
--         kind-generic (verified unchanged); the new kind flows through as an ordinary entry
--         fact.
--       GATES: kind_shape_manifest_gate (CHAIN += s60, one new MANIFEST row, one widened row),
--         ledger_reader_allowlist (CHAIN += s60, three new declared entries), hash_coverage_gate
--         (green on this head with the 88-column re-issue, red on a no-re-issue scratch),
--         fixture_census (this delta''s seen-red registered) -- all in this same commit.
--   - DENOMINATION: entitlement in in-force EVENTS (role bindings, acts-for relations,
--     entitlement_class_configured rows), computed fresh at act time, never stored, never
--     cached; act-class identity in a kernel-COMPUTED string vocabulary (entitlement_act_class_of),
--     never a writer assertion; role/act-class NAMES free text (the s36/s41 ratified idiom); the
--     authority root in a single immutable historical fact (the first-ever principal_registered
--     row''s subject), never a mutable pointer. No bound is a bare round literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape (this delta only ADDS refusals -- one new kind, one new column, one widened existing
-- CHECK, one new trigger member, read-only new views/functions; no existing CHECK narrowed, no
-- existing trigger body re-issued, no existing grant revoked) -- but per the spec''s own §1
-- header ("scratch-schema witness on both polarities... admits it to the birth chain without a
-- per-delta maintainer question") this delta is EXPLICITLY named as riding the 2026-07-09 class
-- rule, not routed for a separate maintainer ratification question -- stated here for the
-- record, matching s36''s own "routed... rather than claimed under that class" disclosure
-- convention in reverse (s36 opted OUT of the class despite qualifying shape; this delta is
-- SPEC-DIRECTED to ride it).
--
-- LIMITS (pre-registered):
--   - No de-configuration path for entitlement_class_configured in v1 (Element 1) -- only fresh
--     assertion and rotation-to-a-different-role; removing a class''s role requirement entirely
--     is not representable, deliberately (it would be a RELAXING mechanism, out of the
--     fail-safe-additive class this delta ships under).
--   - No construction-time cycle refusal exists for acts-for relations (unlike work''s
--     blocks-start/blocks-close subgraphs) -- a delegation cycle that never reaches genesis is
--     FAIL-SAFE (every act through it refused, depth-capped at 10000), never a bypass; named as
--     a limit, not built as a feature, since nothing in the spec asks for it and the failure
--     mode is refusal, not permission.
--   - Trigger/CHECK refusals bind the granted role''s ordinary INSERT path only; the schema-
--     owner/superuser bypass stands (the standing s26..s59 disclosed bound).
--   - Conjunct (a)''s role-token matching is exact string equality on entitlement_act_class_of''s
--     OWN kernel-computed vocabulary -- a deployment cannot invent a new configurable act class
--     without a future delta widening that function (unlike role NAMES, which stay genuinely
--     free text).
--   - The milestone_closure/gate_edge_supersession detection reads work_edge_blocks_start joined
--     to ledger_current -- a blocks-start edge retracted in the SAME transaction as the
--     dependent close it once qualified is read as already-gone (current-truth, matching every
--     other in-force edge reading in this lineage; no special same-transaction ordering
--     guarantee beyond Postgres'' own statement-level MVCC visibility).
--   - Attention points 1 and 2 (the default role name, and the narrower milestone-closure
--     reading) are PROVISIONAL per the commission''s own framing -- policy the maintainer may
--     re-rule without touching this file''s CHECKs/triggers (only the birth-sequence discharge
--     and/or a fresh entitlement_class_configured row would need to change).
--   - The entitlement_class_configured self-protection (this file''s own header-surfaced
--     addition) is NOT in the spec''s own §1.1b enumerated set -- a divergence, surfaced, never
--     silently folded in; strictly additive (narrows who may reconfigure entitlement, relaxes
--     nothing), so it stays inside the fail-safe-additive class regardless.
--   - In a solo world, every entitlement fact is written by machinery the one operator controls
--     -- complete and attributed, not adversarially independent (s17''s own honesty, inherited).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s59):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s60val -v kern=s60val_kernel -v role=s60val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s27-chain-high-water.sql \
--        -f s28-work-parent-edge.sql -f s29-obligation-item-key-and-typed-close.sql \
--        -f s30-typed-dependency-edges.sql -f s31-supersession-uniform-retraction.sql \
--        -f s32-edge-views-single-home.sql -f s33-composite-discharge.sql \
--        -f s34-computed-grade-refusal.sql -f s35-validation-decomposition.sql \
--        -f s36-decision-grade.sql -f s37-violation-disposition.sql \
--        -f s38-bookkeeping-close.sql -f s39-blocks-start.sql \
--        -f s40-principal-identity-events.sql -f s41-principal-bindings-and-relations.sql \
--        -f s42-row-hash-full-coverage.sql -f s43-typed-verdict-write-boundary.sql \
--        -f s44-model-identity-attestation.sql -f s45-standing-lifecycle.sql \
--        -f s46-credited-views.sql -f s47-claim-on-closed-refusal.sql \
--        -f s48-review-witness-existence.sql -f s49-journaler-overflow-guard.sql \
--        -f s50-defeat-input-raw-domain.sql -f s51-artifact-store.sql \
--        -f s52-artifact-witness-check.sql -f s53-belief-substrate.sql \
--        -f s54-belief-views.sql -f s55-dispatch-grain-independence.sql \
--        -f s56-reservation-residue.sql -f s57-obligation-revocation-event.sql \
--        -f s58-missive-substrate.sql -f s59-missive-views.sql \
--        -f s60-entitlement-enforcement.sql
--     (genesis seed per s26; register the write-boundary principal and discharge the s40/s43
--     birth sequence, THEN the two new s60 birth acts -- bind genesis to role ''authority'',
--     then configure the default act-class map -- before exercising any other act, or conjunct
--     (a) reads every act class as unconfigured, which is fail-safe [vacuous conjunct (a),
--     conjunct (b) still enforced] but not the intended zero-friction posture.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world''s
--   birth chain via bootstrap/new-project.sh''s LINEAGE_CHAIN (this same commit's Element 10
--   surfaces the s58/s59 wiring gap named at this file''s own PREREQUISITE section; wiring s60
--   itself into that chain is the maintainer''s own integration act, matching s28/s31''s own
--   "deliberately NOT taken here" precedent for a delta whose scaffold prose this same commit
--   nonetheless prepares). Authored and scratch-witnessed on scratch schema pairs in the TOY db
--   only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP/CREATE TRIGGER).
-- ============================================================================================
