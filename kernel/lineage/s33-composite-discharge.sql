-- s33 COMPOSITE WORK-ITEM DISCHARGE (design/FABLE-COMPOSITE-DISCHARGE-SPEC.md, Fable-authored
-- HISTORY: safe -- adds one nullable column (work_discharge, no DEFAULT, so no rewrite and no
-- backfill: every pre-existing row reads NULL = non-composite, byte-for-byte prior behavior),
-- one appended view column, and refusals scoped entirely to the new opt-in type; nothing
-- existing relaxed or reinterpreted.
-- spec, RATIFIED 2026-07-15 (maintainer yes); ledger item composite-parent-autodischarge, claimed
-- by the orchestrator). This delta is AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any
-- live/existing world is the maintainer's act at a FUTURE world's birth (runs-are-strictly-linear
-- ruling, 2026-07-11), never taken here. An ADDITIVE delta applied ON TOP of the s15..s32 kernel
-- (the established remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005
-- Rule 8) and NOT a second hand-copy of any existing mechanism (ADR-0012 P1: one home per
-- mechanism).
--
-- PREREQUISITE: this delta REQUIRES s32 (kernel/lineage/s32-edge-views-single-home.sql) applied
-- first -- it re-issues work_item_current/work_item_violations/work_item_strict_blockers(), all
-- s32-shaped objects (work_edge_parent/work_edge_obligation/discharging_attest-composing bodies),
-- and validate_work_item() (last re-issued s31, s32 deliberately left it untouched). Applying this
-- file on a pre-s32 kernel fails loudly at CREATE OR REPLACE VIEW/FUNCTION time (undefined
-- relation work_edge_parent/work_edge_obligation), the correct, disclosed failure mode for a hard
-- dependency, matching s29/s30/s31/s32's own PREREQUISITE precedent.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): the spec's sec-1 gap, stated once. A parent item whose entire deliverable IS its children
-- has, until this delta, no way to leave the queue except a hand-written close act that restates
-- what the ledger already knows (or it sits open forever). The motivating evidence is the
-- experience-world deployment's own emulation (spec header: rows 128/129 there, a parent closed by
-- hand and disposition-named as an emulation of semantics the kernel does not provide) -- cited,
-- not read, per this commission's own instruction.
--
-- PRINCIPLE (spec sec-2, the whole delta in one line): a composite item's discharge is a DERIVED
-- fact, READ off the SAME obligation calculus s29/s30/s31/s32 already own
-- (`work_item_strict_blockers()`), never a second recursive walker and never a trigger-authored
-- close row (a row nobody stamped would forge agency -- spec sec-3, "Rejected: trigger-authored
-- close rows"). This delta therefore mints exactly: one typed, opt-in column (Element 1); one
-- widened condition on the EXISTING s29 strict-close trigger branch, no new refusal logic (Element
-- 2); one small, composite-aware extension INSIDE `work_item_strict_blockers()`'s own `not_closed`
-- leaf-check, so a nested composite's own children (already flattened into the SAME recursive
-- walk) discharge it without requiring its own close row (Element 3 -- see that element's own
-- comment for why this is a read-conjunction extension, not a second walker); one appended derived
-- column on `work_item_current` that is nothing but a read of that one conjunction (Element 4); one
-- new `work_item_violations` member for the defeasibility polarity (Element 5).
--
-- ELEMENT 1 -- work_discharge COLUMN, ONE-WAY SHAPE, CLOSED VOCABULARY (spec sec-3, first bullet).
-- New nullable column on `ledger`, legal only on `work_opened` rows (the s28 `work_parent` idiom:
-- ONE-WAY, not a two-way iff -- every non-composite item is legally work_discharge IS NULL
-- forever). Exactly one legal non-NULL value: `composite`. CLI: `./led work open <slug> "<title>"
-- --discharge composite` (bootstrap/templates/led.tmpl, following the existing `--parent` flag
-- idiom -- live column-existence gated, the SAME convention `--parent`/`--strict`/`--type` already
-- use, so this file does not break `led work open` on a world whose kernel predates s33).
--
-- ELEMENT 2 -- STRICT-BY-TYPE (spec sec-3, second bullet). `validate_work_item()` (extended a
-- SIXTH time -- the SAME function s22 defined and s28/s29/s30/s31 extended; s32 deliberately left
-- it untouched -- CREATE OR REPLACE, not a second copy, ADR-0012 P1) now computes, for a
-- `work_closed` row, whether NEW.work_slug's OWN `work_opened` row carries
-- `work_discharge = 'composite'`, and if so, runs the row through the EXISTING s29 strict-close
-- branch (Element C of s29) exactly as if `work_strict_close` were true -- the widened condition
-- is `COALESCE(NEW.work_strict_close, false) OR is_composite`, nothing else in that branch changes,
-- byte-for-byte. NO NEW REFUSAL CODE: the type sets the flag (spec's own words, quoted in this
-- commission). The strict+deferred contradiction (a `--review-deferred` close of a composite slug)
-- fires through the SAME pre-existing RAISE, unconditionally, because the widened condition also
-- widens entry into that guard -- named here so a reader does not have to re-derive it: a composite
-- close therefore ALSO requires `--review-witness` (never `--review-deferred`), exactly s29
-- Element C's existing text, now reached by two doors (`--strict` or `work_discharge='composite'`)
-- instead of one.
--
-- ELEMENT 3 -- work_item_strict_blockers() EXTENDED A THIRD TIME (s29-defined, s30/s31/s32
-- extended; CREATE OR REPLACE, the SAME function, ADR-0012 P1) -- THE ONE CHANGE THAT MAKES NESTED
-- COMPOSITES WORK WITHOUT A SECOND WALKER. The pre-existing `not_closed` leaf-check requires every
-- non-root tree member to carry its own `work_closed` row. A composite tree member that is itself
-- discharged PURELY BY DERIVATION (spec's own text: "a hand-written close remains legal and
-- optional... it never substitutes for" the derived fact) has NO close row by design -- so an
-- outer (grandparent) call to this SAME function would, unmodified, misreport a fully-resolved
-- inner composite as an unresolved blocker. THE FIX (a read-conjunction extension, not a second
-- walker, per the spec's own "no second tree walker" mandate): a tree member is exempted from the
-- own-close-row requirement IFF (a) its own `work_opened` row (read via `ledger_current`, the
-- in-force reading, s31's own posture) carries `work_discharge = 'composite'`, AND (b) it has AT
-- LEAST ONE CHILD already present in THIS SAME flattened `edges`/`tree` walk (`EXISTS (SELECT 1
-- FROM edges e2 WHERE e2.parent = t.slug)`) -- condition (b) is exactly spec sec-3's "Zero children
-- => never vacuously discharged" carried one level up: a composite with no children is NOT
-- exempted, and still needs its own close row to read resolved from an ancestor's point of view.
-- When both hold, the member's OWN resolution is fully delegated to its descendants, which are
-- ALREADY tree members of this SAME recursive walk and ALREADY separately contribute their own
-- `not_closed`/`review_unresolved` rows to this SAME UNION result -- so nested composites resolve
-- for free, with zero additional recursion, by construction. Every other clause (`edges`, `tree`,
-- `closes`, `review_unresolved`) is UNCHANGED, byte-for-byte, from s32's own version.
--
-- ELEMENT 4 -- work_item_current GAINS effective_state (spec sec-3, third bullet + sec-3b).
-- Appended column (the s20 column-complete lesson, re-applied a SIXTH time). For a non-composite
-- item: `effective_state = state`, unconditionally (byte-identical behavior -- spec's own explicit
-- acceptance bullet). For a declared composite: if it carries a `work_closed` row (`state =
-- 'closed'`, i.e. a hand-close happened at some point), the DERIVED reading ALWAYS WINS over that
-- hand-close (spec sec-3b: "Derived state ALWAYS wins over a hand-close... a tree defeated AFTER a
-- hand-close re-surfaces the composite as open") -- `effective_state` re-checks
-- `work_item_strict_blockers(slug)` on EVERY read and reads `closed` only while blockers stay
-- empty, `open` the instant a later defeat (an attest review superseded) makes them non-empty
-- again, in the SAME read, no propagation machinery (spec sec-3b, first bullet: review defeat
-- propagates by construction, because `work_item_strict_blockers` stores no verdict). If it carries
-- NO close row: `discharged-by-obligations` when it has at least one direct child (via the s32
-- `work_edge_parent` view, in-force) AND `work_item_strict_blockers(slug)` returns empty; `open`
-- otherwise -- INCLUDING the zero-children case (never vacuously discharged, spec sec-3, its own
-- named LIMIT: "the parent opened before its decomposition exists must wait for it").
--
-- ELEMENT 5 -- work_item_violations GAINS closed_but_tree_defeated (spec sec-3b, second bullet:
-- "the divergence is surfaced as a new work_item_violations member... never silently reconciled in
-- either direction"). One row per composite slug that carries a `work_closed` row (in-force) AND
-- whose `work_item_strict_blockers(slug)` is CURRENTLY non-empty -- exactly the case
-- `effective_state` above reads `open` while the raw `state` column still reads `closed`. Detail
-- names the close row id and the live blocker list (the same `string_agg` shape the strict-close
-- trigger refusal itself already uses). Every PRE-EXISTING member of this view (s22/s28/s30/s31/
-- s32's own eight) is UNCHANGED, byte-for-byte, below.
--
-- WHAT THIS DELTA DELIBERATELY DOES NOT DO (ADR-0013 Rule 4, filed not buried):
--   - NO second recursive obligation-tree walker -- Element 3 extends the ONE existing conjunction
--     `work_item_strict_blockers()` already owns; `effective_state`/`closed_but_tree_defeated` are
--     both pure reads of that same function, never a second derivation.
--   - NO trigger-authored close row of any kind -- a discharged-by-obligations composite carries no
--     ledger row at all beyond its own `work_opened` act; "discharged" is computed at read time,
--     every time, from facts that already exist (spec sec-3's own "Rejected" list, re-applied).
--   - NO new precedence mechanism -- s30 `blocks-close` edges compose with this delta exactly as
--     they already compose with s29 strict close; this delta adds no second ordering primitive.
--   - NO change to `led work list`/`led work violations`/`led work asof` -- this commission's own
--     read-surface scope names exactly `./pickup`'s work-item section and
--     `hooks/stop_clean_exit.py`'s INFORMATIONAL open-items line; `led work list`'s own default
--     filter is untouched (ADR-0004 minimal-touch) -- named here as a filed, not silently swept,
--     scope boundary: a discharged-by-obligations composite still appears in `led work list`'s
--     default `state <> 'closed'` view today (it reads its raw `state` column, unchanged by this
--     delta), a future pass may widen that read-surface's own scope on its own commission.
--   - NO change to `work_item_descendants` (s28) -- it reads `work_item_current`'s pre-existing
--     `parent_slug` column only, untouched by this delta.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: a work item's `work_discharge` is a MANDATORY-when-composite, closed-vocabulary,
--     one-way-shape-checked fact set ONLY at the item's opening act, never later. Every future close
--     of a composite slug is a strict close, enforced by widening the EXISTING s29 strict-close
--     trigger branch's entry condition, never by new refusal code. `effective_state` is a PURE READ
--     of `work_item_strict_blockers()` for every composite item, on every read, with derived state
--     always overriding a hand-close's raw `state`; a composite with zero children is never
--     vacuously discharged. `closed_but_tree_defeated` surfaces, never silently reconciles, the one
--     divergence a hand-close-then-later-defeat can produce.
--
--   - QUANTIFICATION UNIVERSE -- enumerated by re-reading every table/view/function the s15..s32
--     chain exposes to :role (mirroring s28/s29/s30/s31/s32's own re-verification discipline),
--     checked against the one new column and the objects this delta re-issues:
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table (work_discharge
--         rides the existing `work_opened` row, the s28/s29/s30 "no new base table" doctrine).
--       VIEWS re-read for the wildcard/column-complete class s20/s22/s23/s24/s26/s28/s29/s30 all
--         named: ledger_current / countersigned_in_force -- GAIN the ONE new column
--         (work_discharge), APPENDED AT THE END, HERE, else the column-complete class recurs one
--         column later (the s20 lesson, re-applied a SIXTH time). work_item_current -- GAINS
--         effective_state (Element 4), appended. work_item_violations -- GAINS
--         closed_but_tree_defeated (Element 5), appended to the UNION list. work_item_descendants
--         -- re-verified NOT a member (reads work_item_current's pre-existing parent_slug column
--         only, untouched). review_gap / question_status / work_review_gap / discharging_attest /
--         work_edge_parent / work_edge_blocks_close / work_edge_obligation / countersigned_in_force
--         -- re-verified NOT members beyond the column-complete append above (none reads or is
--         shaped by work_discharge).
--       KIND VOCABULARY -- unchanged. This delta adds no new `kind` value: work_discharge rides the
--         EXISTING `work_opened` kind's own row, one more optional column beside work_parent.
--       GRANTS -- mirrors s28/s29/s30/s31/s32's own posture: no new view is added by this delta (no
--         table/view-level grant change is needed); every re-issued view/function keeps its exact
--         prior signature plus the one appended column (s21's additive-column-order idiom).
--       READER TYPING (s31's standing gate, gates/ledger_reader_allowlist.py) -- work_item_current
--         gains a call to `work_item_strict_blockers()` (already a ZERO-raw-ledger-leg, vestigial
--         allowlist entry per s32) -- no new raw-`ledger` reference is introduced anywhere by this
--         delta; work_item_violations' three new CTEs (composites/composite_hand_closed/
--         closed_but_tree_defeated) read `ledger_current` exclusively, matching its own
--         orphaned_by_retraction member's posture -- no NEW raw leg. `gates/ledger_reader_
--         allowlist.py`'s scratch CHAIN gains `s33-composite-discharge.sql` (this delta's own
--         commission-scoped edit) so the gate's scratch apply exercises this delta's re-issued
--         objects; no ALLOWLIST dict entry needs to change (nothing new to declare).
--       ENGINE -- `engine/lp/work_review.lp` gains ONE new EDB fact family (`w_composite/1`) and
--         ONE amended rule (`w_not_closed/1`, Element 3's own read-conjunction extension, mirrored
--         independently -- SQL and lp encodings stay independent per the standing do-not-abstract
--         ruling, I6). `engine/ledger_floor.py`'s `work_review_floor_atoms()` gains the matching,
--         independently-derived SQL extension to its own `not_closed` CTE. `engine/ledger_edb.py`'s
--         `export_work()` gains the `work_discharge` capability (gated, s33-only) and emits
--         `w_composite(Slug)` facts. `WORK_REVIEW_PREDS`/`WORK_LAYER_PREDS`
--         (engine/ledger_differential.py) are UNCHANGED -- no new predicate NAME, only a changed
--         extension of the existing `w_tree_unresolved/1` derivation, so `./judge --layer work`
--         compares it automatically once both producers are updated, no new registry/differential
--         wiring needed. `effective_state`/`work_discharge` themselves are NOT modeled as ASP atoms
--         (per this file's own header note, and the commission's own "ONLY if parity requires it"
--         instruction): they are a pure SQL presentation of the SAME derivation the ASP side already
--         computes via w_tree_unresolved; only the underlying derivation (composite exemption in the
--         tree walk) needed a twin, and it has one.
--
--   - DENOMINATION: work_discharge is `text`, closed vocabulary (`{composite}` today, extensible
--     only by ratified amendment per s30's own precedent for a closed-vocabulary column). The item
--     key is the SLUG (s22/s28/s29/s30's own denomination, re-applied); effective_state's identity
--     is the SAME slug work_item_current already denominates every other column by.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT class-ratified fail-safe on
-- its own motion -- it is the Fable-authored, maintainer-ratified delta the spec's own header names
-- (RATIFIED 2026-07-15) because it mints new discharge SEMANTICS (a new way for an item to leave
-- the queue, spec sec-4's own text) even though every individual mechanism, in isolation, adds only
-- a refusal/column/derived-view-member: the new column is opt-in and one-way (no existing item's
-- shape changes); Element 2 widens an EXISTING refusal's entry condition, scoped entirely to the
-- new opt-in `composite` type (no existing item's close behavior changes); Element 3's read-
-- conjunction extension is scoped to composite tree members only (a non-composite tree member's
-- `not_closed` reading is byte-identical to s32's); Element 4/5 are pure additions (one appended
-- column, one appended violations member). Named for the record per the standing decision-tree
-- text, not claimed as the routing reason (ratification already happened via the spec itself).
--
-- LIMITS (pre-registered, matching s22/s26/s28/s29/s30/s31/s32's own disclosure convention):
--   - The residual vacuous-discharge RACE the spec itself names (sec-3): "all currently-open
--     children close before a sibling is opened" is not mechanically closable in an append-only
--     ledger -- named as a LIMIT there, inherited here unchanged; the standing operating discipline
--     (decompose the ENTIRE commission into items before implementing) is the mitigation, not a
--     mechanism this delta adds.
--   - The SUPERSEDED-CLOSE polarity (a defeated `work_closed` row on a NON-composite item still
--     reading closed) remains exactly as `supersession-semantics-closure`'s own spec named it:
--     UNEXERCISED, deferred to that work's own acceptance (s31's own header, unchanged by this
--     delta -- composites inherit the SAME bound: a composite's own hand-close leaf, once
--     `witnessed`, has no discharge-attest mechanism to defeat, matching a non-composite item's
--     identical close-leaf blind spot exactly, named not hidden).
--   - Like every trigger-enforced refusal in this lineage, Element 2's widened strict-close branch
--     binds ONLY the granted `:role`'s ordinary INSERT path -- a schema-owner/superuser with DDL
--     privilege can disable the trigger or write directly, the same disclosed bound s26/s28/s29/
--     s30/s31 already name.
--   - `led work list`/`led work violations`/`led work asof` are NOT updated to read
--     `effective_state` -- named above under WHAT THIS DELTA DELIBERATELY DOES NOT DO, a filed scope
--     boundary, not an oversight.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s22/s28/s29/s30/s31/s32):
-- schema/kern/role are psql variables so this delta is VALIDATED on a throwaway substrate before
-- any real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s33val -v kern=s33val_kernel -v role=s33val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql \
--        -f s29-obligation-item-key-and-typed-close.sql -f s30-typed-dependency-edges.sql \
--        -f s31-supersession-uniform-retraction.sql -f s32-edge-views-single-home.sql \
--        -f s33-composite-discharge.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired by the orchestrator's seam-integration pass into
--   `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` (NOT taken here -- this commission's own brief:
--   "Do NOT wire LINEAGE_CHAIN"). Authored and scratch-witnessed on scratch schema pairs in the TOY
--   db only -- NOT applied to any live schema by this pass.
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
-- ELEMENT 1 -- work_discharge COLUMN, ONE-WAY SHAPE, CLOSED VOCABULARY.
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS work_discharge text;

COMMENT ON COLUMN :"schema".ledger.work_discharge IS
  'Composite discharge type (kernel/lineage/s33-composite-discharge.sql): legal only on a
   work_opened row (one-way shape CHECK -- every non-composite item is work_discharge IS NULL
   forever), closed vocabulary, ONE legal value: composite. Set exactly once, at the item''s
   opening act (CLI: ./led work open <slug> "<title>" --discharge composite), never later --
   composite-ness is a declared TYPE, not something inferred from having children (spec''s own
   Rejected list: implicit typing would retroactively change every EXISTING parent item''s
   semantics). Effect: every future close of this slug is a STRICT close (validate_work_item(),
   widened below -- Element 2), and work_item_current.effective_state (Element 4) reads this
   item''s obligation tree instead of its own close row.';

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_discharge_kind_shape;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_discharge_kind_shape CHECK (
    work_discharge IS NULL OR kind = 'work_opened');

ALTER TABLE :"schema".ledger DROP CONSTRAINT IF EXISTS work_discharge_check;
ALTER TABLE :"schema".ledger ADD CONSTRAINT work_discharge_check CHECK (
    work_discharge IS NULL OR work_discharge = 'composite');

-- ============================================================================================
-- s20/s22/.../s32 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN the ONE new
-- column, APPENDED AT THE END. Explicit column lists throughout -- never `l.*`. Re-issued HERE,
-- BEFORE Element 3 below, because work_item_strict_blockers() (Element 3) reads
-- ledger_current.work_discharge -- the re-issue must land before any consumer of the new column.
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
       l.work_discharge
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
       l.work_discharge
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".discharging_attest da WHERE da.regards_id = l.id);

-- ============================================================================================
-- ELEMENT 2 -- validate_work_item() EXTENDED A SIXTH TIME: STRICT-BY-TYPE. Every branch other
-- than the work_closed strict-close entry condition is BYTE-IDENTICAL to s31's version (s32 left
-- this function untouched). The ONLY change: `is_composite` is computed for a work_closed row,
-- and the strict-close block's own entry condition widens from
-- `COALESCE(NEW.work_strict_close, false)` to `COALESCE(NEW.work_strict_close, false) OR
-- COALESCE(is_composite, false)` -- NOTHING INSIDE that block changes (no new refusal code, the
-- type sets the flag, spec sec-3).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
  is_composite boolean;
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
    -- s29 (unchanged, byte-for-byte): epoch-gated review-disposition presence.
    IF NEW.kind = 'work_closed'
       AND NEW.id > COALESCE((SELECT epoch FROM migration_epoch LIMIT 1), 0)
       AND NEW.work_review_disposition IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: work_closed row for item ''%'' (ledger id %) carries no review disposition — every close act past this world''s migration epoch (id %, see %.migration_epoch) must be witnessed or deferred, never silent (s29 Element B, sec-10 epoch amendment). Retry with --review-witness <ref> or --review-deferred.', NEW.work_slug, NEW.id, (SELECT epoch FROM migration_epoch LIMIT 1), TG_TABLE_SCHEMA;
    END IF;
    -- s33 Element 2 -- STRICT-BY-TYPE: a composite slug's close is treated as if
    -- work_strict_close were set. Read raw ledger for the slug's own work_opened row
    -- (write-boundary trigger, history-typed -- the SAME posture every other identity/shape check
    -- in this function already has, gates/ledger_reader_allowlist.py's own ALLOWLIST entry for
    -- validate_work_item names this explicitly).
    IF NEW.kind = 'work_closed' THEN
      is_composite := EXISTS (SELECT 1 FROM ledger WHERE kind = 'work_opened'
                              AND work_slug = NEW.work_slug AND work_discharge = 'composite');
    END IF;
    -- s29 (Element C, unchanged, byte-for-byte INSIDE the block) -- s33 widens ONLY the entry
    -- condition (OR COALESCE(is_composite, false)); no other line in this block changes.
    IF NEW.kind = 'work_closed'
       AND (COALESCE(NEW.work_strict_close, false) OR COALESCE(is_composite, false)) THEN
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
DROP TRIGGER IF EXISTS validate_work_item ON :"schema".ledger;
CREATE TRIGGER validate_work_item BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_work_item();

-- ============================================================================================
-- ELEMENT 3 -- work_item_strict_blockers() EXTENDED A THIRD TIME (s29-defined, s30/s31/s32
-- extended): `not_closed` gains the composite-with-children exemption (see header). `edges`,
-- `tree`, `closes`, `review_unresolved` are UNCHANGED, byte-for-byte, from s32's version.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".work_item_strict_blockers(root_slug text)
    RETURNS TABLE(blocking_slug text, reason text) LANGUAGE sql STABLE
    SET search_path = :"schema", pg_temp AS $fn$
  WITH RECURSIVE
  edges AS (
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
    -- s33 Element 3: a composite tree member (its own IN-FORCE work_opened row carries
    -- work_discharge='composite') that has AT LEAST ONE CHILD in this SAME flattened `edges`
    -- walk is exempted from needing its own close row -- its resolution is fully delegated to
    -- its own children, already tree members here, already separately contributing their own
    -- not_closed/review_unresolved rows to this SAME UNION. A composite with ZERO children in
    -- this walk is NOT exempted (never vacuously discharged, spec sec-3).
    SELECT t.slug, 'item is not yet closed'::text AS reason
    FROM tree t
    WHERE t.slug <> root_slug
      AND NOT EXISTS (SELECT 1 FROM closes c WHERE c.slug = t.slug)
      AND NOT (
        EXISTS (SELECT 1 FROM ledger_current oo WHERE oo.kind = 'work_opened'
                AND oo.work_slug = t.slug AND oo.work_discharge = 'composite')
        AND EXISTS (SELECT 1 FROM edges e2 WHERE e2.parent = t.slug)
      )
  ),
  review_unresolved AS (
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
-- ELEMENT 4 -- work_item_current GAINS effective_state, APPENDED. Every other column
-- (state/resolution/witness/claimant/parent_slug/review_disposition/review_ref) is UNCHANGED,
-- byte-for-byte, from s32's version.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".work_item_current
    WITH (security_invoker = true) AS
WITH opened AS (
  SELECT work_slug AS slug, work_title AS title, work_parent AS parent_slug,
         work_discharge AS discharge, id AS opened_id
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
),
-- s33: direct-child count via the s32 single-home edge view, IN-FORCE (each edge row joined
-- against ledger_current on its own carrying row -- the SAME reasoning work_edge_obligation
-- already uses one level up).
child_counts AS (
  SELECT e.parent_slug AS slug, count(*) AS n
  FROM   :"schema".work_edge_parent e
  JOIN   :"schema".ledger_current lc ON lc.id = e.edge_row_id
  GROUP BY e.parent_slug
)
SELECT o.slug, o.title,
       CASE WHEN c.slug IS NULL THEN 'open' ELSE 'closed' END AS state,
       c.resolution, c.witness, cl.claimant, o.parent_slug,
       c.review_disposition, c.review_ref,
       -- s33 Element 4: effective_state. Non-composite: byte-identical to state (spec's own
       -- explicit acceptance bullet). Composite, hand-closed: derived reading ALWAYS wins (spec
       -- sec-3b) -- re-checks work_item_strict_blockers() on every read; a later defeat re-opens
       -- it in the SAME read even though the raw work_closed row still stands (history). Composite,
       -- never hand-closed: discharged-by-obligations iff >=1 direct child AND blockers empty;
       -- zero children never vacuously discharges (spec sec-3).
       CASE
         WHEN o.discharge IS DISTINCT FROM 'composite' THEN
           CASE WHEN c.slug IS NULL THEN 'open' ELSE 'closed' END
         WHEN c.slug IS NOT NULL THEN
           CASE WHEN EXISTS (SELECT 1 FROM :"schema".work_item_strict_blockers(o.slug))
                THEN 'open' ELSE 'closed' END
         WHEN COALESCE(cc.n, 0) >= 1
              AND NOT EXISTS (SELECT 1 FROM :"schema".work_item_strict_blockers(o.slug))
           THEN 'discharged-by-obligations'
         ELSE 'open'
       END AS effective_state
FROM   opened o
LEFT JOIN claimed      cl ON cl.slug = o.slug
LEFT JOIN closed       c  ON c.slug  = o.slug
LEFT JOIN child_counts cc ON cc.slug = o.slug;

-- ============================================================================================
-- ELEMENT 5 -- work_item_violations GAINS closed_but_tree_defeated. Every PRE-EXISTING member
-- (duplicate_open, shipped_without_witness, depends_on_unknown_slug, dependency_cycle,
-- dangling_parent, parent_cycle, blocks_close_cycle, orphaned_by_retraction x4) is UNCHANGED,
-- byte-for-byte, from s32's version.
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
  -- s33 Element 5: a declared composite that carries an IN-FORCE work_closed row (a hand-close
  -- happened) whose obligation tree is CURRENTLY non-empty -- the exact case where
  -- work_item_current.effective_state reads 'open' while the raw state column still reads
  -- 'closed'. Reads ledger_current exclusively (current-truth, matching orphaned_by_retraction's
  -- own posture) -- no new raw-ledger leg.
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
SELECT 'orphaned_by_retraction', slug, 'surviving child work_opened row ' || id || ' names a retracted parent opening act (' || parent_slug || ')' FROM orphan_children
UNION ALL
SELECT 'closed_but_tree_defeated', slug, 'close row ' || close_id || '; unresolved: ' || blockers FROM closed_but_tree_defeated;

-- ============================================================================================
-- GRANTS: none needed -- no new view/column beyond the one column-complete append above; every
-- re-issued view/function keeps its exact prior signature plus the one appended column (s21's
-- additive-column-order idiom, trivially satisfied).
-- ============================================================================================
