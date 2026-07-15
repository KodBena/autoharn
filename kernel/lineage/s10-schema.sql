-- e9 / s10 schema build — the isolated per-session ledger for the vocabulary run.
-- Mirrors s9 (physical schema, own sequence, security_invoker view, self-FK, one-row
-- trigger, led_s10 role, isolation grants) with the single lever added: the record
-- vocabulary gains two nullable columns —
--   concern  : the axis the entry addresses (design vs enactment vs process), CHECK-
--              constrained text with the ADR-0008 escape value 'other' (kept in the
--              kind/status idiom rather than a native pg enum — behaviourally an enum,
--              nullable, and read as text by every existing instrument unchanged).
--   enacts   : self-FK, the sibling of `supersedes` — an enactment row names the design
--              row it carries into a file, so the design→enactment chain is machine-walkable.
-- Both nullable; every e3–e9 comparison holds (historical rows are all NULL; `kind` byte-
-- identical). Run as the schema owner (bork). Idempotent enough to re-run before launch.

CREATE SCHEMA IF NOT EXISTS s10;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'led_s10') THEN
    CREATE ROLE led_s10 LOGIN INHERIT;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS s10.ledger (
    id          bigserial PRIMARY KEY,
    ts          timestamptz NOT NULL DEFAULT now(),
    session     text NOT NULL DEFAULT 's10',
    kind        text NOT NULL CHECK (kind IN
                    ('assumption','decision','question','verification',
                     'finding','snag','revision','note')),
    statement   text NOT NULL,
    rationale   text,
    status      text NOT NULL DEFAULT 'open' CHECK (status IN
                    ('open','held','confirmed','refuted','superseded','answered')),
    evidence    text,
    confidence  text CHECK (confidence IN ('low','medium','high')),
    supersedes  bigint REFERENCES s10.ledger(id),
    refs        text,
    concern     text CHECK (concern IN ('design','enactment','process','other')),
    enacts      bigint REFERENCES s10.ledger(id)
);

CREATE OR REPLACE VIEW s10.ledger_current
    WITH (security_invoker = true) AS
SELECT l.*
FROM   s10.ledger l
WHERE  NOT EXISTS (SELECT 1 FROM s10.ledger s WHERE s.supersedes = l.id);

-- Backstop for multi-row VALUES bulk loads (mirrors the s9 trigger verbatim).
CREATE OR REPLACE FUNCTION s10.one_row_per_insert() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  IF (SELECT count(*) FROM newrows) > 1 THEN
    RAISE EXCEPTION 'Ledger policy: one entry per INSERT — log each decision at the time of the event it records; bulk multi-row inserts are disabled.';
  END IF;
  RETURN NULL;
END;
$fn$;

DROP TRIGGER IF EXISTS one_row_per_insert ON s10.ledger;
CREATE TRIGGER one_row_per_insert
    AFTER INSERT ON s10.ledger
    REFERENCING NEW TABLE AS newrows
    FOR EACH STATEMENT EXECUTE FUNCTION s10.one_row_per_insert();

-- Isolation grants (mirror s9): led_s10 may read the shared reference, append + read its
-- own ledger, read the live view — and nothing else. No cross-schema, no reference write.
GRANT USAGE ON SCHEMA s10 TO led_s10;
GRANT USAGE ON SCHEMA ref TO led_s10;
GRANT SELECT ON ref.prior_decisions TO led_s10;
GRANT INSERT, SELECT ON s10.ledger TO led_s10;
GRANT USAGE ON SEQUENCE s10.ledger_id_seq TO led_s10;
GRANT SELECT ON s10.ledger_current TO led_s10;
