-- e10 / s11 schema build — the isolated per-session ledger for the neutral-mechanism run.
-- Mirrors s10 (physical schema, own sequence, security_invoker view, self-supersedes FK,
-- one-row trigger, led_s11 role, isolation grants) with the e10 lever and the F29 repair:
--
--   LEVER (consult 11 §7.1): `enacts` becomes MULTI-TARGET — bigint[] (nullable), with a
--     documented honest-empty. The single-column self-FK `bigint REFERENCES ledger(id)` that
--     Postgres gave for free on a scalar column has no array analogue, so per-element FK
--     semantics are restored by a BEFORE-INSERT trigger (the Port/ACL boundary of ADR-0012 P2:
--     it translates-and-validates and REFUSES what it cannot honor). Each element must resolve
--     to an EARLIER, OWN-SESSION row — the same existence+precedence contract the scalar FK +
--     the gate's enacts_ok jointly enforced in e9, now made unrepresentable-if-violated at the
--     write boundary. `{}` and NULL both pass (the honest-empty: "no single design row applies").
--
--   F29 REPAIR (consult 11 §2.3/§7.2): `ALTER ROLE led_s11 SET search_path = s11`. led_s9 carried
--     this role-level pin; led_s10 did not (the omission that resolved CLAUDE.md's unqualified
--     `ledger` to legacy public.ledger and manufactured the e9 opening spiral). Restored here so
--     the byte-held unqualified-`ledger` example resolves to s11.ledger as written.
--
-- `supersedes` untouched (comparability). All prior-shape rows read unchanged; historical enacts
-- were scalar and are NULL in this fresh schema. Run as the schema owner (bork). Idempotent
-- enough to re-run before launch.

CREATE SCHEMA IF NOT EXISTS s11;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'led_s11') THEN
    CREATE ROLE led_s11 LOGIN INHERIT;
  END IF;
END $$;

-- F29: role-level search_path pin (the setting led_s10 was missing). Idempotent.
ALTER ROLE led_s11 SET search_path = s11;

CREATE TABLE IF NOT EXISTS s11.ledger (
    id          bigserial PRIMARY KEY,
    ts          timestamptz NOT NULL DEFAULT now(),
    session     text NOT NULL DEFAULT 's11',
    kind        text NOT NULL CHECK (kind IN
                    ('assumption','decision','question','verification',
                     'finding','snag','revision','note')),
    statement   text NOT NULL,
    rationale   text,
    status      text NOT NULL DEFAULT 'open' CHECK (status IN
                    ('open','held','confirmed','refuted','superseded','answered')),
    evidence    text,
    confidence  text CHECK (confidence IN ('low','medium','high')),
    supersedes  bigint REFERENCES s11.ledger(id),
    refs        text,
    concern     text CHECK (concern IN ('design','enactment','process','other')),
    enacts      bigint[]                                 -- multi-target; per-element FK by trigger
);

CREATE OR REPLACE VIEW s11.ledger_current
    WITH (security_invoker = true) AS
SELECT l.*
FROM   s11.ledger l
WHERE  NOT EXISTS (SELECT 1 FROM s11.ledger s WHERE s.supersedes = l.id);

-- Backstop for multi-row VALUES bulk loads (mirrors the s10 trigger verbatim).
CREATE OR REPLACE FUNCTION s11.one_row_per_insert() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
BEGIN
  IF (SELECT count(*) FROM newrows) > 1 THEN
    RAISE EXCEPTION 'Ledger policy: one entry per INSERT — log each decision at the time of the event it records; bulk multi-row inserts are disabled.';
  END IF;
  RETURN NULL;
END;
$fn$;

DROP TRIGGER IF EXISTS one_row_per_insert ON s11.ledger;
CREATE TRIGGER one_row_per_insert
    AFTER INSERT ON s11.ledger
    REFERENCING NEW TABLE AS newrows
    FOR EACH STATEMENT EXECUTE FUNCTION s11.one_row_per_insert();

-- Per-element enacts validation (the array analogue of the scalar self-FK). Each element must
-- name an EARLIER row in the SAME session; empty {}/NULL pass (the documented honest-empty).
-- Column defaults (ts=now(), session='s11') are populated before this BEFORE-ROW trigger fires,
-- so NEW.ts / NEW.session are the values the row will carry. A self-reference (own not-yet-
-- inserted id) fails EXISTS naturally, so it is refused with no special case.
CREATE OR REPLACE FUNCTION s11.validate_enacts() RETURNS trigger
    LANGUAGE plpgsql AS $fn$
DECLARE e bigint;
BEGIN
  IF NEW.enacts IS NOT NULL THEN
    FOREACH e IN ARRAY NEW.enacts LOOP
      IF NOT EXISTS (SELECT 1 FROM s11.ledger d
                     WHERE d.id = e AND d.session = NEW.session AND d.ts < NEW.ts) THEN
        RAISE EXCEPTION 'Ledger policy: enacts element % does not resolve to an earlier entry in this session — each enacts id must name an EARLIER own-session row; leave enacts empty when no single design row applies.', e;
      END IF;
    END LOOP;
  END IF;
  RETURN NEW;
END;
$fn$;

DROP TRIGGER IF EXISTS validate_enacts ON s11.ledger;
CREATE TRIGGER validate_enacts
    BEFORE INSERT ON s11.ledger
    FOR EACH ROW EXECUTE FUNCTION s11.validate_enacts();

-- Isolation grants (mirror s10): led_s11 may read the shared reference, append + read its own
-- ledger, read the live view — and nothing else. No cross-schema, no reference write, and (by
-- omission) no grant of any kind on legacy public.ledger.
GRANT USAGE ON SCHEMA s11 TO led_s11;
GRANT USAGE ON SCHEMA ref TO led_s11;
GRANT SELECT ON ref.prior_decisions TO led_s11;
GRANT INSERT, SELECT ON s11.ledger TO led_s11;
GRANT USAGE ON SEQUENCE s11.ledger_id_seq TO led_s11;
GRANT SELECT ON s11.ledger_current TO led_s11;
