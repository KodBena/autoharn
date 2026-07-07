-- db/harness/004_rulings_ledger.sql
-- autoharn operational store #4 — the RULINGS LEDGER (consult 25 §2.2; Increment-4 build).
-- Kills the prose-half-life class (the forged scheduling ruling; the false-positive misattribution —
-- both specimens of paraphrase drift). A ruling is filed here VERBATIM, quote-never-paraphrase, by an
-- AUTHENTIC principal, BEFORE it is delivered; the message actually sent must match its filed
-- verbatim, and the audit checks it did (the delivery-drill splice scan, A.5).
--
-- e15 USE: the directive text (§4.1, opaque-labelled per A.3) and the change-order (§4.2) are filed
-- here binding + subject-invisible BEFORE the run. The A.5 sha256 freight for both delivered texts
-- lives on the row (verbatim_sha256) — the same hash the oracle §7 pre-registers.
--
-- SCOPE (honest): a ruling is a CLAIM ABOUT AUTHORITY (who ruled what, verbatim) — apparatus-side,
-- never a subject-visible byte and never an evidence ledger. It lives in the `harness` DB.
--
-- Idempotent + re-runnable, parameterized by a psql `:schema` variable. Default schema: `acts`
-- (the rulings ledger shares the acts apparatus schema — one apparatus home for the act stream and
-- the rulings that frame it). REWIND: DROP SCHEMA acts CASCADE (or the :schema you built).
--     psql -h 192.168.122.1 -d harness -f db/harness/004_rulings_ledger.sql

\if :{?schema}
\else
  \set schema acts
\endif

BEGIN;
CREATE SCHEMA IF NOT EXISTS :"schema";

-- ===== the ruling (append-only; id-is-order; VERBATIM never paraphrase) =====
CREATE TABLE IF NOT EXISTS :"schema".ruling (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- id-is-order (THE key)
  actor          text NOT NULL,                    -- the AUTHENTIC principal ('human:maintainer') — never a synthetic label
  verbatim       text NOT NULL,                    -- the ruling's EXACT words; quote, never paraphrase
  verbatim_sha256 text NOT NULL,                   -- the A.5 delivery freight — the frozen bytes' hash, fixed pre-run
  binding_grade  text NOT NULL CHECK (binding_grade IN ('binding','advisory','informational')),
  regards        text,                             -- what the ruling is about (free text: a run label, a step, a row ref)
  supersedes     bigint REFERENCES :"schema".ruling(id),  -- a ruling that replaces an earlier one
  ts             timestamptz NOT NULL DEFAULT now()
);

COMMENT ON COLUMN :"schema".ruling.verbatim IS
  'The EXACT words filed BEFORE delivery. The delivered message must match this byte-for-byte; the audit checks it (A.5). Quote, never paraphrase — this table exists to kill paraphrase drift.';
COMMENT ON COLUMN :"schema".ruling.verbatim_sha256 IS
  'sha256 of verbatim, fixed pre-run (the A.5 F40 delivery freight; the oracle §7 pre-registers the same hash).';

-- The verbatim_sha256 must actually be the hash of verbatim (illegal states unrepresentable —
-- ADR-0000/0012: a filed ruling whose hash does not match its own text is a lying freight).
CREATE OR REPLACE FUNCTION :"schema".ruling_hash_matches() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.verbatim_sha256 <> encode(sha256(convert_to(NEW.verbatim, 'UTF8')), 'hex') THEN
    RAISE EXCEPTION 'ruling.verbatim_sha256 does not match sha256(verbatim) — the delivery freight would be a lie. Refusing (A.5).';
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS ruling_hash_matches ON :"schema".ruling;
CREATE TRIGGER ruling_hash_matches BEFORE INSERT ON :"schema".ruling
  FOR EACH ROW EXECUTE FUNCTION :"schema".ruling_hash_matches();

-- ===== append-only hardening (a ruling is a FACT; the record is never rewritten — F28) =====
-- A correction to a ruling is a NEW ruling that `supersedes` the old, never an UPDATE. This is the
-- whole point: paraphrase drift happens when a "ruling" is edited in place; here it cannot be.
CREATE OR REPLACE FUNCTION :"schema".ruling_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'acts.ruling is append-only (a ruling is an audit fact — this table kills paraphrase drift): % refused. To correct a ruling, file a NEW one that supersedes the old.', TG_OP;
END $$;
DROP TRIGGER IF EXISTS ruling_append_only_row ON :"schema".ruling;
CREATE TRIGGER ruling_append_only_row BEFORE UPDATE OR DELETE ON :"schema".ruling
  FOR EACH ROW EXECUTE FUNCTION :"schema".ruling_append_only();
DROP TRIGGER IF EXISTS ruling_append_only_trunc ON :"schema".ruling;
CREATE TRIGGER ruling_append_only_trunc BEFORE TRUNCATE ON :"schema".ruling
  FOR EACH STATEMENT EXECUTE FUNCTION :"schema".ruling_append_only();

COMMIT;

-- ===== honest ledger of strength =====
-- ENFORCED at write time (structural): id-is-order (identity PK); binding_grade closed (CHECK);
--   verbatim_sha256 = sha256(verbatim) (trigger — the freight cannot lie); append-only (trigger —
--   UPDATE/DELETE/TRUNCATE refused; a correction supersedes, never edits).
-- NOT ENFORCED here (delivery-side, A.5): that the DELIVERED message matched verbatim (the
--   delivery_drill.py --check operator-turns scan is the blocking close check; 0 splices or the
--   delivery datum is confounded). The DB pins the filed bytes; the drill pins the sent bytes.
