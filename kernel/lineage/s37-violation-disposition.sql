-- s37 VIOLATION DISPOSITION (design/FABLE-ORPHAN-DISPOSITION-SPEC.md v2, RATIFIED 2026-07-16,
-- reviewed under ADR-0014 by a fresh-context Fable instance -- consult banked verbatim at
-- design/ORCH-ADR14-ORPHAN-DISPOSITION-CONSULT-2026-07-16.md, amendments A1-A6 incorporated).
-- HISTORY: safe -- one new kind (work_violation_disposition), three new nullable columns legal
-- ONLY on that new kind (work_violation_class/work_violation_target_id two-way, work_violation_
-- witness one-way), TWO existing columns' kind-shape CHECKs WIDENED to also license the new kind
-- (work_resolution: vocabulary widened with two new legal values reissued/retired, disjoint from
-- the pre-existing shipped/superseded/dropped/deferred set; work_review_ref: one-way CHECK
-- widened from kind='work_closed' to kind IN ('work_closed','work_violation_disposition')) --
-- NEITHER widening relaxes any EXISTING row's legality (a pre-existing work_closed row's
-- work_resolution/work_review_ref shape is untouched; the widened CHECKs are still exactly as
-- strict for kind='work_closed' as before), two views re-issued (work_item_violations narrows,
-- one new companion view work_violation_history) -- no existing row is touched, no backfill, no
-- UPDATE.
--
-- Sonnet-authored per the standing delegation contract (CLAUDE.md ORCHESTRATION), from the
-- Fable-authored, maintainer-ratified spec above (ledger item s37-violation-disposition-build).
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is
-- the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11),
-- never taken here. An ADDITIVE delta applied ON TOP of the s15..s36 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second hand-copy of any existing mechanism (ADR-0012 P1: one home per mechanism -- this delta
-- reuses work_resolution/rationale/work_review_disposition/work_review_ref, s22/s29's own
-- existing columns, rather than minting five new ones for the same shapes).
--
-- PREREQUISITE: this delta REQUIRES s36 (kernel/lineage/s36-decision-grade.sql) applied first --
-- it re-issues ledger_current/countersigned_in_force in the EXACT column-list shape s36 left them
-- (the s20/.../s36 LESSON: a view's SELECT l.<cols> is frozen at CREATE VIEW time), appending the
-- three new columns after s36's own last column (l.decision_grade); and it re-issues
-- work_item_violations, which s33 last shaped (s34/s36 added no column to it). Applying this
-- file on a pre-s36 kernel fails loudly at CREATE OR REPLACE VIEW time (column l.decision_grade
-- does not exist), the correct, disclosed failure mode for a hard dependency, matching every
-- prior delta's own PREREQUISITE precedent. ALSO REQUIRES s35
-- (kernel/lineage/s35-validation-decomposition.sql): Element 2 below ADDS A FIFTH LEAF to s35's
-- dispatcher-with-leaves decomposition of validate_work_item() (validate_work_item_open/depends/
-- close_is_composite/close, called from the dispatcher) rather than reverting to the pre-s35
-- monolithic function body -- caught LIVE by gates/ledger_reader_allowlist.py's own scratch run
-- on this delta's first draft, which had copied s33's monolith verbatim and orphaned s35's four
-- leaves as undeclared raw-ledger readers (see Element 2's own header for the full account).
-- Applying this file on a pre-s35 kernel fails loudly at CREATE OR REPLACE FUNCTION time
-- (validate_work_item_open/depends/close_is_composite/close do not exist), the correct,
-- disclosed failure mode.
--
-- WHY (operator-side prose; NOT subject-visible): the spec's Provenance section, two witnessed
-- traps. (1) The PANEL trap: superseding a composite parent burns its slug (s31); the five
-- children's surviving parent-edges become orphaned_by_retraction violations, three already
-- closed -- no re-issue possible, permanent debt, only the stop-gate's fail-open. (2) The CONSULT
-- trap: an informs self-edge (accepted at construction -- cycle refusal is blocks-close-only)
-- surfaces as dependency_cycle and persists after the edge's own retraction (the view's
-- dependency arm reads raw history by design). Both are members of the SAME class: a
-- work_item_violations member with no answering act, counted as blocking debt forever.
--
-- THE WHOLE DELTA IN ONE LINE (spec "The principle"): every violations-view member becomes
-- answerable by a typed, reviewed, validity-bounded disposition act -- debt until answered,
-- record forever -- without touching retraction semantics anywhere (nothing here un-burns a
-- slug, revives a retracted row, or edits history).
--
-- DESIGN CHOICE, NAMED (not in the spec's own text, a builder decision within its bounds): the
-- spec says a disposition carries "a stable key identifying the violations-view member it
-- answers (the member class + the violating act's ledger id)". Four of work_item_violations'
-- eleven arms already carry a natural row id (shipped_without_witness, the three orphan_* arms,
-- closed_but_tree_defeated); five do not (duplicate_open, dependency_cycle, dangling_parent,
-- parent_cycle, blocks_close_cycle -- all slug-keyed, no single edge/row is "the" violator of a
-- cycle or a duplicate). This delta gives EVERY member a target_id (appended column, Element 1
-- below) by using the natural row id where one exists, and the SLUG'S OWN work_opened row id
-- where it does not (always resolvable once a slug is opened, and itself the row the spec's own
-- "violating act" language most naturally lands on for a slug-shaped defect) -- filed here, not
-- buried, because it is the one place this spec's prose underdetermines the mechanism.
--
-- ELEMENT 1 -- KIND + COLUMNS + THE RE-DERIVED VALIDATOR (spec sec-1).
-- New kind `work_violation_disposition`, three new columns (work_violation_class,
-- work_violation_target_id, work_violation_witness), reusing four EXISTING columns for the rest
-- of the act's shape (work_resolution: 'reissued'|'retired', vocabulary widened, disjoint from
-- work_closed's own four values; rationale: the free-text basis, already CORE/kind-agnostic;
-- work_review_disposition/work_review_ref: the SAME witnessed/deferred discipline work_closed
-- already carries, kind-shape widened one column). work_item_violations (Element 1 continued,
-- below the trigger) gains a target_id column on EVERY arm and narrows: a member drops out only
-- while an in-force disposition answers it AND the disposition's own checkable basis still holds
-- (Element 3/A4, folded into the SAME view re-issue rather than a second pass). The validator
-- establishes "is an in-force violations member" by RE-DERIVING against work_item_violations
-- itself (a real query keyed on (violation, target_id), never a parse of the view's `detail` text
-- column -- the consult's own builder note, "minor... not amendments").
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_violation_class text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_violation_target_id bigint;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_violation_witness bigint;

COMMENT ON COLUMN :"schema".ledger.work_violation_class IS
  'kernel/lineage/s37-violation-disposition.sql: which work_item_violations arm (violation
   column value, e.g. orphaned_by_retraction, dependency_cycle) this disposition answers. Legal
   and REQUIRED only on kind=work_violation_disposition (work_violation_class_kind_shape).';
COMMENT ON COLUMN :"schema".ledger.work_violation_target_id IS
  'kernel/lineage/s37-violation-disposition.sql: the answered violations-view row''s target_id
   (the violating act''s own ledger row id, or -- for the five slug-keyed arms with no single
   violating row -- the slug''s own work_opened row id; see this file''s header DESIGN CHOICE).
   Legal and REQUIRED only on kind=work_violation_disposition
   (work_violation_target_id_kind_shape).';
COMMENT ON COLUMN :"schema".ledger.work_violation_witness IS
  'kernel/lineage/s37-violation-disposition.sql: for work_resolution=reissued, the cited
   successor ledger row id (element 1 spec text: "the row cites it via the witness column").
   NULLABLE even when reissued (element 4: warns, never refused -- the kernel cannot verify
   successor equivalence). Legal ONLY on kind=work_violation_disposition
   (work_violation_witness_kind_shape, one-way).';

-- THE VOCABULARY WIDENING (s22/s25's own re-issue point, one member later -- additive union, no
-- removal, no reordering of the pre-existing members; caught LIVE on this delta's own first
-- scratch-witness attempt, exactly the s36-header-shaped lesson this file's PREREQUISITE section
-- already warns every reader to expect one column/value at a time).
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS ledger_kind_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT ledger_kind_check CHECK (kind IN
    ('assumption','decision','question','verification',
     'finding','snag','revision','note','review',
     'work_opened','work_claimed','work_depends_on','work_closed',
     'commission','work_violation_disposition'));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_violation_class_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_violation_class_kind_shape CHECK (
    (kind = 'work_violation_disposition') = (work_violation_class IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_violation_target_id_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_violation_target_id_kind_shape CHECK (
    (kind = 'work_violation_disposition') = (work_violation_target_id IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_violation_witness_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_violation_witness_kind_shape CHECK (
    work_violation_witness IS NULL OR kind = 'work_violation_disposition');

-- REUSE, WIDENED (ADR-0012 P1 -- one home per shape, not five new columns for shapes that
-- already have one): work_resolution's vocabulary widens with two values disjoint from
-- work_closed's own set (no ambiguity possible: a work_closed row can never read 'reissued'/
-- 'retired', a work_violation_disposition row can never read 'shipped'/'superseded'/'dropped'/
-- 'deferred' -- both enforced by the SAME single CHECK below), and its kind-shape iff widens to
-- the two-kind union. rationale (CORE, no shape column at all) carries the basis text --
-- required, refused empty, by the trigger (Element 2 below), not a CHECK.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_resolution_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_resolution_kind_shape CHECK (
    (kind IN ('work_closed', 'work_violation_disposition')) = (work_resolution IS NOT NULL));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_resolution_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_resolution_check CHECK (
    work_resolution IS NULL
    OR work_resolution IN ('shipped','superseded','dropped','deferred','reissued','retired'));

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_review_ref_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_review_ref_kind_shape CHECK (
    work_review_ref IS NULL OR kind IN ('work_closed', 'work_violation_disposition'));

-- ============================================================================================
-- s20/.../s36 LESSON RE-APPLIED (most recently s36's own header, which caught this LIVE on its
-- own first scratch-witness attempt): ledger_current/countersigned_in_force GAIN the THREE new
-- columns, APPENDED AT THE END. Column list = s36's exact list + the three new ones.
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
       l.work_violation_class, l.work_violation_target_id, l.work_violation_witness
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
       l.work_violation_class, l.work_violation_target_id, l.work_violation_witness
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 2 -- a FIFTH LEAF, added to s35's dispatcher-with-leaves decomposition
-- (kernel/lineage/s35-validation-decomposition.sql), NOT a reversion to the pre-s35 monolith --
-- caught LIVE by gates/ledger_reader_allowlist.py's own scratch run on this delta's first draft
-- (which had copied s33's monolithic validate_work_item() body verbatim, silently UNDOING s35's
-- refactor and orphaning its four leaf functions as undeclared raw-ledger readers). The four
-- PRE-EXISTING leaves (validate_work_item_open/depends/close_is_composite/close) are NOT
-- re-issued here -- untouched, exactly s35's own header discipline for a delta that adds a fifth
-- concern rather than changing one of the first four.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_disposition(r :"schema".ledger)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  -- Three refusals, in order:
  --   (a) the target must be an IN-FORCE work_item_violations member RIGHT NOW, established by
  --       RE-DERIVING against the view itself (a typed (violation, target_id) match), never by
  --       parsing `detail` (consult builder note). A pre-s37 world naturally refuses at the
  --       CLI's own live column-existence gate first (Element 4).
  --   (b) IN-FORCE-SCOPED uniqueness (consult A3): a second disposition on the SAME
  --       (class, target_id) is refused only while a PRIOR one is still in force (reads
  --       ledger_current) -- superseding a wrong disposition reopens the slot.
  --   (c) the basis (rationale) must be stated, non-blank.
  IF NOT EXISTS (SELECT 1 FROM work_item_violations v
                 WHERE v.violation = r.work_violation_class
                   AND v.target_id = r.work_violation_target_id) THEN
    RAISE EXCEPTION 'Ledger policy: work_violation_disposition (class ''%'', target %) refused — that is not currently an in-force work_item_violations member (re-derived against the view itself, never parsed from display text). Either the defect was never real, has already lapsed on its own, or is already answered by an in-force disposition (see work_violation_history for the trail). Run ./led work violations to see what is currently answerable.', r.work_violation_class, r.work_violation_target_id;
  END IF;
  IF EXISTS (SELECT 1 FROM ledger_current lc
             WHERE lc.kind = 'work_violation_disposition'
               AND lc.work_violation_class = r.work_violation_class
               AND lc.work_violation_target_id = r.work_violation_target_id) THEN
    RAISE EXCEPTION 'Ledger policy: work_violation_disposition (class ''%'', target %) refused — an IN-FORCE disposition already answers this member (s37 consult A3: uniqueness is in-force-scoped, not raw-history). If that disposition was wrong, SUPERSEDE it first (--supersedes <its-row-id>) — superseding reopens the slot; a raw-history uniqueness read would re-mint the slug-burn trap this spec exists to remove.', r.work_violation_class, r.work_violation_target_id;
  END IF;
  IF r.rationale IS NULL OR btrim(r.rationale) = '' THEN
    RAISE EXCEPTION 'Ledger policy: work_violation_disposition requires a non-blank basis (the rationale field) — "what became of this defect?" is the whole point of the record (spec: "a free-text basis"). Retry with a stated basis.';
  END IF;
  -- consult A5: the SAME witnessed-or-deferred discipline work_closed already carries (s29
  -- Element B), unconditionally -- work_violation_disposition is a BRAND NEW kind (s37 itself),
  -- so there is no legacy-row epoch question to gate on; every disposition ever written requires
  -- one.
  IF r.work_review_disposition IS NULL THEN
    RAISE EXCEPTION 'Ledger policy: work_violation_disposition for item ''%'' carries no review disposition — a disposition removes stop-gate debt, so it carries the SAME witnessed-or-deferred posture as work_closed (consult A5), never silent. Retry with --review-witness <ref> or --review-deferred.', r.work_violation_class;
  END IF;
  RETURN r;
END; $fn$;

-- ============================================================================================
-- THE DISPATCHER, RE-ISSUED (CREATE OR REPLACE, the SAME function s35 defined -- ADR-0012 P1):
-- ONE new ELSIF arm calling the new leaf, under the SAME "has this slug ever been opened"
-- precondition posture the other three later-event kinds share -- EXCEPT a disposition answers a
-- VIOLATION, not a work item, so it does NOT require NEW.work_slug (it has none) and is
-- dispatched BEFORE that shared precondition, not through it. Every other line is BYTE-IDENTICAL
-- to s35's own dispatcher.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  is_composite boolean;
BEGIN
  IF NEW.kind = 'work_opened' THEN
    NEW := validate_work_item_open(NEW);
  ELSIF NEW.kind = 'work_violation_disposition' THEN
    NEW := validate_work_item_disposition(NEW);
  ELSIF NEW.kind IN ('work_claimed','work_depends_on','work_closed') THEN
    IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' has no opening act — every later event on an item must reference an item that has been opened (invariant 2, item identity).', NEW.work_slug;
    END IF;
    IF NEW.kind = 'work_depends_on' THEN
      NEW := validate_work_item_depends(NEW);
    END IF;
    IF NEW.kind = 'work_closed' THEN
      is_composite := validate_work_item_close_is_composite(NEW.work_slug);
      NEW := validate_work_item_close(NEW, is_composite, TG_TABLE_SCHEMA);
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_work_item ON :"schema".ledger;
CREATE TRIGGER validate_work_item BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_work_item();

-- ============================================================================================
-- ELEMENT 1 continued -- work_item_violations RE-ISSUED: (a) every arm gains a target_id column
-- (see header DESIGN CHOICE), (b) dependency_cycle NARROWS to blocks-close edges only (RATIFIED
-- sibling narrowing -- blocks-close cycles are already refused at construction, so this member
-- becomes properly vacuous, defense-in-depth, matching blocks_close_cycle's own existing vacuous
-- posture; an informs cycle is now a legal non-event, matching informs' advisory-only semantics),
-- (c) a FINAL anti-join drops any arm answered by an in-force, basis-still-holding disposition
-- (Element 3 / A4 folded in here, "one join... not a procedure"). Every pre-existing CTE body
-- (opens/dup_open/shipped_no_witness/deps/dangling_dep/parents/dangling_parent/parent_anc/
-- parent_cycle/blocks_close_deps/bc_reach/blocks_close_cycle/opened_current/orphan_claims/
-- orphan_closes/orphan_deps/orphan_children/composites/composite_hand_closed/
-- closed_but_tree_defeated) is UNCHANGED, byte-for-byte, below -- only `deps`/`reach`/`dep_cycle`
-- (dependency_cycle's OWN computation) are replaced with a blocks-close-only pair, and every arm's
-- final SELECT gains one more expression (its target_id).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_violations
    WITH (security_invoker = true) AS
WITH RECURSIVE
  opens AS (
    SELECT work_slug AS slug, count(*) AS n
    FROM :"schema".ledger WHERE kind = 'work_opened'
    GROUP BY work_slug
  ),
  dup_open AS (
    SELECT slug FROM opens WHERE n > 1
  ),
  shipped_no_witness AS (
    SELECT work_slug AS slug, id
    FROM :"schema".ledger
    WHERE kind = 'work_closed' AND work_resolution = 'shipped'
      AND (work_witness IS NULL OR btrim(work_witness) = '')
  ),
  -- s37: dependency_cycle NARROWS to blocks-close edges only -- reads work_edge_blocks_close
  -- (s32's single home of the RAW s30 blocks-close edge relation) instead of ALL work_depends_on
  -- rows. depends_on_unknown_slug's OWN `deps`/`dangling_dep` (below, unchanged) still reads every
  -- edge type -- this narrowing is scoped to dependency_cycle alone, per the ratified sibling fix.
  deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent
    FROM :"schema".ledger WHERE kind = 'work_depends_on'
  ),
  dangling_dep AS (
    SELECT d.dependent AS slug, d.antecedent
    FROM deps d
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = d.antecedent)
  ),
  bc_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_close
  ),
  bc_reach_dep(start_slug, cur) AS (
    SELECT dependent, antecedent FROM bc_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach_dep r JOIN bc_deps d ON d.dependent = r.cur
  ),
  dep_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bc_reach_dep WHERE cur = start_slug
  ),
  parents AS (
    SELECT child_slug AS slug, parent_slug, edge_row_id FROM :"schema".work_edge_parent
  ),
  dangling_parent AS (
    SELECT p.slug, p.parent_slug, p.edge_row_id
    FROM parents p
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = p.parent_slug)
  ),
  parent_anc(start_slug, cur, depth) AS (
    SELECT slug, parent_slug, 1 FROM parents
    UNION ALL
    SELECT pa.start_slug, p.parent_slug, pa.depth + 1
    FROM parent_anc pa JOIN parents p ON p.slug = pa.cur
    WHERE pa.depth < 10000
  ),
  parent_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM parent_anc WHERE cur = start_slug
  ),
  blocks_close_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent FROM :"schema".work_edge_blocks_close
  ),
  bc_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_close_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach r JOIN blocks_close_deps d ON d.dependent = r.cur
  ),
  blocks_close_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bc_reach WHERE cur = start_slug
  ),
  opened_current AS (
    SELECT work_slug AS slug FROM :"schema".ledger_current WHERE kind = 'work_opened'
  ),
  orphan_claims AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_claimed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_closes AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_closed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_deps AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_depends_on'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_children AS (
    SELECT e.edge_row_id AS id, e.child_slug AS slug, e.parent_slug
    FROM :"schema".work_edge_parent e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
    WHERE NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = e.parent_slug)
  ),
  composites AS (
    SELECT work_slug AS slug
    FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_discharge = 'composite'
  ),
  composite_hand_closed AS (
    SELECT c.slug, lc.id AS close_id
    FROM composites c
    JOIN :"schema".ledger_current lc ON lc.kind = 'work_closed' AND lc.work_slug = c.slug
  ),
  closed_but_tree_defeated AS (
    SELECT chc.slug, chc.close_id,
           (SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
              FROM :"schema".work_item_strict_blockers(chc.slug) b) AS blockers
    FROM composite_hand_closed chc
    WHERE EXISTS (SELECT 1 FROM :"schema".work_item_strict_blockers(chc.slug))
  ),
  -- s37 Element 1/3 -- raw_violations: every arm above, PLUS its target_id (the natural row id
  -- where one exists; the slug's own work_opened row id otherwise -- header DESIGN CHOICE).
  raw_violations AS (
    SELECT 'duplicate_open'::text AS violation, slug, NULL::text AS detail,
           (SELECT min(id) FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = dup_open.slug) AS target_id
    FROM dup_open
    UNION ALL
    SELECT 'shipped_without_witness', slug, 'ledger row ' || id, id FROM shipped_no_witness
    UNION ALL
    SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent, NULL::bigint FROM dangling_dep
    UNION ALL
    SELECT 'dependency_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = dep_cycle.slug) AS target_id
    FROM dep_cycle
    UNION ALL
    SELECT 'dangling_parent', slug, 'parent ' || parent_slug || ' has no opening act', edge_row_id
    FROM dangling_parent
    UNION ALL
    SELECT 'parent_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = parent_cycle.slug) AS target_id
    FROM parent_cycle
    UNION ALL
    SELECT 'blocks_close_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = blocks_close_cycle.slug) AS target_id
    FROM blocks_close_cycle
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_claimed row ' || id || ' cites a retracted opening act', id FROM orphan_claims
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_closed row ' || id || ' cites a retracted opening act', id FROM orphan_closes
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_depends_on row ' || id || ' cites a retracted opening act', id FROM orphan_deps
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving child work_opened row ' || id || ' names a retracted parent opening act (' || parent_slug || ')', id FROM orphan_children
    UNION ALL
    SELECT 'closed_but_tree_defeated', slug, 'close row ' || close_id || '; unresolved: ' || blockers, close_id FROM closed_but_tree_defeated
  ),
  -- s37 Element 3 (A4) -- dispositions IN FORCE, and whether each one's OWN checkable basis
  -- STILL holds, re-derived on every read (never a stored verdict):
  --   retired : holds while the target row's own acts still read settled. If the target is a
  --             work_opened row (the four slug-keyed arms + orphan_children), "settled" means its
  --             own slug currently reads 'closed' in work_item_current -- so a LATER-superseded
  --             close on that slug flips this back to false in the SAME read (A4's own example,
  --             verbatim). For every other kind of target row (claim/dep/close/edge row),
  --             "settled" is the row's own continued presence in ledger_current.
  --   reissued: holds while EITHER no successor was cited (nothing to invalidate -- element 4's
  --             own "warns, never refused" posture) OR the cited successor row is itself still
  --             in force (ledger_current).
  dispositions AS (
    SELECT lc.id AS disp_id, lc.work_violation_class AS class, lc.work_violation_target_id AS target_id,
           lc.work_resolution AS resolution, lc.work_violation_witness AS witness_id
    FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_violation_disposition'
  ),
  disposition_basis_holds AS (
    SELECT d.class, d.target_id
    FROM dispositions d
    JOIN :"schema".ledger_current t ON t.id = d.target_id
    WHERE
      (d.resolution = 'retired' AND (
         t.kind <> 'work_opened'
         OR EXISTS (SELECT 1 FROM :"schema".work_item_current wic
                    WHERE wic.slug = t.work_slug AND wic.state = 'closed')
      ))
      OR
      (d.resolution = 'reissued' AND (
         d.witness_id IS NULL
         OR EXISTS (SELECT 1 FROM :"schema".ledger_current w WHERE w.id = d.witness_id)
      ))
  )
SELECT rv.violation, rv.slug, rv.detail, rv.target_id
FROM   raw_violations rv
WHERE  NOT EXISTS (
         SELECT 1 FROM disposition_basis_holds dbh
         WHERE dbh.class = rv.violation AND dbh.target_id = rv.target_id
       );

COMMENT ON VIEW :"schema".work_item_violations IS
  'kernel/lineage/s37-violation-disposition.sql: every member now carries target_id, the key a
   work_violation_disposition answers it by. A member drops out only while an in-force
   disposition answers it AND that disposition''s own checkable basis still holds (validity-
   bounded, consult A4) -- see work_violation_history for the UNFILTERED read (every violation
   ever surfaced, with its disposition trail, thinner never).';

-- ============================================================================================
-- work_violation_history -- THE ONE NEW VIEW (spec element 1). Every violation ever surfaced
-- (raw_violations, UNFILTERED -- the SAME computation work_item_violations narrows FROM, not a
-- second derivation) LEFT JOINed to its full disposition trail (every disposition ever written
-- against that (class, target_id), in force or superseded, oldest first) -- "the record is never
-- thinner than today, only no longer miscounted as debt" (spec, verbatim).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_violation_history
    WITH (security_invoker = true) AS
WITH RECURSIVE
  opens AS (
    SELECT work_slug AS slug, count(*) AS n
    FROM :"schema".ledger WHERE kind = 'work_opened'
    GROUP BY work_slug
  ),
  dup_open AS (SELECT slug FROM opens WHERE n > 1),
  shipped_no_witness AS (
    SELECT work_slug AS slug, id
    FROM :"schema".ledger
    WHERE kind = 'work_closed' AND work_resolution = 'shipped'
      AND (work_witness IS NULL OR btrim(work_witness) = '')
  ),
  deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent
    FROM :"schema".ledger WHERE kind = 'work_depends_on'
  ),
  dangling_dep AS (
    SELECT d.dependent AS slug, d.antecedent FROM deps d
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = d.antecedent)
  ),
  bc_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_close
  ),
  bc_reach_dep(start_slug, cur) AS (
    SELECT dependent, antecedent FROM bc_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach_dep r JOIN bc_deps d ON d.dependent = r.cur
  ),
  dep_cycle AS (SELECT DISTINCT start_slug AS slug FROM bc_reach_dep WHERE cur = start_slug),
  parents AS (
    SELECT child_slug AS slug, parent_slug, edge_row_id FROM :"schema".work_edge_parent
  ),
  dangling_parent AS (
    SELECT p.slug, p.parent_slug, p.edge_row_id FROM parents p
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = p.parent_slug)
  ),
  parent_anc(start_slug, cur, depth) AS (
    SELECT slug, parent_slug, 1 FROM parents
    UNION ALL
    SELECT pa.start_slug, p.parent_slug, pa.depth + 1
    FROM parent_anc pa JOIN parents p ON p.slug = pa.cur
    WHERE pa.depth < 10000
  ),
  parent_cycle AS (SELECT DISTINCT start_slug AS slug FROM parent_anc WHERE cur = start_slug),
  blocks_close_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent FROM :"schema".work_edge_blocks_close
  ),
  bc_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_close_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach r JOIN blocks_close_deps d ON d.dependent = r.cur
  ),
  blocks_close_cycle AS (SELECT DISTINCT start_slug AS slug FROM bc_reach WHERE cur = start_slug),
  opened_current AS (
    SELECT work_slug AS slug FROM :"schema".ledger_current WHERE kind = 'work_opened'
  ),
  orphan_claims AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_claimed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_closes AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_closed'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_deps AS (
    SELECT lc.id, lc.work_slug AS slug FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_depends_on'
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_slug)
  ),
  orphan_children AS (
    SELECT e.edge_row_id AS id, e.child_slug AS slug, e.parent_slug
    FROM :"schema".work_edge_parent e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
    WHERE NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = e.parent_slug)
  ),
  composites AS (
    SELECT work_slug AS slug
    FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_discharge = 'composite'
  ),
  composite_hand_closed AS (
    SELECT c.slug, lc.id AS close_id
    FROM composites c
    JOIN :"schema".ledger_current lc ON lc.kind = 'work_closed' AND lc.work_slug = c.slug
  ),
  closed_but_tree_defeated AS (
    SELECT chc.slug, chc.close_id,
           (SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
              FROM :"schema".work_item_strict_blockers(chc.slug) b) AS blockers
    FROM composite_hand_closed chc
    WHERE EXISTS (SELECT 1 FROM :"schema".work_item_strict_blockers(chc.slug))
  ),
  raw_violations AS (
    SELECT 'duplicate_open'::text AS violation, slug, NULL::text AS detail,
           (SELECT min(id) FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = dup_open.slug) AS target_id
    FROM dup_open
    UNION ALL
    SELECT 'shipped_without_witness', slug, 'ledger row ' || id, id FROM shipped_no_witness
    UNION ALL
    SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent, NULL::bigint FROM dangling_dep
    UNION ALL
    SELECT 'dependency_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = dep_cycle.slug)
    FROM dep_cycle
    UNION ALL
    SELECT 'dangling_parent', slug, 'parent ' || parent_slug || ' has no opening act', edge_row_id
    FROM dangling_parent
    UNION ALL
    SELECT 'parent_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = parent_cycle.slug)
    FROM parent_cycle
    UNION ALL
    SELECT 'blocks_close_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = blocks_close_cycle.slug)
    FROM blocks_close_cycle
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_claimed row ' || id || ' cites a retracted opening act', id FROM orphan_claims
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_closed row ' || id || ' cites a retracted opening act', id FROM orphan_closes
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving work_depends_on row ' || id || ' cites a retracted opening act', id FROM orphan_deps
    UNION ALL
    SELECT 'orphaned_by_retraction', slug, 'surviving child work_opened row ' || id || ' names a retracted parent opening act (' || parent_slug || ')', id FROM orphan_children
    UNION ALL
    SELECT 'closed_but_tree_defeated', slug, 'close row ' || close_id || '; unresolved: ' || blockers, close_id FROM closed_but_tree_defeated
  )
