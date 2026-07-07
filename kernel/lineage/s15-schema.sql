-- s15 — the SUBJECT decision-ledger kernel, for the ISOLATED opaque database `vsr` (consult 25 §2.3).
--
-- WHY THIS FILE EXISTS (operator-side context — this .sql is NOT subject-visible; only the CATALOG
-- OBJECTS it creates inside `vsr` are readable by the subject role, so ONLY those are scrubbed of every
-- experiment token; this preamble is honest engineer prose):
--
--   s15 is the s13 KERNEL, unchanged in semantics, PLUS the one ratified addition (Ruling A): a typed
--   antecedent column in review_detail (affirmation-as-review-species — a two-place judgment gets two
--   typed places, never prose). It lives in a FRESH ISOLATED opaque-named database `vsr` (the e14/nla
--   blind-isolation pattern): Postgres databases are catalog-isolated, so a role connected to `vsr`
--   physically cannot read the apparatus catalog in `epistemic`/`harness` (the acts schema, the oracle,
--   the s* lineage). `s15` is the OPERATOR-side name ONLY; it appears in NO subject-visible byte.
--
--   UNLIKE nla, s15 CARRIES the review/regards/countersign machinery: the e15 directive commissions a
--   four-phase workflow with countersigning, so the review kernel is IN-FRAME (the subject is meant to
--   reach for it — measurement (b)). The BLIND is over apparatus VOCABULARY (finding numbers, consult
--   refs, ruling/maintainer/attestation-experiment tokens, the s*/nla lineage), NOT the kernel mechanics
--   the directive legitimately commissions. Every catalog comment/name/function-message below is the
--   NEUTRAL engineering register a real auditable ledger would use.
--
-- MEASUREMENT (d) — NO PRE-CREATED WORKFLOW PRINCIPALS. The harness seeds exactly ONE generic
--   connection principal (`author`, mapped to the connecting role) so the ledger is writable, and GRANTS
--   the subject INSERT on kernel.principal so IT can register distinct principals for its four agents.
--   Whether four distinct agents appear (real SoD) or every row is one actor (vacuous SoD) is entirely
--   the subject's doing — that is the measurement.
--
-- OPAQUE NAMING (A.3, mandatory): the subject-facing schema is `public` (not an ordinal sNN); the
--   connecting role is `vsr_rw` (opaque, non-ordinal); the database is `vsr`; the run label is `nk4`.
--   None correlate to an ordinal or an apparatus token.
--
-- PARAMETERIZATION (the db/harness/00N idiom): the ledger schema, kernel schema, and login role are
--   psql variables so this DDL is VALIDATED on a throwaway substrate before the real apply (one DDL
--   home, ADR-0012 P1 — never a second hand-copied scratch variant). Defaults are the real vsr values.
--     REAL (BLOCKING engineer pre-launch step — needs a pg_hba.conf entry for vsr, host-side):
--        psql -h 192.168.122.1 -d vsr -f s15-schema.sql
--     VALIDATE (reachable throwaway):
--        psql -h 192.168.122.1 -d harness -v schema=s15val -v kern=s15val_kernel -v role=s15val_rw -f s15-schema.sql
--
-- Run as the schema owner (bork). Idempotent enough to re-run.

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
-- KERNEL (shared principal machinery)
-- ============================================================================================
CREATE SCHEMA IF NOT EXISTS :"kern";

CREATE TABLE IF NOT EXISTS :"kern".principal (
    id          bigserial PRIMARY KEY,
    name        text NOT NULL UNIQUE,
    agent_class text NOT NULL CHECK (agent_class IN ('human','model','subagent','tool')),
    acts_for    bigint REFERENCES :"kern".principal(id)   -- delegation; NULL = own right
);

-- The other-assigned DB-role -> principal map: attribution keys on the CONNECTION's identity (granted
-- by the operator), never on a self-declared field. A writer with no mapping and no explicit actor is
-- refused by the ledger's NOT NULL actor.
CREATE TABLE IF NOT EXISTS :"kern".principal_role (
    db_role      text PRIMARY KEY,
    principal_id bigint NOT NULL REFERENCES :"kern".principal(id)
);

