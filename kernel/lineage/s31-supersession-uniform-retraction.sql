-- s31 SUPERSESSION = UNIFORM RETRACTION (design/FABLE-SUPERSESSION-UNIFORM-RETRACTION-SPEC.md,
-- HISTORY: safe -- re-issues readers only (views + trigger text; the one new violations member
-- is a derived read); no backfill, no UPDATE, no new column; every pre-existing row's bytes and
-- every history reader's output are untouched (byte-identity witnessed in this delta's own
-- seen-red fixture: hash chain recomputes clean across retracted rows, led --recent unchanged).
-- Fable-authored spec, RATIFIED 2026-07-15 (maintainer yes) -- ledger item
-- `supersession-semantics-closure`). This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING
-- it to any live/existing world is the maintainer's act at a FUTURE world's birth
-- (runs-are-strictly-linear ruling, 2026-07-11), never taken here. An ADDITIVE delta applied ON
-- TOP of the s15..s30 kernel (the established remediation-delta idiom), NOT a retro-edit of a
-- frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of any existing mechanism
-- (ADR-0012 P1: one home per mechanism).
--
-- PREREQUISITE: this delta REQUIRES s30 (kernel/lineage/s30-typed-dependency-edges.sql) applied
-- first -- it re-issues work_item_strict_blockers(), an s29-defined/s30-extended function, and
-- reads edge_type (an s30 column) inside that re-issue; it also re-issues validate_work_item()
-- carrying s29/s30's own branches. Applying this file on a pre-s30 kernel fails loudly at CREATE
-- OR REPLACE VIEW/FUNCTION time (undefined column edge_type), the correct, disclosed failure mode
-- for a hard dependency, matching s29/s30's own PREREQUISITE precedent.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): the ratified spec's sec-2 finding. Four current-truth readers -- work_item_current's
-- opened/claimed/closed CTEs, work_item_strict_blockers()'s edges/closes CTEs, question_status's
-- question-row side, work_review_gap's close-row side -- were built reading RAW `ledger` instead
-- of the kernel's one existing home of "the un-superseded reading" (`ledger_current`, s15+), each
-- quantifying over raw history on its own judgment. The first cell of this class surfaced in
-- design/FABLE-COMPOSITE-DISCHARGE-SPEC.md sec-3b (a defeated work_closed row still reading
-- closed); a spot-fix of that one CTE was withdrawn on the maintainer's ADR-0000 2(a) challenge
-- (patchwork -- one cell of an unenumerated matrix), and the WHOLE class routed here. THE
-- SEMANTICS (spec sec-1, the whole spec in one line): superseding a row of ANY kind means exactly
-- one thing -- the event is retracted from current truth, reinstatement-free; no kind carries its
-- own defeat semantics, because current state is a pure fold over in-force events only.
--
-- THE TWO RATIFIED FORKS (spec sec-3, both maintainer-decided 2026-07-15, restated for a
-- zero-context reader of THIS file):
--   1. UNIFORM RETRACTION over refuse-on-work-kinds: the write side gains NO kind-compatibility
--      refusal on `supersedes` (under uniform retraction every target is meaningful); the
--      pre-existing FK (supersedes -> ledger.id) stays the one write constraint, unchanged.
--   2. SLUG BURNED over slug re-openable: duplicate_open -- BOTH homes, the trigger's refusal AND
--      the violations view's member -- keeps its RAW/history reading, byte-identical: a retracted
--      work_opened permanently burns its slug (s28's cycle-impossibility induction PROVES its own
--      vacuity from "a slug is opened exactly once, parent fixed at birth"; a re-openable slug
--      would silently reopen that proof's hole, and slug identity -- the lineage's identity
--      primitive, s22 -- would fork from history). This delta touches the duplicate-open
--      EXCEPTION TEXT ONLY (naming the new-slug-citing-old redo idiom, led.tmpl's own
--      pre-existing `--refs row:<id>` convention), never its query or condition.
--
-- THE READER TYPE (spec sec-2): every ledger reader is exactly one of two DECLARED types --
-- CURRENT-TRUTH (factors through ledger_current / in_force) or HISTORY/FORENSIC (reads raw
-- `ledger`, named on a closed allowlist with its reason). This delta re-issues the four known
-- misfactored current-truth readers to factor through `ledger_current` (the ONE factoring, never
-- a fifth inline `NOT EXISTS (supersedes)` copy -- the ADR-0012 P1 two-writers drift the spec
-- names), adds ONE new derived violations member, and leaves every declared history reader
-- byte-identical. The allowlist gate (gates/ledger_reader_allowlist.py, shipped with this delta)
-- is the standing mechanical detect that keeps the reader universe closed hereafter (ADR-0011
-- Rule 4: the net quantifies over the CLASS -- the next reader -- not today's cells).
--
-- ELEMENT 1 -- work_item_current RE-ISSUED. The opened/claimed/closed CTEs read `ledger_current`.
-- Consequences, uniform and derived, never hand-coded per kind: a retracted close empties the
-- `closed` CTE for that slug -> the item reads OPEN again; a retracted claim -> UNCLAIMED; a
-- retracted open -> the item leaves this view entirely (surviving children surface via Element
-- 5). REINSTATEMENT-FREE COSTS NO NEW LOGIC: `ledger_current` excludes row R iff SOME row's
-- `supersedes` names R -- superseding the SUPERSEDER does not un-name the original target, so the
-- victim stays retracted regardless of its retractor's own later fate. Witnessed, not asserted
-- (acceptance case e).
--
-- ELEMENT 2 -- work_item_strict_blockers() RE-ISSUED. The `edges` CTE (both the s28 work_parent
-- arm and the s30 blocks-close arm) and the `closes` CTE read `ledger_current`. The
-- discharge-review subquery inside `review_unresolved` is UNCHANGED, BYTE-FOR-BYTE -- it was
-- already a correctly-scoped in-force read (spec sec-2: "the discharge-review side is already
-- filtered"). A retracted blocks-close edge drops out of `edges` -> a formerly-blocked strict
-- close succeeds; the edge's retraction stays visible in history reads.
--
-- ELEMENT 3 -- question_status RE-ISSUED. The question-row side reads `ledger_current` -- a
-- retracted question row no longer surfaces at all. The per-answer in-force filters (inside
-- `answered`/`first_answer_id`) are UNCHANGED -- already correctly factored (a per-candidate
-- anti-join scoped to the answering row itself); only the question row's OWN currentness was the
-- gap.
--
-- ELEMENT 4 -- work_review_gap RE-ISSUED. The close-row subquery reads `ledger_current` -- a
-- retracted deferred-close stops being an open review obligation (the item itself re-opened via
-- Element 1; a gap row for a close that no longer exists would be a stale artifact). The outer
-- discharge-review NOT EXISTS is UNCHANGED, byte-for-byte (same already-filtered reasoning as
-- Element 2).
--
-- ELEMENT 5 -- work_item_violations GAINS `orphaned_by_retraction` (spec sec-1: "a retracted open
-- retracts the item, and its surviving child events become a NEW derived violations member ...
-- surfaced, never silently tolerated"). Four sub-cases, one per event shape that can cite an item
-- without BEING its opening act: a surviving (in-force) work_claimed / work_closed /
-- work_depends_on row whose own slug's opening act is retracted, and a surviving CHILD
-- work_opened row (s28) whose work_parent names a slug whose opening act is retracted. All four
-- read `ledger_current` (the same one factoring, reused not re-derived). Every PRE-EXISTING
-- member of this view is UNCHANGED, byte-for-byte -- all seven are declared history /
-- defense-in-depth reads (see CLOSURE STATEMENT).
--
-- ELEMENT 6 -- validate_work_item() RE-ISSUED: DUPLICATE-OPEN EXCEPTION TEXT ONLY. The refusal's
-- condition (EXISTS over raw `ledger` -- retraction-blind, on purpose, slug-burned) is
-- byte-identical to s22's original; the MESSAGE gains two sentences naming the uniform-retraction
-- ruling and the redo idiom (open a NEW slug citing the old row via --refs row:<id>). Every other
-- branch (dangling/cycling parent, unopened slug, s30 edge_type default+refusals, s29 epoch-gated
-- disposition + strict close) is UNCHANGED, byte-for-byte.
--
-- WHAT THIS DELTA DELIBERATELY DOES NOT DO (ADR-0013 Rule 4, filed not buried):
--   - NO kind-compatibility refusal on supersedes writes (ratified fork 1).
--   - NO change to duplicate_open's raw/history QUERY in either home (trigger or view) -- text
--     only, Element 6.
--   - NO change to depends_on_unknown_slug / dependency_cycle / dangling_parent / parent_cycle /
--     blocks_close_cycle / shipped_without_witness: all answer structural-existence questions
--     over the graph's raw history ("did this shape ever get written"), not current-truth
--     questions -- declared history/defense-in-depth reads, re-verified NOT members.
--   - NO composite-discharge mechanism (design/FABLE-COMPOSITE-DISCHARGE-SPEC.md is itself still
--     DRAFT, unratified, unbuilt -- no work_discharge/effective_state column exists in this
--     kernel). The spec's acceptance clause "a discharged composite ancestor re-opens in the same
--     read" describes how that FUTURE mechanism inherits this fix once it lands (its own sec-3b
--     text); it is UNEXERCISABLE today and this delta's acceptance evidence marks it UNEXERCISED
--     with exactly this blocker, never silently claimed.
--   - NO change to the row-hash chain, led --recent, or any other declared history reader.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: "in force" has ONE home per producer (SQL: `ledger_current`; ASP:
--     ledger_tnow.lp's `superseded/1`/`in_force/1`); every CURRENT-TRUTH reader is a function of
--     the in-force subledger only, factored through that one home -- never an independent inline
--     anti-join; every raw-`ledger` reader is a DECLARED history reader on the closed allowlist
--     below, with its reason; and supersession has NO per-kind meaning -- every kind's retraction
--     is the same fold-removal, reinstatement-free.
--
--   - QUANTIFICATION UNIVERSE -- the spec's 2026-07-15 mechanical enumeration (every live
--     view/function across kernel/lineage s10->s30 with the write-side FK-only finding and the
--     pickup/led/stop-hook/judge-floor/engine-lp reader sweep), re-verified here against the
--     s15..s30 chain this delta applies on top of, and kept closed HEREAFTER by the allowlist
--     gate (gates/ledger_reader_allowlist.py), not by re-running the enumeration by hand:
--       CURRENT-TRUTH READERS RE-ISSUED (5, all in this file): work_item_current;
--         work_item_strict_blockers(); question_status; work_review_gap; work_item_violations
--         (its NEW orphaned_by_retraction member only).
--       CURRENT-TRUTH READERS ALREADY CORRECTLY FACTORED (re-verified, untouched):
--         ledger_current / countersigned_in_force (the projection home itself -- cannot factor
--         through itself; its inline anti-join IS the one authoritative encoding); review_gap
--         (s15 -- actor-keyed, both its ledger reads carry their own row-scoped in-force
--         anti-joins, correct since s15, outside this delta's four named members); the per-answer
--         legs of question_status and the discharge-review legs of work_item_strict_blockers()/
--         work_review_gap (unchanged, Elements 2/3/4).
--       DECLARED HISTORY/FORENSIC READERS (unchanged, each named with its reason -- spec sec-2's
--         allowlist, carried here as this delta's own record):
--         * zz_set_row_hash() + chain verification (s26/s27): every row must chain, superseded or
--           not -- a retraction is itself a ledger fact that hashes like any other row.
--         * led --recent (bootstrap/templates/led.tmpl): displays AND MARKS superseded rows,
--           never hides them -- a declared history display by design.
--         * work_item_violations.duplicate_open + validate_work_item()'s duplicate-open branch:
--           slug burned (ratified fork 2).
--         * work_item_violations.shipped_without_witness: provably-vacuous defense-in-depth read
--           of raw history ("did a malformed row ever land"), s22's own belt-and-braces posture.
--         * work_item_violations.depends_on_unknown_slug / dependency_cycle / dangling_parent /
--           parent_cycle / blocks_close_cycle: structural-existence questions over raw history.
--         * validate_work_item()'s write-boundary existence checks (has this slug EVER been
--           opened; would this edge cycle against history): a BEFORE INSERT trigger cannot read a
--           view excluding the row being inserted, and identity/cycle checks are deliberately
--           history-typed (spec sec-2's trigger clause + fork 2).
--         * validate_independence() (s17/s21/s29): reads (stamp_session, stamp_agent) off the two
--           named rows directly -- row-addressed forensics, not a truth projection.
--       VIEWS RE-VERIFIED NOT MEMBERS: work_item_descendants (s28 -- reads work_item_current, so
--         it INHERITS Element 1's in-force reading with zero edits here: a retracted open drops
--         the item from work_item_current and therefore from the closure -- named as inherited,
--         not silently skipped); ledger_current / countersigned_in_force (no new column -- the
--         s20 "column-complete" class has ZERO members this time: this delta adds no column).
--       TABLES: unchanged -- no new base table, no new column (a pure re-issue of view/function
--         bodies plus one exception-text edit).
--       KIND VOCABULARY: unchanged.
--       GRANTS: unchanged -- no new view/column; CREATE OR REPLACE with identical column
--         lists/signatures preserves every existing grant (s21's idiom, trivially satisfied).
--       ENGINE -- engine/lp/work_items.lp and engine/lp/work_review.lp COMPOSE with
--         ledger_tnow.lp's supersession closure (`superseded/1`): work_review.lp's tree/close
--         reads and work_items.lp's NEW work_orphaned_by_retraction judgment consume in-force
--         work events only, via row-id-carrying EDB families filtered by `not superseded(R)` --
--         mirroring Elements 1/2/5. Their headers' "never whole-row superseded by design" premise
--         is SUPERSEDED by the ratified spec and both files now say so, citing it.
--         engine/ledger_floor.py's work_item_floor_atoms()/work_review_floor_atoms() are updated
--         to match byte-for-byte (reading ledger_current exactly where the SQL DDL twins do).
--         STANDING ./judge WIRING -- assessed, NOT half-wired: engine/ledger_edb.py's export()
--         (the EDB both standing producers consume) carries NO work_* fact family today
--         (verified: entry/supersedes/enacts/amends/answers only), and ledger_differential.py's
--         run_asp/run_sql pipeline is single-program-typed (TNOW_LP hardcoded, floor_atoms only)
--         -- wiring the work layer into the standing differential requires a new EDB fact-family
--         export plus a per-layer differential pass, a genuinely separate seam. UNEXERCISED with
--         that concrete blocker (mirrors s22/s29/s30's own verified, identical finding: judge
--         does not auto-discover engine/lp/*.lp; every non-core .lp keeps a bespoke
--         scratch-differential). This delta's own acceptance (seen-red/s31-supersession-uniform-
--         retraction/run_fixtures.py) runs that bespoke differential -- ledger_tnow.lp +
--         work_items.lp + work_review.lp composed over ONE shared EDB vs the SQL floor -- and
--         asserts AGREE on a world containing every acceptance shape.
--
--   - DENOMINATION: the in-force projection is denominated in the LEDGER ROW ID on both producers
--     (SQL: row R excluded iff EXISTS s.supersedes = R.id; ASP: superseded(R) via supersedes/2 --
--     the id-is-order law, never ts, never a proxy). orphaned_by_retraction is denominated in the
--     SLUG (s22's item-identity primitive) plus the surviving row's own ledger id (a per-EVENT
--     handle, correctly so -- it names WHICH surviving event is orphaned, exactly
--     work_review_gap's close_id denomination one member over).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT class-ratified fail-safe
-- on its own motion -- it CHANGES the read semantics of four existing, in-use readers (a
-- superseded work event now reads retracted where it read live), a real behavior change, not a
-- pure addition. It is the Fable-authored, maintainer-RATIFIED delta the spec's own header names
-- (2026-07-15), so it routes on that ratification. The one purely-additive piece
-- (orphaned_by_retraction) would qualify as class-ratified alone -- named for the record, not
-- claimed as the routing reason.
--
-- LIMITS (pre-registered, matching s22/s26/s28/s29/s30's own disclosure convention):
--   - The unchanged write-boundary refusals bind only the granted :role's ordinary INSERT path
--     (schema-owner/superuser bypass, the same disclosed bound s26/s28/s29/s30 name). This delta
--     adds NO new trigger refusal, so no new instance of that bound.
--   - orphaned_by_retraction is SURFACED, never refused at construction -- the spec's own verb
--     ("surfaced, never silently tolerated"). Retracting an opening act while children survive is
--     legal; this member is how an operator sees it happened.
--   - The composite-ancestor re-open polarity is UNEXERCISABLE today (no composite mechanism in
--     the kernel -- see WHAT THIS DELTA DOES NOT DO). Filed, not buried.
--   - The standing ./judge differential is NOT wired to the work layer (see ENGINE above) -- the
--     acceptance evidence uses the established bespoke scratch differential; the standing wiring
--     is a named separate seam.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s22/s28/s29/s30): schema/
-- kern/role are psql variables so this delta is VALIDATED on a throwaway substrate before any
-- real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s31val -v kern=s31val_kernel -v role=s31val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql \
--        -f s29-obligation-item-key-and-typed-close.sql -f s30-typed-dependency-edges.sql \
--        -f s31-supersession-uniform-retraction.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (runs are
--   strictly linear, 2026-07-11). This delta reaches reality by entering a FUTURE world's birth
--   chain, wired by the ORCHESTRATOR's seam-integration pass into bootstrap/new-project.sh's
--   LINEAGE_CHAIN -- deliberately NOT taken here (the s28 precedent, and this build's own brief).
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only -- never applied to
--   any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE VIEW/FUNCTION; DROP/CREATE
-- TRIGGER).

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
-- ELEMENT 1 -- work_item_current RE-ISSUED: opened/claimed/closed CTEs read ledger_current.
-- Column list/shape otherwise BYTE-IDENTICAL to s29's version (no new column).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_current
    WITH (security_invoker = true) AS
WITH opened AS (
  SELECT work_slug AS slug, work_title AS title, work_parent AS parent_slug, id AS opened_id
  FROM :"schema".ledger_current WHERE kind = 'work_opened'
),
claimed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, actor AS claimant, id AS claimed_id
  FROM :"schema".ledger_current WHERE kind = 'work_claimed'
  ORDER BY work_slug, id DESC
),
closed AS (
  SELECT DISTINCT ON (work_slug) work_slug AS slug, work_resolution AS resolution,
         work_witness AS witness, work_review_disposition AS review_disposition,
         work_review_ref AS review_ref, id AS closed_id
  FROM :"schema".ledger_current WHERE kind = 'work_closed'
  ORDER BY work_slug, id DESC
)
SELECT o.slug, o.title,
       CASE WHEN c.slug IS NULL THEN 'open' ELSE 'closed' END AS state,
       c.resolution, c.witness, cl.claimant, o.parent_slug,
       c.review_disposition, c.review_ref
FROM   opened o
LEFT JOIN claimed cl ON cl.slug = o.slug
LEFT JOIN closed  c  ON c.slug  = o.slug;

-- ============================================================================================
-- ELEMENT 2 -- work_item_strict_blockers() RE-ISSUED: edges (both arms) + closes read
-- ledger_current; review_unresolved's discharge-review subquery UNCHANGED byte-for-byte (already
-- correctly factored -- header). Every other clause identical to s30's version.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_item_strict_blockers(root_slug text)
    RETURNS TABLE(blocking_slug text, reason text) LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE
  edges AS (
    -- s31: both arms read ledger_current (in-force only) -- a retracted work_parent or retracted
    -- blocks-close edge no longer feeds the AND-tree. Direction unchanged from s29/s30 (see those
    -- files' own comments for the parent/child role mapping).
    SELECT o.work_slug AS child, o.work_parent AS parent
    FROM ledger_current o WHERE o.kind = 'work_opened' AND o.work_parent IS NOT NULL
    UNION ALL
    SELECT dep.work_depends_on AS child, dep.work_slug AS parent
    FROM ledger_current dep WHERE dep.kind = 'work_depends_on' AND dep.edge_type = 'blocks-close'
  ),
  tree(slug) AS (
    SELECT root_slug
    UNION
    SELECT e.child FROM tree t JOIN edges e ON e.parent = t.slug
  ),
  closes AS (
    -- s31: reads ledger_current -- a retracted close no longer counts as "this tree member is
    -- closed" (not_closed below then correctly re-blocks the member).
    SELECT work_slug AS slug, id AS close_id, actor AS closer, work_review_disposition AS disp
    FROM ledger_current WHERE kind = 'work_closed'
  ),
  not_closed AS (
    SELECT t.slug, 'item is not yet closed'::text AS reason
    FROM tree t
    WHERE t.slug <> root_slug AND NOT EXISTS (SELECT 1 FROM closes c WHERE c.slug = t.slug)
  ),
  review_unresolved AS (
    -- UNCHANGED byte-for-byte from s29/s30: the discharge-review side was already correctly
    -- factored (an inline in-force filter scoped to the discharging review row itself).
    SELECT c.slug, 'review disposition deferred and undischarged (close row ' || c.close_id || ')' AS reason
    FROM closes c
    JOIN tree t ON t.slug = c.slug
    WHERE c.disp = 'deferred'
      AND NOT EXISTS (
        SELECT 1 FROM ledger r
        JOIN review_detail d ON d.ledger_id = r.id
        WHERE r.kind = 'review' AND r.regards = c.close_id AND d.verdict = 'attest' AND r.actor <> c.closer
          AND NOT EXISTS (SELECT 1 FROM ledger s2 WHERE s2.supersedes = r.id)
      )
  )
  SELECT slug, reason FROM not_closed
  UNION ALL SELECT slug, reason FROM review_unresolved;
$fn$;

-- ============================================================================================
-- ELEMENT 3 -- question_status RE-ISSUED: the question-row side reads ledger_current; the
-- per-answer in-force filters are UNCHANGED byte-for-byte (already correctly factored -- header).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".question_status
    WITH (security_invoker = true) AS
SELECT q.id AS question_id, q.kind AS question_kind,
       EXISTS (SELECT 1 FROM :"schema".ledger a WHERE a.answers = q.id
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = a.id)) AS answered,
       (SELECT min(a.id) FROM :"schema".ledger a WHERE a.answers = q.id
        AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = a.id)) AS first_answer_id,
       (q.kind <> 'question') AS answers_target_not_a_question
FROM   :"schema".ledger_current q
WHERE  q.kind = 'question' OR EXISTS (SELECT 1 FROM :"schema".ledger a WHERE a.answers = q.id);

-- ============================================================================================
-- ELEMENT 4 -- work_review_gap RE-ISSUED: the close-row subquery reads ledger_current; the outer
-- discharge-review NOT EXISTS is UNCHANGED byte-for-byte (already correctly factored -- header).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_review_gap
    WITH (security_invoker = true) AS
SELECT c.slug, c.close_id, c.closer
FROM (
  SELECT work_slug AS slug, id AS close_id, actor AS closer
  FROM :"schema".ledger_current WHERE kind = 'work_closed' AND work_review_disposition = 'deferred'
) c
WHERE NOT EXISTS (
  SELECT 1 FROM :"schema".ledger r
  JOIN :"schema".review_detail d ON d.ledger_id = r.id
  WHERE r.kind = 'review' AND r.regards = c.close_id AND d.verdict = 'attest' AND r.actor <> c.closer
    AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id)
);

-- ============================================================================================
-- ELEMENT 5 -- work_item_violations GAINS orphaned_by_retraction. Every PRE-EXISTING member
-- (duplicate_open, shipped_without_witness, depends_on_unknown_slug, dependency_cycle,
-- dangling_parent, parent_cycle, blocks_close_cycle) is UNCHANGED, byte-for-byte -- all seven
-- remain declared history/defense-in-depth reads over raw ledger (header). The four NEW orphan_*
-- CTEs read ledger_current (the one in-force factoring, reused not re-derived, ADR-0012 P1).
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
  ),
  blocks_close_deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent
    FROM :"schema".ledger WHERE kind = 'work_depends_on' AND edge_type = 'blocks-close'
  ),
  bc_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_close_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach r JOIN blocks_close_deps d ON d.dependent = r.cur
  ),
  blocks_close_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bc_reach WHERE cur = start_slug
  ),
  -- s31 (Element 5): the in-force opening-act set, and the four surviving-but-orphaned event
  -- shapes citing a retracted opening act (see header).
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
    SELECT lc.id, lc.work_slug AS slug, lc.work_parent AS parent_slug
    FROM :"schema".ledger_current lc
    WHERE lc.kind = 'work_opened' AND lc.work_parent IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM opened_current oc WHERE oc.slug = lc.work_parent)
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
SELECT 'parent_cycle', slug, NULL FROM parent_cycle
UNION ALL
SELECT 'blocks_close_cycle', slug, NULL FROM blocks_close_cycle
UNION ALL
SELECT 'orphaned_by_retraction', slug, 'surviving work_claimed row ' || id || ' cites a retracted opening act' FROM orphan_claims
UNION ALL
SELECT 'orphaned_by_retraction', slug, 'surviving work_closed row ' || id || ' cites a retracted opening act' FROM orphan_closes
UNION ALL
SELECT 'orphaned_by_retraction', slug, 'surviving work_depends_on row ' || id || ' cites a retracted opening act' FROM orphan_deps
UNION ALL
SELECT 'orphaned_by_retraction', slug, 'surviving child work_opened row ' || id || ' names a retracted parent opening act (' || parent_slug || ')' FROM orphan_children;

-- ============================================================================================
-- ELEMENT 6 -- validate_work_item() RE-ISSUED: DUPLICATE-OPEN EXCEPTION TEXT ONLY (the redo-idiom
-- sentences appended). Every query/condition in every branch is BYTE-IDENTICAL to s30's version
-- -- see header for why the duplicate-open condition itself must NOT change (slug burned,
-- ratified fork 2: the EXISTS deliberately reads raw ledger, retraction-blind).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
BEGIN
  IF NEW.kind = 'work_opened' THEN
    IF EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' already has an opening act — one opening act per slug (the Q5 defect: a decomposition ledgered twice under the same identity is refused, never silently duplicated). This holds even if that opening act has since been RETRACTED (superseded): under uniform retraction (s31, ratified 2026-07-15) a retracted open still permanently burns its slug, reinstatement-free. To redo the work under a fresh identity, open a NEW slug citing the old row: ./led work open <new-slug> "<title>" --refs row:<old-open-row-id>.', NEW.work_slug;
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
    -- s30 (unchanged, byte-for-byte): edge_type, fail-safe-defaulted and, for blocks-close,
    -- structurally refused.
    IF NEW.kind = 'work_depends_on' THEN
      IF NEW.edge_type IS NULL THEN
        NEW.edge_type := 'informs';
      END IF;
      IF NEW.edge_type = 'blocks-close' THEN
        IF NEW.work_depends_on = NEW.work_slug THEN
          RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot have a blocks-close dependency on itself — a self-edge is refused at construction for blocks-close (s30). informs edges are not subject to this refusal.', NEW.work_slug;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = NEW.work_depends_on) THEN
          RAISE EXCEPTION 'Ledger policy: work item slug ''%'' names a blocks-close antecedent ''%'' which has no opening act — a blocks-close edge requires BOTH endpoints to be close-tracked work items (s30), unlike an informs edge''s deliberately lax posture (s22). Open the antecedent first, or retry as --type informs.', NEW.work_slug, NEW.work_depends_on;
        ELSIF work_depends_on_would_cycle(NEW.work_slug, NEW.work_depends_on) THEN
          RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot take a blocks-close dependency on ''%'' — ''%'' already (transitively) has a blocks-close dependency on ''%'', so this edge would create a cycle; the obligation AND-tree must be a DAG or conjunction has no fixpoint (s30). informs edges are not subject to this refusal.', NEW.work_slug, NEW.work_depends_on, NEW.work_depends_on, NEW.work_slug;
        END IF;
      END IF;
    END IF;
    -- s29 (unchanged, byte-for-byte): epoch-gated review-disposition presence + strict-close.
    IF NEW.kind = 'work_closed'
       AND NEW.id > COALESCE((SELECT epoch FROM migration_epoch LIMIT 1), 0)
       AND NEW.work_review_disposition IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: work_closed row for item ''%'' (ledger id %) carries no review disposition — every close act past this world''s migration epoch (id %, see %.migration_epoch) must be witnessed or deferred, never silent (s29 Element B, sec-10 epoch amendment). Retry with --review-witness <ref> or --review-deferred.', NEW.work_slug, NEW.id, (SELECT epoch FROM migration_epoch LIMIT 1), TG_TABLE_SCHEMA;
    END IF;
    IF NEW.kind = 'work_closed' AND COALESCE(NEW.work_strict_close, false) THEN
      IF NEW.work_review_disposition = 'deferred' THEN
        RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' requires --review-witness (a review already on record) — --review-deferred cannot satisfy strict mode''s immediate obligation-tree requirement, because a just-deferred obligation is, by definition, unresolved the moment it is created (s29 Element C). Record the review first (./led review ...), then close with --review-witness <ref>.', NEW.work_slug;
      ELSIF NEW.work_review_disposition = 'witnessed' THEN
        SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
          INTO blockers
          FROM work_item_strict_blockers(NEW.work_slug) b;
        IF blockers IS NOT NULL THEN
          RAISE EXCEPTION 'Ledger policy: strict close of work item ''%'' refused — its obligation tree is unresolved: %. Resolve every named leaf, then retry (s29 Element C: strict close is a pure query over the derived conjunction, no stored verdict).', NEW.work_slug, blockers;
        END IF;
      END IF;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
-- The trigger definition itself (name, timing, table) is UNCHANGED -- CREATE OR REPLACE FUNCTION
-- above is sufficient; re-issuing DROP/CREATE TRIGGER is harmless idempotence, kept for symmetry
-- with s22/s28/s29/s30's own script shape.
DROP TRIGGER IF EXISTS validate_work_item ON :"schema".ledger;
CREATE TRIGGER validate_work_item BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_work_item();

-- ============================================================================================
-- GRANTS: none needed -- no new view/column; CREATE OR REPLACE with identical column lists/
-- signatures preserves every existing grant (s21's additive-column-order idiom, trivially
-- satisfied here since nothing is added or removed from any exposed shape).
-- ============================================================================================
