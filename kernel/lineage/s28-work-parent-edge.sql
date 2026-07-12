-- s28 WORK-PARENT EDGE -- a TYPED parent edge for work items (tracker slug work-tree-rollup,
-- design captured at ledger row 151, wave-3 dispatch decision at row 192). An ADDITIVE delta
-- applied ON TOP of the s15/s17/s17b/s19/s20/s21/s22/s23/s24/s25/s26 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second hand-copy of any existing mechanism (ADR-0012 P1: one home per mechanism). Numbering
-- coordinated with a sibling wave-3 delta, s27 (tail-deletion-witness, authored elsewhere): s27 is
-- NOT a prerequisite of this file and this file applies cleanly whether or not s27 has landed yet
-- (verified against the CHAIN this file's own PARAMETERIZATION section validates, s15 through s26
-- only -- s28 does not read or depend on any s27 object).
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): row 151's own framing, verbatim in substance -- task decomposition already forms a TREE
-- in the ledger (a child work item cites its parent), but today that citation is expressible ONLY
-- as free-text `--refs row:<id>` prose (led.tmpl's own header: "a bare reference uses refs").
-- Prose is not a fact a rollup can join on (ADR-0000 Rule 2(a): the fix is a TYPE, not a
-- convention leaned on and trusted to agree). This delta types the edge so `work-tree-rollup`'s
-- point (2) (a recursive rollup over real structure) and point (3) (the free split-time metric)
-- have something to join against that the kernel itself refuses to let go stale or dangling.
--
-- SLUG CHOSEN OVER ID (the commission's own instruction: "choose and justify"). The parent is
-- named by the ANTECEDENT'S SLUG (`work_parent text`, mirroring `work_depends_on`'s own choice of
-- antecedent-by-slug, s22), never by the antecedent's ledger row id, for three converging reasons:
--   1. SLUG IS ALREADY THIS LINEAGE'S IDENTITY PRIMITIVE for a work item (s22's own DENOMINATION
--      section: "the identity primitive is the SLUG ... never the ledger row id, which is
--      per-EVENT, not per-ITEM"). A parent edge names an ITEM, not an EVENT; the id of the
--      parent's OPENING ROW would be a per-event handle standing in for a per-item fact -- the
--      exact category error ADR-0012's `CellLedger` specimen (ADR-0000) warns against, one column
--      over.
--   2. THE ESTIMATE GRAMMAR ALREADY JOINS ON SLUG. design/USER-RETROSPECTIVE-RECIPE.md's
--      `estimate:` statement carries a bare `TASK-SLUG` field (no row-id field at all) as its own
--      join key -- ANY rollup that wants to line up a work item's parent edge against its
--      `estimate:` row needs the SAME key on both sides, or the join is a second, silently
--      drifting re-encoding of "which item is this" (ADR-0012 P1). Naming the parent by id would
--      force the rollup to translate id<->slug at the join boundary for no gain.
--   3. SIBLING PRECEDENT, KEPT CONSISTENT. `work_depends_on` (s22) already names its antecedent by
--      slug, not id, and is genuinely reachable with a dangling antecedent (deliberately unrefused
--      there). Naming THIS edge's antecedent by id while the sibling edge on the SAME table names
--      its antecedent by slug would be two different denominations for "an antecedent work item"
--      on two columns of one row -- an SSOT violation at the column-shape level. work_parent
--      follows work_depends_on's own choice for that reason alone, even setting aside points 1/2.
--
-- DANGLING PARENT: REFUSED, DELIBERATELY DIFFERENT FROM work_depends_on's OWN ANTECEDENT (the
-- commission's own instruction: "refuse-before-write on a dangling parent"). s22's
-- `work_depends_on` antecedent is deliberately LEFT unrefused (spec invariant 4 offered no refusal
-- option there, per s22's own header) -- but a work-item TREE is a stronger structural claim than
-- a bare dependency citation: the whole point of typing the edge is to hand a rollup a topology it
-- can walk without first auditing every row for a dangling reference, and every ROLLUP semantic
-- (subtree sums, split-time comparison) is silently wrong the moment one edge names a parent that
-- was never opened. ADR-0000 Rule 2(a): the loudest possible failure is at construction time, not
-- a tolerated-but-flagged row -- and the trigger layer already carries this shape for
-- `work_claimed`/`work_closed` (s22's own `validate_work_item`, unchanged), so extending the same
-- function to refuse a dangling PARENT too is the direct, minimal extension of an existing,
-- proven mechanism, not a new one.
--
-- CYCLES: REFUSED, AND WHY THIS IS PROVABLY VACUOUS UNDER NORMAL OPERATION (named, not silently
-- claimed reachable -- s22's own belt-and-braces precedent for `duplicate_open` and
-- `shipped_without_witness`, applied here to a THIRD member of that same class). `work_parent` is
-- captured ONLY at a slug's OWN opening act (work_title_kind_shape's sibling shape check below
-- makes work_parent legal only when kind='work_opened'), and a slug may be opened exactly ONCE
-- (validate_work_item's pre-existing duplicate-open refusal, s22, untouched here) -- so a parent
-- edge is written exactly once, at the moment its own item is born, and can NEVER be revised
-- afterward (append-only; there is no "reparent" kind). A cycle A->B->...->A would require some
-- node's parent edge to point at a slug that is, at THAT INSERT's moment, already an ANCESTOR of
-- the node being inserted -- but a genuinely new slug (this INSERT) has no rows naming it as
-- ANYONE's parent yet (nothing can cite an as-yet-unopened slug as its own parent, because the
-- referenced parent must already have an opening act -- the dangling-parent refusal above). So the
-- only way a cycle could ever form is if it existed BEFORE this row was inserted, which is
-- impossible by induction on insertion order (the empty ledger has no edges, hence no cycle; each
-- subsequent work_opened row can only extend the forest by attaching a NEW leaf under an EXISTING
-- node, never rewiring an existing edge) -- REACHABILITY: NONE, under ordinary INSERT, by this
-- structural argument, not by assertion. The cycle check below (`work_parent_would_cycle`,
-- consulted by the SAME trigger) is kept anyway, defense in depth, exactly as s22 keeps
-- `duplicate_open`'s own provably-vacuous trigger-level check as a second line: the function is a
-- REAL, independently callable, independently testable piece of logic (not a comment asserting
-- safety), so a future relaxation of "one opening act per slug, parent set once" (should one ever
-- be proposed) does not silently reopen the cycle class with no one watching. Scratch-witnessed
-- directly against the function in isolation (seen-red/s28-work-parent-edge/), the same technique
-- s26's own case h uses to test a closed collision in isolation without needing a reachable INSERT
-- path.
--
-- SELF-PARENT: the one sub-case of "cycle" cheap enough to foreclose at CONSTRUCTION TIME rather
-- than trigger time (ADR-0000 Rule 1: the strongest available surface) -- `work_parent_not_self`
-- below is a table CHECK, so `work_parent = work_slug` cannot exist even transiently, stronger
-- than relying on the trigger's cycle walk to catch it (which it also would, redundantly, at
-- depth 0 -- named, not hidden).
--
-- WHAT THIS DELTA DOES NOT DO (named per ADR-0013 Rule 4, filed rather than silently omitted):
--   - No "reparent" event kind. A work item's parent is fixed at its own opening act, forever
--     (append-only). Re-parenting an already-opened item is out of this delta's scope -- the
--     commission's own four design points name none of this, and inventing disposition-churn
--     machinery the spec never asked for is exactly the scope creep ADR-0004 forbids.
--   - No enforcement that a child's parent must be CLAIMED, or open, or anything about the
--     PARENT's own state -- only that it EXISTS (has an opening act). A closed or superseded
--     parent is a perfectly legal parent (a finished feature can still have had sub-tasks).
--   - No change to `work_depends_on`'s own semantics, refusal posture, or view. The two edges
--     (parent = tree structure; depends_on = a free dependency citation) are deliberately
--     DIFFERENT relations serving different questions, kept apart rather than merged into one
--     more-general-but-vaguer edge (ADR-0008: do not fuzzy-match two distinct facts into one).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: every work-item TREE fact is carried on the child's OWN `work_opened` row (the
--     `work_parent` column, naming the parent's slug), set exactly once, refused at construction
--     if the named parent has no opening act, and refused at construction if honoring it would
--     create a cycle (provably vacuous under normal operation, defended in depth per the header
--     above); the transitive closure of that edge (every ancestor/descendant pair, at every depth)
--     is a DERIVED view (`work_item_descendants`), never a second hand-maintained table.
--
--   - QUANTIFICATION UNIVERSE -- enumerated by re-reading every table and view the
--     s15+...+s26 chain exposes to :role, re-verifying s26's own enumeration and checking it
--     against the one new column:
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table (mirrors s22's own
--         invariant 1: work-item facts ride the existing `ledger` row).
--       VIEWS re-read for the wildcard-and-staleness class s20/s22/s23/s24/s26 all named:
--         * ledger_current / countersigned_in_force -- explicit column lists (s20+). GAIN
--           `work_parent`, APPENDED AT THE END, HERE, else the column-complete class recurs one
--           column later (the s20 lesson, re-applied again).
--         * review_gap / question_status / review_stamp_distinctness -- re-verified NOT members,
--           for the identical reasons s22/s24/s26 each already gave (no general ledger-row column
--           passthrough a work-tree fact belongs on).
--         * work_item_current -- s22's own view, explicit column list. GAINS `parent_slug`
--           (sourced from the SAME `opened` CTE that already carries `work_slug`/`work_title`,
--           since `work_parent` -- like `work_title` -- is captured only on the opening row).
--         * work_item_violations -- s22's own view. GAINS two members, `dangling_parent` and
--           `parent_cycle`, both PROVABLY VACUOUS under normal operation for the identical reason
--           `duplicate_open`/`shipped_without_witness` already are (both refused at construction
--           above) -- belt-and-braces, named as such, not claimed reachable.
--         * work_item_descendants -- NEW view, the transitive closure of the parent edge
--           (ancestor_slug, descendant_slug, depth), `WITH RECURSIVE`, depth-bounded (see LIMITS)
--           as defense against ever looping should the cycle refusal somehow be bypassed
--           (a schema-owner with DDL privilege, s26's own disclosed limit, applies here too).
--     So the "column-complete" class has THREE members this delta must re-issue (all three done
--     here: ledger_current, countersigned_in_force, work_item_current); the rest are checked and
--     confirmed NOT members, named rather than silently skipped.
--     KIND VOCABULARY -- unchanged. This delta adds no new `kind` value (unlike s22, which minted
--       four); a parent edge is carried entirely on the EXISTING `work_opened` kind's own row, one
--       more optional column beside `work_title`.
--     GRANTS -- mirrors s22's own posture: the ONE new view (`work_item_descendants`) gets a fresh
--       GRANT SELECT; `work_parent` rides the already-granted `ledger` table (INSERT+SELECT since
--       s15), so no table-level grant change is needed for it.
--     ENGINE -- NONE shipped in this delta (mirrors s23/s25/s26's own "ENGINE -- NONE"
--       disclosure): `engine/lp/work_items.lp` (s22's own ASP companion) is NOT extended here --
--       the rollup arithmetic (point 2/3 of the commission) is a PULL read surface
--       (`bootstrap/templates/pickup.tmpl`'s new ROLLUP section), not a T_now derivation, so it has
--       no ASP counterpart to keep in step; `./judge`'s existing SQL/ASP differential is UNAFFECTED
--       by this delta (it derives T_now facts from kind/status/supersedes/etc., none of which this
--       delta touches) and continues to AGREE -- scratch-witnessed as part of this delta's own
--       acceptance (see seen-red/s28-work-parent-edge/).
--
--   - DENOMINATION: `work_parent` is `text` (a slug, matching `work_slug`/`work_depends_on`'s own
--     denomination -- s22's DENOMINATION section, re-applied, not re-argued). The two new
--     `work_item_violations` members are denominated identically to their siblings: `slug` (the
--     child's own slug) + a free-text `detail` naming the parent slug involved, same shape as
--     `depends_on_unknown_slug`/`dependency_cycle` already use.
--
-- SMALLEST-HONEST-SURFACE CHOICE FOR THE ROLLUP (commission point 2: "a WITH RECURSIVE derived
-- view (or led/pickup read surface -- smallest honest surface, justify)"). This delta ships ONLY
-- the topology (`work_item_descendants`, below) in SQL. The ARITHMETIC -- joining that topology
-- against `estimate:`-prefixed decision statements and summing their fields -- is deliberately
-- NOT reimplemented in PL/pgSQL here: `estimate:`'s six-field grammar already has exactly ONE
-- documented home (design/USER-RETROSPECTIVE-RECIPE.md's "Estimate statement grammar" section) and
-- exactly two readers, `led.tmpl`'s intake validator and `pickup.tmpl`'s `estimates()` display --
-- both Python. Re-deriving that same parse in SQL would be a THIRD, independently-drifting
-- re-implementation of one grammar (ADR-0012 P7's "two writers of one truth", here two LANGUAGES
-- of one truth) for no structural gain, since the topology this delta's view exposes is exactly
-- what a Python reader needs to walk the tree itself. The kernel therefore owns the STRUCTURE
-- (this file); `bootstrap/templates/pickup.tmpl`'s new ROLLUP section owns the SEMANTICS of an
-- estimate, reusing its own existing field-parsing code rather than a hand-copy of it.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta ONLY adds a column
-- (`work_parent`, nullable, legal only on `work_opened` rows), a construction-time CHECK
-- (no-self-parent), a trigger EXTENSION on the SAME pre-existing `validate_work_item` function
-- (refuse dangling parent / refuse cycle -- both are NEW refusals, no existing refusal loosened),
-- one new helper function (`work_parent_would_cycle`, read-only, called only by the trigger), one
-- new view (`work_item_descendants`), and re-issues of two "column-complete" views to append the
-- new column -- nothing existing is relaxed, no existing refusal loosened, no existing semantics
-- changed (a `work_opened` row with no `--parent` behaves byte-for-byte as it did before this
-- delta; `work_depends_on`'s own posture is untouched). Class-ratified per the maintainer's
-- 2026-07-09 ruling once scratch-witnessed both polarities (valid parent accepted; dangling parent
-- refused; cycle refused) with the SQL/ASP differential in AGREE -- all done, this same commission
-- (see seen-red/s28-work-parent-edge/) -- it enters the birth chain without a per-delta maintainer
-- question. Wiring it INTO `bootstrap/new-project.sh`'s own `LINEAGE_CHAIN` (so it actually ships
-- in the NEXT scaffolded world) is left to the wave-3 orchestrator's seam-integration pass (row
-- 192: "orchestrator lands at seam"), not taken here, to avoid two concurrent worktree builders
-- (this delta and its sibling s27) racing edits to the SAME shared script.
--
-- LIMITS (pre-registered, matching s22/s26's own disclosure convention):
--   - The cycle refusal (and the dangling-parent refusal) binds ONLY the granted `:role`'s
--     ordinary INSERT path, exactly like every other trigger-enforced refusal in this lineage --
--     a schema-owner/superuser with DDL privilege can `DROP TRIGGER validate_work_item` (or
--     disable it) and write an inconsistent tree directly, the same disclosed bound s26's own
--     LIMITS section already names for the row-hash chain. `work_item_descendants`'s depth cap
--     (10000) is this delta's own answer to that SAME bound applied to a NEW hazard: an
--     adversarially- or accidentally-bypassed cycle would otherwise make the recursive view loop
--     without termination -- the cap turns "hangs forever" into "returns an honestly-truncated
--     result", never a resource-exhaustion incident.
--   - `work_item_violations`'s two new members (`dangling_parent`, `parent_cycle`) are, like
--     `duplicate_open`/`shipped_without_witness` before them, PROVABLY VACUOUS reads under normal
--     operation (both refused at construction) -- they exist for defense in depth and for the
--     bypassed-trigger scenario above, not as a live detector under ordinary use.
--   - No claim is made about `work_depends_on`'s own dangling-antecedent or cycle behavior --
--     that edge is untouched by this delta and keeps its s22-given, deliberately-unrefused
--     posture.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s20/s22/s23/s24/s25/s26):
-- schema/kern/role are psql variables so this delta is VALIDATED on a throwaway substrate before
-- any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s28val -v kern=s28val_kernel -v role=s28val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a
--   FUTURE world's birth chain, wired by the wave-3 orchestrator's seam-integration pass into
--   `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` (not taken here -- see FAIL-SAFE CLASSIFICATION
--   above). It was authored and scratch-witnessed on scratch schema pairs in the TOY db only --
--   NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP+ADD CONSTRAINT;
-- CREATE OR REPLACE + DROP/CREATE TRIGGER/FUNCTION/VIEW).

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
-- THE ONE NEW COLUMN (SSOT: work-tree structure rides the child's OWN opening row, exactly as
-- work_title/work_depends_on already do -- no new base table).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_parent text;

COMMENT ON COLUMN :"schema".ledger.work_parent IS
  'Work-tree parent edge (kernel/lineage/s28-work-parent-edge.sql): the PARENT''s slug, carried
   ONLY on the child''s own work_opened row (work_parent_kind_shape below), set exactly once (the
   opening act is unique per slug, s22) and never revised. NULL means "no parent -- a root item".
   Refused at construction if the named parent has no opening act, or if honoring it would create
   a cycle (validate_work_item, extended here) -- deliberately DIFFERENT from work_depends_on''s
   own antecedent, which is left unrefused by design (s22). Denominated by SLUG, not row id --
   see this file''s header for why (the estimate: grammar''s own join key is a slug).';

-- ============================================================================================
-- SHAPE INVARIANT (illegal states unrepresentable AT CONSTRUCTION, ADR-0000 Rule 1): work_parent
-- is legal ONLY on a work_opened row (one-way, unlike work_slug_kind_shape's two-way correlation --
-- a root item legitimately has kind='work_opened' with work_parent NULL, so this is NOT an iff).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_parent_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_parent_kind_shape CHECK (
    work_parent IS NULL OR kind = 'work_opened');

-- self-parent: foreclosed at CONSTRUCTION TIME (stronger than the trigger's own cycle walk, which
-- would also catch this redundantly at depth 0 -- named, not hidden, see header). NOTE THE ONE
-- REAL BUG THIS DELTA HAD AND FIXED BEFORE SHIPPING (named per this project's own house
-- convention of disclosing a closed defect rather than silently correcting it, s26's own
-- INJECTIVITY note is the precedent): a first draft wrote this as a bare
-- `work_parent IS DISTINCT FROM work_slug`, which is WRONG for every ORDINARY ledger row where
-- BOTH columns are NULL (a decision/finding/etc. row) -- SQL's `NULL IS DISTINCT FROM NULL`
-- evaluates to FALSE (two NULLs are "not distinct"), so that bare form made EVERY non-work-item
-- row in the whole ledger fail this CHECK, a severe regression caught by this delta's own
-- scratch-witness run (seen-red/s28-work-parent-edge/) before it shipped, not discovered later.
-- The corrected form below is guarded: when work_parent IS NULL (every ordinary row, and every
-- root work item), the first disjunct makes the whole CHECK true unconditionally; the
-- IS DISTINCT FROM comparison only ever runs when work_parent IS NOT NULL, at which point
-- work_slug is also guaranteed NOT NULL (work_slug_kind_shape, s22), so the comparison is a plain
-- non-NULL inequality, exactly the self-parent refusal intended.
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_parent_not_self;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_parent_not_self CHECK (
    work_parent IS NULL OR work_parent IS DISTINCT FROM work_slug);

-- ============================================================================================
-- work_parent_would_cycle() -- the ONE home of "would honoring this parent edge create a cycle"
-- (ADR-0012 P1). Walks candidate_parent's OWN ancestor chain (via work_parent, following each
-- ancestor's own opening row); returns true iff candidate_child appears anywhere in that chain
-- (including candidate_parent itself, depth 0 -- redundant with work_parent_not_self above for the
-- self-parent case, intentionally, belt-and-braces). Depth-capped (10000) so a hypothetically
-- bypassed-trigger cycle in the data cannot make this loop forever -- the header's own LIMITS
-- section names why this cap exists. LANGUAGE sql STABLE: a pure read of ledger's current state,
-- no side effects, safe to call from the trigger below.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_parent_would_cycle(candidate_parent text, candidate_child text)
    RETURNS boolean LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE anc(slug, depth) AS (
    SELECT candidate_parent, 0
    UNION ALL
    SELECT o.work_parent, a.depth + 1
    FROM anc a
    JOIN ledger o ON o.kind = 'work_opened' AND o.work_slug = a.slug
    WHERE o.work_parent IS NOT NULL AND a.depth < 10000
  )
  SELECT EXISTS (SELECT 1 FROM anc WHERE slug = candidate_child);
$fn$;

-- ============================================================================================
-- validate_work_item() EXTENDED (the SAME function s22 defined -- CREATE OR REPLACE, not a
-- second copy; ADR-0012 P1). New: for kind='work_opened' with a non-NULL work_parent, refuse a
-- dangling parent (no opening act on record) and refuse a cycle (work_parent_would_cycle). Every
-- pre-existing branch (duplicate-open refusal; the work_claimed/work_depends_on/work_closed
-- unopened-slug refusal) is UNCHANGED, byte-for-byte, below.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
BEGIN
  IF NEW.kind = 'work_opened' THEN
    IF EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' already has an opening act — one opening act per slug (the Q5 defect: a decomposition ledgered twice under the same identity is refused, never silently duplicated).', NEW.work_slug;
    END IF;
    IF NEW.work_parent IS NOT NULL THEN
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_parent) THEN
        RAISE EXCEPTION 'Ledger policy: work item slug ''%'' names parent ''%'' which has no opening act — a --parent must reference an ALREADY-OPENED work item slug (dangling parents are refused here, unlike work_depends_on''s antecedent, which the spec deliberately leaves unrefused, s22). Open the parent first: ./led work open % "<title>", then retry this open with --parent %.', NEW.work_slug, NEW.work_parent, NEW.work_parent, NEW.work_parent;
      ELSIF work_parent_would_cycle(NEW.work_parent, NEW.work_slug) THEN
        RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot be parented to ''%'' — ''%'' is already an ancestor of ''%'' in the work-tree, so this edge would create a cycle. Refused at construction, never a tolerated-but-flagged row (see work_item_violations.parent_cycle for the defense-in-depth read).', NEW.work_slug, NEW.work_parent, NEW.work_slug, NEW.work_parent;
      END IF;
    END IF;
  ELSIF NEW.kind IN ('work_claimed','work_depends_on','work_closed') THEN
    IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' has no opening act — every later event on an item must reference an item that has been opened (invariant 2, item identity).', NEW.work_slug;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
-- The trigger definition itself (name, timing, table) is UNCHANGED -- CREATE OR REPLACE FUNCTION
-- above is sufficient; re-issuing DROP/CREATE TRIGGER is harmless idempotence, kept for symmetry
-- with s22's own script shape.
DROP TRIGGER IF EXISTS validate_work_item ON :"schema".ledger;
CREATE TRIGGER validate_work_item BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_work_item();

-- ============================================================================================
-- s20/s22/s23/s24/s26 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN
-- work_parent, APPENDED AT THE END. Explicit column lists throughout -- never `l.*`. Column list =
-- s26's exact list + l.work_parent.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));

-- ============================================================================================
-- work_item_current (s22) GAINS parent_slug, sourced from the SAME `opened` CTE that already
-- carries work_slug/work_title (work_parent, like work_title, lives only on the opening row).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_current
    WITH (security_invoker = true) AS
WITH opened AS (
  SELECT work_slug AS slug, work_title AS title, work_parent AS parent_slug, id AS opened_id
  FROM :"schema".ledger WHERE kind = 'work_opened'
),
claimed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, actor AS claimant, id AS claimed_id
  FROM :"schema".ledger WHERE kind = 'work_claimed'
  ORDER BY work_slug, id DESC
),
closed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, work_resolution AS resolution,
         work_witness AS witness, id AS closed_id
  FROM :"schema".ledger WHERE kind = 'work_closed'
  ORDER BY work_slug, id DESC
)
SELECT o.slug, o.title,
       CASE WHEN c.slug IS NULL THEN 'open' ELSE 'closed' END AS state,
       c.resolution, c.witness, cl.claimant, o.parent_slug
FROM   opened o
LEFT JOIN claimed cl ON cl.slug = o.slug
LEFT JOIN closed  c  ON c.slug  = o.slug;

-- ============================================================================================
-- work_item_violations (s22) GAINS two members, dangling_parent and parent_cycle -- both PROVABLY
-- VACUOUS under normal operation (both refused at construction above), belt-and-braces, matching
-- duplicate_open/shipped_without_witness's own existing precedent in this same view. `parent_anc`
-- below is a SEPARATE recursive member for the PARENT edge (Postgres requires exactly one `WITH
-- RECURSIVE` header covering every CTE in the query when any one is recursive, and the two edges,
-- parent vs depends_on, are deliberately different relations -- header's own "WHAT THIS DELTA
-- DOES NOT DO"); the pre-existing `reach` member (work_depends_on's own cycle detector) is
-- UNTOUCHED.
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
  reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM deps
    UNION
    SELECT r.start_slug, d.antecedent FROM reach r JOIN deps d ON d.dependent = r.cur
  ),
  dep_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM reach WHERE cur = start_slug
  ),
  parents AS (
    SELECT work_slug AS slug, work_parent AS parent_slug
    FROM :"schema".ledger WHERE kind = 'work_opened' AND work_parent IS NOT NULL
  ),
  dangling_parent AS (
    SELECT p.slug, p.parent_slug
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
  )
SELECT 'duplicate_open'::text AS violation, slug, NULL::text AS detail FROM dup_open
UNION ALL
SELECT 'shipped_without_witness', slug, 'ledger row ' || id FROM shipped_no_witness
UNION ALL
SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent FROM dangling_dep
UNION ALL
SELECT 'dependency_cycle', slug, NULL FROM dep_cycle
UNION ALL
SELECT 'dangling_parent', slug, 'parent ' || parent_slug || ' has no opening act' FROM dangling_parent
UNION ALL
SELECT 'parent_cycle', slug, NULL FROM parent_cycle;

-- ============================================================================================
-- work_item_descendants -- NEW view (commission point 2's typed-edge topology). The transitive
-- closure of the parent edge: every (ancestor_slug, descendant_slug, depth>=1) pair reachable by
-- following child->parent edges upward from descendant_slug to ancestor_slug. Depth-capped
-- (10000, matching work_parent_would_cycle's own cap) purely as defense against a
-- bypassed-trigger cycle looping this view forever (see LIMITS in the header) -- under normal
-- operation the cap is never approached (the trigger already refuses a cycle at construction).
-- `pickup.tmpl`'s new ROLLUP section reads THIS view for topology and joins it, in Python, against
-- `estimate:`-prefixed decision rows (see header's SMALLEST-HONEST-SURFACE note for why the join
-- itself lives there and not here).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_descendants
    WITH (security_invoker = true) AS
WITH RECURSIVE tree(ancestor_slug, descendant_slug, depth) AS (
  SELECT w.slug, w.slug, 0
  FROM :"schema".work_item_current w
  UNION ALL
  SELECT t.ancestor_slug, c.slug, t.depth + 1
  FROM tree t
  JOIN :"schema".work_item_current c ON c.parent_slug = t.descendant_slug
  WHERE t.depth < 10000
)
SELECT ancestor_slug, descendant_slug, depth FROM tree WHERE depth > 0;

-- ============================================================================================
-- GRANTS (mirrors s22's own posture: append-only is inherited from the ledger itself -- no new
-- mutable surface exists to guard). ONE new view gets a fresh GRANT.
-- ============================================================================================
GRANT SELECT ON :"schema".work_item_descendants TO :"role";
