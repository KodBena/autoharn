-- db/harness/002_rationalization_ledger.sql
-- autoharn operational store #2 — the RATIONALIZATION LEDGER: hack-rationalization-detector
-- outcomes as an appendable, LABELED SQL corpus (BACKLOG.md "Rationalization ledger", commit ad1b2a3;
-- maintainer directive 2026-07-06). The THIRD consumer of the finding+disposition idiom, after
-- contra.finding/contra.adjudication and research.finding — a finding is a QUOTED detector fire, a
-- disposition is an actor-attributed act that LABELS it (confirmed-hack / false-positive / duplicate-of).
--
-- SCOPE (honest): these are CLAIMS ABOUT WORK — a detector fired on a change's justification — never
-- subject/epistemic/evidence records (never the s*/nla/marriage ledgers). It lives in the `harness` DB.
--
-- WHY SQL, WHY APPEND-ONLY: the corpus feeds two directions the maintainer named — (1) LAW improvement
-- (bulk-audit which ADR formulations get rationalized around most; every confirmed case is a failed
-- position appended to the LAW's training corpus) and (2) detector precision (measure the false-positive
-- rate; the labeled false-positives tighten the skill). Both need it QUERYABLE and APPENDABLE, so:
--   * a finding is one immutable row (idempotent re-file via UNIQUE);
--   * a disposition is an append-only, actor-attributed ACT (F28: nothing auto-resolves; id-is-order —
--     the identity PK IS the record order, and the CURRENT label is the latest disposition by id);
--   * the confirmed set is a DERIVED view, never a writable flag (as research.finding_confirmed is).
--
-- Idempotent + re-runnable (contra_schema.sql posture). Parameterized by a psql `:schema` variable so
-- it is exercised on a throwaway schema before touching the real `harness` corpus — one DDL home
-- (ADR-0012 P1), not a second hand-copied scratch variant. Default is `harness`:
--     psql -h 192.168.122.1 -d harness -f db/harness/002_rationalization_ledger.sql
--     psql -h 192.168.122.1 -d harness -v schema=rat_scratch -f db/harness/002_rationalization_ledger.sql
-- REWIND (the exact command):  DROP SCHEMA harness CASCADE;   (or the :schema you built)

\if :{?schema}
\else
  \set schema harness
\endif

BEGIN;
CREATE SCHEMA IF NOT EXISTS :"schema";

-- ===== the detector fire (one immutable row per rationalization) =====
CREATE TABLE IF NOT EXISTS :"schema".rationalization_finding (
  finding_id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- id-is-order (F28)
  quoted_rationalization text NOT NULL,                    -- the VERBATIM passage the detector fired on (the tell)
  register               text NOT NULL,                    -- the discipline-word/register used ('minimal' | 'scope creep' | 'for now' | 'proportionate' | ...)
  named_better_fix       text,                             -- the more-general fix that was named-and-downgraded (NULL = none was named)
  law_refs               text NOT NULL DEFAULT '',         -- the ADR/LAW refs the rationalization routes around (e.g. 'ADR-0013 R3; ADR-0000')
  context                text NOT NULL,                    -- WHAT change/diff/file/PR the fire was on (the object of suspicion)
  session_id             text,                             -- WHO detected (the detecting session) — provenance, nullable
  git_commit             text,                             -- the commit the change sat on — provenance, nullable
  detector_version       text NOT NULL,                    -- the skill/detector version that fired (precision-tracking over time)
  extra                  jsonb NOT NULL DEFAULT '{}'::jsonb,-- additive escape hatch (tells scanner hits, writer delta, ...)
  created_at             timestamptz NOT NULL DEFAULT now(),
  UNIQUE (context, quoted_rationalization, detector_version)  -- re-file is idempotent (no duplicate finding)
);

