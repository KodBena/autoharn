-- s38 BOOKKEEPING CLOSE (design/FABLE-BOOKKEEPING-CLOSE-SPEC.md, Fable-authored spec, RATIFIED
-- 2026-07-17, maintainer choosing option (b) of design/MAINT-DECISION-QUEUE-2026-07-17.md Q1;
-- verbatim ratification + orchestrator grounds in the ledger, durable-graded decision row of the
-- same date). A THIRD, machine-verified review-disposition constructor for `work close`, closed
-- to exactly ONE form (a git-commit witness) per the spec's own "the category is CLOSED" section.
--
-- Sonnet-authored per the standing delegation contract (CLAUDE.md ORCHESTRATION), from the
-- Fable-authored, maintainer-ratified spec above. This delta is AUTHORED and SCRATCH-WITNESSED
-- only; APPLYING it to any live/existing world is the maintainer's act at a FUTURE world's birth
-- (runs-are-strictly-linear ruling, 2026-07-11), never taken here. An ADDITIVE delta applied ON
-- TOP of the s15..s37 kernel (the established remediation-delta idiom), NOT a retro-edit of a
-- frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of any existing mechanism
-- (ADR-0012 P1: this delta reuses work_review_disposition/work_review_ref, s29's own existing
-- columns, rather than minting new ones for the same shape).
--
-- PREREQUISITE: this delta REQUIRES s35 (kernel/lineage/s35-validation-decomposition.sql) applied
-- first -- Element 2 below re-issues validate_work_item_close(), the LEAF s35 minted, rather than
-- reverting to any earlier monolithic validate_work_item() body. Applying this file on a pre-s35
-- kernel fails loudly at CREATE OR REPLACE FUNCTION time (validate_work_item_close does not exist
-- with this signature), the correct, disclosed failure mode for a hard dependency, matching every
-- prior delta's own PREREQUISITE precedent. ALSO REQUIRES s29
-- (kernel/lineage/s29-obligation-item-key-and-typed-close.sql): the vocabulary/CHECK this delta
-- widens (work_review_disposition_check) and the column it constrains (work_review_ref) are both
-- s29's own. Applying this file on a pre-s29 kernel fails loudly at ALTER TABLE ... ADD CONSTRAINT
-- time (constraint does not exist to DROP -- the IF EXISTS guard makes that silent, but the
-- subsequent ADD CONSTRAINT against a schema with no work_review_disposition column fails loudly
-- at CREATE time instead), the correct, disclosed failure mode.
--
-- WHY (operator-side prose; NOT subject-visible): the spec's own "Why loosen at all" section --
-- the panel deployment's git-transaction pairing convention manufactures work items whose entire
-- close content is "the commit landed, here is its hash." Forcing witnessed/deferred onto those
-- closes produces either review-gap debt with nothing to review, or boilerplate countersigns --
-- the content-free-review failure shape design/USER-RECIPES-FAQ.md's Review Discipline section
-- already names. The fix is a typed distinction, not a stretched ceremony: the close KIND says
-- whether there was judgment, and the "no judgment" claim is checked by machine (kernel: commit
-- SHAPE at construction; CLI: commit EXISTENCE at construction), never asserted by the operator.
--
-- THE CATEGORY IS CLOSED (spec's own "the creep guard" section, verbatim in spirit): v1
-- `bookkeeping` admits exactly ONE form -- a close whose witness is a git commit that verifiably
-- exists in the world's own repository. Nothing else (no artifact paths, no URLs, no ledger-row
-- references, no free text) is admissible. Widening the category requires a new Fable-authored,
-- maintainer-ratified spec; an executor extending it under any other authority is an ADR-0013
-- violation. The kernel enforces the SHAPE half of that closure (the new CHECK below); the CLI
-- enforces the EXISTENCE half (`led work close --review-bookkeeping`, this same commit's
-- bootstrap/templates/led.tmpl edit) -- see Element 3/ADR-0011 below for the honest trust boundary
-- between the two.
--
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

