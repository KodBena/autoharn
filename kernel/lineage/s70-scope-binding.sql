-- s70 SCOPE BINDING (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b/§1c, ratified
-- basis: ledger row 639 -- "Ratified AC spec mechanism 1b/1c: the s70 scope-binding kernel
-- delta, authored and scratch-witnessed, entering NO chain until the next birth"). FAIL-SAFE-
-- ADDITIVE (CLAUDE.md 2026-07-09 class rule, the SAME class s60/s61/s62/s64/s69 rode): this
-- delta ONLY ADDS refusals and read-only derived surface -- one new kind
-- (principal_scope_bound), three new nullable columns (scope_surfaces, scope_exclusions,
-- scope_disclosure_mode), one new value-shape function (scope_exclusions_shape_ok, called ONLY
-- from this delta's own new CHECK), two widened existing CHECKs (principal_subject_kind_shape,
-- principal_binding_active_kind_shape -- additive, every pre-existing kind's licensing
-- unchanged), three widened existing functions (entitlement_act_class_of,
-- entitlement_act_class_of_target, entitlement_enforce_class -- each gains ONE new branch/token,
-- no existing branch's text edited), one re-issued compute_row_hash/ledger_current/
-- countersigned_in_force (s42's law, self-applied, +3 columns), and one new derived view
-- (principal_scopes); nothing existing is relaxed, no existing CHECK narrowed, no existing
-- trigger's pre-existing branch edited, no existing grant revoked, validate_entitlement's OWN
-- trigger body is NOT re-issued at all (unchanged -- see WHY section below for why this delta
-- needs no new call site there). Sonnet-built per the standing delegation contract, from the
-- ratified spec above.
--
-- THIS DELTA IS AUTHORED AND SCRATCH-WITNESSED ONLY; applying it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s69 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of any frozen sNN record (ADR-0005 Rule 8) and NOT
-- a second copy of any existing mechanism (ADR-0012 P1): scope binding extends s60's OWN
-- authority-bearing act-class machinery (entitlement_act_class_of/entitlement_act_class_of_
-- target/entitlement_enforce_class) exactly as s62 (delegation_lifecycle, the seventh token) and
-- s64 (independent_verification_delegation, the eighth) already extended it -- this delta mints
-- the NINTH token, scope_binding, by the identical widen-in-place mechanism, never a parallel
-- entitlement pipeline. The derived view follows s41 D-5's OWN "current in-force X per
-- principal, supersession-aware, security_invoker, factored through ledger_current" shape
-- (principal_role_bindings is the literal template, quoted at Element 5's own header).
--
-- PREREQUISITE: this delta REQUIRES s69 (kernel/lineage/s69-role-coherence-refusals.sql) applied
-- first -- it re-issues compute_row_hash/ledger_current/countersigned_in_force in the EXACT
-- 101-column shape s68 left them (s69 added no ledger column, verified: its own HISTORY section
-- states "zero columns, zero kinds, zero views added or altered"), and re-issues
-- entitlement_act_class_of/entitlement_act_class_of_target/entitlement_enforce_class in the
-- EXACT shape s64 left them (s65/s66/s67/s68/s69 none of them touch these three names -- grepped
-- in full before authoring this delta: only s60/s62/s64 ever CREATE OR REPLACE any of the three).
-- It ALSO re-issues (widens) principal_subject_kind_shape in the exact eight-kind shape s41 left
-- it (no file since s41 touches this constraint -- grepped) and principal_binding_active_
-- kind_shape in the exact six-kind shape s45 left it (no file since s45 touches this constraint
-- -- grepped; s61's own header mentions "principal_binding_active_kind_shape's sibling" but never
-- itself re-issues that constraint, confirmed by grep for its own ADD CONSTRAINT statement).
-- Applying this file on a kernel that does not already carry those objects in their s69-head
-- shape fails loudly at ALTER TABLE / CREATE OR REPLACE FUNCTION time (a column, relation, or
-- prior CHECK definition referenced or DROP-targeted does not exist/match), the correct,
-- disclosed failure mode, matching every prior PREREQUISITE precedent. THE HEAD-BODY RULE (s45's
-- own standing instruction, carried here verbatim): at this delta's authoring the lineage head
-- is s69 (kernel/lineage/'s own directory listing, confirmed by the builder before authoring).
-- This file's re-issued bodies are quoted, verified, against their true immediately-prior
-- re-issue's own text (s64 for the three entitlement functions and for compute_row_hash's true
-- immediately-prior re-issue see below; s68 for compute_row_hash specifically, since s64 does not
-- carry the two s65/s67/s68 columns) -- each ELEMENT below carries its own
-- `-- prior-body-sha256:` line (gates/lineage_reissue_lineage.py, MIN_N_HASH-covered).
--
-- WHY (the two concepts the medium adds, spec §1, read literally against this delta's own
-- scope -- §1b/§1c ONLY; §1a, read-path identity resolution + read journaling, is a SERVING-layer
-- mechanism, explicitly NOT a kernel delta, spec's own roster item 2; the boundary-side
-- enforcement filter, spec §2's first bullet, is likewise a serving-layer follow-on this delta
-- does NOT build -- flagged loudly below as the engine/serving-side follow-on the spec's own
-- roster already names, not silently assumed done):
--
--   §1b SCOPES AS FIRST-CLASS, LEDGERED OBJECTS. A scope is a named, ledgered visibility
--   predicate bound to a principal: a set of GRANTED READ SURFACES (scope_surfaces, free text --
--   the registry's own closed vocabulary of view/route names lives in the SERVING layer, not the
--   kernel; the kernel stores and matches strings, exactly the s36/s41 graded-token precedent for
--   "a deployment configures the vocabulary, the kernel enforces only shape") plus an OPTIONAL
--   row-level EXCLUSION FAMILY (scope_exclusions -- a jsonb array of {family, value} objects,
--   family in the spec's own closed four-member vocabulary: kind-class, thread, work-item-
--   lineage, rows -- denominated in the ledger's OWN vocabulary per the spec's denomination
--   check, §4, never row-id ARITHMETIC: the "rows" family names an EXPLICIT set of ids, a plain
--   assertion, not an offset/threshold computation over them). ONE new kind,
--   principal_scope_bound (the entitlement machinery's NINTH authority-bearing token -- see
--   Element 6/7/8's own header for the join-list this file's own header already names), ONE
--   derived view, principal_scopes (Element 5), and THE FAIL-SAFE DEFAULT, stated here verbatim
--   from the spec's own §1b text: **a principal with no bound scope holds the open scope** --
--   an unarmed world is byte-identical. This is structural, not merely documented: principal_
--   scopes (like every s41 D-5 sibling view) returns ZERO rows for a principal with no fresh,
--   active principal_scope_bound row -- there is no "default-deny" row to author, no migration
--   to backfill, and no boundary-side consumer of this view can distinguish "never armed" from
--   "explicitly armed with the universal scope" without this delta minting a SEPARATE marker for
--   the latter, which it deliberately does NOT (an absent row IS the fail-safe default, exactly
--   as s60's own entitlement_class_roles reads an unconfigured act class as vacuously satisfied
--   rather than needing an explicit "unconfigured" row).
--
--   §1c DISCLOSURE TIERS. scope_disclosure_mode is a CHECK-constrained closed vocabulary of
--   THREE values -- marked | hash_stub | full -- ALL THREE representable from birth (Element 2's
--   own CHECK licenses all three equally), matching the spec's own text: "only the first is
--   built in this spec's own build" refers to the SERVING-layer consumer (which tiers a boundary
--   filter actually HONORS today), never to the kernel's own storage/vocabulary, which is
--   deliberately NOT narrowed to one value -- narrowing the CHECK to admit only 'marked' today and
--   widening it later would itself be the exact "narrow the class to the build in view" reflex
--   ADR-0000 Rule 2(a)'s 2026-07-02 amendment warns against, and would ALSO violate the
--   fail-safe-additive class this delta rides (a later CHECK-widening to admit hash_stub/full
--   would be adding legality, not merely adding a refusal -- named here so the choice to build
--   all three now is seen as deliberate, not an oversight the CHECK happens to admit).
--
-- THE ENGINE/SERVING-SIDE FOLLOW-ON, FLAGGED LOUDLY PER THE COMMISSION'S OWN INSTRUCTION (never
-- silently assumed built, never routed around): spec §2's boundary-side filtering ("the conduit
-- applies the resolved principal's scope to every read route") and spec §1a's read-path identity
-- resolution + read journaling are BOTH serving-layer mechanisms this delta does NOT build -- the
-- spec's own roster (§5 items 2 and 3) names them as separate, sequenced steps, and this delta is
-- exactly item 3's kernel half ("`principal_scope_bound` kind + `principal_scopes` view... the
-- delta rides the s70 batch"). A world carrying this kernel delta alone, with no serving-layer
-- consumer of principal_scopes, is BYTE-IDENTICAL in every served response to a world without it
-- (the view exists and can be queried directly via `led`/boundary reads of the view itself, but
-- nothing yet FILTERS a served route by it) -- stated so no reader mistakes "the kernel object
-- exists" for "reads are now scoped," which they are not, yet, by this delta alone. Likewise: no
-- ASP export for scope binding exists in engine/lp/ledger_entitlement.lp or engine/ledger_edb.py
-- (see CLOSURE STATEMENT's ENGINE line and LIMITS below) -- if a differential covering the new
-- view's family is wanted, THAT is the engine-side follow-on flagged loudly here, per the
-- commission's own instruction, rather than hacked in under this delta's own time budget.
--
-- ELEMENT 1 -- ONE NEW KIND: principal_scope_bound (thirty-fourth member, joining s60's six
-- [principal_registered, principal_role_bound, standing_lifecycle (three kinds bundled under one
-- act-class token but each itself a distinct KIND: principal_standing_declared/
-- principal_suspended/principal_revoked), milestone_closure (work_closed), gate_edge_supersession
-- (work_depends_on), entitlement_class_configured], s62's seventh (delegation_lifecycle,
-- principal_relation_asserted/'acts-for', later widened by s64 to also cover 'dispatched-by'),
-- and s64's eighth (independent_verification_delegation, the same kind under
-- delegation_purpose='independent-verification')). Mirrors s41's OWN four binding/relation kinds'
-- shape (D-1: identity fields principal_subject + principal_binding_active, VALUE fields
-- mandatory-never/optional-when-eligible) rather than s41's role/relation IDENTITY-field pattern
-- (principal_role_name, principal_relation) -- a scope binding's three payload columns are all
-- OPTIONAL even when eligible (the task's own text: "additive, nullable"), so this kind reuses
-- ONLY the two existing identity/discriminator columns (principal_subject, principal_binding_
-- active), never a new identity column of its own.
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
     'entitlement_class_configured',
     'commission_signature_verified','principal_key_possession_verified',
     'principal_scope_bound'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s70-scope-binding.sql: widens s61''s thirty-three-member vocabulary by
   principal_scope_bound (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b) -- a
   named, ledgered visibility predicate bound to a principal (granted read surfaces, an optional
   row-level exclusion family, a disclosure-tier mode). Fresh assertion AND rotation/unbind (via
   principal_binding_active=false, the s41 D-1 discriminator) both ride this ONE kind -- no
   separate unbind kind, matching every s41-family binding.';

-- ============================================================================================
-- ELEMENT 2 -- THE THREE NEW COLUMNS + CHECKs. scope_exclusions_shape_ok is created FIRST (a
-- CHECK constraint referencing a function requires the function to already exist). All three
-- columns are OPTIONAL even on an eligible (fresh, active) principal_scope_bound row -- the
-- task's own text, "additive, nullable" -- so each carries the s64 ELIGIBILITY-ONE-WAY idiom
-- (`(kind = 'principal_scope_bound' AND principal_binding_active IS TRUE) OR col IS NULL`),
-- never a two-way mandatory-iff shape: an eligible row may legally bind ZERO of the three (a
-- scope binding that grants nothing and excludes nothing is a degenerate but representable
-- assertion, e.g. a placeholder row a later rotation replaces), and none is licensed on a
-- RETRACTION row (principal_binding_active = false), which restates identity only.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".scope_exclusions_shape_ok(v jsonb)
    RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $fn$
DECLARE
  elem jsonb;
  v_family text;
  v_value jsonb;
  v_keys text[];
BEGIN
  IF jsonb_typeof(v) IS DISTINCT FROM 'array' THEN
    RETURN false;
  END IF;
  FOR elem IN SELECT * FROM jsonb_array_elements(v) LOOP
    IF jsonb_typeof(elem) IS DISTINCT FROM 'object' THEN
      RETURN false;
    END IF;
    SELECT array_agg(k ORDER BY k) INTO v_keys FROM jsonb_object_keys(elem) k;
    IF v_keys IS DISTINCT FROM ARRAY['family', 'value'] THEN
      RETURN false;
    END IF;
    v_family := elem->>'family';
    IF v_family IS NULL
       OR v_family NOT IN ('kind-class', 'thread', 'work-item-lineage', 'rows') THEN
      RETURN false;
    END IF;
    v_value := elem->'value';
    IF v_family = 'rows' THEN
      -- the "explicit rows" family: a plain, enumerated set of ledger row ids -- never an
      -- offset/threshold computed over them (the denomination check, spec §4).
      IF jsonb_typeof(v_value) IS DISTINCT FROM 'array' THEN
        RETURN false;
      END IF;
      IF EXISTS (SELECT 1 FROM jsonb_array_elements(v_value) e2
                 WHERE jsonb_typeof(e2) IS DISTINCT FROM 'number'
                    OR (e2::text) !~ '^[0-9]+$') THEN
        RETURN false;
      END IF;
      IF (SELECT count(*) FROM jsonb_array_elements(v_value)) = 0 THEN
        RETURN false;
      END IF;
    ELSE
      -- kind-class / thread / work-item-lineage: a single non-empty string naming the ledger
      -- vocabulary token (a kind name, a missive thread id, a work-item slug) this exclusion
      -- keys on -- denominated in the ledger's OWN vocabulary, never a row-id proxy.
      IF jsonb_typeof(v_value) IS DISTINCT FROM 'string' OR btrim(v_value #>> '{}') = '' THEN
        RETURN false;
      END IF;
    END IF;
  END LOOP;
  RETURN true;
END; $fn$;

COMMENT ON FUNCTION :"schema".scope_exclusions_shape_ok(jsonb) IS
  'kernel/lineage/s70-scope-binding.sql: well-formedness of a scope_exclusions payload -- a jsonb
   ARRAY of {family, value} objects, family in the spec''s own closed four-member vocabulary
   (kind-class, thread, work-item-lineage, rows), value a non-empty string for the first three or
   a non-empty array of numeral strings for "rows" (an explicit, enumerated row-id SET, never an
   arithmetic bound over them -- design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §4
   denomination check). IMMUTABLE: a pure function of its jsonb argument, no catalog/table read --
   safe inside a CHECK constraint. Called ONLY from scope_exclusions_shape (below); no other
   caller exists.';

ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS scope_surfaces text[];
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS scope_exclusions jsonb;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS scope_disclosure_mode text;

COMMENT ON COLUMN :"schema".ledger.scope_surfaces IS
  'kernel/lineage/s70-scope-binding.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md
   §1b): the GRANTED read-surface names (view/route names from the registry''s own vocabulary) a
   principal_scope_bound row licenses. FREE TEXT ARRAY, no kernel-enforced closed vocabulary --
   which surface names a deployment''s registry actually serves is a SERVING-layer fact, read here
   only by string-equality once a boundary filter consumes this column (the s36/s41 graded-token
   precedent). NULL/absent = this binding grants no surfaces of its own (still additive: a
   principal''s EFFECTIVE surface set, if any consumer computes one, is a serving-layer concern
   outside this delta''s own scope). Optional even on an eligible row (Element 2''s own header).';
COMMENT ON COLUMN :"schema".ledger.scope_exclusions IS
  'kernel/lineage/s70-scope-binding.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md
   §1b): the row-level EXCLUSION family this scope binding carries -- a jsonb array of
   {family, value} objects, family in {kind-class, thread, work-item-lineage, rows}, shape-CHECKed
   by scope_exclusions_shape_ok (Element 2). Denominated in the ledger''s own vocabulary (kinds,
   threads, work-item lineage, or an explicit row-id SET), never row-id arithmetic or byte
   offsets (spec §4 denomination check). NULL/absent = no exclusions (the binding grants its
   surfaces unconditionally). Optional even on an eligible row.';
COMMENT ON COLUMN :"schema".ledger.scope_disclosure_mode IS
  'kernel/lineage/s70-scope-binding.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md
   §1c): the disclosure tier a scoped-out row is withheld under -- marked (existence + typed
   redaction marker, full client-side chain verification -- the tier this spec''s own build
   actually SERVES today) | hash_stub (existence + row_hash visible, content withheld) | full (the
   row does not cross at all). ALL THREE representable from birth (this delta''s own header
   explains why the CHECK is not narrowed to ''marked'' alone) -- which tiers a boundary filter
   actually HONORS is a serving-layer fact, outside this delta''s own scope. NULL/absent on a
   binding that carries no explicit tier -- a serving-layer consumer''s own default (this delta
   does not pick one) is named as a LIMIT below, not silently assumed to be ''marked''.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS scope_surfaces_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT scope_surfaces_kind_shape CHECK (
    (kind = 'principal_scope_bound' AND principal_binding_active IS TRUE)
    OR scope_surfaces IS NULL);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS scope_exclusions_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT scope_exclusions_kind_shape CHECK (
    (kind = 'principal_scope_bound' AND principal_binding_active IS TRUE)
    OR scope_exclusions IS NULL);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS scope_disclosure_mode_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT scope_disclosure_mode_kind_shape CHECK (
    (kind = 'principal_scope_bound' AND principal_binding_active IS TRUE)
    OR scope_disclosure_mode IS NULL);