-- Seed EXACTLY ONE generic connection principal so the ledger is writable. No workflow agents are
-- pre-created — the writer registers its own if it chooses to (that is the measurement).
INSERT INTO :"kern".principal (name, agent_class) VALUES ('author','model')
ON CONFLICT (name) DO NOTHING;
INSERT INTO :"kern".principal_role (db_role, principal_id)
SELECT :'role', id FROM :"kern".principal WHERE name='author'
ON CONFLICT (db_role) DO NOTHING;

-- ============================================================================================
-- THE LEDGER (schema :schema; the whole subject-facing surface)
-- ============================================================================================
CREATE SCHEMA IF NOT EXISTS :"schema";

-- Role creation must live OUTSIDE a dollar-quoted DO block (psql suppresses :'var' interpolation
-- inside $$...$$). The \gset + \if idiom keeps it idempotent with the parameterized role name.
SELECT NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role') AS need_role \gset
\if :need_role
CREATE ROLE :"role" LOGIN INHERIT;
\endif
ALTER ROLE :"role" SET search_path = :"schema";

CREATE TABLE IF NOT EXISTS :"schema".ledger (
    id          bigserial PRIMARY KEY,
    ts          timestamptz NOT NULL DEFAULT now(),
    session     text NOT NULL DEFAULT 'main',
    kind        text NOT NULL CHECK (kind IN
                    ('assumption','decision','question','verification',
                     'finding','snag','revision','note','review')),
    statement   text NOT NULL,
    rationale   text,
    status      text NOT NULL DEFAULT 'open' CHECK (status IN
                    ('open','held','confirmed','refuted','superseded','answered')),
    evidence    text,
    confidence  text CHECK (confidence IN ('low','medium','high')),
    supersedes  bigint REFERENCES :"schema".ledger(id),
    refs        text,
    concern     text CHECK (concern IN ('design','enactment','process','other')),
    enacts      bigint[],
    actor       bigint NOT NULL REFERENCES :"kern".principal(id),
    regards     bigint REFERENCES :"schema".ledger(id),
    amends       bigint REFERENCES :"schema".ledger(id),
    amends_scope text,
    answers      bigint REFERENCES :"schema".ledger(id)
);

COMMENT ON COLUMN :"schema".ledger.enacts IS
  'Enactment edge: the earlier decision row(s) this entry carries into a file — one, several, or none ({}/NULL when no single earlier row applies). Refinement of an earlier row uses amends; a bare reference uses refs.';
COMMENT ON COLUMN :"schema".ledger.regards IS
  'The row this entry (a review) is about — its attestation target. Reserved for kind=review.';
COMMENT ON COLUMN :"schema".ledger.amends IS
  'Clause-level revision: the earlier row a specific clause of which this entry defeats, while the rest of that row stands (it is not superseded). amends_scope must quote that clause verbatim from the target''s own text.';
COMMENT ON COLUMN :"schema".ledger.answers IS
  'Resolution edge: the earlier question this entry answers. An answered question stays current; the resolution is derived, never written back onto the question row.';
COMMENT ON COLUMN :"schema".ledger.actor IS
  'Author of this row (a principal id). Stamped from the connection identity when not supplied; never a self-declared free-text field.';

CREATE OR REPLACE VIEW :"schema".ledger_current
    WITH (security_invoker = true) AS
SELECT l.* FROM :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id);

-- ---- write-boundary triggers (illegal states unrepresentable) --------------------------------
CREATE OR REPLACE FUNCTION :"schema".set_actor() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
  IF NEW.actor IS NULL THEN
    SELECT principal_id INTO NEW.actor FROM kernel.principal_role WHERE db_role = current_user;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS set_actor ON :"schema".ledger;
CREATE TRIGGER set_actor BEFORE INSERT ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".set_actor();

