-- s41 PRINCIPAL BINDINGS AND RELATIONS (design/FABLE-PRINCIPAL-IDENTITY-SPEC-BUILD-BASIS.md §4,
-- the FROZEN build basis read AS CORRECTED by its dated amendment block C1-C13; ratifications:
-- ledger rows 1419 and 1426; competence grants BUILT by maintainer ruling row 1411; Fable-built
-- per C12). SECOND delta of the s40/s41 family -- everything a registered identity can be bound
-- TO: roles, cryptographic keys (the empty slot, not the ceremony), competence grants, and typed
-- relationships to other principals. This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING
-- it to any live/existing world is the maintainer's act at a FUTURE world's birth (runs-are-
-- strictly-linear, 2026-07-11). An ADDITIVE delta on the s15..s40 kernel, NOT a retro-edit of a
-- frozen record (ADR-0005 Rule 8) and NOT a second copy of any mechanism (ADR-0012 P1: binding
-- events ride the ledger; retraction is s31 supersession, uniformly -- no *_revoked/*_released
-- kinds are minted, one retraction mechanism, one home).
--
-- PREREQUISITE: this delta REQUIRES s40 (kernel/lineage/s40-principal-identity-events.sql)
-- applied first -- a HARD dependency (basis §2): it re-issues s40's principal_subject_kind_shape
-- CHECK widened (the constraint must exist to DROP meaningfully; more to the point, the four
-- binding kinds' rows are attributed under s40's strict attribution and their subjects are
-- s40-registered principals), and re-issues ledger_current/countersigned_in_force in the exact
-- column-list shape s40 left them. Applying this file on a pre-s40 kernel fails loudly at
-- CREATE OR REPLACE VIEW time (column l.principal_subject does not exist), the correct,
-- disclosed failure mode, matching every prior PREREQUISITE precedent.
--
-- WHY (operator-side prose): the basis §1/§2. The panel deployment's `acts_for` column sat
-- unused across 1800+ rows because it is single-valued, undated, kind-less; `reviewer`
-- (subagent) vs `reviewer2` (model) drifted with no event recording either assignment; the
-- ratified GPG trust layer's §5 assumes a principal<->key binding the schema could not
-- represent; the BRIEF's G13 competence record had a reserved name and no typed home. This
-- delta gives each of those facts ONE home as an append-only attributed event, current truth as
-- a derived view, retraction by supersession.
--
-- D-1: FOUR NEW KINDS (kind CHECK re-issued wider): principal_relation_asserted,
-- principal_role_bound, principal_key_bound, principal_competence_granted (the fourth BUILT by
-- maintainer ruling, row 1411, overruling the consultation's named-not-built suggestion).
--
-- THE IDENTITY/VALUE SPLIT + WITHDRAWAL-WITH-NO-REPLACEMENT (D-1, a fixpoint-review closure):
-- each kind's columns split into IDENTITY fields (which binding this row is about -- mandatory
-- on EVERY row of the kind, active or not: a retraction that doesn't say what it retracts isn't
-- a retraction) and VALUE fields (the content of an active binding -- mandatory when asserted,
-- FORBIDDEN when not). One shared boolean carries the distinction: principal_binding_active --
-- nullable, NO column DEFAULT (the s30 lesson; a column-level default would populate every
-- OTHER kind's writes too), mandatory via the kind-shape CHECK on the four new kinds (never a
-- column-level NOT NULL -- basis C10), forbidden on every s40 kind and the generic path. A
-- fresh assertion explicitly supplies true in its VALUES list; a retraction is a NEW row of the
-- SAME kind, superseding the prior row, active = false, restating only the identity field(s).
-- A structural CHECK refuses active = false with supersedes IS NULL (an inactive-FROM-BIRTH
-- binding -- one never asserted -- is nonsensical and unrepresentable). For relation_asserted/
-- role_bound/key_bound ALL content columns ARE identity fields (there is no separate value
-- field); only principal_competence_granted splits: activity is identity (a principal may hold
-- grants for several activities, so a retraction must say which), band/basis are value
-- (mandatory iff active).
--
-- D-2 COLUMNS (all nullable, no DEFAULT; kind-shape CHECKs below; the re-issued
-- principal_subject_kind_shape licenses ALL EIGHT principal_* kinds, enumerated in full --
-- a re-issue licensing only seven would be a defect, not a valid reading):
--   principal_binding_active boolean -- the identity/value discriminator (above).
--   principal_object bigint REFERENCES kernel.principal(id) -- relation_asserted's far
--     endpoint (identity field).
--   principal_relation text -- closed vocabulary {acts-for, dispatched-by, same-natural-person,
--     succeeds} (identity field). This vocabulary IS kernel-structural (D-3's self-edge refusal
--     and the canonicalization CHECK key off the values), unlike...
--   principal_role_name text -- FREE NON-EMPTY TEXT, NOT a closed vocabulary (§9(c) RATIFIED +
--     C13: role naming is organizational configuration, not the harness's to impose; witnessed
--     derivation ledger rows 1432/1433 -- NIST AC-2(a)/OSCAL require an account-type governance
--     PROCESS, not a data-layer enumeration; nothing in this delta's own CHECKs or triggers
--     branches on WHICH role name a binding carries).
--   principal_key_fingerprint text -- shape CHECK ~ '^[0-9A-F]{40}$' (an OpenPGP v4
--     fingerprint, uppercase hex, the form design/MAINT-GPG-TRUST-LAYER.md §5 implies; a longer
--     future-format digest is REFUSED like any malformed witness -- the s38 SHA-256 posture --
--     named, never silently coerced or truncated).
--   principal_competence_activity/band/basis text -- G13's three fields (activity identity;
--     band/basis value, mandatory-iff-active). FREE TEXT, non-empty, in v1 -- §9(g) RATIFIED
--     with the maintainer's REQUIRED loud note: this is a PLACEHOLDER ARCHITECTURE ONLY, not a
--     considered final design; whether band/activity become a closed vocabulary (and under
--     which band system -- ASIL/SIL/DAL or a house scheme) is deferred until the deployment
--     population's conventions exist and bandwidth allows extending it properly. A reader must
--     not mistake the free-text shape for a settled judgment that no closed vocabulary is ever
--     warranted.
--
-- D-3 STRUCTURAL (KERNEL-LEVEL) REFUSALS: a BEFORE INSERT trigger (validate_principal_binding,
-- alphabetical position between validate_enacts and validate_review -- it reads only NEW +
-- kernel.principal, so its position among the validators is immaterial and its name follows
-- the family convention) refuses (a) a self-edge on principal_relation_asserted, for all four
-- relation values, and (b) principal_key_bound unless the subject's agent_class = 'human' --
-- AGENT KEYS STAY REFUSED, the GPG spec's §6 carried into the type. Both endpoints' existence
-- is already forced by the FKs (the trigger adds nothing further -- stated, not silently
-- relied on). A FOURTH, plain CHECK (not a trigger -- a same-row constraint needs no
-- cross-table lookup): principal_relation IS DISTINCT FROM 'same-natural-person' OR
-- principal_subject < principal_object -- the CLI's canonicalization made KERNEL-ENFORCED (a
-- fixpoint-review closure: a direct-psql write could otherwise construct a non-canonical row a
-- subsequent canonical-order relate would not detect as a duplicate). Principal ids are
-- assigned once and never reused, so "lower id" is a stable ordering for both lifetimes --
-- this CHECK cannot flip its own verdict later. VALUE-CONTINUITY on release/revoke/withdrawal
-- is CLI-side, NOT kernel-side, for all four kinds (see LIMITS -- the one place D-1's
-- "identity field, mandatory always" rule has no kernel-level cross-row check behind it).
--
-- D-4 THE CRYPTO RECONCILIATION, carried here so no future auditor re-litigates it (basis,
-- verbatim in substance): the standing deferral ("key generation/signing deferred until all
-- else banked; never re-raise as recommendation") governs the operational CEREMONY. The
-- maintainer's grounding injection names cryptographic authentication a first-class concern
-- for the principal-surface DESIGN. These do not conflict: MODELING the binding is in scope
-- now; PERFORMING the ceremony remains deferred. principal_key_bound is an empty-until-
-- ceremony slot -- a strictly additive fact that may sit unexercised indefinitely (the
-- STANDARDS-REGISTRY posture: named, never silently absent). The residual tension (the
-- deferral said never re-raise; the maintainer himself re-raised the modeling half) is
-- resolved by the newer maintainer word governing -- recorded here precisely so it is settled.
-- Nothing in this delta generates a key, recommends generating one, or wires signing.
--
-- D-5 DERIVED VIEWS (security_invoker, SELECT to :role; all four filter unsuperseded AND
-- principal_binding_active -- the withdrawal fix means "unsuperseded" alone is NO LONGER
-- sufficient: a retraction chain's terminal row is itself unsuperseded but active = false and
-- must not read as a live binding): principal_relations, principal_role_bindings (deliberately
-- NOT named principal_roles: the singular kernel.principal_role view (s40) is the structurally
-- unrelated db-role<->principal binding, and a near-identical plural would invite conflation),
-- principal_keys, principal_competences. Role bindings and competence grants are RECORDABLE,
-- NOT YET GATING: no review path checks entitlement or competence in v1 -- the representational
-- foreclosure ships now; enforcement (refusing a countersign by an unbound principal; consulting
-- competence before accepting an act) is the NAMED follow-on ratified amendment (basis §7 items
-- 4/6), never smuggled in as a side effect.
--
-- D-6 INDEPENDENCE-VOCABULARY HONESTY (§9(a) RATIFIED: human-attested scoping, the default --
-- accepted as lax but documented; not the outright-refusal alternative): validate_independence
-- (s17-defined, s21/s29/s34-extended) is re-issued -- the HEAD's body (s34's), behavior-
-- fingerprinted -- with ONE added refusal: a review claiming managerial or financial
-- independence is refused unless the review's actor principal has agent_class = 'human'. The
-- stamp-distinctness gate stays untouched on top (its refusals run FIRST, byte-identical).
-- This is additive-refusal, fail-safe in shape, and ends the quiet overclaim where a
-- stamp-distinct model pair could assert an unwitnessable grade (IEEE 1012's managerial/
-- financial dimensions). The function's SET search_path gains :"kern" (it now reads
-- kernel.principal's agent_class) -- a header change, not a branch change; every pre-existing
-- branch's text is byte-identical to s34's. s18-CLASS ARMING NOTE (basis C4, ruled -- the
-- enumerated column grant, not a new SECURITY DEFINER accessor): an s18-style deployment must
-- grant its reviewer roles (1) EXECUTE on kernel.principal_standing [s40], (2) SELECT on the
-- kernel.principal_role view [s40], and (3) SELECT (agent_class) ON kernel.principal [this
-- delta] -- without (3), an s18 reviewer asserting a managerial/financial claim meets an
-- untaught permission-denied instead of this refusal's taught text. s18 itself is not in the
-- birth chain; the enumeration lives here for its arming script.
--
-- D-7 acts_for RETIRED BY SUPERSESSION, NOT DELETION: the column stays (frozen-record
-- discipline; s13/s14/s15 texts are never retro-edited) but gains CHECK acts_for IS NULL --
-- argued (not assumed) safe: it whole-table-validates at ADD CONSTRAINT time and passes on any
-- world whose history carries no non-NULL acts_for -- true of every world this delta can ever
-- reach (birth chains only; the panel's history is dust and stays dust; the consultation
-- verified the value was never once used in any live history). The one home for delegation is
-- now the acts-for relation EVENT.
--
-- D-8 HISTORY: safe -- per-mechanism grounds (as corrected by C3):
--   * additive kind vocabulary (re-issue wider; pre-existing kinds untouched).
--   * EIGHT new nullable no-default columns, kind-scoped mandatory/forbidden by CHECKs that
--     validate vacuously on pre-existing rows (no pre-existing row carries the new kinds).
--   * principal_subject_kind_shape re-issued WIDER (the four s40 kinds keep their exact
--     legality; four new kinds join the licensed set -- additive on both sides of the iff).
--   * all new CHECKs vacuous on pre-existing rows EXCEPT acts_for IS NULL, argued above (D-7).
--   * validate_independence re-issue: NEW-REFUSAL-ONLY; pre-existing branches byte-identical
--     to s34's text (the search_path clause gains :"kern" -- a resolution-context addition
--     that changes no pre-existing branch's behavior: every name those branches read resolves
--     in :schema, which stays first).
--   * validate_principal_binding is a NEW trigger firing only on kinds born in this delta.
--   * C3 (the s20 view-re-issue leg an earlier draft omitted, executed): ledger_current and
--     countersigned_in_force re-issued with the EIGHT s41 columns appended at the end
--     (principal_actor_resolution moved to s40 per C1 and is already in their lists). The
--     §3.8 non-member re-verification (work_item_current, work_item_violations,
--     work_violation_history, work_review_gap, review_gap, question_status,
--     review_stamp_distinctness, work_edge_*, work_startable, work_bookkeeping_closes,
--     standing_decisions, principal_standing_current [reads named s40 columns only]) repeats
--     here: none does general column passthrough; none is re-issued.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's slice -- the FAMILY
-- closure is the basis §5, checked against the consultation's §4 universe):
--   - INVARIANT: every binding or relationship a registered identity carries -- role bindings,
--     key bindings (human subjects only), competence grants, and the four typed principal<->
--     principal relations -- is an append-only, attributed, dated ledger event; current
--     bindings are derived views over unsuperseded, active rows; retraction is uniformly a
--     superseding same-kind row with active = false restating the identity fields (value
--     fields forbidden); an inactive-from-birth binding, a self-relation, an agent-keyed
--     binding, a non-canonical same-natural-person ordering, and a non-NULL acts_for are
--     unrepresentable at construction; no identity fact has a second home outside its event.
--   - QUANTIFICATION UNIVERSE (checked outward, the s38 lesson):
--       KINDS carrying each new column: enumerated per-CHECK below; principal_subject's
--         re-issued CHECK enumerates ALL EIGHT principal kinds in one home.
--       VIEWS: the two projection homes re-issued (+8, C3); D-5's four new views + s40's
--         principal_standing_current factor through ledger_current (allowlist gate witnesses
--         all classifying clean); non-members re-verified (D-8).
--       TRIGGERS: one NEW BEFORE INSERT member (validate_principal_binding) -- fires only on
--         two of the four new kinds' rows plus the relation CHECK's kinds; ordering among the
--         validators immaterial (reads only NEW + kernel.principal); still before
--         zz_set_row_hash alphabetically. validate_independence re-issued in place (its
--         trigger definition on review_detail unchanged).
--       ENGINE: entry/6 emission is kind-generic (verified at s40; unchanged here); the four
--         new kinds flow through; ./judge witnessed in AGREE on a fixture carrying every s41
--         kind (this delta's fixture). No new .lp predicate (no T_now derivation of its own).
--       HASH CHAIN: the eight new columns are OUTSIDE compute_row_hash's serialization
--         (s28..s40 precedent, named in LIMITS -- the standing lineage-wide limit).
--       GATES: kind_shape_manifest_gate CHAIN += s41, principal_subject row widened to eight
--         kinds, eight new MANIFEST rows; ledger_reader_allowlist CHAIN += s41 (no new entry
--         needed, witnessed); fixture census registers this delta's seen-red. All in this
--         same commit.
--       CLI: eight new `led principal` verbs (relate/unrelate, bind-role/release-role,
--         bind-key/revoke-key, grant-competence/withdraw-competence), each through
--         resolve_actor, each honoring --event-time and refusing the other shared channels
--         (meta-consult Axis 1 discipline); the general channel-coverage gate stays OUT
--         (basis §7 item 1, the RCA's to mint).
--   - DENOMINATION: relations in a closed four-value vocabulary the kernel's own refusals key
--     off; role names free-non-empty BY RATIFIED RULING (organizational configuration, §9(c));
--     key custody in an OpenPGP-v4-shaped fingerprint (derived from the format it names, the
--     one regex in the family); competence in G13's three fields, free-text v1 BY RATIFIED
--     PLACEHOLDER (§9(g), loud note above); the active/inactive discriminator a boolean on
--     the row, never a stored view-side verdict; canonical same-natural-person ordering
--     denominated in immutable principal ids, never names.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (basis §9): it re-issues a live trigger body
-- (validate_independence) and, though every behavioral delta is additive (new kinds, new
-- refusals, new derived views, one vacuously-validated retirement CHECK), it ships as the
-- second half of the family under the basis's own ratification (rows 1419/1426), never under
-- the 2026-07-09 class rule.
--
-- LIMITS (pre-registered; the basis §8, this delta's slice):
--   - Trigger/CHECK refusals bind the granted role's ordinary INSERT path only (superuser
--     bypass, the standing disclosed bound).
--   - VALUE-CONTINUITY on release/revoke/withdrawal is enforced by the sanctioned CLI verbs,
--     NOT by a kernel CHECK: a direct-psql write bypassing release-role/revoke-key/
--     withdraw-competence/unrelate could construct a superseding row whose restated identity
--     value mismatches its target's, or that targets an already-inactive row. Cross-row
--     value-matching genuinely needs a lookup the kernel's CHECK machinery cannot express;
--     same accepted direct-writer boundary as ever -- named, not silent. (The same-natural-
--     person canonical ordering is NOT in this category: a same-row property, kernel-CHECKed.)
--   - D-6 is the RATIFIED human-attested scoping -- accepted as lax but documented (§9(a)):
--     a human principal CAN attest a managerial/financial claim in their own right; no schema
--     can witness the claim's truth, only its attestor's class.
--   - Role bindings/competence grants are recordable, NOT gating (D-5) -- entitlement and
--     competence ENFORCEMENT are named follow-on amendments (basis §7 items 4/6).
--   - The competence band/basis vocabulary is a PLACEHOLDER (§9(g), the maintainer's own loud
--     note) -- free text non-empty, quality unenforceable beyond that; the countersign path is
--     the control.
--   - The eight new columns are outside the row-hash serialization (s28..s40 precedent).
--   - In a solo world, every governance event is written by the one operator's principals; the
--     record is complete and attributed, not adversarially independent (s17's own honesty).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s40):
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s41val -v kern=s41val_kernel -v role=s41val_rw \
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
--        -f s40-principal-identity-events.sql -f s41-principal-bindings-and-relations.sql
--     (genesis seed per s26; the s40 birth acts per that delta's own VALIDATE note.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in this SAME commit.
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP/CREATE TRIGGER).
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
-- D-1 -- KIND VOCABULARY WIDENED (four binding/relation kinds; additive union).
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
     'principal_competence_granted'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s41-principal-bindings-and-relations.sql: widens s40''s nineteen-member
   vocabulary by the four binding/relation kinds (relation_asserted/role_bound/key_bound/
   competence_granted). Retraction of any of the four is s31 supersession with
   principal_binding_active = false -- no *_revoked/*_released kinds exist (one retraction
   mechanism, one home).';

-- ============================================================================================
-- D-2 -- THE EIGHT NEW COLUMNS + CHECKs. principal_subject_kind_shape is RE-ISSUED here,
-- widened to license all EIGHT principal_* kinds (one home -- never patched by a second
-- constraint).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_binding_active boolean;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_object bigint
    REFERENCES :"kern".principal(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_relation text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_role_name text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_key_fingerprint text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_competence_activity text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_competence_band text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS principal_competence_basis text;

COMMENT ON COLUMN :"schema".ledger.principal_binding_active IS
  'The identity/value discriminator of the four s41 binding kinds: true = a fresh assertion
   (value fields mandatory), false = a retraction (a superseding row restating only the
   identity fields; value fields forbidden; supersedes mandatory -- an inactive-from-birth
   binding is unrepresentable). Nullable with NO default (mandatory via the kind-shape CHECK on
   exactly the four s41 kinds -- never a column-level NOT NULL, basis C10; forbidden on every
   other kind). kernel/lineage/s41-principal-bindings-and-relations.sql D-1.';
COMMENT ON COLUMN :"schema".ledger.principal_relation IS
  'The typed principal<->principal relation a principal_relation_asserted row asserts between
   principal_subject and principal_object: acts-for | dispatched-by | same-natural-person |
   succeeds (closed vocabulary -- the kernel''s own refusals key off these values, unlike
   principal_role_name''s ratified free text). same-natural-person rows are canonically ordered
   (subject id < object id, kernel CHECK). dispatched-by is the DECLARATION of a supervision
   fact whose WITNESS remains the stamp pair -- declaration and evidence denominated
   separately. kernel/lineage/s41-principal-bindings-and-relations.sql D-2.';
COMMENT ON COLUMN :"schema".ledger.principal_role_name IS
  'The organizational role a principal_role_bound row binds to its subject. FREE NON-EMPTY
   TEXT, NOT a closed vocabulary -- ratified (basis §9(c)/C13; witnessed derivation ledger rows
   1432/1433: AC-2(a)/OSCAL mandate an account-type governance PROCESS, not a data-layer
   enumeration): a deployment names its own roles; the kernel enforces only that a name was
   given. kernel/lineage/s41-principal-bindings-and-relations.sql D-2.';
COMMENT ON COLUMN :"schema".ledger.principal_key_fingerprint IS
  'The OpenPGP v4 fingerprint (40 uppercase hex chars, shape-CHECKed) a principal_key_bound row
   binds to its HUMAN subject (agent keys refused -- design/MAINT-GPG-TRUST-LAYER.md §6 carried
   into the type). The EMPTY-UNTIL-CEREMONY slot: modeling the binding is in scope; key
   generation/signing stays deferred by standing ruling (D-4 reconciliation, this delta''s
   header). A longer future-format digest is refused like any malformed witness (the s38
   posture). kernel/lineage/s41-principal-bindings-and-relations.sql D-2.';
COMMENT ON COLUMN :"schema".ledger.principal_competence_activity IS
  'G13''s "safety activity" field (IDENTITY: mandatory on every principal_competence_granted
   row, active or not -- a withdrawal must say WHICH activity). Free text non-empty.
   kernel/lineage/s41-principal-bindings-and-relations.sql D-1a.';
COMMENT ON COLUMN :"schema".ledger.principal_competence_band IS
  'G13''s integrity-band field (VALUE: mandatory non-empty when active, forbidden when not).
   FREE TEXT IN V1 -- ratified as a PLACEHOLDER ARCHITECTURE ONLY (basis §9(g), the
   maintainer''s required loud note): whether this becomes a closed vocabulary, and under which
   band system, is deferred until deployment conventions exist -- not a settled judgment that
   no closed vocabulary is warranted. kernel/lineage/s41-principal-bindings-and-relations.sql.';
COMMENT ON COLUMN :"schema".ledger.principal_competence_basis IS
  'G13''s competence-basis field (training, track record, certification reference). VALUE field,
   same mandatory-iff-active shape as band; quality unenforceable beyond non-emptiness -- the
   countersign path is the control. kernel/lineage/s41-principal-bindings-and-relations.sql.';

-- principal_subject: ONE home, re-issued wider (all eight principal kinds).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_subject_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_subject_kind_shape CHECK (
    (kind IN ('principal_registered','principal_suspended','principal_revoked',
              'principal_standing_declared',
              'principal_relation_asserted','principal_role_bound','principal_key_bound',
              'principal_competence_granted')) = (principal_subject IS NOT NULL));

-- kind-shape CHECKs for the new columns (two-way where the field is identity-mandatory on its
-- one kind; one-way for the two value fields, whose mandatory-iff-active rule is a separate,
-- kind-free CHECK below):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_binding_active_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_binding_active_kind_shape CHECK (
    (kind IN ('principal_relation_asserted','principal_role_bound','principal_key_bound',
              'principal_competence_granted')) = (principal_binding_active IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_object_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_object_kind_shape CHECK (
    (kind = 'principal_relation_asserted') = (principal_object IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_relation_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_relation_kind_shape CHECK (
    (kind = 'principal_relation_asserted') = (principal_relation IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_role_name_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_role_name_kind_shape CHECK (
    (kind = 'principal_role_bound') = (principal_role_name IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_key_fingerprint_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_key_fingerprint_kind_shape CHECK (
    (kind = 'principal_key_bound') = (principal_key_fingerprint IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_competence_activity_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_competence_activity_kind_shape CHECK (
    (kind = 'principal_competence_granted') = (principal_competence_activity IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_competence_band_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_competence_band_kind_shape CHECK (
    principal_competence_band IS NULL OR kind = 'principal_competence_granted');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_competence_basis_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_competence_basis_kind_shape CHECK (
    principal_competence_basis IS NULL OR kind = 'principal_competence_granted');

-- value/structural CHECKs (no kind test -- ordinary business-rule CHECKs, out of the kind-shape
-- manifest's scope by its classifier's own first test):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_relation_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_relation_check CHECK (
    principal_relation IS NULL
    OR principal_relation IN ('acts-for','dispatched-by','same-natural-person','succeeds'));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_role_name_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_role_name_nonempty CHECK (
    principal_role_name IS NULL OR btrim(principal_role_name) <> '');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_key_fingerprint_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_key_fingerprint_shape CHECK (
    principal_key_fingerprint IS NULL OR principal_key_fingerprint ~ '^[0-9A-F]{40}$');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_competence_activity_nonempty;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_competence_activity_nonempty CHECK (
    principal_competence_activity IS NULL OR btrim(principal_competence_activity) <> '');

-- an inactive-from-birth binding is unrepresentable: only a superseding row may set false.
-- (NULL active -- every non-binding kind -- passes vacuously; the kind-shape CHECK owns
-- mandatoriness.)
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_binding_inactive_needs_supersedes;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_binding_inactive_needs_supersedes CHECK (
    principal_binding_active IS NULL OR principal_binding_active OR supersedes IS NOT NULL);

-- the competence identity/value split (D-1a): band and basis are mandatory non-empty iff the
-- grant row is active, forbidden on a withdrawal. Guarded via principal_competence_activity
-- (non-NULL exactly on this kind, by its own two-way CHECK) so this CHECK needs no `kind` test
-- of its own.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_competence_band_iff_active;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_competence_band_iff_active CHECK (
    principal_competence_activity IS NULL
    OR (principal_binding_active AND btrim(coalesce(principal_competence_band, '')) <> '')
    OR ((NOT principal_binding_active) AND principal_competence_band IS NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_competence_basis_iff_active;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_competence_basis_iff_active CHECK (
    principal_competence_activity IS NULL
    OR (principal_binding_active AND btrim(coalesce(principal_competence_basis, '')) <> '')
    OR ((NOT principal_binding_active) AND principal_competence_basis IS NULL));

-- D-3's fourth refusal, the plain same-row CHECK (not a trigger): same-natural-person rows are
-- canonically ordered by immutable principal id, so ONE row shape exists per unordered pair --
-- the duplicate guard needs no special-casing, and a direct-psql non-canonical write cannot
-- silently defeat it (the fixpoint-review closure).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS principal_snp_canonical_order;
ALTER TABLE :"schema".ledger ADD CONSTRAINT principal_snp_canonical_order CHECK (
    principal_relation IS DISTINCT FROM 'same-natural-person'
    OR principal_subject < principal_object);

-- ============================================================================================
-- s20 LESSON, C3's leg: the two projection homes gain the EIGHT s41 columns, appended at the
-- end. Column list = s40's exact list + the eight.
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
       l.principal_competence_basis
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
       l.principal_competence_basis
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- D-3 -- THE STRUCTURAL TRIGGER (self-edges; human-only keys). Reads only NEW +
-- kernel.principal; no ledger read at all.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_principal_binding() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_class text;
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
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_principal_binding ON :"schema".ledger;
CREATE TRIGGER validate_principal_binding BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_principal_binding();

-- ============================================================================================
-- D-6 -- validate_independence RE-ISSUED (s17-defined, s21/s29/s34-extended; CREATE OR
-- REPLACE, the SAME function -- ADR-0012 P1). ONE added refusal, placed INSIDE the
-- independence-claiming branch AFTER the stamp-distinctness gate (which stays untouched on
-- top, byte-identical); the search_path gains :"kern" (this body now reads
-- kernel.principal.agent_class). Every pre-existing branch is byte-identical to s34's text.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_independence() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  rev_session text; rev_agent text; rev_verified boolean; regards_id bigint;
  tgt_session text; tgt_agent text;
  distinct_pair boolean;
  rev_actor bigint; rev_actor_class text;
BEGIN
  -- s34: discharge_grade is a KERNEL-COMPUTED fact, never a writer assertion (s29's own COMMENT
  -- ON COLUMN). Pre-s34, a writer-supplied value was silently OVERWRITTEN by the computation below
  -- with no error (ledger finding 1157) -- refuse it instead, loudly, before any other branch runs.
  IF NEW.discharge_grade IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: review_detail.discharge_grade is COMPUTED by the kernel from this review''s own independence facts (the (stamp_session,stamp_agent) pair comparison between this review and the row it regards) -- it is never writer-asserted (kernel/lineage/s29-obligation-item-key-and-typed-close.sql''s own COMMENT ON COLUMN). A supplied value (%) is refused here, not silently accepted: prior to this delta (kernel/lineage/s34-computed-grade-refusal.sql), a writer-supplied grade was silently OVERWRITTEN by the computed value with no error, so a caller who believed their asserted grade was honored had no way to discover it was discarded (ledger finding 1157). Omit discharge_grade on INSERT (leave it NULL/unset) -- this trigger computes and sets it for you.', NEW.discharge_grade;
  END IF;

  SELECT stamp_session, stamp_agent, stamp_verified, regards
    INTO rev_session, rev_agent, rev_verified, regards_id FROM ledger WHERE id = NEW.ledger_id;
  SELECT stamp_session, stamp_agent INTO tgt_session, tgt_agent FROM ledger WHERE id = regards_id;

  IF NEW.independence IN ('technical','managerial','financial') THEN
    IF NOT COALESCE(rev_verified, false) THEN
      RAISE EXCEPTION 'Ledger policy: a review claiming independence (%) must carry a VERIFIED interception stamp — an unstamped review cannot establish it was a distinct invocation. Record independence=''self-review'' if you reviewed your own work, or write the review through a genuinely distinct stamped invocation (a separate agent).', NEW.independence;
    END IF;
    -- identity is the PAIR; a NULL half (on either row) is NEVER distinct — fail-safe, never fail-open.
    distinct_pair := (rev_session IS NOT NULL AND rev_agent IS NOT NULL
                       AND tgt_session IS NOT NULL AND tgt_agent IS NOT NULL)
                      AND (rev_session IS DISTINCT FROM tgt_session
                           OR rev_agent IS DISTINCT FROM tgt_agent);
    IF NOT distinct_pair THEN
      RAISE EXCEPTION 'Ledger policy: this review claims independence (%) but the SAME invocation (session=%, agent=%) wrote both it and the row it regards — one context cannot countersign its own work as independent (finding 31 / s21 session-aware distinctness). Record independence=''self-review'' if you reviewed your own work, or have a genuinely distinct invocation (a different session, or a different agent within this session) write the review.', NEW.independence, rev_session, rev_agent;
    END IF;
    -- s41 D-6 (§9(a) RATIFIED: human-attested scoping): the managerial/financial vocabulary is
    -- honest only when a human attests it in their own right — the stamp-distinctness gate
    -- above stays untouched on top; this refusal is ADDITIVE, after it.
    IF NEW.independence IN ('managerial','financial') THEN
      SELECT actor INTO rev_actor FROM ledger WHERE id = NEW.ledger_id;
      SELECT p.agent_class INTO rev_actor_class FROM principal p WHERE p.id = rev_actor;
      IF rev_actor_class IS DISTINCT FROM 'human' THEN
        RAISE EXCEPTION 'Ledger policy: no schema can witness %-grade independence between model principals sharing one orchestrator and one payer (IEEE 1012''s managerial/financial dimensions; the principal-surface consultation §1.3) — this review''s actor principal % has agent_class ''%''. Claim independence=''technical'' (stamp-witnessed), or have a HUMAN principal attest this claim in their own right (s41 D-6, human-attested scoping — ratified basis §9(a)).', NEW.independence, rev_actor, rev_actor_class;
      END IF;
    END IF;
  END IF;

  -- Element C (s29): independence GRADE, computed for EVERY discharge act (not only an
  -- independence-CLAIMING one), closed vocabulary, fail-safe same-principal default. UNCHANGED
  -- from s29's version -- s34 only guards entry to this block via the refusal above.
  IF rev_session IS NULL OR rev_agent IS NULL OR tgt_session IS NULL OR tgt_agent IS NULL THEN
    NEW.discharge_grade := 'same-principal';
  ELSIF rev_session IS NOT DISTINCT FROM tgt_session AND rev_agent IS NOT DISTINCT FROM tgt_agent THEN
    NEW.discharge_grade := 'same-principal';
  ELSIF rev_session IS NOT DISTINCT FROM tgt_session THEN
    NEW.discharge_grade := 'same-session';
  ELSE
    -- 'distinct-deployment' is closed vocabulary but UNREACHABLE here today -- see s29's header LIMITS.
    NEW.discharge_grade := 'distinct-session';
  END IF;

  RETURN NEW;
END; $fn$;
-- this trigger's home table is review_detail (s17), unchanged here.
DROP TRIGGER IF EXISTS validate_independence ON :"schema".review_detail;
CREATE TRIGGER validate_independence BEFORE INSERT ON :"schema".review_detail
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_independence();

-- ============================================================================================
-- D-7 -- acts_for RETIRED (the column stays; non-NULL becomes unrepresentable; the supersessor
-- is named in the re-issued COMMENT). Whole-table-validates at ADD CONSTRAINT time: vacuous on
-- every world this delta can reach (birth chains only; the value was never once used in any
-- live history -- consultation-verified).
-- ============================================================================================
ALTER TABLE :"kern".principal DROP CONSTRAINT IF EXISTS principal_acts_for_retired;
ALTER TABLE :"kern".principal ADD CONSTRAINT principal_acts_for_retired CHECK (
    acts_for IS NULL);

COMMENT ON COLUMN :"kern".principal.acts_for IS
  'RETIRED BY SUPERSESSION since s41 (kernel/lineage/s41-principal-bindings-and-relations.sql
   D-7; the column itself stays -- s13/s14/s15 are frozen records, never retro-edited -- but a
   non-NULL value is unrepresentable by CHECK). The ONE home for delegation is now the
   principal_relation_asserted event with relation = ''acts-for'' (dated, attributed, typed,
   retractable by supersession -- everything this single-valued, undated, kind-less column
   could not represent, which is why it sat unused across 1800+ panel rows).';

-- ============================================================================================
-- D-5 -- THE FOUR DERIVED BINDING VIEWS (security_invoker, ledger_current-factored; all filter
-- active = true -- the withdrawal fix: a retraction chain's terminal row is unsuperseded but
-- inactive and must not read as a live binding).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".principal_relations
    WITH (security_invoker = true) AS
SELECT lc.principal_subject AS subject, lc.principal_relation AS relation,
       lc.principal_object AS object, lc.actor AS asserted_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_relation_asserted' AND lc.principal_binding_active;

COMMENT ON VIEW :"schema".principal_relations IS
  'In-force typed principal<->principal relations (unsuperseded, active). A RAW, ORDERED
   projection: same-natural-person facts appear in canonical (lower-id-subject) order only --
   a caller asking "is X the same natural person as anyone" checks subject = X OR object = X
   (the standing caller-side concern of any bidirectional fact table; no extra view machinery
   for one relation kind out of four -- basis D-2). row_id is the carrying event''s ledger id
   (the --supersedes target for `led principal unrelate`).
   kernel/lineage/s41-principal-bindings-and-relations.sql D-5.';

CREATE OR REPLACE VIEW :"schema".principal_role_bindings
    WITH (security_invoker = true) AS
SELECT lc.principal_subject AS subject, lc.principal_role_name AS role_name,
       lc.actor AS bound_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_role_bound' AND lc.principal_binding_active;

COMMENT ON VIEW :"schema".principal_role_bindings IS
  'In-force organizational role bindings (unsuperseded, active). Deliberately NOT named
   principal_roles: the singular kernel.principal_role (s40) is the structurally unrelated
   db-role<->principal standing binding, and a near-identical plural would invite conflation in
   queries and future migrations. RECORDABLE, NOT GATING in v1: no review path checks
   entitlement -- that enforcement is the named follow-on ratified amendment (basis §7 item 4).
   kernel/lineage/s41-principal-bindings-and-relations.sql D-5.';

CREATE OR REPLACE VIEW :"schema".principal_keys
    WITH (security_invoker = true) AS
SELECT lc.principal_subject AS subject, lc.principal_key_fingerprint AS fingerprint,
       lc.actor AS bound_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_key_bound' AND lc.principal_binding_active;

COMMENT ON VIEW :"schema".principal_keys IS
  'In-force key bindings (unsuperseded, active; human subjects only by D-3''s refusal). The
   empty-until-ceremony slot: key generation/signing stays deferred by standing ruling (D-4).
   kernel/lineage/s41-principal-bindings-and-relations.sql D-5.';

CREATE OR REPLACE VIEW :"schema".principal_competences
    WITH (security_invoker = true) AS
SELECT lc.principal_subject AS subject, lc.principal_competence_activity AS activity,
       lc.principal_competence_band AS band, lc.principal_competence_basis AS basis,
       lc.actor AS granted_by, lc.ts AS at, lc.id AS row_id
FROM   :"schema".ledger_current lc
WHERE  lc.kind = 'principal_competence_granted' AND lc.principal_binding_active;

COMMENT ON VIEW :"schema".principal_competences IS
  'In-force competence grants (unsuperseded, active) -- the BRIEF''s G13 record with a typed
   home: who is believed competent for what activity, at what band, on what basis, granted by
   whom, when. RECORDABLE, NOT GATING in v1 (nothing consults competence before accepting an
   act -- enforcement is the named follow-on amendment, basis §7 item 6); band/basis are
   free-text v1 BY RATIFIED PLACEHOLDER (§9(g), loud note in this delta''s header). A
   withdrawal (active = false superseding row) drops the grant from this view by construction;
   the terminal row stays in raw history. kernel/lineage/s41-principal-bindings-and-relations.sql.';

GRANT SELECT ON :"schema".principal_relations,
                :"schema".principal_role_bindings,
                :"schema".principal_keys,
                :"schema".principal_competences TO :"role";
