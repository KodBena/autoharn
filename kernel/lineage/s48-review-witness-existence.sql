-- s48 REVIEW-WITNESS ROW EXISTENCE (design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md Delta 1, ledger row
-- 1600, RATIFIED BUILD BASIS commit 58f1533, maintainer-prioritized 2026-07-18 ("Block F must be
-- independent, you should see to it right away ... a priority item not only to spec but to
-- implement"; Fable-authored). CLASS-RATIFIED FAIL-SAFE (CLAUDE.md ORCHESTRATION, 2026-07-09
-- ruling): this delta ONLY ADDS a refusal -- nothing existing is relaxed, no existing refusal
-- loosened, no existing edge/kind/column semantics changed. Sonnet-executed per the standing
-- delegation contract, from this ratified spec.
--
-- ADR-0000 2(a), the two questions this delta answers: (a) the TYPE that forecloses "a
-- review-witness citation naming a nonexistent row" is a construction-time existence check on the
-- review-witness field ITSELF, scoped to the two close-family kinds that carry it (work_closed,
-- work_violation_disposition) -- the ONE field the whole ledger treats as load-bearing evidence
-- (s29 Element B: "review already on record, cited by work_review_ref" -- the field's own
-- COMMENT ON COLUMN text), never a general refs-integrity mechanism (WK1-c below is the named
-- boundary: prose `refs` citations of future/foreign rows stay legal, by design, everywhere
-- else); (b) the operational lapse (ADR-0000 Rule 2(b), self-directed) is that s29/s37, when they
-- MINTED work_review_ref as a mandatory-when-witnessed field, never asked whether the cited value
-- was itself checkable -- the column was typed as free text (row id, commit hash, or artifact
-- path, s29's own COMMENT) precisely because a checkable existence constraint was never built for
-- any of its three forms; this delta builds the checkable form for exactly the one sub-shape that
-- IS checkable inside this database (a `row:<id>` token naming a ledger row), the same
-- "unrepresentable, not merely discouraged" standard s29 Element B already set for the
-- review-silent-close class one column over.
--
-- WHY (the defect, witnessed 2026-07-18): `led work close` accepted `--review-witness row:1594`
-- when no row 1594 existed -- the orchestrator guessed its own decision row's id (a row that had
-- not yet been assigned, because ledger `id` is server-assigned at INSERT time, s15). A witness
-- citation naming a nonexistent row is a claim with a dangling evidence pointer, in the one place
-- evidence pointers are load-bearing: the "witnessed" review-disposition constructor (s29 Element
-- B) exists specifically so a review-silent close is unrepresentable, and a citation that resolves
-- to nothing quietly reintroduces exactly that class one indirection later -- a dangling pointer
-- masquerading as a discharged obligation.
--
-- MECHANISM (spec's own text, verbatim scoping): a NEW, standalone BEFORE INSERT trigger,
-- validate_review_witness_existence -- the s43 validate_supersession_target idiom (a single-
-- purpose write-boundary trigger added beside the existing validate_* family, ADR-0012 P1: a
-- THIRD sibling of that shape, never folded into validate_work_item's dispatcher, because this
-- check is orthogonal to every one of that dispatcher's leaf concerns -- open/depends/close/
-- disposition -- and shares no state with any of them; a fourth call site added to a dispatcher
-- built for work-item lifecycle leaves would be the second, competing factoring ADR-0012 P1
-- warns against, not a reuse of it). Scope, deliberately narrow (spec's own words): ONLY
-- kind IN ('work_closed', 'work_violation_disposition') (the close-family kinds that carry
-- work_review_ref at all -- s29/s37's own kind-shape CHECK, work_review_ref_kind_shape, already
-- forecloses every other kind from carrying a non-NULL value there, so this IF is a documented
-- restatement of an existing invariant, not a new one), and ONLY the review-witness field itself
-- (work_review_ref) -- NEVER the generic `refs` column, where prose citation of future/foreign
-- rows stays legal everywhere (WK1-c, the scope-boundary witness). Tokens matching `row:<digits>`
-- inside work_review_ref (led's own existing bare-reference citation form, per
-- bootstrap/templates/led.tmpl's "row:<id> ... a bare reference uses refs" comment -- the SAME
-- vocabulary this delta now makes checkable, one field over) are extracted and each cited id is
-- checked for existence in `ledger` (raw table, not `ledger_current` -- EXISTENCE is the question,
-- not in-force status: a citation of a row that was later superseded still names a real,
-- once-written review event, and this delta does not relitigate s31's supersession semantics one
-- field over). A missing id refuses with a teaching message naming the missing id, the kinds
-- checked, and the corrective form (cite an existing row, or use --review-deferred/
-- --review-bookkeeping if none exists yet) -- and, when the cited id is AT OR BEYOND the ledger's
-- current head (the exact shape of the witnessed defect: guessing the id one's OWN not-yet-
-- inserted row will receive), the message says so explicitly: self-reference is impossible by
-- construction, because `id` is a server-assigned SERIAL (s15) never visible to the inserting
-- statement itself.
--
-- HISTORY: safe -- ONE new object (a standalone BEFORE INSERT trigger function), ADDED beside the
-- existing validate_* family, calling nothing and touching no pre-existing function/view/column.
-- No table, column, kind, or CHECK constraint of any kind is added or altered. The new trigger
-- reads ONLY the raw `ledger` table (id existence, row-addressed, not a truth projection -- the
-- SAME history-typed posture validate_review/validate_supersession_target already hold, per
-- gates/ledger_reader_allowlist.py's own declared vocabulary for a write-boundary trigger:
-- "cannot read a view excluding the inserting row"). No pre-existing row's legality changes: a
-- row whose review-witness citation was already valid stays valid; a row that would have been
-- accepted before this delta with a DANGLING citation is now refused, which is this delta's own
-- point, not a regression -- and no PRE-s48 world's data is retroactively judged (this delta
-- governs INSERTs from its own application forward only, the standing trigger-refusal posture
-- every prior delta in this lineage shares).
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment; spec's own Delta 1 section):
--
--   - INVARIANT: a work_closed or work_violation_disposition row whose work_review_ref carries
--     one or more `row:<id>` tokens is admitted iff every cited id names a row that already
--     exists in `ledger` at INSERT time -- a review-witness citation with a dangling evidence
--     pointer is unrepresentable, not merely discouraged.
--
--   - QUANTIFICATION UNIVERSE (enumerated OUTWARD, ADR-0000's 2026-07-02 amendment text):
--       TABLES reachable off :"schema"/:"kern": unchanged -- no new base table, no new column.
--         The check rides the EXISTING work_review_ref column (s29) and the EXISTING ledger `id`
--         column (s15), nothing new to enumerate.
--       EVERY KIND THAT CARRIES work_review_ref: unchanged -- exactly the two kinds s29/s37
--         already license (work_closed, work_violation_disposition); this delta narrows WHICH OF
--         THOSE ROWS are admitted, it does not widen which kinds may carry the column.
--       VIEWS re-read for the wildcard/column-complete class (s20/s22/.../s43 all named):
--         ledger_current / countersigned_in_force -- unchanged, this delta adds no column and
--         reads neither view at all (the check reads raw `ledger` by the mechanism's own design,
--         above) -- re-verified NOT members needing re-issue. work_item_current -- unchanged,
--         re-verified NOT a member: this delta touches no work-item-state derivation, only the
--         review-witness citation's own referential integrity.
--       KIND VOCABULARY -- unchanged. No new `kind` value.
--       SCOPE BOUNDARY, named (not a silent narrowing): `refs` (the GENERIC citation column,
--         used by decision/finding/verification/etc. rows to cite antecedent or even
--         not-yet-written rows -- led.tmpl's own documented convention, "a verification result
--         citing its pre-registered criteria") is DELIBERATELY NOT checked by this delta -- prose
--         citation of a future/foreign row stays legal everywhere it always was (WK1-c). Only the
--         review-witness POSITION (work_review_ref, on the two close-family kinds) is load-bearing
--         evidence in the sense this delta forecloses; a generic `refs` citation is commentary,
--         not a discharge claim.
--       GRANTS -- unchanged. The new trigger function needs no explicit GRANT (a trigger function
--         fires under the table owner's/trigger's own execution context, the s19/s43 discipline;
--         it holds SELECT on `ledger` implicitly the same way every sibling write-boundary trigger
--         does).
--       ENGINE -- VERIFIED, not merely asserted (per this codebase's own standing instruction to
--         check engine/lp/ and engine/ledger_*.py for every writer-side widening): this delta adds
--         NO new predicate, NO new fact emission, and touches NEITHER engine/ledger_edb.py NOR any
--         engine/lp/*.lp file NOR engine/ledger_floor.py at all -- it is a PURE construction-time
--         refusal (a row that fails this check is simply never written; there is no admitted-row
--         shape for the ASP/SQL floor to diverge over -- s30/s39/s47's own "construction-time-only"
--         precedent, re-applied). `./judge`'s existing SQL/ASP differential is UNAFFECTED and
--         continues to AGREE -- witnessed as part of this delta's own scratch acceptance (see
--         seen-red/s48-review-witness-existence/run_fixtures.py).
--
--   - DENOMINATION: unchanged. `row:<id>` stays the existing bare-reference citation vocabulary
--     (led.tmpl's own convention, cited above); "exists" is denominated in ledger `id` membership,
--     the same currency the row's own primary key already is -- never a proxy (e.g. row COUNT, or
--     a cached high-water mark) for the fact that actually matters here.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): CLASS-RATIFIED FAIL-SAFE.
-- This delta ONLY adds ONE refusal (a work_closed/work_violation_disposition INSERT whose
-- work_review_ref cites a nonexistent row:<id> is refused) -- nothing existing is relaxed, no
-- column/kind/CHECK is added or widened, the dispatcher is untouched. Per the standing ruling this
-- qualifies for entry into the birth chain without a per-delta maintainer question, PENDING the
-- scratch-witness-on-both-polarities-with-SQL/ASP-AGREE this delta's own commissioning spec
-- (Delta 1's own "Witnesses" list) requires and this file's own witness pass performs (named here
-- for the record, not claimed as a bypass of that witness).
--
-- LIMITS (pre-registered, matching s22/.../s47's own disclosure convention):
--   - Only the `row:<id>` sub-shape of work_review_ref is checkable inside this database; a
--     commit-hash or artifact-path witness (the column's other two legal forms, s29's own COMMENT)
--     is NOT existence-checked by this delta -- named, not silently absorbed: neither form has a
--     row this database can look up (a commit hash is checked, when checked at all, by
--     s38's own git-existence CLI-side machinery; an artifact path is not checkable from SQL at
--     all). Filed as a named non-goal, not a gap this delta claims to have closed.
--   - `refs` (the generic citation column) is deliberately OUT OF SCOPE everywhere (see the
--     SCOPE BOUNDARY note above) -- exercised as WK1-c in this delta's own fixture.
--   - A citation naming a row that once existed but was later SUPERSEDED still passes this check
--     (existence, not in-force status, by design -- see the MECHANISM note above); relitigating
--     "is this citation still the RIGHT witness" is a different, unbuilt type, not this delta's.
--   - Like every trigger-enforced refusal in this lineage, this refusal binds ONLY the granted
--     `:role`'s ordinary write path -- a schema-owner/superuser with DDL privilege can disable a
--     trigger or write directly, the same disclosed bound s26/s28/.../s47 already name.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s47): schema/kern/role are
-- psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway; scratch CHAIN order matches gates/ledger_reader_allowlist.py's
--   and gates/kind_shape_manifest_gate.py's own extended CHAIN, s48 appended immediately after
--   s47 per the HEAD-BODY RULE s44/s46/s47 already established):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s48val -v kern=s48val_kernel -v role=s48val_rw \
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
--        -f s46-credited-views.sql -f s47-claim-on-closed-refusal.sql \
--        -f s48-review-witness-existence.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` as the
--   MAINTAINER's own act at that future world's --new-world run (s47's own precedent, this same
--   spec's own Status block, explicit builder guidance: NOT wired into LINEAGE_CHAIN by this
--   authoring pass -- birth-chain entry is the maintainer's act).
--   Authored and scratch-witnessed on scratch schema pairs in the TOY db only -- NOT applied to
--   any live schema by this pass. This file's own scratch witness IS wired into the gates'
--   scratch-only CHAIN extensions (gates/ledger_reader_allowlist.py, gates/kind_shape_manifest_
--   gate.py), the SAME way s44/s46/s47 are wired -- see those files' own CHAIN lists and headers.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION; DROP+CREATE TRIGGER).
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
-- ELEMENT 1 -- validate_review_witness_existence: a NEW, standalone BEFORE INSERT trigger (the
-- s43 validate_supersession_target idiom -- a single-purpose write-boundary trigger added beside
-- the existing validate_* family, never folded into validate_work_item's dispatcher, ADR-0012 P1
-- -- this check shares no state with any of that dispatcher's lifecycle leaves).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_review_witness_existence() RETURNS trigger
    LANGUAGE plpgsql SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_match text;
  v_id bigint;
  v_head bigint;
BEGIN
  -- Scope, deliberately narrow (spec Delta 1, verbatim): ONLY the two close-family kinds that
  -- carry work_review_ref at all (work_review_ref_kind_shape, s29/s37, already forecloses every
  -- other kind from a non-NULL value here -- this IF restates an existing invariant, it does not
  -- mint a new one), and ONLY the review-witness field itself -- never the generic `refs` column
  -- (WK1-c: prose citation of future/foreign rows stays legal everywhere else).
  IF NEW.kind IN ('work_closed', 'work_violation_disposition')
     AND NEW.work_review_ref IS NOT NULL THEN
    FOR v_match IN
      SELECT (regexp_matches(NEW.work_review_ref, 'row:([0-9]+)', 'g'))[1]
    LOOP
      v_id := v_match::bigint;
      IF NOT EXISTS (SELECT 1 FROM ledger WHERE id = v_id) THEN
        SELECT max(id) INTO v_head FROM ledger;
        RAISE EXCEPTION 'Ledger policy: review-witness citation ''row:%'' in work_review_ref is refused — no ledger row % exists (checked at INSERT time; review-witness position only, close-family kinds work_closed/work_violation_disposition -- s48). A witness citation naming a nonexistent row is a claim with a dangling evidence pointer, in the one place evidence pointers are load-bearing.%  Cite an EXISTING row instead (e.g. --review-witness row:<id> naming an already-recorded review event), or use --review-deferred/--review-bookkeeping if no review exists yet.',
          v_id, v_id,
          CASE WHEN v_head IS NOT NULL AND v_id > v_head
               THEN ' This id is AT OR BEYOND the ledger''s current head — if you meant to cite THIS row''s own id, that is impossible by construction: ledger `id` is server-assigned (s15) and is never visible to the row being inserted.'
               ELSE '' END;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_review_witness_existence ON :"schema".ledger;
CREATE TRIGGER validate_review_witness_existence BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_review_witness_existence();

COMMENT ON FUNCTION :"schema".validate_review_witness_existence() IS
  'kernel/lineage/s48-review-witness-existence.sql: a work_closed/work_violation_disposition row
   whose work_review_ref cites one or more row:<id> tokens is refused unless every cited id
   already exists in ledger at INSERT time (raw ledger, existence not in-force status). Scoped to
   the review-witness position on the two close-family kinds only -- prose `refs` citations of
   future/foreign rows stay legal everywhere else (design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md
   Delta 1, ledger row 1600).';
-- ============================================================================================
