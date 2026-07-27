-- s67 REFUSAL-DIGEST BOUND (design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md §2 + the §2 AMENDMENT
-- 2026-07-27 "NULL may not carry the meaning" -- maintainer ruling at merge-hold on this delta's
-- first build, ledger row 1514 item 1, "all should go in," verbatim). Second of the s66/s67
-- journal-totality pair, same s49 family: the refusal journal must record refusals under
-- hostile conditions, because the refusal path is exactly where hostile input arrives (the s65
-- lesson, restated once more). Sonnet-built per the standing delegation contract, from the
-- ratified spec.
--
-- PREREQUISITE / THE HEAD-BODY RULE (s45's own standing instruction): at this delta's
-- authoring the lineage head is s66 (kernel/lineage/s66-forged-stamp-journal-totality.sql,
-- this same commit -- the builder's own directory listing, confirmed before authoring). THE
-- FUNCTIONS THIS DELTA RE-ISSUES: kernel.journal_write_refusal is NOT touched by s66 (s66's own
-- header states plainly: "NO CHANGE to kernel.journal_write_refusal or the four (now seven)
-- boundary functions calling it" -- grep-verified against s66-forged-stamp-journal-totality.sql,
-- which re-issues ONLY kernel.set_stamp). So the TRUE immediately-prior re-issue of
-- kernel.journal_write_refusal is s65 (kernel/lineage/s65-refusal-attempted-kind.sql Element 4),
-- NOT s66 -- stated here explicitly per the spec's own instruction ("the builder states which").
-- kernel.journal_write_refusal is `:"kern".`-namespaced, OUTSIDE gates/lineage_reissue_lineage.py's
-- own `:"schema".`-anchored citation-check universe (per that gate's own docstring; the SAME
-- disclosed exemption s65's own Element 4/Element 5 re-issues already name) -- the citation/
-- prior-body-sha256 line below is carried as a matter of this codebase's house idiom, NOT
-- mechanically gate-enforced, named here rather than silently assumed to be checked.
-- compute_row_hash's true immediately-prior re-issue is s65 (98 columns) -- s66 does not touch
-- it either (grep-verified: s66 re-issues only kernel.set_stamp, a trigger function outside
-- compute_row_hash's own citation chain).
--
-- WHY (spec §2's own words): kernel.journal_write_refusal digests the refused payload WHOLE,
-- whatever its size (encode(sha256(convert_to(p_payload::text,'utf8')),'hex')). The service
-- caps write bodies at 1 MiB (MAX_WRITE_BODY_BYTES), but a direct psql caller bypasses the
-- service entirely -- the kernel journaler is the ONLY backstop on that path, and until this
-- delta it has none. RE-WITNESSED on this delta's own scratch world (pre-fix, s66probe, s15..
-- s65+s66 head): an oversized (>1 MiB) refused payload journals TODAY with a full 64-hex
-- digest computed over the whole payload (build report has the verbatim transcript) -- the
-- unbounded baseline this delta closes.
--
-- MECHANISM (spec §2, one bound): when octet_length(p_payload::text) exceeds 1,048,576 bytes
-- (the s51 artifact_too_large precedent, and the exact figure the service already enforces),
-- refusal_payload_digest is recorded NULL. BELOW the bound, byte-identical: the same
-- sha256-over-canonical-text digest computation as s43/s49/s65 left it, unconditionally. The
-- digest is a grep handle, never a join key (the row-1498 witness: joins anchor on refusal_id)
-- -- losing it beyond the bound costs an attacker-sized payload its vanity hash, nothing else;
-- the refusal ITSELF (surface, sqlstate, message, attempted actor/role/kind) is unaffected and
-- fully recorded regardless of payload size.
--
-- §2 AMENDMENT 2026-07-27 -- NULL MAY NOT CARRY THE MEANING (maintainer ruling at merge-hold on
-- this delta's FIRST build): that first build recorded refusal_payload_digest NULL above the
-- bound and widened refusal_payload_digest_kind_shape from mandatory-two-way to one-way to
-- license it -- reviewed and functionally CLEARED (findings ledger, commit 26444ef), but the
-- maintainer separately REFUSED the CHECK-widening shape at merge-hold: "NULL as an implicit
-- sentinel/meaning-carrier is not condonable ... a drift hazard" -- ADR-0000's
-- unrepresentable-illegal-states principle and the standing no-bare-types rule (autoharn2 row
-- 1105), applied to a comment-carried inference ("NULL here means over-bound") instead of a
-- representable, typed value. The re-shape, per the amendment's own four items:
--
--   1. ONE NEW COLUMN, refusal_digest_disposition text -- kind-scoped to write_refused by the
--      house TWO-WAY kind-shape idiom (mandatory when kind='write_refused', forbidden
--      elsewhere -- the SAME shape s44's attest_verdict already uses for "always known within
--      the kind"), closed two-member vocabulary CHECK ('computed', 'payload_over_bound') --
--      extend ONLY by a future delta, never by this one growing past two members.
--   2. THE COUPLING CHECK, table-level: the amendment's own prose gives the fixed rule as
--      `(refusal_digest_disposition = 'computed') = (refusal_payload_digest IS NOT NULL)` --
--      logically the exact right relation, but that BARE unguarded shape has a live gap this
--      builder verified with a throwaway psql table before shipping it: `disposition =
--      'computed'` evaluates to SQL NULL (neither true nor false) whenever disposition itself
--      is NULL (any non-write_refused row), and a CHECK constraint that evaluates to NULL is
--      SATISFIED, not violated -- so the bare form would silently fail to forbid a non-
--      write_refused row from carrying a populated digest, reopening exactly the hazard s43's
--      original two-way refusal_payload_digest_kind_shape existed to close. This codebase
--      already has the SOUND idiom for this exact shape -- s44's attest_expected_verdict_
--      coupling, kind-guarded: `kind <> '<K>' OR (<nullable-within-kind col> IS NULL) =
--      (<always-known-within-kind col> = '<value>')` -- transcribed here byte-for-shape as
--      refusal_payload_digest_disposition_coupling, `kind <> 'write_refused' OR
--      (refusal_payload_digest IS NULL) = (refusal_digest_disposition = 'payload_over_bound')`.
--      This is EQUIVALENT to the amendment's own formula given the two-member closed
--      vocabulary (digest NULL iff disposition='payload_over_bound' iff NOT
--      disposition='computed' iff digest IS NOT NULL is false), airtight because
--      refusal_digest_disposition is GUARANTEED non-NULL whenever kind='write_refused' (by
--      item 1's own two-way kind-shape CHECK) -- the identical soundness argument s44's own
--      guard already rests on, re-verified rather than merely assumed for this new instance.
--      s44's OWN precedent ALSO keeps a separate one-way kind-shape CHECK on the
--      nullable-within-kind column (attest_expected_kind_shape) ALONGSIDE its coupling CHECK --
--      this delta does the same: refusal_payload_digest_kind_shape (this delta's first build's
--      own one-way widening, `refusal_payload_digest IS NULL OR kind = 'write_refused'`) STAYS,
--      UNCHANGED, because the coupling CHECK's own kind-guard means it does not (and by the
--      three-valued-logic argument above, structurally CANNOT alone) forbid a non-write_refused
--      row from carrying a digest -- that job is refusal_payload_digest_kind_shape's, and
--      dropping it would reopen the hazard. Named explicitly here, not silently done: the
--      amendment's own prose ("the original widening dissolves") is read as describing the
--      CONCEPTUAL widening this fix closes (an implicit, undeclared NULL-as-meaning on the
--      write_refused kind), not a literal instruction to delete a CHECK whose own established
--      codebase precedent (s44) keeps its exact structural sibling. Net effect matches the
--      amendment's own words precisely: a digest NULL row MUST declare payload_over_bound; a
--      populated digest MUST declare computed; a non-write_refused row may carry neither --
--      every cell of the state space is now table-caught, not commentary-inferred.
--   3. journal_write_refusal writes the disposition in the SAME INSERT statement that writes
--      (or NULLs) the digest -- one writer, one home, no second code path that could drift the
--      two columns apart.
--   4. compute_row_hash re-issued for the new column under s42's law; hash-coverage/kind-shape-
--      manifest/kernel-function-census/fixture-family all extended accordingly (this same
--      commit).
--   Precedent-columns note (amendment item 4, not acted on here): refusal_attempted_kind (s65)
--   and the s43/s49 attempted-actor NULLs carry the SAME implicit-sentinel shape this ruling
--   condemns for refusal_payload_digest. The amendment names this a SEPARATE, later maintainer
--   decision (ADR-0008 Rule 3, a visible gap not silently absorbed) -- not touched by this
--   delta, which is scoped exactly to refusal_payload_digest per the ruling that triggered it.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a)): the payloads this delta bounds are EXACTLY those
-- reaching kernel.journal_write_refusal -- every one of the SEVEN boundary functions'
-- refusal legs (grep-enumerated, current count seven as of this lineage's head: ledger_write,
-- review_write, registration_write, obligation_write -- all four born s43; artifact_write --
-- s51; obligation_revoke -- s57; missive_dispose -- s58), all calling journal_write_refusal
-- identically -- this ONE re-issue covers every call site, the same "one home" argument s43's
-- own header makes and s49/s65 both re-verify rather than merely assume. TABLES/COLUMNS: ONE new
-- column, refusal_digest_disposition, kind-scoped two-way (mandatory on write_refused, forbidden
-- elsewhere) plus its own closed-vocabulary value CHECK; refusal_payload_digest's own kind-shape
-- CHECK is UNCHANGED from this delta's first build (one-way, still legitimately NULL on the
-- licensed kind); the NEW coupling CHECK ties the two together, table-level, two-way in effect.
-- KINDS: unchanged. VIEWS: ledger_current/countersigned_in_force gain ONE column, APPENDED (the
-- s20/s23/s65 lesson -- CREATE OR REPLACE VIEW forbids reordering existing columns). GATES:
-- hash-coverage (this delta's own compute_row_hash re-issue, 99 columns, gate-witnessed both
-- polarities); kind-shape manifest (CHAIN extended through s67, this same commit; MANIFEST gains
-- the new column's two-way row plus the CROSS_COLUMN_COUPLING_MANIFEST row for the new coupling
-- CHECK); lineage-reissue-lineage (citation of s65 for both re-issued functions stated above,
-- NOT mechanically checked for `:"kern".`-namespaced journal_write_refusal, but compute_row_hash
-- IS a `:"schema".`-namespaced function inside that gate's own checked universe -- citation +
-- prior-body-sha256 both supplied and gate-verified); kernel-function-census (bank updated same
-- commit -- kern:journal_write_refusal's hash changes again, schema:compute_row_hash's hash
-- changes for the first time in this pair).
--
-- DENOMINATION: the 1,048,576-byte bound is NOT a bare round literal -- it is s51's own
-- artifact_too_large figure (2^20, the same "1 MiB" the service's MAX_WRITE_BODY_BYTES already
-- enforces), reused rather than re-derived. refusal_digest_disposition's own vocabulary is a
-- closed, two-member, kernel-authored set ('computed', 'payload_over_bound') -- never free text,
-- extended only by a future delta (the s43/s58/s60 "kind-structural closed CHECK" idiom, applied
-- here to a disposition rather than a surface/act-class).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (s43/s49/s65/s66's own precedent for this same honesty
-- requirement): this delta re-issues an EXISTING function body via CREATE OR REPLACE
-- (kernel.journal_write_refusal, compute_row_hash) and adds a new mandatory-on-kind column plus
-- a cross-column coupling CHECK -- not a letter-2(a) "only adds" shape, even though the EFFECT
-- is strictly fail-safe (more refusals survive with a full, now EXPLICITLY TYPED record; nothing
-- ACCEPTED before is accepted differently; every refusal that journaled a digest before still
-- journals the SAME digest, below the bound, now additionally declaring disposition='computed').
-- It ships under the maintainer's OWN EXPLICIT RATIFICATION (design/FABLE-S66-S67-JOURNAL-
-- TOTALITY-SPEC.md, ledger row 1514 item 1, "all should go in" -- verbatim; the §2 AMENDMENT's
-- own merge-hold ruling), read per the 2026-07-11 vocabulary note, exactly the posture
-- s43/s49/s65/s66 shipped under for the same reason.
--
-- LIMITS (pre-registered, matching s43/s49/s65/s66's own disclosure convention; this delta's
-- FIRST build's own LIMITS section is superseded by this one per the amendment, not carried
-- forward -- NULL no longer carries meaning at all after this re-shape, so the prior section's
-- own "NULL is NEW, single-cause state" framing is retired, not merely amended):
--   - refusal_payload_digest is NULL if and only if refusal_digest_disposition =
--     'payload_over_bound' (table-CHECK-enforced, not an inference); a write_refused row's
--     digest state is therefore always EXPLICITLY DECLARED, never implicit. A non-write_refused
--     row carries neither column (both NULL, kind-shape-enforced on both).
--   - The bound applies to the WHOLE payload's canonical text (octet_length(p_payload::text)),
--     not to any individual key inside it -- matching s51's own artifact-size reasoning (the
--     whole write body is what the service caps, not a per-field measure).
--   - This delta does not change the attempted-actor guard (s49, unchanged), the
--     attempted-kind extraction (s65, unchanged, and NOT re-shaped by this amendment -- named
--     as a separate, later maintainer decision above), or what happens when the journal INSERT
--     itself fails (s43's own named, disclosed loud-abort/sequence-gap/server-log composition,
--     untouched here).
--   - A deliberately LYING re-issue of journal_write_refusal could still write disposition and
--     digest inconsistently with the TRUTH of what happened (e.g. claim 'computed' while
--     recording a digest of the wrong payload) -- the coupling CHECK enforces internal
--     CONSISTENCY between the two columns, never that either one TRUTHFULLY reflects the
--     original payload; that trust boundary is the same one every other kernel-computed column
--     already rests on (the SECURITY DEFINER function is trusted to tell the truth; the CHECK
--     only catches an ACCIDENTAL drift between two columns the function itself controls, the
--     realistic bug class the maintainer's own ruling named) -- stated, not hidden.
--   - Every other named limit in s17/s23/s43/s49/s65/s66's own headers is unchanged by this
--     delta and not re-stated in full here.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s66): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway): apply the FULL s15..s66 chain (s65's own VALIDATE block +
--   s66), THEN -f s67-refusal-digest-bound.sql (genesis seed per s26; register the
--   write-boundary principal before exercising any refusal path, or the journaler aborts
--   loudly by design, unchanged since s43).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world's birth chain via bootstrap/new-project.sh's
--   LINEAGE_CHAIN narrative (this same commit) and its GENERATED apply loop. Authored and
--   scratch-witnessed on scratch schema pairs in the TOY db only, torn down after.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP+ADD CONSTRAINT;
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
-- ELEMENT 1 -- ONE NEW COLUMN, refusal_digest_disposition, the house TWO-WAY kind-shape idiom
-- (mandatory when kind='write_refused', forbidden elsewhere -- s44's attest_verdict_kind_shape
-- is the exact structural precedent: "always known within the kind"), plus its own closed
-- two-member vocabulary CHECK. refusal_payload_digest_kind_shape (this delta's first build,
-- one-way -- "legitimately NULL within the licensed kind, forbidden elsewhere") is UNCHANGED --
-- see this file's own header §2 AMENDMENT item 2 for why it stays, matching s44's own
-- attest_expected_kind_shape precedent living alongside attest_expected_verdict_coupling.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_digest_disposition text;

