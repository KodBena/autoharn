-- s32 EDGE VIEWS + DISCHARGE JOIN: SINGLE HOME (design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md,
-- a fresh-Fable-eyes consultation record, F3/F6 + plan step 3; ledger item edge-views-single-home,
-- claimed by the orchestrator). This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to
-- any live/existing world is the maintainer's act at a FUTURE world's birth (runs-are-strictly-
-- linear ruling, 2026-07-11), never taken here. An ADDITIVE delta applied ON TOP of the s15..s31
-- kernel (the established remediation-delta idiom), NOT a retro-edit of a frozen sNN record
-- (ADR-0005 Rule 8) and NOT a second hand-copy of any existing mechanism (ADR-0012 P1: one home
-- per mechanism) -- this delta IS that collapse, applied to itself.
--
-- PREREQUISITE: this delta REQUIRES s31 (kernel/lineage/s31-supersession-uniform-retraction.sql)
-- applied first -- it re-issues work_item_strict_blockers()/work_item_violations/question_status-
-- adjacent objects that s31 itself re-issued to read ledger_current, and reads ledger_current
-- directly in the new work_edge_obligation/discharging_attest views. Applying this file on a
-- pre-s31 kernel fails loudly at CREATE VIEW/FUNCTION time (undefined relation ledger_current, or
-- the s31-shaped work_item_violations/strict_blockers bodies this file's CREATE OR REPLACE assumes
-- as its base), the correct, disclosed failure mode for a hard dependency, matching s29/s30/s31's
-- own PREREQUISITE precedent.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): the consult's F3/F6 findings, ADR-0000 Rule 2(a) applied to the kernel's OWN authoring
-- idiom (the consult's one-sentence diagnosis: recurring morphisms re-instantiated by hand per
-- delta, coherence asserted in PROSE -- "an edge walks OPPOSITE its own column names" -- rather
-- than held by ONE definition). Two hand-copied facts, collapsed here:
--   F3 -- the parent/depends-on DIRECTION-FLIP comment block ("a work_depends_on edge walks
--   OPPOSITE its own column names ... the DEPENDENT plays the parent role") is copied verbatim at
--   s29:466-473, s30:382-391, s31:384-391 (work_item_strict_blockers' own edges CTE, re-issued
--   three times as the function itself was extended) -- one fact, three prose homes. The consult's
--   own ladder (sec 2): SQL "can state the objects once (named edge views) but cannot parameterize
--   the recursion over a relation name" -- so this delta collapses the edge SOURCE (what is an
--   edge, which way does it point) into three named views, and leaves every WALK (the recursive
--   CTEs, the would_cycle functions' seeded per-call walks) exactly as they were, reading the new
--   views instead of re-deriving the edge predicate inline.
--   F6 -- "an un-superseded, distinct-actor attest review regarding row R" is hand-copied in
--   review_gap (s15), countersigned_in_force (s15+, re-issued through s30), work_review_gap (s29,
--   whose own header already says "mirrors review_gap's own join shape exactly"), and
--   work_item_strict_blockers' review_unresolved (s29/s30/s31). One derived view
--   (discharging_attest) is now the single home; every consumer composes with it.
--
-- WHAT "SINGLE HOME" MEANS HERE, PRECISELY (the one real design decision this delta makes, named
-- because two of the four hand-copies were NOT byte-identical to begin with -- countersigned_in_force
-- has NO distinct-actor predicate; the other three DO). discharging_attest(regards_id, reviewer)
-- exposes the GENERAL shape -- an un-superseded attest review, with its reviewing actor as a
-- column -- and does NOT bake in "distinct from whom", because "distinct from whom" varies by
-- consumer (review_gap/work_review_gap/strict_blockers each compare against their OWN closer/actor;
-- countersigned_in_force asks no such question at all, verified against its own s30 body, unchanged
-- since). This is the correct single home under ADR-0012 P1 (a fact has one home) READ TOGETHER
-- with ADR-0008 (do not fuzzy-match two distinct facts into one): "is this an attest review of row
-- R, un-superseded" is the one shared fact; "is the reviewer distinct from actor X" is a
-- per-consumer PREDICATE over that fact, not a second copy of the fact itself. Baking the
-- distinct-actor filter into the view would have been the FUZZY-MATCH error -- forcing
-- countersigned_in_force's genuinely different semantics to either drift from its three siblings or
-- silently change (forbidden, see FAIL-SAFE CLASSIFICATION below).
--
-- THE SAME SPLIT APPLIES TO THE EDGE VIEWS, FOR A DIFFERENT REASON (raw history vs in-force,
-- not a predicate variance): work_parent_would_cycle()/work_depends_on_would_cycle() and
-- work_item_violations' dangling_parent/parent_cycle/blocks_close_cycle members are all DECLARED
-- HISTORY readers (gates/ledger_reader_allowlist.py's own allowlist, s31) -- a bypassed-trigger
-- cycle check or a structural-existence question over "did this edge shape ever get written" must
-- see EVERY edge ever inserted, retracted or not (a retracted node still occupies its slug's place
-- in history, s31's own allowlist reason for work_parent_would_cycle, verbatim). work_edge_parent
-- and work_edge_blocks_close are therefore RAW (read ledger directly, no supersession filter) --
-- the exact same rows their five current consumers already see, so repointing them is provably
-- byte-identical, never a semantics change. work_item_strict_blockers' obligation-tree walk is the
-- ONE consumer that needs the IN-FORCE reading (s31's own Element 2 fix) -- so work_edge_obligation
-- is built by JOINing the two raw edge views against ledger_current on each edge's OWN carrying row
-- (a work_parent edge and a work_depends_on edge are each carried entirely on ONE ledger row, s28/
-- s30's own "no new base table" doctrine -- "is the edge in force" IS "is its carrying row in
-- ledger_current", nothing more to compute). This reproduces s31's own edges CTE bit-for-bit: filter-
-- then-join and join-then-filter select the identical row set. No fourth "in-force parent edge"
-- view is minted -- work_edge_obligation IS that composition, named once.
--
-- ELEMENT 1 -- THREE NAMED EDGE VIEWS, ONE HOME EACH (spec F3, consult plan step 3):
--   * work_edge_parent(parent_slug, child_slug, edge_row_id) -- the s28 work_parent edge, RAW
--     (every work_opened row with a non-NULL work_parent, retracted or not). edge_row_id is the
--     CHILD's own opening-act ledger id -- the edge and the opening act are the SAME row (s28's own
--     "no new base table" doctrine), so this is the one column an in-force filter needs to join on.
--   * work_edge_blocks_close(dependent_slug, antecedent_slug, edge_row_id) -- the s30 blocks-close
--     edge, RAW (every work_depends_on row with edge_type='blocks-close', retracted or not).
--     edge_row_id is the work_depends_on row's own id, the SAME reasoning one edge kind over.
--   * work_edge_obligation(from_slug, to_slug) -- the UNION in obligation-tree orientation
--     ("walking FROM from_slug reaches tree member to_slug" -- s29/s30/s31's own direction-flip
--     comment, now stated ONCE, here): parent->child for s28 (from_slug=parent_slug,
--     to_slug=child_slug), dependent->antecedent for blocks-close (from_slug=dependent_slug,
--     to_slug=antecedent_slug) -- IN-FORCE ONLY (each arm's carrying row joined against
--     ledger_current), matching s31's own Element 2 exactly.
--
-- ELEMENT 2 -- discharging_attest(regards_id, reviewer) -- ONE home of "un-superseded attest review
-- regarding row R" (spec F6). Reads ledger_current (not a hand-rolled anti-join) -- itself an
-- ADR-0012 P1 improvement over all four of its predecessor hand-copies, which each re-derived the
-- "un-superseded" half inline as a second NOT EXISTS(supersedes) (exactly the two-writers drift
-- s31's own allowlist gate exists to foreclose). The DISTINCT-ACTOR predicate is NOT baked in here
-- (see WHAT "SINGLE HOME" MEANS above) -- each consumer applies its own `reviewer <> X` (or no
-- filter at all, countersigned_in_force) at the join site.
--
-- ELEMENT 3 -- CONSUMERS RE-ISSUED TO COMPOSE, BYTE-IDENTICAL OUTPUT (CREATE OR REPLACE, the SAME
-- objects s15/s22/s28/s29/s30/s31 already defined -- ADR-0012 P1, not a second copy):
--   * review_gap (s15) -- discharge leg only; its own row's-currentness anti-join (the FIRST
--     NOT EXISTS, a DIFFERENT concern from the discharge join) is untouched, verbatim.
--   * countersigned_in_force (s15+, last re-issued s30) -- discharge leg only, same reasoning;
--     its own row's-currentness anti-join untouched, verbatim.
--   * work_review_gap (s29, re-issued s31) -- discharge leg only; the close-row ledger_current leg
--     (s31's own Element 4) untouched, verbatim.
--   * work_item_strict_blockers() (s29, extended s30, re-issued s31) -- the `edges` CTE now reads
--     work_edge_obligation directly (replacing its own two-arm UNION ALL); `review_unresolved`'s
--     discharge leg now reads discharging_attest. `closes`/`tree`/`not_closed` untouched, verbatim.
--   * work_item_violations (s22, extended s28/s30, re-issued s31) -- its `parents`/`parent_anc`
--     (feeding dangling_parent/parent_cycle) and `blocks_close_deps`/`bc_reach` (feeding
--     blocks_close_cycle) CTEs now read work_edge_parent/work_edge_blocks_close instead of
--     re-deriving the same predicate inline; its `orphan_children` member (Element 5, s31) now
--     reads work_edge_parent joined to ledger_current instead of re-deriving the parent-edge
--     predicate a second time over ledger_current directly. Every OTHER member (duplicate_open,
--     shipped_without_witness, the plain depends_on graph -- deps/dangling_dep/reach/dep_cycle,
--     which is NOT type-filtered and so has no covering edge view -- opened_current/orphan_claims/
--     orphan_closes/orphan_deps) is UNCHANGED, byte-for-byte, below.
--   * work_parent_would_cycle() (s28) -- its recursive walk now reads work_edge_parent (RAW,
--     matching its own prior inline `JOIN ledger o ON o.kind='work_opened' AND o.work_slug=a.slug`)
--     instead of re-deriving the same predicate; the WALK SHAPE (seeded per-call recursion, depth
--     capped at 10000) is UNCHANGED -- the consult's own plan step 3 is explicit that a full-star
--     view is the wrong complexity for a per-INSERT trigger check, so only the edge SOURCE moves.
--   * work_depends_on_would_cycle() (s30) -- same treatment, reading work_edge_blocks_close (RAW).
-- validate_work_item() is NOT re-issued by this delta -- it calls the two would_cycle functions by
-- name (unchanged call signature) and contains no edge-walk or discharge-join logic of its own to
-- collapse; leaving it untouched is the smaller diff and the lower-risk one (ADR-0004 minimal-touch).
--
-- WHAT THIS DELTA DELIBERATELY DOES NOT DO (ADR-0013 Rule 4, filed not buried):
--   - NO change to the plain (untyped) work_depends_on graph (deps/dangling_dep/reach/dep_cycle in
--     work_item_violations) -- it is not filtered to any single edge kind (it reads EVERY
--     work_depends_on row regardless of edge_type), so no covering view exists in this delta's
--     3-view scope; inventing a fourth "any-type edge" view the consult never asked for is exactly
--     the scope creep ADR-0004 forbids.
--   - NO change to duplicate_open, shipped_without_witness, depends_on_unknown_slug,
--     dependency_cycle, opened_current, orphan_claims, orphan_closes, orphan_deps -- none of these
--     read the parent or blocks-close edge relation this delta names.
--   - NO change to validate_work_item()'s own inline dangling-parent/self-edge/dangling-antecedent
--     EXISTS checks -- those are simple existence predicates, not edge WALKS, and are out of this
--     delta's F3/F6 scope.
--   - NO wiring of engine/**, no ledger_floor.py edit -- ENGINE below explains why none is needed.
--   - NO change to LINEAGE_CHAIN in bootstrap/new-project.sh -- the orchestrator lands that seam
--     (this file's own commission: "Do NOT wire LINEAGE_CHAIN").
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: the parent edge, the blocks-close edge, the obligation-tree union edge, and the
--     discharge join each have exactly ONE definition (ADR-0012 P1) -- a reader that needs the
--     RAW/history reading of an edge composes with work_edge_parent/work_edge_blocks_close; a
--     reader that needs the IN-FORCE reading composes with work_edge_obligation (itself built by
--     joining the raw views to ledger_current on the edge's own carrying row -- never a fourth,
--     independently-filtered edge relation); a reader that needs "an un-superseded attest review
--     regarding row R" composes with discharging_attest, adding its OWN distinct-actor predicate
--     (or none) at the join site rather than re-deriving the shared half.
--
--   - QUANTIFICATION UNIVERSE -- re-reading every table/view/function the s15..s31 chain exposes to
--     :role (mirroring s28/s29/s30/s31's own re-verification discipline), checked against the four
--     new views and the seven re-issued consumers this delta touches:
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table, no new column (a
--         pure re-issue of view/function bodies plus four new derived views over existing columns).
--       NEW VIEWS (four, all named above): work_edge_parent, work_edge_blocks_close,
--         work_edge_obligation, discharging_attest.
--       VIEWS/FUNCTIONS RE-ISSUED (seven): review_gap, countersigned_in_force, work_review_gap,
--         work_item_strict_blockers(), work_item_violations, work_parent_would_cycle(),
--         work_depends_on_would_cycle().
--       VIEWS RE-VERIFIED NOT MEMBERS of the "column-complete" class: ledger_current /
--         countersigned_in_force's own COLUMN LIST -- unchanged (this delta adds no column, only
--         rewrites countersigned_in_force's WHERE clause); work_item_current, work_item_descendants
--         -- re-verified NOT touched (neither reads the discharge join or the raw edge predicate
--         this delta collapses; work_item_descendants inherits Element-1-shaped currentness from
--         work_item_current with zero edits here, s31's own precedent, re-applied).
--       KIND VOCABULARY -- unchanged. This delta adds no new `kind` value and no new column.
--       GRANTS -- the four new views each get a fresh GRANT SELECT (security_invoker views compose
--         through invoker privilege on every underlying relation they read, so :role needs direct
--         SELECT on each new view even though it also reaches them indirectly through a re-issued
--         consumer view/function). No existing grant changes -- every re-issued view/function keeps
--         its exact prior column list/signature (s21's additive-column-order idiom, trivially
--         satisfied: zero columns added or removed anywhere in this delta).
--       READER TYPING (s31's own standing gate, gates/ledger_reader_allowlist.py) -- work_edge_parent
--         and work_edge_blocks_close are RAW/history readers by design (see WHY above) and are added
--         to the gate's ALLOWLIST with their reasons, in this same delta's own commit (the gate file
--         is not engine/** or law/ and is the standing mechanical detect s31 shipped for exactly
--         this class of change). work_edge_obligation and discharging_attest read ONLY
--         ledger_current and other named views (never raw `ledger` directly) -- current-truth-typed
--         by construction, no allowlist entry needed. The seven re-issued consumers each have EQUAL
--         OR FEWER raw-ledger legs than before (work_item_strict_blockers and work_review_gap now
--         have ZERO raw-ledger legs at all, having composed away their only remaining one; review_gap/
--         countersigned_in_force keep their one pre-existing, unrelated raw currentness leg;
--         work_item_violations keeps its untouched plain-depends-on-graph and defense-in-depth
--         legs) -- never MORE, so the allowlist gate's green/red polarity is unaffected in the
--         refusing direction and only shrinks in the declaring direction.
--       ENGINE -- NONE shipped or touched in this delta (mirrors s23/s25/s26/s28's own "ENGINE --
--         NONE" disclosure, and s31's own finding that the standing ./judge differential is not
--         wired to the work layer): engine/ledger_floor.py's work_item_floor_atoms()/
--         work_review_floor_atoms() already read `ledger_current` directly (their own independent
--         SQL-floor mirror, per s31's own header) and this delta changes NO output of any SQL
--         object they query -- their queries need zero edits to stay byte-for-byte correct.
--         engine/lp/*.lp is untouched (this delta's own scope explicitly excludes engine/**, a
--         concurrently-owned area per this commission's own brief). `./judge`'s existing SQL/ASP
--         differential is UNAFFECTED (it derives T_now facts from kind/status/supersedes/etc., none
--         of which this delta touches) and continues to AGREE -- scratch-witnessed as part of this
--         delta's own acceptance.
--
--   - DENOMINATION: every edge view's identity columns are SLUGS (s22/s28/s30's own denomination,
--     re-applied, never a row id as the join key) -- edge_row_id is present ONLY as internal
--     provenance (which ledger row carries this edge fact, needed solely to join against
--     ledger_current), never surfaced as a second identity for the edge itself. discharging_attest's
--     regards_id is the LEDGER ROW ID of the row being discharged (the SAME denomination
--     review_detail.antecedent/ledger.regards already use, s15/s29 -- a per-EVENT handle, correctly
--     so, since a discharge names WHICH row it discharges); reviewer is the ACTOR column, unchanged
--     denomination.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta is PURE REFACTOR --
-- (a)-CLASS COLLAPSE-NOW, not class-ratified-fail-safe-by-the-maintainer's-2026-07-09-dict (that
-- ruling is for ADDITIVE deltas; this one changes zero refusal, zero column, zero kind, zero output
-- row of any query in the tree -- it is a strictly STRONGER claim than fail-safe-additive: NO
-- observable behavior changes at all, additive or otherwise). Every re-issued object's new body was
-- checked, by construction, to select the identical row set as its predecessor (see ELEMENT 3's own
-- per-object reasoning above) and this is witnessed empirically (not merely argued) by this delta's
-- own acceptance: a full BEFORE/AFTER capture of every re-issued view's rows plus
-- work_item_strict_blockers()'s output on one fixture world, diffed EMPTY across the s32 apply.
-- Routed to the orchestrator per this commission's own claimed ledger item (edge-views-single-home)
-- rather than self-certified class-ratified, consistent with s28/s29/s30/s31's own posture of
-- naming the classification for the record without treating the naming as a bypass of review.
--
-- LIMITS (pre-registered, matching s22/s26/s28/s29/s30/s31's own disclosure convention):
--   - work_edge_parent/work_edge_blocks_close are RAW BY DESIGN (see WHY above) -- a reader that
--     wants the in-force-only reading of either edge kind alone (not the obligation-tree union) has
--     no single-view shortcut in this delta; it would JOIN the raw view to ledger_current itself,
--     exactly as work_edge_obligation does internally. No such reader exists in this tree today, so
--     none is built ahead of need (ADR-0004: no speculative generality).
--   - The plain (untyped) work_depends_on graph -- deps/dangling_dep/reach/dep_cycle in
--     work_item_violations -- has NO covering edge view in this delta (see WHAT THIS DELTA
--     DELIBERATELY DOES NOT DO); a future delta wanting to collapse it would mint a fourth,
--     unfiltered `work_edge_depends_on(dependent_slug, antecedent_slug, edge_row_id, edge_type)`
--     view, not shoehorn it into work_edge_blocks_close's blocks-close-only shape.
--   - Like every trigger-enforced refusal in this lineage, work_parent_would_cycle()/
--     work_depends_on_would_cycle()'s bypass bound (a schema-owner/superuser with DDL privilege can
--     disable the trigger or write directly) is UNCHANGED -- this delta adds no new refusal and
--     touches no trigger definition.
--   - The allowlist gate's ALLOWLIST dict entries for work_item_strict_blockers/work_review_gap
--     become VESTIGIAL after this delta (both objects now have ZERO raw-ledger legs and would
--     classify as clean without an entry at all) -- left in place, reworded to say so, rather than
--     deleted, so a reader diffing gates/ledger_reader_allowlist.py's history sees the collapse
--     recorded at the object it describes, not silently vanished (ADR-0013 Rule 4).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s22/s28/s29/s30/s31):
-- schema/kern/role are psql variables so this delta is VALIDATED on a throwaway substrate before
-- any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s32val -v kern=s32val_kernel -v role=s32val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql \
--        -f s29-obligation-item-key-and-typed-close.sql -f s30-typed-dependency-edges.sql \
--        -f s31-supersession-uniform-retraction.sql -f s32-edge-views-single-home.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired by the orchestrator's seam-integration pass into
--   `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` (not taken here -- this commission's own brief:
--   "Do not wire LINEAGE_CHAIN"). Authored and scratch-witnessed on scratch schema pairs in the TOY
--   db only -- NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE VIEW/FUNCTION).

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
-- ELEMENT 1a -- work_edge_parent -- the ONE home of the s28 parent-edge relation, RAW (see header
-- WHY: every current consumer of this shape is a declared history reader, or joins to
-- ledger_current itself downstream, so no supersession filter belongs on the view itself).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_edge_parent
    WITH (security_invoker = true) AS
SELECT o.work_parent AS parent_slug, o.work_slug AS child_slug, o.id AS edge_row_id
FROM   :"schema".ledger o
WHERE  o.kind = 'work_opened' AND o.work_parent IS NOT NULL;

COMMENT ON VIEW :"schema".work_edge_parent IS
  'Single home (kernel/lineage/s32-edge-views-single-home.sql, ADR-0012 P1) of the s28 work_parent
   edge relation: an edge walks PARENT -> CHILD literally (child.work_parent = parent, matching the
   column names). RAW -- includes every such edge ever written, retracted or not (a retracted
   opening act still occupies its slug''s place in history, s31''s own allowlist reasoning for
   work_parent_would_cycle, re-applied here). edge_row_id is the child''s own opening-act ledger id
   (the edge and the opening act are the SAME row) -- join it to ledger_current for the in-force
   reading (see work_edge_obligation), never re-derive the predicate inline a second time.';

-- ============================================================================================
-- ELEMENT 1b -- work_edge_blocks_close -- the ONE home of the s30 blocks-close edge relation, RAW,
-- same reasoning one edge kind over.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_edge_blocks_close
    WITH (security_invoker = true) AS
SELECT dep.work_slug AS dependent_slug, dep.work_depends_on AS antecedent_slug, dep.id AS edge_row_id
FROM   :"schema".ledger dep
WHERE  dep.kind = 'work_depends_on' AND dep.edge_type = 'blocks-close';

COMMENT ON VIEW :"schema".work_edge_blocks_close IS
  'Single home (kernel/lineage/s32-edge-views-single-home.sql, ADR-0012 P1) of the s30 blocks-close
   edge relation: an edge walks DEPENDENT -> ANTECEDENT opposite its own column names (the DEPENDENT
   plays the walk-from role; the ANTECEDENT is the tree member reached -- s29/s30/s31''s own
   direction-flip comment, now stated once, here). RAW -- includes every blocks-close edge ever
   written, retracted or not, matching work_depends_on_would_cycle()''s and
   work_item_violations.blocks_close_cycle''s own pre-existing raw reading exactly. edge_row_id is
   the work_depends_on row''s own ledger id -- the SAME reasoning work_edge_parent gives one edge
   kind over.';

-- ============================================================================================
-- ELEMENT 1c -- work_edge_obligation -- the IN-FORCE union, in obligation-tree walk orientation
-- (from_slug -> to_slug), built by joining EACH raw edge view to ledger_current on its own carrying
-- row -- reproduces s31's own two-arm edges CTE bit-for-bit (filter-then-join and join-then-filter
-- select the identical row set). The ONE consumer of this exact shape is
-- work_item_strict_blockers()'s obligation-tree walk.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_edge_obligation
    WITH (security_invoker = true) AS
SELECT e.parent_slug AS from_slug, e.child_slug AS to_slug
FROM   :"schema".work_edge_parent e
JOIN   :"schema".ledger_current lc ON lc.id = e.edge_row_id
UNION ALL
SELECT e.dependent_slug AS from_slug, e.antecedent_slug AS to_slug
FROM   :"schema".work_edge_blocks_close e
JOIN   :"schema".ledger_current lc ON lc.id = e.edge_row_id;

COMMENT ON VIEW :"schema".work_edge_obligation IS
  'The obligation-tree union edge (kernel/lineage/s32-edge-views-single-home.sql): walking FROM
   from_slug reaches tree member to_slug -- parent->child for the s28 arm, dependent->antecedent for
   the s30 blocks-close arm (s29 sec-5''s own "children via work_depends_on, the s28 parent edge"
   text, now composed from work_edge_parent/work_edge_blocks_close rather than re-derived). IN-FORCE
   ONLY (each arm''s carrying row joined against ledger_current) -- matches s31''s own Element 2
   fix exactly; the sole consumer needing this exact composition is
   work_item_strict_blockers()''s edges CTE.';

-- ============================================================================================
-- ELEMENT 2 -- discharging_attest -- the ONE home of "un-superseded attest review regarding row R"
-- (F6). Reads ledger_current directly (never a hand-rolled anti-join) -- the reviewer's distinct-
-- actor predicate is DELIBERATELY NOT baked in here (see header WHY: countersigned_in_force asks no
-- such question; the other three consumers each apply their own comparison at the join site).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".discharging_attest
    WITH (security_invoker = true) AS
SELECT r.regards AS regards_id, r.actor AS reviewer
FROM   :"schema".ledger_current r
JOIN   :"schema".review_detail d ON d.ledger_id = r.id
WHERE  r.kind = 'review' AND d.verdict = 'attest';

COMMENT ON VIEW :"schema".discharging_attest IS
  'Single home (kernel/lineage/s32-edge-views-single-home.sql, ADR-0012 P1) of "an un-superseded
   attest review regarding row R" -- regards_id names R, reviewer is the reviewing actor. Deliberately
   does NOT filter reviewer against any particular actor -- that predicate varies per consumer
   (review_gap/work_review_gap/work_item_strict_blockers each compare reviewer <> their own
   closer/actor; countersigned_in_force applies no such filter at all, unchanged since s15) -- baking
   it in here would have fuzzy-matched two distinct facts into one (ADR-0008).';

GRANT SELECT ON :"schema".work_edge_parent, :"schema".work_edge_blocks_close,
                :"schema".work_edge_obligation, :"schema".discharging_attest TO :"role";

-- ============================================================================================
-- ELEMENT 3a -- review_gap (s15) RE-ISSUED: discharge leg composes with discharging_attest. The
-- row's-own-currentness anti-join (a DIFFERENT concern) is UNCHANGED, verbatim.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".review_gap
    WITH (security_invoker = true) AS
SELECT l.id, l.actor, o.scope, o.assigned_by
FROM   :"schema".ledger l JOIN :"schema".countersign_obligation o ON o.obliges_actor = l.actor
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    NOT EXISTS (SELECT 1 FROM :"schema".discharging_attest da
                    WHERE da.regards_id = l.id AND da.reviewer <> l.actor);

-- ============================================================================================
-- ELEMENT 3b -- countersigned_in_force (s15+, last re-issued s30) RE-ISSUED: discharge leg composes
-- with discharging_attest, WITH NO distinct-actor predicate (unchanged semantics -- see header WHY).
-- Column list and the row's-own-currentness anti-join are UNCHANGED, verbatim.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close, l.edge_type
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 3c -- work_review_gap (s29, re-issued s31) RE-ISSUED: discharge leg composes with
-- discharging_attest. The close-row ledger_current leg (s31's own Element 4) is UNCHANGED, verbatim.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_review_gap
    WITH (security_invoker = true) AS
SELECT c.slug, c.close_id, c.closer
FROM (
  SELECT work_slug AS slug, id AS close_id, actor AS closer
  FROM :"schema".ledger_current WHERE kind = 'work_closed' AND work_review_disposition = 'deferred'
) c
WHERE NOT EXISTS (
  SELECT 1 FROM :"schema".discharging_attest da
  WHERE da.regards_id = c.close_id AND da.reviewer <> c.closer
);

-- ============================================================================================
-- ELEMENT 3d -- work_item_strict_blockers() (s29, extended s30, re-issued s31) RE-ISSUED: the
-- `edges` CTE now reads work_edge_obligation directly (replacing its own two-arm UNION ALL);
-- `review_unresolved`'s discharge leg now composes with discharging_attest. `closes`/`tree`/
-- `not_closed` are UNCHANGED, verbatim.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_item_strict_blockers(root_slug text)
    RETURNS TABLE(blocking_slug text, reason text) LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE
  edges AS (
    -- s32: both arms now read the single obligation-tree edge view (ELEMENT 1c above) -- same
    -- direction ("walking FROM parent we reach child"), same in-force filtering (s31's own
    -- Element 2), zero re-derivation of either edge's own predicate here.
    SELECT e.to_slug AS child, e.from_slug AS parent FROM work_edge_obligation e
  ),
  tree(slug) AS (
    SELECT root_slug
    UNION
    SELECT e.child FROM tree t JOIN edges e ON e.parent = t.slug
  ),
  closes AS (
    SELECT work_slug AS slug, id AS close_id, actor AS closer, work_review_disposition AS disp
    FROM ledger_current WHERE kind = 'work_closed'
  ),
  not_closed AS (
    SELECT t.slug, 'item is not yet closed'::text AS reason
    FROM tree t
    WHERE t.slug <> root_slug AND NOT EXISTS (SELECT 1 FROM closes c WHERE c.slug = t.slug)
  ),
  review_unresolved AS (
    -- s32: discharge leg composes with discharging_attest (ELEMENT 2 above) instead of re-deriving
    -- the review/verdict/not-superseded join inline a fourth time.
    SELECT c.slug, 'review disposition deferred and undischarged (close row ' || c.close_id || ')' AS reason
    FROM closes c
    JOIN tree t ON t.slug = c.slug
    WHERE c.disp = 'deferred'
      AND NOT EXISTS (
        SELECT 1 FROM discharging_attest da WHERE da.regards_id = c.close_id AND da.reviewer <> c.closer
      )
  )
  SELECT slug, reason FROM not_closed
  UNION ALL SELECT slug, reason FROM review_unresolved;
$fn$;

-- ============================================================================================
-- ELEMENT 3e -- work_parent_would_cycle() (s28) RE-ISSUED: the recursive walk now reads
-- work_edge_parent (RAW, ELEMENT 1a above) instead of re-deriving its own
-- `JOIN ledger o ON o.kind='work_opened' AND o.work_slug=a.slug` predicate. WALK SHAPE UNCHANGED
-- (seeded per-call recursion, depth-capped at 10000, self-case redundant with work_parent_not_self
-- at depth 0 -- s28's own header, unchanged reasoning) -- only the edge SOURCE moves, per the
-- consult's own plan step 3 ("collapse the edge SOURCE, not the walk").
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_parent_would_cycle(candidate_parent text, candidate_child text)
    RETURNS boolean LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE anc(slug, depth) AS (
    SELECT candidate_parent, 0
    UNION ALL
    SELECT e.parent_slug, a.depth + 1
    FROM anc a
    JOIN work_edge_parent e ON e.child_slug = a.slug
    WHERE a.depth < 10000
  )
  SELECT EXISTS (SELECT 1 FROM anc WHERE slug = candidate_child);
$fn$;

-- ============================================================================================
-- ELEMENT 3f -- work_depends_on_would_cycle() (s30) RE-ISSUED: same treatment, reading
-- work_edge_blocks_close (RAW, ELEMENT 1b above). WALK SHAPE UNCHANGED.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_depends_on_would_cycle(dependent_slug text, antecedent_slug text)
    RETURNS boolean LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE reach(slug, depth) AS (
    SELECT antecedent_slug, 0
    UNION ALL
    SELECT e.antecedent_slug, r.depth + 1
    FROM reach r
    JOIN work_edge_blocks_close e ON e.dependent_slug = r.slug
    WHERE r.depth < 10000
  )
  SELECT EXISTS (SELECT 1 FROM reach WHERE slug = dependent_slug);
$fn$;

-- ============================================================================================
-- ELEMENT 3g -- work_item_violations (s22, extended s28/s30, re-issued s31) RE-ISSUED: `parents`/
-- `parent_anc` (feeding dangling_parent/parent_cycle) and `blocks_close_deps`/`bc_reach` (feeding
-- blocks_close_cycle) now read work_edge_parent/work_edge_blocks_close instead of re-deriving the
-- same predicate inline; `orphan_children` (Element 5, s31) now reads work_edge_parent joined to
-- ledger_current instead of re-deriving the in-force parent-edge predicate a second time. Every
-- OTHER member is UNCHANGED, byte-for-byte, below (opens/dup_open, shipped_no_witness, the plain
-- depends_on graph -- deps/dangling_dep/reach/dep_cycle, not type-filtered, no covering edge view --
-- opened_current/orphan_claims/orphan_closes/orphan_deps, and the final SELECT/UNION ALL list).
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
  -- s32: parents/parent_anc/blocks_close_deps/bc_reach compose with the s32 edge views (ELEMENT 1a/
  -- 1b) instead of re-deriving their own predicate inline -- provably byte-identical: both views are
  -- RAW, the same row set these four CTEs already selected before this delta.
  parents AS (
    SELECT child_slug AS slug, parent_slug FROM :"schema".work_edge_parent
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
  -- s31 (Element 5): the in-force opening-act set, and the four surviving-but-orphaned event shapes
  -- citing a retracted opening act. opened_current/orphan_claims/orphan_closes/orphan_deps UNCHANGED,
  -- byte-for-byte; orphan_children (s32) composes with work_edge_parent joined to ledger_current.
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
-- GRANTS: the four new views' grants are issued above (ELEMENT 1c's GRANT block). No other grant
-- change -- every re-issued view/function keeps its exact prior column list/signature (s21's
-- additive-column-order idiom, trivially satisfied: zero columns added or removed anywhere here).
-- ============================================================================================
