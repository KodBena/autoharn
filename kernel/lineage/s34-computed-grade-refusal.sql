-- s34 COMPUTED-GRADE REFUSAL (ledger item discharge-grade-refuse-if-supplied, claimed by the
-- HISTORY: safe -- adds one INSERT-time refusal only; no existing row is read, validated, or
-- reinterpreted (a historical writer-supplied grade was already silently overwritten at its
-- own INSERT and is stored as the computed value -- nothing to re-judge).
-- orchestrator; refinement-consult finding, ledger row 1157). This delta is AUTHORED and
-- SCRATCH-WITNESSED only; APPLYING it to any live/existing world is the maintainer's act at a
-- FUTURE world's birth (runs-are-strictly-linear ruling, 2026-07-11), never taken here. An
-- ADDITIVE delta applied ON TOP of the s15..s33 kernel (the established remediation-delta idiom),
-- NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of
-- `validate_independence()` (ADR-0012 P1: one home per mechanism -- the SAME function s17 defined,
-- s21 extended for session-aware distinctness, and s29 extended again to compute discharge_grade).
--
-- PREREQUISITE: this delta REQUIRES s29 (kernel/lineage/s29-obligation-item-key-and-typed-close.sql)
-- applied first -- it re-issues `validate_independence()` in the exact shape s29 left it (the
-- discharge_grade column and its computation), and refuses loudly at CREATE OR REPLACE FUNCTION
-- time on a pre-s29 kernel (NEW.discharge_grade would not resolve as a column), the correct,
-- disclosed failure mode for a hard dependency, matching s28/s29/s30/s31/s32/s33's own precedent.
--
-- WHY (operator-side prose; NOT subject-visible -- only the catalog objects inside the opaque db
-- are): ledger finding 1157 (Idris refinement consult, verified by reading s29's own live SQL):
-- `review_detail.discharge_grade` is documented as "COMPUTED at write time... NEVER
-- writer-asserted" (s29's own COMMENT ON COLUMN), but nothing in the schema actually REFUSES a
-- writer-supplied value -- `review_detail` has carried `GRANT INSERT` for `:role` since s15, the
-- column has been ordinarily writable since s29 added it, and `validate_independence()`
-- unconditionally OVERWRITES `NEW.discharge_grade` with its own computation (s29's own trigger
-- body, lines assigning `NEW.discharge_grade := ...` in every branch, no prior read of what the
-- writer supplied). A writer who asserts a grade today gets no error and no warning -- the
-- assertion silently vanishes, replaced by the kernel's own computation, with nothing on the
-- record to show the coercion happened. This is a SILENT-COERCION defect precisely where this
-- lineage's OWN idiom is loud refusal everywhere else it can detect a writer overstepping a
-- computed/kernel-owned fact (the independence-claim gate two branches up in this SAME function;
-- the append-only triggers; every `validate_*` REFUSE-and-teach in s15/s17/s19/s21/s22/s28/s29/
-- s30/s31/s33). The fix restores that idiom here: refuse the INSERT rather than silently discard
-- the writer's value.
--
-- PRINCIPLE (the whole delta in one line): `validate_independence()` gains ONE refusal -- a
-- non-NULL writer-supplied `discharge_grade` on `review_detail` INSERT is REFUSED, with
-- teach-text naming the WHY (the field is a kernel-computed fact about invocation separation,
-- never an assertable claim, and the refusal exists because the pre-s34 kernel silently
-- discarded a supplied value instead of erroring). This mints NO new column, NO new table, NO new
-- vocabulary member -- every pre-existing branch of `validate_independence()` (the independence-
-- claim distinctness gate, the discharge_grade COMPUTATION itself) is re-issued BYTE-IDENTICAL;
-- the one new branch is a REFUSAL, checked first, before any of the pre-existing logic runs.
--
-- ELEMENT 1 -- validate_independence() EXTENDED A FOURTH TIME (s17-defined, s21 extended for
-- session-aware distinctness, s29 extended to compute discharge_grade; CREATE OR REPLACE, the
-- SAME function, ADR-0012 P1). The ONLY change from s29's version: one new IF block, placed FIRST
-- in the function body (before the independence-claim distinctness gate and before the
-- discharge_grade computation), that RAISEs when `NEW.discharge_grade IS NOT NULL` on entry --
-- i.e. the writer supplied a value on INSERT. Every other line -- the independence-claim
-- distinctness gate (unstamped/unverified refusal, same-invocation refusal), and the
-- discharge_grade COMPUTATION itself (same-principal / same-session / distinct-session, the
-- fail-safe NULL-half default) -- is UNCHANGED, byte-for-byte, from s29's version: the computed-
-- default path this delta must not disturb is untouched code, not re-derived logic.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--   - INVARIANT: `review_detail.discharge_grade` is NEVER writer-asserted on INSERT -- a non-NULL
--     value supplied by the writer is REFUSED at the write boundary (construction-time, ADR-0002's
--     strongest rung), never silently accepted, never silently overwritten. The ONLY way a row's
--     `discharge_grade` becomes non-NULL is the trigger's own computation, which runs unconditionally
--     on every INSERT that passes the refusal (i.e. every INSERT where the writer left the column
--     unset/NULL) and is unchanged by this delta.
--
--   - QUANTIFICATION UNIVERSE -- enumerated by grep over the whole tree (kernel/lineage/,
--     bootstrap/templates/, instruments/, engine/) for every WRITER of `review_detail`, per the
--     ADR-0000 2026-07-02 amendment's "check the universe outward":
--       * `bootstrap/templates/led.tmpl`'s `led review` command (the ONE CLI writer) -- its own
--         `INSERT INTO ... review_detail (ledger_id, verdict, independence, basis, antecedent)`
--         column list NEVER names `discharge_grade` (verified by reading the live template) --
--         this delta's refusal can NEVER fire against the CLI path; it defends the column against
--         a writer with direct table access only (the s15 GRANT's own honest bound, named not
--         hidden -- see LIMITS).
--       * Any OTHER direct-SQL writer against `review_detail` (a script, a fixture, a future
--         instrument) -- this is exactly the class the finding names: `GRANT INSERT` has stood
--         since s15, so any such writer COULD supply `discharge_grade` today with no error. This
--         delta forecloses the class at the one choke point every writer -- CLI or direct -- passes
--         through: the BEFORE INSERT trigger itself, not a per-caller convention.
--       * `kernel/fixtures/*.py` / `seen-red/*/run_fixtures.py` writers of `review_detail` --
--         re-verified (grep) to never supply `discharge_grade` themselves; none require a change.
--     No second writer surface exists that could bypass the trigger (review_detail carries no
--     other INSERT-capable trigger and no default-value mechanism that races the BEFORE trigger).
--
--   - DENOMINATION: the refusal is keyed on the SAME column the computation already owns
--     (`discharge_grade`), checked via Postgres's own `IS NOT NULL` -- never a proxy (a separate
--     "was this supplied" sentinel, a second column, a session variable). `IS NOT NULL` is the
--     correct and only denomination here because the column's fail-safe NULL-at-rest default (s29)
--     makes "writer supplied a value" and "column is non-NULL on entry" the SAME fact -- there is
--     no representable state where a writer sets the column to a value that happens to look
--     unset.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION "class-ratified fail-safe deltas" ruling,
-- 2026-07-09): this delta ADDS exactly one refusal and relaxes nothing -- every review INSERT that
-- was legal before this delta (i.e. every INSERT that left `discharge_grade` NULL, which is the
-- ENTIRE set the CLI can produce and the entire set every existing fixture/instrument produces)
-- remains legal, byte-identically, after it; the ONLY newly-refused shape is one that was already
-- a silently-broken assertion (a writer-supplied grade that used to vanish without error). Nothing
-- existing is loosened, no existing semantics changes, no `law/` file is touched. Class-ratified
-- once scratch-witnessed both polarities (red: writer-supplied grade REFUSED with teach-text;
-- green: normal review INSERT computes the grade exactly as before, verified by before/after
-- equality of the computed grade on identical inputs across an s33-only world and an s33+s34
-- world) with the SQL/ASP differential in AGREE on both layers -- see
-- seen-red/s34-computed-grade-refusal/run_fixtures.py for the live witness this classification
-- rests on.
--
-- LIMITS (pre-registered, matching s22/s26/s28/s29/s30/s31/s32/s33's own disclosure convention):
--   - Like every trigger-enforced refusal in this lineage, this refusal binds ONLY the granted
--     `:role`'s ordinary INSERT path -- a schema-owner/superuser with DDL privilege can disable
--     the trigger or write directly, the same disclosed bound s26/s28/s29/s30/s31/s33 already name.
--   - The CLI (`led review`) can never trigger this refusal (it never supplies the column) -- this
--     delta's live-fire surface is a direct-SQL writer against `review_detail`, named above under
--     QUANTIFICATION UNIVERSE, not a gap silently left.
--   - `distinct-deployment` remains closed vocabulary but UNREACHABLE from the computation (s29's
--     own LIMIT, unchanged, re-stated not re-litigated here): this delta touches only the REFUSAL
--     path, never the reachability of any computed value.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s22/s28/s29/s30/s31/s32/s33):
-- schema/kern are psql variables so this delta is VALIDATED on a throwaway substrate before any
-- real apply.
--   VALIDATE (reachable throwaway):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s34val -v kern=s34val_kernel -v role=s34val_rw \
--        -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--        -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--        -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--        -f s23-per-invocation-stamp-token.sql -f s24-declared-event-time.sql \
--        -f s25-commission-kind.sql -f s26-row-hash-chain.sql -f s28-work-parent-edge.sql \
--        -f s29-obligation-item-key-and-typed-close.sql -f s30-typed-dependency-edges.sql \
--        -f s31-supersession-uniform-retraction.sql -f s32-edge-views-single-home.sql \
--        -f s33-composite-discharge.sql -f s34-computed-grade-refusal.sql
--     (provision a genesis seed per s26's own block before the first ledger INSERT, or that
--     trigger refuses loudly -- this delta adds no genesis requirement of its own.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer ruling
--   2026-07-11, "runs are strictly linear"). This delta reaches reality by entering a FUTURE
--   world's birth chain, wired by the orchestrator's own seam-integration pass. NOT wired into
--   `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` by this commission's own instruction ("Do NOT wire
--   LINEAGE_CHAIN"). Authored and scratch-witnessed on scratch schema pairs in the TOY db only --
--   NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE + DROP/CREATE TRIGGER).

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif

