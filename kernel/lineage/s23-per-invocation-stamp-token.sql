-- s23 PER-INVOCATION STAMP TOKEN — the contemporaneity-audit correlation column
-- (AUTHORED FROM design/CONTEMPORANEITY-AUDIT.md, Part 1; Fable-authored memo 2026-07-11, this
-- delta Sonnet-authored FROM it per the delegation contract, then scratch-witnessed both polarities).
-- An ADDITIVE delta applied ON TOP of the s15/s17/s17b/s19/s20/s21/s22 kernel (the established
-- remediation-delta idiom, cf. s17-stamp-mechanism.sql / s20-* / s22-*), NOT a retro-edit of a
-- frozen sNN record (ADR-0005 Rule 8) and NOT a second hand-copy of the kernel body (ADR-0012 P1:
-- one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db are):
--
--   design/CONTEMPORANEITY-AUDIT.md's Part 1. The ledger's `ts` is INSERT time masquerading as
--   event time, and nothing binds a row to the tool INVOCATION that wrote it — so honest
--   simultaneity (an LLM emitting N conclusions 0.02s apart) and run-5-style backfill (19 rows
--   written retroactively in 0.43s) are the SAME row shape, distinguishable only by hand-correlating
--   transcripts (runs 5/7/8 did it ad-hoc, i.e. not at all between crises). The fix (Part 1, this
--   delta + the hook change) makes the batching STRUCTURE visible: `hooks/stamp_intercept.py` mints a
--   per-Bash-invocation UUID, exports it via the SAME PGOPTIONS/GUC path as the existing stamp GUCs
--   (`app.vendor_invocation`), and journals (token, wall-clock, command hash) to
--   `.claude/logs/invocations.jsonl` — the "actual event" side. This delta adds the LEDGER side: a
--   sixth stamp column `stamp_invocation`, captured by the existing set_stamp trigger EXACTLY as
--   `stamp_session` is (one register down). Part 2 (the correlation `audit` verb that joins the two
--   sides) is a SEPARATE, later commission — NOT in this delta.
--
--   CAPTURE-ONLY, VERIFICATION-INERT (the load-bearing property of this delta). Unlike
--   stamp_session/agent/ts/hmac — which feed the HMAC recompute and set stamp_verified — the
--   invocation token participates in NO verification and NO refusal. It is read from its GUC
--   (missing_ok => NULL) and stored, full stop. A row with a valid HMAC stamp but no injected token
--   still verifies true; a row with a self-set token but no valid HMAC still records verified=false.
--   So this delta relaxes no refusal and alters no existing semantics — the class-ratified fail-safe
--   shape (maintainer ruling 2026-07-09: ADDS a derived column only). BUT it touches the stamping
--   machinery (set_stamp is re-issued to read one more GUC), so per the memo's own standing
--   doubt-check the authoring review must certify "existing-semantics wobble: none" or route the
--   whole delta to the maintainer instead of the class. (Scratch witness: the s17 fixture-style
--   checks — HMAC agreement, forgery refused, stale refused, unstamped recorded — pass byte-identical
--   before and after this delta; stamp_verified is unchanged in every case.)
--
--   BACKWARD-HONEST: rows written before this ALTER carry NULL stamp_invocation (nullable, no
--   DEFAULT) — visibly "pre-token era", never guessed (memo's own requirement).
--
--   HONEST LIMIT, NAMED (not a wobble in existing behavior — a property of the NEW column): the
--   invocation token is UNAUTHENTICATED. session/agent/ts are bound into the HMAC the subject role
--   cannot forge; the invocation token has no HMAC (it is a plain correlation aid). A same-OS-user
--   subject that self-SETs `app.vendor_invocation` can therefore forge the correlation token — the
--   same disclosed tripwire-not-authentication posture s17 already carries for the whole mechanism
--   (BACKLOG ffafa59). The token makes the record's SHAPE honest, not the mind legible; it does not
--   widen or narrow any existing guarantee.
--
--   CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--
--     - INVARIANT: the per-invocation token is a SIXTH stamp column on `ledger`, captured by the
--       one set_stamp trigger (one home, ADR-0012 P1), verification-inert; and — the s20/s22 lesson
--       RE-APPLIED to this new column, not merely cited — every view that reads `ledger` with an
--       EXPLICIT column list is re-issued to append stamp_invocation IN THIS SAME DELTA, or the
--       "column-complete w.r.t. the base table" class s20 fixed recurs one column later.
--
--     - QUANTIFICATION UNIVERSE — enumerated by reading every view the s15+s17+s17b+s19+s20+s21+s22
--       chain exposes to :role (the live, user-facing kernel), re-verifying s20's/s22's own
--       enumeration against the ONE new column:
--         * ledger_current           — explicit column list (s20/s22). GAINS stamp_invocation HERE,
--           APPENDED AT THE END (see the note on the view block below — CREATE OR REPLACE VIEW forbids
--           reordering or renaming existing columns without dropping the GRANT, so the new column
--           cannot be grouped next to the other stamp_* columns; it appends, exactly as s22's own
--           work_* columns had to append after the stamp_* block).
--         * countersigned_in_force   — same: explicit list (s20/s22), GAINS stamp_invocation HERE.
--         * review_gap               — explicit cols (l.id, l.actor, o.scope, o.assigned_by); the
--           invocation token is not meaningful to an obligation-gap read. NOT extended — named.
--         * question_status          — explicit cols, no ledger-row passthrough. NOT in this class.
--         * work_item_current / work_item_violations (s22) — derived work-state aggregates, no
--           general ledger-row passthrough; the invocation token is not a work-state fact. NOT in
--           this class — named, not silently skipped.
--         * review_stamp_distinctness (s17/s21) — reads only stamp_session/stamp_agent/actor via
--           r./g. aliases (the distinctness question keys on agent, not invocation). NOT in this
--           class; deliberately NOT extended (the token is a contemporaneity aid, not a SoD input).
--       So the "column-complete" class has EXACTLY TWO members this delta must re-issue (both done
--       here); four views are checked and confirmed NOT members (named, not assumed).
--     TRIGGERS — set_stamp is the SOLE capture path (grep-verified: s17 is its only home; s19/s21/s22
--       do not re-issue it). It is re-issued here with ONE added assignment line and an otherwise
--       byte-identical body + an idempotent DROP/CREATE of its trigger (no trigger-definition change).
--     ENGINE — NONE. grep-verified: no engine/ file reads any stamp_* column (the ASP floor mirrors
--       ledger FACTS, not provenance stamps), so stamp_invocation has no floor atom and no SQL/ASP
--       differential to run — named, not assumed. (Part 2's `audit` verb will consume the token +
--       the journal; that is its own later commission, out of scope here.)
--
--     - DENOMINATION: the column is `text` (a UUID string, the hook's own mint), nullable with no
--       DEFAULT (the pre-token era must read as NULL, never a fabricated value). The GUC is
--       `app.vendor_invocation`, mirroring the `app.vendor_*` namespace + `stamp_session`/
--       `stamp_invocation` naming correspondence the existing four GUC/column pairs already use.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s22): schema/kern are psql
--   variables (no :role-affecting change — CREATE OR REPLACE VIEW preserves the existing GRANTs, and
--   this delta adds no new grantable object) so this delta is VALIDATED on a throwaway substrate
--   before any real apply.
--     VALIDATE (reachable throwaway):
--        psql -h 192.168.122.1 -d toy -v ON_ERROR_STOP=1 \
--          -v schema=s23val -v kern=s23val_kernel -v role=s23val_rw \
--          -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--          -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--          -f s21-session-aware-distinctness.sql -f s22-work-item-ledger.sql \
--          -f s23-per-invocation-stamp-token.sql
--     REAL (owed to a maintainer-assented apply on a live deployment — NOT taken here; never apply
--     bare, spell out every -v var explicitly — standing rule):
--        psql -h 192.168.122.1 -d <db> -v schema=<schema> -v kern=<kern> -v role=<role> \
--          -f s23-per-invocation-stamp-token.sql
--   This delta was authored and scratch-witnessed on a scratch schema pair in the TOY db only
--   (schema invprobe / invprobe_kernel, role invprobe_rw). NOT applied to any live schema by this pass.
-- Run as the schema owner (bork). Idempotent (ADD COLUMN IF NOT EXISTS; CREATE OR REPLACE FUNCTION;
-- DROP/CREATE TRIGGER; CREATE OR REPLACE VIEW).

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif

-- ============================================================================================
-- THE SIXTH STAMP COLUMN (nullable, no DEFAULT — pre-token rows stay NULL, visibly).
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS stamp_invocation text;

COMMENT ON COLUMN :"schema".ledger.stamp_invocation IS
  'The per-Bash-invocation correlation token (a UUID minted by hooks/stamp_intercept.py and exported
   via the app.vendor_invocation GUC, one register below the HMAC-bound stamp GUCs). CAPTURE-ONLY: it
   feeds no HMAC verification and no refusal — stamp_verified is computed exactly as before, ignoring
   this column. NULL for any non-intercepted write and for every row predating s23 (the pre-token
   era). Correlates a ledger row to the .claude/logs/invocations.jsonl journal line the hook wrote
   when it injected this token (design/CONTEMPORANEITY-AUDIT.md Part 1; Part 2''s audit verb joins the
   two sides). UNAUTHENTICATED (no HMAC over it): a same-OS-user subject that self-SETs
   app.vendor_invocation can forge it — a disclosed tripwire aid, not authentication (s17''s posture).';

