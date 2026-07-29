-- s72 STAMP-BINDING CONJUNCT (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec5
-- item 5, "S3 stamp-binding conjunct... RBAC's authenticated input", ratified basis ledger row
-- 639; design basis ledger row 601, the S3 adjudication and its four REQUIRED corrections,
-- restated and discharged below). FAIL-SAFE-ADDITIVE (CLAUDE.md 2026-07-09 class rule): this
-- delta ONLY ADDS refusals -- TWO new kinds, ONE new nullable column, TWO new derived views, one
-- widened existing CHECK (entitlement_act_class_kind_shape, a third kind), two widened existing
-- CHECKs one kind further each (principal_subject_kind_shape, principal_binding_active_kind_
-- shape), three widened existing functions (entitlement_act_class_of, entitlement_act_class_of_
-- target, entitlement_enforce_class -- each gains new branches/tokens, no existing branch text
-- edited), and ONE re-issued trigger body (validate_entitlement -- a genuinely new conjunct,
-- unlike s70/s71, see WHY below for why this delta cannot ride the "zero trigger bodies touched"
-- shape s70 rode). Nothing existing is relaxed: an UNARMED world (zero stamp_binding_class_
-- configured rows -- the shipped default, no birth-sequence act of this delta's own) is BYTE-
-- IDENTICAL to s71-head (conjunct (c), below, is a no-op whenever a candidate's own act class is
-- not among the nominated set, which is empty by default). Sonnet-built per the standing
-- delegation contract, from the ratified spec plus row 601's adjudication.
--
-- THIS DELTA IS AUTHORED AND SCRATCH-WITNESSED ONLY; applying it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s71 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of any frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second copy of any existing mechanism (ADR-0012 P1): stamp binding extends s60's OWN
-- authority-bearing act-class machinery (entitlement_act_class_of/entitlement_act_class_of_
-- target/entitlement_enforce_class) exactly as s62/s64/s70 already extended it -- this delta
-- mints the TENTH and ELEVENTH tokens (stamp_binding, stamp_binding_class_configured) by the
-- identical widen-in-place mechanism, never a parallel entitlement pipeline. The two new derived
-- views follow s41 D-5's/s60 Element 4's OWN shape (principal_role_bindings/entitlement_class_
-- roles are the literal templates, quoted at Elements 5/6's own headers). The one new column
-- (stamp_binding_agent) reuses the principal_role_name IDENTITY-field precedent (s41 D-1: mandatory
-- on BOTH a fresh assertion and a retraction, since it names WHICH binding this row is about, not
-- merely its value) rather than s70's OPTIONAL-value-field precedent -- see Element 2's own header
-- for why this delta's one column is an identity field, not a value field.
--
-- PREREQUISITE: this delta REQUIRES s71 (kernel/lineage/s71-row-level-scope-policies.sql) applied
-- first -- it re-issues compute_row_hash/ledger_current/countersigned_in_force in the EXACT
-- 104-column shape s70 left them (s71 added no ledger column, verified: its own header states
-- "It re-issues NOTHING: no column added"), and re-issues entitlement_act_class_of/entitlement_
-- act_class_of_target/entitlement_enforce_class/validate_entitlement in the EXACT shape s64 left
-- them for the first three (s70 widened them; s71 touches none of the four -- grepped in full
-- before authoring this delta: only s60/s62/s64/s70 ever CREATE OR REPLACE any of the three
-- act-class functions, and only s60/s62/s64 ever CREATE OR REPLACE validate_entitlement itself,
-- s70's own Element 9 stating explicitly it re-issues zero trigger bodies). It ALSO re-issues
-- (widens) principal_subject_kind_shape in the exact nine-kind shape s70 left it and principal_
-- binding_active_kind_shape in the exact seven-kind shape s70 left it (no file since s70 touches
-- either constraint -- grepped), and entitlement_act_class_kind_shape in the exact one-kind shape
-- s60 left it (no file since s60 touches it -- grepped). Applying this file on a kernel that does
-- not already carry those objects in their s71-head shape fails loudly at ALTER TABLE / CREATE OR
-- REPLACE FUNCTION time, the correct, disclosed failure mode, matching every prior PREREQUISITE
-- precedent. THE HEAD-BODY RULE (s45's own standing instruction, carried here verbatim): at this
-- delta's authoring the lineage head is s71 (kernel/lineage/'s own directory listing, confirmed
-- by the builder before authoring). This file's re-issued bodies are quoted, verified, against
-- their true immediately-prior re-issue's own text (s70 for the three act-class functions and for
-- compute_row_hash/ledger_current/countersigned_in_force; s64 for validate_entitlement itself,
-- the true lineage head for that trigger per s70's own Element 9 note, re-verified here) -- each
-- ELEMENT below carries its own `-- prior-body-sha256:` line (gates/lineage_reissue_lineage.py,
-- MIN_N_HASH-covered).
--
-- WHY (the S3 mechanism, spec sec5 item 5, read literally against row 601's four required
-- corrections -- restated here as this delta's own obligations, each discharged by name):
--
--   THE MECHANISM. A world may ARM a stamp-binding requirement over a NOMINATED subset of the
--   kernel's OWN closed act-class vocabulary (the same eleven-token set entitlement_class_roles
--   already matches against, s60 Element 4's own free-text-token-over-a-kernel-computed-
--   vocabulary idiom, one axis over): once an act class is nominated (a fresh stamp_binding_
--   class_configured row naming it), every future write in that class must ALSO carry a VERIFIED
--   interception stamp (stamp_verified = true -- an unstamped OR a present-but-invalid-HMAC write
--   never counts, see Element 10's own header for why verification, not mere string equality, is
--   load-bearing here) whose stamp_agent value matches an IN-FORCE principal_stamp_bound row
--   naming the ACTING principal (NEW.actor) as bound to that exact agent string. This is RBAC's
--   AUTHENTICATED INPUT (spec sec5 item 5's own phrase): entitlement (s60..s70) already answers
--   "does this principal hold the required role/chain"; this conjunct additionally answers "was
--   THIS PARTICULAR WRITE actually produced by an invocation this principal is on record as
--   controlling" -- a question entitlement's own actor/role/chain machinery, keyed purely on the
--   WRITER-SUPPLIED `actor` column, cannot answer by itself (a forger who merely knows a
--   genesis-chained actor's numeric id can already satisfy conjuncts a/b; conjunct (c) additionally
--   requires the WRITE to have arrived over an invocation the kernel can verify, by HMAC, that
--   principal has bound in advance).
--
--   CORRECTION 1 (row 601, verbatim basis): "binding to 'main' admits every governed session's
--   main thread, which is acceptable single-trust-domain semantics ONLY if disclosed as such, and
--   its true value is enforceable orchestrator-only act classes (excludes unstamped and subagent-
--   stamped writes)." DISCLOSED HERE, PLAINLY: this delta's own new column, stamp_binding_agent,
--   binds ONLY on stamp_agent (s17's own hook-injected invocation-identity string), NEVER on the
--   (stamp_session, stamp_agent) PAIR s21 uses for cross-session DISTINCTNESS -- a deliberate,
--   narrower identity than s21's own, chosen because the s21 lesson this correction cites is
--   EXACTLY "session-blindness would falsely refuse an honest cross-session claim"; the SAME
--   session-blindness is, for THIS mechanism, the intended posture: binding a principal to agent
--   'main' means "every session's main (interactive orchestrator) thread, in this single-trust-
--   domain solo world, is this principal's authenticated voice" -- admitting every governed
--   session's main thread is not a gap here, it is the shape of the guarantee this conjunct
--   actually offers (one operator, s17's own "complete and attributed, not adversarially
--   independent" honesty, restated one mechanism further). The enforceable VALUE, per row 601, is
--   confining a deployment's OWN nominated set to orchestrator-only act classes -- see CORRECTION
--   2 immediately below for exactly which existing act classes that is and is not.
--
--   CORRECTION 2 (row 601, verbatim basis): "ephemeral dispatched-agent ids are unbindable in
--   advance -- either verify the gated class enumeration excludes the ephemeral-principal idiom
--   (check entitlement_act_class_of, never assume) or design a dispatch-time/first-verified-use
--   binding path." CHECKED, NOT ASSUMED (this delta's own builder read hooks/stamp_intercept.py
--   and kernel/lineage/s21-session-aware-distinctness.sql's own header before writing this
--   paragraph): stamp_agent is `str(data.get("agent_id") or "main")` -- a dispatched subagent
--   carries a DISTINCT, harness-minted, unknowable-in-advance ephemeral id (e.g.
--   "agent-a47950d7504b5b166"), never 'main'. Checking entitlement_act_class_of's OWN eleven-token
--   enumeration (this file's Elements 7/8) against OBSERVED PRACTICE (not assumption): four of the
--   pre-existing tokens -- principal_registered, principal_role_bound, standing_lifecycle,
--   entitlement_class_configured -- are, by this project's own documented convention (tools/
--   dispatch_principal.py's own docstring: registering/suspending a principal is "the
--   orchestrator's own deliberate act"), ALWAYS written by the interactive orchestrator's main
--   thread; binding a stamp-binding-eligible principal to 'main' alone gives FULL, byte-honest
--   enforcement for a world that nominates ONLY those four (plus this delta's own two new
--   self-protecting tokens, stamp_binding and stamp_binding_class_configured -- see CORRECTION 4).
--   ONE existing token is NOT in that shape: milestone_closure (a gated work_closed act) is, by
--   this project's own routine practice, closed by the DISPATCHED SUBAGENT that was assigned the
--   work item -- nominating milestone_closure (or gate_edge_supersession, its sibling) under this
--   conjunct, with only a 'main'-bound principal available, WOULD refuse those legitimate subagent
--   closes, since their ephemeral stamp_agent can never be bound in advance. THIS IS THE FORK ROW
--   601 NAMES, AND THE JUDGMENT IT REQUIRES BEYOND WHAT THIS BUILD CAN WITNESS: a dispatch-time/
--   first-verified-use binding path (row 601's own second option) would need to mint the principal_
--   stamp_bound row at the MOMENT a subagent's real ephemeral stamp_agent first becomes observable
--   (e.g. the dispatcher's own first write after receiving the subagent's agent_id) -- a genuinely
--   new ceremony this codebase has no existing precedent for (tools/dispatch_scope.py's own
--   dispatch-time minting binds a principal TO A PRINCIPAL, already known at mint time, never to a
--   stamp string, confirmed by reading that file in full: `stamp_agent` appears nowhere in it), and
--   whose soundness (what stops a compromised dispatcher from binding the WRONG ephemeral id, or
--   binding one that never gets stamp_verified, and does the binding need its own revocation
--   window) is a maintainer-grade design question, not a build-time implementation detail. PER ROW
--   601'S OWN INSTRUCTION ("if this fork requires judgment beyond what you can witness, STOP on
--   that item and report the fork with evidence -- do not pick silently"): this build does NOT
--   invent that ceremony. Instead it ships the mechanism so that its OWN default nomination is
--   EMPTY (byte-identical, Element 9's own note -- no token is in the default nominated set,
--   mirroring s62/s70's own "not in the default map" choice for their own new tokens) and
--   DISCLOSES, in this header and in LIMITS below, the EXACT boundary a deployment must respect:
--   nominate stamp_binding_class_configured, stamp_binding, principal_registered, principal_role_
--   bound, or standing_lifecycle freely (orchestrator-only by observed practice, 'main'-binding is
--   sound); do NOT nominate milestone_closure or gate_edge_supersession without EITHER (a)
--   accepting that a dispatched subagent's legitimate close is now refused (a real, disclosed
--   friction cost, not a defect) or (b) building the dispatch-time/first-verified-use path this
--   header names as a REPORTED, NOT-BUILT follow-on. Reported, not picked silently.
--
--   CORRECTION 3 (row 601, verbatim basis): "bootstrap ordering for the birth-sequence binding
--   act." STATED, NOT SCAFFOLD-EDITED (this delta's own commission: do not touch bootstrap): since
--   this delta ships with ZERO nominated classes by default (Element 9's own note), NO birth-
--   sequence act of this delta's own is required for a fresh world's zero-friction birth --
--   exactly the s62/s70 precedent for a newly minted, not-yet-configured token. A deployment
--   ARMING this conjunct over its own two self-protecting tokens (stamp_binding, stamp_binding_
--   class_configured -- CORRECTION 4 below) has a well-defined, NAMED seat for the ordering this
--   correction asks about: mint the genesis principal's OWN principal_stamp_bound row (agent=
--   'main') via ledger_write BEFORE writing the stamp_binding_class_configured row that nominates
--   either self-protecting token -- otherwise the FIRST such nomination (which is itself gated by
--   conjunct (c) the instant it is nominated, self-referentially) would refuse itself. This is the
--   IDENTICAL bootstrapping shape s60 Element 9's own header already discloses for conjunct (a)'s
--   "bind the role before writing the config that requires it" ordering, one conjunct over -- named
--   here as the exact seat a scaffold integration would need (immediately after the existing s60
--   birth-sequence discharge, before any stamp_binding_class_configured write), NOT built as a
--   bootstrap/new-project.sh edit by this delta (this delta's own commission: "do NOT touch
--   bootstrap templates"). A deployment nominating ONLY the four pre-existing orchestrator-only
--   tokens (CORRECTION 2) needs no such self-referential ordering at all -- binding genesis to
--   'main' is itself gated by conjunct (b) alone (stamp_binding is unconditionally authority-
--   bearing, Element 9) until stamp_binding itself is separately nominated.
--
--   CORRECTION 4 (row 601, verbatim basis): "compose with S2's owner/access split, which shrinks
--   the 'superuser INSERT triggers-disabled' [item] to a birth-only act." STATED: the standing
--   disclosed bound every s26..s71 delta carries ("trigger/CHECK refusals bind the granted role's
--   ordinary INSERT path only; the schema-owner/superuser bypass stands") is, per the S2b split
--   (ledger row 600, 0e2eda39/513c91e2) that has now landed a chain, narrower than it reads in
--   isolation: post-split, the connecting/access role (:"role", e.g. a world's `<name>_rw`) is
--   NEVER the schema owner, so an ORDINARY served session can never bypass THIS conjunct (or any
--   other trigger-enforced refusal) by owner-equivalence at runtime -- that bypass is confined to
--   the LITERAL migration/apply identity (the superuser who runs `psql -f` at birth or at a future
--   delta's own application), a BIRTH-ONLY act, never a standing runtime exposure for a served
--   principal. This delta's OWN two new self-protecting tokens (stamp_binding, stamp_binding_
--   class_configured) inherit that same narrowed bound automatically -- they gate the GRANTED
--   role's INSERT path exactly like every sibling authority-bearing token, and the S2b split is
--   what makes that gate meaningful at runtime rather than merely on paper (s71's own "HONEST
--   BOUND" header note, restated here one mechanism further for THIS delta's own conjunct).
--
-- ELEMENT 1 -- TWO NEW KINDS: principal_stamp_bound (thirty-fifth member) and stamp_binding_class_
-- configured (thirty-sixth member). principal_stamp_bound mirrors s41's OWN binding-kind shape
-- (D-1: principal_subject + principal_binding_active discriminator, fresh assert vs retraction)
-- one kind further; stamp_binding_class_configured mirrors s60's OWN entitlement_class_configured
-- shape (a configuration EVENT naming which act class this conjunct nominates) one axis further --
-- REUSING entitlement_act_class (s60, Element 2 below) rather than a second "which act class"
-- column (ADR-0012 P1), exactly as s60 itself reused principal_role_name across two kinds.
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
     'principal_scope_bound',
     'principal_stamp_bound','stamp_binding_class_configured'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s72-stamp-binding-conjunct.sql: widens s70''s thirty-four-member vocabulary by
   principal_stamp_bound (binds a registered principal to a stamp_agent identity string -- RBAC''s
   authenticated input, design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec5 item 5) and
   stamp_binding_class_configured (nominates which act class this conjunct governs, s60''s own
   entitlement_class_configured shape one axis over).';

-- ============================================================================================
-- ELEMENT 2 -- THE ONE NEW COLUMN + THE THREE WIDENED CHECKS. stamp_binding_agent is an IDENTITY
-- field (s41 D-1's own split), NOT a value field like s70's scope_surfaces/scope_exclusions/
-- scope_disclosure_mode: it names WHICH stamp-agent string this binding is about, so it is
-- mandatory on BOTH a fresh assertion AND a retraction (principal_binding_active=false still
-- restates identity fields only) -- the identical shape principal_role_name already carries for
-- principal_role_bound (s41), reused here one kind further, never a second "which identity"
-- column shape invented. A principal may hold MULTIPLE simultaneous stamp bindings (e.g. bound to
-- BOTH 'main' and some other stable, deployment-chosen agent string) -- each is its own row,
-- individually retractable, exactly as s41's own role/relation bindings already permit multiple
-- simultaneous bindings per principal.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS stamp_binding_agent text;

COMMENT ON COLUMN :"schema".ledger.stamp_binding_agent IS
  'kernel/lineage/s72-stamp-binding-conjunct.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-
   FLOW-SPEC.md sec5 item 5): the stamp_agent STRING (s17''s own hook-injected invocation-identity
   value, e.g. ''main'') a principal_stamp_bound row binds to its principal_subject. IDENTITY
   field (s41 D-1), mandatory on BOTH a fresh assertion and a retraction -- this delta''s own
   header CORRECTION 1: binding is on stamp_agent ALONE, never the (stamp_session, stamp_agent)
   PAIR s21 uses for cross-session distinctness -- deliberately admitting every governed session''s
   own instance of that agent string, single-trust-domain semantics, disclosed as such.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS stamp_binding_agent_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT stamp_binding_agent_kind_shape CHECK (
    (kind = 'principal_stamp_bound') = (stamp_binding_agent IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS stamp_binding_agent_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT stamp_binding_agent_nonempty CHECK (
    stamp_binding_agent IS NULL OR btrim(stamp_binding_agent) <> '');

-- entitlement_act_class (s60, Element 2 there): ONE home, re-issued wider -- the THIRD kind that
-- carries it (entitlement_class_configured, and now stamp_binding_class_configured), never a
-- second, parallel "which act class this configures" column (ADR-0012 P1).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS entitlement_act_class_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT entitlement_act_class_kind_shape CHECK (
    (kind IN ('entitlement_class_configured', 'stamp_binding_class_configured'))
    = (entitlement_act_class IS NOT NULL));

COMMENT ON COLUMN :"schema".ledger.entitlement_act_class IS
  'kernel/lineage/s60-entitlement-enforcement.sql: the act-class token an entitlement_class_
   configured OR (as of s72) a stamp_binding_class_configured row names (identity field, mandatory
   on those two kinds, forbidden elsewhere). Free text, no enum -- the kernel-computed set of
   act-class strings entitlement_act_class_of() emits is the only vocabulary either configuration
   row can USEFULLY match. REUSED across two configuration kinds by kernel/lineage/
   s72-stamp-binding-conjunct.sql, the SAME free-text vocabulary answering both "this class
   requires this role" and "this class requires a bound stamp" -- one column, two configuration
   axes, ADR-0012 P1.';

-- principal_subject: ONE home (s40/s41), re-issued wider -- the TENTH principal_* kind joins the
-- nine s70 left it (identical widen-in-place idiom every prior principal_* kind addition used).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_subject_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_subject_kind_shape CHECK (
    (kind IN ('principal_registered','principal_suspended','principal_revoked',
              'principal_standing_declared',
              'principal_relation_asserted','principal_role_bound','principal_key_bound',
              'principal_competence_granted',
              'principal_scope_bound','principal_stamp_bound')) = (principal_subject IS NOT NULL));

COMMENT ON COLUMN :"schema".ledger.principal_subject IS
  'The principal an identity/binding event is ABOUT (distinct from actor). Mandatory on exactly
   TEN kinds as of s72 (kernel/lineage/s72-stamp-binding-conjunct.sql widens s70''s nine-kind
   licensing by principal_stamp_bound -- WHO this stamp binding governs), forbidden elsewhere. ONE
   constraint, re-issued wider (never a second, patching constraint, ADR-0012 P1).';

-- principal_binding_active: ONE home (s41, widened by s45, s70), re-issued wider -- the EIGHTH
-- licensed kind (principal_stamp_bound) joins the seven s70 left it.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_binding_active_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_binding_active_kind_shape CHECK (
    (kind IN ('principal_relation_asserted','principal_role_bound','principal_key_bound',
              'principal_competence_granted',
              'principal_standing_declared','principal_suspended',
              'principal_scope_bound','principal_stamp_bound'))
    = (principal_binding_active IS NOT NULL));

COMMENT ON CONSTRAINT principal_binding_active_kind_shape ON :"schema".ledger IS
  'kernel/lineage/s72-stamp-binding-conjunct.sql: widens s70''s seven-kind licensing of the
   identity/value discriminator to EIGHT -- principal_stamp_bound joins the seven s70 left it
   (true = a fresh stamp-binding assertion, stamp_binding_agent mandatory; false = a retraction,
   restating BOTH principal_subject and stamp_binding_agent -- both identity fields, per Element
   2''s own header, unlike s70''s optional-value-field siblings).';

-- ============================================================================================
-- ELEMENT 3 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 105 COLUMNS (the one new
-- column appended in catalog ordinal order, before the predecessor link; base body = s70's own
-- text, byte-identical above the one appended line -- s71 does not re-issue this function,
-- verified by grep before authoring this delta).
-- prior-body-sha256: ebb75d46e430e56847d18842af01f33a593151e6a7b7b92838f2592337efd92e (s70-scope-binding.sql)
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
      hashfield(array_to_string(r.scope_surfaces, ',')),
      hashfield(r.scope_exclusions::text),
      hashfield(r.scope_disclosure_mode),
      -- s72: the one new column, appended last before the predecessor link.
      hashfield(r.stamp_binding_agent),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 4 -- THE TWO COLUMN-COMPLETE VIEWS, +1 APPENDED (the s20 lesson).
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
       l.scope_surfaces, l.scope_exclusions, l.scope_disclosure_mode,
       l.stamp_binding_agent
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
       l.scope_surfaces, l.scope_exclusions, l.scope_disclosure_mode,
       l.stamp_binding_agent
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 5 -- principal_stamp_bindings: THE FIRST NEW DERIVED VIEW (security_invoker, ledger_
-- current-factored, filters active=true -- the s41 D-5 shape, one kind further). Literal
-- template, quoted (kernel/lineage/s41-principal-bindings-and-relations.sql lines 636-641):
--   CREATE OR REPLACE VIEW :"schema".principal_role_bindings
--       WITH (security_invoker = true) AS
--   SELECT lc.principal_subject AS subject, lc.principal_role_name AS role_name,
--          lc.actor AS bound_by, lc.ts AS at, lc.id AS row_id
--   FROM   :"schema".ledger_current lc
--   WHERE  lc.kind = 'principal_role_bound' AND lc.principal_binding_active;
-- Unlike principal_role_bindings/principal_scopes (ONE governing row per subject -- s31's uniform
-- retraction supersession), a subject may hold SEVERAL simultaneous rows here (Element 2's own
-- header: multiple stamp bindings per principal are representable) -- this view returns ALL of a
-- subject's currently in-force bindings, one row per (subject, stamp_binding_agent) pair last
-- asserted active-and-unsuperseded; Element 10's own conjunct (c) check reads it with an EXISTS
-- over (subject, stamp_binding_agent), never assuming at most one row.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".principal_stamp_bindings
    WITH (security_invoker = true) AS
SELECT lc.principal_subject AS subject, lc.stamp_binding_agent AS agent,
       lc.actor AS bound_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_stamp_bound' AND lc.principal_binding_active;

COMMENT ON VIEW :"schema".principal_stamp_bindings IS
  'kernel/lineage/s72-stamp-binding-conjunct.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-
   FLOW-SPEC.md sec5 item 5): every CURRENTLY in-force (unsuperseded, active) principal_stamp_
   bound row -- mirrors principal_role_bindings'' own shape one kind over, but MULTI-ROW per
   subject (a principal may bind several stamp_agent strings simultaneously, Element 2''s own
   header). A subject with NO row here can satisfy no nominated act class''s stamp-binding
   conjunct regardless of role/chain entitlement -- the fail-safe direction (this NARROWS who may
   act in a nominated class, never widens).';

GRANT SELECT ON :"schema".principal_stamp_bindings TO :"role";

-- ============================================================================================
-- ELEMENT 6 -- stamp_binding_classes: THE SECOND NEW DERIVED VIEW (mirrors s60 Element 4's
-- entitlement_class_roles shape exactly, one configuration axis over -- REUSES entitlement_act_
-- class, Element 2 above, rather than a second "which class" column). Literal template, quoted
-- (kernel/lineage/s60-entitlement-enforcement.sql lines 367-375):
--   CREATE OR REPLACE VIEW :"schema".entitlement_class_roles
--       WITH (security_invoker = true) AS
--   SELECT lc.entitlement_act_class AS act_class, lc.principal_role_name AS role_name,
--          lc.actor AS configured_by, lc.ts AS at, lc.id AS row_id
--   FROM   :"schema".ledger_current lc
--   WHERE  lc.kind = 'entitlement_class_configured'
--     AND  lc.id = (SELECT max(lc2.id) FROM :"schema".ledger_current lc2
--                   WHERE lc2.kind = 'entitlement_class_configured'
--                     AND lc2.entitlement_act_class = lc.entitlement_act_class);
-- Same max-id-per-key shape (kernel.principal_role's own pre-s45 precedent): fresh-assert and
-- rotation only, no de-configuration path in v1 (a de-configuration would RELAX an existing
-- refusal, out of the fail-safe-additive class this delta ships under -- the identical LIMIT
-- s60 Element 1 already discloses for its own sibling configuration kind).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".stamp_binding_classes
    WITH (security_invoker = true) AS
SELECT lc.entitlement_act_class AS act_class,
       lc.actor AS configured_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'stamp_binding_class_configured'
  AND  lc.id = (SELECT max(lc2.id) FROM :"schema".ledger_current lc2
                WHERE lc2.kind = 'stamp_binding_class_configured'
                  AND lc2.entitlement_act_class = lc.entitlement_act_class);

COMMENT ON VIEW :"schema".stamp_binding_classes IS
  'kernel/lineage/s72-stamp-binding-conjunct.sql (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-
   FLOW-SPEC.md sec5 item 5): the governing stamp_binding_class_configured row per act-class
   token -- the LATEST unsuperseded nomination event for that class (rotation = a newer row; no
   de-configuration path in v1, mirroring entitlement_class_roles'' own shape). An act class
   ABSENT from this view is NOT NOMINATED -- conjunct (c) (Element 10) is a total no-op for it,
   the fail-safe default (EMPTY by shipped default -- no birth-sequence act of this delta''s own,
   this file''s own header CORRECTION 3).';

GRANT SELECT ON :"schema".stamp_binding_classes TO :"role";

-- ============================================================================================
-- ELEMENT 7 -- entitlement_act_class_of RE-ISSUED (s70's own body, verified unedited above the
-- two new branches appended last, before the final RETURN NULL). Every existing branch (through
-- the principal_scope_bound branch) is BYTE-IDENTICAL to s70's text.
-- prior-body-sha256: 5bf573ea53abfb5ecfc6ce26bef20598c70f32bea1b995dbcc829bdefe03c029 (s70-scope-binding.sql)
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
  IF r.kind = 'principal_scope_bound' THEN
    RETURN 'scope_binding';
  END IF;
  -- s72 (kernel/lineage/s72-stamp-binding-conjunct.sql, design/FABLE-ACCESS-CONTROL-AND-
  -- INFORMATION-FLOW-SPEC.md sec5 item 5): a principal_stamp_bound row (fresh assertion OR
  -- retraction -- "kind, not fresh-vs-supersedes, decides the class", the identical uniform
  -- treatment every sibling token above already carries) is its own act class, stamp_binding --
  -- the TENTH authority-bearing token. A stamp_binding_class_configured row (nominating which
  -- OTHER class this conjunct governs) is its own act class, stamp_binding_class_configured --
  -- the ELEVENTH, self-protecting exactly as entitlement_class_configured protects ITS OWN
  -- configuration surface (s60's own header-surfaced addition, one axis over).
  IF r.kind = 'principal_stamp_bound' THEN
    RETURN 'stamp_binding';
  END IF;
  IF r.kind = 'stamp_binding_class_configured' THEN
    RETURN 'stamp_binding_class_configured';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of(:"schema".ledger) IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (AMENDMENT), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED), kernel/lineage/
   s70-scope-binding.sql (WIDENED: scope_binding), kernel/lineage/
   s72-stamp-binding-conjunct.sql (WIDENED: stamp_binding, stamp_binding_class_configured, the
   tenth and eleventh tokens): the act-class token a CANDIDATE ledger row belongs to by its OWN
   kind/attributes, or NULL if it belongs to none. ELEVEN tokens as of s72.';

-- ============================================================================================
-- ELEMENT 8 -- entitlement_act_class_of_target RE-ISSUED (s70's own body, verified unedited
-- above the two new branches appended last). Symmetric with Element 7 -- a principal_stamp_bound
-- OR stamp_binding_class_configured row being SUPERSEDED is itself an in-force member of its own
-- class, closing the SAME cross-kind severance vessel s62 round 2 closed generally, extended two
-- tokens further.
-- prior-body-sha256: a089418948fd4ea3e6d90e598ace2c642cb1fe0d4ecb37006a8eba1bd83ba457 (s70-scope-binding.sql)
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
  IF p_kind = 'principal_scope_bound' THEN
    RETURN 'scope_binding';
  END IF;
  -- s72: a principal_stamp_bound / stamp_binding_class_configured TARGET row is, by its own
  -- identity, an in-force member of its own class -- no further indirection needed (mirrors every
  -- sibling branch above, s62 round 2's own "classify the target as if fresh" rule).
  IF p_kind = 'principal_stamp_bound' THEN
    RETURN 'stamp_binding';
  END IF;
  IF p_kind = 'stamp_binding_class_configured' THEN
    RETURN 'stamp_binding_class_configured';
  END IF;
  RETURN NULL;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_act_class_of_target(text, text, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (base), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED), kernel/lineage/
   s70-scope-binding.sql (WIDENED: scope_binding), kernel/lineage/
   s72-stamp-binding-conjunct.sql (WIDENED: stamp_binding, stamp_binding_class_configured): the
   act-class token a row belongs to, judged purely from four of its own columns, one hop only.
   principal_stamp_bound/stamp_binding_class_configured targets are now protected against the
   SAME cross-kind severance vessel every other protected class already is.';

-- ============================================================================================
-- ELEMENT 9 -- entitlement_enforce_class RE-ISSUED (s70's own body, verified unedited above the
-- widened authority-bearing set). TWO widenings: the authority-bearing set gains the TENTH and
-- ELEVENTH tokens, stamp_binding and stamp_binding_class_configured -- conjunct (b), unconditional,
-- exactly like every other token (the task's own commission: "a scope binding is refused unless
-- the binder passes the entitlement conjuncts -- it IS authority-bearing"; a stamp binding and its
-- own configuration surface are the identical shape, one mechanism over). Both are DELIBERATELY
-- LEFT OUT of the default conjunct-(a) role map AND (this delta's own header CORRECTION 3) out of
-- the default STAMP-BINDING-CONJUNCT nomination set (stamp_binding_classes, Element 6) -- a
-- deployment wanting either a role requirement (conjunct a) or a stamp-binding requirement
-- (conjunct c, Element 10) on stamp-binding acts THEMSELVES configures it explicitly, exactly as
-- s62's own text states for its sibling token.
-- prior-body-sha256: 29856e96a593fa120c953e0d3aa2ed4de3a26c8582ebdd07a0d26756fdff3de4 (s70-scope-binding.sql)
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
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/s64/s70/s72, factored acceptance predicate conjunct a, %) — act class ''%'' requires an in-force role binding named ''%'' (this world''s configured entitlement map, see entitlement_class_roles); actor % holds no such binding. Remedy: a principal who ALREADY holds the ''%'' role (or genesis-chain authority) binds it to you: ./autoharn led principal bind-role <your-principal-name> "%" (kernel/lineage/s41-principal-bindings-and-relations.sql), then retry this act. See design/USER-RECIPES-FAQ.md''s entitlement-enforcement recipe for the worked example (kernel/lineage/s60-entitlement-enforcement.sql).', p_source, p_act_class, v_required_role, p_actor, v_required_role, v_required_role;
    END IF;
  END IF;

  -- s72: ELEVEN tokens (stamp_binding, stamp_binding_class_configured join the nine s70 left).
  v_authority_bearing := p_act_class IN (
      'principal_registered', 'principal_role_bound', 'standing_lifecycle',
      'milestone_closure', 'gate_edge_supersession', 'entitlement_class_configured',
      'delegation_lifecycle', 'independent_verification_delegation',
      'scope_binding', 'stamp_binding', 'stamp_binding_class_configured');
  IF v_authority_bearing THEN
    SELECT principal_authority_chain_reaches_genesis_scoped(p_actor, p_act_class) INTO v_reaches;
    IF NOT v_reaches THEN
      RAISE EXCEPTION 'Ledger policy: entitlement refused (s60/s62/s64/s70/s72, factored acceptance predicate conjunct b, %) — act class ''%'' is authority-bearing (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §1.1b; design/FABLE-PRINCIPAL-STAMPS-SPEC.md §2.3; design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md §1b/§5 for scope_binding/stamp_binding); actor %''s authority chain (transitive reachability over in-force acts-for/dispatched-by relations, honoring every hop''s expiry/scope conditions, kernel/lineage/s64-principal-stamps-delegation-conditions.sql) does not reach this world''s genesis principal for this act class. Remedy: this is NOT a write you can perform on yourself — have your DELEGATOR run, on your behalf: ./autoharn led principal relate <delegator-principal-name> acts-for <a-principal-already-chain-connected-to-genesis>, covering you, and (if any upstream edge is scoped) confirm this act class is among that edge''s delegation_scope_classes — or have a severed/expired link repaired (suspension/revocation/expiry severs a chain PROSPECTIVELY only; past accepted acts through that link stay credited, kernel/lineage/s45-standing-lifecycle.sql''s I5 asymmetry).', p_source, p_act_class, p_actor;
    END IF;
  END IF;
END; $fn$;

COMMENT ON FUNCTION :"schema".entitlement_enforce_class(bigint, text, text) IS
  'kernel/lineage/s62-delegation-lifecycle-gating.sql (base), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (WIDENED), kernel/lineage/
   s70-scope-binding.sql (WIDENED: scope_binding), kernel/lineage/
   s72-stamp-binding-conjunct.sql (WIDENED: stamp_binding, stamp_binding_class_configured, the
   tenth/eleventh authority-bearing tokens): the two-conjunct acceptance predicate (a/b). A no-op
   when act_class IS NULL. Conjunct (c), the stamp-binding requirement itself, is a SEPARATE check
   inside validate_entitlement (Element 10) -- not folded into this function, since (c) is keyed
   on the NOMINATED-class configuration (stamp_binding_classes), an axis orthogonal to (a)''s
   role map and (b)''s hardcoded authority-bearing set.';

-- ============================================================================================
-- ELEMENT 10 -- validate_entitlement RE-ISSUED (s64's own body, the TRUE lineage head for this
-- trigger -- verified by grep, s65..s71 none of them touch it, s70 Element 9's own header stating
-- explicitly it re-issues zero trigger bodies). UNLIKE s70/s71, THIS delta DOES re-issue this
-- trigger body: conjunct (c), the stamp-binding requirement itself, is irreducibly a NEW check on
-- the ledger row being written (whether NEW's own stamp columns satisfy a NOMINATED class's
-- requirement) -- no existing call site can absorb it the way s70's ninth token rode the EXISTING
-- entitlement_enforce_class call graph unchanged. Added AFTER the existing three PERFORM calls
-- (candidate class a/b, target class a/b, s64's delegation-conditions c/d) -- a fourth, INDEPENDENT
-- conjunct, gated on v_act_class (the CANDIDATE's own class) ONLY, never the target class -- the
-- IDENTICAL "candidate-only" choice s64 Element 12 already made for ITS OWN two conjuncts (that
-- header's own words: "never also called for v_target_act_class... not meaningful for a row being
-- superseded" -- true here too: a supersession TARGET's own stamp-binding requirement was already
-- satisfied when THAT row was originally accepted; severing it is separately gated by conjunct b
-- via entitlement_act_class_of_target, unaffected by this delta).
--
-- WHY STAMP_VERIFIED, NOT MERE STRING EQUALITY (the hazard this delta's own builder caught in
-- reach, CLAUDE.md's engineering-responsibility corollary): s17's set_stamp trigger sets
-- NEW.stamp_agent from the app.vendor_agent GUC UNCONDITIONALLY, regardless of whether the
-- accompanying HMAC validates (kernel/lineage/s17-stamp-mechanism.sql: "NEW.stamp_agent := a"
-- happens before the stamp_valid() branch; only stamp_verified distinguishes a genuine, HMAC-
-- checked stamp from a claimed-but-unauthenticated one). Matching stamp_binding_agent against
-- NEW.stamp_agent ALONE, without also requiring NEW.stamp_verified, would let a forger who merely
-- knows a bound agent string (e.g. the well-known literal 'main') claim it with a bogus or absent
-- HMAC and be ACCEPTED -- defeating the entire "authenticated input" point of this mechanism
-- (this delta's own header WHY paragraph). Conjunct (c) below therefore requires BOTH:
-- NEW.stamp_verified (the HMAC genuinely validated) AND an in-force principal_stamp_bindings row
-- naming NEW.actor bound to NEW.stamp_agent exactly.
-- prior-body-sha256: 7edad02e003173b07f0299aa870681712a104f6f36aab72db7c2bf9bd034d7a1 (s64-principal-stamps-delegation-conditions.sql)
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
  v_stamp_nominated boolean;
  v_stamp_bound boolean;
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

  -- s64: the depth-budget/must-countersign conjuncts, CANDIDATE class only.
  PERFORM entitlement_enforce_delegation_conditions(
      NEW.actor, v_act_class, NEW.principal_object, NEW.signature_symmetry_witness);

  -- s72 (kernel/lineage/s72-stamp-binding-conjunct.sql, design/FABLE-ACCESS-CONTROL-AND-
  -- INFORMATION-FLOW-SPEC.md sec5 item 5): CONJUNCT (c), the stamp-binding requirement, CANDIDATE
  -- class only (this element's own header explains why, mirroring s64 Element 12's identical
  -- choice). A no-op unless v_act_class is itself among the world's NOMINATED classes
  -- (stamp_binding_classes, Element 6) -- the fail-safe default, empty by shipped default.
  IF v_act_class IS NOT NULL THEN
    SELECT EXISTS (SELECT 1 FROM stamp_binding_classes WHERE act_class = v_act_class)
      INTO v_stamp_nominated;
    IF v_stamp_nominated THEN
      SELECT (COALESCE(NEW.stamp_verified, false)
              AND EXISTS (SELECT 1 FROM principal_stamp_bindings psb
                          WHERE psb.subject = NEW.actor AND psb.agent = NEW.stamp_agent))
        INTO v_stamp_bound;
      IF NOT v_stamp_bound THEN
        RAISE EXCEPTION 'Ledger policy: entitlement refused (s72, factored acceptance predicate conjunct c, %) — act class ''%'' is nominated for the stamp-binding conjunct (this world''s configured stamp_binding_classes, design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md sec5 item 5); this write''s own interception stamp (verified=%, agent=%) does not resolve to an in-force principal_stamp_bound row naming actor % as bound to that agent string. Remedy: an unstamped or unverified write can never satisfy this conjunct — route the write through the intercepted path; a verified write from an agent this actor has not bound needs the actor''s own genesis-chained delegator to bind it first: ./autoharn led ledger-write --kind principal_stamp_bound --principal-subject % --stamp-binding-agent <the-agent-string-this-invocation-actually-stamps-as> --principal-binding-active true (kernel/lineage/s72-stamp-binding-conjunct.sql). See this delta''s own header CORRECTION 1/2 for which act classes ''main''-only binding actually secures.', v_act_class, v_act_class, COALESCE(NEW.stamp_verified, false), NEW.stamp_agent, NEW.actor, NEW.actor;
      END IF;
    END IF;
  END IF;

  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_entitlement ON :"schema".ledger;
CREATE TRIGGER validate_entitlement BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_entitlement();

COMMENT ON FUNCTION :"schema".validate_entitlement() IS
  'kernel/lineage/s60-entitlement-enforcement.sql (base), kernel/lineage/
   s62-delegation-lifecycle-gating.sql (round 2), kernel/lineage/
   s64-principal-stamps-delegation-conditions.sql (depth-budget/must-countersign conjuncts),
   kernel/lineage/s72-stamp-binding-conjunct.sql (conjunct c, the stamp-binding requirement,
   candidate class only, gated on stamp_binding_classes'' own nomination): the factored acceptance
   predicate, now FIVE conjuncts wide for a delegation-classified AND stamp-nominated candidate
   act (a/b via entitlement_enforce_class, c/d via entitlement_enforce_delegation_conditions, the
   stamp-binding conjunct inline here), two conjuncts wide (a/b only) for a supersession TARGET''s
   class. Refusals journal as write_refused rows via the s43 boundary, unchanged.';

-- ============================================================================================
-- ELEMENT 11 -- GRANTS (belt-and-braces; CREATE OR REPLACE VIEW preserves grants on
-- ledger_current/countersigned_in_force -- s21's own additive-column-order idiom, re-verified
-- here). principal_stamp_bindings' and stamp_binding_classes' own GRANT SELECT are issued at
-- Elements 5/6, immediately after their own CREATE OR REPLACE -- kept there rather than
-- duplicated here, matching s36/s60/s70's own single-grant-site idiom.
-- ============================================================================================

-- ============================================================================================
-- HISTORY: safe -- per-mechanism grounds:
--   * ledger_kind_check re-issued WIDER (additive vocabulary: every pre-existing kind''s legality
--     unchanged; principal_stamp_bound/stamp_binding_class_configured are disjoint from the
--     thirty-four existing members and are BORN in this delta -- no pre-existing row can carry
--     either).
--   * ONE new nullable no-DEFAULT column (stamp_binding_agent), kind-scoped (mandatory on BOTH a
--     fresh assert and a retraction of principal_stamp_bound -- an IDENTITY field, Element 2''s
--     own header) by a CHECK that validates vacuously on every pre-existing row (no pre-existing
--     row can carry the new kind).
--   * entitlement_act_class_kind_shape re-issued WIDER (additive on both sides of the iff:
--     entitlement_class_configured keeps its exact prior legality; stamp_binding_class_configured
--     joins the licensed set -- the s60/s41 precedent for widening an existing two-way CHECK to a
--     second/third kind).
--   * principal_subject_kind_shape / principal_binding_active_kind_shape re-issued WIDER
--     (additive on both sides of each iff: every pre-existing licensed kind keeps its EXACT prior
--     legality; principal_stamp_bound joins the licensed set -- the s41/s45/s60/s61/s70 precedent
--     for widening an existing two-way CHECK to one more kind, applied a sixth/seventh time).
--   * entitlement_act_class_of / entitlement_act_class_of_target / entitlement_enforce_class
--     re-issued: each gains exactly TWO new branches/tokens, appended LAST, with every existing
--     branch''s text byte-identical to s70''s own (Elements 7/8/9''s own `-- prior-body-sha256:`
--     lines bind this mechanically, gates/lineage_reissue_lineage.py CHECK 2) -- new-refusal-only:
--     no candidate or target row classified by any EXISTING branch before this delta changes its
--     classification; the only NEW classifications are for kinds (principal_stamp_bound,
--     stamp_binding_class_configured) that did not exist before this delta.
--   * validate_entitlement IS re-issued (unlike s70/s71) -- Element 10''s own header explains why
--     this delta cannot ride the "zero trigger bodies touched" shape; the addition is new-refusal-
--     only (conjunct (c) fires ONLY for a candidate whose act class is BOTH non-NULL AND present
--     in stamp_binding_classes -- a view that is EMPTY by shipped default, so no pre-existing
--     write, and no write of any kind on ANY world that has never written a stamp_binding_class_
--     configured row, is newly refused by this delta''s mere existence).
--   * compute_row_hash/ledger_current/countersigned_in_force re-issues are s42''s law,
--     self-applied, pure column-list appends (s20 lesson), byte-identical to the s28..s70
--     precedent.
--   * principal_stamp_bindings/stamp_binding_classes are BRAND NEW views with no pre-existing
--     reader.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: (1) a principal_stamp_bound row (binding a registered principal to a
--     stamp_agent identity string, or a retraction restating that identity) is accepted only when
--     its writer passes the SAME two-conjunct entitlement predicate every other authority-bearing
--     act class already passes; a supersession NAMING a live principal_stamp_bound OR
--     stamp_binding_class_configured row as its target is gated identically, on the SAME class,
--     regardless of the superseding row''s own kind. (2) For every act class the world has
--     NOMINATED (a fresh stamp_binding_class_configured row naming it, stamp_binding_classes),
--     every future candidate write of that class is ADDITIONALLY accepted only when its own
--     interception stamp is VERIFIED and its (actor, stamp_agent) pair resolves to an in-force
--     principal_stamp_bindings row -- an unstamped, unverified, or unbound write in a nominated
--     class is refused, typed, journaled. An act class ABSENT from stamp_binding_classes is
--     UNAFFECTED by conjunct (c) -- EMPTY by shipped default, the fail-safe posture.
--   - QUANTIFICATION UNIVERSE:
--       ACT CLASSES gated by conjunct (b), the hardcoded authority-bearing set: ELEVEN tokens as
--         of s72 (the six s60 tokens, delegation_lifecycle [s62], independent_verification_
--         delegation [s64], scope_binding [s70], stamp_binding and stamp_binding_class_configured
--         [s72]) -- enumerated once, inside entitlement_enforce_class (Element 9), never a second
--         copy. Every OTHER kind is UNTOUCHED by this delta.
--       ACT CLASSES gated by conjunct (a): unchanged POLICY set (whichever tokens
--         entitlement_class_roles currently governs); stamp_binding/stamp_binding_class_
--         configured are NOT in the default map (Element 9''s own note, mirroring s62/s70''s
--         identical choice) -- no birth-sequence act of this delta''s own.
--       ACT CLASSES gated by conjunct (c), THE STAMP-BINDING CONJUNCT ITSELF (the axis this delta
--         adds): whichever tokens stamp_binding_classes currently NOMINATES -- EMPTY by shipped
--         default (this file''s own header CORRECTION 3), a deployment configures it by writing a
--         fresh stamp_binding_class_configured row per nominated class. This file''s own header
--         CORRECTION 2 discloses PRECISELY which of the pre-existing tokens are safe to nominate
--         under 'main'-only binding (principal_registered/principal_role_bound/standing_lifecycle/
--         entitlement_class_configured, plus this delta''s own stamp_binding/stamp_binding_class_
--         configured) and which are NOT (milestone_closure/gate_edge_supersession -- routinely
--         written by dispatched, ephemeral-stamped subagents whose agent id cannot be bound in
--         advance).
--       KINDS/COLUMNS: ONE new column (stamp_binding_agent), licensed ONLY on principal_stamp_
--         bound rows (mandatory both active and inactive, an IDENTITY field unlike s70''s optional
--         value fields); entitlement_act_class_kind_shape widened to a third kind (two-way);
--         principal_subject_kind_shape/principal_binding_active_kind_shape widened by ONE kind
--         each (both two-way). No other column touched.
--       VIEWS: principal_stamp_bindings and stamp_binding_classes are new, factor through
--         ledger_current exclusively (no raw `ledger` reference of their own -- classify clean
--         under gates/ledger_reader_allowlist.py with no allowlist entry needed); ledger_current/
--         countersigned_in_force re-issued (+1 column, Element 4); no other pre-existing view
--         touched.
--       FUNCTIONS: entitlement_act_class_of, entitlement_act_class_of_target,
--         entitlement_enforce_class RE-ISSUED (each widened by exactly two branches/tokens, no
--         existing branch''s text edited -- see HISTORY above); compute_row_hash re-issued
--         (append-only, s42''s law).
--       TRIGGERS: ONE re-issued body -- validate_entitlement (Element 10), the FIRST re-issue of
--         this trigger''s body since s64; gains conjunct (c), new-refusal-only, gated on a view
--         that is empty by shipped default (HISTORY''s own note).
--       ENGINE: NO ASP twin ships in this delta (mirrors s70''s own disclosed choice) -- reaches_
--         genesis/1 and reaches_genesis_scoped/2 remain generic over act class (s62/s64/s70''s own
--         identical claim, re-verified one token further for conjuncts a/b); conjunct (c) itself
--         (the stamp-binding requirement) has NO ASP predicate at all -- flagged loudly as a
--         follow-on for the engine twin, per the commission''s own instruction, rather than hacked
--         in under this build''s own time budget (UNEXERCISED, named below, not silently claimed
--         AGREE for that family).
--       GATES: gates/kind_shape_manifest_gate.py (CHAIN += s72, three new MANIFEST rows --
--         stamp_binding_agent, and the widened principal_subject/principal_binding_active/
--         entitlement_act_class tuples), gates/ledger_reader_allowlist.py (CHAIN += s72, zero new
--         ALLOWLIST entries), gates/fixture_census.py (REGISTRY += s72), gates/
--         lineage_reissue_lineage.py (mechanical, no registry edit -- this file''s own five
--         `-- prior-body-sha256:` lines are what it checks), gates/lineage_chain_coverage.py
--         (this delta''s own commission: report the refusal verbatim rather than wiring s72 into
--         bootstrap/new-project.sh''s LINEAGE_CHAIN narrative ahead of its actual birth-chain
--         entry -- see this delta''s own build report for the observed text; UNLIKE s70/s71, this
--         build DID add the narrative-home string per the s71 precedent and this file''s own
--         commission carve-out -- see the LINEAGE_CHAIN edit alongside this commit and this
--         delta''s own build report for the gate''s observed pass/refuse status) -- all in this
--         same commit.
--   - DENOMINATION: entitlement in in-force EVENTS (role bindings, acts-for/dispatched-by
--     relations, entitlement_class_configured/stamp_binding_class_configured rows), computed
--     fresh at act time, never cached (unchanged from s60/s62/s64/s70); stamp-binding identity in
--     the ledger''s OWN vocabulary (a stamp_agent string, s17''s own kernel-injected identity
--     field), never row-id arithmetic or byte offsets; the nominated-class vocabulary a kernel-
--     computed act-class string (entitlement_act_class_of''s own output), never a writer assertion.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape (this delta only ADDS refusals and read-only derived surface -- two new kinds, one new
-- nullable column, one widened existing CHECK to a third kind, two widened existing CHECKs one
-- kind further each, three widened existing functions each gaining two new branches/tokens with
-- no existing branch''s text edited, one re-issued trigger body whose addition is new-refusal-only
-- and gated on an empty-by-default view, two new derived views; nothing existing is relaxed, no
-- existing CHECK narrowed, no existing grant revoked) -- per the ratified spec''s own framing
-- (design/FABLE-ACCESS-CONTROL-AND-INFORMATION-FLOW-SPEC.md, ratification row 639, mechanism
-- roster item 5 naming this exact delta) and row 601''s own adjudication (ADOPT-AS-DESIGN-INPUT,
-- corrections required and discharged above), this delta rides the 2026-07-09 class rule,
-- scratch-witnessed both polarities on this same commit''s own fixture, not routed for a separate
-- maintainer ratification question beyond the mechanism-level ratification row 639 already
-- records -- stated here for the record, matching s60/s62/s64/s70''s own disclosure convention.
--
-- LIMITS (pre-registered, matching every prior delta''s own disclosure convention):
--   - THE EPHEMERAL-DISPATCHED-AGENT FORK (this file''s own header CORRECTION 2, restated as a
--     LIMIT): nominating milestone_closure or gate_edge_supersession under this conjunct, with
--     only 'main'-bound principals available, refuses every dispatched subagent's legitimate
--     close of the work item it was assigned -- a real, disclosed friction cost this build does
--     NOT resolve. A dispatch-time/first-verified-use binding path (row 601's own second option)
--     is a NAMED, NOT-BUILT follow-on -- reported, per row 601's own STOP-and-report instruction,
--     rather than invented under this build's own time budget or silently punted by narrowing the
--     mechanism's own vocabulary.
--   - BINDING IS ON stamp_agent ALONE, NEVER THE (stamp_session, stamp_agent) PAIR (this file's
--     own header CORRECTION 1) -- admits every governed session's own instance of the bound agent
--     string (e.g. every session's 'main' thread), single-trust-domain semantics, disclosed as
--     such, NOT the s21 cross-session-distinctness identity.
--   - NO IDENTITY-CONTINUITY GUARD in validate_supersession_target for principal_stamp_bound rows
--     (contrast s45's guard for the three standing-lifecycle kinds) -- a superseding principal_
--     stamp_bound row may legally name a DIFFERENT principal_subject than the row it supersedes;
--     the target-class entitlement check (Element 8/9) still requires the SUPERSEDING actor to be
--     stamp_binding-entitled, but does not require subject continuity -- the SAME disclosed limit
--     s41/s70's own bindings already carry, one mechanism further.
--   - stamp_binding_agent vocabulary is free text, kernel-unchecked against any live hook
--     configuration or observed session -- binding a principal to an agent string that never
--     actually appears on any future write is legal to write, simply never matches (the s36
--     free-text-policy-token precedent, restated here one mechanism further).
--   - Conjunct (c) checks the CANDIDATE's own class only, never the target class (Element 10's own
--     header) -- the identical choice s64 Element 12 made for its own two conjuncts, restated here
--     rather than re-argued.
--   - Trigger/CHECK refusals bind the granted role's ordinary INSERT path only; the schema-
--     owner/superuser bypass stands -- per this file's own header CORRECTION 4, narrowed by the
--     S2b split to a BIRTH-ONLY act (the migration/apply identity), never a standing runtime
--     exposure for a served principal, once a world has split.
--   - NO ASP TWIN for the stamp_binding/stamp_binding_class_configured act classes, and NO
--     predicate at all for conjunct (c) itself -- named above (CLOSURE STATEMENT's ENGINE line)
--     as a possible follow-on, UNEXERCISED (not claimed AGREE).
--   - In a solo world, every stamp-binding fact is written by machinery the one operator
--     controls -- complete and attributed, not adversarially independent (s17's own honesty,
--     inherited, restated here one mechanism further).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s71):
--   VALIDATE (reachable throwaway): apply the FULL s15..s71 chain (see kernel/lineage/
--   s71-row-level-scope-policies.sql's own VALIDATE block for the complete -f list, itself s70's
--   VALIDATE block +1), THEN -f s72-stamp-binding-conjunct.sql (genesis seed per s26; discharge
--   the s40/s43/s60 birth sequence before exercising any stamp-binding act, exactly as s60/s62/
--   s64/s69/s70's own VALIDATE notes require).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world's birth chain automatically via bootstrap/new-project.sh's
--   --new-world glob-driven apply list the moment a tree carrying it is scaffolded from; the
--   hand-maintained CLASSIC-scaffold LINEAGE_CHAIN narrative list is a SEPARATE, later maintainer
--   integration act -- taken in THIS SAME commit (the s71 precedent, its own header: "taken here
--   in THIS SAME commit, not deferred"), never a bootstrap/new-project.sh apply-list edit (this
--   delta's own commission: do not touch bootstrap templates beyond that one narrative string).
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP/CREATE TRIGGER).
-- ============================================================================================