-- value/structural CHECKs (no kind test -- ordinary business-rule CHECKs, out of the kind-shape
-- manifest gate's scope by its classifier's own first test, the s41/s64 precedent for their own
-- sibling value CHECKs):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS scope_surfaces_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT scope_surfaces_nonempty CHECK (
    scope_surfaces IS NULL OR array_length(scope_surfaces, 1) > 0);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS scope_disclosure_mode_vocabulary;
ALTER TABLE :"schema".ledger ADD CONSTRAINT scope_disclosure_mode_vocabulary CHECK (
    scope_disclosure_mode IS NULL
    OR scope_disclosure_mode IN ('marked', 'hash_stub', 'full'));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS scope_exclusions_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT scope_exclusions_shape CHECK (
    scope_exclusions IS NULL OR :"schema".scope_exclusions_shape_ok(scope_exclusions));

-- principal_subject: ONE home (s40/s41), re-issued wider -- the NINTH principal_* kind joins the
-- eight s41 left it (identical widen-in-place idiom every prior principal_* kind addition used).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_subject_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_subject_kind_shape CHECK (
    (kind IN ('principal_registered','principal_suspended','principal_revoked',
              'principal_standing_declared',
              'principal_relation_asserted','principal_role_bound','principal_key_bound',
              'principal_competence_granted',
              'principal_scope_bound')) = (principal_subject IS NOT NULL));

