-- s17 STAMP MECHANISM — interception-stamped row provenance (BACKLOG ffafa59; finding 31 /
-- measure-once-then-mechanize). An ADDITIVE delta applied ON TOP of the s15/s16 kernel (the lineage's
-- established remediation-delta idiom, e.g. s13-review_detail-truncate-guard-remediation.sql) — NOT a
-- second hand-copy of the 342-line kernel body (ADR-0012 P1: one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db are):
--   A ledger row's `actor` is a principal the SUBJECT registers and supplies, so the SoD gate
--   (validate_review) keys on a value the subject controls — finding 31's `proxy_written(7)`: ONE context
--   registered a "reviewer" principal and countersigned its own work; actor differed, SoD passed, but no
--   genuinely distinct agent reviewed. The stamp binds each row to the ACTUAL invocation identity
--   (session_id + agent_id), injected by the tool interception (a PreToolUse hook), NOT typed by the
--   writer. The writer can neither omit it (the hook stamps every intercepted write) nor forge it (the
--   HMAC needs a secret the subject role cannot read). A self-review then carries the SAME stamp identity
--   as its authoring — mechanically visible — while a genuinely distinct subagent carries a different one.
--
-- LIMITS (pre-registered, BACKLOG ffafa59): the hook runs as the same OS user (the secret is hunt-able);
--   a subject that SETs app.vendor_* itself cannot produce a valid HMAC (no secret) -> refused; a
--   script-mediated INSERT bypassing the psql interception is UNSTAMPED -> refused where a stamp is
--   required, and is itself a disposition finding. A TRIPWIRE, not authentication.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15): schema/kern/role are psql vars so
--   the delta is VALIDATED on a throwaway substrate before any real apply.
--     VALIDATE:  psql -h 192.168.122.1 -d harness -v schema=s17val -v kern=s17val_kernel -v role=s17val_rw \
--                  -f s15-schema.sql -f s17-stamp-mechanism.sql
-- Run as the schema owner (bork). Idempotent.

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

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================================
-- THE APPARATUS SECRET — one home, apparatus-owned, subject-unreadable (the negative control)
-- ============================================================================================
-- Exactly one row (only_one PK + CHECK). The secret itself is PROVISIONED AT ARM (a fresh random value),
-- never in this DDL — the DDL creates the empty, ungranted table. The subject role gets NO privilege on
-- it: a subject `SELECT * FROM :kern.stamp_secret` must fail `permission denied` (verified by a
-- negative-control SELECT as that role at arm time — an ARMING CHECK).
CREATE TABLE IF NOT EXISTS :"kern".stamp_secret (
    only_one boolean PRIMARY KEY DEFAULT true CHECK (only_one),
    secret   bytea NOT NULL
);
REVOKE ALL ON :"kern".stamp_secret FROM PUBLIC;
-- (no GRANT to :role — the subject cannot read the secret; the SECURITY DEFINER function below is the
--  only sanctioned reader, and it never returns the secret, only a boolean verdict.)

-- ============================================================================================
-- SECURITY DEFINER recompute — the subject may CALL it, never READ the secret
-- ============================================================================================
-- Runs as the function owner (apparatus), so it reads stamp_secret the subject cannot. Recomputes
-- HMAC(secret, session||'|'||agent||'|'||ts) and returns TRUE iff it matches the presented hmac AND the
-- stamp ts is within the freshness window (a replayed/stale stamp is refused). Fail-closed: an
-- unprovisioned secret or any NULL input returns FALSE (nothing validates until the secret is armed).
CREATE OR REPLACE FUNCTION :"kern".stamp_valid(p_session text, p_agent text, p_ts bigint, p_hmac text)
    RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = :"kern", public, pg_temp AS $fn$
DECLARE k bytea; computed text; skew bigint;
BEGIN
  IF p_session IS NULL OR p_agent IS NULL OR p_ts IS NULL OR p_hmac IS NULL THEN
    RETURN false;
  END IF;
  SELECT secret INTO k FROM stamp_secret LIMIT 1;
  IF k IS NULL THEN
    RETURN false;   -- fail-closed: no secret provisioned yet
  END IF;
  -- hmac(data bytea, key bytea, type) — data is convert_to(...,'utf8') so it matches Python's
  -- hmac.new(secret, ("%s|%s|%s" % (session,agent,ts)).encode(), sha256).hexdigest() byte-for-byte.
  computed := encode(hmac(convert_to(p_session || '|' || p_agent || '|' || p_ts::text, 'utf8'),
                          k, 'sha256'), 'hex');
  IF computed <> p_hmac THEN
    RETURN false;
  END IF;
  skew := abs(extract(epoch FROM now())::bigint - p_ts);
  IF skew > 300 THEN
    RETURN false;   -- stale / replayed beyond the +-300s liveness window
  END IF;
  RETURN true;
END; $fn$;
REVOKE ALL ON FUNCTION :"kern".stamp_valid(text, text, bigint, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION :"kern".stamp_valid(text, text, bigint, text) TO :"role";

-- ============================================================================================
-- STAMP COLUMNS + set_stamp trigger (fires BEFORE INSERT, alphabetically after set_actor, before
-- validate_review — so the distinctness gate item-4 adds can read a set stamp)
-- ============================================================================================
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS stamp_session  text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS stamp_agent    text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS stamp_ts       bigint;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS stamp_hmac     text;
ALTER TABLE :"schema".ledger ADD COLUMN IF NOT EXISTS stamp_verified boolean NOT NULL DEFAULT false;

COMMENT ON COLUMN :"schema".ledger.stamp_agent IS
  'The invocation identity that WROTE this row (the tool interception''s agent id; "main" for the top-level context). Injected by the hook, never typed by the writer; the SoD distinctness of a review is keyed on THIS, not on the writer-supplied actor.';
COMMENT ON COLUMN :"schema".ledger.stamp_verified IS
  'TRUE iff this row carried a valid, fresh interception stamp (HMAC matched the apparatus secret). An unstamped row is recorded verified=false; a PRESENT-but-invalid stamp is refused at write time.';

-- search_path carries :"kern" (interpolated HERE, outside the $fn$ body where psql vars do not expand),
-- so the body calls stamp_valid UNQUALIFIED and it resolves in the kernel schema in BOTH validate mode
-- (custom kern) and real apply (kern='kernel') — no hardcoded schema (cf. s15's set_actor, frozen).
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
DROP TRIGGER IF EXISTS set_stamp ON :"schema".ledger;
CREATE TRIGGER set_stamp BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".set_stamp();

-- A derived, read-only view of the stamp-vs-actor divergence: a review whose stamp_agent EQUALS the
-- stamp_agent of the row it regards is a self-review by one invocation (proxy_written), regardless of the
-- writer-supplied actor principals. The independence gate (item 4) consults this; it is also the audit's
-- first live stamp-vs-acts read (SEED ride-along).
CREATE OR REPLACE VIEW :"schema".review_stamp_distinctness
    WITH (security_invoker = true) AS
SELECT r.id AS review_id, r.actor AS review_actor, r.stamp_agent AS review_stamp_agent,
       g.id AS regards_id, g.actor AS regards_actor, g.stamp_agent AS regards_stamp_agent,
       (r.stamp_agent IS NOT DISTINCT FROM g.stamp_agent) AS same_invocation,
       (r.stamp_verified AND g.stamp_verified)            AS both_stamped
FROM   :"schema".ledger r
JOIN   :"schema".ledger g ON g.id = r.regards
WHERE  r.kind = 'review';
GRANT SELECT ON :"schema".review_stamp_distinctness TO :"role";
