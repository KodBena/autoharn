-- s21 SESSION-AWARE STAMP DISTINCTNESS + s19 residue fold-in (design/S21-SESSION-AWARE-DISTINCTNESS.md,
-- Fable-authored spec, session be693afb, 2026-07-09, PENDING MAINTAINER RATIFICATION — this delta is
-- AUTHORED and SCRATCH-WITNESSED only; APPLYING it to any live deployment is the maintainer's act, not
-- taken here). An ADDITIVE delta applied ON TOP of the s15/s17/s19/s20 kernel (the established
-- remediation-delta idiom), NOT a retro-edit of a frozen sNN record (ADR-0005 Rule 8) and NOT a second
-- hand-copy of the kernel body (ADR-0012 P1: one home per mechanism).
--
-- WHY (operator-side prose; NOT subject-visible — only the catalog objects inside the opaque db are):
--
--   DEFECT 1 — distinctness is session-blind (falsely refuses honest cross-session review). s17's
--   `validate_independence` and the `review_stamp_distinctness` view decide "distinct invocation" from
--   `stamp_agent` ALONE. Every interactive session's main thread stamps `agent='main'`, so two DIFFERENT
--   sessions' main threads are indistinguishable: a genuinely independent second-session review claiming
--   `technical` is refused as same-invocation. Fails safe (refuses an honest claim; never admits a false
--   one) — witnessed consequence (BACKLOG, 2026-07-09): e18's second-session reviewers could pass only
--   as subagents, foreclosing the "separate interactive reviewer session" idiom the kernel's own design
--   commissions (AGENTIC-PATTERNS 11, ephemeral principals).
--
--   THE FIX (the type answer): an invocation's identity is the PAIR `(stamp_session, stamp_agent)`, never
--   `stamp_agent` alone.
--     - `validate_independence`: a technical/managerial/financial claim is refused iff either row is
--       unstamped/unverified, OR the (session, agent) pair on the review equals the pair on the
--       regards-target. A NULL half on EITHER side is treated as NOT distinct (fail-safe, never
--       fail-open) — this can only arise for the regarded row (an unverified independence claim on the
--       REVIEWING row is already refused one check earlier by the pre-existing rev_verified gate).
--     - `review_stamp_distinctness.same_invocation`: recomputed on the pair, same rule; the two new
--       `*_stamp_session` columns are ADDED (never replacing `*_stamp_agent`, per the lineage's
--       additive/never-remove idiom — s17_stamp_fixture.py item 6 reads `same_invocation` unchanged).
--
--   COMPATIBILITY: strictly more permissive than agent-only for cross-session (retires the false
--   refusal), IDENTICAL for same-session (distinct agents within one session remain distinct; the same
--   agent within one session remains not-distinct — the witnessed e17 shape is preserved exactly).
--   Insert-time trigger only — no retroactive effect; e17/e18's passing rows (distinct agents, same or
--   distinct sessions) pass under both rules unchanged.
--
--   DEFECT 2 (fold-in) — s19 residue: validate_* resolve the ledger via SESSION search_path, and
--   SET ROLE voids the login-default premise (BACKLOG, "s19 residue", 2026-07-09). s19's own closure
--   statement scoped `validate_enacts/review/amends/answers` OUT of the search-path class with the
--   premise "resolved by the role's login search_path" — a premise that holds only when the writer LOGS
--   IN as the ledger role. The documented usage pattern (QUICKSTART, WALKTHROUGH) connects as the OWNER
--   and `SET ROLE`s to the subject role instead, and Postgres applies a role's `ALTER ROLE ... SET
--   search_path` at SESSION START, never at `SET ROLE` — so under that pattern the four validate_*
--   triggers' unqualified `FROM ledger` reads resolve nothing UNLESS the session also carries an
--   explicit `SET search_path`, today undocumented as a hard requirement and masked only because every
--   shipped walkthrough happens to issue that line. Fix exactly as s19 itself did for set_actor/
--   set_stamp (and as the s19 closure statement's own denomination already prescribes): each of the four
--   functions gains a per-function `SET search_path = :"schema", pg_temp`.
--
--   CLOSURE STATEMENT (ADR-0000 Rule 2(a), 2026-07-02 amendment):
--     - INVARIANT (defect 1): every consumer of invocation-distinctness derives it from the
--       (stamp_session, stamp_agent) PAIR; no consumer reads stamp_agent alone as an identity.
--       INVARIANT (defect 2): every kernel trigger/function that reads the ledger's OWN schema (not just
--       kernel objects — s19's narrower invariant, widened here to the whole in-chain family) resolves it
--       via a per-function `SET search_path`, never the ambient session/role search_path.
--     - QUANTIFICATION UNIVERSE — enumerated by grep over the WHOLE TREE (kernel/lineage/, instruments/,
--       engine/, kernel/fixtures/), not just kernel/lineage/, per the ADR-0000 2026-07-02 amendment's
--       "check the universe outward, not the scope of the fix already built":
--         DEFECT-1 UNIVERSE (readers of stamp_agent/same_invocation as a distinctness signal):
--         * validate_independence()          (s17-independence-vocabulary.sql) — COVERED here.
--         * review_stamp_distinctness (view) (s17-stamp-mechanism.sql)         — COVERED here.
--         * stamp_valid()/set_stamp()         — NOT COVERED, and correctly so: they verify HMAC
--           INTEGRITY (is this stamp genuine?), never distinctness (are these two stamps the same
--           invocation?) — a different question, out of this defect's scope by construction.
--         * the engine EDB (ledger_edb.py / ledger_tnow.lp et al.) — NOT COVERED: it carries no stamp
--           vocabulary at all, by design (BACKLOG, engine-frontier-semantics-SEED.md §B.3 names this as a
--           standing, named gap on the engine side, not a same-class defect here).
--         * `instruments/review_fixpoint.py` (`review_fixpoint_verdict`, the e18 criterion-review lever)
--           and its caller `instruments/review_fixpoint_close.py` — FOUND IN PASSING BY THIS GREP,
--           NAMED AS NOT COVERED BY THIS DDL: `FpRow` carries `stamp_agent` only (no `stamp_session`
--           field), and both the "stamp-distinct" join (line ~41: `r.stamp_agent != author_stamp`) and
--           the "first-contact" join (line ~47: `o.stamp_agent == rev.stamp_agent`) exhibit the IDENTICAL
--           session-blind shape defect 1 fixes here — a genuinely fresh cross-session criterion-reviewer
--           whose agent also stamps 'main' would be mis-scored as NOT first-contact / NOT stamp-distinct.
--           This is a PYTHON instrument reading `l.stamp_agent` directly (`review_fixpoint_close.py`'s
--           `_SQL`), not a kernel DDL trigger/view — no SQL delta in this file can cover it; the real fix
--           (thread `stamp_session` through `FpRow` and the SELECT, mirroring this delta's rule) is a
--           genuine type, its blast radius deferred, filed per ADR-0000's Exceptions clause — see BACKLOG.
--         * `kernel/fixtures/s17_independence_fixture.py` / `s17_stamp_fixture.py` — historical FROZEN
--           witness records for their own generation (ADR-0005 Rule 8), not retro-edited; this delta's own
--           witness protocol (design/S21-SESSION-AWARE-DISTINCTNESS.md) is the s21-generation instance.
--         DEFECT-2 UNIVERSE (in-chain BEFORE-INSERT ledger functions, s19's own enumeration re-verified,
--         widened past "kernel-object resolution" to "own-schema resolution"):
--         * set_actor()    — already `SET search_path = :schema, :kern` (s19).      not in this class.
--         * set_stamp()    — reads via SECURITY DEFINER stamp_valid, already scoped. not in this class.
--         * validate_independence() — reads ONLY the ledger (own :schema); gains the SET clause here as
--           part of the same touch (already being replaced for defect 1; costs nothing extra to close).
--         * validate_enacts/review/amends/answers() — read ONLY the ledger, unqualified, resolved (per
--           s19's premise) by the role's LOGIN search_path — the exact premise defect 2 falsifies under
--           SET ROLE. FIXED here: all four gain `SET search_path = :"schema", pg_temp`.
--         * append_only()/one_row_per_insert() — read no relation by name (COUNT(*) FROM newrows is the
--           trigger transition table, resolved by REFERENCING, not search_path); verified NOT in this
--           class by inspection (grep + read, s15-schema.sql).
--       So defect 1's universe has exactly two DDL-coverable members (both fixed here) and one
--       Python-instrument member (found, named, filed — not silently left); defect 2's universe has
--       exactly four members (all fixed here), with set_actor/set_stamp already closed by s19 verified
--       unchanged.
--     - DENOMINATION: defect 1's identity is the (stamp_session, stamp_agent) PAIR, never a proxy for
--       it (never re-deriving distinctness from `actor`, `ts`, or any writer-supplied column) — a NULL
--       half is unrepresentable on a VERIFIED row (set_stamp writes both stamp_session and stamp_agent
--       together or neither) but the trigger/view still treat a NULL half as NOT distinct defensively,
--       fail-safe over relying on that invariant holding forever. Defect 2's fix is the RESOLUTION
--       MECHANISM itself (`SET search_path`), never a copied schema name or a session-level workaround —
--       exactly s19's own denomination, applied to the four functions s19 named but did not yet cover.
--
-- PARAMETERIZATION (db/harness/00N idiom; same vars/defaults as s15/s17/s19): schema/kern are psql
--   variables so this delta is VALIDATED on a throwaway substrate before any real apply. (No :role
--   variable is declared — this delta touches no GRANT; review_stamp_distinctness keeps its existing
--   grant across CREATE OR REPLACE VIEW, and the two new columns are additive.)
--     VALIDATE (reachable throwaway):
--        psql -h 192.168.122.1 -d harness -v schema=s21val -v kern=s21val_kernel \
--          -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql \
--          -f s19-trigger-search-path.sql -f s20-obligation-grants-and-view-refresh.sql \
--          -f s21-session-aware-distinctness.sql
--     REAL (owed to a maintainer-assented apply on a live deployment — NOT taken here; RATIFICATION
--     PENDING, per this file's own header — never apply bare, spell out every -v var explicitly):
--        psql -h 192.168.122.1 -d <db> -v schema=<schema> -v kern=<kern> \
--          -f s21-session-aware-distinctness.sql
--   This delta was authored and scratch-witnessed on a scratch schema pair in the TOY db only (schema
--   s21probe / s21probe_kernel, role s21probe_rw); see BACKLOG for the witness log and the exact toycolors
--   apply one-liner pending maintainer assent. NEVER applied to toycolors or any live schema by this pass.
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
-- DEFECT 1 — validate_independence(): distinctness on the (stamp_session, stamp_agent) PAIR,
-- NULL-half = not distinct (fail-safe). Also gains the defect-2 search_path clause (already being
-- replaced; costs nothing extra to close the same-generation gap here).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_independence() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE
  rev_session text; rev_agent text; rev_verified boolean; regards_id bigint;
  tgt_session text; tgt_agent text;
  distinct_pair boolean;
BEGIN
  IF NEW.independence IN ('technical','managerial','financial') THEN
    SELECT stamp_session, stamp_agent, stamp_verified, regards
      INTO rev_session, rev_agent, rev_verified, regards_id FROM ledger WHERE id = NEW.ledger_id;
    IF NOT COALESCE(rev_verified, false) THEN
      RAISE EXCEPTION 'Ledger policy: a review claiming independence (%) must carry a VERIFIED interception stamp — an unstamped review cannot establish it was a distinct invocation. Record independence=''self-review'' if you reviewed your own work, or write the review through a genuinely distinct stamped invocation (a separate agent).', NEW.independence;
    END IF;
    SELECT stamp_session, stamp_agent INTO tgt_session, tgt_agent FROM ledger WHERE id = regards_id;
    -- identity is the PAIR; a NULL half (on either row) is NEVER distinct — fail-safe, never fail-open.
    distinct_pair := (rev_session IS NOT NULL AND rev_agent IS NOT NULL
                       AND tgt_session IS NOT NULL AND tgt_agent IS NOT NULL)
                      AND (rev_session IS DISTINCT FROM tgt_session
                           OR rev_agent IS DISTINCT FROM tgt_agent);
    IF NOT distinct_pair THEN
      RAISE EXCEPTION 'Ledger policy: this review claims independence (%) but the SAME invocation (session=%, agent=%) wrote both it and the row it regards — one context cannot countersign its own work as independent (finding 31 / s21 session-aware distinctness). Record independence=''self-review'' if you reviewed your own work, or have a genuinely distinct invocation (a different session, or a different agent within this session) write the review.', NEW.independence, rev_session, rev_agent;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
-- this trigger's home table is review_detail (s17), unchanged here — the wiring below re-asserts the
-- identical FOR-EACH-ROW/BEFORE-INSERT shape s17 established, only the function body/header changed.
DROP TRIGGER IF EXISTS validate_independence ON :"schema".review_detail;
CREATE TRIGGER validate_independence BEFORE INSERT ON :"schema".review_detail
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_independence();

-- ============================================================================================
-- DEFECT 1 — review_stamp_distinctness: same_invocation recomputed on the PAIR. ADDITIVE: the two
-- existing stamp_agent columns and same_invocation/both_stamped stay in place and in order (so
-- CREATE OR REPLACE VIEW is legal and the existing GRANT survives unchanged); the two new
-- *_stamp_session columns are APPENDED, never inserted mid-list (s17_stamp_fixture.py item 6 reads
-- same_invocation unchanged; s20's view-refresh idiom applies here too — no bare `l.*`/`r.*`/`g.*`).
-- ============================================================================================
CREATE OR REPLACE VIEW :"schema".review_stamp_distinctness
    WITH (security_invoker = true) AS
SELECT r.id AS review_id, r.actor AS review_actor, r.stamp_agent AS review_stamp_agent,
       g.id AS regards_id, g.actor AS regards_actor, g.stamp_agent AS regards_stamp_agent,
       NOT (
         r.stamp_session IS NOT NULL AND r.stamp_agent IS NOT NULL
         AND g.stamp_session IS NOT NULL AND g.stamp_agent IS NOT NULL
         AND (r.stamp_session IS DISTINCT FROM g.stamp_session
              OR r.stamp_agent IS DISTINCT FROM g.stamp_agent)
       ) AS same_invocation,
       (r.stamp_verified AND g.stamp_verified) AS both_stamped,
       r.stamp_session AS review_stamp_session, g.stamp_session AS regards_stamp_session
FROM   :"schema".ledger r
JOIN   :"schema".ledger g ON g.id = r.regards
WHERE  r.kind = 'review';
-- GRANT is NOT re-issued: CREATE OR REPLACE VIEW preserves the relation's existing privileges (the oid is
-- unchanged) as long as the pre-existing columns keep their names/types/order, which this delta honors.

-- ============================================================================================
-- DEFECT 2 (fold-in) — the s19 residue: the four validate_* functions gain the per-function
-- SET search_path = :"schema", pg_temp carried by set_actor/set_stamp (s19), so a SET-ROLE session with
-- no explicit SET search_path resolves the ledger correctly (bodies UNCHANGED from s15 — only the
-- function header gains the SET clause, exactly the s19 idiom applied to set_actor).
-- ============================================================================================
CREATE OR REPLACE FUNCTION :"schema".validate_enacts() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE e bigint;
BEGIN
  IF NEW.enacts IS NOT NULL THEN
    FOREACH e IN ARRAY NEW.enacts LOOP
      IF NOT EXISTS (SELECT 1 FROM ledger d WHERE d.id = e AND d.session = NEW.session AND d.ts < NEW.ts) THEN
        RAISE EXCEPTION 'Ledger policy: enacts element % does not resolve to an earlier entry in this session.', e;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_enacts ON :"schema".ledger;
CREATE TRIGGER validate_enacts BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_enacts();

CREATE OR REPLACE FUNCTION :"schema".validate_review() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE target_actor bigint;
BEGIN
  IF NEW.kind = 'review' THEN
    IF NEW.regards IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: a review must name the row it regards.';
    END IF;
    SELECT l.actor INTO target_actor FROM ledger l WHERE l.id = NEW.regards AND l.id < NEW.id;
    IF target_actor IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: regards must resolve to an earlier row.';
    END IF;
    IF target_actor = NEW.actor THEN
      RAISE EXCEPTION 'Ledger policy: a row''s author may not countersign it (segregation of duties).';
    END IF;
  ELSIF NEW.regards IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: regards is reserved for kind=review.';
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_review ON :"schema".ledger;
CREATE TRIGGER validate_review BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_review();

CREATE OR REPLACE FUNCTION :"schema".validate_amends() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE t_statement text; t_rationale text;
BEGIN
  IF NEW.amends IS NOT NULL THEN
    IF NEW.amends_scope IS NULL OR btrim(NEW.amends_scope) = '' THEN
      RAISE EXCEPTION 'Ledger policy: an amends edge must name WHICH clause it defeats (amends_scope).';
    END IF;
    SELECT d.statement, coalesce(d.rationale,'') INTO t_statement, t_rationale
      FROM ledger d WHERE d.id = NEW.amends AND d.session = NEW.session AND d.id < NEW.id;
    IF t_statement IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: amends must resolve to an EARLIER own-session row.';
    END IF;
    IF NEW.supersedes IS NOT NULL AND NEW.supersedes = NEW.amends THEN
      RAISE EXCEPTION 'Ledger policy: a row may not both supersede and amends-defeat the same target.';
    END IF;
    IF length(btrim(NEW.amends_scope)) < 10 THEN
      RAISE EXCEPTION 'Ledger policy: amends_scope must quote the defeated clause (10+ characters).';
    END IF;
    IF position(NEW.amends_scope IN t_statement) = 0 AND position(NEW.amends_scope IN t_rationale) = 0 THEN
      RAISE EXCEPTION 'Ledger policy: amends_scope must be a VERBATIM quotation of the defeated clause from row %.', NEW.amends;
    END IF;
    IF ( (length(t_statement) - length(replace(t_statement, NEW.amends_scope, ''))) / length(NEW.amends_scope)
       + (length(t_rationale) - length(replace(t_rationale, NEW.amends_scope, ''))) / length(NEW.amends_scope)
       ) > 1 THEN
      RAISE EXCEPTION 'Ledger policy: amends_scope ''%'' occurs more than once — the referent is AMBIGUOUS. Extend the quotation.', NEW.amends_scope;
    END IF;
  ELSIF NEW.amends_scope IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: amends_scope is meaningless without an amends target.';
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_amends ON :"schema".ledger;
CREATE TRIGGER validate_amends BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_amends();

CREATE OR REPLACE FUNCTION :"schema".validate_answers() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
BEGIN
  IF NEW.answers IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM ledger d WHERE d.id = NEW.answers AND d.session = NEW.session AND d.id < NEW.id) THEN
      RAISE EXCEPTION 'Ledger policy: answers must resolve to an EARLIER own-session row.';
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_answers ON :"schema".ledger;
CREATE TRIGGER validate_answers BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_answers();