COMMENT ON COLUMN :"schema".ledger.principal_subject IS
  'The principal an identity/binding event is ABOUT (distinct from actor). Mandatory on exactly
   NINE kinds as of s70 (kernel/lineage/s70-scope-binding.sql widens s41''s eight-kind licensing
   by principal_scope_bound -- WHO this scope binding governs), forbidden elsewhere. ONE
   constraint, re-issued wider (never a second, patching constraint, ADR-0012 P1).';

-- principal_binding_active: ONE home (s41, widened by s45), re-issued wider -- the SEVENTH
-- licensed kind (principal_scope_bound) joins the six s45 left it.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_binding_active_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_binding_active_kind_shape CHECK (
    (kind IN ('principal_relation_asserted','principal_role_bound','principal_key_bound',
              'principal_competence_granted',
              'principal_standing_declared','principal_suspended',
              'principal_scope_bound'))
    = (principal_binding_active IS NOT NULL));

COMMENT ON CONSTRAINT principal_binding_active_kind_shape ON :"schema".ledger IS
  'kernel/lineage/s70-scope-binding.sql: widens s45''s six-kind licensing of the identity/value
   discriminator to SEVEN -- principal_scope_bound joins the six s45 left it (true = a fresh
   scope assertion, value fields optional per Element 2; false = a retraction/unbind, value
   fields forbidden, supersedes mandatory -- the s41 D-1 shape, unchanged in kind).';