-- ============================================================================================
-- set_stamp RE-ISSUED — the SOLE capture path (s17's only home; s19/s21/s22 leave it untouched),
-- re-issued with ONE added assignment reading app.vendor_invocation EXACTLY as app.vendor_session is
-- read. Everything else is byte-identical to s17-stamp-mechanism.sql's set_stamp: the HMAC recompute,
-- the +-300s liveness, the forge/stale RAISE, and the verified=false unstamped path all stand
-- UNCHANGED. The new line is CAPTURE-ONLY and sits OUTSIDE the verification IF, so no existing refusal
-- or verification semantics move (the delta's whole class claim). search_path carries :"kern"
-- interpolated HERE (outside the $fn$ body where psql vars do not expand), so stamp_valid resolves in
-- the kernel schema in BOTH validate mode and real apply — the s17 idiom, preserved.
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
    ELSE
      RAISE EXCEPTION 'Ledger policy: the write stamp did not validate (fabricated, replayed, or stale). Ledger writes are stamped by the tool interception, not typed by the writer — route this write through the intercepted psql path; do not hand-set app.vendor_*.';
    END IF;
  ELSE
    NEW.stamp_verified := false;   -- unstamped (a non-intercepted path); recorded, not refused HERE (the
                                   -- independence gate refuses an unverified-row independence claim)
  END IF;
  RETURN NEW;
END; $fn$;
-- Idempotent DROP/CREATE of the trigger — byte-identical definition (BEFORE INSERT FOR EACH ROW),
-- no change; present only so this delta is self-contained/re-runnable (the s17/s19 idiom). CREATE OR
-- REPLACE FUNCTION already rebinds the existing trigger to the new body, so this is a no-op on a live
-- deployment.
DROP TRIGGER IF EXISTS set_stamp ON :"schema".ledger;
CREATE TRIGGER set_stamp BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".set_stamp();

-- ============================================================================================
-- s20/s22 LESSON RE-APPLIED: ledger_current + countersigned_in_force GAIN stamp_invocation, APPENDED
-- AT THE END. It CANNOT be grouped next to the other stamp_* columns: CREATE OR REPLACE VIEW forbids
-- renaming/reordering the existing columns (the GRANT survives ONLY if pre-existing columns keep
-- name/type/order), so the new column appends — exactly as s22's own work_* columns had to append
-- after the stamp_* block. Explicit column lists throughout — never `l.*` again (the class this
-- re-issue exists to foreclose one more time). Column list = s22's exact list + l.stamp_invocation.
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.id, l.ts, l.session, l.kind, l.statement, l.rationale, l.status, l.evidence,
       l.confidence, l.supersedes, l.refs, l.concern, l.enacts, l.actor, l.regards,
       l.amends, l.amends_scope, l.answers,
       l.stamp_session, l.stamp_agent, l.stamp_ts, l.stamp_hmac, l.stamp_verified,
       l.work_slug, l.work_title, l.work_depends_on, l.work_resolution, l.work_witness,
       l.stamp_invocation
FROM   :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));
