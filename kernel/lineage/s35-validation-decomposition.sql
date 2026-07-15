-- s35 VALIDATION DECOMPOSITION (design/ORCH-CATEGORICAL-REFACTOR-CONSULT-2026-07-15.md F4 + plan
-- HISTORY: safe -- pure refactor of validate_work_item() into dispatcher + leaves; every
-- refusal's error text byte-identical (witnessed across the s22..s33 fixture suites); no
-- table, view, or row change of any kind.
-- step 7; design/ORCH-IDRIS-REFINEMENT-CONSULT-2026-07-15.md's R8 lowering row; ledger item
-- validation-trigger-decomposition, claimed by the orchestrator, not closed by this delta). This
-- delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the
-- maintainer's act at a FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s33 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8). This delta
-- does NOT depend on, wire, or reference kernel/lineage/s34 (a concurrent, separately-owned delta
-- touching validate_independence() -- disjoint territory, disjoint function).
--
-- PREREQUISITE: this delta REQUIRES s33 (kernel/lineage/s33-composite-discharge.sql) applied first
-- -- it re-issues validate_work_item(), the SAME function s22 defined and s28/s29/s30/s31/s33 each
-- extended (s32 deliberately left it untouched). Applying this file on a pre-s33 kernel fails
-- loudly at CREATE OR REPLACE FUNCTION time (the leaf bodies below assume s33's is_composite/
-- work_discharge shape), the correct, disclosed failure mode for a hard dependency, matching
-- s29/s30/s31/s32/s33's own PREREQUISITE precedent.
--
-- WHY (F4, verbatim finding): "`validate_work_item` as an accreting monolith. CONFIRMED. Defined
-- in s22, wholly re-issued in s28, s29 (twice, with the sec-10 amendment), and s30 [and s31, s33]
-- -- each time copying every prior branch with only a PROSE assertion of byte-identity. That is a
-- hand-maintained fold over the delta chain; the coherence condition ('prior branches unchanged')
-- is checkable by no mechanism today. One silent mutation in a re-issue would ship." The refinement
-- consult's R8 row names the same hazard from the typed-model side and its lowering table calls it
-- a REAL, UNBUILT hazard whose "typed premise list is the natural manifest source" -- Element 2
-- below is that manifest, made mechanical rather than typed (SQL cannot carry Idris's type-level
-- premise family; a banked-canonical-text gate is this floor's honest equivalent).
--
-- SCRATCH WITNESS FIRST (per this commission's own instruction and the categorical consult's own
-- uncertainty #2: "multiple-trigger ordering (alphabetical firing) for step 7 needs a scratch
-- witness; the dispatcher-with-leaf-functions shape avoids it but adds one indirection -- pick on
-- evidence, not preference"). Empirically compared, on a throwaway schema (script banked at
-- /tmp scratch, reproduced in this header for the record -- see orchlog.d/validation-trigger-
-- decomposition.md for the full transcript):
--   SHAPE (a) -- dispatcher-with-leaves: ONE trigger, ONE function, leaves called as two
--   sequential statements in ONE function body. A model policy ("NULL defaults to a sentinel that
--   a subsequent check refuses") was probed: insert NULL -> default fires, THEN check fires and
--   correctly refuses. The order is TEXTUAL LINE ORDER inside one function; there is no side
--   channel by which it can silently invert.
--   SHAPE (b) -- multiple triggers under enforced alphabetical naming (a_default, b_check): the
--   SAME probe, correctly named, refuses correctly (a_default fires before b_check). Then: an
--   innocuous DDL rename (`ALTER TRIGGER a_default ... RENAME TO z_default`, the kind of refiling
--   a future author might do for an unrelated reason -- no syntax error, nothing loud) SILENTLY
--   REVERSED firing order (b_check now < z_default alphabetically). The SAME NULL-insert probe
--   then LANDED A ROW THE POLICY MEANT TO ALWAYS REFUSE (val=999, the check's own >=900 threshold)
--   with ZERO errors anywhere -- the check ran on the pre-default NEW and never saw the value it
--   exists to police.
-- VERDICT: shape (a), dispatcher-with-leaves. The consult's own lean is confirmed by evidence, not
-- assumed: shape (b)'s failure mode is silent, undetectable by any mechanism short of re-running
-- the full acceptance suite after every trigger rename, and the "enforced alphabetical naming"
-- convention it depends on is a PROSE discipline (exactly the class ADR-0000/ADR-0011 exist to
-- foreclose) with no construction-time or catalog-level backstop. Shape (a)'s one indirection (a
-- dispatcher calling leaves by name) costs one extra frame per validation; it buys ORDER AS A
-- TEXTUAL FACT IN ONE FUNCTION, the same property s30's own "must stay within one function" caution
-- named as the safe option. s30's OWN default-then-check pair (edge_type NULL -> 'informs', then
-- the blocks-close checks) is reproduced below inside ONE leaf function
-- (validate_work_item_depends), preserving that property exactly.
--
-- SHAPE (Element 1 -- the four leaves, F4's own enumeration): validate_work_item() is re-issued as
-- a THIN DISPATCHER over four per-concern leaf functions, each independently re-issuable by a
-- FUTURE delta without touching the other three or the dispatcher's own branching (which kind
-- routes to which leaf is unchanged from s22's own if/elsif shape, so this delta changes WHERE
-- code lives, never WHAT it does or WHEN it runs):
--   validate_work_item_open       -- open-uniqueness+parent (s22 duplicate-open, s22 dangling-
--                                     parent, s28 parent-cycle).
--   validate_work_item_depends    -- depends-edge typing (s30 default-then-check: edge_type NULL
--                                     -> 'informs', THEN self-edge/dangling-antecedent/cycle
--                                     refusals for blocks-close only).
--   validate_work_item_close_is_composite -- s33's is_composite predicate, split out as its own
--                                     pure read (no RAISE, no mutation) so a future delta can
--                                     change WHAT counts as composite without touching the close
--                                     leaf's own refusal logic.
--   validate_work_item_close      -- close review-disposition/strict (s29 Element B epoch-gated
--                                     presence, s29 Element C strict-close witness/deferred +
--                                     obligation-tree blockers, s33's widened entry condition
--                                     consuming the is_composite leaf's output).
-- The shared "has this slug ever been opened" precondition (invariant 2, item identity -- s22)
-- applies to ALL THREE non-open kinds and is not specific to any one of the four named concerns;
-- it stays in the dispatcher itself, exactly where it already was, unmoved and byte-identical.
--
-- BYTE-IDENTITY: every RAISE EXCEPTION string below is a VERBATIM copy of s33's text (character
-- for character, including every em-dash, every doubled single-quote escape, every format
-- placeholder and its argument order) -- moved to a new function body, never reworded. This is
-- checked, not merely claimed: gates/validation_leaf_manifest_gate.py (Element 2) banks the
-- canonical (pg_get_functiondef, schema-normalized) text of all four leaves and refuses ANY future
-- re-issue that silently changes a leaf's canonical text without a --declare-change naming it.
-- seen-red/s35-validation-decomposition/run_fixtures.py additionally re-runs every refusal
-- polarity from the s22/s29/s30/s31/s33 fixtures against THIS chain and diffs the exact error text
-- byte-for-byte against pre-recorded s33-era text.
--
-- NOT IN SCOPE: LINEAGE_CHAIN wiring (this commission's own instruction -- s35 is authored and
-- scratch-witnessed only, exactly like s32/s33 before it); validate_independence() (s17/s21/s29's
-- OWN accreting monolith, F4's "same shape, smaller" sibling -- owned by the concurrent s34
-- builder, untouched here); any change to WHICH kind routes to WHICH leaf, or to any refusal's
-- trigger condition, message text, or argument order.
-- ============================================================================================

-- ============================================================================================
-- ELEMENT 1a -- LEAF: validate_work_item_open. s22's duplicate-open refusal + s22's dangling-
-- parent refusal + s28's parent-cycle refusal. BYTE-IDENTICAL to the corresponding lines inside
-- s33's monolith (moved, not reworded).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_open(r :"schema".ledger)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
BEGIN
  IF EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = r.work_slug) THEN
    RAISE EXCEPTION 'Ledger policy: work item slug ''%'' already has an opening act — one opening act per slug (the Q5 defect: a decomposition ledgered twice under the same identity is refused, never silently duplicated). This holds even if that opening act has since been RETRACTED (superseded): under uniform retraction (s31, ratified 2026-07-15) a retracted open still permanently burns its slug, reinstatement-free. To redo the work under a fresh identity, open a NEW slug citing the old row: ./led work open <new-slug> "<title>" --refs row:<old-open-row-id>.', r.work_slug;
  END IF;
  IF r.work_parent IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened' AND work_slug = r.work_parent) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' names parent ''%'' which has no opening act — a --parent must reference an ALREADY-OPENED work item slug (dangling parents are refused here, unlike work_depends_on''s antecedent, which the spec deliberately leaves unrefused, s22). Open the parent first: ./led work open % "<title>", then retry this open with --parent %.', r.work_slug, r.work_parent, r.work_parent, r.work_parent;
    ELSIF work_parent_would_cycle(r.work_parent, r.work_slug) THEN
      RAISE EXCEPTION 'Ledger policy: work item slug ''%'' cannot be parented to ''%'' — ''%'' is already an ancestor of ''%'' in the work-tree, so this edge would create a cycle. Refused at construction, never a tolerated-but-flagged row (see work_item_violations.parent_cycle for the defense-in-depth read).', r.work_slug, r.work_parent, r.work_slug, r.work_parent;
    END IF;
  END IF;
  RETURN r;