-- ============================================================================================
-- ELEMENT 3 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 104 COLUMNS (the three new
-- columns appended in catalog ordinal order, before the predecessor link; base body = s68's own
-- text, byte-identical above the three appended lines -- s69 does not re-issue this function,
-- verified by grep before authoring this delta).
-- prior-body-sha256: e6b250394b7fdfbf2c31011b3100650e6db4fe3f72d9130e92eaa472656d82a6 (s68-typed-absence-dispositions.sql)
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
      hashfield(r.entitlement_act_class),
      hashfield(r.signature_attests_row::text),
      hashfield(r.signature_grade),
      hashfield(r.signature_symmetry_witness::text),
      hashfield(r.key_binding_possession_ref::text),
      hashfield(r.delegation_redelegate_depth::text),
      hashfield(r.delegation_must_countersign::text),
      hashfield(extract(epoch FROM r.delegation_expiry)::text),
      hashfield(array_to_string(r.delegation_scope_classes, ',')),
      hashfield(r.delegation_purpose),
      hashfield(r.refusal_attempted_kind),
      hashfield(r.refusal_digest_disposition),
      hashfield(r.refusal_attempted_kind_disposition),
      hashfield(r.refusal_attempted_actor_disposition),
      -- s70: the three new columns, appended last before the predecessor link.
      hashfield(array_to_string(r.scope_surfaces, ',')),
      hashfield(r.scope_exclusions::text),
      hashfield(r.scope_disclosure_mode),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 4 -- THE TWO COLUMN-COMPLETE VIEWS, +3 APPENDED (the s20 lesson).
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
       l.entitlement_act_class,
       l.signature_attests_row, l.signature_grade, l.signature_symmetry_witness,
       l.key_binding_possession_ref,
       l.delegation_redelegate_depth, l.delegation_must_countersign, l.delegation_expiry,
       l.delegation_scope_classes, l.delegation_purpose,
       l.refusal_attempted_kind,
       l.refusal_digest_disposition,
       l.refusal_attempted_kind_disposition,
       l.refusal_attempted_actor_disposition,
       l.scope_surfaces, l.scope_exclusions, l.scope_disclosure_mode
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
       l.entitlement_act_class,
       l.signature_attests_row, l.signature_grade, l.signature_symmetry_witness,
       l.key_binding_possession_ref,
       l.delegation_redelegate_depth, l.delegation_must_countersign, l.delegation_expiry,
       l.delegation_scope_classes, l.delegation_purpose,
       l.refusal_attempted_kind,
       l.refusal_digest_disposition,
       l.refusal_attempted_kind_disposition,
       l.refusal_attempted_actor_disposition,
       l.scope_surfaces, l.scope_exclusions, l.scope_disclosure_mode
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 5 -- principal_scopes: THE DERIVED VIEW (security_invoker, ledger_current-factored,
-- filters active=true -- the s41 D-5 withdrawal fix applied one kind over). Literal template,
-- quoted (kernel/lineage/s41-principal-bindings-and-relations.sql lines 636-641):
--   CREATE OR REPLACE VIEW :"schema".principal_role_bindings
--       WITH (security_invoker = true) AS
--   SELECT lc.principal_subject AS subject, lc.principal_role_name AS role_name,
--          lc.actor AS bound_by, lc.ts AS at, lc.id AS row_id
--   FROM   :"schema".ledger_current lc
--   WHERE  lc.kind = 'principal_role_bound' AND lc.principal_binding_active;
-- Supersession-awareness is entirely inherited from ledger_current (already excludes superseded
-- rows) -- this view adds only the kind filter and the active-not-merely-unsuperseded filter,
-- the SAME two predicates every s41 D-5 sibling view uses. "Current in-force scope per
-- principal" falls out for free: each principal_subject's LATEST unsuperseded, active
-- principal_scope_bound row is the only one ledger_current+this WHERE clause can ever return for
-- that subject (s31's uniform-retraction supersession discipline, applied here as everywhere
-- else in this lineage) -- no GROUP BY / window function needed, matching principal_role_
-- bindings' own zero-aggregation shape.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".principal_scopes
    WITH (security_invoker = true) AS
SELECT lc.principal_subject AS subject,
       lc.scope_surfaces, lc.scope_exclusions, lc.scope_disclosure_mode,
       lc.actor AS bound_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_scope_bound' AND lc.principal_binding_active;

COMMENT ON VIEW :"schema".principal_scopes IS
  'kernel/lineage/s70-scope-binding.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md
   §1b): the CURRENT in-force scope per principal (unsuperseded, active) -- mirrors principal_
   role_bindings'' own shape one kind over (kernel/lineage/
   s41-principal-bindings-and-relations.sql D-5). THE FAIL-SAFE DEFAULT: a principal_subject with
   NO row in this view holds the OPEN scope (every surface, no exclusions) -- absence is the
   fail-safe, not an explicit "unrestricted" row this view would otherwise need to author. A
   withdrawal (a superseding row with principal_binding_active=false) drops the subject from this
   view by construction, returning them to the open-scope default -- the SAME "unbind restores
   the fail-safe" shape s41''s own role/relation/key/competence withdrawals already carry.
   RECORDABLE HERE; NOT YET ENFORCED AT ANY BOUNDARY ROUTE (this delta''s own header: the
   serving-layer filter is a named, flagged follow-on, spec §2, not built in this kernel-only
   delta).';

