-- nla — the SUBJECT-FACING decision ledger, re-instantiated in the ISOLATED database `nla`.
--
-- WHY THIS FILE EXISTS (operator-side context — this .sql is NOT subject-visible; it lives in the
-- operator repo. Only the CATALOG OBJECTS it creates inside `nla` are readable by the subject role,
-- so only THOSE must be scrubbed of every experiment token; this preamble is honest engineer prose):
--
--   Link 20 built the subject ledger in schema s14 of database `epistemic`. An out-of-frame
--   hack-rationalization audit returned UNDISCHARGED-HACK: Postgres system catalogs are
--   world-readable WITHIN a database, so the subject role could read apparatus vocabulary across the
--   whole epistemic catalog — function bodies, object names, view defs, the s9..s14 schema lineage —
--   a comment-strip could not close it. The ratified fix (maintainer, engineer-ruled under
--   delegation): move the subject to a SEPARATE database. Postgres databases are catalog-isolated —
--   a role connected to `nla` physically cannot read `epistemic`'s catalog. This file instantiates
--   that isolated ledger.
--
-- THE SPLIT (engineer-ruled; built to, not re-litigated):
--   * `nla` carries ONLY the disclosed decision-ledger the subject writes: the ledger table
--     (the disclosed vocabulary — kind/status/concern/statement/rationale/evidence/confidence/refs,
--     supersedes/enacts/amends/answers, and the amends_scope verbatim-quotation + uniqueness
--     contract), its append-only trigger, its one-row-per-INSERT trigger, the ledger_current view,
--     and a MINIMAL self-contained actor attribution sufficient to stamp the subject's own writes.
--   * WITHHELD (stays in `epistemic`, invisible to the subject): the operator-side
--     attestation/obligation machinery — the `review` kind, the `regards` edge, review_detail,
--     countersign_obligation, countersigned_in_force, review_gap — and the waiver rows and
--     coverage/soundness instruments. A subject that sees the countersign kernel is primed; a subject
--     that sees a resolution-status consumer for `answers` is primed on the resolution readout. So the
--     `answers` edge's consumer lives operator-side (an instrument reading nla), never as a
--     subject-readable view here.
--
-- OPAQUE NAMING (mandatory): the schema is `public` (not an ordinal `sNN` — an ordinal is a lineage
--   leak); the connecting role is `nla_rw` (not `led_sNN`), a mundane non-ordinal service account.
--   Every experiment token (finding numbers, ruling/maintainer/apparatus vocabulary, attestation
--   vocabulary, the s9..s14 lineage) is scrubbed from every catalog object the subject can read —
--   comments (pg_description), function bodies (pg_proc.prosrc), object/constraint/trigger names,
--   and view definitions. The disclosed ledger vocabulary itself (the kind names, amends/answers/
--   enacts/supersedes, amends_scope) STAYS — it is the instrument the subject is handed.
--
-- ACTOR ATTRIBUTION, MINIMAL & SELF-CONTAINED: in `nla` only one principal writes — the subject, via
--   `nla_rw`. There is no operator/engineer/second-principal writer here (that machinery is withheld
--   with the review kernel). So the FK-priced principal table is unnecessary: `actor` is stamped from
--   the connection identity (`current_user`) by a NOT NULL column default. The write is attributed by
--   WHAT THE CONNECTION IS — the connection's granted identity, not a subject-authored label — which
--   is exactly the other-assigned attribution principle, realized in its minimal self-contained form.
--
-- Run as the schema owner (bork) against database `nla`. Idempotent enough to re-run.

-- ============================================================================================
-- THE LEDGER (the whole subject-facing surface: one table, its views, its write-boundary triggers)
-- ============================================================================================
CREATE TABLE IF NOT EXISTS public.ledger (
    id          bigserial PRIMARY KEY,
    ts          timestamptz NOT NULL DEFAULT now(),
    session     text NOT NULL DEFAULT 'main',
    kind        text NOT NULL CHECK (kind IN
                    ('assumption','decision','question','verification',
                     'finding','snag','revision','note')),
    statement   text NOT NULL,
    rationale   text,
    status      text NOT NULL DEFAULT 'open' CHECK (status IN
                    ('open','held','confirmed','refuted','superseded','answered')),
    evidence    text,
    confidence  text CHECK (confidence IN ('low','medium','high')),
    -- supersedes: whole-row replacement — the superseded row leaves the current view.
    supersedes  bigint REFERENCES public.ledger(id),
    refs        text,
    concern     text CHECK (concern IN ('design','enactment','process','other')),
    -- enacts: the enactment edge — the earlier decision row(s) this entry carries into a file. A
    -- multi-target array with a documented honest-empty ({}/NULL = no single earlier row applies).
    enacts      bigint[],
    -- actor: who authored this row. NOT NULL — an unattributable writer cannot touch the ledger.
    -- Stamped from the connection identity by the column default (the other-assigned attribution).
    actor       text NOT NULL DEFAULT current_user,
    -- amends + amends_scope: clause-level revision. `amends` names the earlier row a specific clause
    -- of which this row defeats (the rest of that row stands — this is NOT supersession); amends_scope
    -- names WHICH clause, as a verbatim quotation of the target's own text (both-or-neither).
    amends       bigint REFERENCES public.ledger(id),
    amends_scope text,
    -- answers: the resolution edge — the earlier question this row answers. Distinct from supersedes:
    -- an answered question stays current, it is not replaced.
    answers      bigint REFERENCES public.ledger(id)
);

