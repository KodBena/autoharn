-- db/harness/007_ruling_delivers_fk.sql
-- The `delivers` FK on acts.ruling (finding 35 stage 2; maintainer grade "air raid siren"). Stage 1 (the
-- delivery_freight_integrity close line) mechanized the CHECK by convention (a binding ruling whose
-- regards says 'delivered', byte-matched to an earlier binding freight). Stage 2 makes the delivery->
-- freight edge a FORMAL KEY: a delivery row names the freight it delivers, and a trigger refuses a
-- delivery whose verbatim does not byte-match that freight (the forged-freight / stale-authority class on
-- the rulings spine itself — id 26 delivered id 25 held ONLY by byte-coincidence + prose regards before).
--
-- Same convention-where-a-key-belongs family as finding 34. Idempotent + re-runnable, parameterized by a
-- psql :schema variable (default acts). Run as the schema owner (bork).
--     psql -h 192.168.122.1 -d harness -f db/harness/007_ruling_delivers_fk.sql

\if :{?schema}
\else
  \set schema acts
\endif

BEGIN;

ALTER TABLE :"schema".ruling ADD COLUMN IF NOT EXISTS delivers bigint REFERENCES :"schema".ruling(id);
COMMENT ON COLUMN :"schema".ruling.delivers IS
  'The freight ruling this row DELIVERS — a FORMAL key replacing byte-coincidence + prose regards (finding 35 stage 2). A delivery row''s verbatim MUST byte-match its freight (verbatim + verbatim_sha256), enforced by ruling_delivers_integrity; a delivery that intends to diverge is an amendment (a supersedes chain), never a silent byte-mismatch.';

-- integrity: a row with delivers set references an EARLIER freight whose bytes it carries EXACTLY.
-- NAMED-NOT-COVERED (ADR-0000 closure statement): an INTENTIONAL divergence (a delivery that knowingly
-- amends the freight) is out of scope here — no delivery has ever diverged; if one arises it is filed as
-- an amendment (supersedes lineage) and this trigger is extended then, not silently relaxed now.
-- search_path carries :"schema" (interpolated HERE, outside the $$ body where psql vars do not expand),
-- so the body queries `ruling` UNQUALIFIED and it resolves in :schema in both validate and real apply.
CREATE OR REPLACE FUNCTION :"schema".ruling_delivers_integrity() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $$
DECLARE f_verbatim text; f_sha text;
BEGIN
  IF NEW.delivers IS NOT NULL THEN
    IF NEW.delivers >= NEW.id THEN
      RAISE EXCEPTION 'acts.ruling.delivers=% must reference an EARLIER row (a delivery follows its freight; id-is-order).', NEW.delivers;
    END IF;
    SELECT verbatim, verbatim_sha256 INTO f_verbatim, f_sha
      FROM ruling WHERE id = NEW.delivers;
    IF f_verbatim IS NULL THEN
      RAISE EXCEPTION 'acts.ruling.delivers=% does not resolve to a freight row.', NEW.delivers;
    END IF;
    IF NEW.verbatim_sha256 <> f_sha OR NEW.verbatim <> f_verbatim THEN
      RAISE EXCEPTION 'acts.ruling delivery %: verbatim does NOT byte-match its declared freight % (finding 35: a delivery carries the frozen freight''s exact bytes, or declares an amendment lineage — a silent divergence is the forged-freight class this FK closes).', NEW.id, NEW.delivers;
    END IF;
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS ruling_delivers_integrity ON :"schema".ruling;
CREATE TRIGGER ruling_delivers_integrity BEFORE INSERT ON :"schema".ruling
  FOR EACH ROW EXECUTE FUNCTION :"schema".ruling_delivers_integrity();

-- ONE-TIME BACK-FILL (convention -> FK). Populate `delivers` on every historical binding delivery row
-- (regards records a 'delivered' act) that byte-matches an earlier binding freight — i.e. id 26 -> id 25.
-- This is a STRUCTURAL column back-fill on historical rows (the FK did not exist when they were written),
-- NOT a content edit: verbatim/actor/binding_grade/regards are untouched. append-only is briefly disabled
-- for it and re-enabled; the WHERE guard sets `delivers` ONLY where the bytes already match, so the
-- back-fill cannot introduce a mismatch. (declared-drop: n/a — no CASCADE; this is an UPDATE migration.)
ALTER TABLE :"schema".ruling DISABLE TRIGGER ruling_append_only_row;
UPDATE :"schema".ruling d SET delivers = f.id
FROM :"schema".ruling f
WHERE d.delivers IS NULL
  AND d.binding_grade = 'binding' AND lower(coalesce(d.regards,'')) LIKE '%delivered%'
  AND f.id < d.id AND f.binding_grade = 'binding'
  AND f.verbatim = d.verbatim AND f.verbatim_sha256 = d.verbatim_sha256;
ALTER TABLE :"schema".ruling ENABLE TRIGGER ruling_append_only_row;

COMMIT;

-- honest ledger of strength: ENFORCED at write time — delivers references an earlier freight (FK + trigger);
--   a delivery's verbatim byte-matches its declared freight (trigger). The stage-1 close line
--   (delivery_freight_integrity) now reads the FK where present, convention where absent (the back-fill
--   makes the historical 26->25 edge formal, so it is FK-checked, not convention-inferred).
