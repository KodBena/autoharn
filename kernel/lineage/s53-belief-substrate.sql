-- s53 BELIEF SUBSTRATE -- KIND, COLUMNS, CHECKS, REFUSAL TRIGGERS (design/
-- FABLE-BELIEF-SUBSTRATE-SPEC.md v2 Delta B1, §3.1/§3.2 -- ratified build basis, ledger rows
-- 1914/1919). Sonnet-executed per the standing delegation contract, from this Fable-authored,
-- maintainer-ratified spec. This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to
-- any live/existing world is the maintainer's act at a FUTURE world's birth (runs-are-strictly-
-- linear, 2026-07-11) -- never taken here.
--
-- PREREQUISITE: s52 (kernel/lineage/s52-artifact-witness-check.sql), and transitively the full
-- chain through it -- a HARD dependency: this delta's validate_belief_evidence trigger reads
-- kernel.artifact (s51) for artifact: witness/universe tokens, and re-issues
-- compute_row_hash/ledger_current/countersigned_in_force from their s44 HEAD TEXT (the most
-- recent re-issuer of all three -- verified: s45/s46/s47/s48/s49/s50/s51/s52 each confirmed in
-- their own headers/HISTORY they do NOT touch these three objects). THE HEAD-BODY RULE (the
-- s44/s45 discipline, carried here verbatim): at this delta's authoring the repository lineage
-- head is s52 -- confirmed by directory listing before authoring. The base bodies this file
-- re-issues below are quoted, verified, against the s44 head text (compute_row_hash/
-- ledger_current/countersigned_in_force, 65 columns) and against s45's HEAD TEXT for
-- validate_supersession_target (the most recent re-issuer of that function), unedited by any
-- delta from s46 through s52.
--
-- WHY (operator-side prose; NOT subject-visible): the spec §1(a)'s class, in its most general
-- form: *an assertion-act whose quantifier, evidence obligation, basis, and holder-relation are
-- unrepresentable, so every overclaim built on it is representable.* Seven witnessed failures
-- (the spec's consult, row 1887's two-bias rule among them) share this shape: a confident belief
-- operated on this project's record without ever being ON the record as a belief. v1 (already
-- shipped, ledger rows 1914/1919) gave the substrate a statement-prefix convention, parse-time
-- only. This delta is v2's kernel half: the SAME nine-column, closed-vocabulary shape, enforced
-- at WRITE time -- a malformed belief is unrepresentable at construction, not merely refused
-- when an engine happens to read it.
--
-- ELEMENT 1 -- THE KIND (spec §3.1): `belief`, twenty-sixth member of the closed vocabulary
-- (after s44's `model_identity_attested`, the twenty-fifth). Kind CHECK re-issued DROP+ADD (its
-- ONE home, the s41->s44 idiom continued). The holder is the existing `actor` + stamp -- no new
-- holder column (one home per fact, spec's own words). The proposition lives in `statement` --
-- no second text column. `confidence` (pre-existing since s15) becomes the holder's own
-- three-valued self-grade on belief rows: hash-covered, deliberately UNREAD by the crediting
-- rules (the s44 attestation-grade precedent, spec §3.1's own words).
--
-- ELEMENT 2 -- NINE NEW COLUMNS (spec §3.1 table, transcribed verbatim; prefix `belief_`, the
-- house `attest_*`/`refusal_*` pattern): all nullable, no column DEFAULT (the s30 lesson), each
-- split into a kind-shape CHECK (one concern per CHECK, the s40 idiom) plus separate value/
-- coupling CHECKs where the column also carries a vocabulary or cross-column constraint.
-- belief_polarity/belief_basis: two-way (mandatory on belief, forbidden elsewhere). The other
-- seven (belief_universe, belief_witness, belief_source, belief_premises, belief_subject,
-- belief_contests, belief_concurs): one-way kind guards (belief-only; presence WITHIN the kind
-- is governed by the separate coupling CHECKs below, spelled off belief_polarity/belief_basis
-- VALUES rather than off `kind` directly -- see ELEMENT 3's own note on why those couplings
-- carry no `kind` literal and so need no CROSS_COLUMN_COUPLING_MANIFEST entry in
-- gates/kind_shape_manifest_gate.py, verified live, §7.2 below).
--
-- ELEMENT 3 -- COUPLING CHECKS (spec §3.1's CHECK-spellings block, transcribed): the polarity/
-- basis obligation truth table -- universal requires a non-empty universe and forbids witness;
-- existential forbids universe and requires a non-empty witness when basis=observed; testimony
-- requires source (forbidden otherwise); derived requires a non-empty premises array (forbidden
-- otherwise). Each coupling is spelled `belief_polarity IS DISTINCT FROM '<v>' OR ...` /
-- `belief_basis IS DISTINCT FROM '<v>' OR ...` -- NEVER `kind = 'belief' AND ...` -- because
-- belief_polarity/belief_basis are THEMSELVES already kind-scoped to exactly 'belief' by their
-- own two-way CHECKs (ELEMENT 2): on any non-belief row both are NULL, and `NULL IS DISTINCT
-- FROM '<v>'` is TRUE, so every coupling clause passes VACUOUSLY on every non-belief row without
-- ever testing `kind` itself -- one indirection cheaper than re-deriving the kind test, and
-- (verified live, §7.2) invisible to gates/kind_shape_manifest_gate.py's kind-shape classifier
-- (which only inspects CHECKs that literally mention `kind`), so no CROSS_COLUMN_COUPLING_
-- MANIFEST entry or classifier extension is owed by this delta.
--
-- ELEMENT 4 -- REFUSAL TRIGGERS (spec §3.2): TWO new single-purpose BEFORE INSERT triggers
-- beside the existing validate_* family (the s43/s48/s52 idiom -- never folded into
-- validate_work_item's dispatcher, ADR-0012 P1: orthogonal concerns, no shared state):
--   validate_belief_evidence -- token existence on belief_witness and belief_universe: every
--     `row:<digits>` token must name an existing ledger row (the s48 extraction/verification
--     mechanism, reused verbatim); every `artifact:<64-hex>` token must resolve in the s51/s52
--     artifact store (the s52 shape-then-existence mechanism, reused verbatim). Fires only when
--     the relevant column is non-NULL (which, by ELEMENT 2's kind-shape CHECKs, means kind =
--     'belief' -- no separate kind test needed, mirroring how ELEMENT 3's couplings avoid one).
--   validate_belief_edges -- cross-row semantics the CHECKs cannot see: (1) every
--     belief_premises element names an existing ledger row (existence only -- in-force-ness is
--     a READ-time judgment, §3.4, because history legitimately grounds beliefs); (2)
--     belief_contests target must exist, be kind='belief', be unsuperseded at write time, and
--     carry a DIFFERENT resolved actor than the new row; (3) belief_concurs target: the same
--     three tests.
--
-- SPEC AMBIGUITY, RESOLVED AND REPORTED (never silently absorbed -- CLAUDE.md engineering-
-- responsibility corollary + this build's own instruction): spec §3.2 item 4 ("supersession
-- discipline on belief targets... enforced rather than assumed: a row whose supersedes names a
-- belief row is refused unless (i) it is itself kind='belief' AND (ii) its resolved actor equals
-- the target's actor") is PROSE-GROUPED under the "validate_belief_edges" enumeration in the
-- spec text, but its actual semantics -- refusing a row of ANY kind whose `supersedes` names a
-- belief -- CANNOT live inside validate_belief_edges as written: that trigger's items 1-3 only
-- fire meaningfully when NEW.kind='belief' (they read belief_premises/contests/concurs, which
-- are NULL on every other kind by ELEMENT 2's own CHECKs), so a non-belief row superseding a
-- belief would never reach a belief_edges check gated that way, and the exact revision-vs-
-- contest confusion item 4 exists to foreclose would slip through unrefused. ADR-0012 P1 ("one
-- home per concern") and the s43->s45 precedent (validate_supersession_target is ALREADY the
-- one home for "which kind may supersede what target kind" rules, re-issued rather than
-- duplicated when s45 added its own three-kind discipline) both point the same direction: item 4
-- is built here as a THIRD re-issue of validate_supersession_target (ELEMENT 5 below), verified
-- against s45's own HEAD TEXT (unedited by s46 through s52), never as a third branch bolted
-- into validate_belief_edges. This is ADR-0013's "the real fix, to its ratified end" read
-- literally: the spec's own §3.2 preamble already invokes "the s45 same-kind identity-continuity
-- pattern" as item 4's own grounds, which IS validate_supersession_target's pattern, not
-- validate_belief_edges's -- the file-organizational grouping in the spec text is read as
-- descriptive labeling, not a mechanism directive, per ADR-0000 Rule 2(a)'s own instruction that
-- the type is chosen to foreclose the class, not to match a prose heading.
--
-- ELEMENT 5 -- validate_supersession_target RE-ISSUED (s45's own precedent, one more branch):
-- the s43 write_refused refusal and s45's three-kind standing-lifecycle block stay BYTE-
-- IDENTICAL and first (verified against s45's own head text); a new belief block follows,
-- widening the target row's SELECT by one more column (l.actor, alongside s45's three) and
-- refusing a row whose `supersedes` names an in-force `belief` row unless the superseding row is
-- itself kind='belief' with the SAME resolved actor -- exactly spec §3.2 item 4 / §3.3
-- "Revision = supersession by the holder."
--
-- ELEMENT 6 -- SAME-COMMIT SET (the s44/s45 "same-commit set" idiom, executed): (a)
-- ledger_current/countersigned_in_force RE-ISSUED with the nine columns appended at the END (the
-- s20 lesson; base = s44's exact 65-column list, verified unedited by s45-s52); (b)
-- compute_row_hash RE-ISSUED to 74 columns (the nine appended in catalog ordinal order, s42's
-- law self-applied, base = s44's exact body); (c) the kind CHECK re-issued widened (ELEMENT 1);
-- (d) gates/kind_shape_manifest_gate.py CHAIN += s50/s51/s52/s53 plus nine new MANIFEST rows
-- (this same commit); (e) gates/ledger_reader_allowlist.py CHAIN += s50/s51/s52/s53 (the two
-- new triggers and the re-issued validate_supersession_target read raw `ledger` by row-addressed
-- id -- the SAME history-typed posture validate_review_witness_existence/
-- validate_artifact_witness_existence already hold, ALLOWLIST entries added); (f)
-- gates/hash_coverage_gate.py needs NO manual edit -- its chain_files() derives the full chain
-- mechanically from kernel/lineage/*.sql filenames (verified, this file's own header); (g) this
-- file's .detect.sql sibling, behavior-fingerprinted per the migrate-detect-drift ruling
-- (2026-07-16); (h) the engine leg -- engine/belief_edb.py's export_belief() and
-- engine/belief_floor.py's belief_floor_atoms() are BOTH widened with a typed-arm branch,
-- capability-probed on belief_polarity's presence (the s44 has_typed=t.has_col("attest_row_id")
-- precedent, transposed) -- both arms feed the SAME fact families (belief/1, belief_polarity/2,
-- ...), so ledger_belief.lp and its SQL twin need NO edit of their own to recognize a world
-- carrying this delta (the s44 "no edit needed" precedent, verified live, §7.2 below);
-- bootstrap/new-project.sh's LINEAGE_CHAIN += s53/s54/s55 (this same commit, the s40-s44
-- same-commit-wiring precedent, chosen over s48/s52's deferred-wiring posture because this
-- build's own task explicitly commissions scratch witnessing via `new-project.sh --new-world`,
-- which can only carry deltas already IN LINEAGE_CHAIN).
--
-- WHAT THIS DELTA DOES NOT TOUCH, stated as loudly as what it does (mirroring s44/s45's own
-- discipline): ZERO edits to validate_review, validate_belief_evidence's sibling triggers, s41's
-- validate_independence, or kernel.principal_role; ZERO CLI (led.tmpl) edits -- writing a belief
-- row is reachable today only through the generic kernel.ledger_write(jsonb) boundary (s43),
-- exactly as s44 shipped model_identity_attested's kernel shape with no verb, named in LIMITS
-- below, not silently left; ZERO changes to the v1 statement-prefix convention (engine/
-- belief_edb.py's v1 parser, engine/belief_floor.py's v1 regex) -- both arms coexist, exactly
-- the s44 attest_row/mismatch_attest dual-arm precedent this delta's engine leg mirrors.
--
-- HISTORY: safe -- per-mechanism grounds (mirroring s44's own HISTORY paragraph):
--   * the kind CHECK is re-issued WIDER (additive: every pre-existing kind's legality is
--     unchanged; `belief` is disjoint and, being BORN in this delta on any birth chain that
--     carries it, no pre-existing row of it can exist to violate the widened CHECK -- vacuous
--     ADD CONSTRAINT validation, the s40/s41/s43/s44 precedent).
--   * all nine new columns' kind-shape CHECKs, and the five coupling CHECKs, validate vacuously
--     for the same reason (the kind is born here; ELEMENT 3's coupling clauses are additionally
--     vacuous on every OTHER pre-existing row because belief_polarity/belief_basis are NULL
--     there, per the argument in ELEMENT 3's own comment above).
--   * ledger_current/countersigned_in_force gain nine columns APPENDED at the end -- no existing
--     consumer's column-position assumption breaks (the s20 lesson, applied again).
--   * compute_row_hash is re-issued to 74 columns -- s42's law, self-applied; every pre-existing
--     row's hash is UNAFFECTED because this file, like every kernel-lineage file, is never
--     applied to a world with existing rows (runs-are-linear; "before" exists only on scratch).
--   * validate_belief_evidence/validate_belief_edges are WHOLLY NEW triggers -- no pre-existing
--     INSERT path is touched; a row that was legal before this delta (any non-belief kind) stays
--     legal, since both triggers' bodies are no-ops when the relevant belief_* column is NULL.
--   * validate_supersession_target's re-issue ADDS one more IF block, after s45's three-kind
--     block, gated on the target being kind='belief' -- a kind that is BORN in this delta, so no
--     pre-existing supersession chain on any prior world can name a belief target; every
--     pre-s53 refusal/acceptance the function already performs (write_refused unretractability,
--     the three standing-lifecycle rules) is byte-identical and unreachable-changed.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form; this delta's own slice -- the spec's
-- own §6 is the FAMILY-INTENDED closure, reproduced faithfully in slice here):
--   - INVARIANT: in an s53 world, a belief row is representable only in the typed shape -- a
--     typed quantifier polarity with that polarity's evidence obligation (universal requires an
--     enumerated, token-existence-checked universe; observed existential requires a token-
--     existence-checked witness), a typed basis with that basis's edge obligation (testimony
--     requires an existing source; derived requires a non-empty, existence-checked premises
--     array), revisable only by its own holder (validate_supersession_target's new belief
--     block), and contestable/concurrable only via edges naming an existing, unsuperseded,
--     different-actor belief row (validate_belief_edges) -- a malformed belief is unrepresentable
--     at construction, and its attempt is itself a recorded refusal event (s43's write_refused
--     machinery, inherited for free).
--   - QUANTIFICATION UNIVERSE: kinds carrying each new column: exactly `belief` (two-way for
--     polarity/basis; one-way for the other seven, coupling CHECKs spelled off polarity/basis
--     values per ELEMENT 3); views: the two projection homes re-issued +9, non-members
--     re-verified per the s40-s52 lists (none does general column passthrough); triggers: TWO
--     new (validate_belief_evidence, validate_belief_edges), ONE re-issued
--     (validate_supersession_target, +1 belief branch); hash: the nine columns inside the v2
--     serialization, gate-enforced; CLI-side residue: writing a belief row is reachable only via
--     kernel.ledger_write(jsonb) directly (no `led belief` verb this delta -- named in LIMITS,
--     not silent, mirroring s44's own posture).
--   - DENOMINATION: polarity/basis in their closed two/four-member vocabularies; universe/
--     witness/premises/source/subject/contests/concurs in the existing row:/artifact: token
--     currency (s48/s51/s52's own); "exists" denominated in ledger.id / kernel.artifact.hash
--     membership, never a proxy count. No bound is a bare round literal.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): the spec's own §3/§11 state
-- this family is WITHIN the class-ratified fail-safe SHAPE (adds a kind, refusals, and columns;
-- relaxes nothing existing) but is NOT claimed under that class -- it mints vocabulary the whole
-- project will reason in, exactly what the class-ratification carve-out reserves for the
-- maintainer. Ships under design/FABLE-BELIEF-SUBSTRATE-SPEC.md's own ratification (ledger rows
-- 1914/1919) plus this build's own commission.
--
-- LIMITS (pre-registered, per the spec §9/§16-transposed discipline, mirroring s44's own):
--   - This file ships the KERNEL SHAPE only. NO CLI verb writes this kind -- `led belief` is
--     UNBUILT this delta (a substantial CLI/argument-parsing addition on top of an already large
--     kernel delta, scoped out under this build's own time/quality tradeoff, named here rather
--     than silently left); the ONLY live write path is kernel.ledger_write(jsonb) directly
--     (payload keys are ledger column names -- belief_* columns pass through unchanged, no
--     boundary-function edit needed, verified against s43's own generic-key-validation logic).
--   - The two CLI-side cross-row properties s44's own precedent already discloses a sibling of
--     (here: nothing analogous -- contest/concurs SoD and existence ARE trigger-enforced by
--     validate_belief_edges, stronger than v1's parse-time-only equivalent) are NOT a gap this
--     delta carries; named for completeness, not because a gap exists.
--   - Universe-rightness, paraphrase-strengthening, and concurrence honesty stay REVIEW-ONLY
--     (spec §3.2's own "Honestly review-only, declared now" paragraph) -- no mechanism reads
--     meaning.
--   - No cryptography of any kind is added, generated, or required by this delta (the standing
--     crypto deferral, honored).
--   - Reaches reality only at a FUTURE world's birth; this builder's act does NOT itself apply
--     it to any existing world (runs-are-strictly-linear).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s52):
--   VALIDATE (reachable throwaway): apply the full chain through s52 (see s52's own VALIDATE
--   list), then -f s53-belief-substrate.sql.
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN, wired in THIS SAME commit (see
--   ELEMENT 6 above for why same-commit wiring is chosen here). Authored and scratch-witnessed
--   on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; ADD COLUMN IF NOT EXISTS;
-- CREATE OR REPLACE FUNCTION/VIEW; DROP+CREATE TRIGGER).
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
-- ELEMENT 1 -- KIND VOCABULARY WIDENED (twenty-sixth member).
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
     'model_identity_attested',
     'belief'));

COMMENT ON CONSTRAINT ledger_kind_check ON :"schema".ledger IS
  'kernel/lineage/s53-belief-substrate.sql: widens s44''s twenty-five-member vocabulary by
   belief -- the typed v2 form of design/FABLE-BELIEF-SUBSTRATE-SPEC.md''s assertion-act kind
   (ledger rows 1914/1919). Supersession-retractable ONLY by its own holder (ELEMENT 5 below) --
   a belief is a defeasible, revisable claim, deliberately NOT given write_refused''s R6
   unretractability.';

-- ============================================================================================
-- ELEMENT 2 -- THE NINE KIND-SCOPED COLUMNS.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_polarity text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_basis text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_universe text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_witness text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_source bigint
    REFERENCES :"schema".ledger(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_premises bigint[];
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_subject bigint
    REFERENCES :"schema".ledger(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_contests bigint
    REFERENCES :"schema".ledger(id);
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS belief_concurs bigint
    REFERENCES :"schema".ledger(id);

COMMENT ON COLUMN :"schema".ledger.belief_polarity IS
  'universal | existential (spec §3.1). Mandatory on belief, forbidden elsewhere (two-way).
   kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_basis IS
  'observed | derived | testimony | assumed (spec §3.1). Mandatory on belief, forbidden
   elsewhere (two-way). kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_universe IS
  'The enumerated quantification universe -- semicolon-separated surfaces/axes/clauses;
   row:/artifact: tokens inside it are existence-checked (validate_belief_evidence). Present
   non-empty iff belief_polarity=''universal'' (belief_universe_coupling); belief-only
   (belief_universe_kind_shape). kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_witness IS
  'Comma-separated row:/artifact: tokens, existence-checked (validate_belief_evidence).
   Forbidden when belief_polarity=''universal''; mandatory non-empty when polarity=existential
   AND basis=observed; optional on other existential rows (the coupling CHECKs).
   kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_source IS
  'The source record a testimony-basis belief relays -- self-referencing FK. Present iff
   belief_basis=''testimony'' (belief_source_coupling); belief-only.
   kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_premises IS
  'The cited premises of a derived-basis belief -- bigint[], NOT the pre-existing `enacts`
   column (a different fact, ADR-0008''s false-cognate lesson, row 1893). Present with
   cardinality >= 1 iff belief_basis=''derived'' (belief_premises_coupling); element existence
   checked by validate_belief_edges (arrays carry no FK). belief-only.
   kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_subject IS
  'The row this belief''s proposition is about, where there is one -- self-referencing FK,
   optional, belief-only (the `regards`/attest_row_id idiom).
   kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_contests IS
  'The challenged belief row -- self-referencing FK, optional, belief-only; cross-row semantics
   (must exist, be kind=belief, unsuperseded, different actor) enforced by
   validate_belief_edges. kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON COLUMN :"schema".ledger.belief_concurs IS
  'The concurred-with belief row -- self-referencing FK, optional, belief-only; same cross-row
   semantics as belief_contests, enforced by validate_belief_edges.
   kernel/lineage/s53-belief-substrate.sql.';

-- kind-shape CHECKs (one concern per CHECK -- the s40 idiom; two-way for polarity/basis,
-- one-way for the other seven -- belief-only, presence WITHIN the kind governed separately):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_polarity_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_polarity_kind_shape CHECK (
    (kind = 'belief') = (belief_polarity IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_basis_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_basis_kind_shape CHECK (
    (kind = 'belief') = (belief_basis IS NOT NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_universe_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_universe_kind_shape CHECK (
    belief_universe IS NULL OR kind = 'belief');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_witness_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_witness_kind_shape CHECK (
    belief_witness IS NULL OR kind = 'belief');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_source_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_source_kind_shape CHECK (
    belief_source IS NULL OR kind = 'belief');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_premises_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_premises_kind_shape CHECK (
    belief_premises IS NULL OR kind = 'belief');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_subject_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_subject_kind_shape CHECK (
    belief_subject IS NULL OR kind = 'belief');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_contests_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_contests_kind_shape CHECK (
    belief_contests IS NULL OR kind = 'belief');
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_concurs_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_concurs_kind_shape CHECK (
    belief_concurs IS NULL OR kind = 'belief');

-- value CHECKs (no kind test -- out of the kind-shape manifest's scope, the attest_grade_check
-- precedent):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_polarity_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_polarity_check CHECK (
    belief_polarity IS NULL OR belief_polarity IN ('universal','existential'));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_basis_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_basis_check CHECK (
    belief_basis IS NULL OR belief_basis IN ('observed','derived','testimony','assumed'));

-- polarity/basis coupling CHECKs (spec §3.1's CHECK-spellings block, transcribed verbatim; no
-- `kind` literal -- see ELEMENT 3's comment above for why these are vacuous, and invisible to
-- the kind-shape classifier, on every non-belief row):
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_universe_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_universe_coupling CHECK (
    (belief_polarity IS DISTINCT FROM 'universal'
       OR (belief_universe IS NOT NULL AND btrim(belief_universe) <> ''))
    AND (belief_polarity IS DISTINCT FROM 'existential' OR belief_universe IS NULL));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_witness_universal_forbidden;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_witness_universal_forbidden CHECK (
    belief_polarity IS DISTINCT FROM 'universal' OR belief_witness IS NULL);
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_witness_observed_mandatory;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_witness_observed_mandatory CHECK (
    NOT (belief_polarity = 'existential' AND belief_basis = 'observed')
    OR (belief_witness IS NOT NULL AND btrim(belief_witness) <> ''));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_source_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_source_coupling CHECK (
    (belief_basis IS DISTINCT FROM 'testimony' OR belief_source IS NOT NULL)
    AND (belief_source IS NULL OR belief_basis = 'testimony'));
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS belief_premises_coupling;
ALTER TABLE :"schema".ledger ADD CONSTRAINT belief_premises_coupling CHECK (
    (belief_basis IS DISTINCT FROM 'derived'
       OR (belief_premises IS NOT NULL AND cardinality(belief_premises) >= 1))
    AND (belief_premises IS NULL OR belief_basis = 'derived'));

COMMENT ON CONSTRAINT belief_universe_coupling ON :"schema".ledger IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.1: universal requires a non-empty universe;
   existential forbids one. kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON CONSTRAINT belief_source_coupling ON :"schema".ledger IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.1: testimony requires a source; every other basis
   forbids one -- relaying another''s verdict as one''s own observation is unrepresentable by
   construction. kernel/lineage/s53-belief-substrate.sql.';
COMMENT ON CONSTRAINT belief_premises_coupling ON :"schema".ledger IS
  'design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.1: derived requires a non-empty premises array;
   every other basis forbids one. kernel/lineage/s53-belief-substrate.sql.';

-- ============================================================================================
-- ELEMENT 4 -- REFUSAL TRIGGERS (spec §3.2).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_belief_evidence() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_match text;
  v_id bigint;
BEGIN
  -- universe: row:<id> / artifact:<hash> tokens (fires only when non-NULL -- by
  -- belief_universe_kind_shape that means kind='belief', no separate test needed).
  IF NEW.belief_universe IS NOT NULL THEN
    FOR v_match IN
      SELECT (regexp_matches(NEW.belief_universe, 'row:([0-9]+)', 'g'))[1]
    LOOP
      v_id := v_match::bigint;
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE id = v_id) THEN
        RAISE EXCEPTION 'belief policy: universe token ''row:%'' names no existing row/artifact — an enumerated universe is the claim''s own evidence (ledger row 1887, rule 1: the surface list derives from where the system PRODUCES artifacts of that kind, not from where the auditor happens to stand); cite rows/artifacts that exist, or name the surface in prose (s53).', v_id;
      END IF;
    END LOOP;
    FOR v_match IN
      SELECT (regexp_matches(NEW.belief_universe, 'artifact:([^\s;,]*)', 'g'))[1]
    LOOP
      IF v_match !~ '^[0-9a-f]{64}$' OR NOT EXISTS (SELECT 1 FROM artifact WHERE hash = v_match) THEN
        RAISE EXCEPTION 'belief policy: universe token ''artifact:%'' names no existing row/artifact — an enumerated universe is the claim''s own evidence (ledger row 1887, rule 1); cite rows/artifacts that exist, or name the surface in prose (s53).', v_match;
      END IF;
    END LOOP;
  END IF;

  -- witness: row:<id> / artifact:<hash> tokens.
  IF NEW.belief_witness IS NOT NULL THEN
    FOR v_match IN
      SELECT (regexp_matches(NEW.belief_witness, 'row:([0-9]+)', 'g'))[1]
    LOOP
      v_id := v_match::bigint;
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE id = v_id) THEN
        RAISE EXCEPTION 'belief policy: witness token ''row:%'' resolves to nothing — a finding without its witness is treated exactly as ADR-0005 Rule 9 treats a verdict without its artifact: as nothing. Record the evidence first (led artifact put / the witnessed row), then the belief (s53).', v_id;
      END IF;
    END LOOP;
    FOR v_match IN
      SELECT (regexp_matches(NEW.belief_witness, 'artifact:([^\s,]*)', 'g'))[1]
    LOOP
      IF v_match !~ '^[0-9a-f]{64}$' OR NOT EXISTS (SELECT 1 FROM artifact WHERE hash = v_match) THEN
        RAISE EXCEPTION 'belief policy: witness token ''artifact:%'' resolves to nothing — a finding without its witness is treated exactly as ADR-0005 Rule 9 treats a verdict without its artifact: as nothing. Record the evidence first (led artifact put), then the belief (s53).', v_match;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_belief_evidence ON :"schema".ledger;
CREATE TRIGGER validate_belief_evidence BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_belief_evidence();

COMMENT ON FUNCTION :"schema".validate_belief_evidence() IS
  'kernel/lineage/s53-belief-substrate.sql: belief_universe/belief_witness row:/artifact:
   tokens are existence-checked at INSERT time (the s48/s52 mechanism, reused verbatim) -- a
   dangling or malformed evidence pointer in either position is refused, not silently accepted.
   design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.2.';

CREATE OR REPLACE FUNCTION :"schema".validate_belief_edges() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_pid bigint;
  v_new_actor bigint;
  v_tgt_kind text;
  v_tgt_actor bigint;
  v_tgt_superseded boolean;
BEGIN
  -- premises: existence only (in-force-ness is a READ-time judgment, §3.4).
  IF NEW.belief_premises IS NOT NULL THEN
    FOREACH v_pid IN ARRAY NEW.belief_premises LOOP
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE id = v_pid) THEN
        RAISE EXCEPTION 'belief policy: premises token ''row:%'' names no existing row — a derived belief''s premises must already be on the record (s53).', v_pid;
      END IF;
    END LOOP;
  END IF;

  -- contests / concurs: exist, kind=belief, unsuperseded, different actor.
  IF NEW.belief_contests IS NOT NULL OR NEW.belief_concurs IS NOT NULL THEN
    v_new_actor := NEW.actor;
    IF NEW.belief_contests IS NOT NULL THEN
      SELECT l.kind, l.actor,
             EXISTS (SELECT 1 FROM ledger s WHERE s.supersedes = l.id)
        INTO v_tgt_kind, v_tgt_actor, v_tgt_superseded
        FROM ledger l WHERE l.id = NEW.belief_contests;
      IF v_tgt_kind IS NULL THEN
        RAISE EXCEPTION 'belief policy: contests target row % does not exist (s53).', NEW.belief_contests;
      ELSIF v_tgt_kind <> 'belief' THEN
        RAISE EXCEPTION 'belief policy: contests target row % (kind ''%'') is not itself a belief — a contest names another belief, nothing else (s53).', NEW.belief_contests, v_tgt_kind;
      ELSIF v_tgt_superseded THEN
        RAISE EXCEPTION 'belief policy: row % is no longer in force; contesting settled history defeats nothing (the record beats memory — contest the current belief, or write your own) (s53).', NEW.belief_contests;
      ELSIF v_tgt_actor IS NOT NULL AND v_new_actor IS NOT NULL AND v_tgt_actor = v_new_actor THEN
        RAISE EXCEPTION 'belief policy: contest is the cross-principal doubt act — you cannot contest your own belief (revise it instead: supersede it with your new position, s31). A contest against row % by its own holder is a revision wearing a challenge''s clothes (s53).', NEW.belief_contests;
      END IF;
    END IF;
    IF NEW.belief_concurs IS NOT NULL THEN
      SELECT l.kind, l.actor,
             EXISTS (SELECT 1 FROM ledger s WHERE s.supersedes = l.id)
        INTO v_tgt_kind, v_tgt_actor, v_tgt_superseded
        FROM ledger l WHERE l.id = NEW.belief_concurs;
      IF v_tgt_kind IS NULL THEN
        RAISE EXCEPTION 'belief policy: concurs target row % does not exist (s53).', NEW.belief_concurs;
      ELSIF v_tgt_kind <> 'belief' THEN
        RAISE EXCEPTION 'belief policy: concurs target row % (kind ''%'') is not itself a belief (s53).', NEW.belief_concurs, v_tgt_kind;
      ELSIF v_tgt_superseded THEN
        RAISE EXCEPTION 'belief policy: row % is no longer in force; concurring with settled history corroborates nothing (write against the current belief) (s53).', NEW.belief_concurs;
      ELSIF v_tgt_actor IS NOT NULL AND v_new_actor IS NOT NULL AND v_tgt_actor = v_new_actor THEN
        RAISE EXCEPTION 'belief policy: self-concurrence is not corroboration — s17''s honesty, one edge over (s53).';
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_belief_edges ON :"schema".ledger;
CREATE TRIGGER validate_belief_edges BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_belief_edges();

COMMENT ON FUNCTION :"schema".validate_belief_edges() IS
  'kernel/lineage/s53-belief-substrate.sql: belief_premises elements must exist; belief_contests/
   belief_concurs targets must exist, be kind=belief, be unsuperseded, and carry a DIFFERENT
   actor than the writing row. design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.2.';

-- ============================================================================================
-- ELEMENT 5 -- validate_supersession_target RE-ISSUED: s43's write_refused refusal and s45's
-- three-kind standing-lifecycle block stay BYTE-IDENTICAL (verified against s45's own head
-- text, unedited by s46-s52); ONE new block added after them (spec §3.2 item 4 / §3.3
-- "Revision = supersession by the holder" -- see this file's own SPEC AMBIGUITY note above for
-- why this lives here, not in validate_belief_edges).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
  v_target_db_role text;
  v_target_subject bigint;
  v_target_actor bigint;
BEGIN
  IF NEW.supersedes IS NOT NULL THEN
    SELECT l.kind, l.principal_db_role, l.principal_subject, l.actor
      INTO v_target_kind, v_target_db_role, v_target_subject, v_target_actor
      FROM ledger l WHERE l.id = NEW.supersedes;

    IF v_target_kind = 'write_refused' THEN
      RAISE EXCEPTION 'Ledger policy: a write_refused row is UNRETRACTABLE (s43, ratified R6) — row % records a historical fact about a refused attempt; it asserts nothing retractable, and superseding it is the one path by which a later writer could make a refusal vanish from every current view. The record stands; if the refusal was wrong, the corrected write simply succeeds beside it (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 2).', NEW.supersedes;
    END IF;

    -- s45 §3.4: standing-lifecycle supersession discipline (byte-identical, s45's own text).
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

    -- s53: belief supersession discipline (spec §3.2 item 4 / §3.3 "Revision = supersession by
    -- the holder" -- a belief is revised only by its own holder; a different principal's
    -- contrary position is a CONTEST (belief_contests), never a supersession).
    IF v_target_kind = 'belief' THEN
      IF NEW.kind IS DISTINCT FROM 'belief' THEN
        RAISE EXCEPTION 'belief policy: a belief is revised only by its own holder through supersession (s31 uniform retraction), same kind (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3) — this write is kind ''%'', but row % is a belief. Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.kind, NEW.supersedes, NEW.supersedes;
      ELSIF NEW.actor IS NOT NULL AND v_target_actor IS NOT NULL AND NEW.actor <> v_target_actor THEN
        RAISE EXCEPTION 'belief policy: a belief is superseded only by its own holder (supersession = self-revision, s31) — row % is held by a different principal than this write''s actor (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3). Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.supersedes, NEW.supersedes;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_supersession_target ON :"schema".ledger;
CREATE TRIGGER validate_supersession_target BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_supersession_target();

COMMENT ON FUNCTION :"schema".validate_supersession_target() IS
  'BEFORE INSERT trigger (s43 Element 2/R6, widened s45 §3.4, widened s53 §3.2 item 4/§3.3):
   (1) a write_refused row is unretractable; (2) the three standing-lifecycle kinds accept only
   SAME-KIND, IDENTITY-CONTINUOUS supersessors; (3) a belief row is superseded only by its own
   holder (same kind, same actor) -- a cross-principal supersession attempt is refused, the
   correct act being a CONTEST (belief_contests), never a supersession
   (kernel/lineage/s53-belief-substrate.sql).';

-- ============================================================================================
-- ELEMENT 6 -- s42'S LAW SELF-APPLIED: compute_row_hash re-issued to 74 columns (the nine
-- belief_* columns appended in catalog ordinal order, before the predecessor link; base body =
-- s44's own text, unedited by s45-s52, verified above).
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
      -- s53: the nine belief_* columns (catalog ordinals 67..75)
      hashfield(r.belief_polarity),
      hashfield(r.belief_basis),
      hashfield(r.belief_universe),
      hashfield(r.belief_witness),
      hashfield(r.belief_source::text),
      hashfield(array_to_string(r.belief_premises, ',')),
      hashfield(r.belief_subject::text),
      hashfield(r.belief_contests::text),
      hashfield(r.belief_concurs::text),
      hashfield(predecessor_hash)
    ], E'\x1f'),
  'utf8')), 'hex');
$fn$;

-- ============================================================================================
-- ELEMENT 7 -- THE TWO COLUMN-COMPLETE VIEWS, +9 APPENDED (the s20 lesson). Base bodies: s44's
-- own text, unedited by s45-s52 (verified above).
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
       l.belief_premises, l.belief_subject, l.belief_contests, l.belief_concurs
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
       l.belief_premises, l.belief_subject, l.belief_contests, l.belief_concurs
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);
-- ============================================================================================