COMMENT ON COLUMN :"schema".ledger.refusal_digest_disposition IS
  'WHY refusal_payload_digest holds the value it does, on a write_refused row -- mandatory there
   (two-way kind-shape CHECK, s44''s attest_verdict idiom), forbidden elsewhere. Closed two-member
   vocabulary: ''computed'' (the digest below is a real SHA-256 of the refused payload) or
   ''payload_over_bound'' (the payload''s canonical text exceeded 1,048,576 bytes, so no digest was
   computed -- refusal_payload_digest is NULL on this row). Table-coupled to refusal_payload_digest
   via refusal_payload_digest_disposition_coupling: a digest NULL row MUST declare
   payload_over_bound, a populated digest MUST declare computed -- the reason for an absence is a
   representable, typed value here, never an inference from a comment (ADR-0000''s
   unrepresentable-illegal-states principle, autoharn2 row 1105; maintainer ruling at merge-hold,
   2026-07-27, design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md §2 AMENDMENT).
   kernel/lineage/s67-refusal-digest-bound.sql.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_digest_disposition_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_digest_disposition_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_digest_disposition IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_digest_disposition_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_digest_disposition_check CHECK (
    refusal_digest_disposition IS NULL
    OR refusal_digest_disposition IN ('computed', 'payload_over_bound'));

