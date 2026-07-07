-- db/harness/006_foreclosure_debt.sql
-- autoharn operational store #6 — the FORECLOSURE-DEBT LEDGER (ADR-0000 never-again, mechanized).
-- Design: never-again-mechanism-fable-consult.md §Core (adopted verbatim) + the RATIFIED HYBRID
-- (never-again-synthesis.md): intent named at disposition time (a `fixed` disposition requires a ref
-- naming the intended foreclosure — one sentence, recorded hot), evidence owed by CLOSE (a
-- class_foreclosure row + a banked seen-red artifact, gated by the foreclosure-debt manifest line).
-- Work unit: docs/work-units/WORK-UNIT-foreclosure-debt.md.
--
-- WHAT THIS MECHANIZES. A `fixed` disposition closes the INSTANCE. Under ADR-0000 it simultaneously opens
-- a CLASS DEBT: "what forecloses the class?" That debt becomes a row-shaped fact the moment the fix is
-- recorded — a TRIGGER makes it, not a person — and the close gate goes RED while unpaid. "Never again"
-- stops being something someone remembers and becomes something the experiment cannot close around.
--
-- THE MECHANISM'S HONEST LIMITS (copied from the consult's failure-modes, per the work-unit acceptance —
-- the mechanism is not claimed to be complete):
--   * THE FILING LAPSE is OUT OF SCOPE, said loudly: a hazard that is never filed as a finding never
--     enters this system at all. This ledger forecloses "a FILED fixed finding had its class-debt
--     forgotten"; it cannot foreclose "the hazard was never noticed / never filed". That residual is
--     the findings-ledger's own (file-at-observation discipline), not this one's.
--   * GOODHART / checkbox foreclosures — the largest residual. seen-red raises the floor (a foreclosure
--     without a banked red artifact is unrecordable by construction), but a gate can still be shaped to
--     pass vacuously. The adversarial pass SAMPLES foreclosure rows; the mechanism forces foreclosures to
--     EXIST, it cannot force them to be WELL-SHAPED.
--   * GATE-BODY DRIFT past the integrity line: the integrity check pins the seen-red ARTIFACT's sha, not
--     the gate's live body — re-bank seen-red on a substantial gate edit (the manual counterpart).
--   * The mechanism forecloses its OWN class: "the ADR-0000 conversion was forgotten" is the omission
--     lapse the debt view kills directly. That is the ADR-0000 answer at the meta level.
--
-- SCOPE (honest): a claim about WORK (which class debts are open / discharged), apparatus-side, never a
-- subject byte, never an evidence ledger. Lives in the `harness` DB. Append-only, same trigger idiom.
-- Idempotent + parameterized by a psql `:schema` variable (default `harness`).
--   psql -h 192.168.122.1 -d harness -f db/harness/006_foreclosure_debt.sql

\if :{?schema}
\else
  \set schema harness
\endif

BEGIN;
CREATE SCHEMA IF NOT EXISTS :"schema";

-- ===== class_foreclosure — the banked answer to "what forecloses the class?" (append-only) =====
CREATE TABLE IF NOT EXISTS :"schema".class_foreclosure (
  foreclosure_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,   -- id-is-order
  finding_id     bigint NOT NULL REFERENCES :"schema".finding(id),
  actor          text   NOT NULL,
  kind           text   NOT NULL CHECK (kind IN ('gate','lint','fixture','trigger','waived')),
  check_line_id  text,    -- id of a line in the close-manifest / lint registry (required for gate|lint|fixture|trigger)
  red_artifact   text,    -- repo path of the banked SEEN-RED artifact (ADR-0011); required for those kinds
  red_sha256     text,    -- sha256 of the seen-red artifact; required for those kinds
  ruling_ref     text,    -- required IFF kind='waived' (a maintainer ruling: an acts.ruling id / message loc)
  note           text,    -- the foreclosure shape in one line (what the gate does)
  created_at     timestamptz NOT NULL DEFAULT now()
);
COMMENT ON COLUMN :"schema".class_foreclosure.red_artifact IS
  'ADR-0011 in the schema, not the discipline: a foreclosure without a banked SEEN-RED artifact is unrecordable by construction (the trigger refuses it). Lives at docs/adr-evidence/seen-red/<finding_id>-<slug>/.';

-- kinds gate|lint|fixture|trigger require ALL of (check_line_id, red_artifact, red_sha256); waived
-- requires ruling_ref (mirrors the finding_disposition waived-requires-ruling pattern). Enforced, not
-- trusted — the never-again evidence cannot be omitted.
CREATE OR REPLACE FUNCTION :"schema".class_foreclosure_evidence_required() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.kind = 'waived' THEN
    IF NEW.ruling_ref IS NULL OR btrim(NEW.ruling_ref) = '' THEN
      RAISE EXCEPTION 'class_foreclosure kind=waived requires a ruling_ref (a maintainer ruling: an acts.ruling id, or the verbatim message location). A waiver without an authority is nothing.';
    END IF;
  ELSE  -- gate | lint | fixture | trigger
    IF NEW.check_line_id IS NULL OR btrim(NEW.check_line_id) = ''
       OR NEW.red_artifact IS NULL OR btrim(NEW.red_artifact) = ''
       OR NEW.red_sha256 IS NULL OR btrim(NEW.red_sha256) = '' THEN
      RAISE EXCEPTION 'class_foreclosure kind=% requires check_line_id + red_artifact + red_sha256 (a registered gate AND a banked seen-red artifact — ADR-0011 in the schema). A foreclosure without seen-red is unrecordable.', NEW.kind;
    END IF;
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS class_foreclosure_evidence_required ON :"schema".class_foreclosure;
CREATE TRIGGER class_foreclosure_evidence_required BEFORE INSERT ON :"schema".class_foreclosure
  FOR EACH ROW EXECUTE FUNCTION :"schema".class_foreclosure_evidence_required();