SELECT rv.violation, rv.slug, rv.detail, rv.target_id,
       d.id AS disposition_id, d.work_resolution AS disposition_resolution,
       d.rationale AS disposition_basis, d.work_violation_witness AS disposition_witness,
       (d.id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = d.id)) AS disposition_in_force
FROM   raw_violations rv
LEFT JOIN :"schema".ledger d
       ON d.kind = 'work_violation_disposition'
      AND d.work_violation_class = rv.violation
      AND d.work_violation_target_id = rv.target_id
ORDER BY rv.violation, rv.slug, d.id;

COMMENT ON VIEW :"schema".work_violation_history IS
  'kernel/lineage/s37-violation-disposition.sql: UNFILTERED read -- every work_item_violations
   member ever surfaced (raw, never narrowed), LEFT JOINed to every disposition ever written
   against it (in force or superseded -- disposition_in_force names which). Never thinner than
   work_item_violations; the companion read for "what became of this defect, ever" (spec element
   1). Deliberately NOT current-truth-narrowed -- see gates/ledger_reader_allowlist.py''s
   classification of this view for the declared-history posture.';

GRANT SELECT ON :"schema".work_violation_history TO :"role";

-- ============================================================================================
-- work_review_gap (s29, re-issued s31/s32) RE-ISSUED (consult A5): a DEFERRED
-- work_violation_disposition carries the SAME item-keyed review obligation a deferred work_closed
-- already does -- "No new review mechanism; the existing column discipline extended to one new
-- kind" (spec element 1, verbatim). The pre-existing work_closed arm is UNCHANGED, byte-for-byte;
-- this adds a SECOND arm to the SAME UNION reading the new kind, `slug` resolved from the
-- disposition's OWN target row (every target row -- work_opened/work_claimed/work_depends_on/
-- work_closed -- carries a work_slug by s22's own two-way kind-shape, so this join never misses).
-- The discharge-side NOT EXISTS (discharging_attest) is UNCHANGED and applies uniformly to BOTH
-- arms via the outer wrapping query -- a review written against a disposition row discharges it
-- exactly the same way a review against a close row does (regards is kind-agnostic, s15).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_review_gap
    WITH (security_invoker = true) AS
SELECT c.slug, c.close_id, c.closer
FROM (
  SELECT work_slug AS slug, id AS close_id, actor AS closer
  FROM :"schema".ledger_current WHERE kind = 'work_closed' AND work_review_disposition = 'deferred'
  UNION ALL
  SELECT t.work_slug AS slug, d.id AS close_id, d.actor AS closer
  FROM :"schema".ledger_current d
  JOIN :"schema".ledger_current t ON t.id = d.work_violation_target_id
  WHERE d.kind = 'work_violation_disposition' AND d.work_review_disposition = 'deferred'
) c
WHERE NOT EXISTS (
  SELECT 1 FROM :"schema".discharging_attest da
  WHERE da.regards_id = c.close_id AND da.reviewer <> c.closer
);

-- ============================================================================================
-- GRANTS: work_item_violations/work_review_gap keep their EXISTING grants (an append-only
-- column-list change / additional UNION arm, s21's own additive-column-order idiom -- nothing to
-- re-grant); work_violation_history above.
-- ============================================================================================