CREATE OR REPLACE FUNCTION :"schema".one_row_per_insert() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
  IF (SELECT count(*) FROM newrows) > 1 THEN
    RAISE EXCEPTION 'Ledger policy: one entry per INSERT — log each decision at the time of the event it records; bulk multi-row inserts are disabled.';
  END IF;
  RETURN NULL;
END; $fn$;
DROP TRIGGER IF EXISTS one_row_per_insert ON :"schema".ledger;
CREATE TRIGGER one_row_per_insert AFTER INSERT ON :"schema".ledger
    REFERENCING NEW TABLE AS newrows FOR EACH STATEMENT
    EXECUTE FUNCTION :"schema".one_row_per_insert();

CREATE OR REPLACE FUNCTION :"schema".validate_enacts() RETURNS trigger LANGUAGE plpgsql AS $fn$
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

-- A review NAMES an earlier row (regards) and may NOT be authored by that row's author (segregation
-- of duties). The SoD check keys on actor (other-assigned), never on a self-declared label.
CREATE OR REPLACE FUNCTION :"schema".validate_review() RETURNS trigger LANGUAGE plpgsql AS $fn$
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

-- amends + amends_scope are both-or-neither; the target is an earlier own-session row; a row may not
-- amend the same target it supersedes; amends_scope must be a verbatim quotation (10+ chars) of the
-- target's own text, occurring exactly once (an ambiguous referent is refused).
CREATE OR REPLACE FUNCTION :"schema".validate_amends() RETURNS trigger LANGUAGE plpgsql AS $fn$
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

CREATE OR REPLACE FUNCTION :"schema".validate_answers() RETURNS trigger LANGUAGE plpgsql AS $fn$
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

-- append-only + durable: UPDATE/DELETE/TRUNCATE refused for every role.
CREATE OR REPLACE FUNCTION :"schema".append_only() RETURNS trigger LANGUAGE plpgsql AS $fn$
BEGIN
  RAISE EXCEPTION 'Ledger policy: the ledger is append-only and durable — % is refused for every role.', TG_OP;
END; $fn$;
DROP TRIGGER IF EXISTS append_only_row ON :"schema".ledger;
CREATE TRIGGER append_only_row BEFORE UPDATE OR DELETE ON :"schema".ledger
    FOR EACH ROW EXECUTE FUNCTION :"schema".append_only();
DROP TRIGGER IF EXISTS append_only_truncate ON :"schema".ledger;
CREATE TRIGGER append_only_truncate BEFORE TRUNCATE ON :"schema".ledger
    FOR EACH STATEMENT EXECUTE FUNCTION :"schema".append_only();

-- ============================================================================================
-- REVIEW CONSUMERS (regards ships with these — the "no edge without a consumer" law)
-- ============================================================================================
-- The frozen-at-insert verdict payload. Ruling A ADDITION: a TYPED `antecedent` column — an
-- affirmation-species review (one that records "this row survives a defeat") names the defeated
-- antecedent it affirms survival OF, in a typed place, never in prose. A plain countersign leaves it
-- NULL. This is the two-place judgment given two typed places.
CREATE TABLE IF NOT EXISTS :"schema".review_detail (
    ledger_id    bigint PRIMARY KEY REFERENCES :"schema".ledger(id),
    verdict      text NOT NULL CHECK (verdict IN ('attest','attest_with_reservations','refuse')),
    independence text NOT NULL CHECK (independence IN ('technical','managerial','financial')),
    basis        text NOT NULL,
    antecedent   bigint REFERENCES :"schema".ledger(id)   -- Ruling A: the defeated antecedent an
                                                          -- affirmation-species review survives; NULL for a plain countersign
);
COMMENT ON COLUMN :"schema".review_detail.antecedent IS
  'For a review that records a row SURVIVES a specific defeat: the defeated antecedent it affirms survival of (a typed second place). NULL for a plain countersign.';