-- ===== the disposition act (append-only, actor-attributed; F28: nothing auto-resolves) =====
-- A finding has NO label until an actor files a disposition. The CURRENT label is the latest act by
-- disposition_id (id-is-order). 'duplicate-of' carries its target finding; the other two do not.
CREATE TABLE IF NOT EXISTS :"schema".rationalization_disposition (
  disposition_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- id-is-order (the act's place in the record)
  finding_id     bigint NOT NULL REFERENCES :"schema".rationalization_finding ON DELETE CASCADE,
  act            text NOT NULL CHECK (act IN ('confirmed-hack','false-positive','duplicate-of')),
  duplicate_of   bigint REFERENCES :"schema".rationalization_finding,  -- required IFF act='duplicate-of'
  actor          text NOT NULL,                            -- WHO disposed (a human id / 'llm:<model>' / a session) — attribution
  note           text NOT NULL DEFAULT '',                 -- the rationale/evidence for the act
  ts             timestamptz NOT NULL DEFAULT now(),
  CHECK ((act = 'duplicate-of') = (duplicate_of IS NOT NULL)),  -- duplicate-of carries its target; others must not
  CHECK (duplicate_of IS NULL OR duplicate_of <> finding_id)    -- a finding cannot be a duplicate of itself
);

-- ===== append-only hardening (F28: finding + disposition are FACTS; the record is never rewritten) =====
-- A FINDING is immutable: "the detector fired with THIS quoted text on THIS context" is an audit fact,
-- and editing it in place would falsify the record the corpus exists to preserve. A correction is a NEW
-- finding plus a `duplicate-of` disposition, never an UPDATE. (A re-file is ON CONFLICT DO NOTHING --
-- it performs no UPDATE, so this trigger does not block idempotent re-filing.) This closes the gap the
-- out-of-frame audit found: the header called a finding "immutable" while nothing enforced it.
CREATE OR REPLACE FUNCTION :"schema".freeze_finding() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'rationalization_finding is IMMUTABLE (a detector fire is an audit fact): % blocked. To correct a finding, file a NEW one and dispose the old duplicate-of/false-positive.', TG_OP;
END $$;
DROP TRIGGER IF EXISTS finding_immutable ON :"schema".rationalization_finding;
CREATE TRIGGER finding_immutable BEFORE UPDATE OR DELETE ON :"schema".rationalization_finding
  FOR EACH ROW EXECUTE FUNCTION :"schema".freeze_finding();

CREATE OR REPLACE FUNCTION :"schema".freeze_disposition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'rationalization_disposition is APPEND-ONLY (F28: a disposition act is a fact, nothing auto-resolves): % blocked. To reverse a judgment, append a NEW act.', TG_OP;
END $$;
DROP TRIGGER IF EXISTS disposition_append_only ON :"schema".rationalization_disposition;
CREATE TRIGGER disposition_append_only BEFORE UPDATE OR DELETE ON :"schema".rationalization_disposition
  FOR EACH ROW EXECUTE FUNCTION :"schema".freeze_disposition();

-- ===== DERIVED current-label + confirmed set (never a writable flag; auto-revises on the next act) =====
-- The current label of a finding is the LATEST disposition by id (id-is-order); a finding with no
-- disposition is UNLABELED (current_act NULL) — it is exactly as confirmed as it has been judged TODAY.
CREATE OR REPLACE VIEW :"schema".rationalization_current AS
  SELECT f.*, d.act AS current_act, d.actor AS current_actor,
         d.duplicate_of AS current_duplicate_of, d.ts AS disposed_at
    FROM :"schema".rationalization_finding f
    LEFT JOIN LATERAL (
      SELECT act, actor, duplicate_of, ts
        FROM :"schema".rationalization_disposition
       WHERE finding_id = f.finding_id
       ORDER BY disposition_id DESC   -- id-is-order: the newest act is the standing label
       LIMIT 1
    ) d ON true;

-- The confirmed corpus — the single source the generated known-cases.md few-shot is built from
-- (design lean (a)): a finding whose current label is 'confirmed-hack'.
CREATE OR REPLACE VIEW :"schema".rationalization_confirmed AS
  SELECT * FROM :"schema".rationalization_current WHERE current_act = 'confirmed-hack';

COMMIT;

-- ===== honest ledger of strength =====
-- ENFORCED at write time (structural): finding idempotent (UNIQUE) AND immutable (trigger); disposition
--   act closed-vocab (CHECK); duplicate-of carries exactly its target (CHECK); dispositions append-only (trigger).
-- DERIVED (cannot be falsely asserted; auto-revises): the current label and the confirmed set are views.
-- F28: nothing auto-resolves — a finding is unlabeled until an actor disposes it; a reversal is a NEW act.
-- NOT ENFORCED here (review-only, stated per ADR-0011 Rule 1): that a `duplicate-of` target is itself a
--   real prior finding of the SAME rationalization (a semantic judgment the actor makes, not a constraint).
