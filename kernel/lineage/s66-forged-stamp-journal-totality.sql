-- s66 FORGED-STAMP JOURNAL TOTALITY (design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md §1,
-- RATIFIED 2026-07-27, ledger row 1519 -- "it's yes of course," verbatim -- basis row 1519's
-- own fixture w36f). First of the s66/s67 journal-totality pair, both s49-family members: the
-- refusal journal must record refusals under hostile conditions, because the refusal path is
-- exactly where hostile input arrives (the s65 lesson, restated once more). Sonnet-built per
-- the standing delegation contract, from the ratified spec.
--
-- PREREQUISITE / THE HEAD-BODY RULE (s45's own standing instruction): at this delta's
-- authoring the lineage head is s65 (kernel/lineage/'s own directory listing, confirmed by the
-- builder before authoring). The one function this delta re-issues, kernel.set_stamp, has its
-- own separate re-issue history: born s17, re-issued ONCE since at s23
-- (kernel/lineage/s23-per-invocation-stamp-token.sql) -- grep-verified across every tracked
-- kernel/lineage/sNN-*.sql file: no delta between s23 and this one re-issues set_stamp. s23 is
-- therefore the TRUE immediately-prior re-issue this delta's base body descends from, matching
-- gates/lineage_reissue_lineage.py's own citation + prior-body-sha256 discipline (MIN_N=43 for
-- citation, MIN_N_HASH=63 for the hash line -- both apply here, s66 > 63).
--
-- DIAGNOSIS, WITNESSED BEFORE BUILDING (spec §1's own instruction: the hypothesis is
-- REPRODUCED first, and the fix is derived from the WITNESSED mechanism, not merely the
-- spec's prose): a scratch full-chain world (s66probe, s15..s65, toy@192.168.122.1) was born
-- via bootstrap/new-project.sh --new-world, and a forged-complete stamp (app.vendor_session/
-- agent/ts all SET, app.vendor_hmac a well-formed-but-wrong 64-hex value) was sent through
-- kernel.ledger_write as the granted role. OBSERVED (build report has the verbatim
-- transcript): the call raises, uncaught, exit 3 -- NOT a typed 'refused' verdict -- and the
-- exception's own CONTEXT trace shows precisely the hypothesized double-fire: set_stamp()'s
-- RAISE (line 26, the forged-but-invalid branch) fires a SECOND time from INSIDE the SQL
-- statement "INSERT INTO ledger (kind, statement, actor, refusal_sqlstate, ...) VALUES
-- ('write_refused', ...)" -- i.e. kernel.journal_write_refusal's OWN journal INSERT -- called
-- from kernel.ledger_write's EXCEPTION WHEN OTHERS block (the "PL/pgSQL function
-- ledger_write(jsonb) line 54 at assignment" frame is the `v_refusal :=
-- journal_write_refusal(...)` call). The forged GUCs (app.vendor_session/agent/ts/hmac) are
-- SESSION-scoped (`current_setting(..., true)`, no `LOCAL`), so they are STILL SET when the
-- journaler's own INSERT fires the SAME set_stamp trigger a second time on the SAME row-to-be
-- (the journal row is itself an INSERT on `ledger`); set_stamp recomputes stamp_valid on the
-- unchanged forged inputs, gets the same FALSE, and raises again -- this time from a call site
-- (journal_write_refusal, itself called from inside ledger_write's own exception handler) that
-- has NO surrounding BEGIN..EXCEPTION of its own, so the second exception propagates all the
-- way out: an unhandled abort, zero write_refused rows committed (verified: `select count(*)
-- from ledger where kind='write_refused'` = 0 after the probe), only kernel.refusal_seq's
-- non-transactional bump (Element 5) as the counted-gap residue s43's own reconciliation
-- already names as "journal double failure." THE HYPOTHESIS IS CONFIRMED, MECHANISM
-- MATCHES EXACTLY: no divergence to report, the fix below proceeds as specced.
--
-- MECHANISM (spec §1, one guard, builder's own restatement against the witnessed trace above):
-- kernel.set_stamp gains ONE new branch, checked ONLY when the forged-complete stamp fails
-- validation: if the row being inserted is itself the journaler's own write_refused row
-- (NEW.kind = 'write_refused'), record stamp_verified := false instead of raising -- the SAME
-- "unstamped, not refused HERE" disposition the unstamped-GUC branch already uses three lines
-- down, reached by one more path. A journal row is not authority-bearing (it asserts a
-- refusal happened, not a proposition the writer wants credited), and s21's NULL-never-distinct
-- discipline already makes an unverified stamp claim-inert everywhere the kernel reads
-- stamp_verified -- so recording false here manufactures no new trust, it only lets the ONE
-- row whose entire purpose is "the refusal happened" survive its own trigger chain. Every
-- OTHER kind's behavior -- including the raise text, byte-for-byte -- is UNCHANGED: a
-- forged-complete stamp on any ordinary write (ledger note, review, registration, obligation,
-- artifact, missive, ...) still raises exactly as it always has; this delta narrows nothing
-- about what a hostile writer can get PAST the gate, it only lets the recording OF that
-- hostile attempt's refusal itself land.
--
-- WHY THIS IS THE RIGHT PLACE, NOT journal_write_refusal ITSELF (a design choice named, not
-- merely followed): the double-fire happens because set_stamp cannot tell "this INSERT is the
-- journaler's own recovery write" from "this INSERT is an ordinary hostile write" -- both carry
-- the SAME forged session GUCs, because they run in the SAME transaction/session. The
-- information that distinguishes them (NEW.kind = 'write_refused') is available to set_stamp
-- for free (it already reads NEW.* to set the stamp_* columns); teaching journal_write_refusal
-- to clear the GUCs before its own INSERT would touch shared session state in a SECURITY
-- DEFINER function that other code (the outer boundary function's own eventual re-raise path,
-- or a future caller) might still expect to read, and would be a second, harder-to-audit
-- mechanism for the identical fact set_stamp already has in hand as NEW.kind. One guard, one
-- function, ADR-0012 P1's "one home" applied to the fix itself.
--
-- NO CHANGE to kernel.journal_write_refusal or the four (now seven, per s51/s57/s58) boundary
-- functions calling it (spec §1 item 2): once the journal INSERT itself survives its own
-- set_stamp fire, s43's existing SQLSTATE-class catch (22*/23*/P0*) inside EACH boundary
-- function's own outer handler does the rest unchanged -- the forged-stamp refusal (itself a
-- P0001 from set_stamp, on the ORIGINAL caller-attempted row) is caught there exactly as any
-- other P0* refusal already is, journaled via journal_write_refusal (which s65's own
-- refusal_attempted_kind extraction and s49's own attempted-actor guard already apply to this
-- refusal like any other), and returned as a typed 'refused' verdict. This delta's own witness
-- (this file's WITNESS PLAN reference, seen-red/s66-forged-stamp-journal-totality/) confirms
-- this end-to-end: the SAME forged-complete-stamp probe that raised uncaught pre-delta returns
-- a typed refused verdict post-delta, with a committed write_refused row.
--
-- CLOSURE STATEMENT (ADR-0000 Rule 2(a)): the write paths that can meet a forged-complete
-- stamp are exactly the INSERTs on the ledger table (one table, one set_stamp trigger, fires
-- on all of them) -- split into (a) caller-attempted rows via the SEVEN s43-family boundary
-- functions (ledger_write, review_write, registration_write, obligation_write, s51's
-- artifact_write, s57's obligation_revoke, s58's missive_dispose), refused exactly as before
-- (untouched by this delta), and (b) the journaler's own write_refused row, the ONE branch this
-- delta changes. QUANTIFICATION: every non-write_refused kind still raises on a forged-complete
-- stamp, byte-identical text, verified in this delta's own fixture (the ordinary valid-stamp
-- and ordinary unstamped-write legs are also re-witnessed byte-identical pre/post, per the
-- spec's own witness plan). VIEWS/COLUMNS/KINDS: none added -- this delta touches ONE existing
-- trigger function body, no new column, no new kind, no CHECK narrowed or widened.
-- compute_row_hash: UNCHANGED (no new column to append; stamp_verified's own hashfield rendering
-- is already covered since s17/s43, and this delta changes WHEN false is assigned, never the
-- column's own type or presence). ENGINE: unaffected, grep-verified -- no engine/ file reads
-- stamp_verified's PROVENANCE (only its value, already covered), so no derivation changes.
-- GATES: hash-coverage (unaffected, no column change); kind-shape manifest (unaffected, no
-- column/kind change); lineage-reissue-lineage (citation + prior-body-sha256 satisfied below,
-- both checks apply since s66 > 63); kernel-function-census (bank updated same commit --
-- schema:set_stamp's hash changes); fixture census (this delta's own seen-red/ entry
-- registered).
--
-- DENOMINATION: unchanged -- stamp_verified stays the same boolean the kernel has always used
-- for "this row's stamp did NOT come from a validated interception"; no new value, no new
-- vocabulary member, no new column. The one guard's condition (NEW.kind = 'write_refused') is
-- the SAME closed kind string s43 already minted and s65's own one-way CHECKs already key on.
--
-- FAIL-SAFE CLASSIFICATION (CLAUDE.md ORCHESTRATION decision tree): NOT CLASS-RATIFIED
-- FAIL-SAFE, stated plainly (s43/s49/s65's own precedent for this same honesty requirement):
-- this delta re-issues an EXISTING function body via CREATE OR REPLACE (kernel.set_stamp) and
-- alters ONE branch of a live trigger's behavior for one kind -- not a letter-2(a) "only adds"
-- shape, even though its EFFECT is strictly fail-safe (a refusal that previously destroyed
-- itself now gets recorded; nothing that was ACCEPTED before is accepted differently; nothing
-- that RAISED before now silently succeeds -- the forged writer's attempted row is STILL
-- refused, only the refusal's OWN recording now survives). It ships under the maintainer's OWN
-- EXPLICIT RATIFICATION of this specific fix (design/FABLE-S66-S67-JOURNAL-TOTALITY-SPEC.md,
-- ledger row 1519, "it's yes of course" -- verbatim), read per the 2026-07-11 vocabulary note,
-- exactly the posture s43/s49/s65 shipped under for the same reason.
--
-- LIMITS (pre-registered, matching s43/s49/s65's own disclosure convention):
--   - The guard fires ONLY when NEW.kind = 'write_refused' -- a forged-complete stamp on any
--     other kind still raises, unchanged. This is deliberate (spec §1's own scoping): widening
--     which OTHER kinds tolerate a forged stamp is NOT in this ratification.
--   - The journaled write_refused row's own stamp_verified is now `false` for exactly this one
--     escape class (a forged-complete stamp coincident with a refusal); every OTHER
--     write_refused row's stamp_verified reflects its own session's actual stamp state exactly
--     as before (an intercepted, correctly-stamped write that happens to be refused for some
--     OTHER reason still records stamp_verified=true on its journal row, unaffected by this
--     guard, which only ever changes an outcome that would otherwise have RAISED).
--   - This delta does not change what happens when the journal INSERT fails for any OTHER
--     reason (a genuine integrity violation on the write_refused row shape itself, say) --
--     that stays s43's own named, disclosed loud-abort/sequence-gap/server-log composition,
--     untouched here.
--   - Every other named limit in s17/s23/s43/s49/s65's own headers (the tripwire-not-
--     authentication posture, the +-300s liveness window, session_user attribution's
--     one-principal-per-login-role assumption) is unchanged by this delta and not re-stated in
--     full here.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/.../s65): schema/kern/role
-- are psql variables so this delta is VALIDATED on a throwaway substrate before any real apply.
--   VALIDATE (reachable throwaway): apply the FULL s15..s65 chain (see kernel/lineage/
--   s65-refusal-attempted-kind.sql's own VALIDATE block), THEN -f
--   s66-forged-stamp-journal-totality.sql (genesis seed per s26; register the write-boundary
--   principal before exercising any refusal path, or the journaler aborts loudly by design,
--   unchanged since s43).
--   REAL: NEVER applied to any existing world by this authoring act (runs-are-strictly-linear,
--   2026-07-11). Enters a FUTURE world's birth chain via bootstrap/new-project.sh's
--   LINEAGE_CHAIN narrative (this same commit) and its GENERATED apply loop (picks this file up
--   automatically from the kernel/lineage/ directory glob, no separate wiring act needed for
--   the apply side). Authored and scratch-witnessed on a scratch schema pair in the TOY db
--   only (world s66probe / s66probe_kernel / s66probe_rw, torn down after).
-- Run as the schema owner (bork). Idempotent (CREATE OR REPLACE FUNCTION; DROP/CREATE TRIGGER).
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
-- ELEMENT 1 -- kernel.set_stamp RE-ISSUED: the s23 body (kernel/lineage/
-- s23-per-invocation-stamp-token.sql), BYTE-IDENTICAL above and below the new branch, with ONE
-- ADDITION -- an ELSIF between the "valid stamp" arm and the "raise" arm, checked ONLY on the
-- validation-failure path, gated on NEW.kind = 'write_refused'. No other line of this function
-- changes: the GUC reads, the stamp_session/agent/ts/hmac/invocation assignments, the raise
-- text, and the unstamped-path stamp_verified := false all stand UNCHANGED. Trigger
-- name/timing/position unchanged (still fires on every INSERT to :"schema".ledger, alphabetized
-- the same as s17/s23 left it).
-- prior-body-sha256: 15a19ee34702fafa8baaddb7514609f3f98d45252ae056d9e16e22e5a730bdb4 (s23-per-invocation-stamp-token.sql)
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".set_stamp() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", :"kern", pg_temp AS $fn$
DECLARE s text; a text; t bigint; h text;
BEGIN
  -- read the interception-injected GUCs (missing_ok => NULL when a non-intercepted path wrote the row)
  s := current_setting('app.vendor_session', true);
  a := current_setting('app.vendor_agent', true);
  t := nullif(current_setting('app.vendor_ts', true), '')::bigint;
  h := current_setting('app.vendor_hmac', true);
  -- the writer cannot self-set the stamp columns: they are ALWAYS derived from the GUCs, overwriting
  -- whatever the INSERT supplied (a forged stamp_* column is ignored; only a valid GUC-carried HMAC counts)
  NEW.stamp_session := s;
  NEW.stamp_agent := a;
  NEW.stamp_ts := t;
  NEW.stamp_hmac := h;
  -- s23 CONTEMPORANEITY TOKEN (design/CONTEMPORANEITY-AUDIT.md Part 1): read one register down,
  -- EXACTLY as stamp_session above (current_setting, missing_ok => NULL for any non-intercepted
  -- path). CAPTURE-ONLY — it feeds NEITHER the HMAC verification nor stamp_verified below, so no
  -- existing refusal/verification semantics change. Overwritten from the GUC like every other
  -- stamp_* column, so a writer cannot self-set it via the INSERT column (only via the GUC — see
  -- the UNAUTHENTICATED limit in this file's header).
  NEW.stamp_invocation := current_setting('app.vendor_invocation', true);
  IF s IS NOT NULL AND a IS NOT NULL AND t IS NOT NULL AND h IS NOT NULL THEN
    IF stamp_valid(s, a, t, h) THEN
      NEW.stamp_verified := true;
    ELSIF NEW.kind = 'write_refused' THEN
      -- s66 GUARD (kernel/lineage/s66-forged-stamp-journal-totality.sql): the journaler's own
      -- write_refused INSERT re-fires this SAME trigger on the SAME (still-forged) session
      -- GUCs -- witnessed double-raise, spec §1. A journal row is not authority-bearing (s21's
      -- NULL-never-distinct discipline already makes an unverified stamp claim-inert), so
      -- record the honest fact (stamp_verified := false, the SAME value the unstamped branch
      -- below already uses) instead of raising a second time and destroying the very refusal
      -- record this row exists to be. Every OTHER kind still raises on the SAME condition,
      -- unchanged -- this branch is reached ONLY for the one kind the boundary's own journaler
      -- mints, never by a caller-supplied kind (kernel.ledger_write's own SERVER-OWNED-key
      -- blocklist already refuses a caller attempting kind='write_refused' directly, s43/s65
      -- Element 4.2/Element 5 unchanged).
      NEW.stamp_verified := false;
    ELSE
      RAISE EXCEPTION 'Ledger policy: the write stamp did not validate (fabricated, replayed, or stale). Ledger writes are stamped by the tool interception, not typed by the writer — route this write through the intercepted psql path; do not hand-set app.vendor_*.';
    END IF;
  ELSE
    NEW.stamp_verified := false;   -- unstamped (a non-intercepted path); recorded, not refused HERE (the
                                   -- independence gate refuses an unverified-row independence claim)
  END IF;
  RETURN NEW;
END; $fn$;
-- Idempotent DROP/CREATE of the trigger — byte-identical definition (BEFORE INSERT FOR EACH
-- ROW), no change; present only so this delta is self-contained/re-runnable (the s17/s19/s23
-- idiom). CREATE OR REPLACE FUNCTION already rebinds the existing trigger to the new body.
DROP TRIGGER IF EXISTS set_stamp ON :"schema".ledger;
CREATE TRIGGER set_stamp BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".set_stamp();

COMMENT ON COLUMN :"schema".ledger.stamp_verified IS
  'TRUE iff this row carried a valid, fresh interception stamp (HMAC matched the apparatus
   secret). An unstamped row is recorded verified=false; a PRESENT-but-invalid stamp is refused
   at write time for every kind EXCEPT the boundary''s own write_refused journal row, which
   records verified=false instead of destroying the refusal it exists to journal (s66:
   kernel/lineage/s66-forged-stamp-journal-totality.sql -- the forged-complete-stamp double-fire
   through kernel.journal_write_refusal''s own INSERT, ledger row 1519).';
-- ============================================================================================
