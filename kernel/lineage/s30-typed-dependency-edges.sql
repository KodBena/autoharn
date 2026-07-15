-- s30 TYPED DEPENDENCY EDGES (design/FABLE-OBLIGATION-DEPENDENT-TYPING-SPEC.md, TRUE PROVENANCE:
-- Opus-drafted under an unrequested mid-session model demotion, Fable-reviewed-and-ADOPTED on
-- restoration with one review note answered by the maintainer on the ledger -- see this file's own
-- REVIEW NOTE DISPOSITION section below -- RATIFIED 2026-07-15, ledger decision row 1018 (same
-- ratifying act as design/MAINT-MIGRATION-ACCOMMODATIONS-SPEC.md, verbatim: "...accepted, apply").
-- This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the
-- maintainer's act at a FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s29 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second hand-copy of any existing mechanism (ADR-0012 P1: one home per mechanism).
--
-- HISTORY: safe -- NO row this delta has ever touched is written to (the ledger's own append-only
-- trigger refuses UPDATE for EVERY role, including the schema owner applying this DDL -- witnessed
-- directly authoring this file: a first draft's backfill UPDATE FAILED with "the ledger is
-- append-only and durable — UPDATE is refused for every role" against exactly the pre-s30-history
-- world this delta must apply cleanly over, caught before shipping, not discovered live). The shape
-- CHECK below is therefore deliberately ONE-WAY, not a two-way iff (contrast s22's own
-- work_depends_on_kind_shape, which IS two-way): a PRE-EXISTING work_depends_on row is legally
-- edge_type IS NULL forever (unwritable, by the SAME append-only guarantee that makes this whole
-- ledger a trustworthy record), and every reader treats that NULL as informs by omission -- NULL is
-- never equal to 'blocks-close' in SQL, so a legacy row is naturally excluded from Element 3's
-- filter with no COALESCE, no backfill, and no re-validation of any existing row at ADD CONSTRAINT
-- time. This is the pairing-RCA invariant applied a THIRD time (s29's sec-10 epoch amendment was
-- the second): never write a fact a read-time derivation can supply for free. No `.accommodate.sql`
-- sibling is needed or provided -- there is no history-validating statement in this file at all.
--
-- PREREQUISITE: this delta REQUIRES s29 (kernel/lineage/s29-obligation-item-key-and-typed-close.sql)
-- applied first -- it extends `work_item_strict_blockers()` and `validate_work_item()`, both s29
-- objects (the latter itself an s28/s22 extension chain). Applying this file on a pre-s29 kernel
-- fails loudly at CREATE OR REPLACE FUNCTION time (the function bodies below assume s29's own
-- migration_epoch/review-disposition clauses are already present, since CREATE OR REPLACE FUNCTION
-- with a plpgsql body containing this file's ADDITIONS still needs a base to extend) -- the correct,
-- disclosed failure mode for a hard dependency, matching s29's own PREREQUISITE-on-s28 precedent.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): spec sec-1, the gap named once -- `work_depends_on` (s22) carries no TYPE, so nothing
-- distinguishes "X must resolve for Y to close" (the only kind of edge s29's obligation AND-tree may
-- conjoin) from "X is merely related to Y" (informational, never gating). Nothing forecloses a
-- cycle, a self-edge, or a dangling endpoint on a load-bearing edge. An AND-tree drawn from an
-- untyped relation is a projection that must GUESS which edges are load-bearing -- exactly the class
-- ADR-0000 forecloses (make the defect unrepresentable) and ADR-0012 P1 names (the fact "is this
-- edge close-blocking" had no home at all before this delta).
--
-- REVIEW NOTE DISPOSITION (the spec's own header names this as the one open question the maintainer
-- had to answer before a build could start): spec sec-2 names `supersedes` in the edge vocabulary
-- prose ("already modeled for rows") without saying whether it is a legal `edge_type` value or a
-- reserved word. Maintainer disposition (on the ledger, commissioning this build): row supersession
-- ALREADY has its one home -- the pre-existing `ledger.supersedes` column (s15, every kind, not
-- work_depends_on-specific) -- so `supersedes` is a RESERVED WORD here, NOT a legal `edge_type`
-- value: minting it as a second, edge-scoped mechanism for the SAME fact would be exactly the
-- two-writers-of-one-truth violation ADR-0012 P1 forbids. The closed vocabulary below is therefore
-- exactly TWO values -- `blocks-close`, `informs` -- and the CHECK constraint actively REFUSES
-- `supersedes` as an edge_type (named, not merely omitted, so a future author cannot reach for the
-- word by habit and get a silent NULL-shape failure instead of a legible refusal).
--
-- ELEMENT 1 -- edge_type COLUMN, CLOSED VOCABULARY, FAIL-SAFE DEFAULT (spec sec-2/sec-4). One new
-- column on `ledger`, legal only on `work_depends_on` rows -- ONE-WAY, deliberately DIFFERENT from
-- s22's own TWO-way `work_depends_on_kind_shape` idiom (SCOUT: s22:203-205): a work_depends_on row
-- MAY be edge_type IS NULL (every PRE-EXISTING row, forever -- append-only makes it unwritable, see
-- HISTORY above), but no OTHER kind may ever carry edge_type. Two legal non-NULL values:
-- `blocks-close` (the only type `work_item_strict_blockers()` conjoins) and `informs` (the fail-safe
-- default for a NEW edge whose applying act supplies none -- an unclassified/legacy edge is SHOWN,
-- never conjoined, until a human types it, and a legacy edge_type IS NULL row reads IDENTICALLY,
-- with no write, since NULL never satisfies `edge_type = 'blocks-close'`). Populated on NEW inserts
-- by `validate_work_item()` (extended a FOURTH time below) exactly like s29's own `discharge_grade`
-- precedent -- COMPUTED/DEFAULTED in the trigger, not a bare column DEFAULT (a column-level DEFAULT
-- would backfill EVERY kind of ledger row, not just work_depends_on rows, breaking the kind-scoped
-- shape convention every other work_* column in this lineage follows).
--
-- ELEMENT 2 -- STRUCTURAL REFUSALS, BLOCKS-CLOSE ONLY (spec sec-2's "Structural refusals" bullet).
-- A `blocks-close` edge is refused at construction if it is a self-edge, if its antecedent has no
-- opening act (a "close-tracked work item" -- both endpoints must exist as work items, unlike an
-- `informs` edge's deliberately lax posture), or if it would create a cycle in the blocks-close-only
-- subgraph (the AND-tree must be a DAG or conjunction has no fixpoint). An `informs` edge keeps
-- EXACTLY s22's original, deliberately-unrefused posture (dangling antecedent visible-only via
-- `work_item_violations.depends_on_unknown_slug`, cross-kind cycles visible-only via
-- `depends_on.dependency_cycle`) -- named, not silently changed: this delta narrows nothing that
-- already worked, it only ADDS a stronger refusal for the NEW, stronger-claim edge type.
--
-- ELEMENT 3 -- ELEMENT C'S CONJUNCTION FILTERED TO blocks-close (spec sec-4's third bullet).
-- `work_item_strict_blockers()` (s29) is extended (CREATE OR REPLACE, the SAME function -- ADR-0012
-- P1) so its `edges` CTE's `work_depends_on` arm reads ONLY `edge_type = 'blocks-close'` rows,
-- instead of every `work_depends_on` row regardless of type. This is the delta's whole point: the
-- AND-tree now reads the type, it never re-infers "is this edge load-bearing" from the edge's mere
-- existence. `informs` edges remain fully visible in the graph (unchanged reads: `work_item_current`,
-- `work_item_violations`) but NEVER enter a strict-close conjunction.
--
-- RESOLUTION STAYS DERIVED (spec sec-2's fourth bullet, the pairing-RCA invariant, inherited a
-- second time): no new stored verdict is introduced anywhere by this delta. `edge_type` is a typed
-- FACT about the edge (what kind of dependency this is), not a computed RESOLUTION verdict (whether
-- the tree is satisfied) -- that computation remains exactly where s29 put it, inside
-- `work_item_strict_blockers()`, re-derived fresh on every call.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: every `work_depends_on` row carries a MANDATORY, closed-vocabulary `edge_type`
--     (`blocks-close`|`informs`, `supersedes` actively refused as a reserved word) -- legal only on
--     that kind (two-way shape CHECK), defaulted fail-safe to `informs` by the write-boundary
--     trigger when the applying act supplies none. A `blocks-close` edge additionally refuses a
--     self-edge, a dangling antecedent, and a cycle in the blocks-close subgraph, all at
--     CONSTRUCTION TIME. The obligation AND-tree's conjunction (`work_item_strict_blockers()`) reads
--     `edge_type` and conjoins EXACTLY the `blocks-close` edges -- it never infers load-bearing-ness
--     from an edge's mere presence.
--
--   - QUANTIFICATION UNIVERSE -- enumerated by re-reading every table/view the s15..s29 chain
--     exposes to :role (mirroring s22/s28/s29's own re-verification discipline), checked against
--     the one new column/two new functions this delta adds:
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table (the edge-type fact
--         rides the existing `work_depends_on` row, exactly like every other work_* fact in this
--         lineage).
--       VIEWS re-read for the wildcard/column-complete class s20/s22/s23/s24/s26/s28/s29 all named:
--         * ledger_current / countersigned_in_force -- explicit column lists (s20+). GAIN the ONE
--           new column (edge_type), APPENDED AT THE END, HERE, else the column-complete class
--           recurs one column later (the s20 lesson, re-applied a FIFTH time).
--         * work_item_current -- s22's own view, extended s28/s29. NOT extended here: `edge_type` is
--           a fact about the EDGE (a `work_depends_on` row), not about the ITEM `work_item_current`
--           enumerates one row per (s22's own precedent for `work_depends_on` itself, which
--           `work_item_current` never surfaced either -- an edge's antecedent/type is read from the
--           ledger directly, or from `work_item_violations`/a future edge-listing view, never
--           smuggled onto the per-item row).
--         * work_item_violations, work_item_descendants -- re-verified NOT members: neither reads a
--           general ledger-row column passthrough this delta's one new column belongs on (both are
--           s22/s28's own specialized derived shapes, untouched by this delta's column).
--         * review_gap / question_status / review_stamp_distinctness / work_review_gap -- re-verified
--           NOT members, for the identical reasons s22/s24/s26/s28/s29 each already gave (no general
--           ledger-row column passthrough an edge-type fact belongs on).
--       KIND VOCABULARY -- unchanged. This delta adds no new `kind` value: `edge_type` is carried
--         entirely on the EXISTING `work_depends_on` kind's own row, one more optional column beside
--         `work_depends_on` (the antecedent slug).
--       GRANTS -- mirrors s22/s28/s29's own posture: no new view is added by this delta (Element 3
--         is a CREATE OR REPLACE of an EXISTING function, `ledger_current`/`countersigned_in_force`
--         re-issues keep their EXISTING grants per s21's additive-column-order idiom), so no
--         table/view-level grant change is needed. The new `work_depends_on_would_cycle()` STABLE
--         function needs no explicit GRANT (Postgres grants EXECUTE to PUBLIC by default, verified
--         against s28's own `work_parent_would_cycle()`, which received none either).
--       ENGINE -- NONE shipped in this delta (mirrors s23/s25/s26/s28's own "ENGINE -- NONE"
--         disclosure): `engine/lp/work_items.lp` (s22's own ASP companion) is NOT extended here --
--         `edge_type` is a construction-time-refused, read-time-filtered SQL fact with no T_now
--         derivation of its own; `./judge`'s existing SQL/ASP differential is UNAFFECTED (it derives
--         T_now facts from kind/status/supersedes/etc., none of which this delta touches) and
--         continues to AGREE.
--
--   - DENOMINATION: `edge_type` is `text`, closed vocabulary (`blocks-close`|`informs`), NEVER a
--     boolean flag (a future third value -- the spec's own sec-6 names extensibility "only by
--     ratified amendment" -- would force a disruptive boolean-to-enum migration were this a
--     bool). The item identity `edge_type` types (which `work_depends_on` row) is the SAME slug
--     pair (`work_slug`, `work_depends_on`) s22 already denominates -- this delta adds no new
--     identity primitive, only a third attribute on the existing pair.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta is NOT class-ratified
-- fail-safe on its own motion (it is the Fable-reviewed-and-adopted, maintainer-ratified delta the
-- spec's own header names, ledger decision row 1018) -- but every individual mechanism within it, in
-- isolation, WOULD qualify: the new column defaults fail-safe (`informs`, never gating), the new
-- refusals are all NEW (no existing refusal loosened -- `informs`'s dangling-antecedent/cycle posture
-- is BYTE-IDENTICAL to s22's original, unrefined posture), and the Element 3 filter only NARROWS
-- what strict-close conjoins (a stricter reading of "resolved" than s29 shipped with, never a
-- laxer one -- a tree that was unresolved under s29's own coarser walk stays unresolved or becomes
-- MORE permissive only by an explicit, human `informs` re-type, exactly the spec's own sec-5
-- acceptance bullet). Named for the record per the standing decision-tree text, not claimed as the
-- routing reason (ratification already happened via the spec itself).
--
-- LIMITS (pre-registered, matching s22/s26/s28/s29's own disclosure convention):
--   - Like every trigger-enforced refusal in this lineage, the blocks-close self/dangling/cycle
--     refusals bind ONLY the granted `:role`'s ordinary INSERT path -- a schema-owner/superuser with
--     DDL privilege can disable the trigger or write directly, the same disclosed bound s26/s28/s29
--     already name.
--   - `work_depends_on_would_cycle()` is depth-capped (10000), matching `work_parent_would_cycle()`'s
--     own cap -- defense against a bypassed-trigger cycle looping the walk forever, never claimed as
--     a live hazard under ordinary operation (a legally-constructed blocks-close subgraph cannot
--     cycle by the SAME construction-time refusal this delta ships, mirrored from s28's own
--     induction argument -- but unlike `work_parent`, a `work_depends_on` edge is NOT fixed at the
--     dependent's own opening act; it can be added at any later point in the item's life, so the
--     induction argument is over INSERTION ORDER of blocks-close edges specifically, not over
--     work-item opening order -- named, not silently assumed identical to s28's case).
--   - `edge_type`'s closed vocabulary is exactly `{blocks-close, informs}`; `supersedes` is actively
--     REFUSED (see REVIEW NOTE DISPOSITION above), not merely absent -- a future amendment widening
--     this vocabulary is the spec's own sec-6 "extensible only by ratified amendment" clause, not
--     this delta's authority.
--   - `work_item_current` is deliberately NOT extended with edge-type-aware columns (see QUANTIFI-
--     CATION UNIVERSE above) -- a caller wanting a work item's typed dependency edges reads
--     `work_depends_on`-kind ledger rows (or `ledger_current`, which now carries `edge_type`)
--     directly; no new rollup view is minted for this delta's narrow scope (ADR-0004: no
--     scope-creep beyond what the spec's own acceptance bullets require).
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s22/s28/s29): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s30val -v kern=s30val_kernel -v role=s30val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql \
--        -f s29-obligation-item-key-and-typed-close.sql -f s30-typed-dependency-edges.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE world's
--   birth chain, wired by this same commission's own seam-integration pass into
--   `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` (done in this same commission -- unlike s28/s29,
--   which deferred that wiring to a later pass, this build's own brief names the wiring as in-scope).
--   It was authored and scratch-witnessed on scratch schema pairs in the TOY db only -- NOT applied
--   to any live schema by this pass.
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
-- ELEMENT 1 -- THE ONE NEW COLUMN. No DEFAULT at the column level (see header: a column-level
-- DEFAULT would backfill every kind of row, not just work_depends_on) and NO backfill UPDATE (the
-- ledger's append-only trigger refuses UPDATE for every role, including the schema owner running
-- this DDL -- see HISTORY above) -- populated ONLY by the write-boundary trigger, for every future
-- INSERT (Element 2 below). A pre-existing work_depends_on row keeps edge_type IS NULL forever,
-- read as informs by omission (Element 3's filter), never written.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS edge_type text;

COMMENT ON COLUMN :"schema".ledger.edge_type IS
  'Typed dependency edge (kernel/lineage/s30-typed-dependency-edges.sql): for a work_depends_on row,
   one of blocks-close (the antecedent must reach a resolved state before the dependent may
   strict-close -- the ONLY type work_item_strict_blockers() conjoins) or informs (context; never
   gates a close), OR NULL on a row that predates this delta (unwritable after the fact -- the
   ledger is append-only -- and read as informs by omission: NULL never satisfies
   `edge_type = ''blocks-close''`, so a legacy edge is excluded from Element 3''s filter with no
   backfill). supersedes is a RESERVED WORD here, not a legal value -- row supersession already has
   its one home in the pre-existing ledger.supersedes column (s15); see this file''s REVIEW NOTE
   DISPOSITION for why. Legal (non-NULL) only on kind=''work_depends_on'' (edge_type_kind_shape
   below, ONE-WAY, not a two-way iff -- see that constraint''s own comment for why). Defaults
   fail-safe to informs, on a NEW row, when the applying act supplies none (validate_work_item(),
   extended here) -- never silently blocks or silently satisfies a close.';

-- ============================================================================================
-- SHAPE INVARIANTS (illegal states unrepresentable AT CONSTRUCTION, ADR-0000 Rule 1 -- the
-- strongest available surface WHERE it can be expressed without touching an existing row). The
-- kind-scoped shape CHECK is deliberately ONE-WAY here, NOT s22's own two-way
-- `work_depends_on_kind_shape` idiom (SCOUT: s22:203-205) -- a two-way iff would demand
-- edge_type IS NOT NULL on every work_depends_on row, which would immediately fail ADD CONSTRAINT's
-- whole-table validation on any world with pre-existing work_depends_on rows (HISTORY above: no
-- backfill is possible, append-only). The ONE-WAY form below forecloses the real hazard (edge_type
-- appearing on a NON-work_depends_on row -- a genuine SSOT violation, still refused at construction)
-- while leaving a legacy work_depends_on row''s NULL alone, exactly like s22's own ONE-WAY
-- `work_witness_kind_shape` precedent (nullable-and-scoped, not a two-way iff) one column over.
-- Closed-vocabulary CHECK names supersedes explicitly as NOT a legal value (REVIEW NOTE DISPOSITION
-- in the header) -- trivially satisfied by NULL, so it never re-validates a legacy row either.
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS edge_type_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT edge_type_kind_shape CHECK (
    edge_type IS NULL OR kind = 'work_depends_on');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS edge_type_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT edge_type_check CHECK (
    edge_type IS NULL OR edge_type IN ('blocks-close', 'informs'));
    -- 'supersedes' deliberately excluded from this list -- reserved, not merely unlisted (header).

-- ============================================================================================
-- work_depends_on_would_cycle(dependent_slug, antecedent_slug) -- the ONE home of "would honoring
-- THIS blocks-close edge create a cycle in the blocks-close subgraph" (ADR-0012 P1). The edge being
-- considered reads dependent_slug -> antecedent_slug (dependent NEEDS antecedent resolved). A cycle
-- would form iff antecedent_slug can ALREADY reach dependent_slug by walking existing blocks-close
-- edges forward (antecedent -> ... -> dependent) -- adding dependent -> antecedent would then close
-- the loop. Self-edges are caught at depth 0 (the walk's own seed row), redundant with
-- work_depends_on_not_self below, intentionally (belt-and-braces, matching work_parent_would_cycle's
-- own self-case precedent, s28). Depth-capped (10000, matching work_parent_would_cycle's own cap) --
-- see header LIMITS for why this is NOT provably vacuous the same way s28's cap is (a
-- work_depends_on edge is addable at any point in an item's life, not fixed at opening). LANGUAGE sql
-- STABLE: a pure read, safe to call from the trigger below.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_depends_on_would_cycle(dependent_slug text, antecedent_slug text)
    RETURNS boolean LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE reach(slug, depth) AS (
    SELECT antecedent_slug, 0
    UNION ALL
    SELECT d.work_depends_on, r.depth + 1
    FROM reach r
    JOIN ledger d ON d.kind = 'work_depends_on' AND d.edge_type = 'blocks-close'
                 AND d.work_slug = r.slug
    WHERE r.depth < 10000
  )
  SELECT EXISTS (SELECT 1 FROM reach WHERE slug = dependent_slug);
$fn$;

-- ============================================================================================
-- validate_work_item() EXTENDED A FOURTH TIME (the SAME function s22 defined, s28/s29 extended --
-- CREATE OR REPLACE, not a second copy; ADR-0012 P1). New, scoped to kind='work_depends_on': default
-- NEW.edge_type to 'informs' when the applying act supplies none (mirrors validate_independence()'s
-- own NEW.discharge_grade computed-default precedent, s29); when the (defaulted-or-explicit) type is
-- 'blocks-close', refuse a self-edge, a dangling antecedent, and a cycle (Element 2). 'informs' edges
-- keep s22's original, BYTE-IDENTICAL unrefined posture -- no new refusal fires for them. Every
-- pre-existing branch (duplicate-open; dangling/cycling parent; unopened-slug; s29's epoch-gated
-- review-disposition and strict-close blocks) is UNCHANGED, byte-for-byte, below.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
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
    -- s30: edge_type, fail-safe-defaulted and, for blocks-close, structurally refused.
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
-- with s22/s28/s29's own script shape.
DROP TRIGGER IF EXISTS validate_work_item ON :"schema".ledger;
CREATE TRIGGER validate_work_item BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_work_item();

-- ============================================================================================
-- ELEMENT 3 -- work_item_strict_blockers() EXTENDED (the SAME function s29 defined -- CREATE OR
-- REPLACE, not a second copy; ADR-0012 P1). ONLY CHANGE from s29's own body: the `edges` CTE's
-- work_depends_on arm now filters to edge_type = 'blocks-close' (was: every work_depends_on row
-- regardless of type). Every other clause (the s28 work_parent arm, `tree`, `closes`, `not_closed`,
-- `review_unresolved`) is UNCHANGED, byte-for-byte, below.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_item_strict_blockers(root_slug text)
    RETURNS TABLE(blocking_slug text, reason text) LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE
  edges AS (
    -- both edge kinds feeding ONE combined successor relation (Postgres allows exactly ONE
    -- self-reference to a recursive CTE in its recursive term, so the two edge kinds are unioned
    -- HERE, outside the recursion, rather than as two separate recursive UNION arms). DIRECTION
    -- (both rows read "walking FROM `parent` we reach tree member `child`"): an s28 work_parent
    -- edge walks PARENT -> CHILD literally (child.work_parent = parent, matching the column
    -- names). A work_depends_on edge walks OPPOSITE its own column names -- the DEPENDENT plays
    -- the `parent` role here (it is the tree member we are walking FROM) and its ANTECEDENT plays
    -- the `child` role (the next tree member we reach) -- because a dependency's antecedent is a
    -- CHILD in obligation-tree terms (spec sec-5: "children via `work_depends_on`"): the item that
    -- depends on it needs the antecedent's own resolution, exactly as it needs an s28 child's.
    -- s30: the work_depends_on arm now conjoins ONLY blocks-close edges -- the AND-tree reads the
    -- type, never re-infers load-bearing-ness from an edge's mere existence (this file's own
    -- Element 3).
    SELECT o.work_slug AS child, o.work_parent AS parent
    FROM ledger o WHERE o.kind = 'work_opened' AND o.work_parent IS NOT NULL
    UNION ALL
    SELECT dep.work_depends_on AS child, dep.work_slug AS parent
    FROM ledger dep WHERE dep.kind = 'work_depends_on' AND dep.edge_type = 'blocks-close'
  ),
  tree(slug) AS (
    SELECT root_slug
    UNION
    SELECT e.child FROM tree t JOIN edges e ON e.parent = t.slug
  ),
  closes AS (
    SELECT work_slug AS slug, id AS close_id, actor AS closer, work_review_disposition AS disp
    FROM ledger WHERE kind = 'work_closed'
  ),
  not_closed AS (
    SELECT t.slug, 'item is not yet closed'::text AS reason
    FROM tree t
    WHERE t.slug <> root_slug AND NOT EXISTS (SELECT 1 FROM closes c WHERE c.slug = t.slug)
  ),
  review_unresolved AS (
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
-- s20/s22/s23/s24/s26/s28/s29 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN the
-- ONE new column, APPENDED AT THE END. Explicit column lists throughout -- never `l.*`. Column list
-- = s29's exact list + l.edge_type.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation, l.event_declared_ts, l.row_hash, l.work_parent,
       l.work_review_disposition, l.work_review_ref, l.work_strict_close, l.edge_type
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
       l.work_review_disposition, l.work_review_ref, l.work_strict_close, l.edge_type
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));

-- ============================================================================================
-- work_item_violations (s22, extended s28) GAINS one member, blocks_close_cycle -- PROVABLY VACUOUS
-- under normal operation (refused at construction above), belt-and-braces, matching
-- duplicate_open/shipped_without_witness/dangling_parent/parent_cycle's own existing precedent in
-- this same view. Every pre-existing member (duplicate_open, shipped_without_witness,
-- depends_on_unknown_slug, dependency_cycle, dangling_parent, parent_cycle) is UNCHANGED, verbatim,
-- below -- this delta deliberately does NOT narrow dependency_cycle to blocks-close-only (it stays
-- the cross-type detector s22 shipped; blocks_close_cycle below is the NEW, narrower, defense-in-
-- depth read specific to the load-bearing subgraph).
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
SELECT 'blocks_close_cycle', slug, NULL FROM blocks_close_cycle;
