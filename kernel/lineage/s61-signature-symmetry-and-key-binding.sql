-- s61 SIGNATURE SYMMETRY AND KEY-BINDING PROOF OF POSSESSION (design/
-- FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2, v1.1 -- "signature symmetry and the key binding
-- (serving/verbs, small)" -- items 1 and 3 of that section's three rows; item 2 [verify against
-- the s41 key binding] is verb-side only, shipped in bootstrap/templates/verify-commission.tmpl
-- this same commit, no kernel touch -- see this file's own WHY section for the derivation of
-- which of the three items needed a kernel delta at all). FAIL-SAFE-ADDITIVE (CLAUDE.md
-- 2026-07-09 class rule, the SAME class s60 rode): this delta ONLY ADDS refusals -- two new
-- kinds, four new columns, one widened existing CHECK (principal_binding_active_kind_shape's
-- sibling -- see below), two new BEFORE INSERT trigger members' worth of NEW refusal branches
-- (one brand-new trigger, validate_signature_witness; one re-issue each of
-- validate_principal_binding and validate_supersession_target, both re-issues ADDING a branch,
-- never touching an existing one), and read-only derived views/functions; nothing existing is
-- relaxed, no existing CHECK narrowed, no existing trigger's PRE-EXISTING branch text edited.
-- Sonnet-built per the standing delegation contract, from the ratified spec (design/
-- FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md, rows 1379/1380's ratification basis) and design/
-- CONSULT-WORK-GATING-SHAPE-2026-07-26.md §0.4/§0.5/§B.2 (the reach of the GPG layer and the
-- three-property authenticity decomposition this delta discharges the two remaining v1.1 rows
-- of).
--
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s60 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second copy of any existing mechanism (ADR-0012 P1): signature symmetry extends s45's OWN
-- single home for supersession discipline (validate_supersession_target) rather than minting a
-- parallel trigger -- the exact precedent s45's own header names for why it re-issued s43's
-- trigger rather than adding a fourth; key-binding proof-of-possession extends s41's OWN single
-- home for principal_key_bound-specific refusals (validate_principal_binding) for the identical
-- reason. The two new well-formedness checks (a commission_signature_verified row's target must
-- itself be a commission; a signature_symmetry_witness must itself be a
-- commission_signature_verified row) are a THIRD, disjoint-concern trigger,
-- validate_signature_witness -- the s48/s52 idiom ("a single-purpose write-boundary trigger
-- added beside the existing validate_* family... because this check is orthogonal to every one
-- of [the others'] leaf concerns and shares no state with any of them").
--
-- PREREQUISITE: this delta REQUIRES s60 (kernel/lineage/s60-entitlement-enforcement.sql) applied
-- first -- it re-issues compute_row_hash/ledger_current/countersigned_in_force in the EXACT
-- 88-column shape s60 left them (s60 added one column over s59's 87), re-issues
-- ledger_kind_check in the exact thirty-one-member shape s60 left it (widened here by two), and
-- re-issues validate_principal_binding (s41's body, UNCHANGED by s45/s60) and
-- validate_supersession_target (s45's body, UNCHANGED by s60) -- every one of those objects must
-- already exist in its s60-head shape. Applying this file on a pre-s60 kernel fails loudly at
-- CREATE OR REPLACE VIEW/FUNCTION time (a column or relation referenced does not exist), the
-- correct, disclosed failure mode, matching every prior PREREQUISITE precedent. THE HEAD-BODY
-- RULE (s45's own standing instruction, carried here verbatim): at this delta's authoring the
-- lineage head is s60 (kernel/lineage/'s own directory listing, confirmed by the builder before
-- authoring -- s58/s59/s60 exist as authored, scratch-witnessed files, none yet wired into
-- bootstrap/new-project.sh's LINEAGE_CHAIN, a PRE-EXISTING condition this delta neither creates
-- nor is required to close, named per s60's own precedent for the identical disclosure). This
-- file's re-issued bodies are quoted, verified, against the s60 head text.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are), THE ENFORCEMENT-HOME DERIVATION FOR EACH OF THE SPEC'S THREE ROWS (commissioned to be
-- derived, not assumed):
--
--   ITEM 1 (SIGNED supersession symmetry) -- KERNEL-SIDE, because the write BOUNDARY is the
--   only surface every writer, `led`-driven or a direct-psql caller through the SECURITY
--   DEFINER boundary functions (s43), must pass through. A verb-side-only check (teach the
--   `led` CLI to refuse an unsigned supersession of a signed act before it ever calls
--   kernel.ledger_write) would be SILENTLY, STRUCTURALLY bypassable by any caller that skips the
--   CLI and calls the boundary function directly -- exactly the class of gap s43's entire
--   write-boundary design exists to close (every write goes through the boundary; a verb is
--   just one caller of it, never the enforcement point itself). Kernel-side wins.
--
--   BUT: "was the target's force resting on a verified signature" is a GPG fact -- Postgres has
--   no gpg binary, no filesystem access, no way to check a detached signature from inside a
--   trigger, and building that in would be its own hazard (shelling out from SECURITY DEFINER
--   plpgsql is not a mechanism this project builds, anywhere). So the signedness of the
--   ORIGINAL act cannot be a fact the kernel COMPUTES; it must be a fact the kernel is TOLD,
--   already checked, by the one surface that CAN run gpg: a verb. THE MARKER, READ HONESTLY
--   (per the commission's own instruction to state plainly whether it exists or needs adding):
--   reading kernel/lineage/s25-commission-kind.sql and bootstrap/templates/
--   verify-commission.tmpl before this delta was authored, a SIGNED commission's signedness
--   lives ENTIRELY OUTSIDE the ledger -- a `.claude/commission-<id>.asc` file banked beside the
--   world, checked on demand by verify-commission against the deployment's `keys/` directory.
--   THE MARKER DOES NOT EXIST as a ledger fact and NEEDS ADDING -- this delta adds it: a new
--   kind, `commission_signature_verified`, written ONLY by verify-commission itself (extended,
--   this same commit, with an opt-in `--attest` flag) the moment its OWN real gpg check returns
--   VERIFIED, never as a bare self-assertion by an ordinary writer. This converts "the kernel
--   trusts the verb's own honesty" into the SAME disclosed-bound shape every other apparatus
--   fact in this project already carries (the HMAC stamp is "a tripwire, not authentication",
--   s17's own words; the hash chain is "tamper-evident, not tamperproof", s26/s42/s43's own
--   words) -- NEVER cryptographic unforgeability inside the trigger (impossible, named, not
--   claimed), but a JOURNALED, HASH-CHAINED, ATTRIBUTED claim that is independently
--   RE-CHECKABLE forever after by re-running verify-commission's actual gpg verification
--   against the cited commission's banked .asc and committed key. A forged marker row (a direct
--   boundary write claiming VERIFIED without ever running gpg) is not made impossible by this
--   delta -- nothing SQL-only can make it impossible -- but it is made FALSIFIABLE where, before
--   this delta, an unsigned act silently superseding a signed one left NO trace distinguishing
--   it from a legitimate signed supersession at all. That is the honest grade this delta ships
--   at, named here so no future reader overclaims it.
--
--   ITEM 3 (proof of possession at key binding) -- ALSO KERNEL-SIDE, via the SAME marker-fact
--   trick, but the derivation differs in a way worth stating precisely (the commission asked
--   this be derived, not assumed identical to item 1). A NAIVE port of item 1's shape --
--   "the bind-key verb checks possession, then kernel-side require SOME marker exists" -- would
--   buy NOTHING beyond a verb-side-only check, because a direct-psql caller could fabricate
--   BOTH the possession marker AND the binding row in the SAME transaction, with zero extra
--   friction: unlike item 1, where the marker (a commission's own SIGNED verdict) is written by
--   an EARLIER, INDEPENDENT act (verify-commission, run against a commission row that already
--   exists, at a time the eventual supersession act's author does not control), a bind-key
--   possession marker written moments before the binding it authorizes has no independent
--   standing over the binding itself -- forging one is exactly as easy as forging the other.
--   The fix that DOES buy something (mirrored from s48/s52's review/artifact-witness-existence
--   idiom, not invented fresh): SPLIT the act into two ledger rows written by two SEPARATE
--   verb-side gpg checks that a THIRD party (a later auditor, or `judge`) can independently
--   re-verify against the actual committed key material -- the possession-proof row
--   (`principal_key_possession_verified`, citing the exact statement text that was signed) and
--   the binding row (`principal_key_bound`, citing the possession row by a mandatory,
--   kernel-CHECKed FK on a FRESH bind). This does not make a colluding direct-psql caller
--   unable to forge both rows -- it cannot, for the same GPG-outside-SQL reason as item 1 -- but
--   it DOES make the FORGERY RE-CHECKABLE: the possession row names the exact statement bytes
--   its own claimed proof covers, and re-running the SAME verification (a future verb, or a
--   human with the committed key) against those bytes either confirms or contradicts the claim,
--   independent of the kernel's own bookkeeping. Same disclosed-bound honesty as item 1, named
--   here rather than oversold as unconditional. The kernel-CHECKED half (well-formedness: the
--   FK exists, targets the right kind, the fingerprints MATCH) closes the class of defect that
--   IS purely structural -- a bind-key act citing NOTHING, or citing a possession row for a
--   DIFFERENT fingerprint, both unrepresentable at construction, exactly matching the
--   "unrepresentable, not merely discouraged" standard s48's own header sets.
--
--   ITEM 2 (verify against the s41 binding) -- VERB-SIDE ONLY, NO KERNEL DELTA, and this is not
--   a downgrade from items 1/3's kernel-side wins but the CORRECT home: item 2 is a REPORTING
--   refinement of an EXISTING verb's OUTPUT (which grade a signature check earned), not a new
--   REFUSAL anyone could bypass by skipping the verb -- there is no boundary-write path that
--   "verify-commission's own grading" could be bypassed ON, because verify-commission is a
--   read-only reporting tool, never a write gate itself. Shipped in
--   bootstrap/templates/verify-commission.tmpl this same commit; see that file's own "GRADE,
--   ADDED" docstring section for the mechanism. No kernel column, kind, or trigger required or
--   added for item 2.
--
-- ATTENTION POINT (this builder's own judgment, surfaced per CLAUDE.md's hazard-in-reach
-- corollary, mirroring s60's own precedent for a divergence beyond the spec's literal text): the
-- spec's item 1 names two examples of a SIGNED-force act ("a SIGNED commission; a signed
-- milestone closure") without specifying the exact linkage mechanism by which a NON-commission
-- row (a milestone's work_closed row) is said to rest its force on a signature. This delta
-- resolves it via a NEW, dedicated, kernel-CHECKed column (`signature_symmetry_witness`,
-- licensed on EVERY kind, mirroring how `refs` is free on every kind but -- UNLIKE refs --
-- existence- AND target-kind-checked, because this field is SECURITY-LOAD-BEARING while `refs`
-- is deliberately NOT (s48's own header: "prose `refs` citations of future/foreign rows stay
-- legal, by design, everywhere else" -- WK1-c's scope boundary). Minting a NEW column rather
-- than overloading `refs` follows that same boundary rather than crossing it: a checkable,
-- security-relevant citation gets its OWN typed field (s29's work_review_ref precedent), never a
-- second job piled onto the one column the project has already ruled must stay uncheckable.
--
-- ELEMENT 1 -- TWO NEW KINDS (thirty-second and thirty-third members):
--   commission_signature_verified -- the marker fact item 1's derivation names: written ONLY by
--     bootstrap/templates/verify-commission.tmpl's `--attest` mode, the moment its OWN real gpg
--     check returns VERIFIED for a commission row. Columns: signature_attests_row (identity,
--     mandatory, the attested commission's row id -- a genuine FK, not a text token, since this
--     kind's whole shape is "attest exactly ONE commission"), signature_grade (identity,
--     mandatory, closed vocabulary {binding-verified, directory-verified} -- item 2's own grade,
--     banked as a permanent ledger fact rather than only a transient CLI print), and REUSE of
--     principal_key_fingerprint (s41's column, ADR-0012 P1 -- ONE home for "an OpenPGP
--     fingerprint", never a second near-identical column) for the signing key.
--   principal_key_possession_verified -- item 3's proof-of-possession marker: written ONLY by
--     `led principal bind-key`'s extended flow (bootstrap/templates/led.tmpl, this same commit),
--     the moment ITS OWN real gpg check confirms a detached signature over a canonical
--     proof-of-possession statement, made with the EXACT key being bound. Columns: REUSE of
--     principal_key_fingerprint (the fingerprint proven) and the generic `statement` column
--     (every kind already carries it, s25's own "a commission is structurally indistinguishable
--     from any other prose ledger row" precedent -- no new column needed for the signed text
--     itself, since `statement` already exists on every kind and this kind needs nothing more
--     structured than "here is the exact text that was signed").
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
     'commission_signature_verified','principal_key_possession_verified'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s61-signature-symmetry-and-key-binding.sql: widens s60''s thirty-one-member
   vocabulary by commission_signature_verified (item 1''s marker fact -- a commission row was
   independently GPG-verified, at what grade) and principal_key_possession_verified (item 3''s
   marker fact -- a fingerprint was proven possessed by a detached signature). Both are written
   ONLY by their respective verbs'' own real gpg checks, never asserted bare by an ordinary
   writer -- see this file''s own WHY section for the disclosed honesty grade.';

-- ============================================================================================
-- ELEMENT 2 -- FOUR NEW COLUMNS + THE ONE WIDENED REUSE (principal_key_fingerprint licensed on
-- a third and fourth kind).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS signature_attests_row bigint
    REFERENCES :"schema".ledger(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS signature_grade text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS signature_symmetry_witness bigint
    REFERENCES :"schema".ledger(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS key_binding_possession_ref bigint
    REFERENCES :"schema".ledger(id);

COMMENT ON COLUMN :"schema".ledger.signature_attests_row IS
  'commission_signature_verified''s identity field: the commission row (kind=''commission'') this
   attestation regards -- a genuine FK (existence kernel-enforced by the REFERENCES clause
   itself, no trigger needed for that half); validate_signature_witness (Element 6) refuses a
   target whose kind is not ''commission''. kernel/lineage/
   s61-signature-symmetry-and-key-binding.sql.';
COMMENT ON COLUMN :"schema".ledger.signature_grade IS
  'commission_signature_verified''s value field: which vocabulary the attested VERIFIED verdict
   earned -- binding-verified (the signing key matches an in-force s41 principal_key_bound
   fingerprint for the commission''s actor) or directory-verified (verified only against the
   deployment''s committed keys/ directory). Closed two-member vocabulary, banked permanently
   (item 2''s grade, item 1''s own supporting fact). kernel/lineage/
   s61-signature-symmetry-and-key-binding.sql.';
COMMENT ON COLUMN :"schema".ledger.signature_symmetry_witness IS
  'Licensed on EVERY kind (no kind-shape mandate -- optional everywhere, mirroring how `refs` is
   free on every kind, but UNLIKE refs this field IS existence-and-target-kind checked, because
   it is security-load-bearing: when present, it names the commission_signature_verified row
   (Element 1) that grounds THIS row''s own claim that its force rests on a verified signature --
   the fact validate_supersession_target''s new symmetry block (Element 7) consults. A NEW
   dedicated column rather than an overload of `refs`, following s48''s own WK1-c scope boundary
   (checkable, security-relevant citations get their own typed field; `refs` stays deliberately
   uncheckable everywhere). kernel/lineage/s61-signature-symmetry-and-key-binding.sql.';
COMMENT ON COLUMN :"schema".ledger.key_binding_possession_ref IS
  'principal_key_bound''s (s41) new, OPTIONAL-BY-KIND-SHAPE column: on a FRESH bind
   (principal_binding_active = true) it is MANDATORY and must name a
   principal_key_possession_verified row (Element 1) proving possession of the EXACT fingerprint
   being bound (validate_principal_binding, re-issued, Element 5); on a retraction
   (principal_binding_active = false) or any other kind it is FORBIDDEN -- revocation needs no
   fresh proof of possession (item 3: revocation is GPG-revocation-certificate + the s41
   retraction event, documented in user-guide/USER-GPG-TRUST-LAYER-FAQ.md, never a second
   signature by a possibly-compromised-or-lost key). kernel/lineage/
   s61-signature-symmetry-and-key-binding.sql.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS signature_attests_row_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT signature_attests_row_kind_shape CHECK (
    (kind = 'commission_signature_verified') = (signature_attests_row IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS signature_grade_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT signature_grade_kind_shape CHECK (
    (kind = 'commission_signature_verified') = (signature_grade IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS signature_grade_vocabulary;
ALTER TABLE :"schema".ledger ADD CONSTRAINT signature_grade_vocabulary CHECK (
    signature_grade IS NULL OR signature_grade IN ('binding-verified', 'directory-verified'));

-- signature_symmetry_witness is licensed on EVERY kind (no kind-shape CHECK at all -- optional
-- everywhere by design, Element 1's own note); its structural checking is target-kind-only
-- (Element 6), never a kind-of-the-CARRYING-row restriction.

-- key_binding_possession_ref: mandatory iff (kind = principal_key_bound AND a FRESH bind);
-- IS TRUE used throughout (never bare boolean comparison) to keep every OTHER kind's NULL
-- principal_binding_active out of three-valued-logic trouble (the s41 D-1 idiom, carried here).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS key_binding_possession_ref_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT key_binding_possession_ref_kind_shape CHECK (
    (kind = 'principal_key_bound' AND principal_binding_active IS TRUE)
    = (key_binding_possession_ref IS NOT NULL));

-- principal_key_fingerprint (s41's ONE home) widened to a third and fourth kind -- additive on
-- every side of the iff (principal_key_bound keeps its exact legality; the two new kinds join).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_key_fingerprint_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_key_fingerprint_kind_shape CHECK (
    (kind IN ('principal_key_bound', 'commission_signature_verified',
              'principal_key_possession_verified'))
    = (principal_key_fingerprint IS NOT NULL));

COMMENT ON COLUMN :"schema".ledger.principal_key_fingerprint IS
  'The OpenPGP v4 fingerprint (40 uppercase hex chars, shape-CHECKed, s41) a row names. Licensed
   on THREE kinds since s61 (kernel/lineage/s61-signature-symmetry-and-key-binding.sql):
   principal_key_bound (s41, "this key is bound to this principal"), commission_signature_verified
   ("this key produced this VERIFIED signature"), and principal_key_possession_verified ("this
   fingerprint''s possession was proven") -- the SAME free-text-shaped fingerprint vocabulary
   answers all three, ADR-0012 P1, never a second near-identical column.';

-- ============================================================================================
-- ELEMENT 3 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 92 COLUMNS (the four new
-- columns appended in serialization order, before the predecessor link; base body = s60''s own
-- text, verified unedited). principal_key_fingerprint is ALREADY serialized (s41) -- reusing the
-- column costs this re-issue nothing beyond it already being present once.
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
      -- s61: the four new columns, appended last before the predecessor link.
      hashfield(r.signature_attests_row::text),
      hashfield(r.signature_grade),
      hashfield(r.signature_symmetry_witness::text),
      hashfield(r.key_binding_possession_ref::text),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 4 -- THE TWO COLUMN-COMPLETE VIEWS, +4 APPENDED (the s20 lesson).
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
       l.key_binding_possession_ref
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
       l.key_binding_possession_ref
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 5 -- THE DERIVED READ: signed_commissions (unsuperseded attestation rows -- no
-- active/inactive discriminator on this kind, Element 1's own note: a plain assertion, not a
-- state machine; if an attestation is ever wrong the correction is a fresh, non-superseding
-- attestation of the SAME commission at a corrected grade, never a retraction -- named as a
-- LIMIT below, not silently built as a withdrawal mechanism this delta does not need).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".signed_commissions
    WITH (security_invoker = true) AS
SELECT lc.signature_attests_row AS commission_id, lc.signature_grade AS grade,
       lc.principal_key_fingerprint AS signing_key, lc.actor AS attested_by, lc.ts AS at,
       lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'commission_signature_verified';

COMMENT ON VIEW :"schema".signed_commissions IS
  'kernel/lineage/s61-signature-symmetry-and-key-binding.sql: every commission row independently
   GPG-verified by bootstrap/templates/verify-commission.tmpl''s --attest mode, at whichever grade
   (binding-verified | directory-verified) that run earned. The fact validate_supersession_target
   (Element 7) and validate_signature_witness (Element 6) both consult.';

GRANT SELECT ON :"schema".signed_commissions TO :"role";

-- ============================================================================================
-- ELEMENT 6 -- validate_signature_witness: A NEW, THIRD-SIBLING TRIGGER (the s48/s52 idiom --
-- orthogonal to every other validate_* member's leaf concern, shares no state with any of them).
-- Two well-formedness refusals, both same-row-addressed target reads (the s45/s48 idiom): (a) a
-- commission_signature_verified row's signature_attests_row must target a kind='commission' row;
-- (b) ANY row's signature_symmetry_witness, when supplied, must target a
-- kind='commission_signature_verified' row.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_signature_witness() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
BEGIN
  IF NEW.kind = 'commission_signature_verified' THEN
    SELECT l.kind INTO v_target_kind FROM ledger l WHERE l.id = NEW.signature_attests_row;
    IF v_target_kind IS DISTINCT FROM 'commission' THEN
      RAISE EXCEPTION 'Ledger policy: a commission_signature_verified row must attest a COMMISSION row (s61) — row % has kind ''%'', not ''commission''. This kind exists to record "verify-commission --attest independently verified THIS commission''s signature"; it cannot attest any other kind of row.', NEW.signature_attests_row, v_target_kind;
    END IF;
  END IF;

  IF NEW.signature_symmetry_witness IS NOT NULL THEN
    SELECT l.kind INTO v_target_kind FROM ledger l WHERE l.id = NEW.signature_symmetry_witness;
    IF v_target_kind IS DISTINCT FROM 'commission_signature_verified' THEN
      RAISE EXCEPTION 'Ledger policy: signature_symmetry_witness must name a commission_signature_verified row (s61) — row % has kind ''%''. This field grounds a claim that THIS row''s own force rests on a verified signature; only an independently GPG-verified attestation row can carry that grounding (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 1).', NEW.signature_symmetry_witness, v_target_kind;
    END IF;
  END IF;

  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_signature_witness ON :"schema".ledger;
CREATE TRIGGER validate_signature_witness BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_signature_witness();

COMMENT ON FUNCTION :"schema".validate_signature_witness() IS
  'kernel/lineage/s61-signature-symmetry-and-key-binding.sql: well-formedness ONLY (two
   same-row-addressed target-kind checks). The SYMMETRY RULE itself (does the target''s signed
   force actually require this supersession to ALSO be signed) lives in
   validate_supersession_target (Element 7, s45''s single home) -- this trigger never refuses a
   supersession on symmetry grounds, only a malformed citation.';

-- ============================================================================================
-- ELEMENT 7 -- validate_supersession_target RE-ISSUED: THE SYMMETRY RULE (item 1). Base body =
-- s45''s (UNCHANGED by s60) -- the write_refused-unretractable branch and the standing-lifecycle
-- branch are BYTE-IDENTICAL; ONE new block appended after them.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
  v_target_db_role text;
  v_target_subject bigint;
  v_target_signed boolean;
  v_new_signed boolean;
BEGIN
  IF NEW.supersedes IS NOT NULL THEN
    -- the row-addressed target read widens from l.kind alone to three columns -- same shape
    -- of read, s43's own gates/ledger_reader_allowlist.py entry covers the widened read
    -- without a new entry (verified live, this delta's fixture).
    SELECT l.kind, l.principal_db_role, l.principal_subject
      INTO v_target_kind, v_target_db_role, v_target_subject
      FROM ledger l WHERE l.id = NEW.supersedes;

    IF v_target_kind = 'write_refused' THEN
      RAISE EXCEPTION 'Ledger policy: a write_refused row is UNRETRACTABLE (s43, ratified R6) — row % records a historical fact about a refused attempt; it asserts nothing retractable, and superseding it is the one path by which a later writer could make a refusal vanish from every current view. The record stands; if the refusal was wrong, the corrected write simply succeeds beside it (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 2).', NEW.supersedes;
    END IF;

    -- s45 §3.4: standing-lifecycle supersession discipline (the conversion-found closure --
    -- without it, ANY writer could lift a revocation or resurrect a stale declaration by
    -- superseding it with an unrelated row of a different kind).
    IF v_target_kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
      IF NEW.kind IS DISTINCT FROM v_target_kind THEN
        RAISE EXCEPTION 'Ledger policy: a standing-lifecycle row (kind ''%'', row %) is superseded ONLY by its OWN kind (s45, kernel/lineage/s45-standing-lifecycle.sql §3.4) — this write is kind ''%''. Rotation/re-declaration or unbind for declarations (./led principal declare-standing / ./led principal undeclare-standing); re-suspend-correction or lift for suspensions (./led principal suspend --supersedes / ./led principal lift-suspension); re-revoke-correction for revocations. A cross-kind supersession would silently alter derived standing (who a role speaks for, or whether a principal is suspended/revoked) with no typed act — refused at construction.', v_target_kind, NEW.supersedes, NEW.kind;
      END IF;

      IF v_target_kind = 'principal_standing_declared' THEN
        IF NEW.principal_db_role IS DISTINCT FROM v_target_db_role THEN
          RAISE EXCEPTION 'Ledger policy: a row superseding a standing declaration must restate the SAME db_role its target governs (s45 §3.4) — target row % binds role ''%'', this write names ''%''. A rotation or unbind restates the role it governs; to bind a DIFFERENT role, write a fresh (non-superseding) declaration instead.', NEW.supersedes, v_target_db_role, NEW.principal_db_role;
        END IF;
        IF NEW.principal_binding_active = false AND NEW.principal_subject IS DISTINCT FROM v_target_subject THEN
          RAISE EXCEPTION 'Ledger policy: an UNBIND must restate the SAME subject principal its target declaration binds (s45 §3.4) — target row % binds principal %, this unbind names %. A ROTATION (principal_binding_active=true) may repoint the subject by design; an unbind may not.', NEW.supersedes, v_target_subject, NEW.principal_subject;
        END IF;
      ELSIF v_target_kind IN ('principal_suspended', 'principal_revoked') THEN
        IF NEW.principal_subject IS DISTINCT FROM v_target_subject THEN
          RAISE EXCEPTION 'Ledger policy: a lift or rationale-correction must restate the SAME subject principal its target row regards (s45 §3.4) — target row % (kind ''%'') regards principal %, this write names %.', NEW.supersedes, v_target_kind, v_target_subject, NEW.principal_subject;
        END IF;
      END IF;
    END IF;

    -- s61 (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 1): SIGNED SUPERSESSION
    -- SYMMETRY. "signed force" for a row R = R itself is a commission independently attested
    -- VERIFIED (Element 5's signed_commissions view, keyed by commission id) OR R carries a
    -- signature_symmetry_witness naming such an attestation directly (Element 6 already
    -- refused a malformed witness at construction, so any non-NULL witness reaching this point
    -- IS a genuine commission_signature_verified row id). Computed for the TARGET via the
    -- row-addressed read above (extended by two columns); computed for NEW directly from the
    -- trigger row (no query needed -- NEW.kind/NEW.signature_symmetry_witness are already in
    -- hand). NEW can never satisfy the "itself an attested commission" disjunct (the
    -- attestation, by construction, can only be written AFTER the commission row it attests
    -- already exists -- so a commission row can never attest itself in the same statement this
    -- trigger fires within) -- this is not a gap, it is the correct asymmetry: a supersessor's
    -- OWN force can only rest on a signature by CITING an already-independently-verified
    -- commission, never by being verified in the same breath as its own insertion.
    SELECT EXISTS (SELECT 1 FROM signed_commissions sc WHERE sc.commission_id = NEW.supersedes)
        OR (v_target_kind IS NOT NULL AND EXISTS (
              SELECT 1 FROM ledger l WHERE l.id = NEW.supersedes
              AND l.signature_symmetry_witness IS NOT NULL
              AND EXISTS (SELECT 1 FROM signed_commissions sc2
                          WHERE sc2.row_id = l.signature_symmetry_witness)))
      INTO v_target_signed;
    IF v_target_signed THEN
      SELECT (NEW.signature_symmetry_witness IS NOT NULL
              AND EXISTS (SELECT 1 FROM signed_commissions sc3
                          WHERE sc3.row_id = NEW.signature_symmetry_witness))
        INTO v_new_signed;
      IF NOT v_new_signed THEN
        RAISE EXCEPTION 'Ledger policy: SIGNED supersession symmetry refused (s61, design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 1) — target row % (kind ''%'') rests its force on a VERIFIED signature (an independently GPG-attested commission); it may only be superseded by an act whose OWN force also rests on a verified signature. This write carries no signature_symmetry_witness naming a commission_signature_verified row. Remedy: have the maintainer write a SIGNED commission directing this supersession (gpg --detach-sign --armor, then LED_ACTOR=commissioner ./led commission "<the ask>", then ./verify-commission --attest --id <that commission''s id> — VERIFIED only), then supply --signature-witness <the attestation row''s id> on this write.', NEW.supersedes, v_target_kind;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_supersession_target ON :"schema".ledger;
CREATE TRIGGER validate_supersession_target BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_supersession_target();

COMMENT ON FUNCTION :"schema".validate_supersession_target() IS
  'BEFORE INSERT trigger (s43 Element 2/R6, widened s45 §3.4, widened s61 item 1): (1) a
   write_refused row is unretractable; (2) the three standing-lifecycle kinds accept only
   SAME-KIND, IDENTITY-CONTINUOUS supersessors (s45); (3) a target row whose force rests on a
   VERIFIED signature (attested via commission_signature_verified, directly or via
   signature_symmetry_witness) may only be superseded by a row that ITSELF carries a valid
   signature_symmetry_witness (s61, kernel/lineage/s61-signature-symmetry-and-key-binding.sql
   Element 7). All three refusals are checked in this ONE home, never a parallel trigger.';

-- ============================================================================================
-- ELEMENT 8 -- validate_principal_binding RE-ISSUED: PROOF OF POSSESSION AT KEY BINDING
-- (item 3). Base body = s41''s (UNCHANGED by s45/s60) -- the self-edge and human-only-subject
-- branches are BYTE-IDENTICAL; ONE new block appended for principal_key_bound fresh binds.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_principal_binding() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_class text;
  v_possession_kind text;
  v_possession_fp text;
BEGIN
  IF NEW.kind = 'principal_relation_asserted' THEN
    IF NEW.principal_subject = NEW.principal_object THEN
      RAISE EXCEPTION 'Ledger policy: a principal cannot stand in relation ''%'' to ITSELF (s41 D-3) — a self-edge is refused at construction for every relation value (a principal cannot act-for, be dispatched-by, be the same natural person as, or succeed itself). Name two distinct registered principals.', NEW.principal_relation;
    END IF;
    -- both endpoints'' existence is already forced by the two FKs — stated, not re-checked.
  END IF;
  IF NEW.kind = 'principal_key_bound' THEN
    SELECT p.agent_class INTO v_class FROM principal p WHERE p.id = NEW.principal_subject;
    IF v_class IS DISTINCT FROM 'human' THEN
      RAISE EXCEPTION 'Ledger policy: a key binding requires a HUMAN subject — principal % has agent_class ''%'' (s41 D-3; design/MAINT-GPG-TRUST-LAYER.md §6: agent keys stay refused — a key attests a human''s own act, and an agent-held key would launder that guarantee). Bind keys to human principals only.', NEW.principal_subject, v_class;
    END IF;

    -- s61 (design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 3): PROOF OF POSSESSION.
    -- key_binding_possession_ref_kind_shape (Element 2) already made this column MANDATORY on
    -- every FRESH bind (principal_binding_active IS TRUE) and FORBIDDEN elsewhere -- this block
    -- only fires the WELL-FORMEDNESS check the CHECK constraint cannot express: the referenced
    -- row must itself be a principal_key_possession_verified row (Element 1) proving possession
    -- of the EXACT fingerprint this bind names, never a different one. A retraction
    -- (principal_binding_active = false) needs no possession proof at all (item 3''s own text:
    -- revocation is a GPG revocation certificate + this retraction event, never a second
    -- signature by a key that may itself be lost or compromised) -- this block is GUARDED to
    -- fire only on the fresh-bind branch, mirroring the CHECK constraint''s own guard.
    IF NEW.principal_binding_active IS TRUE THEN
      -- the NULL case is ALSO reachable here (the trigger runs BEFORE the CHECK constraint is
      -- evaluated, Postgres''s own BEFORE-trigger-then-CHECK ordering) -- given its own, clearer
      -- teach-text rather than falling through to the generic-kind branch below and printing a
      -- confusing "row <NULL> has kind '<NULL>'" (caught by this delta''s own scratch witness,
      -- seen-red/s61-signature-symmetry-and-key-binding/, before shipping).
      IF NEW.key_binding_possession_ref IS NULL THEN
        RAISE EXCEPTION 'Ledger policy: a FRESH principal_key_bound row (principal_binding_active=true) must name a key_binding_possession_ref (s61, design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 3) — this write supplies none. Run ./led principal attest-possession <fingerprint> --asc <detached-signature-path> first (proves you hold the private key by verifying a detached signature over a canonical proof-of-possession statement against THIS deployment''s committed keys/ entry for that fingerprint), then bind citing the returned row id.';
      END IF;
      SELECT l.kind, l.principal_key_fingerprint INTO v_possession_kind, v_possession_fp
        FROM ledger l WHERE l.id = NEW.key_binding_possession_ref;
      IF v_possession_kind IS DISTINCT FROM 'principal_key_possession_verified' THEN
        RAISE EXCEPTION 'Ledger policy: key_binding_possession_ref must name a principal_key_possession_verified row (s61) — row % has kind ''%''. A FRESH key binding requires proof the binder holds the private key: run ./led principal attest-possession <fingerprint> --asc <detached-signature-path> first (verifies a signature over a canonical proof-of-possession statement against THIS deployment''s committed keys/ entry for that fingerprint), then bind citing the returned row id.', NEW.key_binding_possession_ref, v_possession_kind;
      END IF;
      IF v_possession_fp IS DISTINCT FROM NEW.principal_key_fingerprint THEN
        RAISE EXCEPTION 'Ledger policy: key_binding_possession_ref names a possession proof for fingerprint ''%'', but this binding is for fingerprint ''%'' (s61) — a possession proof authorizes ONLY the exact fingerprint it proved, never a different one. Run ./led principal attest-possession for the fingerprint you intend to bind.', v_possession_fp, NEW.principal_key_fingerprint;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_principal_binding ON :"schema".ledger;
CREATE TRIGGER validate_principal_binding BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_principal_binding();

COMMENT ON FUNCTION :"schema".validate_principal_binding() IS
  'BEFORE INSERT trigger (s41, widened s61 item 3): (1) no principal_relation_asserted self-edge;
   (2) principal_key_bound requires a human subject; (3) a FRESH principal_key_bound
   (principal_binding_active=true) must cite, via key_binding_possession_ref, a
   principal_key_possession_verified row proving possession of the EXACT fingerprint being bound
   (kernel/lineage/s61-signature-symmetry-and-key-binding.sql Element 8). A retraction needs no
   possession proof (item 3: revocation is a GPG revocation certificate + this event).';

-- ============================================================================================
-- ELEMENT 9 -- GRANTS (belt-and-braces; CREATE OR REPLACE VIEW preserves grants on
-- ledger_current/countersigned_in_force, s21''s own additive-column-order idiom).
-- ============================================================================================
-- (signed_commissions' GRANT SELECT is issued at Element 5, immediately after its
-- CREATE OR REPLACE -- kept there rather than duplicated here, matching s36/s60's own
-- single-grant-site idiom.)

-- ============================================================================================
-- HISTORY: safe -- per-mechanism grounds:
--   * ledger_kind_check re-issued WIDER (additive vocabulary: every pre-existing kind''s
--     legality is unchanged; the two new kinds are disjoint from the thirty-one existing
--     members and are BORN in this delta -- no pre-existing row can carry either).
--   * FOUR new nullable no-DEFAULT columns, kind-scoped mandatory/forbidden by CHECKs that
--     validate vacuously on every pre-existing row (no pre-existing row carries a new kind, and
--     no pre-existing principal_key_bound row can retroactively acquire
--     principal_binding_active IS TRUE with no key_binding_possession_ref -- the CHECK reads the
--     row''s OWN two columns, both already present and both unchanged by this delta for any
--     pre-existing row).
--   * principal_key_fingerprint_kind_shape re-issued WIDER (additive on both sides of the iff:
--     principal_key_bound keeps its exact legality; two new kinds join the licensed set).
--   * validate_signature_witness is a NEW trigger member, firing only on kinds/columns THIS
--     delta makes representable.
--   * validate_supersession_target and validate_principal_binding are RE-ISSUED with ONE new
--     appended block each; every pre-existing branch''s text is BYTE-IDENTICAL to the s45/s41
--     (respectively) bodies quoted above this file''s own header confirmed against the s60 head.
--   * signed_commissions is a brand-new view with no pre-existing reader.
--   * compute_row_hash/ledger_current/countersigned_in_force re-issues are s42''s law, self-
--     applied, pure column-list appends (s20 lesson), byte-identical to the s28..s60 precedent.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: an act whose force rests on an independently GPG-verified signature (a
--     commission_signature_verified attestation, directly or cited via
--     signature_symmetry_witness) is superseded only by an act carrying its own valid
--     signature_symmetry_witness (item 1); a FRESH principal_key_bound row is accepted only when
--     it cites a principal_key_possession_verified row proving possession of the EXACT
--     fingerprint being bound (item 3); both marker kinds are written only by their owning
--     verb''s OWN real gpg check, never asserted bare -- and both are RE-CHECKABLE forever after
--     against the cited commission''s/statement''s bytes, the honest, disclosed grade this delta
--     ships at (see this file''s own WHY section -- NEVER cryptographic unforgeability inside a
--     trigger, which SQL alone cannot provide).
--   - QUANTIFICATION UNIVERSE: KINDS gaining a new column: signature_attests_row/signature_grade
--     on commission_signature_verified only (two-way); signature_symmetry_witness on every kind
--     (unrestricted, target-kind-checked instead); key_binding_possession_ref on
--     principal_key_bound''s fresh-bind branch only (three-part CHECK, IS TRUE-guarded).
--     principal_key_fingerprint widened to two more kinds (two-way, additive). VIEWS:
--     signed_commissions is new, factors through ledger_current exclusively (no raw `ledger`
--     reference of its own); ledger_current/countersigned_in_force re-issued (+4 columns); no
--     other pre-existing view touched. TRIGGERS: ONE new member (validate_signature_witness);
--     TWO re-issues, each adding exactly one new block after its pre-existing, byte-identical
--     text (validate_supersession_target, validate_principal_binding). ENGINE: the ASP twin is
--     DEFERRED this pass -- named as a LIMIT below, not silently omitted (see LIMITS).
--   - DENOMINATION: signedness in independently-verified, journaled, hash-chained EVENTS
--     (commission_signature_verified, principal_key_possession_verified), never a boolean
--     self-assertion on the act it concerns; the symmetry/possession CITATIONS in dedicated,
--     target-kind-checked FK columns, never the deliberately-uncheckable `refs` column; the
--     signature GRADE in a closed two-member vocabulary (binding-verified | directory-verified).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE
-- shape (this delta only ADDS refusals -- two new kinds, four new columns, one widened existing
-- CHECK, one new trigger member, two trigger re-issues each APPENDING one new refusal block
-- after byte-identical pre-existing text, read-only new views; no existing CHECK narrowed, no
-- existing trigger''s PRE-EXISTING branch edited, no existing grant revoked) -- riding the
-- 2026-07-09 class rule exactly as s60 did (spec §1''s own "not filed as pairing debt" posture
-- for the ASP twin does NOT extend to this delta -- see LIMITS: the ASP twin is deferred, named,
-- not claimed shipped).
--
-- LIMITS (pre-registered):
--   - NO ASP TWIN IN THIS PASS. Unlike s60''s authority-chain closure (a genuinely recursive
--     transitive-reachability predicate, where an independent SECOND derivation buys real
--     defense-in-depth against a stratification mistake), items 1 and 3''s kernel-side checks are
--     single-hop EXISTS/equality tests over already-in-force facts -- the SAME shape s48/s52''s
--     review/artifact-witness-existence checks ALSO ship with no ASP twin (grepped and confirmed
--     before this delta was authored: neither s48 nor s52 has an engine/lp/ counterpart). This
--     delta follows that precedent rather than s60''s, but the choice is NAMED, not silent, and
--     is the maintainer''s to override: an ASP twin for a single-hop existence check would mirror
--     the SQL query nearly verbatim (no closure/recursion to independently re-derive), so the
--     defense-in-depth an ASP twin buys is smaller here than at s60 -- but not zero (a mis-typed
--     column name in the SQL check would still go undetected by any twin, mirrored or not).
--     Filed as a possible follow-on, not built or claimed built.
--   - THE VERB-SIDE HALVES (bootstrap/templates/led.tmpl''s `led principal attest-possession`
--     subcommand and `bind-key --possession-ref` wiring; the two verbs'' own real gpg checks) are
--     NAMED here as this delta''s OWN LOAD-BEARING DEPENDENCY -- the kernel-side CHECKs above are
--     inert without a verb that ever WRITES a well-formed commission_signature_verified or
--     principal_key_possession_verified row. Shipped THIS SAME COMMIT (bootstrap/templates/
--     verify-commission.tmpl''s --attest flag; bootstrap/templates/led.tmpl''s new subcommand and
--     bind-key extension) -- see those files'' own headers for their half of this delta''s
--     witness plan.
--   - Signature symmetry''s NEW column (signature_symmetry_witness) is licensed on EVERY kind
--     but is only EVER CONSULTED by validate_supersession_target''s symmetry block on a
--     SUPERSEDING write -- a non-superseding row may carry it harmlessly (a caller pre-declaring
--     "this row, too, rests on a verified signature" for a FUTURE supersession to find), or omit
--     it; nothing refuses an ordinary write for lacking one.
--   - No de-configuration / de-attestation path for either new kind (Element 1''s own note) --
--     a wrong attestation is corrected by a FRESH, non-superseding attestation, never a
--     retraction; named, not built, since nothing in the spec asks for a withdrawal and building
--     one would raise its own "can an attestation be un-attested" question this delta does not
--     need to answer.
--   - Trigger/CHECK refusals bind the granted role''s ordinary INSERT path only; the schema-
--     owner/superuser bypass stands (the standing s26..s60 disclosed bound) -- AND, named
--     explicitly per this delta''s own WHY section: a direct-boundary writer with ordinary
--     GRANTed access (not merely a superuser) CAN forge a commission_signature_verified or
--     principal_key_possession_verified row without ever running gpg, since the kernel cannot
--     itself verify a signature. What this delta buys is FALSIFIABILITY (the forged row is
--     independently re-checkable against the cited commission/statement''s actual bytes and the
--     deployment''s committed keys), never cryptographic impossibility -- the SAME disclosed
--     grade the HMAC stamp (s17) and hash chain (s26/s42/s43) already carry, extended here to a
--     third apparatus fact, never claimed as a stronger guarantee than those.
--   - In a solo world, every signature-symmetry/possession fact is written by machinery the one
--     operator controls -- complete and attributed, not adversarially independent (s17''s own
--     honesty, inherited).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s60):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s61val -v kern=s61val_kernel -v role=s61val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        [... s21 through s60, the exact CHAIN_S60 list seen-red/s60-entitlement-enforcement/
--        run_fixtures.py already carries, this delta appends ONE more -f ...] \
--        -f s61-signature-symmetry-and-key-binding.sql
--     (genesis seed per s26; register the write-boundary principal and discharge the s40/s43/s60
--     birth sequence before exercising any other act.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world''s
--   birth chain via bootstrap/new-project.sh''s LINEAGE_CHAIN, the maintainer''s own integration
--   act (matching s60''s own precedent for a delta whose PREREQUISITE chain is not yet wired
--   into that script). Authored and scratch-witnessed on scratch schema pairs in the TOY db
--   only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP/CREATE TRIGGER).
-- ============================================================================================