-- ELEMENT 1 -- VOCABULARY WIDENING + THE NEW SHAPE CHECK (spec Element 1).
-- work_review_disposition_check (s29) widens from ('witnessed','deferred') to
-- ('witnessed','deferred','bookkeeping') -- THIS is the one loosening this spec ratifies;
-- everything else in this delta narrows it back down. work_review_disposition_check carries no
-- `kind` test at all (a flat vocabulary CHECK on the column's own value, distinct from the
-- (kind, column, arity) SHAPE gates/kind_shape_manifest_gate.py tracks for work_review_ref/
-- work_review_disposition -- see this delta's own gate-wiring commit for the confirmation that
-- classifier is unaffected), so widening it here touches no kind-shape manifest row.
--
-- The new CHECK, `work_review_bookkeeping_requires_commit_ref`, mirrors
-- `work_review_witnessed_requires_ref` (s29) one clause over: a bookkeeping row without a
-- commit-shaped review ref is UNREPRESENTABLE, not merely discouraged. The regex
-- `^commit:[0-9a-f]{7,40}$` admits a short-to-full-length lowercase-hex git SHA (7 is git's own
-- historical minimum unambiguous abbreviation; 40 is a full SHA-1; a future SHA-256 repository's
-- longer hex digest is OUT OF SCOPE for this v1 -- named, not silently accepted or rejected: this
-- schema has no repository-hash-algorithm fact to gate on, so a 41+ char digest is refused by this
-- regex exactly like any other malformed witness, teach-text naming the two honest alternatives,
-- CLI-side).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_disposition_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_disposition_check CHECK (
    work_review_disposition IS NULL
    OR work_review_disposition IN ('witnessed', 'deferred', 'bookkeeping'));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_bookkeeping_requires_commit_ref;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_bookkeeping_requires_commit_ref CHECK (
    work_review_disposition IS DISTINCT FROM 'bookkeeping'
    OR work_review_ref ~ '^commit:[0-9a-f]{7,40}$');

-- REVIEWER-CAUGHT GAP (pre-commit review round, this same delta): work_review_disposition is a
-- column s37 already shares between TWO kinds -- work_closed (this delta's own home for
-- 'bookkeeping') and work_violation_disposition (s37's own vocabulary, 'witnessed'/'deferred'
-- there too, see work_review_ref_kind_shape one column over). Without a kind test of its own,
-- work_review_disposition_check above admits 'bookkeeping' on EITHER kind -- a raw INSERT could
-- construct a work_violation_disposition row carrying work_review_disposition='bookkeeping' (plus
-- a commit-shaped ref, satisfying the CHECK immediately above), a state this file's own closure
-- statement claims does not exist ("the bookkeeping fact rides the EXISTING work_closed kind's own
-- columns") and one work_bookkeeping_closes (`WHERE kind = 'work_closed'`) never enumerates --
-- invisible to the one audit view this delta's own Element 4 built specifically to make the
-- category's growth rate visible. Fixed by mirroring the file family's established kind-scoping
-- idiom one column over (s37's own work_review_ref_kind_shape, `col IS NULL OR kind IN (...)`,
-- one-way): 'bookkeeping' is licensed on work_closed alone, closing the gap the SAME way s37 closed
-- work_resolution_check's own flat-union defect (that file's own "reviewer-witnessed defect 3"
-- header, this constraint's direct precedent).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_bookkeeping_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_bookkeeping_kind_shape CHECK (
    work_review_disposition IS DISTINCT FROM 'bookkeeping' OR kind = 'work_closed');

COMMENT ON CONSTRAINT work_review_disposition_check ON :"schema".ledger IS
  'kernel/lineage/s38-bookkeeping-close.sql: widens s29''s two-value vocabulary to a third,
   machine-verified value, bookkeeping -- a close with no judgment content, whose witness is a
   git commit verifiably existing in the world''s own repository at construction (CLI-side check;
   see work_review_bookkeeping_requires_commit_ref for the kernel-side shape half). The category
   is CLOSED to this one form -- widening it further requires a new Fable-authored,
   maintainer-ratified spec (design/FABLE-BOOKKEEPING-CLOSE-SPEC.md, "the category is CLOSED").';