-- append-only (a foreclosure is an audit fact; to change one, file a new row)
CREATE OR REPLACE FUNCTION :"schema".class_foreclosure_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'class_foreclosure is append-only (an audit fact): % refused. File a new row to amend.', TG_OP;
END $$;
DROP TRIGGER IF EXISTS class_foreclosure_append_only_row ON :"schema".class_foreclosure;
CREATE TRIGGER class_foreclosure_append_only_row BEFORE UPDATE OR DELETE ON :"schema".class_foreclosure
  FOR EACH ROW EXECUTE FUNCTION :"schema".class_foreclosure_append_only();
DROP TRIGGER IF EXISTS class_foreclosure_append_only_trunc ON :"schema".class_foreclosure;
CREATE TRIGGER class_foreclosure_append_only_trunc BEFORE TRUNCATE ON :"schema".class_foreclosure
  FOR EACH STATEMENT EXECUTE FUNCTION :"schema".class_foreclosure_append_only();

-- ===== foreclosure_debt — the DERIVED backlog (a view, never maintained; cannot go stale) =====
-- A fixed finding with NO class_foreclosure row owes a debt. explained/filed/waived/duplicate-of owe
-- nothing here (explained=not a defect; filed=owes nothing until fixed; waived=already ruled;
-- duplicate-of rides the canonical finding). The view IS the backlog for this class.
CREATE OR REPLACE VIEW :"schema".foreclosure_debt AS
SELECT DISTINCT f.id AS finding_id, f.class
FROM   :"schema".finding f
JOIN   :"schema".finding_disposition d ON d.finding_id = f.id AND d.kind = 'fixed'
LEFT   JOIN :"schema".class_foreclosure c ON c.finding_id = f.id
WHERE  c.foreclosure_id IS NULL;

-- ===== THE HYBRID — extend the finding_disposition trigger: `fixed` requires an INTENT ref =====
-- Intent recorded HOT (at disposition time): a `fixed` disposition must NAME the intended foreclosure in
-- its ref (one sentence). The EVIDENCE (class_foreclosure row + seen-red) is owed by close (the debt view
-- gates). Both meta-law readings satisfied; neither failure mode fully priced in. (Existing fixed rows
-- predate this and are grandfathered — the back-fill gives them class_foreclosure rows directly.)
CREATE OR REPLACE FUNCTION :"schema".finding_disposition_ref_required() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE dup_ok bigint;
BEGIN
  IF NEW.ref IS NULL OR btrim(NEW.ref) = '' THEN
    -- ALL kinds now require a ref. fixed → the INTENDED FORECLOSURE (the ADR-0000 never-again answer,
    -- named hot, one sentence); others as before (filed→work-unit; explained→evidence; waived→ruling;
    -- duplicate-of→finding id).
    RAISE EXCEPTION 'finding_disposition.kind=% requires a ref. fixed→name the intended foreclosure (the ADR-0000 never-again answer, one sentence — evidence owed by close via class_foreclosure); filed→work-unit/backlog; explained→evidence; waived→maintainer ruling ref; duplicate-of→finding id. A disposition without its witness is nothing (ADR-0005 R9).', NEW.kind;
  END IF;
  IF NEW.kind = 'duplicate-of' THEN
    EXECUTE 'SELECT id FROM ' || quote_ident(TG_TABLE_SCHEMA) || '.finding WHERE id = $1::bigint'
      INTO dup_ok USING btrim(NEW.ref);
    IF dup_ok IS NULL THEN
      RAISE EXCEPTION 'finding_disposition.kind=duplicate-of requires ref = an existing finding id (got %).', NEW.ref;
    END IF;
  END IF;
  RETURN NEW;
END $$;
-- (the trigger binding from 005 stays; CREATE OR REPLACE FUNCTION swaps the body in place.)

COMMIT;

-- ===== honest ledger of strength =====
-- ENFORCED at write time: kind vocabulary (CHECK); evidence-per-kind (trigger — gate/lint/fixture/trigger
--   require a registered line + a banked seen-red artifact+sha; waived requires a ruling); append-only
--   (trigger). DERIVED: foreclosure_debt (a view — cannot go stale). The two close-manifest lines
--   (foreclosure-debt, foreclosure-integrity) live in the SIBLING repo's
--   epistemic-operator/instruments/close_manifest.py (registered permanently) — not in this repo's
--   tools/; only append_only_integrity.py is local.
-- NOT ENFORCED here (the honest limits, above): the filing lapse (out of scope); Goodhart checkbox
--   foreclosures (seen-red raises the floor; the adversarial pass samples); gate-body drift past the
--   integrity line (re-bank seen-red on substantial gate edits).
