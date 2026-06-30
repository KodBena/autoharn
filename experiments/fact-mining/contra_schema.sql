-- experiments/fact-mining/contra_schema.sql
-- NEW, REVERSIBLE contradiction store. Idempotent + re-runnable.
-- REWIND (the exact command):  DROP SCHEMA contra CASCADE;
-- Touches NOTHING else: mining / nla / trace / public are never referenced.

CREATE SCHEMA IF NOT EXISTS contra;

-- a candidate contradiction the transparent rules found (the detector's one home)
CREATE TABLE IF NOT EXISTS contra.finding (
  finding_id  bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_doc  text NOT NULL,                       -- provenance: the document the claims came from
  rule        text NOT NULL,                       -- 'R-NEG' | 'R-FUNC' | 'R-NUM'  (the rule-id IS the confidence)
  subj_key    text NOT NULL,                       -- canonical subject the two claims share (the join key)
  pred        text NOT NULL,                       -- predicate lemma the two claims share
  claim_a     text NOT NULL,                       -- human-readable claim A
  claim_b     text NOT NULL,                       -- human-readable claim B
  span_a      text NOT NULL,                       -- source sentence grounding claim A
  span_b      text NOT NULL,                       -- source sentence grounding claim B
  grounding   text NOT NULL,                       -- the rule-specific evidence (allowlist entry / numbers / polarity)
  extra       jsonb NOT NULL DEFAULT '{}'::jsonb,  -- additive escape hatch (char offsets, sent ids)
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_doc, rule, subj_key, pred, claim_a, claim_b)   -- re-run = idempotent (no duplicate finding)
);

-- a verdict on a finding (rule / human / llm), via the REUSED adjudicate stack
CREATE TABLE IF NOT EXISTS contra.adjudication (
  adjudication_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  finding_id  bigint NOT NULL REFERENCES contra.finding ON DELETE CASCADE,
  verdict     text NOT NULL,                       -- 'contradiction' | 'not-contradiction' | 'uncertain'
  adjudicator text NOT NULL,                       -- 'rule:auto' | 'llm' | a human id
  note        text NOT NULL DEFAULT '',            -- the adjudicate Adjudication.note (policy provenance)
  ts          timestamptz NOT NULL DEFAULT now()
);

-- convenience projection for review (DERIVED, not a third store — ADR-0012 P1)
CREATE OR REPLACE VIEW contra.review AS
  SELECT f.finding_id, f.source_doc, f.rule, f.subj_key, f.pred,
         f.claim_a, f.claim_b, f.grounding,
         a.verdict, a.adjudicator, a.ts
  FROM contra.finding f
  LEFT JOIN contra.adjudication a USING (finding_id);