-- ============================================================================================
-- ELEMENT 1 -- validate_independence(): ONE new refusal, checked FIRST. Every other line is
-- byte-identical to s29's version (kernel/lineage/s29-obligation-item-key-and-typed-close.sql).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_independence() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE
  rev_session text; rev_agent text; rev_verified boolean; regards_id bigint;
  tgt_session text; tgt_agent text;
  distinct_pair boolean;
BEGIN
  -- s34: discharge_grade is a KERNEL-COMPUTED fact, never a writer assertion (s29's own COMMENT
  -- ON COLUMN). Pre-s34, a writer-supplied value was silently OVERWRITTEN by the computation below
  -- with no error (ledger finding 1157) -- refuse it instead, loudly, before any other branch runs.
  IF NEW.discharge_grade IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: review_detail.discharge_grade is COMPUTED by the kernel from this review''s own independence facts (the (stamp_session,stamp_agent) pair comparison between this review and the row it regards) -- it is never writer-asserted (kernel/lineage/s29-obligation-item-key-and-typed-close.sql''s own COMMENT ON COLUMN). A supplied value (%) is refused here, not silently accepted: prior to this delta (kernel/lineage/s34-computed-grade-refusal.sql), a writer-supplied grade was silently OVERWRITTEN by the computed value with no error, so a caller who believed their asserted grade was honored had no way to discover it was discarded (ledger finding 1157). Omit discharge_grade on INSERT (leave it NULL/unset) -- this trigger computes and sets it for you.', NEW.discharge_grade;
  END IF;

  SELECT stamp_session, stamp_agent, stamp_verified, regards
    INTO rev_session, rev_agent, rev_verified, regards_id FROM ledger WHERE id = NEW.ledger_id;
  SELECT stamp_session, stamp_agent INTO tgt_session, tgt_agent FROM ledger WHERE id = regards_id;

  IF NEW.independence IN ('technical','managerial','financial') THEN
    IF NOT COALESCE(rev_verified, false) THEN
      RAISE EXCEPTION 'Ledger policy: a review claiming independence (%) must carry a VERIFIED interception stamp — an unstamped review cannot establish it was a distinct invocation. Record independence=''self-review'' if you reviewed your own work, or write the review through a genuinely distinct stamped invocation (a separate agent).', NEW.independence;
    END IF;
    -- identity is the PAIR; a NULL half (on either row) is NEVER distinct — fail-safe, never fail-open.
    distinct_pair := (rev_session IS NOT NULL AND rev_agent IS NOT NULL
                       AND tgt_session IS NOT NULL AND tgt_agent IS NOT NULL)
                      AND (rev_session IS DISTINCT FROM tgt_session
                           OR rev_agent IS DISTINCT FROM tgt_agent);
    IF NOT distinct_pair THEN
      RAISE EXCEPTION 'Ledger policy: this review claims independence (%) but the SAME invocation (session=%, agent=%) wrote both it and the row it regards — one context cannot countersign its own work as independent (finding 31 / s21 session-aware distinctness). Record independence=''self-review'' if you reviewed your own work, or have a genuinely distinct invocation (a different session, or a different agent within this session) write the review.', NEW.independence, rev_session, rev_agent;
    END IF;
  END IF;

  -- Element C (s29): independence GRADE, computed for EVERY discharge act (not only an
  -- independence-CLAIMING one), closed vocabulary, fail-safe same-principal default. UNCHANGED
  -- from s29's version -- s34 only guards entry to this block via the refusal above.
  IF rev_session IS NULL OR rev_agent IS NULL OR tgt_session IS NULL OR tgt_agent IS NULL THEN
    NEW.discharge_grade := 'same-principal';
  ELSIF rev_session IS NOT DISTINCT FROM tgt_session AND rev_agent IS NOT DISTINCT FROM tgt_agent THEN
    NEW.discharge_grade := 'same-principal';
  ELSIF rev_session IS NOT DISTINCT FROM tgt_session THEN
    NEW.discharge_grade := 'same-session';
  ELSE
    -- 'distinct-deployment' is closed vocabulary but UNREACHABLE here today -- see s29's header LIMITS.
    NEW.discharge_grade := 'distinct-session';
  END IF;

  RETURN NEW;
END; $fn$;
-- this trigger's home table is review_detail (s17), unchanged here.
DROP TRIGGER IF EXISTS validate_independence ON :"schema".review_detail;
CREATE TRIGGER validate_independence BEFORE INSERT ON :"schema".review_detail
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_independence();
