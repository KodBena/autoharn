-- s69 ROLE-COHERENCE REFUSALS (design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, Fable-authored,
-- maintainer-ratified autoharn3 ledger row 201 -- his disposition verbatim in that row: "1(a) as
-- you suggest, with the proviso that the current can be resolved ... so a claim must be able to
-- be defeated and reclaimed ... 1(b) and 1(c) as recommended ... 2 as recommended ... our
-- append-only semantics should handle that transparently ... 3 approved ... 5 yes, fold into
-- s69"). Mechanizes the three enforcement gaps design/WORK-ROLE-PRACTICE-EVIDENCE-2026-07-28.md
-- §4 enumerated as pure convention (never kernel-checked) plus one semantics-neutral teach-text
-- re-issue explicitly ratified as item 5 -- NOT fail-safe-class for that one rider element (a
-- teach-text spelling fix is not a NEW refusal, so it does not ride the class-ratified lane;
-- it ships under its own explicit row-201 ratification instead, exactly as the spec's own §2
-- states). Sonnet-built per the standing delegation contract (CLAUDE.md ORCHESTRATION), from the
-- Fable-authored, maintainer-ratified spec above.
--
-- §0 (the governing principle, row 201, binding on every rule below): a higher authority can
-- judge another actor inept, so a claim must be DEFEATABLE and RECLAIMABLE. Nothing below binds
-- any act to a HISTORICAL role-holder -- every refusal below is computed against the CURRENT
-- (in-force / latest) holder only, so a later claim (s47's own "multiple claimants are
-- representable ... claim-stealing is representable, not refused") composes transparently: the
-- reclaimer becomes the new claimant-of-record and may then close, with zero additional
-- machinery. This delta adds NO new columns, NO new kinds, NO new views (spec §3) -- every
-- element below is a re-issued trigger function gaining ONE new refusal branch (or, for the
-- rider, a pure teach-text spelling change), verified against gates/hash_coverage_gate.py (no
-- serialized-column-set change is possible where no column is added) rather than merely
-- asserted.
--
-- THIS DELTA IS AUTHORED AND SCRATCH-WITNESSED ONLY; applying it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s68 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of any frozen sNN record (ADR-0005 Rule 8).
--
-- PREREQUISITE: this delta REQUIRES s68 (kernel/lineage/s68-typed-absence-dispositions.sql)
-- applied first -- it re-issues validate_work_item_close in the exact shape s38 left it,
-- validate_review_witness_existence in the exact shape s48 left it, validate_review in the exact
-- shape s21 left it, and validate_supersession_target in the exact shape s63 left it (its own
-- true immediately-prior re-issue, gates/lineage_reissue_lineage.py's own THE INVARIANT --
-- s64/s65/s66/s67/s68 none of them touch validate_supersession_target, verified by grep before
-- this delta was authored: only s43/s45/s53/s58/s61/s63 ever CREATE OR REPLACE that name).
-- Applying this file on a kernel that does not already carry those four objects in their s68-head
-- shape fails loudly at CREATE OR REPLACE FUNCTION time (a column/view/function referenced does
-- not exist), the correct, disclosed failure mode, matching every prior PREREQUISITE precedent.
-- THE HEAD-BODY RULE (s45's own standing instruction, carried here verbatim): at this delta's
-- authoring the lineage head is s68 (kernel/lineage/'s own directory listing, confirmed by the
-- builder before authoring). This file's four re-issued bodies are quoted, verified, against
-- their true immediately-prior re-issue's own text (s38/s48/s21/s63 respectively) -- see each
-- ELEMENT's own header for its `-- prior-body-sha256:` line.
--
-- WHY (the three refusals, each answering ADR-0000 Rule 2(a)'s two questions):
--
--   §1 CLOSER-IS-CLAIMANT-OF-RECORD. (a) The TYPE that forecloses "an item is closed by someone
--   other than whoever currently holds it" is a construction-time identity check binding the
--   closing actor to work_item_current.claimant -- the SAME resolution the view already computes
--   (the latest work_claimed row for the slug, DISTINCT ON ... ORDER BY id DESC), cited here, never
--   re-derived (ADR-0012 P1). (b) The operational lapse (design/WORK-ROLE-PRACTICE-EVIDENCE-
--   2026-07-28.md §4): claim-before-close was CLI-side only (`led work close`'s own comment,
--   "run-5 forensics: two work items were closed with no claim ever landing, unflagged"), and even
--   that CLI check verifies only that SOME claimant exists, never that the CLOSER is that
--   claimant -- a direct-boundary write bypasses the CLI check entirely, and even the CLI's own
--   check leaves cross-identity closes unrefused. This element closes BOTH gaps at the one
--   surface every writer must pass through (the write boundary, s43): a work_closed row's actor
--   must equal the slug's current claimant-of-record, INCLUDING the case where no claim exists at
--   all (claimant IS NULL) -- an unclaimed close is now refused at the kernel, not merely
--   discouraged CLI-side, closing the exact "two work items closed with no claim" hazard named
--   above rather than leaving it in reach. Per §0: bound to the LATEST in-force claimant only,
--   never the opener, never a historical claimant, no composite-parent carve-out (spec §1 item 1's
--   own explicit exclusions -- the decomposer claims the parent at decomposition time, so its
--   close is ordinary under this rule, a doctrinal convention the FAQ already carries).
--
--   §2 WITNESS-REF SHAPE, PER CLOSE SHAPE. (a) The TYPE that forecloses "a witness citation that
--   exists but proves nothing" is a target-KIND check on top of s48's existing target-EXISTENCE
--   check: a `row:<id>` witness is legal only when the cited row is evidentiary (kind IN
--   ('review','finding')) or is a CHILD's own work_opened row citing this closing item as its
--   parent, in force (the planning-close carve-in: a parent's discharge-by-decomposition is
--   witnessed by pointing at the child that carries the actual work, s33's own composite-discharge
--   convention). (b) The operational lapse (evidence doc §3 specimen 1, the autoharn2 row-1265
--   specimen): s48 checks EXISTENCE only, never SHAPE, so a `row:1232` citation of a bare
--   work_claimed row was accepted as a "review already on record" -- a claim event is not
--   evidence of judgment. This element closes the gap s48's own header named as future work
--   ("Only the row:<id> sub-shape ... is checkable") one axis further: checkable AND checked.
--
--   §3 REVIEW-REGARDS-IN-FORCE. (a) The TYPE that forecloses "a review of a fact that has since
--   been superseded, silently stale" is a construction-time check that a review's `regards`
--   target has no in-force superseder -- and, per ADR-0002/fail-loud, the refusal NAMES the
--   successor id the kernel already computed, rather than making the caller re-derive it. (b) The
--   operational lapse (evidence doc §3 specimen, "the experience4 431/435 specimen", witnessed
--   live TWICE): validate_review (s21) checks only that `regards` resolves to an earlier row and
--   that the author does not countersign themselves -- it never asks whether the regarded row is
--   STILL the current fact. Scope, stated so this element is not silently widened: it keys on the
--   REGARDED row being superseded -- a review of an in-force row (including the s56
--   reservation-discharge shape, a review regarding an in-force reservation review) is untouched.
--
--   RIDER (row 201 item 5, spec §2): s61's own signed-supersession-symmetry teach-text instructs
--   the operator to run `./led ...` -- a surface no current world has (the umbrella-CLI migration,
--   design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md, retired the bare per-verb shims). validate_
--   supersession_target is the ONE function carrying that text (both its s45-inherited
--   standing-lifecycle block and its own s61-minted symmetry block use the stale spelling). This
--   element re-issues it changing ONLY the printed spelling (`./led ` -> `./autoharn led `)
--   wherever it appears -- every other character byte-identical to s63's restored UNION body (the
--   rider's report carries the diff).
--
-- HISTORY: safe -- four function re-issues, each APPENDING or WIDENING exactly one refusal branch
-- (or, for the rider, editing ONLY quoted teach-text characters, no code-path change at all);
-- zero columns, zero kinds, zero views added or altered; no existing branch's REFUSAL CONDITION
-- loosened (§2 widens what a witness citation must additionally satisfy to be ACCEPTED --
-- strictly narrower acceptance, strictly additive refusal, the same shape s48 itself shipped
-- under). compute_row_hash/ledger_current/countersigned_in_force are UNCHANGED (no re-issue) --
-- this delta serializes no new column, so s42's law has nothing new to cover; proved by
-- gates/hash_coverage_gate.py's own set-equality check rather than asserted.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 form):
--   - INVARIANT: (1) a work_closed row's actor must equal work_item_current.claimant for its
--     slug (bound to the CURRENT/latest claimant only, per §0); (2) a row:<id> witness citation on
--     a work_closed/work_violation_disposition row is accepted only when the cited row is
--     kind IN ('review','finding'), or is an in-force work_opened row of a CHILD of the closing
--     slug; (3) a kind='review' row's `regards` target must have no in-force superseder, the
--     refusal naming the successor id when one exists; (4) validate_supersession_target's printed
--     teach-text spells the CLI surface as `./autoharn led`, never `./led`, with no other
--     behavioral change.
--   - QUANTIFICATION UNIVERSE: KINDS -- unchanged (no new kind; §1 constrains work_closed only,
--     §2 constrains work_closed/work_violation_disposition's existing work_review_ref field, §3
--     constrains kind='review' only, the rider touches no kind vocabulary at all). COLUMNS --
--     unchanged (zero added; every refusal reads EXISTING columns: actor, work_slug,
--     work_review_ref, regards, supersedes). VIEWS -- unchanged; work_item_current (s33 head) and
--     ledger_current (s21+ head) are READ, never re-issued (re-verified NOT members needing
--     re-issue: this delta adds no column either view would need to expose). TRIGGERS -- FOUR
--     re-issues (validate_work_item_close, validate_review_witness_existence, validate_review,
--     validate_supersession_target), each citing its true immediately-prior re-issue and carrying
--     a `-- prior-body-sha256:` line (gates/lineage_reissue_lineage.py, MIN_N_HASH=63, all four
--     re-issues are >= 63 so all four carry the line). ENGINE -- the ASP twin is DEFERRED this
--     pass, named as a LIMIT below (see LIMITS), matching s48/s52's own no-ASP-twin precedent for
--     a single-hop existence/shape check (s61's own header names the identical precedent).
--   - DENOMINATION: claimant-of-record in work_item_current.claimant (the one existing home, never
--     re-derived); witness shape in the cited row's own `kind` column (never a proxy string match
--     on `work_review_ref`'s free text); the review-regards successor in the actual row id a
--     supersedes-lookup computes (never a placeholder token the caller must resolve by hand).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): §1/§2/§3 are CLASS-RATIFIED
-- FAIL-SAFE (each ONLY adds a refusal -- nothing previously refused becomes newly permitted; the
-- maintainer additionally ratified each individually at row 201, "the standing ruling's own text"
-- notwithstanding, per his own "I'll reiterate ... but for the shape of s69 this needs to be taken
-- into account" -- read as belt-and-braces, not a claim that per-delta ratification was required).
-- The RIDER is NOT class-ratified fail-safe (it is a teach-text edit, not a new refusal at all --
-- outside the class's own definition either way) and ships under its own explicit item-5
-- ratification instead (spec §2's own header).
--
-- LIMITS (pre-registered, matching every prior delta's own disclosure convention):
--   - §1 binds the closer to the CURRENT claimant only; it does not (and per §0 must not) verify
--     that the claimant is the RIGHT performer for the work -- performer-identity fidelity stays
--     doctrine + the approved role-census view (spec §5's own "not covered, stated honestly").
--   - §2's shape check covers the `row:<id>` sub-shape only, the SAME limit s48 itself named
--     (a commit-hash or artifact-path witness is not kind-checkable from SQL).
--   - §3 keys on the regarded row being superseded; it does not relitigate WHICH successor is
--     "the right one" when more than one row claims to supersede the same target (an edge case
--     with no uniqueness constraint on `supersedes` anywhere in this lineage) -- the refusal names
--     the LATEST such superseder by id, the same latest-wins idiom work_item_current.claimant
--     already uses one concern over.
--   - NO ASP TWIN IN THIS PASS. All three checks are single-hop EXISTS/equality tests over
--     already-in-force facts (the s48/s52 shape, not s60's recursive-closure shape) -- an
--     independent ASP derivation would mirror the SQL nearly verbatim. Filed as a possible
--     follow-on, not built or claimed built (s61's own identical disclosure, re-applied).
--   - Like every trigger/CHECK-enforced refusal in this lineage, all four refusals bind ONLY the
--     granted `:role`'s ordinary INSERT path -- a schema-owner/superuser with DDL privilege can
--     disable a trigger or write directly, the same disclosed bound s26..s68 already name.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s68):
--   VALIDATE (reachable throwaway): psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--     -v schema=s69val -v kern=s69val_kernel -v role=s69val_rw \
--     -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--     [... s21 through s68, the exact CHAIN this file's own seen-red fixture carries ...] \
--     -f s69-role-coherence-refusals.sql
--     (genesis seed per s26; register the write-boundary principal and discharge the s40/s43/s60
--     birth sequence before exercising any other act.)
--   REAL: NEVER applied to any existing world by this authoring act. Enters a FUTURE world's
--   birth chain via bootstrap/new-project.sh's LINEAGE_CHAIN (this same commit). Authored and
--   scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION; DROP/CREATE TRIGGER).
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
-- ELEMENT 1 -- validate_work_item_close RE-ISSUED (§1, closer-is-claimant-of-record). True
-- immediately-prior re-issue: s38 (kernel/lineage/s38-bookkeeping-close.sql) Element 2. Every
-- pre-existing branch below is BYTE-IDENTICAL to s38's own text; ONE new block appended at the
-- top (checked before the disposition/strict logic, since a close with no standing to close at
-- all has nothing else worth evaluating).
-- prior-body-sha256: c8e424f3a46ba7517453db8eef56c772859f202a9d51846135f75d1ccf2c0ff8 (s38-bookkeeping-close.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_close(r :"schema".ledger, is_composite boolean, tg_schema text)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
  v_claimant bigint;
BEGIN
  -- s69 §1 (design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, row 201 item 1(a)):
  -- CLOSER-IS-CLAIMANT-OF-RECORD. Bound to the CURRENT holder only -- work_item_current.claimant
  -- is the SAME resolution s47/the evidence census already treat as "the claimant" (latest
  -- in-force work_claimed row, last-claim-wins), cited here rather than re-derived (ADR-0012 P1).
  -- A later claim DEFEATS an earlier one (s47: "multiple claimants are representable ...
  -- claim-stealing is representable, not refused"), so a higher authority's reclaim-then-close
  -- composes transparently (row 201 §0's own proviso) -- nothing here binds to a historical
  -- claimant, the opener, or (spec's own explicit exclusion) a composite parent's own
  -- decomposition-time claim as a permanent exemption from this rule.
  SELECT wic.claimant INTO v_claimant FROM work_item_current wic WHERE wic.slug = r.work_slug;
  IF r.actor IS DISTINCT FROM v_claimant THEN
    RAISE EXCEPTION 'Ledger policy: close of work item ''%'' refused — closing actor % is not the item''s claimant-of-record (%), defined as the actor of the LATEST in-force work_claimed row for this slug (s69 §1, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md; the SAME resolution work_item_current.claimant already computes). A cross-identity close is a HANDOFF, and handoffs are claims: claim the item as yourself first (./autoharn led work claim %), then close. If the current claimant is inept or unavailable, a higher authority DEFEATS the claim with a fresh one (claim-stealing is legal by design, s47) and closes as the new claimant — nothing here forecloses reclaim.', r.work_slug, r.actor, COALESCE(v_claimant::text, '<none — this item was never claimed>'), r.work_slug;
  END IF;

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
-- No DROP/CREATE TRIGGER needed: the dispatcher (validate_work_item()) already calls
-- validate_work_item_close(...) by name (s35's own dispatcher body, untouched here) -- CREATE OR
-- REPLACE FUNCTION above is sufficient for the new body to take effect on the next call.

COMMENT ON FUNCTION :"schema".validate_work_item_close(:"schema".ledger, boolean, text) IS
  'kernel/lineage/s69-role-coherence-refusals.sql: the s35 leaf, s38-widened (bookkeeping
   disposition), s69-widened (closer-is-claimant-of-record, §1): (1) the closing actor must equal
   work_item_current.claimant for the slug, bound to the CURRENT/latest claimant only (row 201 §0
   -- a claim is always defeatable-and-reclaimable, never frozen to a historical holder); (2) a
   close past the migration epoch needs a review disposition; (3) a strict/composite close of
   disposition deferred/bookkeeping is refused, and a witnessed strict close re-checks the
   obligation tree.';

-- ============================================================================================
-- ELEMENT 2 -- validate_review_witness_existence RE-ISSUED (§2, witness-ref shape per close
-- shape). True immediately-prior re-issue: s48 (kernel/lineage/s48-review-witness-existence.sql)
-- Element 1 (its only prior definition -- confirmed, grepped, before authoring this delta: no
-- s49..s68 file re-issues this function). Existence check (the byte-identical carried branch)
-- runs first, unchanged; the NEW shape check runs immediately after, for the SAME cited row,
-- inside the SAME loop iteration (a natural widening of the one check this trigger owns, not a
-- second, parallel scan).
-- prior-body-sha256: 1409e899c3813b9e2c2ddb0d4497761760ecf6ea0093393d1d28dcd754d09da7 (s48-review-witness-existence.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_review_witness_existence() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_match text;
  v_id bigint;
  v_head bigint;
  v_cited_kind text;
BEGIN
  IF NEW.kind IN ('work_closed', 'work_violation_disposition')
     AND NEW.work_review_ref IS NOT NULL THEN
    FOR v_match IN
      SELECT (regexp_matches(NEW.work_review_ref, 'row:([0-9]+)', 'g'))[1]
    LOOP
      v_id := v_match::bigint;
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE id = v_id) THEN
        SELECT max(id) INTO v_head FROM ledger;
        RAISE EXCEPTION 'Ledger policy: review-witness citation ''row:%'' in work_review_ref is refused — no ledger row % exists (checked at INSERT time; review-witness position only, close-family kinds work_closed/work_violation_disposition -- s48). A witness citation naming a nonexistent row is a claim with a dangling evidence pointer, in the one place evidence pointers are load-bearing.%  Cite an EXISTING row instead (e.g. --review-witness row:<id> naming an already-recorded review event), or use --review-deferred/--review-bookkeeping if no review exists yet.',
          v_id, v_id,
          CASE WHEN v_head IS NOT NULL AND v_id > v_head
               THEN ' This id is AT OR BEYOND the ledger''s current head — if you meant to cite THIS row''s own id, that is impossible by construction: ledger `id` is server-assigned (s15) and is never visible to the row being inserted.'
               ELSE '' END;
      END IF;

      -- s69 §2 (design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, row 201 item 1(b)): WITNESS-REF
      -- SHAPE, PER CLOSE SHAPE. Existence alone (above) is not evidence of judgment (the
      -- autoharn2 row-1265 specimen: a bare work_claimed row cited as a "review already on
      -- record"). Legal shapes: the cited row is itself evidentiary (kind IN ('review',
      -- 'finding')), OR it is an IN-FORCE work_opened row of a CHILD of the closing slug (the
      -- planning-close carve-in: a parent's discharge-by-decomposition points at the child that
      -- actually carries the work, s33's own composite-discharge convention). `commit:<sha>`/
      -- artifact-path witnesses are untouched by construction -- this loop only ever sees
      -- `row:<id>` tokens (the regexp above).
      SELECT l.kind INTO v_cited_kind FROM ledger l WHERE l.id = v_id;
      IF v_cited_kind NOT IN ('review', 'finding')
         AND NOT EXISTS (
           SELECT 1 FROM ledger_current lc
           WHERE lc.id = v_id AND lc.kind = 'work_opened' AND lc.work_parent = NEW.work_slug
         )
      THEN
        RAISE EXCEPTION 'Ledger policy: review-witness citation ''row:%'' in work_review_ref is refused — row % exists but is not evidence: its kind is ''%'', not ''review'' or ''finding'', and it is not an in-force work_opened row of a CHILD of this closing item (s69 §2, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md). Legal witnesses here are: a review or finding row (the judgment itself), or — for a planning/parent item discharged by decomposition — the work_opened row of a child slug naming THIS item as its --parent (the planning-close carve-in). A work_claimed row (or any other kind) is not a review, whatever it cites (the autoharn2 row-1265 specimen this refusal closes).', v_id, v_id, v_cited_kind;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_review_witness_existence ON :"schema".ledger;
CREATE TRIGGER validate_review_witness_existence BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_review_witness_existence();

COMMENT ON FUNCTION :"schema".validate_review_witness_existence() IS
  'kernel/lineage/s69-role-coherence-refusals.sql (s48-widened, §2): a work_closed/
   work_violation_disposition row''s work_review_ref row:<id> tokens must EXIST (s48) AND be
   SHAPED as evidence -- kind IN (review, finding), or an in-force work_opened row of a CHILD of
   the closing slug (the planning-close carve-in). Prose `refs` citations of future/foreign rows
   stay legal everywhere else, unchanged (s48''s own WK1-c scope boundary).';
-- ============================================================================================

-- ============================================================================================
-- ELEMENT 3 -- validate_review RE-ISSUED (§3, review-regards-in-force). True immediately-prior
-- re-issue: s21 (kernel/lineage/s21-session-aware-distinctness.sql) (its only prior definition --
-- confirmed, grepped, before authoring this delta: no s22..s68 file re-issues this function). The
-- three pre-existing branches (must-name-regards, must-resolve-earlier, no-self-countersign) are
-- BYTE-IDENTICAL below; ONE new block appended after them.
-- prior-body-sha256: 54bccb60fc6a8b92a26c01171f466e1528186e92a77b85f0a651cfe140223d6d (s21-session-aware-distinctness.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_review() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  target_actor bigint;
  v_successor bigint;
BEGIN
  IF NEW.kind = 'review' THEN
    IF NEW.regards IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: a review must name the row it regards.';
    END IF;
    SELECT l.actor INTO target_actor FROM ledger l WHERE l.id = NEW.regards AND l.id < NEW.id;
    IF target_actor IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: regards must resolve to an earlier row.';
    END IF;
    IF target_actor = NEW.actor THEN
      RAISE EXCEPTION 'Ledger policy: a row''s author may not countersign it (segregation of duties).';
    END IF;

    -- s69 §3 (design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md, row 201 item 1(c)):
    -- REVIEW-REGARDS-IN-FORCE. A review of a row that has since been SUPERSEDED is stale the
    -- moment it is written (the experience4 431/435 specimen, witnessed live twice) -- the
    -- kernel already knows the successor (whichever row's `supersedes` names NEW.regards), so the
    -- refusal NAMES it rather than making the caller re-derive it (ADR-0002: a refusal that
    -- withholds the fix it just computed is not teaching). Scope, stated so this element is not
    -- silently widened: this keys on the REGARDED row being superseded -- a review of an IN-FORCE
    -- row (including the s56 reservation-discharge shape, a review regarding an in-force
    -- reservation review) is untouched, since its regarded row carries no superseder at all.
    SELECT s.id INTO v_successor FROM ledger s WHERE s.supersedes = NEW.regards ORDER BY s.id DESC LIMIT 1;
    IF v_successor IS NOT NULL THEN
      RAISE EXCEPTION 'Ledger policy: review refused — row % (this review''s regards target) has an IN-FORCE SUPERSEDER, row % (s69 §3, design/FABLE-S69-ROLE-COHERENCE-REFUSALS-SPEC.md) — a review of a superseded row is stale the moment it is written. Cite the successor instead: retry this review with regards=%.', NEW.regards, v_successor, v_successor;
    END IF;
  ELSIF NEW.regards IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: regards is reserved for kind=review.';
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_review ON :"schema".ledger;
CREATE TRIGGER validate_review BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_review();

COMMENT ON FUNCTION :"schema".validate_review() IS
  'kernel/lineage/s69-role-coherence-refusals.sql (s21-widened, §3): a review must name an
   earlier row it regards, its author may not countersign itself, and (s69) the regarded row
   must carry NO in-force superseder — a review of a superseded row is refused, naming the
   successor id to cite instead. A review regarding an in-force row (including an s56
   reservation-discharge review) is unaffected.';
-- ============================================================================================

-- ============================================================================================
-- ELEMENT 4 -- THE RIDER (row 201 item 5, spec §2): validate_supersession_target RE-ISSUED,
-- TEACH-TEXT SPELLING ONLY. True immediately-prior re-issue: s63
-- (kernel/lineage/s63-supersession-body-restoration.sql) Element 1 (the SIXTH re-issue overall;
-- confirmed by grep before authoring this delta: s64/s65/s66/s67/s68 none of them touch this
-- function name). Every line below is BYTE-IDENTICAL to s63's own restored UNION body EXCEPT the
-- two `./led ` occurrences (both inside quoted RAISE EXCEPTION teach-text: the s45-inherited
-- standing-lifecycle block, and the s61-minted signed-supersession-symmetry block), each changed
-- to `./autoharn led ` -- the umbrella-CLI surface (design/FABLE-AUTOHARN-UMBRELLA-CLI-SPEC.md)
-- this repository's own worlds actually carry; the bare `./led` shim was retired ahead of the
-- 2.0.0 tag (root-shim-pruning, ledger row 1357). No logic, condition, column, or non-spelling
-- character changes (the build report's own diff shows this).
-- prior-body-sha256: 5d04a209290b734fca6cdb3e829475afd195200f4c133f9e633be3f14b22a17d (s63-supersession-body-restoration.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_supersession_target() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_target_kind text;
  v_target_db_role text;
  v_target_subject bigint;
  v_target_actor bigint;
  v_target_thread text;
  v_target_regards bigint;
  v_target_signed boolean;
  v_new_signed boolean;
BEGIN
  IF NEW.supersedes IS NOT NULL THEN
    SELECT l.kind, l.principal_db_role, l.principal_subject, l.actor, l.missive_thread,
           l.missive_regards
      INTO v_target_kind, v_target_db_role, v_target_subject, v_target_actor, v_target_thread,
           v_target_regards
      FROM ledger l WHERE l.id = NEW.supersedes;

    IF v_target_kind = 'write_refused' THEN
      RAISE EXCEPTION 'Ledger policy: a write_refused row is UNRETRACTABLE (s43, ratified R6) — row % records a historical fact about a refused attempt; it asserts nothing retractable, and superseding it is the one path by which a later writer could make a refusal vanish from every current view. The record stands; if the refusal was wrong, the corrected write simply succeeds beside it (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 2).', NEW.supersedes;
    END IF;

    -- s45 §3.4: standing-lifecycle supersession discipline (the conversion-found closure --
    -- without it, ANY writer could lift a revocation or resurrect a stale declaration by
    -- superseding it with an unrelated row of a different kind).
    IF v_target_kind IN ('principal_standing_declared', 'principal_suspended', 'principal_revoked') THEN
      IF NEW.kind IS DISTINCT FROM v_target_kind THEN
        RAISE EXCEPTION 'Ledger policy: a standing-lifecycle row (kind ''%'', row %) is superseded ONLY by its OWN kind (s45, kernel/lineage/s45-standing-lifecycle.sql §3.4) — this write is kind ''%''. Rotation/re-declaration or unbind for declarations (./autoharn led principal declare-standing / ./autoharn led principal undeclare-standing); re-suspend-correction or lift for suspensions (./autoharn led principal suspend --supersedes / ./autoharn led principal lift-suspension); re-revoke-correction for revocations. A cross-kind supersession would silently alter derived standing (who a role speaks for, or whether a principal is suspended/revoked) with no typed act — refused at construction.', v_target_kind, NEW.supersedes, NEW.kind;
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

    -- s53: belief supersession discipline (unedited).
    IF v_target_kind = 'belief' THEN
      IF NEW.kind IS DISTINCT FROM 'belief' THEN
        RAISE EXCEPTION 'belief policy: a belief is revised only by its own holder through supersession (s31 uniform retraction), same kind (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3) — this write is kind ''%'', but row % is a belief. Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.kind, NEW.supersedes, NEW.supersedes;
      ELSIF NEW.actor IS NOT NULL AND v_target_actor IS NOT NULL AND NEW.actor <> v_target_actor THEN
        RAISE EXCEPTION 'belief policy: a belief is superseded only by its own holder (supersession = self-revision, s31) — row % is held by a different principal than this write''s actor (s53, design/FABLE-BELIEF-SUBSTRATE-SPEC.md §3.3). Another principal''s contrary position is a CONTEST — write your own belief with contests=row:% and both enter visible doubt until resolved by evidence class or withdrawal (Q3, paraconsistent; recency never decides between principals).', NEW.supersedes, NEW.supersedes;
      END IF;
    END IF;

    -- s58: missive_sent supersession discipline (Q7 ratified, spec §2.5) -- superseding a
    -- missive_sent row is refused unless the superseding row is itself the successor missive
    -- in the SAME thread. No same-actor condition -- the party is the world, not the principal
    -- (spec §13 item 6).
    IF v_target_kind = 'missive_sent' THEN
      IF NOT (NEW.kind = 'missive_sent' AND NEW.missive_thread = v_target_thread) THEN
        RAISE EXCEPTION 'missive policy: a missive_sent row (row %, thread ''%'') is superseded ONLY by a same-thread successor missive_sent row (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5, Q7 ratified) — an author revising its position SENDS the revision (a withdrawal, or a successor assertion/request with responds_to) so the supersession itself travels and the addressee''s missive_stale view sees it; a silent local retraction is exactly the staleness class this family exists to close.', NEW.supersedes, v_target_thread;
      END IF;
    END IF;

    -- s58: missive_received target refused outright -- a receipt is unretractable history
    -- (spec §2.5, §13 item 6).
    IF v_target_kind = 'missive_received' THEN
      RAISE EXCEPTION 'missive policy: a missive_received row (row %) may NEVER be superseded — a receipt is a historical fact of arrival; superseding it is the one path by which delivery could be un-recorded and by which the dedup guarantee could be argued around (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5, §13 item 6). Nothing was recorded.', NEW.supersedes;
    END IF;

    -- s58: missive_disposed supersession discipline -- re-disposition of the SAME receipt only
    -- (the s45 identity-continuity pattern, spec §2.5; AMENDMENT 1: was `regards`, now
    -- `missive_regards`).
    IF v_target_kind = 'missive_disposed' THEN
      IF NOT (NEW.kind = 'missive_disposed' AND NEW.missive_regards = v_target_regards) THEN
        RAISE EXCEPTION 'missive policy: a missive_disposed row (row %, regards %) is superseded ONLY by a same-kind re-disposition regarding the SAME receipt (design/FABLE-MISSIVES-KERNEL-SPEC.md §2.5) — this write is kind ''%'' regarding %.', NEW.supersedes, v_target_regards, NEW.kind, NEW.missive_regards;
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
        RAISE EXCEPTION 'Ledger policy: SIGNED supersession symmetry refused (s61, design/FABLE-ENTITLEMENT-ENFORCEMENT-SPEC.md §2 item 1) — target row % (kind ''%'') rests its force on a VERIFIED signature (an independently GPG-attested commission); it may only be superseded by an act whose OWN force also rests on a verified signature. This write carries no signature_symmetry_witness naming a commission_signature_verified row. Remedy: have the maintainer write a SIGNED commission directing this supersession (gpg --detach-sign --armor, then LED_ACTOR=commissioner ./autoharn led commission "<the ask>", then ./verify-commission --attest --id <that commission''s id> — VERIFIED only), then supply --signature-witness <the attestation row''s id> on this write.', NEW.supersedes, v_target_kind;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_supersession_target ON :"schema".ledger;
CREATE TRIGGER validate_supersession_target BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_supersession_target();

COMMENT ON FUNCTION :"schema".validate_supersession_target() IS
  'BEFORE INSERT trigger (s43 Element 2/R6, widened s45 §3.4, widened s53 §3.2 item 4/§3.3,
   widened s58 §2.5/Q7, widened s61 item 1, RESTORED s63, TEACH-TEXT SPELLING FIXED s69 rider --
   row 201 item 5): (1) a write_refused row is unretractable; (2) the three standing-lifecycle
   kinds accept only SAME-KIND, IDENTITY-CONTINUOUS supersessors; (3) a belief row is superseded
   only by its own holder; (4) a missive_sent row is superseded only by a same-thread successor
   missive_sent row; (5) a missive_received row may never be superseded; (6) a missive_disposed
   row is superseded only by a same-regards re-disposition; (7) a target row whose force rests on
   a VERIFIED signature may only be superseded by a row that itself carries a valid
   signature_symmetry_witness. All seven refusals are checked in this ONE home, never a parallel
   trigger (kernel/lineage/s69-role-coherence-refusals.sql). This re-issue changes ONLY the
   printed CLI spelling in the standing-lifecycle and symmetry teach-texts (./led -> ./autoharn
   led) -- no condition, column, or other character differs from s63''s restored body.';
-- ============================================================================================
