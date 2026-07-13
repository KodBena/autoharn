-- stores/008_harness_failure_ledger.sql
-- autoharn operational store #8 — the HARNESS FAILURE LEDGER: a structured, cross-project home for
-- how autoharn's OWN mechanisms (hooks, verbs, gates, scaffolds) misbehave, teach badly, or surprise an
-- operator -- the "stop-breaker stall" class (ledger row 419, ent deployment, 2026-07-13). Maintainer
-- directive 2026-07-13 (design/ORCH-HARNESS-FAILURE-LEDGER.md, commission ledger row 425): "in the
-- interest of IMPROVING AUTOHARN, start collecting failures like the stop-breaker stall in an
-- AUXILIARY SCHEMA, for projects that subscribe to it -- DEFAULT ON, since he is currently the
-- project's only known user."
--
-- PLACEMENT: this is a SECOND auxiliary schema in the SAME standing `research` db
-- stores/001_research_ledger.sql already uses -- not a new database. It reuses core.project/
-- core.session (built by 001) for deployment/session identity rather than re-deriving a parallel
-- registry (ADR-0012 P1, single source of truth); see design/ORCH-HARNESS-FAILURE-LEDGER.md's
-- "Why research, not a new database" section for the argument in full.
--
-- SHAPE: mirrors the finding+disposition idiom this project's other ledgers already use
-- (research.finding/research.finding_confirmed; stores/002_rationalization_ledger.sql's own
-- finding+disposition split) -- an IMMUTABLE observation (harness_failure.record) plus an
-- APPEND-ONLY disposition trail (harness_failure.disposition), never one mutable row conflating
-- "what happened" with "what became of it" (ADR-0012 P3, no god-objects). "Currently open" is a
-- DERIVED view (harness_failure.open_records), never a writable flag -- the same posture
-- research.finding_confirmed already established.
--
-- EVIDENCE DISCIPLINE (ledger row 296, action-stream-is-evidentiary-basis ruling): a record's
-- evidence pointer is a journal file+line, a tracker ledger row id, or a git commit hash -- NEVER a
-- session transcript excerpt. There is no "transcript" evidence_kind and none should ever be added.
--
-- STATUS: STRUCTURE ONLY. This DDL creates empty tables; nothing here inserts a row and nothing here
-- is applied to any database by this commission -- applying is the operator's/maintainer's own typed-
-- confirmation act via bootstrap/apply-harness-failure-ledger.sh, exactly as for 001. The nine
-- ready-to-INSERT backfill records (the five ENT TESTBED FINDINGs + four NEW observatory lessons) are
-- DATA, listed in design/ORCH-HARNESS-FAILURE-LEDGER.md's appendix, not in this file -- structure and
-- data ship separately, same posture as 001.

BEGIN;

CREATE SCHEMA IF NOT EXISTS harness_failure;

-- ===== immutable observation =====
CREATE TABLE harness_failure.record (
  record_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  schema_version text NOT NULL DEFAULT 'harness-failure/1'
                 CHECK (schema_version = 'harness-failure/1'),   -- widen by adding a new literal + nullable columns, never by repurposing one (see design doc "Growing the envelope")
  project_id     text NOT NULL REFERENCES core.project,          -- deployment identity (SSOT: core.project, built by 001)
  observed_at    timestamptz NOT NULL,                           -- WHEN the failure was OBSERVED (writer-supplied; distinct from created_at)
  mechanism      text NOT NULL,                                  -- the harness surface involved (e.g. 'stop_clean_exit', 'change_gate', 'pickup') -- free text, deliberately not a closed CHECK: the mechanism set grows with the harness itself
  event_class    text NOT NULL CHECK (event_class IN ('defect','friction','watch','teach-gap')),
  evidence_kind  text NOT NULL CHECK (evidence_kind IN ('journal','ledger_row','git_commit')),
  evidence_journal_file text,                                    -- e.g. '.claude/logs/stop_clean_exit.journal.jsonl'
  evidence_journal_line integer,
  evidence_ledger_row_id bigint,                                 -- a `./led show <id>`-resolvable row, in the DEPLOYMENT's own tracker (not this db)
  evidence_git_commit    text,
  summary        text NOT NULL,                                  -- free-text account of what happened
  session_id     text REFERENCES core.session,                   -- who/what filed this record
  git_commit     text,                                            -- the AUTOHARN checkout's own commit at observation time, when known
  created_at     timestamptz NOT NULL DEFAULT now(),              -- ingest/ordering clock (DB-stamped; see trigger) -- NOT the observation time
  CHECK (
    (evidence_kind = 'journal'     AND evidence_journal_file IS NOT NULL) OR
    (evidence_kind = 'ledger_row'  AND evidence_ledger_row_id IS NOT NULL) OR
    (evidence_kind = 'git_commit'  AND evidence_git_commit    IS NOT NULL)
  )                                                                -- a record cannot claim an evidence kind with no pointer to show for it
);