-- refusal_payload_digest_kind_shape: UNCHANGED from this delta's first build (one-way -- the
-- digest is forbidden outside write_refused, and may legitimately be NULL within it). Re-applied
-- here (idempotent DROP+ADD) only because CREATE CONSTRAINT has no IF NOT EXISTS-equivalent
-- upsert and this file must be self-contained/re-runnable, the s17/s19/s23 idiom -- NOT a
-- semantic change from the first build.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_payload_digest_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_payload_digest_kind_shape CHECK (
    refusal_payload_digest IS NULL OR kind = 'write_refused');

COMMENT ON COLUMN :"schema".ledger.refusal_payload_digest IS
  'SHA-256 (hex) of the refused payload''s canonical text (payload::text of the jsonb
   argument -- key-sorted, deterministic on a given server; a cross-major-version recompute
   is a named limit, diagnostic linkage only). Digest, never verbatim (R4, ratified:
   adversary-authored content gets no permanent hash-chained storage channel). LEGITIMATELY
   NULL when refusal_digest_disposition = ''payload_over_bound'' (s67: kernel/lineage/
   s67-refusal-digest-bound.sql -- the direct-psql-bypass hazard the service''s own
   MAX_WRITE_BODY_BYTES cap cannot reach; a grep handle lost, never the refusal record itself,
   which is otherwise complete), TABLE-COUPLED to that column via
   refusal_payload_digest_disposition_coupling so the reason for a NULL digest is always a typed,
   representable fact, never an implicit sentinel (maintainer ruling at merge-hold, 2026-07-27,
   ADR-0000''s unrepresentable-illegal-states principle). kernel/lineage/
   s43-typed-verdict-write-boundary.sql; kernel/lineage/s67-refusal-digest-bound.sql.';