GRANT SELECT ON :"schema".principal_scopes TO :"role";

-- ============================================================================================
-- ELEMENT 6 -- entitlement_act_class_of RE-ISSUED (s64's own body, verified unedited above the
-- one new branch appended last, before the final RETURN NULL). Every existing branch (through
-- the principal_relation_asserted/independent-verification branch) is BYTE-IDENTICAL to s64's
-- text.
-- prior-body-sha256: dfa16283507fdf5ee3df8f96b396ac0762f8ec1fa6a91d016124a9ccdc5cd780 (s64-principal-stamps-delegation-conditions.sql)
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
  IF r.kind = 'principal_relation_asserted' AND r.principal_relation IN ('acts-for', 'dispatched-by') THEN
    IF r.delegation_purpose = 'independent-verification' THEN
      RETURN 'independent_verification_delegation';
    END IF;
    RETURN 'delegation_lifecycle';
  END IF;
  -- s70 (kernel/lineage/s70-scope-binding.sql, design/FABLE-ACCESS-CONTROL-AND-INFORMATION-
  -- FLOW-SPEC.md §1b): a principal_scope_bound row (fresh assertion OR retraction/rotation --
  -- "kind, not fresh-vs-supersedes, decides the class", s60's own uniform treatment, identical to
  -- principal_registered/principal_role_bound above) is its OWN act class, scope_binding -- the
  -- ninth authority-bearing token.
  IF r.kind = 'principal_scope_bound' THEN
    RETURN 'scope_binding';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of(:"schema".ledger) IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (AMENDMENT), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED), kernel/lineage/
   s70-scope-binding.sql (WIDENED: scope_binding, the ninth token): the act-class token a
   CANDIDATE ledger row belongs to by its OWN kind/attributes, or NULL if it belongs to none.
   NINE tokens as of s70.';

