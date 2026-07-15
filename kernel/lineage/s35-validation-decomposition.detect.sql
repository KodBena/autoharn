-- s35-validation-decomposition.detect.sql -- sibling DETECT file, per the PER-DELTA VERIFICATION
-- CONVENTION (bootstrap/migrate_core.py module docstring). Never edits the frozen s35 file itself
-- (ADR-0005 Rule 8).
--
-- BEHAVIOR-FINGERPRINT, NOT NAME-MATCH (ledger finding 781's lesson, re-applied -- the same
-- discipline s29/s30/s31/s32/s33's own detects use). s35 adds NO new column and NO new view -- it
-- re-issues validate_work_item() as a thin dispatcher and adds FOUR new catalog function objects
-- (the leaves) that did not exist under s33. This detect confirms two independent facts together:
--   1. all four leaf functions exist with their s35 signatures (to_regprocedure, schema-qualified
--      -- absent on any pre-s35 kernel, including s33's own monolith).
--   2. the LIVE validate_work_item() body (via pg_get_functiondef) CALLS the leaves by name --
--      proving the live dispatcher is the s35 build, not an s22..s33 monolith that merely happens
--      to coexist with four orphaned leaf functions on the same schema.
SELECT
  to_regprocedure(format('%I.validate_work_item_open(%I.ledger)', :'schema', :'schema')) IS NOT NULL
  AND to_regprocedure(format('%I.validate_work_item_depends(%I.ledger)', :'schema', :'schema')) IS NOT NULL
  AND to_regprocedure(format('%I.validate_work_item_close_is_composite(text)', :'schema')) IS NOT NULL
  AND to_regprocedure(format('%I.validate_work_item_close(%I.ledger,boolean,text)', :'schema', :'schema')) IS NOT NULL
  AND pg_get_functiondef((:'schema' || '.validate_work_item()')::regprocedure) LIKE '%validate_work_item_open%'
  AND pg_get_functiondef((:'schema' || '.validate_work_item()')::regprocedure) LIKE '%validate_work_item_depends%'
  AND pg_get_functiondef((:'schema' || '.validate_work_item()')::regprocedure) LIKE '%validate_work_item_close%'
AS applied;