-- Column comments (a subject-readable surface via \d+ ledger): the neutral engineering register a
-- real auditable ledger would use — no apparatus provenance, disclosed vocabulary only.
COMMENT ON COLUMN public.ledger.enacts IS
  'Enactment edge: the earlier decision row(s) this entry carries into a file — one, several, or none ({}/NULL when no single earlier row applies). Refinement of an earlier row uses amends; a bare reference uses refs.';
COMMENT ON COLUMN public.ledger.amends IS
  'Clause-level revision: the earlier row a specific clause of which this entry defeats, while the rest of that row stands (it is not superseded). amends_scope must quote that clause verbatim from the target''s statement or rationale.';
COMMENT ON COLUMN public.ledger.answers IS
  'Resolution edge: the earlier question this entry answers. Distinct from supersedes — an answered question stays current; the resolution is derived, never written back onto the question row.';
COMMENT ON COLUMN public.ledger.actor IS
  'Author of this row, stamped from the connection identity (never a self-declared field).';

-- Current view: the rows not whole-row-superseded. (An answered question is NOT superseded, so it
-- correctly survives here.)
CREATE OR REPLACE VIEW public.ledger_current
    WITH (security_invoker = true) AS
SELECT l.*
FROM   public.ledger l
WHERE  NOT EXISTS (SELECT 1 FROM public.ledger s WHERE s.supersedes = l.id);

-- ---- write-boundary triggers (illegal states unrepresentable) -------------------------------

-- (a) one entry per INSERT — log each decision at the time of the event it records.
CREATE OR REPLACE FUNCTION public.one_row_per_insert() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  IF (SELECT count(*) FROM newrows) > 1 THEN
    RAISE EXCEPTION 'Ledger policy: one entry per INSERT — log each decision at the time of the event it records; bulk multi-row inserts are disabled.';
  END IF;
  RETURN NULL;
END;
$fn$;
DROP TRIGGER IF EXISTS one_row_per_insert ON public.ledger;
CREATE TRIGGER one_row_per_insert AFTER INSERT ON public.ledger
    REFERENCING NEW TABLE AS newrows
    FOR EACH STATEMENT EXECUTE FUNCTION public.one_row_per_insert();

-- (b) per-element enacts validation: each enacts id names an EARLIER own-session row.
CREATE OR REPLACE FUNCTION public.validate_enacts() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
DECLARE e bigint;
BEGIN
  IF NEW.enacts IS NOT NULL THEN
    FOREACH e IN ARRAY NEW.enacts LOOP
      IF NOT EXISTS (SELECT 1 FROM public.ledger d
                     WHERE d.id = e AND d.session = NEW.session AND d.ts < NEW.ts) THEN
        RAISE EXCEPTION 'Ledger policy: enacts element % does not resolve to an earlier entry in this session — each enacts id must name an EARLIER own-session row; leave enacts empty when no single design row applies.', e;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END;
$fn$;
DROP TRIGGER IF EXISTS validate_enacts ON public.ledger;
CREATE TRIGGER validate_enacts BEFORE INSERT ON public.ledger
    FOR EACH ROW EXECUTE FUNCTION public.validate_enacts();

-- (c) validate_amends: amends and amends_scope are both-or-neither; the target is an earlier
-- own-session row; a row may not amend the same target it supersedes (whole-row and clause defeat of
-- one row is a category error). amends_scope must be a VERBATIM substring of the target row's
-- statement or rationale — the defeated clause, quoted — and must occur EXACTLY ONCE across
-- statement + rationale, so a span occurring in two distinct clauses (an ambiguous referent) is
-- refused with instruction to extend the quotation. A quotation shorter than 10 characters is
-- refused (a stopword quotation satisfies substring vacuously). Append-only makes the quotation
-- binding: the target text can never change under it.
CREATE OR REPLACE FUNCTION public.validate_amends() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
DECLARE t_statement text; t_rationale text;
BEGIN
  IF NEW.amends IS NOT NULL THEN
    IF NEW.amends_scope IS NULL OR btrim(NEW.amends_scope) = '' THEN
      RAISE EXCEPTION 'Ledger policy: an amends edge must name WHICH clause it defeats (amends_scope) — a scopeless amends is indistinguishable from a supersede.';
    END IF;
    SELECT d.statement, coalesce(d.rationale,'') INTO t_statement, t_rationale
      FROM public.ledger d
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
    -- occurrence count across statement + rationale = (len(hay) - len(hay with needle removed)) /
    -- len(needle); more than one occurrence names an ambiguous referent and is refused.
    IF ( (length(t_statement) - length(replace(t_statement, NEW.amends_scope, ''))) / length(NEW.amends_scope)
       + (length(t_rationale) - length(replace(t_rationale, NEW.amends_scope, ''))) / length(NEW.amends_scope)
       ) > 1 THEN
      RAISE EXCEPTION 'Ledger policy: amends_scope ''%'' occurs more than once across row %''s statement/rationale — the referent is AMBIGUOUS between clauses. Extend the quotation to name exactly one clause.', NEW.amends_scope, NEW.amends;
    END IF;
  ELSIF NEW.amends_scope IS NOT NULL THEN
    RAISE EXCEPTION 'Ledger policy: amends_scope is meaningless without an amends target.';
  END IF;
  RETURN NEW;