-- ============================================================================================
-- ELEMENT 1b -- THE COUPLING CHECK (§2 AMENDMENT item 2; s44's attest_expected_verdict_coupling
-- idiom, kind-guarded so the fragile `=`-of-a-possibly-NULL-column comparison only ever runs on
-- a row where refusal_digest_disposition is GUARANTEED non-NULL by Element 1's own two-way
-- kind-shape CHECK -- see this file's own header for the live psql test that falsifies the bare,
-- unguarded form the amendment's prose gives literally).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_payload_digest_disposition_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_payload_digest_disposition_coupling CHECK (
    kind <> 'write_refused'
    OR (refusal_payload_digest IS NULL) = (refusal_digest_disposition = 'payload_over_bound'));

COMMENT ON CONSTRAINT refusal_payload_digest_disposition_coupling ON :"schema".ledger IS
  'design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md §2 AMENDMENT''s fixed structural rule (maintainer
   ruling at merge-hold, 2026-07-27): a write_refused row''s digest is NULL if and only if its own
   disposition declares payload_over_bound -- the reason for an absent digest is table-caught, not
   commentary-inferred. kernel/lineage/s67-refusal-digest-bound.sql.';

-- ============================================================================================
-- ELEMENT 2 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 99 COLUMNS (the one new
-- column appended in catalog ordinal order, before the predecessor link; base body = s65's own
-- text, byte-identical above this delta's one appended line).
-- prior-body-sha256: 3bc5854af5404e99a98c8639c4a15a7693ca65135029d83deafd144e7d08f541 (s65-refusal-attempted-kind.sql)
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
      -- s67: the one new column, appended last before the predecessor link.
      hashfield(r.refusal_digest_disposition),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 3 -- THE TWO COLUMN-COMPLETE VIEWS, +1 APPENDED (the s20/s23/s65 lesson).
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
       l.refusal_digest_disposition
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
       l.refusal_digest_disposition
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 4 -- kernel.journal_write_refusal RE-ISSUED: the s65 body (kernel/lineage/
-- s65-refusal-attempted-kind.sql Element 4 -- the TRUE immediately-prior re-issue; s66 does NOT
-- touch this function, see this file's own header), BYTE-IDENTICAL above and below the new
-- bound, with the payload-size check now ALSO computing the typed disposition and writing it in
-- the SAME INSERT statement that writes (or NULLs) the digest (§2 AMENDMENT item 3 -- one
-- writer, one home). No other line of this function changes: the oracle bump stays first, the
-- write-boundary principal lookup and its own loud abort stay exactly as s43/s49/s65 left them,
-- the s49 attempted-actor guard and s65 attempted-kind extraction are untouched, and the journal
-- INSERT's own loud-abort-on-failure semantics are untouched.
-- prior-body-sha256: 59f5ba9b2a27015d51d692f90f97d043fa250b965b20a8239ca8bdb0c771362b (s65-refusal-attempted-kind.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".journal_write_refusal(
    p_surface text, p_payload jsonb, p_sqlstate text, p_message text)
    RETURNS bigint LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_wb bigint;
  v_attempted bigint;
  v_attempted_kind text;
  v_digest text;
  v_disposition text;
  v_id bigint;
BEGIN
  -- the oracle bump, BEFORE the journal INSERT (non-transactional, survives everything --
  -- s43 Element 5): if the INSERT below then fails, the sequence shows a counted gap the
  -- verify-chain reconciliation names. UNCHANGED by s67.
  PERFORM nextval('refusal_seq');
  SELECT id INTO v_wb FROM principal WHERE name = 'write-boundary';
  IF v_wb IS NULL THEN
    RAISE EXCEPTION 'write boundary: the ''write-boundary'' tool principal is not registered in this world -- refusal recording has no authoring identity (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 6; bootstrap/new-project.sh''s birth sequence registers it). The original refusal (SQLSTATE %) was: %', p_sqlstate, p_message;
  END IF;
  -- the ATTEMPTED identity: the explicit payload actor when it resolves to a registered id,
  -- else the session's own standing-declaration default (the identity that WOULD have been
  -- attributed); NULL when neither resolves -- the role below is still always known.
  --
  -- s49 GUARD (kernel/lineage/s49-journaler-overflow-guard.sql): the regex `^[0-9]+$` admits
  -- arbitrary-length digit strings, but bigint's own range does not -- an over-bigint numeral
  -- previously raised 22003 HERE; the cast is total (UNCHANGED by s67).
  IF (p_payload ? 'actor') AND (p_payload->>'actor') ~ '^[0-9]+$' THEN
    BEGIN
      SELECT id INTO v_attempted FROM principal WHERE id = (p_payload->>'actor')::bigint;
    EXCEPTION WHEN numeric_value_out_of_range THEN
      v_attempted := NULL;
    END;
  END IF;
  IF v_attempted IS NULL THEN
    SELECT principal_id INTO v_attempted FROM principal_role WHERE db_role = session_user;
  END IF;
  -- s65 (kernel/lineage/s65-refusal-attempted-kind.sql): the ATTEMPTED kind, extracted from the
  -- refused payload -- TOTAL, NULL when not extractable (key absent, non-string, or over the
  -- 256-byte bound). UNCHANGED by s67.
  IF jsonb_typeof(p_payload->'kind') = 'string'
     AND octet_length(p_payload->>'kind') <= 256 THEN
    v_attempted_kind := p_payload->>'kind';
  ELSE
    v_attempted_kind := NULL;
  END IF;
  -- s67 BOUND, RE-SHAPED PER THE §2 AMENDMENT (kernel/lineage/s67-refusal-digest-bound.sql): the
  -- refused payload's canonical text is digested WHOLE only up to 1,048,576 bytes (the s51
  -- artifact_too_large precedent -- the same figure the service's own MAX_WRITE_BODY_BYTES
  -- already enforces on the served path, restated here for the direct-psql bypass that cap
  -- cannot reach). The digest and its OWN typed disposition are computed and written TOGETHER,
  -- in this one IF/ELSE, so the two columns can never drift apart from two separate code paths
  -- (amendment item 3, "one writer, one home"). The refusal ITSELF (surface/sqlstate/message/
  -- attempted actor/role/kind) is unaffected and journals in full regardless of payload size --
  -- only the digest, a grep handle never a join key (row-1498 witness), is foreclosed on an
  -- attacker-sized payload, and its absence is now a DECLARED fact (v_disposition), never an
  -- implicit NULL a reader must infer the meaning of.
  IF octet_length(p_payload::text) > 1048576 THEN
    v_digest := NULL;
    v_disposition := 'payload_over_bound';
  ELSE
    v_digest := encode(sha256(convert_to(p_payload::text, 'utf8')), 'hex');
    v_disposition := 'computed';
  END IF;
  INSERT INTO ledger (kind, statement, actor,
                      refusal_sqlstate, refusal_message, refusal_surface,
                      refusal_payload_digest, refusal_attempted_actor, refusal_attempted_role,
                      refusal_attempted_kind, refusal_digest_disposition)
  VALUES ('write_refused',
          format('write refused at surface %s (SQLSTATE %s)', p_surface, p_sqlstate),
          v_wb,
          p_sqlstate, p_message, p_surface,
          v_digest,
          v_attempted, session_user,
          v_attempted_kind, v_disposition)
  RETURNING id INTO v_id;
  RETURN v_id;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) FROM PUBLIC;

