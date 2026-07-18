-- s47 CLAIM-ON-CLOSED REFUSAL (design/FABLE-CLAIM-ON-CLOSED-REFUSAL-SPEC.md, RATIFIED BUILD BASIS
-- -- maintainer sign-off 2026-07-18, overnight batch item 3, following the witnessed defect at
-- ledger rows 1539/1540 and its filing at row 1544 / work item claim-on-closed-item-admitted;
-- Fable-authored). FAIL-SAFE-ADDITIVE class (CLAUDE.md ORCHESTRATION, class-ratified 2026-07-09):
-- this delta ONLY adds a refusal -- nothing existing is relaxed, no existing refusal loosened, no
-- existing edge/kind/column semantics changed. Sonnet-executed per the standing delegation
-- contract, from this ratified spec.
--
-- ADR-0000 2(a), the two questions this delta answers: (a) the TYPE that forecloses "claimed after
-- closed" is a claim-time construction refusal keyed on the slug's own in-force close, exactly the
-- same shape s39 already gave "claimed before its blocks-start antecedent resolved" -- a THIRD
-- construction-time precondition on the SAME leaf, not a second competing mechanism (ADR-0012 P1);
-- (b) the operational lapse (ADR-0000 Rule 2(b), self-directed, executive-owned) is that s39's own
-- claim-time leaf checked ONE precondition (blocks-start antecedents) and never asked whether the
-- claimed slug's OWN close was itself the disqualifying fact -- a closed item was never on s39's
-- own commission text, so no check existed for it at all, not a loosened one. ADR-0002: the fix
-- lands at construction time, the loudest rung in ADR-0002's own hierarchy -- an admitted
-- work_claimed row on a closed slug is now unconstructable, never a downstream guard/report.
--
-- HISTORY: safe -- ONE existing object (validate_work_item_claim, s39's leaf) re-issued with ONE
-- additional check PREPENDED before its existing blocks-start blockers check (this delta's own
-- commission text, verbatim: "placed before the existing blocks-start check"); every line of s39's
-- own blockers logic below is BYTE-IDENTICAL, unchanged, unmoved. No table, column, kind, or CHECK
-- constraint of any kind is added or altered -- the closed-item fact is read entirely off the
-- EXISTING ledger_current projection (s31, the ONE home of "in force"), the SAME projection
-- work_item_current's own `closed` CTE already reads (s31 Element 1: DISTINCT ON work_slug ORDER
-- BY id DESC over ledger_current, the slug's own latest in-force close). No new kind, no new
-- column, no new view. The dispatcher (validate_work_item, s35's own dispatcher-with-leaves,
-- extended s37/s38/s39) is NOT touched -- it already calls validate_work_item_claim for every
-- work_claimed row (s39 Element 3's own wiring), so this delta's new check rides that existing
-- call site with zero dispatcher edit. compute_row_hash untouched.
--
-- WHY (the defect, verbatim-shaped, spec §1): witnessed 2026-07-18 (ledger rows 1539/1540), `led
-- work claim` wrote work_claimed rows for slugs whose items were already closed and shipped.
-- Nothing in the kernel refused this -- s39's own claim-time leaf checks blocks-start antecedents
-- only, never the claimed slug's OWN close. ADR-0000 2(a): "claimed after closed" was
-- representable and should not be. This delta closes exactly that gap, on the SAME leaf s39
-- introduced for the SAME lifecycle moment (claim-time), never a second, competing claim-refusal
-- mechanism (ADR-0012 P1).
--
-- PREREQUISITE: this delta REQUIRES s39 (kernel/lineage/s39-blocks-start.sql) applied first -- it
-- re-issues validate_work_item_claim, the leaf s39 defined, in the EXACT shape s39 left it (no
-- other delta between s39 and this one touches that function). Applying this file on a pre-s39
-- kernel fails loudly at CREATE OR REPLACE FUNCTION time (there is no validate_work_item_claim to
-- re-issue, and no work_item_blocks_start_blockers for the preserved blockers query to call), the
-- correct, disclosed failure mode for a hard dependency, matching every prior delta's own
-- PREREQUISITE precedent.
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
-- ELEMENT 1 -- validate_work_item_claim (s39's leaf, CREATE OR REPLACE -- ADR-0012 P1, not a
-- second copy) GAINS ONE new check, PREPENDED before the pre-existing blocks-start blockers check
-- (spec §2, verbatim placement instruction). The pre-existing DECLARE/blockers-query/RAISE/RETURN
-- below this new block is BYTE-IDENTICAL to s39's own issue of this function -- only the two new
-- DECLARE variables and the one new IF block are appended/prepended; nothing pre-existing is
-- reordered past, narrowed, or reworded.
--
-- THE NEW CHECK: reads the slug's own latest IN-FORCE work_closed row straight off
-- ledger_current (s31's ONE home of "in force" -- a close retracted by s31 supersession is, by
-- ledger_current's own construction, simply absent from this read; no second "is this close still
-- standing" predicate is invented here). Mirrors work_item_current's own `closed` CTE (s31 Element
-- 1) exactly: DISTINCT-latest-by-id over ledger_current, scoped to this one slug. If a row is
-- found, the claim is refused, naming the closing row's OWN id and resolution (the two facts the
-- spec's own commission text requires named), and the two honest next acts: open a NEW item for
-- any follow-on work (the slug itself stays permanently burned-closed, matching work_opened's own
-- slug-burn posture, s22/FAQ), or -- if the close itself is wrong -- retract it first via the
-- supersession recipe (design/USER-RECIPES-FAQ.md's "Correcting the record" section), then retry
-- the claim. Diction and citation style mirror s39's own blocks-start refusal one paragraph below,
-- verbatim in structure ("Ledger policy: ... refused — ...", the FAQ section cited by name, never
-- a raw-SQL fourth alternative invented here).
--
-- NOTE (found live, this delta's own first scratch-witness attempt -- the SAME finding s39's own
-- Element 4 header already recorded, re-confirmed here rather than silently relied on): a function
-- body inside $fn$...$fn$ is NOT a site psql performs :"var" substitution in (confirmed empirically
-- a second time, this delta's own plpgsql body, not merely s39's LANGUAGE sql one) -- the new
-- `ledger_current` reference below is UNQUALIFIED, resolving via the SET search_path clause, the
-- SAME house idiom s39's own leaf already used for `work_item_blocks_start_blockers` one line down.
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_work_item_claim(r :"schema".ledger)
    RETURNS :"schema".ledger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  blockers text;
  closer_id bigint;
  closer_resolution text;
BEGIN
  -- s47: the NEW closed-item check, PREPENDED before s39's own blocks-start blockers check below
  -- (spec §2's own placement instruction). "In force" is read the SAME way work_item_current's own
  -- `closed` CTE reads it (s31 Element 1) -- ledger_current, DISTINCT-latest-by-id per slug --
  -- never a second, competing "is this item closed" derivation minted for this one check.
  SELECT c.id, c.work_resolution INTO closer_id, closer_resolution
    FROM ledger_current c
    WHERE c.kind = 'work_closed' AND c.work_slug = r.work_slug
    ORDER BY c.id DESC LIMIT 1;
  IF closer_id IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: claim of work item ''%'' refused — it is already closed (ledger row %, resolution %) and a closed item is not claimable (s47). If there is follow-on work, open a NEW item for it (./led work open <new-slug> ...) -- the closed slug itself stays burned, matching a work item''s own permanent slug-burn posture; if the close itself is wrong, first retract it via the supersession recipe (design/USER-RECIPES-FAQ.md''s "Correcting the record" section), then retry the claim.', r.work_slug, closer_id, closer_resolution;
  END IF;
  -- s39 (BYTE-IDENTICAL below, unchanged, unmoved): the pre-existing blocks-start blockers check.
  SELECT string_agg(format('%s (%s)', b.blocking_slug, b.reason), '; ' ORDER BY b.blocking_slug)
    INTO blockers
    FROM work_item_blocks_start_blockers(r.work_slug) b;
  IF blockers IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: claim of work item ''%'' refused — its blocks-start antecedent(s) are not yet resolved: %. Claim and finish each named antecedent first (./led work claim <antecedent>, then ./led work close <antecedent> <resolution> ...), or -- if the dependency itself is wrong -- correct the record (see design/USER-RECIPES-FAQ.md''s "Correcting the record" section for the supersession recipe: the mistaken work_depends_on row is superseded, then a fresh row is issued with the right edge_type) (s39: claim-time precondition foreclosure, direct antecedents only — see work_item_blocks_start_blockers''s own LIMITS).', r.work_slug, blockers;
  END IF;
  RETURN r;
END; $fn$;

-- ============================================================================================
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment; spec §4, verbatim):
--
--   - INVARIANT: a work_claimed row is admitted iff (1) the slug has an opening act (s22), (2) it
--     carries no unresolved blocks-start antecedent (s39, unchanged), AND (3) the slug has no
--     in-force work_closed row (s47, this delta) -- three independent construction-time
--     preconditions, all on the SAME leaf, none relaxing another.
--
--   - QUANTIFICATION UNIVERSE -- enumerated OUTWARD (ADR-0000's own 2026-07-02 amendment text,
--     re-read against every kind that carries every column this delta constrains, not merely the
--     kind the feature is FOR -- the s38-week lesson):
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table, no new column. The
--         closed-item fact rides the EXISTING work_closed kind's EXISTING work_resolution column
--         and the ledger's EXISTING kind/work_slug/supersedes columns (via ledger_current), all
--         s22/s26/s31's own pre-existing columns -- nothing new to enumerate.
--       EVERY KIND THAT CARRIES work_slug: unchanged by this delta -- it reads work_slug on TWO
--         pre-existing kinds (work_claimed, the row under construction; work_closed, the row
--         queried), neither newly scoped, neither widened.
--       VIEWS re-read for the wildcard/column-complete class (s20/s22/.../s39 all named):
--         ledger_current / countersigned_in_force -- unchanged, this delta adds no column and
--         reads both purely as an EXISTING consumer (exactly work_item_current's own posture) --
--         re-verified NOT members needing re-issue. work_item_current -- unchanged, re-verified
--         NOT a member: this delta does not re-issue it, it re-derives the SAME `closed` fact
--         inline (a second textual instance of the SAME query shape, not a second SEMANTIC
--         derivation -- ADR-0012 P1's "one factoring" is about the MEANING of "in force," which
--         stays ledger_current throughout, not about a single shared SQL text object; the
--         alternative, a cross-function call into work_item_current's own CTE, is not
--         representable in SQL without a second view/function of its own, which would be the
--         actual second mechanism ADR-0012 P1 warns against here).
--       KIND VOCABULARY -- unchanged. No new `kind` value; the refusal fires on the EXISTING
--         work_claimed kind (s22) by consulting the EXISTING work_closed kind (s22/s29/s37/s38).
--       GRANTS -- unchanged. validate_work_item_claim needs no explicit GRANT (Postgres grants
--         EXECUTE to PUBLIC by default, s39's own precedent for this exact function, re-verified
--         unchanged here -- a CREATE OR REPLACE does not reset a function's grants).
--       ENGINE -- VERIFIED, not merely asserted, per this codebase's own standing instruction to
--         check engine/lp/ and engine/ledger_*.py for every writer-side widening: this delta adds
--         NO new predicate, NO new fact emission, and touches NEITHER engine/ledger_edb.py NOR
--         engine/lp/work_items.lp NOR engine/ledger_floor.py at all -- it is a PURE
--         construction-time refusal (a row that fails this check is simply never written; there
--         is no admitted-row shape for the ASP/SQL floor to diverge over, exactly s30/s32/s33/
--         s39's own "construction-time-only, no T_now derivation" precedent for their own
--         self-edge/dangling-antecedent/cycle refusals). `./judge`'s existing SQL/ASP
--         differential is UNAFFECTED (it derives T_now facts from rows that DID get written; a
--         row this delta refuses never reaches that derivation in the first place) and continues
--         to AGREE -- witnessed as part of this delta's own acceptance (see the commit record and
--         seen-red/s47-claim-on-closed-refusal/run_fixtures.py).
--
--   - DENOMINATION: unchanged. work_resolution stays the existing text vocabulary
--     (shipped|superseded|dropped|deferred, s29/s37); "closed" itself stays denominated in
--     ledger_current's own in-force reading of the work_closed kind (s31), never a second,
--     competing "closed-ness" vocabulary minted for this one check.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE. This
-- delta ONLY adds ONE refusal (a work_claimed INSERT is refused when its slug carries an in-force
-- work_closed row) -- nothing existing is relaxed: s39's own blocks-start blockers check is
-- byte-identical and unmoved below its new prepended sibling, the dispatcher is untouched, and no
-- column/kind/CHECK is added or widened. Per the standing ruling this qualifies for entry into the
-- birth chain without a per-delta maintainer question, PENDING the scratch-witness-on-both-
-- polarities-with-SQL/ASP-AGREE this delta's own commissioning spec (§3) requires and this file's
-- own witness pass (seen-red/s47-claim-on-closed-refusal/run_fixtures.py) performs -- named here
-- for the record, not claimed as a bypass of that witness.
--
-- LIMITS (pre-registered, matching s22/.../s39's own disclosure convention; spec §4's own
-- enumerated non-goals, named so silence is not drift):
--   - Claiming an ALREADY-CLAIMED item remains legal -- multiple claimants are representable by
--     design (the ledger records, it does not lock); this delta's own check is scoped to the
--     claimed slug's CLOSE state only, never its claim history, and does not touch that posture.
--   - Claim-after-close-RETRACTION is legal by construction above (a superseded close is, by
--     ledger_current's own construction, simply absent from this check's read) -- exercised as
--     WORLD GREEN leg 2 in this delta's own fixture.
--   - A CLOSE on a never-claimed item is s22/s38's business, not this delta's -- this delta gates
--     claim-time only, never close-time, mirroring s39's own single-lifecycle-moment scoping.
--   - The class presumed too narrow here is "events admissible on a settled item" (spec §4,
--     verbatim) -- the next candidate axes (depends-edges on closed items, double-close) are
--     NAMED, out-of-scope observations for this delta's own builder to file if witnessed during
--     the witness pass, not to fix here (spec §4's own instruction).
--   - Like every trigger-enforced refusal in this lineage, this refusal binds ONLY the granted
--     `:role`'s ordinary INSERT path -- a schema-owner/superuser with DDL privilege can disable a
--     trigger or write directly, the same disclosed bound s26/s28/s29/s30/s37/s38/s39 already name.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s46): schema/kern/role are
-- psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway; scratch CHAIN order matches gates/ledger_reader_allowlist.py's
--   and gates/kind_shape_manifest_gate.py's own extended CHAIN, s44/s46 immediately after s45 per
--   the HEAD-BODY RULE, s47 appended last):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s47val -v kern=s47val_kernel -v role=s47val_rw \
--        -f high_watermark_1.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s27-chain-high-water.sql \
--        -f s28-work-parent-edge.sql -f s29-obligation-item-key-and-typed-close.sql \
--        -f s30-typed-dependency-edges.sql -f s31-supersession-uniform-retraction.sql \
--        -f s32-edge-views-single-home.sql -f s33-composite-discharge.sql \
--        -f s34-computed-grade-refusal.sql -f s35-validation-decomposition.sql \
--        -f s36-decision-grade.sql -f s37-violation-disposition.sql \
--        -f s38-bookkeeping-close.sql -f s39-blocks-start.sql \
--        -f s40-principal-identity-events.sql -f s41-principal-bindings-and-relations.sql \
--        -f s42-row-hash-full-coverage.sql -f s43-typed-verdict-write-boundary.sql \
--        -f s45-standing-lifecycle.sql -f s44-model-identity-attestation.sql \
--        -f s46-credited-views.sql -f s47-claim-on-closed-refusal.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` as the
--   MAINTAINER's own act at that future world's --new-world run (spec §5, explicit builder
--   guidance: NOT wired into LINEAGE_CHAIN by this authoring pass -- birth-chain entry is the
--   maintainer's act, performed delta-by-delta, after the s44/s46 lineage-review finding).
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only -- NOT applied to
--   any live schema by this pass. This file's own scratch witness IS wired into the gates'
--   scratch-only CHAIN extensions (gates/ledger_reader_allowlist.py, gates/kind_shape_manifest_
--   gate.py), the SAME way s44/s46 are wired -- see those files' own CHAIN lists and headers.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE).
-- ============================================================================================
