-- s68 TYPED ABSENCE DISPOSITIONS (design/FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md,
-- RATIFIED 2026-07-27, ledger rows 1541/1542 -- the maintainer's own verbatim ruling at s67's
-- merge-hold, "As for the NUL sentinel, that shoulde be fixed", answering the question s67's own
-- §2 AMENDMENT item 4 filed rather than silently absorbed). Third of the s65/s67/s68 family:
-- extends the s67 §2-AMENDMENT discipline (ADR-0012 P11: absence carries a typed reason,
-- ADR-0008's 2026-07-27 twin: NULL is not a vocabulary member) to the two remaining
-- implicit-sentinel columns that amendment's own item 4 named as a visible, disclosed gap --
-- refusal_attempted_kind (s65) and refusal_attempted_actor (s43/s49). Sonnet-built per the
-- standing delegation contract, from the ratified spec.
--
-- PREREQUISITE / THE HEAD-BODY RULE (s45's own standing instruction, carried here verbatim): at
-- this delta's authoring the lineage head is s67 (kernel/lineage/s67-refusal-digest-bound.sql,
-- this same directory's own listing, confirmed by the builder before authoring -- grep-verified,
-- no tracked kernel/lineage/sNN-*.sql file between s67 and this one exists). THE FUNCTIONS THIS
-- DELTA RE-ISSUES: kernel.journal_write_refusal's TRUE immediately-prior re-issue is s67 (kernel/
-- lineage/s67-refusal-digest-bound.sql Element 4 -- s67's own header names it the true prior of
-- ITS OWN re-issue, and grep across every tracked kernel/lineage/sNN-*.sql file confirms no delta
-- between s67 and this one re-issues it either). compute_row_hash's true immediately-prior
-- re-issue is likewise s67 (Element 2, 99 columns).
-- kernel.journal_write_refusal is `:"kern".`-namespaced, OUTSIDE gates/lineage_reissue_lineage.py's
-- own `:"schema".`-anchored citation-check universe (per that gate's own docstring; the SAME
-- disclosed exemption s65's/s67's own Element 4 re-issues already name) -- the citation/
-- prior-body-sha256 line below is carried as a matter of this codebase's house idiom, NOT
-- mechanically gate-enforced, named here rather than silently assumed to be checked. compute_row_
-- hash IS `:"schema".`-namespaced and inside that gate's own checked universe -- its citation +
-- prior-body-sha256 below ARE gate-verified.
--
-- WHY (spec §1's own words, verbatim mechanics read off s67's journaler body): the refusal
-- journal today collapses THREE different payload defects into one silent NULL on
-- refusal_attempted_kind (the payload's own `kind` key ABSENT, present but NOT A STRING, or
-- present but over the 256-byte bound -- a client bug omitting `kind` and an attacker shipping a
-- 10-KiB `kind` read as the SAME row today), and conflates TWO different resolution outcomes into
-- one silent state on refusal_attempted_actor (a populated value does not record whether it came
-- from the payload's own explicit claim or the session's standing-declaration fallback -- the
-- 2026-07-26 principal-stamps work already treats that distinction as load-bearing). ADR-0012's
-- P11 amendment (2026-07-27) names the rule this delta discharges: an absence with a reason any
-- reader could need is a representable, typed fact, never an inference from a comment; ADR-0008's
-- same-day twin: NULL is not a vocabulary member. Both columns' NULLs carry EXACTLY that
-- undocumented-multi-cause shape today (ADR-0012 §1234's own "two or more causes of absence"
-- test).
--
-- MECHANISM (spec §2, five items):
--   1. TWO NEW COLUMNS, both text, both kind-scoped to write_refused by the house TWO-WAY
--      kind-shape idiom (mandatory when kind='write_refused', forbidden elsewhere -- s44's
--      attest_verdict_kind_shape / s67's refusal_digest_disposition_kind_shape precedent,
--      "always known within the kind"):
--        - refusal_attempted_kind_disposition, closed vocabulary CHECK ('extracted', 'absent',
--          'not_a_string', 'over_bound') -- one member per witnessed branch of s67's own §1
--          reading, extend ONLY by a future delta.
--        - refusal_attempted_actor_disposition, closed vocabulary CHECK ('resolved_explicit',
--          'resolved_session_default', 'unresolvable').
--   2. COUPLING CHECKs, kind-guarded, the s44 attest_verdict idiom EXACTLY as the s67 fix round
--      transcribed it -- NOT a bare biconditional (the s67 build's own live psql test: a bare
--      `(a) = (b)` form is NULL-satisfied, never violated, on every non-write_refused row, since
--      SQL's three-valued logic makes a CHECK that evaluates to NULL pass):
--        - refusal_attempted_kind_disposition_coupling: `kind <> 'write_refused' OR
--          ((refusal_attempted_kind IS NULL) = (refusal_attempted_kind_disposition <>
--          'extracted'))` -- a FOUR-member vocabulary (unlike s67's two-member digest
--          disposition), so the coupled comparison is necessarily an inequality (`<> 'extracted'`)
--          rather than an equality against a single "the NULL-causing value" literal: THREE of
--          the four members (absent/not_a_string/over_bound) all mean "kind IS NULL", and only
--          the fourth ('extracted') means "kind IS NOT NULL" -- logically airtight because
--          refusal_attempted_kind_disposition is GUARANTEED non-NULL whenever kind='write_refused'
--          (item 1's own two-way kind-shape CHECK), the identical soundness argument s44's guard
--          and s67's coupling already rest on, re-verified for a three-vs-one split rather than
--          a two-member split.
--        - refusal_attempted_actor_disposition_coupling: `kind <> 'write_refused' OR
--          ((refusal_attempted_actor IS NULL) = (refusal_attempted_actor_disposition =
--          'unresolvable'))` -- a THREE-member vocabulary where exactly one member
--          ('unresolvable') means "actor IS NULL", so the coupled comparison is the s67-shape
--          equality against that one literal, airtight by the same guarantee.
--      The existing ONE-WAY kind-shape CHECKs on refusal_attempted_kind (s65) and
--      refusal_attempted_actor (s43) STAY, UNCHANGED (the s67 fix round's retained-sibling
--      precedent: the coupling CHECK's own kind-guard means it does not, and by the same
--      three-valued-logic argument structurally CANNOT alone, forbid either column appearing on
--      a non-write_refused row -- that job is each column's OWN one-way kind-shape CHECK, and
--      dropping it would reopen the off-kind hazard).
--   3. kernel.journal_write_refusal RE-ISSUED: each disposition is assigned IN THE SAME branch
--      that assigns (or NULLs) its column -- the kind extraction's single IF/ELSE splits into the
--      three witnessed failure arms plus the success arm; the actor resolution's existing
--      two-stage IF now records which stage won (or that neither did) in the same branch. One
--      writer, one home (amendment item 3's rule, the s67 precedent transcribed one delta over).
--      Every other line byte-identical to s67's own body, including s66's stamp branch (which
--      s67 did not touch either), the oracle bump, and the s67 digest/disposition block.
--   4. compute_row_hash RE-ISSUED to 101 columns under s42's law (99 + 2, appended in catalog
--      ordinal order, before the predecessor link); gates/hash_coverage_gate.py,
--      gates/kind_shape_manifest_gate.py (two new MANIFEST rows + two CROSS_COLUMN_COUPLING_
--      MANIFEST rows), gates/kernel_function_census.py bank, and the fixture family all extended
--      in this same commit.
--   5. PER-COLUMN, not consolidated (the amendment item 4 left this open, spec §2 item 5's own
--      reasoning): a single consolidated disposition would itself be a fuzzy vocabulary spanning
--      two value domains (ADR-0008's positive register -- refuse the inadequate shared bucket),
--      and the two columns' absence causes share no member (a "kind was over-bound" fact and an
--      "actor was unresolvable" fact are not interchangeable tokens of one vocabulary).
--
-- THE ASP TWIN: NO CHANGE to any derivation, the SAME finding s65's own header names and s67's
-- own header re-verifies rather than merely assumes: grepped across the whole engine/ tree for
-- every one of the existing refusal_* column names (including refusal_attempted_kind,
-- refusal_attempted_actor, refusal_digest_disposition) -- ZERO hits in engine/ledger_edb.py or
-- any engine/lp/*.lp file. No exporter emits ANY refusal column today, so none is widened to emit
-- either of this delta's two new ones. Coverage for THIS delta is its own fixtures (seen-red/
-- s68-typed-absence-dispositions/), never the differential.
--
-- FIXTURE FAMILY CHOICE (stated explicitly, per the build brief's own instruction): this delta
-- opens a NEW sibling fixture family, seen-red/s68-typed-absence-dispositions/, rather than
-- extending seen-red/s66-s67-journal-totality/ in place. Reasoning: that family's own RED/GREEN
-- pair is keyed to s66's forged-stamp branch and s67's digest bound, a self-contained two-delta
-- story already fully witnessed and closed; s68 dispositions a DIFFERENT pair of columns
-- (attempted-kind/attempted-actor, not the digest) with its own four-branch and three-branch
-- vocabularies, closer in shape to s65's own standalone family (seen-red/
-- s65-refusal-attempted-kind/) than to s66/s67's shared one. A sibling keeps each family's own
-- RED baseline legible against the ONE delta pair it actually re-witnesses, matching the
-- s65-vs-s66/s67 precedent (three deltas, two fixture families, split at the natural seam) rather
-- than growing one file into a four-delta omnibus.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a)): quantification universe, per the spec's own §4 -- the
-- nullable self-describing columns of the write_refused row shape as of s67:
-- refusal_attempted_kind (dispositioned HERE), refusal_attempted_actor (dispositioned HERE),
-- refusal_attempted_role (never NULL by construction -- session_user is always server-witnessed
-- -- no disposition, a vacuous disposition on a column that cannot be absent would fail the
-- named-consumer test, ledger row 1906), refusal_payload_digest (already dispositioned by s67),
-- refusal_sqlstate/refusal_message/refusal_surface (mandatory-populated by the journaler's own
-- INSERT, absence unrepresentable on the happy path -- their own two-way kind-shape CHECKs make
-- them structurally non-nullable within the kind). NOT COVERED, stated honestly (not silently
-- absorbed): every OTHER implicit-NULL in kernel and service code is ledger row 1542's own
-- backlogged audit, not this delta; live worlds keep the s67 shape until their next birth
-- (runs-are-linear, 2026-07-11).
-- TABLES/COLUMNS: TWO new columns, refusal_attempted_kind_disposition and
-- refusal_attempted_actor_disposition, each kind-scoped two-way (mandatory on write_refused,
-- forbidden elsewhere) plus its own closed-vocabulary value CHECK; refusal_attempted_kind's and
-- refusal_attempted_actor's own one-way kind-shape CHECKs are UNCHANGED; TWO new coupling CHECKs
-- tie each disposition to its own nullable sibling, table-level. KINDS: unchanged.
-- VIEWS: ledger_current/countersigned_in_force gain TWO columns, APPENDED (the s20/s23/s65/s67
-- lesson -- CREATE OR REPLACE VIEW forbids reordering existing columns). GATES: hash-coverage
-- (this delta's own compute_row_hash re-issue, 101 columns, gate-witnessed both polarities);
-- kind-shape manifest (CHAIN extended through s68, this same commit; MANIFEST gains two new
-- rows plus two CROSS_COLUMN_COUPLING_MANIFEST rows, ONE of which needed the classifier itself
-- extended -- see gates/kind_shape_manifest_gate.py's own header for the `<>`-comparator
-- generalization this delta's own kind-disposition coupling CHECK required); lineage-reissue-
-- lineage (citation of s67 for both re-issued functions stated above, gate-verified for
-- compute_row_hash, house-idiom-only for the `:"kern".`-namespaced journal_write_refusal exactly
-- as s65/s67 disclose); kernel-function-census (bank updated same commit -- kern:journal_write_
-- refusal's hash changes again, schema:compute_row_hash's hash changes again).
--
-- DENOMINATION: both dispositions are closed, kernel-authored, small (four and three members
-- respectively) vocabularies -- never free text, extended only by a future delta (the s43/s58/
-- s60/s67 "kind-structural closed CHECK" idiom, applied here to two more dispositions).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED FAIL-SAFE,
-- stated plainly (s43/s49/s65/s66/s67's own precedent for this same honesty requirement): this
-- delta re-issues an EXISTING function body via CREATE OR REPLACE (kernel.journal_write_refusal,
-- compute_row_hash) and adds two new mandatory-on-kind columns plus two cross-column coupling
-- CHECKs -- not a letter-2(a) "only adds" shape, even though the EFFECT is strictly fail-safe
-- (more refusals survive with a fuller, now EXPLICITLY TYPED record; nothing ACCEPTED before is
-- accepted differently; every refusal that journaled an attempted-kind/attempted-actor value
-- before still journals the SAME value, now additionally declaring a typed disposition). It
-- ships under the maintainer's OWN EXPLICIT RATIFICATION (design/
-- FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md, ledger rows 1541/1542, "As for the NUL sentinel,
-- that shoulde be fixed" -- verbatim), read per the 2026-07-11 vocabulary note, exactly the
-- posture s43/s49/s65/s66/s67 shipped under for the same reason.
--
-- LIMITS (pre-registered, matching s43/s49/s65/s66/s67's own disclosure convention):
--   - refusal_attempted_kind is NULL if and only if refusal_attempted_kind_disposition <>
--     'extracted' (table-CHECK-enforced); refusal_attempted_actor is NULL if and only if
--     refusal_attempted_actor_disposition = 'unresolvable' (table-CHECK-enforced). A
--     write_refused row's own absence-or-presence on either column is therefore always
--     EXPLICITLY DECLARED, never implicit. A non-write_refused row carries none of the four
--     columns (all NULL, kind-shape-enforced on all four).
--   - The four-way kind-disposition split does NOT recover which sub-case of "not extractable"
--     applied on any row journaled BEFORE this delta (a live world's own s65/s67-shape history is
--     untouched, runs-are-linear) -- only rows journaled from this delta's own birth chain onward
--     carry the finer distinction.
--   - This delta does not change the 256-byte length bound on refusal_attempted_kind (s65,
--     unchanged), the digest/disposition bound on refusal_payload_digest (s67, unchanged), or
--     what happens when the journal INSERT itself fails (s43's own named, disclosed loud-abort/
--     sequence-gap/server-log composition, untouched here).
--   - A deliberately LYING re-issue of journal_write_refusal could still write a disposition and
--     its sibling column inconsistently with the TRUTH of what happened -- the coupling CHECKs
--     enforce internal CONSISTENCY between each pair of columns, never that either one
--     TRUTHFULLY reflects the original payload/resolution; that trust boundary is the same one
--     every other kernel-computed column already rests on (stated, not hidden, the s67 precedent
--     restated one delta over).
--   - Every other named limit in s17/s23/s43/s49/s65/s66/s67's own headers is unchanged by this
--     delta and not re-stated in full here.
--
-- AUTOHARN.IDR: design/Autoharn.idr's own AS-OF banner is currently pinned at s65, LAGGING
-- s66/s67/s68 (its own header, lines 29-39) -- the model refresh named "in flight this same day"
-- has NOT merged by this build's own authoring time (grep-verified: no s66/s67 transcription
-- exists in that file beyond the pre-existing LAGGING note). The LAGGING suffix is therefore left
-- HONESTLY IN PLACE, per the spec's own §3 instruction, rather than extended or silently ignored;
-- this file is not touched by this delta.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s67): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway): apply the FULL s15..s67 chain (s65's own VALIDATE block +
--   s66 + s67), THEN -f s68-typed-absence-dispositions.sql (genesis seed per s26; register the
--   write-boundary principal before exercising any refusal path, or the journaler aborts loudly
--   by design, unchanged since s43).
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
-- ELEMENT 1 -- TWO NEW COLUMNS, the house TWO-WAY kind-shape idiom (mandatory when
-- kind='write_refused', forbidden elsewhere -- s44's attest_verdict_kind_shape / s67's
-- refusal_digest_disposition_kind_shape precedent), plus their own closed vocabulary CHECKs.
-- refusal_attempted_kind_kind_shape (s65, one-way) and refusal_attempted_actor_kind_shape (s43,
-- one-way) are UNCHANGED -- see this file's own header §2 item 2 for why they stay, matching
-- s44's/s67's own retained-sibling precedent.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_attempted_kind_disposition text;

COMMENT ON COLUMN :"schema".ledger.refusal_attempted_kind_disposition IS
  'WHY refusal_attempted_kind holds the value it does, on a write_refused row -- mandatory there
   (two-way kind-shape CHECK, s44''s attest_verdict idiom), forbidden elsewhere. Closed
   four-member vocabulary: ''extracted'' (a JSON string <=256 bytes was found at the payload''s
   `kind` key), ''absent'' (no `kind` key at all, or the payload was not a JSON object), ''not_a_
   string'' (the `kind` key held a non-string JSON value), ''over_bound'' (a string value exceeded
   256 bytes). Table-coupled to refusal_attempted_kind via
   refusal_attempted_kind_disposition_coupling: refusal_attempted_kind IS NULL if and only if this
   column is NOT ''extracted'' -- the reason for an absence is a representable, typed value here,
   never an inference from a comment (ADR-0012 P11, ADR-0008''s 2026-07-27 amendment; maintainer
   ruling, ledger rows 1541/1542). kernel/lineage/s68-typed-absence-dispositions.sql.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_kind_disposition_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_kind_disposition_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_attempted_kind_disposition IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_kind_disposition_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_kind_disposition_check CHECK (
    refusal_attempted_kind_disposition IS NULL
    OR refusal_attempted_kind_disposition IN ('extracted', 'absent', 'not_a_string', 'over_bound'));

ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS refusal_attempted_actor_disposition text;

COMMENT ON COLUMN :"schema".ledger.refusal_attempted_actor_disposition IS
  'WHY refusal_attempted_actor holds the value it does, on a write_refused row -- mandatory there
   (two-way kind-shape CHECK, s44''s attest_verdict idiom), forbidden elsewhere. Closed
   three-member vocabulary: ''resolved_explicit'' (the payload''s own `actor` key resolved to a
   registered principal id), ''resolved_session_default'' (the explicit claim did not resolve, but
   the session''s own standing-declaration default did), ''unresolvable'' (neither resolved).
   Table-coupled to refusal_attempted_actor via
   refusal_attempted_actor_disposition_coupling: refusal_attempted_actor IS NULL if and only if
   this column is ''unresolvable'' -- a populated attempted-actor now records WHOSE claim it is
   (the payload''s own, or the session''s standing default), a distinction the 2026-07-26
   principal-stamps work already treats as load-bearing (ADR-0012 P11, ADR-0008''s 2026-07-27
   amendment; maintainer ruling, ledger rows 1541/1542). kernel/lineage/
   s68-typed-absence-dispositions.sql.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_actor_disposition_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_actor_disposition_kind_shape CHECK (
    (kind = 'write_refused') = (refusal_attempted_actor_disposition IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_actor_disposition_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_actor_disposition_check CHECK (
    refusal_attempted_actor_disposition IS NULL
    OR refusal_attempted_actor_disposition IN
       ('resolved_explicit', 'resolved_session_default', 'unresolvable'));

-- refusal_attempted_kind_kind_shape / refusal_attempted_actor_kind_shape: UNCHANGED (one-way --
-- legitimately NULL within the licensed kind, forbidden elsewhere). Re-applied here (idempotent
-- DROP+ADD) only because CREATE CONSTRAINT has no IF NOT EXISTS-equivalent upsert and this file
-- must be self-contained/re-runnable, the s17/s19/s23/s67 idiom -- NOT a semantic change.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_kind_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_kind_kind_shape CHECK (
    refusal_attempted_kind IS NULL OR kind = 'write_refused');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_actor_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_actor_kind_shape CHECK (
    refusal_attempted_actor IS NULL OR kind = 'write_refused');

COMMENT ON COLUMN :"schema".ledger.refusal_attempted_kind IS
  'The refused write''s ATTEMPTED `kind` token, extracted from the refused payload before it is
   digested (s43''s R4 digest-only discipline over the payload AS A WHOLE is unchanged) --
   legitimately NULL when refusal_attempted_kind_disposition <> ''extracted'' (s68: kernel/
   lineage/s68-typed-absence-dispositions.sql), TABLE-COUPLED to that column via
   refusal_attempted_kind_disposition_coupling so the reason for a NULL kind token is always a
   typed, representable fact, never an implicit sentinel (maintainer ruling, ledger rows
   1541/1542; ADR-0012 P11). kernel/lineage/s65-refusal-attempted-kind.sql; kernel/lineage/
   s68-typed-absence-dispositions.sql.';

COMMENT ON COLUMN :"schema".ledger.refusal_attempted_actor IS
  'The ATTEMPTED principal when it resolved to a registered id -- legitimately NULL when
   refusal_attempted_actor_disposition = ''unresolvable'' (s68: kernel/lineage/
   s68-typed-absence-dispositions.sql), TABLE-COUPLED to that column via
   refusal_attempted_actor_disposition_coupling so the reason for a NULL attempted actor is always
   a typed, representable fact, never an implicit sentinel (maintainer ruling, ledger rows
   1541/1542; ADR-0012 P11). FK to kernel.principal. kernel/lineage/
   s43-typed-verdict-write-boundary.sql; kernel/lineage/s68-typed-absence-dispositions.sql.';

-- ============================================================================================
-- ELEMENT 1b -- THE TWO COUPLING CHECKs (spec §2 item 2; s44's attest_expected_verdict_coupling
-- idiom, kind-guarded so the fragile `=`-of-a-possibly-NULL-column comparison only ever runs on a
-- row where the disposition column is GUARANTEED non-NULL by Element 1's own two-way kind-shape
-- CHECK -- see this file's own header for the live psql test s67's build ran that falsifies the
-- bare, unguarded form).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_kind_disposition_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_kind_disposition_coupling CHECK (
    kind <> 'write_refused'
    OR (refusal_attempted_kind IS NULL) = (refusal_attempted_kind_disposition <> 'extracted'));

COMMENT ON CONSTRAINT refusal_attempted_kind_disposition_coupling ON :"schema".ledger IS
  'design/FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md §2 item 2 (maintainer ruling, ledger rows
   1541/1542): a write_refused row''s attempted-kind token is NULL if and only if its own
   disposition is NOT ''extracted'' -- three of the four disposition members (absent/not_a_string/
   over_bound) all mean the token is NULL, so the coupled comparison is an inequality, not an
   equality against one literal (contrast refusal_payload_digest_disposition_coupling, a two-
   member vocabulary where equality suffices). kernel/lineage/
   s68-typed-absence-dispositions.sql.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS refusal_attempted_actor_disposition_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT refusal_attempted_actor_disposition_coupling CHECK (
    kind <> 'write_refused'
    OR (refusal_attempted_actor IS NULL) = (refusal_attempted_actor_disposition = 'unresolvable'));

COMMENT ON CONSTRAINT refusal_attempted_actor_disposition_coupling ON :"schema".ledger IS
  'design/FABLE-S68-TYPED-ABSENCE-DISPOSITIONS-SPEC.md §2 item 2 (maintainer ruling, ledger rows
   1541/1542): a write_refused row''s attempted-actor is NULL if and only if its own disposition
   declares ''unresolvable'' -- a populated attempted actor must declare EITHER resolved_explicit
   OR resolved_session_default (never unresolvable), an absent one must declare unresolvable.
   kernel/lineage/s68-typed-absence-dispositions.sql.';

-- ============================================================================================
-- ELEMENT 2 -- s42'S LAW SELF-APPLIED: compute_row_hash RE-ISSUED TO 101 COLUMNS (the two new
-- columns appended in catalog ordinal order, before the predecessor link; base body = s67's own
-- text, byte-identical above this delta's two appended lines).
-- prior-body-sha256: 014ee6e6a86f20df8a34bd940efb40f01f1c2475bb03c15ec958b887a5eed115 (s67-refusal-digest-bound.sql)
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
      -- s68: the two new columns, appended last before the predecessor link.
      hashfield(r.refusal_attempted_kind_disposition),
      hashfield(r.refusal_attempted_actor_disposition),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 3 -- THE TWO COLUMN-COMPLETE VIEWS, +2 APPENDED (the s20/s23/s65/s67 lesson).
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
       l.refusal_attempted_actor_disposition
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
       l.refusal_attempted_actor_disposition
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 4 -- kernel.journal_write_refusal RE-ISSUED: the s67 body (kernel/lineage/
-- s67-refusal-digest-bound.sql Element 4 -- the TRUE immediately-prior re-issue), BYTE-IDENTICAL
-- above and below the two re-shaped blocks, with the kind extraction's single IF/ELSE split into
-- its four witnessed branches (recording refusal_attempted_kind_disposition alongside
-- refusal_attempted_kind in the same branch) and the actor resolution's existing two-stage IF now
-- also recording refusal_attempted_actor_disposition in the same branch that resolves (or fails
-- to resolve) v_attempted. No other line of this function changes: the oracle bump stays first,
-- the write-boundary principal lookup and its own loud abort stay exactly as s43/s49/s65/s67 left
-- them, the s67 digest/disposition block is untouched, and the journal INSERT's own
-- loud-abort-on-failure semantics are untouched.
-- prior-body-sha256: d0b01e0d3edbb0de5c482aa816cca1ee8c71b56aa51e7448c66a23180e108d43 (s67-refusal-digest-bound.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".journal_write_refusal(
    p_surface text, p_payload jsonb, p_sqlstate text, p_message text)
    RETURNS bigint LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_wb bigint;
  v_attempted bigint;
  v_attempted_actor_disposition text;
  v_attempted_kind text;
  v_attempted_kind_disposition text;
  v_kind_typeof text;
  v_digest text;
  v_disposition text;
  v_id bigint;
BEGIN
  -- the oracle bump, BEFORE the journal INSERT (non-transactional, survives everything --
  -- s43 Element 5): if the INSERT below then fails, the sequence shows a counted gap the
  -- verify-chain reconciliation names. UNCHANGED by s68.
  PERFORM nextval('refusal_seq');
  SELECT id INTO v_wb FROM principal WHERE name = 'write-boundary';
  IF v_wb IS NULL THEN
    RAISE EXCEPTION 'write boundary: the ''write-boundary'' tool principal is not registered in this world -- refusal recording has no authoring identity (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 6; bootstrap/new-project.sh''s birth sequence registers it). The original refusal (SQLSTATE %) was: %', p_sqlstate, p_message;
  END IF;
  -- the ATTEMPTED identity: the explicit payload actor when it resolves to a registered id,
  -- else the session's own standing-declaration default, else neither -- the role below is
  -- still always known. s68 (kernel/lineage/s68-typed-absence-dispositions.sql): each branch now
  -- ALSO records WHICH of the two stages produced the value, or that neither did -- one writer,
  -- one home, the same branch that resolves v_attempted also sets its disposition.
  --
  -- s49 GUARD (kernel/lineage/s49-journaler-overflow-guard.sql): the regex `^[0-9]+$` admits
  -- arbitrary-length digit strings, but bigint's own range does not -- an over-bigint numeral
  -- previously raised 22003 HERE; the cast is total (UNCHANGED by s65/s67/s68).
  IF (p_payload ? 'actor') AND (p_payload->>'actor') ~ '^[0-9]+$' THEN
    BEGIN
      SELECT id INTO v_attempted FROM principal WHERE id = (p_payload->>'actor')::bigint;
    EXCEPTION WHEN numeric_value_out_of_range THEN
      v_attempted := NULL;
    END;
  END IF;
  IF v_attempted IS NOT NULL THEN
    v_attempted_actor_disposition := 'resolved_explicit';
  ELSE
    SELECT principal_id INTO v_attempted FROM principal_role WHERE db_role = session_user;
    IF v_attempted IS NOT NULL THEN
      v_attempted_actor_disposition := 'resolved_session_default';
    ELSE
      v_attempted_actor_disposition := 'unresolvable';
    END IF;
  END IF;
  -- s65 (kernel/lineage/s65-refusal-attempted-kind.sql): the ATTEMPTED kind, extracted from the
  -- refused payload -- TOTAL, NULL when not extractable. s68 (kernel/lineage/
  -- s68-typed-absence-dispositions.sql): the single IF/ELSE that decided NULL-or-not now splits
  -- into its four witnessed branches, one writer one home, so the disposition is set in the SAME
  -- branch that sets (or NULLs) the token. jsonb_typeof(p_payload->'kind') is SQL NULL exactly
  -- when the `kind` key is absent OR p_payload is not a JSON object at all (Postgres's own
  -- documented `->` semantics: it returns NULL rather than raising on either shape) -- that SQL
  -- NULL is the 'absent' branch's own total, no-exception-handler-needed signal, s65's own
  -- MECHANISM section reasoning carried one delta over.
  v_kind_typeof := jsonb_typeof(p_payload->'kind');
  IF v_kind_typeof IS NULL THEN
    v_attempted_kind := NULL;
    v_attempted_kind_disposition := 'absent';
  ELSIF v_kind_typeof <> 'string' THEN
    v_attempted_kind := NULL;
    v_attempted_kind_disposition := 'not_a_string';
  ELSIF octet_length(p_payload->>'kind') > 256 THEN
    v_attempted_kind := NULL;
    v_attempted_kind_disposition := 'over_bound';
  ELSE
    v_attempted_kind := p_payload->>'kind';
    v_attempted_kind_disposition := 'extracted';
  END IF;
  -- s67 BOUND (kernel/lineage/s67-refusal-digest-bound.sql): UNCHANGED by s68.
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
                      refusal_attempted_kind, refusal_digest_disposition,
                      refusal_attempted_kind_disposition, refusal_attempted_actor_disposition)
  VALUES ('write_refused',
          format('write refused at surface %s (SQLSTATE %s)', p_surface, p_sqlstate),
          v_wb,
          p_sqlstate, p_message, p_surface,
          v_digest,
          v_attempted, session_user,
          v_attempted_kind, v_disposition,
          v_attempted_kind_disposition, v_attempted_actor_disposition)
  RETURNING id INTO v_id;
  RETURN v_id;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) FROM PUBLIC;

COMMENT ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) IS
  'The ONE home of "a refusal becomes a committed write_refused row" (s43 Element 4), called
   only from inside the SECURITY DEFINER boundary functions (no role holds EXECUTE). Bumps the
   refusal_seq oracle FIRST (non-transactional), then journals: actor = the write-boundary tool
   principal; the attempted identity in refusal_attempted_* plus WHICH stage produced it in
   refusal_attempted_actor_disposition (s49: the actor cast is TOTAL; s68: kernel/lineage/
   s68-typed-absence-dispositions.sql); the attempted kind token in refusal_attempted_kind plus
   WHY it is absent when it is in refusal_attempted_kind_disposition (s65: TOTAL, 256-byte bound;
   s68); the payload as a SHA-256 digest, plus its own typed refusal_digest_disposition (s67).
   If the journal INSERT itself fails the exception propagates -- a loud abort, a counted
   sequence gap, the server log as residual coverage (fail-safe on both legs, unchanged by
   s49/s65/s67/s68). kernel/lineage/s43-typed-verdict-write-boundary.sql; kernel/lineage/
   s49-journaler-overflow-guard.sql; kernel/lineage/s65-refusal-attempted-kind.sql; kernel/
   lineage/s67-refusal-digest-bound.sql; kernel/lineage/s68-typed-absence-dispositions.sql.';
-- ============================================================================================