COMMENT ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) IS
  'The ONE home of "a refusal becomes a committed write_refused row" (s43 Element 4), called
   only from inside the SECURITY DEFINER boundary functions (no role holds EXECUTE). Bumps the
   refusal_seq oracle FIRST (non-transactional), then journals: actor = the write-boundary tool
   principal; the attempted identity in refusal_attempted_* (s49: the actor cast is TOTAL); the
   attempted kind token in refusal_attempted_kind (s65: TOTAL, 256-byte bound); the payload as a
   SHA-256 digest, plus its own typed refusal_digest_disposition (''computed'' or
   ''payload_over_bound'', table-coupled -- s67: kernel/lineage/s67-refusal-digest-bound.sql,
   §2 AMENDMENT -- the direct-psql-bypass hazard the service''s own size cap cannot reach,
   digest NULL only ever with a declared reason, never an implicit sentinel). If the journal
   INSERT itself fails the exception propagates -- a loud abort, a counted sequence gap, the
   server log as residual coverage (fail-safe on both legs, unchanged by s49/s65/s67).
   kernel/lineage/s43-typed-verdict-write-boundary.sql; kernel/lineage/
   s49-journaler-overflow-guard.sql; kernel/lineage/s65-refusal-attempted-kind.sql;
   kernel/lineage/s67-refusal-digest-bound.sql.';
-- ============================================================================================