COMMENT ON CONSTRAINT work_review_bookkeeping_requires_commit_ref ON :"schema".ledger IS
  'kernel/lineage/s38-bookkeeping-close.sql: mirrors work_review_witnessed_requires_ref (s29) one
   clause over -- a bookkeeping row without a commit-shaped review ref (commit:<7-40 lowercase hex
   chars>) is UNREPRESENTABLE. The kernel checks SHAPE only; commit EXISTENCE is a CLI-side check
   at construction (ADR-0011: the honest trust boundary, see this file''s ELEMENT 3 note below).';
COMMENT ON CONSTRAINT work_review_bookkeeping_kind_shape ON :"schema".ledger IS
  'kernel/lineage/s38-bookkeeping-close.sql: reviewer-caught gap fix -- work_review_disposition is
   shared with work_violation_disposition rows (s37), so without this CHECK ''bookkeeping'' would be
   constructible on a work_violation_disposition row, invisible to work_bookkeeping_closes (WHERE
   kind = ''work_closed''). Mirrors work_review_ref_kind_shape (s37) one column over: one-way,
   licenses ''bookkeeping'' on kind = ''work_closed'' alone.';

-- ============================================================================================
-- ELEMENT 2 -- validate_work_item_close() RE-ISSUED (the s35 LEAF, CREATE OR REPLACE -- ADR-0012
-- P1, not a second copy). Two changes from s35's own text, both named:
--   (a) the mandatory-disposition arm needs NO edit at all -- it refuses only on
--       `work_review_disposition IS NULL`, which is already false for disposition='bookkeeping'
--       (a non-NULL value); the third constructor is therefore ALREADY accepted there, by
--       construction, with zero lines changed. Stated here, not silently relied on, per this
--       delta's own closure statement below.
--   (b) the strict-close arm GAINS one ELSIF: without it, disposition='bookkeeping' would match
--       NEITHER the existing 'deferred' nor 'witnessed' branches and fall through with NO
--       refusal and NO obligation-tree check -- silently letting a strict bookkeeping close
--       succeed, exactly the contradiction the spec's own Element 2 forbids ("--strict demands
--       witnessed -- a strict bookkeeping close is a contradiction, same footing as the existing
--       --review-deferred --strict refusal"). Every other line below is BYTE-IDENTICAL to s35's
--       own validate_work_item_close, including the mandatory-disposition RAISE text (unchanged:
--       it still names only witnessed/deferred as the two named remedies there, since a caller
--       reading THAT specific refusal is mid-construction and has not yet chosen a disposition at
--       all -- the CLI's own usage/teach text, not this trigger's, is where the third constructor
--       is introduced to a caller before they ever reach the kernel).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_close(r :"schema".ledger, is_composite boolean, tg_schema text)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
BEGIN
  IF r.id > COALESCE((SELECT epoch FROM migration_epoch LIMIT 1), 0)
     AND r.work_review_disposition IS NULL THEN
    RAISE EXCEPTION 'Ledger policy: work_closed row for item ''%'' (ledger id %) carries no review disposition — every close act past this world''s migration epoch (id %, see %.migration_epoch) must be witnessed or deferred, never silent (s29 Element B, sec-10 epoch amendment). Retry with --review-witness <ref> or --review-deferred.', r.work_slug, r.id, (SELECT epoch FROM migration_epoch LIMIT 1), tg_schema;
  END IF;
  IF (COALESCE(r.work_strict_close, false) OR COALESCE(is_composite, false)) THEN
    IF r.work_review_disposition = 'deferred' THEN
      RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' requires --review-witness (a review already on record) — --review-deferred cannot satisfy strict mode''s immediate obligation-tree requirement, because a just-deferred obligation is, by definition, unresolved the moment it is created (s29 Element C). Record the review first (./led review ...), then close with --review-witness <ref>.', r.work_slug;
    ELSIF r.work_review_disposition = 'bookkeeping' THEN
      RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' requires --review-witness (a review already on record) — --review-bookkeeping is a judgment-free close and cannot satisfy strict mode''s obligation-tree requirement (a bookkeeping close carries no reviewer verdict to check the tree against; s38 Element 2, same footing as --review-deferred --strict). Record the review first (./led review ...), then close with --review-witness <ref>.', r.work_slug;
    ELSIF r.work_review_disposition = 'witnessed' THEN
      SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
        INTO blockers
        FROM work_item_strict_blockers(r.work_slug) b;
      IF blockers IS NOT NULL THEN
        RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' refused — its obligation tree is unresolved: %. Resolve every named leaf, then retry (s29 Element C: strict close is a pure query over the derived conjunction, no stored verdict).', r.work_slug, blockers;
      END IF;
    END IF;
  END IF;
  RETURN r;