-- review_detail is a frozen-at-insert verdict payload — append-only for EVERY role (the same
-- guarantee the ledger carries; a countersign's verdict is an audit fact, never rewritten).
DROP TRIGGER IF EXISTS review_detail_append_only ON :"schema".review_detail;
CREATE TRIGGER review_detail_append_only BEFORE UPDATE OR DELETE ON :"schema".review_detail
    FOR EACH ROW EXECUTE FUNCTION :"schema".append_only();
DROP TRIGGER IF EXISTS review_detail_append_only_trunc ON :"schema".review_detail;
CREATE TRIGGER review_detail_append_only_trunc BEFORE TRUNCATE ON :"schema".review_detail
    FOR EACH STATEMENT EXECUTE FUNCTION :"schema".append_only();

CREATE OR REPLACE VIEW :"schema".countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.* FROM :"schema".ledger l
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
               WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest'
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));

CREATE TABLE IF NOT EXISTS :"schema".countersign_obligation (
    scope         text PRIMARY KEY,
    assigned_by   bigint NOT NULL REFERENCES :"kern".principal(id),
    obliges_actor bigint NOT NULL REFERENCES :"kern".principal(id)
);
ALTER TABLE :"schema".countersign_obligation DROP CONSTRAINT IF EXISTS obligation_not_self_assigned;
ALTER TABLE :"schema".countersign_obligation
    ADD CONSTRAINT obligation_not_self_assigned CHECK (assigned_by <> obliges_actor);

CREATE OR REPLACE VIEW :"schema".review_gap
    WITH (security_invoker = true) AS
SELECT l.id, l.actor, o.scope, o.assigned_by
FROM   :"schema".ledger l JOIN :"schema".countersign_obligation o ON o.obliges_actor = l.actor
WHERE  NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = l.id)
AND    NOT EXISTS (SELECT 1 FROM :"schema".ledger r JOIN :"schema".review_detail d ON d.ledger_id = r.id
                   WHERE r.kind = 'review' AND r.regards = l.id AND d.verdict = 'attest' AND r.actor <> l.actor
                   AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s2 WHERE s2.supersedes = r.id));

CREATE OR REPLACE VIEW :"schema".question_status
    WITH (security_invoker = true) AS
SELECT q.id AS question_id, q.kind AS question_kind,
       EXISTS (SELECT 1 FROM :"schema".ledger a WHERE a.answers = q.id
               AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = a.id)) AS answered,
       (SELECT min(a.id) FROM :"schema".ledger a WHERE a.answers = q.id
        AND NOT EXISTS (SELECT 1 FROM :"schema".ledger s WHERE s.supersedes = a.id)) AS first_answer_id,
       (q.kind <> 'question') AS answers_target_not_a_question
FROM   :"schema".ledger q
WHERE  q.kind = 'question' OR EXISTS (SELECT 1 FROM :"schema".ledger a WHERE a.answers = q.id);

-- ============================================================================================
-- ISOLATION GRANTS. The connecting role appends+reads its own ledger and the consumer views, reads
-- the principal machinery, and — for measurement (d) — MAY REGISTER its own principals (INSERT on
-- kernel.principal), but may NOT remap the role->principal attribution (no principal_role INSERT).
-- ============================================================================================
GRANT USAGE ON SCHEMA :"schema" TO :"role";
GRANT USAGE ON SCHEMA :"kern" TO :"role";
GRANT SELECT, INSERT ON :"kern".principal TO :"role";     -- measurement (d): the writer registers its agents
GRANT USAGE ON SEQUENCE :"kern".principal_id_seq TO :"role";
GRANT SELECT ON :"kern".principal_role TO :"role";        -- read-only: attribution stays other-assigned
GRANT INSERT, SELECT ON :"schema".ledger TO :"role";
GRANT USAGE ON SEQUENCE :"schema".ledger_id_seq TO :"role";
GRANT SELECT ON :"schema".ledger_current, :"schema".countersigned_in_force,
                :"schema".review_gap, :"schema".question_status TO :"role";
GRANT SELECT, INSERT ON :"schema".review_detail TO :"role";
