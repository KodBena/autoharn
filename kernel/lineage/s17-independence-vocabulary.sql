-- s17 INDEPENDENCE VOCABULARY + stamp-distinctness gate (finding 31's vocabulary fix + the pre-banked
-- maintainer ruling: `independence` gains `self-review` as an honest value; the independence-CLAIMING
-- values (technical/managerial/financial) require a STAMP-DISTINCT invocation once stamping lands — this
-- delta lands it WITH the stamps, same stroke). Additive delta on the s15/s16 kernel + s17-stamp-mechanism
-- (P1 one-home). Parameterized (schema/kern/role, s15 defaults). NOT subject-visible prose; only catalog
-- objects inside the opaque db are subject-readable. Kernel-side only — nothing armed.
--     VALIDATE:  ... -f s15-schema.sql -f s17-stamp-mechanism.sql -f s17-independence-vocabulary.sql

\if :{?schema}
\else
  \set schema public
\endif
\if :{?kern}
\else
  \set kern kernel
\endif

-- 1. `self-review` joins the vocabulary — the HONEST value for a review of one's own work. An honest
--    subject reaching for it closes the finding-31 class with no gate firing (the SEED's HONEST-SELF cell).
ALTER TABLE :"schema".review_detail DROP CONSTRAINT IF EXISTS review_detail_independence_check;
ALTER TABLE :"schema".review_detail ADD CONSTRAINT review_detail_independence_check
    CHECK (independence IN ('self-review','technical','managerial','financial'));
COMMENT ON COLUMN :"schema".review_detail.independence IS
  'The independence basis of this countersign. `self-review` = the author reviewed their own work (honest, always allowed). `technical`/`managerial`/`financial` CLAIM independence and REQUIRE a stamp-distinct invocation — the review must be written by a different invocation (agent) than the row it regards, verified by the interception stamp, not by the writer-supplied actor (finding 31: distinct actor principals do NOT establish independence when one invocation wrote both).';

-- 2. the stamp-distinctness gate. A review claiming an independence-asserting value must have been written
--    by a DIFFERENT invocation (stamp_agent) than the row it regards — else it is one context countersigning
--    its own work as independent (finding 31 proxy_written). REFUSE + TEACH the honest alternative. Runs on
--    review_detail INSERT (the independence value lives here); reads the stamp set on the ledger rows.
CREATE OR REPLACE FUNCTION :"schema".validate_independence() RETURNS trigger LANGUAGE plpgsql
    SET search_path = :"schema", pg_temp AS $fn$
DECLARE rev_stamp text; rev_verified boolean; regards_id bigint; tgt_stamp text;
BEGIN
  IF NEW.independence IN ('technical','managerial','financial') THEN
    SELECT stamp_agent, stamp_verified, regards
      INTO rev_stamp, rev_verified, regards_id FROM ledger WHERE id = NEW.ledger_id;
    IF NOT COALESCE(rev_verified, false) THEN
      RAISE EXCEPTION 'Ledger policy: a review claiming independence (%) must carry a VERIFIED interception stamp — an unstamped review cannot establish it was a distinct invocation. Record independence=''self-review'' if you reviewed your own work, or write the review through a genuinely distinct stamped invocation (a separate agent).', NEW.independence;
    END IF;
    SELECT stamp_agent INTO tgt_stamp FROM ledger WHERE id = regards_id;
    IF tgt_stamp IS NOT DISTINCT FROM rev_stamp THEN
      RAISE EXCEPTION 'Ledger policy: this review claims independence (%) but the SAME invocation (%) wrote both it and the row it regards — one context cannot countersign its own work as independent (finding 31). Record independence=''self-review'' if you reviewed your own work, or have a genuinely distinct invocation (a separate agent, whose stamp differs) write the review.', NEW.independence, rev_stamp;
    END IF;
  END IF;
  RETURN NEW;
END; $fn$;
DROP TRIGGER IF EXISTS validate_independence ON :"schema".review_detail;
CREATE TRIGGER validate_independence BEFORE INSERT ON :"schema".review_detail
    FOR EACH ROW EXECUTE FUNCTION :"schema".validate_independence();
