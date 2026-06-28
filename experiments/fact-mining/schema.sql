-- experiments/fact-mining/schema.sql
-- EXPERIMENTAL, EPHEMERAL fact store for the spaCy mining experiment.
-- Lives in its own schema so the whole thing wipes with one statement and
-- cannot touch anything else:
--     DROP SCHEMA mining CASCADE;
-- This is NOT a blessed migration (cf. db/harness/) — it is a throwaway we keep
-- only until the shape stabilises, then it graduates to a real db/harness/NNN_*.sql.
--
-- Design intent: store facts in a LOGIC-AGNOSTIC relational base, then let each
-- logic be a VIEW / export over it (see the bottom of this file). The base
-- records WHAT was extracted and WHERE from (provenance spine); it commits to no
-- single logic. Additive-by-construction: a jsonb `extra` on every fact table is
-- the escape hatch for structure we have not modelled yet (dep paths, modality,
-- confidence, normalised time intervals).

BEGIN;
DROP SCHEMA IF EXISTS mining CASCADE;
CREATE SCHEMA mining;

-- ===== provenance spine =====
CREATE TABLE mining.document (
  doc_id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  path      text NOT NULL,
  title     text,
  sha256    text NOT NULL,            -- hash of the normalised body actually parsed
  model     text NOT NULL,            -- spaCy pipeline that produced these facts
  loaded_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (sha256, model)              -- same text+model = same facts; re-load replaces
);

CREATE TABLE mining.sentence (
  sent_id    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  doc_id     bigint NOT NULL REFERENCES mining.document ON DELETE CASCADE,
  sent_index int NOT NULL,            -- order within the document (cheap temporal proxy)
  text       text NOT NULL,
  UNIQUE (doc_id, sent_index)
);

-- ===== the atom: an SVO assertion (logic-agnostic) =====
CREATE TABLE mining.assertion (
  assertion_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sent_id    bigint NOT NULL REFERENCES mining.sentence ON DELETE CASCADE,
  subj       text NOT NULL,           -- human-readable phrase (subtree)
  pred       text NOT NULL,           -- verb lemma
  obj        text NOT NULL,
  subj_key   text NOT NULL,           -- canonical constant: coref- + entity-resolved (what joins)
  obj_key    text NOT NULL,
  negated    boolean NOT NULL DEFAULT false,  -- seam to defeasible / paraconsistent
  subj_label text,                    -- NER label of the subject head, if any (a sort)
  obj_label  text,
  extra      jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX assertion_spo ON mining.assertion (pred, subj_key, obj_key);

-- ===== constants / sorts: named entities =====
CREATE TABLE mining.entity (
  entity_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sent_id   bigint NOT NULL REFERENCES mining.sentence ON DELETE CASCADE,
  text      text NOT NULL,            -- surface form as it appeared
  canonical text NOT NULL,            -- normalized constant (clusters Greek/Greeks/the Greeks)
  label     text NOT NULL,            -- PERSON | GPE | ORG | DATE | ...
  extra     jsonb NOT NULL DEFAULT '{}'::jsonb
);

-- ===== temporal expressions: raw material for a temporal logic (valid-time) =====
CREATE TABLE mining.temporal (
  temporal_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sent_id   bigint NOT NULL REFERENCES mining.sentence ON DELETE CASCADE,
  text      text NOT NULL,            -- e.g. 'the sixth century B.C.'
  label     text NOT NULL,            -- DATE | TIME
  extra     jsonb NOT NULL DEFAULT '{}'::jsonb  -- normalised interval goes here later
);

-- ===== per-logic projections over the one base =====

-- CLASSICAL: the positive fact base, over canonical constants. pred(subj_key, obj_key).
-- Empty keys (unresolved pronouns, punctuation) are not usable constants -> excluded.
CREATE VIEW mining.fact_classical AS
  SELECT assertion_id, subj_key, pred, obj_key, subj, obj
  FROM mining.assertion
  WHERE NOT negated AND subj_key <> '' AND obj_key <> '';

-- PARACONSISTENT / DEFEASIBLE: the same canonical (subj,pred,obj) asserted both ways.
-- Classical logic explodes on this (ex falso quodlibet); a paraconsistent or
-- defeasible logic is exactly what you reach for to hold it without trivialising.
CREATE VIEW mining.contradiction AS
  SELECT p.subj_key, p.pred, p.obj_key,
         p.assertion_id AS pos_id, n.assertion_id AS neg_id
  FROM mining.assertion p
  JOIN mining.assertion n
    ON  p.subj_key = n.subj_key AND p.pred = n.pred AND p.obj_key = n.obj_key
   AND  p.negated = false AND n.negated = true;

-- TEMPORAL: assertions co-occurring with a time expression in the same sentence.
-- The seed of valid-time facts: holds(fact) DURING <when>.
CREATE VIEW mining.fact_temporal AS
  SELECT a.assertion_id, a.subj_key, a.pred, a.obj_key, t.text AS when_text, t.label AS when_label
  FROM mining.assertion a
  JOIN mining.temporal t USING (sent_id);

COMMIT;