-- ===== append-only disposition trail =====
-- id-is-order (stores/002_rationalization_ledger.sql's own convention): the identity PK IS the
-- record order; the CURRENT disposition is the row with the greatest disposition_id for a record_id,
-- never re-derived by any other ordering.
CREATE TABLE harness_failure.disposition (
  disposition_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  record_id      bigint NOT NULL REFERENCES harness_failure.record,
  disposition    text NOT NULL CHECK (disposition IN ('open','filed-as-item','fixed','wontfix')),
  tracker_item_slug text,
  note           text,
  session_id     text REFERENCES core.session,
  created_at     timestamptz NOT NULL DEFAULT now(),
  CHECK (disposition = 'open' OR tracker_item_slug IS NOT NULL)  -- any disposition past 'open' names the tracker item that disposed it -- never a floating "fixed" with nothing to cite
);

-- ===== DERIVED "open" view (never a writable flag) =====
CREATE VIEW harness_failure.open_records AS
  SELECT r.*
    FROM harness_failure.record r
    LEFT JOIN LATERAL (
      SELECT d.disposition, d.tracker_item_slug
        FROM harness_failure.disposition d
       WHERE d.record_id = r.record_id
       ORDER BY d.disposition_id DESC
       LIMIT 1
    ) latest ON true
   WHERE latest.disposition IS NULL OR latest.disposition = 'open';
-- a record with NO disposition row yet is implicitly 'open' (mirrors research.finding's own
-- 'provisional' default with no forced first write); a record IS open iff its latest disposition act
-- (by disposition_id, the id-is-order convention) says so or none has been recorded yet.

-- ===== write-time hardening =====
CREATE FUNCTION harness_failure.freeze_record() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'harness_failure.record is immutable (an observation is a fact): % blocked', TG_OP; END $$;
CREATE TRIGGER record_immutable BEFORE UPDATE OR DELETE ON harness_failure.record
  FOR EACH ROW EXECUTE FUNCTION harness_failure.freeze_record();

CREATE FUNCTION harness_failure.freeze_disposition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'harness_failure.disposition is append-only (a disposition is an act): % blocked', TG_OP; END $$;
CREATE TRIGGER disposition_immutable BEFORE UPDATE OR DELETE ON harness_failure.disposition
  FOR EACH ROW EXECUTE FUNCTION harness_failure.freeze_disposition();

CREATE FUNCTION harness_failure.stamp_created_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.created_at := now(); RETURN NEW; END $$;       -- stamps INGEST time only; observed_at (record) is untouched
CREATE TRIGGER stamp_record BEFORE INSERT ON harness_failure.record
  FOR EACH ROW EXECUTE FUNCTION harness_failure.stamp_created_at();
CREATE TRIGGER stamp_disposition BEFORE INSERT ON harness_failure.disposition
  FOR EACH ROW EXECUTE FUNCTION harness_failure.stamp_created_at();

COMMIT;

-- ===== honest ledger of strength (no word worn that isn't earned) =====
-- ENFORCED at write time (structural — cannot be violated):
--   record->core.project NOT NULL (deployment identity always resolves); evidence_kind's declared
--   variant carries its required pointer field (CHECK); event_class/evidence_kind/disposition are
--   closed vocabularies (CHECK); records are immutable once written (trigger); dispositions are
--   append-only (trigger); a disposition past 'open' always names a tracker_item_slug (CHECK);
--   record.created_at / disposition.created_at = DB-stamped ingest time (trigger), distinct from
--   record.observed_at (writer-supplied).
-- DERIVED (cannot be falsely asserted; auto-revises as new disposition acts are appended):
--   "currently open" = harness_failure.open_records.
-- SEAMS left for additive growth (deferring these loses no data): schema_version's own literal (a
--   future harness-failure/2 widens by addition, per the design doc); mechanism stays free text
--   rather than a closed CHECK because the harness's own mechanism set grows; a future
--   filing/record_harness_failure.py writer helper (named, not built, in design/
--   ORCH-HARNESS-FAILURE-LEDGER.md -- mirrors filing/record_reading.py's shape).
-- NOT YET — labelled: a writer CLI (see above); mechanized cross-check of `mechanism` against
--   filing/apparatus_registry.py's live-derived mechanism set (review-only today); the scaffold
--   subscription wiring itself (bootstrap/templates/apparatus.json), shipped as a PROPOSAL in the
--   design doc rather than code in this commit (see that doc's "Scaffold wiring" section for why).
--   OUT OF SCOPE (consumer concern): a session transcript evidence kind — deliberately never added,
--   per ledger row 296's action-stream-is-evidentiary-basis ruling.
-- STATUS: structure only, not yet applied to the standing `research` db. Next gated step is the
--   operator's/maintainer's own APPLY, via bootstrap/apply-harness-failure-ledger.sh (armed, not
--   run) — then, separately, the maintainer's own decision to apply the nine backfill INSERTs listed
--   in design/ORCH-HARNESS-FAILURE-LEDGER.md's appendix.
