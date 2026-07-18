-- s49 JOURNALER ATTEMPTED-IDENTITY OVERFLOW GUARD (design/FABLE-KERNEL-INTAKE-PAIR-SPEC.md
-- Delta 2, ledger row 1581, RATIFIED BUILD BASIS commit 58f1533, built under the MAINTAINER'S
-- DIRECT INSTRUCTION of 2026-07-18 ("Block F must be independent, you should see to it right
-- away ... a priority item not only to spec but to implement"; Fable-authored). NOT
-- letter-2(a) class-ratified fail-safe (this delta edits an existing function body via
-- CREATE OR REPLACE, kernel.journal_write_refusal) -- its ratification is the maintainer's
-- instruction itself, read plainly per the 2026-07-11 vocabulary note ("'ratified' in this
-- project's record has mostly meant 'instructed by the operator and therefore implemented'").
-- Effect is strictly fail-safe: MORE refusals get recorded (the exact ones that previously
-- destroyed themselves on the way in), nothing is newly permitted. Sonnet-executed per the
-- standing delegation contract.
--
-- ADR-0000 2(a): (a) the TYPE that forecloses "the refusal recorder itself can be defeated by
-- the shape of input it exists to record" is TOTALITY on the one partial step inside the
-- journaler's attempted-identity resolution -- an unguarded cast is a partial function
-- (undefined, i.e. it raises, on out-of-range input) masquerading as a total one; this delta
-- makes that ONE step total, so it returns a value (including the "neither resolves" NULL the
-- function already had a name for) for every input the regex admits, not just the range a
-- bigint happens to hold. (b) the operational lapse (ADR-0000 Rule 2(b), self-directed): s43's
-- own Element 4 built the attempted-identity resolution to accept "any digit string" via
-- `~ '^[0-9]+$'` but cast it straight to bigint without ever asking whether every digit string
-- the regex admits is a legal bigint -- the regex's own domain (arbitrary-length numerals) is
-- strictly wider than bigint's range (max 19 digits, and not every 19-digit numeral fits
-- either), and nobody asked the second question when the first one shipped.
--
-- WHY (the defect, witnessed 2026-07-18, ledger row 1581): kernel.journal_write_refusal
-- resolves the attempted identity by regex `^[0-9]+$` then an unguarded
-- `(p_payload->>'actor')::bigint` cast (s43 line ~730). An over-bigint digit string -- which is
-- EXACTLY the kind of payload that ARRIVES at the journaler, since it arrives already refused,
-- i.e. already known-bad -- makes the cast raise 22003 (numeric_value_out_of_range) INSIDE the
-- journaler itself. Because journal_write_refusal is called from inside the four boundary
-- functions' own guarded BEGIN..EXCEPTION block (s43 Element 3), and journal_write_refusal has
-- no guard of its OWN around this one cast, the 22003 propagates out of the journaler and is
-- caught by the CALLER's outer handler -- but that handler's own recovery path is "journal the
-- refusal", which is the very call that just failed, so the second attempt fails identically
-- and the exception ultimately escapes the boundary function as an unhandled abort: the
-- refusal recording itself aborts, the write_refused row is never written, and only the
-- oracle's refusal_seq gap remains (s43 Element 5's own reconciliation, EXPLAIN-grade not
-- FAIL-grade for THIS specific cause -- named there as "journal double failure" without this
-- delta's own root-cause detail). The recording path fails on precisely the inputs it exists
-- to record -- the refute-architecture flaw-1 class (s43's own header, "a refusal whose only
-- witness is destroyed by the refusal's own mechanism") recurring one level down, inside the
-- very mechanism s43 built to close it.
--
-- MECHANISM (spec's own text; builder's guard choice, stated and reasoned as instructed): the
-- attempted-identity resolution becomes TOTAL via a LOCAL EXCEPTION HANDLER scoped to the one
-- cast, not a pre-check on the digit string's length/value. REASON: a length/magnitude
-- pre-check would have to duplicate bigint's own range boundary in SQL text (a second,
-- hand-maintained copy of a fact Postgres's own numeric-input parser already knows precisely
-- and exactly -- ADR-0012 P1's "one home per mechanism," applied to a RANGE fact this time, not
-- a query) and get it subtly wrong at the edges the way the very first draft of this file's own
-- reason for existing got the SAME class of "did we check whether the input actually fits"
-- wrong one level up; a plpgsql BEGIN..EXCEPTION WHEN numeric_value_out_of_range block, by
-- contrast, asks Postgres's own cast machinery the true answer and reacts to it, adding four
-- lines local to the ONE step that can fail, touching nothing else in the function, and
-- catching exactly the ONE named condition this defect is (SQLSTATE 22003) -- never a bare
-- `WHEN OTHERS`, which would silently swallow an unrelated defect in this same resolution step
-- were one ever introduced later (a `WHEN OTHERS` here would be the fail-open failure mode
-- ADR-0000's own foreclosure standard exists to rule out, not the fail-safe one this guard is
-- for). On catching it, v_attempted is set to NULL -- the SAME value the function already uses
-- for "neither resolves" (the pre-existing fallback three lines below), so an unresolvable
-- attempted-actor cast is not a NEW terminal state, it is the EXISTING one, reached by one more
-- path. No other line of the function changes: the oracle bump stays first (Element 5's
-- non-transactional counter, unmoved), the write-boundary principal lookup and its own loud
-- abort on an unregistered world stay exactly as s43 left them, and the loud-abort semantics
-- for a genuinely failing INSERT (the journal INSERT itself, further down) are untouched --
-- this delta's ONE change is scoped to the attempted-identity resolution's one partial cast,
-- nothing downstream of it.
--
-- HISTORY: NOT additive-safe by s43's own per-mechanism grounds (CREATE OR REPLACE on an
-- existing function body -- named plainly in the FAIL-SAFE CLASSIFICATION section below,
-- exactly per this codebase's own honesty convention for a non-2(a) delta), but BEHAVIOR-SAFE
-- on every pre-existing path: for every payload actor value the pre-s49 function already
-- resolved successfully (any digit string that fits in bigint, matched or not against a
-- registered principal), this delta's re-issued function does EXACTLY what s43's did -- the
-- new BEGIN..EXCEPTION block changes NOTHING about the SELECT's own result on a value that
-- does not raise. Only the previously-fatal path (a digit string too large for bigint) changes
-- behavior, and it changes from "the journaler itself aborts, destroying the refusal record it
-- exists to create" to "the journaler records the refusal with attempted_actor NULL" -- MORE
-- refusals get recorded, in the strict subset/superset sense s43's own header already uses for
-- its "REVOKEs are pure narrowing" argument, applied here to "journaled outcomes are pure
-- widening" instead.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment; spec's own Delta 2 section):
--
--   - INVARIANT: kernel.journal_write_refusal's attempted-identity resolution is now TOTAL --
--     for every payload the regex `^[0-9]+$` admits, the resolution either yields a registered
--     principal id or NULL (the pre-existing "neither resolves" value); it never raises. A
--     refusal whose payload carries an over-bigint attempted-actor digit string is no longer a
--     refusal the recording mechanism itself cannot survive.
--
--   - QUANTIFICATION UNIVERSE (enumerated OUTWARD, ADR-0000's 2026-07-02 amendment text --
--     re-read against every caller/consumer of the one function this delta touches, not merely
--     the payload shape the defect was FOUND on):
--       CALL SITES: all four s43 boundary functions (ledger_write, review_write,
--         registration_write, obligation_write) call journal_write_refusal identically --
--         none passes a differently-shaped payload to the `actor` resolution, so this ONE
--         re-issue covers every call site with no per-caller change needed (the SAME argument
--         s43's own header makes for why journal_write_refusal is "the ONE home" -- re-verified,
--         not merely assumed, by this delta's own WK2-a/b legs running the guard through
--         kernel.ledger_write specifically, the payload path that produced the witnessed
--         defect).
--       PAYLOAD SHAPES reaching the guarded cast: the regex `^[0-9]+$` (unchanged by this
--         delta) admits arbitrary-length all-digit strings; bigint's own range
--         (-9223372036854775808..9223372036854775807) is the ONLY axis this delta forecloses --
--         a non-digit `actor` value was ALREADY excluded from reaching the cast by the regex
--         (unchanged, out of this delta's scope by construction) and a MISSING `actor` key was
--         already handled by the pre-existing `(p_payload ? 'actor')` guard one line up
--         (unchanged). This delta's own axis is exactly and only "digit string too large for
--         bigint," named because it is the one axis the pre-existing code left partial.
--       TABLES/COLUMNS/KINDS/VIEWS/GRANTS: unchanged -- this delta adds no column, no kind, no
--         view, no grant; it re-issues ONE existing :kern-schema function body with a four-line
--         local guard added around one pre-existing statement.
--       ENGINE: unaffected -- this delta touches no engine/ledger_edb.py, engine/lp/*.lp, or
--         engine/ledger_floor.py path; a write_refused row's shape and downstream ASP/SQL
--         readability are identical whether refusal_attempted_actor resolved via the
--         unguarded pre-s49 cast or the guarded s49 one (both write NULL on non-resolution --
--         this delta only widens WHICH inputs reach that same NULL rather than aborting first).
--         `./judge`'s differential is UNAFFECTED and continues to AGREE -- witnessed as part of
--         this delta's own scratch acceptance (seen-red/s49-journaler-overflow-guard/
--         run_fixtures.py).
--       GATES: gates/ledger_reader_allowlist.py -- unaffected, journal_write_refusal lives in
--         :"kern", outside that gate's declared :"schema" universe, exactly the same standing
--         scope note s43's own header already gives for this same function (no entry needed,
--         re-verified not silently assumed). gates/kind_shape_manifest_gate.py -- unaffected,
--         zero new columns/kinds. gates/hash_coverage_gate.py -- unaffected, compute_row_hash is
--         not touched by this delta (a write_refused row's column SET is identical to s43's;
--         only how ONE of those columns' VALUES gets computed, not which columns exist, changes).
--
--   - DENOMINATION: unchanged. The attempted-identity fact stays denominated in
--     `kernel.principal.id` (a registered principal, or NULL for "unattributable") -- this
--     delta widens WHICH inputs resolve to NULL, it mints no new value and no new column to
--     carry one.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (s43's own precedent for this same honesty requirement): this delta
-- re-issues an EXISTING function body via CREATE OR REPLACE (kernel.journal_write_refusal),
-- which is not a letter-2(a) "only adds a refusal" shape even though its EFFECT is strictly
-- fail-safe (more refusals recorded, nothing newly permitted, no existing behavior narrowed on
-- any input that did not previously raise). It ships under the MAINTAINER'S DIRECT
-- INSTRUCTION of 2026-07-18 (quoted in this file's own Status line above), the ratification
-- read plainly per the 2026-07-11 vocabulary note, exactly the posture s43 itself shipped
-- under (rows 1419/1460/1462) for the same reason -- a live function re-issue is not
-- self-certifying under the class-ratified path no matter how narrow the diff.
--
-- LIMITS (pre-registered, matching s43's own disclosure convention, this delta's own slice):
--   - The guard catches SQLSTATE 22003 (numeric_value_out_of_range) specifically, never
--     `WHEN OTHERS` -- a genuinely different defect introduced later in this same resolution
--     step would still raise and still be caught by the OUTER boundary-function handler
--     (journaled as its own write_refused row via the SAME class-based 22/23/P0 journaling
--     s43 Element 4 already performs on the caller side), not silently absorbed here. Named so
--     the guard's own narrowness is legible, not merely asserted.
--   - This delta does not change what happens when the JOURNAL INSERT itself fails (further
--     down in the same function, unmodified) -- that loud-abort/sequence-gap/server-log
--     composition is s43's own named, disclosed limit, untouched here.
--   - Every other named limit in s43's own header (session_user attribution's one-principal-
--     per-login-role assumption, the digest-only payload posture, the superuser/schema-owner
--     bound) is unchanged by this delta and not re-stated in full here -- see
--     kernel/lineage/s43-typed-verdict-write-boundary.sql's own LIMITS section.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s48): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway; appended immediately after s48 per the HEAD-BODY RULE
--   s44/s46/s47/s48 already established):
--      psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--        -v schema=s49val -v kern=s49val_kernel -v role=s49val_rw \
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
--        -f s48-review-witness-existence.sql -f s49-journaler-overflow-guard.sql
--     (genesis seed per s26; register the write-boundary principal, per s43's own VALIDATE note,
--     before exercising any refusal path, or the journaler aborts loudly by design -- unchanged
--     by this delta.)
--   REAL: NEVER applied to any existing world by this delta's own authoring act (maintainer
--   ruling 2026-07-11, "runs are strictly linear"). Reaches reality by entering a FUTURE world's
--   birth chain, wired into `bootstrap/new-project.sh`'s `LINEAGE_CHAIN` as the MAINTAINER's own
--   act at that future world's --new-world run -- NOT wired into LINEAGE_CHAIN by this
--   authoring pass. Authored and scratch-witnessed on scratch schema pairs in the TOY db only.
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION).
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
-- ELEMENT 1 -- kernel.journal_write_refusal RE-ISSUED: the s43 body, BYTE-IDENTICAL below and
-- above the guarded resolution, with ONE change -- the attempted-identity cast wrapped in a
-- local BEGIN..EXCEPTION WHEN numeric_value_out_of_range block (guard choice: local exception
-- handler over a length/magnitude pre-check; reason in this file's own header MECHANISM
-- section above). v_attempted := NULL on catch -- the SAME value the function already uses for
-- "neither resolves."
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"kern".journal_write_refusal(
    p_surface text, p_payload jsonb, p_sqlstate text, p_message text)
    RETURNS bigint LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE
  v_wb bigint;
  v_attempted bigint;
  v_id bigint;
BEGIN
  -- the oracle bump, BEFORE the journal INSERT (non-transactional, survives everything --
  -- s43 Element 5): if the INSERT below then fails, the sequence shows a counted gap the
  -- verify-chain reconciliation names. UNCHANGED by s49.
  PERFORM nextval('refusal_seq');
  SELECT id INTO v_wb FROM principal WHERE name = 'write-boundary';
  IF v_wb IS NULL THEN
    RAISE EXCEPTION 'write boundary: the ''write-boundary'' tool principal is not registered in this world -- refusal recording has no authoring identity (kernel/lineage/s43-typed-verdict-write-boundary.sql Element 6; bootstrap/new-project.sh''s birth sequence registers it). The original refusal (SQLSTATE %) was: %', p_sqlstate, p_message;
  END IF;
  -- the ATTEMPTED identity: the explicit payload actor when it resolves to a registered id,
  -- else the session's own standing-declaration default (the identity that WOULD have been
  -- attributed); NULL when neither resolves -- the role below is still always known.
  --
  -- s49 GUARD (kernel/lineage/s49-journaler-overflow-guard.sql): the regex `^[0-9]+$` admits
  -- arbitrary-length digit strings, but bigint's own range does not -- an over-bigint numeral
  -- (EXACTLY the shape of payload that reaches this function, since it arrives already
  -- refused) previously raised 22003 HERE, inside the one mechanism that exists to record a
  -- refusal, destroying the very record it was resolving an identity for. The cast is now
  -- total: numeric_value_out_of_range is caught locally and yields v_attempted := NULL -- the
  -- SAME value the fallback below already uses for "neither resolves." No other line of this
  -- function changes.
  IF (p_payload ? 'actor') AND (p_payload->>'actor') ~ '^[0-9]+$' THEN
    BEGIN
      SELECT id INTO v_attempted FROM principal WHERE id = (p_payload->>'actor')::bigint;
    EXCEPTION WHEN numeric_value_out_of_range THEN
      v_attempted := NULL;
    END;
  END IF;
  IF v_attempted IS NULL THEN
    SELECT principal_id INTO v_attempted FROM principal_role WHERE db_role = session_user;
  END IF;
  INSERT INTO ledger (kind, statement, actor,
                      refusal_sqlstate, refusal_message, refusal_surface,
                      refusal_payload_digest, refusal_attempted_actor, refusal_attempted_role)
  VALUES ('write_refused',
          format('write refused at surface %s (SQLSTATE %s)', p_surface, p_sqlstate),
          v_wb,
          p_sqlstate, p_message, p_surface,
          encode(sha256(convert_to(p_payload::text, 'utf8')), 'hex'),
          v_attempted, session_user)
  RETURNING id INTO v_id;
  RETURN v_id;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) FROM PUBLIC;

COMMENT ON FUNCTION :"kern".journal_write_refusal(text, jsonb, text, text) IS
  'The ONE home of "a refusal becomes a committed write_refused row" (s43 Element 4), called
   only from inside the four SECURITY DEFINER boundary functions (no role holds EXECUTE).
   Bumps the refusal_seq oracle FIRST (non-transactional), then journals: actor = the
   write-boundary tool principal; the attempted identity in refusal_attempted_* (s49: the cast
   is now TOTAL -- an over-bigint attempted-actor digit string resolves to NULL instead of
   aborting the journaler itself, kernel/lineage/s49-journaler-overflow-guard.sql); the payload
   as a SHA-256 digest only (R4). If the journal INSERT itself fails the exception propagates --
   a loud abort, a counted sequence gap, the server log as residual coverage (fail-safe on
   both legs, unchanged by s49). kernel/lineage/s43-typed-verdict-write-boundary.sql;
   kernel/lineage/s49-journaler-overflow-guard.sql.';
-- ============================================================================================