END; $fn$;
-- The dispatcher (validate_work_item()) and every OTHER leaf (validate_work_item_open/depends/
-- close_is_composite) are UNTOUCHED -- this delta re-issues exactly the one leaf its own concern
-- (the close review-disposition/strict logic) owns, per s35's own decomposition discipline. No
-- DROP/CREATE TRIGGER is needed: the dispatcher already calls validate_work_item_close(...) by
-- name (s35's own dispatcher body), and CREATE OR REPLACE FUNCTION above is sufficient for the
-- new body to take effect on the next call -- the trigger's own definition (name, timing, table)
-- never changes.

-- ============================================================================================
-- ELEMENT 3 -- work_review_gap / work_item_strict_blockers() VERIFIED UNCHANGED, NOT MERELY
-- ASSERTED (spec's own explicit instruction: "the executor's witness plan checks both, not just
-- the view"). Neither object is re-issued by this file -- both already select `disp = 'deferred'`
-- (work_item_strict_blockers(), s29/s37) / `work_review_disposition = 'deferred'` (work_review_gap,
-- s29, re-issued s31/s32/s37 with an added UNION arm for a different kind, its 'deferred' predicate
-- itself untouched throughout) BY EQUALITY -- 'bookkeeping' matches neither predicate, so a
-- bookkeeping close creates NO review-gap debt and blocks NO strict-close obligation-tree walk,
-- exactly the disposition-with-no-judgment-content the spec calls for. This is stated here, in the
-- provenance record, rather than left as an implication a future reader must re-derive -- and it is
-- WITNESSED, not merely reasoned about, in this delta's own scratch-witness pass (see the commit
-- record / orchlog note for this delta): work_review_gap shows no new debt after a --review-
-- bookkeeping close, and a --strict close attempt against a bookkeeping-closed item's own
-- obligation-tree leaf is refused by Element 2's new ELSIF above, never silently passed through.
--
-- THE ENGINE LAYER -- also verified, not merely asserted, per the spec's own closure statement
-- ("the executor checks whether the engine's work-layer rules enumerate disposition vocabulary and
-- extends them in the same change if so"). `engine/ledger_floor.py`'s `work_review_floor_atoms()`
-- (`own_unresolved` CTE: `WHERE c.disp = 'deferred' AND ...`) and `engine/lp/work_review.lp`'s own
-- ASP rule (`w_disposition(R,deferred), not w_discharged(R)`) BOTH test equality against the single
-- literal `deferred` -- neither ENUMERATES the full disposition vocabulary as a closed set (neither
-- reads "IN ('witnessed','deferred')" or its ASP equivalent), so NEITHER requires a code change:
-- `engine/ledger_edb.py`'s `w_disposition(RowId, Disp)` fact emission (`disp_col =
-- "COALESCE(work_review_disposition,'')"`) already carries WHATEVER value the column holds through
-- generically, with no hardcoded value set to widen. A bookkeeping-disposition close therefore
-- already produces `w_disposition(RowId,bookkeeping)` with zero engine-layer edits, and is already
-- correctly excluded from `own_unresolved`/its ASP twin by the SAME not-equal-to-deferred logic
-- that already excludes 'witnessed'. Verified live in this delta's own scratch-witness pass (the
-- SQL/ASP differential, `./judge`, in AGREE on a bkprobe fixture carrying a bookkeeping close) --
-- not merely read and reasoned about.
-- ============================================================================================

-- ============================================================================================
-- ELEMENT 4 -- work_bookkeeping_closes, THE NEW AUDIT PROJECTION (spec's own Element 1). A view
-- over `ledger`, NOT `ledger_current` -- RECORD semantics, everything forever, mirroring s37's own
-- `work_violation_history` (declared history reader by design, gates/ledger_reader_allowlist.py's
-- own entry for that view, extended in this same commit to cover this one too). Every use of the
-- escape hatch is enumerable in one query, so the category's growth rate is itself an auditable
-- fact -- the mechanism that keeps Element 1's loosening honest under ADR-0013 Rule 3: the
-- ceremony is removed only where a machine check replaces it, and the removals are permanently
-- visible, never quietly retracted out of view by a later supersession the way a current-truth
-- reader would silently drop a superseded row.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_bookkeeping_closes
    WITH (security_invoker = true) AS
SELECT work_slug AS slug, id AS close_id, actor AS closer, work_review_ref AS commit_ref, ts AS closed_at
FROM   :"schema".ledger
WHERE  kind = 'work_closed' AND work_review_disposition = 'bookkeeping';

COMMENT ON VIEW :"schema".work_bookkeeping_closes IS
  'kernel/lineage/s38-bookkeeping-close.sql: every judgment-free (bookkeeping) close ever recorded,
   raw/UNFILTERED (record semantics, like work_violation_history one file over -- s37) -- the
   auditable trail that keeps the v1-only-one-form loosening (spec: "the category is CLOSED")
   honest: the category''s growth rate is itself a query away, permanently, retraction or not.';

GRANT SELECT ON :"schema".work_bookkeeping_closes TO :"role";

-- ============================================================================================
-- HISTORY: safe -- one existing CHECK re-issued WIDER (work_review_disposition_check gains one
-- new legal value, 'bookkeeping', disjoint from the pre-existing two -- every pre-existing row's
-- own disposition value was already witnessed/deferred/NULL and remains exactly as legal as
-- before: RE-ISSUE-ONLY, no existing row touched, no backfill, no UPDATE); two NEW CHECKs
-- (work_review_bookkeeping_requires_commit_ref, work_review_bookkeeping_kind_shape) that are BOTH
-- VACUOUSLY SATISFIED by every pre-existing row (work_review_disposition IS DISTINCT FROM
-- 'bookkeeping' is TRUE for every row whose disposition is witnessed, deferred, or NULL -- i.e.
-- every row that exists before this delta ever ships, since 'bookkeeping' did not exist as a legal
-- value until the CHECK immediately above these two licensed it in the SAME file: ADDITIVE-
-- VOCABULARY, neither new constraint can ever be exercised by a row this delta's own widening
-- does not first make legal; work_review_bookkeeping_kind_shape closes the reviewer-caught gap
-- that a flat, kind-blind vocabulary widening would otherwise leave open on
-- work_violation_disposition rows, s37's own sibling kind sharing this same column); one existing LEAF
-- FUNCTION re-issued with one new ELSIF branch (a NEW refusal path, never a relaxation of an
-- existing one -- the pre-existing 'deferred'/'witnessed' branches are BYTE-IDENTICAL, unchanged);
-- one new VIEW (work_bookkeeping_closes, a pure additive audit projection, no existing object
-- narrowed or widened by its presence). NEITHER widening relaxes any EXISTING row's legality or
-- any EXISTING refusal's trigger condition -- a pre-s38 world's witnessed/deferred closes, strict
-- or not, behave byte-for-byte as before. Grounds: re-issue-only / additive-vocabulary (Element 1);
-- output-equality on every pre-existing branch / new-refusal-only, never a relaxation (Element 2);
-- new-view-only, no reader narrowed (Element 4). Detect sibling fingerprints BEHAVIOR (the widened
-- vocabulary's third legal value plus the new CHECK's own shape), never a pinned object name, per
-- the s29/s30 detect ruling of 2026-07-16 (migrate-detect-drift fix: a fingerprint pinned to a
-- single named object silently false-negatives the moment a later refactor moves the marker
-- elsewhere -- e.g. s35's own dispatcher-into-leaves move, or s32's edge-source single-homing).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: a work_closed row's review disposition is one of exactly THREE constructors --
--     witnessed (non-empty ref, s29 CHECK, unchanged), deferred (enters work_review_gap debt, s29
--     view, unchanged), or bookkeeping (a commit-shaped ref, this delta's new CHECK, whose commit
--     existed in the world's own repository at CLI-side construction time and appears permanently
--     in work_bookkeeping_closes) -- or the row is refused at construction (no disposition at all,
--     s29's mandatory-disposition trigger clause, unchanged). No fourth value is representable
--     (the widened but still-closed vocabulary CHECK); no bookkeeping row without a commit-shaped
--     ref is representable (work_review_bookkeeping_requires_commit_ref); no bookkeeping row on any
--     kind other than work_closed is representable (work_review_bookkeeping_kind_shape, the
--     reviewer-caught gap fix); a --strict close of any disposition other than witnessed is refused
--     (Element 2, the new ELSIF closes what would otherwise have been a silent fall-through gap for
--     exactly this one new value).
--
--   - QUANTIFICATION UNIVERSE (re-read every table/view the s15..s37 chain exposes to :role,
--     checked against this delta's own additions, mirroring every prior delta's own
--     re-verification discipline):
--       TABLES: no new base table (ledger's own existing work_review_disposition/work_review_ref
--         columns, s29, are reused wholesale -- ADR-0012 P1 -- carrying the new value/shape, not a
--         new column).
--       VIEWS re-read for the wildcard/column-complete class (s20/s22/s23/s24/s26/s28/s29/s37 all
--         named): ledger_current / countersigned_in_force -- explicit column lists (s20+), NEITHER
--         gains a new column here (this delta adds no column, only a new legal VALUE on two
--         already-listed columns) -- re-verified NOT members needing re-issue. work_item_current
--         (s22, extended s28/s37) -- same reasoning, its review_disposition/review_ref columns
--         already pass through whatever value the closing row carries; NOT re-issued.
--         work_item_violations / work_violation_history -- re-verified NOT members: neither reads
--         work_review_disposition/work_review_ref at all (both are s37's own violation-answering
--         machinery, an orthogonal concern -- a work_closed row's OWN review disposition is not a
--         work_item_violations arm). work_review_gap -- re-verified UNCHANGED (Element 3 above):
--         its 'deferred'-equality predicate is untouched, so it needs no re-issue to stay correct
--         under the widened vocabulary -- the correctness is BY EQUALITY, not by any code this
--         delta needed to touch. work_bookkeeping_closes -- THIS delta's own new view (Element 4).
--       KIND VOCABULARY -- unchanged (no new `kind` value); the bookkeeping fact rides the EXISTING
--         work_closed kind's own work_review_disposition/work_review_ref columns -- but NOT
--         "exactly as witnessed/deferred already do" (an earlier draft of this paragraph claimed
--         that; it is false, reviewer-caught: witnessed/deferred are NOT work_closed-exclusive --
--         s37 shares work_review_disposition/work_review_ref with work_violation_disposition rows
--         too, and witnessed/deferred ride BOTH kinds by s37's own design, work_review_ref_kind_shape
--         licensing both). 'bookkeeping' is deliberately NOT given that same two-kind license: this
--         delta's new work_review_bookkeeping_kind_shape CHECK scopes it to kind = 'work_closed'
--         alone, so the bookkeeping universe is EXACTLY the work_closed rows work_bookkeeping_closes
--         (WHERE kind = 'work_closed') enumerates -- no work_violation_disposition row can ever
--         carry it, closing the gap a flat vocabulary widening (Element 1's own CHECK, which carries
--         no kind test) would otherwise have left open.
--       GRANTS -- mirrors s29/s37's own posture: the ONE new view (work_bookkeeping_closes) gets a
--         fresh GRANT SELECT; the widened CHECK and the re-issued leaf function ride their
--         already-granted base table/already-EXECUTE-by-default function, so no other grant change
--         is needed.
--       ENGINE -- verified, not merely asserted (Element 3 above): `engine/ledger_floor.py`'s
--         `work_review_floor_atoms()` and `engine/lp/work_review.lp`'s own rule both test equality
--         against the literal 'deferred' only, and `engine/ledger_edb.py`'s `w_disposition/2` fact
--         emission carries the column's live value through generically -- NEITHER requires a code
--         change; a bookkeeping-disposition close already round-trips correctly through both
--         producers with zero engine-layer edits. NOT wired into `judge`/`ledger_differential.py`
--         as a new top-level scratch-differential (mirrors s29's own verified precedent -- `judge`
--         does not auto-discover `engine/lp/*.lp`); this delta's own scratch-witness pass instead
--         exercises the EXISTING work_review.lp differential against a bkprobe fixture carrying a
--         bookkeeping close, confirming AGREE, per the spec's own witness plan.
--
--   - DENOMINATION: the disposition value is denominated in the CLOSED, three-member vocabulary
--     itself (witnessed|deferred|bookkeeping), never a proxy (never a free-text label, never a
--     boolean "is this bookkeeping" flag re-deriving what the vocabulary column already states).
--     The bookkeeping witness is denominated in a GIT COMMIT SHA (7-40 lowercase hex chars,
--     regex-shaped at the kernel, existence-checked CLI-side) -- never a ledger row id, an artifact
--     path, or a URL; the spec's own "the category is CLOSED" section is explicit that widening the
--     admissible witness FORM (not merely adding a second value alongside it) requires a new
--     ratified spec, not this executor's own authority.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta is NOT
-- class-ratified fail-safe -- it LOOSENS an existing refusal (the vocabulary CHECK widens to admit
-- a value that was previously refused outright), which the standing ruling's own text places
-- OUTSIDE the class-ratified fail-safe lane by definition ("nothing existing relaxed" is the
-- fail-safe class's own requirement; Element 1's widening is precisely something existing being
-- relaxed, even though every OTHER element of this delta narrows it back down to one closed form).
-- It IS the Fable-authored, maintainer-ratified delta design/FABLE-BOOKKEEPING-CLOSE-SPEC.md's own
-- header names (RATIFIED 2026-07-17, this file's own header).
--
-- LIMITS (pre-registered, matching s22/s26/s28/s29/s37's own disclosure convention):
--   - Commit EXISTENCE is checked CLI-side, at construction, only -- a hand-issued INSERT (bypassing
--     `led work close --review-bookkeeping`) could cite a nonexistent commit; the kernel enforces
--     SHAPE only (spec's own Element 3, "the honest trust boundary"). Same disclosed bound every
--     CLI-side check in this project already has, and the standing no-raw-writes instruction is the
--     (social) control for it -- work_bookkeeping_closes gives an auditor the row set to spot-check
--     against the repository, the strongest honest claim available.
--   - The commit-shape regex admits 7-40 lowercase hex characters (git's historical short-SHA floor
--     through a full SHA-1); a repository on a longer hash algorithm (a future SHA-256 git) is
--     OUT OF SCOPE for this v1 -- named, not silently accepted or rejected: no fact this schema
--     carries distinguishes a repository's hash algorithm, so any digest this regex cannot match is
--     refused exactly like any other malformed witness (CLI-side teach-text), never silently
--     truncated or coerced.
--   - Like every trigger/CHECK-enforced refusal in this lineage (s22/s26/s28/s29/s37's own
--     disclosed bound), the widened vocabulary CHECK and the new commit-ref-shape CHECK bind ONLY
--     the granted `:role`'s ordinary INSERT path -- a schema-owner/superuser with DDL privilege can
--     disable a constraint or write directly, the same disclosed bound s26/s28/s29/s37 already name.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s20/.../s37): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway): psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--     -v schema=s38val -v kern=s38val_kernel -v role=s38val_rw \
--     -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--     -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--     -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--     -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s27-chain-high-water.sql \
--     -f s28-work-parent-edge.sql -f s29-obligation-item-key-and-typed-close.sql \
--     -f s30-typed-dependency-edges.sql -f s31-supersession-uniform-retraction.sql \
--     -f s32-edge-views-single-home.sql -f s33-composite-discharge.sql \
--     -f s34-computed-grade-refusal.sql -f s35-validation-decomposition.sql \
--     -f s36-decision-grade.sql -f s37-violation-disposition.sql \
--     -f s38-bookkeeping-close.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` in this SAME
--   commit (s37 precedent). It was authored and scratch-witnessed on scratch schema pairs in the
--   TOY db only -- NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; CREATE OR REPLACE).
-- ============================================================================================
