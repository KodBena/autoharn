-- s64 PRINCIPAL-STAMPS DELEGATION CONDITIONS (design/FABLE-PRINCIPAL-STAMPS-SPEC.md, RATIFIED by
-- the maintainer 2026-07-26, §3 item 1 -- "Kernel (one fail-safe-additive delta): the conditions
-- attribute on delegation edges + conjunction in the existing chain walk; the grant-subset check;
-- the independent-verification act class"). FAIL-SAFE-ADDITIVE (CLAUDE.md 2026-07-09 class rule,
-- the SAME class s60/s62 rode): this delta ONLY ADDS refusals -- five new nullable columns (NO
-- new kind: the spec's own text, "acts-for and dispatched-by -- the s41 vocabulary; NO new
-- relation kind"), one widened existing view (principal_relations, additive column-append), two
-- widened existing CHECKs (none -- see ELEMENT 1, every new CHECK here is BRAND NEW, licensed on
-- rows this delta itself makes representable), four brand-new functions (principal_redelegate_
-- budget, the NEW principal_authority_chain_reaches_genesis_scoped(pid, act_class) -- a
-- DIFFERENTLY-NAMED sibling of the existing principal_authority_chain_reaches_genesis(pid), NOT
-- an overload of the same name: gates/kernel_function_census.py's own key scheme (bare function
-- name, no signature) asserts no kernel function is EVER overloaded in this codebase, and a
-- same-name 2-arg sibling would have been exactly the vessel that gate was never built to key
-- past -- caught empirically running this delta's own gates, before shipping, and fixed by
-- naming rather than by weakening the gate's own assumption (CLAUDE.md's hazard-in-reach
-- corollary). The existing 1-arg function stays BYTE-IDENTICAL, untouched; every existing caller
-- keeps its exact existing meaning,
-- principal_authority_chain_countersigners, entitlement_enforce_delegation_conditions), three
-- re-issued functions (entitlement_act_class_of, entitlement_act_class_of_target,
-- entitlement_enforce_class -- each widened, no existing branch's text edited) and one re-issued
-- trigger body (validate_entitlement -- one new call appended, its two existing calls
-- byte-identical); nothing existing is relaxed, no existing CHECK narrowed, no existing trigger's
-- pre-existing branch edited, no existing grant revoked. Sonnet-built per the standing delegation
-- contract, from the ratified spec.
--
-- SCOPE, READ LITERALLY AGAINST THE COMMISSION: exactly stamps spec §3 item 1 -- kernel only.
-- Hooks (item 2) and dispatch mechanics (item 3, minting the principal + writing the edge +
-- injecting the stamp) are NOT built here, per the commission's own explicit instruction; nothing
-- below assumes either exists. Count/history-shaped conditions are DERIVED over the chain walk,
-- computed FRESH at act time (the s40 "computed at read, never stored" law) -- never a served
-- counter; principal_redelegate_budget (ELEMENT 6) is exactly this: a value recomputed from
-- scratch on every call, never written to a row.
--
-- A HAZARD FOUND IN REACH OF THIS DELTA'S OWN SURFACE, FIXED HERE, NOT ROUTED AROUND (CLAUDE.md's
-- hazard-in-reach corollary -- the mother's-life bar, applied to code met while authoring this
-- very file, not a tangential area): s62's own entitlement_act_class_of/
-- entitlement_act_class_of_target classify a principal_relation_asserted candidate as
-- 'delegation_lifecycle' ONLY when its principal_relation = 'acts-for' -- a 'dispatched-by' row
-- (the OTHER relation this very spec's own §2.3 names as carrying conditions: "delegation edges
-- (acts-for and dispatched-by)") was, before this delta, classified NULL by both functions and
-- therefore COMPLETELY UNGATED by conjunct (b) -- any actor, chained to genesis or not, could
-- assert or supersede a dispatched-by edge with zero entitlement check, and (worse, once this
-- delta's own new columns exist) could attach delegation conditions to a dispatched-by edge that
-- gate nothing, because the edge asserting them was never itself gated. This delta widens BOTH
-- classifier functions' relation test from `= 'acts-for'` to `IN ('acts-for', 'dispatched-by')`
-- (ELEMENT 9/10 below) -- strictly additive (narrows who may write a dispatched-by edge; nothing
-- that was refused before becomes newly accepted), and is why this delta touches
-- entitlement_act_class_of/entitlement_act_class_of_target at all, beyond the independent-
-- verification carve-out. Named loudly, per the commission's own instruction and CLAUDE.md's own
-- text ("you do not route around it because it wasn't the assigned task") -- this IS the assigned
-- task's own surface (delegation-edge classification), not a tangential file.
--
-- PREREQUISITE: this delta REQUIRES s63 (kernel/lineage/s63-supersession-body-restoration.sql)
-- applied first -- it re-issues compute_row_hash/ledger_current/countersigned_in_force in the
-- EXACT 92-column shape s61 left them (s62/s63 added no ledger column), re-issues
-- principal_relations in the exact shape s41 left it, and re-issues entitlement_act_class_of/
-- entitlement_act_class_of_target/entitlement_enforce_class/validate_entitlement in the EXACT
-- shape s62 left them (s63 touches validate_supersession_target only, verified: s63's own header
-- states "no other function is touched"). Applying this file on a pre-s62 kernel fails loudly at
-- CREATE OR REPLACE FUNCTION/VIEW time (a column or relation referenced does not exist), the
-- correct, disclosed failure mode, matching every prior PREREQUISITE precedent. THE HEAD-BODY
-- RULE (s45's own standing instruction, carried here verbatim): at this delta's authoring the
-- lineage head is s63 (kernel/lineage/'s own directory listing, confirmed by the builder before
-- authoring); s58/s59/s60/s61/s62/s63 exist as authored, scratch-witnessed files, none yet wired
-- into bootstrap/new-project.sh's own hand-maintained LINEAGE_CHAIN list (the CLASSIC scaffold
-- path) -- a PRE-EXISTING condition this delta neither creates nor is required to close, named
-- per s60/s61/s62/s63's own identical disclosure. The --new-world scaffold path derives its own
-- apply list LIVE from a kernel/lineage/*.sql glob (bootstrap/new-project.sh's own documented
-- "LINEAGE HEAD, derived live... never hand-typed" mechanism), so this file is picked up there
-- automatically the moment it exists in a tree --new-world scaffolds from -- the mechanism this
-- delta's own witnessing and gates/kernel_function_census.py --bank both rely on. This file's
-- re-issued bodies are quoted, verified, against the s62 head text (entitlement_act_class_of/
-- entitlement_act_class_of_target/entitlement_enforce_class/validate_entitlement) and the s41
-- head text (principal_relations) and the s61 head text (compute_row_hash/ledger_current/
-- countersigned_in_force).
--
-- WHY, THE THREE MECHANISMS (operator-side prose):
--
-- (1) CONDITIONS ON DELEGATION EDGES (spec §2.3): a principal_relation_asserted row with relation
-- acts-for/dispatched-by, on a FRESH (rotating) assertion (principal_binding_active = true --
-- never a retraction: conditions are VALUE-shaped, the s41 D-1 identity/value split applied to a
-- fifth kind's own fresh-only fields, mirroring the s41 competence grant's own band/basis
-- mandatory-iff-active shape), may carry: delegation_redelegate_depth (no-redelegate is the
-- degenerate depth=0 case, "no-redelegate / depth-N" read as ONE integer-valued caveat, per the
-- spec's own single bullet naming both), delegation_must_countersign (a principal id -- "binds
-- via s61 signature-verified rows", ELEMENT 12 below is where this is actually checked, against
-- s61's signed_commissions), delegation_expiry (a validity window's upper bound), and
-- delegation_scope_classes (restriction to named act classes -- the spec's own "or worlds" half
-- is NOT built: a kernel schema/world IS the chain-walk's own boundary already -- there is no
-- cross-world chain to scope within a single schema's own delta, named as a LIMIT below, not
-- silently dropped). delegation_purpose is the FIFTH column, the independent-verification
-- carve-out's own typed vocabulary (mechanism 3, below).
--
-- (2) CONJUNCTION IN THE EXISTING CHAIN WALK (spec §2.2/§3 item 1 "grant-subset monotonicity"):
-- a NEW, DIFFERENTLY-NAMED SIBLING function,
-- principal_authority_chain_reaches_genesis_scoped(pid, act_class) (ELEMENT 7, never an overload
-- of the same name -- this file's own header note explains why), walks the SAME acts-for/
-- dispatched-by chain the existing 1-arg function already walks, but ALSO
-- requires, at EVERY hop: the edge is not expired (delegation_expiry IS NULL OR in the future) AND
-- (the edge is unscoped OR act_class is named in its scope) -- "refuses any act outside the
-- intersection of every edge's grant and conditions along the path" (spec §2.2, verbatim):
-- conjunction along a recursive walk is EXACTLY an intersection, by construction, never an audit.
-- On any edge carrying no conditions at all (every edge that predates this delta, since the five
-- new columns are all NULL by construction on any pre-existing row), the 2-arg walk agrees with
-- the 1-arg walk on every input -- vacuous conjunction, the new-refusal-only shape s62's own
-- round-2 widening already established as fail-safe-additive-compatible. entitlement_enforce_class
-- (ELEMENT 10) is re-issued to call the new sibling function in place of the 1-arg one it used to call --
-- the ONLY behavioral change for a world with no delegation conditions set anywhere is none at
-- all; the 1-arg function itself is NEVER re-issued, staying available, byte-identical, for any
-- other caller.
--
-- (3) THE INDEPENDENT-VERIFICATION ACT CLASS (spec §2.3 carve-out, row 1420): a fresh
-- acts-for/dispatched-by assertion whose delegation_purpose = 'independent-verification' (closed
-- vocabulary, ELEMENT 1) classifies as an EIGHTH act-class token, independent_verification_
-- delegation (ELEMENT 9), rather than delegation_lifecycle -- still authority-bearing (conjunct b:
-- the writer must still chain-reach genesis; this delta mints no free write for anyone), but
-- EXEMPT BY TYPE from the no-redelegate/depth-budget conjunct (ELEMENT 11/12), which fires ONLY
-- when the candidate's own act class is EXACTLY 'delegation_lifecycle'. This closes the row-1420
-- deadlock the spec names: a leaf stamped no-redelegate (depth 0) that is ALSO mandated to obtain
-- independent verification (an attestation B round, a fresh-context review, a countersign) would
-- otherwise be refused for "re-delegating" the moment it dispatches the independent verifier;
-- marking that specific dispatch's own purpose exempts it from the depth conjunct while leaving
-- every OTHER conjunct (writer-chains-to-genesis, scope, expiry, countersign) fully in force.
--
-- ELEMENT 1 -- FIVE NEW COLUMNS (NO new kind -- spec's own text, verbatim). Licensed ONLY on a
-- FRESH principal_relation_asserted row naming relation acts-for or dispatched-by
-- (principal_binding_active IS TRUE) -- forbidden on a retraction (principal_binding_active =
-- false or NULL) and on every other kind/relation, mirroring the s41 D-1 identity/value split
-- (VALUE fields, mandatory-never, optional-when-eligible -- none of the five is MANDATORY even
-- on an eligible row, matching signature_symmetry_witness's "licensed but optional" shape, s61
-- Element 2, rather than the identity-field "mandatory whenever eligible" shape s41's own
-- principal_relation/principal_object carry).
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

ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS delegation_redelegate_depth integer;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS delegation_must_countersign bigint
    REFERENCES :"kern".principal(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS delegation_expiry timestamptz;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS delegation_scope_classes text[];
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS delegation_purpose text;

COMMENT ON COLUMN :"schema".ledger.delegation_redelegate_depth IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: how many FURTHER hops of
   re-delegation this edge''s delegate may perform -- 0 = no-redelegate (the degenerate case,
   design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.3), N>0 = up to N further hops, NULL = unrestricted.
   DERIVED-not-stored budget consumer: principal_redelegate_budget() (ELEMENT 6), never a served
   counter.';
COMMENT ON COLUMN :"schema".ledger.delegation_must_countersign IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: the principal id whose s61
   signature-verified attestation must ground any act relying on this edge (spec §2.3
   "must-countersign... binds via s61 signature-verified rows"). Consulted via
   principal_authority_chain_countersigners() (ELEMENT 8) and enforced in
   entitlement_enforce_delegation_conditions (ELEMENT 11).';
COMMENT ON COLUMN :"schema".ledger.delegation_expiry IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: the validity window''s upper
   bound (spec §2.3 "expiry / scope") -- an edge past its expiry is read as not-currently-usable
   by the principal_authority_chain_reaches_genesis_scoped(pid, act_class) walk (ELEMENT 7) and by
   the budget/countersign walks (ELEMENTS 6/8), exactly like a suspended delegate (I5 asymmetry:
   the chain link dies PROSPECTIVELY, nothing already accepted through it is retroactively
   altered).';
COMMENT ON COLUMN :"schema".ledger.delegation_scope_classes IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: restriction to named act-class
   tokens (entitlement_act_class_of''s own kernel-computed vocabulary, spec §2.3 "expiry / scope")
   -- NULL = unrestricted (backs every act class); non-NULL = backs ONLY the named classes.
   Deliberately does NOT restrict by "world" (the spec''s own second scope axis): a kernel
   schema/world IS the chain walk''s own boundary already -- there is no cross-world chain for a
   single schema''s delta to scope within (named as a LIMIT, not silently dropped).';
COMMENT ON COLUMN :"schema".ledger.delegation_purpose IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: the independent-verification
   carve-out''s own typed vocabulary (spec §2.3 carve-out, row 1420) -- NULL (ordinary delegation)
   or ''independent-verification'' (attestation B rounds, fresh-context reviews, countersigning
   itself: their own act class, independent_verification_delegation, EXEMPT BY TYPE from the
   no-redelegate/depth conjunct, ELEMENT 9/11). Closed two-member vocabulary (NULL or the one
   reserved string), CHECKed below.';

-- eligibility test, repeated per-column (matching this lineage''s own per-column kind-shape idiom
-- rather than one combined multi-column CHECK -- s41 D-2''s own convention, one CHECK per field):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_redelegate_depth_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_redelegate_depth_kind_shape CHECK (
    (kind = 'principal_relation_asserted' AND principal_relation IN ('acts-for', 'dispatched-by')
     AND principal_binding_active IS TRUE)
    OR delegation_redelegate_depth IS NULL);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_must_countersign_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_must_countersign_kind_shape CHECK (
    (kind = 'principal_relation_asserted' AND principal_relation IN ('acts-for', 'dispatched-by')
     AND principal_binding_active IS TRUE)
    OR delegation_must_countersign IS NULL);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_expiry_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_expiry_kind_shape CHECK (
    (kind = 'principal_relation_asserted' AND principal_relation IN ('acts-for', 'dispatched-by')
     AND principal_binding_active IS TRUE)
    OR delegation_expiry IS NULL);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_scope_classes_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_scope_classes_kind_shape CHECK (
    (kind = 'principal_relation_asserted' AND principal_relation IN ('acts-for', 'dispatched-by')
     AND principal_binding_active IS TRUE)
    OR delegation_scope_classes IS NULL);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_purpose_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_purpose_kind_shape CHECK (
    (kind = 'principal_relation_asserted' AND principal_relation IN ('acts-for', 'dispatched-by')
     AND principal_binding_active IS TRUE)
    OR delegation_purpose IS NULL);

-- value CHECKs (ordinary business-rule CHECKs, no kind test -- outside the kind-shape manifest
-- gate''s own classifier by its first test, matching s41''s identical convention for its own
-- value CHECKs):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_redelegate_depth_nonneg;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_redelegate_depth_nonneg CHECK (
    delegation_redelegate_depth IS NULL OR delegation_redelegate_depth >= 0);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_scope_classes_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_scope_classes_nonempty CHECK (
    delegation_scope_classes IS NULL OR array_length(delegation_scope_classes, 1) > 0);

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS delegation_purpose_vocabulary;
ALTER TABLE :"schema".ledger ADD CONSTRAINT delegation_purpose_vocabulary CHECK (
    delegation_purpose IS NULL OR delegation_purpose = 'independent-verification');

-- ============================================================================================
-- ELEMENT 2 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 97 COLUMNS (the five new
-- columns appended in serialization order, before the predecessor link; base body = s61's own
-- text, verified unedited by s62/s63, neither of which touches this function).
-- prior-body-sha256: ca23b1c3fe09f4462eadccda877ce071dbbffbdbd2432301a117c13d991cbb8d (s61-signature-symmetry-and-key-binding.sql)
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
      -- s64: the five new columns, appended last before the predecessor link.
      hashfield(r.delegation_redelegate_depth::text),
      hashfield(r.delegation_must_countersign::text),
      hashfield(extract(epoch FROM r.delegation_expiry)::text),
      hashfield(array_to_string(r.delegation_scope_classes, ',')),
      hashfield(r.delegation_purpose),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 3 -- THE TWO COLUMN-COMPLETE VIEWS, +5 APPENDED (the s20 lesson).
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
       l.delegation_scope_classes, l.delegation_purpose
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
       l.delegation_scope_classes, l.delegation_purpose
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 4 -- principal_relations (s41 D-5) RE-ISSUED, +5 APPENDED (the SAME s20 append lesson
-- applied to a non-ledger_current/countersigned_in_force view for the first time in this
-- lineage -- an equally safe append: every existing consumer selecting explicit columns is
-- unaffected; a hypothetical `SELECT *` consumer sees five more columns, never fewer). Base body
-- = s41's own text (unedited since; grepped, only definer). Needed so the depth-budget and
-- countersign walks (ELEMENTS 6/8) and the 2-arg scoped chain walk (ELEMENT 7) can read the five
-- new columns without a raw `ledger` reference of their own (staying inside
-- gates/ledger_reader_allowlist.py's clean classification, factoring through ledger_current
-- exclusively, exactly as principal_relations already did).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".principal_relations
    WITH (security_invoker = true) AS
SELECT lc.principal_subject AS subject, lc.principal_relation AS relation,
       lc.principal_object AS object, lc.actor AS asserted_by, lc.ts AS at, lc.id AS row_id,
       lc.delegation_redelegate_depth, lc.delegation_must_countersign, lc.delegation_expiry,
       lc.delegation_scope_classes, lc.delegation_purpose
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_relation_asserted' AND lc.principal_binding_active;

COMMENT ON VIEW :"schema".principal_relations IS
  'In-force typed principal<->principal relations (unsuperseded, active). Widened
   kernel/lineage/s64-principal-stamps-delegation-conditions.sql: +5 delegation-condition
   columns, NULL on every same-natural-person/succeeds row and on every acts-for/dispatched-by
   row asserted before this delta (the columns did not exist). A RAW, ORDERED projection: see
   s41 D-5''s own header for the same-natural-person canonical-ordering note, unchanged here.
   kernel/lineage/s41-principal-bindings-and-relations.sql D-5.';

-- ============================================================================================
-- ELEMENT 5 -- GRANT (belt-and-braces; CREATE OR REPLACE VIEW preserves the existing GRANT --
-- s21''s own additive-column-order idiom, re-verified here as every prior column-appending delta
-- already re-verifies it for its own append).
-- ============================================================================================
-- (principal_relations already carries its GRANT SELECT from s41 D-5; CREATE OR REPLACE VIEW
-- preserves it -- no re-grant needed, matching s60/s61''s own single-grant-site idiom.)

-- ============================================================================================
-- ELEMENT 6 -- principal_redelegate_budget(pid): NEW. The no-redelegate/depth-N conjunct's own
-- derivation (spec §2.3), computed FRESH at act time, never stored. B(genesis) = NULL
-- (unrestricted: genesis has no inbound edge to cap it). For a principal P whose OWN inbound edge
-- (subject=P) carries cap c (NULL = unlimited) and whose delegator O has budget B(O): B(P) =
-- LEAST(c, B(O)-1) if both finite, c if B(O) is NULL (unrestricted upstream, so P''s budget is
-- simply its OWN edge''s cap), B(O)-1 if c is NULL (P''s own edge places no cap, so P inherits
-- O''s remaining budget, minus the one hop just spent) -- equivalently (verified by induction,
-- this file''s own header WHY section), for a principal P at chain-position i counting from P''s
-- own edge as i=1, B(P) = MIN over i of (cap_i - (i-1)) across every finite cap_i on the path --
-- a plain running minimum, computed by ONE forward walk (no separate backward pass needed). A
-- principal reachable via MULTIPLE valid delegation paths takes the MOST PERMISSIVE (MAX) of
-- their per-path budgets (mirroring principal_authority_chain_reaches_genesis''s OWN
-- any-path-suffices existential -- an actor invokes whichever path backs the act, so the best
-- available path governs, never the worst). An edge that is EXPIRED (delegation_expiry in the
-- past) or whose delegating principal is not presently ''active'' is skipped exactly like
-- principal_authority_chain_reaches_genesis''s own hop test (I5 asymmetry: a chain link dies
-- PROSPECTIVELY). Depth-capped at 10000 (the s39/s60 shape), matching every recursive walk in
-- this lineage.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".principal_redelegate_budget(pid bigint)
    RETURNS integer LANGUAGE plpgsql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_genesis bigint;
  v_budget integer;
  v_sentinel constant integer := 2000000000;  -- "unrestricted", collapsed back to NULL at return.
BEGIN
  v_genesis := entitlement_genesis_principal();
  IF v_genesis IS NULL OR pid = v_genesis THEN
    RETURN NULL;  -- genesis (or a pre-genesis world) has no inbound edge to cap it.
  END IF;
  WITH RECURSIVE chain(cur, hop, running_min) AS (
    SELECT pid, 1, v_sentinel
    UNION ALL
    SELECT pr.object, c.hop + 1,
           LEAST(c.running_min,
                 CASE WHEN pr.delegation_redelegate_depth IS NULL THEN v_sentinel
                      ELSE pr.delegation_redelegate_depth - (c.hop - 1) END)
    FROM chain c
    JOIN principal_relations pr
      ON pr.subject = c.cur AND pr.relation IN ('acts-for', 'dispatched-by')
    WHERE c.hop < 10000
      AND c.cur <> v_genesis
      AND principal_standing(pr.object) = 'active'
      AND (pr.delegation_expiry IS NULL OR pr.delegation_expiry > now())
  )
  SELECT MAX(running_min) INTO v_budget FROM chain WHERE cur = v_genesis;
  IF v_budget IS NULL OR v_budget >= v_sentinel THEN
    RETURN NULL;
  END IF;
  RETURN v_budget;
END; $fn$;

COMMENT ON FUNCTION :"schema".principal_redelegate_budget(bigint) IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: how many further hops of
   re-delegation pid may perform (NULL = unrestricted), the running-minimum-of-(cap - position)
   derivation over pid''s own acts-for/dispatched-by chain to genesis, MOST-PERMISSIVE-PATH-WINS
   across multiple valid paths, active-delegator-and-non-expired-edge filtered (I5 asymmetry).
   Computed fresh on every call -- never a served counter (spec''s own count/history-shaped-
   conditions rule).';

-- ============================================================================================
-- ELEMENT 7 -- principal_authority_chain_reaches_genesis_scoped(pid, act_class): NEW, a
-- DIFFERENTLY-NAMED sibling function (NOT an overload of principal_authority_chain_reaches_
-- genesis -- see this file's own header note: gates/kernel_function_census.py's bare-name key
-- scheme asserts no kernel function is ever overloaded, so a same-name 2-arg sibling would have
-- been exactly the vessel that gate was never built to key past). The EXISTING 1-arg function
-- (s60 Element 6) is NEVER re-issued by this delta -- byte-identical, untouched, still available
-- to any caller wanting the unscoped question. Mirrors the 1-arg function''s own chain-walk shape
-- exactly (same depth cap, same active-delegator filter, same genesis exception) with ONE
-- addition per hop: the edge must be UNEXPIRED (delegation_expiry IS NULL OR in the future) AND
-- UNSCOPED-OR-SCOPE-INCLUDES-act_class (delegation_scope_classes IS NULL OR act_class =
-- ANY(...)) -- "refuses any act outside the intersection of every edge''s grant and conditions
-- along the path" (spec §2.2, verbatim): a recursive AND across every hop IS an intersection, by
-- construction. On an edge with no conditions (every edge that predates this delta), both new
-- tests are vacuously true -- this function agrees with the 1-arg function on every world that
-- has never used a delegation condition, at every pid, for every act_class.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".principal_authority_chain_reaches_genesis_scoped(
    pid bigint, act_class text)
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
      JOIN principal_relations pr
        ON pr.subject = c.cur AND pr.relation IN ('acts-for', 'dispatched-by')
      WHERE c.depth < 10000
        AND c.cur <> v_genesis
        AND principal_standing(pr.object) = 'active'
        AND (pr.delegation_expiry IS NULL OR pr.delegation_expiry > now())
        AND (pr.delegation_scope_classes IS NULL OR act_class = ANY(pr.delegation_scope_classes))
    )
    SELECT 1 FROM chain WHERE cur = v_genesis
  );
END; $fn$;

COMMENT ON FUNCTION :"schema".principal_authority_chain_reaches_genesis_scoped(bigint, text) IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: the SCOPE/EXPIRY-conjuncted
   sibling of principal_authority_chain_reaches_genesis(bigint) (s60 Element 6, NEVER
   re-issued by this delta) -- a DIFFERENTLY-NAMED sibling function, NOT an overload of the same
   name (ADR-0012 P1 read strictly: this codebase''s own gates/kernel_function_census.py asserts
   no kernel function is ever overloaded -- a same-name 2-arg sibling would have been exactly the
   vessel that gate was never built to key past; named and fixed here, not routed around, per
   CLAUDE.md''s hazard-in-reach corollary) -- whether pid''s authority chain reaches genesis for act_class
   SPECIFICALLY, honoring every hop''s delegation_expiry/delegation_scope_classes conditions
   (design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.2/§2.3). Vacuously agrees with the 1-arg function on
   any chain carrying no conditions.';

-- ============================================================================================
-- ELEMENT 8 -- principal_authority_chain_countersigners(pid, act_class): NEW. Collects the
-- DISTINCT set of principal ids whose s61-verified countersign is required to ground an act of
-- act_class performed via pid''s authority chain (spec §2.3 "must-countersign... binds via s61
-- signature-verified rows") -- every hop on pid''s SCOPE/EXPIRY-conjuncted path to genesis
-- (mirroring ELEMENT 7''s own hop test exactly, so a hop that could not back this act_class at
-- all never contributes a countersign requirement either -- "every hop''s conditions bind the
-- whole suffix of the chain", spec §2.3) whose delegation_must_countersign is non-NULL.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".principal_authority_chain_countersigners(
    pid bigint, act_class text)
    RETURNS bigint[] LANGUAGE plpgsql STABLE
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_genesis bigint;
  v_result bigint[];
BEGIN
  v_genesis := entitlement_genesis_principal();
  IF v_genesis IS NULL THEN
    RETURN ARRAY[]::bigint[];
  END IF;
  WITH RECURSIVE chain(cur, depth) AS (
    SELECT pid, 0
    UNION ALL
    SELECT pr.object, c.depth + 1
    FROM chain c
    JOIN principal_relations pr
      ON pr.subject = c.cur AND pr.relation IN ('acts-for', 'dispatched-by')
    WHERE c.depth < 10000
      AND c.cur <> v_genesis
      AND principal_standing(pr.object) = 'active'
      AND (pr.delegation_expiry IS NULL OR pr.delegation_expiry > now())
      AND (pr.delegation_scope_classes IS NULL OR act_class = ANY(pr.delegation_scope_classes))
  )
  SELECT ARRAY_AGG(DISTINCT pr2.delegation_must_countersign ORDER BY pr2.delegation_must_countersign)
    INTO v_result
    FROM chain c2
    JOIN principal_relations pr2
      ON pr2.subject = c2.cur AND pr2.relation IN ('acts-for', 'dispatched-by')
    WHERE pr2.delegation_must_countersign IS NOT NULL
      AND principal_standing(pr2.object) = 'active'
      AND (pr2.delegation_expiry IS NULL OR pr2.delegation_expiry > now())
      AND (pr2.delegation_scope_classes IS NULL OR act_class = ANY(pr2.delegation_scope_classes));
  RETURN COALESCE(v_result, ARRAY[]::bigint[]);
END; $fn$;

COMMENT ON FUNCTION :"schema".principal_authority_chain_countersigners(bigint, text) IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: the DISTINCT set of principal
   ids required to countersign an act of act_class performed via pid''s authority chain (spec
   §2.3), gathered over the SAME scope/expiry-conjuncted path ELEMENT 7 walks. Empty array = no
   requirement. entitlement_enforce_delegation_conditions (ELEMENT 11) is the ONE caller.';

-- ============================================================================================
-- ELEMENT 9 -- entitlement_act_class_of RE-ISSUED (s62''s own body, verified unedited). TWO
-- widenings: (a) the principal_relation_asserted branch''s relation test widens from
-- `= 'acts-for'` to `IN ('acts-for', 'dispatched-by')` (the hazard-in-reach fix, this file''s own
-- header note); (b) that same branch now returns 'independent_verification_delegation' instead
-- of 'delegation_lifecycle' when delegation_purpose = 'independent-verification' (the carve-out,
-- spec §2.3). Every OTHER branch (principal_registered through gate_edge_supersession) is
-- BYTE-IDENTICAL to s62''s own text.
-- prior-body-sha256: 8faea33ec0936e061a53febf34abca017c67a89f101417023f17653953c74e22 (s62-delegation-lifecycle-gating.sql)
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
  -- s64 (kernel/lineage/s64-principal-stamps-delegation-conditions.sql): WIDENED from s62''s own
  -- `r.principal_relation = 'acts-for'` to include 'dispatched-by' (the hazard-in-reach fix, this
  -- file''s own header) -- and the independent-verification carve-out (spec §2.3): a fresh edge
  -- purposed for independent verification is its OWN act class, exempt by type from the
  -- no-redelegate/depth conjunct (ELEMENT 11), never from conjunct (b).
  IF r.kind = 'principal_relation_asserted' AND r.principal_relation IN ('acts-for', 'dispatched-by') THEN
    IF r.delegation_purpose = 'independent-verification' THEN
      RETURN 'independent_verification_delegation';
    END IF;
    RETURN 'delegation_lifecycle';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of(:"schema".ledger) IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (AMENDMENT), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED: acts-for widened to acts-for AND
   dispatched-by; independent_verification_delegation carve-out added): the act-class token a
   CANDIDATE ledger row belongs to by its OWN kind/attributes, or NULL if it belongs to none.
   EIGHT tokens as of s64.';

-- ============================================================================================
-- ELEMENT 10 -- entitlement_act_class_of_target RE-ISSUED (s62''s own body, verified unedited).
-- ONE widening, symmetric with ELEMENT 9: the relation test widens to
-- `IN ('acts-for', 'dispatched-by')`. Deliberately UNIFORM: a TARGET row (being superseded) is
-- always classified 'delegation_lifecycle' here regardless of its own delegation_purpose --
-- named as a LIMIT (not a gap): both delegation_lifecycle and independent_verification_delegation
-- are equally authority-bearing (conjunct b) and this function''s ONLY job is severance
-- protection ("is this row, by its own identity, an in-force member of a PROTECTED class") --
-- protecting it under either token achieves the identical refusal; a deployment configuring
-- DIFFERENT conjunct-(a) roles per token for a TARGET read would be the one case this uniform
-- read under-distinguishes, named in LIMITS below.
-- prior-body-sha256: a181b9b54009a282405fe7079f2070111f91da857997de9d2e1cc99450e21c7e (s62-delegation-lifecycle-gating.sql)
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
  -- s64: widened from s62''s own `p_principal_relation = 'acts-for'` to include 'dispatched-by'
  -- (symmetric with ELEMENT 9''s candidate-side fix; uniformly 'delegation_lifecycle', never
  -- 'independent_verification_delegation' -- see this element''s own header note).
  IF p_kind = 'principal_relation_asserted' AND p_principal_relation IN ('acts-for', 'dispatched-by') THEN
    RETURN 'delegation_lifecycle';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of_target(text, text, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (base), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED: acts-for widened to acts-for AND
   dispatched-by, symmetric with entitlement_act_class_of): the act-class token a row belongs to,
   judged purely from its own columns, one hop only. A dispatched-by target now protected against
   the SAME cross-kind severance vessel s62''s own round 2 closed for acts-for.';

-- ============================================================================================
-- ELEMENT 11 -- entitlement_enforce_class RE-ISSUED (s62''s own body, verified unedited). TWO
-- widenings: (a) the authority-bearing set gains the eighth token, independent_verification_
-- delegation (conjunct b: still must chain-reach genesis -- the carve-out exempts ONLY the
-- depth conjunct, ELEMENT 11b/12, never this one); (b) the chain-reachability call swaps from
-- the 1-arg principal_authority_chain_reaches_genesis(p_actor) to the NEW sibling function
-- principal_authority_chain_reaches_genesis_scoped(p_actor, p_act_class) (ELEMENT 7) --
-- "conjunction in the existing chain walk" (spec §3 item 1), a DROP-IN swap since p_act_class is
-- already this
-- function''s own parameter. On any chain carrying no delegation conditions (every pre-s64 edge),
-- this swap changes NOTHING -- ELEMENT 7''s own header proves the vacuous-agreement claim.
-- prior-body-sha256: 388c518301e99e7bc3df89916fdd97d6d9ef932440a14681433fe4544cf0e62c (s62-delegation-lifecycle-gating.sql)
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
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/s64, factored acceptance predicate conjunct a, %) — act class ''%'' requires an in-force role binding named ''%'' (this world''s configured entitlement map, see entitlement_class_roles); actor % holds no such binding. Remedy: a principal who ALREADY holds the ''%'' role (or genesis-chain authority) binds it to you: ./led principal bind-role <your-principal-name> "%" (kernel/lineage/s41-principal-bindings-and-relations.sql), then retry this act. See design/USER-RECIPES-FAQ.md''s entitlement-enforcement recipe for the worked example (kernel/lineage/s60-entitlement-enforcement.sql).', p_source, p_act_class, v_required_role, p_actor, v_required_role, v_required_role;
    END IF;
  END IF;

  -- s64: EIGHT tokens (delegation_lifecycle's AND independent_verification_delegation's writer
  -- must BOTH still chain-reach genesis -- the carve-out is scoped to the depth conjunct only,
  -- ELEMENT 12, never to this one).
  v_authority_bearing := p_act_class IN (
      'principal_registered', 'principal_role_bound', 'standing_lifecycle',
      'milestone_closure', 'gate_edge_supersession', 'entitlement_class_configured',
      'delegation_lifecycle', 'independent_verification_delegation');
  IF v_authority_bearing THEN
    -- s64: the condition-conjuncted sibling function (ELEMENT 7) -- a drop-in swap, vacuously
    -- agreeing with the 1-arg call it replaces on any chain with no delegation conditions set.
    SELECT principal_authority_chain_reaches_genesis_scoped(p_actor, p_act_class) INTO v_reaches;
    IF NOT v_reaches THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/s64, factored acceptance predicate conjunct b, %) — act class ''%'' is authority-bearing (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1.1b; design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.3); actor %''s authority chain (transitive reachability over in-force acts-for/dispatched-by relations, honoring every hop''s expiry/scope conditions, kernel/lineage/s64-principal-stamps-delegation-conditions.sql) does not reach this world''s genesis principal for this act class. Remedy: this is NOT a write you can perform on yourself — have your DELEGATOR run, on your behalf: ./autoharn led principal relate <delegator-principal-name> acts-for <a-principal-already-chain-connected-to-genesis>, covering you, and (if any upstream edge is scoped) confirm this act class is among that edge''s delegation_scope_classes — or have a severed/expired link repaired (suspension/revocation/expiry severs a chain PROSPECTIVELY only; past accepted acts through that link stay credited, kernel/lineage/s45-standing-lifecycle.sql''s I5 asymmetry).', p_source, p_act_class, p_actor;
    END IF;
  END IF;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_enforce_class(bigint, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (base), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED: eighth authority-bearing token,
   2-arg scope/expiry-conjuncted chain-reach call): the two-conjunct acceptance predicate. A
   no-op when act_class IS NULL.';

-- ============================================================================================
-- ELEMENT 11b -- entitlement_enforce_delegation_conditions(actor, act_class, obj,
-- p_signature_symmetry_witness): NEW. The two conjuncts entitlement_enforce_class does NOT
-- cover (depth-budget and must-countersign, spec §2.3) -- factored into their OWN helper
-- (ADR-0012 P1: one home) rather than folded into entitlement_enforce_class, because BOTH are
-- CANDIDATE-only conjuncts (they read NEW''s own principal_object/signature_symmetry_witness, not
-- available when entitlement_enforce_class is called a SECOND time for the TARGET''s class,
-- ELEMENT 12''s own note) -- calling this on the target class would be a category error (a
-- target row''s own object/witness are NOT what the candidate write is asking permission to use).
-- CONJUNCT (c), DEPTH: fires ONLY when act_class = 'delegation_lifecycle' EXACTLY (never
-- 'independent_verification_delegation' -- the carve-out, spec §2.3 row 1420, exempt BY TYPE) --
-- requires obj''s remaining redelegate budget (ELEMENT 6) to be NULL (unrestricted) or >= 1 (this
-- grant would be the Nth-of-N, still within budget; a grant when budget = 0 -- no-redelegate
-- reached -- is refused).
-- CONJUNCT (d), MUST-COUNTERSIGN: fires whenever the actor''s chain for act_class passes through
-- ANY edge naming a required countersigner (ELEMENT 8) -- a SINGLETON required set demands
-- p_signature_symmetry_witness name a s61 signed_commissions row attested by exactly that
-- principal; a set with MORE THAN ONE distinct required countersigner is UNSATISFIABLE by a
-- single-column witness and refused unconditionally (named as a LIMIT, not silently
-- fail-open -- fail-safe, never fail-open, the s60 D-6 idiom applied here).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".entitlement_enforce_delegation_conditions(
    p_actor bigint, p_act_class text, p_object bigint, p_signature_symmetry_witness bigint)
    RETURNS void LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_budget integer;
  v_countersigners bigint[];
  v_witness_attested_by bigint;
BEGIN
  IF p_act_class IS NULL THEN
    RETURN;
  END IF;

  -- CONJUNCT (c): DEPTH / NO-REDELEGATE. Fires only for the exact token 'delegation_lifecycle'
  -- (never the independent-verification carve-out token).
  IF p_act_class = 'delegation_lifecycle' AND p_object IS NOT NULL THEN
    v_budget := principal_redelegate_budget(p_object);
    IF v_budget IS NOT NULL AND v_budget < 1 THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s64, factored acceptance predicate conjunct c, no-redelegate/depth) — principal % has NO further redelegation budget (delegation_redelegate_depth exhausted along its own inbound chain, design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.3) -- a delegation edge naming % as the far endpoint (object) would grant a re-delegation this principal''s OWN grant forbids. Remedy: have the edge that ultimately caps % re-issued with a larger depth (a fresh grant, never a retroactive edit of the existing one), or route this authority through a principal whose chain is not depth-capped.', p_object, p_object, p_object;
    END IF;
  END IF;

  -- CONJUNCT (d): MUST-COUNTERSIGN. Applies to any act class (not merely delegation acts) --
  -- "an act under this edge binds only when an s61 signature-verified row by the named
  -- countersigner exists for it" (spec §2.3).
  v_countersigners := principal_authority_chain_countersigners(p_actor, p_act_class);
  IF array_length(v_countersigners, 1) IS NOT NULL THEN
    IF array_length(v_countersigners, 1) > 1 THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s64, factored acceptance predicate conjunct d, must-countersign) — actor %''s authority chain for act class ''%'' carries MORE THAN ONE distinct required countersigner (%) -- a single act can name only one signature_symmetry_witness, so this stacked caveat combination is UNSATISFIABLE by construction (a LIMIT, not a fail-open: named in kernel/lineage/s64-principal-stamps-delegation-conditions.sql''s own LIMITS). Remedy: have the conflicting must-countersign caveats corrected at their source edges so at most one distinct countersigner governs this path.', p_actor, p_act_class, v_countersigners;
    END IF;
    IF p_signature_symmetry_witness IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s64, factored acceptance predicate conjunct d, must-countersign) — actor %''s authority chain for act class ''%'' requires countersign by principal % (design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.3, "binds via s61 signature-verified rows") -- this write carries no signature_symmetry_witness. Remedy: have principal % run verify-commission --attest against a signed commission directing this act (kernel/lineage/s61-signature-symmetry-and-key-binding.sql), then supply --signature-witness <that attestation row''s id>.', p_actor, p_act_class, v_countersigners[1], v_countersigners[1];
    END IF;
    SELECT attested_by INTO v_witness_attested_by FROM signed_commissions
      WHERE row_id = p_signature_symmetry_witness;
    IF v_witness_attested_by IS DISTINCT FROM v_countersigners[1] THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s64, factored acceptance predicate conjunct d, must-countersign) — this write''s signature_symmetry_witness (row %) was attested by principal %, but the required countersigner for actor %''s chain, act class ''%'', is principal % (design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.3). Remedy: have principal % (not %) run the verify-commission --attest step.', p_signature_symmetry_witness, v_witness_attested_by, p_actor, p_act_class, v_countersigners[1], v_countersigners[1], v_witness_attested_by;
    END IF;
  END IF;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_enforce_delegation_conditions(bigint, text, bigint, bigint) IS
  'kernel/lineage/s64-principal-stamps-delegation-conditions.sql: the depth-budget (conjunct c,
   delegation_lifecycle ONLY, carved out for independent_verification_delegation) and
   must-countersign (conjunct d, any act class) checks the spec''s conditions vocabulary adds
   beyond entitlement_enforce_class''s own a/b. Called ONCE, on the CANDIDATE''s own class only
   (validate_entitlement, ELEMENT 12) -- never on a supersession TARGET''s class (these two
   conjuncts read NEW''s own object/witness, not meaningful for a row being superseded).';

-- ============================================================================================
-- ELEMENT 12 -- validate_entitlement RE-ISSUED (s62''s own body, verified unedited). ONE addition:
-- after both entitlement_enforce_class calls (candidate class, target class -- BYTE-IDENTICAL to
-- s62''s own two calls), a THIRD call to entitlement_enforce_delegation_conditions, for the
-- CANDIDATE''s own class only, passing NEW.principal_object and NEW.signature_symmetry_witness
-- (both already s41/s61 columns on NEW -- no new read this trigger did not already have access
-- to). A no-op when v_act_class IS NULL (ELEMENT 11b''s own early return).
-- prior-body-sha256: 8585db7119605489e9db261758f3021b62f6e0c4a337e5da4ad1d5b67cec10a5 (s62-delegation-lifecycle-gating.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_entitlement() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_act_class text;
  v_target_kind text;
  v_target_edge_type text;
  v_target_relation text;
  v_target_work_slug text;
  v_target_act_class text;
BEGIN
  v_act_class := entitlement_act_class_of(NEW);

  v_target_act_class := NULL;
  IF NEW.supersedes IS NOT NULL THEN
    SELECT l.kind, l.edge_type, l.principal_relation, l.work_slug
      INTO v_target_kind, v_target_edge_type, v_target_relation, v_target_work_slug
      FROM ledger l WHERE l.id = NEW.supersedes;
    IF FOUND THEN
      v_target_act_class := entitlement_act_class_of_target(
          v_target_kind, v_target_edge_type, v_target_relation, v_target_work_slug);
    END IF;
  END IF;

  IF v_act_class IS NULL AND v_target_act_class IS NULL THEN
    RETURN NEW;
  END IF;

  PERFORM entitlement_enforce_class(NEW.actor, v_act_class, 'this row''s own act class');
  PERFORM entitlement_enforce_class(
      NEW.actor, v_target_act_class,
      format('the class of row %s, which this write supersedes', NEW.supersedes));

  -- s64: the depth-budget/must-countersign conjuncts, CANDIDATE class only (ELEMENT 11b''s own
  -- header explains why this is never also called for v_target_act_class).
  PERFORM entitlement_enforce_delegation_conditions(
      NEW.actor, v_act_class, NEW.principal_object, NEW.signature_symmetry_witness);

  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_entitlement ON :"schema".ledger;
CREATE TRIGGER validate_entitlement BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_entitlement();

COMMENT ON FUNCTION :"schema".validate_entitlement() IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (round 2), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (adds the depth-budget/must-countersign
   conjuncts, candidate class only): the factored acceptance predicate, now four conjuncts wide
   for a delegation-classified candidate act (a/b via entitlement_enforce_class, c/d via
   entitlement_enforce_delegation_conditions), two conjuncts wide (a/b only) for a supersession
   TARGET''s class. Refusals journal as write_refused rows via the s43 boundary, unchanged.';

-- ============================================================================================
-- ELEMENT 13 -- GRANTS. No new GRANT needed: principal_redelegate_budget/
-- principal_authority_chain_reaches_genesis_scoped/principal_authority_chain_countersigners
-- factor entirely through principal_relations/entitlement_genesis_principal/
-- principal_standing/signed_commissions (all already granted or SECURITY-context-inherited
-- exactly as their s60/s61 siblings); entitlement_enforce_delegation_conditions is called only
-- from validate_entitlement (a SECURITY DEFINER-context trigger, s43''s own boundary), never
-- directly by :role.
-- ============================================================================================

-- ============================================================================================
-- HISTORY: safe -- per-mechanism grounds:
--   * FIVE new nullable no-DEFAULT columns, kind-scoped (never mandatory) by CHECKs that
--     validate vacuously on every pre-existing row (no pre-existing principal_relation_asserted
--     row can retroactively acquire a non-NULL delegation_* value -- the columns did not exist
--     before this delta, so their prior value is uniformly NULL, satisfying every new CHECK''s
--     "OR column IS NULL" disjunct).
--   * principal_relations re-issued WIDER (append-only column list, s41''s own "raw, ordered
--     projection" shape unchanged; every existing named-column consumer unaffected).
--   * principal_authority_chain_reaches_genesis(bigint) [1-arg] is NEVER touched -- the NEW
--     principal_authority_chain_reaches_genesis_scoped(bigint,text) is a SEPARATE, DIFFERENTLY-
--     NAMED function object (never an overload of the same name -- this file's own header note
--     on gates/kernel_function_census.py's bare-name key scheme explains why), so every existing
--     caller of the 1-arg form keeps its EXACT existing meaning, unconditionally.
--   * entitlement_act_class_of/entitlement_act_class_of_target re-issued: the ONLY behavioral
--     change is that a 'dispatched-by' principal_relation_asserted row is now classified
--     (was NULL, i.e. UNGATED, before this delta -- a hazard this delta closes, this file''s own
--     header) -- new-refusal-only, no row that was gated before becomes ungated.
--   * entitlement_enforce_class re-issued: the authority-bearing SET only WIDENS (+1 token); the
--     chain-reach call swaps to the new sibling function, which VACUOUSLY agrees with the 1-arg
--     call on every chain with no delegation conditions (every pre-s64 edge) -- new-refusal-only.
--   * entitlement_enforce_delegation_conditions/principal_redelegate_budget/
--     principal_authority_chain_countersigners are BRAND NEW functions with no pre-existing
--     reader.
--   * validate_entitlement re-issued: ONE new PERFORM call appended after its two existing,
--     byte-identical calls; the new call is itself a no-op whenever v_act_class IS NULL
--     (ELEMENT 11b''s own early return) -- exactly the shape every prior validate_entitlement
--     re-issue (s62) already established.
--   * compute_row_hash/ledger_current/countersigned_in_force re-issues are s42''s law, self-
--     applied, pure column-list appends (s20 lesson), byte-identical to the s28..s61 precedent.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: a delegation edge (principal_relation_asserted, relation acts-for or
--     dispatched-by, fresh assertion) may carry conditions -- a redelegation-depth budget, a
--     required countersigner, an expiry, and a scope restricting which act classes it backs; the
--     acceptance predicate for any authority-bearing candidate act refuses it unless (a) an
--     in-force role binding when configured, (b) the actor''s chain reaches genesis THROUGH ONLY
--     unexpired, in-scope edges for that specific act class, (c) — for a FRESH delegation act
--     specifically, exempting the independent-verification carve-out class BY TYPE — the far
--     endpoint''s own redelegation budget is not exhausted, and (d) every DISTINCT required
--     countersigner along the chain is satisfied by an s61-verified signature_symmetry_witness;
--     every refusal is a committed, journaled write_refused row via the existing s43 boundary.
--   - QUANTIFICATION UNIVERSE:
--       ACT CLASSES: EIGHT tokens as of s64 (the seven s60/s62 tokens plus
--         independent_verification_delegation); delegation_lifecycle''s OWN classification is
--         widened from acts-for-only to acts-for-or-dispatched-by (the hazard-in-reach fix).
--       KINDS/COLUMNS: five new columns, licensed ONLY on principal_relation_asserted rows
--         naming relation acts-for/dispatched-by with principal_binding_active = true (two-way
--         per column); no other kind touched; NO new kind (spec''s own text, verbatim).
--       VIEWS: principal_relations widened (+5, append-only); ledger_current/
--         countersigned_in_force re-issued (+5, s20 lesson); no other view touched.
--       FUNCTIONS: principal_authority_chain_reaches_genesis(bigint) [1-arg] UNTOUCHED;
--         principal_authority_chain_reaches_genesis_scoped(bigint,text) [a DIFFERENTLY-NAMED
--         sibling, never an overload], principal_redelegate_
--         budget, principal_authority_chain_countersigners, entitlement_enforce_delegation_
--         conditions are BRAND NEW; entitlement_act_class_of, entitlement_act_class_of_target,
--         entitlement_enforce_class, validate_entitlement RE-ISSUED (each widened, no existing
--         branch''s text edited -- see HISTORY above per-function).
--       TRIGGERS: ZERO new members; validate_entitlement''s SAME trigger, DROP/CREATE at the
--         SAME position (s60 Element 8''s own ordering, unchanged).
--       ENGINE: engine/lp/ledger_entitlement.lp gains reaches_genesis_scoped/2 (the SAME
--         conjunction -- scope AND expiry -- in its stratified closure, BESIDE reaches_genesis/1,
--         never folded into it -- spec §3 item 4, verbatim). engine/ledger_edb.py''s
--         export_entitlement gains THREE new, purely-ADDITIVE fact families (act_class/1,
--         edge_scope_class/3, edge_unscoped/2) -- the four PRE-EXISTING families (principal,
--         acts_for_edge, genesis, principal_active) are BYTE-IDENTICAL in every emission rule,
--         so ./judge''s AGREE on reaches_genesis/1 (the s60/s62 differential) is UNCHANGED by
--         this delta -- a SEPARATE, NEW AGREE leg (reaches_genesis_scoped/2 vs the SQL 2-arg
--         function) is this delta''s own differential proof.
--       GATES: gates/kernel_function_census_bank.json gains four new entries (schema:
--         principal_authority_chain_countersigners, schema:principal_redelegate_budget,
--         schema:entitlement_enforce_delegation_conditions -- new bank rows -- and the four
--         widened schema:entitlement_act_class_of/entitlement_act_class_of_target/
--         entitlement_enforce_class/validate_entitlement rows, whose deployed pg_get_functiondef
--         hash necessarily changes since their bodies changed) via
--         `python3 gates/kernel_function_census.py --bank`, run and committed as part of this
--         delta (this file''s own commit).
--   - DENOMINATION: a redelegation budget in a DERIVED integer (or NULL for unrestricted),
--     recomputed fresh at act time, never stored (spec''s own count/history-shaped-conditions
--     rule); a countersign requirement in the s61-verified signed_commissions substrate, never a
--     boolean self-assertion; scope in the SAME kernel-computed act-class vocabulary
--     entitlement_act_class_of already emits, never a writer-invented string; expiry in a
--     timestamptz compared against now() at read time, never a stored "is-expired" boolean (the
--     s40 "computed at read" law, applied to time). No bound is a bare round literal (the depth
--     cap and the countersign/scope/expiry conditions are per-edge writer-chosen values, never a
--     kernel-hardcoded constant beyond the 10000 depth-cap shared with every other recursive walk
--     in this lineage).
--
-- PER-REFUSAL DIFFERENTIAL VISIBILITY (the commission''s own explicit request, per s63''s finding
-- that AGREE is blind to write-boundary refusal drift -- stated honestly, per refusal, not as an
-- umbrella claim):
--   - Conjunct (b) widened (scope/expiry-conjuncted chain reach): AGREE COVERS this. The NEW
--     reaches_genesis_scoped/2 ASP predicate independently re-derives the SAME scope/expiry-
--     filtered reachable set the SQL 2-arg function computes; a stratification mistake in either
--     side''s closure would surface as a differential disagreement, exactly like s60''s own
--     reaches_genesis/1 leg. AGREE says nothing about WHICH writes were refused at the write
--     boundary (s63''s own finding, unchanged) -- it is a statement about the chain the exporter
--     reads on a POST-mutation snapshot, not about refusal timing.
--   - Conjunct (c), depth-budget (no-redelegate): AGREE DOES NOT COVER this. No ASP twin ships
--     (this file''s own LIMITS, below) -- deferred on the SAME grounds s61 named for its own
--     single-hop checks (the value an independent aggregate-recursion re-derivation would buy is
--     smaller than the risk of getting a novel MIN-aggregate stratification wrong under this
--     build''s own time budget), stated as a LIMIT, never silently skipped. Proven ONLY by the
--     RED/GREEN fixture legs (below), never by the differential.
--   - Conjunct (d), must-countersign: AGREE DOES NOT COVER this. Same class of deferral as s61''s
--     OWN item-1/item-3 checks (single-hop EXISTS against signed_commissions) -- named there as
--     acceptable precedent for exactly this shape, followed here. Proven ONLY by the RED/GREEN
--     fixture legs.
--   - The hazard-in-reach fix (dispatched-by now classified): AGREE DOES NOT DIRECTLY COVER this
--     EITHER (classification happens entirely SQL-side, before any row ever reaches the ledger
--     the exporter reads -- a refused write never becomes an acts_for_edge/2 fact on EITHER side,
--     matching s62''s own identical disclosure for its own cross-kind fix). Proven ONLY by the
--     RED/GREEN fixture legs.
--   - Independent-verification carve-out: same as conjunct (c) -- the carve-out is a
--     classification-time decision (entitlement_act_class_of), invisible to the differential by
--     the SAME reasoning; proven by its own dedicated GREEN leg.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape (this delta only ADDS refusals -- five new columns, one widened existing view, four new
-- functions, three widened re-issues that only ADD to an existing enumerated set or swap in a
-- vacuously-agreeing sibling function call (never an overload -- distinct names throughout, this
-- file's own header note), one re-issued trigger appending one new no-op-by-default call; no
-- existing CHECK narrowed, no existing trigger''s pre-existing branch edited, no existing grant
-- revoked, no existing function''s SIGNATURE behavior changed) -- riding the
-- 2026-07-09 class rule exactly as s60/s62 did, per the spec''s own §3 item 1 framing
-- ("scratch-witnessed both polarities, SQL/ASP AGREE (the applicable half) admits it to the
-- birth chain without a per-delta maintainer question").
--
-- LIMITS (pre-registered):
--   - NO ASP TWIN for conjunct (c) (depth-budget) or conjunct (d) (must-countersign) -- named
--     above (PER-REFUSAL DIFFERENTIAL VISIBILITY) and here: both are single-hop-or-aggregate
--     checks over already-in-force facts, the SAME shape s61 itself deferred (its own header:
--     "an ASP twin for a single-hop existence check would mirror the SQL query nearly verbatim").
--     Filed as a possible follow-on, not built or claimed built.
--   - delegation_scope_classes restricts by ACT CLASS only, never by "world" (the spec''s own
--     second scope axis) -- a kernel schema/world IS the chain walk''s own boundary; there is no
--     cross-world chain for a single schema''s delta to scope within. Cross-world authority is the
--     domain/zone conjunct seat design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §4 reserves for its
--     OWN later delta, not built here.
--   - entitlement_act_class_of_target classifies EVERY protected acts-for/dispatched-by target
--     row uniformly as 'delegation_lifecycle', never distinguishing independent_verification_
--     delegation on the TARGET side (ELEMENT 10''s own header) -- the one narrow scenario this
--     under-distinguishes (a deployment configuring DIFFERENT conjunct-(a) roles for the two
--     tokens, where a target-side read would matter) is named, not silently accepted as
--     equivalent in every case.
--   - A required-countersigner SET with more than one distinct member is UNSATISFIABLE by a
--     single signature_symmetry_witness column and is refused unconditionally (ELEMENT 11b) --
--     fail-safe, never fail-open, but this means STACKING two must-countersign caveats naming
--     DIFFERENT principals on the same chain makes every act through that chain impossible, not
--     merely harder -- named as a LIMIT of the single-witness-column substrate this delta reuses
--     from s61, not a new column minted to carry multiple simultaneous witnesses.
--   - No construction-time refusal exists for a delegation_redelegate_depth value that is
--     internally inconsistent with an ALREADY-established downstream chain (e.g., rotating an
--     edge to a SMALLER cap after descendants already exist under the larger one) -- the budget
--     is recomputed FRESH on every call (never cached), so a rotation''s effect is simply that the
--     NEXT act by any descendant sees the NEW, smaller budget; nothing already accepted is
--     retroactively altered (I5 asymmetry, the standing lineage-wide rule, applied here rather
--     than re-argued).
--   - Trigger/CHECK refusals bind the granted role''s ordinary INSERT path only; the schema-
--     owner/superuser bypass stands (the standing s26..s63 disclosed bound).
--   - Anonymous sessions (no minted principal, no dispatch edge): authority-bearing writes refuse
--     ALREADY, by the pre-existing s43 actor-resolution + s60/s62 conjunct (b) machinery
--     (an unregistered actor cannot chain-reach genesis) -- this delta adds NO new mechanism for
--     this, it is a pre-existing invariant this delta does not disturb, named here per the
--     commission''s own explicit text rather than left unaddressed.
--   - In a solo world, every delegation-condition fact is written by machinery the one operator
--     controls -- complete and attributed, not adversarially independent (s17''s own honesty,
--     inherited).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s63):
--   VALIDATE (reachable throwaway): apply the FULL s15..s63 chain (see kernel/lineage/
--   s63-supersession-body-restoration.sql''s own PREREQUISITE chain, itself s61''s VALIDATE block
--   +2), THEN -f s64-principal-stamps-delegation-conditions.sql (genesis seed per s26; discharge
--   the s40/s43/s60 birth sequence before exercising any delegation act, exactly as s60/s62''s own
--   VALIDATE notes require).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world''s birth chain automatically via bootstrap/new-project.sh''s
--   --new-world glob-driven apply list (this file''s own PREREQUISITE section) the moment a tree
--   carrying it is scaffolded from; the hand-maintained CLASSIC-scaffold LINEAGE_CHAIN list is a
--   SEPARATE, later maintainer integration act, matching s58 through s63''s own identical
--   precedent. Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP/CREATE TRIGGER).
-- ============================================================================================