-- ============================================================================================
-- ELEMENT 7 -- entitlement_act_class_of_target RE-ISSUED (s64's own body, verified unedited
-- above the one new branch appended last). Symmetric with Element 6 -- a principal_scope_bound
-- row being SUPERSEDED is itself an in-force member of the scope_binding class, closing the SAME
-- cross-kind severance vessel s62 round 2 closed generally for every other protected class (an
-- unclassified candidate kind superseding a live principal_scope_bound row, e.g. to silently
-- revert a principal to the open-scope default, is now itself gated on the scope_binding class
-- via validate_entitlement's existing target-class enforcement, s62 Element 2 -- unchanged by
-- this delta, no re-issue of validate_entitlement needed, see this file's own header WHY note).
-- prior-body-sha256: 4cf8771add62f521c0eaf1d75ad232c9c1b59703b09a85295d73cac291ee25bc (s64-principal-stamps-delegation-conditions.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_act_class_of_target(
    p_kind text, p_edge_type text, p_principal_relation text, p_work_slug text)
    RETURNS text LANGUAGE plpgsql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF p_kind = 'principal_registered' THEN
    RETURN 'principal_registered';
  END IF;
  IF p_kind = 'principal_role_bound' THEN
    RETURN 'principal_role_bound';
  END IF;
  IF p_kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
    RETURN 'standing_lifecycle';
  END IF;
  IF p_kind = 'entitlement_class_configured' THEN
    RETURN 'entitlement_class_configured';
  END IF;
  IF p_kind = 'work_closed' THEN
    IF EXISTS (SELECT 1 FROM work_edge_blocks_start e
               JOIN ledger_current lc ON lc.id = e.edge_row_id
               WHERE e.antecedent_slug = p_work_slug) THEN
      RETURN 'milestone_closure';
    END IF;
    RETURN NULL;
  END IF;
  IF p_kind = 'work_depends_on' AND p_edge_type = 'blocks-start' THEN
    RETURN 'gate_edge_supersession';
  END IF;
  IF p_kind = 'principal_relation_asserted' AND p_principal_relation IN ('acts-for', 'dispatched-by') THEN
    RETURN 'delegation_lifecycle';
  END IF;
  -- s70: a principal_scope_bound TARGET row is, by its own identity, an in-force member of the
  -- scope_binding class -- no further indirection needed (mirrors every sibling branch above:
  -- "is THIS ROW, by its own kind, presently protected", never a second hop through its own
  -- supersedes chain, s62 round 2's own "classify the target as if fresh" rule).
  IF p_kind = 'principal_scope_bound' THEN
    RETURN 'scope_binding';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of_target(text, text, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (base), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED), kernel/lineage/
   s70-scope-binding.sql (WIDENED: scope_binding): the act-class token a row belongs to, judged
   purely from four of its own columns, one hop only. A principal_scope_bound target is now
   protected against the SAME cross-kind severance vessel every other protected class already is.';

-- ============================================================================================
-- ELEMENT 8 -- entitlement_enforce_class RE-ISSUED (s64's own body, verified unedited above the
-- widened authority-bearing set). ONE widening: the authority-bearing set gains the NINTH token,
-- scope_binding -- conjunct (b), unconditional, exactly like every other token (a scope binding
-- IS an authority-bearing act, per the task's own commission: "a scope binding is refused unless
-- the binder passes the entitlement conjuncts -- it IS authority-bearing"). scope_binding is
-- DELIBERATELY LEFT OUT of the default conjunct-(a) role map (no birth-sequence act of this
-- delta's own, mirroring s62's identical choice for delegation_lifecycle, Element 3 of that
-- file) -- conjunct (a) stays vacuous for it by default; a deployment wanting a role requirement
-- on scope-binding acts, not merely a chain requirement, configures it explicitly via a fresh
-- (chain-gated) entitlement_class_configured row, exactly as s62's own text states for its
-- sibling token.
-- prior-body-sha256: bd13ee309255c3292c7ff502f79321b967dfc2eb8432c54269368075a8ae7425 (s64-principal-stamps-delegation-conditions.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_enforce_class(
    p_actor bigint, p_act_class text, p_source text)
    RETURNS void LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_required_role text;
  v_has_role boolean;
  v_authority_bearing boolean;
  v_reaches boolean;
BEGIN
  IF p_act_class IS NULL THEN
    RETURN;
  END IF;

  SELECT role_name INTO v_required_role FROM entitlement_class_roles WHERE act_class = p_act_class;
  IF v_required_role IS NOT NULL THEN
    SELECT EXISTS (SELECT 1 FROM principal_role_bindings prb
                   WHERE prb.subject = p_actor AND prb.role_name = v_required_role)
      INTO v_has_role;
    IF NOT v_has_role THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/s64/s70, factored acceptance predicate conjunct a, %) — act class ''%'' requires an in-force role binding named ''%'' (this world''s configured entitlement map, see entitlement_class_roles); actor % holds no such binding. Remedy: a principal who ALREADY holds the ''%'' role (or genesis-chain authority) binds it to you: ./autoharn led principal bind-role <your-principal-name> "%" (kernel/lineage/s41-principal-bindings-and-relations.sql), then retry this act. See design/USER-RECIPES-FAQ.md''s entitlement-enforcement recipe for the worked example (kernel/lineage/s60-entitlement-enforcement.sql).', p_source, p_act_class, v_required_role, p_actor, v_required_role, v_required_role;
    END IF;
  END IF;

  -- s70: NINE tokens (scope_binding joins the eight s64 left).
  v_authority_bearing := p_act_class IN (
      'principal_registered', 'principal_role_bound', 'standing_lifecycle',
      'milestone_closure', 'gate_edge_supersession', 'entitlement_class_configured',
      'delegation_lifecycle', 'independent_verification_delegation',
      'scope_binding');
  IF v_authority_bearing THEN
    SELECT principal_authority_chain_reaches_genesis_scoped(p_actor, p_act_class) INTO v_reaches;
    IF NOT v_reaches THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/s64/s70, factored acceptance predicate conjunct b, %) — act class ''%'' is authority-bearing (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1.1b; design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.3; design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b for scope_binding); actor %''s authority chain (transitive reachability over in-force acts-for/dispatched-by relations, honoring every hop''s expiry/scope conditions, kernel/lineage/s64-principal-stamps-delegation-conditions.sql) does not reach this world''s genesis principal for this act class. Remedy: this is NOT a write you can perform on yourself — have your DELEGATOR run, on your behalf: ./autoharn led principal relate <delegator-principal-name> acts-for <a-principal-already-chain-connected-to-genesis>, covering you, and (if any upstream edge is scoped) confirm this act class is among that edge''s delegation_scope_classes — or have a severed/expired link repaired (suspension/revocation/expiry severs a chain PROSPECTIVELY only; past accepted acts through that link stay credited, kernel/lineage/s45-standing-lifecycle.sql''s I5 asymmetry).', p_source, p_act_class, p_actor;
    END IF;
  END IF;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_enforce_class(bigint, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (base), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED), kernel/lineage/
   s70-scope-binding.sql (WIDENED: ninth authority-bearing token, scope_binding): the
   two-conjunct acceptance predicate. A no-op when act_class IS NULL.';

-- ============================================================================================
-- ELEMENT 9 -- NO validate_entitlement RE-ISSUE (contrast s62/s64, both of which re-issued it).
-- validate_entitlement (kernel/lineage/s64-principal-stamps-delegation-conditions.sql Element 12,
-- the true lineage head for this trigger -- verified by grep, s65..s69 none of them touch it)
-- ALREADY computes v_act_class := entitlement_act_class_of(NEW) and v_target_act_class via
-- entitlement_act_class_of_target on any supersession target, and ALREADY calls
-- entitlement_enforce_class for BOTH -- every one of Elements 6/7/8's widenings is consumed by
-- that EXISTING, unedited call graph with zero new call sites needed. A principal_scope_bound
-- candidate row is classified 'scope_binding' by Element 6, enforced by the existing
-- `PERFORM entitlement_enforce_class(NEW.actor, v_act_class, ...)` call; a principal_scope_bound
-- SUPERSESSION TARGET is classified 'scope_binding' by Element 7, enforced by the existing
-- `PERFORM entitlement_enforce_class(NEW.actor, v_target_act_class, ...)` call. This delta
-- therefore touches ZERO trigger bodies -- the smallest possible surface for a ninth token,
-- exactly the "coexisting, disjoint-concern member" precedent s60's own header names for
-- validate_* generally, applied here to token-widening rather than trigger-membership.
-- entitlement_enforce_delegation_conditions (s64 Element 11b, the depth-budget/must-countersign
-- conjuncts) is NOT called for scope_binding -- those two conjuncts are s64's own delegation-
-- specific vocabulary (redelegation depth, required countersigner), neither of which a scope
-- binding carries; validate_entitlement's existing THIRD call
-- (`PERFORM entitlement_enforce_delegation_conditions(NEW.actor, v_act_class, ...)`) is itself a
-- no-op for v_act_class = 'scope_binding' (its own Element 11b early-return fires whenever
-- p_act_class IS NULL, and its two conjuncts' own conditions -- `p_act_class = 'delegation_
-- lifecycle'` for conjunct c, `principal_authority_chain_countersigners` for conjunct d, itself
-- keyed on the SAME chain walk Element 8 already performs -- simply do not match a scope-binding
-- act class, so this call falls through harmlessly for it, exactly as it already does for every
-- OTHER non-delegation authority-bearing token (principal_registered, milestone_closure, etc.)
-- today).
-- ============================================================================================

-- ============================================================================================
-- ELEMENT 10 -- GRANTS (belt-and-braces; CREATE OR REPLACE VIEW preserves grants on
-- ledger_current/countersigned_in_force -- s21's own additive-column-order idiom, re-verified
-- here exactly as every prior column-appending delta re-verifies it for its own append).
-- principal_scopes' own GRANT SELECT is issued at Element 5, immediately after its
-- CREATE OR REPLACE -- kept there rather than duplicated here, matching s36/s60's own
-- single-grant-site idiom. No GRANT EXECUTE needed for scope_exclusions_shape_ok: this codebase's
-- own house default (verified: no ALTER DEFAULT PRIVILEGES REVOKE exists in s15/high_watermark_1,
-- and no prior STABLE/IMMUTABLE helper in this lineage carries an explicit GRANT EXECUTE either)
-- leaves EXECUTE granted to PUBLIC on newly created functions, exactly like every other
-- IMMUTABLE/STABLE helper this lineage has ever shipped without one.
-- ============================================================================================

-- ============================================================================================
-- HISTORY: safe -- per-mechanism grounds:
--   * ledger_kind_check re-issued WIDER (additive vocabulary: every pre-existing kind''s legality
--     unchanged; principal_scope_bound is disjoint from the thirty-three existing members and is
--     BORN in this delta -- no pre-existing row can carry it).
--   * THREE new nullable no-DEFAULT columns, kind-scoped (never mandatory even on the eligible
--     kind, Element 2''s own header) by CHECKs that validate vacuously on every pre-existing row
--     (no pre-existing row can carry kind=''principal_scope_bound'', since the kind did not exist
--     before this delta).
--   * scope_exclusions_shape_ok is a BRAND NEW function with no pre-existing reader (called ONLY
--     from this delta''s own new CHECK).
--   * principal_subject_kind_shape / principal_binding_active_kind_shape re-issued WIDER
--     (additive on both sides of each iff: every pre-existing licensed kind keeps its EXACT prior
--     legality; principal_scope_bound joins the licensed set -- the s41/s45/s60/s61 precedent for
--     widening an existing two-way CHECK to one more kind, applied a fifth/sixth time).
--   * entitlement_act_class_of / entitlement_act_class_of_target / entitlement_enforce_class
--     re-issued: each gains exactly ONE new branch/token, appended LAST, with every existing
--     branch''s text byte-identical to s64''s own (Elements 6/7/8''s own `-- prior-body-sha256:`
--     lines bind this mechanically, gates/lineage_reissue_lineage.py CHECK 2) -- new-refusal-only:
--     no candidate or target row classified by any EXISTING branch before this delta changes its
--     classification; the only NEW classification is for a kind (principal_scope_bound) that did
--     not exist before this delta, so no previously-accepted write''s treatment changes.
--   * validate_entitlement is NOT re-issued at all (Element 9''s own header) -- zero trigger
--     bodies touched by this delta, the smallest possible surface for a ninth act-class token.
--   * compute_row_hash/ledger_current/countersigned_in_force re-issues are s42''s law,
--     self-applied, pure column-list appends (s20 lesson), byte-identical to the s28..s69
--     precedent.
--   * principal_scopes is a BRAND NEW view with no pre-existing reader.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: a principal_scope_bound row (fresh assertion, binding one principal to a named
--     visibility predicate -- granted read surfaces, an optional row-level exclusion family
--     denominated in the ledger''s own vocabulary, a disclosure-tier mode -- or a retraction
--     restating identity alone) is accepted only when its writer passes the SAME two-conjunct
--     entitlement predicate every other authority-bearing act class already passes (an in-force
--     role binding when one is configured for scope_binding, and an in-force authority chain
--     rooted at this world''s genesis principal, evaluated fresh, honoring every hop''s
--     expiry/scope delegation conditions); a supersession NAMING a live principal_scope_bound row
--     as its target is gated identically, on the SAME class, regardless of the superseding row''s
--     own kind (the cross-kind severance protection every other protected class already carries,
--     s62 round 2). A principal_subject with NO in-force principal_scope_bound row holds the
--     OPEN scope -- the fail-safe default, structural (an absent row, not an explicit
--     "unrestricted" marker row).
--   - QUANTIFICATION UNIVERSE:
--       ACT CLASSES gated by conjunct (b), the hardcoded authority-bearing set: NINE tokens as of
--         s70 (the six s60 tokens, delegation_lifecycle [s62], independent_verification_
--         delegation [s64], scope_binding [s70]) -- enumerated once, inside
--         entitlement_enforce_class (Element 8), never a second copy. Every OTHER kind is
--         UNTOUCHED by this delta -- entitlement_act_class_of/entitlement_act_class_of_target
--         return NULL for all of them exactly as before, and every existing branch''s TEXT (not
--         merely its observable behavior) is byte-identical to s64''s own, mechanically bound by
--         this file''s own `-- prior-body-sha256:` lines.
--       ACT CLASSES gated by conjunct (a): unchanged POLICY set (whichever tokens
--         entitlement_class_roles currently governs); scope_binding is NOT in the default map
--         (Element 8''s own note, mirroring s62''s identical choice for delegation_lifecycle) --
--         no birth-sequence act of this delta''s own, and no bootstrap/new-project.sh edit at all
--         (this delta''s own commission: "do NOT touch bootstrap/new-project.sh's lineage
--         application, LINEAGE_CHAIN, or any live schema").
--       KINDS/COLUMNS: THREE new columns, licensed ONLY on principal_scope_bound rows with
--         principal_binding_active = true, each OPTIONAL even when eligible (one-way per column,
--         the s64 ELIGIBILITY-ONE-WAY idiom); principal_subject_kind_shape/principal_binding_
--         active_kind_shape widened by ONE kind each (both two-way, additive on both sides). No
--         other column touched.
--       VIEWS: principal_scopes is new, factors through ledger_current exclusively (no raw
--         `ledger` reference of its own -- classifies clean under gates/
--         ledger_reader_allowlist.py with no allowlist entry needed); ledger_current/
--         countersigned_in_force re-issued (+3 columns, Element 4); no other pre-existing view
--         touched.
--       FUNCTIONS: scope_exclusions_shape_ok is a BRAND NEW, IMMUTABLE, no-catalog-read function
--         (declared clean under gates/ledger_reader_allowlist.py, reading only its own jsonb
--         argument); entitlement_act_class_of, entitlement_act_class_of_target,
--         entitlement_enforce_class RE-ISSUED (each widened by exactly one branch/token, no
--         existing branch''s text edited -- see HISTORY above); compute_row_hash re-issued
--         (append-only, s42''s law).
--       TRIGGERS: ZERO touched -- validate_entitlement is NOT re-issued (Element 9). No other
--         trigger reads any column this delta adds.
--       ENGINE: NO ASP twin ships in this delta (see this file''s own header, "THE ENGINE/
--         SERVING-SIDE FOLLOW-ON") -- flagged loudly as a follow-on, per the commission''s own
--         instruction, rather than hacked in; reaches_genesis/1 and reaches_genesis_scoped/2
--         (engine/lp/ledger_entitlement.lp) are GENERIC over act class by construction (s62''s own
--         header: "reaches_genesis/1 was never act-class-specific"; s64''s identical claim for the
--         scoped sibling) -- a ninth token requires NO new predicate for the CHAIN-REACHABILITY
--         question (conjunct b) to remain differential-provable in principle, but this delta does
--         NOT re-run ./judge or extend engine/ledger_edb.py''s export_entitlement to prove it for
--         scope_binding specifically (UNEXERCISED, named below, not silently claimed AGREE).
--       GATES: gates/kind_shape_manifest_gate.py (CHAIN += s69/s70, MANIFEST += three new rows,
--         two existing rows'' kinds tuples widened by one member each), gates/
--         ledger_reader_allowlist.py (CHAIN += s70, zero new ALLOWLIST entries -- every new/
--         re-issued object classifies clean through ledger_current or reads no ledger row at
--         all), gates/fixture_census.py (REGISTRY += s70), gates/lineage_reissue_lineage.py
--         (mechanical, no registry edit -- this file''s own four `-- prior-body-sha256:` lines
--         are what it checks) -- all in this same commit. gates/lineage_chain_coverage.py is
--         DELIBERATELY NOT satisfied by this commit (this delta''s own commission: report the
--         refusal verbatim rather than wiring s70 into bootstrap/new-project.sh's LINEAGE_CHAIN
--         narrative ahead of its actual birth-chain entry) -- see this delta''s own build report
--         for the observed refusal text.
--   - DENOMINATION: entitlement in in-force EVENTS (role bindings, acts-for/dispatched-by
--     relations, entitlement_class_configured rows), computed fresh at act time, never cached
--     (unchanged from s60/s62/s64); scope-exclusion families in the ledger''s OWN vocabulary
--     (kind names, missive threads, work-item slugs, or an explicit enumerated row-id SET) --
--     NEVER row-id arithmetic or byte offsets (spec §4, mechanically checked by
--     scope_exclusions_shape_ok, never merely documented); the disclosure-tier vocabulary a
--     closed three-member CHECK, no bound a bare round literal anywhere in this delta.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape (this delta only ADDS refusals and read-only derived surface -- one new kind, three new
-- nullable columns each optional-even-when-eligible, one new value-shape function used only by
-- its own new CHECK, two widened existing CHECKs that keep every pre-existing kind''s exact prior
-- legality, three widened existing functions each gaining one new branch/token with no existing
-- branch''s text edited, one new derived view; nothing existing is relaxed, no existing CHECK
-- narrowed, no existing trigger touched at all, no existing grant revoked) -- but per the ratified
-- spec's own framing (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md, ratification row
-- 639) this delta is EXPLICITLY named as riding the 2026-07-09 class rule, scratch-witnessed both
-- polarities on this same commit's own fixture, not routed for a separate maintainer ratification
-- question beyond the mechanism-level ratification row 639 already records -- stated here for the
-- record, matching s60/s62/s64/s69's own disclosure convention.
--
-- LIMITS (pre-registered, matching every prior delta's own disclosure convention):
--   - NO SERVING-LAYER ENFORCEMENT SHIPS IN THIS DELTA (this file''s own header, "THE ENGINE/
--     SERVING-SIDE FOLLOW-ON") -- principal_scopes is queryable but nothing yet FILTERS a served
--     boundary route by it; a world carrying this delta alone is byte-identical in every served
--     response to a world without it. Flagged loudly, not silently assumed built.
--   - NO ASP TWIN for the scope_binding act class specifically -- named above (CLOSURE
--     STATEMENT''s ENGINE line) as a possible follow-on, UNEXERCISED (not claimed AGREE); if a
--     differential covering principal_scopes'' own family is wanted, that is the engine-side
--     follow-on this delta flags rather than builds.
--   - NO IDENTITY-CONTINUITY GUARD in validate_supersession_target for principal_scope_bound
--     rows (contrast s45''s guard for the three standing-lifecycle kinds) -- a superseding
--     principal_scope_bound row may legally name a DIFFERENT principal_subject than the row it
--     supersedes; the target-class entitlement check (Element 7/9) still requires the SUPERSEDING
--     actor to be scope_binding-entitled, but does not require subject continuity. This mirrors
--     the SAME disclosed limit s41''s own role/relation/key/competence bindings already carry
--     ("RECORDABLE, NOT GATING [for identity continuity]" -- principal_role_bindings'' own
--     COMMENT) -- named as a LIMIT, not silently accepted as equivalent to a continuity guard;
--     the practical exposure is bounded by the fail-safe direction (severing someone''s scope
--     binding, by construction, returns them to the OPEN scope, never to a MORE restrictive or
--     spoofed one, since the new row''s own principal_subject governs whatever it asserts).
--   - scope_disclosure_mode NULL/absent on an eligible row picks NO implicit default at the
--     kernel layer (Element 2''s own COMMENT ON COLUMN) -- a serving-layer consumer choosing to
--     read absence as "marked" is that consumer''s own documented choice, not this delta''s.
--   - scope_surfaces/scope_exclusions vocabulary (surface names, kind/thread/slug tokens) is
--     free text/free string, kernel-unchecked against any live registry or ledger row set beyond
--     the "rows" family''s own numeral-shape check -- an unrecognized surface name or a
--     nonexistent thread/slug is legal to write, simply never matches anything a future
--     serving-layer consumer looks for (the s36 free-text-policy-token precedent, named
--     explicitly here as the accepted shape, matching every graded-token column this lineage has
--     ever shipped).
--   - The "rows" exclusion family stores an explicit, enumerated SET of row ids with no
--     existence check against `ledger` -- a nonexistent or future row id is legal to write (the
--     same non-verification s48''s own review-witness EXISTENCE check exists precisely to close
--     for a DIFFERENT column; this delta does not extend that check to scope_exclusions, named
--     as a LIMIT, not silently assumed safe).
--   - Trigger/CHECK refusals bind the granted role''s ordinary INSERT path only; the schema-
--     owner/superuser bypass stands (the standing s26..s69 disclosed bound).
--   - In a solo world, every scope-binding fact is written by machinery the one operator
--     controls -- complete and attributed, not adversarially independent (s17''s own honesty,
--     inherited).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s69):
--   VALIDATE (reachable throwaway): apply the FULL s15..s69 chain (see kernel/lineage/
--   s69-role-coherence-refusals.sql's own VALIDATE block for the complete -f list, itself s68's
--   VALIDATE block +1), THEN -f s70-scope-binding.sql (genesis seed per s26; discharge the
--   s40/s43/s60 birth sequence before exercising any scope-binding act, exactly as s60/s62/s64/s69's
--   own VALIDATE notes require).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world's birth chain automatically via bootstrap/new-project.sh's
--   --new-world glob-driven apply list the moment a tree carrying it is scaffolded from; the
--   hand-maintained CLASSIC-scaffold LINEAGE_CHAIN narrative list is a SEPARATE, later maintainer
--   integration act, deliberately NOT taken by this delta (this delta's own commission: "entering
--   NO chain until the next birth"). Authored and scratch-witnessed on scratch schema pairs in
--   the TOY db only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP/CREATE TRIGGER -- no trigger touched by this delta, this
-- clause carried forward for the idiom's own uniform-footer consistency).
-- ============================================================================================