END;
$fn$;
DROP TRIGGER IF EXISTS validate_amends ON public.ledger;
CREATE TRIGGER validate_amends BEFORE INSERT ON public.ledger
    FOR EACH ROW EXECUTE FUNCTION public.validate_amends();

-- (d) validate_answers: answers resolves to an earlier own-session row. The target's kind is NOT
-- enforced here — an answers-target-that-is-not-a-question is a review-side flag, never a denial.
CREATE OR REPLACE FUNCTION public.validate_answers() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  IF NEW.answers IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM public.ledger d
                   WHERE d.id = NEW.answers AND d.session = NEW.session AND d.id < NEW.id) THEN
      RAISE EXCEPTION 'Ledger policy: answers must resolve to an EARLIER own-session row.';
    END IF;
  END IF;
  RETURN NEW;
END;
$fn$;
DROP TRIGGER IF EXISTS validate_answers ON public.ledger;
CREATE TRIGGER validate_answers BEFORE INSERT ON public.ledger
    FOR EACH ROW EXECUTE FUNCTION public.validate_answers();

-- BEGIN APPEND-ONLY (the one section a scratch mirror strips — a mirror resets at will; the durable
-- ledger never does. The mirror derivation in run-nla-acceptance.sh drops this block.)
-- (e) append-only protection: the ledger is DURABLE — UPDATE, DELETE, and TRUNCATE are refused at
-- the write boundary, for every role. (The owner can still DROP the table by hand for a reset; the
-- invariant is that no DML write path can rewrite or erase a logged entry.)
CREATE OR REPLACE FUNCTION public.append_only() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  RAISE EXCEPTION 'Ledger policy: the ledger is append-only and durable — % is refused for every role.', TG_OP;
END;
$fn$;
DROP TRIGGER IF EXISTS append_only_row ON public.ledger;
CREATE TRIGGER append_only_row
    BEFORE UPDATE OR DELETE ON public.ledger
    FOR EACH ROW EXECUTE FUNCTION public.append_only();
DROP TRIGGER IF EXISTS append_only_truncate ON public.ledger;
CREATE TRIGGER append_only_truncate
    BEFORE TRUNCATE ON public.ledger
    FOR EACH STATEMENT EXECUTE FUNCTION public.append_only();
-- END APPEND-ONLY

-- BEGIN ROLE-GRANTS (stripped for the scratch mirror; the mirror is owner-only)
-- ============================================================================================
-- THE CONNECTING ROLE (opaque, non-ordinal) + GRANTS (appends + reads its own ledger; nothing else)
-- ============================================================================================
--
-- *** BLOCKING HAZARD — creating this login role is NOT sufficient for subject isolation. ***
-- Database catalog isolation only forecloses the apparatus leak if this role is ALSO denied CONNECT
-- to the apparatus databases. PostgreSQL grants CONNECT to PUBLIC by default and pg_hba.conf here
-- admits every role to every database (`host <db> all <ip> trust`), so an UNCONFINED `nla_rw` can
-- `psql -U nla_rw -d epistemic` and read the ENTIRE apparatus catalog (F44/maintainer comments, the
-- excluded review/regards/kernel machinery, the s6..s14 lineage) — verified live. Confining this
-- role requires a pg_hba.conf write on the DB server host (or a PUBLIC-connect revoke on epistemic),
-- BOTH of which are outside this build's sanctioned reach. It is a REQUIRED engineer pre-launch step:
-- see harness/e14-build/nla/BLOCKING-confine-subject-role.md. The subject run MUST NOT start until it
-- is discharged and verified (nla_rw connects to `nla` only, rejected from `epistemic`).
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nla_rw') THEN
    CREATE ROLE nla_rw LOGIN INHERIT;
  END IF;
END $$;

-- Pin the role's search_path to the public schema (deterministic; no ordinal).
ALTER ROLE nla_rw SET search_path = public;

GRANT USAGE ON SCHEMA public TO nla_rw;
GRANT INSERT, SELECT ON public.ledger TO nla_rw;
GRANT USAGE ON SEQUENCE public.ledger_id_seq TO nla_rw;
GRANT SELECT ON public.ledger_current TO nla_rw;
-- END ROLE-GRANTS
