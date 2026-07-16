-- s36 DECISION GRADE (design/FABLE-GRADED-DECISIONS-SPEC.md, RATIFIED 2026-07-16 by the
-- HISTORY: safe -- nullable column, NO default, no backfill, no UPDATE of any existing row; the
-- CHECK constraint only restricts a FUTURE insert's own new value (kind='decision' or NULL), it
-- reads no other row and changes no existing row's evaluation; the one new view is a pure
-- additive read, factored through the kernel's own established current-truth home
-- (ledger_current, s15+) -- every pre-existing view/function/trigger is untouched, byte-for-byte.
-- This is the shape of the class-ratified fail-safe delta rule (CLAUDE.md ORCHESTRATION,
-- "Class-ratified fail-safe deltas", 2026-07-09), but per the spec's own header this delta is
-- routed for ratification as part of the spec rather than claimed under that class.
--
-- maintainer, ledger item `graded-decisions-build`). Sonnet-authored per the standing delegation
-- contract (CLAUDE.md ORCHESTRATION), from a Fable-authored, maintainer-ratified spec. This delta
-- is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the
-- maintainer's act at a FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11), never
-- taken here. An ADDITIVE delta applied ON TOP of the s15..s35 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a
-- second hand-copy of the in-force projection (ADR-0012 P1: one home per mechanism -- this delta
-- reuses `ledger_current`, s15's own existing home, never a fifth inline anti-join).
--
-- PREREQUISITE: this delta REQUIRES s33 (kernel/lineage/s33-composite-discharge.sql) applied
-- first -- it re-issues `ledger_current`/`countersigned_in_force` in the EXACT column-list shape
-- s33 left them (the s20/s22/s23/s24/s26/s28/s29/s30/s33 LESSON: a view's `SELECT l.<cols>` is
-- frozen at CREATE VIEW time, so a new column is invisible through it until re-issued -- see
-- ELEMENT below for where this was caught live on this delta's own first scratch-witness
-- attempt), appending `l.decision_grade` after s33's own last column (`l.work_discharge`).
-- Applying this file on a pre-s33 kernel fails loudly at CREATE OR REPLACE VIEW time (column
-- `l.work_discharge` does not exist), the correct, disclosed failure mode for a hard dependency,
-- matching s28/s29/s30/s31/s32/s33/s34/s35's own PREREQUISITE precedent -- even though
-- `decision_grade` ITSELF has no semantic dependency on s17..s33's own machinery (no function,
-- trigger, or column any of those deltas defined is READ here); the dependency is purely
-- syntactic, on the two views' own CURRENT column-list shape.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): the spec's own root-cause finding (its header, "Provenance"). A decision row today has
-- exactly one durability: none. Every decision competes for the same recency window in both
-- `./pickup`'s IN-FORCE-DECISIONS section (`ORDER BY id DESC LIMIT 10`) and a compacted context
-- window, so "we use spaces not tabs, this week" and "consults MUST land in docs/consults,
-- forever" age out identically. A downstream deployment (the panel, `autoharn-panel`) was
-- witnessed violating a standing decision (its own ledger rows 193/200) ~34 minutes after a
-- context-compaction event, and `./pickup` COULD NOT have surfaced it -- the ledger stood at row
-- ~370, four orders of magnitude past the ten-row window. This delta gives a decision row a
-- durability GRADE the rest of this spec's machinery (led --grade, the SessionStart hook,
-- pickup's new section, `led standing`) can select on, independent of recency.
--
-- THE WHOLE DELTA IN ONE LINE: `ledger.decision_grade` is a nullable text column, legal only on
-- kind='decision' rows, with NO enum and NO CHECK on its value -- the kernel stores a word; which
-- words matter (starter vocabulary: `durable`, "must survive any context loss") is deployment
-- policy, read by the hook/pickup/led layer from `apparatus.json` (element 4 of the spec, built
-- outside the kernel entirely) -- the maintainer's own framing at commissioning, "or something
-- more flexible, who knows," is the design. `standing_decisions` is the one new view: the
-- in-force (ledger_current-factored, so a superseded standing decision drops out automatically,
-- reinstatement-free, s31's own semantics inherited for free -- see CLOSURE STATEMENT) decision
-- rows carrying a non-NULL grade, ordered by id.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: `decision_grade` is non-NULL ONLY on a kind='decision' row (the CHECK below);
--     no other kind can carry a grade. `standing_decisions` is a CURRENT-TRUTH reader (s31's own
--     declared-type discipline, kernel/lineage/s31-supersession-uniform-retraction.sql CLOSURE
--     STATEMENT): it factors through `ledger_current`, the kernel's ONE home of "the un-
--     superseded reading" -- never an inline `NOT EXISTS (supersedes)` copy of its own (ADR-0012
--     P1: one home per mechanism). A standing decision that is later superseded or retracted
--     drops out of `standing_decisions` the moment its own row leaves `ledger_current` --
--     REINSTATEMENT-FREE, costing this delta NO new logic (the same free consequence s31's own
--     header names for `work_item_current`: "superseding the SUPERSEDER does not un-name the
--     original target, so the victim stays retracted regardless of its retractor's own later
--     fate").
--
--   - QUANTIFICATION UNIVERSE -- enumerated by grep over the whole tree (kernel/lineage/,
--     bootstrap/templates/, hooks/, engine/) for every WRITER and every CURRENT-TRUTH READER of
--     `ledger.kind='decision'` rows, per the ADR-0000 2026-07-02 amendment's "check the universe
--     outward":
--       * WRITERS: the ONE writer is the generic `led [flags] <kind> <statement...>` path
--         (bootstrap/templates/led.tmpl) -- `led decision ...` is not a dedicated subcommand
--         today, it is `kind="decision"` through that one generic INSERT. This delta's sibling
--         CLI change (`led decision --grade <word>`, same commission) is the only writer taught
--         to populate the new column; every OTHER existing writer of a decision row (fixtures,
--         instruments, a bare `led decision "..."` with no --grade) continues to insert NULL,
--         unchanged.
--       * CURRENT-TRUTH READERS: `standing_decisions` (this delta, the one new member) is the
--         ONLY reader that queries `decision_grade` by name. `ledger_current` and
--         `countersigned_in_force` are RE-ISSUED (mechanically required, see PREREQUISITE above --
--         a view's `*`-expansion is frozen at creation time) to append `l.decision_grade`, but
--         neither view's own WHERE-clause semantics change by one character -- both re-issues are
--         a pure column-list append, byte-identical to the s20/s22/s23/s24/s26/s28/s29/s30/s33
--         precedent every one of those deltas' own headers already names for the identical reason.
--       * DOWNSTREAM CONSUMERS (outside the kernel, named for the record though they are built by
--         this same commission's sibling deliverables, not this file): `hooks/
--         sessionstart_durable_decisions.py`, `bootstrap/templates/pickup.tmpl`'s new STANDING-
--         DECISIONS section, and `led standing` all read `standing_decisions` directly -- none
--         reads `ledger`/`decision_grade` independently, so the view stays the one factoring
--         every consumer shares (ADR-0012 P1).
--     No second writer or reader surface exists that could bypass either the CHECK or the view.
--
--   - DENOMINATION: `decision_grade` is denominated on the LEDGER ROW ID (one column per row,
--     exactly like every other scalar column on `ledger`) -- never a proxy (a separate grade
--     table, a session variable, a second decision-identity primitive). `standing_decisions` is
--     ordered by `id`, the same "id-is-order law" s31's own CLOSURE STATEMENT names for the
--     in-force projection's own denomination.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): this delta's SHAPE is
-- class-ratified fail-safe (ADDS a nullable column with no default, one CHECK that only bounds
-- the new column's own future values, and one additive view; nothing existing is relaxed, no
-- existing semantics changes, no `law/` file is touched) -- but per the spec's own header
-- ("routed for ratification as part of this spec rather than claimed under that class") it is
-- NOT claimed under the 2026-07-09 class-ratified rule; it routes on design/FABLE-GRADED-
-- DECISIONS-SPEC.md's own RATIFIED status (2026-07-16, maintainer yes) instead, named here for
-- the record, not silently substituted.
--
-- LIMITS (pre-registered, matching s22/s26/s28/s29/s30/s31/s32/s33/s34's own disclosure
-- convention):
--   - NO enum, NO CHECK on `decision_grade`'s VALUE (deliberate, per the spec's own text: "which
--     words matter is deployment policy"). A typo'd grade (e.g. `durrable`) is legal at the
--     kernel layer and simply never matches any deployment's configured grade set -- silently
--     inert, not refused. This is a NAMED limit, not an oversight: closing it would require
--     either a kernel-level enum (which the spec explicitly declines, "widening to other kinds
--     later is a strictly additive follow-up delta, not this one" -- the same posture extends to
--     widening the WORD vocabulary) or a deployment-policy-aware CHECK (which would make the
--     kernel read `apparatus.json`, a layering violation the spec's element 4 explicitly forbids:
--     "the kernel knows nothing of it").
--   - `standing_decisions` surfaces every graded decision in the configured grade SET (a
--     deployment-policy filter applied OUTSIDE this view, by the hook/pickup/led readers) -- this
--     view itself does not filter by grade word at all, it surfaces every non-NULL grade. A
--     future deployment inventing a grade word no reader's configured set recognizes yet is
--     visible here but invisible to the hook/pickup/led surfaces until their own config is
--     updated -- exactly the deployment-policy-vs-kernel split the spec's element 4 draws on
--     purpose.
--   - Like every trigger-enforced refusal in this lineage, the CHECK constraint binds ONLY the
--     granted `:role`'s ordinary INSERT path -- a schema-owner/superuser with DDL privilege can
--     disable/bypass it, the same disclosed bound s26/s28/s29/s30/s31/s33/s34 already name.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s22/s28/s29/s30/s31/s33/s34):
-- schema/kern are psql variables so this delta is VALIDATED on a throwaway substrate before any
-- real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s36val -v kern=s36val_kernel -v role=s36val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql \
--        -f s29-obligation-item-key-and-typed-close.sql -f s30-typed-dependency-edges.sql \
--        -f s31-supersession-uniform-retraction.sql -f s32-edge-views-single-home.sql \
--        -f s33-composite-discharge.sql -f s34-computed-grade-refusal.sql \
--        -f s35-validation-decomposition.sql -f s36-decision-grade.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (runs are
--   strictly linear, 2026-07-11). This delta reaches reality by entering a FUTURE world's birth
--   chain, wired by the ORCHESTRATOR's own seam-integration pass into bootstrap/new-project.sh's
--   LINEAGE_CHAIN -- deliberately NOT taken here (this build's own brief, mirroring s28/s31's own
--   precedent). Authored and scratch-witnessed on scratch schema pairs in the TOY db only --
--   never applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; DROP/ADD CONSTRAINT;
-- CREATE OR REPLACE VIEW).

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
-- THE ONE NEW COLUMN (SSOT: decision durability rides the decision row's own kind='decision'
-- entry -- no new base table, no separate grade registry).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS decision_grade text;

COMMENT ON COLUMN :"schema".ledger.decision_grade IS
  'Durability grade (kernel/lineage/s36-decision-grade.sql, design/FABLE-GRADED-DECISIONS-SPEC.md):
   nullable, legal ONLY on kind=''decision'' rows (decision_grade_kind_shape below). NO enum, NO
   CHECK on the value -- the kernel stores a word; which words matter is deployment policy
   (apparatus.json mechanisms.standing_decisions.grades), read by hooks/
   sessionstart_durable_decisions.py, bootstrap/templates/pickup.tmpl, and led standing/led
   decision --grade -- never by the kernel itself. Starter vocabulary by convention: ''durable''
   (must survive any context loss). Set via ./led decision --grade <word> "<statement...>".';

-- ============================================================================================
-- SHAPE INVARIANT (illegal states unrepresentable AT CONSTRUCTION, ADR-0000 Rule 1): a grade is
-- legal ONLY on a kind=''decision'' row -- one-way, exactly s28's work_parent_kind_shape pattern
-- (a decision legitimately has decision_grade NULL, so this is NOT an iff).
-- ============================================================================================
ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS decision_grade_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT decision_grade_kind_shape CHECK (
    decision_grade IS NULL OR kind = 'decision');

-- ============================================================================================
-- s20/s22/s23/s24/s26/s28/s29/s30 LESSON RE-APPLIED (most recently re-stated in s30's own
-- header): `ledger_current`/`countersigned_in_force` are `SELECT l.<explicit column list>`, NEVER
-- `l.*` -- a view's `*`-expansion is FROZEN at CREATE VIEW time (verified empirically authoring
-- this delta: a first draft that skipped this re-issue and read `decision_grade` straight through
-- `ledger_current` failed loudly, `column "decision_grade" does not exist`, on this delta's own
-- scratch witness -- the exact class this recurring header note exists to foreclose, caught here
-- rather than shipped). `decision_grade` GAINS BOTH views, APPENDED AT THE END (CREATE OR REPLACE
-- VIEW forbids reordering/renaming existing columns) -- column list = s33's exact list (the
-- lineage's latest re-issue of these two views; s34/s35 added no column) + l.decision_grade.
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
       l.work_discharge, l.decision_grade
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
       l.work_discharge, l.decision_grade
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- standing_decisions -- THE ONE NEW VIEW. In-force (ledger_current-factored, s15+'s own home of
-- the un-superseded reading, s31's declared-type discipline) decision rows carrying a non-NULL
-- grade, ordered by id. A CURRENT-TRUTH reader by construction (factors through ledger_current,
-- contains no raw `ledger` reference of its own) -- a superseded/retracted standing decision
-- drops out automatically, reinstatement-free (see header CLOSURE STATEMENT).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".standing_decisions
    WITH (security_invoker = true) AS
SELECT id, decision_grade AS grade, statement
FROM   :"schema".ledger_current
WHERE  kind = 'decision' AND decision_grade IS NOT NULL
ORDER BY id;

-- ============================================================================================
-- GRANTS: `ledger_current`/`countersigned_in_force` keep their EXISTING grants untouched --
-- CREATE OR REPLACE with an appended (never reordered/renamed) column list preserves every prior
-- grant, s21's own additive-column-order idiom, re-verified here exactly as s24/s26/s28/s30 each
-- re-verified it for their own append. `standing_decisions` is a NEW view -- grant SELECT to
-- :role explicitly, mirroring s20's own obligation-grants idiom for every reader view this
-- lineage exposes to the granted role (the SAME role `led`/`pickup`/the hook query under --
-- without this grant, every one of this delta's three downstream readers would see "permission
-- denied" instead of an honest empty/populated result, exactly the pre-s20 grants gap
-- review_gap's own header still discloses for a DIFFERENT view).
-- ============================================================================================
GRANT SELECT ON :"schema".standing_decisions TO :role;