END; $fn$;

-- ============================================================================================
-- ELEMENT 1b -- LEAF: validate_work_item_depends. s30's default-then-check pair, kept inside ONE
-- function body (the scratch-witnessed safe shape): NEW.edge_type defaulted to 'informs' FIRST,
-- THEN the blocks-close self-edge/dangling-antecedent/cycle refusals. BYTE-IDENTICAL text.
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
  RETURN r;
END; $fn$;

-- ============================================================================================
-- ELEMENT 1c -- LEAF: validate_work_item_close_is_composite. s33's is_composite predicate, split
-- into its own pure read (no RAISE, no mutation) -- BYTE-IDENTICAL query shape, just named and
-- callable on its own so a future delta can change what counts as composite without touching the
-- close leaf's refusal logic.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_close_is_composite(p_work_slug text)
    RETURNS boolean LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  is_composite boolean;
BEGIN
  is_composite := EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened'
                          AND work_slug = p_work_slug AND work_discharge = 'composite');
  RETURN is_composite;
END; $fn$;

-- ============================================================================================
-- ELEMENT 1d -- LEAF: validate_work_item_close. s29 Element B (epoch-gated review-disposition
-- presence) + s29 Element C (strict-close witness/deferred + obligation-tree blockers) with s33's
-- widened entry condition (OR COALESCE(is_composite, false)). `tg_schema` replaces the dispatcher-
-- only magic variable TG_TABLE_SCHEMA (unavailable inside a non-trigger function) -- the caller
-- passes it through so the epoch-refusal's error text stays BYTE-IDENTICAL (same %.migration_epoch
-- interpolation, same value).
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

-- ============================================================================================
-- ELEMENT 1e -- THE DISPATCHER: validate_work_item() re-issued as a THIN wrapper (CREATE OR
-- REPLACE, not a second copy -- ADR-0012 P1) calling the four leaves above in the SAME order and
-- under the SAME conditions s33's monolith already used. The shared "has this slug ever been
-- opened" precondition (invariant 2, s22) stays here, byte-identical, since it is not owned by any
-- one of the four named concerns.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  is_composite boolean;
BEGIN
  IF NEW.kind = 'work_opened' THEN
    NEW := validate_work_item_open(NEW);
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
-- ELEMENT 2 -- gates/validation_leaf_manifest_gate.py (F4's real hazard, mechanized): banks the
-- canonical (pg_get_functiondef, schema-normalized) text of the four leaves above at THIS delta's
-- authorship time, and refuses a FUTURE re-issue that silently mutates a leaf it did not declare
-- changed. See that file's own header for the closure statement. Not DDL -- a Python gate, no SQL
-- object of its own; named here so this file's own header is the one place documenting Element 2's
-- existence and purpose, per this delta's own byte-identity claim.
-- ============================================================================================
