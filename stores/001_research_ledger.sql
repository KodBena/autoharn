-- stores/001_research_ledger.sql
-- autoharn operational store #1 — a PROJECT-AGNOSTIC measurement-provenance / evidence ledger.
--
-- SCOPE (honest, per the ADR-0014 second opinion of 2026-06-28): this records MEASUREMENTS and the
-- FINDINGS drawn from them, with attributable provenance and earned-not-asserted confirmation. It is
-- software-benchmark-shaped TODAY, with seams for other modalities (human / sensor / survey / observational).
-- It is NOT an empirical-study-design engine: panel / longitudinal / factorial / RCT machinery
-- (units × waves × arms × factors) is OUT OF SCOPE and belongs to a consumer schema that EXTENDS this one.
-- chocofarm's throughput_lab and omega's perf work are consumers that write here tagged `project_id`;
-- this is not their schema (no `tlab_`).
--
-- STATUS: PROPOSAL v0.1, scratch-validated 2026-07-11 (see BACKLOG "Chocofarm experiment-ledger
-- disposition"). Not yet applied to the standing `research` db, not committed. First increment plus the
-- second-opinion fixes (honest scope; observation-time, which is lossy-if-deferred; cheap additive seams).
--
-- Creed kept where load-bearing:
--   * confirmation is DERIVED, never a writable field — earned, not asserted; auto-revises.
--   * the warrant predicate GROWS by increment; a finding is exactly as confirmed as it checks TODAY.
--   * measurement ⊥ interpretation; readings immutable; ingest time DB-stamped (ordering, not writer data).

BEGIN;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS research;

-- ===== shared spine =====
CREATE TABLE core.project (
  project_id text PRIMARY KEY,                           -- 'chocofarm' | 'omega' | 'autoharn' | ...
  name       text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE core.session (                               -- the WHO (attribution)
  session_id text PRIMARY KEY,
  project_id text NOT NULL REFERENCES core.project,
  model      text,
  started_at timestamptz NOT NULL DEFAULT now(),
  summary    text
);

-- ===== apparatus (first-class) =====
-- NOTE (ADR-0008): `kind` is NOT YET MECE — 'harness' overlaps 'script', and survey/sensor/simulation/
-- human-rater modalities are absent. To be split into orthogonal axes later: modality {software,human,
-- sensor,survey,simulation,derived} × role {harness,probe,benchmark,fixture}. Read it as provisional.
CREATE TABLE research.instrument (
  instrument_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project_id    text NOT NULL REFERENCES core.project,
  name          text NOT NULL,
  kind          text NOT NULL CHECK (kind IN ('benchmark','probe','script','harness')),  -- provisional, non-MECE (see note)
  source_hash   text NOT NULL,
  build_recipe  jsonb NOT NULL DEFAULT '{}'::jsonb,
  git_commit    text NOT NULL,
  git_tree      text NOT NULL CHECK (git_tree IN ('clean','dirty')),
  session_id    text REFERENCES core.session,
  qualification text NOT NULL DEFAULT 'provisional'
                CHECK (qualification IN ('provisional','qualified','suspect','retracted')),
  qualification_note text,
  supersedes    bigint REFERENCES research.instrument,
  created_at    timestamptz NOT NULL DEFAULT now(),
  -- dedupe seam (2026-07-11 scratch-validation fix; mirrors chocofarm exp_db's tlab_config
  -- ON CONFLICT(config_key) DO NOTHING): `source_hash` was already carrying content identity in
  -- its own name and comment intent but no constraint enforced it — a re-run writer that
  -- re-registers the SAME built apparatus every call (the natural harness-flush shape) would
  -- otherwise flood this table with duplicate rows for one unchanged build, each needing its own
  -- qualification bookkeeping. UNIQUE(project_id, source_hash) makes "same apparatus, one row"
  -- structural; a genuinely NEW build (different source_hash) still gets its own row, optionally
  -- linked via `supersedes`. Requalifying an EXISTING row is a plain UPDATE of `qualification`
  -- (this table carries no immutability trigger, unlike research.reading — only the measurement
  -- is frozen; the apparatus record is mutable metadata by design).
  UNIQUE (project_id, source_hash)
);

-- ===== measurement (immutable) =====
CREATE TABLE research.reading (
  reading_id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project_id    text NOT NULL REFERENCES core.project,
  instrument_id bigint NOT NULL REFERENCES research.instrument,   -- no reading without an apparatus
  subject_id    text,                                   -- SEAM: unit/subject of observation (the panel/longitudinal seam); NULL = implicit
  metric        text NOT NULL,
  value         double precision,                        -- numeric outcome ...
  value_text    text,                                    -- ... or categorical/boolean/ranked (A>B, pass/fail, label)
  unit          text,
  n             integer,
  stderr        double precision,
  config        jsonb NOT NULL DEFAULT '{}'::jsonb,
  git_commit    text,                                    -- SEAM: provenance, not identity — NULL for non-software/observational data
  git_tree      text CHECK (git_tree IN ('clean','dirty')),     -- NULL when there is no git context
  observed_at   timestamptz,                             -- WHEN the observation occurred (writer-supplied; NULL if unknown). DISTINCT from created_at.
  session_id    text REFERENCES core.session,
  created_at    timestamptz NOT NULL DEFAULT now(),      -- ingest/ordering clock (DB-stamped; see trigger) — NOT the observation time
  CHECK (value IS NOT NULL OR value_text IS NOT NULL)    -- a reading must record an outcome
);

-- ===== interpretation (append-only; SEPARATE from measurement) =====
-- `reading_id` is the PRIMARY reading. SEAM: multi-reading findings (a contrast / A-B / model-fit over a
-- SET) arrive via a future research.finding_evidence(finding_id, reading_id, role) join — reading_id is
-- NOT an enshrined 1:1. `status` holds only writer-intent; 'confirmed' is derived below, not assertable.
CREATE TABLE research.finding (
  finding_id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project_id     text NOT NULL REFERENCES core.project,
  reading_id     bigint NOT NULL REFERENCES research.reading,
  motivation     text,                                   -- the belief/hypothesis ("x believed y")
  interpretation text NOT NULL,                           -- the conclusion ("... is z, because ...")
  status         text NOT NULL DEFAULT 'provisional' CHECK (status IN ('provisional','retracted')),
  supersedes     bigint REFERENCES research.finding,
  session_id     text REFERENCES core.session,
  git_commit     text,
  created_at     timestamptz NOT NULL DEFAULT now()
);

-- ===== DERIVED confirmation (one positive invariant; cannot be falsely asserted; auto-revises) =====
-- v0 warrant is SOFTWARE-FRAMED (requires a clean git tree): a non-software reading (NULL git) is not yet
-- confirmable here — honest, not hidden (its confirmation criteria are out of v0 scope). The predicate GROWS.
CREATE VIEW research.finding_confirmed AS
  SELECT f.*
    FROM research.finding   f
    JOIN research.reading    r ON r.reading_id    = f.reading_id
    JOIN research.instrument i ON i.instrument_id = r.instrument_id
   WHERE f.status = 'provisional'                                              -- not retracted
     AND NOT EXISTS (SELECT 1 FROM research.finding s WHERE s.supersedes = f.finding_id)  -- not superseded
     AND r.git_tree    = 'clean'                                               -- CALIB (software frame)
     AND i.qualification = 'qualified'                                         -- apparatus qualified
     AND f.session_id IS NOT NULL;                                            -- ATTR: attributed
-- v0 STRENGTH (stated, not laundered): clean-tree ∧ qualified-instrument ∧ not-superseded ∧ attributed.
-- NOT YET (labelled): independent reproduction (INDEP) and criterion-before-result (RECORD) — increment 2.

-- ===== write-time hardening =====
CREATE FUNCTION research.freeze_reading() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'research.reading is immutable (a measurement is a fact): % blocked', TG_OP; END $$;
CREATE TRIGGER reading_immutable BEFORE UPDATE OR DELETE ON research.reading
  FOR EACH ROW EXECUTE FUNCTION research.freeze_reading();

CREATE FUNCTION core.stamp_created_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.created_at := now(); RETURN NEW; END $$;       -- stamps INGEST time only; observed_at is untouched
CREATE TRIGGER stamp_reading BEFORE INSERT ON research.reading
  FOR EACH ROW EXECUTE FUNCTION core.stamp_created_at();

COMMIT;

-- ===== honest ledger of strength (no word worn that isn't earned) =====
-- ENFORCED at write time (structural — cannot be violated):
--   measurement ⊥ interpretation (separate tables); reading→instrument NOT NULL; an outcome present
--   (value OR value_text); closed-vocab CHECKs; readings immutable (trigger); reading.created_at = DB-stamped
--   ingest time (trigger).
-- DERIVED (cannot be falsely asserted; auto-revises): confirmation = research.finding_confirmed.
-- SEAMS left for additive growth (deferring these loses no data): subject_id (unit), value_text (non-numeric),
--   nullable git (non-software), finding_evidence join (contrast/set findings), modality/role split of `kind`.
--   observed_at was NOT deferred (it would have been lossy) — added now, writer-supplied.
-- NOT YET — labelled: increment 2 reproduction (INDEP) + prereg (RECORD); AUTH (write-authority);
--   store #2 registry; store #3 work-log. OUT OF SCOPE (consumer concern): empirical study-design machinery.
-- STATUS: scratch-validated 2026-07-11 against a throwaway schema pair in the `toy` db (both polarities
--   witnessed: well-formed rows insert; every declared CHECK/trigger/view-write refusal refuses). Zero-residue
--   torn down. Next gated step is the operator's/maintainer's own APPLY to the standing `research` db, via
--   bootstrap/apply-research-ledger.sh (armed, not run).
