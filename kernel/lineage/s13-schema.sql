-- e13 / s13 kernel migration — the codification arm (consult 17 §6, link-18 build).
--
-- This is NOT a subject run. It is the schema the vocabulary-misfit deferrals (whose re-entry
-- conditions have all fired) are codified into, plus the actor axis the record has needed since
-- the phantom "operator ruling" of s10. The new kernel lives in a NEW session-era lineage (s13+):
-- historical schemas s1..s12 are CLOSED EVIDENCE and are NEVER migrated in place (append-only
-- applies to the apparatus too — consult 17 §6, link-18 brief). Run as the schema owner (bork).
-- Idempotent enough to re-run before a probe.
--
-- WHAT IS BYTE-HELD FROM s12 (comparability): the ledger's physical shape (bigserial id, ts,
-- session, kind CHECK, statement/rationale/status/evidence/confidence, supersedes self-FK, refs,
-- concern CHECK, enacts bigint[] multi-target with its per-element validation trigger), the
-- security_invoker current view, the one-row-per-INSERT backstop, the F29 role-level search_path
-- pin, and the isolation-grant shape.
--
-- WHAT IS NEW IN e13 (each edge ships WITH its consumer(s) — the "no edge type no consumer
-- consumes" law, consult 15/16, external clause 8):
--
--   1. ACTOR AXIS (external clause 1/6, consult 17 §6.1; the record's first-needed-at-row-29 axis):
--      kernel.principal (shared across the s13+ lineage and all domain profiles) + a NOT NULL
--      `actor` on the ledger, attributed by the CONNECTING DB ROLE (label-indifferent, F33/F26:
--      the writer's identity is what the connection IS, other-assigned by whoever granted the
--      role — never a self-declared field). `acts_for` is the delegation self-reference, nullable
--      with a documented honest-NULL ("NULL = own right"); delegation-depth semantics are left
--      UNDECIDED here (external clause 10) — the column represents the relation, it does not decide
--      independence inheritance. That is the delegation arm's call when it first needs it.
--
--   2. REVIEW SPEECH ACT (external clauses 2/6): kind='review' (the vocabulary grows by this ONE
--      kind — the sketch's assumption/finding/revision/snag additions are DROPPED as unconsumed,
--      the fabricated-category move ADR-0008's negative register forbids) + a single-target
--      `regards` self-FK (the attestation edge) + a frozen-at-insert verdict payload
--      (s13.review_detail). validate_review is keyed on `id` order, NOT `ts` (consult 17 §5.3
--      correction: s12 has 41ms and same-second ts neighbours; id is the sound order for a
--      single-sequence append-only table). Consumers: s13.countersigned_in_force (the profile
--      compliance closure) + s13.review_gap (the gap detector feeding the review queue).
--
--   3. CLAUSE-LEVEL DEFEAT / amends (F44, the aspectual gap's third-and-forced instance): a typed
--      single-target `amends` self-FK with a MANDATORY `amends_scope` that VERBATIM-QUOTES the defeated
--      clause from the target's own text (trigger-checked). This is the vocabulary between
--      "whole-row supersede" and "silence"
--      that row 5-vs-29 needed and could not reach. Consumers: soundness (clause-level-defeat
--      readout) + stale_enactment_debt (antecedent-clause staleness). SHAPE DECISION + rationale +
--      the loud-flag on its one design smell are in the build consult (consult 18 §amends).
--
--   4. RESOLUTION AXIS / answers (B-axis, row 30): a dedicated single-target `answers` self-FK
--      (answer -> question), DISTINCT from supersedes-as-replacement. An answered question is a
--      CURRENT fact (asked and answered), not a REPLACED one, so it must survive in the current
--      view — which the supersedes overload wrongly evicted. Consumer: s13.question_status (the
--      resolution closure) + the review queue. No auto-resolve (F28): status is frozen at insert;
--      "answered" is DERIVED, never written back onto the question row.
--
--   5. enacts DEFINED to ticket-only semantics (consult 17 §6 item 4; F39): the column comment
--      below is the single documented meaning (the 3-subject convergent use). Refinement-of-a-
--      design now has `amends`; bare reference has `refs`; DISCHARGE stays deliberately undefined
--      (2-for-1-against — defining it now would fabricate a convention, ADR-0008).
--
-- The gate matcher (event-61 repair, F45), the observed-currency instrument (F42), and the
-- operator-touchpoint repair (F40) are separate artifacts in this build dir; the soundness /
-- stale_enactment_debt consumers for amends live in the shared instruments (session-generic,
-- amends-aware only where the column exists).

-- ============================================================================================
-- KERNEL (one definition, shared across the s13+ lineage and every domain profile)
-- ============================================================================================
CREATE SCHEMA IF NOT EXISTS kernel;

CREATE TABLE IF NOT EXISTS kernel.principal (
    id          bigserial PRIMARY KEY,
    name        text NOT NULL UNIQUE,          -- the principal's stable name
    agent_class text NOT NULL CHECK (agent_class IN ('human','model','subagent','tool')),
    acts_for    bigint REFERENCES kernel.principal(id)   -- delegation; NULL = own right (honest-NULL)
);

-- The other-assigned DB-role -> principal map (F33/F26 label-indifference: attribution keys on the
-- CONNECTION's identity, granted by the operator, never on a subject-authored field). A writer with
-- no mapping and no explicit actor is refused by the ledger's NOT NULL actor (ADR-0002 fail-loud:
-- an unattributable writer cannot touch the sovereign repository).
CREATE TABLE IF NOT EXISTS kernel.principal_role (
    db_role      text PRIMARY KEY,             -- a Postgres role name (current_user)
    principal_id bigint NOT NULL REFERENCES kernel.principal(id)
);

-- Seed the three principals the record already needs (AC2). subject=model; operator/engineer=human.
INSERT INTO kernel.principal (name, agent_class) VALUES
    ('subject','model'), ('operator','human'), ('engineer','human')
ON CONFLICT (name) DO NOTHING;

-- Role map: the isolated subject role attributes to `subject`; the schema owner (bork), used for
-- engineer-run apparatus rows (e.g. waiver rows), attributes to `engineer`. The operator, when it
-- ever writes, connects under its own granted role (added when the delegation arm needs it).
INSERT INTO kernel.principal_role (db_role, principal_id)
SELECT 'led_s13', id FROM kernel.principal WHERE name='subject'
ON CONFLICT (db_role) DO NOTHING;
INSERT INTO kernel.principal_role (db_role, principal_id)
SELECT 'bork', id FROM kernel.principal WHERE name='engineer'
ON CONFLICT (db_role) DO NOTHING;

-- ============================================================================================
-- SESSION SCHEMA s13 (the codification-arm scratch/probe schema; e14 gets its own s14 in this
-- same kernel lineage — fresh session schemas are never historical migrations)
-- ============================================================================================
CREATE SCHEMA IF NOT EXISTS s13;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'led_s13') THEN
    CREATE ROLE led_s13 LOGIN INHERIT;
  END IF;
END $$;

-- F29: role-level search_path pin (the setting led_s10 was missing; the omission that manufactured
-- the e9 opening spiral). Idempotent.
ALTER ROLE led_s13 SET search_path = s13;

CREATE TABLE IF NOT EXISTS s13.ledger (
    id          bigserial PRIMARY KEY,
    ts          timestamptz NOT NULL DEFAULT now(),
    session     text NOT NULL DEFAULT 's13',
    kind        text NOT NULL CHECK (kind IN
                    ('assumption','decision','question','verification',
                     'finding','snag','revision','note','review')),   -- grows by 'review' ONLY
    statement   text NOT NULL,
    rationale   text,
    status      text NOT NULL DEFAULT 'open' CHECK (status IN
                    ('open','held','confirmed','refuted','superseded','answered')),
    evidence    text,
    confidence  text CHECK (confidence IN ('low','medium','high')),
    supersedes  bigint REFERENCES s13.ledger(id),   -- whole-row replacement (unchanged; comparability)
    refs        text,
    concern     text CHECK (concern IN ('design','enactment','process','other')),
    -- enacts: THE ENACTMENT-TICKET edge. Single documented meaning (F39, consult 17 item 4): "this
    -- row is the ticket carrying its design antecedent(s) into files." Multi-target bigint[] with a
    -- documented honest-empty ({}/NULL = no single design antecedent applies). Refinement-of-a-
    -- design is `amends`, not enacts; bare reference is `refs`; discharge is undefined.
    enacts      bigint[],
    -- actor: WHO authored this row. NOT NULL — the sovereign repository refuses an unattributable
    -- writer (ADR-0002). Attributed from the connecting DB role by set_actor() when not supplied.
    actor       bigint NOT NULL REFERENCES kernel.principal(id),
    -- regards: the attestation target of a kind='review' row (single-target; external clause 2).
    regards     bigint REFERENCES s13.ledger(id),
    -- amends + amends_scope: clause-level (aspectual) defeat (F44). amends names the earlier row a
    -- specific clause of which this row defeats; amends_scope names WHICH clause. Both-or-neither
    -- (validate_amends). This is NOT supersession: the target stays in force as a row.
    amends       bigint REFERENCES s13.ledger(id),
    amends_scope text,
    -- answers: the resolution edge (B-axis, row 30). Names the earlier question this row answers.
    -- DISTINCT from supersedes: an answered question is current, not replaced (see question_status).
    answers      bigint REFERENCES s13.ledger(id)
);

COMMENT ON COLUMN s13.ledger.enacts IS
  'Enactment-ticket edge (single documented meaning, F39): design antecedent(s) this row carries into files. {}/NULL = honest-empty. Refinement uses amends; reference uses refs; discharge is undefined.';
COMMENT ON COLUMN s13.ledger.amends IS
  'Clause-level defeat (F44): the earlier row a specific clause of which this row defeats. Requires amends_scope = a VERBATIM quotation (10+ chars) of the defeated clause from the target''s statement/rationale (maintainer ruling 2026-07-06). NOT supersession — the target remains in force as a row.';
COMMENT ON COLUMN s13.ledger.answers IS
  'Resolution edge (B-axis): the earlier question this row answers. Distinct from supersedes; an answered question stays current. No auto-resolve — answered is derived, never written back.';

-- Current view: not whole-row-superseded. Byte-held from s12 (an answered question is NOT
-- superseded, so it correctly survives here — the fix the B-axis overload needed).
CREATE OR REPLACE VIEW s13.ledger_current
    WITH (security_invoker = true) AS
SELECT l.*
FROM   s13.ledger l
WHERE  NOT EXISTS (SELECT 1 FROM s13.ledger s WHERE s.supersedes = l.id);

-- ---- write-boundary triggers (illegal states unrepresentable — ADR-0000/0012) ---------------

-- (a) actor attribution from the connecting role, when not explicitly supplied.
CREATE OR REPLACE FUNCTION s13.set_actor() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  IF NEW.actor IS NULL THEN
    SELECT principal_id INTO NEW.actor FROM kernel.principal_role WHERE db_role = current_user;
    -- NULL stays NULL -> the NOT NULL constraint fails loudly for an unmapped writer.
  END IF;
  RETURN NEW;
END;
$fn$;
DROP TRIGGER IF EXISTS set_actor ON s13.ledger;
CREATE TRIGGER set_actor BEFORE INSERT ON s13.ledger
    FOR EACH ROW EXECUTE FUNCTION s13.set_actor();

-- (b) one entry per INSERT (mirrors s12 verbatim — log each event at its time).
CREATE OR REPLACE FUNCTION s13.one_row_per_insert() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  IF (SELECT count(*) FROM newrows) > 1 THEN
    RAISE EXCEPTION 'Ledger policy: one entry per INSERT — log each decision at the time of the event it records; bulk multi-row inserts are disabled.';
  END IF;
  RETURN NULL;
END;
$fn$;
DROP TRIGGER IF EXISTS one_row_per_insert ON s13.ledger;
CREATE TRIGGER one_row_per_insert AFTER INSERT ON s13.ledger
    REFERENCING NEW TABLE AS newrows
    FOR EACH STATEMENT EXECUTE FUNCTION s13.one_row_per_insert();

-- (c) per-element enacts validation (byte-held from s12: each element an earlier own-session row).
CREATE OR REPLACE FUNCTION s13.validate_enacts() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
DECLARE e bigint;
BEGIN
  IF NEW.enacts IS NOT NULL THEN
    FOREACH e IN ARRAY NEW.enacts LOOP
      IF NOT EXISTS (SELECT 1 FROM s13.ledger d
                     WHERE d.id = e AND d.session = NEW.session AND d.ts < NEW.ts) THEN
        RAISE EXCEPTION 'Ledger policy: enacts element % does not resolve to an earlier entry in this session — each enacts id must name an EARLIER own-session row; leave enacts empty when no single design row applies.', e;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END;
$fn$;
DROP TRIGGER IF EXISTS validate_enacts ON s13.ledger;
CREATE TRIGGER validate_enacts BEFORE INSERT ON s13.ledger
    FOR EACH ROW EXECUTE FUNCTION s13.validate_enacts();

-- (d) validate_review (external clause 6, consult 17 §5.3 correction — keyed on id, not ts).
-- A review NAMES an earlier row (regards) and may NOT be authored by that row's author
-- (segregation of duties, I6). regards is reserved for kind='review'. NB: the target's KIND is
-- NOT checked here — a review may regard any earlier row, and gating on the target's self-declared
-- kind would price a label (F26). The SoD check keys on `actor` (other-assigned), never a label.
CREATE OR REPLACE FUNCTION s13.validate_review() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
DECLARE target_actor bigint;
BEGIN
  IF NEW.kind = 'review' THEN
    IF NEW.regards IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: a review must name the row it regards.';
    END IF;
    SELECT l.actor INTO target_actor
      FROM s13.ledger l WHERE l.id = NEW.regards AND l.id < NEW.id;
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
END;
$fn$;
DROP TRIGGER IF EXISTS validate_review ON s13.ledger;
CREATE TRIGGER validate_review BEFORE INSERT ON s13.ledger
    FOR EACH ROW EXECUTE FUNCTION s13.validate_review();

-- (e) validate_amends (F44): amends and amends_scope are both-or-neither; the target is an earlier
-- own-session row; a row may not amend the same target it supersedes (whole-row + clause defeat of
-- one row is a category error). The target's KIND is NOT checked (label-indifference, F26) — a
-- non-decision amends target is a REVIEW-QUEUE flag in soundness, never a write-boundary denial.
--
-- SCOPE IS A QUOTATION, NOT PROSE (maintainer ruling 2026-07-06 on the link-18 loud flag; the
-- structural middle between free text and a sub-row clause model): amends_scope must be a VERBATIM
-- substring of the target row's statement or rationale — the defeated clause, quoted. This makes a
-- vacuous or misdirected scope UNREPRESENTABLE at the write boundary (ADR-0000: the type that
-- forecloses the class) with no change to any prior write contract (amends is new to the s13+
-- lineage). Append-only makes the quotation binding: the target text can never change under it —
-- the same version-binding property the review attestation gets for free. Commentary ("...the
-- architecture stands") is NOT scope; it belongs in the citing row's rationale — one field, one
-- meaning. MIN_SCOPE floor: a quotation shorter than 10 chars is refused (a stopword quotation like
-- 'the' satisfies substring vacuously; the floor prices that out — a heuristic backstop under the
-- structural rule, named here per ADR-0012 F). Re-entry condition (named, filed): the first
-- defeated clause that genuinely cannot be expressed as one contiguous quotation (e.g. an
-- implication spread across sentences) escalates to the typed sub-row clause model — it is not
-- worked around with a paraphrase.
CREATE OR REPLACE FUNCTION s13.validate_amends() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
DECLARE t_statement text; t_rationale text;
BEGIN
  IF NEW.amends IS NOT NULL THEN
    IF NEW.amends_scope IS NULL OR btrim(NEW.amends_scope) = '' THEN
      RAISE EXCEPTION 'Ledger policy: an amends edge must name WHICH clause it defeats (amends_scope) — a scopeless amends is indistinguishable from a supersede.';
    END IF;
    SELECT d.statement, coalesce(d.rationale,'') INTO t_statement, t_rationale
      FROM s13.ledger d
      WHERE d.id = NEW.amends AND d.session = NEW.session AND d.id < NEW.id;
    IF t_statement IS NULL THEN
      RAISE EXCEPTION 'Ledger policy: amends must resolve to an EARLIER own-session row.';
    END IF;
    IF NEW.supersedes IS NOT NULL AND NEW.supersedes = NEW.amends THEN
      RAISE EXCEPTION 'Ledger policy: a row may not both supersede and amends-defeat the same target (whole-row and clause defeat of one row is a category error).';
    END IF;
    IF length(btrim(NEW.amends_scope)) < 10 THEN
      RAISE EXCEPTION 'Ledger policy: amends_scope must quote the defeated clause (10+ characters of the target row''s own text) — a fragment shorter than a clause cannot identify one.';
    END IF;
    IF position(NEW.amends_scope IN t_statement) = 0
       AND position(NEW.amends_scope IN t_rationale) = 0 THEN
      RAISE EXCEPTION 'Ledger policy: amends_scope must be a VERBATIM quotation of the defeated clause from row %''s statement or rationale — quote the exact text the new row defeats; commentary belongs in rationale.', NEW.amends;
    END IF;
  ELSIF NEW.amends_scope IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: amends_scope is meaningless without an amends target.';
  END IF;
  RETURN NEW;
END;
$fn$;
DROP TRIGGER IF EXISTS validate_amends ON s13.ledger;
CREATE TRIGGER validate_amends BEFORE INSERT ON s13.ledger
    FOR EACH ROW EXECUTE FUNCTION s13.validate_amends();

-- (f) validate_answers (B-axis): answers resolves to an earlier own-session row. The target's KIND
-- (question) is NOT enforced here (label-indifference, F26) — an answers-target-not-a-question is a
-- question_status/review-queue flag, never a denial (the alias_surface precedent for enacts).
CREATE OR REPLACE FUNCTION s13.validate_answers() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  IF NEW.answers IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM s13.ledger d
                   WHERE d.id = NEW.answers AND d.session = NEW.session AND d.id < NEW.id) THEN
      RAISE EXCEPTION 'Ledger policy: answers must resolve to an EARLIER own-session row.';
    END IF;
  END IF;
  RETURN NEW;
END;
$fn$;
DROP TRIGGER IF EXISTS validate_answers ON s13.ledger;
CREATE TRIGGER validate_answers BEFORE INSERT ON s13.ledger
    FOR EACH ROW EXECUTE FUNCTION s13.validate_answers();

-- BEGIN LINEAGE-ONLY (append-only protection — the ONE section the probe-mirror derivation strips;
-- a scratch mirror is reset at will, the lineage ledger never; see run-acceptance.sh)
-- (g) APPEND-ONLY PROTECTION (engineer-verification repair, 2026-07-06): the lineage ledger is
-- DURABLE — UPDATE, DELETE, and TRUNCATE are refused AT THE WRITE BOUNDARY, for every role
-- including the owner's own apparatus scripts. The defect this forecloses (ADR-0000: the type that
-- makes the class unrepresentable): s13 doubled as a scratch probe schema (TRUNCATE-for-idempotence)
-- and as the durable home of the ratified waiver rows, so whichever probe ran last silently wiped
-- the escape-hatch rows the ratification requires to BE ledger rows. The category error is split
-- structurally: probes run on a sed-derived scratch mirror (s13probe — no protection triggers,
-- reset at will, see run-acceptance.sh); the lineage ledger carries NO truncation path at all.
-- s14+ INHERIT these triggers with the schema: the TRUNCATE-for-idempotence pattern is BANNED in
-- the kernel lineage — a probe that needs a reset derives a mirror, never touches the lineage
-- ledger. (The owner can still DROP the triggers by hand; the invariant is that no APPARATUS code
-- path can — every script in this repo hits the refusal.)
CREATE OR REPLACE FUNCTION s13.append_only() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  RAISE EXCEPTION 'Ledger policy: the lineage ledger is append-only and durable — % is refused for every role. Probes run on the scratch mirror (s13probe), never here.', TG_OP;
END;
$fn$;
DROP TRIGGER IF EXISTS append_only_row ON s13.ledger;
CREATE TRIGGER append_only_row
    BEFORE UPDATE OR DELETE ON s13.ledger
    FOR EACH ROW EXECUTE FUNCTION s13.append_only();
DROP TRIGGER IF EXISTS append_only_truncate ON s13.ledger;
CREATE TRIGGER append_only_truncate
    BEFORE TRUNCATE ON s13.ledger
    FOR EACH STATEMENT EXECUTE FUNCTION s13.append_only();
-- END LINEAGE-ONLY

-- ============================================================================================
-- REVIEW CONSUMERS (regards ships with these — the "no edge without a consumer" law)
-- ============================================================================================

-- Frozen-at-insert verdict payload (external clause 3/6: an attestation binds to an immutable
-- record version; the meaning — author/reviewer/approver — is explicit per Part 11 §11.50/.70/G9).
-- Keyed 1:1 to a kind='review' ledger row. verdict {attest, attest_with_reservations, refuse} makes
-- refusal-to-sign a first-class outcome (I4/G7). This is the harness's own domain profile side-table
-- (the sketch's `nrc.` is one example domain; the harness is the domain here) — a TYPED SIDE-TABLE,
-- never a nullable kernel column (external clause 7: NULL must not be ambiguous between
-- not-applicable and required-and-missing).
CREATE TABLE IF NOT EXISTS s13.review_detail (
    ledger_id    bigint PRIMARY KEY REFERENCES s13.ledger(id),
    verdict      text NOT NULL CHECK (verdict IN
                     ('attest','attest_with_reservations','refuse')),
    independence text NOT NULL CHECK (independence IN
                     ('technical','managerial','financial')),
    basis        text NOT NULL                       -- competence basis (G13/I2)
);

-- Consumer 1 — the profile compliance closure: "countersigned and in force" is a DERIVED property
-- over the shared history (external clause 4: countersigned joins in-force as a theorem, never a
-- stored field). A row is countersigned-in-force iff it is not whole-row-superseded AND some
-- in-force review with verdict='attest' regards it. A superseding row is born unattested, so
-- sign-off staleness propagates for free (external clause 3).
CREATE OR REPLACE VIEW s13.countersigned_in_force
    WITH (security_invoker = true) AS
SELECT l.*
FROM   s13.ledger l
WHERE  NOT EXISTS (SELECT 1 FROM s13.ledger s WHERE s.supersedes = l.id)
AND    EXISTS (
         SELECT 1 FROM s13.ledger r
         JOIN   s13.review_detail d ON d.ledger_id = r.id
         WHERE  r.kind = 'review' AND r.regards = l.id
         AND    d.verdict = 'attest'
         AND    NOT EXISTS (SELECT 1 FROM s13.ledger s2 WHERE s2.supersedes = r.id));

-- Consumer 2 — the gap detector (flag-and-journal feed, NEVER a repair; a missing countersign is a
-- finding, external clause 8). It reports, for each OBLIGED row, whether a live attesting review
-- exists. The obligation is OTHER-ASSIGNED and label-indifferent (F26/external clause 5): a row is
-- obliged iff a countersign obligation names its actor's-work scope, assigned BY A DIFFERENT
-- principal. It does NOT key on the subject's self-declared kind/concern. The obligation table is
-- populated by an assessor principal (operator/engineer), never by the row's author.
CREATE TABLE IF NOT EXISTS s13.countersign_obligation (
    scope        text PRIMARY KEY,          -- an other-assigned work/hazard scope key
    assigned_by  bigint NOT NULL REFERENCES kernel.principal(id),
    obliges_actor bigint NOT NULL REFERENCES kernel.principal(id)  -- whose rows this scope obliges
);

-- review_gap: obliged in-force rows lacking a live attesting review by an independent actor.
-- assigned_by <> obliges_actor is enforced structurally below so the obligation cannot be
-- self-assigned (an assessor prices the work, not the worker — external clause 6).
ALTER TABLE s13.countersign_obligation DROP CONSTRAINT IF EXISTS obligation_not_self_assigned;
ALTER TABLE s13.countersign_obligation
    ADD CONSTRAINT obligation_not_self_assigned CHECK (assigned_by <> obliges_actor);

CREATE OR REPLACE VIEW s13.review_gap
    WITH (security_invoker = true) AS
SELECT l.id, l.actor, o.scope, o.assigned_by
FROM   s13.ledger l
JOIN   s13.countersign_obligation o ON o.obliges_actor = l.actor
WHERE  NOT EXISTS (SELECT 1 FROM s13.ledger s WHERE s.supersedes = l.id)
AND    NOT EXISTS (
         SELECT 1 FROM s13.ledger r
         JOIN   s13.review_detail d ON d.ledger_id = r.id
         WHERE  r.kind = 'review' AND r.regards = l.id
         AND    d.verdict = 'attest' AND r.actor <> l.actor
         AND    NOT EXISTS (SELECT 1 FROM s13.ledger s2 WHERE s2.supersedes = r.id));

-- ============================================================================================
-- RESOLUTION CONSUMER (answers ships with this)
-- ============================================================================================
-- question_status: for each question row, DERIVE whether it is answered (an in-force row with
-- answers=Q exists) — distinct from supersedes-replacement. `answered_by_nonquestion` flags an
-- answers edge whose SOURCE is itself a question (a category smell surfaced, not denied); the
-- resolution status is never written back to the question row (no auto-resolve, F28).
CREATE OR REPLACE VIEW s13.question_status
    WITH (security_invoker = true) AS
SELECT q.id AS question_id,
       q.kind AS question_kind,
       EXISTS (SELECT 1 FROM s13.ledger a
               WHERE a.answers = q.id
               AND   NOT EXISTS (SELECT 1 FROM s13.ledger s WHERE s.supersedes = a.id)) AS answered,
       (SELECT min(a.id) FROM s13.ledger a
        WHERE a.answers = q.id
        AND   NOT EXISTS (SELECT 1 FROM s13.ledger s WHERE s.supersedes = a.id)) AS first_answer_id,
       (q.kind <> 'question') AS answers_target_not_a_question
FROM   s13.ledger q
WHERE  q.kind = 'question'
   OR  EXISTS (SELECT 1 FROM s13.ledger a WHERE a.answers = q.id);

-- ============================================================================================
-- ISOLATION GRANTS (mirror s12: led_s13 appends+reads its own ledger and the profile views, reads
-- the shared reference, and NOTHING else — no cross-schema, no reference write, no legacy grant).
-- kernel.principal / principal_role are SELECT-only to the subject (attribution is other-assigned;
-- the subject cannot mint or remap a principal).
-- ============================================================================================
GRANT USAGE ON SCHEMA s13 TO led_s13;
GRANT USAGE ON SCHEMA kernel TO led_s13;
GRANT SELECT ON kernel.principal, kernel.principal_role TO led_s13;
GRANT INSERT, SELECT ON s13.ledger TO led_s13;
GRANT USAGE ON SEQUENCE s13.ledger_id_seq TO led_s13;
GRANT SELECT ON s13.ledger_current, s13.countersigned_in_force, s13.review_gap,
                s13.question_status TO led_s13;
GRANT SELECT, INSERT ON s13.review_detail TO led_s13;
GRANT USAGE ON SCHEMA ref TO led_s13;
GRANT SELECT ON ref.prior_decisions TO led_s13;
