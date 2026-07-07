-- db/harness/005_findings_ledger.sql
-- autoharn operational store #5 — the GENERAL FINDINGS LEDGER (finding + disposition; the FOURTH
-- consumer). Commissioned in docs/work-units/WORK-UNIT-findings-disposition.md; landed with e15
-- Increment 5 (the idiom — the rationalization ledger, db/harness/002 — is proven, so it rides).
--
-- (The work-unit names the file `003_findings_ledger.sql`; `003` was taken by the acts-stream
-- contract in Increment 4, so this lands as `005`. The number is the only deviation; the schema and
-- idiom are the work-unit's.)
--
-- THE GAP (work-unit §0). Agents surface in-passing observations ("both diffs predate this increment",
-- "the slot was already filled") in prose, where attribution reads as closure and the observation
-- evaporates. The governing move is the STRUCTURAL SEPARATION OF PROVENANCE FROM DISPOSITION:
-- "predates this increment" is legitimate provenance METADATA on an OPEN finding; it is NEVER a
-- disposition. No prose closes a finding; only a recorded, actor-attributed disposition act does (F28).
-- A finding is OPEN iff it has NO disposition row. "NOTED" in prose stops being a disposition.
--
-- SCOPE (honest): these are CLAIMS ABOUT WORK (in-passing findings + their dispositions) — apparatus-
-- side, never a subject-visible byte, never an evidence ledger. It lives in the `harness` DB alongside
-- the rationalization ledger (002) and the acts/rulings stores (003/004). The rationalization store
-- stays SEPARATE (it carries detector-specific columns — a rationalization FIRE goes there; a general
-- in-passing FINDING goes here); the two share the trigger idiom and the filing-script shape.
--
-- NO VERDICT VOCABULARY (work-unit §4): `class` is a descriptive kebab slug (correctness | hazard |
-- instrument-gap | …), never a verdict on a person. F28: nothing auto-resolves; identity (duplicate-of)
-- is ADJUDICATED by a disposition act, never auto-computed.
--
-- Idempotent + re-runnable, parameterized by a psql `:schema` variable (default `harness`).
--     psql -h 192.168.122.1 -d harness -f db/harness/005_findings_ledger.sql

\if :{?schema}
\else
  \set schema harness
\endif

BEGIN;
CREATE SCHEMA IF NOT EXISTS :"schema";

-- ===== the finding (append-only; id-is-order; provenance is METADATA, never a disposition) =====
CREATE TABLE IF NOT EXISTS :"schema".finding (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- id-is-order (THE key)
  actor            text NOT NULL,                 -- who OBSERVED (agent label or human)
  session          text,                          -- context tag (free text, honest)
  increment        text,                          -- context tag (e.g. 'e15-inc5')
  class            text NOT NULL,                 -- descriptive kebab slug — NEVER a verdict
  statement        text NOT NULL,                 -- the observation, verbatim-quoting where it cites anyone
  evidence_ref     text,                          -- path / commit / row ref
  provenance_claim text,                          -- 'predates-increment' | 'inherited-from-e13' — METADATA, NOT a disposition
  frame            text NOT NULL DEFAULT 'in-frame' CHECK (frame IN ('in-frame','out-of-frame')),
  created_at       timestamptz NOT NULL DEFAULT now()
);
COMMENT ON COLUMN :"schema".finding.provenance_claim IS
  'Provenance METADATA on an OPEN finding (e.g. predates-increment). NEVER a disposition — a finding with a provenance_claim and no finding_disposition row is still OPEN. This column exists precisely so provenance cannot be smuggled in as closure.';

-- ===== the disposition (append-only; the ONLY thing that closes a finding — F28) =====
CREATE TABLE IF NOT EXISTS :"schema".finding_disposition (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  finding_id  bigint NOT NULL REFERENCES :"schema".finding(id),
  actor       text NOT NULL,                      -- who DISPOSED (agent label or human)
  kind        text NOT NULL CHECK (kind IN ('fixed','filed','explained','waived','duplicate-of')),
  ref         text,                               -- REQUIRED for filed/explained/waived/duplicate-of (see trigger)
  created_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE :"schema".finding_disposition IS
  'A finding is OPEN iff it has NO row here. duplicate-of is FindingIdentity in its honest minimal form: identity is ADJUDICATED by this act, never auto-computed — a fuzzy match may SUGGEST, only an act disposes.';

-- ref is REQUIRED per kind: filed (work-unit/backlog ref), explained (evidence), waived (maintainer
-- ruling ref — an acts.ruling id, or until then the verbatim message location), duplicate-of (finding id).
-- Only 'fixed' MAY omit ref (a fix is self-evidencing via the commit, though a commit ref is encouraged).
-- (`:"schema"` is NOT interpolated inside a $$…$$ body — psql suppresses it, the s15/002 gotcha — so
-- the duplicate-of existence check resolves the schema dynamically from TG_TABLE_SCHEMA, which is the
-- finding_disposition table's schema = the finding table's schema.)
CREATE OR REPLACE FUNCTION :"schema".finding_disposition_ref_required() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE dup_ok boolean;
BEGIN
  IF NEW.kind <> 'fixed' AND (NEW.ref IS NULL OR btrim(NEW.ref) = '') THEN
    RAISE EXCEPTION 'finding_disposition.kind=% requires a ref (filed→work-unit/backlog; explained→evidence; waived→maintainer ruling ref; duplicate-of→finding id). A disposition without its witness is nothing (ADR-0005 R9).', NEW.kind;
  END IF;
  IF NEW.kind = 'duplicate-of' THEN
    EXECUTE format('SELECT EXISTS(SELECT 1 FROM %I.finding WHERE id::text = $1)', TG_TABLE_SCHEMA)
      INTO dup_ok USING btrim(NEW.ref);
    IF NOT dup_ok THEN
      RAISE EXCEPTION 'finding_disposition.kind=duplicate-of requires ref = an existing finding id (got %).', NEW.ref;
    END IF;
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS finding_disposition_ref_required ON :"schema".finding_disposition;
CREATE TRIGGER finding_disposition_ref_required BEFORE INSERT ON :"schema".finding_disposition
  FOR EACH ROW EXECUTE FUNCTION :"schema".finding_disposition_ref_required();

-- ===== append-only hardening (a finding + its disposition are audit FACTS — F28; 002's idiom) =====
CREATE OR REPLACE FUNCTION :"schema".finding_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'the findings ledger is append-only (a finding/disposition is an audit fact): % refused. To change a finding''s standing, file a NEW disposition; to correct a finding, file a new one that duplicate-of the old.', TG_OP;
END $$;
DROP TRIGGER IF EXISTS finding_immutable_row ON :"schema".finding;
CREATE TRIGGER finding_immutable_row BEFORE UPDATE OR DELETE ON :"schema".finding
  FOR EACH ROW EXECUTE FUNCTION :"schema".finding_immutable();
DROP TRIGGER IF EXISTS finding_immutable_trunc ON :"schema".finding;
CREATE TRIGGER finding_immutable_trunc BEFORE TRUNCATE ON :"schema".finding
  FOR EACH STATEMENT EXECUTE FUNCTION :"schema".finding_immutable();
DROP TRIGGER IF EXISTS finding_disposition_append_only_row ON :"schema".finding_disposition;
CREATE TRIGGER finding_disposition_append_only_row BEFORE UPDATE OR DELETE ON :"schema".finding_disposition
  FOR EACH ROW EXECUTE FUNCTION :"schema".finding_immutable();
DROP TRIGGER IF EXISTS finding_disposition_append_only_trunc ON :"schema".finding_disposition
;
CREATE TRIGGER finding_disposition_append_only_trunc BEFORE TRUNCATE ON :"schema".finding_disposition
  FOR EACH STATEMENT EXECUTE FUNCTION :"schema".finding_immutable();

-- ===== the OPEN view (a finding with no disposition — the close-gate's query) =====
CREATE OR REPLACE VIEW :"schema".finding_open AS
SELECT f.* FROM :"schema".finding f
WHERE NOT EXISTS (SELECT 1 FROM :"schema".finding_disposition d WHERE d.finding_id = f.id);

COMMIT;

-- ===== honest ledger of strength =====
-- ENFORCED at write time (structural): id-is-order; class/frame/kind vocabularies (CHECK); ref-per-kind
--   (trigger); append-only UPDATE/DELETE/TRUNCATE refused on BOTH tables (trigger). A finding is OPEN
--   iff finding_open lists it; only a disposition act closes it (F28) — provenance_claim never does.
-- NOT ENFORCED here (review/close-gate): that an in-passing observation was ACTUALLY filed (the only
--   way to cheat is not to file — one detectable act class); the close-gate (tools/findings_gate.py,
--   a close_manifest line) makes an OPEN finding turn the close RED so an increment cannot report
--   complete with undischarged findings.
