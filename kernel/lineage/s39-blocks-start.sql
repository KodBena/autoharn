-- s39 BLOCKS-START (claim-time precondition foreclosure) -- the maintainer's 2026-07-17
-- commission, verbatim: "do we have some kind of way to ensure that items ... are not 'opened' or
-- 'started' until preconditions are met? So that a hook can tell the agent 'don't do that, do the
-- right thing instead', to structurally foreclose dependency violations?" FAIL-SAFE-ADDITIVE class
-- (CLAUDE.md ORCHESTRATION, class-ratified 2026-07-09): this delta ONLY adds vocabulary, refusals,
-- and derived views -- nothing existing is relaxed, no existing refusal loosened, no existing edge
-- semantics changed. Sonnet-authored per the standing delegation contract.
--
-- HISTORY: safe -- one existing CHECK (s30's edge_type_check) re-issued WIDER (gains one new
-- legal value, 'blocks-start', disjoint from the pre-existing {blocks-close, informs}; every
-- pre-existing row's own edge_type value -- blocks-close, informs, or NULL -- remains exactly as
-- legal as before: RE-ISSUE-ONLY, no existing row touched, no backfill, no UPDATE, matching s30's
-- own "the ledger is append-only" grounds for why no backfill is ever possible here). No new
-- column, no new kind. Two existing objects re-issued to ALSO handle the new value (validate_
-- work_item_depends, the s35 leaf; work_item_violations, last shaped by s37 v3) -- both re-issues
-- are ADDITIVE ONLY: every pre-existing branch/arm is byte-identical below, a new branch/arm is
-- appended. One existing object (validate_work_item, the s35 dispatcher) gains ONE new ELSIF-arm
-- call -- the pre-existing branches (open/disposition/depends/close) are byte-identical. Grounds:
-- re-issue-only / additive-vocabulary (Element 1); new-branch-only, never a relaxation (Element
-- 2/3); new-arm-only, no existing arm narrowed or widened (Element 4). Detect sibling fingerprints
-- BEHAVIOR (the widened vocabulary's third legal value plus the new claim-time refusal's own
-- shape), never a pinned object name, per the s29/s30 detect ruling of 2026-07-16
-- (migrate-detect-drift fix: a fingerprint pinned to a single named object silently
-- false-negatives the moment a later refactor moves the marker elsewhere).
--
-- Sonnet-authored per the standing delegation contract (CLAUDE.md ORCHESTRATION), from this
-- commission's own brief. This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any
-- live/existing world is the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear
-- ruling, 2026-07-11), never taken here. An ADDITIVE delta applied ON TOP of the s15..s38 kernel
-- (the established remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005
-- Rule 8) and NOT a second hand-copy of any existing mechanism (ADR-0012 P1: this delta reuses
-- edge_type/work_depends_on, s30's own existing columns, and composes with work_edge_blocks_close's
-- own single-home pattern (s32) for its new sibling view, rather than minting a fourth
-- freestanding mechanism for the same shape).
--
-- PREREQUISITE: this delta REQUIRES s38 (kernel/lineage/s38-bookkeeping-close.sql) applied first
-- -- it re-issues work_item_violations in the EXACT v3 shape s37 (unaltered by s38) left it, and
-- validate_work_item()/validate_work_item_depends, the s35 dispatcher/leaf shape s37/s38 left
-- untouched. Applying this file on a pre-s38 kernel fails loudly at CREATE OR REPLACE
-- FUNCTION/VIEW time (the leaf/view bodies below assume s37 v3's own CTE shape and s35's own
-- leaf-decomposition signatures), the correct, disclosed failure mode for a hard dependency,
-- matching every prior delta's own PREREQUISITE precedent. ALSO REQUIRES s32
-- (kernel/lineage/s32-edge-views-single-home.sql): the new work_edge_blocks_start view mirrors
-- work_edge_blocks_close's own single-home shape one edge-type over, and the new claim-time
-- blockers function joins it to ledger_current exactly as work_edge_obligation already does for
-- the two pre-existing edge kinds.
--
-- WHY (operator-side prose; NOT subject-visible): s30 typed a "must resolve before CLOSE" edge
-- (blocks-close) but named no "must resolve before START (claim)" edge at all -- an agent (or a
-- human) could claim a work item whose real precondition (a prerequisite item's own completion)
-- was never checked at the moment that matters most: BEFORE work begins, not after. The gap is
-- exactly the maintainer's own commission text: a hook can refuse an illegal *tool call*
-- (decomposition_review, permit_to_work), but nothing in the kernel refused an illegal *claim* --
-- so "started before its precondition" was representable, and a claim-time hook had no ledger
-- fact to check it against. This delta gives the CLI (and any future hook) exactly that fact:
-- edge_type='blocks-start' on a work_depends_on row, checked at INSERT time on the DEPENDENT'S OWN
-- work_claimed row, refused by name with the right next act.
--
-- ELEMENT 1 -- edge_type VOCABULARY WIDENED (spec-equivalent to s30's own Element 1, one value
-- wider). The CHECK is flat (no kind test, s30's own shape, out of gates/kind_shape_manifest_gate.py's
-- (kind,column,arity) MANIFEST scope exactly like work_review_disposition_check -- s30's edge_type_
-- kind_shape, the SEPARATE (kind,column,arity) CHECK that scopes the column to kind='work_depends_on'
-- at all, is UNTOUCHED here: blocks-start rides the SAME column, the SAME kind-scoping, no new
-- MANIFEST row is needed). 'supersedes' stays actively refused (s30's own REVIEW NOTE DISPOSITION,
-- unchanged).
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

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS edge_type_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT edge_type_check CHECK (
    edge_type IS NULL OR edge_type IN ('blocks-close', 'blocks-start', 'informs'));
    -- 'supersedes' deliberately excluded from this list -- reserved, not merely unlisted (s30 header).

COMMENT ON CONSTRAINT edge_type_check ON :"schema".ledger IS
  'kernel/lineage/s39-blocks-start.sql: widens s30''s two-value vocabulary to a third,
   claim-time-refused value, blocks-start -- the antecedent must reach CLOSED before the dependent
   may be CLAIMED (work_claimed INSERT refused otherwise, Element 3 below). Disjoint from
   blocks-close (which gates CLOSE, not claim) and informs (never gates anything). See
   kernel/lineage/s30-typed-dependency-edges.sql for the pre-existing two-value CHECK this widens.';

-- ============================================================================================
-- ELEMENT 1b -- work_edge_blocks_start -- the ONE home of the new blocks-start edge relation
-- (s32's own single-home pattern, ADR-0012 P1, one edge kind over from work_edge_blocks_close).
-- RAW (every work_depends_on row with edge_type='blocks-start', retracted or not) -- same
-- reasoning as work_edge_blocks_close/work_edge_parent's own RAW posture (s32 header WHY): the
-- construction-time cycle refusal below (Element 2) needs the UNRETRACTED reading (a retracted
-- edge still occupies its slug-pair's place in the induction argument over insertion order,
-- mirroring work_depends_on_would_cycle's own s30 precedent exactly).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_edge_blocks_start
    WITH (security_invoker = true) AS
SELECT dep.work_slug AS dependent_slug, dep.work_depends_on AS antecedent_slug, dep.id AS edge_row_id
FROM   :"schema".ledger dep
WHERE  dep.kind = 'work_depends_on' AND dep.edge_type = 'blocks-start';

COMMENT ON VIEW :"schema".work_edge_blocks_start IS
  'Single home (kernel/lineage/s39-blocks-start.sql, ADR-0012 P1, mirroring s32''s
   work_edge_blocks_close one edge-type over) of the blocks-start edge relation: an edge walks
   DEPENDENT -> ANTECEDENT opposite its own column names (the DEPENDENT plays the walk-from role;
   the ANTECEDENT is the tree member reached -- s29/s30/s31''s own direction-flip comment,
   inherited). RAW -- includes every blocks-start edge ever written, retracted or not, matching
   work_edge_blocks_close''s own raw reading (s32) exactly. edge_row_id is the work_depends_on
   row''s own ledger id.';

GRANT SELECT ON :"schema".work_edge_blocks_start TO :"role";

-- ============================================================================================
-- ELEMENT 2 -- work_blocks_start_would_cycle(dependent, antecedent) -- the construction-time
-- cycle refusal over the blocks-start subgraph, mirroring work_depends_on_would_cycle (s30) one
-- edge-type over. depth-capped (10000), matching every would_cycle function in this lineage.
--
-- THE CYCLE-QUESTION DECISION (this delta's own design choice, named and defended per this
-- commission's own instruction -- both options were defensible, this is the one taken):
-- BLOCKS-START GETS ITS OWN, SEPARATE construction-time cycle refusal, over its OWN subgraph --
-- it is NOT merged into blocks-close's own gating subgraph (work_depends_on_would_cycle /
-- blocks_close_cycle), and it does NOT extend dependency_cycle (the untyped, cross-type raw
-- graph) to treat blocks-start specially either. Two independent grounds:
--   (a) MIXING WOULD FALSE-POSITIVE. A work item A that is blocks-close-dependent on B, while B
--       is blocks-start-dependent on A, is NOT a genuine deadlock -- the two obligations fire at
--       different lifecycle moments (A cannot CLOSE until B resolves; B cannot be CLAIMED until A
--       is CLOSED) and are jointly satisfiable in the ordinary case (open A, open B, claim+close A,
--       then claim B). A single merged DAG-over-both-types check would refuse this legal
--       construction as a false cycle.
--   (b) A BLOCKS-START-ONLY CYCLE IS ITS OWN, ARGUABLY WORSE, FAILURE CLASS AND DESERVES ITS OWN
--       DEDICATED CHECK, NOT A SHARED ONE. A blocks-close cycle (already refused at construction,
--       s30) forecloses CLOSING every member of the cycle forever -- but every member can still be
--       OPENED, CLAIMED, and WORKED ON; the deadlock is soft, a permanently-open item is a legal,
--       if unusual, standing state. A blocks-start cycle forecloses CLAIMING every member forever
--       (each member's own claim precondition is another cycle member's own CLOSE, which in turn
--       needs a claim first -- no member can ever legally enter the claimed state at all): a hard,
--       total deadlock on the very act of STARTING work, structurally worse than the close-only
--       case this delta's own commission flags. Refusing it independently, at construction, with
--       its own dedicated function and its own dedicated defense-in-depth view member (Element 4
--       below), gives it the SAME strength blocks-close's own cycle already has, without diluting
--       either check's precision by conflating two obligations that are not, in general, the same
--       graph.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_blocks_start_would_cycle(dependent_slug text, antecedent_slug text)
    RETURNS boolean LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE reach(slug, depth) AS (
    SELECT antecedent_slug, 0
    UNION ALL
    SELECT e.antecedent_slug, r.depth + 1
    FROM reach r
    JOIN work_edge_blocks_start e ON e.dependent_slug = r.slug
    WHERE r.depth < 10000
  )
  SELECT EXISTS (SELECT 1 FROM reach WHERE slug = dependent_slug);
$fn$;

-- ============================================================================================
-- ELEMENT 3 -- validate_work_item_depends (the s35 LEAF, CREATE OR REPLACE -- ADR-0012 P1, not a
-- second copy) GAINS a blocks-start branch, structurally mirroring the pre-existing blocks-close
-- branch: self-edge / dangling-antecedent / cycle, all refused at construction. The pre-existing
-- default-then-check pair (edge_type NULL -> 'informs', then the blocks-close branch) is
-- BYTE-IDENTICAL below, unchanged; the new branch is appended.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_depends(r :"schema".ledger)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF r.edge_type IS NULL THEN
    r.edge_type := 'informs';
  END IF;
  IF r.edge_type = 'blocks-close' THEN
    IF r.work_depends_on = r.work_slug THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot have a blocks-close dependency on itself — a self-edge is refused at construction for blocks-close (s30). informs edges are not subject to this refusal.', r.work_slug;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = r.work_depends_on) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' names a blocks-close antecedent ''%'' which has no opening act — a blocks-close edge requires BOTH endpoints to be close-tracked work items (s30), unlike an informs edge''s deliberately lax posture (s22). Open the antecedent first, or retry as --type informs.', r.work_slug, r.work_depends_on;
    ELSIF work_depends_on_would_cycle(r.work_slug, r.work_depends_on) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot take a blocks-close dependency on ''%'' — ''%'' already (transitively) has a blocks-close dependency on ''%'', so this edge would create a cycle; the obligation AND-tree must be a DAG or conjunction has no fixpoint (s30). informs edges are not subject to this refusal.', r.work_slug, r.work_depends_on, r.work_depends_on, r.work_slug;
    END IF;
  END IF;
  -- s39: the blocks-start branch, structurally mirroring blocks-close above one edge-type over.
  -- See Element 2's own header for why this cycle check is INDEPENDENT of blocks-close's.
  IF r.edge_type = 'blocks-start' THEN
    IF r.work_depends_on = r.work_slug THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot have a blocks-start dependency on itself — a self-edge is refused at construction for blocks-start (s39), mirroring blocks-close''s own self-edge refusal (s30). informs edges are not subject to this refusal.', r.work_slug;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = r.work_depends_on) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' names a blocks-start antecedent ''%'' which has no opening act — a blocks-start edge requires BOTH endpoints to be close-tracked work items (s39, mirroring s30''s blocks-close posture), unlike an informs edge''s deliberately lax posture (s22). Open the antecedent first, or retry as --type informs.', r.work_slug, r.work_depends_on;
    ELSIF work_blocks_start_would_cycle(r.work_slug, r.work_depends_on) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot take a blocks-start dependency on ''%'' — ''%'' already (transitively) has a blocks-start dependency on ''%'', so this edge would create a cycle in the blocks-start subgraph; unlike a blocks-close cycle (which only forecloses CLOSING, leaving every member still claimable), a blocks-start cycle would foreclose CLAIMING every member forever, so it is refused at construction INDEPENDENTLY of blocks-close''s own cycle check (s39 -- the two edge types'' DAG requirements are verified over separate subgraphs; see kernel/lineage/s39-blocks-start.sql''s own Element 2 header for why they are not merged). informs edges are not subject to this refusal.', r.work_slug, r.work_depends_on, r.work_depends_on, r.work_slug;
    END IF;
  END IF;
  RETURN r;
END; $fn$;

-- ============================================================================================
-- ELEMENT 4 -- work_item_blocks_start_blockers(root_slug) -- the ONE home of "which of root_slug's
-- OWN blocks-start antecedents are not yet resolved (closed)". DIRECT antecedents only, NOT a
-- transitive tree walk -- named as a LIMIT (see the file-level LIMITS section below), not silently
-- assumed either way: the commission's own text ("the item has an unresolved blocks-start
-- antecedent (antecedent's work item not closed)") reads as a direct-edge precondition, and a
-- direct check is the smaller, more legible claim-time gate -- a future delta wanting the
-- transitive form has this function's own signature to widen, not a second one to mint.
-- IN-FORCE ONLY (each edge's own carrying row joined to ledger_current, s32's own pattern) --
-- a retracted blocks-start edge no longer blocks anything, exactly like every other in-force
-- edge reading in this lineage.
-- ============================================================================================
-- NOTE (found live, this delta's own first scratch-witness attempt): a LANGUAGE sql function body
-- inside $fn$...$fn$ is NOT a site psql performs :"var" substitution in (confirmed empirically --
-- every pre-existing function body in this lineage relies on SET search_path for unqualified name
-- resolution instead, never a :"schema" prefix inside a dollar-quoted body; this function follows
-- that SAME house idiom, unqualified names resolving via the SET search_path clause below).
CREATE OR REPLACE FUNCTION :"schema".work_item_blocks_start_blockers(root_slug text)
    RETURNS TABLE(blocking_slug text, reason text) LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  SELECT e.antecedent_slug, 'item is not yet closed'::text
  FROM   work_edge_blocks_start e
  JOIN   ledger_current lc ON lc.id = e.edge_row_id
  WHERE  e.dependent_slug = root_slug
    AND  NOT EXISTS (
           SELECT 1 FROM work_item_current wic
           WHERE wic.slug = e.antecedent_slug AND wic.state = 'closed'
         );
$fn$;

COMMENT ON FUNCTION :"schema".work_item_blocks_start_blockers(text) IS
  'kernel/lineage/s39-blocks-start.sql: root_slug''s own DIRECT, in-force blocks-start antecedents
   that have not yet reached state=closed (work_item_current). Direct only, not transitive -- see
   this file''s own LIMITS section. The claim-time trigger (validate_work_item_claim below) and
   work_startable (Element 5) both compose with this, never re-deriving the predicate inline.';

-- ============================================================================================
-- ELEMENT 3 (claim-time refusal) -- validate_work_item_claim -- A NEW LEAF, added to s35's
-- dispatcher-with-leaves decomposition (kernel/lineage/s35-validation-decomposition.sql), NOT a
-- reversion to any earlier shape -- mirroring s37's own "a FIFTH LEAF" precedent (that file's own
-- Element 2 header) for adding a new per-concern leaf without touching the four/five pre-existing
-- ones. Refuses a work_claimed INSERT when root_slug carries any unresolved blocks-start
-- antecedent, naming EVERY unresolved antecedent slug (string_agg, mirroring work_item_strict_
-- blockers'/validate_work_item_close's own teach-text idiom exactly) and the two honest next acts:
-- resolve the antecedent, or re-edge if the dependency itself is wrong.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_claim(r :"schema".ledger)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
BEGIN
  SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
    INTO blockers
    FROM work_item_blocks_start_blockers(r.work_slug) b;
  IF blockers IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: claim of work item ''%'' refused — its blocks-start antecedent(s) are not yet resolved: %. Claim and finish each named antecedent first (./led work claim <antecedent>, then ./led work close <antecedent> <resolution> ...), or -- if the dependency itself is wrong -- correct the record (see design/USER-RECIPES-FAQ.md''s "Correcting the record" section for the supersession recipe: the mistaken work_depends_on row is superseded, then a fresh row is issued with the right edge_type) (s39: claim-time precondition foreclosure, direct antecedents only — see work_item_blocks_start_blockers''s own LIMITS).', r.work_slug, blockers;
  END IF;
  RETURN r;
END; $fn$;

-- ============================================================================================
-- THE DISPATCHER, RE-ISSUED (CREATE OR REPLACE, the SAME function s35 defined, s37/s38 extended --
-- ADR-0012 P1): ONE new call to the new leaf, under the SAME "has this slug ever been opened"
-- shared precondition every non-open, non-disposition kind already goes through -- a claim, like a
-- depends-edge or a close, requires the slug to have an opening act first; this delta adds no new
-- precondition of its own, it adds a new CHECK performed AFTER that shared gate, exactly where the
-- depends/close leaves are already called. Every other line is BYTE-IDENTICAL to s38's own
-- dispatcher (unchanged since s37).
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
    IF NEW.kind = 'work_claimed' THEN
      NEW := validate_work_item_claim(NEW);
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
-- ELEMENT 5 -- work_startable -- the "what can I legitimately start right now" derived view:
-- open, unclaimed work items whose blocks-start antecedents (if any) are ALL resolved (closed).
-- Read-only, current-truth-typed throughout (composes with work_item_current and
-- work_item_blocks_start_blockers, no raw `ledger` reference of its own -- classifies clean under
-- gates/ledger_reader_allowlist.py with no allowlist entry needed).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_startable
    WITH (security_invoker = true) AS
SELECT wic.slug, wic.title
FROM   :"schema".work_item_current wic
WHERE  wic.state = 'open' AND wic.claimant IS NULL
  AND  NOT EXISTS (SELECT 1 FROM :"schema".work_item_blocks_start_blockers(wic.slug));

COMMENT ON VIEW :"schema".work_startable IS
  'kernel/lineage/s39-blocks-start.sql: open, unclaimed work items whose blocks-start antecedents
   (direct, in-force) are all resolved (closed) -- the honest "what can I legitimately claim right
   now" read. An item with no blocks-start antecedents at all is vacuously startable (NOT EXISTS
   over an empty blockers set), matching claim''s own construction-time posture: no blocks-start
   edge means no claim-time refusal.';

GRANT SELECT ON :"schema".work_startable TO :"role";

-- ============================================================================================
-- ELEMENT 6 -- work_item_violations (s22, extended s28/s30/s31/s33/s37, re-issued s32/s37/s38 --
-- CREATE OR REPLACE, the SAME view -- ADR-0012 P1) GAINS ONE MEMBER, blocks_start_cycle -- pure
-- defense-in-depth (already refused at construction, Element 3 above), mirroring blocks_close_
-- cycle's own precedent (s30) exactly one edge-type over. Every pre-existing CTE and every
-- pre-existing member's EXECUTABLE SQL is byte-identical below (comment-stripped diff against
-- s37 v3, unaltered by s38, per this file's own PREREQUISITE section) -- only the two new CTEs
-- (blocks_start_deps/bs_reach/blocks_start_cycle) and the one new UNION ALL arm are appended.
-- s37's OWN hazard/design-rationale comments on the pre-existing CTEs are CARRIED FORWARD
-- verbatim below (restored in this file after a review catch: an earlier pass of this re-issue
-- had dropped them while re-typing the view text by hand -- the code was never wrong, only the
-- comments guarding it went missing; see this delta's own commit history for the fix). The v3
-- final gate (`JOIN ledger_current tgt ON tgt.id = rv.target_id`) covers the new arm
-- automatically, with no edit of its own -- it is written once, over `raw_violations` as a
-- whole, not per-arm.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_violations
    WITH (security_invoker = true) AS
WITH RECURSIVE
  opens_cur AS (
    SELECT work_slug AS slug, count(*) AS n
    FROM :"schema".ledger_current WHERE kind = 'work_opened'
    GROUP BY work_slug
  ),
  dup_open AS (
    SELECT slug FROM opens_cur WHERE n > 1
  ),
  shipped_no_witness AS (
    SELECT work_slug AS slug, id
    FROM :"schema".ledger_current
    WHERE kind = 'work_closed' AND work_resolution = 'shipped'
      AND (work_witness IS NULL OR btrim(work_witness) = '')
  ),
  -- s37 fix (reviewer-witnessed defect 1, ADR-0014-review round; UNCHANGED by v3): `deps` gains
  -- the depending act's OWN ledger id -- the SAME "violating act's own row" reading target_id
  -- already uses everywhere else an id is natural. v3: reads ledger_current, not raw ledger --
  -- a retracted depends_on row is no longer even a CANDIDATE dangling-dep, matching the amendment
  -- (this is the TARGET row's own currency -- element 1's actual gate).
  deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent, id
    FROM :"schema".ledger_current WHERE kind = 'work_depends_on'
  ),
  -- v3 CORRECTNESS NOTE (found in this delta's own build, hazard-in-reach per CLAUDE.md's
  -- engineering-responsibility corollary): the antecedent-opened check below reads RAW `ledger`,
  -- UNCHANGED from v2 -- deliberately NOT switched to ledger_current. Element 1 gates lapsing on
  -- the MEMBER'S OWN TARGET ROW currency (d.id, via `deps` above) ONLY; it does not redefine the
  -- INNER PREDICATE (whether the antecedent was ever opened). Switching this NOT EXISTS check to
  -- ledger_current would make it fire for "antecedent was opened, then later retracted" too -- a
  -- case history's OWN unfiltered computation (work_violation_history, unchanged, same raw check)
  -- can NEVER produce, since that condition has no raw-history counterpart at all -- breaking
  -- "the record is never thinner than work_item_violations" in the WRONG direction (debt showing
  -- a member history structurally cannot represent). Kept raw so DEBT's member set is always the
  -- in-force-target SUBSET of HISTORY's raw member set, never a superset.
  dangling_dep AS (
    SELECT d.dependent AS slug, d.antecedent, d.id
    FROM deps d
    WHERE NOT EXISTS (SELECT 1 FROM :"schema".ledger o
                       WHERE o.kind = 'work_opened' AND o.work_slug = d.antecedent)
  ),
  -- v3: work_edge_blocks_close (s32's RAW single home) JOINed to ledger_current on edge_row_id --
  -- the edge's own carrying row must be in force, matching work_edge_obligation's own composition
  -- one file over (s32) and orphan_children's own pre-existing pattern one CTE below.
  bc_deps AS (
    SELECT e.dependent_slug AS dependent, e.antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_close e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
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
    SELECT e.child_slug AS slug, e.parent_slug, e.edge_row_id
    FROM :"schema".work_edge_parent e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
  ),
  -- v3 CORRECTNESS NOTE (same hazard as dangling_dep's own comment above, same fix): the
  -- parent-opened check below reads RAW `ledger`, UNCHANGED from v2. `parents` above already
  -- carries the TARGET row's own currency gate (edge_row_id JOINed to ledger_current -- the
  -- child's own opening act, this class's actual target per the header DESIGN CHOICE). Switching
  -- THIS NOT EXISTS check to ledger_current would make dangling_parent fire for "parent was
  -- opened, then retracted" -- exactly orphaned_by_retraction's own territory, and a shape
  -- work_violation_history's unchanged raw computation can never reproduce (same "debt showing a
  -- member history cannot represent" defect dangling_dep's comment names). Kept raw.
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
    SELECT e.dependent_slug AS dependent, e.antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_close e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
  ),
  bc_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_close_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bc_reach r JOIN blocks_close_deps d ON d.dependent = r.cur
  ),
  blocks_close_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bc_reach WHERE cur = start_slug
  ),
  -- s39 Element 6 -- the NEW blocks-start defense-in-depth cycle CTEs, structurally identical to
  -- blocks_close_deps/bc_reach/blocks_close_cycle immediately above, one edge-type over.
  blocks_start_deps AS (
    SELECT e.dependent_slug AS dependent, e.antecedent_slug AS antecedent
    FROM :"schema".work_edge_blocks_start e
    JOIN :"schema".ledger_current lc ON lc.id = e.edge_row_id
  ),
  bs_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_start_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bs_reach r JOIN blocks_start_deps d ON d.dependent = r.cur
  ),
  blocks_start_cycle AS (
    SELECT DISTINCT start_slug AS slug FROM bs_reach WHERE cur = start_slug
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
  -- s37 Element 1/3, v3-rederived -- raw_violations: every arm above, PLUS its target_id (the
  -- natural row id where one exists; the slug's own CURRENT work_opened row id otherwise --
  -- header DESIGN CHOICE). Every target_id subquery below now reads ledger_current, so a handle
  -- whose own opening act is retracted resolves to NULL here (excluded downstream by the final
  -- target-in-force join, same as any other lapsed member).
  raw_violations AS (
    SELECT 'duplicate_open'::text AS violation, slug, NULL::text AS detail,
           (SELECT min(id) FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = dup_open.slug) AS target_id
    FROM dup_open
    UNION ALL
    SELECT 'shipped_without_witness', slug, 'ledger row ' || id, id FROM shipped_no_witness
    UNION ALL
    SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent, id FROM dangling_dep
    UNION ALL
    SELECT 'dependency_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = dep_cycle.slug) AS target_id
    FROM dep_cycle
    UNION ALL
    SELECT 'dangling_parent', slug, 'parent ' || parent_slug || ' has no opening act', edge_row_id
    FROM dangling_parent
    UNION ALL
    SELECT 'parent_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = parent_cycle.slug) AS target_id
    FROM parent_cycle
    UNION ALL
    SELECT 'blocks_close_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = blocks_close_cycle.slug) AS target_id
    FROM blocks_close_cycle
    UNION ALL
    -- s39 Element 6 -- the NEW arm. Same target_id resolution as blocks_close_cycle immediately
    -- above (the slug's own current work_opened row id, s37's own DESIGN CHOICE for a slug-keyed
    -- member with no single violating row).
    SELECT 'blocks_start_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger_current WHERE kind = 'work_opened' AND work_slug = blocks_start_cycle.slug) AS target_id
    FROM blocks_start_cycle
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
  -- s37 Element 3 (A4), v3-corrected -- dispositions IN FORCE, and whether each one's OWN
  -- checkable basis STILL holds, re-derived on every read (never a stored verdict):
  --   retired : holds while the target row's own acts still read settled. If the target is a
  --             work_opened row (the four slug-keyed arms + orphan_children), "settled" means its
  --             own slug currently reads 'closed' in work_item_current -- so a LATER-superseded
  --             close on that slug flips this back to false in the SAME read (A4's own example,
  --             verbatim, still fully live under v3 -- the CHILD's own opening row stays current
  --             throughout this scenario, only its CLOSE row's currency changes). For every other
  --             kind of target row (claim/dep/close/edge row), "settled" holds unconditionally
  --             once retired (no named resurrectable condition for those classes -- element 3/
  --             consult 2D: only retired-on-a-settled-child and reissued name a condition at all).
  --   reissued: holds while EITHER no successor was cited (nothing to invalidate -- element 4's
  --             own "warns, never refused" posture) OR the cited successor row is itself still
  --             in force (ledger_current).
  -- v3 NOTE on the `JOIN ledger_current t` below (consult part 2D: "remove the unconditional
  -- target-currency requirement"): this join is KEPT, not deleted, but it can no longer PRODUCE
  -- v2's defect, by construction -- PROOF: disposition_basis_holds is consulted ONLY via the
  -- final anti-join against `raw_violations rv` (below), and every rv.target_id is ALREADY
  -- current (every CTE feeding raw_violations above reads ledger_current exclusively, so a
  -- retracted target never produces an rv row to match against in the first place). So whenever
  -- this join's WHERE clause actually gets evaluated for a (class, target_id) pair that matters,
  -- `t` is GUARANTEED to be found -- the join can never again FALSIFY a basis that would
  -- otherwise hold. A disposition whose target is later retracted is MOOT (its rv row already
  -- gone upstream), never DEFEATED by this join finding no match -- exactly "moot, never
  -- defeated" (spec Element 3, consult part 2D), achieved structurally rather than by deleting
  -- the join and re-deriving t's static kind/work_slug off raw ledger (which would reintroduce a
  -- raw-ledger leg into THIS view, undoing the current-truth retype gates/ledger_reader_
  -- allowlist.py now expects -- see that file's own s37 entry).
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
-- v3 Element 1 -- the EXPLICIT target-in-force gate: redundant with raw_violations' own
-- current-truth construction above (every target_id it emits is already current or NULL), kept
-- as the ONE textual anchor a future arm's author must preserve (matching Element 3's own "one
-- join... not a procedure" idiom) -- "a member lapses when its target row leaves ledger_current"
-- is now true by TWO independent readings of this view's text, not one.
JOIN   :"schema".ledger_current tgt ON tgt.id = rv.target_id
WHERE  NOT EXISTS (
         SELECT 1 FROM disposition_basis_holds dbh
         WHERE dbh.class = rv.violation AND dbh.target_id = rv.target_id
       );

COMMENT ON VIEW :"schema".work_item_violations IS
  'kernel/lineage/s39-blocks-start.sql (s37 v3 body + ONE new member, blocks_start_cycle):
   defense-in-depth mirror of blocks_close_cycle one edge-type over -- already refused at
   construction (validate_work_item_depends'' blocks-start branch, s39 Element 3). See
   kernel/lineage/s37-violation-disposition.sql for the v3 debt-projection semantics this view
   inherits unchanged.';

-- ============================================================================================
-- work_violation_history (s37, THE declared raw/history reader -- unfiltered, never narrowed)
-- RE-ISSUED to add the SAME blocks_start_cycle shape, raw/unfiltered, mirroring blocks_close_
-- cycle's own raw arm in this same view exactly one edge-type over. Every pre-existing CTE and
-- arm's EXECUTABLE SQL is byte-identical below; only the two new CTEs and the one new UNION ALL
-- arm are appended. s37's OWN comments on the pre-existing CTEs/arms are carried forward
-- verbatim (restored in this file after a review catch -- see Element 6's own header above for
-- the same note, which applies here too).
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
  -- s37 fix (reviewer-witnessed defect 1, ADR-0014-review round; same fix as the view's own
  -- `deps`/`dangling_dep` above -- see that CTE's own comment for why `id` is required).
  deps AS (
    SELECT work_slug AS dependent, work_depends_on AS antecedent, id
    FROM :"schema".ledger WHERE kind = 'work_depends_on'
  ),
  dangling_dep AS (
    SELECT d.dependent AS slug, d.antecedent, d.id FROM deps d
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
  -- s39 -- the raw/unfiltered blocks-start mirror, one edge-type over.
  blocks_start_deps AS (
    SELECT dependent_slug AS dependent, antecedent_slug AS antecedent FROM :"schema".work_edge_blocks_start
  ),
  bs_reach(start_slug, cur) AS (
    SELECT dependent, antecedent FROM blocks_start_deps
    UNION
    SELECT r.start_slug, d.antecedent FROM bs_reach r JOIN blocks_start_deps d ON d.dependent = r.cur
  ),
  blocks_start_cycle AS (SELECT DISTINCT start_slug AS slug FROM bs_reach WHERE cur = start_slug),
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
    SELECT 'depends_on_unknown_slug', slug, 'depends on ' || antecedent, id FROM dangling_dep
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
    -- s39 -- the new raw/unfiltered arm.
    SELECT 'blocks_start_cycle', slug, NULL,
           (SELECT id FROM :"schema".ledger WHERE kind = 'work_opened' AND work_slug = blocks_start_cycle.slug)
    FROM blocks_start_cycle
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
-- v3 amendment (element 2 / consult part 2C): two ADDITIVE columns, appended after the
-- pre-existing disposition_in_force (a pure column-list widening of an already-declared-history
-- view -- HISTORY: safe, no existing column touched). target_in_force names whether rv.target_id
-- itself still reads current -- the direct, attributable answer to "is this member's target row
-- still standing" that work_item_violations' own narrowing computes but never surfaced before.
-- target_retraction_id names the SPECIFIC ledger row that superseded (retracted) the target, when
-- one exists -- the "a retraction, a disposition, or open debt" trichotomy (spec element 2,
-- verbatim) now fully attributable in ONE row: target_in_force=false + target_retraction_id set
-- is the retraction story; a disposition_id with disposition_in_force=true is the disposition
-- story; neither is open debt (assuming target_in_force is also true, i.e. a live, unanswered
-- violation). A member can show BOTH a retraction and a disposition trail (e.g. a corrected
-- disposition superseded before the target itself was later retracted) -- the record stays
-- complete, never collapsed to one story.
SELECT rv.violation, rv.slug, rv.detail, rv.target_id,
       d.id AS disposition_id, d.work_resolution AS disposition_resolution,
       d.rationale AS disposition_basis, d.work_violation_witness AS disposition_witness,
       (d.id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = d.id)) AS disposition_in_force,
       EXISTS (SELECT 1 FROM :"schema".ledger_current tgt WHERE tgt.id = rv.target_id) AS target_in_force,
       (SELECT s3.id FROM :"schema".ledger s3 WHERE s3.supersedes = rv.target_id) AS target_retraction_id
FROM   raw_violations rv
LEFT JOIN :"schema".ledger d
       ON d.kind = 'work_violation_disposition'
      AND d.work_violation_class = rv.violation
      AND d.work_violation_target_id = rv.target_id
ORDER BY rv.violation, rv.slug, d.id;

COMMENT ON VIEW :"schema".work_violation_history IS
  'kernel/lineage/s37-violation-disposition.sql, re-issued by s39 to add the blocks_start_cycle
   raw/unfiltered arm (mirroring blocks_close_cycle one edge-type over) -- UNFILTERED read, every
   work_item_violations member ever surfaced, never thinner. See s37''s own header for the full
   semantics this view carries unchanged.';

GRANT SELECT ON :"schema".work_violation_history TO :"role";

-- ============================================================================================
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: a work_depends_on row's edge_type is one of THREE constructors -- blocks-close
--     (gates CLOSE, s30, unchanged), informs (gates nothing, s22, unchanged), or blocks-start
--     (gates CLAIM: a work_claimed INSERT for the dependent slug is refused at construction while
--     any direct, in-force blocks-start antecedent has not reached state=closed,
--     validate_work_item_claim, this delta) -- or the row is refused at construction if it
--     attempts a fourth value (the still-closed vocabulary CHECK), a self-edge on blocks-start
--     (validate_work_item_depends' new branch), a dangling blocks-start antecedent (same branch),
--     or a blocks-start cycle (work_blocks_start_would_cycle, its own independent subgraph per
--     this file's Element 2 decision). work_startable derives, read-only, the open+unclaimed items
--     whose blocks-start antecedents are all resolved.
--
--   - QUANTIFICATION UNIVERSE -- enumerated OUTWARD (ADR-0000's own 2026-07-02 amendment text,
--     re-read against every kind that carries every column this delta constrains, not merely the
--     kind the feature is FOR -- the s38-week lesson this commission's own brief names explicitly):
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table, no new column (the
--         blocks-start fact rides the EXISTING edge_type column, s30's own column, widened by one
--         value -- exactly the s30/s38 precedent for a pure vocabulary widening).
--       EVERY KIND THAT CARRIES edge_type: exactly ONE, work_depends_on (edge_type_kind_shape,
--         s30, UNCHANGED by this delta -- the column's kind-scoping is untouched, only its
--         legal-VALUE set on that one kind widens). No other kind carries this column; re-verified
--         against the full CHAIN (s22..s38), not merely asserted.
--       EVERY KIND THAT CARRIES work_review_disposition/work_review_ref (the OTHER two-kind-shared
--         columns in this lineage, s37/s38's own precedent for what "enumerate outward" catches):
--         work_closed and work_violation_disposition (s37/s38). This delta touches NEITHER column
--         at all -- named here, explicitly, as the negative check the s38-week lesson demands: a
--         claim-time refusal is a NEW leaf/branch on DIFFERENT columns (edge_type, and the
--         work_claimed kind's own pre-existing shape), not a value on either of those two shared
--         columns, so no widening of either is needed or attempted by this delta.
--       VIEWS re-read for the wildcard/column-complete class (s20/s22/.../s38 all named):
--         ledger_current / countersigned_in_force -- explicit column lists (s20+). NEITHER gains a
--         column here (this delta adds no column, only a new legal VALUE on edge_type, already
--         listed on both views since s30) -- re-verified NOT members needing re-issue.
--         work_item_current -- re-verified NOT a member: it carries no edge_type-derived column
--         and needs none (work_startable reads it directly for state/claimant, unchanged).
--       KIND VOCABULARY -- unchanged. This delta adds no new `kind` value: the claim-time refusal
--         fires on the EXISTING work_claimed kind (s22), and the new edge value rides the EXISTING
--         work_depends_on kind (s22/s30).
--       GRANTS -- mirrors s30/s32's own posture: the two NEW views (work_edge_blocks_start,
--         work_startable) each get a fresh GRANT SELECT (security_invoker views compose through
--         invoker privilege, s32's own house rule); the re-issued edge_type_check/validate_work_
--         item_depends/validate_work_item/work_item_violations/work_violation_history keep their
--         EXISTING grants (s21's additive-column-order idiom: zero columns added or removed
--         anywhere in this delta). work_blocks_start_would_cycle/work_item_blocks_start_blockers/
--         validate_work_item_claim need no explicit GRANT (Postgres grants EXECUTE to PUBLIC by
--         default, verified against work_depends_on_would_cycle''s own s30 precedent, which
--         received none either).
--       ENGINE -- VERIFIED, not merely asserted (per this commission's own instruction to check
--         engine/lp/ and engine/ledger_*.py for edge_type enumeration): `engine/ledger_edb.py`'s
--         `work_dep_type/2` fact emission (lines ~412-415) is FULLY GENERIC -- it emits
--         `work_dep_type(rid, etype)` for WHATEVER value the `edge_type` column carries, with no
--         hardcoded value list to widen; a blocks-start-typed row already round-trips through it
--         with zero engine-layer edits. `engine/lp/work_items.lp`'s own blocks-close-specific DAG
--         predicate (`work_dep_star_bc/2`, feeding `work_dependency_cycle/1`) and its SQL floor
--         twin (`engine/ledger_floor.py`'s `bc_deps_cte`) are SPECIFICALLY SCOPED to blocks-close
--         (they feed dependency_cycle's OWN narrowing, s37 sibling narrowing) -- and, verified by
--         grep against both files, NEITHER `parent_cycle` NOR `blocks_close_cycle` (this delta's
--         own direct structural precedent, s28/s30's defense-in-depth cycle members) has ANY ASP-
--         side counterpart at all: `SUPPORTED_KIND` in `engine/ledger_floor.py` and every emitted
--         predicate name in `engine/lp/work_items.lp` cover only `work_duplicate_open`,
--         `work_shipped_without_witness`, `work_depends_on_unknown`, `work_dependency_cycle`, and
--         `work_orphaned_by_retraction` -- the two pre-existing construction-time-refused,
--         defense-in-depth cycle members (parent_cycle, blocks_close_cycle) are OUT OF the SQL/ASP
--         differential's own compared-atom scope BY EXISTING, RATIFIED PRECEDENT (their own
--         comments in both files say so explicitly). `blocks_start_cycle`, this delta's own new
--         member, is the SAME SHAPE -- a construction-time-refused, defense-in-depth cycle member,
--         never itself a T_now derivation `judge` compares -- so it inherits that SAME precedent
--         and needs NO new engine/lp/ predicate or floor CTE, matching s30/s32/s33's own identical
--         "ENGINE -- NONE" disclosure for their own construction-time-only refusals. `./judge`'s
--         existing SQL/ASP differential is UNAFFECTED by this delta (it derives T_now facts from
--         kind/status/supersedes/edge_type-generic-passthrough/etc., none of which this delta's
--         own new CHECK/branch/view narrows or widens in a way any compared atom depends on) and
--         continues to AGREE -- witnessed as part of this delta's own acceptance (see the commit
--         record).
--
--   - DENOMINATION: edge_type stays `text`, closed vocabulary (blocks-close|blocks-start|informs),
--     never a boolean (s30's own reasoning, unchanged: a boolean would force a disruptive
--     boolean-to-enum migration the moment a fourth value is ever ratified). The claim-time
--     precondition itself is denominated in work_item_current.state='closed' (the SAME state
--     vocabulary work_item_strict_blockers' 'item is not yet closed' reason string already uses,
--     s29 -- never a second, competing "resolved" vocabulary minted for blocks-start alone).
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE. This
-- delta ONLY adds vocabulary (one new edge_type value), refusals (self-edge/dangling-antecedent/
-- cycle on construction, unresolved-antecedent on claim), and derived views/functions
-- (work_edge_blocks_start, work_startable, work_item_blocks_start_blockers,
-- work_blocks_start_would_cycle, the blocks_start_cycle defense-in-depth member) -- nothing
-- existing is relaxed: every pre-existing branch of validate_work_item_depends/validate_work_item
-- and every pre-existing arm of work_item_violations/work_violation_history is byte-identical
-- above, and the edge_type_check widening only ADDS a legal value, disjoint from the pre-existing
-- two, exactly the s30-precedent shape the standing ruling's own text names as the paradigm case
-- ("the new column defaults fail-safe... the new refusals are all NEW... a stricter reading...
-- never a laxer one"). Per the standing ruling this qualifies for entry into the birth chain
-- without a per-delta maintainer question, PENDING the scratch-witness-on-both-polarities-with-
-- SQL/ASP-AGREE this delta's own commission requires and this file's own witness pass (below)
-- performs -- named here for the record, not claimed as a bypass of that witness.
--
-- LIMITS (pre-registered, matching s22/.../s38's own disclosure convention):
--   - work_item_blocks_start_blockers checks DIRECT antecedents only, never a transitive walk --
--     named explicitly above (Element 4's own header) as a deliberate, filed scope choice, not a
--     silent omission. A future delta wanting the transitive form widens this function's own body
--     (and validate_work_item_claim's caller, unchanged), not a second mechanism.
--   - Like every trigger-enforced refusal in this lineage, the blocks-start self/dangling/cycle
--     refusals and the claim-time blockers refusal bind ONLY the granted `:role`'s ordinary INSERT
--     path -- a schema-owner/superuser with DDL privilege can disable a trigger or write directly,
--     the same disclosed bound s26/s28/s29/s30/s37/s38 already name.
--   - `work_blocks_start_would_cycle` is depth-capped (10000), matching every would_cycle function
--     in this lineage -- defense against a bypassed-trigger cycle looping the walk forever, never
--     claimed as a live hazard under ordinary operation (a legally-constructed blocks-start
--     subgraph cannot cycle by the SAME construction-time refusal this delta ships).
--   - The claim-time refusal fires on work_claimed INSERT only -- it does not retroactively refuse
--     a PRE-EXISTING claim made before its own blocks-start antecedent existed or closed (the
--     ledger is append-only; there is no UPDATE path to un-claim). This mirrors s30's own posture
--     for blocks-close (a strict-close check is likewise construction-time-only, never retroactive)
--     and is the correct, disclosed bound for an append-only ledger, not a gap this delta could
--     close without violating HISTORY: safe.
--   - A blocks-close edge and a blocks-start edge between the SAME two items, in OPPOSITE
--     directions, construct without refusal -- deliberate, per Element 2's own ground (a) above
--     (the two obligations fire at different lifecycle moments and are jointly satisfiable in the
--     ordinary case). But if --strict (or composite discharge) is later invoked on the
--     blocks-close side, the topology produces a GENUINE mutual claim/close deadlock that NEITHER
--     construction-time cycle check detects, each being scoped to a single edge type by design
--     (Element 2's own decision, this file). This is an admitted, named axis, not a mechanism gap:
--     it is recoverable via the standard supersession recipe (supersede one of the two edges),
--     the same recovery path as any other regretted edge in this lineage.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s38): schema/kern/role are
-- psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s39val -v kern=s39val_kernel -v role=s39val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s27-chain-high-water.sql \
--        -f s28-work-parent-edge.sql -f s29-obligation-item-key-and-typed-close.sql \
--        -f s30-typed-dependency-edges.sql -f s31-supersession-uniform-retraction.sql \
--        -f s32-edge-views-single-home.sql -f s33-composite-discharge.sql \
--        -f s34-computed-grade-refusal.sql -f s35-validation-decomposition.sql \
--        -f s36-decision-grade.sql -f s37-violation-disposition.sql \
--        -f s38-bookkeeping-close.sql -f s39-blocks-start.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` in this SAME
--   commit (s37/s38 precedent). Authored and scratch-witnessed on scratch schema pairs in the TOY
--   db only -- NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (DROP+ADD CONSTRAINT; CREATE OR REPLACE).
-- ============================================================================================
